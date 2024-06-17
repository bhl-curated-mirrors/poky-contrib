SUMMARY = "A JSON Schema CLI"
HOMEPAGE = "https://github.com/python-jsonschema/check-jsonschema"
LICENSE = "Apache-2.0"
LIC_FILES_CHKSUM = "file://LICENSE;md5=6d5521b169354a237f3adf255fb0bfd4"

inherit pypi setuptools3

PYPI_PACKAGE = "check_jsonschema"

SRC_URI[sha256sum] = "8100ff34ed042189c486866b0448ab9930825dc6ad1acb86c1ffb000f4648b42"

RDEPENDS:${PN} += " \
    python3-click \
    python3-jsonschema \
    python3-regress \
    python3-requests \
    python3-ruamel-yaml \
    python3-tomli \
"

BBCLASSEXTEND = "native nativesdk"
