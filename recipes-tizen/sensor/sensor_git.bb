require sensor.inc

PRIORITY = "10"

LIC_FILES_CHKSUM ??= "file://${COMMON_LICENSE_DIR}/GPL-2.0;md5=801f80980d171dd6425610833a22dbe6"

SRC_URI += "git://review.tizen.org/platform/core/api/sensor;tag=27e942b01a6edc3748961c5c81f2b55586b5ca14;nobranch=1"

BBCLASSEXTEND += " native "

