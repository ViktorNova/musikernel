# -*- coding: utf-8 -*-
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

from libpydaw.pydaw_widgets import *
from libpydaw.translate import _


#Modulex

MKDELAY_INPUT0 = 0
MKDELAY_INPUT1 = 1
MKDELAY_OUTPUT0 = 2
MKDELAY_OUTPUT1 = 3
MKDELAY_FIRST_CONTROL_PORT = 4
MKDELAY_DELAY_TIME = 4
MKDELAY_FEEDBACK = 5
MKDELAY_DRY = 6
MKDELAY_WET = 7
MKDELAY_DUCK = 8
MKDELAY_CUTOFF = 9
MKDELAY_STEREO = 10


MKDELAY_PORT_MAP = {
    "Delay Feedback": MKDELAY_FEEDBACK,
    "Delay Dry": MKDELAY_DRY,
    "Delay Wet": MKDELAY_WET,
    "Delay Duck": MKDELAY_DUCK,
    "Delay LP Cutoff": MKDELAY_CUTOFF,
}


class mkdelay_plugin_ui(pydaw_abstract_plugin_ui):
    def __init__(self, a_val_callback, a_project,
                 a_folder, a_plugin_uid, a_track_name, a_stylesheet,
                 a_configure_callback, a_midi_learn_callback,
                 a_cc_map_callback):
        pydaw_abstract_plugin_ui.__init__(
            self, a_val_callback, a_project, a_plugin_uid, a_stylesheet,
            a_configure_callback, a_folder, a_midi_learn_callback,
            a_cc_map_callback)
        self._plugin_name = "MKDELAY"
        self.set_window_title(a_track_name)
        self.is_instrument = False

        self.tab_widget = QtGui.QTabWidget()
        self.layout.addWidget(self.tab_widget)
        self.layout.setSizeConstraint(QtGui.QLayout.SetFixedSize)

        self.misc_tab = QtGui.QWidget()
        self.tab_widget.addTab(self.misc_tab, _("Misc."))
        self.delay_vlayout = QtGui.QVBoxLayout()
        self.misc_tab.setLayout(self.delay_vlayout)
        self.delay_hlayout = QtGui.QHBoxLayout()
        self.delay_vlayout.addLayout(self.delay_hlayout)

        f_knob_size = 48
        self.preset_manager = None

        delay_groupbox = QtGui.QGroupBox(_("Delay"))
        delay_groupbox.setObjectName("plugin_groupbox")
        self.delay_hlayout.addWidget(delay_groupbox)
        delay_gridlayout = QtGui.QGridLayout(delay_groupbox)
        self.delay_hlayout.addWidget(delay_groupbox)
        self.delay_time_knob = pydaw_knob_control(
            f_knob_size, _("Time"), MKDELAY_DELAY_TIME,
            self.plugin_rel_callback, self.plugin_val_callback,
            10, 100, 50, KC_TIME_DECIMAL, self.port_dict, self.preset_manager)
        self.delay_time_knob.add_to_grid_layout(delay_gridlayout, 0)
        self.feedback = pydaw_knob_control(
            f_knob_size, _("Fdbk"), MKDELAY_FEEDBACK,
            self.plugin_rel_callback, self.plugin_val_callback,
            -20, 0, -12, KC_INTEGER, self.port_dict, self.preset_manager)
        self.feedback.add_to_grid_layout(delay_gridlayout, 1)
        self.dry_knob = pydaw_knob_control(
            f_knob_size, _("Dry"), MKDELAY_DRY,
            self.plugin_rel_callback, self.plugin_val_callback,
            -30, 0, 0, KC_INTEGER, self.port_dict, self.preset_manager)
        self.dry_knob.add_to_grid_layout(delay_gridlayout, 2)
        self.wet_knob = pydaw_knob_control(
            f_knob_size, _("Wet"), MKDELAY_WET,
            self.plugin_rel_callback, self.plugin_val_callback, -30, 0, -30,
            KC_INTEGER, self.port_dict, self.preset_manager)
        self.wet_knob.add_to_grid_layout(delay_gridlayout, 3)
        self.duck_knob = pydaw_knob_control(
            f_knob_size, _("Duck"), MKDELAY_DUCK,
            self.plugin_rel_callback, self.plugin_val_callback,
            -40, 0, 0, KC_INTEGER, self.port_dict, self.preset_manager)
        self.duck_knob.add_to_grid_layout(delay_gridlayout, 4)
        self.cutoff_knob = pydaw_knob_control(
            f_knob_size, _("Cutoff"), MKDELAY_CUTOFF,
            self.plugin_rel_callback, self.plugin_val_callback,
            40, 118, 90, KC_PITCH, self.port_dict, self.preset_manager)
        self.cutoff_knob.add_to_grid_layout(delay_gridlayout, 5)
        self.stereo_knob = pydaw_knob_control(
            f_knob_size, _("Stereo"), MKDELAY_STEREO,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 100, KC_DECIMAL, self.port_dict, self.preset_manager)
        self.stereo_knob.add_to_grid_layout(delay_gridlayout, 6)

        self.open_plugin_file()
        self.set_midi_learn(MKDELAY_PORT_MAP)

    def open_plugin_file(self):
        pydaw_abstract_plugin_ui.open_plugin_file(self)

    def save_plugin_file(self):
        pydaw_abstract_plugin_ui.save_plugin_file(self)

    def set_window_title(self, a_track_name):
        self.track_name = str(a_track_name)
        self.widget.setWindowTitle(
            "MusiKernel Modulex - {}".format(self.track_name))

    def widget_close_event(self, a_event):
        pydaw_abstract_plugin_ui.widget_close_event(self, a_event)

    def raise_widget(self):
        pydaw_abstract_plugin_ui.raise_widget(self)

    def ui_message(self, a_name, a_value):
        pydaw_abstract_plugin_ui.ui_message(a_name, a_value)


