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
import subprocess
import time
import random
import shutil

from PyQt4 import QtGui, QtCore
from libpydaw import *
from mkplugins import *

from libpydaw.pydaw_util import *
from libpydaw.pydaw_widgets import *
from libpydaw.translate import _
import libpydaw.strings
import libedmnext.strings
import libmk
from libmk import mk_project
from libedmnext import *

def pydaw_get_current_region_length():
    if CURRENT_REGION is None:
        return 8
    f_result = CURRENT_REGION.region_length_bars
    if f_result == 0:
        return 8
    else:
        return f_result

def pydaw_get_region_length(a_index):
    f_song = PROJECT.get_song()
    if not a_index in f_song.regions:
        return 8
    else:
        f_region = PROJECT.get_region_by_uid(f_song.regions[a_index])
        f_result = f_region.region_length_bars
        if f_result == 0:
            return 8
        else:
            return f_result

REGION_TIME = [0] * 300  # Fast lookup of song times in seconds

def global_update_region_time():
    global REGION_TIME
    REGION_TIME = []
    f_seconds_per_beat = 60.0 / float(TRANSPORT.tempo_spinbox.value())
    f_total = 0.0
    for x in range(300):
        REGION_TIME.append(f_total)
        f_total += pydaw_get_region_length(x) * 4.0 * f_seconds_per_beat

def global_get_audio_file_from_clipboard():
    f_clipboard = QtGui.QApplication.clipboard()
    f_path = f_clipboard.text()
    if not f_path:
        QtGui.QMessageBox.warning(
            MAIN_WINDOW, _("Error"), _("No text in the system clipboard"))
    else:
        f_path = str(f_path).strip()
        if os.path.isfile(f_path):
            print(f_path)
            return f_path
        else:
            f_path = f_path[:100]
            QtGui.QMessageBox.warning(
                MAIN_WINDOW, _("Error"),
                _("{} is not a valid file").format(f_path))
    return None


def set_tooltips_enabled(a_enabled):
    """ Set extensive tooltips as an alternative to
        maintaining a separate user manual
    """
    libmk.TOOLTIPS_ENABLED = a_enabled

    f_list = [SONG_EDITOR, AUDIO_SEQ_WIDGET, PIANO_ROLL_EDITOR,
              MAIN_WINDOW, AUDIO_SEQ, TRANSPORT,
              REGION_EDITOR, MIXER_WIDGET] + list(AUTOMATION_EDITORS)
    for f_widget in f_list:
        f_widget.set_tooltips(a_enabled)

    pydaw_util.set_file_setting("tooltips", int(a_enabled))


def pydaw_current_region_is_none():
    if CURRENT_REGION is None:
        QtGui.QMessageBox.warning(
            MAIN_WINDOW, _("Error"),
            _("You must create or select a region first by clicking "
            "in the song editor above."))
        return True
    return False

def pydaw_scale_to_rect(a_to_scale, a_scale_to):
    """ Returns a tuple that scales one QRectF to another """
    f_x = (a_scale_to.width() / a_to_scale.width())
    f_y = (a_scale_to.height() / a_to_scale.height())
    return (f_x, f_y)


CURRENT_SONG_INDEX = None

class song_editor:
    def __init__(self):
        self.song = pydaw_song()
        self.last_midi_dir = None
        self.main_vlayout = QtGui.QVBoxLayout()
        self.table_widget = QtGui.QTableWidget()
        self.table_widget.setColumnCount(300)
        self.table_widget.setRowCount(1)
        self.table_widget.setFixedHeight(87)
        self.table_widget.setHorizontalScrollMode(
            QtGui.QAbstractItemView.ScrollPerPixel)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setAutoScroll(True)
        self.table_widget.setAutoScrollMargin(1)
        self.table_widget.setRowHeight(0, 50)
        self.table_widget.horizontalHeader().setResizeMode(
            QtGui.QHeaderView.Fixed)
        self.table_widget.verticalHeader().setResizeMode(
            QtGui.QHeaderView.Fixed)
        self.table_widget.cellClicked.connect(self.cell_clicked)
        self.table_widget.setDragDropOverwriteMode(False)
        self.table_widget.setDragEnabled(True)
        self.table_widget.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.table_widget.dropEvent = self.table_drop_event
        self.table_widget.setEditTriggers(
            QtGui.QAbstractItemView.NoEditTriggers)
        self.main_vlayout.addWidget(self.table_widget)

        self.table_widget.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.rename_action = QtGui.QAction(
            _("Rename Region"), self.table_widget)
        self.rename_action.triggered.connect(self.on_rename_region)
        self.table_widget.addAction(self.rename_action)
        self.delete_action = QtGui.QAction(
            _("Delete Region(s)"), self.table_widget)
        self.delete_action.triggered.connect(self.on_delete)
        # Too often, this was being triggered by accident,
        # making it a PITA as there
        # was no easy way to tell which widget had focus...
        #self.delete_action.setShortcut(QtGui.QKeySequence.Delete)
        #self.delete_action.setShortcutContext(
        #    QtCore.Qt.WidgetWithChildrenShortcut)
        self.table_widget.addAction(self.delete_action)

    def add_qtablewidgetitem(self, a_name, a_region_num):
        """ Adds a properly formatted item.  This is not for
            creating empty items...
        """
        f_qtw_item = QtGui.QTableWidgetItem(a_name)
        f_qtw_item.setBackground(pydaw_region_gradient)
        f_qtw_item.setTextAlignment(QtCore.Qt.AlignCenter)
        f_qtw_item.setFlags(f_qtw_item.flags() | QtCore.Qt.ItemIsSelectable)
        self.table_widget.setItem(0, a_region_num, f_qtw_item)

    def open_song(self):
        """ This method clears the existing song from the editor and opens the
            one currently in PROJECT
        """
        self.table_widget.setUpdatesEnabled(False)
        self.table_widget.clearContents()
        self.song = PROJECT.get_song()
        f_region_dict = PROJECT.get_regions_dict()
        for f_pos, f_region in list(self.song.regions.items()):
            self.add_qtablewidgetitem(
            f_region_dict.get_name_by_uid(f_region), f_pos)
        self.table_widget.setUpdatesEnabled(True)
        self.table_widget.update()
        #global_open_audio_items()
        self.clipboard = []

    def cell_clicked(self, x, y):
        if libmk.IS_PLAYING:
            return
        f_cell = self.table_widget.item(x, y)
        if f_cell is None:
            def song_ok_handler():
                if f_new_radiobutton.isChecked():
                    f_uid = PROJECT.create_empty_region(
                        str(f_new_lineedit.text()))
                    f_msg = _("Create empty region '{}' at {}").format(
                        f_new_lineedit.text(), y)
                elif f_copy_radiobutton.isChecked():
                    f_uid = PROJECT.copy_region(
                        str(f_copy_combobox.currentText()),
                        str(f_new_lineedit.text()))
                    f_msg = (_("Create new region '{}' at {} copying from "
                        "{}")).format(f_new_lineedit.text(), y,
                        f_copy_combobox.currentText())
                self.add_qtablewidgetitem(f_new_lineedit.text(), y)
                self.song.add_region_ref_by_uid(y, f_uid)
                REGION_SETTINGS.open_region(f_new_lineedit.text())
                global CURRENT_SONG_INDEX
                CURRENT_SONG_INDEX = y
                PROJECT.save_song(self.song)
                PROJECT.commit(f_msg)
                TRANSPORT.set_region_value(y)
                TRANSPORT.set_bar_value(0)
                global_update_region_time()
                f_window.close()

            def song_cancel_handler():
                f_window.close()

            def on_name_changed():
                f_new_lineedit.setText(
                    pydaw_remove_bad_chars(f_new_lineedit.text()))

            def on_current_index_changed(a_index):
                f_copy_radiobutton.setChecked(True)

            def on_import_midi():
                f_window.close()
                self.on_import_midi(y)

            f_window = QtGui.QDialog(MAIN_WINDOW)
            f_window.setWindowTitle(_("Add region to song..."))
            f_window.setMinimumWidth(240)
            f_layout = QtGui.QGridLayout()
            f_window.setLayout(f_layout)
            f_new_radiobutton = QtGui.QRadioButton()
            f_new_radiobutton.setChecked(True)
            f_layout.addWidget(f_new_radiobutton, 0, 0)
            f_layout.addWidget(QtGui.QLabel(_("New:")), 0, 1)
            f_new_lineedit = QtGui.QLineEdit(
                PROJECT.get_next_default_region_name())
            f_new_lineedit.setMaxLength(24)
            f_new_lineedit.editingFinished.connect(on_name_changed)
            f_layout.addWidget(f_new_lineedit, 0, 2)
            f_copy_radiobutton = QtGui.QRadioButton()
            f_layout.addWidget(f_copy_radiobutton, 1, 0)
            f_copy_combobox = QtGui.QComboBox()
            f_copy_combobox.addItems(PROJECT.get_region_list())
            f_copy_combobox.currentIndexChanged.connect(
                on_current_index_changed)
            f_layout.addWidget(QtGui.QLabel(_("Copy from:")), 1, 1)
            f_layout.addWidget(f_copy_combobox, 1, 2)
            f_import_midi = QtGui.QPushButton("Import MIDI File")
            f_import_midi.pressed.connect(on_import_midi)
            f_layout.addWidget(f_import_midi, 3, 2)
            f_ok_cancel_layout = QtGui.QHBoxLayout()
            f_layout.addLayout(f_ok_cancel_layout, 5, 2)
            f_ok_button = QtGui.QPushButton(_("OK"))
            f_ok_cancel_layout.addWidget(f_ok_button)
            f_ok_button.clicked.connect(song_ok_handler)
            f_ok_button.setDefault(True)
            f_cancel_button = QtGui.QPushButton(_("Cancel"))
            f_ok_cancel_layout.addWidget(f_cancel_button)
            f_cancel_button.clicked.connect(song_cancel_handler)
            f_window.move(QtGui.QCursor.pos())
            f_window.exec_()
        else:
            REGION_SETTINGS.open_region(str(f_cell.text()))
            global CURRENT_SONG_INDEX
            CURRENT_SONG_INDEX = y
            REGION_EDITOR.scene.clearSelection()
            TRANSPORT.set_region_value(y)
            TRANSPORT.set_bar_value(0)

    def on_import_midi(self, a_index):
        self.midi_file = None

        def ok_handler():
            if self.midi_file is None:
                QtGui.QMessageBox.warning(
                    f_window, _("Error"), _("File name cannot be empty"))
                return
            f_item_name_str = str(f_item_name.text())
            if f_item_name_str == "":
                QtGui.QMessageBox.warning(
                    f_window, _("Error"), _("File name cannot be empty"))
                return
            if not self.midi_file.populate_region_from_track_map(
            PROJECT, f_item_name_str, a_index):
                QtGui.QMessageBox.warning(f_window, _("Error"),
                _("No available slots for inserting a region, delete "
                "an existing region from the song editor first"))
            else:
                PROJECT.commit(_("Import MIDI file"))
                SONG_EDITOR.open_song()
            f_window.close()

        def cancel_handler():
            f_window.close()

        def file_name_select():
            if self.last_midi_dir is None:
                f_dir_name = global_default_project_folder
            else:
                f_dir_name = self.last_midi_dir
            f_file_name = QtGui.QFileDialog.getOpenFileName(
                parent=self.table_widget, caption=_('Open MIDI File'),
                directory=f_dir_name, filter='MIDI File (*.mid)')
            if not f_file_name is None and not str(f_file_name) == "":
                self.midi_file = pydaw_midi_file_to_items(f_file_name)
                f_name.setText(f_file_name)
                self.last_midi_dir = os.path.dirname(str(f_file_name))
                if str(f_item_name.text()).strip() == "":
                    f_item_name.setText(pydaw_remove_bad_chars(
                        f_file_name.split("/")[-1].replace(".", "-")))

        def item_name_changed(a_val=None):
            f_item_name.setText(pydaw_remove_bad_chars(f_item_name.text()))

        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Import MIDI File..."))
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

        f_item_name = QtGui.QLineEdit()
        f_item_name.setMaxLength(24)
        f_layout.addWidget(QtGui.QLabel(_("Item Name:")), 2, 0)
        f_item_name.editingFinished.connect(item_name_changed)
        f_layout.addWidget(f_item_name, 2, 1)

        f_info_label = QtGui.QLabel()
        f_layout.addWidget(f_info_label, 4, 1)

        f_ok_layout = QtGui.QHBoxLayout()
        f_ok_layout.addItem(
            QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Minimum))
        f_ok = QtGui.QPushButton(_("OK"))
        f_ok.pressed.connect(ok_handler)
        f_ok_layout.addWidget(f_ok)
        f_layout.addLayout(f_ok_layout, 9, 1)
        f_cancel = QtGui.QPushButton(_("Cancel"))
        f_cancel.pressed.connect(cancel_handler)
        f_layout.addWidget(f_cancel, 9, 2)
        f_window.exec_()

    def set_tooltips(self, a_on):
        if a_on:
            self.table_widget.setToolTip(libedmnext.strings.song_editor)
        else:
            self.table_widget.setToolTip("")

    def on_delete(self):
        if not self.table_widget.selectedIndexes():
            return
        f_commit_list = []
        for f_index in self.table_widget.selectedIndexes():
            f_item = self.table_widget.item(f_index.row(), f_index.column())
            if f_item is not None and str(f_item.text()) != "":
                f_commit_list.append(str(f_index.column()))
                f_empty = QtGui.QTableWidgetItem()
                self.table_widget.setItem(
                    f_index.row(), f_index.column(), f_empty)
        if f_commit_list:
            self.tablewidget_to_song()
            REGION_SETTINGS.clear_items()
            REGION_SETTINGS.region_name_lineedit.setText("")
            REGION_SETTINGS.enabled = False
            REGION_SETTINGS.update_region_length()
            PROJECT.commit(
                _("Deleted region references at {}").format(
                ", ".join(f_commit_list)))

    def on_rename_region(self):
        f_item = self.table_widget.currentItem()
        if f_item is None:
            return

        f_item_text = str(f_item.text())

        if f_item_text == "":
            return

        f_index = self.table_widget.currentColumn()

        def ok_handler():
            f_new_name = str(f_new_lineedit.text())
            if f_new_name == "":
                QtGui.QMessageBox.warning(
                    self.table_widget, _("Error"), _("Name cannot be blank"))
                return
            PROJECT.rename_region(f_item_text, f_new_name)
            PROJECT.commit(_("Rename region"))
            SONG_EDITOR.open_song()
            REGION_SETTINGS.open_region(f_new_name)
            SONG_EDITOR.table_widget.setCurrentCell(0, f_index)
            f_window.close()

        def cancel_handler():
            f_window.close()

        def on_name_changed():
            f_new_lineedit.setText(
                pydaw_remove_bad_chars(f_new_lineedit.text()))

        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Rename region..."))
        f_layout = QtGui.QGridLayout()
        f_window.setLayout(f_layout)
        f_new_lineedit = QtGui.QLineEdit()
        f_new_lineedit.editingFinished.connect(on_name_changed)
        f_new_lineedit.setMaxLength(24)
        f_layout.addWidget(QtGui.QLabel(_("New name:")), 0, 0)
        f_layout.addWidget(f_new_lineedit, 0, 1)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_layout.addWidget(f_ok_button, 5, 0)
        f_ok_button.clicked.connect(ok_handler)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_layout.addWidget(f_cancel_button, 5, 1)
        f_cancel_button.clicked.connect(cancel_handler)
        f_window.exec_()

    def table_drop_event(self, a_event):
        QtGui.QTableWidget.dropEvent(self.table_widget, a_event)
        a_event.acceptProposedAction()
        self.tablewidget_to_song()
        self.table_widget.clearSelection()
        PROJECT.commit(_("Drag-n-drop song item(s)"))
        self.select_current_region()

    def select_current_region(self):
        if not CURRENT_REGION_NAME:
            return
        for f_i in range(0, 300):
            f_item = self.table_widget.item(0, f_i)
            if f_item and str(f_item.text()) == CURRENT_REGION_NAME:
                f_item.setSelected(True)
                global CURRENT_SONG_INDEX
                CURRENT_SONG_INDEX = f_i
                TRANSPORT.set_region_value(f_i)
                TRANSPORT.set_bar_value(0)
                global_update_region_time()

    def tablewidget_to_song(self):
        """ Flush the edited content of the QTableWidget back to
            the native song class...
        """
        self.song.regions = {}
        f_uid_dict = PROJECT.get_regions_dict()
        global CURRENT_SONG_INDEX
        CURRENT_SONG_INDEX = None
        for f_i in range(0, 300):
            f_item = self.table_widget.item(0, f_i)
            if f_item:
                if str(f_item.text()) != "":
                    self.song.add_region_ref_by_name(
                        f_i, f_item.text(), f_uid_dict)
                if str(f_item.text()) == CURRENT_REGION_NAME:
                    CURRENT_SONG_INDEX = f_i
                    print(str(f_i))
        PROJECT.save_song(self.song)
        self.open_song()

    def open_first_region(self):
        for f_i in range(300):
            f_item = self.table_widget.item(0, f_i)
            if f_item is not None and str(f_item.text()) != "":
                REGION_SETTINGS.open_region(str(f_item.text()))
                TRANSPORT.set_region_value(f_i)
                f_item.setSelected(True)
                break


def global_update_hidden_rows(a_val=None):
    return # TODO
#    REGION_EDITOR.setUpdatesEnabled(False)
#    if CURRENT_REGION and REGION_SETTINGS.hide_inactive:
#        f_active = {x.track_num for x in CURRENT_REGION.items}
#        for k, v in TRACK_PANEL.tracks.items():
#            v.group_box.setHidden(k not in f_active)
#    else:
#        for v in TRACK_PANEL.tracks.values():
#            v.group_box.setHidden(False)
#    REGION_EDITOR.setUpdatesEnabled(True)
#    REGION_EDITOR.update()


CURRENT_REGION = None
CURRENT_REGION_NAME = None

class region_settings:
    def __init__(self):
        self.enabled = False
        self.hlayout0 = QtGui.QHBoxLayout()
        self.region_num_label = QtGui.QLabel()
        self.region_num_label.setText(_("Region:"))
        self.hlayout0.addWidget(self.region_num_label)
        self.region_name_lineedit = QtGui.QLineEdit()
        self.region_name_lineedit.setEnabled(False)
        self.region_name_lineedit.setMaximumWidth(210)
        self.hlayout0.addWidget(self.region_name_lineedit)

        self.edit_mode_combobox = QtGui.QComboBox()
        self.edit_mode_combobox.setMinimumWidth(132)
        self.edit_mode_combobox.addItems([_("Items"), _("Automation")])
        self.edit_mode_combobox.currentIndexChanged.connect(
            self.edit_mode_changed)
        self.hlayout0.addWidget(QtGui.QLabel(_("Edit Mode:")))
        self.hlayout0.addWidget(self.edit_mode_combobox)

        self.menu_button = QtGui.QPushButton(_("Menu"))
        self.hlayout0.addWidget(self.menu_button)
        self.menu = QtGui.QMenu(self.menu_button)
        self.menu_button.setMenu(self.menu)
        self.shift_action = self.menu.addAction(_("Shift Song..."))
        self.shift_action.triggered.connect(self.on_shift)
        self.split_action = self.menu.addAction(_("Split Region..."))
        self.split_action.triggered.connect(self.on_split)
        self.reorder_tracks_action = self.menu.addAction(
            _("Reorder Tracks..."))
        self.reorder_tracks_action.triggered.connect(self.set_track_order)
        self.menu.addSeparator()
        self.hide_inactive = False
#        self.toggle_hide_action = self.menu.addAction(
#            _("Hide Inactive Instruments"))
#        self.toggle_hide_action.setCheckable(True)
#        self.toggle_hide_action.triggered.connect(self.toggle_hide_inactive)
#        self.toggle_hide_action.setShortcut(
#            QtGui.QKeySequence.fromString("CTRL+H"))
        self.menu.addSeparator()
        self.unsolo_action = self.menu.addAction(_("Un-Solo All"))
        self.unsolo_action.triggered.connect(self.unsolo_all)
        self.unsolo_action.setShortcut(QtGui.QKeySequence.fromString("CTRL+J"))
        self.unmute_action = self.menu.addAction(_("Un-Mute All"))
        self.unmute_action.triggered.connect(self.unmute_all)
        self.unmute_action.setShortcut(QtGui.QKeySequence.fromString("CTRL+M"))

        self.hlayout0.addItem(
            QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Expanding))
        self.hlayout0.addWidget(QtGui.QLabel(_("Region Length:")))
        self.length_default_radiobutton = QtGui.QRadioButton(_("default"))
        self.length_default_radiobutton.setChecked(True)
        self.length_default_radiobutton.toggled.connect(
            self.update_region_length)
        self.hlayout0.addWidget(self.length_default_radiobutton)
        self.length_alternate_radiobutton = QtGui.QRadioButton()
        self.length_alternate_radiobutton.toggled.connect(
            self.update_region_length)
        self.hlayout0.addWidget(self.length_alternate_radiobutton)
        self.length_alternate_spinbox = QtGui.QSpinBox()
        self.length_alternate_spinbox.setKeyboardTracking(False)
        self.length_alternate_spinbox.setRange(1, MAX_REGION_LENGTH)
        self.length_alternate_spinbox.setValue(8)
        self.length_alternate_spinbox.valueChanged.connect(
            self.update_region_length)
        self.hlayout0.addWidget(self.length_alternate_spinbox)

    def edit_mode_changed(self, a_value=None):
        global REGION_EDITOR_MODE
        REGION_EDITOR_MODE = a_value
        if a_value == 0:
            REGION_EDITOR.setDragMode(QtGui.QGraphicsView.NoDrag)
        elif a_value == 1:
            REGION_EDITOR.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
        REGION_EDITOR.open_region()

    def update_region_length(self, a_value=None):
        f_region_name = str(self.region_name_lineedit.text())
        global CURRENT_REGION
        if not libmk.IS_PLAYING and \
        CURRENT_REGION is not None and f_region_name != "":
            if not self.enabled or CURRENT_REGION is None:
                return
            if self.length_alternate_radiobutton.isChecked():
                f_region_length = self.length_alternate_spinbox.value()
                CURRENT_REGION.region_length_bars = f_region_length
                f_commit_message = _(
                    "Set region '{}' length to {}").format(f_region_name,
                    self.length_alternate_spinbox.value())
            else:
                CURRENT_REGION.region_length_bars = 0
                f_region_length = 8
                f_commit_message = _(
                    "Set region '{}' length to default value").format(
                    f_region_name)
            PROJECT.save_region(
                f_region_name, CURRENT_REGION)
            AUDIO_ITEMS.set_region_length(f_region_length)
            PROJECT.save_audio_region(
                CURRENT_REGION.uid, AUDIO_ITEMS)
            self.open_region(self.region_name_lineedit.text())
            f_resave = False
            for f_item in AUDIO_SEQ.audio_items:
                if f_item.clip_at_region_end():
                    f_resave = True
            if f_resave:
                PROJECT.save_audio_region(
                    CURRENT_REGION.uid, AUDIO_ITEMS)
            PROJECT.commit(f_commit_message)
            global_update_region_time()
            pydaw_set_audio_seq_zoom(AUDIO_SEQ.h_zoom, AUDIO_SEQ.v_zoom)
            global_open_audio_items()

    def toggle_hide_inactive(self):
        self.hide_inactive = self.toggle_hide_action.isChecked()
        global_update_hidden_rows()

    def unsolo_all(self):
        for f_track in TRACK_PANEL.tracks.values():
            f_track.solo_checkbox.setChecked(False)

    def unmute_all(self):
        for f_track in TRACK_PANEL.tracks.values():
            f_track.mute_checkbox.setChecked(False)

    def on_shift(self):
        if libmk.IS_PLAYING:
            return

        def ok_handler():
            f_song = PROJECT.get_song()
            f_amt = f_shift_amt.value()
            if f_amt == 0:
                return
            f_song.shift(f_amt)
            PROJECT.save_song(f_song)
            PROJECT.commit("Shift song by {}".format(f_amt))

            SONG_EDITOR.open_song()
            self.clear_items()
            SONG_EDITOR.open_first_region()
            global_update_region_time()
            f_window.close()

        def cancel_handler():
            f_window.close()

        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Shift song..."))
        f_layout = QtGui.QGridLayout()
        f_window.setLayout(f_layout)
        f_shift_amt = QtGui.QSpinBox()
        f_shift_amt.setRange(-10, 10)
        f_layout.addWidget(QtGui.QLabel(_("Amount:")), 2, 1)
        f_layout.addWidget(f_shift_amt, 2, 2)
        f_ok_cancel_layout = QtGui.QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout, 5, 2)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_ok_button.clicked.connect(ok_handler)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_cancel_button.clicked.connect(cancel_handler)
        f_window.exec_()


    def on_split(self):
        if CURRENT_REGION is None or libmk.IS_PLAYING or \
        CURRENT_REGION.region_length_bars == 1:
            return

        def split_ok_handler():
            f_index = f_split_at.value()
            f_region_name = str(f_new_lineedit.text())
            f_new_uid = PROJECT.create_empty_region(f_region_name)
            f_midi_tuple = CURRENT_REGION.split(f_index, f_new_uid)
            f_audio_tuple = AUDIO_ITEMS.split(f_index)
            f_atm_tuple = ATM_REGION.split(f_index)
            f_current_index = SONG_EDITOR.song.get_index_of_region(
                CURRENT_REGION.uid)
            SONG_EDITOR.song.insert_region(f_current_index + 1, f_new_uid)
            PROJECT.save_song(SONG_EDITOR.song)
            PROJECT.save_region(
                CURRENT_REGION_NAME, f_midi_tuple[0])
            PROJECT.save_region(f_region_name, f_midi_tuple[1])
            PROJECT.save_audio_region(
                CURRENT_REGION.uid, f_audio_tuple[0])
            PROJECT.save_audio_region(f_new_uid, f_audio_tuple[1])
            PROJECT.save_atm_region(f_atm_tuple[0], CURRENT_REGION.uid)
            PROJECT.save_atm_region(f_atm_tuple[1], f_new_uid)
            PROJECT.commit(_("Split region {} into {}").format(
                CURRENT_REGION_NAME, f_region_name))
            REGION_SETTINGS.open_region_by_uid(CURRENT_REGION.uid)
            SONG_EDITOR.open_song()
            global_update_region_time()
            f_window.close()

        def split_cancel_handler():
            f_window.close()

        def on_name_changed():
            f_new_lineedit.setText(
                pydaw_remove_bad_chars(f_new_lineedit.text()))

        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Split Region..."))
        f_layout = QtGui.QGridLayout()
        f_window.setLayout(f_layout)
        f_vlayout0 = QtGui.QVBoxLayout()
        f_new_lineedit = QtGui.QLineEdit(
            PROJECT.get_next_default_region_name())
        f_new_lineedit.editingFinished.connect(on_name_changed)
        f_new_lineedit.setMaxLength(24)
        f_layout.addWidget(QtGui.QLabel(_("New Name:")), 0, 1)
        f_layout.addWidget(f_new_lineedit, 0, 2)
        f_layout.addLayout(f_vlayout0, 1, 0)
        f_split_at = QtGui.QSpinBox()
        f_split_at.setRange(1, pydaw_get_current_region_length() - 1)
        f_layout.addWidget(QtGui.QLabel(_("Split After:")), 2, 1)
        f_layout.addWidget(f_split_at, 2, 2)
        f_ok_cancel_layout = QtGui.QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout, 5, 2)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_ok_button.clicked.connect(split_ok_handler)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_cancel_button.clicked.connect(split_cancel_handler)
        f_window.exec_()

    def open_region_by_uid(self, a_uid):
        f_regions_dict = PROJECT.get_regions_dict()
        self.open_region(f_regions_dict.get_name_by_uid(a_uid))

    def open_region(self, a_file_name):
        self.enabled = False
        self.clear_items()
        self.region_name_lineedit.setText(a_file_name)
        global CURRENT_REGION_NAME
        CURRENT_REGION_NAME = str(a_file_name)
        global CURRENT_REGION
        CURRENT_REGION = PROJECT.get_region_by_name(a_file_name)
        if CURRENT_REGION.region_length_bars > 0:
            self.length_alternate_spinbox.setValue(
                CURRENT_REGION.region_length_bars)
            TRANSPORT.bar_spinbox.setRange(
                1, (CURRENT_REGION.region_length_bars))
            self.length_alternate_radiobutton.setChecked(True)
        else:
            self.length_alternate_spinbox.setValue(8)
            TRANSPORT.bar_spinbox.setRange(1, 8)
            self.length_default_radiobutton.setChecked(True)
        self.enabled = True
        REGION_EDITOR.open_region()
        global_open_audio_items()
        global_update_hidden_rows()
        TRANSPORT.set_time(
            TRANSPORT.get_region_value(), TRANSPORT.get_bar_value(), 0.0)

    def clear_items(self):
        self.region_name_lineedit.setText("")
        self.length_alternate_spinbox.setValue(8)
        self.length_default_radiobutton.setChecked(True)
        REGION_EDITOR.clear_drawn_items()
        AUDIO_SEQ.clear_drawn_items()
        global CURRENT_REGION
        CURRENT_REGION = None

    def clear_new(self):
        self.region_name_lineedit.setText("")
        global CURRENT_REGION
        CURRENT_REGION = None
        REGION_EDITOR.clear_new()

    def on_play(self):
        self.length_default_radiobutton.setEnabled(False)
        self.length_alternate_radiobutton.setEnabled(False)
        self.length_alternate_spinbox.setEnabled(False)

    def on_stop(self):
        self.length_default_radiobutton.setEnabled(True)
        self.length_alternate_radiobutton.setEnabled(True)
        self.length_alternate_spinbox.setEnabled(True)

    def set_track_order(self):
        f_result = pydaw_widgets.ordered_table_dialog(
            TRACK_NAMES[1:], [x + 1 for x in range(len(TRACK_NAMES[1:]))],
            30, 200, MAIN_WINDOW)
        if f_result:
            f_result = {f_result[x]:x + 1 for x in range(len(f_result))}
            print(f_result)
            f_result[0] = 0 # master track
            print(f_result)
            PROJECT.reorder_tracks(f_result)
            TRACK_PANEL.open_tracks()
            for k, f_track in TRACK_PANEL.tracks.items():
                f_track.refresh()
            if CURRENT_REGION:
                self.open_region_by_uid(CURRENT_REGION.uid)

def global_set_region_editor_zoom():
    global REGION_EDITOR_GRID_WIDTH
    global MIDI_SCALE

    f_width = float(REGION_EDITOR.rect().width()) - \
        float(REGION_EDITOR.verticalScrollBar().width()) - 6.0 - \
        REGION_TRACK_WIDTH
    f_region_scale = f_width / 1000.0

    REGION_EDITOR_GRID_WIDTH = 1000.0 * MIDI_SCALE * f_region_scale
    pydaw_set_region_editor_quantize(REGION_EDITOR_QUANTIZE_INDEX)

REGION_EDITOR_SNAP = True
REGION_EDITOR_GRID_WIDTH = 1000.0
REGION_TRACK_WIDTH = 180  #Width of the tracks in px
REGION_EDITOR_MAX_START = 999.0 + REGION_TRACK_WIDTH
REGION_EDITOR_TRACK_HEIGHT = pydaw_util.get_file_setting(
    "TRACK_VZOOM", int, 64)
REGION_EDITOR_SNAP_DIVISOR = 16.0
REGION_EDITOR_SNAP_BEATS = 4.0 / REGION_EDITOR_SNAP_DIVISOR
REGION_EDITOR_SNAP_VALUE = \
    REGION_EDITOR_GRID_WIDTH / REGION_EDITOR_SNAP_DIVISOR
REGION_EDITOR_SNAP_DIVISOR_BEATS = REGION_EDITOR_SNAP_DIVISOR / 4.0
REGION_EDITOR_TRACK_COUNT = 32
REGION_EDITOR_HEADER_HEIGHT = 24
#gets updated by the region editor to it's real value:
REGION_EDITOR_TOTAL_HEIGHT = 1000
REGION_EDITOR_QUANTIZE_INDEX = 4

SELECTED_ITEM_GRADIENT = QtGui.QLinearGradient(
    QtCore.QPointF(0, 0), QtCore.QPointF(0, 12))
SELECTED_ITEM_GRADIENT.setColorAt(0, QtGui.QColor(180, 172, 100))
SELECTED_ITEM_GRADIENT.setColorAt(1, QtGui.QColor(240, 240, 240))

REGION_EDITOR_MODE = 0

def pydaw_set_region_editor_quantize(a_index):
    global REGION_EDITOR_SNAP
    global REGION_EDITOR_SNAP_VALUE
    global REGION_EDITOR_SNAP_DIVISOR
    global REGION_EDITOR_SNAP_DIVISOR_BEATS
    global REGION_EDITOR_SNAP_BEATS
    global REGION_EDITOR_QUANTIZE_INDEX

    REGION_EDITOR_QUANTIZE_INDEX = a_index

    if a_index == 0:
        REGION_EDITOR_SNAP = False
    else:
        REGION_EDITOR_SNAP = True

    if a_index == 0:
        REGION_EDITOR_SNAP_DIVISOR = 16.0
    elif a_index == 7:
        REGION_EDITOR_SNAP_DIVISOR = 128.0
    elif a_index == 6:
        REGION_EDITOR_SNAP_DIVISOR = 64.0
    elif a_index == 5:
        REGION_EDITOR_SNAP_DIVISOR = 32.0
    elif a_index == 4:
        REGION_EDITOR_SNAP_DIVISOR = 16.0
    elif a_index == 3:
        REGION_EDITOR_SNAP_DIVISOR = 12.0
    elif a_index == 2:
        REGION_EDITOR_SNAP_DIVISOR = 8.0
    elif a_index == 1:
        REGION_EDITOR_SNAP_DIVISOR = 4.0

    REGION_EDITOR_SNAP_BEATS = 4.0 / REGION_EDITOR_SNAP_DIVISOR
    REGION_EDITOR_SNAP_VALUE = \
        REGION_EDITOR_GRID_WIDTH / REGION_EDITOR_SNAP_DIVISOR
    REGION_EDITOR_SNAP_DIVISOR_BEATS = REGION_EDITOR_SNAP_DIVISOR / 4.0

REGION_EDITOR_MIN_NOTE_LENGTH = REGION_EDITOR_GRID_WIDTH / 128.0

REGION_EDITOR_DELETE_MODE = False

REGION_EDITOR_HEADER_GRADIENT = QtGui.QLinearGradient(
    0.0, 0.0, 0.0, REGION_EDITOR_HEADER_HEIGHT)
REGION_EDITOR_HEADER_GRADIENT.setColorAt(0.0, QtGui.QColor.fromRgb(61, 61, 61))
REGION_EDITOR_HEADER_GRADIENT.setColorAt(0.5, QtGui.QColor.fromRgb(50,50, 50))
REGION_EDITOR_HEADER_GRADIENT.setColorAt(0.6, QtGui.QColor.fromRgb(43, 43, 43))
REGION_EDITOR_HEADER_GRADIENT.setColorAt(1.0, QtGui.QColor.fromRgb(65, 65, 65))

def region_editor_set_delete_mode(a_enabled):
    global REGION_EDITOR_DELETE_MODE
    if a_enabled:
        REGION_EDITOR.setDragMode(QtGui.QGraphicsView.NoDrag)
        REGION_EDITOR_DELETE_MODE = True
        QtGui.QApplication.setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.ForbiddenCursor))
    else:
        REGION_EDITOR.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
        REGION_EDITOR_DELETE_MODE = False
        REGION_EDITOR.selected_item_strings = set([])
        QtGui.QApplication.restoreOverrideCursor()


class region_editor_item(QtGui.QGraphicsRectItem):
    def __init__(self, a_track, a_bar, a_name, a_path):
        self.bar_width = (REGION_EDITOR_GRID_WIDTH /
            pydaw_get_current_region_length())
        QtGui.QGraphicsRectItem.__init__(
            self, 0, 0, self.bar_width, REGION_EDITOR_TRACK_HEIGHT)
        if REGION_EDITOR_MODE == 0:
            self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
            self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
            self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges)
        else:
            self.setEnabled(False)
            self.setOpacity(0.6)
        self.path_item = QtGui.QGraphicsPathItem(a_path)
        self.path_item.setParentItem(self)
        self.path_item.setPos(0.0, 0.0)
        self.path_item.setZValue(2000.0)
        self.setZValue(1001.0)
        self.track_num = int(a_track)
        self.bar = int(a_bar)
        self.setAcceptHoverEvents(True)
        self.resize_rect = self.rect()
        self.mouse_y_pos = QtGui.QCursor.pos().y()
        self.label = QtGui.QGraphicsSimpleTextItem(self)
        self.label.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        self.label.setText(a_name)
        self.name = str(a_name)
        self.label.setPos(2.0, 2.0)
        self.set_brush()
        self.set_pos()

    def setSelected(self, a_bool):
        QtGui.QGraphicsRectItem.setSelected(self, a_bool)
        self.set_brush()

    def set_pos(self):
        f_start = self.bar_width * self.bar
        f_track_pos = REGION_EDITOR_HEADER_HEIGHT + (self.track_num *
            REGION_EDITOR_TRACK_HEIGHT)
        self.setPos(f_start, f_track_pos)

    def set_brush(self):
        if self.isSelected():
            self.setBrush(pydaw_selected_gradient)
            self.label.setBrush(QtCore.Qt.black)
            self.path_item.setBrush(QtCore.Qt.black)
            self.path_item.setPen(QtCore.Qt.black)
        else:
            self.label.setBrush(QtCore.Qt.white)
            f_index = self.track_num % len(pydaw_track_gradients)
            self.setBrush(pydaw_track_gradients[f_index])
            self.path_item.setBrush(QtCore.Qt.white)
            self.path_item.setPen(QtCore.Qt.white)

    def get_selected_string(self):
        return "|".join(str(x) for x in (self.track_num, self.bar, self.name))

    def hoverEnterEvent(self, a_event):
        QtGui.QGraphicsRectItem.hoverEnterEvent(self, a_event)
        REGION_EDITOR.click_enabled = False

    def hoverLeaveEvent(self, a_event):
        QtGui.QGraphicsRectItem.hoverLeaveEvent(self, a_event)
        QtGui.QApplication.restoreOverrideCursor()

    def mouseDoubleClickEvent(self, a_event):
        a_event.setAccepted(True)
        QtGui.QGraphicsRectItem.mouseDoubleClickEvent(self, a_event)
        global_open_items([self.name], a_reset_scrollbar=True)
        MAIN_WINDOW.main_tabwidget.setCurrentIndex(1)

    def mousePressEvent(self, a_event):
        if not self.isEnabled():
            return
        a_event.setAccepted(True)
        QtGui.QGraphicsRectItem.mousePressEvent(self, a_event)
        self.setSelected(True)
        if a_event.button() == QtCore.Qt.RightButton:
            return
        if a_event.modifiers() == QtCore.Qt.ShiftModifier:
            region_editor_set_delete_mode(True)
        else:
            f_region_length = pydaw_get_current_region_length()
            f_selected = REGION_EDITOR.get_selected_items()
            f_max_x = max(x.bar for x in f_selected)
            f_min_x = min(x.bar for x in f_selected)
            f_max_y = max(x.track_num for x in f_selected)
            f_min_y = min(x.track_num for x in f_selected)
            self.max_x = f_region_length - f_max_x - 1
            self.min_x = -f_min_x
            self.max_y = TRACK_COUNT_ALL - f_max_y
            self.min_y = -f_min_y
            for f_item in f_selected:
                f_item.orig_track_num = f_item.track_num
                f_item.orig_bar = f_item.bar

    def mouseMoveEvent(self, a_event):
        QtGui.QGraphicsRectItem.mouseMoveEvent(self, a_event)
        if self.isEnabled():
            f_pos = a_event.scenePos()
            f_coord = REGION_EDITOR.get_item_coord(f_pos)
            if not f_coord:
                for f_item in REGION_EDITOR.get_selected_items():
                    f_item.set_pos()
                return
            f_x = pydaw_clip_value(
                f_coord[1] - self.orig_bar, self.min_x, self.max_x)
            f_y = pydaw_clip_value(
                f_coord[0] - self.orig_track_num, self.min_y, self.max_y)
            for f_item in REGION_EDITOR.get_selected_items():
                f_item.track_num = f_item.orig_track_num + f_y
                f_item.bar = f_item.orig_bar + f_x
                f_item.set_pos()

    def mouseReleaseEvent(self, a_event):
        if not self.isEnabled():
            QtGui.QGraphicsRectItem.mouseReleaseEvent(self, a_event)
            return
        a_event.setAccepted(True)
        QtGui.QGraphicsRectItem.mouseReleaseEvent(self, a_event)
        if not self.isEnabled():
            return
        if REGION_EDITOR_DELETE_MODE:
            region_editor_set_delete_mode(False)
            return
        REGION_EDITOR.set_selected_strings()
        global_tablewidget_to_region()
        QtGui.QApplication.restoreOverrideCursor()


ALL_PEAK_METERS = {}

class tracks_widget:
    def __init__(self):
        self.tracks = {}
        self.plugin_uid_map = {}
        self.tracks_widget = QtGui.QWidget()
        self.tracks_widget.setObjectName("plugin_ui")
        self.tracks_widget.setContentsMargins(0, 0, 0, 0)
        self.tracks_widget.setFixedSize(
            QtCore.QSize(REGION_TRACK_WIDTH,
            (REGION_EDITOR_TRACK_HEIGHT * REGION_EDITOR_TRACK_COUNT) +
            REGION_EDITOR_HEADER_HEIGHT))
        self.tracks_layout = QtGui.QVBoxLayout(self.tracks_widget)
        self.tracks_layout.addItem(
            QtGui.QSpacerItem(0, REGION_EDITOR_HEADER_HEIGHT + 2.0,
            vPolicy=QtGui.QSizePolicy.MinimumExpanding))
        self.tracks_layout.setContentsMargins(0, 0, 0, 0)
        for i in range(REGION_EDITOR_TRACK_COUNT):
            f_track = seq_track(i, TRACK_NAMES[i])
            self.tracks[i] = f_track
            self.tracks_layout.addWidget(f_track.group_box)
        self.automation_dict = {
            x:(None, None) for x in range(REGION_EDITOR_TRACK_COUNT)}

    def get_track_names(self):
        return [
            self.tracks[k].track_name_lineedit.text()
            for k in sorted(self.tracks)]

    def get_atm_params(self, a_track_num):
        f_track = self.tracks[int(a_track_num)]
        return (
            f_track.automation_uid, f_track.automation_plugin)

    def update_automation(self):
        self.automation_dict = {
            x:(self.tracks[x].port_num, self.tracks[x].automation_uid)
            for x in self.tracks}

    def update_plugin_track_map(self):
        self.plugin_uid_map = {int(y.plugin_uid):int(x)
            for x in self.tracks for y in self.tracks[x].plugins}

    def has_automation(self, a_track_num):
        return self.automation_dict[int(a_track_num)]

    def update_ccs_in_use(self):
        for v in self.tracks.values():
            v.update_in_use_combobox()

    def open_tracks(self):
        global TRACK_NAMES
        f_tracks = PROJECT.get_tracks()
        TRACK_NAMES = f_tracks.get_names()
        global_update_track_comboboxes()
        for f_track_num, f_name in zip(sorted(self.tracks), TRACK_NAMES):
            self.tracks[f_track_num].track_name_lineedit.setText(f_name)
        for key, f_track in f_tracks.tracks.items():
            self.tracks[key].open_track(f_track)
        self.update_plugin_track_map()

    def get_tracks(self):
        f_result = pydaw_tracks()
        for k, v in self.tracks.items():
            f_result.add_track(k, v.get_track())
        return f_result


ATM_POINT_DIAMETER = 6.0
ATM_POINT_RADIUS = ATM_POINT_DIAMETER * 0.5

ATM_GRADIENT = QtGui.QLinearGradient(
    0, 0, ATM_POINT_DIAMETER, ATM_POINT_DIAMETER)
ATM_GRADIENT.setColorAt(0, QtGui.QColor(255, 255, 255))
ATM_GRADIENT.setColorAt(0.5, QtGui.QColor(210, 210, 210))

ATM_REGION = pydaw_atm_region()

class atm_item(QtGui.QGraphicsEllipseItem):
    def __init__(self, a_item, a_save_callback, a_min_y, a_max_y):
        QtGui.QGraphicsEllipseItem.__init__(
            self, 0, 0, ATM_POINT_DIAMETER, ATM_POINT_DIAMETER)
        self.save_callback = a_save_callback
        self.item = a_item
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setZValue(1100.0)
        self.set_brush()
        self.min_y = a_min_y
        self.max_y = a_max_y

    def set_brush(self):
        if self.isSelected():
            self.setBrush(QtCore.Qt.black)
        else:
            self.setBrush(ATM_GRADIENT)

    def mousePressEvent(self, a_event):
        a_event.setAccepted(True)
        QtGui.QGraphicsEllipseItem.mousePressEvent(self, a_event)

    def mouseMoveEvent(self, a_event):
        QtGui.QGraphicsEllipseItem.mouseMoveEvent(self, a_event)
        f_pos = self.pos()
        f_x = pydaw_util.pydaw_clip_value(
            f_pos.x(), 0.0, REGION_EDITOR_MAX_START)
        f_y = pydaw_util.pydaw_clip_value(
            f_pos.y(), self.min_y, self.max_y)
        self.setPos(f_x, f_y)

    def mouseReleaseEvent(self, a_event):
        a_event.setAccepted(True)
        QtGui.QGraphicsEllipseItem.mouseReleaseEvent(self, a_event)
        f_pos = self.pos()
        f_point = self.item
        f_point.track, f_point.bar, f_point.beat, f_point.cc_val = \
            REGION_EDITOR.get_item_coord(f_pos, a_clip=True)
        self.save_callback()

    def __lt__(self, other):
        return self.pos().x() < other.pos().x()


class region_editor(QtGui.QGraphicsView):
    def __init__(self):
        QtGui.QGraphicsView.__init__(self)

        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.last_item_copied = None
        self.padding = 2
        self.update_note_height()

        self.scene = QtGui.QGraphicsScene(self)
        self.scene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
        self.scene.setBackgroundBrush(QtGui.QColor(100, 100, 100))
        self.scene.mousePressEvent = self.sceneMousePressEvent
        self.scene.mouseMoveEvent = self.sceneMouseMoveEvent
        self.scene.mouseReleaseEvent = self.sceneMouseReleaseEvent
        self.setAlignment(QtCore.Qt.AlignLeft)
        self.setScene(self.scene)
        self.first_open = True
        self.clear_drawn_items()

        self.has_selected = False

        self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
        self.region_items = {}
        self.playback_cursor = None

        self.last_scale = 1.0
        self.last_x_scale = 1.0
        self.scene.selectionChanged.connect(self.highlight_selected)
        self.selected_item_strings = set([])
        self.selected_point_strings = set([])
        self.clipboard = []
        self.automation_points = []
        self.painter_path_cache = {}

        self.atm_select_pos_x = None
        self.atm_select_track = None
        self.atm_delete = False

        self.current_coord = None
        self.current_item = None

        self.menu = QtGui.QMenu()
        self.atm_menu = QtGui.QMenu()

        self.edit_group_action = self.menu.addAction(
            _("Edit Selected Item(s)"))
        self.edit_group_action.triggered.connect(self.edit_group)
        self.edit_group_action.setShortcut(
            QtGui.QKeySequence.fromString("CTRL+E"))
        self.addAction(self.edit_group_action)

        self.edit_unique_action = self.menu.addAction(_("Edit Unique Item(s)"))
        self.edit_unique_action.triggered.connect(self.edit_unique)
        self.edit_unique_action.setShortcut(
            QtGui.QKeySequence.fromString("ALT+E"))
        self.addAction(self.edit_unique_action)

        self.menu.addSeparator()

        self.copy_action = self.menu.addAction(_("Copy"))
        self.copy_action.triggered.connect(self.copy_selected)
        self.copy_action.setShortcut(QtGui.QKeySequence.Copy)
        self.addAction(self.copy_action)
        self.atm_menu.addAction(self.copy_action)

        self.cut_action = self.menu.addAction(_("Cut"))
        self.cut_action.triggered.connect(self.cut_selected)
        self.cut_action.setShortcut(QtGui.QKeySequence.Cut)
        self.addAction(self.cut_action)
        self.atm_menu.addAction(self.cut_action)

        self.paste_action = self.menu.addAction(_("Paste"))
        self.paste_action.triggered.connect(self.paste_clipboard)
        self.atm_menu.addAction(self.paste_action)

        self.paste_ctrl_action = self.atm_menu.addAction(
            _("Paste Plugin Control"))
        self.paste_ctrl_action.triggered.connect(self.paste_atm_point)

        self.paste_to_end_action = self.menu.addAction(
            _("Paste to Region End"))
        self.paste_to_end_action.triggered.connect(self.paste_to_region_end)

        self.paste_to_orig_action = self.menu.addAction(
            _("Paste to Original Pos"))
        self.paste_to_orig_action.triggered.connect(self.paste_at_original_pos)
        self.paste_to_orig_action.setShortcut(QtGui.QKeySequence.Paste)
        self.addAction(self.paste_to_orig_action)

        self.select_all_action = QtGui.QAction(_("Select All"), self)
        self.select_all_action.triggered.connect(self.select_all)
        self.select_all_action.setShortcut(QtGui.QKeySequence.SelectAll)
        self.addAction(self.select_all_action)

        self.smooth_atm_action = self.atm_menu.addAction(
            _("Smooth Selected Points"))
        self.smooth_atm_action.triggered.connect(self.smooth_atm_points)
        self.smooth_atm_action.setShortcut(
            QtGui.QKeySequence.fromString("ALT+S"))
        self.addAction(self.smooth_atm_action)

        self.clear_selection_action = self.menu.addAction(_("Clear Selection"))
        self.clear_selection_action.triggered.connect(self.clearSelection)
        self.clear_selection_action.setShortcut(
            QtGui.QKeySequence.fromString("Esc"))
        self.addAction(self.clear_selection_action)

        self.delete_action = self.menu.addAction(_("Delete"))
        self.delete_action.triggered.connect(self.delete_selected)
        self.delete_action.setShortcut(QtGui.QKeySequence.Delete)
        self.addAction(self.delete_action)
        self.atm_menu.addAction(self.delete_action)

        self.menu.addSeparator()

        self.unlink_selected_action = self.menu.addAction(
            _("Auto-Unlink Item(s)"))
        self.unlink_selected_action.setShortcut(
            QtGui.QKeySequence.fromString("CTRL+U"))
        self.unlink_selected_action.triggered.connect(
            self.on_auto_unlink_selected)
        self.addAction(self.unlink_selected_action)

        self.unlink_unique_action = self.menu.addAction(
            _("Auto-Unlink Unique Item(s)"))
        self.unlink_unique_action.setShortcut(
            QtGui.QKeySequence.fromString("ALT+U"))
        self.unlink_unique_action.triggered.connect(self.on_auto_unlink_unique)
        self.addAction(self.unlink_unique_action)

        self.rename_action = self.menu.addAction(
            _("Rename Selected Item(s)..."))
        self.rename_action.triggered.connect(self.on_rename_items)
        self.addAction(self.rename_action)

        self.unlink_action = self.menu.addAction(_("Unlink Single Item..."))
        self.unlink_action.triggered.connect(self.on_unlink_item)
        self.addAction(self.unlink_action)

        self.transpose_action = self.menu.addAction(_("Transpose..."))
        self.transpose_action.triggered.connect(self.transpose_dialog)
        self.addAction(self.transpose_action)

    def paste_atm_point(self):
        if libmk.IS_PLAYING:
            return
        if pydaw_widgets.CC_CLIPBOARD is None:
            QtGui.QMessageBox.warning(
                self, _("Error"),
                _("Nothing copied to the clipboard.\n"
                "Right-click->'Copy' on any knob on any plugin."))
            return
        self.add_atm_point(pydaw_widgets.CC_CLIPBOARD)

    def add_atm_point(self, a_value=None):
        if libmk.IS_PLAYING:
            return

        def ok_handler():
            f_track = f_track_cbox.currentIndex()
            f_port, f_index = TRACK_PANEL.has_automation(f_track)

            if f_port is not None:
                f_bar = f_bar_spinbox.value() - 1
                f_beat = f_pos_spinbox.value() - 1.0
                f_val = f_value_spinbox.value()
                f_point = pydaw_atm_point(
                    f_bar, f_beat, f_port, f_val,
                    *TRACK_PANEL.get_atm_params(f_track))
                ATM_REGION.add_point(f_point)
                self.draw_point(f_point)
                self.automation_save_callback()

        def goto_start():
            f_bar_spinbox.setValue(f_bar_spinbox.minimum())
            f_pos_spinbox.setValue(f_pos_spinbox.minimum())

        def goto_end():
            f_bar_spinbox.setValue(f_bar_spinbox.maximum())
            f_pos_spinbox.setValue(f_pos_spinbox.maximum())

        def value_paste():
            f_value_spinbox.setValue(pydaw_widgets.CC_CLIPBOARD)

        def cancel_handler():
            f_window.close()

        f_window = QtGui.QDialog(self)
        f_window.setWindowTitle(_("Add automation point"))
        f_layout = QtGui.QGridLayout()
        f_window.setLayout(f_layout)

        f_layout.addWidget(QtGui.QLabel(_("Track")), 0, 0)
        f_track_cbox = QtGui.QComboBox()
        f_track_cbox.addItems(TRACK_NAMES)
        f_layout.addWidget(f_track_cbox, 0, 1)

        f_layout.addWidget(QtGui.QLabel(_("Position (bars)")), 2, 0)
        f_bar_spinbox = QtGui.QSpinBox()
        f_bar_spinbox.setRange(1, pydaw_get_current_region_length())
        f_layout.addWidget(f_bar_spinbox, 2, 1)

        f_layout.addWidget(QtGui.QLabel(_("Position (beats)")), 5, 0)
        f_pos_spinbox = QtGui.QDoubleSpinBox()
        f_pos_spinbox.setRange(1.0, 4.99)
        f_pos_spinbox.setDecimals(2)
        f_pos_spinbox.setSingleStep(0.25)
        f_layout.addWidget(f_pos_spinbox, 5, 1)

        f_begin_end_layout = QtGui.QHBoxLayout()
        f_layout.addLayout(f_begin_end_layout, 6, 1)
        f_start_button = QtGui.QPushButton("<<")
        f_start_button.pressed.connect(goto_start)
        f_begin_end_layout.addWidget(f_start_button)
        f_begin_end_layout.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))
        f_end_button = QtGui.QPushButton(">>")
        f_end_button.pressed.connect(goto_end)
        f_begin_end_layout.addWidget(f_end_button)

        f_layout.addWidget(QtGui.QLabel(_("Value")), 10, 0)
        f_value_spinbox = QtGui.QDoubleSpinBox()
        f_value_spinbox.setRange(0.0, 127.0)
        f_value_spinbox.setDecimals(4)
        if a_value is not None:
            f_value_spinbox.setValue(a_value)
        f_layout.addWidget(f_value_spinbox, 10, 1)
        f_value_paste = QtGui.QPushButton(_("Paste"))
        f_layout.addWidget(f_value_paste, 10, 2)
        f_value_paste.pressed.connect(value_paste)

        if self.current_coord:
            f_track, f_bar, f_beat, f_val = self.current_coord
            f_track_cbox.setCurrentIndex(f_track)
            f_bar_spinbox.setValue(f_bar + 1)
            f_pos_spinbox.setValue(f_beat + 1.0)

        f_ok = QtGui.QPushButton(_("Add"))
        f_ok.pressed.connect(ok_handler)
        f_ok_cancel_layout = QtGui.QHBoxLayout()
        f_ok_cancel_layout.addWidget(f_ok)

        f_layout.addLayout(f_ok_cancel_layout, 40, 1)
        f_cancel = QtGui.QPushButton(_("Close"))
        f_cancel.pressed.connect(cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel)
        f_window.show()


    def set_playback_pos(self, a_bar=None, a_beat=0.0):
        if a_bar is None:
            f_bar = TRANSPORT.get_bar_value()
        else:
            f_bar = int(a_bar)
        f_beat = float(a_beat)
        f_pos = (f_bar * self.px_per_bar) + (f_beat * self.px_per_beat)
        self.playback_cursor.setPos(f_pos, 0.0)

    def set_playback_clipboard(self):
        self.reselect_on_stop = []
        for f_item in self.audio_items:
            if f_item.isSelected():
                self.reselect_on_stop.append(str(f_item.audio_item))

    def start_playback(self, a_bpm):
        self.is_playing = True

    def stop_playback(self, a_bar=None):
        if self.is_playing:
            self.is_playing = False
            self.reset_selection()
            self.set_playback_pos(a_bar)

    def reset_selection(self):
        for f_item in self.audio_items:
            if str(f_item.audio_item) in self.reselect_on_stop:
                f_item.setSelected(True)

    def show_context_menu(self):
        if REGION_EDITOR_MODE == 0:
            self.menu.exec_(QtGui.QCursor.pos())
        elif REGION_EDITOR_MODE == 1:
            self.atm_menu.exec_(QtGui.QCursor.pos())

    def update_note_height(self):
        self.tracks_height = \
            REGION_EDITOR_TRACK_HEIGHT * REGION_EDITOR_TRACK_COUNT

        global REGION_EDITOR_TOTAL_HEIGHT
        REGION_EDITOR_TOTAL_HEIGHT = \
            self.tracks_height + REGION_EDITOR_HEADER_HEIGHT

    def get_selected_items(self):
        return [x for x in self.get_all_items() if x.isSelected()]

    def get_item_coord(self, a_pos, a_clip=False):
        f_pos_x = a_pos.x()
        f_pos_y = a_pos.y()
        if a_clip or (
        f_pos_x > 0 and
        f_pos_x < REGION_EDITOR_MAX_START and
        f_pos_y > REGION_EDITOR_HEADER_HEIGHT and
        f_pos_y < REGION_EDITOR_TOTAL_HEIGHT):
            f_pos_x = pydaw_util.pydaw_clip_value(
                f_pos_x, 0.0, REGION_EDITOR_MAX_START)
            f_pos_y = pydaw_util.pydaw_clip_value(
                f_pos_y, REGION_EDITOR_HEADER_HEIGHT,
                REGION_EDITOR_TOTAL_HEIGHT)
            f_pos_y = f_pos_y - REGION_EDITOR_HEADER_HEIGHT
            f_track_height = REGION_EDITOR_TRACK_HEIGHT - ATM_POINT_DIAMETER
            f_track = int((f_pos_y / (self.tracks_height))
                * REGION_EDITOR_TRACK_COUNT)
            f_val = (1.0 - ((f_pos_y - (f_track * REGION_EDITOR_TRACK_HEIGHT))
                / f_track_height)) * 127.0
            f_bar = int((f_pos_x / self.viewer_width) * self.item_length)
            f_beat = (((f_pos_x / self.viewer_width) *
                self.item_length) - f_bar) * 4.0
            return f_track, f_bar, round(f_beat, 4), round(f_val, 4)
        else:
            return None

    def get_pos_from_point(self, a_point):
        f_item_width = self.viewer_width / self.item_length
        f_track_height = REGION_EDITOR_TRACK_HEIGHT - ATM_POINT_DIAMETER
        f_track = TRACK_PANEL.plugin_uid_map[a_point.index]
        return QtCore.QPointF(
            (a_point.bar * f_item_width) +
            (a_point.beat * 0.25 * f_item_width),
            (f_track_height * (1.0 - (a_point.cc_val / 127.0))) +
            (REGION_EDITOR_TRACK_HEIGHT * f_track) +
            REGION_EDITOR_HEADER_HEIGHT)

    def show_cell_dialog(self):
        if REGION_EDITOR_MODE != 0:
            return
        if not self.current_coord or not CURRENT_REGION:
            return
        x, y = self.current_coord[:2]
        def note_ok_handler():
            self.scene.clearSelection()
            global CURRENT_REGION
            if f_new_radiobutton.isChecked() and \
            f_item_count.value() == 1:
                f_cell_text = str(f_new_lineedit.text())
                if PROJECT.item_exists(f_cell_text):
                    QtGui.QMessageBox.warning(
                        self, _("Error"),
                        _("An item named '{}' already exists.").format(
                        f_cell_text))
                    return
                f_uid = PROJECT.create_empty_item(f_cell_text)
                self.draw_item(x, y, f_cell_text, True)
                CURRENT_REGION.add_item_ref_by_uid(x, y, f_uid)
                if f_repeat_checkbox.isChecked():
                    for i in range(y, pydaw_get_current_region_length()):
                        self.draw_item(x, i, f_cell_text, True)
                        CURRENT_REGION.add_item_ref_by_uid(x, i, f_uid)
            elif f_new_radiobutton.isChecked() and f_item_count.value() > 1:
                f_name_suffix = 1
                f_cell_text = str(f_new_lineedit.text())
                f_list = []
                for i in range(f_item_count.value()):
                    while PROJECT.item_exists(
                        "{}-{}".format(f_cell_text, f_name_suffix)):
                        f_name_suffix += 1
                    f_item_name = "{}-{}".format(f_cell_text, f_name_suffix)
                    f_uid = PROJECT.create_empty_item(f_item_name)
                    f_list.append((f_uid, f_item_name))
                    self.draw_item(x, y + i, f_item_name, True)
                    CURRENT_REGION.add_item_ref_by_uid(x, y + i, f_uid)
                if f_repeat_checkbox.isChecked():
                    f_i = 0
                    for i in range(i + 1, pydaw_get_current_region_length()):
                        f_uid, f_item_name = f_list[f_i]
                        f_i += 1
                        if f_i >= len(f_list):
                            f_i = 0
                        self.draw_item(x, y + i, f_item_name, True)
                        CURRENT_REGION.add_item_ref_by_uid(x, y + i, f_uid)
            elif f_copy_radiobutton.isChecked():
                f_cell_text = str(f_copy_combobox.currentText())
                self.draw_item(x, y, f_cell_text, True)
                CURRENT_REGION.add_item_ref_by_name(
                    x, y, f_cell_text, f_item_dict)
            elif f_copy_from_radiobutton.isChecked():
                f_cell_text = str(f_new_lineedit.text())
                f_copy_from_text = str(f_copy_combobox.currentText())
                if PROJECT.item_exists(f_cell_text):
                    QtGui.QMessageBox.warning(
                        self, _("Error"),
                        _("An item named '{}' already exists.").format(
                        f_cell_text))
                    return
                f_uid = PROJECT.copy_item(
                    f_copy_from_text, f_cell_text)
                self.draw_item(x, y, f_cell_text, True)
                CURRENT_REGION.add_item_ref_by_uid(x, y, f_uid)
            elif f_take_radiobutton.isChecked():
                f_cell_text = str(f_take_name_combobox.currentText())
                f_start = f_take_dict[f_cell_text].index(
                    str(f_take_start_combobox.currentText()))
                f_end = f_take_dict[f_cell_text].index(
                    str(f_take_end_combobox.currentText()))
                if f_end > f_start:
                    f_end += 1
                elif f_end < f_start:
                    f_end -= 1
                f_step = 1 if f_start <= f_end else -1
                f_range = f_take_dict[f_cell_text][f_start:f_end:f_step]
                for f_suffix, f_pos in zip(
                f_range, range(y, pydaw_get_current_region_length())):
                    f_name = "".join((f_cell_text, f_suffix))
                    print(f_name)
                    self.draw_item(x, f_pos, f_name, True)
                    CURRENT_REGION.add_item_ref_by_name(
                        x, f_pos, f_name, f_item_dict)
            PROJECT.save_region(
                str(REGION_SETTINGS.region_name_lineedit.text()),
                CURRENT_REGION)
            PROJECT.commit(
                _("Add reference(s) to item (group) '{}' in region "
                "'{}'").format(f_cell_text,
                REGION_SETTINGS.region_name_lineedit.text()))
            self.last_item_copied = f_cell_text

            f_window.close()

        def paste_button_pressed():
            self.paste_clipboard()
            f_window.close()

        def paste_to_end_button_pressed():
            self.paste_to_region_end()
            f_window.close()

        def note_cancel_handler():
            f_window.close()

        def copy_combobox_index_changed(a_index):
            f_copy_radiobutton.setChecked(True)

        def on_name_changed():
            f_new_lineedit.setText(
                pydaw_remove_bad_chars(f_new_lineedit.text()))

        def goto_start():
            f_item_count.setValue(f_item_count.minimum())

        def goto_end():
            f_item_count.setValue(f_item_count.maximum())

        def take_changed(a_val=None, a_check=True):
            f_take_start_combobox.clear()
            f_take_end_combobox.clear()
            f_key = str(f_take_name_combobox.currentText())
            f_take_start_combobox.addItems(f_take_dict[f_key])
            f_take_end_combobox.addItems(f_take_dict[f_key])
            if a_check:
                f_take_radiobutton.setChecked(True)

        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Add item reference to region..."))
        f_layout = QtGui.QGridLayout()
        f_vlayout0 = QtGui.QVBoxLayout()
        f_vlayout1 = QtGui.QVBoxLayout()
        f_window.setLayout(f_layout)
        f_new_radiobutton = QtGui.QRadioButton()
        f_new_radiobutton.setChecked(True)
        f_layout.addWidget(f_new_radiobutton, 0, 0)
        f_layout.addWidget(QtGui.QLabel(_("New:")), 0, 1)
        f_new_lineedit = QtGui.QLineEdit(
            PROJECT.get_next_default_item_name())
        f_new_lineedit.editingFinished.connect(on_name_changed)
        f_new_lineedit.setMaxLength(24)
        f_layout.addWidget(f_new_lineedit, 0, 2)
        f_layout.addLayout(f_vlayout0, 1, 0)
        f_copy_from_radiobutton = QtGui.QRadioButton()
        f_vlayout0.addWidget(f_copy_from_radiobutton)
        f_copy_radiobutton = QtGui.QRadioButton()
        f_vlayout0.addWidget(f_copy_radiobutton)
        f_copy_combobox = QtGui.QComboBox()
        f_copy_combobox.addItems(PROJECT.get_item_list())
        if not self.last_item_copied is None:
            f_copy_combobox.setCurrentIndex(
            f_copy_combobox.findText(self.last_item_copied))
        f_copy_combobox.currentIndexChanged.connect(
            copy_combobox_index_changed)
        f_layout.addLayout(f_vlayout1, 1, 1)
        f_vlayout1.addWidget(QtGui.QLabel(_("Copy from:")))
        f_vlayout1.addWidget(QtGui.QLabel(_("Existing:")))
        f_layout.addWidget(f_copy_combobox, 1, 2)
        f_layout.addWidget(QtGui.QLabel(_("Item Count:")), 2, 1)
        f_item_count = QtGui.QSpinBox()
        f_item_count.setRange(1, pydaw_get_current_region_length() - y)
        f_item_count.setToolTip(_("Only used for 'New'"))

        f_begin_end_layout = QtGui.QHBoxLayout()
        f_begin_end_layout.addWidget(f_item_count)
        f_layout.addLayout(f_begin_end_layout, 2, 2)
        f_start_button = QtGui.QPushButton("<<")
        f_start_button.pressed.connect(goto_start)
        f_begin_end_layout.addWidget(f_start_button)
        f_end_button = QtGui.QPushButton(">>")
        f_end_button.pressed.connect(goto_end)
        f_begin_end_layout.addWidget(f_end_button)

        f_repeat_checkbox = QtGui.QCheckBox(_("Repeat to end?"))
        f_layout.addWidget(f_repeat_checkbox, 3, 2)

        if REGION_CLIPBOARD:
            f_paste_clipboard_button = QtGui.QPushButton(_("Paste Clipboard"))
            f_layout.addWidget(f_paste_clipboard_button, 4, 2)
            f_paste_clipboard_button.pressed.connect(paste_button_pressed)

        if len(REGION_CLIPBOARD) == 1:
            f_paste_to_end_button = QtGui.QPushButton(_("Paste to End"))
            f_layout.addWidget(f_paste_to_end_button, 7, 2)
            f_paste_to_end_button.pressed.connect(paste_to_end_button_pressed)

        f_item_dict = PROJECT.get_items_dict()
        f_take_dict = f_item_dict.get_takes()

        if f_take_dict:
            f_take_radiobutton = QtGui.QRadioButton()
            f_layout.addWidget(f_take_radiobutton, 12, 0)
            f_layout.addWidget(QtGui.QLabel(_("Take:")), 12, 1)
            f_take_name_combobox = QtGui.QComboBox()
            f_layout.addWidget(f_take_name_combobox, 12, 2)
            f_take_start_combobox = QtGui.QComboBox()
            f_take_start_combobox.setMinimumWidth(60)
            f_layout.addWidget(f_take_start_combobox, 12, 3)
            f_take_end_combobox = QtGui.QComboBox()
            f_take_end_combobox.setMinimumWidth(60)
            f_layout.addWidget(f_take_end_combobox, 12, 4)
            f_take_name_combobox.addItems(sorted(f_take_dict))
            take_changed(a_check=False)
            f_take_name_combobox.currentIndexChanged.connect(take_changed)

        f_ok_cancel_layout = QtGui.QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout, 24, 2)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_ok_button.clicked.connect(note_ok_handler)
        f_ok_button.setDefault(True)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_cancel_button.clicked.connect(note_cancel_handler)
        f_window.move(QtGui.QCursor.pos())
        f_window.exec_()

    def set_tooltips(self, a_on):
        if a_on:
            self.setToolTip(libedmnext.strings.region_list_editor)
        else:
            self.setToolTip("")

    def prepare_to_quit(self):
        self.scene.clearSelection()
        self.scene.clear()

    def set_header_pos(self):
        f_y = self.get_scene_pos()
        self.header.setPos(self.padding, f_y - 2.0)

    def get_scene_pos(self):
        try:
            return MAIN_WINDOW.midi_scroll_area.verticalScrollBar().value()
        except:
            return 0

    def get_all_items(self):
        for k1 in sorted(self.region_items):
            for k2 in sorted(self.region_items[k1]):
                yield self.region_items[k1][k2]

    def get_item(self, a_track, a_bar):
        if a_track in self.region_items and \
        a_bar in self.region_items[a_track]:
            return self.region_items[a_track][a_bar]
        else:
            return None

    def get_all_points(self, a_track=None):
        f_dict = TRACK_PANEL.plugin_uid_map
        if a_track is None:
            for f_point in self.automation_points:
                yield f_point
        else:
            a_track = int(a_track)
            for f_point in self.automation_points:
                if f_dict[f_point.item.index] == a_track:
                    yield f_point

    def get_selected_points(self, a_track=None):
        f_dict = TRACK_PANEL.plugin_uid_map
        if a_track is None:
            for f_point in self.automation_points:
                if f_point.isSelected():
                    yield f_point
        else:
            a_track = int(a_track)
            for f_point in self.automation_points:
                if f_dict[f_point.item.index] == a_track and \
                f_point.isSelected():
                    yield f_point

    def select_all(self):
        for f_item in self.get_all_items():
            f_item.setSelected(True)

    def highlight_selected(self):
        self.setUpdatesEnabled(False)
        self.has_selected = False
        if REGION_EDITOR_MODE == 0:
            for f_item in self.get_all_items():
                f_item.set_brush()
                self.has_selected = True
        elif REGION_EDITOR_MODE == 1:
            for f_item in self.get_all_points():
                f_item.set_brush()
                self.has_selected = True
        self.setUpdatesEnabled(True)
        self.update()

    def set_selected_strings(self):
        self.selected_item_strings = {x.get_selected_string()
            for x in self.get_selected_items()}

    def set_selected_point_strings(self):
        self.selected_point_strings = {
            str(x.item) for x in self.get_selected_points()}

    def keyPressEvent(self, a_event):
        QtGui.QGraphicsView.keyPressEvent(self, a_event)
        QtGui.QApplication.restoreOverrideCursor()

    def focusOutEvent(self, a_event):
        QtGui.QGraphicsView.focusOutEvent(self, a_event)
        QtGui.QApplication.restoreOverrideCursor()

    def sceneMouseReleaseEvent(self, a_event):
        if REGION_EDITOR_DELETE_MODE:
            region_editor_set_delete_mode(False)
            global_tablewidget_to_region()
        else:
            QtGui.QGraphicsScene.mouseReleaseEvent(self.scene, a_event)
        if self.atm_delete:
            for f_point in self.get_selected_points(self.atm_select_track):
                ATM_REGION.remove_point(f_point.item)
            self.automation_save_callback()
            self.open_region()
        self.atm_select_pos_x = None
        self.atm_select_track = None
        self.atm_delete = False

    def sceneMouseMoveEvent(self, a_event):
        QtGui.QGraphicsScene.mouseMoveEvent(self.scene, a_event)
        if REGION_EDITOR_MODE == 1:
            if self.atm_select_pos_x is not None:
                f_pos_x = a_event.scenePos().x()
                f_vals = sorted((f_pos_x, self.atm_select_pos_x))
                for f_item in self.get_all_points(self.atm_select_track):
                    f_item_pos_x = f_item.pos().x()
                    if f_item_pos_x >= f_vals[0] and \
                    f_item_pos_x <= f_vals[1]:
                        f_item.setSelected(True)
                    else:
                        f_item.setSelected(False)

    def sceneMousePressEvent(self, a_event):
        if CURRENT_REGION is None:
            self.warn_no_region_selected()
            return
        self.current_coord = self.get_item_coord(a_event.scenePos())
        if a_event.button() == QtCore.Qt.RightButton:
            if self.current_coord:
                f_item = self.get_item(*self.current_coord[:2])
                if f_item and not f_item.isSelected():
                    self.clearSelection()
                    f_item.setSelected(True)
                self.show_context_menu()
            return
        if REGION_EDITOR_MODE == 0:
            self.current_item = None
            for f_item in self.scene.items(a_event.scenePos()):
                if isinstance(f_item, region_editor_item):
                    self.current_item = f_item
                    if not f_item.isSelected():
                        self.scene.clearSelection()
                    f_item.setSelected(True)
                    break
            if a_event.modifiers() == QtCore.Qt.ControlModifier:
                pass
            elif a_event.modifiers() == QtCore.Qt.ShiftModifier:
                region_editor_set_delete_mode(True)
                return
            else:
                if not self.current_item:
                    self.show_cell_dialog()
        elif REGION_EDITOR_MODE == 1:
            REGION_EDITOR.setDragMode(QtGui.QGraphicsView.NoDrag)
            self.atm_select_pos_x = None
            self.atm_select_track = None
            if a_event.modifiers() == QtCore.Qt.ControlModifier or \
            a_event.modifiers() == QtCore.Qt.ShiftModifier:
                self.current_coord = self.get_item_coord(
                    a_event.scenePos(), True)
                self.clearSelection()
                self.atm_select_pos_x = a_event.scenePos().x()
                self.atm_select_track = self.current_coord[0]
                if a_event.modifiers() == QtCore.Qt.ShiftModifier:
                    self.atm_delete = True
                return
            elif self.current_coord is not None:
                f_port, f_index = TRACK_PANEL.has_automation(
                    self.current_coord[0])
                if f_port is not None:
                    f_track, f_bar, f_beat, f_val = self.current_coord
                    f_point = pydaw_atm_point(
                        f_bar, f_beat, f_port, f_val,
                        *TRACK_PANEL.get_atm_params(f_track))
                    ATM_REGION.add_point(f_point)
                    self.draw_point(f_point)
                    self.automation_save_callback()

        a_event.setAccepted(True)
        QtGui.QGraphicsScene.mousePressEvent(self.scene, a_event)
        QtGui.QApplication.restoreOverrideCursor()

    def automation_save_callback(self):
        PROJECT.save_atm_region(ATM_REGION, CURRENT_REGION.uid)

    def mouseMoveEvent(self, a_event):
        QtGui.QGraphicsView.mouseMoveEvent(self, a_event)
        if REGION_EDITOR_DELETE_MODE:
            for f_item in self.items(a_event.pos()):
                if isinstance(f_item, region_editor_item):
                    self.scene.removeItem(f_item)
                    self.region_items[f_item.track_num].pop(f_item.bar)

    def hover_restore_cursor_event(self, a_event=None):
        QtGui.QApplication.restoreOverrideCursor()

    def draw_header(self):
        self.header = QtGui.QGraphicsRectItem(
            0, 0, self.viewer_width, REGION_EDITOR_HEADER_HEIGHT)
        self.header.hoverEnterEvent = self.hover_restore_cursor_event
        self.header.setBrush(REGION_EDITOR_HEADER_GRADIENT)
        self.scene.addItem(self.header)
        self.beat_width = self.viewer_width / self.item_length
        self.header.setZValue(1003.0)
        self.playback_cursor = self.scene.addLine(
            0.0, 0.0, 0.0,
            REGION_EDITOR_TOTAL_HEIGHT, QtGui.QPen(QtCore.Qt.red, 2.0))
        self.playback_cursor.setPos(0.0, 0.0)
        self.playback_cursor.setZValue(2000.0)

    def draw_grid(self):
        f_brush = QtGui.QLinearGradient(
            0.0, 0.0, 0.0, REGION_EDITOR_TRACK_HEIGHT)
        f_brush.setColorAt(0.0, QtGui.QColor(96, 96, 96, 60))
        f_brush.setColorAt(0.5, QtGui.QColor(21, 21, 21, 75))

        for i in range(REGION_EDITOR_TRACK_COUNT):
            f_note_bar = QtGui.QGraphicsRectItem(
                0, 0, self.viewer_width, REGION_EDITOR_TRACK_HEIGHT)
            f_note_bar.setZValue(60.0)
            self.scene.addItem(f_note_bar)
            f_note_bar.setBrush(f_brush)
            f_note_bar_y = (i *
                REGION_EDITOR_TRACK_HEIGHT) + REGION_EDITOR_HEADER_HEIGHT
            f_note_bar.setPos(self.padding, f_note_bar_y)
        f_bar_pen = QtGui.QPen()
        f_bar_pen.setWidth(2)
        f_beat_pen = QtGui.QPen(QtGui.QColor.fromRgb(21, 21, 21))
        f_beat_pen.setWidth(1)
        f_bar_y = self.tracks_height + REGION_EDITOR_HEADER_HEIGHT
        for i in range(0, int(self.item_length)):
            f_bar_x = (self.beat_width * i)
            f_bar = self.scene.addLine(f_bar_x, 0, f_bar_x, f_bar_y)
            f_bar.setPen(f_bar_pen)
            for i2 in range(1, 4):
                f_beat_x = ((self.beat_width * i) +
                    (i2 * self.beat_width * 0.25))
                f_beat = self.scene.addLine(f_beat_x, 0, f_beat_x, f_bar_y)
                f_beat.setPen(f_beat_pen)
            if i < self.item_length:
                f_number = QtGui.QGraphicsSimpleTextItem(
                    str(i + 1), self.header)
                f_number.setFlag(
                    QtGui.QGraphicsItem.ItemIgnoresTransformations)
                f_number.setPos((self.beat_width * i), 5)
                f_number.setBrush(QtCore.Qt.white)

    def resizeEvent(self, a_event):
        QtGui.QGraphicsView.resizeEvent(self, a_event)
        self.clear_drawn_items()
        self.open_region()

    def open_region(self):
        self.enabled = False
        global ATM_REGION
        if not CURRENT_REGION:
            ATM_REGION = None
            return
        ATM_REGION = PROJECT.get_atm_region_by_uid(CURRENT_REGION.uid)
        f_items_dict = PROJECT.get_items_dict()
        self.setUpdatesEnabled(False)
        self.clear_drawn_items()
        for f_item in sorted(
        CURRENT_REGION.items, key=lambda x: x.bar_num, reverse=True):
            if f_item.bar_num < pydaw_get_current_region_length():
                f_item_name = f_items_dict.get_name_by_uid(f_item.item_uid)
                f_new_item = self.draw_item(
                    f_item.track_num, f_item.bar_num, f_item_name)
                if f_new_item.get_selected_string() in \
                self.selected_item_strings:
                    f_new_item.setSelected(True)
        if REGION_EDITOR_MODE == 1:
            self.open_atm_region()
            TRACK_PANEL.update_ccs_in_use()
        self.setUpdatesEnabled(True)
        self.update()
        self.enabled = True

    def open_atm_region(self):
        for f_track in TRACK_PANEL.tracks:
            f_port, f_index = TRACK_PANEL.has_automation(f_track)
            if f_port is not None:
                for f_point in ATM_REGION.get_points(f_index, f_port):
                    self.draw_point(f_point)

    def clear_drawn_items(self):
        global REGION_EDITOR_GRID_WIDTH, REGION_EDITOR_MAX_START
        self.item_length = pydaw_get_current_region_length()
        self.viewer_width = self.width() - 50.0
        REGION_EDITOR_MAX_START = self.width() - 51.0
        REGION_EDITOR_GRID_WIDTH = self.viewer_width
        self.px_per_bar = \
            self.viewer_width / float(pydaw_get_current_region_length())
        self.px_per_beat = self.px_per_bar / 4.0

        self.region_items = {}
        self.painter_path_cache = {}
        self.automation_points = []
        self.scene.clear()
        self.update_note_height()
        self.draw_header()
        self.draw_grid()
        self.set_header_pos()

    def clear_new(self):
        """ Reset the region editor state to empty """
        self.clear_drawn_items()
        #self.reset_tracks()
        self.enabled = False
        global REGION_CLIPBOARD
        REGION_CLIPBOARD = []

    def clearSelection(self):
        self.scene.clearSelection()

    def draw_item(self, a_track, a_bar, a_name, a_selected=False):
        if a_name in self.painter_path_cache:
            f_path = self.painter_path_cache[a_name]
        else:
            f_item_obj = PROJECT.get_item_by_name(a_name)
            f_path = f_item_obj.painter_path(
                REGION_EDITOR_GRID_WIDTH / pydaw_get_current_region_length(),
                REGION_EDITOR_TRACK_HEIGHT)
            self.painter_path_cache[a_name] = f_path
        f_item = region_editor_item(a_track, a_bar, a_name, f_path)
        self.scene.addItem(f_item)
        if a_selected:
            f_item.setSelected(True)
        self.set_item(f_item)
        return f_item

    def draw_point(self, a_point):
        if a_point.index not in TRACK_PANEL.plugin_uid_map:
            print("{} not in {}".format(
                a_point.index, TRACK_PANEL.plugin_uid_map))
            return
        f_track = TRACK_PANEL.plugin_uid_map[a_point.index]
        f_min = (f_track *
            REGION_EDITOR_TRACK_HEIGHT) + REGION_EDITOR_HEADER_HEIGHT
        f_max = f_min + REGION_EDITOR_TRACK_HEIGHT - ATM_POINT_DIAMETER
        f_item = atm_item(
            a_point, self.automation_save_callback, f_min, f_max)
        self.scene.addItem(f_item)
        f_item.setPos(self.get_pos_from_point(a_point))
        self.automation_points.append(f_item)
        if str(a_point) in self.selected_point_strings:
            f_item.setSelected(True)

    def pop_item(self, a_item):
        self.region_items[a_item.track_num].pop(a_item.bar)

    def pop_orig_item(self, a_item):
        self.region_items[a_item.orig_track_num].pop(a_item.orig_bar)

    def set_item(self, a_item):
        if not a_item.track_num in self.region_items:
            self.region_items[a_item.track_num] = {}
        if a_item.bar in self.region_items[a_item.track_num]:
            f_old = self.region_items[a_item.track_num][a_item.bar]
            if f_old != a_item and f_old.scene():
                self.scene.removeItem(f_old)
        self.region_items[a_item.track_num][a_item.bar] = a_item

    def smooth_atm_points(self):
        if not self.current_coord:
            return
        f_track, f_bar, f_beat, f_val = self.current_coord
        f_index, f_plugin = TRACK_PANEL.get_atm_params(f_track)
        if f_index is None:
            return
        f_port, f_index = TRACK_PANEL.has_automation(f_track)
        f_points = [x.item for x in self.get_selected_points()]
        ATM_REGION.smooth_points(f_index, f_port, f_plugin, f_points)
        self.automation_save_callback()
        self.open_region()

    def transpose_dialog(self):
        if REGION_EDITOR_MODE != 0:
            return
        if pydaw_current_region_is_none():
            return

        f_item_set = {x.name for x in self.get_selected_items()}
        if len(f_item_set) == 0:
            QtGui.QMessageBox.warning(
                MAIN_WINDOW, _("Error"), _("No items selected"))
            return

        def transpose_ok_handler():
            for f_item_name in f_item_set:
                f_item = PROJECT.get_item_by_name(f_item_name)
                f_item.transpose(
                    f_semitone.value(), f_octave.value(),
                    a_selected_only=False,
                    a_duplicate=f_duplicate_notes.isChecked())
                PROJECT.save_item(f_item_name, f_item)
            PROJECT.commit(_("Transpose item(s)"))
            if len(OPEN_ITEM_UIDS) > 0:
                global_open_items()
            f_window.close()

        def transpose_cancel_handler():
            f_window.close()

        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Transpose"))
        f_layout = QtGui.QGridLayout()
        f_window.setLayout(f_layout)

        f_semitone = QtGui.QSpinBox()
        f_semitone.setRange(-12, 12)
        f_layout.addWidget(QtGui.QLabel(_("Semitones")), 0, 0)
        f_layout.addWidget(f_semitone, 0, 1)
        f_octave = QtGui.QSpinBox()
        f_octave.setRange(-5, 5)
        f_layout.addWidget(QtGui.QLabel(_("Octaves")), 1, 0)
        f_layout.addWidget(f_octave, 1, 1)
        f_duplicate_notes = QtGui.QCheckBox(_("Duplicate notes?"))
        f_duplicate_notes.setToolTip(
            _("Checking this box causes the transposed "
            "notes to be added rather than moving the existing notes."))
        f_layout.addWidget(f_duplicate_notes, 2, 1)
        f_ok = QtGui.QPushButton(_("OK"))
        f_ok.pressed.connect(transpose_ok_handler)
        f_layout.addWidget(f_ok, 6, 0)
        f_cancel = QtGui.QPushButton(_("Cancel"))
        f_cancel.pressed.connect(transpose_cancel_handler)
        f_layout.addWidget(f_cancel, 6, 1)
        f_window.exec_()

    def cut_selected(self):
        self.copy_selected()
        self.delete_selected()

    def edit_unique(self):
        self.edit_group(True)

    def edit_group(self, a_unique=False):
        if REGION_EDITOR_MODE != 0:
            return
        f_result = [x.name for x in self.get_selected_items()]
        f_result2 = []
        for x in f_result:
            if x not in f_result2:
                f_result2.append(x)
        if not a_unique and len(f_result2) != len(f_result):
            QtGui.QMessageBox.warning(
                self, _("Error"),
                _("You cannot open multiple instances of the same "
                "item as a group.\n"
                "You should unlink all duplicate instances into their own "
                "individual item names before editing as a group."))
            return

        if f_result2:
            global_open_items(f_result2, a_reset_scrollbar=True)
            MAIN_WINDOW.main_tabwidget.setCurrentIndex(1)
        else:
            QtGui.QMessageBox.warning(
                self, _("Error"), _("No items selected"))


    def on_rename_items(self):
        if REGION_EDITOR_MODE != 0:
            return
        f_result = []
        for f_item_name in (x.name for x in self.get_selected_items()):
            if not f_item_name in f_result:
                f_result.append(f_item_name)
        if not f_result:
            return

        def ok_handler():
            f_new_name = str(f_new_lineedit.text())
            if f_new_name == "":
                QtGui.QMessageBox.warning(
                    self.group_box, _("Error"), _("Name cannot be blank"))
                return
            global REGION_CLIPBOARD, OPEN_ITEM_NAMES, \
                LAST_OPEN_ITEM_NAMES, LAST_OPEN_ITEM_UIDS
            #Clear the clipboard, otherwise the names could be invalid
            REGION_CLIPBOARD = []
            OPEN_ITEM_NAMES = []
            LAST_OPEN_ITEM_NAMES = []
            LAST_OPEN_ITEM_UIDS = []
            PROJECT.rename_items(f_result, f_new_name)
            PROJECT.commit(_("Rename items"))
            REGION_SETTINGS.open_region_by_uid(CURRENT_REGION.uid)
            global_update_items_label()
            if DRAW_LAST_ITEMS:
                global_open_items()
                OPEN_ITEM_NAMES = ITEM_EDITOR.item_names[:]
            f_window.close()

        def cancel_handler():
            f_window.close()

        def on_name_changed():
            f_new_lineedit.setText(
                pydaw_remove_bad_chars(f_new_lineedit.text()))

        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Rename selected items..."))
        f_layout = QtGui.QGridLayout()
        f_window.setLayout(f_layout)
        f_new_lineedit = QtGui.QLineEdit()
        f_new_lineedit.editingFinished.connect(on_name_changed)
        f_new_lineedit.setMaxLength(24)
        f_layout.addWidget(QtGui.QLabel(_("New name:")), 0, 0)
        f_layout.addWidget(f_new_lineedit, 0, 1)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_layout.addWidget(f_ok_button, 5, 0)
        f_ok_button.clicked.connect(ok_handler)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_layout.addWidget(f_cancel_button, 5, 1)
        f_cancel_button.clicked.connect(cancel_handler)
        f_window.exec_()

    def on_unlink_item(self):
        """ Rename a single instance of an item and
            make it into a new item
        """
        if not self.enabled:
            self.warn_no_region_selected()
            return
        if REGION_EDITOR_MODE != 0:
            return
        if not self.current_coord or not self.current_item:
            return

        f_current_item_text = self.current_item.name
        x, y, f_beat = self.current_coord[:3]

        def note_ok_handler():
            f_cell_text = str(f_new_lineedit.text())
            if f_cell_text == f_current_item_text:
                QtGui.QMessageBox.warning(
                    self.group_box, _("Error"),
                    _("You must choose a different name than the "
                    "original item"))
                return
            if PROJECT.item_exists(f_cell_text):
                QtGui.QMessageBox.warning(
                    self.group_box, _("Error"),
                    _("An item with this name already exists."))
                return
            f_uid = PROJECT.copy_item(
                f_current_item_text, str(f_new_lineedit.text()))
            global_open_items([f_cell_text], a_reset_scrollbar=True)
            self.last_item_copied = f_cell_text
            CURRENT_REGION.add_item_ref_by_uid(x, y, f_uid)
            PROJECT.save_region(
                str(REGION_SETTINGS.region_name_lineedit.text()),
                CURRENT_REGION)
            PROJECT.commit(
                _("Unlink item '{}' as '{}'").format(
                f_current_item_text, f_cell_text))
            self.open_region()
            f_window.close()

        def note_cancel_handler():
            f_window.close()

        def on_name_changed():
            f_new_lineedit.setText(
                pydaw_remove_bad_chars(f_new_lineedit.text()))

        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Copy and unlink item..."))
        f_layout = QtGui.QGridLayout()
        f_window.setLayout(f_layout)
        f_new_lineedit = QtGui.QLineEdit(f_current_item_text)
        f_new_lineedit.editingFinished.connect(on_name_changed)
        f_new_lineedit.setMaxLength(24)
        f_layout.addWidget(QtGui.QLabel(_("New name:")), 0, 0)
        f_layout.addWidget(f_new_lineedit, 0, 1)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_layout.addWidget(f_ok_button, 5, 0)
        f_ok_button.clicked.connect(note_ok_handler)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_layout.addWidget(f_cancel_button, 5, 1)
        f_cancel_button.clicked.connect(note_cancel_handler)
        f_window.exec_()

    def on_auto_unlink_selected(self):
        """ Adds an automatic -N suffix """
        if REGION_EDITOR_MODE != 0:
            return
        for f_item in self.get_selected_items():
            f_name_suffix = 1
            while PROJECT.item_exists(
            "{}-{}".format(f_item.name, f_name_suffix)):
                f_name_suffix += 1
            f_cell_text = "{}-{}".format(f_item.name, f_name_suffix)
            f_uid = PROJECT.copy_item(f_item.name, f_cell_text)
            self.draw_item(f_item.track_num, f_item.bar, f_cell_text, True)
            if f_item.scene():
                self.scene.removeItem(f_item)
            CURRENT_REGION.add_item_ref_by_uid(
                f_item.track_num, f_item.bar, f_uid)
        self.set_selected_strings()
        PROJECT.save_region(
            str(REGION_SETTINGS.region_name_lineedit.text()),
            CURRENT_REGION)
        PROJECT.commit(_("Auto-Unlink items"))

    def on_auto_unlink_unique(self):
        if REGION_EDITOR_MODE != 0:
            return
        f_result = {(x.track_num, x.bar):x.name
            for x in self.get_selected_items()}

        for f_item in self.get_selected_items():
            if f_item.scene():
                self.scene.removeItem(f_item)

        old_new_map = {}

        for f_item_name in set(f_result.values()):
            f_name_suffix = 1
            while PROJECT.item_exists(
            "{}-{}".format(f_item_name, f_name_suffix)):
                f_name_suffix += 1
            f_cell_text = "{}-{}".format(f_item_name, f_name_suffix)
            f_uid = PROJECT.copy_item(f_item_name, f_cell_text)
            old_new_map[f_item_name] = (f_cell_text, f_uid)

        for k, v in f_result.items():
            self.draw_item(k[0], k[1], old_new_map[v][0], True)
            CURRENT_REGION.add_item_ref_by_uid(k[0], k[1], old_new_map[v][1])
        PROJECT.save_region(
            str(REGION_SETTINGS.region_name_lineedit.text()),
            CURRENT_REGION)
        PROJECT.commit(_("Auto-Unlink unique items"))

    def paste_to_region_end(self):
        if not self.enabled:
            self.warn_no_region_selected()
            return
        if not self.current_coord:
            return
        if REGION_EDITOR_MODE == 0:
            if len(REGION_CLIPBOARD) != 1:
                QtGui.QMessageBox.warning(
                    MAIN_WINDOW, _("Error"), _("Paste to region end only "
                    "works when you have exactly one item copied to the "
                    "clipboard.\n"
                    "You have {} items copied.").format(len(REGION_CLIPBOARD)))
                return
            f_base_row, f_base_column, f_beat = self.current_coord[:3]
            f_region_length = pydaw_get_current_region_length()
            f_item = REGION_CLIPBOARD[0]
            for f_column in range(f_base_column, f_region_length):
                self.draw_item(f_base_row, f_column, f_item[2])
            global_tablewidget_to_region()
        elif REGION_EDITOR_MODE == 1:
            raise NotImplementedError()
            # this will be tricky and require new variables

    def paste_at_original_pos(self):
        self.paste_clipboard(True)

    def paste_clipboard(self, a_original_pos=False):
        if not self.enabled:
            self.warn_no_region_selected()
            return
        if REGION_EDITOR_MODE == 0:
            if a_original_pos:
                f_base_row = REGION_CLIPBOARD_ROW_OFFSET
                f_base_column = REGION_CLIPBOARD_COL_OFFSET
            else:
                if not self.current_coord:
                    return
                f_base_row, f_base_column, f_beat = self.current_coord[:3]
            self.scene.clearSelection()
            f_region_length = pydaw_get_current_region_length()
            for f_item in REGION_CLIPBOARD:
                f_column = f_item[1] + f_base_column
                if f_column >= f_region_length or f_column < 0:
                    continue
                f_row = f_item[0] + f_base_row
                if f_row >= len(TRACK_PANEL.tracks) or f_row < 0:
                    continue
                self.draw_item(f_row, f_column, f_item[2], a_selected=True)
            global_tablewidget_to_region()
            global_update_hidden_rows()
        elif REGION_EDITOR_MODE == 1:
            if not self.current_coord:
                return
            f_track_port_num, f_track_index = TRACK_PANEL.has_automation(
                self.current_coord[0])
            if f_track_port_num is None:
                QtGui.QMessageBox.warning(
                    self, _("Error"),
                    _("No automation selected for this track"))
                return
            f_row, f_base_column, f_val, f_beat = self.current_coord
            f_track_params = TRACK_PANEL.get_atm_params(f_row)
            self.scene.clearSelection()
            f_region_length = pydaw_get_current_region_length()
            for f_item in ATM_CLIPBOARD:
                f_column = f_item[1] + f_base_column
                if f_column >= f_region_length or f_column < 0:
                    continue
                f_point = f_item[2]
                ATM_REGION.add_point(
                    pydaw_atm_point(
                        f_column, f_point.beat, f_track_port_num,
                        f_point.cc_val, *f_track_params))
            self.automation_save_callback()
            self.open_region()

    def delete_selected(self):
        if not self.enabled:
            self.warn_no_region_selected()
            return
        if REGION_EDITOR_MODE == 0:
            for f_item in self.get_selected_items():
                self.scene.removeItem(f_item)
                self.pop_item(f_item)
            global_tablewidget_to_region()
            #self.scene.clearSelection()
        elif REGION_EDITOR_MODE == 1:
            for f_point in self.get_selected_points():
                ATM_REGION.remove_point(f_point.item)
            self.automation_save_callback()
            self.open_region()

    def copy_selected(self):
        if not self.enabled:
            self.warn_no_region_selected()
            return
        if REGION_EDITOR_MODE == 0:
            global REGION_CLIPBOARD, REGION_CLIPBOARD_ROW_OFFSET, \
                REGION_CLIPBOARD_COL_OFFSET
            REGION_CLIPBOARD = []  #Clear the clipboard
            for f_item in self.get_selected_items():
                REGION_CLIPBOARD.append(
                    [f_item.track_num, f_item.bar, f_item.name])
            if REGION_CLIPBOARD:
                REGION_CLIPBOARD.sort(key=lambda x: x[0])
                f_row_offset = REGION_CLIPBOARD[0][0]
                for f_item in REGION_CLIPBOARD:
                    f_item[0] -= f_row_offset
                REGION_CLIPBOARD.sort(key=lambda x: x[1])
                f_column_offset = REGION_CLIPBOARD[0][1]
                for f_item in REGION_CLIPBOARD:
                    f_item[1] -= f_column_offset
                REGION_CLIPBOARD_COL_OFFSET = f_column_offset
                REGION_CLIPBOARD_ROW_OFFSET = f_row_offset
        elif REGION_EDITOR_MODE == 1:
            global ATM_CLIPBOARD, ATM_CLIPBOARD_ROW_OFFSET, \
                ATM_CLIPBOARD_COL_OFFSET
            ATM_CLIPBOARD = []  #Clear the clipboard
            for f_item in self.get_selected_points(self.current_coord[0]):
                ATM_CLIPBOARD.append(
                    [f_item.item.track, f_item.item.bar, f_item.item])
            if ATM_CLIPBOARD:
                ATM_CLIPBOARD.sort(key=lambda x: x[0])
                f_row_offset = ATM_CLIPBOARD[0][0]
                for f_item in ATM_CLIPBOARD:
                    f_item[0] -= f_row_offset
                ATM_CLIPBOARD.sort(key=lambda x: x[1])
                f_column_offset = ATM_CLIPBOARD[0][1]
                for f_item in ATM_CLIPBOARD:
                    f_item[1] -= f_column_offset
                ATM_CLIPBOARD_COL_OFFSET = f_column_offset
                ATM_CLIPBOARD_ROW_OFFSET = f_row_offset

    def warn_no_region_selected(self):
        QtGui.QMessageBox.warning(
            MAIN_WINDOW, _("Error"),
            _("You must create or select a region first by clicking "
            "in the song editor above."))

    def tablewidget_to_list(self):
        """ Convert an edited QTableWidget to a list of tuples
            for a region ref
        """
        return [(x.track_num, x.bar, x.name) for x in self.get_all_items()]


ATM_CLIPBOARD_ROW_OFFSET = 0
ATM_CLIPBOARD_COL_OFFSET = 0

ATM_CLIPBOARD = []

REGION_CLIPBOARD_ROW_OFFSET = 0
REGION_CLIPBOARD_COL_OFFSET = 0

REGION_CLIPBOARD = []

def global_tablewidget_to_region():
    CURRENT_REGION.items = []
    f_uid_dict = PROJECT.get_items_dict()
    f_result = REGION_EDITOR.tablewidget_to_list()
    for f_tuple in f_result:
        CURRENT_REGION.add_item_ref_by_name(
            f_tuple[0], f_tuple[1], f_tuple[2], f_uid_dict)
    PROJECT.save_region(
        str(REGION_SETTINGS.region_name_lineedit.text()), CURRENT_REGION)
    PROJECT.commit(_("Edit region"))
    REGION_EDITOR.open_region()


def global_update_track_comboboxes(a_index=None, a_value=None):
    if not a_index is None and not a_value is None:
        TRACK_NAMES[int(a_index)] = str(a_value)
    global SUPPRESS_TRACK_COMBOBOX_CHANGES
    SUPPRESS_TRACK_COMBOBOX_CHANGES = True
    for f_cbox in AUDIO_TRACK_COMBOBOXES:
        f_current_index = f_cbox.currentIndex()
        f_cbox.clear()
        f_cbox.clearEditText()
        f_cbox.addItems(TRACK_NAMES)
        f_cbox.setCurrentIndex(f_current_index)

    SUPPRESS_TRACK_COMBOBOX_CHANGES = False
    ROUTING_GRAPH_WIDGET.draw_graph(
        PROJECT.get_routing_graph(), TRACK_PANEL.get_track_names())
    global_open_mixer()


#TODO:  Clean these up...
BEATS_PER_MINUTE = 128.0
BEATS_PER_SECOND = BEATS_PER_MINUTE / 60.0
BARS_PER_SECOND = BEATS_PER_SECOND * 0.25

def pydaw_set_bpm(a_bpm):
    global BEATS_PER_MINUTE, BEATS_PER_SECOND, BARS_PER_SECOND
    BEATS_PER_MINUTE = a_bpm
    BEATS_PER_SECOND = a_bpm / 60.0
    BARS_PER_SECOND = BEATS_PER_SECOND * 0.25
    pydaw_widgets.set_global_tempo(a_bpm)

def pydaw_seconds_to_bars(a_seconds):
    '''converts seconds to regions'''
    return a_seconds * BARS_PER_SECOND

def pydaw_set_audio_seq_zoom(a_horizontal, a_vertical):
    global AUDIO_PX_PER_BAR, AUDIO_PX_PER_BEAT, \
           AUDIO_PX_PER_8TH, AUDIO_PX_PER_12TH, \
           AUDIO_PX_PER_16TH, AUDIO_ITEM_HEIGHT

    f_width = float(AUDIO_SEQ.rect().width()) - \
        float(AUDIO_SEQ.verticalScrollBar().width()) - 6.0
    f_region_length = pydaw_get_current_region_length()
    f_region_px = f_region_length * 100.0
    f_region_scale = f_width / f_region_px

    AUDIO_PX_PER_BAR = 100.0 * a_horizontal * f_region_scale
    AUDIO_PX_PER_BEAT = AUDIO_PX_PER_BAR * 0.25 # / 4.0
    AUDIO_PX_PER_8TH = AUDIO_PX_PER_BAR * 0.125 # / 8.0
    AUDIO_PX_PER_12TH = AUDIO_PX_PER_BAR / 12.0
    AUDIO_PX_PER_16TH = AUDIO_PX_PER_BAR * 0.0625 # / 16.0
    pydaw_set_audio_snap(AUDIO_SNAP_VAL)
    AUDIO_ITEM_HEIGHT = 75.0 * a_vertical


def pydaw_set_audio_snap(a_val):
    global AUDIO_QUANTIZE, AUDIO_QUANTIZE_PX, \
           AUDIO_QUANTIZE_AMT, AUDIO_SNAP_VAL, \
           AUDIO_LINES_ENABLED, AUDIO_SNAP_RANGE
    AUDIO_SNAP_VAL = a_val
    AUDIO_QUANTIZE = True
    AUDIO_LINES_ENABLED = True
    AUDIO_SNAP_RANGE = 8
    if a_val == 0:
        AUDIO_QUANTIZE = False
        AUDIO_QUANTIZE_PX = AUDIO_PX_PER_BEAT
        AUDIO_LINES_ENABLED = False
    elif a_val == 1:
        AUDIO_QUANTIZE_PX = AUDIO_PX_PER_BAR
        AUDIO_LINES_ENABLED = False
        AUDIO_QUANTIZE_AMT = 0.25
    elif a_val == 2:
        AUDIO_QUANTIZE_PX = AUDIO_PX_PER_BEAT
        AUDIO_LINES_ENABLED = False
        AUDIO_QUANTIZE_AMT = 1.0
    elif a_val == 3:
        AUDIO_QUANTIZE_PX = AUDIO_PX_PER_8TH
        AUDIO_SNAP_RANGE = 2
        AUDIO_QUANTIZE_AMT = 2.0
    elif a_val == 4:
        AUDIO_QUANTIZE_PX = AUDIO_PX_PER_12TH
        AUDIO_SNAP_RANGE = 3
        AUDIO_QUANTIZE_AMT = 3.0
    elif a_val == 5:
        AUDIO_QUANTIZE_PX = AUDIO_PX_PER_16TH
        AUDIO_SNAP_RANGE = 4
        AUDIO_QUANTIZE_AMT = 4.0

AUDIO_LINES_ENABLED = True
AUDIO_SNAP_RANGE = 8
AUDIO_SNAP_VAL = 2
AUDIO_PX_PER_BAR = 100.0
AUDIO_PX_PER_BEAT = AUDIO_PX_PER_BAR / 4.0
AUDIO_PX_PER_8TH = AUDIO_PX_PER_BAR / 8.0
AUDIO_PX_PER_12TH = AUDIO_PX_PER_BAR / 12.0
AUDIO_PX_PER_16TH = AUDIO_PX_PER_BAR / 16.0

AUDIO_QUANTIZE = False
AUDIO_QUANTIZE_PX = 25.0
AUDIO_QUANTIZE_AMT = 1.0

AUDIO_RULER_HEIGHT = 20.0
AUDIO_ITEM_HEIGHT = 75.0

AUDIO_ITEM_HANDLE_HEIGHT = 12.0
AUDIO_ITEM_HANDLE_SIZE = 6.25

AUDIO_ITEM_HANDLE_BRUSH = QtGui.QLinearGradient(
    0.0, 0.0, AUDIO_ITEM_HANDLE_SIZE, AUDIO_ITEM_HANDLE_HEIGHT)
AUDIO_ITEM_HANDLE_BRUSH.setColorAt(
    0.0, QtGui.QColor.fromRgb(255, 255, 255, 120))
AUDIO_ITEM_HANDLE_BRUSH.setColorAt(
    0.0, QtGui.QColor.fromRgb(255, 255, 255, 90))

AUDIO_ITEM_HANDLE_SELECTED_BRUSH = QtGui.QLinearGradient(
    0.0, 0.0, AUDIO_ITEM_HANDLE_SIZE, AUDIO_ITEM_HANDLE_HEIGHT)
AUDIO_ITEM_HANDLE_SELECTED_BRUSH.setColorAt(
    0.0, QtGui.QColor.fromRgb(24, 24, 24, 120))
AUDIO_ITEM_HANDLE_SELECTED_BRUSH.setColorAt(
    0.0, QtGui.QColor.fromRgb(24, 24, 24, 90))


AUDIO_ITEM_HANDLE_PEN = QtGui.QPen(QtCore.Qt.white)
AUDIO_ITEM_LINE_PEN = QtGui.QPen(QtCore.Qt.white, 2.0)
AUDIO_ITEM_HANDLE_SELECTED_PEN = QtGui.QPen(QtGui.QColor.fromRgb(24, 24, 24))
AUDIO_ITEM_LINE_SELECTED_PEN = QtGui.QPen(
    QtGui.QColor.fromRgb(24, 24, 24), 2.0)

AUDIO_ITEM_MAX_LANE = 23
AUDIO_ITEM_LANE_COUNT = 24

LAST_AUDIO_ITEM_DIR = global_home


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
    f_db_spinbox.setDecimals(1)
    f_hlayout.addWidget(f_db_spinbox)
    f_db_spinbox.setRange(-18, 0)
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

class audio_viewer_item(QtGui.QGraphicsRectItem):
    def __init__(self, a_track_num, a_audio_item, a_graph):
        QtGui.QGraphicsRectItem.__init__(self)
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setFlag(QtGui.QGraphicsItem.ItemClipsChildrenToShape)

        self.sample_length = a_graph.length_in_seconds
        self.graph_object = a_graph
        self.audio_item = a_audio_item
        self.orig_string = str(a_audio_item)
        self.track_num = a_track_num
        f_graph = libmk.PROJECT.get_sample_graph_by_uid(
            self.audio_item.uid)
        self.painter_paths = f_graph.create_sample_graph(True)
        self.y_inc = AUDIO_ITEM_HEIGHT / len(self.painter_paths)
        f_y_pos = 0.0
        self.path_items = []
        for f_painter_path in self.painter_paths:
            f_path_item = QtGui.QGraphicsPathItem(f_painter_path)
            f_path_item.setBrush(
                mk_project.pydaw_audio_item_scene_gradient)
            f_path_item.setParentItem(self)
            f_path_item.mapToParent(0.0, 0.0)
            self.path_items.append(f_path_item)
            f_y_pos += self.y_inc
        f_file_name = libmk.PROJECT.get_wav_name_by_uid(
            self.audio_item.uid)
        f_file_name = libmk.PROJECT.timestretch_lookup_orig_path(
            f_file_name)
        f_name_arr = f_file_name.rsplit("/", 1)
        f_name = f_name_arr[-1]
        self.label = QtGui.QGraphicsSimpleTextItem(f_name, parent=self)
        self.label.setPos(10, (AUDIO_ITEM_HEIGHT * 0.5) -
            (self.label.boundingRect().height() * 0.5))
        self.label.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations)

        self.start_handle = QtGui.QGraphicsRectItem(parent=self)
        self.start_handle.setAcceptHoverEvents(True)
        self.start_handle.hoverEnterEvent = self.generic_hoverEnterEvent
        self.start_handle.hoverLeaveEvent = self.generic_hoverLeaveEvent
        self.start_handle.setRect(
            QtCore.QRectF(0.0, 0.0, AUDIO_ITEM_HANDLE_SIZE,
                          AUDIO_ITEM_HANDLE_HEIGHT))
        self.start_handle.mousePressEvent = self.start_handle_mouseClickEvent
        self.start_handle_line = QtGui.QGraphicsLineItem(
            0.0, AUDIO_ITEM_HANDLE_HEIGHT, 0.0,
            (AUDIO_ITEM_HEIGHT * -1.0) + AUDIO_ITEM_HANDLE_HEIGHT,
            self.start_handle)

        self.start_handle_line.setPen(AUDIO_ITEM_LINE_PEN)

        self.length_handle = QtGui.QGraphicsRectItem(parent=self)
        self.length_handle.setAcceptHoverEvents(True)
        self.length_handle.hoverEnterEvent = self.generic_hoverEnterEvent
        self.length_handle.hoverLeaveEvent = self.generic_hoverLeaveEvent
        self.length_handle.setRect(
            QtCore.QRectF(0.0, 0.0, AUDIO_ITEM_HANDLE_SIZE,
                          AUDIO_ITEM_HANDLE_HEIGHT))
        self.length_handle.mousePressEvent = self.length_handle_mouseClickEvent
        self.length_handle_line = QtGui.QGraphicsLineItem(
            AUDIO_ITEM_HANDLE_SIZE, AUDIO_ITEM_HANDLE_HEIGHT,
            AUDIO_ITEM_HANDLE_SIZE,
            (AUDIO_ITEM_HEIGHT * -1.0) + AUDIO_ITEM_HANDLE_HEIGHT,
            self.length_handle)

        self.fade_in_handle = QtGui.QGraphicsRectItem(parent=self)
        self.fade_in_handle.setAcceptHoverEvents(True)
        self.fade_in_handle.hoverEnterEvent = self.generic_hoverEnterEvent
        self.fade_in_handle.hoverLeaveEvent = self.generic_hoverLeaveEvent
        self.fade_in_handle.setRect(
            QtCore.QRectF(0.0, 0.0, AUDIO_ITEM_HANDLE_SIZE,
                          AUDIO_ITEM_HANDLE_HEIGHT))
        self.fade_in_handle.mousePressEvent = \
            self.fade_in_handle_mouseClickEvent
        self.fade_in_handle_line = QtGui.QGraphicsLineItem(
            0.0, 0.0, 0.0, 0.0, self)

        self.fade_out_handle = QtGui.QGraphicsRectItem(parent=self)
        self.fade_out_handle.setAcceptHoverEvents(True)
        self.fade_out_handle.hoverEnterEvent = self.generic_hoverEnterEvent
        self.fade_out_handle.hoverLeaveEvent = self.generic_hoverLeaveEvent
        self.fade_out_handle.setRect(
            QtCore.QRectF(0.0, 0.0, AUDIO_ITEM_HANDLE_SIZE,
                          AUDIO_ITEM_HANDLE_HEIGHT))
        self.fade_out_handle.mousePressEvent = \
            self.fade_out_handle_mouseClickEvent
        self.fade_out_handle_line = QtGui.QGraphicsLineItem(
            0.0, 0.0, 0.0, 0.0, self)

        self.stretch_handle = QtGui.QGraphicsRectItem(parent=self)
        self.stretch_handle.setAcceptHoverEvents(True)
        self.stretch_handle.hoverEnterEvent = self.generic_hoverEnterEvent
        self.stretch_handle.hoverLeaveEvent = self.generic_hoverLeaveEvent
        self.stretch_handle.setRect(
            QtCore.QRectF(0.0, 0.0, AUDIO_ITEM_HANDLE_SIZE,
                          AUDIO_ITEM_HANDLE_HEIGHT))
        self.stretch_handle.mousePressEvent = \
            self.stretch_handle_mouseClickEvent
        self.stretch_handle_line = QtGui.QGraphicsLineItem(
            AUDIO_ITEM_HANDLE_SIZE,
            (AUDIO_ITEM_HANDLE_HEIGHT * 0.5) - (AUDIO_ITEM_HEIGHT * 0.5),
            AUDIO_ITEM_HANDLE_SIZE,
            (AUDIO_ITEM_HEIGHT * 0.5) + (AUDIO_ITEM_HANDLE_HEIGHT * 0.5),
            self.stretch_handle)
        self.stretch_handle.hide()

        self.split_line = QtGui.QGraphicsLineItem(
            0.0, 0.0, 0.0, AUDIO_ITEM_HEIGHT, self)
        self.split_line.mapFromParent(0.0, 0.0)
        self.split_line.hide()
        self.split_line_is_shown = False

        self.setAcceptHoverEvents(True)

        self.is_start_resizing = False
        self.is_resizing = False
        self.is_copying = False
        self.is_fading_in = False
        self.is_fading_out = False
        self.is_stretching = False
        self.set_brush()
        self.waveforms_scaled = False
        self.is_amp_curving = False
        self.is_amp_dragging = False
        self.event_pos_orig = None
        self.width_orig = None
        self.vol_linear = pydaw_db_to_lin(self.audio_item.vol)
        self.quantize_offset = 0.0
        if libmk.TOOLTIPS_ENABLED:
            self.set_tooltips(True)
        self.draw()

    def generic_hoverEnterEvent(self, a_event):
        QtGui.QApplication.setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.SizeHorCursor))

    def generic_hoverLeaveEvent(self, a_event):
        QtGui.QApplication.restoreOverrideCursor()

    def draw(self):
        f_temp_seconds = self.sample_length

        if self.audio_item.time_stretch_mode == 1 and \
        (self.audio_item.pitch_shift_end == self.audio_item.pitch_shift):
            f_temp_seconds /= pydaw_pitch_to_ratio(self.audio_item.pitch_shift)
        elif self.audio_item.time_stretch_mode == 2 and \
        (self.audio_item.timestretch_amt_end ==
        self.audio_item.timestretch_amt):
            f_temp_seconds *= self.audio_item.timestretch_amt

        f_start = float(self.audio_item.start_bar) + \
            (self.audio_item.start_beat * 0.25)
        f_start *= AUDIO_PX_PER_BAR

        f_length_seconds = \
            pydaw_seconds_to_bars(f_temp_seconds) * AUDIO_PX_PER_BAR
        self.length_seconds_orig_px = f_length_seconds
        self.rect_orig = QtCore.QRectF(
            0.0, 0.0, f_length_seconds, AUDIO_ITEM_HEIGHT)
        self.length_px_start = \
            (self.audio_item.sample_start * 0.001 * f_length_seconds)
        self.length_px_minus_start = f_length_seconds - self.length_px_start
        self.length_px_minus_end = \
            (self.audio_item.sample_end * 0.001 * f_length_seconds)
        f_length = self.length_px_minus_end - self.length_px_start

        f_track_num = \
        AUDIO_RULER_HEIGHT + (AUDIO_ITEM_HEIGHT) * self.audio_item.lane_num

        f_fade_in = self.audio_item.fade_in * 0.001
        f_fade_out = self.audio_item.fade_out * 0.001
        self.setRect(0.0, 0.0, f_length, AUDIO_ITEM_HEIGHT)
        f_fade_in_handle_pos = (f_length * f_fade_in)
        f_fade_in_handle_pos = pydaw_clip_value(
            f_fade_in_handle_pos, 0.0, (f_length - 6.0))
        f_fade_out_handle_pos = \
            (f_length * f_fade_out) - AUDIO_ITEM_HANDLE_SIZE
        f_fade_out_handle_pos = pydaw_clip_value(
            f_fade_out_handle_pos, (f_fade_in_handle_pos + 6.0), f_length)
        self.fade_in_handle.setPos(f_fade_in_handle_pos, 0.0)
        self.fade_out_handle.setPos(f_fade_out_handle_pos, 0.0)
        self.update_fade_in_line()
        self.update_fade_out_line()
        self.setPos(f_start, f_track_num)
        self.is_moving = False
        if self.audio_item.time_stretch_mode >= 3 or \
        (self.audio_item.time_stretch_mode == 2 and \
        (self.audio_item.timestretch_amt_end ==
        self.audio_item.timestretch_amt)):
            self.stretch_width_default = \
                f_length / self.audio_item.timestretch_amt

        self.sample_start_offset_px = \
        self.audio_item.sample_start * -0.001 * self.length_seconds_orig_px

        self.start_handle_scene_min = f_start + self.sample_start_offset_px
        self.start_handle_scene_max = \
            self.start_handle_scene_min + self.length_seconds_orig_px

        if not self.waveforms_scaled:
            f_channels = len(self.painter_paths)
            f_i_inc = 1.0 / f_channels
            f_i = f_i_inc
            f_y_inc = 0.0
            # Kludge to fix the problem, there must be a better way...
            if f_channels == 1:
                f_y_offset = \
                    (1.0 - self.vol_linear) * (AUDIO_ITEM_HEIGHT * 0.5)
            else:
                f_y_offset = (1.0 - self.vol_linear) * self.y_inc * f_i_inc
            for f_path_item in self.path_items:
                if self.audio_item.reversed:
                    f_path_item.setPos(
                        self.sample_start_offset_px +
                        self.length_seconds_orig_px,
                        self.y_inc + (f_y_offset * -1.0) + (f_y_inc * f_i))
                    f_path_item.rotate(-180.0)
                else:
                    f_path_item.setPos(
                        self.sample_start_offset_px,
                        f_y_offset + (f_y_inc * f_i))
                f_x_scale, f_y_scale = pydaw_scale_to_rect(
                    mk_project.pydaw_audio_item_scene_rect, self.rect_orig)
                f_y_scale *= self.vol_linear
                f_path_item.scale(f_x_scale, f_y_scale)
                f_i += f_i_inc
                f_y_inc += self.y_inc
        self.waveforms_scaled = True

        self.length_handle.setPos(
            f_length - AUDIO_ITEM_HANDLE_SIZE,
            AUDIO_ITEM_HEIGHT - AUDIO_ITEM_HANDLE_HEIGHT)
        self.start_handle.setPos(
            0.0, AUDIO_ITEM_HEIGHT - AUDIO_ITEM_HANDLE_HEIGHT)
        if self.audio_item.time_stretch_mode >= 2 and \
        (((self.audio_item.time_stretch_mode != 5) and \
        (self.audio_item.time_stretch_mode != 2)) \
        or (self.audio_item.timestretch_amt_end ==
        self.audio_item.timestretch_amt)):
            self.stretch_handle.show()
            self.stretch_handle.setPos(f_length - AUDIO_ITEM_HANDLE_SIZE,
                                       (AUDIO_ITEM_HEIGHT * 0.5) -
                                       (AUDIO_ITEM_HANDLE_HEIGHT * 0.5))

    def set_tooltips(self, a_on):
        if a_on:
            self.setToolTip(libpydaw.strings.audio_viewer_item)
            self.start_handle.setToolTip(
                _("Use this handle to resize the item by changing "
                "the start point."))
            self.length_handle.setToolTip(
                _("Use this handle to resize the item by "
                "changing the end point."))
            self.fade_in_handle.setToolTip(
                _("Use this handle to change the fade in."))
            self.fade_out_handle.setToolTip(
                _("Use this handle to change the fade out."))
            self.stretch_handle.setToolTip(
                _("Use this handle to resize the item by "
                "time-stretching it."))
        else:
            self.setToolTip("")
            self.start_handle.setToolTip("")
            self.length_handle.setToolTip("")
            self.fade_in_handle.setToolTip("")
            self.fade_out_handle.setToolTip("")
            self.stretch_handle.setToolTip("")

    def clip_at_region_end(self):
        f_current_region_length = pydaw_get_current_region_length()
        f_max_x = f_current_region_length * AUDIO_PX_PER_BAR
        f_pos_x = self.pos().x()
        f_end = f_pos_x + self.rect().width()
        if f_end > f_max_x:
            f_end_px = f_max_x - f_pos_x
            self.setRect(0.0, 0.0, f_end_px, AUDIO_ITEM_HEIGHT)
            self.audio_item.sample_end = \
                ((self.rect().width() + self.length_px_start) /
                self.length_seconds_orig_px) * 1000.0
            self.audio_item.sample_end = pydaw_util.pydaw_clip_value(
                self.audio_item.sample_end, 1.0, 1000.0, True)
            self.draw()
            return True
        else:
            return False

    def set_brush(self, a_index=None):
        if self.isSelected():
            self.setBrush(pydaw_selected_gradient)
            self.start_handle.setPen(AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.length_handle.setPen(AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.fade_in_handle.setPen(AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.fade_out_handle.setPen(AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.stretch_handle.setPen(AUDIO_ITEM_HANDLE_SELECTED_PEN)
            self.split_line.setPen(AUDIO_ITEM_HANDLE_SELECTED_PEN)

            self.start_handle_line.setPen(AUDIO_ITEM_LINE_SELECTED_PEN)
            self.length_handle_line.setPen(AUDIO_ITEM_LINE_SELECTED_PEN)
            self.fade_in_handle_line.setPen(AUDIO_ITEM_LINE_SELECTED_PEN)
            self.fade_out_handle_line.setPen(AUDIO_ITEM_LINE_SELECTED_PEN)
            self.stretch_handle_line.setPen(AUDIO_ITEM_LINE_SELECTED_PEN)

            self.label.setBrush(QtCore.Qt.darkGray)
            self.start_handle.setBrush(AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
            self.length_handle.setBrush(AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
            self.fade_in_handle.setBrush(AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
            self.fade_out_handle.setBrush(AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
            self.stretch_handle.setBrush(AUDIO_ITEM_HANDLE_SELECTED_BRUSH)
        else:
            self.start_handle.setPen(AUDIO_ITEM_HANDLE_PEN)
            self.length_handle.setPen(AUDIO_ITEM_HANDLE_PEN)
            self.fade_in_handle.setPen(AUDIO_ITEM_HANDLE_PEN)
            self.fade_out_handle.setPen(AUDIO_ITEM_HANDLE_PEN)
            self.stretch_handle.setPen(AUDIO_ITEM_HANDLE_PEN)
            self.split_line.setPen(AUDIO_ITEM_HANDLE_PEN)

            self.start_handle_line.setPen(AUDIO_ITEM_LINE_PEN)
            self.length_handle_line.setPen(AUDIO_ITEM_LINE_PEN)
            self.fade_in_handle_line.setPen(AUDIO_ITEM_LINE_PEN)
            self.fade_out_handle_line.setPen(AUDIO_ITEM_LINE_PEN)
            self.stretch_handle_line.setPen(AUDIO_ITEM_LINE_PEN)

            self.label.setBrush(QtCore.Qt.white)
            self.start_handle.setBrush(AUDIO_ITEM_HANDLE_BRUSH)
            self.length_handle.setBrush(AUDIO_ITEM_HANDLE_BRUSH)
            self.fade_in_handle.setBrush(AUDIO_ITEM_HANDLE_BRUSH)
            self.fade_out_handle.setBrush(AUDIO_ITEM_HANDLE_BRUSH)
            self.stretch_handle.setBrush(AUDIO_ITEM_HANDLE_BRUSH)
            if a_index is None:
                self.setBrush(pydaw_track_gradients[
                self.audio_item.lane_num % len(pydaw_track_gradients)])
            else:
                self.setBrush(pydaw_track_gradients[
                    a_index % len(pydaw_track_gradients)])

    def pos_to_musical_time(self, a_pos):
        f_bar_frac = a_pos / AUDIO_PX_PER_BAR
        f_pos_bars = int(f_bar_frac)
        f_pos_beats = (f_bar_frac - f_pos_bars) * 4.0
        return(f_pos_bars, f_pos_beats)

    def start_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QtGui.QGraphicsRectItem.mousePressEvent(self.length_handle, a_event)
        for f_item in AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_item.min_start = f_item.pos().x() * -1.0
                f_item.is_start_resizing = True
                f_item.setFlag(QtGui.QGraphicsItem.ItemClipsChildrenToShape,
                               False)

    def length_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QtGui.QGraphicsRectItem.mousePressEvent(self.length_handle, a_event)
        for f_item in AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_item.is_resizing = True
                f_item.setFlag(QtGui.QGraphicsItem.ItemClipsChildrenToShape,
                               False)

    def fade_in_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QtGui.QGraphicsRectItem.mousePressEvent(self.fade_in_handle, a_event)
        for f_item in AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_item.is_fading_in = True

    def fade_out_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QtGui.QGraphicsRectItem.mousePressEvent(self.fade_out_handle, a_event)
        for f_item in AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_item.is_fading_out = True

    def stretch_handle_mouseClickEvent(self, a_event):
        if libmk.IS_PLAYING:
            return
        self.check_selected_status()
        a_event.setAccepted(True)
        QtGui.QGraphicsRectItem.mousePressEvent(self.stretch_handle, a_event)
        f_max_region_pos = AUDIO_PX_PER_BAR * pydaw_get_current_region_length()
        for f_item in AUDIO_SEQ.audio_items:
            if f_item.isSelected() and \
            f_item.audio_item.time_stretch_mode >= 2:
                f_item.is_stretching = True
                f_item.max_stretch = f_max_region_pos - f_item.pos().x()
                f_item.setFlag(
                    QtGui.QGraphicsItem.ItemClipsChildrenToShape, False)
                #for f_path in f_item.path_items:
                #    f_path.hide()

    def check_selected_status(self):
        """ If a handle is clicked and not selected, clear the selection
            and select only this item
        """
        if not self.isSelected():
            AUDIO_SEQ.scene.clearSelection()
            self.setSelected(True)

    def show_context_menu(self):
        global CURRENT_AUDIO_ITEM_INDEX
        f_CURRENT_AUDIO_ITEM_INDEX = CURRENT_AUDIO_ITEM_INDEX
        CURRENT_AUDIO_ITEM_INDEX = self.track_num
        f_menu = QtGui.QMenu(MAIN_WINDOW)

        f_file_menu = f_menu.addMenu(_("File"))
        f_save_a_copy_action = f_file_menu.addAction(_("Save a Copy..."))
        f_save_a_copy_action.triggered.connect(self.save_a_copy)
        f_open_folder_action = f_file_menu.addAction(_("Open File in Browser"))
        f_open_folder_action.triggered.connect(self.open_item_folder)
        f_wave_editor_action = f_file_menu.addAction(_("Open in Wave Editor"))
        f_wave_editor_action.triggered.connect(self.open_in_wave_editor)
        f_copy_file_path_action = f_file_menu.addAction(
            _("Copy File Path to Clipboard"))
        f_copy_file_path_action.triggered.connect(
            self.copy_file_path_to_clipboard)
        f_select_instance_action = f_file_menu.addAction(
            _("Select All Instances of This File"))
        f_select_instance_action.triggered.connect(self.select_file_instance)
        f_file_menu.addSeparator()
        f_replace_action = f_file_menu.addAction(
            _("Replace with Path in Clipboard"))
        f_replace_action.triggered.connect(self.replace_with_path_in_clipboard)

        f_properties_menu = f_menu.addMenu(_("Properties"))
        f_output_menu = f_properties_menu.addMenu("Track")
        f_output_menu.triggered.connect(self.output_menu_triggered)

        f_output_tracks = {x.audio_item.output_track
            for x in AUDIO_SEQ.get_selected()}

        for f_track_name, f_index in zip(
        TRACK_NAMES, range(len(TRACK_NAMES))):
            f_action = f_output_menu.addAction(f_track_name)
            if len(f_output_tracks) == 1 and f_index in f_output_tracks:
                f_action.setCheckable(True)
                f_action.setChecked(True)

        f_ts_mode_menu = f_properties_menu.addMenu("Timestretch Mode")
        f_ts_mode_menu.triggered.connect(self.ts_mode_menu_triggered)

        f_ts_modes = {x.audio_item.time_stretch_mode
            for x in AUDIO_SEQ.get_selected()}

        for f_ts_mode, f_index in zip(
        TIMESTRETCH_MODES, range(len(TIMESTRETCH_MODES))):
            f_action = f_ts_mode_menu.addAction(f_ts_mode)
            if len(f_ts_modes) == 1 and f_index in f_ts_modes:
                f_action.setCheckable(True)
                f_action.setChecked(True)

        if len(f_ts_modes) == 1 and [x for x in (3, 4) if x in f_ts_modes]:
            f_crisp_menu = f_properties_menu.addMenu("Crispness")
            f_crisp_menu.triggered.connect(self.crisp_menu_triggered)
            f_crisp_settings = {x.audio_item.crispness
                for x in AUDIO_SEQ.get_selected()}
            for f_crisp_mode, f_index in zip(
            CRISPNESS_SETTINGS, range(len(CRISPNESS_SETTINGS))):
                f_action = f_crisp_menu.addAction(f_crisp_mode)
                if len(f_crisp_settings) == 1 and \
                f_index in f_crisp_settings:
                    f_action.setCheckable(True)
                    f_action.setChecked(True)

        f_volume_action = f_properties_menu.addAction(_("Volume..."))
        f_volume_action.triggered.connect(self.volume_dialog)
        f_normalize_action = f_properties_menu.addAction(_("Normalize..."))
        f_normalize_action.triggered.connect(self.normalize_dialog)
        f_reset_fades_action = f_properties_menu.addAction(_("Reset Fades"))
        f_reset_fades_action.triggered.connect(self.reset_fades)
        f_reset_end_action = f_properties_menu.addAction(_("Reset Ends"))
        f_reset_end_action.triggered.connect(self.reset_end)
        f_move_to_end_action = f_properties_menu.addAction(
            _("Move to Region End"))
        f_move_to_end_action.triggered.connect(self.move_to_region_end)
        f_reverse_action = f_properties_menu.addAction(_("Reverse/Unreverse"))
        f_reverse_action.triggered.connect(self.reverse)
        f_time_pitch_action = f_properties_menu.addAction(_("Time/Pitch..."))
        f_time_pitch_action.triggered.connect(self.time_pitch_dialog)
        f_fade_vol_action = f_properties_menu.addAction(_("Fade Volume..."))
        f_fade_vol_action.triggered.connect(self.fade_vol_dialog)
        f_sends_action = f_properties_menu.addAction(_("Sends..."))
        f_sends_action.triggered.connect(self.sends_dialog)

        f_paif_menu = f_menu.addMenu(_("Per-Item FX"))
        f_edit_paif_action = f_paif_menu.addAction(_("Edit Per-Item Effects"))
        f_edit_paif_action.triggered.connect(self.edit_paif)
        f_paif_menu.addSeparator()
        f_paif_copy = f_paif_menu.addAction(_("Copy"))
        f_paif_copy.triggered.connect(
            AUDIO_SEQ_WIDGET.on_modulex_copy)
        f_paif_paste = f_paif_menu.addAction(_("Paste"))
        f_paif_paste.triggered.connect(
            AUDIO_SEQ_WIDGET.on_modulex_paste)
        f_paif_clear = f_paif_menu.addAction(_("Clear"))
        f_paif_clear.triggered.connect(
            AUDIO_SEQ_WIDGET.on_modulex_clear)

        f_per_file_menu = f_menu.addMenu("For All Instances of This File Set")
        f_all_volumes_action = f_per_file_menu.addAction(_("Volume..."))
        f_all_volumes_action.triggered.connect(self.set_vol_for_all_instances)
        f_all_fades_action = f_per_file_menu.addAction(_("Fades"))
        f_all_fades_action.triggered.connect(self.set_fades_for_all_instances)
        f_all_paif_action = f_per_file_menu.addAction(_("Per-Item FX"))
        f_all_paif_action.triggered.connect(self.set_paif_for_all_instance)

        f_set_all_output_menu = f_per_file_menu.addMenu("Track")
        f_set_all_output_menu.triggered.connect(
            self.set_all_output_menu_triggered)
        for f_track_name, f_index in zip(
        TRACK_NAMES, range(len(TRACK_NAMES))):
            f_action = f_set_all_output_menu.addAction(f_track_name)
            if f_index == self.audio_item.output_track:
                f_action.setCheckable(True)
                f_action.setChecked(True)

        f_groove_menu = f_menu.addMenu(_("Groove"))
        f_copy_as_cc_action = f_groove_menu.addAction(
            _("Copy Volume Envelope as CC Automation"))
        f_copy_as_cc_action.triggered.connect(
            self.copy_as_cc_automation)
        f_copy_as_pb_action = f_groove_menu.addAction(
            _("Copy Volume Envelope as Pitchbend Automation"))
        f_copy_as_pb_action.triggered.connect(
            self.copy_as_pb_automation)
        f_copy_as_notes_action = f_groove_menu.addAction(
            _("Copy Volume Envelope as MIDI Notes"))
        f_copy_as_notes_action.triggered.connect(self.copy_as_notes)

        f_menu.exec_(QtGui.QCursor.pos())
        CURRENT_AUDIO_ITEM_INDEX = f_CURRENT_AUDIO_ITEM_INDEX

    def time_pitch_dialog(self):
        f_dialog = time_pitch_dialog_widget(self.audio_item)
        f_dialog.widget.exec_()

    def fade_vol_dialog(self):
        f_dialog = fade_vol_dialog_widget(self.audio_item)
        f_dialog.widget.exec_()

    def copy_as_cc_automation(self):
        CC_EDITOR.clipboard = en_project.envelope_to_automation(
            self.graph_object, True, TRANSPORT.tempo_spinbox.value())

    def copy_as_pb_automation(self):
        PB_EDITOR.clipboard = en_project.envelope_to_automation(
            self.graph_object, False, TRANSPORT.tempo_spinbox.value())

    def copy_as_notes(self):
        PIANO_ROLL_EDITOR.clipboard = en_project.envelope_to_notes(
            self.graph_object, TRANSPORT.tempo_spinbox.value())

    def output_menu_triggered(self, a_action):
        f_index = TRACK_NAMES.index(str(a_action.text()))
        f_list = [x.audio_item for x in AUDIO_SEQ.audio_items
            if x.isSelected()]
        for f_item in f_list:
            f_item.output_track = f_index
        PROJECT.save_audio_region(CURRENT_REGION.uid, AUDIO_ITEMS)
        PROJECT.commit(_("Change output track for audio item(s)"))
        global_open_audio_items()

    def crisp_menu_triggered(self, a_action):
        f_index = CRISPNESS_SETTINGS.index(str(a_action.text()))
        f_list = [x.audio_item for x in AUDIO_SEQ.get_selected() if
            x.audio_item.time_stretch_mode in (3, 4)]
        for f_item in f_list:
            f_item.crispness = f_index
        self.timestretch_items(f_list)

    def ts_mode_menu_triggered(self, a_action):
        f_index = TIMESTRETCH_MODES.index(str(a_action.text()))
        f_list = [x.audio_item for x in AUDIO_SEQ.get_selected()]
        for f_item in f_list:
            f_item.time_stretch_mode = f_index
        self.timestretch_items(f_list)

    def timestretch_items(self, a_list):
        f_stretched_items = []
        for f_item in a_list:
            if f_item.time_stretch_mode >= 3:
                f_ts_result = libmk.PROJECT.timestretch_audio_item(f_item)
                if f_ts_result is not None:
                    f_stretched_items.append(f_ts_result)

        libmk.PROJECT.save_stretch_dicts()

        for f_stretch_item in f_stretched_items:
            f_stretch_item[2].wait()
            libmk.PROJECT.get_wav_uid_by_name(
                f_stretch_item[0], a_uid=f_stretch_item[1])
        for f_audio_item in AUDIO_SEQ.get_selected():
            f_new_graph = libmk.PROJECT.get_sample_graph_by_uid(
                f_audio_item.audio_item.uid)
            f_audio_item.audio_item.clip_at_region_end(
                pydaw_get_current_region_length(),
                TRANSPORT.tempo_spinbox.value(),
                f_new_graph.length_in_seconds)

        PROJECT.save_audio_region(CURRENT_REGION.uid, AUDIO_ITEMS)
        PROJECT.commit(_("Change timestretch mode for audio item(s)"))
        global_open_audio_items()

    def select_file_instance(self):
        AUDIO_SEQ.scene.clearSelection()
        f_uid = self.audio_item.uid
        for f_item in AUDIO_SEQ.audio_items:
            if f_item.audio_item.uid == f_uid:
                f_item.setSelected(True)

    def set_paif_for_all_instance(self):
        f_paif = PROJECT.get_audio_per_item_fx_region(
            CURRENT_REGION.uid)
        f_paif_row = f_paif.get_row(self.track_num)
        PROJECT.set_paif_for_all_audio_items(
            self.audio_item.uid, f_paif_row)

    def set_all_output_menu_triggered(self, a_action):
        f_index = TRACK_NAMES.index(str(a_action.text()))
        PROJECT.set_output_for_all_audio_items(
            self.audio_item.uid, f_index)
        global_open_audio_items()

    def set_fades_for_all_instances(self):
        PROJECT.set_fades_for_all_audio_items(self.audio_item)
        global_open_audio_items()

    def sends_dialog(self):
        def ok_handler():
            f_list = [x.audio_item for x in AUDIO_SEQ.audio_items
                if x.isSelected()]
            for f_item in f_list:
                f_item.output_track = f_track_cboxes[0].currentIndex()
                f_item.vol = get_vol(f_track_vols[0].value())
                f_item.s0_sc = f_sc_checkboxes[0].isChecked()
                f_item.send1 = f_track_cboxes[1].currentIndex() - 1
                f_item.s1_vol = get_vol(f_track_vols[1].value())
                f_item.s1_sc = f_sc_checkboxes[1].isChecked()
                f_item.send2 = f_track_cboxes[2].currentIndex() - 1
                f_item.s2_vol = get_vol(f_track_vols[2].value())
                f_item.s2_sc = f_sc_checkboxes[2].isChecked()
            PROJECT.save_audio_region(CURRENT_REGION.uid, AUDIO_ITEMS)
            PROJECT.commit(_("Update sends for audio item(s)"))
            global_open_audio_items()
            f_dialog.close()

        def cancel_handler():
            f_dialog.close()

        def vol_changed(a_val=None):
            for f_vol_label, f_vol_slider in zip(f_vol_labels, f_track_vols):
                f_vol_label.setText(
                    "{}dB".format(get_vol(f_vol_slider.value())))

        def get_vol(a_val):
            return round(a_val * 0.1, 1)

        f_dialog = QtGui.QDialog(MAIN_WINDOW)
        f_dialog.setWindowTitle(_("Set Volume for all Instance of File"))
        f_layout = QtGui.QGridLayout(f_dialog)
        f_layout.setAlignment(QtCore.Qt.AlignCenter)
        f_track_cboxes = []
        f_sc_checkboxes = []
        f_track_vols = []
        f_vol_labels = []
        f_current_vals = [
            (self.audio_item.output_track, self.audio_item.vol,
             self.audio_item.s0_sc),
            (self.audio_item.send1, self.audio_item.s1_vol,
             self.audio_item.s1_sc),
            (self.audio_item.send2, self.audio_item.s2_vol,
             self.audio_item.s2_sc)]
        for f_i in range(3):
            f_out, f_vol, f_sc = f_current_vals[f_i]
            f_tracks_combobox = QtGui.QComboBox()
            f_track_cboxes.append(f_tracks_combobox)
            if f_i == 0:
                f_tracks_combobox.addItems(TRACK_NAMES)
                f_tracks_combobox.setCurrentIndex(f_out)
            else:
                f_tracks_combobox.addItems(["None"] + TRACK_NAMES)
                f_tracks_combobox.setCurrentIndex(f_out + 1)
            f_tracks_combobox.setMinimumWidth(105)
            f_layout.addWidget(f_tracks_combobox, 0, f_i)
            f_sc_checkbox = QtGui.QCheckBox(_("Sidechain"))
            f_sc_checkboxes.append(f_sc_checkbox)
            if f_sc:
                f_sc_checkbox.setChecked(True)
            f_layout.addWidget(f_sc_checkbox, 1, f_i)
            f_vol_slider = QtGui.QSlider(QtCore.Qt.Vertical)
            f_track_vols.append(f_vol_slider)
            f_vol_slider.setRange(-240, 240)
            f_vol_slider.setMinimumHeight(360)
            f_vol_slider.valueChanged.connect(vol_changed)
            f_layout.addWidget(f_vol_slider, 2, f_i, QtCore.Qt.AlignCenter)
            f_vol_label = QtGui.QLabel("0.0dB")
            f_vol_labels.append(f_vol_label)
            f_layout.addWidget(f_vol_label, 3, f_i)
            f_vol_slider.setValue(f_vol * 10.0)

        f_ok_cancel_layout = QtGui.QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout, 10, 2)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_handler)
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_dialog.exec_()


    def set_vol_for_all_instances(self):
        def ok_handler():
            f_index = f_reverse_combobox.currentIndex()
            f_reverse_val = None
            if f_index == 1:
                f_reverse_val = False
            elif f_index == 2:
                f_reverse_val = True
            PROJECT.set_vol_for_all_audio_items(
                self.audio_item.uid, get_vol(), f_reverse_val,
                f_same_vol_checkbox.isChecked(), self.audio_item.vol)
            f_dialog.close()
            global_open_audio_items()

        def cancel_handler():
            f_dialog.close()

        def vol_changed(a_val=None):
            f_vol_label.setText("{}dB".format(get_vol()))

        def get_vol():
            return round(f_vol_slider.value() * 0.1, 1)

        f_dialog = QtGui.QDialog(MAIN_WINDOW)
        f_dialog.setWindowTitle(_("Set Volume for all Instance of File"))
        f_layout = QtGui.QGridLayout(f_dialog)
        f_layout.setAlignment(QtCore.Qt.AlignCenter)
        f_vol_slider = QtGui.QSlider(QtCore.Qt.Vertical)
        f_vol_slider.setRange(-240, 240)
        f_vol_slider.setMinimumHeight(360)
        f_vol_slider.valueChanged.connect(vol_changed)
        f_layout.addWidget(f_vol_slider, 0, 1, QtCore.Qt.AlignCenter)
        f_vol_label = QtGui.QLabel("0dB")
        f_layout.addWidget(f_vol_label, 1, 1)
        f_vol_slider.setValue(self.audio_item.vol)
        f_reverse_combobox = QtGui.QComboBox()
        f_reverse_combobox.addItems(
            [_("Either"), _("Not-Reversed"), _("Reversed")])
        f_reverse_combobox.setMinimumWidth(105)
        f_layout.addWidget(QtGui.QLabel(_("Reversed Items?")), 2, 0)
        f_layout.addWidget(f_reverse_combobox, 2, 1)
        f_same_vol_checkbox = QtGui.QCheckBox(
            _("Only items with same volume?"))
        f_layout.addWidget(f_same_vol_checkbox, 3, 1)
        f_ok_cancel_layout = QtGui.QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout, 10, 1)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_ok_button.pressed.connect(ok_handler)
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_dialog.exec_()

    def reverse(self):
        f_list = AUDIO_SEQ.get_selected()
        for f_item in f_list:
            f_item.audio_item.reversed = not f_item.audio_item.reversed
        PROJECT.save_audio_region(CURRENT_REGION.uid, AUDIO_ITEMS)
        PROJECT.commit(_("Toggle audio items reversed"))
        global_open_audio_items(True)

    def move_to_region_end(self):
        f_list = AUDIO_SEQ.get_selected()
        if f_list:
            f_current_region_length = pydaw_get_current_region_length()
            f_global_tempo = float(TRANSPORT.tempo_spinbox.value())
            for f_item in f_list:
                f_item.audio_item.clip_at_region_end(
                    f_current_region_length, f_global_tempo,
                    f_item.graph_object.length_in_seconds, False)
            PROJECT.save_audio_region(CURRENT_REGION.uid, AUDIO_ITEMS)
            PROJECT.commit(_("Move audio item(s) to region end"))
            global_open_audio_items(True)

    def reset_fades(self):
        f_list = AUDIO_SEQ.get_selected()
        if f_list:
            for f_item in f_list:
                f_item.audio_item.fade_in = 0.0
                f_item.audio_item.fade_out = 999.0
            PROJECT.save_audio_region(CURRENT_REGION.uid, AUDIO_ITEMS)
            PROJECT.commit(_("Reset audio item fades"))
            global_open_audio_items(True)

    def reset_end(self):
        f_list = AUDIO_SEQ.get_selected()
        for f_item in f_list:
            f_item.audio_item.sample_start = 0.0
            f_item.audio_item.sample_end = 1000.0
            self.draw()
            self.clip_at_region_end()
        PROJECT.save_audio_region(CURRENT_REGION.uid, AUDIO_ITEMS)
        PROJECT.commit(_("Reset sample ends for audio item(s)"))
        global_open_audio_items()

    def replace_with_path_in_clipboard(self):
        f_path = global_get_audio_file_from_clipboard()
        if f_path is not None:
            self.audio_item.uid = libmk.PROJECT.get_wav_uid_by_name(f_path)
            PROJECT.save_audio_region(CURRENT_REGION.uid, AUDIO_ITEMS)
            PROJECT.commit(_("Replace audio item"))
            global_open_audio_items(True)

    def open_in_wave_editor(self):
        f_path = self.get_file_path()
        libmk.MAIN_WINDOW.open_in_wave_editor(f_path)

    def edit_paif(self):
        AUDIO_SEQ.scene.clearSelection()
        self.setSelected(True)
        AUDIO_SEQ_WIDGET.folders_tab_widget.setCurrentIndex(2)

    def normalize(self, a_value):
        f_val = self.graph_object.normalize(a_value)
        self.audio_item.vol = f_val

    def volume_dialog(self):
        def on_ok():
            f_val = round(f_db_spinbox.value(), 1)
            for f_item in AUDIO_SEQ.get_selected():
                f_item.audio_item.vol = f_val
            PROJECT.save_audio_region(CURRENT_REGION.uid, AUDIO_ITEMS)
            PROJECT.commit(_("Normalize audio items"))
            global_open_audio_items(True)
            f_window.close()

        def on_cancel():
            f_window.close()

        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.f_result = None
        f_window.setWindowTitle(_("Volume"))
        f_window.setFixedSize(150, 90)
        f_layout = QtGui.QVBoxLayout()
        f_window.setLayout(f_layout)
        f_hlayout = QtGui.QHBoxLayout()
        f_layout.addLayout(f_hlayout)
        f_hlayout.addWidget(QtGui.QLabel("dB"))
        f_db_spinbox = QtGui.QDoubleSpinBox()
        f_hlayout.addWidget(f_db_spinbox)
        f_db_spinbox.setDecimals(1)
        f_db_spinbox.setRange(-24, 24)
        f_vols = {x.audio_item.vol for x in AUDIO_SEQ.get_selected()}
        if len(f_vols) == 1:
            f_db_spinbox.setValue(f_vols.pop())
        else:
            f_db_spinbox.setValue(0)
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


    def normalize_dialog(self):
        f_val = normalize_dialog()
        if f_val is None:
            return
        f_save = False
        for f_item in AUDIO_SEQ.get_selected():
            f_save = True
            f_item.normalize(f_val)
        if f_save:
            PROJECT.save_audio_region(CURRENT_REGION.uid, AUDIO_ITEMS)
            PROJECT.commit(_("Normalize audio items"))
            global_open_audio_items(True)

    def get_file_path(self):
        return libmk.PROJECT.get_wav_path_by_uid(self.audio_item.uid)

    def copy_file_path_to_clipboard(self):
        f_path = self.get_file_path()
        f_clipboard = QtGui.QApplication.clipboard()
        f_clipboard.setText(f_path)

    def save_a_copy(self):
        global LAST_AUDIO_ITEM_DIR
        f_file = QtGui.QFileDialog.getSaveFileName(
            parent=AUDIO_SEQ,
            caption=_('Save audio item as .wav'),
            directory=LAST_AUDIO_ITEM_DIR)
        if not f_file is None and not str(f_file) == "":
            f_file = str(f_file)
            if not f_file.endswith(".wav"):
                f_file += ".wav"
            LAST_AUDIO_ITEM_DIR = os.path.dirname(f_file)
            f_orig_path = libmk.PROJECT.get_wav_name_by_uid(
                self.audio_item.uid)
            shutil.copy(f_orig_path, f_file)

    def open_item_folder(self):
        f_path = libmk.PROJECT.get_wav_name_by_uid(self.audio_item.uid)
        AUDIO_SEQ_WIDGET.open_file_in_browser(f_path)

    def mousePressEvent(self, a_event):
        if libmk.IS_PLAYING:
            return

        if a_event.modifiers() == (QtCore.Qt.AltModifier |
        QtCore.Qt.ShiftModifier):
            self.setSelected((not self.isSelected()))
            return

        if not self.isSelected():
            AUDIO_SEQ.scene.clearSelection()
            self.setSelected(True)

        if a_event.button() == QtCore.Qt.RightButton:
            self.show_context_menu()
            return

        if a_event.modifiers() == QtCore.Qt.ShiftModifier:
            f_per_item_fx_dict = \
            PROJECT.get_audio_per_item_fx_region(
                CURRENT_REGION.uid)

            f_item = self.audio_item
            f_item_old = f_item.clone()
            f_item.fade_in = 0.0
            f_item_old.fade_out = 999.0
            f_width_percent = a_event.pos().x() / self.rect().width()
            f_item.fade_out = pydaw_clip_value(
                f_item.fade_out, (f_item.fade_in + 90.0), 999.0, True)
            f_item_old.fade_in /= f_width_percent
            f_item_old.fade_in = pydaw_clip_value(
                f_item_old.fade_in, 0.0, (f_item_old.fade_out - 90.0), True)

            f_index = AUDIO_ITEMS.get_next_index()
            if f_index == -1:
                QtGui.QMessageBox.warning(
                    self, _("Error"),
                    _("No more available audio item slots, max per region "
                    "is {}").format(MAX_AUDIO_ITEM_COUNT))
                return
            else:
                AUDIO_ITEMS.add_item(f_index, f_item_old)
                f_per_item_fx = f_per_item_fx_dict.get_row(self.track_num)
                if f_per_item_fx is not None:
                    f_per_item_fx_dict.set_row(f_index, f_per_item_fx)
                    f_save_paif = True
                else:
                    f_save_paif = False

            f_event_pos = a_event.pos().x()
            # for items that are not quantized
            f_pos = f_event_pos - (f_event_pos - self.quantize(f_event_pos))
            f_scene_pos = self.quantize(a_event.scenePos().x())
            f_musical_pos = self.pos_to_musical_time(f_scene_pos)
            f_sample_shown = f_item.sample_end - f_item.sample_start
            f_sample_rect_pos = f_pos / self.rect().width()
            f_item.sample_start = \
                (f_sample_rect_pos * f_sample_shown) + f_item.sample_start
            f_item.sample_start = pydaw_clip_value(
                f_item.sample_start, 0.0, 999.0, True)
            f_item.start_bar = f_musical_pos[0]
            f_item.start_beat = f_musical_pos[1]
            f_item_old.sample_end = f_item.sample_start
            PROJECT.save_audio_region(CURRENT_REGION.uid, AUDIO_ITEMS)
            if f_save_paif:
                PROJECT.save_audio_per_item_fx_region(
                    CURRENT_REGION.uid, f_per_item_fx_dict, False)
                PROJECT.en_osc.pydaw_audio_per_item_fx_region(
                    CURRENT_REGION.uid)
            PROJECT.commit(_("Split audio item"))
            global_open_audio_items(True)
        elif a_event.modifiers() == \
        QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier:
            self.is_amp_dragging = True
        elif a_event.modifiers() == \
        QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier:
            self.is_amp_curving = True
            f_list = [((x.audio_item.start_bar * 4.0) +
                x.audio_item.start_beat)
                for x in AUDIO_SEQ.audio_items if x.isSelected()]
            f_list.sort()
            self.vc_start = f_list[0]
            self.vc_mid = (self.audio_item.start_bar *
                4.0) + self.audio_item.start_beat
            self.vc_end = f_list[-1]
        else:
            if a_event.modifiers() == QtCore.Qt.ControlModifier:
                f_per_item_fx_dict = PROJECT.get_audio_per_item_fx_region(
                    CURRENT_REGION.uid)
            QtGui.QGraphicsRectItem.mousePressEvent(self, a_event)
            self.event_pos_orig = a_event.pos().x()
            for f_item in AUDIO_SEQ.get_selected():
                f_item_pos = f_item.pos().x()
                f_item.quantize_offset = \
                    f_item_pos - f_item.quantize_all(f_item_pos)
                if a_event.modifiers() == QtCore.Qt.ControlModifier:
                    f_item.is_copying = True
                    f_item.width_orig = f_item.rect().width()
                    f_item.per_item_fx = \
                        f_per_item_fx_dict.get_row(f_item.track_num)
                    AUDIO_SEQ.draw_item(
                        f_item.track_num, f_item.audio_item,
                        f_item.graph_object)
                if self.is_fading_out:
                    f_item.fade_orig_pos = f_item.fade_out_handle.pos().x()
                elif self.is_fading_in:
                    f_item.fade_orig_pos = f_item.fade_in_handle.pos().x()
                if self.is_start_resizing:
                    f_item.width_orig = 0.0
                else:
                    f_item.width_orig = f_item.rect().width()
        if self.is_amp_curving or self.is_amp_dragging:
            a_event.setAccepted(True)
            self.setSelected(True)
            self.event_pos_orig = a_event.pos().x()
            QtGui.QGraphicsRectItem.mousePressEvent(self, a_event)
            self.orig_y = a_event.pos().y()
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.BlankCursor)
            for f_item in AUDIO_SEQ.get_selected():
                f_item.orig_value = f_item.audio_item.vol
                f_item.add_vol_line()

    def hoverEnterEvent(self, a_event):
        f_item_pos = self.pos().x()
        self.quantize_offset = f_item_pos - self.quantize_all(f_item_pos)

    def hoverMoveEvent(self, a_event):
        if a_event.modifiers() == QtCore.Qt.ShiftModifier:
            if not self.split_line_is_shown:
                self.split_line_is_shown = True
                self.split_line.show()
            f_x = a_event.pos().x()
            f_x = self.quantize_all(f_x)
            f_x -= self.quantize_offset
            self.split_line.setPos(f_x, 0.0)
        else:
            if self.split_line_is_shown:
                self.split_line_is_shown = False
                self.split_line.hide()

    def hoverLeaveEvent(self, a_event):
        if self.split_line_is_shown:
            self.split_line_is_shown = False
            self.split_line.hide()

    def y_pos_to_lane_number(self, a_y_pos):
        f_lane_num = int((a_y_pos - AUDIO_RULER_HEIGHT) / AUDIO_ITEM_HEIGHT)
        f_lane_num = pydaw_clip_value(
            f_lane_num, 0, AUDIO_ITEM_MAX_LANE)
        f_y_pos = (f_lane_num * AUDIO_ITEM_HEIGHT) + AUDIO_RULER_HEIGHT
        return f_lane_num, f_y_pos

    def quantize_all(self, a_x):
        f_x = a_x
        if AUDIO_QUANTIZE:
            f_x = round(f_x / AUDIO_QUANTIZE_PX) * AUDIO_QUANTIZE_PX
        return f_x

    def quantize(self, a_x):
        f_x = a_x
        f_x = self.quantize_all(f_x)
        if AUDIO_QUANTIZE and f_x < AUDIO_QUANTIZE_PX:
            f_x = AUDIO_QUANTIZE_PX
        return f_x

    def quantize_start(self, a_x):
        f_x = a_x
        f_x = self.quantize_all(f_x)
        if f_x >= self.length_handle.pos().x():
            f_x -= AUDIO_QUANTIZE_PX
        return f_x

    def quantize_scene(self, a_x):
        f_x = a_x
        f_x = self.quantize_all(f_x)
        return f_x

    def update_fade_in_line(self):
        f_pos = self.fade_in_handle.pos()
        self.fade_in_handle_line.setLine(
            f_pos.x(), 0.0, 0.0, AUDIO_ITEM_HEIGHT)

    def update_fade_out_line(self):
        f_pos = self.fade_out_handle.pos()
        self.fade_out_handle_line.setLine(
            f_pos.x() + AUDIO_ITEM_HANDLE_SIZE, 0.0,
            self.rect().width(), AUDIO_ITEM_HEIGHT)

    def add_vol_line(self):
        self.vol_line = QtGui.QGraphicsLineItem(
            0.0, 0.0, self.rect().width(), 0.0, self)
        self.vol_line.setPen(QtGui.QPen(QtCore.Qt.red, 2.0))
        self.set_vol_line()

    def set_vol_line(self):
        f_pos = (float(48 - (self.audio_item.vol + 24))
            * 0.020833333) * AUDIO_ITEM_HEIGHT # 1.0 / 48.0
        self.vol_line.setPos(0, f_pos)
        self.label.setText("{}dB".format(self.audio_item.vol))

    def mouseMoveEvent(self, a_event):
        if libmk.IS_PLAYING or self.event_pos_orig is None:
            return
        if self.is_amp_curving or self.is_amp_dragging:
            f_pos = a_event.pos()
            f_y = f_pos.y()
            f_diff_y = self.orig_y - f_y
            f_val = (f_diff_y * 0.05)
        f_event_pos = a_event.pos().x()
        f_event_diff = f_event_pos - self.event_pos_orig
        if self.is_resizing:
            for f_item in AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    f_x = f_item.width_orig + f_event_diff + \
                        f_item.quantize_offset
                    f_x = pydaw_clip_value(
                        f_x, AUDIO_ITEM_HANDLE_SIZE,
                        f_item.length_px_minus_start)
                    if f_x < f_item.length_px_minus_start:
                        f_x = f_item.quantize(f_x)
                        f_x -= f_item.quantize_offset
                    f_item.length_handle.setPos(
                        f_x - AUDIO_ITEM_HANDLE_SIZE,
                        AUDIO_ITEM_HEIGHT - AUDIO_ITEM_HANDLE_HEIGHT)
        elif self.is_start_resizing:
            for f_item in AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    f_x = f_item.width_orig + f_event_diff + \
                        f_item.quantize_offset
                    f_x = pydaw_clip_value(
                        f_x, f_item.sample_start_offset_px,
                        f_item.length_handle.pos().x())
                    f_x = pydaw_clip_min(f_x, f_item.min_start)
                    if f_x > f_item.min_start:
                        f_x = f_item.quantize_start(f_x)
                        f_x -= f_item.quantize_offset
                    f_item.start_handle.setPos(
                        f_x, AUDIO_ITEM_HEIGHT - AUDIO_ITEM_HANDLE_HEIGHT)
        elif self.is_fading_in:
            for f_item in AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    #f_x = f_event_pos #f_item.width_orig + f_event_diff
                    f_x = f_item.fade_orig_pos + f_event_diff
                    f_x = pydaw_clip_value(
                        f_x, 0.0, f_item.fade_out_handle.pos().x() - 4.0)
                    f_item.fade_in_handle.setPos(f_x, 0.0)
                    f_item.update_fade_in_line()
        elif self.is_fading_out:
            for f_item in AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    f_x = f_item.fade_orig_pos + f_event_diff
                    f_x = pydaw_clip_value(
                        f_x, f_item.fade_in_handle.pos().x() + 4.0,
                        f_item.width_orig - AUDIO_ITEM_HANDLE_SIZE)
                    f_item.fade_out_handle.setPos(f_x, 0.0)
                    f_item.update_fade_out_line()
        elif self.is_stretching:
            for f_item in AUDIO_SEQ.audio_items:
                if f_item.isSelected() and \
                f_item.audio_item.time_stretch_mode >= 2:
                    f_x = f_item.width_orig + f_event_diff + \
                        f_item.quantize_offset
                    f_x = pydaw_clip_value(
                        f_x, f_item.stretch_width_default * 0.1,
                        f_item.stretch_width_default * 200.0)
                    f_x = pydaw_clip_max(f_x, f_item.max_stretch)
                    f_x = f_item.quantize(f_x)
                    f_x -= f_item.quantize_offset
                    f_item.stretch_handle.setPos(
                        f_x - AUDIO_ITEM_HANDLE_SIZE,
                        (AUDIO_ITEM_HEIGHT * 0.5) -
                        (AUDIO_ITEM_HANDLE_HEIGHT * 0.5))
        elif self.is_amp_dragging:
            for f_item in AUDIO_SEQ.get_selected():
                f_new_vel = pydaw_util.pydaw_clip_value(
                    f_val + f_item.orig_value, -24.0, 24.0)
                f_new_vel = round(f_new_vel, 1)
                f_item.audio_item.vol = f_new_vel
                f_item.set_vol_line()
        elif self.is_amp_curving:
            AUDIO_SEQ.setUpdatesEnabled(False)
            for f_item in AUDIO_SEQ.get_selected():
                f_start = ((f_item.audio_item.start_bar * 4.0) +
                    f_item.audio_item.start_beat)
                if f_start == self.vc_mid:
                    f_new_vel = f_val + f_item.orig_value
                else:
                    if f_start > self.vc_mid:
                        f_frac =  (f_start -
                            self.vc_mid) / (self.vc_end - self.vc_mid)
                        f_new_vel = pydaw_util.linear_interpolate(
                            f_val, 0.3 * f_val, f_frac)
                    else:
                        f_frac = (f_start -
                            self.vc_start) / (self.vc_mid - self.vc_start)
                        f_new_vel = pydaw_util.linear_interpolate(
                            0.3 * f_val, f_val, f_frac)
                    f_new_vel += f_item.orig_value
                f_new_vel = pydaw_util.pydaw_clip_value(f_new_vel, -24.0, 24.0)
                f_new_vel = round(f_new_vel, 1)
                f_item.audio_item.vol = f_new_vel
                f_item.set_vol_line()
            AUDIO_SEQ.setUpdatesEnabled(True)
            AUDIO_SEQ.update()
        else:
            QtGui.QGraphicsRectItem.mouseMoveEvent(self, a_event)
            if AUDIO_QUANTIZE:
                f_max_x = (pydaw_get_current_region_length() *
                    AUDIO_PX_PER_BAR) - AUDIO_QUANTIZE_PX
            else:
                f_max_x = (pydaw_get_current_region_length() *
                    AUDIO_PX_PER_BAR) - AUDIO_ITEM_HANDLE_SIZE
            for f_item in AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    f_pos_x = f_item.pos().x()
                    f_pos_y = f_item.pos().y()
                    f_pos_x = pydaw_clip_value(f_pos_x, 0.0, f_max_x)
                    f_ignored, f_pos_y = f_item.y_pos_to_lane_number(f_pos_y)
                    f_pos_x = f_item.quantize_scene(f_pos_x)
                    f_item.setPos(f_pos_x, f_pos_y)
                    if not f_item.is_moving:
                        f_item.setGraphicsEffect(
                            QtGui.QGraphicsOpacityEffect())
                        f_item.is_moving = True

    def mouseReleaseEvent(self, a_event):
        if libmk.IS_PLAYING or self.event_pos_orig is None:
            return
        QtGui.QGraphicsRectItem.mouseReleaseEvent(self, a_event)
        QtGui.QApplication.restoreOverrideCursor()
        f_audio_items =  AUDIO_ITEMS
        #Set to True when testing, set to False for better UI performance...
        f_reset_selection = True
        f_did_change = False
        f_was_stretching = False
        f_stretched_items = []
        f_event_pos = a_event.pos().x()
        f_event_diff = f_event_pos - self.event_pos_orig
        if self.is_copying:
            f_was_copying = True
            f_per_item_fx_dict = \
            PROJECT.get_audio_per_item_fx_region(
                CURRENT_REGION.uid)
        else:
            f_was_copying = False
        for f_audio_item in AUDIO_SEQ.get_selected():
            f_item = f_audio_item.audio_item
            f_pos_x = f_audio_item.pos().x()
            if f_audio_item.is_resizing:
                f_x = f_audio_item.width_orig + f_event_diff + \
                    f_audio_item.quantize_offset
                f_x = pydaw_clip_value(f_x, AUDIO_ITEM_HANDLE_SIZE,
                                       f_audio_item.length_px_minus_start)
                f_x = f_audio_item.quantize(f_x)
                f_x -= f_audio_item.quantize_offset
                f_audio_item.setRect(0.0, 0.0, f_x, AUDIO_ITEM_HEIGHT)
                f_item.sample_end = ((f_audio_item.rect().width() +
                f_audio_item.length_px_start) /
                f_audio_item.length_seconds_orig_px) * 1000.0
                f_item.sample_end = pydaw_util.pydaw_clip_value(
                    f_item.sample_end, 1.0, 1000.0, True)
            elif f_audio_item.is_start_resizing:
                f_x = f_audio_item.start_handle.scenePos().x()
                f_x = pydaw_clip_min(f_x, 0.0)
                f_x = self.quantize_all(f_x)
                if f_x < f_audio_item.sample_start_offset_px:
                    f_x = f_audio_item.sample_start_offset_px
                f_start_result = self.pos_to_musical_time(f_x)
                f_item.start_bar = f_start_result[0]
                f_item.start_beat = f_start_result[1]
                f_item.sample_start = ((f_x -
                    f_audio_item.start_handle_scene_min) /
                    (f_audio_item.start_handle_scene_max -
                    f_audio_item.start_handle_scene_min)) * 1000.0
                f_item.sample_start = pydaw_clip_value(
                    f_item.sample_start, 0.0, 999.0, True)
            elif f_audio_item.is_fading_in:
                f_pos = f_audio_item.fade_in_handle.pos().x()
                f_val = (f_pos / f_audio_item.rect().width()) * 1000.0
                f_item.fade_in = pydaw_clip_value(f_val, 0.0, 997.0, True)
            elif f_audio_item.is_fading_out:
                f_pos = f_audio_item.fade_out_handle.pos().x()
                f_val = ((f_pos + AUDIO_ITEM_HANDLE_SIZE) /
                    (f_audio_item.rect().width())) * 1000.0
                f_item.fade_out = pydaw_clip_value(f_val, 1.0, 998.0, True)
            elif f_audio_item.is_stretching and f_item.time_stretch_mode >= 2:
                f_reset_selection = True
                f_x = f_audio_item.width_orig + f_event_diff + \
                    f_audio_item.quantize_offset
                f_x = pydaw_clip_value(
                    f_x, f_audio_item.stretch_width_default * 0.1,
                    f_audio_item.stretch_width_default * 200.0)
                f_x = pydaw_clip_max(f_x, f_audio_item.max_stretch)
                f_x = f_audio_item.quantize(f_x)
                f_x -= f_audio_item.quantize_offset
                f_item.timestretch_amt = \
                    f_x / f_audio_item.stretch_width_default
                f_item.timestretch_amt_end = f_item.timestretch_amt
                if f_item.time_stretch_mode >= 3 and \
                f_audio_item.orig_string != str(f_item):
                    f_was_stretching = True
                    f_ts_result = libmk.PROJECT.timestretch_audio_item(f_item)
                    if f_ts_result is not None:
                        f_stretched_items.append(f_ts_result)
                f_audio_item.setRect(0.0, 0.0, f_x, AUDIO_ITEM_HEIGHT)
            elif self.is_amp_curving or self.is_amp_dragging:
                f_did_change = True
            else:
                f_pos_y = f_audio_item.pos().y()
                if f_audio_item.is_copying:
                    f_reset_selection = True
                    f_item_old = f_item.clone()
                    f_index = f_audio_items.get_next_index()
                    if f_index == -1:
                        QtGui.QMessageBox.warning(self, _("Error"),
                        _("No more available audio item slots, max per "
                        "region is {}").format(MAX_AUDIO_ITEM_COUNT))
                        break
                    else:
                        f_audio_items.add_item(f_index, f_item_old)
                        if f_audio_item.per_item_fx is not None:
                            f_per_item_fx_dict.set_row(
                                f_index, f_audio_item.per_item_fx)
                else:
                    f_audio_item.set_brush(f_item.lane_num)
                f_pos_x = self.quantize_all(f_pos_x)
                f_item.lane_num, f_pos_y = self.y_pos_to_lane_number(f_pos_y)
                f_audio_item.setPos(f_pos_x, f_pos_y)
                f_start_result = f_audio_item.pos_to_musical_time(f_pos_x)
                f_item.set_pos(f_start_result[0], f_start_result[1])
            f_audio_item.clip_at_region_end()
            f_item_str = str(f_item)
            if f_item_str != f_audio_item.orig_string:
                f_audio_item.orig_string = f_item_str
                f_did_change = True
                if not f_reset_selection:
                    f_audio_item.draw()
            f_audio_item.is_moving = False
            f_audio_item.is_resizing = False
            f_audio_item.is_start_resizing = False
            f_audio_item.is_copying = False
            f_audio_item.is_fading_in = False
            f_audio_item.is_fading_out = False
            f_audio_item.is_stretching = False
            f_audio_item.setGraphicsEffect(None)
            f_audio_item.setFlag(QtGui.QGraphicsItem.ItemClipsChildrenToShape)
        if f_did_change:
            f_audio_items.deduplicate_items()
            if f_was_copying:
                PROJECT.save_audio_per_item_fx_region(
                    CURRENT_REGION.uid, f_per_item_fx_dict, False)
                PROJECT.en_osc.pydaw_audio_per_item_fx_region(
                    CURRENT_REGION.uid)
            if f_was_stretching:
                libmk.PROJECT.save_stretch_dicts()
                for f_stretch_item in f_stretched_items:
                    f_stretch_item[2].wait()
                    libmk.PROJECT.get_wav_uid_by_name(
                        f_stretch_item[0], a_uid=f_stretch_item[1])
                for f_audio_item in AUDIO_SEQ.get_selected():
                    f_new_graph = libmk.PROJECT.get_sample_graph_by_uid(
                        f_audio_item.audio_item.uid)
                    f_audio_item.audio_item.clip_at_region_end(
                        pydaw_get_current_region_length(),
                        TRANSPORT.tempo_spinbox.value(),
                        f_new_graph.length_in_seconds)
            PROJECT.save_audio_region(
                CURRENT_REGION.uid, f_audio_items)
            PROJECT.commit(_("Update audio items"))
        global_open_audio_items(f_reset_selection)

AUDIO_ITEMS_HEADER_GRADIENT = QtGui.QLinearGradient(
    0.0, 0.0, 0.0, AUDIO_RULER_HEIGHT)
AUDIO_ITEMS_HEADER_GRADIENT.setColorAt(0.0, QtGui.QColor.fromRgb(61, 61, 61))
AUDIO_ITEMS_HEADER_GRADIENT.setColorAt(0.5, QtGui.QColor.fromRgb(50,50, 50))
AUDIO_ITEMS_HEADER_GRADIENT.setColorAt(0.6, QtGui.QColor.fromRgb(43, 43, 43))
AUDIO_ITEMS_HEADER_GRADIENT.setColorAt(1.0, QtGui.QColor.fromRgb(65, 65, 65))

DEFAULT_AUDIO_TRACK = 0

class audio_items_viewer(QtGui.QGraphicsView):
    def __init__(self):
        QtGui.QGraphicsView.__init__(self)
        self.reset_line_lists()
        self.h_zoom = 1.0
        self.v_zoom = 1.0
        self.scene = QtGui.QGraphicsScene(self)
        self.scene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
        self.scene.dropEvent = self.sceneDropEvent
        self.scene.dragEnterEvent = self.sceneDragEnterEvent
        self.scene.dragMoveEvent = self.sceneDragMoveEvent
        self.scene.contextMenuEvent = self.sceneContextMenuEvent
        self.scene.setBackgroundBrush(QtGui.QColor(90, 90, 90))
        self.scene.selectionChanged.connect(self.scene_selection_changed)
        self.setAcceptDrops(True)
        self.setScene(self.scene)
        self.audio_items = []
        self.track = 0
        self.gradient_index = 0
        self.playback_px = 0.0
        self.draw_headers(0)
        self.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
        self.is_playing = False
        self.reselect_on_stop = []
        self.playback_cursor = None
        #Somewhat slow on my AMD 5450 using the FOSS driver
        #self.setRenderHint(QtGui.QPainter.Antialiasing)

    def reset_line_lists(self):
        self.text_list = []
        self.beat_line_list = []

    def prepare_to_quit(self):
        self.scene.clearSelection()
        self.scene.clear()

    def keyPressEvent(self, a_event):
        #Done this way to prevent the region editor from grabbing the key
        if a_event.key() == QtCore.Qt.Key_Delete:
            self.delete_selected()
        else:
            QtGui.QGraphicsView.keyPressEvent(self, a_event)
        QtGui.QApplication.restoreOverrideCursor()

    def scrollContentsBy(self, x, y):
        QtGui.QGraphicsView.scrollContentsBy(self, x, y)
        self.set_ruler_y_pos()

    def set_ruler_y_pos(self):
        f_point = self.get_scene_pos()
        self.ruler.setPos(0.0, f_point.y())

    def get_scene_pos(self):
        return QtCore.QPointF(
            self.horizontalScrollBar().value(),
            self.verticalScrollBar().value())

    def get_selected(self):
        return [x for x in self.audio_items if x.isSelected()]

    def delete_selected(self):
        if pydaw_current_region_is_none() or self.check_running():
            return
        f_items = PROJECT.get_audio_region(
            CURRENT_REGION.uid)
        f_paif = PROJECT.get_audio_per_item_fx_region(
            CURRENT_REGION.uid)
        for f_item in self.get_selected():
            f_items.remove_item(f_item.track_num)
            f_paif.clear_row_if_exists(f_item.track_num)
        PROJECT.save_audio_region(CURRENT_REGION.uid, f_items)
        PROJECT.save_audio_per_item_fx_region(
            CURRENT_REGION.uid, f_paif, False)
        PROJECT.commit(_("Delete audio item(s)"))
        global_open_audio_items(True)

    def crossfade_selected(self):
        f_list = self.get_selected()
        if len(f_list) < 2:
            QtGui.QMessageBox.warning(
                MAIN_WINDOW, _("Error"),
                _("You must have at least 2 items selected to crossfade"))
            return

        f_tempo = float(TRANSPORT.tempo_spinbox.value())
        f_changed = False

        for f_item in f_list:
            f_start_sec = pydaw_util.musical_time_to_seconds(
                f_tempo, f_item.audio_item.start_bar,
                f_item.audio_item.start_beat)
            f_time_frac = f_item.audio_item.sample_end - \
                f_item.audio_item.sample_start
            f_time_frac *= 0.001
            f_time = f_item.graph_object.length_in_seconds * f_time_frac
            f_end_sec = f_start_sec + f_time
            f_list2 = [x for x in f_list if x.audio_item != f_item.audio_item]

            for f_item2 in f_list2:
                f_start_sec2 = pydaw_util.musical_time_to_seconds(
                    f_tempo, f_item2.audio_item.start_bar,
                    f_item2.audio_item.start_beat)
                f_time_frac2 = f_item2.audio_item.sample_end - \
                    f_item2.audio_item.sample_start
                f_time_frac2 *= 0.001
                f_time2 = f_item2.graph_object.length_in_seconds * f_time_frac2
                f_end_sec2 = f_start_sec2 + f_time2

                if f_start_sec > f_start_sec2 and \
                f_end_sec > f_end_sec2 and \
                f_end_sec2 > f_start_sec:  # item1 is after item2
                    f_changed = True
                    f_diff_sec = f_end_sec2 - f_start_sec
                    f_val = (f_diff_sec / f_time) * 1000.0
                    f_item.audio_item.set_fade_in(f_val)
                elif f_start_sec < f_start_sec2 and \
                f_end_sec < f_end_sec2 and \
                f_end_sec > f_start_sec2: # item1 is before item2
                    f_changed = True
                    f_diff_sec = f_start_sec2 - f_start_sec
                    f_val = (f_diff_sec / f_time) * 1000.0
                    f_item.audio_item.set_fade_out(f_val)

        if f_changed:
            PROJECT.save_audio_region(CURRENT_REGION.uid, AUDIO_ITEMS)
            PROJECT.commit(_("Crossfade audio items"))
            global_open_audio_items(True)


    def set_tooltips(self, a_on):
        if a_on:
            self.setToolTip(libpydaw.strings.audio_items_viewer)
        else:
            self.setToolTip("")
        for f_item in self.audio_items:
            f_item.set_tooltips(a_on)

    def resizeEvent(self, a_event):
        QtGui.QGraphicsView.resizeEvent(self, a_event)
        pydaw_set_audio_seq_zoom(self.h_zoom, self.v_zoom)
        global_open_audio_items(a_reload=False)

    def sceneContextMenuEvent(self, a_event):
        if self.check_running():
            return
        QtGui.QGraphicsScene.contextMenuEvent(self.scene, a_event)
        self.context_menu_pos = a_event.scenePos()
        f_menu = QtGui.QMenu(MAIN_WINDOW)
        f_paste_action = QtGui.QAction(
            _("Paste file path from clipboard"), self)
        f_paste_action.triggered.connect(self.on_scene_paste_paths)
        f_menu.addAction(f_paste_action)
        f_menu.exec_(a_event.screenPos())

    def on_scene_paste_paths(self):
        f_path = global_get_audio_file_from_clipboard()
        if f_path:
            self.add_items(
                self.context_menu_pos.x(), self.context_menu_pos.y(),
                [f_path])

    def scene_selection_changed(self):
        f_selected_items = []
        global CURRENT_AUDIO_ITEM_INDEX
        for f_item in self.audio_items:
            f_item.set_brush()
            if f_item.isSelected():
                f_selected_items.append(f_item)
        if len(f_selected_items) == 1:
            CURRENT_AUDIO_ITEM_INDEX = f_selected_items[0].track_num
            AUDIO_SEQ_WIDGET.modulex.widget.setEnabled(True)
            f_paif = PROJECT.get_audio_per_item_fx_region(CURRENT_REGION.uid)
            AUDIO_SEQ_WIDGET.modulex.set_from_list(
                f_paif.get_row(CURRENT_AUDIO_ITEM_INDEX))
        elif len(f_selected_items) == 0:
            CURRENT_AUDIO_ITEM_INDEX = None
            AUDIO_SEQ_WIDGET.modulex.widget.setDisabled(True)
        else:
            AUDIO_SEQ_WIDGET.modulex.widget.setDisabled(True)

    def sceneDragEnterEvent(self, a_event):
        a_event.setAccepted(True)

    def sceneDragMoveEvent(self, a_event):
        a_event.setDropAction(QtCore.Qt.CopyAction)

    def check_running(self):
        if pydaw_current_region_is_none() or libmk.IS_PLAYING:
            return True
        return False

    def sceneDropEvent(self, a_event):
        if AUDIO_ITEMS_TO_DROP:
            f_x = a_event.scenePos().x()
            f_y = a_event.scenePos().y()
            self.add_items(f_x, f_y, AUDIO_ITEMS_TO_DROP)

    def add_items(self, f_x, f_y, a_item_list):
        if self.check_running():
            return
        if CURRENT_REGION.region_length_bars == 0:
            f_max_start = 7
        else:
            f_max_start = CURRENT_REGION.region_length_bars - 1

        f_pos_bars = int(f_x / AUDIO_PX_PER_BAR)
        f_pos_bars = pydaw_clip_value(f_pos_bars, 0, f_max_start)

        if f_pos_bars == f_max_start:
            f_beat_frac = 0.0
        else:
            f_beat_frac = ((f_x % AUDIO_PX_PER_BAR) / AUDIO_PX_PER_BAR) * 4.0
            f_beat_frac = pydaw_clip_value(
                f_beat_frac, 0.0, 3.99, a_round=True)
        print("{}".format(f_beat_frac))
        if AUDIO_QUANTIZE:
            f_beat_frac = \
                int(f_beat_frac * AUDIO_QUANTIZE_AMT) / AUDIO_QUANTIZE_AMT

        print("{} {}".format(f_pos_bars, f_beat_frac))

        f_lane_num = int((f_y - AUDIO_RULER_HEIGHT) / AUDIO_ITEM_HEIGHT)
        f_lane_num = pydaw_clip_value(f_lane_num, 0, AUDIO_ITEM_MAX_LANE)

        f_items = PROJECT.get_audio_region(CURRENT_REGION.uid)

        for f_file_name in a_item_list:
            f_file_name_str = str(f_file_name)
            if not f_file_name_str is None and not f_file_name_str == "":
                f_index = f_items.get_next_index()
                if f_index == -1:
                    QtGui.QMessageBox.warning(self, _("Error"),
                    _("No more available audio item slots, "
                    "max per region is {}").format(MAX_AUDIO_ITEM_COUNT))
                    break
                else:
                    f_uid = libmk.PROJECT.get_wav_uid_by_name(f_file_name_str)
                    f_item = pydaw_audio_item(
                        f_uid, a_start_bar=f_pos_bars,
                        a_start_beat=f_beat_frac, a_lane_num=f_lane_num,
                        a_output_track=DEFAULT_AUDIO_TRACK)
                    f_items.add_item(f_index, f_item)
                    f_graph = libmk.PROJECT.get_sample_graph_by_uid(f_uid)
                    f_audio_item = AUDIO_SEQ.draw_item(
                        f_index, f_item, f_graph)
                    f_audio_item.clip_at_region_end()
        PROJECT.save_audio_region(CURRENT_REGION.uid, f_items)
        PROJECT.commit(
            _("Added audio items to region {}").format(CURRENT_REGION.uid))
        global_open_audio_items()
        self.last_open_dir = os.path.dirname(f_file_name_str)

    def glue_selected(self):
        if pydaw_current_region_is_none() or self.check_running():
            return

        f_region_uid = CURRENT_REGION.uid
        f_indexes = []
        f_start_bar = None
        f_end_bar = None
        f_lane = None
        f_audio_track_num = None
        for f_item in self.audio_items:
            if f_item.isSelected():
                f_indexes.append(f_item.track_num)
                if f_start_bar is None or \
                f_start_bar > f_item.audio_item.start_bar:
                    f_start_bar = f_item.audio_item.start_bar
                    f_lane = f_item.audio_item.lane_num
                    f_audio_track_num = f_item.audio_item.output_track
                f_end, f_beat = \
                f_item.pos_to_musical_time(
                    f_item.pos().x() + f_item.rect().width())
                if f_beat > 0.0:
                    f_end += 1
                if f_end_bar is None or f_end_bar < f_end:
                    f_end_bar = f_end
        if len(f_indexes) == 0:
            print(_("No audio items selected, not glueing"))
            return
        f_path = libmk.PROJECT.get_next_glued_file_name()
        PROJECT.en_osc.pydaw_glue_audio(
            f_path, CURRENT_SONG_INDEX, f_start_bar, f_end_bar, f_indexes)
        f_items = PROJECT.get_audio_region(f_region_uid)
        f_paif = PROJECT.get_audio_per_item_fx_region(f_region_uid)
        for f_index in f_indexes:
            f_items.remove_item(f_index)
            f_paif.clear_row_if_exists(f_index)
        f_index = f_items.get_next_index()
        f_uid = libmk.PROJECT.get_wav_uid_by_name(f_path)
        f_item = pydaw_audio_item(
            f_uid, a_start_bar=f_start_bar, a_lane_num=f_lane,
            a_output_track=f_audio_track_num)
        f_items.add_item(f_index, f_item)

        PROJECT.save_audio_region(f_region_uid, f_items)
        PROJECT.save_audio_per_item_fx_region(f_region_uid, f_paif)
        PROJECT.en_osc.pydaw_audio_per_item_fx_region(f_region_uid)
        PROJECT.commit(_("Glued audio items"))
        global_open_audio_items()

    def set_playback_pos(self, a_bar=None, a_beat=0.0):
        if a_bar is None:
            f_bar = TRANSPORT.get_bar_value()
        else:
            f_bar = int(a_bar)
        f_beat = float(a_beat)
        f_pos = (f_bar * AUDIO_PX_PER_BAR) + (f_beat * AUDIO_PX_PER_BEAT)
        self.playback_cursor.setPos(f_pos, 0.0)

    def set_playback_clipboard(self):
        self.reselect_on_stop = []
        for f_item in self.audio_items:
            if f_item.isSelected():
                self.reselect_on_stop.append(str(f_item.audio_item))

    def start_playback(self, a_bpm):
        self.is_playing = True

    def stop_playback(self, a_bar=None):
        if self.is_playing:
            self.is_playing = False
            self.reset_selection()
            self.set_playback_pos(a_bar)

    def reset_selection(self):
        for f_item in self.audio_items:
            if str(f_item.audio_item) in self.reselect_on_stop:
                f_item.setSelected(True)

    def set_zoom(self, a_scale):
        self.h_zoom = a_scale
        self.update_zoom()

    def set_v_zoom(self, a_scale):
        self.v_zoom = a_scale
        self.update_zoom()

    def update_zoom(self):
        pydaw_set_audio_seq_zoom(self.h_zoom, self.v_zoom)

    def ruler_click_event(self, a_event):
        if not libmk.IS_PLAYING:
            f_val = int(a_event.pos().x() / AUDIO_PX_PER_BAR)
            TRANSPORT.set_bar_value(f_val)

    def check_line_count(self):
        """ Check that there are not too many vertical
            lines on the screen
        """
        return

        f_num_count = len(self.text_list)
        if f_num_count == 0:
            return
        f_num_visible_count = int(f_num_count /
            pydaw_clip_min(self.h_zoom, 1))

        if f_num_visible_count > 24:
            for f_line in self.beat_line_list:
                f_line.setVisible(False)
            f_factor = f_num_visible_count // 24
            if f_factor == 1:
                for f_num in self.text_list:
                    f_num.setVisible(True)
            else:
                f_factor = int(round(f_factor / 2.0) * 2)
                for f_num in self.text_list:
                    f_num.setVisible(False)
                for f_num in self.text_list[::f_factor]:
                    f_num.setVisible(True)
        else:
            for f_line in self.beat_line_list:
                f_line.setVisible(True)
            for f_num in self.text_list:
                f_num.setVisible(True)


    def draw_headers(self, a_cursor_pos=None):
        f_region_length = pydaw_get_current_region_length()
        f_size = AUDIO_PX_PER_BAR * f_region_length
        self.ruler = QtGui.QGraphicsRectItem(0, 0, f_size, AUDIO_RULER_HEIGHT)
        self.ruler.setZValue(1500.0)
        self.ruler.setBrush(AUDIO_ITEMS_HEADER_GRADIENT)
        self.ruler.mousePressEvent = self.ruler_click_event
        self.scene.addItem(self.ruler)
        f_v_pen = QtGui.QPen(QtCore.Qt.black)
        f_beat_pen = QtGui.QPen(QtGui.QColor(210, 210, 210))
        f_16th_pen = QtGui.QPen(QtGui.QColor(120, 120, 120))
        f_reg_pen = QtGui.QPen(QtCore.Qt.white)
        f_total_height = (AUDIO_ITEM_LANE_COUNT *
            (AUDIO_ITEM_HEIGHT)) + AUDIO_RULER_HEIGHT
        self.scene.setSceneRect(0.0, 0.0, f_size, f_total_height)
        self.playback_cursor = self.scene.addLine(
            0.0, 0.0, 0.0, f_total_height, QtGui.QPen(QtCore.Qt.red, 2.0))
        self.playback_cursor.setZValue(1000.0)
        i3 = 0.0
        for i in range(f_region_length):
            f_number = QtGui.QGraphicsSimpleTextItem(
                "{}".format(i + 1), self.ruler)
            f_number.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations)
            f_number.setBrush(QtCore.Qt.white)
            f_number.setZValue(1000.0)
            self.text_list.append(f_number)
            self.scene.addLine(i3, 0.0, i3, f_total_height, f_v_pen)
            f_number.setPos(i3 + 3.0, 2)
            if AUDIO_LINES_ENABLED:
                for f_i4 in range(1, AUDIO_SNAP_RANGE):
                    f_sub_x = i3 + (AUDIO_QUANTIZE_PX * f_i4)
                    f_line = self.scene.addLine(
                        f_sub_x, AUDIO_RULER_HEIGHT,
                        f_sub_x, f_total_height, f_16th_pen)
                    self.beat_line_list.append(f_line)
            for f_beat_i in range(1, 4):
                f_beat_x = i3 + (AUDIO_PX_PER_BEAT * f_beat_i)
                f_line = self.scene.addLine(
                    f_beat_x, 0.0, f_beat_x, f_total_height, f_beat_pen)
                self.beat_line_list.append(f_line)
                if AUDIO_LINES_ENABLED:
                    for f_i4 in range(1, AUDIO_SNAP_RANGE):
                        f_sub_x = f_beat_x + (AUDIO_QUANTIZE_PX * f_i4)
                        f_line = self.scene.addLine(
                            f_sub_x, AUDIO_RULER_HEIGHT,
                            f_sub_x, f_total_height, f_16th_pen)
                        self.beat_line_list.append(f_line)
            i3 += AUDIO_PX_PER_BAR
        self.scene.addLine(
            i3, AUDIO_RULER_HEIGHT, i3, f_total_height, f_reg_pen)
        for i2 in range(AUDIO_ITEM_LANE_COUNT):
            f_y = ((AUDIO_ITEM_HEIGHT) * (i2 + 1)) + AUDIO_RULER_HEIGHT
            self.scene.addLine(0, f_y, f_size, f_y)
        self.set_playback_pos(a_cursor_pos)
        self.check_line_count()
        self.set_ruler_y_pos()

    def clear_drawn_items(self):
        if self.is_playing:
            f_was_playing = True
            self.is_playing = False
        else:
            f_was_playing = False
        self.reset_line_lists()
        self.audio_items = []
        self.scene.clear()
        self.draw_headers()
        if f_was_playing:
            self.is_playing = True

    def draw_item(self, a_audio_item_index, a_audio_item, a_graph):
        """a_start in seconds, a_length in seconds"""
        f_audio_item = audio_viewer_item(
            a_audio_item_index, a_audio_item, a_graph)
        self.audio_items.append(f_audio_item)
        self.scene.addItem(f_audio_item)
        return f_audio_item


class time_pitch_dialog_widget:
    def __init__(self, a_audio_item):
        self.widget = QtGui.QDialog()
        self.widget.setWindowTitle(_("Time/Pitch..."))
        self.widget.setMaximumWidth(480)
        self.main_vlayout = QtGui.QVBoxLayout(self.widget)

        self.layout = QtGui.QGridLayout()
        self.main_vlayout.addLayout(self.layout)

        self.vlayout2 = QtGui.QVBoxLayout()
        self.layout.addLayout(self.vlayout2, 1, 1)
        self.start_hlayout = QtGui.QHBoxLayout()
        self.vlayout2.addLayout(self.start_hlayout)

        self.timestretch_hlayout = QtGui.QHBoxLayout()
        self.time_pitch_gridlayout = QtGui.QGridLayout()
        self.vlayout2.addLayout(self.timestretch_hlayout)
        self.vlayout2.addLayout(self.time_pitch_gridlayout)
        self.timestretch_hlayout.addWidget(QtGui.QLabel(_("Mode:")))
        self.timestretch_mode = QtGui.QComboBox()

        self.timestretch_mode.setMinimumWidth(240)
        self.timestretch_hlayout.addWidget(self.timestretch_mode)
        self.timestretch_mode.addItems(TIMESTRETCH_MODES)
        self.timestretch_mode.setCurrentIndex(a_audio_item.time_stretch_mode)
        self.timestretch_mode.currentIndexChanged.connect(
            self.timestretch_mode_changed)
        self.time_pitch_gridlayout.addWidget(QtGui.QLabel(_("Pitch:")), 0, 0)
        self.pitch_shift = QtGui.QDoubleSpinBox()
        self.pitch_shift.setRange(-36, 36)
        self.pitch_shift.setValue(a_audio_item.pitch_shift)
        self.pitch_shift.setDecimals(6)
        self.time_pitch_gridlayout.addWidget(self.pitch_shift, 0, 1)

        self.pitch_shift_end_checkbox = QtGui.QCheckBox(_("End:"))
        self.pitch_shift_end_checkbox.setChecked(
            a_audio_item.pitch_shift != a_audio_item.pitch_shift_end)
        self.pitch_shift_end_checkbox.toggled.connect(
            self.pitch_end_mode_changed)
        self.time_pitch_gridlayout.addWidget(
            self.pitch_shift_end_checkbox, 0, 2)
        self.pitch_shift_end = QtGui.QDoubleSpinBox()
        self.pitch_shift_end.setRange(-36, 36)
        self.pitch_shift_end.setValue(a_audio_item.pitch_shift_end)
        self.pitch_shift_end.setDecimals(6)
        self.time_pitch_gridlayout.addWidget(self.pitch_shift_end, 0, 3)

        self.time_pitch_gridlayout.addWidget(QtGui.QLabel(_("Time:")), 1, 0)
        self.timestretch_amt = QtGui.QDoubleSpinBox()
        self.timestretch_amt.setRange(0.1, 200.0)
        self.timestretch_amt.setDecimals(6)
        self.timestretch_amt.setSingleStep(0.1)
        self.timestretch_amt.setValue(a_audio_item.timestretch_amt)
        self.time_pitch_gridlayout.addWidget(self.timestretch_amt, 1, 1)

        self.crispness_layout = QtGui.QHBoxLayout()
        self.vlayout2.addLayout(self.crispness_layout)
        self.crispness_layout.addWidget(QtGui.QLabel(_("Crispness")))
        self.crispness_combobox = QtGui.QComboBox()
        self.crispness_combobox.addItems(CRISPNESS_SETTINGS)
        self.crispness_combobox.setCurrentIndex(a_audio_item.crispness)
        self.crispness_layout.addWidget(self.crispness_combobox)

        self.timestretch_amt_end_checkbox = QtGui.QCheckBox(_("End:"))
        self.timestretch_amt_end_checkbox.toggled.connect(
            self.timestretch_end_mode_changed)
        self.time_pitch_gridlayout.addWidget(
            self.timestretch_amt_end_checkbox, 1, 2)
        self.timestretch_amt_end = QtGui.QDoubleSpinBox()
        self.timestretch_amt_end.setRange(0.2, 4.0)
        self.timestretch_amt_end.setDecimals(6)
        self.timestretch_amt_end.setSingleStep(0.1)
        self.timestretch_amt_end.setValue(a_audio_item.timestretch_amt_end)
        self.time_pitch_gridlayout.addWidget(self.timestretch_amt_end, 1, 3)

        self.timestretch_mode_changed(0)

        self.timestretch_mode.currentIndexChanged.connect(
            self.timestretch_changed)
        self.pitch_shift.valueChanged.connect(self.timestretch_changed)
        self.pitch_shift_end.valueChanged.connect(self.timestretch_changed)
        self.timestretch_amt.valueChanged.connect(self.timestretch_changed)
        self.timestretch_amt_end.valueChanged.connect(self.timestretch_changed)
        self.crispness_combobox.currentIndexChanged.connect(
            self.timestretch_changed)

        self.ok_layout = QtGui.QHBoxLayout()
        self.ok = QtGui.QPushButton(_("OK"))
        self.ok.pressed.connect(self.ok_handler)
        self.ok_layout.addWidget(self.ok)
        self.cancel = QtGui.QPushButton(_("Cancel"))
        self.cancel.pressed.connect(self.widget.close)
        self.ok_layout.addWidget(self.cancel)
        self.vlayout2.addLayout(self.ok_layout)

        self.last_open_dir = global_home

    def timestretch_end_mode_changed(self, a_val=None):
        if not self.timestretch_amt_end_checkbox.isChecked():
            self.timestretch_amt_end.setValue(self.timestretch_amt.value())

    def pitch_end_mode_changed(self, a_val=None):
        if not self.pitch_shift_end_checkbox.isChecked():
            self.pitch_shift_end.setValue(self.pitch_shift.value())

    def end_mode_changed(self, a_val=None):
        self.end_mode_checkbox.setChecked(True)

    def timestretch_changed(self, a_val=None):
        if not self.pitch_shift_end_checkbox.isChecked():
            self.pitch_shift_end.setValue(self.pitch_shift.value())
        if not self.timestretch_amt_end_checkbox.isChecked():
            self.timestretch_amt_end.setValue(self.timestretch_amt.value())

    def timestretch_mode_changed(self, a_val=None):
        if a_val == 0:
            self.pitch_shift.setEnabled(False)
            self.timestretch_amt.setEnabled(False)
            self.pitch_shift.setValue(0.0)
            self.pitch_shift_end.setValue(0.0)
            self.timestretch_amt.setValue(1.0)
            self.timestretch_amt_end.setValue(1.0)
            self.timestretch_amt_end_checkbox.setEnabled(False)
            self.timestretch_amt_end_checkbox.setChecked(False)
            self.pitch_shift_end_checkbox.setEnabled(False)
            self.pitch_shift_end_checkbox.setChecked(False)
            self.crispness_combobox.setCurrentIndex(5)
            self.crispness_combobox.setEnabled(False)
        elif a_val == 1:
            self.pitch_shift.setEnabled(True)
            self.timestretch_amt.setEnabled(False)
            self.timestretch_amt.setValue(1.0)
            self.timestretch_amt_end.setValue(1.0)
            self.timestretch_amt_end.setEnabled(False)
            self.timestretch_amt_end_checkbox.setEnabled(False)
            self.timestretch_amt_end_checkbox.setChecked(False)
            self.pitch_shift_end_checkbox.setEnabled(True)
            self.pitch_shift_end.setEnabled(True)
            self.crispness_combobox.setCurrentIndex(5)
            self.crispness_combobox.setEnabled(False)
        elif a_val == 2:
            self.pitch_shift.setEnabled(False)
            self.timestretch_amt.setEnabled(True)
            self.pitch_shift.setValue(0.0)
            self.pitch_shift_end.setValue(0.0)
            self.pitch_shift_end.setEnabled(False)
            self.timestretch_amt_end.setEnabled(True)
            self.timestretch_amt_end_checkbox.setEnabled(True)
            self.pitch_shift_end_checkbox.setEnabled(False)
            self.pitch_shift_end_checkbox.setChecked(False)
            self.crispness_combobox.setCurrentIndex(5)
            self.crispness_combobox.setEnabled(False)
        elif a_val == 3 or a_val == 4:
            self.pitch_shift.setEnabled(True)
            self.pitch_shift_end.setEnabled(False)
            self.timestretch_amt.setEnabled(True)
            self.timestretch_amt_end_checkbox.setEnabled(False)
            self.timestretch_amt_end_checkbox.setChecked(False)
            self.pitch_shift_end_checkbox.setEnabled(False)
            self.pitch_shift_end_checkbox.setChecked(False)
            self.crispness_combobox.setEnabled(True)
        elif a_val == 5:
            self.pitch_shift.setEnabled(True)
            self.pitch_shift_end.setEnabled(True)
            self.timestretch_amt.setEnabled(True)
            self.timestretch_amt_end.setEnabled(True)
            self.timestretch_amt_end_checkbox.setEnabled(True)
            self.pitch_shift_end_checkbox.setEnabled(True)
            self.crispness_combobox.setCurrentIndex(5)
            self.crispness_combobox.setEnabled(False)
        elif a_val == 6:
            self.pitch_shift.setEnabled(True)
            self.timestretch_amt.setEnabled(True)
            self.timestretch_amt_end.setEnabled(False)
            self.pitch_shift_end.setEnabled(False)
            self.timestretch_amt_end_checkbox.setEnabled(False)
            self.timestretch_amt_end_checkbox.setChecked(False)
            self.pitch_shift_end_checkbox.setEnabled(False)
            self.pitch_shift_end_checkbox.setChecked(False)
            self.crispness_combobox.setCurrentIndex(5)
            self.crispness_combobox.setEnabled(False)


    def ok_handler(self):
        if libmk.IS_PLAYING:
            QtGui.QMessageBox.warning(
                self.widget, _("Error"),
                _("Cannot edit audio items during playback"))
            return

        self.end_mode = 0

        f_selected_count = 0

        f_region_length = CURRENT_REGION.region_length_bars
        if f_region_length == 0:
            f_region_length = 8
        f_region_length -= 1

        f_was_stretching = False
        f_stretched_items = []

        for f_item in AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_new_ts_mode = self.timestretch_mode.currentIndex()
                f_new_ts = round(self.timestretch_amt.value(), 6)
                f_new_ps = round(self.pitch_shift.value(), 6)
                if self.timestretch_amt_end_checkbox.isChecked():
                    f_new_ts_end = round(
                        self.timestretch_amt_end.value(), 6)
                else:
                    f_new_ts_end = f_new_ts
                if self.pitch_shift_end_checkbox.isChecked():
                    f_new_ps_end = round(self.pitch_shift_end.value(), 6)
                else:
                    f_new_ps_end = f_new_ps
                f_item.audio_item.crispness = \
                    self.crispness_combobox.currentIndex()

                if ((f_item.audio_item.time_stretch_mode >= 3) or
                (f_item.audio_item.time_stretch_mode == 1 and \
                (f_item.audio_item.pitch_shift_end !=
                    f_item.audio_item.pitch_shift)) or \
                (f_item.audio_item.time_stretch_mode == 2 and \
                (f_item.audio_item.timestretch_amt_end !=
                    f_item.audio_item.timestretch_amt))) and \
                ((f_new_ts_mode == 0) or \
                (f_new_ts_mode == 1 and f_new_ps == f_new_ps_end) or \
                (f_new_ts_mode == 2 and f_new_ts == f_new_ts_end)):
                    f_item.audio_item.uid = \
                        libmk.PROJECT.timestretch_get_orig_file_uid(
                            f_item.audio_item.uid)

                f_item.audio_item.time_stretch_mode = f_new_ts_mode
                f_item.audio_item.pitch_shift = f_new_ps
                f_item.audio_item.timestretch_amt = f_new_ts
                f_item.audio_item.pitch_shift_end = f_new_ps_end
                f_item.audio_item.timestretch_amt_end = f_new_ts_end
                f_item.draw()
                f_item.clip_at_region_end()
                if (f_new_ts_mode >= 3) or \
                (f_new_ts_mode == 1 and f_new_ps != f_new_ps_end) or \
                (f_new_ts_mode == 2 and f_new_ts != f_new_ts_end) and \
                (f_item.orig_string != str(f_item.audio_item)):
                    f_was_stretching = True
                    f_ts_result = libmk.PROJECT.timestretch_audio_item(
                        f_item.audio_item)
                    if f_ts_result is not None:
                        f_stretched_items.append(
                            (f_ts_result, f_item.audio_item))
                f_item.draw()
                f_selected_count += 1
        if f_selected_count == 0:
            QtGui.QMessageBox.warning(
                self.widget, _("Error"), _("No items selected"))
        else:
            if f_was_stretching:
                f_current_region_length = pydaw_get_current_region_length()
                f_global_tempo = float(TRANSPORT.tempo_spinbox.value())
                libmk.PROJECT.save_stretch_dicts()
                for f_stretch_item, f_audio_item in f_stretched_items:
                    f_stretch_item[2].wait()
                    f_new_uid = libmk.PROJECT.get_wav_uid_by_name(
                        f_stretch_item[0], a_uid=f_stretch_item[1])
                    f_graph = libmk.PROJECT.get_sample_graph_by_uid(f_new_uid)
                    f_audio_item.clip_at_region_end(
                        f_current_region_length, f_global_tempo,
                        f_graph.length_in_seconds)
            PROJECT.save_audio_region(CURRENT_REGION.uid, AUDIO_ITEMS)
            global_open_audio_items(True)
            PROJECT.commit(_("Update audio items"))
        self.widget.close()


class fade_vol_dialog_widget:
    def __init__(self, a_audio_item):
        self.widget = QtGui.QDialog()
        self.widget.setWindowTitle(_("Fade Volume..."))
        self.widget.setMaximumWidth(480)
        self.main_vlayout = QtGui.QVBoxLayout(self.widget)

        self.layout = QtGui.QGridLayout()
        self.main_vlayout.addLayout(self.layout)

        self.fadein_vol_layout = QtGui.QHBoxLayout()
        self.fadein_vol_checkbox = QtGui.QCheckBox(_("Fade-In:"))
        self.fadein_vol_layout.addWidget(self.fadein_vol_checkbox)
        self.fadein_vol_spinbox = QtGui.QSpinBox()
        self.fadein_vol_spinbox.setRange(-50, -6)
        self.fadein_vol_spinbox.setValue(a_audio_item.fadein_vol)
        self.fadein_vol_spinbox.valueChanged.connect(self.fadein_vol_changed)
        self.fadein_vol_layout.addWidget(self.fadein_vol_spinbox)
        self.fadein_vol_layout.addItem(
            QtGui.QSpacerItem(5, 5, QtGui.QSizePolicy.Expanding))
        self.main_vlayout.addLayout(self.fadein_vol_layout)

        self.fadeout_vol_checkbox = QtGui.QCheckBox(_("Fade-Out:"))
        self.fadein_vol_layout.addWidget(self.fadeout_vol_checkbox)
        self.fadeout_vol_spinbox = QtGui.QSpinBox()
        self.fadeout_vol_spinbox.setRange(-50, -6)
        self.fadeout_vol_spinbox.setValue(a_audio_item.fadeout_vol)
        self.fadeout_vol_spinbox.valueChanged.connect(self.fadeout_vol_changed)
        self.fadein_vol_layout.addWidget(self.fadeout_vol_spinbox)

        self.ok_layout = QtGui.QHBoxLayout()
        self.ok = QtGui.QPushButton(_("OK"))
        self.ok.pressed.connect(self.ok_handler)
        self.ok_layout.addWidget(self.ok)
        self.cancel = QtGui.QPushButton(_("Cancel"))
        self.cancel.pressed.connect(self.widget.close)
        self.ok_layout.addWidget(self.cancel)
        self.main_vlayout.addLayout(self.ok_layout)

        self.last_open_dir = global_home

    def fadein_vol_changed(self, a_val=None):
        self.fadein_vol_checkbox.setChecked(True)

    def fadeout_vol_changed(self, a_val=None):
        self.fadeout_vol_checkbox.setChecked(True)

    def ok_handler(self):
        if libmk.IS_PLAYING:
            QtGui.QMessageBox.warning(
                self.widget, _("Error"),
                _("Cannot edit audio items during playback"))
            return

        self.end_mode = 0

        f_selected_count = 0

        f_region_length = CURRENT_REGION.region_length_bars
        if f_region_length == 0:
            f_region_length = 8
        f_region_length -= 1

        for f_item in AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                if self.fadein_vol_checkbox.isChecked():
                    f_item.audio_item.fadein_vol = \
                        self.fadein_vol_spinbox.value()
                if self.fadeout_vol_checkbox.isChecked():
                    f_item.audio_item.fadeout_vol = \
                        self.fadeout_vol_spinbox.value()
                f_item.draw()
                f_selected_count += 1
        if f_selected_count == 0:
            QtGui.QMessageBox.warning(
                self.widget, _("Error"), _("No items selected"))
        else:
            PROJECT.save_audio_region(CURRENT_REGION.uid, AUDIO_ITEMS)
            global_open_audio_items(True)
            PROJECT.commit(_("Update audio items"))
        self.widget.close()


AUDIO_ITEMS_TO_DROP = []

CURRENT_AUDIO_ITEM_INDEX = None

def global_paif_val_callback(a_port, a_val):
    if CURRENT_REGION is not None and \
    CURRENT_AUDIO_ITEM_INDEX is not None:
        PROJECT.en_osc.pydaw_audio_per_item_fx(
            CURRENT_REGION.uid, CURRENT_AUDIO_ITEM_INDEX, a_port, a_val)

def global_paif_rel_callback(a_port, a_val):
    if CURRENT_REGION is not None and \
    CURRENT_AUDIO_ITEM_INDEX is not None:
        f_paif = PROJECT.get_audio_per_item_fx_region(CURRENT_REGION.uid)
        f_index_list = AUDIO_SEQ_WIDGET.modulex.get_list()
        f_paif.set_row(CURRENT_AUDIO_ITEM_INDEX, f_index_list)
        PROJECT.save_audio_per_item_fx_region(CURRENT_REGION.uid, f_paif)

class audio_items_viewer_widget(
pydaw_widgets.pydaw_abstract_file_browser_widget):
    def __init__(self):
        pydaw_widgets.pydaw_abstract_file_browser_widget.__init__(self)

        self.list_file.setDragEnabled(True)
        self.list_file.mousePressEvent = self.file_mouse_press_event
        self.preview_button.pressed.connect(self.on_preview)
        self.stop_preview_button.pressed.connect(self.on_stop_preview)

        self.modulex = pydaw_widgets.pydaw_per_audio_item_fx_widget(
            global_paif_rel_callback, global_paif_val_callback)

        self.modulex_widget = QtGui.QWidget()
        self.modulex_widget.setObjectName("plugin_ui")
        self.modulex_vlayout = QtGui.QVBoxLayout(self.modulex_widget)
        self.folders_tab_widget.addTab(self.modulex_widget, _("Per-Item FX"))
        self.modulex.widget.setDisabled(True)
        self.modulex_vlayout.addWidget(self.modulex.scroll_area)

        self.widget = QtGui.QWidget()
        self.hsplitter.addWidget(self.widget)
        self.vlayout = QtGui.QVBoxLayout()
        self.widget.setLayout(self.vlayout)
        self.controls_grid_layout = QtGui.QGridLayout()
        self.controls_grid_layout.addItem(
            QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Expanding), 0, 30)
        self.vlayout.addLayout(self.controls_grid_layout)
        self.vlayout.addWidget(AUDIO_SEQ)
        self.snap_combobox = QtGui.QComboBox()
        self.snap_combobox.setFixedWidth(105)
        self.snap_combobox.addItems(
            [_("None"), _("Bar"), _("Beat"), "1/8th", "1/12th", "1/16th"])
        self.controls_grid_layout.addWidget(QtGui.QLabel(_("Snap:")), 0, 9)
        self.controls_grid_layout.addWidget(self.snap_combobox, 0, 10)
        self.snap_combobox.currentIndexChanged.connect(self.set_snap)
        self.snap_combobox.setCurrentIndex(2)

        self.menu_button = QtGui.QPushButton(_("Menu"))
        self.controls_grid_layout.addWidget(self.menu_button, 0, 3)
        self.action_menu = QtGui.QMenu(self.widget)
        self.menu_button.setMenu(self.action_menu)
        self.copy_action = self.action_menu.addAction(_("Copy"))
        self.copy_action.triggered.connect(self.on_copy)
        self.copy_action.setShortcut(QtGui.QKeySequence.Copy)
        self.cut_action = self.action_menu.addAction(_("Cut"))
        self.cut_action.triggered.connect(self.on_cut)
        self.cut_action.setShortcut(QtGui.QKeySequence.Cut)
        self.paste_action = self.action_menu.addAction(_("Paste"))
        self.paste_action.triggered.connect(self.on_paste)
        self.paste_action.setShortcut(QtGui.QKeySequence.Paste)
        self.select_all_action = self.action_menu.addAction(_("Select All"))
        self.select_all_action.triggered.connect(self.on_select_all)
        self.select_all_action.setShortcut(QtGui.QKeySequence.SelectAll)
        self.clear_selection_action = self.action_menu.addAction(
            _("Clear Selection"))
        self.clear_selection_action.triggered.connect(
            AUDIO_SEQ.scene.clearSelection)
        self.clear_selection_action.setShortcut(
            QtGui.QKeySequence.fromString("Esc"))
        self.action_menu.addSeparator()
        self.delete_selected_action = self.action_menu.addAction(_("Delete"))
        self.delete_selected_action.triggered.connect(self.on_delete_selected)
        self.delete_selected_action.setShortcut(QtGui.QKeySequence.Delete)
        self.action_menu.addSeparator()
        self.clone_action = self.action_menu.addAction(
            _("Clone from Region..."))
        self.clone_action.triggered.connect(self.on_clone)
        self.glue_selected_action = self.action_menu.addAction(
            _("Glue Selected"))
        self.glue_selected_action.triggered.connect(self.on_glue_selected)
        self.glue_selected_action.setShortcut(
            QtGui.QKeySequence.fromString("CTRL+G"))
        self.crossfade_action = self.action_menu.addAction(
            _("Crossfade Selected"))
        self.crossfade_action.triggered.connect(AUDIO_SEQ.crossfade_selected)
        self.crossfade_action.setShortcut(
            QtGui.QKeySequence.fromString("CTRL+F"))

        self.default_combobox = QtGui.QComboBox()
        self.default_combobox.setMinimumWidth(150)
        self.default_combobox.addItems(TRACK_NAMES)
        self.default_combobox.currentIndexChanged.connect(
            self.default_track_changed)
        self.controls_grid_layout.addWidget(
            QtGui.QLabel(_(("Default:"))), 0, 20)
        self.controls_grid_layout.addWidget(self.default_combobox, 0, 21)
        AUDIO_TRACK_COMBOBOXES.append(self.default_combobox)

        self.v_zoom_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.v_zoom_slider.setObjectName("zoom_slider")
        self.v_zoom_slider.setRange(10, 100)
        self.v_zoom_slider.setValue(10)
        self.v_zoom_slider.setSingleStep(1)
        self.v_zoom_slider.setMaximumWidth(210)
        self.v_zoom_slider.valueChanged.connect(self.set_v_zoom)
        self.controls_grid_layout.addWidget(QtGui.QLabel(_("V-Zoom:")), 0, 45)
        self.controls_grid_layout.addWidget(self.v_zoom_slider, 0, 46)

        self.h_zoom_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.h_zoom_slider.setObjectName("zoom_slider")
        self.h_zoom_slider.setRange(10, 200)
        self.h_zoom_slider.setValue(10)
        self.h_zoom_slider.setSingleStep(1)
        self.h_zoom_slider.setMaximumWidth(210)
        self.h_zoom_slider.valueChanged.connect(self.set_zoom)
        self.controls_grid_layout.addWidget(QtGui.QLabel(_("H-Zoom:")), 0, 49)
        self.controls_grid_layout.addWidget(self.h_zoom_slider, 0, 50)



        self.audio_items_clipboard = []
        self.hsplitter.setSizes([100, 9999])
        self.disable_on_play = (self.menu_button, self.snap_combobox)

    def on_play(self):
        for f_item in self.disable_on_play:
            f_item.setEnabled(False)

    def on_stop(self):
        for f_item in self.disable_on_play:
            f_item.setEnabled(True)

    def set_tooltips(self, a_on):
        if a_on:
            self.folders_widget.setToolTip(
                libpydaw.strings.audio_viewer_widget_folders)
            self.modulex.widget.setToolTip(
                libpydaw.strings.audio_viewer_widget_modulex)
        else:
            self.folders_widget.setToolTip("")
            self.modulex.widget.setToolTip("")

    def file_mouse_press_event(self, a_event):
        QtGui.QListWidget.mousePressEvent(self.list_file, a_event)
        global AUDIO_ITEMS_TO_DROP
        AUDIO_ITEMS_TO_DROP = []
        for f_item in self.list_file.selectedItems():
            AUDIO_ITEMS_TO_DROP.append(
                "{}/{}".format(self.last_open_dir, f_item.text()))

    def default_track_changed(self, a_val):
        global DEFAULT_AUDIO_TRACK
        DEFAULT_AUDIO_TRACK = a_val

    def on_select_all(self):
        if CURRENT_REGION is None or libmk.IS_PLAYING:
            return
        for f_item in AUDIO_SEQ.audio_items:
            f_item.setSelected(True)

    def on_glue_selected(self):
        if CURRENT_REGION is None or libmk.IS_PLAYING:
            return
        AUDIO_SEQ.glue_selected()

    def on_delete_selected(self):
        if CURRENT_REGION is None or libmk.IS_PLAYING:
            return
        AUDIO_SEQ.delete_selected()

    def on_preview(self):
        f_list = self.list_file.selectedItems()
        if f_list:
            libmk.IPC.pydaw_preview_audio(
                "{}/{}".format(self.last_open_dir, f_list[0].text()))

    def on_stop_preview(self):
        libmk.IPC.pydaw_stop_preview()

    def on_modulex_copy(self):
        if CURRENT_AUDIO_ITEM_INDEX is not None and \
        CURRENT_REGION is not None:
            f_paif = PROJECT.get_audio_per_item_fx_region(CURRENT_REGION.uid)
            self.modulex_clipboard = f_paif.get_row(
                CURRENT_AUDIO_ITEM_INDEX)

    def on_modulex_paste(self):
        if self.modulex_clipboard is not None and CURRENT_REGION is not None:
            f_paif = PROJECT.get_audio_per_item_fx_region(CURRENT_REGION.uid)
            for f_item in AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    f_paif.set_row(f_item.track_num, self.modulex_clipboard)
            PROJECT.save_audio_per_item_fx_region(CURRENT_REGION.uid, f_paif)
            PROJECT.en_osc.pydaw_audio_per_item_fx_region(
                CURRENT_REGION.uid)
            AUDIO_SEQ_WIDGET.modulex.set_from_list(self.modulex_clipboard)

    def on_modulex_clear(self):
        if CURRENT_REGION is not None:
            f_paif = PROJECT.get_audio_per_item_fx_region(CURRENT_REGION.uid)
            for f_item in AUDIO_SEQ.audio_items:
                if f_item.isSelected():
                    f_paif.clear_row(f_item.track_num)
            PROJECT.save_audio_per_item_fx_region(CURRENT_REGION.uid, f_paif)
            PROJECT.en_osc.pydaw_audio_per_item_fx_region(
                CURRENT_REGION.uid)
            self.modulex.clear_effects()

    def on_copy(self):
        if CURRENT_REGION is None or libmk.IS_PLAYING:
            return 0
        self.audio_items_clipboard = []
        f_per_item_fx_dict = PROJECT.get_audio_per_item_fx_region(
            CURRENT_REGION.uid)
        f_count = False
        for f_item in AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_count = True
                self.audio_items_clipboard.append(
                    (str(f_item.audio_item),
                     f_per_item_fx_dict.get_row(f_item.track_num, True)))
        if not f_count:
            QtGui.QMessageBox.warning(
                self.widget, _("Error"), _("Nothing selected."))
        return f_count

    def on_cut(self):
        if self.on_copy():
            self.on_delete_selected()

    def on_paste(self):
        if CURRENT_REGION is None or libmk.IS_PLAYING:
            return
        if not self.audio_items_clipboard:
            QtGui.QMessageBox.warning(self.widget, _("Error"),
                                      _("Nothing copied to the clipboard."))
        AUDIO_SEQ.reselect_on_stop = []
        f_per_item_fx_dict = PROJECT.get_audio_per_item_fx_region(
            CURRENT_REGION.uid)
        f_current_region_length = pydaw_get_current_region_length()
        f_global_tempo = float(TRANSPORT.tempo_spinbox.value())
        for f_str, f_list in self.audio_items_clipboard:
            AUDIO_SEQ.reselect_on_stop.append(f_str)
            f_index = AUDIO_ITEMS.get_next_index()
            if f_index == -1:
                break
            f_item = pydaw_audio_item.from_str(f_str)
            f_start = f_item.start_bar + (f_item.start_beat * 0.25)
            if f_start < f_current_region_length:
                f_graph = libmk.PROJECT.get_sample_graph_by_uid(f_item.uid)
                f_item.clip_at_region_end(
                    f_current_region_length, f_global_tempo,
                    f_graph.length_in_seconds)
                AUDIO_ITEMS.add_item(f_index, f_item)
                if f_list is not None:
                    f_per_item_fx_dict.set_row(f_index, f_list)
        AUDIO_ITEMS.deduplicate_items()
        PROJECT.save_audio_region(CURRENT_REGION.uid, AUDIO_ITEMS)
        PROJECT.save_audio_per_item_fx_region(
            CURRENT_REGION.uid, f_per_item_fx_dict, False)
        PROJECT.en_osc.pydaw_audio_per_item_fx_region(
            CURRENT_REGION.uid)
        PROJECT.commit(_("Paste audio items"))
        global_open_audio_items(True)
        AUDIO_SEQ.scene.clearSelection()
        AUDIO_SEQ.reset_selection()

    def on_clone(self):
        if CURRENT_REGION is None or libmk.IS_PLAYING:
            return
        def ok_handler():
            f_region_name = str(f_region_combobox.currentText())
            PROJECT.region_audio_clone(CURRENT_REGION.uid, f_region_name)
            global_open_audio_items(True)
            f_window.close()

        def cancel_handler():
            f_window.close()

        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Clone audio from region..."))
        f_window.setMinimumWidth(270)
        f_layout = QtGui.QGridLayout()
        f_window.setLayout(f_layout)
        f_layout.addWidget(QtGui.QLabel(_("Clone from:")), 0, 0)
        f_region_combobox = QtGui.QComboBox()
        f_regions_dict = PROJECT.get_regions_dict()
        f_regions_list = list(f_regions_dict.uid_lookup.keys())
        f_regions_list.sort()
        f_region_combobox.addItems(f_regions_list)
        f_layout.addWidget(f_region_combobox, 0, 1)
        f_ok_button = QtGui.QPushButton(_("OK"))
        f_layout.addWidget(f_ok_button, 5, 0)
        f_ok_button.clicked.connect(ok_handler)
        f_cancel_button = QtGui.QPushButton(_("Cancel"))
        f_layout.addWidget(f_cancel_button, 5, 1)
        f_cancel_button.clicked.connect(cancel_handler)
        f_window.exec_()

    def set_v_zoom(self, a_val=None):
        AUDIO_SEQ.set_v_zoom(float(a_val) * 0.1)
        global_open_audio_items(a_reload=False)

    def set_snap(self, a_val=None):
        pydaw_set_audio_snap(a_val)
        global_open_audio_items(a_reload=False)

    def set_zoom(self, a_val=None):
        AUDIO_SEQ.set_zoom(float(a_val) * 0.1)
        global_open_audio_items(a_reload=False)


AUDIO_ITEMS = None

def global_open_audio_items(a_update_viewer=True, a_reload=True):
    global AUDIO_ITEMS
    if a_reload:
        if CURRENT_REGION:
            AUDIO_ITEMS = PROJECT.get_audio_region(CURRENT_REGION.uid)
        else:
            AUDIO_ITEMS = None
    if a_update_viewer:
        f_selected_list = []
        for f_item in AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_selected_list.append(str(f_item.audio_item))
        AUDIO_SEQ.setUpdatesEnabled(False)
        AUDIO_SEQ.update_zoom()
        AUDIO_SEQ.clear_drawn_items()
        if AUDIO_ITEMS:
            for k, v in AUDIO_ITEMS.items.items():
                try:
                    f_graph = libmk.PROJECT.get_sample_graph_by_uid(v.uid)
                    if f_graph is None:
                        print(_("Error drawing item for {}, could not get "
                        "sample graph object").format(v.uid))
                        continue
                    AUDIO_SEQ.draw_item(k, v, f_graph)
                except:
                    if libmk.IS_PLAYING:
                        print(_("Exception while loading {}".format(v.uid)))
                    else:
                        f_path = libmk.PROJECT.get_wav_path_by_uid(v.uid)
                        if os.path.isfile(f_path):
                            f_error_msg = _(
                                "Unknown error loading sample f_path {}, "
                                "\n\n{}").format(f_path, locals())
                        else:
                            f_error_msg = _(
                                "Error loading '{}', file does not "
                                "exist.").format(f_path)
                        QtGui.QMessageBox.warning(
                            MAIN_WINDOW, _("Error"), f_error_msg)
        for f_item in AUDIO_SEQ.audio_items:
            if str(f_item.audio_item) in f_selected_list:
                f_item.setSelected(True)
        AUDIO_SEQ.setUpdatesEnabled(True)
        AUDIO_SEQ.update()


def global_set_piano_roll_zoom():
    global PIANO_ROLL_GRID_WIDTH
    global MIDI_SCALE

    f_width = float(PIANO_ROLL_EDITOR.rect().width()) - \
        float(PIANO_ROLL_EDITOR.verticalScrollBar().width()) - 6.0 - \
        PIANO_KEYS_WIDTH
    f_region_scale = f_width / (ITEM_EDITING_COUNT * 1000.0)

    PIANO_ROLL_GRID_WIDTH = 1000.0 * MIDI_SCALE * f_region_scale
    pydaw_set_piano_roll_quantize(PIANO_ROLL_QUANTIZE_INDEX)

ITEM_EDITING_COUNT = 1

PIANO_ROLL_SNAP = False
PIANO_ROLL_GRID_WIDTH = 1000.0
PIANO_KEYS_WIDTH = 34  #Width of the piano keys in px
PIANO_ROLL_GRID_MAX_START_TIME = 999.0 + PIANO_KEYS_WIDTH
PIANO_ROLL_NOTE_HEIGHT = pydaw_util.get_file_setting("PIANO_VZOOM", int, 21)
PIANO_ROLL_SNAP_DIVISOR = 16.0
PIANO_ROLL_SNAP_BEATS = 4.0 / PIANO_ROLL_SNAP_DIVISOR
PIANO_ROLL_SNAP_VALUE = PIANO_ROLL_GRID_WIDTH / PIANO_ROLL_SNAP_DIVISOR
PIANO_ROLL_SNAP_DIVISOR_BEATS = PIANO_ROLL_SNAP_DIVISOR / 4.0
PIANO_ROLL_NOTE_COUNT = 120
PIANO_ROLL_HEADER_HEIGHT = 45
#gets updated by the piano roll to it's real value:
PIANO_ROLL_TOTAL_HEIGHT = 1000
PIANO_ROLL_QUANTIZE_INDEX = 4

SELECTED_NOTE_GRADIENT = QtGui.QLinearGradient(
    QtCore.QPointF(0, 0), QtCore.QPointF(0, 12))
SELECTED_NOTE_GRADIENT.setColorAt(0, QtGui.QColor(180, 172, 100))
SELECTED_NOTE_GRADIENT.setColorAt(1, QtGui.QColor(240, 240, 240))

SELECTED_PIANO_NOTE = None   #Used for mouse click hackery

def pydaw_set_piano_roll_quantize(a_index):
    global PIANO_ROLL_SNAP
    global PIANO_ROLL_SNAP_VALUE
    global PIANO_ROLL_SNAP_DIVISOR
    global PIANO_ROLL_SNAP_DIVISOR_BEATS
    global PIANO_ROLL_SNAP_BEATS
    global LAST_NOTE_RESIZE
    global PIANO_ROLL_QUANTIZE_INDEX

    PIANO_ROLL_QUANTIZE_INDEX = a_index

    if a_index == 0:
        PIANO_ROLL_SNAP = False
    else:
        PIANO_ROLL_SNAP = True

    if a_index == 0:
        PIANO_ROLL_SNAP_DIVISOR = 16.0
    elif a_index == 7:
        PIANO_ROLL_SNAP_DIVISOR = 128.0
    elif a_index == 6:
        PIANO_ROLL_SNAP_DIVISOR = 64.0
    elif a_index == 5:
        PIANO_ROLL_SNAP_DIVISOR = 32.0
    elif a_index == 4:
        PIANO_ROLL_SNAP_DIVISOR = 16.0
    elif a_index == 3:
        PIANO_ROLL_SNAP_DIVISOR = 12.0
    elif a_index == 2:
        PIANO_ROLL_SNAP_DIVISOR = 8.0
    elif a_index == 1:
        PIANO_ROLL_SNAP_DIVISOR = 4.0

    PIANO_ROLL_SNAP_BEATS = 4.0 / PIANO_ROLL_SNAP_DIVISOR
    LAST_NOTE_RESIZE = pydaw_clip_min(LAST_NOTE_RESIZE, PIANO_ROLL_SNAP_BEATS)
    PIANO_ROLL_EDITOR.set_grid_div(PIANO_ROLL_SNAP_DIVISOR / 4.0)
    PIANO_ROLL_SNAP_DIVISOR *= ITEM_EDITING_COUNT
    PIANO_ROLL_SNAP_VALUE = (PIANO_ROLL_GRID_WIDTH *
        ITEM_EDITING_COUNT) / PIANO_ROLL_SNAP_DIVISOR
    PIANO_ROLL_SNAP_DIVISOR_BEATS = \
        PIANO_ROLL_SNAP_DIVISOR / (4.0 * ITEM_EDITING_COUNT)

PIANO_ROLL_MIN_NOTE_LENGTH = PIANO_ROLL_GRID_WIDTH / 128.0

PIANO_ROLL_NOTE_LABELS = [
    "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

PIANO_NOTE_GRADIENT_TUPLE = \
    ((255, 0, 0), (255, 123, 0), (255, 255, 0), (123, 255, 0), (0, 255, 0),
     (0, 255, 123), (0, 255, 255), (0, 123, 255), (0, 0, 255), (0, 0, 255))

PIANO_ROLL_DELETE_MODE = False
PIANO_ROLL_DELETED_NOTES = []

LAST_NOTE_RESIZE = 0.25

PIANO_ROLL_HEADER_GRADIENT = QtGui.QLinearGradient(
    0.0, 0.0, 0.0, PIANO_ROLL_HEADER_HEIGHT)
PIANO_ROLL_HEADER_GRADIENT.setColorAt(0.0, QtGui.QColor.fromRgb(61, 61, 61))
PIANO_ROLL_HEADER_GRADIENT.setColorAt(0.5, QtGui.QColor.fromRgb(50,50, 50))
PIANO_ROLL_HEADER_GRADIENT.setColorAt(0.6, QtGui.QColor.fromRgb(43, 43, 43))
PIANO_ROLL_HEADER_GRADIENT.setColorAt(1.0, QtGui.QColor.fromRgb(65, 65, 65))

def piano_roll_set_delete_mode(a_enabled):
    global PIANO_ROLL_DELETE_MODE, PIANO_ROLL_DELETED_NOTES
    if a_enabled:
        PIANO_ROLL_EDITOR.setDragMode(QtGui.QGraphicsView.NoDrag)
        PIANO_ROLL_DELETED_NOTES = []
        PIANO_ROLL_DELETE_MODE = True
        QtGui.QApplication.setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.ForbiddenCursor))
    else:
        PIANO_ROLL_EDITOR.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
        PIANO_ROLL_DELETE_MODE = False
        for f_item in PIANO_ROLL_DELETED_NOTES:
            f_item.delete()
        PIANO_ROLL_EDITOR.selected_note_strings = []
        global_save_and_reload_items()
        QtGui.QApplication.restoreOverrideCursor()


class piano_roll_note_item(QtGui.QGraphicsRectItem):
    def __init__(self, a_length, a_note_height, a_note, a_note_item,
                 a_item_index, a_enabled=True):
        QtGui.QGraphicsRectItem.__init__(self, 0, 0, a_length, a_note_height)
        self.item_index = a_item_index
        if a_enabled:
            self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
            self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
            self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges)
            self.setZValue(1002.0)
        else:
            self.setZValue(1001.0)
            self.setEnabled(False)
            self.setOpacity(0.3)
        self.note_height = a_note_height
        self.current_note_text = None
        self.note_item = a_note_item
        self.setAcceptHoverEvents(True)
        self.resize_start_pos = self.note_item.start
        self.is_copying = False
        self.is_velocity_dragging = False
        self.is_velocity_curving = False
        if SELECTED_PIANO_NOTE is not None and \
        a_note_item == SELECTED_PIANO_NOTE:
            self.is_resizing = True
            PIANO_ROLL_EDITOR.click_enabled = True
        else:
            self.is_resizing = False
        self.showing_resize_cursor = False
        self.resize_rect = self.rect()
        self.mouse_y_pos = QtGui.QCursor.pos().y()
        self.note_text = QtGui.QGraphicsSimpleTextItem(self)
        self.note_text.setPen(QtGui.QPen(QtCore.Qt.black))
        self.update_note_text()
        self.vel_line = QtGui.QGraphicsLineItem(self)
        self.set_vel_line()
        self.set_brush()

    def set_vel_line(self):
        f_vel = self.note_item.velocity
        f_rect = self.rect()
        f_y = (1.0 - (f_vel * 0.007874016)) * f_rect.height()
        f_width = f_rect.width()
        self.vel_line.setLine(0.0, f_y, f_width, f_y)

    def set_brush(self):
        f_val = (1.0 - (self.note_item.velocity / 127.0)) * 9.0
        f_val = pydaw_util.pydaw_clip_value(f_val, 0.0, 9.0)
        f_int = int(f_val)
        f_frac = f_val - f_int
        f_vals = []
        for f_i in range(3):
            f_val = (((PIANO_NOTE_GRADIENT_TUPLE[f_int + 1][f_i] -
                PIANO_NOTE_GRADIENT_TUPLE[f_int][f_i]) * f_frac) +
                PIANO_NOTE_GRADIENT_TUPLE[f_int][f_i])
            f_vals.append(int(f_val))
        f_vals_m1 = pydaw_rgb_minus(f_vals, 90)
        f_vals_m2 = pydaw_rgb_minus(f_vals, 120)
        f_gradient = QtGui.QLinearGradient(0.0, 0.0, 0.0, self.note_height)
        f_gradient.setColorAt(0.0, QtGui.QColor(*f_vals_m1))
        f_gradient.setColorAt(0.4, QtGui.QColor(*f_vals))
        f_gradient.setColorAt(0.6, QtGui.QColor(*f_vals))
        f_gradient.setColorAt(1.0, QtGui.QColor(*f_vals_m2))
        self.setBrush(f_gradient)

    def update_note_text(self, a_note_num=None):
        f_note_num = a_note_num if a_note_num is not None \
            else self.note_item.note_num
        f_octave = (f_note_num // 12) - 2
        f_note = PIANO_ROLL_NOTE_LABELS[f_note_num % 12]
        f_text = "{}{}".format(f_note, f_octave)
        if f_text != self.current_note_text:
            self.current_note_text = f_text
            self.note_text.setText(f_text)

    def mouse_is_at_end(self, a_pos):
        f_width = self.rect().width()
        if f_width >= 30.0:
            return a_pos.x() > (f_width - 15.0)
        else:
            return a_pos.x() > (f_width * 0.72)

    def hoverMoveEvent(self, a_event):
        #QtGui.QGraphicsRectItem.hoverMoveEvent(self, a_event)
        if not self.is_resizing:
            PIANO_ROLL_EDITOR.click_enabled = False
            self.show_resize_cursor(a_event)

    def delete_later(self):
        global PIANO_ROLL_DELETED_NOTES
        if self.isEnabled() and self not in PIANO_ROLL_DELETED_NOTES:
            PIANO_ROLL_DELETED_NOTES.append(self)
            self.hide()

    def delete(self):
        ITEM_EDITOR.items[self.item_index].remove_note(self.note_item)

    def show_resize_cursor(self, a_event):
        f_is_at_end = self.mouse_is_at_end(a_event.pos())
        if f_is_at_end and not self.showing_resize_cursor:
            QtGui.QApplication.setOverrideCursor(
                QtGui.QCursor(QtCore.Qt.SizeHorCursor))
            self.showing_resize_cursor = True
        elif not f_is_at_end and self.showing_resize_cursor:
            QtGui.QApplication.restoreOverrideCursor()
            self.showing_resize_cursor = False

    def get_selected_string(self):
        return "{}|{}".format(self.item_index, self.note_item)

    def hoverEnterEvent(self, a_event):
        QtGui.QGraphicsRectItem.hoverEnterEvent(self, a_event)
        PIANO_ROLL_EDITOR.click_enabled = False

    def hoverLeaveEvent(self, a_event):
        QtGui.QGraphicsRectItem.hoverLeaveEvent(self, a_event)
        PIANO_ROLL_EDITOR.click_enabled = True
        QtGui.QApplication.restoreOverrideCursor()
        self.showing_resize_cursor = False

    def mouseDoubleClickEvent(self, a_event):
        QtGui.QGraphicsRectItem.mouseDoubleClickEvent(self, a_event)
        QtGui.QApplication.restoreOverrideCursor()

    def mousePressEvent(self, a_event):
        if a_event.modifiers() == QtCore.Qt.ShiftModifier:
            piano_roll_set_delete_mode(True)
            self.delete_later()
        elif a_event.modifiers() == \
        QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier:
            self.is_velocity_dragging = True
        elif a_event.modifiers() == \
        QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier:
            self.is_velocity_curving = True
            f_list = [((x.item_index * 4.0) + x.note_item.start)
                for x in PIANO_ROLL_EDITOR.get_selected_items()]
            f_list.sort()
            self.vc_start = f_list[0]
            self.vc_mid = (self.item_index * 4.0) + self.note_item.start
            self.vc_end = f_list[-1]
        else:
            a_event.setAccepted(True)
            QtGui.QGraphicsRectItem.mousePressEvent(self, a_event)
            self.setBrush(SELECTED_NOTE_GRADIENT)
            self.o_pos = self.pos()
            if self.mouse_is_at_end(a_event.pos()):
                self.is_resizing = True
                self.mouse_y_pos = QtGui.QCursor.pos().y()
                self.resize_last_mouse_pos = a_event.pos().x()
                for f_item in PIANO_ROLL_EDITOR.get_selected_items():
                    f_item.resize_start_pos = f_item.note_item.start + (
                        4.0 * f_item.item_index)
                    f_item.resize_pos = f_item.pos()
                    f_item.resize_rect = f_item.rect()
            elif a_event.modifiers() == QtCore.Qt.ControlModifier:
                self.is_copying = True
                for f_item in PIANO_ROLL_EDITOR.get_selected_items():
                    PIANO_ROLL_EDITOR.draw_note(
                        f_item.note_item, f_item.item_index)
        if self.is_velocity_curving or self.is_velocity_dragging:
            a_event.setAccepted(True)
            self.setSelected(True)
            QtGui.QGraphicsRectItem.mousePressEvent(self, a_event)
            self.orig_y = a_event.pos().y()
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.BlankCursor)
            for f_item in PIANO_ROLL_EDITOR.get_selected_items():
                f_item.orig_value = f_item.note_item.velocity
                f_item.set_brush()
            for f_item in PIANO_ROLL_EDITOR.note_items:
                f_item.note_text.setText(str(f_item.note_item.velocity))
        PIANO_ROLL_EDITOR.click_enabled = True

    def mouseMoveEvent(self, a_event):
        if self.is_velocity_dragging or self.is_velocity_curving:
            f_pos = a_event.pos()
            f_y = f_pos.y()
            f_diff_y = self.orig_y - f_y
            f_val = (f_diff_y * 0.5)
        else:
            QtGui.QGraphicsRectItem.mouseMoveEvent(self, a_event)

        if self.is_resizing:
            f_pos_x = a_event.pos().x()
            self.resize_last_mouse_pos = a_event.pos().x()
        for f_item in PIANO_ROLL_EDITOR.get_selected_items():
            if self.is_resizing:
                if PIANO_ROLL_SNAP:
                    f_adjusted_width = round(
                        f_pos_x / PIANO_ROLL_SNAP_VALUE) * \
                        PIANO_ROLL_SNAP_VALUE
                    if f_adjusted_width == 0.0:
                        f_adjusted_width = PIANO_ROLL_SNAP_VALUE
                else:
                    f_adjusted_width = pydaw_clip_min(
                        f_pos_x, PIANO_ROLL_MIN_NOTE_LENGTH)
                f_item.resize_rect.setWidth(f_adjusted_width)
                f_item.setRect(f_item.resize_rect)
                f_item.setPos(f_item.resize_pos.x(), f_item.resize_pos.y())
                QtGui.QCursor.setPos(QtGui.QCursor.pos().x(), self.mouse_y_pos)
            elif self.is_velocity_dragging:
                f_new_vel = pydaw_util.pydaw_clip_value(
                    f_val + f_item.orig_value, 1, 127)
                f_new_vel = int(f_new_vel)
                f_item.note_item.velocity = f_new_vel
                f_item.note_text.setText(str(f_new_vel))
                f_item.set_brush()
                f_item.set_vel_line()
            elif self.is_velocity_curving:
                f_start = ((f_item.item_index * 4.0) + f_item.note_item.start)
                if f_start == self.vc_mid:
                    f_new_vel = f_val + f_item.orig_value
                else:
                    if f_start > self.vc_mid:
                        f_frac = (f_start -
                            self.vc_mid) / (self.vc_end - self.vc_mid)
                        f_new_vel = pydaw_util.linear_interpolate(
                            f_val, 0.3 * f_val, f_frac)
                    else:
                        f_frac = (f_start -
                            self.vc_start) / (self.vc_mid - self.vc_start)
                        f_new_vel = pydaw_util.linear_interpolate(
                            0.3 * f_val, f_val, f_frac)
                    f_new_vel += f_item.orig_value
                f_new_vel = pydaw_util.pydaw_clip_value(f_new_vel, 1, 127)
                f_new_vel = int(f_new_vel)
                f_item.note_item.velocity = f_new_vel
                f_item.note_text.setText(str(f_new_vel))
                f_item.set_brush()
                f_item.set_vel_line()
            else:
                f_pos_x = f_item.pos().x()
                f_pos_y = f_item.pos().y()
                if f_pos_x < PIANO_KEYS_WIDTH:
                    f_pos_x = PIANO_KEYS_WIDTH
                elif f_pos_x > PIANO_ROLL_GRID_MAX_START_TIME:
                    f_pos_x = PIANO_ROLL_GRID_MAX_START_TIME
                if f_pos_y < PIANO_ROLL_HEADER_HEIGHT:
                    f_pos_y = PIANO_ROLL_HEADER_HEIGHT
                elif f_pos_y > PIANO_ROLL_TOTAL_HEIGHT:
                    f_pos_y = PIANO_ROLL_TOTAL_HEIGHT
                f_pos_y = \
                    (int((f_pos_y - PIANO_ROLL_HEADER_HEIGHT) /
                    self.note_height) * self.note_height) + \
                    PIANO_ROLL_HEADER_HEIGHT
                if PIANO_ROLL_SNAP:
                    f_pos_x = (int((f_pos_x - PIANO_KEYS_WIDTH) /
                    PIANO_ROLL_SNAP_VALUE) *
                    PIANO_ROLL_SNAP_VALUE) + PIANO_KEYS_WIDTH
                f_item.setPos(f_pos_x, f_pos_y)
                f_new_note = self.y_pos_to_note(f_pos_y)
                f_item.update_note_text(f_new_note)

    def y_pos_to_note(self, a_y):
        return int(PIANO_ROLL_NOTE_COUNT -
            ((a_y - PIANO_ROLL_HEADER_HEIGHT) /
            PIANO_ROLL_NOTE_HEIGHT))

    def mouseReleaseEvent(self, a_event):
        if PIANO_ROLL_DELETE_MODE:
            piano_roll_set_delete_mode(False)
            return
        a_event.setAccepted(True)
        f_recip = 1.0 / PIANO_ROLL_GRID_WIDTH
        QtGui.QGraphicsRectItem.mouseReleaseEvent(self, a_event)
        global SELECTED_PIANO_NOTE
        if self.is_copying:
            f_new_selection = []
        for f_item in PIANO_ROLL_EDITOR.get_selected_items():
            f_pos_x = f_item.pos().x()
            f_pos_y = f_item.pos().y()
            if self.is_resizing:
                f_new_note_length = ((f_pos_x + f_item.rect().width() -
                    PIANO_KEYS_WIDTH) * f_recip *
                    4.0) - f_item.resize_start_pos
                if SELECTED_PIANO_NOTE is not None and \
                self.note_item != SELECTED_PIANO_NOTE:
                    f_new_note_length -= (self.item_index * 4.0)
                if PIANO_ROLL_SNAP and \
                f_new_note_length < PIANO_ROLL_SNAP_BEATS:
                    f_new_note_length = PIANO_ROLL_SNAP_BEATS
                elif f_new_note_length < pydaw_min_note_length:
                    f_new_note_length = pydaw_min_note_length
                f_item.note_item.set_length(f_new_note_length)
            elif self.is_velocity_dragging or self.is_velocity_curving:
                pass
            else:
                f_new_note_start = (f_pos_x -
                    PIANO_KEYS_WIDTH) * 4.0 * f_recip
                f_new_note_num = self.y_pos_to_note(f_pos_y)
                if self.is_copying:
                    f_item.item_index, f_new_note_start = \
                        pydaw_beats_to_index(f_new_note_start)
                    f_new_note = pydaw_note(
                        f_new_note_start, f_item.note_item.length,
                        f_new_note_num, f_item.note_item.velocity)
                    ITEM_EDITOR.items[f_item.item_index].add_note(
                        f_new_note, False)
                    # pass a ref instead of a str in case
                    # fix_overlaps() modifies it.
                    f_item.note_item = f_new_note
                    f_new_selection.append(f_item)
                else:
                    ITEM_EDITOR.items[f_item.item_index].notes.remove(
                        f_item.note_item)
                    f_item.item_index, f_new_note_start = \
                        pydaw_beats_to_index(f_new_note_start)
                    f_item.note_item.set_start(f_new_note_start)
                    f_item.note_item.note_num = f_new_note_num
                    ITEM_EDITOR.items[f_item.item_index].notes.append(
                        f_item.note_item)
                    ITEM_EDITOR.items[f_item.item_index].notes.sort()
        if self.is_resizing:
            global LAST_NOTE_RESIZE
            LAST_NOTE_RESIZE = self.note_item.length
        for f_item in ITEM_EDITOR.items:
            f_item.fix_overlaps()
        SELECTED_PIANO_NOTE = None
        PIANO_ROLL_EDITOR.selected_note_strings = []
        if self.is_copying:
            for f_new_item in f_new_selection:
                PIANO_ROLL_EDITOR.selected_note_strings.append(
                    f_new_item.get_selected_string())
        else:
            for f_item in PIANO_ROLL_EDITOR.get_selected_items():
                PIANO_ROLL_EDITOR.selected_note_strings.append(
                    f_item.get_selected_string())
        for f_item in PIANO_ROLL_EDITOR.note_items:
            f_item.is_resizing = False
            f_item.is_copying = False
            f_item.is_velocity_dragging = False
            f_item.is_velocity_curving = False
        global_save_and_reload_items()
        self.showing_resize_cursor = False
        QtGui.QApplication.restoreOverrideCursor()
        PIANO_ROLL_EDITOR.click_enabled = True

class piano_key_item(QtGui.QGraphicsRectItem):
    def __init__(self, a_piano_width, a_note_height, a_parent):
        QtGui.QGraphicsRectItem.__init__(
            self, 0, 0, a_piano_width, a_note_height, a_parent)
        self.setAcceptHoverEvents(True)
        self.hover_brush = QtGui.QColor(200, 200, 200)

    def hoverEnterEvent(self, a_event):
        QtGui.QGraphicsRectItem.hoverEnterEvent(self, a_event)
        self.o_brush = self.brush()
        self.setBrush(self.hover_brush)
        QtGui.QApplication.restoreOverrideCursor()

    def hoverLeaveEvent(self, a_event):
        QtGui.QGraphicsRectItem.hoverLeaveEvent(self, a_event)
        self.setBrush(self.o_brush)

class piano_roll_editor(QtGui.QGraphicsView):
    def __init__(self):
        self.item_length = 4.0
        self.viewer_width = 1000
        self.grid_div = 16

        self.end_octave = 8
        self.start_octave = -2
        self.notes_in_octave = 12
        self.piano_width = 32
        self.padding = 2

        self.update_note_height()

        QtGui.QGraphicsView.__init__(self)
        self.scene = QtGui.QGraphicsScene(self)
        self.scene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
        self.scene.setBackgroundBrush(QtGui.QColor(100, 100, 100))
        self.scene.mousePressEvent = self.sceneMousePressEvent
        self.scene.mouseReleaseEvent = self.sceneMouseReleaseEvent
        self.setAlignment(QtCore.Qt.AlignLeft)
        self.setScene(self.scene)
        self.first_open = True
        self.draw_header()
        self.draw_piano()
        self.draw_grid()

        self.has_selected = False

        self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
        self.note_items = []

        self.right_click = False
        self.left_click = False
        self.click_enabled = True
        self.last_scale = 1.0
        self.last_x_scale = 1.0
        self.scene.selectionChanged.connect(self.highlight_selected)
        self.selected_note_strings = []
        self.piano_keys = None
        self.vel_rand = 0
        self.vel_emphasis = 0
        self.clipboard = []

    def update_note_height(self):
        self.note_height = PIANO_ROLL_NOTE_HEIGHT
        self.octave_height = self.notes_in_octave * self.note_height

        self.piano_height = self.note_height * PIANO_ROLL_NOTE_COUNT

        self.piano_height = self.note_height * PIANO_ROLL_NOTE_COUNT
        global PIANO_ROLL_TOTAL_HEIGHT
        PIANO_ROLL_TOTAL_HEIGHT = self.piano_height + PIANO_ROLL_HEADER_HEIGHT

    def get_selected_items(self):
        return (x for x in self.note_items if x.isSelected())

    def set_tooltips(self, a_on):
        if a_on:
            self.setToolTip(libpydaw.strings.piano_roll_editor)
        else:
            self.setToolTip("")

    def prepare_to_quit(self):
        self.scene.clearSelection()
        self.scene.clear()

    def highlight_keys(self, a_state, a_note):
        f_note = int(a_note)
        f_state = int(a_state)
        if self.piano_keys is not None and f_note in self.piano_keys:
            if f_state == 0:
                if self.piano_keys[f_note].is_black:
                    self.piano_keys[f_note].setBrush(QtGui.QColor(0, 0, 0))
                else:
                    self.piano_keys[f_note].setBrush(
                        QtGui.QColor(255, 255, 255))
            elif f_state == 1:
                self.piano_keys[f_note].setBrush(QtGui.QColor(237, 150, 150))
            else:
                assert(False)

    def set_grid_div(self, a_div):
        self.grid_div = int(a_div)

    def scrollContentsBy(self, x, y):
        QtGui.QGraphicsView.scrollContentsBy(self, x, y)
        self.set_header_and_keys()

    def set_header_and_keys(self):
        f_point = self.get_scene_pos()
        self.piano.setPos(f_point.x(), PIANO_ROLL_HEADER_HEIGHT)
        self.header.setPos(self.piano_width + self.padding, f_point.y())

    def get_scene_pos(self):
        return QtCore.QPointF(self.horizontalScrollBar().value(),
                              self.verticalScrollBar().value())

    def highlight_selected(self):
        self.has_selected = False
        for f_item in self.note_items:
            if f_item.isSelected():
                f_item.setBrush(SELECTED_NOTE_GRADIENT)
                f_item.note_item.is_selected = True
                self.has_selected = True
            else:
                f_item.note_item.is_selected = False
                f_item.set_brush()

    def set_selected_strings(self):
        self.selected_note_strings = [x.get_selected_string()
            for x in self.note_items if x.isSelected()]

    def keyPressEvent(self, a_event):
        QtGui.QGraphicsView.keyPressEvent(self, a_event)
        QtGui.QApplication.restoreOverrideCursor()

    def half_selected(self):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return

        self.selected_note_strings = []

        min_split_size = 4.0 / 64.0

        f_selected = [x for x in self.note_items if x.isSelected()]
        if not f_selected:
            QtGui.QMessageBox.warning(self, _("Error"), _("Nothing selected"))
            return

        for f_note in f_selected:
            if f_note.note_item.length < min_split_size:
                continue
            f_half = f_note.note_item.length * 0.5
            f_note.note_item.set_length(f_half)
            f_new_start = f_note.note_item.start + f_half
            f_index = f_note.item_index
            f_note_num = f_note.note_item.note_num
            f_velocity = f_note.note_item.velocity
            self.selected_note_strings.append(
                "{}|{}".format(f_index, f_note.note_item))
            if f_new_start >= 4.0:
                f_index += int(f_new_start // 4)
                if f_index >= len(OPEN_ITEM_UIDS):
                    print("Item start exceeded item index length")
                    continue
                f_new_start = f_new_start % 4.0
            f_new_note_item = pydaw_note(
                f_new_start, f_half, f_note_num, f_velocity)
            ITEM_EDITOR.items[f_index].add_note(f_new_note_item, False)
            self.selected_note_strings.append(
                "{}|{}".format(f_index, f_new_note_item))

        global_save_and_reload_items()

    def glue_selected(self):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return

        f_selected = [x for x in self.note_items if x.isSelected()]
        if not f_selected:
            QtGui.QMessageBox.warning(self, _("Error"), _("Nothing selected"))
            return

        f_dict = {}
        for f_note in f_selected:
            f_note_num = f_note.note_item.note_num
            if not f_note_num in f_dict:
                f_dict[f_note_num] = []
            f_dict[f_note_num].append(f_note)

        f_result = []

        for k in sorted(f_dict.keys()):
            v = f_dict[k]
            if len(v) == 1:
                v[0].setSelected(False)
                f_dict.pop(k)
            else:
                f_max = -1.0
                f_min = 99999999.9
                for f_note in f_dict[k]:
                    f_offset = f_note.item_index * 4.0
                    f_start = f_note.note_item.start + f_offset
                    if f_start < f_min:
                        f_min = f_start
                    f_end = f_note.note_item.length + f_start
                    if f_end > f_max:
                        f_max = f_end
                f_vels = [x.note_item.velocity for x in f_dict[k]]
                f_vel = int(sum(f_vels) // len(f_vels))

                print(str(f_max))
                print(str(f_min))
                f_length = f_max - f_min
                print(str(f_length))
                f_index = int(f_min // 4)
                print(str(f_index))
                f_start = f_min % 4.0
                print(str(f_start))
                f_new_note = pydaw_note(f_start, f_length, k, f_vel)
                print(str(f_new_note))
                f_result.append((f_index, f_new_note))

        self.delete_selected(False)
        for f_index, f_new_note in f_result:
            ITEM_EDITOR.items[f_index].add_note(f_new_note, False)
        global_save_and_reload_items()


    def copy_selected(self):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return 0
        self.clipboard = [(str(x.note_item), x.item_index)
                          for x in self.note_items if x.isSelected()]
        return len(self.clipboard)

    def paste(self):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return
        if not self.clipboard:
            QtGui.QMessageBox.warning(
                self, _("Error"), _("Nothing copied to the clipboard"))
            return
        f_item_count = len(ITEM_EDITOR.items)
        for f_item, f_index in self.clipboard:
            if f_index < f_item_count:
                ITEM_EDITOR.items[f_index].add_note(
                    pydaw_note.from_str(f_item))
        global_save_and_reload_items()
        self.scene.clearSelection()
        for f_item in self.note_items:
            f_tuple = (str(f_item.note_item), f_item.item_index)
            if f_tuple in self.clipboard:
                f_item.setSelected(True)

    def delete_selected(self, a_save_and_reload=True):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return
        self.selected_note_strings = []
        for f_item in self.get_selected_items():
            ITEM_EDITOR.items[f_item.item_index].remove_note(f_item.note_item)
        if a_save_and_reload:
            global_save_and_reload_items()

    def transpose_selected(self, a_amt):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return

        f_list = [x for x in self.note_items if x.isSelected()]
        if not f_list:
            return
        self.selected_note_strings = []
        for f_item in f_list:
            f_item.note_item.note_num = pydaw_clip_value(
                f_item.note_item.note_num + a_amt, 0, 120)
            self.selected_note_strings.append(f_item.get_selected_string())
        global_save_and_reload_items()

    def focusOutEvent(self, a_event):
        QtGui.QGraphicsView.focusOutEvent(self, a_event)
        QtGui.QApplication.restoreOverrideCursor()

    def sceneMouseReleaseEvent(self, a_event):
        if PIANO_ROLL_DELETE_MODE:
            piano_roll_set_delete_mode(False)
        else:
            QtGui.QGraphicsScene.mouseReleaseEvent(self.scene, a_event)
        self.click_enabled = True

    def sceneMousePressEvent(self, a_event):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
        elif a_event.button() == QtCore.Qt.RightButton:
            return
        elif a_event.modifiers() == QtCore.Qt.ControlModifier:
            self.hover_restore_cursor_event()
        elif a_event.modifiers() == QtCore.Qt.ShiftModifier:
            piano_roll_set_delete_mode(True)
            return
        elif self.click_enabled and ITEM_EDITOR.enabled:
            self.scene.clearSelection()
            f_pos_x = a_event.scenePos().x()
            f_pos_y = a_event.scenePos().y()
            if f_pos_x > PIANO_KEYS_WIDTH and \
            f_pos_x < PIANO_ROLL_GRID_MAX_START_TIME and \
            f_pos_y > PIANO_ROLL_HEADER_HEIGHT and \
            f_pos_y < PIANO_ROLL_TOTAL_HEIGHT:
                f_recip = 1.0 / PIANO_ROLL_GRID_WIDTH
                if self.vel_rand == 1:
                    pass
                elif self.vel_rand == 2:
                    pass
                f_note = int(
                    PIANO_ROLL_NOTE_COUNT - ((f_pos_y -
                    PIANO_ROLL_HEADER_HEIGHT) / self.note_height)) + 1
                if PIANO_ROLL_SNAP:
                    f_beat = (int((f_pos_x - PIANO_KEYS_WIDTH) /
                        PIANO_ROLL_SNAP_VALUE) *
                        PIANO_ROLL_SNAP_VALUE) * f_recip * 4.0
                    f_note_item = pydaw_note(
                        f_beat, LAST_NOTE_RESIZE, f_note, self.get_vel(f_beat))
                else:
                    f_beat = (f_pos_x -
                        PIANO_KEYS_WIDTH) * f_recip * 4.0
                    f_note_item = pydaw_note(
                        f_beat, 0.25, f_note, self.get_vel(f_beat))
                f_note_index = ITEM_EDITOR.add_note(f_note_item)
                global SELECTED_PIANO_NOTE
                SELECTED_PIANO_NOTE = f_note_item
                f_drawn_note = self.draw_note(f_note_item, f_note_index)
                f_drawn_note.setSelected(True)
                f_drawn_note.resize_start_pos = \
                    f_drawn_note.note_item.start + (4.0 *
                    f_drawn_note.item_index)
                f_drawn_note.resize_pos = f_drawn_note.pos()
                f_drawn_note.resize_rect = f_drawn_note.rect()
                f_drawn_note.is_resizing = True
                f_cursor_pos = QtGui.QCursor.pos()
                f_drawn_note.mouse_y_pos = f_cursor_pos.y()
                f_drawn_note.resize_last_mouse_pos = \
                    f_pos_x - f_drawn_note.pos().x()

        a_event.setAccepted(True)
        QtGui.QGraphicsScene.mousePressEvent(self.scene, a_event)
        QtGui.QApplication.restoreOverrideCursor()

    def mouseMoveEvent(self, a_event):
        QtGui.QGraphicsView.mouseMoveEvent(self, a_event)
        if PIANO_ROLL_DELETE_MODE:
            for f_item in self.items(a_event.pos()):
                if isinstance(f_item, piano_roll_note_item):
                    f_item.delete_later()

    def hover_restore_cursor_event(self, a_event=None):
        QtGui.QApplication.restoreOverrideCursor()

    def draw_header(self):
        self.header = QtGui.QGraphicsRectItem(
            0, 0, self.viewer_width, PIANO_ROLL_HEADER_HEIGHT)
        self.header.hoverEnterEvent = self.hover_restore_cursor_event
        self.header.setBrush(PIANO_ROLL_HEADER_GRADIENT)
        self.scene.addItem(self.header)
        #self.header.mapToScene(self.piano_width + self.padding, 0.0)
        self.beat_width = self.viewer_width / self.item_length
        self.value_width = self.beat_width / self.grid_div
        self.header.setZValue(1003.0)

    def draw_piano(self):
        self.piano_keys = {}
        f_black_notes = [2, 4, 6, 9, 11]
        f_piano_label = QtGui.QFont()
        f_piano_label.setPointSize(8)
        self.piano = QtGui.QGraphicsRectItem(
            0, 0, self.piano_width, self.piano_height)
        self.scene.addItem(self.piano)
        self.piano.mapToScene(0.0, PIANO_ROLL_HEADER_HEIGHT)
        f_key = piano_key_item(self.piano_width, self.note_height, self.piano)
        f_label = QtGui.QGraphicsSimpleTextItem("C8", f_key)
        f_label.setPen(QtCore.Qt.black)
        f_label.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations)
        f_label.setPos(4, 0)
        f_label.setFont(f_piano_label)
        f_key.setBrush(QtGui.QColor(255, 255, 255))
        f_note_index = 0
        f_note_num = 0

        for i in range(self.end_octave - self.start_octave,
                       self.start_octave - self.start_octave, -1):
            for j in range(self.notes_in_octave, 0, -1):
                f_key = piano_key_item(
                    self.piano_width, self.note_height, self.piano)
                self.piano_keys[f_note_index] = f_key
                f_note_index += 1
                f_key.setPos(
                    0, (self.note_height * j) + (self.octave_height * (i - 1)))

                f_key.setToolTip("{} - {}hz - MIDI note #{}".format(
                    pydaw_util.note_num_to_string(f_note_num),
                    round(pydaw_pitch_to_hz(f_note_num)), f_note_num))
                f_note_num += 1
                if j == 12:
                    f_label = QtGui.QGraphicsSimpleTextItem("C{}".format(
                        self.end_octave - i), f_key)
                    f_label.setFlag(
                        QtGui.QGraphicsItem.ItemIgnoresTransformations)
                    f_label.setPos(4, 0)
                    f_label.setFont(f_piano_label)
                    f_label.setPen(QtCore.Qt.black)
                if j in f_black_notes:
                    f_key.setBrush(QtGui.QColor(0, 0, 0))
                    f_key.is_black = True
                else:
                    f_key.setBrush(QtGui.QColor(255, 255, 255))
                    f_key.is_black = False
        self.piano.setZValue(1000.0)

    def draw_grid(self):
        f_black_key_brush = QtGui.QBrush(QtGui.QColor(30, 30, 30, 90))
        f_white_key_brush = QtGui.QBrush(QtGui.QColor(210, 210, 210, 90))
        f_base_brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 120))
        try:
            f_index = PIANO_ROLL_EDITOR_WIDGET.scale_combobox.currentIndex()
        except NameError:
            f_index = 0
        if self.first_open or f_index == 0: #Major
            f_octave_brushes = [
                f_base_brush, f_black_key_brush, f_white_key_brush,
                f_black_key_brush, f_white_key_brush, f_white_key_brush,
                f_black_key_brush, f_white_key_brush, f_black_key_brush,
                f_white_key_brush, f_black_key_brush, f_white_key_brush]
        elif f_index == 1: #Melodic Minor
            f_octave_brushes = [
                f_base_brush, f_black_key_brush, f_white_key_brush,
                f_white_key_brush, f_black_key_brush, f_white_key_brush,
                f_black_key_brush, f_white_key_brush, f_black_key_brush,
                f_white_key_brush, f_black_key_brush, f_white_key_brush]
        elif f_index == 2: #Harmonic Minor
            f_octave_brushes = [
                f_base_brush, f_black_key_brush, f_white_key_brush,
                f_white_key_brush, f_black_key_brush, f_white_key_brush,
                f_black_key_brush, f_white_key_brush, f_white_key_brush,
                f_black_key_brush, f_black_key_brush, f_white_key_brush]
        elif f_index == 3: #Natural Minor
            f_octave_brushes = [
                f_base_brush, f_black_key_brush, f_white_key_brush,
                f_white_key_brush, f_black_key_brush, f_white_key_brush,
                f_black_key_brush, f_white_key_brush, f_white_key_brush,
                f_black_key_brush, f_white_key_brush, f_black_key_brush]
        elif f_index == 4: #Pentatonic Major
            f_octave_brushes = [
                f_base_brush, f_black_key_brush, f_white_key_brush,
                f_black_key_brush, f_white_key_brush, f_black_key_brush,
                f_black_key_brush, f_white_key_brush, f_black_key_brush,
                f_white_key_brush, f_black_key_brush, f_black_key_brush]
        elif f_index == 5: #Pentatonic Minor
            f_octave_brushes = [
                f_base_brush, f_black_key_brush, f_black_key_brush,
                f_white_key_brush, f_black_key_brush, f_white_key_brush,
                f_black_key_brush, f_white_key_brush, f_black_key_brush,
                f_black_key_brush, f_white_key_brush, f_black_key_brush]
        elif f_index == 6: #Dorian
            f_octave_brushes = [
                f_base_brush, f_black_key_brush, f_white_key_brush,
                f_white_key_brush, f_black_key_brush, f_white_key_brush,
                f_black_key_brush, f_white_key_brush, f_black_key_brush,
                f_white_key_brush, f_white_key_brush, f_black_key_brush]
        elif f_index == 7: #Phrygian
            f_octave_brushes = [
                f_base_brush, f_white_key_brush, f_black_key_brush,
                f_white_key_brush, f_black_key_brush, f_white_key_brush,
                f_black_key_brush, f_white_key_brush, f_white_key_brush,
                f_black_key_brush, f_white_key_brush, f_black_key_brush]
        elif f_index == 8: #Lydian
            f_octave_brushes = [
                f_base_brush, f_black_key_brush, f_white_key_brush,
                f_black_key_brush, f_white_key_brush, f_black_key_brush,
                f_white_key_brush, f_white_key_brush, f_black_key_brush,
                f_white_key_brush, f_black_key_brush, f_white_key_brush]
        elif f_index == 9: #Mixolydian
            f_octave_brushes = [
                f_base_brush, f_black_key_brush, f_white_key_brush,
                f_black_key_brush, f_white_key_brush, f_white_key_brush,
                f_black_key_brush, f_white_key_brush, f_black_key_brush,
                f_white_key_brush, f_white_key_brush, f_black_key_brush]
        elif f_index == 10: #Locrian
            f_octave_brushes = [
                f_base_brush, f_white_key_brush, f_black_key_brush,
                f_white_key_brush, f_black_key_brush, f_white_key_brush,
                f_white_key_brush, f_black_key_brush, f_white_key_brush,
                f_black_key_brush, f_white_key_brush, f_black_key_brush]
        elif f_index == 11: #Phrygian Dominant
            f_octave_brushes = [
                f_base_brush, f_white_key_brush, f_black_key_brush,
                f_black_key_brush, f_white_key_brush, f_white_key_brush,
                f_black_key_brush, f_white_key_brush, f_white_key_brush,
                f_black_key_brush, f_white_key_brush, f_black_key_brush]
        elif f_index == 12: #Double Harmonic
            f_octave_brushes = [
                f_base_brush, f_white_key_brush, f_black_key_brush,
                f_black_key_brush, f_white_key_brush, f_white_key_brush,
                f_black_key_brush, f_white_key_brush, f_white_key_brush,
                f_black_key_brush, f_black_key_brush, f_white_key_brush]

        f_current_key = 0
        if not self.first_open:
            f_index = \
                12 - PIANO_ROLL_EDITOR_WIDGET.scale_key_combobox.currentIndex()
            f_octave_brushes = \
                f_octave_brushes[f_index:] + f_octave_brushes[:f_index]
        self.first_open = False
        f_note_bar = QtGui.QGraphicsRectItem(0, 0, self.viewer_width,
                                             self.note_height)
        f_note_bar.hoverMoveEvent = self.hover_restore_cursor_event
        f_note_bar.setBrush(f_base_brush)
        self.scene.addItem(f_note_bar)
        f_note_bar.setPos(
            self.piano_width + self.padding, PIANO_ROLL_HEADER_HEIGHT)
        for i in range(self.end_octave - self.start_octave,
                       self.start_octave - self.start_octave, -1):
            for j in range(self.notes_in_octave, 0, -1):
                f_note_bar = QtGui.QGraphicsRectItem(
                    0, 0, self.viewer_width, self.note_height)
                f_note_bar.setZValue(60.0)
                self.scene.addItem(f_note_bar)
                f_note_bar.setBrush(f_octave_brushes[f_current_key])
                f_current_key += 1
                if f_current_key >= len(f_octave_brushes):
                    f_current_key = 0
                f_note_bar_y = (self.note_height * j) + (self.octave_height *
                    (i - 1)) + PIANO_ROLL_HEADER_HEIGHT
                f_note_bar.setPos(
                    self.piano_width + self.padding, f_note_bar_y)
        f_beat_pen = QtGui.QPen()
        f_beat_pen.setWidth(2)
        f_bar_pen = QtGui.QPen(QtGui.QColor(240, 30, 30), 12.0)
        f_line_pen = QtGui.QPen(QtGui.QColor(0, 0, 0))
        f_beat_y = \
            self.piano_height + PIANO_ROLL_HEADER_HEIGHT + self.note_height
        for i in range(0, int(self.item_length) + 1):
            f_beat_x = (self.beat_width * i) + self.piano_width
            f_beat = self.scene.addLine(f_beat_x, 0, f_beat_x, f_beat_y)
            f_beat_number = i % 4
            if f_beat_number == 0 and not i == 0:
                f_beat.setPen(f_bar_pen)
            else:
                f_beat.setPen(f_beat_pen)
            if i < self.item_length:
                f_number = QtGui.QGraphicsSimpleTextItem(
                    str(f_beat_number + 1), self.header)
                f_number.setFlag(
                    QtGui.QGraphicsItem.ItemIgnoresTransformations)
                f_number.setPos((self.beat_width * i), 24)
                f_number.setBrush(QtCore.Qt.white)
                for j in range(0, self.grid_div):
                    f_x = (self.beat_width * i) + (self.value_width *
                        j) + self.piano_width
                    f_line = self.scene.addLine(
                        f_x, PIANO_ROLL_HEADER_HEIGHT, f_x, f_beat_y)
                    if float(j) != self.grid_div * 0.5:
                        f_line.setPen(f_line_pen)

    def resizeEvent(self, a_event):
        QtGui.QGraphicsView.resizeEvent(self, a_event)
        ITEM_EDITOR.tab_changed()

    def clear_drawn_items(self):
        self.note_items = []
        self.scene.clear()
        self.update_note_height()
        self.draw_header()
        self.draw_piano()
        self.draw_grid()
        self.set_header_and_keys()

    def draw_item(self):
        self.has_selected = False #Reset the selected-ness state...
        self.viewer_width = PIANO_ROLL_GRID_WIDTH * ITEM_EDITING_COUNT
        self.setSceneRect(
            0.0, 0.0, self.viewer_width + PIANO_ROLL_GRID_WIDTH,
            self.piano_height + PIANO_ROLL_HEADER_HEIGHT + 24.0)
        self.item_length = float(4 * ITEM_EDITING_COUNT)
        global PIANO_ROLL_GRID_MAX_START_TIME
        PIANO_ROLL_GRID_MAX_START_TIME = ((PIANO_ROLL_GRID_WIDTH - 1.0) *
            ITEM_EDITING_COUNT) + PIANO_KEYS_WIDTH
        self.setUpdatesEnabled(False)
        self.clear_drawn_items()
        if ITEM_EDITOR.enabled:
            f_item_count = len(ITEM_EDITOR.items)
            for f_i, f_item in zip(range(f_item_count), ITEM_EDITOR.items):
                for f_note in f_item.notes:
                    f_note_item = self.draw_note(f_note, f_i)
                    f_note_item.resize_last_mouse_pos = \
                        f_note_item.scenePos().x()
                    f_note_item.resize_pos = f_note_item.scenePos()
                    if f_note_item.get_selected_string() in \
                    self.selected_note_strings:
                        f_note_item.setSelected(True)
            if DRAW_LAST_ITEMS:
                for f_i, f_uid in zip(
                range(f_item_count), LAST_OPEN_ITEM_UIDS):
                    f_item = PROJECT.get_item_by_uid(f_uid)
                    for f_note in f_item.notes:
                        f_note_item = self.draw_note(f_note, f_i, False)
            self.scrollContentsBy(0, 0)
            for f_name, f_i in zip(
            ITEM_EDITOR.item_names, range(len(ITEM_EDITOR.item_names))):
                f_text = QtGui.QGraphicsSimpleTextItem(f_name, self.header)
                f_text.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations)
                f_text.setBrush(QtCore.Qt.yellow)
                f_text.setPos((f_i * PIANO_ROLL_GRID_WIDTH), 2.0)
        self.setUpdatesEnabled(True)
        self.update()

    def draw_note(self, a_note, a_item_index, a_enabled=True):
        """ a_note is an instance of the pydaw_note class"""
        f_start = self.piano_width + self.padding + self.beat_width * \
            (a_note.start + (float(a_item_index) * 4.0))
        f_length = self.beat_width * a_note.length
        f_note = PIANO_ROLL_HEADER_HEIGHT + self.note_height * \
            (PIANO_ROLL_NOTE_COUNT - a_note.note_num)
        f_note_item = piano_roll_note_item(
            f_length, self.note_height, a_note.note_num,
            a_note, a_item_index, a_enabled)
        f_note_item.setPos(f_start, f_note)
        self.scene.addItem(f_note_item)
        if a_enabled:
            self.note_items.append(f_note_item)
            return f_note_item

    def set_vel_rand(self, a_rand, a_emphasis):
        self.vel_rand = int(a_rand)
        self.vel_emphasis = int(a_emphasis)

    def get_vel(self, a_beat):
        if self.vel_rand == 0:
            return 100
        f_emph = self.get_beat_emphasis(a_beat)
        if self.vel_rand == 1:
            return random.randint(75 - f_emph, 100 - f_emph)
        elif self.vel_rand == 2:
            return random.randint(75 - f_emph, 100 - f_emph)
        else:
            assert(False)

    def get_beat_emphasis(self, a_beat, a_amt=25.0):
        if self.vel_emphasis == 0:
            return 0
        f_beat = a_beat
        if self.vel_emphasis == 2:
            f_beat += 0.5
        f_beat = f_beat % 1.0
        if f_beat > 0.5:
            f_beat = 0.5 - (f_beat - 0.5)
            f_beat = 0.5 - f_beat
        return int(f_beat * 2.0 * a_amt)


class piano_roll_editor_widget:
    def quantize_dialog(self):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return
        ITEM_EDITOR.quantize_dialog(PIANO_ROLL_EDITOR.has_selected)

    def transpose_dialog(self):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return
        ITEM_EDITOR.transpose_dialog(PIANO_ROLL_EDITOR.has_selected)

    def velocity_dialog(self):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return
        ITEM_EDITOR.velocity_dialog(PIANO_ROLL_EDITOR.has_selected)

    def select_all(self):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return
        for f_note in PIANO_ROLL_EDITOR.note_items:
            f_note.setSelected(True)

    def __init__(self):
        self.widget = QtGui.QWidget()
        self.vlayout = QtGui.QVBoxLayout()
        self.widget.setLayout(self.vlayout)

        self.controls_grid_layout = QtGui.QGridLayout()
        self.scale_key_combobox = QtGui.QComboBox()
        self.scale_key_combobox.setMinimumWidth(60)
        self.scale_key_combobox.addItems(PIANO_ROLL_NOTE_LABELS)
        self.scale_key_combobox.currentIndexChanged.connect(
            self.reload_handler)
        self.controls_grid_layout.addWidget(QtGui.QLabel("Key:"), 0, 3)
        self.controls_grid_layout.addWidget(self.scale_key_combobox, 0, 4)
        self.scale_combobox = QtGui.QComboBox()
        self.scale_combobox.setMinimumWidth(172)
        self.scale_combobox.addItems(
            ["Major", "Melodic Minor", "Harmonic Minor",
             "Natural Minor", "Pentatonic Major", "Pentatonic Minor",
             "Dorian", "Phrygian", "Lydian", "Mixolydian", "Locrian",
             "Phrygian Dominant", "Double Harmonic"])
        self.scale_combobox.currentIndexChanged.connect(self.reload_handler)
        self.controls_grid_layout.addWidget(QtGui.QLabel(_("Scale:")), 0, 5)
        self.controls_grid_layout.addWidget(self.scale_combobox, 0, 6)

        self.controls_grid_layout.addItem(
            QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Expanding), 0, 30)

        self.edit_menu_button = QtGui.QPushButton(_("Menu"))
        self.edit_menu_button.setFixedWidth(60)
        self.edit_menu = QtGui.QMenu(self.widget)
        self.edit_menu_button.setMenu(self.edit_menu)
        self.controls_grid_layout.addWidget(self.edit_menu_button, 0, 30)

        self.edit_actions_menu = self.edit_menu.addMenu(_("Edit"))

        self.copy_action = self.edit_actions_menu.addAction(_("Copy"))
        self.copy_action.triggered.connect(
            PIANO_ROLL_EDITOR.copy_selected)
        self.copy_action.setShortcut(QtGui.QKeySequence.Copy)

        self.cut_action = self.edit_actions_menu.addAction(_("Cut"))
        self.cut_action.triggered.connect(self.on_cut)
        self.cut_action.setShortcut(QtGui.QKeySequence.Cut)

        self.paste_action = self.edit_actions_menu.addAction(_("Paste"))
        self.paste_action.triggered.connect(PIANO_ROLL_EDITOR.paste)
        self.paste_action.setShortcut(QtGui.QKeySequence.Paste)

        self.select_all_action = self.edit_actions_menu.addAction(
            _("Select All"))
        self.select_all_action.triggered.connect(self.select_all)
        self.select_all_action.setShortcut(QtGui.QKeySequence.SelectAll)

        self.clear_selection_action = self.edit_actions_menu.addAction(
            _("Clear Selection"))
        self.clear_selection_action.triggered.connect(
            PIANO_ROLL_EDITOR.scene.clearSelection)
        self.clear_selection_action.setShortcut(
            QtGui.QKeySequence.fromString("Esc"))

        self.edit_actions_menu.addSeparator()

        self.delete_selected_action = self.edit_actions_menu.addAction(
            _("Delete"))
        self.delete_selected_action.triggered.connect(self.on_delete_selected)
        self.delete_selected_action.setShortcut(QtGui.QKeySequence.Delete)

        self.quantize_action = self.edit_menu.addAction(_("Quantize..."))
        self.quantize_action.triggered.connect(self.quantize_dialog)

        self.transpose_menu = self.edit_menu.addMenu(_("Transpose"))

        self.transpose_action = self.transpose_menu.addAction(_("Dialog..."))
        self.transpose_action.triggered.connect(self.transpose_dialog)

        self.transpose_menu.addSeparator()

        self.up_semitone_action = self.transpose_menu.addAction(
            _("Up Semitone"))
        self.up_semitone_action.triggered.connect(self.transpose_up_semitone)
        self.up_semitone_action.setShortcut(
            QtGui.QKeySequence.fromString("SHIFT+UP"))

        self.down_semitone_action = self.transpose_menu.addAction(
            _("Down Semitone"))
        self.down_semitone_action.triggered.connect(
            self.transpose_down_semitone)
        self.down_semitone_action.setShortcut(
            QtGui.QKeySequence.fromString("SHIFT+DOWN"))

        self.up_octave_action = self.transpose_menu.addAction(_("Up Octave"))
        self.up_octave_action.triggered.connect(self.transpose_up_octave)
        self.up_octave_action.setShortcut(
            QtGui.QKeySequence.fromString("ALT+UP"))

        self.down_octave_action = self.transpose_menu.addAction(
            _("Down Octave"))
        self.down_octave_action.triggered.connect(self.transpose_down_octave)
        self.down_octave_action.setShortcut(
            QtGui.QKeySequence.fromString("ALT+DOWN"))

        self.velocity_menu = self.edit_menu.addMenu(_("Velocity"))

        self.velocity_action = self.velocity_menu.addAction(_("Dialog..."))
        self.velocity_action.triggered.connect(self.velocity_dialog)

        self.velocity_menu.addSeparator()

        self.vel_random_index = 0
        self.velocity_random_menu = self.velocity_menu.addMenu(_("Randomness"))
        self.random_types = [_("None"), _("Tight"), _("Loose")]
        self.vel_rand_action_group = QtGui.QActionGroup(
            self.velocity_random_menu)
        self.velocity_random_menu.triggered.connect(self.vel_rand_triggered)

        for f_i, f_type in zip(
        range(len(self.random_types)), self.random_types):
            f_action = self.velocity_random_menu.addAction(f_type)
            f_action.setActionGroup(self.vel_rand_action_group)
            f_action.setCheckable(True)
            f_action.my_index = f_i
            if f_i == 0:
                f_action.setChecked(True)

        self.vel_emphasis_index = 0
        self.velocity_emphasis_menu = self.velocity_menu.addMenu(_("Emphasis"))
        self.emphasis_types = [_("None"), _("On-beat"), _("Off-beat")]
        self.vel_emphasis_action_group = QtGui.QActionGroup(
            self.velocity_random_menu)
        self.velocity_emphasis_menu.triggered.connect(
            self.vel_emphasis_triggered)

        for f_i, f_type in zip(
        range(len(self.emphasis_types)), self.emphasis_types):
            f_action = self.velocity_emphasis_menu.addAction(f_type)
            f_action.setActionGroup(self.vel_emphasis_action_group)
            f_action.setCheckable(True)
            f_action.my_index = f_i
            if f_i == 0:
                f_action.setChecked(True)

        self.edit_menu.addSeparator()

        self.glue_selected_action = self.edit_menu.addAction(
            _("Glue Selected"))
        self.glue_selected_action.triggered.connect(
            PIANO_ROLL_EDITOR.glue_selected)
        self.glue_selected_action.setShortcut(
            QtGui.QKeySequence.fromString("CTRL+G"))

        self.half_selected_action = self.edit_menu.addAction(
            _("Split Selected in Half"))
        self.half_selected_action.triggered.connect(
            PIANO_ROLL_EDITOR.half_selected)
        self.half_selected_action.setShortcut(
            QtGui.QKeySequence.fromString("CTRL+H"))


        self.edit_menu.addSeparator()

        self.draw_last_action = self.edit_menu.addAction(
            _("Draw Last Item(s)"))
        self.draw_last_action.triggered.connect(self.draw_last)
        self.draw_last_action.setCheckable(True)
        self.draw_last_action.setShortcut(
            QtGui.QKeySequence.fromString("CTRL+F"))

        self.open_last_action = self.edit_menu.addAction(
            _("Open Last Item(s)"))
        self.open_last_action.triggered.connect(self.open_last)
        self.open_last_action.setShortcut(
            QtGui.QKeySequence.fromString("ALT+F"))

        self.controls_grid_layout.addItem(
            QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Expanding), 0, 31)

        self.vlayout.addLayout(self.controls_grid_layout)
        self.vlayout.addWidget(PIANO_ROLL_EDITOR)
        self.snap_combobox = QtGui.QComboBox()
        self.snap_combobox.setMinimumWidth(90)
        self.snap_combobox.addItems(
            [_("None"), "1/4", "1/8", "1/12", "1/16", "1/32", "1/64", "1/128"])
        self.controls_grid_layout.addWidget(QtGui.QLabel(_("Snap:")), 0, 0)
        self.controls_grid_layout.addWidget(self.snap_combobox, 0, 1)
        self.snap_combobox.currentIndexChanged.connect(self.set_snap)

    def open_last(self):
        if LAST_OPEN_ITEM_NAMES:
            global_open_items(LAST_OPEN_ITEM_NAMES)

    def draw_last(self):
        global DRAW_LAST_ITEMS
        DRAW_LAST_ITEMS = not DRAW_LAST_ITEMS
        self.draw_last_action.setChecked(DRAW_LAST_ITEMS)
        global_open_items()

    def vel_rand_triggered(self, a_action):
        self.vel_random_index = a_action.my_index
        self.set_vel_rand()

    def vel_emphasis_triggered(self, a_action):
        self.vel_emphasis_index = a_action.my_index
        self.set_vel_rand()

    def transpose_up_semitone(self):
        PIANO_ROLL_EDITOR.transpose_selected(1)

    def transpose_down_semitone(self):
        PIANO_ROLL_EDITOR.transpose_selected(-1)

    def transpose_up_octave(self):
        PIANO_ROLL_EDITOR.transpose_selected(12)

    def transpose_down_octave(self):
        PIANO_ROLL_EDITOR.transpose_selected(-12)

    def set_vel_rand(self, a_val=None):
        PIANO_ROLL_EDITOR.set_vel_rand(
            self.vel_random_index, self.vel_emphasis_index)

    def on_delete_selected(self):
        PIANO_ROLL_EDITOR.delete_selected()

    def on_cut(self):
        if PIANO_ROLL_EDITOR.copy_selected():
            self.on_delete_selected()

    def set_snap(self, a_val=None):
        f_index = self.snap_combobox.currentIndex()
        pydaw_set_piano_roll_quantize(f_index)
        if OPEN_ITEM_UIDS:
            PIANO_ROLL_EDITOR.set_selected_strings()
            global_open_items()
        else:
            PIANO_ROLL_EDITOR.clear_drawn_items()

    def reload_handler(self, a_val=None):
        PROJECT.set_midi_scale(
            self.scale_key_combobox.currentIndex(),
            self.scale_combobox.currentIndex())
        if OPEN_ITEM_UIDS:
            PIANO_ROLL_EDITOR.set_selected_strings()
            global_open_items()
        else:
            PIANO_ROLL_EDITOR.clear_drawn_items()

def global_set_automation_zoom():
    global AUTOMATION_WIDTH
    AUTOMATION_WIDTH = 690.0 * MIDI_SCALE

AUTOMATION_POINT_DIAMETER = 15.0
AUTOMATION_POINT_RADIUS = AUTOMATION_POINT_DIAMETER * 0.5
AUTOMATION_RULER_WIDTH = 36.0
AUTOMATION_WIDTH = 690.0

AUTOMATION_MIN_HEIGHT = AUTOMATION_RULER_WIDTH - AUTOMATION_POINT_RADIUS

global_automation_gradient = QtGui.QLinearGradient(
    0, 0, AUTOMATION_POINT_DIAMETER, AUTOMATION_POINT_DIAMETER)
global_automation_gradient.setColorAt(0, QtGui.QColor(240, 10, 10))
global_automation_gradient.setColorAt(1, QtGui.QColor(250, 90, 90))

global_automation_selected_gradient = QtGui.QLinearGradient(
    0, 0, AUTOMATION_POINT_DIAMETER, AUTOMATION_POINT_DIAMETER)
global_automation_selected_gradient.setColorAt(0, QtGui.QColor(255, 255, 255))
global_automation_selected_gradient.setColorAt(1, QtGui.QColor(240, 240, 240))

class automation_item(QtGui.QGraphicsEllipseItem):
    def __init__(self, a_time, a_value, a_cc, a_view, a_is_cc, a_item_index):
        QtGui.QGraphicsEllipseItem.__init__(
            self, 0, 0, AUTOMATION_POINT_DIAMETER,
            AUTOMATION_POINT_DIAMETER)
        self.item_index = a_item_index
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges)
        self.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setPos(a_time - AUTOMATION_POINT_RADIUS,
                    a_value - AUTOMATION_POINT_RADIUS)
        self.setBrush(global_automation_gradient)
        f_pen = QtGui.QPen()
        f_pen.setWidth(2)
        f_pen.setColor(QtGui.QColor(170, 0, 0))
        self.setPen(f_pen)
        self.cc_item = a_cc
        self.parent_view = a_view
        self.is_cc = a_is_cc

    def set_brush(self):
        if self.isSelected():
            self.setBrush(global_automation_selected_gradient)
        else:
            self.setBrush(global_automation_gradient)

    def mouseMoveEvent(self, a_event):
        QtGui.QGraphicsEllipseItem.mouseMoveEvent(self, a_event)
        for f_point in self.parent_view.automation_points:
            if f_point.isSelected():
                if f_point.pos().x() < AUTOMATION_MIN_HEIGHT:
                    f_point.setPos(
                        AUTOMATION_MIN_HEIGHT, f_point.pos().y())
                elif f_point.pos().x() > self.parent_view.grid_max_start_time:
                    f_point.setPos(
                        self.parent_view.grid_max_start_time,
                        f_point.pos().y())
                if f_point.pos().y() < AUTOMATION_MIN_HEIGHT:
                    f_point.setPos(f_point.pos().x(), AUTOMATION_MIN_HEIGHT)
                elif f_point.pos().y() > self.parent_view.total_height:
                    f_point.setPos(
                        f_point.pos().x(), self.parent_view.total_height)

    def mouseReleaseEvent(self, a_event):
        QtGui.QGraphicsEllipseItem.mouseReleaseEvent(self, a_event)
        self.parent_view.selected_str = []
        for f_point in self.parent_view.automation_points:
            if f_point.isSelected():
                f_cc_start = \
                (((f_point.pos().x() - AUTOMATION_MIN_HEIGHT) /
                    self.parent_view.item_width) * 4.0)
                if f_cc_start >= 4.0 * ITEM_EDITING_COUNT:
                    f_cc_start = (4.0 * ITEM_EDITING_COUNT) - 0.01
                elif f_cc_start < 0.0:
                    f_cc_start = 0.0
                f_new_item_index, f_cc_start = pydaw_beats_to_index(f_cc_start)
                if self.is_cc:
                    ITEM_EDITOR.items[f_point.item_index].ccs.remove(
                        f_point.cc_item)
                    f_point.item_index = f_new_item_index
                    f_cc_val = (127.0 - (((f_point.pos().y() -
                        AUTOMATION_MIN_HEIGHT) /
                        self.parent_view.viewer_height) * 127.0))

                    f_point.cc_item.start = f_cc_start
                    f_point.cc_item.set_val(f_cc_val)
                    ITEM_EDITOR.items[f_point.item_index].ccs.append(
                        f_point.cc_item)
                    ITEM_EDITOR.items[f_point.item_index].ccs.sort()
                else:
                    #try:
                    ITEM_EDITOR.items[f_point.item_index].pitchbends.\
                        remove(f_point.cc_item)
                    #except ValueError:
                    #print("Exception removing {} from list".format(
                        #f_point.cc_item))
                    f_point.item_index = f_new_item_index
                    f_cc_val = (1.0 - (((f_point.pos().y() -
                        AUTOMATION_MIN_HEIGHT) /
                        self.parent_view.viewer_height) * 2.0))

                    f_point.cc_item.start = f_cc_start
                    f_point.cc_item.set_val(f_cc_val)
                    ITEM_EDITOR.items[f_point.item_index].pitchbends.append(
                        f_point.cc_item)
                    ITEM_EDITOR.items[f_point.item_index].pitchbends.sort()
                self.parent_view.selected_str.append(
                    hash((int(f_point.item_index), str(f_point.cc_item))))
        global_save_and_reload_items()

AUTOMATION_EDITORS = []

class automation_viewer(QtGui.QGraphicsView):
    def __init__(self, a_is_cc=True):
        QtGui.QGraphicsView.__init__(self)
        self.is_cc = a_is_cc
        self.set_scale()
        self.item_length = 4.0
        self.grid_max_start_time = AUTOMATION_WIDTH + \
            AUTOMATION_RULER_WIDTH - AUTOMATION_POINT_RADIUS
        self.viewer_width = AUTOMATION_WIDTH
        self.automation_points = []
        self.clipboard = []
        self.selected_str = []

        self.axis_size = AUTOMATION_RULER_WIDTH

        self.beat_width = self.viewer_width / self.item_length
        self.value_width = self.beat_width / 16.0
        self.lines = []

        self.setMinimumHeight(370)
        self.scene = QtGui.QGraphicsScene(self)
        self.scene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
        self.scene.setBackgroundBrush(QtGui.QColor(100, 100, 100))
        self.scene.mouseDoubleClickEvent = self.sceneMouseDoubleClickEvent
        self.setAlignment(QtCore.Qt.AlignLeft)
        self.setScene(self.scene)
        self.draw_axis()
        self.draw_grid()
        self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter)
        self.cc_num = 1
        self.last_scale = 1.0
        self.last_x_scale = 1.0
        AUTOMATION_EDITORS.append(self)
        self.selection_enabled = True
        self.scene.selectionChanged.connect(self.selection_changed)

    def selection_changed(self, a_event=None):
        if self.selection_enabled:
            for f_item in self.automation_points:
                f_item.set_brush()

    def set_tooltips(self, a_enabled=False):
        if a_enabled:
            if self.is_cc:
                f_start = _("Select the CC you wish to "
                    "automate using the comboboxes below\n")
            else:
                f_start = ""
            self.setToolTip(
                _("{}Draw points by double-clicking, then click "
                "the 'smooth' button to "
                "draw extra points between them.\nClick+drag "
                "to select points\n"
                "Press the 'delete' button to delete selected "
                "points.").format(f_start))
        else:
            self.setToolTip("")

    def prepare_to_quit(self):
        self.selection_enabled = False
        self.scene.clearSelection()
        self.scene.clear()

    def copy_selected(self):
        if not ITEM_EDITOR.enabled:
            return
        self.clipboard = [(x.cc_item.clone(), x.item_index)
            for x in self.automation_points if x.isSelected()]
        self.clipboard.sort(key=lambda x: (x[1], x[0].start))

    def cut(self):
        self.copy_selected()
        self.delete_selected()

    def paste(self):
        if not ITEM_EDITOR.enabled:
            return
        self.selected_str = []
        if self.clipboard:
            self.clear_range(
                self.clipboard[0][1], self.clipboard[0][0].start,
                self.clipboard[-1][1], self.clipboard[-1][0].start)
            for f_item, f_index in self.clipboard:
                if f_index < ITEM_EDITING_COUNT:
                    f_item2 = f_item.clone()
                    if self.is_cc:
                        f_item2.cc_num = self.cc_num
                        ITEM_EDITOR.items[f_index].add_cc(f_item2)
                    else:
                        ITEM_EDITOR.items[f_index].add_pb(f_item2)
                    self.selected_str.append(hash((f_index, str(f_item2))))
            global_save_and_reload_items()

    def clear_range(self, a_start_index, a_start_beat,
                    a_end_index, a_end_beat, a_save=False):
        f_start_tuple = (a_start_index, a_start_beat)
        f_end_tuple = (a_end_index, a_end_beat)
        for f_point in self.automation_points:
            f_tuple = (f_point.item_index, f_point.cc_item.start)
            if f_tuple >= f_start_tuple and f_tuple <= f_end_tuple:
                if self.is_cc:
                    ITEM_EDITOR.items[f_point.item_index].remove_cc(
                        f_point.cc_item)
                else:
                    ITEM_EDITOR.items[f_point.item_index].remove_pb(
                        f_point.cc_item)
        if a_save:
            self.selected_str = []
            global_save_and_reload_items()

    def delete_selected(self):
        if not ITEM_EDITOR.enabled:
            return
        self.selection_enabled = False
        for f_point in self.automation_points:
            if f_point.isSelected():
                if self.is_cc:
                    ITEM_EDITOR.items[f_point.item_index].remove_cc(
                        f_point.cc_item)
                else:
                    ITEM_EDITOR.items[f_point.item_index].remove_pb(
                        f_point.cc_item)
        self.selected_str = []
        global_save_and_reload_items()
        self.selection_enabled = True

    def clear_current_item(self):
        """ If this is a CC editor, it only clears the selected CC.  """
        self.selection_enabled = False
        if not self.automation_points:
            return
        for f_point in self.automation_points:
            if self.is_cc:
                ITEM_EDITOR.items[f_point.item_index].remove_cc(
                    f_point.cc_item)
            else:
                ITEM_EDITOR.items[f_point.item_index].remove_pb(
                    f_point.cc_item)
        self.selected_str = []
        global_save_and_reload_items()
        self.selection_enabled = True

    def sceneMouseDoubleClickEvent(self, a_event):
        if not ITEM_EDITOR.enabled:
            ITEM_EDITOR.show_not_enabled_warning()
            return
        f_pos_x = a_event.scenePos().x() - AUTOMATION_POINT_RADIUS
        f_pos_y = a_event.scenePos().y() - AUTOMATION_POINT_RADIUS
        f_cc_start = ((f_pos_x -
            AUTOMATION_MIN_HEIGHT) / self.item_width) * 4.0
        f_cc_start = pydaw_clip_value(
            f_cc_start, 0.0,
            (4.0  * ITEM_EDITING_COUNT) - 0.01, a_round=True)
        if self.is_cc:
            f_cc_val = int(127.0 - (((f_pos_y - AUTOMATION_MIN_HEIGHT) /
                self.viewer_height) * 127.0))
            f_cc_val = pydaw_clip_value(f_cc_val, 0, 127)
            ITEM_EDITOR.add_cc(pydaw_cc(f_cc_start, self.cc_num, f_cc_val))
        else:
            f_cc_val = 1.0 - (((f_pos_y - AUTOMATION_MIN_HEIGHT) /
                self.viewer_height) * 2.0)
            f_cc_val = pydaw_clip_value(f_cc_val, -1.0, 1.0)
            ITEM_EDITOR.add_pb(pydaw_pitchbend(f_cc_start, f_cc_val))
        QtGui.QGraphicsScene.mouseDoubleClickEvent(self.scene, a_event)
        self.selected_str = []
        global_save_and_reload_items()

    def draw_axis(self):
        self.x_axis = QtGui.QGraphicsRectItem(
            0, 0, self.viewer_width, self.axis_size)
        self.x_axis.setPos(self.axis_size, 0)
        self.scene.addItem(self.x_axis)
        self.y_axis = QtGui.QGraphicsRectItem(
            0, 0, self.axis_size, self.viewer_height)
        self.y_axis.setPos(0, self.axis_size)
        self.scene.addItem(self.y_axis)

    def draw_grid(self):
        f_beat_pen = QtGui.QPen()
        f_beat_pen.setWidth(2)
        f_bar_pen = QtGui.QPen()
        f_bar_pen.setWidth(2)
        f_bar_pen.setColor(QtGui.QColor(224, 60, 60))
        f_line_pen = QtGui.QPen()
        f_line_pen.setColor(QtGui.QColor(0, 0, 0, 40))
        if self.is_cc:
            f_labels = [0, '127', 0, '64', 0, '0']
        else:
            f_labels = [0, '1.0', 0, '0', 0, '-1.0']
        for i in range(1, 6):
            f_line = QtGui.QGraphicsLineItem(
                0, 0, self.viewer_width, 0, self.y_axis)
            f_line.setPos(self.axis_size, self.viewer_height * (i - 1) / 4)
            if i % 2:
                f_label = QtGui.QGraphicsSimpleTextItem(
                    f_labels[i], self.y_axis)
                f_label.setPos(1, self.viewer_height * (i - 1) / 4)
                f_label.setBrush(QtCore.Qt.white)
            if i == 3:
                f_line.setPen(f_beat_pen)

        for i in range(0, int(self.item_length) + 1):
            f_beat = QtGui.QGraphicsLineItem(
                0, 0, 0,
                self.viewer_height + self.axis_size-f_beat_pen.width(),
                self.x_axis)
            f_beat.setPos(self.beat_width * i, 0.5 * f_beat_pen.width())
            f_beat.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations)
            f_beat_number = i % 4
            if f_beat_number == 0 and not i == 0:
                f_beat.setPen(f_bar_pen)
                f_beat.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations)
            else:
                f_beat.setPen(f_beat_pen)
            if i < self.item_length:
                f_number = QtGui.QGraphicsSimpleTextItem(
                    str(f_beat_number + 1), self.x_axis)
                f_number.setFlag(
                    QtGui.QGraphicsItem.ItemIgnoresTransformations)
                f_number.setPos(self.beat_width * i + 5, 2)
                f_number.setBrush(QtCore.Qt.white)
                for j in range(0, 16):
                    f_line = QtGui.QGraphicsLineItem(
                        0, 0, 0, self.viewer_height, self.x_axis)
                    if float(j) == 8:
                        f_line.setLine(0, 0, 0, self.viewer_height)
                        f_line.setPos(
                            (self.beat_width * i) + (self.value_width * j),
                            self.axis_size)
                    else:
                        f_line.setPos((self.beat_width * i) +
                            (self.value_width * j), self.axis_size)
                        f_line.setPen(f_line_pen)

    def clear_drawn_items(self):
        self.selection_enabled = False
        self.scene.clear()
        self.automation_points = []
        self.lines = []
        self.draw_axis()
        self.draw_grid()
        self.selection_enabled = True

    def resizeEvent(self, a_event):
        QtGui.QGraphicsView.resizeEvent(self, a_event)
        ITEM_EDITOR.tab_changed()

    def set_scale(self):
        f_rect = self.rect()
        f_width = float(f_rect.width()) - self.verticalScrollBar().width() - \
            30.0 - AUTOMATION_RULER_WIDTH
        self.region_scale = f_width / (ITEM_EDITING_COUNT * 690.0)
        self.item_width = AUTOMATION_WIDTH * self.region_scale
        self.viewer_height = float(f_rect.height()) - \
            self.horizontalScrollBar().height() - \
            30.0 - AUTOMATION_RULER_WIDTH
        self.total_height = AUTOMATION_RULER_WIDTH + \
            self.viewer_height - AUTOMATION_POINT_RADIUS

    def set_cc_num(self, a_cc_num):
        self.cc_num = a_cc_num
        self.clear_drawn_items()
        self.draw_item()

    def draw_item(self):
        self.setUpdatesEnabled(False)
        self.set_scale()
        self.viewer_width = ITEM_EDITING_COUNT * self.item_width
        self.item_length = 4.0 * ITEM_EDITING_COUNT
        self.beat_width = self.viewer_width / self.item_length
        self.value_width = self.beat_width / 16.0
        self.grid_max_start_time = self.viewer_width + \
            AUTOMATION_RULER_WIDTH - AUTOMATION_POINT_RADIUS
        self.clear_drawn_items()
        if not ITEM_EDITOR.enabled:
            self.setUpdatesEnabled(True)
            return
        f_item_index = 0
        f_pen = QtGui.QPen(pydaw_note_gradient, 2.0)
        f_note_height = (self.viewer_height / 127.0)
        for f_item in ITEM_EDITOR.items:
            if self.is_cc:
                for f_cc in f_item.ccs:
                    if f_cc.cc_num == self.cc_num:
                        self.draw_point(f_cc, f_item_index)
            else:
                for f_pb in f_item.pitchbends:
                    self.draw_point(f_pb, f_item_index)
            for f_note in f_item.notes:
                f_note_start = (f_item_index *
                    self.item_width) + (f_note.start * 0.25 *
                    self.item_width) + AUTOMATION_RULER_WIDTH
                f_note_end = f_note_start + (f_note.length *
                    self.item_width * 0.25)
                f_note_y = AUTOMATION_RULER_WIDTH + ((127.0 -
                    (f_note.note_num)) * f_note_height)
                f_note_item = QtGui.QGraphicsLineItem(
                    f_note_start, f_note_y, f_note_end, f_note_y)
                f_note_item.setPen(f_pen)
                self.scene.addItem(f_note_item)
            f_item_index += 1
        self.setSceneRect(
            0.0, 0.0, self.grid_max_start_time + 100.0, self.height())
        self.setUpdatesEnabled(True)
        self.update()

    def draw_point(self, a_cc, a_item_index, a_select=True):
        """ a_cc is an instance of the pydaw_cc class"""
        f_time = self.axis_size + (((float(a_item_index) * 4.0) +
            a_cc.start) * self.beat_width)
        if self.is_cc:
            f_value = self.axis_size +  self.viewer_height / 127.0 * (127.0 -
                a_cc.cc_val)
        else:
            f_value = self.axis_size +  self.viewer_height / 2.0 * (1.0 -
                a_cc.pb_val)
        f_point = automation_item(
            f_time, f_value, a_cc, self, self.is_cc, a_item_index)
        self.automation_points.append(f_point)
        self.scene.addItem(f_point)
        if a_select and hash((a_item_index, str(a_cc))) in self.selected_str:
            f_point.setSelected(True)

    def select_all(self):
        self.setUpdatesEnabled(False)
        for f_item in self.automation_points:
            f_item.setSelected(True)
        self.setUpdatesEnabled(True)
        self.update()

LAST_IPB_VALUE = 18  #For the 'add point' dialog to remember settings

class automation_viewer_widget:
    def __init__(self, a_viewer, a_is_cc=True):
        self.is_cc = a_is_cc
        self.widget = QtGui.QGroupBox()
        self.vlayout = QtGui.QVBoxLayout()
        self.widget.setLayout(self.vlayout)
        self.automation_viewer = a_viewer
        self.vlayout.addWidget(self.automation_viewer)
        self.hlayout = QtGui.QHBoxLayout()

        if a_is_cc:
            self.control_combobox = QtGui.QComboBox()
            self.control_combobox.addItems([str(x) for x in range(1, 128)])
            self.control_combobox.setMinimumWidth(90)
            self.hlayout.addWidget(QtGui.QLabel(_("CC")))
            self.hlayout.addWidget(self.control_combobox)
            self.control_combobox.currentIndexChanged.connect(
                self.control_changed)
            self.ccs_in_use_combobox = QtGui.QComboBox()
            self.ccs_in_use_combobox.setMinimumWidth(90)
            self.suppress_ccs_in_use = False
            self.ccs_in_use_combobox.currentIndexChanged.connect(
                self.ccs_in_use_combobox_changed)
            self.hlayout.addWidget(QtGui.QLabel(_("In Use:")))
            self.hlayout.addWidget(self.ccs_in_use_combobox)

        self.vlayout.addLayout(self.hlayout)
        self.smooth_button = QtGui.QPushButton(_("Smooth"))
        self.smooth_button.setToolTip(
            _("By default, the control points are steppy, "
            "this button draws extra points between the exisiting points."))
        self.smooth_button.pressed.connect(self.smooth_pressed)
        self.hlayout.addWidget(self.smooth_button)
        self.hlayout.addItem(QtGui.QSpacerItem(10, 10))
        self.edit_button = QtGui.QPushButton(_("Menu"))
        self.hlayout.addWidget(self.edit_button)
        self.edit_menu = QtGui.QMenu(self.widget)
        self.copy_action = self.edit_menu.addAction(_("Copy"))
        self.copy_action.triggered.connect(
            self.automation_viewer.copy_selected)
        self.copy_action.setShortcut(QtGui.QKeySequence.Copy)
        self.cut_action = self.edit_menu.addAction(_("Cut"))
        self.cut_action.triggered.connect(self.automation_viewer.cut)
        self.cut_action.setShortcut(QtGui.QKeySequence.Cut)
        self.paste_action = self.edit_menu.addAction(_("Paste"))
        self.paste_action.triggered.connect(self.automation_viewer.paste)
        self.paste_action.setShortcut(QtGui.QKeySequence.Paste)
        self.select_all_action = self.edit_menu.addAction(_("Select All"))
        self.select_all_action.triggered.connect(self.select_all)
        self.select_all_action.setShortcut(QtGui.QKeySequence.SelectAll)
        self.delete_action = self.edit_menu.addAction(_("Delete"))
        self.delete_action.triggered.connect(
            self.automation_viewer.delete_selected)
        self.delete_action.setShortcut(QtGui.QKeySequence.Delete)

        self.edit_menu.addSeparator()
        self.add_point_action = self.edit_menu.addAction(_("Add Point..."))
        if self.is_cc:
            self.add_point_action.triggered.connect(self.add_cc_point)
            self.paste_point_action = self.edit_menu.addAction(
                _("Paste Point from Plugin..."))
            self.paste_point_action.triggered.connect(self.paste_cc_point)
        else:
            self.add_point_action.triggered.connect(self.add_pb_point)
        self.edit_menu.addSeparator()
        self.clear_action = self.edit_menu.addAction(_("Clear"))
        self.clear_action.triggered.connect(self.clear)
        self.edit_button.setMenu(self.edit_menu)
        self.hlayout.addItem(
            QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Expanding))

    def control_changed(self, a_val=None):
        self.set_cc_num()
        self.ccs_in_use_combobox.setCurrentIndex(0)

    def set_cc_num(self, a_val=None):
        f_cc_num = int(str(self.control_combobox.currentText()))
        self.automation_viewer.set_cc_num(f_cc_num)

    def ccs_in_use_combobox_changed(self, a_val=None):
        if not self.suppress_ccs_in_use:
            f_str = str(self.ccs_in_use_combobox.currentText())
            if f_str != "":
                self.control_combobox.setCurrentIndex(
                    self.control_combobox.findText(f_str))

    def update_ccs_in_use(self, a_ccs):
        self.suppress_ccs_in_use = True
        self.ccs_in_use_combobox.clear()
        self.ccs_in_use_combobox.addItem("")
        for f_cc in sorted(a_ccs):
            self.ccs_in_use_combobox.addItem(str(f_cc))
        self.suppress_ccs_in_use = False

    def smooth_pressed(self):
        if self.is_cc:
            f_cc_num = int(str(self.control_combobox.currentText()))
            pydaw_smooth_automation_points(
                ITEM_EDITOR.items, self.is_cc, f_cc_num)
        else:
            pydaw_smooth_automation_points(ITEM_EDITOR.items, self.is_cc)
        self.automation_viewer.selected_str = []
        global_save_and_reload_items()

    def select_all(self):
        self.automation_viewer.select_all()

    def clear(self):
        self.automation_viewer.clear_current_item()

    def paste_cc_point(self):
        if pydaw_widgets.CC_CLIPBOARD is None:
            QtGui.QMessageBox.warning(
                self.widget, _("Error"),
                _("Nothing copied to the clipboard.\n"
                "Right-click->'Copy' on any knob on any plugin."))
            return
        self.add_cc_point(pydaw_widgets.CC_CLIPBOARD)

    def add_cc_point(self, a_value=None):
        if not ITEM_EDITOR.enabled:  #TODO:  Make this global...
            ITEM_EDITOR.show_not_enabled_warning()
            return

        def ok_handler():
            f_bar = f_bar_spinbox.value() - 1
            f_item = ITEM_EDITOR.items[f_bar]

            f_cc = pydaw_cc(
                f_pos_spinbox.value() - 1.0, self.automation_viewer.cc_num,
                f_value_spinbox.value())
            f_item.add_cc(f_cc)

            PROJECT.save_item(
                ITEM_EDITOR.item_names[f_bar], ITEM_EDITOR.items[f_bar])
            global_open_items()
            PROJECT.commit(_("Add automation point"))

        def goto_start():
            f_bar_spinbox.setValue(f_bar_spinbox.minimum())
            f_pos_spinbox.setValue(f_pos_spinbox.minimum())

        def goto_end():
            f_bar_spinbox.setValue(f_bar_spinbox.maximum())
            f_pos_spinbox.setValue(f_pos_spinbox.maximum())

        def cancel_handler():
            f_window.close()

        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Add automation point"))
        f_layout = QtGui.QGridLayout()
        f_window.setLayout(f_layout)

        f_layout.addWidget(QtGui.QLabel(_("Position (bars)")), 2, 0)
        f_bar_spinbox = QtGui.QSpinBox()
        f_bar_spinbox.setRange(1, len(OPEN_ITEM_UIDS))
        f_layout.addWidget(f_bar_spinbox, 2, 1)

        f_layout.addWidget(QtGui.QLabel(_("Position (beats)")), 5, 0)
        f_pos_spinbox = QtGui.QDoubleSpinBox()
        f_pos_spinbox.setRange(1.0, 4.99)
        f_pos_spinbox.setDecimals(2)
        f_pos_spinbox.setSingleStep(0.25)
        f_layout.addWidget(f_pos_spinbox, 5, 1)

        f_begin_end_layout = QtGui.QHBoxLayout()
        f_layout.addLayout(f_begin_end_layout, 6, 1)
        f_start_button = QtGui.QPushButton("<<")
        f_start_button.pressed.connect(goto_start)
        f_begin_end_layout.addWidget(f_start_button)
        f_begin_end_layout.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))
        f_end_button = QtGui.QPushButton(">>")
        f_end_button.pressed.connect(goto_end)
        f_begin_end_layout.addWidget(f_end_button)

        f_layout.addWidget(QtGui.QLabel(_("Value")), 10, 0)
        f_value_spinbox = QtGui.QDoubleSpinBox()
        f_value_spinbox.setRange(0.0, 127.0)
        f_value_spinbox.setDecimals(4)
        if a_value is not None:
            f_value_spinbox.setValue(a_value)
        f_layout.addWidget(f_value_spinbox, 10, 1)

        f_ok = QtGui.QPushButton(_("Add"))
        f_ok.pressed.connect(ok_handler)
        f_ok_cancel_layout = QtGui.QHBoxLayout()
        f_ok_cancel_layout.addWidget(f_ok)

        f_layout.addLayout(f_ok_cancel_layout, 40, 1)
        f_cancel = QtGui.QPushButton(_("Close"))
        f_cancel.pressed.connect(cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel)
        f_window.exec_()

    def add_pb_point(self):
        if not ITEM_EDITOR.enabled:  #TODO:  Make this global...
            ITEM_EDITOR.show_not_enabled_warning()
            return

        def ok_handler():
            f_bar = f_bar_spinbox.value() - 1
            f_item = ITEM_EDITOR.items[f_bar]

            f_value = pydaw_clip_value(
                f_epb_spinbox.value() / f_ipb_spinbox.value(),
                -1.0, 1.0, a_round=True)
            f_pb = pydaw_pitchbend(f_pos_spinbox.value() - 1.0, f_value)
            f_item.add_pb(f_pb)

            global LAST_IPB_VALUE
            LAST_IPB_VALUE = f_ipb_spinbox.value()

            PROJECT.save_item(
                ITEM_EDITOR.item_names[f_bar], ITEM_EDITOR.items[f_bar])
            global_open_items()
            PROJECT.commit(_("Add pitchbend automation point"))

        def cancel_handler():
            f_window.close()

        def ipb_changed(a_self=None, a_event=None):
            f_epb_spinbox.setRange(
                f_ipb_spinbox.value() * -1, f_ipb_spinbox.value())

        def goto_start():
            f_bar_spinbox.setValue(f_bar_spinbox.minimum())
            f_pos_spinbox.setValue(f_pos_spinbox.minimum())

        def goto_end():
            f_bar_spinbox.setValue(f_bar_spinbox.maximum())
            f_pos_spinbox.setValue(f_pos_spinbox.maximum())

        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Add automation point"))
        f_layout = QtGui.QGridLayout()
        f_window.setLayout(f_layout)

        f_layout.addWidget(QtGui.QLabel(_("Position (bars)")), 2, 0)
        f_bar_spinbox = QtGui.QSpinBox()
        f_bar_spinbox.setRange(1, len(OPEN_ITEM_UIDS))
        f_layout.addWidget(f_bar_spinbox, 2, 1)

        f_layout.addWidget(QtGui.QLabel(_("Position (beats)")), 5, 0)
        f_pos_spinbox = QtGui.QDoubleSpinBox()
        f_pos_spinbox.setRange(1.0, 4.99)
        f_pos_spinbox.setDecimals(2)
        f_pos_spinbox.setSingleStep(0.25)
        f_layout.addWidget(f_pos_spinbox, 5, 1)

        f_begin_end_layout = QtGui.QHBoxLayout()
        f_layout.addLayout(f_begin_end_layout, 6, 1)
        f_start_button = QtGui.QPushButton("<<")
        f_start_button.pressed.connect(goto_start)
        f_begin_end_layout.addWidget(f_start_button)
        f_begin_end_layout.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))
        f_end_button = QtGui.QPushButton(">>")
        f_end_button.pressed.connect(goto_end)
        f_begin_end_layout.addWidget(f_end_button)

        f_layout.addWidget(QtGui.QLabel(_("Instrument Pitchbend")), 10, 0)
        f_ipb_spinbox = QtGui.QSpinBox()
        f_ipb_spinbox.setToolTip(
            _("Set this to the same setting that your instrument plugin uses"))
        f_ipb_spinbox.setRange(2, 36)
        f_ipb_spinbox.setValue(LAST_IPB_VALUE)
        f_layout.addWidget(f_ipb_spinbox, 10, 1)
        f_ipb_spinbox.valueChanged.connect(ipb_changed)

        f_layout.addWidget(QtGui.QLabel(_("Effective Pitchbend")), 20, 0)
        f_epb_spinbox = QtGui.QSpinBox()
        f_epb_spinbox.setToolTip("")
        f_epb_spinbox.setRange(-18, 18)
        f_layout.addWidget(f_epb_spinbox, 20, 1)

        f_layout.addWidget(QtGui.QLabel(
            libpydaw.strings.pitchbend_dialog), 30, 1)

        f_ok = QtGui.QPushButton(_("Add"))
        f_ok.pressed.connect(ok_handler)
        f_ok_cancel_layout = QtGui.QHBoxLayout()
        f_ok_cancel_layout.addWidget(f_ok)

        f_layout.addLayout(f_ok_cancel_layout, 40, 1)
        f_cancel = QtGui.QPushButton(_("Close"))
        f_cancel.pressed.connect(cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel)
        f_window.exec_()

OPEN_ITEM_UIDS = []
LAST_OPEN_ITEM_UIDS = []
OPEN_ITEM_NAMES = []
LAST_OPEN_ITEM_NAMES = []

def global_update_items_label():
    global OPEN_ITEM_UIDS
    ITEM_EDITOR.item_names = []
    f_items_dict = PROJECT.get_items_dict()
    for f_item_uid in OPEN_ITEM_UIDS:
        ITEM_EDITOR.item_names.append(f_items_dict.get_name_by_uid(f_item_uid))
    global_open_items()

def global_check_midi_items():
    """ Return True if OK, otherwise clear the the item
        editors and return False
    """
    f_items_dict = PROJECT.get_items_dict()
    f_invalid = False
    for f_uid in OPEN_ITEM_UIDS:
        if not f_items_dict.uid_exists(f_uid):
            f_invalid = True
            break
    if f_invalid:
        ITEM_EDITOR.clear_new()
        return False
    else:
        return True

DRAW_LAST_ITEMS = False
MIDI_SCALE = 1.0

def global_set_midi_zoom(a_val):
    global MIDI_SCALE
    MIDI_SCALE = a_val
    global_set_piano_roll_zoom()
    global_set_automation_zoom()


def global_open_items(a_items=None, a_reset_scrollbar=False):
    """ a_items is a list of str, which are the names of the items.
        Leave blank to open the existing list
    """
    if ITEM_EDITOR.items or a_items:
        ITEM_EDITOR.enabled = True
    global OPEN_ITEM_NAMES, OPEN_ITEM_UIDS, \
        LAST_OPEN_ITEM_UIDS, LAST_OPEN_ITEM_NAMES

    if a_items is not None:
        PIANO_ROLL_EDITOR.selected_note_strings = []
        global ITEM_EDITING_COUNT
        ITEM_EDITING_COUNT = len(a_items)
        global_set_piano_roll_zoom()
        ITEM_EDITOR.zoom_slider.setMaximum(100 * ITEM_EDITING_COUNT)
        ITEM_EDITOR.zoom_slider.setSingleStep(ITEM_EDITING_COUNT)
        pydaw_set_piano_roll_quantize(
            PIANO_ROLL_EDITOR_WIDGET.snap_combobox.currentIndex())
        ITEM_EDITOR.item_names = a_items
        ITEM_EDITOR.item_index_enabled = False
        ITEM_EDITOR.item_name_combobox.clear()
        ITEM_EDITOR.item_name_combobox.clearEditText()
        ITEM_EDITOR.item_name_combobox.addItems(a_items)
        ITEM_EDITOR.item_name_combobox.setCurrentIndex(0)
        ITEM_EDITOR.item_index_enabled = True
        if a_reset_scrollbar:
            for f_editor in MIDI_EDITORS:
                f_editor.horizontalScrollBar().setSliderPosition(0)
        LAST_OPEN_ITEM_NAMES = OPEN_ITEM_NAMES
        OPEN_ITEM_NAMES = a_items[:]
        f_items_dict = PROJECT.get_items_dict()
        LAST_OPEN_ITEM_UIDS = OPEN_ITEM_UIDS[:]
        OPEN_ITEM_UIDS = []
        for f_item_name in a_items:
            OPEN_ITEM_UIDS.append(
                f_items_dict.get_uid_by_name(f_item_name))

    CC_EDITOR.clear_drawn_items()
    PB_EDITOR.clear_drawn_items()
    ITEM_EDITOR.items = []
    f_cc_set = set()

    for f_item_uid in OPEN_ITEM_UIDS:
        f_item = PROJECT.get_item_by_uid(f_item_uid)
        ITEM_EDITOR.items.append(f_item)
        for cc in f_item.ccs:
            f_cc_set.add(cc.cc_num)

    CC_EDITOR_WIDGET.update_ccs_in_use(list(f_cc_set))

    if a_items is not None and f_cc_set:
        CC_EDITOR_WIDGET.set_cc_num(sorted(f_cc_set)[0])

    ITEM_EDITOR.tab_changed()
    if ITEM_EDITOR.items:
        ITEM_EDITOR.open_item_list()

def global_save_and_reload_items():
    assert(len(ITEM_EDITOR.item_names) == len(ITEM_EDITOR.items))
    for f_i in range(len(ITEM_EDITOR.item_names)):
        PROJECT.save_item(
            ITEM_EDITOR.item_names[f_i], ITEM_EDITOR.items[f_i])
    global_open_items()
    PROJECT.commit(_("Edit item(s)"))


class item_list_editor:
    def __init__(self):
        self.enabled = False
        self.items = []
        self.item_names = []
        self.events_follow_default = True

        self.widget = QtGui.QWidget()
        self.master_vlayout = QtGui.QVBoxLayout()
        self.widget.setLayout(self.master_vlayout)

        self.tab_widget = QtGui.QTabWidget()
        self.piano_roll_tab = QtGui.QGroupBox()
        self.tab_widget.addTab(self.piano_roll_tab, _("Piano Roll"))
        self.notes_tab = QtGui.QGroupBox()
        self.cc_tab = QtGui.QGroupBox()
        self.tab_widget.addTab(self.cc_tab, _("CC"))

        self.pitchbend_tab = QtGui.QGroupBox()
        self.tab_widget.addTab(self.pitchbend_tab, _("Pitchbend"))

        self.editing_hboxlayout = QtGui.QHBoxLayout()
        self.master_vlayout.addWidget(self.tab_widget)

        self.notes_groupbox = QtGui.QGroupBox(_("Notes"))
        self.notes_vlayout = QtGui.QVBoxLayout(self.notes_groupbox)

        self.cc_vlayout = QtGui.QVBoxLayout()
        self.cc_tab.setLayout(self.cc_vlayout)

        self.editing_hboxlayout.addWidget(QtGui.QLabel(_("Viewing Item:")))
        self.item_name_combobox = QtGui.QComboBox()
        self.item_name_combobox.setMinimumWidth(150)
        self.item_name_combobox.setEditable(False)
        self.item_name_combobox.currentIndexChanged.connect(
            self.item_index_changed)
        self.item_index_enabled = True
        self.editing_hboxlayout.addWidget(self.item_name_combobox)
        self.editing_hboxlayout.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))

        self.notes_table_widget = QtGui.QTableWidget()
        self.notes_table_widget.setVerticalScrollMode(
            QtGui.QAbstractItemView.ScrollPerPixel)
        self.notes_table_widget.setColumnCount(5)
        self.notes_table_widget.setRowCount(256)
        self.notes_table_widget.setSortingEnabled(True)
        self.notes_table_widget.sortItems(0)
        self.notes_table_widget.setEditTriggers(
            QtGui.QAbstractItemView.NoEditTriggers)
        self.notes_table_widget.setSelectionBehavior(
            QtGui.QAbstractItemView.SelectRows)
        self.notes_vlayout.addWidget(self.notes_table_widget)
        self.notes_table_widget.resizeColumnsToContents()

        self.notes_hlayout = QtGui.QHBoxLayout()
        self.list_tab_vlayout = QtGui.QVBoxLayout()
        self.notes_tab.setLayout(self.list_tab_vlayout)
        self.list_tab_vlayout.addLayout(self.editing_hboxlayout)
        self.list_tab_vlayout.addLayout(self.notes_hlayout)
        self.notes_hlayout.addWidget(self.notes_groupbox)

        self.piano_roll_hlayout = QtGui.QHBoxLayout(self.piano_roll_tab)
        self.piano_roll_hlayout.setMargin(2)
        self.piano_roll_hlayout.addWidget(PIANO_ROLL_EDITOR_WIDGET.widget)

        self.ccs_groupbox = QtGui.QGroupBox(_("CCs"))
        self.ccs_vlayout = QtGui.QVBoxLayout(self.ccs_groupbox)

        self.ccs_table_widget = QtGui.QTableWidget()
        self.ccs_table_widget.setVerticalScrollMode(
            QtGui.QAbstractItemView.ScrollPerPixel)
        self.ccs_table_widget.setColumnCount(3)
        self.ccs_table_widget.setRowCount(256)
        self.ccs_table_widget.setSortingEnabled(True)
        self.ccs_table_widget.sortItems(0)
        self.ccs_table_widget.setEditTriggers(
            QtGui.QAbstractItemView.NoEditTriggers)
        self.ccs_table_widget.setSelectionBehavior(
            QtGui.QAbstractItemView.SelectRows)
        self.ccs_table_widget.resizeColumnsToContents()
        self.ccs_vlayout.addWidget(self.ccs_table_widget)
        self.notes_hlayout.addWidget(self.ccs_groupbox)

        self.cc_vlayout.addWidget(CC_EDITOR_WIDGET.widget)

        self.pb_hlayout = QtGui.QHBoxLayout()
        self.pitchbend_tab.setLayout(self.pb_hlayout)
        self.pb_groupbox = QtGui.QGroupBox(_("Pitchbend"))
        self.pb_groupbox.setFixedWidth(240)
        self.pb_vlayout = QtGui.QVBoxLayout(self.pb_groupbox)

        self.pitchbend_table_widget = QtGui.QTableWidget()
        self.pitchbend_table_widget.setVerticalScrollMode(
            QtGui.QAbstractItemView.ScrollPerPixel)
        self.pitchbend_table_widget.setColumnCount(2)
        self.pitchbend_table_widget.setRowCount(256)
        self.pitchbend_table_widget.setSortingEnabled(True)
        self.pitchbend_table_widget.sortItems(0)
        self.pitchbend_table_widget.setEditTriggers(
            QtGui.QAbstractItemView.NoEditTriggers)
        self.pitchbend_table_widget.setSelectionBehavior(
            QtGui.QAbstractItemView.SelectRows)
        self.pitchbend_table_widget.resizeColumnsToContents()
        self.pb_vlayout.addWidget(self.pitchbend_table_widget)
        self.notes_hlayout.addWidget(self.pb_groupbox)
        self.pb_auto_vlayout = QtGui.QVBoxLayout()
        self.pb_hlayout.addLayout(self.pb_auto_vlayout)
        self.pb_viewer_widget = automation_viewer_widget(PB_EDITOR, False)
        self.pb_auto_vlayout.addWidget(self.pb_viewer_widget.widget)

        self.tab_widget.addTab(self.notes_tab, _("List Viewers"))

        self.zoom_widget = QtGui.QWidget()
        self.zoom_widget.setContentsMargins(0, 0, 0, 0)
        self.zoom_hlayout = QtGui.QHBoxLayout(self.zoom_widget)
        self.zoom_hlayout.setMargin(0)
        self.zoom_hlayout.setSpacing(0)

        self.zoom_hlayout.addWidget(QtGui.QLabel("V"))
        self.vzoom_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.zoom_hlayout.addWidget(self.vzoom_slider)
        self.vzoom_slider.setObjectName("zoom_slider")
        self.vzoom_slider.setRange(9, 24)
        self.vzoom_slider.setValue(PIANO_ROLL_NOTE_HEIGHT)
        self.vzoom_slider.valueChanged.connect(self.set_midi_vzoom)
        self.vzoom_slider.sliderReleased.connect(self.save_vzoom)

        self.zoom_hlayout.addWidget(QtGui.QLabel("H"))
        self.zoom_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.zoom_hlayout.addWidget(self.zoom_slider)
        self.zoom_slider.setObjectName("zoom_slider")
        self.zoom_slider.setRange(10, 100)
        self.zoom_slider.valueChanged.connect(self.set_midi_zoom)
        self.tab_widget.setCornerWidget(self.zoom_widget)
        self.tab_widget.currentChanged.connect(self.tab_changed)

        self.set_headers()
        self.default_note_start = 0.0
        self.default_note_length = 1.0
        self.default_note_note = 0
        self.default_note_octave = 3
        self.default_note_velocity = 100
        self.default_cc_num = 0
        self.default_cc_start = 0.0
        self.default_cc_val = 0
        self.default_quantize = 5
        self.default_pb_start = 0
        self.default_pb_val = 0
        self.default_pb_quantize = 0


    def clear_new(self):
        self.enabled = False
        self.ccs_table_widget.clearContents()
        self.notes_table_widget.clearContents()
        self.pitchbend_table_widget.clearContents()
        PIANO_ROLL_EDITOR.clear_drawn_items()
        self.item = None
        self.items = []

    def quantize_dialog(self, a_selected_only=False):
        if not self.enabled:
            self.show_not_enabled_warning()
            return

        def quantize_ok_handler():
            f_quantize_text = f_quantize_combobox.currentText()
            self.events_follow_default = f_events_follow_notes.isChecked()
            f_clip = []
            for f_i in range(len(self.items)):
                f_clip += self.items[f_i].quantize(f_quantize_text,
                    f_events_follow_notes.isChecked(),
                    a_selected_only=f_selected_only.isChecked(), a_index=f_i)
                PROJECT.save_item(self.item_names[f_i], self.items[f_i])

            if f_selected_only.isChecked():
                PIANO_ROLL_EDITOR.selected_note_strings = f_clip
            else:
                PIANO_ROLL_EDITOR.selected_note_strings = []

            global_open_items()
            PROJECT.commit(_("Quantize item(s)"))
            f_window.close()

        def quantize_cancel_handler():
            f_window.close()

        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Quantize"))
        f_layout = QtGui.QGridLayout()
        f_window.setLayout(f_layout)

        f_layout.addWidget(QtGui.QLabel(_("Quantize")), 0, 0)
        f_quantize_combobox = QtGui.QComboBox()
        f_quantize_combobox.addItems(bar_fracs)
        f_layout.addWidget(f_quantize_combobox, 0, 1)
        f_events_follow_notes = QtGui.QCheckBox(
            _("CCs and pitchbend follow notes?"))
        f_events_follow_notes.setChecked(self.events_follow_default)
        f_layout.addWidget(f_events_follow_notes, 1, 1)
        f_ok = QtGui.QPushButton(_("OK"))
        f_ok.pressed.connect(quantize_ok_handler)
        f_ok_cancel_layout = QtGui.QHBoxLayout()
        f_ok_cancel_layout.addWidget(f_ok)

        f_selected_only = QtGui.QCheckBox(_("Selected Notes Only?"))
        f_selected_only.setChecked(a_selected_only)
        f_layout.addWidget(f_selected_only, 2, 1)

        f_layout.addLayout(f_ok_cancel_layout, 3, 1)
        f_cancel = QtGui.QPushButton(_("Cancel"))
        f_cancel.pressed.connect(quantize_cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel)
        f_window.exec_()

    def velocity_dialog(self, a_selected_only=False):
        if not self.enabled:
            self.show_not_enabled_warning()
            return

        def ok_handler():
            if f_draw_line.isChecked() and \
            not f_add_values.isChecked() and \
            f_end_amount.value() < 1:
                QtGui.QMessageBox.warning(
                    f_window, _("Error"),
                    _("Cannot have end value less than 1 if not using "
                    "'Add Values'"))
                return

            f_clip = pydaw_velocity_mod(
                self.items, f_amount.value(), f_draw_line.isChecked(),
                f_end_amount.value(), f_add_values.isChecked(),
                a_selected_only=f_selected_only.isChecked())
            print(f_clip)
            print(PIANO_ROLL_EDITOR.selected_note_strings)
            if f_selected_only.isChecked():
                PIANO_ROLL_EDITOR.selected_note_strings = f_clip
            else:
                PIANO_ROLL_EDITOR.selected_note_strings = []
            for f_i in range(ITEM_EDITING_COUNT):
                PROJECT.save_item(self.item_names[f_i], self.items[f_i])
            global_open_items()
            PROJECT.commit(_("Velocity mod item(s)"))
            f_window.close()

        def cancel_handler():
            f_window.close()

        def end_value_changed(a_val=None):
            f_draw_line.setChecked(True)

        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Velocity Mod"))
        f_layout = QtGui.QGridLayout()
        f_window.setLayout(f_layout)

        f_layout.addWidget(QtGui.QLabel(_("Amount")), 0, 0)
        f_amount = QtGui.QSpinBox()
        f_amount.setRange(-127, 127)
        f_amount.setValue(100)
        f_layout.addWidget(f_amount, 0, 1)
        f_draw_line = QtGui.QCheckBox(_("Draw line?"))
        f_layout.addWidget(f_draw_line, 1, 1)

        f_layout.addWidget(QtGui.QLabel(_("End Amount")), 2, 0)
        f_end_amount = QtGui.QSpinBox()
        f_end_amount.setRange(-127, 127)
        f_end_amount.valueChanged.connect(end_value_changed)
        f_layout.addWidget(f_end_amount, 2, 1)

        f_add_values = QtGui.QCheckBox(_("Add Values?"))
        f_add_values.setToolTip(
            _("Check this to add Amount to the existing value, or leave\n"
            "unchecked to set the value to Amount."))
        f_layout.addWidget(f_add_values, 5, 1)

        f_selected_only = QtGui.QCheckBox(_("Selected Notes Only?"))
        f_selected_only.setChecked(a_selected_only)
        f_layout.addWidget(f_selected_only, 6, 1)

        f_ok = QtGui.QPushButton(_("OK"))
        f_ok.pressed.connect(ok_handler)
        f_ok_cancel_layout = QtGui.QHBoxLayout()
        f_ok_cancel_layout.addWidget(f_ok)
        f_layout.addLayout(f_ok_cancel_layout, 10, 1)
        f_cancel = QtGui.QPushButton(_("Cancel"))
        f_cancel.pressed.connect(cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel)
        f_window.exec_()

    def transpose_dialog(self, a_selected_only=False):
        if not self.enabled:
            self.show_not_enabled_warning()
            return

        def transpose_ok_handler():
            f_clip = []

            for f_i in range(len(self.items)):
                f_clip += self.items[f_i].transpose(
                    f_semitone.value(), f_octave.value(),
                    a_selected_only=f_selected_only.isChecked(),
                    a_duplicate=f_duplicate_notes.isChecked(), a_index=f_i)
                PROJECT.save_item(self.item_names[f_i], self.items[f_i])

            if f_selected_only.isChecked():
                PIANO_ROLL_EDITOR.selected_note_strings = f_clip
            else:
                PIANO_ROLL_EDITOR.selected_note_strings = []

            global_open_items()
            PROJECT.commit(_("Transpose item(s)"))
            f_window.close()

        def transpose_cancel_handler():
            f_window.close()

        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setWindowTitle(_("Transpose"))
        f_layout = QtGui.QGridLayout()
        f_window.setLayout(f_layout)

        f_semitone = QtGui.QSpinBox()
        f_semitone.setRange(-12, 12)
        f_layout.addWidget(QtGui.QLabel(_("Semitones")), 0, 0)
        f_layout.addWidget(f_semitone, 0, 1)
        f_octave = QtGui.QSpinBox()
        f_octave.setRange(-5, 5)
        f_layout.addWidget(QtGui.QLabel(_("Octaves")), 1, 0)
        f_layout.addWidget(f_octave, 1, 1)
        f_duplicate_notes = QtGui.QCheckBox(_("Duplicate notes?"))
        f_duplicate_notes.setToolTip(
            _("Checking this box causes the transposed notes "
            "to be added rather than moving the existing notes."))
        f_layout.addWidget(f_duplicate_notes, 2, 1)
        f_selected_only = QtGui.QCheckBox(_("Selected Notes Only?"))
        f_selected_only.setChecked(a_selected_only)
        f_layout.addWidget(f_selected_only, 4, 1)
        f_ok_cancel_layout = QtGui.QHBoxLayout()
        f_layout.addLayout(f_ok_cancel_layout, 6, 1)
        f_ok = QtGui.QPushButton(_("OK"))
        f_ok.pressed.connect(transpose_ok_handler)
        f_ok_cancel_layout.addWidget(f_ok)
        f_cancel = QtGui.QPushButton(_("Cancel"))
        f_cancel.pressed.connect(transpose_cancel_handler)
        f_ok_cancel_layout.addWidget(f_cancel)
        f_window.exec_()

    def tab_changed(self, a_val=None):
        f_list = [PIANO_ROLL_EDITOR, CC_EDITOR, PB_EDITOR]
        f_index = self.tab_widget.currentIndex()
        if f_index == 0:
            global_set_piano_roll_zoom()
        if f_index < len(f_list):
            f_list[f_index].draw_item()
        PIANO_ROLL_EDITOR.click_enabled = True
        #^^^^huh?

    def show_not_enabled_warning(self):
        QtGui.QMessageBox.warning(
            MAIN_WINDOW, _("Error"),
           _("You must open an item first by double-clicking on one in "
           "the region editor on the 'Song/Region' tab."))

    def item_index_changed(self, a_index=None):
        if self.item_index_enabled:
            self.open_item_list()

    def set_midi_vzoom(self, a_val):
        global PIANO_ROLL_NOTE_HEIGHT
        PIANO_ROLL_NOTE_HEIGHT = a_val
        global_open_items()

    def save_vzoom(self):
        pydaw_util.set_file_setting("PIANO_VZOOM", self.vzoom_slider.value())

    def set_midi_zoom(self, a_val):
        global_set_midi_zoom(a_val * 0.1)
        global_open_items()

    def set_headers(self): #Because clearing the table clears the headers
        self.notes_table_widget.setHorizontalHeaderLabels(
            [_('Start'), _('Length'), _('Note'), _('Note#'), _('Velocity')])
        self.ccs_table_widget.setHorizontalHeaderLabels(
            [_('Start'), _('Control'), _('Value')])
        self.pitchbend_table_widget.setHorizontalHeaderLabels(
            [_('Start'), _('Value')])

    def set_row_counts(self):
        self.notes_table_widget.setRowCount(256)
        self.ccs_table_widget.setRowCount(256)
        self.pitchbend_table_widget.setRowCount(256)

    def add_cc(self, a_cc):
        f_index, f_start = pydaw_beats_to_index(a_cc.start)
        a_cc.start = f_start
        self.items[f_index].add_cc(a_cc)
        return f_index

    def add_note(self, a_note):
        f_index, f_start = pydaw_beats_to_index(a_note.start)
        a_note.start = f_start
        self.items[f_index].add_note(a_note, False)
        return f_index

    def add_pb(self, a_pb):
        f_index, f_start = pydaw_beats_to_index(a_pb.start)
        a_pb.start = f_start
        self.items[f_index].add_pb(a_pb)
        return f_index

    def open_item_list(self):
        self.notes_table_widget.clear()
        self.ccs_table_widget.clear()
        self.pitchbend_table_widget.clear()
        self.set_headers()
        self.item_name = self.item_names[
            self.item_name_combobox.currentIndex()]
        self.item = PROJECT.get_item_by_name(self.item_name)
        self.notes_table_widget.setSortingEnabled(False)

        for note, f_i in zip(self.item.notes, range(len(self.item.notes))):
            f_note_str = note_num_to_string(note.note_num)
            self.notes_table_widget.setItem(
                f_i, 0, QtGui.QTableWidgetItem(str(note.start)))
            self.notes_table_widget.setItem(
                f_i, 1, QtGui.QTableWidgetItem(str(note.length)))
            self.notes_table_widget.setItem(
                f_i, 2, QtGui.QTableWidgetItem(f_note_str))
            self.notes_table_widget.setItem(
                f_i, 3, QtGui.QTableWidgetItem(str(note.note_num)))
            self.notes_table_widget.setItem(
                f_i, 4, QtGui.QTableWidgetItem(str(note.velocity)))
        self.notes_table_widget.setSortingEnabled(True)
        self.ccs_table_widget.setSortingEnabled(False)

        for cc, f_i in zip(self.item.ccs, range(len(self.item.ccs))):
            self.ccs_table_widget.setItem(
                f_i, 0, QtGui.QTableWidgetItem(str(cc.start)))
            self.ccs_table_widget.setItem(
                f_i, 1, QtGui.QTableWidgetItem(str(cc.cc_num)))
            self.ccs_table_widget.setItem(
                f_i, 2, QtGui.QTableWidgetItem(str(cc.cc_val)))
        self.ccs_table_widget.setSortingEnabled(True)
        self.pitchbend_table_widget.setSortingEnabled(False)

        for pb, f_i in zip(
        self.item.pitchbends, range(len(self.item.pitchbends))):
            self.pitchbend_table_widget.setItem(
                f_i, 0, QtGui.QTableWidgetItem(str(pb.start)))
            self.pitchbend_table_widget.setItem(
                f_i, 1, QtGui.QTableWidgetItem(str(pb.pb_val)))
        self.pitchbend_table_widget.setSortingEnabled(True)
        self.notes_table_widget.resizeColumnsToContents()
        self.ccs_table_widget.resizeColumnsToContents()
        self.pitchbend_table_widget.resizeColumnsToContents()


class midi_device:
    def __init__(self, a_name, a_index, a_layout, a_save_callback):
        self.name = str(a_name)
        self.index = int(a_index)
        self.save_callback = a_save_callback
        self.record_checkbox = QtGui.QCheckBox()
        self.record_checkbox.toggled.connect(self.device_changed)
        f_index = int(a_index) + 1
        a_layout.addWidget(self.record_checkbox, f_index, 0)
        a_layout.addWidget(QtGui.QLabel(a_name), f_index, 1)
        self.track_combobox = QtGui.QComboBox()
        self.track_combobox.setMinimumWidth(180)
        self.track_combobox.addItems(TRACK_NAMES)
        AUDIO_TRACK_COMBOBOXES.append(self.track_combobox)
        self.track_combobox.currentIndexChanged.connect(self.device_changed)
        a_layout.addWidget(self.track_combobox, f_index, 2)

    def device_changed(self, a_val=None):
        if SUPPRESS_TRACK_COMBOBOX_CHANGES:
            return
        PROJECT.en_osc.pydaw_midi_device(
            self.record_checkbox.isChecked(), self.index,
            self.track_combobox.currentIndex())
        self.save_callback()

    def get_routing(self):
        return pydaw_midi_route(
            1 if self.record_checkbox.isChecked() else 0,
            self.track_combobox.currentIndex(), self.name)

    def set_routing(self, a_routing):
        self.track_combobox.setCurrentIndex(a_routing.track_num)
        self.record_checkbox.setChecked(a_routing.on)

class midi_devices_dialog:
    def __init__(self):
        self.layout = QtGui.QGridLayout()
        if not pydaw_util.MIDI_IN_DEVICES:
            return
        self.layout.addWidget(QtGui.QLabel(_("On")), 0, 0)
        self.layout.addWidget(QtGui.QLabel(_("MIDI Device")), 0, 1)
        self.layout.addWidget(QtGui.QLabel(_("Output")), 0, 2)
        self.devices = []
        self.devices_dict = {}
        for f_name, f_i in zip(
        pydaw_util.MIDI_IN_DEVICES, range(len(pydaw_util.MIDI_IN_DEVICES))):
            f_device = midi_device(
                f_name, f_i, self.layout, self.save_callback)
            self.devices.append(f_device)
            self.devices_dict[f_name] = f_device

    def get_routings(self):
        return pydaw_midi_routings([x.get_routing() for x in self.devices])

    def save_callback(self):
        PROJECT.save_midi_routing(self.get_routings())

    def on_ready(self):
        self.set_routings()

    def set_routings(self):
        f_routings = PROJECT.get_midi_routing()
        for f_routing in f_routings.routings:
            if f_routing.device_name in self.devices_dict:
                self.devices_dict[f_routing.device_name].set_routing(f_routing)


def global_open_mixer():
    f_graph = PROJECT.get_routing_graph()
    f_track_names = {
        f_i:x for f_i, x in zip(range(len(TRACK_NAMES)), TRACK_NAMES)}
    f_plugins = {}
    for k in f_track_names:
        f_track_plugins = PROJECT.get_track_plugins(k)
        if f_track_plugins:
            f_plugins[k] = {x.index:x for x in f_track_plugins.plugins}
    MIXER_WIDGET.clear()
    for f_track_index, f_send_dict in f_graph.graph.items():
        for k, f_send in f_send_dict.items():
            f_send_plugin_index = k + 10
            if f_track_index in f_plugins and \
            f_send_plugin_index in f_plugins[f_track_index]:
                f_plugin_obj = f_plugins[f_track_index][f_send_plugin_index]
                if f_plugin_obj.plugin_index == 0:  # None
                    continue
                f_plugin_ui = libmk.PLUGIN_UI_DICT.open_plugin_ui(
                    f_plugin_obj.plugin_uid, f_plugin_obj.plugin_index,
                    "Track:  {}".format(f_track_index), False)
                MIXER_WIDGET.set_plugin_widget(
                    f_track_index, k, f_send.output, f_plugin_ui)
    MIXER_WIDGET.update_track_names(
        {f_i:x for f_i, x in zip(
        range(len(TRACK_NAMES)), TRACK_NAMES)})


class seq_track:
    def __init__(self, a_track_num, a_track_text=_("track")):
        self.suppress_osc = True
        self.automation_uid = None
        self.automation_plugin = None
        self.track_number = a_track_num
        self.group_box = QtGui.QWidget()
        self.group_box.setFixedHeight(REGION_EDITOR_TRACK_HEIGHT)
        self.group_box.contextMenuEvent = self.context_menu_event
        self.group_box.setObjectName("track_panel")
        self.main_hlayout = QtGui.QHBoxLayout()
        self.main_hlayout.setContentsMargins(2, 2, 2, 2)
        self.main_vlayout = QtGui.QVBoxLayout()
        self.main_hlayout.addLayout(self.main_vlayout)
        self.peak_meter = pydaw_widgets.peak_meter()
        if a_track_num in ALL_PEAK_METERS:
            ALL_PEAK_METERS[a_track_num].append(self.peak_meter)
        else:
            ALL_PEAK_METERS[a_track_num] = [self.peak_meter]
        self.main_hlayout.addWidget(self.peak_meter.widget)
        self.group_box.setLayout(self.main_hlayout)
        self.track_name_lineedit = QtGui.QLineEdit()
        if a_track_num == 0:
            self.track_name_lineedit.setText("Master")
            self.track_name_lineedit.setDisabled(True)
        else:
            self.track_name_lineedit.setText(a_track_text)
            self.track_name_lineedit.setMaxLength(48)
            self.track_name_lineedit.editingFinished.connect(
                self.on_name_changed)
        self.main_vlayout.addWidget(self.track_name_lineedit)
        self.hlayout3 = QtGui.QHBoxLayout()
        self.main_vlayout.addLayout(self.hlayout3)

        self.menu_button = QtGui.QPushButton()
        self.menu_button.setFixedWidth(42)
        self.button_menu = QtGui.QMenu()
        self.menu_button.setMenu(self.button_menu)
        self.hlayout3.addWidget(self.menu_button)
        self.button_menu.aboutToShow.connect(self.menu_button_pressed)
        self.menu_created = False
        self.solo_checkbox = QtGui.QCheckBox()
        self.mute_checkbox = QtGui.QCheckBox()
        if self.track_number == 0:
            self.hlayout3.addItem(
                QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))
        else:
            self.solo_checkbox.stateChanged.connect(self.on_solo)
            self.solo_checkbox.setObjectName("solo_checkbox")
            self.hlayout3.addWidget(self.solo_checkbox)
            self.mute_checkbox.stateChanged.connect(self.on_mute)
            self.mute_checkbox.setObjectName("mute_checkbox")
            self.hlayout3.addWidget(self.mute_checkbox)
        self.plugins = []
        self.action_widget = None
        self.automation_plugin_name = "None"
        self.port_num = None
        self.ccs_in_use_combobox = None
        self.suppress_osc = False

    def menu_button_pressed(self):
        if not self.menu_created:
            self.create_menu()
        for f_send in self.sends:
            f_send.update_names(TRACK_NAMES)
        self.open_plugins()
        self.update_in_use_combobox()

    def create_menu(self):
        self.plugins = []
        if self.action_widget:
            self.button_menu.removeAction(self.action_widget)
        self.menu_created = True
        self.menu_widget = QtGui.QWidget()
        self.menu_hlayout = QtGui.QHBoxLayout(self.menu_widget)
        self.menu_gridlayout = QtGui.QGridLayout()
        self.menu_hlayout.addLayout(self.menu_gridlayout)
        self.plugins_button = QtGui.QPushButton(_("Plugins"))
        self.plugins_menu = QtGui.QMenu(self.menu_widget)
        self.plugins_button.setMenu(self.plugins_menu)
        self.plugins_order_action = self.plugins_menu.addAction(_("Order..."))
        self.plugins_order_action.triggered.connect(self.set_plugin_order)
        self.menu_gridlayout.addWidget(self.plugins_button, 0, 0)
        self.menu_gridlayout.addWidget(QtGui.QLabel(_("A")), 0, 2)
        self.menu_gridlayout.addWidget(QtGui.QLabel(_("P")), 0, 3)
        for f_i in range(10):
            f_plugin = plugin_settings_main(
                PROJECT.en_osc.pydaw_set_plugin,
                f_i, self.track_number, self.menu_gridlayout,
                self.save_callback, self.name_callback,
                self.automation_callback)
            self.plugins.append(f_plugin)
        self.sends = []
        if self.track_number != 0:
            self.menu_gridlayout.addWidget(
                QtGui.QLabel(_("Sends")), 0, 20)
            self.menu_gridlayout.addWidget(
                QtGui.QLabel(_("Mixer Plugin")), 0, 21)
            self.menu_gridlayout.addWidget(
                QtGui.QLabel(_("Sidechain")), 0, 27)
            self.menu_gridlayout.addWidget(QtGui.QLabel(_("A")), 0, 23)
            self.menu_gridlayout.addWidget(QtGui.QLabel(_("P")), 0, 24)
            for f_i in range(4):
                f_send = track_send(
                    f_i, self.track_number, self.menu_gridlayout,
                    self.save_callback,PROJECT.get_routing_graph,
                    PROJECT.save_routing_graph, TRACK_NAMES)
                self.sends.append(f_send)
                f_plugin = plugin_settings_mixer(
                    PROJECT.en_osc.pydaw_set_plugin,
                    f_i, self.track_number, self.menu_gridlayout,
                    self.save_callback, self.name_callback,
                    self.automation_callback, a_offset=21, a_send=f_send)
                self.plugins.append(f_plugin)
        self.action_widget = QtGui.QWidgetAction(self.button_menu)
        self.action_widget.setDefaultWidget(self.menu_widget)
        self.button_menu.addAction(self.action_widget)

        self.control_combobox = QtGui.QComboBox()
        self.control_combobox.setMinimumWidth(240)
        self.menu_gridlayout.addWidget(QtGui.QLabel(_("Automation:")), 9, 20)
        self.menu_gridlayout.addWidget(self.control_combobox, 9, 21)
        self.control_combobox.currentIndexChanged.connect(
            self.control_changed)
        self.ccs_in_use_combobox = QtGui.QComboBox()
        self.ccs_in_use_combobox.setMinimumWidth(300)
        self.suppress_ccs_in_use = False
        self.ccs_in_use_combobox.currentIndexChanged.connect(
            self.ccs_in_use_combobox_changed)
        self.menu_gridlayout.addWidget(QtGui.QLabel(_("In Use:")), 10, 20)
        self.menu_gridlayout.addWidget(self.ccs_in_use_combobox, 10, 21)

    def set_plugin_order(self):
        f_labels = ["{} : {}".format(f_i, x.plugin_combobox.currentText())
            for f_i, x in zip(range(1, 11), self.plugins)]
        f_result = pydaw_widgets.ordered_table_dialog(
            f_labels, self.plugins, 30, 200, MAIN_WINDOW)
        if f_result:
            for f_plugin in self.plugins:
                f_plugin.remove_from_layout()
            for f_i, f_plugin in zip(range(len(f_result)), f_result):
                f_plugin.index = f_i
                f_plugin.on_plugin_change(a_save=False)
                f_plugin.add_to_layout()
            self.plugins[0:len(f_result)] = f_result
            self.save_callback()
            self.create_menu()
            self.open_plugins()

    def refresh(self):
        self.track_name_lineedit.setText(TRACK_NAMES[self.track_number])
        if self.menu_created:
            for f_plugin in self.plugins:
                f_plugin.remove_from_layout()
            self.create_menu()
            self.open_plugins()

    def get_plugin_uids(self):
        return [x.plugin_uid for x in self.plugins if x.plugin_uid != -1]

    def plugin_changed(self, a_val=None):
        self.control_combobox.clear()
        if self.automation_plugin_name != "None":
            self.control_combobox.addItems(
                CC_NAMES[self.automation_plugin_name])
        TRACK_PANEL.update_plugin_track_map()

    def control_changed(self, a_val=None):
        self.set_cc_num()
        self.ccs_in_use_combobox.setCurrentIndex(0)
        if not libmk.IS_PLAYING:
            REGION_EDITOR.open_region()

    def set_cc_num(self, a_val=None):
        f_port_name = str(self.control_combobox.currentText())
        if f_port_name == "":
            self.port_num = None
        else:
            self.port_num = CONTROLLER_PORT_NAME_DICT[
                self.automation_plugin_name][f_port_name].port
        TRACK_PANEL.update_automation()

    def ccs_in_use_combobox_changed(self, a_val=None):
        if not self.suppress_ccs_in_use:
            f_str = str(self.ccs_in_use_combobox.currentText())
            if f_str:
                self.control_combobox.setCurrentIndex(
                    self.control_combobox.findText(f_str))

    def update_in_use_combobox(self):
        if self.ccs_in_use_combobox is not None:
            self.ccs_in_use_combobox.clear()
            if self.automation_uid is not None:
                f_list = ATM_REGION.get_ports(self.automation_uid)
                self.ccs_in_use_combobox.addItems(
                    [""] +
                    [CONTROLLER_PORT_NUM_DICT[
                        self.automation_plugin_name][x].name
                    for x in f_list])

    def on_solo(self, value):
        if not self.suppress_osc:
            PROJECT.en_osc.pydaw_set_solo(
                self.track_number, self.solo_checkbox.isChecked())
            PROJECT.save_tracks(TRACK_PANEL.get_tracks())
            PROJECT.commit(_("Set solo for track {} to {}").format(
                self.track_number, self.solo_checkbox.isChecked()))

    def on_mute(self, value):
        if not self.suppress_osc:
            PROJECT.en_osc.pydaw_set_mute(
                self.track_number, self.mute_checkbox.isChecked())
            PROJECT.save_tracks(TRACK_PANEL.get_tracks())
            PROJECT.commit(_("Set mute for track {} to {}").format(
                self.track_number, self.mute_checkbox.isChecked()))

    def on_name_changed(self):
        f_name = pydaw_remove_bad_chars(self.track_name_lineedit.text())
        self.track_name_lineedit.setText(f_name)
        global_update_track_comboboxes(self.track_number, f_name)
        f_tracks = PROJECT.get_tracks()
        f_tracks.tracks[self.track_number].name = f_name
        PROJECT.save_tracks(f_tracks)
        PROJECT.commit(
            _("Set name for track {} to {}").format(self.track_number,
            self.track_name_lineedit.text()))
        f_plugins = PROJECT.get_track_plugins(self.track_number)
        if not f_plugins:
            return
        for f_plugin in f_plugins.plugins:
            libmk.PLUGIN_UI_DICT.plugin_set_window_title(
                f_plugin.plugin_uid,
                _("Track: {}").format(self.name_callback()))

    def context_menu_event(self, a_event=None):
        pass

    def automation_callback(self, a_plugin_uid, a_plugin_type, a_name):
        self.automation_uid = int(a_plugin_uid)
        self.automation_plugin = int(a_plugin_type)
        self.automation_plugin_name = str(a_name)
        self.plugin_changed()
        if not libmk.IS_PLAYING:
            REGION_EDITOR.open_region()

    def save_callback(self):
        f_result = libmk.pydaw_track_plugins()
        f_result.plugins = [x.get_value() for x in self.plugins]
        PROJECT.save_track_plugins(self.track_number, f_result)
        PROJECT.commit(
            "Update track plugins for '{}', {}".format(
            self.name_callback(), self.track_number))
        f_graph = PROJECT.get_routing_graph()
        if self.track_number != 0 and \
        f_graph.set_default_output(self.track_number):
            PROJECT.save_routing_graph(f_graph)
            PROJECT.commit(_("Set default output "
                "for track {}".format(self.track_number)))
            self.open_plugins()
        self.plugin_changed()

    def name_callback(self):
        return str(self.track_name_lineedit.text())

    def open_track(self, a_track, a_notify_osc=False):
        if not a_notify_osc:
            self.suppress_osc = True
        if self.track_number != 0:
            self.track_name_lineedit.setText(a_track.name)
            self.solo_checkbox.setChecked(a_track.solo)
            self.mute_checkbox.setChecked(a_track.mute)
        self.suppress_osc = False

    def open_plugins(self):
        f_plugins = PROJECT.get_track_plugins(self.track_number)
        if f_plugins:
            for f_plugin in f_plugins.plugins:
                self.plugins[f_plugin.index].set_value(f_plugin)
        if not self.sends:  # master track, etc...
            return
        f_graph = PROJECT.get_routing_graph()
        if self.track_number in f_graph.graph:
            f_sends = f_graph.graph[self.track_number]
            for f_i, f_send in f_sends.items():
                self.sends[f_i].set_value(f_send)

    def get_track(self):
        return pydaw_track(
            self.track_number, self.solo_checkbox.isChecked(),
            self.mute_checkbox.isChecked(),
            self.track_number, self.track_name_lineedit.text())


MREC_EVENTS = []

class transport_widget(libmk.AbstractTransport):
    def __init__(self):
        self.suppress_osc = True
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
        self.playback_menu_button = QtGui.QPushButton("")
        self.playback_menu_button.setMaximumWidth(21)
        self.playback_menu_button.setSizePolicy(
            QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.hlayout1.addWidget(self.playback_menu_button)
        self.grid_layout1 = QtGui.QGridLayout()
        self.hlayout1.addLayout(self.grid_layout1)
        self.grid_layout1.addWidget(QtGui.QLabel(_("BPM")), 0, 0)
        self.tempo_spinbox = QtGui.QSpinBox()
        self.tempo_spinbox.setKeyboardTracking(False)
        self.tempo_spinbox.setObjectName("large_spinbox")
        self.tempo_spinbox.setRange(50, 200)
        self.tempo_spinbox.valueChanged.connect(self.on_tempo_changed)
        self.grid_layout1.addWidget(self.tempo_spinbox, 1, 0)
        self.grid_layout1.addWidget(QtGui.QLabel(_("Region")), 0, 10)
        self.region_spinbox = QtGui.QSpinBox()
        self.region_spinbox.setObjectName("large_spinbox")
        self.region_spinbox.setRange(1, 300)
        self.region_spinbox.valueChanged.connect(self.on_region_changed)
        self.grid_layout1.addWidget(self.region_spinbox, 1, 10)
        self.grid_layout1.addWidget(QtGui.QLabel(_("Bar")), 0, 20)
        self.bar_spinbox = QtGui.QSpinBox()
        self.bar_spinbox.setObjectName("large_spinbox")
        self.bar_spinbox.setRange(1, 8)
        self.bar_spinbox.valueChanged.connect(self.on_bar_changed)
        self.grid_layout1.addWidget(self.bar_spinbox, 1, 20)

        self.playback_menu = QtGui.QMenu(self.playback_menu_button)
        self.playback_menu_button.setMenu(self.playback_menu)
        self.playback_widget_action = QtGui.QWidgetAction(self.playback_menu)
        self.playback_widget = QtGui.QWidget()
        self.playback_widget_action.setDefaultWidget(self.playback_widget)
        self.playback_vlayout = QtGui.QVBoxLayout(self.playback_widget)
        self.playback_menu.addAction(self.playback_widget_action)

        self.grid_layout1.addWidget(QtGui.QLabel(_("Loop Mode:")), 0, 45)
        self.loop_mode_combobox = QtGui.QComboBox()
        self.loop_mode_combobox.addItems([_("Off"), _("Region")])
        self.loop_mode_combobox.setMinimumWidth(90)
        self.loop_mode_combobox.currentIndexChanged.connect(
            self.on_loop_mode_changed)
        self.grid_layout1.addWidget(self.loop_mode_combobox, 1, 45)

        self.overdub_checkbox = QtGui.QCheckBox(_("Overdub"))
        self.overdub_checkbox.clicked.connect(self.on_overdub_changed)
        self.playback_vlayout.addWidget(self.overdub_checkbox)

        self.playback_vlayout.addLayout(MIDI_DEVICES_DIALOG.layout)
        self.active_devices = []

        self.last_region_num = -99
        self.suppress_osc = False

    def on_panic(self):
        PROJECT.en_osc.pydaw_panic()

    def set_time(self, a_region, a_bar, a_beat):
        f_seconds = REGION_TIME[a_region]
        f_seconds_per_beat = 60.0 / float(self.tempo_spinbox.value())
        f_seconds += f_seconds_per_beat * ((4.0 * a_bar) + a_beat)
        f_minutes = int(f_seconds / 60)
        f_seconds = str(round(f_seconds % 60, 1))
        f_seconds, f_frac = f_seconds.split('.', 1)
        f_text = "{}:{}.{}".format(f_minutes, str(f_seconds).zfill(2), f_frac)
        libmk.TRANSPORT.set_time(f_text)

    def set_region_value(self, a_val):
        self.region_spinbox.setValue(int(a_val) + 1)

    def set_bar_value(self, a_val):
        self.bar_spinbox.setValue(int(a_val) + 1)

    def get_region_value(self):
        return self.region_spinbox.value() - 1

    def get_bar_value(self):
        return self.bar_spinbox.value() - 1

    def set_pos_from_cursor(self, a_region, a_bar, a_beat):
        if libmk.IS_PLAYING or libmk.IS_RECORDING:
            f_region = int(a_region)
            f_bar = int(a_bar)
            f_beat = float(a_beat)
            self.set_time(f_region, f_bar, f_beat)
            if self.get_region_value() != f_region or \
            self.get_bar_value() != f_bar:
                self.set_region_value(f_region)
                self.set_bar_value(f_bar)
                if f_region != self.last_region_num:
                    self.last_region_num = f_region
                    f_item = SONG_EDITOR.table_widget.item(0, f_region)
                    SONG_EDITOR.table_widget.selectColumn(f_region)
                    if not f_item is None and f_item.text() != "":
                        REGION_SETTINGS.open_region(f_item.text())
                    else:
                        global CURRENT_REGION_NAME
                        global AUDIO_ITEMS
                        global CURRENT_REGION
                        CURRENT_REGION_NAME = None
                        CURRENT_REGION = None
                        AUDIO_ITEMS = None
                        REGION_SETTINGS.clear_items()
                        AUDIO_SEQ.update_zoom()
                        AUDIO_SEQ.clear_drawn_items()

    def init_playback_cursor(self, a_start=True):
        if SONG_EDITOR.table_widget.item(
        0, self.get_region_value()) is not None:
            f_region_name = str(SONG_EDITOR.table_widget.item(
                0, self.get_region_value()).text())
            if not a_start or (CURRENT_REGION_NAME is not None and \
            f_region_name != CURRENT_REGION_NAME) or CURRENT_REGION is None:
                REGION_SETTINGS.open_region(f_region_name)
        else:
            REGION_EDITOR.clear_drawn_items()
            AUDIO_SEQ.clear_drawn_items()
        if not a_start:
            REGION_EDITOR.clearSelection()
        SONG_EDITOR.table_widget.selectColumn(self.get_region_value())

    def on_play(self):
        if libmk.IS_PLAYING:
            self.set_region_value(self.start_region)
            self.set_bar_value(self.last_bar)

        SONG_EDITOR.table_widget.setEnabled(False)
        REGION_SETTINGS.on_play()
        AUDIO_SEQ_WIDGET.on_play()
        self.bar_spinbox.setEnabled(False)
        self.region_spinbox.setEnabled(False)
        self.init_playback_cursor()
        self.last_region_num = self.get_region_value()
        self.start_region = self.get_region_value()
        self.last_bar = self.get_bar_value()
        self.trigger_audio_playback()
        AUDIO_SEQ.set_playback_clipboard()
        PROJECT.en_osc.pydaw_en_playback(
            1, self.get_region_value(), self.get_bar_value())
        return True

    def trigger_audio_playback(self):
        AUDIO_SEQ.set_playback_pos(self.get_bar_value())
        AUDIO_SEQ.start_playback(self.tempo_spinbox.value())

    def on_stop(self):
        PROJECT.en_osc.pydaw_en_playback(0)
        SONG_EDITOR.table_widget.setEnabled(True)
        REGION_SETTINGS.on_stop()
        AUDIO_SEQ_WIDGET.on_stop()

        self.bar_spinbox.setEnabled(True)
        self.region_spinbox.setEnabled(True)
        self.overdub_checkbox.setEnabled(True)

        self.set_region_value(self.start_region)
        if libmk.IS_RECORDING:
            self.show_save_items_dialog()
            if CURRENT_REGION is not None and \
            REGION_SETTINGS.enabled:
                REGION_SETTINGS.open_region_by_uid(CURRENT_REGION.uid)
            SONG_EDITOR.open_song()
        self.init_playback_cursor(a_start=False)
        self.set_bar_value(self.last_bar)
        f_song_table_item = SONG_EDITOR.table_widget.item(
            0, self.get_region_value())
        if f_song_table_item is not None and \
        str(f_song_table_item.text()) != None:
            f_song_table_item_str = str(f_song_table_item.text())
            REGION_SETTINGS.open_region(f_song_table_item_str)
        else:
            REGION_SETTINGS.clear_items()
        AUDIO_SEQ.stop_playback(self.last_bar)
        time.sleep(0.1)

    def show_save_items_dialog(self):
        def ok_handler():
            f_file_name = str(f_file.text())
            if f_file_name is None or f_file_name == "":
                QtGui.QMessageBox.warning(
                    f_window, _("Error"),
                    _("You must select a name for the item"))
                return
            PROJECT.save_recorded_items(
                f_file_name, MREC_EVENTS, self.overdub_checkbox.isChecked(),
                self.tempo_spinbox.value(), pydaw_util.SAMPLE_RATE)
            SONG_EDITOR.open_song()
            if not CURRENT_REGION:
                SONG_EDITOR.open_first_region()
            REGION_SETTINGS.open_region_by_uid(CURRENT_REGION.uid)
            f_window.close()

        def text_edit_handler(a_val=None):
            f_file.setText(pydaw_remove_bad_chars(f_file.text()))

        f_window = QtGui.QDialog(MAIN_WINDOW)
        f_window.setMinimumWidth(330)
        f_layout = QtGui.QGridLayout()
        f_window.setLayout(f_layout)
        f_layout.addWidget(QtGui.QLabel(_("Save recorded MIDI items")), 0, 2)
        f_layout.addWidget(QtGui.QLabel(_("Item Name:")), 3, 1)
        f_file = QtGui.QLineEdit()
        f_file.setMaxLength(24)
        f_file.textEdited.connect(text_edit_handler)
        f_layout.addWidget(f_file, 3, 2)
        f_ok_button = QtGui.QPushButton(_("Save"))
        f_ok_button.clicked.connect(ok_handler)
        f_cancel_button = QtGui.QPushButton(_("Discard"))
        f_cancel_button.clicked.connect(f_window.close)
        f_ok_cancel_layout = QtGui.QHBoxLayout()
        f_ok_cancel_layout.addWidget(f_ok_button)
        f_ok_cancel_layout.addWidget(f_cancel_button)
        f_layout.addLayout(f_ok_cancel_layout, 8, 2)
        f_window.exec_()

    def on_rec(self):
        self.active_devices = [x for x in MIDI_DEVICES_DIALOG.devices
            if x.record_checkbox.isChecked()]
        if not self.active_devices:
            QtGui.QMessageBox.warning(
                self.group_box, _("Error"), _("No track record-armed"))
            return False
        if self.overdub_checkbox.isChecked() and \
        self.loop_mode_combobox.currentIndex() > 0:
            QtGui.QMessageBox.warning(
                self.group_box, _("Error"),
                _("Cannot use overdub mode with loop mode to record"))
            return False
        SONG_EDITOR.table_widget.setEnabled(False)
        REGION_SETTINGS.on_play()
        AUDIO_SEQ_WIDGET.on_play()
        self.bar_spinbox.setEnabled(False)
        self.region_spinbox.setEnabled(False)
        self.overdub_checkbox.setEnabled(False)
        global MREC_EVENTS
        MREC_EVENTS = []
        self.init_playback_cursor()
        self.last_region_num = self.get_region_value()
        self.start_region = self.get_region_value()
        self.last_bar = self.get_bar_value()
        PROJECT.en_osc.pydaw_en_playback(
            2, a_region_num=self.get_region_value(),
            a_bar=self.get_bar_value())
        self.trigger_audio_playback()
        AUDIO_SEQ.set_playback_clipboard()
        return True

    def on_tempo_changed(self, a_tempo):
        self.transport.bpm = a_tempo
        pydaw_set_bpm(a_tempo)
        if CURRENT_REGION is not None:
            global_open_audio_items()
        if not self.suppress_osc:
            PROJECT.en_osc.pydaw_set_tempo(a_tempo)
            PROJECT.save_transport(self.transport)
            PROJECT.commit(_("Set project tempo to {}").format(a_tempo))
        global_update_region_time()

    def on_loop_mode_changed(self, a_loop_mode):
        if not self.suppress_osc:
            PROJECT.en_osc.pydaw_set_loop_mode(a_loop_mode)

    def toggle_loop_mode(self):
        f_index = self.loop_mode_combobox.currentIndex() + 1
        if f_index >= self.loop_mode_combobox.count():
            f_index = 0
        self.loop_mode_combobox.setCurrentIndex(f_index)

    def on_bar_changed(self, a_bar):
        if not self.suppress_osc and \
        not libmk.IS_PLAYING and \
        not libmk.IS_RECORDING:
            for f_editor in (AUDIO_SEQ, REGION_EDITOR):
                f_editor.set_playback_pos(self.get_bar_value())
            PROJECT.en_osc.pydaw_set_pos(
                self.get_region_value(), self.get_bar_value())
        self.set_time(self.get_region_value(), self.get_bar_value(), 0.0)

    def on_region_changed(self, a_region):
        #self.bar_spinbox.setRange(1, pydaw_get_region_length(a_region - 1))
        self.bar_spinbox.setRange(1, pydaw_get_current_region_length())
        if not libmk.IS_PLAYING and not libmk.IS_RECORDING:
            for f_editor in (AUDIO_SEQ, REGION_EDITOR):
                f_editor.set_playback_pos(self.get_bar_value())
            PROJECT.en_osc.pydaw_set_pos(
                self.get_region_value(), self.get_bar_value())
        self.set_time(self.get_region_value(), self.get_bar_value(), 0.0)

    def open_transport(self, a_notify_osc=False):
        if not a_notify_osc:
            self.suppress_osc = True
        self.transport = PROJECT.get_transport()
        self.tempo_spinbox.setValue(int(self.transport.bpm))
        self.suppress_osc = False

    def on_overdub_changed(self, a_val=None):
        PROJECT.en_osc.pydaw_set_overdub_mode(
            self.overdub_checkbox.isChecked())

    def reset(self):
        self.loop_mode_combobox.setCurrentIndex(0)
        self.overdub_checkbox.setChecked(False)

    def set_tooltips(self, a_enabled):
        if a_enabled:
            self.overdub_checkbox.setToolTip(
                _("Checking this box causes recording to "
                "unlink existing items and append new events to the "
                "existing events"))
            self.loop_mode_combobox.setToolTip(
                _("Use this to toggle between normal playback "
                "and looping a region.\nYou can toggle between "
                "settings with CTRL+L"))
            self.group_box.setToolTip(libedmnext.strings.transport)
        else:
            self.overdub_checkbox.setToolTip("")
            self.loop_mode_combobox.setToolTip("")
            self.group_box.setToolTip("")


class pydaw_main_window(QtGui.QScrollArea):
    def __init__(self):
        QtGui.QScrollArea.__init__(self)
        self.first_offline_render = True
        self.last_offline_dir = global_home
        self.copy_to_clipboard_checked = True
        self.last_midi_dir = None
        self.last_bar = 0

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

        self.loop_mode_action = QtGui.QAction(self)
        self.addAction(self.loop_mode_action)
        self.loop_mode_action.setShortcut(
            QtGui.QKeySequence.fromString("CTRL+L"))
        self.loop_mode_action.triggered.connect(TRANSPORT.toggle_loop_mode)

        #The tabs
        self.main_tabwidget = QtGui.QTabWidget()
        self.main_layout.addWidget(self.main_tabwidget)

        self.regions_tab_widget = QtGui.QTabWidget()
        self.song_region_tab = QtGui.QWidget()
        self.song_region_vlayout = QtGui.QVBoxLayout()
        self.song_region_vlayout.setMargin(3)
        self.song_region_tab.setLayout(self.song_region_vlayout)
        self.song_region_splitter = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.song_region_splitter.addWidget(self.song_region_tab)
        self.main_tabwidget.addTab(self.song_region_splitter, _("Song/Region"))

        self.song_region_vlayout.addWidget(SONG_EDITOR.table_widget)
        self.song_region_vlayout.addLayout(REGION_SETTINGS.hlayout0)

        self.song_region_splitter.addWidget(self.regions_tab_widget)
        self.midi_scroll_area = QtGui.QScrollArea()
        self.midi_scroll_area.setWidgetResizable(True)
        self.midi_scroll_widget = QtGui.QWidget()
        self.midi_scroll_widget.setContentsMargins(0, 0, 0, 0)
        self.midi_hlayout = QtGui.QHBoxLayout(self.midi_scroll_widget)
        self.midi_hlayout.setContentsMargins(0, 0, 0, 0)
        self.midi_scroll_area.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn)
        self.midi_scroll_area.setWidget(self.midi_scroll_widget)
        self.midi_hlayout.addWidget(TRACK_PANEL.tracks_widget)
        self.midi_hlayout.addWidget(REGION_EDITOR)

        self.regions_tab_widget.addTab(self.midi_scroll_area, _("MIDI"))
        self.midi_scroll_area.scrollContentsBy = self.midi_scrollContentsBy

        self.regions_tab_widget.addTab(AUDIO_SEQ_WIDGET.hsplitter, _("Audio"))

        self.first_audio_tab_click = True
        self.regions_tab_widget.currentChanged.connect(
            self.regions_tab_changed)

        self.main_tabwidget.addTab(ITEM_EDITOR.widget, _("MIDI Items"))

        self.automation_tab = QtGui.QWidget()
        self.automation_tab.setObjectName("plugin_ui")

        self.main_tabwidget.addTab(ROUTING_GRAPH_WIDGET, _("Routing"))
        self.main_tabwidget.addTab(MIXER_WIDGET.widget, _("Mixer"))

        self.notes_tab = QtGui.QTextEdit(self)
        self.notes_tab.setAcceptRichText(False)
        self.notes_tab.leaveEvent = self.on_edit_notes
        self.main_tabwidget.addTab(self.notes_tab, _("Project Notes"))
        self.main_tabwidget.currentChanged.connect(self.tab_changed)

    def on_offline_render(self):
        def ok_handler():
            if str(f_name.text()) == "":
                QtGui.QMessageBox.warning(
                    f_window, _("Error"), _("Name cannot be empty"))
                return
            if (f_end_region.value() < f_start_region.value()) or \
            ((f_end_region.value() == f_start_region.value()) and \
            (f_start_bar.value() >= f_end_bar.value())):
                QtGui.QMessageBox.warning(f_window, _("Error"),
                _("End point is before start point."))
                return

            libmk.PLUGIN_UI_DICT.save_all_plugin_state()

            if f_copy_to_clipboard_checkbox.isChecked():
                self.copy_to_clipboard_checked = True
                f_clipboard = QtGui.QApplication.clipboard()
                f_clipboard.setText(f_name.text())
            else:
                self.copy_to_clipboard_checked = False
            #TODO:  Check that the end is actually after the start....

            f_dir = PROJECT.project_folder
            f_out_file = f_name.text()
            f_sr = f_start_region.value() - 1
            f_sb = f_start_bar.value() - 1
            f_er = f_end_region.value() - 1
            f_eb = f_end_bar.value() - 1
            f_samp_rate = f_sample_rate.currentText()
            f_buff_size = pydaw_util.global_device_val_dict["bufferSize"]
            f_thread_count = pydaw_util.global_device_val_dict["threads"]

            self.start_reg = f_start_region.value()
            self.end_reg = f_end_region.value()
            self.start_bar = f_start_bar.value()
            self.end_bar = f_end_bar.value()
            self.last_offline_dir = os.path.dirname(str(f_name.text()))

            f_window.close()

            if f_debug_checkbox.isChecked():
                f_cmd = "x-terminal-emulator -e bash -c " \
                "'gdb {}-dbg'".format(pydaw_util.global_pydaw_render_bin_path)
                f_run_cmd = [str(x) for x in
                    ("run", "'{}'".format(f_dir),
                     "'{}'".format(f_out_file), f_sr, f_sb,
                     f_er, f_eb, f_samp_rate, f_buff_size, f_thread_count)]
                f_clipboard = QtGui.QApplication.clipboard()
                f_clipboard.setText(" ".join(f_run_cmd))
                subprocess.Popen(f_cmd, shell=True)
            else:
                f_cmd = [str(x) for x in
                    (pydaw_util.global_pydaw_render_bin_path,
                     f_dir, f_out_file, f_sr, f_sb, f_er, f_eb,
                     f_samp_rate, f_buff_size, f_thread_count,
                     pydaw_util.USE_HUGEPAGES)]
                libmk.MAIN_WINDOW.show_offline_rendering_wait_window_v2(
                    f_cmd, f_out_file)

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

        if self.first_offline_render:
            self.first_offline_render = False
            self.start_reg = 1
            self.end_reg = 1
            self.start_bar = 1
            self.end_bar = 2

            for i in range(300):
                f_item = SONG_EDITOR.table_widget.item(0, i)
                if not f_item is None and f_item.text() != "":
                    self.start_reg = i + 1
                    break

            for i in range(self.start_reg, 300):
                f_item = SONG_EDITOR.table_widget.item(0, i)
                if f_item is None or f_item.text() == "":
                    self.end_reg = i + 1
                    break

        def start_region_changed(a_val=None):
            f_max = pydaw_get_region_length(f_start_region.value() - 1)
            f_start_bar.setMaximum(f_max)

        def end_region_changed(a_val=None):
            f_max = pydaw_get_region_length(f_end_region.value() - 1)
            f_end_bar.setMaximum(f_max)

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

        f_layout.addWidget(QtGui.QLabel(_("Start:")), 1, 0)
        f_start_hlayout = QtGui.QHBoxLayout()
        f_layout.addLayout(f_start_hlayout, 1, 1)
        f_start_hlayout.addWidget(QtGui.QLabel(_("Region:")))
        f_start_region = QtGui.QSpinBox()
        f_start_region.setRange(1, 299)
        f_start_region.setValue(self.start_reg)
        f_start_hlayout.addWidget(f_start_region)
        f_start_hlayout.addWidget(QtGui.QLabel(_("Bar:")))
        f_start_bar = QtGui.QSpinBox()
        f_start_bar.setRange(1, 8)
        f_start_bar.setValue(self.start_bar)
        f_start_hlayout.addWidget(f_start_bar)
        f_start_region.valueChanged.connect(start_region_changed)
        start_region_changed()

        f_layout.addWidget(QtGui.QLabel(_("End:")), 2, 0)
        f_end_hlayout = QtGui.QHBoxLayout()
        f_layout.addLayout(f_end_hlayout, 2, 1)
        f_end_hlayout.addWidget(QtGui.QLabel(_("Region:")))
        f_end_region = QtGui.QSpinBox()
        f_end_region.setRange(1, 299)
        f_end_region.setValue(self.end_reg)
        f_end_hlayout.addWidget(f_end_region)
        f_end_hlayout.addWidget(QtGui.QLabel(_("Bar:")))
        f_end_bar = QtGui.QSpinBox()
        f_end_bar.setRange(1, 8)
        f_end_bar.setValue(self.end_bar)
        f_end_hlayout.addWidget(f_end_bar)
        f_end_region.valueChanged.connect(end_region_changed)
        end_region_changed()

        f_sample_rate_hlayout = QtGui.QHBoxLayout()
        f_layout.addLayout(f_sample_rate_hlayout, 3, 1)
        f_sample_rate_hlayout.addWidget(QtGui.QLabel(_("Sample Rate")))
        f_sample_rate = QtGui.QComboBox()
        f_sample_rate.setMinimumWidth(105)
        f_sample_rate.addItems(["44100", "48000", "88200", "96000", "192000"])

        try:
            f_sr_index = f_sample_rate.findText(
                pydaw_util.global_device_val_dict["sampleRate"])
            f_sample_rate.setCurrentIndex(f_sr_index)
        except:
            pass

        f_sample_rate_hlayout.addWidget(f_sample_rate)
        f_sample_rate_hlayout.addItem(
            QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding))

        f_layout.addWidget(QtGui.QLabel(
            _("File is exported to 32 bit .wav at the selected sample rate. "
            "\nYou can convert the format using "
            "Menu->Tools->MP3/Ogg Converter")),
            6, 1)
        f_copy_to_clipboard_checkbox = QtGui.QCheckBox(
        _("Copy export path to clipboard? (useful for right-click pasting "
        "back into the audio sequencer)"))
        f_copy_to_clipboard_checkbox.setChecked(self.copy_to_clipboard_checked)
        f_layout.addWidget(f_copy_to_clipboard_checkbox, 7, 1)
        f_ok_layout = QtGui.QHBoxLayout()

        f_debug_checkbox = QtGui.QCheckBox("Debug with GDB?")
        f_ok_layout.addWidget(f_debug_checkbox)

        f_ok_layout.addItem(
            QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Minimum))
        f_ok = QtGui.QPushButton(_("OK"))
        f_ok.setMinimumWidth(75)
        f_ok.pressed.connect(ok_handler)
        f_ok_layout.addWidget(f_ok)
        f_layout.addLayout(f_ok_layout, 9, 1)
        f_cancel = QtGui.QPushButton(_("Cancel"))
        f_cancel.setMinimumWidth(75)
        f_cancel.pressed.connect(cancel_handler)
        f_ok_layout.addWidget(f_cancel)
        f_window.exec_()

    def on_undo(self):
        if libmk.IS_PLAYING:
            return
        if PROJECT.undo():
            global_ui_refresh_callback()
        else:
            QtGui.QMessageBox.warning(
                MAIN_WINDOW, "Error", "No more undo history left")

    def on_redo(self):
        if libmk.IS_PLAYING:
            return
        if PROJECT.redo():
            global_ui_refresh_callback()
        else:
            QtGui.QMessageBox.warning(
                MAIN_WINDOW, "Error", "Already at the latest commit")

    def tab_changed(self):
        f_index = self.main_tabwidget.currentIndex()
        if f_index == 0 and not libmk.IS_PLAYING:
            REGION_EDITOR.open_region()
        elif f_index == 1:
            ITEM_EDITOR.tab_changed()
        elif f_index == 2:
            ROUTING_GRAPH_WIDGET.draw_graph(
                PROJECT.get_routing_graph(), TRACK_NAMES)
        elif f_index == 3:
            global_open_mixer()

    def on_edit_notes(self, a_event=None):
        QtGui.QTextEdit.leaveEvent(self.notes_tab, a_event)
        PROJECT.write_notes(self.notes_tab.toPlainText())

    def set_tooltips(self, a_on):
        if a_on:
            ROUTING_GRAPH_WIDGET.setToolTip(libpydaw.strings.routing_graph)
        else:
            ROUTING_GRAPH_WIDGET.setToolTip("")

    def regions_tab_changed(self, a_val=None):
        if self.regions_tab_widget.currentIndex() == 1 and \
        self.first_audio_tab_click:
            self.first_audio_tab_click = False
            pydaw_set_audio_seq_zoom(1.0, 1.0)
            global_open_audio_items(a_reload=False)

    def midi_scrollContentsBy(self, x, y):
        QtGui.QScrollArea.scrollContentsBy(self.midi_scroll_area, x, y)
        REGION_EDITOR.set_header_pos()

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
                    f_region, f_bar = (int(x) for x in (f_region, f_bar))
                    f_beat = float(f_beat)
                    if self.last_bar != f_bar or f_beat >= 4.0:
                        f_beat = 0.0
                    self.last_bar = f_bar
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
            elif a_key == "ready":
                for f_widget in (libmk.TRANSPORT, MIDI_DEVICES_DIALOG):
                    f_widget.on_ready()
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
        try:
            for f_widget in (AUDIO_SEQ, PIANO_ROLL_EDITOR,
            CC_EDITOR, PB_EDITOR, REGION_EDITOR):
                f_widget.prepare_to_quit()
        except Exception as ex:
            print("Exception thrown while attempting to close EDM-Next")
            print("Exception:  {}".format(ex))


def global_update_peak_meters(a_val):
    for f_val in a_val.split("|"):
        f_list = f_val.split(":")
        f_index = int(f_list[0])
        if f_index in ALL_PEAK_METERS:
            for f_pkm in ALL_PEAK_METERS[f_index]:
                f_pkm.set_value(f_list[1:])
        else:
            print("{} not in ALL_PEAK_METERS".format(f_index))


def global_close_all():
    global OPEN_ITEM_UIDS, AUDIO_ITEMS_TO_DROP
    if libmk.PLUGIN_UI_DICT:
        libmk.PLUGIN_UI_DICT.close_all_plugin_windows()
    REGION_SETTINGS.clear_new()
    ITEM_EDITOR.clear_new()
    SONG_EDITOR.table_widget.clearContents()
    AUDIO_SEQ.clear_drawn_items()
    PB_EDITOR.clear_drawn_items()
    TRANSPORT.reset()
    OPEN_ITEM_UIDS = []
    AUDIO_ITEMS_TO_DROP = []

def global_ui_refresh_callback(a_restore_all=False):
    """ Use this to re-open all existing items/regions/song in
        their editors when the files have been changed externally
    """
    TRACK_PANEL.open_tracks()
    f_regions_dict = PROJECT.get_regions_dict()
    global CURRENT_REGION
    if CURRENT_REGION is not None and \
    f_regions_dict.uid_exists(CURRENT_REGION.uid):
        REGION_SETTINGS.open_region_by_uid(CURRENT_REGION.uid)
        global_open_audio_items()
        #this_audio_editor.open_tracks()
    else:
        REGION_SETTINGS.clear_new()
        CURRENT_REGION = None
    if ITEM_EDITOR.enabled and global_check_midi_items():
        global_open_items()
    SONG_EDITOR.open_song()
    TRANSPORT.open_transport()
    PROJECT.en_osc.pydaw_open_song(
        PROJECT.project_folder, a_restore_all)

#Opens or creates a new project
def global_open_project(a_project_file):
    global PROJECT, TRACK_NAMES
    PROJECT = EdmNextProject(global_pydaw_with_audio)
    PROJECT.suppress_updates = True
    PROJECT.open_project(a_project_file, False)
    TRACK_PANEL.open_tracks()
    SONG_EDITOR.open_song()
    REGION_EDITOR.clear_drawn_items()
    TRANSPORT.open_transport()
    PROJECT.suppress_updates = False
    f_scale = PROJECT.get_midi_scale()
    if f_scale is not None:
        PIANO_ROLL_EDITOR_WIDGET.scale_key_combobox.setCurrentIndex(f_scale[0])
        PIANO_ROLL_EDITOR_WIDGET.scale_combobox.setCurrentIndex(f_scale[1])
    SONG_EDITOR.open_first_region()
    MAIN_WINDOW.last_offline_dir = libmk.PROJECT.user_folder
    MAIN_WINDOW.notes_tab.setText(PROJECT.get_notes())
    global_update_region_time()
    ROUTING_GRAPH_WIDGET.draw_graph(
        PROJECT.get_routing_graph(), TRACK_PANEL.get_track_names())
    global_open_mixer()

def global_new_project(a_project_file):
    global PROJECT
    PROJECT = EdmNextProject(global_pydaw_with_audio)
    PROJECT.new_project(a_project_file)
    PROJECT.save_transport(TRANSPORT.transport)
    SONG_EDITOR.open_song()
    PROJECT.save_song(SONG_EDITOR.song)
    TRANSPORT.open_transport()
    global_update_track_comboboxes()
    MAIN_WINDOW.last_offline_dir = libmk.PROJECT.user_folder
    MAIN_WINDOW.notes_tab.setText("")
    global_update_region_time()
    ROUTING_GRAPH_WIDGET.scene.clear()
    global_open_mixer()

PROJECT = EdmNextProject(global_pydaw_with_audio)

TIMESTRETCH_MODES = [
    _("None"), _("Pitch(affecting time)"), _("Time(affecting pitch)"),
    "Rubberband", "Rubberband(formants)", "SBSMS", "Paulstretch"]

CRISPNESS_SETTINGS = [
    _("0 (smeared)"), _("1 (piano)"), "2", "3",
    "4", "5 (normal)", _("6 (sharp, drums)")]

TRACK_NAMES = ["Master" if x == 0 else "track{}".format(x)
    for x in range(TRACK_COUNT_ALL)]

SUPPRESS_TRACK_COMBOBOX_CHANGES = False
AUDIO_TRACK_COMBOBOXES = []

PB_EDITOR = automation_viewer(a_is_cc=False)
CC_EDITOR = automation_viewer()
CC_EDITOR_WIDGET = automation_viewer_widget(CC_EDITOR)

SONG_EDITOR = song_editor()
REGION_SETTINGS = region_settings()
TRACK_PANEL = tracks_widget()
REGION_EDITOR = region_editor()

PIANO_ROLL_EDITOR = piano_roll_editor()
PIANO_ROLL_EDITOR_WIDGET = piano_roll_editor_widget()
ITEM_EDITOR = item_list_editor()
AUDIO_SEQ = audio_items_viewer()
MIXER_WIDGET = pydaw_widgets.mixer_widget(TRACK_COUNT_ALL)

def get_mixer_peak_meters():
    for k, v in MIXER_WIDGET.tracks.items():
        ALL_PEAK_METERS[k].append(v.peak_meter)

get_mixer_peak_meters()

MIDI_EDITORS = (PIANO_ROLL_EDITOR, CC_EDITOR, PB_EDITOR)

MIDI_DEVICES_DIALOG = midi_devices_dialog()
TRANSPORT = transport_widget()
AUDIO_SEQ_WIDGET = audio_items_viewer_widget()

def routing_graph_toggle_callback(a_src, a_dest, a_sidechain):
    f_graph = PROJECT.get_routing_graph()
    f_result = f_graph.toggle(a_src, a_dest, a_sidechain)
    if f_result:
        QtGui.QMessageBox.warning(MAIN_WINDOW, _("Error"), f_result)
    else:
        PROJECT.save_routing_graph(f_graph)
        ROUTING_GRAPH_WIDGET.draw_graph(f_graph, TRACK_NAMES)
        PROJECT.commit(_("Update routing"))

ROUTING_GRAPH_WIDGET = pydaw_widgets.routing_graph_widget(
    routing_graph_toggle_callback)

# Must call this after instantiating the other widgets,
# as it relies on them existing
MAIN_WINDOW = pydaw_main_window()

PIANO_ROLL_EDITOR.verticalScrollBar().setSliderPosition(
    PIANO_ROLL_EDITOR.scene.height() * 0.4)
PIANO_ROLL_EDITOR_WIDGET.snap_combobox.setCurrentIndex(4)

if libmk.TOOLTIPS_ENABLED:
    set_tooltips_enabled(libmk.TOOLTIPS_ENABLED)

