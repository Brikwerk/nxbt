import argparse
import time
from random import randint

from .web import start_web_app
from .nxbt import Nxbt, PRO_CONTROLLER


parser = argparse.ArgumentParser()
parser.add_argument('command', default=False, choices=['start', 'demo'],
                    help="Specifies the Nxbt command to run")
args = parser.parse_args()


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
DPAD_DOWN 0.95s
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

    nx = Nxbt()
    adapters = nx.get_available_adapters()
    controller_idxs = []
    for i in range(0, len(adapters)):
        index = nx.create_controller(
            PRO_CONTROLLER,
            adapters[i],
            colour_body=random_colour(),
            colour_buttons=random_colour())
        controller_idxs.append(index)

    # Run a macro on the last controller
    # and don't wait for the macro to complete
    nx.macro(controller_idxs[-1], MACRO)


def main():

    if args.command == 'start':
        start_web_app()
    elif args.command == 'demo':
        demo()
