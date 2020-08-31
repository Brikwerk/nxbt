# NXBT

Control a Nintendo Switch Locally or Remotely

---

This is meant to serve as an all-in-one solution to controlling a Nintendo Switch from a variety of devices.

Functionality is currently under development.

## Prerequisites

- A Bluetooth adapter with a Bluetooth version greater than or equal to 4.0
- A computer running Linux
- A Nintendo Switch

## Getting Started

TBA

## TODO

- Rebinding of keys within the TUI and webapp
- Incorporate React and components library into the webapp
- Allow for recording macros from direct input from within the webapp
- Allow for playing recorded direct input macros from the API
- Write a full testing suite

## Issues

- Switching from the slow frequency mode on the "Change Grip/Order" menu to the full input report
    frequency is still a bit of a frail process. Some game start menus have a frequency of 15Hz
    but specifically only allow exiting by pressing the A button. The "Change Grip/Order" menu
    allows for exiting with A, B, or the Home button, however.
