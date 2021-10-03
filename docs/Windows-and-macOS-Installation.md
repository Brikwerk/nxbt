# Windows and macOS Installation

To support the necessary Bluetooth APIs leveraged within NXBT, installation within a Virtual Machine (VM) is necessary. To install on Windows or macOS using a VM, please follow the instructions below.

## Prerequisites

Before continuing, please ensure you have the following:

- A **USB** Bluetooth Adapter
    - Internal Bluetooth adapters are incompatible (generally) with the process that allows a VM to use external resources.
- VirtualBox v6 or above
    - If you don't have this, you can install VirtualBox [here](https://www.virtualbox.org/wiki/Downloads)
- VirtualBox Extension Pack
    - The Extension Pack should be available to download on the [same page as VirtualBox.](https://www.virtualbox.org/wiki/Downloads)
- Vagrant
    - Available to download [here](https://www.vagrantup.com/downloads)
- Python 3

Additionally, please ensure that VBoxManage (a CLI that ships with VirtualBox) is available on your system path. Eg: A help message should be displayed if `VBoxManage` is entered into Terminal (macOS) or Command Prompt (Windows). If you don't see a help message, please add VirtualBox's installation directory to your system path.

## Installation

1. Clone the NXBT repo to a location of your choosing:

    ```bash
    git clone https://github.com/Brikwerk/nxbt
    ```

2. Navigate inside the cloned directory and run the Vagrant setup tool.

    ```bash
    cd nxbt
    python3 vagrant_setup.py
    ```

3. Follow the tool's directions and choose the USB Bluetooth adapter you would like to use with NXBT. Additionally, you'll be able to choose between intalling NXBT from PyPi or from the cloned repository. Installing NXBT from the cloned repository allows for use of development version (as well as editing NXBT itself)

4. Once the Vagrant setup tool is finished, you should see a file called `Vagrantfile` located in the same directory as the setup tool. You should now be able to boot the VM with the following command:

    ```bash
    vagrant up
    ```

5. After the VM has fully completed its setup, you can SSH into the terminal. Please note that your terminal's current working directory must be in the same directory at the Vagrantfile you generated earlier.

    ```bash
    # SSHing into the VM
    vagrant ssh
    ```

6. Unplug the USB Bluetooth adapter from your machine and plug it back in. The allows for VirtualBox to properly claim and forward to the USB into the Vagrant VM.

7. Inside the VirtualBox, check that your Bluetooth Adapter is available with `lsusb`:

    ```bash
    > lsusb
    # Something like the following will be printed
    # if your USB Bluetooth adapter is available:
    Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
    Bus 002 Device 002: ID 0a5c:21e9 Broadcom Corp. BCM20702A0 Bluetooth 4.0
    Bus 002 Device 001: ID 1d6b:0001 Linux Foundation 1.1 root hub
    ```

    Next, use `bluetoothctl` to test if Bluetooth is functional with the adapter:

    ```bash
    > sudo bluetoothctl
    # bluetoothctl should print something like below
    # if the adapter is functional
    Agent registered
    [CHG] Controller XX:XX:XX:XX:XX:XX Pairable: yes
    # You can additionally run the `show` command in
    # bluetoothctl to list your adapters stats as a final check
    > [bluetooth]# show
    Controller XX:XX:XX:XX:XX:XX (public)
        Name: ubuntu2010.localdomain
        ...
    ```

    If you're not able to see your adapter within the VM or the adapter isn't functional, please refer to the troubleshooting section below.

8. If the above checks pass, NXBT should be functional within your VM. You can run NXBT commands as normal while SSHed into the VM:

    ```bash
    # Eg:
    sudo nxbt test
    ```

9. Finally, Vagrant exposes the following other commands to halt the VM and completely destroy it:

    ```bash
    # Stop the VM but don't destroy it
    vagrant halt
    # Completely destroy the VM
    vagrant destroy
    ```

## Troubleshooting

### My USB Bluetooth adapter won't show up inside the VM

First, halt your VM (`vagrant halt`) and unplug your adapter. Next, restart the VM (`vagrant up`) and SSH into it (`vagrant ssh`). Plug the Bluetooth adapter in and check if it's listed with `lsusb`. If the adapter still isn't listed, unplug the adapter again and manually add a USB passthrough with the VirtualBox application. Instructions on this can be found [here](https://help.ubuntu.com/community/VirtualBox/USB) under the "For persistent device connection to VM" section.

### My adapter appears but Bluetooth isn't functional

Typically, restarting the VM resolves the issue. Make sure you unplug the adapter and plug it back in when the VM has fully booted (AKA when it's possible to SSH into it).
