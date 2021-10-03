"""
This is a quick and dirty script for recording input from a controller
and dumping it into a "messages.txt" file. You'll need to input the
device's Bluetooth MAC address manually and specify the type of
controller before this script works.

Note: If you get an Invalid Exchange error when running this script, this means
that the Switch has paired to the controller, invalidating the original pairing
key we created. You'll need to remove the controller before continuing.

-- This was tested on a Raspberry Pi 4B (4GB) with Python 3.7.3 --

-------------------------------------------------------------------------------
Directions for Use:
-------------------------------------------------------------------------------

1.) Begin with both the Switch and Pro Controller off (Sleep Mode is fine).
2.) Start the proxy.py script
3.) Immediately after starting the script, press and hold the small, circular
button on the back of the Pro Controller (near the USB-C input) until the
player lights begin Flashing.
4.) Once the script prints "Got Connection" and then "Waiting for Switch to
connect...", start up your Switch and navigate to the "Pair/Change Grip" menu.
5.) The Switch should connect the controller Proxy and the script should enter
the mainloop.
6.) Perform any actions with your controller that you want recorded.
7.) Press Ctrl-C to end the script and dump the commands in the current
working directory.
"""

import socket
import sys
import os
import time
import fcntl
from time import perf_counter

from nxbt import toggle_clean_bluez
from nxbt import BlueZ
from nxbt import Controller
from nxbt import JOYCON_L, JOYCON_R, PRO_CONTROLLER


JCL_REPLY02 = b'\xA2\x21\x05\x8E\x84\x00\x12\x01\x18\x80\x01\x18\x80\x80\x82\x02\x03\x48\x01\x02\xDC\xA6\x32\x16\x4A\x7C\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
PRO_REPLY02 = b'\xA2\x21\x1A\x40\x00\x00\x00\x02\x20\x00\x01\x00\x00\x00\x82\x02\x03\x48\x03\x02\xDC\xA6\x32\x16\x4A\x7C\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
JCR_REPLY02 = b'\xA2\x21\x05\x8E\x84\x00\x12\x01\x18\x80\x01\x18\x80\x80\x82\x02\x03\x48\x02\x02\xDC\xA6\x32\x16\x4A\x7C\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'


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


def write_to_buffer(buffer, message, message_type):

    formatted_message = None
    if message_type == "switch":
        formatted_message = format_message(message, 10, "Switch")
    elif message_type == "controller":
        formatted_message = format_message(message, 13, "Controller")
    elif message_type == "comment":
        formatted_message = "### " + message + " ###"
    else:
        raise ValueError("Unspecified or wrong message type")

    buffer.append(formatted_message)


if __name__ == "__main__":
    # Switch Controller Bluetooth MAC Address goes here
    # jc_MAC = "98:B6:E9:B0:05:E7"
    jc_MAC = "7C:BB:8A:FA:41:3D"
    # Specify the type of controller here
    controller_type = PRO_CONTROLLER
    if controller_type == JOYCON_L:
        REPLY = JCL_REPLY02
    elif controller_type == JOYCON_R:
        REPLY = JCR_REPLY02
    else:
        REPLY = PRO_REPLY02

    port_ctrl = 17
    port_itr = 19
    message_buffer = []

    toggle_clean_bluez(True)
    bt = BlueZ(adapter_path="/org/bluez/hci0")

    controller = Controller(bt, controller_type)

    # Joy-Con Sockets
    jc_ctrl = socket.socket(family=socket.AF_BLUETOOTH,
                            type=socket.SOCK_SEQPACKET,
                            proto=socket.BTPROTO_L2CAP)
    jc_itr = socket.socket(family=socket.AF_BLUETOOTH,
                           type=socket.SOCK_SEQPACKET,
                           proto=socket.BTPROTO_L2CAP)

    # Switch sockets
    switch_itr = socket.socket(family=socket.AF_BLUETOOTH,
                               type=socket.SOCK_SEQPACKET,
                               proto=socket.BTPROTO_L2CAP)
    switch_ctrl = socket.socket(family=socket.AF_BLUETOOTH,
                                type=socket.SOCK_SEQPACKET,
                                proto=socket.BTPROTO_L2CAP)
    switch_test1 = socket.socket(family=socket.AF_BLUETOOTH,
                                type=socket.SOCK_SEQPACKET,
                                proto=socket.BTPROTO_L2CAP)
    switch_test3 = socket.socket(family=socket.AF_BLUETOOTH,
                                type=socket.SOCK_SEQPACKET,
                                proto=socket.BTPROTO_L2CAP)

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

        # print("Bruteforcing sockets")
        # for i in range(1,99999,2):
        #     try:
        #         test_socket = socket.socket(family=socket.AF_BLUETOOTH,
        #                                 type=socket.SOCK_SEQPACKET,
        #                                 proto=socket.BTPROTO_L2CAP)
        #         test_socket.settimeout(3)
        #         # print("Connecting to", i)
        #         test_socket.connect((jc_MAC, i))
        #         print("!!!!!! Got connection to", i)
        #     except Exception as e:
        #         # print(str(e))
        #         pass

        # switch_test1.bind((bt.address, 1))
        # switch_test3.bind((bt.address, 3))

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

        # Initial Input report from Joy-Con
        jc_data = jc_itr.recv(350)
        print("Got initial Joy-Con Empty Report")
        # print_msg_controller(jc_data)
        write_to_buffer(
                    message_buffer,
                    "Joy-Con Empty Report",
                    "comment")
        write_to_buffer(message_buffer, jc_data, "controller")
        print(message_buffer)

        # Send the input report to the Switch a couple times
        for i in range(3):
            print("Sending input report", i)
            client_interrupt.sendall(jc_data)
            time.sleep(1)

        # Get the Switch's reply and send it to the Joy-Con
        reply = client_interrupt.recv(350)
        # print_msg_switch(reply)
        write_to_buffer(
                    message_buffer,
                    "Switch Input Report Reply",
                    "comment")
        write_to_buffer(message_buffer, reply, "switch")
        jc_itr.sendall(reply)

        # Sending Switch the proxy's device info
        if controller_type == JOYCON_R:
            client_interrupt.sendall(REPLY)
        elif controller_type == JOYCON_L:
            client_interrupt.sendall(REPLY)
        elif controller_type == PRO_CONTROLLER:
            client_interrupt.sendall(REPLY)

        # Waste some cycles here until we get the controllers info.
        # We don't want to proxy the device's info to the Switch
        # since it includes a MAC address.
        print("Waiting on Joy-Con Device Info")
        while True:
            jc_data = jc_itr.recv(350)
            if jc_data[1] == 0x21:
                print("Got Device Info")
                # print_msg_controller(jc_data)
                print("Joy-Con Device Info Reply Length", len(jc_data))
                write_to_buffer(
                    message_buffer,
                    "Joy-Con Device Info",
                    "comment")
                write_to_buffer(message_buffer, jc_data, "controller")
                break

        # Main loop
        print("Entering main proxy loop")
        write_to_buffer(
                    message_buffer,
                    "Entering Main Loop",
                    "comment")
        time_old = perf_counter()
        timer_old = 0
        timer_counter = 0
        while True:
            try:
                reply = client_interrupt.recv(350)
                # print_msg_switch(reply)
                write_to_buffer(message_buffer, reply, "switch")
            except BlockingIOError:
                reply = None

            if reply:
                jc_itr.sendall(reply)
            jc_data = jc_itr.recv(350)

            timer_new = int(jc_data[2])
            if timer_new < timer_old:
                timer_counter += timer_new - (timer_old - 255)
            else:
                timer_counter += timer_new - timer_old
            timer_old = timer_new

            # print_msg_controller(jc_data)
            write_to_buffer(message_buffer, jc_data, "controller")
            client_interrupt.sendall(jc_data)

    except KeyboardInterrupt:
        print("Closing sockets")

        # time_new = perf_counter()
        # print(f"Total Delta: {(time_new - time_old) * 1000}")
        # print(f"Timer Counter: {timer_counter}")

        jc_ctrl.close()
        jc_itr.close()

        switch_itr.close()
        switch_ctrl.close()

        # Write the buffer
        with open("messages.txt", "w") as f:
            f.write("\n".join(message_buffer))

    except OSError as e:
        print("Closing sockets")

        jc_ctrl.close()
        jc_itr.close()

        switch_itr.close()
        switch_ctrl.close()

        # Write the buffer
        with open("messages.txt", "w") as f:
            f.write("\n".join(message_buffer))

        raise e

    finally:
        toggle_clean_bluez(False)
