SUMMARY = "mimalloc is a compact general purpose allocator with excellent performance."
HOMEPAGE = "https://github.com/microsoft/mimalloc"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=cd47cf280095d74b469beed1f28c8e77"

SRC_URI = "git://github.com/microsoft/mimalloc;protocol=https;branch=dev-slice"
SRCREV = "28cf67e5b64c704cad993c71f29a24e781bee544"

S = "${WORKDIR}/git"

inherit cmake

EXTRA_OECMAKE += "-DMI_INSTALL_TOPLEVEL=ON"

BBCLASSEXTEND = "native nativesdk"
