/*
This file is part of the PyDAW project, Copyright PyDAW Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
*/

#ifndef SIMPLE_FADER_SYNTH_H
#define	SIMPLE_FADER_SYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../include/pydaw_plugin.h"
#include "libmodsynth.h"

#define SFADER_INPUT0  0
#define SFADER_INPUT1  1
#define SFADER_OUTPUT0  2
#define SFADER_OUTPUT1  3

#define SFADER_FIRST_CONTROL_PORT 4
#define SFADER_VOL_SLIDER 4

#define SFADER_LAST_CONTROL_PORT 4
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define SFADER_COUNT 5

typedef struct
{
    PYFX_Data *output0;
    PYFX_Data *output1;

    PYFX_Data *vol_slider;
    float fs;
    t_sfader_mono_modules * mono_modules;

    int i_mono_out;
    int i_buffer_clear;

    int midi_event_types[200];
    int midi_event_ticks[200];
    float midi_event_values[200];
    int midi_event_ports[200];
    int midi_event_count;
    t_plugin_event_queue atm_queue;
    int plugin_uid;
    fp_queue_message queue_func;

    float * port_table;
    t_plugin_cc_map cc_map;
    PYFX_Descriptor * descriptor;
} t_sfader;

#ifdef	__cplusplus
}
#endif

#endif	/* SIMPLE_FADER_SYNTH_H */

