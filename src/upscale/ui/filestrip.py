from enum import Enum
from functools import partial
import time
from typing import Dict, List
from PySide6.QtWidgets import QMenu, QPushButton, QLabel, QVBoxLayout, QFrame, QScrollArea, QSizePolicy, QApplication, QMessageBox
from PySide6.QtGui import QPixmap, QColor, QIcon, QPaintEvent, QPainter, QPalette, QFontMetrics, QFont, QMouseEvent
from PySide6.QtCore import QObject, Qt, QSize, QPoint, Signal, QTimer
from PIL import Image
from PIL.ImageQt import ImageQt

from upscale.app import App
from upscale.lib.file import File, InputFile
from upscale.ui.selectionManager import SelectionManager
from upscale.ui.signals import Signals, emitLater, getSignals

FILESTRIP_CONTAINER_HEIGHT = 210
FILESTRIP_SCROLL_HEIGHT = 180
FILE_BUTTON_SIZE = 160
FILE_IMAGE_SIZE = 148

DOUBLE_CLICK_INTERVAL = 200


class Indicator(Enum):
    FIRST = 1
    SECOND = 2
    THIRD = 3
    FOURTH = 4


class FileStrip:

    def __init__(self, frameBaseFile: QFrame, frameFileList: QFrame, frameContainer: QFrame, app: App, selectionManager: SelectionManager, redrawSignal: Signal, maxVisibleButtons=-1):
        self.buttons: Dict[File, FileButton] = {}
        self.frameBaseFile = frameBaseFile
        self.frameFileList = frameFileList
        self.frameContainer = frameContainer
        self.signals = getSignals()
        self.app = app
        self.maxVisibleButtons = maxVisibleButtons
        self.selectionManager = selectionManager

        self.scroll = self.frameContainer.findChildren(QScrollArea)[0]
        self.scroll.horizontalScrollBar().valueChanged.connect(partial(self.slotUpdateThumbnails, self.frameFileList))
        self.signals.updateThumbnail.connect(self.slotUpdateThumbnail)

        self.frameContainer.setMinimumSize(QSize(FILE_BUTTON_SIZE+8, FILESTRIP_CONTAINER_HEIGHT))
        self.frameContainer.setMaximumSize(QSize(16777215, FILESTRIP_CONTAINER_HEIGHT))
        self.scroll.setMinimumSize(QSize(FILE_BUTTON_SIZE+8, FILESTRIP_SCROLL_HEIGHT))
        self.scroll.setMaximumSize(QSize(16777215, FILESTRIP_SCROLL_HEIGHT))
        self.fileCountLabel = self.frameContainer.findChildren(QLabel)[1]

        self.signals.focusFile.connect(self.focusFile)
        self.signals.updateIndicator.connect(self.updateIndicator)
        self.signals.addFileButton.connect(self.slotAddFileButton)
        self.signals.appendFile.connect(self.appendFile)
        redrawSignal.connect(self.drawFileList)

        self.drawFileList()

    def removeButton(self, file: File):
        button = self.buttons.pop(file)
        button.deleteLater()

    def makeFileButton(self, frame, file, doFocus, doPriority):
        button = FileButton(self.signals, file)
        self.buttons[file] = button

        priority = 10 if doPriority else 0
        emitLater(self.signals.addFileButton.emit, frame, button, doFocus, priority=priority)

    def cleanFrame(self, frame):
        for child in frame.findChildren(QLabel):
            child.setParent(None)
            child.deleteLater()
        for child in frame.findChildren(QPushButton):
            child.setParent(None)
            child.deleteLater()
        for child in frame.findChildren(QFrame):
            child.setParent(None)
            child.deleteLater()

    def appendFile(self, file: File):
        fileList = self.app.getFileList()
        self.fileCountLabel.setText(f"({len(fileList)})")
        self.makeFileButton(self.frameFileList, file, True, True)

    def drawFileList(self, focusOnFile: File = None):
        self.cleanFrame(self.frameBaseFile)
        if self.app.getBaseFile() is not None:
            self.makeFileButton(self.frameBaseFile, self.app.getBaseFile(), True, True)

        self.cleanFrame(self.frameFileList)
        fileList = self.app.getFileList()
        self.fileCountLabel.setText(f"({len(fileList)})")

        for idx, file in enumerate(fileList):
            doFocus = False
            if focusOnFile is not None:
                if file == focusOnFile:
                    doFocus = True
            else:
                if idx == 0:
                    doFocus = True
            doPriority = idx < 10 if self.maxVisibleButtons < 0 else idx < self.maxVisibleButtons
            if idx % 5 == 0:  # yield periodically to enable the frame to render with full width buttons
                QApplication.processEvents()
            self.makeFileButton(self.frameFileList, file, doFocus, doPriority)

        if self.maxVisibleButtons > 0:
            self.fitMaxSize()

    def fitMaxSize(self):
        c = len(self.app.getFileList())
        if c > self.maxVisibleButtons:
            c = self.maxVisibleButtons
        self.frameContainer.setMinimumSize(QSize(c*(FILE_BUTTON_SIZE+8), FILESTRIP_CONTAINER_HEIGHT))

    def focusFile(self, file: File):
        if file in self.buttons:
            self.buttons[file].setFocus()
            self.scroll.ensureWidgetVisible(self.buttons[file])

    def slotAddFileButton(self, frame: QFrame, button: QPushButton, forceFocus=False):
        frame.layout().addWidget(button, 0, Qt.AlignTop)

        # force frame relayout to adjust to content
        frame.layout().invalidate()
        frame.layout().activate()
        frame.updateGeometry()

    def slotUpdateThumbnails(self, frame, _=None):
        if frame == self.frameFileList:
            for child in frame.findChildren(FileButton):
                if child.isVisible() and not child.renderedThumbnail and not child.visibleRegion().isEmpty():
                    emitLater(self.signals.updateThumbnail.emit, frame, child)

    def slotUpdateThumbnail(self, frame, button):
        if frame == self.frameFileList:
            button.showEvent(None)

    def updateIndicator(self, file: File, idx: int):
        if file in self.buttons:
            button = self.buttons[file]
            button.updateIndicator(idx)


class IconLabel(QLabel):
    def __init__(self, file: File = None):
        super().__init__()
        self.file = file
        self.isExcluded = False
        self.indicators: List[Indicator] = []

        self.setFixedSize(QSize(FILE_IMAGE_SIZE, FILE_IMAGE_SIZE))
        if not self.file is None:
            self.pixmap = QPixmap(file.path)
        else:
            self.pixmap = QPixmap(FILE_IMAGE_SIZE, FILE_IMAGE_SIZE)
            self.pixmap.fill(self.palette().color(QPalette.Window))
        self.setAlignment(Qt.AlignCenter)

    def setFile(self, file: File) -> None:
        self.file = file
        try:
            image = Image.open(file.path)
            image.thumbnail((FILE_IMAGE_SIZE, FILE_IMAGE_SIZE))
            qt_image = ImageQt(image)
            self.pixmap = QPixmap.fromImage(qt_image)
        except:
            pass

    def drawIndicator(self, painter: QPainter, color: QColor, label: str, offset: int):
        painter.setBrush(color)
        painter.setPen(color)
        painter.drawEllipse(FILE_IMAGE_SIZE - 25-offset, 5, 20, 20)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(FILE_IMAGE_SIZE - 25-offset, 5, 20, 20, Qt.AlignCenter, label)
        offset += 12
        return offset

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)

        painter = QPainter(self)
        painter.drawPixmap(QPoint(0, 0), self.pixmap)

        offset = 0
        if Indicator.FIRST in self.indicators:
            offset = self.drawIndicator(painter, QColor(0, 0, 255), "1", offset)
        if Indicator.SECOND in self.indicators:
            offset = self.drawIndicator(painter, QColor(64, 64, 64), "2", offset)
        if Indicator.THIRD in self.indicators:
            offset = self.drawIndicator(painter, QColor(64, 64, 64), "3", offset)
        if Indicator.FOURTH in self.indicators:
            offset = self.drawIndicator(painter, QColor(64, 64, 64), "4", offset)


class FileButton(QPushButton):
    def __init__(self, signals: Signals, file: File):
        super().__init__()
        self.file = file
        self.signals = signals
        self.renderedThumbnail = False

        self.iconLabel = IconLabel()
        self.objectName = file.basename
        placeHolder = QPixmap(FILE_IMAGE_SIZE, FILE_IMAGE_SIZE)
        placeHolder.fill(QColor(0, 0, 0, 0))

        textLabel = QLabel(file.basename)
        textLabel.setAlignment(Qt.AlignCenter)
        textLabel.setFont(QFont("Arial", 9))
        metrics = QFontMetrics(textLabel.font())
        clippedText = metrics.elidedText(file.basename, Qt.TextElideMode.ElideMiddle, FILE_IMAGE_SIZE)
        textLabel.setText(clippedText)

        layout = QVBoxLayout(self)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.setFixedSize(QSize(FILE_BUTTON_SIZE, FILE_BUTTON_SIZE))
        layout.setContentsMargins(4, 9, 4, 9)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.iconLabel)
        layout.addWidget(textLabel)

        # timer to distinguish double / single clicks
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(lambda: self.delayedMousePressEvent(self.click_pending_event))
        self.click_pending = False
        self.click_pending_event = None

    def focusOutEvent(self, arg__1):
        return super().focusOutEvent(arg__1)

    def mousePressEvent(self, e: QMouseEvent):
        self.click_pending = True
        self.click_pending_event = e.clone()
        self.timer.start(DOUBLE_CLICK_INTERVAL)

    def delayedMousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.signals.selectCompareFile.emit(self.file)

            if e.modifiers() == Qt.ShiftModifier:
                self.signals.selectBaseFile.emit(self.file)

        if self.click_pending:
            self.click_pending = False

        if e.button() == Qt.RightButton:
            menu = QMenu(self)
            actionRemove = menu.addAction("Remove from Project")
            actionRemove.triggered.connect(self.actionRemove)

            menu.exec_(e.globalPos())
        else:
            return super().mousePressEvent(e)

    def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:
        if self.click_pending:
            self.timer.stop()
            self.click_pending = False
            self.delayedMouseDoubleClickEvent()

    def delayedMouseDoubleClickEvent(self):
        self.signals.selectBaseFile.emit(self.file)

    def maybeDeferredRenderThumbnail(self, forceFocus=False):
        if self.isVisible() and not self.renderedThumbnail and not self.iconLabel.visibleRegion().isEmpty():
            self.iconLabel.setFile(self.file)
            self.renderedThumbnail = True

            # focus first instance in list once it is available
            if forceFocus:
                self.click()
                self.setFocus()

            return True
        return False

    def updateIndicator(self, idx):
        self.iconLabel.indicators.clear()
        if idx == 0:
            self.iconLabel.indicators.append(Indicator.FIRST)
        elif idx == 1:
            self.iconLabel.indicators.append(Indicator.SECOND)
        elif idx == 2:
            self.iconLabel.indicators.append(Indicator.THIRD)
        elif idx == 3:
            self.iconLabel.indicators.append(Indicator.FOURTH)

        if idx == 0:
            self.setStyleSheet("background-color: blue;")
        elif idx > 0:
            self.setStyleSheet("background-color: dimgray;")
        else:
            self.setStyleSheet("")

        self.repaint()

    def showEvent(self, event):
        self.maybeDeferredRenderThumbnail()
        return super().showEvent(event)

    def actionRemove(self):
        self.signals.removeFile.emit(self.file, self)
