from enum import Enum
from functools import partial
import time
from typing import Dict, List
from PySide6.QtWidgets import QMenu, QPushButton, QLabel, QVBoxLayout, QFrame, QScrollArea, QSizePolicy, QApplication, QMessageBox
from PySide6.QtGui import QPixmap, QColor, QIcon, QPaintEvent, QPainter, QPalette, QFontMetrics, QFont, QMouseEvent
from PySide6.QtCore import QObject, Qt, QSize, QPoint, Signal, QTimer
from PIL import Image
from PIL.ImageQt import ImageQt

from enhance.app import App
from enhance.lib.file import File, InputFile, OutputFile
from enhance.ui.selectionManager import SelectionManager
from enhance.ui.signals import Signals, emitLater, getSignals

FILESTRIP_CONTAINER_HEIGHT = 150
FILESTRIP_SCROLL_HEIGHT = 146
FILE_BUTTON_SIZE = 120
FILE_IMAGE_SIZE = 108

DOUBLE_CLICK_INTERVAL = 200


class Indicator(Enum):
    FIRST = 1
    SECOND = 2
    THIRD = 3
    FOURTH = 4
    SAVED = 5


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
        self.addButton: QPushButton = None  # The "+" button for creating new output files

        self.scroll = self.frameContainer.findChildren(QScrollArea)[0]
        self.scroll.horizontalScrollBar().valueChanged.connect(
            partial(self.updateThumbnails, self.frameFileList)
        )
        self.signals.updateThumbnail.connect(self.updateThumbnail)

        self.frameContainer.setMinimumSize(QSize(FILE_BUTTON_SIZE+8, FILESTRIP_CONTAINER_HEIGHT))
        self.frameContainer.setMaximumSize(QSize(16777215, FILESTRIP_CONTAINER_HEIGHT))
        self.scroll.setMinimumSize(QSize(FILE_BUTTON_SIZE+8, FILESTRIP_SCROLL_HEIGHT))
        self.scroll.setMaximumSize(QSize(16777215, FILESTRIP_SCROLL_HEIGHT))
        self.fileCountLabel = self.frameContainer.findChildren(QLabel)[1]

        self.signals.focusFile.connect(self.focusFile)
        self.signals.updateIndicator.connect(self.updateIndicator)
        self.signals.addFileButton.connect(self.addFileButton)
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

    def makeAddButton(self):
        """Create the '+' button for adding new output files"""
        if self.addButton is not None:
            return self.addButton
        
        self.addButton = QPushButton("+")
        self.addButton.setObjectName("addOutputFileButton")
        self.addButton.setFixedSize(QSize(FILE_BUTTON_SIZE, FILE_BUTTON_SIZE))
        self.addButton.setStyleSheet("font-size: 32px; font-weight: bold;")
        self.addButton.setToolTip("Create new output file from current base")
        self.addButton.clicked.connect(lambda: self.signals.createOutputFile.emit())
        return self.addButton

    def cleanFrame(self, frame):
        for child in frame.findChildren(QLabel):
            child.setParent(None)
            child.deleteLater()
        for child in frame.findChildren(QPushButton):
            # Preserve the add button
            if child == self.addButton:
                continue
            child.setParent(None)
            child.deleteLater()
        for child in frame.findChildren(QFrame):
            child.setParent(None)
            child.deleteLater()

    def appendFile(self, file: File):
        fileList = self.app.getFileList()
        self.fileCountLabel.setText(f"({len(fileList)})")
        self.makeFileButton(self.frameFileList, file, True, True)
        # Re-add the "+" button at the end
        self.ensureAddButtonAtEnd()

    def ensureAddButtonAtEnd(self):
        """Ensure the '+' button is at the end of the file list"""
        if self.app.getBaseFile() is None:
            return  # No base file, don't show add button
        addBtn = self.makeAddButton()
        # Remove from layout if present, then re-add at end
        layout = self.frameFileList.layout()
        if addBtn.parent() == self.frameFileList:
            layout.removeWidget(addBtn)
        layout.addWidget(addBtn, 0, Qt.AlignTop)

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

        # Add the "+" button at the end
        self.ensureAddButtonAtEnd()

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

    def addFileButton(self, frame: QFrame, button: QPushButton, forceFocus=False):
        frame.layout().addWidget(button, 0, Qt.AlignTop)

        # force frame relayout to adjust to content
        frame.layout().invalidate()
        frame.layout().activate()
        frame.updateGeometry()

    def updateThumbnails(self, frame, _=None):
        if frame == self.frameFileList:
            for child in frame.findChildren(FileButton):
                if child.isVisible() and not child.renderedThumbnail and not child.visibleRegion().isEmpty():
                    emitLater(self.signals.updateThumbnail.emit, frame, child)

    def updateThumbnail(self, frame, button):
        if frame == self.frameFileList:
            button.showEvent(None)

    def updateIndicator(self, file: File, idx: int):
        if file in self.buttons:
            button = self.buttons[file]
            button.updateIndicator(idx)

    def getButton(self, file: File):
        if file in self.buttons:
            return self.buttons[file]
        return None


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
            pixmap = QPixmap.fromImage(qt_image)

            self.pixmap = QPixmap(FILE_IMAGE_SIZE, FILE_IMAGE_SIZE)
            self.pixmap.fill(QColor(128, 128, 128))
            painter = QPainter(self.pixmap)
            offset_x = 0
            offset_y = 0
            if pixmap.width() < FILE_IMAGE_SIZE:
                offset_x = (FILE_IMAGE_SIZE - pixmap.width()) / 2
            if pixmap.height() < FILE_IMAGE_SIZE:
                offset_y = (FILE_IMAGE_SIZE - pixmap.height()) / 2
            painter.drawPixmap(offset_x, offset_y, pixmap)
            painter.end()
        except:
            pass

    def drawIndicator(self, painter: QPainter, color: QColor, label: str, offset: int):
        painter.setBrush(color)
        painter.setPen(color)
        painter.drawEllipse(FILE_IMAGE_SIZE - 25, 5 + offset, 20, 20)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            FILE_IMAGE_SIZE - 25, 5 + offset, 20, 20, Qt.AlignCenter, label
        )
        offset += 28
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
        if Indicator.SAVED in self.indicators:
            offset = self.drawIndicator(painter, QColor(0, 128, 0), "S", offset)


class FileButton(QPushButton):
    def __init__(self, signals: Signals, file: File):
        super().__init__()
        self.file = file
        self.signals = signals
        self.renderedThumbnail = False
        self.draw()

    def draw(self):
        self.iconLabel = IconLabel()
        self.objectName = self.file.basename
        placeHolder = QPixmap(FILE_IMAGE_SIZE, FILE_IMAGE_SIZE)
        placeHolder.fill(QColor(0, 0, 0, 0))

        self.textLabel = QLabel(self.file.basename)
        self.textLabel.setAlignment(Qt.AlignCenter)
        self.textLabel.setFont(QFont("Arial", 9))
        metrics = QFontMetrics(self.textLabel.font())
        clippedText = metrics.elidedText(self.file.basename, Qt.TextElideMode.ElideMiddle, FILE_IMAGE_SIZE)
        self.textLabel.setText(clippedText)

        layout = QVBoxLayout(self)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.setFixedSize(QSize(FILE_BUTTON_SIZE, FILE_BUTTON_SIZE))
        layout.setContentsMargins(4, 9, 4, 9)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.iconLabel)
        layout.addWidget(self.textLabel)

        # timer to distinguish double / single clicks
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(lambda: self.delayedMousePressEvent(self.click_pending_event))
        self.click_pending = False
        self.click_pending_event = None

    def updateTextLabel(self):
        metrics = QFontMetrics(self.textLabel.font())
        clippedText = metrics.elidedText(self.file.basename, Qt.TextElideMode.ElideMiddle, FILE_IMAGE_SIZE)
        self.textLabel.setText(clippedText)

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
                self.signals.selectBaseFile.emit(self.file, False)

        if self.click_pending:
            self.click_pending = False

        if e.button() == Qt.RightButton:
            if isinstance(self.file, OutputFile):
                menu = QMenu(self)
                actionRemove = menu.addAction("Remove from Project")
                actionRemove.triggered.connect(self.actionRemove)
                actionSave = menu.addAction("Save to File")
                actionSave.triggered.connect(self.actionSaveFile)

                menu.exec_(e.globalPos())
        else:
            return super().mousePressEvent(e)

    def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:
        if self.click_pending:
            self.timer.stop()
            self.click_pending = False
            self.delayedMouseDoubleClickEvent()

    def delayedMouseDoubleClickEvent(self):
        self.signals.selectBaseFile.emit(self.file, False)

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
        if idx < -1 and len(self.iconLabel.indicators) > 0:
            idx = self.iconLabel.indicators[0].value - 1

        self.iconLabel.indicators.clear()
        if idx == 0:
            self.iconLabel.indicators.append(Indicator.FIRST)
        elif idx == 1:
            self.iconLabel.indicators.append(Indicator.SECOND)
        elif idx == 2:
            self.iconLabel.indicators.append(Indicator.THIRD)
        elif idx == 3:
            self.iconLabel.indicators.append(Indicator.FOURTH)

        if self.file.saved:
            self.iconLabel.indicators.append(Indicator.SAVED)

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

    def actionSaveFile(self):
        self.signals.saveFile.emit(self.file, self)
