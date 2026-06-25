"""Test item sidebar widget with macOS-style QListWidget."""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QListWidget, QListWidgetItem, QScrollArea)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap


class SidebarWidget(QWidget):
    """Sidebar showing test items in a macOS-style list."""

    sheet_selected = Signal(str)  # Emits selected sheet name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Logo area
        self.logo_label = QLabel()
        logo_path = "resources/NC logo.png"
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(264, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
        self.logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo_label)

        # Title
        title = QLabel("Sheets")
        title.setObjectName("sidebarTitle")
        layout.addWidget(title)

        # Scroll area for list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # List widget
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("sidebarWidget")
        self.list_widget.currentRowChanged.connect(self._on_sheet_selected)

        scroll.setWidget(self.list_widget)
        layout.addWidget(scroll)

        # Current sheet badge
        self.item_badge = QLabel("Current: -")
        self.item_badge.setStyleSheet("color: #86868B; font-size: 11px; padding: 4px;")
        layout.addWidget(self.item_badge)

        # Load sheets from Excel (will be called when file is selected)
        # self._load_sheets_from_excel()  # Commented out, will be called by ConfigPanel

    def load_sheets(self, sheet_names):
        """Load sheet names from a list (no Excel access needed).

        Called by MainWindow when sheets are loaded from Excel.
        """
        self.list_widget.clear()
        for name in sheet_names:
            QListWidgetItem(name, self.list_widget)
        print(f"[Sidebar] Loaded {len(sheet_names)} sheets")

    def _load_sheets_from_excel(self):
        """Load sheet names from the app state's Excel instance."""
        # This method is kept for backward compatibility but
        # prefer using load_sheets() directly from MainWindow.
        from ..app.state import AppState
        parent = self.parent()
        if parent and hasattr(parent, 'state'):
            state = parent.state
        else:
            # Try to find MainWindow by walking up
            w = self.parent()
            while w:
                if hasattr(w, 'state'):
                    state = w.state
                    break
                w = w.parent()
            else:
                print("[Sidebar] Could not find AppState")
                return

        if not state or not state.xls:
            print("[Sidebar] No Excel instance available")
            return

        try:
            sheet_names = state.xls.get_sheet_names()
            self.load_sheets(sheet_names)
        except Exception as e:
            print(f"[Sidebar] Error: {e}")

    def _on_sheet_selected(self, row):
        """Handle sheet selection."""
        if 0 <= row < self.list_widget.count():
            sheet_name = self.list_widget.item(row).text()
            self.sheet_selected.emit(sheet_name)
            self.item_badge.setText(f"Current: {sheet_name}")
            print(f"[Sidebar] Selected sheet: {sheet_name}")

    def set_current_item(self, test_item):
        """Set the currently selected test item."""
        # Reverse map
        row_map = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7, 9: 8, 10: 9, 12: 10}
        row = row_map.get(test_item)
        if row is not None:
            self.list_widget.setCurrentRow(row)