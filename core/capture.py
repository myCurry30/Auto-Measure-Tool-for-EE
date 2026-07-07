"""Capture and image export functions.

Contains Capture_Pic, savepic, and mkdir functions.
"""
import os
import time
from .logger import log
import re


def _pulse():
    """Let the GUI event loop breathe during long operations.

    Set by the app layer (main_window) to QApplication.processEvents.
    A no-op when capture is used headless or during testing.
    """
    pass


def _ascii_safe(s: str) -> str:
    """Replace non-ASCII characters so the scope filesystem can handle the path."""
    return s.encode('ascii', errors='replace').decode('ascii').replace('?', '_')


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
        log.info('Capture', f'{path} 创建成功')
        return True
    else:
        log.debug('Capture', f'{path} 目录已存在')
        return False


def savepic(osc, pic_path, sheet_name, signals, signal_enables,
           project_name, test_type, flag_monotony_direction,
           save_to_scope=False, save_to_local=True,
           use_ch_labels=False, ch_labels=None, ch_enables=None):
    """Capture a screenshot from the oscilloscope and save it locally.

    The Tektronix VISA protocol requires SAV:IMAG + FILESYSTEM:READFILE
    to transfer a screenshot — a scope-disk file is unavoidable during
    transfer.  This function gives you two modes:

        save_to_scope=False  → temp file on scope → transfer → delete from scope
        save_to_scope=True   → project path on scope → transfer → keep on scope

    Args:
        ...
        save_to_scope: If True, keep the file on the scope disk after transfer
        save_to_local: If True, save the PNG file to the local pic_path

    Returns:
        Local file path of saved screenshot (or None if save_to_local=False)
    """
    if use_ch_labels:
        # CH Label mode: save directly under pic_path, no sheet subfolder
        mkpath = pic_path
    else:
        mkpath = '%s/%s' % (pic_path, sheet_name)
    log.debug('Capture', f'Save path: {mkpath}')
    mkdir(mkpath)

    signal1 = signals[0] if len(signals) > 0 else ""
    signal2 = signals[1] if len(signals) > 1 else ""
    signal3 = signals[2] if len(signals) > 2 else ""

    if use_ch_labels and ch_labels is not None and ch_enables is not None:
        # CH Label naming mode: use channel labels instead of signal names
        active = []
        for lbl, en in zip(ch_labels, ch_enables):
            if en and lbl:
                active.append(lbl)
        if active:
            name = ' TO '.join(active)
        else:
            name = 'screenshot'
        # Monotony: append _R / _F suffix
        if test_type == "monotony":
            if flag_monotony_direction == 1:
                name = '%s_R' % name
            else:
                name = '%s_F' % name
    elif test_type != "monotony":
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

    # ── Build scope path ─────────────────────────────────────────────
    if save_to_scope:
        # User wants organised project dirs on scope
        if re.match(r'^[a-zA-Z]:[\\/]', project_name):
            scope_base = _ascii_safe(project_name.rstrip('\\/'))
        else:
            scope_base = 'C:\\%s' % _ascii_safe(project_name)
        scope_dir = '%s\\%s' % (scope_base, _ascii_safe(sheet_name))
        scope_path_no_ext = '%s\\%s' % (scope_dir, _ascii_safe(name))
        osc.makeDir(scope_base)
        osc.makeDir(scope_dir)
    else:
        # Temp directory — cleaned up after transfer
        scope_base = 'C:\\tmp_autotool'
        scope_dir = scope_base
        scope_path_no_ext = '%s\\_cap' % scope_base
        osc.makeDir(scope_base)

    scope_path_with_ext = '%s.PNG' % scope_path_no_ext

    # ── Transfer ─────────────────────────────────────────────────────
    # Temporarily extend timeout for file operations (can be slow)
    old_timeout = osc.osc.timeout
    osc.osc.timeout = 30000  # 30s for file transfers
    try:
        osc.export('PNG', scope_path_no_ext)                # → SAV:IMAG
        _pulse(); time.sleep(0.3); _pulse()
        osc.readfile(scope_path_with_ext.replace('\\', '/')) # → FILESYSTEM:READFILE
        _pulse(); time.sleep(0.2); _pulse()
        data = osc.readraw(file_path) if save_to_local else None  # → read_raw()
        _pulse(); time.sleep(0.1); _pulse()
    finally:
        osc.osc.timeout = old_timeout

    # ── Clean up temp file if user didn't request scope save ─────────
    if not save_to_scope:
        try:
            osc.delete_file(scope_path_with_ext)
            log.debug('Capture', 'Deleted temp scope file: %s' % scope_path_with_ext)
        except Exception as e:
            log.debug('Capture', 'Could not delete temp scope file: %s' % e)

    return data


def Capture_Pic(osc, xls, sheet_name, signals, signal_enables,
                test_type, flag_monotony_direction, m, mso5,
                pic_path, project_name,
                save_pic=True, save_data=False,
                save_to_excel=False, save_to_scope=False,
                save_to_local=True,
                data_col=7, mono_p_cols=None, mono_n_cols=None,
                pic_cols=None, ch_enables=None,
                seq_data_en=True, mono_p_data_en=None, mono_n_data_en=None,
                use_ch_labels=False, ch_labels=None,
                rise_col=1, fall_col=2, rise_en=False, fall_en=False):
    """Capture screenshot, insert into Excel, and/or write measurements.

    Args:
        ...
        data_col: Excel column for Sequence DELAY data (default 7=G)
        mono_p_cols: [TOP,BASE,MAX,MIN] columns for Monotony P (default [9,10,11,12])
        mono_n_cols: [TOP,BASE,MAX,MIN] columns for Monotony N (default [13,14,15,16])
        ch_enables: Optional list[bool] of enabled CH1-4 channels.
        seq_data_en: Enable Sequence DELAY data write
        mono_p_data_en: [TOP,BASE,MAX,MIN] enable flags for Monotony P
        mono_n_data_en: [TOP,BASE,MAX,MIN] enable flags for Monotony N

    Returns:
        Tuple of (delay_time, value_top, value_base, value_max, value_min)
    """
    if ch_enables is None:
        ch_enables = [True, True, True, True]
    if mono_p_cols is None:
        mono_p_cols = [9, 10, 11, 12]
    if mono_n_cols is None:
        mono_n_cols = [13, 14, 15, 16]
    if mono_p_data_en is None:
        mono_p_data_en = [True, True, True, True]
    if mono_n_data_en is None:
        mono_n_data_en = [True, True, True, True]
    # Extract individual signal names for convenience in measurement naming
    signal1 = signals[0] if len(signals) > 0 else ""
    signal2 = signals[1] if len(signals) > 1 else ""
    signal3 = signals[2] if len(signals) > 2 else ""

    pic_file_path = None

    # --- Step 1: Save screenshot picture ---
    if save_pic:
        log.info('Capture', '[Pic] Starting screenshot capture (to_local=%s, to_excel=%s)' % (
            save_to_local, save_to_excel))
        need_local = save_to_local or (save_to_excel and bool(xls))
        try:
            pic_file_path = savepic(
                osc, pic_path, sheet_name, signals, signal_enables,
                project_name, test_type, flag_monotony_direction,
                save_to_scope=save_to_scope,
                save_to_local=need_local,
                use_ch_labels=use_ch_labels,
                ch_labels=ch_labels,
                ch_enables=ch_enables)
            if pic_file_path:
                log.success('Capture', '[Pic] Screenshot saved: %s' % pic_file_path)
            else:
                log.info('Capture', '[Pic] Screenshot saved to scope only (not local)')
        except Exception as e:
            log.error('Capture', '[Pic] Screenshot FAILED: %s' % e)
            raise

        pic_is_temp = False
        if pic_file_path:
            pic_file_path = os.path.abspath(pic_file_path)
            if not save_to_local:
                pic_is_temp = True

        if save_to_excel and xls and pic_file_path:
            try:
                xls.addPicture(sheet_name, pic_file_path, m, 0, 0, 0, 0,
                              test_type, flag_monotony_direction, pic_cols)
                log.success('Capture', '[Pic] Inserted into Excel at row %d' % m)
            except Exception as e:
                log.error('Capture', '[Pic] Excel insert FAILED at row %d: %s' % (m, e))
                raise

        if pic_is_temp and pic_file_path:
            try:
                os.remove(pic_file_path)
                log.debug('Capture', 'Deleted temp image: %s' % pic_file_path)
                pic_file_path = None
            except Exception as e:
                log.debug('Capture', 'Could not delete temp image: %s' % e)

    # --- Step 2: Write measurement data to Excel ---
    delay_time = None
    value_top = value_base = value_max = value_min = None

    if save_data and xls:
        log.info('Capture', '[Data] Starting data read from scope (type=%s)' % test_type)
        xls.save()
        _pulse()

        if test_type != "monotony":
            if not seq_data_en:
                log.info('Capture', '[Data] Sequence DELAY disabled, skipping')
                delay_time = ''
            else:
                try:
                    source = osc.query('MEASUrement:MEAS5:SOUrce1?')
                    log.info('Capture', '[Data] MEAS5 (DELAY) source=%s' % source)
                    # 3-round consistency check
                    def _read_delay():
                        raw = osc.query('MEASUrement:MEAS5:MEAN?')
                        if raw.find('MEASUREMENT') != -1 and mso5:
                            raw = raw.split()[-1]
                        return float(eval(raw))
                    delay_time_value = None
                    for rd in range(1, 4):
                        try:
                            vals = [_read_delay() for _ in range(3)]
                            log.info('Capture', '[Data] DELAY round %d: %s' % (rd, vals))
                            if vals[0] == vals[1] == vals[2]:
                                delay_time_value = vals[0]
                                break
                            delay_time_value = vals[-1]
                        except Exception as e:
                            log.error('Capture', '[Data] DELAY query FAILED: %s' % e)
                            break
                    if delay_time_value is None:
                        delay_time_raw = None
                        delay_time_value = 0.0
                    else:
                        delay_time_raw = str(delay_time_value)
                except Exception as e:
                    log.error('Capture', '[Data] MEAS5 (DELAY) query FAILED: %s' % e)
                    delay_time_raw = None

                if not delay_time_raw:
                    delay_time = ''
                else:
                    log.debug('Capture', f'Query delaytime: {delay_time_raw}')
                    delay_time_value = float(delay_time_value)
                    log.debug('Capture', f'Result delaytime: {delay_time_value}')

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

                if seq_data_en:
                    xls.setCell(sheet_name, m, data_col, delay_time)

        if test_type == "monotony":
            # DEBUG: query all results at once
            try:
                all_results = osc.query('MEASUrement?')
                log.info('Capture', '[DEBUG] MEASUrement? = %s' % all_results.strip())
            except Exception:
                pass

            # Monotony: query known MEAS names directly — no LIST?/TYPE? needed.
            # measure_monotony creates: MEAS1=TOP, MEAS2=BASE,
            # MEAS3=MAX, MEAS4=MIN, MEAS5=RISETIME, MEAS6=FALLTIME
            ch_names = ['CH1', 'CH2', 'CH3', 'CH4']
            meas_map = {}  # type_name → measurement_name

            for name, expected_type in [('MEAS1', 'TOP'), ('MEAS2', 'BASE'),
                                         ('MEAS3', 'MAX'), ('MEAS4', 'MIN'),
                                         ('MEAS5', 'RISE'), ('MEAS6', 'FALL')]:
                try:
                    source = osc.query('MEASUrement:%s:SOUrce1?' % name)
                    source_upper = source.strip().upper() if source else ''
                    log.info('Capture', '%s → SOURCE1=%s' % (name, source_upper))

                    # Check if this measurement's channel is enabled
                    ch_idx = None
                    for i, cn in enumerate(ch_names):
                        if cn in source_upper:
                            ch_idx = i
                            break
                    if ch_idx is not None and not ch_enables[ch_idx]:
                        log.debug('Capture',
                            '%s (%s) skipped — %s disabled' % (name, expected_type, ch_names[ch_idx]))
                        continue

                    meas_map[expected_type] = name
                except Exception as e:
                    log.warning('Capture', '%s → query error: %s' % (name, e))

            missing = [k for k in ['TOP', 'BASE', 'MAX', 'MIN'] if k not in meas_map]
            if missing:
                log.warning('Capture', 'Missing measurement types: %s' % ', '.join(missing))

            # Active enable flags: P or N based on direction
            en_flags = mono_p_data_en if flag_monotony_direction == 1 else mono_n_data_en
            type_to_idx = {'TOP': 0, 'BASE': 1, 'MAX': 2, 'MIN': 3}

            def _query_meas(meas_name, label):
                """Query with 3-round consistency check."""
                def _read_one(suffix=':MEAN?'):
                    raw = osc.query('MEASUrement:%s%s' % (meas_name, suffix))
                    if raw.find('MEASUREMENT') != -1 and mso5:
                        raw = raw.split()[-1]
                    return float(eval(raw))

                # DEBUG: query all 4 variants for comparison
                try:
                    v1 = _read_one(':MEAN?')
                    v2 = _read_one(':RESUlts:CURRentacq:MEAN?')
                    v3 = _read_one(':CCRESUlts:CURRentacq:MEAN?')
                    v4 = _read_one(':ALLAcqs:MEAN?')
                    log.info('Capture', '[DEBUG] %s(%s) MEAN=%.6f  CURRentacq=%.6f  CCRESUlts=%.6f  ALLAcqs=%.6f' % (
                        label, meas_name, v1, v2, v3, v4))
                except Exception as e:
                    log.warning('Capture', '[DEBUG] %s debug query failed: %s' % (label, e))

                # Main: 3-round consistency using :MEAN?
                best_val = ''
                for round_num in range(1, 4):
                    try:
                        vals = ['%.4f' % _read_one() for _ in range(3)]
                        log.info('Capture', '[Data] Query %s(%s) round %d: %s' % (
                            label, meas_name, round_num, vals))
                        if vals[0] == vals[1] == vals[2]:
                            log.success('Capture', '[Data] %s = %s (consistent, round %d)' % (
                                label, vals[0], round_num))
                            return vals[0]
                        best_val = vals[-1]
                        log.warning('Capture', '[Data] %s inconsistent round %d, retrying' % (
                            label, round_num))
                    except Exception as e:
                        log.error('Capture', '[Data] %s query FAILED round %d: %s' % (
                            label, round_num, e))
                        return ''
                log.warning('Capture', '[Data] %s using last value after 3 rounds: %s' % (
                    label, best_val))
                return best_val

            def _maybe_query(meas_type, fallback):
                """Query measurement value if enabled and available."""
                if meas_type not in meas_map:
                    return ''
                idx = type_to_idx.get(meas_type, -1)
                if idx >= 0 and not en_flags[idx]:
                    log.info('Capture', '[Data] %s disabled, skipping' % meas_type)
                    return ''
                return _query_meas(meas_map[meas_type], meas_type)

            value_top = _maybe_query('TOP', '')
            value_base = _maybe_query('BASE', '')
            value_max = _maybe_query('MAX', '')
            value_min = _maybe_query('MIN', '')

            # Rise time → P direction only; Fall time → N direction only
            value_rise = ''
            value_fall = ''
            if flag_monotony_direction == 1:  # P
                if rise_en and 'RISE' in meas_map:
                    value_rise = _query_meas(meas_map['RISE'], 'RISE')
            else:  # N
                if fall_en and 'FALL' in meas_map:
                    value_fall = _query_meas(meas_map['FALL'], 'FALL')

            cols = mono_p_cols if flag_monotony_direction == 1 else mono_n_cols
            dir_label = 'P' if flag_monotony_direction == 1 else 'N'
            # Only write enabled items to Excel
            for col_idx, (val, label, en_idx) in enumerate([
                    (value_top, 'TOP', 0), (value_base, 'BASE', 1),
                    (value_max, 'MAX', 2), (value_min, 'MIN', 3)]):
                if en_flags[en_idx]:
                    xls.setCell(sheet_name, m, cols[col_idx], val)
            # Rise / Fall time — direction-specific
            if flag_monotony_direction == 1 and rise_en and value_rise:
                xls.setCell(sheet_name, m, rise_col, value_rise)
            elif flag_monotony_direction == 0 and fall_en and value_fall:
                xls.setCell(sheet_name, m, fall_col, value_fall)
        xls.save()
        _pulse()          # restore GUI BEFORE log output

        # Log success AFTER GUI is responsive again
        if test_type != "monotony":
            col_letter = chr(64 + data_col) if data_col <= 26 else 'col%d' % data_col
            log.success('Capture', 'SaveData: DELAY → %s%d = %s' % (col_letter, m, delay_time or '(none)'))
        else:
            log.success('Capture', 'SaveData %s: TOP→col%d=%sV  BASE→col%d=%sV  MAX→col%d=%sV  MIN→col%d=%sV' %
                  (dir_label, cols[0], value_top or '(none)',
                   cols[1], value_base or '(none)',
                   cols[2], value_max or '(none)',
                   cols[3], value_min or '(none)'))
            if flag_monotony_direction == 1 and rise_en and value_rise:
                log.success('Capture', 'SaveData P: RISE TIME→col%d=%ss' % (rise_col, value_rise))
            elif flag_monotony_direction == 0 and fall_en and value_fall:
                log.success('Capture', 'SaveData N: FALL TIME→col%d=%ss' % (fall_col, value_fall))

    return delay_time, value_top, value_base, value_max, value_min
