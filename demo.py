import time

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


if __name__ == "__main__":

    nxbt = Nxbt()
    adapters = nxbt.get_available_adapters()
    index = nxbt.create_controller(
        ControllerTypes.PRO_CONTROLLER,
        adapters[0],
        colour_body=[0xFF, 0x7B, 0x83],
        colour_buttons=[0xFF, 0xF0, 0x78])
    index2 = nxbt.create_controller(
        ControllerTypes.PRO_CONTROLLER,
        adapters[1],
        colour_body=[0xFF, 0xFF, 0xFF],
        colour_buttons=[0xFF, 0xF0, 0x78])
    nxbt.macro(index2, MACRO, block=False)
    while True:
        time.sleep(1)
        state = nxbt.state[0]
        if not state["errors"]:
            print(state["finished_macros"])
        else:
            print(state["errors"])
            break
