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

#ifndef INTERPOLATE_LINEAR_H
#define	INTERPOLATE_LINEAR_H

#include "lmalloc.h"

#ifdef	__cplusplus
extern "C" {
#endif

inline float f_linear_interpolate(float, float, float);
inline float f_linear_interpolate_arr(float[],float);
inline float f_linear_interpolate_arr_wrap(float[],int,float);
float f_linear_interpolate_ptr_wrap(float*, int, float);
inline float f_linear_interpolate_ptr(float*, float);
inline float f_linear_interpolate_ptr_ifh(float * a_table, int a_whole_number,
        float a_frac);

#ifdef	__cplusplus
}
#endif


/* inline float f_linear_interpolate(
 * float a_a, //item 0
 * float a_b, //item 1
 * float a_position)  //position between the 2, range:  0 to 1
 */
inline float f_linear_interpolate(float a_a, float a_b, float a_position)
{
    return (((a_a - a_b) * a_position) + a_b);
}

/* inline float f_linear_interpolate_arr(
 * float a_table[], //an array of floats
 * float a_ptr, //the position in a_table to interpolate
 * t_lin_interpolater * a_lin)
 *
 * You will typically want to use f_linear_interpolate_arr_wrap instead,
 * unless you already know ahead of time
 * that you either won't be outside the bounds of your table, or else that
 * wrapping is not acceptable behavior
 */
inline float f_linear_interpolate_arr(float a_table[], float a_ptr)
{
    int int_pos = (int)a_ptr;
    int int_pos_plus_1 = int_pos + 1;
    float pos = a_ptr - int_pos;

    return ((a_table[int_pos] - a_table[int_pos_plus_1]) *
            pos) + a_table[int_pos_plus_1];
}

/* inline float f_linear_interpolate_arr_wrap(
 * float a_table[], //an array of floats
 * int a_table_size, //the size of a_table
 * float a_ptr)  //The position on the table you are interpolating
 *
 * example:
 * //interpolates halfway between a_table[5] and a_table[6]
 * f_linear_interpolate_arr_wrap(a_table[], 10, 5.5);
 *
 * This function wraps if a_ptr exceeds a_table_size or is less than 0.
 */
inline float f_linear_interpolate_arr_wrap(float a_table[], int a_table_size,
        float a_ptr)
{
    int int_pos = (int)a_ptr;
    int int_pos_plus_1 = int_pos + 1;

    if(int_pos_plus_1 >= a_table_size)
    {
        int_pos_plus_1 = 0;
    }

    float pos = a_ptr - int_pos;

    return (((a_table[int_pos]) - (a_table[int_pos_plus_1])) *
            pos) + (a_table[int_pos_plus_1]);
}

/* float f_linear_interpolate_ptr_wrap(
 * float * a_table,
 * int a_table_size,
 * float a_ptr,
 * )
 *
 * This method uses a pointer instead of an array the float* must be malloc'd
 * to (sizeof(float) * a_table_size)
 */
float f_linear_interpolate_ptr_wrap(float * a_table, int a_table_size,
        float a_ptr)
{
    int int_pos = (int)a_ptr;
    int int_pos_plus_1 = int_pos + 1;

    if(int_pos >= a_table_size)
    {
        int_pos -= a_table_size;
    }

    if(int_pos_plus_1 >= a_table_size)
    {
        int_pos_plus_1 -= a_table_size;
    }

    if(int_pos < 0)
    {
        int_pos += a_table_size;
    }

    if(int_pos_plus_1 < 0)
    {
        int_pos_plus_1 += a_table_size;
    }

    float pos = a_ptr - int_pos;

    return (((a_table[int_pos]) - (a_table[int_pos_plus_1])) *
            pos) + (a_table[int_pos_plus_1]);
}

/* inline float f_linear_interpolate_ptr_wrap(
 * float * a_table,
 * float a_ptr,
 * )
 *
 * This method uses a pointer instead of an array the float* must be malloc'd
 * to (sizeof(float) * a_table_size)
 *
 * THIS DOES NOT CHECK THAT YOU PROVIDED A VALID POSITION
 */
inline float f_linear_interpolate_ptr(float * a_table, float a_ptr)
{
    int int_pos = (int)a_ptr;
    int int_pos_plus_1 = int_pos + 1;

    float pos = a_ptr - int_pos;

    return (((a_table[int_pos]) - (a_table[int_pos_plus_1])) *
            pos) + (a_table[int_pos_plus_1]);
}

/* inline float f_linear_interpolate_ptr_ifh(
 * float * a_table,
 * int a_table_size,
 * int a_whole_number,
 * float a_frac,
 * )
 *
 * For use with the read_head type in Euphoria Sampler
 */
inline float f_linear_interpolate_ptr_ifh(float * a_table, int a_whole_number,
        float a_frac)
{
    int int_pos = a_whole_number;
    int int_pos_plus_1 = int_pos + 1;

    float pos = a_frac;

    return (((a_table[int_pos]) - (a_table[int_pos_plus_1])) *
            pos) + (a_table[int_pos_plus_1]);
}

#endif	/* INTERPOLATE_LINEAR_H */

