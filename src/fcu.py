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
from config import Config

# IMPORTANT: This must be run as administrator (PowerShell on Windows) or it will encounter a write error.

class Fcu:
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config
        
        self.logger = logging.getLogger("FCU")

        # FCU DLL Loading
        self.dll_path = self.config.dll_path
        self.dll_filename = self.config.dll_filename
        self.dll_filepath = (os.path.join(self.dll_path, self.dll_filename))
        self.logger.info("Loading dll '{}'".format(self.dll_filepath))
        try:
            self.lib = ctypes.CDLL(self.dll_filepath)
        except Exception as e:
            self.logger.err(e)

        # Setup callback references. 
        # *** Important: these must stay alive for the duration of the script or the DLL will not work **
        # @todo: include reference for ^
        self.callback_refs = {}
    
    
        # The delegate sub for win32 debug (text) c
        #Public Delegate Sub DEBUG_PRINTF__CallbackDelegate(ByVal pu8String As IntPtr)
        # The debugger callback
        #Private Shared Sub vDEBUG_PRINTF_WIN32__Set_Callback(ByVal callback As MulticastDelegate)

        """
        # Set the function in the dll
        debug_printf_callback = ctypes.CFUNCTYPE(None, ctypes.c_char_p)  # Returns nothing, takes a char*

        vDEBUG_PRINTF_WIN32__Set_Callback = lib.vDEBUG_PRINTF_WIN32__Set_Callback
        vDEBUG_PRINTF_WIN32__Set_Callback.argtypes = [debug_printf_callback]
        vDEBUG_PRINTF_WIN32__Set_Callback.restype = None
        vDEBUG_PRINTF_WIN32__Set_Callback.errcheck = errcheck_callback

        # Define the python function that we'll use for the callback
        def debug_printf(val):
            print "Python Debug printf callback called with value '{}'".format(val)
    
        # reference the callback to keep it alive
        _debug_printf_callback = debug_printf_callback(debug_printf)

        # Pass in our referenced python function to the dll function
        vDEBUG_PRINTF_WIN32__Set_Callback(_debug_printf_callback)

        """
        
        self.register_callback(self.debug_printf, "vDEBUG_PRINTF_WIN32__Set_Callback", None, [ctypes.c_char_p])


    def debug_printf(self, message):
        print "FCU.debug_printf() received {}".format(message)
    
    def register_callback(self, python_function, dll_function_name, restype, args):
        # Create the callback functype
        callback_functype = ctypes.CFUNCTYPE(restype, *args)

        # Set the attributes on the method
        dll_method = getattr(self.lib, dll_function_name)
        dll_method.argtypes = [callback_functype]
        dll_method.restype = restype
        
        # reference the callback to keep it alive
        self.callback_refs[dll_function_name] = callback_functype(python_function)
        
        # Call the method on the dll and pass in our reference
        dll_method(self.callback_refs[dll_function_name])


        """
        vSTEPDRIVE_WIN32__UpdatePositionCallback = ctypes.CFUNCTYPE(None, ctypes.c_ubyte, ctypes.c_ubyte, ctypes.c_ubyte, ctypes.c_int32)
        vSTEPDRIVE_WIN32__Set_UpdatePositionCallback = lib.vSTEPDRIVE_WIN32__Set_UpdatePositionCallback
        vSTEPDRIVE_WIN32__Set_UpdatePositionCallback.argtypes = [vSTEPDRIVE_WIN32__UpdatePositionCallback]
        vSTEPDRIVE_WIN32__Set_UpdatePositionCallback.restype = None
        
        Ethernet_TxCallback = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint16)
        vETH_WIN32__Set_Ethernet_TxCallback = lib.vETH_WIN32__Set_Ethernet_TxCallback
        vETH_WIN32__Set_Ethernet_TxCallback.argtypes = [Ethernet_TxCallback]
        vETH_WIN32__Set_Ethernet_TxCallback.restype = None
        """
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    config = Config()
    config.dll_path = "../eng-software-pod/APPLICATIONS/PROJECT_CODE/DLLS/LDLL174__RLOOP__LCCM655/bin/Debug/"  # Relative to top level of this repo (../)
    config.dll_filename = "LDLL174__RLOOP__LCCM655.dll"

    fcu = Fcu(None, config)
    
    fcu.lib.vFCU__Init()  # Should get a debug message back
    
    """
    lib = ctypes.CDLL(dll_filepath)
    
    print dir(lib)
    """