#!/usr/bin/env bash

#$SRC contains source code
#$ROOTFS points to $DIST/busybox which is where everything will be installed and root filesystem created

#this script sets up the root filesystem, installs kernel headers, musl, and busybox

set -euo pipefail

DIR="$(realpath "$(dirname "$0" )" )"

#set up required directories
mkdir -p $ROOTFS/usr/include $ROOTFS/usr/lib $ROOTFS/usr/bin $ROOTFS/etc $ROOTFS/lib $ROOTFS/sbin

#install kernel headers
mkdir -p $DIST/build/kernel
make -C "$SRC/kernel" O="$DIST/build/kernel" INSTALL_HDR_PATH="$ROOTFS/usr" headers_install -j$(nproc)

#install musl
mkdir -p $DIST/build/musl
cd "$DIST/build/musl"
$SRC/musl/configure --prefix="$ROOTFS/usr" \
    --syslibdir="$ROOTFS/lib"
make -C "$DIST/build/musl" -j$(nproc)
make -C "$DIST/build/musl" DESTDIR="" install

#install busybox
mkdir -p $DIST/build/busybox
make -C "$SRC/busybox" O="$DIST/build/busybox" defconfig
sed -i 's/CONFIG_VI=y/# CONFIG_VI is not set/' $DIST/build/busybox/.config #disable unneeded applet
make -C "$SRC/busybox" O="$DIST/build/busybox" \
     CONFIG_PREFIX="$ROOTFS" \
CFLAGS="-nostdinc -I$ROOTFS/usr/include" \
     LDFLAGS="-static -L$ROOTFS/usr/lib" \
  -j$(nproc) install

#edit init script
cat > "$DIST/busybox/init" << 'EOF'
#!/bin/sh
mkdir -p /run /sys /proc /dev /tmp /mnt
mount -t sysfs sysfs /sys
mount -t tmpfs tmpfs /run
mount -t tmpfs tmpfs /tmp
mount -t proc proc /proc
mount -t devtmpfs devtmpfs /dev

mount /dev/vda2 /mnt
mount --bind /dev /mnt/dev
mount -t proc proc /mnt/proc
mount -t sysfs sys /mnt/sys
mount -t tmpfs tmp /mnt/run

#exec switch_root /mnt /sbin/init
exec switch_root /mnt /sbin/init || { 
    echo "switch_root failed, dropping to shell..." >/dev/console
    exec /bin/sh </dev/console >/dev/console 2>/dev/console
}
EOF

#create initarmfs image for testing
chmod +x "$ROOTFS/init"
cd "$ROOTFS"
find . | cpio -H newc -o | gzip > "$DIST/archive.cpio.gz"
