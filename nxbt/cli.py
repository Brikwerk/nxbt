import argparse
from random import randint
from time import sleep
import os
import traceback

from .nxbt import Nxbt, PRO_CONTROLLER
from .bluez import find_devices_by_alias
from .tui import InputTUI


parser = argparse.ArgumentParser()
parser.add_argument('command', default=False, choices=[
                        'webapp', 'demo', 'macro', 'tui', 'remote_tui', 'addresses', 'test'
                    ],
                    help="""Specifies the nxbt command to run:
                    webapp - Runs web server and allows for controller/macro
                    input from a web browser.
                    demo - Runs a demo macro (please ensure that your Switch
                    is on the main menu's Change Grip/Order menu before running).
                    macro - Allows for input of a specified macro from the command line
                    (with the argument -s) or from a file (with the argument -f).
                    tui/remote_tui - Opens a TUI that allows for direct input from the keyboard
                    to the Switch. 
                    addresses - Lists the Bluetooth MAC addresses for
                    all previously connected Nintendo Switches.
                    test - Runs through a series of tests to ensure NXBT is working and
                    compatible with your system.""")
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
parser.add_argument('-i', '--ip', required=False, default="0.0.0.0", type=str,
                    help="""Specifies the IP to run the webapp at. Defaults to 0.0.0.0""")
parser.add_argument('-p', '--port', required=False, default=8000, type=int,
                    help="""Specifies the port to run the webapp at. Defaults to 8000""")
parser.add_argument('--usessl', required=False, default=False, action='store_true',
                    help="""Enables or disables SSL use in the webapp""")
parser.add_argument('--certpath', required=False, default=None, type=str,
                    help="""Specifies the folder location for SSL certificates used
                    in the webapp. Certificates in this folder should be in the form of
                    a 'cert.pem' and 'key.pem' pair.""")                
args = parser.parse_args()


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
DPAD_DOWN 0.93s
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
    print("Running Demo...")
    macro_id = nx.macro(controller_idxs[-1], MACRO, block=False)
    while macro_id not in nx.state[controller_idxs[-1]]["finished_macros"]:
        state = nx.state[controller_idxs[-1]]
        if state['state'] == 'crashed':
            print("An error occurred while running the demo:")
            print(state['errors'])
            exit(1)
        sleep(1.0)

    print("Finished!")


def test():
    """Tests NXBT functionality"""
    # Init
    print("[1] Attempting to initialize NXBT...")
    nx = None
    try:
        nx = Nxbt(debug=args.debug, log_to_file=args.logfile)
    except Exception as e:
        print("Failed to initialize:")
        print(traceback.format_exc())
        exit(1)
    print("Successfully initialized NXBT.\n")

    # Adapter Check
    print("[2] Checking for Bluetooth adapter availability...")
    adapters = None
    try:
        adapters = nx.get_available_adapters()
    except Exception as e:
        print("Failed to check for adapters:")
        print(traceback.format_exc())
        exit(1)
    if len(adapters) < 1:
        print("Unable to detect any Bluetooth adapters.")
        print("Please ensure you system has Bluetooth capability.")
        exit(1)
    print(f"{len(adapters)} Bluetooth adapter(s) available.")
    print("Adapters:", adapters, "\n")

    # Creating a controller
    print("[3] Please turn on your Switch and navigate to the 'Change Grip/Order menu.'")
    input("Press Enter to continue...")

    print("Creating a controller with the first Bluetooth adapter...")
    cindex = None
    try:
        cindex = nx.create_controller(
                 PRO_CONTROLLER,
                 adapters[0],
                 colour_body=random_colour(),
                 colour_buttons=random_colour())
    except Exception as e:
        print("Failed to create a controller:")
        print(traceback.format_exc())
        exit(1)
    print("Successfully created a controller.\n")

    # Controller connection check
    print("[4] Waiting for controller to connect with the Switch...")
    timeout = 120
    print(f"Connection timeout is {timeout} seconds for this test script.")
    elapsed = 0
    while nx.state[cindex]['state'] != 'connected':
        if elapsed >= timeout:
            print("Timeout reached, exiting...")
            exit(1)
        elif nx.state[cindex]['state'] == 'crashed':
            print("An error occurred while connecting:")
            print(nx.state[cindex]['errors'])
            exit(1)
        elapsed += 1
        sleep(1)
    print("Successfully connected.\n")

    # Exit the Change Grip/Order Menu
    print("[5] Attempting to exit the 'Change Grip/Order Menu'...")
    nx.macro(cindex, "B 0.1s\n0.1s")
    sleep(5)
    if nx.state[cindex]['state'] != 'connected':
        print("Controller disconnected after leaving the menu.")
        print("Exiting...")
        exit(1)
    print("Controller successfully exited the menu.\n")

    print("All tests passed.")


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
        reconnect_address=reconnect_target,
        frequency=132)
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
        start_web_app(ip=args.ip, port=args.port,
            usessl=args.usessl, cert_path=args.certpath)
    elif args.command == 'demo':
        demo()
    elif args.command == 'macro':
        macro()
    elif args.command == 'tui':
        reconnect_target = get_reconnect_target()
        tui = InputTUI(reconnect_target=reconnect_target)
        tui.start()
    elif args.command == 'remote_tui':
        reconnect_target = get_reconnect_target()
        tui = InputTUI(reconnect_target=reconnect_target, force_remote=True)
        tui.start()
    elif args.command == 'addresses':
        list_switch_addresses()
    elif args.command == 'test':
        test()
