import os
import re
import shutil
from typing import Optional, List
from PySide6.QtGui import QGuiApplication, QFontMetrics
from PySide6.QtCore import QThreadPool, QTimer, QPoint, Qt
from PySide6.QtWidgets import (
    QWidget,
    QFileDialog,
    QMainWindow,
    QDialog,
    QMenu,
    QMessageBox,
    QVBoxLayout,
)
from functools import partial
import logging

logger = logging.getLogger(__name__)

from enhance.app import App
from enhance.lib.file import (
    File,
    InputFile,
    Label,
    OutputFile,
    Operation,
    AppliedOperation,
)
from enhance.ui.canvasLabel import CanvasLabel
from enhance.ui.filestrip import FileButton, FileStrip
from enhance.ui.operation_widget import OperationWidget
from enhance.ui.progress import ProgressBarUpdater
from enhance.ui.selectionManager import SAVE_STATE_CHANGED, SelectionManager
from enhance.ui.signals import AsyncWorker, WorkerHistory, getSignals
from enhance.ui.ui_dialog_model_manager_wrap import DialogModelManager
from enhance.ui.ui_dialog_model_wrap import DialogModel
from enhance.ui.ui_dialog_taskqueue_wrap import DialogTaskQueue
from enhance.ui.ui_interface import Ui_MainWindow
from enhance.ui.common import RenderMode, ZoomLevel


class MainWindow(QMainWindow):
    def __init__(self, app: App):
        QMainWindow.__init__(self)
        self.ui = Ui_AppWindow(app)
        self.ui.setupUi(self)
        self.show()

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
        self.ui.closeEvent(event)

class Ui_AppWindow(Ui_MainWindow):
    app = None

    def __init__(self, app: App):
        super().__init__()
        self.app = app
        self.op_queue = QThreadPool()
        self.op_queue.setMaxThreadCount(1)

    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)
        self.MainWindow = MainWindow

        # timer for updating GPU stats
        self.timer = QTimer(MainWindow)
        self.timer.timeout.connect(self.updateGPUStats)
        self.timer.start(2000)

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

        # Track operation widgets for the operations list
        self.operationWidgets: List[OperationWidget] = []
        self.currentCompareFile: OutputFile = None

        # Set up the operations container within group_postprocess
        self._setupOperationsContainer()

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

        self.signals.incrementProgress.connect(self.incrementProgressBar)
        self.signals.removeFile.connect(self.removeFile)
        self.signals.saveFile.connect(self.saveFile)
        self.signals.changeZoom.connect(self.changeZoom)
        self.signals.selectCompareFile.connect(self.renderPostProcess)
        self.signals.createOutputFile.connect(self.createOutputFile)
        self.signals.updateOperationWidgetMasks.connect(
            self._updateOperationWidgetMasks
        )

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

        self.updateGPUStats()

    def clear(self):
        self.app.setBaseFile(None)
        self.app.clearFileList()
        self.signals.drawFileList.emit(None)
        self.selectionManager.clear()
        self._clearOperationWidgets()
        self.currentCompareFile = None
        self.group_compare.hide()
        self.group_postprocess.hide()

    def showOpenDialog(self):
        path, _ = QFileDialog.getOpenFileName(
            filter="Image Files (*.jpg *.jpeg *.tif *.tiff, *.png)"
        )
        if path is not None and len(path) > 0:
            file = InputFile(path)
            self.app.setBaseFile(path)
            self.app.clearFileList()
            self._clearOperationWidgets()
            self.currentCompareFile = None
            self.group_compare.hide()
            self.group_postprocess.hide()
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
            maintainScale = dialog.ui.checkBox_maintainScale.isChecked()
            selectedMasks = dialog.ui.getSelectedMasks()

            desc = "Sharpen"
            if operation == Operation.Upscale:
                desc = "Upscale"
            elif operation == Operation.Denoise:
                desc = "Denoise"

            def f(selectedModel):
                baseFile = self.selectionManager.getBaseFile()
                compareFile = self.selectionManager.getCompareFile(0)

                if baseFile is None:
                    return

                progressUpdater = ProgressBarUpdater(
                    self.progressBar, self.label_progressBar, total=1, desc=desc
                )

                # If we have a selected OutputFile, append operation to it
                if compareFile is not None and isinstance(compareFile, OutputFile):
                    result = self.app.runModelOnExisting(
                        compareFile,
                        selectedModel,
                        progressUpdater.tick,
                        tileSize,
                        tilePadding,
                        maintainScale,
                        gpuId,
                        operation,
                        masks=selectedMasks if selectedMasks else None,
                    )
                    if result is None:
                        return
                    # Update the file button to reflect changes
                    self.signals.selectCompareFile.emit(result)
                    self.signals.taskCompleted.emit()
                else:
                    # No OutputFile selected, create a new one from base file
                    result = self.app.runModel(
                        baseFile,
                        selectedModel,
                        progressUpdater.tick,
                        tileSize,
                        tilePadding,
                        maintainScale,
                        gpuId,
                        operation,
                        masks=selectedMasks if selectedMasks else None,
                    )
                    if result is None:
                        return
                    self.signals.appendFile.emit(result)
                    self.signals.selectCompareFile.emit(result)
                    self.signals.taskCompleted.emit()

            for selectedItem in selectedItems:
                selectedModel = selectedItem.text()

                worker = AsyncWorker(
                    partial(f, selectedModel),
                    label=f"{desc}: {selectedModel}",
                    device=gpuId if gpuId is not None else "cpu",
                )
                self.op_queue.start(worker)

    def showSharpen(self):
        self.showModelDialog(Operation.Sharpen)

    def showUpscale(self):
        self.showModelDialog(Operation.Upscale)

    def showDenoise(self):
        self.showModelDialog(Operation.Denoise)

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
                self.signals.updateOperationWidgetMasks.emit()
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

    def createOutputFile(self):
        """Create a new OutputFile from the current base file"""
        baseFile = self.selectionManager.getBaseFile()
        if baseFile is None:
            return

        # Create a new OutputFile with the base file's image as starting point
        outputFile = self.app.createOutputFile(baseFile)
        if outputFile is not None:
            self.app.rawFiles.append(outputFile)
            self.signals.appendFile.emit(outputFile)
            self.selectionManager.selectCompare(outputFile)

    def saveFile(self, file: OutputFile, button: FileButton):
        if file is not None:
            targetDir = os.path.dirname(self.selectionManager.getBaseFile().path)
            file.saveImage(targetDir)
            self.signals.updateIndicator.emit(file, SAVE_STATE_CHANGED)

    def updateGPUStats(self):
        gpu_data_available = self.app.gpuInfo.getGpuPresent()
        if gpu_data_available:
            self.frame_gpu_label.setVisible(False)
            gpu_utilization = self.app.gpuInfo.getGpuUtilization()
            if gpu_utilization is None:
                self.frame_gpu_util.setVisible(False)
            else:
                self.frame_gpu_util.setVisible(True)
                self.progressBar_gpu_util.setValue(gpu_utilization * 100)
                self.progressBar_gpu_util.setFormat(
                    "GPU: {:.0f}%".format(gpu_utilization * 100)
                )

            gpu_mem_total = self.app.gpuInfo.getGpuMemeoryTotal()
            gpu_mem_available = self.app.gpuInfo.getGpuMemoryAvailable()
            if gpu_mem_total is None:
                self.frame_gpu_mem.setVisible(False)
            else:
                mem_util = (gpu_mem_total - gpu_mem_available) / gpu_mem_total
                self.progressBar_gpu_mem.setValue(mem_util * 100)
                self.progressBar_gpu_mem.setFormat(
                    "GPU Mem: {:.0f}%  {:.1f}GB / {:.1f}GB".format(
                        mem_util * 100, (gpu_mem_total - gpu_mem_available), gpu_mem_total
                    )
                )

            gpu_data_available = (gpu_utilization is not None) or (gpu_mem_total is not None)

        if not gpu_data_available:
            self.frame_gpu_label.setVisible(True)
            self.frame_gpu_util.setVisible(False)
            self.frame_gpu_mem.setVisible(False)
            self.label_gpu.setText("NO GPU")

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

    def _setupOperationsContainer(self):
        """Set up the container for dynamically-created operation widgets."""
        # Clear the existing postprocess group contents and replace with a vertical layout
        # Hide the old static controls
        self.frame_blur.hide()
        self.frame_scale.hide()
        self.frame_blend.hide()
        self.pushButton_postprocess_apply.hide()

        # Create a container frame for operation widgets
        self.operationsContainer = QWidget(self.group_postprocess)
        self.operationsContainerLayout = QVBoxLayout(self.operationsContainer)
        self.operationsContainerLayout.setContentsMargins(0, 0, 0, 0)
        self.operationsContainerLayout.setSpacing(4)

        # Add the container to the postprocess group layout
        self.verticalLayout_20.insertWidget(0, self.operationsContainer)

        # Set up debounce timer for strength changes
        self.strengthDebounceTimer = QTimer()
        self.strengthDebounceTimer.setSingleShot(True)
        self.strengthDebounceTimer.setInterval(500)
        self.strengthDebounceTimer.timeout.connect(self._applyStrengthChanges)

    def _clearOperationWidgets(self):
        """Clear all operation widgets from the container."""
        for widget in self.operationWidgets:
            widget.deleteLater()
        self.operationWidgets.clear()

    def _createOperationWidgets(self, compareFile: OutputFile):
        """Create operation widgets for each operation in the file."""
        self._clearOperationWidgets()

        # Get available masks from the base file
        availableMasks = []
        if self.app.baseFile and hasattr(self.app.baseFile, "masks"):
            availableMasks = self.app.baseFile.masks

        for op in compareFile.operations:
            widget = OperationWidget(op, availableMasks, self.operationsContainer)
            widget.strengthChanged.connect(self._onOperationStrengthChanged)
            widget.masksChanged.connect(self._onOperationMasksChanged)
            self.operationsContainerLayout.addWidget(widget)
            self.operationWidgets.append(widget)

    def _updateOperationWidgetMasks(self):
        """Update available masks on all operation widgets after mask generation."""
        if not self.app.baseFile or not hasattr(self.app.baseFile, "masks"):
            return

        availableMasks = self.app.baseFile.masks
        for widget in self.operationWidgets:
            widget.updateAvailableMasks(availableMasks)

    def _onOperationStrengthChanged(self, operation: AppliedOperation, strength: float):
        """Handle strength change from an operation widget - debounced."""
        # Restart the debounce timer on each change
        self.strengthDebounceTimer.start()

    def _onOperationMasksChanged(
        self, operation: AppliedOperation, masks: list
    ):
        """When masks change, we need to re-run the operation from scratch since
        the mask affects which pixels are processed by the model.
        """
        # Check if anything actually changed - compare labels and inverted states
        currentMaskKey = set((m.uniqueLabel, m.inverted) for m in operation.masks)
        newMaskKey = set((m.uniqueLabel, m.inverted) for m in masks)
        if currentMaskKey == newMaskKey:
            return

        # Update the operation's masks
        operation.masks = masks

        # Re-run this operation and all following operations
        self._rerunOperationChain(operation)

    def _applyStrengthChanges(self):
        """Apply strength changes after debounce period."""
        if self.currentCompareFile is None:
            return

        compareFile = self.currentCompareFile
        if not isinstance(compareFile, OutputFile):
            return

        # Update strengths from widgets and reapply
        anyChanged = False
        for widget in self.operationWidgets:
            op = widget.operation
            if op.supportsStrength():
                newStrength = widget.getStrength()
                if op.strength != newStrength:
                    op.strength = newStrength
                    compareFile.reapplyStrength(op)
                    anyChanged = True

        if anyChanged:
            button = self.fileStrip.getButton(compareFile)
            if button:
                button.updateTextLabel()
            self.signals.showFiles.emit(False)
            self.signals.updateIndicator.emit(compareFile, SAVE_STATE_CHANGED)

    def _rerunOperationChain(self, startOperation: AppliedOperation):
        """Re-run operations starting from the given operation."""

        if self.currentCompareFile is None or not isinstance(
            self.currentCompareFile, OutputFile
        ):
            return

        compareFile = self.currentCompareFile
        opIndex = compareFile.getOperationIndex(startOperation)
        if opIndex < 0:
            logger.warning("Operation not found in file")
            return

        def rerunOps():
            progressUpdater = ProgressBarUpdater(
                self.progressBar,
                self.label_progressBar,
                total=1,
                desc="Re-running operations",
            )

            success = self.app.rerunOperationChain(
                compareFile,
                opIndex,
                progressCallback=progressUpdater.tick,
            )

            if not success:
                logger.error("Failed to re-run operation chain")
                return

            # Update UI
            self.signals.selectCompareFile.emit(compareFile)
            self.signals.taskCompleted.emit()

        # Run async
        worker = AsyncWorker(
            rerunOps,
            label="Re-running operations",
            device=self.app.gpuInfo.getPreferredDevice(),
        )
        self.op_queue.start(worker)

    def renderPostProcess(self, compareFile: OutputFile):
        self.group_compare.hide()
        self.group_postprocess.hide()

        if compareFile is None:
            compareFile = self.selectionManager.getCompareFile(0)

        self.currentCompareFile = compareFile

        if compareFile is not None and isinstance(compareFile, OutputFile):
            if compareFile.operations:
                # Update the compare file info panel
                firstOp = compareFile.getFirstOperation()
                self.drawLabelText(
                    self.label_filename, compareFile.basename, maybeElide=True
                )
                self.drawLabelText(
                    self.label_opname, firstOp.operation_type.value if firstOp else ""
                )
                self.drawLabelText(
                    self.label_modelname,
                    firstOp.model if firstOp else "",
                    maybeElide=True,
                )

                compareImg = compareFile.loadUnchanged()
                self.drawLabelShape(self.label_shape, compareImg)

                # Create operation widgets for all operations
                self._createOperationWidgets(compareFile)

                self.group_compare.show()
                self.group_postprocess.show()

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

    def closeEvent(self, event):
        self.cancelOp()
        self.app.clearCacheExpiredFiles()
        if self.app.hasUnsavedChanges():
            reply = QMessageBox.question(
                self.MainWindow,
                "Unsaved Changes",
                "You have unsaved files. Do you really want to quit?",
                buttons=QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                event.ignore()
                return

        self.timer.stop()
        event.accept()


def replaceWidget(placeHolder: QWidget, newWidget: QWidget):
    parentLayout = placeHolder.parent().layout()
    placeHolder.setParent(None)
    placeHolder.deleteLater
    parentLayout.addWidget(newWidget)
    return newWidget
