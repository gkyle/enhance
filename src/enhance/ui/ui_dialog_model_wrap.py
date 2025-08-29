from enum import Enum
from typing import List
from PySide6.QtWidgets import QDialog, QButtonGroup, QListWidget

from enhance.app import App, Operation
from enhance.ui.ui_dialog_model import Ui_Dialog


class DialogModel(QDialog):
    def __init__(self, app: App, operations: List[Operation]):
        super().__init__()
        self.ui = UI_DialogModel(app, operations)
        self.ui.setupUi(self)


class UI_DialogModel(Ui_Dialog):
    def __init__(self, app: App, filterOperations: List[Operation]):
        super().__init__()
        self.app = app
        self.filterOperations = filterOperations

    def setupUi(self, dialog: QDialog):
        super().setupUi(dialog)

        self.listWidget.setSelectionMode(QListWidget.ExtendedSelection)

        self.pushButton_modelManager.clicked.connect(self.showModelManager)
        self.drawModelList()

    def drawModelList(self):
        models = self.app.getModels(installed=True)

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
        for gpuId, gpuName in self.app.getGpuNames():
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

    def showModelManager(self):
        from enhance.ui.ui_dialog_model_manager_wrap import DialogModelManager

        dialog = DialogModelManager(self.app)
        result = dialog.exec()
        self.drawModelList()
