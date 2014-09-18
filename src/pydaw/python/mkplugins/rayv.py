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


class rayv_plugin_ui(pydaw_abstract_plugin_ui):
    def __init__(self, a_val_callback, a_project,
                 a_folder, a_plugin_uid, a_track_name,
                 a_stylesheet, a_configure_callback, a_midi_learn_callback,
                 a_cc_map_callback):
        pydaw_abstract_plugin_ui.__init__(
            self, a_val_callback, a_project, a_plugin_uid, a_stylesheet,
            a_configure_callback, a_folder, a_midi_learn_callback,
            a_cc_map_callback)
        self._plugin_name = "RAYV"
        self.set_window_title(a_track_name)
        self.is_instrument = True
        f_osc_types = [_("Saw"), _("Square"), _("Triangle"),
                       _("Sine"), _("Off")]
        f_lfo_types = [_("Off"), _("Sine"), _("Triangle")]
        self.preset_manager = pydaw_preset_manager_widget(
            self.get_plugin_name())
        self.main_layout = QtGui.QVBoxLayout()
        self.main_layout.setMargin(3)
        self.layout.addLayout(self.main_layout)
        self.layout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.hlayout0 = QtGui.QHBoxLayout()
        self.main_layout.addLayout(self.hlayout0)
        self.hlayout0.addWidget(self.preset_manager.group_box)
        self.hlayout0.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))
        f_logo_label = QtGui.QLabel()
        f_pixmap = QtGui.QPixmap(
            "{}/lib/{}/themes/default/rayv.png".format(
            pydaw_util.global_pydaw_install_prefix,
            pydaw_util.global_pydaw_version_string)).scaled(
                120, 60, transformMode=QtCore.Qt.SmoothTransformation)
        f_logo_label.setMinimumSize(90, 30)
        f_logo_label.setPixmap(f_pixmap)
        f_knob_size = 55

        self.hlayout0.addWidget(f_logo_label)
        self.hlayout1 = QtGui.QHBoxLayout()
        self.main_layout.addLayout(self.hlayout1)
        self.osc1 = pydaw_osc_widget(
            f_knob_size, pydaw_ports.RAYV_OSC1_PITCH,
            pydaw_ports.RAYV_OSC1_TUNE, pydaw_ports.RAYV_OSC1_VOLUME,
            pydaw_ports.RAYV_OSC1_TYPE, f_osc_types,
            self.plugin_rel_callback, self.plugin_val_callback,
            _("Oscillator 1"), self.port_dict,
            a_preset_mgr=self.preset_manager)
        self.hlayout1.addWidget(self.osc1.group_box)
        self.adsr_amp = pydaw_adsr_widget(
            f_knob_size, True, pydaw_ports.RAYV_ATTACK, pydaw_ports.RAYV_DECAY,
            pydaw_ports.RAYV_SUSTAIN, pydaw_ports.RAYV_RELEASE,
            _("ADSR Amp"), self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager,
            a_prefx_port=pydaw_ports.RAYV_ADSR_PREFX, a_knob_type=KC_LOG_TIME)
        self.hlayout1.addWidget(self.adsr_amp.groupbox)
        self.groupbox_distortion = QtGui.QGroupBox(_("Distortion"))
        self.groupbox_distortion.setObjectName("plugin_groupbox")
        self.groupbox_distortion_layout = QtGui.QGridLayout(
            self.groupbox_distortion)
        self.hlayout1.addWidget(self.groupbox_distortion)
        self.dist = pydaw_knob_control(
            f_knob_size, _("Gain"), pydaw_ports.RAYV_DIST,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 48, 15, KC_INTEGER, self.port_dict, self.preset_manager)
        self.dist.add_to_grid_layout(self.groupbox_distortion_layout, 0)
        self.dist_wet = pydaw_knob_control(
            f_knob_size, _("Wet"), pydaw_ports.RAYV_DIST_WET,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 0, KC_NONE, self.port_dict, self.preset_manager)
        self.dist_wet.add_to_grid_layout(self.groupbox_distortion_layout, 1)
        self.hlayout2 = QtGui.QHBoxLayout()
        self.main_layout.addLayout(self.hlayout2)
        self.osc2 = pydaw_osc_widget(
            f_knob_size, pydaw_ports.RAYV_OSC2_PITCH,
            pydaw_ports.RAYV_OSC2_TUNE, pydaw_ports.RAYV_OSC2_VOLUME,
            pydaw_ports.RAYV_OSC2_TYPE, f_osc_types,
            self.plugin_rel_callback, self.plugin_val_callback,
            _("Oscillator 2"), self.port_dict, self.preset_manager, 4)
        self.hlayout2.addWidget(self.osc2.group_box)
        self.sync_groupbox = QtGui.QGroupBox(_("Sync"))
        self.sync_groupbox.setObjectName("plugin_groupbox")
        self.hlayout2.addWidget(self.sync_groupbox)
        self.sync_gridlayout = QtGui.QGridLayout(self.sync_groupbox)
        self.sync_gridlayout.setMargin(3)
        self.hard_sync = pydaw_checkbox_control(
            "On", pydaw_ports.RAYV_OSC_HARD_SYNC,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager)
        self.hard_sync.control.setToolTip(
            _("Setting self hard sync's Osc1 to Osc2. Usually you "
            "would want to distort and pitchbend if this is enabled."))
        self.sync_gridlayout.addWidget(
            self.hard_sync.control, 1, 0, QtCore.Qt.AlignCenter)
        self.groupbox_noise = QtGui.QGroupBox(_("Noise"))
        self.groupbox_noise.setObjectName("plugin_groupbox")
        self.noise_layout = QtGui.QGridLayout(self.groupbox_noise)
        self.noise_layout.setMargin(3)
        self.hlayout2.addWidget(self.groupbox_noise)
        self.noise_amp = pydaw_knob_control(
            f_knob_size, _("Vol"), pydaw_ports.RAYV_NOISE_AMP,
            self.plugin_rel_callback, self.plugin_val_callback,
            -60, 0, -30, KC_INTEGER, self.port_dict, self.preset_manager)
        self.noise_amp.add_to_grid_layout(self.noise_layout, 0)
        self.adsr_filter = pydaw_adsr_widget(
            f_knob_size, False, pydaw_ports.RAYV_FILTER_ATTACK,
            pydaw_ports.RAYV_FILTER_DECAY, pydaw_ports.RAYV_FILTER_SUSTAIN,
            pydaw_ports.RAYV_FILTER_RELEASE, _("ADSR Filter"),
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager, a_knob_type=KC_LOG_TIME)
        self.hlayout2.addWidget(self.adsr_filter.groupbox)
        self.filter = pydaw_filter_widget(
            f_knob_size, self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, pydaw_ports.RAYV_TIMBRE, pydaw_ports.RAYV_RES,
            a_preset_mgr=self.preset_manager)
        self.hlayout2.addWidget(self.filter.groupbox)
        self.filter_env_amt = pydaw_knob_control(
            f_knob_size, _("Env Amt"), pydaw_ports.RAYV_FILTER_ENV_AMT,
            self.plugin_rel_callback, self.plugin_val_callback,
            -36, 36, 0, KC_INTEGER, self.port_dict, self.preset_manager)
        self.filter_env_amt.add_to_grid_layout(self.filter.layout, 2)
        self.filter_keytrk = pydaw_knob_control(
            f_knob_size, _("KeyTrk"), pydaw_ports.RAYV_FILTER_KEYTRK,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 0, KC_NONE, self.port_dict, self.preset_manager)
        self.filter_keytrk.add_to_grid_layout(self.filter.layout, 3)
        self.hlayout3 = QtGui.QHBoxLayout()
        self.main_layout.addLayout(self.hlayout3)
        self.master = pydaw_master_widget(
            f_knob_size, self.plugin_rel_callback, self.plugin_val_callback,
            pydaw_ports.RAYV_MASTER_VOLUME, pydaw_ports.RAYV_MASTER_GLIDE,
            pydaw_ports.RAYV_MASTER_PITCHBEND_AMT, self.port_dict, _("Master"),
            pydaw_ports.RAYV_MASTER_UNISON_VOICES,
            pydaw_ports.RAYV_MASTER_UNISON_SPREAD,
            self.preset_manager, a_poly_port=pydaw_ports.RAYV_MONO_MODE,
            a_min_note_port=pydaw_ports.RAYV_MIN_NOTE,
            a_max_note_port=pydaw_ports.RAYV_MAX_NOTE)
        self.hlayout3.addWidget(self.master.group_box)

        self.pitch_env = pydaw_ramp_env_widget(
            f_knob_size, self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, pydaw_ports.RAYV_PITCH_ENV_TIME,
            pydaw_ports.RAYV_PITCH_ENV_AMT, _("Pitch Env"),
            self.preset_manager, pydaw_ports.RAYV_RAMP_CURVE)
        self.hlayout1.addWidget(self.pitch_env.groupbox)
        self.lfo = pydaw_lfo_widget(
            f_knob_size, self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, pydaw_ports.RAYV_LFO_FREQ,
            pydaw_ports.RAYV_LFO_TYPE, f_lfo_types, _("LFO"),
            self.preset_manager, pydaw_ports.RAYV_LFO_PHASE)
        self.hlayout3.addWidget(self.lfo.groupbox)

        self.lfo_amp = pydaw_knob_control(
            f_knob_size, _("Amp"), pydaw_ports.RAYV_LFO_AMP,
            self.plugin_rel_callback, self.plugin_val_callback,
            -24, 24, 0, KC_INTEGER, self.port_dict, self.preset_manager)
        self.lfo_amp.add_to_grid_layout(self.lfo.layout, 7)
        self.lfo_pitch = pydaw_knob_control(
            f_knob_size, _("Pitch"), pydaw_ports.RAYV_LFO_PITCH,
            self.plugin_rel_callback, self.plugin_val_callback,
            -36, 36, 0, KC_INTEGER, self.port_dict, self.preset_manager)
        self.lfo_pitch.add_to_grid_layout(self.lfo.layout, 8)

        self.lfo_pitch_fine = pydaw_knob_control(
            f_knob_size, _("Fine"), pydaw_ports.RAYV_LFO_PITCH_FINE,
            self.plugin_rel_callback, self.plugin_val_callback,
            -100, 100, 0, KC_DECIMAL, self.port_dict, self.preset_manager)
        self.lfo_pitch_fine.add_to_grid_layout(self.lfo.layout, 9)

        self.lfo_cutoff = pydaw_knob_control(
            f_knob_size, _("Filter"), pydaw_ports.RAYV_LFO_FILTER,
            self.plugin_rel_callback, self.plugin_val_callback,
            -48, 48, 0, KC_INTEGER, self.port_dict, self.preset_manager)
        self.lfo_cutoff.add_to_grid_layout(self.lfo.layout, 10)

        self.open_plugin_file()
        self.set_midi_learn(pydaw_ports.RAYV_PORT_MAP)

    def set_window_title(self, a_track_name):
        self.track_name = str(a_track_name)
        self.widget.setWindowTitle(
            "MusiKernel Ray-V - {}".format(self.track_name))


