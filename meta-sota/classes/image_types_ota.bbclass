inherit image_types

# Boot filesystem size in MiB
# OSTree updates may require some space on boot file system for
# boot scripts, kernel and initramfs images
#
BOOTFS_EXTRA_SIZE ?= "512"
export BOOTFS_EXTRA_SIZE

IMAGE_TYPES += " otaimg"
IMAGE_DEPENDS_ota = "e2fsprogs-native \
                     virtual/bootloader \
		     virtual/kernel \
		     parted-native \
                     ${INITRD_IMAGE}"

build_bootfs () {
	KERNEL_FILE=${DEPLOY_DIR_IMAGE}/${KERNEL_IMAGETYPE} 
	KERNEL_SIZE=`du -Lbs ${KERNEL_FILE} | cut -f 1`

	RAMDISK_FILE=${DEPLOY_DIR_IMAGE}/${INITRD_IMAGE}-${MACHINE}.cpio.gz 
	RAMDISK_SIZE=`du -Lbs ${RAMDISK_FILE} | cut -f 1`

	EXTRA_BYTES=$(expr $BOOTFS_EXTRA_SIZE \* 1024 \* 1024)

	TOTAL_SIZE=$(expr ${KERNEL_SIZE} \+ ${RAMDISK_SIZE} \+ ${EXTRA_BYTES})
	TOTAL_BLOCKS=$(expr 1 \+ $TOTAL_SIZE / 1024)

	dd if=/dev/zero of=$1 bs=1024 count=${TOTAL_BLOCKS}
	BOOTTMP=$(mktemp -d mkotaboot-XXX) 
	cp ${DEPLOY_DIR_IMAGE}/${KERNEL_IMAGETYPE} ${BOOTTMP}
	cp ${DEPLOY_DIR_IMAGE}/${INITRD_IMAGE}-${MACHINE}.cpio.gz ${BOOTTMP}
	mkfs.ext4 $1 -d ${BOOTTMP}
	rm -rf $BOOTTMP
}

IMAGE_CMD_otaimg () {
	BOOTIMG=${DEPLOY_DIR_IMAGE}/${IMAGE_NAME}.otaboot.ext4
	rm -f $BOOTIMG
	build_bootfs $BOOTIMG

	# ext4 image should be already here because of IMAGE_TYPEDEP_otaimg
	ROOTIMG=${DEPLOY_DIR_IMAGE}/${IMAGE_NAME}.rootfs.ext4

	BOOTFSBLOCKS=`du -bks ${BOOTIMG} | cut -f 1`

	ROOTFSBLOCKS=`du -bks ${ROOTIMG} | cut -f 1`
	TOTALSIZE=`expr $BOOTFSBLOCKS \+ $ROOTFSBLOCKS`
	END1=`expr $BOOTFSBLOCKS \* 1024`
	END2=`expr $END1 + 512`
	END3=`expr \( $ROOTFSBLOCKS \* 1024 \) + $END1`

	FULLIMG=${DEPLOY_DIR_IMAGE}/${IMAGE_NAME}.otaimg
	rm -rf ${FULLIMG}

	dd if=/dev/zero of=${FULLIMG} bs=1024 seek=${TOTALSIZE} count=1
	parted ${FULLIMG} mklabel msdos 
	parted ${FULLIMG} mkpart primary ext4 0 ${END1}B
	parted ${FULLIMG} unit B mkpart primary ext4 ${END2}B ${END3}B

	OFFSET=`expr $END2 / 512`

	dd if=${BOOTIMG} of=${FULLIMG} conv=notrunc seek=1 bs=512
	dd if=${ROOTIMG} of=${FULLIMG} conv=notrunc seek=$OFFSET bs=512

	cd ${DEPLOY_DIR_IMAGE}
	rm -f ${IMAGE_LINK_NAME}.otaimg
	ln -s ${IMAGE_NAME}.otaimg ${IMAGE_LINK_NAME}.otaimg
}

IMAGE_TYPEDEP_otaimg = "ext4"
