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
    MK_VERSION = f_file.read().strip()

BIN = "./{}_render".format(MK_VERSION)
HOME = os.path.expanduser("~")
LAST_PROJECT = os.path.join(HOME, MK_VERSION, "config", "last-project.txt")

if os.path.exists(LAST_PROJECT):
    with open(LAST_PROJECT) as f_file:
        PROJECT = os.path.dirname(f_file.read().strip())
else:
    PROJECT = os.path.join(HOME, MK_VERSION, "default-project")

TOOLS = {
    "benchmark": "make clean > /dev/null 2>&1 && "
        "make release > /dev/null 2>&1 && "
        "{BIN} '{PROJECT}' test.wav 0 0 3 0 {SR} 512 {CORES} 1 --no-file",
    "valgrind": "make clean > /dev/null 2>&1 && "
        "make debug > /dev/null 2>&1 && "
        "valgrind --alignment=16 --track-origins=yes "
        "{BIN}-dbg '{PROJECT}' test.wav 0 0 3 3 {SR} 512 1 0 --no-file",
    "perf": "make clean > /dev/null 2>&1 && "
        "make release > /dev/null 2>&1 && "
        "perf stat -e cache-references,cache-misses,dTLB-loads,"
        "dTLB-load-misses,iTLB-loads,iTLB-load-misses,L1-dcache-loads,"
        "L1-dcache-load-misses,L1-icache-loads,L1-icache-load-misses,"
        "branch-misses,LLC-loads,LLC-load-misses "
        "{BIN} '{PROJECT}' test.wav 0 0 3 0 {SR} 512 {CORES} 1 --no-file",
    "profile": "make clean && make gprof && "
        "{BIN} '{PROJECT}' test.wav 0 0 3 3 {SR} 512 {CORES} 1 "
        "&& gprof {BIN} > profile.txt && gedit profile.txt",
    "pahole": "make clean && make debug && pahole {BIN}",
}

if len(sys.argv) < 2 or sys.argv[1] not in TOOLS:
    print("Usage: {} {} [CORES=1] [SAMPLE_RATE=44100]".format(
        os.path.basename(__file__), "|".join(TOOLS)))
    exit(1)

TOOL = sys.argv[1]

if len(sys.argv) >= 3:
    CORES = int(sys.argv[2])
    assert(CORES >= 0 and CORES < 32)
else:
    CORES = 1

if len(sys.argv) >= 4:
    SR = int(sys.argv[3])
    assert(SR >= 11025 and SR <= 384000)
else:
    SR = 44100

os.system(TOOLS[TOOL].format(BIN=BIN, PROJECT=PROJECT, CORES=CORES, SR=SR))
