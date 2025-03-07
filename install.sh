#!/bin/sh
set -e

apt update

apt install socat gpsd chrony build-essential python3-serial

# installing gpsd enables this, we don't want it
systemctl disable --now gpsd.socket

# compile and install cobs_to_shm
make -C cobs_to_shm
mv cobs_to_shm/cobs_to_shm /usr/local/bin/
make -C cobs_to_shm clean

cp handle_sbc_command.py /usr/local/bin/

cp *.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable handle_sbc_command

if ! grep SHM /etc/chrony/chrony.conf > /dev/null; then
    printf 'refclock SHM 0 offset 0.0 delay 0.2\nrefclock SHM 1 offset 0.0 delay 0.0\n' >> /etc/chrony/chrony.conf
fi
