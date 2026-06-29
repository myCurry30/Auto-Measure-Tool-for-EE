from abc import ABC, abstractmethod


class OscilloscopeBase(ABC):
    """Abstract base class for oscilloscope drivers.

    Defines the common interface for all oscilloscope models.
    """

    def __init__(self, address, resource_manager):
        """Initialize oscilloscope connection.

        Args:
            address: VISA resource string (e.g., 'TCPIP0::192.168.1.1::INSTR')
            resource_manager: pyvisa.ResourceManager instance
        """
        address = address.strip().rstrip()
        self.osc = resource_manager.open_resource(address)
        self.osc.timeout = 30000  # 30s for screenshot/file transfers
        self.osc.baud_rate = 9600

    @abstractmethod
    def state(self, state):
        """Set oscilloscope acquisition state.

        Args:
            state: 'run', 'single', or 'stop'
        """
        pass

    @abstractmethod
    def measure(self, measNum, channel, type1, source):
        """Add a measurement item.

        Args:
            measNum: Measurement slot number (1-8)
            channel: Channel name (e.g., 'CH1', 'CH2')
            type1: Measurement type (e.g., 'Top', 'Base', 'DELAY')
            source: Source index for measurement
        """
        pass

    @abstractmethod
    def measOff(self, measNum):
        """Delete or disable a measurement item.

        Args:
            measNum: Measurement slot number to delete/disable
        """
        pass

    @abstractmethod
    def makeDir(self, dir1):
        """Create directory on oscilloscope filesystem.

        Args:
            dir1: Directory path on oscilloscope
        """
        pass

    @abstractmethod
    def export(self, temp1, dir1):
        """Export screenshot/image to oscilloscope filesystem.

        Args:
            temp1: Format (e.g., 'PNG')
            dir1: Target path on oscilloscope
        """
        pass

    @abstractmethod
    def readfile(self, dir1):
        """Read file from oscilloscope filesystem.

        Args:
            dir1: File path on oscilloscope
        """
        pass

    @abstractmethod
    def persistence(self, state):
        """Set display persistence.

        Args:
            state: 'ON' or 'OFF'
        """
        pass

    @abstractmethod
    def cursor(self, state):
        """Set cursor state.

        Args:
            state: 'ON' or 'OFF'
        """
        pass

    @abstractmethod
    def hormode(self, state):
        """Set horizontal acquisition mode.

        Args:
            state: Mode name (e.g., 'AUTO')
        """
        pass

    @abstractmethod
    def horpos(self, num):
        """Set horizontal position.

        Args:
            num: Position value (0-100)
        """
        pass

    @abstractmethod
    def coupling(self, channel, state):
        """Set channel coupling.

        Args:
            channel: Channel name (e.g., 'CH1')
            state: 'DC' or 'AC'
        """
        pass

    @abstractmethod
    def number(self, number):
        """Wait for a specified number of acquisitions.

        Args:
            number: Number of acquisitions to wait for
        """
        pass

    @abstractmethod
    def record(self, num):
        """Set record length.

        Args:
            num: Record length value
        """
        pass

    @abstractmethod
    def query(self, query):
        """Send query command and return response.

        Args:
            query: SCPI query string

        Returns:
            Response string
        """
        pass

    @abstractmethod
    def write(self, write):
        """Send write command.

        Args:
            write: SCPI command string
        """
        pass

    @abstractmethod
    def scale(self, channel, num):
        """Set channel vertical scale.

        Args:
            channel: Channel name (e.g., 'CH1')
            num: Scale value (V/div)
        """
        pass

    @abstractmethod
    def channel_state(self, ch1, ch2, ch3, ch4):
        """Set channel ON/OFF states.

        Args:
            ch1: 'ON' or 'OFF'
            ch2: 'ON' or 'OFF'
            ch3: 'ON' or 'OFF'
            ch4: 'ON' or 'OFF'
        """
        pass

    @abstractmethod
    def label(self, channel, name, xi, y):
        """Set channel label.

        Args:
            channel: Channel name (e.g., 'CH1')
            name: Label text
            xi: X position (0-100)
            y: Y position (0-100)
        """
        pass

    @abstractmethod
    def chanset(self, channel, pos, offset, bandwidth, scale):
        """Configure channel parameters.

        Args:
            channel: Channel name (e.g., 'CH1')
            pos: Vertical position
            offset: Vertical offset
            bandwidth: Bandwidth (e.g., '1.0000E+09')
            scale: Vertical scale (V/div)
        """
        pass

    @abstractmethod
    def trigger(self, mode, channel, slope, level):
        """Configure trigger settings.

        Args:
            mode: Trigger mode (e.g., 'NORMAL')
            channel: Trigger source channel
            slope: 'RISE' or 'FALL'
            level: Trigger level
        """
        pass

    @abstractmethod
    def math(self, channel, define, offset, pos, scale):
        """Configure math channel.

        Args:
            channel: Math channel name (e.g., 'MATH1')
            define: Math expression
            offset: Vertical offset
            pos: Vertical position
            scale: Vertical scale
        """
        pass

    @abstractmethod
    def readraw(self, file_path):
        """Read raw data from oscilloscope and save to file.

        Args:
            file_path: Local file path to save data

        Returns:
            Actual file path used (may have suffix if duplicate)
        """
        pass