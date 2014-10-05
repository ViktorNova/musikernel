#!/usr/bin/env python3

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

try:
    import libpydaw.pydaw_util as pydaw_util
    from libpydaw.translate import _
except ImportError:
    import pydaw_util
    from translate import _

from PyQt4 import QtGui, QtCore
import json
import os

class project_history_widget(QtGui.QTreeWidget):
    def __init__(self, a_backup_dir, a_backup_file):
        QtGui.QTreeWidget.__init__(self)
        self.backup_file = a_backup_file
        self.backup_dir = a_backup_dir
        with open(a_backup_file) as f_handle:
            self.project_data = json.load(f_handle)
        self.draw_tree()

    def draw_tree(self):
        for f_name, f_data in self.project_data["NODES"].items():
            pass
        # ^^^ should be exactly one root
        f_root_node = self.get_node(f_name, f_name)
        self.addTopLevelItem(f_root_node)
        self.recursive_node_add(f_name, f_data, f_root_node)
        self.expandAll()

    def get_node(self, a_text, a_path):
        f_node = QtGui.QTreeWidgetItem()
        f_node.setText(0, a_text)
        f_node.node_path = a_path
        return f_node

    def recursive_node_add(self, a_path, a_node, a_parent_node):
        for k in sorted(a_node):
            v = a_node[k]
            f_path = "/".join((a_path, k))
            f_node = self.get_node(k, f_path)
            a_parent_node.addChild(f_node)
            self.recursive_node_add(f_path, v, f_node)


def project_recover_dialog():
    f_window = QtGui.QMainWindow()
    f_window.setWindowState(QtCore.Qt.WindowMaximized)
    f_window.setWindowTitle("Project History")
    f_file = QtGui.QFileDialog.getOpenFileName(
        caption='Open Project',
        filter=pydaw_util.global_pydaw_file_type_string,
        directory=pydaw_util.global_home)
    if f_file is not None:
        f_file = str(f_file)
        if f_file != "":
            f_project_dir = os.path.dirname(f_file)
            f_backup_file = "{}/backups.json".format(f_project_dir)
            if not os.path.isfile(f_backup_file):
                QtGui.QMessageBox.warning(
                    f_window, _("Error"), _("No backups exist for this "
                    "project, recovery is not possible."))
                return
            f_backup_dir = "{}/backups".format(f_project_dir)
            f_central_widget = QtGui.QWidget()
            f_layout = QtGui.QVBoxLayout(f_central_widget)
            f_window.setCentralWidget(f_central_widget)
            f_widget = project_history_widget(f_backup_dir, f_backup_file)
            f_layout.addWidget(f_widget)
            print("showing")
            f_window.show()
            return f_window


if __name__ == "__main__":
    def _main():
        import sys
        app = QtGui.QApplication(sys.argv)
        f_window = project_recover_dialog()
        exit(app.exec_())

    _main()
