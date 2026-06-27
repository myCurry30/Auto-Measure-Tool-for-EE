"""Simplified test management — flag_test_items removed, uses test_type."""


def go(file_path, state):
    """Initialize test state. No flag-specific logic — signals read from user R:/C:."""
    xls = state.get('xls')
    sheet_name = state.get('sheet_name', 'Sheet1')
    if xls and sheet_name:
        try:
            xls.activate_sheet(sheet_name)
        except Exception:
            pass

    # Reset to init_row
    init_row = state.get('init_row', 8)
    row = init_row
    if 'row' in state:
        row = state.get('row', init_row)

    # Signal names are read by config_panel via user's R:/C: — no override needed
    state['row'] = row
    state['current_item'] = int(row - init_row + 1)
    state['excel_row'] = int(row)
    state['pn_direction'] = ''
    state['flag_monotony_direction'] = state.get('flag_monotony_direction', 1)
    print(f"[test_manager] go: row={row}, type={state.get('test_type', 'sequence')}")


def Last(state):
    """Go to previous row."""
    init_row = state.get('init_row', 8)
    row = state.get('row', init_row)

    if row > init_row:
        row -= 1

    is_monotony = state.get('test_type', 'sequence') == 'monotony'
    if is_monotony:
        direction = state.get('flag_monotony_direction', 1)
        if direction == 1:
            state['pn_direction'] = 'P'
        else:
            state['pn_direction'] = 'P'
            direction = 1
        state['flag_monotony_direction'] = direction

    state['row'] = row
    state['current_item'] = int(row - init_row + 1)
    state['excel_row'] = int(row)
    print(f"[test_manager] Last: row={row}")


def Next(state):
    """Go to next row."""
    row = state.get('row', 8)
    row += 1

    is_monotony = state.get('test_type', 'sequence') == 'monotony'
    if is_monotony:
        direction = state.get('flag_monotony_direction', 1)
        if direction == 1:
            direction = 0
            state['pn_direction'] = 'N'
        else:
            direction = 1
            state['pn_direction'] = 'P'
        state['flag_monotony_direction'] = direction

    state['row'] = row
    init_row = state.get('init_row', 8)
    state['current_item'] = int(row - init_row + 1)
    state['excel_row'] = int(row)
    print(f"[test_manager] Next: row={row}")


def jump(state, jump_target):
    """Jump to a specific test item."""
    init_row = state.get('init_row', 8)
    target = int(jump_target) if jump_target else init_row
    if target < init_row:
        target = init_row

    is_monotony = state.get('test_type', 'sequence') == 'monotony'
    if is_monotony:
        state['flag_monotony_direction'] = 1
        state['pn_direction'] = 'P'

    state['row'] = target
    state['current_item'] = int(target - init_row + 1)
    state['excel_row'] = int(target)
    print(f"[test_manager] Jump: target={target}, row={target}")
