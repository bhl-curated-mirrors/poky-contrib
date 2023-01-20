
# Get the host's default pkg-config search path by using command -p to run the
# host's binary and not the one in the SDK.
HOST_PKG_PATH=$(command -p pkg-config --variable=pc_path pkg-config 2>/dev/null)

# If there is a target sysroot, until we have a proper native/target split we need to search this too.
if test -n "${SDKTARGETSYSROOT}" -a -d "${SDKTARGETSYSROOT}"; then
    export PKG_CONFIG_SYSROOT_DIR=$SDKTARGETSYSROOT
    export PKG_CONFIG_PATH=${SDKTARGETSYSROOT}${OECORE_LIBDIR}/pkgconfig:${SDKTARGETSYSROOT}${OECORE_DATADIR}/pkgconfig
fi

# PKG_CONFIG_LIBDIR is the system search path, always searched after
# PKG_CONFIG_PATH. By default these are the paths defined at build time which
# are meaningless in a nativesdk build, so we can override them wih the native
# paths.
#
# If the host doesn't have pkg-config, use sensible defaults.
export PKG_CONFIG_LIBDIR=@LIBDIR@/pkgconfig:@DATADIR@/pkgconfig:${HOST_PKG_PATH:-/usr/lib/pkgconfig:/usr/share/pkgconfig}
