SUMMARY = "This library provides an implementation of the rpm's pgp interface using Sequoia."
HOMEPAGE = "https://github.com/rpm-software-management/rpm-sequoia"

LICENSE = "LGPL-2.0-or-later"
LIC_FILES_CHKSUM = "file://LICENSE.txt;md5=c4eec0c20c6034b9407a09945b48a43f"

SRC_URI = "git://github.com/rpm-software-management/rpm-sequoia;branch=main;protocol=https"
require ${BPN}-crates.inc

SRCREV = "f2e54298585ad80aadd206deb9bed5a1db0c44c4"
S = "${WORKDIR}/git"

inherit cargo cargo-update-recipe-crates pkgconfig

DEPENDS = "nettle"

do_compile:prepend () {
    mkdir -p ${S}/target/release/
}

BBCLASSEXTEND = "native nativesdk"
