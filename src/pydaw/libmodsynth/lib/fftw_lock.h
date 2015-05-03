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

#ifndef FFTW_LOCK_H
#define	FFTW_LOCK_H

#include <pthread.h>
#include <fftw3.h>

pthread_mutex_t FFTW_LOCK;
int FFTW_LOCK_INIT = 0;

fftwf_plan g_fftwf_plan_dft_r2c_1d(
int a_size, float * a_in, fftwf_complex * a_out, unsigned a_flags)
{
    fftwf_plan f_result;

    if(!FFTW_LOCK_INIT)
    {
        pthread_mutex_init(&FFTW_LOCK, NULL);
        FFTW_LOCK_INIT = 1;
    }

    pthread_mutex_lock(&FFTW_LOCK);
    f_result = fftwf_plan_dft_r2c_1d(a_size, a_in, a_out, a_flags);
    pthread_mutex_unlock(&FFTW_LOCK);

    return f_result;
}

#endif	/* FFTW_LOCK_H */

