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

# add fastboot
echo "Adding fastboot"
if ! grep -q 'fastboot' /boot/firmware/cmdline.txt; then
  perl -i -pe 's/rootwait/rootwait quiet fastboot nofsck/' /boot/firmware/cmdline.txt
fi

# append config.txt settings
# guard against double-application
echo "Updating /boot/firmware/config.txt with power savings and boot time reductions"
if ! grep -q 'disable_camera_led=1' /boot/firmware/config.txt; then
  cat >> /boot/firmware/config.txt << 'EOF'
# disable camera module
disable_camera_led=1
# improve boot time
disable_splash=1
boot_delay=0
# disable HDMI
max_framebuffers=1
disable_overscan=1
hdmi_ignore_hotplug=1
hdmi_ignore_edid=0xa5000080
hdmi_blanking=2
display_auto_detect=0
# disable composite video output
enable_tvout=0
# disable bluetooth
dtoverlay=disable-bt
# disable LEDs
dtparam=act_led_trigger=none
dtparam=act_led_activelow=on
dtparam=pwr_led_trigger=none
dtparam=pwr_led_activelow=on
# disable audio
dtparam=audio=off
avoid_warnings=1
# gpu power optimization
gpu_freq=50
gpu_mem=16
EOF
fi

# set cpu governor
echo "Setting CPU governor to low power mode"
if ! grep -q 'GOVERNOR=powersave' /etc/default/cpufrequtils 2>/dev/null; then
  tee -a /etc/default/cpufrequtils << 'EOF'
GOVERNOR=powersave
EOF
fi

# disable services that suck up boot time

echo "---- Disabling services ----"

# cloud init, remove this to enable cloud-init
echo "Disabling cloud-init"
touch /etc/cloud/cloud-init.disabled

# no keyboard/mouse connected
echo "Disabling keyboard/mouse"
systemctl disable keyboard-setup.service
systemctl disable console-setup.service

# swap file services (swap is disabled)
echo "Disabling swap"
systemctl disable rpi-resize-swap-file.service
systemctl disable rpi-setup-loop@var-swap.service
systemctl mask rpi-resize-swap-file.service
systemctl mask rpi-setup-loop@var-swap.service
systemctl disable systemd-zram-setup@zram0.service
systemctl mask systemd-zram-setup@zram0.service

# binary format handler not needed headless
echo "Disabling binary format handling"
systemctl disable systemd-binfmt.service
systemctl mask systemd-binfmt.service
systemctl mask proc-sys-fs-binfmt_misc.mount

# e2fsck reaper, filesystem check cleanup, safe to disable with fastboot
echo "Disabling filesystem check"
systemctl disable e2scrub_reap.service

# pi doesn't use EFI
echo "Disabling EFI"
systemctl mask modprobe@efi_pstore.service
