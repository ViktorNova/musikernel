# Compiling for ARM:

# Install all required dependencies for Debian or Ubuntu
./ubuntu_deps.sh

# or for Fedora

./fedora_deps.sh

# Uses -march=native , may work badly on some boards
# make native

PLAT_FLAGS="" make
make install

# or, MusiKernel is fully relocatable, you can do a root-less install 
# to any folder you'd like, and you can even move the folder later.

make PREFIX=$(your prefix) DESTDIR=$(where you want to install it) install

