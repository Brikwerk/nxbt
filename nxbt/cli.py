import argparse
from random import randint
from time import sleep
import os

from .nxbt import Nxbt, PRO_CONTROLLER
from .bluez import find_devices_by_alias
from .tui import InputTUI


parser = argparse.ArgumentParser()
parser.add_argument('command', default=False, choices=[
                        'webapp', 'demo', 'macro', 'tui', 'addresses'
                    ],
                    help="""Specifies the nxbt command to run:
                    webapp - Runs web server and allows for controller/macro
                    input from a web browser.
                    demo - Runs a demo macro (please ensure that your Switch
                    is on the main menu's Change Grip/Order menu before running).
                    macro - Allows for input of a specified macro from the command line
                    (with the argument -s) or from a file (with the argument -f).
                    input - Opens a TUI that allows for direct input from the keyboard
                    to the Switch. addresses - Lists the Bluetooth MAC addresses for
                    all previously connected Nintendo Switches""")
parser.add_argument('-c', '--commands', required=False, default=False,
                    help="""Used in conjunction with the macro command. Specifies a
                    macro string or a file location to load a macro string from.""")
parser.add_argument('-r', '--reconnect', required=False, default=False, action='store_true',
                    help="""Used in conjunction with the macro or tui command. If specified,
                    nxbt will attmept to reconnect to any previously connected
                    Nintendo Switch.""")
parser.add_argument('-a', '--address', required=False, default=False,
                    help="""Used in conjunction with the macro or tui command. If specified,
                    nxbt will attmept to reconnect to a specific Bluetooth MAC address
                    of a Nintendo Switch.""")
parser.add_argument('-d', '--debug', required=False, default=False, action='store_true',
                    help="""Enables debug mode in nxbt.""")
parser.add_argument('-l', '--logfile', required=False, default=False, action='store_true',
                    help="""Enables logging to a file in the current working directory
                    instead of stderr.""")
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


def check_bluetooth_address(address):
    """Check the validity of a given Bluetooth MAC address

    :param address: A Bluetooth MAC address
    :type address: str
    :raises ValueError: If the Bluetooth address is invalid
    """

    address_bytes = len(address.split(":"))
    if address_bytes != 6:
        raise ValueError("Invalid Bluetooth address")


def get_reconnect_target():

    if args.reconnect:
        reconnect_target = find_devices_by_alias("Nintendo Switch")
    elif args.address:
        check_bluetooth_address(args.address)
        reconnect_target = args.address
    else:
        reconnect_target = None

    return reconnect_target


def demo():
    """Loops over all available Bluetooth adapters
    and creates controllers on each. The last available adapter
    is used to run a macro.
    """

    nx = Nxbt(debug=args.debug, log_to_file=args.logfile)
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


def macro():
    """Runs a macro from the command line.
    The macro can be from a specified file, a command line string,
    or input from the user in an interactive process.
    """

    macro = None
    if args.commands:
        if os.path.isfile(args.commands):
            with open(args.commands, "r") as f:
                macro = f.read()
        else:
            macro = args.commands
    else:
        print("No macro commands were specified.")
        print("Please use the -c argument to specify a macro string or a file location")
        print("to load a macro string from.")
        return

    reconnect_target = get_reconnect_target()

    nx = Nxbt(debug=args.debug, log_to_file=args.logfile)
    print("Creating controller...")
    index = nx.create_controller(
        PRO_CONTROLLER,
        colour_body=random_colour(),
        colour_buttons=random_colour(),
        reconnect_address=reconnect_target)
    print("Waiting for connection...")
    nx.wait_for_connection(index)
    print("Connected!")

    print("Running macro...")
    macro_id = nx.macro(index, macro, block=False)
    while (True):
        if nx.state[index]["state"] == "crashed":
            print("Controller crashed while running macro")
            print(nx.state[index]["errors"])
            break
        if macro_id in nx.state[index]["finished_macros"]:
            print("Finished running macro. Exiting...")
            break
        sleep(1/30)


def list_switch_addresses():

    addresses = find_devices_by_alias("Nintendo Switch")

    if not addresses or len(addresses) < 1:
        print("No Switches have previously connected to this device.")
        return

    print("---------------------------")
    print("| Num | Address           |")
    print("---------------------------")
    for i in range(0, len(addresses)):
        address = addresses[i]
        print(f"| {i+1}   | {address} |")
    print("---------------------------")


def main():

    if args.command == 'webapp':
        from .web import start_web_app
        start_web_app()
    elif args.command == 'demo':
        demo()
    elif args.command == 'macro':
        macro()
    elif args.command == 'tui':
        reconnect_target = get_reconnect_target()
        tui = InputTUI(reconnect_target=reconnect_target)
        tui.start()
    elif args.command == 'addresses':
        list_switch_addresses()
