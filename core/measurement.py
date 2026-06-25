"""Measurement configuration functions for oscilloscopes.

Contains measurement setup functions (measure1-6), common_set, and channel_Lable_set.
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


def channel_Lable_set(osc, ch1_label, ch2_label, ch3_label):
    """Set channel labels on oscilloscope.

    Args:
        osc: Oscilloscope instance
        ch1_label: CH1 label text
        ch2_label: CH2 label text
        ch3_label: CH3 label text
    """
    osc.label('CH1', ch1_label, 10, 40)
    osc.label('CH2', ch2_label, 10, 40)
    osc.label('CH3', ch3_label, 10, 40)


def measure1(osc, mso5):
    """Configure measurement for test items 1, 0 (G3 to S0).

    RISE-edge delay measurement (CH1->CH2, 90%/10%).

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


def measure2(osc, mso5):
    """Configure measurement for test items 2-6.

    FALL-edge delay measurement (CH1->CH2, 10%/90%).

    Args:
        osc: Oscilloscope instance
        mso5: True if MSO4/5/6 series
    """
    if mso5:
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


def measure3(osc, mso5):
    """Configure measurement for test item 7 (LVT).

    Same as measure2 (FALL-edge delay).

    Args:
        osc: Oscilloscope instance
        mso5: True if MSO4/5/6 series
    """
    if mso5:
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


def measure4(osc, mso5):
    """Configure measurement for test item 8 (HW Strap).

    Top/Base only on CH1+CH2, trigger on CH2 RISE.

    Args:
        osc: Oscilloscope instance
        mso5: True if MSO4/5/6 series
    """
    if mso5:
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


def measure5(osc, mso5):
    """Configure measurement for test item 9 (PG&EN).

    Top/Base on CH1, CH2, CH3, trigger on CH1 RISE.

    Args:
        osc: Oscilloscope instance
        mso5: True if MSO4/5/6 series
    """
    if mso5:
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


def measure6(osc, mso5):
    """Configure measurement for test item 10 (Monotony).

    Top/Base + Max/Min + RiseTime/FallTime on CH1 only.

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