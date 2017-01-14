#!/usr/bin/env python

"""
This should really be a wrapper (or similar) around the DLL that is our actual firmware.
- What to call when? The timers (10ms and 100ms) for processing loops? 
- How to get data in and out? How does the firmware pick up what we're dropping off? What about interrupts?
- We want to log data independent of what the FCU/firmware is going, and we want to log data *about* the fcu/firmware
- The sensors will likely need to put data directly to the firmware by calling c functions. Maybe wrap those functions so we can do our own logging separately? 
    - Or sometimes the sensor get called back by the FCU to give up their data. They'll probably need a queue of some sort...
- Also we'll want to do things like check state in the FCU from time to time. How to do that? Can we access the strFCU from python? How often? 10ms? 
- 
"""

import logging
import sys
import os
import ctypes
import pprint

class Fcu:
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config
        
        self.logger = logging.getLogger("FCU")

        # FCU DLL Loading
        self.dll_path = self.config.dll_path
        self.dll_filename = self.config.dll_filename
        self.lib = self.load_dll(os.path.join(dll_path, dll_filename))

        # Setup callback references. 
        # *** Important: these must stay alive for the duration of the script or the DLL will not work **
        # @todo: include reference for ^
        self.callback_refs = {}
        
    def register_callback(name, args, pyton_function):
        self.

        vSTEPDRIVE_WIN32__UpdatePositionCallback = ctypes.CFUNCTYPE(None, ctypes.c_ubyte, ctypes.c_ubyte, ctypes.c_ubyte, ctypes.c_int32)
        vSTEPDRIVE_WIN32__Set_UpdatePositionCallback = lib.vSTEPDRIVE_WIN32__Set_UpdatePositionCallback
        vSTEPDRIVE_WIN32__Set_UpdatePositionCallback.argtypes = [vSTEPDRIVE_WIN32__UpdatePositionCallback]
        vSTEPDRIVE_WIN32__Set_UpdatePositionCallback.restype = None