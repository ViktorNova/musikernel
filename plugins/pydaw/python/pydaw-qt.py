#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
PyDAW - Part of the LibModSynth project

A DAW using Python and Qt, with a high performance audio/MIDI
backend written in C

Copyright 2012, Jeff Hubbard
See GPLv3 for license
"""

import sys, os
from PyQt4 import QtGui, QtCore
from sys import argv
from os.path import expanduser


from lms_session import lms_session
from dssi_gui import dssi_gui

class seq_track:
    def __init__(self):
        self.regions = []
        
    def __str__(self):
        return "" #TODO

class list_region:
    def __init__(self, a_string=None):
        self.seq_items = []
        
        if not a_string is None:
            pass            
    
    def __str__(self):
        return "" #TODO

class lms_note_selector:
    def __init__(self):
        pass

class list_item_seq:
    def __init__(self, a_position, a_file_name, a_length=1, a_actual_length=1):
        self.position = a_position
        self.length = a_length
        self.name = a_file_name
        self.note_items = []
        self.fq_file_path = os.getcwd() + a_file_name        
        
        file_handle = open(self.fq_file_path, 'r')        
        line_arr = file_handle.readlines()        
        file_handle.close()
        
        for line in line_arr:
            item_arr = line.split('|')
            self.note_items.append(list_item_content(item_arr[0], item_arr[1]))
        
    """
    Rename the underlying file associated with the sequencer item
    """
    def rename(self, a_name):
        pass
    
    def __str__(self):
        f_result = ""
        for content_item in self.note_items:
            f_result += content_item
        
        return f_result
        
class list_item_note:
    """
    Tentatively, for a_type:  0 == MIDI Note, 1 == MIDI CC, 2 == Pitchbend, 3 == Audio
    """
    def __init__(self, a_type, a_start=0.0, a_length=1.0):
        self.type = a_type        
        self.start = a_start
        self.length = a_length
            
    def __str__(self):
        return str(self.type) + '|' + str(self.start) + '|' + str(self.length) + "\n"
    
    def on_delete(self):
        pass
    
    def on_mute(self):
        pass
    
def note_number_to_string(a_note_number):
    pass

def string_to_note_number(a_note_string):
    pass

class region_list_editor:
    #If a_new_file_name is set, a_file_name will be copied into a new file name with the name a_new_file_name
    def __init__(self):
        self.events = []
         
    """
    This should be called whenever the items have been changed, or when 
    switching items
    
    a_items should be an array of 
    """
    def update_items(self, a_items=[]):
         self.layout.delete()
         
         for item in a_items:
             item_dialog = item.get_widget()
             self.layout.add(item_dialog)
    

class item_list_editor:
    #If a_new_file_name is set, a_file_name will be copied into a new file name with the name a_new_file_name
    def __init__(self):
        self.events = []
        self.group_box = QtGui.QGroupBox()
        self.group_box.setTitle("Item Editor")
         
    """
    This should be called whenever the items have been changed, or when 
    switching items
    
    a_items should be an array of 
    """
    def update_items(self, a_items=[]):
         self.layout.delete()
         
         for item in a_items:
             item_dialog = item.get_widget()
             self.layout.content.append(item_dialog)

    
class seq_track:
    def on_vol_change(self, value):
        self.volume_label.setText(str(value))
    def on_pan_change(self, value):
        pass
    def on_solo(self, value):
        print(value)
    def on_mute(self, value):
        print(value)
    def on_rec(self, value):
        print(value)
    def on_name_changed(self, new_name):
        print(new_name)
    def on_instrument_change(self, selected_instrument):
        session_mgr.instrument_index_changed(self.track_number, selected_instrument, str(self.track_name_lineedit.text()))
    
    def __init__(self, a_track_num, a_track_text="track"):        
        self.track_number = a_track_num
        self.group_box = QtGui.QGroupBox()
        self.main_vlayout = QtGui.QVBoxLayout()
        self.group_box.setLayout(self.main_vlayout)
        self.hlayout1 = QtGui.QHBoxLayout()
        self.main_vlayout.addLayout(self.hlayout1)
        self.track_name_lineedit = QtGui.QLineEdit()
        self.track_name_lineedit.setText(a_track_text)
        self.track_name_lineedit.textChanged.connect(self.on_name_changed)
        self.hlayout1.addWidget(self.track_name_lineedit)
        self.solo_checkbox = QtGui.QCheckBox()
        self.solo_checkbox.setText("Solo")
        self.solo_checkbox.clicked.connect(self.on_solo)
        self.hlayout1.addWidget(self.solo_checkbox)
        self.mute_checkbox = QtGui.QCheckBox()
        self.mute_checkbox.setText("Mute")
        self.hlayout1.addWidget(self.mute_checkbox)
        self.record_radiobutton = QtGui.QRadioButton()
        self.record_radiobutton.setText("Rec")
        self.record_radiobutton.clicked.connect(self.on_rec)
        self.hlayout1.addWidget(self.record_radiobutton)
        self.hlayout2 = QtGui.QHBoxLayout()
        self.main_vlayout.addLayout(self.hlayout2)
        self.volume_slider = QtGui.QSlider()
        self.volume_slider.setMinimum(-50)
        self.volume_slider.setMaximum(12)
        self.volume_slider.setValue(0)
        self.volume_slider.setOrientation(QtCore.Qt.Horizontal)
        self.volume_slider.valueChanged.connect(self.on_vol_change)                
        self.hlayout2.addWidget(self.volume_slider)
        self.volume_label = QtGui.QLabel()
        self.volume_label.setText("0")
        self.hlayout2.addWidget(self.volume_label)
        self.hlayout3 = QtGui.QHBoxLayout()
        self.main_vlayout.addLayout(self.hlayout3)
        self.instrument_combobox = QtGui.QComboBox()
        self.instrument_combobox.addItems(["None", "Euphoria", "Ray-V"])
        self.instrument_combobox.currentIndexChanged.connect(self.on_instrument_change)
        self.hlayout3.addWidget(self.instrument_combobox)


class track_view:
    def on_play(self):
        print("Playing")
    def on_stop(self):
        print("Stopping")
    def on_rec(self):
        print("Recording")
    def on_new(self):
        print("Creating new project")
    def on_open(self):
        print("Opening existing project")
    def on_save(self):
        print("Saving project")
        session_mgr.save_session_file()  #Notify the instruments to save their state
        this_dssi_gui.send_configure("save", "testing") #Send a message to the DSSI engine to save it's state.  Currently, this doesn't do anything...
    def on_file_menu_select(self, a_selected):
        pass            
            
    def __init__(self):
        self.tracks = []

        for i in range(0, 16):
            f_seq_track = seq_track(i, a_track_text="track" + str(i))
            self.tracks.append(f_seq_track.dialog)

        self.region_editor = region_list_editor()
        self.item_editor = item_list_editor()        
            
def __del__(self):
    this_dssi_gui.stop_server()

class Example(QtGui.QWidget):
    
    def __init__(self):
        super(Example, self).__init__()
        
        self.initUI()
        
    def initUI(self):               
        QtGui.QMainWindow.__init__(self)
        self.resize(1000, 600)
        self.center()
        self.main_layout = QtGui.QVBoxLayout(self)
        self.setLayout(self.main_layout)
        
        self.transport_hlayout = QtGui.QHBoxLayout()
        self.main_layout.addLayout(self.transport_hlayout)        
        
        self.editor_hlayout = QtGui.QHBoxLayout()
        self.main_layout.addLayout(self.editor_hlayout)
        self.tracks_tablewidget = QtGui.QTableWidget()
        self.tracks_tablewidget.setColumnCount(1)
        self.tracks_tablewidget.setHorizontalHeaderLabels(['Tracks'])
        self.editor_hlayout.addWidget(self.tracks_tablewidget)
                
        self.tracks = []
        
        for i in range(0, 16):
            track = seq_track(a_track_num=i, a_track_text="test" + str(i))
            self.tracks.append(track)
            self.tracks_tablewidget.insertRow(i)
            self.tracks_tablewidget.setCellWidget(i, 0, track.group_box)

        self.tracks_tablewidget.resizeColumnsToContents()
        self.tracks_tablewidget.resizeRowsToContents()        
        
        self.setWindowTitle('PyDAW')    
        self.show()
        
    def center(self):
        
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    user_home_folder = expanduser("~")
    print("user_home_folder = " + user_home_folder)
    session_mgr = lms_session(user_home_folder + '/default.pydaw')    

    for arg in argv:
        print arg
    
    if(len(argv) >= 2):
        this_dssi_gui = dssi_gui(argv[1])
    main()     