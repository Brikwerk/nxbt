import socket
import fcntl
import os
import time
import queue
import logging
import traceback

from .controller import Controller, ControllerTypes
from ..bluez import BlueZ
from .protocol import ControllerProtocol
from .input import InputParser
from .utils import format_msg_controller, format_msg_switch


class ControllerServer():

    def __init__(self, controller_type, adapter_path="/org/bluez/hci0",
                 state=None, task_queue=None, lock=None, colour_body=None,
                 colour_buttons=None):

        self.logger = logging.getLogger('nxbt')
        # Cache logging level to increase performance on checks
        self.logger_level = self.logger.level

        if state:
            self.state = state
        else:
            self.state = {
                "state": "",
                "finished_macros": [],
                "errors": None,
                "direct_input": None
            }

        self.task_queue = task_queue

        self.controller_type = controller_type
        self.colour_body = colour_body
        self.colour_buttons = colour_buttons

        if lock:
            self.lock = lock

        self.reconnect_counter = 0

        # Intializing Bluetooth
        self.bt = BlueZ(adapter_path=adapter_path)

        self.controller = Controller(self.bt, self.controller_type)
        self.protocol = ControllerProtocol(
            self.controller_type,
            self.bt.address,
            colour_body=self.colour_body,
            colour_buttons=self.colour_buttons)

        self.input = InputParser(self.protocol)

        self.slow_input_frequency = False

    def run(self, reconnect_address=None):
        """Runs the mainloop of the controller server.

        :param reconnect_address: The Bluetooth MAC address of a
        previously connected to Nintendo Switch, defaults to None
        :type reconnect_address: string or list, optional
        """

        self.state["state"] = "initializing"

        try:
            # If we have a lock, prevent other controllers
            # from initializing at the same time and saturating the DBus,
            # potentially causing a kernel panic.
            if self.lock:
                self.lock.acquire()
            try:
                self.controller.setup()

                if reconnect_address:
                    itr, ctrl = self.reconnect(reconnect_address)
                else:
                    itr, ctrl = self.connect()
            finally:
                if self.lock:
                    self.lock.release()

            self.switch_address = itr.getsockname()[0]

            self.state["state"] = "connected"

            self.mainloop(itr, ctrl)

        except KeyboardInterrupt:
            pass
        except Exception:
            self.state["state"] = "crashed"
            self.state["errors"] = traceback.format_exc()
            return self.state

    def mainloop(self, itr, ctrl):

        # Mainloop
        while True:
            # Start timing the command processing
            timer_start = time.perf_counter()

            # Attempt to get output from Switch
            try:
                reply = itr.recv(50)
                if self.logger_level <= logging.DEBUG and len(reply) > 40:
                    self.logger.debug(format_msg_switch(reply))
            except BlockingIOError:
                reply = None

            # Getting any inputs from the task queue
            if self.task_queue:
                try:
                    while True:
                        msg = self.task_queue.get_nowait()
                        if msg and msg["type"] == "macro":
                            self.input.buffer_macro(
                                msg["macro"], msg["macro_id"])
                        elif msg and msg["type"] == "stop":
                            self.input.stop_macro(
                                msg["macro_id"], state=self.state)
                        elif msg and msg["type"] == "clear":
                            self.input.clear_macros()
                except queue.Empty:
                    pass

            # Set Direct Input
            if self.state["direct_input"]:
                self.input.set_controller_input(self.state["direct_input"])

            self.protocol.process_commands(reply)
            self.input.set_protocol_input(state=self.state)

            msg = self.protocol.get_report()

            if self.logger_level <= logging.DEBUG and reply and len(reply) > 45:
                self.logger.debug(format_msg_controller(msg))

            try:
                itr.sendall(msg)
            except BlockingIOError:
                continue
            except OSError as e:
                # Attempt to reconnect to the Switch
                itr, ctrl = self.save_connection(e)

            # Figure out how long it took to process commands
            timer_end = time.perf_counter()
            elapsed_time = (timer_end - timer_start)

            if self.slow_input_frequency:
                # Check if we can switch out of slow frequency input
                if self.input.exited_grip_order_menu:
                    self.slow_input_frequency = False

                if elapsed_time < 1/15:
                    time.sleep(1/15 - elapsed_time)
            else:
                # Respond at 120Hz for Pro Controller
                # or 60Hz for Joy-Cons.
                # Sleep timers are compensated with the elapsed command
                # processing time.
                if self.controller_type == ControllerTypes.PRO_CONTROLLER:
                    if elapsed_time < 1/120:
                        time.sleep(1/120 - elapsed_time)
                else:
                    if elapsed_time < 1/60:
                        time.sleep(1/60 - elapsed_time)

    def save_connection(self, error, state=None):

        while self.reconnect_counter < 2:
            try:
                self.logger.debug("Attempting to reconnect")
                # Reinitialize the protocol
                self.protocol = ControllerProtocol(
                    self.controller_type,
                    self.bt.address,
                    colour_body=self.colour_body,
                    colour_buttons=self.colour_buttons)
                if self.lock:
                    self.lock.acquire()
                try:
                    itr, ctrl = self.reconnect(self.switch_address)
                    return itr, ctrl
                finally:
                    if self.lock:
                        self.lock.release()
            except OSError:
                self.reconnect_counter += 1
                self.logger.exception(error)
                time.sleep(0.5)

        # If we can't reconnect, transition to attempting
        # to connect to any Switch.
        self.logger.debug("Connecting to any Switch")
        self.reconnect_counter = 0

        # Reinitialize the protocol
        self.protocol = ControllerProtocol(
            self.controller_type,
            self.bt.address,
            colour_body=self.colour_body,
            colour_buttons=self.colour_buttons)
        self.input.reassign_protocol(self.protocol)

        # Since we were forced to attempt a reconnection
        # we need to press the L/SL and R/SR buttons before
        # we can proceed with any input.
        if self.controller_type == ControllerTypes.PRO_CONTROLLER:
            self.input.current_macro_commands = "L R 0.0s".strip(" ").split(" ")
        elif self.controller_type == ControllerTypes.JOYCON_L:
            self.input.current_macro_commands = "JCL_SL JCL_SR 0.0s".strip(" ").split(" ")
        elif self.controller_type == ControllerTypes.JOYCON_R:
            self.input.current_macro_commands = "JCR_SL JCR_SR 0.0s".strip(" ").split(" ")

        if self.lock:
            self.lock.acquire()
        try:
            itr, ctrl = self.connect()
        finally:
            if self.lock:
                self.lock.release()

        self.state["state"] = "connected"

        self.switch_address = itr.getsockname()[0]

        return itr, ctrl

    def connect(self):
        """Configures as a specified controller, pairs with a Nintendo Switch,
        and creates/accepts sockets for communication with the Switch.
        """

        self.state["state"] = "connecting"

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

        # Setting interrupt connection as non-blocking.
        # In this case, non-blocking means it throws a "BlockingIOError"
        # for sending and receiving, instead of blocking.
        fcntl.fcntl(itr, fcntl.F_SETFL, os.O_NONBLOCK)

        # Mainloop
        while True:
            # Attempt to get output from Switch
            try:
                reply = itr.recv(50)
                if self.logger_level <= logging.DEBUG and len(reply) > 40:
                    self.logger.debug(format_msg_switch(reply))
            except BlockingIOError:
                reply = None

            self.protocol.process_commands(reply)
            msg = self.protocol.get_report()

            if self.logger_level <= logging.DEBUG and reply:
                self.logger.debug(format_msg_controller(msg))

            try:
                itr.sendall(msg)
            except BlockingIOError:
                continue

            # Exit pairing loop when player lights have been set and
            # vibration has been enabled
            if (reply and len(reply) > 45 and
                    self.protocol.vibration_enabled and self.protocol.player_number):
                break

            # Switch responds to packets slower during pairing
            # Pairing cycle responds optimally on a 15Hz loop
            time.sleep(1/15)

        self.slow_input_frequency = True
        self.input.exited_grip_order_menu = False

        return itr, ctrl

    def reconnect(self, reconnect_address):
        """Attempts to reconnect with a Switch at the given address.

        :param reconnect_address: The Bluetooth MAC address of the Switch
        :type reconnect_address: string or list
        """

        def recreate_sockets():
            # Creating control and interrupt sockets
            ctrl = socket.socket(
                family=socket.AF_BLUETOOTH,
                type=socket.SOCK_SEQPACKET,
                proto=socket.BTPROTO_L2CAP)
            itr = socket.socket(
                family=socket.AF_BLUETOOTH,
                type=socket.SOCK_SEQPACKET,
                proto=socket.BTPROTO_L2CAP)

            return itr, ctrl

        self.state["state"] = "reconnecting"

        itr = None
        ctrl = None
        if type(reconnect_address) == list:
            for address in reconnect_address:
                test_itr, test_ctrl = recreate_sockets()
                try:
                    # Setting up HID interrupt/control sockets
                    test_ctrl.connect((address, 17))
                    test_itr.connect((address, 19))

                    itr = test_itr
                    ctrl = test_ctrl
                except OSError:
                    test_itr.close()
                    test_ctrl.close()
                    pass
        elif type(reconnect_address) == str:
            test_itr, test_ctrl = recreate_sockets()

            # Setting up HID interrupt/control sockets
            test_ctrl.connect((reconnect_address, 17))
            test_itr.connect((reconnect_address, 19))

            itr = test_itr
            ctrl = test_ctrl

        if not itr and not ctrl:
            raise OSError("Unable to reconnect to sockets at the given address(es)",
                          reconnect_address)

        fcntl.fcntl(itr, fcntl.F_SETFL, os.O_NONBLOCK)

        # Send an empty input report to the Switch to prompt a reply
        self.protocol.process_commands(None)
        msg = self.protocol.get_report()
        itr.sendall(msg)

        # Setting interrupt connection as non-blocking
        # In this case, non-blocking means it throws a "BlockingIOError"
        # for sending and receiving, instead of blocking
        fcntl.fcntl(itr, fcntl.F_SETFL, os.O_NONBLOCK)

        return itr, ctrl
