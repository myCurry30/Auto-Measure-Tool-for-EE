"""Measurement configuration functions for oscilloscopes.

Contains measure_sequence, measure_monotony, common_set, and channel_Lable_set.
All functions accept oscilloscope instance and parameters, no global state.
"""


def common_set(osc, dpo7000, dpo5104b):
    """Reset oscilloscope to common initial state."""
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
    if dpo7000:
        osc.write('HORIZONTAL:ROLL OFF')
    if dpo5104b:
        osc.write('HORIZONTAL:ROLL OFF')
    osc.state('run')


def channel_Lable_set(osc, ch1_label, ch2_label, ch3_label, ch4_label="",
                     label_x=None, label_y=None):
    """Set channel labels on oscilloscope. None = skip (disabled).

    Args:
        osc: Oscilloscope instance
        ch1_label: CH1 label text or None to skip
        ch2_label: CH2 label text or None to skip
        ch3_label: CH3 label text or None to skip
        ch4_label: CH4 label text or None to skip
        label_x: Optional list [x1,x2,x3,x4] of X positions (0-100), default 10
        label_y: Optional list [y1,y2,y3,y4] of Y positions (0-100), default 40
    """
    if label_x is None:
        label_x = [10, 10, 10, 10]
    if label_y is None:
        label_y = [40, 40, 40, 40]
    if ch1_label is not None:
        osc.label('CH1', ch1_label, label_x[0], label_y[0])
    if ch2_label is not None:
        osc.label('CH2', ch2_label, label_x[1], label_y[1])
    if ch3_label is not None:
        osc.label('CH3', ch3_label, label_x[2], label_y[2])
    if ch4_label is not None:
        osc.label('CH4', ch4_label, label_x[3], label_y[3])


def measure_sequence(osc, mso5):
    """Sequence measurement: RISE-edge delay (CH1→CH2, 90%/10%).

    Args:
        osc: Oscilloscope instance
        mso5: True if MSO4/5/6 series
    """
    if mso5:
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


def measure_monotony(osc, mso5):
    """Monotony measurement: Top/Base + Max/Min + RiseTime/FallTime on CH1.

    Args:
        osc: Oscilloscope instance
        mso5: True if MSO4/5/6 series
    """
    if mso5:
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