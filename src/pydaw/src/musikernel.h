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

#ifndef MUSIKERNEL_H
#define	MUSIKERNEL_H

#include "../libmodsynth/lib/lmalloc.h"

#define PYDAW_MIDI_NOTE_COUNT 128
#define MAX_PLUGIN_COUNT 10

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    /*This is reset to bus_count each cycle and the
     * bus track processed when count reaches 0*/
    int bus_counter __attribute__((aligned(16)));
    int status __attribute__((aligned(16)));
    int solo;
    int mute;
    t_pydaw_seq_event * event_buffer;
    int period_event_index;
    t_pydaw_plugin * plugins[MAX_PLUGIN_TOTAL_COUNT];
    int track_num;
    t_pkm_peak_meter * peak_meter;
    float ** buffers;
    float ** sc_buffers;
    int sc_buffers_dirty;
    int channels;
    pthread_spinlock_t lock;
    t_ramp_env * fade_env;
    int fade_state;
    /*When a note_on event is fired,
     * a sample number of when to release it is stored here*/
    long note_offs[PYDAW_MIDI_NOTE_COUNT];
    int item_event_index;
    char * osc_cursor_message;
    int * extern_midi_count;
    t_pydaw_seq_event * extern_midi;
    t_midi_device * midi_device;
}t_pytrack;

typedef struct
{
    t_pydaw_plugin * plugin_pool[MAX_PLUGIN_POOL_COUNT];
    t_wav_pool * wav_pool;
    pthread_spinlock_t main_lock;
    int ab_mode;  //0 == off, 1 == on
    int is_ab_ing;  //Set this to self->ab_mode on playback
    int is_offline_rendering;
    float sample_rate;
    //set from the audio device buffer size every time the main loop is called.
    int sample_count;
    char * project_folder;
    char * audio_folder;
    char * audio_tmp_folder;
    char * samples_folder;
    char * samplegraph_folder;
    char * wav_pool_file;
    char * plugins_folder;
    float ** input_buffers;
    int input_buffers_active;
    t_wav_pool_item * preview_wav_item;
    t_pydaw_audio_item * preview_audio_item;
    float preview_start; //0.0f to 1.0f
    int is_previewing;  //Set this to self->ab_mode on playback
    float preview_amp_lin;
    int preview_max_sample_count;
    t_pyaudio_input * audio_inputs[PYDAW_AUDIO_INPUT_TRACK_COUNT];
    pthread_mutex_t audio_inputs_mutex;
    pthread_t audio_recording_thread;
    int audio_recording_quit_notifier __attribute__((aligned(16)));
    int playback_mode;  //0 == Stop, 1 == Play, 2 == Rec
    lo_server_thread serverThread;
    char * osc_url;
    lo_address uiTarget;
    char * osc_cursor_message;
    int osc_queue_index;
    char osc_queue_keys[PYDAW_OSC_SEND_QUEUE_SIZE][12];
    char osc_queue_vals[PYDAW_OSC_SEND_QUEUE_SIZE][PYDAW_OSC_MAX_MESSAGE_SIZE];
    pthread_t osc_queue_thread;
    //Threads must hold this to write OSC messages
    pthread_spinlock_t ui_spinlock;
}t_musikernel;

void g_musikernel_get(float);
t_pytrack * g_pytrack_get(int, float);
inline void v_pydaw_zero_buffer(float**, int);
void v_pydaw_print_benchmark(char * a_message, clock_t a_start);
void * v_pydaw_audio_recording_thread(void* a_arg);

#ifdef	__cplusplus
}
#endif

t_musikernel * musikernel = NULL;
int ZERO = 0;

void pydaw_osc_error(int num, const char *msg, const char *path)
{
    fprintf(stderr, "PyDAW: liblo server error %d in path %s: %s\n",
	    num, path, msg);
}

void g_musikernel_get(float a_sr)
{
    lmalloc((void**)&musikernel, sizeof(t_musikernel));
    musikernel->wav_pool = g_wav_pool_get(a_sr);
    musikernel->ab_mode = 0;
    musikernel->is_ab_ing = 0;
    musikernel->is_offline_rendering = 0;
    pthread_spin_init(&musikernel->main_lock, 0);
    musikernel->project_folder = (char*)malloc(sizeof(char) * 1024);
    musikernel->audio_folder = (char*)malloc(sizeof(char) * 1024);
    musikernel->audio_tmp_folder = (char*)malloc(sizeof(char) * 1024);
    musikernel->samples_folder = (char*)malloc(sizeof(char) * 1024);
    musikernel->wav_pool_file = (char*)malloc(sizeof(char) * 1024);
    musikernel->plugins_folder = (char*)malloc(sizeof(char) * 1024);
    musikernel->sample_rate = a_sr;
    musikernel->input_buffers_active = 0;

    musikernel->preview_wav_item = 0;
    musikernel->preview_audio_item =
            g_pydaw_audio_item_get(musikernel->sample_rate);
    musikernel->preview_start = 0.0f;
    musikernel->preview_amp_lin = 1.0f;
    musikernel->is_previewing = 0;
    musikernel->preview_max_sample_count = ((int)(a_sr)) * 30;
    musikernel->playback_mode = 0;

    int f_i = 0;
    while(f_i < PYDAW_AUDIO_INPUT_TRACK_COUNT)
    {
        musikernel->audio_inputs[f_i] = g_pyaudio_input_get(a_sr);
        musikernel->audio_inputs[f_i]->input_port[0] = f_i * 2;
        musikernel->audio_inputs[f_i]->input_port[1] = (f_i * 2) + 1;
        ++f_i;
    }

    /* Create OSC thread */

    pthread_spin_init(&musikernel->ui_spinlock, 0);
    musikernel->osc_queue_index = 0;
    musikernel->osc_cursor_message = (char*)malloc(sizeof(char) * 1024);

    char *tmp;

    char osc_path_tmp[1024];

    musikernel->serverThread = lo_server_thread_new(NULL, pydaw_osc_error);
    snprintf(osc_path_tmp, 31, "/dssi/pydaw_plugins");
    tmp = lo_server_thread_get_url(musikernel->serverThread);
    musikernel->osc_url = (char *)malloc(strlen(tmp) + strlen(osc_path_tmp));
    sprintf(musikernel->osc_url, "%s%s", tmp, osc_path_tmp + 1);
    free(tmp);

    musikernel->uiTarget = lo_address_new_from_url(
        "osc.udp://localhost:30321/");

    f_i = 0;
    while(f_i < MAX_PLUGIN_POOL_COUNT)
    {
        musikernel->plugin_pool[f_i] = 0;
        ++f_i;
    }
}

void v_queue_osc_message(
    char * __restrict__ a_key, char * __restrict__ a_val)
{
    if(musikernel->osc_queue_index >= PYDAW_OSC_SEND_QUEUE_SIZE)
    {
        printf("Dropping OSC event to prevent buffer overrun:\n%s|%s\n\n",
                a_key, a_val);
    }
    else
    {
        pthread_spin_lock(&musikernel->ui_spinlock);
        sprintf(musikernel->osc_queue_keys[musikernel->osc_queue_index],
                "%s", a_key);
        sprintf(musikernel->osc_queue_vals[musikernel->osc_queue_index],
                "%s", a_val);
        ++musikernel->osc_queue_index;
        pthread_spin_unlock(&musikernel->ui_spinlock);
    }
}

void v_pydaw_activate_osc_thread(lo_method_handler osc_message_handler)
{
    lo_server_thread_add_method(musikernel->serverThread, NULL, NULL,
            osc_message_handler, NULL);
    lo_server_thread_start(musikernel->serverThread);
}

/* Create a clock_t with clock() when beginning some work,
 * and use this function to print the completion time*/
inline void v_pydaw_print_benchmark(char * a_message, clock_t a_start)
{
    printf ( "\n\nCompleted %s in %f seconds\n", a_message,
            ( (double)clock() - a_start ) / CLOCKS_PER_SEC );
}

inline void v_pydaw_zero_buffer(float ** a_buffers, int a_count)
{
    register int f_i2 = 0;

    while(f_i2 < a_count)
    {
        a_buffers[0][f_i2] = 0.0f;
        a_buffers[1][f_i2] = 0.0f;
        ++f_i2;
    }
}

t_pytrack * g_pytrack_get(int a_track_num, float a_sr)
{
    int f_i = 0;

    t_pytrack * f_result;
    lmalloc((void**)&f_result, sizeof(t_pytrack));

    f_result->track_num = a_track_num;
    f_result->channels = 2;
    f_result->extern_midi = 0;
    f_result->extern_midi_count = &ZERO;
    f_result->midi_device = 0;
    f_result->sc_buffers_dirty = 0;

    pthread_spin_init(&f_result->lock, 0);

    lmalloc((void**)&f_result->buffers, (sizeof(float*) * f_result->channels));
    lmalloc((void**)&f_result->sc_buffers,
        (sizeof(float*) * f_result->channels));

    while(f_i < f_result->channels)
    {
        buffer_alloc((void**)&f_result->buffers[f_i],
            (sizeof(float) * FRAMES_PER_BUFFER));
        buffer_alloc((void**)&f_result->sc_buffers[f_i],
            (sizeof(float) * FRAMES_PER_BUFFER));
        ++f_i;
    }

    v_pydaw_zero_buffer(f_result->buffers, FRAMES_PER_BUFFER);
    v_pydaw_zero_buffer(f_result->sc_buffers, FRAMES_PER_BUFFER);

    f_result->mute = 0;
    f_result->solo = 0;
    f_result->event_buffer = (t_pydaw_seq_event*)malloc(
            sizeof(t_pydaw_seq_event) * PYDAW_MAX_EVENT_BUFFER_SIZE);
    f_result->bus_counter = 0;

    f_i = 0;

    while(f_i < PYDAW_MAX_EVENT_BUFFER_SIZE)
    {
        v_pydaw_ev_clear(&f_result->event_buffer[f_i]);
        ++f_i;
    }

    f_i = 0;
    while(f_i < MAX_PLUGIN_TOTAL_COUNT)
    {
        f_result->plugins[f_i] = 0;
        ++f_i;
    }

    f_i = 0;

    while(f_i < PYDAW_MIDI_NOTE_COUNT)
    {
        f_result->note_offs[f_i] = -1;
        ++f_i;
    }

    f_result->period_event_index = 0;

    f_result->peak_meter = g_pkm_get();

    f_result->fade_env = g_rmp_get_ramp_env(a_sr);
    v_rmp_set_time(f_result->fade_env, 0.03f);
    f_result->fade_state = 0;

    f_result->osc_cursor_message = (char*)malloc(sizeof(char) * 1024);

    f_result->status = STATUS_NOT_PROCESSED;

    return f_result;
}

void * v_pydaw_audio_recording_thread(void* a_arg)
{
    char f_file_name[1024];

    sleep(3);

    while(1)
    {
        int f_flushed_buffer = 0;
        int f_did_something = 0;

        if(musikernel->audio_recording_quit_notifier)
        {
            printf("audio recording thread exiting...\n");
            break;
        }

        pthread_mutex_lock(&musikernel->audio_inputs_mutex);

        if(musikernel->playback_mode == PYDAW_PLAYBACK_MODE_REC)
        {
            int f_i = 0;

            while(f_i < PYDAW_AUDIO_INPUT_TRACK_COUNT)
            {
                if((musikernel->audio_inputs[f_i]->rec) &&
                    (musikernel->audio_inputs[f_i]->
                        flush_last_buffer_pending))
                {
                    f_flushed_buffer = 1;
                    printf("Flushing record buffer of %i frames\n",
                            ((musikernel->audio_inputs[f_i]->
                            buffer_iterator[(musikernel->
                            audio_inputs[f_i]->buffer_to_flush)]) / 2));

                    sf_writef_float(musikernel->audio_inputs[f_i]->sndfile,
                            musikernel->audio_inputs[f_i]->
                            rec_buffers[(musikernel->
                            audio_inputs[f_i]->buffer_to_flush)],
                            ((musikernel->audio_inputs[f_i]->
                            buffer_iterator[(musikernel->audio_inputs[f_i]->
                            buffer_to_flush)]) / 2) );

                    musikernel->audio_inputs[f_i]->
                            flush_last_buffer_pending = 0;
                    musikernel->audio_inputs[f_i]->
                            buffer_iterator[(musikernel->audio_inputs[f_i]->
                            buffer_to_flush)] = 0;
                }

                ++f_i;
            }
        }
        else
        {
            int f_i = 0;

            while(f_i < PYDAW_AUDIO_INPUT_TRACK_COUNT)
            {
                /*I guess the main mutex keeps this concurrent, as the
                 * set_playback_mode has to grab it before setting the
                 * recording_stopped flag, which means we won't wind up with
                 * half-a-buffer, even if this
                 * thread uses lockless techniques while running
                 * fast-and-loose with the data...
                 * TODO:  verify that this is safe...*/
                if(musikernel->audio_inputs[f_i]->recording_stopped)
                {
                    f_did_something = 1;
                    sf_writef_float(musikernel->audio_inputs[f_i]->sndfile,
                            musikernel->audio_inputs[f_i]->rec_buffers[
                            (musikernel->audio_inputs[f_i]->current_buffer)],
                            ((musikernel->audio_inputs[f_i]->
                            buffer_iterator[(musikernel->audio_inputs[f_i]->
                            current_buffer)]) / 2) );

                    sf_close(musikernel->audio_inputs[f_i]->sndfile);
                    musikernel->audio_inputs[f_i]->recording_stopped = 0;
                    musikernel->audio_inputs[f_i]->sndfile = 0;
                }
                ++f_i;
            }

            /*Re-create the sndfile if it no longer exists, that means the
             * UI has moved it from the tmp folder...*/
            f_i = 0;

            while(f_i < PYDAW_AUDIO_INPUT_TRACK_COUNT)
            {
                if(musikernel->audio_inputs[f_i]->rec)
                {
                    f_did_something = 1;

                    sprintf(f_file_name, "%s%i.wav",
                            musikernel->audio_tmp_folder, f_i);

                    if(!i_pydaw_file_exists(f_file_name))
                    {
                        v_pydaw_audio_input_record_set(
                                musikernel->audio_inputs[f_i], f_file_name);
                    }
                }
                ++f_i;
            }

        }

        pthread_mutex_unlock(&musikernel->audio_inputs_mutex);

        if(!f_flushed_buffer || !f_did_something)
        {
            usleep(10000);
        }
    }

    return (void*)1;
}

#endif	/* MUSIKERNEL_H */

