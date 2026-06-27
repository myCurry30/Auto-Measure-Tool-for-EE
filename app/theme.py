"""macOS-style QSS themes for light and dark modes."""
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor


# ========== LIGHT THEME (macOS style) ==========
LIGHT_STYLE = """
/* === Window === */
QMainWindow, QWidget {
    background-color: #FFFFFF;
    color: #1D1D1F;
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", sans-serif;
    font-size: 13px;
}

/* === Menu Bar & Toolbar === */
QMenuBar { background-color: #F5F5F7; border-bottom: 1px solid #E5E5E7; padding: 2px 8px; font-size: 13px; }
QMenuBar::item { padding: 4px 12px; border-radius: 5px; color: #1D1D1F; }
QMenuBar::item:selected { background-color: rgba(0,0,0,0.06); }
QMenu { background-color: #FFFFFF; border: 1px solid #DADADF; border-radius: 8px; padding: 4px; margin: 4px 0 0 0; }
QMenu::item { padding: 6px 32px 6px 12px; border-radius: 5px; color: #1D1D1F; }
QMenu::item:selected { background-color: #007AFF; color: white; }
QMenu::separator { height: 1px; background: #E5E5E7; margin: 4px 8px; }
QToolBar { background: transparent; border: none; spacing: 4px; padding: 0 4px; }
QToolBar QToolButton { padding: 4px 8px; border-radius: 5px; color: #1D1D1F; }
QToolBar QToolButton:hover { background-color: rgba(0,0,0,0.06); }

/* === Scroll Area === */
QScrollArea {
    border: none;
    background: transparent;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}

/* === Sidebar === */
#sidebarWidget {
    background-color: #F5F5F7;
    border-radius: 8px;
    margin: 4px;
}

#sidebarTitle {
    color: #86868B;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 8px 16px 4px 16px;
}

QListWidget {
    background-color: #F5F5F7;
    border: none;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}

QListWidget::item {
    padding: 8px 12px;
    border-radius: 6px;
    color: #1D1D1F;
    margin: 1px;
}

QListWidget::item:selected {
    background-color: #007AFF;
    color: white;
}

QListWidget::item:hover:!selected {
    background-color: rgba(0, 0, 0, 0.04);
}

/* === Config Cards === */
#configCard {
    background-color: #FFFFFF;
    border: 1px solid #E5E5E7;
    border-radius: 10px;
    padding: 16px;
}

#cardTitle {
    color: #86868B;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}

/* === Form Labels === */
QLabel {
    color: #1D1D1F;
}

QLabel#formLabel {
    color: #86868B;
    font-size: 12px;
    font-weight: 500;
}

QLabel[readOnly="true"] {
    color: #86868B;
    font-style: italic;
}

/* === Line Edit === */
QLineEdit {
    background-color: #FAFAFA;
    border: 1px solid #E5E5E7;
    border-radius: 6px;
    padding: 6px 10px;
    color: #1D1D1F;
    selection-background-color: #007AFF;
    selection-color: white;
}

QLineEdit:focus {
    border: 1px solid #007AFF;
    background-color: white;
}

QLineEdit:disabled {
    background-color: #F5F5F7;
    color: #86868B;
    border: 1px solid #E5E5E7;
}

QLineEdit[readOnly="true"] {
    background-color: #F5F5F7;
    color: #86868B;
}

/* === Buttons === */
QPushButton {
    background-color: #007AFF;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #0066D6;
}

QPushButton:pressed {
    background-color: #0055B3;
}

QPushButton:disabled {
    background-color: #E8E8ED;
    color: #86868B;
}

QPushButton#secondary {
    background-color: #E8E8ED;
    color: #1D1D1F;
}

QPushButton#secondary:hover {
    background-color: #DADADF;
}

QPushButton#secondary:pressed {
    background-color: #C8C8CD;
}

QPushButton#navButton {
    background-color: #E8E8ED;
    color: #1D1D1F;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 600;
}

QPushButton#navButton:hover {
    background-color: #DADADF;
}

QPushButton#navButton:pressed {
    background-color: #C8C8CD;
}

/* === Status Badge === */
#statusBadge {
    border-radius: 10px;
    border: 2px solid;
}

#statusBadge[connected="false"] {
    border-color: #FF3B30;
    background-color: rgba(255, 59, 48, 0.1);
}

#statusBadge[connected="true"] {
    border-color: #34C759;
    background-color: rgba(52, 199, 89, 0.1);
}

/* === SpinBox === */
QSpinBox {
    background-color: #FAFAFA;
    border: 1px solid #E5E5E7;
    border-radius: 6px;
    padding: 6px 10px;
    color: #1D1D1F;
}

QSpinBox:focus {
    border: 1px solid #007AFF;
    background-color: white;
}

QSpinBox::up-button, QSpinBox::down-button {
    border: none;
    background: transparent;
    width: 20px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: rgba(0, 0, 0, 0.04);
}

/* === Status Bar === */
QStatusBar {
    background-color: #F5F5F7;
    border-top: 1px solid #E5E5E7;
    color: #86868B;
}

QStatusBar QLabel {
    color: #86868B;
}

QStatusBar QPushButton {
    background: transparent;
    border: none;
    color: #86868B;
    padding: 4px 8px;
}

QStatusBar QPushButton:hover {
    color: #007AFF;
}
"""


# ========== DARK THEME (macOS dark mode) ==========
DARK_STYLE = """
/* === Window === */
QMainWindow, QWidget {
    background-color: #1E1E1E;
    color: #F5F5F7;
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", sans-serif;
    font-size: 13px;
}

/* === Scroll Area === */
QScrollArea {
    border: none;
    background: transparent;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}

/* === Menu Bar & Toolbar (Dark) === */
QMenuBar { background-color: #2C2C2E; border-bottom: 1px solid #3A3A3C; padding: 2px 8px; font-size: 13px; }
QMenuBar::item { padding: 4px 12px; border-radius: 5px; color: #F5F5F7; }
QMenuBar::item:selected { background-color: rgba(255,255,255,0.08); }
QMenu { background-color: #2C2C2E; border: 1px solid #3A3A3C; border-radius: 8px; padding: 4px; margin: 4px 0 0 0; }
QMenu::item { padding: 6px 32px 6px 12px; border-radius: 5px; color: #F5F5F7; }
QMenu::item:selected { background-color: #0A84FF; color: white; }
QMenu::separator { height: 1px; background: #3A3A3C; margin: 4px 8px; }
QToolBar { background: transparent; border: none; spacing: 4px; padding: 0 4px; }
QToolBar QToolButton { padding: 4px 8px; border-radius: 5px; color: #F5F5F7; }
QToolBar QToolButton:hover { background-color: rgba(255,255,255,0.08); }

/* === Sidebar === */
#sidebarWidget {
    background-color: #2C2C2E;
    border-radius: 8px;
    margin: 4px;
}

#sidebarTitle {
    color: #98989D;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 8px 16px 4px 16px;
}

QListWidget {
    background-color: #2C2C2E;
    border: none;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}

QListWidget::item {
    padding: 8px 12px;
    border-radius: 6px;
    color: #F5F5F7;
    margin: 1px;
}

QListWidget::item:selected {
    background-color: #0A84FF;
    color: white;
}

QListWidget::item:hover:!selected {
    background-color: rgba(255, 255, 255, 0.06);
}

/* === Config Cards === */
#configCard {
    background-color: #2C2C2E;
    border: 1px solid #3A3A3C;
    border-radius: 10px;
    padding: 16px;
}

#cardTitle {
    color: #98989D;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}

/* === Form Labels === */
QLabel {
    color: #F5F5F7;
}

QLabel#formLabel {
    color: #98989D;
    font-size: 12px;
    font-weight: 500;
}

QLabel[readOnly="true"] {
    color: #98989D;
    font-style: italic;
}

/* === Line Edit === */
QLineEdit {
    background-color: #3A3A3C;
    border: 1px solid #3A3A3C;
    border-radius: 6px;
    padding: 6px 10px;
    color: #F5F5F7;
    selection-background-color: #0A84FF;
    selection-color: white;
}

QLineEdit:focus {
    border: 1px solid #0A84FF;
    background-color: #444444;
}

QLineEdit:disabled {
    background-color: #2C2C2E;
    color: #98989D;
    border: 1px solid #3A3A3C;
}

QLineEdit[readOnly="true"] {
    background-color: #2C2C2E;
    color: #98989D;
}

/* === Buttons === */
QPushButton {
    background-color: #0A84FF;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #0070E0;
}

QPushButton:pressed {
    background-color: #0058C0;
}

QPushButton:disabled {
    background-color: #3A3A3C;
    color: #98989D;
}

QPushButton#secondary {
    background-color: #3A3A3C;
    color: #F5F5F7;
}

QPushButton#secondary:hover {
    background-color: #4A4A4C;
}

QPushButton#secondary:pressed {
    background-color: #5A5A5C;
}

QPushButton#navButton {
    background-color: #3A3A3C;
    color: #F5F5F7;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 600;
}

QPushButton#navButton:hover {
    background-color: #4A4A4C;
}

QPushButton#navButton:pressed {
    background-color: #5A5A5C;
}

/* === Status Badge === */
#statusBadge {
    border-radius: 10px;
    border: 2px solid;
}

#statusBadge[connected="false"] {
    border-color: #FF453A;
    background-color: rgba(255, 69, 58, 0.15);
}

#statusBadge[connected="true"] {
    border-color: #30D158;
    background-color: rgba(48, 209, 88, 0.15);
}

/* === SpinBox === */
QSpinBox {
    background-color: #3A3A3C;
    border: 1px solid #3A3A3C;
    border-radius: 6px;
    padding: 6px 10px;
    color: #F5F5F7;
}

QSpinBox:focus {
    border: 1px solid #0A84FF;
    background-color: #444444;
}

QSpinBox::up-button, QSpinBox::down-button {
    border: none;
    background: transparent;
    width: 20px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: rgba(255, 255, 255, 0.06);
}

/* === Status Bar === */
QStatusBar {
    background-color: #2C2C2E;
    border-top: 1px solid #3A3A3C;
    color: #98989D;
}

QStatusBar QLabel {
    color: #98989D;
}

QStatusBar QPushButton {
    background: transparent;
    border: none;
    color: #98989D;
    padding: 4px 8px;
}

QStatusBar QPushButton:hover {
    color: #0A84FF;
}
"""


def apply_theme(app, theme_name='light'):
    """Apply macOS-style theme to application.

    Args:
        app: QApplication instance
        theme_name: 'light' or 'dark'
    """
    if theme_name == 'light':
        style = LIGHT_STYLE
        # Light theme palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#FFFFFF"))
        palette.setColor(QPalette.WindowText, QColor("#1D1D1F"))
        palette.setColor(QPalette.Base, QColor("#FAFAFA"))
        palette.setColor(QPalette.AlternateBase, QColor("#F5F5F7"))
        palette.setColor(QPalette.ToolTipBase, QColor("#FFFFFF"))
        palette.setColor(QPalette.ToolTipText, QColor("#1D1D1F"))
        palette.setColor(QPalette.Text, QColor("#1D1D1F"))
        palette.setColor(QPalette.Button, QColor("#007AFF"))
        palette.setColor(QPalette.ButtonText, QColor("#FFFFFF"))
        palette.setColor(QPalette.BrightText, QColor("#FF0000"))
        palette.setColor(QPalette.Link, QColor("#007AFF"))
        palette.setColor(QPalette.Highlight, QColor("#007AFF"))
        palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        app.setPalette(palette)
    else:
        style = DARK_STYLE
        # Dark theme palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#1E1E1E"))
        palette.setColor(QPalette.WindowText, QColor("#F5F5F7"))
        palette.setColor(QPalette.Base, QColor("#3A3A3C"))
        palette.setColor(QPalette.AlternateBase, QColor("#2C2C2E"))
        palette.setColor(QPalette.ToolTipBase, QColor("#2C2C2E"))
        palette.setColor(QPalette.ToolTipText, QColor("#F5F5F7"))
        palette.setColor(QPalette.Text, QColor("#F5F5F7"))
        palette.setColor(QPalette.Button, QColor("#0A84FF"))
        palette.setColor(QPalette.ButtonText, QColor("#FFFFFF"))
        palette.setColor(QPalette.BrightText, QColor("#FF0000"))
        palette.setColor(QPalette.Link, QColor("#0A84FF"))
        palette.setColor(QPalette.Highlight, QColor("#0A84FF"))
        palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        app.setPalette(palette)

    app.setStyleSheet(style)