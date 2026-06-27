"""Action bar with reconnect and status indicator."""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Signal


class StatusBadge(QWidget):
    """Circular status indicator with reconnect capability."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.connected = False
        self.reconnecting = False
        self.setFixedSize(14, 14)
        self.update_style()

    def set_connected(self, connected):
        self.connected = connected
        self.reconnecting = False
        self.update_style()

    def set_reconnecting(self, reconnecting):
        self.reconnecting = reconnecting
        self.update_style()

    def update_style(self):
        if self.reconnecting:
            color = "#FF9500"
        elif self.connected:
            color = "#30D158"
        else:
            color = "#FF3B30"
        self.setStyleSheet(
            f"background-color: {color};"
            f"border-radius: 7px;"
            f"border: 2px solid {color};"
        )


class ActionBar(QWidget):
    """Action bar with reconnect button and status indicator."""

    reconnect_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._connected = False
        self._last_method = 'usb_gpib'
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.status_badge = StatusBadge()
        layout.addWidget(self.status_badge)

        self.reconnect_btn = QPushButton("🔄 Reconnect")
        self.reconnect_btn.setObjectName("secondary")
        self.reconnect_btn.setVisible(False)
        self.reconnect_btn.clicked.connect(self.reconnect_clicked.emit)
        layout.addWidget(self.reconnect_btn)

        layout.addStretch()

    def set_connection_status(self, connected):
        self._connected = connected
        self.status_badge.set_connected(connected)
        if connected:
            self.reconnect_btn.setVisible(False)
        else:
            self.reconnect_btn.setVisible(True)

    def set_reconnecting(self, reconnecting):
        self.status_badge.set_reconnecting(reconnecting)
        if reconnecting:
            self.reconnect_btn.setEnabled(False)
            self.reconnect_btn.setText("🔄 Reconnecting...")
        else:
            self.reconnect_btn.setEnabled(True)
            self.reconnect_btn.setText("🔄 Reconnect")

    def set_connection_info(self, method, ip='', port=4000):
        self._last_method = method

    def get_last_method(self):
        return self._last_method
