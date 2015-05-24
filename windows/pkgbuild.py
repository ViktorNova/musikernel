#/usr/bin/env python3
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

import hashlib
import os
import shutil
import urllib.request

CWD = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(CWD, "..", "src", "minor-version.txt")) as fh:
    MINOR_VERSION = fh.read().strip()

with open(os.path.join(CWD, "..", "src", "major-version.txt")) as fh:
    MAJOR_VERSION = fh.read().strip()

url = "https://github.com/j3ffhubb/musikernel/archive/master.zip"
file_name = os.path.join(CWD, "musikernel-master.zip")

#with urllib.request.urlopen(url) as response, \
#open(file_name, 'wb') as out_file:
#    shutil.copyfileobj(response, out_file)

with open(file_name, "rb") as fh:
    MD5 = hashlib.md5(fh.read()).hexdigest()

PKGBUILD = os.path.join(CWD, "PKGBUILD")
PKGBUILD_TEMPLATE = PKGBUILD + ".txt"

with open(PKGBUILD_TEMPLATE) as fh_t, open(PKGBUILD, "w") as fh_p:
    tmp_str = fh_t.read()
    tmp_str = tmp_str.format(
        major_version=MAJOR_VERSION, minor_version=MINOR_VERSION,
        zip_md5sum=MD5)
    fh_p.write(tmp_str)
