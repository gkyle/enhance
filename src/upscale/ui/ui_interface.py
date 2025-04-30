# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'interfacejLHkJA.ui'
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
from PySide6.QtWidgets import (QAbstractScrollArea, QApplication, QCheckBox, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLayout,
    QMainWindow, QProgressBar, QPushButton, QScrollArea,
    QSizePolicy, QSlider, QVBoxLayout, QWidget)
import icons_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1600, 1200)
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy1)
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.toolbar = QFrame(self.centralwidget)
        self.toolbar.setObjectName(u"toolbar")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.toolbar.sizePolicy().hasHeightForWidth())
        self.toolbar.setSizePolicy(sizePolicy2)
        self.toolbar.setMaximumSize(QSize(16777215, 40))
        self.toolbar.setFrameShape(QFrame.NoFrame)
        self.toolbar.setFrameShadow(QFrame.Plain)
        self.toolbar.setLineWidth(0)
        self.gridLayout = QGridLayout(self.toolbar)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setHorizontalSpacing(0)
        self.gridLayout.setContentsMargins(0, 0, 6, 0)
        self.frame = QFrame(self.toolbar)
        self.frame.setObjectName(u"frame")
        sizePolicy2.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy2)
        self.frame.setMinimumSize(QSize(300, 0))
        self.frame.setFrameShape(QFrame.NoFrame)
        self.frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_9 = QHBoxLayout(self.frame)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.label_title = QLabel(self.frame)
        self.label_title.setObjectName(u"label_title")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.label_title.setFont(font)

        self.horizontalLayout_9.addWidget(self.label_title)


        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)

        self.frame_4 = QFrame(self.toolbar)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setMinimumSize(QSize(244, 0))
        self.frame_4.setMaximumSize(QSize(244, 16777215))
        self.frame_4.setFrameShape(QFrame.NoFrame)
        self.frame_4.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_7 = QHBoxLayout(self.frame_4)
        self.horizontalLayout_7.setSpacing(6)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(9, -1, 0, -1)
        self.label_cuda = QLabel(self.frame_4)
        self.label_cuda.setObjectName(u"label_cuda")

        self.horizontalLayout_7.addWidget(self.label_cuda)


        self.gridLayout.addWidget(self.frame_4, 0, 3, 1, 1)

        self.frame_3 = QFrame(self.toolbar)
        self.frame_3.setObjectName(u"frame_3")
        sizePolicy2.setHeightForWidth(self.frame_3.sizePolicy().hasHeightForWidth())
        self.frame_3.setSizePolicy(sizePolicy2)
        self.frame_3.setFrameShape(QFrame.NoFrame)
        self.frame_3.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_10 = QHBoxLayout(self.frame_3)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.frame_progressBar = QFrame(self.frame_3)
        self.frame_progressBar.setObjectName(u"frame_progressBar")
        sizePolicy2.setHeightForWidth(self.frame_progressBar.sizePolicy().hasHeightForWidth())
        self.frame_progressBar.setSizePolicy(sizePolicy2)
        self.frame_progressBar.setMinimumSize(QSize(0, 16))
        self.frame_progressBar.setFrameShape(QFrame.NoFrame)
        self.frame_progressBar.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_11 = QHBoxLayout(self.frame_progressBar)
        self.horizontalLayout_11.setSpacing(6)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.label_progressBar = QLabel(self.frame_progressBar)
        self.label_progressBar.setObjectName(u"label_progressBar")
        font1 = QFont()
        font1.setPointSize(12)
        self.label_progressBar.setFont(font1)

        self.horizontalLayout_11.addWidget(self.label_progressBar)

        self.progressBar = QProgressBar(self.frame_progressBar)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setMinimumSize(QSize(250, 30))
        self.progressBar.setMaximumSize(QSize(180, 16777215))
        font2 = QFont()
        font2.setPointSize(11)
        self.progressBar.setFont(font2)
        self.progressBar.setValue(0)

        self.horizontalLayout_11.addWidget(self.progressBar)

        self.pushButton_cancelOp = QPushButton(self.frame_progressBar)
        self.pushButton_cancelOp.setObjectName(u"pushButton_cancelOp")
        self.pushButton_cancelOp.setMinimumSize(QSize(30, 0))
        self.pushButton_cancelOp.setMaximumSize(QSize(30, 16777215))
        font3 = QFont()
        font3.setPointSize(9)
        self.pushButton_cancelOp.setFont(font3)
        icon = QIcon()
        icon.addFile(u":/icons32/x.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_cancelOp.setIcon(icon)
        self.pushButton_cancelOp.setIconSize(QSize(24, 24))

        self.horizontalLayout_11.addWidget(self.pushButton_cancelOp)


        self.horizontalLayout_10.addWidget(self.frame_progressBar)

        self.frame_2 = QFrame(self.frame_3)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setMinimumSize(QSize(25, 0))
        self.frame_2.setFrameShape(QFrame.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Raised)

        self.horizontalLayout_10.addWidget(self.frame_2)

        self.checkBox_antialias = QCheckBox(self.frame_3)
        self.checkBox_antialias.setObjectName(u"checkBox_antialias")
        self.checkBox_antialias.setChecked(False)

        self.horizontalLayout_10.addWidget(self.checkBox_antialias)

        self.pushButton_single = QPushButton(self.frame_3)
        self.pushButton_single.setObjectName(u"pushButton_single")
        self.pushButton_single.setMinimumSize(QSize(40, 40))
        icon1 = QIcon()
        icon1.addFile(u":/icons32/square.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_single.setIcon(icon1)
        self.pushButton_single.setIconSize(QSize(24, 24))

        self.horizontalLayout_10.addWidget(self.pushButton_single)

        self.pushButton_split = QPushButton(self.frame_3)
        self.pushButton_split.setObjectName(u"pushButton_split")
        self.pushButton_split.setMinimumSize(QSize(40, 40))
        icon2 = QIcon()
        icon2.addFile(u":/icons32/columns.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_split.setIcon(icon2)
        self.pushButton_split.setIconSize(QSize(24, 24))

        self.horizontalLayout_10.addWidget(self.pushButton_split)

        self.pushButton_quad = QPushButton(self.frame_3)
        self.pushButton_quad.setObjectName(u"pushButton_quad")
        self.pushButton_quad.setMinimumSize(QSize(40, 40))
        icon3 = QIcon()
        icon3.addFile(u":/icons32/grid.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_quad.setIcon(icon3)
        self.pushButton_quad.setIconSize(QSize(24, 24))

        self.horizontalLayout_10.addWidget(self.pushButton_quad)

        self.pushButton_zoom = QPushButton(self.frame_3)
        self.pushButton_zoom.setObjectName(u"pushButton_zoom")
        self.pushButton_zoom.setMinimumSize(QSize(0, 40))
        self.pushButton_zoom.setFont(font1)
        icon4 = QIcon()
        icon4.addFile(u":/icons32/zoom-in.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_zoom.setIcon(icon4)
        self.pushButton_zoom.setIconSize(QSize(24, 24))

        self.horizontalLayout_10.addWidget(self.pushButton_zoom)


        self.gridLayout.addWidget(self.frame_3, 0, 1, 1, 1, Qt.AlignRight)


        self.verticalLayout_2.addWidget(self.toolbar)

        self.frame1 = QFrame(self.centralwidget)
        self.frame1.setObjectName(u"frame1")
        sizePolicy3 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(1)
        sizePolicy3.setHeightForWidth(self.frame1.sizePolicy().hasHeightForWidth())
        self.frame1.setSizePolicy(sizePolicy3)
        self.frame1.setFrameShape(QFrame.NoFrame)
        self.frame1.setFrameShadow(QFrame.Plain)
        self.horizontalLayout = QHBoxLayout(self.frame1)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.frame_main = QFrame(self.frame1)
        self.frame_main.setObjectName(u"frame_main")
        sizePolicy4 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy4.setHorizontalStretch(1)
        sizePolicy4.setVerticalStretch(1)
        sizePolicy4.setHeightForWidth(self.frame_main.sizePolicy().hasHeightForWidth())
        self.frame_main.setSizePolicy(sizePolicy4)
        self.frame_main.setStyleSheet(u"background-color: rgb(32,32,32);")
        self.frame_main.setFrameShape(QFrame.NoFrame)
        self.frame_main.setFrameShadow(QFrame.Raised)
        self.verticalLayout = QVBoxLayout(self.frame_main)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.canvas_main = QLabel(self.frame_main)
        self.canvas_main.setObjectName(u"canvas_main")
        self.canvas_main.setFrameShape(QFrame.NoFrame)
        self.canvas_main.setFrameShadow(QFrame.Raised)
        self.canvas_main.setLineWidth(1)

        self.verticalLayout.addWidget(self.canvas_main)


        self.horizontalLayout.addWidget(self.frame_main)

        self.frame_sidebar = QFrame(self.frame1)
        self.frame_sidebar.setObjectName(u"frame_sidebar")
        sizePolicy5 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.frame_sidebar.sizePolicy().hasHeightForWidth())
        self.frame_sidebar.setSizePolicy(sizePolicy5)
        self.frame_sidebar.setMinimumSize(QSize(244, 0))
        self.frame_sidebar.setMaximumSize(QSize(100, 16777215))
        self.frame_sidebar.setFrameShape(QFrame.StyledPanel)
        self.frame_sidebar.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.frame_sidebar)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.pushButton_open = QPushButton(self.frame_sidebar)
        self.pushButton_open.setObjectName(u"pushButton_open")

        self.verticalLayout_3.addWidget(self.pushButton_open)

        self.pushButton_run = QPushButton(self.frame_sidebar)
        self.pushButton_run.setObjectName(u"pushButton_run")

        self.verticalLayout_3.addWidget(self.pushButton_run)

        self.line = QFrame(self.frame_sidebar)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_3.addWidget(self.line)

        self.pushButton_clear = QPushButton(self.frame_sidebar)
        self.pushButton_clear.setObjectName(u"pushButton_clear")

        self.verticalLayout_3.addWidget(self.pushButton_clear)

        self.line_3 = QFrame(self.frame_sidebar)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.HLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_3.addWidget(self.line_3)

        self.label_4 = QLabel(self.frame_sidebar)
        self.label_4.setObjectName(u"label_4")

        self.verticalLayout_3.addWidget(self.label_4, 0, Qt.AlignHCenter)

        self.line_2 = QFrame(self.frame_sidebar)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_3.addWidget(self.line_2)

        self.frame_postprocess_sharpen = QFrame(self.frame_sidebar)
        self.frame_postprocess_sharpen.setObjectName(u"frame_postprocess_sharpen")
        self.frame_postprocess_sharpen.setFrameShape(QFrame.StyledPanel)
        self.frame_postprocess_sharpen.setFrameShadow(QFrame.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.frame_postprocess_sharpen)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label_blend = QLabel(self.frame_postprocess_sharpen)
        self.label_blend.setObjectName(u"label_blend")

        self.verticalLayout_4.addWidget(self.label_blend)

        self.frame_5 = QFrame(self.frame_postprocess_sharpen)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setFrameShape(QFrame.NoFrame)
        self.frame_5.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_5)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label_blend_amt = QLabel(self.frame_5)
        self.label_blend_amt.setObjectName(u"label_blend_amt")

        self.horizontalLayout_2.addWidget(self.label_blend_amt)

        self.horizontalSlider_blend = QSlider(self.frame_5)
        self.horizontalSlider_blend.setObjectName(u"horizontalSlider_blend")
        self.horizontalSlider_blend.setOrientation(Qt.Horizontal)
        self.horizontalSlider_blend.setTickPosition(QSlider.TicksBothSides)
        self.horizontalSlider_blend.setTickInterval(5)

        self.horizontalLayout_2.addWidget(self.horizontalSlider_blend)


        self.verticalLayout_4.addWidget(self.frame_5)

        self.pushButton_postprocess_apply = QPushButton(self.frame_postprocess_sharpen)
        self.pushButton_postprocess_apply.setObjectName(u"pushButton_postprocess_apply")

        self.verticalLayout_4.addWidget(self.pushButton_postprocess_apply)


        self.verticalLayout_3.addWidget(self.frame_postprocess_sharpen)


        self.horizontalLayout.addWidget(self.frame_sidebar, 0, Qt.AlignTop)


        self.verticalLayout_2.addWidget(self.frame1)

        self.frame_filesContainer = QFrame(self.centralwidget)
        self.frame_filesContainer.setObjectName(u"frame_filesContainer")
        sizePolicy6 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy6.setHorizontalStretch(100)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.frame_filesContainer.sizePolicy().hasHeightForWidth())
        self.frame_filesContainer.setSizePolicy(sizePolicy6)
        self.frame_filesContainer.setMinimumSize(QSize(160, 200))
        self.frame_filesContainer.setFrameShape(QFrame.NoFrame)
        self.frame_filesContainer.setFrameShadow(QFrame.Raised)
        self.verticalLayout_6 = QVBoxLayout(self.frame_filesContainer)
        self.verticalLayout_6.setSpacing(6)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.verticalLayout_6.setContentsMargins(6, 0, 6, 0)
        self.frame_10 = QFrame(self.frame_filesContainer)
        self.frame_10.setObjectName(u"frame_10")
        self.frame_10.setMinimumSize(QSize(0, 20))
        self.frame_10.setMaximumSize(QSize(16777215, 20))
        self.frame_10.setFrameShape(QFrame.NoFrame)
        self.frame_10.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_12 = QHBoxLayout(self.frame_10)
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.horizontalLayout_12.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.frame_10)
        self.label.setObjectName(u"label")
        font4 = QFont()
        font4.setPointSize(12)
        font4.setBold(True)
        self.label.setFont(font4)

        self.horizontalLayout_12.addWidget(self.label)

        self.label_files_count = QLabel(self.frame_10)
        self.label_files_count.setObjectName(u"label_files_count")

        self.horizontalLayout_12.addWidget(self.label_files_count)


        self.verticalLayout_6.addWidget(self.frame_10, 0, Qt.AlignLeft)

        self.frame_6 = QFrame(self.frame_filesContainer)
        self.frame_6.setObjectName(u"frame_6")
        self.frame_6.setFrameShape(QFrame.NoFrame)
        self.frame_6.setFrameShadow(QFrame.Plain)
        self.horizontalLayout_3 = QHBoxLayout(self.frame_6)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.frame_inputFile = QFrame(self.frame_6)
        self.frame_inputFile.setObjectName(u"frame_inputFile")
        self.frame_inputFile.setMinimumSize(QSize(160, 160))
        self.frame_inputFile.setFrameShape(QFrame.NoFrame)
        self.frame_inputFile.setFrameShadow(QFrame.Sunken)
        self.horizontalLayout_5 = QHBoxLayout(self.frame_inputFile)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.label_3 = QLabel(self.frame_inputFile)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_5.addWidget(self.label_3)


        self.horizontalLayout_3.addWidget(self.frame_inputFile)

        self.line_4 = QFrame(self.frame_6)
        self.line_4.setObjectName(u"line_4")
        sizePolicy7 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(6)
        sizePolicy7.setHeightForWidth(self.line_4.sizePolicy().hasHeightForWidth())
        self.line_4.setSizePolicy(sizePolicy7)
        self.line_4.setMinimumSize(QSize(8, 160))
        self.line_4.setMaximumSize(QSize(8, 160))
        self.line_4.setFrameShape(QFrame.VLine)
        self.line_4.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_3.addWidget(self.line_4, 0, Qt.AlignTop)

        self.scrollArea = QScrollArea(self.frame_6)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy8 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        sizePolicy8.setHorizontalStretch(0)
        sizePolicy8.setVerticalStretch(0)
        sizePolicy8.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy8)
        self.scrollArea.setMinimumSize(QSize(158, 200))
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scrollArea.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.scrollArea.setWidgetResizable(True)
        self.frame_outputFiles_scroll = QWidget()
        self.frame_outputFiles_scroll.setObjectName(u"frame_outputFiles_scroll")
        self.frame_outputFiles_scroll.setGeometry(QRect(0, 0, 1390, 200))
        sizePolicy2.setHeightForWidth(self.frame_outputFiles_scroll.sizePolicy().hasHeightForWidth())
        self.frame_outputFiles_scroll.setSizePolicy(sizePolicy2)
        self.frame_outputFiles_scroll.setMinimumSize(QSize(0, 0))
        self.horizontalLayout1 = QHBoxLayout(self.frame_outputFiles_scroll)
        self.horizontalLayout1.setSpacing(0)
        self.horizontalLayout1.setObjectName(u"horizontalLayout1")
        self.horizontalLayout1.setContentsMargins(0, 0, 0, 0)
        self.frame_outputFiles = QFrame(self.frame_outputFiles_scroll)
        self.frame_outputFiles.setObjectName(u"frame_outputFiles")
        sizePolicy1.setHeightForWidth(self.frame_outputFiles.sizePolicy().hasHeightForWidth())
        self.frame_outputFiles.setSizePolicy(sizePolicy1)
        self.frame_outputFiles.setFrameShape(QFrame.NoFrame)
        self.frame_outputFiles.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.frame_outputFiles)
        self.horizontalLayout_4.setSpacing(2)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.label_2 = QLabel(self.frame_outputFiles)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_4.addWidget(self.label_2)


        self.horizontalLayout1.addWidget(self.frame_outputFiles, 0, Qt.AlignLeft)

        self.scrollArea.setWidget(self.frame_outputFiles_scroll)

        self.horizontalLayout_3.addWidget(self.scrollArea)


        self.verticalLayout_6.addWidget(self.frame_6)


        self.verticalLayout_2.addWidget(self.frame_filesContainer)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Enhance AI", None))
        self.label_title.setText(QCoreApplication.translate("MainWindow", u"Enhance AI", None))
        self.label_cuda.setText("")
        self.label_progressBar.setText("")
        self.pushButton_cancelOp.setText("")
        self.checkBox_antialias.setText("")
        self.pushButton_single.setText("")
        self.pushButton_split.setText("")
        self.pushButton_quad.setText("")
        self.pushButton_zoom.setText(QCoreApplication.translate("MainWindow", u"100%", None))
        self.canvas_main.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.pushButton_open.setText(QCoreApplication.translate("MainWindow", u"Open", None))
        self.pushButton_run.setText(QCoreApplication.translate("MainWindow", u"Run", None))
        self.pushButton_clear.setText(QCoreApplication.translate("MainWindow", u"Clear", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Post Processing", None))
        self.label_blend.setText(QCoreApplication.translate("MainWindow", u"Blend Original Image", None))
        self.label_blend_amt.setText(QCoreApplication.translate("MainWindow", u"0%", None))
        self.pushButton_postprocess_apply.setText(QCoreApplication.translate("MainWindow", u"Apply", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Files", None))
        self.label_files_count.setText("")
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"text", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"text", None))
    # retranslateUi

