# Left Stick Calibration
stick_cal_left = [0xBA, 0xF5, 0x62, 0x6F, 0xC8, 0x77, 0xED, 0x95, 0x5B]
# Right Stick Calibration
stick_cal_right = [0x16, 0xD8, 0x7D, 0xF2, 0xB5, 0x5F, 0x86, 0x65, 0x5E]
data_left = [0] * 6
data_right = [0] * 6

# Left stick uint16 conversion
data_left[0] = (stick_cal_left[1] << 8) & 0xF00 | stick_cal_left[0]
data_left[1] = (stick_cal_left[2] << 4) | (stick_cal_left[1] >> 4)
data_left[2] = (stick_cal_left[4] << 8) & 0xF00 | stick_cal_left[3]
data_left[3] = (stick_cal_left[5] << 4) | (stick_cal_left[4] >> 4)
data_left[4] = (stick_cal_left[7] << 8) & 0xF00 | stick_cal_left[6]
data_left[5] = (stick_cal_left[8] << 4) | (stick_cal_left[7] >> 4)

# Right stick uint16 conversion
data_right[0] = (stick_cal_right[1] << 8) & 0xF00 | stick_cal_right[0]
data_right[1] = (stick_cal_right[2] << 4) | (stick_cal_right[1] >> 4)
data_right[2] = (stick_cal_right[4] << 8) & 0xF00 | stick_cal_right[3]
data_right[3] = (stick_cal_right[5] << 4) | (stick_cal_right[4] >> 4)
data_right[4] = (stick_cal_right[7] << 8) & 0xF00 | stick_cal_right[6]
data_right[5] = (stick_cal_right[8] << 4) | (stick_cal_right[7] >> 4)

# Left Stick Decode
left_center_x = data_left[2]
left_center_y = data_left[3]
left_x_min = (left_center_x - data_left[0]) - left_center_x
left_x_max = (left_center_x + data_left[4]) - left_center_x
left_y_min = (left_center_y - data_left[1]) - left_center_y
left_y_max = (left_center_y + data_left[5]) - left_center_y

print("Left Stick Values:")
print("~~~~~~~~~~~~~~~~~~")
print("Left Center X and Y:", left_center_x, left_center_y)
print("Left X Min/Max:     ", left_x_min, "", left_x_max)
print("Left Y Min/Max:     ", left_y_min, "", left_y_max)

# Right Stick Decode
right_center_x = data_right[0]
right_center_y = data_right[1]
right_x_min = (right_center_x - data_right[2]) - right_center_x
right_x_max = (right_center_x + data_right[4]) - right_center_x
right_y_min = (right_center_y - data_right[3]) - right_center_y
right_y_max = (right_center_y + data_right[5]) - right_center_y

print("\nRight Stick Values:")
print("~~~~~~~~~~~~~~~~~~~")
print("Right Center X and Y:", right_center_x, right_center_y)
print("Right X Min/Max:     ", right_x_min, "", right_x_max)
print("Right Y Min/Max:     ", right_y_min, "", right_y_max)

# Sample Stick Data Conversion:
stick_data = [0xB3, 0x32, 0x6C]
stick_horizontal = stick_data[0] | ((stick_data[1] & 0xF) << 8)
stick_vertical = (stick_data[1] >> 4) | (stick_data[2] << 4)

print("\nExample Left Stick Data to Ratio Conversion:")
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("Raw X/Y Uint16 Values:", stick_horizontal, stick_vertical)
ratio_x = abs((stick_horizontal - left_center_x)) / (left_x_min - left_center_x)
ratio_y = (stick_vertical - left_center_y) / (left_y_min - left_center_y)
print("Relative X/Y Values", ratio_x, ratio_y)

print("\nExample Left Stick Ratio to Data Conversion:")
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
if ratio_x < 0:
    data_x_converted = (
        abs(ratio_x) * (left_x_min - left_center_x) + left_center_x)
else:
    data_x_converted = (
        abs(ratio_x) * (left_x_max - left_center_x) + left_center_x)
data_x_converted = int(round(data_x_converted))

if ratio_y < 0:
    data_y_converted = (
        abs(ratio_y) * (left_y_min - left_center_y) + left_center_y)
else:
    data_y_converted = (
        abs(ratio_y) * (left_y_max - left_center_y) + left_center_y)
data_y_converted = int(round(data_y_converted))
print("X/Y Converted Values:", data_x_converted, data_y_converted)

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
