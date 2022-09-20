import socket
import fcntl
import os
import time
import queue
import logging
import traceback
import atexit
from threading import Thread
import statistics as stat

from .controller import Controller, ControllerTypes
from ..bluez import BlueZ, find_devices_by_alias
from .protocol import ControllerProtocol
from .input import InputParser
from .utils import format_msg_controller, format_msg_switch


class ControllerServer():

    def __init__(self, controller_type, adapter_path="/org/bluez/hci0",
                 state=None, task_queue=None, lock=None, colour_body=None,
                 colour_buttons=None, frequency=66):

        self.logger = logging.getLogger('nxbt')
        # Cache logging level to increase performance on checks
        self.logger_level = self.logger.level

        self.frequency = frequency

        atexit.register(self._on_exit)

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

        # Debug timekeeping storage array
        self.times = []

        # Initial reconnection overload protection
        self.tick = 1
        self.cached_msg = ''

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
                    try:
                        itr, ctrl = self.reconnect(reconnect_address)
                    except OSError:
                        itr, ctrl = self.connect()
                else:
                    itr, ctrl = self.connect()
            finally:
                if self.lock:
                    self.lock.release()

            self.switch_address = itr.getpeername()[0]
            self.state["last_connection"] = self.switch_address

            self.state["state"] = "connected"

            self.mainloop(itr, ctrl)

        except KeyboardInterrupt:
            pass
        except Exception:
            try:
                self.state["state"] = "crashed"
                self.state["errors"] = traceback.format_exc()
                return self.state
            except Exception as e:
                self.logger.debug("Error during graceful shutdown:")
                self.logger.debug(traceback.format_exc())

    def mainloop(self, itr, ctrl):

        duration_start = time.perf_counter_ns()
        period = 1 / self.frequency
        period_ns = int(period * 1_000_000_000)
        t = time.perf_counter_ns()
        while True:
            # Start timing command processing
            timer_start = time.perf_counter_ns()

            # Attempt to get output from Switch
            try:
                reply = itr.recv(50)
                if len(reply) > 40:
                    self.logger.debug(format_msg_switch(reply))
            except BlockingIOError:
                reply = None
            except ConnectionAbortedError:
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
                # Cache the last packet to prevent overloading the switch
                # with packets on the "Change Grip/Order" menu.
                if msg[3:] != self.cached_msg:
                    itr.sendall(msg)
                    self.cached_msg = msg[3:]
                # Send a blank packet every so often to keep the Switch
                # from disconnecting from the controller.
                elif self.tick >= 132:
                    itr.sendall(msg)
                    self.tick = 0
            except BlockingIOError:
                continue
            except OSError as e:
                # Attempt to reconnect to the Switch
                itr, ctrl = self.save_connection(e)

            # Figure out how long it took to process commands
            duration_end = time.perf_counter_ns()
            duration_elapsed = duration_end - duration_start
            duration_start = duration_end
            
            t += period_ns
            #time.sleep(max(0,t-time.perf_counter()))
            while True:
                if time.perf_counter_ns() > t:
                    break

            self.tick += 1

            if self.logger_level <= logging.DEBUG:
                self.times.append(duration_elapsed)
                if len(self.times) > 100:
                    self.times.pop()
                mean_time = stat.mean(self.times)

                self.logger.debug(
                    f"Tick: {self.tick}, Mean Time: {str(1/mean_time)}")


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
                self.input.reassign_protocol(self.protocol)
                if self.lock:
                    self.lock.acquire()
                try:
                    itr, ctrl = self.reconnect(self.switch_address)

                    received_first_message = False
                    while True:
                        # Attempt to get output from Switch
                        try:
                            reply = itr.recv(50)
                            if self.logger_level <= logging.DEBUG and len(reply) > 40:
                                self.logger.debug(format_msg_switch(reply))
                        except BlockingIOError:
                            reply = None

                        if reply:
                            received_first_message = True

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
                        if not received_first_message:
                            time.sleep(1)
                        else:
                            time.sleep(1/15)

                    self.state["state"] = "connected"
                    return itr, ctrl
                finally:
                    if self.lock:
                        self.lock.release()
            except OSError:
                self.reconnect_counter += 1
                self.logger.debug(error)
                time.sleep(0.5)

        # If we can't reconnect, transition to attempting
        # to connect to any Switch.
        self.logger.debug("Connecting to any Switch")
        self.reconnect_counter = 0

        # Reinitialize initial communication overload protections
        self.tick = 1

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

    def connection_reset_watchdog(self):

        connected_devices = []
        connected_devices_count = {}
        while self._crw_running:
            # Check that the adapter is still discoverable
            if not self.bt.discoverable:
                # If not, ensure it's powered, pariable and visible.
                # This action needs to be undertaken due to systemctl
                # performing a delayed reset of the adapter when
                # restarting the Bluetooth daemon.
                time.sleep(0.75) # Wait for systemctl to disable all properties
                self.bt.set_powered(True)
                self.bt.set_pairable(True)
                self.bt.set_pairable_timeout(0)
                self.bt.set_discoverable(True)
                self.bt.set_class("0x02508")

            paths = self.bt.find_connected_devices(alias_filter="Nintendo Switch")
            # Keep track of Switches that connect
            if len(paths) > 0:
                connected_devices = list(set(connected_devices + paths))
            
            # Increment a counter if a Switch connected and disconnected
            disconnected = list(set(connected_devices) - set(paths))
            if len(disconnected) > 0:
                for path in disconnected:
                    if path not in connected_devices_count.keys():
                        connected_devices_count[path] = 1
                    else:
                        connected_devices_count[path] += 1
                connected_devices = list(set(connected_devices) - set(disconnected))
            
            # Delete Switches that connect/disconnect twice.
            # This behaviour is characteristic of connection issues and is corrected
            # by removing the Switch's connection to the system.
            if len(connected_devices_count.keys()) > 0:
                for key in connected_devices_count.keys():
                    if connected_devices_count[key] >= 2:
                        self.logger.debug(
                            "A Nintendo Switch disconnected. Resetting Connection...")
                        self.logger.debug(f"Removing {str(key)}")
                        self.bt.remove_device(key)
                        connected_devices_count[key] = 0

            time.sleep(0.1)

    def connect(self):
        """Configures as a specified controller, pairs with a Nintendo Switch,
        and creates/accepts sockets for communication with the Switch.
        """

        # The controller server will continue attempting to connect
        # to any Nintendo Switch until the connection procedure fully
        # succeeds. This prevents situations where the Switch will
        # disconnect during a connection.
        while True:
            try:
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

                # WARNING:
                # A device's class must be set **AFTER** discoverability
                # is set. If it is set before or in a similar timeframe,
                # the class will be reset to the default value.
                self.bt.set_class("0x02508")

                self._crw_running = True
                crw = Thread(target = self.connection_reset_watchdog)
                crw.start()

                itr, itr_address = s_itr.accept()
                ctrl, ctrl_address = s_ctrl.accept()

                self._crw_running = False

                # Send an empty input report to the Switch to prompt a reply
                self.protocol.process_commands(None)
                msg = self.protocol.get_report()
                itr.sendall(msg)

                # Setting interrupt connection as non-blocking.
                # In this case, non-blocking means it throws a "BlockingIOError"
                # for sending and receiving, instead of blocking.
                fcntl.fcntl(itr, fcntl.F_SETFL, os.O_NONBLOCK)

                # Mainloop
                received_first_message = False
                while True:
                    # Attempt to get output from Switch
                    try:
                        reply = itr.recv(50)
                        if self.logger_level <= logging.DEBUG and len(reply) > 40:
                            self.logger.debug(format_msg_switch(reply))
                    except BlockingIOError:
                        reply = None

                    if reply:
                        received_first_message = True

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
                    if not received_first_message:
                        time.sleep(1)
                    else:
                        time.sleep(1/15)
                
                break
            except OSError as e:
                self.logger.debug(e)

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

    def _on_exit(self):
        self.bt.reset_address()
