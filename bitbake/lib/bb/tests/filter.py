#
# Copyright (C) 2022 Garmin Ltd. or its subsidiaries
#
# SPDX-License-Identifier: GPL-2.0-only
#

import unittest
import bb.filter


class BuiltinFilterTest(unittest.TestCase):
    def test_disallowed_builtins(self):
        with self.assertRaises(NameError):
            val = bb.filter.apply_filters("1", ["open('foo.txt', 'rb')"])

    def test_prefix(self):
        val = bb.filter.apply_filters("1 2 3", ["prefix(v, 'a')"])
        self.assertEqual(val, "a1 a2 a3")

        val = bb.filter.apply_filters("", ["prefix(v, 'a')"])
        self.assertEqual(val, "")

    def test_suffix(self):
        val = bb.filter.apply_filters("1 2 3", ["suffix(v, 'b')"])
        self.assertEqual(val, "1b 2b 3b")

        val = bb.filter.apply_filters("", ["suffix(v, 'b')"])
        self.assertEqual(val, "")

    def test_sort(self):
        val = bb.filter.apply_filters("z y x", ["sort(v)"])
        self.assertEqual(val, "x y z")

        val = bb.filter.apply_filters("", ["sort(v)"])
        self.assertEqual(val, "")

    def test_identity(self):
        val = bb.filter.apply_filters("1 2 3", ["v"])
        self.assertEqual(val, "1 2 3")

        val = bb.filter.apply_filters("123", ["v"])
        self.assertEqual(val, "123")

    def test_empty(self):
        val = bb.filter.apply_filters("1 2 3", ["", "prefix(v, 'a')", ""])
        self.assertEqual(val, "a1 a2 a3")

        val = bb.filter.eval_expression("1 2 3", "\n \n prefix(v, 'a') \n \n")
        self.assertEqual(val, "a1 a2 a3")

    def test_nested(self):
        val = bb.filter.apply_filters("1 2 3", ["prefix(prefix(v, 'a'), 'b')"])
        self.assertEqual(val, "ba1 ba2 ba3")

        val = bb.filter.apply_filters("1 2 3", ["prefix(prefix(v, 'b'), 'a')"])
        self.assertEqual(val, "ab1 ab2 ab3")

    def test_extra_proc(self):
        def get_foo():
            return "foo"

        val = bb.filter.apply_filters(
            "1 2 3",
            ["prefix(v, get_foo())"],
            extra_globals={
                "get_foo": get_foo,
            },
        )
        self.assertEqual(val, "foo1 foo2 foo3")

    def test_filter_order(self):
        val = bb.filter.apply_filters("1 2 3", ["prefix(v, 'a')", "prefix(v, 'b')"])
        self.assertEqual(val, "ba1 ba2 ba3")

        val = bb.filter.apply_filters("1 2 3", ["prefix(v, 'b')", "prefix(v, 'a')"])
        self.assertEqual(val, "ab1 ab2 ab3")

        val = bb.filter.apply_filters("1 2 3", ["prefix(v, 'a')", "suffix(v, 'b')"])
        self.assertEqual(val, "a1b a2b a3b")

        val = bb.filter.apply_filters("1 2 3", ["suffix(v, 'b')", "prefix(v, 'a')"])
        self.assertEqual(val, "a1b a2b a3b")

    def test_remove(self):
        val = bb.filter.apply_filters("1 2 3", ["remove(v, ['2'])"])
        self.assertEqual(val, "1 3")

        val = bb.filter.apply_filters("1,2,3", ["remove(v, ['2'], ',')"])
        self.assertEqual(val, "1,3")

        val = bb.filter.apply_filters("1 2 3", ["remove(v, ['4'])"])
        self.assertEqual(val, "1 2 3")

        val = bb.filter.apply_filters("1 2 3", ["remove(v, ['1', '2'])"])
        self.assertEqual(val, "3")

        val = bb.filter.apply_filters("1 2 3", ["remove(v, '2')"])
        self.assertEqual(val, "1 3")

        val = bb.filter.apply_filters("1 2 3", ["remove(v, '4')"])
        self.assertEqual(val, "1 2 3")

        val = bb.filter.apply_filters("1 2 3", ["remove(v, '1 2')"])
        self.assertEqual(val, "3")

    def test_newline_eval(self):
        val = bb.filter.eval_expression(
            "1\n2\n3\n",
            "remove(v, ['2'], '\\n') \n remove(v, ['1'], '\\n')",
        )
        self.assertEqual(val, "3\n")
