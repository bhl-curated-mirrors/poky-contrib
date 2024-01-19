DEPENDS:append = " b2-native"

# TODO something with out-of-tree builds
# B = "${WORKDIR}/build"

B2_DIR ?= "${S}"
B2_VARIANT ?= "release"
B2_TARGET ?= ""

B2_OPTS = "\
        -d+2 \
        --debug-configuration \
        --ignore-site-config \
        --user-config=${WORKDIR}/user-config.jam \
        ${@oe.utils.parallel_make_argument(d, '-j%d')} \
        toolset=gcc \
        variant=${B2_VARIANT} \
        debug-symbols=on \
        staging-prefix=${D}${prefix} \
    "

addtask write_config before do_configure
do_write_config() {
    cat >${WORKDIR}/user-config.jam <<EOF
using gcc : : ${CXX} : <cflags>"${CFLAGS}" <cxxflags>"${CXXFLAGS}" <linkflags>"${LDFLAGS}" ;
EOF
}
do_write_config[vardeps] += "CXX CFLAGS CXXFLAGS LDFLAGS"

b2_do_configure() {
    cd ${B2_DIR}
    b2 ${B2_OPTS} clean
}

b2_do_compile() {
    cd ${B2_DIR}
    b2 ${B2_OPTS} ${B2_TARGET}
}

# TODO These arguments are clearly nonsense wtf
b2_do_install() {
    cd ${B2_DIR}
    b2 ${B2_OPTS} install --prefix=${prefix}
}

EXPORT_FUNCTIONS do_configure do_compile do_install
