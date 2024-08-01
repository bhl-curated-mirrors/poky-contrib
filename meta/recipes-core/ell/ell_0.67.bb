SUMMARY  = "Embedded Linux Library"
HOMEPAGE = "https://01.org/ell"
DESCRIPTION = "The Embedded Linux Library (ELL) provides core, \
low-level functionality for system daemons. It typically has no \
dependencies other than the Linux kernel, C standard library, and \
libdl (for dynamic linking). While ELL is designed to be efficient \
and compact enough for use on embedded Linux platforms, it is not \
limited to resource-constrained systems."
SECTION = "libs"
LICENSE  = "LGPL-2.1-only"
LIC_FILES_CHKSUM = "file://COPYING;md5=fb504b67c50331fc78734fed90fb0e09"

DEPENDS = "dbus openssl-native xxd-native"

inherit autotools pkgconfig ptest

SRC_URI = " \
    https://mirrors.edge.kernel.org/pub/linux/libs/${BPN}/${BPN}-${PV}.tar.xz \
    file://run-ptest \
"
SRC_URI[sha256sum] = "97942e8cefb130b632496e5485242f3f374f3b8846800fb74fffd76dc2a0c726"

EXTRA_OECONF += "--enable-tests --enable-maintainer-mode"
CFLAGS += "-UUNITDIR -DUNITDIR="\\"./unit/\\"""

do_compile:prepend() {
    mkdir -p ${B}/unit
}

do_install_ptest() {
    install -m755 -Dt ${D}${PTEST_PATH} $(find ${B}/unit -executable -type f)
    install -Dt ${D}${PTEST_PATH}/unit \
        ${S}/unit/dbus.conf \
        ${S}/unit/settings.test \
        $(find ${B}/unit -name \*.pem -type f)
}
