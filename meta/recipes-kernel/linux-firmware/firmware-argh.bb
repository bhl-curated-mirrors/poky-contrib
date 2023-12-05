LICENSE = "CLOSED"

SRC_URI = "https://cdn.kernel.org/pub/linux/kernel/firmware/linux-firmware-20190312.tar.gz"
SRC_URI[sha256sum] = "42eb807019cc0b43545a046a1b9c8f98d733ef9aa8e90f4ccb8f97d85bb1ee6d"

S = "${WORKDIR}/linux-firmware-20190312"

inherit bin_package

INHIBIT_DEFAULT_DEPS = "1"
