# Analog Stick Input Information

**Disclaimer:** A chunk of info within this document is sourced from the Switch reverse engineering
effort at [DekuNukem's Repository](https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering).

The below sections contain info on the formulation and derivation of data
pertaining to the Nintendo Switch's controllers. The section on the analog
sticks contains info on encoding/decoding stick X/Y data, deadzones,
maximum range, etc.

If you want to tweak or check out the full stick decode/encode script,
please visit the *scripts/sticks.py* script.

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

```python
# The following code comes from DekuNukem's reverse engineering repo:
# https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering/blob/master/spi_flash_notes.md
# All credit goes to the original author(s)

# The nine stick bytes are labelled stick_cal[0] - stick_cal[8] here
data = [0] * 6
data[0] = (stick_cal[1] << 8) & 0xF00 | stick_cal[0];
data[1] = (stick_cal[2] << 4) | (stick_cal[1] >> 4);
data[2] = (stick_cal[4] << 8) & 0xF00 | stick_cal[3];
data[3] = (stick_cal[5] << 4) | (stick_cal[4] >> 4);
data[4] = (stick_cal[7] << 8) & 0xF00 | stick_cal[6];
data[5] = (stick_cal[8] << 4) | (stick_cal[7] >> 4);

# Using the above data to create right stick data
right_center_x = data[0];
right_center_y = data[1];
right_x_min = rstick_center_x - data[2];
right_x_max = rstick_center_x + data[4];
right_y_min = rstick_center_y - data[3];
right_y_max = rstick_center_y + data[5];

# or left stick data
left_center_x = data[2]
left_center_y = data[3]
left_x_min = left_center_x - data[0]
left_x_max = left_center_x + data[4]
left_y_min = left_center_y - data[1]
left_y_max = left_center_y + data[5]
```

Resulting in the following values for the sticks:

```
Right Stick
~~~~~~~~~~~
Center X = 2070
Center Y = 2013
X Min = 548
X Max = 3484
Y Min = 482
Y Max = 3523

Left Stick
~~~~~~~~~~
Center X = 2159
Center Y = 1916
X Min = 693
X Max = 3676
Y Min = 333
Y Max = 3381
```

Please note that the left stick calibration data is decoded slightly 
different than the right stick calibration data.

With the above calibration data, we can now decode a controller's 
reported stick position:

```python
# Sample Stick Data Conversion:
stick_data = [0xB3, 0x32, 0x6C]
stick_horizontal = stick_data[0] | ((stick_data[1] & 0xF) << 8)
stick_vertical = (stick_data[1] >> 4) | (stick_data[2] << 4)

print("Example Left Stick Data to Ratio Conversion:")
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("Raw X/Y Uint16 Values:", stick_horizontal, stick_vertical)
ratio_x = abs((stick_horizontal - left_center_x)) / (left_x_min - left_center_x)
ratio_y = (stick_vertical - left_center_y) / (left_y_min - left_center_y)
print("Relative X/Y Values", ratio_x, ratio_y)
```

Which results in the ratios:

```
Example Left Stick Data to Ratio Conversion:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Raw X/Y Uint16 Values: 691 1731
Relative X/Y Values -1.0013642564802183 0.11686670878079596
```

We can see from the above data that the stick is being pushed left horizontally with 
very little vertical component.

## Converting Ratio-based Stick Position to a Calibrated Position

Given the stick calibration settings from the previous section,
we can convert a given set of X/Y stick ratios to a calibrated set
of values. This worked example will use the ratios defined before 
(-1.00136 X and 0.116866 Y).

First, we need to convert our given ratios to the numeric range
defined by the calibration settings. Since we're using left stick ratios
for our example, our X values range from 693 - 3676 and our Y values range
from 333 - 3381. The following section of code demonstrates the math
behind this conversion.

```python
print("Example Left Stick Ratio to Data Conversion:")
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
if ratio_x < 0:
  data_x_converted = (abs(ratio_x) * (left_x_min - left_center_x) + left_center_x)
else:
  data_x_converted = (abs(ratio_x) * (left_x_max - left_center_x) + left_center_x)
data_x_converted = int(round(data_x_converted))

if ratio_y < 0:
  data_y_converted = (abs(ratio_y) * (left_y_min - left_center_y) + left_center_y)
else:
  data_y_converted = (abs(ratio_y) * (left_y_max - left_center_y) + left_center_y)
data_y_converted = int(round(data_y_converted))

print("X/Y Converted Values:", data_x_converted, data_y_converted)
```

Which results in:

```
Example Left Stick Ratio to Data Conversion:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
X/Y Converted Values: 691 1731
```

Since the stick's X/Y position is broken up into 3 bytes in the standard input
report, we need to split these uint16 values into 3 uint8 values. The following
code accomplishes this split:

```python
# Converting the two X/Y uint16 values to 3 uint8 Little Endian values
converted_values = [
    # Get the last two hex digits
    hex(data_x_converted & 0xFF),
    # Combine the last digit of the Y uint16 and the first digit
    # of the X uint16
    hex(((data_y_converted & 0xF) << 4) + (data_x_converted >> 8)),
    # Get the first two digits of the Y uint16
    hex(data_y_converted >> 4)]
print("Uint8 Converted Values:", converted_values)
```

Which results bytes ready to be sent to the Switch:

```
Uint8 Converted Values: ['0xb3', '0x32', '0x6c']
```
