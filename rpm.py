#!/usr/bin/env python3
"""
This file is part of the MusiKernel project, Copyright MusiKernel Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

import os
import sys
import shutil

DELETE_ME = 'src/pydaw/python/__pycache__'

IS_INSTALL = "-i" in sys.argv

if IS_INSTALL:
    for f_file in os.listdir("."):
        if f_file.startswith("core."):
            print("Deleting {}".format(f_file))
            os.remove(f_file)

#these files may or may not exist, and should not be packaged
if os.path.isdir(DELETE_ME):
    print('Deleting ' + DELETE_ME)
    shutil.rmtree(DELETE_ME)

# invoke sudo at the beginning of the script so that future invokations
# will automatically work without a password
if IS_INSTALL:
    os.system("sudo true")

PYTHON_VERSION = "".join(str(x) for x in sys.version_info[:2])

orig_wd = os.path.dirname(os.path.abspath(__file__))

os.chdir(orig_wd)
os.system("./src.sh")

with open("src/major-version.txt") as f_file:
    MAJOR_VERSION = f_file.read().strip()

with open("src/minor-version.txt") as f_file:
    MINOR_VERSION = f_file.read().strip()

global_version_fedora = MINOR_VERSION.replace("-", ".")
PACKAGE_NAME = "{}-{}".format(
    MAJOR_VERSION, global_version_fedora)

global_home = os.path.expanduser("~")

if not os.path.isdir("{}/rpmbuild".format(global_home)):
    os.system("rpmdev-setuptree")

SPEC_DIR = "{}/rpmbuild/SPECS/".format(global_home)
SOURCE_DIR = "{}/rpmbuild/SOURCES/".format(global_home)

TARBALL_NAME = "{}.tar.gz".format(PACKAGE_NAME)
TARBALL_URL = ("https://github.com/j3ffhubb/musikernel/archive"
    "/{}".format(TARBALL_NAME))

os.system('cp "{}" "{}"'.format(TARBALL_NAME, SOURCE_DIR))

global_spec_file = "{}.spec".format(MAJOR_VERSION,)

if "--native" in sys.argv:
    f_native = "native"
else:
    f_native = ""

f_spec_template = \
"""
Name:           {0}
Version:        {1}

Release:        1%{{?dist}}
Summary:        Digital audio workstations, instrument and effect plugins

License:        GPLv3
URL:            http://github.com/j3ffhubb/musikernel/
Source0:        {2}

Requires:      python3-qt5 alsa-lib-devel liblo-devel \
libsndfile-devel python3-numpy fftw-devel portmidi-devel \
libsamplerate-devel python3-devel vorbis-tools

%define __provides_exclude_from ^/usr/lib/{0}/.*$

%description
MusiKernel is digital audio workstations (DAWs), instrument and effect plugins

%prep
%setup -q

%build
make {3}

%install
export DONT_STRIP=1
rm -rf $RPM_BUILD_ROOT
%make_install

%post
%preun

%files

%defattr(644, root, root)

%attr(4755, root, root) /usr/bin/{0}-engine

%attr(755, root, root) /usr/bin/{0}
%attr(755, root, root) /usr/bin/{0}_render
%attr(755, root, root) /usr/bin/{0}_render-dbg
%attr(755, root, root) /usr/bin/{0}-engine-dbg
%attr(755, root, root) /usr/bin/{0}-engine-no-root
%attr(755, root, root) /usr/lib/{0}/pydaw/python/libpydaw/pydaw_paulstretch.py
%attr(755, root, root) /usr/lib/{0}/pydaw/python/musikernel.py
%attr(755, root, root) /usr/lib/{0}/rubberband/bin/rubberband
%attr(755, root, root) /usr/lib/{0}/sbsms/bin/sbsms
%attr(755, root, root) /usr/lib/{0}/pydaw/python/libpydaw/project_recover.py
%attr(755, root, root) /usr/lib/{0}/pydaw/python/libpydaw/pydaw_device_dialog.py

/usr/lib/{0}/pydaw/python/edmnext.py
/usr/lib/{0}/presets/MODULEX.mkp
/usr/lib/{0}/presets/RAYV.mkp
/usr/lib/{0}/presets/WAYV.mkp
/usr/lib/{0}/pydaw/python/libpydaw/__init__.py
/usr/lib/{0}/pydaw/python/libpydaw/liblo.cpython-{4}m.so
/usr/lib/{0}/pydaw/python/libpydaw/libportaudio.so
/usr/lib/{0}/pydaw/python/libpydaw/midicomp
/usr/lib/{0}/pydaw/python/libpydaw/portaudio.py
/usr/lib/{0}/pydaw/python/libpydaw/portmidi.py
/usr/lib/{0}/pydaw/python/libedmnext/gradients.py
/usr/lib/{0}/pydaw/python/libpydaw/pydaw_history.py
/usr/lib/{0}/pydaw/python/libedmnext/osc.py
/usr/lib/{0}/pydaw/python/libedmnext/project.py
/usr/lib/{0}/pydaw/python/libpydaw/pydaw_util.py
/usr/lib/{0}/pydaw/python/libpydaw/pydaw_widgets.py
/usr/lib/{0}/pydaw/python/libpydaw/staging.py
/usr/lib/{0}/pydaw/python/libpydaw/super_formant_maker.py
/usr/lib/{0}/pydaw/python/libpydaw/translate.py
/usr/lib/{0}/major-version.txt
/usr/lib/{0}/minor-version.txt
/usr/lib/{0}/themes/default/drop-down.png
/usr/lib/{0}/themes/default/euphoria.png
/usr/lib/{0}/themes/default/h-fader.png
/usr/lib/{0}/themes/default/mute-off.png
/usr/lib/{0}/themes/default/mute-on.png
/usr/lib/{0}/themes/default/play-off.png
/usr/lib/{0}/themes/default/play-on.png
/usr/lib/{0}/themes/default/pydaw-knob.png
/usr/lib/{0}/themes/default/rayv.png
/usr/lib/{0}/themes/default/rec-off.png
/usr/lib/{0}/themes/default/rec-on.png
/usr/lib/{0}/themes/default/record-off.png
/usr/lib/{0}/themes/default/record-on.png
/usr/lib/{0}/themes/default/solo-off.png
/usr/lib/{0}/themes/default/solo-on.png
/usr/lib/{0}/themes/default/spinbox-down.png
/usr/lib/{0}/themes/default/spinbox-up.png
/usr/lib/{0}/themes/default/stop-off.png
/usr/lib/{0}/themes/default/stop-on.png
/usr/lib/{0}/themes/default/default.pytheme
/usr/lib/{0}/themes/default/v-fader.png
/usr/share/applications/{0}.desktop
/usr/share/doc/{0}/copyright
/usr/share/pixmaps/{0}.png
#/usr/share/locale/pt_PT/LC_MESSAGES/{0}.mo
#/usr/share/locale/de/LC_MESSAGES/{0}.mo
#/usr/share/locale/fr/LC_MESSAGES/{0}.mo
/usr/lib/{0}/pydaw/python/wavefile/__init__.py
/usr/lib/{0}/pydaw/python/wavefile/libsndfile.py
/usr/lib/{0}/pydaw/python/wavefile/wavefile.py


/usr/lib/{0}/pydaw/python/libpydaw/__init__.pyc
/usr/lib/{0}/pydaw/python/libpydaw/__init__.pyo
/usr/lib/{0}/pydaw/python/libpydaw/portaudio.pyc
/usr/lib/{0}/pydaw/python/libpydaw/portaudio.pyo
/usr/lib/{0}/pydaw/python/libpydaw/portmidi.pyc
/usr/lib/{0}/pydaw/python/libpydaw/portmidi.pyo
/usr/lib/{0}/pydaw/python/libpydaw/project_recover.pyc
/usr/lib/{0}/pydaw/python/libpydaw/project_recover.pyo
/usr/lib/{0}/pydaw/python/libpydaw/pydaw_device_dialog.pyc
/usr/lib/{0}/pydaw/python/libpydaw/pydaw_device_dialog.pyo
/usr/lib/{0}/pydaw/python/libedmnext/gradients.pyc
/usr/lib/{0}/pydaw/python/libedmnext/gradients.pyo
/usr/lib/{0}/pydaw/python/libpydaw/pydaw_history.pyc
/usr/lib/{0}/pydaw/python/libpydaw/pydaw_history.pyo
/usr/lib/{0}/pydaw/python/libedmnext/osc.pyc
/usr/lib/{0}/pydaw/python/libedmnext/osc.pyo
/usr/lib/{0}/pydaw/python/libpydaw/pydaw_paulstretch.pyc
/usr/lib/{0}/pydaw/python/libpydaw/pydaw_paulstretch.pyo
/usr/lib/{0}/pydaw/python/libedmnext/project.pyc
/usr/lib/{0}/pydaw/python/libedmnext/project.pyo
/usr/lib/{0}/pydaw/python/libpydaw/pydaw_util.pyc
/usr/lib/{0}/pydaw/python/libpydaw/pydaw_util.pyo
/usr/lib/{0}/pydaw/python/libpydaw/pydaw_widgets.pyc
/usr/lib/{0}/pydaw/python/libpydaw/pydaw_widgets.pyo
/usr/lib/{0}/pydaw/python/libpydaw/staging.pyc
/usr/lib/{0}/pydaw/python/libpydaw/staging.pyo
/usr/lib/{0}/pydaw/python/libpydaw/super_formant_maker.pyc
/usr/lib/{0}/pydaw/python/libpydaw/super_formant_maker.pyo
/usr/lib/{0}/pydaw/python/edmnext.pyc
/usr/lib/{0}/pydaw/python/edmnext.pyo
/usr/lib/{0}/pydaw/python/libpydaw/translate.pyc
/usr/lib/{0}/pydaw/python/libpydaw/translate.pyo
/usr/lib/{0}/pydaw/python/wavefile/__init__.pyc
/usr/lib/{0}/pydaw/python/wavefile/__init__.pyo
/usr/lib/{0}/pydaw/python/wavefile/libsndfile.pyc
/usr/lib/{0}/pydaw/python/wavefile/libsndfile.pyo
/usr/lib/{0}/pydaw/python/wavefile/wavefile.pyc
/usr/lib/{0}/pydaw/python/wavefile/wavefile.pyo

/usr/lib/{0}/pydaw/python/libpydaw/strings.py
/usr/lib/{0}/pydaw/python/libpydaw/strings.pyc
/usr/lib/{0}/pydaw/python/libpydaw/strings.pyo

/usr/lib/{0}/pydaw/python/libedmnext/strings.py
/usr/lib/{0}/pydaw/python/libedmnext/strings.pyc
/usr/lib/{0}/pydaw/python/libedmnext/strings.pyo

/usr/lib/{0}/pydaw/python/mkplugins/__init__.py
/usr/lib/{0}/pydaw/python/mkplugins/__init__.pyc
/usr/lib/{0}/pydaw/python/mkplugins/__init__.pyo
/usr/lib/{0}/pydaw/python/mkplugins/euphoria.py
/usr/lib/{0}/pydaw/python/mkplugins/euphoria.pyc
/usr/lib/{0}/pydaw/python/mkplugins/euphoria.pyo
/usr/lib/{0}/pydaw/python/mkplugins/modulex.py
/usr/lib/{0}/pydaw/python/mkplugins/modulex.pyc
/usr/lib/{0}/pydaw/python/mkplugins/modulex.pyo
/usr/lib/{0}/pydaw/python/mkplugins/rayv.py
/usr/lib/{0}/pydaw/python/mkplugins/rayv.pyc
/usr/lib/{0}/pydaw/python/mkplugins/rayv.pyo
/usr/lib/{0}/pydaw/python/mkplugins/wayv.py
/usr/lib/{0}/pydaw/python/mkplugins/wayv.pyc
/usr/lib/{0}/pydaw/python/mkplugins/wayv.pyo

/usr/lib/{0}/pydaw/python/mkplugins/mk_delay.py
/usr/lib/{0}/pydaw/python/mkplugins/mk_delay.pyc
/usr/lib/{0}/pydaw/python/mkplugins/mk_delay.pyo
/usr/lib/{0}/pydaw/python/mkplugins/mk_eq.py
/usr/lib/{0}/pydaw/python/mkplugins/mk_eq.pyc
/usr/lib/{0}/pydaw/python/mkplugins/mk_eq.pyo
/usr/lib/{0}/pydaw/python/mkplugins/simple_fader.py
/usr/lib/{0}/pydaw/python/mkplugins/simple_fader.pyc
/usr/lib/{0}/pydaw/python/mkplugins/simple_fader.pyo
/usr/lib/{0}/pydaw/python/mkplugins/simple_reverb.py
/usr/lib/{0}/pydaw/python/mkplugins/simple_reverb.pyc
/usr/lib/{0}/pydaw/python/mkplugins/simple_reverb.pyo
/usr/lib/{0}/pydaw/python/mkplugins/trigger_fx.py
/usr/lib/{0}/pydaw/python/mkplugins/trigger_fx.pyc
/usr/lib/{0}/pydaw/python/mkplugins/trigger_fx.pyo

/usr/lib/{0}/pydaw/python/mkplugins/sidechain_comp.py
/usr/lib/{0}/pydaw/python/mkplugins/sidechain_comp.pyc
/usr/lib/{0}/pydaw/python/mkplugins/sidechain_comp.pyo

/usr/lib/{0}/pydaw/python/mkplugins/mk_channel.py
/usr/lib/{0}/pydaw/python/mkplugins/mk_channel.pyc
/usr/lib/{0}/pydaw/python/mkplugins/mk_channel.pyo
/usr/lib/{0}/pydaw/python/mkplugins/xfade.py
/usr/lib/{0}/pydaw/python/mkplugins/xfade.pyc
/usr/lib/{0}/pydaw/python/mkplugins/xfade.pyo

/usr/lib/{0}/pydaw/python/mkplugins/mk_compressor.py
/usr/lib/{0}/pydaw/python/mkplugins/mk_compressor.pyc
/usr/lib/{0}/pydaw/python/mkplugins/mk_compressor.pyo

/usr/lib/{0}/pydaw/python/mkplugins/mk_vocoder.py
/usr/lib/{0}/pydaw/python/mkplugins/mk_vocoder.pyc
/usr/lib/{0}/pydaw/python/mkplugins/mk_vocoder.pyo

/usr/lib/{0}/pydaw/python/musikernel.pyc
/usr/lib/{0}/pydaw/python/musikernel.pyo

/usr/lib/{0}/pydaw/python/mkplugins/mk_limiter.py
/usr/lib/{0}/pydaw/python/mkplugins/mk_limiter.pyc
/usr/lib/{0}/pydaw/python/mkplugins/mk_limiter.pyo

/usr/lib/{0}/pydaw/python/libmk/__init__.py
/usr/lib/{0}/pydaw/python/libmk/__init__.pyc
/usr/lib/{0}/pydaw/python/libmk/__init__.pyo

/usr/lib/{0}/pydaw/python/libmk/mk_project.py
/usr/lib/{0}/pydaw/python/libmk/mk_project.pyc
/usr/lib/{0}/pydaw/python/libmk/mk_project.pyo

/usr/lib/{0}/pydaw/python/libedmnext/__init__.py
/usr/lib/{0}/pydaw/python/libedmnext/__init__.pyc
/usr/lib/{0}/pydaw/python/libedmnext/__init__.pyo

/usr/lib/{0}/pydaw/python/wavenext.py
/usr/lib/{0}/pydaw/python/wavenext.pyc
/usr/lib/{0}/pydaw/python/wavenext.pyo

/usr/lib/{0}/pydaw/python/dawnext.py
/usr/lib/{0}/pydaw/python/dawnext.pyc
/usr/lib/{0}/pydaw/python/dawnext.pyo
/usr/lib/{0}/pydaw/python/libdawnext/__init__.py
/usr/lib/{0}/pydaw/python/libdawnext/__init__.pyc
/usr/lib/{0}/pydaw/python/libdawnext/__init__.pyo
/usr/lib/{0}/pydaw/python/libdawnext/gradients.py
/usr/lib/{0}/pydaw/python/libdawnext/gradients.pyc
/usr/lib/{0}/pydaw/python/libdawnext/gradients.pyo
/usr/lib/{0}/pydaw/python/libdawnext/osc.py
/usr/lib/{0}/pydaw/python/libdawnext/osc.pyc
/usr/lib/{0}/pydaw/python/libdawnext/osc.pyo
/usr/lib/{0}/pydaw/python/libdawnext/project.py
/usr/lib/{0}/pydaw/python/libdawnext/project.pyc
/usr/lib/{0}/pydaw/python/libdawnext/project.pyo
/usr/lib/{0}/pydaw/python/libdawnext/strings.py
/usr/lib/{0}/pydaw/python/libdawnext/strings.pyc
/usr/lib/{0}/pydaw/python/libdawnext/strings.pyo


%doc

""".format(MAJOR_VERSION, global_version_fedora,
    TARBALL_URL, f_native, PYTHON_VERSION)

f_spec_file = open(global_spec_file, "w")
f_spec_file.write(f_spec_template)
f_spec_file.close()

os.system('cp "{}" "{}"'.format(global_spec_file, SPEC_DIR))

os.chdir(SPEC_DIR)
f_rpm_result = os.system("rpmbuild -ba {}".format(global_spec_file))

if f_rpm_result:
    print("Error:  rpmbuild returned {}".format(f_rpm_result))
    exit(f_rpm_result)
else:
    pkg_name = "{}-*{}*rpm".format(
        MAJOR_VERSION, MINOR_VERSION)

    cp_cmd = "cp ~/rpmbuild/RPMS/*/{} '{}'".format(pkg_name, orig_wd)
    print(cp_cmd)
    os.system(cp_cmd)

    if IS_INSTALL:
        os.system("sudo rpm -e {0}".format(MAJOR_VERSION))
        os.system("sudo rpm -e {0}-debuginfo".format(MAJOR_VERSION))
        os.system("sudo rpm -ivh {}/{}".format(orig_wd, pkg_name))

