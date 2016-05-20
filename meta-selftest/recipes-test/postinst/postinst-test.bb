SUMMARY = "Test packages for postinsts"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COREBASE}/meta/COPYING.MIT;md5=3da9cfbcb788c80a0384361b4de20420"

INHIBIT_DEFAULT_DEPS = "1"
EXCLUDE_FROM_WORLD = "1"

PACKAGES = "${PN}-good ${PN}-delayed ${PN}-bad"


ALLOW_EMPTY_${PN}-good = "1"
pkg_postinst_${PN}-good() {
    echo ${PN}-good, exit 0
    exit 0
}

ALLOW_EMPTY_${PN}-bad = "1"
pkg_postinst_${PN}-bad() {
    echo ${PN}-bad, aborting
    exit 1
}

ALLOW_EMPTY_${PN}-delayed = "1"
pkg_postinst_${PN}-delayed() {
    if [ "$D" ]; then
        echo ${PN}-delayed at rootfs time, aborting
        exit 1
    else
        echo ${PN}-delayed at first boot
        exit 0
    fi
}
