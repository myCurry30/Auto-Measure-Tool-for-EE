import tkinter as tk
from tkinter import *  # 导入tkinter模块的所有内容
import time
import os
import pyvisa
import win32com.client
from tkinter import messagebox
from tkinter import filedialog
import xlwings as xw


##################################################################################
class EasyExcel:
    """A utility to make it easier to get at Excel.  Remembering
    to save the data is your problem, as is  error handling.
    Operates on one workbook at a time."""

    def __init__(self, filename=None):

        self.xlApp = win32com.client.Dispatch('Excel.Application')
        if filename:
            self.filename = filename
            print(filename)
            self.xlBook = self.xlApp.Workbooks.Open(filename)
            self.xlApp.Visible = True
        else:
            self.xlBook = self.xlApp.Workbooks.Add()
            self.filename = ''

    def save(self, newfilename=None):
        if newfilename:
            self.filename = newfilename
            self.xlBook.SaveAs(newfilename)
        else:
            self.xlBook.Save()

    def close(self):
        self.xlBook.Close(SaveChanges=0)
        del self.xlApp

    def getCell(self, sheet, row, col):
        sht = self.xlBook.Worksheets(sheet)
        sht.Activate()
        return sht.Cells(row, col).Value

    def setCell(self, sheet, row, col, value):
        sht = self.xlBook.Worksheets(sheet)
        sht.Activate()
        sht.Cells(row, col).Value = value

    def getRange(self, sheet, row1, col1, row2, col2):
        sht = self.xlBook.Worksheets(sheet)
        sht.Activate()
        return sht.Range(sht.Cells(row1, col1), sht.Cells(row2, col2)).Value

    def addPicture(self, sheet, PictureName, row, left_offset, Top_offset,width, height):
        sht = self.xlBook.Worksheets(sheet)
        sht.Activate()
        if (flag_Test_items == 8):
            Width = sht.Cells(row-1, 14).Width
            Height = sht.Cells(row-1, 14).Height
            cell = sht.Range('N' + str(row-1))
        elif(flag_Test_items == 9):
            Width = sht.Cells(row - 6, 4).Width
            Height = sht.Cells(row - 6, 4).Height
            cell = sht.Range('D' + str(row-6))
        elif (flag_Test_items == 10):
            if(flag_monotony_direction == 1):
                Width = sht.Cells(row + 13, 17).Width
                Height = sht.Cells(row + 13, 17).Height
                cell = sht.Range('Q' + str(row + 13))
            if (flag_monotony_direction == 0):
                Width = sht.Cells(row + 13, 18).Width
                Height = sht.Cells(row + 13, 18).Height
                cell = sht.Range('R' + str(row + 13))
        else:
            Width = sht.Cells(row, 9).Width
            Height = sht.Cells(row, 9).Height
            cell = sht.Range('I' + str(row))
        cell.Select()
        cell.ClearFormats()
        sht.Shapes.AddPicture(PictureName, LinkToFile=False, SaveWithDocument=True, Left=cell.Left + left_offset,
                              Top=cell.Top + Top_offset,
                              Width= Width, Height=Height)

    def cpSheet(self):
        shts = self.xlBook.Worksheets
        shts(1).Copy(None, shts(1))

##################################################################################


def Last():
    global m,Signal1_name,Signal2_name,xls,flag_MSOConnect,flag_Test_items,Signal3_name,flag_monotony_direction,MSO5
    i = 0
    EnValue14.set('')
    print('m1',m)
    if (m <= 8):
        m = 8
    else:
        m = m - 1
    print('m2', m)
    if(flag_Test_items == 8):
        Signal1_name = str(xls.getCell(entry.get(), m-1, 2))
        Signal2_name = str(xls.getCell(entry.get(), m-1, 3))
        while (Signal1_name == "None"):
            i = i + 1
            Signal1_name = str(xls.getCell(entry.get(), m - i - 1, 2))
        while (Signal2_name == "None"):
            i = i + 1
            Signal2_name = str(xls.getCell(entry.get(), m - i - 1, 3))
    elif(flag_Test_items == 9):
        Signal1_name = str(xls.getCell(entry.get(), m - 6, 1))
        Signal2_name = str(xls.getCell(entry.get(), m - 6, 2))
        Signal3_name = str(xls.getCell(entry.get(), m - 6, 3))
        """while (Signal1_name == "None"):
            i = i + 1
            Signal1_name = str(xls.getCell(entry.get(), m - i - 6, 1))
        while (Signal2_name == "None"):
            i = i + 1
            Signal2_name = str(xls.getCell(entry.get(), m - i - 6, 2))
        while (Signal3_name == "None"):
            i = i + 1
            Signal3_name = str(xls.getCell(entry.get(), m - i - 6, 3))"""
    elif(flag_Test_items == 10):
        #选择测量方向
        if(flag_monotony_direction == 1):
            EnValue14.set('N')
            flag_monotony_direction = 0
            if (MSO5 == 1):
                osc.trigger('NORMAL', 'CH1', 'FALL', 0.5)
        elif(flag_monotony_direction == 0):
            if(m > 8):
                m = m + 1
            print('m3', m)
            EnValue14.set('P')
            flag_monotony_direction = 1
            if (MSO5 == 1):
                osc.trigger('NORMAL', 'CH1', 'RISE', 0.5)
        Signal1_name = str(xls.getCell(entry.get(), m + 13, 2))
        Signal2_name = ''
        Signal3_name = ''
    else:
        Signal1_name = str(xls.getCell(entry.get(), m, 5))
        Signal2_name = str(xls.getCell(entry.get(), m, 6))
        while (Signal1_name == "None"):
            i = i + 1
            Signal1_name = str(xls.getCell(entry.get(), m - i, 5))
        while (Signal2_name == "None"):
            i = i + 1
            Signal2_name = str(xls.getCell(entry.get(), m - i, 6))
    if (flag_Test_items != 10):
        if (Signal1_name == Signal2_name):
            Signal2_name = "None"
        if(flag_MSOConnect == 1):
            if (Signal1_name == 'None'):
                osc.write('SELECT:CH1 OFF')
            else:
                osc.write('SELECT:CH1 ON')
            if (Signal2_name == 'None'):
                osc.write('SELECT:CH2 OFF')
            else:
                osc.write('SELECT:CH2 ON')
            if(flag_Test_items == 9):
                if(Signal3_name == 'None'):
                    osc.write('SELECT:CH3 OFF')
                else:
                    osc.write('SELECT:CH3 ON')
    print(Signal1_name)
    print(Signal2_name)
    if (flag_Test_items == 9):
        print(Signal3_name)
        EnValue12.set(Signal3_name)
        EnValue13.set(Signal3_name)
    EnValue5.set(Signal1_name)
    EnValue6.set(Signal2_name)
    EnValue7.set(Signal1_name)
    EnValue8.set(Signal2_name)
    EnValue9.set(int(m - 7))
def Next():
    global m,Signal1_name,Signal2_name,xls,i,flag_MSOConnect,Signal3_name,flag_monotony_direction,MSO5
    Tests_Sum = int(entry3.get())
    i=0
    EnValue14.set('')
    """if (m >= Tests_Sum+8 - 1):
        m = Tests_Sum+8 - 1
    else:
        m = m + 1"""
    m = m + 1
    if (flag_Test_items == 8):
        Signal1_name = str(xls.getCell(entry.get(), m-1, 2))
        Signal2_name = str(xls.getCell(entry.get(), m-1, 3))
        while (Signal1_name == "None"):
            i = i + 1
            Signal1_name = str(xls.getCell(entry.get(), m - i-1, 2))
        while (Signal2_name == "None"):
            i = i + 1
            Signal2_name = str(xls.getCell(entry.get(), m - i-1, 3))
    elif(flag_Test_items == 9):
        Signal1_name = str(xls.getCell(entry.get(), m - 6, 1))
        Signal2_name = str(xls.getCell(entry.get(), m - 6, 2))
        Signal3_name = str(xls.getCell(entry.get(), m - 6, 3))
        """while (Signal1_name == "None"):
            i = i + 1
            Signal1_name = str(xls.getCell(entry.get(), m - i - 6, 1))
        while (Signal2_name == "None"):
            i = i + 1
            Signal2_name = str(xls.getCell(entry.get(), m - i - 6, 2))
        while (Signal3_name == "None"):
            i = i + 1
            Signal3_name = str(xls.getCell(entry.get(), m - i - 6, 3))"""
    elif (flag_Test_items == 10):
        # 选择测量方向
        if (flag_monotony_direction == 1):
            m = m - 1
            EnValue14.set('N')
            flag_monotony_direction = 0
            if (MSO5 == 1):
                osc.trigger('NORMAL', 'CH1', 'FALL', 0.5)
        elif (flag_monotony_direction == 0):
            EnValue14.set('P')
            flag_monotony_direction = 1
            if (MSO5 == 1):
                osc.trigger('NORMAL', 'CH1', 'RISE', 0.5)
        Signal1_name = str(xls.getCell(entry.get(), m + 13, 2))
        Signal2_name = ''
        Signal3_name = ''
    else:
        Signal1_name = str(xls.getCell(entry.get(), m, 5))
        Signal2_name = str(xls.getCell(entry.get(), m, 6))
        while (Signal1_name == "None"):
            i = i + 1
            Signal1_name = str(xls.getCell(entry.get(), m - i, 5))
        while (Signal2_name == "None"):
            i = i + 1
            Signal2_name = str(xls.getCell(entry.get(), m - i, 6))
    if (flag_Test_items != 10):
        if(Signal1_name == Signal2_name):
            Signal2_name = "None"
        if (flag_MSOConnect == 1):
            if (Signal1_name == 'None'):
                osc.write('SELECT:CH1 OFF')
            else:
                osc.write('SELECT:CH1 ON')
            if (Signal2_name == 'None'):
                osc.write('SELECT:CH2 OFF')
            else:
                osc.write('SELECT:CH2 ON')
            if (flag_Test_items == 9):
                if (Signal3_name == 'None'):
                    osc.write('SELECT:CH3 OFF')
                else:
                    osc.write('SELECT:CH3 ON')
    print(Signal1_name)
    print(Signal2_name)
    if (flag_Test_items == 9):
        print(Signal3_name)
        EnValue12.set(Signal3_name)
        EnValue13.set(Signal3_name)
    EnValue5.set(Signal1_name)
    EnValue6.set(Signal2_name)
    EnValue7.set(Signal1_name)
    EnValue8.set(Signal2_name)
    EnValue9.set(int(m-7))

def jump():
    global m, Signal1_name, Signal2_name, xls, i, flag_MSOConnect,flag_monotony_direction,MSO5,flag_Test_items
    #Tests_Sum = int(entry3.get())
    i = 0
    EnValue14.set('')
    if(flag_Test_items == 8):
        m = int(entry5.get()) + 1

    elif(flag_Test_items == 9):
        m = int(entry5.get()) + 6
    elif (flag_Test_items == 10):
        m = int(entry5.get()) - 13
    else:
        m = int(entry5.get())

    """if (m >= Tests_Sum + 8 - 1):
        m = Tests_Sum + 8 - 1"""
    print('m1',m)
    if (m <= 8):
        m = 8
    if(flag_Test_items == 8):
        Signal1_name = str(xls.getCell(entry.get(), m -1, 2))
        Signal2_name = str(xls.getCell(entry.get(), m -1, 3))
        while (Signal1_name == "None"):
            i = i + 1
            Signal1_name = str(xls.getCell(entry.get(), m - i-1, 2))
        while (Signal2_name == "None"):
            i = i + 1
            Signal2_name = str(xls.getCell(entry.get(), m - i-1, 3))
    elif (flag_Test_items == 9):
        Signal1_name = str(xls.getCell(entry.get(), m - 6, 1))
        Signal2_name = str(xls.getCell(entry.get(), m - 6, 2))
        Signal3_name = str(xls.getCell(entry.get(), m - 6, 3))
        """while (Signal1_name == "None"):
            i = i + 1
            Signal1_name = str(xls.getCell(entry.get(), m - i - 6, 1))
        while (Signal2_name == "None"):
            i = i + 1
            Signal2_name = str(xls.getCell(entry.get(), m - i - 6, 2))
        while (Signal3_name == "None"):
            i = i + 1
            Signal2_name = str(xls.getCell(entry.get(), m - i - 6, 3))"""
    elif (flag_Test_items == 10):
        # 选择测量方向
        Signal1_name = str(xls.getCell(entry.get(), m + 13, 2))
        Signal2_name = ''
        Signal3_name = ''
        EnValue14.set('P')
        flag_monotony_direction = 1
        if(MSO5 == 1):
            osc.trigger('NORMAL', 'CH1', 'RISE', 0.5)
    else:
        Signal1_name = str(xls.getCell(entry.get(), m, 5))
        Signal2_name = str(xls.getCell(entry.get(), m, 6))
        while (Signal1_name == "None"):
            i = i + 1
            Signal1_name = str(xls.getCell(entry.get(), m - i, 5))
        while (Signal2_name == "None"):
            i = i + 1
            Signal2_name = str(xls.getCell(entry.get(), m - i, 6))
    print('m2', m)
    if(flag_Test_items != 10):
        if (Signal1_name == Signal2_name):
            Signal2_name = "None"
        if (flag_MSOConnect == 1):
            if (Signal1_name == 'None'):
                osc.write('SELECT:CH1 OFF')
            else:
                osc.write('SELECT:CH1 ON')
            if (Signal2_name == 'None'):
                osc.write('SELECT:CH2 OFF')
            else:
                osc.write('SELECT:CH2 ON')
            if (flag_Test_items == 9):
                if (Signal3_name == 'None'):
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

def go():
    global temp,xls,Tests_Sum,file_path,Signal1_name,Signal2_name,m,n,sheet_Summary,Signal3_name
    m=8
    xls = EasyExcel(file_path)

    """if(flag_Test_items == 1 ):
        Tests_Sum = xls.getCell(sheet_Summary, n, 3)
    elif (flag_Test_items == 2):
        Tests_Sum = xls.getCell(sheet_Summary, n+1, 3)
    elif (flag_Test_items == 3):
        Tests_Sum = xls.getCell(sheet_Summary, n+2, 3)
    elif (flag_Test_items == 4):
        Tests_Sum = xls.getCell(sheet_Summary, n+3, 3)
    elif (flag_Test_items == 5):
        Tests_Sum = xls.getCell(sheet_Summary, n+4, 3)
    elif (flag_Test_items == 6):
        Tests_Sum = xls.getCell(sheet_Summary, n+5, 3)
    elif (flag_Test_items == 7):
        Tests_Sum = xls.getCell(sheet_Summary, n+6, 3)
    elif (flag_Test_items == 8):
        Tests_Sum = xls.getCell(sheet_Summary, n+7, 3)
    elif (flag_Test_items == 9):
        Tests_Sum = xls.getCell(sheet_Summary, n+8, 3)"""

    """if(flag_Test_items == 7):
        Signal1_name = str(xls.getCell(entry.get(), 8, 3))
        Signal2_name = str(xls.getCell(entry.get(), 8, 4))"""
    Signal1_name = ''
    Signal2_name = ''
    Signal3_name = ''
    EnValue14.set('')
    if (flag_Test_items == 8):
        Signal1_name = str(xls.getCell(entry.get(), 7, 2))
        Signal2_name = str(xls.getCell(entry.get(), 7, 3))
        Signal3_name = ''
    elif(flag_Test_items == 9):
        Signal1_name = str(xls.getCell(entry.get(), 2, 1))
        Signal2_name = str(xls.getCell(entry.get(), 2, 2))
        Signal3_name = str(xls.getCell(entry.get(), 2, 3))
    elif (flag_Test_items == 10):
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
    """if(flag_Test_items == 9):
        print(Signal3_name)
        EnValue12.set(Signal3_name)
        EnValue13.set(Signal3_name)"""

    EnValue9.set(int(m-7))
    if(flag_Test_items == 8):
        EnValue11.set(int(m - 1))
    elif(flag_Test_items == 9):
        EnValue11.set(int(m - 6))
    elif (flag_Test_items == 10):
        EnValue11.set(int(m + 13))
    else:
        EnValue11.set(int(m))




##################################################################################

def common_set():
    osc.state('stop')   #按下STOP按钮
    osc.persistence('OFF')  # 关闭累积
    osc.cursor('OFF')  # 关闭cursor
    # osc.hormode('MAN')  # 设置 Horizontal格式
    osc.coupling('CH1', 'DC')   #设置耦合方式：DC耦合
    osc.coupling('CH2', 'DC')
    osc.channel('OFF', 'OFF', 'OFF', 'OFF', 'OFF', 'OFF')
    osc.measOff(1)
    osc.measOff(2)
    osc.measOff(3)
    osc.measOff(4)
    osc.measOff(5)
    osc.measOff(6)
    osc.measOff(7)
    osc.measOff(8)
    if DPO7000 == 1:
        osc.write('HORIZONTAL:ROLL OFF')
    if DPO5104B == 1:
        osc.write('HORIZONTAL:ROLL OFF')
    osc.state('run')

def channel_Lable_set():
    global flag_Test_items
    #osc.write('DISplay:GLObal:CH1:STATE ON')  # 打开通道1
    #osc.write('DISplay:GLObal:CH2:STATE ON')  # 打开通道2
    osc.label('CH1', entry1.get(), 10, 40)  # 设置label
    osc.label('CH2', entry2.get(), 10, 40)  # 设置label
    #osc.write('DISplay:GLObal:CH3:STATE ON')  # 打开通道3
    osc.label('CH3', entry6.get(), 10, 40)  # 设置label
    """if(flag_Test_items == 9):
        osc.write('DISplay:GLObal:CH3:STATE ON')  # 打开通道3
        osc.label('CH3', entry6.get(), 10, 40)  # 设置label"""
def measure1():
    if MSO5 == 1:
        osc.measure_1(1, 'CH1', 'Top')
        osc.measure_1(2, 'CH1', 'Base')
        osc.measure_1(3, 'CH2', 'Top')
        osc.measure_1(4, 'CH2', 'Base')
        osc.measure_delay(7,'CH1','CH2','DELAY','RISE','RISE',90,10,'RISEMid')
        osc.measure_1(5, 'CH1', 'MAXimum')
        osc.measure_1(6, 'CH1', 'Minimum')
        osc.measure_1(8, 'CH2', 'MAXimum')
        osc.measure_1(9, 'CH2', 'Minimum')

    else:
        osc.measure(1, 'CH1', 'Top',1)
        osc.measure(2, 'CH1', 'Base',1)
        osc.measure(3, 'CH2', 'Top',1)
        osc.measure(4, 'CH2', 'Base',1)

        osc.measure(7, 'CH1', 'DELAY', 1)
        osc.measure(7, 'CH2', 'DELAY', 2)
        osc.write('MEASUREMENT:MEAS%d:DELAY:EDGE %s' % (7, 'RISE'))

        osc.write('MEASUREMENT:MEAS%d:TOEdge %s' % (7, 'RISE'))
        osc.write('MEASUrement:MEAS%d:GLOBalref 0' % (7))
        osc.write('MEASUrement:MEAS%d:REFLevels1:PERCent:TYPE CUSTom' % (7))
        osc.write('MEASUrement:MEAS%d:REFLevels2:PERCent:TYPE CUSTom' % (7))
        osc.write('MEASUrement:MEAS%d:REFLevels1:PERCent:%s %d', 7, 'RISEMid', 90)

        osc.write('MEASUrement:MEAS%d:REFLevels2:PERCent:%s %d', 7, 'RISEMid', 10)

        osc.measure(5, 'CH1', 'MAXimum',1)
        osc.measure(6, 'CH1', 'Minimum',1)
        osc.measure(8, 'CH2', 'MAXimum',1)
        osc.measure(9, 'CH2', 'Minimum',1)
    osc.trigger('NORMAL', 'CH1', 'RISE', 0.5)
def measure2():
    if MSO5 == 1:
        osc.measure_1(1, 'CH1', 'Top')
        osc.measure_1(2, 'CH1', 'Base')
        osc.measure_1(3, 'CH2', 'Top')
        osc.measure_1(4, 'CH2', 'Base')

        osc.measure_delay(7, 'CH1', 'CH2', 'DELAY', 'FALL', 'FALL', 10, 90, 'FALLMid')
        osc.measure_1(5, 'CH1', 'MAXimum')
        osc.measure_1(6, 'CH1', 'Minimum')
        osc.measure_1(8, 'CH2', 'MAXimum')
        osc.measure_1(9, 'CH2', 'Minimum')
    else:
        osc.measure(1, 'CH1', 'Top',1)
        osc.measure(2, 'CH1', 'Base',1)
        osc.measure(3, 'CH2', 'Top',1)
        osc.measure(4, 'CH2', 'Base',1)

        osc.measure(7, 'CH1', 'DELAY', 1)
        osc.measure(7, 'CH2', 'DELAY', 2)
        osc.write('MEASUREMENT:MEAS%d:DELAY:EDGE %s ' % (7, 'FALL'))
        osc.write('MEASUREMENT:MEAS%d:TOEdge %s ' % (7, 'FALL'))
        osc.write('MEASUrement:MEAS%d:GLOBalref 0' % (7))
        osc.write('MEASUrement:MEAS%d:REFLevels1:PERCent:TYPE CUSTom' % (7))
        osc.write('MEASUrement:MEAS%d:REFLevels2:PERCent:TYPE CUSTom' % (7))
        osc.write('MEASUrement:MEAS%d:REFLevels1:PERCent:%s %d', 7, 'FALLMid', 10)
        osc.write('MEASUrement:MEAS%d:REFLevels2:PERCent:%s %d', 7, 'FALLMid', 90)

        osc.measure(5, 'CH1', 'MAXimum', 1)
        osc.measure(6, 'CH1', 'Minimum', 1)
        osc.measure(8, 'CH2', 'MAXimum', 1)
        osc.measure(9, 'CH2', 'Minimum', 1)
    osc.trigger('NORMAL', 'CH1', 'FALL', 0.5)

def measure3():
    if MSO5 == 1:
        osc.measure_1(1, 'CH1', 'Top')
        osc.measure_1(2, 'CH1', 'Base')
        osc.measure_1(3, 'CH2', 'Top')
        osc.measure_1(4, 'CH2', 'Base')
        osc.measure_delay(7, 'CH1', 'CH2', 'DELAY', 'FALL', 'FALL', 10, 90, 'FALLMid')
        osc.measure_1(5, 'CH1', 'MAXimum')
        osc.measure_1(6, 'CH1', 'Minimum')
        osc.measure_1(8, 'CH2', 'MAXimum')
        osc.measure_1(9, 'CH2', 'Minimum')

    else:
        osc.measure(1, 'CH1', 'Top',1)
        osc.measure(2, 'CH1', 'Base',1)
        osc.measure(3, 'CH2', 'Top',1)
        osc.measure(4, 'CH2', 'Base',1)
        osc.measure(7, 'CH1', 'DELAY', 1)
        osc.measure(7, 'CH2', 'DELAY', 2)
        osc.write('MEASUREMENT:MEAS%d:DELAY:EDGE %s ' % (7, 'FALL'))
        osc.write('MEASUREMENT:MEAS%d:TOEdge %s ' % (7, 'FALL'))
        osc.write('MEASUrement:MEAS%d:GLOBalref 0' % (7))
        osc.write('MEASUrement:MEAS%d:REFLevels1:PERCent:TYPE CUSTom' % (7))
        osc.write('MEASUrement:MEAS%d:REFLevels2:PERCent:TYPE CUSTom' % (7))
        osc.write('MEASUrement:MEAS%d:REFLevels1:PERCent:%s %d', 7, 'FALLMid', 10)
        osc.write('MEASUrement:MEAS%d:REFLevels2:PERCent:%s %d', 7, 'FALLMid', 90)

        osc.measure(5, 'CH1', 'MAXimum', 1)
        osc.measure(6, 'CH1', 'Minimum', 1)
        osc.measure(8, 'CH2', 'MAXimum', 1)
        osc.measure(9, 'CH2', 'Minimum', 1)
    osc.trigger('NORMAL', 'CH1', 'FALL', 0.5)
def measure4():
    if MSO5 == 1:
        osc.measure_1(1, 'CH1', 'Top')
        osc.measure_1(2, 'CH1', 'Base')
        osc.measure_1(3, 'CH2', 'Top')
        osc.measure_1(4, 'CH2', 'Base')

    else:
        osc.measure(1, 'CH1', 'Top',1)
        osc.measure(2, 'CH1', 'Base',1)
        osc.measure(3, 'CH2', 'Top',1)
        osc.measure(4, 'CH2', 'Base',1)

    osc.trigger('NORMAL', 'CH2', 'RISE', 0.5)
def measure5():
    if MSO5 == 1:
        osc.measure_1(1, 'CH1', 'Top')
        osc.measure_1(2, 'CH1', 'Base')
        osc.measure_1(3, 'CH2', 'Top')
        osc.measure_1(4, 'CH2', 'Base')
        osc.measure_1(5, 'CH3', 'Top')
        osc.measure_1(6, 'CH3', 'Base')

    else:
        osc.measure(1, 'CH1', 'Top',1)
        osc.measure(2, 'CH1', 'Base',1)
        osc.measure(3, 'CH2', 'Top',1)
        osc.measure(4, 'CH2', 'Base',1)
        osc.measure(5, 'CH3', 'Top', 1)
        osc.measure(6, 'CH3', 'Base', 1)
    osc.trigger('NORMAL', 'CH1', 'RISE', 0.5)
def measure6():
    if MSO5 == 1:
        osc.measure_1(1, 'CH1', 'Top')
        osc.measure_1(2, 'CH1', 'Base')
        osc.measure_1(5, 'CH1', 'MAXimum')
        osc.measure_1(6, 'CH1', 'Minimum')
        osc.measure_1(10, 'CH1', 'RISETIME')
        osc.measure_1(11, 'CH1', 'FALLTIME')

    else:
        osc.measure(1, 'CH1', 'Top',1)
        osc.measure(2, 'CH1', 'Base',1)
        osc.measure(5, 'CH1', 'MAXimum', 1)
        osc.measure(6, 'CH1', 'Minimum', 1)
        osc.measure(10, 'CH1', 'RISETIME', 1)
        osc.measure(11, 'CH1', 'FALLTIME', 1)
    osc.trigger('NORMAL', 'CH1', 'RISE', 0.5)
class OscMPO5series:
    def __init__(self, address):
        address = address.strip()
        address = address.rstrip()
        self.osc = rm.open_resource(address)

    def state(self, state):
        if state == 'run':
            self.osc.write('DIS:PERS:RESET')  # clear
            self.osc.write('ACQUIRE:STOPAFTER RUNSTOP')
            self.osc.write('ACQUIRE:STATE RUN')
        elif state == 'single':
            self.osc.write('ACQUIRE:STOPAFTER SEQUENCE')  # 按下single
            self.osc.write('ACQUIRE:STATE 1')
        elif state == 'stop':
            self.osc.write('ACQUIRE:STOPAFTER RUNSTOP')
            self.osc.write('ACQUIRE:STATE STOP')

    def measure(self, measNum, channel, type1,source):
        self.osc.write('MEASUREMENT:ADDNEW "MEAS%d"' % measNum)     # 增加测量项measNum
        self.osc.write('MEASUREMENT:MEAS%d:SOURCE%d %s' % (measNum,source,channel))    # 将测量项measNum归属于通道channel
        self.osc.write('MEASUREMENT:MEAS%d:TYPE %s' % (measNum, type1))  # 设置测量内容
        self.osc.write('MEASUrement:MEAS%d:DISPlaystat:ENABle ON' % measNum)    # 显示测量项

    def measure_1(self, measNum, channel, TYPE):
        self.osc.write('MEASUREMENT:ADDNEW "MEAS%d"' % measNum)
        self.osc.write('MEASUREMENT:MEAS%d:TYPE %s' % (measNum, TYPE))
        self.osc.write('MEASUREMENT:MEAS%d:SOURCE1 %s' % (measNum,channel))
    def measure_delay(self,measNum,source1,source2,TYPE,FromEDGE_TYPE,TOEDGE_TYPE,Percent1,Percent2,Mode):
        self.osc.write('MEASUREMENT:ADDNEW "MEAS%d"' % measNum)
        self.osc.write('MEASUREMENT:MEAS%d:TYPE %s' % (measNum, TYPE))

        self.osc.write('MEASUREMENT:MEAS%d:SOURCE1 %s' % (measNum, source1))
        self.osc.write('MEASUREMENT:MEAS%d:SOURCE2 %s' % (measNum, source2))

        self.osc.write('MEASUREMENT:MEAS%d:DELAY:EDGE %s' % (measNum, FromEDGE_TYPE))

        self.osc.write('MEASUREMENT:MEAS%d:TOEdge %s' % (measNum, TOEDGE_TYPE))
        self.osc.write('MEASUrement:MEAS%d:GLOBalref 0' % (measNum))
        self.osc.write('MEASUrement:MEAS%d:REFLevels1:PERCent:TYPE CUSTom' % (measNum))
        self.osc.write('MEASUrement:MEAS%d:REFLevels2:PERCent:TYPE CUSTom' % (measNum))
        self.osc.write('MEASUrement:MEAS%d:REFLevels1:PERCent:%s %d' %(measNum,Mode,Percent1))

        self.osc.write('MEASUrement:MEAS%d:REFLevels2:PERCent:%s %d' %(measNum,Mode,Percent2))
    def measOff(self, measNum):
        self.osc.write('MEASU:DEL "MEAS%d"' % measNum)
        # self.osc.write('MEASUrement:ANNOTate AUTO')

    def makeDir(self, dir1):
        print(dir1)
        self.osc.write('FILESystem:MKDir "%s"' % dir1)

    def export(self, temp1, dir1):
        self.osc.write('SAV:IMAG "%s.%s"' % (dir1, temp1))

    def readfile(self, dir1):
        self.osc.write('FILESYSTEM:READFILE "%s"' % dir1)

    def persistence(self, state):
        self.osc.write('DISplay:PERSistence %s' % state)  # 关闭累积

    def cursor(self, state):
        self.osc.write('CURSOR:STATE %s' % state)  # 关闭cursor

    def hormode(self, state):
        self.osc.write('HOR:MODE %s' % state)  # 设置 Horizontal格式
        self.osc.write('HOR:MODE:%s:CONFIGure HORIZ' % state)
        self.osc.write('DISplay:WAVEView:GRIDTYPE FIXED')  # 设置 Horizontal格式
        self.osc.write('DISplay:WAVEView1:VIEWStyle OVErlay')

    def horpos(self, num):
        self.osc.write('HORIZONTAL:POSITION %d' % num)  # 水平位置

    def coupling(self, channel, state):
        self.osc.write('%s:COUP %s' % (channel, state))

    def number(self, number):
        num = 0
        while num <= number:
            time.sleep(0.1)
            num = self.osc.query('ACQuire:NUMAC?')
            if MSO5 == 1:
                num = num[15:]
            num = int(num)

    def record(self, num):
        num = num * 1.25
        self.osc.write('HOR:MODE:RECO %d' % num)

    def query(self, query):
        self.osc.query('%s' % query)
        return self.osc.query('%s' % query)

    def write(self, write):
        self.osc.write('%s' % write)

    def scale(self, channel, num):
        self.osc.write('%s:SCALE %.3f' % (channel, num))

    def channel_state(self, ch1, ch2, ch3, ch4,):
        self.osc.write('SELECT:CH4 %s' % ch4)
        self.osc.write('SELECT:CH3 %s' % ch3)
        self.osc.write('SELECT:CH2 %s' % ch2)
        self.osc.write('SELECT:CH1 %s' % ch1)

    def label(self, channel, name, xi, y):
        self.osc.write('%s:LABel:NAMe "%s"' % (channel, name))  # 设置label
        xi_new = xi
        #xi_new = 348 * xi - 174
        y_new = y
        self.osc.write('%s:LABel:XPOS %.1f' % (channel, xi_new))
        self.osc.write('%s:LABel:YPOS %.1f' % (channel, y_new))
        self.osc.write('%s:LABel:FONT:BOLD OFF' % channel)
        self.osc.write('%s:LABel:FONT:ITALic OFF' % channel)
        self.osc.write('%s:LABel:FONT:SIZE 14' % channel)
        self.osc.write('%s:LABel:FONT:UNDERline OFF' % channel)

    def chanset(self, channel, pos, offset, bandwidth, scale):
        self.osc.write('%s:POS %.1f' % (channel, pos))  # 竖直位置
        self.osc.write('%s:OFFSET %.2f' % (channel, offset))  # 设置offset
        self.osc.write('%s:BANDWIDTH %s' % (channel, bandwidth))  # 一通道带宽设置为20MHz
        self.osc.write('%s:SCALE %.3f' % (channel, scale))  # 设置一通道的scale

    def trigger(self, mode, channel, slope, level):
        self.osc.write('TRIGGER:A:MODE %s' % mode)
        self.osc.write('TRIGGER:A:EDGE:SOURCE %s' % channel)
        self.osc.write('TRIGGER:A:EDGE:SLOPE %s' % slope)  # 设置触发频道和形式
        self.osc.write('TRIGGER:A:LEVEL:%s %.3f' % (channel, level))

    def math(self, channel, define, offset, pos, scale):
        self.osc.write('MATH:%s:DEFINE "%s"' % (channel, define))
        self.osc.write('MATH:%s:VERT:AUTOSC OFF' % channel)

        self.osc.write('MATH:%s:OFFSET %.1f' % (channel, offset))  # 设置offset

        self.osc.write('DISplay:WAVEView1:MATH:%s:VERTICAL:POSITION %.1f' % (channel, pos))  # 设置math通道的position

        self.osc.write('DISplay:WAVEView1:MATH:%s:VERTICAL:SCALE %.1f' % (channel, scale))
        # self.osc.write('MATH:ADDNEW "%s"' % channel)  # 开启math通道

    def readraw(self, file_path):
        data = self.osc.read_raw()
        if os.path.exists(file_path):
            # 如果存在同名文件，则在文件名后加上数字后缀M
            count = 1
            basename, ext = os.path.splitext(file_path)
            new_file_path = f"{basename}({count}){ext}"
            while os.path.exists(new_file_path):
                count += 1
                new_file_path = f"{basename}({count}){ext}"
            file_path = new_file_path
        data_temp = open(file_path, 'wb')
        data_temp.write(data)
        data_temp.close()
        data = file_path
        return data

class OscDPO7000C:
    def __init__(self, address):
        address = address.strip()
        address = address.rstrip()
        self.osc = rm.open_resource(address)

    def state(self, state):
        if state == 'run':
            self.osc.write('DIS:PERS:RESET')  # clear
            self.osc.write('ACQUIRE:STOPAFTER RUNSTOP')
            self.osc.write('ACQUIRE:STATE RUN')
        elif state == 'single':
            self.osc.write('ACQUIRE:STOPAFTER SEQUENCE')  # 按下single
            self.osc.write('ACQUIRE:STATE 1')
        elif state == 'stop':
            self.osc.write('ACQUIRE:STOPAFTER RUNSTOP')
            self.osc.write('ACQUIRE:STATE STOP')
        else:
            print('状态设置失败')

    def measure(self, measNum, channel, type1, source):
        self.osc.write('MEASUREMENT:ADDNEW "MEAS%d"' % measNum)  # 增加测量项measNum
        self.osc.write('MEASUREMENT:MEAS%d:SOURCE%d %s' % (measNum, source, channel))  # 将测量项measNum归属于通道channel
        self.osc.write('MEASUREMENT:MEAS%d:TYPE %s' % (measNum, type1))  # 设置测量内容
        self.osc.write('MEASUrement:MEAS%d:DISPlaystat:ENABle ON' % measNum)  # 显示测量项

    def measOff(self, measNum):
        self.osc.write('MEASUrement:MEAS%d:STATE OFF' % measNum)
        self.osc.write('MEASUrement:ANNOTate AUTO')

    def makeDir(self, dir1):
        self.osc.write('FILESystem:MKDir "%s"' % dir1)

    def export(self, temp1, dir1):
        self.osc.write('EXPort:FORMat %s' % temp1)
        self.osc.write('EXPORT:FILENAME "%s"' % dir1)  # 保存图片
        self.osc.write('EXPort STARt')

    def readfile(self, dir1):
        self.osc.write('FILESYSTEM:READFILE "%s"' % dir1)

    def persistence(self, state):
        self.osc.write('DISplay:PERSistence %s' % state)  # 关闭累积

    def cursor(self, state):
        self.osc.write('CURSOR:STATE %s' % state)  # 关闭cursor

    def hormode(self, state):
        self.osc.write('HOR:MODE %s' % state)  # 设置 Horizontal格式

    def horpos(self, num):
        self.osc.write('HORIZONTAL:POSITION %d' % num)  # 水平位置

    def coupling(self, channel, state):
        self.osc.write('%s:COUP %s' % (channel, state))

    def number(self, number):
        num = 0
        while num <= number:

            num = self.osc.query('ACQuire:NUMAC?')
            num = int(num)

    def record(self, num):
        self.osc.write('HOR:MODE:RECO %d' % num)

    def query(self, query):
        self.osc.query('%s' % query)
        return self.osc.query('%s' % query)

    def write(self, write):
        self.osc.write('%s' % write)

    def readraw(self, file_path):
        data = self.osc.read_raw()
        if os.path.exists(file_path):
            # 如果存在同名文件，则在文件名后加上数字后缀M
            count = 1
            basename, ext = os.path.splitext(file_path)
            new_file_path = f"{basename}({count}){ext}"
            while os.path.exists(new_file_path):
                count += 1
                new_file_path = f"{basename}({count}){ext}"
            file_path = new_file_path
        data_temp = open(file_path, 'wb')
        data_temp.write(data)
        data_temp.close()
        data = file_path
        return data

    def scale(self, channel, num):
        self.osc.write('%s:SCALE %.3f' % (channel, num))

    def channel_state(self, ch1, ch2, ch3, ch4):
        self.osc.write('SELECT:CH4 %s' % ch4)
        self.osc.write('SELECT:CH3 %s' % ch3)
        self.osc.write('SELECT:CH2 %s' % ch2)
        self.osc.write('SELECT:CH1 %s' % ch1)

    def label(self, channel, name, xi, y):
        self.osc.write('%s:LABel:NAMe "%s"' % (channel, name))  # 设置label
        self.osc.write('%s:LABel:XPOS %.1f' % (channel, xi))
        self.osc.write('%s:LABel:YPOS %.1f' % (channel, y))

    def chanset(self, channel, pos, offset, bandwidth, scale):
        self.osc.write('%s:POS %.1f' % (channel, pos))  # 竖直位置
        self.osc.write('%s:OFFSET %.2f' % (channel, offset))  # 设置offset
        self.osc.write('%s:BANDWIDTH %s' % (channel, bandwidth))  # 一通道带宽设置为20MHz
        self.osc.write('%s:SCALE %.3f' % (channel, scale))  # 设置一通道的scale

    def trigger(self, mode, channel, slope, level):
        self.osc.write('TRIGGER:A:MODE %s' % mode)
        self.osc.write('TRIGGER:A:EDGE:SOURCE %s' % channel)
        self.osc.write('TRIGGER:A:EDGE:SLOPE %s' % slope)  # 设置触发频道和形式
        self.osc.write('TRIGGER:A:LEVEL %.2f' % level)

    def math(self, channel, define, offset, pos, scale):
        self.osc.write('%s:DEFINE "%s"' % (channel, define))
        self.osc.write('%s:VERT:AUTOSC OFF' % channel)
        self.osc.write('%s:OFFSET %.2f' % (channel, offset))  # 设置offset
        self.osc.write('%s:VERTICAL:POSITION %.2f' % (channel, pos))  # 设置math通道的position
        self.osc.write('%s:VERTICAL:SCALE %.2f' % (channel, scale))
        self.osc.write('SELECT:%s ON' % channel)  # 开启math通道

class OscDPO5104B:
    def __init__(self, address):
        address = address.strip()
        address = address.rstrip()
        self.osc = rm.open_resource(address)

    def state(self, state):
        if state == 'run':
            self.osc.write('DIS:PERS:RESET')  # clear
            self.osc.write('ACQUIRE:STOPAFTER RUNSTOP')
            self.osc.write('ACQUIRE:STATE RUN')
        elif state == 'single':
            self.osc.write('ACQUIRE:STOPAFTER SEQUENCE')  # 按下single
            self.osc.write('ACQUIRE:STATE 1')
        elif state == 'stop':
            self.osc.write('ACQUIRE:STOPAFTER RUNSTOP')
            self.osc.write('ACQUIRE:STATE STOP')
        else:
            print('状态设置失败')

    def measure(self, measNum, channel, type1, source):
        self.osc.write('MEASUREMENT:ADDNEW "MEAS%d"' % measNum)  # 增加测量项measNum
        self.osc.write('MEASUREMENT:MEAS%d:SOURCE%d %s' % (measNum, source, channel))  # 将测量项measNum归属于通道channel
        self.osc.write('MEASUREMENT:MEAS%d:TYPE %s' % (measNum, type1))  # 设置测量内容
        self.osc.write('MEASUrement:MEAS%d:DISPlaystat:ENABle ON' % measNum)  # 显示测量项

    def measOff(self, measNum):
        self.osc.write('MEASUrement:MEAS%d:STATE OFF' % measNum)
        self.osc.write('MEASUrement:ANNOTate AUTO')

    def makeDir(self, dir1):
        self.osc.write('FILESystem:MKDir "%s"' % dir1)

    def export(self, temp1, dir1):
        self.osc.write('EXPort:FORMat %s' % temp1)
        self.osc.write('EXPORT:FILENAME "%s"' % dir1)  # 保存图片
        self.osc.write('EXPort STARt')

    def readfile(self, dir1):
        self.osc.write('FILESYSTEM:READFILE "%s"' % dir1)

    def persistence(self, state):
        self.osc.write('DISplay:PERSistence %s' % state)  # 关闭累积

    def cursor(self, state):
        self.osc.write('CURSOR:STATE %s' % state)  # 关闭cursor

    def hormode(self, state):
        self.osc.write('HOR:MODE %s' % state)  # 设置 Horizontal格式

    def horpos(self, num):
        self.osc.write('HORIZONTAL:POSITION %d' % num)  # 水平位置

    def coupling(self, channel, state):
        self.osc.write('%s:COUP %s' % (channel, state))

    def number(self, number):
        num = 0
        while num <= number:

            num = self.osc.query('ACQuire:NUMAC?')
            num = int(num)

    def record(self, num):
        self.osc.write('HOR:MODE:RECO %d' % num)

    def query(self, query):
        self.osc.query('%s' % query)
        return self.osc.query('%s' % query)

    def write(self, write):
        self.osc.write('%s' % write)

    def readraw(self, file_path):
        data = self.osc.read_raw()
        if os.path.exists(file_path):
            # 如果存在同名文件，则在文件名后加上数字后缀M
            count = 1
            basename, ext = os.path.splitext(file_path)
            new_file_path = f"{basename}({count}){ext}"
            while os.path.exists(new_file_path):
                count += 1
                new_file_path = f"{basename}({count}){ext}"
            file_path = new_file_path
        data_temp = open(file_path, 'wb')
        data_temp.write(data)
        data_temp.close()
        data = file_path
        return data

    def scale(self, channel, num):
        self.osc.write('%s:SCALE %.3f' % (channel, num))

    def channel_state(self, ch1, ch2, ch3, ch4):
        self.osc.write('SELECT:CH4 %s' % ch4)
        self.osc.write('SELECT:CH3 %s' % ch3)
        self.osc.write('SELECT:CH2 %s' % ch2)
        self.osc.write('SELECT:CH1 %s' % ch1)

    def label(self, channel, name, xi, y):
        self.osc.write('%s:LABel:NAMe "%s"' % (channel, name))  # 设置label
        self.osc.write('%s:LABel:XPOS %.1f' % (channel, xi))
        self.osc.write('%s:LABel:YPOS %.1f' % (channel, y))

    def chanset(self, channel, pos, offset, bandwidth, scale):
        self.osc.write('%s:POS %.1f' % (channel, pos))  # 竖直位置
        self.osc.write('%s:OFFSET %.2f' % (channel, offset))  # 设置offset
        self.osc.write('%s:BANDWIDTH %s' % (channel, bandwidth))  # 一通道带宽设置为20MHz
        self.osc.write('%s:SCALE %.3f' % (channel, scale))  # 设置一通道的scale

    def trigger(self, mode, channel, slope, level):
        self.osc.write('TRIGGER:A:MODE %s' % mode)
        self.osc.write('TRIGGER:A:EDGE:SOURCE %s' % channel)
        self.osc.write('TRIGGER:A:EDGE:SLOPE %s' % slope)  # 设置触发频道和形式
        self.osc.write('TRIGGER:A:LEVEL %.2f' % level)

    def math(self, channel, define, offset, pos, scale):
        self.osc.write('%s:DEFINE "%s"' % (channel, define))
        self.osc.write('%s:VERT:AUTOSC OFF' % channel)
        self.osc.write('%s:OFFSET %.2f' % (channel, offset))  # 设置offset
        self.osc.write('%s:VERTICAL:POSITION %.2f' % (channel, pos))  # 设置math通道的position
        self.osc.write('%s:VERTICAL:SCALE %.2f' % (channel, scale))
        self.osc.write('SELECT:%s ON' % channel)  # 开启math通道


def instrument():
    global osc, rm, MSO5, DPO7000, DPO5104B,flag_MSOConnect
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
                osc = OscDPO7000C(addr)
                DPO7000 = 1
            str2 = insinf.find('TEKTRONIX,MSO')
            if str2 != -1:
                print('该仪器型号为TEKTRONIX,MSO4/5/6系列示波器，设备连接成功')
                print('地址为' + addr)
                osc = OscMPO5series(addr)
                MSO5 = 1
            str3 = insinf.find('TEKTRONIX,DPO5')
            if str3 != -1:
                print('该仪器型号为TEKTRONIX,DPO5000系列示波器，设备连接成功')
                print('地址为' + addr)
                osc = OscDPO5104B(addr)
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
    global flag_Test_items
    osc.write('FACTORY')
    #common_set()
    osc.write('DISplay:WAVEView1:VIEWStyle OVErlay')    #设置波形显示模式为叠加显示模式
    if(flag_Test_items == 9):
        osc.channel_state('ON', 'ON', 'ON', 'OFF')  # 开启通道1,通道2,通道3
        osc.chanset('CH1', -2.5, 0, '1.0000E+09', 1)  # 设置通道1波形位置，带宽:1GHZ，1V/div
        osc.chanset('CH2', -3.5, 0, '1.0000E+09', 1)
        osc.chanset('CH3', -4.5, 0, '1.0000E+09', 1)
    elif(flag_Test_items == 10):
        osc.channel_state('ON', 'OFF', 'OFF', 'OFF')     #开启通道1,通道2
        osc.chanset('CH1', -2.5, 0, '1.0000E+09', 1)     #设置通道1波形位置，带宽:1GHZ，1V/div

    else:
        osc.channel_state('ON', 'ON', 'OFF', 'OFF')     #开启通道1,通道2
        osc.chanset('CH1', -2.5, 0, '1.0000E+09', 1)     #设置通道1波形位置，带宽:1GHZ，1V/div
        osc.chanset('CH2', -3.5, 0, '1.0000E+09', 1)
    osc.write('HORIZONTAL:MODE AUTO')
    osc.write('HORIZONTAL:MODE:SCALE 1e-2') #10ms/div
    osc.write('HORIZONTAL:POSITION 30') #光标位于30%位置
    if(flag_Test_items == 1 or flag_Test_items == 0):
        measure1()  #增加测量项1~7，CH1 CH2 (MAX MIN RISETIME DELAY)

    if (flag_Test_items == 2 or flag_Test_items == 3 or flag_Test_items == 4 or flag_Test_items == 5 or flag_Test_items == 6):
        measure2()  # 增加测量项1~7，CH1 CH2 (MAX MIN FALLTIME DELAY)
    if (flag_Test_items == 7):
        measure3()
    if (flag_Test_items == 8):
        measure4()
    if(flag_Test_items == 9):
        measure5()
    if (flag_Test_items == 10):
        measure6()
    osc.state('run')

def Set_Lable():
    global flag_MSOConnect,flag_Test_items,xls
    if (flag_MSOConnect == 0):
        messagebox.showerror(title='仪器连接', message='示波器连接错误，请检查!')
    #xls.save()

    channel_Lable_set()

def mkdir(path):
    # 去除首位空格
    path = path.strip()
    # 去除尾部 \ 符号
    path = path.rstrip("\\")

    # 判断路径是否存在
    # 存在     True
    # 不存在   False
    isExists = os.path.exists(path)

    # 判断结果
    if not isExists:
        # 如果不存在则创建目录
        # 创建目录操作函数
        os.makedirs(path)
        print(path + ' 创建成功')
        return True
    else:
        # 如果目录存在则不创建，并提示目录已存在
        print(path + ' 目录已存在')
        return False


def savepic():
    global flag_Test_items
    mkpath = '%s/%s' % (pic_path,entry.get())
    print("-->",mkpath)
    mkdir(mkpath)   # 创建本地文件夹
    if(flag_Test_items != 10):
        if(entry6.get() != ""):
            name = '%s TO %s TO %s' % (entry1.get(), entry2.get() ,entry6.get())
        elif(entry2.get() != ""):
            name = '%s TO %s' % (entry1.get(), entry2.get())
        else:
            name = '%s' % (entry1.get())
    else:
        if(flag_monotony_direction == 1):
            name = '%s_R' % (entry1.get())
        if (flag_monotony_direction == 0):
            name = '%s_F' % (entry1.get())
    file_path = r'%s/%s.PNG' % (mkpath, name)
    osc.makeDir('C:\\%s Test Pictures' % entry4.get())
    osc.makeDir('C:\\%s Test Pictures\\%s' % (entry4.get(),entry.get()))
    osc.export('PNG', 'C:\\%s Test Pictures\\%s\\%s' %  (entry4.get(),entry.get(),name))  # 保存图片
    time.sleep(1.5)
    osc.readfile('C:/%s Test Pictures/%s/%s.PNG' % (entry4.get(), entry.get(), name))
    time.sleep(0.5)
    data = osc.readraw(file_path)
    time.sleep(0.5)
    return data

def Capture_Pic():
    global flag_MSOConnect,delay_time,xls,flag_monotony_direction,Value_TOP,Value_BASE,Value_MAX,Value_MIN,index_i
    if (flag_MSOConnect == 0):
        messagebox.showerror(title='仪器连接', message='示波器连接错误，请检查!')
    xls.save()
    a1_1 = r'%s' % (savepic())
    a1_1 = os.path.abspath(a1_1)
    # savepic('T3-1')  # 保存图片
    # a3_1 = r'%s/POL Test Pictures/%s/%s/T3-1.png' % (pic_path, temp, entry.get())
    # a3_1 = 'D:\\POL Test Pictures\\' + temp + '\\' + entry.get() + r'\Power Up Sequence with NO Load.png'
    #print('a1_1:',a1_1)

    xls.addPicture(entry.get(), a1_1, m,0,0, 0, 0)
    if(flag_Test_items != 8 and flag_Test_items != 9 and flag_Test_items != 10):
        delay_time = osc.query('MEASUrement:MEAS7:MAX?')
        print('query delaytime:', delay_time)
        #print(delay_time)
        if (delay_time.find('MEASUREMENT') != -1):
            if MSO5 == 1:
                delay_time = delay_time[26:]
        #delay_time = float(delay_time)
        delay_time=eval(delay_time)
        delay_time = float(delay_time)
        print('result delaytime:', delay_time)
        #print(delay_time)
        if(abs(delay_time)>=1):
            delay_time = '%.2f' % delay_time
            delay_time = str(delay_time) + 's'
        elif(abs(delay_time)<1 and abs(delay_time)>=0.001):
            delay_time = float(delay_time) * 1000
            delay_time = '%.2f' % delay_time
            delay_time = str(delay_time) + 'ms'
        elif(abs(delay_time) < 0.001 and abs(delay_time) >= 0.000001):
            delay_time = float(delay_time) * 1000000
            delay_time = '%.2f' % delay_time
            delay_time = str(delay_time) + 'μs'
        else:
            delay_time = float(delay_time) * 1000000000
            delay_time = '%.2f' % delay_time
            delay_time = str(delay_time) + 'ns'

        xls.setCell(entry.get(), m, 7, delay_time)
    #delay_time = str(delay_time) + 'ns'
    """delay_time = str(delay_time) + 'μs'
    delay_time = str(delay_time) + 'ms'
    delay_time = str(delay_time) + 's'"""
    #print(delay_time)
    """if (flag_Test_items == 7):
        xls.setCell(entry.get(), m, 5, delay_time)
    else:"""
    if (flag_Test_items == 10):
        Value_TOP = osc.query('MEASUrement:MEAS1:MAX?')
        Value_BASE = osc.query('MEASUrement:MEAS2:MAX?')
        Value_MAX = osc.query('MEASUrement:MEAS5:MAX?')
        Value_MIN = osc.query('MEASUrement:MEAS6:MAX?')
        print('query Value_TOP:', Value_TOP)
        print('query Value_BASE:', Value_BASE)
        print('query Value_MAX:', Value_MAX)
        print('query Value_MIN:', Value_MIN)
        if (Value_TOP.find('MEASUREMENT') != -1):
            if MSO5 == 1:
                Value_TOP = Value_TOP[26:]
        Value_TOP = eval(Value_TOP)
        Value_TOP = float(Value_TOP)
        Value_TOP = '%.4f' % Value_TOP
        if (Value_BASE.find('MEASUREMENT') != -1):
            if MSO5 == 1:
                Value_BASE = Value_BASE[26:]
        Value_BASE = eval(Value_BASE)
        Value_BASE = float(Value_BASE)
        Value_BASE = '%.4f' % Value_BASE
        if (Value_MAX.find('MEASUREMENT') != -1):
            if MSO5 == 1:
                Value_MAX = Value_MAX[26:]
        Value_MAX = eval(Value_MAX)
        Value_MAX = float(Value_MAX)
        Value_MAX = '%.4f' % Value_MAX
        if (Value_MIN.find('MEASUREMENT') != -1):
            if MSO5 == 1:
                Value_MIN = Value_MIN[26:]
        Value_MIN = eval(Value_MIN)
        Value_MIN = float(Value_MIN)
        Value_MIN = '%.4f' % Value_MIN
        if(flag_monotony_direction == 1):
            xls.setCell(entry.get(), m + 13, 9 , Value_TOP)
            xls.setCell(entry.get(), m + 13, 10, Value_BASE)
            xls.setCell(entry.get(), m + 13, 11, Value_MAX)
            xls.setCell(entry.get(), m + 13, 12, Value_MIN)
        if (flag_monotony_direction == 0):
            xls.setCell(entry.get(), m + 13, 13, Value_TOP)
            xls.setCell(entry.get(), m + 13, 14, Value_BASE)
            xls.setCell(entry.get(), m + 13, 15, Value_MAX)
            xls.setCell(entry.get(), m + 13, 16, Value_MIN)
    xls.save()


def test_insertPic():

    print("5--->",'I'+str(m))
    """wb = xw.Book(file_path)
    print(file_path)
    sheet = wb.sheets.active
    #fileName = os.path.join(os.getcwd(),'E:\\Project\\tools\\MSO TOOL\\EE-自动化测试\\PIC\\Power Sequence(G3 to S0)\\P12V_AUX TO P3V3_AUX.PNG')
    picture = sheet.pictures.add('E:\\Project\\tools\\MSO TOOL\\EE-自动化测试\\PIC\\Power Sequence(G3 to S0)\\P12V_AUX TO P3V3_AUX.PNG')
    picture.height /= 2
    picture.width /= 2
    picture.left = 0
    picture.top = 0
    wb.save(file_path)"""


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

    #xls.Close(False)
    """root11 = Toplevel()
    root11.title('保存/退出表格')  # 设置tl在宽和高
    root11.geometry('340x200')
    root11.transient(root)  # 为了区别root和tl，我们向tl中添加了一个Label
    Label(root11, text='该项测试正在开发中，敬请期待...').pack()
    root11.attributes("-topmost", 1)"""


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

global file_path, pic_path, xls,Tests_Sum,flag_Test_items,\
    Signal1_name,Signal2_name,osc,rm,MSO5, DPO7000, DPO5104B,flag_monotony_direction,insinf
flag_Test_items = 0
m = 8
n = 6
Tests_Sum = 999
flag_monotony_direction = 1     #1->Positive    0->Negtive
sheet_Summary = "Summary"
flag_MSOConnect = 0
MSO5 = 0
root = Tk()  # 初始框的声明
root.title('Nettrix Power Sequence Test Tool V2.0          by liujch2')
root.resizable(False, False)
root.geometry('750x700')  # 设置初始框的大小
# root.focus_force() # Take Focus
visa_dll = 'c:/windows/system32/visa32.dll'

image_file = PhotoImage(file='NC logo.png')

image = Label(root, image=image_file)
image.place(x=0, y=10, width=400, height=70)
EnValue1 = StringVar()  #file_path
EnValue2 = StringVar()  #pic_path
EnValue3 = StringVar()  #SheetName
EnValue4 = IntVar()  #Part number
EnValue5 = StringVar()  #Signal1 name
EnValue6 = StringVar()  #Signal2 name
EnValue12 = StringVar()  #Signal3 name
EnValue7 = StringVar()  #CH1 Lable
EnValue8 = StringVar()  #CH2 Lable
EnValue13 = StringVar()  #CH3 Lable
EnValue9 = IntVar()  #Current item
EnValue10 = StringVar() #project name
EnValue11 = IntVar()
EnValue14 = StringVar() #positive or negtive

##################################################################################
theButton = Button(root, text="选择测试报告路径", command=select_excel_path)  # 按下按钮 执行instrument函数
theButton.place(x=10, y=90, width=115, height=30)
Entry(root, show=None, textvariable=EnValue1, state='readonly').place(x=130, y=90, width=250, height=30)

theButton = Button(root, text="选择保存图片路径", command=select_pic_path)  # 按下按钮 执行instrument函数
theButton.place(x=10, y=140, width=115, height=30)
Entry(root, show=None, textvariable=EnValue2, state='readonly').place(x=130, y=140, width=250, height=30)

Label(root, text='Project name：').place(x=00, y=190, width=140, height=30)
entry4 = Entry(root, show=None, width=20,textvariable=EnValue10)
entry4.place(x=130, y=190, width=250, height=30)

Label(root, text='SheetName:').place(x=00, y=230, width=140, height=30)
entry = Entry(root, show=None, width=20, textvariable=EnValue3)
entry.place(x=130, y=230, width=250, height=30)

Label(root, text='Tests Sum：').place(x=00, y=270, width=140, height=30)
entry3 = Entry(root, show=None, width=20,textvariable=EnValue4, state='readonly')
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
entry1 = Entry(root, show=None, width=20,textvariable=EnValue7)
entry1.place(x=130, y=430, width=250, height=30)

Entry(root, show=None, textvariable=EnValue14, state='readonly',justify='center').place(x=390, y=430, width=30, height=30)

Label(root, text='CH2 Lable：').place(x=00, y=470, width=140, height=30)
entry2 = Entry(root, show=None, width=20,textvariable=EnValue8)
entry2.place(x=130, y=470, width=250, height=30)

Label(root, text='CH3 Lable：').place(x=00, y=510, width=140, height=30)
entry6 = Entry(root, show=None, width=20,textvariable=EnValue13)
entry6.place(x=130, y=510, width=250, height=30)

Label(root, text='跳转测试项：').place(x=00, y=550, width=140, height=30)
entry5 = Entry(root, show=None, width=20,textvariable=EnValue11)
entry5.place(x=130, y=550, width=100, height=30)

theButton18 =Button(root, text="跳转", command=jump).place(x=280, y=550, width=50, height=30)

theButton11 = Button(root, text="连接仪器", command=instrument).place(x=415, y=570, width=80,height=30)  # 按下按钮 执行instrument函数

theButton12 = Button(root, text='保存并退出表格', command=tl11, activeforeground='white', activebackground='red').place(
    x=515, y=570, width=100, height=30)  # 退出按钮的设计

theButton13 =Button(root, text="<--", command=Last).place(x=415, y=510, width=80, height=30)

theButton14 =Button(root, text="-->", command=Next).place(x=525, y=510, width=80, height=30)

theButton15 =Button(root, text="保存图片", command=Capture_Pic).place(x=635, y=570, width=80, height=30)

theButton16 =Button(root, text="Set Lable", command=Set_Lable).place(x=635, y=510, width=80, height=30)

theButton17 =Button(root, text="Set_MSO", command=MSO_set).place(x=635, y=630, width=80, height=30)

group = LabelFrame(root, text='Power on 测试项', padx=5, pady=5)
group.place(x=450, y=30, width=280, height=470)
theButton01 = Button(group, text="CPU Power Sequence(G3 to S0)", command=tl1)  # 按下按钮 打开tl1界面
theButton01.grid(row=1, column=1, sticky=E + W, padx=20, pady=5)
theButton02 = Button(group, text="CPU Power Sequence(S0-S5-S0)", command=tl2)  # 按下按钮 打开tl2界面
theButton02.grid(row=2, column=1, sticky=E + W, padx=20, pady=5)
theButton03 = Button(group, text="CPU Power Sequence(S0 GLO RST)", command=tl3)  # 按下按钮 打开tl3界面
theButton03.grid(row=3, column=1, sticky=E + W, padx=20, pady=5)
theButton04 = Button(group, text="CPU Power Sequence(WARM RESET)", command=tl4)  # 按下按钮 打开tl4界面
theButton04.grid(row=4, column=1, sticky=E + W, padx=20, pady=5)
theButton05 = Button(group, text="CPU Power Sequence(S5 GLO RST)", command=tl5)  # 按下按钮 打开tl5界面
theButton05.grid(row=5, column=1, sticky=E + W, padx=20, pady=5)
theButton06 = Button(group, text="CPU Power Sequence(THERMTRIP)", command=tl6)  # 按下按钮 打开tl6界面
theButton06.grid(row=6, column=1, sticky=E + W, padx=20, pady=5)
theButton19 = Button(group, text="CPU Power Sequence(S5 to G3)", command=tl12)  # 按下按钮 打开tl6界面
theButton19.grid(row=7, column=1, sticky=E + W, padx=20, pady=5)
theButton07 = Button(group, text="CPU LVT", command=tl7)  # 按下按钮 打开tl7界面
theButton07.grid(row=8, column=1, sticky=E + W, padx=20, pady=5)
theButton08 = Button(group, text="CPU HW Strap", command=tl8)  # 按下按钮 打开tl8界面
theButton08.grid(row=9, column=1, sticky=E + W, padx=20, pady=5)
theButton09 = Button(group, text="CPU PG&EN", command=tl9)  # 按下按钮 打开tl9界面
theButton09.grid(row=10, column=1, sticky=E + W, padx=20, pady=5)
theButton10 = Button(group, text="CPU Monotony", command=tl10)  # 按下按钮 打开tl9界面
theButton10.grid(row=11, column=1, sticky=E + W, padx=20, pady=5)
1
##################################################################################
root.mainloop()

#20240710
#待优化：
#1.增加信号跳转-ok
#2.增加自动读取sheet name，通过下拉选择
#3.保存并退出表格：仅保存、保存并退出
#4.自适应标签位置-ok
#插入图片之前清除单元格格式-OK
#20240808
#1.测LVT/Monotony保存图片时弹出选择保存的图片时R/F，根据选择插入图片至相应位置
#2.测Monotony时填写相关数据
#3.增加CPU测试和BMC测试区分