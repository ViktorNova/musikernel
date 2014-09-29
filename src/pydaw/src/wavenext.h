/*
 * File:   wavenext.h
 * Author: userbuntu
 *
 * Created on September 28, 2014, 6:30 PM
 */

#ifndef WAVENEXT_H
#define	WAVENEXT_H

#include "musikernel.h"

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    t_wav_pool_item * ab_wav_item;
    t_pydaw_audio_item * ab_audio_item;
    t_pytrack * track_pool[1];
}t_wavenext;

void v_pydaw_set_ab_file(t_wavenext * self, const char * a_file);
void v_pydaw_set_wave_editor_item(t_wavenext * self, const char * a_string);
inline void v_pydaw_run_wave_editor(t_wavenext * self,
    int sample_count, float **output);

#ifdef	__cplusplus
}
#endif

t_wavenext * wavenext;

void g_wavenext_get()
{
    lmalloc((void**)&wavenext, sizeof(t_wavenext));
    wavenext->ab_wav_item = 0;
    wavenext->ab_audio_item = g_pydaw_audio_item_get(musikernel->sample_rate);
    int f_i = 0;
    while(f_i < 1)
    {
        wavenext->track_pool[f_i] = g_pytrack_get(f_i, musikernel->sample_rate);
        f_i++;
    }
}

void v_wn_set_playback_mode(t_wavenext * self, int a_mode, int a_lock)
{
    switch(a_mode)
    {
        case 0: //stop
        {
            int f_i = 0;
            t_pytrack * f_track;

            if(a_lock)
            {
                pthread_spin_lock(&musikernel->main_lock);
            }

            musikernel->playback_mode = a_mode;

            f_i = 0;

            t_pydaw_plugin * f_plugin;

            while(f_i < 1)
            {
                int f_i2 = 0;
                f_track = self->track_pool[f_i];

                f_track->period_event_index = 0;

                while(f_i2 < MAX_PLUGIN_TOTAL_COUNT)
                {
                    f_plugin = f_track->plugins[f_i2];
                    if(f_plugin)
                    {
                        f_plugin->descriptor->on_stop(f_plugin->PYFX_handle);
                    }
                    f_i2++;
                }

                f_track->item_event_index = 0;

                f_i++;
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

            if(wavenext->ab_wav_item)
            {
                musikernel->is_ab_ing = musikernel->ab_mode;
                if(musikernel->is_ab_ing)
                {
                    v_ifh_retrigger(
                        wavenext->ab_audio_item->sample_read_head,
                        wavenext->ab_audio_item->sample_start_offset);
                    v_adsr_retrigger(wavenext->ab_audio_item->adsr);
                    v_svf_reset(wavenext->ab_audio_item->lp_filter);
                }
            }

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

            musikernel->playback_mode = a_mode;

            if(a_lock)
            {
                pthread_spin_unlock(&musikernel->main_lock);
            }
            break;
    }
}

void v_pydaw_we_export(t_wavenext * self, const char * a_file_out)
{
    pthread_spin_lock(&musikernel->main_lock);
    musikernel->is_offline_rendering = 1;
    pthread_spin_unlock(&musikernel->main_lock);

    musikernel->input_buffers_active = 0;

    long f_size = 0;
    long f_block_size = (musikernel->sample_count);

    float * f_output = (float*)malloc(sizeof(float) * (f_block_size * 2));

    float ** f_buffer = (float**)malloc(sizeof(float) * 2);

    int f_i = 0;
    while(f_i < 2)
    {
        f_buffer[f_i] = (float*)malloc(sizeof(float) * f_block_size);
        f_i++;
    }

    int f_old_ab_mode = musikernel->ab_mode;
    musikernel->ab_mode = 1;

    v_wn_set_playback_mode(self, PYDAW_PLAYBACK_MODE_PLAY, 0);

    printf("\nOpening SNDFILE with sample rate %f\n",
            musikernel->sample_rate);

    SF_INFO f_sf_info;
    f_sf_info.channels = 2;
    f_sf_info.format = SF_FORMAT_WAV | SF_FORMAT_FLOAT;
    f_sf_info.samplerate = (int)(musikernel->sample_rate);

    SNDFILE * f_sndfile = sf_open(a_file_out, SFM_WRITE, &f_sf_info);

    printf("\nSuccessfully opened SNDFILE\n\n");

    clock_t f_start = clock();

    while((self->ab_audio_item->sample_read_head->whole_number) <
            (self->ab_audio_item->sample_end_offset))
    {
        int f_i = 0;
        f_size = 0;

        while(f_i < f_block_size)
        {
            f_buffer[0][f_i] = 0.0f;
            f_buffer[1][f_i] = 0.0f;
            f_i++;
        }

        v_pydaw_run_wave_editor(self, f_block_size, f_buffer);

        f_i = 0;
        /*Interleave the samples...*/
        while(f_i < f_block_size)
        {
            f_output[f_size] = f_buffer[0][f_i];
            f_size++;
            f_output[f_size] = f_buffer[1][f_i];
            f_size++;
            f_i++;
        }

        sf_writef_float(f_sndfile, f_output, f_block_size);
    }

    v_pydaw_print_benchmark("v_pydaw_offline_render ", f_start);
    printf("f_size = %ld\n", f_size);

    v_wn_set_playback_mode(self, PYDAW_PLAYBACK_MODE_OFF, 0);

    sf_close(f_sndfile);

    free(f_buffer[0]);
    free(f_buffer[1]);
    free(f_output);

    char f_tmp_finished[1024];

    sprintf(f_tmp_finished, "%s.finished", a_file_out);

    v_pydaw_write_to_file(f_tmp_finished, "finished");

    pthread_spin_lock(&musikernel->main_lock);
    musikernel->is_offline_rendering = 0;
    pthread_spin_unlock(&musikernel->main_lock);

    musikernel->ab_mode = f_old_ab_mode;
}


void v_pydaw_set_ab_file(t_wavenext * self, const char * a_file)
{
    t_wav_pool_item * f_result = g_wav_pool_item_get(0, a_file,
            musikernel->sample_rate);

    if(i_wav_pool_item_load(f_result))
    {
        pthread_spin_lock(&musikernel->main_lock);

        t_wav_pool_item * f_old = self->ab_wav_item;
        self->ab_wav_item = f_result;

        if(!f_result)
        {
            musikernel->ab_mode = 0;
        }

        self->ab_audio_item->ratio =
                self->ab_wav_item->ratio_orig;

        pthread_spin_unlock(&musikernel->main_lock);

        if(f_old)
        {
            v_wav_pool_item_free(f_old);
        }
    }
    else
    {
        printf("i_wav_pool_item_load failed in v_pydaw_set_ab_file\n");
    }
}


void v_pydaw_set_wave_editor_item(t_wavenext * self,
        const char * a_val)
{
    t_2d_char_array * f_current_string = g_get_2d_array(PYDAW_MEDIUM_STRING);
    sprintf(f_current_string->array, "%s", a_val);
    t_pydaw_audio_item * f_old = self->ab_audio_item;
    t_pydaw_audio_item * f_result = g_audio_item_load_single(
            musikernel->sample_rate, f_current_string, 0, 0,
            self->ab_wav_item);

    pthread_spin_lock(&musikernel->main_lock);
    self->ab_audio_item = f_result;
    pthread_spin_unlock(&musikernel->main_lock);

    g_free_2d_char_array(f_current_string);
    if(f_old)
    {
        v_pydaw_audio_item_free(f_old);
    }
}


inline void v_pydaw_run_wave_editor(t_wavenext * self,
        int sample_count, float **output)
{
    t_pydaw_plugin * f_plugin;
    int f_global_track_num = 0;
    t_pytrack * f_track = self->track_pool[f_global_track_num];
    int f_i = 0;

    while(f_i < sample_count)
    {
        if((self->ab_audio_item->sample_read_head->whole_number) >=
            (self->ab_audio_item->sample_end_offset))
        {
            output[0][f_i] = 0.0f;
            output[1][f_i] = 0.0f;
        }
        else
        {
            v_adsr_run_db(self->ab_audio_item->adsr);
            v_pydaw_audio_item_set_fade_vol(self->ab_audio_item);

            if(self->ab_wav_item->channels == 1)
            {
                float f_tmp_sample = f_cubic_interpolate_ptr_ifh(
                (self->ab_wav_item->samples[0]),
                (self->ab_audio_item->sample_read_head->
                    whole_number),
                (self->ab_audio_item->sample_read_head->fraction)) *
                (self->ab_audio_item->adsr->output) *
                (self->ab_audio_item->vol_linear) *
                (self->ab_audio_item->fade_vol);

                output[0][f_i] = f_tmp_sample;
                output[1][f_i] = f_tmp_sample;
            }
            else if(self->ab_wav_item->channels > 1)
            {
                output[0][f_i] = f_cubic_interpolate_ptr_ifh(
                (self->ab_wav_item->samples[0]),
                (self->ab_audio_item->sample_read_head->
                    whole_number),
                (self->ab_audio_item->sample_read_head->fraction)) *
                (self->ab_audio_item->adsr->output) *
                (self->ab_audio_item->vol_linear) *
                (self->ab_audio_item->fade_vol);

                output[1][f_i] = f_cubic_interpolate_ptr_ifh(
                (self->ab_wav_item->samples[1]),
                (self->ab_audio_item->sample_read_head->whole_number),
                (self->ab_audio_item->sample_read_head->fraction)) *
                (self->ab_audio_item->adsr->output) *
                (self->ab_audio_item->vol_linear) *
                (self->ab_audio_item->fade_vol);
            }

            v_ifh_run(self->ab_audio_item->sample_read_head,
                    self->ab_audio_item->ratio);

            if(musikernel->playback_mode != PYDAW_PLAYBACK_MODE_PLAY &&
                self->ab_audio_item->adsr->stage < ADSR_STAGE_RELEASE)
            {
                v_adsr_release(self->ab_audio_item->adsr);
            }
        }
        f_i++;
    }

    float ** f_buff = f_track->buffers;

    f_i = 0;
    while(f_i < sample_count)
    {
        f_buff[0][f_i] = output[0][f_i];
        f_buff[1][f_i] = output[1][f_i];
        f_i++;
    }

    f_i = 0;
    while(f_i < MAX_PLUGIN_COUNT)
    {
        f_plugin = f_track->plugins[f_i];
        if(f_plugin)
        {
            f_plugin->descriptor->run_replacing(
                f_plugin->PYFX_handle, sample_count,
                f_track->event_buffer, f_track->period_event_index,
                f_plugin->atm_buffer, f_plugin->atm_count,
                f_track->extern_midi, *f_track->extern_midi_count);
        }
        f_i++;
    }

    f_i = 0;
    while(f_i < sample_count)
    {
        output[0][f_i] = f_buff[0][f_i];
        output[1][f_i] = f_buff[1][f_i];
        f_i++;
    }

    v_pkm_run(f_track->peak_meter, f_buff[0], f_buff[1],
        musikernel->sample_count);
}


#endif	/* WAVENEXT_H */

