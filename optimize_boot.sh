#!/bin/sh

# add fastboot
echo "Adding fastboot"
if ! grep -q 'fastboot' /boot/firmware/cmdline.txt; then
  perl -i -pe 's/rootwait/rootwait quiet fastboot nofsck/' /boot/firmware/cmdline.txt
fi

# append config.txt settings
echo "Updating /boot/firmware/config.txt with boot time reductions"
if ! grep -q 'disable_splash=1' /boot/firmware/config.txt; then
  cat >> /boot/firmware/config.txt << 'EOF'
disable_splash=1
boot_delay=0
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
