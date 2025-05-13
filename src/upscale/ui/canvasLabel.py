from enum import Enum
from typing import List, Optional, Tuple
import cv2
import numpy as np
from PySide6.QtCore import (Qt, QPointF)
from PySide6.QtGui import (QPainter, QPaintEvent, QWheelEvent, QMouseEvent,
                           QPixmap, QColor, QPen, QPainterPath, QFont, QImage)
from PySide6.QtWidgets import QLabel, QWidget

from upscale.lib.file import File
from upscale.ui.selectionManager import SelectionManager
from upscale.ui.signals import Signals, getSignals
from upscale.ui.common import RenderMode, ZoomLevel


class CanvasLabel(QLabel):

    def __init__(self, selectionManager: SelectionManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.selectionManager: SelectionManager = selectionManager
        self.zoomFactor: float = 1.0
        self.posX: int = 0
        self.posY: int = 0
        self.dragX: int = 0
        self.dragY: int = 0
        self.mouseX: int = 0
        self.mouseY: int = 0
        self.signals: Signals = getSignals()
        self.setMouseTracking(True)

        self.signals.showFiles.connect(self.showFiles)
        self.signals.setRenderMode.connect(self.setRenderMode)

        self.antialias = False
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Arial", 20, QFont.Bold))

        self.img = None  # Canvas img used for single and split modes
        self.img1 = None # Seperate imgs used for grid mode
        self.img2 = None
        self.img3 = None
        self.img4 = None
        self.fraction = 0.5
        self.renderMode: RenderMode = RenderMode.Single

        self.setScaledContents(False)

    def updateFraction(self, value: int) -> None:
        self.fraction = value / 100
        self.img = None
        if self.renderMode == RenderMode.Single:
            h, w, _ = np.shape(self.img1)
            newImg = np.zeros((h, w, 3), np.uint8)
            newImg[0:h, 0:int(w)] = self.img1[0:h, 0:int(w)]
            self.img = newImg
            self.update(False)
            self.repaint()

        elif self.renderMode == RenderMode.Split:
            h, w, _ = np.shape(self.img1)
            newImg = np.zeros((h, w, 3), np.uint8)
            newImg[0:h, 0:int(w * self.fraction)] = self.img1[0:h, 0:int(w * self.fraction)]
            newImg[0:h, int(w * (self.fraction)):w] = self.img2[0:h, int(w * (self.fraction)):w]
            newImg[0:h, int(self.fraction * w) - 2:int(self.fraction * w) + 2] = (0, 255, 0)
            self.img = newImg
            self.update(False)
            self.repaint()

        elif self.renderMode == RenderMode.Grid:
            # For grid view, we redraw 4 pixmap for each paint operation. See paintGrid().
            pass

    # We load files here with 8bits/channel for consistent display via QPixmap. This doesn't impact how we work with channels in models.
    # TODO: Ensure img shapes match
    def showFiles(self, resetView=False):
        baseFile = self.selectionManager.getBaseFile()
        if baseFile is not None:
            self.img1 = cv2.imread(baseFile.path)
            if self.renderMode == RenderMode.Split or self.renderMode == RenderMode.Grid:
                compareFile = self.selectionManager.getCompareFile(0)
                if compareFile is not None:
                    self.img2 = cv2.imread(compareFile.path)
                else:
                    self.img2 = np.zeros((self.img1.shape[0], self.img1.shape[1], 3), np.uint8)

            if self.renderMode == RenderMode.Grid:
                compareFile2 = self.selectionManager.getCompareFile(1)
                if compareFile2 is not None:
                    self.img3 = cv2.imread(compareFile2.path)
                else:
                    self.img3 = np.zeros((self.img1.shape[0], self.img1.shape[1], 3), np.uint8)

                compareFile3 = self.selectionManager.getCompareFile(2)
                if compareFile3 is not None:
                    self.img4 = cv2.imread(compareFile3.path)
                else:
                    self.img4 = np.zeros((self.img1.shape[0], self.img1.shape[1], 3), np.uint8)

        else:
            self.img1 = np.zeros((0, 0, 3), np.uint8)
            self.update(True)

        self.updateFraction(self.fraction * 100)
        if resetView or len(self.selectionManager.compare) == 0:
            self.setZoomFactor(ZoomLevel.FIT)
        self.repaint()

    def update(self, doResetZoomAndPosition: bool = True) -> None:
        if self.img is None:
            self.setText("No images selected")
        else:
            h,w,c = self.img.shape
            if h == 0 or w == 0:
                self.setText("No images selected")
            else:
                self.setText("")

        if doResetZoomAndPosition:
            # Presevering zoom / position after user actions, but need to perform at initial load
            if self.zoomFactor == 1:
                self.resetZoomAndPosition()

        self.repaint()

    def setRenderMode(self, renderMode: RenderMode) -> None:
        self.renderMode = renderMode
        self.showFiles()

    def setAntialias(self, antialias: bool) -> None:
        self.antialias = antialias
        self.repaint()

    def resetZoomAndPosition(self, zoomFactor=1) -> None:
        self.zoomFactor = zoomFactor

        # Center the pixmap within the QLabel
        if self.img is not None and self.img.shape[0] > 0 and self.img.shape[1] > 0:
            labelWidth = self.width()
            labelHeight = self.height()
            imageWidth = self.img.shape[1]
            imageHeight = self.img.shape[0]

            if imageWidth == 0 or imageHeight == 0:
                return

            renderWidth = int(imageWidth * self.zoomFactor)
            renderHeight = int(imageHeight * self.zoomFactor)

            if self.renderMode == RenderMode.Grid:
                self.posX = (labelWidth/2 - renderWidth) // 2
                self.posY = (labelHeight/2 - renderHeight) // 2

            else:
                self.posX = (labelWidth - renderWidth) // 2
                self.posY = (labelHeight - renderHeight) // 2

            self.signals.changeZoom.emit(self.zoomFactor)

    def setZoom(self, dir: int, mouseX: int, mouseY: int) -> None:
        old_zoom_factor = self.zoomFactor
        if dir < 0:
            self.zoomFactor /= 1.1
        if dir > 0:
            self.zoomFactor *= 1.1

        imageWidth = self.img1.shape[1]
        labelWidth = self.width()
        imageHeight = self.img1.shape[0]
        labelHeight = self.height()

        if imageWidth == 0 or imageHeight == 0:
            return

        if self.renderMode == RenderMode.Grid:
            minZoom = min(labelWidth / 2 / imageWidth, labelHeight / 2 / imageHeight)
        else:
            minZoom = min(labelWidth / imageWidth, labelHeight / imageHeight)

        if self.zoomFactor < minZoom:
            self.zoomFactor = minZoom
            self.resetZoomAndPosition(self.zoomFactor)

        # Calculate the new position to keep the mouse position at the same place
        if self.renderMode == RenderMode.Grid:
            if mouseX > self.width() // 2:
                mouseX = mouseX - self.width() // 2
            if mouseY > self.height() // 2:
                mouseY = mouseY - self.height() // 2

            self.posX = mouseX - (mouseX - self.posX) * (self.zoomFactor / old_zoom_factor)
            self.posY = mouseY - (mouseY - self.posY) * (self.zoomFactor / old_zoom_factor)
        else:
            self.posX = mouseX - (mouseX - self.posX) * (self.zoomFactor / old_zoom_factor)
            self.posY = mouseY - (mouseY - self.posY) * (self.zoomFactor / old_zoom_factor)

        self.repaint()
        self.signals.changeZoom.emit(self.zoomFactor)

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta: int = event.angleDelta().y()
        self.setZoom(delta, self.mouseX, self.mouseY)

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        super().mousePressEvent(ev)
        if ev.button() == Qt.RightButton:
            self.dragX = ev.position().x() - self.posX
            self.dragY = ev.position().y() - self.posY

        if ev.button() == Qt.LeftButton:
            x = int((ev.position().x() - self.posX) / self.zoomFactor)
            width = self.img.shape[1]
            fraction = x / width
            self.updateFraction(int(100 * fraction))

    def mouseMoveEvent(self, ev: QMouseEvent) -> None:
        super().mouseMoveEvent(ev)
        self.mouseX = ev.position().x()
        self.mouseY = ev.position().y()

        # Dragging
        if ev.buttons() == Qt.RightButton:
            self.posX = ev.position().x() - self.dragX
            self.posY = ev.position().y() - self.dragY
            self.repaint()

        # Sliding
        if ev.buttons() == Qt.LeftButton:
            x = int((ev.position().x() - self.posX) / self.zoomFactor)
            width = self.img.shape[1]
            fraction = x / width
            self.updateFraction(int(100 * fraction))
            self.repaint()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self.resetZoomAndPosition(self.getZoomFit())
        self.repaint()

    def getZoomFitWidth(self):
        imageWidth = self.img1.shape[1]
        labelWidth = self.width()
        if self.renderMode == RenderMode.Grid:
            labelWidth = labelWidth / 2
        return labelWidth/imageWidth

    def getZoomFitHeight(self):
        imageHeight = self.img1.shape[0]
        labelHeight = self.height()
        if self.renderMode == RenderMode.Grid:
            labelHeight = labelHeight / 2
        return labelHeight/imageHeight

    def getZoomFit(self):
        return min(self.getZoomFitWidth(), self.getZoomFitHeight())

    def setZoomFactor(self, zoomFactor: ZoomLevel) -> None:
        if zoomFactor == ZoomLevel.FIT:
            self.resetZoomAndPosition(self.getZoomFit())
        elif zoomFactor == ZoomLevel.FIT_WIDTH:
            self.resetZoomAndPosition(self.getZoomFitWidth())
        elif zoomFactor == ZoomLevel.FIT_HEIGHT:
            self.resetZoomAndPosition(self.getZoomFitHeight())
        elif "%" in zoomFactor:
            zoomFactor = zoomFactor.replace("%", "")
            try:
                zoomFactor = int(zoomFactor) / 100
                self.resetZoomAndPosition(zoomFactor)
            except ValueError:
                print("Invalid zoom factor: ", zoomFactor)
                return
        else:
            print("Unexpected zoom factor: ", zoomFactor)

        self.repaint()

    def updatePixMapDimensions(self):
        if self.img is not None and self.img.shape[0] > 0 and self.img.shape[1] > 0:
            imageWidth: int = self.img1.shape[1]
            imageHeight: int = self.img1.shape[0]
            labelWidth: int = self.width()
            labelHeight: int = self.height()

            renderWidth: int = int(imageWidth * self.zoomFactor)
            renderHeight: int = int(imageHeight * self.zoomFactor)

            if renderWidth is None:
                return

            if self.renderMode == RenderMode.Grid:
                if renderWidth < labelWidth//2 and renderHeight < labelHeight//2:
                    self.resetZoomAndPosition()
                    renderWidth = int(imageWidth * self.zoomFactor)
                    renderHeight = int(imageHeight * self.zoomFactor)
            else:
                # if the rendered image is larger than the label, reset the zoom
                # use a 1px fudge factor to accomodate rounding
                if renderWidth < (labelWidth-1) and renderHeight < (labelHeight-1):
                    self.resetZoomAndPosition()
                    renderWidth = int(imageWidth * self.zoomFactor)
                    renderHeight = int(imageHeight * self.zoomFactor)

            return renderWidth, renderHeight

        return None, None

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)

        if self.renderMode == RenderMode.Grid:
            self.paintGrid()

        elif self.img is not None and self.img.shape[0] > 0 and self.img.shape[1] > 0:
            renderWidth, renderHeight = self.updatePixMapDimensions()
            if renderWidth is None or renderHeight is None:
                return

            # Use opencv to resize the image for better quality, particularly on Windows
            if self.img is not None:
                interpolation = cv2.INTER_AREA if self.zoomFactor < 1 else cv2.INTER_CUBIC
                scaledPImg = cv2.resize(self.img, (renderWidth, renderHeight), interpolation=interpolation)
                newPixmap = QPixmap.fromImage(QImage(scaledPImg.data, scaledPImg.shape[1], scaledPImg.shape[0],
                                                    scaledPImg.shape[1] * 3, QImage.Format_BGR888))

            x: int = self.posX
            y: int = self.posY
            painter = QPainter(self)
            painter.drawPixmap(x, y, newPixmap)

            font = QFont("Arial", 12)
            painter.setFont(font)
            pen = QPen(QColor(255, 255, 255))
            painter.setPen(pen)

            fname1 = self.selectionManager.getBaseFilename()
            painter.drawText(5, newPixmap.height()-25, newPixmap.width()-5, 20, Qt.AlignLeft | Qt.AlignBottom, fname1)

            if self.renderMode == RenderMode.Split:
                fname2 = self.selectionManager.getCompareFilename(0)
                painter.drawText(0, newPixmap.height()-25,
                                 newPixmap.width()-5, 20, Qt.AlignRight | Qt.AlignBottom, fname2)

            painter.end()

    def translateAndScalePoints(self, points: List[List[float]], scale: float) -> List[QPointF]:
        return [QPointF(point[0] * scale + self.posX, point[1] * scale + self.posY) for point in points]

    def translateAndScaleMousePoint(self, x: int, y: int, scale: float) -> List[float]:
        return [(x - self.posX) / self.zoomFactor / scale, (y - self.posY) / self.zoomFactor / scale]

    def paintGrid(self):
        renderWidth, renderHeight = self.updatePixMapDimensions()

        pixmapWidth = self.width() // 2
        pixmapHeight = self.height() // 2
        x = self.posX * -1
        y = self.posY * -1

        padX = 0 if x > 0 else -x
        padY = 0 if y > 0 else -y

        fname1 = self.selectionManager.getBaseFilename()
        fname2 = self.selectionManager.getCompareFilename(0)
        fname3 = self.selectionManager.getCompareFilename(1)
        fname4 = self.selectionManager.getCompareFilename(2)

        pixmapQ1 = self.makeScaledPixmap(self.img1, x, y, pixmapWidth, pixmapHeight, renderWidth, renderHeight, fname1)
        pixmapQ2 = self.makeScaledPixmap(self.img2, x, y, pixmapWidth, pixmapHeight, renderWidth, renderHeight, fname2)
        pixmapQ3 = self.makeScaledPixmap(self.img3, x, y, pixmapWidth, pixmapHeight, renderWidth, renderHeight, fname3)
        pixmapQ4 = self.makeScaledPixmap(self.img4, x, y, pixmapWidth, pixmapHeight, renderWidth, renderHeight, fname4)

        painter = QPainter(self)
        painter.drawPixmap(padX, padY, pixmapQ1)
        painter.drawPixmap(padX + pixmapWidth, padY, pixmapQ2)
        painter.drawPixmap(padX, padY + pixmapHeight, pixmapQ3)
        painter.drawPixmap(padX + pixmapWidth, padY + pixmapHeight, pixmapQ4)

        painter.setPen(QPen(Qt.GlobalColor.green, 2, Qt.PenStyle.SolidLine))
        painter.drawLine(pixmapWidth-1, 0, pixmapWidth-1, self.height())
        painter.drawLine(0, pixmapHeight-1, self.width(), pixmapHeight-1)

        painter.end()


    # make a pixmap for a quadrant
    def makeScaledPixmap(self, img, x, y, w, h, renderWidth, renderHeight, fname):
        if img is None:
            return QPixmap(w, h)

        interpolation = cv2.INTER_AREA if self.zoomFactor < 1 else cv2.INTER_CUBIC
        scaledImg = cv2.resize(img, (renderWidth, renderHeight), interpolation=interpolation)

        pixmap = QPixmap.fromImage(QImage(scaledImg.data, scaledImg.shape[1], scaledImg.shape[0],
                                          scaledImg.shape[1] * 3, QImage.Format_BGR888))
        # crop
        pixmap = pixmap.copy(x, y, w, h)

        painter = QPainter(pixmap)
        font = QFont("Arial", 12)
        painter.setFont(font)
        pen = QPen(QColor(255, 255, 255))
        painter.setPen(pen)

        painter.drawText(0, pixmap.height()-25, pixmap.width()-5, 20, Qt.AlignRight | Qt.AlignBottom, fname)
        painter.end()

        return pixmap
