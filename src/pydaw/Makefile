#!/usr/bin/make -f

CC  ?= gcc

PREFIX ?= /usr
PYDAW_VERSION = $(shell cat ../major-version.txt)

#Default flags are mostly x86 specific
PLAT_FLAGS     ?= -mstackrealign -msse -msse2 -msse3 -mfpmath=sse \
-mtune=generic

CACHE_LINE_SIZE = 64  # $(shell getconf LEVEL1_DCACHE_LINESIZE)

BASE_FLAGS     = -ffast-math -fprefetch-loop-arrays \
-floop-optimize -fsingle-precision-constant -funroll-loops -Wall \
-Isrc -fstrength-reduce -fstrict-aliasing \
-finline-functions -fno-stack-protector \
-DCACHE_LINE_SIZE=$(CACHE_LINE_SIZE)


BUILD_CFLAGS   = $(PLAT_FLAGS) $(BASE_FLAGS) $(CFLAGS)
MATH_LIB_FLAG ?= -lm
RT_LIB_FLAG ?= -lrt
ALSA_FLAG ?= $(shell pkg-config --libs alsa)

LINK_CFLAGS  = $(RT_LIB_FLAG) -lpthread \
$(LIBLO_FLAG) -lportmidi -lportaudio $(LDFLAGS) \
$(shell pkg-config --libs sndfile fftw3f liblo) $(ALSA_FLAG) $(MATH_LIB_FLAG)

C_OBJS   = src/main.o

# --------------------------------------------------------------

all:
	make lib
	make dbg
	make eng

dbg:
	rm -f src/*.o $(PYDAW_VERSION)-engine  $(PYDAW_VERSION)-engine-dbg ; echo
	make CFLAGS+=" -O0 -g -gdwarf-3 " $(PYDAW_VERSION)-engine
	mv $(PYDAW_VERSION)-engine $(PYDAW_VERSION)-engine-dbg

eng:
	rm -f src/*.o $(PYDAW_VERSION)-engine ; echo
	rm -f $(PYDAW_VERSION)-engine src/*.o
	make CFLAGS+=" -O2 " $(PYDAW_VERSION)-engine

lib:
	rm -f src/*.o $(PYDAW_VERSION)-engine ; echo
	make CFLAGS+=" -O0 -g -gdwarf-3 -fPIC -DMK_DLL " \
		LDFLAGS+=" -shared " $(PYDAW_VERSION)-engine
	mv $(PYDAW_VERSION)-engine $(PYDAW_VERSION).so

# --------------------------------------------------------------

$(PYDAW_VERSION)-engine: $(C_OBJS)
	$(CC) $(C_OBJS) $(LINK_CFLAGS) -o $@

# --------------------------------------------------------------

.c.o:
	$(CC) -c $< $(BUILD_CFLAGS) -o $@

# --------------------------------------------------------------

install:
	rm -rf python/*.pyc python/libpydaw/*.pyc python/*~ \
	python/libpydaw/*~ python/core python/*/__pycache__ \
	python/mkplugins/__pycache__
	install -d $(DESTDIR)$(PREFIX)/bin
	install -m 755 $(PYDAW_VERSION) $(DESTDIR)$(PREFIX)/bin
	install -d $(DESTDIR)$(PREFIX)/lib/$(PYDAW_VERSION)
	install -d $(DESTDIR)$(PREFIX)/lib/$(PYDAW_VERSION)/pydaw
	install -m 755 $(PYDAW_VERSION)-engine-dbg $(DESTDIR)$(PREFIX)/bin
	install -s -m 4755 $(PYDAW_VERSION)-engine $(DESTDIR)$(PREFIX)/bin
	install -s -m 755 $(PYDAW_VERSION)-engine \
	$(DESTDIR)$(PREFIX)/bin/$(PYDAW_VERSION)-engine-no-root
	cp -r python $(DESTDIR)$(PREFIX)/lib/$(PYDAW_VERSION)/pydaw
	install -d $(DESTDIR)$(PREFIX)/lib/$(PYDAW_VERSION)/pydaw/python/mkengine
	install -m 644 $(PYDAW_VERSION).so $(DESTDIR)$(PREFIX)/lib/$(PYDAW_VERSION)/pydaw/python/mkengine
	cp -r themes $(DESTDIR)$(PREFIX)/lib/$(PYDAW_VERSION)
	cp -r presets $(DESTDIR)$(PREFIX)/lib/$(PYDAW_VERSION)
	cp -r share $(DESTDIR)$(PREFIX)
	#locale/Makefile.py $(DESTDIR)$(PREFIX)
	install -m 644 ../major-version.txt \
		$(DESTDIR)$(PREFIX)/lib/$(PYDAW_VERSION)
	install -m 644 ../minor-version.txt \
		$(DESTDIR)$(PREFIX)/lib/$(PYDAW_VERSION)
	#Add the Git revision to the version.txt file if possible
	@       if [ -e /usr/bin/git ] && [ -e ../../.git ]; then \
                        echo "\n\nGit: " `/usr/bin/git rev-parse HEAD` >> \
			$(DESTDIR)$(PREFIX)/lib/$(PYDAW_VERSION)/minor-version.txt ; \
                fi

clean:
	rm -f src/*.o *.so $(PYDAW_VERSION)-engine* core python/core  \
	*.pyo *.pyc */*.pyo */*.pyc */*/*.pyo */*/*.pyc \
	*~ */*~ */*/*~ */*/*/*~ 

