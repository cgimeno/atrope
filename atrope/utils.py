# -*- coding: utf-8 -*-

# Copyright 2014 Alvaro Lopez Garcia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import errno
import hashlib
import shutil
import os

import prettytable


def print_list(objs, fields, sortby=None):
    pt = prettytable.PrettyTable([f for f in fields], caching=False)
    pt.align = 'l'
    for o in objs:
        row = []
        for field in fields:
            row.append(o.get(field, None))
        pt.add_row(row)

    result = pt.get_string(sortby=sortby)
    print(result)


def print_dict(d, dict_property="Property", dict_value="Value", wrap=0):
    pt = prettytable.PrettyTable([dict_property, dict_value], caching=False)
    pt.align = 'l'
    for k, v in sorted(d.items()):
        # if value has a newline, add in multiple rows
        # e.g. fault with stacktrace
        if v and isinstance(v, basestring) and r'\n' in v:
            lines = v.strip().split(r'\n')
            col1 = k
            for line in lines:
                pt.add_row([col1, line])
                col1 = ''
        else:
            if v is None:
                v = '-'
            pt.add_row([k, v])

    result = pt.get_string()
    print(result)


def rmtree(path):
    """Recursively remove a directory."""
    try:
        shutil.rmtree(path)
    except OSError as exc:
        if exc.errno == errno.ENOENT:
            pass
        else:
            raise


def makedirs(path):
    """Recursive directory creation function.

    If the directory exists it will not raise an exception.

    :param path: Directory to create
    """
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            if not os.path.isdir(path):
                raise
        else:
            raise


def get_file_checksum(path, block_size=2 ** 20):
    sha512 = hashlib.sha512()
    with open(path, "rb") as f:
        buf = f.read(block_size)
        while len(buf) > 0:
            sha512.update(buf)
            buf = f.read(block_size)
    return sha512


def yn_question(msg="Enabled", default=True):
    if default is True:
        default = "y"
    else:
        default = "n"

    yn = raw_input("%s (y/n) [%s]: " % (msg, default)).lower() or default
    if yn == "y":
        return True
    elif yn == "n":
        return False
    else:
        print "Please enter one of 'Y' or 'N'."
        return yn_question()
