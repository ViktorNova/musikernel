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

#ifndef SCC_SYNTH_H
#define	SCC_SYNTH_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../include/pydaw_plugin.h"
#include "libmodsynth.h"

#define SCC_FIRST_CONTROL_PORT 0

#define SCC_THRESHOLD 0
#define SCC_RATIO 1
#define SCC_SPEED 2
#define SCC_WET 3

#define SCC_LAST_CONTROL_PORT 3
/* must be 1 + highest value above
 * CHANGE THIS IF YOU ADD OR TAKE AWAY ANYTHING*/
#define SCC_COUNT 4

typedef struct
{
    PYFX_Data *output0;
    PYFX_Data *output1;

    PYFX_Data *sc_input0;
    PYFX_Data *sc_input1;

    PYFX_Data *threshold;
    PYFX_Data *ratio;
    PYFX_Data *speed;
    PYFX_Data *wet;

    float fs;
    t_scc_mono_modules * mono_modules;

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
} t_scc;

#ifdef	__cplusplus
}
#endif

#endif	/* SCC_SYNTH_H */

