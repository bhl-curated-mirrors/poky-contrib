#!/usr/bin/env python3

import os
import re
import string
import sys

# Keep these in sync with the logic in meson-routines.bbclass
def meson_cpu_family():
    arch = os.environ["OECORE_TARGET_ARCH"]
    if arch == 'powerpc':
        return 'ppc'
    elif arch == 'powerpc64' or arch == 'powerpc64le':
        return 'ppc64'
    elif arch == 'armeb':
        return 'arm'
    elif arch == 'aarch64_be':
        return 'aarch64'
    elif arch == 'mipsel':
        return 'mips'
    elif arch == 'mips64el':
        return 'mips64'
    elif re.match(r"i[3-6]86", arch):
        return "x86"
    elif arch == "microblazeel":
        return "microblaze"
    else:
        return arch

def meson_operating_system():
    opersys = os.environ["OECORE_TARGET_ARCH"]
    if "mingw" in opersys:
        return "windows"
    # avoid e.g 'linux-gnueabi'
    elif "linux" in opersys:
        return "linux"
    else:
        return opersys

class Template(string.Template):
    delimiter = "@"

class Environ():
    def __getitem__(self, name):
        val = os.environ[name]
        val = val.split()
        if len(val) > 1:
            val = ["'%s'" % x for x in val]
            val = ', '.join(val)
            val = '[%s]' % val
        elif val:
            val = "'%s'" % val.pop()
        return val

try:
    sysroot = os.environ['OECORE_NATIVE_SYSROOT']
except KeyError:
    print("Not in environment setup, bailing")
    sys.exit(1)

template_file = os.path.join(sysroot, 'usr/share/meson/meson.cross.template')
cross_file = os.path.join(sysroot, 'usr/share/meson/%smeson.cross' % os.environ["TARGET_PREFIX"])
native_template_file = os.path.join(sysroot, 'usr/share/meson/meson.native.template')
native_file = os.path.join(sysroot, 'usr/share/meson/meson.native')

# Inject transformed values
os.environ["OECORE_MESON_TARGET_FAMILY"] = meson_cpu_family()
os.environ["OECORE_MESON_TARGET_OS"] = meson_operating_system()

with open(template_file) as in_file:
    template = in_file.read()
    output = Template(template).substitute(Environ())
    with open(cross_file, "w") as out_file:
        out_file.write(output)

with open(native_template_file) as in_file:
    template = in_file.read()
    output = Template(template).substitute({'OECORE_NATIVE_SYSROOT': os.environ['OECORE_NATIVE_SYSROOT']})
    with open(native_file, "w") as out_file:
        out_file.write(output)
