import socket
import fcntl
import os
import time

from .controller import Controller, ControllerTypes
from ..bluez import BlueZ
from .protocol import ControllerProtocol
from .utils import format_msg_controller, format_msg_switch


class ControllerServer():

    def __init__(self, controller_type, bt_device_id="hci0"):

        self.controller_type = controller_type

        # Intializing Bluetooth
        self.bt = BlueZ(device_id=bt_device_id)

        self.controller = Controller(self.bt, self.controller_type)
        self.protocol = ControllerProtocol(
            self.controller_type,
            self.bt.address)

    def run(self, reconnect_address=None):
        """Runs the mainloop of the controller server.

        :param reconnect_address: The Bluetooth MAC address of a
        previously connected to Nintendo Switch, defaults to None
        :type reconnect_address: string, optional
        """

        self.controller.setup()

        if reconnect_address:
            itr, s_itr, ctrl, s_ctrl = self.reconnect(reconnect_address)
        else:
            itr, s_itr, ctrl, s_ctrl = self.connect()

        # Mainloop
        while True:
            # Attempt to get output from Switch
            try:
                reply = itr.recv(50)
                if len(reply) > 40:
                    print(format_msg_switch(reply))
            except BlockingIOError:
                reply = None

            self.protocol.process_commands(reply)
            msg = self.protocol.get_report()

            if reply:
                print(format_msg_controller(msg))

            try:
                itr.sendall(msg)
            except BlockingIOError:
                continue

            # Respond at 120Hz for Pro Controller
            # or 60Hz for Joy-Cons
            if self.controller_type == ControllerTypes.PRO_CONTROLLER:
                time.sleep(1/120)
            else:
                time.sleep(1/60)

    def connect(self):
        """Configures as a specified controller, pairs with a Nintendo Switch,
        and creates/accepts sockets for communication with the Switch.
        """

        # Creating control and interrupt sockets
        s_ctrl = socket.socket(
            family=socket.AF_BLUETOOTH,
            type=socket.SOCK_SEQPACKET,
            proto=socket.BTPROTO_L2CAP)
        s_itr = socket.socket(
            family=socket.AF_BLUETOOTH,
            type=socket.SOCK_SEQPACKET,
            proto=socket.BTPROTO_L2CAP)

        # Setting up HID interrupt/control sockets
        try:
            s_ctrl.bind((self.bt.address, 17))
            s_itr.bind((self.bt.address, 19))
        except OSError:
            s_ctrl.bind((socket.BDADDR_ANY, 17))
            s_itr.bind((socket.BDADDR_ANY, 19))

        s_itr.listen(1)
        s_ctrl.listen(1)

        self.bt.set_discoverable(True)

        ctrl, ctrl_address = s_ctrl.accept()
        itr, itr_address = s_itr.accept()

        # Send an empty input report to the Switch to prompt a reply
        self.protocol.process_commands(None)
        msg = self.protocol.get_report()
        itr.sendall(msg)

        # Setting interrupt connection as non-blocking
        # In this case, non-blocking means it throws a "BlockingIOError"
        # for sending and receiving, instead of blocking
        fcntl.fcntl(itr, fcntl.F_SETFL, os.O_NONBLOCK)

        # Mainloop
        while True:
            # Attempt to get output from Switch
            try:
                reply = itr.recv(50)
                if len(reply) > 40:
                    print(format_msg_switch(reply))
            except BlockingIOError:
                reply = None

            self.protocol.process_commands(reply)
            msg = self.protocol.get_report()

            #if reply:
            #    print(format_msg_controller(msg))

            try:
                itr.sendall(msg)
            except BlockingIOError:
                continue

            # Exit pairing loop on set player lights
            if reply and len(reply) > 45 and reply[11] == 0x30:
                break

            # Switch responds to packets slower during pairing
            # Pairing cycle responds optimally on a 15Hz loop
            time.sleep(1/15)

        return itr, s_itr, ctrl, s_ctrl

    def reconnect(self, reconnect_address):
        """Attempts to reconnect with a Switch at the given address.

        :param reconnect_address: The Bluetooth MAC address of the Switch
        :type reconnect_address: string
        """

        device_path = self.bt.find_device_by_address(reconnect_address)
        if not device_path:
            raise ValueError(
                "No device Switch found with MAC address " + reconnect_address)

        # Creating control and interrupt sockets
        s_ctrl = socket.socket(
            family=socket.AF_BLUETOOTH,
            type=socket.SOCK_SEQPACKET,
            proto=socket.BTPROTO_L2CAP)
        s_itr = socket.socket(
            family=socket.AF_BLUETOOTH,
            type=socket.SOCK_SEQPACKET,
            proto=socket.BTPROTO_L2CAP)

        # Setting up HID interrupt/control sockets
        s_ctrl.bind((self.bt.address, 17))
        s_itr.bind((self.bt.address, 19))

        s_itr.listen(1)
        s_ctrl.listen(1)

        self.bt.connect_device(device_path)

        ctrl, ctrl_address = s_ctrl.accept()
        itr, itr_address = s_itr.accept()

        print("Here")
