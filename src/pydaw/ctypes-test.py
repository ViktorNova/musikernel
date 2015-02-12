#!/usr/bin/python3

import ctypes

mk = ctypes.CDLL("./musikernel1.so")
mk.main.restype = ctypes.c_int
mk.main.argstype = [ctypes.c_int, ctypes.POINTER(ctypes.c_char_p)]

myargv = ctypes.c_char_p * 5
argv = myargv(
    b"/usr/bin/musikernel1-engine", b"/usr",
    b"/home/userbuntu/musikernel1/default-project", b"7957", b"1")
argc = ctypes.c_int(5)

mk.main(5, ctypes.byref(argv))

