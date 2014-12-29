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
import re
import traceback
import subprocess

import numpy
import scipy
import scipy.signal

import libmk

from libmk.mk_project import *

from libpydaw.pydaw_util import *
from libpydaw.translate import _
from libpydaw.pydaw_widgets import pydaw_modulex_settings

from libdawnext.osc import DawNextOsc

from PyQt4 import QtGui
from libpydaw import pydaw_history

TRACK_COUNT_ALL = 32
MAX_AUDIO_ITEM_COUNT = 256
MAX_REGION_LENGTH = 512 #measures

pydaw_folder_dawnext = os.path.join("projects", "dawnext")
pydaw_folder_items = os.path.join(pydaw_folder_dawnext, "items")
pydaw_folder_tracks = os.path.join(pydaw_folder_dawnext, "tracks")

FILE_SEQUENCER = os.path.join(pydaw_folder_dawnext, "sequencer.txt")
pydaw_file_regions_atm = os.path.join(pydaw_folder_dawnext, "automation.txt")
pydaw_file_routing_graph = os.path.join(pydaw_folder_dawnext, "routing.txt")
pydaw_file_midi_routing = os.path.join(
    pydaw_folder_dawnext, "midi_routing.txt")
pydaw_file_audio_per_item_fx = os.path.join(
    pydaw_folder_dawnext, "audio_per_item_fx.txt")
pydaw_file_pyitems = os.path.join(pydaw_folder_dawnext, "items.txt")
pydaw_file_pytransport = os.path.join(pydaw_folder_dawnext, "transport.txt")
pydaw_file_pytracks = os.path.join(pydaw_folder_dawnext, "tracks.txt")
pydaw_file_notes = os.path.join(pydaw_folder_dawnext, "notes.txt")

#Anything smaller gets deleted when doing a transform
pydaw_min_note_length = 4.0 / 129.0


class DawNextProject(libmk.AbstractProject):
    def __init__(self, a_with_audio):
        self.last_item_number = 1
        self.last_region_number = 1
        self.history_files = []
        self.history_commits = []
        self.history_undo_cursor = 0
        self.IPC = DawNextOsc(a_with_audio)
        self.suppress_updates = False

    def save_file(self, a_folder, a_file, a_text, a_force_new=False):
        f_result = libmk.AbstractProject.save_file(
            self, a_folder, a_file, a_text, a_force_new)
        if f_result:
            f_existed, f_old = f_result
            f_history_file = pydaw_history.pydaw_history_file(
                a_folder, a_file, a_text, f_old, f_existed)
            self.history_files.append(f_history_file)
            #TODO:  debug/verbose mode this output...
            print(str(f_history_file))

    def commit(self, a_message):
        """ Commit the project history """
        if self.history_undo_cursor > 0:
            self.history_commits = self.history_commits[
                :self.history_undo_cursor]
            self.history_undo_cursor = 0
        if len(self.history_files) > 0:
            self.history_commits.append(pydaw_history.pydaw_history_commit(
                self.history_files, a_message))
            self.history_files = []

    def undo(self):
        if self.history_undo_cursor >= len(self.history_commits):
            return False
        self.history_undo_cursor += 1
        self.history_commits[-1 * self.history_undo_cursor].undo(
            self.project_folder)
        return True

    def redo(self):
        if self.history_undo_cursor == 0:
            return False
        self.history_commits[-1 * self.history_undo_cursor].redo(
            self.project_folder)
        self.history_undo_cursor -= 1
        return True

    def get_files_dict(self, a_folder, a_ext=None):
        f_result = {}
        f_files = []
        if a_ext is not None :
            for f_file in os.listdir(a_folder):
                if f_file.endswith(a_ext):
                    f_files.append(f_file)
        else:
            f_files = os.listdir(a_folder)
        for f_file in f_files:
            f_result[f_file] = pydaw_read_file_text(
                "{}/{}".format(a_folder, f_file))
        return f_result

    def set_project_folders(self, a_project_file):
        #folders
        self.project_folder = os.path.dirname(a_project_file)
        self.project_file = os.path.splitext(
            os.path.basename(a_project_file))[0]
        self.items_folder = os.path.join(
            self.project_folder, pydaw_folder_items)
        self.dawnext_folder = os.path.join(
            self.project_folder, pydaw_folder_dawnext)
        self.track_pool_folder = os.path.join(
            self.project_folder, pydaw_folder_tracks)
        #files
        self.sequencer_file = os.path.join(
            self.project_folder, FILE_SEQUENCER)
        self.pyitems_file = os.path.join(
            self.project_folder, pydaw_file_pyitems)
        self.pyscale_file = os.path.join(
            self.project_folder, "default.pyscale")
        self.pynotes_file = os.path.join(
            self.project_folder, pydaw_file_notes)
        self.routing_graph_file = os.path.join(
            self.project_folder, pydaw_file_routing_graph)
        self.midi_routing_file = os.path.join(
            self.project_folder, pydaw_file_midi_routing)
        self.paif_file = os.path.join(
            self.project_folder, pydaw_file_audio_per_item_fx)
        self.automation_file = os.path.join(
            self.project_folder, pydaw_file_regions_atm)

        self.project_folders = [
            self.project_folder, self.items_folder, self.track_pool_folder,]

    def open_project(self, a_project_file, a_notify_osc=True):
        self.set_project_folders(a_project_file)
        if not os.path.exists(a_project_file):
            print("project file {} does not exist, creating as "
                "new project".format(a_project_file))
            self.new_project(a_project_file)

        if a_notify_osc:
            self.IPC.pydaw_open_song(self.project_folder)

    def new_project(self, a_project_file, a_notify_osc=True):
        self.set_project_folders(a_project_file)

        for project_dir in self.project_folders:
            print(project_dir)
            if not os.path.isdir(project_dir):
                os.makedirs(project_dir)

        self.create_file("", pydaw_file_pyitems, pydaw_terminating_char)
        self.create_file("", pydaw_file_pytransport, str(pydaw_transport()))
        f_tracks = pydaw_tracks()
        for i in range(TRACK_COUNT_ALL):
            f_tracks.add_track(i, pydaw_track(
                a_track_uid=i, a_track_pos=i,
                a_name="Master" if i == 0 else "track{}".format(i)))
        self.create_file("", pydaw_file_pytracks, str(f_tracks))

        self.commit("Created project")
        if a_notify_osc:
            self.IPC.pydaw_open_song(self.project_folder)

    def get_notes(self):
        if os.path.isfile(self.pynotes_file):
            return pydaw_read_file_text(self.pynotes_file)
        else:
            return ""

    def write_notes(self, a_text):
        pydaw_write_file_text(self.pynotes_file, a_text)

    def set_midi_scale(self, a_key, a_scale):
        pydaw_write_file_text(
            self.pyscale_file, "{}|{}".format(a_key, a_scale))

    def get_midi_scale(self):
        if os.path.exists(self.pyscale_file):
            f_list = pydaw_read_file_text(self.pyscale_file).split("|")
            return (int(f_list[0]), int(f_list[1]))
        else:
            return None

    def get_routing_graph(self):
        if os.path.isfile(self.routing_graph_file):
            with open(self.routing_graph_file) as f_handle:
                return pydaw_routing_graph.from_str(f_handle.read())
        else:
            return pydaw_routing_graph()

    def save_routing_graph(self, a_graph):
        self.save_file("", pydaw_file_routing_graph, str(a_graph))
        self.IPC.pydaw_update_track_send()

    def get_midi_routing(self):
        if os.path.isfile(self.midi_routing_file):
            with open(self.midi_routing_file) as f_handle:
                return pydaw_midi_routings.from_str(f_handle.read())
        else:
            return pydaw_midi_routings()

    def save_midi_routing(self, a_routing):
        self.save_file("", pydaw_file_midi_routing, str(a_routing))
        self.commit("Update MIDI routing")

    def get_items_dict(self):
        try:
            f_file = open(self.pyitems_file, "r")
        except:
            return pydaw_name_uid_dict()
        f_str = f_file.read()
        f_file.close()
        return pydaw_name_uid_dict.from_str(f_str)

    def save_items_dict(self, a_uid_dict):
        self.save_file("", pydaw_file_pyitems, str(a_uid_dict))

    def get_region(self):
        if os.path.isfile(self.sequencer_file):
            with open(self.sequencer_file) as f_file:
                return pydaw_sequencer.from_str(f_file.read())
        else:
            return pydaw_sequencer()

    def get_atm_region(self):
        if os.path.isfile(self.automation_file):
            with open(self.automation_file) as f_file:
                return pydaw_atm_region.from_str(f_file.read())
        else:
            return pydaw_atm_region()

    def save_atm_region(self, a_region):
        self.save_file(pydaw_folder_regions_atm, a_uid, str(a_region))
        self.IPC.pydaw_save_atm_region(a_uid)

    def rename_items(self, a_item_names, a_new_item_name):
        f_items_dict = self.get_items_dict()
        if len(a_item_names) > 1 or f_items_dict.name_exists(a_new_item_name):
            f_suffix = 1
            f_new_item_name = "{}-".format(a_new_item_name)
            for f_item_name in a_item_names:
                while f_items_dict.name_exists(
                "{}{}".format(f_new_item_name, f_suffix)):
                    f_suffix += 1
                f_items_dict.rename_item(
                    f_item_name, f_new_item_name + str(f_suffix))
        else:
            f_items_dict.rename_item(a_item_names[0], a_new_item_name)
        self.save_items_dict(f_items_dict)

    def rename_region(self, a_old_name, a_new_name):
        f_regions_dict = self.get_regions_dict()
        if f_regions_dict.name_exists(a_new_name):
            f_suffix = 1
            f_new_name = "{}-".format(a_new_name)
            while f_regions_dict.name_exists(f_new_name + str(f_suffix)):
                f_suffix += 1
            f_regions_dict.rename_item(a_old_name, f_new_name)
        else:
            f_regions_dict.rename_item(a_old_name, a_new_name)
        self.save_regions_dict(f_regions_dict)

    def set_vol_for_all_audio_items(self, a_uid, a_vol,
                                    a_reverse=None, a_same_vol=False,
                                    a_old_vol=0):
        """ a_uid:  wav_pool uid
            a_vol:  dB
            a_reverse:  None=All, True=reversed-only,
                False=only-if-not-reversed
        """
        f_uid = int(a_uid)
        f_changed_any = False
        assert(False)  # this needs to be reworked
        f_pysong = self.get_song()
        for f_region_uid in f_pysong.regions.values():
            f_audio_region = self.get_audio_region(f_region_uid)
            f_changed = False
            for f_audio_item in f_audio_region.items.values():
                if f_audio_item.uid == f_uid:
                    if a_reverse is None or \
                    (a_reverse and f_audio_item.reversed) or \
                    (not a_reverse and not f_audio_item.reversed):
                        if not a_same_vol or a_old_vol == f_audio_item.vol:
                            f_audio_item.vol = float(a_vol)
                            f_changed = True
            if f_changed:
                self.save_audio_region(f_region_uid, f_audio_region)
                f_changed_any = True
        if f_changed_any:
            self.commit("Changed volume for all audio items "
                "with uid {}".format(f_uid))

    def set_fades_for_all_audio_items(self, a_item):
        """ a_uid:  wav_pool uid
            a_item:  pydaw_audio_item
        """
        f_changed_any = False
        # this needs to be reworked
        assert(False)
        f_pysong = self.get_song()
        for f_region_uid in f_pysong.regions.values():
            f_audio_region = self.get_audio_region(f_region_uid)
            f_changed = False
            for f_audio_item in f_audio_region.items.values():
                if f_audio_item.uid == a_item.uid:
                    if a_item.reversed == f_audio_item.reversed and \
                    a_item.sample_start == f_audio_item.sample_start and \
                    a_item.sample_end == f_audio_item.sample_end:
                        f_audio_item.fade_in = a_item.fade_in
                        f_audio_item.fade_out = a_item.fade_out
                        f_audio_item.fadein_vol = a_item.fadein_vol
                        f_audio_item.fadeout_vol = a_item.fadeout_vol
                        f_changed = True
            if f_changed:
                self.save_audio_region(f_region_uid, f_audio_region)
                f_changed_any = True
        if f_changed_any:
            self.commit("Changed volume for all audio items "
                "with uid {}".format(a_item.uid))

    def set_output_for_all_audio_items(self, a_uid, a_index):
        """ a_uid:  wav_pool uid
            a_index:  output track
        """
        f_uid = int(a_uid)
        f_changed_any = False
        #this needs to be reworked
        assert(False)
        f_pysong = self.get_song()
        for f_region_uid in f_pysong.regions.values():
            f_audio_region = self.get_audio_region(f_region_uid)
            f_changed = False
            for f_audio_item in f_audio_region.items.values():
                if f_audio_item.uid == f_uid:
                    f_audio_item.output_track = int(a_index)
                    f_changed = True
            if f_changed:
                self.save_audio_region(f_region_uid, f_audio_region)
                f_changed_any = True
        if f_changed_any:
            self.commit("Changed output to {} for all "
                "audio items with uid {}".format(a_index, f_uid))

    def set_paif_for_all_audio_items(self, a_uid, a_paif):
        """ a_uid:  wav_pool uid
            a_paif:  a list that corresponds to a paif row
        """
        f_uid = int(a_uid)
        f_changed_any = False
        f_pysong = self.get_song()
        for f_region_uid in f_pysong.regions.values():
            f_audio_region = self.get_audio_region(f_region_uid)
            f_paif = self.get_audio_per_item_fx_region(f_region_uid)
            f_changed = False
            for f_index, f_audio_item in f_audio_region.items.items():
                if f_audio_item.uid == f_uid:
                    f_paif.set_row(f_index, a_paif)
                    self.save_audio_per_item_fx_region(f_region_uid, f_paif)
                    self.IPC.pydaw_audio_per_item_fx_region(
                        f_region_uid)
                    f_changed = True
            if f_changed:
                self.save_audio_region(f_region_uid, f_audio_region)
                f_changed_any = True
        if f_changed_any:
            self.commit("Update per-audio-item-fx for all audio "
                "items with uid {}".format(f_uid))

    def get_item_string(self, a_item_uid):
        try:
            f_file = open("{}/{}".format(self.items_folder, a_item_uid), "r")
        except:
            return ""
        f_result = f_file.read()
        f_file.close()
        return f_result

    def get_item_by_uid(self, a_item_uid):
        a_item_uid = int(a_item_uid)
        return pydaw_item.from_str(
            self.get_item_string(a_item_uid), a_item_uid)

    def get_item_by_name(self, a_item_name):
        f_items_dict = self.get_items_dict()
        return pydaw_item.from_str(
            self.get_item_string(f_items_dict.get_uid_by_name(a_item_name)))

    def save_recorded_items(
            self, a_item_name, a_mrec_list, a_overdub, a_tempo, a_sr):
        print("\n".join(a_mrec_list))
        # TODO:  Ensure that the user can't switch MIDI device/track during
        # recording, but can during playback...
        f_mrec_items = [x.split("|") for x in a_mrec_list]
        f_mrec_items.sort(key=lambda x: int(x[-1]))
        print("\n".join(str(x) for x in f_mrec_items))
        f_song = self.get_song()
        f_note_tracker = {}
        f_items_to_save = {}
        f_regions_to_save = {}
        f_last_bar = -1
        f_last_region = -1
        self.rec_item = None
        f_current_region = None
        f_beats_per_second = float(a_tempo) / 60.0
        f_item_name = str(a_item_name)
        f_items_dict = self.get_items_dict()
        f_orig_items = {}
        self.rec_take = None

        def get_item(a_region, a_track_num, a_bar_num):
            if a_region in f_orig_items:
                for f_item in f_orig_items[a_region]:
                    if f_item.bar_num == int(a_bar_num) and \
                    f_item.track_num == int(a_track_num):
                        return f_item.item_uid
            return None

        def new_take():
            self.rec_take = {}

        def copy_take(a_track_num):
            f_length = f_current_region.get_length()
            for f_i in range(f_length):
                if a_overdub:
                    copy_item(f_i)
                else:
                    new_item(f_i, a_track_num)

        def new_item(a_bar, a_track_num):
            f_name = self.get_next_default_item_name(f_item_name)
            f_uid = self.create_empty_item(f_name)
            f_item = self.get_item_by_uid(f_uid)
            f_items_to_save[f_uid] = f_item
            if a_track_num not in self.rec_take:
                self.rec_take[a_track_num] = {}
            self.rec_take[a_track_num][a_bar] = f_item
            f_current_region.add_item_ref_by_uid(
                a_track_num, a_bar, f_uid)

        def copy_item(a_bar, a_track_num):
            f_uid = get_item(a_track_num, a_bar)
            if f_uid is not None:
                f_old_name = f_items_dict.get_name_by_uid(f_uid)
                f_name = self.get_next_default_item_name(
                    f_item_name)
                f_uid = self.copy_item(f_old_name, f_name)
                f_item = self.get_item_by_uid(f_uid)
                f_items_to_save[f_uid] = f_item
                self.rec_take[a_track_num][a_bar] = f_item
                f_current_region.add_item_ref_by_uid(
                    a_track_num, a_bar, f_uid)
            else:
                new_item(a_bar, a_track_num)

        def pos_subtract(a_start_bar, a_start_beat, a_end_bar, a_end_beat):
            return (float(a_end_bar - a_start_bar)
                * 4.0) + (a_end_beat - a_start_beat)

        def set_note_length(a_track_num, f_note_num,
        f_end_bar, f_end_beat, f_tick):
            f_note = f_note_tracker[a_track_num][f_note_num]
            f_length = pos_subtract(
                f_note.bar, f_note.start, f_end_bar, f_end_beat)
            if f_length > 0.0:
                print("Using beat length for:")
                f_note.set_length(f_length)
            else:
                print("Using tick length for:")
                f_sample_count = f_tick - f_note.start_sample
                f_seconds = float(f_sample_count) / float(a_sr)
                f_note.set_length(f_seconds * f_beats_per_second)
            print(f_note_tracker[a_track_num].pop(f_note_num))

        for f_event in f_mrec_items:
            f_type, f_region, f_bar, f_beat, f_track = f_event[:5]
            f_region, f_bar, f_track = (
                int(x) for x in (f_region, f_bar, f_track))
            f_beat = float(f_beat)
            if not f_track in f_note_tracker:
                f_note_tracker[f_track] = {}
            if f_region in f_song.regions:
                if f_region not in f_regions_to_save:
                    f_regions_to_save[f_region] = self.get_region_by_uid(
                        f_song.regions[f_region])
                    f_orig_items[f_region] = f_regions_to_save[
                        f_region].items[:]
            else:
                f_name = self.get_next_default_region_name(f_item_name)
                f_uid = self.create_empty_region(f_name)
                f_regions_to_save[f_region] = self.get_region_by_uid(f_uid)
                f_song.add_region_ref_by_uid(f_region, f_uid)

            f_current_region = f_regions_to_save[f_region]

            f_is_looping = f_type == "loop"

            if f_is_looping or \
            f_last_region != f_region or \
            f_last_bar != f_bar:
                if f_is_looping or f_region != f_last_region:
                    new_take()
                f_last_region = f_region
                f_last_bar = f_bar

            if f_type == "loop":
                print("Loop event")
                continue

            if not f_track in self.rec_take:
                    copy_take(f_track)

            self.rec_item = self.rec_take[f_track][f_bar]

            if f_type == "on":
                f_note_num, f_velocity, f_tick = (int(x) for x in f_event[5:])
                print("New note: {} {} {}".format(f_bar, f_beat, f_note_num))
                f_note = pydaw_note(f_beat, 1.0, f_note_num, f_velocity)
                f_note.bar = f_bar
                f_note.start_sample = f_tick
                if f_note_num in f_note_tracker[f_track]:
                    print("Terminating note early: {}".format(
                        (f_track, f_note_num, f_tick)))
                    set_note_length(
                        f_track, f_note_num, f_bar, f_beat, f_tick)
                f_note_tracker[f_track][f_note_num] = f_note
                self.rec_item.add_note(f_note, a_check=False)
            elif f_type == "off":
                f_note_num, f_tick = (int(x) for x in f_event[5:])
                if f_note_num in f_note_tracker[f_track]:
                    set_note_length(
                        f_track, f_note_num, f_bar, f_beat, f_tick)
                else:
                    print("Error:  note event not in note tracker")
            elif f_type == "cc":
                f_port, f_val = f_event[5:]
                f_port = int(f_port)
                f_val = float(f_val)
                f_cc = pydaw_cc(f_beat, f_port, f_val)
                self.rec_item.add_cc(f_cc)
            elif f_type == "pb":
                f_pb = pydaw_pitchbend(f_beat, float(f_event[4]) / 8192.0)
                self.rec_item.add_pb(f_pb)
            else:
                print("Invalid mrec event type {}".format(f_type))

        for f_uid, f_item in f_items_to_save.items():
            f_item.fix_overlaps()
            self.save_item_by_uid(f_uid, f_item, a_new_item=True)
            f_name = self.get_next_default_item_name(f_item_name)

        f_region_dict = self.get_regions_dict()

        for f_region in f_regions_to_save.values():
            f_name = f_region_dict.get_name_by_uid(f_region.uid)
            self.save_region(f_name, f_region)

        self.save_song(f_song)
        self.commit("Record MIDI")

    def reorder_tracks(self, a_dict):
        f_tracks = self.get_tracks()
        f_tracks.reorder(a_dict)
        self.save_tracks(f_tracks)

        f_track_plugins = {k:self.get_track_plugins(k)
            for k in f_tracks.tracks}
        # Delete the existing track files
        for k in f_track_plugins:
            f_path = os.path.join(
                *(str(x) for x in (self.track_pool_folder, k)))
            if os.path.exists(f_path):
                os.remove(f_path)
        for k, v in f_track_plugins.items():
            if v:
                self.save_track_plugins(a_dict[k], v)

        f_graph = self.get_routing_graph()
        f_graph.reorder(a_dict)
        self.save_routing_graph(f_graph)

        f_regions_dict = self.get_regions_dict()

        for f_uid in f_regions_dict.name_lookup:
            f_region = self.get_region_by_uid(f_uid)
            f_region.reorder(a_dict)
            self.save_region_by_uid(f_uid, f_region)
            f_audio_region = self.get_audio_region(f_uid)
            f_audio_region.reorder(a_dict)
            self.save_audio_region(f_uid, f_audio_region)
        self.IPC.pydaw_open_song(self.project_folder)
        self.commit("Re-order tracks")

    def get_tracks_string(self):
        try:
            f_file = open(
                os.path.join(self.project_folder, pydaw_file_pytracks))
        except:
            return pydaw_terminating_char
        f_result = f_file.read()
        f_file.close()
        return f_result

    def get_tracks(self):
        return pydaw_tracks.from_str(self.get_tracks_string())

    def get_track_plugins(self, a_track_num):
        f_folder = self.track_pool_folder
        f_path = "{}/{}".format(f_folder, a_track_num)
        if os.path.isfile(f_path):
            with open(f_path) as f_handle:
                f_str = f_handle.read()
            return libmk.pydaw_track_plugins.from_str(f_str)
        else:
            return None

    def get_audio_per_item_fx_region(self, a_region_uid):
        f_path = "{}/{}".format(self.audio_per_item_fx_folder, a_region_uid)
        #TODO:  Sort this out at PyDAWv4 and create an empty file first
        if not os.path.isfile(f_path):
            return pydaw_audio_item_fx_region()
        else:
            f_text = pydaw_read_file_text(f_path)
            return pydaw_audio_item_fx_region.from_str(f_text)

    def save_audio_per_item_fx_region(self, a_region_uid, a_paif,
                                      a_commit=True):
        if not self.suppress_updates:
            self.save_file(
                pydaw_folder_audio_per_item_fx, str(a_region_uid), str(a_paif))
            if a_commit:
                self.commit("Update per-audio-item effects")

    def get_transport(self):
        try:
            f_file = open(
                "{}/{}".format(self.project_folder, pydaw_file_pytransport))
        except:
            return pydaw_transport()  #defaults
        f_str = f_file.read()
        f_file.close()
        f_result = pydaw_transport.from_str(f_str)
        f_file_name = "{}/default.pymididevice".format(self.project_folder)
        if os.path.isfile(f_file_name):
            f_file = open(f_file_name)
            f_result.midi_keybd = f_file.read()
            f_file.close()
        return f_result

    def save_transport(self, a_transport):
        if not self.suppress_updates:
            self.save_file("", pydaw_file_pytransport, str(a_transport))

    def create_empty_region(self, a_region_name):
        # TODO:  Check for uniqueness, from
        # a DawNextProject.check_for_uniqueness method...
        f_regions_dict = self.get_regions_dict()
        f_uid = f_regions_dict.add_new_item(a_region_name)
        self.save_file(pydaw_folder_regions, f_uid, pydaw_terminating_char)
        self.save_file(
            pydaw_folder_regions_audio, f_uid, pydaw_terminating_char)
        self.save_file(
            pydaw_folder_regions_atm, f_uid, pydaw_terminating_char)
        self.save_regions_dict(f_regions_dict)
        return f_uid

    def create_empty_item(self):
        f_items_dict = self.get_items_dict()
        f_item_name = self.get_next_default_item_name(
            a_items_dict=f_items_dict)
        f_uid = f_items_dict.add_new_item(f_item_name)
        self.save_file(pydaw_folder_items, str(f_uid), pydaw_item(f_uid))
        self.IPC.pydaw_save_item(f_uid)
        self.save_items_dict(f_items_dict)
        return f_uid

    def copy_region(self, a_old_region_name, a_new_region_name):
        f_regions_dict = self.get_regions_dict()
        f_uid = f_regions_dict.add_new_item(a_new_region_name)
        f_old_uid = f_regions_dict.get_uid_by_name(a_old_region_name)
        self.save_file(
            pydaw_folder_regions,  str(f_uid),
            pydaw_read_file_text(
                "{}/{}".format(self.regions_folder, f_old_uid)))
        self.save_file(
            pydaw_folder_regions_audio,  str(f_uid),
            pydaw_read_file_text(
                "{}/{}".format(self.regions_audio_folder, f_old_uid)))
        self.save_file(
            pydaw_folder_regions_atm,  str(f_uid),
            pydaw_read_file_text(
                "{}/{}".format(self.regions_atm_folder, f_old_uid)))
        f_paif_file = "{}/{}".format(self.audio_per_item_fx_folder, f_old_uid)
        if os.path.isfile(f_paif_file):
            self.save_file(pydaw_folder_audio_per_item_fx, str(f_uid),
                           pydaw_read_file_text(f_paif_file))
        self.save_regions_dict(f_regions_dict)
        return f_uid

    def region_audio_clone(self, a_dest_region_uid, a_src_region_name):
        f_regions_dict = self.get_regions_dict()
        f_uid = f_regions_dict.get_uid_by_name(a_src_region_name)
        self.save_file(
            pydaw_folder_regions_audio, str(a_dest_region_uid),
            pydaw_read_file_text(
                "{}/{}".format(self.regions_audio_folder, f_uid)))
        f_paif_file = "{}/{}".format(self.audio_per_item_fx_folder, f_uid)
        if os.path.isfile(f_paif_file):
            self.save_file(
                pydaw_folder_audio_per_item_fx, str(a_dest_region_uid),
                pydaw_read_file_text(f_paif_file))
            self.IPC.pydaw_audio_per_item_fx_region(
                a_dest_region_uid)
        self.IPC.pydaw_reload_audio_items(a_dest_region_uid)
        self.commit("Clone audio from region {}".format(a_src_region_name))

    def copy_item(self, a_old_item, a_new_item):
        f_items_dict = self.get_items_dict()
        f_uid = f_items_dict.add_new_item(a_new_item)
        f_old_uid = f_items_dict.get_uid_by_name(a_old_item)
        self.save_file(pydaw_folder_items,  str(f_uid), pydaw_read_file_text(
            "{}/{}".format(self.items_folder, f_old_uid)))
        self.IPC.pydaw_save_item(f_uid)
        self.save_items_dict(f_items_dict)
        return f_uid

    def save_item(self, a_name, a_item):
        if not self.suppress_updates:
            f_items_dict = self.get_items_dict()
            f_uid = f_items_dict.get_uid_by_name(a_name)
            self.save_file(pydaw_folder_items, str(f_uid), str(a_item))
            self.IPC.pydaw_save_item(f_uid)

    def save_item_by_uid(self, a_uid, a_item, a_new_item=False):
        if not self.suppress_updates:
            f_uid = int(a_uid)
            self.save_file(
                pydaw_folder_items, str(f_uid), str(a_item), a_new_item)
            self.IPC.pydaw_save_item(f_uid)

    def save_region(self, a_region):
        if not self.suppress_updates:
            self.save_file("", FILE_SEQUENCER, str(a_region))
            self.IPC.pydaw_save_region()

    def save_tracks(self, a_tracks):
        if not self.suppress_updates:
            self.save_file("", pydaw_file_pytracks, str(a_tracks))
            #Is there a need for a configure message here?

    def save_track_plugins(self, a_uid, a_track):
        f_folder = pydaw_folder_tracks
        if not self.suppress_updates:
            self.save_file(f_folder, str(a_uid), str(a_track))

    def save_audio_region(self, a_region_uid, a_tracks):
        if not self.suppress_updates:
            self.save_file(
                pydaw_folder_regions_audio, str(a_region_uid), str(a_tracks))
            self.IPC.pydaw_reload_audio_items(a_region_uid)

    def item_exists(self, a_item_name, a_name_dict=None):
        if a_name_dict is None:
            f_name_dict = self.get_items_dict()
        else:
            f_name_dict = a_name_dict
        if str(a_item_name) in f_name_dict.uid_lookup:
            return True
        else:
            return False

    def get_next_default_item_name(self, a_item_name="item",
                                   a_items_dict=None):
        f_item_name = str(a_item_name)
        f_end_number = re.search(r"[0-9]+$", f_item_name)
        if f_item_name == "item":
            f_start = self.last_item_number
        else:
            if f_end_number:
                f_num_str = f_end_number.group()
                f_start = int(f_num_str)
                f_item_name = f_item_name[:-len(f_num_str)]
                f_item_name = f_item_name.strip('-')
            else:
                f_start = 1
        if a_items_dict:
            f_items_dict = a_items_dict
        else:
            f_items_dict = self.get_items_dict()
        for i in range(f_start, 10000):
            f_result = "{}-{}".format(f_item_name, i)
            if not f_result in f_items_dict.uid_lookup:
                if f_item_name == "item":
                    self.last_item_number = i
                return f_result

    def get_next_default_region_name(self, a_region_name="region"):
        f_regions_dict = self.get_regions_dict()
        if str(a_region_name) != "region" and \
        not str(a_region_name) in f_regions_dict.uid_lookup:
            return str(a_region_name)
        for i in range(self.last_region_number, 10000):
            f_result = str(a_region_name) + "-" + str(i)
            if not f_result in f_regions_dict.uid_lookup:
                if str(a_region_name) == "region":
                    self.last_region_number = i
                return f_result

    def get_item_list(self):
        f_result = self.get_items_dict()
        return sorted(f_result.uid_lookup.keys())

    def get_region_list(self):
        f_result = self.get_regions_dict()
        return sorted(f_result.uid_lookup.keys())

    def error_log_write(self, a_message):
        f_file = open("{}/error.log".format(self.project_folder), "a")
        f_file.write(a_message)
        f_file.close()

    def check_audio_files(self):
        """ Verify that all audio files exist  """
        f_result = []
        f_regions = self.get_regions_dict()
        f_wav_pool = self.get_wavs_dict()
        f_to_delete = []
        f_commit = False
        for k, v in list(f_wav_pool.name_lookup.items()):
            if not os.path.isfile(v):
                f_to_delete.append(k)
        if len(f_to_delete) > 0:
            f_commit = True
            for f_key in f_to_delete:
                f_wav_pool.name_lookup.pop(f_key)
            self.save_wavs_dict(f_wav_pool)
            self.error_log_write("Removed missing audio item(s) from wav_pool")
        for f_uid in list(f_regions.uid_lookup.values()):
            f_to_delete = []
            f_region = self.get_audio_region(f_uid)
            for k, v in list(f_region.items.items()):
                if not f_wav_pool.uid_exists(v.uid):
                    f_to_delete.append(k)
            if len(f_to_delete) > 0:
                f_commit = True
                for f_key in f_to_delete:
                    f_region.remove_item(f_key)
                f_result += f_to_delete
                self.save_audio_region(f_uid, f_region)
                self.error_log_write("Removed missing audio item(s) "
                    "from region {}".format(f_uid))
        if f_commit:
            self.commit("")
        return f_result

class pydaw_sequencer_item:
    def __init__(
            self, a_track_num, a_start_beat, a_length_beats,
            a_item_uid, a_start_pos=0.0):
        self.track_num = int(a_track_num)
        self.start_beat = float(a_start_beat)
        self.length_beats = float(a_length_beats)
        self.item_uid = int(a_item_uid)
        self.sample_start = float(a_start_pos)

    def clone(self):
        f_self = str(self).split("|")
        return pydaw_sequencer_item(*f_self)

    def __str__(self):
        return "|".join(str(x) for x in
            (self.track_num, round(self.start_beat, 6),
            round(self.length_beats, 6), self.item_uid,
            round(self.sample_start, 6)))

    def __lt__(self, other):
        if self.track_num == other.track_num:
            return self.start_beat < other.start_beat
        else:
            return self.track_num < other.track_num

class pydaw_sequencer:
    def __init__(self):
        self.items = []
        self.beats_per_measure = 4
        self.length_bars = 32

    def reorder(self, a_dict):
        for f_item in self.items:
            f_item.track_num = a_dict[f_item.track_num]

    def add_item_ref_by_name(
            self, a_track_num, a_start_beat,
            a_length_beats, a_item_name, a_uid_dict):
        f_item_uid = a_uid_dict.get_uid_by_name(a_item_name)
        self.add_item_ref_by_uid(
            a_track_num, a_start_beat, a_length_beats, f_item_uid)

    def add_item_ref_by_uid(
            self, a_track_num, a_start_beat, a_length_beats, a_item_uid):
        self.remove_item_ref(
            a_track_num, a_start_beat, a_length_beats, a_item_uid)
        self.items.append(pydaw_sequencer_item(
            a_track_num, a_start_beat, a_length_beats, a_item_uid))

    def add_item(self, a_item):
        self.items.append(a_item)

    def remove_item_ref(
            self, a_track_num, a_start_beat, a_length_beats, a_item_uid):
        f_to_remove = pydaw_sequencer_item(
            a_track_num, a_start_beat, a_length_beats, a_item_uid)
        f_to_remove = str(f_to_remove)
        for f_item in self.items:
            if str(f_item) == f_to_remove:
                self.items.remove(f_item)

    def get_length(self):
        return int(self.length_bars * self.beats_per_measure)

    def __str__(self):
        f_result = []
        f_result.append("L|{}".format(self.length_bars))
        f_result.append("T|{}".format(self.beats_per_measure))
        f_result.append("C|{}".format(len(self.items)))
        self.items.sort()
        for f_item in self.items:
            f_result.append(str(f_item))
        f_result.append(pydaw_terminating_char)
        return "\n".join(f_result)

    @staticmethod
    def from_str(a_str):
        f_result = pydaw_sequencer()
        f_arr = a_str.split("\n")
        for f_line in f_arr:
            if f_line == pydaw_terminating_char:
                break
            else:
                f_item_arr = f_line.split("|")
                if f_item_arr[0] == "L":
                    f_result.length_bars = int(f_item_arr[1])
                    continue
                if f_item_arr[0] == "T":
                    f_result.beats_per_measure = int(f_item_arr[1])
                    continue
                if f_item_arr[0] == "C":
                    continue
                f_result.add_item(pydaw_sequencer_item(*f_item_arr))
        f_result.items.sort()
        return f_result


class pydaw_atm_region:
    def __init__(self):
        self.plugins = {}

    def split(self, a_index):
        f_region0 = pydaw_atm_region()
        f_region1 = pydaw_atm_region()
        for f_plugin in self.plugins:
            for f_list in self.plugins[f_plugin].values():
                for f_item in f_list:
                    if f_item.bar >= a_index:
                        f_item.bar -= a_index
                        f_region1.add_point(f_item)
                    else:
                        f_region0.add_point(f_item)
        return f_region0, f_region1

    def add_port_list(self, a_point):
        if not a_point.index in self.plugins:
            self.plugins[a_point.index] = {}
        if not a_point.port_num in self.plugins[a_point.index]:
            self.plugins[a_point.index][a_point.port_num] = []

    def add_point(self, a_point):
        self.add_port_list(a_point)
        self.plugins[a_point.index][a_point.port_num].append(a_point)

    def remove_point(self, a_point):
        #self.add_port_list(a_point)
        self.plugins[a_point.index][a_point.port_num].remove(a_point)

    def get_ports(self, a_index):
        a_index = int(a_index)
        if a_index not in self.plugins:
            return []
        else:
            return sorted(self.plugins[a_index])

    def get_points(self, a_index, a_port_num):
        a_port_num = int(a_port_num)
        a_index = int(a_index)
        if a_index not in self.plugins or \
        a_port_num not in self.plugins[a_index]:
            return []
        else:
            f_result = self.plugins[a_index][a_port_num]
            f_result.sort()
            return f_result

    def clear_range(
            self, a_index, a_port_num, a_start_bar, a_start_beat,
            a_end_bar, a_end_beat):
        f_list = self.get_points(a_index, a_port_num)
        if f_list:
            f_result = [x for x in f_list if
                (x.bar < a_start_bar or x.bar > a_end_bar) or
                (x.bar == a_start_bar and x.beat < a_start_beat) or
                (x.bar == a_end_bar and x.beat > a_end_beat)]
            self.plugins[a_index][a_port_num] = f_result

    def smooth_points(
            self, a_index, a_port_num, a_plugin_index, a_points):
        if len(a_points) <= 1:
            return
        f_start = a_points[0]
        f_end = a_points[-1]
        self.clear_range(
            a_index, a_port_num,
            f_start.bar, f_start.beat, f_end.bar, f_end.beat)
        f_inc = 0.0625 # 64th note
        f_result = self.plugins[a_index][a_port_num]
        for f_point, f_next in zip(a_points, a_points[1:]):
            f_bar = f_point.bar
            f_beat = f_point.beat + f_inc
            f_val = f_point.cc_val
            f_bar_next = f_next.bar
            f_beat_next = f_next.beat
            f_val_next = f_next.cc_val
            if round(f_val, 3) == round(f_val_next, 3):
                f_result.append(f_point)
                f_result.append(f_next)
                continue
            f_beat_diff = count_beats(
                f_bar, f_beat, f_bar_next, f_beat_next)
            if f_beat_diff < f_inc:
                continue
            f_val_diff = f_val_next - f_val
            f_inc_count = int(round(f_beat_diff / f_inc))
            f_val_inc = f_val_diff / f_inc_count
            for f_i in range(f_inc_count - 1):
                f_result.append(pydaw_atm_point(
                    f_bar, f_beat, a_port_num, f_val,
                    a_index, a_plugin_index))
                f_val += f_val_inc
                f_beat += f_inc
                if f_beat >= 4.0:
                    f_beat -= 4.0
                    f_bar += 1
            f_result.append(a_points[-1])

    def __str__(self):
        f_result = []
        for f_index in sorted(self.plugins):
            f_point_list = []
            for f_port in self.plugins[f_index].values():
                f_point_list.extend(f_port)
            f_point_len = len(f_point_list)
            if f_point_len == 0:
                continue
            f_result.append(
                "|".join(str(x) for x in
                ("p", f_index, f_point_len)))
            for f_point in sorted(f_point_list):
                f_result.append(str(f_point))
        f_result.append(pydaw_terminating_char)
        return "\n".join(f_result)

    @staticmethod
    def from_str(a_str):
        f_result = pydaw_atm_region()
        for f_line in str(a_str).split("\n"):
            if f_line == pydaw_terminating_char:
                break
            if f_line[0] == "p":
                continue
            f_point = pydaw_atm_point.from_str(f_line)
            f_result.add_point(f_point)
        return f_result

class pydaw_atm_point:
    def __init__(
            self, a_bar, a_beat, a_port_num, a_cc_val,
            a_index, a_plugin_index):
        self.bar = int(a_bar)
        self.beat = round(float(a_beat), 4)
        self.port_num = int(a_port_num)
        self.cc_val = round(float(a_cc_val), 4)
        self.index = int(a_index) # Now means plugin pool UID
        self.plugin_index = int(a_plugin_index) # UID of the plugin

    def set_val(self, a_val):
        self.cc_val = pydaw_clip_value(float(a_val), 0.0, 127.0, True)

    def __lt__(self, other):
        return ((self.bar < other.bar) or
            (self.bar == other.bar and self.beat <= other.beat))

#    def __eq__(self, other):
#        return (
#            (self.track == other.track) and
#            (self.bar == other.bar) and
#            (self.beat == other.beat) and
#            (self.port_num == other.port_num) and
#            (self.cc_val == other.cc_val) and
#            (self.index == other.index) and
#            (self.plugin_index == other.plugin_index))

    def __str__(self):
        return "|".join(str(x) for x in (
            self.bar, self.beat, self.port_num, self.cc_val,
            self.index, self.plugin_index))

    @staticmethod
    def from_arr(a_arr):
        f_result = pydaw_atm_point(*a_arr)
        return f_result

    @staticmethod
    def from_str(a_str):
        f_arr = a_str.split("|")
        return pydaw_atm_point.from_arr(f_arr)

    def clone(self):
        return pydaw_atm_point.from_str(str(self))


def pydaw_smooth_automation_points(
    a_items_list, a_is_cc, a_cc_num=-1):
    if a_is_cc:
        f_this_cc_arr = []
        f_beat_offset = 0.0
        f_index = 0
        f_cc_num = int(a_cc_num)
        f_result_arr = []
        for f_item in a_items_list:
            for f_cc in f_item.ccs:
                if f_cc.cc_num == f_cc_num:
                    f_new_cc = pydaw_cc(
                        (f_cc.start + f_beat_offset), f_cc_num, f_cc.cc_val)
                    f_new_cc.item_index = f_index
                    f_new_cc.beat_offset = f_beat_offset
                    f_this_cc_arr.append(f_new_cc)
            f_beat_offset += 4.0
            f_index += 1
            f_result_arr.append([])

        f_result_arr_len = len(f_result_arr)
        f_this_cc_arr.sort()
        for i in range(len(f_this_cc_arr) - 1):
            f_val_diff = abs(
                f_this_cc_arr[i + 1].cc_val - f_this_cc_arr[i].cc_val)
            if f_val_diff == 0:
                continue
            f_time_inc = .0625  #1/16 of a beat
            f_start = f_this_cc_arr[i].start + f_time_inc

            f_start_diff = f_this_cc_arr[i + 1].start - f_this_cc_arr[i].start
            if f_start_diff == 0.0:
                continue

            f_inc = (f_val_diff / (f_start_diff * 16.0))
            if (f_this_cc_arr[i].cc_val) > (f_this_cc_arr[i + 1].cc_val):
                f_inc *= -1.0
            f_new_val = f_this_cc_arr[i].cc_val + f_inc
            while True:
                f_index_offset = 0
                f_adjusted_start = f_start - f_this_cc_arr[i].beat_offset
                while f_adjusted_start >= 4.0:
                    f_index_offset += 1
                    f_adjusted_start -= 4.0
                f_interpolated_cc = pydaw_cc(
                    f_adjusted_start, f_cc_num, f_new_val)
                f_new_val += f_inc
                f_new_index = f_this_cc_arr[i].item_index + f_index_offset
                if f_new_index >= f_result_arr_len:
                    print(
                        "Error, {} >= {}".format(
                        f_new_index, f_result_arr_len))
                    break
                f_result_arr[f_new_index].append(f_interpolated_cc)
                f_start += f_time_inc
                if f_start >= (f_this_cc_arr[i + 1].start - 0.0625):
                    break
        for f_i in range(len(a_items_list)):
            a_items_list[f_i].ccs += f_result_arr[f_i]
            a_items_list[f_i].ccs.sort()
    else:
        f_this_pb_arr = []
        f_beat_offset = 0.0
        f_index = 0
        f_result_arr = []
        for f_item in a_items_list:
            for f_pb in f_item.pitchbends:
                f_new_pb = pydaw_pitchbend(
                    f_pb.start + f_beat_offset, f_pb.pb_val)
                f_new_pb.item_index = f_index
                f_new_pb.beat_offset = f_beat_offset
                f_this_pb_arr.append(f_new_pb)
            f_beat_offset += 4.0
            f_index += 1
            f_result_arr.append([])
        f_result_arr_len = len(f_result_arr)
        for i in range(len(f_this_pb_arr) - 1):
            f_val_diff = abs(
                f_this_pb_arr[i + 1].pb_val - f_this_pb_arr[i].pb_val)
            if f_val_diff == 0.0:
                continue
            f_time_inc = 0.0625
            f_start = f_this_pb_arr[i].start + f_time_inc
            f_start_diff = f_this_pb_arr[i + 1].start - f_this_pb_arr[i].start
            if f_start_diff == 0.0:
                continue
            f_val_inc = f_val_diff / (f_start_diff * 16.0)
            if f_this_pb_arr[i].pb_val > f_this_pb_arr[i + 1].pb_val:
                f_val_inc *= -1.0
            f_new_val = f_this_pb_arr[i].pb_val + f_val_inc

            while True:
                f_index_offset = 0
                f_adjusted_start = f_start - f_this_pb_arr[i].beat_offset
                while f_adjusted_start >= 4.0:
                    f_index_offset += 1
                    f_adjusted_start -= 4.0
                f_interpolated_pb = pydaw_pitchbend(
                    f_adjusted_start, f_new_val)
                f_new_val += f_val_inc
                f_new_index = f_this_pb_arr[i].item_index + f_index_offset
                if f_new_index >= f_result_arr_len:
                    print(
                        "Error, {} >= {}".format(
                        f_new_index, f_result_arr_len))
                    break
                f_result_arr[f_new_index].append(f_interpolated_pb)
                f_start += f_time_inc
                if f_start >= (f_this_pb_arr[i + 1].start - 0.0625):
                    break
        for f_i in range(len(a_items_list)):
            a_items_list[f_i].pitchbends += f_result_arr[f_i]
            a_items_list[f_i].pitchbends.sort()

def pydaw_velocity_mod(
        a_items, a_amt, a_line=False, a_end_amt=127,
        a_add=False, a_selected_only=False):
    f_start_beat = 0.0
    f_range_beats = 0.0
    f_tmp_index = 0
    f_break = False
    f_result = []

    for f_item in a_items:
        for note in f_item.notes:
            if not a_selected_only or (a_selected_only and note.is_selected):
                f_start_beat = note.start + (f_tmp_index * 4.0)
                f_break = True
                break
        if f_break:
            break
        f_tmp_index += 1
    f_tmp_index = len(a_items) - 1
    f_break = False
    for f_item in reversed(a_items):
        for note in reversed(f_item.notes):
            if not a_selected_only or note.is_selected:
                f_range_beats = note.start + (4.0 * f_tmp_index) - f_start_beat
                f_break = True
                break
        if f_break:
            break
        f_tmp_index -= 1

    f_beat_offset = 0.0
    for f_index, f_item in zip(range(len(a_items)), a_items):
        for note in f_item.notes:
            if a_selected_only and not note.is_selected:
                continue
            if a_line and f_range_beats != 0.0:
                f_frac = ((note.start + f_beat_offset -
                    f_start_beat) / f_range_beats)
                f_value = int(((a_end_amt - a_amt) * f_frac) + a_amt)
            else:
                f_value = int(a_amt)
            if a_add:
                note.velocity += f_value
            else:
                note.velocity = f_value
            if note.velocity > 127:
                note.velocity = 127
            elif note.velocity < 1:
                note.velocity = 1
            f_result.append("{}|{}".format(f_index, note))
        f_beat_offset += 4.0
    return f_result


class pydaw_item:
    def __init__(self, a_uid):
        self.items = {}  # audio items:  TODO rename
        self.notes = []
        self.ccs = []
        self.pitchbends = []
        self.length = 4
        self.uid = int(a_uid)

    def painter_path(self, a_width, a_height):
        f_result = QtGui.QPainterPath()
        f_note_height = float(a_height) / 128.0
        f_beat_width = a_width * 0.25
        for f_note in self.notes:
            f_y_pos = a_height - (f_note_height * float(f_note.note_num))
            f_x_pos = f_note.start * f_beat_width
            f_width = f_note.length * f_beat_width
            f_result.addRect(f_x_pos, f_y_pos, f_width, f_note_height)
        return f_result

    def add_note(self, a_note, a_check=True):
        if a_check:
            for note in self.notes:
                if note.overlaps(a_note):
                    # TODO:  return -1 instead of True, and the
                    # offending editor_index when False
                    return False
        self.notes.append(a_note)
        self.notes.sort()
        if not a_check:
            self.fix_overlaps()
        return True

    def remove_note(self, a_note):
        try:
            self.notes.remove(a_note)
        except Exception as ex:
            print("\n\n\nException in remove_note:\n{}".format(ex))
            print((repr(traceback.extract_stack())))
            print("\n\n\n")

    def velocity_mod(self, a_amt, a_start_beat=0.0,
                     a_end_beat=4.0, a_line=False,
                     a_end_amt=127, a_add=False, a_notes=None):
        """ velocity_mod
        (self, a_amt, #The amount to add or subtract
         a_start_beat=0.0, #modify values with a start at >= this, and...
         a_end_beat=4.0, # <= to this.
         a_line=False, # draw a line to a_end,
             otherwise all events are modified by a_amt
         a_end_amt=127, #not used unless a_line=True
         a_add=False, #True to add/subtract from each value, False to assign
         a_notes=None) #Process all notes if None, or
             selected if a list of notes is provided

         Modify the velocity of a range of notes
         """
        f_notes = []

        if a_notes is None:
            f_notes = self.notes
        else:
            for f_note in a_notes:
                for f_note2 in self.notes:
                    if f_note2 == f_note:
                        f_notes.append(f_note2)
                        break

        f_range_beats = a_end_beat - a_start_beat

        for note in f_notes:
            if note.start >= a_start_beat and note.start <= a_end_beat:
                if a_line:
                    f_frac = ((note.start - a_start_beat)/f_range_beats)
                    f_value = int(((a_end_amt - a_amt) * f_frac) + a_amt)
                else:
                    f_value = int(a_amt)
                if a_add:
                    note.velocity += f_value
                else:
                    note.velocity = f_value
                if note.velocity > 127:
                    note.velocity = 127
                elif note.velocity < 1:
                    note.velocity = 1

    def quantize(self, a_beat_frac, a_events_move_with_item=False,
                 a_notes=None, a_selected_only=False, a_index=0):
        f_notes = []
        f_ccs = []
        f_pbs = []

        f_result = []

        if a_notes is None:
            f_notes = self.notes
            f_ccs = self.ccs
            f_pbs = self.pitchbends
        else:
            for i in range(len(a_notes)):
                for f_note in self.notes:
                    if f_note == a_notes[i]:
                        if a_events_move_with_item:
                            f_start = f_note.start
                            f_end = f_note.start + f_note.length
                            for f_cc in self.ccs:
                                if f_cc.start >= f_start and \
                                f_cc.start <= f_end:
                                    f_ccs.append(f_cc)
                            for f_pb in self.pitchbends:
                                if f_pb.start >= f_start and \
                                f_pb.start <= f_end:
                                    f_pbs.append(f_pb)
                        f_notes.append(f_note)
                        break

        f_quantized_value = bar_frac_text_to_float(a_beat_frac)
        f_quantize_multiple = 1.0 / f_quantized_value

        for note in f_notes:
            if a_selected_only and not note.is_selected:
                continue
            f_new_start = round(note.start *
                f_quantize_multiple) * f_quantized_value
            note.start = f_new_start
            shift_adjust = note.start - f_new_start
            f_new_length = round(note.length *
                f_quantize_multiple) * f_quantized_value
            if f_new_length == 0.0:
                f_new_length = f_quantized_value
            note.set_length(f_new_length)
            f_result.append("{}|{}".format(a_index, note))

        self.fix_overlaps()

        if a_events_move_with_item:
            for cc in f_ccs:
                cc.start -= shift_adjust
            for pb in f_pbs:
                pb.start -= shift_adjust

        return f_result

    def transpose(self, a_semitones, a_octave=0, a_notes=None,
                  a_selected_only=False, a_duplicate=False, a_index=0):
        f_total = a_semitones + (a_octave * 12)
        f_notes = []
        f_result = []

        if a_notes is None:
            f_notes = self.notes
        else:
            for i in range(len(a_notes)):
                for f_note in self.notes:
                    if f_note == a_notes[i]:
                        f_notes.append(f_note)
                        break
        if a_duplicate:
            f_duplicates = []
        for note in f_notes:
            if a_selected_only and not note.is_selected:
                continue
            if a_duplicate:
                f_duplicates.append(pydaw_note.from_str(str(note)))
            note.note_num += f_total
            note.note_num = pydaw_clip_value(note.note_num, 0, 120)
            if note.note_num < 0:
                note.note_num = 0
            elif note.note_num > 127:
                note.note_num = 127
            f_result.append("{}|{}".format(a_index, note))
        if a_duplicate:
            self.notes += f_duplicates
            self.notes.sort()
        return f_result

    def fix_overlaps(self):
        """ Truncate the lengths of any notes that overlap
            the start of another note
        """
        f_to_delete = []
        for f_note in self.notes:
            if f_note not in f_to_delete:
                for f_note2 in self.notes:
                    if f_note != f_note2 and f_note2 not in f_to_delete:
                        if f_note.note_num == f_note2.note_num:
                            if f_note2.start == f_note.start:
                                if f_note2.length == f_note.length:
                                    f_to_delete.append(f_note2)
                                elif f_note2.length > f_note.length:
                                    f_note2.length = \
                                        f_note2.length - f_note.length
                                    f_note2.start = f_note.end
                                    f_note2.set_end()
                                else:
                                    f_note.length = \
                                        f_note.length - f_note2.length
                                    f_note.start = f_note2.end
                                    f_note.set_end()
                            elif f_note2.start > f_note.start:
                                if f_note.end > f_note2.start:
                                    f_note.length = \
                                        f_note2.start - f_note.start
                                    f_note.set_end()
        for f_note in self.notes:
            if f_note.length < pydaw_min_note_length:
                f_to_delete.append(f_note)
        for f_note in f_to_delete:
            self.notes.remove(f_note)

    def get_next_default_note(self):
        pass

    def add_cc(self, a_cc):
        if a_cc in self.ccs:
            return False
        self.ccs.append(a_cc)
        self.ccs.sort()
        return True

    def remove_cc(self, a_cc):
        self.ccs.remove(a_cc)

    def remove_cc_range(self, a_cc_num, a_start_beat=0.0, a_end_beat=4.0):
        """ Delete all pitchbends greater than a_start_beat
            and less than a_end_beat
        """
        f_ccs_to_delete = []
        for cc in self.ccs:
            if cc.cc_num == a_cc_num and \
            cc.start >= a_start_beat and \
            cc.start <= a_end_beat:
                f_ccs_to_delete.append(cc)
        for cc in f_ccs_to_delete:
            self.remove_cc(cc)

    #TODO:  A maximum number of events per line?
    def draw_cc_line(self, a_cc, a_start, a_start_val,
                     a_end, a_end_val, a_curve=0):
        f_cc = int(a_cc)
        f_start = float(a_start)
        f_start_val = int(a_start_val)
        f_end = float(a_end)
        f_end_val = int(a_end_val)
        #Remove any events that would overlap
        self.remove_cc_range(f_cc, f_start, f_end)

        f_start_diff = f_end - f_start
        f_val_diff = abs(f_end_val - f_start_val)
        if f_start_val > f_end_val:
            f_inc = -1
        else:
            f_inc = 1
        f_time_inc = abs(f_start_diff / float(f_val_diff))
        for i in range(0, (f_val_diff + 1)):
            self.ccs.append(pydaw_cc(f_start, f_cc, f_start_val))
            f_start_val += f_inc
            f_start += f_time_inc
        self.ccs.sort()

    def add_pb(self, a_pb):
        if a_pb in self.pitchbends:
            return False
        self.pitchbends.append(a_pb)
        self.pitchbends.sort()
        return True

    def remove_pb(self, a_pb):
        self.pitchbends.remove(a_pb)

    def remove_pb_range(self, a_start_beat=0.0, a_end_beat=4.0):
        """ Delete all pitchbends greater than
            a_start_beat and less than a_end_beat
        """
        f_pbs_to_delete = []
        for pb in self.pitchbends:
            if pb.start >= a_start_beat and \
            pb.start <= a_end_beat:
                f_pbs_to_delete.append(pb)
        for pb in f_pbs_to_delete:
            self.remove_pb(pb)

    def draw_pb_line(self, a_start, a_start_val, a_end, a_end_val, a_curve=0):
        f_start = float(a_start)
        f_start_val = float(a_start_val)
        f_end = float(a_end)
        f_end_val = float(a_end_val)
        #Remove any events that would overlap
        self.remove_pb_range(f_start, f_end)

        f_start_diff = f_end - f_start
        f_val_diff = abs(f_end_val - f_start_val)
        if f_start_val > f_end_val:
            f_inc = -0.025
        else:
            f_inc = 0.025
        f_time_inc = abs(f_start_diff/(float(f_val_diff) * 40.0))
        for i in range(0, int((f_val_diff * 40) + 1)):
            self.pitchbends.append(pydaw_pitchbend(f_start, f_start_val))
            f_start_val += f_inc
            f_start += f_time_inc
        #Ensure that the last value is what the user wanted it to be
        self.pitchbends[(len(self.pitchbends) - 1)].pb_val = f_end_val
        self.pitchbends.sort()

    def get_next_default_cc(self):
        pass

    @staticmethod
    def from_str(a_str, a_uid):
        f_result = pydaw_item(a_uid)
        f_arr = a_str.split("\n")
        for f_event_str in f_arr:
            if f_event_str == pydaw_terminating_char:
                break
            else:
                f_event_arr = f_event_str.split("|")
                if f_event_arr[0] == "n":
                    f_result.add_note(pydaw_note.from_arr(f_event_arr[1:]))
                elif f_event_arr[0] == "c":
                    f_result.add_cc(pydaw_cc.from_arr(f_event_arr[1:]))
                elif f_event_arr[0] == "p":
                    f_result.add_pb(pydaw_pitchbend.from_arr(f_event_arr[1:]))
                elif f_event_arr[0] == "a":
                    f_result.add_item(
                        pydaw_audio_item.from_arr(f_event_arr[1:]))
                elif f_event_arr[0] == "L":
                    f_result.length = int(f_event_arr[1])
                elif f_event_arr[0] == "U":
                    f_result.uid = int(f_event_arr[1])
        return f_result

    def __str__(self):
        f_result = [str(x) for x in
            sorted(self.notes + self.ccs + self.pitchbends)]
        f_result.append("L|{}".format(self.length))
        f_result.append("U|{}".format(self.uid))
        for k, f_item in list(self.items.items()):
            f_result.append("{}|{}".format(k, f_item))
        f_result.append(pydaw_terminating_char)
        return "\n".join(f_result)

    def reorder(self, a_dict):
        for f_item in self.items.values():
            f_item.output_track = a_dict[f_item.output_track]
            if f_item.send1 != -1:
                f_item.send1 = a_dict[f_item.send1]
            if f_item.send2 != -1:
                f_item.send2 = a_dict[f_item.send2]

    def get_next_index(self):
        """ Return the next available index, or -1
            if none are available
        """
        for i in range(MAX_AUDIO_ITEM_COUNT):
            if not i in self.items:
                return i
        return -1

    def split(self, a_index):
        f_region0 = pydaw_audio_region()
        f_region1 = pydaw_audio_region()
        for k, v in list(self.items.items()):
            if v.start_bar >= a_index:
                v.start_bar -= a_index
                f_region1.items[k] = v
            else:
                f_region0.items[k] = v
        return f_region0, f_region1

    def add_item(self, a_index, a_item):
        self.items[int(a_index)] = a_item

    def remove_item(self, a_index):
        self.items.pop(int(a_index))

    def deduplicate_items(self):
        f_to_delete = []
        f_values = []
        for k, v in list(self.items.items()):
            f_str = str(v)
            if f_str in f_values:
                f_to_delete.append(k)
            else:
                f_values.append(f_str)
        for f_key in f_to_delete:
            print("Removing duplicate audio item at {}".format(f_key))
            self.items.pop(f_key)

    def set_region_length(self, a_length):
        """ Remove any items not within the new length,
            or change any end points that are past
            the new end.  Return True if anything changed, otherwise False
        """
        f_to_delete = []
        f_length = int(a_length)
        for k, v in list(self.items.items()):
            if v.start_bar >= f_length:
                f_to_delete.append(k)
                print("Item begins after new region length of "
                      "{}, deleting: {}".format(a_length, v))
        for f_key in f_to_delete:
            self.items.pop(f_key)




class pydaw_audio_item(MkAudioItem):
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

    def clone(self):
        return pydaw_audio_item.from_arr(str(self).strip("\n").split("|"))

    @staticmethod
    def from_str(f_str):
        return pydaw_audio_item.from_arr(f_str.split("|"))

    @staticmethod
    def from_arr(a_arr):
        f_result = pydaw_audio_item(*a_arr)
        return f_result

class pydaw_audio_item_fx_region:
    def __init__(self):
        self.fx_list = {}

    def __str__(self):
        f_result = ""
        for k, v in list(self.fx_list.items()):
            f_result += "{}\n".format(self.get_row_str(k))
        f_result += pydaw_terminating_char
        return f_result

    def get_row_str(self, a_row_index):
        f_result = str(a_row_index)
        for f_item in self.fx_list[int(a_row_index)]:
            f_result += str(f_item)
        return f_result

    def set_row(self, a_row_index, a_fx_list):
        self.fx_list[int(a_row_index)] = a_fx_list

    def clear_row(self, a_row_index):
        self.fx_list.pop(a_row_index)

    def clear_row_if_exists(self, a_row_index):
        if a_row_index in self.fx_list:
            self.fx_list.pop(a_row_index)

    def get_row(self, a_row_index, a_return_none=False):
        if int(a_row_index) in self.fx_list:
            return self.fx_list[int(a_row_index)]
        else:
            # print("Index {} not found in "
            #     "pydaw_audio_item_fx_region".format(a_row_index))
            if a_return_none:
                return None
            else:
                f_result = []
                for f_i in range(8):
                    f_result.append(pydaw_modulex_settings(64, 64, 64, 0))
                return f_result

    @staticmethod
    def from_str(a_str):
        f_result = pydaw_audio_item_fx_region()
        f_arr = str(a_str).split("\n")
        for f_line in f_arr:
            if f_line == pydaw_terminating_char:
                break
            f_items_arr = []
            f_item_index, f_vals = f_line.split("|", 1)
            f_vals_arr = f_vals.split("|")
            for f_i in range(8):
                f_index = f_i * 4
                f_index_end = f_index + 4
                a_knob0, a_knob1, a_knob2, a_type = f_vals_arr[
                    f_index:f_index_end]
                f_items_arr.append(
                    pydaw_modulex_settings(a_knob0, a_knob1, a_knob2, a_type))
            f_result.set_row(f_item_index, f_items_arr)
        return f_result

class pydaw_midi_route:
    def __init__(self, a_on, a_track_num, a_device_name):
        self.on = int(a_on)
        self.track_num = int(a_track_num)
        self.device_name = str(a_device_name)

    def __str__(self):
        return "|".join(
            str(x) for x in (self.on, self.track_num, self.device_name))

class pydaw_midi_routings:
    def __init__(self, a_routings=[]):
        self.routings = a_routings

    def __str__(self):
        return "\n".join(str(x) for x in self.routings + ["\\"])

    @staticmethod
    def from_str(a_str):
        f_routings = []
        for f_line in a_str.split("\n"):
            if f_line == "\\":
                break
            f_routings.append(pydaw_midi_route(*f_line.split("|", 2)))
        return pydaw_midi_routings(f_routings)


class pydaw_transport:
    def __init__(self, a_bpm=128):
        self.bpm = a_bpm

    def __str__(self):
        return "{}\n\\".format(self.bpm)

    @staticmethod
    def from_str(a_str):
        f_str = a_str.split("\n")[0]
        f_arr = f_str.split("|")
        return pydaw_transport(f_arr[0])


class pydaw_midicomp_event:
    def __init__(self, a_arr):
        self.tick = int(a_arr[0])
        self.type = a_arr[1]
        self.ch = int(a_arr[2].split("ch=")[1]) - 1
        self.pitch = int(a_arr[3].split("n=")[1])
        if self.pitch >= 24:
            self.pitch -= 24
        self.vel = int(a_arr[4].split("v=")[1])
        self.length = -1

    def __lt__(self, other):
        return self.tick < other.tick

class pydaw_midi_file_to_items:
    """ Convert the MIDI file at a_file to a dict of pydaw_item's with keys
        in the format (track#, channel#, bar#)"""
    def __init__(self, a_file):
        f_midi_comp = "{}/../libpydaw/midicomp".format(
            os.path.dirname(os.path.abspath(__file__)))
        f_midi_text_arr = subprocess.check_output(
            [f_midi_comp, str(a_file)]).decode("utf-8").split("\n")
        #First fix the lengths of events that have note-off events
        f_note_on_dict = {}
        f_item_list = []
        f_resolution = 96
        for f_line in f_midi_text_arr:
            f_line_arr = f_line.split()
            if len(f_line_arr) <= 1:
                continue
            if f_line_arr[0] == "MFile":
                f_resolution = int(f_line_arr[3])
            elif f_line_arr[1] == "On":
                f_event = pydaw_midicomp_event(f_line_arr)
                if f_event.vel == 0:
                    f_tuple = (f_event.ch, f_event.pitch)
                    if f_tuple in f_note_on_dict:
                        f_note_on_dict[f_tuple].length = \
                            float(f_event.tick -
                            f_note_on_dict[f_tuple].tick) / float(f_resolution)
                        f_note_on_dict.pop(f_tuple)
                else:
                    f_note_on_dict[(f_event.ch, f_event.pitch)] = f_event
                    f_item_list.append(f_event)
            elif f_line_arr[1] == "Off":
                f_event = pydaw_midicomp_event(f_line_arr)
                f_tuple = (f_event.ch, f_event.pitch)
                if f_tuple in f_note_on_dict:
                    f_note_on_dict[f_tuple].length = \
                        float(f_event.tick -
                        f_note_on_dict[f_tuple].tick) / float(f_resolution)
                    print("{} {}".format(f_note_on_dict[f_tuple].tick,
                          f_note_on_dict[f_tuple].length))
                    f_note_on_dict.pop(f_tuple)
                else:
                    print("Error, note-off event does not correspond to a "
                          "note-on event, ignoring event:\n{}".format(
                        f_event))
            else:
                print("Ignoring event: {}".format(f_line))

        self.result_dict = {}
        f_item_list.sort()

        for f_event in f_item_list:
            if f_event.length > 0.0:
                f_velocity = f_event.vel
                f_beat = (float(f_event.tick) / float(f_resolution)) % 4.0
                f_bar = int((int(f_event.tick) // int(f_resolution)) // 4)
                print("f_beat : {} | f_bar : {}".format(f_beat, f_bar))
                f_pitch = f_event.pitch
                f_length = f_event.length
                f_channel = f_event.ch
                f_key = (f_channel, f_bar)
                if not f_key in self.result_dict:
                    self.result_dict[f_key] = pydaw_item()
                f_note = pydaw_note(f_beat, f_length, f_pitch, f_velocity)
                self.result_dict[f_key].add_note(f_note) #, a_check=False)
            else:
                print("Ignoring note event with <= zero length")

        f_min = 0
        f_max = 0

        for k, v in list(self.result_dict.items()):
            if k[1] < f_min:
                f_min = k[1]
            if k[1] > f_max:
                f_max = k[1]

        print("f_min : {} | f_max : {}".format(f_min, f_max))

        self.bar_count = int(f_max - f_min + 1)
        self.bar_offset = int(f_min)
        self.channel_count = self.get_channel_count()

        #Nested dict in format [channel][bar]
        self.track_map = {x:{} for x in range(TRACK_COUNT_ALL)}

        for k, v in list(self.result_dict.items()):
            f_channel, f_bar = k
            self.track_map[f_channel][f_bar - self.bar_offset] = v

    def get_channel_count(self):
        f_result = []
        for k in list(self.result_dict.keys()):
            if k[0] not in f_result:
                f_result.append(k[0])
        return len(f_result)

    def populate_region_from_track_map(self, a_project, a_name, a_index):
        f_actual_track_num = 0
        f_song = a_project.get_song()

        f_region_name = a_project.get_next_default_region_name(a_name)
        f_region_uid = a_project.create_empty_region(f_region_name)
        f_result_region = a_project.get_region_by_uid(f_region_uid)
        f_song.add_region_ref_by_uid(a_index, f_region_uid)
        a_project.save_song(f_song)

        if self.bar_count > MAX_REGION_LENGTH:
            f_result_region.length_bars = MAX_REGION_LENGTH
        else:
            f_result_region.length_bars = self.bar_count
            for f_channel, f_bar_dict in list(self.track_map.items()):
                for f_bar, f_item in list(self.track_map[f_channel].items()):
                    f_this_item_name = "{}-{}-{}".format(
                        a_name, f_channel, f_bar)
                    if a_project.item_exists(f_this_item_name):
                        f_this_item_name = \
                            a_project.get_next_default_item_name(
                            f_this_item_name)
                    f_item_uid = a_project.create_empty_item(f_this_item_name)
                    a_project.save_item_by_uid(f_item_uid, f_item)
                    f_result_region.add_item_ref_by_uid(
                        f_actual_track_num, f_bar, f_item_uid)
                    if f_bar >= MAX_REGION_LENGTH:
                        break
                f_actual_track_num += 1
                if f_actual_track_num >= TRACK_COUNT_ALL:
                    break
        a_project.save_region(f_region_name, f_result_region)
        return True


def envelope_to_automation(self, a_is_cc, a_tempo):
    " In the automation viewer clipboard format "
    f_list = [(x if x > y else y) for x, y in
        zip([abs(x) for x in self.high_peaks[0]],
            [abs(x) for x in reversed(self.low_peaks[0])])]
    f_seconds_per_beat = 60.0 / float(a_tempo)
    f_length_beats = self.length_in_seconds / f_seconds_per_beat
    f_point_count = int(f_length_beats * 16.0)
    print("Resampling {} to {}".format(len(f_list), f_point_count))
    f_result = []
    f_arr = numpy.array(f_list)
    #  Smooth the array by sampling smaller and then larger
    f_arr = scipy.signal.resample(f_arr, int(f_length_beats * 4.0))
    f_arr = scipy.signal.resample(f_arr, f_point_count)
    f_max = numpy.amax(f_arr)
    if f_max > 0.0:
        f_arr *= (1.0 / f_max)
    for f_point, f_pos in zip(f_arr, range(f_arr.shape[0])):
        f_start = (float(f_pos) / float(f_arr.shape[0])) * \
            f_length_beats
        f_index = int(f_start / 4.0)
        f_start = f_start % 4.0
        if a_is_cc:
            f_val = pydaw_clip_value(f_point * 127.0, 0.0, 127.0)
            f_result.append((pydaw_cc(f_start, 0, f_val), f_index))
        else:
            f_val = pydaw_clip_value(f_point, 0.0, 1.0)
            f_result.append((pydaw_pitchbend(f_start, f_val), f_index))
    return f_result

def envelope_to_notes(self, a_tempo):
    " In the piano roll clipboard format "
    f_list = [(x if x > y else y) for x, y in
        zip([abs(x) for x in self.high_peaks[0]],
            [abs(x) for x in reversed(self.low_peaks[0])])]
    f_seconds_per_beat = 60.0 / float(a_tempo)
    f_length_beats = self.length_in_seconds / f_seconds_per_beat
    f_point_count = int(f_length_beats * 16.0)  # 64th note resolution
    print("Resampling {} to {}".format(len(f_list), f_point_count))
    f_result = []
    f_arr = numpy.array(f_list)
    f_arr = scipy.signal.resample(f_arr, f_point_count)
    f_current_note = None
    f_max = numpy.amax(f_arr)
    if f_max > 0.0:
        f_arr *= (1.0 / f_max)
    f_thresh = pydaw_db_to_lin(-24.0)
    f_has_been_less = False

    for f_point, f_pos in zip(f_arr, range(f_arr.shape[0])):
        f_start = (float(f_pos) / float(f_arr.shape[0])) * \
            f_length_beats
        if f_point > f_thresh:
            if not f_current_note:
                f_has_been_less = False
                f_current_note = [f_start, 0.25, f_point, f_point]
            else:
                if f_point > f_current_note[2]:
                    f_current_note[2] = f_point
                else:
                    f_has_been_less = True
                if f_point < f_current_note[3]:
                    f_current_note[3] = f_point
                if f_has_been_less and \
                f_point >= f_current_note[3] * 2.0:
                    f_current_note[1] = f_start - f_current_note[0]
                    f_result.append(f_current_note)
                    f_current_note = [f_start, 0.25, f_point, f_point]
        else:
            if f_current_note:
                f_current_note[1] = f_start - f_current_note[0]
                f_result.append(f_current_note)
                f_current_note = None
    f_result2 = []
    for f_pair in f_result:
        f_index = int(f_pair[0] / 4.0)
        f_start = f_pair[0] % 4.0
        f_vel = pydaw_clip_value((f_pair[2] * 70.0) + 40.0, 1.0, 127.0)
        f_result2.append(
            (str(pydaw_note(f_start, f_pair[1], 60, f_vel)), f_index))
    return f_result2

