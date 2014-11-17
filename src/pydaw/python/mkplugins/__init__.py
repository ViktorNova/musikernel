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

import mkplugins.euphoria
import mkplugins.rayv
import mkplugins.wayv
import mkplugins.modulex
import mkplugins.mk_channel
import mkplugins.mk_delay
import mkplugins.mk_eq
import mkplugins.simple_fader
import mkplugins.simple_reverb
import mkplugins.sidechain_comp
import mkplugins.trigger_fx
import mkplugins.xfade
import mkplugins.mk_compressor
import mkplugins.mk_vocoder
import mkplugins.mk_limiter

from PyQt4 import QtGui
from libpydaw.pydaw_util import pydaw_clip_value

PLUGIN_INSTRUMENT_COUNT = 3  # For inserting the split line into the menu

PLUGIN_NAMES = [
    "Euphoria", "Ray-V", "Way-V", "MK Channel", "MK Compressor",
    "MK Delay", "MK EQ", "MK Limiter", "MK Vocoder", "Modulex",
    "Sidechain Comp.", "Simple Fader", "Simple Reverb", "TriggerFX",
    "X-Fade",
    ]

PLUGIN_UIDS = {
    "None":0, "Euphoria":1, "Ray-V":2, "Way-V":3, "Modulex":4, "MK Delay":5,
    "MK EQ":6, "Simple Fader":7, "Simple Reverb":8, "TriggerFX":9,
    "Sidechain Comp.":10, "MK Channel":11, "X-Fade":12, "MK Compressor":13,
    "MK Vocoder":14, "MK Limiter":15
    }

WAVE_EDITOR_PLUGIN_NAMES = [
    "None", "MK Channel", "MK Compressor", "MK Delay", "MK EQ",
    "MK Limiter", "Modulex", "Simple Fader", "Simple Reverb"
    ]

MIXER_PLUGIN_NAMES = ["None", "Simple Fader", "MK Channel"]
PLUGIN_UIDS_REVERSE = {v:k for k, v in PLUGIN_UIDS.items()}
CC_NAMES = {x:[] for x in PLUGIN_NAMES}
CONTROLLER_PORT_NAME_DICT = {x:{} for x in PLUGIN_NAMES}
CONTROLLER_PORT_NUM_DICT = {x:{} for x in PLUGIN_NAMES}

PLUGIN_UI_TYPES = {
    1:mkplugins.euphoria.euphoria_plugin_ui,
    2:mkplugins.rayv.rayv_plugin_ui,
    3:mkplugins.wayv.wayv_plugin_ui,
    4:mkplugins.modulex.modulex_plugin_ui,
    5:mkplugins.mk_delay.mkdelay_plugin_ui,
    6:mkplugins.mk_eq.mkeq_plugin_ui,
    7:mkplugins.simple_fader.sfader_plugin_ui,
    8:mkplugins.simple_reverb.sreverb_plugin_ui,
    9:mkplugins.trigger_fx.triggerfx_plugin_ui,
    10:mkplugins.sidechain_comp.scc_plugin_ui,
    11:mkplugins.mk_channel.mkchnl_plugin_ui,
    12:mkplugins.xfade.xfade_plugin_ui,
    13:mkplugins.mk_compressor.mk_comp_plugin_ui,
    14:mkplugins.mk_vocoder.mk_vocoder_plugin_ui,
    15:mkplugins.mk_limiter.mk_lim_plugin_ui,
}

PORTMAP_DICT = {
    "Euphoria":mkplugins.euphoria.EUPHORIA_PORT_MAP,
    "Way-V":mkplugins.wayv.WAYV_PORT_MAP,
    "Ray-V":mkplugins.rayv.RAYV_PORT_MAP,
    "Modulex":mkplugins.modulex.MODULEX_PORT_MAP,
    "MK Channel":mkplugins.mk_channel.MKCHNL_PORT_MAP,
    "MK Compressor":mkplugins.mk_compressor.MK_COMP_PORT_MAP,
    "MK Delay":mkplugins.mk_delay.MKDELAY_PORT_MAP,
    "MK EQ":mkplugins.mk_eq.MKEQ_PORT_MAP,
    "Simple Fader":mkplugins.simple_fader.SFADER_PORT_MAP,
    "Simple Reverb":mkplugins.simple_reverb.SREVERB_PORT_MAP,
    "TriggerFX":mkplugins.trigger_fx.TRIGGERFX_PORT_MAP,
    "Sidechain Comp.":mkplugins.sidechain_comp.SCC_PORT_MAP,
    "X-Fade":mkplugins.xfade.XFADE_PORT_MAP,
    "MK Vocoder":mkplugins.mk_vocoder.MK_VOCODER_PORT_MAP,
    "MK Limiter":mkplugins.mk_limiter.MK_LIM_PORT_MAP,
}

def get_plugin_uid_by_name(a_name):
    return PLUGIN_UIDS[str(a_name)]

class pydaw_controller_map_item:
    def __init__(self, a_name, a_port):
        self.name = str(a_name)
        self.port = int(a_port)

def pydaw_load_controller_maps():
    for k, v in PORTMAP_DICT.items():
        for k2, v2 in v.items():
            f_map = pydaw_controller_map_item(k2, v2)
            CONTROLLER_PORT_NAME_DICT[k][k2] = f_map
            CONTROLLER_PORT_NUM_DICT[k][int(v2)] = f_map
            CC_NAMES[k].append(k2)
        CC_NAMES[k].sort()

pydaw_load_controller_maps()

def pydaw_center_widget_on_screen(a_widget):
    f_desktop_center = QtGui.QApplication.desktop().screen().rect().center()
    f_widget_center = a_widget.rect().center()
    f_x = pydaw_clip_value(f_desktop_center.x() - f_widget_center.x(), 0, 300)
    f_y = pydaw_clip_value(f_desktop_center.y() - f_widget_center.y(), 0, 200)
    a_widget.move(f_x, f_y)

class mk_plugin_ui_dict:
    def __init__(self, a_project, a_ipc, a_stylesheet):
        """ a_project:    libmk.AbstractProject
            a_ipc:        libmk.AbstractIPC
            a_stylesheet: Qt-CSS string
        """
        self.ui_dict = {}
        self.midi_learn_control = None
        self.ctrl_update_callback = a_ipc.pydaw_update_plugin_control
        self.project = a_project
        self.plugin_pool_dir = a_project.plugin_pool_folder
        self.stylesheet = a_stylesheet
        self.configure_callback = a_ipc.pydaw_configure_plugin
        self.midi_learn_osc_callback = a_ipc.pydaw_midi_learn
        self.load_cc_map_callback = a_ipc.pydaw_load_cc_map

    def __contains__(self, a_plugin_uid):
        return a_plugin_uid in self.ui_dict

    def __getitem__(self, a_plugin_uid):
        return self.ui_dict[a_plugin_uid]

    def open_plugin_ui(self, a_plugin_uid, a_plugin_type, a_title,
                              a_show=True):
        if not a_plugin_uid in self.ui_dict:
            f_plugin = PLUGIN_UI_TYPES[a_plugin_type](
                self.ctrl_update_callback, self.project, self.plugin_pool_dir,
                a_plugin_uid, a_title, self.stylesheet,
                self.configure_callback, self.midi_learn_callback,
                self.load_cc_map_callback)
            pydaw_center_widget_on_screen(f_plugin.widget)
            self.ui_dict[a_plugin_uid] = f_plugin
            if a_show:
                f_plugin.show_widget()
            else:
                return f_plugin
        else:
            if not a_show:
                return self.ui_dict[a_plugin_uid]
            if self.ui_dict[a_plugin_uid].widget.isHidden():
                self.ui_dict[a_plugin_uid].widget.show()
            self.ui_dict[a_plugin_uid].raise_widget()

    def midi_learn_callback(self, a_plugin, a_control):
        self.midi_learn_control = (a_plugin, a_control)
        self.midi_learn_osc_callback()

    def close_plugin_ui(self, a_track_num):
        f_track_num = int(a_track_num)
        if f_track_num in self.ui_dict:
            self.ui_dict[f_track_num].widget.close()
            self.ui_dict.pop(f_track_num)

    def plugin_set_window_title(self, a_plugin_uid, a_track_name):
        f_plugin_uid = int(a_plugin_uid)
        if f_plugin_uid in self.ui_dict:
            self.ui_dict[a_plugin_uid].set_window_title(a_track_name)


    def close_all_plugin_windows(self):
        for v in list(self.ui_dict.values()):
            v.is_quitting = True
            v.widget.close()
        self.ui_dict = {}

    def save_all_plugin_state(self):
        for v in list(self.ui_dict.values()):
            v.save_plugin_file()
