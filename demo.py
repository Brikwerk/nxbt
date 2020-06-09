import time
from random import randint

import nxbt

MACRO = """
B 0.1s
0.1s
B 0.1s
0.1s
B 0.1s
0.1s
B 0.1s
1.5s
DPAD_RIGHT 0.075s
0.075s
A 0.1s
1.5s
DPAD_DOWN 1.0s
A 0.1s
0.25s
DPAD_DOWN 0.8s
A 0.1s
0.25s
L_STICK_PRESS 0.1s
1.0s
L_STICK@-100+000 0.75s
L_STICK@+000+100 0.75s
L_STICK@+100+000 0.75s
L_STICK@+000-100 0.75s
B 0.1s
0.25s
R_STICK_PRESS 0.1s
1.0s
R_STICK@-100+000 0.75s
R_STICK@+000+100 0.75s
R_STICK@+100+000 0.75s
R_STICK@+000-100 0.75s
B 0.1s
0.1s
B 0.1s
0.1s
B 0.1s
0.1s
B 0.1s
0.4s
DPAD_LEFT 0.1s
0.1s
A 0.1s
1.5s
A 0.1s
0.1s
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
    nx = nxbt.Nxbt()
    adapters = nx.get_available_adapters()
    controller_idxs = []
    for i in range(0, len(adapters)):
        index = nx.create_controller(
            nxbt.PRO_CONTROLLER,
            adapters[i],
            colour_body=random_colour(),
            colour_buttons=random_colour())
        controller_idxs.append(index)

    # Run a macro on the last controller
    # and don't wait for the macro to complete
    nx.macro(controller_idxs[-1], MACRO, block=False)

    # Check the state
    while True:
        time.sleep(1)
        for key in nx.state.keys():
            state = nx.state[key]
            if not state["errors"]:
                print(state)
            else:
                print(state["errors"])
