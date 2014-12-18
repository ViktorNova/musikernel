#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This file is part of the MusiKernel project, Copyright MusiKernel Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

import os

from PyQt4 import QtGui, QtCore
from libpydaw import *
from mkplugins import *

from libpydaw.pydaw_util import *
from libpydaw.pydaw_widgets import *
from libpydaw.translate import _
import libpydaw.strings
import libmk


def set_tooltips_enabled(a_enabled):
    """ Set extensive tooltips as an alternative to
        maintaining a separate user manual
    """
    libmk.TOOLTIPS_ENABLED = a_enabled

    f_list = [WAVE_EDITOR, TRANSPORT,]
    for f_widget in f_list:
        f_widget.set_tooltips(a_enabled)

    pydaw_util.set_file_setting("tooltips", int(a_enabled))


def pydaw_scale_to_rect(a_to_scale, a_scale_to):
    """ Returns a tuple that scales one QRectF to another """
    f_x = (a_scale_to.width() / a_to_scale.width())
    f_y = (a_scale_to.height() / a_to_scale.height())
    return (f_x, f_y)


class WaveNextOsc(libmk.AbstractIPC):
    def __init__(self, a_with_audio=False,
             a_configure_path="/musikernel/wavenext"):
        libmk.AbstractIPC.__init__(self, a_with_audio, a_configure_path)

    def pydaw_wn_playback(self, a_mode):
        self.send_configure("wnp", str(a_mode))

    def pydaw_set_plugin(
    self, a_track_num, a_index, a_plugin_index, a_uid, a_on):
        self.send_configure(
            "pi", "|".join(str(x) for x in
            (a_track_num, a_index, a_plugin_index,
             a_uid, bool_to_int(a_on))))

    def pydaw_save_tracks(self):
        self.send_configure("st", "")

    def pydaw_we_export(self, a_file_name):
        self.send_configure("wex", "{}".format(a_file_name))

    def pydaw_ab_open(self, a_file):
        self.send_configure("abo", str(a_file))

    def pydaw_we_set(self, a_val):
        self.send_configure("we", str(a_val))

    def pydaw_panic(self):
        self.send_configure("panic", "")

    def save_audio_inputs(self):
        self.send_configure("ai", "")


wavenext_folder_tracks = "projects/wavenext/tracks"
pydaw_file_wave_editor_bookmarks = "projects/edmnext/wave_editor_bookmarks.txt"
pydaw_file_notes = "projects/wavenext/notes.txt"
pydaw_file_pyinput = "projects/wavenext/input.txt"


class WaveNextProject(libmk.AbstractProject):
    def __init__(self, a_with_audio):
        self.wn_osc = WaveNextOsc(a_with_audio)
        self.suppress_updates = False

    def save_track_plugins(self, a_uid, a_track):
        f_folder = wavenext_folder_tracks
        if not self.suppress_updates:
            self.save_file(f_folder, str(a_uid), str(a_track))

    def set_project_folders(self, a_project_file):
        #folders
        self.project_folder = os.path.dirname(a_project_file)
        self.project_file = os.path.splitext(
            os.path.basename(a_project_file))[0]
        self.wn_track_pool_folder = "{}/{}".format(
            self.project_folder, wavenext_folder_tracks)
        #files
        self.pynotes_file = "{}/{}".format(
            self.project_folder, pydaw_file_notes)
        self.pywebm_file = "{}/{}".format(
            self.project_folder, pydaw_file_wave_editor_bookmarks)
        self.audio_inputs_file = os.path.join(
            self.project_folder, pydaw_file_pyinput)

        self.project_folders = [
            self.project_folder, self.wn_track_pool_folder,]

    def open_project(self, a_project_file, a_notify_osc=True):
        self.set_project_folders(a_project_file)
        if not os.path.exists(a_project_file):
            print("project file {} does not exist, creating as "
                "new project".format(a_project_file))
            self.new_project(a_project_file)

#        if a_notify_osc:
#            self.wn_osc.pydaw_open_song(self.project_folder)

    def new_project(self, a_project_file, a_notify_osc=True):
        self.set_project_folders(a_project_file)

        for project_dir in self.project_folders:
            print(project_dir)
            if not os.path.isdir(project_dir):
                os.makedirs(project_dir)

#        self.commit("Created project")
#        if a_notify_osc:
#            self.wn_osc.pydaw_open_song(self.project_folder)

    def get_notes(self):
        if os.path.isfile(self.pynotes_file):
            return pydaw_read_file_text(self.pynotes_file)
        else:
            return ""

    def write_notes(self, a_text):
        pydaw_write_file_text(self.pynotes_file, a_text)

    def set_we_bm(self, a_file_list):
        f_list = [x for x in sorted(a_file_list) if len(x) < 1000]
        pydaw_write_file_text(self.pywebm_file, "\n".join(f_list))

    def get_we_bm(self):
        if os.path.exists(self.pywebm_file):
            f_list = pydaw_read_file_text(self.pywebm_file).split("\n")
            return [x for x in f_list if x]
        else:
            return []

    def get_track_plugins(self,  a_track_num):
        f_folder = self.wn_track_pool_folder
        f_path = "{}/{}".format(f_folder, a_track_num)
        if os.path.isfile(f_path):
            with open(f_path) as f_handle:
                f_str = f_handle.read()
            return libmk.pydaw_track_plugins.from_str(f_str)
        else:
            return None

    def save_audio_inputs(self, a_tracks):
        if not self.suppress_updates:
            self.save_file("", pydaw_file_pyinput, str(a_tracks))
            self.wn_osc.save_audio_inputs()

    def get_audio_inputs(self):
        if os.path.isfile(self.audio_inputs_file):
            with open(self.audio_inputs_file) as f_file:
                f_str = f_file.read()
            return libmk.mk_project.AudioInputTracks.from_str(f_str)
        else:
            return libmk.mk_project.AudioInputTracks()


def normalize_dialog():
    def on_ok():
        f_window.f_result = f_db_spinbox.value()
        f_window.close()

    def on_cancel():
        f_window.close()

    f_window = QtGui.QDialog(MAIN_WINDOW)
    f_window.f_result = None
    f_window.setWindowTitle(_("Normalize"))
    f_window.setFixedSize(150, 90)
    f_layout = QtGui.QVBoxLayout()
    f_window.setLayout(f_layout)
    f_hlayout = QtGui.QHBoxLayout()
    f_layout.addLayout(f_hlayout)
    f_hlayout.addWidget(QtGui.QLabel("dB"))
    f_db_spinbox = QtGui.QDoubleSpinBox()
    f_hlayout.addWidget(f_db_spinbox)
    f_db_spinbox.setRange(-18.0, 0.0)
    f_db_spinbox.setDecimals(1)
    f_db_spinbox.setValue(0.0)
    f_ok_button = QtGui.QPushButton(_("OK"))
    f_ok_cancel_layout = QtGui.QHBoxLayout()
    f_layout.addLayout(f_ok_cancel_layout)
    f_ok_cancel_layout.addWidget(f_ok_button)
    f_ok_button.pressed.connect(on_ok)
    f_cancel_button = QtGui.QPushButton(_("Cancel"))
    f_ok_cancel_layout.addWidget(f_cancel_button)
    f_cancel_button.pressed.connect(on_cancel)
    f_window.exec_()
    return f_window.f_result

class AudioInput:
    def __init__(self, a_num, a_layout, a_callback):
        self.input_num = int(a_num)
        self.callback = a_callback
        self.checkbox = QtGui.QCheckBox(str(a_num))
        self.checkbox.clicked.connect(self.update_engine)
        a_layout.addWidget(self.checkbox, a_num, 0)
        self.vol_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.vol_slider.setRange(-240, 240)
        self.vol_slider.setValue(0)
        self.vol_slider.setMinimumWidth(240)
        self.vol_slider.valueChanged.connect(self.vol_changed)
        self.vol_slider.sliderReleased.connect(self.update_engine)
        a_layout.addWidget(self.vol_slider, a_num, 9)
        self.vol_label = QtGui.QLabel("0.0dB")
        self.vol_label.setMinimumWidth(64)
        a_layout.addWidget(self.vol_label, a_num, 10)
        self.suppress_updates = False

    def update_engine(self, a_val=None):
        if not self.suppress_updates:
            self.callback()

    def vol_changed(self):
        f_vol = self.get_vol()
        self.vol_label.setText("{}dB".format(f_vol))
        if not self.suppress_updates:
            libmk.IPC.audio_input_volume(self.input_num, f_vol)

    def get_vol(self):
        return round(self.vol_slider.value() * 0.1, 1)

    def get_value(self):
        f_on = 1 if self.checkbox.isChecked() else 0
        f_vol = self.get_vol()
        return libmk.mk_project.AudioInputTrack(f_on, f_vol, 0)

    def set_value(self, a_val):
        self.suppress_updates = True
        f_rec = True if a_val.rec else False
        self.checkbox.setChecked(f_rec)
        self.vol_slider.setValue(int(a_val.vol * 10.0))
        self.suppress_updates = False


class AudioInputWidget:
    def __init__(self):
        self.widget = QtGui.QWidget()
        self.main_layout = QtGui.QVBoxLayout(self.widget)
        self.layout = QtGui.QGridLayout()
        self.main_layout.addWidget(QtGui.QLabel(_("Audio Inputs")))
        self.main_layout.addLayout(self.layout)
        self.inputs = []
        f_count = 0
        if "audioInputs" in pydaw_util.global_device_val_dict:
            f_count = int(pydaw_util.global_device_val_dict["audioInputs"])
        for f_i in range(f_count):
            f_input = AudioInput(f_i, self.layout, self.callback)
            self.inputs.append(f_input)

    def callback(self):
        f_result = libmk.mk_project.AudioInputTracks()
        for f_i, f_input in zip(range(len(self.inputs)), self.inputs):
            f_result.add_track(f_i, f_input.get_value())
        PROJECT.save_audio_inputs(f_result)

    def active(self):
        return [x.get_value() for x in self.inputs
            if x.checkbox.isChecked()]

    def open_project(self):
        f_audio_inputs = PROJECT.get_audio_inputs()
        for k, v in f_audio_inputs.tracks.items():
            if k < len(self.inputs):
                self.inputs[k].set_value(v)


class transport_widget(libmk.AbstractTransport):
    def __init__(self):
        self.suppress_osc = True
        self.start_region = 0
        self.last_bar = 0
        self.last_open_dir = global_home
        self.group_box = QtGui.QGroupBox()
        self.group_box.setObjectName("transport_panel")
        self.vlayout = QtGui.QVBoxLayout(self.group_box)
        self.hlayout1 = QtGui.QHBoxLayout()
        self.vlayout.addLayout(self.hlayout1)

        self.playback_menu_button = QtGui.QPushButton("")
        self.playback_menu_button.setMaximumWidth(21)
        self.playback_menu_button.setSizePolicy(
            QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.hlayout1.addWidget(self.playback_menu_button)

        self.playback_menu = QtGui.QMenu(self.playback_menu_button)
        self.playback_menu_button.setMenu(self.playback_menu)
        self.playback_widget_action = QtGui.QWidgetAction(self.playback_menu)
        self.playback_widget = QtGui.QWidget()
        self.playback_widget_action.setDefaultWidget(self.playback_widget)
        self.playback_vlayout = QtGui.QVBoxLayout(self.playback_widget)
        self.playback_menu.addAction(self.playback_widget_action)

        self.audio_inputs = AudioInputWidget()
        self.playback_vlayout.addWidget(self.audio_inputs.widget)

        self.hlayout1.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))

        self.suppress_osc = False

    def open_project(self):
        self.audio_inputs.open_project()

    def on_panic(self):
        pass
        #PROJECT.wn_osc.pydaw_panic()

    def set_time(self, f_text):
        #f_text = "{}:{}.{}".format(f_minutes, str(f_seconds).zfill(2), f_frac)
        libmk.TRANSPORT.set_time(f_text)

    def on_play(self):
        if not WAVE_EDITOR.current_file:
            return False
        WAVE_EDITOR.on_play()
        PROJECT.wn_osc.pydaw_wn_playback(1)
        return True

    def on_stop(self):
        PROJECT.wn_osc.pydaw_wn_playback(0)
        WAVE_EDITOR.on_stop()
        if libmk.IS_RECORDING:
            self.show_rec_dialog()

    def on_rec(self):
        if not self.audio_inputs.active():
            QtGui.QMessageBox.warning(
                self.group_box, _("Error"),
                _("No audio inputs are active, cannot record.  "
                "Enable one or more inputs in the transport drop-down."))
            return False
        PROJECT.wn_osc.pydaw_wn_playback(2)
        return True

    def show_rec_dialog(self):
        def on_ok():
            f_txt = str(f_name_lineedit.text()).strip()
            if not f_txt:
                QtGui.QMessageBox.warning(
                    MAIN_WINDOW, _("Error"), _("Name cannot be empty"))
                return
            for x in ("\\", "/", "~", "|"):
                if x in f_txt:
                    QtGui.QMessageBox.warning(
                        MAIN_WINDOW, _("Error"),
                        _("Invalid char '{}'".format(x)))
                    return
            if not f_txt.endswith(".wav"):
                f_txt += ".wav"
            for f_i, f_ai in zip(
            range(len(self.audio_inputs.inputs)), self.audio_inputs.inputs):
                f_val = f_ai.get_value()
                if f_val.rec:
                    f_path = os.path.join(
                        libmk.PROJECT.audio_tmp_folder, str(f_i), ".wav")
                    if os.path.isfile(f_path):
                        f_new_path = os.path.join(
                            libmk.PROJECT.user_folder, str(f_i), "-", f_txt)
                        shutil.move(f_path, f_new_path)
                    else:
                        print("Error, path did not exist: {}".format(f_path))
            f_window.close()

        def on_cancel():
            f_window.close()

        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Save Recorded Audio"))
        f_window.setFixedSize(420, 90)
        f_layout = QtGui.QVBoxLayout()
        f_window.setLayout(f_layout)
        f_hlayout = QtGui.QHBoxLayout()
        f_layout.addLayout(f_hlayout)
        f_hlayout.addWidget(QtGui.QLabel("Name"))
        f_name_lineedit = QtGui.QLineEdit()
        f_hlayout.addWidget(f_name_lineedit)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_ok_cancel_layout = QtGui.QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout)
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_ok_button.pressed.connect(on_ok)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_cancel_button.pressed.connect(on_cancel)
        f_window.exec_()

    def set_tooltips(self, a_enabled):
        pass


# TODO:  Remove some of the junk from here
class pydaw_audio_item:
    def __init__(
            self, a_uid, a_sample_start=0.0, a_sample_end=1000.0,
            a_start_bar=0, a_start_beat=0.0, a_timestretch_mode=3,
            a_pitch_shift=0.0, a_output_track=0, a_vol=0.0,
            a_timestretch_amt=1.0, a_fade_in=0.0, a_fade_out=999.0,
            a_lane_num=0, a_pitch_shift_end=0.0,
            a_timestretch_amt_end=1.0, a_reversed=False, a_crispness=5,
            a_fadein_vol=-18, a_fadeout_vol=-18, a_paif_automation_uid=0,
            a_send1=-1, a_s1_vol=0.0, a_send2=-1, a_s2_vol=0.0,
            a_s0_sc=False, a_s1_sc=False, a_s2_sc=False):
        self.uid = int(a_uid)
        self.sample_start = float(a_sample_start)
        self.sample_end = float(a_sample_end)
        self.start_bar = int(a_start_bar)
        self.start_beat = float(a_start_beat)
        self.time_stretch_mode = int(a_timestretch_mode)
        self.pitch_shift = float(a_pitch_shift)
        self.output_track = int(a_output_track)
        self.vol = round(float(a_vol), 1)
        self.timestretch_amt = float(a_timestretch_amt)
        self.fade_in = float(a_fade_in)
        self.fade_out = float(a_fade_out)
        self.lane_num = int(a_lane_num)
        self.pitch_shift_end = float(a_pitch_shift_end)
        self.timestretch_amt_end = float(a_timestretch_amt_end)
        if isinstance(a_reversed, bool):
            self.reversed = a_reversed
        else:
            self.reversed = int_to_bool(a_reversed)
        self.crispness = int(a_crispness) #This is specific to Rubberband
        self.fadein_vol = int(a_fadein_vol)
        self.fadeout_vol = int(a_fadeout_vol)
        self.paif_automation_uid = int(a_paif_automation_uid)
        self.send1 = int(a_send1)
        self.s1_vol = round(float(a_s1_vol), 1)
        self.send2 = int(a_send2)
        self.s2_vol = round(float(a_s2_vol), 1)
        self.s0_sc = int_to_bool(a_s0_sc)
        self.s1_sc = int_to_bool(a_s1_sc)
        self.s2_sc = int_to_bool(a_s2_sc)

    def set_pos(self, a_bar, a_beat):
        self.start_bar = int(a_bar)
        self.start_beat = float(a_beat)

    def set_fade_in(self, a_value):
        f_value = pydaw_clip_value(a_value, 0.0, self.fade_out - 1.0)
        self.fade_in = f_value

    def set_fade_out(self, a_value):
        f_value = pydaw_clip_value(a_value, self.fade_in + 1.0, 999.0)
        self.fade_out = f_value

    def clip_at_region_end(self, a_region_length, a_tempo,
            a_sample_length_seconds, a_truncate=True):
        f_region_length_beats = a_region_length * 4
        f_seconds_per_beat = (60.0 / a_tempo)
        f_region_length_seconds = f_seconds_per_beat * f_region_length_beats
        f_item_start_beats = (self.start_bar * 4.0) + self.start_beat
        f_item_start_seconds = f_item_start_beats * f_seconds_per_beat
        f_sample_start_seconds = (
            self.sample_start * 0.001 * a_sample_length_seconds)
        f_sample_end_seconds = (
            self.sample_end * 0.001 * a_sample_length_seconds)
        f_actual_sample_length = f_sample_end_seconds - f_sample_start_seconds
        f_actual_item_end = f_item_start_seconds + f_actual_sample_length

        if a_truncate and f_actual_item_end > f_region_length_seconds:
            f_new_item_end_seconds = (f_region_length_seconds -
                f_item_start_seconds) + f_sample_start_seconds
            f_new_item_end = (
                f_new_item_end_seconds / a_sample_length_seconds) * 1000.0
            print("clip_at_region_end:  new end: {}".format(f_new_item_end))
            self.sample_end = f_new_item_end
            return True
        elif not a_truncate:
            f_new_start_seconds = \
                f_region_length_seconds - f_actual_sample_length
            f_beats_total = f_new_start_seconds / f_seconds_per_beat
            self.start_bar = int(f_beats_total) // 4
            self.start_beat = f_beats_total % 4.0
            return True
        else:
            return False

    def __eq__(self, other):
        return str(self) == str(other)

    def clone(self):
        return pydaw_audio_item.from_arr(str(self).strip("\n").split("|"))

    def __str__(self):
        return "{}\n".format("|".join(proj_file_str(x) for x in
            (self.uid, self.sample_start, self.sample_end,
            self.start_bar, self.start_beat,
            self.time_stretch_mode, self.pitch_shift, self.output_track,
            self.vol, self.timestretch_amt,
            self.fade_in, self.fade_out, self.lane_num, self.pitch_shift_end,
            self.timestretch_amt_end, bool_to_int(self.reversed),
            int(self.crispness), int(self.fadein_vol), int(self.fadeout_vol),
            int(self.paif_automation_uid),
            self.send1, self.s1_vol, self.send2, self.s2_vol,
            bool_to_int(self.s0_sc), bool_to_int(self.s1_sc),
            bool_to_int(self.s2_sc))))

    @staticmethod
    def from_str(f_str):
        return pydaw_audio_item.from_arr(f_str.split("|"))

    @staticmethod
    def from_arr(a_arr):
        f_result = pydaw_audio_item(*a_arr)
        return f_result



class pydaw_main_window(QtGui.QScrollArea):
    def __init__(self):
        QtGui.QScrollArea.__init__(self)
        self.first_offline_render = True
        self.last_offline_dir = global_home
        self.copy_to_clipboard_checked = True

        self.setObjectName("plugin_ui")
        self.widget = QtGui.QWidget()
        self.widget.setObjectName("plugin_ui")
        self.setWidget(self.widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.main_layout = QtGui.QVBoxLayout()
        self.main_layout.setMargin(2)
        self.widget.setLayout(self.main_layout)

        #The tabs
        self.main_tabwidget = QtGui.QTabWidget()
        self.main_layout.addWidget(self.main_tabwidget)

        self.main_tabwidget.addTab(WAVE_EDITOR.widget, _("Wave Editor"))

        self.notes_tab = QtGui.QTextEdit(self)
        self.notes_tab.setAcceptRichText(False)
        self.notes_tab.leaveEvent = self.on_edit_notes
        self.main_tabwidget.addTab(self.notes_tab, _("Project Notes"))

    def on_edit_notes(self, a_event=None):
        QtGui.QTextEdit.leaveEvent(self.notes_tab, a_event)
        PROJECT.write_notes(self.notes_tab.toPlainText())

    def configure_callback(self, path, arr):
        f_pc_dict = {}
        f_ui_dict = {}
        f_cc_dict = {}
        for f_line in arr[0].split("\n"):
            if f_line == "":
                break
            a_key, a_val = f_line.split("|", 1)
            if a_key == "pc":
                f_plugin_uid, f_port, f_val = a_val.split("|")
                f_pc_dict[(f_plugin_uid, f_port)] = f_val
            elif a_key == "cur":
                if libmk.IS_PLAYING:
                    f_region, f_bar, f_beat = a_val.split("|")
                    TRANSPORT.set_pos_from_cursor(f_region, f_bar, f_beat)
                    for f_editor in (AUDIO_SEQ, REGION_EDITOR):
                        f_editor.set_playback_pos(f_bar, f_beat)
            elif a_key == "peak":
                global_update_peak_meters(a_val)
            elif a_key == "cc":
                f_track_num, f_cc, f_val = a_val.split("|")
                f_cc_dict[(f_track_num, f_cc)] = f_val
            elif a_key == "ui":
                f_plugin_uid, f_name, f_val = a_val.split("|", 2)
                f_ui_dict[(f_plugin_uid, f_name)] = f_val
            elif a_key == "mrec":
                MREC_EVENTS.append(a_val)
            elif a_key == "ne":
                f_state, f_note = a_val.split("|")
                PIANO_ROLL_EDITOR.highlight_keys(f_state, f_note)
            elif a_key == "ml":
                libmk.PLUGIN_UI_DICT.midi_learn_control[0].update_cc_map(
                    a_val, libmk.PLUGIN_UI_DICT.midi_learn_control[1])
            elif a_key == "wec":
                if libmk.IS_PLAYING:
                    WAVE_EDITOR.set_playback_cursor(float(a_val))
            elif a_key == "ready":
                pass
        #This prevents multiple events from moving the same control,
        #only the last goes through
        for k, f_val in f_ui_dict.items():
            f_plugin_uid, f_name = k
            if int(f_plugin_uid) in libmk.PLUGIN_UI_DICT:
                libmk.PLUGIN_UI_DICT[int(f_plugin_uid)].ui_message(
                    f_name, f_val)
        for k, f_val in f_pc_dict.items():
            f_plugin_uid, f_port = (int(x) for x in k)
            if f_plugin_uid in libmk.PLUGIN_UI_DICT:
                libmk.PLUGIN_UI_DICT[f_plugin_uid].set_control_val(
                    f_port, float(f_val))
        for k, f_val in f_cc_dict.items():
            f_track_num, f_cc = (int(x) for x in k)
            for f_plugin_uid in \
            TRACK_PANEL.tracks[f_track_num].get_plugin_uids():
                if f_plugin_uid in libmk.PLUGIN_UI_DICT:
                    libmk.PLUGIN_UI_DICT[f_plugin_uid].set_cc_val(f_cc, f_val)

    def prepare_to_quit(self):
        pass

def global_update_peak_meters(a_val):
    for f_val in a_val.split("|"):
        f_list = f_val.split(":")
        f_index = int(f_list[0])
        if f_index in ALL_PEAK_METERS:
            for f_pkm in ALL_PEAK_METERS[f_index]:
                f_pkm.set_value(f_list[1:])
        else:
            print("{} not in ALL_PEAK_METERS".format(f_index))


class pydaw_wave_editor_widget:
    def __init__(self):
        self.widget = QtGui.QWidget()
        self.layout = QtGui.QVBoxLayout(self.widget)
        self.right_widget = QtGui.QWidget()
        self.vlayout = QtGui.QVBoxLayout(self.right_widget)
        self.file_browser = pydaw_widgets.pydaw_file_browser_widget()
        self.file_browser.load_button.pressed.connect(self.on_file_open)
        self.file_browser.list_file.itemDoubleClicked.connect(
            self.on_file_open)
        self.file_browser.preview_button.pressed.connect(self.on_preview)
        self.file_browser.stop_preview_button.pressed.connect(
            self.on_stop_preview)
        self.file_browser.list_file.setSelectionMode(
            QtGui.QListWidget.SingleSelection)
        self.layout.addWidget(self.file_browser.hsplitter)
        self.file_browser.hsplitter.addWidget(self.right_widget)
        self.file_hlayout = QtGui.QHBoxLayout()

        self.menu = QtGui.QMenu(self.widget)
        self.menu_button = QtGui.QPushButton(_("Menu"))
        self.menu_button.setMenu(self.menu)
        self.file_hlayout.addWidget(self.menu_button)
        self.export_action = self.menu.addAction(_("Export..."))
        self.export_action.triggered.connect(self.on_export)
        self.menu.addSeparator()
        self.copy_action = self.menu.addAction(_("Copy File to Clipboard"))
        self.copy_action.triggered.connect(self.copy_file_to_clipboard)
        self.copy_action.setShortcut(QtGui.QKeySequence.Copy)
#        self.copy_item_action = self.menu.addAction(_("Copy as Audio Item"))
#        self.copy_item_action.triggered.connect(self.copy_audio_item)
#        self.copy_item_action.setShortcut(
#            QtGui.QKeySequence.fromString("ALT+C"))
        self.paste_action = self.menu.addAction(
            _("Paste File from Clipboard"))
        self.paste_action.triggered.connect(self.open_file_from_clipboard)
        self.paste_action.setShortcut(QtGui.QKeySequence.Paste)
        self.open_folder_action = self.menu.addAction(
            _("Open parent folder in browser"))
        self.open_folder_action.triggered.connect(self.open_item_folder)
        self.menu.addSeparator()
        self.bookmark_action = self.menu.addAction(_("Bookmark File"))
        self.bookmark_action.triggered.connect(self.bookmark_file)
        self.bookmark_action.setShortcut(
            QtGui.QKeySequence.fromString("CTRL+D"))
        self.delete_bookmark_action = self.menu.addAction(
            _("Delete Bookmark"))
        self.delete_bookmark_action.triggered.connect(self.delete_bookmark)
        self.delete_bookmark_action.setShortcut(
            QtGui.QKeySequence.fromString("ALT+D"))
        self.menu.addSeparator()
        self.reset_markers_action = self.menu.addAction(
            _("Reset Markers"))
        self.reset_markers_action.triggered.connect(self.reset_markers)
        self.normalize_action = self.menu.addAction(
            _("Normalize (non-destructive)..."))
        self.normalize_action.triggered.connect(self.normalize_dialog)
        self.stretch_shift_action = self.menu.addAction(
            _("Time-Stretch/Pitch-Shift..."))
        self.stretch_shift_action.triggered.connect(self.stretch_shift_dialog)

        self.bookmark_button = QtGui.QPushButton(_("Bookmarks"))
        self.file_hlayout.addWidget(self.bookmark_button)

        self.history_button = QtGui.QPushButton(_("History"))
        self.file_hlayout.addWidget(self.history_button)

        self.fx_button = QtGui.QPushButton(_("Effects"))
        self.file_hlayout.addWidget(self.fx_button)

        ###############################

        self.fx_menu = QtGui.QMenu()
        self.fx_menu.aboutToShow.connect(self.open_plugins)
        self.fx_button.setMenu(self.fx_menu)
        self.track_number = 0
        self.plugins = []
        self.menu_widget = QtGui.QWidget()
        self.menu_hlayout = QtGui.QHBoxLayout(self.menu_widget)
        self.menu_gridlayout = QtGui.QGridLayout()
        self.menu_hlayout.addLayout(self.menu_gridlayout)
        self.menu_gridlayout.addWidget(QtGui.QLabel(_("Plugins")), 0, 0)
        self.menu_gridlayout.addWidget(QtGui.QLabel(_("P")), 0, 3)
        for f_i in range(10):
            f_plugin = plugin_settings_wave_editor(
                PROJECT.wn_osc.pydaw_set_plugin,
                f_i, self.track_number, self.menu_gridlayout,
                self.save_callback, self.name_callback, None)
            self.plugins.append(f_plugin)
        self.action_widget = QtGui.QWidgetAction(self.fx_menu)
        self.action_widget.setDefaultWidget(self.menu_widget)
        self.fx_menu.addAction(self.action_widget)

        ###############################

        self.menu_info = QtGui.QMenu()
        self.menu_info_button = QtGui.QPushButton(_("Info"))
        self.menu_info_button.setMenu(self.menu_info)
        self.file_hlayout.addWidget(self.menu_info_button)

        self.file_lineedit = QtGui.QLineEdit()
        self.file_lineedit.setReadOnly(True)
        self.file_hlayout.addWidget(self.file_lineedit)
        self.vlayout.addLayout(self.file_hlayout)
        self.edit_tab = QtGui.QWidget()
        self.file_browser.folders_tab_widget.addTab(self.edit_tab, _("Edit"))
        self.edit_hlayout = QtGui.QHBoxLayout(self.edit_tab)
        self.vol_layout = QtGui.QVBoxLayout()
        self.edit_hlayout.addLayout(self.vol_layout)
        self.vol_slider = QtGui.QSlider(QtCore.Qt.Vertical)
        self.vol_slider.setRange(-240, 120)
        self.vol_slider.setValue(0)
        self.vol_slider.valueChanged.connect(self.vol_changed)
        self.vol_layout.addWidget(self.vol_slider)
        self.vol_label = QtGui.QLabel("0.0db")
        self.vol_label.setMinimumWidth(75)
        self.vol_layout.addWidget(self.vol_label)
        self.peak_meter = pydaw_widgets.peak_meter(28, a_text=True)
        ALL_PEAK_METERS[0] = [self.peak_meter]
        self.edit_hlayout.addWidget(self.peak_meter.widget)
        self.ctrl_vlayout = QtGui.QVBoxLayout()
        self.edit_hlayout.addLayout(self.ctrl_vlayout)
        self.fade_in_start = QtGui.QSpinBox()
        self.fade_in_start.setRange(-50, -6)
        self.fade_in_start.setValue(-24)
        self.fade_in_start.valueChanged.connect(self.marker_callback)
        self.ctrl_vlayout.addWidget(QtGui.QLabel(_("Fade-In")))
        self.ctrl_vlayout.addWidget(self.fade_in_start)
        self.fade_out_end = QtGui.QSpinBox()
        self.fade_out_end.setRange(-50, -6)
        self.fade_out_end.setValue(-24)
        self.fade_out_end.valueChanged.connect(self.marker_callback)
        self.ctrl_vlayout.addWidget(QtGui.QLabel(_("Fade-Out")))
        self.ctrl_vlayout.addWidget(self.fade_out_end)
        self.ctrl_vlayout.addItem(
            QtGui.QSpacerItem(1, 1, vPolicy=QtGui.QSizePolicy.Expanding))
        self.edit_hlayout.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))
        self.sample_graph = pydaw_audio_item_viewer_widget(
            self.marker_callback, self.marker_callback,
            self.marker_callback, self.marker_callback)
        self.vlayout.addWidget(self.sample_graph)

        self.label_action = QtGui.QWidgetAction(self.menu_button)
        self.label_action.setDefaultWidget(self.sample_graph.label)
        self.menu_info.addAction(self.label_action)
        self.sample_graph.label.setFixedSize(210, 123)

        self.orig_pos = 0
        self.duration = None
        self.sixty_recip = 1.0 / 60.0
        self.playback_cursor = None
        self.time_label_enabled = False
        self.file_browser.hsplitter.setSizes([420, 9999])
        self.copy_to_clipboard_checked = True
        self.last_offline_dir = global_home
        self.open_exported = False
        self.history = []
        self.graph_object = None
        self.current_file = None
        self.callbacks_enabled = True

        self.controls_to_disable = (
            self.file_browser.load_button, self.file_browser.preview_button,
            self.file_browser.stop_preview_button, self.history_button,
            self.sample_graph, self.vol_slider, self.bookmark_button,
            self.fade_in_start, self.fade_out_end)

    def save_callback(self):
        f_result = libmk.pydaw_track_plugins()
        f_result.plugins = [x.get_value() for x in self.plugins]
        PROJECT.save_track_plugins(self.track_number, f_result)

    def open_plugins(self):
        f_plugins = PROJECT.get_track_plugins(self.track_number)
        if f_plugins:
            for f_plugin in f_plugins.plugins:
                self.plugins[f_plugin.index].set_value(f_plugin)

    def name_callback(self):
        return "Wave-Next"

    def copy_audio_item(self):
        pass
#        if self.graph_object is None:
#            return
#        f_uid = libmk.PROJECT.get_wav_uid_by_name(self.current_file)
#        f_item = self.get_audio_item(f_uid)
#        raise NotImplementedError

    def bookmark_file(self):
        if self.graph_object is None:
            return
        f_list = self.get_bookmark_list()
        if self.current_file not in f_list:
            f_list.append(self.current_file)
            PROJECT.set_we_bm(f_list)
            self.open_project()

    def get_bookmark_list(self):
        f_list = PROJECT.get_we_bm()
        f_resave = False
        for f_item in f_list[:]:
            if not os.path.isfile(f_item):
                f_resave = True
                f_list.remove(f_item)
                print("os.path.isfile({}) returned False, removing "
                    "from bookmarks".format(f_item))
        if f_resave:
            PROJECT.set_we_bm(f_list)
        return sorted(f_list)

    def open_project(self):
        f_list = self.get_bookmark_list()
        if f_list:
            f_menu = QtGui.QMenu(self.widget)
            f_menu.triggered.connect(self.open_file_from_action)
            self.bookmark_button.setMenu(f_menu)
            for f_item in f_list:
                f_menu.addAction(f_item)
        else:
            self.bookmark_button.setMenu(None)

    def delete_bookmark(self):
        if self.graph_object is None:
            return
        f_list = PROJECT.get_we_bm()
        if self.current_file in f_list:
            f_list.remove(self.current_file)
            PROJECT.set_we_bm(f_list)
            self.open_project()

    def open_item_folder(self):
        f_path = str(self.file_lineedit.text())
        self.file_browser.open_file_in_browser(f_path)

    def normalize_dialog(self):
        if self.graph_object is None or libmk.IS_PLAYING:
            return
        f_val = normalize_dialog()
        if f_val is not None:
            self.normalize(f_val)

    def normalize(self, a_value):
        f_val = self.graph_object.normalize(a_value)
        self.vol_slider.setValue(int(f_val * 10.0))

    def reset_markers(self):
        if libmk.IS_PLAYING:
            return
        self.sample_graph.reset_markers()

    def set_tooltips(self, a_on):
        if a_on:
            self.sample_graph.setToolTip(
                _("Load samples here by using the browser on the left "
                "and clicking the  'Load' button"))
            self.fx_button.setToolTip(
                _("This button shows the Modulex effects window.  "
                "Export the audio (using the menu button) to "
                "permanently apply effects."))
            self.menu_button.setToolTip(
                _("This menu can export the audio or perform "
                "various operations."))
            self.history_button.setToolTip(
                _("Use this button to view or open files that "
                "were previously opened during this session."))
        else:
            self.sample_graph.setToolTip("")
            self.fx_button.setToolTip("")
            self.menu_button.setToolTip("")
            self.history_button.setToolTip("")

    def stretch_shift_dialog(self):
        f_path = self.current_file
        if f_path is None or libmk.IS_PLAYING:
            return

        f_base_file_name = f_path.rsplit("/", 1)[1]
        f_base_file_name = f_base_file_name.rsplit(".", 1)[0]
        print(f_base_file_name)

        def on_ok(a_val=None):
            f_stretch = f_timestretch_amt.value()
            f_crispness = f_crispness_combobox.currentIndex()
            f_preserve_formants = f_preserve_formants_checkbox.isChecked()
            f_algo = f_algo_combobox.currentIndex()
            f_pitch = f_pitch_shift.value()

            f_file = QtGui.QFileDialog.getSaveFileName(
                self.widget, "Save file as...", self.last_offline_dir,
                filter="Wav File (*.wav)")
            if f_file is None:
                return
            f_file = str(f_file)
            if f_file == "":
                return
            if not f_file.endswith(".wav"):
                f_file += ".wav"
            self.last_offline_dir = os.path.dirname(f_file)

            if f_algo == 0:
                f_proc = pydaw_util.pydaw_rubberband(
                    f_path, f_file, f_stretch, f_pitch, f_crispness,
                    f_preserve_formants)
            elif f_algo == 1:
                f_proc = pydaw_util.pydaw_sbsms(
                    f_path, f_file, f_stretch, f_pitch)

            f_proc.wait()
            self.open_file(f_file)
            f_window.close()

        def on_cancel(a_val=None):
            f_window.close()

        f_window = QtGui.QDialog(self.widget)
        f_window.setMinimumWidth(390)
        f_window.setWindowTitle(_("Time-Stretch/Pitch-Shift Sample"))
        f_layout = QtGui.QVBoxLayout()
        f_window.setLayout(f_layout)

        f_time_gridlayout = QtGui.QGridLayout()
        f_layout.addLayout(f_time_gridlayout)

        f_time_gridlayout.addWidget(QtGui.QLabel(_("Pitch(semitones):")), 0, 0)
        f_pitch_shift = QtGui.QDoubleSpinBox()
        f_pitch_shift.setRange(-36, 36)
        f_pitch_shift.setValue(0.0)
        f_pitch_shift.setDecimals(6)
        f_time_gridlayout.addWidget(f_pitch_shift, 0, 1)

        f_time_gridlayout.addWidget(QtGui.QLabel(_("Stretch:")), 3, 0)
        f_timestretch_amt = QtGui.QDoubleSpinBox()
        f_timestretch_amt.setRange(0.2, 4.0)
        f_timestretch_amt.setDecimals(6)
        f_timestretch_amt.setSingleStep(0.1)
        f_timestretch_amt.setValue(1.0)
        f_time_gridlayout.addWidget(f_timestretch_amt, 3, 1)
        f_time_gridlayout.addWidget(QtGui.QLabel(_("Algorithm:")), 6, 0)
        f_algo_combobox = QtGui.QComboBox()
        f_algo_combobox.addItems(["Rubberband", "SBSMS"])
        f_time_gridlayout.addWidget(f_algo_combobox, 6, 1)

        f_groupbox = QtGui.QGroupBox(_("Rubberband Options"))
        f_layout.addWidget(f_groupbox)
        f_groupbox_layout = QtGui.QGridLayout(f_groupbox)
        f_groupbox_layout.addWidget(QtGui.QLabel(_("Crispness")), 12, 0)
        f_crispness_combobox = QtGui.QComboBox()
        f_crispness_combobox.addItems(CRISPNESS_SETTINGS)
        f_crispness_combobox.setCurrentIndex(5)
        f_groupbox_layout.addWidget(f_crispness_combobox, 12, 1)
        f_preserve_formants_checkbox = QtGui.QCheckBox("Preserve formants?")
        f_preserve_formants_checkbox.setChecked(True)
        f_groupbox_layout.addWidget(f_preserve_formants_checkbox, 18, 1)

        f_hlayout2 = QtGui.QHBoxLayout()
        f_layout.addLayout(f_hlayout2)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_ok_button.pressed.connect(on_ok)
        f_hlayout2.addWidget(f_ok_button)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(on_cancel)
        f_hlayout2.addWidget(f_cancel_button)

        f_window.exec_()

    def open_file_from_action(self, a_action):
        self.open_file(str(a_action.text()))

    def on_export(self):
        if not self.history or libmk.IS_PLAYING:
            return

        def ok_handler():
            if str(f_name.text()) == "":
                QtGui.QMessageBox.warning(
                    f_window, _("Error"), _("Name cannot be empty"))
                return

            if f_copy_to_clipboard_checkbox.isChecked():
                self.copy_to_clipboard_checked = True
                f_clipboard = QtGui.QApplication.clipboard()
                f_clipboard.setText(f_name.text())
            else:
                self.copy_to_clipboard_checked = False

            f_file_name = str(f_name.text())
            PROJECT.wn_osc.pydaw_we_export(f_file_name)
            self.last_offline_dir = os.path.dirname(f_file_name)
            self.open_exported = f_open_exported.isChecked()
            f_window.close()
            libmk.MAIN_WINDOW.show_offline_rendering_wait_window(f_file_name)
            if self.open_exported:
                self.open_file(f_file_name)


        def cancel_handler():
            f_window.close()

        def file_name_select():
            try:
                if not os.path.isdir(self.last_offline_dir):
                    self.last_offline_dir = global_home
                f_file_name = str(QtGui.QFileDialog.getSaveFileName(
                    f_window, _("Select a file name to save to..."),
                    self.last_offline_dir))
                if not f_file_name is None and f_file_name != "":
                    if not f_file_name.endswith(".wav"):
                        f_file_name += ".wav"
                    if not f_file_name is None and not str(f_file_name) == "":
                        f_name.setText(f_file_name)
                    self.last_offline_dir = os.path.dirname(f_file_name)
            except Exception as ex:
                libmk.pydaw_print_generic_exception(ex)

        def on_overwrite(a_val=None):
            f_name.setText(self.file_lineedit.text())

        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Offline Render"))
        f_layout = QtGui.QGridLayout()
        f_window.setLayout(f_layout)

        f_name = QtGui.QLineEdit()
        f_name.setReadOnly(True)
        f_name.setMinimumWidth(360)
        f_layout.addWidget(QtGui.QLabel(_("File Name:")), 0, 0)
        f_layout.addWidget(f_name, 0, 1)
        f_select_file = QtGui.QPushButton(_("Select"))
        f_select_file.pressed.connect(file_name_select)
        f_layout.addWidget(f_select_file, 0, 2)

        f_overwrite_button = QtGui.QPushButton("Overwrite\nFile")
        f_layout.addWidget(f_overwrite_button, 3, 0)
        f_overwrite_button.pressed.connect(on_overwrite)

        f_layout.addWidget(QtGui.QLabel(
            libpydaw.strings.export_format), 3, 1)
        f_copy_to_clipboard_checkbox = QtGui.QCheckBox(
        _("Copy export path to clipboard? (useful for right-click pasting "
        "back into the audio sequencer)"))
        f_copy_to_clipboard_checkbox.setChecked(self.copy_to_clipboard_checked)
        f_layout.addWidget(f_copy_to_clipboard_checkbox, 4, 1)
        f_open_exported = QtGui.QCheckBox("Open exported item?")
        f_open_exported.setChecked(self.open_exported)
        f_layout.addWidget(f_open_exported, 6, 1)
        f_ok_layout = QtGui.QHBoxLayout()
        f_ok_layout.addItem(
            QtGui.QSpacerItem(10, 10,
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))
        f_ok = QtGui.QPushButton(_("OK"))
        f_ok.pressed.connect(ok_handler)
        f_ok_layout.addWidget(f_ok)
        f_layout.addLayout(f_ok_layout, 9, 1)
        f_cancel = QtGui.QPushButton(_("Cancel"))
        f_cancel.pressed.connect(cancel_handler)
        f_layout.addWidget(f_cancel, 9, 2)
        f_window.exec_()


    def on_reload(self):
        pass

    def vol_changed(self, a_val=None):
        f_result = round(self.vol_slider.value()  * 0.1, 1)
        self.marker_callback()
        self.vol_label.setText("{}dB".format(f_result))

    def on_preview(self):
        f_list = self.file_browser.files_selected()
        if f_list:
            libmk.IPC.pydaw_preview_audio(f_list[0])

    def on_stop_preview(self):
        libmk.IPC.pydaw_stop_preview()

    def on_file_open(self):
        if libmk.IS_PLAYING:
            return
        f_file = self.file_browser.files_selected()
        if not f_file:
            return
        f_file_str = f_file[0]
        self.open_file(f_file_str)

    def copy_file_to_clipboard(self):
        f_clipboard = QtGui.QApplication.clipboard()
        f_clipboard.setText(str(self.file_lineedit.text()))

    def open_file_from_clipboard(self):
        if libmk.IS_PLAYING:
            return
        f_clipboard = QtGui.QApplication.clipboard()
        f_text = str(f_clipboard.text()).strip()
        if len(f_text) < 1000 and os.path.isfile(f_text):
            self.open_file(f_text)
        else:
            QtGui.QMessageBox.warning(
                self.widget, _("Error"),
                _("No file path in the clipboard"))

    def open_file(self, a_file):
        f_file = str(a_file)
        if not os.path.exists(f_file):
            QtGui.QMessageBox.warning(
                self.widget, _("Error"),
                _("{} does not exist".format(f_file)))
            return
        self.clear_sample_graph()
        self.current_file = f_file
        self.file_lineedit.setText(f_file)
        self.set_sample_graph(f_file)
        self.duration = float(self.graph_object.frame_count) / float(
            self.graph_object.sample_rate)
        if f_file in self.history:
            self.history.remove(f_file)
        self.history.append(f_file)
        f_menu = QtGui.QMenu(self.history_button)
        f_menu.triggered.connect(self.open_file_from_action)
        for f_path in reversed(self.history):
            f_menu.addAction(f_path)
        self.history_button.setMenu(f_menu)
        PROJECT.wn_osc.pydaw_ab_open(a_file)
        self.marker_callback()

    def get_audio_item(self, a_uid=0):
        f_start = self.sample_graph.start_marker.value
        f_end = self.sample_graph.end_marker.value
        f_diff = f_end - f_start
        f_diff = pydaw_clip_value(f_diff, 0.1, 1000.0)
        f_fade_in = ((self.sample_graph.fade_in_marker.value - f_start) /
            f_diff) * 1000.0
        f_fade_out = 1000.0 - (((f_end -
            self.sample_graph.fade_out_marker.value) / f_diff) * 1000.0)

        return pydaw_audio_item(
            a_uid, a_sample_start=f_start, a_sample_end=f_end,
            a_vol=self.vol_slider.value() * 0.1,
            a_fade_in=f_fade_in, a_fade_out=f_fade_out,
            a_fadein_vol=self.fade_in_start.value(),
            a_fadeout_vol=self.fade_out_end.value())

    def set_audio_item(self, a_item):
        self.callbacks_enabled = False
        self.sample_graph.start_marker.set_value(a_item.sample_start)
        self.sample_graph.end_marker.set_value(a_item.sample_end)
        f_start = self.sample_graph.start_marker.value
        f_end = self.sample_graph.end_marker.value
        f_diff = f_end - f_start
        f_diff = pydaw_clip_value(f_diff, 0.1, 1000.0)
        f_fade_in = (f_diff * (a_item.fade_in / 1000.0)) + f_start
        f_fade_out = (f_diff * (a_item.fade_out / 1000.0)) + f_start
        self.sample_graph.fade_in_marker.set_value(f_fade_in)
        self.sample_graph.fade_out_marker.set_value(f_fade_out)
        self.vol_slider.setValue(int(a_item.vol * 10.0))
        self.fade_in_start.setValue(a_item.fadein_vol)
        self.fade_out_end.setValue(a_item.fadeout_vol)
        self.callbacks_enabled = True
        self.marker_callback()

    def marker_callback(self, a_val=None):
        if self.callbacks_enabled:
            f_item = self.get_audio_item()
            PROJECT.wn_osc.pydaw_we_set(
                "0|{}".format(f_item))
            f_start = self.sample_graph.start_marker.value
            self.set_time_label(f_start * 0.001, True)

    def set_playback_cursor(self, a_pos):
        if self.playback_cursor is not None:
            self.playback_cursor.setPos(
                a_pos * pydaw_widgets.AUDIO_ITEM_SCENE_WIDTH, 0.0)
        self.set_time_label(a_pos)

    def set_time_label(self, a_value, a_override=False):
        if self.history and (a_override or self.time_label_enabled):
            f_seconds = self.duration * a_value
            f_minutes = int(f_seconds * self.sixty_recip)
            f_seconds %= 60.0
            f_tenths = round(f_seconds - float(int(f_seconds)), 1)
            f_seconds = str(int(f_seconds)).zfill(2)
            libmk.TRANSPORT.set_time("{}:{}.{}".format(
                f_minutes, f_seconds, str(f_tenths)[2]))

    def on_play(self):
        for f_control in self.controls_to_disable:
            f_control.setEnabled(False)
        self.time_label_enabled = True
        self.playback_cursor = self.sample_graph.scene.addLine(
            self.sample_graph.start_marker.line.line(),
            self.sample_graph.start_marker.line.pen())

    def on_stop(self):
        for f_control in self.controls_to_disable:
            f_control.setEnabled(True)
        if self.playback_cursor is not None:
            #self.sample_graph.scene.removeItem(self.playback_cursor)
            self.playback_cursor = None
        self.time_label_enabled = False
        if self.history:
            self.set_time_label(
                self.sample_graph.start_marker.value * 0.001, True)
        if self.graph_object is not None:
            self.sample_graph.redraw_item(
                self.sample_graph.start_marker.value,
                self.sample_graph.end_marker.value,
                self.sample_graph.fade_in_marker.value,
                self.sample_graph.fade_out_marker.value)

    def set_sample_graph(self, a_file_name):
        libmk.PROJECT.delete_sample_graph_by_name(a_file_name)
        self.graph_object = libmk.PROJECT.get_sample_graph_by_name(
            a_file_name, a_cp=False)
        self.sample_graph.draw_item(
            self.graph_object, 0.0, 1000.0, 0.0, 1000.0)

    def clear_sample_graph(self):
        self.sample_graph.clear_drawn_items()

    def clear(self):
        self.clear_sample_graph()
        self.file_lineedit.setText("")


def global_close_all():
    global OPEN_ITEM_UIDS, AUDIO_ITEMS_TO_DROP
    WAVE_EDITOR.clear()

#Opens or creates a new project
def global_open_project(a_project_file):
    global PROJECT, TRACK_NAMES
    PROJECT = WaveNextProject(global_pydaw_with_audio)
    PROJECT.suppress_updates = True
    PROJECT.open_project(a_project_file, False)
    WAVE_EDITOR.last_offline_dir = libmk.PROJECT.user_folder
    PROJECT.suppress_updates = False
    MAIN_WINDOW.last_offline_dir = libmk.PROJECT.user_folder
    MAIN_WINDOW.notes_tab.setText(PROJECT.get_notes())
    WAVE_EDITOR.open_project()
    TRANSPORT.open_project()


def global_new_project(a_project_file):
    global PROJECT
    PROJECT = WaveNextProject(global_pydaw_with_audio)
    PROJECT.new_project(a_project_file)
    WAVE_EDITOR.last_offline_dir = libmk.PROJECT.user_folder
    MAIN_WINDOW.last_offline_dir = libmk.PROJECT.user_folder
    MAIN_WINDOW.notes_tab.setText("")
    WAVE_EDITOR.open_project()


PROJECT = WaveNextProject(True)

ALL_PEAK_METERS = {}

TIMESTRETCH_MODES = [
    _("None"), _("Pitch(affecting time)"), _("Time(affecting pitch)"),
    "Rubberband", "Rubberband(formants)", "SBSMS", "Paulstretch"]

CRISPNESS_SETTINGS = [
    _("0 (smeared)"), _("1 (piano)"), "2", "3",
    "4", "5 (normal)", _("6 (sharp, drums)")]

WAVE_EDITOR = pydaw_wave_editor_widget()
TRANSPORT = transport_widget()
MAIN_WINDOW = pydaw_main_window()

if libmk.TOOLTIPS_ENABLED:
    set_tooltips_enabled(libmk.TOOLTIPS_ENABLED)

