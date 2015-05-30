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

song_editor = _(
"""Click 'Menu->Show Tooltips' in the transport to disable these tooltips

This is the song editor.  A song is a timeline consisting of regions,
click here to add a region, click and drag to move a region,
or 'right-click->Delete Region' to delete the selected regions.
Click on a region to edit it in the region editor below.
""")

region_list_editor = _(
"""Click 'Menu->Show Tooltips' in the transport to disable these tooltips

This is a region editor, it consists of items, tracks and automation.

Tracks:

A track can be any/all of: instrument, audio, bus or send.
An item is one bar of MIDI notes and/or pitch-bend.

Items:

Click an empty cell to add a new item.

Select multiple items or automation points using CTRL+click+drag
(automation points only allow selecting from one track at a time)

Double click an item to open it in the piano-roll-editor or select
 multiple and right-click->'Edit Selected Items'

The term 'unlink' means to create a new copy of the item that does not
change it's parent item when edited. (by default all items are
'ghost items' that update all items with the same name)

See the right-click context menu for additional actions and keyboard shortcuts.

Automation:

An automation point moves a control on a plugin.  The automation points are
steppy, you must smooth the points to get a continuous line by selecting
points using CTRL+drag and pressing ALT+s.

Shift+click+drag to delete items or automation points with the mouse

See the right-click context menu for additional actions and keyboard shortcuts.
""")

transport = _(
"""Click 'Menu->Show Tooltips' in the transport to disable these tooltips

The MIDI controller used for each track can be configured in the dropdown
The 'Loop Mode' combobox can be used to loop a region.
The 'Follow' checkbox causes the UI to follow the project's playback position
The 'Overdub' checkbox causes recorded MIDI notes to be appended to existing
items, rather than placed in new items that replace the existing items.
""")

