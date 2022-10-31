# Based on runqemu.py test file
#
# Copyright (c) 2017 Wind River Systems, Inc.
#
# SPDX-License-Identifier: MIT
#

import re

from oeqa.selftest.case import OESelftestTestCase
from oeqa.utils.commands import bitbake, runqemu

class GenericEFITest(OESelftestTestCase):
    """EFI booting test class"""
    def test_boot_efi(self):
        cmd_common = "runqemu nographic serial wic ovmf"
        efi_provider = "systemd-boot"
        image = "core-image-minimal"
        machine = "qemux86-64"

        self.write_config(self,
"""
EFI_PROVIDER = "%s"
IMAGE_FSTYPES:pn-%s:append = " wic"
MACHINE = "%s"
MACHINE_FEATURES:append = " efi"
WKS_FILE = "efi-bootdisk.wks.in"
IMAGE_INSTALL:append = " grub-efi systemd-boot kernel-image-bzimage"
"""
% (self.efi_provider, self.image, self.machine))

        bitbake("ovmf")
        bitbake(self.image)

        cmd = "%s %s" % (self.cmd_common, self.machine)
        with runqemu(self.image, ssh=False, launch_cmd=cmd) as qemu:
            self.assertTrue(qemu.runner.logged, "Failed: %s" % cmd)
