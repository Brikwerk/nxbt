from time import perf_counter
from json import dumps


DIRECT_INPUT_IDLE_PACKET = {
    # Sticks
    "L_STICK": {
        "PRESSED": False,
        "X_VALUE": 0,
        "Y_VALUE": 0,
        # Keyboard position calculation values
        "LS_UP": False,
        "LS_LEFT": False,
        "LS_RIGHT": False,
        "LS_DOWN": False
    },
    "R_STICK": {
        "PRESSED": False,
        "X_VALUE": 0,
        "Y_VALUE": 0,
        # Keyboard position calculation values
        "RS_UP": False,
        "RS_LEFT": False,
        "RS_RIGHT": False,
        "RS_DOWN": False
    },
    # Dpad
    "DPAD_UP": False,
    "DPAD_LEFT": False,
    "DPAD_RIGHT": False,
    "DPAD_DOWN": False,
    # Triggers
    "L": False,
    "ZL": False,
    "R": False,
    "ZR": False,
    # Joy-Con Specific Buttons
    "JCL_SR": False,
    "JCL_SL": False,
    "JCR_SR": False,
    "JCR_SL": False,
    # Meta buttons
    "PLUS": False,
    "MINUS": False,
    "HOME": False,
    "CAPTURE": False,
    # Buttons
    "Y": False,
    "X": False,
    "B": False,
    "A": False
}


class InputParser():

    # Left Stick calibration values
    LEFT_STICK_CALIBRATION = {
        "center_x": 2159,
        "center_y": 1916,
        # Zeroed Min/Max X and Y
        "min_x": -1466,
        "max_x": 1517,
        "min_y": -1583,
        "max_y": 1465,
    }
    # Right Stick calibration values
    RIGHT_STICK_CALIBRATION = {
        "center_x": 2070,
        "center_y": 2013,
        # Zeroed Min/Max X and Y
        "min_x": -1522,
        "max_x": 1414,
        "min_y": -1531,
        "max_y": 1510,
    }

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

        # Whether or not input has been entered
        # that would close the "Change Grip/Order" menu
        self.exited_grip_order_menu = False

    def buffer_macro(self, macro, macro_id):

        # Doesn't have any info
        if len(macro) < 4:
            return

        self.macro_buffer.append([macro, macro_id])

    def stop_macro(self, macro_id, state=None):

        # Check if the macro is being input currently
        if macro_id == self.current_macro_id:
            # If so, reset the current macro
            self.current_macro = None
            self.current_macro_id = None
            self.current_macro_commands = None
            self.macro_timer_length = 0
            self.macro_timer_start = 0
        else:
            # Check if the macro is still in the buffer
            for i in range(0, len(self.macro_buffer)):
                if macro_id == self.macro_buffer[i][1]:
                    del self.macro_buffer[i]

        # Ensure the stopped macro is added to the finished
        # macros so that any blocking parties listening can
        # continue.
        if state:
            finished = state["finished_macros"]
            finished.append(macro_id)
            state["finished_macros"] = finished

        return

    def clear_macros(self):

        self.current_macro = None
        self.current_macro_id = None
        self.current_macro_commands = None
        self.macro_timer_length = 0
        self.macro_timer_start = 0
        self.macro_buffer = []

        return

    def set_controller_input(self, controller_input):

        self.controller_input = controller_input
    
    def commands_queued(self):
        check = dumps(self.controller_input) != dumps(DIRECT_INPUT_IDLE_PACKET)
        check = check or self.macro_buffer
        check = check or self.current_macro
        check = check or self.current_macro_commands
        return check

    def active_input_queued(self):
        """Checks if an active command input is queued. An active command
        is a depressed button or tilted stick.

        :return: True (on an active button) or False (no active buttons)
        :rtype: bool
        """
        if (self.current_macro_commands is not None):
            if len(self.current_macro_commands) < 2:
                return False
            else:
                return True
        elif dumps(self.controller_input) != dumps(DIRECT_INPUT_IDLE_PACKET):
            return True
        else:
            return False

    def set_protocol_input(self, state=None):

        # Act on direct input if we're not getting idle packets
        if dumps(self.controller_input) != dumps(DIRECT_INPUT_IDLE_PACKET):
            self.parse_controller_input(self.controller_input)
            self.controller_input = None

        elif (self.macro_buffer or self.current_macro or
              self.current_macro_commands):
            # Check if we can start on a new macro.
            if not self.current_macro and self.macro_buffer:
                # Preprocess command lines of current macro
                macro = self.macro_buffer.pop(0)
                self.current_macro = self.parse_macro(macro[0])
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

            self.set_macro_input(self.current_macro_commands)

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

        # Check for input validity
        if type(controller_input) != dict:
            return

        # Check if the Grip/Order menu would be closed
        if not self.exited_grip_order_menu and (
                controller_input["A"] or controller_input["B"] or controller_input["HOME"]):
            self.exited_grip_order_menu = True

        # Arrays representing the 3 button bytes in the
        # standard input report as binary.
        upper = ['0'] * 8
        shared = ['0'] * 8
        lower = ['0'] * 8
        # Upper Byte
        if controller_input["Y"]:
            upper[7] = '1'
        if controller_input["X"]:
            upper[6] = '1'
        if controller_input["B"]:
            upper[5] = '1'
        if controller_input["A"]:
            upper[4] = '1'
        if controller_input["JCL_SR"]:
            upper[3] = '1'
        if controller_input["JCL_SL"]:
            upper[2] = '1'
        if controller_input["R"]:
            upper[1] = '1'
        if controller_input["ZR"]:
            upper[0] = '1'

        # Shared byte
        if controller_input["MINUS"]:
            shared[7] = '1'
        if controller_input["PLUS"]:
            shared[6] = '1'
        if controller_input["R_STICK"]["PRESSED"]:
            shared[5] = '1'
        if controller_input["L_STICK"]["PRESSED"]:
            shared[4] = '1'
        if controller_input["HOME"]:
            shared[3] = '1'
        if controller_input["CAPTURE"]:
            shared[2] = '1'

        # Lower byte
        if controller_input["DPAD_DOWN"]:
            lower[7] = '1'
        if controller_input["DPAD_UP"]:
            lower[6] = '1'
        if controller_input["DPAD_RIGHT"]:
            lower[5] = '1'
        if controller_input["DPAD_LEFT"]:
            lower[4] = '1'
        if controller_input["JCR_SR"]:
            lower[3] = '1'
        if controller_input["JCR_SL"]:
            lower[2] = '1'
        if controller_input["L"]:
            lower[1] = '1'
        if controller_input["ZL"]:
            lower[0] = '1'

        # Analog Stick Positions
        stick_left = self.stick_ratio_to_calibrated_position(
            controller_input["L_STICK"]["X_VALUE"] / 100,
            controller_input["L_STICK"]["Y_VALUE"] / 100,
            "L_STICK"
        )
        stick_right = self.stick_ratio_to_calibrated_position(
            controller_input["R_STICK"]["X_VALUE"] / 100,
            controller_input["R_STICK"]["Y_VALUE"] / 100,
            "R_STICK"
        )

        # Converting binary strings to ints
        upper_byte = int("".join(upper), 2)
        shared_byte = int("".join(shared), 2)
        lower_byte = int("".join(lower), 2)

        self.protocol.set_button_inputs(upper_byte, shared_byte, lower_byte)
        self.protocol.set_left_stick_inputs(stick_left)
        self.protocol.set_right_stick_inputs(stick_right)

        return controller_input

    def parse_macro(self, macro):

        parsed = macro.split("\n")
        parsed = list(filter(lambda s: not s.strip() == "", parsed))
        parsed = self.parse_loops(parsed)

        return parsed

    def parse_loops(self, macro):
        parsed = []
        i = 0
        while i < len(macro):
            line = macro[i]
            if line.startswith("LOOP"):
                loop_count = int(line.split(" ")[1])
                loop_buffer = []

                # Detect delimiter and record
                if macro[i+1].startswith("\t"):
                    loop_delimiter = "\t"
                elif macro[i+1].startswith("    "):
                    loop_delimiter = "    "
                else:
                    loop_delimiter = "  "

                # Gather looping commands
                for j in range(i+1, len(macro)):
                    loop_line = macro[j]
                    if loop_line.startswith(loop_delimiter):
                        # Replace the first instance of the delimiter
                        loop_line = loop_line.replace(loop_delimiter, "", 1)
                        loop_buffer.append(loop_line)
                    # Set the new position if we either encounter the end
                    # of the loop or we reach the end of the macro
                    else:
                        i = j - 1
                        break
                    if j+1 >= len(macro):
                        i = j

                # Recursively gather other loops if present
                if any(s.startswith("LOOP") for s in loop_buffer):
                    loop_buffer = self.parse_loops(loop_buffer)
                # Multiply out the loop and concatenate
                parsed = parsed + (loop_buffer * loop_count)
            else:
                parsed.append(line)
            i += 1

        return parsed

    def set_macro_input(self, macro_input):

        # Checking if this is a wait macro command
        if len(macro_input) < 2:
            return

        # Check if the Grip/Order menu would be closed
        if not self.exited_grip_order_menu and (
                'A' in macro_input or 'B' in macro_input or 'HOME' in macro_input):
            self.exited_grip_order_menu = True

        # Arrays representing the 3 button bytes in the
        # standard input report as binary.
        upper = ['0'] * 8
        shared = ['0'] * 8
        lower = ['0'] * 8
        # Analog stick byte placeholders
        stick_left = None
        stick_right = None
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
            elif button == "JCL_SR":
                upper[3] = '1'
            elif button == "JCL_SL":
                upper[2] = '1'
            elif button == "R":
                upper[1] = '1'
            elif button == "ZR":
                upper[0] = '1'

            # Shared byte
            elif button == "MINUS":
                shared[7] = '1'
            elif button == "PLUS":
                shared[6] = '1'
            elif button == "R_STICK_PRESS":
                shared[5] = '1'
            elif button == "L_STICK_PRESS":
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
            elif button == "JCR_SR":
                lower[3] = '1'
            elif button == "JCR_SL":
                lower[2] = '1'
            elif button == "L":
                lower[1] = '1'
            elif button == "ZL":
                lower[0] = '1'

            # Analog Stick Positions
            elif button.startswith("L_STICK@"):
                stick_left = self.parse_macro_stick_position(button)
            elif button.startswith("R_STICK@"):
                stick_right = self.parse_macro_stick_position(button)

        # Converting binary strings to ints
        upper_byte = int("".join(upper), 2)
        shared_byte = int("".join(shared), 2)
        lower_byte = int("".join(lower), 2)

        self.protocol.set_button_inputs(upper_byte, shared_byte, lower_byte)
        if stick_left:
            self.protocol.set_left_stick_inputs(stick_left)
        if stick_right:
            self.protocol.set_right_stick_inputs(stick_right)

    def parse_macro_stick_position(self, stick_pos):

        stick_type = stick_pos.split("@")[0]
        positions = stick_pos.split("@")[1]
        if len(positions) < 8:
            return None

        # Converting macro to proper ratios
        sign_x = positions[0]
        ratio_x = int(positions[1:4]) / 100
        if sign_x == "-":
            ratio_x = ratio_x * -1

        sign_y = positions[4]
        ratio_y = int(positions[5:8]) / 100
        if sign_y == "-":
            ratio_y = ratio_y * -1

        calibrated_position = self.stick_ratio_to_calibrated_position(
            ratio_x, ratio_y, stick_type)

        return calibrated_position

    def stick_ratio_to_calibrated_position(self, ratio_x, ratio_y, stick_type):

        # Using the appropriate calibration values for the stick type
        if stick_type == "L_STICK":
            cal = self.LEFT_STICK_CALIBRATION
        else:
            cal = self.RIGHT_STICK_CALIBRATION

        # Converting ratios to uint16 values
        if ratio_x < 0:
            data_x_converted = (
                abs(ratio_x) * cal["min_x"] + cal["center_x"])
        else:
            data_x_converted = (
                abs(ratio_x) * cal["max_x"] + cal["center_x"])
        data_x_converted = int(round(data_x_converted))

        if ratio_y < 0:
            data_y_converted = (
                abs(ratio_y) * cal["min_y"] + cal["center_y"])
        else:
            data_y_converted = (
                abs(ratio_y) * cal["max_y"] + cal["center_y"])
        data_y_converted = int(round(data_y_converted))

        # Converting the two X/Y uint16 values to 3 uint8 Little Endian values
        # using bitshifting techniques
        converted_values = [
            # Get the last two hex digits
            data_x_converted & 0xFF,
            # Combine the last digit of the Y uint16 and the first digit
            # of the X uint16
            ((data_y_converted & 0xF) << 4) + (data_x_converted >> 8),
            # Get the first two digits of the Y uint16
            data_y_converted >> 4]

        return converted_values

    def reassign_protocol(self, protocol):

        self.protocol = protocol
