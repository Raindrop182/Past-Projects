#!/usr/bin/env bash

# Creates a bootable disk image with EFI and rootfs partitions

set -euo pipefail

rm -f "$DIST/bootable.img" "$DIST/esp.img" "$DIST/rootfs.img"

truncate -s 190M "$DIST/bootable.img"

sgdisk -Z "$DIST/bootable.img"
sgdisk -n 1:2048:+40M -t 1:ef00 -c 1:"EFI System" "$DIST/bootable.img"
sgdisk -n 2:83968:0   -t 2:8300 -c 2:"RootFS"     "$DIST/bootable.img"

truncate -s 40M "$DIST/esp.img"
mkfs.vfat -F 32 "$DIST/esp.img"
mmd -i "$DIST/esp.img" ::EFI ::EFI/BOOT
mcopy -i "$DIST/esp.img" "$DIST/linuximage" ::EFI/BOOT/BOOTX64.EFI
mcopy -i "$DIST/esp.img" "$DIST/archive.cpio.gz" ::EFI/BOOT/initramfs.cpio.gz

echo "fs0:\EFI\BOOT\BOOTX64.EFI initrd=\EFI\BOOT\initramfs.cpio.gz root=/dev/vda2 console=ttyS0 rw" > "$DIST/startup.nsh"
mcopy -i "$DIST/esp.img" "$DIST/startup.nsh" ::startup.nsh

# Size: 190 - 40 - overhead = ~145M
truncate -s 145M "$DIST/rootfs.img"
mke2fs -F -d "$DIST/busybox" -t ext4 "$DIST/rootfs.img" 145M

dd if="$DIST/esp.img" of="$DIST/bootable.img" bs=1M seek=1 conv=notrunc
dd if="$DIST/rootfs.img" of="$DIST/bootable.img" bs=1M seek=41 conv=notrunc

sgdisk -e "$DIST/bootable.img"

