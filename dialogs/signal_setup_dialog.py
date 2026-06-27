"""Signal setup dialog — configure which signals to read from Excel."""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                QCheckBox, QSpinBox, QComboBox, QPushButton,
                                QDialogButtonBox, QFormLayout, QGroupBox)
from PySide6.QtCore import Qt

# Excel column letters: index 1→A, 2→B, ..., 26→Z, 27→AA, ...
_COL_LETTERS = [""]  # 0-index placeholder
for i in range(1, 53):
    if i <= 26:
        _COL_LETTERS.append(chr(64 + i))
    else:
        _COL_LETTERS.append("A" + chr(64 + i - 26))


def col_to_letter(n):
    """Convert 1-based column number to Excel letter."""
    if 1 <= n < len(_COL_LETTERS):
        return _COL_LETTERS[n]
    return str(n)


def letter_to_col(s):
    """Convert Excel letter to 1-based column number."""
    try:
        return _COL_LETTERS.index(s.upper())
    except ValueError:
        return 1


class SignalSetupDialog(QDialog):
    """Dialog for configuring which signals to read and their Excel positions."""

    def __init__(self, parent=None, defaults=None):
        super().__init__(parent)
        self.setWindowTitle("Signal Setup")
        self.setMinimumWidth(420)
        self.defaults = defaults or [
            {"enable": True, "row": 8, "col": 3},
            {"enable": True, "row": 9, "col": 3},
            {"enable": True, "row": 10, "col": 3},
            {"enable": False, "row": 11, "col": 3},
        ]
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        info = QLabel("Select signals to read from Excel and set their cell positions.\n"
                       "Column uses Excel letters (A, B, C…).")
        info.setWordWrap(True)
        info.setStyleSheet("color: #86868B; font-size: 12px;")
        layout.addWidget(info)

        # Signal rows
        self.sig_checks = []
        self.sig_rows = []
        self.sig_cols = []

        group = QGroupBox("Signal Configuration")
        form = QFormLayout(group)
        form.setSpacing(6)

        for i, d in enumerate(self.defaults):
            row_w = QWidget()
            row_lay = QHBoxLayout(row_w)
            row_lay.setContentsMargins(0, 0, 0, 0)
            row_lay.setSpacing(6)

            cb = QCheckBox()
            cb.setChecked(d["enable"])
            row_lay.addWidget(cb)
            self.sig_checks.append(cb)

            rspin = QSpinBox()
            rspin.setRange(1, 999)
            rspin.setValue(d["row"])
            rspin.setPrefix("Row: ")
            rspin.setFixedWidth(90)
            row_lay.addWidget(rspin)
            self.sig_rows.append(rspin)

            ccombo = QComboBox()
            ccombo.addItems([_COL_LETTERS[c] for c in range(1, 27)])  # A-Z
            ccombo.setCurrentText(col_to_letter(d["col"]))
            ccombo.setFixedWidth(80)
            row_lay.addWidget(QLabel("Col:"))
            row_lay.addWidget(ccombo)
            self.sig_cols.append(ccombo)

            row_lay.addStretch()
            form.addRow(f"Signal {i + 1}:", row_w)

        layout.addWidget(group)

        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_config(self):
        """Return list of signal configs."""
        result = []
        for i in range(4):
            result.append({
                "enable": self.sig_checks[i].isChecked(),
                "row": self.sig_rows[i].value(),
                "col": letter_to_col(self.sig_cols[i].currentText()),
            })
        return result
