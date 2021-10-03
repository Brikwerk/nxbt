from enum import Enum
import os
import logging

import dbus


class ControllerTypes(Enum):
    """Controller type enumerations for initializing the controller server.
    """

    JOYCON_L = 1
    JOYCON_R = 2
    PRO_CONTROLLER = 3


class Controller():

    GAMEPAD_CLASS = "0x002508"
    SDP_UUID = "00001000-0000-1000-8000-00805f9b34fb"
    SDP_RECORD_PATH = "/nxbt/controller"
    ALIASES = {
        ControllerTypes.JOYCON_L: "Joy-Con (L)",
        ControllerTypes.JOYCON_R: "Joy-Con (R)",
        ControllerTypes.PRO_CONTROLLER: "Pro Controller"
    }

    def __init__(self, bluetooth, controller_type):

        self.bt = bluetooth
        self.logger = logging.getLogger('nxbt')

        if controller_type not in self.ALIASES.keys():
            raise ValueError("Unknown controller type specified")
        self.alias = self.ALIASES[controller_type]

    def setup(self):
        """Configures the specified Bluetooth device as the
        specified controller.
        """

        # Setting up Bluetooth adapter options
        self.bt.set_powered(True)
        self.bt.set_pairable(True)
        self.bt.set_pairable_timeout(0)
        self.bt.set_discoverable_timeout(180)

        self.bt.set_alias(self.alias)

        # Adding the SDP record
        sdp_record_path = os.path.join(
            os.path.dirname(__file__), "sdp", "switch-controller.xml")
        sdp_record = None
        with open(sdp_record_path, "r") as f:
            sdp_record = f.read()

        opts = {
            "ServiceRecord": sdp_record,
            "Role": "server",
            "RequireAuthentication": False,
            "RequireAuthorization": False,
            "AutoConnect": True
        }
        # If the profile has already been registered,
        # catch the error and continue
        try:
            self.bt.register_profile(self.SDP_RECORD_PATH, self.SDP_UUID, opts)
        except dbus.exceptions.DBusException as e:
            self.logger.debug(e)
