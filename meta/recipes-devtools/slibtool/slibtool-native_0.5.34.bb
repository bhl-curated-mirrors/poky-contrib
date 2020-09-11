LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://COPYING.SLIBTOOL;md5=1293820cb7ae16ca38db503f4b1d7693 \
                    file://COPYING.SOFORT;md5=10ec882898f4f7acad2c38c2570e560c"

SRC_URI = "git://dev.midipix.org/cross/slibtool.git;protocol=https;branch=main"

SRCREV = "dea897bf4775c9de9b7b64655734dd33dc42fbd5"
#PV .= "+git${SRCPV}"

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
