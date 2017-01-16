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

        # Load the DLL
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
    
        # ------------------------
        #  Register Callbacks
        # ------------------------
        
        # debug_printf
        # The debugger callback
        #Public Delegate Sub DEBUG_PRINTF__CallbackDelegate(ByVal pu8String As IntPtr)
        #Private Shared Sub vDEBUG_PRINTF_WIN32__Set_Callback(ByVal callback As MulticastDelegate)
        self.register_callback(self.debug_printf_callback, 
            'vDEBUG_PRINTF_WIN32__Set_Callback', None, 
            [ctypes.c_char_p])
        
        # 'Ethernet
        # Public Shared Sub vETH_WIN32__Set_Ethernet_TxCallback(ByVal callback As MulticastDelegate)
        # Public Delegate Sub ETH_WIN32__TxCallbackDelegate(ByVal pu8Buffer As IntPtr, ByVal u16BufferLength As UInt16)
        self.register_callback(self.eth_tx_callback, 
            'vETH_WIN32__Set_Ethernet_TxCallback', None, 
            [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint16])

        # 'mma8451
        # Public Shared Sub vMMA8451_WIN32__Set_ReadDataCallback(ByVal callback As MulticastDelegate)
        # Public Delegate Sub MMA8451_WIN32__ReadDataCallbackDelegate(u8DeviceIndex As Byte, pu8X As IntPtr, pu8Y As IntPtr, pu8Z As IntPtr)
        self.register_callback(self.MMA8451_readdata_callback, 
            'vMMA8451_WIN32__Set_ReadDataCallback', None, 
            [ctypes.c_ubyte, ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8)])
        
        # 'stepper system
        # Public Shared Sub vSTEPDRIVE_WIN32__Set_UpdatePositionCallback(ByVal callback As MulticastDelegate)
        # Public Delegate Sub STEPDRIVE_WIN32__Set_UpdatePositionCallbackDelegate(u8MotorIndex As Byte, u8Step As Byte, u8Dir As Byte, s32Position As Int32)
        self.register_callback(self.stepdrive_update_position_callback, 
            'vSTEPDRIVE_WIN32__Set_UpdatePositionCallback', None, 
            [ctypes.c_ubyte, ctypes.c_ubyte, ctypes.c_ubyte, ctypes.c_int32])

        # 'SC16 UARTS
        # Public Shared Sub vSC16IS_WIN32__Set_TxData_Callback(u8DeviceIndex As Byte, ByVal callback As MulticastDelegate)
        # Public Delegate Sub SC16IS_WIN32__Set_TxData_CallbackDelegate(u8DeviceIndex As Byte, pu8Data As IntPtr, u8Length As Byte)
        self.register_callback(self.SC16IS_txdata_callback, 
            'vSC16IS_WIN32__Set_TxData_Callback', None,
            [ctypes.c_uint8, ctypes.POINTER(c_uint8), ctypes.c_uint8])
        
        # 'AMC7812 for HE Thrott
        # Public Delegate Sub AMC7812_WIN32__Set_DACVoltsCallbackDelegate(u8Channel As Byte, f32Volts As Single)
        # Public Shared Sub vAMC7812_WIN32__Set_DACVoltsCallback(ByVal callback As MulticastDelegate)
        self.register_callback(self.AMC7812_DAC_volts_callback, 
            'AMC7812_WIN32__Set_DACVoltsCallbackDelegate', None,
            [ctypes.c_uint8, ctypes.c_float32])
        
        # ------------------------
        #  Callable Functions
        # ------------------------

        # '''Debugging / Testing / Simulating
        
        # Public Shared Sub vETH_WIN32__Ethernet_Input(pu8Buffer() As Byte, u16BufferLength As UInt16)
        # Public Shared Sub vMMA8451_WIN32__TriggerInterrupt(u8DeviceIndex As Byte)
        # Public Shared Sub vSTEPDRIVE_WIN32__ForcePosition(u8MotorIndex As Byte, s32Position As Int32)
        # Public Shared Sub vSC16IS_WIN32__InjectData(u8DeviceIndex As Byte, pu8Data() As Byte, u8Length As Byte)

        # '''Running
        
        # 'Control and Timing
        # Private Shared Sub vFCU__Init()
        # Private Shared Sub vFCU__Process()
        # Private Shared Sub vFCU__RTI_10MS_ISR()
        # Private Shared Sub vFCU__RTI_100MS_ISR()
        # Private Shared Sub vSTEPDRIVE_TIMEBASE__ISR()   # Note: 50usec
        
        # 'Laser Distance
        # Private Shared Sub vFCU_LASERDIST_WIN32__Set_DistanceRaw(f32Value As Single)

        # 'laser optoncdt
        # Private Shared Sub vFCU_LASEROPTO_WIN32__Set_DistanceRaw(u32Index As UInt32, f32Value As Single)
        
        # 'brake switches
        # Private Shared Sub vFCU_BRAKES_SW_WIN32__Inject_SwitchState(u8Brake As Byte, u8ExtendRetract As Byte, u8Value As Byte)
        # Private Shared Sub vFCU_BRAKES_SW__Left_SwitchExtend_ISR()
        # Private Shared Sub vFCU_BRAKES_SW__Left_SwitchRetract_ISR()
        # Private Shared Sub vFCU_BRAKES_SW__Right_SwitchExtend_ISR()
        # Private Shared Sub vFCU_BRAKES_SW__Right_SwitchRetract_ISR()
        
        # 'MLP
        # Private Shared Sub vFCU_BRAKES_MLP_WIN32__ForceADC(u8Brake As Byte, u16Value As UInt16)

        # 'ASI
        # Private Shared Function u8FCU_ASI_MUX_WIN32__Get() As Byte
        # Private Shared Function u16FCU_ASI_CRC__ComputeCRC(pu8Data() As Byte, u16DataLen As UInt16) As UInt16

        # 'Testing Area
        # Private Shared Sub vLCCM655R0_TS_000()
        # Private Shared Sub vLCCM655R0_TS_001()
        # Private Shared Sub vLCCM655R0_TS_002()
        # Private Shared Sub vLCCM655R0_TS_003()
        # Private Shared Sub vLCCM655R0_TS_004()
        # Private Shared Sub vLCCM655R0_TS_005()
        # Private Shared Sub vLCCM655R0_TS_006()


        
    def debug_printf_callback(self, message):
        # Public Delegate Sub DEBUG_PRINTF__CallbackDelegate(ByVal pu8String As IntPtr)
        self.logger.debug("Fcu.debug_printf('{}')".format(message))

    def eth_tx_callback(self, pu8Buffer, u16BufferLength):
        # Public Delegate Sub ETH_WIN32__TxCallbackDelegate(ByVal pu8Buffer As IntPtr, ByVal u16BufferLength As UInt16)
        # @todo: Format the buffer so it's readable (bytes)
        self.logger.debug("Fcu.eth_tx_callback('{}', {})".format(pu8Buffer, u16BufferLength))

    def MMA8451_readdata_callback(self, u8DeviceIndex, pu8X, pu8Y, pu8Z):
        # Public Delegate Sub MMA8451_WIN32__ReadDataCallbackDelegate(u8DeviceIndex As Byte, pu8X As IntPtr, pu8Y As IntPtr, pu8Z As IntPtr)
        self.logger.debug("Fcu.MMA8451_readdata_callback({}, {}, {}, {})".format(u8DeviceIndex, pu8X, pu8Y, pu8Z))

    def stepdrive_update_position_callback(self, u8MotorIndex, u8Step, u8Dir, s32Position):
        # Public Delegate Sub STEPDRIVE_WIN32__Set_UpdatePositionCallbackDelegate(u8MotorIndex As Byte, u8Step As Byte, u8Dir As Byte, s32Position As Int32)
        self.logger.debug("Fcu.stepdrive_update_position_callback({}, {}, {}, {})".format(u8MotorIndex, u8Step, u8Dir, s32Position))

    def SC16IS_txdata_callback(self, u8DeviceIndex, pu8Data, u8Length):
        # Public Delegate Sub SC16IS_WIN32__Set_TxData_CallbackDelegate(u8DeviceIndex As Byte, pu8Data As IntPtr, u8Length As Byte)
        self.logger.debug("Fcu.SC16IS_txdata_callback({}, {}, {})".format(u8DeviceIndex, pu8Data, u8Length))

    def AMC7812_DAC_volts_callback(self, u8Channel, f32Volts):
        # Public Delegate Sub AMC7812_WIN32__Set_DACVoltsCallbackDelegate(u8Channel As Byte, f32Volts As Single)
        self.logger.debug("Fcu.AMC7812_DAC_volts_callback({}, {})".format(u8Channel, f32Volts))

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
        Example (manual version):
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