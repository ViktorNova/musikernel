#!/usr/bin/env python3
"""
This file is part of the MusiKernel project, Copyright MusiKernel Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

"""

import os
import shutil
import urllib.request


URL = ("https://copr-be.cloud.fedoraproject.org/results/musikernel/"
    "musikernel/fedora-{FED_VER1}-{ARCH1}/"
    "{MK_MAJOR}-{MK_MINOR}-1.fc{FED_VER2}/"
    "{MK_MAJOR}-{MK_MINOR}-1.fc{FED_VER3}.{ARCH2}.rpm")

FED_VER = ((21, 21, 21), (22, 21, 22))
ARCHS = (("x86_64", "x86_64"), ("i386", "i686"))

with open("../src/minor-version.txt") as fh:
    MK_MINOR = fh.read().strip()

with open("../src/major-version.txt") as fh:
    MK_MAJOR = fh.read().strip()

DIR = "../packages"
if not os.path.isdir(DIR):
    os.mkdir(DIR)

for fed_ver1, fed_ver2, fed_ver3 in FED_VER:
    for arch1, arch2 in ARCHS:
        url = URL.format(
            FED_VER1=fed_ver1, FED_VER2=fed_ver2, FED_VER3=fed_ver3,
            ARCH1=arch1, ARCH2=arch2, MK_MINOR=MK_MINOR, MK_MAJOR=MK_MAJOR)
        file_name = os.path.join(DIR, url.rsplit("/", 1)[1])
        try:
            with urllib.request.urlopen(url) as response, \
            open(file_name, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        except Exception as ex:
            print("Error downloading {}".format(url))
            print(ex)

