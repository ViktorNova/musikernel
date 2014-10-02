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

#ifndef DELAY_H
#define	DELAY_H

#ifdef	__cplusplus
extern "C" {
#endif

#include "../../lib/interpolate-linear.h"
#include "../../lib/pitch_core.h"
#include "../../lib/lmalloc.h"


    typedef struct st_delay_tap
{
    int read_head;
    int read_head_p1;
    float fraction;
    int delay_samples;
    float delay_seconds;
    float delay_beats;
    float delay_pitch;
    float delay_hz;
    float output;
}t_delay_tap;


typedef struct
{
    int write_head;
    float sample_rate;
    float tempo;
    float tempo_recip;
    int sample_count;
    float* buffer;
#ifdef DLY_DEBUG_MODE
    int debug_counter;
#endif
}t_delay_simple;


t_delay_simple * g_dly_get_delay(float, float);
t_delay_tap * g_dly_get_tap();
inline void v_dly_set_delay_seconds(t_delay_simple*,t_delay_tap*,float);
inline void v_dly_set_delay_lin(t_delay_simple*,t_delay_tap*,float);
inline void v_dly_set_delay_tempo(t_delay_simple*,t_delay_tap*,float);
inline void v_dly_set_delay_pitch(t_delay_simple*,t_delay_tap*,float);
inline void v_dly_set_delay_pitch_fast(t_delay_simple*,t_delay_tap*,float);
inline void v_dly_set_delay_hz(t_delay_simple*,t_delay_tap*,float);
inline void v_dly_run_delay(t_delay_simple*,float);
inline void v_dly_run_tap(t_delay_simple*,t_delay_tap*);
inline void v_dly_run_tap_lin(t_delay_simple*,t_delay_tap*);


/*inline void v_dly_set_delay(
 * t_delay_simple* a_dly,
 * float a_seconds //delay in seconds, typically .1 to 1
 * )
 */
inline void v_dly_set_delay_seconds(t_delay_simple* a_dly, t_delay_tap* a_tap,
        float a_seconds)
{
    if((a_tap->delay_seconds) != a_seconds)
    {
        a_tap->delay_seconds = a_seconds;
        a_tap->delay_samples = (int)((a_dly->sample_rate) * a_seconds);
    }
}

/* inline void v_dly_set_delay_lin(
 * t_delay_simple* a_dly,
 * t_delay_tap* a_tap,
 * float a_seconds
 * )
 *
 * This must be run if running the tap as linear, otherwise you will segfault
 */
inline void v_dly_set_delay_lin(t_delay_simple* a_dly, t_delay_tap* a_tap,
        float a_seconds)
{
    if((a_tap->delay_seconds) != a_seconds)
    {
        a_tap->delay_seconds = a_seconds;
        a_tap->delay_samples = (int)((a_dly->sample_rate) * a_seconds);
        a_tap->fraction = ((a_dly->sample_rate) * a_seconds) -
                (a_tap->delay_samples);
    }
}


/*inline void v_dly_set_delay_tempo(
 * t_delay_simple* a_dly,
 * t_delay_tap* a_tap,
 * float a_beats //Delay time in beats.  Typical value:  .25, .5, 1, 2....
 * )
 */
inline void v_dly_set_delay_tempo(t_delay_simple* a_dly, t_delay_tap* a_tap,
        float a_beats)
{
    if((a_tap->delay_beats) != a_beats)
    {
        a_tap->delay_beats = a_beats;
        a_tap->delay_samples = (a_dly->tempo_recip) * a_beats *
                (a_dly->sample_rate);
    }
}

/*inline void v_dly_set_delay_pitch(
 * t_delay_simple* a_dly,
 * t_delay_tap* a_tap,
 * float a_pitch)  //Pitch in MIDI note number
 *
 * This method is very slow because it calculates a more accurate result
 * that the fast method, it should only be used in things like reverbs, where
 * feedback and pitch are tightly coupled together, and
 * require accuracy.
 */
inline void v_dly_set_delay_pitch(t_delay_simple* a_dly, t_delay_tap* a_tap, float a_pitch)
{
    if((a_tap->delay_pitch) != a_pitch)
    {
        a_tap->delay_pitch = a_pitch;
        a_tap->delay_samples =
            ((a_dly->sample_rate) / (f_pit_midi_note_to_hz(a_pitch)));
    }
}



/*inline void v_dly_set_delay_pitch(
 * t_delay_simple* a_dly,
 * t_delay_tap* a_tap,
 * float a_pitch)  //Pitch in MIDI note number
 *
 * This method is very slow because it calculates a more accurate result
 * that the fast method, it should only be used in things like reverbs,
 * where feedback and pitch are tightly coupled together, and
 * require accuracy.
 */
inline void v_dly_set_delay_pitch_fast(t_delay_simple* a_dly,
        t_delay_tap* a_tap, float a_pitch)
{
    if((a_tap->delay_pitch) != a_pitch)
    {
        a_tap->delay_pitch = a_pitch;
        a_tap->delay_samples =
            ((a_dly->sample_rate) / (f_pit_midi_note_to_hz(a_pitch)));
    }
}


/*inline void v_dly_set_delay_hz(
 * t_delay_simple* a_dly,
 * t_delay_tap* a_tap,
 * float a_hz)  //Frequency in hz.  1.0f/a_hz == the delay time
 *
 */
inline void v_dly_set_delay_hz(t_delay_simple* a_dly, t_delay_tap* a_tap,
        float a_hz)
{
    if((a_tap->delay_hz) != a_hz)
    {
        a_tap->delay_hz = a_hz;
        a_tap->delay_samples = ((a_dly->sample_rate)/(a_hz));
    }
}


inline void v_dly_run_delay(t_delay_simple* a_dly,float a_input)
{
    a_dly->buffer[(a_dly->write_head)] = a_input;

    a_dly->write_head = (a_dly->write_head) + 1;
    if((a_dly->write_head) >= (a_dly->sample_count))
    {
        a_dly->write_head = 0;
    }

}

inline void v_dly_run_tap(t_delay_simple* a_dly,t_delay_tap* a_tap)
{
    a_tap->read_head = (a_dly->write_head) - (a_tap->delay_samples);

    if((a_tap->read_head) < 0)
    {
        a_tap->read_head = (a_tap->read_head) + (a_dly->sample_count);
    }

    a_tap->output = (a_dly->buffer[(a_tap->read_head)]);
}


inline void v_dly_run_tap_lin(t_delay_simple* a_dly,t_delay_tap* a_tap)
{
    a_tap->read_head = (a_dly->write_head) - (a_tap->delay_samples);

    if((a_tap->read_head) < 0)
    {
        a_tap->read_head = (a_tap->read_head) + (a_dly->sample_count);
    }

    ++a_tap->read_head_p1;

    if((a_tap->read_head_p1) >= (a_dly->sample_count))
    {
        a_tap->read_head_p1 = (a_tap->read_head_p1) - (a_dly->sample_count);
    }

    a_tap->output = f_linear_interpolate(
            a_dly->buffer[(a_tap->read_head)],
            a_dly->buffer[(a_tap->read_head_p1)], (a_tap->fraction));
}

void g_dly_init(t_delay_simple * f_result, float a_max_size, float a_sr)
{
    f_result->write_head = 0;
    f_result->sample_rate = a_sr;
    f_result->tempo = 999;
    f_result->tempo_recip = 999;
    //add 2400 samples to ensure we don't overrun our buffer
    f_result->sample_count = (int)((a_max_size * a_sr) + 2400);
    buffer_alloc((void**)&f_result->buffer,
        sizeof(float) * (f_result->sample_count));

    int f_i = 0;

    while(f_i < (f_result->sample_count))
    {
        f_result->buffer[f_i] = 0.0f;
        ++f_i;
    }
}


t_delay_simple * g_dly_get_delay(float a_max_size, float a_sr)
{
    t_delay_simple * f_result;
    lmalloc((void**)&f_result, sizeof(t_delay_simple));
    g_dly_init(f_result, a_max_size, a_sr);
    return f_result;
}



void g_dly_tap_init(t_delay_tap * f_result)
{
    f_result->read_head = 0;
    f_result->delay_samples = 0;
    f_result->delay_seconds  = 0.0f;
    f_result->delay_beats = 0.0f;
    f_result->output = 0.0f;
    f_result->delay_pitch = 20.0123f;
    f_result->delay_hz = 20.2021f;
}

t_delay_tap * g_dly_get_tap()
{
    t_delay_tap * f_result;
    lmalloc((void**)&f_result, sizeof(t_delay_tap));
    g_dly_tap_init(f_result);
    return f_result;
}

#ifdef	__cplusplus
}
#endif

#endif	/* DELAY_H */

