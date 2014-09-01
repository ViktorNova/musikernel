# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore
from libpydaw import pydaw_util
from libpydaw.translate import _

def global_set_region_editor_zoom():
    global REGION_EDITOR_GRID_WIDTH
    global MIDI_SCALE

    f_width = float(REGION_EDITOR.rect().width()) - \
        float(REGION_EDITOR.verticalScrollBar().width()) - 6.0 - \
        REGION_TRACK_WIDTH
    f_region_scale = f_width / (ITEM_EDITING_COUNT * 1000.0)

    REGION_EDITOR_GRID_WIDTH = 1000.0 * MIDI_SCALE * f_region_scale
    pydaw_set_region_editor_quantize(REGION_EDITOR_QUANTIZE_INDEX)

ITEM_EDITING_COUNT = 1

REGION_EDITOR_SNAP = False
REGION_EDITOR_GRID_WIDTH = 800.0
REGION_TRACK_WIDTH = 180  #Width of the tracks in px
REGION_EDITOR_MAX_START = 999.0 + REGION_TRACK_WIDTH
REGION_EDITOR_TRACK_HEIGHT = pydaw_util.get_file_setting("TRACK_VZOOM", int, 80)
REGION_EDITOR_SNAP_DIVISOR = 16.0
REGION_EDITOR_SNAP_BEATS = 4.0 / REGION_EDITOR_SNAP_DIVISOR
REGION_EDITOR_SNAP_VALUE = REGION_EDITOR_GRID_WIDTH / REGION_EDITOR_SNAP_DIVISOR
REGION_EDITOR_SNAP_DIVISOR_BEATS = REGION_EDITOR_SNAP_DIVISOR / 4.0
REGION_EDITOR_TRACK_COUNT = 32
REGION_EDITOR_HEADER_HEIGHT = 45
#gets updated by the piano roll to it's real value:
REGION_EDITOR_TOTAL_HEIGHT = 1000
REGION_EDITOR_QUANTIZE_INDEX = 4

SELECTED_ITEM_GRADIENT = QtGui.QLinearGradient(
    QtCore.QPointF(0, 0), QtCore.QPointF(0, 12))
SELECTED_ITEM_GRADIENT.setColorAt(0, QtGui.QColor(180, 172, 100))
SELECTED_ITEM_GRADIENT.setColorAt(1, QtGui.QColor(240, 240, 240))

SELECTED_REGION_ITEM = None   #Used for mouse click hackery

def pydaw_set_region_editor_quantize(a_index):
    global REGION_EDITOR_SNAP
    global REGION_EDITOR_SNAP_VALUE
    global REGION_EDITOR_SNAP_DIVISOR
    global REGION_EDITOR_SNAP_DIVISOR_BEATS
    global REGION_EDITOR_SNAP_BEATS
    global LAST_NOTE_RESIZE
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
    LAST_NOTE_RESIZE = pydaw_util.pydaw_clip_min(
        LAST_NOTE_RESIZE, REGION_EDITOR_SNAP_BEATS)
    REGION_EDITOR.set_grid_div(REGION_EDITOR_SNAP_DIVISOR / 4.0)
    REGION_EDITOR_SNAP_DIVISOR *= ITEM_EDITING_COUNT
    REGION_EDITOR_SNAP_VALUE = (REGION_EDITOR_GRID_WIDTH *
        ITEM_EDITING_COUNT) / REGION_EDITOR_SNAP_DIVISOR
    REGION_EDITOR_SNAP_DIVISOR_BEATS = \
        REGION_EDITOR_SNAP_DIVISOR / (4.0 * ITEM_EDITING_COUNT)

REGION_EDITOR_MIN_NOTE_LENGTH = REGION_EDITOR_GRID_WIDTH / 128.0

PIANO_NOTE_GRADIENT_TUPLE = \
    ((255, 0, 0), (255, 123, 0), (255, 255, 0), (123, 255, 0), (0, 255, 0),
     (0, 255, 123), (0, 255, 255), (0, 123, 255), (0, 0, 255), (0, 0, 255))

REGION_EDITOR_DELETE_MODE = False
REGION_EDITOR_DELETED_NOTES = []

LAST_NOTE_RESIZE = 0.25

REGION_EDITOR_HEADER_GRADIENT = QtGui.QLinearGradient(
    0.0, 0.0, 0.0, REGION_EDITOR_HEADER_HEIGHT)
REGION_EDITOR_HEADER_GRADIENT.setColorAt(0.0, QtGui.QColor.fromRgb(61, 61, 61))
REGION_EDITOR_HEADER_GRADIENT.setColorAt(0.5, QtGui.QColor.fromRgb(50,50, 50))
REGION_EDITOR_HEADER_GRADIENT.setColorAt(0.6, QtGui.QColor.fromRgb(43, 43, 43))
REGION_EDITOR_HEADER_GRADIENT.setColorAt(1.0, QtGui.QColor.fromRgb(65, 65, 65))

def region_editor_set_delete_mode(a_enabled):
    global REGION_EDITOR_DELETE_MODE, REGION_EDITOR_DELETED_NOTES
    if a_enabled:
        REGION_EDITOR.setDragMode(QtGui.QGraphicsView.NoDrag)
        REGION_EDITOR_DELETED_NOTES = []
        REGION_EDITOR_DELETE_MODE = True
        QtGui.QApplication.setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.ForbiddenCursor))
    else:
        REGION_EDITOR.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
        REGION_EDITOR_DELETE_MODE = False
        for f_item in REGION_EDITOR_DELETED_NOTES:
            f_item.delete()
        REGION_EDITOR.selected_note_strings = []
        global_save_and_reload_items()
        QtGui.QApplication.restoreOverrideCursor()


class region_editor_item(QtGui.QGraphicsRectItem):
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
        REGION_EDITOR_TRACK_HEIGHT = a_note_height
        self.current_note_text = None
        self.note_item = a_note_item
        self.setAcceptHoverEvents(True)
        self.resize_start_pos = self.note_item.start
        self.is_copying = False
        self.is_velocity_dragging = False
        self.is_velocity_curving = False
        if SELECTED_REGION_ITEM is not None and \
        a_note_item == SELECTED_REGION_ITEM:
            self.is_resizing = True
            REGION_EDITOR.click_enabled = True
        else:
            self.is_resizing = False
        self.showing_resize_cursor = False
        self.resize_rect = self.rect()
        self.mouse_y_pos = QtGui.QCursor.pos().y()
        self.note_text = QtGui.QGraphicsSimpleTextItem(self)
        self.note_text.setPen(QtGui.QPen(QtCore.Qt.black))
        self.note_text.setText("TODO")
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
        f_gradient = QtGui.QLinearGradient(0.0, 0.0, 0.0, REGION_EDITOR_TRACK_HEIGHT)
        f_gradient.setColorAt(0.0, QtGui.QColor(*f_vals_m1))
        f_gradient.setColorAt(0.4, QtGui.QColor(*f_vals))
        f_gradient.setColorAt(0.6, QtGui.QColor(*f_vals))
        f_gradient.setColorAt(1.0, QtGui.QColor(*f_vals_m2))
        self.setBrush(f_gradient)

    def mouse_is_at_end(self, a_pos):
        f_width = self.rect().width()
        if f_width >= 30.0:
            return a_pos.x() > (f_width - 15.0)
        else:
            return a_pos.x() > (f_width * 0.72)

    def hoverMoveEvent(self, a_event):
        #QtGui.QGraphicsRectItem.hoverMoveEvent(self, a_event)
        if not self.is_resizing:
            REGION_EDITOR.click_enabled = False
            self.show_resize_cursor(a_event)

    def delete_later(self):
        global REGION_EDITOR_DELETED_NOTES
        if self.isEnabled() and self not in REGION_EDITOR_DELETED_NOTES:
            REGION_EDITOR_DELETED_NOTES.append(self)
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
        REGION_EDITOR.click_enabled = False

    def hoverLeaveEvent(self, a_event):
        QtGui.QGraphicsRectItem.hoverLeaveEvent(self, a_event)
        REGION_EDITOR.click_enabled = True
        QtGui.QApplication.restoreOverrideCursor()
        self.showing_resize_cursor = False

    def mouseDoubleClickEvent(self, a_event):
        QtGui.QGraphicsRectItem.mouseDoubleClickEvent(self, a_event)
        QtGui.QApplication.restoreOverrideCursor()

    def mousePressEvent(self, a_event):
        if a_event.modifiers() == QtCore.Qt.ShiftModifier:
            region_editor_set_delete_mode(True)
            self.delete_later()
        elif a_event.modifiers() == \
        QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier:
            self.is_velocity_dragging = True
        elif a_event.modifiers() == \
        QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier:
            self.is_velocity_curving = True
            f_list = [((x.item_index * 4.0) + x.note_item.start)
                for x in REGION_EDITOR.get_selected_items()]
            f_list.sort()
            self.vc_start = f_list[0]
            self.vc_mid = (self.item_index * 4.0) + self.note_item.start
            self.vc_end = f_list[-1]
        else:
            a_event.setAccepted(True)
            QtGui.QGraphicsRectItem.mousePressEvent(self, a_event)
            self.setBrush(SELECTED_ITEM_GRADIENT)
            self.o_pos = self.pos()
            if self.mouse_is_at_end(a_event.pos()):
                self.is_resizing = True
                self.mouse_y_pos = QtGui.QCursor.pos().y()
                self.resize_last_mouse_pos = a_event.pos().x()
                for f_item in REGION_EDITOR.get_selected_items():
                    f_item.resize_start_pos = f_item.note_item.start + (
                        4.0 * f_item.item_index)
                    f_item.resize_pos = f_item.pos()
                    f_item.resize_rect = f_item.rect()
            elif a_event.modifiers() == QtCore.Qt.ControlModifier:
                self.is_copying = True
                for f_item in REGION_EDITOR.get_selected_items():
                    REGION_EDITOR.draw_item(
                        f_item.note_item, f_item.item_index)
        if self.is_velocity_curving or self.is_velocity_dragging:
            a_event.setAccepted(True)
            self.setSelected(True)
            QtGui.QGraphicsRectItem.mousePressEvent(self, a_event)
            self.orig_y = a_event.pos().y()
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.BlankCursor)
            for f_item in REGION_EDITOR.get_selected_items():
                f_item.orig_value = f_item.note_item.velocity
                f_item.set_brush()
            for f_item in REGION_EDITOR.note_items:
                f_item.note_text.setText(str(f_item.note_item.velocity))
        REGION_EDITOR.click_enabled = True

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
        for f_item in REGION_EDITOR.get_selected_items():
            if self.is_resizing:
                if REGION_EDITOR_SNAP:
                    f_adjusted_width = round(
                        f_pos_x / REGION_EDITOR_SNAP_VALUE) * \
                        REGION_EDITOR_SNAP_VALUE
                    if f_adjusted_width == 0.0:
                        f_adjusted_width = REGION_EDITOR_SNAP_VALUE
                else:
                    f_adjusted_width = pydaw_clip_min(
                        f_pos_x, REGION_EDITOR_MIN_NOTE_LENGTH)
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
                if f_pos_x < REGION_TRACK_WIDTH:
                    f_pos_x = REGION_TRACK_WIDTH
                elif f_pos_x > REGION_EDITOR_MAX_START:
                    f_pos_x = REGION_EDITOR_MAX_START
                if f_pos_y < REGION_EDITOR_HEADER_HEIGHT:
                    f_pos_y = REGION_EDITOR_HEADER_HEIGHT
                elif f_pos_y > REGION_EDITOR_TOTAL_HEIGHT:
                    f_pos_y = REGION_EDITOR_TOTAL_HEIGHT
                f_pos_y = \
                    (int((f_pos_y - REGION_EDITOR_HEADER_HEIGHT) /
                    REGION_EDITOR_TRACK_HEIGHT) * REGION_EDITOR_TRACK_HEIGHT) + \
                    REGION_EDITOR_HEADER_HEIGHT
                if REGION_EDITOR_SNAP:
                    f_pos_x = (int((f_pos_x - REGION_TRACK_WIDTH) /
                    REGION_EDITOR_SNAP_VALUE) *
                    REGION_EDITOR_SNAP_VALUE) + REGION_TRACK_WIDTH
                f_item.setPos(f_pos_x, f_pos_y)
                f_new_note = self.y_pos_to_note(f_pos_y)
                f_item.update_note_text(f_new_note)

    def y_pos_to_note(self, a_y):
        return int(REGION_EDITOR_TRACK_COUNT -
            ((a_y - REGION_EDITOR_HEADER_HEIGHT) /
            REGION_EDITOR_TRACK_HEIGHT))

    def mouseReleaseEvent(self, a_event):
        if REGION_EDITOR_DELETE_MODE:
            region_editor_set_delete_mode(False)
            return
        a_event.setAccepted(True)
        f_recip = 1.0 / REGION_EDITOR_GRID_WIDTH
        QtGui.QGraphicsRectItem.mouseReleaseEvent(self, a_event)
        global SELECTED_REGION_ITEM
        if self.is_copying:
            f_new_selection = []
        for f_item in REGION_EDITOR.get_selected_items():
            f_pos_x = f_item.pos().x()
            f_pos_y = f_item.pos().y()
            if self.is_resizing:
                f_new_note_length = ((f_pos_x + f_item.rect().width() -
                    REGION_TRACK_WIDTH) * f_recip *
                    4.0) - f_item.resize_start_pos
                if SELECTED_REGION_ITEM is not None and \
                self.note_item != SELECTED_REGION_ITEM:
                    f_new_note_length -= (self.item_index * 4.0)
                if REGION_EDITOR_SNAP and \
                f_new_note_length < REGION_EDITOR_SNAP_BEATS:
                    f_new_note_length = REGION_EDITOR_SNAP_BEATS
                elif f_new_note_length < pydaw_min_note_length:
                    f_new_note_length = pydaw_min_note_length
                f_item.note_item.set_length(f_new_note_length)
            elif self.is_velocity_dragging or self.is_velocity_curving:
                pass
            else:
                f_new_note_start = (f_pos_x -
                    REGION_TRACK_WIDTH) * 4.0 * f_recip
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
        SELECTED_REGION_ITEM = None
        REGION_EDITOR.selected_note_strings = []
        if self.is_copying:
            for f_new_item in f_new_selection:
                REGION_EDITOR.selected_note_strings.append(
                    f_new_item.get_selected_string())
        else:
            for f_item in REGION_EDITOR.get_selected_items():
                REGION_EDITOR.selected_note_strings.append(
                    f_item.get_selected_string())
        for f_item in REGION_EDITOR.note_items:
            f_item.is_resizing = False
            f_item.is_copying = False
            f_item.is_velocity_dragging = False
            f_item.is_velocity_curving = False
        global_save_and_reload_items()
        self.showing_resize_cursor = False
        QtGui.QApplication.restoreOverrideCursor()
        REGION_EDITOR.click_enabled = True


class region_editor(QtGui.QGraphicsView):
    def __init__(self):
        QtGui.QGraphicsView.__init__(self)
        self.item_length = 8.0
        self.viewer_width = 1000
        self.grid_div = 16

        self.end_octave = 8
        self.start_octave = -2
        self.notes_in_octave = 12
        self.padding = 2

        self.update_note_height()

        self.scene = QtGui.QGraphicsScene(self)
        self.scene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
        self.scene.setBackgroundBrush(QtGui.QColor(100, 100, 100))
        self.scene.mousePressEvent = self.sceneMousePressEvent
        self.scene.mouseReleaseEvent = self.sceneMouseReleaseEvent
        self.setAlignment(QtCore.Qt.AlignLeft)
        self.setScene(self.scene)
        self.first_open = True
        self.draw_header()
        self.draw_tracks()
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
        self.clipboard = []

    def update_note_height(self):
        self.tracks_height = \
            REGION_EDITOR_TRACK_HEIGHT * REGION_EDITOR_TRACK_COUNT

        global REGION_EDITOR_TOTAL_HEIGHT
        REGION_EDITOR_TOTAL_HEIGHT = \
            self.tracks_height + REGION_EDITOR_HEADER_HEIGHT

    def get_selected_items(self):
        return (x for x in self.note_items if x.isSelected())

    def get_item_coord(self):
        f_pos = QtGui.QCursor.pos()
        f_pos_x = f_pos.x()
        f_pos_y = f_pos.y()
        if f_pos_x < REGION_TRACK_WIDTH or \
        f_pos_y < REGION_EDITOR_HEADER_HEIGHT:
            return None


    def set_tooltips(self, a_on):
        if a_on:
            self.setToolTip("TODO")
        else:
            self.setToolTip("")

    def prepare_to_quit(self):
        self.scene.clearSelection()
        self.scene.clear()

    def set_grid_div(self, a_div):
        self.grid_div = int(a_div)

    def scrollContentsBy(self, x, y):
        QtGui.QGraphicsView.scrollContentsBy(self, x, y)
        self.set_header_and_keys()

    def set_header_and_keys(self):
        f_point = self.get_scene_pos()
        self.tracks.setPos(f_point.x(), REGION_EDITOR_HEADER_HEIGHT)
        self.header.setPos(REGION_TRACK_WIDTH + self.padding, f_point.y())

    def get_scene_pos(self):
        return QtCore.QPointF(
            self.horizontalScrollBar().value(),
            self.verticalScrollBar().value())

    def highlight_selected(self):
        self.has_selected = False
        for f_item in self.note_items:
            if f_item.isSelected():
                f_item.setBrush(SELECTED_ITEM_GRADIENT)
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

    def focusOutEvent(self, a_event):
        QtGui.QGraphicsView.focusOutEvent(self, a_event)
        QtGui.QApplication.restoreOverrideCursor()

    def sceneMouseReleaseEvent(self, a_event):
        if REGION_EDITOR_DELETE_MODE:
            region_editor_set_delete_mode(False)
        else:
            QtGui.QGraphicsScene.mouseReleaseEvent(self.scene, a_event)
        self.click_enabled = True

    def sceneMousePressEvent(self, a_event):
        if a_event.button() == QtCore.Qt.RightButton:
            return
        elif a_event.modifiers() == QtCore.Qt.ControlModifier:
            self.hover_restore_cursor_event()
        elif a_event.modifiers() == QtCore.Qt.ShiftModifier:
            region_editor_set_delete_mode(True)
            return
        elif self.click_enabled:
            self.scene.clearSelection()
            f_pos_x = a_event.scenePos().x()
            f_pos_y = a_event.scenePos().y()
            if f_pos_x > REGION_TRACK_WIDTH and \
            f_pos_x < REGION_EDITOR_MAX_START and \
            f_pos_y > REGION_EDITOR_HEADER_HEIGHT and \
            f_pos_y < REGION_EDITOR_TOTAL_HEIGHT:
                f_recip = 1.0 / REGION_EDITOR_GRID_WIDTH
                f_note = int(
                    REGION_EDITOR_TRACK_COUNT - ((f_pos_y -
                    REGION_EDITOR_HEADER_HEIGHT) / REGION_EDITOR_TRACK_HEIGHT)) + 1
                if REGION_EDITOR_SNAP:
                    f_beat = (int((f_pos_x - REGION_TRACK_WIDTH) /
                        REGION_EDITOR_SNAP_VALUE) *
                        REGION_EDITOR_SNAP_VALUE) * f_recip * 4.0
                    f_note_item = pydaw_item(
                        f_beat, LAST_NOTE_RESIZE, f_note, self.get_vel(f_beat))
                else:
                    f_beat = (f_pos_x -
                        REGION_TRACK_WIDTH) * f_recip * 4.0
                    f_note_item = pydaw_note(
                        f_beat, 0.25, f_note, self.get_vel(f_beat))
                f_note_index = ITEM_EDITOR.add_note(f_note_item)
                global SELECTED_REGION_ITEM
                SELECTED_REGION_ITEM = f_note_item
                f_drawn_item = self.draw_item(f_note_item, f_note_index)
                f_drawn_item.setSelected(True)

        a_event.setAccepted(True)
        QtGui.QGraphicsScene.mousePressEvent(self.scene, a_event)
        QtGui.QApplication.restoreOverrideCursor()

    def mouseMoveEvent(self, a_event):
        QtGui.QGraphicsView.mouseMoveEvent(self, a_event)
        if REGION_EDITOR_DELETE_MODE:
            for f_item in self.items(a_event.pos()):
                if isinstance(f_item, region_editor_item):
                    f_item.delete_later()

    def hover_restore_cursor_event(self, a_event=None):
        QtGui.QApplication.restoreOverrideCursor()

    def draw_header(self):
        self.header = QtGui.QGraphicsRectItem(
            0, 0, self.viewer_width, REGION_EDITOR_HEADER_HEIGHT)
        self.header.hoverEnterEvent = self.hover_restore_cursor_event
        self.header.setBrush(REGION_EDITOR_HEADER_GRADIENT)
        self.scene.addItem(self.header)
        #self.header.mapToScene(REGION_TRACK_WIDTH + self.padding, 0.0)
        self.beat_width = self.viewer_width / self.item_length
        self.value_width = self.beat_width / self.grid_div
        self.header.setZValue(1003.0)

    def draw_tracks(self):
        f_brush = QtGui.QLinearGradient(0.0, 0.0, 0.0, REGION_EDITOR_TRACK_HEIGHT)
        f_brush.setColorAt(0.0, QtGui.QColor(234, 234, 234))
        f_brush.setColorAt(0.5, QtGui.QColor(159, 159, 159))
        self.tracks_widget = QtGui.QWidget()
        self.tracks_widget.setFixedSize(
            QtCore.QSize(REGION_TRACK_WIDTH, self.tracks_height))

        self.tracks_layout = QtGui.QVBoxLayout(self.tracks_widget)
        self.tracks_layout.setContentsMargins(0, 0, 0, 0)
        self.tracks = self.scene.addWidget(self.tracks_widget)

        for i in range(REGION_EDITOR_TRACK_COUNT):
            f_track = seq_track(i)
            self.tracks_layout.addWidget(f_track.group_box)
            #f_track.setBrush(f_brush)
        self.tracks.setZValue(1000.0)

    def draw_grid(self):
        f_brush = QtGui.QLinearGradient(0.0, 0.0, 0.0, REGION_EDITOR_TRACK_HEIGHT)
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
            f_note_bar.setPos(
                REGION_TRACK_WIDTH + self.padding, f_note_bar_y)
        f_beat_pen = QtGui.QPen()
        f_beat_pen.setWidth(2)
        f_beat_y = self.tracks_height + REGION_EDITOR_HEADER_HEIGHT
        for i in range(0, int(self.item_length)):
            f_beat_x = (self.beat_width * i) + REGION_TRACK_WIDTH
            f_beat = self.scene.addLine(f_beat_x, 0, f_beat_x, f_beat_y)
            f_beat.setPen(f_beat_pen)
            if i < self.item_length:
                f_number = QtGui.QGraphicsSimpleTextItem(
                    str(i + 1), self.header)
                f_number.setFlag(
                    QtGui.QGraphicsItem.ItemIgnoresTransformations)
                f_number.setPos((self.beat_width * i), 24)
                f_number.setBrush(QtCore.Qt.white)

    def resizeEvent(self, a_event):
        QtGui.QGraphicsView.resizeEvent(self, a_event)

    def clear_drawn_items(self):
        self.note_items = []
        self.scene.clear()
        self.update_note_height()
        self.draw_header()
        self.draw_tracks()
        self.draw_grid()
        self.set_header_and_keys()

    def draw_region(self):
        self.has_selected = False #Reset the selected-ness state...
        self.viewer_width = REGION_EDITOR_GRID_WIDTH * ITEM_EDITING_COUNT
        self.setSceneRect(
            0.0, 0.0, self.viewer_width + REGION_EDITOR_GRID_WIDTH,
            self.tracks_height + REGION_EDITOR_HEADER_HEIGHT + 24.0)
        self.item_length = float(4 * ITEM_EDITING_COUNT)
        global REGION_EDITOR_MAX_START
        REGION_EDITOR_MAX_START = ((REGION_EDITOR_GRID_WIDTH - 1.0) *
            ITEM_EDITING_COUNT) + REGION_TRACK_WIDTH
        self.setUpdatesEnabled(False)
        self.clear_drawn_items()
        if ITEM_EDITOR.enabled:
            f_item_count = len(ITEM_EDITOR.items)
            for f_i, f_item in zip(range(f_item_count), ITEM_EDITOR.items):
                for f_note in f_item.notes:
                    f_note_item = self.draw_item(f_note, f_i)
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
                        f_note_item = self.draw_item(f_note, f_i, False)
            self.scrollContentsBy(0, 0)
            for f_name, f_i in zip(
            ITEM_EDITOR.item_names, range(len(ITEM_EDITOR.item_names))):
                f_text = QtGui.QGraphicsSimpleTextItem(f_name, self.header)
                f_text.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations)
                f_text.setBrush(QtCore.Qt.yellow)
                f_text.setPos((f_i * REGION_EDITOR_GRID_WIDTH), 2.0)
        self.setUpdatesEnabled(True)
        self.update()

    def draw_item(self, a_note, a_item_index, a_enabled=True):
        """ a_note is an instance of the pydaw_note class"""
        f_start = REGION_TRACK_WIDTH + self.padding + \
            self.beat_width * (a_note.start + (float(a_item_index) * 4.0))
        f_length = self.beat_width * a_note.length
        f_note = REGION_EDITOR_HEADER_HEIGHT + REGION_EDITOR_TRACK_HEIGHT * \
            (REGION_EDITOR_TRACK_COUNT - a_note.note_num)
        f_note_item = region_editor_item(
            f_length, REGION_EDITOR_TRACK_HEIGHT, a_note.note_num,
            a_note, a_item_index, a_enabled)
        f_note_item.setPos(f_start, f_note)
        self.scene.addItem(f_note_item)
        if a_enabled:
            self.note_items.append(f_note_item)
            return f_note_item


class plugin_settings:
    instrument = 0
    effect = 1
    def __init__(self, a_index, a_track_num,
                 a_layout, a_type, a_save_callback, a_name_callback):
        self.suppress_osc = False
        self.save_callback = a_save_callback
        self.name_callback = a_name_callback
        self.plugin_uid = -1
        self.type = a_type
        self.track_num = a_track_num
        f_offset = 0 if self.type == self.instrument else 10
        self.index = a_index
        self.plugin_combobox = QtGui.QComboBox()
        self.plugin_combobox.setMinimumWidth(150)
        self.plugin_combobox.wheelEvent = self.wheel_event
        if self.type == plugin_settings.instrument:
            self.plugin_combobox.addItems(
                ["None", "Euphoria", "Ray-V", "Way-V"])
        elif self.type == plugin_settings.effect:
            self.plugin_combobox.addItems(["None", "Modulex"])
        self.plugin_combobox.currentIndexChanged.connect(
            self.on_plugin_change)
        a_layout.addWidget(self.plugin_combobox, a_index + 1, f_offset)
        self.ui_button = QtGui.QPushButton("UI")
        self.ui_button.pressed.connect(self.on_show_ui)
        self.ui_button.setObjectName("uibutton")
        self.ui_button.setFixedWidth(24)
        a_layout.addWidget(self.ui_button, a_index + 1, f_offset + 1)

    def set_value(self, a_val):
        self.suppress_osc = True
        self.plugin_combobox.setCurrentIndex(a_val.plugin_index)
        self.plugin_uid = a_val.plugin_uid
        self.suppress_osc = False

    def get_value(self):
        return pydaw_track_plugin(
            self.type, self.index, self.plugin_combobox.currentIndex(),
            self.plugin_uid)

    def on_plugin_change(self, a_val):
        if self.suppress_osc:
            return
        if a_val == 0:
            self.plugin_uid = -1
        else:
            self.plugin_uid = PROJECT.get_next_plugin_uid()
        PROJECT.this_pydaw_osc.pydaw_set_plugin_index(
            self.track_num, self.type, self.index,
            a_val, self.plugin_uid)
        self.save_callback()

    def wheel_event(self, a_event=None):
        pass

    def on_show_ui(self):
        f_index = self.plugin_combobox.currentIndex()
        if f_index == 0 or self.plugin_uid == -1:
            return
        global_open_plugin_ui(
            self.plugin_uid, self.type, f_index,
            "Track:  {}".format(self.name_callback()))


class track_send:
    def __init__(self, a_index, a_track_num, a_layout, a_save_callback):
        self.save_callback = a_save_callback
        self.suppress_osc = True
        self.track_num = a_track_num
        self.index = int(a_index)
        self.bus_combobox = QtGui.QComboBox()
        self.bus_combobox.setMinimumWidth(180)
        self.bus_combobox.wheelEvent = self.wheel_event
        self.bus_combobox.currentIndexChanged.connect(self.on_bus_changed)
        self.update_names()
        a_layout.addWidget(self.bus_combobox, a_index + 1, 20)
        self.vol_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        a_layout.addWidget(self.vol_slider, a_index + 1, 21)
        self.vol_slider.setMinimumWidth(300)
        self.vol_slider.setRange(-400, 120)
        self.vol_slider.setValue(0)
        self.vol_slider.valueChanged.connect(self.on_vol_changed)
        self.vol_slider.sliderReleased.connect(self.on_vol_released)
        self.vol_label = QtGui.QLabel("0.0dB")
        self.vol_label.setMinimumWidth(60)
        a_layout.addWidget(self.vol_label, a_index + 1, 22)
        self.suppress_osc = False

    def on_bus_changed(self, a_value=0):
        self.update_engine()

    def update_engine(self):
        if not self.suppress_osc:
            f_graph = PROJECT.get_routing_graph()
            if not self.track_num in f_graph.graph:
                f_graph.graph[self.track_num] = {}
            f_graph.graph[self.track_num][self.index] = self.get_value()
            PROJECT.save_routing_graph(f_graph)

    def get_vol(self):
        return round(self.vol_slider.value() * 0.1, 1)

    def set_vol(self, a_val):
        self.vol_slider.setValue(int(a_val * 10.0))

    def on_vol_changed(self, a_val):
        f_val = self.get_vol()
        self.vol_label.setText("{}dB".format(f_val))
        if not self.suppress_osc:
            PROJECT.this_pydaw_osc.pydaw_send_vol(
                self.track_num, self.index, self.get_vol())

    def on_vol_released(self):
        self.update_engine()

    def wheel_event(self, a_event=None):
        pass

    def get_value(self):
        return pydaw_track_send(
            self.track_num, self.index,
            self.bus_combobox.currentIndex() - 1,
            round(self.get_vol()))

    def set_value(self, a_val):
        self.suppress_osc = True
        self.set_vol(a_val.vol)
        self.bus_combobox.setCurrentIndex(a_val.output + 1)
        self.suppress_osc = False

    def update_names(self):
        f_index = pydaw_clip_min(self.bus_combobox.currentIndex(), 0)
        # TODO^^^^^  Why does that do that?
        self.suppress_osc = True
        self.bus_combobox.clear()
        self.bus_combobox.addItems(["None"] + TRACK_NAMES)
        self.bus_combobox.setCurrentIndex(f_index)
        self.suppress_osc = False

TRACK_COUNT_ALL = 32

TRACK_NAMES = ["Master" if x == 0 else "track{}".format(x)
    for x in range(TRACK_COUNT_ALL)]

class seq_track:
    def __init__(self, a_track_num, a_track_text=_("track")):
        self.suppress_osc = True
        self.track_number = a_track_num
        self.group_box = QtGui.QWidget()
        self.group_box.contextMenuEvent = self.context_menu_event
        self.group_box.setObjectName("track_panel")
        self.group_box.setFixedHeight(REGION_EDITOR_TRACK_HEIGHT)
        self.main_hlayout = QtGui.QHBoxLayout()
        self.main_hlayout.setContentsMargins(2, 2, 2, 2)
        self.main_vlayout = QtGui.QVBoxLayout()
        self.main_hlayout.addLayout(self.main_vlayout)
        self.peak_meter = pydaw_widgets.peak_meter()
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
        self.menu_widget = QtGui.QWidget()
        self.menu_hlayout = QtGui.QHBoxLayout(self.menu_widget)
        self.menu_gridlayout = QtGui.QGridLayout()
        self.menu_hlayout.addLayout(self.menu_gridlayout)
        self.instruments = []
        if a_track_num != 0:
            self.menu_gridlayout.addWidget(
                QtGui.QLabel(_("Instruments")), 0, 0)
            for f_i in range(5):
                f_plugin = plugin_settings(
                    f_i, self.track_number, self.menu_gridlayout,
                    plugin_settings.instrument, self.save_callback,
                    self.name_callback)
                self.instruments.append(f_plugin)
        self.menu_gridlayout.addWidget(
            QtGui.QLabel(_("Effects")), 0, 10)
        self.effects = []
        for f_i in range(10):
            f_plugin = plugin_settings(
                f_i, self.track_number, self.menu_gridlayout,
                plugin_settings.effect, self.save_callback,
                self.name_callback)
            self.effects.append(f_plugin)
        self.sends = []
        if self.track_number != 0:
            self.menu_gridlayout.addWidget(
                QtGui.QLabel(_("Sends")), 0, 20)
            for f_i in range(4):
                f_send = track_send(
                    f_i, self.track_number, self.menu_gridlayout,
                    self.save_callback)
                self.sends.append(f_send)
        self.action_widget = QtGui.QWidgetAction(self.button_menu)
        self.action_widget.setDefaultWidget(self.menu_widget)
        self.button_menu.addAction(self.action_widget)
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
        self.suppress_osc = False

    def menu_button_pressed(self):
        for f_send in self.sends:
            f_send.update_names()

    def on_solo(self, value):
        if not self.suppress_osc:
            PROJECT.this_pydaw_osc.pydaw_set_solo(
                self.track_number, self.solo_checkbox.isChecked())
            PROJECT.save_tracks(REGION_INST_EDITOR.get_tracks())
            PROJECT.commit(_("Set solo for track {} to {}").format(
                self.track_number, self.solo_checkbox.isChecked()))

    def on_mute(self, value):
        if not self.suppress_osc:
            PROJECT.this_pydaw_osc.pydaw_set_mute(
                self.track_number, self.mute_checkbox.isChecked())
            PROJECT.save_tracks(REGION_INST_EDITOR.get_tracks())
            PROJECT.commit(_("Set mute for track {} to {}").format(
                self.track_number, self.mute_checkbox.isChecked()))

    def on_name_changed(self):
        f_name = pydaw_remove_bad_chars(self.track_name_lineedit.text())
        self.track_name_lineedit.setText(f_name)
        global_update_track_comboboxes(self.track_number, f_name)
        PROJECT.save_tracks(REGION_INST_EDITOR.get_tracks())
        PROJECT.commit(
            _("Set name for track {} to {}").format(self.track_number,
            self.track_name_lineedit.text()))
        f_plugins = PROJECT.get_track_plugins(self.track_number)
        if not f_plugins:
            return
        for f_plugin in f_plugins.instruments + f_plugins.effects:
            global_plugin_set_window_title(
                f_plugin.plugin_uid,
                _("Track: {}").format(self.name_callback()))

    def context_menu_event(self, a_event=None):
        pass

    def save_callback(self):
        f_result = pydaw_track_plugins(
            [x.get_value() for x in self.instruments],
            [x.get_value() for x in self.effects])
        PROJECT.save_track_plugins(self.track_number, f_result)
        PROJECT.commit(
            "Update track plugins for '{}', {}".format(
            self.name_callback(), self.track_number))

    def name_callback(self):
        return str(self.track_name_lineedit.text())

    def open_track(self, a_track, a_notify_osc=False):
        if not a_notify_osc:
            self.suppress_osc = True
        if self.track_number != 0:
            self.track_name_lineedit.setText(a_track.name)
            self.solo_checkbox.setChecked(a_track.solo)
            self.mute_checkbox.setChecked(a_track.mute)
        f_plugins = PROJECT.get_track_plugins(self.track_number)
        if not f_plugins:
            return
        if self.track_number != 0:
            for f_plugin in f_plugins.instruments:
                self.instruments[f_plugin.index].set_value(f_plugin)
        for f_plugin in f_plugins.effects:
            self.effects[f_plugin.index].set_value(f_plugin)

        f_graph = PROJECT.get_routing_graph()
        if self.track_number in f_graph.graph:
            f_sends = f_graph.graph[self.track_number]
            for f_i, f_send in f_sends.items():
                self.sends[f_i].set_value(f_send)

        self.suppress_osc = False

    def get_track(self):
        return pydaw_track(
            self.track_number, self.solo_checkbox.isChecked(),
            self.mute_checkbox.isChecked(),
            self.track_number, self.track_name_lineedit.text())




import sys
from libpydaw import *

#test = QtGui.QGraphicsProxyWidget()
#test.setLayout()
APP = QtGui.QApplication(sys.argv)
REGION_EDITOR = region_editor()
REGION_EDITOR.show()

PROJECT = pydaw_project(False)
PROJECT.open_project(
    "/home/userbuntu/musikernel/default-project/default.musikernel", False)

APP.exec_()
