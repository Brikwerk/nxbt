# Miscellaneous Notes

This is a compilation of quirks, tidbits, and other info that pertain to
this project.

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
