#!/bin/sh
set -e

apt update

# perform full upgrade to obtain latest kernel
apt full-upgrade -y

apt install socat gpsd chrony build-essential cmake python3-serial python3-numpy python3-cbor2 picotool

# installing gpsd enables this, we don't want it
systemctl disable --now gpsd.socket

git submodule update --init --recursive

# compile and install cobs_to_shm
make -C cobs_to_shm
make -C cobs_to_shm install
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

# copy over default stub runner
STUB_DIR=/etc/stub_runner
SBC_GATEWAY_DIR="$STUB_DIR"/bm_sbc_gateway
mkdir -p "$STUB_DIR"
mkdir -p "$SBC_GATEWAY_DIR"
install -m 0755 replay_stub.py "$STUB_DIR"
install -m 0755 cobs_to_shm/shared_memory_ringbuffer_reader.py "$STUB_DIR"
install -m 0755 cobs_to_shm/parse_acoustic_packets.py "$STUB_DIR"
install -m 0755 bm_sbc/clients/python/bm_sbc_gateway/__init__.py "$SBC_GATEWAY_DIR"

cp borealis_default.sh /usr/local/bin/

install -m 0755 wifi_restore.sh /usr/local/bin/wifi_restore.sh
cp *.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable bm_sbc_gateway
systemctl enable wifi_restore

cp chrony.conf /etc/chrony/chrony.conf

# prevent some systemd default behaviour which can interfere with persistent processes run as a regular user
sed 's/^#*RemoveIPC=.*/RemoveIPC=no/' -i /etc/systemd/logind.conf

# configure sudo to allow `sudo -i` without requiring a password:
printf '%%sudo ALL=NOPASSWD: /bin/bash\n' > /etc/sudoers.d/010_sudo_dash_i_nopasswd

# disable UART serial console
perl -i -pe 's/console=serial0,115200 //' /boot/firmware/cmdline.txt

# reduce power and boot time
./optimize_power.sh
./optimize_boot.sh

# set wifi backup
systemctl start wifi_restore
