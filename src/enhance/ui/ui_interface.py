# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'interfacegksxeT.ui'
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
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLayout, QMainWindow, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QSlider, QVBoxLayout,
    QWidget)
import icons_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1622, 1343)
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setBaseSize(QSize(1600, 1200))
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
        font = QFont()
        font.setPointSize(12)
        self.label_progressBar.setFont(font)

        self.horizontalLayout_11.addWidget(self.label_progressBar)

        self.frame_9 = QFrame(self.frame_progressBar)
        self.frame_9.setObjectName(u"frame_9")
        self.frame_9.setMinimumSize(QSize(280, 0))
        self.frame_9.setMaximumSize(QSize(280, 16777215))
        self.frame_9.setFrameShape(QFrame.NoFrame)
        self.frame_9.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_17 = QHBoxLayout(self.frame_9)
        self.horizontalLayout_17.setSpacing(0)
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.horizontalLayout_17.setContentsMargins(0, 0, 0, 0)
        self.progressBar = QProgressBar(self.frame_9)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setMinimumSize(QSize(250, 30))
        self.progressBar.setMaximumSize(QSize(250, 16777215))
        font1 = QFont()
        font1.setPointSize(11)
        self.progressBar.setFont(font1)
        self.progressBar.setValue(0)

        self.horizontalLayout_17.addWidget(self.progressBar)

        self.pushButton_taskQueue = QPushButton(self.frame_9)
        self.pushButton_taskQueue.setObjectName(u"pushButton_taskQueue")
        self.pushButton_taskQueue.setMinimumSize(QSize(30, 30))
        self.pushButton_taskQueue.setMaximumSize(QSize(30, 30))
        icon = QIcon()
        icon.addFile(u":/icons32/chevron-down.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_taskQueue.setIcon(icon)
        self.pushButton_taskQueue.setIconSize(QSize(32, 32))

        self.horizontalLayout_17.addWidget(self.pushButton_taskQueue)


        self.horizontalLayout_11.addWidget(self.frame_9)

        self.pushButton_cancelOp = QPushButton(self.frame_progressBar)
        self.pushButton_cancelOp.setObjectName(u"pushButton_cancelOp")
        self.pushButton_cancelOp.setMinimumSize(QSize(30, 0))
        self.pushButton_cancelOp.setMaximumSize(QSize(30, 16777215))
        font2 = QFont()
        font2.setPointSize(9)
        self.pushButton_cancelOp.setFont(font2)
        icon1 = QIcon()
        icon1.addFile(u":/icons32/x.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_cancelOp.setIcon(icon1)
        self.pushButton_cancelOp.setIconSize(QSize(24, 24))

        self.horizontalLayout_11.addWidget(self.pushButton_cancelOp)


        self.horizontalLayout_10.addWidget(self.frame_progressBar)

        self.frame_2 = QFrame(self.frame_3)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setMinimumSize(QSize(25, 0))
        self.frame_2.setFrameShape(QFrame.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Raised)

        self.horizontalLayout_10.addWidget(self.frame_2)

        self.pushButton_single = QPushButton(self.frame_3)
        self.pushButton_single.setObjectName(u"pushButton_single")
        self.pushButton_single.setMinimumSize(QSize(40, 40))
        icon2 = QIcon()
        icon2.addFile(u":/icons32/square.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_single.setIcon(icon2)
        self.pushButton_single.setIconSize(QSize(24, 24))

        self.horizontalLayout_10.addWidget(self.pushButton_single)

        self.pushButton_split = QPushButton(self.frame_3)
        self.pushButton_split.setObjectName(u"pushButton_split")
        self.pushButton_split.setMinimumSize(QSize(40, 40))
        icon3 = QIcon()
        icon3.addFile(u":/icons32/columns.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_split.setIcon(icon3)
        self.pushButton_split.setIconSize(QSize(24, 24))

        self.horizontalLayout_10.addWidget(self.pushButton_split)

        self.pushButton_quad = QPushButton(self.frame_3)
        self.pushButton_quad.setObjectName(u"pushButton_quad")
        self.pushButton_quad.setMinimumSize(QSize(40, 40))
        icon4 = QIcon()
        icon4.addFile(u":/icons32/grid.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_quad.setIcon(icon4)
        self.pushButton_quad.setIconSize(QSize(24, 24))

        self.horizontalLayout_10.addWidget(self.pushButton_quad)

        self.pushButton_zoom = QPushButton(self.frame_3)
        self.pushButton_zoom.setObjectName(u"pushButton_zoom")
        self.pushButton_zoom.setMinimumSize(QSize(0, 40))
        self.pushButton_zoom.setFont(font)
        icon5 = QIcon()
        icon5.addFile(u":/icons32/zoom-in.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_zoom.setIcon(icon5)
        self.pushButton_zoom.setIconSize(QSize(24, 24))

        self.horizontalLayout_10.addWidget(self.pushButton_zoom)


        self.gridLayout.addWidget(self.frame_3, 0, 1, 1, 1, Qt.AlignRight)

        self.frame_4 = QFrame(self.toolbar)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setMinimumSize(QSize(244, 0))
        self.frame_4.setMaximumSize(QSize(244, 16777215))
        self.frame_4.setFrameShape(QFrame.NoFrame)
        self.frame_4.setFrameShadow(QFrame.Plain)
        self.verticalLayout_14 = QVBoxLayout(self.frame_4)
        self.verticalLayout_14.setSpacing(6)
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.verticalLayout_14.setContentsMargins(12, 0, 0, 0)
        self.frame_gpu = QFrame(self.frame_4)
        self.frame_gpu.setObjectName(u"frame_gpu")
        self.frame_gpu.setStyleSheet(u"")
        self.frame_gpu.setFrameShape(QFrame.NoFrame)
        self.frame_gpu.setFrameShadow(QFrame.Raised)
        self.verticalLayout_15 = QVBoxLayout(self.frame_gpu)
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.verticalLayout_15.setContentsMargins(0, 0, 0, 0)
        self.frame_gpu_label = QFrame(self.frame_gpu)
        self.frame_gpu_label.setObjectName(u"frame_gpu_label")
        self.frame_gpu_label.setMinimumSize(QSize(0, 0))
        self.frame_gpu_label.setFrameShape(QFrame.StyledPanel)
        self.frame_gpu_label.setFrameShadow(QFrame.Raised)
        self.verticalLayout_7 = QVBoxLayout(self.frame_gpu_label)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.label_gpu = QLabel(self.frame_gpu_label)
        self.label_gpu.setObjectName(u"label_gpu")

        self.verticalLayout_7.addWidget(self.label_gpu)


        self.verticalLayout_15.addWidget(self.frame_gpu_label)

        self.frame_gpu_util = QFrame(self.frame_gpu)
        self.frame_gpu_util.setObjectName(u"frame_gpu_util")
        self.frame_gpu_util.setFrameShape(QFrame.NoFrame)
        self.frame_gpu_util.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_19 = QHBoxLayout(self.frame_gpu_util)
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.horizontalLayout_19.setContentsMargins(0, 0, 0, 0)
        self.progressBar_gpu_util = QProgressBar(self.frame_gpu_util)
        self.progressBar_gpu_util.setObjectName(u"progressBar_gpu_util")
        font3 = QFont()
        font3.setPointSize(8)
        self.progressBar_gpu_util.setFont(font3)
        self.progressBar_gpu_util.setStyleSheet(u"QProgressBar {\n"
"            border: 2px solid grey;\n"
"            border-radius: 5px;\n"
"        }\n"
"\n"
"        QProgressBar::chunk {\n"
"            background-color: green;\n"
"            width: 20px;\n"
"        }")
        self.progressBar_gpu_util.setValue(0)
        self.progressBar_gpu_util.setAlignment(Qt.AlignCenter)
        self.progressBar_gpu_util.setTextVisible(True)
        self.progressBar_gpu_util.setInvertedAppearance(False)
        self.progressBar_gpu_util.setTextDirection(QProgressBar.TopToBottom)

        self.horizontalLayout_19.addWidget(self.progressBar_gpu_util)


        self.verticalLayout_15.addWidget(self.frame_gpu_util)

        self.frame_gpu_mem = QFrame(self.frame_gpu)
        self.frame_gpu_mem.setObjectName(u"frame_gpu_mem")
        self.frame_gpu_mem.setFrameShape(QFrame.NoFrame)
        self.frame_gpu_mem.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_18 = QHBoxLayout(self.frame_gpu_mem)
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.horizontalLayout_18.setContentsMargins(0, 0, 0, 0)
        self.progressBar_gpu_mem = QProgressBar(self.frame_gpu_mem)
        self.progressBar_gpu_mem.setObjectName(u"progressBar_gpu_mem")
        self.progressBar_gpu_mem.setFont(font3)
        self.progressBar_gpu_mem.setStyleSheet(u"QProgressBar {\n"
"            border: 2px solid grey;\n"
"            border-radius: 5px;\n"
"        }\n"
"\n"
"        QProgressBar::chunk {\n"
"            background-color: green;\n"
"            width: 20px;\n"
"        }")
        self.progressBar_gpu_mem.setValue(0)
        self.progressBar_gpu_mem.setAlignment(Qt.AlignCenter)
        self.progressBar_gpu_mem.setTextVisible(True)
        self.progressBar_gpu_mem.setInvertedAppearance(False)

        self.horizontalLayout_18.addWidget(self.progressBar_gpu_mem)


        self.verticalLayout_15.addWidget(self.frame_gpu_mem)


        self.verticalLayout_14.addWidget(self.frame_gpu)


        self.gridLayout.addWidget(self.frame_4, 0, 3, 1, 1)

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
        font4 = QFont()
        font4.setPointSize(18)
        font4.setBold(True)
        self.label_title.setFont(font4)

        self.horizontalLayout_9.addWidget(self.label_title)


        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)


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
        self.frame_sidebar.setFrameShadow(QFrame.Plain)
        self.verticalLayout_3 = QVBoxLayout(self.frame_sidebar)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(2, 2, 2, 2)
        self.pushButton_open = QPushButton(self.frame_sidebar)
        self.pushButton_open.setObjectName(u"pushButton_open")

        self.verticalLayout_3.addWidget(self.pushButton_open)

        self.pushButton_clear = QPushButton(self.frame_sidebar)
        self.pushButton_clear.setObjectName(u"pushButton_clear")

        self.verticalLayout_3.addWidget(self.pushButton_clear)

        self.line_8 = QFrame(self.frame_sidebar)
        self.line_8.setObjectName(u"line_8")
        self.line_8.setStyleSheet(u"color: rgb(92, 92, 92);")
        self.line_8.setFrameShadow(QFrame.Plain)
        self.line_8.setFrameShape(QFrame.HLine)

        self.verticalLayout_3.addWidget(self.line_8)

        self.pushButton_run = QPushButton(self.frame_sidebar)
        self.pushButton_run.setObjectName(u"pushButton_run")

        self.verticalLayout_3.addWidget(self.pushButton_run)

        self.pushButton_denoise = QPushButton(self.frame_sidebar)
        self.pushButton_denoise.setObjectName(u"pushButton_denoise")

        self.verticalLayout_3.addWidget(self.pushButton_denoise)

        self.pushButton_upscale = QPushButton(self.frame_sidebar)
        self.pushButton_upscale.setObjectName(u"pushButton_upscale")

        self.verticalLayout_3.addWidget(self.pushButton_upscale)

        self.line = QFrame(self.frame_sidebar)
        self.line.setObjectName(u"line")
        self.line.setStyleSheet(u"color: rgb(92, 92, 92);")
        self.line.setFrameShadow(QFrame.Plain)
        self.line.setFrameShape(QFrame.HLine)

        self.verticalLayout_3.addWidget(self.line)

        self.pushButton_modelManager = QPushButton(self.frame_sidebar)
        self.pushButton_modelManager.setObjectName(u"pushButton_modelManager")

        self.verticalLayout_3.addWidget(self.pushButton_modelManager)

        self.line_3 = QFrame(self.frame_sidebar)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setStyleSheet(u"color: rgb(92, 92, 92);")
        self.line_3.setFrameShadow(QFrame.Plain)
        self.line_3.setFrameShape(QFrame.HLine)

        self.verticalLayout_3.addWidget(self.line_3)

        self.group_base = QGroupBox(self.frame_sidebar)
        self.group_base.setObjectName(u"group_base")
        self.group_base.setStyleSheet(u"QGroupBox {\n"
"border: 1px solid rgb(92, 92, 92);\n"
"margin-top: 14px;\n"
"padding-top:10px;\n"
"}\n"
"QGroupBox::title {\n"
"subcontrol-origin: margin;\n"
"subcontrol-position: top left;\n"
"left: 8px;\n"
"padding:0 5px;\n"
"margin-top:5px;\n"
"}")
        self.group_base.setFlat(False)
        self.group_base.setCheckable(False)
        self.verticalLayout_18 = QVBoxLayout(self.group_base)
        self.verticalLayout_18.setSpacing(6)
        self.verticalLayout_18.setObjectName(u"verticalLayout_18")
        self.verticalLayout_18.setContentsMargins(6, 6, 6, 6)
        self.label_13 = QLabel(self.group_base)
        self.label_13.setObjectName(u"label_13")

        self.verticalLayout_18.addWidget(self.label_13)

        self.frame_label_filename_base = QFrame(self.group_base)
        self.frame_label_filename_base.setObjectName(u"frame_label_filename_base")
        self.frame_label_filename_base.setFrameShape(QFrame.NoFrame)
        self.frame_label_filename_base.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_13 = QHBoxLayout(self.frame_label_filename_base)
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.horizontalLayout_13.setContentsMargins(12, 0, 0, 0)
        self.label_filename_base = QLabel(self.frame_label_filename_base)
        self.label_filename_base.setObjectName(u"label_filename_base")
        self.label_filename_base.setMargin(0)

        self.horizontalLayout_13.addWidget(self.label_filename_base)


        self.verticalLayout_18.addWidget(self.frame_label_filename_base)

        self.label_14 = QLabel(self.group_base)
        self.label_14.setObjectName(u"label_14")

        self.verticalLayout_18.addWidget(self.label_14)

        self.frame_label_shape_base = QFrame(self.group_base)
        self.frame_label_shape_base.setObjectName(u"frame_label_shape_base")
        self.frame_label_shape_base.setFrameShape(QFrame.NoFrame)
        self.frame_label_shape_base.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_14 = QHBoxLayout(self.frame_label_shape_base)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.horizontalLayout_14.setContentsMargins(12, 0, 0, 0)
        self.label_shape_base = QLabel(self.frame_label_shape_base)
        self.label_shape_base.setObjectName(u"label_shape_base")

        self.horizontalLayout_14.addWidget(self.label_shape_base)


        self.verticalLayout_18.addWidget(self.frame_label_shape_base)

        self.frame_subject = QFrame(self.group_base)
        self.frame_subject.setObjectName(u"frame_subject")
        self.frame_subject.setFrameShape(QFrame.NoFrame)
        self.frame_subject.setFrameShadow(QFrame.Raised)
        self.verticalLayout_5 = QVBoxLayout(self.frame_subject)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.label_4 = QLabel(self.frame_subject)
        self.label_4.setObjectName(u"label_4")

        self.verticalLayout_5.addWidget(self.label_4)

        self.frame_label_subjects = QFrame(self.frame_subject)
        self.frame_label_subjects.setObjectName(u"frame_label_subjects")
        self.frame_label_subjects.setFrameShape(QFrame.NoFrame)
        self.frame_label_subjects.setFrameShadow(QFrame.Plain)
        self.horizontalLayout_16 = QHBoxLayout(self.frame_label_subjects)
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.horizontalLayout_16.setContentsMargins(12, 0, 0, 0)
        self.label_subjects = QLabel(self.frame_label_subjects)
        self.label_subjects.setObjectName(u"label_subjects")

        self.horizontalLayout_16.addWidget(self.label_subjects)


        self.verticalLayout_5.addWidget(self.frame_label_subjects)


        self.verticalLayout_18.addWidget(self.frame_subject)


        self.verticalLayout_3.addWidget(self.group_base)

        self.frame_mask = QFrame(self.frame_sidebar)
        self.frame_mask.setObjectName(u"frame_mask")
        self.frame_mask.setFrameShape(QFrame.NoFrame)
        self.frame_mask.setFrameShadow(QFrame.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.frame_mask)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 9, 0, 0)
        self.pushButton_mask = QPushButton(self.frame_mask)
        self.pushButton_mask.setObjectName(u"pushButton_mask")

        self.verticalLayout_4.addWidget(self.pushButton_mask)

        self.checkBox_render_masks = QCheckBox(self.frame_mask)
        self.checkBox_render_masks.setObjectName(u"checkBox_render_masks")

        self.verticalLayout_4.addWidget(self.checkBox_render_masks)


        self.verticalLayout_3.addWidget(self.frame_mask)

        self.frame_8 = QFrame(self.frame_sidebar)
        self.frame_8.setObjectName(u"frame_8")
        self.frame_8.setFrameShape(QFrame.NoFrame)
        self.frame_8.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_15 = QHBoxLayout(self.frame_8)
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.horizontalLayout_15.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout_3.addWidget(self.frame_8)

        self.group_compare = QGroupBox(self.frame_sidebar)
        self.group_compare.setObjectName(u"group_compare")
        self.group_compare.setStyleSheet(u"QGroupBox {\n"
"border: 1px solid rgb(92, 92, 92);\n"
"margin-top: 14px;\n"
"padding-top:10px;\n"
"}\n"
"QGroupBox::title {\n"
"subcontrol-origin: margin;\n"
"subcontrol-position: top left;\n"
"left: 8px;\n"
"padding:0 5px;\n"
"margin-top:5px;\n"
"}")
        self.verticalLayout_19 = QVBoxLayout(self.group_compare)
        self.verticalLayout_19.setSpacing(6)
        self.verticalLayout_19.setObjectName(u"verticalLayout_19")
        self.verticalLayout_19.setContentsMargins(6, 6, 9, 6)
        self.label_8 = QLabel(self.group_compare)
        self.label_8.setObjectName(u"label_8")

        self.verticalLayout_19.addWidget(self.label_8)

        self.frame_label_filename = QFrame(self.group_compare)
        self.frame_label_filename.setObjectName(u"frame_label_filename")
        self.frame_label_filename.setFrameShape(QFrame.NoFrame)
        self.frame_label_filename.setFrameShadow(QFrame.Raised)
        self.verticalLayout_10 = QVBoxLayout(self.frame_label_filename)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_10.setContentsMargins(12, 0, 0, 0)
        self.label_filename = QLabel(self.frame_label_filename)
        self.label_filename.setObjectName(u"label_filename")
        self.label_filename.setMargin(0)

        self.verticalLayout_10.addWidget(self.label_filename)


        self.verticalLayout_19.addWidget(self.frame_label_filename)

        self.label_10 = QLabel(self.group_compare)
        self.label_10.setObjectName(u"label_10")

        self.verticalLayout_19.addWidget(self.label_10)

        self.frame_label_opname = QFrame(self.group_compare)
        self.frame_label_opname.setObjectName(u"frame_label_opname")
        self.frame_label_opname.setFrameShape(QFrame.NoFrame)
        self.frame_label_opname.setFrameShadow(QFrame.Raised)
        self.verticalLayout_11 = QVBoxLayout(self.frame_label_opname)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.verticalLayout_11.setContentsMargins(12, 0, 0, 0)
        self.label_opname = QLabel(self.frame_label_opname)
        self.label_opname.setObjectName(u"label_opname")

        self.verticalLayout_11.addWidget(self.label_opname)


        self.verticalLayout_19.addWidget(self.frame_label_opname)

        self.label_12 = QLabel(self.group_compare)
        self.label_12.setObjectName(u"label_12")

        self.verticalLayout_19.addWidget(self.label_12)

        self.frame_label_modelname = QFrame(self.group_compare)
        self.frame_label_modelname.setObjectName(u"frame_label_modelname")
        self.frame_label_modelname.setFrameShape(QFrame.NoFrame)
        self.frame_label_modelname.setFrameShadow(QFrame.Raised)
        self.verticalLayout_12 = QVBoxLayout(self.frame_label_modelname)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.verticalLayout_12.setContentsMargins(12, 0, 0, 0)
        self.label_modelname = QLabel(self.frame_label_modelname)
        self.label_modelname.setObjectName(u"label_modelname")

        self.verticalLayout_12.addWidget(self.label_modelname)


        self.verticalLayout_19.addWidget(self.frame_label_modelname)

        self.label_9 = QLabel(self.group_compare)
        self.label_9.setObjectName(u"label_9")

        self.verticalLayout_19.addWidget(self.label_9)

        self.frame_label_shape = QFrame(self.group_compare)
        self.frame_label_shape.setObjectName(u"frame_label_shape")
        self.frame_label_shape.setFrameShape(QFrame.NoFrame)
        self.frame_label_shape.setFrameShadow(QFrame.Raised)
        self.verticalLayout_13 = QVBoxLayout(self.frame_label_shape)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.verticalLayout_13.setContentsMargins(12, 0, 0, 0)
        self.label_shape = QLabel(self.frame_label_shape)
        self.label_shape.setObjectName(u"label_shape")

        self.verticalLayout_13.addWidget(self.label_shape)


        self.verticalLayout_19.addWidget(self.frame_label_shape)


        self.verticalLayout_3.addWidget(self.group_compare)

        self.group_postprocess = QGroupBox(self.frame_sidebar)
        self.group_postprocess.setObjectName(u"group_postprocess")
        self.group_postprocess.setStyleSheet(u"QGroupBox {\n"
"border: 1px solid rgb(92, 92, 92);\n"
"margin-top: 14px;\n"
"padding-top:10px;\n"
"}\n"
"QGroupBox::title {\n"
"subcontrol-origin: margin;\n"
"subcontrol-position: top left;\n"
"left: 8px;\n"
"padding:0 5px;\n"
"margin-top:5px;\n"
"}")
        self.verticalLayout_20 = QVBoxLayout(self.group_postprocess)
        self.verticalLayout_20.setObjectName(u"verticalLayout_20")
        self.verticalLayout_20.setContentsMargins(6, 6, 6, 6)
        self.frame_blur = QFrame(self.group_postprocess)
        self.frame_blur.setObjectName(u"frame_blur")
        self.frame_blur.setFrameShape(QFrame.NoFrame)
        self.frame_blur.setFrameShadow(QFrame.Raised)
        self.verticalLayout_71 = QVBoxLayout(self.frame_blur)
        self.verticalLayout_71.setSpacing(6)
        self.verticalLayout_71.setObjectName(u"verticalLayout_71")
        self.verticalLayout_71.setContentsMargins(0, 0, 0, 9)
        self.label_6 = QLabel(self.frame_blur)
        self.label_6.setObjectName(u"label_6")

        self.verticalLayout_71.addWidget(self.label_6)

        self.frame_7 = QFrame(self.frame_blur)
        self.frame_7.setObjectName(u"frame_7")
        self.frame_7.setFrameShape(QFrame.NoFrame)
        self.frame_7.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_6 = QHBoxLayout(self.frame_7)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(12, 0, 0, 0)
        self.label_blur_amt = QLabel(self.frame_7)
        self.label_blur_amt.setObjectName(u"label_blur_amt")
        self.label_blur_amt.setMinimumSize(QSize(30, 0))

        self.horizontalLayout_6.addWidget(self.label_blur_amt)

        self.horizontalSlider_blur = QSlider(self.frame_7)
        self.horizontalSlider_blur.setObjectName(u"horizontalSlider_blur")
        self.horizontalSlider_blur.setOrientation(Qt.Horizontal)
        self.horizontalSlider_blur.setTickPosition(QSlider.TicksBothSides)

        self.horizontalLayout_6.addWidget(self.horizontalSlider_blur)


        self.verticalLayout_71.addWidget(self.frame_7)

        self.line_2 = QFrame(self.frame_blur)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setStyleSheet(u"color: rgb(92, 92, 92);")
        self.line_2.setFrameShadow(QFrame.Plain)
        self.line_2.setFrameShape(QFrame.HLine)

        self.verticalLayout_71.addWidget(self.line_2)


        self.verticalLayout_20.addWidget(self.frame_blur)

        self.frame_scale = QFrame(self.group_postprocess)
        self.frame_scale.setObjectName(u"frame_scale")
        self.frame_scale.setFrameShape(QFrame.NoFrame)
        self.frame_scale.setFrameShadow(QFrame.Plain)
        self.verticalLayout_8 = QVBoxLayout(self.frame_scale)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 9)
        self.frame_14 = QFrame(self.frame_scale)
        self.frame_14.setObjectName(u"frame_14")
        self.frame_14.setFrameShape(QFrame.NoFrame)
        self.frame_14.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_8 = QHBoxLayout(self.frame_14)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.label_5 = QLabel(self.frame_14)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_8.addWidget(self.label_5)

        self.label_scale = QLabel(self.frame_14)
        self.label_scale.setObjectName(u"label_scale")
        self.label_scale.setMinimumSize(QSize(30, 25))
        self.label_scale.setMaximumSize(QSize(30, 30))

        self.horizontalLayout_8.addWidget(self.label_scale)


        self.verticalLayout_8.addWidget(self.frame_14, 0, Qt.AlignLeft)

        self.line_5 = QFrame(self.frame_scale)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setStyleSheet(u"color: rgb(92, 92, 92);")
        self.line_5.setFrameShadow(QFrame.Plain)
        self.line_5.setFrameShape(QFrame.HLine)

        self.verticalLayout_8.addWidget(self.line_5)


        self.verticalLayout_20.addWidget(self.frame_scale)

        self.frame_blend = QFrame(self.group_postprocess)
        self.frame_blend.setObjectName(u"frame_blend")
        self.frame_blend.setFrameShape(QFrame.NoFrame)
        self.frame_blend.setFrameShadow(QFrame.Raised)
        self.verticalLayout_9 = QVBoxLayout(self.frame_blend)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 9)
        self.label_blend = QLabel(self.frame_blend)
        self.label_blend.setObjectName(u"label_blend")

        self.verticalLayout_9.addWidget(self.label_blend)

        self.frame_5 = QFrame(self.frame_blend)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setFrameShape(QFrame.NoFrame)
        self.frame_5.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_5)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(12, 0, 0, 0)
        self.label_blend_amt = QLabel(self.frame_5)
        self.label_blend_amt.setObjectName(u"label_blend_amt")
        self.label_blend_amt.setMinimumSize(QSize(30, 0))

        self.horizontalLayout_2.addWidget(self.label_blend_amt)

        self.horizontalSlider_blend = QSlider(self.frame_5)
        self.horizontalSlider_blend.setObjectName(u"horizontalSlider_blend")
        self.horizontalSlider_blend.setOrientation(Qt.Horizontal)
        self.horizontalSlider_blend.setTickPosition(QSlider.TicksBothSides)
        self.horizontalSlider_blend.setTickInterval(5)

        self.horizontalLayout_2.addWidget(self.horizontalSlider_blend)


        self.verticalLayout_9.addWidget(self.frame_5)

        self.line_6 = QFrame(self.frame_blend)
        self.line_6.setObjectName(u"line_6")
        self.line_6.setStyleSheet(u"color: rgb(92, 92, 92);")
        self.line_6.setFrameShadow(QFrame.Plain)
        self.line_6.setFrameShape(QFrame.HLine)

        self.verticalLayout_9.addWidget(self.line_6)


        self.verticalLayout_20.addWidget(self.frame_blend)

        self.pushButton_postprocess_apply = QPushButton(self.group_postprocess)
        self.pushButton_postprocess_apply.setObjectName(u"pushButton_postprocess_apply")

        self.verticalLayout_20.addWidget(self.pushButton_postprocess_apply)


        self.verticalLayout_3.addWidget(self.group_postprocess)


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
        font5 = QFont()
        font5.setPointSize(12)
        font5.setBold(True)
        self.label.setFont(font5)

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
        self.frame_inputFile.setMinimumSize(QSize(100, 100))
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
        self.frame_outputFiles_scroll.setGeometry(QRect(0, 0, 1472, 200))
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
        self.label_progressBar.setText("")
        self.pushButton_taskQueue.setText("")
        self.pushButton_cancelOp.setText("")
        self.pushButton_single.setText("")
        self.pushButton_split.setText("")
        self.pushButton_quad.setText("")
        self.pushButton_zoom.setText(QCoreApplication.translate("MainWindow", u"100%", None))
        self.label_gpu.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.label_title.setText(QCoreApplication.translate("MainWindow", u"Enhance AI", None))
        self.canvas_main.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.pushButton_open.setText(QCoreApplication.translate("MainWindow", u"Open", None))
        self.pushButton_clear.setText(QCoreApplication.translate("MainWindow", u"Clear", None))
        self.pushButton_run.setText(QCoreApplication.translate("MainWindow", u"Sharpen", None))
        self.pushButton_denoise.setText(QCoreApplication.translate("MainWindow", u"Denoise", None))
        self.pushButton_upscale.setText(QCoreApplication.translate("MainWindow", u"Upscale", None))
        self.pushButton_modelManager.setText(QCoreApplication.translate("MainWindow", u"Model Manager", None))
        self.group_base.setTitle(QCoreApplication.translate("MainWindow", u"Base File", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", u"Filename:", None))
        self.label_filename_base.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p><span style=\" color:#9a9996;\"/></p></body></html>", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"Shape:", None))
        self.label_shape_base.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p/></body></html>", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Subjects:", None))
        self.label_subjects.setText("")
        self.pushButton_mask.setText(QCoreApplication.translate("MainWindow", u"Auto Mask", None))
        self.checkBox_render_masks.setText(QCoreApplication.translate("MainWindow", u"Render Masks", None))
        self.group_compare.setTitle(QCoreApplication.translate("MainWindow", u"Compare File", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"Filename:", None))
        self.label_filename.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p><span style=\" color:#9a9996;\"/></p></body></html>", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"Operation:", None))
        self.label_opname.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p><span style=\" color:#9a9996;\"/></p></body></html>", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"Model:", None))
        self.label_modelname.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p><span style=\" color:#9a9996;\"/></p></body></html>", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"Shape:", None))
        self.label_shape.setText(QCoreApplication.translate("MainWindow", u"<html><head/><body><p/></body></html>", None))
        self.group_postprocess.setTitle(QCoreApplication.translate("MainWindow", u"Post Processing", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Blur:", None))
        self.label_blur_amt.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Downscale:", None))
        self.label_scale.setText("")
        self.label_blend.setText(QCoreApplication.translate("MainWindow", u"Blend Original Image:", None))
        self.label_blend_amt.setText(QCoreApplication.translate("MainWindow", u"0%", None))
        self.pushButton_postprocess_apply.setText(QCoreApplication.translate("MainWindow", u"Apply", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Files", None))
        self.label_files_count.setText("")
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"text", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"text", None))
    # retranslateUi

