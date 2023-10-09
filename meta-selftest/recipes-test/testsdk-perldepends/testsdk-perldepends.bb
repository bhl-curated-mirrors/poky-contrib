SUMMARY = "Test recipe for sdk populate test case"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

INHIBIT_DEFAULT_DEPS = "1"

RDEPENDS:${PN}="perl (>= 5.12)"

do_install(){
	mkdir -p ${D}/var/lib/
	touch ${D}/var/lib/testname 
	echo "${PN}" > ${D}/var/lib/testname
}



