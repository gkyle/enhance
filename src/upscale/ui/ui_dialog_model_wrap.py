
from PySide6.QtWidgets import QDialog, QButtonGroup

from upscale.app import App
from upscale.ui.ui_dialog_model import Ui_Dialog


class DialogModel(QDialog):
    def __init__(self, app: App, gpuPresent: bool):
        super().__init__()
        self.ui = UI_DialogModel(app)
        self.ui.setupUi(self, gpuPresent)


class UI_DialogModel(Ui_Dialog):
    def __init__(self, app: App):
        super().__init__()
        self.app = app

    def setupUi(self, dialog: QDialog, gpuPresent: bool):
        super().setupUi(dialog)
        self.listWidget.addItems(self.app.listModels())
        self.listWidget.setCurrentRow(0)

        self.checkBox_blend.stateChanged.connect(self.toggleBlend)
        self.checkBox_blur.stateChanged.connect(self.toggleBlur)

        self.horizontalSlider_blend.enanled = False
        self.horizontalSlider_blur.enabled = False

        if not gpuPresent:
            self.checkBox_gpu.setEnabled(False)
            self.checkBox_gpu.setChecked(False)
        else:
            self.checkBox_gpu.setEnabled(True)
            self.checkBox_gpu.setChecked(True)

    def toggleBlur(self, checked: bool):
        if checked:
            self.horizontalSlider_blur.setEnabled(True)
        else:
            self.horizontalSlider_blur.setEnabled(False)

    def toggleBlend(self, checked: bool):
        if checked:
            self.horizontalSlider_blend.setEnabled(True)
        else:
            self.horizontalSlider_blend.setEnabled(False)
