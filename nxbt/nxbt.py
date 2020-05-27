from multiprocessing import Process, Lock
from multiprocessing import Queue, Manager
import queue
from enum import Enum
import atexit

import dbus

from .controller import ControllerServer
from .bluez import find_objects, SERVICE_NAME, ADAPTER_INTERFACE


class NxbtCommands(Enum):

    CREATE_CONTROLLER = 0


class Nxbt():

    def __init__(self):

        # Main queue for nbxt tasks
        self.task_queue = Queue()

        # Creates/manages shared resources
        self.resource_manager = Manager()
        # Shared dictionary for viewing overall nxbt state.
        # Should only be read by threads and wrote to by
        # the main nxbt multiprocessing process.
        self.state = self.resource_manager.dict()

        # Shared, controller management properties.
        # The controller lock is used to sychronize use.
        self.__controller_lock = Lock()
        self.__controller_counter = 0
        self.__adapters_in_use = []

        # Exit handler
        atexit.register(self.on_exit)

        # Starting the nxbt worker process
        self.controllers = Process(
            target=self.__command_manager,
            args=((self.task_queue), (self.state)))
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

    def __command_manager(self, task_queue, state):

        cm = ControllerManager(state)

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
                        msg["arguments"]["adapter_path"])

    def send_input(self, msg):

        self.task_queue.put(msg)

    def create_controller(self, controller_type, adapter_path):

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
                }
            })
            controller_index = self.__controller_counter
            self.__controller_counter += 1
            self.__adapters_in_use.append(adapter_path)
        finally:
            self.__controller_lock.release()
            pass

        return controller_index

    def get_available_adapters(self):

        bus = dbus.SystemBus()
        adapters = find_objects(bus, SERVICE_NAME, ADAPTER_INTERFACE)

        return adapters

    def get_state(self):

        return self.state


class ControllerManager():

    def __init__(self, state):

        self.state = state
        self.controller_resources = Manager()
        self.controller_states = []
        self.controller_queues = []

    def create_controller(self, index, controller_type, adapter_path):

        controller_queue = Queue()

        controller_state = self.controller_resources.dict()
        controller_state["state"] = "initializing"
        controller_state["finished_macros"] = []
        controller_state["errors"] = False

        self.state[index] = controller_state
        # Get the last parameter of the path, AKA the ID
        device_id = adapter_path.split("/")[-1]

        server = ControllerServer(controller_type, bt_device_id=device_id)
        controller = Process(target=server.run, args=(
            None, controller_state, controller_queue))
        controller.daemon = True
        controller.start()
