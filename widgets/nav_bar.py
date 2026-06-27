"""Navigation bar with Previous, Next, and Jump buttons."""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSpinBox, QVBoxLayout, QLineEdit
from PySide6.QtCore import Signal, Qt, QEvent


class NavBar(QWidget):
    """Navigation control bar."""

    last_clicked = Signal()
    next_clicked = Signal()
    jump_clicked = Signal(int)  # Emits jump target row

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_row = 8
        self.setup_ui()

    def eventFilter(self, obj, event):
        if obj is self.jump_edit and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Up:
                self._delta_jump(1)
                return True
            elif event.key() == Qt.Key.Key_Down:
                self._delta_jump(-1)
                return True
        return super().eventFilter(obj, event)

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Navigation buttons
        self.last_btn = QPushButton("◀ Last")
        self.last_btn.setObjectName("navButton")
        self.last_btn.setToolTip("Go to previous test item")
        self.last_btn.clicked.connect(lambda: (print("[NavBar] Last clicked"), self.last_clicked.emit()))

        self.next_btn = QPushButton("Next ▶")
        self.next_btn.setObjectName("navButton")
        self.next_btn.setToolTip("Go to next test item")
        self.next_btn.clicked.connect(lambda: (print("[NavBar] Next clicked"), self.next_clicked.emit()))

        # Jump control: number input + triangle buttons
        jump_w = QWidget()
        jump_w.setFixedWidth(66)
        jump_lay = QHBoxLayout(jump_w)
        jump_lay.setContentsMargins(0, 0, 0, 0)
        jump_lay.setSpacing(0)

        self.jump_edit = QLineEdit()
        self.jump_edit.setText("8")
        self.jump_edit.setAlignment(Qt.AlignCenter)
        self.jump_edit.setStyleSheet(
            "QLineEdit { border: 1px solid #E5E5E7; border-radius: 4px 0 0 4px; padding: 3px 4px; }")
        self.jump_edit.returnPressed.connect(self._on_jump)
        self.jump_edit.installEventFilter(self)
        jump_lay.addWidget(self.jump_edit, 1)

        arrows_w = QWidget()
        arrows_w.setFixedWidth(16)
        arrows_lay = QVBoxLayout(arrows_w)
        arrows_lay.setContentsMargins(0, 0, 0, 0)
        arrows_lay.setSpacing(0)

        ARROW_QSS = "QPushButton { background:#333; color:#FFF; border:none; font-size:8px; padding:0; } QPushButton:hover { background:#555; }"
        up_btn = QPushButton("▲")
        up_btn.setStyleSheet(ARROW_QSS + "QPushButton { border-radius: 0 4px 0 0; }")
        up_btn.setFixedHeight(12)
        up_btn.clicked.connect(lambda: self._delta_jump(1))
        arrows_lay.addWidget(up_btn)

        down_btn = QPushButton("▼")
        down_btn.setStyleSheet(ARROW_QSS + "QPushButton { border-radius: 0 0 4px 0; }")
        down_btn.setFixedHeight(12)
        down_btn.clicked.connect(lambda: self._delta_jump(-1))
        arrows_lay.addWidget(down_btn)

        jump_lay.addWidget(arrows_w)

        self.jump_btn = QPushButton("Jump")
        self.jump_btn.setObjectName("navButton")
        self.jump_btn.setToolTip("Jump to specific test item number")
        self.jump_btn.clicked.connect(self._on_jump)

        layout.addWidget(self.last_btn)
        layout.addWidget(self.next_btn)
        layout.addSpacing(8)
        layout.addWidget(jump_w)
        layout.addWidget(self.jump_btn)
        layout.addStretch()

    def _delta_jump(self, delta):
        try:
            v = int(self.jump_edit.text()) + delta
            if v >= 1:
                self.jump_edit.setText(str(v))
        except ValueError:
            pass

    def clamp_min(self, min_val):
        """Ensure jump value is >= min_val."""
        try:
            v = int(self.jump_edit.text())
            if v < min_val:
                self.jump_edit.setText(str(min_val))
        except ValueError:
            self.jump_edit.setText(str(min_val))

    def _on_jump(self):
        try:
            target = int(self.jump_edit.text())
        except ValueError:
            target = 1
        if target < 1:
            target = 1
            self.jump_edit.setText(str(target))
        print(f"[NavBar] Jump to {target}")
        self.jump_clicked.emit(target)