import time
from random import randint

from nxbt import Nxbt
from nxbt import ControllerTypes

MACRO = """
B 0.1s
0.1s
B 0.1s
0.1s
B 0.1s
0.1s
B 0.1s
1.5s
DPAD_LEFT 0.1s
0.1s
DPAD_LEFT 0.1s
0.1s
DPAD_LEFT 0.1s
0.1s
DPAD_LEFT 0.1s
0.1s
DPAD_LEFT 0.1s
0.1s
DPAD_RIGHT 0.075s
0.075s
DPAD_RIGHT 0.075s
0.075s
DPAD_RIGHT 0.075s
0.075s
A 0.1s
1.5s
A 0.1s
"""


def random_colour():

    return [
        randint(0, 255),
        randint(0, 255),
        randint(0, 255),
    ]


if __name__ == "__main__":

    # Loop over all Bluetooth adapters and create
    # Switch Pro Controllers
    nxbt = Nxbt()
    adapters = nxbt.get_available_adapters()
    # adapters = ["/org/bluez/hci0"]
    controller_idxs = []
    for i in range(0, len(adapters)):
        index = nxbt.create_controller(
            ControllerTypes.PRO_CONTROLLER,
            adapters[i],
            colour_body=random_colour(),
            colour_buttons=random_colour())
        controller_idxs.append(index)
    # Run a macro on the last controller
    nxbt.macro(controller_idxs[-1], MACRO, block=False)

    # Check the state
    while True:
        time.sleep(1)
        for key in nxbt.state.keys():
            state = nxbt.state[key]
            if not state["errors"]:
                print(state)
            else:
                print(state["errors"])
