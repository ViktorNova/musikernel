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
from libpydaw import *
from libpydaw.pydaw_util import *
import numpy
import scipy
import scipy.signal
import tarfile
import json
import wavefile
import datetime

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

