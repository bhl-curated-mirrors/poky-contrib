LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://COPYING.SLIBTOOL;md5=818b2bf3780a97a2150e665f258a599d \
                    file://COPYING.SOFORT;md5=9f4c4d0d4fd1aeb9286e0bc06d32330c"

SRC_URI = "git://dev.midipix.org/cross/slibtool.git;protocol=https;branch=main"

SRCREV = "a126a7f68ef374d65d014226195380eb7dceb634"
PV .= "+git${SRCPV}"

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

do_install () {
	oe_runmake install DESTDIR=${D}
}
