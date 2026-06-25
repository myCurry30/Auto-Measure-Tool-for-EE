"""Configuration panel with macOS-style cards for all settings."""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                                QPushButton, QSpinBox, QFormLayout, QGraphicsDropShadowEffect, QComboBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor


class ConfigCard(QWidget):
    """A rounded card widget with shadow effect."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("configCard")
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

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 15))  # alpha=15/255 ≈ 0.06
        self.setGraphicsEffect(shadow)


class ConfigPanel(QWidget):
    """Main configuration panel with all cards."""

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # File Paths Card
        self.file_card = ConfigCard("File Paths")
        file_layout = QFormLayout()
        file_layout.setContentsMargins(0, 8, 0, 0)
        file_layout.setLabelAlignment(Qt.AlignLeft)
        file_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.excel_edit = QLineEdit()
        self.excel_edit.setReadOnly(True)
        self.excel_edit.setPlaceholderText("Select Excel report...")
        self.excel_browse = QPushButton("Browse")
        self.excel_browse.setObjectName("secondary")
        self.excel_browse.clicked.connect(self._browse_excel)

        self.pic_edit = QLineEdit()
        self.pic_edit.setReadOnly(True)
        self.pic_edit.setPlaceholderText("Select save folder...")
        self.pic_browse = QPushButton("Browse")
        self.pic_browse.setObjectName("secondary")
        self.pic_browse.clicked.connect(self._browse_pic)

        file_layout.addRow("Excel Report:", self._create_path_row(self.excel_edit, self.excel_browse))
        file_layout.addRow("Save Pictures:", self._create_path_row(self.pic_edit, self.pic_browse))
        self.file_card.content_layout.addLayout(file_layout)
        layout.addWidget(self.file_card)

        # Project Info Card
        self.info_card = ConfigCard("Project Info")
        info_layout = QFormLayout()
        info_layout.setContentsMargins(0, 8, 0, 0)

        self.project_edit = QLineEdit()
        self.project_edit.setPlaceholderText("Project name...")
        self.sheet_combo = QComboBox()
        self.sheet_combo.setPlaceholderText("Select sheet...")
        self.tests_sum_edit = QLineEdit()
        self.tests_sum_edit.setReadOnly(True)
        self.current_item_edit = QLineEdit()
        self.current_item_edit.setReadOnly(True)

        info_layout.addRow("Project Name:", self.project_edit)
        info_layout.addRow("Sheet Name:", self.sheet_combo)
        info_layout.addRow("Tests Sum:", self.tests_sum_edit)
        info_layout.addRow("Current Item:", self.current_item_edit)
        self.info_card.content_layout.addLayout(info_layout)
        layout.addWidget(self.info_card)

        # Signal Display Card
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
        layout.addWidget(self.signal_card)

        # Channel Labels Card
        self.label_card = ConfigCard("Channel Labels")
        label_layout = QFormLayout()
        label_layout.setContentsMargins(0, 8, 0, 0)

        self.ch1_edit = QLineEdit()
        self.ch1_edit.setPlaceholderText("CH1 label...")
        self.pn_badge = QLabel("P")
        self.pn_badge.setFixedSize(24, 24)
        self.pn_badge.setAlignment(Qt.AlignCenter)
        self.pn_badge.setStyleSheet("""
            QLabel {
                background-color: #007AFF;
                color: white;
                border-radius: 12px;
                font-weight: 600;
                font-size: 11px;
            }
        """)

        self.ch2_edit = QLineEdit()
        self.ch2_edit.setPlaceholderText("CH2 label...")
        self.ch3_edit = QLineEdit()
        self.ch3_edit.setPlaceholderText("CH3 label...")

        ch1_row = QWidget()
        ch1_layout = QHBoxLayout(ch1_row)
        ch1_layout.setContentsMargins(0, 0, 0, 0)
        ch1_layout.addWidget(self.ch1_edit, 1)
        ch1_layout.addWidget(self.pn_badge)
        ch1_layout.addSpacing(8)

        label_layout.addRow("CH1 Label:", ch1_row)
        label_layout.addRow("CH2 Label:", self.ch2_edit)
        label_layout.addRow("CH3 Label:", self.ch3_edit)
        self.label_card.content_layout.addLayout(label_layout)
        layout.addWidget(self.label_card)

        # Add spacer
        layout.addStretch()

    def _create_path_row(self, line_edit, button):
        """Create a row with line edit and browse button."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(line_edit, 1)
        layout.addWidget(button)
        return widget

    def connect_signals(self):
        """Connect state signals to UI updates."""
        # GUI reads state
        self.state.file_path_changed.connect(self._on_file_path_changed)
        self.state.pic_path_changed.connect(self.pic_edit.setText)
        self.state.sheet_name_changed.connect(self.sheet_combo.setCurrentText)
        self.state.tests_sum_changed.connect(self.tests_sum_edit.setText)
        self.state.signal1_changed.connect(self.signal1_edit.setText)
        self.state.signal2_changed.connect(self.signal2_edit.setText)
        self.state.signal3_changed.connect(self.signal3_edit.setText)
        self.state.current_item_changed.connect(self.current_item_edit.setText)
        self.state.project_name_changed.connect(self.project_edit.setText)
        self.state.pn_direction_changed.connect(self._update_pn_badge)

        # GUI writes to state (two-way binding)
        self.project_edit.textChanged.connect(lambda t: setattr(self.state, 'project_name', t))
        self.sheet_combo.currentTextChanged.connect(self._on_sheet_selected)
        self.ch1_edit.textChanged.connect(lambda t: setattr(self.state, 'ch1_label', t))
        self.ch2_edit.textChanged.connect(lambda t: setattr(self.state, 'ch2_label', t))
        self.ch3_edit.textChanged.connect(lambda t: setattr(self.state, 'ch3_label', t))

    def _on_file_path_changed(self, file_path):
        """Handle file path change by loading sheet names into QComboBox.

        This is the SINGLE place where Excel is created when a file is selected.
        _browse_excel() just sets the file path and this handler does the rest.
        """
        if not file_path:
            return

        try:
            from core import EasyExcel
            import os
            abs_file_path = os.path.abspath(file_path)
            print(f"[ConfigPanel] _on_file_path_changed: {abs_file_path}")

            # Close any existing Excel before opening new one
            if hasattr(self.state, 'xls') and self.state.xls:
                try:
                    print("[ConfigPanel] Closing previous Excel instance...")
                    old_xls = self.state.xls
                    self.state.xls = None
                    old_xls.close()
                except Exception as e:
                    print(f"[ConfigPanel] Error closing previous Excel: {e}")
                    self.state.xls = None

            # 创建Excel对象并保持打开状态
            xls = EasyExcel(abs_file_path)

            # 加载工作表名称
            sheet_names = xls.get_sheet_names()
            self.sheet_combo.blockSignals(True)  # 阻止combo信号触发对话框
            self.sheet_combo.clear()
            self.sheet_combo.addItems(sheet_names)
            self.sheet_combo.setPlaceholderText("Select sheet...")
            self.sheet_combo.blockSignals(False)

            # 将Excel对象保存到state中，保持打开状态
            self.state.xls = xls
            print(f"[ConfigPanel] Loaded {len(sheet_names)} sheets, Excel kept open")

        except Exception as e:
            print(f"[ConfigPanel] Error loading sheet names: {e}")
            self.sheet_combo.clear()
            self.sheet_combo.setPlaceholderText("Error loading sheets")
            # 确保清理
            if hasattr(self.state, 'xls') and self.state.xls:
                try:
                    self.state.xls.close()
                    self.state.xls = None
                except:
                    pass

    def _update_pn_badge(self, direction):
        """Update P/N direction badge."""
        self.pn_badge.setText(direction or "P")
        if direction == "N":
            self.pn_badge.setStyleSheet("""
                QLabel {
                    background-color: #FF3B30;
                    color: white;
                    border-radius: 12px;
                    font-weight: 600;
                    font-size: 11px;
                }
            """)
        else:
            self.pn_badge.setStyleSheet("""
                QLabel {
                    background-color: #007AFF;
                    color: white;
                    border-radius: 12px;
                    font-weight: 600;
                    font-size: 11px;
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
                print(f"[ConfigPanel] State updated, signal should be emitted")
            else:
                print(f"[ConfigPanel] Dialog cancelled, resetting to: {self.state.sheet_name}")
                # Reset to previous selection
                self.sheet_combo.setCurrentText(self.state.sheet_name)
        else:
            print(f"[ConfigPanel] Sheet not selected or same as current, skipping")

    def _browse_excel(self):
        """Open file dialog for Excel selection.

        Only sets the file path - Excel creation is handled by
        _on_file_path_changed signal handler to avoid duplicates.
        """
        from PySide6.QtWidgets import QFileDialog
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
        from PySide6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Picture Save Folder",
            ""
        )
        if dir_path:
            self.state.pic_path = dir_path
            print(f"[ConfigPanel] Picture path selected: {dir_path}")