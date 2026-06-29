"""Capture and image export functions.

Contains Capture_Pic, savepic, and mkdir functions.
"""
import os
import re
import time


def mkdir(path):
    """Create directory if it does not exist.

    Args:
        path: Directory path

    Returns:
        True if created, False if already exists
    """
    path = path.strip()
    path = path.rstrip("\\")
    is_exists = os.path.exists(path)
    if not is_exists:
        os.makedirs(path)
        print(path + ' 创建成功')
        return True
    else:
        print(path + ' 目录已存在')
        return False


def savepic(osc, pic_path, sheet_name, signals, signal_enables,
           project_name, test_type, flag_monotony_direction):
    """Save screenshot from oscilloscope to local disk.

    Args:
        osc: Oscilloscope instance
        pic_path: Base path for saving pictures
        sheet_name: Current sheet name (creates subdirectory)
        signals: List of signal names [signal1, signal2, signal3, signal4]
        signal_enables: List of bools indicating active channels [ch1, ch2, ch3, ch4]
        project_name: Project name (for oscilloscope directory)
        test_type: Test item type ("sequence" or "monotony")
        flag_monotony_direction: 1=Positive/Rise, 0=Negative/Fall (for monotony)

    Returns:
        Local file path of saved screenshot
    """
    mkpath = '%s/%s' % (pic_path, sheet_name)
    print("-->", mkpath)
    mkdir(mkpath)

    signal1 = signals[0] if len(signals) > 0 else ""
    signal2 = signals[1] if len(signals) > 1 else ""
    signal3 = signals[2] if len(signals) > 2 else ""

    if test_type != "monotony":
        # Build name from active signals
        active = []
        for sig, en in zip(signals, signal_enables):
            if en and sig:
                active.append(sig)
        name = ' TO '.join(active) if active else 'screenshot'
    else:
        if flag_monotony_direction == 1:
            name = '%s_R' % (signal1)
        else:
            name = '%s_F' % (signal1)

    file_path = r'%s/%s.PNG' % (mkpath, name)
    # Build scope base path from project_name:
    #   "TH_V2"          → C:\TH_V2                 (default C:)
    #   "D:\MyProject"   → D:\MyProject              (user-specified drive)
    if re.match(r'^[a-zA-Z]:[\\/]', project_name):
        scope_base = project_name.rstrip('\\/')
    else:
        scope_base = 'C:\\%s' % project_name
    scope_dir = '%s\\%s' % (scope_base, sheet_name)
    # export() appends ".PNG" itself → pass path WITHOUT extension
    scope_path_no_ext = '%s\\%s' % (scope_dir, name)
    scope_path_with_ext = '%s.PNG' % scope_path_no_ext
    osc.makeDir(scope_base)
    osc.makeDir(scope_dir)
    osc.export('PNG', scope_path_no_ext)               # → SAV:IMAG "path.PNG"
    time.sleep(1.5)
    osc.readfile(scope_path_with_ext.replace('\\', '/'))  # → read "path.PNG"
    time.sleep(0.5)
    data = osc.readraw(file_path)
    time.sleep(0.5)
    return data


def Capture_Pic(osc, xls, sheet_name, signals, signal_enables,
                test_type, flag_monotony_direction, m, mso5,
                pic_path, project_name,
                save_pic=True, save_data=False,
                save_to_excel=False, save_to_scope=False,
                data_col=7, mono_p_cols=None, mono_n_cols=None,
                pic_cols=None):
    """Capture screenshot, insert into Excel, and/or write measurements.

    Args:
        ...
        data_col: Excel column for Sequence DELAY data (default 7=G)
        mono_p_cols: [TOP,BASE,MAX,MIN] columns for Monotony P (default [9,10,11,12])
        mono_n_cols: [TOP,BASE,MAX,MIN] columns for Monotony N (default [13,14,15,16])

    Returns:
        Tuple of (delay_time, value_top, value_base, value_max, value_min)
    """
    if mono_p_cols is None:
        mono_p_cols = [9, 10, 11, 12]
    if mono_n_cols is None:
        mono_n_cols = [13, 14, 15, 16]
    # Extract individual signal names for convenience in measurement naming
    signal1 = signals[0] if len(signals) > 0 else ""
    signal2 = signals[1] if len(signals) > 1 else ""
    signal3 = signals[2] if len(signals) > 2 else ""

    pic_file_path = None

    # --- Step 1: Save screenshot picture ---
    if save_pic:
        pic_file_path = r'%s' % (savepic(
            osc, pic_path, sheet_name, signals, signal_enables,
            project_name, test_type, flag_monotony_direction))
        pic_file_path = os.path.abspath(pic_file_path)

        # Insert picture into Excel if requested
        if save_to_excel and xls:
            xls.addPicture(sheet_name, pic_file_path, m, 0, 0, 0, 0,
                          test_type, flag_monotony_direction, pic_cols)

    # --- Step 2: Write measurement data to Excel ---
    delay_time = None
    value_top = value_base = value_max = value_min = None

    if save_data and xls:
        xls.save()

        if test_type != "monotony":
            # Find which MEASurement slot is DELAY (not hardcoded to MEAS7)
            delay_meas_num = None
            for n in range(1, 21):  # scan MEAS1~MEAS20
                try:
                    meas_type = osc.query('MEASUrement:MEAS%d:TYPE?' % n)
                    if meas_type and 'DELAY' in meas_type.upper():
                        delay_meas_num = n
                        print('Found DELAY at MEAS%d' % n)
                        break
                except Exception:
                    continue
            if delay_meas_num is None:
                print('[Capture_Pic] WARNING: no DELAY measurement found on oscilloscope')
                delay_time = ''
            else:
                delay_time_raw = osc.query('MEASUrement:MEAS%d:MAX?' % delay_meas_num)
                print('query delaytime:', delay_time_raw)
                if delay_time_raw.find('MEASUREMENT') != -1:
                    if mso5:
                        delay_time_raw = delay_time_raw[26:]
                delay_time_value = eval(delay_time_raw)
                delay_time_value = float(delay_time_value)
                print('result delaytime:', delay_time_value)

                if abs(delay_time_value) >= 1:
                    delay_time_value = '%.2f' % delay_time_value
                    delay_time = str(delay_time_value) + 's'
                elif abs(delay_time_value) < 1 and abs(delay_time_value) >= 0.001:
                    delay_time_value = float(delay_time_value) * 1000
                    delay_time_value = '%.2f' % delay_time_value
                    delay_time = str(delay_time_value) + 'ms'
                elif abs(delay_time_value) < 0.001 and abs(delay_time_value) >= 0.000001:
                    delay_time_value = float(delay_time_value) * 1000000
                    delay_time_value = '%.2f' % delay_time_value
                    delay_time = str(delay_time_value) + 'μs'
                else:
                    delay_time_value = float(delay_time_value) * 1000000000
                    delay_time_value = '%.2f' % delay_time_value
                    delay_time = str(delay_time_value) + 'ns'

            xls.setCell(sheet_name, m, data_col, delay_time)
            col_letter = chr(64 + data_col) if data_col <= 26 else 'col%d' % data_col
            print('[Capture_Pic] SaveData: DELAY → %s%d = %s' % (col_letter, m, delay_time or '(none)'))

        if test_type == "monotony":
            # Scan MEAS1~MEAS20 for TOP, BASE, MAX, MIN types
            meas_map = {}  # type_name → meas_num
            for n in range(1, 21):
                try:
                    meas_type = osc.query('MEASUrement:MEAS%d:TYPE?' % n)
                    if meas_type:
                        t = meas_type.strip().upper()
                        if t == 'TOP' and 'TOP' not in meas_map:
                            meas_map['TOP'] = n
                        elif t == 'BASE' and 'BASE' not in meas_map:
                            meas_map['BASE'] = n
                        elif t == 'MAXIMUM' and 'MAX' not in meas_map:
                            meas_map['MAX'] = n
                        elif t == 'MINIMUM' and 'MIN' not in meas_map:
                            meas_map['MIN'] = n
                except Exception:
                    continue
            missing = [k for k in ['TOP', 'BASE', 'MAX', 'MIN'] if k not in meas_map]
            if missing:
                print('[Capture_Pic] WARNING: missing measurement types: %s' % ', '.join(missing))

            def _query_meas(meas_num, label):
                raw = osc.query('MEASUrement:MEAS%d:MAX?' % meas_num)
                print('query Value_%s:' % label, raw)
                if raw.find('MEASUREMENT') != -1:
                    if mso5:
                        raw = raw[26:]
                return '%.4f' % float(eval(raw))

            value_top = _query_meas(meas_map['TOP'], 'TOP') if 'TOP' in meas_map else ''
            value_base = _query_meas(meas_map['BASE'], 'BASE') if 'BASE' in meas_map else ''
            value_max = _query_meas(meas_map['MAX'], 'MAX') if 'MAX' in meas_map else ''
            value_min = _query_meas(meas_map['MIN'], 'MIN') if 'MIN' in meas_map else ''

            cols = mono_p_cols if flag_monotony_direction == 1 else mono_n_cols
            dir_label = 'P' if flag_monotony_direction == 1 else 'N'
            xls.setCell(sheet_name, m, cols[0], value_top)
            xls.setCell(sheet_name, m, cols[1], value_base)
            xls.setCell(sheet_name, m, cols[2], value_max)
            xls.setCell(sheet_name, m, cols[3], value_min)
            print('[Capture_Pic] SaveData %s: TOP→col%d=%sV  BASE→col%d=%sV  MAX→col%d=%sV  MIN→col%d=%sV' %
                  (dir_label, cols[0], value_top or '(none)',
                   cols[1], value_base or '(none)',
                   cols[2], value_max or '(none)',
                   cols[3], value_min or '(none)'))

        xls.save()

    return delay_time, value_top, value_base, value_max, value_min
