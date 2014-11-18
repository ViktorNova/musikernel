#!/usr/bin/python3
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

from PyQt4 import QtGui, QtCore
import time
from libpydaw import *
from libpydaw import pydaw_util
from libpydaw.pydaw_util import *
from libpydaw.translate import _
import numpy
import scipy
import scipy.signal
import gc
import sys
import libmk
import tarfile
import json
import wavefile
import datetime

class MkIpc(libmk.AbstractIPC):
    def __init__(self):
        libmk.AbstractIPC.__init__(self, True, "/musikernel/master")

    def stop_server(self):
        print("stop_server called")
        if self.with_osc:
            self.send_configure("exit", "")

    def pydaw_kill_engine(self):
        self.send_configure("abort", "")

    def pydaw_master_vol(self, a_vol):
        self.send_configure("mvol", str(round(a_vol, 8)))

pydaw_folder_audio = "audio/files"
pydaw_folder_samplegraph = "audio/samplegraph"
pydaw_folder_samples = "audio/samples"
pydaw_folder_timestretch = "audio/timestretch"
pydaw_folder_glued = "audio/glued"
pydaw_folder_user = "user"
pydaw_folder_backups = "backups"
pydaw_folder_projects = "projects"
pydaw_folder_plugins = "projects/plugins"
pydaw_file_plugin_uid = "projects/plugin_uid.txt"
pydaw_file_pywavs = "audio/wavs.txt"
pydaw_file_pystretch = "audio/stretch.txt"
pydaw_file_pystretch_map = "audio/stretch_map.txt"
pydaw_file_backups = "backups.json"


class MkProject:
    def __init__(self):
        pass

    def set_project_folders(self, a_project_file):
        #folders
        self.project_folder = os.path.dirname(a_project_file)

        self.audio_folder = "{}/{}".format(
            self.project_folder, pydaw_folder_audio)
        self.audio_tmp_folder = "{}/{}/tmp".format(
            self.project_folder, pydaw_folder_audio)
        self.samplegraph_folder = "{}/{}".format(
            self.project_folder, pydaw_folder_samplegraph)
        self.timestretch_folder = "{}/{}".format(
            self.project_folder, pydaw_folder_timestretch)
        self.glued_folder = "{}/{}".format(
            self.project_folder, pydaw_folder_glued)
        self.user_folder = "{}/{}".format(
            self.project_folder, pydaw_folder_user)
        self.backups_folder = "{}/{}".format(
            self.project_folder, pydaw_folder_backups)
        self.samples_folder = "{}/{}".format(
            self.project_folder, pydaw_folder_samples)
        self.backups_file = "{}/{}".format(
            self.project_folder, pydaw_file_backups)
        self.plugin_pool_folder = "{}/{}".format(
            self.project_folder, pydaw_folder_plugins)
        self.projects_folder = "{}/{}".format(
            self.project_folder, pydaw_folder_projects)
        self.plugin_uid_file = "{}/{}".format(
            self.project_folder, pydaw_file_plugin_uid)
        self.pywavs_file = "{}/{}".format(
            self.project_folder, pydaw_file_pywavs)
        self.pystretch_file = "{}/{}".format(
            self.project_folder, pydaw_file_pystretch)
        self.pystretch_map_file = "{}/{}".format(
            self.project_folder, pydaw_file_pystretch_map)

        self.project_folders = [
            self.audio_folder, self.audio_tmp_folder, self.samples_folder,
            self.samplegraph_folder, self.timestretch_folder,
            self.glued_folder, self.user_folder, self.projects_folder,
            self.backups_folder, self.plugin_pool_folder]

    def get_next_plugin_uid(self):
        if os.path.isfile(self.plugin_uid_file):
            with open(self.plugin_uid_file) as f_handle:
                f_result = int(f_handle.read())
            f_result += 1
            with open(self.plugin_uid_file, "w") as f_handle:
                f_handle.write(str(f_result))
            assert(f_result < 100000)
            return f_result
        else:
            with open(self.plugin_uid_file, "w") as f_handle:
                f_handle.write(str(0))
            return 0

    def create_backup(self, a_name=None):
        f_backup_name = a_name if a_name else \
            datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        with tarfile.open(
        "{}/{}.tar.bz2".format(self.backups_folder, f_backup_name),
        "w:bz2") as f_tar:
            f_tar.add(
                self.projects_folder,
                arcname=os.path.basename(self.projects_folder))
        f_history = self.get_backups_history()
        if f_history:
            f_node = f_history["NODES"]
            for f_name in f_history["CURRENT"].split("/"):
                f_node = f_node[f_name]
            f_node[f_backup_name] = {}
            f_history["CURRENT"] = "{}/{}".format(
                f_history["CURRENT"], f_backup_name)
            self.save_backups_history(f_history)
        else:
            self.save_backups_history(
                {"NODES":{f_backup_name:{}}, "CURRENT":f_backup_name})

    def get_backups_history(self):
        if os.path.exists(self.backups_file):
            with open(self.backups_file) as f_handle:
                return json.load(f_handle)
        else:
            return None

    def save_backups_history(self, a_struct):
        with open(self.backups_file, "w") as f_handle:
            json.dump(
                a_struct, f_handle, sort_keys=True, indent=4,
                separators=(',', ': '))

    def show_project_history(self):
        self.create_backup()
        f_file = "{}/default.musikernel".format(self.project_folder)
        subprocess.Popen([PROJECT_HISTORY_SCRIPT, f_file])

    def get_next_glued_file_name(self):
        while True:
            self.glued_name_index += 1
            f_path = "{}/glued-{}.wav".format(
                self.glued_folder, self.glued_name_index)
            if not os.path.isfile(f_path):
                break
        return f_path

    def open_stretch_dicts(self):
        self.timestretch_cache = {}
        self.timestretch_reverse_lookup = {}

        f_cache_text = pydaw_read_file_text(self.pystretch_file)
        for f_line in f_cache_text.split("\n"):
            if f_line == pydaw_terminating_char:
                break
            f_line_arr = f_line.split("|", 5)
            f_file_path_and_uid = f_line_arr[5].split("|||")
            self.timestretch_cache[
                (int(f_line_arr[0]), float(f_line_arr[1]),
                float(f_line_arr[2]), float(f_line_arr[3]),
                float(f_line_arr[4]),
                f_file_path_and_uid[0])] = int(f_file_path_and_uid[1])

        f_map_text = pydaw_read_file_text(self.pystretch_map_file)
        for f_line in f_map_text.split("\n"):
            if f_line == pydaw_terminating_char:
                break
            f_line_arr = f_line.split("|||")
            self.timestretch_reverse_lookup[f_line_arr[0]] = f_line_arr[1]

    def save_stretch_dicts(self):
        f_stretch_text = ""
        for k, v in list(self.timestretch_cache.items()):
            for f_tuple_val in k:
                f_stretch_text += "{}|".format(f_tuple_val)
            f_stretch_text += "||{}\n".format(v)
        f_stretch_text += pydaw_terminating_char
        self.save_file("", pydaw_file_pystretch, f_stretch_text)

        f_map_text = ""
        for k, v in list(self.timestretch_reverse_lookup.items()):
            f_map_text += "{}|||{}\n".format(k, v)
        f_map_text += pydaw_terminating_char
        self.save_file("", pydaw_file_pystretch_map, f_map_text)

    def get_wavs_dict(self):
        try:
            f_file = open(self.pywavs_file, "r")
        except:
            return pydaw_name_uid_dict()
        f_str = f_file.read()
        f_file.close()
        return pydaw_name_uid_dict.from_str(f_str)

    def save_wavs_dict(self, a_uid_dict):
        pydaw_write_file_text (self.pywavs_file, str(a_uid_dict))
        #self.save_file("", pydaw_file_pywavs, str(a_uid_dict))


    def timestretch_lookup_orig_path(self, a_path):
        if a_path in self.timestretch_reverse_lookup:
            return self.timestretch_reverse_lookup[a_path]
        else:
            return a_path

    def timestretch_audio_item(self, a_audio_item):
        """ Return path, uid for a time-stretched
            audio item and update all project files,
            or None if the UID already exists in the cache
        """
        a_audio_item.timestretch_amt = round(
            a_audio_item.timestretch_amt, 6)
        a_audio_item.pitch_shift = round(a_audio_item.pitch_shift, 6)
        a_audio_item.timestretch_amt_end = round(
            a_audio_item.timestretch_amt_end, 6)
        a_audio_item.pitch_shift_end = round(a_audio_item.pitch_shift_end, 6)

        f_src_path = self.get_wav_name_by_uid(a_audio_item.uid)
        if f_src_path in self.timestretch_reverse_lookup:
            f_src_path = self.timestretch_reverse_lookup[f_src_path]
        else:
            if (a_audio_item.timestretch_amt == 1.0 and \
            a_audio_item.pitch_shift == 0.0 and \
            a_audio_item.timestretch_amt_end == 1.0 and \
            a_audio_item.pitch_shift_end == 0.0) or \
            (a_audio_item.time_stretch_mode == 1 and \
            a_audio_item.pitch_shift == a_audio_item.pitch_shift_end) or \
            (a_audio_item.time_stretch_mode == 2 and \
            a_audio_item.timestretch_amt == a_audio_item.timestretch_amt_end):
                #Don't process if the file is not being stretched/shifted yet
                return None
        f_key = (a_audio_item.time_stretch_mode, a_audio_item.timestretch_amt,
                 a_audio_item.pitch_shift, a_audio_item.timestretch_amt_end,
                 a_audio_item.pitch_shift_end, a_audio_item.crispness,
                 f_src_path)
        if f_key in self.timestretch_cache:
            a_audio_item.uid = self.timestretch_cache[f_key]
            return None
        else:
            f_wavs_dict = self.get_wavs_dict()
            f_uid = f_wavs_dict.gen_file_name_uid()
            f_dest_path = "{}/{}.wav".format(self.timestretch_folder, f_uid)

            f_cmd = None
            if a_audio_item.time_stretch_mode == 1:
                self.this_pydaw_osc.pydaw_pitch_env(
                    f_src_path, f_dest_path, a_audio_item.pitch_shift,
                    a_audio_item.pitch_shift_end)
                #add it to the pool
                self.get_wav_uid_by_name(f_dest_path, a_uid=f_uid)
            elif a_audio_item.time_stretch_mode == 2:
                self.this_pydaw_osc.pydaw_rate_env(
                    f_src_path, f_dest_path, a_audio_item.timestretch_amt,
                    a_audio_item.timestretch_amt_end)
                #add it to the pool
                self.get_wav_uid_by_name(f_dest_path, a_uid=f_uid)
            elif a_audio_item.time_stretch_mode == 3:
                f_cmd = [
                    pydaw_rubberband_util, "-c", str(a_audio_item.crispness),
                    "-t", str(a_audio_item.timestretch_amt), "-p",
                    str(a_audio_item.pitch_shift), "-R", "--pitch-hq",
                    f_src_path, f_dest_path]
            elif a_audio_item.time_stretch_mode == 4:
                f_cmd = [
                    pydaw_rubberband_util, "-F", "-c",
                    str(a_audio_item.crispness), "-t",
                    str(a_audio_item.timestretch_amt), "-p",
                    str(a_audio_item.pitch_shift), "-R", "--pitch-hq",
                    f_src_path, f_dest_path]
            elif a_audio_item.time_stretch_mode == 5:
                f_cmd = [
                    pydaw_sbsms_util, f_src_path, f_dest_path,
                    str(1.0 / a_audio_item.timestretch_amt),
                    str(1.0 / a_audio_item.timestretch_amt_end),
                    str(a_audio_item.pitch_shift),
                    str(a_audio_item.pitch_shift_end) ]
            elif a_audio_item.time_stretch_mode == 6:
                if a_audio_item.pitch_shift != 0.0:
                    f_cmd = [pydaw_paulstretch_util,
                             "-s", str(a_audio_item.timestretch_amt), "-p",
                             str(a_audio_item.pitch_shift),
                             f_src_path, f_dest_path ]
                else:
                    f_cmd = [pydaw_paulstretch_util,
                             "-s", str(a_audio_item.timestretch_amt),
                             f_src_path, f_dest_path ]

            self.timestretch_cache[f_key] = f_uid
            self.timestretch_reverse_lookup[f_dest_path] = f_src_path
            a_audio_item.uid = self.timestretch_cache[f_key]

            if f_cmd is not None:
                print("Running {}".format(" ".join(f_cmd)))
                f_proc = subprocess.Popen(f_cmd)
                return f_dest_path, f_uid, f_proc
            else:
                return None

    def timestretch_get_orig_file_uid(self, a_uid):
        """ Return the UID of the original file """
        f_new_path = self.get_wav_path_by_uid(a_uid)
        if f_new_path in self.timestretch_reverse_lookup:
            f_old_path = self.timestretch_reverse_lookup[f_new_path]
            return self.get_wav_uid_by_name(f_old_path)
        else:
            print("\n####\n####\nWARNING:  "
                "timestretch_get_orig_file_uid could not find uid {}"
                "\n####\n####\n".format(a_uid))
            return a_uid


    def get_sample_graph_by_name(self, a_path, a_uid_dict=None, a_cp=True):
        f_uid = self.get_wav_uid_by_name(a_path, a_cp=a_cp)
        return self.get_sample_graph_by_uid(f_uid)

    def get_sample_graph_by_uid(self, a_uid):
        f_pygraph_file = "{}/{}".format(self.samplegraph_folder, a_uid)
        f_result = pydaw_sample_graph.create(
            f_pygraph_file, self.samples_folder)
        if not f_result.is_valid(): # or not f_result.check_mtime():
            print("\n\nNot valid, or else mtime is newer than graph time, "
                  "deleting sample graph...\n")
            pydaw_remove_item_from_sg_cache(f_pygraph_file)
            self.create_sample_graph(self.get_wav_path_by_uid(a_uid), a_uid)
            return pydaw_sample_graph.create(
                f_pygraph_file, self.samples_folder)
        else:
            return f_result

    def delete_sample_graph_by_name(self, a_path):
        f_uid = self.get_wav_uid_by_name(a_path, a_cp=False)
        self.delete_sample_graph_by_uid(f_uid)

    def delete_sample_graph_by_uid(self, a_uid):
        f_pygraph_file = "{}/{}".format(self.samplegraph_folder, a_uid)
        pydaw_remove_item_from_sg_cache(f_pygraph_file)

    def get_wav_uid_by_name(self, a_path, a_uid_dict=None,
                            a_uid=None, a_cp=True):
        """ Return the UID from the wav pool, or add to the
            pool if it does not exist
        """
        if a_uid_dict is None:
            f_uid_dict = self.get_wavs_dict()
        else:
            f_uid_dict = a_uid_dict
        f_path = str(a_path).replace("//", "/")
        if a_cp:
            self.cp_audio_file_to_cache(f_path)
        if f_uid_dict.name_exists(f_path):
            return f_uid_dict.get_uid_by_name(f_path)
        else:
            f_uid = f_uid_dict.add_new_item(f_path, a_uid)
            self.create_sample_graph(f_path, f_uid)
            self.save_wavs_dict(f_uid_dict)
            return f_uid

    def cp_audio_file_to_cache(self, a_file):
        if a_file in self.cached_audio_files:
            return
        f_cp_path = "{}{}".format(self.samples_folder, a_file)
        f_cp_dir = os.path.dirname(f_cp_path)
        if not os.path.isdir(f_cp_dir):
            os.makedirs(f_cp_dir)
        if not os.path.isfile(f_cp_path):
            f_cmd = "cp -f '{}' '{}'".format(a_file, f_cp_path)
            print(f_cmd)
            os.system(f_cmd)
        self.cached_audio_files.append(a_file)

    def get_wav_name_by_uid(self, a_uid, a_uid_dict=None):
        """ Return the UID from the wav pool, or add to the
            pool if it does not exist
        """
        if a_uid_dict is None:
            f_uid_dict = self.get_wavs_dict()
        else:
            f_uid_dict = a_uid_dict
        if f_uid_dict.uid_exists(a_uid):
            return f_uid_dict.get_name_by_uid(a_uid)
        else:
            raise Exception

    def get_wav_path_by_uid(self, a_uid):
        f_uid_dict = self.get_wavs_dict()
        return f_uid_dict.get_name_by_uid(a_uid)

    def create_sample_graph(self, a_path, a_uid):
        f_uid = int(a_uid)
        f_sample_dir_path = "{}{}".format(self.samples_folder, a_path)
        if os.path.isfile(a_path):
            f_path = a_path
        elif os.path.isfile(f_sample_dir_path):
            f_path = f_sample_dir_path
        else:
            raise Exception("Cannot create sample graph, the "
                "following do not exist:\n{}\n{}\n".format(
                a_path, f_sample_dir_path))

        # TODO:  This algorithm is somewhat screwed up in the C code,
        #  and this is a one-to-one port.  The f_peak_count and so on
        #  are not consistent with length, need to fix it.
        with wavefile.WaveReader(f_path) as f_reader:
            f_result = "meta|filename|{}\n".format(f_path)
            f_ts = int(datetime.datetime.now().strftime("%s"))
            f_result += "meta|timestamp|{}\n".format(f_ts)
            f_result += "meta|channels|{}\n".format(f_reader.channels)
            f_result += "meta|frame_count|{}\n".format(f_reader.frames)
            f_result += "meta|sample_rate|{}\n".format(
                int(f_reader.samplerate))
            f_length = float(f_reader.frames) / float(f_reader.samplerate)
            f_length = round(f_length, 6)
            f_result += "meta|length|{}\n".format(f_length)
            f_peak_count = int(f_length * 32.0)
            f_points = []
            f_count = 0
            for f_chunk in f_reader.read_iter(size=f_peak_count * 50):
                for f_i2 in range(50):
                    f_pos = f_i2 * f_peak_count
                    f_break = False
                    for f_i in range(f_chunk.shape[0]):
                        f_frame = f_chunk[f_i][f_pos:f_pos+f_peak_count]
                        if not len(f_frame):
                            f_break = True
                            continue
                        f_high = -1.0
                        f_low = 1.0
                        for f_i2 in range(0, f_frame.shape[0], 10):
                            f_val = f_frame[f_i2]
                            if f_val > f_high:
                                f_high = f_val
                            elif f_val < f_low:
                                f_low = f_val
                        f_high = round(float(f_high), 6)
                        f_points.append("p|{}|h|{}".format(f_i, f_high))
                        f_low = round(float(f_low), 6)
                        f_points.append("p|{}|l|{}".format(f_i, f_low))
                    f_count += 1
                    if f_break:
                        break
            f_result += "\n".join(f_points)
            f_result += "\nmeta|count|{}\n\\".format(f_count)
        self.this_pydaw_osc.pydaw_add_to_wav_pool(f_path, f_uid)
        f_pygraph_file = "{}/{}".format(self.samplegraph_folder, f_uid)
        with open(f_pygraph_file, "w") as f_handle:
            f_handle.write(f_result)


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

#From old sample_graph..py
pydaw_audio_item_scene_height = 1200.0
pydaw_audio_item_scene_width = 6000.0
pydaw_audio_item_scene_rect = QtCore.QRectF(
    0.0, 0.0, pydaw_audio_item_scene_width, pydaw_audio_item_scene_height)

pydaw_audio_item_scene_gradient = QtGui.QLinearGradient(0, 0, 0, 1200)
pydaw_audio_item_scene_gradient.setColorAt(
    0.0, QtGui.QColor.fromRgb(60, 60, 60, 120))
pydaw_audio_item_scene_gradient.setColorAt(
    1.0, QtGui.QColor.fromRgb(30, 30, 30, 120))

pydaw_audio_item_editor_gradient = QtGui.QLinearGradient(0, 0, 0, 1200)
pydaw_audio_item_editor_gradient.setColorAt(
    0.0, QtGui.QColor.fromRgb(190, 192, 123, 120))
pydaw_audio_item_editor_gradient.setColorAt(
    1.0, QtGui.QColor.fromRgb(130, 130, 100, 120))
#end from sample_graph.py

def pydaw_clear_sample_graph_cache():
    global global_sample_graph_cache
    global_sample_graph_cache = {}

def pydaw_remove_item_from_sg_cache(a_path):
    global global_sample_graph_cache
    if os.path.exists(a_path):
        os.system("rm -f '{}'".format(a_path))
    if a_path in global_sample_graph_cache:
        global_sample_graph_cache.pop(a_path)
    else:
        print("\n\npydaw_remove_item_from_sg_cache: {} "
            "not found.\n\n".format(a_path))

global_sample_graph_cache = {}

class pydaw_sample_graph:
    @staticmethod
    def create(a_file_name, a_sample_dir):
        """ Used to instantiate a pydaw_sample_graph, but
            grabs from the cache if it already exists...
            Prefer this over directly instantiating.
        """
        f_file_name = str(a_file_name)
        global global_sample_graph_cache
        if f_file_name in global_sample_graph_cache:
            return global_sample_graph_cache[f_file_name]
        else:
            f_result = pydaw_sample_graph(f_file_name, a_sample_dir)
            global_sample_graph_cache[f_file_name] = f_result
            return f_result

    def __init__(self, a_file_name, a_sample_dir):
        """
        a_file_name:  The full path to /.../sample_graphs/uid
        a_sample_dir:  The project's sample dir
        """
        self.sample_graph_cache = None
        f_file_name = str(a_file_name)
        self._file = None
        self.sample_dir = str(a_sample_dir)
        self.sample_dir_file = None
        self.timestamp = None
        self.channels = None
        self.high_peaks = ([],[])
        self.low_peaks = ([],[])
        self.count = None
        self.length_in_seconds = None
        self.sample_rate = None
        self.frame_count = None
        self.peak = 0.0

        if not os.path.isfile(f_file_name):
            return

        try:
            f_file = open(f_file_name, "r")
        except:
            return

        f_line_arr = f_file.readlines()
        f_file.close()
        for f_line in f_line_arr:
            f_line_arr = f_line.split("|")
            if f_line_arr[0] == "\\":
                break
            elif f_line_arr[0] == "meta":
                if f_line_arr[1] == "filename":
                    #Why does this have a newline on the end???
                    self._file = str(f_line_arr[2]).strip("\n")
                    self.sample_dir_file = "{}{}".format(
                        self.sample_dir, self._file)
                elif f_line_arr[1] == "timestamp":
                    self.timestamp = int(f_line_arr[2])
                elif f_line_arr[1] == "channels":
                    self.channels = int(f_line_arr[2])
                elif f_line_arr[1] == "count":
                    self.count = int(f_line_arr[2])
                elif f_line_arr[1] == "length":
                    self.length_in_seconds = float(f_line_arr[2])
                elif f_line_arr[1] == "frame_count":
                    self.frame_count = int(f_line_arr[2])
                elif f_line_arr[1] == "sample_rate":
                    self.sample_rate = int(f_line_arr[2])
            elif f_line_arr[0] == "p":
                f_p_val = float(f_line_arr[3])
                f_abs_p_val = abs(f_p_val)
                if f_abs_p_val > self.peak:
                    self.peak = f_abs_p_val
                if f_p_val > 1.0:
                    f_p_val = 1.0
                elif f_p_val < -1.0:
                    f_p_val = -1.0
                if f_line_arr[2] == "h":
                    self.high_peaks[int(f_line_arr[1])].append(f_p_val)
                elif f_line_arr[2] == "l":
                    self.low_peaks[int(f_line_arr[1])].append(f_p_val)
                else:
                    print("Invalid sample_graph [2] value " + f_line_arr[2])
        for f_list in self.low_peaks:
            f_list.reverse()

    def is_valid(self):
        if (self._file is None):
            print("\n\npydaw_sample_graph.is_valid() "
                "self._file is None {}\n".format(self._file))
            return False
        if self.timestamp is None:
            print("\n\npydaw_sample_graph.is_valid() "
                "self.timestamp is None {}\n".format(self._file))
            return False
        if self.channels is None:
            print("\n\npydaw_sample_graph.is_valid() "
                "self.channels is None {}\n".format(self._file))
            return False
        if self.frame_count is None:
            print("\n\npydaw_sample_graph.is_valid() "
                "self.frame_count is None {}\n".format(self._file))
            return False
        if self.sample_rate is None:
            print("\n\npydaw_sample_graph.is_valid() "
                "self.sample_rate is None {}\n".format(self._file))
            return False
        return True

    def normalize(self, a_db=0.0):
        if self.peak == 0.0:
            return 0.0
        f_norm_lin = pydaw_db_to_lin(a_db)
        f_diff = f_norm_lin / self.peak
        f_result = int(pydaw_lin_to_db(f_diff))
        f_result = pydaw_clip_value(f_result, -24, 24)
        return f_result

    def create_sample_graph(self, a_for_scene=False):
        if self.sample_graph_cache is None:
            if self.length_in_seconds > 0.5:
                if a_for_scene:
                    f_width_inc = pydaw_audio_item_scene_width / self.count
                    f_section = \
                        pydaw_audio_item_scene_height / float(self.channels)
                else:
                    f_width_inc = 98.0 / self.count
                    f_section = 100.0 / float(self.channels)
                f_section_div2 = f_section * 0.5

                f_paths = []

                for f_i in range(self.channels):
                    f_result = QtGui.QPainterPath()
                    f_width_pos = 1.0
                    f_result.moveTo(f_width_pos, f_section_div2)
                    for f_peak in self.high_peaks[f_i]:
                        f_peak_clipped = pydaw_clip_value(f_peak, 0.01, 0.99)
                        f_result.lineTo(f_width_pos, f_section_div2 -
                            (f_peak_clipped * f_section_div2))
                        f_width_pos += f_width_inc
                    for f_peak in self.low_peaks[f_i]:
                        f_peak_clipped = pydaw_clip_value(f_peak, -0.99, -0.01)
                        f_result.lineTo(f_width_pos, (f_peak_clipped * -1.0 *
                            f_section_div2) + f_section_div2)
                        f_width_pos -= f_width_inc
                    f_result.closeSubpath()
                    f_paths.append(f_result)
                self.sample_graph_cache = f_paths
            else:
                f_width_inc = pydaw_audio_item_scene_width / self.count
                f_section = \
                    pydaw_audio_item_scene_height / float(self.channels)
                f_section_div2 = f_section * 0.5
                f_paths = []

                for f_i in range(self.channels):
                    f_result = QtGui.QPainterPath()
                    f_width_pos = 1.0
                    f_result.moveTo(f_width_pos, f_section_div2)
                    for f_i2 in range(len(self.high_peaks[f_i])):
                        f_peak = self.high_peaks[f_i][f_i2]
                        f_result.lineTo(
                            f_width_pos, f_section_div2 -
                            (f_peak * f_section_div2))
                        f_width_pos += f_width_inc
                    f_paths.append(f_result)
                self.sample_graph_cache = f_paths
        return self.sample_graph_cache

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

    def check_mtime(self):
        """ Returns False if the sample graph is older than
            the file modified time

            UPDATE:  Now obsolete, will require some fixing if used again...
        """
        try:
            if os.path.isfile(self._file):
                f_timestamp = int(os.path.getmtime(self._file))
            elif os.path.isfile(self.sample_dir_file):
                #f_timestamp = int(os.path.getmtime(self.sample_dir_file))
                return True
            else:
                raise Exception("Neither original nor cached file exists.")
            return self.timestamp > f_timestamp
        except Exception as f_ex:
            print("\n\nError getting mtime: \n{}\n\n".format(f_ex.message))
            return False


class transport_widget:
    def __init__(self):
        self.suppress_osc = True
        self.is_recording = False
        self.is_playing = False
        self.start_region = 0
        self.last_bar = 0
        self.last_open_dir = global_home
        self.transport = pydaw_transport()
        self.group_box = QtGui.QGroupBox()
        self.group_box.setObjectName("transport_panel")
        self.vlayout = QtGui.QVBoxLayout()
        self.group_box.setLayout(self.vlayout)
        self.hlayout1 = QtGui.QHBoxLayout()
        self.vlayout.addLayout(self.hlayout1)
        self.play_button = QtGui.QRadioButton()
        self.play_button.setObjectName("play_button")
        self.play_button.clicked.connect(self.on_play)
        self.hlayout1.addWidget(self.play_button)
        self.stop_button = QtGui.QRadioButton()
        self.stop_button.setChecked(True)
        self.stop_button.setObjectName("stop_button")
        self.stop_button.clicked.connect(self.on_stop)
        self.hlayout1.addWidget(self.stop_button)
        self.rec_button = QtGui.QRadioButton()
        self.rec_button.setObjectName("rec_button")
        self.rec_button.clicked.connect(self.on_rec)
        self.hlayout1.addWidget(self.rec_button)
        self.grid_layout1 = QtGui.QGridLayout()
        self.hlayout1.addLayout(self.grid_layout1)

        f_time_label = QtGui.QLabel(_("Time"))
        f_time_label.setAlignment(QtCore.Qt.AlignCenter)
        self.grid_layout1.addWidget(f_time_label, 0, 27)
        self.time_label = QtGui.QLabel(_("0:00"))
        self.time_label.setMinimumWidth(90)
        self.time_label.setAlignment(QtCore.Qt.AlignCenter)
        self.grid_layout1.addWidget(self.time_label, 1, 27)

        self.menu_button = QtGui.QPushButton(_("Menu"))
        self.grid_layout1.addWidget(self.menu_button, 1, 50)
        self.panic_button = QtGui.QPushButton(_("Panic"))
        self.panic_button.pressed.connect(self.on_panic)
        self.grid_layout1.addWidget(self.panic_button, 0, 50)
        self.master_vol_knob = pydaw_widgets.pydaw_pixmap_knob(60, -480, 0)
        self.hlayout1.addWidget(self.master_vol_knob)
        self.master_vol_knob.valueChanged.connect(self.master_vol_changed)
        self.master_vol_knob.sliderReleased.connect(self.master_vol_released)
        self.last_region_num = -99
        self.suppress_osc = False

    def master_vol_released(self):
        pydaw_util.set_file_setting(
            "master_vol", self.master_vol_knob.value())

    def load_master_vol(self):
        self.master_vol_knob.setValue(
            pydaw_util.get_file_setting("master_vol", int, 0))

    def master_vol_changed(self, a_val):
        if a_val == 0:
            f_result = 1.0
        else:
            f_result = pydaw_util.pydaw_db_to_lin(float(a_val) * 0.1)
        libmk.IPC.pydaw_master_vol(f_result)

    def set_time(self, a_text):
        self.time_label.setText(a_text)

    def on_spacebar(self):
        if self.is_playing or self.is_recording:
            self.stop_button.click()
        else:
            self.play_button.click()

    def on_play(self):
        if self.is_recording:
            self.rec_button.setChecked(True)
            return
        libmk.IS_PLAYING = True
        self.is_playing = True
        MAIN_WINDOW.current_module.TRANSPORT.on_play()
        self.menu_button.setEnabled(False)

    def on_ready(self):
        self.master_vol_changed(self.master_vol_knob.value())

    def on_stop(self):
        if not self.is_playing and not self.is_recording:
            return
        libmk.IS_PLAYING = False
        MAIN_WINDOW.current_module.TRANSPORT.on_stop()
        self.is_playing = False
        self.menu_button.setEnabled(True)
        time.sleep(0.1)

    def on_rec(self):
        if self.is_playing:
            self.play_button.setChecked(True)
            return
        if self.is_recording:
            return
        libmk.IS_PLAYING = True
        self.is_recording = True
        MAIN_WINDOW.current_module.TRANSPORT.on_rec()
        self.menu_button.setEnabled(False)

    def open_transport(self, a_notify_osc=False):
        if not a_notify_osc:
            self.suppress_osc = True
        self.suppress_osc = False
        self.load_master_vol()

    def on_panic(self):
        MAIN_WINDOW.current_module.TRANSPORT.on_panic()

    def set_tooltips(self, a_enabled):
        if a_enabled:
            self.panic_button.setToolTip(
                _("Panic button:   Sends a note-off signal on every "
                "note to every instrument\nYou can also use CTRL+P"))
            self.group_box.setToolTip(
                libpydaw.strings.transport)
        else:
            self.panic_button.setToolTip("")
            self.group_box.setToolTip("")


class MkMainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        libmk.MAIN_WINDOW = self
        try:
            libmk.OSC = liblo.Address(19271)
        except liblo.AddressError as err:
            print((str(err)))
            sys.exit()
        except:
            print("Unable to start OSC with {}".format(19271))
            libmk.OSC = None
        libmk.IPC = MkIpc()
        libmk.TRANSPORT = transport_widget()
        self.setObjectName("mainwindow")
        self.setObjectName("plugin_ui")
        self.setMinimumSize(500, 500)
        self.widget = QtGui.QWidget()
        self.widget.setObjectName("plugin_ui")
        self.setCentralWidget(self.widget)
        self.main_layout = QtGui.QVBoxLayout(self.widget)
        self.main_layout.setMargin(0)
        self.transport_splitter = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.main_layout.addWidget(self.transport_splitter)

        self.transport_widget = QtGui.QWidget()
        self.transport_hlayout = QtGui.QHBoxLayout(self.transport_widget)
        self.transport_hlayout.setMargin(2)
        self.transport_splitter.addWidget(self.transport_widget)
        self.transport_widget.setSizePolicy(
            QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)

        self.transport_hlayout.addWidget(
            libmk.TRANSPORT.group_box, alignment=QtCore.Qt.AlignLeft)

        import edmnext

        self.transport_hlayout.addWidget(
            edmnext.TRANSPORT.group_box, alignment=QtCore.Qt.AlignLeft)

        self.transport_hlayout.addItem(QtGui.QSpacerItem(
            1, 1, QtGui.QSizePolicy.Expanding))

        self.edm_next_module = edmnext
        self.edm_next_window = edmnext.MAIN_WINDOW
        self.current_module = self.edm_next_module
        self.current_window = self.edm_next_window

        self.transport_splitter.addWidget(self.edm_next_window)

        self.host_windows = (self.edm_next_window,)

        self.ignore_close_event = True

                #The menus
        self.menu_bar = QtGui.QMenu(self)
        # Dirty hack, rather than moving the methods to the transport
        libmk.TRANSPORT.menu_button.setMenu(self.menu_bar)
        self.menu_file = self.menu_bar.addMenu(_("File"))

        self.new_action = self.menu_file.addAction(_("New..."))
        self.new_action.triggered.connect(self.on_new)
        self.new_action.setShortcut(QtGui.QKeySequence.New)

        self.open_action = self.menu_file.addAction(_("Open..."))
        self.open_action.triggered.connect(self.on_open)
        self.open_action.setShortcut(QtGui.QKeySequence.Open)

        self.save_action = self.menu_file.addAction(
            _("Save (projects are automatically saved, "
            "this creates a timestamped backup)"))
        self.save_action.triggered.connect(self.on_save)
        self.save_action.setShortcut(QtGui.QKeySequence.Save)

        self.save_as_action = self.menu_file.addAction(
            _("Save As...(this creates a named backup)"))
        self.save_as_action.triggered.connect(self.on_save_as)
        self.save_as_action.setShortcut(QtGui.QKeySequence.SaveAs)

        self.save_copy_action = self.menu_file.addAction(
            _("Save Copy...("
            "This creates a full copy of the project directory)"))
        self.save_copy_action.triggered.connect(self.on_save_copy)

        self.menu_file.addSeparator()

        self.project_history_action = self.menu_file.addAction(
            _("Project History...("
            "This shows a tree of all backups)"))
        self.project_history_action.triggered.connect(self.on_project_history)

        self.menu_file.addSeparator()

        self.offline_render_action = self.menu_file.addAction(
            _("Offline Render..."))
        self.offline_render_action.triggered.connect(self.on_offline_render)

        self.audio_device_action = self.menu_file.addAction(
            _("Hardware Settings..."))
        self.audio_device_action.triggered.connect(
            self.on_change_audio_settings)
        self.menu_file.addSeparator()

        self.kill_engine_action = self.menu_file.addAction(
            _("Kill Audio Engine"))
        self.kill_engine_action.triggered.connect(self.on_kill_engine)
        self.menu_file.addSeparator()

        self.quit_action = self.menu_file.addAction(_("Quit"))
        self.quit_action.triggered.connect(self.close)
        self.quit_action.setShortcut(QtGui.QKeySequence.Quit)

        self.menu_edit = self.menu_bar.addMenu(_("Edit"))

        self.undo_action = self.menu_edit.addAction(_("Undo"))
        self.undo_action.triggered.connect(self.on_undo)
        self.undo_action.setShortcut(QtGui.QKeySequence.Undo)

        self.redo_action = self.menu_edit.addAction(_("Redo"))
        self.redo_action.triggered.connect(self.on_redo)
        self.redo_action.setShortcut(QtGui.QKeySequence.Redo)

        self.menu_edit.addSeparator()

        self.undo_history_action = self.menu_edit.addAction(
            _("Undo History..."))
        self.undo_history_action.triggered.connect(self.on_undo_history)

        self.verify_history_action = self.menu_edit.addAction(
            _("Verify History DB..."))
        self.verify_history_action.triggered.connect(self.on_verify_history)

        self.menu_appearance = self.menu_bar.addMenu(_("Appearance"))

        self.collapse_splitters_action = self.menu_appearance.addAction(
            _("Collapse Transport and Song Editor"))
        self.collapse_splitters_action.triggered.connect(
            self.on_collapse_splitters)
        self.collapse_splitters_action.setShortcut(
            QtGui.QKeySequence("CTRL+Up"))

        self.restore_splitters_action = self.menu_appearance.addAction(
            _("Restore Transport and Song Editor"))
        self.restore_splitters_action.triggered.connect(
            self.on_restore_splitters)
        self.restore_splitters_action.setShortcut(
            QtGui.QKeySequence("CTRL+Down"))

        self.menu_appearance.addSeparator()

        self.open_theme_action = self.menu_appearance.addAction(
            _("Open Theme..."))
        self.open_theme_action.triggered.connect(self.on_open_theme)

        self.menu_tools = self.menu_bar.addMenu(_("Tools"))

        self.ac_action = self.menu_tools.addAction(_("MP3 Converter..."))
        self.ac_action.triggered.connect(self.mp3_converter_dialog)

        self.ac_action = self.menu_tools.addAction(_("Ogg Converter..."))
        self.ac_action.triggered.connect(self.ogg_converter_dialog)

        self.menu_help = self.menu_bar.addMenu(_("Help"))

        self.troubleshoot_action = self.menu_help.addAction(
            _("Troubleshooting..."))
        self.troubleshoot_action.triggered.connect(self.on_troubleshoot)

        self.version_action = self.menu_help.addAction(_("Version Info..."))
        self.version_action.triggered.connect(self.on_version)

        self.menu_bar.addSeparator()

        self.tooltips_action = self.menu_bar.addAction(_("Show Tooltips"))
        self.tooltips_action.setCheckable(True)
        self.tooltips_action.setChecked(libmk.TOOLTIPS_ENABLED)
        self.tooltips_action.triggered.connect(self.set_tooltips_enabled)

        self.panic_action = QtGui.QAction(self)
        self.addAction(self.panic_action)
        self.panic_action.setShortcut(QtGui.QKeySequence.fromString("CTRL+P"))
        self.panic_action.triggered.connect(libmk.TRANSPORT.on_panic)

        self.spacebar_action = QtGui.QAction(self)
        self.addAction(self.spacebar_action)
        self.spacebar_action.triggered.connect(self.on_spacebar)
        self.spacebar_action.setShortcut(
            QtGui.QKeySequence(QtCore.Qt.Key_Space))

        try:
            self.osc_server = liblo.Server(30321)
        except liblo.ServerError as err:
            print("Error creating OSC server: {}".format(err))
            self.osc_server = None
        if self.osc_server is not None:
            print(self.osc_server.get_url())
            self.osc_server.add_method(
                "musikernel/ui_configure", 's',
                self.edm_next_window.configure_callback)
            self.osc_server.add_method(None, None, self.osc_fallback)
            self.osc_timer = QtCore.QTimer(self)
            self.osc_timer.setSingleShot(False)
            self.osc_timer.timeout.connect(self.osc_time_callback)
            self.osc_timer.start(0)

        self.on_restore_splitters()
        self.show()

    def osc_time_callback(self):
        self.osc_server.recv(1)

    def osc_fallback(self, path, args, types, src):
        print("got unknown message '{}' from '{}'".format(path, src))
        for a, t in zip(args, types):
            print("argument of type '{}': {}".format(t, a))

    def on_new(self):
        if libmk.IS_PLAYING:
            return
        try:
            while True:
                f_file = QtGui.QFileDialog.getSaveFileName(
                    parent=self, caption=_('New Project'),
                    directory="{}/default.{}".format(
                        global_home, global_pydaw_version_string),
                    filter=global_pydaw_file_type_string)
                if not f_file is None and not str(f_file) == "":
                    f_file = str(f_file)
                    if not self.check_for_empty_directory(f_file) or \
                    not self.check_for_rw_perms(f_file):
                        continue
                    if not f_file.endswith("." + global_pydaw_version_string):
                        f_file += "." + global_pydaw_version_string
                    global_new_project(f_file)
                break
        except Exception as ex:
            pydaw_print_generic_exception(ex)

    def on_open(self):
        if libmk.IS_PLAYING:
            return
        try:
            f_file = QtGui.QFileDialog.getOpenFileName(
                parent=self, caption=_('Open Project'),
                directory=global_default_project_folder,
                filter=global_pydaw_file_type_string)
            if f_file is None:
                return
            f_file_str = str(f_file)
            if f_file_str == "":
                return
            if not self.check_for_rw_perms(f_file):
                return
            global_open_project(f_file_str)
        except Exception as ex:
            pydaw_print_generic_exception(ex)

    def on_project_history(self):
        f_result = QtGui.QMessageBox.warning(
            self, _("Warning"), _("This will close the application, "
            "restart the application after you're done with the "
            "project history editor"),
            buttons=QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
        if f_result == QtGui.QMessageBox.Ok:
            PROJECT.show_project_history()
            self.ignore_close_event = False
            self.prepare_to_quit()

    def on_save(self):
        PROJECT.create_backup()

    def on_save_as(self):
        if libmk.IS_PLAYING:
            return
        def ok_handler():
            f_name = str(f_lineedit.text()).strip()
            f_name = f_name.replace("/", "")
            if f_name:
                PROJECT.create_backup(f_name)
                f_window.close()

        f_window = QtGui.QDialog()
        f_window.setWindowTitle(_("Save As..."))
        f_layout = QtGui.QVBoxLayout(f_window)
        f_lineedit = QtGui.QLineEdit()
        f_lineedit.setMinimumWidth(240)
        f_lineedit.setMaxLength(48)
        f_layout.addWidget(f_lineedit)
        f_ok_layout = QtGui.QHBoxLayout()
        f_layout.addLayout(f_ok_layout)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_handler)
        f_ok_layout.addWidget(f_ok_button)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_ok_layout.addWidget(f_cancel_button)
        f_cancel_button.pressed.connect(f_window.close)
        f_window.exec_()

    def on_save_copy(self):
        if libmk.IS_PLAYING:
            return
        try:
            while True:
                f_new_file = QtGui.QFileDialog.getSaveFileName(
                    self, _("Save copy of project as..."),
                    directory="{}/{}.{}".format(global_default_project_folder,
                    PROJECT.project_file, global_pydaw_version_string))
                if not f_new_file is None and not str(f_new_file) == "":
                    f_new_file = str(f_new_file)
                    if not self.check_for_empty_directory(f_new_file) or \
                    not self.check_for_rw_perms(f_new_file):
                        continue
                    if not f_new_file.endswith(
                    ".{}".format(global_pydaw_version_string)):
                        f_new_file += ".{}".format(global_pydaw_version_string)
                    PLUGIN_UI_DICT.close_all_plugin_windows()
                    PROJECT.save_project_as(f_new_file)
                    set_window_title()
                    pydaw_util.set_file_setting("last-project", f_new_file)
                    break
                else:
                    break
        except Exception as ex:
            pydaw_print_generic_exception(ex)


    def prepare_to_quit(self):
        try:
            if self.osc_server is not None:
                self.osc_timer.stop()
                self.osc_server.free()
            libmk.IPC.stop_server()
            for f_host in self.host_windows:
                f_host.prepare_to_quit()
            self.ignore_close_event = False
            libmk.IPC = None
            libmk.OSC = None
            libmk.MAIN_WINDOW = None
            libmk.TRANSPORT = None
            f_quit_timer = QtCore.QTimer(self)
            f_quit_timer.setSingleShot(True)
            f_quit_timer.timeout.connect(self.close)
            f_quit_timer.start(1000)
        except Exception as ex:
            print("Exception thrown while attempting to exit, "
                "forcing MusiKernel to exit")
            print("Exception:  {}".format(ex))
            exit(999)

    def closeEvent(self, event):
        if self.ignore_close_event:
            event.ignore()
            if libmk.IS_PLAYING:
                return
            self.setEnabled(False)
            f_reply = QtGui.QMessageBox.question(
                self, _('Message'), _("Are you sure you want to quit?"),
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel,
                QtGui.QMessageBox.Cancel)
            if f_reply == QtGui.QMessageBox.Cancel:
                self.setEnabled(True)
                return
            else:
                self.prepare_to_quit()
        else:
            event.accept()


    def on_undo_history(self):
        if libmk.IS_PLAYING:
            return
        PROJECT.flush_history()
        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Undo history"))
        f_layout = QtGui.QVBoxLayout()
        f_window.setLayout(f_layout)
        f_widget = pydaw_history_log_widget(
            PROJECT.history, global_ui_refresh_callback)
        f_widget.populate_table()
        f_layout.addWidget(f_widget)
        f_window.setGeometry(
            QtCore.QRect(f_window.x(), f_window.y(), 900, 720))
        f_window.exec_()

    def on_verify_history(self):
        if libmk.IS_PLAYING:
            return
        f_str = PROJECT.verify_history()
        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Verify Project History Database"))
        f_window.setFixedSize(800, 600)
        f_layout = QtGui.QVBoxLayout()
        f_window.setLayout(f_layout)
        f_text = QtGui.QTextEdit(f_str)
        f_text.setReadOnly(True)
        f_layout.addWidget(f_text)
        f_window.exec_()

    def on_change_audio_settings(self):
        f_dialog = pydaw_device_dialog.pydaw_device_dialog(True)
        f_dialog.show_device_dialog(a_notify=True)

    def on_kill_engine(self):
        libmk.IPC.pydaw_kill_engine()

    def on_open_theme(self):
        try:
            f_file = QtGui.QFileDialog.getOpenFileName(self,
                _("Open a theme file"), "{}/lib/{}/themes".format(
                pydaw_util.global_pydaw_install_prefix,
                global_pydaw_version_string), "MusiKernel Style(*.pytheme)")
            if f_file is not None and str(f_file) != "":
                f_file = str(f_file)
                f_style = pydaw_read_file_text(f_file)
                f_dir = os.path.dirname(f_file)
                f_style = pydaw_escape_stylesheet(f_style, f_dir)
                pydaw_write_file_text(global_user_style_file, f_file)
                QtGui.QMessageBox.warning(
                    MAIN_WINDOW, _("Theme Applied..."),
                    _("Please restart MusiKernel to update the UI"))
        except Exception as ex:
            pydaw_print_generic_exception(ex)

    def on_version(self):
        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Version Info"))
        f_window.setFixedSize(420, 150)
        f_layout = QtGui.QVBoxLayout()
        f_window.setLayout(f_layout)
        f_minor_version = pydaw_read_file_text(
            "{}/lib/{}/minor-version.txt".format(
                pydaw_util.global_pydaw_install_prefix,
                global_pydaw_version_string))
        f_version = QtGui.QLabel(
            "{}-{}".format(global_pydaw_version_string, f_minor_version))
        f_version.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        f_layout.addWidget(f_version)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_layout.addWidget(f_ok_button)
        f_ok_button.pressed.connect(f_window.close)
        f_window.exec_()

    def on_troubleshoot(self):
        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Troubleshooting"))
        f_window.setFixedSize(640, 460)
        f_layout = QtGui.QVBoxLayout()
        f_window.setLayout(f_layout)
        f_label = QtGui.QTextEdit(libpydaw.strings.troubleshooting)
        f_label.setReadOnly(True)
        f_layout.addWidget(f_label)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_layout.addWidget(f_ok_button)
        f_ok_button.pressed.connect(f_window.close)
        f_window.exec_()


    def on_spacebar(self):
        libmk.TRANSPORT.on_spacebar()

    def on_collapse_splitters(self):
        #self.song_region_splitter.setSizes([0, 9999])
        self.transport_splitter.setSizes([0, 9999])

    def on_restore_splitters(self):
        #self.song_region_splitter.setSizes([100, 9999])
        self.transport_splitter.setSizes([100, 9999])


    def mp3_converter_dialog(self):
        if pydaw_which("avconv") is None and \
        pydaw_which("ffmpeg") is not None:
            f_avconv = "ffmpeg"
        else:
            f_avconv = "avconv"
        f_lame = "lame"
        for f_app in (f_avconv, f_lame):
            if pydaw_which(f_app) is None:
                QtGui.QMessageBox.warning(self, _("Error"),
                    libpydaw.strings.avconv_error.format(f_app))
                return
        self.audio_converter_dialog("lame", "avconv", "mp3")

    def ogg_converter_dialog(self):
        if pydaw_which("oggenc") is None or \
        pydaw_which("oggdec") is None:
            QtGui.QMessageBox.warning(self, _("Error"),
                _("Error, vorbis-tools are not installed"))
            return
        self.audio_converter_dialog("oggenc", "oggdec", "ogg")

    def audio_converter_dialog(self, a_enc, a_dec, a_label):
        def get_cmd(f_input_file, f_output_file):
            if f_wav_radiobutton.isChecked():
                if a_dec == "avconv" or a_dec == "ffmpeg":
                    f_cmd = [a_dec, "-i", f_input_file, f_output_file]
                elif a_dec == "oggdec":
                    f_cmd = [a_dec, "--output", f_output_file, f_input_file]
            else:
                if a_enc == "oggenc":
                    f_cmd = [a_enc, "-b",
                         "{}k".format(f_mp3_br_combobox.currentText()),
                         "-o", f_output_file, f_input_file]
                elif a_enc == "lame":
                    f_cmd = [a_enc, "-b", str(f_mp3_br_combobox.currentText()),
                         f_input_file, f_output_file]
            return f_cmd

        def ok_handler():
            f_input_file = str(f_name.text())
            f_output_file = str(f_output_name.text())
            if f_input_file == "" or f_output_file == "":
                QtGui.QMessageBox.warning(f_window, _("Error"),
                                          _("File names cannot be empty"))
                return
            if f_batch_checkbox.isChecked():
                if f_wav_radiobutton.isChecked():
                    f_ext = ".{}".format(a_label)
                else:
                    f_ext = ".wav"
                f_ext = f_ext.upper()
                f_list = [x for x in os.listdir(f_input_file)
                    if x.upper().endswith(f_ext)]
                if not f_list:
                    QtGui.QMessageBox.warning(f_window, _("Error"),
                          _("No {} files in {}".format(f_ext, f_input_file)))
                    return
                f_proc_list = []
                for f_file in f_list:
                    f_in = "{}/{}".format(f_input_file, f_file)
                    f_out = "{}/{}{}".format(f_output_file,
                        f_file.rsplit(".", 1)[0], self.ac_ext)
                    f_cmd = get_cmd(f_in, f_out)
                    f_proc = subprocess.Popen(f_cmd)
                    f_proc_list.append((f_proc, f_out))
                for f_proc, f_out in f_proc_list:
                    f_status_label.setText(f_out)
                    QtGui.QApplication.processEvents()
                    f_proc.communicate()
            else:
                f_cmd = get_cmd(f_input_file, f_output_file)
                f_proc = subprocess.Popen(f_cmd)
                f_proc.communicate()
            if f_close_checkbox.isChecked():
                f_window.close()
            QtGui.QMessageBox.warning(self, _("Success"), _("Created file(s)"))

        def cancel_handler():
            f_window.close()

        def set_output_file_name():
            if str(f_output_name.text()) == "":
                f_file = str(f_name.text())
                if f_file:
                    f_file_name = f_file.rsplit('.')[0] + self.ac_ext
                    f_output_name.setText(f_file_name)

        def file_name_select():
            try:
                if not os.path.isdir(self.last_ac_dir):
                    self.last_ac_dir = global_home
                if f_batch_checkbox.isChecked():
                    f_dir = QtGui.QFileDialog.getExistingDirectory(f_window,
                        _("Open Folder"), self.last_ac_dir)
                    if f_dir is None:
                        return
                    f_dir = str(f_dir)
                    if f_dir == "":
                        return
                    f_name.setText(f_dir)
                    self.last_ac_dir = f_dir
                else:
                    f_file_name = QtGui.QFileDialog.getOpenFileName(
                        f_window, _("Select a file name to save to..."),
                        self.last_ac_dir,
                        filter=_("Audio Files {}").format(
                        '(*.wav *.{})'.format(a_label)))
                    if not f_file_name is None and str(f_file_name) != "":
                        f_name.setText(str(f_file_name))
                        self.last_ac_dir = os.path.dirname(f_file_name)
                        if f_file_name.lower().endswith(".{}".format(a_label)):
                            f_wav_radiobutton.setChecked(True)
                        elif f_file_name.lower().endswith(".wav"):
                            f_mp3_radiobutton.setChecked(True)
                        set_output_file_name()
                        self.last_ac_dir = os.path.dirname(f_file_name)
            except Exception as ex:
                pydaw_print_generic_exception(ex)

        def file_name_select_output():
            try:
                if not os.path.isdir(self.last_ac_dir):
                    self.last_ac_dir = global_home
                if f_batch_checkbox.isChecked():
                    f_dir = QtGui.QFileDialog.getExistingDirectory(f_window,
                        _("Open Folder"), self.last_ac_dir)
                    if f_dir is None:
                        return
                    f_dir = str(f_dir)
                    if f_dir == "":
                        return
                    f_output_name.setText(f_dir)
                    self.last_ac_dir = f_dir
                else:
                    f_file_name = QtGui.QFileDialog.getSaveFileName(
                        f_window, _("Select a file name to save to..."),
                        self.last_ac_dir)
                    if not f_file_name is None and str(f_file_name) != "":
                        f_file_name = str(f_file_name)
                        if not f_file_name.endswith(self.ac_ext):
                            f_file_name += self.ac_ext
                        f_output_name.setText(f_file_name)
                        self.last_ac_dir = os.path.dirname(f_file_name)
            except Exception as ex:
                pydaw_print_generic_exception(ex)

        def format_changed(a_val=None):
            if f_wav_radiobutton.isChecked():
                self.ac_ext = ".wav"
            else:
                self.ac_ext = ".{}".format(a_label)
            if not f_batch_checkbox.isChecked():
                f_str = str(f_output_name.text()).strip()
                if f_str != "" and not f_str.endswith(self.ac_ext):
                    f_arr = f_str.rsplit(".")
                    f_output_name.setText(f_arr[0] + self.ac_ext)

        def batch_changed(a_val=None):
            f_name.setText("")
            f_output_name.setText("")

        self.ac_ext = ".wav"
        f_window = QtGui.QDialog(MAIN_WINDOW)

        f_window.setWindowTitle(_("{} Converter".format(a_label)))
        f_layout = QtGui.QGridLayout()
        f_window.setLayout(f_layout)

        f_name = QtGui.QLineEdit()
        f_name.setReadOnly(True)
        f_name.setMinimumWidth(480)
        f_layout.addWidget(QtGui.QLabel(_("Input:")), 0, 0)
        f_layout.addWidget(f_name, 0, 1)
        f_select_file = QtGui.QPushButton(_("Select"))
        f_select_file.pressed.connect(file_name_select)
        f_layout.addWidget(f_select_file, 0, 2)

        f_output_name = QtGui.QLineEdit()
        f_output_name.setReadOnly(True)
        f_output_name.setMinimumWidth(480)
        f_layout.addWidget(QtGui.QLabel(_("Output:")), 1, 0)
        f_layout.addWidget(f_output_name, 1, 1)
        f_select_file_output = QtGui.QPushButton(_("Select"))
        f_select_file_output.pressed.connect(file_name_select_output)
        f_layout.addWidget(f_select_file_output, 1, 2)

        f_layout.addWidget(QtGui.QLabel(_("Convert to:")), 2, 1)
        f_rb_group = QtGui.QButtonGroup()
        f_wav_radiobutton = QtGui.QRadioButton("wav")
        f_wav_radiobutton.setChecked(True)
        f_rb_group.addButton(f_wav_radiobutton)
        f_wav_layout = QtGui.QHBoxLayout()
        f_wav_layout.addWidget(f_wav_radiobutton)
        f_layout.addLayout(f_wav_layout, 3, 1)
        f_wav_radiobutton.toggled.connect(format_changed)

        f_mp3_radiobutton = QtGui.QRadioButton(a_label)
        f_rb_group.addButton(f_mp3_radiobutton)
        f_mp3_layout = QtGui.QHBoxLayout()
        f_mp3_layout.addWidget(f_mp3_radiobutton)
        f_mp3_radiobutton.toggled.connect(format_changed)
        f_mp3_br_combobox = QtGui.QComboBox()
        f_mp3_br_combobox.addItems(["320", "256", "192", "160", "128"])
        f_mp3_layout.addWidget(QtGui.QLabel(_("Bitrate")))
        f_mp3_layout.addWidget(f_mp3_br_combobox)
        f_layout.addLayout(f_mp3_layout, 4, 1)

        f_batch_checkbox = QtGui.QCheckBox(_("Batch convert entire folder?"))
        f_batch_checkbox.stateChanged.connect(batch_changed)
        f_layout.addWidget(f_batch_checkbox, 6, 1)

        f_close_checkbox = QtGui.QCheckBox("Close on finish?")
        f_close_checkbox.setChecked(True)
        f_layout.addWidget(f_close_checkbox, 9, 1)

        f_ok_layout = QtGui.QHBoxLayout()
        f_ok_layout.addItem(
            QtGui.QSpacerItem(
            10, 10, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))
        f_ok = QtGui.QPushButton(_("OK"))
        f_ok.setMinimumWidth(75)
        f_ok.pressed.connect(ok_handler)
        f_ok_layout.addWidget(f_ok)
        f_layout.addLayout(f_ok_layout, 9, 2)
        f_cancel = QtGui.QPushButton(_("Cancel"))
        f_cancel.setMinimumWidth(75)
        f_cancel.pressed.connect(cancel_handler)
        f_ok_layout.addWidget(f_cancel)
        f_status_label = QtGui.QLabel("")
        f_layout.addWidget(f_status_label, 15, 1)
        f_window.exec_()

    def on_offline_render(self):
        self.current_window.on_offline_render()

    def on_undo(self):
        self.current_window.on_undo()

    def on_redo(self):
        self.current_window.on_redo()

    def set_tooltips_enabled(self):
        for f_window in self.host_windows:
            f_window.set_tooltips_enabled(self.tooltips_action.isChecked())



libmk.APP = QtGui.QApplication(sys.argv)

libmk.APP.setWindowIcon(
    QtGui.QIcon("{}/share/pixmaps/{}.png".format(
    pydaw_util.global_pydaw_install_prefix, global_pydaw_version_string)))

libmk.APP.setStyleSheet(global_stylesheet)

QtCore.QTextCodec.setCodecForLocale(QtCore.QTextCodec.codecForName("UTF-8"))

def final_gc():
    """ Brute-force garbage collect all possible objects to
        prevent the infamous PyQt SEGFAULT-on-exit...
    """
    f_last_unreachable = gc.collect()
    if not f_last_unreachable:
        print("Successfully garbage collected all objects")
        return
    for f_i in range(2, 12):
        time.sleep(0.1)
        f_unreachable = gc.collect()
        if f_unreachable == 0:
            print("Successfully garbage collected all objects "
                "in {} iterations".format(f_i))
            return
        elif f_unreachable >= f_last_unreachable:
            break
        else:
            f_last_unreachable = f_unreachable
    print("gc.collect() returned {} unreachable objects "
        "after {} iterations".format(f_unreachable, f_i))

def flush_events():
    for f_i in range(1, 10):
        if libmk.APP.hasPendingEvents():
            libmk.APP.processEvents()
            time.sleep(0.1)
        else:
            print("Successfully processed all pending events "
                "in {} iterations".format(f_i))
            return
    print("Could not process all events")

MAIN_WINDOW = MkMainWindow()
MAIN_WINDOW.setWindowState(QtCore.Qt.WindowMaximized)

libmk.APP.lastWindowClosed.connect(libmk.APP.quit)
libmk.APP.setStyle(QtGui.QStyleFactory.create("Fusion"))
libmk.APP.exec_()
time.sleep(0.6)
flush_events()
libmk.APP.deleteLater()
time.sleep(0.6)
libmk.APP = None
time.sleep(0.6)
final_gc()

