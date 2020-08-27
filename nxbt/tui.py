import os
import time
import psutil
from collections import deque

from blessed import Terminal

from .nxbt import Nxbt, PRO_CONTROLLER


class LoadingSpinner():

    SPINNER_CHARS = ['⢸', '⣰', '⣤', '⣆', '⡇', '⠏', '⠛', '⠹']

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
        "DP_UP": "△",
        "DP_LEFT": "◁",
        "DP_RIGHT": "▷",
        "DP_DOWN": "▽",
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

    def activate_control(self, key, activated_text=None):

        if activated_text:
            self.CONTROLS[key] = activated_text
        else:
            self.CONTROLS[key] = self.term.bold_black_on_white(self.CONTROLS[key])

        # Keep track of when the key was pressed so we can release later
        self.CONTROL_RELEASE_TIMERS[key] = time.perf_counter()

    def deactivate_control(self, key):

        self.CONTROLS[key] = self.DEFAULT_CONTROLS[key]

    def render_controller(self):

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
        DU = self.CONTROLS['DP_UP']
        DL = self.CONTROLS['DP_LEFT']
        DR = self.CONTROLS['DP_RIGHT']
        DD = self.CONTROLS['DP_DOWN']
        MN = self.CONTROLS['MINUS']
        PL = self.CONTROLS['PLUS']
        HM = self.CONTROLS['HOME']
        CP = self.CONTROLS['CAPTURE']
        A = self.CONTROLS['A']
        B = self.CONTROLS['B']
        X = self.CONTROLS['X']
        Y = self.CONTROLS['Y']

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
        print(self.term.center("│╱                          ╲│                              "))


class InputTUI():

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
        "DP_UP": "△",
        "DP_LEFT": "◁",
        "DP_RIGHT": "▷",
        "DP_DOWN": "▽",
        "MINUS": "◎",
        "PLUS": "◎",
        "HOME": "□",
        "CAPTURE": "□",
        "A": "○",
        "B": "○",
        "X": "○",
        "Y": "○",
    }

    def __init__(self, reconnect_target=None):

        self.reconnect_target = reconnect_target
        self.term = Terminal()
        self.remote_connection = self.detect_remote_connection()
        self.controller = ControllerTUI(self.term)

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
        self.nx = Nxbt(disable_logging=True)
        self.controller_index = self.nx.create_controller(
            PRO_CONTROLLER,
            reconnect_address=self.reconnect_target)

        state = None
        spinner = LoadingSpinner()
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
                    inp = term.inkey(timeout=1/15)
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

    def remote_input_loop(self, term):

        inp = term.inkey(timeout=0)
        while inp != chr(113):  # Checking for q press
            # Cutoff large buffered input from the deque
            # so that we avoid spamming the Switch after
            # a key releases from being held.
            # Increasing the size of the buffer does not
            # smooth out the jagginess of input.
            if len(term._keyboard_buf) > 1:
                term._keyboard_buf = deque([term._keyboard_buf.pop()])

            inp = term.inkey(1/60)

            pressed_key = None
            if inp.is_sequence:
                pressed_key = inp.name
            elif inp:
                pressed_key = inp

            if pressed_key == 'w':
                self.controller.activate_control('LS_UP')
                self.nx.macro(self.controller_index, "L_STICK@+000+100 0.1s")
            elif pressed_key == 'a':
                self.controller.activate_control('LS_LEFT')
                self.nx.macro(self.controller_index, "L_STICK@-100+000 0.1s")
            elif pressed_key == 'd':
                self.controller.activate_control('LS_RIGHT')
                self.nx.macro(self.controller_index, "L_STICK@+100+000 0.1s")
            elif pressed_key == 's':
                self.controller.activate_control('LS_DOWN')
                self.nx.macro(self.controller_index, "L_STICK@+000-100 0.1s")

            elif pressed_key == 'g':
                self.controller.activate_control('DP_UP')
                self.nx.macro(self.controller_index, "DPAD_UP 0.1s")
            elif pressed_key == 'v':
                self.controller.activate_control('DP_LEFT')
                self.nx.macro(self.controller_index, "DPAD_LEFT 0.1s")
            elif pressed_key == 'n':
                self.controller.activate_control('DP_RIGHT')
                self.nx.macro(self.controller_index, "DPAD_RIGHT 0.1s")
            elif pressed_key == 'b':
                self.controller.activate_control('DP_DOWN')
                self.nx.macro(self.controller_index, "DPAD_DOWN 0.1s")

            elif pressed_key == '[':
                self.controller.activate_control('CAPTURE')
                self.nx.macro(self.controller_index, "CAPTURE 0.1s")
            elif pressed_key == ']':
                self.controller.activate_control('HOME')
                self.nx.macro(self.controller_index, "HOME 0.1s")

            elif pressed_key == '6':
                self.controller.activate_control('MINUS')
                self.nx.macro(self.controller_index, "- 0.1s")
            elif pressed_key == '7':
                self.controller.activate_control('PLUS')
                self.nx.macro(self.controller_index, "+ 0.1s")

            elif pressed_key == 'i':
                self.controller.activate_control('X')
                self.nx.macro(self.controller_index, "X 0.1s")
            elif pressed_key == 'j':
                self.controller.activate_control('Y')
                self.nx.macro(self.controller_index, "Y 0.1s")
            elif pressed_key == 'l':
                self.controller.activate_control('A')
                self.nx.macro(self.controller_index, "A 0.1s")
            elif pressed_key == 'k':
                self.controller.activate_control('B')
                self.nx.macro(self.controller_index, "B 0.1s")

            elif pressed_key == '1':
                self.controller.activate_control('L')
                self.nx.macro(self.controller_index, "L 0.1s")
            elif pressed_key == '2':
                self.controller.activate_control('ZL')
                self.nx.macro(self.controller_index, "ZL 0.1s")

            elif pressed_key == '8':
                self.controller.activate_control('R')
                self.nx.macro(self.controller_index, "R 0.1s")
            elif pressed_key == '9':
                self.controller.activate_control('ZR')
                self.nx.macro(self.controller_index, "ZR 0.1s")

            elif pressed_key == 'KEY_UP':
                self.controller.activate_control('RS_UP')
                self.nx.macro(self.controller_index, "L_STICK@+000+100 0.1s")
            elif pressed_key == 'KEY_LEFT':
                self.controller.activate_control('RS_LEFT')
                self.nx.macro(self.controller_index, "L_STICK@-100+000 0.1s")
            elif pressed_key == 'KEY_RIGHT':
                self.controller.activate_control('RS_RIGHT')
                self.nx.macro(self.controller_index, "L_STICK@+100+000 0.1s")
            elif pressed_key == 'KEY_DOWN':
                self.controller.activate_control('RS_DOWN')
                self.nx.macro(self.controller_index, "L_STICK@+000-100 0.1s")

            self.controller.render_controller()

            self.check_for_disconnect(term)

    def direct_input_loop(self, term):

        pass

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
            self.nx.wait_for_connection(self.controller_index)


def main():
    """Program entry point."""
    tui = InputTUI()
    tui.start()


if __name__ == '__main__':
    main()
