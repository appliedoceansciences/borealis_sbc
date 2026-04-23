#!/bin/sh
set -e

apt update

apt install socat gpsd chrony build-essential cmake python3-serial python3-numpy

# installing gpsd enables this, we don't want it
systemctl disable --now gpsd.socket

# compile and install cobs_to_shm
make -C cobs_to_shm
mv cobs_to_shm/cobs_to_shm /usr/local/bin/
make -C cobs_to_shm clean

# compile and install bm_sbc_gateway
cmake -S bm_sbc --preset gateway
cmake --build bm_sbc/build/gateway --parallel
cmake --install bm_sbc/build/gateway
mkdir -p /etc/bm_sbc/gateway
if [ ! -e /etc/bm_sbc/gateway/gateway.toml ]; then
    NODE_ID=$(od -An -N8 -tx1 /dev/urandom | tr -d ' \n')
    sed "s/@NODE_ID@/$NODE_ID/" gateway.toml > /etc/bm_sbc/gateway/gateway.toml
fi
echo "d /run/bm_sbc 0755 root root -" > /usr/lib/tmpfiles.d/bm_sbc.conf
systemd-tmpfiles --create /usr/lib/tmpfiles.d/bm_sbc.conf

cp borealis_default.sh /usr/local/bin/

cp *.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable bm_sbc_gateway

if ! grep SHM /etc/chrony/chrony.conf > /dev/null; then
    printf 'refclock SHM 0 offset 0.0 delay 0.2\nrefclock SHM 1 offset 0.0 delay 0.0\n' >> /etc/chrony/chrony.conf
fi
