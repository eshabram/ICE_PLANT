# ICE_PLANT

## Setting Up RPi Zero 2 w
Download Raspberry Pi imager software and burn a Raspberry Pi OS Lite (64 bit) image to your drive. 

When the imager is done, it will automatically eject the sd. Reinsert it and add the `usb-gadget.sh` and `iceplant-gadget.service` located in the `gadget/` dir in this repository to the bootfs directory. If you are on mac, run this from the root of the repo:
```bash
sudo cp gadget/* /Volumes/bootfs/
```
Once completed, you'll have to hook up a screen and keyboard and log into the device to enable a service and edit some files. 

Once logged in, copy the script and service files to their respective locations and enable the service:
```bash
sudo mkdir -p /opt/iceplant
sudo mv /boot/firmware/usb-gadget.sh /opt/iceplant/
sudo chmod +x /opt/iceplant/usb-gadget.sh
sudo mv /boot/firmware/iceplant-gadget.service /etc/systemd/system/
sudo systemctl enable iceplant-gadget.service
```

Run this command to enable console login from serial:
```bash
sudo systemctl enable serial-getty@ttyGS0.service
# and check with this command
sudo systemctl status serial-getty@ttyGS0.service
```

Then open and edit the `/boot/firmware/config.txt` by adding this line at the bottom:
```sh
dtoverlay=dwc2
```

Now open the `/boot/firmware/cmdline.txt` and add this after `rootwait` with spaces. Be careful to not add new lines here because this is a command:
```sh
modules-load=dwc2
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