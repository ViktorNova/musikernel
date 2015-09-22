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

#ifndef MULTI_DIST_H
#define	MULTI_DIST_H

#include "clipper.h"
#include "foldback.h"
#include "../signal_routing/audio_xfade.h"


#ifdef	__cplusplus
extern "C" {
#endif

typedef struct{
    t_clipper clipper1;
    t_audio_xfade dist_dry_wet;
}t_mds_multidist;

#ifdef	__cplusplus
}
#endif

typedef float (*fp_multi_dist)(t_mds_multidist*, float, float);

float f_multi_dist_off(t_mds_multidist* self, float a_sample, float a_out)
{
    return a_sample;
}

float f_multi_dist_clip(t_mds_multidist* self, float a_sample, float a_out)
{
    return f_axf_run_xfade(&self->dist_dry_wet, a_sample,
        f_clp_clip(&self->clipper1, a_sample) * a_out);
}

float f_multi_dist_foldback(t_mds_multidist* self, float a_sample, float a_out)
{
    return f_axf_run_xfade(&self->dist_dry_wet, a_sample,
        f_fbk_mono(a_sample) * a_out);
}

__thread fp_multi_dist MULTI_DIST_FP[] = {
    f_multi_dist_off, f_multi_dist_clip, f_multi_dist_foldback
};

fp_multi_dist g_mds_get_fp(int index)
{
    assert(index >= 0 && index <= 2);
    return MULTI_DIST_FP[index];
}

void g_mds_init(t_mds_multidist * self)
{
    g_clp_init(&self->clipper1);
    g_axf_init(&self->dist_dry_wet, -3.0f);
}

#endif	/* MULTI_DIST_H */

