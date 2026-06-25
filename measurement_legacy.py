"""测量配置函数 - tkinter 版本。

包含 common_set(), channel_Lable_set(), measure1()-measure6() 函数。
"""


# 全局变量（由主模块注入）
osc = None
MSO5 = 0
DPO7000 = 0
DPO5104B = 0
entry1 = None
entry2 = None
entry6 = None


def common_set():
    """示波器通用初始设置。"""
    osc.state('stop')
    osc.persistence('OFF')
    osc.cursor('OFF')
    osc.coupling('CH1', 'DC')
    osc.coupling('CH2', 'DC')
    osc.channel_state('OFF', 'OFF', 'OFF', 'OFF')
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
    """设置示波器通道标签。"""
    osc.label('CH1', entry1.get(), 10, 40)
    osc.label('CH2', entry2.get(), 10, 40)
    osc.label('CH3', entry6.get(), 10, 40)


def measure1():
    """测量配置1：G3 to S0（上升沿触发，90%/10%延迟）。"""
    if MSO5 == 1:
        osc.measure_1(1, 'CH1', 'Top')
        osc.measure_1(2, 'CH1', 'Base')
        osc.measure_1(3, 'CH2', 'Top')
        osc.measure_1(4, 'CH2', 'Base')
        osc.measure_delay(7, 'CH1', 'CH2', 'DELAY', 'RISE', 'RISE', 90, 10, 'RISEMid')
        osc.measure_1(5, 'CH1', 'MAXimum')
        osc.measure_1(6, 'CH1', 'Minimum')
        osc.measure_1(8, 'CH2', 'MAXimum')
        osc.measure_1(9, 'CH2', 'Minimum')
    else:
        osc.measure(1, 'CH1', 'Top', 1)
        osc.measure(2, 'CH1', 'Base', 1)
        osc.measure(3, 'CH2', 'Top', 1)
        osc.measure(4, 'CH2', 'Base', 1)
        osc.measure(7, 'CH1', 'DELAY', 1)
        osc.measure(7, 'CH2', 'DELAY', 2)
        osc.write('MEASUREMENT:MEAS%d:DELAY:EDGE %s' % (7, 'RISE'))
        osc.write('MEASUREMENT:MEAS%d:TOEdge %s' % (7, 'RISE'))
        osc.write('MEASUrement:MEAS%d:GLOBalref 0' % (7))
        osc.write('MEASUrement:MEAS%d:REFLevels1:PERCent:TYPE CUSTom' % (7))
        osc.write('MEASUrement:MEAS%d:REFLevels2:PERCent:TYPE CUSTom' % (7))
        osc.write('MEASUrement:MEAS%d:REFLevels1:PERCent:%s %d' % (7, 'RISEMid', 90))
        osc.write('MEASUrement:MEAS%d:REFLevels2:PERCent:%s %d' % (7, 'RISEMid', 10))
        osc.measure(5, 'CH1', 'MAXimum', 1)
        osc.measure(6, 'CH1', 'Minimum', 1)
        osc.measure(8, 'CH2', 'MAXimum', 1)
        osc.measure(9, 'CH2', 'Minimum', 1)
    osc.trigger('NORMAL', 'CH1', 'RISE', 0.5)


def measure2():
    """测量配置2：S0-S5-S0 等（下降沿触发，10%/90%延迟）。"""
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
        osc.measure(1, 'CH1', 'Top', 1)
        osc.measure(2, 'CH1', 'Base', 1)
        osc.measure(3, 'CH2', 'Top', 1)
        osc.measure(4, 'CH2', 'Base', 1)
        osc.measure(7, 'CH1', 'DELAY', 1)
        osc.measure(7, 'CH2', 'DELAY', 2)
        osc.write('MEASUREMENT:MEAS%d:DELAY:EDGE %s ' % (7, 'FALL'))
        osc.write('MEASUREMENT:MEAS%d:TOEdge %s ' % (7, 'FALL'))
        osc.write('MEASUrement:MEAS%d:GLOBalref 0' % (7))
        osc.write('MEASUrement:MEAS%d:REFLevels1:PERCent:TYPE CUSTom' % (7))
        osc.write('MEASUrement:MEAS%d:REFLevels2:PERCent:TYPE CUSTom' % (7))
        osc.write('MEASUrement:MEAS%d:REFLevels1:PERCent:%s %d' % (7, 'FALLMid', 10))
        osc.write('MEASUrement:MEAS%d:REFLevels2:PERCent:%s %d' % (7, 'FALLMid', 90))
        osc.measure(5, 'CH1', 'MAXimum', 1)
        osc.measure(6, 'CH1', 'Minimum', 1)
        osc.measure(8, 'CH2', 'MAXimum', 1)
        osc.measure(9, 'CH2', 'Minimum', 1)
    osc.trigger('NORMAL', 'CH1', 'FALL', 0.5)


def measure3():
    """测量配置3：LVT（下降沿触发）。"""
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
        osc.measure(1, 'CH1', 'Top', 1)
        osc.measure(2, 'CH1', 'Base', 1)
        osc.measure(3, 'CH2', 'Top', 1)
        osc.measure(4, 'CH2', 'Base', 1)
        osc.measure(7, 'CH1', 'DELAY', 1)
        osc.measure(7, 'CH2', 'DELAY', 2)
        osc.write('MEASUREMENT:MEAS%d:DELAY:EDGE %s ' % (7, 'FALL'))
        osc.write('MEASUREMENT:MEAS%d:TOEdge %s ' % (7, 'FALL'))
        osc.write('MEASUrement:MEAS%d:GLOBalref 0' % (7))
        osc.write('MEASUrement:MEAS%d:REFLevels1:PERCent:TYPE CUSTom' % (7))
        osc.write('MEASUrement:MEAS%d:REFLevels2:PERCent:TYPE CUSTom' % (7))
        osc.write('MEASUrement:MEAS%d:REFLevels1:PERCent:%s %d' % (7, 'FALLMid', 10))
        osc.write('MEASUrement:MEAS%d:REFLevels2:PERCent:%s %d' % (7, 'FALLMid', 90))
        osc.measure(5, 'CH1', 'MAXimum', 1)
        osc.measure(6, 'CH1', 'Minimum', 1)
        osc.measure(8, 'CH2', 'MAXimum', 1)
        osc.measure(9, 'CH2', 'Minimum', 1)
    osc.trigger('NORMAL', 'CH1', 'FALL', 0.5)


def measure4():
    """测量配置4：HW Strap（CH2上升沿触发）。"""
    if MSO5 == 1:
        osc.measure_1(1, 'CH1', 'Top')
        osc.measure_1(2, 'CH1', 'Base')
        osc.measure_1(3, 'CH2', 'Top')
        osc.measure_1(4, 'CH2', 'Base')
    else:
        osc.measure(1, 'CH1', 'Top', 1)
        osc.measure(2, 'CH1', 'Base', 1)
        osc.measure(3, 'CH2', 'Top', 1)
        osc.measure(4, 'CH2', 'Base', 1)
    osc.trigger('NORMAL', 'CH2', 'RISE', 0.5)


def measure5():
    """测量配置5：PG&EN（3通道，CH1上升沿触发）。"""
    if MSO5 == 1:
        osc.measure_1(1, 'CH1', 'Top')
        osc.measure_1(2, 'CH1', 'Base')
        osc.measure_1(3, 'CH2', 'Top')
        osc.measure_1(4, 'CH2', 'Base')
        osc.measure_1(5, 'CH3', 'Top')
        osc.measure_1(6, 'CH3', 'Base')
    else:
        osc.measure(1, 'CH1', 'Top', 1)
        osc.measure(2, 'CH1', 'Base', 1)
        osc.measure(3, 'CH2', 'Top', 1)
        osc.measure(4, 'CH2', 'Base', 1)
        osc.measure(5, 'CH3', 'Top', 1)
        osc.measure(6, 'CH3', 'Base', 1)
    osc.trigger('NORMAL', 'CH1', 'RISE', 0.5)


def measure6():
    """测量配置6：Monotony（单通道，上升时间/下降时间）。"""
    if MSO5 == 1:
        osc.measure_1(1, 'CH1', 'Top')
        osc.measure_1(2, 'CH1', 'Base')
        osc.measure_1(5, 'CH1', 'MAXimum')
        osc.measure_1(6, 'CH1', 'Minimum')
        osc.measure_1(10, 'CH1', 'RISETIME')
        osc.measure_1(11, 'CH1', 'FALLTIME')
    else:
        osc.measure(1, 'CH1', 'Top', 1)
        osc.measure(2, 'CH1', 'Base', 1)
        osc.measure(5, 'CH1', 'MAXimum', 1)
        osc.measure(6, 'CH1', 'Minimum', 1)
        osc.measure(10, 'CH1', 'RISETIME', 1)
        osc.measure(11, 'CH1', 'FALLTIME', 1)
    osc.trigger('NORMAL', 'CH1', 'RISE', 0.5)
