"""Main application window orchestrating all components."""
import os, json
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QSizePolicy,
                                QScrollArea, QStatusBar, QPushButton, QLabel,
                                QMessageBox)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QCloseEvent, QAction

from .state import AppState
from .theme import apply_theme
from widgets import ConfigPanel

from core import EasyExcel, instrument_manager, test_manager, measurement, capture
from dialogs.connect_dialog import ConnectDialog


class MainWindow(QMainWindow):
    """Main application window with macOS-style layout."""

    def __init__(self):
        super().__init__()
        self.state = AppState()
        self.current_theme = 'light'

        # Connection state (restore from last session)
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

        # Restore saved scope/pic/file settings
        if saved.get('scope_path'):
            self.config_panel.project_edit.setText(saved['scope_path'])
        if 'save_to_scope' in saved:
            self.config_panel.save_to_scope_cb.setChecked(saved['save_to_scope'])
        if 'save_to_excel' in saved:
            self.config_panel.save_to_excel_cb.setChecked(saved['save_to_excel'])
        if saved.get('file_path'):
            self.state.file_path = saved['file_path']
        if saved.get('pic_path'):
            self.state.pic_path = saved['pic_path']
        if saved.get('project_name'):
            self.state.project_name = saved['project_name']
        if saved.get('init_row'):
            self.config_panel.init_row = saved['init_row']
            self.state.row = saved['init_row']
            self.config_panel.nav_bar.clamp_min(saved['init_row'])
            for rspin in self.config_panel.signal_rows:
                rspin.setMinimum(saved['init_row'])

        # Show saved IP in menu bar if any
        if self._last_ip:
            self.conn_info_label.setText(f"IP: {self._last_ip}:{self._last_port}")
        elif self._last_connect_method != 'ip':
            self.conn_info_label.setText("GPIB/USB")

    def setup_ui(self):
        self.setWindowTitle("Nettrix Power Sequence Test Tool V3.0 (PySide6)")
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
        save_action = QAction("📋  Save Excel", self)
        save_action.setToolTip("Save the opened Excel workbook")
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)
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

        # Spacer to push IP label to right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        toolbar.addWidget(self.conn_dot)
        toolbar.addWidget(self.conn_info_label)

        # -- Settings menu --
        settings_menu = menu_bar.addMenu("Settings")
        settings_menu.setToolTipsVisible(True)
        reload_action = QAction("Reload Excel", self)
        reload_action.setToolTip("Reopen Excel file and restore current sheet")
        reload_action.triggered.connect(self._reload_excel)
        settings_menu.addAction(reload_action)
        init_row_action = QAction("Set Init Row...", self)
        init_row_action.setToolTip("Set the starting row number for test items")
        init_row_action.triggered.connect(self._set_init_row)
        settings_menu.addAction(init_row_action)
        sig_col_action = QAction("Set Signal Cols...", self)
        sig_col_action.setToolTip("Set Excel column for each signal")
        sig_col_action.triggered.connect(self._set_signal_cols)
        settings_menu.addAction(sig_col_action)
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

        print("[MainWindow] UI setup complete")

    def closeEvent(self, event: QCloseEvent):
        """Handle application close — save settings, keep Excel open."""
        if hasattr(self, '_connection_monitor_timer'):
            self._connection_monitor_timer.stop()
        self._save_settings()
        print("[MainWindow] Application closed (settings saved)")
        super().closeEvent(event)

    def _load_settings(self):
        try:
            with open(self._settings_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_settings(self):
        cp = self.config_panel
        cfg = {
            'method': self._last_connect_method,
            'ip': self._last_ip,
            'port': self._last_port,
            'use_socket': self._last_use_socket,
            'scope_path': cp.project_edit.text(),
            'save_to_scope': cp.save_to_scope_cb.isChecked(),
            'save_to_excel': cp.save_to_excel_cb.isChecked(),
            'init_row': cp.init_row,
            'file_path': self.state.file_path,
            'sheet_name': self.state.sheet_name,
            'pic_path': self.state.pic_path,
            'project_name': self.state.project_name,
        }
        try:
            with open(self._settings_file, 'w') as f:
                json.dump(cfg, f, indent=2)
        except Exception as e:
            print(f"[MainWindow] Failed to save settings: {e}")

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

                # Set IP text BEFORE connection signal (so green dot prepends correctly)
                if params['method'] == 'ip':
                    self.conn_info_label.setText(f"IP: {params['ip_address']}:{params['port']}")
                else:
                    self.conn_info_label.setText("GPIB/USB")
                self.conn_info_label.repaint()

                self.state.set_connection(True)
                self.state.set_status(message)

                # Start connection monitor (every 5 seconds)
                self._connection_monitor_timer.start(5000)

                model_str = "MSO5" if model_flags['mso5'] else \
                            "DPO7000" if model_flags['dpo7000'] else \
                            "DPO5104B" if model_flags['dpo5104b'] else "Unknown"
                self.state.set_status(f"Connected: {model_str} ({params['method']})")
                print(f"[MainWindow] Connected: {model_str} via {params['method']}")
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
                print(f"[MainWindow] Reconnected: {model_str} via {self._last_connect_method}")

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
            print(f"[MainWindow] Error in _on_reconnect: {e}")

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
                print("[MainWindow] Connection lost detected (2 consecutive failures)!")
                self.state.set_connection(False)
                self._connection_monitor_timer.stop()
                self.state.set_status("⚠️ Connection lost! Click Reconnect to restore.")
                QMessageBox.warning(
                    self, "Connection Lost",
                    "Connection to the oscilloscope has been lost.\n"
                    "Click '🔄 Reconnect' to restore the connection."
                )
            else:
                print(f"[MainWindow] Connection check timeout ({self._fail_count}/2)")
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
            print(f"[MainWindow] Test data loaded: item={self.state.test_type}, "
                  f"signal1={self.state.signal1_name}, signal2={self.state.signal2_name}, "
                  f"signal3={self.state.signal3_name}")
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
            col = cp.signal_cols[i].value()
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
        spins = []
        cp = self.config_panel
        for i in range(4):
            sp = QSpinBox()
            sp.setRange(1, 99)
            sp.setValue(cp.signal_cols[i])
            spins.append(sp)
            form.addRow(f"Signal {i+1}:", sp)
        lay.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)
        if dlg.exec() == QDialog.Accepted:
            cp.signal_cols = [s.value() for s in spins]
            cp._read_initial_signals()
            print(f"[MainWindow] Signal cols set to {cp.signal_cols}")

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
            print(f"[MainWindow] Init row set to {val}")

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
        print("[MainWindow] Excel reloaded")

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
            print("[MainWindow] Excel saved")
        except Exception as e:
            self._show_save_error("Save Excel", e)

    def _on_save_pic(self):
        """Save screenshot to local + scope. No Excel data writing."""
        if not self.state.pic_path:
            self._warn("Save Picture", "Please select a picture save folder first (File Paths → Pic).")
            return
        if not self.state.osc:
            self._warn("Save Picture", "Please connect to an oscilloscope first.")
            return
        try:
            capture.Capture_Pic(
                self.state.osc, self.state.xls,
                self.state.sheet_name or "Sheet1",
                [self.state.signal1, self.state.signal2, self.state.signal3, self.state.signal4],
                [self.config_panel.signal_enables[i].isChecked() for i in range(4)],
                self.state.test_type, self.state.flag_monotony_direction,
                self.state.row, self.state.mso5, self.state.pic_path,
                self.state.project_name, save_to_excel=False,
                save_to_scope=self.config_panel.save_to_scope_cb.isChecked()
            )
            self.state.set_status("Picture saved to local" +
                (" + Scope" if self.config_panel.save_to_scope_cb.isChecked() else ""))
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
                self.state.project_name, save_to_excel=True, save_pic=False,
                save_to_scope=self.config_panel.save_to_scope_cb.isChecked()
            )
            self.state.set_status("Data saved to Excel")
        except Exception as e:
            self._show_save_error("Save Data", e)

    def _on_save_pic_and_data(self):
        """Save both screenshot and data to Excel."""
        if not self.state.osc:
            self._warn("Save Pic+Data", "Please connect to an oscilloscope first.")
            return
        try:
            capture.Capture_Pic(
                self.state.osc, self.state.xls,
                self.state.sheet_name or "Sheet1",
                [self.state.signal1, self.state.signal2, self.state.signal3, self.state.signal4],
                [self.config_panel.signal_enables[i].isChecked() for i in range(4)],
                self.state.test_type, self.state.flag_monotony_direction,
                self.state.row, self.state.mso5, self.state.pic_path,
                self.state.project_name, save_to_excel=True, save_pic=True,
                save_to_scope=self.config_panel.save_to_scope_cb.isChecked()
            )
            self.state.set_status("Picture + Data saved")
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
                labels[0], labels[1], labels[2], labels[3]
            )
            self.state.set_status("Labels set on instrument")
        except Exception as e:
            self._handle_connection_error(e, "Set Label")

    def _on_set_mso(self):
        if not self.state.osc:
            self._warn("Set MSO", "Please connect to an oscilloscope first.")
            return

        try:
            osc = self.state.osc
            is_monotony = self.state.test_type == "monotony"

            osc.write('FACTORY')
            osc.write('DISplay:WAVEView1:VIEWStyle OVErlay')

            if is_monotony:
                osc.channel_state('ON', 'OFF', 'OFF', 'OFF')
                osc.chanset('CH1', -2.5, 0, '1.0000E+09', 1)
                measurement.measure6(osc, self.state.mso5)
            else:  # sequence
                osc.channel_state('ON', 'ON', 'OFF', 'OFF')
                osc.chanset('CH1', -2.5, 0, '1.0000E+09', 1)
                osc.chanset('CH2', -3.5, 0, '1.0000E+09', 1)
                measurement.measure1(osc, self.state.mso5)

            osc.write('HORIZONTAL:MODE AUTO')
            osc.write('HORIZONTAL:MODE:SCALE 1e-2')
            osc.write('HORIZONTAL:POSITION 30')

            osc.state('run')
            self.state.set_status("MSO configured")
            print(f"[MainWindow] MSO configured as {self.state.test_type}")

        except Exception as e:
            self._show_save_error("Set MSO", e)

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
        print(f"[MainWindow] Current item: {current_item}")

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
        # test_type set by user in Settings card
        self._load_test_data()
        self.state.set_status(f"Sheet: {sheet_name}")

    def _update_state_from_dict(self, state_dict):
        self.state.row = state_dict.get('row', self.state.row)
        self.state.flag_monotony_direction = state_dict.get('flag_monotony_direction', self.state.flag_monotony_direction)
        self.state.signal1_name = state_dict.get('signal1_name', '')
        self.state.signal2_name = state_dict.get('signal2_name', '')
        self.state.signal3_name = state_dict.get('signal3_name', '')
        self.state.signal4_name = state_dict.get('signal4_name', '')

        self.state.signal1 = self.state.signal1_name
        self.state.signal2 = self.state.signal2_name
        self.state.signal3 = self.state.signal3_name
        self.state.signal4 = self.state.signal4_name
        self.state.pn_direction = state_dict.get('pn_direction', self.state.pn_direction)
        self.state.current_item = state_dict.get('current_item', self.state.current_item)

        # Sync R: only for enabled signals; disabled keep their default value
        row = state_dict.get('excel_row', self.state.row)
        cp = self.config_panel
        for i in range(4):
            if cp.signal_enables[i].isChecked():
                cp.signal_rows[i].blockSignals(True)
                cp.signal_rows[i].setValue(row)
                cp.signal_rows[i].blockSignals(False)

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
