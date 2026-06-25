"""Capture and image export functions.

Contains Capture_Pic, savepic, and mkdir functions.
"""
import os
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


def savepic(osc, pic_path, sheet_name, signal1, signal2, signal3,
           project_name, flag_test_items, flag_monotony_direction):
    """Save screenshot from oscilloscope to local disk.

    Args:
        osc: Oscilloscope instance
        pic_path: Base path for saving pictures
        sheet_name: Current sheet name (creates subdirectory)
        signal1: CH1 signal name
        signal2: CH2 signal name
        signal3: CH3 signal name (for item 9)
        project_name: Project name (for oscilloscope directory)
        flag_test_items: Test item type
        flag_monotony_direction: 1=Positive/Rise, 0=Negative/Fall (for item 10)

    Returns:
        Local file path of saved screenshot
    """
    mkpath = '%s/%s' % (pic_path, sheet_name)
    print("-->", mkpath)
    mkdir(mkpath)

    if flag_test_items != 10:
        if signal3 != "":
            name = '%s TO %s TO %s' % (signal1, signal2, signal3)
        elif signal2 != "":
            name = '%s TO %s' % (signal1, signal2)
        else:
            name = '%s' % (signal1)
    else:
        if flag_monotony_direction == 1:
            name = '%s_R' % (signal1)
        if flag_monotony_direction == 0:
            name = '%s_F' % (signal1)

    file_path = r'%s/%s.PNG' % (mkpath, name)
    osc.makeDir('C:\\%s Test Pictures' % project_name)
    osc.makeDir('C:\\%s Test Pictures\\%s' % (project_name, sheet_name))
    osc.export('PNG', 'C:\\%s Test Pictures\\%s\\%s' % (project_name, sheet_name, name))
    time.sleep(1.5)
    osc.readfile('C:/%s Test Pictures/%s/%s.PNG' % (project_name, sheet_name, name))
    time.sleep(0.5)
    data = osc.readraw(file_path)
    time.sleep(0.5)
    return data


def Capture_Pic(osc, xls, sheet_name, signal1, signal2, signal3,
                flag_test_items, flag_monotony_direction, m, mso5,
                pic_path, project_name):
    """Capture screenshot, insert into Excel, and write measurements.

    Args:
        osc: Oscilloscope instance
        xls: EasyExcel instance
        sheet_name: Current sheet name
        signal1: CH1 signal name
        signal2: CH2 signal name
        signal3: CH3 signal name
        flag_test_items: Test item type
        flag_monotony_direction: 1=Positive/Rise, 0=Negative/Fall
        m: Current row index
        mso5: True if MSO4/5/6 series
        pic_path: Base path for saving pictures
        project_name: Project name

    Returns:
        Tuple of (delay_time, value_top, value_base, value_max, value_min)
        delay_time is formatted with unit, others are None for non-monotony tests
    """
    xls.save()
    a1_1 = r'%s' % (savepic(osc, pic_path, sheet_name, signal1, signal2, signal3,
                            project_name, flag_test_items, flag_monotony_direction))
    a1_1 = os.path.abspath(a1_1)

    xls.addPicture(sheet_name, a1_1, m, 0, 0, 0, 0,
                   flag_test_items, flag_monotony_direction)

    delay_time = None
    value_top = value_base = value_max = value_min = None

    if flag_test_items != 8 and flag_test_items != 9 and flag_test_items != 10:
        delay_time_raw = osc.query('MEASUrement:MEAS7:MAX?')
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

        xls.setCell(sheet_name, m, 7, delay_time)

    if flag_test_items == 10:
        value_top_raw = osc.query('MEASUrement:MEAS1:MAX?')
        value_base_raw = osc.query('MEASUrement:MEAS2:MAX?')
        value_max_raw = osc.query('MEASUrement:MEAS5:MAX?')
        value_min_raw = osc.query('MEASUrement:MEAS6:MAX?')
        print('query Value_TOP:', value_top_raw)
        print('query Value_BASE:', value_base_raw)
        print('query Value_MAX:', value_max_raw)
        print('query Value_MIN:', value_min_raw)

        if value_top_raw.find('MEASUREMENT') != -1:
            if mso5:
                value_top_raw = value_top_raw[26:]
        value_top = eval(value_top_raw)
        value_top = float(value_top)
        value_top = '%.4f' % value_top

        if value_base_raw.find('MEASUREMENT') != -1:
            if mso5:
                value_base_raw = value_base_raw[26:]
        value_base = eval(value_base_raw)
        value_base = float(value_base)
        value_base = '%.4f' % value_base

        if value_max_raw.find('MEASUREMENT') != -1:
            if mso5:
                value_max_raw = value_max_raw[26:]
        value_max = eval(value_max_raw)
        value_max = float(value_max)
        value_max = '%.4f' % value_max

        if value_min_raw.find('MEASUREMENT') != -1:
            if mso5:
                value_min_raw = value_min_raw[26:]
        value_min = eval(value_min_raw)
        value_min = float(value_min)
        value_min = '%.4f' % value_min

        if flag_monotony_direction == 1:
            xls.setCell(sheet_name, m + 13, 9, value_top)
            xls.setCell(sheet_name, m + 13, 10, value_base)
            xls.setCell(sheet_name, m + 13, 11, value_max)
            xls.setCell(sheet_name, m + 13, 12, value_min)
        if flag_monotony_direction == 0:
            xls.setCell(sheet_name, m + 13, 13, value_top)
            xls.setCell(sheet_name, m + 13, 14, value_base)
            xls.setCell(sheet_name, m + 13, 15, value_max)
            xls.setCell(sheet_name, m + 13, 16, value_min)

    xls.save()
    return delay_time, value_top, value_base, value_max, value_min