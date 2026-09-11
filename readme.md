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

## Setting up Raspberry Pi

Most of the procedure below is agnostic to the type of Pi, provided it is a 64-bit processor. Some of the items may be specific to the Pi Zero 2W.

### Pre-boot procedure

With a blank microSD card in the slot on your computer, download and run the latest version of the the Raspberry Pi imager tool.

On the "Device" tab, select "Raspberry Pi Zero 2W", then "Raspberry Pi OS (other)", then "Raspberry Pi OS Lite (64-bit)" for the operating system image.

On the "Storage" tab, select the SD card reader. If it is marked read-only, ensure that your SD to microSD adapter does not have the read-only slider slid.

On the "Customization" screen, for hostname, type "borealis".

On the "Localisation" screen, choose Washington DC as the capital city, GMT as the time zone, and "us" as the keyboard layout.

On the "User" screen, use "borealis" as the username and password.

On the "Wi-Fi" screen, use "borealis" as the SSID and password.

On the "SSH authentication" screen, make sure "use password authentication" is selected.

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

Log in as the `borealis` user and run the following commands:

    sudo apt install git
    git clone --depth 1 --recurse-submodules https://github.com/appliedoceansciences/borealis_sbc
    cd borealis_sbc
    sudo ./install.sh
    sudo reboot
