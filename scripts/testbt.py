"""
A quick script to test aspects of the BlueZ API.
"""
import dbus

from nxbt import BlueZ, find_objects, SERVICE_NAME, ADAPTER_INTERFACE


bus = dbus.SystemBus()
adapters = find_objects(bus, SERVICE_NAME, ADAPTER_INTERFACE)
print(adapters)

bt = BlueZ(device_id=adapters[0].split("/")[-1])

# jc_MAC = "XX:XX:XX:XX:XX:XX"
# res = bt.discover_devices(alias="Joy-Con (L)", timeout=10)
# for key in res.keys():
#     print(res[key]["Alias"], res[key]["Address"])
# print(bt.find_device_by_address(jc_MAC))

# devices = bt.discover_devices(alias="Joy-Con (L)")
# print(devices.keys())

print("Address", bt.address)
print("Name", bt.name)
print("Alias", bt.alias)
print("Pairable", bt.pairable)

print("")
print("Pairable Timeout", bt.pairable_timeout)
bt.set_pairable_timeout(10)
print("Pairable Timeout", bt.pairable_timeout)
bt.set_pairable_timeout(0)
print("Pairable Timeout", bt.pairable_timeout)

print("")
print("Discoverable", bt.discoverable)
bt.set_discoverable(True)
print("Discoverable", bt.discoverable)
bt.set_discoverable(False)
print("Discoverable", bt.discoverable)

print("")
print("Discoverable Timeout", bt.discoverable_timeout)
bt.set_discoverable_timeout(0)
print("Discoverable Timeout", bt.discoverable_timeout)
bt.set_discoverable_timeout(180)
print("Discoverable Timeout", bt.discoverable_timeout)

try:
    print("")
    print("Device Class", bt.device_class)
    bt.set_device_class("0x002058")
    print("Device Class", bt.device_class)
    bt.set_device_class("0x480000")
    print("Device Class", bt.device_class)
except Exception as e:
    print(e)

print("")
print("Powered", bt.powered)
bt.set_powered(False)
print("Powered", bt.powered)
bt.set_powered(True)
print("Powered", bt.powered)
