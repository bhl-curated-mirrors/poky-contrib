LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://COPYING.SLIBTOOL;md5=818b2bf3780a97a2150e665f258a599d \
                    file://COPYING.SOFORT;md5=dccc614a8e7daa9b436fdc7cd4e65e99"

SRC_URI = "git://dev.midipix.org/cross/slibtool.git;protocol=https;branch=main"

SRCREV = "fc7ad9f9947b5097e1a246b009b487d3206fd588"
PV .= "+git"

DEPENDS = "m4-native"

inherit native

S = "${WORKDIR}/git"
B = "${WORKDIR}/build"

# TODO build/host/target, BBCLASSEXTEND

do_configure() {
	${S}/configure \
		--source-dir=${S} \
		--prefix=${prefix} \
		--libdir=${libdir} \
		--compiler="${CC}"
}
do_configure[cleandirs] = "${B}"

do_install () {
	oe_runmake install DESTDIR=${D}
	install -d ${D}${datadir}/aclocal
	install -m 644 ${S}/m4/slibtool.m4 ${D}${datadir}/aclocal
}
