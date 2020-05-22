import time

from nxbt import ControllerTypes
from nxbt import ControllerProtocol


INPUT_REPORT = b'\xa2\x01\x0E\x00\x00\x00\x00\x00\x00\x00\x00\x02\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

protocol = ControllerProtocol(
    ControllerTypes.JOYCON_L,
    "AA:AA:AA:AA:AA:AA")
protocol.process_commands(None)
print(hex(protocol.get_report()[2]))
time.sleep(1)
protocol.process_commands(None)
print(hex(protocol.get_report()[2]))
protocol.process_commands(INPUT_REPORT)
print(hex(protocol.get_report()[2]))
time.sleep(1)
protocol.process_commands(None)
print(hex(protocol.get_report()[2]))
protocol.process_commands(None)
print(hex(protocol.get_report()[2]))
