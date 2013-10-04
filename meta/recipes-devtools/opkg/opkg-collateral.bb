DESCRIPTION = "opkg configuration files"
SECTION = "base"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COREBASE}/meta/COPYING.MIT;md5=3da9cfbcb788c80a0384361b4de20420"
<<<<<<< HEAD
PR = "r2"
=======
PR = "r1"
>>>>>>> cb9658cf8ab6cf009030dcadde9dc6c54b72bddc

SRC_URI = "file://opkg.conf.comments \
	   file://dest \
	   file://src "

OPKGLIBDIR = "${localstatedir}/lib"
do_compile () {
	cat ${WORKDIR}/opkg.conf.comments >${WORKDIR}/opkg.conf
	cat ${WORKDIR}/src	>>${WORKDIR}/opkg.conf
	cat ${WORKDIR}/dest	>>${WORKDIR}/opkg.conf
	echo "lists_dir ext ${OPKGLIBDIR}/opkg" >>${WORKDIR}/opkg.conf
}

do_install () {
	install -d ${D}${sysconfdir}/opkg
	install -m 0644 ${WORKDIR}/opkg.conf ${D}${sysconfdir}/opkg/opkg.conf
}

CONFFILES_${PN} = "${sysconfdir}/opkg/opkg.conf"
