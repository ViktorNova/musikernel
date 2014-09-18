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


class wayv_plugin_ui(pydaw_abstract_plugin_ui):
    def __init__(self, a_val_callback, a_project,
                 a_folder, a_plugin_uid, a_track_name, a_stylesheet,
                 a_configure_callback, a_midi_learn_callback,
                 a_cc_map_callback):
        pydaw_abstract_plugin_ui.__init__(
            self, a_val_callback, a_project, a_plugin_uid, a_stylesheet,
            a_configure_callback, a_folder, a_midi_learn_callback,
            a_cc_map_callback)
        self._plugin_name = "WAYV"
        self.set_window_title(a_track_name)
        self.is_instrument = True

        f_osc_types = [_("Off"),
            #Saw-like waves
            _("Plain Saw"), _("SuperbSaw"), _("Viral Saw"), _("Soft Saw"),
            _("Mid Saw"), _("Lush Saw"),
            #Square-like waves
            _("Evil Square"), _("Punchy Square"), _("Soft Square"),
            #Glitchy and distorted waves
            _("Pink Glitch"), _("White Glitch"), _("Acid"), _("Screetch"),
            #Sine and triangle-like waves
            _("Thick Bass"), _("Rattler"), _("Deep Saw"), _("Sine"),
            #The custom additive oscillator tab
            _("(Additive 1)"), _("(Additive 2)"), _("(Additive 3)")
        ]

        self.fm_knobs = []
        self.fm_origin = None
        self.fm_macro_spinboxes = [[] for x in range(2)]

        f_lfo_types = [_("Off"), _("Sine"), _("Triangle")]
        self.tab_widget = QtGui.QTabWidget()
        self.layout.addWidget(self.tab_widget)
        self.layout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.osc_tab = QtGui.QWidget()
        self.osc_tab_vlayout = QtGui.QVBoxLayout(self.osc_tab)
        self.osc_scrollarea = QtGui.QScrollArea()
        self.osc_scrollarea.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.osc_scrollarea.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn)
        self.tab_widget.addTab(self.osc_tab, _("Oscillators"))
        self.fm_tab = QtGui.QWidget()
        self.tab_widget.addTab(self.fm_tab, _("FM"))
        self.modulation_tab = QtGui.QWidget()
        self.tab_widget.addTab(self.modulation_tab, _("Modulation"))
        self.poly_fx_tab = QtGui.QWidget()
        self.tab_widget.addTab(self.poly_fx_tab, _("PolyFX"))
        self.osc_tab_widget = QtGui.QWidget()
        self.osc_tab_widget.setObjectName("plugin_ui")
        self.osc_scrollarea.setWidget(self.osc_tab_widget)
        self.osc_scrollarea.setWidgetResizable(True)
        self.oscillator_layout = QtGui.QVBoxLayout(self.osc_tab_widget)
        self.preset_manager = pydaw_preset_manager_widget(
            self.get_plugin_name(), self.configure_dict,
            self.reconfigure_plugin)
        self.preset_hlayout = QtGui.QHBoxLayout()
        self.preset_hlayout.addWidget(self.preset_manager.group_box)
        self.preset_hlayout.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))
        self.osc_tab_vlayout.addLayout(self.preset_hlayout)
        self.osc_tab_vlayout.addWidget(self.osc_scrollarea)

        self.hlayout0 = QtGui.QHBoxLayout()
        self.oscillator_layout.addLayout(self.hlayout0)
        self.hlayout0.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))
        f_knob_size = 48

        for f_i in range(1, 7):
            f_hlayout1 = QtGui.QHBoxLayout()
            self.oscillator_layout.addLayout(f_hlayout1)
            f_osc1 = pydaw_osc_widget(
                f_knob_size,
                getattr(pydaw_ports, "WAYV_OSC{}_PITCH".format(f_i)),
                getattr(pydaw_ports, "WAYV_OSC{}_TUNE".format(f_i)),
                getattr(pydaw_ports, "WAYV_OSC{}_VOLUME".format(f_i)),
                getattr(pydaw_ports, "WAYV_OSC{}_TYPE".format(f_i)),
                f_osc_types,
                self.plugin_rel_callback, self.plugin_val_callback,
                _("Oscillator {}".format(f_i)),
                self.port_dict, self.preset_manager,
                1 if f_i == 1 else 0)
            f_osc1.pitch_knob.control.setRange(-72, 72)
            f_osc1_uni_voices = pydaw_knob_control(
                f_knob_size, _("Unison"),
                getattr(pydaw_ports, "WAYV_OSC{}_UNISON_VOICES".format(f_i)),
                self.plugin_rel_callback, self.plugin_val_callback,
                1, 7, 1, KC_INTEGER, self.port_dict, self.preset_manager)
            f_osc1_uni_voices.add_to_grid_layout(f_osc1.grid_layout, 4)
            f_osc1_uni_spread = pydaw_knob_control(
                f_knob_size, _("Spread"), getattr(pydaw_ports,
                "WAYV_OSC{}_UNISON_SPREAD".format(f_i)),
                self.plugin_rel_callback, self.plugin_val_callback,
                0, 100, 50, KC_DECIMAL, self.port_dict, self.preset_manager)
            f_osc1_uni_spread.add_to_grid_layout(f_osc1.grid_layout, 5)

            f_hlayout1.addWidget(f_osc1.group_box)

            f_adsr_amp1 = pydaw_adsr_widget(
                f_knob_size, True,
                getattr(pydaw_ports, "WAYV_ATTACK{}".format(f_i)),
                getattr(pydaw_ports, "WAYV_DECAY{}".format(f_i)),
                getattr(pydaw_ports, "WAYV_SUSTAIN{}".format(f_i)),
                getattr(pydaw_ports, "WAYV_RELEASE{}".format(f_i)),
                _("DAHDSR Osc{}".format(f_i)),
                self.plugin_rel_callback,
                self.plugin_val_callback,
                self.port_dict, self.preset_manager,
                a_knob_type=KC_LOG_TIME,
                a_delay_port=
                getattr(pydaw_ports, "WAYV_ADSR{}_DELAY".format(f_i)),
                a_hold_port=
                getattr(pydaw_ports, "WAYV_ADSR{}_HOLD".format(f_i)))
            f_hlayout1.addWidget(f_adsr_amp1.groupbox)

            f_adsr_amp1_checkbox = pydaw_checkbox_control(
                _("On"), getattr(pydaw_ports,
                "WAYV_ADSR{}_CHECKBOX".format(f_i)),
                self.plugin_rel_callback, self.plugin_val_callback,
                self.port_dict, self.preset_manager)
            f_adsr_amp1_checkbox.add_to_grid_layout(f_adsr_amp1.layout, 15)

            f_hlayout1.addItem(
                QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))


        ######################


        self.fm_vlayout = QtGui.QVBoxLayout(self.fm_tab)

        # FM Matrix

        self.fm_matrix_hlayout = QtGui.QHBoxLayout()
        self.fm_vlayout.addLayout(self.fm_matrix_hlayout)
        self.fm_matrix_hlayout.addWidget(QtGui.QLabel("FM Matrix"))
        self.fm_matrix = QtGui.QTableWidget()

        self.fm_matrix.setCornerButtonEnabled(False)
        self.fm_matrix.setRowCount(6)
        self.fm_matrix.setColumnCount(6)
        self.fm_matrix.setFixedHeight(228)
        self.fm_matrix.setFixedWidth(447)
        f_fm_src_matrix_labels = ["From Osc{}".format(x) for x in range(1, 7)]
        f_fm_dest_matrix_labels = ["To\nOsc{}".format(x) for x in range(1, 7)]
        self.fm_matrix.setHorizontalHeaderLabels(f_fm_dest_matrix_labels)
        self.fm_matrix.setVerticalHeaderLabels(f_fm_src_matrix_labels)
        self.fm_matrix.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.fm_matrix.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.fm_matrix.horizontalHeader().setResizeMode(
            QtGui.QHeaderView.Fixed)
        self.fm_matrix.verticalHeader().setResizeMode(QtGui.QHeaderView.Fixed)

        self.fm_matrix_hlayout.addWidget(self.fm_matrix)

        for f_i in range(6):
            for f_i2 in range(6):
                f_port = getattr(
                    pydaw_ports, "WAYV_OSC{}_FM{}".format(f_i2 + 1, f_i + 1))
                f_spinbox = pydaw_spinbox_control(
                    None, f_port,
                    self.plugin_rel_callback, self.plugin_val_callback,
                    0, 100, 0, KC_NONE, self.port_dict, self.preset_manager)
                self.fm_matrix.setCellWidget(f_i, f_i2, f_spinbox.control)
                self.fm_knobs.append(f_spinbox)

        self.fm_matrix.resizeColumnsToContents()

        self.fm_matrix_button = QtGui.QPushButton(_("Menu"))
        self.fm_matrix_hlayout.addWidget(
            self.fm_matrix_button,
            alignment=QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

        self.fm_matrix_menu = QtGui.QMenu(self.widget)
        self.fm_matrix_button.setMenu(self.fm_matrix_menu)
        f_origin_action = self.fm_matrix_menu.addAction(_("Set Origin"))
        f_origin_action.triggered.connect(self.set_fm_origin)
        f_return_action = self.fm_matrix_menu.addAction(_("Return to Origin"))
        f_return_action.triggered.connect(self.return_to_origin)
        self.fm_matrix_menu.addSeparator()
        f_macro1_action = self.fm_matrix_menu.addAction(_("Set Macro 1 End"))
        f_macro1_action.triggered.connect(self.set_fm_macro1_end)
        f_macro2_action = self.fm_matrix_menu.addAction(_("Set Macro 2 End"))
        f_macro2_action.triggered.connect(self.set_fm_macro2_end)
        self.fm_matrix_menu.addSeparator()
        f_return_macro1_action = self.fm_matrix_menu.addAction(
            _("Return to Macro 1 End"))
        f_return_macro1_action.triggered.connect(self.return_fm_macro1_end)
        f_return_macro2_action = self.fm_matrix_menu.addAction(
            _("Return to Macro 2 End"))
        f_return_macro2_action.triggered.connect(self.return_fm_macro2_end)
        self.fm_matrix_menu.addSeparator()
        f_clear_fm_action = self.fm_matrix_menu.addAction(_("Clear All"))
        f_clear_fm_action.triggered.connect(self.clear_all)

        self.fm_matrix_hlayout.addWidget(
            QtGui.QLabel(_("FM\nModulation\nMacros")))

        self.fm_macro_knobs_gridlayout = QtGui.QGridLayout()
        self.fm_macro_knobs_gridlayout.addItem(
            QtGui.QSpacerItem(1, 1, vPolicy=QtGui.QSizePolicy.Expanding),
            10, 0)

        self.fm_matrix_hlayout.addLayout(self.fm_macro_knobs_gridlayout)

        self.fm_matrix_hlayout.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))

        self.fm_macro_knobs = []
        self.osc_amp_mod_matrix_spinboxes = [[] for x in range(2)]

        self.fm_macro_labels_hlayout = QtGui.QHBoxLayout()
        self.fm_vlayout.addLayout(self.fm_macro_labels_hlayout)
        self.fm_macro_matrix_hlayout = QtGui.QHBoxLayout()
        self.fm_vlayout.addLayout(self.fm_macro_matrix_hlayout)

        for f_i in range(2):
            f_port = getattr(pydaw_ports, "WAYV_FM_MACRO{}".format(f_i + 1))
            f_macro = pydaw_knob_control(
                f_knob_size, _("Macro{}".format(f_i + 1)), f_port,
                self.plugin_rel_callback, self.plugin_val_callback,
                0, 100, 0, KC_DECIMAL, self.port_dict, self.preset_manager)
            f_macro.add_to_grid_layout(self.fm_macro_knobs_gridlayout, f_i)
            self.fm_macro_knobs.append(f_macro)

            f_fm_macro_matrix = QtGui.QTableWidget()
            self.fm_macro_labels_hlayout.addWidget(
                QtGui.QLabel("Macro {}".format(f_i + 1),
                f_fm_macro_matrix), -1)

            f_fm_macro_matrix.setCornerButtonEnabled(False)
            f_fm_macro_matrix.setRowCount(7)
            f_fm_macro_matrix.setColumnCount(6)
            f_fm_macro_matrix.setFixedHeight(264)
            f_fm_macro_matrix.setFixedWidth(474)
            f_fm_src_matrix_labels = ["From Osc{}".format(x)
                for x in range(1, 7)] + ["Vol"]
            f_fm_dest_matrix_labels = ["To\nOsc{}".format(x)
                for x in range(1, 7)]
            f_fm_macro_matrix.setHorizontalHeaderLabels(
                f_fm_dest_matrix_labels)
            f_fm_macro_matrix.setVerticalHeaderLabels(f_fm_src_matrix_labels)
            f_fm_macro_matrix.setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff)
            f_fm_macro_matrix.setVerticalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff)
            f_fm_macro_matrix.horizontalHeader().setResizeMode(
                QtGui.QHeaderView.Fixed)
            f_fm_macro_matrix.verticalHeader().setResizeMode(
                QtGui.QHeaderView.Fixed)

            self.fm_macro_matrix_hlayout.addWidget(f_fm_macro_matrix)

            for f_i2 in range(6):
                for f_i3 in range(6):
                    f_port = getattr(
                        pydaw_ports, "WAYV_FM_MACRO{}_OSC{}_FM{}".format(
                            f_i + 1, f_i3 + 1, f_i2 + 1))
                    f_spinbox = pydaw_spinbox_control(
                        None, f_port,
                        self.plugin_rel_callback, self.plugin_val_callback,
                        -100, 100, 0, KC_NONE, self.port_dict,
                        self.preset_manager)
                    f_fm_macro_matrix.setCellWidget(
                        f_i2, f_i3, f_spinbox.control)
                    self.fm_macro_spinboxes[f_i].append(f_spinbox)

                f_port = getattr(
                    pydaw_ports, "WAYV_FM_MACRO{}_OSC{}_VOL".format(
                    f_i + 1, f_i2 + 1))
                f_spinbox = pydaw_spinbox_control(
                    None, f_port,
                    self.plugin_rel_callback, self.plugin_val_callback,
                    -100, 100, 0, KC_NONE, self.port_dict, self.preset_manager)
                f_fm_macro_matrix.setCellWidget(6, f_i2, f_spinbox.control)
                self.osc_amp_mod_matrix_spinboxes[f_i].append(f_spinbox)
                f_fm_macro_matrix.resizeColumnsToContents()
        self.fm_macro_matrix_hlayout.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))
        self.fm_vlayout.addItem(
            QtGui.QSpacerItem(1, 1, vPolicy=QtGui.QSizePolicy.Expanding))

        ############################

        self.modulation_vlayout = QtGui.QVBoxLayout(self.modulation_tab)

        self.hlayout_master = QtGui.QHBoxLayout()
        self.modulation_vlayout.addLayout(self.hlayout_master)
        self.master = pydaw_master_widget(
            f_knob_size, self.plugin_rel_callback,
            self.plugin_val_callback, pydaw_ports.WAYV_MASTER_VOLUME,
            pydaw_ports.WAYV_MASTER_GLIDE,
            pydaw_ports.WAYV_MASTER_PITCHBEND_AMT,
            self.port_dict, a_preset_mgr=self.preset_manager,
            a_poly_port=pydaw_ports.WAYV_MONO_MODE,
            a_min_note_port=pydaw_ports.WAYV_MIN_NOTE,
            a_max_note_port=pydaw_ports.WAYV_MAX_NOTE)

        self.hlayout_master.addWidget(self.master.group_box)

        self.adsr_amp_main = pydaw_adsr_widget(
            f_knob_size, True, pydaw_ports.WAYV_ATTACK_MAIN,
            pydaw_ports.WAYV_DECAY_MAIN, pydaw_ports.WAYV_SUSTAIN_MAIN,
            pydaw_ports.WAYV_RELEASE_MAIN, _("AHDSR Master"),
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager,
            a_prefx_port=pydaw_ports.WAYV_ADSR_PREFX,
            a_knob_type=KC_LOG_TIME, a_hold_port=pydaw_ports.WAYV_HOLD_MAIN)
        self.hlayout_master.addWidget(self.adsr_amp_main.groupbox)

        self.perc_env = pydaw_perc_env_widget(
            f_knob_size, self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, pydaw_ports.WAYV_PERC_ENV_TIME1,
            pydaw_ports.WAYV_PERC_ENV_PITCH1, pydaw_ports.WAYV_PERC_ENV_TIME2,
            pydaw_ports.WAYV_PERC_ENV_PITCH2, pydaw_ports.WAYV_PERC_ENV_ON,
            a_preset_mgr=self.preset_manager)

        self.hlayout_master2 = QtGui.QHBoxLayout()
        self.modulation_vlayout.addLayout(self.hlayout_master2)
        self.hlayout_master2.addWidget(self.perc_env.groupbox)

        self.adsr_noise = pydaw_adsr_widget(
            f_knob_size, True, pydaw_ports.WAYV_ATTACK_NOISE,
            pydaw_ports.WAYV_DECAY_NOISE, pydaw_ports.WAYV_SUSTAIN_NOISE,
            pydaw_ports.WAYV_RELEASE_NOISE, _("DAHDSR Noise"),
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager,
            a_knob_type=KC_LOG_TIME, a_hold_port=pydaw_ports.WAYV_HOLD_NOISE,
            a_delay_port=pydaw_ports.WAYV_DELAY_NOISE)
        self.hlayout_master2.addWidget(self.adsr_noise.groupbox)
        self.adsr_noise_on = pydaw_checkbox_control(
            "On", pydaw_ports.WAYV_ADSR_NOISE_ON,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager)
        self.adsr_noise_on.add_to_grid_layout(self.adsr_noise.layout, 21)

        self.groupbox_noise = QtGui.QGroupBox(_("Noise"))
        self.groupbox_noise.setObjectName("plugin_groupbox")
        self.groupbox_noise_layout = QtGui.QGridLayout(self.groupbox_noise)
        self.hlayout_master2.addWidget(self.groupbox_noise)
        self.noise_amp = pydaw_knob_control(
            f_knob_size, _("Vol"), pydaw_ports.WAYV_NOISE_AMP,
            self.plugin_rel_callback, self.plugin_val_callback,
            -60, 0, -30, KC_INTEGER, self.port_dict, self.preset_manager)
        self.noise_amp.add_to_grid_layout(self.groupbox_noise_layout, 0)

        self.noise_type = pydaw_combobox_control(
            87, _("Type"), pydaw_ports.WAYV_NOISE_TYPE,
            self.plugin_rel_callback, self.plugin_val_callback,
            [_("Off"), _("White"), _("Pink")], self.port_dict,
             a_preset_mgr=self.preset_manager)
        self.noise_type.control.setMaximumWidth(87)
        self.noise_type.add_to_grid_layout(self.groupbox_noise_layout, 1)

        self.noise_prefx = pydaw_checkbox_control(
            "PreFX", pydaw_ports.WAYV_NOISE_PREFX,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, a_preset_mgr=self.preset_manager, a_default=1)
        self.noise_prefx.add_to_grid_layout(self.groupbox_noise_layout, 6)

        self.modulation_vlayout.addItem(
            QtGui.QSpacerItem(1, 1, vPolicy=QtGui.QSizePolicy.Expanding))

        self.hlayout_master.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))

        self.hlayout_master2.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))

        self.modulation_vlayout.addWidget(QtGui.QLabel(_("PolyFX")))

        ############################

        self.main_layout = QtGui.QVBoxLayout(self.poly_fx_tab)
        self.hlayout5 = QtGui.QHBoxLayout()
        self.main_layout.addLayout(self.hlayout5)
        self.hlayout6 = QtGui.QHBoxLayout()
        self.main_layout.addLayout(self.hlayout6)
        #From Modulex
        self.fx0 = pydaw_modulex_single(
            _("FX0"), pydaw_ports.WAYV_FX0_KNOB0,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager, a_knob_size=f_knob_size)
        self.hlayout5.addWidget(self.fx0.group_box)
        self.fx1 = pydaw_modulex_single(
            _("FX1"), pydaw_ports.WAYV_FX1_KNOB0,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager, a_knob_size=f_knob_size)
        self.hlayout5.addWidget(self.fx1.group_box)
        self.fx2 = pydaw_modulex_single(
            _("FX2"), pydaw_ports.WAYV_FX2_KNOB0,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager, a_knob_size=f_knob_size)
        self.hlayout6.addWidget(self.fx2.group_box)
        self.fx3 = pydaw_modulex_single(
            _("FX3"), pydaw_ports.WAYV_FX3_KNOB0,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager, a_knob_size=f_knob_size)
        self.hlayout6.addWidget(self.fx3.group_box)

        self.mod_matrix = QtGui.QTableWidget()
        self.mod_matrix.setCornerButtonEnabled(False)
        self.mod_matrix.setRowCount(8)
        self.mod_matrix.setColumnCount(12)
        self.mod_matrix.setFixedHeight(291)
        self.mod_matrix.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.mod_matrix.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.mod_matrix.horizontalHeader().setResizeMode(
            QtGui.QHeaderView.Fixed)
        self.mod_matrix.verticalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
        f_hlabels = ["FX{}\nCtrl{}".format(x, y)
            for x in range(4) for y in range(1, 4)]
        self.mod_matrix.setHorizontalHeaderLabels(f_hlabels)
        self.mod_matrix.setVerticalHeaderLabels(
            [_("DAHDSR 1"), _("DAHDSR 2"), _("Ramp Env"),
             _("LFO"), _("Pitch"), _("Velocity"),
             _("FM Macro 1"), _("FM Macro 2")])

        for f_i_dst in range(4):
            for f_i_src in range(8):
                for f_i_ctrl in range(3):
                    f_ctrl = pydaw_spinbox_control(
                        None,
                        getattr(pydaw_ports, "WAVV_PFXMATRIX_"
                        "GRP0DST{}SRC{}CTRL{}".format(
                        f_i_dst, f_i_src, f_i_ctrl)),
                        self.plugin_rel_callback, self.plugin_val_callback,
                        -100, 100, 0, KC_NONE, self.port_dict,
                        self.preset_manager)
                    f_x = (f_i_dst * 3) + f_i_ctrl
                    self.mod_matrix.setCellWidget(f_i_src, f_x, f_ctrl.control)

        self.main_layout.addWidget(self.mod_matrix)
        self.mod_matrix.resizeColumnsToContents()

        self.main_layout.addItem(
            QtGui.QSpacerItem(1, 1, vPolicy=QtGui.QSizePolicy.Expanding))

        self.hlayout7 = QtGui.QHBoxLayout()
        self.modulation_vlayout.addLayout(self.hlayout7)

        self.adsr_amp = pydaw_adsr_widget(
            f_knob_size, True,
            pydaw_ports.WAYV_ATTACK_PFX1, pydaw_ports.WAYV_DECAY_PFX1,
            pydaw_ports.WAYV_SUSTAIN_PFX1, pydaw_ports.WAYV_RELEASE_PFX1,
            _("DAHDSR 1"), self.plugin_rel_callback,
            self.plugin_val_callback, self.port_dict, self.preset_manager,
            a_knob_type=KC_LOG_TIME,
            a_delay_port=pydaw_ports.WAYV_PFX_ADSR_DELAY,
            a_hold_port=pydaw_ports.WAYV_PFX_ADSR_HOLD)

        self.hlayout7.addWidget(self.adsr_amp.groupbox)

        self.adsr_filter = pydaw_adsr_widget(
            f_knob_size, False, pydaw_ports.WAYV_ATTACK_PFX2,
            pydaw_ports.WAYV_DECAY_PFX2, pydaw_ports.WAYV_SUSTAIN_PFX2,
            pydaw_ports.WAYV_RELEASE_PFX2, _("DAHDSR 2"),
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager,
            a_knob_type=KC_LOG_TIME,
            a_delay_port=pydaw_ports.WAYV_PFX_ADSR_F_DELAY,
            a_hold_port=pydaw_ports.WAYV_PFX_ADSR_F_HOLD)
        self.hlayout7.addWidget(self.adsr_filter.groupbox)

        self.pitch_env = pydaw_ramp_env_widget(
            f_knob_size,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, pydaw_ports.WAYV_RAMP_ENV_TIME,
            pydaw_ports.WAYV_PITCH_ENV_AMT, _("Ramp Env"),
            self.preset_manager, pydaw_ports.WAYV_RAMP_CURVE)
        self.pitch_env.amt_knob.name_label.setText(_("Pitch"))
        self.pitch_env.amt_knob.control.setRange(-60, 60)
        self.hlayout7.addWidget(self.pitch_env.groupbox)
        self.hlayout7.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))

        self.lfo = pydaw_lfo_widget(
            f_knob_size, self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, pydaw_ports.WAYV_LFO_FREQ,
            pydaw_ports.WAYV_LFO_TYPE, f_lfo_types,
            _("LFO"), self.preset_manager, pydaw_ports.WAYV_LFO_PHASE)

        self.lfo_hlayout = QtGui.QHBoxLayout()
        self.modulation_vlayout.addLayout(self.lfo_hlayout)
        self.lfo_hlayout.addWidget(self.lfo.groupbox)

        self.lfo_amount = pydaw_knob_control(
            f_knob_size, _("Amount"), pydaw_ports.WAYV_LFO_AMOUNT,
            self.plugin_rel_callback, self.plugin_val_callback,
            0, 100, 100, KC_DECIMAL, self.port_dict, self.preset_manager)
        self.lfo_amount.add_to_grid_layout(self.lfo.layout, 7)

        self.lfo_amp = pydaw_knob_control(
            f_knob_size, _("Amp"), pydaw_ports.WAYV_LFO_AMP,
            self.plugin_rel_callback, self.plugin_val_callback,
            -24, 24, 0, KC_INTEGER, self.port_dict, self.preset_manager)
        self.lfo_amp.add_to_grid_layout(self.lfo.layout, 8)

        self.lfo_pitch = pydaw_knob_control(
            f_knob_size, _("Pitch"), pydaw_ports.WAYV_LFO_PITCH,
            self.plugin_rel_callback, self.plugin_val_callback,
            -36, 36, 0, KC_INTEGER, self.port_dict, self.preset_manager)
        self.lfo_pitch.add_to_grid_layout(self.lfo.layout, 9)

        self.lfo_pitch_fine = pydaw_knob_control(
            f_knob_size, _("Fine"), pydaw_ports.WAYV_LFO_PITCH_FINE,
            self.plugin_rel_callback, self.plugin_val_callback,
            -100, 100, 0, KC_DECIMAL, self.port_dict, self.preset_manager)
        self.lfo_pitch_fine.add_to_grid_layout(self.lfo.layout, 10)

        self.adsr_lfo = pydaw_adsr_widget(
            f_knob_size, False, pydaw_ports.WAYV_ATTACK_LFO,
            pydaw_ports.WAYV_DECAY_LFO, pydaw_ports.WAYV_SUSTAIN_LFO,
            pydaw_ports.WAYV_RELEASE_LFO, _("DAHDSR LFO"),
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager,
            a_knob_type=KC_LOG_TIME, a_hold_port=pydaw_ports.WAYV_HOLD_LFO,
            a_delay_port=pydaw_ports.WAYV_DELAY_LFO)
        self.lfo_hlayout.addWidget(self.adsr_lfo.groupbox)
        self.adsr_lfo_on = pydaw_checkbox_control(
            "On", pydaw_ports.WAYV_ADSR_LFO_ON,
            self.plugin_rel_callback, self.plugin_val_callback,
            self.port_dict, self.preset_manager)
        self.adsr_lfo_on.add_to_grid_layout(self.adsr_lfo.layout, 21)

        self.lfo_hlayout.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))

        self.additive_osc = pydaw_custom_additive_oscillator(
            self.configure_plugin)
        self.tab_widget.addTab(self.additive_osc.widget, "Additive")

        self.open_plugin_file()
        self.set_midi_learn(pydaw_ports.WAYV_PORT_MAP)

    def open_plugin_file(self):
        pydaw_abstract_plugin_ui.open_plugin_file(self)
        self.set_fm_origin()

    def configure_plugin(self, a_key, a_message):
        self.configure_dict[a_key] = a_message
        self.configure_callback(self.plugin_uid, a_key, a_message)

    def set_configure(self, a_key, a_message):
        self.configure_dict[a_key] = a_message
        if a_key.startswith("wayv_add_ui"):
            self.configure_dict[a_key] = a_message
            f_arr = a_message.split("|")
            self.additive_osc.set_values(int(a_key[-1]), f_arr)
        if a_key.startswith("wayv_add_phase"):
            self.configure_dict[a_key] = a_message
            f_arr = a_message.split("|")
            self.additive_osc.set_phases(int(a_key[-1]), f_arr)
        elif a_key.startswith("wayv_add_eng"):
            pass
        else:
            print("Way-V: Unknown configure message '{}'".format(a_key))

    def reconfigure_plugin(self, a_dict):
        # Clear existing sample tables
        f_ui_config_keys = ["wayv_add_ui0", "wayv_add_ui1", "wayv_add_ui2"]
        f_eng_config_keys = ["wayv_add_eng0", "wayv_add_eng1", "wayv_add_eng2"]
        f_ui_phase_keys = ["wayv_add_phase0", "wayv_add_phase1",
                           "wayv_add_phase2"]
        f_empty_ui_val = "|".join(["-30"] * ADDITIVE_OSC_HARMONIC_COUNT)
        f_empty_eng_val = "{}|{}".format(ADDITIVE_WAVETABLE_SIZE,
            "|".join(["0.0"] * ADDITIVE_WAVETABLE_SIZE))
        for f_key in (f_ui_config_keys + f_ui_phase_keys):
            if f_key in a_dict:
                self.configure_plugin(f_key, a_dict[f_key])
                self.set_configure(f_key, a_dict[f_key])
            else:
                self.configure_plugin(f_key, f_empty_ui_val)
                self.set_configure(f_key, f_empty_ui_val)
        for f_key in f_eng_config_keys:
            if f_key in a_dict:
                self.configure_plugin(f_key, a_dict[f_key])
            else:
                self.configure_plugin(f_key, f_empty_eng_val)

    def set_window_title(self, a_track_name):
        self.track_name = str(a_track_name)
        self.widget.setWindowTitle(
            "MusiKernel Way-V - {}".format(self.track_name))

    def set_fm_origin(self):
        self.fm_origin = []
        for f_knob in self.fm_knobs:
            self.fm_origin.append(f_knob.get_value())

    def return_to_origin(self):
        for f_value, f_knob in zip(self.fm_origin, self.fm_knobs):
            f_knob.set_value(f_value, True)
        self.reset_fm_macro_knobs()

    def reset_fm_macro_knobs(self):
        for f_knob in self.fm_macro_knobs:
            f_knob.set_value(0, True)

    def set_fm_macro1_end(self):
        self.set_fm_macro_end(0)

    def set_fm_macro2_end(self):
        self.set_fm_macro_end(1)

    def set_fm_macro_end(self, a_index):
        for f_spinbox, f_knob, f_origin in zip(
        self.fm_macro_spinboxes[a_index], self.fm_knobs, self.fm_origin):
            f_value = f_knob.get_value() - f_origin
            f_value = pydaw_util.pydaw_clip_value(f_value, -100, 100)
            f_spinbox.set_value(f_value, True)

    def clear_all(self):
        for f_control in (
        self.fm_knobs + self.fm_macro_spinboxes[0] +
        self.fm_macro_spinboxes[1]):
            f_control.set_value(0, True)

    def return_fm_macro1_end(self):
        self.return_fm_macro_end(0)

    def return_fm_macro2_end(self):
        self.return_fm_macro_end(1)

    def return_fm_macro_end(self, a_index):
        for f_spinbox, f_knob, f_origin in zip(
        self.fm_macro_spinboxes[a_index], self.fm_knobs, self.fm_origin):
            f_value = f_spinbox.get_value() + f_origin
            f_value = pydaw_util.pydaw_clip_value(f_value, 0, 100)
            f_knob.set_value(f_value, True)
        self.reset_fm_macro_knobs()

