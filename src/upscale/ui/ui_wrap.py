import os
import re
import shutil
from typing import Optional
from PySide6.QtGui import QGuiApplication, QFontMetrics
from PySide6.QtCore import QThreadPool, QTimer, QPoint, Qt
from PySide6.QtWidgets import (
    QWidget,
    QFileDialog,
    QMainWindow,
    QDialog,
    QMenu,
)
from functools import partial

from upscale.app import App, Operation
from upscale.lib.file import (
    BlendOperation,
    DownscaleOperation,
    File,
    InputFile,
    Label,
    OutputFile,
)
from upscale.ui.canvasLabel import CanvasLabel
from upscale.ui.filestrip import FileButton, FileStrip
from upscale.ui.progress import ProgressBarUpdater
from upscale.ui.selectionManager import SelectionManager
from upscale.ui.signals import AsyncWorker, WorkerHistory, getSignals
from upscale.ui.ui_dialog_model_manager_wrap import DialogModelManager
from upscale.ui.ui_dialog_model_wrap import DialogModel
from upscale.ui.ui_dialog_taskqueue_wrap import DialogTaskQueue
from upscale.ui.ui_interface import Ui_MainWindow
from upscale.ui.common import RenderMode, ZoomLevel


class MainWindow(QMainWindow):
    def __init__(self, app: App):
        QMainWindow.__init__(self)
        self.ui = Ui_AppWindow(app)
        self.ui.setupUi(self)
        self.show()

        # timer for updating GPU stats
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.ui.updateGPUStats)
        self.timer.start(2000)

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
        self.ui.cancelOp()
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

        MainWindow.resize(width * 0.80, height * 0.90)
        MainWindow.center()

        self.signals = getSignals()
        self.selectionManager = SelectionManager(self.signals)

        # Replace placeholders
        self.canvas_main: CanvasLabel = replaceWidget(
            self.canvas_main, CanvasLabel(self.selectionManager)
        )

        # Hide optional panels
        self.group_compare.hide()
        self.group_postprocess.hide()

        # Bind events
        self.pushButton_cancelOp.clicked.connect(self.cancelOp)
        self.pushButton_clear.clicked.connect(self.clear)
        self.pushButton_open.clicked.connect(self.showOpenDialog)
        self.pushButton_run.clicked.connect(self.showSharpen)
        self.pushButton_upscale.clicked.connect(self.showUpscale)
        self.pushButton_denoise.clicked.connect(self.showDenoise)
        self.pushButton_mask.clicked.connect(self.runAutoMask)
        self.pushButton_modelManager.clicked.connect(lambda: self.showModelManager())
        self.pushButton_zoom.clicked.connect(self.showZoomMenu)
        self.pushButton_taskQueue.clicked.connect(self.showTaskQueue)
        self.pushButton_single.clicked.connect(
            lambda: self.canvas_main.setRenderMode(RenderMode.Single)
        )
        self.pushButton_split.clicked.connect(
            lambda: self.canvas_main.setRenderMode(RenderMode.Split)
        )
        self.pushButton_quad.clicked.connect(
            lambda: self.canvas_main.setRenderMode(RenderMode.Grid)
        )
        self.checkBox_render_masks.stateChanged.connect(
            lambda state: self.canvas_main.setShowMasks(state != 0)
        )

        self.horizontalSlider_blend.valueChanged.connect(self.onChangeBlendAmount)
        self.pushButton_postprocess_apply.clicked.connect(self.applyPostProcess)

        self.signals.incrementProgress.connect(self.incrementProgressBar)
        self.signals.removeFile.connect(self.removeFile)
        self.signals.saveFile.connect(self.saveFile)
        self.signals.changeZoom.connect(self.changeZoom)
        self.signals.selectCompareFile.connect(self.renderPostProcess)

        self.fileStrip = FileStrip(
            self.frame_inputFile,
            self.frame_outputFiles,
            self.frame_filesContainer,
            self.app,
            self.selectionManager,
            self.signals.drawFileList,
        )

        if self.app.baseFile is not None:
            self.selectionManager.selectBase(self.app.baseFile)

        for i in range(1, min(len(self.app.getFileList()), 4)):
            self.selectionManager.selectCompare(self.app.getFileList()[i])

        self.renderBaseFile()
        if self.app.doDetect:
            self.runDetectSubjects()
        else:
            self.frame_mask.setVisible(False)
            self.frame_subject.setVisible(False)

    def clear(self):
        self.app.setBaseFile(None)
        self.app.clearFileList()
        self.signals.drawFileList.emit(None)
        self.selectionManager.clear()

    def showOpenDialog(self):
        path, _ = QFileDialog.getOpenFileName(
            filter="Image Files (*.jpg *.jpeg *.tif *.tiff, *.png)"
        )
        if path is not None and len(path) > 0:
            file = InputFile(path)
            self.app.setBaseFile(path)
            self.app.clearFileList()
            self.signals.selectBaseFile.emit(file, True)
            self.signals.drawFileList.emit(file)
            self.renderBaseFile()
            self.runDetectSubjects()

    def showModelDialog(self, operation):
        dialog = DialogModel(self.app, [operation])
        result = dialog.exec()
        if result == QDialog.Accepted:
            selectedItems = dialog.ui.listWidget.selectedItems()
            tileSize = int(dialog.ui.tileSize_combobox.currentText())
            tilePadding = int(dialog.ui.tilePadding_combobox.currentText())
            gpuId = dialog.ui.device_combobox.currentData()
            maintainScale = operation != Operation.Upscale

            desc = "Sharpen"
            if operation == Operation.Upscale:
                desc = "Upscale"
            elif operation == Operation.Denoise:
                desc = "Denoise"

            def f(selectedModel):
                file = self.selectionManager.getBaseFile()
                if file is not None:
                    progressUpdater = ProgressBarUpdater(
                        self.progressBar, self.label_progressBar, total=1, desc=desc
                    )
                    result = self.app.runModel(
                        file,
                        selectedModel,
                        progressUpdater.tick,
                        tileSize,
                        tilePadding,
                        maintainScale,
                        gpuId,
                    )
                    if result is None:
                        return
                    self.signals.appendFile.emit(result)
                    self.signals.selectCompareFile.emit(result)
                    self.signals.taskCompleted.emit()

            for selectedItem in selectedItems:
                selectedModel = selectedItem.text()

                worker = AsyncWorker(
                    partial(f, selectedModel), label=f"{desc}: {selectedModel}"
                )
                self.op_queue.start(worker)

    def showSharpen(self):
        self.showModelDialog(Operation.Sharpen.value)

    def showUpscale(self):
        self.showModelDialog(Operation.Upscale.value)

    def showDenoise(self):
        self.showModelDialog(Operation.Denoise.value)

    def showTaskQueue(self):
        dialog = DialogTaskQueue(WorkerHistory)
        result = dialog.exec()

    def runAutoMask(self):
        file = self.selectionManager.getBaseFile()
        desc = "Generating Masks"

        def f():
            if file is not None:
                progressUpdater = ProgressBarUpdater(
                    self.progressBar,
                    self.label_progressBar,
                    total=1,
                    desc=desc,
                )
                self.app.runAutoMask(file, progressUpdater.tick)
                self.signals.showFiles.emit(False)
                self.checkBox_render_masks.setChecked(True)
                self.signals.taskCompleted.emit()

        worker = AsyncWorker(partial(f), label=desc)
        self.op_queue.start(worker)

    def showModelManager(self):
        dialog = DialogModelManager(self.app)
        result = dialog.exec()

    def runDetectSubjects(self):
        file = self.selectionManager.getBaseFile()
        desc = "Detecting Subjects"

        def f():
            if file is not None:
                progressUpdater = ProgressBarUpdater(
                    self.progressBar,
                    self.label_progressBar,
                    total=1,
                    desc=desc,
                )
                result = self.app.runDetectSubjects(file, progressUpdater.tick)
                if result is not None:
                    for idx, label in enumerate(result["labels"]):
                        box = result["bboxes"][idx]
                        file.labels.append(Label(label, box))
                self.renderBaseFile()
                self.signals.showFiles.emit(False)
                self.signals.taskCompleted.emit()

        worker = AsyncWorker(partial(f), label=desc)
        self.op_queue.start(worker)

    def cancelOp(self):
        self.app.interruptOperation()

    def incrementProgressBar(
        self,
        progressUpdater: ProgressBarUpdater,
        total: int,
        increment: int,
        count: int,
        done: bool,
        data: Optional[File],
    ):
        progressUpdater.total = total
        progressUpdater.update(increment)
        if data is not None:
            if isinstance(data, File):
                self.showFile(data)
            else:
                raise ValueError("Unknown data type")

    def removeFile(self, file: File, button: QWidget):
        self.app.removeFile(file)
        self.selectionManager.removeFile(file)
        self.fileStrip.removeButton(file)

    def saveFile(self, file: OutputFile, button: FileButton):
        if file is not None:
            targetDir = os.path.dirname(self.selectionManager.getBaseFile().path)
            newPath = os.path.join(targetDir, os.path.basename(file.path))
            shutil.copyfile(file.path, newPath)

    def updateGPUStats(self):
        cudaStats = self.app.getGpuStats()
        if cudaStats is None:
            self.label_cuda.setText("NO GPU")
        else:
            self.label_cuda.setText("GPU: Free: {}GB | Total: {}GB".format(*cudaStats))

    def changeZoom(self, zoomFactor: float):
        self.pushButton_zoom.setText(str(int(zoomFactor * 100)) + "%")

    def showZoomMenu(self):
        menu = QMenu("Select Zoom")
        menu.addAction("FIT", lambda: self.canvas_main.setZoomFactor(ZoomLevel.FIT))
        menu.addAction(
            "FIT WIDTH", lambda: self.canvas_main.setZoomFactor(ZoomLevel.FIT_WIDTH)
        )
        menu.addAction(
            "FIT HEIGHT", lambda: self.canvas_main.setZoomFactor(ZoomLevel.FIT_HEIGHT)
        )
        menu.addAction("100%", lambda: self.canvas_main.setZoomFactor("100%"))
        menu.addAction("200%", lambda: self.canvas_main.setZoomFactor("200%"))
        menu.addAction("400%", lambda: self.canvas_main.setZoomFactor("400%"))
        menu.exec(
            self.pushButton_zoom.mapToGlobal(self.pushButton_zoom.rect().bottomLeft())
        )

    def observeResizeEvent(self, event):
        self.persistentSettings["windowSize"] = event.size()
        self.app.updateWindowSettings(self.persistentSettings)

    def observeMoveEvent(self, event):
        self.persistentSettings["windowPosition"] = event.pos()
        self.app.updateWindowSettings(self.persistentSettings)

    def renderBaseFile(self):
        file = self.selectionManager.getBaseFile()
        if file is not None:
            self.drawLabelText(self.label_filename_base, file.basename, maybeElide=True)

            baseImg = file.loadUnchanged()
            self.drawLabelShape(self.label_shape_base, baseImg)

            if file.labels is not None:
                self.drawLabelText(
                    self.label_subjects,
                    ", ".join([label.label for label in file.labels]),
                    maybeElide=True,
                )

    def renderPostProcess(self, compareFile: OutputFile):
        self.group_compare.hide()
        self.group_postprocess.hide()
        self.group_postprocess.hide()
        if compareFile is None:
            compareFile = self.selectionManager.getCompareFile(0)
        if compareFile is not None:
            if (
                type(compareFile) == OutputFile
                and compareFile.operation == Operation.Sharpen
            ):
                self.drawLabelText(
                    self.label_filename, compareFile.basename, maybeElide=True
                )
                self.drawLabelText(self.label_opname, compareFile.operation.value)
                self.drawLabelText(
                    self.label_modelname, compareFile.model, maybeElide=True
                )

                compareImg = compareFile.loadUnchanged()
                self.drawLabelShape(self.label_shape, compareImg)

                self.horizontalSlider_blend.setValue(0)

                hasScaleOp = False
                for postop in compareFile.postops:
                    if isinstance(postop, DownscaleOperation):
                        hasScaleOp = True
                        scale = str(int(1 / postop.scale)) + "X"
                        self.drawLabelText(self.label_scale, scale)
                    if isinstance(postop, BlendOperation):
                        factor = postop.factor
                        self.horizontalSlider_blend.setValue(factor * 100)

                self.frame_blur.hide()
                if not hasScaleOp:
                    self.frame_scale.hide()
                else:
                    self.frame_scale.show()
                self.frame_blend.show()

                self.group_compare.show()
                self.group_postprocess.show()

    def onChangeBlendAmount(self, value):
        self.label_blend_amt.setText(str(value) + "%")

    # TODO: Move implementation to op
    def applyPostProcess(self):
        compareFile = self.selectionManager.getCompareFile(0)
        if compareFile is not None:
            if (
                type(compareFile) == OutputFile
                and compareFile.operation == Operation.Sharpen
            ):
                blendFactor = self.horizontalSlider_blend.value() / 100

                hasBlendOp = False
                for postop in compareFile.postops:
                    if isinstance(postop, BlendOperation):
                        postop.factor = blendFactor
                        hasBlendOp = True
                if not hasBlendOp:
                    compareFile.postops.append(BlendOperation(blendFactor))

                compareFile.applyPostProcessAndSave()

                self.fileStrip.getButton(compareFile).updateTextLabel()
                self.signals.showFiles.emit(False)

    def drawLabelText(self, label, text, maybeElide=False):
        if maybeElide:
            metrics = QFontMetrics(label.font())
            clippedText = metrics.elidedText(text, Qt.TextElideMode.ElideMiddle, 200)
            label.setText(clippedText)
        else:
            label.setText(text)
        label.setStyleSheet("color: #aaa;")

    def drawLabelShape(self, label, img):
        text = ""
        if img is not None:
            h, w, _ = img.shape
            dt = img.dtype.name
            dtn = re.findall(r"\d+", dt)
            text = f"{h}H X {w}W  {int(dtn[0])}-bit"
        self.drawLabelText(label, text, maybeElide=False)


def replaceWidget(placeHolder: QWidget, newWidget: QWidget):
    parentLayout = placeHolder.parent().layout()
    placeHolder.setParent(None)
    placeHolder.deleteLater
    parentLayout.addWidget(newWidget)
    return newWidget
