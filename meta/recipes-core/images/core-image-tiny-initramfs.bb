# Simple initramfs image artifact generation for tiny images.
DESCRIPTION = "Tiny image capable of booting a device. The kernel includes \
the Minimal RAM-based Initial Root Filesystem (initramfs), which finds the \
first 'init' program more efficiently.  core-image-tiny-initramfs doesn't \
actually generate an image but rather generates boot and rootfs artifacts \
into a common location that can subsequently be picked up by external image \
generation tools such as wic."

PACKAGE_INSTALL = "initramfs-live-boot packagegroup-core-boot dropbear ${VIRTUAL-RUNTIME_base-utils} udev base-passwd ${ROOTFS_BOOTSTRAP_INSTALL}"

# Do not pollute the initrd image with rootfs features
IMAGE_FEATURES = ""

export IMAGE_BASENAME = "core-image-tiny-initramfs"
IMAGE_LINGUAS = ""

LICENSE = "MIT"

# don't actually generate an image, just the artifacts needed for one
ARTIFACTS_ONLY ?= "1"

IMAGE_FSTYPES = "${INITRAMFS_FSTYPES}"
inherit core-image

IMAGE_ROOTFS_SIZE = "8192"
IMAGE_ROOTFS_EXTRA_SPACE = "0"

BAD_RECOMMENDATIONS += "busybox-syslog"

# Use the same restriction as initramfs-live-install
COMPATIBLE_HOST = "(i.86|x86_64).*-linux"

python tinyinitrd () {
  # Modify our init file so the user knows we drop to shell prompt on purpose
  newinit = None
  with open(d.expand('${IMAGE_ROOTFS}/init'), 'r') as init:
    newinit = init.read()
    newinit = newinit.replace('Cannot find $ROOT_IMAGE file in /run/media/* , dropping to a shell ', 'Poky Tiny Reference Distribution:')
  with open(d.expand('${IMAGE_ROOTFS}/init'), 'w') as init:
    init.write(newinit)
}

IMAGE_PREPROCESS_COMMAND += "tinyinitrd;"
