<h1 align="center">
  <br>
  <img src="https://raw.githubusercontent.com/Brikwerk/nxbt/master/docs/img/nxbt-logo.png" alt="NXBT" width="200">
  <br>
  NXBT
  <br>
</h1>

<h4 align="center">Control your Nintendo Switch through a website, terminal, or macro.</h4>

<div align="center">

  [![Stars](https://img.shields.io/github/stars/brikwerk/nxbt.svg)]() 
  [![GitHub Issues](https://img.shields.io/github/issues/brikwerk/nxbt.svg)](https://github.com/brikwerk/ctqa/issues)
  [![GitHub Pull Requests](https://img.shields.io/github/issues-pr/brikwerk/nxbt.svg)](https://github.com/brikwerk/ctqa/pulls)
  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)

</div>

<p align="center">
  <a href="#key-features">Key Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#troubleshooting">Troubleshooting</a> •
  <a href="#credits">Credits</a> •
  <a href="#license">License</a>
</p>

![screenshot](https://raw.githubusercontent.com/Brikwerk/nxbt/master/docs/img/nxbt-example.png)

## Key Features

- Use your favourite web browser to control a Nintendo Switch with any keyboard or gamepad.
- Use your terminal to control a Nintendo Switch with a keyboard.
- Use a macro from your terminal, browser, or Python script
- Use the NXBT Python API to write programs to control your Nintendo Switch.
- Primitive loop support in macros.
- In-depth command line interface.
- Support for emulating multiple controllers at once.
- Support for fast connection or reconnection to a Nintendo Switch.
- Emulated ontrollers support thread-safe access.

## Installation

### Linux

```bash
sudo pip3 install nxbt
```

**Please Note:** NXBT needs root privileges to toggle the BlueZ Input plugin. If you're not comfortable running this program as root, you can disable the Input plugin manually, and install NXBT as a regular user.

### Windows and macOS

See the installation guide [here.](docs/Windows-and-macOS-Installation.md)

## Getting Started

**Note:** If you installed NXBT as a non-root user, please omit the use of `sudo` from any of the following commands.

### Running the demo

The demo is meant to gauge whether or not NXBT is working. To do so, the demo will create a Pro Controller and run through a small loop of commands.

**NOTE:** If this is your first time connecting to an NXBT emulated controller on the specific host computer, you **MUST** have the "Change Grip/Order Menu" open on your Nintendo Switch. You can see how to navigate to the "Change Grip/Order Menu" [HERE](docs/img/change-grip-order-menu.png).

To start the demo, run the following command in your terminal:

```bash
sudo nxbt demo
```

If all is working correctly, the controller should connect, navigate to the settings, test the stick calibration, and navigate back to the "Change Grip/Order Menu".

## Using the Webapp

The NXBT webapp provides a web interface that allows for quick creation of a Nintendo Switch controller and use of a keyboard or gamepad to control the Nintendo Switch. This lets anyone who can access the website control a Nintendo Switch with their favourite keyboard or gamepad.

The webapp server can be started with the following command:

```bash
sudo nxbt webapp
```

The above command boots NXBT and an accompanying web server that allows for controller creation and use over your web browser.

The webapp itself will be locally accessible at `http://127.0.0.1:8000` or, if you're on the same network as the host computer, http://HOST_COMPUTER_IP:8000. It's also possible to expose your NXBT webapp to the internet, however, you'll need to configure a reverse proxy, which is out of the scope of this readme.

You should see a webpage similar to the following image:

<div align="center">
  <img src="https://raw.githubusercontent.com/Brikwerk/nxbt/master/docs/img/nxbt-webapp-start.png" alt="NXBT Webapp Start Screen" width="600">
</div>

To create and start a Pro Controller, click the Pro controller graphic. If creation/boot is successful, the website will switch to a loading screen. During this time, you should have the Nintendo Switch you wish to connect to powered on and within range of the host computer.

**NOTE:** If this is your first time connecting to your Nintendo Switch with the specific host computer, make sure you're on the "Change Grip/Order Menu". If you're still unable to connect, try running the demo (in the above section) or refer to the troubleshooting documentation.

Once you've successfully connected to the Nintendo Switch, you should see a webpage similar to below:

<div align="center">
  <img src="https://raw.githubusercontent.com/Brikwerk/nxbt/master/docs/img/nxbt-webapp-connected.png" alt="NXBT Webapp Connected Screen" width="600">
</div>

Here, you can change your input method, shutdown or restart the controller, and run an NXBT macro.

A few other functions to note:
- If you exit the webpage, the controller will shutdown.
- Once you've connected over the "Change Grip/Order Menu", NXBT will automatically reconnect. This applies on a per-Bluetooth-adapter basis.
- Most gamepads should be usable over the browser. To get started with a gamepad, click a button and it should show up under the input dropdown list. If it doesn't show up, try another browser. Chrome is the recommended standard as it seems to have the best gamepad support currently (as of September 2020)

## Using the TUI

The TUI (Terminal User Interface) allows for local or remote (SSH/Mosh) terminal sessions to control a Nintendo Switch with a keyboard.

The TUI can be started with:

```bash
sudo nxbt tui
```

**NOTE:** If this is your first time connecting to your Nintendo Switch with the specific host computer, make sure you're on the "Change Grip/Order Menu". If you're still unable to connect, try running the demo (in the above section) or refer to the troubleshooting documentation.

A loading screen should open and, once connected, the main TUI control screen should load. This should look something like below:

<div align="center">
  <img src="https://raw.githubusercontent.com/Brikwerk/nxbt/master/docs/img/nxbt-tui.png" alt="NXBT TUI Connected" width="600">
</div>

There are two types of NXBT TUI sessions:
1. **Remote Mode (pictured above):** When connecting over an SSH (or Mosh) connection, "Remote Mode" is used to compensate for keyup events not being sent over remote terminal sessions. This functionally means that "Remote Mode" is a bit less responsive than "Direct Mode".
2. **Direct Mode:** When running the NXBT TUI directly on the host computer, keyboard key presses are taken directly from any keyboard plugged in.

Once you've successfully connected to a Nintendo Switch over the "Change Grip/Order Menu", you can reconnect quickly to the same Switch with the following command:

```bash
sudo nxbt tui -r
```

A couple other funcionality notes:
- Press 'q' to exit the TUI.
- In Direct Mode, press Escape to toggle input to the Nintendo Switch.
- NXBT looks for SSH and Mosh connections before deciding whether or note Remote Mode should be used. If you use another method for creating a remote terminal instance, NXBT likely won't detect it. Please open an issue if this happens to you!

## Running Macros

NXBT provides three ways to run macros on your Nintendo Switch:

1. The NXBT Webapp (easiest)
2. The CLI
3. The Python API

For the first method, refer to the "Using the Webapp" section for more info.

For info on writing macros, check out the documentation [here](docs/Macros.md).

### Running Macros with the Command Line Interface

To run a simple, inline macro, you can use the following command:

```bash
sudo nxbt macro -c "B 0.1s\n 0.1s"
```

The above command will press the B button for 0.1 seconds and release all buttons for 0.1 seconds. The `-c` flag specifies the commands you would like to run. You'll need to be on the "Change Grip/Order Menu" for the above command to work. If you've already connected to the Switch on the host computer, you can reconnect and run the macro by adding the `-r` or `--reconnect` flag:

```bash
sudo nxbt macro -c "B 0.1s\n 0.1s" -r
```

Since it can be a little cumbersome typing out a large macro in the terminal, the macro command also supports reading from text files instead!

commands.txt file:
```
B 0.1s
0.1s
```

```bash
sudo nxbt macro -c "commands.txt" -r
```

If you want more information on NXBT's CLI arguments:

```bash
sudo nxbt -h
```

### Running Macros with the Python API

Macros are supported with the `macro` function in the Python API. All macros are expected as strings (multiline strings are accepted).

Minimal working example:

```python
import nxbt

macro = """
B 0.1s
0.1s
"""

# Start the NXBT service
nx = nxbt.Nxbt()

# Create a Pro Controller and wait for it to connect
controller_index = nx.create_controller(nxbt.PRO_CONTROLLER)
nx.wait_for_connection(controller_index)

# Run a macro on the Pro Controller
nx.macro(controller_index, macro)
```

The above example uses a blocking macro call, however, multiple macros can be queued (or other actions taken) with the non-blocking syntax. Queued macros are processed in FIFO (First-In-First-Out) order.

```python
# Run a macro on the Pro Controller but don't block.
# In this instance, we record the macro ID so we can keep track of its status later on.
macro_id = nx.macro(controller_index, macro, block=False)

from time import sleep
while macro_id not in nx.state[controller_index]["finished_macros"]:
    print("Macro hasn't finished")
    sleep(1/10)

print("Macro has finished")
```

## Using the API

NXBT provides a Python API for use in Python applications or code.

If you're someone that learns by example, check out the `demo.py` file located at the root of this project.

For a more in-depth look at all the functionality provided by the API, checkout the `nxbt/nxbt.py` file.

For those looking to get started with a few simple examples: Read on!

**Creating a Controller and Waiting for it to Connect**
```python
import nxbt

# Start the NXBT service
nx = nxbt.Nxbt()

# Create a Pro Controller and wait for it to connect
controller_index = nx.create_controller(nxbt.PRO_CONTROLLER)
nx.wait_for_connection(controller_index)

print("Connected")
```

**Pressing a Button**
```python
# Press the B button
# press_buttons defaults to pressing a button for 0.1s and releasing for 0.1s
nx.press_buttons(controller_idx, [nxbt.Buttons.B])

# Pressing the B button for 1.0s instead of 0.1s
nx.press_buttons(controller_idx, [nxbt.Buttons.B], down=1.0)
```

**Tilting a Analog Stick**
```python
# Tilt the right stick fully to the left.
# tilt_stick defaults to tilting the stick for 0.1s and releasing for 0.1s
nx.tilt_stick(controller_idx, Sticks.RIGHT_STICK, -100, 0)

# Tilting the stick for 1.0s instead of 0.1s
nx.tilt_stick(controller_idx, Sticks.RIGHT_STICK, -100, 0, tilted=1.0)
```

**Getting the available Bluetooth adapters**
```python
# This prints the device paths for each available adapter.
# If a controller is in use, an adapter will be removed from this list.
print(nx.get_available_adapters)
```

**Shutting Down a running Controller**
```python
# This frees up the adapter that was in use by this controller
nx.remove_controller(controller_index)
```

**Reconnecting to a Switch**
```python
# Get a list of all previously connected Switches and pass it as a reconnect_address argument
controller_index = nx.create_controller(
    nxbt.PRO_CONTROLLER,
    reconnect_address=nx.get_switch_addresses())
```

**Stopping or Clearing Macros**
```python
# Stops/deletes a single macro from a specified controller
nx.stop_macro(controller_index, macro_id)

# Clears all macros from a given controller
nx.clear_macros(controller_index)

# Clears all macros from every created controller
nx.clear_all_macros()
```

## Troubleshooting

### I get an error when installing the `dbus-python` package

This error can occur due to missing dbus-related libraries on some Linux distributions. To fix this in most cases, `libdbus-glib-1-dev` and `libdbus-1-dev` need to be installed with your system's package manager. For systems using aptitude for package management (Ubuntu, Debian, etc), installation instructions follow:

```bash
sudo apt-get install libdbus-glib-1-dev libdbus-1-dev
```

### My controller disconnects after exiting the "Change Grip/Order" Menu

This can occasionally occur due to timing sensitivities when transitioning off of the "Change Grip/Order" menu. To avoid disconnections when exiting this menu, please only press A (or B) a single time and wait until the menu has fully exited. If a disconnect still occurs, you should be able to reconnect your controller and use NXBT as normal.

### "No Available Adapters"

This means that NXBT wasn't able to find a suitable Bluetooth adapter to use for Nintendo Switch controller emulation. Only one controller can be emulated per adapter on the system, so if you've got one Bluetooth adapter available, you'll only be able to emulate one Nintendo Switch controller. The general causes (and solutions) to the above error follows:

1. **Cause:** All available adapters are currently emulating a controller.
  - **Solution:** End one of the other controller sessions (either through the webapp or command line) or plug in another Bluetooth adapter.
2. **Cause:** No Bluetooth adapters are available to NXBT.
  - **Solution:** Ensure that you've installed the relevant Bluetooth stack for your operating system (BlueZ on Linux) and check that your Bluetooth adapter is visible within to your OS.

### "Address already in use"

This means that another service has already bound itself to the Control and Interrupt ports on the specified Bluetooth adapter. Causes/solutions follow:

1. **Cause:** (Linux specific solution) This is typically the BlueZ input plugin binding itself to the Control/Interrupt ports for your adapter.
  - **Solution:** Either disable the input plugin (you will lose access to Bluetooth keyboards/mice while it is disabled) or install NXBT as root to allow for temporary toggling of the Input plugin.

## Future Plans

1. Allows for rebinding keys within the TUI and webapp
2. Add a touchscreen input option for the webapp to enable input on smartphones
3. Transition the webapp to a more maintainable React build
4. Allow for recording macros from direct input within the webapp
5. Allow for replaying recorded input
6. Write a full testing suite

### Plans that Need More Testing

- Use mouse movement as right stick input

## Issues

- Switching from the slow frequency mode on the "Change Grip/Order" menu to the full input report frequency is still a bit of a frail process. Some game start menus have a frequency of 15Hz but specifically only allow exiting by pressing the A button. The "Change Grip/Order" menu allows for exiting with A, B, or the Home button, however.
- The webapp can sometimes have small amounts of input lag (<8ms).

## Credits

A big thank you goes out to all the contributors at the [dekuNukem/Nintendo_Switch_Reverse_Engineering](https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering) repository! Almost all information pertaining to the innerworkings of the Nintendo Switch Controllers comes from the documentation in that repo. Without it, NXBT wouldn't have been possible.

## License

MIT
