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

//Required for sched.h
#ifndef __USE_GNU
#define __USE_GNU
#endif

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <stdio.h>
#include <stdlib.h>

#include "../pydaw/src/pydaw.h"
#include "../pydaw/include/pydaw_plugin.h"
#include "../pydaw/libmodsynth/lib/lmalloc.h"
#include <unistd.h>


void print_help()
{
    printf("Usage:  %s_render [project_dir] [output_file] [start_region] "
            "[start_bar] [end_region] [end_bar] [sample_rate] "
            "[buffer_size] [thread_count]\n\n", PYDAW_VERSION);
}

int main(int argc, char** argv)
{
    if(argc != 10)
    {
        print_help();
        exit(100);
    }

    char * f_project_dir = argv[1];
    char * f_output_file = argv[2];
    int f_start_region = atoi(argv[3]);
    int f_start_bar = atoi(argv[4]);
    int f_end_region = atoi(argv[5]);
    int f_end_bar = atoi(argv[6]);
    int f_sample_rate = atoi(argv[7]);
    int f_buffer_size = atoi(argv[8]);
    int f_thread_count = atoi(argv[9]);

    g_musikernel_get(f_sample_rate);
    g_pydaw_instantiate(0);
    g_wavenext_get();

    float** f_output;
    lmalloc((void**)&f_output, sizeof(float*) * 2);

    v_pydaw_activate(f_thread_count, 0, f_project_dir);

    int f_i = 0;
    while(f_i < 2)
    {
        buffer_alloc((void**)&f_output[f_i], sizeof(float) * f_buffer_size);
        f_i++;
    }

    f_i = 0;
    while(f_i < f_buffer_size)
    {
        f_output[0][f_i] = 0.0f;
        f_output[1][f_i] = 0.0f;
        f_i++;
    }

    musikernel->sample_count = f_buffer_size;
    v_pydaw_offline_render_prep(pydaw_data);

    /*
    v_pydaw_set_midi_device(pydaw_data, 1, 0, 5);
    v_set_playback_mode(pydaw_data, 1, 0, 0, 0);

    t_pydaw_seq_event f_events[2];
    v_pydaw_ev_set_noteon(&f_events[0], 0, 60, 100);
    f_events[0].tick = 2;
    v_pydaw_ev_set_noteoff(&f_events[1], 0, 60, 100);
    f_events[1].tick = 200;

    f_i = 0;
    while(f_i < 20)
    {
        v_pydaw_run_main_loop(
            pydaw_data, 512, f_events, 2, 512 * (f_i + 1),
            f_engine->output0, f_engine->output1, 0);
    }
    */

    v_pydaw_offline_render(pydaw_data, f_start_region, f_start_bar,
            f_end_region, f_end_bar, f_output_file, 0);

    /*
    printf("\nRunning benchmark of interleaved vs. non-interleaved buffers\n");

    float ** f_non_interleaved;

    buffer_alloc((void**)&f_non_interleaved, sizeof(float*) * 2);
    buffer_alloc((void**)&f_non_interleaved[0], sizeof(float) * f_buffer_size);
    buffer_alloc((void**)&f_non_interleaved[1], sizeof(float) * f_buffer_size);

    for(f_i = 0; f_i < f_buffer_size; ++f_i)
    {
        f_non_interleaved[0][f_i] = 1.0f;
        f_non_interleaved[1][f_i] = 1.0f;
    }

    float * f_interleaved;
    buffer_alloc((void**)&f_interleaved, sizeof(float) * f_buffer_size * 2);

    int ITERATIONS = 10000000;
    float f_mult = 0.99999999f;

    for(f_i = 0; f_i < f_buffer_size * 2; ++f_i)
    {
        f_interleaved[f_i] = 1.0f;
    }

    register int f_i2;

    clock_t f_start_interleaved = clock();

    for(f_i = 0; f_i < ITERATIONS; ++f_i)
    {
        for(f_i2 = 0; f_i2 < f_buffer_size * 2; ++f_i2)
        {
            f_interleaved[f_i2] *= f_mult;
        }
    }

    v_pydaw_print_benchmark("Interleaved: ", f_start_interleaved);

    clock_t f_start_non_interleaved = clock();

    for(f_i = 0; f_i < ITERATIONS; ++f_i)
    {
        for(f_i2 = 0; f_i2 < f_buffer_size; ++f_i2)
        {
            f_non_interleaved[0][f_i2] *= f_mult;
            f_non_interleaved[1][f_i2] *= f_mult;
        }
    }

    v_pydaw_print_benchmark("Non-interleaved: ", f_start_non_interleaved);
    */

    return 0;
}
