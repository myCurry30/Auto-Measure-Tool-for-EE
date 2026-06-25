"""Instrument connection and management.

Supports:
  - GPIB/USB auto-detect (original method)
  - IP/Ethernet direct connection (TCPIP)
  - Connection monitoring and auto-reconnect
"""
import time
import pyvisa
from .osc_mpo5 import OscMPO5series
from .osc_dpo7000c import OscDPO7000C
from .osc_dpo5104b import OscDPO5104B


def _identify_oscilloscope(addr, rm):
    """Try to identify oscilloscope model at the given VISA address.

    Args:
        addr: VISA resource string
        rm: pyvisa.ResourceManager instance

    Returns:
        Tuple of (osc_instance, model_flags) or (None, empty dict) on failure
    """
    model_flags = {'mso5': False, 'dpo7000': False, 'dpo5104b': False}
    osc = None

    try:
        ins = rm.open_resource(addr)
        ins.timeout = 5000  # 5s timeout for identification
        insinf = ins.query('*IDN?')
        insinf = insinf.upper()
        print(f'[InstrumentManager] *IDN? response: {insinf}')

        ins.close()  # Close probe connection, driver will reopen

        if insinf.find('TEKTRONIX,DPO7') != -1:
            print(f'[InstrumentManager] DPO7000 series detected at {addr}')
            osc = OscDPO7000C(addr, rm)
            model_flags['dpo7000'] = True

        elif insinf.find('TEKTRONIX,MSO') != -1:
            print(f'[InstrumentManager] MSO4/5/6 series detected at {addr}')
            osc = OscMPO5series(addr, rm)
            model_flags['mso5'] = True

        elif insinf.find('TEKTRONIX,DPO5') != -1:
            print(f'[InstrumentManager] DPO5000 series detected at {addr}')
            osc = OscDPO5104B(addr, rm)
            model_flags['dpo5104b'] = True

        else:
            print(f'[InstrumentManager] Unknown instrument at {addr}: {insinf}')

    except pyvisa.Error as e:
        print(f'[InstrumentManager] VISA error probing {addr}: {e}')
    except Exception as e:
        print(f'[InstrumentManager] Error probing {addr}: {e}')

    return osc, model_flags


def connect_usb_gpib():
    """Connect via GPIB/USB by scanning all VISA resources (original method).

    Returns:
        Tuple of (osc_instance, resource_manager, model_flags, message)
    """
    rm = pyvisa.ResourceManager()
    insadd = rm.list_resources()
    print(f'[InstrumentManager] Found VISA resources: {insadd}')

    model_flags = {'mso5': False, 'dpo7000': False, 'dpo5104b': False}
    osc = None

    for addr in insadd:
        # Only probe GPIB and USB resources
        if 'GPIB' not in addr and 'USB' not in addr:
            continue

        result_osc, result_flags = _identify_oscilloscope(addr, rm)
        if result_osc:
            osc = result_osc
            model_flags = result_flags
            break  # Use first found instrument

    if osc:
        message = '示波器已通过 GPIB/USB 连接成功'
    else:
        message = '未找到 GPIB/USB 连接的示波器，请检查!'

    return osc, rm, model_flags, message


def connect_ip(ip_address, port=4000, use_socket=False):
    """Connect via Ethernet/IP (TCPIP).

    Per Tektronix MSO4/5/6 Programmer Manual:
      - VISA TCPIP resource: TCPIP0::<IP>::INSTR
      - Socket server:       TCPIP0::<IP>::<PORT>::SOCKET

    Args:
        ip_address: IP address of the oscilloscope (e.g. '192.168.1.100')
        port: Socket port number (default 4000 per Tektronix default)
        use_socket: If True, use raw socket connection instead of VISA instrument protocol

    Returns:
        Tuple of (osc_instance, resource_manager, model_flags, message)
    """
    rm = pyvisa.ResourceManager()

    # Build VISA resource string
    if use_socket:
        visa_addr = f'TCPIP0::{ip_address}::{port}::SOCKET'
    else:
        visa_addr = f'TCPIP0::{ip_address}::INSTR'

    print(f'[InstrumentManager] Attempting IP connection: {visa_addr}')

    osc, model_flags = _identify_oscilloscope(visa_addr, rm)

    if osc:
        message = f'示波器已通过 IP ({ip_address}) 连接成功'
    else:
        message = f'无法通过 IP ({ip_address}) 连接示波器，请检查:\n' \
                  f'  1. IP 地址是否正确\n' \
                  f'  2. 示波器已连接网络\n' \
                  f'  3. 示波器 LAN 设置已启用\n' \
                  f'  4. 防火墙未阻止连接'

    return osc, rm, model_flags, message


def check_connection(osc):
    """Check if the oscilloscope connection is still alive.

    Sends *IDN? query and checks for response.

    Args:
        osc: Oscilloscope driver instance

    Returns:
        True if connection is alive, False otherwise
    """
    if osc is None:
        return False

    try:
        response = osc.osc.query('*IDN?')
        if response and len(response) > 0:
            return True
    except pyvisa.Error as e:
        print(f'[InstrumentManager] Connection check failed: {e}')
    except Exception as e:
        print(f'[InstrumentManager] Connection check error: {e}')

    return False


def reconnect(last_method='usb_gpib', ip_address='', port=4000, use_socket=False):
    """Attempt to reconnect to the oscilloscope.

    Args:
        last_method: 'usb_gpib' or 'ip'
        ip_address: IP address (used when last_method='ip')
        port: Socket port (used when last_method='ip')
        use_socket: Use socket mode (used when last_method='ip')

    Returns:
        Tuple of (osc_instance, resource_manager, model_flags, message)
    """
    print(f'[InstrumentManager] Attempting reconnect via {last_method}...')

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        print(f'[InstrumentManager] Reconnect attempt {attempt}/{max_retries}')

        if last_method == 'ip' and ip_address:
            osc, rm, model_flags, message = connect_ip(ip_address, port, use_socket)
        else:
            osc, rm, model_flags, message = connect_usb_gpib()

        if osc:
            print(f'[InstrumentManager] Reconnect successful on attempt {attempt}')
            return osc, rm, model_flags, message

        if attempt < max_retries:
            wait_time = attempt * 2  # Progressive backoff: 2s, 4s
            print(f'[InstrumentManager] Retrying in {wait_time}s...')
            time.sleep(wait_time)

    message = f'重连失败（尝试 {max_retries} 次后仍无法连接）'
    print(f'[InstrumentManager] {message}')
    return None, None, {'mso5': False, 'dpo7000': False, 'dpo5104b': False}, message
