KBRANCH ?= "v6.5/standard/base"

require recipes-kernel/linux/linux-yocto.inc

# CVE exclusions
include recipes-kernel/linux/cve-exclusion.inc
include recipes-kernel/linux/cve-exclusion_6.5.inc

# board specific branches
KBRANCH:qemuarm  ?= "v6.5/standard/arm-versatile-926ejs"
KBRANCH:qemuarm64 ?= "v6.5/standard/qemuarm64"
KBRANCH:qemumips ?= "v6.5/standard/mti-malta32"
KBRANCH:qemuppc  ?= "v6.5/standard/qemuppc"
KBRANCH:qemuriscv64  ?= "v6.5/standard/base"
KBRANCH:qemuriscv32  ?= "v6.5/standard/base"
KBRANCH:qemux86  ?= "v6.5/standard/base"
KBRANCH:qemux86-64 ?= "v6.5/standard/base"
KBRANCH:qemuloongarch64  ?= "v6.5/standard/base"
KBRANCH:qemumips64 ?= "v6.5/standard/mti-malta64"

SRCREV_machine:qemuarm ?= "619d7b434792c35b501914d481eb3178d87b9f60"
SRCREV_machine:qemuarm64 ?= "5b2595c3e0dce2912b32ef69aaaacd52cd0e720c"
SRCREV_machine:qemuloongarch64 ?= "5b2595c3e0dce2912b32ef69aaaacd52cd0e720c"
SRCREV_machine:qemumips ?= "622b9a83a51276528ddd38ec9c239b7ef7eac1ee"
SRCREV_machine:qemuppc ?= "5b2595c3e0dce2912b32ef69aaaacd52cd0e720c"
SRCREV_machine:qemuriscv64 ?= "5b2595c3e0dce2912b32ef69aaaacd52cd0e720c"
SRCREV_machine:qemuriscv32 ?= "5b2595c3e0dce2912b32ef69aaaacd52cd0e720c"
SRCREV_machine:qemux86 ?= "5b2595c3e0dce2912b32ef69aaaacd52cd0e720c"
SRCREV_machine:qemux86-64 ?= "5b2595c3e0dce2912b32ef69aaaacd52cd0e720c"
SRCREV_machine:qemumips64 ?= "72909f2a89c5bcd4e8ab9aaab280eb961b4e1282"
SRCREV_machine ?= "5b2595c3e0dce2912b32ef69aaaacd52cd0e720c"
SRCREV_meta ?= "06cf3d8830fda41ff271eec7da6e3c8425df790f"

# set your preferred provider of linux-yocto to 'linux-yocto-upstream', and you'll
# get the <version>/base branch, which is pure upstream -stable, and the same
# meta SRCREV as the linux-yocto-standard builds. Select your version using the
# normal PREFERRED_VERSION settings.
BBCLASSEXTEND = "devupstream:target"
SRCREV_machine:class-devupstream ?= "2309983b0ac063045af3b01b0251dfd118d45449"
PN:class-devupstream = "linux-yocto-upstream"
KBRANCH:class-devupstream = "v6.5/base"

SRC_URI = "git://git.yoctoproject.org/linux-yocto.git;name=machine;branch=${KBRANCH};protocol=https \
           git://git.yoctoproject.org/yocto-kernel-cache;type=kmeta;name=meta;branch=yocto-6.5;destsuffix=${KMETA};protocol=https \
           file://0001-locking-atomic-scripts-fix-fallback-ifdeffery.patch \
           file://jitter.patch"

LIC_FILES_CHKSUM = "file://COPYING;md5=6bc538ed5bd9a7fc9398086aedcd7e46"
LINUX_VERSION ?= "6.5.5"

PV = "${LINUX_VERSION}+git"

KMETA = "kernel-meta"
KCONF_BSP_AUDIT_LEVEL = "1"

KERNEL_DEVICETREE:qemuarmv5 = "versatile-pb.dtb"

COMPATIBLE_MACHINE = "^(qemuarm|qemuarmv5|qemuarm64|qemux86|qemuppc|qemuppc64|qemumips|qemumips64|qemux86-64|qemuriscv64|qemuriscv32|qemuloongarch64)$"

# Functionality flags
KERNEL_EXTRA_FEATURES ?= "features/netfilter/netfilter.scc"
KERNEL_FEATURES:append = " ${KERNEL_EXTRA_FEATURES}"
KERNEL_FEATURES:append:qemuall=" cfg/virtio.scc features/drm-bochs/drm-bochs.scc cfg/net/mdio.scc"
KERNEL_FEATURES:append:qemux86=" cfg/sound.scc cfg/paravirt_kvm.scc"
KERNEL_FEATURES:append:qemux86-64=" cfg/sound.scc cfg/paravirt_kvm.scc"
KERNEL_FEATURES:append = " ${@bb.utils.contains("TUNE_FEATURES", "mx32", " cfg/x32.scc", "", d)}"
KERNEL_FEATURES:append = " ${@bb.utils.contains("DISTRO_FEATURES", "ptest", " features/scsi/scsi-debug.scc", "", d)}"
KERNEL_FEATURES:append = " ${@bb.utils.contains("DISTRO_FEATURES", "ptest", " features/gpio/mockup.scc", "", d)}"
KERNEL_FEATURES:append:powerpc =" arch/powerpc/powerpc-debug.scc"
KERNEL_FEATURES:append:powerpc64 =" arch/powerpc/powerpc-debug.scc"
KERNEL_FEATURES:append:powerpc64le =" arch/powerpc/powerpc-debug.scc"

INSANE_SKIP:kernel-vmlinux:qemuppc64 = "textrel"

