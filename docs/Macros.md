# NXBT Macros

## Writing an NXBT Macro

Each NXBT macro line is composed of the buttons/sticks being set and the amount of time they are set for. A simple macro follows:

```
B 0.1s
0.1s
```

The above macro is the B button being pressed for 0.1s and no controls being set for 0.1s. This is effectively a single B button press.

A slightly more complicated example follows:

```
A B 0.5s
B 0.1s
0.1s
```

This new macro, first, has both the A and the B button being pressed for 0.5s. Next, the A button is released and the B button continues to be held for an additional 0.1s. Finally, no controls are set for 0.1s.

The above macros deal with only button-based input. A stick input example follows:

```
L_STICK@-100+000 0.75s
1.0s
```

Above, we're setting the left analog stick to 100% in the left horizontal direction. To explain, analog stick positions are composed of two values: and X position and Y position. You can think of both as positions on a traditional X/Y plane, with X being the horizontal component and Y being the vertical component. An X/Y of 0/0 means that the analog stick is in a neutral position (no input), while an X/Y position of 0/100 means our stick is tilted 100% up.

<div align="center">
  <img src="img/pro-controller-stick-axis.jpg" width="300">
</div>

To be clear, the first numeric argument after L_STICK@ is the X value and the second is the Y value. Eg: An X value of 50 and a Y Value of 25 on the right stick would be `R_STICK@+050+025`.

As such, a neutral stick position is as follows:

```
L_STICK@+000+000 0.75s
1.0s
```

### Loops

A simple for-loop can be used to repeat a macro block a specified number of times. The below example loops through an indented macro block 100 times.

```
LOOP 100
    B 0.1s
    0.1s
```

Nested loops are also supported.

```
LOOP 100
    B 0.1s
    0.1s
    # Nested loop
    LOOP 5
        A 0.1s
        0.1s
```

Note, a macro line starting with `#` is ignored.

## Macro Control Values

| Macro Value | Control Name |
--- | ---
Y | Y Button
X | X Button
B | B Button
A | A Button
JCL_SR | Left Joy-Con SR
JCL_SL | Left Joy-Con SL
R | Upper Right Shoulder Trigger
ZR | Lower Right Shoulder Trigger
MINUS | Minus Button
PLUS | Plus Button
R_STICK_PRESS | Right Stick Press
L_STICK_PRESS | Left Stick Press
HOME | Home Button
CAPTURE | Capture Button
DPAD_DOWN | Down Button on the DPad
DPAD_UP | Up Button on the DPad
DPAD_RIGHT | Right Button on the DPad
DPAD_LEFT | Left Button on the DPad
JCR_SR | Right Joy-Con SR
JCR_SL | Right Joy-Con SL
L | Upper Left Shoulder Trigger
ZL | Lower Left Should Trigger
