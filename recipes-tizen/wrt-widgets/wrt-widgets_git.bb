require wrt-widgets.inc

PRIORITY = "10"

LIC_FILES_CHKSUM ??= "file://${COMMON_LICENSE_DIR}/GPL-2.0;md5=801f80980d171dd6425610833a22dbe6"

SRC_URI += "git://review.tizen.org/profile/common/wrt-widgets;tag=044e7781b29f2232cd25fa8bea1db229b7077bf0;nobranch=1"

BBCLASSEXTEND += " native "

