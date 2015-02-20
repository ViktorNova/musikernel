#Notice

Starting with 15.02.2 , MusiKernel is ported to PyQt5 and is no longer compatible with PyQt4.  If you are using an older Linux distro that does not package PyQt5, you should stick to 15.02.1 or (ideally) switch to a more up-to-date distro like Fedora 21 or Ubuntu 14.04.  This was necessary to simplify the forthcoming Windows and Mac ports.

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

