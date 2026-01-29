#!/usr/bin/env bash

# Configures and builds a bootable Linux kernel with an embedded initramfs

set -euo pipefail

DIR="$(realpath "$(dirname "$0" )" )"

# some convenience variables
KERNEL_SRC="$SRC/kernel"

BUILD_DIR="$DIST/build/kernel"
mkdir -p "$BUILD_DIR"

make -C "$SRC/kernel" O="$BUILD_DIR" x86_64_defconfig
cd "$BUILD_DIR"

$SRC/kernel/scripts/config --disable MODULES
$SRC/kernel/scripts/config --enable EFI
$SRC/kernel/scripts/config --enable EFI_STUB
$SRC/kernel/scripts/config --set-str INITRAMFS_SOURCE "$DIST/archive.cpio.gz"
$SRC/kernel/scripts/config --set-str CMDLINE "console=ttyS0"
$SRC/kernel/scripts/config --enable CMDLINE_BOOL
$SRC/kernel/scripts/config --set-str DEFAULT_HOSTNAME "raine-6S913"
$SRC/kernel/scripts/config --enable VIRTIO
$SRC/kernel/scripts/config --enable VIRTIO_PCI
$SRC/kernel/scripts/config --enable VIRTIO_NET
$SRC/kernel/scripts/config --enable SERIAL_8250_CONSOLE
$SRC/kernel/scripts/config --enable SERIAL_8250

make O="$BUILD_DIR" olddefconfig

make -C "$SRC/kernel" O="$BUILD_DIR" -j$(nproc) bzImage

cp "$BUILD_DIR/arch/x86/boot/bzImage" "$DIST/linuximage"
