"""Main application window orchestrating all components."""
import os, json
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QSizePolicy,
                                QScrollArea, QStatusBar, QPushButton, QLabel,
                                QMessageBox, QApplication)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QCloseEvent, QAction

from .state import AppState
from .theme import apply_theme
from widgets import ConfigPanel

from core import EasyExcel, instrument_manager, test_manager, measurement, capture
from core.logger import log
from dialogs.connect_dialog import ConnectDialog
from dialogs.help_dialog import HelpDialog

# Wire capture._pulse to the Qt event loop so the GUI stays responsive
# during long VISA / Excel operations.
import core.capture as capture_mod
capture_mod._pulse = lambda: QApplication.processEvents()


class MainWindow(QMainWindow):
    """Main application window with macOS-style layout."""

    def __init__(self):
        super().__init__()
        self.state = AppState()
        self.current_theme = 'light'

        # Connection state (restore from last session — connection info only)
        self._settings_file = os.path.join(os.path.dirname(__file__), '..', 'app_settings.json')
        saved = self._load_settings()
        self._last_connect_method = saved.get('method', 'usb_gpib')
        self._last_ip = saved.get('ip', '')
        self._last_port = saved.get('port', 4000)
        self._last_use_socket = saved.get('use_socket', False)
        self._connection_monitor_timer = QTimer(self)
        self._connection_monitor_timer.timeout.connect(self._check_connection_alive)
        self._fail_count = 0

        self.setup_ui()
        self.connect_signals()

        # Restore file paths (display only, no auto-load)
        if saved.get('file_path'):
            self.state._file_path = saved['file_path']
            self.config_panel.excel_edit.setText(saved['file_path'])

        # Auto-load config.json to restore last session state
        self._config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        self._auto_load_config()

        # Initialize connection info on config panel (for export)
        self.config_panel._connect_method = self._last_connect_method
        self.config_panel._connect_ip = self._last_ip
        self.config_panel._connect_port = self._last_port
        self.config_panel._connect_use_socket = self._last_use_socket
        if saved.get('pic_path'):
            self.state.pic_path = saved['pic_path']

        # Restore scope save path (project_name)
        if saved.get('project_name'):
            self.state.project_name = saved['project_name']

        # Show saved IP in menu bar if any
        if self._last_ip:
            self.conn_info_label.setText(f"IP: {self._last_ip}:{self._last_port}")
        elif self._last_connect_method != 'ip':
            self.conn_info_label.setText("GPIB/IP")

    def setup_ui(self):
        self.setWindowTitle("硬件工程师自动化测试工具 V2.1 - liujch2")
        self.setMinimumSize(700, 400)
        self.resize(740, 460)

        # ── Menu Bar ──
        menu_bar = self.menuBar()

        # IP connection info (toolbar right side)
        self.conn_info_label = QLabel("")
        self.conn_info_label.setStyleSheet("color: #86868B; font-size: 12px; padding: 0 4px;")

        # Connection status dot (colored circle)
        self.conn_dot = QWidget()
        self.conn_dot.setFixedSize(8, 8)
        self.conn_dot.setStyleSheet("background: #C8C8CD; border-radius: 4px;")

        # -- File menu --
        file_menu = menu_bar.addMenu("File")
        file_menu.setToolTipsVisible(True)
        save_action = QAction("Save Excel", self)
        save_action.setToolTip("Save the opened Excel workbook")
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)
        reload_action = QAction("Reload Excel", self)
        reload_action.setToolTip("Reopen Excel file and restore current sheet")
        reload_action.triggered.connect(self._reload_excel)
        file_menu.addAction(reload_action)
        file_menu.addSeparator()
        export_action = QAction("Export Config", self)
        export_action.setToolTip("Export all settings to a JSON config file")
        export_action.triggered.connect(lambda: (print("[Menu] Export Config"), self.config_panel.export_config()))
        file_menu.addAction(export_action)
        import_action = QAction("Import Config", self)
        import_action.setToolTip("Import settings from a JSON config file")
        import_action.triggered.connect(lambda: (print("[Menu] Import Config"), self.config_panel.import_config()))
        file_menu.addAction(import_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.setToolTip("Close the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # -- Toolbar (icons next to menu) --
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setIconSize(toolbar.iconSize() * 0.7)

        save_tb = QAction("📋", self)
        save_tb.setToolTip("Save Excel")
        save_tb.triggered.connect(self._on_save)
        toolbar.addAction(save_tb)

        self.connect_tb = QAction("🔗", self)
        self.connect_tb.setToolTip("Connect")
        self.connect_tb.triggered.connect(self._on_connect)
        toolbar.addAction(self.connect_tb)

        self.reconnect_tb = QAction("🔄", self)
        self.reconnect_tb.setToolTip("Reconnect")
        self.reconnect_tb.triggered.connect(self._on_reconnect)
        toolbar.addAction(self.reconnect_tb)

        toolbar.addSeparator()

        self.reload_tb = QAction("📂 Reload Excel", self)
        self.reload_tb.setToolTip("Reopen Excel file and restore current sheet")
        self.reload_tb.triggered.connect(self._reload_excel)
        toolbar.addAction(self.reload_tb)

        # Spacer to push IP label to right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        toolbar.addWidget(self.conn_dot)
        toolbar.addWidget(self.conn_info_label)

        # -- Settings menu --
        settings_menu = menu_bar.addMenu("Settings")
        settings_menu.setToolTipsVisible(True)
        init_row_action = QAction("Set Init Row...", self)
        init_row_action.setToolTip("Set the starting row number for test items")
        init_row_action.triggered.connect(self._set_init_row)
        settings_menu.addAction(init_row_action)
        sig_col_action = QAction("Set Signal Cols...", self)
        sig_col_action.setToolTip("Set Excel column for each signal")
        sig_col_action.triggered.connect(self._set_signal_cols)
        settings_menu.addAction(sig_col_action)
        data_col_action = QAction("Set Data Columns...", self)
        data_col_action.setToolTip("Set Excel columns for measurement data (Sequence + Monotony)")
        data_col_action.triggered.connect(self._set_data_cols)
        settings_menu.addAction(data_col_action)
        pic_col_action = QAction("Set Picture Columns...", self)
        pic_col_action.setToolTip("Set Excel columns for screenshot insertion (Sequence + Monotony P/N)")
        pic_col_action.triggered.connect(self._set_pic_cols)
        settings_menu.addAction(pic_col_action)
        settings_menu.addSeparator()
        hor_action = QAction("MSO Horizontal...", self)
        hor_action.setToolTip("Configure oscilloscope horizontal: mode, scale, position")
        hor_action.triggered.connect(self._set_mso_horizontal)
        settings_menu.addAction(hor_action)
        ch_action = QAction("MSO Channel Setup...", self)
        ch_action.setToolTip("Configure per-channel vertical position and scale")
        ch_action.triggered.connect(self._set_mso_channels)
        settings_menu.addAction(ch_action)
        label_action = QAction("Set Label Position...", self)
        label_action.setToolTip("Configure channel label X/Y position on oscilloscope display")
        label_action.triggered.connect(self._set_label_position)
        settings_menu.addAction(label_action)
        settings_menu.addSeparator()
        light_action = QAction("Light Theme", self)
        light_action.setToolTip("Switch to light color theme")
        light_action.setCheckable(True)
        light_action.setChecked(True)
        light_action.triggered.connect(lambda: self._set_theme('light'))
        settings_menu.addAction(light_action)
        dark_action = QAction("Dark Theme", self)
        dark_action.setToolTip("Switch to dark color theme")
        dark_action.setCheckable(True)
        dark_action.triggered.connect(lambda: self._set_theme('dark'))
        settings_menu.addAction(dark_action)

        # Store refs for syncing checkmarks
        self._light_action = light_action
        self._dark_action = dark_action

        # -- Help menu --
        help_menu = menu_bar.addMenu("Help")
        help_menu.setToolTipsVisible(True)
        manual_action = QAction("User Manual", self)
        manual_action.setToolTip("Open the user operation manual with chapter navigation")
        manual_action.triggered.connect(self._show_help)
        help_menu.addAction(manual_action)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(8, 2, 8, 8)
        root_layout.setSpacing(0)

        # Scroll area for content
        content_scroll = QScrollArea()
        content_scroll.setWidgetResizable(True)
        content_scroll.setFrameShape(QScrollArea.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Config panel (contains two-column cards + NavBar + ActionBar)
        self.config_panel = ConfigPanel(self.state)
        content_layout.addWidget(self.config_panel)
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

        log.debug('MainWindow', 'UI setup complete')

    def closeEvent(self, event: QCloseEvent):
        """Handle application close — save connection info, keep Excel open."""
        if hasattr(self, '_connection_monitor_timer'):
            self._connection_monitor_timer.stop()
        self._save_settings()
        log.info('MainWindow', 'Application closed')
        super().closeEvent(event)

    def _load_settings(self):
        try:
            with open(self._settings_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_settings(self):
        """Save connection info + file paths. Other settings reset to defaults on restart."""
        cfg = {
            'method': self._last_connect_method,
            'ip': self._last_ip,
            'port': self._last_port,
            'use_socket': self._last_use_socket,
            'file_path': self.state.file_path,
            'pic_path': self.state.pic_path,
            'project_name': self.state.project_name,
        }
        try:
            with open(self._settings_file, 'w') as f:
                json.dump(cfg, f, indent=2)
        except Exception as e:
            log.warning('MainWindow', f'Failed to save settings: {e}')
        # Auto-export config to restore full state on next launch
        try:
            self.config_panel._silent_export(self._config_path)
        except Exception:
            pass

    def _auto_load_config(self):
        """Silently import config.json if it exists, to restore last session."""
        if hasattr(self, '_config_path') and self.config_panel._silent_import(self._config_path):
            # Restore connection info from loaded config
            cp = self.config_panel
            if hasattr(cp, '_connect_method'):
                self._last_connect_method = cp._connect_method
            if hasattr(cp, '_connect_ip'):
                self._last_ip = cp._connect_ip
            if hasattr(cp, '_connect_port'):
                self._last_port = cp._connect_port
            if hasattr(cp, '_connect_use_socket'):
                self._last_use_socket = cp._connect_use_socket
            # Update display
            if self._last_ip:
                self.conn_info_label.setText(f"IP: {self._last_ip}:{self._last_port}")

    def connect_signals(self):
        """Connect all signals between components and business logic."""

        # Navigation buttons -> Handlers
        self.config_panel.nav_bar.last_clicked.connect(self._on_last)
        self.config_panel.nav_bar.next_clicked.connect(self._on_next)
        self.config_panel.nav_bar.jump_clicked.connect(self._on_jump)

        # Action buttons -> Handlers

        self.config_panel.save_pic_clicked.connect(self._on_save_pic)
        self.config_panel.save_data_clicked.connect(self._on_save_data)
        self.config_panel.save_pic_and_data_clicked.connect(self._on_save_pic_and_data)
        self.config_panel.set_label_clicked.connect(self._on_set_label)
        self.config_panel.set_mso_clicked.connect(self._on_set_mso)

        # State status updates
        self.state.status_message_changed.connect(self.status_label.setText)
        self.state.connection_changed.connect(self._on_connection_changed)
        self.state.signal1_changed.connect(self.config_panel.signal1_edit.setText)
        self.state.signal2_changed.connect(self.config_panel.signal2_edit.setText)
        self.state.signal3_changed.connect(self.config_panel.signal3_edit.setText)
        self.state.signal4_changed.connect(self.config_panel.signal4_edit.setText)
        self.state.current_item_changed.connect(self._update_item_badge)
        self.state.sheet_name_changed.connect(self._on_sheet_name_changed)

        log.debug('MainWindow', 'All signals connected')

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

                # Set IP text BEFORE connection signal (so green dot prepends correctly)
                if params['method'] == 'ip':
                    self.conn_info_label.setText(f"IP: {params['ip_address']}:{params['port']}")
                else:
                    self.conn_info_label.setText("GPIB/USB")
                self.conn_info_label.repaint()

                self.state.set_connection(True)
                self.state.set_status(message)

                # Store connection info on config panel for export
                self.config_panel._connect_method = params['method']
                self.config_panel._connect_ip = params['ip_address']
                self.config_panel._connect_port = params['port']
                self.config_panel._connect_use_socket = params['use_socket']

                # Start connection monitor (every 5 seconds)
                self._connection_monitor_timer.start(5000)

                model_str = "MSO5" if model_flags['mso5'] else \
                            "DPO7000" if model_flags['dpo7000'] else \
                            "DPO5104B" if model_flags['dpo5104b'] else "Unknown"
                self.state.set_status(f"Connected: {model_str} ({params['method']})")
                log.success('MainWindow', f'Connected: {model_str} via {params["method"]}')
            else:
                self.state.set_connection(False)
                self.state.set_status(message)
                QMessageBox.warning(self, "Connection Failed", message)

        except Exception as e:
            self.state.set_connection(False)
            self.state.set_status(f"Connection failed: {str(e)}")
            QMessageBox.critical(self, "Connection Error", f"Failed to connect:\n{str(e)}")
            log.error('MainWindow', f'Error in _do_connect: {e}')

    @Slot()
    def _on_reconnect(self):
        """Handle Reconnect — reconnect using last method."""
        self.reconnect_tb.setToolTip("Reconnecting...")
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

                model_str = "MSO5" if model_flags['mso5'] else \
                            "DPO7000" if model_flags['dpo7000'] else \
                            "DPO5104B" if model_flags['dpo5104b'] else "Unknown"

                # Update menu bar with green dot + model
                if self._last_connect_method == 'ip':
                    self.conn_info_label.setText(f"IP: {self._last_ip}:{self._last_port}")
                else:
                    self.conn_info_label.setText("GPIB/USB")
                self.conn_info_label.repaint()

                self.state.set_connection(True)
                self.state.set_status(f"Reconnected: {model_str} ({self._last_connect_method})")
                log.success('MainWindow', f'Reconnected: {model_str} via {self._last_connect_method}')

                # Restart connection monitor
                self._connection_monitor_timer.start(5000)
            else:
                self.state.set_connection(False)
                self.state.set_status(message)
                QMessageBox.warning(self, "Reconnect Failed", message)

        except Exception as e:
            self.state.set_connection(False)
            self.state.set_status(f"Reconnect failed: {str(e)}")
            QMessageBox.critical(self, "Reconnect Error", f"Failed to reconnect:\n{str(e)}")
            log.error('MainWindow', f'Error in _on_reconnect: {e}')

        finally:
            self.reconnect_tb.setToolTip("Reconnect")

    def _check_connection_alive(self):
        """Periodically check if the instrument connection is still alive.
        Requires 2 consecutive failures before declaring connection lost."""
        if not self.state.flag_mso_connect or self.state.osc is None:
            self._fail_count = 0
            return

        alive = instrument_manager.check_connection(self.state.osc)

        if not alive:
            self._fail_count = getattr(self, '_fail_count', 0) + 1
            if self._fail_count >= 2:
                log.error('MainWindow', 'Connection lost detected (2 consecutive failures)!')
                self.state.set_connection(False)
                self._connection_monitor_timer.stop()
                self.state.set_status("⚠️ Connection lost! Click Reconnect to restore.")
                QMessageBox.warning(
                    self, "Connection Lost",
                    "Connection to the oscilloscope has been lost.\n"
                    "Click '🔄 Reconnect' to restore the connection."
                )
            else:
                log.warning('MainWindow', f'Connection check timeout ({self._fail_count}/2)')
        else:
            self._fail_count = 0

    @Slot(bool)
    def _on_connection_changed(self, connected):
        """Green dot when connected, light gray when disconnected."""
        if connected:
            self.conn_dot.setStyleSheet("background: #34C759; border-radius: 4px;")
        else:
            self.conn_dot.setStyleSheet("background: #C8C8CD; border-radius: 4px;")
            self._connection_monitor_timer.stop()

    # =========================================================================
    # Test item selection
    # =========================================================================

    
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
                'test_type': self.state.test_type,
                'flag_monotony_direction': self.state.flag_monotony_direction,
                'xls': self.state.xls,
                'row': self.config_panel.init_row,
                'init_row': self.config_panel.init_row,
            }

            test_manager.go(file_path, state_dict)

            self.state.row = state_dict.get('row', self.config_panel.init_row)
            self.state.signal1_name = state_dict.get('signal1_name', '')
            self.state.signal2_name = state_dict.get('signal2_name', '')
            self.state.signal3_name = state_dict.get('signal3_name', '')
            self.state.signal4_name = state_dict.get('signal4_name', '')

            self.state.signal1 = self.state.signal1_name
            self.state.signal2 = self.state.signal2_name
            self.state.signal3 = self.state.signal3_name
            self.state.signal4 = self.state.signal4_name

            self.state.set_status(f"Loaded test item {self.state.test_type}")
            log.info('MainWindow', f"Test data loaded: item={self.state.test_type}, "
                     f"signal1={self.state.signal1_name}, signal2={self.state.signal2_name}, "
                     f"signal3={self.state.signal3_name}")
            log.debug('MainWindow', 'Using existing Excel instance - no new window opened')

        except Exception as e:
            self.state.set_status(f"Error loading test: {str(e)}")
            log.error('MainWindow', f'Error in _load_test_data: {e}')

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
            self._log_signals()
        except Exception as e:
            self._show_save_error("Last",
                f"Failed to go to previous test item.\n\nError: {e}\n\n"
                f"Check: sheet={self.state.sheet_name}, row={self.state.row}")

    def _on_next(self):
        if not self._check_ready():
            return
        try:
            state_dict = self._get_state_dict()
            test_manager.Next(state_dict)
            self._update_state_from_dict(state_dict)
            self._log_signals()
        except Exception as e:
            self._show_save_error("Next",
                f"Failed to go to next test item.\n\nError: {e}\n\n"
                f"Check: sheet={self.state.sheet_name}, row={self.state.row}")

    def _on_jump(self, target):
        if not self._check_ready():
            return
        try:
            state_dict = self._get_state_dict()
            test_manager.jump(state_dict, target)
            self._update_state_from_dict(state_dict)
            self._log_signals()
        except Exception as e:
            self._show_save_error("Jump",
                f"Failed to jump to item {target}.\n\nError: {e}\n\n"
                f"Check: sheet={self.state.sheet_name}, row={self.state.row}")

    def _log_signals(self):
        """Print current signal coordinates and values to log (enabled only)."""
        cp = self.config_panel
        lines = ["── Signal State ──"]
        for i in range(4):
            if not cp.signal_enables[i].isChecked():
                continue
            row = cp.signal_rows[i].value()
            col = cp.signal_cols[i]  # int list, not spinbox
            name = getattr(self.state, f'signal{i + 1}', '') or '-'
            lines.append(f"  Sig{i + 1}: [✓] R:{row} C:{col} = {name}")
        lines.append("─" * 20)
        print("\n".join(lines))

    # =========================================================================
    # Instrument operations
    # =========================================================================

    def _set_signal_cols(self):
        """Open dialog to set all 4 signal columns at once."""
        from PySide6.QtWidgets import (QDialog, QFormLayout, QSpinBox,
                                        QDialogButtonBox, QVBoxLayout, QLabel)
        dlg = QDialog(self)
        dlg.setWindowTitle("Signal Columns")
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel("Set Excel column for each signal:"))
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form.setSpacing(6)
        spins = []
        cp = self.config_panel
        for i in range(4):
            sp = QSpinBox()
            sp.setRange(1, 99)
            sp.setValue(cp.signal_cols[i])
            spins.append(sp)
            form.addRow(f"Signal {i+1}:", self._col_spin_with_letter(sp))
        lay.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        lay.addWidget(btns)

        def _validate_and_accept():
            # Only check enabled signals for duplicates
            enabled_vals = [s.value() for i, s in enumerate(spins)
                            if cp.signal_enables[i].isChecked()]
            seen = set()
            for v in enabled_vals:
                if v in seen:
                    QMessageBox.warning(dlg, "Duplicate Column",
                        f"Column {self._col_to_letter(v)} "
                        f"appears more than once among enabled signals.\n\n"
                        f"Each enabled signal must have a unique column.")
                    return
                seen.add(v)
            dlg.accept()

        btns.accepted.connect(_validate_and_accept)
        btns.rejected.connect(dlg.reject)

        if dlg.exec() == QDialog.Accepted:
            cp.signal_cols = [s.value() for s in spins]
            cp._read_initial_signals()
            log.info('MainWindow', f'Signal cols set to {cp.signal_cols}')

    @staticmethod
    def _col_to_letter(n):
        """1→A, 26→Z, 27→AA, ..."""
        s = ''
        while n > 0:
            n, r = divmod(n - 1, 26)
            s = chr(65 + r) + s
        return s

    def _col_spin_with_letter(self, spin):
        """Return a widget: spinbox + '→ letter' label."""
        from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
        w = QWidget()
        lay = QHBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(4)
        lay.addWidget(spin)
        letter = QLabel('→ ' + self._col_to_letter(spin.value()))
        letter.setFixedWidth(45)
        spin.valueChanged.connect(lambda v, l=letter: l.setText('→ ' + self._col_to_letter(v)))
        lay.addWidget(letter)
        lay.addStretch()
        return w

    def _set_data_cols(self):
        """Open dialog to set measurement data columns with enable/disable."""
        from PySide6.QtWidgets import (QDialog, QFormLayout, QSpinBox,
                                        QDialogButtonBox, QVBoxLayout, QLabel, QGroupBox,
                                        QCheckBox, QHBoxLayout)
        dlg = QDialog(self)
        dlg.setWindowTitle("Data Columns")
        lay = QVBoxLayout(dlg)
        cp = self.config_panel

        def _make_spin(val):
            sp = QSpinBox(); sp.setRange(1, 99); sp.setValue(val); return sp

        def _row_with_enable(label, val, en, parent_form):
            """Add a row: [✓] spin → letter to *parent_form*.  Returns (cb, spin)."""
            cb = QCheckBox()
            cb.setChecked(en)
            sp = _make_spin(val)
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(4)
            row.addWidget(cb)
            row.addWidget(sp)
            row.addStretch()
            letter = QLabel('→ ' + self._col_to_letter(sp.value()))
            letter.setFixedWidth(45)
            sp.valueChanged.connect(lambda v, l=letter: l.setText('→ ' + self._col_to_letter(v)))
            row.addWidget(letter)
            parent_form.addRow(label + ':', row)
            return cb, sp

        # ── Sequence ──
        seq_grp = QGroupBox("Sequence")
        seq_form = QFormLayout()
        seq_form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        seq_form.setSpacing(6)
        seq_cb, seq_spin = _row_with_enable("DELAY", cp.data_col, cp.seq_data_en, seq_form)
        seq_grp.setLayout(seq_form)
        lay.addWidget(seq_grp)

        # ── Monotony P ──
        p_grp = QGroupBox("Monotony P")
        p_form = QFormLayout()
        p_form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        p_form.setSpacing(6)
        p_cbs, p_spins = [], []
        for label, col, en in zip(['TOP', 'BASE', 'MAX', 'MIN'],
                                   cp.mono_p_cols, cp.mono_p_data_en):
            cb, sp = _row_with_enable(label, col, en, p_form)
            p_cbs.append(cb); p_spins.append(sp)
        # Rise Time row (Monotony P)
        rise_cb, rise_spin = _row_with_enable("RISE TIME", cp.rise_col, cp.rise_en, p_form)
        p_grp.setLayout(p_form)
        lay.addWidget(p_grp)

        # ── Monotony N ──
        n_grp = QGroupBox("Monotony N")
        n_form = QFormLayout()
        n_form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        n_form.setSpacing(6)
        n_cbs, n_spins = [], []
        for label, col, en in zip(['TOP', 'BASE', 'MAX', 'MIN'],
                                   cp.mono_n_cols, cp.mono_n_data_en):
            cb, sp = _row_with_enable(label, col, en, n_form)
            n_cbs.append(cb); n_spins.append(sp)
        # Fall Time row (Monotony N)
        fall_cb, fall_spin = _row_with_enable("FALL TIME", cp.fall_col, cp.fall_en, n_form)
        n_grp.setLayout(n_form)
        lay.addWidget(n_grp)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        lay.addWidget(btns)

        def _validate_and_accept():
            # Only check enabled items for duplicates (incl. rise/fall time)
            p_en_vals = [s.value() for s, cb in zip(p_spins, p_cbs) if cb.isChecked()]
            n_en_vals = [s.value() for s, cb in zip(n_spins, n_cbs) if cb.isChecked()]
            extra_vals = []
            if rise_cb.isChecked(): extra_vals.append(rise_spin.value())
            if fall_cb.isChecked(): extra_vals.append(fall_spin.value())
            all_vals = p_en_vals + n_en_vals + extra_vals
            seen = set()
            for v in all_vals:
                if v in seen:
                    QMessageBox.warning(dlg, "Duplicate Column",
                        f"Column {self._col_to_letter(v)} appears more than once.\n\n"
                        f"All enabled Monotony data columns must be unique.")
                    return
                seen.add(v)
            dlg.accept()

        btns.accepted.connect(_validate_and_accept)
        btns.rejected.connect(dlg.reject)

        if dlg.exec() == QDialog.Accepted:
            cp.seq_data_en = seq_cb.isChecked()
            cp.data_col = seq_spin.value()
            cp.mono_p_data_en = [cb.isChecked() for cb in p_cbs]
            cp.mono_p_cols = [s.value() for s in p_spins]
            cp.mono_n_data_en = [cb.isChecked() for cb in n_cbs]
            cp.mono_n_cols = [s.value() for s in n_spins]
            cp.rise_en = rise_cb.isChecked()
            cp.rise_col = rise_spin.value()
            cp.fall_en = fall_cb.isChecked()
            cp.fall_col = fall_spin.value()
            log.info('MainWindow', f"Data cols: seq={self._col_to_letter(cp.data_col)}"
                     f"({'ON' if cp.seq_data_en else 'OFF'}), "
                     f"monoP={[self._col_to_letter(c) for c in cp.mono_p_cols]}"
                     f"({['ON' if e else 'OFF' for e in cp.mono_p_data_en]}), "
                     f"monoN={[self._col_to_letter(c) for c in cp.mono_n_cols]}"
                     f"({['ON' if e else 'OFF' for e in cp.mono_n_data_en]}), "
                     f"rise=col{self._col_to_letter(cp.rise_col)} {'ON' if cp.rise_en else 'OFF'}, "
                     f"fall=col{self._col_to_letter(cp.fall_col)} {'ON' if cp.fall_en else 'OFF'}")

    def _set_pic_cols(self):
        """Open dialog to set picture insertion columns (Sequence + Monotony P/N)."""
        from PySide6.QtWidgets import (QDialog, QFormLayout, QSpinBox,
                                        QDialogButtonBox, QVBoxLayout, QGroupBox)
        dlg = QDialog(self)
        dlg.setWindowTitle("Picture Columns")
        lay = QVBoxLayout(dlg)
        cp = self.config_panel

        def _make_spin(val):
            sp = QSpinBox(); sp.setRange(1, 99); sp.setValue(val); return sp

        def _make_form():
            f = QFormLayout()
            f.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            f.setSpacing(6)
            return f

        # ── Sequence ──
        seq_grp = QGroupBox("Sequence")
        seq_form = _make_form()
        seq_spin = _make_spin(cp.seq_pic_col)
        seq_form.addRow("Picture:", self._col_spin_with_letter(seq_spin))
        seq_grp.setLayout(seq_form)
        lay.addWidget(seq_grp)

        # ── Monotony P ──
        p_grp = QGroupBox("Monotony P")
        p_form = _make_form()
        p_spin = _make_spin(cp.mono_p_pic_col)
        p_form.addRow("Picture:", self._col_spin_with_letter(p_spin))
        p_grp.setLayout(p_form)
        lay.addWidget(p_grp)

        # ── Monotony N ──
        n_grp = QGroupBox("Monotony N")
        n_form = _make_form()
        n_spin = _make_spin(cp.mono_n_pic_col)
        n_form.addRow("Picture:", self._col_spin_with_letter(n_spin))
        n_grp.setLayout(n_form)
        lay.addWidget(n_grp)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)

        if dlg.exec() == QDialog.Accepted:
            cp.seq_pic_col = seq_spin.value()
            cp.mono_p_pic_col = p_spin.value()
            cp.mono_n_pic_col = n_spin.value()
            log.info('MainWindow', f"Picture cols: seq={self._col_to_letter(cp.seq_pic_col)}, "
                     f"monoP={self._col_to_letter(cp.mono_p_pic_col)}, "
                     f"monoN={self._col_to_letter(cp.mono_n_pic_col)}")

    def _set_init_row(self):
        """Open dialog to set initial row number."""
        from PySide6.QtWidgets import QInputDialog
        val, ok = QInputDialog.getInt(
            self, "Set Init Row", "Initial test row number:",
            self.config_panel.init_row, 1, 999999, 1)
        if ok:
            self.config_panel.init_row = val
            self.state.row = val
            # Clamp jump and R: spinboxes to >= init_row
            self.config_panel.nav_bar.clamp_min(val)
            for rspin in self.config_panel.signal_rows:
                rspin.setMinimum(val)
                if rspin.value() < val:
                    rspin.setValue(val)
            # Re-read signals at the new row + sync CH labels
            self.config_panel._read_initial_signals()
            log.info('MainWindow', f'Init row set to {val}')

    def _reload_excel(self):
        """Reopen Excel file and restore current sheet selection."""
        saved_path = self.state.file_path
        if not saved_path:
            self.state.set_status("No Excel file to reload")
            return
        saved_sheet = self.state.sheet_name
        # Re-trigger file_path to reopen Excel and load sheets
        self.state.file_path = ""
        self.state.file_path = saved_path
        # Force sheet selection after reload
        if saved_sheet and self.state.xls:
            self.state.xls.activate_sheet(saved_sheet)
            self.config_panel.sheet_combo.setCurrentText(saved_sheet)
            self.state.sheet_name = saved_sheet
            self.config_panel._read_initial_signals()
        self.state.set_status("Excel reloaded")
        log.info('MainWindow', 'Excel reloaded')

    def _show_save_error(self, operation, error):
        """Show popup dialog when a save operation fails."""
        msg = f"{operation} failed:\n\n{error}"
        self.state.set_status(msg[:80])
        QMessageBox.critical(self, f"{operation} Failed", msg)

    def _warn(self, title, msg):
        """Show warning popup + status bar."""
        self.state.set_status(msg)
        QMessageBox.warning(self, title, msg)

    def _on_save(self):
        """Save Excel workbook."""
        if not self.state.xls:
            self._warn("Save Excel", "No Excel file is open. Please select an Excel file first.")
            return
        try:
            self.state.xls.save()
            self.state.set_status("Excel saved")
            log.success('MainWindow', 'Excel saved')
        except Exception as e:
            self._show_save_error("Save Excel", e)

    def _on_save_pic(self):
        """Save screenshot to local disk. Insert into Excel / save to Scope per checkboxes."""
        if not self.state.pic_path:
            self._warn("Save Picture", "Please select a picture save folder first (File Paths → Pic).")
            return
        if not self.state.osc:
            self._warn("Save Picture", "Please connect to an oscilloscope first.")
            return
        do_excel = self.config_panel.save_to_excel_cb.isChecked()
        if do_excel and not self.state.xls:
            self._warn("Save Picture", "Save to Excel is checked but no Excel file is loaded.\nUse Reload Excel first.")
            return
        try:
            do_scope = self.config_panel.save_to_scope_cb.isChecked()
            do_local = self.config_panel.save_to_local_cb.isChecked()
            use_ch = self.config_panel.ch_label_naming_cb.isChecked()
            ch_labels = [self.state.ch1_label, self.state.ch2_label,
                         self.state.ch3_label, self.state.ch4_label]
            capture.Capture_Pic(
                self.state.osc, self.state.xls,
                self.state.sheet_name or "Sheet1",
                [self.state.signal1, self.state.signal2, self.state.signal3, self.state.signal4],
                [self.config_panel.signal_enables[i].isChecked() for i in range(4)],
                self.state.test_type, self.state.flag_monotony_direction,
                self.state.row, self.state.mso5, self.state.pic_path,
                self.state.project_name,
                save_pic=True, save_data=False,
                save_to_excel=do_excel, save_to_scope=do_scope,
                save_to_local=do_local,
                data_col=self.config_panel.data_col,
                mono_p_cols=self.config_panel.mono_p_cols,
                mono_n_cols=self.config_panel.mono_n_cols,
                pic_cols=(self.config_panel.seq_pic_col,
                          self.config_panel.mono_p_pic_col,
                          self.config_panel.mono_n_pic_col),
                ch_enables=[self.config_panel.ch_enables[i].isChecked() for i in range(4)],
                seq_data_en=self.config_panel.seq_data_en,
                mono_p_data_en=list(self.config_panel.mono_p_data_en),
                mono_n_data_en=list(self.config_panel.mono_n_data_en),
                use_ch_labels=use_ch,
                ch_labels=ch_labels,
                rise_col=self.config_panel.rise_col,
                fall_col=self.config_panel.fall_col,
                rise_en=self.config_panel.rise_en,
                fall_en=self.config_panel.fall_en,
            )
            parts = []
            if do_local:
                parts.append("Local")
            if do_excel:
                parts.append("Excel")
            if do_scope:
                parts.append("Scope")
            if not parts:
                parts.append("Scope only")
            self.state.set_status("Picture saved: " + " + ".join(parts))
            self.config_panel.remember_current_sheet_config()
        except Exception as e:
            self._show_save_error("Save Picture", e)

    def _on_save_data(self):
        """Save measurement data to Excel."""
        if not self.state.xls:
            self._warn("Save Data", "No Excel file is open. Please select an Excel file first.")
            return
        if not self.state.osc:
            self._warn("Save Data", "Please connect to an oscilloscope first.")
            return
        try:
            capture.Capture_Pic(
                self.state.osc, self.state.xls,
                self.state.sheet_name or "Sheet1",
                [self.state.signal1, self.state.signal2, self.state.signal3, self.state.signal4],
                [self.config_panel.signal_enables[i].isChecked() for i in range(4)],
                self.state.test_type, self.state.flag_monotony_direction,
                self.state.row, self.state.mso5, self.state.pic_path,
                self.state.project_name,
                save_pic=False, save_data=True,
                data_col=self.config_panel.data_col,
                mono_p_cols=self.config_panel.mono_p_cols,
                mono_n_cols=self.config_panel.mono_n_cols,
                pic_cols=(self.config_panel.seq_pic_col,
                          self.config_panel.mono_p_pic_col,
                          self.config_panel.mono_n_pic_col),
                ch_enables=[self.config_panel.ch_enables[i].isChecked() for i in range(4)],
                seq_data_en=self.config_panel.seq_data_en,
                mono_p_data_en=list(self.config_panel.mono_p_data_en),
                mono_n_data_en=list(self.config_panel.mono_n_data_en),
                rise_col=self.config_panel.rise_col,
                fall_col=self.config_panel.fall_col,
                rise_en=self.config_panel.rise_en,
                fall_en=self.config_panel.fall_en,
            )
            self.state.set_status("Data saved to Excel")
            self.config_panel.remember_current_sheet_config()
        except Exception as e:
            self._show_save_error("Save Data", e)

    def _on_save_pic_and_data(self):
        """Save both screenshot and data to Excel."""
        if not self.state.osc:
            self._warn("Save Pic+Data", "Please connect to an oscilloscope first.")
            return
        try:
            do_excel = self.config_panel.save_to_excel_cb.isChecked()
            do_local = self.config_panel.save_to_local_cb.isChecked()
            do_scope = self.config_panel.save_to_scope_cb.isChecked()
            capture.Capture_Pic(
                self.state.osc, self.state.xls,
                self.state.sheet_name or "Sheet1",
                [self.state.signal1, self.state.signal2, self.state.signal3, self.state.signal4],
                [self.config_panel.signal_enables[i].isChecked() for i in range(4)],
                self.state.test_type, self.state.flag_monotony_direction,
                self.state.row, self.state.mso5, self.state.pic_path,
                self.state.project_name,
                save_pic=True, save_data=True,
                save_to_excel=do_excel, save_to_scope=do_scope,
                save_to_local=do_local,
                data_col=self.config_panel.data_col,
                mono_p_cols=self.config_panel.mono_p_cols,
                mono_n_cols=self.config_panel.mono_n_cols,
                pic_cols=(self.config_panel.seq_pic_col,
                          self.config_panel.mono_p_pic_col,
                          self.config_panel.mono_n_pic_col),
                ch_enables=[self.config_panel.ch_enables[i].isChecked() for i in range(4)],
                seq_data_en=self.config_panel.seq_data_en,
                mono_p_data_en=list(self.config_panel.mono_p_data_en),
                mono_n_data_en=list(self.config_panel.mono_n_data_en),
                rise_col=self.config_panel.rise_col,
                fall_col=self.config_panel.fall_col,
                rise_en=self.config_panel.rise_en,
                fall_en=self.config_panel.fall_en,
            )
            self.state.set_status("Picture + Data saved")
            self.config_panel.remember_current_sheet_config()
        except Exception as e:
            self._show_save_error("Save Pic+Data", e)

    def _on_set_label(self):
        if not self.state.osc:
            self._warn("Set Label", "Please connect to an oscilloscope first.")
            return
        try:
            # Resolve labels: use signal name if label is empty
            signal_names = [
                self.state.signal1, self.state.signal2,
                self.state.signal3, self.state.signal4
            ]
            ch_labels = [
                self.state.ch1_label, self.state.ch2_label,
                self.state.ch3_label, self.state.ch4_label
            ]
            labels = []
            for i in range(4):
                if self.config_panel.ch_enables[i].isChecked():
                    lbl = ch_labels[i] or signal_names[i] or ''
                    labels.append(lbl)
                else:
                    labels.append(None)  # disabled
            measurement.channel_Lable_set(
                self.state.osc,
                labels[0], labels[1], labels[2], labels[3],
                label_x=self.config_panel.ch_label_x,
                label_y=self.config_panel.ch_label_y,
            )
            self.state.set_status("Labels set on instrument")
        except Exception as e:
            self._handle_connection_error(e, "Set Label")

    @staticmethod
    def _fmt_scale(s):
        """Format time in seconds to a user-friendly unit string."""
        if abs(s) >= 1: return f'{s:.3g}s'
        if abs(s) >= 1e-3: return f'{s*1e3:.3g}ms'
        if abs(s) >= 1e-6: return f'{s*1e6:.3g}μs'
        return f'{s*1e9:.3g}ns'

    @staticmethod
    def _fmt_level(v):
        """Format voltage to a user-friendly unit string."""
        if abs(v) >= 1: return f'{v:.3g}V'
        return f'{v*1e3:.3g}mV'

    def _set_mso_horizontal(self):
        """Settings → MSO Horizontal: dialog to configure scope horizontal parameters."""
        from PySide6.QtWidgets import (QDialog, QFormLayout, QComboBox,
                                        QDialogButtonBox, QVBoxLayout, QDoubleSpinBox, QSpinBox, QHBoxLayout)
        cp = self.config_panel
        dlg = QDialog(self)
        dlg.setWindowTitle("MSO Horizontal Setup")
        lay = QVBoxLayout(dlg)
        form = QFormLayout()

        mode_combo = QComboBox()
        mode_combo.addItems(["AUTO", "MANUAL"])
        mode_combo.setCurrentText(cp.hor_mode)
        form.addRow("Mode:", mode_combo)

        # Scale: value + unit combo, auto-converted
        _SCALE_UNITS = [("ns", 1e-9), ("μs", 1e-6), ("ms", 1e-3), ("s", 1.0)]
        scale_row = QHBoxLayout()
        scale_spin = QDoubleSpinBox()
        scale_spin.setDecimals(0)
        scale_spin.setRange(1, 99999)
        unit_combo = QComboBox()
        for label, _ in _SCALE_UNITS:
            unit_combo.addItem(label)

        # Convert saved seconds → display unit
        raw = cp.hor_scale  # always in seconds
        best_idx = 3  # default: seconds
        best_val = raw
        for i, (_, mult) in enumerate(_SCALE_UNITS):
            v = raw / mult
            if 1.0 <= v < 1000.0:
                best_idx = i; best_val = v; break
            elif v < 1.0 and mult <= raw * 1000:
                best_idx = i; best_val = v
        scale_spin.setValue(best_val)
        unit_combo.setCurrentIndex(best_idx)

        scale_row.addWidget(scale_spin)
        scale_row.addWidget(unit_combo)
        form.addRow("Scale:", scale_row)

        pos_spin = QSpinBox()
        pos_spin.setRange(0, 100)
        pos_spin.setValue(cp.hor_pos)
        pos_spin.setSuffix(" %")
        form.addRow("Position:", pos_spin)

        # ── Trigger ──
        trig_ch_combo = QComboBox()
        trig_ch_combo.addItems(["CH1", "CH2", "CH3", "CH4"])
        trig_ch_combo.setCurrentText(cp.trig_channel)
        form.addRow("Trig Channel:", trig_ch_combo)

        trig_edge_combo = QComboBox()
        trig_edge_combo.addItems(["RISE", "FALL", "BOTH"])
        trig_edge_combo.setCurrentText(cp.trig_edge)
        form.addRow("Trig Edge:", trig_edge_combo)

        _TRIG_LEVEL_UNITS = [("mV", 1e-3), ("V", 1.0)]
        trig_level_row = QHBoxLayout()
        trig_spin = QDoubleSpinBox()
        trig_spin.setDecimals(0)
        trig_spin.setRange(1, 99999)
        trig_unit_combo = QComboBox()
        for label, _ in _TRIG_LEVEL_UNITS:
            trig_unit_combo.addItem(label)
        raw_level = cp.trig_level
        if raw_level < 1.0:
            trig_spin.setValue(raw_level * 1000)
            trig_unit_combo.setCurrentIndex(0)  # mV
        else:
            trig_spin.setValue(raw_level)
            trig_unit_combo.setCurrentIndex(1)  # V
        trig_level_row.addWidget(trig_spin)
        trig_level_row.addWidget(trig_unit_combo)
        form.addRow("Trig Level:", trig_level_row)

        lay.addLayout(form)
        btns = QDialogButtonBox(
            QDialogButtonBox.Apply | QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)

        def _apply():
            cp.hor_mode = mode_combo.currentText()
            unit_mult = _SCALE_UNITS[unit_combo.currentIndex()][1]
            cp.hor_scale = scale_spin.value() * unit_mult
            cp.hor_pos = pos_spin.value()
            cp.trig_channel = trig_ch_combo.currentText()
            cp.trig_edge = trig_edge_combo.currentText()
            trig_unit = _TRIG_LEVEL_UNITS[trig_unit_combo.currentIndex()][1]
            cp.trig_level = trig_spin.value() * trig_unit
            if self.state.osc:
                osc = self.state.osc
                osc.hormode(cp.hor_mode)
                osc.write(f'HORIZONTAL:MODE:SCALE {cp.hor_scale:g}')
                osc.horpos(cp.hor_pos)
                osc.trigger('NORMAL', cp.trig_channel, cp.trig_edge, cp.trig_level)
                self.state.set_status(f"Horizontal: {cp.hor_mode} {self._fmt_scale(cp.hor_scale)}/div {cp.hor_pos}%"
                    f" Trig:{cp.trig_channel} {cp.trig_edge} {self._fmt_level(cp.trig_level)}")
            log.info('MainWindow', f"MSO HOR: mode={cp.hor_mode}, scale={self._fmt_scale(cp.hor_scale)}, pos={cp.hor_pos}"
                f" trig={cp.trig_channel}/{cp.trig_edge}/{self._fmt_level(cp.trig_level)}")

        btns.button(QDialogButtonBox.Apply).clicked.connect(_apply)
        if dlg.exec() == QDialog.Accepted:
            _apply()

    def _set_mso_channels(self):
        """Settings → MSO Channel Setup: dialog to configure per-channel pos/scale."""
        from PySide6.QtWidgets import (QDialog, QFormLayout,
                                        QDialogButtonBox, QVBoxLayout, QHBoxLayout,
                                        QDoubleSpinBox)
        cp = self.config_panel
        dlg = QDialog(self)
        dlg.setWindowTitle("MSO Channel Setup")
        lay = QVBoxLayout(dlg)
        form = QFormLayout()

        pos_spins = []
        scale_spins = []
        for i, ch_name in enumerate(["CH1", "CH2", "CH3", "CH4"]):
            pos_spin = QDoubleSpinBox()
            pos_spin.setRange(-20, 20); pos_spin.setDecimals(1)
            pos_spin.setValue(cp.ch_pos[i]); pos_spin.setSuffix(" div")
            pos_spins.append(pos_spin)

            scale_spin = QDoubleSpinBox()
            scale_spin.setRange(0.001, 100.0); scale_spin.setDecimals(3)
            scale_spin.setValue(cp.ch_scale[i]); scale_spin.setSuffix(" V/div")
            scale_spins.append(scale_spin)

            row = QHBoxLayout()
            row.addWidget(pos_spin)
            row.addWidget(scale_spin)
            form.addRow(f"{ch_name} Pos / Scale:", row)

        lay.addLayout(form)
        btns = QDialogButtonBox(
            QDialogButtonBox.Apply | QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)

        def _apply():
            for i in range(4):
                cp.ch_pos[i] = pos_spins[i].value()
                cp.ch_scale[i] = scale_spins[i].value()
            if self.state.osc:
                osc = self.state.osc
                ch_enables = [cp.ch_enables[i].isChecked() for i in range(4)]
                for i, ch_name in enumerate(['CH1', 'CH2', 'CH3', 'CH4']):
                    if ch_enables[i]:
                        osc.chanset(ch_name, cp.ch_pos[i], 0, '1.0000E+09', cp.ch_scale[i])
                self.state.set_status("Channel setup applied")
            log.info('MainWindow', f"MSO CH: pos={cp.ch_pos}, scale={cp.ch_scale}")

        btns.button(QDialogButtonBox.Apply).clicked.connect(_apply)
        if dlg.exec() == QDialog.Accepted:
            _apply()

    def _set_label_position(self):
        """Settings → Set Label Position: dialog to configure per-channel label X/Y."""
        from PySide6.QtWidgets import (QDialog, QFormLayout, QLabel,
                                        QDialogButtonBox, QVBoxLayout, QHBoxLayout,
                                        QSpinBox)
        cp = self.config_panel
        dlg = QDialog(self)
        dlg.setWindowTitle("Label Position")
        lay = QVBoxLayout(dlg)
        form = QFormLayout()

        x_spins = []
        y_spins = []
        for i, ch_name in enumerate(["CH1", "CH2", "CH3", "CH4"]):
            x_spin = QSpinBox()
            x_spin.setRange(0, 999); x_spin.setValue(cp.ch_label_x[i])
            x_spins.append(x_spin)
            y_spin = QSpinBox()
            y_spin.setRange(0, 9999); y_spin.setValue(cp.ch_label_y[i])
            y_spins.append(y_spin)

            row = QHBoxLayout()
            row.addWidget(QLabel("X:")); row.addWidget(x_spin)
            row.addWidget(QLabel("Y:")); row.addWidget(y_spin)
            row.addStretch()
            form.addRow(f"{ch_name}:", row)

        lay.addLayout(form)
        btns = QDialogButtonBox(
            QDialogButtonBox.Apply | QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)

        def _apply():
            for i in range(4):
                cp.ch_label_x[i] = x_spins[i].value()
                cp.ch_label_y[i] = y_spins[i].value()
            log.info('MainWindow', f"Label pos: x={cp.ch_label_x}, y={cp.ch_label_y}")
            # Re-apply labels to scope with new positions
            self._on_set_label()

        btns.button(QDialogButtonBox.Apply).clicked.connect(_apply)
        if dlg.exec() == QDialog.Accepted:
            _apply()

    def _on_set_mso(self):
        """One-click full oscilloscope configuration."""
        if not self.state.osc:
            self._warn("Set MSO", "Please connect to an oscilloscope first.")
            return

        try:
            osc = self.state.osc
            cp = self.config_panel
            is_monotony = self.state.test_type == "monotony"

            osc.write('FACTORY')
            osc.write('DISplay:WAVEView1:VIEWStyle OVErlay')

            # Channel states from UI enable checkboxes
            ch_enables = [cp.ch_enables[i].isChecked() for i in range(4)]
            osc.channel_state(
                'ON' if ch_enables[0] else 'OFF',
                'ON' if ch_enables[1] else 'OFF',
                'ON' if ch_enables[2] else 'OFF',
                'ON' if ch_enables[3] else 'OFF',
            )

            # Configure enabled channels with saved attributes
            for i, ch_name in enumerate(['CH1', 'CH2', 'CH3', 'CH4']):
                if ch_enables[i]:
                    osc.chanset(ch_name, cp.ch_pos[i], 0, '1.0000E+09', cp.ch_scale[i])

            # Measurement (depends on test type)
            if is_monotony:
                measurement.measure_monotony(osc, self.state.mso5)
            else:  # sequence
                measurement.measure_sequence(osc, self.state.mso5)

            # Horizontal
            osc.hormode(cp.hor_mode)
            osc.write(f'HORIZONTAL:MODE:SCALE {cp.hor_scale:g}')
            osc.horpos(cp.hor_pos)

            # Trigger
            osc.trigger('NORMAL', cp.trig_channel, cp.trig_edge, cp.trig_level)

            osc.state('run')
            self.state.set_status("MSO configured (one-click)")
            log.info('MainWindow', f"One-click MSO: type={self.state.test_type}, "
                     f"hor={cp.hor_mode}/{self._fmt_scale(cp.hor_scale)}/{cp.hor_pos}%, "
                     f"trig={cp.trig_channel}/{cp.trig_edge}/{self._fmt_level(cp.trig_level)}, "
                     f"ch_pos={cp.ch_pos}, ch_scale={cp.ch_scale}")

            # Auto-set labels after MSO configuration
            self._on_set_label()

        except Exception as e:
            self._show_save_error("Set MSO", e)

    # =========================================================================
    # Help
    # =========================================================================

    def _show_help(self):
        """Open the user manual dialog (non-modal — won't block the main GUI)."""
        # Reuse existing dialog if already open; just bring it to front
        if hasattr(self, '_help_dlg') and self._help_dlg is not None:
            if self._help_dlg.isVisible():
                self._help_dlg.raise_()
                self._help_dlg.activateWindow()
                return
        self._help_dlg = HelpDialog()  # no parent — independent window, won't block main GUI
        self._help_dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._help_dlg.destroyed.connect(lambda: setattr(self, '_help_dlg', None))
        self._help_dlg.show()

    # =========================================================================
    # Theme
    # =========================================================================

    def _set_theme(self, theme):
        """Set theme and sync menu checkmarks + status bar button."""
        self.current_theme = theme
        apply_theme(self, theme)
        self._light_action.setChecked(theme == 'light')
        self._dark_action.setChecked(theme == 'dark')
        self.theme_btn.setText("☀️" if theme == 'dark' else "🌙")
        self.state.set_status(f"Theme: {theme}")

    def _toggle_theme(self):
        """Toggle via status bar button."""
        self._set_theme('dark' if self.current_theme == 'light' else 'light')

    # =========================================================================
    # Helpers
    # =========================================================================

    def _check_ready(self):
        if not self.state.xls:
            self._warn("Navigation", "Excel not loaded.\nPlease select an Excel file first (File Paths → Browse).")
            return False
        if not self.state.sheet_name:
            self._warn("Navigation", "Sheet not selected.\nPlease choose a sheet from the dropdown.")
            return False
        return True

    def _get_state_dict(self):
        return {
            'sheet_name': self.state.sheet_name or "Sheet1",
            'test_type': self.state.test_type,
            'flag_monotony_direction': self.state.flag_monotony_direction,
            'flag_mso_connect': self.state.flag_mso_connect,
            'mso5': self.state.mso5,
            'osc': self.state.osc,
            'xls': self.state.xls,
            'row': self.state.row,
            'init_row': self.config_panel.init_row,
        }

    def _update_item_badge(self, current_item):
        """Update current item badge."""
        log.debug('MainWindow', f'Current item: {current_item}')

    @Slot(str)
    @Slot(str)
    def _on_sheet_name_changed(self, sheet_name):
        """Handle sheet name change from combo box - activate Excel and load test data."""
        log.info('MainWindow', f'Sheet name changed: {sheet_name}')

        if not sheet_name:
            log.debug('MainWindow', 'Empty sheet name, skipping')
            return

        if not self.state.xls:
            log.debug('MainWindow', 'No Excel instance, skipping')
            return

        # Activate the sheet in Excel
        try:
            self.state.xls.activate_sheet(sheet_name)
            log.info('MainWindow', f'Excel sheet activated: {sheet_name}')
        except Exception as e:
            log.error('MainWindow', f'Error activating Excel sheet: {e}')
            self.state.set_status(f"Error: {str(e)}")
            return

        # Set test item flag and load data
        # test_type set by user in Settings card
        self._load_test_data()
        self.state.set_status(f"Sheet: {sheet_name}")

    def _update_state_from_dict(self, state_dict):
        self.state.row = state_dict.get('row', self.state.row)
        self.state.flag_monotony_direction = state_dict.get('flag_monotony_direction', self.state.flag_monotony_direction)
        self.state.pn_direction = state_dict.get('pn_direction', self.state.pn_direction)
        self.state.current_item = state_dict.get('current_item', self.state.current_item)

        # Sync R: spinboxes to new row, triggering read from Excel
        row = state_dict.get('excel_row', self.state.row)
        cp = self.config_panel
        for i in range(4):
            if cp.signal_enables[i].isChecked():
                cp.signal_rows[i].setValue(row)

        # Re-read signal values from Excel at the new row
        cp._read_initial_signals()
        # Sync CH labels to follow signal values
        for i in range(4):
            if cp.ch_enables[i].isChecked():
                sig_val = getattr(self.state, f'signal{i + 1}', '')
                cp.ch_edits[i].setText(sig_val)
                setattr(self.state, f'ch{i + 1}_label', sig_val)

        # Auto-switch trigger edge on P/N toggle for Monotony
        if (self.state.test_type == 'monotony'
                and self.state.flag_mso_connect and self.state.osc):
            direction = self.state.flag_monotony_direction
            edge = 'RISE' if direction == 1 else 'FALL'
            # Use first enabled CH as trigger source
            source = 'CH1'
            for i in range(4):
                if cp.ch_enables[i].isChecked():
                    source = f'CH{i + 1}'
                    break
            try:
                self.state.osc.write(f'TRIGGER:A:EDGE:SLOPE {edge}')
                log.info('MainWindow', f'Trigger edge → {edge} (src={source})')
            except Exception as e:
                log.warning('MainWindow', f'Failed to set trigger edge: {e}')

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
            log.error('MainWindow', f'Connection error during {operation}: {error}')
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
            log.error('MainWindow', f'Error in {operation}: {error}')
