require python3_${PV}.bb

SRC_URI += "file://Makefile-add-install_generate_profile-target.patch \
            file://rename-libpython3-to-libpython-profile-opt3.patch \
           "

PYTHON3_MAKE_TARGET = "build_all_generate_profile"

RCONFLICTS_${PN}-core = "python3-core"
RCONFLICTS_lib${BPN} = "libpython3"
