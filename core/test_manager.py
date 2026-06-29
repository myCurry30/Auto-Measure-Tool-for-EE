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
    """Go to previous item.

    Sequence: row -= 1
    Monotony: N→P (same row) → P→row-1→N (prev row)
    """
    init_row = state.get('init_row', 8)
    row = state.get('row', init_row)
    is_monotony = state.get('test_type', 'sequence') == 'monotony'

    if is_monotony:
        direction = state.get('flag_monotony_direction', 1)
        if direction == 0:
            # N → P: same row, flip direction
            direction = 1
            state['pn_direction'] = 'P'
            # row unchanged
        else:
            # P → row-1 → N: decrement row, flip direction
            if row > init_row:
                row -= 1
            direction = 0
            state['pn_direction'] = 'N'
        state['flag_monotony_direction'] = direction
    else:
        if row > init_row:
            row -= 1

    state['row'] = row
    state['current_item'] = int(row - init_row + 1)
    state['excel_row'] = int(row)
    print(f"[test_manager] Last: row={row}, dir={state.get('flag_monotony_direction', '')}")


def Next(state):
    """Go to next item.

    Sequence: row += 1
    Monotony: P→N (same row) → N→row+1→P (next row)
    """
    row = state.get('row', 8)
    init_row = state.get('init_row', 8)
    is_monotony = state.get('test_type', 'sequence') == 'monotony'

    if is_monotony:
        direction = state.get('flag_monotony_direction', 1)
        if direction == 1:
            # P → N: same row, flip direction
            direction = 0
            state['pn_direction'] = 'N'
            # row unchanged
        else:
            # N → row+1 → P: increment row, flip direction
            row += 1
            direction = 1
            state['pn_direction'] = 'P'
        state['flag_monotony_direction'] = direction
    else:
        row += 1

    state['row'] = row
    state['current_item'] = int(row - init_row + 1)
    state['excel_row'] = int(row)
    print(f"[test_manager] Next: row={row}, dir={state.get('flag_monotony_direction', '')}")


def jump(state, jump_target):
    """Jump to a specific test item.

    Sequence: jump to target row.
    Monotony: jump to target row, direction = P.
    """
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
    print(f"[test_manager] Jump: target={target}, row={target}, dir={state.get('flag_monotony_direction', '')}")
