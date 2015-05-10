- **Twitter:** Follow @musikernel for the latest news and release announcements
- [**Screenshots**](http://www.kvraudio.com/product/musikernel-by-musikernel)
- [How to install](#)
			- [Windows](#)
			- [Fedora](#)
			- [Ubuntu](#)
- [How to Build](#)
			- [Ubuntu/Debian](#)
			- [Fedora](#)
			- [All Others](#)
- [What is MusiKernel?](#)

###How to Install

######Windows

LiveOS image available [here](https://drive.google.com/folderview?id=0BycGQs-5oRdffkthTmo2Q0lQLWNCblFkZkhodTJ0VlJlaXRMMzl4SXJ5ajI4YUR2WTFReUE&usp=sharing), you can follow the instructions to create a bootable USB drive for running MusiKernel without installing anything to your PC.

######Fedora

From [here](https://copr.fedoraproject.org/coprs/musikernel/musikernel/)

```
sudo dnf copr enable -y musikernel/musikernel
sudo dnf install -y musikernel1
```

RPM packages can be downloaded directly from [here](https://copr-be.cloud.fedoraproject.org/results/musikernel/musikernel/)

######Ubuntu

Follow the instructions in the "Adding this PPA to your system" section [here](https://launchpad.net/~musikernel/+archive/ubuntu/musikernel1), then:

`sudo apt-get update && sudo apt-get install musikernel1`

You can download the .deb package(s) directly by clicking [here](https://launchpad.net/~musikernel/+archive/ubuntu/musikernel1/+packages), clicking "View package details", clicking the arrow next to the package, then clicking on the package name link.

###How to Build

######Ubuntu/Debian

```
cd [musikernel dir]/src 
./ubuntu_deps.sh   # as root
make deps
make deb  # as root
cd ../ubuntu
dpkg -i musikernel[your_version].deb  # as root
```

######Fedora

```
cd [musikernel src dir]/src
./fedora_deps.sh
make rpm
cd ~/rpmbuild/RPMS/[your arch]
sudo yum localinstall musikernel[version number].rpm
```

######All Others

```
# figure out the dependencies based on the Fedora or Ubuntu dependencies
cd [musikernel src dir]/src
make
# You can specify DESTDIR or PREFIX if packaging,
# the result is fully relocatable
make install
```

###What is MusiKernel?

MusiKernel is DAWs/hosts, instrument & effect plugins, and a new approach to developing an audio software ecosystem.  By promoting centralized development and quality control with maximal code re-use, MusiKernel aims to avoid many of the compatibility problems that have plagued traditional host/plugin architectures.

MusiKernel's UI is powered entirely by Python3 and PyQt5.  MusiKernel's audio/MIDI engine is written in C (C89 dialect) for maximum performance and low memory usage.

