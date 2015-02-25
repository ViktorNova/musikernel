#!/bin/bash

if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root, use sudo or su" 1>&2
   exit 1
fi

apt-get update

apt-get install -y libasound2-dev \
libportmidi-dev portaudio19-dev liblo-dev g++ libsndfile1-dev \
libtool gdb debhelper dh-make build-essential automake autoconf \
python3-pyqt5 python3 squashfs-tools genisoimage \
python3-scipy python3-numpy libsamplerate0-dev \
libfftw3-dev gcc python3-dev libsbsms-dev libcpufreq-dev \
libav-tools lame vorbis-tools gettext rubberband-cli 

