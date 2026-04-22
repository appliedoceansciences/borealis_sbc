#!/bin/sh

# disable graphics
if ! grep -q '#dtoverlay=vc4-kms-v3d' /boot/firmware/config.txt; then
  perl -i -pe 's/^dtoverlay=vc4-kms-v3d/#dtoverlay=vc4-kms-v3d/' /boot/firmware/config.txt
fi

# disable swap (zram)
echo "Disabling swap"
if ! grep -q 'systemd.zram=0' /boot/firmware/cmdline.txt; then
  perl -i -pe 's/rootwait/rootwait systemd.zram=0/' /boot/firmware/cmdline.txt
fi

#disable serial console
echo "Disabling serial console"
if grep -q 'console=serial0,115200' /boot/firmware/config.txt; then
  perl -i -pe 's/console=serial0,115200 //' /boot/firmware/cmdline.txt
fi

# append config.txt settings
echo "Updating /boot/firmware/config.txt with power savings"
if ! grep -q 'dtoverlay=disable-bt' /boot/firmware/config.txt; then
  cat >> /boot/firmware/config.txt << 'EOF'
dtoverlay=disable-bt
enable_tvout=0
dtparam=act_led_trigger=heartbeat
gpu_mem=16
arm_freq=600
core_freq=48
h264_freq=48
isp_freq=48
v3d_freq=48
EOF
fi

# set cpu governor
echo "Setting CPU governor to low power mode"
if ! grep -q 'GOVERNOR=powersave' /etc/default/cpufrequtils 2>/dev/null; then
  tee -a /etc/default/cpufrequtils << 'EOF'
GOVERNOR=powersave
EOF
fi
