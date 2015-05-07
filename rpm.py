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

BuildRequires:  alsa-lib-devel liblo-devel libsndfile-devel fftw-devel \
portmidi-devel portaudio-devel python3-devel gcc gcc-c++

Requires:       python3-qt5 alsa-lib-devel liblo-devel rubberband \
libsndfile-devel python3-numpy fftw-devel portmidi-devel \
portaudio-devel python3-devel vorbis-tools

%define __provides_exclude_from ^%{{_usr}}/lib/{0}/.*$

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

%attr(4755, root, root) %{{_usr}}/bin/{0}-engine

%attr(755, root, root) %{{_usr}}/bin/{0}
%attr(755, root, root) %{{_usr}}/bin/{0}_render
%attr(755, root, root) %{{_usr}}/bin/{0}_render-dbg
%attr(755, root, root) %{{_usr}}/bin/{0}-engine-dbg
%attr(755, root, root) %{{_usr}}/bin/{0}-engine-no-root
%attr(755, root, root) %{{_usr}}/lib/{0}/pydaw/python/libpydaw/pydaw_paulstretch.py
%attr(755, root, root) %{{_usr}}/lib/{0}/pydaw/python/musikernel.py
%attr(755, root, root) %{{_usr}}/lib/{0}/sbsms/bin/sbsms
%attr(755, root, root) %{{_usr}}/lib/{0}/pydaw/python/libpydaw/project_recover.py
%attr(755, root, root) %{{_usr}}/lib/{0}/pydaw/python/libpydaw/pydaw_device_dialog.py

%{{_usr}}/lib/{0}/pydaw/mkengine/{0}.so
%{{_usr}}/lib/{0}/pydaw/python/edmnext.py
%{{_usr}}/lib/{0}/presets/MODULEX.mkp
%{{_usr}}/lib/{0}/presets/RAYV.mkp
%{{_usr}}/lib/{0}/presets/WAYV.mkp
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/__init__.py
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/liblo.cpython-{4}m.so
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/midicomp
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/portaudio.py
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/portmidi.py
%{{_usr}}/lib/{0}/pydaw/python/libedmnext/gradients.py
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/pydaw_history.py
%{{_usr}}/lib/{0}/pydaw/python/libedmnext/osc.py
%{{_usr}}/lib/{0}/pydaw/python/libedmnext/project.py
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/pydaw_util.py
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/pydaw_widgets.py
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/staging.py
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/super_formant_maker.py
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/translate.py
%{{_usr}}/lib/{0}/major-version.txt
%{{_usr}}/lib/{0}/minor-version.txt
%{{_usr}}/lib/{0}/themes/default/drop-down.png
%{{_usr}}/lib/{0}/themes/default/euphoria.png
%{{_usr}}/lib/{0}/themes/default/h-fader.png
%{{_usr}}/lib/{0}/themes/default/mute-off.png
%{{_usr}}/lib/{0}/themes/default/mute-on.png
%{{_usr}}/lib/{0}/themes/default/play-off.png
%{{_usr}}/lib/{0}/themes/default/play-on.png
%{{_usr}}/lib/{0}/themes/default/pydaw-knob.png
%{{_usr}}/lib/{0}/themes/default/rayv.png
%{{_usr}}/lib/{0}/themes/default/rec-off.png
%{{_usr}}/lib/{0}/themes/default/rec-on.png
%{{_usr}}/lib/{0}/themes/default/record-off.png
%{{_usr}}/lib/{0}/themes/default/record-on.png
%{{_usr}}/lib/{0}/themes/default/solo-off.png
%{{_usr}}/lib/{0}/themes/default/solo-on.png
%{{_usr}}/lib/{0}/themes/default/spinbox-down.png
%{{_usr}}/lib/{0}/themes/default/spinbox-up.png
%{{_usr}}/lib/{0}/themes/default/stop-off.png
%{{_usr}}/lib/{0}/themes/default/stop-on.png
%{{_usr}}/lib/{0}/themes/default/default.pytheme
%{{_usr}}/lib/{0}/themes/default/v-fader.png
%{{_usr}}/share/applications/{0}.desktop
%{{_usr}}/share/doc/{0}/copyright
%{{_usr}}/share/pixmaps/{0}.png
#%{{_usr}}/share/locale/pt_PT/LC_MESSAGES/{0}.mo
#%{{_usr}}/share/locale/de/LC_MESSAGES/{0}.mo
#%{{_usr}}/share/locale/fr/LC_MESSAGES/{0}.mo
%{{_usr}}/lib/{0}/pydaw/python/splash.png
%{{_usr}}/lib/{0}/pydaw/python/wavefile/__init__.py
%{{_usr}}/lib/{0}/pydaw/python/wavefile/libsndfile.py
%{{_usr}}/lib/{0}/pydaw/python/wavefile/wavefile.py


%{{_usr}}/lib/{0}/pydaw/python/libpydaw/__init__.pyc
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/__init__.pyo
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/portaudio.pyc
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/portaudio.pyo
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/portmidi.pyc
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/portmidi.pyo
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/project_recover.pyc
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/project_recover.pyo
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/pydaw_device_dialog.pyc
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/pydaw_device_dialog.pyo
%{{_usr}}/lib/{0}/pydaw/python/libedmnext/gradients.pyc
%{{_usr}}/lib/{0}/pydaw/python/libedmnext/gradients.pyo
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/pydaw_history.pyc
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/pydaw_history.pyo
%{{_usr}}/lib/{0}/pydaw/python/libedmnext/osc.pyc
%{{_usr}}/lib/{0}/pydaw/python/libedmnext/osc.pyo
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/pydaw_paulstretch.pyc
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/pydaw_paulstretch.pyo
%{{_usr}}/lib/{0}/pydaw/python/libedmnext/project.pyc
%{{_usr}}/lib/{0}/pydaw/python/libedmnext/project.pyo
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/pydaw_util.pyc
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/pydaw_util.pyo
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/pydaw_widgets.pyc
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/pydaw_widgets.pyo
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/staging.pyc
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/staging.pyo
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/super_formant_maker.pyc
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/super_formant_maker.pyo
%{{_usr}}/lib/{0}/pydaw/python/edmnext.pyc
%{{_usr}}/lib/{0}/pydaw/python/edmnext.pyo
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/translate.pyc
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/translate.pyo
%{{_usr}}/lib/{0}/pydaw/python/wavefile/__init__.pyc
%{{_usr}}/lib/{0}/pydaw/python/wavefile/__init__.pyo
%{{_usr}}/lib/{0}/pydaw/python/wavefile/libsndfile.pyc
%{{_usr}}/lib/{0}/pydaw/python/wavefile/libsndfile.pyo
%{{_usr}}/lib/{0}/pydaw/python/wavefile/wavefile.pyc
%{{_usr}}/lib/{0}/pydaw/python/wavefile/wavefile.pyo

%{{_usr}}/lib/{0}/pydaw/python/libpydaw/strings.py
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/strings.pyc
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/strings.pyo

%{{_usr}}/lib/{0}/pydaw/python/libpydaw/scales.py
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/scales.pyc
%{{_usr}}/lib/{0}/pydaw/python/libpydaw/scales.pyo

%{{_usr}}/lib/{0}/pydaw/python/libedmnext/strings.py
%{{_usr}}/lib/{0}/pydaw/python/libedmnext/strings.pyc
%{{_usr}}/lib/{0}/pydaw/python/libedmnext/strings.pyo

%{{_usr}}/lib/{0}/pydaw/python/mkplugins/__init__.py
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/__init__.pyc
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/__init__.pyo
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/euphoria.py
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/euphoria.pyc
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/euphoria.pyo
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/modulex.py
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/modulex.pyc
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/modulex.pyo
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/rayv.py
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/rayv.pyc
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/rayv.pyo
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/wayv.py
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/wayv.pyc
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/wayv.pyo

%{{_usr}}/lib/{0}/pydaw/python/mkplugins/mk_delay.py
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/mk_delay.pyc
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/mk_delay.pyo
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/mk_eq.py
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/mk_eq.pyc
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/mk_eq.pyo
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/simple_fader.py
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/simple_fader.pyc
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/simple_fader.pyo
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/simple_reverb.py
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/simple_reverb.pyc
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/simple_reverb.pyo
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/trigger_fx.py
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/trigger_fx.pyc
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/trigger_fx.pyo

%{{_usr}}/lib/{0}/pydaw/python/mkplugins/sidechain_comp.py
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/sidechain_comp.pyc
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/sidechain_comp.pyo

%{{_usr}}/lib/{0}/pydaw/python/mkplugins/mk_channel.py
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/mk_channel.pyc
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/mk_channel.pyo
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/xfade.py
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/xfade.pyc
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/xfade.pyo

%{{_usr}}/lib/{0}/pydaw/python/mkplugins/mk_compressor.py
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/mk_compressor.pyc
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/mk_compressor.pyo

%{{_usr}}/lib/{0}/pydaw/python/mkplugins/mk_vocoder.py
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/mk_vocoder.pyc
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/mk_vocoder.pyo

%{{_usr}}/lib/{0}/pydaw/python/musikernel.pyc
%{{_usr}}/lib/{0}/pydaw/python/musikernel.pyo

%{{_usr}}/lib/{0}/pydaw/python/mkplugins/mk_limiter.py
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/mk_limiter.pyc
%{{_usr}}/lib/{0}/pydaw/python/mkplugins/mk_limiter.pyo

%{{_usr}}/lib/{0}/pydaw/python/libmk/__init__.py
%{{_usr}}/lib/{0}/pydaw/python/libmk/__init__.pyc
%{{_usr}}/lib/{0}/pydaw/python/libmk/__init__.pyo

%{{_usr}}/lib/{0}/pydaw/python/libmk/mk_project.py
%{{_usr}}/lib/{0}/pydaw/python/libmk/mk_project.pyc
%{{_usr}}/lib/{0}/pydaw/python/libmk/mk_project.pyo

%{{_usr}}/lib/{0}/pydaw/python/libedmnext/__init__.py
%{{_usr}}/lib/{0}/pydaw/python/libedmnext/__init__.pyc
%{{_usr}}/lib/{0}/pydaw/python/libedmnext/__init__.pyo

%{{_usr}}/lib/{0}/pydaw/python/wavenext.py
%{{_usr}}/lib/{0}/pydaw/python/wavenext.pyc
%{{_usr}}/lib/{0}/pydaw/python/wavenext.pyo

%{{_usr}}/lib/{0}/pydaw/python/dawnext.py
%{{_usr}}/lib/{0}/pydaw/python/dawnext.pyc
%{{_usr}}/lib/{0}/pydaw/python/dawnext.pyo
%{{_usr}}/lib/{0}/pydaw/python/libdawnext/__init__.py
%{{_usr}}/lib/{0}/pydaw/python/libdawnext/__init__.pyc
%{{_usr}}/lib/{0}/pydaw/python/libdawnext/__init__.pyo
%{{_usr}}/lib/{0}/pydaw/python/libdawnext/gradients.py
%{{_usr}}/lib/{0}/pydaw/python/libdawnext/gradients.pyc
%{{_usr}}/lib/{0}/pydaw/python/libdawnext/gradients.pyo
%{{_usr}}/lib/{0}/pydaw/python/libdawnext/osc.py
%{{_usr}}/lib/{0}/pydaw/python/libdawnext/osc.pyc
%{{_usr}}/lib/{0}/pydaw/python/libdawnext/osc.pyo
%{{_usr}}/lib/{0}/pydaw/python/libdawnext/project.py
%{{_usr}}/lib/{0}/pydaw/python/libdawnext/project.pyc
%{{_usr}}/lib/{0}/pydaw/python/libdawnext/project.pyo
%{{_usr}}/lib/{0}/pydaw/python/libdawnext/strings.py
%{{_usr}}/lib/{0}/pydaw/python/libdawnext/strings.pyc
%{{_usr}}/lib/{0}/pydaw/python/libdawnext/strings.pyo


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

