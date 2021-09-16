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

5. After the VM has fully completed its setup, you can SSH into the terminal and start NXBT:

    ```bash
    # SSHing into the VM
    vagrant ssh
    # Starting NXBT in the VM
    sudo nxbt test
    ```

6. Vagrant exposes the following other commands to halt the VM and completely destroy it:

    ```bash
    # Stop the VM but don't destroy it
    vagrant halt
    # Completely destroy the VM
    vagrant destroy
    ```
