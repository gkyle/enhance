# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_modelKrZoFU.ui'
##
## Created by: Qt User Interface Compiler version 6.4.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QDialog,
    QDialogButtonBox, QFrame, QGridLayout, QLabel,
    QListWidget, QListWidgetItem, QSizePolicy, QSlider,
    QVBoxLayout, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(400, 300)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(Dialog)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")

        self.verticalLayout_2.addWidget(self.label)

        self.listWidget = QListWidget(self.frame)
        self.listWidget.setObjectName(u"listWidget")

        self.verticalLayout_2.addWidget(self.listWidget)


        self.verticalLayout.addWidget(self.frame)

        self.frame_2 = QFrame(Dialog)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.gridLayout = QGridLayout(self.frame_2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalSlider_blur = QSlider(self.frame_2)
        self.horizontalSlider_blur.setObjectName(u"horizontalSlider_blur")
        self.horizontalSlider_blur.setEnabled(False)
        self.horizontalSlider_blur.setMinimum(1)
        self.horizontalSlider_blur.setMaximum(11)
        self.horizontalSlider_blur.setSingleStep(2)
        self.horizontalSlider_blur.setValue(5)
        self.horizontalSlider_blur.setOrientation(Qt.Horizontal)
        self.horizontalSlider_blur.setTickPosition(QSlider.TicksBothSides)
        self.horizontalSlider_blur.setTickInterval(2)

        self.gridLayout.addWidget(self.horizontalSlider_blur, 0, 1, 1, 1)

        self.checkBox_blur = QCheckBox(self.frame_2)
        self.checkBox_blur.setObjectName(u"checkBox_blur")

        self.gridLayout.addWidget(self.checkBox_blur, 0, 0, 1, 1)

        self.horizontalSlider_blend = QSlider(self.frame_2)
        self.horizontalSlider_blend.setObjectName(u"horizontalSlider_blend")
        self.horizontalSlider_blend.setEnabled(False)
        self.horizontalSlider_blend.setValue(50)
        self.horizontalSlider_blend.setOrientation(Qt.Horizontal)

        self.gridLayout.addWidget(self.horizontalSlider_blend, 1, 1, 1, 1)

        self.checkBox_blend = QCheckBox(self.frame_2)
        self.checkBox_blend.setObjectName(u"checkBox_blend")

        self.gridLayout.addWidget(self.checkBox_blend, 1, 0, 1, 1)

        self.checkBox_gpu = QCheckBox(self.frame_2)
        self.checkBox_gpu.setObjectName(u"checkBox_gpu")

        self.gridLayout.addWidget(self.checkBox_gpu, 2, 0, 1, 1)


        self.verticalLayout.addWidget(self.frame_2)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Choose Model:", None))
        self.checkBox_blur.setText(QCoreApplication.translate("Dialog", u"Mid Process Blur", None))
        self.checkBox_blend.setText(QCoreApplication.translate("Dialog", u"Blend Original", None))
        self.checkBox_gpu.setText(QCoreApplication.translate("Dialog", u"Use GPU", None))
    # retranslateUi

