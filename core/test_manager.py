"""Test management and signal navigation functions.

Contains go(), Last(), Next(), jump() functions that manage Excel data
and oscilloscope channel states.
"""
from .easy_excel import EasyExcel
from .capture import Capture_Pic


def go(file_path, state):
    """Initialize test by loading Excel and loading initial signal data.

    Args:
        file_path: Path to Excel test report
        state: Dictionary containing:
            - m: Current row index (will be set to 8)
            - xls: EasyExcel instance (should already be open from GUI)
            - flag_test_items: Test item type
            - signal1_name: CH1 signal name (will be set)
            - signal2_name: CH2 signal name (will be set)
            - signal3_name: CH3 signal name (will be set)
            - tests_sum: Total tests (will be set)
            - flag_monotony_direction: Monotony direction (will be set for item 10)
            - osc: Oscilloscope instance (optional, for channel control)
    """
    m = 8

    # 使用传入的Excel对象，而不是重新创建
    xls = state.get('xls')
    if not xls:
        # 如果没有传入Excel对象，才创建新的（作为后备）
        print("[TestManager] No existing Excel instance, creating new one")
        xls = EasyExcel(file_path)
    else:
        print("[TestManager] Using existing Excel instance")

    # Activate the selected sheet
    sheet_name = state.get('sheet_name', 'Sheet1')
    xls.activate_sheet(sheet_name)

    signal1_name = ''
    signal2_name = ''
    signal3_name = ''
    flag_monotony_direction = state.get('flag_monotony_direction', 1)

    # Determine flag_test_items from sheet name if not provided
    flag_test_items = state.get('flag_test_items', 0)
    if flag_test_items == 0 and state.get('sheet_name'):
        # Try to determine flag from sheet name pattern
        sheet_name = state['sheet_name']
        if "G3 to S0" in sheet_name:
            flag_test_items = 1
        elif "S0-S5-S0" in sheet_name:
            flag_test_items = 2
        elif "S0 GLO RST" in sheet_name:
            flag_test_items = 3
        elif "WARM RESET" in sheet_name:
            flag_test_items = 4
        elif "S5 GLO RST" in sheet_name:
            flag_test_items = 5
        elif "THERMTRIP" in sheet_name:
            flag_test_items = 6
        elif "LVT" in sheet_name:
            flag_test_items = 7
        elif "HW Strap" in sheet_name:
            flag_test_items = 8
        elif "PG&EN" in sheet_name:
            flag_test_items = 9
        elif "Monotony" in sheet_name:
            flag_test_items = 10
        elif "S5 to G3" in sheet_name:
            flag_test_items = 12
        else:
            # Default to 0 if no pattern matches
            flag_test_items = 0

    state['flag_test_items'] = flag_test_items

    if flag_test_items == 8:
        signal1_name = str(xls.getCell(state['sheet_name'], 7, 2))
        signal2_name = str(xls.getCell(state['sheet_name'], 7, 3))
        signal3_name = ''
    elif flag_test_items == 9:
        signal1_name = str(xls.getCell(state['sheet_name'], 2, 1))
        signal2_name = str(xls.getCell(state['sheet_name'], 2, 2))
        signal3_name = str(xls.getCell(state['sheet_name'], 2, 3))
    elif flag_test_items == 10:
        signal1_name = str(xls.getCell(state['sheet_name'], 21, 2))
        signal2_name = ''
        signal3_name = ''
        flag_monotony_direction = 1
    else:
        signal1_name = str(xls.getCell(state['sheet_name'], 8, 5))
        signal2_name = str(xls.getCell(state['sheet_name'], 8, 6))
        signal3_name = ''

    print(state.get('tests_sum', 999))
    print(signal1_name)
    print(signal2_name)

    # Update state
    state['m'] = m
    state['xls'] = xls
    state['signal1_name'] = signal1_name
    state['signal2_name'] = signal2_name
    state['signal3_name'] = signal3_name
    state['flag_monotony_direction'] = flag_monotony_direction

    # Calculate excel row for display
    if flag_test_items == 8:
        excel_row = int(m - 1)
    elif flag_test_items == 9:
        excel_row = int(m - 6)
    elif flag_test_items == 10:
        excel_row = int(m + 13)
    else:
        excel_row = int(m)

    state['excel_row'] = excel_row
    state['current_item'] = int(m - 7)


def Last(state):
    """Navigate to previous signal, reading from Excel and updating oscilloscope channels.

    Args:
        state: Dictionary with all test state variables
    """
    i = 0
    state['pn_direction'] = ''
    m = state.get('m', 8)

    if m <= 8:
        m = 8
    else:
        m = m - 1

    print('m2', m)

    flag_test_items = state.get('flag_test_items', 0)

    # Read signal names from Excel
    if flag_test_items == 8:
        signal1_name = str(state['xls'].getCell(state['sheet_name'], m - 1, 2))
        signal2_name = str(state['xls'].getCell(state['sheet_name'], m - 1, 3))
        while signal1_name == "None":
            i = i + 1
            signal1_name = str(state['xls'].getCell(state['sheet_name'], m - i - 1, 2))
        while signal2_name == "None":
            i = i + 1
            signal2_name = str(state['xls'].getCell(state['sheet_name'], m - i - 1, 3))

    elif flag_test_items == 9:
        signal1_name = str(state['xls'].getCell(state['sheet_name'], m - 6, 1))
        signal2_name = str(state['xls'].getCell(state['sheet_name'], m - 6, 2))
        signal3_name = str(state['xls'].getCell(state['sheet_name'], m - 6, 3))

    elif flag_test_items == 10:
        flag_monotony_direction = state.get('flag_monotony_direction', 1)
        if flag_monotony_direction == 1:
            state['pn_direction'] = 'N'
            flag_monotony_direction = 0
            if state.get('mso5'):
                state['osc'].trigger('NORMAL', 'CH1', 'FALL', 0.5)
        elif flag_monotony_direction == 0:
            if m > 8:
                m = m + 1
            print('m3', m)
            state['pn_direction'] = 'P'
            flag_monotony_direction = 1
            if state.get('mso5'):
                state['osc'].trigger('NORMAL', 'CH1', 'RISE', 0.5)
        signal1_name = str(state['xls'].getCell(state['sheet_name'], m + 13, 2))
        signal2_name = ''
        signal3_name = ''

    else:
        signal1_name = str(state['xls'].getCell(state['sheet_name'], m, 5))
        signal2_name = str(state['xls'].getCell(state['sheet_name'], m, 6))
        while signal1_name == "None":
            i = i + 1
            signal1_name = str(state['xls'].getCell(state['sheet_name'], m - i, 5))
        while signal2_name == "None":
            i = i + 1
            signal2_name = str(state['xls'].getCell(state['sheet_name'], m - i, 6))

    # Update oscilloscope channels
    if flag_test_items != 10:
        if signal1_name == signal2_name:
            signal2_name = "None"

        if state.get('flag_mso_connect'):
            osc = state['osc']
            if signal1_name == 'None':
                osc.write('SELECT:CH1 OFF')
            else:
                osc.write('SELECT:CH1 ON')
            if signal2_name == 'None':
                osc.write('SELECT:CH2 OFF')
            else:
                osc.write('SELECT:CH2 ON')
            if flag_test_items == 9:
                if signal3_name == 'None':
                    osc.write('SELECT:CH3 OFF')
                else:
                    osc.write('SELECT:CH3 ON')

    # Update state
    state['m'] = m
    state['flag_monotony_direction'] = flag_monotony_direction
    state['signal1_name'] = signal1_name
    state['signal2_name'] = signal2_name
    state['signal3_name'] = signal3_name
    state['current_item'] = int(m - 7)

    # Calculate excel row for display
    if flag_test_items == 8:
        excel_row = int(m - 1)
    elif flag_test_items == 9:
        excel_row = int(m - 6)
    elif flag_test_items == 10:
        excel_row = int(m + 13)
    else:
        excel_row = int(m)
    state['excel_row'] = excel_row


def Next(state):
    """Navigate to next signal, reading from Excel and updating oscilloscope channels.

    Args:
        state: Dictionary with all test state variables
    """
    i = 0
    state['pn_direction'] = ''
    m = state.get('m', 8)

    m = m + 1

    flag_test_items = state.get('flag_test_items', 0)

    # Read signal names from Excel
    if flag_test_items == 8:
        signal1_name = str(state['xls'].getCell(state['sheet_name'], m - 1, 2))
        signal2_name = str(state['xls'].getCell(state['sheet_name'], m - 1, 3))
        while signal1_name == "None":
            i = i + 1
            signal1_name = str(state['xls'].getCell(state['sheet_name'], m - i - 1, 2))
        while signal2_name == "None":
            i = i + 1
            signal2_name = str(state['xls'].getCell(state['sheet_name'], m - i - 1, 3))

    elif flag_test_items == 9:
        signal1_name = str(state['xls'].getCell(state['sheet_name'], m - 6, 1))
        signal2_name = str(state['xls'].getCell(state['sheet_name'], m - 6, 2))
        signal3_name = str(state['xls'].getCell(state['sheet_name'], m - 6, 3))

    elif flag_test_items == 10:
        flag_monotony_direction = state.get('flag_monotony_direction', 1)
        if flag_monotony_direction == 1:
            m = m - 1
            state['pn_direction'] = 'N'
            flag_monotony_direction = 0
            if state.get('mso5'):
                state['osc'].trigger('NORMAL', 'CH1', 'FALL', 0.5)
        elif flag_monotony_direction == 0:
            state['pn_direction'] = 'P'
            flag_monotony_direction = 1
            if state.get('mso5'):
                state['osc'].trigger('NORMAL', 'CH1', 'RISE', 0.5)
        signal1_name = str(state['xls'].getCell(state['sheet_name'], m + 13, 2))
        signal2_name = ''
        signal3_name = ''

    else:
        signal1_name = str(state['xls'].getCell(state['sheet_name'], m, 5))
        signal2_name = str(state['xls'].getCell(state['sheet_name'], m, 6))
        while signal1_name == "None":
            i = i + 1
            signal1_name = str(state['xls'].getCell(state['sheet_name'], m - i, 5))
        while signal2_name == "None":
            i = i + 1
            signal2_name = str(state['xls'].getCell(state['sheet_name'], m - i, 6))

    # Update oscilloscope channels
    if flag_test_items != 10:
        if signal1_name == signal2_name:
            signal2_name = "None"

        if state.get('flag_mso_connect'):
            osc = state['osc']
            if signal1_name == 'None':
                osc.write('SELECT:CH1 OFF')
            else:
                osc.write('SELECT:CH1 ON')
            if signal2_name == 'None':
                osc.write('SELECT:CH2 OFF')
            else:
                osc.write('SELECT:CH2 ON')
            if flag_test_items == 9:
                if signal3_name == 'None':
                    osc.write('SELECT:CH3 OFF')
                else:
                    osc.write('SELECT:CH3 ON')

    # Update state
    state['m'] = m
    state['flag_monotony_direction'] = flag_monotony_direction
    state['signal1_name'] = signal1_name
    state['signal2_name'] = signal2_name
    state['signal3_name'] = signal3_name
    state['current_item'] = int(m - 7)

    # Calculate excel row for display
    if flag_test_items == 8:
        excel_row = int(m - 1)
    elif flag_test_items == 9:
        excel_row = int(m - 6)
    elif flag_test_items == 10:
        excel_row = int(m + 13)
    else:
        excel_row = int(m)
    state['excel_row'] = excel_row


def jump(state, jump_target):
    """Jump to specific test item.

    Args:
        state: Dictionary with all test state variables
        jump_target: Target row number to jump to
    """
    i = 0
    state['pn_direction'] = ''
    flag_test_items = state.get('flag_test_items', 0)

    # Convert jump_target to m based on test item type
    if flag_test_items == 8:
        m = int(jump_target) + 1
    elif flag_test_items == 9:
        m = int(jump_target) + 6
    elif flag_test_items == 10:
        m = int(jump_target) - 13
    else:
        m = int(jump_target)

    print('m1', m)

    if m <= 8:
        m = 8

    # Read signal names from Excel
    if flag_test_items == 8:
        signal1_name = str(state['xls'].getCell(state['sheet_name'], m - 1, 2))
        signal2_name = str(state['xls'].getCell(state['sheet_name'], m - 1, 3))
        while signal1_name == "None":
            i = i + 1
            signal1_name = str(state['xls'].getCell(state['sheet_name'], m - i - 1, 2))
        while signal2_name == "None":
            i = i + 1
            signal2_name = str(state['xls'].getCell(state['sheet_name'], m - i - 1, 3))

    elif flag_test_items == 9:
        signal1_name = str(state['xls'].getCell(state['sheet_name'], m - 6, 1))
        signal2_name = str(state['xls'].getCell(state['sheet_name'], m - 6, 2))
        signal3_name = str(state['xls'].getCell(state['sheet_name'], m - 6, 3))

    elif flag_test_items == 10:
        signal1_name = str(state['xls'].getCell(state['sheet_name'], m + 13, 2))
        signal2_name = ''
        signal3_name = ''
        state['pn_direction'] = 'P'
        flag_monotony_direction = 1
        if state.get('mso5'):
            state['osc'].trigger('NORMAL', 'CH1', 'RISE', 0.5)

    else:
        signal1_name = str(state['xls'].getCell(state['sheet_name'], m, 5))
        signal2_name = str(state['xls'].getCell(state['sheet_name'], m, 6))
        while signal1_name == "None":
            i = i + 1
            signal1_name = str(state['xls'].getCell(state['sheet_name'], m - i, 5))
        while signal2_name == "None":
            i = i + 1
            signal2_name = str(state['xls'].getCell(state['sheet_name'], m - i, 6))

    print('m2', m)

    # Update oscilloscope channels
    if flag_test_items != 10:
        if signal1_name == signal2_name:
            signal2_name = "None"

        if state.get('flag_mso_connect'):
            osc = state['osc']
            if signal1_name == 'None':
                osc.write('SELECT:CH1 OFF')
            else:
                osc.write('SELECT:CH1 ON')
            if signal2_name == 'None':
                osc.write('SELECT:CH2 OFF')
            else:
                osc.write('SELECT:CH2 ON')
            if flag_test_items == 9:
                if signal3_name == 'None':
                    osc.write('SELECT:CH3 OFF')
                else:
                    osc.write('SELECT:CH3 ON')

    # Update state
    state['m'] = m
    state['flag_monotony_direction'] = flag_monotony_direction
    state['signal1_name'] = signal1_name
    state['signal2_name'] = signal2_name
    state['signal3_name'] = signal3_name
    state['current_item'] = int(m - 7)

    # Calculate excel row for display
    if flag_test_items == 8:
        excel_row = int(m - 1)
    elif flag_test_items == 9:
        excel_row = int(m - 6)
    elif flag_test_items == 10:
        excel_row = int(m + 13)
    else:
        excel_row = int(m)
    state['excel_row'] = excel_row