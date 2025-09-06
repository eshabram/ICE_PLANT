#!/bin/bash
set -e
modprobe libcomposite
G=/sys/kernel/config/usb_gadget/iceplant
[ -d "$G" ] || mkdir -p "$G"
cd "$G"

# Spoof as ASIX AX88772 
echo 0x0b95 > idVendor    # ASIX
echo 0x7720 > idProduct   # AX88772 USB Ethernet
echo 0x0200 > bcdUSB

mkdir -p strings/0x409
echo "ICEPLANT-0001" > strings/0x409/serialnumber
echo "Elliot"        > strings/0x409/manufacturer
echo "ICE_PLANT"     > strings/0x409/product

mkdir -p configs/c.1
echo 250 > configs/c.1/MaxPower
mkdir -p configs/c.1/strings/0x409
echo "ECM+ACM" > configs/c.1/strings/0x409/configuration

# Ethernet (usb0) + Serial (ttyGS0)
mkdir -p functions/ecm.usb0
# stable, locally-administered MACs
echo 02:11:22:33:44:55 > functions/ecm.usb0/dev_addr
echo 06:11:22:33:44:55 > functions/ecm.usb0/host_addr
mkdir -p functions/acm.GS0

ln -sf functions/ecm.usb0 configs/c.1/
ln -sf functions/acm.GS0  configs/c.1/

UDC=$(ls /sys/class/udc | head -n1)
echo "$UDC" > UDC

# Pi-side IP ONLY 
ip link set usb0 up || true
ip addr flush dev usb0 || true
ip addr add 192.168.7.2/24 dev usb0 || true
