from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QTableWidgetItem

from ui_dialog_taskqueue import Ui_Dialog
from upscale.ui.signals import getSignals

class DialogTaskQueue(QDialog):
    def __init__(self, history=None):
        super().__init__()
        self.ui = UI_DialogTaskQueue(history)
        self.ui.setupUi(self)

class UI_DialogTaskQueue(Ui_Dialog):

    def __init__(self, history=None):
        super().__init__()
        self.history = history
        self.signals = getSignals()
        self.signals.taskCompleted.connect(self.updateTable)

    def setupUi(self, dialog):
        super().setupUi(dialog)      

        self.tableWidget_history.setColumnCount(3)
        self.tableWidget_history.setHorizontalHeaderLabels(["Task", "Status", "Latency"])
        self.tableWidget_history.setColumnWidth(0, 450)
        self.tableWidget_history.setColumnWidth(1, 100)
        self.tableWidget_history.setColumnWidth(2, 100)
        self.tableWidget_history.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
        self.tableWidget_history.horizontalHeader().setStretchLastSection(True)

        self.updateTable()

    def updateTable(self):
        self.tableWidget_history.clearContents()
        self.tableWidget_history.setRowCount(0)
        for i, status in enumerate(reversed(self.history)):
            self.tableWidget_history.insertRow(i)
            self.tableWidget_history.setItem(i, 0, QTableWidgetItem(status.label))
            self.tableWidget_history.setItem(i, 1, QTableWidgetItem(status.status))
            if status.latency is not None:
                self.tableWidget_history.setItem(i, 2, QTableWidgetItem(f"{status.latency:.2f}s"))
