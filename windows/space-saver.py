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

# This script for for creating clean, minimal installs of MSYS2, suitable
# for creating NSIS installers from

import fnmatch
import os
import shutil
import stat

SAVED = 0

DELETE_DIRS = (
    ('share', 'qt5', 'doc'),
    ('mingw64', 'share', 'doc'),
    ('mingw64', 'include'),
    ('share', 'man'),
    ('lib', 'python3.4', 'test', '__pycache__'))

# TODO:  implement this:

DELETE_FILES = (
    ('bin', 'tiff*.exe'),
    ('bin', 'q*.exe'),
    ('bin', 'sndfile*.exe'),
    ('bin', 'pm-*.exe'),
    #('bin', 'x86_64-w64-*.exe'),
)

# TODO:  List of Qt*.dll's to delete...

fnmatch.filter()

WARN_SIZE = (1024 * 1024 * 5)

def on_error(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=on_error)``
    """
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


def delete_it_all(a_path):
    global SAVED

    for dir_tuple in DELETE_DIRS:
        path = os.path.join(a_path, *dir_tuple)
        if os.path.isdir(path):
            shutil.rmtree(path, onerror=on_error)

    for (dirpath, dirnames, filenames) in os.walk(a_path):
        filename_set = set(filenames)
        dir_size = 0
        for name in filenames:
            path = os.path.join(dirpath, name)
            size = os.path.getsize(path)
            dir_size += size
            if name.endswith(".a") or (
            name.endswith("d.dll") and name[:-5] + ".dll" in filename_set):
                print("Deleting " + path)
                os.remove(path)
                SAVED += size
#            elif size >= WARN_SIZE:
#                print("Warning:  '{}' is {} MB".format(
#                    path, round(size / (1024 * 1024), 2)))
        if dir_size > WARN_SIZE:
            print("Warning:  '{}' is {} MB".format(dirpath, dir_size))
    pkg_dir = os.path.join(a_path, r'var\cache\pacman\pkg')
    if os.path.isdir(pkg_dir) and os.listdir(pkg_dir):
        print("Warning:  '{}' is not empty".format(pkg_dir))

delete_it_all(r'C:\musikernel1-64\mingw64')

MB = round(SAVED / (1024 * 1024), 2)

print("Saved {} MB (not including directories)".format(MB))
