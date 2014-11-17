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

class AbstractIPC:
    """ Abstract class containing the minimum contract
        to run MK Plugins for host communication to the
        MusiKernel engine
    """
    def __init__(self):
        pass

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

    def save_file(a_plugins_folder, a_plugin_uid, a_file):
        raise NotImplementedError

    def commit(self, a_message):
        raise NotImplementedError

    def flush_history(self):
        raise NotImplementedError

