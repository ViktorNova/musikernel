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

import os
import math
from . import pydaw_util
from libpydaw.pydaw_project import pydaw_audio_item_fx, pydaw_folder_plugins
from libpydaw.translate import _
from PyQt4 import QtGui, QtCore
import numpy


KNOB_ARC_GRADIENT = QtGui.QLinearGradient(0.0, 0.0, 90.0, 0.0)
KNOB_ARC_GRADIENT.setColorAt(
    0.0, QtGui.QColor.fromRgb(60, 60, 255, 255))
KNOB_ARC_GRADIENT.setColorAt(
    0.25, QtGui.QColor.fromRgb(255, 120, 0, 255))
KNOB_ARC_GRADIENT.setColorAt(
    0.75, QtGui.QColor.fromRgb(255, 0, 0, 255))
KNOB_ARC_PEN = QtGui.QPen(
    KNOB_ARC_GRADIENT, 5.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap,
    QtCore.Qt.RoundJoin)

class pydaw_plugin_file:
    """ Abstracts an instrument state file.  Plugins are not required
        to implement this and can instead implement their own custom
        state files, but this should be a sane and well tested way
        for most plugins to save their state.
    """
    def __init__(self, a_path=None):
        self.port_dict = {}
        self.configure_dict = {}
        self.cc_map = {}
        if a_path is not None:
            f_text = pydaw_util.pydaw_read_file_text(a_path)
            self.set_from_str(f_text)

    def set_from_str(self, a_str):
        f_line_arr = a_str.split("\n")
        for f_line in f_line_arr:
            if f_line == "\\":
                break
            f_items = f_line.split("|", 1)
            if f_items[0] == 'c':
                f_items2 = f_items[1].split("|", 1)
                self.configure_dict[(f_items2[0])] = f_items2[1]
            elif f_items[0] == 'm':
                f_cc, f_val = f_items[1].split("|", 1)
                self.cc_map[int(f_cc)] = cc_mapping.from_str(f_items[1])
            else:
                self.port_dict[int(f_items[0])] = int(float(f_items[1]))

    @staticmethod
    def from_str(a_str):
        f_result = pydaw_plugin_file()
        f_result.set_from_str(a_str)
        return f_result

    @staticmethod
    def from_dict(a_port_dict, a_configure_dict, a_cc_map_dict):
        f_result = pydaw_plugin_file()
        for k, v in a_port_dict.items():
            f_result.port_dict[int(k)] = v
        for k, v in a_configure_dict.items():
            f_result.configure_dict[k] = v
        for k, v in a_cc_map_dict.items():
            f_result.cc_map[k] = v
        return f_result

    def __str__(self):
        f_result = []
        for k in sorted(self.configure_dict):
            v = self.configure_dict[k]
            f_result.append("|".join(str(x) for x in ("c", k, v)))
        for k in sorted(self.cc_map):
            v = self.cc_map[k]
            f_result.append(str(v))
        for k in sorted(self.port_dict):
            v = self.port_dict[k]
            f_result.append("|".join(str(int(x)) for x in (k, v.get_value())))
        f_result.append("\\")
        return "\n".join(f_result)


class cc_mapping:
    def __init__(self, a_cc_num):
        self.cc_num = int(a_cc_num)
        self.ports = {}  # port_num : (low, high)

    def set_port(self, a_port, a_low=0.0, a_high=1.0):
        """ Return None on success or the ports on failure """
        a_port = int(a_port)
        if len(self.ports) >= 5 and a_port not in self.ports:
            return self.ports.keys()
        else:
            self.ports[a_port] = (float(a_low), float(a_high))
            return None

    def has_port(self, a_port):
        return int(a_port) in self.ports

    def remove_port(self, a_port):
        a_port = int(a_port)
        if a_port in self.ports:
            self.ports.pop(a_port)
            return True
        else:
            return False

    @staticmethod
    def from_str(a_str):
        f_cc_num, f_count, f_list = a_str.split("|", 2)
        f_list = f_list.split("|")
        f_result = cc_mapping(f_cc_num)
        for f_i in range(0, int(f_count) * 3, 3):
            f_result.set_port(*f_list[f_i:f_i + 3])
        return f_result

    def __str__(self):
        f_result = ["|".join(str(x) for x in
            ("m", self.cc_num, len(self.ports)))]
        for k, v in self.ports.items():
            f_low, f_high = v
            f_result.append("|".join(str(x) for x in (k, f_low, f_high)))
        return "|".join(f_result)



PYDAW_KNOB_PIXMAP = None
PYDAW_KNOB_PIXMAP_CACHE = {}

def get_scaled_pixmap_knob(a_size):
    global PYDAW_KNOB_PIXMAP, PYDAW_KNOB_PIXMAP_CACHE
    if PYDAW_KNOB_PIXMAP is None:
        PYDAW_KNOB_PIXMAP = QtGui.QPixmap(
            "{}/pydaw-knob.png".format(pydaw_util.global_stylesheet_dir))

    if not a_size in PYDAW_KNOB_PIXMAP_CACHE:
        PYDAW_KNOB_PIXMAP_CACHE[
            a_size] = PYDAW_KNOB_PIXMAP.scaled(a_size, a_size,
            QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

    return PYDAW_KNOB_PIXMAP_CACHE[a_size]

CC_CLIPBOARD = None
TEMPO = 128.0

def set_global_tempo(a_tempo):
    global TEMPO
    TEMPO = a_tempo

class pydaw_pixmap_knob(QtGui.QDial):
    def __init__(self, a_size, a_min_val, a_max_val):
        QtGui.QDial.__init__(self)
        self.setRange(a_min_val, a_max_val)
        self.val_step = float(a_max_val - a_min_val) * 0.005  # / 200.0
        self.val_step_small = self.val_step * 0.1
        self.setGeometry(0, 0, a_size, a_size)
        self.pixmap_size = a_size - 10
        self.pixmap = get_scaled_pixmap_knob(self.pixmap_size)
        self.setFixedSize(a_size, a_size)

    def paintEvent(self, a_event):
        p = QtGui.QPainter(self)
        f_frac_val = (((float)(self.value() - self.minimum())) /
            ((float)(self.maximum() - self.minimum())))
        f_rotate_value = f_frac_val * 270.0
        f_rect = self.rect()
        f_rect.setWidth(f_rect.width() - 3)
        f_rect.setHeight(f_rect.height() - 3)
        f_rect.setX(f_rect.x() + 3)
        f_rect.setY(f_rect.y() + 3)
        p.setPen(KNOB_ARC_PEN)
        p.drawArc(f_rect, -136 * 16, (f_rotate_value + 1.0) * -16)
        p.setRenderHints(
            QtGui.QPainter.HighQualityAntialiasing |
            QtGui.QPainter.SmoothPixmapTransform)
        # xc and yc are the center of the widget's rect.
        xc = self.width() * 0.5
        yc = self.height() * 0.5
        # translates the coordinate system by xc and yc
        p.translate(xc, yc)
        p.rotate(f_rotate_value)
        # we need to move the rectangle that we draw by
        # rx and ry so it's in the center.
        rx = -(self.pixmap_size * 0.5)
        ry = -(self.pixmap_size * 0.5)
        p.drawPixmap(rx, ry, self.pixmap)

    def mousePressEvent(self, a_event):
        if a_event.button() == QtCore.Qt.RightButton:
            QtGui.QDial.mousePressEvent(self, a_event)
            return
        self.mouse_pos = QtGui.QCursor.pos()
        f_pos = a_event.pos()
        self.orig_x = f_pos.x()
        self.orig_y = f_pos.y()
        self.orig_value = self.value()
        self.fine_only = (a_event.modifiers() == QtCore.Qt.ControlModifier)
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.BlankCursor)

    def mouseMoveEvent(self, a_event):
        f_pos = a_event.pos()
        f_x = f_pos.x()
        f_diff_x = f_x - self.orig_x
        if self.fine_only:
            f_val = (f_diff_x * self.val_step_small) + self.orig_value
        else:
            f_y = f_pos.y()
            f_diff_y = self.orig_y - f_y
            f_val = ((f_diff_y * self.val_step) +
                (f_diff_x * self.val_step_small)) + self.orig_value
        f_val = pydaw_util.pydaw_clip_value(
            f_val, self.minimum(), self.maximum())
        f_val = int(f_val)
        if f_val != self.value():
            self.setValue(f_val)
            self.valueChanged.emit(f_val)

    def mouseReleaseEvent(self, a_event):
        QtGui.QCursor.setPos(self.mouse_pos)
        QtGui.QApplication.restoreOverrideCursor()
        self.sliderReleased.emit()


KC_INTEGER = 0
KC_DECIMAL = 1
KC_PITCH = 2
KC_NONE = 3
KC_127_PITCH = 4
KC_127_ZERO_TO_X = 5
KC_LOG_TIME = 6
KC_127_ZERO_TO_X_INT = 7
KC_TIME_DECIMAL = 8
KC_HZ_DECIMAL = 9
KC_INT_PITCH = 10
KC_TENTH = 11

LAST_TEMPO_COMBOBOX_INDEX = 2

class pydaw_abstract_ui_control:
    def __init__(self, a_label, a_port_num, a_rel_callback, a_val_callback,
                 a_val_conversion=KC_NONE, a_port_dict=None, a_preset_mgr=None,
                 a_default_value=None):
        if a_label is None:
            self.name_label = None
        else:
            self.name_label = QtGui.QLabel(str(a_label))
            self.name_label.setAlignment(QtCore.Qt.AlignCenter)
            self.name_label.setMinimumWidth(15)
        self.port_num = int(a_port_num)
        self.val_callback = a_val_callback
        self.rel_callback = a_rel_callback
        self.suppress_changes = False
        self.val_conversion = a_val_conversion
        if a_port_dict is not None:
            a_port_dict[self.port_num] = self
        if a_preset_mgr is not None:
            a_preset_mgr.add_control(self)
        self.default_value = a_default_value
        self.ratio_callback = None
        self.midi_learn_callback = None

    def set_midi_learn(self, a_callback, a_get_cc_map):
        self.midi_learn_callback = a_callback
        self.get_cc_map = a_get_cc_map

    def reset_default_value(self):
        if self.default_value is not None:
            self.set_value(self.default_value, True)

    def set_value(self, a_val, a_changed=False):
        if not a_changed:
            self.suppress_changes = True
        f_val = int(a_val)
        self.control.setValue(f_val)
        self.control_value_changed(f_val)
        self.suppress_changes = False

    def get_value(self):
        return self.control.value()

    def set_127_min_max(self, a_min, a_max):
        self.min_label_value_127 = a_min;
        self.max_label_value_127 = a_max;
        self.label_value_127_add_to = 0.0 - a_min;
        self.label_value_127_multiply_by = ((a_max - a_min) / 127.0);

    def control_released(self):
        if self.rel_callback is not None:
            self.rel_callback(self.port_num, self.control.value())

    def control_value_changed(self, a_value):
        if not self.suppress_changes:
            self.val_callback(self.port_num, self.control.value())

        if self.value_label is not None:
            f_value = float(a_value)
            f_dec_value = 0.0
            if self.val_conversion == KC_NONE:
                pass
            elif self.val_conversion == KC_DECIMAL or \
            self.val_conversion == KC_TIME_DECIMAL or \
            self.val_conversion == KC_HZ_DECIMAL:
                self.value_label.setText(str(round(f_value * .01, 2)))
            elif self.val_conversion == KC_INTEGER or \
            self.val_conversion == KC_INT_PITCH:
                self.value_label.setText(str(int(f_value)))
            elif self.val_conversion == KC_PITCH:
                self.value_label.setText(
                    str(int(pydaw_util.pydaw_pitch_to_hz(f_value))))
            elif self.val_conversion == KC_127_PITCH:
                self.value_label.setText(
                    str(int(pydaw_util.pydaw_pitch_to_hz(
                    (f_value * 0.818897638) + 20.0))))
            elif self.val_conversion == KC_127_ZERO_TO_X:
                f_dec_value = (float(f_value) *
                    self.label_value_127_multiply_by) - \
                    self.label_value_127_add_to
                f_dec_value = ((int)(f_dec_value * 10.0)) * 0.1
                self.value_label.setText(str(round(f_dec_value, 2)))
            elif self.val_conversion == KC_127_ZERO_TO_X_INT:
                f_dec_value = (float(f_value) *
                    self.label_value_127_multiply_by) - \
                    self.label_value_127_add_to
                self.value_label.setText(str(int(f_dec_value)))
            elif self.val_conversion == KC_LOG_TIME:
                f_dec_value = float(f_value) * 0.01
                f_dec_value = f_dec_value * f_dec_value
                self.value_label.setText(str(round(f_dec_value, 2)))
            elif self.val_conversion == KC_TENTH:
                self.value_label.setText(str(round(f_value * .1, 1)))


    def add_to_grid_layout(self, a_layout, a_x):
        if self.name_label is not None:
            a_layout.addWidget(
                self.name_label, 0, a_x, alignment=QtCore.Qt.AlignHCenter)
        a_layout.addWidget(
            self.control, 1, a_x, alignment=QtCore.Qt.AlignHCenter)
        if self.value_label is not None:
            a_layout.addWidget(
                self.value_label, 2, a_x, alignment=QtCore.Qt.AlignHCenter)

    def set_value_dialog(self):
        def ok_handler(a_self=None, a_val=None):
            self.control.setValue(f_spinbox.value())
            f_dialog.close()
        f_dialog = QtGui.QDialog(self.control)
        f_dialog.setWindowTitle(_("Set Value"))
        f_layout = QtGui.QGridLayout(f_dialog)
        f_layout.addWidget(QtGui.QLabel(_("Value:")), 3, 0)
        f_spinbox = QtGui.QSpinBox()
        f_spinbox.setMinimum(self.control.minimum())
        f_spinbox.setMaximum(self.control.maximum())
        f_spinbox.setValue(self.control.value())
        f_layout.addWidget(f_spinbox, 3, 1)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(f_dialog.close)
        f_layout.addWidget(f_cancel_button, 6, 0)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_handler)
        f_layout.addWidget(f_ok_button, 6, 1)
        f_dialog.move(self.control.mapToGlobal(QtCore.QPoint(0.0, 0.0)))
        f_dialog.exec_()

    def tempo_sync_dialog(self):
        def sync_button_pressed(a_self=None):
            global LAST_TEMPO_COMBOBOX_INDEX
            f_frac = 1.0
            f_switch = (f_beat_frac_combobox.currentIndex())
            f_dict = {0 : 0.25, 1 : 0.33333, 2 : 0.5, 3 : 0.666666, 4 : 0.75,
                      5 : 1.0, 6 : 2.0, 7 : 4.0}
            f_frac = f_dict[f_switch]
            f_seconds_per_beat = 60 / (f_spinbox.value())
            if self.val_conversion == KC_TIME_DECIMAL:
                f_result = round(f_seconds_per_beat * f_frac * 100)
            elif self.val_conversion == KC_HZ_DECIMAL:
                f_result = round((1.0 / (f_seconds_per_beat * f_frac)) * 100)
            elif self.val_conversion == KC_LOG_TIME:
                f_result = round(math.sqrt(f_seconds_per_beat * f_frac) * 100)
            f_result = pydaw_util.pydaw_clip_value(
                f_result, self.control.minimum(), self.control.maximum())
            self.control.setValue(f_result)
            LAST_TEMPO_COMBOBOX_INDEX = f_beat_frac_combobox.currentIndex()
            f_dialog.close()
        f_dialog = QtGui.QDialog(self.control)
        f_dialog.setWindowTitle(_("Tempo Sync"))
        f_groupbox_layout = QtGui.QGridLayout(f_dialog)
        f_spinbox = QtGui.QDoubleSpinBox()
        f_spinbox.setDecimals(1)
        f_spinbox.setRange(60, 200)
        f_spinbox.setSingleStep(0.1)
        f_spinbox.setValue(TEMPO)
        f_beat_fracs = ["1/16", "1/12", "1/8", "2/12", "3/16",
                        "1/4", "2/4", "4/4"]
        f_beat_frac_combobox = QtGui.QComboBox()
        f_beat_frac_combobox.setMinimumWidth(75)
        f_beat_frac_combobox.addItems(f_beat_fracs)
        f_beat_frac_combobox.setCurrentIndex(LAST_TEMPO_COMBOBOX_INDEX)
        f_sync_button = QtGui.QPushButton(_("Sync"))
        f_sync_button.pressed.connect(sync_button_pressed)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(f_dialog.close)
        f_groupbox_layout.addWidget(QtGui.QLabel(_("BPM")), 0, 0)
        f_groupbox_layout.addWidget(f_spinbox, 1, 0)
        f_groupbox_layout.addWidget(QtGui.QLabel("Length"), 0, 1)
        f_groupbox_layout.addWidget(f_beat_frac_combobox, 1, 1)
        f_groupbox_layout.addWidget(f_cancel_button, 2, 0)
        f_groupbox_layout.addWidget(f_sync_button, 2, 1)
        f_dialog.move(self.control.mapToGlobal(QtCore.QPoint(0.0, 0.0)))
        f_dialog.exec_()

    def set_note_dialog(self):
        def ok_button_pressed():
            f_value = f_note_selector.get_value()
            f_value = pydaw_util.pydaw_clip_value(
                f_value, self.control.minimum(), self.control.maximum())
            self.set_value(f_value)
            f_dialog.close()
        f_dialog = QtGui.QDialog(self.control)
        f_dialog.setMinimumWidth(210)
        f_dialog.setWindowTitle(_("Set to Note"))
        f_vlayout = QtGui.QVBoxLayout(f_dialog)
        f_note_selector = pydaw_note_selector_widget(0, None, None)
        f_note_selector.set_value(self.get_value())
        f_vlayout.addWidget(f_note_selector.widget)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_button_pressed)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_ok_cancel_layout = QtGui.QHBoxLayout()
        f_cancel_button.pressed.connect(f_dialog.close)
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_vlayout.addLayout(f_ok_cancel_layout)
        f_dialog.move(self.control.mapToGlobal(QtCore.QPoint(0.0, 0.0)))
        f_dialog.exec_()

    def set_ratio_dialog(self):
        def ok_button_pressed():
            f_value = pydaw_util.pydaw_ratio_to_pitch(f_ratio_spinbox.value())
            if self.ratio_callback:
                f_int = round(f_value)
                self.set_value(f_int, True)
                f_frac = round((f_value - f_int) * 100)
                self.ratio_callback(f_frac, True)
            else:
                self.set_value(f_value, True)
            f_dialog.close()
        f_dialog = QtGui.QDialog(self.control)
        f_dialog.setMinimumWidth(210)
        f_dialog.setWindowTitle(_("Set to Ratio"))
        f_layout = QtGui.QGridLayout(f_dialog)
        f_layout.addWidget(QtGui.QLabel(_("Ratio:")), 0, 0)
        f_ratio_spinbox = QtGui.QDoubleSpinBox()

        f_min = pydaw_util.pydaw_pitch_to_ratio(self.control.minimum())
        f_max = pydaw_util.pydaw_pitch_to_ratio(self.control.maximum())
        f_ratio_spinbox.setRange(f_min, round(f_max))
        f_ratio_spinbox.setDecimals(4)
        f_ratio_spinbox.setValue(
            pydaw_util.pydaw_pitch_to_ratio(self.get_value()))
        f_layout.addWidget(f_ratio_spinbox, 0, 1)

        f_ok_button = QtGui.QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_button_pressed)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(f_dialog.close)
        f_layout.addWidget(f_ok_button, 5, 0)
        f_layout.addWidget(f_cancel_button, 5, 1)
        f_dialog.move(self.control.mapToGlobal(QtCore.QPoint(0.0, 0.0)))
        f_dialog.exec_()

    def set_octave_dialog(self):
        def ok_button_pressed():
            f_value = f_spinbox.value() * 12
            self.set_value(f_value, True)
            f_dialog.close()
        f_dialog = QtGui.QDialog(self.control)
        f_dialog.setMinimumWidth(210)
        f_dialog.setWindowTitle(_("Set to Octave"))
        f_layout = QtGui.QGridLayout(f_dialog)
        f_layout.addWidget(QtGui.QLabel(_("Octave:")), 0, 0)
        f_spinbox = QtGui.QSpinBox()
        f_min = self.control.minimum() // 12
        f_max = self.control.maximum() // 12
        f_spinbox.setRange(f_min, f_max)
        f_spinbox.setValue(self.get_value() // 12)
        f_layout.addWidget(f_spinbox, 0, 1)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_button_pressed)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(f_dialog.close)
        f_layout.addWidget(f_ok_button, 5, 0)
        f_layout.addWidget(f_cancel_button, 5, 1)
        f_dialog.move(self.control.mapToGlobal(QtCore.QPoint(0.0, 0.0)))
        f_dialog.exec_()

    def copy_automation(self):
        global CC_CLIPBOARD
        f_value = ((self.get_value() - self.control.minimum()) /
                  (self.control.maximum() - self.control.minimum())) * 127.0
        CC_CLIPBOARD = pydaw_util.pydaw_clip_value(f_value, 0.0, 127.0)

    def paste_automation(self):
        f_frac = CC_CLIPBOARD / 127.0
        f_frac = pydaw_util.pydaw_clip_value(f_frac, 0.0, 1.0)
        f_min = self.control.minimum()
        f_max = self.control.maximum()
        f_value = round(((f_max - f_min) * f_frac) + f_min)
        self.set_value(f_value)

    def midi_learn(self):
        self.midi_learn_callback(self)

    def cc_menu_triggered(self, a_item):
        f_cc = int(str(a_item.text()))
        self.midi_learn_callback(self, f_cc)

    def cc_range_dialog(self, a_item):
        f_cc = int(str(a_item.text()))

        def get_zero_to_one(a_val):
            a_val = float(a_val)
            f_min = float(self.control.minimum())
            f_max = float(self.control.maximum())
            f_range = f_max - f_min
            f_result = (a_val - f_min) / f_range
            return round(f_result, 6)

        def get_real_value(a_val):
            a_val = float(a_val)
            f_min = float(self.control.minimum())
            f_max = float(self.control.maximum())
            f_range = f_max - f_min
            f_result = (a_val * f_range) + f_min
            return int(round(f_result))

        def ok_hander():
            f_low = get_zero_to_one(f_low_spinbox.value())
            f_high = get_zero_to_one(f_high_spinbox.value())
            print((f_low, f_high))
            self.midi_learn_callback(self, f_cc, f_low, f_high)
            f_dialog.close()

        f_cc_map = self.get_cc_map()
        f_default_low, f_default_high = (get_real_value(x) for x in
            f_cc_map[f_cc].ports[self.port_num])

        f_dialog = QtGui.QDialog()
        f_dialog.setWindowTitle(_("Set Range for CC"))
        f_layout = QtGui.QVBoxLayout(f_dialog)
        f_spinbox_layout = QtGui.QHBoxLayout()
        f_layout.addLayout(f_spinbox_layout)
        f_spinbox_layout.addWidget(QtGui.QLabel(_("Low")))
        f_low_spinbox = QtGui.QSpinBox()
        f_low_spinbox.setRange(self.control.minimum(), self.control.maximum())
        f_low_spinbox.setValue(f_default_low)
        f_spinbox_layout.addWidget(f_low_spinbox)
        f_spinbox_layout.addWidget(QtGui.QLabel(_("High")))
        f_high_spinbox = QtGui.QSpinBox()
        f_high_spinbox.setRange(self.control.minimum(), self.control.maximum())
        f_high_spinbox.setValue(f_default_high)
        f_spinbox_layout.addWidget(f_high_spinbox)
        f_ok_cancel_layout = QtGui.QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_hander)
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(f_dialog.close)
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_dialog.move(self.control.mapToGlobal(QtCore.QPoint(0.0, 0.0)))
        f_dialog.exec_()


    def contextMenuEvent(self, a_event):
        f_menu = QtGui.QMenu(self.control)
        if self.midi_learn_callback:
            f_ml_action = f_menu.addAction(_("MIDI Learn"))
            f_ml_action.triggered.connect(self.midi_learn)
            f_cc_menu = QtGui.QMenu(_("CCs"))
            f_menu.addMenu(f_cc_menu)
            f_cc_menu.triggered.connect(self.cc_menu_triggered)
            f_cc_map = self.get_cc_map()
            if f_cc_map:
                f_range_menu = QtGui.QMenu(_("Set Range for CC"))
                f_range_menu.triggered.connect(self.cc_range_dialog)
                f_menu.addMenu(f_range_menu)
            for f_i in range(1, 128):
                f_cc_action = f_cc_menu.addAction(str(f_i))
                f_cc_action.setCheckable(True)
                if f_i in f_cc_map and f_cc_map[f_i].has_port(self.port_num):
                    f_cc_action.setChecked(True)
                    f_range_menu.addAction(str(f_i))
            f_menu.addSeparator()
        f_reset_action = f_menu.addAction(_("Reset to Default Value"))
        f_reset_action.triggered.connect(self.reset_default_value)
        f_set_value_action = f_menu.addAction(_("Set Raw Controller Value..."))
        f_set_value_action.triggered.connect(self.set_value_dialog)
        f_menu.addSeparator()
        f_copy_automation_action = f_menu.addAction(_("Copy"))
        f_copy_automation_action.triggered.connect(self.copy_automation)
        if CC_CLIPBOARD:
            f_paste_automation_action = f_menu.addAction(_("Paste"))
            f_paste_automation_action.triggered.connect(self.paste_automation)
        f_menu.addSeparator()

        if self.val_conversion == KC_TIME_DECIMAL or \
        self.val_conversion == KC_HZ_DECIMAL or \
        self.val_conversion == KC_LOG_TIME:
            f_tempo_sync_action = f_menu.addAction(_("Tempo Sync..."))
            f_tempo_sync_action.triggered.connect(self.tempo_sync_dialog)
        if self.val_conversion == KC_PITCH:
            f_set_note_action = f_menu.addAction(_("Set to Note..."))
            f_set_note_action.triggered.connect(self.set_note_dialog)
        if self.val_conversion == KC_INT_PITCH:
            f_set_ratio_action = f_menu.addAction(_("Set to Ratio..."))
            f_set_ratio_action.triggered.connect(self.set_ratio_dialog)
            f_set_octave_action = f_menu.addAction(_("Set to Octave..."))
            f_set_octave_action.triggered.connect(self.set_octave_dialog)

        f_menu.exec_(QtGui.QCursor.pos())


class pydaw_null_control:
    """ For controls with no visual representation,
        ie: controls that share a UI widget
        depending on selected index, so that they can participate
        normally in the data representation mechanisms
    """
    def __init__(self, a_port_num, a_rel_callback,
                 a_val_callback, a_default_val,
                 a_port_dict, a_preset_mgr=None):
        self.name_label = None
        self.value_label = None
        self.port_num = int(a_port_num)
        self.val_callback = a_val_callback
        self.rel_callback = a_rel_callback
        self.suppress_changes = False
        self.value = a_default_val
        a_port_dict[self.port_num] = self
        self.default_value = a_default_val
        self.control_callback = None
        if a_preset_mgr is not None:
            a_preset_mgr.add_control(self)

    def reset_default_value(self):
        if self.default_value is not None:
            self.set_value(self.default_value, True)

    def get_value(self):
        return self.value

    def set_value(self, a_val, a_changed=False):
        self.value = a_val
        if self.control_callback is not None:
            self.control_callback.set_value(self.value)
        if a_changed:
            self.control_value_changed(a_val)

    def set_control_callback(self, a_callback=None):
        self.control_callback = a_callback

    def control_released(self):
        if self.rel_callback is not None:
            self.rel_callback(self.port_num, self.value)

    def control_value_changed(self, a_value):
        self.val_callback(self.port_num, self.value)

    def set_midi_learn(self, a_ignored, a_ignored2):
        pass

class pydaw_knob_control(pydaw_abstract_ui_control):
    def __init__(self, a_size, a_label, a_port_num,
                 a_rel_callback, a_val_callback,
                 a_min_val, a_max_val, a_default_val, a_val_conversion=KC_NONE,
                 a_port_dict=None, a_preset_mgr=None):
        pydaw_abstract_ui_control.__init__(
            self, a_label, a_port_num, a_rel_callback,
            a_val_callback, a_val_conversion, a_port_dict, a_preset_mgr,
            a_default_val)
        self.control = pydaw_pixmap_knob(a_size, a_min_val, a_max_val)
        self.control.valueChanged.connect(self.control_value_changed)
        self.control.sliderReleased.connect(self.control_released)
        self.control.contextMenuEvent = self.contextMenuEvent
        self.value_label = QtGui.QLabel("")
        self.value_label.setAlignment(QtCore.Qt.AlignCenter)
        self.value_label.setMinimumWidth(15)
        self.set_value(a_default_val)


class pydaw_slider_control(pydaw_abstract_ui_control):
    def __init__(self, a_orientation, a_label, a_port_num, a_rel_callback,
                 a_val_callback, a_min_val, a_max_val,
                 a_default_val, a_val_conversion=KC_NONE, a_port_dict=None,
                 a_preset_mgr=None):
        pydaw_abstract_ui_control.__init__(
            self, a_label, a_port_num, a_rel_callback, a_val_callback,
            a_val_conversion, a_port_dict, a_preset_mgr, a_default_val)
        self.control = QtGui.QSlider(a_orientation)
        self.control.contextMenuEvent = self.contextMenuEvent
        self.control.setRange(a_min_val, a_max_val)
        self.control.valueChanged.connect(self.control_value_changed)
        self.control.sliderReleased.connect(self.control_released)
        self.value_label = QtGui.QLabel("")
        self.value_label.setAlignment(QtCore.Qt.AlignCenter)
        self.value_label.setMinimumWidth(15)
        self.set_value(a_default_val)


class pydaw_spinbox_control(pydaw_abstract_ui_control):
    def __init__(self, a_label, a_port_num, a_rel_callback,
                 a_val_callback, a_min_val, a_max_val,
                 a_default_val, a_val_conversion=KC_NONE,
                 a_port_dict=None, a_preset_mgr=None):
        pydaw_abstract_ui_control.__init__(
            self, a_label, a_port_num, a_rel_callback,
            a_val_callback, a_val_conversion,
            a_port_dict, a_preset_mgr, a_default_val)
        self.control = QtGui.QSpinBox()
        self.widget = self.control
        self.control.setRange(a_min_val, a_max_val)
        self.control.setKeyboardTracking(False)
        self.control.valueChanged.connect(self.control_value_changed)
        self.control.valueChanged.connect(self.control_released)
        self.value_label = None
        self.set_value(a_default_val)


class pydaw_doublespinbox_control(pydaw_abstract_ui_control):
    def __init__(self, a_label, a_port_num, a_rel_callback,
                 a_val_callback, a_min_val, a_max_val,
                 a_default_val, a_val_conversion=KC_NONE, a_port_dict=None,
                 a_preset_mgr=None):
        pydaw_abstract_ui_control.__init__(
            self, a_label, a_port_num, a_rel_callback,
            a_val_callback, a_val_conversion,
            a_port_dict, a_preset_mgr, a_default_val)
        self.control = QtGui.QDoubleSpinBox()
        self.widget = self.control
        self.control.setRange(a_min_val, a_max_val)
        self.control.setKeyboardTracking(False)
        self.control.valueChanged.connect(self.control_value_changed)
        self.control.valueChanged.connect(self.control_released)
        self.value_label = None
        self.set_value(a_default_val)


class pydaw_checkbox_control(pydaw_abstract_ui_control):
    def __init__(self, a_label, a_port_num, a_rel_callback, a_val_callback,
                 a_port_dict=None, a_preset_mgr=None, a_default=0):
        pydaw_abstract_ui_control.__init__(
            self, None, a_port_num, a_rel_callback, a_val_callback,
            a_port_dict=a_port_dict, a_preset_mgr=a_preset_mgr,
            a_default_value=a_default)
        self.control = QtGui.QCheckBox(a_label)
        if a_default:
            self.control.setChecked(True)
        self.widget = self.control
        self.control.stateChanged.connect(self.control_value_changed)
        #self.control.stateChanged.connect(self.control_released)
        self.value_label = None
        self.suppress_changes = False

    def control_value_changed(self, a_val=None):
        if not self.suppress_changes:
            self.val_callback(self.port_num, self.get_value())

    def control_released(self):
        if self.rel_callback is not None:
            self.rel_callback(self.port_num, self.get_value())

    def set_value(self, a_val, a_changed=False):
        self.suppress_changes = True
        f_val = int(a_val)
        if f_val == 0:
            self.control.setChecked(False)
        else:
            self.control.setChecked(True)
        self.suppress_changes = False
        if a_changed:
            self.control_value_changed()

    def get_value(self):
        if self.control.isChecked():
            return 1
        else:
            return 0


class pydaw_combobox_control(pydaw_abstract_ui_control):
    def __init__(self, a_size, a_label, a_port_num,
                 a_rel_callback, a_val_callback,
                 a_items_list=[], a_port_dict=None, a_default_index=None,
                 a_preset_mgr=None):
        self.suppress_changes = True
        self.name_label = QtGui.QLabel(str(a_label))
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        self.control = QtGui.QComboBox()
        self.control.wheelEvent = self.wheel_event
        self.widget = self.control
        self.control.setMinimumWidth(a_size)
        self.control.addItems(a_items_list)
        self.control.setCurrentIndex(0)
        self.control.currentIndexChanged.connect(self.control_value_changed)
        self.port_num = int(a_port_num)
        self.rel_callback = a_rel_callback
        self.val_callback = a_val_callback
        self.suppress_changes = False
        if a_port_dict is not None:
            a_port_dict[self.port_num] = self
        self.value_label = None
        self.default_value = a_default_index
        if a_default_index is not None:
            self.set_value(a_default_index)
        if a_preset_mgr is not None:
            a_preset_mgr.add_control(self)

    def wheel_event(self, a_event=None):
        pass

    def control_value_changed(self, a_val):
        if not self.suppress_changes:
            self.val_callback(self.port_num, a_val)
            if self.rel_callback is not None:
                self.rel_callback(self.port_num, a_val)

    def set_value(self, a_val, a_changed=False):
        if not a_changed:
            self.suppress_changes = True
        self.control.setCurrentIndex(int(a_val))
        self.suppress_changes = False

    def get_value(self):
        return self.control.currentIndex()

ADSR_CLIPBOARD = {}

class pydaw_adsr_widget:
    def __init__(self, a_size, a_sustain_in_db, a_attack_port, a_decay_port,
                 a_sustain_port, a_release_port, a_label,
                 a_rel_callback, a_val_callback,
                 a_port_dict=None, a_preset_mgr=None, a_attack_default=10,
                 a_prefx_port=None, a_knob_type=KC_TIME_DECIMAL,
                 a_delay_port=None, a_hold_port=None):
        self.clipboard_dict = {}
        self.groupbox = QtGui.QGroupBox(a_label)
        self.groupbox.contextMenuEvent = self.context_menu_event
        self.groupbox.setObjectName("plugin_groupbox")
        self.layout = QtGui.QGridLayout(self.groupbox)
        self.layout.setMargin(3)

        if a_delay_port is not None:
            self.delay_knob = pydaw_knob_control(
                a_size, _("Delay"), a_delay_port,
                a_rel_callback, a_val_callback, 0, 200,
                0, KC_TIME_DECIMAL, a_port_dict, a_preset_mgr)
            self.delay_knob.add_to_grid_layout(self.layout, 0)
            self.clipboard_dict["delay"] = self.delay_knob
        self.attack_knob = pydaw_knob_control(
            a_size, _("Attack"), a_attack_port, a_rel_callback,
            a_val_callback, 0, 200, a_attack_default,
            a_knob_type, a_port_dict, a_preset_mgr)
        if a_hold_port is not None:
            self.hold_knob = pydaw_knob_control(
                a_size, _("Hold"), a_hold_port,
                a_rel_callback, a_val_callback, 0, 200,
                0, KC_TIME_DECIMAL, a_port_dict, a_preset_mgr)
            self.hold_knob.add_to_grid_layout(self.layout, 3)
            self.clipboard_dict["hold"] = self.hold_knob
        self.decay_knob = pydaw_knob_control(
            a_size, _("Decay"), a_decay_port, a_rel_callback,
            a_val_callback, 10, 200, 50, a_knob_type,
            a_port_dict, a_preset_mgr)
        if a_sustain_in_db:
            self.sustain_knob = pydaw_knob_control(
                a_size, _("Sustain"), a_sustain_port,
                a_rel_callback, a_val_callback,
                -30, 0, 0, KC_INTEGER, a_port_dict, a_preset_mgr)
            self.clipboard_dict["sustain_db"] = self.sustain_knob
        else:
            self.sustain_knob = pydaw_knob_control(
                a_size, _("Sustain"), a_sustain_port,
                a_rel_callback, a_val_callback,
                0, 100, 100, KC_DECIMAL, a_port_dict, a_preset_mgr)
            self.clipboard_dict["sustain"] = self.sustain_knob
        self.release_knob = pydaw_knob_control(
            a_size, _("Release"), a_release_port,
            a_rel_callback, a_val_callback, 10,
            400, 50, a_knob_type, a_port_dict, a_preset_mgr)
        self.attack_knob.add_to_grid_layout(self.layout, 2)
        self.decay_knob.add_to_grid_layout(self.layout, 4)
        self.sustain_knob.add_to_grid_layout(self.layout, 6)
        self.release_knob.add_to_grid_layout(self.layout, 8)
        self.clipboard_dict["attack"] = self.attack_knob
        self.clipboard_dict["decay"] = self.decay_knob
        self.clipboard_dict["release"] = self.release_knob
        if a_prefx_port is not None:
            self.prefx_checkbox = pydaw_checkbox_control(
                "PreFX", a_prefx_port, a_rel_callback, a_val_callback,
                a_port_dict, a_preset_mgr)
            self.prefx_checkbox.add_to_grid_layout(self.layout, 10)

    def context_menu_event(self, a_event):
        f_menu = QtGui.QMenu(self.groupbox)
        f_copy_action = f_menu.addAction(_("Copy"))
        f_copy_action.triggered.connect(self.copy)
        f_paste_action = f_menu.addAction(_("Paste"))
        f_paste_action.triggered.connect(self.paste)
        f_menu.exec_(QtGui.QCursor.pos())

    def copy(self):
        global ADSR_CLIPBOARD
        ADSR_CLIPBOARD = dict([(k, v.get_value())
            for k, v in self.clipboard_dict.items()])

    def paste(self):
        if ADSR_CLIPBOARD:
            for k, v in self.clipboard_dict.items():
                v.set_value(ADSR_CLIPBOARD[k], True)

class pydaw_filter_widget:
    def __init__(self, a_size, a_rel_callback, a_val_callback, a_port_dict,
                 a_cutoff_port, a_res_port, a_type_port=None,
                 a_label=_("Filter"), a_preset_mgr=None):
        self.groupbox = QtGui.QGroupBox(str(a_label))
        self.groupbox.setObjectName("plugin_groupbox")
        self.layout = QtGui.QGridLayout(self.groupbox)
        self.layout.setMargin(3)
        self.cutoff_knob = pydaw_knob_control(
            a_size, _("Cutoff"), a_cutoff_port,
            a_rel_callback, a_val_callback,
            20, 124, 124, KC_PITCH, a_port_dict, a_preset_mgr)
        self.cutoff_knob.add_to_grid_layout(self.layout, 0)
        self.res_knob = pydaw_knob_control(
            a_size, _("Res"), a_res_port, a_rel_callback,
            a_val_callback, -300, 0, -120, KC_TENTH,
            a_port_dict, a_preset_mgr)
        self.res_knob.add_to_grid_layout(self.layout, 1)
        if a_type_port is not None:
            self.type_combobox = pydaw_combobox_control(
                150, _("Type"), a_type_port, a_rel_callback, a_val_callback,
                ["LP 2", "HP 2", "BP2", "LP 4", "HP 4", "BP4", _("Off")],
                a_port_dict, a_preset_mgr=a_preset_mgr)
            self.layout.addWidget(self.type_combobox.name_label, 2, 0)
            self.layout.addWidget(self.type_combobox.control, 2, 1)


class pydaw_perc_env_widget:
    def __init__(self, a_size, a_rel_callback, a_val_callback, a_port_dict,
                 a_time1_port, a_pitch1_port, a_time2_port,
                 a_pitch2_port, a_on_port,
                 a_label=_("Perc Env"), a_preset_mgr=None):
        self.groupbox = QtGui.QGroupBox(str(a_label))
        self.groupbox.setObjectName("plugin_groupbox")
        self.layout = QtGui.QGridLayout(self.groupbox)
        self.layout.setMargin(3)

        self.time1_knob = pydaw_knob_control(
            a_size, _("Time1"), a_time1_port,
            a_rel_callback, a_val_callback,
            2, 40, 10, KC_INTEGER, a_port_dict, a_preset_mgr)
        self.time1_knob.add_to_grid_layout(self.layout, 0)

        self.pitch1_knob = pydaw_knob_control(
            a_size, _("Pitch1"), a_pitch1_port, a_rel_callback,
            a_val_callback, 42, 120, 66, KC_PITCH,
            a_port_dict, a_preset_mgr)
        self.pitch1_knob.add_to_grid_layout(self.layout, 1)

        self.time2_knob = pydaw_knob_control(
            a_size, _("Time2"), a_time2_port, a_rel_callback, a_val_callback,
            20, 400, 100, KC_INTEGER, a_port_dict, a_preset_mgr)
        self.time2_knob.add_to_grid_layout(self.layout, 2)

        self.pitch2_knob = pydaw_knob_control(
            a_size, _("Pitch2"), a_pitch2_port, a_rel_callback,
            a_val_callback, 33, 63, 48, KC_PITCH, a_port_dict, a_preset_mgr)
        self.pitch2_knob.add_to_grid_layout(self.layout, 3)

        self.on_switch = pydaw_checkbox_control(
            _("On"), a_on_port, a_rel_callback, a_val_callback,
            a_port_dict, a_preset_mgr)
        self.on_switch.add_to_grid_layout(self.layout, 4)


class pydaw_ramp_env_widget:
    def __init__(self, a_size, a_rel_callback, a_val_callback, a_port_dict,
                 a_time_port, a_amt_port,
                 a_label=_("Ramp Env"), a_preset_mgr=None, a_curve_port=None):
        self.groupbox = QtGui.QGroupBox(str(a_label))
        self.groupbox.setObjectName("plugin_groupbox")
        self.layout = QtGui.QGridLayout(self.groupbox)
        self.layout.setMargin(3)

        if a_amt_port is not None:
            self.amt_knob = pydaw_knob_control(
                a_size, _("Amt"), a_amt_port,
                a_rel_callback, a_val_callback,
                -36, 36, 0, KC_INTEGER, a_port_dict, a_preset_mgr)
            self.amt_knob.add_to_grid_layout(self.layout, 0)
        self.time_knob = pydaw_knob_control(
            a_size, _("Time"), a_time_port, a_rel_callback, a_val_callback,
            1, 600, 100, KC_TIME_DECIMAL, a_port_dict, a_preset_mgr)
        self.time_knob.add_to_grid_layout(self.layout, 1)
        if a_curve_port is not None:
            self.curve_knob = pydaw_knob_control(
                a_size, _("Curve"), a_curve_port,
                a_rel_callback, a_val_callback,
                0, 100, 50, KC_NONE, a_port_dict, a_preset_mgr)
            self.curve_knob.add_to_grid_layout(self.layout, 2)

class pydaw_lfo_widget:
    def __init__(self, a_size, a_rel_callback, a_val_callback, a_port_dict,
                 a_freq_port, a_type_port, a_type_list,
                 a_label=_("LFO"), a_preset_mgr=None, a_phase_port=None):
        self.groupbox = QtGui.QGroupBox(str(a_label))
        self.groupbox.setObjectName("plugin_groupbox")
        self.layout = QtGui.QGridLayout(self.groupbox)
        self.layout.setMargin(3)
        self.freq_knob = pydaw_knob_control(
            a_size, _("Freq"), a_freq_port, a_rel_callback, a_val_callback,
            10, 1600, 200, KC_HZ_DECIMAL, a_port_dict, a_preset_mgr)
        self.freq_knob.add_to_grid_layout(self.layout, 0)
        self.type_combobox = pydaw_combobox_control(
            120, _("Type"), a_type_port, a_rel_callback, a_val_callback,
            a_type_list, a_port_dict, 0, a_preset_mgr=a_preset_mgr)
        self.layout.addWidget(self.type_combobox.name_label, 0, 1)
        self.layout.addWidget(self.type_combobox.control, 1, 1)
        if a_phase_port:
            self.phase_knob = pydaw_knob_control(
                a_size, _("Phase"), a_phase_port,
                a_rel_callback, a_val_callback,
                0, 100, 0, KC_DECIMAL, a_port_dict, a_preset_mgr)
            self.phase_knob.add_to_grid_layout(self.layout, 2)

class pydaw_osc_widget:
    def __init__(self, a_size, a_pitch_port, a_fine_port,
                 a_vol_port, a_type_port,
                 a_osc_types_list, a_rel_callback, a_val_callback, a_label,
                 a_port_dict=None, a_preset_mgr=None, a_default_type=0):
        self.pitch_knob = pydaw_knob_control(
            a_size, _("Pitch"), a_pitch_port,
            a_rel_callback, a_val_callback, -36, 36,
            0, a_val_conversion=KC_INT_PITCH, a_port_dict=a_port_dict,
            a_preset_mgr=a_preset_mgr)
        self.fine_knob = pydaw_knob_control(
            a_size, _("Fine"), a_fine_port, a_rel_callback,
            a_val_callback, -100, 100, 0, a_val_conversion=KC_DECIMAL,
            a_port_dict=a_port_dict, a_preset_mgr=a_preset_mgr)

        self.pitch_knob.ratio_callback = self.fine_knob.set_value

        self.vol_knob = pydaw_knob_control(
            a_size, _("Vol"), a_vol_port, a_rel_callback,
            a_val_callback, -30, 0, -6, a_val_conversion=KC_INTEGER,
            a_port_dict=a_port_dict, a_preset_mgr=a_preset_mgr)
        self.osc_type_combobox = pydaw_combobox_control(
            139, _("Type"), a_type_port, a_rel_callback, a_val_callback,
            a_osc_types_list, a_port_dict, a_preset_mgr=a_preset_mgr,
            a_default_index=a_default_type)
        self.grid_layout = QtGui.QGridLayout()
        self.group_box = QtGui.QGroupBox(str(a_label))
        self.group_box.setObjectName("plugin_groupbox")
        self.group_box.setLayout(self.grid_layout)
        self.pitch_knob.add_to_grid_layout(self.grid_layout, 0)
        self.fine_knob.add_to_grid_layout(self.grid_layout, 1)
        self.vol_knob.add_to_grid_layout(self.grid_layout, 2)
        self.grid_layout.addWidget(self.osc_type_combobox.name_label, 0, 3)
        self.grid_layout.addWidget(self.osc_type_combobox.control, 1, 3)


NOTE_SELECTOR_CLIPBOARD = None

class pydaw_note_selector_widget:
    def __init__(self, a_port_num, a_rel_callback, a_val_callback,
                 a_port_dict=None, a_default_value=None, a_preset_mgr=None):
        self.control = self
        self.port_num = a_port_num
        self.rel_callback = a_rel_callback
        self.val_callback = a_val_callback
        self.note_combobox = QtGui.QComboBox()
        self.note_combobox.wheelEvent = self.wheel_event
        self.note_combobox.setMinimumWidth(60)
        self.note_combobox.addItems(
            ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])
        self.note_combobox.contextMenuEvent = self.context_menu_event
        self.octave_spinbox = QtGui.QSpinBox()
        self.octave_spinbox.setRange(-2, 8)
        self.octave_spinbox.setValue(3)
        self.octave_spinbox.contextMenuEvent = self.context_menu_event
        self.widget = QtGui.QWidget()
        self.layout = QtGui.QHBoxLayout()
        self.layout.setMargin(0)
        self.widget.setLayout(self.layout)
        self.layout.addWidget(self.note_combobox)
        self.layout.addWidget(self.octave_spinbox)
        self.note_combobox.currentIndexChanged.connect(
            self.control_value_changed)
        self.octave_spinbox.valueChanged.connect(self.control_value_changed)
        self.suppress_changes = False
        if a_port_dict is not None:
            a_port_dict[self.port_num] = self
        self.name_label = None
        self.value_label = None
        self.default_value = a_default_value
        if a_default_value is not None:
            self.selected_note = a_default_value
            self.set_value(a_default_value)
        else:
            self.selected_note = 60
        if a_preset_mgr is not None:
            a_preset_mgr.add_control(self)

    def context_menu_event(self, a_event=None):
        f_menu = QtGui.QMenu(self.widget)
        f_copy_action = f_menu.addAction(_("Copy"))
        f_copy_action.triggered.connect(self.copy_to_clipboard)
        f_paste_action = f_menu.addAction(_("Paste"))
        f_paste_action.triggered.connect(self.paste_from_clipboard)
        f_menu.exec_(QtGui.QCursor.pos())

    def copy_to_clipboard(self):
        global NOTE_SELECTOR_CLIPBOARD
        NOTE_SELECTOR_CLIPBOARD = self.get_value()

    def paste_from_clipboard(self):
        if NOTE_SELECTOR_CLIPBOARD is not None:
            self.set_value(NOTE_SELECTOR_CLIPBOARD, True)

    def wheel_event(self, a_event=None):
        pass

    def control_value_changed(self, a_val=None):
        self.selected_note = (self.note_combobox.currentIndex()) + \
                             (((self.octave_spinbox.value()) + 2) * 12)
        if not self.suppress_changes:
            if self.val_callback is not None:
                self.val_callback(self.port_num, self.selected_note)
            if self.rel_callback is not None:
                self.rel_callback(self.port_num, self.selected_note)

    def set_value(self, a_val, a_changed=False):
        self.suppress_changes = True
        self.note_combobox.setCurrentIndex(a_val % 12)
        self.octave_spinbox.setValue((int(float(a_val) / 12.0)) - 2)
        self.suppress_changes = False
        if a_changed:
            self.control_value_changed(a_val)

    def get_value(self):
        return self.selected_note

    def reset_default_value(self):
        if self.default_value is not None:
            self.set_value(self.default_value, True)

    def add_to_grid_layout(self, a_layout, a_x):
        if self.name_label is not None:
            a_layout.addWidget(
                self.name_label, 0, a_x, alignment=QtCore.Qt.AlignHCenter)
        a_layout.addWidget(
            self.widget, 1, a_x, alignment=QtCore.Qt.AlignHCenter)
        if self.value_label is not None:
            a_layout.addWidget(
                self.value_label, 2, a_x, alignment=QtCore.Qt.AlignHCenter)

class pydaw_file_select_widget:
    """
        a_load_callback : function to call when loading
        that accepts a single argument of [list of paths,...]
    """
    def __init__(self, a_load_callback):
        self.load_callback = a_load_callback
        self.layout = QtGui.QHBoxLayout()
        self.layout.setMargin(2)
        self.clear_button = QtGui.QPushButton(_("Clear"))
        self.clear_button.setMaximumWidth(60)
        self.copy_to_clipboard = QtGui.QPushButton(_("Copy"))
        self.copy_to_clipboard.setToolTip(_("Copy file path to clipboard"))
        self.copy_to_clipboard.pressed.connect(self.copy_to_clipboard_pressed)
        self.copy_to_clipboard.setMaximumWidth(60)
        self.paste_from_clipboard = QtGui.QPushButton(_("Paste"))
        self.paste_from_clipboard.setToolTip(
            _("Paste file path from clipboard"))
        self.paste_from_clipboard.pressed.connect(
            self.paste_from_clipboard_pressed)
        self.paste_from_clipboard.setMaximumWidth(60)
        self.reload_button = QtGui.QPushButton(_("Reload"))
        self.reload_button.setMaximumWidth(60)
        self.file_path = QtGui.QLineEdit()
        self.file_path.setSizePolicy(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.file_path.setReadOnly(True)
        self.file_path.setMinimumWidth(210)
        self.last_directory = ("")
        self.layout.addWidget(self.file_path)
        self.layout.addWidget(self.clear_button)
        self.layout.addWidget(self.copy_to_clipboard)
        self.layout.addWidget(self.paste_from_clipboard)
        self.layout.addWidget(self.reload_button)


    def clear_button_pressed(self):
        self.file_path.setText("")

    def get_file(self):
        return self.file_path.text()

    def set_file(self, a_file):
        self.file_path.setText(str(a_file))

    def copy_to_clipboard_pressed(self):
        f_text = str(self.file_path.text())
        if f_text != "":
            f_clipboard = QtGui.QApplication.clipboard()
            f_clipboard.setText(f_text)

    def paste_from_clipboard_pressed(self):
        f_clipboard = QtGui.QApplication.clipboard()
        f_text = f_clipboard.text()
        if f_text is None:
            QtGui.QMessageBox.warning(
                self.paste_from_clipboard, _("Error"),
                _("No file path in the system clipboard."))
        else:
            f_text = str(f_text).strip()
            if os.path.isfile(f_text):
                self.set_file(f_text)
                self.load_callback([f_text])
            else:
                #Don't show more than 100 chars just in case somebody had an
                #entire book copied to the clipboard
                f_str = f_text[100:]
                QtGui.QMessageBox.warning(
                    self.paste_from_clipboard, _("Error"),
                    _("{} does not exist.").format(f_str))



class pydaw_abstract_file_browser_widget():
    def __init__(self):
        self.hsplitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
        self.vsplitter = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.folders_tab_widget = QtGui.QTabWidget()
        self.hsplitter.addWidget(self.folders_tab_widget)
        self.folders_widget = QtGui.QWidget()
        self.vsplitter.addWidget(self.folders_widget)
        self.folders_widget_layout = QtGui.QVBoxLayout()
        self.folders_widget.setLayout(self.folders_widget_layout)
        self.folders_tab_widget.setMaximumWidth(660)
        self.folders_tab_widget.addTab(self.vsplitter, _("Files"))
        self.folder_path_lineedit = QtGui.QLineEdit()
        self.folder_path_lineedit.setReadOnly(True)
        self.folders_widget_layout.addWidget(self.folder_path_lineedit)

        self.folder_filter_hlayout = QtGui.QHBoxLayout()
        self.folder_filter_hlayout.addWidget(QtGui.QLabel(_("Filter:")))
        self.folder_filter_lineedit = QtGui.QLineEdit()
        self.folder_filter_lineedit.textChanged.connect(self.on_filter_folders)
        self.folder_filter_hlayout.addWidget(self.folder_filter_lineedit)
        self.folder_filter_clear_button = QtGui.QPushButton(_("Clear"))
        self.folder_filter_clear_button.pressed.connect(
            self.on_folder_filter_clear)
        self.folder_filter_hlayout.addWidget(self.folder_filter_clear_button)
        self.folders_widget_layout.addLayout(self.folder_filter_hlayout)

        self.list_folder = QtGui.QListWidget()
        self.list_folder.itemClicked.connect(self.folder_item_clicked)
        self.folders_widget_layout.addWidget(self.list_folder)
        self.folder_buttons_hlayout = QtGui.QHBoxLayout()
        self.folders_widget_layout.addLayout(self.folder_buttons_hlayout)
        self.up_button = QtGui.QPushButton(_("Up"))
        self.up_button.pressed.connect(self.on_up_button)
        self.up_button.contextMenuEvent = self.up_contextMenuEvent
        self.folder_buttons_hlayout.addWidget(self.up_button)
        self.back_button = QtGui.QPushButton(_("Back"))
        self.folder_buttons_hlayout.addWidget(self.back_button)
        self.back_button.contextMenuEvent = self.back_contextMenuEvent
        self.back_button.pressed.connect(self.on_back)
        self.bookmark_button = QtGui.QPushButton(_("Bookmark"))
        self.bookmark_button.pressed.connect(self.bookmark_button_pressed)
        self.folder_buttons_hlayout.addWidget(self.bookmark_button)
        self.paste_button = QtGui.QPushButton(_("Paste"))
        self.paste_button.pressed.connect(self.paste_button_pressed)
        self.folder_buttons_hlayout.addWidget(self.paste_button)

        self.bookmarks_tab = QtGui.QWidget()
        self.bookmarks_tab_vlayout = QtGui.QVBoxLayout()
        self.bookmarks_tab.setLayout(self.bookmarks_tab_vlayout)
        self.list_bookmarks = QtGui.QTreeWidget()
        self.list_bookmarks.setHeaderHidden(True)
        self.list_bookmarks.itemClicked.connect(self.bookmark_clicked)
        self.list_bookmarks.contextMenuEvent = self.bookmark_context_menu_event
        self.bookmarks_tab_vlayout.addWidget(self.list_bookmarks)
        self.bookmark_button_hlayout = QtGui.QHBoxLayout()
        self.bookmarks_reload_button = QtGui.QPushButton(_("Reload"))
        self.bookmarks_tab_vlayout.addLayout(self.bookmark_button_hlayout)
        self.bookmark_button_hlayout.addWidget(self.bookmarks_reload_button)
        self.bookmarks_reload_button.pressed.connect(self.open_bookmarks)
        self.bookmarks_menu_button = QtGui.QPushButton(_("Menu"))
        self.bookmark_button_hlayout.addWidget(self.bookmarks_menu_button)
        f_bookmark_menu = QtGui.QMenu(self.bookmarks_tab)
        self.bookmarks_menu_button.setMenu(f_bookmark_menu)
        f_bookmark_open_action = f_bookmark_menu.addAction(_("Open..."))
        f_bookmark_open_action.triggered.connect(self.on_bookmark_open)
        f_bookmark_save_as_action = f_bookmark_menu.addAction(_("Save As..."))
        f_bookmark_save_as_action.triggered.connect(self.on_bookmark_save_as)
        self.folders_tab_widget.addTab(self.bookmarks_tab, _("Bookmarks"))

        self.file_vlayout = QtGui.QVBoxLayout()
        self.file_widget = QtGui.QWidget()
        self.file_widget.setLayout(self.file_vlayout)
        self.vsplitter.addWidget(self.file_widget)
        self.filter_hlayout = QtGui.QHBoxLayout()
        self.filter_hlayout.addWidget(QtGui.QLabel(_("Filter:")))
        self.filter_lineedit = QtGui.QLineEdit()
        self.filter_lineedit.textChanged.connect(self.on_filter_files)
        self.filter_hlayout.addWidget(self.filter_lineedit)
        self.filter_clear_button = QtGui.QPushButton(_("Clear"))
        self.filter_clear_button.pressed.connect(self.on_filter_clear)
        self.filter_hlayout.addWidget(self.filter_clear_button)
        self.file_vlayout.addLayout(self.filter_hlayout)
        self.list_file = QtGui.QListWidget()
        self.list_file.setSelectionMode(QtGui.QListWidget.SingleSelection)
        self.file_vlayout.addWidget(self.list_file)
        self.file_hlayout = QtGui.QHBoxLayout()
        self.preview_button = QtGui.QPushButton(_("Preview"))
        self.file_hlayout.addWidget(self.preview_button)
        self.stop_preview_button = QtGui.QPushButton(_("Stop"))
        self.file_hlayout.addWidget(self.stop_preview_button)
        self.refresh_button = QtGui.QPushButton(_("Refresh"))
        self.file_hlayout.addWidget(self.refresh_button)
        self.refresh_button.pressed.connect(self.on_refresh)
        self.file_vlayout.addLayout(self.file_hlayout)

        self.last_open_dir = pydaw_util.global_home
        self.history = [pydaw_util.global_home]
        self.set_folder(".")
        self.open_bookmarks()
        self.modulex_clipboard = None
        self.audio_items_clipboard = []
        self.hsplitter.setSizes([300, 9999])

    def open_file_in_browser(self, a_path):
        f_path = str(a_path)
        f_dir = os.path.dirname(f_path)
        if os.path.isdir(f_dir):
            self.folders_tab_widget.setCurrentIndex(0)
            self.set_folder(f_dir, True)
            f_file = os.path.basename(f_path)
            self.select_file(f_file)
        else:
            QtGui.QMessageBox.warning(self.vsplitter, _("Error"),
            _("The folder did not exist:\n\n{}").format(f_dir))

    def on_bookmark_save_as(self):
        f_file = QtGui.QFileDialog.getSaveFileName(
            parent=self.bookmarks_tab, caption=_('Save bookmark file...'),
            directory=pydaw_util.global_home,
            filter=BM_FILE_DIALOG_STRING)
        if not f_file is None and not str(f_file) == "":
            f_file = str(f_file)
            if not f_file.endswith(".pybm4"):
                f_file += ".pybm4"
            os.system('cp "{}" "{}"'.format(
                pydaw_util.BOOKMARKS_FILE, f_file))

    def on_bookmark_open(self):
        f_file = QtGui.QFileDialog.getOpenFileName(
            parent=self.bookmarks_tab, caption=_('Open bookmark file...'),
            directory=pydaw_util.global_home,
            filter=BM_FILE_DIALOG_STRING)
        if not f_file is None and not str(f_file) == "":
            f_file = str(f_file)
            os.system('cp "{}" "{}"'.format(
                f_file, pydaw_util.BOOKMARKS_FILE))
            self.open_bookmarks()

    def on_refresh(self):
        self.set_folder(".")

    def on_back(self):
        if len(self.history) > 1:
            self.history.pop(-1)
            self.set_folder(self.history[-1], a_full_path=True)

    def open_path_from_action(self, a_action):
        self.set_folder(str(a_action.text()), a_full_path=True)

    def back_contextMenuEvent(self, a_event):
        f_menu = QtGui.QMenu(self.back_button)
        f_menu.triggered.connect(self.open_path_from_action)
        for f_path in reversed(self.history):
            f_menu.addAction(f_path)
        f_menu.exec_(QtGui.QCursor.pos())

    def up_contextMenuEvent(self, a_event):
        if self.last_open_dir != "/":
            f_menu = QtGui.QMenu(self.up_button)
            f_menu.triggered.connect(self.open_path_from_action)
            f_arr = self.last_open_dir.split("/")[1:]
            f_paths = []
            for f_i in range(len(f_arr)):
                f_paths.append("/{}".format("/".join(f_arr[:f_i])))
            for f_path in reversed(f_paths):
                f_menu.addAction(f_path)
            f_menu.exec_(QtGui.QCursor.pos())

    def on_filter_folders(self):
        self.on_filter(self.folder_filter_lineedit, self.list_folder)

    def on_filter_files(self):
        self.on_filter(self.filter_lineedit, self.list_file)

    def on_filter(self, a_line_edit, a_list_widget):
        f_text = str(a_line_edit.text()).lower().strip()
        for f_i in range(a_list_widget.count()):
            f_item = a_list_widget.item(f_i)
            f_item_text = str(f_item.text()).lower()
            if f_text in f_item_text:
                f_item.setHidden(False)
            else:
                f_item.setHidden(True)

    def on_folder_filter_clear(self):
        self.folder_filter_lineedit.setText("")

    def on_filter_clear(self):
        self.filter_lineedit.setText("")

    def open_bookmarks(self):
        self.list_bookmarks.clear()
        f_dict = pydaw_util.global_get_file_bookmarks()
        for k in sorted(f_dict.keys(), key=lambda s: s.lower()):
            f_parent = QtGui.QTreeWidgetItem()
            f_parent.setText(0, k)
            self.list_bookmarks.addTopLevelItem(f_parent)
            for k2 in sorted(f_dict[k].keys(), key=lambda s: s.lower()):
                f_child = QtGui.QTreeWidgetItem()
                f_child.setText(0, k2)
                f_parent.addChild(f_child)
            f_parent.setExpanded(True)

    def bookmark_button_pressed(self):
        def on_ok(a_val=None):
            f_text = str(f_category.currentText()).strip()
            if not f_text:
                QtGui.QMessageBox.warning(
                    f_window, _("Error"), _("Category cannot be empty"))
            f_val = str(f_lineedit.text()).strip()
            if not f_val:
                QtGui.QMessageBox.warning(
                    f_window, _("Error"), _("Name cannot be empty"))
                return
            pydaw_util.global_add_file_bookmark(
                f_val, self.last_open_dir, f_text)
            self.open_bookmarks()
            f_window.close()

        def on_cancel(a_val=None):
            f_window.close()

        f_window = QtGui.QDialog(self.list_bookmarks)
        f_window.setMinimumWidth(300)
        f_window.setWindowTitle(_("Add Bookmark"))
        f_layout = QtGui.QVBoxLayout()
        f_window.setLayout(f_layout)
        f_grid_layout = QtGui.QGridLayout()
        f_layout.addLayout(f_grid_layout)
        f_dict = pydaw_util.global_get_file_bookmarks()
        if not f_dict:
            f_dict = {'default':None}
        f_grid_layout.addWidget(QtGui.QLabel(_("Category:")), 0, 0)
        f_category = QtGui.QComboBox()
        f_category.setEditable(True)
        f_category.addItems(sorted(f_dict.keys(), key=lambda s: s.lower()))
        f_grid_layout.addWidget(f_category, 0, 1)
        f_lineedit = QtGui.QLineEdit()
        f_tmp_arr = self.last_open_dir.rsplit("/", 1)
        if len(f_tmp_arr) >= 2:
            f_lineedit.setText(f_tmp_arr[-1])
        f_grid_layout.addWidget(QtGui.QLabel(_("Name:")), 1, 0)
        f_grid_layout.addWidget(f_lineedit, 1, 1)
        f_hlayout2 = QtGui.QHBoxLayout()
        f_layout.addLayout(f_hlayout2)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_ok_button.pressed.connect(on_ok)
        f_hlayout2.addWidget(f_ok_button)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(on_cancel)
        f_hlayout2.addWidget(f_cancel_button)
        f_window.exec_()

    def paste_button_pressed(self):
        f_clipboard = QtGui.QApplication.clipboard()
        f_text = f_clipboard.text()
        if f_text is None:
            QtGui.QMessageBox.warning(self.paste_from_clipboard, _("Error"),
            _("No file path in the system clipboard."))
        else:
            f_text = str(f_text).strip()
            if os.path.exists(f_text):
                if os.path.isfile(f_text):
                    self.open_file_in_browser(f_text)
                elif os.path.isdir(f_text):
                    self.set_folder(f_text, True)
                else:
                    QtGui.QMessageBox.warning(
                        self.hsplitter, _("Error"),
                        "'{}' exists, but did not test True for being "
                        "a file or a folder".format(f_text))
            else:
                #Don't show more than 100 chars just in case somebody had an
                #entire book copied to the clipboard
                f_str = f_text[100:]
                QtGui.QMessageBox.warning(
                    self.hsplitter, _("Error"),
                    _("'{}' does not exist.").format(f_str))

    def bookmark_clicked(self, a_item):
        #test = QtGui.QTreeWidgetItem()
        #test.parent()
        f_parent = a_item.parent()
        if f_parent is not None:
            f_parent_str = str(f_parent.text(0))
            f_dict = pydaw_util.global_get_file_bookmarks()
            f_folder_name = str(a_item.text(0))
            if f_parent_str in f_dict:
                if f_folder_name in f_dict[f_parent_str]:
                    self.set_folder(f_dict[f_parent_str][f_folder_name], True)
                    self.folders_tab_widget.setCurrentIndex(0)
                else:
                    QtGui.QMessageBox.warning(
                        self.widget, _("Error"),
                        _("This bookmark no longer exists.  You may have "
                        "deleted it in another window."))
                self.open_bookmarks()

    def delete_bookmark(self):
        f_items = self.list_bookmarks.selectedItems()
        if len(f_items) > 0:
            f_parent = f_items[0].parent()
            if f_parent is None:
                f_parent = f_items[0]
                for f_i in range(f_parent.childCount()):
                    f_child = f_parent.child(f_i)
                    pydaw_util.global_delete_file_bookmark(
                        f_parent.text(0), f_child.text(0))
            else:
                pydaw_util.global_delete_file_bookmark(
                    f_parent.text(0), f_items[0].text(0))
                self.list_bookmarks.clear()
            self.open_bookmarks()

    def bookmark_context_menu_event(self, a_event):
        f_menu = QtGui.QMenu(self.list_bookmarks)
        f_del_action = f_menu.addAction(_("Delete"))
        f_del_action.triggered.connect(self.delete_bookmark)
        f_menu.exec_(QtGui.QCursor.pos())

    def folder_item_clicked(self, a_item):
        self.set_folder(a_item.text())

    def on_up_button(self):
        self.set_folder("..")

    def set_folder(self, a_folder, a_full_path=False):
        self.list_file.clear()
        self.list_folder.clear()
        self.folder_filter_lineedit.clear()
        if a_full_path:
            self.last_open_dir = str(a_folder)
        else:
            self.last_open_dir = os.path.abspath(
                "{}/{}".format(self.last_open_dir, a_folder))
        self.last_open_dir = self.last_open_dir.replace("//", "/")
        if self.last_open_dir != self.history[-1]:
            #don't keep more than one copy in history
            if self.last_open_dir in self.history:
                self.history.remove(self.last_open_dir)
            self.history.append(self.last_open_dir)
        self.folder_path_lineedit.setText(self.last_open_dir)
        f_list = os.listdir(self.last_open_dir)
        f_list.sort(key=str.lower)
        for f_file in f_list:
            f_full_path = "{}/{}".format(self.last_open_dir, f_file)
            if  not f_file.startswith("."):
                if os.path.isdir(f_full_path):
                    self.list_folder.addItem(f_file)
                elif pydaw_util.is_audio_file(f_file) and \
                os.path.isfile(f_full_path):
                    if not pydaw_util.pydaw_str_has_bad_chars(f_full_path):
                        self.list_file.addItem(f_file)
                    else:
                        QtGui.QMessageBox.warning(_(
                        "Not adding '{}' because it contains bad chars, "
                        "you must rename this file path without:\n{}").format(
                        f_full_path, "\n".join(pydaw_util.pydaw_bad_chars)))
        self.on_filter_files()
        self.on_filter_folders()

    def select_file(self, a_file):
        """ Select the file if present in the list, a_file should be
            a file name, not a full path
        """
        for f_i in range(self.list_file.count()):
            f_item = self.list_file.item(f_i)
            if str(f_item.text()) == str(a_file):
                self.list_file.setCurrentRow(f_i)
                break

    def files_selected(self):
        f_result = []
        for f_file in self.list_file.selectedItems():
            f_result.append("{}/{}".format(self.last_open_dir, f_file.text()))
        return f_result


class pydaw_file_browser_widget(pydaw_abstract_file_browser_widget):
    def __init__(self):
        pydaw_abstract_file_browser_widget.__init__(self)
        self.load_button = QtGui.QPushButton(_("Load"))
        self.file_hlayout.addWidget(self.load_button)
        self.list_file.setSelectionMode(QtGui.QListWidget.ExtendedSelection)

PYSOUND_FOLDER = "{}/presets".format(pydaw_util.global_pydaw_home)

class pysound_file:
    """ Pre-production, work in progress... """
    def __init__(self, **kwargs):
        self.name = None
        self.hash = None
        self.tags = []
        self.plugin = None
        self.version = []
        self.control_dict = {}
        assert(len(kwargs) == 1)
        if "a_path" in kwargs:
            with open(kwargs["a_path"], 'r') as f_file:
                self.string = f_file.read()
            self.string_to_data()
        elif "a_string" in kwargs:
            self.string = kwargs["a_string"]
            self.string_to_data()

    def string_to_data(self):
        for f_line in self.string.split("\n"):
            if f_line == "\\":
                break
            k, v = f_line.split("|")
            if k == "name":
                self.name = v
            elif k == "tag":
                self.tags.append(v)
            elif k == "hash":
                self.hash = v
            elif k == "plugin":
                self.plugin = v
            elif k == "version":
                self.version.append(v)
            else:
                self.control_dict[int(k)] = int(v)

    def data_to_string(self):
        f_result = ""
        raise NotImplementedError()
        return f_result

    def save_to_file(self, a_path):
        pass

class pysound_index:
    def __init__(self, a_plugin):
        pass

class pysound_indices:
    def __init__(self):
        self.tag_dict = {}

class pydaw_preset_browser_widget:
    """ To eventually replace the legacy preset system """
    def __init__(self, a_plugin_name, a_configure_dict=None,
                 a_reconfigure_callback=None):
        self.plugin_name = str(a_plugin_name)
        self.configure_dict = a_configure_dict
        self.reconfigure_callback = a_reconfigure_callback
        self.widget = QtGui.QWidget()
        self.widget.setObjectName("plugin_groupbox")
        self.main_vlayout = QtGui.QVBoxLayout(self.widget)
        self.hlayout1 = QtGui.QHBoxLayout()
        self.menu_button = QtGui.QPushButton(_("Menu"))
        self.hlayout1.addWidget(self.menu_button)
        self.menu = QtGui.QMenu(self.menu_button)
        self.menu_button.setMenu(self.menu)
        self.reload_action = self.menu.addAction(_("Reload"))
        self.reload_action.triggered.connect(self.on_reload)
        self.main_vlayout.addLayout(self.hlayout1)
        self.hlayout2 = QtGui.QHBoxLayout()
        self.main_vlayout.addLayout(self.hlayout2)
        self.tag_list = QtGui.QListWidget()
        self.hlayout2.addWidget(self.tag_list)

    def on_reload(self):
        pass

PEAK_GRADIENT_CACHE = {}

def peak_meter_gradient(a_height):
    if a_height not in PEAK_GRADIENT_CACHE:
        f_gradient = QtGui.QLinearGradient(0.0, 0.0, 0.0, a_height)
        f_gradient.setColorAt(0.0, QtGui.QColor.fromRgb(255, 0, 0))
        f_gradient.setColorAt(0.0333, QtGui.QColor.fromRgb(255, 0, 0))
        f_gradient.setColorAt(0.05, QtGui.QColor.fromRgb(150, 255, 0))
        f_gradient.setColorAt(0.2, QtGui.QColor.fromRgb(90, 255, 0))
        f_gradient.setColorAt(0.4, QtGui.QColor.fromRgb(0, 255, 0))
        f_gradient.setColorAt(0.7, QtGui.QColor.fromRgb(0, 255, 0))
        f_gradient.setColorAt(1.0, QtGui.QColor.fromRgb(0, 210, 180))
        PEAK_GRADIENT_CACHE[a_height] = f_gradient
    return PEAK_GRADIENT_CACHE[a_height]

class peak_meter:
    def __init__(self, a_width=14, a_text=False):
        self.text = a_text
        self.widget = QtGui.QWidget()
        self.widget.setFixedWidth(a_width)
        self.set_value([0.0, 0.0])
        self.widget.setStyleSheet("background-color: black;")
        self.widget.paintEvent = self.paint_event
        self.high = 0.0
        self.set_tooltip()
        self.widget.mousePressEvent = self.reset_high
        self.white_pen = QtGui.QPen(QtCore.Qt.white, 1.0)

    def set_value(self, a_vals):
        self.values = [float(x) for x in a_vals]
        self.widget.update()

    def reset_high(self, a_val=None):
        self.high = 0.0
        self.set_tooltip()

    def set_tooltip(self):
        if self.high == 0:
            f_val = -100.0
        else:
            f_val = round(pydaw_util.pydaw_lin_to_db(self.high), 1)
        self.widget.setToolTip(
            _("Peak {}dB\nClick with mouse to reset").format(f_val))

    def paint_event(self, a_ev):
        p = QtGui.QPainter(self.widget)
        p.setBackground(QtCore.Qt.black)
        p.setPen(QtCore.Qt.NoPen)
        f_height = self.widget.height()
        p.setBrush(peak_meter_gradient(f_height))
        f_rect_width = self.widget.width() * 0.5

        for f_val, f_i in zip(self.values, range(2)):
            if f_val == 0.0:
                continue
            elif f_val > 1.0:
                f_rect_y = 0.0
                f_rect_height = f_height
            else:
                f_db = pydaw_util.pydaw_lin_to_db(f_val)
                f_db = pydaw_util.pydaw_clip_min(f_db, -29.0)
                f_rect_y = f_height * f_db * -0.033333333 # / -30.0
                f_rect_height = f_height - f_rect_y
            if f_val > self.high:
                self.high = f_val
                self.set_tooltip()
            f_rect_x = f_i * f_rect_width
            f_rect = QtCore.QRectF(
                f_rect_x, f_rect_y, f_rect_width, f_rect_height)
            p.drawRect(f_rect)

        if self.text:
            p.setPen(self.white_pen)
            for f_y, f_db in zip(
            range(0, int(f_height), int(f_height * 0.2)), # / 5.0
            range(0, -30, -6)):
                p.drawText(3, f_y, str(-f_db))

PRESET_FILE_DIALOG_STRING = 'MusiKernel Presets (*.mkp)'
BM_FILE_DIALOG_STRING = 'MusiKernel Bookmarks (*.pybm4)'
PLUGIN_SETTINGS_CLIPBOARD = {}
PLUGIN_CONFIGURE_CLIPBOARD = None

class pydaw_preset_manager_widget:
    def __init__(self, a_plugin_name, a_configure_dict=None,
                 a_reconfigure_callback=None):
        self.suppress_change = False
        self.plugin_name = str(a_plugin_name)
        self.configure_dict = a_configure_dict
        self.reconfigure_callback = a_reconfigure_callback
        self.factory_preset_path = "{}/lib/{}/presets/{}.mkp".format(
            pydaw_util.global_pydaw_install_prefix,
            pydaw_util.global_pydaw_version_string, a_plugin_name)
        self.bank_dir = "{}/{}".format(pydaw_util.PRESET_DIR, a_plugin_name)
        if not os.path.isdir(self.bank_dir):
            os.makedirs(self.bank_dir)
        self.user_factory_presets = "{}/factory.mkp".format(self.bank_dir)
        self.bank_file = "{}/{}-last-bank.txt".format(
            pydaw_util.PRESET_DIR, a_plugin_name)
        self.group_box = QtGui.QWidget()
        self.group_box.setObjectName("plugin_groupbox")
        self.layout = QtGui.QHBoxLayout(self.group_box)
        self.layout.addWidget(QtGui.QLabel(_("Bank")))
        self.bank_combobox = QtGui.QComboBox()
        self.bank_combobox.setMinimumWidth(210)
        self.layout.addWidget(self.bank_combobox)
        self.layout.addWidget(QtGui.QLabel(_("Presets")))
        self.layout.setMargin(3)
        self.program_combobox = QtGui.QComboBox()
        self.program_combobox.setEditable(True)
        self.program_combobox.setMinimumWidth(300)
        self.layout.addWidget(self.program_combobox)
        self.save_button = QtGui.QPushButton("Save")
        self.save_button.setToolTip(
            _("Save the current settings to a preset.  "
            "Plugin settings are saved to the project automatically\n"
            "when you close the plugin window, this button is only for "
            "presets."))
        self.save_button.pressed.connect(self.save_presets)
        self.layout.addWidget(self.save_button)
        self.more_button = QtGui.QPushButton(_("Menu"))

        self.more_menu = QtGui.QMenu(self.more_button)

        f_new_bank_action = self.more_menu.addAction(_("New Bank..."))
        f_new_bank_action.triggered.connect(self.on_new_bank)
        f_reload_bank_action = self.more_menu.addAction(_("Reload Bank..."))
        f_reload_bank_action.triggered.connect(self.reload_default_presets)
        f_save_as_action = self.more_menu.addAction(_("Save Bank As..."))
        f_save_as_action.triggered.connect(self.on_save_as)
        f_open_action = self.more_menu.addAction(_("Open Bank..."))
        f_open_action.triggered.connect(self.on_open_bank)
        f_restore_action = self.more_menu.addAction(
            _("Restore Factory Bank..."))
        f_restore_action.triggered.connect(self.on_restore_bank)
        self.more_menu.addSeparator()
        f_delete_action = self.more_menu.addAction(_("Delete Preset"))
        f_delete_action.triggered.connect(self.delete_preset)
        self.more_menu.addSeparator()
        f_copy_action = self.more_menu.addAction(_("Copy Plugin Settings"))
        f_copy_action.triggered.connect(self.on_copy)
        f_paste_action = self.more_menu.addAction(_("Paste Plugin Settings"))
        f_paste_action.triggered.connect(self.on_paste)
        self.more_menu.addSeparator()
        f_reset_default_action = self.more_menu.addAction(
            _("Reset to Default Values"))
        f_reset_default_action.triggered.connect(self.reset_controls)

        self.more_button.setMenu(self.more_menu)
        self.layout.addWidget(self.more_button)
        self.presets_delimited = {}
        self.controls = {}
        self.suppress_bank_changes = False
        self.load_default_preset_path()
        self.load_banks()
        self.load_presets()
        self.program_combobox.currentIndexChanged.connect(
            self.program_changed)
        self.bank_combobox.currentIndexChanged.connect(
            self.bank_changed)

    def delete_preset(self):
        f_name = self.program_combobox.currentText()
        if f_name:
            f_name = str(f_name)
        print(f_name)
        if f_name and f_name in self.presets_delimited:
            print("Found preset, deleting")
            self.presets_delimited.pop(f_name)
            self.program_combobox.clearEditText()
            self.commit_presets()

    def load_banks(self):
        if not os.path.isfile(self.user_factory_presets):
            os.system("cp -f '{}' '{}'".format(
                self.factory_preset_path, self.user_factory_presets))
        self.bank_combobox.clear()
        self.bank_combobox.addItems(
            sorted(x.rsplit(".", 1)[0]
                for x in os.listdir(self.bank_dir) if x.endswith(".mkp")))
        self.suppress_bank_changes = True
        self.bank_combobox.setCurrentIndex(
            self.bank_combobox.findText(self.bank_name))
        self.suppress_bank_changes = False

    def bank_changed(self, a_val=None):
        if self.suppress_bank_changes:
            return
        self.preset_path = "{}/{}.mkp".format(
            self.bank_dir, self.bank_combobox.currentText())
        pydaw_util.pydaw_write_file_text(self.bank_file, self.preset_path)
        self.load_presets()

    def load_default_preset_path(self):
        self.preset_path = self.user_factory_presets
        if os.path.isfile(self.bank_file):
            f_text = pydaw_util.pydaw_read_file_text(self.bank_file)
            if os.path.isfile(f_text):
                print("Setting self.preset_path to {}".format(f_text))
                self.preset_path = f_text
                self.bank_name = f_text.rsplit("/", 1)[1].rsplit(".", 1)[0]
                return
            else:
                print("{} does not exist".format(f_text))
        else:
            print("{} does not exist".format(self.bank_file))
        self.bank_name = "factory"

    def reload_default_presets(self):
        self.load_default_preset_path()
        self.load_presets()

    def on_copy(self):
        f_result = {}
        for k, v in self.controls.items():
            f_result[k] = v.get_value()
        PLUGIN_SETTINGS_CLIPBOARD[self.plugin_name] = f_result
        global PLUGIN_CONFIGURE_CLIPBOARD
        if self.configure_dict is None:
            PLUGIN_CONFIGURE_CLIPBOARD = None
        else:
            PLUGIN_CONFIGURE_CLIPBOARD = self.configure_dict.copy()

    def on_paste(self):
        if not self.plugin_name in PLUGIN_SETTINGS_CLIPBOARD:
            QtGui.QMessageBox.warning(
                self.group_box, _("Error"),
                _("Nothing copied to clipboard for {}").format(
                self.plugin_name))
            return
        f_dict = PLUGIN_SETTINGS_CLIPBOARD[self.plugin_name]
        for k, v in f_dict.items():
            self.controls[k].set_value(v, True)
        if PLUGIN_CONFIGURE_CLIPBOARD is not None:
            self.reconfigure_callback(PLUGIN_CONFIGURE_CLIPBOARD)

    def on_new_bank(self):
        self.on_save_as(True)

    def on_save_as(self, a_new=False):
        def ok_handler():
            f_name = pydaw_util.pydaw_remove_bad_chars(f_lineedit.text())
            f_file = "{}/{}".format(self.bank_dir, f_name)
            if not f_file.endswith(".mkp"):
                f_file += ".mkp"
            if os.path.exists(f_file):
                QtGui.QMessageBox.warning(
                    self.group_box, _("Error"),
                    _("This bank name already exists"))
                return
            if a_new:
                pydaw_util.pydaw_write_file_text(
                    f_file, "\n".join([self.plugin_name]))
            else:
                os.system("cp -f '{}' '{}'".format(self.preset_path, f_file))
            self.preset_path = f_file
            pydaw_util.pydaw_write_file_text(self.bank_file, self.preset_path)
            self.load_banks()
            self.program_combobox.setCurrentIndex(
                self.program_combobox.findText(f_name))


        f_dialog = QtGui.QDialog(self.group_box)
        f_dialog.setWindowTitle(_("Save Bank"))
        f_groupbox_layout = QtGui.QGridLayout(f_dialog)
        f_groupbox_layout.addWidget(QtGui.QLabel(_("Name")), 0, 0)
        f_lineedit = QtGui.QLineEdit()
        f_groupbox_layout.addWidget(f_lineedit, 0, 1)
        f_sync_button = QtGui.QPushButton(_("OK"))
        f_sync_button.pressed.connect(ok_handler)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(f_dialog.close)
        f_groupbox_layout.addWidget(f_cancel_button, 2, 0)
        f_groupbox_layout.addWidget(f_sync_button, 2, 1)
        f_dialog.exec_()

    def on_open_bank(self):
        f_file = QtGui.QFileDialog.getOpenFileName(
            parent=self.group_box, caption=_('Open preset bank...'),
            directory=pydaw_util.global_home,
            filter=PRESET_FILE_DIALOG_STRING)
        if not f_file is None and not str(f_file) == "":
            f_file = str(f_file)
            self.preset_path = f_file
            pydaw_util.pydaw_write_file_text(self.bank_file, self.preset_path)
            self.program_combobox.setCurrentIndex(0)
            self.load_presets()

    def on_restore_bank(self):
        os.system("cp -f '{}' '{}'".format(
            self.factory_preset_path, self.user_factory_presets))
        self.preset_path = self.user_factory_presets
        self.bank_name = "factory"
        self.load_banks()
        self.load_presets()

    def reset_controls(self):
        for v in self.controls.values():
            v.reset_default_value()
        if self.reconfigure_callback is not None:
            self.reconfigure_callback({})

    def load_presets(self):
        if os.path.isfile(self.preset_path):
            print("loading presets from file {}".format(self.preset_path))
            f_text = pydaw_util.pydaw_read_file_text(self.preset_path)
        else:
            print("loading factory presets")
            f_text = pydaw_util.pydaw_read_file_text(
                self.user_factory_presets)
        f_line_arr = f_text.split("\n")

        if f_line_arr[0].strip() != self.plugin_name:
            QtGui.QMessageBox.warning(
                self.group_box, _("Error"),
                _("The selected preset bank is for {}, please select "
                "one for {}").format(
            f_line_arr[0], self.plugin_name))
            if os.path.isfile(self.bank_file):
                os.system('rm "{}"'.format(self.bank_file))
            return

        f_line_arr = f_line_arr[1:]
        self.presets_delimited = {}
        self.program_combobox.clear()
        self.program_combobox.addItem("")

        for f_line in f_line_arr:
            f_arr = f_line.split("|")
            f_name = f_arr[0]
            if f_name and f_name != "empty":  # legacy bank support
                self.presets_delimited[f_name] = f_arr[1:]
                self.program_combobox.addItem(f_name)

    def save_presets(self):
        print("saving preset")
        f_index = self.program_combobox.currentIndex()
        f_preset_name = str(self.program_combobox.currentText())
        if not f_index and not f_preset_name:
            QtGui.QMessageBox.warning(
                self.group_box, _("Error"),
                _("You must name the preset"))
            return
        f_result_values = []
        for k in sorted(self.controls.keys()):
            f_control = self.controls[k]
            f_result_values.append(
                "{}:{}".format(f_control.port_num, f_control.get_value()))
        if self.configure_dict is not None:
            for k in self.configure_dict.keys():
                v = self.configure_dict[k]
                f_result_values.append(
                    "c:{}:{}".format(k, v.replace("|", ":")))

        self.presets_delimited[f_preset_name] = f_result_values
        self.commit_presets()
        self.suppress_change = True
        self.program_combobox.setCurrentIndex(
            self.program_combobox.findText(f_preset_name))
        self.suppress_change = False

    def commit_presets(self):
        f_presets = "\n".join("|".join([x] + self.presets_delimited[x])
            for x in sorted(self.presets_delimited, key=lambda s: s.lower()))
        f_result = "{}\n{}".format(self.plugin_name, f_presets)
        pydaw_util.pydaw_write_file_text(self.preset_path, f_result)
        self.load_presets()

    def program_changed(self, a_val=None):
        if not a_val or self.suppress_change:
            return
        f_key = str(self.program_combobox.currentText())
        if not f_key:
            return
        f_preset = self.presets_delimited[f_key]
        f_preset_dict = {}
        f_configure_dict = {}
        for f_kvp in f_preset:
            f_list = f_kvp.split(":")
            if f_list[0] == "c":
                f_configure_dict[f_list[1]] = "|".join(f_list[2:])
            else:
                f_preset_dict[int(f_list[0])] = int(f_list[1])

        for k, v in self.controls.items():
            if int(k) in f_preset_dict:
                v.set_value(f_preset_dict[k], True)
            else:
                v.reset_default_value()
        if self.reconfigure_callback is not None:
            self.reconfigure_callback(f_configure_dict)

    def add_control(self, a_control):
        self.controls[a_control.port_num] = a_control

class pydaw_master_widget:
    def __init__(self, a_size, a_rel_callback, a_val_callback, a_vol_port,
                 a_glide_port, a_pitchbend_port, a_port_dict,
                 a_title=_("Master"), a_uni_voices_port=None,
                 a_uni_spread_port=None, a_preset_mgr=None, a_poly_port=None,
                 a_min_note_port=None, a_max_note_port=None):
        self.group_box = QtGui.QGroupBox()
        self.group_box.setObjectName("plugin_groupbox")
        self.group_box.setTitle(str(a_title))
        self.layout = QtGui.QGridLayout(self.group_box)
        self.layout.setMargin(3)
        self.vol_knob = pydaw_knob_control(
            a_size, _("Vol"), a_vol_port, a_rel_callback, a_val_callback, -30,
            12, -6, KC_INTEGER, a_port_dict, a_preset_mgr)
        self.vol_knob.add_to_grid_layout(self.layout, 0)
        if a_uni_voices_port is not None and a_uni_spread_port is not None:
            self.uni_voices_knob = pydaw_knob_control(
                a_size, _("Unison"), a_uni_voices_port,
                a_rel_callback, a_val_callback, 1, 7, 4, KC_INTEGER,
                a_port_dict, a_preset_mgr)
            self.uni_voices_knob.add_to_grid_layout(self.layout, 1)
            self.uni_spread_knob = pydaw_knob_control(
                a_size, _("Spread"), a_uni_spread_port,
                a_rel_callback, a_val_callback,
                10, 100, 50, KC_DECIMAL, a_port_dict, a_preset_mgr)
            self.uni_spread_knob.add_to_grid_layout(self.layout, 2)
        self.glide_knob = pydaw_knob_control(
            a_size, _("Glide"), a_glide_port,
            a_rel_callback, a_val_callback,
            0, 200, 0, KC_TIME_DECIMAL, a_port_dict, a_preset_mgr)
        self.glide_knob.add_to_grid_layout(self.layout, 3)
        self.pb_knob = pydaw_knob_control(
            a_size, _("Pitchbend"), a_pitchbend_port,
            a_rel_callback, a_val_callback, 1, 36, 18,
            KC_INTEGER, a_port_dict, a_preset_mgr)
        self.pb_knob.add_to_grid_layout(self.layout, 4)
        if a_poly_port is not None:
            self.mono_combobox = pydaw_combobox_control(
                90, "Poly Mode", a_poly_port, a_rel_callback, a_val_callback,
                ["Retrig.", "Free", "Mono", "Mono2"],
                a_port_dict, 0, a_preset_mgr)
            self.mono_combobox.add_to_grid_layout(self.layout, 5)
        if a_min_note_port or a_max_note_port:
            assert(a_min_note_port and a_max_note_port)
            self.min_note = pydaw_note_selector_widget(
                a_min_note_port, a_rel_callback, a_val_callback, a_port_dict,
                0, a_preset_mgr)
            self.max_note = pydaw_note_selector_widget(
                a_max_note_port, a_rel_callback, a_val_callback, a_port_dict,
                120, a_preset_mgr)
            self.layout.addWidget(
                QtGui.QLabel(_("Range")), 0, 9,
                alignment=QtCore.Qt.AlignHCenter)
            self.layout.addWidget(self.min_note.widget, 1, 9)
            self.layout.addWidget(self.max_note.widget, 2, 9)


EQ_POINT_DIAMETER = 12.0
EQ_POINT_RADIUS = EQ_POINT_DIAMETER * 0.5
EQ_WIDTH = 600
EQ_HEIGHT = 300
EQ_OCTAVE_PX = (EQ_WIDTH / (100.0 / 12.0))

EQ_LOW_PITCH = 4
EQ_HIGH_PITCH = 123

EQ_GRADIENT = QtGui.QLinearGradient(0, 0, EQ_POINT_DIAMETER, EQ_POINT_DIAMETER)
EQ_GRADIENT.setColorAt(0, QtGui.QColor(255, 255, 255))
EQ_GRADIENT.setColorAt(1, QtGui.QColor(240, 240, 240))

EQ_FILL = QtGui.QLinearGradient(0.0, 0.0, 0.0, EQ_HEIGHT)

EQ_FILL.setColorAt(0.0, QtGui.QColor(255, 0, 0, 90)) #red
EQ_FILL.setColorAt(0.14285, QtGui.QColor(255, 123, 0, 90)) #orange
EQ_FILL.setColorAt(0.2857, QtGui.QColor(255, 255, 0, 90)) #yellow
EQ_FILL.setColorAt(0.42855, QtGui.QColor(0, 255, 0, 90)) #green
EQ_FILL.setColorAt(0.5714, QtGui.QColor(0, 123, 255, 90)) #blue
EQ_FILL.setColorAt(0.71425, QtGui.QColor(0, 0, 255, 90)) #indigo
EQ_FILL.setColorAt(0.8571, QtGui.QColor(255, 0, 255, 90)) #violet

EQ_BACKGROUND = QtGui.QLinearGradient(0.0, 0.0, 0.0, EQ_HEIGHT)

EQ_BACKGROUND.setColorAt(0.0, QtGui.QColor(40, 40, 40))
EQ_BACKGROUND.setColorAt(0.1, QtGui.QColor(20, 20, 20))
EQ_BACKGROUND.setColorAt(0.9, QtGui.QColor(30, 30, 30))
EQ_BACKGROUND.setColorAt(1.0, QtGui.QColor(40, 40, 40))

class eq_item(QtGui.QGraphicsEllipseItem):
    def __init__(self, a_eq, a_num, a_val_callback):
        QtGui.QGraphicsEllipseItem.__init__(
            self, 0, 0, EQ_POINT_DIAMETER, EQ_POINT_DIAMETER)
        self.val_callback = a_val_callback
        self.eq = a_eq
        self.num = a_num
        self.setToolTip("EQ{}".format(self.num))
        self.setBrush(EQ_GRADIENT)
        self.mapToScene(0.0, 0.0)
        self.path_item = None
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)

    def mouseMoveEvent(self, a_event):
        QtGui.QGraphicsEllipseItem.mouseMoveEvent(self, a_event)
        f_pos = self.pos()
        f_pos_x = pydaw_util.pydaw_clip_value(
            f_pos.x(), -EQ_POINT_RADIUS, EQ_WIDTH)
        f_pos_y = pydaw_util.pydaw_clip_value(
            f_pos.y(), -EQ_POINT_RADIUS, EQ_HEIGHT)

        if f_pos_x != f_pos.x() or f_pos_y != f_pos.y():
            self.setPos(f_pos_x, f_pos_y)

        f_freq, f_gain = self.get_value()
        self.val_callback(self.eq.freq_knob.port_num, f_freq)
        self.val_callback(self.eq.gain_knob.port_num, f_gain)
        self.eq.freq_knob.set_value(f_freq)
        self.eq.gain_knob.set_value(f_gain)
        self.draw_path_item()

    def mouseReleaseEvent(self, a_event):
        QtGui.QGraphicsEllipseItem.mouseReleaseEvent(self, a_event)
        self.eq.freq_knob.control_value_changed(self.eq.freq_knob.get_value())
        self.eq.gain_knob.control_value_changed(self.eq.gain_knob.get_value())

    def set_pos(self):
        f_freq = self.eq.freq_knob.get_value()
        f_gain = self.eq.gain_knob.get_value()
        f_x = (((f_freq - EQ_LOW_PITCH) / EQ_HIGH_PITCH) *
            EQ_WIDTH) - EQ_POINT_RADIUS
        f_y = ((1.0 - ((f_gain + 240.0) / 480.0)) *
            EQ_HEIGHT) - EQ_POINT_RADIUS
        self.setPos(f_x, f_y)
        self.draw_path_item()

    def get_value(self):
        f_pos = self.pos()
        f_freq = (((f_pos.x() + EQ_POINT_RADIUS) / EQ_WIDTH) *
            EQ_HIGH_PITCH) + EQ_LOW_PITCH
        f_freq = pydaw_util.pydaw_clip_value(
            f_freq, EQ_LOW_PITCH, EQ_HIGH_PITCH)
        f_gain = ((1.0 - ((f_pos.y() + EQ_POINT_RADIUS) /
            EQ_HEIGHT)) * 480.0) - 240.0
        f_gain = pydaw_util.pydaw_clip_value(f_gain, -240.0, 240.0)
        return round(f_freq, 2), round(f_gain, 1)

    def __lt__(self, other):
        return self.pos().x() < other.pos().x()

    def draw_path_item(self):
        f_res = self.eq.res_knob.get_value()

        if self.path_item is not None:
            self.scene().removeItem(self.path_item)

        f_line_pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 210), 2.0)
        f_path = QtGui.QPainterPath()

        f_pos = self.pos()
        f_bw = (f_res * 0.01)
        f_point_x = f_pos.x() + EQ_POINT_RADIUS
        f_point_y = f_pos.y() + EQ_POINT_RADIUS
        f_start_x = f_point_x - ((f_bw * 0.5 * EQ_OCTAVE_PX))
        f_end_x = f_point_x + ((f_bw * 0.5 * EQ_OCTAVE_PX))

        f_path.moveTo(f_start_x, EQ_HEIGHT * 0.5)

        f_path.lineTo(f_point_x, f_point_y)

        f_path.lineTo(f_end_x, EQ_HEIGHT * 0.5)

        self.path_item = QtGui.QGraphicsPathItem(f_path)
        self.path_item.setPen(f_line_pen)
        self.path_item.setBrush(EQ_FILL)
        self.scene().addItem(self.path_item)


class eq_viewer(QtGui.QGraphicsView):
    def __init__(self, a_val_callback):
        QtGui.QGraphicsView.__init__(self)
        self.val_callback = a_val_callback
        self.eq_points = []
        self.scene = QtGui.QGraphicsScene(self)
        self.scene.setBackgroundBrush(EQ_BACKGROUND)
        self.setScene(self.scene)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter)
        self.last_x_scale = 1.0
        self.last_y_scale = 1.0
        self.eq_points = []
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setSceneRect(-EQ_POINT_RADIUS, -EQ_POINT_RADIUS,
                          EQ_WIDTH + EQ_POINT_RADIUS,
                          EQ_HEIGHT + EQ_POINT_DIAMETER)

    def set_spectrum(self, a_message):
        self.spectrum.set_spectrum(a_message)

    def draw_eq(self, a_eq_list=[]):
        f_hline_pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 90), 1.0)
        f_vline_pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 150), 2.0)

        f_label_pos = 0.0

        self.scene.clear()
        self.spectrum = pydaw_spectrum(EQ_HEIGHT, EQ_WIDTH)
        self.scene.addItem(self.spectrum)

        f_y_pos = 0.0
        f_db = 24.0
        f_inc = (EQ_HEIGHT * 0.5) * 0.25

        for i in range(4):
            self.scene.addLine(
                0.0, f_y_pos, EQ_WIDTH, f_y_pos, f_hline_pen)
            f_label = QtGui.QGraphicsSimpleTextItem(
                "{}".format(f_db), scene=self.scene)
            f_label.setPos(EQ_WIDTH - 36.0, f_y_pos + 3.0)
            f_label.setBrush(QtCore.Qt.white)
            f_db -= 6.0
            f_y_pos += f_inc

        self.scene.addLine(
            0.0, EQ_HEIGHT * 0.5, EQ_WIDTH,
            EQ_HEIGHT * 0.5,
            QtGui.QPen(QtGui.QColor(255, 255, 255, 210), 2.0))

        f_y_pos = EQ_HEIGHT
        f_db = -24.0

        for i in range(4):
            self.scene.addLine(
                0.0, f_y_pos, EQ_WIDTH, f_y_pos, f_hline_pen)
            f_label = QtGui.QGraphicsSimpleTextItem(
                "{}".format(f_db), scene=self.scene)
            f_label.setPos(EQ_WIDTH - 36.0, f_y_pos - 24.0)
            f_label.setBrush(QtCore.Qt.white)
            f_db += 6.0
            f_y_pos -= f_inc

        f_label_pos = 0.0
        f_pitch = EQ_LOW_PITCH
        f_pitch_inc = 17.0
        f_label_inc = EQ_WIDTH / (EQ_HIGH_PITCH / f_pitch_inc)

        for i in range(7):
            f_hz = int(pydaw_util.pydaw_pitch_to_hz(f_pitch))
            if f_hz > 950:
                f_hz = round(f_hz, -1)
                f_hz = "{}khz".format(round(f_hz / 1000, 1))
            f_label = QtGui.QGraphicsSimpleTextItem(
                "{}".format(f_hz), scene=self.scene)
            f_label.setPos(f_label_pos + 4.0, EQ_HEIGHT - 30.0)
            self.scene.addLine(
                f_label_pos, 0.0, f_label_pos, EQ_HEIGHT, f_vline_pen)
            f_label.setBrush(QtCore.Qt.white)
            f_label_pos += f_label_inc
            f_pitch += f_pitch_inc

        self.eq_points = []

        for f_eq, f_num in zip(a_eq_list, range(1, len(a_eq_list) + 1)):
            f_eq_point = eq_item(f_eq, f_num, self.val_callback)
            self.eq_points.append(f_eq_point)
            self.scene.addItem(f_eq_point)
            f_eq_point.set_pos()


    def resizeEvent(self, a_resize_event):
        QtGui.QGraphicsView.resizeEvent(self, a_resize_event)
        self.scale(1.0 / self.last_x_scale, 1.0 / self.last_y_scale)
        f_rect = self.rect()
        self.last_x_scale = f_rect.width() / (EQ_WIDTH +
            EQ_POINT_DIAMETER + 3.0)
        self.last_y_scale = f_rect.height() / (EQ_HEIGHT +
            EQ_POINT_DIAMETER + 3.0)
        self.scale(self.last_x_scale, self.last_y_scale)



class eq_widget:
    def __init__(self, a_number, a_freq_port, a_res_port,
                 a_gain_port, a_rel_callback,
                 a_val_callback, a_default_value, a_port_dict=None,
                 a_preset_mgr=None, a_size=48):
        self.groupbox = QtGui.QGroupBox("EQ{}".format(a_number))
        self.groupbox.setObjectName("plugin_groupbox")
        self.layout = QtGui.QGridLayout(self.groupbox)

        self.freq_knob = pydaw_knob_control(
            a_size, "Freq", a_freq_port, a_rel_callback,
            a_val_callback, EQ_LOW_PITCH, EQ_HIGH_PITCH, a_default_value,
            KC_PITCH, a_port_dict, a_preset_mgr)
        self.freq_knob.add_to_grid_layout(self.layout, 0)

        self.res_knob = pydaw_knob_control(
            a_size, "BW", a_res_port, a_rel_callback,
            a_val_callback, 100.0, 600.0, 300.0, KC_DECIMAL,
            a_port_dict, a_preset_mgr)
        self.res_knob.add_to_grid_layout(self.layout, 1)

        self.gain_knob = pydaw_knob_control(
            a_size, _("Gain"), a_gain_port, a_rel_callback,
            a_val_callback, -240.0, 240.0, 0.0, KC_TENTH,
            a_port_dict, a_preset_mgr)
        self.gain_knob.add_to_grid_layout(self.layout, 2)

EQ6_CLIPBOARD = None

EQ6_FORMANTS = {
    "soprano a":((800, 1150, 2900, 3900, 4950), (0, -6, -32, -20, -50),
                 (80, 90, 120, 130, 140)),
    "soprano e":((350, 2000, 2800, 3600, 4950), (0, -20, -15, -40, -56),
                 (60, 100, 120, 150, 200)),
    "soprano i":((270, 2140, 2950, 3900, 4950), (0, -12, -26, -26, -44),
                 (60, 90, 100, 120, 120)),
    "soprano o":((450, 800, 2830, 3800, 4950), (0, -11, -22, -22, -50),
                 (70, 80, 100, 130, 135)),
    "soprano u":((325, 700, 2700, 3800, 4950), (0, -16, -35, -40, -60),
                 (50, 60, 170, 180, 200)),
    "alto a":((800, 1150, 2800, 3500, 4950), (0, -4, -20, -36, -60),
              (80, 90, 120, 130, 140)),
    "alto e":((400, 1600, 2700, 3300, 4950), (0, -24, -30, -35, -60),
              (60, 80, 120, 150, 200)),
    "alto i":((350, 1700, 2700, 3700, 4950), (0, -20, -30, -36, -60),
              (50, 100, 120, 150, 200)),
    "alto o":((450, 800, 2830, 3500, 4950), (0, -9, -16, -28, -55),
              (70, 80, 100, 130, 135)),
    "alto u":((325, 700, 2530, 3500, 4950), (0, -12, -30, -40, -64),
              (50, 60, 170, 180, 200)),
    "countertenor a":((660, 1120, 2750, 3000, 3350), (0, -6, -23, -24, -38),
                      (80, 90, 120, 130, 140)),
    "countertenor e":((440, 1800, 2700, 3000, 3300), (0, -14, -18, -20, -20),
                      (70, 80, 100, 120, 120)),
    "countertenor i":((270, 1850, 2900, 3350, 3590), (0, -24, -24, -36, -36),
                      (40, 90, 100, 120, 120)),
    "countertenor o":((430, 820, 2700, 3000, 3300), (0, -10, -26, -22, -34),
                      (40, 80, 100, 120, 120)),
    "countertenor u":((370, 630, 2750, 3000, 3400), (0, -20, -23, -30, -34),
                      (40, 60, 100, 120, 120)),
    "tenor a":((650, 1080, 2650, 2900, 3250), (0, -6, -7, -8, -22),
               (80, 90, 120, 130, 140)),
    "tenor e":((400, 1700, 2600, 3200, 3580), (0, -14, -12, -14, -20),
               (70, 80, 100, 120, 120)),
    "tenor i":((290, 1870, 2800, 3250, 3540), (0, -15, -18, -20, -30),
               (40, 90, 100, 120, 120)),
    "tenor o":((400, 800, 2600, 2800, 3000), (0, -10, -12, -12, -26),
               (40, 80, 100, 120, 120)),
    "tenor u":((350, 600, 2700, 2900, 3300), (0, -20, -17, -14, -26),
               (40, 60, 100, 120, 120)),
    "bass a":((600, 1040, 2250, 2450, 2750), (0, -7, -9, -9, -20),
              (60, 70, 110, 120, 130)),
    "bass e":((400, 1620, 2400, 2800, 3100), (0, -12, -9, -12, -18),
              (40, 80, 100, 120, 120)),
    "bass i":((250, 1750, 2600, 3050, 3340), (0, -30, -16, -22, -28),
              (60, 90, 100, 120, 120)),
    "bass o":((400, 750, 2400, 2600, 2900), (0, -11, -21, -20, -40),
              (40, 80, 100, 120, 120)),
    "bass u":((350, 600, 2400, 2675, 2950), (0, -20, -32, -28, -36),
              (40, 80, 100, 120, 120))
}


class eq6_widget:
    def __init__(self, a_first_port, a_rel_callback, a_val_callback,
                 a_port_dict=None, a_preset_mgr=None,
                 a_size=48, a_vlayout=True):
        self.rel_callback = a_rel_callback
        self.val_callback = a_val_callback
        self.widget = QtGui.QWidget()
        self.widget.setObjectName("plugin_ui")
        self.eq_viewer = eq_viewer(a_val_callback)

        self.vlayout = QtGui.QVBoxLayout()
        self.combobox_hlayout = QtGui.QHBoxLayout()
        self.grid_layout = QtGui.QGridLayout()

        self.vlayout.addLayout(self.combobox_hlayout)
        self.vlayout.addWidget(self.eq_viewer)
        if a_vlayout:
            f_col_width = 3
            self.widget.setLayout(self.vlayout)
            self.vlayout.addLayout(self.grid_layout)
        else:
            f_col_width = 2
            self.hlayout = QtGui.QHBoxLayout(self.widget)
            self.hlayout.addLayout(self.vlayout)
            self.hlayout.addLayout(self.grid_layout)

        self.combobox_hlayout.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))

        self.menu_button = QtGui.QPushButton(_("Menu"))
        self.menu = QtGui.QMenu(self.menu_button)
        self.menu_button.setMenu(self.menu)
        self.copy_action = self.menu.addAction(_("Copy"))
        self.copy_action.triggered.connect(self.on_copy)
        self.paste_action = self.menu.addAction(_("Paste"))
        self.paste_action.triggered.connect(self.on_paste)
        self.menu.addSeparator()
        self.formant_menu = self.menu.addMenu(_("Set Formant"))
        self.formant_menu.triggered.connect(self.set_formant)
        for k in sorted(EQ6_FORMANTS.keys()):
            self.formant_menu.addAction(k)
        self.menu.addSeparator()
        self.reset_action = self.menu.addAction(_("Reset"))
        self.reset_action.triggered.connect(self.reset_controls)
        self.combobox_hlayout.addWidget(self.menu_button)

        self.eqs = []

        f_port = a_first_port
        f_default_value = 24

        f_x = 0
        f_y = 0

        for f_i in range(1, 7):
            f_eq = eq_widget(
                f_i, f_port, f_port + 1, f_port + 2,
                a_rel_callback, self.knob_callback,
                f_default_value, a_port_dict, a_preset_mgr, a_size)
            self.eqs.append(f_eq)
            self.grid_layout.addWidget(f_eq.groupbox, f_y, f_x)

            f_x += 1
            if f_x >= f_col_width:
                f_x = 0
                f_y += 1
            f_port += 3
            f_default_value += 18
        self.update_viewer()

    def set_formant(self, a_action):
        f_key = str(a_action.text())
        f_hz_list, f_db_list, f_bw_list = EQ6_FORMANTS[f_key]
        for f_eq, f_hz, f_db, f_bw in zip(
        self.eqs, f_hz_list, f_db_list, f_bw_list):
            f_pitch = pydaw_util.pydaw_hz_to_pitch(f_hz)
            f_eq.freq_knob.set_value(f_pitch, True)
            f_bw_adjusted = f_bw + 60
            f_eq.res_knob.set_value(f_bw_adjusted, True)
            f_db_adjusted = (f_db * 0.3) + 21.0
            f_eq.gain_knob.set_value(f_db_adjusted, True)

    def set_spectrum(self, a_message):
        self.eq_viewer.set_spectrum(a_message)

    def on_paste(self):
        global EQ6_CLIPBOARD
        if EQ6_CLIPBOARD is not None:
            for f_eq, f_tuple in zip(self.eqs, EQ6_CLIPBOARD):
                f_eq.freq_knob.set_value(f_tuple[0], True)
                f_eq.res_knob.set_value(f_tuple[1], True)
                f_eq.gain_knob.set_value(f_tuple[2], True)

    def on_copy(self):
        global EQ6_CLIPBOARD
        EQ6_CLIPBOARD = []
        for f_eq in self.eqs:
            EQ6_CLIPBOARD.append(
            (f_eq.freq_knob.get_value(),
            f_eq.res_knob.get_value(),
            f_eq.gain_knob.get_value())
            )

    def knob_callback(self, a_port, a_val):
        self.val_callback(a_port, a_val)
        self.update_viewer()

    def update_viewer(self):
        self.eq_viewer.draw_eq(self.eqs)

    def reset_controls(self):
        for f_eq in self.eqs:
            f_eq.freq_knob.reset_default_value()
            f_eq.res_knob.reset_default_value()
            f_eq.gain_knob.reset_default_value()

class morph_eq(eq6_widget):
    def __init__(self, a_first_port, a_rel_callback, a_val_callback,
                 a_port_dict=None, a_preset_mgr=None, a_size=48,
                 a_vlayout=True):
        raise NotImplementedError()
        self.rel_callback_orig = a_rel_callback
        self.val_callback_orig = a_val_callback
        eq6_widget.__init__(
            self, a_first_port, self.rel_callback_wrapper, a_val_callback,
            a_port_dict, a_preset_mgr, a_size, a_vlayout)
        self.eq_num_spinbox = QtGui.QSpinBox()
        self.eq_num_spinbox.setRange(1, 2)
        self.eq_num_spinbox.valueChanged.connect(self.eq_num_changed)
        self.eq_values = {}

    def eq_num_changed(self, a_val=None):
        self.eq_index = self.eq_num_spinbox.value() - 1

    def val_callback_wrapper(self):
        pass

    def rel_callback_wrapper(self):
        pass


ROUTING_GRAPH_NODE_GRADIENT = None
ROUTING_GRAPH_SELECTED_GRADIENT = None

class routing_graph_node(QtGui.QGraphicsRectItem):
    def __init__(self, a_text, a_width, a_height):
        QtGui.QGraphicsRectItem.__init__(self, 0, 0, a_width, a_height)
        self.text = QtGui.QGraphicsSimpleTextItem(a_text, self)
        self.text.setPos(3.0, 3.0)
        self.setPen(QtCore.Qt.black)
        self.set_brush()

    def set_brush(self, a_highlighted=False):
        self.setBrush(ROUTING_GRAPH_SELECTED_GRADIENT if a_highlighted
            else ROUTING_GRAPH_NODE_GRADIENT)


class routing_graph_widget(QtGui.QGraphicsView):
    def __init__(self, a_toggle_callback=None):
        QtGui.QGraphicsView.__init__(self)
        self.scene = QtGui.QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.setBackgroundBrush(QtCore.Qt.darkGray)
        self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.node_dict = {}
        self.setMouseTracking(True)
        self.toggle_callback = a_toggle_callback

    def get_coords(self, a_pos):
        f_x = int(a_pos.x() // self.node_width)
        f_y = int(a_pos.y() // self.node_height)
        return (f_x, f_y)

    def backgroundMousePressEvent(self, a_event):
        #QtGui.QGraphicsRectItem.mousePressEvent(self.background_item, a_event)
        if self.toggle_callback:
            f_x, f_y = self.get_coords(a_event.scenePos())
            if f_x == f_y or f_y == 0:
                return
            self.toggle_callback(
                f_y, f_x,
                1 if a_event.modifiers() == QtCore.Qt.ControlModifier else 0)

    def backgroundHoverEvent(self, a_event):
        QtGui.QGraphicsRectItem.hoverMoveEvent(self.background_item, a_event)
        f_x, f_y = self.get_coords(a_event.scenePos())
        if f_x == f_y or f_y == 0:
            self.clear_selection()
            return
        for k, v in self.node_dict.items():
            v.set_brush(k in (f_x, f_y))

    def backgroundHoverLeaveEvent(self, a_event):
        self.clear_selection()

    def clear_selection(self):
        for v in self.node_dict.values():
            v.set_brush(False)

    def draw_graph(self, a_graph, a_track_names):
        self.graph_height = self.height() - 36.0
        self.graph_width = self.width() - 36.0
        self.node_width = self.graph_width / 32.0
        self.node_height = self.graph_height / 32.0
        self.wire_width = self.node_height / 4.0  #max conns
        self.wire_width_div2 = self.wire_width * 0.5
        ROUTING_GRAPH_WIRE_INPUT = ((self.node_width * 0.5) -
            (self.wire_width * 0.5))

        f_line_pen = QtGui.QPen(QtGui.QColor(105, 105, 105))

        global ROUTING_GRAPH_NODE_GRADIENT, ROUTING_GRAPH_SELECTED_GRADIENT
        ROUTING_GRAPH_NODE_GRADIENT = QtGui.QLinearGradient(
            0.0, 0.0, 0.0, self.node_height)
        ROUTING_GRAPH_NODE_GRADIENT.setColorAt(0.0, QtGui.QColor(255, 255, 0))
        ROUTING_GRAPH_NODE_GRADIENT.setColorAt(0.1, QtGui.QColor(231, 231, 0))
        ROUTING_GRAPH_NODE_GRADIENT.setColorAt(0.8, QtGui.QColor(180, 180, 0))
        ROUTING_GRAPH_NODE_GRADIENT.setColorAt(1.0, QtGui.QColor(150, 150, 90))
        ROUTING_GRAPH_SELECTED_GRADIENT = QtGui.QLinearGradient(
            0.0, 0.0, 0.0, self.node_height)
        ROUTING_GRAPH_SELECTED_GRADIENT.setColorAt(
            0.0, QtGui.QColor(255, 160, 160))
        ROUTING_GRAPH_SELECTED_GRADIENT.setColorAt(
            0.1, QtGui.QColor(231, 160, 160))
        ROUTING_GRAPH_SELECTED_GRADIENT.setColorAt(
            0.8, QtGui.QColor(180, 160, 180))
        ROUTING_GRAPH_SELECTED_GRADIENT.setColorAt(
            1.0, QtGui.QColor(150, 140, 150))

        self.node_dict = {}
        f_wire_gradient = QtGui.QLinearGradient(
            0.0, 0.0, self.width(), self.height())
        f_wire_gradient.setColorAt(0.0, QtGui.QColor(250, 250, 255))
        f_wire_gradient.setColorAt(1.0, QtGui.QColor(210, 210, 222))
        f_wire_pen = QtGui.QPen(f_wire_gradient, self.wire_width_div2)
        f_sc_wire_pen = QtGui.QPen(QtCore.Qt.red, self.wire_width_div2)
        self.setUpdatesEnabled(False)
        self.scene.clear()
        self.background_item = QtGui.QGraphicsRectItem(
            0.0, 0.0, self.graph_width, self.graph_height)
        self.background_item.setBrush(QtCore.Qt.transparent)
        self.background_item.setPen(QtGui.QPen(QtCore.Qt.black))
        self.scene.addItem(self.background_item)
        self.background_item.hoverMoveEvent = self.backgroundHoverEvent
        self.background_item.hoverLeaveEvent = self.backgroundHoverLeaveEvent
        self.background_item.setAcceptHoverEvents(True)
        self.background_item.mousePressEvent = self.backgroundMousePressEvent
        for k, f_i in zip(a_track_names, range(len(a_track_names))):
            f_node_item = routing_graph_node(
                k, self.node_width,
                self.node_height)
            self.node_dict[f_i] = f_node_item
            self.scene.addItem(f_node_item)
            f_x = self.node_width * f_i
            f_y = self.node_height * f_i
            if f_i != 0:
                self.scene.addLine(
                    0.0, f_y, self.graph_width, f_y, f_line_pen)
                self.scene.addLine(
                    f_x, 0.0, f_x, self.graph_height, f_line_pen)
            f_node_item.setPos(f_x, f_y)
            if f_i == 0 or f_i not in a_graph.graph:
                continue
            f_connections = [(x.output, x.index, x.sidechain)
                for x in a_graph.graph[f_i].values()]
            for f_dest_pos, f_wire_index, f_sidechain in f_connections:
                f_pen = f_sc_wire_pen if f_sidechain else f_wire_pen
                if f_dest_pos > f_i:
                    f_src_x = f_x + self.node_width
                    f_y_wire_offset = (f_wire_index *
                        self.wire_width) + self.wire_width_div2
                    f_src_y = f_y + f_y_wire_offset
                    f_wire_width = ((f_dest_pos - f_i - 1) *
                        self.node_width) + ROUTING_GRAPH_WIRE_INPUT
                    f_v_wire_x = f_src_x + f_wire_width
                    if f_sidechain:
                        f_v_wire_x += self.wire_width_div2 * 2
                    else:
                        f_v_wire_x -= self.wire_width_div2 * 2
                    f_wire_height = ((f_dest_pos - f_i) *
                        self.node_height) - f_y_wire_offset
                    f_dest_y = f_src_y + f_wire_height
                    self.scene.addLine( # horizontal wire
                        f_src_x, f_src_y, f_v_wire_x, f_src_y, f_pen)
                    self.scene.addLine( # vertical wire
                        f_v_wire_x, f_src_y, f_v_wire_x, f_dest_y, f_pen)
                else:
                    f_src_x = f_x
                    f_y_wire_offset = (f_wire_index *
                        self.wire_width) + self.wire_width_div2
                    f_src_y = f_y + f_y_wire_offset
                    f_wire_width = ((f_i - f_dest_pos - 1) *
                        self.node_width) + ROUTING_GRAPH_WIRE_INPUT
                    f_v_wire_x = f_src_x - f_wire_width
                    if f_sidechain:
                        f_v_wire_x += self.wire_width_div2 * 2
                    else:
                        f_v_wire_x -= self.wire_width_div2 * 2
                    f_wire_height = ((f_i - f_dest_pos - 1) *
                        self.node_height) + f_y_wire_offset
                    f_dest_y = f_src_y - f_wire_height
                    self.scene.addLine( # horizontal wire
                        f_v_wire_x, f_src_y, f_src_x, f_src_y, f_pen)
                    self.scene.addLine( # vertical wire
                        f_v_wire_x, f_dest_y, f_v_wire_x, f_src_y, f_pen)

        self.setUpdatesEnabled(True)
        self.update()

class mixer_channel:
    def __init__(self, a_name):
        self.widget = QtGui.QWidget()
        self.vlayout = QtGui.QVBoxLayout(self.widget)
        self.sends = {}
        self.outputs = {}
        self.output_labels = {}
        self.name_label = QtGui.QLabel(a_name)
        self.vlayout.addWidget(self.name_label, -1, QtCore.Qt.AlignTop)
        self.grid_layout = QtGui.QGridLayout()
        self.vlayout.addLayout(self.grid_layout, 1)
        self.peak_meter = peak_meter(20, True)
        self.grid_layout.addWidget(self.peak_meter.widget, 1, 0)

    def clear(self):
        self.sends = {}
        self.outputs = {}
        self.output_labels = {}
        for i in reversed(range(1, self.grid_layout.count())):
            f_widget = self.grid_layout.itemAt(i).widget()
            self.grid_layout.removeWidget(f_widget)
            f_widget.setParent(None)

    def set_name(self, a_name, a_dict):
        self.name_label.setText(a_name)
        for k in self.outputs:
            self.output_labels[k].setText(a_dict[self.outputs[k]])

    def add_plugin(self, a_index, a_plugin, a_output):
        assert(a_index != -1)
        if a_index in self.sends:
            self.remove_plugin(a_index)
        self.sends[a_index] = a_plugin
        self.outputs[a_index] = a_output
        f_label = QtGui.QLabel(str(a_output))
        self.output_labels[a_index] = f_label
        self.grid_layout.addWidget(f_label, 0, a_index + 1)
        a_plugin.widget.setSizePolicy(
            QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Expanding)
        self.grid_layout.addWidget(a_plugin.widget, 1, a_index + 1)

    def remove_plugin(self, a_index):
        if a_index in self.sends:
            for f_widget in (
            self.sends.pop(a_index).widget, self.output_labels.pop(a_index)):
                self.grid_layout.removeWidget(f_widget)
                f_widget.setParent(None)

MIXER_TOOLTIP = _("""This is the mixer.
To add volume sliders, etc...  select a mixer plugin for each send on
each track that you wish to be able to control""")

class mixer_widget:
    def __init__(self, a_track_count):
        self.widget = QtGui.QScrollArea()
        self.widget.setWidgetResizable(True)
        self.main_widget = QtGui.QWidget()
        self.main_widget.setObjectName("plugin_ui")
        self.widget.setWidget(self.main_widget)
        self.tracks = {}
        self.grid_layout = QtGui.QGridLayout(self.main_widget)
        for f_i in range(a_track_count):
            f_channel = mixer_channel("track{}".format(f_i))
            self.tracks[f_i] = f_channel
            self.grid_layout.addWidget(f_channel.widget, 0, f_i)

    def set_tooltips(self, a_enabled):
        if a_enabled:
            self.widget.setToolTip(MIXER_TOOLTIP)
        else:
            self.widget.setToolTip("")

    def update_track_names(self, a_track_names_dict):
        for k, v in a_track_names_dict.items():
            self.tracks[k].set_name(v, a_track_names_dict)

    def set_plugin_widget(self, a_track_index, a_send_index, a_output,
                          a_plugin):
        self.tracks[a_track_index].add_plugin(
            a_send_index, a_plugin, a_output)

    def remove_plugin_widget(self, a_track_index, a_send_index):
        self.tracks[a_track_index].remove_plugin(a_send_index)

    def clear(self):
        for v in self.tracks.values():
            v.clear()


# Custom oscillator widgets

class pydaw_abstract_custom_oscillator:
    def __init__(self):
        self.widget = QtGui.QWidget()
        self.widget.setObjectName("plugin_ui")
        self.layout = QtGui.QVBoxLayout(self.widget)

    def open_settings(self, a_settings):
        pass


ADDITIVE_OSC_HEIGHT = 310
ADDITIVE_OSC_MIN_AMP = -30
ADDITIVE_OSC_INC = 10 #int(ADDITIVE_OSC_HEIGHT / -ADDITIVE_OSC_MIN_AMP)
ADDITIVE_MAX_Y_POS = ADDITIVE_OSC_HEIGHT - ADDITIVE_OSC_INC
ADDITIVE_OSC_HARMONIC_COUNT = 32
ADDITIVE_OSC_BAR_WIDTH = 10
ADDITIVE_OSC_WIDTH = ADDITIVE_OSC_HARMONIC_COUNT * ADDITIVE_OSC_BAR_WIDTH
ADDITIVE_WAVETABLE_SIZE = 1024
#ADDITIVE_OSC_HEIGHT_div2 = ADDITIVE_OSC_HEIGHT * 0.5

ADD_OSC_FILL = QtGui.QLinearGradient(0.0, 0.0, 0.0, ADDITIVE_OSC_HEIGHT)

ADD_OSC_FILL.setColorAt(0.0, QtGui.QColor(255, 0, 0, 90)) #red
ADD_OSC_FILL.setColorAt(0.14285, QtGui.QColor(255, 123, 0, 90)) #orange
ADD_OSC_FILL.setColorAt(0.2857, QtGui.QColor(255, 255, 0, 90)) #yellow
ADD_OSC_FILL.setColorAt(0.42855, QtGui.QColor(0, 255, 0, 90)) #green
ADD_OSC_FILL.setColorAt(0.5714, QtGui.QColor(0, 123, 255, 90)) #blue
ADD_OSC_FILL.setColorAt(0.71425, QtGui.QColor(0, 0, 255, 90)) #indigo
ADD_OSC_FILL.setColorAt(0.8571, QtGui.QColor(255, 0, 255, 90)) #violet

ADD_OSC_BACKGROUND = QtGui.QLinearGradient(0.0, 0.0, 10.0, ADDITIVE_OSC_HEIGHT)
ADD_OSC_BACKGROUND.setColorAt(0.0, QtGui.QColor(40, 40, 40))
ADD_OSC_BACKGROUND.setColorAt(0.2, QtGui.QColor(20, 20, 20))
ADD_OSC_BACKGROUND.setColorAt(0.7, QtGui.QColor(30, 30, 30))
ADD_OSC_BACKGROUND.setColorAt(1.0, QtGui.QColor(40, 40, 40))

ADD_OSC_SINE_CACHE = {}

def global_get_sine(a_size, a_phase):
    f_key = (a_size, a_phase)
    if f_key in ADD_OSC_SINE_CACHE:
        return numpy.copy(ADD_OSC_SINE_CACHE[f_key])
    else:
        f_phase = a_phase * numpy.pi
        f_lin = numpy.linspace(f_phase, (2.0 * numpy.pi) + f_phase, a_size)
        f_sin = numpy.sin(f_lin)
        ADD_OSC_SINE_CACHE[f_key] = f_sin
        return numpy.copy(f_sin)


class pydaw_additive_osc_amp_bar(QtGui.QGraphicsRectItem):
    def __init__(self, a_x_pos):
        QtGui.QGraphicsRectItem.__init__(self)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges)
        self.setBrush(ADD_OSC_FILL)
        self.setPen(QtGui.QPen(QtCore.Qt.white))
        self.x_pos = a_x_pos
        self.setPos(a_x_pos, ADDITIVE_OSC_HEIGHT - ADDITIVE_OSC_INC)
        self.setRect(0.0, 0.0, ADDITIVE_OSC_BAR_WIDTH, ADDITIVE_OSC_INC)
        self.value = ADDITIVE_OSC_MIN_AMP
        self.extend_to_bottom()

    def set_value(self, a_value):
        if self.value != a_value:
            self.value = int(a_value)
            f_y_pos = (a_value * ADDITIVE_OSC_INC * -1.0)
            self.setPos(self.x_pos, f_y_pos)
            self.extend_to_bottom()
            return True
        else:
            return False

    def get_value(self):
        return int(self.value)

    def extend_to_bottom(self):
        f_pos_y = pydaw_util.pydaw_clip_value(
            round(self.pos().y(), -1), ADDITIVE_OSC_INC, ADDITIVE_MAX_Y_POS)
        self.setPos(self.x_pos, f_pos_y)
        self.setRect(
            0.0, 0.0, ADDITIVE_OSC_BAR_WIDTH,
            ADDITIVE_OSC_HEIGHT - f_pos_y - 1.0)

class pydaw_additive_wav_viewer(QtGui.QGraphicsView):
    def __init__(self):
        QtGui.QGraphicsView.__init__(self)
        self.setMaximumWidth(600)
        self.last_x_scale = 1.0
        self.last_y_scale = 1.0
        self.scene = QtGui.QGraphicsScene()
        self.setScene(self.scene)
        self.scene.setBackgroundBrush(ADD_OSC_BACKGROUND)
        self.setSceneRect(
            0.0, 0.0, ADDITIVE_WAVETABLE_SIZE, ADDITIVE_OSC_HEIGHT)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setRenderHint(QtGui.QPainter.Antialiasing)

    def draw_array(self, a_np_array):
        self.setUpdatesEnabled(False)
        f_path = QtGui.QPainterPath(QtCore.QPointF(
            0.0, ADDITIVE_OSC_HEIGHT * 0.5))
        f_x = 1.0
        f_half = ADDITIVE_OSC_HEIGHT * 0.5
        for f_point in a_np_array:
            f_path.lineTo(f_x, (f_point * f_half) + f_half)
            f_x += 1.0
        self.scene.clear()
        f_path_item = self.scene.addPath(
            f_path, QtGui.QPen(QtCore.Qt.white, 1.0))
        f_path_item.setBrush(ADD_OSC_FILL)
        self.setUpdatesEnabled(True)
        self.update()

    def resizeEvent(self, a_resize_event):
        QtGui.QGraphicsView.resizeEvent(self, a_resize_event)
        self.scale(1.0 / self.last_x_scale, 1.0 / self.last_y_scale)
        f_rect = self.rect()
        self.last_x_scale = f_rect.width() / ADDITIVE_WAVETABLE_SIZE
        self.last_y_scale = f_rect.height() / ADDITIVE_OSC_HEIGHT
        self.scale(self.last_x_scale, self.last_y_scale)


class pydaw_additive_osc_viewer(QtGui.QGraphicsView):
    def __init__(self, a_draw_callback, a_configure_callback, a_get_wav):
        QtGui.QGraphicsView.__init__(self)
        self.setMaximumWidth(600)
        self.configure_callback = a_configure_callback
        self.get_wav = a_get_wav
        self.draw_callback = a_draw_callback
        self.last_x_scale = 1.0
        self.last_y_scale = 1.0
        self.is_drawing = False
        self.edit_mode = 0
        self.setMinimumSize(
            ADDITIVE_OSC_WIDTH, ADDITIVE_OSC_HEIGHT)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scene = QtGui.QGraphicsScene()
        self.setScene(self.scene)
        self.scene.mousePressEvent = self.scene_mousePressEvent
        self.scene.mouseReleaseEvent = self.scene_mouseReleaseEvent
        self.scene.mouseMoveEvent = self.scene_mouseMoveEvent
        self.scene.setBackgroundBrush(ADD_OSC_BACKGROUND)
        self.setSceneRect(
            0.0, 0.0, ADDITIVE_OSC_WIDTH, ADDITIVE_OSC_HEIGHT)
        self.bars = []
        for f_i in range(
        0, ADDITIVE_OSC_WIDTH, int(ADDITIVE_OSC_BAR_WIDTH)):
            f_bar = pydaw_additive_osc_amp_bar(f_i)
            self.bars.append(f_bar)
            self.scene.addItem(f_bar)

    def set_edit_mode(self, a_mode):
        self.edit_mode = a_mode

    def resizeEvent(self, a_resize_event):
        QtGui.QGraphicsView.resizeEvent(self, a_resize_event)
        self.scale(1.0 / self.last_x_scale, 1.0 / self.last_y_scale)
        f_rect = self.rect()
        self.last_x_scale = f_rect.width() / ADDITIVE_OSC_WIDTH
        self.last_y_scale = f_rect.height() / ADDITIVE_OSC_HEIGHT
        self.scale(self.last_x_scale, self.last_y_scale)

    def scene_mousePressEvent(self, a_event):
        QtGui.QGraphicsScene.mousePressEvent(self.scene, a_event)
        self.is_drawing = True
        self.draw_harmonics(a_event.scenePos())

    def scene_mouseReleaseEvent(self, a_event):
        QtGui.QGraphicsScene.mouseReleaseEvent(self.scene, a_event)
        self.is_drawing = False
        self.get_wav(True)

    def scene_mouseMoveEvent(self, a_event):
        if self.is_drawing:
            QtGui.QGraphicsScene.mouseMoveEvent(self.scene, a_event)
            self.draw_harmonics(a_event.scenePos())

    def clear_osc(self):
        for f_point in self.bars:
            f_point.set_value(ADDITIVE_OSC_MIN_AMP)
        self.get_wav()

    def open_osc(self, a_arr):
        for f_val, f_point in zip(a_arr, self.bars):
            f_point.set_value(int(f_val))
        self.get_wav()

    def draw_harmonics(self, a_pos):
        f_pos = a_pos
        f_pos_x = f_pos.x()
        f_pos_y = f_pos.y()
        f_db = (f_pos_y / ADDITIVE_OSC_HEIGHT) * ADDITIVE_OSC_MIN_AMP
        f_harmonic = int((f_pos_x / ADDITIVE_OSC_WIDTH) *
            ADDITIVE_OSC_HARMONIC_COUNT)
        if f_harmonic < 0:
            f_harmonic = 0
        elif f_harmonic >= ADDITIVE_OSC_HARMONIC_COUNT:
            f_harmonic = ADDITIVE_OSC_HARMONIC_COUNT - 1
        if self.edit_mode == 1 and (f_harmonic % 2) != 0:
            return
        if f_db > 0:
            f_db = 0
        elif f_db < ADDITIVE_OSC_MIN_AMP:
            f_db = ADDITIVE_OSC_MIN_AMP
        if self.bars[int(f_harmonic)].set_value(int(f_db)):
            self.get_wav()


class pydaw_custom_additive_oscillator(pydaw_abstract_custom_oscillator):
    def __init__(self, a_configure_callback=None, a_osc_count=3):
        pydaw_abstract_custom_oscillator.__init__(self)
        self.configure_callback = a_configure_callback
        self.hlayout = QtGui.QHBoxLayout()
        self.layout.addLayout(self.hlayout)
        self.osc_num = 0
        self.hlayout.addWidget(QtGui.QLabel(_("Oscillator#:")))
        self.osc_num_combobox = QtGui.QComboBox()
        self.osc_num_combobox.setMinimumWidth(66)
        self.hlayout.addWidget(self.osc_num_combobox)
        for f_i in range(1, a_osc_count + 1):
            self.osc_num_combobox.addItem(str(f_i))
        self.osc_num_combobox.currentIndexChanged.connect(
            self.osc_index_changed)
        self.hlayout.addWidget(QtGui.QLabel(_("Edit Mode:")))
        self.edit_mode_combobox = QtGui.QComboBox()
        self.edit_mode_combobox.setMinimumWidth(90)
        self.hlayout.addWidget(self.edit_mode_combobox)
        self.edit_mode_combobox.addItems([_("All"), _("Odd")])
        self.edit_mode_combobox.currentIndexChanged.connect(
            self.edit_mode_combobox_changed)
        self.tools_button = QtGui.QPushButton(_("Tools"))
        self.hlayout.addWidget(self.tools_button)
        self.tools_menu = QtGui.QMenu(self.tools_button)
        self.tools_button.setMenu(self.tools_menu)

        self.hlayout.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))
        self.hlayout.addWidget(
            QtGui.QLabel(_("Select (Additive [n]) as your osc type to use")))
        self.wav_viewer = pydaw_additive_wav_viewer()
        self.draw_callback = self.wav_viewer.draw_array
        self.viewer = pydaw_additive_osc_viewer(
            self.wav_viewer.draw_array, self.configure_wrapper, self.get_wav)
        self.phase_viewer = pydaw_additive_osc_viewer(
            self.wav_viewer.draw_array, self.configure_wrapper, self.get_wav)
        self.view_widget = QtGui.QWidget()
        self.view_widget.setMaximumSize(900, 540)
        self.vlayout2 = QtGui.QVBoxLayout()
        self.hlayout2 = QtGui.QHBoxLayout(self.view_widget)
        self.layout.addWidget(self.view_widget)
        self.hlayout2.addLayout(self.vlayout2)
        #self.vlayout2.addWidget(QtGui.QLabel(_("Harmonics")))
        self.viewer.setToolTip(_("Harmonics"))
        self.vlayout2.addWidget(self.viewer)
        #self.vlayout2.addWidget(QtGui.QLabel(_("Phases")))
        self.phase_viewer.setToolTip(_("Phases"))
        self.vlayout2.addWidget(self.phase_viewer)
        self.hlayout2.addWidget(self.wav_viewer)

        f_saw_action = self.tools_menu.addAction(_("Set Saw"))
        f_saw_action.triggered.connect(self.set_saw)
        f_square_action = self.tools_menu.addAction(_("Set Square"))
        f_square_action.triggered.connect(self.set_square)
        f_tri_action = self.tools_menu.addAction(_("Set Triangle"))
        f_tri_action.triggered.connect(self.set_triangle)
        f_sine_action = self.tools_menu.addAction(_("Set Sine"))
        f_sine_action.triggered.connect(self.set_sine)
        self.osc_values = {0 : None, 1 : None, 2 : None}
        self.phase_values = {0 : None, 1 : None, 2 : None}

    def configure_wrapper(self, a_key, a_val):
        if self.configure_callback is not None:
            self.configure_callback(a_key, a_val)
        f_index = int(a_key[-1])
        if a_key.startswith("wayv_add_ui"):
            self.osc_values[f_index] = a_val.split("|")
        elif a_key.startswith("wayv_add_phase"):
            self.phase_values[f_index] = a_val.split("|")

    def osc_index_changed(self, a_event):
        self.osc_num = self.osc_num_combobox.currentIndex()
        if self.osc_values[self.osc_num] is None:
            self.viewer.clear_osc()
        else:
            self.viewer.open_osc(self.osc_values[self.osc_num])
        if self.phase_values[self.osc_num] is None:
            self.phase_viewer.clear_osc()
        else:
            self.phase_viewer.open_osc(self.phase_values[self.osc_num])

    def edit_mode_combobox_changed(self, a_event):
        self.viewer.set_edit_mode(self.edit_mode_combobox.currentIndex())

    def set_values(self, a_num, a_val):
        self.osc_values[int(a_num)] = a_val
        if self.osc_num_combobox.currentIndex() == int(a_num):
            self.osc_index_changed(None)

    def set_phases(self, a_num, a_val):
        self.phase_values[int(a_num)] = a_val
        if self.osc_num_combobox.currentIndex() == int(a_num):
            self.osc_index_changed(None)

    def get_wav(self, a_configure=False):
        f_result = numpy.zeros(ADDITIVE_WAVETABLE_SIZE)
        f_recall_list = []
        f_phase_list = []
        for f_i in range(1, ADDITIVE_OSC_HARMONIC_COUNT + 1):
            f_size = int(ADDITIVE_WAVETABLE_SIZE / f_i)
            f_db = self.viewer.bars[f_i - 1].get_value()
            f_phase = self.phase_viewer.bars[f_i - 1].get_value()
            if a_configure:
                f_recall_list.append("{}".format(f_db))
                f_phase_list.append("{}".format(f_phase))
            f_phase = (f_phase + (ADDITIVE_OSC_MIN_AMP * -1.0)) / (
                ADDITIVE_OSC_MIN_AMP / 2)
            if f_db > (ADDITIVE_OSC_MIN_AMP + 1):
                f_sin = global_get_sine(
                    f_size, f_phase) * pydaw_util.pydaw_db_to_lin(f_db)
                for f_i2 in range(
                int(ADDITIVE_WAVETABLE_SIZE / f_size)):
                    f_start = (f_i2) * f_size
                    f_end = f_start + f_size
                    f_result[f_start:f_end] += f_sin
        f_max = numpy.max(numpy.abs(f_result), axis=0)
        if f_max > 0.0:
            f_normalize = 0.99 / f_max
            f_result *= f_normalize
        self.draw_callback(f_result)
        if a_configure and self.configure_callback is not None:
            f_engine_list = []
            for f_float in f_result:
                f_engine_list.append("{}".format(round(f_float, 6)))
            f_engine_str = "{}|{}".format(ADDITIVE_WAVETABLE_SIZE,
                "|".join(f_engine_list))
            self.configure_wrapper(
                "wayv_add_eng{}".format(self.osc_num), f_engine_str)
            self.configure_wrapper(
                "wayv_add_ui{}".format(self.osc_num), "|".join(f_recall_list))
            self.configure_wrapper(
                "wayv_add_phase{}".format(self.osc_num),
                "|".join(f_phase_list))

    def set_saw(self):
        for f_i in range(len(self.viewer.bars)):
            f_db = int(pydaw_util.pydaw_lin_to_db(1.0 / (f_i + 1)))
            self.viewer.bars[f_i].set_value(f_db)
        for f_i in range(len(self.phase_viewer.bars)):
            self.phase_viewer.bars[f_i].set_value(ADDITIVE_OSC_MIN_AMP)
        for f_i in range(1, len(self.phase_viewer.bars), 2):
            self.phase_viewer.bars[f_i].set_value(ADDITIVE_OSC_MIN_AMP / 2)
        self.get_wav(True)

    def set_square(self):
        f_odd = True
        for f_i in range(len(self.viewer.bars)):
            f_point = self.viewer.bars[f_i]
            if f_odd:
                f_db = int(pydaw_util.pydaw_lin_to_db(1.0 / (f_i + 1)))
                f_odd = False
                f_point.set_value(f_db)
            else:
                f_odd = True
                f_point.set_value(ADDITIVE_OSC_MIN_AMP)
            self.phase_viewer.bars[f_i].set_value(ADDITIVE_OSC_MIN_AMP)
        self.get_wav(True)

    def set_triangle(self):
        f_odd = True
        for f_i in range(len(self.viewer.bars)):
            f_point = self.viewer.bars[f_i]
            if f_odd:
                f_num = f_i + 1
                f_db = int(pydaw_util.pydaw_lin_to_db(1.0 / (f_num * f_num)))
                f_odd = False
                f_point.set_value(f_db)
            else:
                f_odd = True
                f_point.set_value(ADDITIVE_OSC_MIN_AMP)
            self.phase_viewer.bars[f_i].set_value(ADDITIVE_OSC_MIN_AMP)
        self.phase_viewer.bars[2].set_value(ADDITIVE_OSC_MIN_AMP / 2.0)
        self.get_wav(True)

    def set_sine(self):
        self.viewer.bars[0].set_value(0)
        for f_point in self.viewer.bars[1:]:
            f_point.set_value(ADDITIVE_OSC_MIN_AMP)
        for f_i in range(len(self.phase_viewer.bars)):
            self.phase_viewer.bars[f_i].set_value(ADDITIVE_OSC_MIN_AMP)
        self.get_wav(True)

AUDIO_ITEM_SCENE_HEIGHT = 1200.0
AUDIO_ITEM_SCENE_WIDTH = 6000.0
AUDIO_ITEM_SCENE_WIDTH_RECIP = 1.0 / AUDIO_ITEM_SCENE_WIDTH
AUDIO_ITEM_MAX_MARKER_VAL = 1000.0
AUDIO_ITEM_END_MARKER_MIN_VAL = 6.0
AUDIO_ITEM_START_MARKER_MAX_VAL = 994.0
AUDIO_ITEM_VAL_TO_PX = AUDIO_ITEM_SCENE_WIDTH / AUDIO_ITEM_MAX_MARKER_VAL
AUDIO_ITEM_PX_TO_VAL = AUDIO_ITEM_MAX_MARKER_VAL / AUDIO_ITEM_SCENE_WIDTH

START_END_GRADIENT = QtGui.QLinearGradient(0.0, 0.0, 66.0, 66.0)
START_END_GRADIENT.setColorAt(0.0, QtGui.QColor.fromRgb(246, 30, 30))
START_END_GRADIENT.setColorAt(1.0, QtGui.QColor.fromRgb(226, 42, 42))
START_END_PEN = QtGui.QPen(QtGui.QColor.fromRgb(246, 30, 30), 12.0)

FADE_PEN = QtGui.QPen(QtGui.QColor.fromRgb(246, 30, 30), 6.0)

LOOP_GRADIENT = QtGui.QLinearGradient(0.0, 0.0, 66.0, 66.0)
LOOP_GRADIENT.setColorAt(0.0, QtGui.QColor.fromRgb(246, 180, 30))
LOOP_GRADIENT.setColorAt(1.0, QtGui.QColor.fromRgb(226, 180, 42))
LOOP_PEN = QtGui.QPen(QtGui.QColor.fromRgb(246, 180, 30), 12.0)

MARKER_MIN_DIFF = 1.0

class pydaw_audio_marker_widget(QtGui.QGraphicsRectItem):
    mode_start_end = 0
    mode_loop = 1
    def __init__(self, a_type, a_val, a_pen, a_brush, a_label, a_graph_object,
                 a_marker_mode, a_offset=0, a_callback=None):
        """ a_type:  0 == start, 1 == end, more types eventually... """
        self.audio_item_marker_height = 66.0
        QtGui.QGraphicsRectItem.__init__(
            self, 0, 0, self.audio_item_marker_height,
            self.audio_item_marker_height)
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.callback = a_callback
        self.graph_object = a_graph_object
        self.line = QtGui.QGraphicsLineItem(
            0.0, 0.0, 0.0, AUDIO_ITEM_SCENE_HEIGHT)
        self.line.setParentItem(self)
        self.line.setPen(a_pen)
        self.marker_type = a_type
        self.marker_mode = a_marker_mode
        self.pos_x = 0.0
        self.max_x = \
            AUDIO_ITEM_SCENE_WIDTH - self.audio_item_marker_height
        self.value = a_val
        self.other = None
        self.fade_marker = None
        self.offset = a_offset
        if a_type == 0:
            self.min_x = 0.0
            self.y_pos = 0.0 + (a_offset * self.audio_item_marker_height)
            self.line.setPos(0.0, self.y_pos * -1.0)
        elif a_type == 1:
            self.min_x = 66.0
            self.y_pos = \
                AUDIO_ITEM_SCENE_HEIGHT - \
                self.audio_item_marker_height - \
                (a_offset * self.audio_item_marker_height)
            self.line.setPos(self.audio_item_marker_height, self.y_pos * -1.0)
        self.setPen(a_pen)
        self.setBrush(a_brush)
        self.text_item = QtGui.QGraphicsTextItem(a_label)
        self.text_item.setParentItem(self)
        self.text_item.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations)

    def __str__(self):
        f_val = self.value * 0.001 * self.graph_object.length_in_seconds
        f_val = pydaw_util.pydaw_seconds_to_time_str(f_val)
        if self.marker_type == 0 and self.marker_mode == 0:
            return "Start {}".format(f_val)
        elif self.marker_type == 1 and self.marker_mode == 0:
            return "End {}".format(f_val)
        elif self.marker_type == 0 and self.marker_mode == 1:
            return "Loop Start {}".format(f_val)
        elif self.marker_type == 1 and self.marker_mode == 1:
            return "Loop End {}".format(f_val)
        else:
            assert(False)

    def reset_default(self):
        if self.marker_type == 0:
            self.value = 0.0
        else:
            self.value = 1000.0
        self.set_pos()
        self.callback(self.value)

    def set_pos(self):
        if self.marker_type == 0:
            f_new_val = self.value * AUDIO_ITEM_VAL_TO_PX
        elif self.marker_type == 1:
            f_new_val = (self.value *
                AUDIO_ITEM_VAL_TO_PX) - self.audio_item_marker_height
        f_new_val = pydaw_util.pydaw_clip_value(
            f_new_val, self.min_x, self.max_x)
        self.setPos(f_new_val, self.y_pos)

    def set_value(self, a_value):
        self.value = float(a_value)
        self.set_pos()
        self.callback(self.value)

    def set_other(self, a_other, a_fade_marker=None):
        self.other = a_other
        self.fade_marker = a_fade_marker

    def mouseMoveEvent(self, a_event):
        a_event.setAccepted(True)
        QtGui.QGraphicsRectItem.mouseMoveEvent(self, a_event)
        self.pos_x = a_event.scenePos().x()
        self.pos_x = pydaw_util.pydaw_clip_value(
            self.pos_x, self.min_x, self.max_x)
        self.setPos(self.pos_x, self.y_pos)
        if self.marker_type == 0:
            f_new_val = self.pos_x * AUDIO_ITEM_PX_TO_VAL
            if self.fade_marker is not None and \
            self.fade_marker.pos().x() < self.pos_x:
                self.fade_marker.value = f_new_val
                self.fade_marker.set_pos()
        elif self.marker_type == 1:
            f_new_val = (self.pos_x +
                self.audio_item_marker_height) * AUDIO_ITEM_PX_TO_VAL
            if self.fade_marker is not None and \
            self.fade_marker.pos().x() > self.pos_x:
                self.fade_marker.value = f_new_val
                self.fade_marker.set_pos()
        f_new_val = pydaw_util.pydaw_clip_value(f_new_val, 0.0, 994.0)
        self.value = f_new_val
        if self.other is not None:
            if self.marker_type == 0:
                if self.value > self.other.value - MARKER_MIN_DIFF:
                    self.other.value = self.value + MARKER_MIN_DIFF
                    self.other.value = pydaw_util.pydaw_clip_value(
                        self.other.value, MARKER_MIN_DIFF,
                        1000.0, a_round=True)
                    self.other.set_pos()
            elif self.marker_type == 1:
                if self.other.value > self.value - MARKER_MIN_DIFF:
                    self.other.value = self.value - MARKER_MIN_DIFF
                    self.other.value = pydaw_util.pydaw_clip_value(
                        self.other.value, 0.0,
                        1000.0 - MARKER_MIN_DIFF, a_round=True)
                    self.other.set_pos()
        if self.fade_marker is not None:
            self.fade_marker.draw_lines()

    def mouseReleaseEvent(self, a_event):
        a_event.setAccepted(True)
        QtGui.QGraphicsRectItem.mouseReleaseEvent(self, a_event)
        if self.callback is not None:
            self.callback(self.value)
        if self.other.callback is not None:
            self.other.callback(self.other.value)
        if self.fade_marker is not None:
            self.fade_marker.callback(self.fade_marker.value)


class pydaw_audio_fade_marker_widget(QtGui.QGraphicsRectItem):
    def __init__(self, a_type, a_val, a_pen, a_brush, a_label, a_graph_object,
                 a_offset=0, a_callback=None):
        """ a_type:  0 == start, 1 == end, more types eventually... """
        self.audio_item_marker_height = 66.0
        QtGui.QGraphicsRectItem.__init__(
            self, 0, 0, self.audio_item_marker_height,
            self.audio_item_marker_height)
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.callback = a_callback
        self.line = QtGui.QGraphicsLineItem(
            0.0, 0.0, 0.0, AUDIO_ITEM_SCENE_HEIGHT)
        self.line.setParentItem(self)
        self.line.setPen(a_pen)
        self.marker_type = a_type
        self.pos_x = 0.0
        self.max_x = \
            AUDIO_ITEM_SCENE_WIDTH - self.audio_item_marker_height
        self.value = a_val
        self.other = None
        self.start_end_marker = None
        if a_type == 0:
            self.min_x = 0.0
            self.y_pos = 0.0 + (a_offset * self.audio_item_marker_height)
            self.line.setPos(0.0, self.y_pos * -1.0)
        elif a_type == 1:
            self.min_x = 66.0
            self.y_pos = AUDIO_ITEM_SCENE_HEIGHT - \
                self.audio_item_marker_height - \
                (a_offset * self.audio_item_marker_height)
            self.line.setPos(self.audio_item_marker_height, self.y_pos * -1.0)
        self.setPen(a_pen)
        self.setBrush(a_brush)
        self.text_item = QtGui.QGraphicsTextItem(a_label)
        self.text_item.setParentItem(self)
        self.text_item.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations)
        self.amp_lines = []
        self.graph_object = a_graph_object
        for f_i in range(self.graph_object.channels * 2):
            f_line = QtGui.QGraphicsLineItem()
            self.amp_lines.append(f_line)
            f_line.setPen(FADE_PEN)

    def __str__(self):
        f_val = self.value * 0.001 * self.graph_object.length_in_seconds
        f_val = pydaw_util.pydaw_seconds_to_time_str(f_val)
        if self.marker_type == 0:
            return "Fade In {}".format(f_val)
        elif self.marker_type == 1:
            return "Fade Out {}".format(f_val)
        else:
            assert(False)

    def reset_default(self):
        if self.marker_type == 0:
            self.value = 0.0
        else:
            self.value = 1000.0
        self.set_pos()
        self.callback(self.value)

    def set_value(self, a_value):
        self.value = float(a_value)
        self.set_pos()
        self.callback(self.value)

    def draw_lines(self):
        f_inc = AUDIO_ITEM_SCENE_HEIGHT / float(len(self.amp_lines))
        f_y_pos = 0
        f_x_inc = 0
        if self.marker_type == 0:
            f_x_list = [self.scenePos().x(),
                        self.start_end_marker.scenePos().x()]
        elif self.marker_type == 1:
            f_x_list = [self.scenePos().x() + self.audio_item_marker_height,
                        self.start_end_marker.scenePos().x() +
                        self.audio_item_marker_height]
        for f_line in self.amp_lines:
            if f_x_inc == 0:
                f_line.setLine(
                    f_x_list[0], f_y_pos, f_x_list[1], f_y_pos + f_inc)
            else:
                f_line.setLine(
                    f_x_list[1], f_y_pos, f_x_list[0], f_y_pos + f_inc)
            f_y_pos += f_inc
            f_x_inc += 1
            if f_x_inc > 1:
                f_x_inc = 0

    def set_pos(self):
        if self.marker_type == 0:
            f_new_val = self.value * AUDIO_ITEM_VAL_TO_PX
        elif self.marker_type == 1:
            f_new_val = (self.value *
                AUDIO_ITEM_VAL_TO_PX) - self.audio_item_marker_height
        f_new_val = pydaw_util.pydaw_clip_value(
            f_new_val, self.min_x, self.max_x)
        self.setPos(f_new_val, self.y_pos)
        self.draw_lines()

    def set_other(self, a_other, a_start_end_marker):
        self.other = a_other
        self.start_end_marker = a_start_end_marker

    def mouseMoveEvent(self, a_event):
        a_event.setAccepted(True)
        QtGui.QGraphicsRectItem.mouseMoveEvent(self, a_event)
        self.pos_x = a_event.scenePos().x()
        self.pos_x = pydaw_util.pydaw_clip_value(
            self.pos_x, self.min_x, self.max_x)
        if self.marker_type == 0:
            self.pos_x = pydaw_util.pydaw_clip_max(
                self.pos_x, self.other.scenePos().x())
        elif self.marker_type == 1:
            self.pos_x = pydaw_util.pydaw_clip_min(
                self.pos_x, self.other.scenePos().x())
        self.setPos(self.pos_x, self.y_pos)
        if self.marker_type == 0:
            f_new_val = self.pos_x * AUDIO_ITEM_PX_TO_VAL
            if self.pos_x < self.start_end_marker.scenePos().x():
                self.start_end_marker.value = f_new_val
                self.start_end_marker.set_pos()
        elif self.marker_type == 1:
            f_new_val = (self.pos_x +
                self.audio_item_marker_height) * AUDIO_ITEM_PX_TO_VAL
            if self.pos_x > self.start_end_marker.scenePos().x():
                self.start_end_marker.value = f_new_val
                self.start_end_marker.set_pos()
        f_new_val = pydaw_util.pydaw_clip_value(f_new_val, 0.0, 1000.0)
        self.value = f_new_val
        self.draw_lines()

    def mouseReleaseEvent(self, a_event):
        a_event.setAccepted(True)
        QtGui.QGraphicsRectItem.mouseReleaseEvent(self, a_event)
        if self.callback is not None:
            self.callback(self.value)
        if self.start_end_marker is not None:
            self.start_end_marker.callback(self.start_end_marker.value)

AUDIO_MARKERS_CLIPBOARD = None

def global_set_audio_markers_clipboard(a_s, a_e, a_fi, a_fo,
                                       a_ls=0.0, a_le=1000.0):
    global AUDIO_MARKERS_CLIPBOARD
    AUDIO_MARKERS_CLIPBOARD = (a_s, a_e, a_fi, a_fo, a_ls, a_le)

class pydaw_audio_item_viewer_widget(QtGui.QGraphicsView):
    def __init__(self, a_start_callback, a_end_callback,
                 a_fade_in_callback, a_fade_out_callback):
        QtGui.QGraphicsView.__init__(self)
        self.setViewportUpdateMode(QtGui.QGraphicsView.MinimalViewportUpdate)
        self.start_callback_x = a_start_callback
        self.end_callback_x = a_end_callback
        self.fade_in_callback_x = a_fade_in_callback
        self.fade_out_callback_x = a_fade_out_callback
        self.scene = QtGui.QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.scene.setBackgroundBrush(QtCore.Qt.darkGray)
        self.scene.mousePressEvent = self.scene_mousePressEvent
        self.scene.mouseMoveEvent = self.scene_mouseMoveEvent
        self.scene.mouseReleaseEvent = self.scene_mouseReleaseEvent
        self.scene_context_menu = QtGui.QMenu(self)
        self.reset_markers_action = self.scene_context_menu.addAction(
            _("Reset Markers"))
        self.reset_markers_action.triggered.connect(self.reset_markers)
        self.copy_markers_action = self.scene_context_menu.addAction(
            _("Copy Markers"))
        self.copy_markers_action.triggered.connect(self.copy_markers)
        self.paste_markers_action = self.scene_context_menu.addAction(
            _("Paste Markers"))
        self.paste_markers_action.triggered.connect(self.paste_markers)
        self.tempo_sync_action = self.scene_context_menu.addAction(
            _("Tempo Sync"))
        self.tempo_sync_action.triggered.connect(self.tempo_sync_dialog)

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.scroll_bar_height = self.horizontalScrollBar().height()
        self.last_x_scale = 1.0
        self.last_y_scale = 1.0
        self.waveform_brush = QtGui.QLinearGradient(
            0.0, 0.0, AUDIO_ITEM_SCENE_HEIGHT,
            AUDIO_ITEM_SCENE_WIDTH)
        self.waveform_brush.setColorAt(0.0, QtGui.QColor(140, 140, 240))
        self.waveform_brush.setColorAt(0.5, QtGui.QColor(240, 190, 140))
        self.waveform_brush.setColorAt(1.0, QtGui.QColor(140, 140, 240))
        self.waveform_pen = QtGui.QPen(QtCore.Qt.NoPen)
        self.is_drag_selecting = False
        self.drag_start_pos = 0.0
        self.drag_start_markers = []
        self.drag_end_markers = []
        self.graph_object = None
        self.label = QtGui.QLabel("")
        self.label.setMinimumWidth(420)
        self.last_ts_bar = 0
        self.last_tempo_combobox_index = 0

    def start_callback(self, a_val):
        self.start_callback_x(a_val)
        self.update_label()

    def end_callback(self, a_val):
        self.end_callback_x(a_val)
        self.update_label()

    def fade_in_callback(self, a_val):
        self.fade_in_callback_x(a_val)
        self.update_label()

    def fade_out_callback(self, a_val):
        self.fade_out_callback_x(a_val)
        self.update_label()

    def update_label(self):
        f_val = "\n".join([str(x) for x in
            self.length_str + self.drag_start_markers + self.drag_end_markers])
        self.label.setText(f_val)

    def tempo_sync_dialog(self):
        def sync_button_pressed(a_self=None):
            f_frac = 1.0
            f_switch = (f_beat_frac_combobox.currentIndex())
            f_dict = {0 : 0.25, 1 : 0.33333, 2 : 0.5, 3 : 0.666666, 4 : 0.75,
                      5 : 1.0, 6 : 2.0, 7 : 4.0, 8 : 0.0}
            f_frac = f_dict[f_switch] + (f_bar_spinbox.value() * 4.0)
            self.last_ts_bar = f_bar_spinbox.value()
            f_seconds_per_beat = 60 / (self.last_ts_bar)

            f_result = ((f_seconds_per_beat * f_frac) /
                self.graph_object.length_in_seconds) * 1000.0
            for f_marker in self.drag_end_markers:
                f_new = f_marker.other.value + f_result
                f_new = pydaw_util.pydaw_clip_value(
                    f_new, f_marker.other.value + 1.0, 1000.0)
                f_marker.set_value(f_new)
            self.last_tempo_combobox_index = \
                f_beat_frac_combobox.currentIndex()
            f_dialog.close()

        f_dialog = QtGui.QDialog(self)
        f_dialog.setWindowTitle(_("Tempo Sync"))
        f_groupbox_layout = QtGui.QGridLayout(f_dialog)
        f_spinbox = QtGui.QDoubleSpinBox()
        f_spinbox.setDecimals(1)
        f_spinbox.setRange(60, 200)
        f_spinbox.setSingleStep(0.1)
        f_spinbox.setValue(TEMPO)
        f_beat_fracs = ["1/16", "1/12", "1/8", "2/12", "3/16",
                        "1/4", "2/4", "4/4", "None"]
        f_beat_frac_combobox = QtGui.QComboBox()
        f_beat_frac_combobox.setMinimumWidth(75)
        f_beat_frac_combobox.addItems(f_beat_fracs)
        f_beat_frac_combobox.setCurrentIndex(self.last_tempo_combobox_index)
        f_bar_spinbox = QtGui.QSpinBox()
        f_bar_spinbox.setRange(0, 64)
        f_bar_spinbox.setValue(self.last_ts_bar)
        f_sync_button = QtGui.QPushButton(_("Sync"))
        f_sync_button.pressed.connect(sync_button_pressed)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(f_dialog.close)
        f_groupbox_layout.addWidget(QtGui.QLabel(_("BPM")), 0, 0)
        f_groupbox_layout.addWidget(f_spinbox, 1, 0)
        f_groupbox_layout.addWidget(QtGui.QLabel("Length"), 0, 1)
        f_groupbox_layout.addWidget(f_beat_frac_combobox, 1, 1)
        f_groupbox_layout.addWidget(QtGui.QLabel("Bars"), 0, 2)
        f_groupbox_layout.addWidget(f_bar_spinbox, 1, 2)
        f_groupbox_layout.addWidget(f_cancel_button, 2, 1)
        f_groupbox_layout.addWidget(f_sync_button, 2, 2)
        f_dialog.exec_()

    def scene_contextMenuEvent(self):
        self.scene_context_menu.exec_(QtGui.QCursor.pos())

    def reset_markers(self):
        for f_marker in self.drag_start_markers + self.drag_end_markers:
            f_marker.reset_default()

    def copy_markers(self):
        if self.graph_object is not None:
            global_set_audio_markers_clipboard(
                self.start_marker.value, self.end_marker.value,
                self.fade_in_marker.value, self.fade_out_marker.value)

    def paste_markers(self):
        if self.graph_object is not None and \
        AUDIO_MARKERS_CLIPBOARD is not None:
            f_markers = (self.start_marker, self.end_marker,
                         self.fade_in_marker, self.fade_out_marker)
            for f_i in range(4):
                f_markers[f_i].set_value(AUDIO_MARKERS_CLIPBOARD[f_i])

    def clear_drawn_items(self):
        self.scene.clear()
        self.drag_start_markers = []
        self.drag_end_markers = []

    def pos_to_marker_val(self, a_pos_x):
        f_result = AUDIO_ITEM_SCENE_WIDTH_RECIP * a_pos_x * 1000.0
        f_result = pydaw_util.pydaw_clip_value(
            f_result, 0.0, AUDIO_ITEM_MAX_MARKER_VAL)
        return f_result

    def scene_mousePressEvent(self, a_event):
        if self.graph_object is None:
            return
        if a_event.button() == QtCore.Qt.RightButton:
            self.scene_contextMenuEvent()
            return
        QtGui.QGraphicsScene.mousePressEvent(self.scene, a_event)
        if not a_event.isAccepted():
            self.is_drag_selecting = True
            f_pos_x = a_event.scenePos().x()
            f_val = self.pos_to_marker_val(f_pos_x)
            self.drag_start_pos = f_val
            if f_val < self.end_marker.value:
                for f_marker in self.drag_start_markers:
                    f_marker.value = f_val
                    f_marker.set_pos()
                    f_marker.callback(f_marker.value)

                if self.fade_out_marker.value <= f_val + MARKER_MIN_DIFF:
                    self.fade_out_marker.value = f_val + MARKER_MIN_DIFF
                    self.fade_out_marker.set_pos()
                    self.fade_out_marker.callback(self.fade_out_marker.value)

    def scene_mouseReleaseEvent(self, a_event):
        if self.graph_object is None:
            return
        QtGui.QGraphicsScene.mouseReleaseEvent(self.scene, a_event)
        if not a_event.isAccepted():
            self.is_drag_selecting = False
            for f_marker in self.drag_start_markers + self.drag_end_markers:
                f_marker.callback(f_marker.value)

    def scene_mouseMoveEvent(self, a_event):
        if self.graph_object is None:
            return
        QtGui.QGraphicsScene.mouseMoveEvent(self.scene, a_event)
        if not a_event.isAccepted() and self.is_drag_selecting:
            f_val = self.pos_to_marker_val(a_event.scenePos().x())

            for f_marker in self.drag_start_markers:
                if f_val < self.drag_start_pos:
                    f_marker.value = f_val
                else:
                    f_marker.value = self.drag_start_pos
                f_marker.set_pos()
            for f_marker in self.drag_end_markers:
                if f_val < self.drag_start_pos:
                    f_marker.value = self.drag_start_pos
                else:
                    f_marker.value = f_val
                f_marker.set_pos()

    def draw_item(self, a_graph_object, a_start, a_end, a_fade_in, a_fade_out):
        self.graph_object = a_graph_object
        self.length_str = ["Length: {}".format(
            pydaw_util.pydaw_seconds_to_time_str(
            self.graph_object.length_in_seconds))]
        self.path_list = a_graph_object.create_sample_graph(True)
        self.path_count = len(self.path_list)
        self.setUpdatesEnabled(False)
        self.redraw_item(a_start, a_end, a_fade_in, a_fade_out)
        self.setUpdatesEnabled(True)
        self.update()

    def redraw_item(self, a_start, a_end, a_fade_in, a_fade_out):
        self.clear_drawn_items()
        f_path_inc = AUDIO_ITEM_SCENE_HEIGHT / self.path_count
        f_path_y_pos = 0.0
        for f_path in self.path_list:
            f_pixmap = QtGui.QPixmap(AUDIO_ITEM_SCENE_WIDTH, f_path_inc)
            f_painter = QtGui.QPainter(f_pixmap)
            f_painter.setPen(self.waveform_pen)
            f_painter.setBrush(self.waveform_brush)
            f_painter.fillRect(
                0, 0, AUDIO_ITEM_SCENE_WIDTH, f_path_inc,
                QtCore.Qt.darkGray)
            f_painter.drawPath(f_path)
            f_painter.end()
            f_path_item = QtGui.QGraphicsPixmapItem(f_pixmap)
            self.scene.addItem(f_path_item)
            f_path_item.setPos(0.0, f_path_y_pos)
            f_path_y_pos += f_path_inc
        self.start_marker = pydaw_audio_marker_widget(
            0, a_start, START_END_PEN, START_END_GRADIENT,
            "S", self.graph_object, pydaw_audio_marker_widget.mode_start_end,
            1, self.start_callback)
        self.scene.addItem(self.start_marker)
        self.end_marker = pydaw_audio_marker_widget(
            1, a_end, START_END_PEN, START_END_GRADIENT, "E",
            self.graph_object, pydaw_audio_marker_widget.mode_start_end,
            1, self.end_callback)
        self.scene.addItem(self.end_marker)

        self.fade_in_marker = pydaw_audio_fade_marker_widget(
            0, a_fade_in, START_END_PEN, START_END_GRADIENT,
            "I", self.graph_object, 0, self.fade_in_callback)
        self.scene.addItem(self.fade_in_marker)
        for f_line in self.fade_in_marker.amp_lines:
            self.scene.addItem(f_line)
        self.fade_out_marker = pydaw_audio_fade_marker_widget(
            1, a_fade_out, START_END_PEN, START_END_GRADIENT, "O",
            self.graph_object, 0, self.fade_out_callback)
        self.scene.addItem(self.fade_out_marker)
        for f_line in self.fade_out_marker.amp_lines:
            self.scene.addItem(f_line)
        self.fade_in_marker.set_other(self.fade_out_marker, self.start_marker)
        self.fade_out_marker.set_other(self.fade_in_marker, self.end_marker)
        #end fade stuff
        self.start_marker.set_other(self.end_marker, self.fade_in_marker)
        self.end_marker.set_other(self.start_marker, self.fade_out_marker)
        self.start_marker.set_pos()
        self.end_marker.set_pos()
        self.fade_in_marker.set_pos()
        self.fade_out_marker.set_pos()
        self.fade_in_marker.draw_lines()
        self.fade_out_marker.draw_lines()
        self.drag_start_markers = [self.start_marker, self.fade_in_marker]
        self.drag_end_markers = [self.end_marker, self.fade_out_marker]
        self.update_label()

    def resizeEvent(self, a_resize_event):
        QtGui.QGraphicsView.resizeEvent(self, a_resize_event)
        self.scale(1.0 / self.last_x_scale, 1.0 / self.last_y_scale)
        f_rect = self.rect()
        self.last_x_scale = f_rect.width() / AUDIO_ITEM_SCENE_WIDTH
        self.last_y_scale = (f_rect.height() -
            self.scroll_bar_height) / AUDIO_ITEM_SCENE_HEIGHT
        self.scale(self.last_x_scale, self.last_y_scale)

AUDIO_LOOP_CLIPBOARD = None

def global_set_audio_loop_clipboard(a_ls, a_le):
    global AUDIO_LOOP_CLIPBOARD
    AUDIO_LOOP_CLIPBOARD = (float(a_ls), float(a_le))


class pydaw_sample_viewer_widget(pydaw_audio_item_viewer_widget):
    def __init__(self, a_start_callback, a_end_callback, a_loop_start_callback,
                 a_loop_end_callback, a_fade_in_callback, a_fade_out_callback):
        pydaw_audio_item_viewer_widget.__init__(
            self, a_start_callback, a_end_callback,
            a_fade_in_callback, a_fade_out_callback)
        self.loop_start_callback_x = a_loop_start_callback
        self.loop_end_callback_x = a_loop_end_callback
        self.scene_context_menu.addSeparator()
        self.loop_copy_action = self.scene_context_menu.addAction(
            _("Copy Loop Markers"))
        self.loop_copy_action.triggered.connect(self.copy_loop)
        self.loop_paste_action = self.scene_context_menu.addAction(
            _("Paste Loop Markers"))
        self.loop_paste_action.triggered.connect(self.paste_loop)

    def copy_loop(self):
        if self.graph_object is not None:
            global_set_audio_loop_clipboard(
                self.loop_start_marker.value, self.loop_end_marker.value)

    def paste_loop(self):
        if self.graph_object is not None and \
        AUDIO_LOOP_CLIPBOARD is not None:
            self.loop_start_marker.set_value(AUDIO_LOOP_CLIPBOARD[0])
            self.loop_end_marker.set_value(AUDIO_LOOP_CLIPBOARD[1])

    def loop_start_callback(self, a_val):
        self.loop_start_callback_x(a_val)
        self.update_label()

    def loop_end_callback(self, a_val):
        self.loop_end_callback_x(a_val)
        self.update_label()

    def draw_item(self, a_path_list, a_start, a_end, a_loop_start, a_loop_end,
                  a_fade_in, a_fade_out):
        pydaw_audio_item_viewer_widget.draw_item(
            self, a_path_list, a_start, a_end, a_fade_in, a_fade_out)
        self.loop_start_marker = pydaw_audio_marker_widget(
            0, a_loop_start, LOOP_PEN, LOOP_GRADIENT, "L",
            self.graph_object, pydaw_audio_marker_widget.mode_loop,
            2, self.loop_start_callback)
        self.scene.addItem(self.loop_start_marker)
        self.loop_end_marker = pydaw_audio_marker_widget(
            1, a_loop_end, LOOP_PEN, LOOP_GRADIENT, "L",
            self.graph_object, pydaw_audio_marker_widget.mode_loop,
            2, self.loop_end_callback)
        self.scene.addItem(self.loop_end_marker)

        self.loop_start_marker.set_other(self.loop_end_marker)
        self.loop_end_marker.set_other(self.loop_start_marker)
        self.loop_start_marker.set_pos()
        self.loop_end_marker.set_pos()

        self.drag_start_markers.append(self.loop_start_marker)
        self.drag_end_markers.append(self.loop_end_marker)
        self.update_label()


class pydaw_spectrum(QtGui.QGraphicsPathItem):
    def __init__(self, a_height, a_width):
        self.spectrum_height = float(a_height)
        self.spectrum_width = float(a_width)
        QtGui.QGraphicsPathItem.__init__(self)
        self.setPen(QtCore.Qt.white)

    def set_spectrum(self, a_message):
        self.painter_path = QtGui.QPainterPath(QtCore.QPointF(0.0, 20.0))
        self.values = a_message.split("|")
        self.painter_path.moveTo(0.0, self.spectrum_height)
        f_low = EQ_LOW_PITCH
        f_high = EQ_HIGH_PITCH
        f_width_per_point = (self.spectrum_width / float(f_high - f_low))
        f_fft_low = float(pydaw_util.SAMPLE_RATE) / 4096.0
        f_nyquist = float(pydaw_util.NYQUIST_FREQ)
        f_i = f_low
        while f_i < f_high:
            f_hz = pydaw_util.pydaw_pitch_to_hz(f_i) - f_fft_low
            f_pos = int((f_hz / f_nyquist) * len(self.values))
            f_val = float(self.values[f_pos])
            f_db = pydaw_util.pydaw_lin_to_db(f_val) - 64.0
            f_db += ((f_i - f_low) / 12.0) * 3.0
            f_db = pydaw_util.pydaw_clip_value(f_db, -70.0, 0.0)
            f_val = 1.0 - ((f_db + 70.0) / 70.0)
            f_x = f_width_per_point * (f_i - f_low)
            f_y = f_val * self.spectrum_height
            self.painter_path.lineTo(f_x, f_y)
            f_i += 0.5
        self.setPath(self.painter_path)


MODULEX_CLIPBOARD = None

MODULEX_EFFECTS_LIST = [
    "Off", "LP2", "LP4", "HP2", "HP4", "BP2", "BP4", "Notch2",
    "Notch4", "EQ", "Distortion", "Comb Filter", "Amp/Pan",
    "Limiter", "Saturator", "Formant", "Chorus", "Glitch",
    "RingMod", "LoFi", "S/H", "LP-D/W", "HP-D/W",
    "Monofier", "LP<-->HP", "Growl Filter",
    "Screech LP", "Metal Comb", "Notch-D/W", "Foldback"]

class pydaw_modulex_single:
    def __init__(self, a_title, a_port_k1, a_rel_callback, a_val_callback,
                 a_port_dict=None, a_preset_mgr=None, a_knob_size=51):
        self.group_box = QtGui.QGroupBox()
        self.group_box.contextMenuEvent = self.contextMenuEvent
        self.group_box.setObjectName("plugin_groupbox")
        if a_title is not None:
            self.group_box.setTitle(str(a_title))
        self.layout = QtGui.QGridLayout()
        self.layout.setMargin(3)
        #self.layout.setAlignment(QtCore.Qt.AlignCenter)
        self.group_box.setLayout(self.layout)
        self.knobs = []
        for f_i in range(3):
            f_knob = pydaw_knob_control(
                a_knob_size, "", a_port_k1 + f_i,
                a_rel_callback, a_val_callback, 0, 127, 64,
                a_port_dict=a_port_dict, a_preset_mgr=a_preset_mgr)
            f_knob.add_to_grid_layout(self.layout, f_i)
            self.knobs.append(f_knob)
        self.combobox = pydaw_combobox_control(
            132, "Type", a_port_k1 + 3, a_rel_callback, a_val_callback,
            MODULEX_EFFECTS_LIST, a_port_dict=a_port_dict,
            a_preset_mgr=a_preset_mgr, a_default_index=0)
        self.layout.addWidget(self.combobox.name_label, 0, 3)
        self.combobox.control.currentIndexChanged.connect(
            self.type_combobox_changed)
        self.layout.addWidget(self.combobox.control, 1, 3)

    def wheel_event(self, a_event=None):
        pass

    def disable_mousewheel(self):
        """ Mousewheel events cause problems with
            per-audio-item-fx because they rely on the mouse release event.
        """
        for knob in self.knobs:
            knob.control.wheelEvent = self.wheel_event
        self.combobox.control.wheelEvent = self.wheel_event

    def contextMenuEvent(self, a_event):
        f_menu = QtGui.QMenu(self.group_box)
        f_copy_action = f_menu.addAction(_("Copy"))
        f_copy_action.triggered.connect(self.copy_settings)
        f_cut_action = f_menu.addAction(_("Cut"))
        f_cut_action.triggered.connect(self.cut_settings)
        f_paste_action = f_menu.addAction(_("Paste"))
        f_paste_action.triggered.connect(self.paste_settings)
        f_paste_and_copy_action = f_menu.addAction(_("Paste and Copy"))
        f_paste_and_copy_action.triggered.connect(self.paste_and_copy)
        f_menu.addAction(f_paste_and_copy_action)
        f_reset_action = f_menu.addAction(_("Reset"))
        f_reset_action.triggered.connect(self.reset_settings)
        f_menu.exec_(QtGui.QCursor.pos())

    def copy_settings(self):
        global MODULEX_CLIPBOARD
        MODULEX_CLIPBOARD = self.get_class()

    def paste_and_copy(self):
        """ Copy the existing setting and then paste,
            for rearranging effects
        """
        self.paste_settings(True)

    def paste_settings(self, a_copy=False):
        global MODULEX_CLIPBOARD
        if MODULEX_CLIPBOARD is None:
            QtGui.QMessageBox.warning(self.group_box, _("Error"),
            _("Nothing copied to clipboard"))
        else:
            f_class = self.get_class()
            self.set_from_class(MODULEX_CLIPBOARD)
            self.update_all_values()
            if a_copy:
                MODULEX_CLIPBOARD = f_class

    def update_all_values(self):
        for f_knob in self.knobs:
            f_knob.control_value_changed(f_knob.get_value())
        self.combobox.control_value_changed(self.combobox.get_value())

    def cut_settings(self):
        self.copy_settings()
        self.reset_settings()

    def reset_settings(self):
        self.set_from_class(pydaw_audio_item_fx(64, 64, 64, 0))
        self.update_all_values()

    def set_from_class(self, a_class):
        """ a_class is a pydaw_audio_item_fx instance """
        self.knobs[0].set_value(a_class.knobs[0])
        self.knobs[1].set_value(a_class.knobs[1])
        self.knobs[2].set_value(a_class.knobs[2])
        self.combobox.set_value(a_class.fx_type)

    def get_class(self):
        """ return a pydaw_audio_item_fx instance """
        return pydaw_audio_item_fx(
            self.knobs[0].control.value(),
            self.knobs[1].control.value(),
            self.knobs[2].control.value(),
            self.combobox.control.currentIndex())

    def type_combobox_changed(self, a_val):
        if a_val == 0: #Off
            self.knobs[0].name_label.setText("")
            self.knobs[1].name_label.setText("")
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = KC_NONE
            self.knobs[1].val_conversion = KC_NONE
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].value_label.setText("")
            self.knobs[2].value_label.setText("")
        elif a_val == 1: #LP2
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = KC_127_PITCH
            self.knobs[1].val_conversion = KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 2: #LP4
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = KC_127_PITCH
            self.knobs[1].val_conversion = KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 3: #HP2
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = KC_127_PITCH
            self.knobs[1].val_conversion = KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 4: #HP4
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = KC_127_PITCH
            self.knobs[1].val_conversion = KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 5: #BP2
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = KC_127_PITCH
            self.knobs[1].val_conversion = KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 6: #BP4
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = KC_127_PITCH
            self.knobs[1].val_conversion = KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 7: #Notch2
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = KC_127_PITCH
            self.knobs[1].val_conversion = KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 8: #Notch4
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = KC_127_PITCH
            self.knobs[1].val_conversion = KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 9: #EQ
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("BW"))
            self.knobs[2].name_label.setText(_("Gain"))
            self.knobs[0].val_conversion = KC_127_PITCH
            self.knobs[1].val_conversion = KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(1.0, 6.0)
            self.knobs[2].val_conversion = KC_127_ZERO_TO_X
            self.knobs[2].set_127_min_max(-24.0, 24.0)
            self.knobs[1].value_label.setText("")
        elif a_val == 10: #Distortion
            self.knobs[0].name_label.setText(_("Gain"))
            self.knobs[1].name_label.setText(_("D/W"))
            self.knobs[2].name_label.setText(_("Out"))
            self.knobs[0].val_conversion = KC_127_ZERO_TO_X
            self.knobs[0].set_127_min_max(0.0, 48.0)
            self.knobs[1].val_conversion = KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = KC_127_ZERO_TO_X
            self.knobs[2].set_127_min_max(-30.0, 0.0)
        elif a_val == 11: #Comb Filter
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Amt"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = KC_NONE
            self.knobs[1].val_conversion = KC_NONE
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].value_label.setText("")
            self.knobs[2].value_label.setText("")
        elif a_val == 12: #Amp/Panner
            self.knobs[0].name_label.setText(_("Pan"))
            self.knobs[1].name_label.setText(_("Amp"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = KC_NONE
            self.knobs[1].val_conversion = KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-40.0, 24.0)
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].value_label.setText("")
            self.knobs[2].value_label.setText("")
        elif a_val == 13: #Limiter
            self.knobs[0].name_label.setText(_("Thresh"))
            self.knobs[1].name_label.setText(_("Ceil"))
            self.knobs[2].name_label.setText(_("Rel"))
            self.knobs[0].val_conversion = KC_127_ZERO_TO_X
            self.knobs[0].set_127_min_max(-30.0, 0.0)
            self.knobs[1].val_conversion = KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-12.0, -0.1)
            self.knobs[2].val_conversion = KC_127_ZERO_TO_X_INT
            self.knobs[2].set_127_min_max(50.0, 1500.0)
        elif a_val == 14: #Saturator
            self.knobs[0].name_label.setText(_("Gain"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[2].name_label.setText(_("Out"))
            self.knobs[0].val_conversion = KC_127_ZERO_TO_X
            self.knobs[0].set_127_min_max(-12.0, 12.0)
            self.knobs[1].val_conversion = KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = KC_127_ZERO_TO_X
            self.knobs[2].set_127_min_max(-12.0, 12.0)
        elif a_val == 15: #Formant Filter
            self.knobs[0].name_label.setText(_("Vowel"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 16: #Chorus
            self.knobs[0].name_label.setText(_("Rate"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = KC_127_ZERO_TO_X
            self.knobs[0].set_127_min_max(0.3, 6.0)
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 17: #Glitch
            self.knobs[0].name_label.setText(_("Pitch"))
            self.knobs[1].name_label.setText(_("Glitch"))
            self.knobs[2].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 18: #RingMod
            self.knobs[0].name_label.setText(_("Pitch"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 19: #LoFi
            self.knobs[0].name_label.setText(_("Bits"))
            self.knobs[1].name_label.setText("")
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = KC_127_ZERO_TO_X
            self.knobs[0].set_127_min_max(4.0, 16.0)
            self.knobs[1].val_conversion = KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 20: #Sample and Hold
            self.knobs[0].name_label.setText(_("Pitch"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 21: #LP2-Dry/Wet
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = KC_127_PITCH
            self.knobs[1].val_conversion = KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 22: #HP2-Dry/Wet
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = KC_127_PITCH
            self.knobs[1].val_conversion = KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 23: #Monofier
            self.knobs[0].name_label.setText(_("Pan"))
            self.knobs[1].name_label.setText(_("Amp"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = KC_NONE
            self.knobs[1].val_conversion = KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 6.0)
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].value_label.setText("")
            self.knobs[2].value_label.setText("")
        elif a_val == 24: #LP<-->HP
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText(("LP/HP"))
            self.knobs[0].val_conversion = KC_127_PITCH
            self.knobs[1].val_conversion = KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 25: #Growl Filter
            self.knobs[0].name_label.setText(_("Vowel"))
            self.knobs[1].name_label.setText(_("Wet"))
            self.knobs[2].name_label.setText(_("Type"))
            self.knobs[0].val_conversion = KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].val_conversion = KC_NONE
            self.knobs[1].value_label.setText("")
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 26: #Screech LP
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText("")
            self.knobs[0].val_conversion = KC_127_PITCH
            self.knobs[1].val_conversion = KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 27: #Metal Comb
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Amt"))
            self.knobs[2].name_label.setText(_("Spread"))
            self.knobs[0].val_conversion = KC_NONE
            self.knobs[1].val_conversion = KC_NONE
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[0].value_label.setText("")
            self.knobs[1].value_label.setText("")
            self.knobs[2].value_label.setText("")
        elif a_val == 28: #Notch4-Dry/Wet
            self.knobs[0].name_label.setText(_("Freq"))
            self.knobs[1].name_label.setText(_("Res"))
            self.knobs[2].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = KC_127_PITCH
            self.knobs[1].val_conversion = KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(-30.0, 0.0)
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")
        elif a_val == 29: #Foldback Distortion
            self.knobs[0].name_label.setText(_("Thresh"))
            self.knobs[1].name_label.setText(_("Gain"))
            self.knobs[2].name_label.setText(_("Wet"))
            self.knobs[0].val_conversion = KC_127_ZERO_TO_X
            self.knobs[0].set_127_min_max(-12.0, 0.0)
            self.knobs[1].val_conversion = KC_127_ZERO_TO_X
            self.knobs[1].set_127_min_max(0.0, 12.0)
            self.knobs[2].val_conversion = KC_NONE
            self.knobs[2].value_label.setText("")

        self.knobs[0].set_value(self.knobs[0].control.value())
        self.knobs[1].set_value(self.knobs[1].control.value())
        self.knobs[2].set_value(self.knobs[2].control.value())


class pydaw_per_audio_item_fx_widget:
    def __init__(self, a_rel_callback, a_val_callback):
        self.effects = []
        self.widget = QtGui.QWidget()
        self.widget.setObjectName("plugin_ui")
        self.layout = QtGui.QVBoxLayout()
        self.widget.setLayout(self.layout)
        f_port = 0
        for f_i in range(8):
            f_effect = pydaw_modulex_single(_("FX{}").format(f_i), f_port,
                                            a_rel_callback, a_val_callback)
            f_effect.disable_mousewheel()
            self.effects.append(f_effect)
            self.layout.addWidget(f_effect.group_box)
            f_port += 4
        self.widget.setGeometry(0, 0, 348, 1100)  #ensure minimum size
        self.scroll_area = QtGui.QScrollArea()
        self.scroll_area.setGeometry(0, 0, 360, 1120)
        self.scroll_area.setWidget(self.widget)

    def set_from_list(self, a_list):
        """ a_class is a pydaw_audio_item_fx instance """
        for f_i in range(len(a_list)):
            self.effects[f_i].set_from_class(a_list[f_i])

    def get_list(self):
        """ return a list of pydaw_audio_item_fx instances """
        f_result = []
        for f_effect in self.effects:
            f_result.append(f_effect.get_class())
        return f_result

    def clear_effects(self):
        for f_effect in self.effects:
            f_effect.combobox.set_value(0)
            for f_knob in f_effect.knobs:
                f_knob.set_value(64)

class pydaw_abstract_plugin_ui:
    def __init__(self, a_val_callback, a_project, a_plugin_uid, a_stylesheet,
                 a_configure_callback, a_folder, a_midi_learn_callback,
                 a_cc_map_callback, a_can_resize=False):
        self.plugin_uid = int(a_plugin_uid)
        self.folder = str(a_folder)
        self.can_resize = a_can_resize
        self.pydaw_project = a_project
        self.val_callback = a_val_callback
        self.configure_callback = a_configure_callback
        self.midi_learn_callback = a_midi_learn_callback
        self.cc_map_callback = a_cc_map_callback
        self.widget = QtGui.QScrollArea()
        self.widget.setObjectName("plugin_ui")
        self.widget.setMinimumSize(500, 500)
        self.widget.setStyleSheet(str(a_stylesheet))
        self.widget.closeEvent = self.widget_close_event

        self.widget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.widget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scrollarea_widget = QtGui.QWidget()
        self.scrollarea_widget.setObjectName("plugin_ui")
        self.widget.setWidgetResizable(True)
        self.widget.setWidget(self.scrollarea_widget)

        self.layout = QtGui.QVBoxLayout()
        self.layout.setMargin(2)
        self.scrollarea_widget.setLayout(self.layout)
        self.port_dict = {}
        self.effects = []
        self.configure_dict = {}
        self.cc_map = {}
        self.save_file_on_exit = True
        self.is_quitting = False
        self._plugin_name = None

    def set_midi_learn(self, a_port_map):
        self.port_map = a_port_map
        self.reverse_port_map = {int(v):k for k, v in self.port_map.items()}
        for f_port in (int(x) for x in a_port_map.values()):
            self.port_dict[f_port].set_midi_learn(
                self.midi_learn, self.get_cc_map)

    def midi_learn(self, a_ctrl, a_cc_num=None, a_low=None, a_high=None):
        if a_cc_num is not None:
            if a_low is not None:
                self.cc_map[a_cc_num].ports[a_ctrl.port_num] = (a_low, a_high)
                self.set_cc_map(a_cc_num)
                return
            if a_cc_num in self.cc_map and \
            self.cc_map[a_cc_num].has_port(a_ctrl.port_num):
                if self.cc_map[a_cc_num].remove_port(a_ctrl.port_num):
                    self.set_cc_map(a_cc_num)
                    if not self.cc_map[a_cc_num].ports:
                        self.cc_map.pop(a_cc_num)
            else:
                self.update_cc_map(a_cc_num, a_ctrl)
        else:
            self.midi_learn_callback(self, a_ctrl)

    def update_cc_map(self, a_cc_num, a_ctrl):
        a_cc_num = int(a_cc_num)
        if not a_cc_num in self.cc_map:
            self.cc_map[a_cc_num] = cc_mapping(a_cc_num)
        f_result = self.cc_map[a_cc_num].set_port(a_ctrl.port_num)
        if f_result:
            QtGui.QMessageBox.warning(
                self.widget, _("Error"), _("CCs can only be assigned to 5 "
                "controls at a time, CC {} is already assigned to "
                "{}").format(a_cc_num,
                [self.reverse_port_map[x] for x in f_result]))
        else:
            self.set_cc_map(a_cc_num)

    def get_cc_map(self):
        return self.cc_map

    def set_cc_map(self, a_cc_num):
        f_str = str(self.cc_map[a_cc_num])
        self.cc_map_callback(self.plugin_uid, f_str[2:])

    def get_plugin_name(self):
        return self._plugin_name

    def set_default_size(self):
        """ Override this for plugins that can't properly resize
            automatically and can be resized
        """
        pass

    def delete_plugin_file(self):
        self.save_file_on_exit = False

    def show_widget(self):
        self.layout.update()
        self.layout.activate()
        f_size = self.scrollarea_widget.size()
        f_desktop_size = QtGui.QApplication.desktop().screen().rect()

        f_x = f_size.width() + 21
        f_y = f_size.height()

        if self.can_resize or \
        f_x > f_desktop_size.width() - 40 or \
        f_y > f_desktop_size.height() - 40:
            f_y += 21
            f_x = pydaw_util.pydaw_clip_value(
                f_x, 400, f_desktop_size.width())
            f_y = pydaw_util.pydaw_clip_value(
                f_y, 400, f_desktop_size.height())
            self.widget.resize(f_x, f_y)
            self.set_default_size()
        else:
            self.widget.setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff)
            self.widget.setVerticalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff)
            self.widget.setFixedSize(f_x, f_y)
        self.widget.show()

    def open_plugin_file(self):
        if self.folder is not None:
            f_file_path = "{}/{}".format(self.folder, self.plugin_uid)
            if os.path.isfile(f_file_path):
                f_file = pydaw_plugin_file(f_file_path)
                for k, v in f_file.port_dict.items():
                    self.set_control_val(int(k), v)
                for k, v in f_file.configure_dict.items():
                    self.set_configure(k, v)
                self.cc_map = f_file.cc_map
            else:
                print("pydaw_abstract_plugin_ui.open_plugin_file():"
                    " '{}' did not exist, not loading.".format(f_file_path))

    def raise_widget(self):
        self.widget.raise_()

    def save_plugin_file(self):
        if self.folder is not None:
            f_file = pydaw_plugin_file.from_dict(
                self.port_dict, self.configure_dict, self.cc_map)
            self.pydaw_project.save_file(
                pydaw_folder_plugins, self.plugin_uid, str(f_file))
            self.pydaw_project.commit(
                _("Update controls for {}").format(self.track_name))
            self.pydaw_project.flush_history()

    def widget_close_event(self, a_event):
        if self.save_file_on_exit:
            self.save_plugin_file()
        if self.is_quitting:
            a_event.accept()
        else:
            self.widget.hide()
            a_event.ignore()
        #QtGui.QWidget.closeEvent(self.widget, a_event)

    def plugin_rel_callback(self, a_port, a_val):
        """ This can optionally be implemented, otherwise it's
            just ignored
        """
        pass

    def plugin_val_callback(self, a_port, a_val):
        self.val_callback(self.plugin_uid, a_port, a_val)

    def set_control_val(self, a_port, a_val):
        f_port = int(a_port)
        if f_port in self.port_dict:
            self.port_dict[int(a_port)].set_value(a_val)
        else:
            print("pydaw_abstract_plugin_ui.set_control_val():  "
                "Did not have port {}".format(f_port))

    def set_cc_val(self, a_cc, a_val):
        a_cc = int(a_cc)
        if a_cc in self.cc_map:
            a_val = float(a_val) * 0.007874016 # / 127.0
            for f_port, f_tuple in self.cc_map[a_cc].ports.items():
                f_low, f_high = f_tuple
                f_frac = (a_val * (f_high - f_low)) + f_low
                f_ctrl = self.port_dict[f_port]
                f_min = float(f_ctrl.control.minimum())
                f_max = float(f_ctrl.control.maximum())
                f_val = int(f_frac * (f_max - f_min) + f_min)
                f_ctrl.set_value(f_val, True)

    def configure_plugin(self, a_key, a_message):
        """ Override this function to allow str|str key/value pair
            messages to be sent to the back-end
        """
        pass

    def set_configure(self, a_key, a_message):
        """ Override this function to configure the
            plugin from the state file
        """
        pass

    def reconfigure_plugin(self, a_dict):
        """ Override this to re-configure a plugin from scratch with the
            values in a_dict
        """
        pass

    def ui_message(self, a_name, a_value):
        """ Override to display ephemeral data such as
            meters/scopes/spectra using key value pairs
        """
        print("Unknown ui_message: {} : {}".format(a_name, a_value))

    def set_window_title(self, a_track_name):
        pass  #Override this function



