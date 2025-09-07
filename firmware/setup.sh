#!/bin/bash

# move the files into their locations and create service
sudo mkdir -p /opt/iceplant
sudo mv /boot/firmware/usb-gadget.sh /boot/firmware/dhcpd.py /opt/iceplant/
sudo mv /boot/firmware/iceplant-gadget.service /boot/firmware/iceplant-dhcp.service /boot/firmware/iceplant.service /etc/systemd/system/
sudo mv /boot/firmware/ucdavis_eduroam.pem /etc/ssl/certs/

sudo chmod +x /opt/iceplant/usb-gadget.sh
sudo chmod +x /opt/iceplant/dhcpd.py

sudo systemctl enable iceplant-gadget.service
# sudo systemctl enable iceplant-dhcp.service

# enable console login through serial
sudo systemctl enable serial-getty@ttyGS0.service

# enable iceplant
sudo systemctl enable iceplant

