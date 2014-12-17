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

#ifndef PYDAW_AUDIO_INPUTS_H
#define	PYDAW_AUDIO_INPUTS_H

#ifdef	__cplusplus
extern "C" {
#endif

#include <sndfile.h>
#include <pthread.h>
#include <stdio.h>
#include "pydaw_files.h"

//1 megabyte interleaved buffer per audio input
#define PYDAW_AUDIO_INPUT_REC_BUFFER_SIZE (1024 * 1024)

typedef struct
{
    int rec;
    int stereo_mode;  // 0 == stereo, 1 == mono
    int output_track;
    int input_port[2];
    float vol, vol_linear;
    SF_INFO sf_info;
    SNDFILE * sndfile;
    float rec_buffers[2][PYDAW_AUDIO_INPUT_REC_BUFFER_SIZE]
        __attribute__((aligned(16)));
    int buffer_iterator[2];
    int current_buffer;
    int flush_last_buffer_pending;
    int buffer_to_flush;
    int recording_stopped;
}t_pyaudio_input;

void g_pyaudio_input_init(t_pyaudio_input *, float, int);

void g_pyaudio_input_init(t_pyaudio_input * f_result, float a_sr, int a_ch)
{
    assert(a_ch >= 1 && a_ch <= 2);

    f_result->sf_info.channels = a_ch;
    f_result->sf_info.format = SF_FORMAT_WAV | SF_FORMAT_FLOAT;
    f_result->sf_info.samplerate = (int)(a_sr);

    f_result->sndfile = 0;

    f_result->rec = 0;
    f_result->current_buffer = 0;
    f_result->buffer_to_flush = 0;
    f_result->flush_last_buffer_pending = 0;
    f_result->output_track = 0;
    f_result->vol = 0.0f;
    f_result->vol_linear = 1.0f;
    f_result->recording_stopped = 0;
}

void v_pydaw_audio_input_record_set(
        t_pyaudio_input * a_audio_input, char * a_file_out)
{
    if(a_audio_input->sndfile)
    {
        sf_close(a_audio_input->sndfile);
        a_audio_input->sndfile = NULL;
    }

    if(i_pydaw_file_exists(a_file_out))
    {
        remove(a_file_out);
    }

    if(a_audio_input->rec)
    {
        a_audio_input->sndfile = sf_open(
            a_file_out, SFM_WRITE, &a_audio_input->sf_info);
    }
}


#ifdef	__cplusplus
}
#endif

#endif	/* PYDAW_AUDIO_INPUTS_H */

