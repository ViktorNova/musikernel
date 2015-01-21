#!/usr/bin/env python3

"""
This file is part of the MusiKernel project, Copyright MusiKernel Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

import os
import shutil

with open("src/major-version.txt") as f_file:
    MAJOR_VERSION = f_file.read().strip()

DESTDIR = os.sep + MAJOR_VERSION

if os.path.isdir(DESTDIR):
    OLD_DIR = "{}-OLD".format(DESTDIR)
    if os.path.isdir(OLD_DIR):
        shutil.rmtree(OLD_DIR)
    shutil.move(DESTDIR, OLD_DIR)
else:
    OLD_DIR = None

os.mkdir(DESTDIR)

f_cwd = os.path.join(os.path.abspath(os.path.dirname(__file__)), "src")

os.chdir(f_cwd)

f_retcode = os.system(
    "make clean && make && make DESTDIR={} install".format(DESTDIR))

if(f_retcode):
    print("Error:  clean, build and install returned {}".format(f_retcode))
