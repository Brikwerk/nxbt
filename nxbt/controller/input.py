from time import perf_counter


class InputParser():

    def __init__(self, protocol):

        self.protocol = protocol

        # Buffers a list of unparsed macros
        self.macro_buffer = []
        # Keeps track of the entire current
        # list of macro commands.
        self.current_macro = None
        self.current_macro_id = None
        # Keeps track of the macro commands being
        # input over a period of time.
        self.current_macro_commands = None
        # The time length of the current macro
        self.macro_timer_length = 0
        # The start time for the current macro commands
        self.macro_timer_start = 0

        self.controller_input = None

    def buffer_macro(self, macro, macro_id):

        # Doesn't have any info
        if len(macro) < 4:
            return

        self.macro_buffer.append([macro, macro_id])

    def set_controller_input(self, controller_input):

        self.controller_input = controller_input

    def set_protocol_input(self, state=None):

        if self.controller_input:
            self.parse_controller_input(self.controller_input)
            self.controller_input = None

        elif (self.macro_buffer or self.current_macro or
              self.current_macro_commands):
            # Check if we can start on a new macro.
            if not self.current_macro and self.macro_buffer:
                # Preprocess command lines of current macro
                macro = self.macro_buffer.pop(0)
                self.current_macro = macro[0].strip("\n")
                self.current_macro = self.current_macro.split("\n")
                self.current_macro_id = macro[1]

            # Check if we can load the next set of commands
            if not self.current_macro_commands and self.current_macro:
                self.current_macro_commands = (
                    self.current_macro.pop(0).strip(" ").split(" "))

                # Timing metadata extraction
                timer_length = self.current_macro_commands[-1]
                timer_length = timer_length[0:len(timer_length)-1]
                self.macro_timer_length = float(timer_length)
                self.macro_timer_start = perf_counter()

            self.parse_macro_input(self.current_macro_commands)

            # Check if we're done inputting the current command
            time_delta = perf_counter() - self.macro_timer_start
            if time_delta > self.macro_timer_length:
                self.current_macro_commands = None
                # Check if we're done the current macro
                if not self.current_macro and state:
                    finished = state["finished_macros"]
                    finished.append(self.current_macro_id)
                    state["finished_macros"] = finished

    def parse_controller_input(self, controller_input):

        return controller_input

    def parse_macro_input(self, macro_input):

        # Checking if this is a wait macro command
        if len(macro_input) < 2:
            return

        # Arrays representing the 3 button bytes in the
        # standard input report as binary.
        upper = ['0'] * 8
        shared = ['0'] * 8
        lower = ['0'] * 8
        for i in range(0, len(macro_input)-1):
            button = macro_input[i]
            # Upper Byte
            if button == "Y":
                upper[7] = '1'
            elif button == "X":
                upper[6] = '1'
            elif button == "B":
                upper[5] = '1'
            elif button == "A":
                upper[4] = '1'
            elif button == "SR":
                upper[3] = '1'
            elif button == "SL":
                upper[2] = '1'
            elif button == "R":
                upper[1] = '1'
            elif button == "ZR":
                upper[0] = '1'

            # Shared byte
            elif button == "-":
                shared[7] = '1'
            elif button == "+":
                shared[6] = '1'
            elif button == "R_ANALOG_DOWN":
                shared[5] = '1'
            elif button == "L_ANALOG_DOWN":
                shared[4] = '1'
            elif button == "HOME":
                shared[3] = '1'
            elif button == "CAPTURE":
                shared[2] = '1'

            # Lower byte
            elif button == "DPAD_DOWN":
                lower[7] = '1'
            elif button == "DPAD_UP":
                lower[6] = '1'
            elif button == "DPAD_RIGHT":
                lower[5] = '1'
            elif button == "DPAD_LEFT":
                lower[4] = '1'
            elif button == "SR":
                lower[3] = '1'
            elif button == "SL":
                lower[2] = '1'
            elif button == "L":
                lower[1] = '1'
            elif button == "ZL":
                lower[0] = '1'

        # Converting binary strings to ints
        upper_byte = int("".join(upper), 2)
        shared_byte = int("".join(shared), 2)
        lower_byte = int("".join(lower), 2)

        self.protocol.set_button_inputs(upper_byte, shared_byte, lower_byte)
