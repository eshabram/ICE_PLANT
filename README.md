# ICE_PLANT

## Setting Up RPi Zero 2 w
Download Raspberry Pi imager software and burn a Raspberry Pi OS Lite (64 bit) image to your drive. 

Once completed, you'll have to hook up a screen and keyboard and log into the device to enable a service and edit some files. 

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
modules-load=dwc2,g_serial
```

Now shut the system down and plug into the computer. Windows users can simply locate the COM in a serial terminal app of their choice.

#### Mac Users
If you are on mac, you can search for it like this:
```bash
ls /dev/cu.* /dev/tty.*
```

You should see something like `/dev/cu.usbmodem1101`. It is best to use the `cu.` version. Using `screen`, run this command to open a serial shell:
```zsh
screen /dev/cu.usbmodem1101 115200
```