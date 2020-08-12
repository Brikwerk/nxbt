import time
from random import randint

import nxbt
from nxbt import Buttons
from nxbt import Sticks

MACRO = """
LOOP 12
    B 0.1s
    0.1s
1.5s
DPAD_RIGHT 0.075s
0.075s
A 0.1s
1.5s
DPAD_DOWN 1.00s
A 0.1s
0.25s
DPAD_DOWN 0.95s
A 0.1s
0.25s
L_STICK_PRESS 0.1s
1.0s
L_STICK@-100+000 0.5s
L_STICK@+000+100 0.5s
L_STICK@+100+000 0.5s
L_STICK@+000-100 0.5s
B 0.1s
0.25s
R_STICK_PRESS 0.1s
1.0s
R_STICK@-100+000 0.5s
R_STICK@+000+100 0.5s
R_STICK@+100+000 0.5s
R_STICK@+000-100 0.5s
LOOP 4
    B 0.1s
    0.1s
B 0.1s
0.4s
DPAD_LEFT 0.1s
0.1s
A 0.1s
1.5s
A 0.1s
5.0s
"""


def random_colour():

    return [
        randint(0, 255),
        randint(0, 255),
        randint(0, 255),
    ]


if __name__ == "__main__":

    # Init NXBT
    nx = nxbt.Nxbt()

    # Get a list of all available Bluetooth adapters
    adapters = nx.get_available_adapters()
    # Prepare a list to store the indexes of the
    # created controllers.
    controller_idxs = []
    # Loop over all Bluetooth adapters and create
    # Switch Pro Controllers
    for i in range(0, len(adapters)):
        index = nx.create_controller(
            nxbt.PRO_CONTROLLER,
            adapter_path=adapters[i],
            colour_body=random_colour(),
            colour_buttons=random_colour())
        controller_idxs.append(index)

    # Select the last controller for input
    controller_idx = controller_idxs[-1]

    # Wait for the switch to connect to the controller
    nx.wait_for_connection(controller_idx)

    # Run a macro on the last controller
    # and don't wait for the macro to complete
    print("Macro Started")
    macro_id = nx.macro(controller_idx, MACRO, block=False)
    time.sleep(3)
    # Stop the macro
    print("Stopping Macro")
    nx.stop_macro(controller_idx, macro_id)
    print("Stopped Macro")

    # Moving the selected home screen item two spaces to the right and back.
    nx.tilt_stick(controller_idx, Sticks.RIGHT_STICK, 100, 0,
                  tilted=0.25, released=0.25)
    nx.tilt_stick(controller_idx, Sticks.RIGHT_STICK, 100, 0,
                  tilted=0.25, released=0.25)
    nx.tilt_stick(controller_idx, Sticks.RIGHT_STICK, -100, 0,
                  tilted=0.25, released=0.25)
    nx.tilt_stick(controller_idx, Sticks.RIGHT_STICK, -100, 0,
                  tilted=0.25, released=0.25)

    # Return to the "Change Grip/Order Screen"
    nx.press_buttons(controller_idx, [Buttons.A])
    time.sleep(2)
    nx.press_buttons(controller_idx, [Buttons.A])
    time.sleep(2)

    # Enter the same macro, but block this time
    print("Macro Started")
    macro_id = nx.macro(controller_idx, MACRO)
    print("Macro finished, going to the home screen...")

    nx.press_buttons(controller_idx, [Buttons.B])
    time.sleep(2)
    nx.press_buttons(controller_idx, [Buttons.B])
    time.sleep(2)

    print("Exiting...")
