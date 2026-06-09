# Borealis SBC software package

### I/O description

The Linux SBC within the BOREALIS payload has the following interconnects with other components:

- an initial two-way conversation with the BOREALIS Mote via Bristlemouth traffic the hardware UART, in which a timestamp and an `sbc_command` nonvolatile configuration variable on the Mote is delivered to and executed by the SBC

- one-way input of `$GPZDA` and other NMEA 0183 strings from the Mote via Bristlemouth traffic over the hardware UART, intended to be consumed by `gpsd` or equivalent logic on the SBC

- one-way output of COBS-framed packets from the SBC to the Mote in the other direction on via Bristlemouth traffic over the same hardware UART, for handling on the Mote by an implementation of the Bristlemouth `bm_sbc` logic

- other one- or two-way Bristlemouth traffic via the hardware UARt

- one-way input of COBS-framed raw acoustic sample packets via USB CDC from the SCARI acoustic data acquisition system

- wi-fi connectivity, expected to work at useful ranges even when the pressure vessel is closed

### Components

The Borealis SBC software package consists of:

- `cobs_to_shm`: A binary compiled from C code which reads COBS-framed packets from the USB CDC serial device representing the acoustic DAQ, and fans them out to a shared-memory ring buffer (and optionally logs them). This binary comes from its own repository, is not unique to BOREALIS, and will be installed to `/usr/local/bin/`.

- `cobs_to_shm.service`: Invokes the above binary, with BOREALIS-specific logic. Will be installed to `/etc/systemd/system/`

- `gpsd.service`: This service invokes `gpsd` in such a way that it can concurrently receive NMEA strings from the same UART that customer application code can use to send output to the `serial_bridge` logic on the BOREALIS Mote. This file will be installed to `/etc/systemd/system/`.

- `bm_sbc_gateway.service`: This service manages the UART link with the Mote as a Bristlemouth port. This gateway service is a C++ application in [https://github.com/bristlemouth/bm_sbc] compiled for the Raspberry Pi and functions as a full-fledged Bristlemouth node visible in the network topology to all other nodes as a neighbor of the Mote. At install time, this service is enabled to always run at boot. This file will be installed to `/etc/systemd/system/`.

## Setting up Raspberry Pi for headless application hosting

Most of the procedure below is agnostic to the type of Pi, provided it is a 64-bit processor. Some of the items may be specific to the Pi Zero 2W.

### Pre-boot procedure

With a blank microSD card in the slot on your computer, download and run the latest version of the the Raspberry Pi imager tool.

Under "Device", select "Raspberry Pi Zero 2W", and then under "Operating System", select "Raspberry Pi OS (other)" and scroll down to "Raspberry Pi OS Lite (64-bit)".

After selecting storage, click "Next", and then click "Edit settings" in the resulting box. Under "General", set a hostname, create a username and password, and provide wifi credentials. Under "Services", click "Allow public-key authentication only" and paste in the contents of your existing `~/.ssh/id_ed25519.pub` or `~/.ssh/id_rsa.pub`, or accept the automatically populated public key if it has done so. Do *NOT* click "Run ssh-keygen" unless you have verified that neither of those files already exist. Click "Save" and then "Yes".

Write the image to a microSD card, boot the system, and ssh into it after determining its local IP address via any available means.

### Adding backup networks

After logging in via ssh, run:

    sudo -i nmtui

Here select `Edit a connection`, then `<Add>`, them `Wi-Fi` and fill out the following information regarding SSID and Security (WPA and WPA2 Personal is most likely the security type).

In order to select a different network to connect to,
head back to the main menu and select `Activate a connection`.
Here select the connection to activate.

If the main network is not found on the Pi on boot,
networks added in the `Edit a connection` will be used.

## Project-specific installation

Prior to running the included `install.sh`, you should have cloned this repository, `apt install`ed git, and run `git submodule update --init --recursive` in this repository. Then, as root (obtainable with `sudo -i` after running the above instructions), run the included `./install.sh` from within this directory.
Reboot the board with `reboot` to apply the above installation.
