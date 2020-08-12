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
    """The button object containing the button string constants.
    """

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
    """The sticks object containing the joystick string constants.
    """

    RIGHT_STICK = "R_STICK"
    LEFT_STICK = "L_STICK"


class NxbtCommands(Enum):
    """An enumeration containing the nxbt message
    commands.
    """

    CREATE_CONTROLLER = 0
    INPUT_MACRO = 1
    STOP_MACRO = 2
    CLEAR_MACROS = 3
    CLEAR_ALL_MACROS = 4
    REMOVE_CONTROLLER = 5
    QUIT = 6


class Nxbt():
    """The nxbt object implements the core multiprocessing logic
    and message passing API that acts as the central of the application.
    Upon creation, a multiprocessing Process is spun off to act at the
    manager for all emulated Nintendo Switch controllers. Messages
    are passed into a queue which is consumed and acted upon by the
    __command_manager__.

    All function calls that interact or control the emulated controllers
    are simply message constructors that submit to the central task_queue.
    This allows for thread-safe control of emulated controllers.
    """

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
        atexit.register(self._on_exit)

        # Starting the nxbt worker process
        self.controllers = Process(
            target=self.__command_manager__,
            args=((self.task_queue), (self.manager_state)))
        # Disabling daemonization since we need to spawn
        # other controller processes, however, this means
        # we need to cleanup on exit.
        self.controllers.daemon = False
        self.controllers.start()

    def _on_exit(self):
        """The exit handler function used with the atexit module.
        This function attempts to gracefully exit by terminating
        all spun up multiprocessing Processes. This is done to
        ensure no zombie processes linger after exit.
        """

        # Need to explicitly kill the controllers process
        # since it isn't daemonized.
        if hasattr(self, "controllers") and self.controllers.is_alive():
            self.controllers.terminate()

        self.resource_manager.shutdown()

        # Re-enable the BlueZ input plugin
        toggle_input_plugin(True)

    def __command_manager__(self, task_queue, state):
        """Used as the main multiprocessing Process that is launched
        on startup to handle the message passing and instantiation of
        the controllers. Messages are pulled out of a Queue and passed
        as appropriately phrased function calls to the ControllerManager.

        :param task_queue: A multiprocessing Queue used as the source
        of messages
        :type task_queue: multiprocessing.Queue
        :param state: A dict used to store the shared state of the
        emulated controllers.
        :type state: multiprocessing.Manager().dict
        """

        cm = __ControllerManager__(state, self.__bluetooth_lock__)
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
        """Used to input a given macro on a specified controller.
        This is done by creating and passing an INPUT_MACRO
        message into the task queue with the given macro.

        If block is set to True, this function waits until the
        macro_id (generated on the submission of the macro)
        shows up under the "finished_macros" list communicated
        under the controllers shared state.

        :param controller_index: The index of a given controller
        :type controller_index: int
        :param macro: The series of button presses and timings
        to be passed to the controller
        :type macro: string
        :param block: A boolean variable indicating whether or not
        to block until the macro completes, defaults to True
        :type block: bool, optional
        :raises ValueError: If the controller_index does not exist
        :return: The generated ID of the passed macro. This ID
        will show up under the "finished_macros" list communicated
        in the controllers shared state.
        :rtype: str
        """

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

    def press_buttons(self, controller_index, buttons, down=0.1, up=0.1, block=True):
        """Used to press a given set of buttons on the controller for a
        specified up and down duration. This is done by inputting a macro
        configured with the specified button presses and timings.

        :param controller_index: The index of a given controller
        :type controller_index: int
        :param buttons: A list of nxbt.Buttons
        :type buttons: list
        :param down: How long to hold the buttons down for
        in seconds, defaults to 0.1
        :type down: float, optional
        :param up: How long to release the button for
        in seconds, defaults to 0.1
        :type up: float, optional
        :param block: A boolean variable indicating whether or not
        to block until the macro completes, defaults to True
        :type block: bool, optional
        :return: The generated ID of the passed macro. This ID
        will show up under the "finished_macros" list communicated
        in the controllers shared state.
        :rtype: str
        """

        macro_buttons = " ".join(buttons)
        macro_times = f"{down}s \n{up}s"
        macro = macro_buttons + " " + macro_times

        macro_id = self.macro(controller_index, macro, block=block)

        return macro_id

    def tilt_stick(self, controller_index, stick, x, y,
                   tilted=0.1, released=0.1, block=True):
        """Used to tilt a given stick on the controller for a
        specified tilted and released duration. This is done by
        inputting a macro configured with the specified stick tilts
        and timings.

        :param controller_index: The index of a given controller
        :type controller_index: int
        :param stick: The right or left nxbt.Stick
        :type stick: nxbt.Stick
        :param x: The positive or negative X-Axis of the stick on
        a 0 to 100 scale
        :type x: int
        :param y: The positive or negative Y-Axis of the stick on
        a 0 to 100 scale
        :type y: int
        :param tilted: The time the stick should remain tilted
        for, defaults to 0.1
        :type tilted: float, optional
        :param released: The time the stick should remain
        released for, defaults to 0.1
        :type released: float, optional
        :type block: bool, optional
        :return: The generated ID of the passed macro. This ID
        will show up under the "finished_macros" list communicated
        in the controllers shared state.
        :rtype: str
        """

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

        macro_id = self.macro(controller_index, macro, block=block)

        return macro_id

    def stop_macro(self, controller_index, macro_id, block=True):
        """Used to stop a given macro by its macro ID. After
        the macro has been stopped, its macro ID will show up
        as a finished macro in the respective controllers
        "finished_macros" list communicated in its state.

        :param controller_index: The index of a given controller
        :type controller_index: int
        :param macro_id: The ID of a given macro (queued or running)
        :type macro_id: str
        :param block: A boolean variable indicating whether or not
        to block until the macro is stopped, defaults to True
        :type block: bool, optional
        :raises ValueError: If the controller_index does not exist
        """

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
        """Clears all running and queued macros on a specified
        controller.

        :param controller_index: The index of a given controller
        :type controller_index: int
        :raises ValueError: If the controller_index does not exist
        """

        if controller_index not in self.manager_state.keys():
            raise ValueError("Specified controller does not exist")

        self.task_queue.put({
            "command": NxbtCommands.CLEAR_MACROS,
            "arguments": {
                "controller_index": controller_index,
            }
        })

    def clear_all_macros(self):
        """Clears all running and queued macros on all
        controllers.
        """

        for controller in self.manager_state.keys():
            self.clear_macros(controller)

    def create_controller(self, controller_type, adapter_path=None,
                          colour_body=None, colour_buttons=None,
                          reconnect_address=None):
        """Used to create a Nintendo Switch controller of a
        given type and colour on an (optionally) specified
        bluetooth adapter.

        If no Bluetooth adapter is specified, the first available
        adapter is used.

        If the reconnect_address is specified, the controller
        will attempt to reconnect to the Switch, rather than
        simply letting any Switch connect to it. To ensure
        that the reconnect succeeds, the Switch must be on
        and *not* on the Change Grip/Order menu.

        :param controller_type: The type of controller to create
        :type controller_type: ControllerTypes
        :param adapter_path: The DBus path to a given Bluetooth
        adapter, defaults to None
        :type adapter_path: str, optional
        :param colour_body: The body colour of the controller
        represented by a hexadecimal colour value (a list of
        three ints (0-255)), defaults to None
        :type colour_body: list, optional
        :param colour_buttons: The button colour of the controller
        represented by a hexadecimal colour value (a list of
        three ints (0-255)), defaults to None
        :type colour_buttons: list, optional
        :param reconnect_address: A previously connected to
        Switch's Bluetooth MAC address, defaults to None
        :type reconnect_address: str or list, optional
        :raises ValueError: If specified adapter is unavailable
        :raises ValueError: If specified adapter is in use
        :return: The index of the created controller
        :rtype: int
        """
        if adapter_path:
            if adapter_path not in self.get_available_adapters():
                raise ValueError("Specified adapter is unavailable")

            if adapter_path in self.__adapters_in_use__.keys():
                raise ValueError("Specified adapter in use")
        else:
            # Get all adapters we can use
            usable_adapters = list(
                set(self.get_available_adapters()) - set(self.__adapters_in_use__))
            if len(usable_adapters) > 0:
                # Use the first available adapter
                adapter_path = usable_adapters[0]
            else:
                raise ValueError("No adapters available")

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
                                state["state"] == "reconnecting" or
                                state["state"] == "crashed"):
                            break
        finally:
            self.__controller_lock__.release()

        return controller_index

    def remove_controller(self, controller_index):
        """Terminates and removes a given controller.

        :param controller_index: The index of a given controller
        :type controller_index: int
        :raises ValueError: If controller does not exist
        """

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
        """Blocks until a given controller is connected
        to a Nintendo Switch.

        :param controller_index: The index of a given controller
        :type controller_index: int
        """

        while not self.state[controller_index]["state"] == "connected":
            if self.state[controller_index]["state"] == "crashed":
                raise OSError("The watched controller has crashe with error",
                              self.state[controller_index]["errors"])
            pass

    def get_available_adapters(self):
        """Gets the DBus paths of all available Bluetooth
        adapters.

        :return: A list of available adapter paths
        :rtype: list
        """

        bus = dbus.SystemBus()
        adapters = find_objects(bus, SERVICE_NAME, ADAPTER_INTERFACE)

        return adapters

    def get_switch_addresses(self):
        """Gets the Bluetooth MAC addresses of all
        previously connected Nintendo Switchs

        :return: A list of Bluetooth MAC addresses
        :rtype: list
        """

        return (find_devices_by_alias("Nintendo Switch"))

    @property
    def state(self):
        """The state of all created and running controllers.
        This state is read-only and is represented as a dict.
        The state dict's structure follows:

        {
            "controller_index"
                {
                    "state":
                        "initializing" or
                        "connecting" or
                        "reconnecting" or
                        "crashed"
                    "finished_macros":
                        A list of UUIDs
                    "errors":
                        A string with the crash error
                }
        }

        :return: The state dict
        :rtype: dict
        """

        return self.manager_state


class __ControllerManager__():
    """Used as the manager for all controllers. Each controller is
    a daemon multiprocessing Process that the ControllerManager
    object creates and manages.

    The ControllerManager object submits messages to the respective
    queues of each controller process for tasks such as macro submission
    or macro clearing/stopping.
    """

    def __init__(self, state, lock):

        self.state = state
        self.lock = lock
        self.controller_resources = Manager()
        self.__controller_queues__ = {}
        self.__children__ = {}

    def create_controller(self, index, controller_type, adapter_path,
                          colour_body=None, colour_buttons=None,
                          reconnect_address=None):
        """Instantiates a given controller as a multiprocessing
        Process with a shared state dict and a task queue.

        Configuration options are available in the form of
        controller colours.

        :param index: The index of the controller
        :type index: int
        :param controller_type: The type of Nintendo Switch controller
        :type controller_type: ControllerTypes
        :param adapter_path: The DBus path to the Bluetooth adapter
        :type adapter_path: str
        :param colour_body: A list of three ints representing the hex
        colour of the controller, defaults to None
        :type colour_body: list, optional
        :param colour_buttons: A list of three ints representing the
        hex colour of the controller, defaults to None
        :type colour_buttons: list, optional
        :param reconnect_address: The address of a Nintendo Switch
        to reconnect to, defaults to None
        :type reconnect_address: str, optional
        """

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
