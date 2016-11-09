# Copyright (C) 2016 Intel Corporation
# Released under the MIT license (see COPYING.MIT)

import os
import sys
import json
import time
import logging
import collections

from oeqa.core.loader import OETestLoader
from oeqa.core.runner import OETestRunner, OEStreamLogger

class OETestContext(object):
    loaderClass = OETestLoader
    runnerClass = OETestRunner

    files_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../files")

    def __init__(self, d=None, logger=None):
        if not type(d) is dict:
            raise TypeError("d isn't dictionary type")

        self.d = d
        self.logger = logger
        self._registry = {}
        self._registry['cases'] = collections.OrderedDict()
        self._results = {}

    def _read_modules_from_manifest(self, manifest):
        if not os.path.exists(manifest):
            raise

        modules = []
        for line in open(manifest).readlines():
            line = line.strip()
            if line and not line.startswith("#"):
                modules.append(line)

        return modules

    def loadTests(self, module_paths, modules=[], tests=[],
            modules_manifest="", modules_required=[], filters={}):
        if modules_manifest:
            modules = self._read_modules_from_manifest(modules_manifest)

        self.loader = self.loaderClass(self, module_paths, modules, tests,
                modules_required, filters)
        self.suites = self.loader.discover()

    def runTests(self):
        streamLogger = OEStreamLogger(self.logger)
        self.runner = self.runnerClass(self, stream=streamLogger, verbosity=2)
        return self.runner.run(self.suites)

class OETestContextExecutor(object):
    _context_class = OETestContext

    name = 'core'
    help = 'core test component example'
    description = 'executes core test suite example'

    default_cases = [os.path.join(os.path.abspath(os.path.dirname(__file__)),
            'cases/example')]
    default_data = os.path.join(default_cases[0], 'data.json')

    def register_commands(self, logger, subparsers):
        self.parser = subparsers.add_parser(self.name, help=self.help,
                description=self.description, group='components')

        self.default_output_log = '%s-results-%s.log' % (self.name,
                time.strftime("%Y%m%d%H%M%S"))
        self.parser.add_argument('--output-log', action='store',
                default=self.default_output_log,
                help="results output log, default: %s" % self.default_output_log)

        if self.default_data:
            self.parser.add_argument('--data-file', action='store',
                    default=self.default_data,
                    help="data file to load, default: %s" % self.default_data)
        else:
            self.parser.add_argument('--data-file', action='store',
                    help="data file to load")

        if self.default_cases:
            self.parser.add_argument('CASES_PATHS', action='store',
                    default=self.default_cases, nargs='*',
                    help="paths to directories with test cases, default: %s"\
                            % self.default_cases)
        else:
            self.parser.add_argument('CASES_PATHS', action='store',
                    nargs='+', help="paths to directories with test cases")

        self.parser.set_defaults(func=self.run)

    def _setup_logger(self, logger, args):
        formatter = logging.Formatter('%(asctime)s - ' + self.name + \
                ' - %(levelname)s - %(message)s')
        sh = logger.handlers[0]
        sh.setFormatter(formatter)
        fh = logging.FileHandler(args.output_log)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        return logger

    def _process_args(self, logger, args):
        self.tc_kwargs = {}
        self.tc_kwargs['init'] = {}
        self.tc_kwargs['load'] = {}
        self.tc_kwargs['run'] = {}

        self.tc_kwargs['init']['logger'] = self._setup_logger(logger, args)
        if args.data_file:
            self.tc_kwargs['init']['d'] = json.load(
                    open(args.data_file, "r"))
        else:
            self.tc_kwargs['init']['d'] = {}

        self.module_paths = args.CASES_PATHS

    def run(self, logger, args):
        self._process_args(logger, args)

        self.tc = self._context_class(**self.tc_kwargs['init'])
        self.tc.loadTests(self.module_paths, **self.tc_kwargs['load'])
        rc = self.tc.runTests(**self.tc_kwargs['run'])

        output_link = os.path.join(os.path.dirname(args.output_log),
                "%s-results.log" % self.name)
        if os.path.exists(output_link):
            os.remove(output_link)
        os.symlink(args.output_log, output_link)

        return rc

_executor_class = OETestContextExecutor
