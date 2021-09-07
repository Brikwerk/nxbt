import os
import time
import psutil
from collections import deque
import multiprocessing

from blessed import Terminal

from .nxbt import Nxbt, PRO_CONTROLLER


class LoadingSpinner():

    SPINNER_CHARS = ['■ □ □ □', '□ ■ □ □', '□ □ ■ □', '□ □ □ ■', '□ □ □ ■', '□ □ ■ □', '□ ■ □ □', '■ □ □ □']  # noqa

    def __init__(self):

        self.creation_time = time.perf_counter()
        self.last_update_time = self.creation_time
        self.current_char_index = 0

    def get_spinner_char(self):

        current_time = time.perf_counter()
        delta = current_time - self.last_update_time

        if delta > 0.07:
            self.last_update_time = current_time

            if self.current_char_index == 7:
                self.current_char_index = 0
            else:
                self.current_char_index += 1

        return self.SPINNER_CHARS[self.current_char_index]


class ControllerTUI():

    CONTROLS = {
        "ZL": "◿□□□□",
        "L": "◿□□□□",
        "ZR": "□□□□◺",
        "R": "□□□□◺",
        "LS_UP": ".─.",
        "LS_LEFT": "(",
        "LS_RIGHT": ")",
        "LS_DOWN": "`─'",
        "RS_UP": ".─.",
        "RS_LEFT": "(",
        "RS_RIGHT": ")",
        "RS_DOWN": "`─'",
        "DPAD_UP": "△",
        "DPAD_LEFT": "◁",
        "DPAD_RIGHT": "▷",
        "DPAD_DOWN": "▽",
        "MINUS": "◎",
        "PLUS": "◎",
        "HOME": "□",
        "CAPTURE": "□",
        "A": "○",
        "B": "○",
        "X": "○",
        "Y": "○",
    }

    def __init__(self, term):

        self.term = term
        # Save a copy of the controls we can restore the
        # control text on deactivation
        self.DEFAULT_CONTROLS = self.CONTROLS.copy()

        self.CONTROL_RELEASE_TIMERS = self.CONTROLS.copy()
        for control in self.CONTROL_RELEASE_TIMERS.keys():
            self.CONTROL_RELEASE_TIMERS[control] = False

        self.auto_keypress_deactivation = True
        self.remote_connection = False

    def toggle_auto_keypress_deactivation(self, toggle):
        """Toggles whether or not the ControllerTUI should deactivate
        a control after a period of time.

        :param toggle: A True/False value that toggles auto keypress
        deactivation
        :type toggle: bool
        """

        self.auto_keypress_deactivation = toggle

    def set_remote_connection_status(self, status):
        """Sets whether or not the controller should render
        with remote connection specific controls.

        :param status: The status of the remote connection
        :type status: bool
        """

        self.remote_connection = status

    def activate_control(self, key, activated_text=None):

        if activated_text:
            self.CONTROLS[key] = activated_text
        else:
            self.CONTROLS[key] = self.term.bold_black_on_white(self.CONTROLS[key])

        # Keep track of when the key was pressed so we can release later
        if self.auto_keypress_deactivation:
            self.CONTROL_RELEASE_TIMERS[key] = time.perf_counter()

    def deactivate_control(self, key):

        self.CONTROLS[key] = self.DEFAULT_CONTROLS[key]

    def render_controller(self):

        if self.auto_keypress_deactivation:
            # Release any overdue timers
            for control in self.CONTROL_RELEASE_TIMERS.keys():
                pressed_time = self.CONTROL_RELEASE_TIMERS[control]
                current_time = time.perf_counter()
                if pressed_time is not False and current_time - pressed_time > 0.25:
                    self.deactivate_control(control)

        ZL = self.CONTROLS['ZL']
        L = self.CONTROLS['L']
        ZR = self.CONTROLS['ZR']
        R = self.CONTROLS['R']
        LU = self.CONTROLS['LS_UP']
        LL = self.CONTROLS['LS_LEFT']
        LR = self.CONTROLS['LS_RIGHT']
        LD = self.CONTROLS['LS_DOWN']
        RU = self.CONTROLS['RS_UP']
        RL = self.CONTROLS['RS_LEFT']
        RR = self.CONTROLS['RS_RIGHT']
        RD = self.CONTROLS['RS_DOWN']
        DU = self.CONTROLS['DPAD_UP']
        DL = self.CONTROLS['DPAD_LEFT']
        DR = self.CONTROLS['DPAD_RIGHT']
        DD = self.CONTROLS['DPAD_DOWN']
        MN = self.CONTROLS['MINUS']
        PL = self.CONTROLS['PLUS']
        HM = self.CONTROLS['HOME']
        CP = self.CONTROLS['CAPTURE']
        A = self.CONTROLS['A']
        B = self.CONTROLS['B']
        X = self.CONTROLS['X']
        Y = self.CONTROLS['Y']

        if self.remote_connection:
            lr_press = "L + R - - - - - - - - -▷ E"
        else:
            lr_press = "                          "

        print(self.term.home + self.term.move_y((self.term.height // 2) - 9))
        print(self.term.center(f"      {ZL}        {ZR}                                    "))
        print(self.term.center(f"    ─{L}──────────{R}─      ┌─────────────┬────────────┐"))
        print(self.term.center("  ╱                        ╲    │  Controls   │    Keys    │"))
        print(self.term.center(f" ╱   {LU}   {MN}       {PL}   {X}    ╲   └─────────────┴────────────┘"))  # noqa
        print(self.term.center(f"│   {LL}   {LR}    {CP}   {HM}   {Y}   {A}   │   Left Stick ─ ─ ─ ▷ W/A/S/D "))  # noqa
        print(self.term.center(f"│    {LD}               {B}     │   DPad ─ ─ ─ ─ ─ ─ ▷ G/V/B/N "))
        print(self.term.center(f"│        {DU}         {RU}       │   Capture/Home ─ ─ ─ ─ ▷ [/] "))
        print(self.term.center(f"│╲     {DL} □ {DR}      {RL}   {RR}     ╱│   +/- ─ ─ ─ ─ ─ ─ ─ ─ ─▷ 6/7 "))  # noqa
        print(self.term.center(f"│░░╲     {DD}         {RD}    ╱░░│   X/Y/B/A ─ ─ ─ ─ ─▷ J/I/K/L "))
        print(self.term.center("│░░░░╲ ──────────────── ╱░░░░│   L/ZL ─ ─ ─ ─ ─ ─ ─ ─ ▷ 1/2 "))
        print(self.term.center("│░░░░╱                  ╲░░░░│   R/ZR ─ ─ ─ ─ ─ ─ ─ ─ ▷ 8/9 "))
        print(self.term.center("│░░╱                      ╲░░│   Right Stick - - - ▷ Arrows "))
        print(self.term.center(f"│╱                          ╲│   {lr_press} "))


class InputTUI():

    KEYMAP = {
        # Left Stick Mapping
        "w": {
            "control": "LS_UP",
            "stick_data": {
                "stick_name": "L_STICK",
                "x": "+000",
                "y": "+100"
            }
        },
        "a": {
            "control": "LS_LEFT",
            "stick_data": {
                "stick_name": "L_STICK",
                "x": "-100",
                "y": "+000"
            }
        },
        "d": {
            "control": "LS_RIGHT",
            "stick_data": {
                "stick_name": "L_STICK",
                "x": "+100",
                "y": "+000"
            }
        },
        "s": {
            "control": "LS_DOWN",
            "stick_data": {
                "stick_name": "L_STICK",
                "x": "+000",
                "y": "-100"
            }
        },

        # Right Stick Mapping
        "KEY_UP": {
            "control": "RS_UP",
            "stick_data": {
                "stick_name": "R_STICK",
                "x": "+000",
                "y": "+100"
            }
        },
        "KEY_LEFT": {
            "control": "RS_LEFT",
            "stick_data": {
                "stick_name": "R_STICK",
                "x": "-100",
                "y": "+000"
            }
        },
        "KEY_RIGHT": {
            "control": "RS_RIGHT",
            "stick_data": {
                "stick_name": "R_STICK",
                "x": "+100",
                "y": "+000"
            }
        },
        "KEY_DOWN": {
            "control": "RS_DOWN",
            "stick_data": {
                "stick_name": "R_STICK",
                "x": "+000",
                "y": "-100"
            }
        },

        # Dpad Mapping
        "g": "DPAD_UP",
        "v": "DPAD_LEFT",
        "n": "DPAD_RIGHT",
        "b": "DPAD_DOWN",

        # Button Mapping
        "6": "MINUS",
        "7": "PLUS",
        "[": "CAPTURE",
        "]": "HOME",
        "i": "X",
        "j": "Y",
        "l": "A",
        "k": "B",

        # Triggers
        "1": "L",
        "2": "ZL",
        "8": "R",
        "9": "ZR",
    }

    def __init__(self, reconnect_target=None, debug=False, logfile=False, force_remote=False):

        self.reconnect_target = reconnect_target
        self.term = Terminal()
        if force_remote:
            self.remote_connection = True
        else:
            self.remote_connection = self.detect_remote_connection()
        self.controller = ControllerTUI(self.term)

        # Check if direct connection will fail
        if not self.remote_connection:
            try:
                from pynput import keyboard
            except ImportError as e:
                print("Unable to import pynput for direct input.")
                print("If you're accessing NXBT over a remote shell, ", end="")
                print("please use the 'remote_tui' option instead of 'tui'.")
                print("The original pynput import is displayed below:\n")
                print(e)
                exit(1)

        self.debug = debug
        self.logfile = logfile

    def detect_remote_connection(self):
        """Traverse up the parent processes and check if any
        have their parent as a remote daemon. If so, the python
        script is running under a remote connection.

        Remote shell detection is required for this TUI, due to
        keyboard input limitations on most remote connections.
        Specifically, no "keyup" events are sent when a key is
        released. Keyup events are required for proper input to
        the Switch, thus, we need to detect if the shell is a remote
        session and workaround this.

        :return: Returns a boolean value indicating whether or not
        the current script is running as SSH
        :rtype: bool
        """

        remote_connection = False
        remote_process_names = ['sshd', 'mosh-server']
        ppid = os.getppid()
        while ppid > 0:
            process = psutil.Process(ppid)
            if process.name() in remote_process_names:
                remote_connection = True
                break
            ppid = process.ppid()

        return remote_connection

    def start(self):

        self.mainloop(self.term)

    def mainloop(self, term):

        # Initializing a controller
        if not self.debug:
            self.nx = Nxbt(disable_logging=True)
        else:
            self.nx = Nxbt(debug=self.debug, logfile=self.logfile)
        self.controller_index = self.nx.create_controller(
            PRO_CONTROLLER,
            reconnect_address=self.reconnect_target)

        state = None
        spinner = LoadingSpinner()
        errors = None
        try:
            with term.cbreak(), term.keypad(), term.location(), term.hidden_cursor():
                print(term.home + term.clear)
                self.render_top_bar(term)
                self.render_bottom_bar(term)
                self.render_start_screen(term, "Loading")
                inp = term.inkey(timeout=0)

                # Loading Screen
                while inp != chr(113):  # Checking for q press
                    # Check key at 15hz
                    inp = term.inkey(timeout=1/30)
                    new_state = self.nx.state[self.controller_index]["state"]

                    if new_state != state:
                        state = new_state

                        loading_text = "Loading"
                        if state == "initializing":
                            loading_text = "Initializing Controller"
                        elif state == "connecting":
                            loading_text = "Connecting to any Nintendo Switch"
                        elif state == "reconnecting":
                            loading_text = "Reconnecting to Nintendo Switch"
                        elif state == "connected":
                            loading_text = "Connected!"
                        elif state == "crashed":
                            errors = self.nx.state[self.controller_index]["errors"]
                            exit(1)
                        self.render_start_screen(term, loading_text)

                    print(term.move_y((term.height // 2) + 6))
                    if state != "connected":
                        print(term.bold(term.center(spinner.get_spinner_char())))
                    else:
                        print(term.center(""))

                    if state == "connected":
                        time.sleep(1)
                        break

                # Main Gamepad Input Loop
                if state == "connected":
                    if self.remote_connection:
                        self.remote_input_loop(term)
                    else:
                        self.direct_input_loop(term)

        except KeyboardInterrupt:
            pass
        finally:
            print(term.clear())
            if errors:
                print("The TUI encountered the following errors:")
                print(errors)

    def remote_input_loop(self, term):

        self.controller.set_remote_connection_status(True)

        inp = term.inkey(timeout=0)
        while inp != chr(113):  # Checking for q press
            # Cutoff large buffered input from the deque
            # so that we avoid spamming the Switch after
            # a key releases from being held.
            # Increasing the size of the buffer does not
            # smooth out the jagginess of input.
            if len(term._keyboard_buf) > 1:
                term._keyboard_buf = deque([term._keyboard_buf.pop()])

            inp = term.inkey(1/66)

            pressed_key = None
            if inp.is_sequence:
                pressed_key = inp.name
            elif inp:
                pressed_key = inp

            if pressed_key == 'e':
                self.controller.activate_control('L')
                self.controller.activate_control('R')
                self.nx.macro(self.controller_index, "L R 0.1s")
            else:
                try:
                    control_data = self.KEYMAP[pressed_key]
                    if type(control_data) == dict and "stick_data" in control_data.keys():
                        x_value = control_data['stick_data']['x']
                        y_value = control_data['stick_data']['y']
                        stick_name = control_data['stick_data']['stick_name']

                        self.controller.activate_control(control_data["control"])
                        self.nx.macro(
                            self.controller_index,
                            f"{stick_name}@{x_value}{y_value} 0.1s")
                    else:
                        self.controller.activate_control(control_data)
                        self.nx.macro(self.controller_index, f"{control_data} 0.05s")
                except KeyError:
                    pass

            self.controller.render_controller()

            self.check_for_disconnect(term)

    def direct_input_loop(self, term):
        from pynput import keyboard

        self.controller.toggle_auto_keypress_deactivation(False)
        self.exit_tui = False
        self.capture_input = True

        # Create a packet that is accessible from a multiprocessing Process
        # and from within threads
        packet_manager = multiprocessing.Manager()
        input_packet = packet_manager.dict()
        input_packet["packet"] = self.nx.create_input_packet()

        print(term.move_y(term.height - 5))
        print(term.center(term.bold_black_on_white(" <Press esc to toggle input capture> ")))

        def on_press(key):

            # Parse the key press event
            pressed_key = None
            try:
                pressed_key = key.char
            except AttributeError:
                pressed_key = str(key).replace(".", "_").upper()

            if not self.capture_input:  # If we're not capturing input, pass
                pass
            else:
                try:
                    control_data = self.KEYMAP[pressed_key]
                    packet = input_packet["packet"]
                    if type(control_data) == dict and "stick_data" in control_data.keys():
                        stick_name = control_data['stick_data']['stick_name']
                        self.controller.activate_control(control_data["control"])
                        packet[stick_name][control_data["control"]] = True
                    else:
                        self.controller.activate_control(control_data)
                        packet[control_data] = True
                    input_packet["packet"] = packet
                except KeyError:
                    pass

        def on_release(key):

            # Parse the key release event
            released_key = None
            try:
                released_key = key.char
            except AttributeError:
                released_key = str(key).replace(".", "_").upper()

            # If the esc key is released, toggle input capturing
            if released_key == "KEY_ESC":
                self.capture_input = not self.capture_input

            # Exit on q key press
            if released_key == 'q':
                self.exit_tui = True
                return False

            if not self.capture_input:  # If we're not capturing input, pass
                pass
            else:
                try:
                    control_data = self.KEYMAP[released_key]
                    packet = input_packet["packet"]
                    if type(control_data) == dict and "stick_data" in control_data.keys():
                        stick_name = control_data['stick_data']['stick_name']
                        self.controller.deactivate_control(control_data["control"])
                        packet[stick_name][control_data["control"]] = False
                    else:
                        self.controller.deactivate_control(control_data)
                        packet[control_data] = False
                    input_packet["packet"] = packet
                except KeyError:
                    pass

        def input_worker(nxbt, controller_index, input_packet):

            while True:
                packet = input_packet["packet"]

                # Calculating left x/y stick values
                ls_x_value = 0
                ls_y_value = 0
                if packet["L_STICK"]["LS_LEFT"]:
                    ls_x_value -= 100
                if packet["L_STICK"]["LS_RIGHT"]:
                    ls_x_value += 100
                if packet["L_STICK"]["LS_UP"]:
                    ls_y_value += 100
                if packet["L_STICK"]["LS_DOWN"]:
                    ls_y_value -= 100
                packet["L_STICK"]["X_VALUE"] = ls_x_value
                packet["L_STICK"]["Y_VALUE"] = ls_y_value

                # Calculating right x/y stick values
                rs_x_value = 0
                rs_y_value = 0
                if packet["R_STICK"]["RS_LEFT"]:
                    rs_x_value -= 100
                if packet["R_STICK"]["RS_RIGHT"]:
                    rs_x_value += 100
                if packet["R_STICK"]["RS_UP"]:
                    rs_y_value += 100
                if packet["R_STICK"]["RS_DOWN"]:
                    rs_y_value -= 100
                packet["R_STICK"]["X_VALUE"] = rs_x_value
                packet["R_STICK"]["Y_VALUE"] = rs_y_value

                nxbt.set_controller_input(controller_index, packet)
                time.sleep(1/120)

        input_process = multiprocessing.Process(
            target=input_worker, args=(self.nx, self.controller_index, input_packet))
        input_process.start()

        # Start a non-blocking keyboard event listener
        listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release)
        listener.start()

        # Main TUI Loop
        while True:
            if self.exit_tui:
                packet_manager.shutdown()
                input_process.terminate()
                break
            if not self.capture_input:
                print(term.home + term.move_y((term.height // 2) - 4))
                print(term.bold_black_on_white(term.center("")))
                print(term.bold_black_on_white(term.center(
                    "<Input Paused. Press ESC Again to Begin Capturing Input>"
                )))
                print(term.bold_black_on_white(term.center("")))
            else:
                self.controller.render_controller()
            self.check_for_disconnect(term)
            time.sleep(1/120)

    def render_start_screen(self, term, loading_text):

        print(term.home + term.move_y((term.height // 2) - 8))
        print(term.center("___╲╱___"))
        print(term.center("│╲  ╱╲  ╱│"))
        print(term.center("│ ╲╱__╲╱ │"))
        print(term.center("│╱      ╲│"))
        print(term.center("┌──────────────────┐"))
        print(term.center("│     NXBT TUI     │"))
        print(term.center("└──────────────────┘"))
        print(term.center(""))
        print(term.black_on_white(term.center("")))
        print(term.bold_black_on_white(term.center(loading_text)))
        print(term.black_on_white(term.center("")))

    def render_top_bar(self, term):

        print(term.move_y(1))
        if self.remote_connection:
            print(term.bold_black_on_white(term.center(term.bold_black_on_red("  REMOTE MODE  "))))
            warning = " WARNING: MACROS WILL BE USED ON KEYPRESS DUE TO REMOTE CLI LIMITATIONS "
            print(term.center(term.black_on_red(warning)))
        else:
            print(term.bold_black_on_white(term.center("DIRECT INPUT MODE")))
        print(term.move_y(1))
        print(term.white_on_black(" NXBT TUI 🎮 "))

    def render_bottom_bar(self, term):

        print(term.move_y(term.height))
        print(term.center(term.bold_black_on_white(" <Press q to quit> ")))

    def check_for_disconnect(self, term):

        state = self.nx.state[self.controller_index]["state"]
        if state != 'connected':
            print(term.home + term.move_y((term.height // 2) - 4))
            print(term.bold_black_on_red(term.center("")))
            print(term.bold_black_on_red(term.center(state.title())))
            print(term.bold_black_on_red(term.center("")))

            if state == 'crashed':
                time.sleep(3)
                term.clear()
                errors = self.nx.state[self.controller_index]["errors"]
                raise ConnectionError(errors)

            while True:
                inp = term.inkey(1/30)
                if inp == chr(113):
                    exit(1)
                elif self.nx.state[self.controller_index]["state"] == 'connected':
                    break


def main():
    """Program entry point."""
    tui = InputTUI()
    tui.start()


if __name__ == '__main__':
    main()
