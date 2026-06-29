"""Configuration panel with macOS-style cards for all settings."""
import sys, os, json
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                                QLineEdit, QPushButton, QFormLayout,
                                QGraphicsDropShadowEffect, QComboBox,
                                QPlainTextEdit, QFileDialog, QSpinBox, QCheckBox)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QColor, QTextCursor

from .nav_bar import NavBar


class LogStream:
    """Redirects stdout/stderr to a QPlainTextEdit and a log file, with early buffer."""
    _buffer = []

    def __init__(self, widget=None):
        self.widget = widget
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        # Create timestamped log file; keep max 10 logs
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        logs = sorted([f for f in os.listdir(log_dir) if f.startswith('log_')])
        while len(logs) >= 20:
            os.remove(os.path.join(log_dir, logs.pop(0)))  # delete oldest
        fname = datetime.now().strftime("log_%Y%m%d_%H%M%S.txt")
        self._log_file = open(os.path.join(log_dir, fname), 'w', encoding='utf-8')

    def write(self, text):
        if text.strip():
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            line = f"[{ts}] {text.rstrip()}\n"
            self._stdout.write(text)
            self._log_file.write(line)
            self._log_file.flush()
            if self.widget:
                self._flush_buffer()
                self.widget.appendPlainText(f"[{ts}] {text.rstrip()}")
                self.widget.moveCursor(QTextCursor.MoveOperation.End)
            else:
                self._buffer.append(f"[{ts}] {text.rstrip()}")
        else:
            self._stdout.write(text)

    def _flush_buffer(self):
        if self._buffer:
            for line in self._buffer:
                self.widget.appendPlainText(line)
            self._buffer.clear()
            self.widget.moveCursor(QTextCursor.MoveOperation.End)

    def flush(self):
        self._stdout.flush()

    def install(self):
        sys.stdout = self
        sys.stderr = self

    def uninstall(self):
        self._log_file.close()
        sys.stdout = self._stdout
        sys.stderr = self._stderr


# ── Install early, before any print() calls ──
_log_stream = LogStream()
_log_stream.install()


class ConfigCard(QFrame):
    """A rounded card with shadow — QFrame so QSS padding renders."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("configCard")
        self.setFrameShape(QFrame.Shape.NoFrame)  # let QSS handle border
        self.setup_ui(title)

    def setup_ui(self, title):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        layout.addWidget(title_label)

        # Content widget (will be set by parent)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.content)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(6)
        shadow.setOffset(0, 1)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)


class ConfigPanel(QWidget):
    """Main configuration panel with all cards."""

    set_label_clicked = Signal()
    save_pic_clicked = Signal()
    save_data_clicked = Signal()
    set_mso_clicked = Signal()
    save_pic_and_data_clicked = Signal()

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        # Data columns (configurable via Settings → Set Data Columns)
        self.data_col = 7              # Sequence: DELAY column (default G)
        self.mono_p_cols = [9, 10, 11, 12]   # P: TOP, BASE, MAX, MIN (I,J,K,L)
        self.mono_n_cols = [13, 14, 15, 16]  # N: TOP, BASE, MAX, MIN (M,N,O,P)
        self.seq_pic_col = 9           # Sequence picture column (default I)
        self.mono_p_pic_col = 17       # Monotony P picture column (default Q)
        self.mono_n_pic_col = 18       # Monotony N picture column (default R)

        # MSO horizontal settings
        self.hor_mode = "AUTO"         # "AUTO" or "MANUAL"
        self.hor_scale = 0.01          # seconds/div
        self.hor_pos = 30              # percent

        # MSO channel position/scale (per channel)
        self.ch_pos = [-2.5, -3.5, -3.5, -3.5]
        self.ch_scale = [1.0, 1.0, 1.0, 1.0]

        # Label position (per channel)
        self.ch_label_x = [10, 10, 10, 10]
        self.ch_label_y = [40, 40, 40, 40]
        self.nav_bar = NavBar()
        self.setup_ui()
        self.connect_signals()
        # Sync defaults for current test type (signals connected now)
        self._on_test_type_changed(self.test_type_combo.currentText())

    def setup_ui(self):
        """Two columns + full-width bottom toolbar."""
        # Qt6 UX: 8px dialog margins, 6px between controls, 4px compact card gaps
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 2, 8, 4)
        outer.setSpacing(0)

        # ===== Two-column area =====
        columns = QWidget()
        main_layout = QHBoxLayout(columns)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)          # gap between left/right columns
        main_layout.setStretch(0, 6)        # left: 60%
        main_layout.setStretch(1, 4)        # right: 40%

        # ===== LEFT COLUMN: Display =====
        left_col = QWidget()
        left_layout = QVBoxLayout(left_col)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(2)

        # --- File Paths ---
        self.file_card = ConfigCard("File Paths")
        file_layout = QFormLayout()
        file_layout.setContentsMargins(0, 2, 0, 0)
        file_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        file_layout.setFormAlignment(Qt.AlignLeft)
        file_layout.setSpacing(4)           # gap between form rows

        self.excel_edit = QLineEdit()
        self.excel_edit.setReadOnly(True)
        self.excel_edit.setPlaceholderText("No file selected")
        self.excel_browse = QPushButton("Browse")
        self.excel_browse.setObjectName("secondary")
        self.excel_browse.setFixedWidth(70)
        self.excel_browse.setToolTip("Select Excel test report file")
        self.excel_browse.clicked.connect(self._browse_excel)

        self.pic_edit = QLineEdit()
        self.pic_edit.setReadOnly(True)
        self.pic_edit.setPlaceholderText("No folder selected")
        self.pic_browse = QPushButton("Browse")
        self.pic_browse.setObjectName("secondary")
        self.pic_browse.setFixedWidth(70)
        self.pic_browse.setToolTip("Select local picture save folder")
        self.pic_browse.clicked.connect(self._browse_pic)

        file_layout.addRow("Excel:", self._create_path_row(self.excel_edit, self.excel_browse))
        file_layout.addRow("Pic:", self._create_path_row(self.pic_edit, self.pic_browse))
        self.file_card.content_layout.addLayout(file_layout)
        left_layout.addWidget(self.file_card, 0, Qt.AlignTop)

        # --- Signal Display ---
        self.signal_card = ConfigCard("Signals")
        signal_layout = QFormLayout()
        signal_layout.setContentsMargins(0, 2, 0, 0)
        signal_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        signal_layout.setFormAlignment(Qt.AlignLeft)
        signal_layout.setSpacing(4)

        # Signal rows: ☑ enable + name + non-scrollable R:/C: spinboxes
        self.signal_edits = []
        self.signal_enables = []
        self.signal_rows = []
        self.signal_cols = [5, 6, 7, 8]  # stored values, not shown in UI
        defaults = [(True, 8), (True, 8), (False, 8), (False, 8)]

        for i, (en, drow) in enumerate(defaults):
            row_w = QWidget()
            row_lay = QHBoxLayout(row_w)
            row_lay.setContentsMargins(0, 0, 0, 0)
            row_lay.setSpacing(4)

            cb = QCheckBox()
            cb.setChecked(en)
            cb.setFixedWidth(22)
            cb.toggled.connect(lambda checked, idx=i:
                self._on_signal_toggled(idx))
            row_lay.addWidget(cb)
            self.signal_enables.append(cb)

            edit = QLineEdit()
            edit.setReadOnly(True)
            row_lay.addWidget(edit, 1)
            self.signal_edits.append(edit)

            rspin = QSpinBox()
            rspin.setRange(1, 999); rspin.setValue(drow)
            rspin.setPrefix("R:"); rspin.setFixedWidth(54)
            rspin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
            rspin.installEventFilter(self)
            rspin.valueChanged.connect(lambda v, idx=i: self._on_signal_coord_changed(idx))
            if not en: rspin.setEnabled(False)
            row_lay.addWidget(rspin)
            self.signal_rows.append(rspin)

            signal_layout.addRow(f"Sig {i + 1}:", row_w)

        self.signal1_edit = self.signal_edits[0]
        self.signal2_edit = self.signal_edits[1]
        self.signal3_edit = self.signal_edits[2]
        self.signal4_edit = self.signal_edits[3]

        self.signal_card.content_layout.addLayout(signal_layout)
        left_layout.addWidget(self.signal_card, 0, Qt.AlignTop)

        # NavBar in left column, directly below Signals
        left_layout.addSpacing(2)
        left_layout.addWidget(self.nav_bar)

        # Log panel — captures all stdout/stderr output
        self.log_card = ConfigCard("Log")
        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(500)
        self.log_view.setPlaceholderText("Log output…")
        self.log_card.content_layout.addWidget(self.log_view)
        left_layout.addWidget(self.log_card, 1)

        # Wire the global LogStream to this widget (flushes buffer)
        _log_stream.widget = self.log_view
        _log_stream._flush_buffer()

        # ===== RIGHT COLUMN: Settings (single merged card) =====
        right_col = QWidget()
        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.settings_card = ConfigCard("Settings")
        card = self.settings_card

        # -- Project Info section --
        info_layout = QFormLayout()
        info_layout.setContentsMargins(0, 2, 0, 0)
        info_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        info_layout.setFormAlignment(Qt.AlignLeft)
        info_layout.setSpacing(4)

        self.project_edit = QLineEdit()
        self.project_edit.setPlaceholderText("e.g. TH_V2 or D:\\MyProject")
        self.sheet_combo = QComboBox()
        self.sheet_combo.setPlaceholderText("Select sheet…")

        info_layout.addRow("Scope:", self.project_edit)
        info_layout.addRow("Sheet:", self.sheet_combo)

        self.test_type_combo = QComboBox()
        self.test_type_combo.addItems(["Sequence", "Monotony"])
        self.test_type_combo.setCurrentText(
            "Monotony" if self.state.test_type == "monotony" else "Sequence")
        info_layout.addRow("Type:", self.test_type_combo)
        card.content_layout.addLayout(info_layout)

        # -- Separator --
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("QFrame { color: #E5E5E7; max-height: 1px; margin: 4px 0; }")
        card.content_layout.addWidget(sep)

        # -- Channel Labels section --
        label_layout = QFormLayout()
        label_layout.setContentsMargins(0, 2, 0, 0)
        label_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label_layout.setFormAlignment(Qt.AlignLeft)
        label_layout.setSpacing(4)

        # CH rows with enable checkbox + editable label
        self.ch_edits = []
        self.ch_enables = []
        ch_defaults = [(True, "CH1…"), (True, "CH2…"), (False, "CH3…"), (False, "CH4…")]

        self.pn_badge = QLabel("P")
        self.pn_badge.setFixedSize(22, 22)
        self.pn_badge.setAlignment(Qt.AlignCenter)
        self.pn_badge.setVisible(self.state.test_type == "monotony")
        self.pn_badge.setStyleSheet("""
            QLabel {
                background-color: #2563EB;
                color: white;
                border-radius: 11px;
                font-weight: 600;
                font-size: 10px;
            }
        """)

        for i, (en, ph) in enumerate(ch_defaults):
            row_w = QWidget()
            row_lay = QHBoxLayout(row_w)
            row_lay.setContentsMargins(0, 0, 0, 0)
            row_lay.setSpacing(4)

            cb = QCheckBox()
            cb.setChecked(en)
            cb.setFixedWidth(22)
            row_lay.addWidget(cb)
            self.ch_enables.append(cb)

            edit = QLineEdit()
            edit.setPlaceholderText(ph)
            edit.setEnabled(en)
            row_lay.addWidget(edit, 1)
            self.ch_edits.append(edit)

            if i == 0:
                row_lay.addWidget(self.pn_badge)

            cb.toggled.connect(lambda checked, e=edit:
                e.setEnabled(checked))

            label_layout.addRow(f"CH{i + 1}:", row_w)

        self.ch1_edit = self.ch_edits[0]
        self.ch2_edit = self.ch_edits[1]
        self.ch3_edit = self.ch_edits[2]
        self.ch4_edit = self.ch_edits[3]

        card.content_layout.addLayout(label_layout)

        # Set Label button
        self.set_label_btn = QPushButton("🏷 Set Label")
        self.set_label_btn.setMinimumWidth(120)
        self.set_label_btn.setToolTip("Write enabled channel labels to oscilloscope")
        self.set_label_btn.clicked.connect(lambda: (
            print("[ConfigPanel] Set Label clicked"), self.set_label_clicked.emit()
        ))
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 4, 0, 0)
        btn_layout.addWidget(self.set_label_btn)
        btn_layout.addStretch()
        card.content_layout.addWidget(btn_row)

        right_layout.addWidget(card, 0, Qt.AlignTop)

        # -- Save Picture card (two columns: options left, buttons right) --
        self.save_card = ConfigCard("Save Picture")
        save_cols = QHBoxLayout()
        save_cols.setContentsMargins(0, 4, 0, 0)
        save_cols.setSpacing(12)

        # Left column: checkboxes + Save Pic
        left_save = QVBoxLayout()
        left_save.setSpacing(4)
        self.save_to_excel_cb = QCheckBox("Save to Excel")
        self.save_to_excel_cb.setChecked(True)
        self.save_to_scope_cb = QCheckBox("Save to Scope")
        self.save_to_scope_cb.setChecked(True)
        self.save_to_scope_cb.toggled.connect(
            lambda en: self.project_edit.setEnabled(en))
        left_save.addWidget(self.save_to_excel_cb)
        left_save.addWidget(self.save_to_scope_cb)
        self.save_pic_btn = QPushButton("📸 Save Pic")
        self.save_pic_btn.setMinimumWidth(140)
        self.save_pic_btn.setToolTip("Capture screenshot from oscilloscope, save to local + Scope")
        self.save_pic_btn.clicked.connect(lambda: self.save_pic_clicked.emit())
        left_save.addWidget(self.save_pic_btn)
        left_save.addStretch()
        save_cols.addLayout(left_save)

        # Single vertical separator (full height)
        vline = QFrame()
        vline.setFrameShape(QFrame.Shape.VLine)
        vline.setStyleSheet("QFrame { color: #E5E5E7; }")
        save_cols.addWidget(vline)

        # Right column: Save Data + Save Pic+Data
        right_save = QVBoxLayout()
        right_save.setSpacing(4)
        self.save_data_btn = QPushButton("📊 Save Data")
        self.save_data_btn.setMinimumWidth(140)
        self.save_data_btn.setToolTip("Read measurements from oscilloscope, write to Excel")
        self.save_data_btn.clicked.connect(lambda: self.save_data_clicked.emit())
        right_save.addWidget(self.save_data_btn)
        self.save_both_btn = QPushButton("📸📊 Save Pic + Data")
        self.save_both_btn.setMinimumWidth(140)
        self.save_both_btn.setToolTip("Screenshot + measurement data to local, Excel, and Scope")
        self.save_both_btn.clicked.connect(lambda: self.save_pic_and_data_clicked.emit())
        right_save.addWidget(self.save_both_btn)
        right_save.addStretch()
        save_cols.addLayout(right_save)

        self.save_card.content_layout.addLayout(save_cols)
        right_layout.addWidget(self.save_card, 0, Qt.AlignTop)

        # -- Set MSO card --
        self.mso_card = ConfigCard("Set MSO")
        self.set_mso_btn = QPushButton("⚡ One-Click Config")
        self.set_mso_btn.setMinimumWidth(140)
        self.set_mso_btn.setToolTip("Full oscilloscope configuration (settings from menu dialogs)")
        self.set_mso_btn.clicked.connect(lambda: self.set_mso_clicked.emit())
        mso_btn_row = QWidget()
        mso_btn_lay = QHBoxLayout(mso_btn_row)
        mso_btn_lay.setContentsMargins(0, 4, 0, 0)
        mso_btn_lay.addWidget(self.set_mso_btn)
        mso_btn_lay.addStretch()
        self.mso_card.content_layout.addWidget(mso_btn_row)

        right_layout.addWidget(self.mso_card, 0, Qt.AlignTop)
        right_layout.addStretch()

        main_layout.addWidget(left_col, 1)
        main_layout.addWidget(right_col, 1)
        outer.addWidget(columns)

    def _create_pn_row(self, line_edit, badge):
        """Create CH1 row with line edit and P/N badge."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(line_edit, 1)
        layout.addWidget(badge)
        return widget

    def _create_path_row(self, line_edit, button):
        """Create a row with line edit and browse button."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(line_edit, 1)
        layout.addWidget(button)
        return widget

    def log(self, msg):
        """Append a timestamped message to the log panel."""
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_view.appendPlainText(f"[{ts}] {msg}")

    def cleanup(self):
        """Restore stdout/stderr before app exit."""
        _log_stream.uninstall()

    def connect_signals(self):
        """Connect state signals to UI updates."""
        # GUI reads state
        self.state.file_path_changed.connect(self._on_file_path_changed)
        self.state.pic_path_changed.connect(self.pic_edit.setText)
        self.state.sheet_name_changed.connect(self.sheet_combo.setCurrentText)
        self.state.signal1_changed.connect(self.signal1_edit.setText)
        self.state.signal2_changed.connect(self.signal2_edit.setText)
        self.state.signal3_changed.connect(self.signal3_edit.setText)
        self.state.signal4_changed.connect(self.signal4_edit.setText)
        self.state.project_name_changed.connect(self.project_edit.setText)
        self.state.pn_direction_changed.connect(self._update_pn_badge)

        # Sync signal names to channel label edits (one-way)
        self.state.signal1_changed.connect(
            lambda t: self.ch_edits[0].setText(t) if not self.ch_edits[0].text() else None)
        self.state.signal2_changed.connect(
            lambda t: self.ch_edits[1].setText(t) if not self.ch_edits[1].text() else None)
        self.state.signal3_changed.connect(
            lambda t: self.ch_edits[2].setText(t) if not self.ch_edits[2].text() else None)
        self.state.signal4_changed.connect(
            lambda t: self.ch_edits[3].setText(t) if not self.ch_edits[3].text() else None)

        # GUI writes to state (two-way binding)
        self.project_edit.textChanged.connect(lambda t: setattr(self.state, 'project_name', t))
        self.sheet_combo.currentTextChanged.connect(self._on_sheet_selected)
        self.test_type_combo.currentTextChanged.connect(
            lambda t: self._on_test_type_changed(t))
        self.ch_edits[0].textChanged.connect(lambda t: setattr(self.state, 'ch1_label', t))
        self.ch_edits[1].textChanged.connect(lambda t: setattr(self.state, 'ch2_label', t))
        self.ch_edits[2].textChanged.connect(lambda t: setattr(self.state, 'ch3_label', t))
        self.ch_edits[3].textChanged.connect(lambda t: setattr(self.state, 'ch4_label', t))

    def _on_file_path_changed(self, file_path):
        """Handle file path change — connect to already-open Excel if possible."""
        if not file_path:
            return

        self.excel_edit.setText(file_path)
        self._raise_gui()

        try:
            from core import EasyExcel
            abs_path = os.path.abspath(file_path)
            fname = os.path.basename(abs_path)
            print(f"[ConfigPanel] _on_file_path_changed: {abs_path}")

            # Release previous Excel reference (don't close the app)
            if hasattr(self.state, 'xls') and self.state.xls:
                self.state.xls = None

            # Try connecting to an already-open Excel instance
            xls = None
            try:
                xls = EasyExcel(abs_path)
            except Exception:
                pass

            if xls is None:
                print("[ConfigPanel] Failed to open Excel")
                return

            # Load sheet names
            sheet_names = xls.get_sheet_names()
            self.sheet_combo.blockSignals(True)
            self.sheet_combo.clear()
            self.sheet_combo.addItems(sheet_names)
            self.sheet_combo.setPlaceholderText("Select sheet...")
            self.sheet_combo.blockSignals(False)

            self.state.xls = xls
            print(f"[ConfigPanel] Loaded {len(sheet_names)} sheets (Excel connected)")

        except Exception as e:
            print(f"[ConfigPanel] Error loading sheet names: {e}")
            self.sheet_combo.clear()
            self.sheet_combo.setPlaceholderText("Error loading sheets")
            self.state.xls = None

    def _update_pn_badge(self, direction):
        """Update P/N direction badge."""
        self.pn_badge.setText(direction or "P")
        if direction == "N":
            self.pn_badge.setStyleSheet("""
                QLabel {
                    background-color: #FF3B30;
                    color: white;
                    border-radius: 11px;
                    font-weight: 600;
                    font-size: 10px;
                }
            """)
        else:
            self.pn_badge.setStyleSheet("""
                QLabel {
                    background-color: #2563EB;
                    color: white;
                    border-radius: 11px;
                    font-weight: 600;
                    font-size: 10px;
                }
            """)

    def _on_sheet_selected(self, sheet_name):
        """Handle sheet selection with confirmation dialog."""
        print(f"[ConfigPanel] _on_sheet_selected called with: {sheet_name}")
        print(f"[ConfigPanel] Current state.sheet_name: {self.state.sheet_name}")
        print(f"[ConfigPanel] Excel object available: {self.state.xls is not None}")

        if sheet_name and sheet_name != self.state.sheet_name:
            from dialogs.sheet_selection_dialog import SheetSelectionDialog
            dialog = SheetSelectionDialog([sheet_name], self)
            print(f"[ConfigPanel] Dialog created, waiting for user selection...")

            if dialog.exec() == SheetSelectionDialog.Accepted:
                selected = dialog.selected_sheet
                print(f"[ConfigPanel] Dialog accepted, selected sheet: {selected}")
                self.state.sheet_name = selected
                self.state.set_status(f"Sheet selected: {selected}")
                self._raise_gui()
                # Apply saved config for this sheet before reading signals
                # (so that init_row and signal R:/C: are correct)
                self._apply_sheet_config(selected)
                self._read_initial_signals()
                print(f"[ConfigPanel] State updated, signal should be emitted")
            else:
                print(f"[ConfigPanel] Dialog cancelled, resetting to: {self.state.sheet_name}")
                # Reset to previous selection
                self.sheet_combo.setCurrentText(self.state.sheet_name)
        else:
            print(f"[ConfigPanel] Sheet not selected or same as current, skipping")

    def _browse_excel(self):
        """Open file dialog for Excel selection."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel Test Report",
            "", "Excel files (*.xlsx *.xls)"
        )
        if file_path:
            # Close any existing Excel before opening new one
            if hasattr(self.state, 'xls') and self.state.xls:
                try:
                    print("[ConfigPanel] Closing previous Excel instance...")
                    self.state.xls.close()
                    self.state.xls = None
                except Exception as e:
                    print(f"[ConfigPanel] Error closing previous Excel: {e}")
                    self.state.xls = None

            # Set file path - this triggers _on_file_path_changed which
            # creates the Excel instance and loads sheets
            self.state.file_path = file_path
            print(f"[ConfigPanel] Excel path selected: {file_path}")

    def _browse_pic(self):
        """Open directory dialog for picture save location."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Picture Save Folder", ""
        )
        if dir_path:
            self.state.pic_path = dir_path
            print(f"[ConfigPanel] Picture path selected: {dir_path}")

    # ── Signal reading from Excel ──────────────────────────────────────


    def _raise_gui(self):
        """Bring GUI to foreground above Excel."""
        w = self.window()
        if w:
            w.raise_()
            w.activateWindow()

    def _read_initial_signals(self):
        """Read enabled signals from Excel using configured R:/C: and set state."""
        if not hasattr(self.state, 'xls') or not self.state.xls:
            return
        if not self.state.sheet_name:
            return
        xls = self.state.xls
        sheet = self.state.sheet_name
        try:
            for i in range(4):
                if not self.signal_enables[i].isChecked():
                    setattr(self.state, f'signal{i + 1}', '')
                    setattr(self.state, f'signal{i + 1}_name', '')
                    continue
                row = self.signal_rows[i].value()
                col = self.signal_cols[i]
                val = xls.getCell(sheet, row, col)
                name = str(val) if val is not None else ''
                setattr(self.state, f'signal{i + 1}', name)
                setattr(self.state, f'signal{i + 1}_name', name)
            print(f"[ConfigPanel] Initial signals read from sheet '{sheet}'")
        except Exception as e:
            print(f"[ConfigPanel] Error reading initial signals: {e}")

    # Stored separately from UI
    init_row = 8

    def _on_test_type_changed(self, text):
        """Update defaults when test type changes."""
        is_monotony = text == 'Monotony'
        setattr(self.state, 'test_type', 'monotony' if is_monotony else 'sequence')
        self.pn_badge.setVisible(is_monotony)
        # Set defaults per type
        if is_monotony:
            self.signal_cols = [2, 2, 2, 2]
            self.init_row = 21
            # Monotony: only SIG1 + CH1 enabled by default
            sig_defaults = [True, False, False, False]
            ch_defaults   = [True, False, False, False]
        else:
            self.signal_cols = [5, 6, 7, 8]
            self.init_row = 8
            # Sequence: SIG1 + SIG2, CH1 + CH2 enabled by default
            sig_defaults = [True, True, False, False]
            ch_defaults   = [True, True, False, False]
        self.state.row = self.init_row
        # Update signal enables + R spinboxes + channel enables
        for i in range(4):
            self.signal_enables[i].setChecked(sig_defaults[i])
            self.signal_rows[i].setMinimum(self.init_row)
            self.signal_rows[i].setValue(self.init_row)
            self.signal_rows[i].setEnabled(sig_defaults[i])
            self.ch_enables[i].setChecked(ch_defaults[i])
            self.ch_edits[i].setEnabled(ch_defaults[i])
            if not ch_defaults[i]:
                self.ch_edits[i].clear()
        self.nav_bar.clamp_min(self.init_row)
        self.nav_bar.reset_jump(self.init_row)
        self._read_initial_signals()
        # Force CH label values to follow signal values after type switch
        for i in range(4):
            if ch_defaults[i]:
                sig_val = getattr(self.state, f'signal{i + 1}', '')
                self.ch_edits[i].setText(sig_val)
                setattr(self.state, f'ch{i + 1}_label', sig_val)

    def _on_signal_toggled(self, idx):
        """Enable/disable signal: gray spinboxes, clear name when disabled."""
        en = self.signal_enables[idx].isChecked()
        self.signal_rows[idx].setEnabled(en)
        if not en:
            self.signal_edits[idx].clear()
            setattr(self.state, f'signal{idx + 1}', '')
            setattr(self.state, f'signal{idx + 1}_name', '')
            print(f"  Sig{idx + 1}: ✗ disabled")
        else:
            print(f"  Sig{idx + 1}: ✓ enabled")
            self.signal_rows[idx].blockSignals(True)
            self.signal_rows[idx].setValue(self.state.row)
            self.signal_rows[idx].blockSignals(False)
            self._on_signal_coord_changed(idx)

    def _on_signal_coord_changed(self, idx):
        """Read cell from Excel when R:/C: changes, update signal display."""
        if not hasattr(self.state, 'xls') or not self.state.xls:
            return
        if not self.state.sheet_name:
            return
        en = self.signal_enables[idx].isChecked()
        if not en:
            return  # disabled: skip logging
        row = self.signal_rows[idx].value()
        col = self.signal_cols[idx]  # int list, not spinbox
        try:
            val = self.state.xls.getCell(self.state.sheet_name, row, col)
            name = str(val) if val is not None else ''
            setattr(self.state, f'signal{idx + 1}', name)
            setattr(self.state, f'signal{idx + 1}_name', name)
            print(f"  Sig{idx + 1}: [✓] R:{row} C:{col} = {name}")
        except Exception as e:
            print(f"[ConfigPanel] Error reading cell R:{row} C:{col}: {e}")

    def eventFilter(self, obj, event):
        """Block wheel scroll on spinboxes."""
        if event.type() == QEvent.Wheel:
            return True
        return super().eventFilter(obj, event)

    # ── Config import/export ───────────────────────────────────────────

    def _gather_sheet_config(self, sheet_name):
        """Build a dict of sheet-specific settings for the given sheet."""
        return {
            "test_type": self.state.test_type,
            "init_row": self.init_row,
            "signal_cols": list(self.signal_cols),
            "signals": [self.signal_enables[i].isChecked() for i in range(4)],
            "ch_enables": [self.ch_enables[i].isChecked() for i in range(4)],
            "data_col": self.data_col,
            "mono_p_cols": list(self.mono_p_cols),
            "mono_n_cols": list(self.mono_n_cols),
            "seq_pic_col": self.seq_pic_col,
            "mono_p_pic_col": self.mono_p_pic_col,
            "mono_n_pic_col": self.mono_n_pic_col,
            "ch_label_x": list(self.ch_label_x),
            "ch_label_y": list(self.ch_label_y),
            "save_to_excel": self.save_to_excel_cb.isChecked(),
            "save_to_scope": self.save_to_scope_cb.isChecked(),
        }

    def _apply_sheet_config(self, sheet_name):
        """Apply saved config for the given sheet, if available in loaded config."""
        if not hasattr(self, '_loaded_config') or not self._loaded_config:
            return
        sheets = self._loaded_config.get("sheets", {})
        if sheet_name not in sheets:
            print(f"[ConfigPanel] No saved config for sheet '{sheet_name}'")
            return
        sc = sheets[sheet_name]
        print(f"[ConfigPanel] Applying saved config for sheet '{sheet_name}'")

        # Test type (applied first; resets init_row to default for the type)
        if "test_type" in sc:
            wanted = "Monotony" if sc["test_type"] == "monotony" else "Sequence"
            self.test_type_combo.blockSignals(True)
            self.test_type_combo.setCurrentText(wanted)
            self.test_type_combo.blockSignals(False)
            self._on_test_type_changed(wanted)

        # Init row — override with saved value (from Settings → Set Init Row)
        if "init_row" in sc:
            self.init_row = sc["init_row"]
            self.state.row = sc["init_row"]
            # Clamp signal R: spinboxes to >= init_row
            for rspin in self.signal_rows:
                rspin.setMinimum(sc["init_row"])

        # Signal columns (global per sheet, from Settings → Set Signal Cols)
        if "signal_cols" in sc:
            self.signal_cols = list(sc["signal_cols"])

        # Signals (enable only; R:/C: derived from init_row + signal_cols)
        if "signals" in sc:
            for i, en in enumerate(sc["signals"]):
                if i < 4:
                    self.signal_enables[i].setChecked(en)
                    self.signal_rows[i].setValue(self.init_row)
                    self.signal_rows[i].setEnabled(en)

        # Channel enables
        if "ch_enables" in sc:
            for i, en in enumerate(sc["ch_enables"]):
                if i < 4:
                    self.ch_enables[i].setChecked(en)

        # Data columns (from Settings → Set Data Columns)
        if "data_col" in sc:
            self.data_col = sc["data_col"]
        if "mono_p_cols" in sc:
            self.mono_p_cols = list(sc["mono_p_cols"])
        if "mono_n_cols" in sc:
            self.mono_n_cols = list(sc["mono_n_cols"])

        # Picture columns (from Settings → Set Picture Columns)
        if "seq_pic_col" in sc:
            self.seq_pic_col = sc["seq_pic_col"]
        if "mono_p_pic_col" in sc:
            self.mono_p_pic_col = sc["mono_p_pic_col"]
        if "mono_n_pic_col" in sc:
            self.mono_n_pic_col = sc["mono_n_pic_col"]

        # Label position
        if "ch_label_x" in sc:
            self.ch_label_x = list(sc["ch_label_x"])
        if "ch_label_y" in sc:
            self.ch_label_y = list(sc["ch_label_y"])

        # Save checkboxes
        if "save_to_excel" in sc:
            self.save_to_excel_cb.setChecked(sc["save_to_excel"])
        if "save_to_scope" in sc:
            self.save_to_scope_cb.setChecked(sc["save_to_scope"])

    def remember_current_sheet_config(self):
        """Save current sheet's config into loaded config memory (for accumulation).

        Call this after data is successfully saved to a sheet, so that the sheet's
        config is accumulated and will be included in the next export.
        """
        sheet = self.state.sheet_name
        if not sheet:
            return
        if not hasattr(self, '_loaded_config') or self._loaded_config is None:
            self._loaded_config = {"sheets": {}}
        if "sheets" not in self._loaded_config:
            self._loaded_config["sheets"] = {}
        self._loaded_config["sheets"][sheet] = self._gather_sheet_config(sheet)
        print(f"[ConfigPanel] Remembered config for sheet '{sheet}'")

    def export_config(self):
        """Export all accumulated sheet configs to a JSON file."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Config", "config.json", "JSON (*.json)")
        if not path:
            return

        # Start from in-memory accumulated config, or load existing file
        cfg = {}
        if hasattr(self, '_loaded_config') and self._loaded_config:
            cfg = self._loaded_config
        elif os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
            except Exception:
                pass
        if "sheets" not in cfg:
            cfg["sheets"] = {}

        # Global settings
        cfg["project_name"] = self.state.project_name
        cfg["excel_path"] = self.state.file_path
        cfg["pic_path"] = self.state.pic_path

        # Always include current sheet (in case it hasn't been remembered yet)
        current_sheet = self.state.sheet_name or "Sheet1"
        cfg["sheets"][current_sheet] = self._gather_sheet_config(current_sheet)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        sheet_names = list(cfg["sheets"].keys())
        print(f"[ConfigPanel] Config exported to {path} ({len(sheet_names)} sheets: {sheet_names})")

    def import_config(self):
        """Import settings from a JSON file. Supports sheet-aware format."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Config", "", "JSON (*.json)")
        if not path:
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)

            # Store for auto-apply on sheet switch
            self._loaded_config = cfg
            self._config_file_path = path

            # Apply global settings
            if cfg.get("project_name"):
                self.state.project_name = cfg["project_name"]
            if cfg.get("excel_path") and os.path.exists(cfg["excel_path"]):
                self.state.file_path = cfg["excel_path"]
            if cfg.get("pic_path") and os.path.isdir(cfg["pic_path"]):
                self.state.pic_path = cfg["pic_path"]

            # Apply current sheet's config if available
            current_sheet = self.state.sheet_name
            if current_sheet:
                self._apply_sheet_config(current_sheet)

            # List loaded sheets
            sheets = cfg.get("sheets", {})
            print(f"[ConfigPanel] Config imported from {path} "
                  f"({len(sheets)} sheets: {list(sheets.keys())})")

        except Exception as e:
            print(f"[ConfigPanel] Error importing config: {e}")