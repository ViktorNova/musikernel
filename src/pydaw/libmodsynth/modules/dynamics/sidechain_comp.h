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

#ifndef SIDECHAIN_COMP_H
#define	SIDECHAIN_COMP_H

#include "../../lib/amp.h"
#include "../../lib/lms_math.h"
#include "../filter/svf.h"
#include "../signal_routing/audio_xfade.h"

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    float pitch, ratio, thresh, wet, speed, output0, output1;
    t_state_variable_filter filter;
    t_audio_xfade xfade;
}t_scc_sidechain_comp;

void g_scc_init(t_scc_sidechain_comp*, float);
void v_scc_set(t_scc_sidechain_comp*, float, float, float, float);
void v_scc_run_comp(t_scc_sidechain_comp*, float, float, float, float);

#ifdef	__cplusplus
}
#endif


void g_scc_init(t_scc_sidechain_comp * self, float a_sr)
{
    g_svf_init(&self->filter, a_sr);
    v_svf_set_res(&self->filter, -15.0f);
    g_axf_init(&self->xfade, -3.0f);
    self->speed = 999.99f;
    self->pitch = 999.99f;
    self->ratio = 999.99f;
    self->thresh = 999.99f;
    self->wet = 999.99f;
    self->output0 = 0.0f;
    self->output1 = 0.0f;
}

void v_scc_set(t_scc_sidechain_comp *self, float a_thresh, float a_ratio,
    float a_speed, float a_wet)
{
    self->thresh = a_thresh;
    self->ratio = a_ratio;

    if(self->speed != a_speed)
    {
        self->speed = a_speed;
        v_svf_set_cutoff_base(&self->filter, a_speed);
        v_svf_set_cutoff(&self->filter);
    }

    if(self->wet != a_wet)
    {
        self->wet = a_wet;
        v_axf_set_xfade(&self->xfade, a_wet);
    }
}

void v_scc_run_comp(t_scc_sidechain_comp *self,
    float a_input0, float a_input1, float a_output0, float a_output1)
{
    float f_gain;

    float f_env = v_svf_run_4_pole_lp(
        &self->filter, f_lms_max(f_lms_abs(a_input0), f_lms_abs(a_input1)));

    f_gain = self->thresh - f_linear_to_db_fast(f_env);


    if(f_gain < 0.0f)
    {
        f_gain *= self->ratio;
        f_gain = f_db_to_linear_fast(f_gain);
        self->output0 = f_axf_run_xfade(
            &self->xfade, a_output0, a_output0 * f_gain);
        self->output1 = f_axf_run_xfade(
            &self->xfade, a_output1, a_output1 * f_gain);
    }
    else
    {
        self->output0 = a_output0;
        self->output1 = a_output1;
    }
}

#endif	/* SIDECHAIN_COMP_H */

