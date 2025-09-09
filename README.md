# ICE_PLANT
ICE_PLANT is a remote monitoring and data aquisition device designed to work with the Philips Series 50 fetal monitoring machine, sending data back to UC Davis [LEPS](http://lepsucd.com/). It functions as a dongle that can be remotely accessed while on an enterprise network. 

## Setting Up RPi Zero 2 w
Download Raspberry Pi imager software and burn a Raspberry Pi OS Lite (64 bit) image to your drive. 

When the imager is done, it will automatically eject the sd. Reinsert it and add the `usb-gadget.sh` and `iceplant-gadget.service` located in the `firmware/` dir in this repository to the bootfs directory. If you are on mac, run this from the root of the repo:
```bash
cp firmware/* /Volumes/bootfs/
```

Once completed, you'll have to hook up a screen and keyboard and log into the device to enable a service and edit some files. 

Once logged in, run this script to setup the service and serial console login:
```bash
sudo chmod +x /boot/firmware/setup.sh
sudo /boot/firmware/setup.sh
```
The service should be enabled but not running. It will start automatically on reboot after you edit some files

Next, open and edit the `/boot/firmware/config.txt` by adding this line at the bottom:
```sh
dtoverlay=dwc2
enable_uart=1
```

Now open the `/boot/firmware/cmdline.txt` and add this after `rootwait` with spaces. Be careful to not add new lines here because this is a command:
```sh
modules-load=dwc2
```
and to enable serial0 communication for our rs232 adapter, remove from the beginning of the file:
```sh
console=serial0,115200
```


Now shut the system down and plug into the computer. Windows users can simply locate the COM in a serial terminal app of their choice.

#### Mac Users
If you are on mac, you can search for it like this:
```bash
ls /dev/cu.* /dev/tty.*
```

You should see something like `/dev/cu.usbmodemICEPLANT_00013`. It is best to use the `cu.` version with `screen`. Using `screen`, run this command to open a serial shell:
```zsh
screen /dev/cu.usbmodemICEPLANT_00013 115200
```

or install minicom:
```bash
sudo minicom -D /dev/tty.usbmodemICEPLANT_00013 -b 115200
```

Lastly, on you mac find the respective interface (something like en8 or 9 maybe) and run this:
```bash
sudo ifconfig en9 inet 192.168.7.1 netmask 255.255.255.0 up
```

NOTE: You may also have to change the order of service in network settings on mac. It might steal your connection and cause your internet connection to fail.

CRITICAL! Turn off you VPN!

## Setup WPA Wifi Connection:
On the university network, WPA authentication is used for connecting to WiFi. That means signing on is tricky, and we'll need to provide our own `wpa_supplicant-wlan0.conf` file. If your system is up and running, then a template for one should have been copied over to the `/boot/firmware/` dir. mv it to the correct location and edit the file like this:
```bash
sudo cp /boot/firmware/wpa_supplicant-wlan0.conf /etc/wpa_supplicant/
sudo nano /etc/wpa_supplicant-wlan0.conf
```
Now you will need to add the SSID (networks name) and your credentials for the network. 

There is a cert pointed to at the bottom of the conf that was copied in earlier from the `setup.sh` script. that contains the keys UC Davis eduroam network, so if another network is going to be used, then a pem will need to be acquired for that network, and the conf should be carefully edited to reflect the method of authentication. The hospital, for example, may not use WPA2 auth as the university does, and the process may be very different. 

Once you have correctly configured the `wpa_supplicant-wlan0.conf`, you can run these commands to enable and start the service:
```bash
sudo systemctl enable wpa_supplicant@wlan0
sudo systemctl start wpa_supplicant@wlan0
```

Open `raspi-config` and got to Localisation options -> L4 WLAN Count... and set your country. Otherwise, rfkill be soft block the wpa supplicant configuration. 

If the status shows good on the service running, then run this to ask for an ip on wlan0:
```bash
sudo dhclient wlan0
ip addr show wlan0
```

To make sure that dhcp gets an IP for wlan0 automatical create this file:
```bash
sudo nano /etc/systemd/network/10-wlan0.network
```

and add this:
```bash
[Match]
Name=wlan0

[Network]
DHCP=yes
```

and run these: 
```bash
sudo systemctl enable systemd-networkd
sudo systemctl restart systemd-networkd
sudo reboot
```

## Dependencies:
Once the board has network connection, run this:
```sh
sudo apt update
sudo apt install python3-serial
```

## Unlink Tailscale:
```bash
sudo systemctl stop tailscaled
sudo tailscale logout
sudo rm -rf /var/lib/tailscale/*
```