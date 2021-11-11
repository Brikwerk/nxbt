import re
from shutil import which
import subprocess
import os


def find_line_items(identifier, input_string):
    pattern = re.compile(fr"(?<={re.escape(identifier)}: ).*.")
    matches = pattern.findall(input_string)
    matches = list(map(str.strip, matches))
    return matches

def get_usb_devices():
    usb_string = subprocess.check_output(['VBoxManage', 'list', 'usbhost'])
    usb_string = usb_string.decode("utf-8").replace('\r', '')

    usb_devices = usb_string.split("\n\n")
    devices = []
    for device in usb_devices:
        productid = find_line_items("ProductId", device)
        vendorid = find_line_items("VendorId", device)
        manufacturer = find_line_items("Manufacturer", device)
        product = find_line_items("Product", device)

        if (len(productid) < 1 or len(vendorid) < 1 or 
                len(manufacturer) < 1 or len(product) < 1):
            continue

        productid = productid[0]
        vendorid = vendorid[0]
        manufacturer = manufacturer[0]
        product = product[0]

        if len(productid) != 13 or len(vendorid) != 13:
            continue
        
        devices.append({
            'product': product,
            'manufacturer': manufacturer,
            'productid': productid[8:12],
            'vendorid': vendorid[8:12]
        })
    
    return devices

def is_cli(cli_string):
    return which(cli_string) is not None

def check_cli(name, cli_string, msg=None):
    print(name, end="")
    if is_cli(cli_string):
        print(" [OK]")
    else:
        print(" [ERROR]")
        print(f" -> {name} wasn't found on your system")
        if msg is not None:
            print(msg)
        exit(1)

GH_SHELL_CONFIG = """cd /vagrant
    pip3 install -e ."""
PYPI_SHELL_CONFIG = """pip3 install nxbt"""

if __name__ == "__main__":
    print("Checking for the required utilities...")

    vg_msg = ("    Please ensure that Vagrant is installed and available on\n"
              "    your system path.")
    check_cli("Vagrant", "vagrant", msg=vg_msg)

    vb_msg = ("    VBoxManage (part of the VirtualBox CLI) wasn't found\n"
              "    on your system path. Please ensure that VirtualBox is\n"
              "    installed and VBoxManage is on your system path.")
    check_cli("VirtualBox", "VBoxManage", msg=vb_msg)
    print("")

    print("---")
    print("Welcome to the nxbt-vagrant setup.")
    print("As part of the first step in this process, you will "
          "select the USB Bluetooth adapter that will be used with NXBT.")
    print("Please ensure that your adapter is plugged into this computer.")
    print("---")
    input("Press the enter key to continue.")
    print("")

    print("USB Devices:")
    print("---")
    devices = get_usb_devices()
    for i, device in enumerate(devices):
        print(f"{i:3}. {device['product']} ({device['manufacturer']})")
    print()

    # Choose a USB Bluetooth adapter
    invalid_choice = True
    while invalid_choice:
        usb_choice = input(
            f"Please choose your Bluetooth USB Adapter from the above list [0-{len(devices)-1}]: ")
        if usb_choice.isdigit() and int(usb_choice) < len(devices):
            invalid_choice = False
        else:
            print(f"Invalid choice. Please choose a number from 0 to {len(devices)-1}.")
    adapter_info = devices[int(usb_choice)]
    print("")

    # Choose how to install NXBT (PyPi or Github)
    invalid_choice = True
    while invalid_choice:
        install_choice = input(
            "Would you like to install NXBT from (1) PyPi or (2) install from local files? (1/2) ")
        if install_choice in ['1', '2']:
            invalid_choice = False
        else:
            print("Invalid choice. Please choose PyPi (1) or Github clone/install (2)")
    print("")

    print("Configuring...")
    with open("template_vagrantfile", "r") as f:
        vagrantfile = f.read()

    vb_usb_filter = f"""vb.customize ["usbfilter", "add", "0",
        "--target", :id,
        "--name", "{adapter_info['product']} ({adapter_info['manufacturer']})",
        "--product", "{adapter_info['product']}",
        "--manufacturer", "{adapter_info['manufacturer']}",
        "--productid", "{adapter_info['productid']}",
        "--vendorid", "{adapter_info['vendorid']}",]"""
    vagrantfile = vagrantfile.replace("{{USB_FILTER}}", vb_usb_filter)
    if install_choice == '1':
        vagrantfile = vagrantfile.replace("{{SHELL_CONFIG}}", PYPI_SHELL_CONFIG)
    else:
        vagrantfile = vagrantfile.replace("{{SHELL_CONFIG}}", GH_SHELL_CONFIG)

    with open("Vagrantfile", "w") as f:
        f.write(vagrantfile)
    print("Done!")
    print("")

    print("You can now start the NXBT Vagrant Box with 'vagrant up'.")
    print("After booting up, the Vagrant Box can be access with 'vagrant ssh'.")
