#!/usr/bin/python3
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
import sys

with open("../major-version.txt") as f_file:
    PYDAW_VERSION = f_file.read().strip()
BIN = "{}_render".format(PYDAW_VERSION)
PROJECT = "{}/{}/default-project".format(
    os.path.expanduser("~"), PYDAW_VERSION)

print(locals())

TOOL, CORES = sys.argv[1:]

TOOLS = {
    "benchmark": "make clean && make release && "
        "./{BIN} {PROJECT} test.wav 0 0 3 0 44100 512 {CORES} 1 --no-file",
    "valgrind": "make clean && make debug && "
        "valgrind --alignment=16 --track-origins=yes "
        "./{BIN}-dbg {PROJECT} test.wav 0 0 3 3 44100 512 1 0 --no-file",
    "perf": "make clean && make release && "
        "perf stat -e cache-references,cache-misses,dTLB-loads,"
        "dTLB-load-misses,iTLB-loads,iTLB-load-misses,L1-dcache-loads,"
        "L1-dcache-load-misses,L1-icache-loads,L1-icache-load-misses,"
        "branch-misses,LLC-loads,LLC-load-misses "
        "./{BIN} {PROJECT} test.wav 0 0 3 0 44100 512 {CORES} 1 --no-file",
    "profile": "make clean && make gprof && "
        "./{BIN} {PROJECT} test.wav 0 0 3 3 44100 512 {CORES} 1 "
        "&& gprof ./{BIN} > profile.txt && gedit profile.txt",
}

os.system(TOOLS[TOOL].format(BIN=BIN, PROJECT=PROJECT, CORES=CORES))
