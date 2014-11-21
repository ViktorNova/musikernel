#!/bin/sh
wc -l pydaw/src/*.c pydaw/src/*.h pydaw/libmodsynth/* \
pydaw/libmodsynth/lib/* pydaw/libmodsynth/*/*/*

echo "^^^ Lines of C code"

wc -l pydaw/python/*.py pydaw/python/libpydaw/*.py \
pydaw/python/libmk/*.py pydaw/python/mkplugins/*

echo "^^^ Lines of Python code"
