SUMMARY = "C library for complex number arithmetic with arbitrary precision and correct rounding"
DESCRIPTION = "Mpc is a C library for the arithmetic of complex numbers with arbitrarily high precision and correct rounding of the result. It is built upon and follows the same principles as Mpfr"
HOMEPAGE = "http://www.multiprecision.org/"
LICENSE = "LGPLv3"
SECTION = "libs"

inherit autotools texinfo

DEPENDS = "gmp mpfr"

LIC_FILES_CHKSUM = "file://COPYING.LESSER;md5=e6a600fd5e1d9cbde2d983680233ad02"
SRC_URI = "http://www.multiprecision.org/mpc/download/mpc-${PV}.tar.gz"

SRC_URI[md5sum] = "d6a1d5f8ddea3abd2cc3e98f58352d26"
SRC_URI[sha256sum] = "617decc6ea09889fb08ede330917a00b16809b8db88c29c31bfbb49cbf88ecc3"

UPSTREAM_CHECK_URI = "http://www.multiprecision.org/index.php?prog=mpc&page=download"

S = "${WORKDIR}/mpc-${PV}"

do_configure_prepend() {
    chmod +w ${S}/m4/*.m4
}

BBCLASSEXTEND = "native nativesdk"
