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

#ifndef PYDAW_REVERB_H
#define	PYDAW_REVERB_H

#define PYDAW_REVERB_DIFFUSER_COUNT 5
#define PYDAW_REVERB_TAP_COUNT 12


#include "../../lib/amp.h"
#include "../../lib/lmalloc.h"
#include "../../lib/pitch_core.h"
#include "../filter/comb_filter.h"
#include "../filter/svf.h"
#include "../oscillator/lfo_simple.h"

#ifdef  __cplusplus
extern "C" {
#endif

typedef struct
{
    t_comb_filter tap;
    float pitch;
}t_rvb_tap;

typedef struct
{
    t_state_variable_filter diffuser;
    float pitch;
}t_rvb_diffuser;

typedef struct
{
    float output;
    float feedback;
    t_lfs_lfo lfo;
    t_state_variable_filter lp;
    t_state_variable_filter hp;
    float wet_linear;
    t_rvb_tap taps[PYDAW_REVERB_TAP_COUNT];
    t_rvb_diffuser diffusers[PYDAW_REVERB_DIFFUSER_COUNT];
    float * predelay_buffer;
    int predelay_counter;
    int predelay_size;
    float color;
    float wet;
    float time;
    float volume_factor;
    float last_predelay;
    float sr;
    float hp_cutoff;
} t_rvb_reverb;

t_rvb_reverb * g_rvb_reverb_get(float);
void v_rvb_reverb_set(t_rvb_reverb *, float, float, float, float, float);
inline void v_rvb_reverb_run(t_rvb_reverb *, float, float);


void v_rvb_reverb_set(t_rvb_reverb * a_reverb, float a_time, float a_wet,
        float a_color, float a_predelay, float a_hp_cutoff)
{
    if(unlikely(a_time != a_reverb->time))
    {
        int f_i;
        float f_base = 30.0f - (a_time * 25.0f);
        float f_factor = 1.4f + (a_time * 0.8f);

        a_reverb->feedback = a_time + -1.05f;
        v_lfs_set(&a_reverb->lfo, 1.0f - (a_time * 0.9f));

        for(f_i = 0; f_i < PYDAW_REVERB_TAP_COUNT; ++f_i)
        {
            a_reverb->taps[f_i].pitch = f_base + (((float)f_i) * f_factor);
            v_cmb_set_all(&a_reverb->taps[f_i].tap, 0.0f, a_reverb->feedback,
                a_reverb->taps[f_i].pitch);
        }

        a_reverb->time = a_time;
    }

    if(unlikely(a_wet != a_reverb->wet))
    {
        a_reverb->wet = a_wet;
        a_reverb->wet_linear =  a_wet * (a_reverb->volume_factor);
    }

    if(unlikely(a_color != a_reverb->color))
    {
        a_reverb->color = a_color;
        v_svf_set_cutoff_base(&a_reverb->lp, a_color);
        v_svf_set_cutoff(&a_reverb->lp);
    }

    if(unlikely(a_reverb->last_predelay != a_predelay))
    {
        a_reverb->last_predelay = a_predelay;
        a_reverb->predelay_size = (int)(a_reverb->sr * a_predelay);
        if(a_reverb->predelay_counter >= a_reverb->predelay_size)
        {
            a_reverb->predelay_counter = 0;
        }
    }

    if(unlikely(a_reverb->hp_cutoff != a_hp_cutoff))
    {
        v_svf_set_cutoff_base(&a_reverb->hp, a_hp_cutoff);
        v_svf_set_cutoff(&a_reverb->hp);
        a_reverb->hp_cutoff = a_hp_cutoff;
    }
}

inline void v_rvb_reverb_run(t_rvb_reverb * a_reverb, float a_input0,
        float a_input1)
{
    int f_i;

    a_reverb->output *= 0.02f;
    v_lfs_run(&a_reverb->lfo);
    float f_lfo_diff = a_reverb->lfo.output * 2.0f;

    float f_tmp_sample = v_svf_run_2_pole_lp(&a_reverb->lp,
            (a_input0 + a_input1));
    f_tmp_sample = v_svf_run_2_pole_hp(&a_reverb->hp, f_tmp_sample);
    f_tmp_sample *= (a_reverb->wet_linear);

    for(f_i = 0; f_i < PYDAW_REVERB_TAP_COUNT; ++f_i)
    {
        v_cmb_run(&a_reverb->taps[f_i].tap, f_tmp_sample);
        a_reverb->output += (a_reverb->taps[f_i].tap.output_sample);
    }

    for(f_i = 0; f_i < PYDAW_REVERB_DIFFUSER_COUNT; ++f_i)
    {
        v_svf_set_cutoff_base(&a_reverb->diffusers[f_i].diffuser,
            a_reverb->diffusers[f_i].pitch + f_lfo_diff);
        v_svf_set_cutoff(&a_reverb->diffusers[f_i].diffuser);
        a_reverb->output =
            v_svf_run_2_pole_allpass(&a_reverb->diffusers[f_i].diffuser,
            a_reverb->output);
    }

    a_reverb->predelay_buffer[(a_reverb->predelay_counter)] = a_reverb->output;
    ++a_reverb->predelay_counter;
    if(unlikely(a_reverb->predelay_counter >= a_reverb->predelay_size))
    {
        a_reverb->predelay_counter = 0;
    }

    a_reverb->output = a_reverb->predelay_buffer[(a_reverb->predelay_counter)];
}

void v_rvb_panic(t_rvb_reverb * self)
{
    register int f_i, f_i2;
    float * f_tmp;
    int f_count;
    int f_pre_count = self->sr + 5000;
    for(f_i = 0; f_i < f_pre_count; ++f_i)
    {
        self->predelay_buffer[f_i] = 0.0f;
    }

    for(f_i = 0; f_i < PYDAW_REVERB_TAP_COUNT; ++f_i)
    {
        f_tmp = self->taps[f_i].tap.input_buffer;
        f_count = self->taps[f_i].tap.buffer_size;
        for(f_i2 = 0; f_i2 < f_count; ++f_i2)
        {
            f_tmp[f_i2] = 0.0f;
        }
    }
}

void g_rvb_reverb_init(t_rvb_reverb * f_result, float a_sr)
{
    int f_i;

    f_result->color = 1.0f;
    f_result->time = 0.5f;
    f_result->wet = 0.0f;
    f_result->wet_linear = 0.0f;
    f_result->hp_cutoff = -12345.0f;

    f_result->sr = a_sr;

    for(f_i = 0; f_i < PYDAW_REVERB_DIFFUSER_COUNT; ++f_i)
    {
        f_result->diffusers[f_i].pitch = 33.0f + (((float)f_i) * 7.0f);
    }

    f_result->output = 0.0f;

    g_lfs_init(&f_result->lfo, a_sr);
    v_lfs_sync(&f_result->lfo, 0.0f, 1);

    g_svf_init(&f_result->hp, a_sr);
    v_svf_set_res(&f_result->hp, -36.0f);
    v_svf_set_cutoff_base(&f_result->hp, 60.0f);
    v_svf_set_cutoff(&f_result->hp);

    g_svf_init(&f_result->lp, a_sr);
    v_svf_set_res(&f_result->lp, -36.0f);

    f_result->volume_factor = (1.0f / (float)PYDAW_REVERB_DIFFUSER_COUNT) * 0.5;

    f_i = 0;

    while(f_i < PYDAW_REVERB_TAP_COUNT)
    {
        g_cmb_init(&f_result->taps[f_i].tap, a_sr, 1);
        ++f_i;
    }

    f_i = 0;

    while(f_i < PYDAW_REVERB_DIFFUSER_COUNT)
    {
        g_svf_init(&f_result->diffusers[f_i].diffuser, a_sr);
        v_svf_set_cutoff_base(&f_result->diffusers[f_i].diffuser,
            f_result->diffusers[f_i].pitch);
        v_svf_set_res(&f_result->diffusers[f_i].diffuser, -6.0f);
        v_svf_set_cutoff(&f_result->diffusers[f_i].diffuser);
        ++f_i;
    }

    f_result->predelay_counter = 0;
    f_result->last_predelay = -1234.0f;
    f_result->predelay_size = (int)(a_sr * 0.01f);

    hpalloc((void**)&f_result->predelay_buffer,
        sizeof(float) * (a_sr + 5000));

    f_i = 0;
    while(f_i < (a_sr + 5000))
    {
        f_result->predelay_buffer[f_i] = 0.0f;
        ++f_i;
    }

    v_rvb_reverb_set(f_result, 0.5f, 0.0f, 55.5f, 0.01f, 60.0f);
}

#ifdef	__cplusplus
}
#endif

#endif	/* PYDAW_REVERB_H */

