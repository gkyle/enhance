
from PySide6.QtWidgets import QDialog, QButtonGroup

from upscale.app import App
from upscale.ui.ui_dialog_model import Ui_Dialog


class DialogModel(QDialog):
    def __init__(self, app: App, doScale: bool):
        super().__init__()
        self.ui = UI_DialogModel(app, doScale)
        self.ui.setupUi(self)


class UI_DialogModel(Ui_Dialog):
    def __init__(self, app: App, doScale: bool):
        super().__init__()
        self.app = app
        self.doScale = doScale

    def setupUi(self, dialog: QDialog):
        super().setupUi(dialog)
        filters = []
        if self.doScale:
            filters.append("x1")
            filters.append("X1")
        self.listWidget.addItems(self.app.listModels(filters))
        self.listWidget.setCurrentRow(0)

        self.device_combobox.clear()
        self.device_combobox.addItem("cpu")
        for gpuId, gpuName in self.app.getGpuNames():
            self.device_combobox.addItem(f"{gpuName} ({gpuId})", userData=gpuId)
        if (self.device_combobox.count() > 1):
            self.device_combobox.setCurrentIndex(1)  # Default to first GPU if available

        tileSizes = [64, 128, 256, 512]
        self.tileSize_combobox.clear()
        self.tileSize_combobox.addItems([str(size) for size in tileSizes])
        self.tileSize_combobox.setCurrentIndex(self.tileSize_combobox.count() - 1)  # Default to max tile size

        tilePadding = [0, 8, 16, 32]
        self.tilePadding_combobox.clear()
        self.tilePadding_combobox.addItems([str(padding) for padding in tilePadding])
        self.tilePadding_combobox.setCurrentIndex(self.tilePadding_combobox.count() - 1)  # Default to max padding
