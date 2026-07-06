"""Configuration panel with macOS-style cards for all settings."""
import sys, os, json
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                                QLineEdit, QPushButton, QFormLayout,
                                QGraphicsDropShadowEffect, QComboBox,
                                QPlainTextEdit, QFileDialog, QSpinBox, QCheckBox)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QColor
from core.logger import log

from .nav_bar import NavBar


class LogStream:
    """Redirects stdout/stderr to a QPlainTextEdit widget and a log file.

    - Console:  raw text WITH ANSI escape codes (terminal renders colors).
    - Log file: plain text — ANSI codes stripped.
    - Widget:   plain text — ANSI codes stripped (fast, no HTML rendering).
    """
    _buffer = []

    _ANSI_RE = None

    @classmethod
    def _strip_ansi(cls, text):
        """Remove ANSI escape sequences from *text*."""
        if cls._ANSI_RE is None:
            import re
            cls._ANSI_RE = re.compile(r'\033\[[0-9;]*m')
        return cls._ANSI_RE.sub('', text)

    def __init__(self, widget=None):
        self.widget = widget
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        # Create timestamped log file; keep max 20 logs
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        logs = sorted([f for f in os.listdir(log_dir) if f.startswith('log_')])
        while len(logs) >= 20:
            os.remove(os.path.join(log_dir, logs.pop(0)))
        fname = datetime.now().strftime("log_%Y%m%d_%H%M%S.txt")
        self._log_file = open(os.path.join(log_dir, fname), 'w', encoding='utf-8')

    def write(self, text):
        if text.strip():
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Console: raw text WITH ANSI codes (None in PyInstaller windowed mode)
            if self._stdout is not None:
                self._stdout.write(text)

            # Log file + widget: plain text, ANSI stripped
            clean = self._strip_ansi(text).rstrip()
            self._log_file.write(f"[{ts}] {clean}\n")
            self._log_file.flush()
            if self.widget:
                self._flush_buffer()
                self.widget.appendPlainText(f"[{ts}] {clean}")
                self.widget.verticalScrollBar().setValue(
                    self.widget.verticalScrollBar().maximum())
            else:
                self._buffer.append(f"[{ts}] {clean}")
        else:
            if self._stdout is not None:
                self._stdout.write(text)

    def _flush_buffer(self):
        if self._buffer:
            for line in self._buffer:
                self.widget.appendPlainText(line)
            self._buffer.clear()
            self.widget.verticalScrollBar().setValue(
                self.widget.verticalScrollBar().maximum())

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
        # Data enable flags — only enabled items are written to Excel
        self.seq_data_en = True
        self.mono_p_data_en = [True, True, True, True]
        self.mono_n_data_en = [True, True, True, True]
        # Rise / Fall time (Monotony only, default disabled)
        self.rise_col = 1   # A
        self.fall_col = 2   # B
        self.rise_en = False
        self.fall_en = False
        self.seq_pic_col = 9           # Sequence picture column (default I)
        self.mono_p_pic_col = 17       # Monotony P picture column (default Q)
        self.mono_n_pic_col = 18       # Monotony N picture column (default R)

        # MSO horizontal settings
        self.hor_mode = "AUTO"         # "AUTO" or "MANUAL"
        self.hor_scale = 0.01          # seconds/div
        self.hor_pos = 30              # percent

        # Trigger settings
        self.trig_channel = "CH1"      # CH1-CH4
        self.trig_edge = "RISE"        # RISE / FALL / BOTH
        self.trig_level = 0.5          # Volts

        # MSO channel position/scale (per channel)
        self.ch_pos = [-2.5, -3.5, -3.5, -3.5]
        self.ch_scale = [1.0, 1.0, 1.0, 1.0]

        # Label position (per channel)
        self.ch_label_x = [10, 10, 10, 10]
        self.ch_label_y = [40, 40, 40, 40]
        self._loaded_config = None       # sheet-aware config (set by import_config)
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

        # Log panel — captures all stdout/stderr output (plain text, fast)
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
        self.sheet_combo.installEventFilter(self)

        info_layout.addRow("Scope:", self.project_edit)
        info_layout.addRow("Sheet:", self.sheet_combo)

        self.test_type_combo = QComboBox()
        self.test_type_combo.addItems(["Sequence", "Monotony"])
        self.test_type_combo.installEventFilter(self)
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

            cb.toggled.connect(lambda checked, idx=i:
                self._on_ch_toggled(idx, checked))

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

        # Left column: checkboxes only
        left_save = QVBoxLayout()
        left_save.setSpacing(4)
        self.save_to_excel_cb = QCheckBox("Save to Excel")
        self.save_to_excel_cb.setChecked(False)
        self.save_to_excel_cb.toggled.connect(
            lambda en: self._on_save_to_excel_toggled(en))
        self.save_to_local_cb = QCheckBox("Save to Local")
        self.save_to_local_cb.setChecked(True)
        self.save_to_local_cb.toggled.connect(
            lambda en: self._on_save_to_local_toggled(en))
        self.save_to_scope_cb = QCheckBox("Save to Scope")
        self.save_to_scope_cb.setChecked(False)
        self.save_to_scope_cb.toggled.connect(
            lambda en: (self.project_edit.setEnabled(en),
                        self._on_save_to_scope_toggled(en)))
        left_save.addWidget(self.save_to_excel_cb)
        left_save.addWidget(self.save_to_local_cb)
        left_save.addWidget(self.save_to_scope_cb)

        # CH Label naming mode — no Excel, local only
        self.ch_label_naming_cb = QCheckBox("Use CH Label Naming")
        self.ch_label_naming_cb.setToolTip(
            "Save screenshot using CH label names instead of signal names.\n"
            "No Excel required. Forces Save to Local only.\n"
            "Multiple CHs: label1 TO label2.png  |  Single CH: label.png")
        self.ch_label_naming_cb.toggled.connect(self._on_ch_label_naming_toggled)
        left_save.addWidget(self.ch_label_naming_cb)
        left_save.addStretch()
        save_cols.addLayout(left_save)

        # Single vertical separator (full height)
        vline = QFrame()
        vline.setFrameShape(QFrame.Shape.VLine)
        vline.setStyleSheet("QFrame { color: #E5E5E7; }")
        save_cols.addWidget(vline)

        # Right column: Save Pic + Save Data + Save Pic+Data
        right_save = QVBoxLayout()
        right_save.setSpacing(4)
        self.save_pic_btn = QPushButton("📸 Save Pic")
        self.save_pic_btn.setMinimumWidth(140)
        self.save_pic_btn.setToolTip("Capture screenshot from oscilloscope")
        self.save_pic_btn.clicked.connect(lambda: self.save_pic_clicked.emit())
        right_save.addWidget(self.save_pic_btn)
        self.save_data_btn = QPushButton("📊 Save Data")
        self.save_data_btn.setMinimumWidth(140)
        self.save_data_btn.setToolTip("Read measurements from oscilloscope, write to Excel")
        self.save_data_btn.clicked.connect(lambda: self.save_data_clicked.emit())
        right_save.addWidget(self.save_data_btn)
        self.save_both_btn = QPushButton("📸📊 Save Pic + Data")
        self.save_both_btn.setMinimumWidth(140)
        self.save_both_btn.setToolTip("Screenshot + measurement data")
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
        self.log_view.verticalScrollBar().setValue(
            self.log_view.verticalScrollBar().maximum())

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
            log.debug('ConfigPanel', f'_on_file_path_changed: {abs_path}')

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
            log.debug('ConfigPanel', f'Loaded {len(sheet_names)} sheets (Excel connected)')

        except Exception as e:
            log.debug('ConfigPanel', f'Error loading sheet names: {e}')
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
        log.debug('ConfigPanel', f'_on_sheet_selected called with: {sheet_name}')
        log.debug('ConfigPanel', f'Current state.sheet_name: {self.state.sheet_name}')
        log.debug('ConfigPanel', f'Excel object available: {self.state.xls is not None}')

        if sheet_name and sheet_name != self.state.sheet_name:
            from dialogs.sheet_selection_dialog import SheetSelectionDialog
            dialog = SheetSelectionDialog([sheet_name], self)
            log.debug('ConfigPanel', f'Dialog created, waiting for user selection...')

            if dialog.exec() == SheetSelectionDialog.Accepted:
                selected = dialog.selected_sheet
                log.debug('ConfigPanel', f'Dialog accepted, selected sheet: {selected}')
                self.state.sheet_name = selected
                self.state.set_status(f"Sheet selected: {selected}")
                self._raise_gui()
                # Apply saved config for this sheet before reading signals
                # (so that init_row and signal R:/C: are correct)
                self._apply_sheet_config(selected)
                self._read_initial_signals()
                log.debug('ConfigPanel', f'State updated, signal should be emitted')
            else:
                log.debug('ConfigPanel', f'Dialog cancelled, resetting to: {self.state.sheet_name}')
                # Reset to previous selection
                self.sheet_combo.setCurrentText(self.state.sheet_name)
        else:
            log.debug('ConfigPanel', f'Sheet not selected or same as current, skipping')

    def _browse_excel(self):
        """Open file dialog for Excel selection."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel Test Report",
            "", "Excel files (*.xlsx *.xls)"
        )
        if file_path:
            # Drop reference to previous Excel WITHOUT closing it.
            # The user may still be reviewing the old workbook.
            if hasattr(self.state, 'xls') and self.state.xls:
                log.debug('ConfigPanel', 'Releasing previous Excel reference (window stays open)')
                self.state.xls = None

            # Reset coordinates to defaults for the new workbook
            self._reset_coordinates_to_defaults()

            # Set file path - this triggers _on_file_path_changed which
            # creates/attaches the Excel instance and loads sheets
            self.state.file_path = file_path
            log.debug('ConfigPanel', f'Excel path selected: {file_path}')

    def _browse_pic(self):
        """Open directory dialog for picture save location."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Picture Save Folder", ""
        )
        if dir_path:
            self.state.pic_path = dir_path
            log.debug('ConfigPanel', f'Picture path selected: {dir_path}')

    # ── Signal reading from Excel ──────────────────────────────────────


    def _raise_gui(self):
        """Bring GUI to foreground above Excel."""
        w = self.window()
        if w:
            w.raise_()
            w.activateWindow()

    def _read_initial_signals(self):
        """Read enabled signals from Excel using configured R:/C: and set state.

        Afterwards, syncs CH label edits to match the signal values so the
        display is consistent immediately (no need for a Last/Next round-trip).
        """
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
            log.debug('ConfigPanel', f"Initial signals read from sheet '{sheet}'")
        except Exception as e:
            log.debug('ConfigPanel', f'Error reading initial signals: {e}')

        # Sync CH label edits and state to follow the just-read signal values
        for i in range(4):
            if self.ch_enables[i].isChecked():
                sig_val = getattr(self.state, f'signal{i + 1}', '')
                self.ch_edits[i].setText(sig_val)
                setattr(self.state, f'ch{i + 1}_label', sig_val)

    # Stored separately from UI
    init_row = 8

    def _reset_coordinates_to_defaults(self):
        """Reset all row/column coordinates to factory defaults.

        Called when importing a new Excel workbook so stale coordinates
        from the previous workbook don't carry over.
        """
        # Data columns
        self.data_col = 7
        self.seq_data_en = True
        self.mono_p_cols = [9, 10, 11, 12]
        self.mono_p_data_en = [True, True, True, True]
        self.mono_n_cols = [13, 14, 15, 16]
        self.mono_n_data_en = [True, True, True, True]
        # Rise / Fall time (Monotony only, default disabled)
        self.rise_col = 1; self.fall_col = 2
        self.rise_en = False; self.fall_en = False
        # Picture columns
        self.seq_pic_col = 9
        self.mono_p_pic_col = 17
        self.mono_n_pic_col = 18
        # MSO
        self.hor_mode = "AUTO"
        self.hor_scale = 0.01
        self.hor_pos = 30
        self.trig_channel = "CH1"
        self.trig_edge = "RISE"
        self.trig_level = 0.5
        self.ch_pos = [-2.5, -3.5, -3.5, -3.5]
        self.ch_scale = [1.0, 1.0, 1.0, 1.0]
        self.ch_label_x = [10, 10, 10, 10]
        self.ch_label_y = [40, 40, 40, 40]
        # Checkboxes
        self.save_to_excel_cb.setChecked(False)
        self.save_to_local_cb.setChecked(True)
        self.save_to_scope_cb.setChecked(False)
        # Clear loaded config so stale per-sheet settings don't apply
        self._loaded_config = None
        # Reset test-type-specific settings (signal_cols, init_row, signal_rows, …)
        self._on_test_type_changed(self.test_type_combo.currentText())
        log.info('ConfigPanel', 'Coordinates reset to defaults for new workbook')

    def _on_test_type_changed(self, text):
        """Update defaults when test type changes."""
        is_monotony = text == 'Monotony'
        log.info('ConfigPanel', f'Test type: {text}')
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
        # CRITICAL order: setMinimum BEFORE setChecked.
        # setChecked fires _on_signal_toggled → setValue(state.row),
        # and if the old minimum was higher, Qt clamps the value up.
        for i in range(4):
            self.signal_rows[i].setMinimum(self.init_row)
            self.ch_enables[i].setChecked(ch_defaults[i])
            self.ch_edits[i].setEnabled(ch_defaults[i])
            if not ch_defaults[i]:
                self.ch_edits[i].clear()
        for i in range(4):
            self.signal_rows[i].setValue(self.init_row)
            self.signal_rows[i].setEnabled(sig_defaults[i])
            self.signal_enables[i].setChecked(sig_defaults[i])
        self.nav_bar.clamp_min(self.init_row)
        self.nav_bar.reset_jump(self.init_row)
        self._read_initial_signals()
        # Force CH label values to follow signal values after type switch
        for i in range(4):
            if ch_defaults[i]:
                sig_val = getattr(self.state, f'signal{i + 1}', '')
                self.ch_edits[i].setText(sig_val)
                setattr(self.state, f'ch{i + 1}_label', sig_val)

        # Re-apply saved per-(sheet, type) config on top of defaults
        if self.state.sheet_name:
            try:
                self._apply_sheet_config(self.state.sheet_name)
            except Exception as e:
                log.warning('ConfigPanel',
                    'Failed to apply saved config after type change: %s' % e)
        # Apply MSO config for the new test type
        if hasattr(self, '_loaded_config') and self._loaded_config:
            mso_sc = self._loaded_config.get(self._mso_key(self.state.test_type))
            if mso_sc:
                self._apply_mso_config(mso_sc)

    def _on_signal_toggled(self, idx):
        """Enable/disable signal: gray spinboxes, clear name when disabled."""
        en = self.signal_enables[idx].isChecked()
        self.signal_rows[idx].setEnabled(en)
        if not en:
            self.signal_edits[idx].clear()
            setattr(self.state, f'signal{idx + 1}', '')
            setattr(self.state, f'signal{idx + 1}_name', '')
            log.info('ConfigPanel', f'Sig{idx + 1} disabled')
        else:
            log.info('ConfigPanel', f'Sig{idx + 1} enabled')
            self.signal_rows[idx].blockSignals(True)
            self.signal_rows[idx].setValue(self.state.row)
            self.signal_rows[idx].blockSignals(False)
            self._on_signal_coord_changed(idx)

    def _on_ch_toggled(self, idx, checked):
        """Enable/disable channel label edit and log the change."""
        self.ch_edits[idx].setEnabled(checked)
        if checked:
            log.info('ConfigPanel', f'CH{idx + 1} enabled')
            sig_val = getattr(self.state, f'signal{idx + 1}', '')
            if sig_val:
                self.ch_edits[idx].setText(sig_val)
                setattr(self.state, f'ch{idx + 1}_label', sig_val)
        else:
            self.ch_edits[idx].clear()
            setattr(self.state, f'ch{idx + 1}_label', '')
            log.info('ConfigPanel', f'CH{idx + 1} disabled')

    def _on_save_to_excel_toggled(self, enabled):
        log.info('ConfigPanel', 'Save to Excel: %s' % ('ON' if enabled else 'OFF'))

    def _on_save_to_local_toggled(self, enabled):
        log.info('ConfigPanel', 'Save to Local: %s' % ('ON' if enabled else 'OFF'))

    def _on_save_to_scope_toggled(self, enabled):
        log.info('ConfigPanel', 'Save to Scope: %s' % ('ON' if enabled else 'OFF'))

    def _on_ch_label_naming_toggled(self, enabled):
        """CH Label naming mode: disable Excel/Scope, force Local on, disable Data."""
        log.info('ConfigPanel', 'CH Label Naming: %s' % ('ON' if enabled else 'OFF'))
        if enabled:
            # Save previous state so we can restore
            self._prev_excel = self.save_to_excel_cb.isChecked()
            self._prev_scope = self.save_to_scope_cb.isChecked()
            self._prev_local = self.save_to_local_cb.isChecked()
            # Force: no Excel, no Scope, Local only
            self.save_to_excel_cb.setChecked(False)
            self.save_to_excel_cb.setEnabled(False)
            self.save_to_scope_cb.setChecked(False)
            self.save_to_scope_cb.setEnabled(False)
            self.save_to_local_cb.setChecked(True)
            self.save_to_local_cb.setEnabled(False)
            self.project_edit.setEnabled(False)
            # Disable data buttons
            self.save_data_btn.setEnabled(False)
            self.save_both_btn.setEnabled(False)
        else:
            # Restore previous state (only if we have saved values; skip during initial load)
            if hasattr(self, '_prev_excel'):
                self.save_to_excel_cb.setEnabled(True)
                self.save_to_scope_cb.setEnabled(True)
                self.save_to_local_cb.setEnabled(True)
                self.save_to_excel_cb.setChecked(self._prev_excel)
                self.save_to_scope_cb.setChecked(self._prev_scope)
                self.save_to_local_cb.setChecked(self._prev_local)
                self.project_edit.setEnabled(self.save_to_scope_cb.isChecked())
                self.save_data_btn.setEnabled(True)
                self.save_both_btn.setEnabled(True)

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
            log.debug('ConfigPanel', f'Error reading cell R:{row} C:{col}: {e}')

    def eventFilter(self, obj, event):
        """Block wheel scroll on spinboxes and combos."""
        if event.type() == QEvent.Wheel:
            return True
        return super().eventFilter(obj, event)

    # ── Config import/export ───────────────────────────────────────────

    @staticmethod
    def _sheet_key(sheet_name, test_type=None):
        """Composite key: 'SheetName|type' so each (sheet, type) pair is separate."""
        t = test_type or 'sequence'
        return '%s|%s' % (sheet_name, t)

    @staticmethod
    def _mso_key(test_type):
        """Key for MSO settings — shared across all sheets, per test type."""
        return 'mso_%s' % (test_type or 'sequence')

    def _gather_mso_config(self):
        """Build a dict of MSO scope settings (per test type, not per sheet)."""
        return {
            "hor_mode": self.hor_mode,
            "hor_scale": self.hor_scale,
            "hor_pos": self.hor_pos,
            "trig_channel": self.trig_channel,
            "trig_edge": self.trig_edge,
            "trig_level": self.trig_level,
            "ch_pos": list(self.ch_pos),
            "ch_scale": list(self.ch_scale),
            "ch_label_x": list(self.ch_label_x),
            "ch_label_y": list(self.ch_label_y),
        }

    def _apply_mso_config(self, sc):
        """Apply MSO scope settings from a config dict."""
        if "hor_mode" in sc: self.hor_mode = sc["hor_mode"]
        if "hor_scale" in sc: self.hor_scale = sc["hor_scale"]
        if "hor_pos" in sc: self.hor_pos = sc["hor_pos"]
        if "trig_channel" in sc: self.trig_channel = sc["trig_channel"]
        if "trig_edge" in sc: self.trig_edge = sc["trig_edge"]
        if "trig_level" in sc: self.trig_level = sc["trig_level"]
        if "ch_pos" in sc: self.ch_pos = list(sc["ch_pos"])
        if "ch_scale" in sc: self.ch_scale = list(sc["ch_scale"])
        if "ch_label_x" in sc: self.ch_label_x = list(sc["ch_label_x"])
        if "ch_label_y" in sc: self.ch_label_y = list(sc["ch_label_y"])

    def _gather_sheet_config(self, sheet_name):
        """Build a dict of all per-(sheet, type) settings (no MSO — MSO is type-level)."""
        return {
            "test_type": self.state.test_type,
            "init_row": self.init_row,
            "signal_cols": list(self.signal_cols),
            "signals": [self.signal_enables[i].isChecked() for i in range(4)],
            "ch_enables": [self.ch_enables[i].isChecked() for i in range(4)],
            "data_col": self.data_col,
            "seq_data_en": self.seq_data_en,
            "mono_p_cols": list(self.mono_p_cols),
            "mono_p_data_en": list(self.mono_p_data_en),
            "mono_n_cols": list(self.mono_n_cols),
            "mono_n_data_en": list(self.mono_n_data_en),
            "rise_col": self.rise_col,
            "fall_col": self.fall_col,
            "rise_en": self.rise_en,
            "fall_en": self.fall_en,
            "seq_pic_col": self.seq_pic_col,
            "mono_p_pic_col": self.mono_p_pic_col,
            "mono_n_pic_col": self.mono_n_pic_col,
            "save_to_excel": self.save_to_excel_cb.isChecked(),
            "save_to_local": self.save_to_local_cb.isChecked(),
            "save_to_scope": self.save_to_scope_cb.isChecked(),
            "ch_label_naming": self.ch_label_naming_cb.isChecked(),
        }

    def _apply_sheet_config(self, sheet_name):
        """Apply saved config for the given sheet+type, if available."""
        if not hasattr(self, '_loaded_config') or not self._loaded_config:
            return
        sheets = self._loaded_config.get("sheets", {})
        key = self._sheet_key(sheet_name, self.state.test_type)
        sc = sheets.get(key)
        is_legacy = False
        if not sc:
            # Old-format key (sheet name only).  Only use it if the
            # saved test_type matches the current one — otherwise the
            # settings are for a different type and would be wrong.
            sc = sheets.get(sheet_name)
            if sc:
                saved_type = sc.get("test_type", "")
                if saved_type != self.state.test_type:
                    log.debug('ConfigPanel',
                        f"Legacy config for '{sheet_name}' is type "
                        f"'{saved_type}', skipping for '{self.state.test_type}'")
                    return
                is_legacy = True
        if not sc:
            log.debug('ConfigPanel', f"No saved config for '{key}'")
            return
        log.debug('ConfigPanel', f"Applying saved config for '{key}'"
                  + (' (legacy)' if is_legacy else ''))

        # Test type — only switch if it differs from current combo.
        if "test_type" in sc and not is_legacy:
            wanted = "Monotony" if sc["test_type"] == "monotony" else "Sequence"
            if self.test_type_combo.currentText() != wanted:
                self.test_type_combo.blockSignals(True)
                try:
                    self.test_type_combo.setCurrentText(wanted)
                finally:
                    self.test_type_combo.blockSignals(False)
                self._on_test_type_changed(wanted)

        # Init row — override with saved value (from Settings → Set Init Row)
        if "init_row" in sc:
            self.init_row = sc["init_row"]
            self.state.row = sc["init_row"]
            # Clamp signal R: spinboxes to >= init_row
            for rspin in self.signal_rows:
                rspin.setMinimum(sc["init_row"])
            # Sync nav_bar jump control
            self.nav_bar.clamp_min(sc["init_row"])
            self.nav_bar.reset_jump(sc["init_row"])

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
        if "seq_data_en" in sc:
            self.seq_data_en = sc["seq_data_en"]
        if "mono_p_cols" in sc:
            self.mono_p_cols = list(sc["mono_p_cols"])
        if "mono_p_data_en" in sc:
            self.mono_p_data_en = list(sc["mono_p_data_en"])
        if "mono_n_cols" in sc:
            self.mono_n_cols = list(sc["mono_n_cols"])
        if "mono_n_data_en" in sc:
            self.mono_n_data_en = list(sc["mono_n_data_en"])
        if "rise_col" in sc:
            self.rise_col = sc["rise_col"]
        if "fall_col" in sc:
            self.fall_col = sc["fall_col"]
        if "rise_en" in sc:
            self.rise_en = sc["rise_en"]
        if "fall_en" in sc:
            self.fall_en = sc["fall_en"]

        # Picture columns (from Settings → Set Picture Columns)
        if "seq_pic_col" in sc:
            self.seq_pic_col = sc["seq_pic_col"]
        if "mono_p_pic_col" in sc:
            self.mono_p_pic_col = sc["mono_p_pic_col"]
        if "mono_n_pic_col" in sc:
            self.mono_n_pic_col = sc["mono_n_pic_col"]

        # Save checkboxes
        if "save_to_excel" in sc:
            self.save_to_excel_cb.setChecked(sc["save_to_excel"])
        if "save_to_local" in sc:
            self.save_to_local_cb.setChecked(sc["save_to_local"])
        if "save_to_scope" in sc:
            self.save_to_scope_cb.setChecked(sc["save_to_scope"])
        if "ch_label_naming" in sc:
            self.ch_label_naming_cb.setChecked(sc["ch_label_naming"])

        # Re-read signals + sync CH labels after all coordinates are restored
        try:
            self._read_initial_signals()
        except Exception as e:
            log.warning('ConfigPanel',
                'Failed to read signals after config apply: %s' % e)

    def remember_current_sheet_config(self):
        """Save current sheet's config into loaded config memory (for accumulation).

        Call this after data is successfully saved to a sheet, so that the sheet's
        config is accumulated and will be included in the next export.
        """
        if self.ch_label_naming_cb.isChecked():
            return  # CH Label Naming mode — don't record settings
        sheet = self.state.sheet_name
        if not sheet:
            return
        if not hasattr(self, '_loaded_config') or self._loaded_config is None:
            self._loaded_config = {"sheets": {}}
        if "sheets" not in self._loaded_config:
            self._loaded_config["sheets"] = {}
        key = self._sheet_key(sheet, self.state.test_type)
        self._loaded_config["sheets"][key] = self._gather_sheet_config(sheet)
        log.debug('ConfigPanel', f"Remembered config for '{key}'")

    def export_config(self):
        """Export all accumulated sheet configs to a JSON file."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Config", "config.json", "JSON (*.json)")
        if not path:
            return
        if self.ch_label_naming_cb.isChecked():
            return  # CH Label Naming mode — don't export

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
        # Connection info (for session restore)
        if hasattr(self, '_connect_method'):
            cfg["connect_method"] = self._connect_method
        if hasattr(self, '_connect_ip'):
            cfg["connect_ip"] = self._connect_ip
        if hasattr(self, '_connect_port'):
            cfg["connect_port"] = self._connect_port
        if hasattr(self, '_connect_use_socket'):
            cfg["connect_use_socket"] = self._connect_use_socket

        # MSO settings — per test type, not per sheet
        cfg[self._mso_key(self.state.test_type)] = self._gather_mso_config()

        # Always include current sheet+type (in case it hasn't been remembered yet)
        current_sheet = self.state.sheet_name or "Sheet1"
        key = self._sheet_key(current_sheet, self.state.test_type)
        cfg["sheets"][key] = self._gather_sheet_config(current_sheet)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        sheet_names = list(cfg["sheets"].keys())
        log.debug('ConfigPanel', f'Config exported to {path} ({len(sheet_names)} entries: {sheet_names})')

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

            # Apply MSO config for current test type
            mso_sc = cfg.get(self._mso_key(self.state.test_type))
            if mso_sc:
                self._apply_mso_config(mso_sc)

            # Apply current sheet+type config immediately
            current_sheet = self.state.sheet_name
            if current_sheet:
                self._apply_sheet_config(current_sheet)
                # Force-refresh: re-apply current type defaults + saved config
                # to ensure nav_bar, signal_rows, CH labels are all synced
                self._on_test_type_changed(self.test_type_combo.currentText())

            # List loaded entries
            sheets = cfg.get("sheets", {})
            keys = list(sheets.keys())
            log.info('ConfigPanel', f'Config imported from {path} ({len(sheets)} entries: {keys})')

        except Exception as e:
            log.debug('ConfigPanel', f'Error importing config: {e}')

    def _silent_export(self, path: str):
        """Export config to path without file dialog (for auto-save)."""
        if self.ch_label_naming_cb.isChecked():
            return  # CH Label Naming mode — don't auto-save
        cfg = {}
        if hasattr(self, '_loaded_config') and self._loaded_config:
            cfg = self._loaded_config
        if "sheets" not in cfg:
            cfg["sheets"] = {}
        # Global
        cfg["project_name"] = self.state.project_name
        cfg["excel_path"] = self.state.file_path
        cfg["pic_path"] = self.state.pic_path
        if hasattr(self, '_connect_method'):
            cfg["connect_method"] = self._connect_method
        if hasattr(self, '_connect_ip'):
            cfg["connect_ip"] = self._connect_ip
        if hasattr(self, '_connect_port'):
            cfg["connect_port"] = self._connect_port
        if hasattr(self, '_connect_use_socket'):
            cfg["connect_use_socket"] = self._connect_use_socket
        # MSO per test type
        cfg[self._mso_key(self.state.test_type)] = self._gather_mso_config()
        # Current sheet
        current_sheet = self.state.sheet_name or "Sheet1"
        key = self._sheet_key(current_sheet, self.state.test_type)
        cfg["sheets"][key] = self._gather_sheet_config(current_sheet)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.debug('ConfigPanel', f'Auto-save config failed: {e}')

    def _silent_import(self, path: str):
        """Import config from path without file dialog (for auto-load)."""
        if not os.path.exists(path):
            return False
        try:
            with open(path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            self._loaded_config = cfg
            self._config_file_path = path
            if cfg.get("project_name"):
                self.state.project_name = cfg["project_name"]
            if cfg.get("excel_path"):
                self.state.file_path = cfg["excel_path"]
            if cfg.get("pic_path"):
                self.state.pic_path = cfg["pic_path"]
            # Restore connection info
            if cfg.get("connect_method"):
                self._connect_method = cfg["connect_method"]
            if cfg.get("connect_ip"):
                self._connect_ip = cfg["connect_ip"]
            if cfg.get("connect_port"):
                self._connect_port = cfg["connect_port"]
            if cfg.get("connect_use_socket", None) is not None:
                self._connect_use_socket = cfg["connect_use_socket"]
            # Apply MSO config for current test type
            mso_sc = cfg.get(self._mso_key(self.state.test_type))
            if mso_sc:
                self._apply_mso_config(mso_sc)
            # Apply current sheet
            current_sheet = self.state.sheet_name
            if current_sheet:
                self._apply_sheet_config(current_sheet)
                self._on_test_type_changed(self.test_type_combo.currentText())
            log.info('ConfigPanel', f'Auto-loaded config from {path}')
            return True
        except Exception as e:
            log.debug('ConfigPanel', f'Auto-load config failed: {e}')
            return False