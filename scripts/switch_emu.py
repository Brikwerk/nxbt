"""
Quick script to emulate a Switch connecting to a Joy-Con/Pro Controller.

Note: If you get an Invalid Exchange error when running this script, this means
that the Switch has paired to the controller, invalidating the original pairing
key we created. You'll need to re-pair the controller to this device.
"""

import socket
import sys
import os
import time

from nxbt import toggle_clean_bluez
from nxbt import BlueZ

REQUEST_INFO = b'\xA2\x01\x02\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SET_SHIPMENT = b'\xA2\x01\x07\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SERIAL_NUMBER = b'\xA2\x01\x08\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x60\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
COLOURS = b'\xA2\x01\x09\x00\x00\x00\x00\x00\x00\x00\x00\x10\x50\x60\x00\x00\x0D\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
INPUT_MODE = b'\xA2\x01\x0A\x00\x01\x40\x40\x00\x01\x40\x40\x03\x30\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
TRIGGER_BUTTONS = b'\xA2\x01\x0D\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
FACTORY_PARAMS = b'\xA2\x01\x0F\x00\x00\x00\x00\x00\x00\x00\x00\x10\x80\x60\x00\x00\x18\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
FACTORY_PARAMS_2 = b'\xA2\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x10\x98\x60\x00\x00\x12\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
USER_CAL = b'\xA2\x01\x02\x00\x00\x00\x00\x00\x00\x00\x00\x10\x10\x80\x00\x00\x18\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
FACTORY_CAL = b'\xA2\x01\x04\x00\x00\x00\x00\x00\x00\x00\x00\x10\x3D\x60\x00\x00\x19\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SIX_AXIS_CAL = b'\xA2\x01\x05\x00\x00\x00\x00\x00\x00\x00\x00\x10\x20\x60\x00\x00\x18\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
ENABLE_IMU = b'\xA2\x01\x07\x00\x01\x40\x40\x00\x01\x40\x40\x40\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
ENABLE_VIBRATION = b'\xA2\x01\x09\x00\x00\x00\x00\x00\x00\x00\x00\x48\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SET_NFC_IR = b'\xA2\x01\x0C\x00\x01\x40\x40\x00\x01\x40\x40\x21\x21\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SET_PLAYER_LIGHTS = b'\xA2\x01\x0D\x00\x00\x00\x00\x00\x00\x00\x00\x30\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

FLASH_PLAYER_LIGHTS = b'\xA2\x01\x0D\x00\x00\x00\x00\x00\x00\x00\x00\x30\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

COMMANDS = [
    REQUEST_INFO,
    SET_SHIPMENT,
    SERIAL_NUMBER,
    COLOURS,
    INPUT_MODE,
    TRIGGER_BUTTONS,
    FACTORY_PARAMS,
    FACTORY_PARAMS_2,
    USER_CAL,
    FACTORY_CAL,
    SIX_AXIS_CAL,
    ENABLE_IMU,
    ENABLE_VIBRATION,
    SET_NFC_IR,
]


def format_message(data, split, name):
    """Formats a given byte message in hex format split
    into payload and subcommand sections.

    :param data: A series of bytes
    :type data: bytes
    :param split: The location of the payload/subcommand split
    :type split: integer
    :param name: The name featured in the start/end messages
    :type name: string
    :return: The formatted data
    :rtype: string
    """

    payload = ""
    subcommand = ""
    for i in range(0, len(data)):
        data_byte = str(hex(data[i]))[2:].upper()
        if len(data_byte) < 2:
            data_byte = "0" + data_byte
        if i <= split:
            payload += "0x" + data_byte + " "
        else:
            subcommand += "0x" + data_byte + " "

    formatted = (
        f"--- {name} Msg ---\n" +
        f"Payload:    {payload}\n" +
        f"Subcommand: {subcommand}")

    return formatted


def print_msg_controller(data):
    """Prints a formatted message from a controller

    :param data: The bytes from the controller message
    :type data: bytes
    """

    print(format_message(data, 13, "Controller"))


def print_msg_switch(data):
    """Prints a formatted message from a Switch

    :param data: The bytes from the Switch message
    :type data: bytes
    """

    print(format_message(data, 10, "Switch"))


def wait_for_reply(itr):

    while True:
        data = itr.recv(350)
        print_msg_controller(data)
        if data[1] == 0x21:
            break


if __name__ == "__main__":

    # Switch Controller Bluetooth MAC Address goes here
    jc_MAC = "98:B6:E9:B0:05:E7"
    port_ctrl = 17
    port_itr = 19

    # Joy-Con Sockets
    jc_ctrl = socket.socket(family=socket.AF_BLUETOOTH,
                            type=socket.SOCK_SEQPACKET,
                            proto=socket.BTPROTO_L2CAP)
    jc_itr = socket.socket(family=socket.AF_BLUETOOTH,
                           type=socket.SOCK_SEQPACKET,
                           proto=socket.BTPROTO_L2CAP)
    toggle_clean_bluez(True)
    bt = BlueZ(adapter_path="/org/bluez/hci0")

    try:
        # Remove the device before we try to re-pair
        device_path = bt.find_device_by_address(jc_MAC)
        if not device_path:
            print("Device not paired. Pairing...")

            # Ensure we are paired/connected to the JC
            print("Attempting to re-pair with device")
            devices = bt.discover_devices(alias="Pro Controller", timeout=8)
            jc_device_path = None
            for key in devices.keys():
                print(devices[key]["Address"])
                if devices[key]["Address"] == jc_MAC:
                    jc_device_path = key
                    break

            if not jc_device_path:
                print("The specified Joy-Con could not be found")
            else:
                bt.pair_device(jc_device_path)
            print("Paired Joy-Con")

        bt.set_alias("Nintendo Switch")
        print("Connecting to Joy-Con: ", jc_MAC)
        jc_ctrl.connect((jc_MAC, port_ctrl))
        jc_itr.connect((jc_MAC, port_itr))
        print("Got connection.")

        # Initial Input report from Joy-Con
        jc_data = jc_itr.recv(350)
        print("Got initial Joy-Con Empty Report")
        print_msg_controller(jc_data)

        for command in COMMANDS:
            print_msg_switch(command)
            jc_itr.sendall(command)
            wait_for_reply(jc_itr)

        while True:
            data = jc_itr.recv(350)
            print_msg_controller(data)
            jc_itr.sendall(SET_PLAYER_LIGHTS)
            print_msg_switch(SET_PLAYER_LIGHTS)
            time.sleep(1/120)

    except KeyboardInterrupt:
        print("Closing sockets")

        jc_ctrl.close()
        jc_itr.close()

        try:
            sys.exit(1)
        except SystemExit:
            os._exit(1)

    except OSError as e:
        print("Closing sockets")

        jc_ctrl.close()
        jc_itr.close()

        raise e

    finally:
        toggle_clean_bluez(False)
