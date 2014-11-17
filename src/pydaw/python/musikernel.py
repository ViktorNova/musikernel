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
import gc
import libmk

class MkMainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        libmk.MAIN_WINDOW = self
        #self.setMinimumSize(1100, 600)
        self.setObjectName("mainwindow")
        import edmnext
        self.edm_next_module = edmnext
        self.edm_next_window = edmnext.MAIN_WINDOW
        self.host_windows = (self.edm_next_window,)
        self.setCentralWidget(self.edm_next_window)
        self.ignore_close_event = True
        self.show()

    def prepare_to_quit(self):
        try:
            for f_host in self.host_windows:
                f_host.prepare_to_quit()
            self.ignore_close_event = False
            libmk.MAIN_WINDOW = None
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
#            if IS_PLAYING:
#                return
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

