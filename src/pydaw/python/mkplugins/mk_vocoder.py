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

MK_VOCODER_PORT_MAP = {}

MK_VOCODER_TEXT = _(
"""This plugin has no controls.
Route the carrier signal to the plugin's main input,
and route the modulator signal to the track's sidechain input.
""")


class mk_vocoder_plugin_ui(pydaw_abstract_plugin_ui):
    def __init__(self, a_val_callback, a_project,
                 a_folder, a_plugin_uid, a_track_name, a_stylesheet,
                 a_configure_callback, a_midi_learn_callback,
                 a_cc_map_callback):
        pydaw_abstract_plugin_ui.__init__(
            self, a_val_callback, a_project, a_plugin_uid, a_stylesheet,
            a_configure_callback, a_folder, a_midi_learn_callback,
            a_cc_map_callback)
        self._plugin_name = "MK Vocoder"
        self.set_window_title(a_track_name)
        self.is_instrument = False
        #self.layout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        f_knob_size = 48
        self.layout.addWidget(QtGui.QLabel(MK_VOCODER_TEXT))
        self.scrollarea_widget.setFixedHeight(90)
        self.scrollarea_widget.setFixedWidth(480)
        self.open_plugin_file()
        self.set_midi_learn(MK_VOCODER_PORT_MAP)

    def set_window_title(self, a_track_name):
        self.track_name = str(a_track_name)
        self.widget.setWindowTitle(
            "MK Vocoder - {}".format(self.track_name))

    def raise_widget(self):
        pydaw_abstract_plugin_ui.raise_widget(self)

    def ui_message(self, a_name, a_value):
        pydaw_abstract_plugin_ui.ui_message(a_name, a_value)


