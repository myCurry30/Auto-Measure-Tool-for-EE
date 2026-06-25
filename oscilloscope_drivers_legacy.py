"""示波器驱动类 - tkinter 版本。

包含 OscMPO5series, OscDPO7000C, OscDPO5104B 三个驱动。
"""
import time
import os


class OscMPO5series:
    """Tektronix MSO4/5/6 系列示波器驱动。"""

    def __init__(self, address, resource_manager):
        address = address.strip().rstrip()
        self.osc = resource_manager.open_resource(address)

    def state(self, state):
        if state == 'run':
            self.osc.write('DIS:PERS:RESET')
            self.osc.write('ACQUIRE:STOPAFTER RUNSTOP')
            self.osc.write('ACQUIRE:STATE RUN')
        elif state == 'single':
            self.osc.write('ACQUIRE:STOPAFTER SEQUENCE')
            self.osc.write('ACQUIRE:STATE 1')
        elif state == 'stop':
            self.osc.write('ACQUIRE:STOPAFTER RUNSTOP')
            self.osc.write('ACQUIRE:STATE STOP')

    def measure(self, measNum, channel, type1, source):
        self.osc.write('MEASUREMENT:ADDNEW "MEAS%d"' % measNum)
        self.osc.write('MEASUREMENT:MEAS%d:SOURCE%d %s' % (measNum, source, channel))
        self.osc.write('MEASUREMENT:MEAS%d:TYPE %s' % (measNum, type1))
        self.osc.write('MEASUrement:MEAS%d:DISPlaystat:ENABle ON' % measNum)

    def measure_1(self, measNum, channel, TYPE):
        self.osc.write('MEASUREMENT:ADDNEW "MEAS%d"' % measNum)
        self.osc.write('MEASUREMENT:MEAS%d:TYPE %s' % (measNum, TYPE))
        self.osc.write('MEASUREMENT:MEAS%d:SOURCE1 %s' % (measNum, channel))

    def measure_delay(self, measNum, source1, source2, TYPE, FromEDGE_TYPE, TOEDGE_TYPE, Percent1, Percent2, Mode):
        self.osc.write('MEASUREMENT:ADDNEW "MEAS%d"' % measNum)
        self.osc.write('MEASUREMENT:MEAS%d:TYPE %s' % (measNum, TYPE))
        self.osc.write('MEASUREMENT:MEAS%d:SOURCE1 %s' % (measNum, source1))
        self.osc.write('MEASUREMENT:MEAS%d:SOURCE2 %s' % (measNum, source2))
        self.osc.write('MEASUREMENT:MEAS%d:DELAY:EDGE %s' % (measNum, FromEDGE_TYPE))
        self.osc.write('MEASUREMENT:MEAS%d:TOEdge %s' % (measNum, TOEDGE_TYPE))
        self.osc.write('MEASUrement:MEAS%d:GLOBalref 0' % (measNum))
        self.osc.write('MEASUrement:MEAS%d:REFLevels1:PERCent:TYPE CUSTom' % (measNum))
        self.osc.write('MEASUrement:MEAS%d:REFLevels2:PERCent:TYPE CUSTom' % (measNum))
        self.osc.write('MEASUrement:MEAS%d:REFLevels1:PERCent:%s %d' % (measNum, Mode, Percent1))
        self.osc.write('MEASUrement:MEAS%d:REFLevels2:PERCent:%s %d' % (measNum, Mode, Percent2))

    def measOff(self, measNum):
        self.osc.write('MEASU:DEL "MEAS%d"' % measNum)

    def makeDir(self, dir1):
        print(dir1)
        self.osc.write('FILESystem:MKDir "%s"' % dir1)

    def export(self, temp1, dir1):
        self.osc.write('SAV:IMAG "%s.%s"' % (dir1, temp1))

    def readfile(self, dir1):
        self.osc.write('FILESYSTEM:READFILE "%s"' % dir1)

    def persistence(self, state):
        self.osc.write('DISplay:PERSistence %s' % state)

    def cursor(self, state):
        self.osc.write('CURSOR:STATE %s' % state)

    def hormode(self, state):
        self.osc.write('HOR:MODE %s' % state)
        self.osc.write('HOR:MODE:%s:CONFIGure HORIZ' % state)
        self.osc.write('DISplay:WAVEView:GRIDTYPE FIXED')
        self.osc.write('DISplay:WAVEView1:VIEWStyle OVErlay')

    def horpos(self, num):
        self.osc.write('HORIZONTAL:POSITION %d' % num)

    def coupling(self, channel, state):
        self.osc.write('%s:COUP %s' % (channel, state))

    def number(self, number):
        num = 0
        while num <= number:
            time.sleep(0.1)
            num = self.osc.query('ACQuire:NUMAC?')
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

    def channel_state(self, ch1, ch2, ch3, ch4):
        self.osc.write('SELECT:CH4 %s' % ch4)
        self.osc.write('SELECT:CH3 %s' % ch3)
        self.osc.write('SELECT:CH2 %s' % ch2)
        self.osc.write('SELECT:CH1 %s' % ch1)

    def label(self, channel, name, xi, y):
        self.osc.write('%s:LABel:NAMe "%s"' % (channel, name))
        self.osc.write('%s:LABel:XPOS %.1f' % (channel, xi))
        self.osc.write('%s:LABel:YPOS %.1f' % (channel, y))
        self.osc.write('%s:LABel:FONT:BOLD OFF' % channel)
        self.osc.write('%s:LABel:FONT:ITALic OFF' % channel)
        self.osc.write('%s:LABel:FONT:SIZE 14' % channel)
        self.osc.write('%s:LABel:FONT:UNDERline OFF' % channel)

    def chanset(self, channel, pos, offset, bandwidth, scale):
        self.osc.write('%s:POS %.1f' % (channel, pos))
        self.osc.write('%s:OFFSET %.2f' % (channel, offset))
        self.osc.write('%s:BANDWIDTH %s' % (channel, bandwidth))
        self.osc.write('%s:SCALE %.3f' % (channel, scale))

    def trigger(self, mode, channel, slope, level):
        self.osc.write('TRIGGER:A:MODE %s' % mode)
        self.osc.write('TRIGGER:A:EDGE:SOURCE %s' % channel)
        self.osc.write('TRIGGER:A:EDGE:SLOPE %s' % slope)
        self.osc.write('TRIGGER:A:LEVEL:%s %.3f' % (channel, level))

    def math(self, channel, define, offset, pos, scale):
        self.osc.write('MATH:%s:DEFINE "%s"' % (channel, define))
        self.osc.write('MATH:%s:VERT:AUTOSC OFF' % channel)
        self.osc.write('MATH:%s:OFFSET %.1f' % (channel, offset))
        self.osc.write('DISplay:WAVEView1:MATH:%s:VERTICAL:POSITION %.1f' % (channel, pos))
        self.osc.write('DISplay:WAVEView1:MATH:%s:VERTICAL:SCALE %.1f' % (channel, scale))

    def readraw(self, file_path):
        data = self.osc.read_raw()
        if os.path.exists(file_path):
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
        return file_path


class OscDPO7000C:
    """Tektronix DPO7000 系列示波器驱动。"""

    def __init__(self, address, resource_manager):
        address = address.strip().rstrip()
        self.osc = resource_manager.open_resource(address)

    def state(self, state):
        if state == 'run':
            self.osc.write('DIS:PERS:RESET')
            self.osc.write('ACQUIRE:STOPAFTER RUNSTOP')
            self.osc.write('ACQUIRE:STATE RUN')
        elif state == 'single':
            self.osc.write('ACQUIRE:STOPAFTER SEQUENCE')
            self.osc.write('ACQUIRE:STATE 1')
        elif state == 'stop':
            self.osc.write('ACQUIRE:STOPAFTER RUNSTOP')
            self.osc.write('ACQUIRE:STATE STOP')
        else:
            print('状态设置失败')

    def measure(self, measNum, channel, type1, source):
        self.osc.write('MEASUREMENT:ADDNEW "MEAS%d"' % measNum)
        self.osc.write('MEASUREMENT:MEAS%d:SOURCE%d %s' % (measNum, source, channel))
        self.osc.write('MEASUREMENT:MEAS%d:TYPE %s' % (measNum, type1))
        self.osc.write('MEASUrement:MEAS%d:DISPlaystat:ENABle ON' % measNum)

    def measOff(self, measNum):
        self.osc.write('MEASUrement:MEAS%d:STATE OFF' % measNum)
        self.osc.write('MEASUrement:ANNOTate AUTO')

    def makeDir(self, dir1):
        self.osc.write('FILESystem:MKDir "%s"' % dir1)

    def export(self, temp1, dir1):
        self.osc.write('EXPort:FORMat %s' % temp1)
        self.osc.write('EXPORT:FILENAME "%s"' % dir1)
        self.osc.write('EXPort STARt')

    def readfile(self, dir1):
        self.osc.write('FILESYSTEM:READFILE "%s"' % dir1)

    def persistence(self, state):
        self.osc.write('DISplay:PERSistence %s' % state)

    def cursor(self, state):
        self.osc.write('CURSOR:STATE %s' % state)

    def hormode(self, state):
        self.osc.write('HOR:MODE %s' % state)

    def horpos(self, num):
        self.osc.write('HORIZONTAL:POSITION %d' % num)

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
        return file_path

    def scale(self, channel, num):
        self.osc.write('%s:SCALE %.3f' % (channel, num))

    def channel_state(self, ch1, ch2, ch3, ch4):
        self.osc.write('SELECT:CH4 %s' % ch4)
        self.osc.write('SELECT:CH3 %s' % ch3)
        self.osc.write('SELECT:CH2 %s' % ch2)
        self.osc.write('SELECT:CH1 %s' % ch1)

    def label(self, channel, name, xi, y):
        self.osc.write('%s:LABel:NAMe "%s"' % (channel, name))
        self.osc.write('%s:LABel:XPOS %.1f' % (channel, xi))
        self.osc.write('%s:LABel:YPOS %.1f' % (channel, y))

    def chanset(self, channel, pos, offset, bandwidth, scale):
        self.osc.write('%s:POS %.1f' % (channel, pos))
        self.osc.write('%s:OFFSET %.2f' % (channel, offset))
        self.osc.write('%s:BANDWIDTH %s' % (channel, bandwidth))
        self.osc.write('%s:SCALE %.3f' % (channel, scale))

    def trigger(self, mode, channel, slope, level):
        self.osc.write('TRIGGER:A:MODE %s' % mode)
        self.osc.write('TRIGGER:A:EDGE:SOURCE %s' % channel)
        self.osc.write('TRIGGER:A:EDGE:SLOPE %s' % slope)
        self.osc.write('TRIGGER:A:LEVEL %.2f' % level)

    def math(self, channel, define, offset, pos, scale):
        self.osc.write('%s:DEFINE "%s"' % (channel, define))
        self.osc.write('%s:VERT:AUTOSC OFF' % channel)
        self.osc.write('%s:OFFSET %.2f' % (channel, offset))
        self.osc.write('%s:VERTICAL:POSITION %.2f' % (channel, pos))
        self.osc.write('%s:VERTICAL:SCALE %.2f' % (channel, scale))
        self.osc.write('SELECT:%s ON' % channel)


class OscDPO5104B:
    """Tektronix DPO5000 系列示波器驱动。"""

    def __init__(self, address, resource_manager):
        address = address.strip().rstrip()
        self.osc = resource_manager.open_resource(address)

    def state(self, state):
        if state == 'run':
            self.osc.write('DIS:PERS:RESET')
            self.osc.write('ACQUIRE:STOPAFTER RUNSTOP')
            self.osc.write('ACQUIRE:STATE RUN')
        elif state == 'single':
            self.osc.write('ACQUIRE:STOPAFTER SEQUENCE')
            self.osc.write('ACQUIRE:STATE 1')
        elif state == 'stop':
            self.osc.write('ACQUIRE:STOPAFTER RUNSTOP')
            self.osc.write('ACQUIRE:STATE STOP')
        else:
            print('状态设置失败')

    def measure(self, measNum, channel, type1, source):
        self.osc.write('MEASUREMENT:ADDNEW "MEAS%d"' % measNum)
        self.osc.write('MEASUREMENT:MEAS%d:SOURCE%d %s' % (measNum, source, channel))
        self.osc.write('MEASUREMENT:MEAS%d:TYPE %s' % (measNum, type1))
        self.osc.write('MEASUrement:MEAS%d:DISPlaystat:ENABle ON' % measNum)

    def measOff(self, measNum):
        self.osc.write('MEASUrement:MEAS%d:STATE OFF' % measNum)
        self.osc.write('MEASUrement:ANNOTate AUTO')

    def makeDir(self, dir1):
        self.osc.write('FILESystem:MKDir "%s"' % dir1)

    def export(self, temp1, dir1):
        self.osc.write('EXPort:FORMat %s' % temp1)
        self.osc.write('EXPORT:FILENAME "%s"' % dir1)
        self.osc.write('EXPort STARt')

    def readfile(self, dir1):
        self.osc.write('FILESYSTEM:READFILE "%s"' % dir1)

    def persistence(self, state):
        self.osc.write('DISplay:PERSistence %s' % state)

    def cursor(self, state):
        self.osc.write('CURSOR:STATE %s' % state)

    def hormode(self, state):
        self.osc.write('HOR:MODE %s' % state)

    def horpos(self, num):
        self.osc.write('HORIZONTAL:POSITION %d' % num)

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
        return file_path

    def scale(self, channel, num):
        self.osc.write('%s:SCALE %.3f' % (channel, num))

    def channel_state(self, ch1, ch2, ch3, ch4):
        self.osc.write('SELECT:CH4 %s' % ch4)
        self.osc.write('SELECT:CH3 %s' % ch3)
        self.osc.write('SELECT:CH2 %s' % ch2)
        self.osc.write('SELECT:CH1 %s' % ch1)

    def label(self, channel, name, xi, y):
        self.osc.write('%s:LABel:NAMe "%s"' % (channel, name))
        self.osc.write('%s:LABel:XPOS %.1f' % (channel, xi))
        self.osc.write('%s:LABel:YPOS %.1f' % (channel, y))

    def chanset(self, channel, pos, offset, bandwidth, scale):
        self.osc.write('%s:POS %.1f' % (channel, pos))
        self.osc.write('%s:OFFSET %.2f' % (channel, offset))
        self.osc.write('%s:BANDWIDTH %s' % (channel, bandwidth))
        self.osc.write('%s:SCALE %.3f' % (channel, scale))

    def trigger(self, mode, channel, slope, level):
        self.osc.write('TRIGGER:A:MODE %s' % mode)
        self.osc.write('TRIGGER:A:EDGE:SOURCE %s' % channel)
        self.osc.write('TRIGGER:A:EDGE:SLOPE %s' % slope)
        self.osc.write('TRIGGER:A:LEVEL %.2f' % level)

    def math(self, channel, define, offset, pos, scale):
        self.osc.write('%s:DEFINE "%s"' % (channel, define))
        self.osc.write('%s:VERT:AUTOSC OFF' % channel)
        self.osc.write('%s:OFFSET %.2f' % (channel, offset))
        self.osc.write('%s:VERTICAL:POSITION %.2f' % (channel, pos))
        self.osc.write('%s:VERTICAL:SCALE %.2f' % (channel, scale))
        self.osc.write('SELECT:%s ON' % channel)
