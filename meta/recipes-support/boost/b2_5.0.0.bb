SUMMARY = "B2 build system"
DESCRIPTION = "B2 makes it easy to build C++ projects, everywhere."
HOMEPAGE = "https://www.bfgroup.xyz/b2/"
SECTION = "devel"

LICENSE = "BSL-1.0"
LIC_FILES_CHKSUM = "file://LICENSE.txt;md5=e4224ccaecb14d942c71d31bef20d78c"

DEPENDS = "bison-native"

GITHUB_BASE_URI = "https://github.com/bfgroup/b2"

SRC_URI = "${GITHUB_BASE_URI}/releases/download/5.0.0/b2-5.0.0.tar.bz2"
SRC_URI[sha256sum] = "1ef867f7d374345a948baca025ed277dadda05a68439aa383a06aceb9911f7d3"

inherit b2 github-releases

B2_TARGET = "b2"

# Bootstrap the native build manually
do_configure:class-native() {
    :
}

do_compile:class-native() {
    ./bootstrap.sh --verbose
}

do_install:prepend:class-native() {
    PATH=$PATH:${S}
}

# TODO can I build a cross b2 by always using the bootstrap path and forcing the right CC?

# The native build is either release mode (pre-stripped) or debug (-O0).
INSANE_SKIP:b2-native = "already-stripped"

# TODO this doesn't actually work
BBCLASSEXTEND = "native nativesdk"
