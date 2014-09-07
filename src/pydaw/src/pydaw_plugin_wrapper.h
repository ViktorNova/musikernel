/*
This file is part of the PyDAW project, Copyright PyDAW Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
*/

#ifndef PYDAW_PLUGIN_H
#define	PYDAW_PLUGIN_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../include/pydaw_plugin.h"
#include "pydaw.h"
#include <stdlib.h>
#include <assert.h>

#include "../plugins/modulex/synth.c"
#include "../plugins/euphoria/synth.c"
#include "../plugins/way_v/synth.c"
#include "../plugins/ray_v/synth.c"


typedef struct
{
    PYFX_Handle PYFX_handle;
    PYFX_Descriptor_Function descfn;
    PYFX_Descriptor *descriptor;
    int mute;
    int solo;
    int power;
}t_pydaw_plugin;


t_pydaw_plugin * g_pydaw_plugin_get(int a_sample_rate, int a_index,
        fp_get_wavpool_item_from_host a_host_wavpool_func,
        int a_plugin_uid, fp_queue_message a_queue_func)
{
    t_pydaw_plugin * f_result = (t_pydaw_plugin*)malloc(sizeof(t_pydaw_plugin));

    switch(a_index)
    {
        case 1:
            f_result->descfn =
                    (PYFX_Descriptor_Function)euphoria_PYFX_descriptor;
            break;
        case 2:
            f_result->descfn =
                    (PYFX_Descriptor_Function)rayv_PYFX_descriptor;
            break;
        case 3:
            f_result->descfn =
                    (PYFX_Descriptor_Function)wayv_PYFX_descriptor;
            break;
        case 4:
            f_result->descfn =
                    (PYFX_Descriptor_Function)modulex_PYFX_descriptor;
            break;
        default:
            assert(0);
    }

    f_result->descriptor = f_result->descfn(0);

    f_result->PYFX_handle = f_result->descriptor->instantiate(
            f_result->descriptor, a_sample_rate,
            a_host_wavpool_func, a_plugin_uid, a_queue_func);

    f_result->solo = 0;
    f_result->mute = 0;
    f_result->power = 1;

    return f_result;
}

void v_free_pydaw_plugin(t_pydaw_plugin * a_plugin)
{
    if(a_plugin)
    {
        if (a_plugin->descriptor->cleanup)
        {
            a_plugin->descriptor->cleanup(a_plugin->PYFX_handle);
        }

        free(a_plugin);
    }
    else
    {
        printf("Error, attempted to free NULL plugin "
                "with v_free_pydaw_plugin()\n");
    }
}


#ifdef	__cplusplus
}
#endif

#endif	/* PYDAW_PLUGIN_H */

