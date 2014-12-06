#!/bin/sh
wc -l pydaw/src/*.c pydaw/src/*.h pydaw/libmodsynth/* \
pydaw/libmodsynth/lib/* pydaw/libmodsynth/*/*/* pydaw/plugins/*/*

echo "^^^ Lines of C code"

wc -l pydaw/python/*.py pydaw/python/lib*/*.py pydaw/python/mkplugins/*.py

echo "^^^ Lines of Python code"

