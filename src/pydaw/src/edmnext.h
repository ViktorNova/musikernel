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


#ifndef EDMNEXT_H
#define	EDMNEXT_H

#define EN_CONFIGURE_KEY_SS "ss"
#define EN_CONFIGURE_KEY_OS "os"
#define EN_CONFIGURE_KEY_SI "si"
#define EN_CONFIGURE_KEY_SR "sr"
#define EN_CONFIGURE_KEY_SAVE_ATM "sa"
#define EN_CONFIGURE_KEY_EN_PLAYBACK "enp"
#define EN_CONFIGURE_KEY_LOOP "loop"
#define EN_CONFIGURE_KEY_TEMPO "tempo"
#define EN_CONFIGURE_KEY_SOLO "solo"
#define EN_CONFIGURE_KEY_MUTE "mute"
#define EN_CONFIGURE_KEY_AUDIO_ITEM_LOAD_ALL "ai"
#define EN_CONFIGURE_KEY_SET_OVERDUB_MODE "od"
#define EN_CONFIGURE_KEY_PANIC "panic"
//Update a single control for a per-audio-item-fx
#define EN_CONFIGURE_KEY_PER_AUDIO_ITEM_FX "paif"
//Reload entire region for per-audio-item-fx
#define EN_CONFIGURE_KEY_PER_AUDIO_ITEM_FX_REGION "par"
#define EN_CONFIGURE_KEY_GLUE_AUDIO_ITEMS "ga"
#define EN_CONFIGURE_KEY_MIDI_DEVICE "md"
#define EN_CONFIGURE_KEY_SET_POS "pos"
#define EN_CONFIGURE_KEY_PLUGIN_INDEX "pi"
#define EN_CONFIGURE_KEY_UPDATE_SEND "ts"

#define EN_LOOP_MODE_OFF 0
#define EN_LOOP_MODE_REGION 1

#define EN_MAX_ITEM_COUNT 5000
#define EN_MAX_REGION_COUNT 300
#define EN_MAX_EVENTS_PER_ITEM_COUNT 1024

#define EN_TRACK_COUNT 32

#define EN_MAX_REGION_SIZE 64


#include <string.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "pydaw_files.h"
#include "pydaw_plugin_wrapper.h"
#include <sys/stat.h>
#include <sched.h>
#include <unistd.h>
#include <time.h>
#include "../libmodsynth/lib/amp.h"
#include "../libmodsynth/lib/lmalloc.h"
#include "../libmodsynth/lib/peak_meter.h"
#include "../libmodsynth/modules/multifx/multifx3knob.h"
#include "../libmodsynth/modules/modulation/ramp_env.h"
#include "pydaw_audio_tracks.h"
#include "pydaw_audio_inputs.h"
#include "pydaw_audio_util.h"
#include <lo/lo.h>
#include "musikernel.h"


#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    t_pydaw_midi_routing routes[EN_TRACK_COUNT];
}t_en_midi_routing_list;

typedef struct
{
    t_pydaw_seq_event events[EN_MAX_EVENTS_PER_ITEM_COUNT];
    int event_count;
    int uid;
}t_en_item;

typedef struct
{
    //Refers to the index of items in the master item pool
    int item_indexes[EN_TRACK_COUNT][EN_MAX_REGION_SIZE];
    int uid;
    /*This flag is set to 1 if created during recording, signifying
     * that it requires a default name to be created for it*/
    int not_yet_saved;
    int region_length_bars;    //0 to use pydaw_data default
    int region_length_beats;    //0 to use pydaw_data default
    int bar_length;  //0 to use pydaw_data default
    int alternate_tempo;  //0 or 1, used as a boolean
    float tempo;
}t_en_region;

typedef struct
{
    int bar;
    float beat;
    int port;
    float val;
    int index;
    int plugin;
}t_en_atm_point;

typedef struct
{
    t_en_atm_point * points;
    int point_count;
    char padding[CACHE_LINE_SIZE - sizeof(int) - sizeof(void*)];
}t_en_atm_plugin;

typedef struct
{
    t_en_atm_plugin plugins[MAX_PLUGIN_POOL_COUNT];
}t_en_atm_region;

typedef struct
{
    int loaded[PYDAW_MAX_AUDIO_ITEM_COUNT];
    t_per_audio_item_fx * items[PYDAW_MAX_AUDIO_ITEM_COUNT][8];
}t_en_per_audio_item_fx_region;

typedef struct
{
    t_en_region * regions[EN_MAX_REGION_COUNT];
    t_pydaw_audio_items * audio_items[EN_MAX_REGION_COUNT];
    t_en_atm_region * regions_atm[EN_MAX_REGION_COUNT];
    t_en_per_audio_item_fx_region
            *per_audio_item_fx[EN_MAX_REGION_COUNT];
    int default_bar_length;
}t_en_song;

typedef struct
{
    int track_pool_sorted[MAX_WORKER_THREADS][EN_TRACK_COUNT]
        __attribute__((aligned(CACHE_LINE_SIZE)));
    t_pytrack_routing routes[EN_TRACK_COUNT][MAX_ROUTING_COUNT]
        __attribute__((aligned(CACHE_LINE_SIZE)));
    int bus_count[EN_TRACK_COUNT];
    int track_pool_sorted_count;
}t_en_routing_graph;

typedef struct
{
    //Main-loop variables, prefixed with ml_
    float ml_sample_period_inc;
    float ml_sample_period_inc_beats;
    float ml_next_playback_cursor;
    float ml_current_period_beats;
    float ml_next_period_beats;
    //New additions, to eventually replace some of the older variables
    int ml_current_region;
    int ml_current_bar;
    float ml_current_beat;
    int ml_next_region;
    int ml_next_bar;
    float ml_next_beat;
    //1 if a new bar starts in this sample period, 0 otherwise
    int ml_starting_new_bar;
    /*0 if false, or 1 if the next bar loops.  Consumers of
     * this value should check for the ->loop_mode variable..*/
    int ml_is_looping;
    char padding[CACHE_LINE_SIZE - (7 * sizeof(float)) - (6 * sizeof(int))];
}t_en_thread_storage;

typedef struct
{
    t_en_thread_storage ts[MAX_WORKER_THREADS];
    float tempo;
    t_en_song * en_song;
    t_pytrack * track_pool[EN_TRACK_COUNT];
    t_en_routing_graph * routing_graph;
    int loop_mode;  //0 == Off, 1 == Bar, 2 == Region
    int overdub_mode;  //0 == Off, 1 == On

    //only refers to the fractional position within the current bar.
    float playback_cursor;
    /*the increment per-period to iterate through 1 bar,
     * as determined by sample rate and tempo*/
    float playback_inc;
    int current_region; //the current region
    int current_bar; //the current bar(0 to 7), within the current region
    //int samples_per_bar;
    /*The sample number of the exact point in the song,
     * 0 == bar0/region0, 44100 == 1 second in at 44.1khz.*/
    long current_sample;
    //The number of samples per beat, for calculating length
    float samples_per_beat;

    t_en_item * item_pool[EN_MAX_ITEM_COUNT];

    int is_soloed;

    int default_region_length_bars;
    int default_region_length_beats;
    int default_bar_length;

    /*used to prevent new audio items from playing while
     * the existing are being faded out.*/
    int suppress_new_audio_items;

    int audio_glue_indexes[PYDAW_MAX_AUDIO_ITEM_COUNT];
    int f_region_length_bars;
    long f_next_current_sample;
    t_en_midi_routing_list midi_routing;

    char * item_folder;
    char * region_folder;
    char * region_audio_folder;
    char * region_atm_folder;
    char * tracks_folder;
    char * per_audio_item_fx_folder;
}t_edmnext;


void g_en_song_get(t_edmnext*, int);
t_pytrack_routing * g_pytrack_routing_get();
t_en_routing_graph * g_en_routing_graph_get(t_edmnext *);
void v_en_routing_graph_free(t_en_routing_graph*);
void v_pytrack_routing_set(t_pytrack_routing *, int, int);
void v_pytrack_routing_free(t_pytrack_routing *);
t_en_region * g_en_region_get(t_edmnext*, const int);
t_en_atm_region * g_en_atm_region_get(t_edmnext*, int);
void v_en_atm_region_free(t_en_atm_region*);
void g_en_item_get(t_edmnext*, int);

t_edmnext * g_edmnext_get();
int i_en_get_region_index_from_name(t_edmnext *, int);
void v_en_set_tempo(t_edmnext*,float);
void v_en_set_is_soloed(t_edmnext * self);
void v_en_set_loop_mode(t_edmnext * self, int a_mode);
void v_en_set_playback_cursor(t_edmnext * self, int a_region,
                           int a_bar);
int i_en_song_index_from_region_uid(t_edmnext*, int);
void v_en_update_track_send(t_edmnext * self, int a_lock);
void v_en_process_external_midi(t_edmnext * pydaw_data,
        t_pytrack * a_track, int sample_count, int a_thread_num,
        t_en_thread_storage * a_ts);
void v_en_offline_render(t_edmnext * self, int a_start_region,
        int a_start_bar, int a_end_region, int a_end_bar, char * a_file_out,
        int a_is_audio_glue, int a_create_file);
void v_en_audio_items_run(
    t_edmnext*, int, float**, float**, int, int, int*, t_en_thread_storage*);
inline float f_en_count_beats(t_edmnext * self,
        int a_start_region, int a_start_bar, float a_start_beat,
        int a_end_region, int a_end_bar, float a_end_beat);
t_pydaw_audio_items * v_en_audio_items_load_all(t_edmnext * self,
        int a_region_uid);

t_en_per_audio_item_fx_region * g_en_paif_region_get();
void v_en_paif_region_free(t_en_per_audio_item_fx_region*);
t_en_per_audio_item_fx_region * g_en_paif_region_open(t_edmnext*, int);

void v_en_paif_set_control(t_edmnext *, int, int, int, float);

void v_en_song_free(t_en_song *);
void v_en_process_note_offs(t_edmnext * self, int f_i);
void v_en_process_midi(t_edmnext * self,
        int f_i, int sample_count, int a_playback_mode,
        t_en_thread_storage * a_ts);
void v_en_zero_all_buffers(t_edmnext * self);
void v_en_panic(t_edmnext * self);

void v_en_process_atm(t_edmnext * self, int f_track_num,
    int f_index, int sample_count, int a_playback_mode,
    t_en_thread_storage * a_ts);

void v_en_set_midi_device(int, int, int);
void v_en_set_midi_devices();

void g_en_midi_routing_list_init(t_en_midi_routing_list*);

#ifdef	__cplusplus
}
#endif

t_edmnext * edmnext;

void g_en_midi_routing_list_init(t_en_midi_routing_list * self)
{
    int f_i;

    for(f_i = 0; f_i < EN_TRACK_COUNT; ++f_i)
    {
        self->routes[f_i].on = 0;
        self->routes[f_i].output_track = -1;
    }
}

void g_en_instantiate()
{
    edmnext = g_edmnext_get();
}

void v_en_reset_audio_item_read_heads(t_edmnext * self,
        int a_region, int a_start_bar)
{
    if(a_start_bar == 0)
    {
        return;  //no need to run because the audio loop will reset it all
    }

    if(!self->en_song->audio_items[a_region])
    {
        return;
    }

    t_pydaw_audio_items * f_audio_items = self->en_song->audio_items[a_region];

    register int f_i;
    int f_i2;
    float f_start_beats = (float)(a_start_bar * 4);
    float f_sr = musikernel->thread_storage[0].sample_rate;
    t_pydaw_audio_item * f_audio_item;
    float f_tempo = self->tempo;

    for(f_i = 0; f_i < PYDAW_MAX_AUDIO_ITEM_COUNT; ++f_i)
    {
        if(f_audio_items->items[f_i])
        {
            f_audio_item = f_audio_items->items[f_i];
            float f_start_beat =
                (float)(f_audio_item->start_bar * 4) +
                f_audio_item->start_beat;

            float f_end_beat =
                f_start_beat + f_pydaw_samples_to_beat_count(
                    (f_audio_item->sample_end_offset -
                     f_audio_item->sample_start_offset),
                    f_tempo, f_sr);

            if((f_start_beats > f_start_beat) && (f_start_beats < f_end_beat))
            {
                float f_beats_offset = (f_start_beats - f_start_beat);
                int f_sample_start = i_beat_count_to_samples(
                        f_beats_offset, f_tempo, f_sr);

                for(f_i2 = 0; f_i2 < MK_AUDIO_ITEM_SEND_COUNT; ++f_i2)
                {
                    v_ifh_retrigger(
                        &f_audio_item->sample_read_heads[f_i2], f_sample_start);

                    v_adsr_retrigger(&f_audio_item->adsrs[f_i2]);
                }
            }
        }
    }
}

/* void v_en_zero_all_buffers(t_pydaw_data * self)
 */
void v_en_zero_all_buffers(t_edmnext * self)
{
    int f_i = 0;
    float ** f_buff;
    while(f_i < EN_TRACK_COUNT)
    {
        f_buff = self->track_pool[f_i]->buffers;
        v_pydaw_zero_buffer(f_buff, FRAMES_PER_BUFFER);
        ++f_i;
    }
}

/* void v_en_panic(t_pydaw_data * self)
 *
 */
void v_en_panic(t_edmnext * self)
{
    register int f_i = 0;
    register int f_i2 = 0;
    t_pytrack * f_track;
    t_pydaw_plugin * f_plugin;

    while(f_i < EN_TRACK_COUNT)
    {
        f_track = self->track_pool[f_i];

        f_i2 = 0;
        while(f_i2 < MAX_PLUGIN_TOTAL_COUNT)
        {
            f_plugin = f_track->plugins[f_i2];
            if(f_plugin && f_plugin->descriptor->panic)
            {
                f_plugin->descriptor->panic(f_plugin->PYFX_handle);
            }
            ++f_i2;
        }

        ++f_i;
    }

    v_en_zero_all_buffers(self);
}


void v_en_song_free(t_en_song * a_en_song)
{
    int f_i = 0;
    while(f_i < EN_MAX_REGION_COUNT)
    {
        if(a_en_song->audio_items[f_i])
        {
            v_pydaw_audio_items_free(a_en_song->audio_items[f_i]);
        }

        if(a_en_song->per_audio_item_fx[f_i])
        {
            v_en_paif_region_free(a_en_song->per_audio_item_fx[f_i]);
        }

        if(a_en_song->regions[f_i])
        {
            free(a_en_song->regions[f_i]);
        }

        ++f_i;
    }
}

t_en_per_audio_item_fx_region * g_en_paif_region_get()
{
    t_en_per_audio_item_fx_region * f_result =
            (t_en_per_audio_item_fx_region*)malloc(
            sizeof(t_en_per_audio_item_fx_region));

    int f_i = 0;

    while(f_i < PYDAW_MAX_AUDIO_ITEM_COUNT)
    {
        f_result->loaded[f_i] = 0;
        int f_i2 = 0;
        while(f_i2 < 8)
        {
            f_result->items[f_i][f_i2] = 0;
            ++f_i2;
        }
        ++f_i;
    }

    return f_result;
}

void v_en_paif_region_free(t_en_per_audio_item_fx_region * a_paif)
{
    int f_i = 0;
    while(f_i < PYDAW_MAX_AUDIO_ITEM_COUNT)
    {
        int f_i2 = 0;
        while(f_i2 < 8)
        {
            if(a_paif->items[f_i][f_i2])
            {
                v_mf3_free(a_paif->items[f_i][f_i2]->mf3);
                free(a_paif->items[f_i][f_i2]);
                a_paif->items[f_i][f_i2] = 0;
            }
            ++f_i2;
        }
        ++f_i;
    }
    free(a_paif);
}


t_en_per_audio_item_fx_region * g_en_paif_region_open(
        t_edmnext * self, int a_region_uid)
{
    t_en_per_audio_item_fx_region * f_result = g_en_paif_region_get();

    int f_i = 0;
    char f_temp[1024];
    sprintf(f_temp, "%s%i", self->per_audio_item_fx_folder, a_region_uid);

    float f_sr = musikernel->thread_storage[0].sample_rate;

    if(i_pydaw_file_exists(f_temp))
    {
        t_2d_char_array * f_current_string =
                g_get_2d_array_from_file(f_temp, PYDAW_LARGE_STRING);
        while(f_i < PYDAW_MAX_AUDIO_ITEM_COUNT)
        {
            v_iterate_2d_char_array(f_current_string);
            if(f_current_string->eof)
            {
                break;
            }
            int f_index = atoi(f_current_string->current_str);

            f_result->loaded[f_index] = 1;

            int f_i2 = 0;

            while(f_i2 < 8)
            {
                f_result->items[f_index][f_i2] = g_paif_get(f_sr);
                int f_i3 = 0;
                while(f_i3 < 3)
                {
                    v_iterate_2d_char_array(f_current_string);
                    float f_knob_val = atof(f_current_string->current_str);
                    f_result->items[f_index][f_i2]->a_knobs[f_i3] = f_knob_val;
                    ++f_i3;
                }
                v_iterate_2d_char_array(f_current_string);
                int f_type_val = atoi(f_current_string->current_str);
                f_result->items[f_index][f_i2]->fx_type = f_type_val;
                f_result->items[f_index][f_i2]->func_ptr =
                        g_mf3_get_function_pointer(f_type_val);
                v_mf3_set(f_result->items[f_index][f_i2]->mf3,
                        f_result->items[f_index][f_i2]->a_knobs[0],
                        f_result->items[f_index][f_i2]->a_knobs[1],
                        f_result->items[f_index][f_i2]->a_knobs[2]);
                ++f_i2;
            }

            ++f_i;
        }

        g_free_2d_char_array(f_current_string);
    }

    return f_result;
}

void v_en_paif_set_control(t_edmnext * self, int a_region_uid,
        int a_item_index, int a_port, float a_val)
{
    int f_effect_index = a_port / 4;
    int f_control_index = a_port % 4;
    int f_song_index = i_en_song_index_from_region_uid(
        self, a_region_uid);
    t_en_per_audio_item_fx_region * f_region =
        self->en_song->per_audio_item_fx[f_song_index];
    t_per_audio_item_fx * f_item;
    float f_sr = musikernel->thread_storage[0].sample_rate;

    if(!f_region)
    {
        f_region = g_en_paif_region_get();
        pthread_spin_lock(&musikernel->main_lock);
        self->en_song->per_audio_item_fx[f_song_index] = f_region;
        pthread_spin_unlock(&musikernel->main_lock);
    }

    if(!f_region->loaded[a_item_index])
    {
        t_per_audio_item_fx * f_items[8];
        int f_i = 0;
        while(f_i < 8)
        {
            f_items[f_i] = g_paif_get(f_sr);
            ++f_i;
        }
        pthread_spin_lock(&musikernel->main_lock);
        f_i = 0;
        while(f_i < 8)
        {
            f_region->items[a_item_index][f_i] = f_items[f_i];
            ++f_i;
        }
        f_region->loaded[a_item_index] = 1;
        pthread_spin_unlock(&musikernel->main_lock);
    }

    f_item = f_region->items[a_item_index][f_effect_index];

    pthread_spin_lock(&musikernel->main_lock);

    if(f_control_index == 3)
    {
        int f_fx_index = (int)a_val;
        f_item->fx_type = f_fx_index;
        f_item->func_ptr = g_mf3_get_function_pointer(f_fx_index);

        v_mf3_set(f_item->mf3, f_item->a_knobs[0],
            f_item->a_knobs[1], f_item->a_knobs[2]);
    }
    else
    {
        f_region->items[a_item_index][
            f_effect_index]->a_knobs[f_control_index] = a_val;

        v_mf3_set(f_item->mf3, f_item->a_knobs[0],
            f_item->a_knobs[1], f_item->a_knobs[2]);
    }

    pthread_spin_unlock(&musikernel->main_lock);

}

void v_en_osc_send(t_osc_send_data * a_buffers)
{
    int f_i;
    t_pkm_peak_meter * f_pkm;

    a_buffers->f_tmp1[0] = '\0';
    a_buffers->f_tmp2[0] = '\0';

    f_pkm = edmnext->track_pool[0]->peak_meter;
    sprintf(a_buffers->f_tmp2, "%i:%f:%f", 0, f_pkm->value[0], f_pkm->value[1]);
    v_pkm_reset(f_pkm);

    for(f_i = 1; f_i < EN_TRACK_COUNT; ++f_i)
    {
        f_pkm = edmnext->track_pool[f_i]->peak_meter;
        if(!f_pkm->dirty)  //has ran since last v_pkm_reset())
        {
            sprintf(a_buffers->f_tmp1, "|%i:%f:%f",
                f_i, f_pkm->value[0], f_pkm->value[1]);
            v_pkm_reset(f_pkm);
            strcat(a_buffers->f_tmp2, a_buffers->f_tmp1);
        }
    }

    v_queue_osc_message("peak", a_buffers->f_tmp2);

    a_buffers->f_tmp1[0] = '\0';
    a_buffers->f_tmp2[0] = '\0';

    if(musikernel->playback_mode > 0 && !musikernel->is_offline_rendering)
    {
        sprintf(a_buffers->f_msg, "%i|%i|%f",
            edmnext->current_region, edmnext->current_bar,
            edmnext->ts[0].ml_current_beat);
        v_queue_osc_message("cur", a_buffers->f_msg);
    }

    if(musikernel->osc_queue_index > 0)
    {
        f_i = 0;

        while(f_i < musikernel->osc_queue_index)
        {
            strcpy(a_buffers->osc_queue_keys[f_i],
                musikernel->osc_queue_keys[f_i]);
            strcpy(a_buffers->osc_queue_vals[f_i],
                musikernel->osc_queue_vals[f_i]);
            ++f_i;
        }

        pthread_spin_lock(&musikernel->main_lock);

        //Now grab any that may have been written since the previous copy

        while(f_i < musikernel->osc_queue_index)
        {
            strcpy(a_buffers->osc_queue_keys[f_i],
                musikernel->osc_queue_keys[f_i]);
            strcpy(a_buffers->osc_queue_vals[f_i],
                musikernel->osc_queue_vals[f_i]);
            ++f_i;
        }

        int f_index = musikernel->osc_queue_index;
        musikernel->osc_queue_index = 0;

        pthread_spin_unlock(&musikernel->main_lock);

        f_i = 0;

        a_buffers->f_tmp1[0] = '\0';

        while(f_i < f_index)
        {
            sprintf(a_buffers->f_tmp2, "%s|%s\n",
                a_buffers->osc_queue_keys[f_i],
                a_buffers->osc_queue_vals[f_i]);
            strcat(a_buffers->f_tmp1, a_buffers->f_tmp2);
            ++f_i;
        }

        if(!musikernel->is_offline_rendering)
        {
            lo_send(musikernel->uiTarget,
                "musikernel/edmnext", "s", a_buffers->f_tmp1);
        }
    }
}


void v_en_sum_track_outputs(t_edmnext * self, t_pytrack * a_track,
        int a_sample_count, int a_playback_mode, t_en_thread_storage * a_ts)
{
    int f_bus_num;
    register int f_i2;
    t_pytrack * f_bus;
    t_pytrack_routing * f_route;
    t_pydaw_plugin * f_plugin = 0;
    float ** f_buff;
    float ** f_track_buff = a_track->buffers;

    if((edmnext->routing_graph->bus_count[a_track->track_num])
        ||
        ((!a_track->mute) && (!self->is_soloed))
        ||
        ((self->is_soloed) && (a_track->solo)))
    {
        if(a_track->fade_state == FADE_STATE_FADED)
        {
            a_track->fade_state = FADE_STATE_RETURNING;
            v_rmp_retrigger(&a_track->fade_env, 0.1f, 1.0f);
        }
        else if(a_track->fade_state == FADE_STATE_FADING)
        {
            a_track->fade_env.output = 1.0f - a_track->fade_env.output;
            a_track->fade_state = FADE_STATE_RETURNING;
        }
    }
    else
    {
        if(a_track->fade_state == FADE_STATE_OFF)
        {
            a_track->fade_state = FADE_STATE_FADING;
            v_rmp_retrigger(&a_track->fade_env, 0.1f, 1.0f);
        }
        else if(a_track->fade_state == FADE_STATE_RETURNING)
        {
            a_track->fade_env.output = 1.0f - a_track->fade_env.output;
            a_track->fade_state = FADE_STATE_FADING;
        }
    }

    f_i2 = 0;

    if(a_track->fade_state == FADE_STATE_OFF)
    {

    }
    else if(a_track->fade_state == FADE_STATE_FADING)
    {
        while(f_i2 < a_sample_count)
        {
            f_rmp_run_ramp(&a_track->fade_env);

            f_track_buff[0][f_i2] *= (1.0f - a_track->fade_env.output);
            f_track_buff[1][f_i2] *= (1.0f - a_track->fade_env.output);
            ++f_i2;
        }

        if(a_track->fade_env.output >= 1.0f)
        {
            a_track->fade_state = FADE_STATE_FADED;
        }
    }
    else if(a_track->fade_state == FADE_STATE_RETURNING)
    {
        while(f_i2 < a_sample_count)
        {
            f_rmp_run_ramp(&a_track->fade_env);
            f_track_buff[0][f_i2] *= a_track->fade_env.output;
            f_track_buff[1][f_i2] *= a_track->fade_env.output;
            ++f_i2;
        }

        if(a_track->fade_env.output >= 1.0f)
        {
            a_track->fade_state = FADE_STATE_OFF;
        }
    }


    int f_i3;

    for(f_i3 = 0; f_i3 < MAX_ROUTING_COUNT; ++f_i3)
    {
        f_route = &self->routing_graph->routes[a_track->track_num][f_i3];

        if(!f_route->active)
        {
            continue;
        }

        f_bus_num = f_route->output;

        if(f_bus_num < 0)
        {
            continue;
        }

        int f_plugin_index = MAX_PLUGIN_COUNT + f_i3;

        if(a_track->plugins[f_plugin_index])
        {
            f_plugin = a_track->plugins[f_plugin_index];
        }
        else
        {
            f_plugin = 0;
        }

        f_bus = self->track_pool[f_bus_num];

        if(f_route->sidechain)
        {
            f_buff = f_bus->sc_buffers;
            f_bus->sc_buffers_dirty = 1;
        }
        else
        {
            f_buff = f_bus->buffers;
        }

        if(a_track->fade_state != FADE_STATE_FADED)
        {
            if(f_plugin && f_plugin->power)
            {
                v_en_process_atm(self, a_track->track_num,
                    f_plugin_index, a_sample_count, a_playback_mode, a_ts);

                pthread_spin_lock(&f_bus->lock);

                f_plugin->descriptor->run_mixing(
                    f_plugin->PYFX_handle, a_sample_count,
                    f_buff, 2, a_track->event_buffer,
                    a_track->period_event_index,
                    f_plugin->atm_buffer, f_plugin->atm_count,
                    a_track->extern_midi, *a_track->extern_midi_count);
            }
            else
            {
                pthread_spin_lock(&f_bus->lock);

                v_buffer_mix(a_sample_count, f_track_buff, f_buff);
            }
        }
        else
        {
            pthread_spin_lock(&f_bus->lock);
        }

        --f_bus->bus_counter;
        pthread_spin_unlock(&f_bus->lock);
    }
}

void v_en_wait_for_bus(t_pytrack * a_track)
{
    int f_bus_count = edmnext->routing_graph->bus_count[a_track->track_num];
    int f_i;

    if(a_track->track_num && f_bus_count)
    {
        for(f_i = 0; f_i < 100000000; ++f_i)
        {
            pthread_spin_lock(&a_track->lock);

            if(a_track->bus_counter <= 0)
            {
                pthread_spin_unlock(&a_track->lock);
                break;
            }

            pthread_spin_unlock(&a_track->lock);
        }

        if(f_i == 100000000)
        {
            printf("Detected deadlock waiting for bus %i\n",
                a_track->track_num);
        }

        if(a_track->bus_counter < 0)
        {
            printf("Bus %i had bus_counter < 0: %i\n",
                a_track->track_num, a_track->bus_counter);
        }
    }
}

void v_en_process_track(t_edmnext * self, int a_global_track_num,
        int a_thread_num, int a_sample_count, int a_playback_mode,
        t_en_thread_storage * a_ts)
{
    t_pytrack * f_track = self->track_pool[a_global_track_num];
    t_pydaw_plugin * f_plugin;

    if(a_playback_mode > 0)
    {
        v_en_process_midi(
            self, a_global_track_num, a_sample_count, a_playback_mode, a_ts);
    }
    else
    {
        f_track->period_event_index = 0;
    }

    v_en_process_external_midi(self, f_track, a_sample_count,
        a_thread_num, a_ts);

    v_en_process_note_offs(self, a_global_track_num);

    v_en_wait_for_bus(f_track);

    v_en_audio_items_run(self, a_sample_count,
        f_track->buffers, f_track->sc_buffers, a_global_track_num, 0,
        &f_track->sc_buffers_dirty, a_ts);

    int f_i = 0;

    while(f_i < MAX_PLUGIN_COUNT)
    {
        f_plugin = f_track->plugins[f_i];
        if(f_plugin && f_plugin->power)
        {
            v_en_process_atm(self, a_global_track_num,
                f_i, a_sample_count, a_playback_mode, a_ts);
            f_plugin->descriptor->run_replacing(
                f_plugin->PYFX_handle, a_sample_count,
                f_track->event_buffer, f_track->period_event_index,
                f_plugin->atm_buffer, f_plugin->atm_count,
                f_track->extern_midi, *f_track->extern_midi_count);
        }
        ++f_i;
    }

    if(a_global_track_num)
    {
        v_en_sum_track_outputs(self, f_track,
            a_sample_count, a_playback_mode, a_ts);
    }

    v_pkm_run(f_track->peak_meter, f_track->buffers[0],
        f_track->buffers[1], a_sample_count);

    if(a_global_track_num)
    {
        v_pydaw_zero_buffer(f_track->buffers, a_sample_count);
    }

    if(f_track->sc_buffers_dirty)
    {
        f_track->sc_buffers_dirty = 0;
        v_pydaw_zero_buffer(f_track->sc_buffers, a_sample_count);
    }
}

inline void v_en_process(t_pydaw_thread_args * f_args)
{
    t_pytrack * f_track;
    int f_track_index;
    t_edmnext * self = edmnext;
    int f_i = f_args->thread_num;
    int f_sorted_count = self->routing_graph->track_pool_sorted_count;
    int * f_sorted = self->routing_graph->track_pool_sorted[f_args->thread_num];
    int f_sample_count = musikernel->sample_count;
    int f_playback_mode = musikernel->playback_mode;

    t_en_thread_storage * f_ts = &edmnext->ts[f_args->thread_num];

    if(f_args->thread_num > 0)
    {
        memcpy(f_ts, &edmnext->ts[0], sizeof(t_en_thread_storage));
    }

    while(f_i < f_sorted_count)
    {
        f_track_index = f_sorted[f_i];
        f_track = self->track_pool[f_track_index];

        if(f_track->status != STATUS_NOT_PROCESSED)
        {
            ++f_i;
            continue;
        }

        pthread_spin_lock(&f_track->lock);

        if(f_track->status == STATUS_NOT_PROCESSED)
        {
            f_track->status = STATUS_PROCESSING;
        }
        else
        {
            pthread_spin_unlock(&f_track->lock);
            ++f_i;
            continue;
        }

        pthread_spin_unlock(&f_track->lock);

        v_en_process_track(self, f_track->track_num, f_args->thread_num,
            f_sample_count, f_playback_mode, f_ts);

        f_track->status = STATUS_PROCESSED;

        ++f_i;
    }
}


inline void v_en_process_atm(
    t_edmnext * self, int f_track_num, int f_index, int sample_count,
    int a_playback_mode, t_en_thread_storage * a_ts)
{
    t_pytrack * f_track = self->track_pool[f_track_num];
    t_pydaw_plugin * f_plugin = f_track->plugins[f_index];
    int f_current_track_region = self->current_region;
    int f_current_track_bar = self->current_bar;
    float f_track_current_period_beats = a_ts->ml_current_period_beats;
    float f_track_next_period_beats = a_ts->ml_next_period_beats;
    float f_track_beats_offset = 0.0f;
    int f_pool_index = f_plugin->pool_uid;

    f_plugin->atm_count = 0;

    if((!self->overdub_mode) && (a_playback_mode == 2) &&
        (f_track->extern_midi))
    {
        return;
    }

    while(1)
    {
        if(self->en_song->regions_atm[f_current_track_region] &&
            self->en_song->regions_atm[
                f_current_track_region]->plugins[f_pool_index].point_count)
        {
            t_en_atm_plugin * f_current_item =
                &self->en_song->regions_atm[
                    f_current_track_region]->plugins[f_pool_index];

            if((f_plugin->atm_pos) >= (f_current_item->point_count))
            {
                if(f_track_next_period_beats >= 4.0f)
                {
                    f_track_current_period_beats = 0.0f;
                    f_track_next_period_beats =
                        f_track_next_period_beats - 4.0f;
                    f_track_beats_offset =
                        ((a_ts->ml_sample_period_inc) * 4.0f) -
                        f_track_next_period_beats;

                    f_plugin->atm_pos = 0;

                    ++f_current_track_bar;

                    if(f_current_track_bar >= self->f_region_length_bars)
                    {
                        f_current_track_bar = 0;

                        if(self->loop_mode != EN_LOOP_MODE_REGION)
                        {
                            ++f_current_track_region;
                        }
                    }

                    continue;
                }
                else
                {
                    break;
                }
            }

            t_en_atm_point * f_point =
                &f_current_item->points[f_plugin->atm_pos];

            if((f_point->bar < f_current_track_bar) ||
                ((f_point->bar == f_current_track_bar) &&
                (f_point->beat < f_track_current_period_beats)))
            {
                ++f_plugin->atm_pos;
                continue;
            }


            if((f_point->bar == f_current_track_bar) &&
                (f_point->beat >= f_track_current_period_beats) &&
                (f_point->beat < f_track_next_period_beats))
            {
                t_pydaw_seq_event * f_buff_ev =
                    &f_plugin->atm_buffer[f_plugin->atm_count];

                int f_note_sample_offset = 0;
                float f_note_start_diff =
                    ((f_point->beat) - f_track_current_period_beats) +
                    f_track_beats_offset;
                float f_note_start_frac =
                    f_note_start_diff / a_ts->ml_sample_period_inc_beats;
                f_note_sample_offset =
                    (int)(f_note_start_frac * (float)sample_count);

                if(f_plugin->uid == f_point->plugin)
                {
                    float f_val = f_atm_to_ctrl_val(
                        f_plugin->descriptor, f_point->port, f_point->val);
                    v_pydaw_ev_clear(f_buff_ev);
                    v_pydaw_ev_set_atm(f_buff_ev, f_point->port, f_val);
                    f_buff_ev->tick = f_note_sample_offset;
                    v_pydaw_set_control_from_atm(
                        f_buff_ev, f_plugin->pool_uid, f_track);
                    ++f_plugin->atm_count;
                }
                ++f_plugin->atm_pos;
            }
            else
            {
                break;
            }
        }
        else
        {
            if(f_track_next_period_beats >= 4.0f)
            {
                f_track_current_period_beats = 0.0f;
                f_track_next_period_beats =
                    f_track_next_period_beats - 4.0f;
                f_track_beats_offset =
                    ((a_ts->ml_sample_period_inc) * 4.0f) -
                        f_track_next_period_beats;

                ++f_current_track_bar;

                if(f_current_track_bar >= self->f_region_length_bars)
                {
                    f_current_track_bar = 0;
                    f_plugin->atm_pos = 0;

                    if(self->loop_mode != EN_LOOP_MODE_REGION)
                    {
                        ++f_current_track_region;
                    }
                }

                continue;
            }
            else
            {
                break;
            }
        }
    }
}

void v_en_process_midi(t_edmnext * self, int f_i, int sample_count,
        int a_playback_mode, t_en_thread_storage * a_ts)
{
    t_pytrack * f_track = self->track_pool[f_i];
    f_track->period_event_index = 0;

    int f_current_track_region = self->current_region;
    int f_current_track_bar = self->current_bar;
    float f_track_current_period_beats = (a_ts->ml_current_period_beats);
    float f_track_next_period_beats = (a_ts->ml_next_period_beats);
    float f_track_beats_offset = 0.0f;

    if((!self->overdub_mode) && (a_playback_mode == 2) &&
        (f_track->extern_midi))
    {

    }
    else
    {
        while(1)
        {
            if((self->en_song->regions[f_current_track_region]) &&
                (self->en_song->regions[
                    f_current_track_region]->item_indexes[
                        f_i][f_current_track_bar] != -1))
            {
                t_en_item * f_current_item =
                    self->item_pool[(self->en_song->regions[
                        f_current_track_region]->item_indexes[
                            f_i][f_current_track_bar])];

                if((f_track->item_event_index) >= (f_current_item->event_count))
                {
                    if(f_track_next_period_beats >= 4.0f)
                    {
                        f_track_current_period_beats = 0.0f;
                        f_track_next_period_beats -= 4.0f;
                        f_track_beats_offset =
                            ((a_ts->ml_sample_period_inc) * 4.0f) -
                            f_track_next_period_beats;

                        f_track->item_event_index = 0;

                        ++f_current_track_bar;

                        if(f_current_track_bar >= self->f_region_length_bars)
                        {
                            f_current_track_bar = 0;

                            if(self->loop_mode !=
                                    EN_LOOP_MODE_REGION)
                            {
                                ++f_current_track_region;
                            }
                        }

                        continue;
                    }
                    else
                    {
                        break;
                    }
                }

                t_pydaw_seq_event * f_event =
                    &f_current_item->events[f_track->item_event_index];

                if((f_event->start >= f_track_current_period_beats) &&
                    (f_event->start < f_track_next_period_beats))
                {
                    if(f_event->type == PYDAW_EVENT_NOTEON)
                    {
                        int f_note_sample_offset = 0;
                        float f_note_start_diff =
                            f_event->start - f_track_current_period_beats +
                            f_track_beats_offset;
                        float f_note_start_frac = f_note_start_diff /
                                (a_ts->ml_sample_period_inc_beats);
                        f_note_sample_offset =  (int)(f_note_start_frac *
                                ((float)sample_count));

                        if(f_track->note_offs[f_event->note]
                            >= (self->current_sample))
                        {
                            t_pydaw_seq_event * f_buff_ev;

                            /*There's already a note_off scheduled ahead of
                             * this one, process it immediately to avoid
                             * hung notes*/
                            f_buff_ev = &f_track->event_buffer[
                                f_track->period_event_index];
                            v_pydaw_ev_clear(f_buff_ev);

                            v_pydaw_ev_set_noteoff(f_buff_ev, 0,
                                    (f_event->note), 0);
                            f_buff_ev->tick = f_note_sample_offset;

                            ++f_track->period_event_index;
                        }

                        t_pydaw_seq_event * f_buff_ev =
                            &f_track->event_buffer[f_track->period_event_index];

                        v_pydaw_ev_clear(f_buff_ev);

                        v_pydaw_ev_set_noteon(f_buff_ev, 0,
                                f_event->note, f_event->velocity);

                        f_buff_ev->tick = f_note_sample_offset;

                        ++f_track->period_event_index;

                        f_track->note_offs[(f_event->note)] =
                            (self->current_sample) + ((int)(f_event->length *
                            self->samples_per_beat));
                    }
                    else if(f_event->type == PYDAW_EVENT_CONTROLLER)
                    {
                        int controller = f_event->param;

                        t_pydaw_seq_event * f_buff_ev =
                            &f_track->event_buffer[f_track->period_event_index];

                        int f_note_sample_offset = 0;

                        float f_note_start_diff =
                            ((f_event->start) - f_track_current_period_beats) +
                            f_track_beats_offset;
                        float f_note_start_frac = f_note_start_diff /
                            a_ts->ml_sample_period_inc_beats;
                        f_note_sample_offset =
                            (int)(f_note_start_frac * ((float)sample_count));

                        v_pydaw_ev_clear(f_buff_ev);

                        v_pydaw_ev_set_controller(
                            f_buff_ev, 0, controller, f_event->value);

                        v_pydaw_set_control_from_cc(f_buff_ev, f_track);

                        f_buff_ev->tick = f_note_sample_offset;

                        ++f_track->period_event_index;
                    }
                    else if(f_event->type == PYDAW_EVENT_PITCHBEND)
                    {
                        int f_note_sample_offset = 0;
                        float f_note_start_diff = ((f_event->start) -
                        f_track_current_period_beats) + f_track_beats_offset;
                        float f_note_start_frac = f_note_start_diff /
                            a_ts->ml_sample_period_inc_beats;
                        f_note_sample_offset =  (int)(f_note_start_frac *
                            ((float)sample_count));

                        t_pydaw_seq_event * f_buff_ev =
                            &f_track->event_buffer[f_track->period_event_index];

                        v_pydaw_ev_clear(f_buff_ev);
                        v_pydaw_ev_set_pitchbend(f_buff_ev, 0, f_event->value);
                        f_buff_ev->tick = f_note_sample_offset;

                        ++f_track->period_event_index;
                    }

                    ++f_track->item_event_index;
                }
                else
                {
                    break;
                }
            }
            else
            {
                if(f_track_next_period_beats >= 4.0f)
                {
                    f_track_current_period_beats = 0.0f;
                    f_track_next_period_beats =
                        f_track_next_period_beats - 4.0f;
                    f_track_beats_offset = (a_ts->ml_sample_period_inc
                        * 4.0f) - f_track_next_period_beats;

                    f_track->item_event_index = 0;

                    ++f_current_track_bar;

                    if(f_current_track_bar >= self->f_region_length_bars)
                    {
                        f_current_track_bar = 0;

                        if(self->loop_mode != EN_LOOP_MODE_REGION)
                        {
                            ++f_current_track_region;
                        }
                    }

                    continue;
                }
                else
                {
                    break;
                }
            }
        }
    }
}

void v_en_process_note_offs(t_edmnext * self, int f_i)
{
    t_pytrack * f_track = self->track_pool[f_i];
    long f_current_sample = self->current_sample;
    long f_next_current_sample = self->f_next_current_sample;

    register int f_i2 = 0;
    long f_note_off;

    while(f_i2 < PYDAW_MIDI_NOTE_COUNT)
    {
        f_note_off = f_track->note_offs[f_i2];
        if(f_note_off >=  f_current_sample &&
           f_note_off < f_next_current_sample)
        {
            t_pydaw_seq_event * f_event =
                &f_track->event_buffer[f_track->period_event_index];
            v_pydaw_ev_clear(f_event);

            v_pydaw_ev_set_noteoff(f_event, 0, f_i2, 0);
            f_event->tick = f_note_off - f_current_sample;
            ++f_track->period_event_index;
            f_track->note_offs[f_i2] = -1;
        }
        ++f_i2;
    }
}

void v_en_process_external_midi(t_edmnext * self,
        t_pytrack * a_track, int sample_count, int a_thread_num,
        t_en_thread_storage * a_ts)
{
    if(!a_track->midi_device)
    {
        return;
    }

    float f_sample_rate = musikernel->thread_storage[a_thread_num].sample_rate;
    int f_playback_mode = musikernel->playback_mode;
    int f_midi_learn = musikernel->midi_learn;
    float f_tempo = self->tempo;

    midiDeviceRead(a_track->midi_device, f_sample_rate, sample_count);

    int f_extern_midi_count = *a_track->extern_midi_count;
    t_pydaw_seq_event * events = a_track->extern_midi;

    assert(f_extern_midi_count < 200);

    register int f_i2 = 0;

    char * f_osc_msg = a_track->osc_cursor_message;

    while(f_i2 < f_extern_midi_count)
    {
        if(events[f_i2].tick >= sample_count)
        {
            //Otherwise the event will be missed
            events[f_i2].tick = sample_count - 1;
        }

        if(events[f_i2].type == PYDAW_EVENT_NOTEON)
        {
            if(f_playback_mode == PYDAW_PLAYBACK_MODE_REC)
            {
                float f_beat = a_ts->ml_current_period_beats +
                    f_pydaw_samples_to_beat_count(events[f_i2].tick,
                        f_tempo, f_sample_rate);

                sprintf(f_osc_msg, "on|%i|%i|%f|%i|%i|%i|%ld",
                    self->current_region, self->current_bar, f_beat,
                    a_track->track_num, events[f_i2].note,
                    events[f_i2].velocity,
                    self->current_sample + events[f_i2].tick);
                v_queue_osc_message("mrec", f_osc_msg);
            }

            sprintf(f_osc_msg, "1|%i", events[f_i2].note);
            v_queue_osc_message("ne", f_osc_msg);

        }
        else if(events[f_i2].type == PYDAW_EVENT_NOTEOFF)
        {
            if(f_playback_mode == PYDAW_PLAYBACK_MODE_REC)
            {
                float f_beat = a_ts->ml_current_period_beats +
                    f_pydaw_samples_to_beat_count(events[f_i2].tick,
                        f_tempo, f_sample_rate);

                sprintf(f_osc_msg, "off|%i|%i|%f|%i|%i|%ld",
                    self->current_region, self->current_bar, f_beat,
                    a_track->track_num, events[f_i2].note,
                    self->current_sample + events[f_i2].tick);
                v_queue_osc_message("mrec", f_osc_msg);
            }

            sprintf(f_osc_msg, "0|%i", events[f_i2].note);
            v_queue_osc_message("ne", f_osc_msg);
        }
        else if(events[f_i2].type == PYDAW_EVENT_PITCHBEND)
        {
            if(f_playback_mode == PYDAW_PLAYBACK_MODE_REC)
            {
                float f_beat = a_ts->ml_current_period_beats +
                    f_pydaw_samples_to_beat_count(events[f_i2].tick,
                        f_tempo, f_sample_rate);

                sprintf(f_osc_msg, "pb|%i|%i|%f|%i|%f|%ld",
                    self->current_region, self->current_bar, f_beat,
                    a_track->track_num, events[f_i2].value,
                    self->current_sample + events[f_i2].tick);
                v_queue_osc_message("mrec", f_osc_msg);
            }
        }
        else if(events[f_i2].type == PYDAW_EVENT_CONTROLLER)
        {
            int controller = events[f_i2].param;

            if(f_midi_learn)
            {
                musikernel->midi_learn = 0;
                f_midi_learn = 0;
                sprintf(f_osc_msg, "%i", controller);
                v_queue_osc_message("ml", f_osc_msg);
            }

            /*float f_start =
                ((self->playback_cursor) +
                ((((float)(events[f_i2].tick)) / ((float)sample_count))
                * (self->playback_inc))) * 4.0f;*/
            v_pydaw_set_control_from_cc(&events[f_i2], a_track);

            if(f_playback_mode == PYDAW_PLAYBACK_MODE_REC)
            {
                float f_beat =
                    a_ts->ml_current_period_beats +
                    f_pydaw_samples_to_beat_count(
                        events[f_i2].tick, f_tempo,
                        f_sample_rate);

                sprintf(f_osc_msg,
                    "cc|%i|%i|%f|%i|%i|%f",
                    self->current_region, self->current_bar, f_beat,
                    a_track->track_num, controller, events[f_i2].value);
                v_queue_osc_message("mrec", f_osc_msg);
            }
        }
        ++f_i2;
    }
}


inline void v_pydaw_set_time_params(t_edmnext * self,
        int sample_count)
{
    self->ts[0].ml_sample_period_inc =
        ((self->playback_inc) * ((float)(sample_count)));
    self->ts[0].ml_sample_period_inc_beats =
        (self->ts[0].ml_sample_period_inc) * 4.0f;
    self->ts[0].ml_next_playback_cursor =
        (self->playback_cursor) + (self->ts[0].ml_sample_period_inc);
    self->ts[0].ml_current_period_beats =
        (self->playback_cursor) * 4.0f;
    self->ts[0].ml_next_period_beats =
        (self->ts[0].ml_next_playback_cursor) * 4.0f;

    self->ts[0].ml_current_region = (self->current_region);
    self->ts[0].ml_current_bar = (self->current_bar);
    self->ts[0].ml_current_beat = (self->ts[0].ml_current_period_beats);

    self->ts[0].ml_next_bar = (self->current_bar);
    self->ts[0].ml_next_region = (self->current_region);

    if((self->ts[0].ml_next_period_beats) > 4.0f)  //Should it be >= ???
    {
        self->ts[0].ml_starting_new_bar = 1;
        self->ts[0].ml_next_beat =
            (self->ts[0].ml_next_period_beats) - 4.0f;

        self->ts[0].ml_next_bar = (self->current_bar) + 1;

        int f_region_length = 8;
        if(self->en_song->regions[(self->current_region)])
        {
            f_region_length =
                (self->en_song->regions[
                    (self->current_region)]->region_length_bars);
        }

        if(f_region_length == 0)
        {
            f_region_length = 8;
        }

        if((self->ts[0].ml_next_bar) >= f_region_length)
        {
            self->ts[0].ml_next_bar = 0;
            if(self->loop_mode != EN_LOOP_MODE_REGION)
            {
                ++self->ts[0].ml_next_region;
            }
            else
            {
                self->ts[0].ml_is_looping = 1;
            }
        }
    }
    else
    {
        self->ts[0].ml_is_looping = 0;
        self->ts[0].ml_starting_new_bar = 0;
        self->ts[0].ml_next_region = self->current_region;
        self->ts[0].ml_next_bar = self->current_bar;
        self->ts[0].ml_next_beat = self->ts[0].ml_next_period_beats;
    }
}

inline void v_pydaw_finish_time_params(t_edmnext * self,
        int a_region_length_bars)
{
    self->playback_cursor = (self->ts[0].ml_next_playback_cursor);

    if((self->playback_cursor) >= 1.0f)
    {
        self->playback_cursor = (self->playback_cursor) - 1.0f;

        ++self->current_bar;

        if((self->current_bar) >= a_region_length_bars)
        {
            self->current_bar = 0;

            if(self->loop_mode != EN_LOOP_MODE_REGION)
            {
                ++self->current_region;

                if((self->current_region) >= EN_MAX_REGION_COUNT)
                {
                    musikernel->playback_mode = 0;
                    self->current_region = 0;
                }
            }
            else if(musikernel->playback_mode == PYDAW_PLAYBACK_MODE_REC)
            {
                float f_beat = self->ts[0].ml_current_period_beats;

                sprintf(musikernel->osc_cursor_message, "loop|%i|%i|%f|%ld",
                    self->current_region, self->current_bar, f_beat,
                    self->current_sample +
                    i_beat_count_to_samples(4.0 - f_beat, self->tempo,
                        musikernel->thread_storage[0].sample_rate));
                v_queue_osc_message("mrec", musikernel->osc_cursor_message);
            }
        }
    }
}

inline void v_en_run_engine(int sample_count,
        float **output, float *a_input_buffers)
{
    t_edmnext * self = edmnext;
    //notify the worker threads to wake up
    register int f_i = 1;
    while(f_i < musikernel->worker_thread_count)
    {
        pthread_spin_lock(&musikernel->thread_locks[f_i]);
        pthread_mutex_lock(&musikernel->track_block_mutexes[f_i]);
        pthread_cond_broadcast(&musikernel->track_cond[f_i]);
        pthread_mutex_unlock(&musikernel->track_block_mutexes[f_i]);
        ++f_i;
    }

    long f_next_current_sample = edmnext->current_sample + sample_count;

    musikernel->sample_count = sample_count;
    self->f_next_current_sample = f_next_current_sample;

    if((musikernel->playback_mode) > 0)
    {
        v_pydaw_set_time_params(self, sample_count);

        self->f_region_length_bars =
                self->default_region_length_bars;
        //float f_bar_length = (float)(self->default_bar_length);

        if(self->en_song->regions[(self->current_region)])
        {
            if(self->en_song->regions[
                (self->current_region)]->bar_length)
            {
                //f_bar_length = (float)(self->en_song->regions[
                        //(self->current_region)]->bar_length);
            }

            if(self->en_song->regions[self->current_region]->region_length_bars)
            {
                self->f_region_length_bars =
                    self->en_song->regions[
                        (self->current_region)]->region_length_bars;

                if(self->en_song->regions[
                        (self->current_region)]->region_length_beats)
                {
                    ++self->f_region_length_bars;

                    if((self->current_bar) == (self->f_region_length_bars - 1))
                    {
                        //f_bar_length = (float)(self->en_song->regions[
                        //    (self->current_region)]->
                        //    region_length_beats);
                    }
                }
            }
        }
    }

    for(f_i = 0; f_i < EN_TRACK_COUNT; ++f_i)
    {
        self->track_pool[f_i]->status = STATUS_NOT_PROCESSED;
        self->track_pool[f_i]->bus_counter =
            self->routing_graph->bus_count[f_i];
    }

    //unleash the hounds
    for(f_i = 1; f_i < musikernel->worker_thread_count; ++f_i)
    {
        pthread_spin_unlock(&musikernel->thread_locks[f_i]);
    }

    v_en_process((t_pydaw_thread_args*)musikernel->main_thread_args);

    t_pytrack * f_master_track = self->track_pool[0];
    float ** f_master_buff = f_master_track->buffers;

    //wait for the other threads to finish
    v_wait_for_threads();

    v_en_process_track(self, 0, 0, sample_count,
        musikernel->playback_mode, &self->ts[0]);

    for(f_i = 0; f_i < sample_count; ++f_i)
    {
        output[0][f_i] = f_master_buff[0][f_i];
        output[1][f_i] = f_master_buff[1][f_i];
    }

    v_pydaw_zero_buffer(f_master_buff, sample_count);

    if((musikernel->playback_mode) > 0)
    {
        v_pydaw_finish_time_params(self, self->f_region_length_bars);
    }

    edmnext->current_sample = f_next_current_sample;
}


void v_en_audio_items_run(t_edmnext * self,
    int a_sample_count, float** a_buff, float ** a_sc_buff,
    int a_audio_track_num, int a_is_audio_glue, int * a_sc_dirty,
    t_en_thread_storage * a_ts)
{
    if(!a_is_audio_glue &&
      (!self->en_song->audio_items[self->current_region] ||
      !self->en_song->audio_items[
        self->current_region]->index_counts[a_audio_track_num])
      && (!self->en_song->audio_items[a_ts->ml_next_region] ||
        !self->en_song->audio_items[
          a_ts->ml_next_region]->index_counts[a_audio_track_num]))
    {
        return;
    }

    int f_i6 = 0;
    int f_region_count = 1;
    int f_playback_mode = musikernel->playback_mode;
    t_en_per_audio_item_fx_region * f_paif_region;
    t_per_audio_item_fx * f_paif_item;

    if(a_ts->ml_current_region != a_ts->ml_next_region || a_ts->ml_is_looping)
    {
        f_region_count = 2;
    }

    int f_adjusted_sample_count = a_sample_count;
    int f_start_sample = 0;

    while(f_i6 < f_region_count)
    {
        float f_adjusted_song_pos_beats;
        float f_adjusted_next_song_pos_beats;
        int f_current_region = a_ts->ml_current_region;

        f_adjusted_song_pos_beats = f_en_count_beats(self,
                a_ts->ml_current_region, 0, 0.0f,
                a_ts->ml_current_region, a_ts->ml_current_bar,
                a_ts->ml_current_beat);

        if(f_region_count == 2)
        {
            if(f_i6 == 0)
            {
                if(!self->en_song->audio_items[f_current_region])
                {
                    ++f_i6;
                    continue;
                }

                if(self->en_song->regions[
                    (self->current_region)]->region_length_bars == 0)
                {
                    f_adjusted_next_song_pos_beats = 32.0f;
                }
                else
                {
                    f_adjusted_next_song_pos_beats =
                        (float)(self->en_song->regions[
                        (self->current_region)]->region_length_bars * 4);
                }

                float test1 = (int)(f_adjusted_next_song_pos_beats);
                float test2 = test1 - f_adjusted_song_pos_beats;
                float test3 = (test2 /
                    (a_ts->ml_sample_period_inc_beats)) *
                    ((float)(a_sample_count));
                f_adjusted_sample_count = (int)test3;
                assert(f_adjusted_sample_count < a_sample_count);

            }
            else
            {
                f_start_sample = f_adjusted_sample_count;
                f_adjusted_sample_count = a_sample_count;
                // - f_adjusted_sample_count;

                f_current_region = a_ts->ml_next_region;

                if(!self->en_song->audio_items[f_current_region])
                {
                    break;
                }

                f_adjusted_song_pos_beats = 0.0f;
                f_adjusted_next_song_pos_beats = a_ts->ml_next_beat;
            }
        }
        else
        {
            if(!self->en_song->audio_items[f_current_region])
            {
                break;
            }

            f_adjusted_next_song_pos_beats = f_en_count_beats(self,
                    a_ts->ml_current_region, 0, 0.0f,
                    a_ts->ml_next_region,
                    a_ts->ml_next_bar, a_ts->ml_next_beat);
        }

        f_paif_region = self->en_song->per_audio_item_fx[(f_current_region)];

        t_pydaw_audio_items * f_region =
            self->en_song->audio_items[f_current_region];
        f_paif_region = self->en_song->per_audio_item_fx[f_current_region];

        int f_i = 0;
        int f_index_pos = 0;
        int f_send_num = 0;
        float ** f_buff = a_buff;

        while(a_is_audio_glue ||
            f_index_pos < f_region->index_counts[a_audio_track_num])
        {
            if(!a_is_audio_glue)
            {
                f_i = f_region->indexes[
                    a_audio_track_num][f_index_pos].item_num;
                f_send_num = f_region->indexes[
                    a_audio_track_num][f_index_pos].send_num;
                ++f_index_pos;
            }
            else
            {
                if(f_i >= PYDAW_MAX_AUDIO_ITEM_COUNT)
                {
                    break;
                }
            }

            if(f_region->items[f_i] == 0)
            {
                ++f_i;
                continue;
            }

            t_pydaw_audio_item * f_audio_item = f_region->items[f_i];

            if(!a_is_audio_glue && f_audio_item->sidechain[f_send_num])
            {
                f_buff = a_sc_buff;
                *a_sc_dirty = 1;
            }

            if(self->suppress_new_audio_items &&
                ((f_audio_item->adsrs[f_send_num].stage) == ADSR_STAGE_OFF))
            {
                ++f_i;
                continue;
            }

            if(a_is_audio_glue  && !self->audio_glue_indexes[f_i])
            {
                ++f_i;
                continue;
            }

            if(f_playback_mode == PYDAW_PLAYBACK_MODE_OFF &&
                f_audio_item->adsrs[f_send_num].stage < ADSR_STAGE_RELEASE)
            {
                v_adsr_release(&f_audio_item->adsrs[f_send_num]);
            }

            if(a_is_audio_glue ||
            f_audio_item->outputs[f_send_num] == a_audio_track_num)
            {
                if((f_audio_item->adjusted_start_beat) >=
                        f_adjusted_next_song_pos_beats)
                {
                    ++f_i;
                    continue;
                }

                register int f_i2 = f_start_sample;

                if(((f_audio_item->adjusted_start_beat) >=
                        f_adjusted_song_pos_beats) &&
                    ((f_audio_item->adjusted_start_beat) <
                        f_adjusted_next_song_pos_beats))
                {
                    if(f_audio_item->is_reversed)
                    {
                        v_ifh_retrigger(
                            &f_audio_item->sample_read_heads[f_send_num],
                            f_audio_item->sample_end_offset);
                    }
                    else
                    {
                        v_ifh_retrigger(
                            &f_audio_item->sample_read_heads[f_send_num],
                            f_audio_item->sample_start_offset);
                    }

                    v_svf_reset(&f_audio_item->lp_filters[f_send_num]);

                    v_adsr_retrigger(&f_audio_item->adsrs[f_send_num]);

                    float f_diff = (f_adjusted_next_song_pos_beats -
                        f_adjusted_song_pos_beats);
                    float f_distance = f_adjusted_next_song_pos_beats -
                        (f_audio_item->adjusted_start_beat);

                    f_i2 = f_adjusted_sample_count - (int)((f_distance /
                            f_diff) * ((float)(f_adjusted_sample_count -
                            f_start_sample)));

                    if(f_i2 < 0)
                    {
                        f_i2 = 0;
                    }
                    else if(f_i2 >= f_adjusted_sample_count)
                    {
                        f_i2 = f_adjusted_sample_count - 1;
                    }
                }

                if((f_audio_item->adsrs[f_send_num].stage) != ADSR_STAGE_OFF)
                {
                    while((f_i2 < f_adjusted_sample_count) &&
                        (((!f_audio_item->is_reversed) &&
                        ((f_audio_item->sample_read_heads[
                            f_send_num].whole_number) <
                        (f_audio_item->sample_end_offset)))
                            ||
                        ((f_audio_item->is_reversed) &&
                        ((f_audio_item->sample_read_heads[
                            f_send_num].whole_number) >
                        (f_audio_item->sample_start_offset)))
                        ))
                    {
                        assert(f_i2 < a_sample_count);
                        v_pydaw_audio_item_set_fade_vol(
                            f_audio_item, f_send_num);

                        if(f_audio_item->wav_pool_item->channels == 1)
                        {
                            float f_tmp_sample0 = f_cubic_interpolate_ptr_ifh(
                            (f_audio_item->wav_pool_item->samples[0]),
                            (f_audio_item->sample_read_heads[
                                f_send_num].whole_number),
                            (f_audio_item->sample_read_heads[
                                f_send_num].fraction)) *
                            (f_audio_item->adsrs[f_send_num].output) *
                            (f_audio_item->vols_linear[f_send_num]) *
                            (f_audio_item->fade_vols[f_send_num]);

                            float f_tmp_sample1 = f_tmp_sample0;

                            if(f_paif_region)
                            {
                                if(f_paif_region->loaded[f_i])
                                {
                                    int f_i3;
                                    for(f_i3 = 0; f_i3 < 8; ++f_i3)
                                    {
                                        f_paif_item =
                                            f_paif_region->items[f_i][f_i3];
                                        f_paif_item->func_ptr(
                                            f_paif_item->mf3,
                                            f_tmp_sample0, f_tmp_sample1);
                                        f_tmp_sample0 =
                                            f_paif_item->mf3->output0;
                                        f_tmp_sample1 =
                                            f_paif_item->mf3->output1;
                                    }
                                }
                            }

                            f_buff[0][f_i2] += f_tmp_sample0;
                            f_buff[1][f_i2] += f_tmp_sample1;
                        }
                        else if(f_audio_item->wav_pool_item->channels == 2)
                        {
                            assert(f_audio_item->sample_read_heads[
                                    f_send_num].whole_number
                                <=
                                f_audio_item->wav_pool_item->length);

                            assert(f_audio_item->sample_read_heads[
                                    f_send_num].whole_number
                                >=
                                PYDAW_AUDIO_ITEM_PADDING_DIV2);

                            float f_tmp_sample0 = f_cubic_interpolate_ptr_ifh(
                            f_audio_item->wav_pool_item->samples[0],
                            f_audio_item->sample_read_heads[
                                f_send_num].whole_number,
                            f_audio_item->sample_read_heads[
                                f_send_num].fraction) *
                            f_audio_item->adsrs[f_send_num].output *
                            f_audio_item->vols_linear[f_send_num] *
                            f_audio_item->fade_vols[f_send_num];

                            float f_tmp_sample1 = f_cubic_interpolate_ptr_ifh(
                            f_audio_item->wav_pool_item->samples[1],
                            f_audio_item->sample_read_heads[
                                f_send_num].whole_number,
                            f_audio_item->sample_read_heads[
                                f_send_num].fraction) *
                            f_audio_item->adsrs[f_send_num].output *
                            f_audio_item->vols_linear[f_send_num]
                            * f_audio_item->fade_vols[f_send_num];

                            if(f_paif_region)
                            {
                                if(f_paif_region->loaded[f_i])
                                {
                                    int f_i3 = 0;
                                    while(f_i3 < 8)
                                    {
                                        f_paif_item =
                                            f_paif_region->items[f_i][f_i3];
                                        f_paif_item->func_ptr(
                                            f_paif_item->mf3,
                                            f_tmp_sample0, f_tmp_sample1);
                                        f_tmp_sample0 =
                                            f_paif_item->mf3->output0;
                                        f_tmp_sample1 =
                                            f_paif_item->mf3->output1;
                                        ++f_i3;
                                    }
                                }
                            }

                            f_buff[0][f_i2] += f_tmp_sample0;
                            f_buff[1][f_i2] += f_tmp_sample1;

                        }
                        else
                        {
                            // TODO:  Catch this during load and
                            // do something then...
                            printf(
                                "Error: v_pydaw_en_song->audio_items"
                                "[f_current_region]_run, invalid number "
                                "of channels %i\n",
                                f_audio_item->wav_pool_item->channels);
                        }

                        if(f_audio_item->is_reversed)
                        {
                            v_ifh_run_reverse(
                                &f_audio_item->sample_read_heads[f_send_num],
                                f_audio_item->ratio);

                            if(f_audio_item->sample_read_heads[
                                    f_send_num].whole_number <
                                PYDAW_AUDIO_ITEM_PADDING_DIV2)
                            {
                                f_audio_item->adsrs[
                                    f_send_num].stage = ADSR_STAGE_OFF;
                            }
                        }
                        else
                        {
                            v_ifh_run(
                                &f_audio_item->sample_read_heads[f_send_num],
                                f_audio_item->ratio);

                            if(f_audio_item->sample_read_heads[
                                    f_send_num].whole_number >=
                                f_audio_item->wav_pool_item->length - 1)
                            {
                                f_audio_item->adsrs[f_send_num].stage =
                                    ADSR_STAGE_OFF;
                            }
                        }


                        if(f_audio_item->adsrs[f_send_num].stage ==
                            ADSR_STAGE_OFF)
                        {
                            break;
                        }

                        v_adsr_run_db(&f_audio_item->adsrs[f_send_num]);

                        ++f_i2;
                    }//while < sample count
                }  //if stage
            } //if this track_num
            ++f_i;
        } //while < audio item count
        ++f_i6;
    } //region count loop
    return;
}

void g_en_song_get(t_edmnext* self, int a_lock)
{
    t_en_song * f_result = (t_en_song*)malloc(sizeof(t_en_song));

    int f_i = 0;

    while(f_i < EN_MAX_REGION_COUNT)
    {
        f_result->regions[f_i] = 0;
        f_result->regions_atm[f_i] = 0;
        f_result->audio_items[f_i] = 0;
        f_result->per_audio_item_fx[f_i] = 0;
        ++f_i;
    }

    char f_full_path[2048];
    sprintf(f_full_path, "%s/projects/edmnext/song.txt",
        musikernel->project_folder);

    if(i_pydaw_file_exists(f_full_path))
    {
        f_i = 0;

        t_2d_char_array * f_current_string =
            g_get_2d_array_from_file(f_full_path, PYDAW_LARGE_STRING);

        while(f_i < EN_MAX_REGION_COUNT)
        {
            v_iterate_2d_char_array(f_current_string);
            if(f_current_string->eof)
            {
                break;
            }
            int f_pos = atoi(f_current_string->current_str);
            v_iterate_2d_char_array(f_current_string);
            int f_uid = atoi(f_current_string->current_str);
            f_result->regions[f_pos] = g_en_region_get(self, f_uid);
            f_result->regions[f_pos]->uid = f_uid;
            f_result->regions_atm[f_pos] = g_en_atm_region_get(self, f_uid);
            //v_pydaw_audio_items_free(self->audio_items);
            f_result->audio_items[f_pos] =
                v_en_audio_items_load_all(self, f_uid);
            f_result->per_audio_item_fx[f_pos] =
                g_en_paif_region_open(self, f_uid);
            ++f_i;
        }

        g_free_2d_char_array(f_current_string);
    }

    t_en_song * f_old = self->en_song;

    if(a_lock)
    {
        pthread_spin_lock(&musikernel->main_lock);
    }

    self->en_song = f_result;

    if(a_lock)
    {
        pthread_spin_unlock(&musikernel->main_lock);
    }

    if(f_old)
    {
        v_en_song_free(f_old);
    }

}


void v_en_open_tracks()
{
    char f_file_name[1024];
    sprintf(f_file_name, "%s/projects/edmnext/tracks.txt",
        musikernel->project_folder);

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

            int f_track_index = atoi(f_2d_array->current_str);

            v_iterate_2d_char_array(f_2d_array);
            int f_solo = atoi(f_2d_array->current_str);
            v_iterate_2d_char_array(f_2d_array);
            int f_mute = atoi(f_2d_array->current_str);
            v_iterate_2d_char_array(f_2d_array);  //ignored
            v_iterate_2d_char_array(f_2d_array); //ignored

            assert(f_track_index >= 0 && f_track_index < EN_TRACK_COUNT);
            assert(f_solo == 0 || f_solo == 1);
            assert(f_mute == 0 || f_mute == 1);

            v_pydaw_open_track(edmnext->track_pool[f_track_index],
                edmnext->tracks_folder, f_track_index);

            edmnext->track_pool[f_track_index]->solo = f_solo;
            edmnext->track_pool[f_track_index]->mute = f_mute;
        }

        g_free_2d_char_array(f_2d_array);
    }
    else   //ensure everything is closed...
    {
        int f_i = 0;

        while(f_i < EN_TRACK_COUNT)
        {
            edmnext->track_pool[f_i]->solo = 0;
            edmnext->track_pool[f_i]->mute = 0;
            v_pydaw_open_track(edmnext->track_pool[f_i],
                edmnext->tracks_folder, f_i);
            ++f_i;
        }
    }
}


void v_en_open_project(int a_first_load)
{
    sprintf(edmnext->item_folder, "%s/projects/edmnext/items/",
        musikernel->project_folder);
    sprintf(edmnext->region_folder, "%s/projects/edmnext/regions/",
        musikernel->project_folder);
    sprintf(edmnext->region_audio_folder, "%s/projects/edmnext/regions_audio/",
        musikernel->project_folder);
    sprintf(edmnext->region_atm_folder, "%s/projects/edmnext/regions_atm/",
        musikernel->project_folder);
    sprintf(edmnext->per_audio_item_fx_folder,
        "%s/projects/edmnext/audio_per_item_fx/", musikernel->project_folder);
    sprintf(edmnext->tracks_folder, "%s/projects/edmnext/tracks",
        musikernel->project_folder);

    int f_i = 0;

    while(f_i < EN_MAX_ITEM_COUNT)
    {
        if(edmnext->item_pool[f_i])
        {
            free(edmnext->item_pool[f_i]);
            edmnext->item_pool[f_i] = NULL;
        }
        ++f_i;
    }

    char f_song_file[1024];
    sprintf(f_song_file,
        "%s/projects/edmnext/song.txt", musikernel->project_folder);

    struct stat f_proj_stat;
    stat((musikernel->project_folder), &f_proj_stat);
    struct stat f_item_stat;
    stat((edmnext->item_folder), &f_item_stat);
    struct stat f_reg_stat;
    stat((edmnext->region_folder), &f_reg_stat);
    struct stat f_song_file_stat;
    stat(f_song_file, &f_song_file_stat);

    //TODO:  This should be moved to a separate function
    char f_transport_file[1024];
    sprintf(f_transport_file, "%s/projects/edmnext/transport.txt",
            musikernel->project_folder);

    if(i_pydaw_file_exists(f_transport_file))
    {
        t_2d_char_array * f_2d_array = g_get_2d_array_from_file(
                f_transport_file, PYDAW_LARGE_STRING);
        v_iterate_2d_char_array(f_2d_array);
        float f_tempo = atof(f_2d_array->current_str);

        assert(f_tempo > 30.0f && f_tempo < 300.0f);
        v_en_set_tempo(edmnext, f_tempo);
        g_free_2d_char_array(f_2d_array);
    }
    else  //No transport file, set default tempo
    {
        printf("No transport file found, defaulting to 128.0 BPM\n");
        v_en_set_tempo(edmnext, 128.0f);
    }

    if(S_ISDIR(f_proj_stat.st_mode) &&
        S_ISDIR(f_item_stat.st_mode) &&
        S_ISDIR(f_reg_stat.st_mode) &&
        S_ISREG(f_song_file_stat.st_mode))
    {
        t_dir_list * f_item_dir_list =
                g_get_dir_list(edmnext->item_folder);
        f_i = 0;

        while(f_i < f_item_dir_list->dir_count)
        {
            g_en_item_get(edmnext, atoi(f_item_dir_list->dir_list[f_i]));
            ++f_i;
        }

        g_en_song_get(edmnext, 0);

        if(a_first_load)
        {
            v_en_open_tracks();
        }
    }
    else
    {
        printf("Song file and project directory structure not found, not "
                "loading project.  This is to be expected if launching PyDAW "
                "for the first time\n");
        //Loads empty...  TODO:  Make this a separate function for getting an
        //empty en_song or loading a file into one...
        g_en_song_get(edmnext, 0);
    }

    v_en_update_track_send(edmnext, 0);

    v_en_set_is_soloed(edmnext);

    v_en_set_midi_devices();
}


int i_en_song_index_from_region_uid(t_edmnext* self, int a_uid)
{
    int f_i = 0;

    while(f_i < EN_MAX_REGION_COUNT)
    {
        if(self->en_song->regions[f_i])
        {
            if(a_uid == self->en_song->regions[f_i]->uid)
            {
                return f_i;
            }
        }
        ++f_i;
    }
    return -1;
}

t_en_atm_region * g_en_atm_region_get(t_edmnext * self, int a_uid)
{
    t_en_atm_region * f_result = NULL;

    char f_file[1024] = "\0";
    sprintf(f_file, "%s%i", self->region_atm_folder, a_uid);

    if(i_pydaw_file_exists(f_file))
    {
        lmalloc((void**)&f_result, sizeof(t_en_atm_region));

        int f_i2;
        for(f_i2 = 0; f_i2 < MAX_PLUGIN_POOL_COUNT; ++f_i2)
        {
            f_result->plugins[f_i2].point_count = 0;
            f_result->plugins[f_i2].points = NULL;
        }

        t_2d_char_array * f_current_string = g_get_2d_array_from_file(f_file,
            PYDAW_XLARGE_STRING); //TODO:  1MB big enough???

        int f_pos = 0;

        while(1)
        {
            v_iterate_2d_char_array(f_current_string);
            if(f_current_string->eof)
            {
                break;
            }

            if(f_current_string->current_str[0] == 'p')
            {
                v_iterate_2d_char_array(f_current_string);
                int f_index = atoi(f_current_string->current_str);

                v_iterate_2d_char_array(f_current_string);
                int f_count = atoi(f_current_string->current_str);

                assert(f_count >= 1 && f_count < 100000);  //sanity check

                f_result->plugins[f_index].point_count = f_count;
                lmalloc(
                    (void**)&f_result->plugins[f_index].points,
                    sizeof(t_en_atm_point) * f_count);
                f_pos = 0;
            }
            else
            {
                int f_bar = atoi(f_current_string->current_str);

                v_iterate_2d_char_array(f_current_string);
                float f_beat = atof(f_current_string->current_str);

                v_iterate_2d_char_array(f_current_string);
                int f_port = atoi(f_current_string->current_str);

                v_iterate_2d_char_array(f_current_string);
                float f_val = atof(f_current_string->current_str);

                v_iterate_2d_char_array(f_current_string);
                int f_index = atoi(f_current_string->current_str);

                v_iterate_2d_char_array(f_current_string);
                int f_plugin = atoi(f_current_string->current_str);

                assert(f_pos < f_result->plugins[f_index].point_count);

                assert(f_result->plugins[f_index].points);

                t_en_atm_point * f_point =
                    &f_result->plugins[f_index].points[f_pos];

                f_point->bar = f_bar;
                f_point->beat = f_beat;
                f_point->port = f_port;
                f_point->val = f_val;
                f_point->index = f_index;
                f_point->plugin = f_plugin;

                ++f_pos;
            }
        }

        g_free_2d_char_array(f_current_string);
    }

    return f_result;
}

void v_en_atm_region_free(t_en_atm_region * self)
{
    int f_i2 = 0;
    while(f_i2 < MAX_PLUGIN_TOTAL_COUNT)
    {
        if(self->plugins[f_i2].point_count)
        {
            free(self->plugins[f_i2].points);
        }
        ++f_i2;
    }

    free(self);
}

t_en_region * g_en_region_get(t_edmnext* self, int a_uid)
{
    t_en_region * f_result = (t_en_region*)malloc(sizeof(t_en_region));

    f_result->alternate_tempo = 0;
    f_result->tempo = 128.0f;
    f_result->region_length_bars = 0;
    f_result->region_length_beats = 0;
    f_result->bar_length = 0;
    f_result->uid = a_uid;
    f_result->not_yet_saved = 0;

    int f_i = 0;
    int f_i2 = 0;

    while(f_i < EN_TRACK_COUNT)
    {
        f_i2 = 0;
        while(f_i2 < EN_MAX_REGION_SIZE)
        {
            f_result->item_indexes[f_i][f_i2] = -1;
            ++f_i2;
        }
        ++f_i;
    }


    char f_full_path[PYDAW_TINY_STRING];
    sprintf(f_full_path, "%s%i", self->region_folder, a_uid);

    t_2d_char_array * f_current_string =
        g_get_2d_array_from_file(f_full_path, PYDAW_LARGE_STRING);

    f_i = 0;

    while(f_i < 264)
    {
        v_iterate_2d_char_array(f_current_string);
        if(f_current_string->eof)
        {
            break;
        }

        if(!strcmp("L", f_current_string->current_str))
        {
            v_iterate_2d_char_array(f_current_string);
            int f_bars = atoi(f_current_string->current_str);
            f_result->region_length_bars = f_bars;

            v_iterate_2d_char_array(f_current_string);
            int f_beats = atoi(f_current_string->current_str);
            f_result->region_length_beats = f_beats;
            continue;
        }
        if(!strcmp("T", f_current_string->current_str))  //per-region tempo, not yet implemented
        {
            v_iterate_2d_char_array(f_current_string);
            f_result->alternate_tempo = 1;
            f_result->tempo = atof(f_current_string->current_str);

            v_iterate_2d_char_array(f_current_string);  //not used
            continue;
        }
        //per-region bar length in beats, not yet implemented
        if(!strcmp("B", f_current_string->current_str))
        {
            v_iterate_2d_char_array(f_current_string);
            f_result->bar_length = atoi(f_current_string->current_str);

            v_iterate_2d_char_array(f_current_string);  //not used
            continue;
        }

        int f_y = atoi(f_current_string->current_str);

        v_iterate_2d_char_array(f_current_string);
        int f_x = atoi(f_current_string->current_str);

        v_iterate_2d_char_array(f_current_string);
        assert(f_y < EN_TRACK_COUNT);
        assert(f_x < EN_MAX_REGION_SIZE);
        f_result->item_indexes[f_y][f_x] = atoi(f_current_string->current_str);
        assert(self->item_pool[f_result->item_indexes[f_y][f_x]]);

        ++f_i;
    }

    g_free_2d_char_array(f_current_string);

    //v_pydaw_assert_memory_integrity(self);

    return f_result;
}


void g_en_item_get(t_edmnext* self, int a_uid)
{
    t_en_item * f_result;
    lmalloc((void**)&f_result, sizeof(t_en_item));

    f_result->event_count = 0;
    f_result->uid = a_uid;

    char f_full_path[2048];
    sprintf(f_full_path, "%s%i", self->item_folder, a_uid);

    t_2d_char_array * f_current_string = g_get_2d_array_from_file(f_full_path,
            PYDAW_LARGE_STRING);

    int f_i = 0;

    while(f_i < EN_MAX_EVENTS_PER_ITEM_COUNT)
    {
        v_iterate_2d_char_array(f_current_string);

        if(f_current_string->eof)
        {
            break;
        }

        char f_type = f_current_string->current_str[0];

        v_iterate_2d_char_array(f_current_string);
        float f_start = atof(f_current_string->current_str);

        if(f_type == 'n')  //note
        {
            v_iterate_2d_char_array(f_current_string);
            float f_length = atof(f_current_string->current_str);
            v_iterate_2d_char_array(f_current_string);
            int f_note = atoi(f_current_string->current_str);
            v_iterate_2d_char_array(f_current_string);
            int f_vel = atoi(f_current_string->current_str);
            assert((f_result->event_count) < EN_MAX_EVENTS_PER_ITEM_COUNT);
            g_pynote_init(&f_result->events[(f_result->event_count)],
                    f_note, f_vel, f_start, f_length);
            ++f_result->event_count;
        }
        else if(f_type == 'c') //cc
        {
            v_iterate_2d_char_array(f_current_string);
            int f_cc_num = atoi(f_current_string->current_str);
            v_iterate_2d_char_array(f_current_string);
            float f_cc_val = atof(f_current_string->current_str);

            g_pycc_init(&f_result->events[(f_result->event_count)],
                f_cc_num, f_cc_val, f_start);
            ++f_result->event_count;
        }
        else if(f_type == 'p') //pitchbend
        {
            v_iterate_2d_char_array(f_current_string);
            float f_pb_val = atof(f_current_string->current_str) * 8192.0f;

            g_pypitchbend_init(&f_result->events[(f_result->event_count)],
                    f_start, f_pb_val);
            ++f_result->event_count;
        }
        else
        {
            printf("Invalid event type %c\n", f_type);
        }
        ++f_i;
    }

    g_free_2d_char_array(f_current_string);

    if(self->item_pool[a_uid])
    {
        free(self->item_pool[a_uid]);
    }

    self->item_pool[a_uid] = f_result;
}

t_edmnext * g_edmnext_get()
{
    t_edmnext * f_result;
    clalloc((void**)&f_result, sizeof(t_edmnext));

    f_result->current_sample = 0;
    f_result->current_bar = 0;
    f_result->current_region = 0;
    f_result->playback_cursor = 0.0f;
    f_result->playback_inc = 0.0f;

    f_result->overdub_mode = 0;
    f_result->loop_mode = 0;
    f_result->item_folder = (char*)malloc(sizeof(char) * 1024);
    f_result->region_folder = (char*)malloc(sizeof(char) * 1024);
    f_result->region_audio_folder = (char*)malloc(sizeof(char) * 1024);
    f_result->region_atm_folder = (char*)malloc(sizeof(char) * 1024);
    f_result->per_audio_item_fx_folder = (char*)malloc(sizeof(char) * 1024);
    f_result->tracks_folder = (char*)malloc(sizeof(char) * 1024);

    f_result->en_song = NULL;
    f_result->is_soloed = 0;
    f_result->suppress_new_audio_items = 0;

    f_result->ts[0].ml_current_period_beats = 0.0f;
    f_result->ts[0].ml_next_period_beats = 0.0f;
    f_result->ts[0].ml_next_playback_cursor = 0.0f;
    f_result->ts[0].ml_sample_period_inc = 0.0f;
    f_result->ts[0].ml_sample_period_inc_beats = 0.0f;

    f_result->ts[0].ml_current_region = 0;
    f_result->ts[0].ml_next_region = 0;
    f_result->ts[0].ml_next_bar = 0;
    f_result->ts[0].ml_next_beat = 0.0;
    f_result->ts[0].ml_starting_new_bar = 0;
    f_result->ts[0].ml_is_looping = 0;

    f_result->default_region_length_bars = 8;
    f_result->default_region_length_beats = 0;
    f_result->default_bar_length = 4;

    f_result->routing_graph = 0;

    int f_i = 0;
    int f_track_total = 0;


    while(f_i < EN_TRACK_COUNT)
    {
        f_result->track_pool[f_track_total] = g_pytrack_get(
            f_i, musikernel->thread_storage[0].sample_rate);
        ++f_i;
        ++f_track_total;
    }

    f_i = 0;

    while(f_i < PYDAW_MAX_AUDIO_ITEM_COUNT)
    {
        f_result->audio_glue_indexes[f_i] = 0;
        ++f_i;
    }

    f_i = 0;

    while(f_i < EN_MAX_ITEM_COUNT)
    {
        f_result->item_pool[f_i] = NULL;
        ++f_i;
    }

    g_en_midi_routing_list_init(&f_result->midi_routing);

    return f_result;
}

/* void v_en_set_playback_mode(t_pydaw_data * self,
 * int a_mode, //
 * int a_region, //The region index to start playback on
 * int a_bar) //The bar index (with a_region) to start playback on
 */
void v_en_set_playback_mode(t_edmnext * self, int a_mode,
        int a_region, int a_bar, int a_lock)
{
    switch(a_mode)
    {
        case 0: //stop
        {
            register int f_i = 0;
            int f_i2;
            t_pytrack * f_track;

            if(a_lock)
            {
                pthread_spin_lock(&musikernel->main_lock);
            }

            self->suppress_new_audio_items = 1;
            //Fade out the playing audio tracks
            if(self->en_song->audio_items[self->current_region])
            {
                while(f_i < PYDAW_MAX_AUDIO_ITEM_COUNT)
                {
                    if(self->en_song->audio_items[
                            self->current_region]->items[f_i])
                    {
                        for(f_i2 = 0; f_i2 < MK_AUDIO_ITEM_SEND_COUNT; ++f_i2)
                        {
                            v_adsr_release(&self->en_song->audio_items[
                                self->current_region]->items[f_i]->adsrs[f_i2]);
                        }
                    }
                    ++f_i;
                }
            }

            self->suppress_new_audio_items = 0;
            musikernel->playback_mode = a_mode;

            f_i = 0;

            t_pydaw_plugin * f_plugin;

            while(f_i < EN_TRACK_COUNT)
            {
                f_i2 = 0;
                f_track = self->track_pool[f_i];

                f_track->period_event_index = 0;

                while(f_i2 < MAX_PLUGIN_TOTAL_COUNT)
                {
                    f_plugin = f_track->plugins[f_i2];
                    if(f_plugin)
                    {
                        f_plugin->descriptor->on_stop(f_plugin->PYFX_handle);
                    }
                    ++f_i2;
                }

                f_track->item_event_index = 0;

                ++f_i;
            }

            if(a_lock)
            {
                pthread_spin_unlock(&musikernel->main_lock);
            }

        }
            break;
        case 1:  //play
        {
            if(a_lock)
            {
                pthread_spin_lock(&musikernel->main_lock);
            }

            v_en_set_playback_cursor(self, a_region, a_bar);

            musikernel->playback_mode = a_mode;

            if(a_lock)
            {
                pthread_spin_unlock(&musikernel->main_lock);
            }

            break;
        }
        case 2:  //record
            if(musikernel->playback_mode == PYDAW_PLAYBACK_MODE_REC)
            {
                return;
            }
            if(a_lock)
            {
                pthread_spin_lock(&musikernel->main_lock);
            }

            v_en_set_playback_cursor(self, a_region, a_bar);

            musikernel->playback_mode = a_mode;

            if(a_lock)
            {
                pthread_spin_unlock(&musikernel->main_lock);
            }
            break;
    }
}


/*Load/Reload samples from file...*/
t_pydaw_audio_items * v_en_audio_items_load_all(t_edmnext * self,
        int a_region_uid)
{
    float f_sample_rate = musikernel->thread_storage[0].sample_rate;
    t_pydaw_audio_items * f_result =
        g_pydaw_audio_items_get(f_sample_rate);
    char f_file[1024] = "\0";
    sprintf(f_file, "%s%i", self->region_audio_folder, a_region_uid);
    int f_i, f_i2;

    if(i_pydaw_file_exists(f_file))
    {
        t_2d_char_array * f_current_string = g_get_2d_array_from_file(f_file,
                PYDAW_LARGE_STRING);

        for(f_i = 0; f_i < PYDAW_MAX_AUDIO_ITEM_COUNT; ++f_i)
        {
            t_pydaw_audio_item * f_new =
                g_audio_item_load_single(f_sample_rate,
                    f_current_string, 0, musikernel->wav_pool, 0);
            if(!f_new)  //EOF'd...
            {
                break;
            }

            int f_global_index = f_new->outputs[0];

            f_result->indexes[f_global_index][
                f_result->index_counts[f_global_index]].item_num = f_new->index;
            f_result->indexes[f_global_index][
                f_result->index_counts[f_global_index]].send_num = 0;
            ++f_result->index_counts[f_global_index];

            for(f_i2 = 1; f_i2 < 3; ++f_i2)
            {
                f_global_index = f_new->outputs[f_i2];
                if(f_global_index > -1)
                {
                    f_result->indexes[f_global_index][
                    f_result->index_counts[f_global_index]].item_num =
                        f_new->index;
                    f_result->indexes[f_global_index][
                        f_result->index_counts[f_global_index]].send_num = f_i2;
                    ++f_result->index_counts[f_global_index];
                }
            }

            f_result->items[f_new->index] = f_new;
        }

        g_free_2d_char_array(f_current_string);
    }
    else
    {
        printf("Error:  v_en_audio_items_load_all:  a_file: \"%s\" "
                "does not exist\n", f_file);
        assert(0);
    }

    return f_result;
}


void v_en_set_playback_cursor(t_edmnext * self, int a_region, int a_bar)
{
    self->current_bar = a_bar;
    self->current_region = a_region;
    self->playback_cursor = 0.0f;
    self->ts[0].ml_current_period_beats = 0.0f;

    v_en_reset_audio_item_read_heads(self, a_region, a_bar);

    register int f_i = 0;

    while(f_i < EN_TRACK_COUNT)
    {
        self->track_pool[f_i]->item_event_index = 0;
        if((self->is_soloed && !self->track_pool[f_i]->solo) ||
            (self->track_pool[f_i]->mute))
        {
            self->track_pool[f_i]->fade_state = FADE_STATE_FADED;
        }
        ++f_i;
    }

    f_i = 0;

    while(f_i < MAX_PLUGIN_TOTAL_COUNT)
    {
        musikernel->plugin_pool[f_i].atm_pos = 0;
        ++f_i;
    }
}

void v_en_set_is_soloed(t_edmnext * self)
{
    int f_i = 0;
    self->is_soloed = 0;

    while(f_i < EN_TRACK_COUNT)
    {
        if(self->track_pool[f_i]->solo)
        {
            self->is_soloed = 1;
            break;
        }
        ++f_i;
    }
}

void v_en_set_loop_mode(t_edmnext * self, int a_mode)
{
    self->loop_mode = a_mode;
}

void v_en_set_tempo(t_edmnext * self, float a_tempo)
{
    float f_sample_rate = musikernel->thread_storage[0].sample_rate;
    self->tempo = a_tempo;
    self->playback_inc = ( (1.0f / (f_sample_rate)) /
        (60.0f / (a_tempo * 0.25f)) );
    self->samples_per_beat = (f_sample_rate) / (a_tempo / 60.0f);
}


/*Count the number of beats between 2 points in time...*/
inline float f_en_count_beats(t_edmnext * self,
        int a_start_region, int a_start_bar, float a_start_beat,
        int a_end_region, int a_end_bar, float a_end_beat)
{
    int f_bar_count = a_end_bar - a_start_bar;

    register int f_i = a_start_region;
    int f_beat_total = 0;

    while(f_i < a_end_region)
    {
        if((self->en_song->regions[f_i]) &&
                (self->en_song->regions[f_i]->region_length_bars))
        {
            f_beat_total +=
                    self->en_song->regions[f_i]->region_length_bars * 4;
        }
        else
        {
            f_beat_total += (8 * 4);
        }
        ++f_i;
    }

    f_beat_total += f_bar_count * 4;

    return ((float)(f_beat_total)) + (a_end_beat - a_start_beat);
}

void v_en_offline_render_prep(t_edmnext * self)
{
    printf("Warming up plugins for offline rendering...\n");
    register int f_i = 0;
    t_pytrack * f_track;
    t_pydaw_plugin * f_plugin;

    while(f_i < EN_TRACK_COUNT)
    {
        f_track = self->track_pool[f_i];
        int f_i2 = 0;
        while(f_i2 < MAX_PLUGIN_TOTAL_COUNT)
        {
            f_plugin = f_track->plugins[f_i2];
            if(f_plugin && f_plugin->descriptor->offline_render_prep)
            {
                f_plugin->descriptor->offline_render_prep(
                    f_plugin->PYFX_handle);
            }
            ++f_i2;
        }
        ++f_i;
    }
    printf("Finished warming up plugins\n");
}

void v_en_offline_render(t_edmnext * self, int a_start_region,
        int a_start_bar, int a_end_region,
        int a_end_bar, char * a_file_out, int a_is_audio_glue,
        int a_create_file)
{
    pthread_spin_lock(&musikernel->main_lock);
    musikernel->is_offline_rendering = 1;
    pthread_spin_unlock(&musikernel->main_lock);

    float f_sample_rate = musikernel->thread_storage[0].sample_rate;

    int f_bar_count = a_end_bar - a_start_bar;

    register int f_i = a_start_region;
    int f_beat_total = 0;

    while(f_i < a_end_region)
    {
        if((self->en_song->regions[f_i]) &&
                (self->en_song->regions[f_i]->region_length_bars))
        {
            f_beat_total +=
                    self->en_song->regions[f_i]->region_length_bars * 4;
        }
        else
        {
            f_beat_total += (8 * 4);
        }
        ++f_i;
    }

    f_beat_total += f_bar_count * 4;

    float f_sample_count =
        self->samples_per_beat * ((float)f_beat_total);

    long f_size = 0;
    long f_block_size = (musikernel->sample_count);

    float * f_output = (float*)malloc(sizeof(float) * (f_block_size * 2));

    float ** f_buffer;
    lmalloc((void**)&f_buffer, sizeof(float*) * 2);

    f_i = 0;
    while(f_i < 2)
    {
        lmalloc((void**)&f_buffer[f_i], sizeof(float) * f_block_size);
        ++f_i;
    }

    //We must set it back afterwards, or the UI will be wrong...
    int f_old_loop_mode = self->loop_mode;
    v_en_set_loop_mode(self, EN_LOOP_MODE_OFF);

    v_en_set_playback_mode(self, PYDAW_PLAYBACK_MODE_PLAY,
            a_start_region, a_start_bar, 0);

    printf("\nOpening SNDFILE with sample rate %i\n", (int)f_sample_rate);

    SF_INFO f_sf_info;
    f_sf_info.channels = 2;
    f_sf_info.format = SF_FORMAT_WAV | SF_FORMAT_FLOAT;
    f_sf_info.samplerate = (int)(f_sample_rate);

    SNDFILE * f_sndfile = sf_open(a_file_out, SFM_WRITE, &f_sf_info);

    printf("\nSuccessfully opened SNDFILE\n\n");

    struct timespec f_start, f_finish;
    clock_gettime(CLOCK_REALTIME, &f_start);

    int f_current_bar = 999;  //For printing the current region/bar

    while(((self->current_region) < a_end_region) ||
            ((self->current_bar) < a_end_bar))
    {
        if(self->current_bar != f_current_bar)
        {
            f_current_bar = self->current_bar;
            printf("%i:%i\n", self->current_region,
                    self->current_bar);
        }

        f_i = 0;
        f_size = 0;

        while(f_i < f_block_size)
        {
            f_buffer[0][f_i] = 0.0f;
            f_buffer[1][f_i] = 0.0f;
            ++f_i;
        }

        if(a_is_audio_glue)
        {
            v_pydaw_set_time_params(self, f_block_size);
            v_en_audio_items_run(
                self, f_block_size, f_buffer, NULL, -1, 1, NULL,
                &self->ts[0]);
            v_pydaw_finish_time_params(self, 999999);
        }
        else
        {
            v_en_run_engine(f_block_size, f_buffer, NULL);
        }

        f_i = 0;
        /*Interleave the samples...*/
        while(f_i < f_block_size)
        {
            f_output[f_size] = f_buffer[0][f_i];
            ++f_size;
            f_output[f_size] = f_buffer[1][f_i];
            ++f_size;
            ++f_i;
        }

        if(a_create_file)
        {
            sf_writef_float(f_sndfile, f_output, f_block_size);
        }
    }

    clock_gettime(CLOCK_REALTIME, &f_finish);
    float f_elapsed = (float)v_pydaw_print_benchmark(
        "v_en_offline_render", f_start, f_finish);
    float f_realtime = f_sample_count / f_sample_rate;

    printf("Realtime: %f\n", f_realtime);

    if(f_elapsed > 0.0f)
    {
        printf("Ratio:  %f : 1\n\n", f_realtime / f_elapsed);
    }
    else
    {
        printf("Ratio:  infinity : 1");
    }

    v_en_set_playback_mode(self, PYDAW_PLAYBACK_MODE_OFF, a_start_region,
            a_start_bar, 0);
    v_en_set_loop_mode(self, f_old_loop_mode);

    sf_close(f_sndfile);

    free(f_buffer[0]);
    free(f_buffer[1]);
    free(f_buffer);
    free(f_output);

    char f_tmp_finished[1024];

    sprintf(f_tmp_finished, "%s.finished", a_file_out);

    v_pydaw_write_to_file(f_tmp_finished, "finished");

    v_en_panic(self);  //ensure all notes are off before returning

    pthread_spin_lock(&musikernel->main_lock);
    musikernel->is_offline_rendering = 0;
    pthread_spin_unlock(&musikernel->main_lock);
}


void v_en_update_track_send(t_edmnext * self, int a_lock)
{
    t_en_routing_graph * f_graph = g_en_routing_graph_get(self);
    t_en_routing_graph * f_old = self->routing_graph;

    if(a_lock)
    {
        pthread_spin_lock(&musikernel->main_lock);
    }

    self->routing_graph = f_graph;

    if(a_lock)
    {
        pthread_spin_unlock(&musikernel->main_lock);
    }

    if(f_old)
    {
        v_en_routing_graph_free(f_old);
    }
}

t_pytrack_routing * g_pytrack_routing_get()
{
    t_pytrack_routing * f_result;
    lmalloc((void**)&f_result, sizeof(t_pytrack_routing));
    return f_result;
}

void v_pytrack_routing_set(t_pytrack_routing * self, int a_output,
        int a_sidechain)
{
    self->output = a_output;
    self->sidechain = a_sidechain;

    if(a_output >= 0)
    {
        self->active = 1;
    }
    else
    {
        self->active = 0;
    }
}

void v_pytrack_routing_free(t_pytrack_routing * self)
{
    free(self);
}

void v_en_routing_graph_free(t_en_routing_graph * self)
{
    free(self);
}

t_en_routing_graph * g_en_routing_graph_get(t_edmnext * self)
{
    t_en_routing_graph * f_result = NULL;
    lmalloc((void**)&f_result, sizeof(t_en_routing_graph));

    int f_i = 0;
    int f_i2 = 0;

    for(f_i = 0; f_i < EN_TRACK_COUNT; ++f_i)
    {
        for(f_i2 = 0; f_i2 < MAX_WORKER_THREADS; ++f_i2)
        {
            f_result->track_pool_sorted[f_i2][f_i] = 0;
            f_result->bus_count[f_i] = 0;
        }

        for(f_i2 = 0; f_i2 < MAX_ROUTING_COUNT; ++f_i2)
        {
            f_result->routes[f_i][f_i2].active = 0;
        }
    }

    f_result->track_pool_sorted_count = 0;

    char f_tmp[1024];
    sprintf(f_tmp, "%s/projects/edmnext/routing.txt",
        musikernel->project_folder);

    if(i_pydaw_file_exists(f_tmp))
    {
        t_2d_char_array * f_2d_array = g_get_2d_array_from_file(
        f_tmp, PYDAW_LARGE_STRING);
        while(1)
        {
            v_iterate_2d_char_array(f_2d_array);
            if(f_2d_array->eof)
            {
                break;
            }

            if(f_2d_array->current_str[0] == 't')
            {
                v_iterate_2d_char_array(f_2d_array);
                int f_track_num = atoi(f_2d_array->current_str);

                v_iterate_2d_char_array(f_2d_array);
                int f_index = atoi(f_2d_array->current_str);

                for(f_i = 0; f_i < MAX_WORKER_THREADS; ++f_i)
                {
                    f_result->track_pool_sorted[f_i][f_index] = f_track_num;
                }

            }
            else if(f_2d_array->current_str[0] == 's')
            {
                v_iterate_2d_char_array(f_2d_array);
                int f_track_num = atoi(f_2d_array->current_str);

                v_iterate_2d_char_array(f_2d_array);
                int f_index = atoi(f_2d_array->current_str);

                v_iterate_2d_char_array(f_2d_array);
                int f_output = atoi(f_2d_array->current_str);

                v_iterate_2d_char_array(f_2d_array);
                int f_sidechain = atoi(f_2d_array->current_str);

                v_pytrack_routing_set(
                    &f_result->routes[f_track_num][f_index], f_output,
                    f_sidechain);
                ++f_result->bus_count[f_output];
            }
            else if(f_2d_array->current_str[0] == 'c')
            {
                v_iterate_2d_char_array(f_2d_array);
                int f_count = atoi(f_2d_array->current_str);
                f_result->track_pool_sorted_count = f_count;
            }
            else
            {
                assert(0);
            }
        }
        g_free_2d_char_array(f_2d_array);
    }

    return f_result;
}

void v_en_set_midi_device(int a_on, int a_device, int a_output)
{
    t_edmnext * self = edmnext;
    /* Interim logic to get a minimum viable product working
     * TODO:  Make it modular and able to support multiple devices
     */
    t_en_midi_routing_list * f_list = &self->midi_routing;
    t_pydaw_midi_routing * f_route = &f_list->routes[a_device];
    t_pytrack * f_track_old = NULL;
    t_pytrack * f_track_new = self->track_pool[a_output];

    if(f_route->output_track != -1)
    {
        f_track_old = self->track_pool[f_route->output_track];
    }

    if(f_track_old && (!f_route->on || f_route->output_track != a_output))
    {
        f_track_old->extern_midi = 0;
        f_track_old->extern_midi_count = &ZERO;
        f_track_old->midi_device = 0;
    }

    f_route->on = a_on;
    f_route->output_track = a_output;

    if(f_route->on && musikernel->midi_devices->devices[a_device].loaded)
    {
        f_track_new->midi_device = &musikernel->midi_devices->devices[a_device];
        f_track_new->extern_midi =
            musikernel->midi_devices->devices[a_device].instanceEventBuffers;

        midiPoll(f_track_new->midi_device);
        midiDeviceRead(f_track_new->midi_device,
            musikernel->thread_storage[0].sample_rate, 512);

        musikernel->midi_devices->devices[a_device].instanceEventCounts = 0;
        musikernel->midi_devices->devices[a_device].midiEventReadIndex = 0;
        musikernel->midi_devices->devices[a_device].midiEventWriteIndex = 0;

        f_track_new->extern_midi_count =
            &musikernel->midi_devices->devices[a_device].instanceEventCounts;
    }
    else
    {
        f_track_new->extern_midi = 0;
        f_track_new->extern_midi_count = &ZERO;
        f_track_new->midi_device = 0;
    }
}


void v_en_set_midi_devices()
{
    char f_path[2048];
    int f_i, f_i2;
    t_midi_device * f_device;

    if(!musikernel->midi_devices)
    {
        return;
    }

    sprintf(f_path, "%s/projects/edmnext/midi_routing.txt",
        musikernel->project_folder);

    if(!i_pydaw_file_exists(f_path))
    {
        return;
    }

    t_2d_char_array * f_current_string =
        g_get_2d_array_from_file(f_path, PYDAW_LARGE_STRING);

    for(f_i = 0; f_i < EN_TRACK_COUNT; ++f_i)
    {
        v_iterate_2d_char_array(f_current_string);
        if(f_current_string->eof)
        {
            break;
        }

        int f_on = atoi(f_current_string->current_str);

        v_iterate_2d_char_array(f_current_string);
        int f_track_num = atoi(f_current_string->current_str);

        v_iterate_2d_char_array_to_next_line(f_current_string);

        for(f_i2 = 0; f_i2 < musikernel->midi_devices->count; ++f_i2)
        {
            f_device = &musikernel->midi_devices->devices[f_i2];
            if(!strcmp(f_current_string->current_str, f_device->name))
            {
                v_en_set_midi_device(f_on, f_i2, f_track_num);
                break;
            }
        }
    }

    g_free_2d_char_array(f_current_string);
}


void v_en_configure(const char* a_key, const char* a_value)
{
    t_edmnext * self = edmnext;
    printf("v_en_configure:  key: \"%s\", value: \"%s\"\n", a_key, a_value);

    if(!strcmp(a_key, EN_CONFIGURE_KEY_PER_AUDIO_ITEM_FX))
    {
        t_1d_char_array * f_arr = c_split_str(a_value, '|', 4,
                PYDAW_SMALL_STRING);
        int f_region_uid = atoi(f_arr->array[0]);
        int f_item_index = atoi(f_arr->array[1]);
        int f_port_num = atoi(f_arr->array[2]);
        float f_port_val = atof(f_arr->array[3]);

        v_en_paif_set_control(self, f_region_uid, f_item_index,
                f_port_num, f_port_val);
    }
    else if(!strcmp(a_key, EN_CONFIGURE_KEY_EN_PLAYBACK))
    {
        t_1d_char_array * f_arr = c_split_str(a_value, '|', 3,
                PYDAW_SMALL_STRING);
        int f_mode = atoi(f_arr->array[0]);
        assert(f_mode >= 0 && f_mode <= 2);
        int f_region = atoi(f_arr->array[1]);
        int f_bar = atoi(f_arr->array[2]);
        v_en_set_playback_mode(self, f_mode, f_region, f_bar, 1);
        g_free_1d_char_array(f_arr);
    }
    else if(!strcmp(a_key, EN_CONFIGURE_KEY_SR))
    {
        //Ensure that a project isn't being loaded right now
        pthread_spin_lock(&musikernel->main_lock);
        pthread_spin_unlock(&musikernel->main_lock);

        int f_uid = atoi(a_value);
        t_en_region * f_result = g_en_region_get(self, f_uid);
        int f_region_index = i_en_song_index_from_region_uid(self, f_uid);

        if(f_region_index >= 0 )
        {
            t_en_region * f_old_region = NULL;
            if(self->en_song->regions[f_region_index])
            {
                f_old_region = self->en_song->regions[f_region_index];
            }
            pthread_spin_lock(&musikernel->main_lock);
            self->en_song->regions[f_region_index] = f_result;
            pthread_spin_unlock(&musikernel->main_lock);
            if(f_old_region)
            {
                free(f_old_region);
            }
        }
        else
        {
            printf("region %i is not in song, not loading...", f_uid);
        }
    }
    else if(!strcmp(a_key, EN_CONFIGURE_KEY_SI)) //Save Item
    {
        pthread_spin_lock(&musikernel->main_lock);
        g_en_item_get(self, atoi(a_value));
        pthread_spin_unlock(&musikernel->main_lock);
    }
    else if(!strcmp(a_key, EN_CONFIGURE_KEY_SS))  //Save Song
    {
        g_en_song_get(self, 1);
    }
    else if(!strcmp(a_key, EN_CONFIGURE_KEY_SAVE_ATM))
    {
        int f_uid = atoi(a_value);
        t_en_atm_region * f_result = g_en_atm_region_get(self, f_uid);
        int f_region_index = i_en_song_index_from_region_uid(self, f_uid);

        if(f_region_index >= 0 )
        {
            t_en_atm_region * f_old_region = NULL;
            if(self->en_song->regions_atm[f_region_index])
            {
                f_old_region = self->en_song->regions_atm[f_region_index];
            }
            pthread_spin_lock(&musikernel->main_lock);
            self->en_song->regions_atm[f_region_index] = f_result;
            pthread_spin_unlock(&musikernel->main_lock);
            if(f_old_region)
            {
                v_en_atm_region_free(f_old_region);
            }
        }
        else
        {
            printf("region %i is not in song, not loading...", f_uid);
        }
    }
    else if(!strcmp(a_key, EN_CONFIGURE_KEY_AUDIO_ITEM_LOAD_ALL))
    {
        int f_uid = atoi(a_value);
        //t_pydaw_audio_items * f_old;
        t_pydaw_audio_items * f_result = v_en_audio_items_load_all(self,
                f_uid);
        int f_region_index = i_en_song_index_from_region_uid(self,
                f_uid);
        pthread_spin_lock(&musikernel->main_lock);
        self->en_song->audio_items[f_region_index] = f_result;
        pthread_spin_unlock(&musikernel->main_lock);
        //v_pydaw_audio_items_free(f_old); //Method needs to be re-thought...
    }
    else if(!strcmp(a_key, EN_CONFIGURE_KEY_PER_AUDIO_ITEM_FX_REGION))
    {
        int f_uid = atoi(a_value);
        t_en_per_audio_item_fx_region * f_result =
                g_en_paif_region_open(self, f_uid);
        int f_region_index = i_en_song_index_from_region_uid(self,
                f_uid);
        t_en_per_audio_item_fx_region * f_old =
                self->en_song->per_audio_item_fx[f_region_index];
        pthread_spin_lock(&musikernel->main_lock);
        self->en_song->per_audio_item_fx[f_region_index] = f_result;
        pthread_spin_unlock(&musikernel->main_lock);
        v_en_paif_region_free(f_old);
    }
    else if(!strcmp(a_key, EN_CONFIGURE_KEY_LOOP)) //Set loop mode
    {
        int f_value = atoi(a_value);

        pthread_spin_lock(&musikernel->main_lock);
        v_en_set_loop_mode(self, f_value);
        pthread_spin_unlock(&musikernel->main_lock);
    }
    else if(!strcmp(a_key, EN_CONFIGURE_KEY_OS)) //Open Song
    {
        t_key_value_pair * f_kvp = g_kvp_get(a_value);
        int f_first_open = atoi(f_kvp->key);
        v_en_open_project(f_first_open);
    }
    else if(!strcmp(a_key, EN_CONFIGURE_KEY_TEMPO)) //Change tempo
    {
        pthread_spin_lock(&musikernel->main_lock);
        v_en_set_tempo(self, atof(a_value));
        pthread_spin_unlock(&musikernel->main_lock);
        //To reload audio items when tempo changed
        //g_en_song_get(self);
    }
    else if(!strcmp(a_key, EN_CONFIGURE_KEY_SOLO)) //Set track solo
    {
        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 2,
                PYDAW_TINY_STRING);
        int f_track_num = atoi(f_val_arr->array[0]);
        int f_mode = atoi(f_val_arr->array[1]);
        assert(f_mode == 0 || f_mode == 1);

        pthread_spin_lock(&musikernel->main_lock);

        self->track_pool[f_track_num]->solo = f_mode;
        //self->track_pool[f_track_num]->period_event_index = 0;

        v_en_set_is_soloed(self);

        pthread_spin_unlock(&musikernel->main_lock);
        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, EN_CONFIGURE_KEY_MUTE)) //Set track mute
    {
        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 2,
                PYDAW_TINY_STRING);
        int f_track_num = atoi(f_val_arr->array[0]);
        int f_mode = atoi(f_val_arr->array[1]);
        assert(f_mode == 0 || f_mode == 1);
        pthread_spin_lock(&musikernel->main_lock);

        self->track_pool[f_track_num]->mute = f_mode;
        //self->track_pool[f_track_num]->period_event_index = 0;

        pthread_spin_unlock(&musikernel->main_lock);
        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, EN_CONFIGURE_KEY_PLUGIN_INDEX))
    {
        t_1d_char_array * f_val_arr = c_split_str(a_value, '|', 5,
                PYDAW_TINY_STRING);
        int f_track_num = atoi(f_val_arr->array[0]);
        int f_index = atoi(f_val_arr->array[1]);
        int f_plugin_index = atoi(f_val_arr->array[2]);
        int f_plugin_uid = atoi(f_val_arr->array[3]);
        int f_power = atoi(f_val_arr->array[4]);

        t_pytrack * f_track = edmnext->track_pool[f_track_num];

        v_pydaw_set_plugin_index(
            f_track, f_index, f_plugin_index, f_plugin_uid, f_power, 1);

        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, EN_CONFIGURE_KEY_UPDATE_SEND))
    {
        v_en_update_track_send(self, 1);
    }
    else if(!strcmp(a_key, EN_CONFIGURE_KEY_SET_OVERDUB_MODE))
    {
        int f_bool = atoi(a_value);
        assert(f_bool == 0 || f_bool == 1);
        pthread_spin_lock(&musikernel->main_lock);
        self->overdub_mode = f_bool;
        pthread_spin_unlock(&musikernel->main_lock);
    }
    else if(!strcmp(a_key, EN_CONFIGURE_KEY_GLUE_AUDIO_ITEMS))
    {
        t_pydaw_line_split * f_val_arr = g_split_line('|', a_value);
        char * f_path = f_val_arr->str_arr[0];  //Don't free this
        int f_region_index = atoi(f_val_arr->str_arr[1]);
        int f_start_bar = atoi(f_val_arr->str_arr[2]);
        int f_end_bar = atoi(f_val_arr->str_arr[3]);
        int f_i = 0;
        while(f_i < PYDAW_MAX_AUDIO_ITEM_COUNT)
        {
            self->audio_glue_indexes[f_i] = 0;
            ++f_i;
        }

        f_i = 4;
        while(f_i < f_val_arr->count)
        {
            int f_index = atoi(f_val_arr->str_arr[f_i]);
            self->audio_glue_indexes[f_index] = 1;
            ++f_i;
        }

        v_en_offline_render(self, f_region_index, f_start_bar,
                f_region_index, f_end_bar, f_path, 1, 1);

        v_free_split_line(f_val_arr);

    }
    else if(!strcmp(a_key, EN_CONFIGURE_KEY_PANIC))
    {
        pthread_spin_lock(&musikernel->main_lock);
        musikernel->is_offline_rendering = 1;
        pthread_spin_unlock(&musikernel->main_lock);

        v_en_panic(self);

        pthread_spin_lock(&musikernel->main_lock);
        musikernel->is_offline_rendering = 0;
        pthread_spin_unlock(&musikernel->main_lock);

    }
    else if(!strcmp(a_key, EN_CONFIGURE_KEY_SET_POS))
    {
        if(musikernel->playback_mode != 0)
        {
            return;
        }
        t_1d_char_array * f_val_arr =
            c_split_str(a_value, '|', 2, PYDAW_TINY_STRING);
        int f_region = atoi(f_val_arr->array[0]);
        int f_bar = atoi(f_val_arr->array[1]);

        pthread_spin_lock(&musikernel->main_lock);
        v_en_set_playback_cursor(self, f_region, f_bar);
        pthread_spin_unlock(&musikernel->main_lock);

        g_free_1d_char_array(f_val_arr);
    }
    else if(!strcmp(a_key, EN_CONFIGURE_KEY_MIDI_DEVICE))
    {
        t_pydaw_line_split * f_val_arr = g_split_line('|', a_value);
        int f_on = atoi(f_val_arr->str_arr[0]);
        int f_device = atoi(f_val_arr->str_arr[1]);
        int f_output = atoi(f_val_arr->str_arr[2]);
        v_free_split_line(f_val_arr);

        pthread_spin_lock(&musikernel->main_lock);

        v_en_set_midi_device(f_on, f_device, f_output);

        pthread_spin_unlock(&musikernel->main_lock);
    }
    else
    {
        printf("Unknown configure message key: %s, value %s\n", a_key, a_value);
    }
}

#endif	/* EDMNEXT_H */

