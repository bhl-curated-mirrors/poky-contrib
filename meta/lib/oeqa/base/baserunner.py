#!/usr/bin/env python
# Copyright (C) 2013 Intel Corporation
#
# Released under the MIT license (see COPYING.MIT)

# Base unittest module used by testrunner
# This provides the common test runner functionalities including manifest input,
# xunit output, timeout, tag filtering.

"""Base testrunner"""

import os
import sys
import time
import unittest
import shutil
from optparse import OptionParser, make_option
from util.log import LogHandler
from util.tag import filter_tagexp
from util.timeout import set_timeout

class TestContext(object):
    '''test context which inject into testcase'''
    def __init__(self):
        self.target = None
        self.def_timeout = None

class TestRunnerBase(object):
    '''test runner base '''
    def __init__(self):
        self.option_list = []
        self.tclist = []
        self.runner = None
        self.context = None
        self.manifest = None
        self.log_handler = None
        self.test_result = None
        self.run_time = None

    @staticmethod
    def __get_tc_from_manifest(fname):
        '''get tc list from manifest format '''
        with open(fname, "r") as f:
            tclist = [{"id":n.strip()} for n in f.readlines() \
                                if n.strip() and not n.strip().startswith('#')]
        return tclist

    def _get_log_dir(self, logdir=None):
        '''get the log directory'''
        if not logdir:
            logdir = os.path.abspath(os.path.join(".", "log"))
            if not os.path.exists(logdir):
                os.makedirs(logdir)
            prefix = self.manifest[:self.manifest.rindex(".")]+"%03d"
            names = set(os.listdir(logdir))
            index = len(names)
            while prefix % index not in names and index >= 1:
                index -= 1
            logdir = os.path.join(logdir, prefix % (index + 1))
        else:
            if os.path.exists(logdir):
                shutil.rmtree(logdir)
        os.makedirs(logdir)
        return logdir

    def options(self):
        '''handle testrunner options'''
        self.option_list = [
            make_option("-f", "--manifest", dest="manifest",
                    help="The test list file"),
            make_option("-x", "--xunit", dest="xunit",
                    help="Output result path of in xUnit XML format"),
            make_option("-l", "--log-dir", dest="logdir",
                    help="Set log dir."),
            make_option("-a", "--tag-expression", dest="tag",
                    help="Set tag expression to filter test cases."),
            make_option("-T", "--timeout", dest="timeout", default=60,
                    help="Set timeout for each test case."),
            make_option("-e", "--tests", dest="tests", action="append",
                    help="Run tests by dot separated module path")
        ]

    def configure(self, options):
        '''configure before testing'''
        if options.xunit:
            try:
                from xmlrunner import XMLTestRunner
            except ImportError:
                raise Exception("unittest-xml-reporting not installed")
            self.runner = XMLTestRunner(stream=sys.stderr, \
                                        verbosity=2, output=options.xunit)
        else:
            self.runner = unittest.TextTestRunner(stream=sys.stderr, \
                                                  verbosity=2)

        self.tclist = []
        if options.manifest:
            self.manifest = options.manifest
            fbname, fext = os.path.splitext(os.path.basename(options.manifest))
            assert fbname == "manifest" or fext == ".manifest", \
                  "Please specify file name like xxx.manifest or manifest.xxx"
            self.tclist = self.__get_tc_from_manifest(options.manifest)
        if options.tests:
            self.tclist.extend([{"id":x} for x in options.tests])

        if options.logdir:
            logdir = self._get_log_dir(options.logdir)
            self.log_handler = LogHandler(logdir)

        self.context = TestContext()

        try:
            self.context.def_timeout = int(options.timeout)
        except ValueError:
            print "timeout need an integer value"
            raise

    def result(self):
        '''output test result '''
        print "output test result..."
        print self.tclist

    @staticmethod
    def loadtest(names):
        '''load test suite'''
        testloader = unittest.TestLoader()
        tclist = []
        for name in names:
            tset = testloader.loadTestsFromName(name)
            if tset.countTestCases() > 0:
                tclist.append(tset)
            elif tset._tests == []:
                tclist.append(testloader.discover(name, "*.py"))
        return testloader.suiteClass(tclist)

    def runtest(self, suite):
        '''run test suite'''
        starttime = time.time()
        self.test_result = self.runner.run(suite)
        self.run_time = time.time() - starttime

    def run(self):
        '''start testing'''
        self.options()
        usage = "usage: %prog [options]"
        parser = OptionParser(option_list=self.option_list, usage=usage)
        options = parser.parse_args()[0]
        self.configure(options)
        print options
        if self.log_handler:
            self.log_handler.start()

        setattr(unittest.TestCase, "tc", self.context)
        tnames = [tc["id"] for tc in self.tclist]
        suite = self.loadtest(tnames)
        if options.tag:
            suite = filter_tagexp(suite, options.tag)
        set_timeout(suite, self.context.def_timeout)
        print "Found %s tests" % suite.countTestCases()
        self.runtest(suite)

        self.result()
        if self.log_handler:
            self.log_handler.end()

if __name__ == "__main__":
    TestRunnerBase().run()
