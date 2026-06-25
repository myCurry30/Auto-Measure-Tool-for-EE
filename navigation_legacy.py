"""测试导航函数 - tkinter 版本。

包含 Last(), Next(), jump() 函数，用于在 Excel 信号之间导航。
"""


# 全局变量（由主模块导入）
m = None
Signal1_name = None
Signal2_name = None
Signal3_name = None
xls = None
flag_MSOConnect = None
flag_Test_items = None
flag_monotony_direction = None
MSO5 = None
osc = None

# GUI 变量（由主模块导入）
EnValue5 = None
EnValue6 = None
EnValue7 = None
EnValue8 = None
EnValue9 = None
EnValue12 = None
EnValue13 = None
EnValue14 = None
entry = None


def Last():
    global m, Signal1_name, Signal2_name, flag_monotony_direction
    i = 0
    EnValue14.set('')
    print('m1', m)
    if m <= 8:
        m = 8
    else:
        m = m - 1
    print('m2', m)
    if flag_Test_items == 8:
        Signal1_name = str(xls.getCell(entry.get(), m-1, 2))
        Signal2_name = str(xls.getCell(entry.get(), m-1, 3))
        while Signal1_name == "None":
            i = i + 1
            Signal1_name = str(xls.getCell(entry.get(), m - i - 1, 2))
        while Signal2_name == "None":
            i = i + 1
            Signal2_name = str(xls.getCell(entry.get(), m - i - 1, 3))
    elif flag_Test_items == 9:
        Signal1_name = str(xls.getCell(entry.get(), m - 6, 1))
        Signal2_name = str(xls.getCell(entry.get(), m - 6, 2))
        Signal3_name = str(xls.getCell(entry.get(), m - 6, 3))
    elif flag_Test_items == 10:
        if flag_monotony_direction == 1:
            EnValue14.set('N')
            flag_monotony_direction = 0
            if MSO5 == 1:
                osc.trigger('NORMAL', 'CH1', 'FALL', 0.5)
        elif flag_monotony_direction == 0:
            if m > 8:
                m = m + 1
            print('m3', m)
            EnValue14.set('P')
            flag_monotony_direction = 1
            if MSO5 == 1:
                osc.trigger('NORMAL', 'CH1', 'RISE', 0.5)
        Signal1_name = str(xls.getCell(entry.get(), m + 13, 2))
        Signal2_name = ''
        Signal3_name = ''
    else:
        Signal1_name = str(xls.getCell(entry.get(), m, 5))
        Signal2_name = str(xls.getCell(entry.get(), m, 6))
        while Signal1_name == "None":
            i = i + 1
            Signal1_name = str(xls.getCell(entry.get(), m - i, 5))
        while Signal2_name == "None":
            i = i + 1
            Signal2_name = str(xls.getCell(entry.get(), m - i, 6))
    if flag_Test_items != 10:
        if Signal1_name == Signal2_name:
            Signal2_name = "None"
        if flag_MSOConnect == 1:
            if Signal1_name == 'None':
                osc.write('SELECT:CH1 OFF')
            else:
                osc.write('SELECT:CH1 ON')
            if Signal2_name == 'None':
                osc.write('SELECT:CH2 OFF')
            else:
                osc.write('SELECT:CH2 ON')
            if flag_Test_items == 9:
                if Signal3_name == 'None':
                    osc.write('SELECT:CH3 OFF')
                else:
                    osc.write('SELECT:CH3 ON')
    print(Signal1_name)
    print(Signal2_name)
    if flag_Test_items == 9:
        print(Signal3_name)
        EnValue12.set(Signal3_name)
        EnValue13.set(Signal3_name)
    EnValue5.set(Signal1_name)
    EnValue6.set(Signal2_name)
    EnValue7.set(Signal1_name)
    EnValue8.set(Signal2_name)
    EnValue9.set(int(m - 7))


def Next():
    global m, Signal1_name, Signal2_name, flag_monotony_direction
    i = 0
    EnValue14.set('')
    m = m + 1
    if flag_Test_items == 8:
        Signal1_name = str(xls.getCell(entry.get(), m-1, 2))
        Signal2_name = str(xls.getCell(entry.get(), m-1, 3))
        while Signal1_name == "None":
            i = i + 1
            Signal1_name = str(xls.getCell(entry.get(), m - i-1, 2))
        while Signal2_name == "None":
            i = i + 1
            Signal2_name = str(xls.getCell(entry.get(), m - i-1, 3))
    elif flag_Test_items == 9:
        Signal1_name = str(xls.getCell(entry.get(), m - 6, 1))
        Signal2_name = str(xls.getCell(entry.get(), m - 6, 2))
        Signal3_name = str(xls.getCell(entry.get(), m - 6, 3))
    elif flag_Test_items == 10:
        if flag_monotony_direction == 1:
            m = m - 1
            EnValue14.set('N')
            flag_monotony_direction = 0
            if MSO5 == 1:
                osc.trigger('NORMAL', 'CH1', 'FALL', 0.5)
        elif flag_monotony_direction == 0:
            EnValue14.set('P')
            flag_monotony_direction = 1
            if MSO5 == 1:
                osc.trigger('NORMAL', 'CH1', 'RISE', 0.5)
        Signal1_name = str(xls.getCell(entry.get(), m + 13, 2))
        Signal2_name = ''
        Signal3_name = ''
    else:
        Signal1_name = str(xls.getCell(entry.get(), m, 5))
        Signal2_name = str(xls.getCell(entry.get(), m, 6))
        while Signal1_name == "None":
            i = i + 1
            Signal1_name = str(xls.getCell(entry.get(), m - i, 5))
        while Signal2_name == "None":
            i = i + 1
            Signal2_name = str(xls.getCell(entry.get(), m - i, 6))
    if flag_Test_items != 10:
        if Signal1_name == Signal2_name:
            Signal2_name = "None"
        if flag_MSOConnect == 1:
            if Signal1_name == 'None':
                osc.write('SELECT:CH1 OFF')
            else:
                osc.write('SELECT:CH1 ON')
            if Signal2_name == 'None':
                osc.write('SELECT:CH2 OFF')
            else:
                osc.write('SELECT:CH2 ON')
            if flag_Test_items == 9:
                if Signal3_name == 'None':
                    osc.write('SELECT:CH3 OFF')
                else:
                    osc.write('SELECT:CH3 ON')
    print(Signal1_name)
    print(Signal2_name)
    if flag_Test_items == 9:
        print(Signal3_name)
        EnValue12.set(Signal3_name)
        EnValue13.set(Signal3_name)
    EnValue5.set(Signal1_name)
    EnValue6.set(Signal2_name)
    EnValue7.set(Signal1_name)
    EnValue8.set(Signal2_name)
    EnValue9.set(int(m-7))


def jump():
    global m, Signal1_name, Signal2_name, flag_monotony_direction
    i = 0
    EnValue14.set('')
    if flag_Test_items == 8:
        m = int(entry5.get()) + 1
    elif flag_Test_items == 9:
        m = int(entry5.get()) + 6
    elif flag_Test_items == 10:
        m = int(entry5.get()) - 13
    else:
        m = int(entry5.get())

    print('m1', m)
    if m <= 8:
        m = 8
    if flag_Test_items == 8:
        Signal1_name = str(xls.getCell(entry.get(), m -1, 2))
        Signal2_name = str(xls.getCell(entry.get(), m -1, 3))
        while Signal1_name == "None":
            i = i + 1
            Signal1_name = str(xls.getCell(entry.get(), m - i-1, 2))
        while Signal2_name == "None":
            i = i + 1
            Signal2_name = str(xls.getCell(entry.get(), m - i-1, 3))
    elif flag_Test_items == 9:
        Signal1_name = str(xls.getCell(entry.get(), m - 6, 1))
        Signal2_name = str(xls.getCell(entry.get(), m - 6, 2))
        Signal3_name = str(xls.getCell(entry.get(), m - 6, 3))
    elif flag_Test_items == 10:
        Signal1_name = str(xls.getCell(entry.get(), m + 13, 2))
        Signal2_name = ''
        Signal3_name = ''
        EnValue14.set('P')
        flag_monotony_direction = 1
        if MSO5 == 1:
            osc.trigger('NORMAL', 'CH1', 'RISE', 0.5)
    else:
        Signal1_name = str(xls.getCell(entry.get(), m, 5))
        Signal2_name = str(xls.getCell(entry.get(), m, 6))
        while Signal1_name == "None":
            i = i + 1
            Signal1_name = str(xls.getCell(entry.get(), m - i, 5))
        while Signal2_name == "None":
            i = i + 1
            Signal2_name = str(xls.getCell(entry.get(), m - i, 6))
    print('m2', m)
    if flag_Test_items != 10:
        if Signal1_name == Signal2_name:
            Signal2_name = "None"
        if flag_MSOConnect == 1:
            if Signal1_name == 'None':
                osc.write('SELECT:CH1 OFF')
            else:
                osc.write('SELECT:CH1 ON')
            if Signal2_name == 'None':
                osc.write('SELECT:CH2 OFF')
            else:
                osc.write('SELECT:CH2 ON')
            if flag_Test_items == 9:
                if Signal3_name == 'None':
                    osc.write('SELECT:CH3 OFF')
                else:
                    osc.write('SELECT:CH3 ON')
    print(Signal1_name)
    print(Signal2_name)
    EnValue5.set(Signal1_name)
    EnValue6.set(Signal2_name)
    EnValue7.set(Signal1_name)
    EnValue8.set(Signal2_name)
    EnValue9.set(int(m - 7))