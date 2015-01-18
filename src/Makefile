#!/usr/bin/make -f

PREFIX ?= /usr
DESTDIR ?=
SBSMS_PREFIX = $(PREFIX)/lib/$(PYDAW_VERSION)/sbsms
RUBBERBAND_PREFIX = $(PREFIX)/lib/$(PYDAW_VERSION)/rubberband
PYDAW_VERSION = $(shell cat major-version.txt)
MK_DIR = $(DESTDIR)$(PREFIX)/lib/$(PYDAW_VERSION)

# --------------------------------------------------------------

all:
	make deps
	make pydaw_src

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
	( sudo ./deb.py --default-version || \
	(echo "You may need to run 'make deps' and/or ./ubuntu_deps.sh first"  \
	&& false ))

# --------------------------------------------------------------

deps:
	make -C pydaw/midicomp && cp pydaw/midicomp/midicomp pydaw/python/libpydaw
	cd pydaw/pyliblo-0.9.2 && python3 setup.py build && cp build/lib*/liblo* ../python/libpydaw
	cd pydaw/portaudio && ./configure --with-jack=no --with-oss=no
	make -C pydaw/portaudio
	cp pydaw/portaudio/lib/.libs/libportaudio.*.2.0.0 pydaw/python/libpydaw/libportaudio.so
	cd sbsms && ( ./configure || ./configure --enable-sse=no ) && make
	cd sbsms/cli && make
	cd rubberband && ./configure --prefix=$(RUBBERBAND_PREFIX) && make

deps_clean:
	make -C pydaw/midicomp clean
	cd pydaw/pyliblo-0.9.2 && python3 setup.py clean
	make -C pydaw/portaudio clean
	make -C sbsms clean
	make -C sbsms/cli clean
	make -C rubberband clean
		
# --------------------------------------------------------------

install:
	install -d $(MK_DIR)
	install -d $(MK_DIR)/sbsms
	install -d $(MK_DIR)/rubberband
	install -d $(MK_DIR)/rubberband/bin
	make -C pydaw PREFIX=$(PREFIX) DESTDIR=$(DESTDIR) install
	make -C sbsms/cli PREFIX=$(SBSMS_PREFIX) \
	DESTDIR=$(DESTDIR) install
	install rubberband/bin/rubberband $(MK_DIR)/rubberband/bin
	make -C pydaw_render DESTDIR=$(DESTDIR) PREFIX=$(PREFIX) install

# --------------------------------------------------------------

clean:
	make -C pydaw clean
	make -C pydaw_render clean



