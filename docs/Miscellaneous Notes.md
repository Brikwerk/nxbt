# Miscellaneous Notes

This is a compilation of quirks, tidbits, and other info that pertain to
this project.

## Requirements for pairing with the Switch

- Controller SDP record. They all share the same one (generally), so a only a single record is needed to emulate all three controllers
- The Bluetooth alias "Joy-Con (L)", "Joy-Con (R)", or "Pro Controller"
- The Bluetooth Gamepad HID Class

### Weird Tibit:

If you wanted to be a little lazy during emulation, the Bluetooth
alias isn't used to define the identity of the controller within
the Switch. You only need to set the alias as one of the three
mentioned above. The Switch only checks for identity in the device
inquiry input report packet.

Eg: You could get away with emulating a Joy-Con (L) while having the
Bluetooth alias set to "Pro Controller".
