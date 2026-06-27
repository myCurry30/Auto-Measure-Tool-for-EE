"""Application state management.

Provides AppState class that replaces all global variables with a
single source of truth using Qt signals for GUI updates.
"""
from PySide6.QtCore import QObject, Signal


class AppState(QObject):
    """Single source of truth for application state.

    GUI reads from this class properties; core logic writes to them.
    Changes are signaled via Qt signals for GUI updates.
    """

    # GUI-bound signals
    file_path_changed = Signal(str)
    pic_path_changed = Signal(str)
    sheet_name_changed = Signal(str)
    tests_sum_changed = Signal(int)
    signal1_changed = Signal(str)
    signal2_changed = Signal(str)
    signal3_changed = Signal(str)
    signal4_changed = Signal(str)
    ch1_label_changed = Signal(str)
    ch2_label_changed = Signal(str)
    ch3_label_changed = Signal(str)
    ch4_label_changed = Signal(str)
    current_item_changed = Signal(int)
    project_name_changed = Signal(str)
    jump_target_changed = Signal(int)
    pn_direction_changed = Signal(str)
    connection_changed = Signal(bool)
    status_message_changed = Signal(str)
    excel_row_changed = Signal(int)

    def __init__(self):
        super().__init__()
        # GUI-bound properties
        self._file_path = ""
        self._pic_path = ""
        self._sheet_name = ""
        self._tests_sum = 0
        self._signal1 = ""
        self._signal2 = ""
        self._signal3 = ""
        self._signal4 = ""
        self._ch1_label = ""
        self._ch2_label = ""
        self._ch3_label = ""
        self._ch4_label = ""
        self._current_item = 0
        self._project_name = ""
        self._jump_target = 0
        self._pn_direction = ""
        self._excel_row = 0

        # Internal state (not bound to GUI)
        self.test_type = "sequence"  # "sequence" or "monotony"
        self.row = 8  # current Excel row number
        self.n = 6
        self.flag_mso_connect = False
        self.flag_monotony_direction = 1
        self.mso5 = False
        self.dpo7000 = False
        self.dpo5104b = False
        self.osc = None
        self.rm = None
        self.xls = None
        self.tests_sum = 0  # no limit
        self.sheet_summary = "Summary"
        self.signal1_name = ""
        self.signal2_name = ""
        self.signal3_name = ""
        self.signal4_name = ""

    # Properties with signal emission
    @property
    def file_path(self):
        return self._file_path

    @file_path.setter
    def file_path(self, v):
        if self._file_path != v:
            self._file_path = v
            self.file_path_changed.emit(v)
            print(f"[AppState] file_path changed: {v}")

    @property
    def pic_path(self):
        return self._pic_path

    @pic_path.setter
    def pic_path(self, v):
        if self._pic_path != v:
            self._pic_path = v
            self.pic_path_changed.emit(v)
            print(f"[AppState] pic_path changed: {v}")

    @property
    def sheet_name(self):
        return self._sheet_name

    @sheet_name.setter
    def sheet_name(self, v):
        if self._sheet_name != v:
            self._sheet_name = v
            self.sheet_name_changed.emit(v)
            print(f"[AppState] sheet_name changed: {v}")

    @property
    def tests_sum(self):
        return self._tests_sum

    @tests_sum.setter
    def tests_sum(self, v):
        if self._tests_sum != v:
            self._tests_sum = v
            self.tests_sum_changed.emit(v)
            print(f"[AppState] tests_sum changed: {v}")

    @property
    def signal1(self):
        return self._signal1

    @signal1.setter
    def signal1(self, v):
        if self._signal1 != v:
            self._signal1 = v
            self.signal1_changed.emit(v)
            if v:
                print(f"[AppState] signal1 changed: {v}")

    @property
    def signal2(self):
        return self._signal2

    @signal2.setter
    def signal2(self, v):
        if self._signal2 != v:
            self._signal2 = v
            self.signal2_changed.emit(v)
            if v:
                print(f"[AppState] signal2 changed: {v}")

    @property
    def signal3(self):
        return self._signal3

    @signal3.setter
    def signal3(self, v):
        if self._signal3 != v:
            self._signal3 = v
            self.signal3_changed.emit(v)
            if v:
                print(f"[AppState] signal3 changed: {v}")

    @property
    def signal4(self):
        return self._signal4

    @signal4.setter
    def signal4(self, v):
        if self._signal4 != v:
            self._signal4 = v
            self.signal4_changed.emit(v)
            if v:
                print(f"[AppState] signal4 changed: {v}")

    @property
    def ch1_label(self):
        return self._ch1_label

    @ch1_label.setter
    def ch1_label(self, v):
        if self._ch1_label != v:
            self._ch1_label = v
            self.ch1_label_changed.emit(v)
            print(f"[AppState] ch1_label changed: {v}")

    @property
    def ch2_label(self):
        return self._ch2_label

    @ch2_label.setter
    def ch2_label(self, v):
        if self._ch2_label != v:
            self._ch2_label = v
            self.ch2_label_changed.emit(v)
            print(f"[AppState] ch2_label changed: {v}")

    @property
    def ch3_label(self):
        return self._ch3_label

    @ch3_label.setter
    def ch3_label(self, v):
        if self._ch3_label != v:
            self._ch3_label = v
            self.ch3_label_changed.emit(v)
            print(f"[AppState] ch3_label changed: {v}")

    @property
    def ch4_label(self):
        return self._ch4_label

    @ch4_label.setter
    def ch4_label(self, v):
        if self._ch4_label != v:
            self._ch4_label = v
            self.ch4_label_changed.emit(v)
            print(f"[AppState] ch4_label changed: {v}")

    @property
    def current_item(self):
        return self._current_item

    @current_item.setter
    def current_item(self, v):
        if self._current_item != v:
            self._current_item = v
            self.current_item_changed.emit(v)
            print(f"[AppState] current_item changed: {v}")

    @property
    def project_name(self):
        return self._project_name

    @project_name.setter
    def project_name(self, v):
        if self._project_name != v:
            self._project_name = v
            self.project_name_changed.emit(v)
            print(f"[AppState] project_name changed: {v}")

    @property
    def jump_target(self):
        return self._jump_target

    @jump_target.setter
    def jump_target(self, v):
        if self._jump_target != v:
            self._jump_target = v
            self.jump_target_changed.emit(v)
            print(f"[AppState] jump_target changed: {v}")

    @property
    def pn_direction(self):
        return self._pn_direction

    @pn_direction.setter
    def pn_direction(self, v):
        if self._pn_direction != v:
            self._pn_direction = v
            self.pn_direction_changed.emit(v)
            print(f"[AppState] pn_direction changed: {v}")

    @property
    def excel_row(self):
        return self._excel_row

    @excel_row.setter
    def excel_row(self, v):
        if self._excel_row != v:
            self._excel_row = v
            self.excel_row_changed.emit(v)
            print(f"[AppState] excel_row changed: {v}")

    def set_connection(self, connected):
        """Set connection state and emit signal."""
        self.flag_mso_connect = connected
        self.connection_changed.emit(connected)
        print(f"[AppState] connection changed: {connected}")

    def set_status(self, message):
        """Set status bar message."""
        self.status_message_changed.emit(message)
        print(f"[AppState] status: {message}")

    def get_state_dict(self):
        """Return a dictionary of state for core logic functions.

        This provides a read-only view of state for core functions
        that need to access multiple state variables.
        """
        return {
            'sheet_name': self._sheet_name,
            'test_type': self.test_type,
            'flag_monotony_direction': self.flag_monotony_direction,
            'flag_mso_connect': self.flag_mso_connect,
            'mso5': self.mso5,
            'osc': self.osc,
            'xls': self.xls,
            'row': self.row,
            'signal1_name': self.signal1_name,
            'signal2_name': self.signal2_name,
            'signal3_name': self.signal3_name,
            'signal4_name': self.signal4_name,
        }