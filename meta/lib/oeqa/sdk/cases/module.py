#
# Copyright OpenEmbedded Contributors
#
# SPDX-License-Identifier: MIT
#

import os
import shutil
import tempfile
import unittest

from oeqa.sdk.case import OESDKTestCase
from oeqa.utils.subprocesstweak import errors_have_output
errors_have_output()

class KernelModuleTest(OESDKTestCase):
    """
    Test that external kernel modules build correctly.
    """

    def setUp(self):
        if not self.tc.hasTargetPackage("kernel-devsrc"):
            raise unittest.SkipTest("SDK doesn't contain kernel-devsrc")

    # TODO: is testsdk running with PATH from hosttools?
    
    def test_kernel_module(self):
        # Calculate the path to the kernel source tree
        kdir = self._run("echo ${SDKTARGETSYSROOT}${prefix}/src/kernel").strip()
        self.assertTrue(kdir)

        output = self._run("make -C %s V=1 modules_prepare" % kdir)
        with tempfile.TemporaryDirectory(prefix="module", dir=self.tc.sdk_dir) as testdir:
            shutil.copyfile(os.path.join(self.tc.files_dir, "hellomod_makefile"), os.path.join(testdir, "Makefile"))
            shutil.copyfile(os.path.join(self.tc.files_dir, "hellomod.c"), os.path.join(testdir, "hellomod.c"))
            output = self._run("make -C %s M=%s V=1 modules" % (kdir, testdir))
            self.check_elf(os.path.join(testdir, "hellomod.ko"))
