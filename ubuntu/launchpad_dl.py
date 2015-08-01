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
    "musikernel/fedora-{FED_VER}-{ARCH1}/"
    "{MK_MAJOR}-{MK_MINOR}-1.fc{FED_VER}/"
    "{MK_MAJOR}-{MK_MINOR}-1.fc{FED_VER}.{ARCH2}.rpm")

URL = ("https://launchpad.net/~musikernel/+archive/ubuntu/musikernel1/"
    "+files/{MK_MAJOR}_{MK_MINOR}-1_{ARCH}.deb")

ARCHS = ("amd64",)

with open("../src/minor-version.txt") as fh:
    MK_MINOR = fh.read().strip()

with open("../src/major-version.txt") as fh:
    MK_MAJOR = fh.read().strip()

DIR = "../packages"
if not os.path.isdir(DIR):
    os.mkdir(DIR)

for arch in ARCHS:
    url = URL.format(ARCH=arch, MK_MINOR=MK_MINOR, MK_MAJOR=MK_MAJOR)
    file_name = os.path.join(DIR, url.rsplit("/", 1)[1])
    file_name = file_name.rsplit('.', 1)[0] + "-ubuntu1404.deb"
    try:
        with urllib.request.urlopen(url) as response, \
        open(file_name, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
    except Exception as ex:
        print("Error downloading {}".format(url))
        print(ex)
