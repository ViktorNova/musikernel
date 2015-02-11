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
the original items.""")

multiple_instances_warning = _(
"""Detected that there are instances of the MusiKernel
audio engine already running.
This could mean that you already have MusiKernel running, if so you
should click 'Cancel' and close the other instance.

This could also mean that for some reason the engine didn't properly
terminate from another session.  If so, click 'OK' to kill the
other process(es)""")

routing_graph = _(
"""This shows the routing per-track, this can also be configured from the
track panel of each individual track.
Click above the tracks to connect/disconnect a track to a destination track
behind it, and click below to connect a track to the track in front of it.
CTRL+click to connect/disconnect to the sidechain input of the track.

Creating feedback loops is not supported, you will receive an error
message if an attempted connection creates feedback.
"""
)

troubleshooting = _(
"""<h3>Drop-outs or Xruns:</h3>

<p>Xruns are usually caused by CPU power management throttling the CPU clock
frequency too aggressively, especially if you are using a laptop.  Other
causes are using an older or slower CPU in a CPU intensive project, or
possibly (but probably not) bad audio drivers.</p>

<p>Some PCs may just be able to force the CPU
governor to "Performance" mode, others may have to disable power management
features in the BIOS.  Many laptops don't expose the ability to turn off
these features in the BIOS.</p>

<p>Unfortunately, there is no one-size-fits-all
solution, as different generations of Intel and AMD processors use different
CPU frequency drivers and offer different power saving features and different
BIOS.</p>

<h3>My microphone doesn't work</h3>

<p>On some interfaces (such as the Apogee One), you may need to open the
terminal, type the command "alsamixer", and select your interface and
set the input.</p>

<h3>The UI is sluggish in a large project</h3>

<p>If using an Nvidia or AMD graphics card, you should probably try
installing the proprietary driver for you card.  In Ubuntu, with an
AMD card, for example: sudo apt-get install fglrx.</p>
"""
)

