from enum import Enum
from typing import List
from PySide6.QtWidgets import QDialog, QButtonGroup, QListWidget, QCheckBox
from PySide6.QtCore import Qt

from enhance.app import App
from enhance.lib.file import Operation, Mask
from enhance.ui.ui_dialog_model import Ui_Dialog
from enhance.ui.mask_selector import MaskSelectorButton


class DialogModel(QDialog):
    def __init__(self, app: App, operations: List[Operation]):
        super().__init__()
        self.ui = UI_DialogModel(app, operations)
        self.ui.setupUi(self)


class UI_DialogModel(Ui_Dialog):
    def __init__(self, app: App, filterOperations: List[Operation]):
        super().__init__()
        self.app = app
        self.filterOperations = [op.value.lower() for op in filterOperations]
        self.maskSelector: MaskSelectorButton = None

    def setupUi(self, dialog: QDialog):
        super().setupUi(dialog)

        self.frame_nomodels.hide()
        self.listWidget.setSelectionMode(QListWidget.ExtendedSelection)

        self.pushButton_modelManager.clicked.connect(self.showModelManager)
        self.drawModelList()
        self.drawMaskList()

        if Operation.Upscale.value.lower() in self.filterOperations:
            self.checkBox_maintainScale.setChecked(False)
        else:
            self.checkBox_maintainScale.setChecked(True)

    def drawModelList(self):
        models = self.app.getModels(installed=True)
        if len(models) == 0:
            self.frame_nomodels.show()
        else:
            self.frame_nomodels.hide()

        if len(self.filterOperations) > 0:
            models = {
                path: model
                for path, model in models.items()
                if model["operation"] is not None
                and len(model["operation"]) > 0
                and model["operation"][0] in self.filterOperations
            }

        self.listWidget.clear()
        self.listWidget.addItems(models.keys())
        self.listWidget.setCurrentRow(0)

        self.device_combobox.clear()
        self.device_combobox.addItem("cpu")
        for gpuId, gpuName in self.app.gpuInfo.getGpuNames():
            self.device_combobox.addItem(f"{gpuName} ({gpuId})", userData=gpuId)
        if self.device_combobox.count() > 1:
            self.device_combobox.setCurrentIndex(1)  # Default to first GPU if available

        tileSizes = [64, 128, 256, 512, 1024]
        self.tileSize_combobox.clear()
        self.tileSize_combobox.addItems([str(size) for size in tileSizes])
        self.tileSize_combobox.setCurrentIndex(self.tileSize_combobox.count() - 2)

        tilePadding = [0, 8, 16, 32]
        self.tilePadding_combobox.clear()
        self.tilePadding_combobox.addItems([str(padding) for padding in tilePadding])
        self.tilePadding_combobox.setCurrentIndex(
            self.tilePadding_combobox.count() - 1
        )  # Default to max padding

    def drawMaskList(self):
        """Setup the mask selector button."""
        # Hide the placeholder
        self.label_placeholder.hide()

        # Get masks from base file
        masks = []
        if (
            self.app.baseFile
            and hasattr(self.app.baseFile, "masks")
            and self.app.baseFile.masks
        ):
            masks = self.app.baseFile.masks
            self.frame_masks.show()
        else:
            self.frame_masks.hide()
            return

        # Create mask selector if not already created
        if self.maskSelector is None:
            self.maskSelector = MaskSelectorButton()
            self.frame_masksSelect.layout().addWidget(self.maskSelector)

        self.maskSelector.setMasks(masks)

    def getSelectedMasks(self) -> List[Mask]:
        """Get the list of selected masks with per-mask inverted property set."""
        if self.maskSelector:
            return self.maskSelector.getSelection()
        return []

    def showModelManager(self):
        from enhance.ui.ui_dialog_model_manager_wrap import DialogModelManager

        dialog = DialogModelManager(self.app)
        result = dialog.exec()
        self.drawModelList()
