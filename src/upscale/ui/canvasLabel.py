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


MASK_COLORS = [
    [255, 0, 255],  # Magenta
    [0, 255, 255],  # Cyan
    [0, 255, 0],  # Green
    [255, 0, 0],  # Red
    [0, 0, 255],  # Blue
    [255, 255, 0],  # Yellow
    [255, 165, 0]   # Orange
]


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

        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Arial", 20, QFont.Bold))

        self.canvasImg = None  # Canvas img used for single and split modes
        self.img1 = None  # Seperate imgs used for grid mode
        self.img2 = None
        self.img3 = None
        self.img4 = None
        self.fraction = 0.5
        self.renderMode: RenderMode = RenderMode.Single
        self.renderMasks: bool = False

        self.setScaledContents(False)
        self.setStatusMessage()

    def updateFraction(self, value: int) -> None:
        self.fraction = value / 100
        self.canvasImg = None

        if self.renderMode == RenderMode.Split:
            self.repaint()

    # We load files here with 8bits/channel for consistent display via QPixmap. This doesn't impact how we work with channels in models.
    # TODO: Ensure img shapes match

    def showFiles(self, resetView=False):
        baseFile = self.selectionManager.getBaseFile()
        if baseFile is not None:
            self.img1 = cv2.imread(baseFile.path)
            if self.renderMasks:
                self.img1 = self.applyMasks(baseFile, self.img1)

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
            self.setStatusMessage()

        self.updateFraction(self.fraction * 100)
        if resetView:
            self.setZoomFactor(ZoomLevel.FIT)
        self.repaint()

    def applyMasks(self, file, img):
        if len(file.masks) > 0:
            for idx, mask in enumerate(file.masks):
                # If there are masks, we can use the first one to set the size of the image
                box = mask.box
                color = MASK_COLORS[idx % len(MASK_COLORS)]
                color.reverse()
                img = cv2.rectangle(img, (int(box[0]), int(
                    box[1])), (int(box[2]), int(box[3])), color, 2)
                img = cv2.putText(img, mask.label,
                                  (int(box[0]), int(box[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                mask_img = mask.mask
                if mask_img is not None and len(mask_img.shape) == 2:
                    mask_img = np.array(mask_img * 255).astype(np.uint8)
                    color_mask_img = np.zeros((mask_img.shape[0], mask_img.shape[1], 3), dtype=np.uint8)
                    color_mask_img[mask_img == 255] = color
                    img = cv2.addWeighted(img, 1.0, color_mask_img, 0.33, 0)
        return img

    def setStatusMessage(self) -> None:
        if self.img1 is None:
            self.setText("No images selected")
        else:
            h, w, _ = self.img1.shape
            if h == 0 or w == 0:
                self.setText("No images selected")
            else:
                self.setText("")

    def setRenderMode(self, renderMode: RenderMode) -> None:
        self.renderMode = renderMode
        self.showFiles(False)

    def resetZoomAndPosition(self, zoomFactor=1) -> None:
        self.zoomFactor = zoomFactor
        self.signals.changeZoom.emit(self.zoomFactor)

    def setZoom(self, dir: int, mouseX: int, mouseY: int) -> None:
        old_zoom_factor = self.zoomFactor
        if dir < 0:
            self.zoomFactor /= 1.1
        if dir > 0:
            self.zoomFactor *= 1.1

        if self.img1 is None or self.img1.size == 0:
            return

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
        elif self.renderMode == RenderMode.Split:
            if mouseX > self.width() // 2:
                mouseX = mouseX - self.width() // 2

            self.posX = mouseX - (mouseX - self.posX) * (self.zoomFactor / old_zoom_factor)
            self.posY = mouseY - (mouseY - self.posY) * (self.zoomFactor / old_zoom_factor)
        else:
            self.posX = mouseX - (mouseX - self.posX) * (self.zoomFactor / old_zoom_factor)
            self.posY = mouseY - (mouseY - self.posY) * (self.zoomFactor / old_zoom_factor)

        self.repaint()
        self.signals.changeZoom.emit(self.zoomFactor)

    def setShowMasks(self, showMasks: bool) -> None:
        self.renderMasks = showMasks
        self.showFiles(False)
        self.repaint()

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta: int = event.angleDelta().y()
        self.setZoom(delta, self.mouseX, self.mouseY)

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        super().mousePressEvent(ev)
        if ev.button() == Qt.LeftButton:
            self.dragX = ev.position().x() - self.posX
            self.dragY = ev.position().y() - self.posY

        if ev.button() == Qt.RightButton:
            fraction = ev.position().x() / self.width()
            self.updateFraction(int(100 * fraction))

    def mouseMoveEvent(self, ev: QMouseEvent) -> None:
        super().mouseMoveEvent(ev)
        self.mouseX = ev.position().x()
        self.mouseY = ev.position().y()

        # Dragging
        if ev.buttons() == Qt.LeftButton:
            self.posX = ev.position().x() - self.dragX
            self.posY = ev.position().y() - self.dragY
            self.repaint()

        # Sliding
        if ev.buttons() == Qt.RightButton:
            fraction = ev.position().x() / self.width()
            self.updateFraction(int(100 * fraction))
            self.repaint()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self.resetZoomAndPosition(self.getZoomFit())
        self.repaint()

    def getZoomFitWidth(self):
        imageWidth = self.img1.shape[1]
        labelWidth = self.width()
        if self.renderMode == RenderMode.Grid or self.renderMode == RenderMode.Split:
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

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)

        if self.img1 is None or self.img1.size == 0:
            return

        if self.renderMode == RenderMode.Single:
            self.paintSingle()

        elif self.renderMode == RenderMode.Split:
            self.paintSplit()

        elif self.renderMode == RenderMode.Grid:
            self.paintGrid()

    def shouldCenterSmallImage(self):
        h = self.img1.shape[0] * self.zoomFactor
        w = self.img1.shape[1] * self.zoomFactor
        return w <= self.width(), h <= self.height()

    def paintSingle(self):
        pixmapWidth = self.width()
        pixmapHeight = self.height()

        centerX, centerY = self.shouldCenterSmallImage()
        if centerX:
            x = 0
            padX = (self.width() - self.img1.shape[1] * self.zoomFactor) // 2
            self.posX = padX
        else:
            x = self.posX * -1
            padX = 0 if x > 0 else -x

        if centerY:
            y = 0
            padY = (self.height() - self.img1.shape[0] * self.zoomFactor) // 2
            self.posY = padY
        else:
            y = self.posY * -1
            padY = 0 if y > 0 else -y

        pixmapQ1 = self.makeScaledPixmap(self.img1, x, y, pixmapWidth, pixmapHeight,
                                         self.selectionManager.getBaseFilename())

        painter = QPainter(self)
        painter.drawPixmap(padX, padY, pixmapQ1)
        painter.end()

    def paintSplit(self):
        pixmapWidth = self.width() // 2
        pixmapHeight = self.height() // 1
        x = self.posX * -1 + pixmapWidth / 2
        y = self.posY * -1

        padX = 0 if x > 0 else -x
        padY = 0 if y > 0 else -y

        fname1 = self.selectionManager.getBaseFilename()
        fname2 = self.selectionManager.getCompareFilename(0)

        leftWidth = int(pixmapWidth * self.fraction * 2)
        rightWidth = self.width() - leftWidth
        pixmapQ1 = self.makeScaledPixmap(self.img1, x, y, leftWidth, pixmapHeight, fname1)
        h1 = self.img1.shape[0]
        h2 = self.img2.shape[0]
        scale = h2 / h1
        pixmapQ2 = self.makeScaledPixmap(self.img2, x, y, rightWidth, pixmapHeight, fname2, scale)

        painter = QPainter(self)
        painter.drawPixmap(padX, padY, pixmapQ1)
        painter.drawPixmap(padX + leftWidth, padY, pixmapQ2)

        painter.setPen(QPen(Qt.GlobalColor.green, 2, Qt.PenStyle.SolidLine))
        painter.drawLine(leftWidth-1, 0, leftWidth-1, self.height())

        painter.end()

    def paintGrid(self):
        pixmapWidth = self.width() // 2
        pixmapHeight = self.height() // 2
        x = self.posX * -1 + pixmapWidth / 2
        y = self.posY * -1 + pixmapHeight / 2

        padX = 0 if x > 0 else -x
        padY = 0 if y > 0 else -y

        fname1 = self.selectionManager.getBaseFilename()
        fname2 = self.selectionManager.getCompareFilename(0)
        fname3 = self.selectionManager.getCompareFilename(1)
        fname4 = self.selectionManager.getCompareFilename(2)

        h1 = self.img1.shape[0]
        h2 = self.img2.shape[0]
        h3 = self.img3.shape[0]
        h4 = self.img4.shape[0]

        pixmapQ1 = self.makeScaledPixmap(self.img1, x, y, pixmapWidth, pixmapHeight, fname1)
        pixmapQ2 = self.makeScaledPixmap(self.img2, x, y, pixmapWidth, pixmapHeight, fname2, h2 / h1)
        pixmapQ3 = self.makeScaledPixmap(self.img3, x, y, pixmapWidth, pixmapHeight, fname3, h3 / h1)
        pixmapQ4 = self.makeScaledPixmap(self.img4, x, y, pixmapWidth, pixmapHeight, fname4, h4 / h1)

        painter = QPainter(self)
        painter.drawPixmap(padX, padY, pixmapQ1)
        painter.drawPixmap(padX + pixmapWidth, padY, pixmapQ2)
        painter.drawPixmap(padX, padY + pixmapHeight, pixmapQ3)
        painter.drawPixmap(padX + pixmapWidth, padY + pixmapHeight, pixmapQ4)

        painter.setPen(QPen(Qt.GlobalColor.green, 2, Qt.PenStyle.SolidLine))
        painter.drawLine(pixmapWidth-1, 0, pixmapWidth-1, self.height())
        painter.drawLine(0, pixmapHeight-1, self.width(), pixmapHeight-1)

        painter.end()

    # Make a pixmap for a quadrant

    def makeScaledPixmap(self, img, x, y, w, h, fname, scale=1):
        if img is None:
            return QPixmap(w, h)

        renderWidth = int(img.shape[1] * self.zoomFactor / scale)
        renderHeight = int(img.shape[0] * self.zoomFactor / scale)

        interpolation = cv2.INTER_AREA if self.zoomFactor < 1 else cv2.INTER_CUBIC
        scaledImg = cv2.resize(img, (renderWidth, renderHeight), interpolation=interpolation)

        pixmap = QPixmap.fromImage(QImage(scaledImg.data, scaledImg.shape[1], scaledImg.shape[0],
                                          scaledImg.shape[1] * 3, QImage.Format_BGR888))
        # crop
        pixmap = pixmap.copy(x, y, w, h)

        # labels
        painter = QPainter(pixmap)
        font = QFont("Arial", 12)
        painter.setFont(font)
        pen = QPen(QColor(255, 255, 255))
        painter.setPen(pen)
        painter.drawText(0, pixmap.height()-25, pixmap.width()-5, 20, Qt.AlignRight | Qt.AlignBottom, fname)
        painter.end()

        return pixmap
