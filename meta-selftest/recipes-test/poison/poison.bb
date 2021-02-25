SUMMARY = "Poison test"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

LICENSE = "MIT"

inherit nopackages

do_compile() {
    touch empty.c
    ${CPP} ${CFLAGS} -I/usr/include empty.c
}

EXCLUDE_FROM_WORLD = "1"
