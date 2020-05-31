from ctypes import c_uint16

# Left Stick Calibration
stick_cal = [0xBA, 0xF5, 0x62, 0x6F, 0xC8, 0x77, 0xED, 0x95, 0x5B]
# Right Stick Calibration
stick_cal = [0x16, 0xD8, 0x7D, 0xF2, 0xB5, 0x5F, 0x86, 0x65, 0x5E]
data = [0] * 6

# The nine stick bytes are labelled stick_cal[0] - stick_cal[8] here
data[0] = (stick_cal[1] << 8) & 0xF00 | stick_cal[0]
data[1] = (stick_cal[2] << 4) | (stick_cal[1] >> 4)
data[2] = (stick_cal[4] << 8) & 0xF00 | stick_cal[3]
data[3] = (stick_cal[5] << 4) | (stick_cal[4] >> 4)
data[4] = (stick_cal[7] << 8) & 0xF00 | stick_cal[6]
data[5] = (stick_cal[8] << 4) | (stick_cal[7] >> 4)

# These values used as such in, for example, a right stick
center_x = data[0]
center_y = data[1]
x_min = c_uint16(center_x - data[2])
x_max = c_uint16(center_x + data[4])
y_min = c_uint16(center_y - data[3])
y_max = c_uint16(center_y + data[5])
center_x = c_uint16(data[0])
center_y = c_uint16(data[1])

print("Center X and Y", center_x, center_y)
print("X Min/Max", x_min, x_max)
print("Y Min/Max", y_min, y_max)
