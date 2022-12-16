#
# Copyright (C) 2022 Garmin Ltd. or its subsidiaries
#
# SPDX-License-Identifier: GPL-2.0-only
#

import json
import builtins

# A select initial set of builtins that are supported in filter expressions
ALLOWED_BUILTINS = (
    "all",
    "any",
    "bin",
    "bool",
    "chr",
    "enumerate",
    "eval",
    "float",
    "format",
    "hex",
    "int",
    "len",
    "map",
    "max",
    "min",
    "oct",
    "ord",
    "pow",
    "str",
    "sum",
)

FILTERS = {k: getattr(builtins, k) for k in ALLOWED_BUILTINS}


def apply_filters(val, expressions, *, default_globals=True, extra_globals={}):
    if default_globals:
        g = FILTERS.copy()
    else:
        g = {}

    g.update(extra_globals)

    # Purposely blank out __builtins__ which prevents users from
    # calling any normal builtin python functions
    g["__builtins__"] = {}

    for e in expressions:
        if not e:
            continue

        # Set val as a local so it can be cleared out while keeping the globals
        l = {"v": val}

        val = eval(e, g, l)

    return val


def eval_expression(val, expression, *, default_globals=True, extra_globals={}):
    return apply_filters(
        val,
        [e.strip() for e in expression.split("\n")],
        default_globals=default_globals,
        extra_globals=extra_globals,
    )


def filter_proc(*, name=None):
    """
    Decorator to mark a function as a filter that can be called in
    `apply_filters`. The `name` argument can be used to specify an alternate
    name for the function if the actual name is not desired.
    """

    def inner(func):
        global FILTERS
        nonlocal name
        if name is None:
            name = func.__name__
        FILTERS[name] = func
        return func

    return inner


@filter_proc()
def suffix(val, suffix):
    return " ".join(v + suffix for v in val.split())


@filter_proc()
def prefix(val, prefix):
    return " ".join(prefix + v for v in val.split())


@filter_proc()
def sort(val):
    return " ".join(sorted(val.split()))


@filter_proc()
def remove(val, remove, sep=None):
    if isinstance(remove, str):
        remove = remove.split(sep)
    new = [i for i in val.split(sep) if not i in remove]

    if not sep:
        return " ".join(new)
    return sep.join(new)


@filter_proc()
def from_json(val):
    return json.loads(val)
