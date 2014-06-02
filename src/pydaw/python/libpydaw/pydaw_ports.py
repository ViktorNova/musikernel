# -*- coding: utf-8 -*-
"""
This file is part of the PyDAW project, Copyright PyDAW Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
"""

#Euphoria
EUPHORIA_FILES_STRING_DELIMITER = '|'
EUPHORIA_MAX_SAMPLE_COUNT = 100

#Total number of LFOs, ADSRs, other envelopes, etc... Used for the PolyFX mod matrix
EUPHORIA_MODULATOR_COUNT = 4
#How many modular PolyFX
EUPHORIA_MODULAR_POLYFX_COUNT = 4
#How many ports per PolyFX, 3 knobs and a combobox
EUPHORIA_PORTS_PER_MOD_EFFECT = 4
#How many knobs per PolyFX, 3 knobs
EUPHORIA_CONTROLS_PER_MOD_EFFECT = 3
EUPHORIA_EFFECTS_GROUPS_COUNT = 1
#The number of mono_fx groups
EUPHORIA_MONO_FX_GROUPS_COUNT = EUPHORIA_MAX_SAMPLE_COUNT
EUPHORIA_MONO_FX_COUNT = 4
EUPHORIA_OUTPUT_LEFT = 0
EUPHORIA_OUTPUT_RIGHT = 1
EUPHORIA_FIRST_CONTROL_PORT = 2
EUPHORIA_SELECTED_SAMPLE = 2
EUPHORIA_ATTACK = 3
EUPHORIA_DECAY = 4
EUPHORIA_SUSTAIN = 5
EUPHORIA_RELEASE = 6
EUPHORIA_FILTER_ATTACK = 7
EUPHORIA_FILTER_DECAY = 8
EUPHORIA_FILTER_SUSTAIN = 9
EUPHORIA_FILTER_RELEASE = 10
EUPHORIA_LFO_PITCH = 11
EUPHORIA_MASTER_VOLUME = 12
EUPHORIA_MASTER_GLIDE = 13
EUPHORIA_MASTER_PITCHBEND_AMT = 14
EUPHORIA_PITCH_ENV_TIME = 15
EUPHORIA_LFO_FREQ = 16
EUPHORIA_LFO_TYPE = 17
#From Modulex
EUPHORIA_FX0_KNOB0 = 18
EUPHORIA_FX0_KNOB1 = 19
EUPHORIA_FX0_KNOB2 = 20
EUPHORIA_FX0_COMBOBOX = 21
EUPHORIA_FX1_KNOB0 = 22
EUPHORIA_FX1_KNOB1 = 23
EUPHORIA_FX1_KNOB2 = 24
EUPHORIA_FX1_COMBOBOX = 25
EUPHORIA_FX2_KNOB0 = 26
EUPHORIA_FX2_KNOB1 = 27
EUPHORIA_FX2_KNOB2 = 28
EUPHORIA_FX2_COMBOBOX = 29
EUPHORIA_FX3_KNOB0 = 30
EUPHORIA_FX3_KNOB1 = 31
EUPHORIA_FX3_KNOB2 = 32
EUPHORIA_FX3_COMBOBOX = 33
#PolyFX Mod Matrix
EUPHORIA_PFXMATRIX_FIRST_PORT = 34
EUPHORIA_PFXMATRIX_GRP0DST0SRC0CTRL0 = 34
EUPHORIA_PFXMATRIX_GRP0DST0SRC0CTRL1 = 35
EUPHORIA_PFXMATRIX_GRP0DST0SRC0CTRL2 = 36
EUPHORIA_PFXMATRIX_GRP0DST0SRC1CTRL0 = 37
EUPHORIA_PFXMATRIX_GRP0DST0SRC1CTRL1 = 38
EUPHORIA_PFXMATRIX_GRP0DST0SRC1CTRL2 = 39
EUPHORIA_PFXMATRIX_GRP0DST0SRC2CTRL0 = 40
EUPHORIA_PFXMATRIX_GRP0DST0SRC2CTRL1 = 41
EUPHORIA_PFXMATRIX_GRP0DST0SRC2CTRL2 = 42
EUPHORIA_PFXMATRIX_GRP0DST0SRC3CTRL0 = 43
EUPHORIA_PFXMATRIX_GRP0DST0SRC3CTRL1 = 44
EUPHORIA_PFXMATRIX_GRP0DST0SRC3CTRL2 = 45
EUPHORIA_PFXMATRIX_GRP0DST1SRC0CTRL0 = 46
EUPHORIA_PFXMATRIX_GRP0DST1SRC0CTRL1 = 47
EUPHORIA_PFXMATRIX_GRP0DST1SRC0CTRL2 = 48
EUPHORIA_PFXMATRIX_GRP0DST1SRC1CTRL0 = 49
EUPHORIA_PFXMATRIX_GRP0DST1SRC1CTRL1 = 50
EUPHORIA_PFXMATRIX_GRP0DST1SRC1CTRL2 = 51
EUPHORIA_PFXMATRIX_GRP0DST1SRC2CTRL0 = 52
EUPHORIA_PFXMATRIX_GRP0DST1SRC2CTRL1 = 53
EUPHORIA_PFXMATRIX_GRP0DST1SRC2CTRL2 = 54
EUPHORIA_PFXMATRIX_GRP0DST1SRC3CTRL0 = 55
EUPHORIA_PFXMATRIX_GRP0DST1SRC3CTRL1 = 56
EUPHORIA_PFXMATRIX_GRP0DST1SRC3CTRL2 = 57
EUPHORIA_PFXMATRIX_GRP0DST2SRC0CTRL0 = 58
EUPHORIA_PFXMATRIX_GRP0DST2SRC0CTRL1 = 59
EUPHORIA_PFXMATRIX_GRP0DST2SRC0CTRL2 = 60
EUPHORIA_PFXMATRIX_GRP0DST2SRC1CTRL0 = 61
EUPHORIA_PFXMATRIX_GRP0DST2SRC1CTRL1 = 62
EUPHORIA_PFXMATRIX_GRP0DST2SRC1CTRL2 = 63
EUPHORIA_PFXMATRIX_GRP0DST2SRC2CTRL0 = 64
EUPHORIA_PFXMATRIX_GRP0DST2SRC2CTRL1 = 65
EUPHORIA_PFXMATRIX_GRP0DST2SRC2CTRL2 = 66
EUPHORIA_PFXMATRIX_GRP0DST2SRC3CTRL0 = 67
EUPHORIA_PFXMATRIX_GRP0DST2SRC3CTRL1 = 68
EUPHORIA_PFXMATRIX_GRP0DST2SRC3CTRL2 = 69
EUPHORIA_PFXMATRIX_GRP0DST3SRC0CTRL0 = 70
EUPHORIA_PFXMATRIX_GRP0DST3SRC0CTRL1 = 71
EUPHORIA_PFXMATRIX_GRP0DST3SRC0CTRL2 = 72
EUPHORIA_PFXMATRIX_GRP0DST3SRC1CTRL0 = 73
EUPHORIA_PFXMATRIX_GRP0DST3SRC1CTRL1 = 74
EUPHORIA_PFXMATRIX_GRP0DST3SRC1CTRL2 = 75
EUPHORIA_PFXMATRIX_GRP0DST3SRC2CTRL0 = 76
EUPHORIA_PFXMATRIX_GRP0DST3SRC2CTRL1 = 77
EUPHORIA_PFXMATRIX_GRP0DST3SRC2CTRL2 = 78
EUPHORIA_PFXMATRIX_GRP0DST3SRC3CTRL0 = 79
EUPHORIA_PFXMATRIX_GRP0DST3SRC3CTRL1 = 80
EUPHORIA_PFXMATRIX_GRP0DST3SRC3CTRL2 = 81

EUPHORIA_PFXMATRIX_GRP0DST0SRC4CTRL0 = 82
EUPHORIA_PFXMATRIX_GRP0DST0SRC4CTRL1 = 83
EUPHORIA_PFXMATRIX_GRP0DST0SRC4CTRL2 = 84
EUPHORIA_PFXMATRIX_GRP0DST1SRC4CTRL0 = 85
EUPHORIA_PFXMATRIX_GRP0DST1SRC4CTRL1 = 86
EUPHORIA_PFXMATRIX_GRP0DST1SRC4CTRL2 = 87
EUPHORIA_PFXMATRIX_GRP0DST2SRC4CTRL0 = 88
EUPHORIA_PFXMATRIX_GRP0DST2SRC4CTRL1 = 89
EUPHORIA_PFXMATRIX_GRP0DST2SRC4CTRL2 = 90
EUPHORIA_PFXMATRIX_GRP0DST3SRC4CTRL0 = 91
EUPHORIA_PFXMATRIX_GRP0DST3SRC4CTRL1 = 92
EUPHORIA_PFXMATRIX_GRP0DST3SRC4CTRL2 = 93

EUPHORIA_PFXMATRIX_GRP0DST0SRC5CTRL0 = 94
EUPHORIA_PFXMATRIX_GRP0DST0SRC5CTRL1 = 95
EUPHORIA_PFXMATRIX_GRP0DST0SRC5CTRL2 = 96
EUPHORIA_PFXMATRIX_GRP0DST1SRC5CTRL0 = 97
EUPHORIA_PFXMATRIX_GRP0DST1SRC5CTRL1 = 98
EUPHORIA_PFXMATRIX_GRP0DST1SRC5CTRL2 = 99
EUPHORIA_PFXMATRIX_GRP0DST2SRC5CTRL0 = 100
EUPHORIA_PFXMATRIX_GRP0DST2SRC5CTRL1 = 101
EUPHORIA_PFXMATRIX_GRP0DST2SRC5CTRL2 = 102
EUPHORIA_PFXMATRIX_GRP0DST3SRC5CTRL0 = 103
EUPHORIA_PFXMATRIX_GRP0DST3SRC5CTRL1 = 104
EUPHORIA_PFXMATRIX_GRP0DST3SRC5CTRL2 = 105

#End PolyFX Mod Matrix

# This is the last control port, + 1, for zero-based iteration
EUPHORIA_LAST_REGULAR_CONTROL_PORT = 106
# The first port to use when enumerating the ports for mod_matrix controls.
# All of the mod_matrix ports should be sequential,
# * any additional ports should prepend self port number
EUPHORIA_FIRST_SAMPLE_TABLE_PORT = 106
#The range of ports for sample pitch
EUPHORIA_SAMPLE_PITCH_PORT_RANGE_MIN = EUPHORIA_FIRST_SAMPLE_TABLE_PORT
EUPHORIA_SAMPLE_PITCH_PORT_RANGE_MAX = \
    (EUPHORIA_SAMPLE_PITCH_PORT_RANGE_MIN + EUPHORIA_MAX_SAMPLE_COUNT)
#The range of ports for the low note to play a sample on
EUPHORIA_PLAY_PITCH_LOW_PORT_RANGE_MIN = EUPHORIA_SAMPLE_PITCH_PORT_RANGE_MAX
EUPHORIA_PLAY_PITCH_LOW_PORT_RANGE_MAX = \
    (EUPHORIA_PLAY_PITCH_LOW_PORT_RANGE_MIN + EUPHORIA_MAX_SAMPLE_COUNT)
#The range of ports for the high note to play a sample on
EUPHORIA_PLAY_PITCH_HIGH_PORT_RANGE_MIN = EUPHORIA_PLAY_PITCH_LOW_PORT_RANGE_MAX
EUPHORIA_PLAY_PITCH_HIGH_PORT_RANGE_MAX = \
    (EUPHORIA_PLAY_PITCH_HIGH_PORT_RANGE_MIN + EUPHORIA_MAX_SAMPLE_COUNT)
#The range of ports for sample volume
EUPHORIA_SAMPLE_VOLUME_PORT_RANGE_MIN = EUPHORIA_PLAY_PITCH_HIGH_PORT_RANGE_MAX
EUPHORIA_SAMPLE_VOLUME_PORT_RANGE_MAX = \
    (EUPHORIA_SAMPLE_VOLUME_PORT_RANGE_MIN + EUPHORIA_MAX_SAMPLE_COUNT)
EUPHORIA_SAMPLE_START_PORT_RANGE_MIN = EUPHORIA_SAMPLE_VOLUME_PORT_RANGE_MAX
EUPHORIA_SAMPLE_START_PORT_RANGE_MAX = \
    (EUPHORIA_SAMPLE_START_PORT_RANGE_MIN + EUPHORIA_MAX_SAMPLE_COUNT)
EUPHORIA_SAMPLE_END_PORT_RANGE_MIN = EUPHORIA_SAMPLE_START_PORT_RANGE_MAX
EUPHORIA_SAMPLE_END_PORT_RANGE_MAX = \
    (EUPHORIA_SAMPLE_END_PORT_RANGE_MIN + EUPHORIA_MAX_SAMPLE_COUNT)
EUPHORIA_SAMPLE_VEL_SENS_PORT_RANGE_MIN = EUPHORIA_SAMPLE_END_PORT_RANGE_MAX
EUPHORIA_SAMPLE_VEL_SENS_PORT_RANGE_MAX = \
    (EUPHORIA_SAMPLE_VEL_SENS_PORT_RANGE_MIN + EUPHORIA_MAX_SAMPLE_COUNT)
EUPHORIA_SAMPLE_VEL_LOW_PORT_RANGE_MIN = EUPHORIA_SAMPLE_VEL_SENS_PORT_RANGE_MAX
EUPHORIA_SAMPLE_VEL_LOW_PORT_RANGE_MAX = \
    (EUPHORIA_SAMPLE_VEL_LOW_PORT_RANGE_MIN + EUPHORIA_MAX_SAMPLE_COUNT)
EUPHORIA_SAMPLE_VEL_HIGH_PORT_RANGE_MIN = EUPHORIA_SAMPLE_VEL_LOW_PORT_RANGE_MAX
EUPHORIA_SAMPLE_VEL_HIGH_PORT_RANGE_MAX = \
    (EUPHORIA_SAMPLE_VEL_HIGH_PORT_RANGE_MIN + EUPHORIA_MAX_SAMPLE_COUNT)
EUPHORIA_PITCH_PORT_RANGE_MIN = EUPHORIA_SAMPLE_VEL_HIGH_PORT_RANGE_MAX
EUPHORIA_PITCH_PORT_RANGE_MAX = (EUPHORIA_PITCH_PORT_RANGE_MIN + EUPHORIA_MAX_SAMPLE_COUNT)
EUPHORIA_TUNE_PORT_RANGE_MIN = EUPHORIA_PITCH_PORT_RANGE_MAX
EUPHORIA_TUNE_PORT_RANGE_MAX = (EUPHORIA_TUNE_PORT_RANGE_MIN + EUPHORIA_MAX_SAMPLE_COUNT)
EUPHORIA_SAMPLE_INTERPOLATION_MODE_PORT_RANGE_MIN = EUPHORIA_TUNE_PORT_RANGE_MAX
EUPHORIA_SAMPLE_INTERPOLATION_MODE_PORT_RANGE_MAX = \
(EUPHORIA_SAMPLE_INTERPOLATION_MODE_PORT_RANGE_MIN + EUPHORIA_MAX_SAMPLE_COUNT)
EUPHORIA_SAMPLE_LOOP_START_PORT_RANGE_MIN = EUPHORIA_SAMPLE_INTERPOLATION_MODE_PORT_RANGE_MAX
EUPHORIA_SAMPLE_LOOP_START_PORT_RANGE_MAX = \
    (EUPHORIA_SAMPLE_LOOP_START_PORT_RANGE_MIN + EUPHORIA_MAX_SAMPLE_COUNT)
EUPHORIA_SAMPLE_LOOP_END_PORT_RANGE_MIN = EUPHORIA_SAMPLE_LOOP_START_PORT_RANGE_MAX
EUPHORIA_SAMPLE_LOOP_END_PORT_RANGE_MAX = \
    (EUPHORIA_SAMPLE_LOOP_END_PORT_RANGE_MIN + EUPHORIA_MAX_SAMPLE_COUNT)
EUPHORIA_SAMPLE_LOOP_MODE_PORT_RANGE_MIN = EUPHORIA_SAMPLE_LOOP_END_PORT_RANGE_MAX
EUPHORIA_SAMPLE_LOOP_MODE_PORT_RANGE_MAX = \
    (EUPHORIA_SAMPLE_LOOP_MODE_PORT_RANGE_MIN + EUPHORIA_MAX_SAMPLE_COUNT)
#MonoFX0
EUPHORIA_MONO_FX0_KNOB0_PORT_RANGE_MIN = EUPHORIA_SAMPLE_LOOP_MODE_PORT_RANGE_MAX
EUPHORIA_MONO_FX0_KNOB0_PORT_RANGE_MAX = \
    (EUPHORIA_MONO_FX0_KNOB0_PORT_RANGE_MIN + EUPHORIA_MONO_FX_GROUPS_COUNT)
EUPHORIA_MONO_FX0_KNOB1_PORT_RANGE_MIN = EUPHORIA_MONO_FX0_KNOB0_PORT_RANGE_MAX
EUPHORIA_MONO_FX0_KNOB1_PORT_RANGE_MAX = \
    (EUPHORIA_MONO_FX0_KNOB1_PORT_RANGE_MIN + EUPHORIA_MONO_FX_GROUPS_COUNT)
EUPHORIA_MONO_FX0_KNOB2_PORT_RANGE_MIN = EUPHORIA_MONO_FX0_KNOB1_PORT_RANGE_MAX
EUPHORIA_MONO_FX0_KNOB2_PORT_RANGE_MAX = \
    (EUPHORIA_MONO_FX0_KNOB2_PORT_RANGE_MIN + EUPHORIA_MONO_FX_GROUPS_COUNT)
EUPHORIA_MONO_FX0_COMBOBOX_PORT_RANGE_MIN = EUPHORIA_MONO_FX0_KNOB2_PORT_RANGE_MAX
EUPHORIA_MONO_FX0_COMBOBOX_PORT_RANGE_MAX = \
    (EUPHORIA_MONO_FX0_COMBOBOX_PORT_RANGE_MIN + EUPHORIA_MONO_FX_GROUPS_COUNT)
#MonoFX1
EUPHORIA_MONO_FX1_KNOB0_PORT_RANGE_MIN = EUPHORIA_MONO_FX0_COMBOBOX_PORT_RANGE_MAX
EUPHORIA_MONO_FX1_KNOB0_PORT_RANGE_MAX = \
    (EUPHORIA_MONO_FX1_KNOB0_PORT_RANGE_MIN + EUPHORIA_MONO_FX_GROUPS_COUNT)
EUPHORIA_MONO_FX1_KNOB1_PORT_RANGE_MIN = EUPHORIA_MONO_FX1_KNOB0_PORT_RANGE_MAX
EUPHORIA_MONO_FX1_KNOB1_PORT_RANGE_MAX = \
    (EUPHORIA_MONO_FX1_KNOB1_PORT_RANGE_MIN + EUPHORIA_MONO_FX_GROUPS_COUNT)
EUPHORIA_MONO_FX1_KNOB2_PORT_RANGE_MIN = EUPHORIA_MONO_FX1_KNOB1_PORT_RANGE_MAX
EUPHORIA_MONO_FX1_KNOB2_PORT_RANGE_MAX = \
    (EUPHORIA_MONO_FX1_KNOB2_PORT_RANGE_MIN + EUPHORIA_MONO_FX_GROUPS_COUNT)
EUPHORIA_MONO_FX1_COMBOBOX_PORT_RANGE_MIN = EUPHORIA_MONO_FX1_KNOB2_PORT_RANGE_MAX
EUPHORIA_MONO_FX1_COMBOBOX_PORT_RANGE_MAX = \
    (EUPHORIA_MONO_FX1_COMBOBOX_PORT_RANGE_MIN + EUPHORIA_MONO_FX_GROUPS_COUNT)
#MonoFX2
EUPHORIA_MONO_FX2_KNOB0_PORT_RANGE_MIN = EUPHORIA_MONO_FX1_COMBOBOX_PORT_RANGE_MAX
EUPHORIA_MONO_FX2_KNOB0_PORT_RANGE_MAX = \
    (EUPHORIA_MONO_FX2_KNOB0_PORT_RANGE_MIN + EUPHORIA_MONO_FX_GROUPS_COUNT)
EUPHORIA_MONO_FX2_KNOB1_PORT_RANGE_MIN = EUPHORIA_MONO_FX2_KNOB0_PORT_RANGE_MAX
EUPHORIA_MONO_FX2_KNOB1_PORT_RANGE_MAX = \
    (EUPHORIA_MONO_FX2_KNOB1_PORT_RANGE_MIN + EUPHORIA_MONO_FX_GROUPS_COUNT)
EUPHORIA_MONO_FX2_KNOB2_PORT_RANGE_MIN = EUPHORIA_MONO_FX2_KNOB1_PORT_RANGE_MAX
EUPHORIA_MONO_FX2_KNOB2_PORT_RANGE_MAX = \
    (EUPHORIA_MONO_FX2_KNOB2_PORT_RANGE_MIN + EUPHORIA_MONO_FX_GROUPS_COUNT)
EUPHORIA_MONO_FX2_COMBOBOX_PORT_RANGE_MIN = EUPHORIA_MONO_FX2_KNOB2_PORT_RANGE_MAX
EUPHORIA_MONO_FX2_COMBOBOX_PORT_RANGE_MAX = \
    (EUPHORIA_MONO_FX2_COMBOBOX_PORT_RANGE_MIN + EUPHORIA_MONO_FX_GROUPS_COUNT)
#MonoFX3
EUPHORIA_MONO_FX3_KNOB0_PORT_RANGE_MIN = EUPHORIA_MONO_FX2_COMBOBOX_PORT_RANGE_MAX
EUPHORIA_MONO_FX3_KNOB0_PORT_RANGE_MAX = \
    (EUPHORIA_MONO_FX3_KNOB0_PORT_RANGE_MIN + EUPHORIA_MONO_FX_GROUPS_COUNT)
EUPHORIA_MONO_FX3_KNOB1_PORT_RANGE_MIN = EUPHORIA_MONO_FX3_KNOB0_PORT_RANGE_MAX
EUPHORIA_MONO_FX3_KNOB1_PORT_RANGE_MAX = \
    (EUPHORIA_MONO_FX3_KNOB1_PORT_RANGE_MIN + EUPHORIA_MONO_FX_GROUPS_COUNT)
EUPHORIA_MONO_FX3_KNOB2_PORT_RANGE_MIN = EUPHORIA_MONO_FX3_KNOB1_PORT_RANGE_MAX
EUPHORIA_MONO_FX3_KNOB2_PORT_RANGE_MAX = \
    (EUPHORIA_MONO_FX3_KNOB2_PORT_RANGE_MIN + EUPHORIA_MONO_FX_GROUPS_COUNT)
EUPHORIA_MONO_FX3_COMBOBOX_PORT_RANGE_MIN = EUPHORIA_MONO_FX3_KNOB2_PORT_RANGE_MAX
EUPHORIA_MONO_FX3_COMBOBOX_PORT_RANGE_MAX = \
    (EUPHORIA_MONO_FX3_COMBOBOX_PORT_RANGE_MIN + EUPHORIA_MONO_FX_GROUPS_COUNT)
#Sample FX Group
EUPHORIA_SAMPLE_MONO_FX_GROUP_PORT_RANGE_MIN = EUPHORIA_MONO_FX3_COMBOBOX_PORT_RANGE_MAX
EUPHORIA_SAMPLE_MONO_FX_GROUP_PORT_RANGE_MAX = \
(EUPHORIA_SAMPLE_MONO_FX_GROUP_PORT_RANGE_MIN + EUPHORIA_MAX_SAMPLE_COUNT)
#Noise amp
EUPHORIA_NOISE_AMP_MIN = EUPHORIA_SAMPLE_MONO_FX_GROUP_PORT_RANGE_MAX
EUPHORIA_NOISE_AMP_MAX = (EUPHORIA_NOISE_AMP_MIN + EUPHORIA_MAX_SAMPLE_COUNT)
#Noise type
EUPHORIA_NOISE_TYPE_MIN = EUPHORIA_NOISE_AMP_MAX
EUPHORIA_NOISE_TYPE_MAX = (EUPHORIA_NOISE_TYPE_MIN + EUPHORIA_MAX_SAMPLE_COUNT)

#sample fade-in
EUPHORIA_SAMPLE_FADE_IN_MIN = EUPHORIA_NOISE_TYPE_MAX
EUPHORIA_SAMPLE_FADE_IN_MAX = (EUPHORIA_SAMPLE_FADE_IN_MIN + EUPHORIA_MAX_SAMPLE_COUNT)

#sample fade-out
EUPHORIA_SAMPLE_FADE_OUT_MIN = EUPHORIA_SAMPLE_FADE_IN_MAX
EUPHORIA_SAMPLE_FADE_OUT_MAX = (EUPHORIA_SAMPLE_FADE_OUT_MIN + EUPHORIA_MAX_SAMPLE_COUNT)

EUPHORIA_FIRST_EQ_PORT = EUPHORIA_SAMPLE_FADE_OUT_MAX

# Stacked as:
# 100 *
#     [freq, bw, gain] * 6

EUPHORIA_LAST_EQ_PORT = (EUPHORIA_FIRST_EQ_PORT + (18 * 100))

EUPHORIA_LFO_PITCH_FINE = EUPHORIA_LAST_EQ_PORT


#Modulex

MODULEX_INPUT0 = 0
MODULEX_INPUT1 = 1
MODULEX_OUTPUT0 = 2
MODULEX_OUTPUT1 = 3
MODULEX_FIRST_CONTROL_PORT = 4
MODULEX_FX0_KNOB0 = 4
MODULEX_FX0_KNOB1 = 5
MODULEX_FX0_KNOB2 = 6
MODULEX_FX0_COMBOBOX = 7
MODULEX_FX1_KNOB0 = 8
MODULEX_FX1_KNOB1 = 9
MODULEX_FX1_KNOB2 = 10
MODULEX_FX1_COMBOBOX = 11
MODULEX_FX2_KNOB0 = 12
MODULEX_FX2_KNOB1 = 13
MODULEX_FX2_KNOB2 = 14
MODULEX_FX2_COMBOBOX = 15
MODULEX_FX3_KNOB0 = 16
MODULEX_FX3_KNOB1 = 17
MODULEX_FX3_KNOB2 = 18
MODULEX_FX3_COMBOBOX = 19
MODULEX_FX4_KNOB0 = 20
MODULEX_FX4_KNOB1 = 21
MODULEX_FX4_KNOB2 = 22
MODULEX_FX4_COMBOBOX = 23
MODULEX_FX5_KNOB0 = 24
MODULEX_FX5_KNOB1 = 25
MODULEX_FX5_KNOB2 = 26
MODULEX_FX5_COMBOBOX = 27
MODULEX_FX6_KNOB0 = 28
MODULEX_FX6_KNOB1 = 29
MODULEX_FX6_KNOB2 = 30
MODULEX_FX6_COMBOBOX = 31
MODULEX_FX7_KNOB0 = 32
MODULEX_FX7_KNOB1 = 33
MODULEX_FX7_KNOB2 = 34
MODULEX_FX7_COMBOBOX = 35
MODULEX_DELAY_TIME = 36
MODULEX_FEEDBACK = 37
MODULEX_DRY = 38
MODULEX_WET = 39
MODULEX_DUCK = 40
MODULEX_CUTOFF = 41
MODULEX_STEREO = 42
MODULEX_VOL_SLIDER = 43
MODULEX_REVERB_TIME = 44
MODULEX_REVERB_WET = 45
MODULEX_REVERB_COLOR = 46

MODULEX_EQ_ON = 47
MODULEX_EQ1_FREQ = 48
MODULEX_EQ1_RES = 49
MODULEX_EQ1_GAIN = 50
MODULEX_EQ1_FREQ = 48
MODULEX_EQ1_RES = 49
MODULEX_EQ1_GAIN = 50
MODULEX_EQ2_FREQ = 51
MODULEX_EQ2_RES = 52
MODULEX_EQ2_GAIN = 53
MODULEX_EQ3_FREQ = 54
MODULEX_EQ3_RES = 55
MODULEX_EQ3_GAIN = 56
MODULEX_EQ4_FREQ = 57
MODULEX_EQ4_RES = 58
MODULEX_EQ4_GAIN = 59
MODULEX_EQ5_FREQ = 60
MODULEX_EQ5_RES = 61
MODULEX_EQ5_GAIN = 62
MODULEX_EQ6_FREQ = 63
MODULEX_EQ6_RES = 64
MODULEX_EQ6_GAIN = 65


#Way-V

#Total number of LFOs, ADSRs, other envelopes, etc... Used for the PolyFX mod matrix
WAYV_MODULATOR_COUNT = 4
#How many modular PolyFX
WAYV_MODULAR_POLYFX_COUNT = 4
#How many ports per PolyFX, 3 knobs and a combobox
WAYV_PORTS_PER_MOD_EFFECT = 4
#How many knobs per PolyFX, 3 knobs
WAYV_CONTROLS_PER_MOD_EFFECT = 3
WAYV_EFFECTS_GROUPS_COUNT = 1
WAYV_OUTPUT0 = 0
WAYV_OUTPUT1 = 1
WAYV_FIRST_CONTROL_PORT = 2
WAYV_ATTACK_MAIN = 2
WAYV_DECAY_MAIN = 3
WAYV_SUSTAIN_MAIN = 4
WAYV_RELEASE_MAIN = 5
WAYV_NOISE_AMP = 6
WAYV_OSC1_TYPE = 7
WAYV_OSC1_PITCH = 8
WAYV_OSC1_TUNE = 9
WAYV_OSC1_VOLUME = 10
WAYV_OSC2_TYPE = 11
WAYV_OSC2_PITCH = 12
WAYV_OSC2_TUNE = 13
WAYV_OSC2_VOLUME = 14
WAYV_MASTER_VOLUME = 15
WAYV_OSC1_UNISON_VOICES = 16
WAYV_OSC1_UNISON_SPREAD = 17
WAYV_MASTER_GLIDE = 18
WAYV_MASTER_PITCHBEND_AMT = 19
WAYV_ATTACK1 = 20
WAYV_DECAY1 = 21
WAYV_SUSTAIN1 = 22
WAYV_RELEASE1 = 23
WAYV_ATTACK2 = 24
WAYV_DECAY2 = 25
WAYV_SUSTAIN2 = 26
WAYV_RELEASE2 = 27
WAYV_ATTACK_PFX1 = 28
WAYV_DECAY_PFX1 = 29
WAYV_SUSTAIN_PFX1 = 30
WAYV_RELEASE_PFX1 = 31
WAYV_ATTACK_PFX2 = 32
WAYV_DECAY_PFX2 = 33
WAYV_SUSTAIN_PFX2 = 34
WAYV_RELEASE_PFX2 = 35
WAYV_NOISE_TYPE = 36
WAYV_RAMP_ENV_TIME = 37
WAYV_LFO_FREQ = 38
WAYV_LFO_TYPE = 39
WAYV_FX0_KNOB0 = 40
WAYV_FX0_KNOB1 = 41
WAYV_FX0_KNOB2 = 42
WAYV_FX0_COMBOBOX = 43
WAYV_FX1_KNOB0 = 44
WAYV_FX1_KNOB1 = 45
WAYV_FX1_KNOB2 = 46
WAYV_FX1_COMBOBOX = 47
WAYV_FX2_KNOB0 = 48
WAYV_FX2_KNOB1 = 49
WAYV_FX2_KNOB2 = 50
WAYV_FX2_COMBOBOX = 51
WAYV_FX3_KNOB0 = 52
WAYV_FX3_KNOB1 = 53
WAYV_FX3_KNOB2 = 54
WAYV_FX3_COMBOBOX = 55
#PolyFX Mod Matrix
WAVV_PFXMATRIX_FIRST_PORT = 56
WAVV_PFXMATRIX_GRP0DST0SRC0CTRL0 = 56
WAVV_PFXMATRIX_GRP0DST0SRC0CTRL1 = 57
WAVV_PFXMATRIX_GRP0DST0SRC0CTRL2 = 58
WAVV_PFXMATRIX_GRP0DST0SRC1CTRL0 = 59
WAVV_PFXMATRIX_GRP0DST0SRC1CTRL1 = 60
WAVV_PFXMATRIX_GRP0DST0SRC1CTRL2 = 61
WAVV_PFXMATRIX_GRP0DST0SRC2CTRL0 = 62
WAVV_PFXMATRIX_GRP0DST0SRC2CTRL1 = 63
WAVV_PFXMATRIX_GRP0DST0SRC2CTRL2 = 64
WAVV_PFXMATRIX_GRP0DST0SRC3CTRL0 = 65
WAVV_PFXMATRIX_GRP0DST0SRC3CTRL1 = 66
WAVV_PFXMATRIX_GRP0DST0SRC3CTRL2 = 67
WAVV_PFXMATRIX_GRP0DST1SRC0CTRL0 = 68
WAVV_PFXMATRIX_GRP0DST1SRC0CTRL1 = 69
WAVV_PFXMATRIX_GRP0DST1SRC0CTRL2 = 70
WAVV_PFXMATRIX_GRP0DST1SRC1CTRL0 = 71
WAVV_PFXMATRIX_GRP0DST1SRC1CTRL1 = 72
WAVV_PFXMATRIX_GRP0DST1SRC1CTRL2 = 73
WAVV_PFXMATRIX_GRP0DST1SRC2CTRL0 = 74
WAVV_PFXMATRIX_GRP0DST1SRC2CTRL1 = 75
WAVV_PFXMATRIX_GRP0DST1SRC2CTRL2 = 76
WAVV_PFXMATRIX_GRP0DST1SRC3CTRL0 = 77
WAVV_PFXMATRIX_GRP0DST1SRC3CTRL1 = 78
WAVV_PFXMATRIX_GRP0DST1SRC3CTRL2 = 79
WAVV_PFXMATRIX_GRP0DST2SRC0CTRL0 = 80
WAVV_PFXMATRIX_GRP0DST2SRC0CTRL1 = 81
WAVV_PFXMATRIX_GRP0DST2SRC0CTRL2 = 82
WAVV_PFXMATRIX_GRP0DST2SRC1CTRL0 = 83
WAVV_PFXMATRIX_GRP0DST2SRC1CTRL1 = 84
WAVV_PFXMATRIX_GRP0DST2SRC1CTRL2 = 85
WAVV_PFXMATRIX_GRP0DST2SRC2CTRL0 = 86
WAVV_PFXMATRIX_GRP0DST2SRC2CTRL1 = 87
WAVV_PFXMATRIX_GRP0DST2SRC2CTRL2 = 88
WAVV_PFXMATRIX_GRP0DST2SRC3CTRL0 = 89
WAVV_PFXMATRIX_GRP0DST2SRC3CTRL1 = 90
WAVV_PFXMATRIX_GRP0DST2SRC3CTRL2 = 91
WAVV_PFXMATRIX_GRP0DST3SRC0CTRL0 = 92
WAVV_PFXMATRIX_GRP0DST3SRC0CTRL1 = 93
WAVV_PFXMATRIX_GRP0DST3SRC0CTRL2 = 94
WAVV_PFXMATRIX_GRP0DST3SRC1CTRL0 = 95
WAVV_PFXMATRIX_GRP0DST3SRC1CTRL1 = 96
WAVV_PFXMATRIX_GRP0DST3SRC1CTRL2 = 97
WAVV_PFXMATRIX_GRP0DST3SRC2CTRL0 = 98
WAVV_PFXMATRIX_GRP0DST3SRC2CTRL1 = 99
WAVV_PFXMATRIX_GRP0DST3SRC2CTRL2 = 100
WAVV_PFXMATRIX_GRP0DST3SRC3CTRL0 = 101
WAVV_PFXMATRIX_GRP0DST3SRC3CTRL1 = 102
WAVV_PFXMATRIX_GRP0DST3SRC3CTRL2 = 103
#End PolyFX Mod Matrix
WAYV_ADSR1_CHECKBOX = 105
WAYV_ADSR2_CHECKBOX = 106
WAYV_LFO_AMP = 107
WAYV_LFO_PITCH = 108
WAYV_PITCH_ENV_AMT = 109
WAYV_OSC2_UNISON_VOICES = 110
WAYV_OSC2_UNISON_SPREAD = 111
WAYV_LFO_AMOUNT = 112
WAYV_OSC3_TYPE = 113
WAYV_OSC3_PITCH = 114
WAYV_OSC3_TUNE = 115
WAYV_OSC3_VOLUME = 116
WAYV_OSC3_UNISON_VOICES = 117
WAYV_OSC3_UNISON_SPREAD = 118
WAYV_OSC1_FM1 = 119
WAYV_OSC1_FM2 = 120
WAYV_OSC1_FM3 = 121
WAYV_OSC2_FM1 = 122
WAYV_OSC2_FM2 = 123
WAYV_OSC2_FM3 = 124
WAYV_OSC3_FM1 = 125
WAYV_OSC3_FM2 = 126
WAYV_OSC3_FM3 = 127
WAYV_ATTACK3 = 128
WAYV_DECAY3 = 129
WAYV_SUSTAIN3 = 130
WAYV_RELEASE3 = 131
WAYV_ADSR3_CHECKBOX = 132

WAVV_PFXMATRIX_GRP0DST0SRC4CTRL0 = 133
WAVV_PFXMATRIX_GRP0DST0SRC4CTRL1 = 134
WAVV_PFXMATRIX_GRP0DST0SRC4CTRL2 = 135
WAVV_PFXMATRIX_GRP0DST1SRC4CTRL0 = 136
WAVV_PFXMATRIX_GRP0DST1SRC4CTRL1 = 137
WAVV_PFXMATRIX_GRP0DST1SRC4CTRL2 = 138
WAVV_PFXMATRIX_GRP0DST2SRC4CTRL0 = 139
WAVV_PFXMATRIX_GRP0DST2SRC4CTRL1 = 140
WAVV_PFXMATRIX_GRP0DST2SRC4CTRL2 = 141
WAVV_PFXMATRIX_GRP0DST3SRC4CTRL0 = 142
WAVV_PFXMATRIX_GRP0DST3SRC4CTRL1 = 143
WAVV_PFXMATRIX_GRP0DST3SRC4CTRL2 = 144

WAVV_PFXMATRIX_GRP0DST0SRC5CTRL0 = 145
WAVV_PFXMATRIX_GRP0DST0SRC5CTRL1 = 146
WAVV_PFXMATRIX_GRP0DST0SRC5CTRL2 = 147
WAVV_PFXMATRIX_GRP0DST1SRC5CTRL0 = 148
WAVV_PFXMATRIX_GRP0DST1SRC5CTRL1 = 149
WAVV_PFXMATRIX_GRP0DST1SRC5CTRL2 = 150
WAVV_PFXMATRIX_GRP0DST2SRC5CTRL0 = 151
WAVV_PFXMATRIX_GRP0DST2SRC5CTRL1 = 152
WAVV_PFXMATRIX_GRP0DST2SRC5CTRL2 = 153
WAVV_PFXMATRIX_GRP0DST3SRC5CTRL0 = 154
WAVV_PFXMATRIX_GRP0DST3SRC5CTRL1 = 155
WAVV_PFXMATRIX_GRP0DST3SRC5CTRL2 = 156
WAYV_PERC_ENV_TIME1 = 157
WAYV_PERC_ENV_PITCH1 = 158
WAYV_PERC_ENV_TIME2 = 159
WAYV_PERC_ENV_PITCH2 = 160
WAYV_PERC_ENV_ON = 161
WAYV_RAMP_CURVE = 162
WAYV_MONO_MODE = 163

WAYV_OSC4_TYPE = 164
WAYV_OSC4_PITCH = 165
WAYV_OSC4_TUNE = 166
WAYV_OSC4_VOLUME = 167
WAYV_OSC4_UNISON_VOICES = 168
WAYV_OSC4_UNISON_SPREAD = 169
WAYV_OSC1_FM4 = 170
WAYV_OSC2_FM4 = 171
WAYV_OSC3_FM4 = 172
WAYV_OSC4_FM1 = 173
WAYV_OSC4_FM2 = 174
WAYV_OSC4_FM3 = 175
WAYV_OSC4_FM4 = 176
WAYV_ATTACK4 = 177
WAYV_DECAY4 =  178
WAYV_SUSTAIN4 = 179
WAYV_RELEASE4 = 180
WAYV_ADSR4_CHECKBOX = 181

WAYV_FM_MACRO1 = 182
WAYV_FM_MACRO1_OSC1_FM1 = 183
WAYV_FM_MACRO1_OSC1_FM2 = 184
WAYV_FM_MACRO1_OSC1_FM3 = 185
WAYV_FM_MACRO1_OSC1_FM4 = 186
WAYV_FM_MACRO1_OSC2_FM1 = 187
WAYV_FM_MACRO1_OSC2_FM2 = 188
WAYV_FM_MACRO1_OSC2_FM3 = 189
WAYV_FM_MACRO1_OSC2_FM4 = 190
WAYV_FM_MACRO1_OSC3_FM1 = 191
WAYV_FM_MACRO1_OSC3_FM2 = 192
WAYV_FM_MACRO1_OSC3_FM3 = 193
WAYV_FM_MACRO1_OSC3_FM4 = 194
WAYV_FM_MACRO1_OSC4_FM1 = 195
WAYV_FM_MACRO1_OSC4_FM2 = 196
WAYV_FM_MACRO1_OSC4_FM3 = 197
WAYV_FM_MACRO1_OSC4_FM4 = 198

WAYV_FM_MACRO2 = 199
WAYV_FM_MACRO2_OSC1_FM1 = 200
WAYV_FM_MACRO2_OSC1_FM2 = 201
WAYV_FM_MACRO2_OSC1_FM3 = 202
WAYV_FM_MACRO2_OSC1_FM4 = 203
WAYV_FM_MACRO2_OSC2_FM1 = 204
WAYV_FM_MACRO2_OSC2_FM2 = 205
WAYV_FM_MACRO2_OSC2_FM3 = 206
WAYV_FM_MACRO2_OSC2_FM4 = 207
WAYV_FM_MACRO2_OSC3_FM1 = 208
WAYV_FM_MACRO2_OSC3_FM2 = 209
WAYV_FM_MACRO2_OSC3_FM3 = 210
WAYV_FM_MACRO2_OSC3_FM4 = 211
WAYV_FM_MACRO2_OSC4_FM1 = 212
WAYV_FM_MACRO2_OSC4_FM2 = 213
WAYV_FM_MACRO2_OSC4_FM3 = 214
WAYV_FM_MACRO2_OSC4_FM4 = 215

WAYV_LFO_PHASE = 216

WAYV_FM_MACRO1_OSC1_VOL = 217
WAYV_FM_MACRO1_OSC2_VOL = 218
WAYV_FM_MACRO1_OSC3_VOL = 219
WAYV_FM_MACRO1_OSC4_VOL = 220

WAYV_FM_MACRO2_OSC1_VOL = 221
WAYV_FM_MACRO2_OSC2_VOL = 222
WAYV_FM_MACRO2_OSC3_VOL = 223
WAYV_FM_MACRO2_OSC4_VOL = 224
WAYV_LFO_PITCH_FINE = 225
WAYV_ADSR_PREFX = 226

WAYV_ADSR1_DELAY = 227
WAYV_ADSR2_DELAY = 228
WAYV_ADSR3_DELAY = 229
WAYV_ADSR4_DELAY = 230

WAYV_ADSR1_HOLD = 231
WAYV_ADSR2_HOLD = 232
WAYV_ADSR3_HOLD = 233
WAYV_ADSR4_HOLD = 234

WAYV_PFX_ADSR_DELAY = 235
WAYV_PFX_ADSR_F_DELAY = 236
WAYV_PFX_ADSR_HOLD = 237
WAYV_PFX_ADSR_F_HOLD = 238
WAYV_HOLD_MAIN  = 239

WAYV_DELAY_NOISE = 240
WAYV_ATTACK_NOISE = 241
WAYV_HOLD_NOISE = 242
WAYV_DECAY_NOISE = 243
WAYV_SUSTAIN_NOISE = 244
WAYV_RELEASE_NOISE = 245
WAYV_ADSR_NOISE_ON = 246

WAYV_DELAY_LFO = 247
WAYV_ATTACK_LFO = 248
WAYV_HOLD_LFO = 249
WAYV_DECAY_LFO = 250
WAYV_SUSTAIN_LFO = 251
WAYV_RELEASE_LFO = 252
WAYV_ADSR_LFO_ON = 253

#Ray-V

RAYV_OUTPUT0 = 0
RAYV_OUTPUT1 = 1
RAYV_FIRST_CONTROL_PORT = 2
RAYV_ATTACK = 2
RAYV_DECAY = 3
RAYV_SUSTAIN = 4
RAYV_RELEASE = 5
RAYV_TIMBRE = 6
RAYV_RES = 7
RAYV_DIST = 8
RAYV_FILTER_ATTACK = 9
RAYV_FILTER_DECAY = 10
RAYV_FILTER_SUSTAIN = 11
RAYV_FILTER_RELEASE = 12
RAYV_NOISE_AMP = 13
RAYV_FILTER_ENV_AMT = 14
RAYV_DIST_WET = 15
RAYV_OSC1_TYPE = 16
RAYV_OSC1_PITCH = 17
RAYV_OSC1_TUNE = 18
RAYV_OSC1_VOLUME = 19
RAYV_OSC2_TYPE = 20
RAYV_OSC2_PITCH = 21
RAYV_OSC2_TUNE = 22
RAYV_OSC2_VOLUME = 23
RAYV_MASTER_VOLUME = 24
RAYV_MASTER_UNISON_VOICES = 25
RAYV_MASTER_UNISON_SPREAD = 26
RAYV_MASTER_GLIDE = 27
RAYV_MASTER_PITCHBEND_AMT = 28
RAYV_PITCH_ENV_TIME = 29
RAYV_PITCH_ENV_AMT = 30
RAYV_LFO_FREQ = 31
RAYV_LFO_TYPE = 32
RAYV_LFO_AMP = 33
RAYV_LFO_PITCH = 34
RAYV_LFO_FILTER = 35
RAYV_OSC_HARD_SYNC = 36
RAYV_RAMP_CURVE = 37
RAYV_FILTER_KEYTRK = 38
RAYV_MONO_MODE = 39
RAYV_LFO_PHASE = 40
RAYV_LFO_PITCH_FINE = 41
RAYV_ADSR_PREFX = 42

#Port maps


# TODO at PyDAWv5:
# Remove those which don't really make sense to automate

WAYV_PORT_MAP = [
    ("Master Attack", "2", "2", "10.0", "100.0"),
    ("Master Decay", "3", "2", "10.0", "100.0"),
    ("Master Sustain", "4", "0", "-30.0", "0.0"),
    ("Master Release", "5", "2", "10.0", "200.0"),
    ("Noise Amp", "6", "0", "-60.0", "0.0"),
    ("Master Glide", "18", "2", "0.0", "200.0"),
    ("Osc1 Attack", "20", "2", "10.0", "100.0"),
    ("Osc1 Decay", "21", "2", "10.0", "100.0"),
    ("Osc1 Sustain", "22", "0", "-30.0", "0.0"),
    ("Osc1 Release", "23", "2", "10.0", "200.0"),
    ("Osc2 Attack", "24", "2", "10.0", "100.0"),
    ("Osc2 Decay", "25", "2", "10.0", "100.0"),
    ("Osc2 Sustain", "26", "0", "-30.0", "0.0"),
    ("Osc2 Release", "27", "2", "10.0", "200.0"),
    ("ADSR1 Attack", "28", "2", "10.0", "100.0"),
    ("ADSR1 Decay", "29", "2", "10.0", "100.0"),
    ("ADSR1 Sustain", "30", "0", "-60.0", "0.0"),
    ("ADSR1 Release", "31", "2", "10.0", "200.0"),
    ("ADSR2 Attack", "32", "2", "10.0", "100.0"),
    ("ADSR2 Sustain", "34", "2", "0.0", "100.0"),
    ("ADSR2 Release", "35", "2", "10.0", "200.0"),
    ("Pitch Env Time", "37", "2", "0.0", "200.0"),
    ("LFO Freq", "38", "2", "10.0", "1600.0"),
    ("FX0 Knob0", "40", "0", "0.0", "127.0"),
    ("FX0 Knob1", "41", "0", "0.0", "127.0"),
    ("FX0 Knob2", "42", "0", "0.0", "127.0"),
    ("FX1 Knob0", "44", "0", "0.0", "127.0"),
    ("FX1 Knob1", "45", "0", "0.0", "127.0"),
    ("FX1 Knob2", "46", "0", "0.0", "127.0"),
    ("FX2 Knob0", "48", "0", "0.0", "127.0"),
    ("FX2 Knob1", "49", "0", "0.0", "127.0"),
    ("FX2 Knob2", "50", "0", "0.0", "127.0"),
    ("FX3 Knob0", "52", "0", "0.0", "127.0"),
    ("FX3 Knob1", "53", "0", "0.0", "127.0"),
    ("FX3 Knob2", "54", "0", "0.0", "127.0"),
    ("LFO Amp", "107", "0", "-24.0", "24.0"),
    ("LFO Pitch", "108", "0", "-36.0", "36.0"),
    ("LFO Pitch Fine", WAYV_LFO_PITCH_FINE, "0", "-100.0", "100.0"),
    ("Pitch Env Amt", "109", "0", "-36.0", "36.0"),
    ("LFO Amount", "112", "2", "0.0", "100.0"),
    ("Osc1 FM1", "119", "0", "0.0", "100.0"),
    ("Osc1 FM2", "120", "0", "0.0", "100.0"),
    ("Osc1 FM3", "121", "0", "0.0", "100.0"),
    ("Osc2 FM1", "122", "0", "0.0", "100.0"),
    ("Osc2 FM2", "123", "0", "0.0", "100.0"),
    ("Osc2 FM3", "124", "0", "0.0", "100.0"),
    ("Osc1 FM1", "125", "0", "0.0", "100.0"),
    ("Osc1 FM2", "126", "0", "0.0", "100.0"),
    ("Osc1 FM3", "127", "0", "0.0", "100.0"),
    ("Osc3 Attack", "128", "2", "10.0", "100.0"),
    ("Osc3 Decay", "129", "2", "10.0", "100.0"),
    ("Osc3 Sustain", "130", "0", "-30.0", "0.0"),
    ("Osc3 Release time", "131", "2", "10.0", "200.0"),
    ("FM Macro 1", WAYV_FM_MACRO1, "2", "0.0", "100.0"),
    ("FM Macro 2", WAYV_FM_MACRO2, "2", "0.0", "100.0")
]

RAYV_PORT_MAP = [
    ("Attack time (s)", "2", "2", "10.0", "100.0"),
    ("Decay time (s)", "3", "2", "10.0", "100.0"),
    ("Sustain level (%)", "4", "0", "-60.0", "0.0"),
    ("Release time (s)", "5", "2", "10.0", "200.0"),
    ("Filter Cutoff", "6", "1", "20.0", "124.0"),
    ("Res", "7", "0", "-30.0", "0.0"),
    ("Dist", "8", "0", "-6.0", "36.0"),
    ("Attack time (s) filter", "9", "2", "10.0", "100.0"),
    ("Decay time (s) filter", "10", "2", "10.0", "100.0"),
    ("Sustain level (%) filter", "11", "2", "0.0", "100.0"),
    ("Release time (s) filter", "12", "2", "10.0", "200.0"),
    ("Noise Amp", "13", "0", "-60.0", "0.0"),
    ("Filter Env Amt", "14", "0", "-36.0", "36.0"),
    ("Dist Wet", "15", "2", "0.0", "100.0"),
    ("Master Glide", "27", "2", "0.0", "200.0"),
    ("Pitch Env Time", "29", "2", "0.0", "200.0"),
    ("Pitch Env Amt", "30", "0", "-36.0", "36.0"),
    ("LFO Freq", "31", "2", "10.0", "400.0"),
    ("LFO Amp", "33", "0", "-24.0", "24.0"),
    ("LFO Pitch", "34", "0", "-36.0", "36.0"),
    ("LFO Pitch Fine", RAYV_LFO_PITCH_FINE, "0", "-100.0", "100.0"),
    ("LFO Filter", "35", "0", "-48.0", "48.0")
]


MODULEX_PORT_MAP = [
    ("FX0 Knob0", "4", "0", "0.0", "127.0"),
    ("FX0 Knob1", "5", "0", "0.0", "127.0"),
    ("FX0 Knob2", "6", "0", "0.0", "127.0"),
    ("FX1 Knob0", "8", "0", "0.0", "127.0"),
    ("FX1 Knob1", "9", "0", "0.0", "127.0"),
    ("FX1 Knob2", "10", "0", "0.0", "127.0"),
    ("FX2 Knob0", "12", "0", "0.0", "127.0"),
    ("FX2 Knob1", "13", "0", "0.0", "127.0"),
    ("FX2 Knob2", "14", "0", "0.0", "127.0"),
    ("FX3 Knob0", "16", "0", "0.0", "127.0"),
    ("FX3 Knob1", "17", "0", "0.0", "127.0"),
    ("FX3 Knob2", "18", "0", "0.0", "127.0"),
    ("FX4 Knob0", "20", "0", "0.0", "127.0"),
    ("FX4 Knob1", "21", "0", "0.0", "127.0"),
    ("FX4 Knob2", "22", "0", "0.0", "127.0"),
    ("FX5 Knob0", "24", "0", "0.0", "127.0"),
    ("FX5 Knob1", "25", "0", "0.0", "127.0"),
    ("FX5 Knob2", "26", "0", "0.0", "127.0"),
    ("FX6 Knob0", "28", "0", "0.0", "127.0"),
    ("FX6 Knob1", "29", "0", "0.0", "127.0"),
    ("FX6 Knob2", "30", "0", "0.0", "127.0"),
    ("FX7 Knob0", "32", "0", "0.0", "127.0"),
    ("FX7 Knob1", "33", "0", "0.0", "127.0"),
    ("FX7 Knob2", "34", "0", "0.0", "127.0"),
    ("Delay Feedback", "37", "0", "-15.0", "0.0"),
    ("Delay Dry", "38", "0", "-30.0", "0.0"),
    ("Delay Wet", "39", "0", "-30.0", "0.0"),
    ("Delay Duck", "40", "0", "-40.0", "0.0"),
    ("Delay LP Cutoff", "41", "0", "40.0", "118.0"),
    ("Volume Slider", "43", "0", "-50.0", "0.0"),
    ("Reverb Wet", "45", "0", "0.0", "100.0"),
    ("Reverb Color", "46", "0", "0.0", "100.0")
]


EUPHORIA_PORT_MAP = [
    ("Master Attack", "3", "2", "10.0", "100.0"),
    ("Master Decay", "4", "2", "10.0", "100.0"),
    ("Master Sustain", "5", "0", "-60.0", "0.0"),
    ("Master Release", "6", "2", "10.0", "200.0"),
    ("ADSR2 Attack", "7", "2", "10.0", "100.0"),
    ("ADSR2 Decay", "8", "2", "10.0", "100.0"),
    ("ADSR2 Sustain", "9", "2", "0.0", "100.0"),
    ("ADSR2 Release", "10", "2", "10.0", "200.0"),
    ("LFO Pitch", "11", "0", "-36.0", "36.0"),
    ("LFO Pitch Fine", EUPHORIA_LFO_PITCH_FINE, "0", "-100.0", "100.0"),
    ("Master Glide", "13", "2", "0.0", "200.0"),
    ("Pitch Env Time", "15", "2", "0.0", "200.0"),
    ("LFO Freq", "16", "2", "10.0", "1600.0"),
    ("FX0 Knob0", "18", "0", "0.0", "127.0"),
    ("FX0 Knob1", "19", "0", "0.0", "127.0"),
    ("FX0 Knob2", "20", "0", "0.0", "127.0"),
    ("FX1 Knob0", "22", "0", "0.0", "127.0"),
    ("FX1 Knob1", "23", "0", "0.0", "127.0"),
    ("FX1 Knob2", "24", "0", "0.0", "127.0"),
    ("FX2 Knob0", "26", "0", "0.0", "127.0"),
    ("FX2 Knob1", "27", "0", "0.0", "127.0"),
    ("FX2 Knob2", "28", "0", "0.0", "127.0"),
    ("FX3 Knob0", "30", "0", "0.0", "127.0"),
    ("FX3 Knob1", "31", "0", "0.0", "127.0"),
    ("FX3 Knob2", "32", "0", "0.0", "127.0"),
    #This one is kept for compatibility because it was once in here incorrectly
    #TODO:  Delete at PyDAWv5
    ("zzDeprecated ignore", "83", "0", "-36.0", "36.0")
]

_euphoria_port_mins = (EUPHORIA_MONO_FX0_KNOB0_PORT_RANGE_MIN,
                       EUPHORIA_MONO_FX1_KNOB0_PORT_RANGE_MIN,
                       EUPHORIA_MONO_FX2_KNOB0_PORT_RANGE_MIN,
                       EUPHORIA_MONO_FX3_KNOB0_PORT_RANGE_MIN)

for f_fx in range(4):
    f_port_iter = _euphoria_port_mins[f_fx]
    for f_knob in range(3):
        for f_group in range(1, EUPHORIA_MAX_SAMPLE_COUNT + 1):
            f_group_str = str(f_group).zfill(3)
            EUPHORIA_PORT_MAP.append((
                "Mono FX{} Knob{} Group {}".format(f_fx, f_knob, f_group_str),
                str(f_port_iter), "0", "0.0", "127.0"))
            f_port_iter += 1
