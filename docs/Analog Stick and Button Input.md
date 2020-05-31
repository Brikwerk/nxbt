# Analog Stick and Button Input Information

**Disclaimer:** The info within this document is sourced from the Switch reverse engineering
effort at [DekuNukem's Repository](https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering).

The below sections contain info on the formulation and derivation of data
pertaining to the Nintendo Switch's controllers. The section on the analog
sticks contains info on encoding/decoding stick X/Y data, deadzones,
maximum range, etc. The button info section contains info on how each
button's state is communicated.

## Analog Stick Information

Information on a controller's analog sticks is stored in three primary
locations (user calibration excluded):

| Obtained From | Byte # | Data Type | Info |
| --- | --- | --- | --- | --- |
| Standard Input Report | 6-11 | 2 uint16 | Contains X/Y Data of Analog Sticks<sup>1</sup>
| SPI Flash Read (Offset 0x6080) | 13-30 | 12 uint16 LE | Dead Zone, Range ratio |
| SPI Flash Read (Offset 0x603D) | 7-24 | 12 uint16 LE | X/Y Min/Max and Centers |

<sup>1</sup> This data is relative, meaning that stick calibration data 
*must* be used to encode/decode X and Y positions.

## Decoding a Stick's Position

**Note:** The following configuration values are used within Nxbt.

First, we use the data obtained from the 0x603D SPI flash read to
derive the right/left stick calibration parameters.

Sample data output by Nxbt:
```
Payload:    0xA1 0x21 0x2B 0x90 0x00 0x00 0x00 0x74 0x58 0x75 0x4B 0x68 0x7C 0x90 
               0    1    2    3    4    5    6    7    8    9   10   11   12   13
Subcommand: 0x90 0x10 0x3D 0x60 0x00 0x00 0x19 0xBA 0xF5 0x62 0x6F 0xC8 0x77 0xED 
              14   15   16   17   18   19   20   21   22   23   24   25   26   27
            0x95 0x5B 0x16 0xD8 0x7D 0xF2 0xB5 0x5F 0x86 0x65 0x5E 0xFF 0x82 0x82 
              28   29   30   31   32   33   34   35
            0x82 0x0F 0x0F 0x0F 0x00 0x00 0x00 0x00 
```

Which gives us:

```
Left Stick:  0xBA 0xF5 0x62 0x6F 0xC8 0x77 0xED 0x95 0x5B
Right Stick: 0x16 0xD8 0x7D 0xF2 0xB5 0x5F 0x86 0x65 0x5E 
```

Using the following equations, we can decode these values into meaningful ones.
Each stick's data is treated as an array of byte values for the equations.

```
# The nine stick bytes are labelled stick_cal[0] - stick_cal[8] here
uint16_t data[6]
data[0] = (stick_cal[1] << 8) & 0xF00 | stick_cal[0];
data[1] = (stick_cal[2] << 4) | (stick_cal[1] >> 4);
data[2] = (stick_cal[4] << 8) & 0xF00 | stick_cal[3];
data[3] = (stick_cal[5] << 4) | (stick_cal[4] >> 4);
data[4] = (stick_cal[7] << 8) & 0xF00 | stick_cal[6];
data[5] = (stick_cal[8] << 4) | (stick_cal[7] >> 4);

# These values used as such in, for example, a right stick
uint16_t rstick_center_x = data[0];
uint16_t rstick_center_y = data[1];
uint16_t rstick_x_min = rstick_center_x - data[2];
uint16_t rstick_x_max = rstick_center_x + data[4];
uint16_t rstick_y_min = rstick_center_y - data[3];
uint16_t rstick_y_max = rstick_center_y + data[5];
```

Resulting in the following values for the sticks:

```
Left Stick
~~~~~~~~~~
Center X =
Center Y = 
X Min = 
X Max = 
Y Min = 
Y Max = 

Right Stick
~~~~~~~~~~~
Center X =
Center Y = 
X Min = 
X Max = 
Y Min = 
Y Max = 
```
