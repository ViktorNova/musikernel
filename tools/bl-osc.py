#!/usr/bin/env python3
"""
This file is part of the MusiKernel project, Copyright MusiKernel Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

# This script generates band-limited wavetables of classic waveforms using
# numpy, and converts the wavetables to C code

import numpy
from matplotlib import pyplot

SR = 44100.
NYQUIST = 20000.  # Leave some headroom from the real nyquist frequency

def pydaw_pitch_to_hz(a_pitch):
    return (440.0 * pow(2.0, (float(a_pitch) - 57.0) * 0.0833333333333333333))

def get_harmonic(a_size, a_phase, a_num):
    """ @a_size:  The size of the fundamental frequency
        @a_phase: Phase in radians
        @a_num:   The harmonic number, where the fundamental == 1
    """
    f_lin = numpy.linspace(
        a_phase, (2.0 * numpy.pi * a_num) + a_phase, a_size)
    return numpy.sin(f_lin)

def dict_to_c_code(a_dict, a_name):
    raise NotImplementedError
    # TODO:  How best to represent in C what is essentially a const array
    # of const float arrays all with different lengths?
    # Maybe declare a float * [] = {arr0, arr1, arr2, ...}

def visualize(a_dict):
    keys = list(sorted(a_dict))
    pyplot.plot(a_dict[keys[0]])
    pyplot.show()

def get_notes():
    for note in range(0, 84):
        hz = pydaw_pitch_to_hz(note)
        # This introduces minor rounding error into the note frequency
        length = round(SR / hz)
        count = int((NYQUIST - hz) // hz)
        yield note, length, count

def get_saws():
    result = {}
    total_length = 0
    for note, length, count in get_notes():
        total_length += length
        arr = numpy.zeros(length)
        result[note] = arr
        for i in range(1, count + 1):
            phase = 0.0 if i % 2 else numpy.pi
            arr += get_harmonic(length, phase, i) * (1.0 / float(i))
    print("saw data size: {} bytes".format(total_length * 4))
    return result

def get_squares():
    result = {}
    total_length = 0
    for note, length, count in get_notes():
        total_length += length
        arr = numpy.zeros(length)
        result[note] = arr
        for i in range(1, count + 1, 2):
            arr += get_harmonic(length, 0.0, i) * (1.0 / float(i))
    print("square data size: {} bytes".format(total_length * 4))
    return result

visualize(get_saws())
visualize(get_squares())
