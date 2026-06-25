"""截图捕获与数据处理 - tkinter 版本。

包含 mkdir(), savepic(), Capture_Pic() 函数。
"""
import os
import time
from tkinter import messagebox


# 全局变量（由主模块注入）
osc = None
xls = None
flag_Test_items = 0
flag_MSOConnect = 0
flag_monotony_direction = 1
MSO5 = 0
pic_path = ''
entry = None
entry1 = None
entry2 = None
entry4 = None
entry6 = None
m = 8

# 导入 EasyExcel 模块的全局变量
import easy_excel_legacy
flag_Test_items_easyexcel = easy_excel_legacy.flag_Test_items
flag_monotony_direction_easyexcel = easy_excel_legacy.flag_monotony_direction


def mkdir(path):
    """创建目录（如不存在）。"""
    path = path.strip()
    path = path.rstrip("\\")
    isExists = os.path.exists(path)
    if not isExists:
        os.makedirs(path)
        print(path + ' 创建成功')
        return True
    else:
        print(path + ' 目录已存在')
        return False


def savepic():
    """从示波器保存截图到本地。"""
    global flag_Test_items
    mkpath = '%s/%s' % (pic_path, entry.get())
    print("-->", mkpath)
    mkdir(mkpath)
    if flag_Test_items != 10:
        if entry6.get() != "":
            name = '%s TO %s TO %s' % (entry1.get(), entry2.get(), entry6.get())
        elif entry2.get() != "":
            name = '%s TO %s' % (entry1.get(), entry2.get())
        else:
            name = '%s' % (entry1.get())
    else:
        if flag_monotony_direction == 1:
            name = '%s_R' % (entry1.get())
        if flag_monotony_direction == 0:
            name = '%s_F' % (entry1.get())
    file_path = r'%s/%s.PNG' % (mkpath, name)
    osc.makeDir('C:\\%s Test Pictures' % entry4.get())
    osc.makeDir('C:\\%s Test Pictures\\%s' % (entry4.get(), entry.get()))
    osc.export('PNG', 'C:\\%s Test Pictures\\%s\\%s' % (entry4.get(), entry.get(), name))
    time.sleep(1.5)
    osc.readfile('C:/%s Test Pictures/%s/%s.PNG' % (entry4.get(), entry.get(), name))
    time.sleep(0.5)
    data = osc.readraw(file_path)
    time.sleep(0.5)
    return data


def Capture_Pic():
    """捕获截图、插入 Excel、写入测量数据。"""
    global flag_MSOConnect, delay_time, flag_monotony_direction, Value_TOP, Value_BASE, Value_MAX, Value_MIN
    if flag_MSOConnect == 0:
        messagebox.showerror(title='仪器连接', message='示波器连接错误，请检查!')
        return
    xls.save()
    a1_1 = r'%s' % (savepic())
    a1_1 = os.path.abspath(a1_1)

    # 同步 EasyExcel 全局变量
    easy_excel_legacy.flag_Test_items = flag_Test_items
    easy_excel_legacy.flag_monotony_direction = flag_monotony_direction

    xls.addPicture(entry.get(), a1_1, m, 0, 0, 0, 0)
    if flag_Test_items != 8 and flag_Test_items != 9 and flag_Test_items != 10:
        delay_time = osc.query('MEASUrement:MEAS7:MAX?')
        print('query delaytime:', delay_time)
        if delay_time.find('MEASUREMENT') != -1:
            if MSO5 == 1:
                delay_time = delay_time[26:]
        delay_time = eval(delay_time)
        delay_time = float(delay_time)
        print('result delaytime:', delay_time)
        if abs(delay_time) >= 1:
            delay_time = '%.2f' % delay_time
            delay_time = str(delay_time) + 's'
        elif abs(delay_time) < 1 and abs(delay_time) >= 0.001:
            delay_time = float(delay_time) * 1000
            delay_time = '%.2f' % delay_time
            delay_time = str(delay_time) + 'ms'
        elif abs(delay_time) < 0.001 and abs(delay_time) >= 0.000001:
            delay_time = float(delay_time) * 1000000
            delay_time = '%.2f' % delay_time
            delay_time = str(delay_time) + 'μs'
        else:
            delay_time = float(delay_time) * 1000000000
            delay_time = '%.2f' % delay_time
            delay_time = str(delay_time) + 'ns'
        xls.setCell(entry.get(), m, 7, delay_time)

    if flag_Test_items == 10:
        Value_TOP = osc.query('MEASUrement:MEAS1:MAX?')
        Value_BASE = osc.query('MEASUrement:MEAS2:MAX?')
        Value_MAX = osc.query('MEASUrement:MEAS5:MAX?')
        Value_MIN = osc.query('MEASUrement:MEAS6:MAX?')
        print('query Value_TOP:', Value_TOP)
        print('query Value_BASE:', Value_BASE)
        print('query Value_MAX:', Value_MAX)
        print('query Value_MIN:', Value_MIN)
        if Value_TOP.find('MEASUREMENT') != -1:
            if MSO5 == 1:
                Value_TOP = Value_TOP[26:]
        Value_TOP = eval(Value_TOP)
        Value_TOP = float(Value_TOP)
        Value_TOP = '%.4f' % Value_TOP
        if Value_BASE.find('MEASUREMENT') != -1:
            if MSO5 == 1:
                Value_BASE = Value_BASE[26:]
        Value_BASE = eval(Value_BASE)
        Value_BASE = float(Value_BASE)
        Value_BASE = '%.4f' % Value_BASE
        if Value_MAX.find('MEASUREMENT') != -1:
            if MSO5 == 1:
                Value_MAX = Value_MAX[26:]
        Value_MAX = eval(Value_MAX)
        Value_MAX = float(Value_MAX)
        Value_MAX = '%.4f' % Value_MAX
        if Value_MIN.find('MEASUREMENT') != -1:
            if MSO5 == 1:
                Value_MIN = Value_MIN[26:]
        Value_MIN = eval(Value_MIN)
        Value_MIN = float(Value_MIN)
        Value_MIN = '%.4f' % Value_MIN
        if flag_monotony_direction == 1:
            xls.setCell(entry.get(), m + 13, 9, Value_TOP)
            xls.setCell(entry.get(), m + 13, 10, Value_BASE)
            xls.setCell(entry.get(), m + 13, 11, Value_MAX)
            xls.setCell(entry.get(), m + 13, 12, Value_MIN)
        if flag_monotony_direction == 0:
            xls.setCell(entry.get(), m + 13, 13, Value_TOP)
            xls.setCell(entry.get(), m + 13, 14, Value_BASE)
            xls.setCell(entry.get(), m + 13, 15, Value_MAX)
            xls.setCell(entry.get(), m + 13, 16, Value_MIN)
    xls.save()
