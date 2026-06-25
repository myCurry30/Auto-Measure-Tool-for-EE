"""Nettrix Power Sequence Test Tool V2.0 - 模块化版本 (tkinter)

原 power_on_autotest.py 已拆分为以下模块：
  - easy_excel_legacy.py      Excel 操作类
  - oscilloscope_drivers_legacy.py  示波器驱动类
  - measurement_legacy.py     测量配置函数
  - instrument_legacy.py      仪器连接与配置
  - navigation_legacy.py      导航函数 (Last/Next/jump)
  - capture_legacy.py         截图捕获与数据处理

本文件负责：GUI 创建 + 全局变量注入 + 程序入口
"""
import tkinter as tk
from tkinter import *
import time
import os
import pyvisa
from tkinter import messagebox
from tkinter import filedialog

# 导入拆分后的模块
from easy_excel_legacy import EasyExcel
import measurement_legacy
import instrument_legacy
import navigation_legacy
import capture_legacy


##################################################################################
# 全局变量
##################################################################################
file_path = ''
pic_path = ''
xls = None
Tests_Sum = 999
flag_Test_items = 0
m = 8
n = 6
sheet_Summary = "Summary"
flag_MSOConnect = 0
MSO5 = 0
DPO7000 = 0
DPO5104B = 0
flag_monotony_direction = 1
Signal1_name = ''
Signal2_name = ''
Signal3_name = ''
osc = None
rm = None
insinf = ''
delay_time = ''
Value_TOP = ''
Value_BASE = ''
Value_MAX = ''
Value_MIN = ''


##################################################################################
# 将全局变量注入到各子模块
##################################################################################
def inject_globals():
    """将全局变量引用注入到各子模块，使其可以访问共享状态。"""
    # EasyExcel 模块
    import easy_excel_legacy
    easy_excel_legacy.flag_Test_items = flag_Test_items  # 注意：这里只注入初始值
    easy_excel_legacy.flag_monotony_direction = flag_monotony_direction

    # Measurement 模块
    measurement_legacy.osc = osc
    measurement_legacy.MSO5 = MSO5
    measurement_legacy.DPO7000 = DPO7000
    measurement_legacy.DPO5104B = DPO5104B

    # Instrument 模块
    instrument_legacy.measure1_fn = measurement_legacy.measure1
    instrument_legacy.measure2_fn = measurement_legacy.measure2
    instrument_legacy.measure3_fn = measurement_legacy.measure3
    instrument_legacy.measure4_fn = measurement_legacy.measure4
    instrument_legacy.measure5_fn = measurement_legacy.measure5
    instrument_legacy.measure6_fn = measurement_legacy.measure6
    instrument_legacy.channel_Lable_set_fn = measurement_legacy.channel_Lable_set

    # Navigation 模块
    navigation_legacy.m = m
    navigation_legacy.xls = xls
    navigation_legacy.flag_MSOConnect = flag_MSOConnect
    navigation_legacy.flag_Test_items = flag_Test_items
    navigation_legacy.flag_monotony_direction = flag_monotony_direction
    navigation_legacy.MSO5 = MSO5
    navigation_legacy.osc = osc

    # Capture 模块
    capture_legacy.osc = osc
    capture_legacy.xls = xls
    capture_legacy.flag_Test_items = flag_Test_items
    capture_legacy.flag_MSOConnect = flag_MSOConnect
    capture_legacy.flag_monotony_direction = flag_monotony_direction
    capture_legacy.MSO5 = MSO5
    capture_legacy.pic_path = pic_path
    capture_legacy.m = m


##################################################################################
# GUI 回调函数
##################################################################################
def go():
    """加载测试数据。"""
    global m, xls, Signal1_name, Signal2_name, Signal3_name, flag_monotony_direction
    m = 8
    xls = EasyExcel(file_path)
    Signal1_name = ''
    Signal2_name = ''
    Signal3_name = ''
    EnValue14.set('')
    if flag_Test_items == 8:
        Signal1_name = str(xls.getCell(entry.get(), 7, 2))
        Signal2_name = str(xls.getCell(entry.get(), 7, 3))
        Signal3_name = ''
    elif flag_Test_items == 9:
        Signal1_name = str(xls.getCell(entry.get(), 2, 1))
        Signal2_name = str(xls.getCell(entry.get(), 2, 2))
        Signal3_name = str(xls.getCell(entry.get(), 2, 3))
    elif flag_Test_items == 10:
        Signal1_name = str(xls.getCell(entry.get(), 21, 2))
        Signal2_name = ''
        Signal3_name = ''
        EnValue14.set('P')
        flag_monotony_direction = 1
    else:
        Signal1_name = str(xls.getCell(entry.get(), 8, 5))
        Signal2_name = str(xls.getCell(entry.get(), 8, 6))
        Signal3_name = ''
    print(Tests_Sum)
    print(Signal1_name)
    print(Signal2_name)
    EnValue4.set(int(Tests_Sum))
    EnValue5.set(Signal1_name)
    EnValue6.set(Signal2_name)
    EnValue7.set(Signal1_name)
    EnValue8.set(Signal2_name)
    EnValue12.set(Signal3_name)
    EnValue13.set(Signal3_name)
    EnValue9.set(int(m - 7))
    if flag_Test_items == 8:
        EnValue11.set(int(m - 1))
    elif flag_Test_items == 9:
        EnValue11.set(int(m - 6))
    elif flag_Test_items == 10:
        EnValue11.set(int(m + 13))
    else:
        EnValue11.set(int(m))

    # 更新子模块引用
    navigation_legacy.m = m
    navigation_legacy.xls = xls
    navigation_legacy.flag_Test_items = flag_Test_items
    navigation_legacy.flag_monotony_direction = flag_monotony_direction
    navigation_legacy.Signal1_name = Signal1_name
    navigation_legacy.Signal2_name = Signal2_name
    navigation_legacy.Signal3_name = Signal3_name
    capture_legacy.xls = xls
    capture_legacy.m = m
    capture_legacy.flag_Test_items = flag_Test_items


def tl1():
    global flag_Test_items
    EnValue3.set(theButton01.cget('text'))
    flag_Test_items = 1
    go()

def tl2():
    global flag_Test_items
    EnValue3.set(theButton02.cget('text'))
    flag_Test_items = 2
    go()

def tl3():
    global flag_Test_items
    EnValue3.set(theButton03.cget('text'))
    flag_Test_items = 3
    go()

def tl4():
    global flag_Test_items
    EnValue3.set(theButton04.cget('text'))
    flag_Test_items = 4
    go()

def tl5():
    global flag_Test_items
    EnValue3.set(theButton05.cget('text'))
    flag_Test_items = 5
    go()

def tl6():
    global flag_Test_items
    EnValue3.set(theButton06.cget('text'))
    flag_Test_items = 6
    go()

def tl12():
    global flag_Test_items
    EnValue3.set(theButton19.cget('text'))
    flag_Test_items = 12
    go()

def tl7():
    global flag_Test_items
    EnValue3.set(theButton07.cget('text'))
    flag_Test_items = 7
    go()

def tl8():
    global flag_Test_items
    EnValue3.set(theButton08.cget('text'))
    flag_Test_items = 8
    go()

def tl9():
    global flag_Test_items
    EnValue3.set(theButton09.cget('text'))
    flag_Test_items = 9
    go()

def tl10():
    global flag_Test_items
    EnValue3.set(theButton10.cget('text'))
    flag_Test_items = 10
    go()

def tl11():
    global xls
    xls.save()


##################################################################################
# 文件路径选择
##################################################################################
def select_excel_path():
    global file_path
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
    print(file_path)
    if file_path:
        EnValue1.set(file_path)

def select_pic_path():
    global pic_path
    pic_path = filedialog.askdirectory()
    print(pic_path)
    if pic_path:
        EnValue2.set(pic_path)
        capture_legacy.pic_path = pic_path


##################################################################################
# 包装函数：更新子模块全局变量后调用
##################################################################################
def Last_wrapper():
    """导航到上一项（包装函数，同步全局变量）。"""
    global m, Signal1_name, Signal2_name, Signal3_name, flag_Test_items, flag_MSOConnect, flag_monotony_direction, MSO5
    navigation_legacy.m = m
    navigation_legacy.Signal1_name = Signal1_name
    navigation_legacy.Signal2_name = Signal2_name
    navigation_legacy.Signal3_name = Signal3_name
    navigation_legacy.xls = xls
    navigation_legacy.flag_MSOConnect = flag_MSOConnect
    navigation_legacy.flag_Test_items = flag_Test_items
    navigation_legacy.flag_monotony_direction = flag_monotony_direction
    navigation_legacy.MSO5 = MSO5
    navigation_legacy.osc = osc
    navigation_legacy.entry = entry
    navigation_legacy.EnValue5 = EnValue5
    navigation_legacy.EnValue6 = EnValue6
    navigation_legacy.EnValue7 = EnValue7
    navigation_legacy.EnValue8 = EnValue8
    navigation_legacy.EnValue9 = EnValue9
    navigation_legacy.EnValue12 = EnValue12
    navigation_legacy.EnValue13 = EnValue13
    navigation_legacy.EnValue14 = EnValue14
    navigation_legacy.Last()
    m = navigation_legacy.m
    flag_monotony_direction = navigation_legacy.flag_monotony_direction
    Signal1_name = navigation_legacy.Signal1_name
    Signal2_name = navigation_legacy.Signal2_name
    Signal3_name = navigation_legacy.Signal3_name


def Next_wrapper():
    """导航到下一项。"""
    global m, Signal1_name, Signal2_name, Signal3_name, flag_Test_items, flag_MSOConnect, flag_monotony_direction, MSO5
    navigation_legacy.m = m
    navigation_legacy.Signal1_name = Signal1_name
    navigation_legacy.Signal2_name = Signal2_name
    navigation_legacy.Signal3_name = Signal3_name
    navigation_legacy.xls = xls
    navigation_legacy.flag_MSOConnect = flag_MSOConnect
    navigation_legacy.flag_Test_items = flag_Test_items
    navigation_legacy.flag_monotony_direction = flag_monotony_direction
    navigation_legacy.MSO5 = MSO5
    navigation_legacy.osc = osc
    navigation_legacy.entry = entry
    navigation_legacy.entry5 = entry5
    navigation_legacy.EnValue5 = EnValue5
    navigation_legacy.EnValue6 = EnValue6
    navigation_legacy.EnValue7 = EnValue7
    navigation_legacy.EnValue8 = EnValue8
    navigation_legacy.EnValue9 = EnValue9
    navigation_legacy.EnValue12 = EnValue12
    navigation_legacy.EnValue13 = EnValue13
    navigation_legacy.EnValue14 = EnValue14
    navigation_legacy.Next()
    m = navigation_legacy.m
    flag_monotony_direction = navigation_legacy.flag_monotony_direction
    Signal1_name = navigation_legacy.Signal1_name
    Signal2_name = navigation_legacy.Signal2_name
    Signal3_name = navigation_legacy.Signal3_name


def jump_wrapper():
    """跳转到指定测试项。"""
    global m, Signal1_name, Signal2_name, Signal3_name, flag_Test_items, flag_MSOConnect, flag_monotony_direction, MSO5
    navigation_legacy.m = m
    navigation_legacy.Signal1_name = Signal1_name
    navigation_legacy.Signal2_name = Signal2_name
    navigation_legacy.Signal3_name = Signal3_name
    navigation_legacy.xls = xls
    navigation_legacy.flag_MSOConnect = flag_MSOConnect
    navigation_legacy.flag_Test_items = flag_Test_items
    navigation_legacy.flag_monotony_direction = flag_monotony_direction
    navigation_legacy.MSO5 = MSO5
    navigation_legacy.osc = osc
    navigation_legacy.entry = entry
    navigation_legacy.entry5 = entry5
    navigation_legacy.EnValue5 = EnValue5
    navigation_legacy.EnValue6 = EnValue6
    navigation_legacy.EnValue7 = EnValue7
    navigation_legacy.EnValue8 = EnValue8
    navigation_legacy.EnValue9 = EnValue9
    navigation_legacy.EnValue12 = EnValue12
    navigation_legacy.EnValue13 = EnValue13
    navigation_legacy.EnValue14 = EnValue14
    navigation_legacy.jump()
    m = navigation_legacy.m
    flag_monotony_direction = navigation_legacy.flag_monotony_direction
    Signal1_name = navigation_legacy.Signal1_name
    Signal2_name = navigation_legacy.Signal2_name
    Signal3_name = navigation_legacy.Signal3_name


def instrument_wrapper():
    """连接仪器（包装函数）。"""
    global osc, rm, MSO5, DPO7000, DPO5104B, flag_MSOConnect
    instrument_legacy.instrument()
    osc = instrument_legacy.osc
    rm = instrument_legacy.rm
    MSO5 = instrument_legacy.MSO5
    DPO7000 = instrument_legacy.DPO7000
    DPO5104B = instrument_legacy.DPO5104B
    flag_MSOConnect = instrument_legacy.flag_MSOConnect
    # 同步到子模块
    measurement_legacy.osc = osc
    measurement_legacy.MSO5 = MSO5
    measurement_legacy.DPO7000 = DPO7000
    measurement_legacy.DPO5104B = DPO5104B
    capture_legacy.osc = osc
    capture_legacy.MSO5 = MSO5
    capture_legacy.flag_MSOConnect = flag_MSOConnect
    navigation_legacy.osc = osc
    navigation_legacy.MSO5 = MSO5
    navigation_legacy.flag_MSOConnect = flag_MSOConnect


def MSO_set_wrapper():
    """配置示波器（包装函数）。"""
    global flag_Test_items
    instrument_legacy.osc = osc
    instrument_legacy.flag_Test_items = flag_Test_items
    instrument_legacy.MSO5 = MSO5
    instrument_legacy.DPO7000 = DPO7000
    instrument_legacy.DPO5104B = DPO5104B
    measurement_legacy.osc = osc
    measurement_legacy.MSO5 = MSO5
    instrument_legacy.MSO_set()


def Set_Lable_wrapper():
    """设置标签（包装函数）。"""
    global flag_MSOConnect, flag_Test_items, xls
    instrument_legacy.flag_MSOConnect = flag_MSOConnect
    instrument_legacy.flag_Test_items = flag_Test_items
    instrument_legacy.xls = xls
    measurement_legacy.osc = osc
    measurement_legacy.entry1 = entry1
    measurement_legacy.entry2 = entry2
    measurement_legacy.entry6 = entry6
    instrument_legacy.Set_Lable()


def Capture_Pic_wrapper():
    """捕获截图（包装函数）。"""
    global flag_MSOConnect, delay_time, flag_monotony_direction, flag_Test_items, MSO5, m, xls
    capture_legacy.osc = osc
    capture_legacy.xls = xls
    capture_legacy.flag_Test_items = flag_Test_items
    capture_legacy.flag_MSOConnect = flag_MSOConnect
    capture_legacy.flag_monotony_direction = flag_monotony_direction
    capture_legacy.MSO5 = MSO5
    capture_legacy.pic_path = pic_path
    capture_legacy.entry = entry
    capture_legacy.entry1 = entry1
    capture_legacy.entry2 = entry2
    capture_legacy.entry4 = entry4
    capture_legacy.entry6 = entry6
    capture_legacy.m = m
    import easy_excel_legacy
    easy_excel_legacy.flag_Test_items = flag_Test_items
    easy_excel_legacy.flag_monotony_direction = flag_monotony_direction
    capture_legacy.Capture_Pic()


##################################################################################
# GUI 创建
##################################################################################
root = Tk()
root.title('Nettrix Power Sequence Test Tool V2.0          by liujch2')
root.resizable(False, False)
root.geometry('750x700')

image_file = PhotoImage(file='NC logo.png')

image = Label(root, image=image_file)
image.place(x=0, y=10, width=400, height=70)
EnValue1 = StringVar()  # file_path
EnValue2 = StringVar()  # pic_path
EnValue3 = StringVar()  # SheetName
EnValue4 = IntVar()  # Part number
EnValue5 = StringVar()  # Signal1 name
EnValue6 = StringVar()  # Signal2 name
EnValue12 = StringVar()  # Signal3 name
EnValue7 = StringVar()  # CH1 Lable
EnValue8 = StringVar()  # CH2 Lable
EnValue13 = StringVar()  # CH3 Lable
EnValue9 = IntVar()  # Current item
EnValue10 = StringVar()  # project name
EnValue11 = IntVar()
EnValue14 = StringVar()  # positive or negtive

##################################################################################
theButton = Button(root, text="选择测试报告路径", command=select_excel_path)
theButton.place(x=10, y=90, width=115, height=30)
Entry(root, show=None, textvariable=EnValue1, state='readonly').place(x=130, y=90, width=250, height=30)

theButton = Button(root, text="选择保存图片路径", command=select_pic_path)
theButton.place(x=10, y=140, width=115, height=30)
Entry(root, show=None, textvariable=EnValue2, state='readonly').place(x=130, y=140, width=250, height=30)

Label(root, text='Project name：').place(x=00, y=190, width=140, height=30)
entry4 = Entry(root, show=None, width=20, textvariable=EnValue10)
entry4.place(x=130, y=190, width=250, height=30)

Label(root, text='SheetName:').place(x=00, y=230, width=140, height=30)
entry = Entry(root, show=None, width=20, textvariable=EnValue3)
entry.place(x=130, y=230, width=250, height=30)

Label(root, text='Tests Sum：').place(x=00, y=270, width=140, height=30)
entry3 = Entry(root, show=None, width=20, textvariable=EnValue4, state='readonly')
entry3.place(x=130, y=270, width=70, height=30)

Label(root, text='Current item：').place(x=200, y=270, width=120, height=30)
Entry(root, show=None, textvariable=EnValue9, state='readonly').place(x=310, y=270, width=70, height=30)

Label(root, text='Signal_1 name：').place(x=00, y=310, width=140, height=30)
Entry(root, show=None, textvariable=EnValue5, state='readonly').place(x=130, y=310, width=250, height=30)

Label(root, text='Signal_2 name：').place(x=00, y=350, width=140, height=30)
Entry(root, show=None, textvariable=EnValue6, state='readonly').place(x=130, y=350, width=250, height=30)

Label(root, text='Signal_3 name：').place(x=00, y=390, width=140, height=30)
Entry(root, show=None, textvariable=EnValue12, state='readonly').place(x=130, y=390, width=250, height=30)

Label(root, text='CH1 Lable：').place(x=00, y=430, width=140, height=30)
entry1 = Entry(root, show=None, width=20, textvariable=EnValue7)
entry1.place(x=130, y=430, width=250, height=30)

Entry(root, show=None, textvariable=EnValue14, state='readonly', justify='center').place(x=390, y=430, width=30, height=30)

Label(root, text='CH2 Lable：').place(x=00, y=470, width=140, height=30)
entry2 = Entry(root, show=None, width=20, textvariable=EnValue8)
entry2.place(x=130, y=470, width=250, height=30)

Label(root, text='CH3 Lable：').place(x=00, y=510, width=140, height=30)
entry6 = Entry(root, show=None, width=20, textvariable=EnValue13)
entry6.place(x=130, y=510, width=250, height=30)

Label(root, text='跳转测试项：').place(x=00, y=550, width=140, height=30)
entry5 = Entry(root, show=None, width=20, textvariable=EnValue11)
entry5.place(x=130, y=550, width=100, height=30)

theButton18 = Button(root, text="跳转", command=jump_wrapper).place(x=280, y=550, width=50, height=30)

theButton11 = Button(root, text="连接仪器", command=instrument_wrapper).place(x=415, y=570, width=80, height=30)

theButton12 = Button(root, text='保存并退出表格', command=tl11, activeforeground='white', activebackground='red').place(
    x=515, y=570, width=100, height=30)

theButton13 = Button(root, text="<--", command=Last_wrapper).place(x=415, y=510, width=80, height=30)

theButton14 = Button(root, text="-->", command=Next_wrapper).place(x=525, y=510, width=80, height=30)

theButton15 = Button(root, text="保存图片", command=Capture_Pic_wrapper).place(x=635, y=570, width=80, height=30)

theButton16 = Button(root, text="Set Lable", command=Set_Lable_wrapper).place(x=635, y=510, width=80, height=30)

theButton17 = Button(root, text="Set_MSO", command=MSO_set_wrapper).place(x=635, y=630, width=80, height=30)

group = LabelFrame(root, text='Power on 测试项', padx=5, pady=5)
group.place(x=450, y=30, width=280, height=470)
theButton01 = Button(group, text="CPU Power Sequence(G3 to S0)", command=tl1)
theButton01.grid(row=1, column=1, sticky=E + W, padx=20, pady=5)
theButton02 = Button(group, text="CPU Power Sequence(S0-S5-S0)", command=tl2)
theButton02.grid(row=2, column=1, sticky=E + W, padx=20, pady=5)
theButton03 = Button(group, text="CPU Power Sequence(S0 GLO RST)", command=tl3)
theButton03.grid(row=3, column=1, sticky=E + W, padx=20, pady=5)
theButton04 = Button(group, text="CPU Power Sequence(WARM RESET)", command=tl4)
theButton04.grid(row=4, column=1, sticky=E + W, padx=20, pady=5)
theButton05 = Button(group, text="CPU Power Sequence(S5 GLO RST)", command=tl5)
theButton05.grid(row=5, column=1, sticky=E + W, padx=20, pady=5)
theButton06 = Button(group, text="CPU Power Sequence(THERMTRIP)", command=tl6)
theButton06.grid(row=6, column=1, sticky=E + W, padx=20, pady=5)
theButton19 = Button(group, text="CPU Power Sequence(S5 to G3)", command=tl12)
theButton19.grid(row=7, column=1, sticky=E + W, padx=20, pady=5)
theButton07 = Button(group, text="CPU LVT", command=tl7)
theButton07.grid(row=8, column=1, sticky=E + W, padx=20, pady=5)
theButton08 = Button(group, text="CPU HW Strap", command=tl8)
theButton08.grid(row=9, column=1, sticky=E + W, padx=20, pady=5)
theButton09 = Button(group, text="CPU PG&EN", command=tl9)
theButton09.grid(row=10, column=1, sticky=E + W, padx=20, pady=5)
theButton10 = Button(group, text="CPU Monotony", command=tl10)
theButton10.grid(row=11, column=1, sticky=E + W, padx=20, pady=5)

##################################################################################
root.mainloop()
