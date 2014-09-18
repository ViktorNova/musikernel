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

class modulex_plugin_ui(pydaw_abstract_plugin_ui):
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

        f_port = 4
        f_column = 0
        f_row = 0
        for f_i in range(8):
            f_effect = pydaw_modulex_single(
                "FX{}".format(f_i), f_port,
                self.plugin_rel_callback, self.plugin_val_callback,
                self.port_dict, self.preset_manager, a_knob_size=f_knob_size)
            self.effects.append(f_effect)
            self.fx_layout.addWidget(f_effect.group_box, f_row, f_column)
            f_column += 1
            if f_column > 1:
                f_column = 0
                f_row += 1
            f_port += 4

        self.volume_gridlayout = QtGui.QGridLayout()
        self.fx_hlayout.addLayout(self.volume_gridlayout)
        self.volume_slider = pydaw_slider_control(
            QtCore.Qt.Vertical, "Vol", pydaw_ports.MODULEX_VOL_SLIDER,
            self.plugin_rel_callback, self.plugin_val_callback,
            -50, 0, 0, KC_INTEGER, self.port_dict)
        self.volume_slider.add_to_grid_layout(self.volume_gridlayout, 0)

        delay_groupbox = QtGui.QGroupBox(_("Delay"))
        delay_groupbox.setObjectName("plugin_groupbox")
        self.delay_hlayout.addWidget(delay_groupbox)
        delay_gridlayout = QtGui.QGridLayout(delay_groupbox)
        self.delay_hlayout.addWidget(delay_groupbox)
        self.delay_time_knob = pydaw_knob_control(
            f_knob_size, _("Time"), pydaw_ports.MODULEX_DELAY_TIME,
            self.plugin_rel_callback, self.plugin_val_callback,
            10, 100, 50, KC_TIME_DECIMAL, self.port_dict, self.preset_manager)
        self.delay_time_knob.add_to_grid_layout(delay_gridlayout, 0)
        self.feedback = pydaw_knob_control(
            f_knob_size, _("Fdbk"), pydaw_ports.MODULEX_FEEDBACK,
            self.plugin_rel_callback, self.plugin_val_callback,
            -20, 0, -12, KC_INTEGER, self.port_dict, self.preset_manager)
        self.feedback.add_to_grid_layout(delay_gridlayout, 1)
        self.dry_knob = pydaw_knob_control(
            f_knob_size, _("Dry"), pydaw_ports.MODULEX_DRY,
            self.plugin_rel_callback, self.plugin_val_callback,
            -30, 0, 0, KC_INTEGER, self.port_dict, self.preset_manager)
        self.dry_knob.add_to_grid_layout(delay_gridlayout, 2)
        self.wet_knob = pydaw_knob_control(
            f_knob_size, _("Wet"), pydaw_ports.MODULEX_WET,
            self.plugin_rel_callback, self.plugin_val_callback, -30, 0, -30,
            KC_INTEGER, self.port_dict, self.preset_manager)
        self.wet_knob.add_to_grid_layout(delay_gridlayout, 3)
        self.duck_knob = pydaw_knob_control(
            f_knob_size, _("Duck"), pydaw_ports.MODULEX_DUCK,
            self.plugin_rel_callback, self.plugin_val_callback,
            -40, 0, 0, KC_INTEGER, self.port_dict, self.preset_manager)
        self.duck_knob.add_to_grid_layout(delay_gridlayout, 4)
        self.cutoff_knob = pydaw_knob_control(
            f_knob_size, _("Cutoff"), pydaw_ports.MODULEX_CUTOFF,
            self.plugin_rel_callback, self.plugin_val_callback,
            40, 118, 90, KC_PITCH, self.port_dict, self.preset_manager)
        self.cutoff_knob.add_to_grid_layout(delay_gridlayout, 5)
        self.stereo_knob = pydaw_knob_control(
            f_knob_size, _("Stereo"), pydaw_ports.MODULEX_STEREO,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 100, KC_DECIMAL, self.port_dict, self.preset_manager)
        self.stereo_knob.add_to_grid_layout(delay_gridlayout, 6)

        self.reverb_groupbox = QtGui.QGroupBox(_("Reverb"))
        self.reverb_groupbox.setObjectName("plugin_groupbox")
        self.reverb_groupbox_gridlayout = QtGui.QGridLayout(
            self.reverb_groupbox)
        self.reverb_hlayout = QtGui.QHBoxLayout()
        self.delay_vlayout.addLayout(self.reverb_hlayout)
        self.reverb_hlayout.addWidget(self.reverb_groupbox)
        self.reverb_hlayout.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))

        f_note_triggered_label = QtGui.QLabel(_("Note-Triggered Effects"))
        f_note_triggered_label.setToolTip(
            _("The below effects are triggered when you play their \n"
            "selected note.  Usually you will want to change the note\n"
            "range on any instrument plugins on the same track to not\n"
            "include the selected note for these effects."))
        self.delay_vlayout.addWidget(f_note_triggered_label)
        self.note_triggered_hlayout = QtGui.QHBoxLayout()
        self.delay_vlayout.addLayout(self.note_triggered_hlayout)

        self.reverb_time_knob = pydaw_knob_control(
            f_knob_size, _("Time"), pydaw_ports.MODULEX_REVERB_TIME,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 50, KC_DECIMAL, self.port_dict, self.preset_manager)
        self.reverb_time_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 3)

        self.reverb_dry_knob = pydaw_knob_control(
            f_knob_size, _("Dry"), pydaw_ports.MODULEX_REVERB_DRY,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 100, KC_DECIMAL, self.port_dict, self.preset_manager)
        self.reverb_dry_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 9)

        self.reverb_wet_knob = pydaw_knob_control(
            f_knob_size, _("Wet"), pydaw_ports.MODULEX_REVERB_WET,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 0, KC_DECIMAL, self.port_dict, self.preset_manager)
        self.reverb_wet_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 10)

        self.reverb_color_knob = pydaw_knob_control(
            f_knob_size, _("Color"), pydaw_ports.MODULEX_REVERB_COLOR,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 50, KC_DECIMAL, self.port_dict, self.preset_manager)
        self.reverb_color_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 15)

        self.reverb_predelay_knob = pydaw_knob_control(
            f_knob_size, _("PreDelay"), pydaw_ports.MODULEX_REVERB_PRE_DELAY,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 1, KC_TIME_DECIMAL, self.port_dict, self.preset_manager)
        self.reverb_predelay_knob.add_to_grid_layout(
            self.reverb_groupbox_gridlayout, 21)

        self.gate_groupbox = QtGui.QGroupBox(_("Gate"))
        self.gate_groupbox.setObjectName("plugin_groupbox")
        self.note_triggered_hlayout.addWidget(self.gate_groupbox)
        self.gate_gridlayout = QtGui.QGridLayout(self.gate_groupbox)
        self.gate_on_checkbox = pydaw_checkbox_control(
            "On", pydaw_ports.MODULEX_GATE_MODE,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, a_preset_mgr=self.preset_manager)
        self.gate_on_checkbox.add_to_grid_layout(self.gate_gridlayout, 3)
        self.gate_note_selector = pydaw_note_selector_widget(
            pydaw_ports.MODULEX_GATE_NOTE,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, 120, self.preset_manager)
        self.gate_note_selector.add_to_grid_layout(self.gate_gridlayout, 6)
        self.gate_wet_knob = pydaw_knob_control(
            f_knob_size, _("Wet"), pydaw_ports.MODULEX_GATE_WET,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 0, KC_DECIMAL, self.port_dict, self.preset_manager)
        self.gate_wet_knob.add_to_grid_layout(self.gate_gridlayout, 9)

        self.gate_pitch_knob = pydaw_knob_control(
            f_knob_size, _("Pitch"), pydaw_ports.MODULEX_GATE_PITCH,
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
            "On", pydaw_ports.MODULEX_GLITCH_ON,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, a_preset_mgr=self.preset_manager)
        self.glitch_on_checkbox.add_to_grid_layout(self.glitch_gridlayout, 3)
        self.glitch_note_selector = pydaw_note_selector_widget(
            pydaw_ports.MODULEX_GLITCH_NOTE,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, 119, self.preset_manager)
        self.glitch_note_selector.add_to_grid_layout(self.glitch_gridlayout, 6)
        self.glitch_time_knob = pydaw_knob_control(
            f_knob_size, _("Time"), pydaw_ports.MODULEX_GLITCH_TIME,
            self.plugin_rel_callback, self.plugin_val_callback,
            1, 25, 10, KC_TIME_DECIMAL, self.port_dict, self.preset_manager)
        self.glitch_time_knob.add_to_grid_layout(self.glitch_gridlayout, 9)
        self.glitch_pb_knob = pydaw_knob_control(
            f_knob_size, _("Pitchbend"), pydaw_ports.MODULEX_GLITCH_PB,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 36, 0, KC_INTEGER, self.port_dict, self.preset_manager)
        self.glitch_pb_knob.add_to_grid_layout(self.glitch_gridlayout, 12)

        self.delay_spacer_layout = QtGui.QVBoxLayout()
        self.delay_vlayout.addLayout(self.delay_spacer_layout)
        self.delay_spacer_layout.addItem(
            QtGui.QSpacerItem(1, 1, vPolicy=QtGui.QSizePolicy.Expanding))

        self.eq6 = eq6_widget(
            pydaw_ports.MODULEX_EQ_ON,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, a_preset_mgr=self.preset_manager,
            a_size=f_knob_size)

        self.tab_widget.addTab(self.eq6.widget, _("EQ/Spectrum"))

        self.spectrum_enabled = pydaw_null_control(
            pydaw_ports.MODULEX_SPECTRUM_ENABLED,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, self.port_dict)

        self.open_plugin_file()
        self.set_midi_learn(pydaw_ports.MODULEX_PORT_MAP)

    def open_plugin_file(self):
        pydaw_abstract_plugin_ui.open_plugin_file(self)
        self.eq6.update_viewer()

    def save_plugin_file(self):
        # Don't allow the spectrum analyzer to run at startup
        self.spectrum_enabled.set_value(0)
        pydaw_abstract_plugin_ui.save_plugin_file(self)

    def bpmSyncPressed(self):
        f_frac = 1.0
        f_switch = (self.beat_frac_combobox.currentIndex())
        f_dict = {0 : 0.25, 1 : 0.33333, 2 : 0.5, 3 : 0.666666,
                  4 : 0.75, 5 : 1.0}
        f_frac = f_dict[f_switch]
        f_seconds_per_beat = 60/(self.bpm_spinbox.value())
        f_result = int(f_seconds_per_beat * f_frac * 100)
        self.delay_time_knob.set_value(f_result)

    def set_window_title(self, a_track_name):
        self.track_name = str(a_track_name)
        self.widget.setWindowTitle(
            "MusiKernel Modulex - {}".format(self.track_name))

    def widget_close_event(self, a_event):
        print("Disabling spectrum")
        self.plugin_val_callback(
            pydaw_ports.MODULEX_SPECTRUM_ENABLED, 0.0)
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
                pydaw_ports.MODULEX_SPECTRUM_ENABLED, 1.0)
        else:
            print("Disabling spectrum")
            self.plugin_val_callback(
                pydaw_ports.MODULEX_SPECTRUM_ENABLED, 0.0)

    def ui_message(self, a_name, a_value):
        if a_name == "spectrum":
            self.eq6.set_spectrum(a_value)
        else:
            pydaw_abstract_plugin_ui.ui_message(a_name, a_value)


