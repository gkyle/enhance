import os
import shutil
import sys
from typing import Optional
from PySide6.QtGui import (QPixmap, QGuiApplication)
from PySide6.QtCore import QThreadPool, QTimer, QPoint
from PySide6.QtWidgets import QWidget, QFileDialog, QMainWindow, QDialog, QApplication, QMenu
from functools import partial
import time
import cv2

from upscale.app import App, Operation
from upscale.lib.file import File, InputFile, OutputFile, PostProcess, PostProcessOperation
from upscale.ui.canvasLabel import CanvasLabel
from upscale.ui.filestrip import FileButton, FileStrip
from upscale.ui.progress import ProgressBarUpdater
from upscale.ui.selectionManager import SelectionManager
from upscale.ui.signals import AsyncWorker, emitLater, getSignals
from upscale.ui.ui_dialog_model_wrap import DialogModel
from upscale.ui.ui_interface import Ui_MainWindow
from upscale.ui.common import RenderMode, ZoomLevel, saveToCache


class MainWindow(QMainWindow):
    def __init__(self, app: App):
        QMainWindow.__init__(self)
        self.ui = Ui_AppWindow(app)
        self.ui.setupUi(self)
        self.show()

        # timer for updating GPU stats
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.ui.slotUpdateGPUStats)
        self.timer.start(10000)

    def center(self):
        screen = QGuiApplication.primaryScreen().availableGeometry()
        window_size = self.geometry()
        x = (screen.width() - window_size.width()) // 2
        y = (screen.height() - window_size.height()) // 2
        self.move(QPoint(x, y))

    def resizeEvent(self, event):
        self.ui.signals.windowResized.emit(event)
        return super().resizeEvent(event)

    def moveEvent(self, event):
        self.ui.signals.windowMoved.emit(event)
        return super().moveEvent(event)

    def closeEvent(self, event):
        self.ui.doCancelOp()
        self.timer.stop()
        event.accept()


class Ui_AppWindow(Ui_MainWindow):
    app = None

    def __init__(self, app: App):
        super().__init__()
        self.app = app
        self.op_queue = QThreadPool()
        self.op_queue.setMaxThreadCount(1)

    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)

        # Set window size
        screen_resolution = QGuiApplication.primaryScreen().availableGeometry()
        width = screen_resolution.width()
        height = screen_resolution.height()
        """
        if "windowSize" in self.persistentSettings and self.persistentSettings["windowSize"] is not None:
            MainWindow.resize(self.persistentSettings["windowSize"])
            if "windowPosition" in self.persistentSettings:
                MainWindow.move(self.persistentSettings["windowPosition"])
            else:
                MainWindow.center()
        else:
            if width > 2000 and height > 1200:
                MainWindow.resize(width*0.6, height*0.6)
            else:
                MainWindow.resize(width*0.90, height*0.90)
            MainWindow.center()
        """
        MainWindow.resize(width*0.80, height*0.90)
        MainWindow.center()

        self.signals = getSignals()
        self.selectionManager = SelectionManager(self.signals)

        # Replace placeholders
        self.canvas_main: CanvasLabel = replaceWidget(
            self.canvas_main,
            CanvasLabel(self.selectionManager, QPixmap(MainWindow.size())))

        # Hide optional panels
        self.frame_postprocess_sharpen.hide()

        # Bind events
        self.pushButton_cancelOp.clicked.connect(self.doCancelOp)
        self.pushButton_clear.clicked.connect(self.doClear)
        self.pushButton_open.clicked.connect(self.doOpen)
        self.pushButton_run.clicked.connect(self.doRun)
        self.checkBox_antialias.stateChanged.connect(self.canvas_main.setAntialias)
        self.pushButton_zoom.clicked.connect(self.showZoomMenu)
        self.pushButton_single.clicked.connect(lambda: self.canvas_main.setRenderMode(RenderMode.Single))
        self.pushButton_split.clicked.connect(lambda: self.canvas_main.setRenderMode(RenderMode.Split))
        self.pushButton_quad.clicked.connect(lambda: self.canvas_main.setRenderMode(RenderMode.Grid))

        self.horizontalSlider_blend.valueChanged.connect(self.onChangeBlendAmount)
        self.pushButton_postprocess_apply.clicked.connect(self.doApplyPostProcess)

        self.signals.incrementProgress.connect(self.slotIncrementProgressBar)
        self.signals.removeFile.connect(self.slotRemoveFile)
        self.signals.saveFile.connect(self.slotSaveFile)
        self.signals.changeZoom.connect(self.slotChangeZoom)
        self.signals.showFiles.connect(self.showFiles)

        self.fileStrip = FileStrip(self.frame_inputFile, self.frame_outputFiles, self.frame_filesContainer, self.app,
                                   self.selectionManager, self.signals.drawFileList)

        if self.app.baseFile is not None:
            self.selectionManager.selectBase(self.app.baseFile)

        for i in range(1, min(len(self.app.getFileList()), 4)):
            self.selectionManager.selectCompare(self.app.getFileList()[i])

    def doClear(self):
        self.app.setBaseFile(None)
        self.app.clearFileList()
        self.signals.drawFileList.emit(None)
        self.selectionManager.clear()

    def doOpen(self):
        path, _ = QFileDialog.getOpenFileName(filter="Image Files (*.jpg *.jpeg *.tif *.tiff, *.png)")
        if path is not None:
            file = InputFile(path)
            self.app.setBaseFile(path)
            self.app.clearFileList()
            self.signals.selectBaseFile.emit(file)
            self.signals.drawFileList.emit(file)

    def doRun(self):
        isGPuPresent = self.app.getGpuPresent()
        dialog = DialogModel(self.app, isGPuPresent)
        result = dialog.exec()
        if result == QDialog.Accepted:
            selectedModel = dialog.ui.listWidget.currentItem().text()
            doBlur = dialog.ui.checkBox_blur.isChecked()
            doBlend = dialog.ui.checkBox_blend.isChecked()
            blendFactor = dialog.ui.horizontalSlider_blend.value() / 100
            blurKernelSize = dialog.ui.horizontalSlider_blur.value()
            useGpu = dialog.ui.checkBox_gpu.isChecked()

            def f():
                file = self.selectionManager.getBaseFile()
                if file is not None:
                    progressUpdater = ProgressBarUpdater(
                        self.progressBar, self.label_progressBar, total=1, desc="Sharpen:")
                    result = self.app.doSharpen(file, selectedModel, doBlur,
                                                blurKernelSize, doBlend, blendFactor, progressUpdater.tick, useGpu)
                    if result is None:
                        return
                    self.signals.appendFile.emit(result)
                    self.selectionManager.selectCompare(result)

            worker = AsyncWorker(partial(f))
            self.op_queue.start(worker)

    def doCancelOp(self):
        self.app.doInterruptOperation()

    def slotIncrementProgressBar(self, progressUpdater: ProgressBarUpdater, total: int, increment: int, count: int, done: bool, data: Optional[File]):
        progressUpdater.total = total
        progressUpdater.update(increment)
        if data is not None:
            if isinstance(data, File):
                self.showFile(data)
            else:
                raise ValueError("Unknown data type")

    def slotRemoveFile(self, file: File, button: QWidget):
        self.app.removeFile(file)
        self.selectionManager.removeFile(file)
        self.fileStrip.removeButton(file)

    def slotSaveFile(self, file: OutputFile, button: FileButton):
        if file is not None:
            targetDir = os.path.dirname(self.selectionManager.getBaseFile().path)
            newPath = os.path.join(targetDir, os.path.basename(file.path))
            shutil.copyfile(file.path, newPath)

    def slotUpdateGPUStats(self):
        cudaStats = self.app.getGpuStats()
        if cudaStats is None:
            self.label_cuda.setText("NO GPU")
        else:
            self.label_cuda.setText("GPU: Free: {}GB | Total: {}GB".format(*cudaStats))

    def slotChangeZoom(self, zoomFactor: float):
        self.pushButton_zoom.setText(str(int(zoomFactor * 100)) + "%")

    def slotSetRenderMode(self, mode: RenderMode):
        self.canvas_main.setRenderMode(mode)

    def showZoomMenu(self):
        menu = QMenu("Select Zoom")
        menu.addAction("FIT", lambda: self.canvas_main.setZoomFactor(ZoomLevel.FIT))
        menu.addAction("FIT WIDTH", lambda: self.canvas_main.setZoomFactor(ZoomLevel.FIT_WIDTH))
        menu.addAction("FIT HEIGHT", lambda: self.canvas_main.setZoomFactor(ZoomLevel.FIT_HEIGHT))
        menu.addAction("100%", lambda: self.canvas_main.setZoomFactor("100%"))
        menu.addAction("200%", lambda: self.canvas_main.setZoomFactor("200%"))
        menu.addAction("400%", lambda: self.canvas_main.setZoomFactor("400%"))
        menu.exec(self.pushButton_zoom.mapToGlobal(self.pushButton_zoom.rect().bottomLeft()))

    def observeResizeEvent(self, event):
        self.persistentSettings["windowSize"] = event.size()
        self.app.updateWindowSettings(self.persistentSettings)

    def observeMoveEvent(self, event):
        self.persistentSettings["windowPosition"] = event.pos()
        self.app.updateWindowSettings(self.persistentSettings)

    def showFiles(self):
        self.frame_postprocess_sharpen.hide()
        compareFile = self.selectionManager.getCompareFile(0)
        if compareFile is not None:
            if type(compareFile) == OutputFile and compareFile.operation == Operation.Sharpen:
                self.horizontalSlider_blend.setValue(0)
                self.frame_postprocess_sharpen.show()

                if compareFile.postprocess is not None and \
                        PostProcessOperation.Blend in compareFile.postprocess:
                    if "blendFactor" in compareFile.postprocess[PostProcessOperation.Blend].parameters:
                        blendFactor = compareFile.postprocess[PostProcessOperation.Blend].parameters["blendFactor"]
                        self.horizontalSlider_blend.setValue(int(blendFactor * 100))

    def onChangeBlendAmount(self, value):
        self.label_blend_amt.setText(str(value) + "%")

    # TODO: Move implementation to op
    def doApplyPostProcess(self):
        compareFile = self.selectionManager.getCompareFile(0)
        if compareFile is not None:
            if type(compareFile) == OutputFile and compareFile.operation == Operation.Sharpen:
                baseFile = self.selectionManager.getBaseFile()
                blendFactor = self.horizontalSlider_blend.value() / 100

                baseImg = cv2.imread(baseFile.path, cv2.IMREAD_UNCHANGED)
                compareImg = cv2.imread(compareFile.origPath, cv2.IMREAD_UNCHANGED)
                newImg = cv2.addWeighted(baseImg, blendFactor, compareImg, 1 - blendFactor, 0)

                newPath = saveToCache(newImg, os.path.basename(baseFile.path))
                compareFile.setPath(newPath)
                compareFile.postprocess[PostProcessOperation.Blend] = \
                    PostProcess(PostProcessOperation.Blend, {"blendFactor": blendFactor})
                self.fileStrip.getButton(compareFile).updateTextLabel()

                self.signals.showFiles.emit()

                # TODO: Store metadata about post processing on the file
                # TODO: Consider moving files to a cache


def replaceWidget(placeHolder: QWidget, newWidget: QWidget):
    parentLayout = placeHolder.parent().layout()
    placeHolder.setParent(None)
    placeHolder.deleteLater
    parentLayout.addWidget(newWidget)
    return newWidget
