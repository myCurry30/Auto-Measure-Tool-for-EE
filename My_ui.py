"""
My_ui.py — Designer-based GUI integrated with business logic.

Usage:
    python My_ui.py          # Standalone preview (no backend)
    python main.py           # Full app with business logic

When you update layout.ui in Designer, recompile:
    .venv/Scripts/pyside6-uic layout.ui -o layout_ui.py

Then update this file if widget names changed, or just restart.
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox,
    QStatusBar, QScrollArea, QFrame, QSizePolicy, QSpacerItem,
    QGraphicsDropShadowEffect, QMessageBox, QFileDialog,
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QColor, QPalette, QCloseEvent


# ── import layout_ui generated code ──
from layout_ui import Ui_MainWindow


# ═════════════════════════════════════════════════════════════════════════════
# QSS Themes
# ═════════════════════════════════════════════════════════════════════════════

LIGHT_STYLE = """
QMainWindow, QWidget {
    background-color: #FFFFFF;
    color: #1D1D1F;
    font-family: "Segoe UI", "Helvetica Neue", sans-serif;
    font-size: 13px;
}
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }

/* Cards */
#fileCard, #signalCard, #infoCard, #labelCard {
    background-color: #FFFFFF;
    border: 1px solid #E5E5E7;
    border-radius: 10px;
    padding: 8px;
}
#fileCardTitle, #signalCardTitle, #infoCardTitle, #labelCardTitle {
    color: #86868B;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding-bottom: 4px;
}

QLineEdit {
    background-color: #FAFAFA;
    border: 1px solid #E5E5E7;
    border-radius: 6px;
    padding: 5px 8px;
    color: #1D1D1F;
}
QLineEdit:focus { border: 1px solid #007AFF; background-color: white; }
QLineEdit[readOnly="true"] { background-color: #F5F5F7; color: #86868B; }

QComboBox {
    background-color: #FAFAFA;
    border: 1px solid #E5E5E7;
    border-radius: 6px;
    padding: 5px 8px;
    color: #1D1D1F;
}

QPushButton {
    background-color: #007AFF;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 5px 14px;
    font-size: 12px;
    font-weight: 500;
}
QPushButton:hover { background-color: #0066D6; }
QPushButton:pressed { background-color: #0055B3; }
QPushButton:disabled { background-color: #E8E8ED; color: #86868B; }
QPushButton#navBtn { background-color: #E8E8ED; color: #1D1D1F; }
QPushButton#navBtn:hover { background-color: #DADADF; }

QSpinBox {
    background-color: #FAFAFA;
    border: 1px solid #E5E5E7;
    border-radius: 6px;
    padding: 5px 8px;
    color: #1D1D1F;
}

QStatusBar { background-color: #F5F5F7; border-top: 1px solid #E5E5E7; }
QStatusBar QLabel { color: #86868B; }
"""

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1E1E1E;
    color: #F5F5F7;
    font-family: "Segoe UI", "Helvetica Neue", sans-serif;
    font-size: 13px;
}
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }

#fileCard, #signalCard, #infoCard, #labelCard {
    background-color: #2C2C2E;
    border: 1px solid #3A3A3C;
    border-radius: 10px;
    padding: 8px;
}
#fileCardTitle, #signalCardTitle, #infoCardTitle, #labelCardTitle {
    color: #98989D;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding-bottom: 4px;
}

QLineEdit {
    background-color: #3A3A3C;
    border: 1px solid #3A3A3C;
    border-radius: 6px;
    padding: 5px 8px;
    color: #F5F5F7;
}
QLineEdit:focus { border: 1px solid #0A84FF; background-color: #444444; }
QLineEdit[readOnly="true"] { background-color: #2C2C2E; color: #98989D; }

QComboBox {
    background-color: #3A3A3C;
    border: 1px solid #3A3A3C;
    border-radius: 6px;
    padding: 5px 8px;
    color: #F5F5F7;
}

QPushButton {
    background-color: #0A84FF;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 5px 14px;
    font-size: 12px;
    font-weight: 500;
}
QPushButton:hover { background-color: #0070E0; }
QPushButton:pressed { background-color: #0058C0; }
QPushButton:disabled { background-color: #3A3A3C; color: #98989D; }
QPushButton#navBtn { background-color: #3A3A3C; color: #F5F5F7; }
QPushButton#navBtn:hover { background-color: #4A4A4C; }

QSpinBox {
    background-color: #3A3A3C;
    border: 1px solid #3A3A3C;
    border-radius: 6px;
    padding: 5px 8px;
    color: #F5F5F7;
}

QStatusBar { background-color: #2C2C2E; border-top: 1px solid #3A3A3C; }
QStatusBar QLabel { color: #98989D; }
"""


def apply_theme(app, theme='light'):
    s = LIGHT_STYLE if theme == 'light' else DARK_STYLE
    p = QPalette()
    if theme == 'light':
        p.setColor(QPalette.Window, QColor("#FFFFFF"))
        p.setColor(QPalette.WindowText, QColor("#1D1D1F"))
        p.setColor(QPalette.Base, QColor("#FAFAFA"))
        p.setColor(QPalette.Text, QColor("#1D1D1F"))
        p.setColor(QPalette.Button, QColor("#007AFF"))
        p.setColor(QPalette.ButtonText, QColor("#FFFFFF"))
        p.setColor(QPalette.Highlight, QColor("#007AFF"))
        p.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    else:
        p.setColor(QPalette.Window, QColor("#1E1E1E"))
        p.setColor(QPalette.WindowText, QColor("#F5F5F7"))
        p.setColor(QPalette.Base, QColor("#3A3A3C"))
        p.setColor(QPalette.Text, QColor("#F5F5F7"))
        p.setColor(QPalette.Button, QColor("#0A84FF"))
        p.setColor(QPalette.ButtonText, QColor("#FFFFFF"))
        p.setColor(QPalette.Highlight, QColor("#0A84FF"))
        p.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(p)
    app.setStyleSheet(s)


# ═════════════════════════════════════════════════════════════════════════════
# ConfigCard — reusable rounded card with shadow (pure-code helper)
# ═════════════════════════════════════════════════════════════════════════════

def wrap_card(frame, title_label):
    """Add drop shadow to a QFrame used as a card."""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(16)
    shadow.setOffset(0, 2)
    shadow.setColor(QColor(0, 0, 0, 20))
    frame.setGraphicsEffect(shadow)


# ═════════════════════════════════════════════════════════════════════════════
# MainWindow — integrates Designer UI + business logic
# ═════════════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    """Main application window. Loads layout from .ui, applies fixes + logic."""

    # ── signals (emitted by this window, connected by app.py) ──
    set_label_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.current_theme = 'light'

        # Load Designer UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Apply card shadows
        for card_name in ['fileCard', 'signalCard', 'infoCard', 'labelCard']:
            card = getattr(self.ui, card_name, None)
            if card:
                wrap_card(card, getattr(self.ui, card_name + 'Title', None))

        # ── FIX label card: rebuild layout (Designer uses absolute pos) ──
        self._fix_label_card()

        # ── Top-align all 4 cards ──
        for layout, widget in [
            (self.ui.leftLayout, self.ui.fileCard),
            (self.ui.leftLayout, self.ui.signalCard),
            (self.ui.rightLayout, self.ui.infoCard),
            (self.ui.rightLayout, self.ui.labelCard),
        ]:
            layout.setAlignment(widget, Qt.AlignTop)

        # ── Adjust column width ratio ──
        # left : right = 4 : 6 (settings column wider)
        self.ui.mainLayout.setStretch(0, 4)  # leftLayout
        self.ui.mainLayout.setStretch(1, 6)  # rightLayout

        # ── Compact spacing: card gaps + card internal padding ──
        self.ui.leftLayout.setSpacing(2)
        self.ui.rightLayout.setSpacing(2)
        self.ui.configOuter.setSpacing(2)
        for fm in [self.ui.fileLayout, self.ui.signalLayout, self.ui.infoLayout]:
            fm.setContentsMargins(0, 4, 0, 0)  # was 0,8,0,0

        # ── Apply QSS + palette ──
        apply_theme(self, self.current_theme)

        # ── Wire signals ──
        self._connect_ui_signals()

        # ── Post-init state ──
        self._setup_connection_state()

    # ─────────────────────────────────────────────────────────────────
    # Fix Designer's broken label card layout
    # ─────────────────────────────────────────────────────────────────

    def _fix_label_card(self):
        """Replace absolute-positioned widgets with a proper QFormLayout."""
        card = self.ui.labelCard
        # Remove old absolute-positioned widgets
        for w in card.findChildren(QWidget):
            w.setParent(None)

        # Set up proper layout
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        title = QLabel(card)
        title.setObjectName('labelCardTitle')
        title.setText('CHANNEL LABELS')
        vbox.addWidget(title)

        content = QWidget(card)
        form = QFormLayout(content)
        form.setContentsMargins(0, 4, 0, 0)
        form.setSpacing(6)

        # CH1 row: edit + P/N badge
        self.ch1_edit = QLineEdit()
        self.ch1_edit.setMinimumWidth(120)
        self.ch1_edit.setMaximumWidth(170)
        self.ch1_edit.setPlaceholderText('CH1…')

        self.pn_badge = QLabel('P')
        self.pn_badge.setFixedSize(22, 22)
        self.pn_badge.setAlignment(Qt.AlignCenter)
        self.pn_badge.setStyleSheet('background:#007AFF;color:white;border-radius:11px;font-weight:600;font-size:10px;')

        ch1_row = QWidget()
        ch1_lay = QHBoxLayout(ch1_row)
        ch1_lay.setContentsMargins(0, 0, 0, 0)
        ch1_lay.setSpacing(4)
        ch1_lay.addWidget(self.ch1_edit, 1)
        ch1_lay.addWidget(self.pn_badge)

        form.addRow('CH1:', ch1_row)

        self.ch2_edit = QLineEdit()
        self.ch2_edit.setMinimumWidth(160)
        self.ch2_edit.setMaximumWidth(220)
        self.ch2_edit.setPlaceholderText('CH2…')

        self.ch3_edit = QLineEdit()
        self.ch3_edit.setMinimumWidth(160)
        self.ch3_edit.setMaximumWidth(220)
        self.ch3_edit.setPlaceholderText('CH3…')

        self.ch4_edit = QLineEdit()
        self.ch4_edit.setMinimumWidth(160)
        self.ch4_edit.setMaximumWidth(220)
        self.ch4_edit.setPlaceholderText('CH4…')

        form.addRow('CH2:', self.ch2_edit)
        form.addRow('CH3:', self.ch3_edit)
        form.addRow('CH4:', self.ch4_edit)

        self.set_label_btn = QPushButton('Set Label')
        self.set_label_btn.setMinimumWidth(100)
        self.set_label_btn.setMaximumWidth(220)
        self.set_label_btn.clicked.connect(self.set_label_clicked.emit)

        btn_row = QWidget()
        btn_lay = QHBoxLayout(btn_row)
        btn_lay.setContentsMargins(0, 4, 0, 0)
        btn_lay.addWidget(self.set_label_btn)
        btn_lay.addStretch()

        form.addRow(btn_row)
        vbox.addWidget(content)

        self.ui.labelCard = card  # ensure ref is correct

    # ─────────────────────────────────────────────────────────────────
    # Signal wiring (UI → internal slots)
    # ─────────────────────────────────────────────────────────────────

    def _connect_ui_signals(self):
        """Connect all button clicks and state-change signals."""
        # Navigation
        self.ui.lastBtn.clicked.connect(lambda: print('[Nav] Last'))
        self.ui.nextBtn.clicked.connect(lambda: print('[Nav] Next'))
        self.ui.jumpBtn.clicked.connect(
            lambda: print(f'[Nav] Jump to {self.ui.jumpSpin.value()}'))

        # Actions
        self.ui.connectBtn.clicked.connect(lambda: print('[Action] Connect'))
        self.ui.reconnectBtn.clicked.connect(lambda: print('[Action] Reconnect'))
        self.ui.saveCloseBtn.clicked.connect(lambda: print('[Action] Save & Close'))
        self.ui.savePicBtn.clicked.connect(lambda: print('[Action] Save Pic'))
        self.ui.setMsoBtn.clicked.connect(lambda: print('[Action] Set MSO'))

        # File path Browse buttons
        self.ui.excelBrowse.clicked.connect(self._browse_excel)
        self.ui.picBrowse.clicked.connect(self._browse_pic)

        # Theme toggle
        self.ui.themeBtn.clicked.connect(self._toggle_theme)

    # ─────────────────────────────────────────────────────────────────
    # Connection state management
    # ─────────────────────────────────────────────────────────────────

    def _setup_connection_state(self):
        """Initialize connection-related UI state."""
        self._connected = False
        self.ui.reconnectBtn.setVisible(False)
        self._update_status_badge(False)

    def _update_status_badge(self, connected):
        """Update the status badge color."""
        badge = self.ui.statusBadge
        color = '#30D158' if connected else '#FF3B30'
        badge.setStyleSheet(
            f'background:{color};border-radius:7px;border:2px solid {color};')

    def set_connection_status(self, connected):
        self._connected = connected
        self._update_status_badge(connected)
        if connected:
            self.ui.reconnectBtn.setVisible(False)
            self.ui.connectBtn.setText('Connected')
        else:
            self.ui.reconnectBtn.setVisible(True)
            self.ui.connectBtn.setText('Connect')

    def set_status(self, msg):
        self.ui.statusLabel.setText(msg)

    # ─────────────────────────────────────────────────────────────────
    # File dialogs (placeholder — real logic in app.py)
    # ─────────────────────────────────────────────────────────────────

    def _browse_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Select Excel Report', '', 'Excel files (*.xlsx *.xls)')
        if path:
            self.ui.excelEdit.setText(path)
            print(f'[File] Excel: {path}')

    def _browse_pic(self):
        path = QFileDialog.getExistingDirectory(self, 'Select Save Folder', '')
        if path:
            self.ui.picEdit.setText(path)
            print(f'[File] Pic folder: {path}')

    # ─────────────────────────────────────────────────────────────────
    # Theme toggle
    # ─────────────────────────────────────────────────────────────────

    def _toggle_theme(self):
        self.current_theme = 'dark' if self.current_theme == 'light' else 'light'
        apply_theme(self, self.current_theme)
        self.ui.themeBtn.setText('☀️' if self.current_theme == 'dark' else 'Theme')
        print(f'[Theme] Switched to {self.current_theme}')


# ═════════════════════════════════════════════════════════════════════════════
# Standalone preview
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    print('My_ui.py — Standalone preview running.')
    print('Layout from layout.ui, column ratio 4:6, compact spacing.')
    sys.exit(app.exec())
