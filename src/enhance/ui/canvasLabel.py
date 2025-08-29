from typing import Optional
import cv2
import numpy as np
from PySide6.QtCore import (Qt)
from PySide6.QtGui import (QPainter, QPaintEvent, QWheelEvent, QMouseEvent,
                           QPixmap, QColor, QPen, QFont, QImage)
from PySide6.QtWidgets import QLabel, QWidget

from enhance.ui.selectionManager import SelectionManager
from enhance.ui.signals import Signals, getSignals
from enhance.ui.common import RenderMode, ZoomLevel


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

        self.img1 = None  # Seperate imgs used for grid mode
        self.img2 = None
        self.img3 = None
        self.img4 = None
        self.fraction = 0.5
        self.renderMode: RenderMode = RenderMode.Single
        self.renderMasks: bool = False

        self.setScaledContents(False)
        self.setStatusMessage()

    def updateFraction(self, value: float) -> None:
        self.fraction = value
        if self.fraction < 0:
            self.fraction = 0
        if self.fraction > 1:
            self.fraction = 1

        if self.renderMode == RenderMode.Split:
            self.repaint()

    def showFiles(self, resetView=False):
        # We load files here with 8bits/channel for consistent display via QPixmap. This doesn't impact how we work with channels in models.
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
        self.selectionManager.setRenderMode(renderMode)
        self.showFiles(False)

    def resetZoom(self, zoomFactor=1, resetPosition=True) -> None:
        if resetPosition:
            self.posX = 0
            self.posY = 0
        self.zoomFactor = zoomFactor
        self.signals.changeZoom.emit(self.zoomFactor)

    def setZoom(self, dir: int, mouseX: int, mouseY: int) -> None:
        oldZoomFactor = self.zoomFactor
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
            self.resetZoom(self.zoomFactor)

        # Calculate the new position to keep the mouse position at the same place
        if self.renderMode == RenderMode.Grid:
            if mouseX > self.width() // 2:
                mouseX = mouseX - self.width() // 2
            if mouseY > self.height() // 2:
                mouseY = mouseY - self.height() // 2

            self.posX = mouseX - (mouseX - self.posX) * (self.zoomFactor / oldZoomFactor)
            self.posY = mouseY - (mouseY - self.posY) * (self.zoomFactor / oldZoomFactor)
        else:
            self.posX = mouseX - (mouseX - self.posX) * (self.zoomFactor / oldZoomFactor)
            self.posY = mouseY - (mouseY - self.posY) * (self.zoomFactor / oldZoomFactor)

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

        if ev.button() == Qt.RightButton and self.renderMode == RenderMode.Split:
            fraction = ev.position().x() / self.width()
            self.updateFraction(fraction)

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
        if ev.buttons() == Qt.RightButton and self.renderMode == RenderMode.Split:
            fraction = ev.position().x() / self.width()
            self.updateFraction(fraction)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self.resetZoom(self.getZoomFit())
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
            self.resetZoom(self.getZoomFit())
        elif zoomFactor == ZoomLevel.FIT_WIDTH:
            self.resetZoom(self.getZoomFitWidth())
        elif zoomFactor == ZoomLevel.FIT_HEIGHT:
            self.resetZoom(self.getZoomFitHeight())
        elif "%" in zoomFactor:
            zoomFactor = zoomFactor.replace("%", "")
            try:
                zoomFactor = int(zoomFactor) / 100
                self.resetZoom(zoomFactor, False)
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

    def maybeClampImage(self, scale=1):
        # Recenter image if it fits within viewport
        # Clamp image if position is out of bounds
        h = int(self.img1.shape[0] * self.zoomFactor)
        w = int(self.img1.shape[1] * self.zoomFactor)

        shouldRecenterX = w <= self.width() // scale
        if shouldRecenterX:
            self.posX = int(
                (self.width() / scale - self.img1.shape[1] * self.zoomFactor) / 2)
        else:
            if self.posX > 0:
                self.posX = 0
            elif int(self.width() / scale) - self.posX > w:
                self.posX = int(self.width() / scale) - w

        shouldRecenterY = h <= self.height() // scale
        if shouldRecenterY:
            self.posY = int(
                (self.height() / scale - self.img1.shape[0] * self.zoomFactor) / 2)
        else:
            if self.posY > 0:
                self.posY = 0
            elif int(self.height() / scale) - self.posY > h:
                self.posY = int(self.height() / scale) - h

    def paintSingle(self):
        pixmapWidth = self.width()
        pixmapHeight = self.height()

        self.maybeClampImage()
        padX = self.posX if self.posX > 0 else 0
        padY = self.posY if self.posY > 0 else 0

        painter = QPainter(self)
        pixmapQ1 = self.makeScaledPixmap(self.img1, self.posX, self.posY, pixmapWidth, pixmapHeight,
                                         self.selectionManager.getBaseFilename())
        painter.drawPixmap(padX, padY, pixmapQ1)
        painter.end()

    def paintSplit(self):
        pixmapWidth = self.width()
        pixmapHeight = self.height()

        self.maybeClampImage()
        padX = self.posX if self.posX > 0 else 0
        padY = self.posY if self.posY > 0 else 0

        splitX = int(pixmapWidth * self.fraction)
        if splitX < padX:
            splitX = padX
        if splitX > pixmapWidth - padX:
            splitX = pixmapWidth - padX

        painter = QPainter(self)
        pixmapQ1 = self.makeScaledPixmap(self.img1, self.posX, self.posY, splitX - padX, pixmapHeight,
                                         self.selectionManager.getBaseFilename())
        painter.drawPixmap(padX, padY, pixmapQ1)

        if splitX < pixmapWidth - padX:
            pixmapQ2 = self.makeScaledPixmap(self.img2, self.posX-splitX, self.posY, pixmapWidth-splitX, pixmapHeight,
                                             self.selectionManager.getCompareFilename(0), self.img2.shape[0]/self.img1.shape[0])
            painter.drawPixmap(splitX, padY, pixmapQ2)

        painter.setPen(QPen(Qt.GlobalColor.green, 2, Qt.PenStyle.SolidLine))
        painter.drawLine(splitX-1, 0, splitX-1, self.height())

        painter.end()

    def paintGrid(self):
        pixmapWidth = self.width() // 2
        pixmapHeight = self.height() // 2
        self.maybeClampImage(scale=2)
        padX = self.posX if self.posX > 0 else 0
        padY = self.posY if self.posY > 0 else 0

        pixmapQ1 = self.makeScaledPixmap(
            self.img1, self.posX, self.posY, pixmapWidth, pixmapHeight, self.selectionManager.getBaseFilename())
        pixmapQ2 = self.makeScaledPixmap(self.img2, self.posX, self.posY, pixmapWidth, pixmapHeight,
                                         self.selectionManager.getCompareFilename(0), self.img2.shape[0] / self.img1.shape[0])
        pixmapQ3 = self.makeScaledPixmap(self.img3, self.posX, self.posY, pixmapWidth, pixmapHeight,
                                         self.selectionManager.getCompareFilename(1), self.img3.shape[0] / self.img1.shape[0])
        pixmapQ4 = self.makeScaledPixmap(self.img4, self.posX, self.posY, pixmapWidth, pixmapHeight,
                                         self.selectionManager.getCompareFilename(2), self.img4.shape[0] / self.img1.shape[0])

        painter = QPainter(self)
        painter.drawPixmap(padX, padY, pixmapQ1)
        painter.drawPixmap(padX + pixmapWidth, padY, pixmapQ2)
        painter.drawPixmap(padX, padY + pixmapHeight, pixmapQ3)
        painter.drawPixmap(padX + pixmapWidth, padY + pixmapHeight, pixmapQ4)

        painter.setPen(QPen(Qt.GlobalColor.green, 2, Qt.PenStyle.SolidLine))
        painter.drawLine(pixmapWidth-1, 0, pixmapWidth-1, self.height())
        painter.drawLine(0, pixmapHeight-1, self.width(), pixmapHeight-1)

        painter.end()

    def makeScaledPixmap(self, img, x, y, w, h, fname, scale=1):
        # Make a pixmap for a quadrant
        if img is None or w <= 0 or h <= 0:
            return QPixmap(w, h)

        renderWidth = int(img.shape[1] * self.zoomFactor / scale)
        renderHeight = int(img.shape[0] * self.zoomFactor / scale)

        interpolation = cv2.INTER_AREA if self.zoomFactor < 1 else cv2.INTER_CUBIC
        scaledImg = cv2.resize(img, (renderWidth, renderHeight), interpolation=interpolation)

        pixmap = QPixmap.fromImage(QImage(scaledImg.data, scaledImg.shape[1], scaledImg.shape[0],
                                          scaledImg.shape[1] * 3, QImage.Format_BGR888))
        # crop
        cx = -x if x < 0 else 0
        cy = -y if y < 0 else 0
        pixmap = pixmap.copy(cx, cy, w, h)

        # labels
        painter = QPainter(pixmap)
        font = QFont("Arial", 12)
        painter.setFont(font)
        pen = QPen(QColor(255, 255, 255))
        painter.setPen(pen)
        painter.drawText(0, pixmap.height()-25, pixmap.width()-5, 20, Qt.AlignRight | Qt.AlignBottom, fname)
        painter.end()

        return pixmap
