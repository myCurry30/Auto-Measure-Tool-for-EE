"""Sheet selection dialog with confirmation."""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox, QMessageBox


class SheetSelectionDialog(QDialog):
    """Dialog for selecting Excel sheet with confirmation."""

    def __init__(self, sheet_names, parent=None):
        super().__init__(parent)
        self.sheet_names = sheet_names
        self.selected_sheet = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select Excel Sheet:"))

        self.sheet_combo = QComboBox()
        self.sheet_combo.addItems(self.sheet_names)
        layout.addWidget(self.sheet_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        self.selected_sheet = self.sheet_combo.currentText()
        super().accept()

    def reject(self):
        # Reset to previous selection if cancelled
        current_sheet = self.parent().state.sheet_name if hasattr(self.parent(), 'state') else ""
        if current_sheet:
            self.sheet_combo.setCurrentText(current_sheet)
        super().reject()