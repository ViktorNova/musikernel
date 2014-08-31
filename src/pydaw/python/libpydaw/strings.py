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

from libpydaw.translate import _

region_list_editor = _(
"""This is a region editor, it consists of items and tracks.
A track can be any/all of: instrument, audio, bus or send.
An item is one bar of MIDI notes or plugin automation.
Click an empty cell to add a new item.
Double click an item to open it in the piano-roll-editor or select
 multiple and right-click->'Edit Selected Items'

The selected items can be copied by pressing CTRL+C, cut with CTRL+X,
 pasted with CTRL+V, and deleted by pressing 'Delete'

Additional functions can be found by right-clicking on
the items, the term 'unlink' means to create a new copy of the item that
does not change it's parent item when edited.
(by default all items are 'ghost items' that update all
items with the same name)
Click 'Menu->Show Tooltips' in the transport to disable these tooltips""")

audio_viewer_item = _(
"""Right click on an audio item to see the various tools and actions available.
Click and drag selected to move.
SHIFT+Click to split items
CTRL+drag to copy selected items
CTRL+ALT+Click and drag to adjust the volume of selected items
CTRL+SHIFT+Click and drag to create a volume line from the selected items
You can multi-select individual items by SHIFT+ALT+clicking on them.

You can glue together multiple items by selecting items and pressing CTRL+G,
the glued item will retain all of the fades, stretches and per-item fx of
the original items.\n""")


audio_viewer_widget_folders = _(
"""Use this tab to browse your folders and files.
Drag and drop one file at a time onto the sequencer.
.wav and .aiff files are the only supported audio file format.
Click the 'Bookmark' button to save the current folder to your
bookmarks located on the 'Bookmarks' tab.

Click 'Menu->Show Tooltips' in the transport to disable these tooltips""")


audio_viewer_widget_modulex = _(
"""This tab allows you to set effects per-item.
The tab is only enabled when you have exactly one item selected,
the copy and paste buttons allow you to copy settings between
multipe items.""")


timestretch_modes = _(
"""Modes:
None:  No stretching or pitch adjustment

Pitch affecting time:  Repitch the item, it will become
shorter at higher pitches, and longer at lower pitches

Time affecting pitch:  Stretch the item to the desired length, it will have
lower pitch at longer lengths, and higher pitch at shorter lengths

Rubberband:  Adjust pitch and time independently

Rubberband (formants): Same as Rubberband, but preserves formants

SBSMS:  Adjust pitch and time independently, also with the ability to
set start/end pitch/time differently

Paulstretch:  Mostly for stretching items very long, creates a very smeared,
atmospheric sound""")


transport = _(
"""This is the transport, use this control to start/stop
playback or recording.
You can start or stop playback by pressing spacebar
The MIDI controller used for recording is selected in the
File->HardwareSettings menu
The 'Loop Mode' combobox can be used to loop a region.
The 'Follow' checkbox causes the UI to follow the project's playback position
The 'Overdub' checkbox causes recorded MIDI notes to be appended to existing
items, rather than placed in new items that replace the existing items.
The panic button sends a note-off event on every note to every plugin,
use this when you get a stuck note.

Click 'Menu->Show Tooltips' in the transport to disable these tooltips""")


avconv_error = _(
"""Please ensure that avconv(or ffmpeg) and lame are installed, can't
open mp3 converter dialog.
Check your normal sources for packages or visit:

http://lame.sourceforge.net
http://libav.org

Can't find {}""")

export_format = _(
"""File is exported to 32 bit .wav at the sample rate your audio
interface is running at.
You can convert the format using the Menu->Tools dialogs""")

pitchbend_dialog = _(
"""Pitchbend values are in semitones.

Use this dialog to add points with precision,or double-click on
the editor to add points.""")

piano_roll_editor = _(
"""Click+drag to draw notes
CTRL+click+drag to marquee select multiple items
SHIFT+click+drag to delete notes
CTRL+ALT+click+drag-up/down to adjust the velocity of selected notes
CTRL+SHIFT+click+drag-up/down to create a velocity curve for the selected notes
Press the Delete button on your keyboard to delete selected notes
To edit velocity, press the menu button and select
the Velocity->Dialog... action
Click and drag the note end to change the length of selected notes
To edit multiple items as one logical item, select multiple items in the region
editor and right-click + 'Edit Selected Items as Group'
The Quantize, Transpose and Velocity actions in the menu button open dialogs
to manipulate the selected notes (or all notes if none are selected)

Click 'Menu->Show Tooltips' in the transport to disable these tooltips""")


audio_items_viewer = _("""Drag .wav files from the file browser onto here.
"You can edit item properties with the 'Edit' tab to the left,
or by clicking and dragging the item handles.

Click 'Menu->Show Tooltips' in the transport to disable these tooltips""")

song_editor = _(
"""This is the song editor.  A song is a timeline consisting of regions,
click here to add a region, click and drag to move a region,
or 'right-click->Delete Region' to delete the selected regions.
Click on a region to edit it in the region editor below.

Click 'Menu->Show Tooltips' in the transport to disable these tooltips""")
