from random import randint
from time import sleep

from nxbt import Nxbt, PRO_CONTROLLER


MACRO = """
B 0.1s
0.5s
B 0.1s
0.5s
B 0.1s
0.5s
B 0.1s
1.5s
DPAD_RIGHT 0.075s
0.075s
A 0.1s
1.5s
LOOP 12
    DPAD_DOWN 0.075s
    0.075s
A 0.1s
0.25s
LOOP 3
    DPAD_DOWN 0.1s
    0.1s
DPAD_DOWN 0.54s
0.1s
A 0.1s
0.25s
L_STICK_PRESS 0.1s
1.0s
L_STICK@-100+000 1.0s
L_STICK@+000+100 1.0s
L_STICK@+100+000 1.0s
L_STICK@+000-100 1.0s
B 0.1s
0.25s
R_STICK_PRESS 0.1s
1.0s
R_STICK@-100+000 1.0s
R_STICK@+000+100 1.0s
R_STICK@+100+000 1.0s
R_STICK@+000-100 1.0s
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
1.75s
A 0.1s
5.0s
"""


def random_colour():

    return [
        randint(0, 255),
        randint(0, 255),
        randint(0, 255),
    ]


def demo():
    """Loops over all available Bluetooth adapters
    and creates controllers on each. The last available adapter
    is used to run a macro.
    """

    nx = Nxbt(debug=False)
    adapters = nx.get_available_adapters()
    if len(adapters) < 1:
        raise OSError("Unable to detect any Bluetooth adapters.")

    controller_idxs = []
    for i in range(0, len(adapters)):
        index = nx.create_controller(
            PRO_CONTROLLER,
            adapters[i],
            colour_body=random_colour(),
            colour_buttons=random_colour())
        controller_idxs.append(index)

    # Run a macro on the last controller
    for i in range(100):
        print(f"Running Demo: Iteration {i}")
        macro_id = nx.macro(controller_idxs[-1], MACRO, block=False)
        while macro_id not in nx.state[controller_idxs[-1]]["finished_macros"]:
            state = nx.state[controller_idxs[-1]]
            if state['state'] == 'crashed':
                print("An error occurred while running the demo:")
                print(state['errors'])
                exit(1)
            sleep(1.0)

    print("Finished!")

if __name__ == "__main__":
    demo()