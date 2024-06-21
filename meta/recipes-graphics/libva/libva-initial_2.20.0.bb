require libva.inc

PACKAGECONFIG ?= ""

do_install:append () {
	rm -f ${D}${libdir}/*.so*
}

RECIPE_NO_UPDATE_REASON = "Upgrades are handled in base libva recipe"
