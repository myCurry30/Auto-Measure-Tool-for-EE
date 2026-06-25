import os
from .osc_base import OscilloscopeBase


class OscDPO5104B(OscilloscopeBase):
    """Tektronix DPO5000 series oscilloscope driver."""

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