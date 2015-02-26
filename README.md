#Notice to packagers

Several dependencies have recently changed, please update accordingly.

Starting with 15.02.2 , MusiKernel is ported to PyQt5 and is no longer compatible with PyQt4.  Distros that currently package PyQt5 include Fedora 21, Ubuntu 14.04+ or Debian 8.

#What is MusiKernel ?

MusiKernel is DAWs, plugins, and a new approach to developing an audio software ecosystem.  By promoting centralized development and quality control with maximal code re-use, MusiKernel aims to avoid many of the compatibility problems that have plagued traditional host/plugin architectures.

#How to build:

#Ubuntu/Debian distros:

cd [musikernel dir]/src
 
./ubuntu_deps.sh   # as root

make deps

make deb  # as root

cd ../ubuntu

dpkg -i musikernel[your_version].deb  # as root

#Fedora based distros:

cd [musikernel src dir]/src

./fedora_deps.sh

make rpm

cd ~/rpmbuild/RPMS/[your arch]

sudo yum localinstall musikernel[version number].rpm

#All others:

 # [figure out the dependencies based on the Fedora or Ubuntu dependencies]

cd [musikernel src dir]/src

make

 # You can specify DESTDIR or PREFIX if packaging, the result is fully relocatable

make install

