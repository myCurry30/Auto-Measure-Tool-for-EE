"""仪器连接与配置 - tkinter 版本。

包含 instrument(), MSO_set(), Set_Lable() 函数。
"""
import pyvisa
from tkinter import messagebox

from oscilloscope_drivers_legacy import OscMPO5series, OscDPO7000C, OscDPO5104B


# 全局变量（由主模块注入）
osc = None
rm = None
MSO5 = 0
DPO7000 = 0
DPO5104B = 0
flag_MSOConnect = 0
flag_Test_items = 0
measure1_fn = None
measure2_fn = None
measure3_fn = None
measure4_fn = None
measure5_fn = None
measure6_fn = None


def instrument():
    """连接示波器，自动识别型号。"""
    global osc, rm, MSO5, DPO7000, DPO5104B, flag_MSOConnect
    rm = pyvisa.ResourceManager()
    insadd = rm.list_resources()
    print(insadd)
    DPO7000 = 0
    DPO5104B = 0
    MSO5 = 0
    flag_MSOConnect = 0
    for addr in insadd:
        str0 = addr.find('GPIB')
        str01 = addr.find('USB')
        if str0 != -1 or str01 != -1:
            ins = rm.open_resource(addr)
            insinf = ins.query('*IDN?')
            insinf = insinf.upper()
            print(insinf)
            str1 = insinf.find('TEKTRONIX,DPO7')
            if str1 != -1:
                print('该仪器型号为TEKTRONIX,DPO7000系列示波器，设备连接成功')
                print('地址为' + addr)
                osc = OscDPO7000C(addr, rm)
                DPO7000 = 1
            str2 = insinf.find('TEKTRONIX,MSO')
            if str2 != -1:
                print('该仪器型号为TEKTRONIX,MSO4/5/6系列示波器，设备连接成功')
                print('地址为' + addr)
                osc = OscMPO5series(addr, rm)
                MSO5 = 1
            str3 = insinf.find('TEKTRONIX,DPO5')
            if str3 != -1:
                print('该仪器型号为TEKTRONIX,DPO5000系列示波器，设备连接成功')
                print('地址为' + addr)
                osc = OscDPO5104B(addr, rm)
                DPO5104B = 1
    oscstate = DPO7000 or MSO5 or DPO5104B
    print(oscstate)
    if oscstate:
        messagebox.showinfo(title='仪器连接', message='示波器已正确连接')
        flag_MSOConnect = 1
    else:
        messagebox.showerror(title='仪器连接', message='示波器连接错误，请检查!')
        flag_MSOConnect = 0


def MSO_set():
    """配置示波器通道和测量项。"""
    global flag_Test_items
    osc.write('FACTORY')
    osc.write('DISplay:WAVEView1:VIEWStyle OVErlay')
    if flag_Test_items == 9:
        osc.channel_state('ON', 'ON', 'ON', 'OFF')
        osc.chanset('CH1', -2.5, 0, '1.0000E+09', 1)
        osc.chanset('CH2', -3.5, 0, '1.0000E+09', 1)
        osc.chanset('CH3', -4.5, 0, '1.0000E+09', 1)
    elif flag_Test_items == 10:
        osc.channel_state('ON', 'OFF', 'OFF', 'OFF')
        osc.chanset('CH1', -2.5, 0, '1.0000E+09', 1)
    else:
        osc.channel_state('ON', 'ON', 'OFF', 'OFF')
        osc.chanset('CH1', -2.5, 0, '1.0000E+09', 1)
        osc.chanset('CH2', -3.5, 0, '1.0000E+09', 1)
    osc.write('HORIZONTAL:MODE AUTO')
    osc.write('HORIZONTAL:MODE:SCALE 1e-2')
    osc.write('HORIZONTAL:POSITION 30')
    if flag_Test_items == 1 or flag_Test_items == 0:
        measure1_fn()
    if flag_Test_items in (2, 3, 4, 5, 6):
        measure2_fn()
    if flag_Test_items == 7:
        measure3_fn()
    if flag_Test_items == 8:
        measure4_fn()
    if flag_Test_items == 9:
        measure5_fn()
    if flag_Test_items == 10:
        measure6_fn()
    osc.state('run')


def Set_Lable():
    """设置示波器通道标签。"""
    global flag_MSOConnect, flag_Test_items, xls
    if flag_MSOConnect == 0:
        messagebox.showerror(title='仪器连接', message='示波器连接错误，请检查!')
    channel_Lable_set_fn()
