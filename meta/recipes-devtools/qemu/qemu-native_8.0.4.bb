BPN = "qemu"

DEPENDS = "glib-2.0-native zlib-native ninja-native meson-native"

require qemu.inc

inherit native

EXTRA_OECONF:append = " --disable-tools --disable-install-blobs --disable-guest-agent"

PACKAGECONFIG ??= "user-targets pie"
