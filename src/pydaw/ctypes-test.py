#!/usr/bin/python3

import ctypes
import threading
import time

ENGINE_LIB = None

def engine_callback(a_path, a_msg):
    print("It works!!!")
    print(a_path.decode("utf-8"))
    print(a_msg.decode("utf-8"))

def load_engine_lib(a_engine_callback):
    global ENGINE_LIB
    ENGINE_LIB = ctypes.CDLL("./musikernel1.so")
    ENGINE_LIB.main.restype = ctypes.c_int
    ENGINE_LIB.main.argstype = [ctypes.c_int, ctypes.POINTER(ctypes.c_char_p)]
    ENGINE_LIB.v_configure.argstype = [
        ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
    ENGINE_LIB.v_configure.restype = ctypes.c_int
    func_sig = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_char_p)
    func_ptr = func_sig(a_engine_callback)
    ENGINE_LIB.v_set_ui_callback.restype = None
    ENGINE_LIB.v_set_ui_callback(func_ptr)

def start_engine_lib(a_prefix, a_project_dir, a_hugepages):
    myargv = ctypes.c_char_p * 5
    argv = myargv(
        b"/usr/bin/musikernel1-engine", a_prefix.encode("ascii"),
        a_project_dir.encode("ascii"), b"0", a_hugepages.encode("ascii"))
    thread = threading.Thread(
        target=ENGINE_LIB.main, args=(5, ctypes.byref(argv)))
    thread.start()

def engine_lib_configure(a_path, a_key, a_val):
    ENGINE_LIB.v_configure(
        a_path.encode("ascii"), a_key.encode("ascii"), a_val.encode("ascii"))

load_engine_lib(engine_callback)
start_engine_lib("/usr", "/home/userbuntu/musikernel1/default-project", "1")

time.sleep(5)

engine_lib_configure("/musikernel/master", "exit", "")

time.sleep(5)
