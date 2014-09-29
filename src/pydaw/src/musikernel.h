/*
 * File:   musikernel.h
 * Author: userbuntu
 *
 * Created on September 28, 2014, 6:28 PM
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
    int status __attribute__((aligned(16)));
    int solo;
    int mute;
    t_pydaw_seq_event * event_buffer;
    int period_event_index;
    t_pydaw_plugin * plugins[MAX_PLUGIN_TOTAL_COUNT];
    int track_num;
    //Only for busses, the count of plugins writing to the buffer
    int bus_count;
    /*This is reset to bus_count each cycle and the
     * bus track processed when count reaches 0*/
    int bus_counter __attribute__((aligned(16)));
    t_pkm_peak_meter * peak_meter;
    float ** buffers;
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
}t_musikernel;

void g_musikernel_get(float);
t_pytrack * g_pytrack_get(int, float);
inline void v_pydaw_zero_buffer(float**, int);
void v_pydaw_print_benchmark(char * a_message, clock_t a_start);

#ifdef	__cplusplus
}
#endif

t_musikernel * musikernel = NULL;
int ZERO = 0;

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
    musikernel->sample_rate = a_sr;
    musikernel->input_buffers_active = 0;

    musikernel->preview_wav_item = 0;
    musikernel->preview_audio_item =
            g_pydaw_audio_item_get(musikernel->sample_rate);
    musikernel->preview_start = 0.0f;
    musikernel->preview_amp_lin = 1.0f;
    musikernel->is_previewing = 0;
    musikernel->preview_max_sample_count = ((int)(a_sr)) * 30;

    int f_i = 0;
    while(f_i < PYDAW_AUDIO_INPUT_TRACK_COUNT)
    {
        musikernel->audio_inputs[f_i] = g_pyaudio_input_get(a_sr);
        musikernel->audio_inputs[f_i]->input_port[0] = f_i * 2;
        musikernel->audio_inputs[f_i]->input_port[1] = (f_i * 2) + 1;
        f_i++;
    }


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
    int f_i2 = 0;

    while(f_i2 < a_count)
    {
        a_buffers[0][f_i2] = 0.0f;
        a_buffers[1][f_i2] = 0.0f;
        f_i2++;
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

    pthread_spin_init(&f_result->lock, 0);

    lmalloc((void**)&f_result->buffers, (sizeof(float*) * f_result->channels));

    while(f_i < f_result->channels)
    {
        buffer_alloc((void**)&f_result->buffers[f_i],
            (sizeof(float) * FRAMES_PER_BUFFER));
        f_i++;
    }

    v_pydaw_zero_buffer(f_result->buffers, FRAMES_PER_BUFFER);

    f_result->mute = 0;
    f_result->solo = 0;
    f_result->event_buffer = (t_pydaw_seq_event*)malloc(
            sizeof(t_pydaw_seq_event) * PYDAW_MAX_EVENT_BUFFER_SIZE);
    f_result->bus_count = 0;
    f_result->bus_counter = 0;

    f_i = 0;

    while(f_i < PYDAW_MAX_EVENT_BUFFER_SIZE)
    {
        v_pydaw_ev_clear(&f_result->event_buffer[f_i]);
        f_i++;
    }

    f_i = 0;
    while(f_i < MAX_PLUGIN_TOTAL_COUNT)
    {
        f_result->plugins[f_i] = 0;
        f_i++;
    }

    f_i = 0;

    while(f_i < PYDAW_MIDI_NOTE_COUNT)
    {
        f_result->note_offs[f_i] = -1;
        f_i++;
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

#endif	/* MUSIKERNEL_H */

