#!/usr/bin/env bash

# Sets up system initialization and builds core userspace services for the initramfs

set -euo pipefail

DIR="$(realpath "$(dirname "$0" )" )"

# some convenience variables if you want to use them.
EUDEV_SRC="$SRC/eudev"
CHRONY_SRC="$SRC/chrony"
DHCPCD_SRC="$SRC/dhcpcd"

#edit inittab script
cat > "$DIST/busybox/etc/inittab" << 'EOF'
echo "+++ inittab started +++" > /dev/console

# BusyBox inittab
::sysinit:/etc/init.d/rcS
ttyS0::respawn:/sbin/getty -L ttyS0 115200 vt100
EOF

#edit init.d script
mkdir -p "$DIST/busybox/etc/init.d"
cat > "$DIST/busybox/etc/init.d/rcS" << 'EOF'
#!/bin/sh
echo "+++ init.d/rcS started +++" > /dev/console

mkdir -p /dev
mount -t devtmpfs devtmpfs /dev

exec 0</dev/console 1>/dev/console 2>/dev/console

echo "Testing: This should now appear in your terminal!"

mknod /dev/console c 5 1
mknod /dev/null c 1 3
chmod 600 /dev/console

# Mount essential kernel filesystems
mkdir -p /proc /sys /run
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t tmpfs tmpfs /run

# Set hostname
echo "raine" > /etc/hostname

# prepare for dhcpcd
mkdir -p "/var/run/dhcpcd"
chown 1000:1000 "/var/run/dhcpcd"
chmod 700 "/var/run/dhcpcd"

#prepare for chrony
mkdir -p /var/run/chrony
mkdir -p /var/lib/chrony
mkdir -p /etc/chrony
mkdir -p /var/log/chrony

#prepare for eudev
mkdir -p /run /run/udev /dev
chown root:root /run /run/udev
chmod 755 /run /run/udev

/usr/sbin/udevd --daemon
echo "+++ starting dhcpcd +++" > /dev/console
/usr/sbin/dhcpcd -b
/usr/sbin/chronyd -f /etc/chrony/chrony.conf &

EOF
chmod +x "$DIST/busybox/etc/init.d/rcS"

cat > "$DIST/busybox/etc/passwd" << 'EOF'
root:x:0:0:root:/root:/bin/sh
dhcpcd:x:1000:1000:dhcpcd:/var/run/dhcpcd:/bin/false
EOF

cat > "$DIST/busybox/etc/shadow" << 'EOF'
root::0:0:99999:7:::
dhcpcd:*:0:0:99999:7:::
EOF

cat > "$DIST/busybox/etc/group" << 'EOF'
root:x:0:
daemon:x:1:
bin:x:2:
sys:x:3:
adm:x:4:
tty:x:5:
disk:x:6:
lp:x:7:
mail:x:8:
kmem:x:9:
cdrom:x:10:
floppy:x:11:
audio:x:12:
dip:x:13:
video:x:14:
plugdev:x:15:
staff:x:16:
games:x:17:
users:x:100:
input:x:101:
netdev:x:102:
ssh:x:103:
docker:x:104:
tape:x:105:
kvm:x:106:
sgx:x:107:
dialout:x:108:
dhcpcd:x:1000:
EOF

mkdir -p "$DIST/build/eudev"
cd "$DIST/build/eudev"
$SRC/eudev/configure \
    --prefix=/usr \
    --disable-shared \
   CC="/dist/busybox/usr/bin/musl-gcc" \
CFLAGS="-nostdinc -I$DIST/busybox/usr/include" \
     LDFLAGS="-static -L$DIST/busybox/usr/lib"
make LDFLAGS="-all-static"
make -j$(nproc)
make DESTDIR="$DIST/busybox" install

mkdir -p "$DIST/build/dhcpcd"
cp -r "$SRC/dhcpcd/." "$DIST/build/dhcpcd/"
cd "$DIST/build/dhcpcd"
./configure \
    --prefix=/usr \
--disable-shared \
    --disable-dbus \
    --disable-ldns \
    CC="/dist/busybox/usr/bin/musl-gcc" \
    CFLAGS="-static -I$DIST/busybox/usr/include" \
    LDFLAGS="-static -L$DIST/busybox/usr/lib"
sed -i '/^${PROG}:/,+1 s/^\(\s*${CC} \)/\1-static /' $DIST/build/dhcpcd/src/Makefile
make clean
make -j$(nproc)
make DESTDIR="$DIST/busybox" install

mkdir -p "$DIST/build/chrony"
cp -r "$SRC/chrony/." "$DIST/build/chrony/"
cd "$DIST/build/chrony"
CC="/dist/busybox/usr/bin/musl-gcc" CFLAGS="-static -I$DIST/busybox/usr/include" LDFLAGS="-static -L$DIST/busybox/usr/lib" ./configure --prefix=/usr --disable-readline --without-nss --without-tomcrypt
make clean
make -j$(nproc)
make DESTDIR="$DIST/busybox" install

mkdir -p "$DIST/busybox/etc/chrony"

cat > $DIST/busybox/etc/chrony/chrony.conf <<EOF
# Use public NTP servers
pool pool.ntp.org iburst

# Where to store the driftfile
driftfile /var/lib/chrony/chrony.drift

# Allow local access if needed
# allow 192.168.0.0/16

# Log measurements statistics
logdir /var/log/chrony

pidfile /var/run/chrony/chronyd.pid
EOF

#create initarmfs image
chmod +x "$DIST/busybox/init"
cd "$DIST/busybox"
find . | cpio -H newc -o | gzip > "$DIST/archive.cpio.gz"
