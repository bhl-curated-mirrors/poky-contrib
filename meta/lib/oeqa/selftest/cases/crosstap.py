from oeqa.selftest.case import OESelftestTestCase
from oeqa.utils.commands import bitbake, get_bb_vars, runCmd, runqemu
import os

class CrossTapTest(OESelftestTestCase):

    def test_crosstap_can_use_systemtap_on_qemu(self):
        self.write_config('EXTRA_IMAGE_FEATURES += "tools-profile ssh-server-openssh"')
        result = bitbake('core-image-minimal')
        self.assertEqual(result.status, 0, msg="Bitbake core-image-minimal failed. Bitbake output: %s" % result.output)
        result = bitbake('systemtap-native')
        self.assertEqual(result.status, 0, msg="Bitbake systemtap-native failed. Bitbake output: %s" % result.output)

        recipe = 'core-image-minimal'
        bb_vars = get_bb_vars(['MACHINE', 'DEPLOY_DIR_IMAGE'])
        machine =  bb_vars['MACHINE']
        deploy_dir_image = bb_vars['DEPLOY_DIR_IMAGE']
        qemuboot_conf = "%s-%s.qemuboot.conf" % (recipe, machine)
        qemuboot_conf = os.path.join(deploy_dir_image, qemuboot_conf)
        cmd_common = "runqemu nographic"
        cmd = "%s %s" % (cmd_common, qemuboot_conf)
        with runqemu(recipe, ssh=True, launch_cmd=cmd) as qemu:
            systap_file = os.path.join(self.tc.files_dir, 'trace_begin_hello.stp')
            result = runCmd("crosstap root@%s %s" % (qemu.ip, systap_file))
        self.assertTrue('hello world' in result.output, 'Crosstap failed.')
