# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'layout.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QLayout, QLineEdit,
    QMainWindow, QPushButton, QScrollArea, QSizePolicy,
    QSpacerItem, QSpinBox, QStatusBar, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(880, 600)
        MainWindow.setMinimumSize(QSize(880, 600))
        self.centralWidget = QWidget(MainWindow)
        self.centralWidget.setObjectName(u"centralWidget")
        self.rootLayout = QVBoxLayout(self.centralWidget)
        self.rootLayout.setSpacing(12)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(16, 16, 16, 16)
        self.contentScroll = QScrollArea(self.centralWidget)
        self.contentScroll.setObjectName(u"contentScroll")
        self.contentScroll.setFrameShape(QFrame.Shape.NoFrame)
        self.contentScroll.setWidgetResizable(True)
        self.scrollContent = QWidget()
        self.scrollContent.setObjectName(u"scrollContent")
        self.scrollContent.setGeometry(QRect(0, 0, 848, 548))
        self.contentLayout = QVBoxLayout(self.scrollContent)
        self.contentLayout.setSpacing(0)
        self.contentLayout.setObjectName(u"contentLayout")
        self.contentLayout.setContentsMargins(8, 8, 8, 8)
        self.configOuter = QVBoxLayout()
        self.configOuter.setSpacing(8)
        self.configOuter.setObjectName(u"configOuter")
        self.configOuter.setContentsMargins(12, 12, 12, 8)
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setSpacing(16)
        self.mainLayout.setObjectName(u"mainLayout")
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.leftLayout = QVBoxLayout()
        self.leftLayout.setSpacing(5)
        self.leftLayout.setObjectName(u"leftLayout")
        self.leftLayout.setContentsMargins(0, 0, 0, 0)
        self.fileCard = QFrame(self.scrollContent)
        self.fileCard.setObjectName(u"fileCard")
        self.fileCard.setEnabled(True)
        self.fileCardLayout = QVBoxLayout(self.fileCard)
        self.fileCardLayout.setSpacing(0)
        self.fileCardLayout.setObjectName(u"fileCardLayout")
        self.fileCardLayout.setContentsMargins(0, 0, 0, 0)
        self.fileCardTitle = QLabel(self.fileCard)
        self.fileCardTitle.setObjectName(u"fileCardTitle")
        self.fileCardTitle.setEnabled(True)

        self.fileCardLayout.addWidget(self.fileCardTitle, 0, Qt.AlignmentFlag.AlignTop)

        self.fileLayout = QFormLayout()
        self.fileLayout.setObjectName(u"fileLayout")
        self.fileLayout.setHorizontalSpacing(6)
        self.fileLayout.setVerticalSpacing(6)
        self.fileLayout.setContentsMargins(0, 8, 0, 0)
        self.excelLabel = QLabel(self.fileCard)
        self.excelLabel.setObjectName(u"excelLabel")

        self.fileLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.excelLabel)

        self.excelRowLayout = QHBoxLayout()
        self.excelRowLayout.setSpacing(8)
        self.excelRowLayout.setObjectName(u"excelRowLayout")
        self.excelRowLayout.setContentsMargins(0, 0, 0, 0)
        self.excelEdit = QLineEdit(self.fileCard)
        self.excelEdit.setObjectName(u"excelEdit")
        self.excelEdit.setReadOnly(True)

        self.excelRowLayout.addWidget(self.excelEdit)

        self.excelBrowse = QPushButton(self.fileCard)
        self.excelBrowse.setObjectName(u"excelBrowse")
        self.excelBrowse.setMaximumSize(QSize(70, 16777215))

        self.excelRowLayout.addWidget(self.excelBrowse)


        self.fileLayout.setLayout(0, QFormLayout.ItemRole.FieldRole, self.excelRowLayout)

        self.picLabel = QLabel(self.fileCard)
        self.picLabel.setObjectName(u"picLabel")

        self.fileLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.picLabel)

        self.picRowLayout = QHBoxLayout()
        self.picRowLayout.setSpacing(8)
        self.picRowLayout.setObjectName(u"picRowLayout")
        self.picRowLayout.setContentsMargins(0, 0, 0, 0)
        self.picEdit = QLineEdit(self.fileCard)
        self.picEdit.setObjectName(u"picEdit")
        self.picEdit.setReadOnly(True)

        self.picRowLayout.addWidget(self.picEdit)

        self.picBrowse = QPushButton(self.fileCard)
        self.picBrowse.setObjectName(u"picBrowse")
        self.picBrowse.setMaximumSize(QSize(70, 16777215))

        self.picRowLayout.addWidget(self.picBrowse)


        self.fileLayout.setLayout(1, QFormLayout.ItemRole.FieldRole, self.picRowLayout)


        self.fileCardLayout.addLayout(self.fileLayout)


        self.leftLayout.addWidget(self.fileCard, 0, Qt.AlignmentFlag.AlignTop)

        self.signalCard = QFrame(self.scrollContent)
        self.signalCard.setObjectName(u"signalCard")
        self.signalCardLayout = QVBoxLayout(self.signalCard)
        self.signalCardLayout.setSpacing(0)
        self.signalCardLayout.setObjectName(u"signalCardLayout")
        self.signalCardLayout.setContentsMargins(0, 0, 0, 0)
        self.signalCardTitle = QLabel(self.signalCard)
        self.signalCardTitle.setObjectName(u"signalCardTitle")

        self.signalCardLayout.addWidget(self.signalCardTitle, 0, Qt.AlignmentFlag.AlignTop)

        self.signalLayout = QFormLayout()
        self.signalLayout.setObjectName(u"signalLayout")
        self.signalLayout.setHorizontalSpacing(6)
        self.signalLayout.setVerticalSpacing(6)
        self.signalLayout.setContentsMargins(0, 8, 0, 0)
        self.sig1Label = QLabel(self.signalCard)
        self.sig1Label.setObjectName(u"sig1Label")

        self.signalLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.sig1Label)

        self.signal1Edit = QLineEdit(self.signalCard)
        self.signal1Edit.setObjectName(u"signal1Edit")
        self.signal1Edit.setReadOnly(True)

        self.signalLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.signal1Edit)

        self.sig2Label = QLabel(self.signalCard)
        self.sig2Label.setObjectName(u"sig2Label")

        self.signalLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.sig2Label)

        self.signal2Edit = QLineEdit(self.signalCard)
        self.signal2Edit.setObjectName(u"signal2Edit")
        self.signal2Edit.setReadOnly(True)

        self.signalLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.signal2Edit)

        self.sig3Label = QLabel(self.signalCard)
        self.sig3Label.setObjectName(u"sig3Label")

        self.signalLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.sig3Label)

        self.signal3Edit = QLineEdit(self.signalCard)
        self.signal3Edit.setObjectName(u"signal3Edit")
        self.signal3Edit.setReadOnly(True)

        self.signalLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.signal3Edit)


        self.signalCardLayout.addLayout(self.signalLayout)


        self.leftLayout.addWidget(self.signalCard, 0, Qt.AlignmentFlag.AlignTop)

        self.bottomToolbarLayout = QVBoxLayout()
        self.bottomToolbarLayout.setSpacing(4)
        self.bottomToolbarLayout.setObjectName(u"bottomToolbarLayout")
        self.bottomToolbarLayout.setContentsMargins(0, 0, 0, 0)
        self.navLayout = QHBoxLayout()
        self.navLayout.setSpacing(6)
        self.navLayout.setObjectName(u"navLayout")
        self.navLayout.setContentsMargins(0, 4, 0, 0)
        self.lastBtn = QPushButton(self.scrollContent)
        self.lastBtn.setObjectName(u"lastBtn")

        self.navLayout.addWidget(self.lastBtn)

        self.nextBtn = QPushButton(self.scrollContent)
        self.nextBtn.setObjectName(u"nextBtn")

        self.navLayout.addWidget(self.nextBtn)

        self.navGap = QSpacerItem(8, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.navLayout.addItem(self.navGap)

        self.jumpSpin = QSpinBox(self.scrollContent)
        self.jumpSpin.setObjectName(u"jumpSpin")
        self.jumpSpin.setMinimumSize(QSize(60, 0))
        self.jumpSpin.setMaximum(999)
        self.jumpSpin.setValue(8)

        self.navLayout.addWidget(self.jumpSpin)

        self.jumpBtn = QPushButton(self.scrollContent)
        self.jumpBtn.setObjectName(u"jumpBtn")

        self.navLayout.addWidget(self.jumpBtn)

        self.navSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.navLayout.addItem(self.navSpacer)


        self.bottomToolbarLayout.addLayout(self.navLayout)

        self.actionLayout = QHBoxLayout()
        self.actionLayout.setSpacing(6)
        self.actionLayout.setObjectName(u"actionLayout")
        self.actionLayout.setContentsMargins(0, 4, 0, 0)
        self.connectBtn = QPushButton(self.scrollContent)
        self.connectBtn.setObjectName(u"connectBtn")

        self.actionLayout.addWidget(self.connectBtn)

        self.statusBadge = QWidget(self.scrollContent)
        self.statusBadge.setObjectName(u"statusBadge")
        self.statusBadge.setMinimumSize(QSize(14, 14))
        self.statusBadge.setMaximumSize(QSize(14, 14))

        self.actionLayout.addWidget(self.statusBadge)

        self.reconnectBtn = QPushButton(self.scrollContent)
        self.reconnectBtn.setObjectName(u"reconnectBtn")

        self.actionLayout.addWidget(self.reconnectBtn)

        self.connInfoLabel = QLabel(self.scrollContent)
        self.connInfoLabel.setObjectName(u"connInfoLabel")

        self.actionLayout.addWidget(self.connInfoLabel)

        self.actionSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.actionLayout.addItem(self.actionSpacer)

        self.saveCloseBtn = QPushButton(self.scrollContent)
        self.saveCloseBtn.setObjectName(u"saveCloseBtn")

        self.actionLayout.addWidget(self.saveCloseBtn)

        self.savePicBtn = QPushButton(self.scrollContent)
        self.savePicBtn.setObjectName(u"savePicBtn")

        self.actionLayout.addWidget(self.savePicBtn)

        self.setMsoBtn = QPushButton(self.scrollContent)
        self.setMsoBtn.setObjectName(u"setMsoBtn")

        self.actionLayout.addWidget(self.setMsoBtn)


        self.bottomToolbarLayout.addLayout(self.actionLayout)


        self.leftLayout.addLayout(self.bottomToolbarLayout)


        self.mainLayout.addLayout(self.leftLayout)

        self.rightLayout = QVBoxLayout()
        self.rightLayout.setSpacing(10)
        self.rightLayout.setObjectName(u"rightLayout")
        self.rightLayout.setContentsMargins(0, 0, 0, 0)
        self.infoCard = QFrame(self.scrollContent)
        self.infoCard.setObjectName(u"infoCard")
        self.infoCardLayout = QVBoxLayout(self.infoCard)
        self.infoCardLayout.setSpacing(0)
        self.infoCardLayout.setObjectName(u"infoCardLayout")
        self.infoCardLayout.setContentsMargins(0, 0, 0, 0)
        self.infoCardTitle = QLabel(self.infoCard)
        self.infoCardTitle.setObjectName(u"infoCardTitle")

        self.infoCardLayout.addWidget(self.infoCardTitle, 0, Qt.AlignmentFlag.AlignTop)

        self.infoLayout = QFormLayout()
        self.infoLayout.setObjectName(u"infoLayout")
        self.infoLayout.setHorizontalSpacing(6)
        self.infoLayout.setVerticalSpacing(6)
        self.infoLayout.setContentsMargins(0, 8, 0, 0)
        self.projectLabel = QLabel(self.infoCard)
        self.projectLabel.setObjectName(u"projectLabel")

        self.infoLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.projectLabel)

        self.projectEdit = QLineEdit(self.infoCard)
        self.projectEdit.setObjectName(u"projectEdit")

        self.infoLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.projectEdit)

        self.sheetLabel = QLabel(self.infoCard)
        self.sheetLabel.setObjectName(u"sheetLabel")

        self.infoLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.sheetLabel)

        self.sheetCombo = QComboBox(self.infoCard)
        self.sheetCombo.setObjectName(u"sheetCombo")

        self.infoLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.sheetCombo)

        self.testsLabel = QLabel(self.infoCard)
        self.testsLabel.setObjectName(u"testsLabel")

        self.infoLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.testsLabel)

        self.testsSumEdit = QLineEdit(self.infoCard)
        self.testsSumEdit.setObjectName(u"testsSumEdit")
        self.testsSumEdit.setReadOnly(True)

        self.infoLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.testsSumEdit)

        self.itemLabel = QLabel(self.infoCard)
        self.itemLabel.setObjectName(u"itemLabel")

        self.infoLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.itemLabel)

        self.currentItemEdit = QLineEdit(self.infoCard)
        self.currentItemEdit.setObjectName(u"currentItemEdit")
        self.currentItemEdit.setReadOnly(True)

        self.infoLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.currentItemEdit)


        self.infoCardLayout.addLayout(self.infoLayout)


        self.rightLayout.addWidget(self.infoCard, 0, Qt.AlignmentFlag.AlignTop)

        self.labelCard = QFrame(self.scrollContent)
        self.labelCard.setObjectName(u"labelCard")
        self.labelCardTitle = QLabel(self.labelCard)
        self.labelCardTitle.setObjectName(u"labelCardTitle")
        self.labelCardTitle.setGeometry(QRect(0, 0, 104, 16))
        self.ch2Edit = QLineEdit(self.labelCard)
        self.ch2Edit.setObjectName(u"ch2Edit")
        self.ch2Edit.setGeometry(QRect(35, 54, 131, 20))
        self.setLabelBtn = QPushButton(self.labelCard)
        self.setLabelBtn.setObjectName(u"setLabelBtn")
        self.setLabelBtn.setGeometry(QRect(35, 132, 75, 24))
        self.ch1Label = QLabel(self.labelCard)
        self.ch1Label.setObjectName(u"ch1Label")
        self.ch1Label.setGeometry(QRect(1, 24, 28, 16))
        self.ch4Label = QLabel(self.labelCard)
        self.ch4Label.setObjectName(u"ch4Label")
        self.ch4Label.setGeometry(QRect(1, 106, 28, 16))
        self.ch3Label = QLabel(self.labelCard)
        self.ch3Label.setObjectName(u"ch3Label")
        self.ch3Label.setGeometry(QRect(1, 80, 28, 16))
        self.ch2Label = QLabel(self.labelCard)
        self.ch2Label.setObjectName(u"ch2Label")
        self.ch2Label.setGeometry(QRect(1, 54, 28, 16))
        self.ch3Edit = QLineEdit(self.labelCard)
        self.ch3Edit.setObjectName(u"ch3Edit")
        self.ch3Edit.setGeometry(QRect(35, 80, 132, 20))
        self.ch4Edit = QLineEdit(self.labelCard)
        self.ch4Edit.setObjectName(u"ch4Edit")
        self.ch4Edit.setGeometry(QRect(35, 106, 132, 20))
        self.ch1Row = QWidget(self.labelCard)
        self.ch1Row.setObjectName(u"ch1Row")
        self.ch1Row.setGeometry(QRect(35, 24, 156, 24))
        self.ch1RowLayout = QHBoxLayout(self.ch1Row)
        self.ch1RowLayout.setSpacing(0)
        self.ch1RowLayout.setObjectName(u"ch1RowLayout")
        self.ch1RowLayout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.ch1RowLayout.setContentsMargins(0, 0, 0, 0)
        self.ch1Edit = QLineEdit(self.ch1Row)
        self.ch1Edit.setObjectName(u"ch1Edit")

        self.ch1RowLayout.addWidget(self.ch1Edit)

        self.pnBadge = QLabel(self.ch1Row)
        self.pnBadge.setObjectName(u"pnBadge")
        self.pnBadge.setMinimumSize(QSize(22, 22))
        self.pnBadge.setMaximumSize(QSize(22, 22))
        self.pnBadge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.ch1RowLayout.addWidget(self.pnBadge)


        self.rightLayout.addWidget(self.labelCard)


        self.mainLayout.addLayout(self.rightLayout)


        self.configOuter.addLayout(self.mainLayout)


        self.contentLayout.addLayout(self.configOuter)

        self.contentScroll.setWidget(self.scrollContent)

        self.rootLayout.addWidget(self.contentScroll)

        MainWindow.setCentralWidget(self.centralWidget)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName(u"statusBar")
        self.statusLabel = QLabel(self.statusBar)
        self.statusLabel.setObjectName(u"statusLabel")
        self.statusLabel.setGeometry(QRect(0, 0, 100, 30))
        self.themeBtn = QPushButton(self.statusBar)
        self.themeBtn.setObjectName(u"themeBtn")
        self.themeBtn.setGeometry(QRect(0, 0, 32, 32))
        self.themeBtn.setMinimumSize(QSize(32, 32))
        self.themeBtn.setMaximumSize(QSize(32, 32))
        MainWindow.setStatusBar(self.statusBar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Nettrix Power Sequence Test Tool V3.0", None))
        self.fileCardTitle.setText(QCoreApplication.translate("MainWindow", u"FILE PATHS", None))
        self.excelLabel.setText(QCoreApplication.translate("MainWindow", u"Excel:", None))
        self.excelEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"No file selected", None))
        self.excelBrowse.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.picLabel.setText(QCoreApplication.translate("MainWindow", u"Pic:", None))
        self.picEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"No folder selected", None))
        self.picBrowse.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.signalCardTitle.setText(QCoreApplication.translate("MainWindow", u"SIGNALS", None))
        self.sig1Label.setText(QCoreApplication.translate("MainWindow", u"Sig 1:", None))
        self.sig2Label.setText(QCoreApplication.translate("MainWindow", u"Sig 2:", None))
        self.sig3Label.setText(QCoreApplication.translate("MainWindow", u"Sig 3:", None))
        self.lastBtn.setText(QCoreApplication.translate("MainWindow", u"Last", None))
        self.nextBtn.setText(QCoreApplication.translate("MainWindow", u"Next", None))
        self.jumpBtn.setText(QCoreApplication.translate("MainWindow", u"Jump", None))
        self.connectBtn.setText(QCoreApplication.translate("MainWindow", u"Connect", None))
        self.reconnectBtn.setText(QCoreApplication.translate("MainWindow", u"Reconnect", None))
        self.connInfoLabel.setText("")
        self.saveCloseBtn.setText(QCoreApplication.translate("MainWindow", u"Save & Close", None))
        self.savePicBtn.setText(QCoreApplication.translate("MainWindow", u"Save Pic", None))
        self.setMsoBtn.setText(QCoreApplication.translate("MainWindow", u"Set MSO", None))
        self.infoCardTitle.setText(QCoreApplication.translate("MainWindow", u"PROJECT INFO", None))
        self.projectLabel.setText(QCoreApplication.translate("MainWindow", u"Project:", None))
        self.projectEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Enter project name\u2026", None))
        self.sheetLabel.setText(QCoreApplication.translate("MainWindow", u"Sheet:", None))
        self.sheetCombo.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Select sheet\u2026", None))
        self.testsLabel.setText(QCoreApplication.translate("MainWindow", u"Tests:", None))
        self.itemLabel.setText(QCoreApplication.translate("MainWindow", u"Item:", None))
        self.labelCardTitle.setText(QCoreApplication.translate("MainWindow", u"CHANNEL LABELS", None))
        self.ch2Edit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"CH2\u2026", None))
        self.setLabelBtn.setText(QCoreApplication.translate("MainWindow", u"Set Label", None))
        self.ch1Label.setText(QCoreApplication.translate("MainWindow", u"CH1:", None))
        self.ch4Label.setText(QCoreApplication.translate("MainWindow", u"CH4:", None))
        self.ch3Label.setText(QCoreApplication.translate("MainWindow", u"CH3:", None))
        self.ch2Label.setText(QCoreApplication.translate("MainWindow", u"CH2:", None))
        self.ch3Edit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"CH3\u2026", None))
        self.ch4Edit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"CH4\u2026", None))
        self.ch1Edit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"CH1\u2026", None))
        self.pnBadge.setText(QCoreApplication.translate("MainWindow", u"P", None))
        self.statusLabel.setText(QCoreApplication.translate("MainWindow", u"Ready", None))
        self.themeBtn.setText(QCoreApplication.translate("MainWindow", u"Theme", None))
    # retranslateUi

