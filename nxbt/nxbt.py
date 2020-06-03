from multiprocessing import Process, Lock
from multiprocessing import Queue, Manager
import queue
from enum import Enum
import atexit
import os

import dbus

from .controller import ControllerServer
from .bluez import find_objects, toggle_input_plugin
from .bluez import SERVICE_NAME, ADAPTER_INTERFACE


class NxbtCommands(Enum):

    CREATE_CONTROLLER = 0
    INPUT_MACRO = 1


class Nxbt():

    def __init__(self):

        # Main queue for nbxt tasks
        self.task_queue = Queue()

        # Sychronizes bluetooth actions
        self.__bluetooth_lock = Lock()

        # Creates/manages shared resources
        self.resource_manager = Manager()
        # Shared dictionary for viewing overall nxbt state.
        # Should only be read by threads and wrote to by
        # the main nxbt multiprocessing process.
        self.manager_state = self.resource_manager.dict()
        self.manager_state_lock = Lock()

        # Shared, controller management properties.
        # The controller lock is used to sychronize use.
        self.__controller_lock = Lock()
        self.__controller_counter = 0
        self.__adapters_in_use = []

        # Disable the BlueZ input plugin so we can use the
        # HID control/interrupt Bluetooth ports
        toggle_input_plugin(False)

        # Exit handler
        atexit.register(self.on_exit)

        # Starting the nxbt worker process
        self.controllers = Process(
            target=self.__command_manager,
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

        # Re-enable the BlueZ input plugin
        toggle_input_plugin(True)

    def __command_manager(self, task_queue, state):

        cm = ControllerManager(state, self.__bluetooth_lock)

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
                        msg["arguments"]["colour_buttons"])
                elif msg["command"] == NxbtCommands.INPUT_MACRO:
                    cm.input_macro(
                        msg["arguments"]["controller_index"],
                        msg["arguments"]["macro"],
                        msg["arguments"]["macro_id"])

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

    def create_controller(self, controller_type, adapter_path,
                          colour_body=None, colour_buttons=None):

        if adapter_path not in self.get_available_adapters():
            raise ValueError("Specified adapter is unavailable")

        if adapter_path in self.__adapters_in_use:
            raise ValueError("Specified adapter in use")

        controller_index = None
        try:
            self.__controller_lock.acquire()
            self.task_queue.put({
                "command": NxbtCommands.CREATE_CONTROLLER,
                "arguments": {
                    "controller_index": self.__controller_counter,
                    "controller_type": controller_type,
                    "adapter_path": adapter_path,
                    "colour_body": colour_body,
                    "colour_buttons": colour_buttons,
                }
            })
            controller_index = self.__controller_counter
            self.__controller_counter += 1
            self.__adapters_in_use.append(adapter_path)

            # Block until the controller is ready
            # This needs to be done to prevent race conditions
            # on DBus resources.
            if type(controller_index) == int:
                while True:
                    if controller_index in self.manager_state.keys():
                        state = self.manager_state[controller_index]
                        if (state["state"] == "connecting" or
                                state["state"] == "reconnecting"):
                            break
        finally:
            self.__controller_lock.release()
            pass

        return controller_index

    def get_available_adapters(self):

        bus = dbus.SystemBus()
        adapters = find_objects(bus, SERVICE_NAME, ADAPTER_INTERFACE)

        return adapters

    @property
    def state(self):

        return self.manager_state


class ControllerManager():

    def __init__(self, state, lock):

        self.state = state
        self.lock = lock
        self.controller_resources = Manager()
        self.__controller_queues = {}

    def create_controller(self, index, controller_type, adapter_path,
                          colour_body=None, colour_buttons=None):

        controller_queue = Queue()

        controller_state = self.controller_resources.dict()
        controller_state["state"] = "initializing"
        controller_state["finished_macros"] = []
        controller_state["errors"] = False

        self.__controller_queues[index] = controller_queue

        self.state[index] = controller_state

        server = ControllerServer(controller_type,
                                  adapter_path=adapter_path,
                                  lock=self.lock,
                                  state=controller_state,
                                  task_queue=controller_queue,
                                  colour_body=colour_body,
                                  colour_buttons=colour_buttons)
        controller = Process(target=server.run)
        controller.daemon = True
        controller.start()

    def input_macro(self, index, macro, macro_id):

        # finished = self.state[index]["finished_macros"]
        # finished.append(macro_id)
        # self.state[index]["finished_macros"] = finished

        self.__controller_queues[index].put({
            "type": "macro",
            "macro": macro,
            "macro_id": macro_id
        })
