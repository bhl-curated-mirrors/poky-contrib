SUMMARY = "TOML parser/encoder for modern C++"
HOMEPAGE = "https://github.com/ToruNiina/toml11"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=44d1fcf70c7aa6991533c38daf7befa3"

SRC_URI = "git://github.com/ToruNiina/toml11;protocol=https;branch=master"
SRCREV = "dcfe39a783a94e8d52c885e5883a6fbb21529019"

S = "${WORKDIR}/git"

inherit cmake

BBCLASSEXTEND = "native nativesdk"
