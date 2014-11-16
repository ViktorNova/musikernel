import mkplugins.euphoria
import mkplugins.rayv
import mkplugins.wayv
import mkplugins.modulex
import mkplugins.mk_channel
import mkplugins.mk_delay
import mkplugins.mk_eq
import mkplugins.simple_fader
import mkplugins.simple_reverb
import mkplugins.sidechain_comp
import mkplugins.trigger_fx
import mkplugins.xfade
import mkplugins.mk_compressor
import mkplugins.mk_vocoder

PLUGIN_INSTRUMENT_COUNT = 3  # For inserting the split line into the menu

PLUGIN_NAMES = [
    "Euphoria", "Ray-V", "Way-V", "MK Channel", "MK Compressor",
    "MK Delay", "MK EQ", "MK Vocoder", "Modulex", "Sidechain Comp.",
    "Simple Fader", "Simple Reverb", "TriggerFX", "X-Fade",
    ]
PLUGIN_UIDS = {
    "None":0, "Euphoria":1, "Ray-V":2, "Way-V":3, "Modulex":4, "MK Delay":5,
    "MK EQ":6, "Simple Fader":7, "Simple Reverb":8, "TriggerFX":9,
    "Sidechain Comp.":10, "MK Channel":11, "X-Fade":12, "MK Compressor":13,
    "MK Vocoder":14,
    }
WAVE_EDITOR_PLUGIN_NAMES = [
    "None", "MK Channel", "MK Compressor", "MK Delay", "MK EQ",
    "Modulex", "Simple Fader", "Simple Reverb"
    ]

MIXER_PLUGIN_NAMES = ["None", "Simple Fader", "MK Channel"]
PLUGIN_UIDS_REVERSE = {v:k for k, v in PLUGIN_UIDS.items()}
CC_NAMES = {x:[] for x in PLUGIN_NAMES}
CONTROLLER_PORT_NAME_DICT = {x:{} for x in PLUGIN_NAMES}
CONTROLLER_PORT_NUM_DICT = {x:{} for x in PLUGIN_NAMES}

PLUGIN_UI_TYPES = {
    1:mkplugins.euphoria.euphoria_plugin_ui,
    2:mkplugins.rayv.rayv_plugin_ui,
    3:mkplugins.wayv.wayv_plugin_ui,
    4:mkplugins.modulex.modulex_plugin_ui,
    5:mkplugins.mk_delay.mkdelay_plugin_ui,
    6:mkplugins.mk_eq.mkeq_plugin_ui,
    7:mkplugins.simple_fader.sfader_plugin_ui,
    8:mkplugins.simple_reverb.sreverb_plugin_ui,
    9:mkplugins.trigger_fx.triggerfx_plugin_ui,
    10:mkplugins.sidechain_comp.scc_plugin_ui,
    11:mkplugins.mk_channel.mkchnl_plugin_ui,
    12:mkplugins.xfade.xfade_plugin_ui,
    13:mkplugins.mk_compressor.mk_comp_plugin_ui,
    14:mkplugins.mk_vocoder.mk_vocoder_plugin_ui,
}

PORTMAP_DICT = {
    "Euphoria":mkplugins.euphoria.EUPHORIA_PORT_MAP,
    "Way-V":mkplugins.wayv.WAYV_PORT_MAP,
    "Ray-V":mkplugins.rayv.RAYV_PORT_MAP,
    "Modulex":mkplugins.modulex.MODULEX_PORT_MAP,
    "MK Channel":mkplugins.mk_channel.MKCHNL_PORT_MAP,
    "MK Compressor":mkplugins.mk_compressor.MK_COMP_PORT_MAP,
    "MK Delay":mkplugins.mk_delay.MKDELAY_PORT_MAP,
    "MK EQ":mkplugins.mk_eq.MKEQ_PORT_MAP,
    "Simple Fader":mkplugins.simple_fader.SFADER_PORT_MAP,
    "Simple Reverb":mkplugins.simple_reverb.SREVERB_PORT_MAP,
    "TriggerFX":mkplugins.trigger_fx.TRIGGERFX_PORT_MAP,
    "Sidechain Comp.":mkplugins.sidechain_comp.SCC_PORT_MAP,
    "X-Fade":mkplugins.xfade.XFADE_PORT_MAP,
    "MK Vocoder":mkplugins.mk_vocoder.MK_VOCODER_PORT_MAP,
}

def get_plugin_uid_by_name(a_name):
    return PLUGIN_UIDS[str(a_name)]

class pydaw_controller_map_item:
    def __init__(self, a_name, a_port):
        self.name = str(a_name)
        self.port = int(a_port)

def pydaw_load_controller_maps():
    for k, v in PORTMAP_DICT.items():
        for k2, v2 in v.items():
            f_map = pydaw_controller_map_item(k2, v2)
            CONTROLLER_PORT_NAME_DICT[k][k2] = f_map
            CONTROLLER_PORT_NUM_DICT[k][int(v2)] = f_map
            CC_NAMES[k].append(k2)
        CC_NAMES[k].sort()

pydaw_load_controller_maps()
