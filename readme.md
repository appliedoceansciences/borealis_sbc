# Borealis SBC software package

### I/O description

The Linux SBC within the BOREALIS payload has the following interconnects with other components:

- an initial two-way conversation with the BOREALIS Mote via the hardware UART, in which an `sbc_command` nonvolatile configuration variable on the Mote is delivered to and executed by the SBC

- one-way input of `$GPZDA` and other NMEA 0183 strings from the Mote via the hardware UART, intended to be consumed by `gpsd` or equivalent logic on the SBC

- one-way output of COBS-framed packets from the SBC to the Mote in the other direction on the same hardware UART, for handling on the Mote by an implementation of the Bristlemouth `serial_bridge` logic

- one-way input of COBS-framed raw acoustic sample packets via USB CDC from the SCARI acoustic data acquisition system

- wi-fi connectivity, expected to work at useful ranges even when the pressure vessel is closed

### Components

The Borealis SBC software package consists of:

- `cobs_to_shm`: A binary compiled from C code which reads COBS-framed packets from the USB CDC serial device representing the acoustic DAQ, and fans them out to a shared-memory ring buffer (and optionally logs them). This binary comes from its own repository, is not unique to BOREALIS, and will be installed to `/usr/local/bin/`.

- `cobs_to_shm.service`: Invokes the above binary, with BOREALIS-specific logic. Will be installed to `/etc/systemd/system/`

- `handle_sbc_command.py`, `handle_sbc_command.service`: This script runs at boot and has a short two-way communcation with the BOREALIS Mote firmware via the hardware UART, in which the Mote tells the SBC what other services to subsequently start. These files will be installed to `/usr/local/bin/` and `/etc/systemd/system/` respectively.

- `gpsd.service`: This service invokes `gpsd` in such a way that it can concurrently receive NMEA strings from the same UART that customer application code can use to send output to the `serial_bridge` logic on the BOREALIS Mote. This file will be installed to `/etc/systemd/system/`

- `bm_serial.py`: This example code shows how to construct and send a COBS-framed packet to the `serial_bridge` logic on the Borealis Mote, in a cooperative fashion with any other logic doing the same thing on the SBC. This is a rough port of [https://github.com/bristlemouth/bm_serial/blob/develop/circuitpython/bm_serial.py] to generic Python that will run on a Raspberry Pi or macOS using the system Python, with an OS-level exclusive lock around the UART access, such that multiple processes on the Pi can send messages to the Bristlemouth ecosystem via the `serial_bridge` functionality on an attached Mote.

## Setting up Raspberry Pi for headless application hosting

Most of the procedure below is agnostic to the type of Pi, provided it is a 64-bit processor. Some of the items may be specific to the Pi Zero 2W.

### Pre-boot procedure

With a blank microSD card in the slot on your computer, download and run the latest version of the the Raspberry Pi imager tool.

Under "Device", select "Raspberry Pi Zero 2W", and then under "Operating System", select "Raspberry Pi OS (other)" and scroll down to "Raspberry Pi OS Lite (64-bit)".

After selecting storage, click "Next", and then click "Edit settings" in the resulting box. Under "General", set a hostname, create a username and password, and provide wifi credentials. Under "Services", click "Allow public-key authentication only" and paste in the contents of your existing `~/.ssh/id_ed25519.pub` or `~/.ssh/id_rsa.pub`, or accept the automatically populated public key if it has done so. Do *NOT* click "Run ssh-keygen" unless you have verified that neither of those files already exist. Click "Save" and then "Yes".

Write the image to a microSD card, boot the system, and ssh into it after determining its local IP address via any available means.

### Basic setup

After logging in via ssh, get to a root prompt and upgrade the system:

    sudo -i
    apt update && apt -y full-upgrade

Prevent some systemd default behaviour which can interfere with persistent processes run as a regular user:

    sed 's/#RemoveIPC=yes/RemoveIPC=no/' -i /etc/systemd/logind.conf

Disable swap:

    perl -i -pe 's/CONF_SWAPSIZE=512/CONF_SWAPSIZE=0/' /etc/dphys-swapfile

Reduce headless power consumption:

    perl -i -pe 's/^dtoverlay=vc4-kms-v3d/#dtoverlay=vc4-kms-v3d/' /boot/firmware/config.txt
    printf 'core_freq=250\ndisable_splash=1\nboot_delay=0\ndtoverlay=disable-bt\nenable_tvout=0\ndtparam=act_led_trigger=heartbeat\ngpu_mem=16\n\n' >> /boot/firmware/config.txt

Disable Linux serial console on the GPIO UART:

    perl -i -pe 's/console=serial0,115200 //' /boot/firmware/cmdline.txt

Configure sudo to allow `sudo -i` without requiring a password:

    printf '%%sudo ALL=NOPASSWD: /bin/bash\n' > /etc/sudoers.d/010_sudo_dash_i_nopasswd

Reboot the board with `reboot` to apply the above mods, and then log in and use `sudo -i` to get back to a root prompt.

### Adding backup networks

After logging in via ssh, run:

    sudo -i nmtui

Here select `Edit a connection`, then `<Add>`, the `Wi-Fi` and fill out the following information regarding SSID and Security (WPA and WPA2 Personal is most likely the security type dealth with).

In order to select a different network to connect to,
head back to the main menu and select `Activate a connection`.
Here select the connection to activate.

If the main network is not found on the Pi on boot,
networks added in the `Edit a connection` will be used.
