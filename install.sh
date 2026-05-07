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
GATEWAY_BUILD=bm_sbc/build/gateway
GATEWAY_CONF_DIR=/etc/bm_sbc/gateway
TMPFILES_CONF=/usr/lib/tmpfiles.d/bm_sbc.conf
cmake -S bm_sbc --preset gateway
cmake --build "$GATEWAY_BUILD" --parallel
cmake --install "$GATEWAY_BUILD"
mkdir -p "$GATEWAY_CONF_DIR"
if [ ! -e "$GATEWAY_CONF_DIR/gateway.toml" ]; then
    NODE_ID=$(od -An -N8 -tx1 /dev/urandom | tr -d ' \n')
    sed "s/@NODE_ID@/$NODE_ID/" gateway.toml > "$GATEWAY_CONF_DIR/gateway.toml"
fi
install -m 0644 bm_sbc/deploy/logrotate.d/bm_sbc     /etc/logrotate.d/bm_sbc
install -m 0644 bm_sbc/deploy/tmpfiles.d/bm_sbc.conf "$TMPFILES_CONF"
systemd-tmpfiles --create "$TMPFILES_CONF"

cp borealis_default.sh /usr/local/bin/

cp *.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable bm_sbc_gateway

if ! grep SHM /etc/chrony/chrony.conf > /dev/null; then
    printf 'refclock SHM 0 offset 0.0 delay 0.2\nrefclock SHM 1 offset 0.0 delay 0.0\n' >> /etc/chrony/chrony.conf
fi
