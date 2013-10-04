DESCRIPTION = "A live image init script for grub-efi"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COREBASE}/meta/COPYING.MIT;md5=3da9cfbcb788c80a0384361b4de20420"
SRC_URI = "file://init-install-efi.sh"

<<<<<<< HEAD
PR = "r1"
=======
PR = "r0"
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc

RDEPENDS_${PN} = "parted e2fsprogs-mke2fs dosfstools"

do_install() {
        install -m 0755 ${WORKDIR}/init-install-efi.sh ${D}/install-efi.sh
}

# While this package maybe an allarch due to it being a
# simple script, reality is that it is Host specific based
# on the COMPATIBLE_HOST below, which needs to take precedence
#inherit allarch
INHIBIT_DEFAULT_DEPS = "1"

FILES_${PN} = " /install-efi.sh "

COMPATIBLE_HOST = "(i.86|x86_64).*-linux"
