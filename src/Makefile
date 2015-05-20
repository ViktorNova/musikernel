#!/usr/bin/make -f

PREFIX ?= /usr
DESTDIR ?=
SBSMS_PREFIX = $(PREFIX)/lib/$(PYDAW_VERSION)/sbsms
PYDAW_VERSION = $(shell cat major-version.txt)
MK_DIR = $(DESTDIR)$(PREFIX)/lib/$(PYDAW_VERSION)

# --------------------------------------------------------------

all:
	make deps
	make pydaw_src

mingw64:
	/mingw64/bin/mingw32-make.exe mingw_deps_clean
	CC=/mingw64/bin/gcc.exe /mingw64/bin/mingw32-make.exe

mingw32:
	/mingw32/bin/mingw32-make.exe mingw_deps_clean
	CC=/mingw32/bin/gcc.exe /mingw32/bin/mingw32-make.exe

clang:
	OPTIMIZE_FLAGS= CC=clang make

native:
	make PLAT_FLAGS=" -march=native " CFLAGS+=" -O2 "

pydaw_src:
	make -C pydaw PREFIX=$(PREFIX) CFLAGS+=" -O2 "
	make -C pydaw_render

native_src:
	make -C pydaw PREFIX=$(PREFIX) CFLAGS+=" -O2 " PLAT_FLAGS=" -march=native "
	make -C pydaw_render PLAT_FLAGS=" -march=native "

rpm:
	../rpm.py

deb:
	( ./deb.py --default-version || \
	(echo "You may need to run 'make deps' and/or ./ubuntu_deps.sh first"  \
	&& false ))

# --------------------------------------------------------------

deps:
	make mingw_deps
	cd pydaw/pyliblo-0.9.2 && python3 setup.py build && cp build/lib*/liblo* ../python/libpydaw

mingw_deps:
	make -C pydaw/midicomp && cp pydaw/midicomp/midicomp pydaw/python/libpydaw
	cd sbsms && ( ./configure || ./configure --enable-sse=no ) && make
	cd sbsms/cli && make

mingw_deps_clean:
	make -C pydaw/midicomp clean
	make -C sbsms clean
	make -C sbsms/cli clean

deps_clean:
	make deps_clean
	cd pydaw/pyliblo-0.9.2 && python3 setup.py clean

# --------------------------------------------------------------

install:
	install -d $(MK_DIR)
	install -d $(MK_DIR)/sbsms
	install -d $(MK_DIR)/sbsms/bin
	make -C pydaw PREFIX=$(PREFIX) DESTDIR=$(DESTDIR) install
	install sbsms/cli/sbsms $(MK_DIR)/sbsms/bin
	make -C pydaw_render DESTDIR=$(DESTDIR) PREFIX=$(PREFIX) install

install_mingw:
	install -d $(MK_DIR)
	make -C pydaw PREFIX=$(PREFIX) DESTDIR=$(DESTDIR) install_mingw
	make -C pydaw_render DESTDIR=$(DESTDIR) PREFIX=$(PREFIX) install

# --------------------------------------------------------------

uninstall:
	rm -f $(DESTDIR)$(PREFIX)/bin/$(PYDAW_VERSION)*
	rm -rf $(MK_DIR)

# --------------------------------------------------------------

clean:
	make -C pydaw clean
	make -C pydaw_render clean



