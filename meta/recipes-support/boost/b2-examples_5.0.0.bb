SUMMARY = "B2 examples"
HOMEPAGE = "https://www.bfgroup.xyz/b2/"

LICENSE = "BSL-1.0"
LIC_FILES_CHKSUM = "file://LICENSE.txt;md5=e4224ccaecb14d942c71d31bef20d78c"

SRC_URI = "https://github.com/bfgroup/b2/releases/download/5.0.0/b2-5.0.0.tar.bz2"
SRC_URI[sha256sum] = "1ef867f7d374345a948baca025ed277dadda05a68439aa383a06aceb9911f7d3"

S = "${WORKDIR}/b2-${PV}"

inherit b2

# TODO built_tool exercises building native code in cross and breaks

B2_DIR = "${S}/example/hello/"

do_install() {
    install -d ${D}${bindir}
    install ${B2_DIR}/bin/*/*/*/hello ${D}${bindir}
}

BBCLASSEXTEND = "native"
