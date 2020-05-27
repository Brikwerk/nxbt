import time

from nxbt import Nxbt
from nxbt import ControllerTypes


if __name__ == "__main__":

    nxbt = Nxbt()
    index = nxbt.create_controller(
        ControllerTypes.PRO_CONTROLLER, "/org/bluez/hci0")

    while True:
        time.sleep(1)
        print(nxbt.get_state())
