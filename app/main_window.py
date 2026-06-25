"""Main application window orchestrating all components."""
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                                QScrollArea, QStatusBar, QPushButton, QLabel,
                                QMessageBox, QFormLayout, QLineEdit)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QCloseEvent

from .state import AppState
from .theme import apply_theme
from widgets import ConfigPanel, NavBar, ActionBar
from widgets.config_panel import ConfigCard
from core import EasyExcel, instrument_manager, test_manager, measurement, capture
from dialogs.connect_dialog import ConnectDialog


class MainWindow(QMainWindow):
    """Main application window with macOS-style layout."""

    def __init__(self):
        super().__init__()
        self.state = AppState()
        self.current_theme = 'light'

        # Connection state
        self._last_connect_method = 'usb_gpib'
        self._last_ip = ''
        self._last_port = 4000
        self._last_use_socket = False
        self._connection_monitor_timer = QTimer(self)
        self._connection_monitor_timer.timeout.connect(self._check_connection_alive)

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        self.setWindowTitle("Nettrix Power Sequence Test Tool V3.0 (PySide6)")
        self.setMinimumSize(800, 680)
        self.resize(900, 750)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        # Scroll area for content
        content_scroll = QScrollArea()
        content_scroll.setWidgetResizable(True)
        content_scroll.setFrameShape(QScrollArea.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(12)

        # Config panel (contains file paths, project info, signals, labels)
        self.config_panel = ConfigPanel(self.state)
        content_layout.addWidget(self.config_panel, 0)

        # Signal display card
        self.signal_card = ConfigCard("Signal Display")
        signal_layout = QFormLayout()
        signal_layout.setContentsMargins(0, 8, 0, 0)

        self.signal1_edit = QLineEdit()
        self.signal1_edit.setReadOnly(True)
        self.signal2_edit = QLineEdit()
        self.signal2_edit.setReadOnly(True)
        self.signal3_edit = QLineEdit()
        self.signal3_edit.setReadOnly(True)

        signal_layout.addRow("Signal 1:", self.signal1_edit)
        signal_layout.addRow("Signal 2:", self.signal2_edit)
        signal_layout.addRow("Signal 3:", self.signal3_edit)
        self.signal_card.content_layout.addLayout(signal_layout)
        content_layout.addWidget(self.signal_card, 0)

        # Current item badge
        self.item_badge = QLabel("Current: -")
        self.item_badge.setStyleSheet("color: #86868B; font-size: 11px; padding: 4px;")
        content_layout.addWidget(self.item_badge)

        # Navigation bar
        self.nav_bar = NavBar()
        content_layout.addWidget(self.nav_bar, 0)

        # Action bar
        self.action_bar = ActionBar()
        content_layout.addWidget(self.action_bar, 0)

        content_layout.addStretch()
        content_scroll.setWidget(content_widget)
        root_layout.addWidget(content_scroll)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label, 1)

        # Theme toggle button
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setFixedSize(32, 32)
        self.theme_btn.setToolTip("Toggle Dark Mode")
        self.theme_btn.clicked.connect(self._toggle_theme)
        self.status_bar.addPermanentWidget(self.theme_btn)

        # Apply initial theme
        apply_theme(self, self.current_theme)

        print("[MainWindow] UI setup complete")

    def closeEvent(self, event: QCloseEvent):
        """Handle application close event - clean up Excel and resources."""
        try:
            # 关闭Excel对象
            if hasattr(self.state, 'xls') and self.state.xls:
                try:
                    self.state.xls.close()
                    self.state.xls = None
                    print("[MainWindow] Excel closed on application exit")
                except Exception as e:
                    print(f"[MainWindow] Error closing Excel: {e}")

            # 停止连接监控定时器
            if hasattr(self, '_connection_monitor_timer'):
                self._connection_monitor_timer.stop()

            print("[MainWindow] Application cleanup complete")
        except Exception as e:
            print(f"[MainWindow] Error during cleanup: {e}")

        # 接受关闭事件
        super().closeEvent(event)

    def connect_signals(self):
        """Connect all signals between components and business logic."""

        # Navigation buttons -> Handlers
        self.nav_bar.last_clicked.connect(self._on_last)
        self.nav_bar.next_clicked.connect(self._on_next)
        self.nav_bar.jump_clicked.connect(self._on_jump)

        # Action buttons -> Handlers
        self.action_bar.connect_clicked.connect(self._on_connect)
        self.action_bar.reconnect_clicked.connect(self._on_reconnect)
        self.action_bar.save_close_clicked.connect(self._on_save_close)
        self.action_bar.save_pic_clicked.connect(self._on_save_pic)
        self.action_bar.set_label_clicked.connect(self._on_set_label)
        self.action_bar.set_mso_clicked.connect(self._on_set_mso)

        # State status updates
        self.state.status_message_changed.connect(self.status_label.setText)
        self.state.connection_changed.connect(self._on_connection_changed)
        self.state.signal1_changed.connect(self.signal1_edit.setText)
        self.state.signal2_changed.connect(self.signal2_edit.setText)
        self.state.signal3_changed.connect(self.signal3_edit.setText)
        self.state.current_item_changed.connect(self._update_item_badge)
        self.state.sheet_name_changed.connect(self._on_sheet_name_changed)

        print("[MainWindow] All signals connected")

    # =========================================================================
    # Connection management
    # =========================================================================

    @Slot()
    def _on_connect(self):
        """Handle Connect button - open connection dialog."""
        dialog = ConnectDialog(
            self,
            last_method=self._last_connect_method,
            last_ip=self._last_ip,
            last_port=self._last_port
        )

        if dialog.exec() == ConnectDialog.Accepted:
            params = dialog.get_connection_params()
            self._last_connect_method = params['method']
            self._last_ip = params['ip_address']
            self._last_port = params['port']
            self._last_use_socket = params['use_socket']
            self._do_connect(params)

    def _do_connect(self, params):
        """Execute connection with given parameters."""
        self.state.set_status("Connecting to instrument...")

        try:
            if params['method'] == 'ip':
                osc, rm, model_flags, message = instrument_manager.connect_ip(
                    params['ip_address'], params['port'], params['use_socket']
                )
            else:
                osc, rm, model_flags, message = instrument_manager.connect_usb_gpib()

            if osc:
                self.state.osc = osc
                self.state.rm = rm
                self.state.mso5 = model_flags['mso5']
                self.state.dpo7000 = model_flags['dpo7000']
                self.state.dpo5104b = model_flags['dpo5104b']
                self.state.set_connection(True)
                self.state.set_status(message)

                # Update action bar info
                self.action_bar.set_connection_info(
                    params['method'], params.get('ip_address', ''), params.get('port', 4000)
                )

                # Start connection monitor (every 5 seconds)
                self._connection_monitor_timer.start(5000)

                model_str = "MSO5" if model_flags['mso5'] else \
                            "DPO7000" if model_flags['dpo7000'] else \
                            "DPO5104B" if model_flags['dpo5104b'] else "Unknown"
                print(f"[MainWindow] Connected via {params['method']}: {model_str}")
            else:
                self.state.set_connection(False)
                self.state.set_status(message)
                QMessageBox.warning(self, "Connection Failed", message)

        except Exception as e:
            self.state.set_connection(False)
            self.state.set_status(f"Connection failed: {str(e)}")
            QMessageBox.critical(self, "Connection Error", f"Failed to connect:\n{str(e)}")
            print(f"[MainWindow] Error in _do_connect: {e}")

    @Slot()
    def _on_reconnect(self):
        """Handle Reconnect button - reconnect using last method."""
        self.action_bar.set_reconnecting(True)
        self.state.set_status("Reconnecting...")

        try:
            osc, rm, model_flags, message = instrument_manager.reconnect(
                last_method=self._last_connect_method,
                ip_address=self._last_ip,
                port=self._last_port,
                use_socket=self._last_use_socket
            )

            if osc:
                self.state.osc = osc
                self.state.rm = rm
                self.state.mso5 = model_flags['mso5']
                self.state.dpo7000 = model_flags['dpo7000']
                self.state.dpo5104b = model_flags['dpo5104b']
                self.state.set_connection(True)
                self.state.set_status(f"Reconnected successfully ({self._last_connect_method})")

                # Restart connection monitor
                self._connection_monitor_timer.start(5000)
                print(f"[MainWindow] Reconnected via {self._last_connect_method}")
            else:
                self.state.set_connection(False)
                self.state.set_status(message)
                QMessageBox.warning(self, "Reconnect Failed", message)

        except Exception as e:
            self.state.set_connection(False)
            self.state.set_status(f"Reconnect failed: {str(e)}")
            QMessageBox.critical(self, "Reconnect Error", f"Failed to reconnect:\n{str(e)}")
            print(f"[MainWindow] Error in _on_reconnect: {e}")

        finally:
            self.action_bar.set_reconnecting(False)

    def _check_connection_alive(self):
        """Periodically check if the instrument connection is still alive."""
        if not self.state.flag_mso_connect or self.state.osc is None:
            return

        alive = instrument_manager.check_connection(self.state.osc)

        if not alive and self.state.flag_mso_connect:
            print("[MainWindow] Connection lost detected!")
            self.state.set_connection(False)
            self._connection_monitor_timer.stop()
            self.state.set_status("⚠️ Connection lost! Click Reconnect to restore.")
            QMessageBox.warning(
                self, "Connection Lost",
                "Connection to the oscilloscope has been lost.\n"
                "Click '🔄 Reconnect' to restore the connection."
            )

    @Slot(bool)
    def _on_connection_changed(self, connected):
        """Handle connection state change."""
        self.action_bar.set_connection_status(connected)
        if not connected:
            self._connection_monitor_timer.stop()

    # =========================================================================
    # Test item selection
    # =========================================================================

    def _get_flag_from_sheet_name(self, sheet_name):
        """Map sheet name to flag_test_items value based on naming patterns."""
        if not sheet_name:
            return 0

        # Map sheet names to flag_test_items values based on naming patterns
        sheet_to_flag = {
            "CPU Power Sequence(G3 to S0)": 1,
            "CPU Power Sequence(S0-S5-S0)": 2,
            "CPU Power Sequence(S0 GLO RST)": 3,
            "CPU Power Sequence(WARM RESET)": 4,
            "CPU Power Sequence(S5 GLO RST)": 5,
            "CPU Power Sequence(THERMTRIP)": 6,
            "CPU LVT": 7,
            "CPU HW Strap": 8,
            "CPU PG&EN": 9,
            "CPU Monotony": 10,
            "CPU Power Sequence(S5 to G3)": 12,
        }

        # Fallback: try to extract flag from sheet name if pattern matches
        for flag, pattern in sheet_to_flag.items():
            if pattern in sheet_name:
                return flag

        # Default: return 0 if no match
        return 0

    def _load_test_data(self):
        """Load test data when test item is selected."""
        file_path = self.state.file_path
        if not file_path:
            self.state.set_status("Please select Excel file first")
            return

        try:
            # 使用state中的Excel对象
            state_dict = {
                'sheet_name': self.state.sheet_name or "Sheet1",
                'flag_test_items': self.state.flag_test_items,
                'flag_monotony_direction': self.state.flag_monotony_direction,
                'xls': self.state.xls,  # 传入已有的Excel对象
            }

            test_manager.go(file_path, state_dict)

            self.state.m = state_dict.get('m', 8)
            self.state.signal1_name = state_dict.get('signal1_name', '')
            self.state.signal2_name = state_dict.get('signal2_name', '')
            self.state.signal3_name = state_dict.get('signal3_name', '')

            self.state.signal1 = self.state.signal1_name
            self.state.signal2 = self.state.signal2_name
            self.state.signal3 = self.state.signal3_name

            self.state.set_status(f"Loaded test item {self.state.flag_test_items}")
            print(f"[MainWindow] Test data loaded: item={self.state.flag_test_items}, "
                  f"signal1={self.state.signal1_name}, signal2={self.state.signal2_name}")
            print("[MainWindow] Using existing Excel instance - no new window opened")

        except Exception as e:
            self.state.set_status(f"Error loading test: {str(e)}")
            print(f"[MainWindow] Error in _load_test_data: {e}")

    # =========================================================================
    # Navigation
    # =========================================================================

    def _on_last(self):
        if not self._check_ready():
            return
        try:
            state_dict = self._get_state_dict()
            test_manager.Last(state_dict)
            self._update_state_from_dict(state_dict)
        except Exception as e:
            self._handle_connection_error(e, "Last")

    def _on_next(self):
        if not self._check_ready():
            return
        try:
            state_dict = self._get_state_dict()
            test_manager.Next(state_dict)
            self._update_state_from_dict(state_dict)
        except Exception as e:
            self._handle_connection_error(e, "Next")

    def _on_jump(self, target):
        if not self._check_ready():
            return
        try:
            state_dict = self._get_state_dict()
            test_manager.jump(state_dict, target)
            self._update_state_from_dict(state_dict)
        except Exception as e:
            self._handle_connection_error(e, "Jump")

    # =========================================================================
    # Instrument operations
    # =========================================================================

    def _on_save_close(self):
        if self.state.xls:
            try:
                # 保存Excel
                self.state.xls.save()

                # 添加确认对话框
                from PySide6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self,
                    "Close Excel",
                    "Do you want to close Excel file now?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    # 关闭Excel
                    self.state.xls.close()
                    self.state.xls = None
                    self.state.set_status("Excel saved and closed")
                    print("[MainWindow] Excel closed by user")
                else:
                    self.state.set_status("Excel saved but kept open")

            except Exception as e:
                self.state.set_status(f"Error saving Excel: {str(e)}")
                # 发生错误时尝试关闭Excel
                try:
                    self.state.xls.close()
                    self.state.xls = None
                except:
                    pass

    def _on_save_pic(self):
        if not self._check_ready() or not self.state.osc:
            self.state.set_status("Please connect instrument first")
            return
        if not self.state.pic_path:
            self.state.set_status("Please select picture save path")
            return

        try:
            osc = self.state.osc
            xls = self.state.xls
            sheet_name = self.state.sheet_name or "Sheet1"
            signal1 = self.state.ch1_label
            signal2 = self.state.ch2_label
            signal3 = self.state.ch3_label

            delay_time, _, _, _, _ = capture.Capture_Pic(
                osc, xls, sheet_name, signal1, signal2, signal3,
                self.state.flag_test_items, self.state.flag_monotony_direction,
                self.state.m, self.state.mso5, self.state.pic_path, self.state.project_name
            )

            self.state.set_status(f"Picture saved, delay={delay_time}")
            print(f"[MainWindow] Picture captured, delay={delay_time}")

        except Exception as e:
            self._handle_connection_error(e, "Save Picture")

    def _on_set_label(self):
        if not self.state.osc:
            self.state.set_status("Please connect instrument first")
            return
        try:
            measurement.channel_Lable_set(
                self.state.osc,
                self.state.ch1_label,
                self.state.ch2_label,
                self.state.ch3_label
            )
            self.state.set_status("Labels set on instrument")
        except Exception as e:
            self._handle_connection_error(e, "Set Label")

    def _on_set_mso(self):
        if not self.state.osc:
            self.state.set_status("Please connect instrument first")
            return

        try:
            osc = self.state.osc
            flag = self.state.flag_test_items

            osc.write('FACTORY')
            osc.write('DISplay:WAVEView1:VIEWStyle OVErlay')

            if flag == 9:
                osc.channel_state('ON', 'ON', 'ON', 'OFF')
                osc.chanset('CH1', -2.5, 0, '1.0000E+09', 1)
                osc.chanset('CH2', -3.5, 0, '1.0000E+09', 1)
                osc.chanset('CH3', -4.5, 0, '1.0000E+09', 1)
            elif flag == 10:
                osc.channel_state('ON', 'OFF', 'OFF', 'OFF')
                osc.chanset('CH1', -2.5, 0, '1.0000E+09', 1)
            else:
                osc.channel_state('ON', 'ON', 'OFF', 'OFF')
                osc.chanset('CH1', -2.5, 0, '1.0000E+09', 1)
                osc.chanset('CH2', -3.5, 0, '1.0000E+09', 1)

            osc.write('HORIZONTAL:MODE AUTO')
            osc.write('HORIZONTAL:MODE:SCALE 1e-2')
            osc.write('HORIZONTAL:POSITION 30')

            if flag == 1 or flag == 0:
                measurement.measure1(osc, self.state.mso5)
            elif flag in (2, 3, 4, 5, 6):
                measurement.measure2(osc, self.state.mso5)
            elif flag == 7:
                measurement.measure3(osc, self.state.mso5)
            elif flag == 8:
                measurement.measure4(osc, self.state.mso5)
            elif flag == 9:
                measurement.measure5(osc, self.state.mso5)
            elif flag == 10:
                measurement.measure6(osc, self.state.mso5)

            osc.state('run')
            self.state.set_status("MSO configured")
            print(f"[MainWindow] MSO configured for test item {flag}")

        except Exception as e:
            self._handle_connection_error(e, "Set MSO")

    # =========================================================================
    # Theme
    # =========================================================================

    def _toggle_theme(self):
        self.current_theme = 'dark' if self.current_theme == 'light' else 'light'
        apply_theme(self, self.current_theme)
        self.theme_btn.setText("☀️" if self.current_theme == 'dark' else "🌙")
        self.state.set_status(f"Switched to {self.current_theme} theme")

    # =========================================================================
    # Helpers
    # =========================================================================

    def _check_ready(self):
        if not self.state.xls:
            self.state.set_status("Please load test first")
            return False
        return True

    def _get_state_dict(self):
        return {
            'sheet_name': self.state.sheet_name or "Sheet1",
            'flag_test_items': self.state.flag_test_items,
            'flag_monotony_direction': self.state.flag_monotony_direction,
            'flag_mso_connect': self.state.flag_mso_connect,
            'mso5': self.state.mso5,
            'osc': self.state.osc,
            'xls': self.state.xls,
            'm': self.state.m,
        }

    def _update_item_badge(self, current_item):
        """Update current item badge."""
        self.item_badge.setText(f"Current: {current_item}")
        print(f"[MainWindow] Updated item badge: {current_item}")

    @Slot(str)
    @Slot(str)
    def _on_sheet_name_changed(self, sheet_name):
        """Handle sheet name change from combo box - activate Excel and load test data."""
        print(f"[MainWindow] _on_sheet_name_changed called: {sheet_name}")

        if not sheet_name:
            print("[MainWindow] Empty sheet name, skipping")
            return

        if not self.state.xls:
            print("[MainWindow] No Excel instance, skipping")
            return

        # Activate the sheet in Excel
        try:
            self.state.xls.activate_sheet(sheet_name)
            print(f"[MainWindow] Excel sheet activated: {sheet_name}")
        except Exception as e:
            print(f"[MainWindow] Error activating Excel sheet: {e}")
            self.state.set_status(f"Error: {str(e)}")
            return

        # Set test item flag and load data
        self.state.flag_test_items = self._get_flag_from_sheet_name(sheet_name)
        self._load_test_data()
        self.state.set_status(f"Sheet: {sheet_name}")

    def _update_state_from_dict(self, state_dict):
        self.state.m = state_dict.get('m', self.state.m)
        self.state.flag_monotony_direction = state_dict.get('flag_monotony_direction', self.state.flag_monotony_direction)
        self.state.signal1_name = state_dict.get('signal1_name', '')
        self.state.signal2_name = state_dict.get('signal2_name', '')
        self.state.signal3_name = state_dict.get('signal3_name', '')

        self.state.signal1 = self.state.signal1_name
        self.state.signal2 = self.state.signal2_name
        self.state.signal3 = self.state.signal3_name
        self.state.pn_direction = state_dict.get('pn_direction', self.state.pn_direction)
        self.state.current_item = state_dict.get('current_item', self.state.current_item)

    def _handle_connection_error(self, error, operation):
        """Handle errors that may indicate a lost connection.

        If the error appears to be a VISA/connection error, mark connection as lost
        and offer to reconnect. Otherwise just show the error.
        """
        error_str = str(error)
        is_connection_error = any(kw in error_str.upper() for kw in [
            'VISA', 'CONNECTION', 'TIMEOUT', 'SOCKET', 'NETWORK', 'IO', 'BROKEN PIPE'
        ])

        if is_connection_error:
            print(f"[MainWindow] Connection error during {operation}: {error}")
            self.state.set_connection(False)
            self._connection_monitor_timer.stop()
            self.state.set_status(f"⚠️ Connection lost during {operation}. Click Reconnect.")
            QMessageBox.warning(
                self, "Connection Lost",
                f"Connection lost during {operation}.\n\n"
                f"Error: {error_str}\n\n"
                f"Click '🔄 Reconnect' to restore the connection."
            )
        else:
            self.state.set_status(f"Error in {operation}: {error_str}")
            print(f"[MainWindow] Error in {operation}: {error}")
