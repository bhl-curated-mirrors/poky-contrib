SUMMARY = "Python bindings to Rust's regress ECMA regular expressions library"
HOMEPAGE = "https://github.com/crate-py/regress"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=7767fa537c4596c54141f32882c4a984"

SRC_URI[sha256sum] = "b42ac506390aea86f3698918889dd6439ca2dca902f3afdc6d70929d144666ef"

require ${BPN}-crates.inc

inherit pypi cargo-update-recipe-crates python_maturin

BBCLASSEXTEND = "native nativesdk"
