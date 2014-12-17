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

#include "pydaw_files.h"
#include "../libmodsynth/lib/lmalloc.h"
#include "pydaw_plugin_wrapper.h"
#include "midi_device.h"
#include "pydaw_audio_inputs.h"

#define MAX_WORKER_THREADS 8

#define PYDAW_MAX_EVENT_BUFFER_SIZE 512

#define PYDAW_MIDI_NOTE_COUNT 128

#define MAX_PLUGIN_COUNT 10
#define MAX_ROUTING_COUNT 4
#define MAX_PLUGIN_TOTAL_COUNT (MAX_PLUGIN_COUNT + MAX_ROUTING_COUNT)

#define MAX_PLUGIN_POOL_COUNT 1000

int PYDAW_AUDIO_INPUT_TRACK_COUNT = 0;
#define PYDAW_VERSION "musikernel"

#define PYDAW_OSC_SEND_QUEUE_SIZE 256
#define PYDAW_OSC_MAX_MESSAGE_SIZE 65536

#define FRAMES_PER_BUFFER 4096

#define STATUS_NOT_PROCESSED 0
#define STATUS_PROCESSING 1
#define STATUS_PROCESSED 2

#define PYDAW_PLAYBACK_MODE_OFF 0
#define PYDAW_PLAYBACK_MODE_PLAY 1
#define PYDAW_PLAYBACK_MODE_REC 2

#define FADE_STATE_OFF 0
#define FADE_STATE_FADING 1
#define FADE_STATE_FADED 2
#define FADE_STATE_RETURNING 3

#define MK_CONFIGURE_KEY_UPDATE_PLUGIN_CONTROL "pc"
#define MK_CONFIGURE_KEY_CONFIGURE_PLUGIN "co"
#define MK_CONFIGURE_KEY_EXIT "exit"
#define MK_CONFIGURE_KEY_PITCH_ENV "penv"
#define MK_CONFIGURE_KEY_RATE_ENV "renv"
#define MK_CONFIGURE_KEY_PREVIEW_SAMPLE "preview"
#define MK_CONFIGURE_KEY_STOP_PREVIEW "spr"
#define MK_CONFIGURE_KEY_KILL_ENGINE "abort"
#define MK_CONFIGURE_KEY_MASTER_VOL "mvol"
#define MK_CONFIGURE_KEY_LOAD_CC_MAP "cm"
#define MK_CONFIGURE_KEY_MIDI_LEARN "ml"
#define MK_CONFIGURE_KEY_ADD_TO_WAV_POOL "wp"
#define MK_CONFIGURE_KEY_WAVPOOL_ITEM_RELOAD "wr"
#define MK_CONFIGURE_KEY_LOAD_AB_SET "abs"
#define MK_CONFIGURE_KEY_AUDIO_IN_VOL "aiv"

#define MK_HOST_EDMNEXT 0
#define MK_HOST_WAVENEXT 1

#define MK_HOST_COUNT 2

volatile int exiting = 0;
float MASTER_VOL __attribute__((aligned(16))) = 1.0f;

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    char * f_tmp1;
    char * f_tmp2;
    char * f_msg;
    char osc_queue_keys[PYDAW_OSC_SEND_QUEUE_SIZE][12];
    char * osc_queue_vals[PYDAW_OSC_SEND_QUEUE_SIZE];
}t_osc_send_data;

typedef struct
{
    int thread_num;
    int stack_size;
}t_pydaw_thread_args;

typedef struct
{
    /*This is reset to bus_count each cycle and the
     * bus track processed when count reaches 0*/
    volatile int bus_counter;
    char bus_counter_padding[CACHE_LINE_SIZE - sizeof(int)];
    volatile int status;
    char status_padding[CACHE_LINE_SIZE - sizeof(int)];
    int solo;
    int mute;
    int period_event_index;
    t_pydaw_plugin * plugins[MAX_PLUGIN_TOTAL_COUNT];
    int track_num;
    t_pkm_peak_meter * peak_meter;
    float ** buffers;
    float ** sc_buffers;
    int sc_buffers_dirty;
    int channels;
    pthread_spinlock_t lock;
    t_ramp_env fade_env;
    int fade_state;
    /*When a note_on event is fired,
     * a sample number of when to release it is stored here*/
    long note_offs[PYDAW_MIDI_NOTE_COUNT];
    int item_event_index;
    char * osc_cursor_message;
    int * extern_midi_count;
    t_midi_device * midi_device;
    t_pydaw_seq_event * extern_midi;
    t_pydaw_seq_event event_buffer[PYDAW_MAX_EVENT_BUFFER_SIZE];
}t_pytrack;

typedef struct
{
    void (*run)(int sample_count, float **output, float **a_input_buffers);
    void (*osc_send)(t_osc_send_data*);
}t_mk_host;

typedef struct
{
    float sample_rate;
    char padding[CACHE_LINE_SIZE - sizeof(float)];
}t_mk_thread_storage;

typedef struct
{
    t_mk_thread_storage thread_storage[MAX_WORKER_THREADS];
    t_mk_host * current_host;
    t_mk_host hosts[MK_HOST_COUNT];
    t_wav_pool * wav_pool;
    pthread_spinlock_t main_lock;

    //For broadcasting to the threads that it's time to process the tracks
    pthread_cond_t * track_cond;
    //For preventing the main thread from continuing until the workers finish
    pthread_mutex_t * track_block_mutexes;
    pthread_spinlock_t * thread_locks;
    pthread_t * worker_threads;
    int worker_thread_count;
    int * track_thread_quit_notifier;
    void * main_thread_args;

    int is_offline_rendering;
    //set from the audio device buffer size every time the main loop is called.
    int sample_count;
    t_wav_pool_item * preview_wav_item;
    t_pydaw_audio_item * preview_audio_item;
    float preview_start; //0.0f to 1.0f
    int is_previewing;  //Set this to self->ab_mode on playback
    float preview_amp_lin;
    int preview_max_sample_count;
    t_pyaudio_input * audio_inputs;
    pthread_mutex_t audio_inputs_mutex;
    pthread_t audio_recording_thread;
    int audio_recording_quit_notifier __attribute__((aligned(16)));
    int playback_mode;  //0 == Stop, 1 == Play, 2 == Rec
    lo_server_thread serverThread;
    lo_address uiTarget;
    char * osc_cursor_message;
    int osc_queue_index;
    char osc_queue_keys[PYDAW_OSC_SEND_QUEUE_SIZE][12];
    char osc_queue_vals[PYDAW_OSC_SEND_QUEUE_SIZE][PYDAW_OSC_MAX_MESSAGE_SIZE];
    pthread_t osc_queue_thread;
    //Threads must hold this to write OSC messages
    pthread_spinlock_t ui_spinlock;
    t_midi_device_list * midi_devices;
    int midi_learn;
    t_pydaw_plugin plugin_pool[MAX_PLUGIN_POOL_COUNT];
    char * project_folder;
    char * audio_folder;
    char * audio_tmp_folder;
    char * samples_folder;
    char * samplegraph_folder;
    char * wav_pool_file;
    char * plugins_folder;
}t_musikernel;

void g_musikernel_get(float, t_midi_device_list*);
t_pytrack * g_pytrack_get(int, float);
inline void v_pydaw_zero_buffer(float**, int);
double v_pydaw_print_benchmark(char * a_message,
        struct timespec a_start, struct timespec a_finish);
void * v_pydaw_audio_recording_thread(void* a_arg);
void v_queue_osc_message(char*, char*);
void v_pydaw_set_plugin_index(t_pytrack*, int, int, int, int, int);


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

void g_musikernel_get(float a_sr, t_midi_device_list * a_midi_devices)
{
    clalloc((void**)&musikernel, sizeof(t_musikernel));
    musikernel->wav_pool = g_wav_pool_get(a_sr);
    musikernel->midi_devices = a_midi_devices;
    musikernel->current_host = &musikernel->hosts[MK_HOST_EDMNEXT];
    musikernel->midi_learn = 0;
    musikernel->is_offline_rendering = 0;
    pthread_spin_init(&musikernel->main_lock, 0);
    musikernel->project_folder = (char*)malloc(sizeof(char) * 1024);
    musikernel->audio_folder = (char*)malloc(sizeof(char) * 1024);
    musikernel->audio_tmp_folder = (char*)malloc(sizeof(char) * 1024);
    musikernel->samples_folder = (char*)malloc(sizeof(char) * 1024);
    musikernel->wav_pool_file = (char*)malloc(sizeof(char) * 1024);
    musikernel->plugins_folder = (char*)malloc(sizeof(char) * 1024);

    musikernel->preview_wav_item = 0;
    musikernel->preview_audio_item = g_pydaw_audio_item_get(a_sr);
    musikernel->preview_start = 0.0f;
    musikernel->preview_amp_lin = 1.0f;
    musikernel->is_previewing = 0;
    musikernel->preview_max_sample_count = ((int)(a_sr)) * 30;
    musikernel->playback_mode = 0;

    int f_i;

    hpalloc((void**)&musikernel->audio_inputs,
        sizeof(t_pyaudio_input) * PYDAW_AUDIO_INPUT_TRACK_COUNT);

    for(f_i = 0; f_i < PYDAW_AUDIO_INPUT_TRACK_COUNT; ++f_i)
    {
        g_pyaudio_input_init(&musikernel->audio_inputs[f_i], a_sr, 1);
        musikernel->audio_inputs[f_i].input_port[0] = f_i * 2;
        musikernel->audio_inputs[f_i].input_port[1] = (f_i * 2) + 1;
    }

    for(f_i = 0; f_i < MAX_WORKER_THREADS; ++f_i)
    {
        musikernel->thread_storage[f_i].sample_rate = a_sr;
    }

    /* Create OSC thread */

    pthread_spin_init(&musikernel->ui_spinlock, 0);
    musikernel->osc_queue_index = 0;
    musikernel->osc_cursor_message = (char*)malloc(sizeof(char) * 1024);

    musikernel->serverThread = lo_server_thread_new(NULL, pydaw_osc_error);
    musikernel->uiTarget = lo_address_new_from_url(
        "osc.udp://localhost:30321/");

    for(f_i = 0; f_i < MAX_PLUGIN_POOL_COUNT; ++f_i)
    {
        musikernel->plugin_pool[f_i].active = 0;
    }
}

void v_pydaw_set_control_from_atm( t_pydaw_seq_event *event,
        int a_plugin_uid, t_pytrack * f_track)
{
    if(!musikernel->is_offline_rendering)
    {
        sprintf(
            f_track->osc_cursor_message, "%i|%i|%f",
            a_plugin_uid, event->port, event->value);
        v_queue_osc_message("pc", f_track->osc_cursor_message);
    }
}

void v_pydaw_set_control_from_cc(t_pydaw_seq_event *event, t_pytrack * f_track)
{
    if(!musikernel->is_offline_rendering)
    {
        sprintf(
            f_track->osc_cursor_message, "%i|%i|%i",
            f_track->track_num, event->param, (int)(event->value));
        v_queue_osc_message("cc", f_track->osc_cursor_message);
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

void v_pydaw_set_host(int a_mode)
{
    assert(a_mode >= 0 && a_mode < MK_HOST_COUNT);

    pthread_spin_lock(&musikernel->main_lock);

    musikernel->current_host = &musikernel->hosts[a_mode];

    pthread_spin_unlock(&musikernel->main_lock);
}

void v_pydaw_activate_osc_thread(lo_method_handler osc_message_handler)
{
    lo_server_thread_add_method(musikernel->serverThread, NULL, NULL,
            osc_message_handler, NULL);
    lo_server_thread_start(musikernel->serverThread);
}

/* Create a clock_t with clock() when beginning some work,
 * and use this function to print the completion time*/
inline double v_pydaw_print_benchmark(char * a_message,
    struct timespec f_start, struct timespec f_finish)
{
    double elapsed;
    elapsed = (f_finish.tv_sec - f_start.tv_sec);
    elapsed += (f_finish.tv_nsec - f_start.tv_nsec) / 1000000000.0;

    printf ( "\n\nCompleted %s in %lf seconds\n", a_message, elapsed);

    return elapsed;
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

void v_pydaw_open_track(t_pytrack * a_track, char * a_tracks_folder,
        int a_index)
{
    char f_file_name[1024];

    sprintf(f_file_name, "%s/%i", a_tracks_folder, a_index);

    if(i_pydaw_file_exists(f_file_name))
    {
        t_2d_char_array * f_2d_array = g_get_2d_array_from_file(f_file_name,
                PYDAW_LARGE_STRING);

        while(1)
        {
            v_iterate_2d_char_array(f_2d_array);

            if(f_2d_array->eof)
            {
                break;
            }

            if(f_2d_array->current_str[0] == 'p')  //plugin
            {
                v_iterate_2d_char_array(f_2d_array);
                int f_index = atoi(f_2d_array->current_str);
                v_iterate_2d_char_array(f_2d_array);
                int f_plugin_index = atoi(f_2d_array->current_str);
                v_iterate_2d_char_array(f_2d_array);
                int f_plugin_uid = atoi(f_2d_array->current_str);
                v_iterate_2d_char_array(f_2d_array); //mute
                v_iterate_2d_char_array(f_2d_array); //solo
                v_iterate_2d_char_array(f_2d_array);
                int f_power = atoi(f_2d_array->current_str);

                v_pydaw_set_plugin_index(a_track, f_index, f_plugin_index,
                    f_plugin_uid, f_power, 0);

            }
            else
            {
                printf("Invalid track identifier '%c'\n",
                    f_2d_array->current_str[0]);
                assert(0);
            }
        }

        g_free_2d_char_array(f_2d_array);
    }
}

t_pytrack * g_pytrack_get(int a_track_num, float a_sr)
{
    int f_i = 0;

    t_pytrack * f_result;
    clalloc((void**)&f_result, sizeof(t_pytrack));

    f_result->track_num = a_track_num;
    f_result->channels = 2;
    f_result->extern_midi = 0;
    f_result->extern_midi_count = &ZERO;
    f_result->midi_device = 0;
    f_result->sc_buffers_dirty = 0;

    pthread_spin_init(&f_result->lock, 0);

    hpalloc((void**)&f_result->buffers, (sizeof(float*) * f_result->channels));
    hpalloc((void**)&f_result->sc_buffers,
        (sizeof(float*) * f_result->channels));

    while(f_i < f_result->channels)
    {
        clalloc((void**)&f_result->buffers[f_i],
            (sizeof(float) * FRAMES_PER_BUFFER));
        clalloc((void**)&f_result->sc_buffers[f_i],
            (sizeof(float) * FRAMES_PER_BUFFER));
        ++f_i;
    }

    v_pydaw_zero_buffer(f_result->buffers, FRAMES_PER_BUFFER);
    v_pydaw_zero_buffer(f_result->sc_buffers, FRAMES_PER_BUFFER);

    f_result->mute = 0;
    f_result->solo = 0;

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

    g_rmp_init(&f_result->fade_env, a_sr);
    v_rmp_set_time(&f_result->fade_env, 0.03f);
    f_result->fade_state = 0;

    hpalloc((void**)&f_result->osc_cursor_message, sizeof(char) * 1024);

    f_result->status = STATUS_NOT_PROCESSED;

    return f_result;
}

void v_pydaw_set_preview_file(const char * a_file)
{
    t_wav_pool_item * f_result = g_wav_pool_item_get(0, a_file,
            musikernel->thread_storage[0].sample_rate);

    if(f_result)
    {
        if(i_wav_pool_item_load(f_result, 0))
        {
            t_wav_pool_item * f_old = musikernel->preview_wav_item;

            pthread_spin_lock(&musikernel->main_lock);

            musikernel->preview_wav_item = f_result;

            musikernel->preview_audio_item->ratio =
                    musikernel->preview_wav_item->ratio_orig;

            musikernel->is_previewing = 1;

            v_ifh_retrigger(
                &musikernel->preview_audio_item->sample_read_heads[0],
                PYDAW_AUDIO_ITEM_PADDING_DIV2);
            v_adsr_retrigger(&musikernel->preview_audio_item->adsrs[0]);

            pthread_spin_unlock(&musikernel->main_lock);

            if(f_old)
            {
                v_wav_pool_item_free(f_old);
            }
        }
        else
        {
            printf("i_wav_pool_item_load(f_result) failed in "
                    "v_pydaw_set_preview_file\n");
        }
    }
    else
    {
        musikernel->is_previewing = 0;
        printf("g_wav_pool_item_get returned zero. could not load "
                "preview item.\n");
    }
}

void * v_pydaw_audio_recording_thread(void* a_arg)
{
    char f_file_name[1024];

    t_pyaudio_input * f_ai;

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
                f_ai = &musikernel->audio_inputs[f_i];
                if((f_ai->rec) && (f_ai->flush_last_buffer_pending))
                {
                    f_flushed_buffer = 1;
                    printf("Flushing record buffer of %i frames\n",
                        ((f_ai->buffer_iterator[(f_ai->buffer_to_flush)]) / 2));

                    sf_writef_float(f_ai->sndfile,
                        f_ai->rec_buffers[f_ai->buffer_to_flush],
                        ((f_ai->buffer_iterator[f_ai->buffer_to_flush]) / 2));

                    f_ai->flush_last_buffer_pending = 0;
                    f_ai->buffer_iterator[f_ai->buffer_to_flush] = 0;
                }

                ++f_i;
            }
        }
        else
        {
            int f_i;

            for(f_i = 0; f_i < PYDAW_AUDIO_INPUT_TRACK_COUNT; ++f_i)
            {
                f_ai = &musikernel->audio_inputs[f_i];
                if(f_ai->recording_stopped)
                {
                    f_did_something = 1;
                    sf_writef_float(f_ai->sndfile,
                        f_ai->rec_buffers[(f_ai->current_buffer)],
                        ((f_ai->buffer_iterator[(f_ai->current_buffer)]) / 2));

                    sf_close(f_ai->sndfile);
                    f_ai->recording_stopped = 0;
                    f_ai->sndfile = 0;
                }
            }

            /*Re-create the sndfile if it no longer exists, that means the
             * UI has moved it from the tmp folder...*/

            for(f_i = 0; f_i < PYDAW_AUDIO_INPUT_TRACK_COUNT; ++f_i)
            {
                if(musikernel->audio_inputs[f_i].rec)
                {
                    f_did_something = 1;

                    sprintf(f_file_name, "%s%i.wav",
                        musikernel->audio_tmp_folder, f_i);

                    if(!i_pydaw_file_exists(f_file_name))
                    {
                        v_pydaw_audio_input_record_set(
                            &musikernel->audio_inputs[f_i], f_file_name);
                    }
                }
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


void v_pydaw_update_audio_inputs(char * a_project_folder)
{
    char f_inputs_file[2048];
    t_pyaudio_input * f_ai;
    sprintf(f_inputs_file, "%sdefault.pyinput", a_project_folder);

    if(a_project_folder && i_pydaw_file_exists(f_inputs_file))
    {
        int f_i;
        t_2d_char_array * f_2d_array = g_get_2d_array_from_file(
            f_inputs_file, PYDAW_LARGE_STRING);

        pthread_mutex_lock(&musikernel->audio_inputs_mutex);
        for(f_i = 0; f_i < PYDAW_AUDIO_INPUT_TRACK_COUNT; ++f_i)
        {
            v_iterate_2d_char_array(f_2d_array);

            if(f_2d_array->eof) //!strcmp(f_index_str, "\\"))
            {
                break;
            }

            int f_index = atoi(f_2d_array->current_str);

            v_iterate_2d_char_array(f_2d_array);
            int f_rec = atoi(f_2d_array->current_str);

            v_iterate_2d_char_array(f_2d_array);
            int f_vol = atoi(f_2d_array->current_str);

            v_iterate_2d_char_array(f_2d_array);
            int f_out = atoi(f_2d_array->current_str);

            v_iterate_2d_char_array(f_2d_array); //Not used

            f_ai = &musikernel->audio_inputs[f_index];
            f_ai->rec = f_rec;
            f_ai->output_track = f_out;

            f_ai->vol = f_vol;
            f_ai->vol_linear = f_db_to_linear_fast(f_vol);

            char f_tmp_file_name[2048];

            sprintf(f_tmp_file_name, "%s%i.wav",
                musikernel->audio_tmp_folder, f_index);

            v_pydaw_audio_input_record_set(f_ai, f_tmp_file_name);
        }
        pthread_mutex_unlock(&musikernel->audio_inputs_mutex);
        g_free_2d_char_array(f_2d_array);
    }
    else
    {
        printf("%s not found, setting default values\n", f_inputs_file);
        pthread_mutex_lock(&musikernel->audio_inputs_mutex);
        int f_i;
        for(f_i = 0; f_i < PYDAW_AUDIO_INPUT_TRACK_COUNT; ++f_i)
        {
            f_ai = &musikernel->audio_inputs[f_i];
            f_ai->rec = 0;
            f_ai->output_track = 0;

            f_ai->vol = 0.0f;
            f_ai->vol_linear = 1.0f;
        }
        pthread_mutex_unlock(&musikernel->audio_inputs_mutex);
    }
}

inline float f_bpm_to_seconds_per_beat(float a_tempo)
{
    return (60.0f / a_tempo);
}

inline float f_pydaw_samples_to_beat_count(int a_sample_count, float a_tempo,
        float a_sr)
{
    float f_seconds_per_beat = f_bpm_to_seconds_per_beat(a_tempo);
    float f_seconds = (float)(a_sample_count) / a_sr;
    return f_seconds / f_seconds_per_beat;
}

inline int i_beat_count_to_samples(float a_beat_count, float a_tempo,
        float a_sr)
{
    float f_seconds = f_bpm_to_seconds_per_beat(a_tempo) * a_beat_count;
    return (int)(f_seconds * a_sr);
}


inline void v_buffer_mix(int a_count,
    float ** __restrict__ a_buffer_src, float ** __restrict__ a_buffer_dest)
{
    register int f_i2 = 0;

    while(f_i2 < a_count)
    {
        a_buffer_dest[0][f_i2] += a_buffer_src[0][f_i2];
        a_buffer_dest[1][f_i2] += a_buffer_src[1][f_i2];
        ++f_i2;
    }
}

void v_wait_for_threads()
{
    int f_i;

    for(f_i = 1; f_i < (musikernel->worker_thread_count); ++f_i)
    {
        pthread_spin_lock(&musikernel->thread_locks[f_i]);
        pthread_spin_unlock(&musikernel->thread_locks[f_i]);
    }
}

void g_pynote_init(t_pydaw_seq_event * f_result, int a_note, int a_vel,
        float a_start, float a_length)
{
    f_result->type = PYDAW_EVENT_NOTEON;
    f_result->length = a_length;
    f_result->note = a_note;
    f_result->start = a_start;
    f_result->velocity = a_vel;
}

t_pydaw_seq_event * g_pynote_get(int a_note, int a_vel,
        float a_start, float a_length)
{
    t_pydaw_seq_event * f_result =
        (t_pydaw_seq_event*)malloc(sizeof(t_pydaw_seq_event));
    g_pynote_init(f_result, a_note, a_vel, a_start, a_length);
    return f_result;
}

void g_pycc_init(t_pydaw_seq_event * f_result, int a_cc_num,
    float a_cc_val, float a_start)
{
    f_result->type = PYDAW_EVENT_CONTROLLER;
    f_result->param = a_cc_num;
    f_result->value = a_cc_val;
    f_result->start = a_start;
}

t_pydaw_seq_event * g_pycc_get(int a_cc_num, float a_cc_val, float a_start)
{
    t_pydaw_seq_event * f_result =
        (t_pydaw_seq_event*)malloc(sizeof(t_pydaw_seq_event));
    g_pycc_init(f_result, a_cc_num, a_cc_val, a_start);
    return f_result;
}

void g_pypitchbend_init(t_pydaw_seq_event * f_result, float a_start,
    float a_value)
{
    f_result->type = PYDAW_EVENT_PITCHBEND;
    f_result->start = a_start;
    f_result->value = a_value;
}

t_pydaw_seq_event * g_pypitchbend_get(float a_start, float a_value)
{
    t_pydaw_seq_event * f_result =
        (t_pydaw_seq_event*)malloc(sizeof(t_pydaw_seq_event));
    g_pypitchbend_init(f_result, a_start, a_value);
    return f_result;
}


void v_mk_configure(const char* a_key, const char* a_value)
{
    printf("v_mk_configure:  key: \"%s\", value: \"%s\"\n", a_key, a_value);

    if(!strcmp(a_key, MK_CONFIGURE_KEY_UPDATE_PLUGIN_CONTROL))
    {
        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 3,
                PYDAW_TINY_STRING);

        int f_plugin_uid = atoi(f_val_arr->array[0]);

        int f_port = atoi(f_val_arr->array[1]);
        float f_value = atof(f_val_arr->array[2]);

        t_pydaw_plugin * f_instance;
        pthread_spin_lock(&musikernel->main_lock);

        f_instance = &musikernel->plugin_pool[f_plugin_uid];

        if(f_instance)
        {
            f_instance->descriptor->set_port_value(
                f_instance->PYFX_handle, f_port, f_value);
        }
        else
        {
            printf("Error, no valid plugin instance\n");
        }
        pthread_spin_unlock(&musikernel->main_lock);
        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_CONFIGURE_PLUGIN))
    {
        t_1d_char_array * f_val_arr = c_split_str_remainder(a_value, '|', 3,
                PYDAW_LARGE_STRING);
        int f_plugin_uid = atoi(f_val_arr->array[0]);
        char * f_key = f_val_arr->array[1];
        char * f_message = f_val_arr->array[2];

        t_pydaw_plugin * f_instance = &musikernel->plugin_pool[f_plugin_uid];

        if(f_instance)
        {
            f_instance->descriptor->configure(
                f_instance->PYFX_handle, f_key, f_message,
                &musikernel->main_lock);
        }
        else
        {
            printf("Error, no valid plugin instance\n");
        }

        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_MASTER_VOL))
    {
        MASTER_VOL = atof(a_value);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_AUDIO_IN_VOL))
    {
        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 2,
                PYDAW_SMALL_STRING);
        int f_index = atoi(f_val_arr->array[0]);
        float f_vol = atof(f_val_arr->array[1]);
        float f_vol_linear = f_db_to_linear_fast(f_vol);

        g_free_1d_char_array(f_val_arr);

        t_pyaudio_input * f_input = &musikernel->audio_inputs[f_index];

        f_input->vol = f_vol;
        f_input->vol_linear = f_vol_linear;
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_KILL_ENGINE))
    {
        pthread_spin_lock(&musikernel->main_lock);
        assert(0);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_EXIT))
    {
        exiting = 1;
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_LOAD_CC_MAP))
    {
        t_1d_char_array * f_val_arr = c_split_str_remainder(a_value, '|', 2,
                PYDAW_SMALL_STRING);
        int f_plugin_uid = atoi(f_val_arr->array[0]);
        musikernel->plugin_pool[f_plugin_uid].descriptor->set_cc_map(
            musikernel->plugin_pool[f_plugin_uid].PYFX_handle,
            f_val_arr->array[1]);
        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_MIDI_LEARN))
    {
        musikernel->midi_learn = 1;
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_ADD_TO_WAV_POOL))
    {
        t_key_value_pair * f_kvp = g_kvp_get(a_value);
        printf("v_wav_pool_add_item(musikernel->wav_pool, %i, \"%s\")\n",
                atoi(f_kvp->key), f_kvp->value);
        v_wav_pool_add_item(musikernel->wav_pool, atoi(f_kvp->key),
                f_kvp->value);
        free(f_kvp);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_PREVIEW_SAMPLE))
    {
        v_pydaw_set_preview_file(a_value);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_STOP_PREVIEW))
    {
        if(musikernel->is_previewing)
        {
            pthread_spin_lock(&musikernel->main_lock);
            v_adsr_release(&musikernel->preview_audio_item->adsrs[0]);
            pthread_spin_unlock(&musikernel->main_lock);
        }
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_RATE_ENV))
    {
        t_2d_char_array * f_arr = g_get_2d_array(PYDAW_SMALL_STRING);
        char f_tmp_char[PYDAW_SMALL_STRING];
        sprintf(f_tmp_char, "%s", a_value);
        f_arr->array = f_tmp_char;
        char * f_in_file = (char*)malloc(sizeof(char) * PYDAW_TINY_STRING);
        v_iterate_2d_char_array(f_arr);
        strcpy(f_in_file, f_arr->current_str);
        char * f_out_file = (char*)malloc(sizeof(char) * PYDAW_TINY_STRING);
        v_iterate_2d_char_array(f_arr);
        strcpy(f_out_file, f_arr->current_str);
        v_iterate_2d_char_array(f_arr);
        float f_start = atof(f_arr->current_str);
        v_iterate_2d_char_array(f_arr);
        float f_end = atof(f_arr->current_str);

        v_pydaw_rate_envelope(f_in_file, f_out_file, f_start, f_end);

        free(f_in_file);
        free(f_out_file);

        f_arr->array = 0;
        g_free_2d_char_array(f_arr);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_LOAD_AB_SET))
    {
        int f_mode = atoi(a_value);
        v_pydaw_set_host(f_mode);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_PITCH_ENV))
    {
        t_2d_char_array * f_arr = g_get_2d_array(PYDAW_SMALL_STRING);
        char f_tmp_char[PYDAW_SMALL_STRING];
        sprintf(f_tmp_char, "%s", a_value);
        f_arr->array = f_tmp_char;
        char * f_in_file = (char*)malloc(sizeof(char) * PYDAW_TINY_STRING);
        v_iterate_2d_char_array(f_arr);
        strcpy(f_in_file, f_arr->current_str);
        char * f_out_file = (char*)malloc(sizeof(char) * PYDAW_TINY_STRING);
        v_iterate_2d_char_array(f_arr);
        strcpy(f_out_file, f_arr->current_str);
        v_iterate_2d_char_array(f_arr);
        float f_start = atof(f_arr->current_str);
        v_iterate_2d_char_array(f_arr);
        float f_end = atof(f_arr->current_str);

        v_pydaw_pitch_envelope(f_in_file, f_out_file, f_start, f_end);

        free(f_in_file);
        free(f_out_file);

        f_arr->array = 0;
        g_free_2d_char_array(f_arr);
    }
    else if(!strcmp(a_key, MK_CONFIGURE_KEY_WAVPOOL_ITEM_RELOAD))
    {
        int f_uid = atoi(a_value);
        t_wav_pool_item * f_old =
                g_wav_pool_get_item_by_uid(musikernel->wav_pool, f_uid);
        t_wav_pool_item * f_new =
                g_wav_pool_item_get(f_uid, f_old->path,
                musikernel->wav_pool->sample_rate);

        float * f_old_samples[2];
        f_old_samples[0] = f_old->samples[0];
        f_old_samples[1] = f_old->samples[1];

        pthread_spin_lock(&musikernel->main_lock);

        f_old->channels = f_new->channels;
        f_old->length = f_new->length;
        f_old->ratio_orig = f_new->ratio_orig;
        f_old->sample_rate = f_new->sample_rate;
        f_old->samples[0] = f_new->samples[0];
        f_old->samples[1] = f_new->samples[1];

        pthread_spin_unlock(&musikernel->main_lock);

        if(f_old_samples[0])
        {
            free(f_old_samples[0]);
        }

        if(f_old_samples[1])
        {
            free(f_old_samples[1]);
        }

        free(f_new);
    }
    else
    {
        printf("Unknown configure message key: %s, value %s\n", a_key, a_value);
    }

}


/*Function for passing to plugins that re-use the wav pool*/
t_wav_pool_item * g_pydaw_wavpool_item_get(int a_uid)
{
    return g_wav_pool_get_item_by_uid(musikernel->wav_pool, a_uid);
}


/* Disable the optimizer for this function because it causes a
 * SEGFAULT on ARM (which could not be reproduced on x86)
 * This is not a performance-critical function. */
__attribute__((optimize("-O0"))) void v_pydaw_set_plugin_index(
        t_pytrack * f_track, int a_index, int a_plugin_index, int a_plugin_uid,
        int a_power, int a_lock)
{
    t_pydaw_plugin * f_plugin = NULL;

    if(a_plugin_index)
    {
        f_plugin = &musikernel->plugin_pool[a_plugin_uid];

        if(!f_plugin->active)
        {
            g_pydaw_plugin_init(
                f_plugin, (int)(musikernel->thread_storage[0].sample_rate),
                a_plugin_index, g_pydaw_wavpool_item_get,
                a_plugin_uid, v_queue_osc_message);

            int f_i = 0;
            while(f_i < f_track->channels)
            {
                f_plugin->descriptor->connect_buffer(
                    f_plugin->PYFX_handle, f_i, f_track->buffers[f_i], 0);
                f_plugin->descriptor->connect_buffer(
                    f_plugin->PYFX_handle, f_i, f_track->sc_buffers[f_i], 1);
                ++f_i;
            }
            char f_file_name[1024];
            sprintf(f_file_name, "%s%i",
                musikernel->plugins_folder, a_plugin_uid);

            if(i_pydaw_file_exists(f_file_name))
            {
                f_plugin->descriptor->load(f_plugin->PYFX_handle,
                    f_plugin->descriptor, f_file_name);
            }
        }
    }

    if(f_plugin)
    {
        f_plugin->power = a_power;
    }

    if(a_lock)
    {
        pthread_spin_lock(&musikernel->main_lock);
    }

    f_track->plugins[a_index] = f_plugin;

    if(a_lock)
    {
        pthread_spin_unlock(&musikernel->main_lock);
    }
}

#endif	/* MUSIKERNEL_H */

