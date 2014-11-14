/*
This file is part of the MusiKernel project, Copyright MusiKernel Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
*/

#ifndef MK_VOCODER_SYNTH_H
#define	MK_VOCODER_SYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../include/pydaw_plugin.h"
#include "libmodsynth.h"

#define MK_VOCODER_FIRST_CONTROL_PORT 0

#define MK_VOCODER_LAST_CONTROL_PORT 0
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define MK_VOCODER_COUNT 0

typedef struct
{
    float * buffers[2];
    float * sc_buffers[2];
    float fs;
    t_mk_vocoder_mono_modules * mono_modules;

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
} t_mk_vocoder;

#ifdef	__cplusplus
}
#endif

#endif	/* MK_VOCODER_SYNTH_H */

