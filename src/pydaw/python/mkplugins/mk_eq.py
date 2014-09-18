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

MKEQ_INPUT0 = 0
MKEQ_INPUT1 = 1
MKEQ_OUTPUT0 = 2
MKEQ_OUTPUT1 = 3
MKEQ_FIRST_CONTROL_PORT = 4
MKEQ_EQ1_FREQ = 4
MKEQ_EQ1_RES = 5
MKEQ_EQ1_GAIN = 6
MKEQ_EQ2_FREQ = 7
MKEQ_EQ2_RES = 8
MKEQ_EQ2_GAIN = 9
MKEQ_EQ3_FREQ = 10
MKEQ_EQ3_RES = 11
MKEQ_EQ3_GAIN = 12
MKEQ_EQ4_FREQ = 13
MKEQ_EQ4_RES = 14
MKEQ_EQ4_GAIN = 15
MKEQ_EQ5_FREQ = 16
MKEQ_EQ5_RES = 17
MKEQ_EQ5_GAIN = 18
MKEQ_EQ6_FREQ = 19
MKEQ_EQ6_RES = 20
MKEQ_EQ6_GAIN = 21
MKEQ_SPECTRUM_ENABLED = 22

MKEQ_PORT_MAP = {
}



class mkeq_plugin_ui(pydaw_abstract_plugin_ui):
    def __init__(self, a_val_callback, a_project,
                 a_folder, a_plugin_uid, a_track_name, a_stylesheet,
                 a_configure_callback, a_midi_learn_callback,
                 a_cc_map_callback):
        pydaw_abstract_plugin_ui.__init__(
            self, a_val_callback, a_project, a_plugin_uid, a_stylesheet,
            a_configure_callback, a_folder, a_midi_learn_callback,
            a_cc_map_callback)
        self._plugin_name = "MKEQ"
        self.set_window_title(a_track_name)
        self.is_instrument = False

        self.preset_manager = pydaw_preset_manager_widget(
            self.get_plugin_name())
        self.presets_hlayout = QtGui.QHBoxLayout()
        self.presets_hlayout.addWidget(self.preset_manager.group_box)
        self.presets_hlayout.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))
        self.layout.addLayout(self.presets_hlayout)
        self.spectrum_enabled = None
        self.tab_widget = QtGui.QTabWidget()
        self.tab_widget.currentChanged.connect(self.tab_changed)
        self.layout.addWidget(self.tab_widget)
        self.layout.setSizeConstraint(QtGui.QLayout.SetFixedSize)

        self.fx_tab = QtGui.QWidget()
        self.tab_widget.addTab(self.fx_tab, _("Effects"))
        self.fx_layout = QtGui.QGridLayout()
        self.fx_hlayout = QtGui.QHBoxLayout(self.fx_tab)
        self.fx_hlayout.addLayout(self.fx_layout)

        self.misc_tab = QtGui.QWidget()
        self.tab_widget.addTab(self.misc_tab, _("Misc."))
        self.delay_vlayout = QtGui.QVBoxLayout()
        self.misc_tab.setLayout(self.delay_vlayout)
        self.delay_hlayout = QtGui.QHBoxLayout()
        self.delay_vlayout.addLayout(self.delay_hlayout)

        f_knob_size = 48

        self.eq6 = eq6_widget(
            MKEQ_EQ_ON,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, a_preset_mgr=self.preset_manager,
            a_size=f_knob_size)

        self.tab_widget.addTab(self.eq6.widget, _("EQ/Spectrum"))

        self.spectrum_enabled = pydaw_null_control(
            MKEQ_SPECTRUM_ENABLED,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, self.port_dict)

        self.open_plugin_file()
        self.set_midi_learn(MKEQ_PORT_MAP)

    def open_plugin_file(self):
        pydaw_abstract_plugin_ui.open_plugin_file(self)
        self.eq6.update_viewer()

    def save_plugin_file(self):
        # Don't allow the spectrum analyzer to run at startup
        self.spectrum_enabled.set_value(0)
        pydaw_abstract_plugin_ui.save_plugin_file(self)

    def set_window_title(self, a_track_name):
        self.track_name = str(a_track_name)
        self.widget.setWindowTitle(
            "MusiKernel Modulex - {}".format(self.track_name))

    def widget_close_event(self, a_event):
        print("Disabling spectrum")
        self.plugin_val_callback(
            MKEQ_SPECTRUM_ENABLED, 0.0)
        pydaw_abstract_plugin_ui.widget_close_event(self, a_event)

    def raise_widget(self):
        pydaw_abstract_plugin_ui.raise_widget(self)
        self.tab_changed()

    def tab_changed(self, a_val=None):
        if not self.spectrum_enabled:
            return
        if self.tab_widget.currentIndex() == 2:
            print("Enabling spectrum")
            self.plugin_val_callback(
                MKEQ_SPECTRUM_ENABLED, 1.0)
        else:
            print("Disabling spectrum")
            self.plugin_val_callback(
                MKEQ_SPECTRUM_ENABLED, 0.0)

    def ui_message(self, a_name, a_value):
        if a_name == "spectrum":
            self.eq6.set_spectrum(a_value)
        else:
            pydaw_abstract_plugin_ui.ui_message(a_name, a_value)

