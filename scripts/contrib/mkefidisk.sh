#!/bin/sh
#
# Copyright (c) 2012, Intel Corporation.
# All rights reserved.
#
# This program is free software;  you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY;  without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
# the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program;  if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#

<<<<<<< HEAD
LANG=C

=======
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
#
# Defaults
#
# 20 Mb for the boot partition
BOOT_SIZE=20
# 5% for swap
SWAP_RATIO=5

<<<<<<< HEAD
usage() {
=======
function usage() {
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
	echo "Usage: $(basename $0) DEVICE HDDIMG TARGET_DEVICE"
	echo "       DEVICE: The device to write the image to, e.g. /dev/sdh"
	echo "       HDDIMG: The hddimg file to generate the efi disk from"
	echo "       TARGET_DEVICE: The device the target will boot from, e.g.  /dev/mmcblk0"
}

<<<<<<< HEAD
image_details() {
=======
function image_details() {
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
	IMG=$1
	echo "Image details"
	echo "============="
	echo "    image: $(stat --printf '%N\n' $IMG)"
	echo "     size: $(stat -L --printf '%s bytes\n' $IMG)"
	echo " modified: $(stat -L --printf '%y\n' $IMG)"
	echo "     type: $(file -L -b $IMG)"
	echo ""
}

<<<<<<< HEAD
device_details() {
=======
function device_details() {
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
	DEV=$1
	BLOCK_SIZE=512

	echo "Device details"
	echo "=============="
	echo "  device: $DEVICE"
	if [ -f "/sys/class/block/$DEV/device/vendor" ]; then
		echo "  vendor: $(cat /sys/class/block/$DEV/device/vendor)"
	else
		echo "  vendor: UNKOWN"
	fi
	if [ -f "/sys/class/block/$DEV/device/model" ]; then
		echo "   model: $(cat /sys/class/block/$DEV/device/model)"
	else
		echo "   model: UNKNOWN"
	fi
	if [ -f "/sys/class/block/$DEV/size" ]; then
<<<<<<< HEAD
		echo "    size: $(($(cat /sys/class/block/$DEV/size) * $BLOCK_SIZE)) bytes"
=======
		echo "    size: $[$(cat /sys/class/block/$DEV/size)*BLOCK_SIZE] bytes"
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
	else
		echo "    size: UNKNOWN"
	fi
	echo ""
}

<<<<<<< HEAD
unmount_device() {
	grep -q $DEVICE /proc/mounts
	if [ $? -eq 0 ]; then
		echo -n "$DEVICE listed in /proc/mounts, attempting to unmount..."
		umount $DEVICE* 2>/dev/null
		grep -q $DEVICE /proc/mounts
		if [ $? -eq 0 ]; then
			echo "FAILED"
			exit 1
		fi
		echo "OK"
	fi
}

=======
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc

#
# Parse and validate arguments
#
if [ $# -ne 3 ]; then
	usage
	exit 1
fi

DEVICE=$1
HDDIMG=$2
TARGET_DEVICE=$3

if [ ! -w "$DEVICE" ]; then
	echo "ERROR: Device $DEVICE does not exist or is not writable"
	usage
	exit 1
fi

if [ ! -e "$HDDIMG" ]; then
	echo "ERROR: HDDIMG $HDDIMG does not exist"
	usage
	exit 1
fi


#
# Check if any $DEVICE partitions are mounted
#
<<<<<<< HEAD
unmount_device
=======
grep -q $DEVICE /proc/mounts
if [ $? -eq 0 ]; then
	echo "ERROR: $DEVICE partitions mounted:"
	grep $DEVICE /proc/mounts | cut -f 1 -d " "
	echo "Unmount the partitions listed and try again."
	exit 1
fi
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc


#
# Confirm device with user
#
image_details $HDDIMG
device_details $(basename $DEVICE)
echo -n "Prepare EFI image on $DEVICE [y/N]? "
read RESPONSE
if [ "$RESPONSE" != "y" ]; then
	echo "Image creation aborted"
	exit 0
fi


#
# Partition $DEVICE
#
<<<<<<< HEAD
DEVICE_SIZE=$(parted $DEVICE unit mb print | grep ^Disk | cut -d" " -f 3 | sed -e "s/MB//")
=======
DEVICE_SIZE=$(parted $DEVICE unit mb print | grep Disk | cut -d" " -f 3 | sed -e "s/MB//")
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
SWAP_SIZE=$((DEVICE_SIZE*SWAP_RATIO/100))
ROOTFS_SIZE=$((DEVICE_SIZE-BOOT_SIZE-SWAP_SIZE))
ROOTFS_START=$((BOOT_SIZE))
ROOTFS_END=$((ROOTFS_START+ROOTFS_SIZE))
SWAP_START=$((ROOTFS_END))

<<<<<<< HEAD
# MMC devices use a partition prefix character 'p'
=======
# MMC devices are special in a couple of ways
# 1) they use a partition prefix character 'p'
# 2) they are detected asynchronously (need ROOTWAIT)
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
PART_PREFIX=""
if [ ! "${DEVICE#/dev/mmcblk}" = "${DEVICE}" ]; then
	PART_PREFIX="p"
fi
BOOTFS=$DEVICE${PART_PREFIX}1
ROOTFS=$DEVICE${PART_PREFIX}2
SWAP=$DEVICE${PART_PREFIX}3

<<<<<<< HEAD
TARGET_PART_PREFIX=""
if [ ! "${TARGET_DEVICE#/dev/mmcblk}" = "${TARGET_DEVICE}" ]; then
	TARGET_PART_PREFIX="p"
=======
ROOTWAIT=""
TARGET_PART_PREFIX=""
if [ ! "${TARGET_DEVICE#/dev/mmcblk}" = "${TARGET_DEVICE}" ]; then
	TARGET_PART_PREFIX="p"
	ROOTWAIT="rootwait"
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
fi
TARGET_ROOTFS=$TARGET_DEVICE${TARGET_PART_PREFIX}2
TARGET_SWAP=$TARGET_DEVICE${TARGET_PART_PREFIX}3

echo "*****************"
echo "Boot partition size:   $BOOT_SIZE MB ($BOOTFS)"
echo "ROOTFS partition size: $ROOTFS_SIZE MB ($ROOTFS)"
echo "Swap partition size:   $SWAP_SIZE MB ($SWAP)"
echo "*****************"
<<<<<<< HEAD

echo "Deleting partition table on $DEVICE ..."
dd if=/dev/zero of=$DEVICE bs=512 count=2

# Use MSDOS by default as GPT cannot be reliably distributed in disk image form
# as it requires the backup table to be on the last block of the device, which
# of course varies from device to device.
echo "Creating new partition table (MSDOS) on $DEVICE ..."
parted $DEVICE mklabel msdos
=======
echo "Deleting partition table on $DEVICE ..."
dd if=/dev/zero of=$DEVICE bs=512 count=2

echo "Creating new partition table (GPT) on $DEVICE ..."
parted $DEVICE mklabel gpt
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc

echo "Creating boot partition on $BOOTFS"
parted $DEVICE mkpart primary 0% $BOOT_SIZE

<<<<<<< HEAD
echo "Enabling boot flag on $BOOTFS"
parted $DEVICE set 1 boot on

=======
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
echo "Creating ROOTFS partition on $ROOTFS"
parted $DEVICE mkpart primary $ROOTFS_START $ROOTFS_END

echo "Creating swap partition on $SWAP"
parted $DEVICE mkpart primary $SWAP_START 100%

parted $DEVICE print


#
<<<<<<< HEAD
# Check if any $DEVICE partitions are mounted after partitioning
#
unmount_device


#
=======
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc
# Format $DEVICE partitions
#
echo ""
echo "Formatting $BOOTFS as vfat..."
<<<<<<< HEAD
mkfs.vfat $BOOTFS -n "efi"

echo "Formatting $ROOTFS as ext3..."
mkfs.ext3 $ROOTFS -L "root"
=======
mkfs.vfat $BOOTFS

echo "Formatting $ROOTFS as ext3..."
mkfs.ext3 $ROOTFS
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc

echo "Formatting swap partition...($SWAP)"
mkswap $SWAP


#
# Installing to $DEVICE
#
echo ""
echo "Mounting images and device in preparation for installation..."
TMPDIR=$(mktemp -d mkefidisk-XXX)
if [ $? -ne 0 ]; then
	echo "ERROR: Failed to create temporary mounting directory."
	exit 1
fi
HDDIMG_MNT=$TMPDIR/hddimg
HDDIMG_ROOTFS_MNT=$TMPDIR/hddimg_rootfs
ROOTFS_MNT=$TMPDIR/rootfs
BOOTFS_MNT=$TMPDIR/bootfs
mkdir $HDDIMG_MNT
mkdir $HDDIMG_ROOTFS_MNT
mkdir $ROOTFS_MNT
mkdir $BOOTFS_MNT

mount -o loop $HDDIMG $HDDIMG_MNT
mount -o loop $HDDIMG_MNT/rootfs.img $HDDIMG_ROOTFS_MNT
mount $ROOTFS $ROOTFS_MNT
mount $BOOTFS $BOOTFS_MNT

echo "Copying ROOTFS files..."
cp -a $HDDIMG_ROOTFS_MNT/* $ROOTFS_MNT

echo "$TARGET_SWAP     swap             swap       defaults              0 0" >> $ROOTFS_MNT/etc/fstab

# We dont want udev to mount our root device while we're booting...
if [ -d $ROOTFS_MNT/etc/udev/ ] ; then
	echo "$TARGET_DEVICE" >> $ROOTFS_MNT/etc/udev/mount.blacklist
fi

umount $ROOTFS_MNT
umount $HDDIMG_ROOTFS_MNT

echo "Preparing boot partition..."
EFIDIR="$BOOTFS_MNT/EFI/BOOT"
mkdir -p $EFIDIR
GRUBCFG="$EFIDIR/grub.cfg"

cp $HDDIMG_MNT/vmlinuz $BOOTFS_MNT
# Copy the efi loader and config (booti*.efi and grub.cfg)
cp $HDDIMG_MNT/EFI/BOOT/* $EFIDIR

# Update grub config for the installed image
# Delete the install entry
sed -i "/menuentry 'install'/,/^}/d" $GRUBCFG
# Delete the initrd lines
sed -i "/initrd /d" $GRUBCFG
# Delete any LABEL= strings
sed -i "s/ LABEL=[^ ]*/ /" $GRUBCFG
<<<<<<< HEAD
# Remove any existing root= kernel parameters and:
# o Add a root= parameter with the target rootfs
# o Specify ro so fsck can be run during boot
# o Specify rootwait in case the target media is an asyncronous block device
#   such as MMC or USB disks
# o Specify "quiet" to minimize boot time when using slow serial consoles
sed -i "s@ root=[^ ]*@ @" $GRUBCFG
sed -i "s@vmlinuz @vmlinuz root=$TARGET_ROOTFS ro rootwait quiet @" $GRUBCFG
=======
# Replace the ramdisk root with the install device and include other options
sed -i "s@ root=[^ ]*@ root=$TARGET_ROOTFS rw $ROOTWAIT quiet@" $GRUBCFG

# Provide a startup.nsh script for older firmware with non-standard boot
# directories and paths.
echo "bootia32.efi" > $BOOTFS_MNT/startup.nsh
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc

umount $BOOTFS_MNT
umount $HDDIMG_MNT
rm -rf $TMPDIR
sync

echo "Installation complete."
