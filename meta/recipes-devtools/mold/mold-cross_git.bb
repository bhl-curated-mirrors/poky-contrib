SUMMARY = "Modern Linker"
HOMEPAGE = "https://github.com/rui314/mold"
LICENSE = "AGPL-3.0-only"
LIC_FILES_CHKSUM = "file://LICENSE;md5=f64a67a3b10cf58f7984209b74f23ec9"

DEPENDS = "zlib-native zstd-native mimalloc-native tbb-native"

SRC_URI = "git://github.com/rui314/mold;protocol=https;branch=main"
UPSTREAM_CHECK_URI = "https://github.com/rui314/mold/releases/"
S = "${WORKDIR}/git"

SRCREV = "040180f933d33fa246f9d2961c2d6e8b74241463"
PV = "1.10.1"

inherit cmake

PN = "mold-cross-${TARGET_ARCH}"
TARGET_ARCH[vardepvalue] = "${TARGET_ARCH}"

EXTRA_OECMAKE = "-DDMOLD_USE_SYSTEM_MIMALLOC=ON -DMOLD_USE_SYSTEM_TBB=ON"

do_install:append() {
    mv ${D}${bindir}/ld.mold ${D}${bindir}/${TARGET_SYS}-ld.mold
}

#BBCLASSEXTEND = "native nativesdk"
inherit cross

# Can't easily disable stripping without disabling optimisations
INSANE_SKIP:${PN} = "already-stripped"

# TODO only works for aarch64 and x86-64 targets

# TODO: generic mold-native recipe and TARGET_ARCH-packages which just install symlinks
