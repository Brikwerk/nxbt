from enum import Enum
import random
from time import perf_counter

from .controller import ControllerTypes
from .utils import replace_subarray


class SwitchResponses(Enum):

    NO_DATA = -1
    MALFORMED = -2
    TOO_SHORT = -3
    UNKNOWN_SUBCOMMAND = -4
    REQUEST_DEVICE_INFO = 2
    SET_SHIPMENT = 0x08
    SPI_READ = 0x10
    SET_MODE = 0x03
    TRIGGER_BUTTONS = 0x04
    TOGGLE_IMU = 0x40
    ENABLE_VIBRATION = 0x48
    SET_PLAYER = 0x30
    SET_NFC_IR_STATE = 0x22
    SET_NFC_IR_CONFIG = 0x21


class ControllerProtocol():

    CONTROLLER_INFO = {
        ControllerTypes.JOYCON_L: {
            "id": 0x01,
            "connection_info": 0x0E
        },
        ControllerTypes.JOYCON_R: {
            "id": 0x02,
            "connection_info": 0x0E
        },
        ControllerTypes.PRO_CONTROLLER: {
            "id": 0x03,
            "connection_info": 0x00
        }
    }
    VIBRATOR_BYTES = [0xA0, 0xB0, 0xC0, 0x90]

    def __init__(self, controller_type, bt_address, report_size=50,
                 colour_body=None, colour_buttons=None):
        """Initializes the protocol for the controller.

        :param controller_type: The type of controller (Joy-Con (L),
        Pro Controller, etc)
        :type controller_type: ControllerTypes
        :param bt_address: A colon-separated Bluetooth MAC address
        :type bt_address: string
        :param report_size: The size of the protocol report, defaults to 50
        :type report_size: int, optional
        :param colour_body: Sets the body colour of the controller, defaults
        to None
        :type colour_body: list of bytes, optional
        :param colour_buttons: Sets the colour of the controller buttons,
        defaults to None
        :type colour_buttons: list of bytes, optional
        :raises ValueError: On unknown controller type
        """

        self.bt_address = bt_address

        if controller_type in self.CONTROLLER_INFO.keys():
            self.controller_type = controller_type
        else:
            raise ValueError("Unknown controller type specified")

        self.report = None
        self.report_size = report_size
        self.set_empty_report()

        # Input report mode
        self.mode = None

        # Player number
        self.player_number = None

        # Setting if the controller has been asked for device info
        # Enables buttons/stick output for the standard full report
        self.device_info_queried = False

        # Standard Input Report Properties
        # Timestamp to generate timer byte ticks
        self.timer = 0
        self.timestamp = None

        # High/Low Nibble
        self.battery_level = 0x90
        self.connection_info = (
            self.CONTROLLER_INFO[self.controller_type]["connection_info"])

        self.button_status = [0x00] * 3

        # Disable left stick if we have a right Joy-Con
        if self.controller_type == ControllerTypes.JOYCON_R:
            self.left_stick_centre = [0x00] * 3
        else:
            # Center values which are also reported under
            # SPI Stick calibration reads
            self.left_stick_centre = [0x6F, 0xC8, 0x77]

        # Disable right stick if we have a left Joy-Con
        if self.controller_type == ControllerTypes.JOYCON_L:
            self.right_stick_centre = [0x00] * 3
        else:
            # Center values which are also reported under
            # SPI Stick calibration reads
            self.right_stick_centre = [0x16, 0xD8, 0x7D]

        self.vibration_enabled = False
        self.vibrator_report = random.choice(self.VIBRATOR_BYTES)

        # IMU (Six Axis Sensor) State
        self.imu_enabled = False

        # Controller colours
        # Body Colour
        if not colour_body:
            self.colour_body = [0x82] * 3
        else:
            self.colour_body = colour_body
        if not colour_buttons:
            self.colour_buttons = [0x0F] * 3
        else:
            self.colour_buttons = colour_buttons

    def get_report(self):

        report = bytes(self.report)
        # Clear report
        self.set_empty_report()
        return report

    def process_commands(self, data):

        # Parsing the Switch's message
        message = SwitchReportParser(data)

        # Responding to the parsed message
        if message.response == SwitchResponses.REQUEST_DEVICE_INFO:
            self.device_info_queried = True
            self.set_subcommand_reply()
            self.set_device_info()

        elif message.response == SwitchResponses.SET_SHIPMENT:
            self.set_subcommand_reply()
            self.set_shipment()

        elif message.response == SwitchResponses.SPI_READ:
            self.set_subcommand_reply()
            self.spi_read(message)

        elif message.response == SwitchResponses.SET_MODE:
            self.set_subcommand_reply()
            self.set_mode(message)

        elif message.response == SwitchResponses.TRIGGER_BUTTONS:
            self.set_subcommand_reply()
            self.set_trigger_buttons()

        elif message.response == SwitchResponses.TOGGLE_IMU:
            self.set_subcommand_reply()
            self.toggle_imu(message)

        elif message.response == SwitchResponses.ENABLE_VIBRATION:
            self.set_subcommand_reply()
            self.enable_vibration()

        elif message.response == SwitchResponses.SET_PLAYER:
            self.set_subcommand_reply()
            self.set_player_lights(message)

        elif message.response == SwitchResponses.SET_NFC_IR_STATE:
            self.set_subcommand_reply()
            self.set_nfc_ir_state()

        elif message.response == SwitchResponses.SET_NFC_IR_CONFIG:
            self.set_subcommand_reply()
            self.set_nfc_ir_config()

        # Bad Packet handling statements
        elif message.response == SwitchResponses.UNKNOWN_SUBCOMMAND:
            # Currently set so that the controller ignores any unknown
            # subcommands. This is better than sending a NACK response
            # since we'd just get stuck in an infinite loop arguing
            # with the Switch.
            self.set_full_input_report()

        elif message.response == SwitchResponses.NO_DATA:
            self.set_full_input_report()

        elif message.response == SwitchResponses.TOO_SHORT:
            self.set_full_input_report()

        elif message.response == SwitchResponses.MALFORMED:
            self.set_full_input_report()

    def set_empty_report(self):

        empty_report = [0] * self.report_size
        empty_report[0] = 0xA1

        self.report = empty_report

    def set_subcommand_reply(self):

        # Input Report ID
        self.report[1] = 0x21

        # TODO: Find out what the vibrator byte is doing.
        # This is a hack in an attempt to semi-emulate
        # actions of the vibrator byte as it seems to change
        # when a subcommand reply is sent.
        self.vibrator_report = random.choice(self.VIBRATOR_BYTES)

        self.set_standard_input_report()

    def set_unknown_subcommand(self, subcommand_id):

        # Set NACK
        self.report[14]

        # Set unknown subcommand ID
        self.report[15] = subcommand_id

    def set_timer(self):

        # If the timer hasn't been set before
        if not self.timestamp:
            self.timestamp = perf_counter()
            self.report[2] = 0x00
            return

        # Get the time that has passed since the last timestamp
        # in milliseconds
        now = perf_counter()
        delta_t = (now - self.timestamp) * 1000

        # Get how many ticks have passed in hex with overflow at 255
        # Joy-Con uses 4.96ms as the timer tick rate
        elapsed_ticks = int(delta_t * 4)
        self.timer = (self.timer + elapsed_ticks) & 0xFF

        self.report[2] = self.timer
        self.timestamp = now

    def set_full_input_report(self):

        # Setting Report ID to full standard input report ID
        self.report[1] = 0x30
        self.set_standard_input_report()
        self.set_imu_data()

    def set_standard_input_report(self):

        self.set_timer()

        if self.device_info_queried:
            self.report[3] = self.battery_level + self.connection_info

            self.report[4] = self.button_status[0]
            self.report[5] = self.button_status[1]
            self.report[6] = self.button_status[2]

            self.report[7] = self.left_stick_centre[0]
            self.report[8] = self.left_stick_centre[1]
            self.report[9] = self.left_stick_centre[2]

            self.report[10] = self.right_stick_centre[0]
            self.report[11] = self.right_stick_centre[1]
            self.report[12] = self.right_stick_centre[2]

            self.report[13] = self.vibrator_report

    def set_button_inputs(self, upper, shared, lower):

        self.report[4] = upper
        self.report[5] = shared
        self.report[6] = lower

    def set_left_stick_inputs(self, left):

        self.report[7] = left[0]
        self.report[8] = left[1]
        self.report[9] = left[2]

    def set_right_stick_inputs(self, right):

        self.report[10] = right[0]
        self.report[11] = right[1]
        self.report[12] = right[2]

    def set_device_info(self):

        # ACK Reply
        self.report[14] = 0x82

        # Subcommand Reply
        self.report[15] = 0x02

        # Firmware version
        self.report[16] = 0x03
        self.report[17] = 0x8B

        # Controller ID
        self.report[18] = self.CONTROLLER_INFO[self.controller_type]["id"]

        # Unknown Byte, always 2
        self.report[19] = 0x02

        # Controller Bluetooth Address
        address = self.bt_address.strip().split(":")  # Getting from adapter
        address_location = 20
        for address_byte_str in address:
            # Converting string address bytes to hex
            # and assigning to report
            address_byte = int(address_byte_str, 16)
            self.report[address_location] = address_byte
            address_location += 1

        # Unknown byte, always 1
        self.report[26] = 0x01

        # Controller colours location (read from SPI)
        self.report[27] = 0x01

    def set_shipment(self):

        # ACK Reply
        self.report[14] = 0x80

        # Subcommand reply
        self.report[15] = 0x08

    def toggle_imu(self, message):

        if message.subcommand[1] == 0x01:
            self.imu_enabled = True
        else:
            self.imu_enabled = False

        # ACK Reply
        self.report[14] = 0x80

        # Subcommand reply
        self.report[15] = 0x40

    def set_imu_data(self):

        if not self.imu_enabled:
            return

        imu_data = [0x75, 0xFD, 0xFD, 0xFF, 0x09, 0x10, 0x21, 0x00, 0xD5, 0xFF,
                    0xE0, 0xFF, 0x72, 0xFD, 0xF9, 0xFF, 0x0A, 0x10, 0x22, 0x00,
                    0xD5, 0xFF, 0xE0, 0xFF, 0x76, 0xFD, 0xFC, 0xFF, 0x09, 0x10,
                    0x23, 0x00, 0xD5, 0xFF, 0xE0, 0xFF]
        replace_subarray(self.report, 14, 49, replace_arr=imu_data)

    def spi_read(self, message):

        addr_top = message.subcommand[2]
        addr_bottom = message.subcommand[1]
        read_length = message.subcommand[5]

        # ACK byte
        self.report[14] = 0x90

        # Subcommand reply
        self.report[15] = 0x10

        # Read address
        self.report[16] = addr_bottom
        self.report[17] = addr_top

        # Read length
        self.report[20] = read_length

        # Stick Parameters
        # Params are generally the same for all sticks
        # Notable difference is the deadzone (10% Joy-Con vs 15% Pro Con)
        params = [0x0F, 0x30, 0x61,  # Unused
                  0x96, 0x30, 0xF3,  # Dead Zone/Range Ratio
                  0xD4, 0x14, 0x54,  # X/Y ?
                  0x41, 0x15, 0x54,  # X/Y ?
                  0xC7, 0x79, 0x9C,  # X/Y ?
                  0x33, 0x36, 0x63]  # X/Y ?
        # Adjusting deadzone for Joy-Cons
        if not self.controller_type == ControllerTypes.PRO_CONTROLLER:
            params[3] = 0xAE

        # Serial Number read
        if addr_top == 0x60 and addr_bottom == 0x00:
            # Switch will take this as no serial number
            replace_subarray(self.report, 21, 16, 0xFF)

        # Colours
        elif addr_top == 0x60 and addr_bottom == 0x50:
            # Body colour
            replace_subarray(
                self.report, 21, 3,
                replace_arr=self.colour_body)
            # Buttons colour
            replace_subarray(
                self.report, 24, 3,
                replace_arr=self.colour_buttons)
            # Left/right grip colours (Pro controller)
            replace_subarray(self.report, 27, 7, 0xFF)

        # Factory sensor/stick device parameters
        elif addr_top == 0x60 and addr_bottom == 0x80:

            # Six-Axis factory parameters
            if self.controller_type == ControllerTypes.PRO_CONTROLLER:
                self.report[21] = 0x50
                self.report[22] = 0xFD
                self.report[23] = 0x00
                self.report[24] = 0x00
                self.report[25] = 0xC6
                self.report[26] = 0x0F
            else:
                self.report[21] = 0x5E
                self.report[22] = 0x01
                self.report[23] = 0x00
                self.report[24] = 0x00
                if self.controller_type == ControllerTypes.JOYCON_L:
                    self.report[25] = 0xF1
                    self.report[26] = 0x0F
                else:
                    self.report[25] = 0x0F
                    self.report[26] = 0xF0

            replace_subarray(self.report, 27, 18, replace_arr=params)

        # Stick device parameters 2
        elif addr_top == 0x60 and addr_bottom == 0x98:

            # Setting same params since controllers always
            # have duplicates of stick params 1 for stick params 2
            replace_subarray(self.report, 21, 18, replace_arr=params)

        # User analog stick calibration
        elif addr_top == 0x80 and addr_bottom == 0x10:

            # Fill report with null user calibration info
            replace_subarray(self.report, 21, 24, 0xFF)

        # Factory analog stick calibration
        elif addr_top == 0x60 and addr_bottom == 0x3D:

            # Left/right stick calibration
            l_calibration = [0xBA, 0xF5, 0x62,
                             0x6F, 0xC8, 0x77,
                             0xED, 0x95, 0x5B]
            r_calibration = [0x16, 0xD8, 0x7D,
                             0xF2, 0xB5, 0x5F,
                             0x86, 0x65, 0x5E]

            # Left stick calibration
            # If null, fill with 0xFF
            if not self.controller_type == ControllerTypes.JOYCON_R:
                replace_subarray(self.report, 21, 9, replace_arr=l_calibration)
            else:
                replace_subarray(self.report, 21, 9, value=0xFF)

            # Right stick calibration
            # If null, fill with 0xFF
            if not self.controller_type == ControllerTypes.JOYCON_L:
                replace_subarray(self.report, 30, 9, replace_arr=r_calibration)
            else:
                replace_subarray(self.report, 30, 9, value=0xFF)

            # Spacer byte
            self.report[39] = 0xFF

            # Body colour
            replace_subarray(
                self.report, 40, 3,
                replace_arr=self.colour_body)
            # Buttons colour
            replace_subarray(
                self.report, 43, 3,
                replace_arr=self.colour_buttons)

        # Six-Axis motion sensor factor calibration
        elif addr_top == 0x60 and addr_bottom == 0x20:

            # 1: Acceleration origin position
            # 2: Acceleration sensitivity coefficient
            # 3: Gyro origin when still
            # 4: Gyro sensitivity coefficient
            sa_calibration = [0xD3, 0xFF, 0xD5, 0xFF, 0x55, 0x01,  # 1
                              0x00, 0x40, 0x00, 0x40, 0x00, 0x40,  # 2
                              0x19, 0x00, 0xDD, 0xFF, 0xDC, 0xFF,  # 3
                              0x3B, 0x34, 0x3B, 0x34, 0x3B, 0x34]  # 4

            replace_subarray(self.report, 21, 24, replace_arr=sa_calibration)

    def set_mode(self, message):

        # ACK byte
        self.report[14] = 0x80

        # Subcommand reply
        self.report[15] = 0x03

        if message.subcommand[1] == 0x30:
            self.mode = "standard"
        elif message.subcommand[1] == 0x31:
            self.mode = "nfc/ir"
        elif message.subcommand[1] == 0x3F:
            self.mode = "simpleHID"

    def set_trigger_buttons(self):

        # ACK byte
        self.report[14] = 0x83

        # Subcommand reply
        self.report[15] = 0x04

    def enable_vibration(self):

        # ACK Reply
        self.report[14] = 0x82

        # Subcommand reply
        self.report[15] = 0x48

        # Set class property
        self.vibration_enabled = True

    def set_player_lights(self, message):

        # ACK byte
        self.report[14] = 0x80

        # Subcommand reply
        self.report[15] = 0x30

        bitfield = message.subcommand[1]

        if bitfield == 0x01 or bitfield == 0x10:
            self.player_number = 1
        elif bitfield == 0x03 or bitfield == 0x30:
            self.player_number = 2
        elif bitfield == 0x07 or bitfield == 0x70:
            self.player_number = 3
        elif bitfield == 0x0F or bitfield == 0xF0:
            self.player_number = 4

    def set_nfc_ir_state(self):

        # ACK byte
        self.report[14] = 0x80

        # Subcommand reply
        self.report[15] = 0x22

    def set_nfc_ir_config(self):

        # ACK byte
        self.report[14] = 0xA0

        # Subcommand reply
        self.report[15] = 0x21

        # NFC/IR state data
        params = [0x01, 0x00, 0xFF, 0x00, 0x08, 0x00, 0x1B, 0x01]
        replace_subarray(self.report, 16, 8, replace_arr=params)
        self.report[49] = 0xC8


class SwitchReportParser():

    SUBCOMMANDS = {
        0x02: SwitchResponses.REQUEST_DEVICE_INFO,
        0x08: SwitchResponses.SET_SHIPMENT,
        0x10: SwitchResponses.SPI_READ,
        0x03: SwitchResponses.SET_MODE,
        0x04: SwitchResponses.TRIGGER_BUTTONS,
        0x40: SwitchResponses.TOGGLE_IMU,
        0x48: SwitchResponses.ENABLE_VIBRATION,
        0x30: SwitchResponses.SET_PLAYER,
        0x22: SwitchResponses.SET_NFC_IR_STATE,
        0x21: SwitchResponses.SET_NFC_IR_CONFIG,
    }

    def __init__(self, data, data_length=50):

        # Non-data check
        if not data:
            self.response = SwitchResponses.NO_DATA
            return

        # Report length check
        if len(data) < data_length:
            self.response = SwitchResponses.TOO_SHORT
            return

        # First byte check
        if data[0] != 0xA2:
            self.response = SwitchResponses.MALFORMED
            return

        # Splitting data
        self.payload = data[:11]
        self.subcommand = data[11:]
        self.subcommand_id = self.subcommand[0]

        # Parsing the subcommand
        if self.subcommand[0] in self.SUBCOMMANDS.keys():
            self.response = self.SUBCOMMANDS[self.subcommand[0]]
        else:
            self.response = SwitchResponses.UNKNOWN_SUBCOMMAND
