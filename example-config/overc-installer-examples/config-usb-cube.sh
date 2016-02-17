source config-usb.sh

HDINSTALL_ROOTFS="${ARTIFACTS_DIR}/cube-essential-genericx86-64.tar.bz2"

HDINSTALL_CONTAINERS="${ARTIFACTS_DIR}/cube-dom0-genericx86-64.tar.bz2:vty=2 \
                      ${ARTIFACTS_DIR}/cube-domE-genericx86-64.tar.bz2:vty=3"


HDINSTALL_CONTAINERS_STRIP="${ARTIFACTS_DIR}/cube-dom0-genericx86-64.tar.bz2 \
                      ${ARTIFACTS_DIR}/cube-domE-genericx86-64.tar.bz2"

## Uncomment for grub legacy
#INSTALL_GRUBUSBCFG="menu.lst.initramfs-installer"
#INSTALL_GRUBCFG="${INSTALLER_FILES_DIR}/${INSTALL_GRUBUSBCFG}"

# Recalculate PREREQ_FILES
calc_prereq_files

# Add to the list of PREREQ_FILES
PREREQ_FILES="${PREREQ_FILES} ${HDINSTALL_ROOTFS} ${HDINSTALL_CONTAINERS_STRIP}"
