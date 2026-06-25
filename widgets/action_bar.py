"""Action bar with operation buttons and connection status."""
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLabel,
                                QVBoxLayout)
from PySide6.QtCore import Signal, Qt, QTimer


class StatusBadge(QWidget):
    """Circular status indicator with reconnect capability."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.connected = False
        self.reconnecting = False
        self.setFixedSize(14, 14)
        self.update_style()

    def set_connected(self, connected):
        """Update connection state."""
        self.connected = connected
        self.reconnecting = False
        self.update_style()

    def set_reconnecting(self, reconnecting):
        """Show reconnecting state."""
        self.reconnecting = reconnecting
        self.update_style()

    def update_style(self):
        """Update badge style based on connection state."""
        if self.reconnecting:
            color = "#FF9500"  # Orange for reconnecting
            border = "#FF9500"
        elif self.connected:
            color = "#30D158"  # Green
            border = "#30D158"
        else:
            color = "#FF3B30"  # Red
            border = "#FF3B30"
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {color};
                border-radius: 7px;
                border: 2px solid {border};
            }}
        """)


class ActionBar(QWidget):
    """Action button bar with connection status and reconnect support."""

    connect_clicked = Signal()           # Open connect dialog
    reconnect_clicked = Signal()         # Reconnect with last method
    save_close_clicked = Signal()
    save_pic_clicked = Signal()
    set_label_clicked = Signal()
    set_mso_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._connected = False
        self._last_method = 'usb_gpib'
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Connect button with status indicator
        connect_container = QWidget()
        connect_layout = QHBoxLayout(connect_container)
        connect_layout.setContentsMargins(0, 0, 0, 0)
        connect_layout.setSpacing(8)

        self.connect_btn = QPushButton("🔗 Connect")
        self.connect_btn.clicked.connect(lambda: (
            print("[ActionBar] Connect clicked"), self.connect_clicked.emit()
        ))

        self.status_badge = StatusBadge()
        connect_layout.addWidget(self.connect_btn)
        connect_layout.addWidget(self.status_badge)

        # Reconnect button (hidden initially)
        self.reconnect_btn = QPushButton("🔄 Reconnect")
        self.reconnect_btn.setObjectName("secondary")
        self.reconnect_btn.setVisible(False)
        self.reconnect_btn.clicked.connect(lambda: (
            print("[ActionBar] Reconnect clicked"), self.reconnect_clicked.emit()
        ))

        # Connection info label
        self.conn_info_label = QLabel("")
        self.conn_info_label.setStyleSheet("color: #86868B; font-size: 11px;")

        layout.addWidget(connect_container)
        layout.addWidget(self.reconnect_btn)
        layout.addWidget(self.conn_info_label)

        # Other action buttons
        self.save_close_btn = QPushButton("Save & Close")
        self.save_close_btn.setObjectName("secondary")
        self.save_close_btn.clicked.connect(lambda: (
            print("[ActionBar] Save & Close clicked"), self.save_close_clicked.emit()
        ))

        self.save_pic_btn = QPushButton("Save Picture")
        self.save_pic_btn.clicked.connect(lambda: (
            print("[ActionBar] Save Picture clicked"), self.save_pic_clicked.emit()
        ))

        self.set_label_btn = QPushButton("Set Label")
        self.set_label_btn.setObjectName("secondary")
        self.set_label_btn.clicked.connect(lambda: (
            print("[ActionBar] Set Label clicked"), self.set_label_clicked.emit()
        ))

        self.set_mso_btn = QPushButton("Set MSO")
        self.set_label_btn.setObjectName("secondary")
        self.set_mso_btn.clicked.connect(lambda: (
            print("[ActionBar] Set MSO clicked"), self.set_mso_clicked.emit()
        ))

        layout.addWidget(self.save_close_btn)
        layout.addWidget(self.save_pic_btn)
        layout.addWidget(self.set_label_btn)
        layout.addWidget(self.set_mso_btn)
        layout.addStretch()

    def set_connection_status(self, connected):
        """Update connection status badge and buttons."""
        self._connected = connected
        self.status_badge.set_connected(connected)

        if connected:
            self.reconnect_btn.setVisible(False)
            self.connect_btn.setText("🔗 Connected")
        else:
            self.reconnect_btn.setVisible(True)
            self.connect_btn.setText("🔗 Connect")

        print(f"[ActionBar] Connection status: {'Connected' if connected else 'Disconnected'}")

    def set_reconnecting(self, reconnecting):
        """Show reconnecting state."""
        self.status_badge.set_reconnecting(reconnecting)
        if reconnecting:
            self.reconnect_btn.setEnabled(False)
            self.reconnect_btn.setText("🔄 Reconnecting...")
        else:
            self.reconnect_btn.setEnabled(True)
            self.reconnect_btn.setText("🔄 Reconnect")

    def set_connection_info(self, method, ip='', port=4000):
        """Display current connection info."""
        self._last_method = method
        if method == 'ip':
            self.conn_info_label.setText(f"IP: {ip}:{port}")
        else:
            self.conn_info_label.setText("GPIB/USB")

    def get_last_method(self):
        """Return last used connection method."""
        return self._last_method
