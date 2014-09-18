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

TRIGGERFX_INPUT0 = 0
TRIGGERFX_INPUT1 = 1
TRIGGERFX_OUTPUT0 = 2
TRIGGERFX_OUTPUT1 = 3
TRIGGERFX_FIRST_CONTROL_PORT = 4
TRIGGERFX_GATE_NOTE = 4
TRIGGERFX_GATE_MODE = 5
TRIGGERFX_GATE_WET = 6
TRIGGERFX_GATE_PITCH = 7
TRIGGERFX_GLITCH_ON = 8
TRIGGERFX_GLITCH_NOTE = 9
TRIGGERFX_GLITCH_TIME = 10
TRIGGERFX_GLITCH_PB = 11


TRIGGERFX_PORT_MAP = {
    "Gate Wet": TRIGGERFX_GATE_WET,
    "Glitch Time": TRIGGERFX_GLITCH_TIME
}



class triggerfx_plugin_ui(pydaw_abstract_plugin_ui):
    def __init__(self, a_val_callback, a_project,
                 a_folder, a_plugin_uid, a_track_name, a_stylesheet,
                 a_configure_callback, a_midi_learn_callback,
                 a_cc_map_callback):
        pydaw_abstract_plugin_ui.__init__(
            self, a_val_callback, a_project, a_plugin_uid, a_stylesheet,
            a_configure_callback, a_folder, a_midi_learn_callback,
            a_cc_map_callback)
        self._plugin_name = "MODULEX"
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

        f_note_triggered_label = QtGui.QLabel(_("Note-Triggered Effects"))
        f_note_triggered_label.setToolTip(
            _("The below effects are triggered when you play their \n"
            "selected note.  Usually you will want to change the note\n"
            "range on any instrument plugins on the same track to not\n"
            "include the selected note for these effects."))
        self.delay_vlayout.addWidget(f_note_triggered_label)
        self.note_triggered_hlayout = QtGui.QHBoxLayout()
        self.delay_vlayout.addLayout(self.note_triggered_hlayout)

        self.gate_groupbox = QtGui.QGroupBox(_("Gate"))
        self.gate_groupbox.setObjectName("plugin_groupbox")
        self.note_triggered_hlayout.addWidget(self.gate_groupbox)
        self.gate_gridlayout = QtGui.QGridLayout(self.gate_groupbox)
        self.gate_on_checkbox = pydaw_checkbox_control(
            "On", TRIGGERFX_GATE_MODE,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, a_preset_mgr=self.preset_manager)
        self.gate_on_checkbox.add_to_grid_layout(self.gate_gridlayout, 3)
        self.gate_note_selector = pydaw_note_selector_widget(
            TRIGGERFX_GATE_NOTE,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, 120, self.preset_manager)
        self.gate_note_selector.add_to_grid_layout(self.gate_gridlayout, 6)
        self.gate_wet_knob = pydaw_knob_control(
            f_knob_size, _("Wet"), TRIGGERFX_GATE_WET,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 0, KC_DECIMAL, self.port_dict, self.preset_manager)
        self.gate_wet_knob.add_to_grid_layout(self.gate_gridlayout, 9)

        self.gate_pitch_knob = pydaw_knob_control(
            f_knob_size, _("Pitch"), TRIGGERFX_GATE_PITCH,
            self.plugin_rel_callback, self.plugin_val_callback,
            20, 120, 60, KC_PITCH, self.port_dict, self.preset_manager)
        self.gate_pitch_knob.add_to_grid_layout(self.gate_gridlayout, 12)

        self.glitch_groupbox = QtGui.QGroupBox(_("Glitch"))
        self.glitch_groupbox.setObjectName("plugin_groupbox")
        self.note_triggered_hlayout.addWidget(self.glitch_groupbox)
        self.note_triggered_hlayout.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))
        self.glitch_gridlayout = QtGui.QGridLayout(self.glitch_groupbox)

        self.glitch_on_checkbox = pydaw_checkbox_control(
            "On", TRIGGERFX_GLITCH_ON,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, a_preset_mgr=self.preset_manager)
        self.glitch_on_checkbox.add_to_grid_layout(self.glitch_gridlayout, 3)
        self.glitch_note_selector = pydaw_note_selector_widget(
            TRIGGERFX_GLITCH_NOTE,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, 119, self.preset_manager)
        self.glitch_note_selector.add_to_grid_layout(self.glitch_gridlayout, 6)
        self.glitch_time_knob = pydaw_knob_control(
            f_knob_size, _("Time"), TRIGGERFX_GLITCH_TIME,
            self.plugin_rel_callback, self.plugin_val_callback,
            1, 25, 10, KC_TIME_DECIMAL, self.port_dict, self.preset_manager)
        self.glitch_time_knob.add_to_grid_layout(self.glitch_gridlayout, 9)
        self.glitch_pb_knob = pydaw_knob_control(
            f_knob_size, _("Pitchbend"), TRIGGERFX_GLITCH_PB,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 36, 0, KC_INTEGER, self.port_dict, self.preset_manager)
        self.glitch_pb_knob.add_to_grid_layout(self.glitch_gridlayout, 12)

        self.delay_spacer_layout = QtGui.QVBoxLayout()
        self.delay_vlayout.addLayout(self.delay_spacer_layout)
        self.delay_spacer_layout.addItem(
            QtGui.QSpacerItem(1, 1, vPolicy=QtGui.QSizePolicy.Expanding))

        self.open_plugin_file()
        self.set_midi_learn(TRIGGERFX_PORT_MAP)

    def open_plugin_file(self):
        pydaw_abstract_plugin_ui.open_plugin_file(self)

    def save_plugin_file(self):
        pydaw_abstract_plugin_ui.save_plugin_file(self)

    def set_window_title(self, a_track_name):
        self.track_name = str(a_track_name)
        self.widget.setWindowTitle(
            "MusiKernel Modulex - {}".format(self.track_name))

    def widget_close_event(self, a_event):
        print("Disabling spectrum")
        self.plugin_val_callback(
            TRIGGERFX_SPECTRUM_ENABLED, 0.0)
        pydaw_abstract_plugin_ui.widget_close_event(self, a_event)

    def raise_widget(self):
        pydaw_abstract_plugin_ui.raise_widget(self)

    def ui_message(self, a_name, a_value):
        pydaw_abstract_plugin_ui.ui_message(a_name, a_value)


