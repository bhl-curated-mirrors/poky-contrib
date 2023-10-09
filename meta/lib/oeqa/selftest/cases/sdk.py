#
# Copyright OpenEmbedded Contributors
#
# SPDX-License-Identifier: MIT
#

import os

from oeqa.selftest.case import OESelftestTestCase
from oeqa.utils.commands import get_bb_var, bitbake

class PopulateSDK(OESelftestTestCase):
    '''Tests for populate SDK task(s)'''

    @classmethod
    def setUpClass(self):

        super(PopulateSDK, self).setUpClass()
        self.buildtarget = 'core-image-minimal'
        self.classname = 'PopulateSDK'

    def sdk_build(self):
        """
        Test if package added via IMAGE_INSTALL
        conflicts with dummy SDK providers
        """
        SDKTASK = '-c populate_sdk'
        bbargs = "{} {}".format(SDKTASK, self.buildtarget)
        self.logger.info("{}: doing bitbake {} ".format(self.classname, bbargs))
        return bitbake(bbargs).status

    def set_config(self, image_install, package_classes):
        config = 'IMAGE_INSTALL:append = " {}"\n'.format(image_install)
        config += 'PACKAGE_CLASSES = " package_{}"\n'.format(package_classes)
        return config

    def do_test_build(self, image_install, package_manager):
        self.write_config(self.set_config(image_install, package_manager))
        res = self.sdk_build()
        self.assertEqual(0, res, "Failed to populate SDK with {} in IMAGE_INSTALL and {} package manager"\
            .format(image_install, package_manager))

    def test_image_install_ipk(self):
        """
        Regression test for [Yocto #13338] 
        """
        self.do_test_build("bash", "ipk")

    def test_image_install_rpm(self):
        """
        Regression test for [Yocto #13338] 
        """
        self.do_test_build("bash", "rpm")

    def test_image_install_deb(self):
        """
        Regression test for [Yocto #13338] 
        """
        self.do_test_build("bash", "deb")
        

    def test_image_install_confictdeps_ipk(self):
        """
        Regression test for [Yocto #14995]
        """
        self.skipTest("Disabled until [Yocto #14995] is fixed")
        self.do_test_build("testsdk-perldepends", "ipk")
        
    def test_image_install_confictdeps_rpm(self):
        """
        Regression test for [Yocto #14995]
        """
        self.do_test_build("testsdk-perldepends", "rpm")

    def test_image_install_confictdeps_deb(self):
        """
        Regression test for [Yocto #14995]
        """
        self.do_test_build("testsdk-perldepends", "deb")
