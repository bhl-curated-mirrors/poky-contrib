LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://COPYING.SLIBTOOL;md5=818b2bf3780a97a2150e665f258a599d \
                    file://COPYING.SOFORT;md5=9f4c4d0d4fd1aeb9286e0bc06d32330c"

SRC_URI = "git://dev.midipix.org/cross/slibtool.git;protocol=https;branch=main"

SRCREV = "74d6e69d0e9672e08b12ba5def427924417d78b9"

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
