"""Navigation bar with Previous, Next, and Jump buttons."""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSpinBox
from PySide6.QtCore import Signal


class NavBar(QWidget):
    """Navigation control bar."""

    last_clicked = Signal()
    next_clicked = Signal()
    jump_clicked = Signal(int)  # Emits jump target row

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Navigation buttons
        self.last_btn = QPushButton("<--")
        self.last_btn.setObjectName("navButton")
        self.last_btn.clicked.connect(lambda: (print("[NavBar] Last clicked"), self.last_clicked.emit()))

        self.next_btn = QPushButton("-->")
        self.next_btn.setObjectName("navButton")
        self.next_btn.clicked.connect(lambda: (print("[NavBar] Next clicked"), self.next_clicked.emit()))

        # Jump control
        jump_label = QLabel("Jump to:")
        jump_label.setStyleSheet("font-size: 13px;")

        self.jump_spin = QSpinBox()
        self.jump_spin.setRange(1, 999)
        self.jump_spin.setValue(8)
        self.jump_spin.setMinimumWidth(80)

        self.jump_btn = QPushButton("Jump")
        self.jump_btn.setObjectName("navButton")
        self.jump_btn.clicked.connect(self._on_jump)

        layout.addWidget(self.last_btn)
        layout.addWidget(self.next_btn)
        layout.addWidget(jump_label)
        layout.addWidget(self.jump_spin)
        layout.addWidget(self.jump_btn)
        layout.addStretch()

    def _on_jump(self):
        target = self.jump_spin.value()
        print(f"[NavBar] Jump to {target}")
        self.jump_clicked.emit(target)