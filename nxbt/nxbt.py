from multiprocessing import Process, Lock, Queue, Manager
import queue
from enum import Enum
import atexit
import signal
import os

import dbus

from .controller import ControllerServer
from .controller import ControllerTypes
from .bluez import find_objects, toggle_input_plugin
from .bluez import find_devices_by_alias
from .bluez import SERVICE_NAME, ADAPTER_INTERFACE


JOYCON_L = ControllerTypes.JOYCON_L
JOYCON_R = ControllerTypes.JOYCON_R
PRO_CONTROLLER = ControllerTypes.PRO_CONTROLLER


class Buttons():

    Y = 'Y'
    X = 'X'
    B = 'B'
    A = 'A'
    JCL_SR = 'JCL_SR'
    JCL_SL = 'JCL_SL'
    R = 'R'
    ZR = 'ZR'
    MINUS = '-'
    PLUS = '+'
    R_STICK_PRESS = 'R_STICK_PRESS'
    L_STICK_PRESS = 'L_STICK_PRESS'
    HOME = 'HOME'
    CAPTURE = 'CAPTURE'
    DPAD_DOWN = 'DPAD_DOWN'
    DPAD_UP = 'DPAD_UP'
    DPAD_RIGHT = 'DPAD_RIGHT'
    DPAD_LEFT = 'DPAD_LEFT'
    JCR_SR = 'JCR_SR'
    JCR_SL = 'JCR_SL'
    L = 'L'
    ZL = 'ZL'


class Sticks():

    RIGHT_STICK = "R_STICK"
    LEFT_STICK = "L_STICK"


class NxbtCommands(Enum):

    CREATE_CONTROLLER = 0
    INPUT_MACRO = 1
    STOP_MACRO = 2
    CLEAR_MACROS = 3
    CLEAR_ALL_MACROS = 4
    REMOVE_CONTROLLER = 5
    QUIT = 6


class Nxbt():

    def __init__(self):

        # Main queue for nbxt tasks
        self.task_queue = Queue()

        # Sychronizes bluetooth actions
        self.__bluetooth_lock__ = Lock()

        # Creates/manages shared resources
        self.resource_manager = Manager()
        # Shared dictionary for viewing overall nxbt state.
        # Should only be read by threads and wrote to by
        # the main nxbt multiprocessing process.
        self.manager_state = self.resource_manager.dict()
        self.manager_state_lock = Lock()

        # Shared, controller management properties.
        # The controller lock is used to sychronize use.
        self.__controller_lock__ = Lock()
        self.__controller_counter__ = 0
        self.__adapters_in_use__ = {}
        self.__controller_adapter_lookup__ = {}

        # Disable the BlueZ input plugin so we can use the
        # HID control/interrupt Bluetooth ports
        toggle_input_plugin(False)

        # Exit handler
        atexit.register(self.on_exit)

        # Starting the nxbt worker process
        self.controllers = Process(
            target=self.__command_manager__,
            args=((self.task_queue), (self.manager_state)))
        # Disabling daemonization since we need to spawn
        # other controller processes, however, this means
        # we need to cleanup on exit.
        self.controllers.daemon = False
        self.controllers.start()

    def on_exit(self):

        # Need to explicitly kill the controllers process
        # since it isn't daemonized.
        if hasattr(self, "controllers") and self.controllers.is_alive():
            self.controllers.terminate()

        self.resource_manager.shutdown()

        # Re-enable the BlueZ input plugin
        toggle_input_plugin(True)

    def __command_manager__(self, task_queue, state):

        cm = ControllerManager(state, self.__bluetooth_lock__)
        # Ensure a SystemExit exception is raised on SIGTERM
        # so that we can gracefully shutdown.
        signal.signal(signal.SIGTERM, lambda sigterm_handler: quit())

        try:
            while True:
                try:
                    msg = task_queue.get_nowait()
                except queue.Empty:
                    msg = None

                if msg:
                    if msg["command"] == NxbtCommands.CREATE_CONTROLLER:
                        cm.create_controller(
                            msg["arguments"]["controller_index"],
                            msg["arguments"]["controller_type"],
                            msg["arguments"]["adapter_path"],
                            msg["arguments"]["colour_body"],
                            msg["arguments"]["colour_buttons"],
                            msg["arguments"]["reconnect_address"])
                    elif msg["command"] == NxbtCommands.INPUT_MACRO:
                        cm.input_macro(
                            msg["arguments"]["controller_index"],
                            msg["arguments"]["macro"],
                            msg["arguments"]["macro_id"])
                    elif msg["command"] == NxbtCommands.STOP_MACRO:
                        cm.stop_macro(
                            msg["arguments"]["controller_index"],
                            msg["arguments"]["macro_id"])
                    elif msg["command"] == NxbtCommands.CLEAR_MACROS:
                        cm.clear_macros(
                            msg["arguments"]["controller_index"])
                    elif msg["command"] == NxbtCommands.REMOVE_CONTROLLER:
                        cm.clear_macros(
                            msg["arguments"]["controller_index"])

        finally:
            cm.shutdown()
            quit()

    def macro(self, controller_index, macro, block=True):

        if controller_index not in self.manager_state.keys():
            raise ValueError("Specified controller does not exist")

        # Get a unique ID to identify the macro
        # so we can check when the controller is done inputting it
        macro_id = os.urandom(24).hex()
        self.task_queue.put({
            "command": NxbtCommands.INPUT_MACRO,
            "arguments": {
                "controller_index": controller_index,
                "macro": macro,
                "macro_id": macro_id,
            }
        })

        if block:
            while True:
                finished = (self.manager_state
                            [controller_index]["finished_macros"])
                if macro_id in finished:
                    break

        return macro_id

    def press_buttons(self, controller_index, buttons, up=0.1, down=0.1, block=True):

        if controller_index not in self.manager_state.keys():
            raise ValueError("Specified controller does not exist")

        macro_buttons = " ".join(buttons)
        macro_times = f"{up}s \n{down}s"
        macro = macro_buttons + " " + macro_times

        # Get a unique ID to identify the button press
        # so we can check when the controller is done inputting it
        macro_id = os.urandom(24).hex()
        self.task_queue.put({
            "command": NxbtCommands.INPUT_MACRO,
            "arguments": {
                "controller_index": controller_index,
                "macro": macro,
                "macro_id": macro_id,
            }
        })

        if block:
            while True:
                finished = (self.manager_state
                            [controller_index]["finished_macros"])
                if macro_id in finished:
                    break

        return macro_id

    def tilt_stick(self, controller_index, stick, x, y,
                   tilted=0.1, released=0.1, block=True):

        if controller_index not in self.manager_state.keys():
            raise ValueError("Specified controller does not exist")

        if x >= 0:
            x_parsed = f'+{x:03}'
        else:
            x_parsed = f'{x:04}'

        if y >= 0:
            y_parsed = f'+{y:03}'
        else:
            y_parsed = f'{y:04}'

        macro = f'{stick}@{x_parsed}{y_parsed} {tilted}s\n{released}s'

        # Get a unique ID to identify the button press
        # so we can check when the controller is done inputting it
        macro_id = os.urandom(24).hex()
        self.task_queue.put({
            "command": NxbtCommands.INPUT_MACRO,
            "arguments": {
                "controller_index": controller_index,
                "macro": macro,
                "macro_id": macro_id,
            }
        })

        if block:
            while True:
                finished = (self.manager_state
                            [controller_index]["finished_macros"])
                if macro_id in finished:
                    break

        return macro_id

    def stop_macro(self, controller_index, macro_id, block=True):

        if controller_index not in self.manager_state.keys():
            raise ValueError("Specified controller does not exist")

        self.task_queue.put({
            "command": NxbtCommands.STOP_MACRO,
            "arguments": {
                "controller_index": controller_index,
                "macro_id": macro_id,
            }
        })

        if block:
            while True:
                finished = (self.manager_state
                            [controller_index]["finished_macros"])
                if macro_id in finished:
                    break

    def clear_macros(self, controller_index):

        if controller_index not in self.manager_state.keys():
            raise ValueError("Specified controller does not exist")

        self.task_queue.put({
            "command": NxbtCommands.CLEAR_MACROS,
            "arguments": {
                "controller_index": controller_index,
            }
        })

    def clear_all_macros(self):

        for controller in self.manager_state.keys():
            self.clear_macros(controller)

    def create_controller(self, controller_type, adapter_path,
                          colour_body=None, colour_buttons=None,
                          reconnect_address=None):

        if adapter_path not in self.get_available_adapters():
            raise ValueError("Specified adapter is unavailable")

        if adapter_path in self.__adapters_in_use__.keys():
            raise ValueError("Specified adapter in use")

        controller_index = None
        try:
            self.__controller_lock__.acquire()
            self.task_queue.put({
                "command": NxbtCommands.CREATE_CONTROLLER,
                "arguments": {
                    "controller_index": self.__controller_counter__,
                    "controller_type": controller_type,
                    "adapter_path": adapter_path,
                    "colour_body": colour_body,
                    "colour_buttons": colour_buttons,
                    "reconnect_address": reconnect_address,
                }
            })
            controller_index = self.__controller_counter__
            self.__controller_counter__ += 1
            self.__adapters_in_use__[adapter_path] = controller_index
            self.__controller_adapter_lookup__[controller_index] = adapter_path

            # Block until the controller is ready
            # This needs to be done to prevent race conditions
            # on Bluetooth resources.
            if type(controller_index) == int:
                while True:
                    if controller_index in self.manager_state.keys():
                        state = self.manager_state[controller_index]
                        if (state["state"] == "connecting" or
                                state["state"] == "reconnecting"):
                            break
        finally:
            self.__controller_lock__.release()

        return controller_index

    def remove_controller(self, controller_index):

        if controller_index not in self.manager_state.keys():
            raise ValueError("Specified controller does not exist")

        self.__controller_lock__.acquire()
        try:
            adapter_path = self.__controller_adapter_lookup__.pop(controller_index, None)
            self.__adapters_in_use__.pop(adapter_path, None)
        finally:
            self.__controller_lock__.release()

        self.task_queue.put({
            "command": NxbtCommands.REMOVE_CONTROLLER,
            "arguments": {
                "controller_index": controller_index,
            }
        })

    def wait_for_connection(self, controller_index):

        while not self.state[controller_index]["state"] == "connected":
            pass

    def get_available_adapters(self):

        bus = dbus.SystemBus()
        adapters = find_objects(bus, SERVICE_NAME, ADAPTER_INTERFACE)

        return adapters

    def get_switch_addresses(self):

        return (find_devices_by_alias("Nintendo Switch"))

    @property
    def state(self):

        return self.manager_state


class ControllerManager():

    def __init__(self, state, lock):

        self.state = state
        self.lock = lock
        self.controller_resources = Manager()
        self.__controller_queues__ = {}
        self.__children__ = {}

    def create_controller(self, index, controller_type, adapter_path,
                          colour_body=None, colour_buttons=None,
                          reconnect_address=None):

        controller_queue = Queue()

        controller_state = self.controller_resources.dict()
        controller_state["state"] = "initializing"
        controller_state["finished_macros"] = []
        controller_state["errors"] = False

        self.__controller_queues__[index] = controller_queue

        self.state[index] = controller_state

        server = ControllerServer(controller_type,
                                  adapter_path=adapter_path,
                                  lock=self.lock,
                                  state=controller_state,
                                  task_queue=controller_queue,
                                  colour_body=colour_body,
                                  colour_buttons=colour_buttons)
        controller = Process(target=server.run, args=(reconnect_address,))
        controller.daemon = True
        self.__children__[index] = controller
        controller.start()

    def input_macro(self, index, macro, macro_id):

        self.__controller_queues__[index].put({
            "type": "macro",
            "macro": macro,
            "macro_id": macro_id
        })

    def stop_macro(self, index, macro_id):

        self.__controller_queues__[index].put({
            "type": "stop",
            "macro_id": macro_id,
        })

    def clear_macros(self, index):

        self.__controller_queues__[index].put({
            "type": "clear",
        })

    def remove_controller(self, index):

        self.__children__[index].kill()

    def shutdown(self):

        # Loop over children and kill all
        for index in self.__children__.keys():
            child = self.__children__[index]
            child.terminate()

        self.controller_resources.shutdown()
