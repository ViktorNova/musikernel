#Notice to packagers

Several dependencies have recently changed, please update accordingly.

Starting with 15.02.2 , MusiKernel is ported to PyQt5 and is no longer compatible with PyQt4.  Distros that currently package PyQt5 include Fedora 21, Ubuntu 14.04+ or Debian 8.

#Supported platforms

Linux:  Latest Fedora and Ubuntu LTS have first tier support, known to work in Debian8, Arch and probably most other distros.

Mac OSX:  It's possible to build and run in OSX Yosemite (minus midicomp and sbsms), but due to the many issues with Yosemite (probably mostly because of LLVM/Clang), you probably will experience frequent crashes.  You might have better luck with Mavericks or earlier, but that has not been tested.  Homebrew can satisfy MusiKernel's dependencies, and it is recommended that you use GCC instead of Clang.

Windows (Cygwin):  Everything works, and has decent performance and stability, but unfortunately the only available back-end is MME, so you probably won't be able to get less than 4096 samples of latency.  Getting Cygwin's X Server to start is flaky.

Windows (Mingw32):  Stability issues, not recommended.

Windows (MSVC): If you're a masochist willing to setup the Visual Studio project to compile and build MusiKernel and all of it's dependencies, then it probably works pretty well.  Windows package maintainers and .vcproj files will be gladly accepted, please submit an issue to the MusiKernel issue tracker if interested.

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

