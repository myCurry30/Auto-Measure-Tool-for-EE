"""Connection dialog for choosing connection method and entering IP address."""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QRadioButton, QButtonGroup,
                                QLineEdit, QSpinBox, QMessageBox, QGroupBox,
                                QFormLayout)
from PySide6.QtCore import Qt


class ConnectDialog(QDialog):
    """Dialog for selecting connection method and entering IP settings."""

    def __init__(self, parent=None, last_method='usb_gpib', last_ip='', last_port=4000):
        super().__init__(parent)
        self.setWindowTitle("Connect to Oscilloscope")
        self.setMinimumWidth(420)
        self.selected_method = last_method
        self.ip_address = last_ip
        self.port = last_port
        self.use_socket = False
        self._setup_ui(last_method, last_ip, last_port)

    def _setup_ui(self, last_method, last_ip, last_port):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Title
        title = QLabel("Select Connection Method")
        title.setStyleSheet("font-size: 15px; font-weight: 600;")
        layout.addWidget(title)

        # Connection method group
        method_group = QGroupBox("Connection Type")
        method_layout = QVBoxLayout(method_group)

        self.btn_group = QButtonGroup(self)

        self.radio_usb_gpib = QRadioButton("GPIB / USB (Auto-detect)")
        self.radio_usb_gpib.setToolTip("Scan all VISA resources for GPIB and USB connected instruments")
        self.radio_usb_gpib.setChecked(last_method == 'usb_gpib')
        self.btn_group.addButton(self.radio_usb_gpib, 0)
        method_layout.addWidget(self.radio_usb_gpib)

        self.radio_ip = QRadioButton("Ethernet / IP (Manual)")
        self.radio_ip.setToolTip("Connect to oscilloscope via TCP/IP network")
        self.radio_ip.setChecked(last_method == 'ip')
        self.btn_group.addButton(self.radio_ip, 1)
        method_layout.addWidget(self.radio_ip)

        layout.addWidget(method_group)

        # IP settings group
        self.ip_group = QGroupBox("IP Connection Settings")
        ip_layout = QFormLayout(self.ip_group)

        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("e.g. 192.168.1.100")
        self.ip_edit.setText(last_ip)
        ip_layout.addRow("IP Address:", self.ip_edit)

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(last_port)
        self.port_spin.setToolTip("Default: 4000 (Tektronix socket server)")
        ip_layout.addRow("Port:", self.port_spin)

        self.socket_radio = QRadioButton("Socket (Port 4000)")
        self.socket_radio.setToolTip("Raw socket connection - use for Tektronix socket server")
        self.instrument_radio = QRadioButton("VISA Instrument (Port not needed)")
        self.instrument_radio.setChecked(True)
        self.instrument_radio.setToolTip("Standard VISA INSTR connection - recommended")

        proto_layout = QHBoxLayout()
        proto_layout.addWidget(self.instrument_radio)
        proto_layout.addWidget(self.socket_radio)
        ip_layout.addRow("Protocol:", proto_layout)

        # Initially hidden if USB/GPIB selected
        self.ip_group.setEnabled(last_method == 'ip')
        layout.addWidget(self.ip_group)

        # Connect radio buttons
        self.btn_group.buttonClicked.connect(self._on_method_changed)

        # Info label
        info = QLabel(
            "💡 Tip: On the oscilloscope, go to Utility → I/O → LAN to find the IP address.\n"
            "   Make sure the oscilloscope is connected to the same network."
        )
        info.setStyleSheet("color: #86868B; font-size: 11px; padding: 8px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        connect_btn = QPushButton("Connect")
        connect_btn.setDefault(True)
        connect_btn.clicked.connect(self._on_connect)
        btn_layout.addWidget(connect_btn)

        layout.addLayout(btn_layout)

    def _on_method_changed(self, button):
        """Enable/disable IP settings based on method selection."""
        is_ip = (button == self.radio_ip)
        self.ip_group.setEnabled(is_ip)

    def _on_connect(self):
        """Validate inputs and accept dialog."""
        if self.radio_ip.isChecked():
            ip = self.ip_edit.text().strip()
            if not ip:
                QMessageBox.warning(self, "Input Error", "Please enter an IP address.")
                return

            # Basic IP format validation
            parts = ip.split('.')
            if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts if p.isdigit()):
                QMessageBox.warning(self, "Input Error",
                                    "Please enter a valid IP address (e.g. 192.168.1.100)")
                return

            self.selected_method = 'ip'
            self.ip_address = ip
            self.port = self.port_spin.value()
            self.use_socket = self.socket_radio.isChecked()
        else:
            self.selected_method = 'usb_gpib'

        self.accept()

    def get_connection_params(self):
        """Return connection parameters as dict."""
        return {
            'method': self.selected_method,
            'ip_address': self.ip_address,
            'port': self.port,
            'use_socket': self.use_socket,
        }
