# Constants
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

printf "\n${RED}Installing System Requirements and Bluetooth Requirements...${NC}\n\n"
# Bluetooth + Sys Reqs
sudo apt install libbluetooth-dev bluez bluez-tools bluez-firmware libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-3.0 -y
