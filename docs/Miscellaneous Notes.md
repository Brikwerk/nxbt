# Miscellaneous Notes

This is a compilation of quirks, tidbits, and other info that pertain to
this project.

## Crashing a Switch with Malformed Packets

After successfully connecting to a Nintendo Switch (either through
reconnection or connection on the "Change Grip/Order" menu), simply
send blank packets for about 2 to 3 seconds. The Switch will throw up
an error screen and force a system restart.

Refer to the "crash_switch.py" script in the "scripts" folder for an
implementation and more details.

## Requirements for pairing with the Switch

- Controller SDP record. They all share the same one (generally), so a only a single record is needed to emulate all three controllers
- The Bluetooth alias "Joy-Con (L)", "Joy-Con (R)", or "Pro Controller"

**Note:** Setting the device's major and minor class is *not* required
to get the Switch to connect. Only the alias and SDP record are required.

### Weird Tibit:

If you wanted to be a little lazy during emulation, the Bluetooth
alias isn't used to define the identity of the controller within
the Switch. You only need to set the alias as one of the three
mentioned above. The Switch only checks for identity in the device
inquiry input report packet.

Eg: You could get away with emulating a Joy-Con (L) while having the
Bluetooth alias set to "Pro Controller".

## Pro Controller Grip Colours

At the time of writing, grip colours are being read by the Switch, however,
they aren't being used to display the controller graphic. Eg: If the left
and right grip colours are set to white and the controller body is set to
black, the grip colours will be black. This is likely because Nintendo hasn't
produced any official Pro Controllers that feature a unique grip and body
colour.

Currently, grip colours are hardcoded for the official, black Pro Controller.
The black pro controller reports all white (or blank) grip colours, however,
the Switch displays a slightly lighter grey when the icon is displayed. Any
emulated controller can produce this grip colour if the body colour is set
to #323232, the button colour set to #FFFFFF and the grip colours are set to
#FFFFFF.

In the future, Nintendo may produce more Pro Controller colours, however,
at this point in time, setting the grip colour is not possible.

## (Re)Connecting after the "Change Grip/Order" menu is opened

Opening the "Change Grip/Order" menu (either through the Controllers menu or
within a game) causes the Switch to cancel all Bluetooth connections to
controllers and force a reconnection. There are a couple of little quirks
and gotchas to be aware of that I've run into:

1. Controllers must run through a complete reconnection after the Grip/Order
    menu is opened. A controller cannot revive or reconnect on its previous
    connection. The Switch must reach out to the controller and the reconnection
    process must be run through again. The Grip/Order menu, however, does not
    cancel previous Bluetooth pairings. This rule only applies while the Grip/Order
    menu is open. Once the menu is closed, controllers can attempt to revive a
    connection, however, they still might have to run through the reconnection 
    process.

2. After reconnection on the Grip/Order menu, **emulated** controllers 
    **must** press the L + R buttons before attempting regular input.
    This is a bit of a strange condition that I'm still grappling with. In some situations,
    a non-emulated controller can get away with not pressing the L + R buttons
    and jump straight into regular input. I'm not 100% sure how they're able to, 
    however, I think it's an okay enough compromise to hardcode an L + R press
    after a reconnection.

3. All communication must be done at 15Hz. Once the controller is off of the
    Change Grip/Order menu, communication speeds up to 60Hz (Joy-Con) or 120Hz
    (Pro Controller). If communication is not done at 15Hz, input can be severely
    delayed or outright ignored.

## Waking the Switch Over Bluetooth

From a preliminary investigation, it seems that the Pro/Joy Controllers use
Broadcom Fast Connect (or something similar) to wake the Switch over Bluetooth.
Since this falls under a hardware-specific function, it's not possible to
emulate this unless a given piece of hardware matches this feature.

In the future, a potential strategy to wake the Switch might be to connect
a given device running nxbt over the dock's USB port and implement
Wake-On-USB instead.
