#!/bin/sh

rm *.zip
wget https://github.com/j3ffhubb/musikernel/archive/master.zip
python3 pkgbuild.py
rm *.tar.xz *.exe *.zip
dos2unix PKGBUILD  #why the fuck this is necessary I don't understand
makepkg-mingw -Cfs


