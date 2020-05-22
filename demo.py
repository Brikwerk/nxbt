import threading
import time

from nxbt import ControllerServer
from nxbt import ControllerTypes

# con = ControllerServer(ControllerTypes.JOYCON_R)
# con.run()
# # con.run(reconnect_address="7C:BB:8A:D9:91:5A")


def thread_func_1():

    print("Starting Thread 1")
    con = ControllerServer(ControllerTypes.JOYCON_R)
    con.run()


def thread_func_2():

    print("Starting Thread 2")
    time.sleep(10)
    con = ControllerServer(ControllerTypes.JOYCON_L)
    con.run()


if __name__ == "__main__":

    x = threading.Thread(target=thread_func_1)
    x.start()
