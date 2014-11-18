"""
This file is part of the MusiKernel project, Copyright MusiKernel Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

"""

import sys
from libpydaw import pydaw_util
from libpydaw import liblo

# These are dynamically assigned by musikernel.py so that
# hosts can access them from this module
MAIN_WINDOW = None
APP = None
TRANSPORT = None
IS_PLAYING = False
IPC = None
OSC = None
PROJECT = None
TOOLTIPS_ENABLED = pydaw_util.get_file_setting("tooltips", int, 1)

def set_window_title():
    MAIN_WINDOW.setWindowTitle('MusiKernel | EDM-Next - {}/{}.{}'.format(
        PROJECT.project_folder, PROJECT.project_file,
        pydaw_util.global_pydaw_version_string))

class AbstractIPC:
    """ Abstract class containing the minimum contract
        to run MK Plugins for host communication to the
        MusiKernel engine
    """
    def __init__(self, a_with_audio=False,
             a_configure_path="/musikernel/edmnext"):
        if not a_with_audio:
            self.with_osc = False
            return
        else:
            self.with_osc = True
            self.m_suppressHostUpdate = False
            self.configure_path = a_configure_path

    def send_configure(self, key, value):
        if self.with_osc:
            liblo.send(OSC, self.configure_path, key, value)
        else:
            print("Running standalone UI without OSC.  "
                "Would've sent configure message: key: \""
                "{}\" value: \"{}\"".format(key, value))

    def pydaw_update_plugin_control(self, a_plugin_uid, a_port, a_val):
        raise NotImplementedError

    def pydaw_configure_plugin(self, a_plugin_uid, a_key, a_message):
        raise NotImplementedError

    def pydaw_midi_learn(self):
        raise NotImplementedError

    def pydaw_load_cc_map(self, a_plugin_uid, a_str):
        raise NotImplementedError

class AbstractProject:
    """ Abstract class containing the minimum contract
        to run MK Plugins for host project file saving
    """
    def __init__(self):
        self.plugin_pool_folder = None



class AbstractTransport:
    pass

