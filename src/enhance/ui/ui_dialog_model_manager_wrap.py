from PySide6.QtWidgets import QDialog, QTableWidgetItem, QPushButton, QAbstractItemView

from enhance.app import App
from enhance.ui.ui_dialog_model_manager import Ui_Dialog

from PySide6.QtCore import Qt
import json


class DialogModelManager(QDialog):
    def __init__(self, app: App):
        super().__init__()
        self.ui = UI_DialogModelManager(app)
        self.ui.setupUi(self)


class UI_DialogModelManager(Ui_Dialog):
    def __init__(self, app: App):
        super().__init__()
        self.app = app

    def setupUi(self, dialog: QDialog):
        super().setupUi(dialog)

        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget.setColumnCount(6)
        self.tableWidget.setHorizontalHeaderLabels(
            ["Operation", "Name", "Subject", "", "Author", "Description"]
        )
        self.tableWidget.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)

        self.comboBox_filterOperation.currentTextChanged.connect(
            self.setSelectOperation
        )
        self.comboBox_filterSubject.currentTextChanged.connect(self.setSelectSubject)
        self.pushButton_refresh.clicked.connect(self.doRefresh)

        self.tableWidget.setColumnWidth(0, 100)
        self.tableWidget.setColumnWidth(1, 300)
        self.tableWidget.setColumnWidth(2, 100)
        self.tableWidget.setColumnWidth(3, 100)
        self.tableWidget.setColumnWidth(4, 100)
        self.tableWidget.setColumnWidth(5, 300)

        self.selectedOperation = "All"
        self.selectedSubject = "All"

        self.drawModelList(True)

    def drawModelList(self, init=False):
        operations = set()
        subjects = set()

        modelList = self.app.getModels()
        self.tableWidget.setRowCount(0)
        for modelName in modelList:
            row = self.tableWidget.rowCount()
            model = modelList[modelName]

            operation = None
            subject = None
            if (
                "operation" in model
                and isinstance(model["operation"], list)
                and len(model["operation"]) > 0
            ):
                operation = model["operation"][0]
                operations.add(operation)

            if (
                "subject" in model
                and isinstance(model["subject"], list)
                and len(model["subject"]) > 0
            ):
                subject = model["subject"][0]
                subjects.add(subject)

            if self.selectedOperation != "All" and operation != self.selectedOperation:
                continue

            if self.selectedSubject != "All" and subject != self.selectedSubject:
                continue

            self.tableWidget.insertRow(row)
            if operation is not None:
                self.tableWidget.setItem(
                    row, 0, QTableWidgetItem(", ".join(model["operation"]))
                )

            self.tableWidget.setItem(row, 1, QTableWidgetItem(model["name"]))

            if "subject" in model:
                self.tableWidget.setItem(
                    row, 2, QTableWidgetItem(", ".join(model["subject"]))
                )

            if model.get("installed"):
                item = QTableWidgetItem("Installed")
                item.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(row, 3, item)
            else:
                installButton = QPushButton("Install")
                installButton.clicked.connect(
                    lambda checked, path=modelName: self.doInstall(path)
                )
                self.tableWidget.setCellWidget(row, 3, installButton)

            self.tableWidget.setItem(row, 4, QTableWidgetItem(model["author"]))
            self.tableWidget.setItem(row, 5, QTableWidgetItem(model["description"]))

        # Populate the filter combo boxes once
        if init:
            self.comboBox_filterOperation.clear()
            self.comboBox_filterOperation.addItem("All")
            self.comboBox_filterOperation.addItems(sorted(operations))
            self.selectedOperation = "All"

            self.comboBox_filterSubject.clear()
            self.comboBox_filterSubject.addItem("All")
            self.comboBox_filterSubject.addItems(sorted(subjects))
            self.selectedSubject = "All"

    def setSelectOperation(self, operation: str):
        self.selectedOperation = operation
        self.drawModelList()

    def setSelectSubject(self, subject: str):
        self.selectedSubject = subject
        self.drawModelList()

    def doInstall(self, path: str):
        self.app.fetchModel(path)
        self.drawModelList()

    def doRefresh(self):
        self.app.refreshModelList()
        self.drawModelList()
