#!/usr/bin/python3

import ctypes

mk = ctypes.CDLL("./musikernel1.so")
mk.main.restype = ctypes.c_int
mk.main.argstype = [ctypes.c_int, ctypes.POINTER(ctypes.c_char_p)]

func_sig = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_char_p)

def engine_callback(a_path, a_msg):
    print("It works!!!")
    print(a_path.decode("utf-8"))
    print(a_msg.decode("utf-8"))

func_ptr = func_sig(engine_callback)

#mk.v_set_ui_callback.argstype = [func_sig]
mk.v_set_ui_callback.restype = None

mk.v_set_ui_callback(func_ptr)

myargv = ctypes.c_char_p * 5
argv = myargv(
    b"/usr/bin/musikernel1-engine", b"/usr",
    b"/home/userbuntu/musikernel1/default-project", b"7957", b"1")

mk.main(5, ctypes.byref(argv))

