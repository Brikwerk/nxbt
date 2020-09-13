import subprocess
import re
import os
import time
import logging

import dbus


SERVICE_NAME = "org.bluez"
BLUEZ_OBJECT_PATH = "/org/bluez"
ADAPTER_INTERFACE = SERVICE_NAME + ".Adapter1"
PROFILEMANAGER_INTERFACE = SERVICE_NAME + ".ProfileManager1"
DEVICE_INTERFACE = SERVICE_NAME + ".Device1"


def find_object_path(bus, service_name, interface_name, object_name=None):
    """Searches for a D-Bus object path that contains a specified interface
    under a specified service.

    :param bus: A DBus object used to access the DBus.
    :type bus: DBus
    :param service_name: The name of a D-Bus service to search for the
    object path under.
    :type service_name: string
    :param interface_name: The name of a D-Bus interface to search for
    within objects under the specified service.
    :type interface_name: string
    :param object_name: The name or ending of the object path,
    defaults to None
    :type object_name: string, optional
    :return: The D-Bus object path or None, if no matching object
    can be found
    :rtype: string
    """

    manager = dbus.Interface(
        bus.get_object(service_name, "/"),
        "org.freedesktop.DBus.ObjectManager")

    # Iterating over objects under the specified service
    # and searching for the specified interface
    for path, ifaces in manager.GetManagedObjects().items():
        managed_interface = ifaces.get(interface_name)
        if managed_interface is None:
            continue
        # If the object name wasn't specified or it matches
        # the interface address or the path ending
        elif (not object_name or
                object_name == managed_interface["Address"] or
                path.endswith(object_name)):
            obj = bus.get_object(service_name, path)
            return dbus.Interface(obj, interface_name).object_path

    return None


def find_objects(bus, service_name, interface_name):
    """Searches for D-Bus objects that contain a specified interface
    under a specified service.

    :param bus: A DBus object used to access the DBus.
    :type bus: DBus
    :param service_name: The name of a D-Bus service to search for the
    object path under.
    :type service_name: string
    :param interface_name: The name of a D-Bus interface to search for
    within objects under the specified service.
    :type interface_name: string
    :return: The D-Bus object paths matching the arguments
    :rtype: array
    """

    manager = dbus.Interface(
        bus.get_object(service_name, "/"),
        "org.freedesktop.DBus.ObjectManager")
    paths = []

    # Iterating over objects under the specified service
    # and searching for the specified interface within them
    for path, ifaces in manager.GetManagedObjects().items():
        managed_interface = ifaces.get(interface_name)
        if managed_interface is None:
            continue
        else:
            obj = bus.get_object(service_name, path)
            path = str(dbus.Interface(obj, interface_name).object_path)
            paths.append(path)

    return paths


def toggle_input_plugin(toggle):
    """Enables or disables the BlueZ input plugin. Requires
    root user to be run. The units and Bluetooth service will
    not be restarted if the input plugin already matches
    the toggle.

    :param toggle: A boolean element indicating if the plugin
    is enabled (True) or disabled (False)
    :type toggle: boolean
    :raises PermissionError: If the user is not root
    :raises Exception: If the units can't be reloaded
    """

    service_path = "/lib/systemd/system/bluetooth.service"
    service = None
    with open(service_path, "r") as f:
        service = f.read()

    # Find the bluetooth service execution line
    lines = service.split("\n")
    for i in range(0, len(lines)):
        line = lines[i]
        if line.startswith("ExecStart="):
            # If we want to ensure the plugin is enabled
            if toggle:
                # If input is already enabled
                if "--noplugin=input" not in line:
                    return
                lines[i] = re.sub(" --noplugin=input", "", line)
            else:
                # If input is already disabled
                if "--noplugin=input" in line:
                    return
                # If not, add the flag
                lines[i] = line + " --noplugin=input"

    service = "\n".join(lines)
    with open(service_path, "w") as f:
        f.write(service)

    # Reload units
    result = subprocess.run(
        ["systemctl", "daemon-reload"],
        stderr=subprocess.PIPE)

    cmd_err = result.stderr.decode("utf-8").replace("\n", "")
    if cmd_err != "":
        raise Exception(cmd_err)

    # Reload the bluetooth service with input disabled
    result = subprocess.run(
            ["systemctl", "restart", "bluetooth"],
            stderr=subprocess.PIPE)

    cmd_err = result.stderr.decode("utf-8").replace("\n", "")
    if cmd_err != "":
        raise Exception(cmd_err)

    # Kill a bit of time here to ensure all services have restarted
    time.sleep(0.5)


def find_devices_by_alias(alias):
    """Finds the Bluetooth addresses of devices
    that have a specified Bluetooth alias. Aliases
    are converted to uppercase before comparison
    as BlueZ usually converts aliases to uppercase.

    :param address: The Bluetooth MAC address
    :type address: string
    :return: The path to the D-Bus object or None
    :rtype: string or None
    """

    bus = dbus.SystemBus()
    # Find all connected/paired/discovered devices
    devices = find_objects(
        bus,
        SERVICE_NAME,
        DEVICE_INTERFACE)

    addresses = []
    for path in devices:
        # Get the device's address and paired status
        device_props = dbus.Interface(
            bus.get_object(SERVICE_NAME, path),
            "org.freedesktop.DBus.Properties")
        device_alias = device_props.Get(
            DEVICE_INTERFACE,
            "Alias").upper()
        device_addr = device_props.Get(
            DEVICE_INTERFACE,
            "Address").upper()

        # Check for an address match
        if device_alias.upper() == alias.upper():
            addresses.append(device_addr)

    bus.close()
    return addresses


class BlueZ():
    """Exposes the BlueZ D-Bus API as a Python object.
    """

    def __init__(self, adapter_path="/org/bluez/hci0"):

        self.logger = logging.getLogger('nxbt')

        self.bus = dbus.SystemBus()
        self.device_path = adapter_path

        # If we weren't able to find an adapter with the specified ID,
        # try to find any usable Bluetooth adapter
        if self.device_path is None:
            self.device_path = find_object_path(
                self.bus,
                SERVICE_NAME,
                ADAPTER_INTERFACE)

        # If we aren't able to find an adapter still
        if self.device_path is None:
            raise Exception("Unable to find a bluetooth adapter")

        # Load the adapter's interface
        self.logger.debug(f"Using adapter under object path: {self.device_path}")
        self.device = dbus.Interface(
            self.bus.get_object(
                SERVICE_NAME,
                self.device_path),
            "org.freedesktop.DBus.Properties")

        self.device_id = self.device_path.split("/")[-1]

        # Load the ProfileManager interface
        self.profile_manager = dbus.Interface(self.bus.get_object(
            SERVICE_NAME, BLUEZ_OBJECT_PATH),
            PROFILEMANAGER_INTERFACE)

        self.adapter = dbus.Interface(
            self.bus.get_object(
                SERVICE_NAME,
                self.device_path),
            ADAPTER_INTERFACE)

    @property
    def address(self):
        """Gets the Bluetooth MAC address of the Bluetooth adapter.

        :return: The Bluetooth Adapter's MAC address
        :rtype: string
        """

        return self.device.Get(ADAPTER_INTERFACE, "Address").upper()

    @property
    def name(self):
        """Gets the name of the Bluetooth adapter.

        :return: The name of the Bluetooth adapter.
        :rtype: string
        """

        return self.device.Get(ADAPTER_INTERFACE, "Name")

    @property
    def alias(self):
        """Gets the alias of the Bluetooth adapter. This value is used
        as the "friendly" name of the adapter when communicating over
        Bluetooth.

        :return: The adapter's alias
        :rtype: string
        """

        return self.device.Get(ADAPTER_INTERFACE, "Alias")

    def set_alias(self, value):
        """Asynchronously sets the alias of the Bluetooth adapter.
        If you wish to check the set value, a time delay is needed
        before the alias getter is run.

        :param value: The new value to be set as the adapter's alias
        :type value: string
        """

        self.device.Set(ADAPTER_INTERFACE, "Alias", value)

    @property
    def pairable(self):
        """Gets the pairable status of the Bluetooth adapter.

        :return: A boolean value representing if the adapter is set as
        pairable or not
        :rtype: boolean
        """

        return bool(self.device.Get(ADAPTER_INTERFACE, "Pairable"))

    def set_pairable(self, value):
        """Sets the pariable boolean status of the Bluetooth adapter.

        :param value: A boolean value representing if the adapter is
        pairable or not.
        :type value: boolean
        """

        dbus_value = dbus.Boolean(value)
        self.device.Set(ADAPTER_INTERFACE, "Pairable", dbus_value)

    @property
    def pairable_timeout(self):
        """Gets the timeout time (in seconds) for how long the adapter
        should remain as pairable. Defaults to 0 (no timeout).

        :return: The pairable timeout in seconds
        :rtype: int
        """

        return self.device.Get(ADAPTER_INTERFACE, "PairableTimeout")

    def set_pairable_timeout(self, value):
        """Sets the timeout time (in seconds) for the pairable property.

        :param value: The pairable timeout value in seconds
        :type value: int
        """

        dbus_value = dbus.UInt32(value)
        self.device.Set(ADAPTER_INTERFACE, "PairableTimeout", dbus_value)

    @property
    def discoverable(self):
        """Gets the discoverable status of the Bluetooth adapter

        :return: The boolean status of the discoverable status
        :rtype: boolean
        """

        return bool(self.device.Get(ADAPTER_INTERFACE, "Discoverable"))

    def set_discoverable(self, value):
        """Sets the discoverable boolean status of the Bluetooth adapter.

        :param value: A boolean value representing if the Bluetooth adapter
        is discoverable or not.
        :type value: boolean
        """

        dbus_value = dbus.Boolean(value)
        self.device.Set(ADAPTER_INTERFACE, "Discoverable", dbus_value)

    @property
    def discoverable_timeout(self):
        """Gets the timeout time (in seconds) for how long the adapter
        should remain as discoverable. Defaults to 180 (3 minutes).

        :return: The discoverable timeout in seconds
        :rtype: int
        """

        return self.device.Get(ADAPTER_INTERFACE, "DiscoverableTimeout")

    def set_discoverable_timeout(self, value):
        """Sets the discoverable time (in seconds) for the discoverable
        property. Setting this property to 0 results in an infinite
        discoverable timeout.

        :param value: The discoverable timeout value in seconds
        :type value: int
        """

        dbus_value = dbus.UInt32(value)
        self.device.Set(
            ADAPTER_INTERFACE,
            "DiscoverableTimeout",
            dbus_value)

    @property
    def device_class(self):
        """Gets the Bluetooth class of the device. This represents what type
        of device this reporting as (Ex: Gamepad, Headphones, etc).

        :return: A 32-bit hexadecimal Integer representing the
        Bluetooth Code for a given device type.
        :rtype: string
        """

        # This is another hacky bit. We're using hciconfig here instead
        # of the D-Bus API so that results match the setter. See the
        # setter for further justification on using hciconfig.
        result = subprocess.run(
            ["hciconfig", self.device_id, "class"],
            stdout=subprocess.PIPE)
        device_class = result.stdout.decode("utf-8").split("Class: ")[1][0:8]

        return device_class

    def set_device_class(self, device_class):
        """Sets the Bluetooth class of the device. This represents what type
        of device this reporting as (Ex: Gamepad, Headphones, etc).
        Note: To work this function *MUST* be run as the super user. An
        exception is returned if this function is run without elevation.

        :param device_class: A 32-bit Hexadecimal integer
        :type device_class: string
        :raises PermissionError: If user is not root
        :raises ValueError: If the device class is not length 8
        :raises Exception: On inability to set class
        """

        if os.geteuid() != 0:
            raise PermissionError("The device class must be set as root")

        if len(device_class) != 8:
            raise ValueError("Device class must be length 8")

        # This is a bit of a hack. BlueZ allows you to set this value, however,
        # a config file needs to filled and the BT daemon restarted. This is a
        # good compromise but requires super user privileges. Not ideal.
        result = subprocess.run(
            ["hciconfig", self.device_id, "class", device_class],
            stderr=subprocess.PIPE)

        # Checking if there was a problem setting the device class
        cmd_err = result.stderr.decode("utf-8").replace("\n", "")
        if cmd_err != "":
            raise Exception(cmd_err)

    @property
    def powered(self):
        """The powered state of the adapter (on/off) as a boolean value.

        :return: A boolean representing the powered state of the adapter.
        :rtype: boolean
        """

        return bool(self.device.Get(ADAPTER_INTERFACE, "Powered"))

    def set_powered(self, value):
        """Switches the adapter on or off.

        :param value: A boolean value switching the adapter on or off
        :type value: boolean
        """

        dbus_value = dbus.Boolean(value)
        self.device.Set(ADAPTER_INTERFACE, "Powered", dbus_value)

    def register_profile(self, profile_path, uuid, opts):
        """Registers an SDP record on the BlueZ SDP server.

        Options (non-exhaustive, refer to BlueZ docs for
        the complete list):

        - Name: Human readable name of the profile

        - Role: Specifies precise local role. Either "client"
        or "servier".

        - RequireAuthentication: A boolean value indicating if
        pairing is required before connection.

        - RequireAuthorization: A boolean value indiciating if
        authorization is needed before connection.

        - AutoConnect: A boolean value indicating whether a
        connection can be forced if a client UUID is present.

        - ServiceRecord: An XML SDP record as a string.

        :param profile_path: The path for the SDP record
        :type profile_path: string
        :param uuid: The UUID for the SDP record
        :type uuid: string
        :param opts: The options for the SDP server
        :type opts: dict
        """

        self.profile_manager.RegisterProfile(profile_path, uuid, opts)

    def reset(self):
        """Restarts the Bluetooth Service

        :raises Exception: If the bluetooth service can't be restarted
        """

        result = subprocess.run(
            ["systemctl", "restart", "bluetooth"],
            stderr=subprocess.PIPE)

        cmd_err = result.stderr.decode("utf-8").replace("\n", "")
        if cmd_err != "":
            raise Exception(cmd_err)

        self.device = dbus.Interface(
            self.bus.get_object(
                SERVICE_NAME,
                self.device_path),
            "org.freedesktop.DBus.Properties")
        self.profile_manager = dbus.Interface(
            self.bus.get_object(
                SERVICE_NAME,
                BLUEZ_OBJECT_PATH),
            PROFILEMANAGER_INTERFACE)

    def get_discovered_devices(self):
        """Gets a dict of all discovered (or previously discovered
        and connected) devices. The key is the device's dbus object
        path and the values are the device's properties.

        The following is a non-exhaustive list of the properties a
        device dictionary can contain:
        - "Address": The Bluetooth address
        - "Alias": The friendly name of the device
        - "Paired": Whether the device is paired
        - "Connected": Whether the device is presently connected
        - "UUIDs": The services a device provides

        :return: A dictionary of all discovered devices
        :rtype: dictionary
        """

        bluez_objects = dbus.Interface(
            self.bus.get_object(SERVICE_NAME, "/"),
            "org.freedesktop.DBus.ObjectManager")

        devices = {}
        objects = bluez_objects.GetManagedObjects()
        for path, interfaces in list(objects.items()):
            if DEVICE_INTERFACE in interfaces:
                devices[str(path)] = interfaces[DEVICE_INTERFACE]

        return devices

    def discover_devices(self, alias=None, timeout=10, callback=None):
        """Runs a device discovery of the timeout length (in seconds)
        on the adapter. If specified, a callback is run, every second,
        and passed an updated list of discovered devices. An alias
        can be specified to filter discovered devices.

        The following is a non-exhaustive list of the properties a
        device dictionary can contain:
        - "Address": The Bluetooth address
        - "Alias": The friendly name of the device
        - "Paired": Whether the device is paired
        - "Connected": Whether the device is presently connected
        - "UUIDs": The services a device provides

        :param alias: The alias of a bluetooth device, defaults to None
        :type alias: string, optional
        :param timeout: The discovery timeout in seconds, defaults to 10
        :type timeout: int, optional
        :param callback: A callback function, defaults to None
        :type callback: function, optional
        :return: A dictionary of discovered devices with the object path
        as the key and the device properties as the dictionary properties
        :rtype: dictionary
        """

        # TODO: Device discovery still needs work. Currently, devices
        # are added as DBus objects while device discovery runs, however,
        # added devices linger after discovery stops. This means a device
        # can become unpairable, still show up on a new discovery session,
        # and throw an error when an attempt is made to pair it. Using DBus
        # signals ("interface added"/"property changed") does not solve
        # this issue.

        # Get all devices that have been previously discovered
        devices = self.get_discovered_devices()

        # Start discovering new devices and loop
        self.adapter.StartDiscovery()
        try:
            for i in range(0, timeout):
                time.sleep(1)

                new_devices = self.get_discovered_devices()
                # Shallowly merging dictionaries. Latter dictionary
                # overrides the former. Requires Python 3.5
                devices = {**devices, **new_devices}

                if callback:
                    callback(devices)
        finally:
            self.adapter.StopDiscovery()

        # Filter out paired devices or devices that don't
        # match a specified alias.
        filtered_devices = {}
        for key in devices.keys():
            # Filter for devices matching alias, if specified
            if "Alias" not in devices[key].keys():
                continue
            if alias and not alias == devices[key]["Alias"]:
                continue

            # Filter for paired devices
            if "Paired" not in devices[key].keys():
                continue
            if devices[key]["Paired"]:
                continue

            filtered_devices[key] = devices[key]

        return filtered_devices

    def pair_device(self, device_path):
        """Pairs a discovered device at a given DBus object path.

        :param device_path: The D-Bus object path to the device
        :type device_path: string
        """

        device = dbus.Interface(
            self.bus.get_object(
                SERVICE_NAME,
                device_path),
            DEVICE_INTERFACE)
        device.Pair()

    def connect_device(self, device_path):

        device = dbus.Interface(
            self.bus.get_object(
                SERVICE_NAME,
                device_path),
            DEVICE_INTERFACE)
        try:
            device.Connect()
        except dbus.exceptions.DBusException as e:
            self.logger.exception(e)

    def remove_device(self, path):
        """Removes a device that's been either discovered, paired,
        connected, etc.

        :param path: The D-Bus path to the object
        :type path: string
        """

        self.adapter.RemoveDevice(
            self.bus.get_object(SERVICE_NAME, path))

    def find_device_by_address(self, address):
        """Finds the D-Bus path to a device that contains the
        specified address.

        :param address: The Bluetooth MAC address
        :type address: string
        :return: The path to the D-Bus object or None
        :rtype: string or None
        """

        # Find all connected/paired/discovered devices
        devices = find_objects(
            self.bus,
            SERVICE_NAME,
            DEVICE_INTERFACE)
        for path in devices:
            # Get the device's address and paired status
            device_props = dbus.Interface(
                self.bus.get_object(SERVICE_NAME, path),
                "org.freedesktop.DBus.Properties")
            device_addr = device_props.Get(
                DEVICE_INTERFACE,
                "Address").upper()

            # Check for an address match
            if device_addr != address.upper():
                continue
            return path

        return None
