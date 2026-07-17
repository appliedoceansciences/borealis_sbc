#!/bin/sh
set -e

apt update

# perform full upgrade to obtain latest kernel
apt full-upgrade -y

apt install socat gpsd chrony build-essential cmake python3-serial python3-numpy picotool

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

cp borealis_default.sh /usr/local/bin/

install -m 0755 wifi_restore.sh /usr/local/bin/wifi_restore.sh
cp *.service /etc/systemd/system/
systemctl enable bm_sbc_gateway
systemctl enable wifi_restore

# fence all services onto cores 1+, reserving core 0 for the gateway
NCPU=$(nproc)
if [ "$NCPU" -gt 1 ]; then
    if [ "$NCPU" -gt 2 ]; then OTHERS="1-$((NCPU - 1))"; else OTHERS=1; fi
    mkdir -p /etc/systemd/system.conf.d
    printf '[Manager]\nCPUAffinity=%s\n' "$OTHERS" \
        > /etc/systemd/system.conf.d/10-cpuset.conf
fi

# add threadirqs to force handling of UART interrupts on core 0
echo "Adding threadirqs"
if ! grep -q 'threadirqs' /boot/firmware/cmdline.txt; then
  perl -i -pe 's/rootwait/rootwait threadirqs/' /boot/firmware/cmdline.txt
fi

# add service to pin UART interrupts to core 0
install -m 0755 pin_uart_irq_thread.sh /usr/local/bin/pin_uart_irq_thread.sh


systemctl daemon-reload

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
