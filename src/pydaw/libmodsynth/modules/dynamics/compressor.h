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

#ifndef COMPRESSOR_H
#define	COMPRESSOR_H

#include "env_follower.h"
#include "../../lib/amp.h"

#ifdef	__cplusplus
extern "C" {
#endif

typedef struct
{
    float thresh, ratio, ratio_recip, knee, knee_thresh,
        gain, gain_lin, output0, output1;
    t_enf2_env_follower env_follower;
}t_cmp_compressor;


#ifdef	__cplusplus
}
#endif

void g_cmp_init(t_cmp_compressor * self, float a_sr)
{
    self->thresh = 0.0f;
    self->knee_thresh = 0.0f;
    self->ratio = 1.0f;
    self->knee = 0.0f;
    self->gain = 0.0f;
    self->gain_lin = 1.0f;
    self->output0 = 0.0f;
    self->output1 = 0.0f;
    g_enf_init(&self->env_follower, a_sr);
}

void v_cmp_set(t_cmp_compressor * self, float thresh, float ratio,
        float knee, float attack, float release, float gain)
{
    v_enf_set(&self->env_follower, attack, release);

    self->knee = knee;
    self->thresh = thresh;
    self->knee_thresh = thresh - knee;

    if(self->ratio != ratio)
    {
        self->ratio = ratio;
        self->ratio_recip = (1.0f - (1.0f / ratio)) * -1.0f;
    }

    if(self->gain != gain)
    {
        self->gain = gain;
        self->gain_lin = f_db_to_linear_fast(gain);
    }
}

void v_cmp_run(t_cmp_compressor * self, float a_in0, float a_in1)
{
    float f_max = f_lms_max(f_lms_abs(a_in0), f_lms_abs(a_in1));
    v_enf_run(&self->env_follower, f_max);
    float f_db = f_linear_to_db_fast(self->env_follower.envelope);

    if(f_db > self->thresh)
    {
        float f_vol =
            f_db_to_linear_fast((f_db - self->thresh) * self->ratio_recip);
        self->output0 = a_in0 * f_vol;
        self->output1 = a_in1 * f_vol;
    }
    else if(f_db > self->knee_thresh)
    {
        float f_diff = (f_db - self->knee_thresh);
        float f_percent = f_diff / self->knee;
        float f_ratio = ((self->ratio - 1.0f) * f_percent) + 1.0f;
        float f_vol = f_db_to_linear_fast(f_diff / f_ratio);
        self->output0 = a_in0 * f_vol;
        self->output1 = a_in1 * f_vol;
    }
    else
    {
        self->output0 = a_in0;
        self->output1 = a_in1;
    }
}


#endif	/* COMPRESSOR_H */

