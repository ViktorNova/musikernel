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


SCC_THRESHOLD = 0
SCC_RATIO = 1
SCC_SPEED = 2
SCC_WET = 3


SCC_PORT_MAP = {
    "Wet": SCC_WET
}


class scc_plugin_ui(pydaw_abstract_plugin_ui):
    def __init__(self, a_val_callback, a_project,
                 a_folder, a_plugin_uid, a_track_name, a_stylesheet,
                 a_configure_callback, a_midi_learn_callback,
                 a_cc_map_callback):
        pydaw_abstract_plugin_ui.__init__(
            self, a_val_callback, a_project, a_plugin_uid, a_stylesheet,
            a_configure_callback, a_folder, a_midi_learn_callback,
            a_cc_map_callback)
        self._plugin_name = "Sidechain Comp."
        self.set_window_title(a_track_name)
        self.is_instrument = False

        self.preset_manager = None
        self.tab_widget = QtGui.QTabWidget()
        self.layout.addWidget(self.tab_widget)
        self.layout.setSizeConstraint(QtGui.QLayout.SetFixedSize)

        self.misc_tab = QtGui.QWidget()
        self.tab_widget.addTab(self.misc_tab, _("Sidechain Comp."))
        self.delay_vlayout = QtGui.QVBoxLayout()
        self.misc_tab.setLayout(self.delay_vlayout)
        self.delay_hlayout = QtGui.QHBoxLayout()
        self.delay_vlayout.addLayout(self.delay_hlayout)

        f_knob_size = 48

        self.reverb_groupbox = QtGui.QGroupBox(_("Sidechain Comp."))
        self.reverb_groupbox.setObjectName("plugin_groupbox")
        self.reverb_groupbox_gridlayout = QtGui.QGridLayout(
            self.reverb_groupbox)
        self.reverb_hlayout = QtGui.QHBoxLayout()
        self.delay_vlayout.addLayout(self.reverb_hlayout)
        self.reverb_hlayout.addWidget(self.reverb_groupbox)
        self.reverb_hlayout.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))

        self.thresh_knob = pydaw_knob_control(
            f_knob_size, _("Thresh"), SCC_THRESHOLD,
            self.plugin_rel_callback, self.plugin_val_callback,
            -36, -6, -24, KC_INTEGER, self.port_dict, self.preset_manager)
        self.thresh_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 3)

        self.ratio_knob = pydaw_knob_control(
            f_knob_size, _("Ratio"), SCC_RATIO,
            self.plugin_rel_callback, self.plugin_val_callback,
            1, 100, 20, KC_TENTH, self.port_dict, self.preset_manager)
        self.ratio_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 7)

        self.speed_knob = pydaw_knob_control(
            f_knob_size, _("Speed"), SCC_SPEED,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 30, 15, KC_NONE, self.port_dict, self.preset_manager)
        self.speed_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 15)

        self.wet_knob = pydaw_knob_control(
            f_knob_size, _("Wet"), SCC_WET,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 100, KC_INTEGER, self.port_dict, self.preset_manager)
        self.wet_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 21)

        self.delay_spacer_layout = QtGui.QVBoxLayout()
        self.delay_vlayout.addLayout(self.delay_spacer_layout)
        self.delay_spacer_layout.addItem(
            QtGui.QSpacerItem(1, 1, vPolicy=QtGui.QSizePolicy.Expanding))

        self.open_plugin_file()
        self.set_midi_learn(SCC_PORT_MAP)

    def set_window_title(self, a_track_name):
        self.track_name = str(a_track_name)
        self.widget.setWindowTitle(
            "MusiKernel Sidechain Comp. - {}".format(self.track_name))

