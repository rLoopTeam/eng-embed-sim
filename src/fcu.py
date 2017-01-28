#!/usr/bin/env python
# coding=UTF-8

# File:     fcu.py
# Purpose:  Flight Control Unit -- Interface and controls for the compiled FCU DLL
#           @see https://github.com/rLoopTeam/eng-software-pod, APPLICATIONS/PROJECT_CODE/DLLS/LDLL174__RLOOP__LCCM655/bin/Debug/LDLL174__RLOOP__LCCM655.dll
# Author:   Ryan Adams (radams@cyandata.com, @ninetimeout)
# Date:     2016-Dec-28


# @see https://github.com/rLoopTeam/eng-software-pod/blob/development/APPLICATIONS/LAPP185__RLOOP__FCU_EMU/Form1.vb
# @see https://github.com/rLoopTeam/eng-software-pod/blob/development/APPLICATIONS/PROJECT_CODE/DLLS/LDLL174__RLOOP__LCCM655/bin/Debug/LDLL174__RLOOP__LCCM655.dll

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

from timers import Timer
import time
import threading
import struct
import bitstring

# Our stuff
from config import Config
from units import Units
from networking import PodComms, UdpListener
from sensors import QueueingListener

# IMPORTANT: This must be run as administrator (PowerShell on Windows) or it will encounter a write error.



class Fcu:
    
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config
        
        self.logger = logging.getLogger("FCU")

        self.logger.info("Initializing FCU")

        # Timers for various callbacks 
        self.timers = []

        # TESTING ONLY @todo: this should probably come from self.sim.networking
        #self.comms = PodComms(self, self.sim.config.networking)

        # Load the DLL
        self.dll_path = self.config.dll_path
        self.dll_filename = self.config.dll_filename
        self.dll_filepath = (os.path.join(self.dll_path, self.dll_filename))
        self.logger.info("- Loading dll '{}'".format(self.dll_filepath))
        try:
            self.lib = ctypes.CDLL(self.dll_filepath)
        except Exception as e:
            self.logger.error(e)

        # constants
        self.C_NUM__SC16IS = 8
        self.C_NUM__ASI = 8

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
        # @see FIRMWARE/COMMON_CODE/MULTICORE/LCCM325__MULTICORE__802_3/eth.h
        # typedef void (__cdecl * pETH_WIN32__TxCallback_FuncType)(Luint8 * pu8Buffer, Luint16 u16BufferLength);
        self.register_callback(self.eth_tx_callback, 
            'vETH_WIN32__Set_Ethernet_TxCallback', None, 
            [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint16])

        # 'mma8451
        # Public Shared Sub vMMA8451_WIN32__Set_ReadDataCallback(ByVal callback As MulticastDelegate)
        # Public Delegate Sub MMA8451_WIN32__ReadDataCallbackDelegate(u8DeviceIndex As Byte, pu8X As IntPtr, pu8Y As IntPtr, pu8Z As IntPtr)
        # @see FIRMWARE/COMMON_CODE/MULTICORE/LCCM418__MULTICORE__MMA8451/mma8451.h
        # void vMMA8451_WIN32__ReadData(Luint8 u8DeviceIndex, Lint16 *ps16X, Lint16 *ps16Y, Lint16 *ps16Z);
        self.register_callback(self.MMA8451_readdata_callback, 
            'vMMA8451_WIN32__Set_ReadDataCallback', None, 
            [ctypes.c_uint8, ctypes.POINTER(ctypes.c_int16), ctypes.POINTER(ctypes.c_int16), ctypes.POINTER(ctypes.c_int16)])

        # 'stepper system
        # Public Shared Sub vSTEPDRIVE_WIN32__Set_UpdatePositionCallback(ByVal callback As MulticastDelegate)
        # Public Delegate Sub STEPDRIVE_WIN32__Set_UpdatePositionCallbackDelegate(u8MotorIndex As Byte, u8Step As Byte, u8Dir As Byte, s32Position As Int32)
        # @see FIRMWARE/COMMON_CODE/MULTICORE/LCCM231__MULTICORE__STEPPER_DRIVE/stepper_drive.h
        # typedef void (__cdecl * pSTEPDRIVE_WIN32__UpdatePosCallback_FuncType)(Luint8 u8MotorIndex, Luint8 u8Step, Luint8 u8Dir, Lint32 s32Position);
        self.register_callback(self.stepdrive_update_position_callback, 
            'vSTEPDRIVE_WIN32__Set_UpdatePositionCallback', None, 
            [ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_int32])

        # 'SC16 UARTS
        # Public Shared Sub vSC16IS_WIN32__Set_TxData_Callback(u8DeviceIndex As Byte, ByVal callback As MulticastDelegate)
        # Public Delegate Sub SC16IS_WIN32__Set_TxData_CallbackDelegate(u8DeviceIndex As Byte, pu8Data As IntPtr, u8Length As Byte)
        # @see FIRMWARE/COMMON_CODE/MULTICORE/LCCM487__MULTICORE__SC16IS741/sc16.h
        # void vSC16IS_WIN32__TxData(Luint8 u8DeviceIndex, Luint8 *pu8Data, Luint8 u8Length);
        # NOTE: @todo: This set callback method takes a device index -- not sure yet but I think this needs to be handled differently than the rest of the callbacks
        #    DLL_DECLARATION void vSC16IS_WIN32__Set_TxData_Callback(Luint8 u8DeviceIndex, pSC16IS_WIN32_TxData_Callback_FuncType pFunc);
        for device_index in xrange(self.C_NUM__SC16IS):
            self.register_SC16IS_callback(device_index, self.SC16IS_txdata_callback, 
                'vSC16IS_WIN32__Set_TxData_Callback', None,
                [ctypes.c_ubyte, ctypes.POINTER(ctypes.c_int), ctypes.c_ubyte])

        
        # 'AMC7812 for HE Thrott
        # Public Shared Sub vAMC7812_WIN32__Set_DACVoltsCallback(ByVal callback As MulticastDelegate)
        # Public Delegate Sub AMC7812_WIN32__Set_DACVoltsCallbackDelegate(u8Channel As Byte, f32Volts As Single)
        # @see FIRMWARE/COMMON_CODE/MULTICORE/LCCM658__MULTICORE__AMC7812/amc7812.h
        # typedef void (__cdecl * pAMC7812_WIN32__DACVoltsCallback_FuncType)(Luint8 u8Channel, Lfloat32 f32Volts);
        # DLL_DECLARATION void vAMC7812_WIN32__Set_DACVoltsCallback(pAMC7812_WIN32__DACVoltsCallback_FuncType pFunc);
        self.register_callback(self.AMC7812_DAC_volts_callback, 
            'vAMC7812_WIN32__Set_DACVoltsCallback', None,
            [ctypes.c_uint8, ctypes.c_float])

        # ------------------------
        #  Callable DLL Functions
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
        # Private Shared Sub vLCCM655R0_TS_000()  # Brakes
        # Private Shared Sub vLCCM655R0_TS_001()  # --
        # Private Shared Sub vLCCM655R0_TS_002()  # --
        # Private Shared Sub vLCCM655R0_TS_003()  # Track Contrast Sensor Database
        # Private Shared Sub vLCCM655R0_TS_004()  # --
        # Private Shared Sub vLCCM655R0_TS_005()  # --
        # Private Shared Sub vLCCM655R0_TS_006()  # Brake Lookup

        # Notes on timers:
        # Private m_pTimer10m As System.Timers.Timer -- for sensor ticks
        # Private m_pTimer100m As System.Timers.Timer -- for process loop ticks (?)
        # Private m_pTimer50u As MicroTimer -- for stepper motor ticks
        # Private m_pTimerAccel As System.Timers.Timer -- Timer to handle accels.
    
        # Notes on default values:
        # Me.m_iAccel0_X = -100
        # Me.m_iAccel0_Y = 500
        # Me.m_iAccel0_Z = 1024
        
        # Notes on SafeUDP (this is called during setup):
        # Me.m_pSafeUDP = New SIL3.SafeUDP.StdUDPLayer("127.0.0.1", 9100, "FCU_ETH_EMU", True, True)
        # AddHandler Me.m_pSafeUDP.UserEvent__UDPSafe__RxPacket, AddressOf Me.InernalEvent__UDPSafe__RxPacket
        # AddHandler Me.m_pSafeUDP.UserEvent__NewPacket, AddressOf Me.InternalEvent__NewPacket

        self.set_return_types()

    def set_return_types(self):
        """ Set the return types for various DLL methods. NOTE: You must do this or risk bad auto-conversions (e.g. int16 -2001 => int32 62259) """
        
        # DLL_DECLARATION void vSTEPDRIVE_WIN32__ForcePosition(Luint8 u8MotorIndex, Lint32 s32Position);
        self.lib.vSTEPDRIVE_WIN32__ForcePosition.argtypes = [ctypes.c_uint8, ctypes.c_int32]
        self.lib.vSTEPDRIVE_WIN32__ForcePosition.restype = None
        
        # DLL_DECLARATION Luint16 u16DAQ__Get_FIFO_Level(Luint16 u16Index);
        self.lib.u16DAQ__Get_FIFO_Level.argtypes = [ctypes.c_uint16]
        self.lib.u16DAQ__Get_FIFO_Level.restype = ctypes.c_uint16
        
        # DLL_DECLARATION Luint16 u16DAQ__Get_FIFO_Max(Luint16 u16Index);
        self.lib.u16DAQ__Get_FIFO_Max.argtypes = [ctypes.c_uint16]
        self.lib.u16DAQ__Get_FIFO_Max.restype = ctypes.c_uint16
        
        # -- Track Database -----
        
        # There is a set of trackdbs in the FCU, keyed by index (?)
        # @see https://github.com/rLoopTeam/eng-software-pod FIRMWARE/PROJECT_CODE/LCCM655__RLOOP__FCU_CORE/fcu_core.h
        
        # DLL_DECLARATION Luint32 u32FCU_FCTL_TRACKDB__Get_CurrentDB(void);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Clear_Array(void);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Get_Array(Luint8 *pu8ByteArray);
        # DLL_DECLARATION Luint16 u16FCU_FCTL_TRACKDB_WIN32__Get_StructureSize(void);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_Array(Luint8 *pu8ByteArray);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_Header(Luint32 u32Value);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_DataLength(Luint32 u32Value);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_TrackID(Luint32 u32Value);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_TrackStartXPos(Luint32 u32Value);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_TrackEndXPos(Luint32 u32Value);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_LRF_StartXPos(Luint32 u32Value);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_NumStripes(Luint32 u32Value);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_StripeStartX(Luint32 u32Index, Luint32 u32Value);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_HeaderSpare(Luint32 u32Index, Luint32 u32Value);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_Footer(Luint32 u32Value);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_Profile_PusherFrontStartPos(Luint32 u32Value);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_Profile_PusherFrontEndPos(Luint32 u32Value);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_Profile_PodFrontTargetXPos(Luint32 u32Value);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_Profile_NumSetpoints(Luint32 u32Value);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_Profile_BrakeSetpointPosX(Luint32 u32Index, Luint32 u32Value);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_Profile_BrakeSetpointVelocityX(Luint32 u32Index, Luint32 u32Value);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_Profile_Spare(Luint32 u32Index, Luint32 u32Value);
        # DLL_DECLARATION Luint16 u16FCTL_TRAKDB_WIN32__ComputeCRC(void);
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_CRC(Luint16 u16Value);

        # Note: only setting return/arg types for the special ones (returns a value, takes a pointer, etc.)

        # DLL_DECLARATION Luint32 u32FCU_FCTL_TRACKDB__Get_CurrentDB(void);
        self.lib.u32FCU_FCTL_TRACKDB__Get_CurrentDB.restype = ctypes.c_uint32
        
        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Get_Array(Luint8 *pu8ByteArray);
        # Note: call this with a byte array that will be filled with the trackdb (?)
        self.lib.vFCU_FCTL_TRACKDB_WIN32__Get_Array.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]
        
        # DLL_DECLARATION Luint16 u16FCU_FCTL_TRACKDB_WIN32__Get_StructureSize(void);
        self.lib.u16FCU_FCTL_TRACKDB_WIN32__Get_StructureSize.restype = ctypes.c_uint16

        # DLL_DECLARATION void vFCU_FCTL_TRACKDB_WIN32__Set_Array(Luint8 *pu8ByteArray);
        self.lib.vFCU_FCTL_TRACKDB_WIN32__Set_Array.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]
        
        # DLL_DECLARATION Luint16 u16FCTL_TRAKDB_WIN32__ComputeCRC(void);
        self.lib.u16FCTL_TRAKDB_WIN32__ComputeCRC.restype = ctypes.c_uint16

        # -- Laser Sensors: Contrast (reflective strips on tube walls), Distance (forward distance), and Opto (height and yaw sensors) -----
        
		# DLL_DECLARATION void vFCU_LASERCONT_TL__ISR(E_FCU__LASER_CONT_INDEX_T eLaser, Luint32 u32Register);
		# DLL_DECLARATION void vFCU_LASERDIST_WIN32__Set_DistanceRaw(Lfloat32 f32Value);
		# DLL_DECLARATION void vFCU_LASEROPTO_WIN32__Set_DistanceRaw(Luint32 u32Index, Lfloat32 f32Value);
        
        # -- Brakes -----

        # DLL_DECLARATION void vFCU_BRAKES_SW__Left_SwitchExtend_ISR(void);
        # DLL_DECLARATION void vFCU_BRAKES_SW__Left_SwitchRetract_ISR(void);
        # DLL_DECLARATION void vFCU_BRAKES_SW__Right_SwitchExtend_ISR(void);
        # DLL_DECLARATION void vFCU_BRAKES_SW__Right_SwitchRetract_ISR(void);
        # DLL_DECLARATION void vFCU_BRAKES_SW_WIN32__Inject_SwitchState(Luint8 u8Brake, Luint8 u8ExtendRetract, Luint8 u8Value);
        # DLL_DECLARATION void vFCU_BRAKES_MLP_WIN32__ForceADC(Luint8 u8Brake, Luint16 u16Value);
        
        # -- Accelerometers -----
        
        # DLL_DECLARATION void vMMA8451_WIN32__TriggerInterrupt(Luint8 u8DeviceIndex);
        # DLL_DECLARATION void vMMA8451_WIN32__Set_ReadDataCallback(pMMA8451_WIN32__ReadDataCallback_FuncType pFunc);   # Handled in __init__    
        
        #DLL_DECLARATION Lint16 s16MMA8451_FILTERING__Get_Average(Luint8 u8DeviceIndex, MMA8451__AXIS_E eAxis);
        self.lib.s16MMA8451_FILTERING__Get_Average.argtypes = [ctypes.c_uint8, ctypes.c_uint8]
        self.lib.s16MMA8451_FILTERING__Get_Average.restype = ctypes.c_int16

        # DLL_DECLARATION Lint32 s32FCU_ACCELL__Get_CurrentAccel_mmss(Luint8 u8Channel);
        self.lib.s32FCU_ACCELL__Get_CurrentAccel_mmss.argtypes = [ctypes.c_uint8]
        self.lib.s32FCU_ACCELL__Get_CurrentAccel_mmss.restype = ctypes.c_int32
        
        # DLL_DECLARATION Lint32 s32FCU_ACCELL__Get_CurrentVeloc_mms(Luint8 u8Channel);
        self.lib.s32FCU_ACCELL__Get_CurrentVeloc_mms.argtypes = [ctypes.c_uint8]
        self.lib.s32FCU_ACCELL__Get_CurrentVeloc_mms.restype = ctypes.c_int32
        
        # DLL_DECLARATION Lint32 s32FCU_ACCELL__Get_CurrentDisplacement_mm(Luint8 u8Channel);
        self.lib.s32FCU_ACCELL__Get_CurrentDisplacement_mm.argtypes = [ctypes.c_uint8]
        self.lib.s32FCU_ACCELL__Get_CurrentDisplacement_mm.restype = ctypes.c_int32
        
        
    def errcheck_callback(self, result, func, arguments):
        self.logger.debug("Fcu.errcheck_callback({}, {}, {})".format(result, func, arguments))
        
    def debug_printf_callback(self, message):
        # Public Delegate Sub DEBUG_PRINTF__CallbackDelegate(ByVal pu8String As IntPtr)
        self.logger.debug("Fcu.debug_printf('{}')".format(message))

    def eth_tx_callback(self, pu8Buffer, u16BufferLength):
        # Public Delegate Sub ETH_WIN32__TxCallbackDelegate(ByVal pu8Buffer As IntPtr, ByVal u16BufferLength As UInt16)
        # @todo: Format the buffer so it's readable (bytes)
        #test = SafeUDP.spacex_payload_from_eth2(pu8Buffer, u16BufferLength)
        #self.logger.debug("Fcu.eth_tx_callback: passing {} bytes to sim.comms".format(u16BufferLength))
        try:
            self.sim.comms.eth_tx_callback(pu8Buffer, u16BufferLength)
        except Exception as e:
            self.logger.error(e)

        # Send the packet to the node specified in the buffer (it's a UDP packet, so it just cares about the port. Send to 127.0.0.1?)
        # @todo: we might need the comms port map to send things to the right place...
    
    def handle_udp_packet(self, packet, source_address, dest_address):
        """ Receive a UDP packet from our network node (owned by the sim, see networking.py / FlightControlNode)"""
        u16PacketLength = ctypes.c_uint16(len(packet))
        u16DestPort = ctypes.c_uint16(dest_address[1])
        
        # Testing:
        #sh_no = struct.unpack("!LHH", packet[0:8])  # Network ordering
        #sh_le = struct.unpack("<LHH", packet[0:8])  # Little Endian
        #print "Handing SafeUDP packet to dest {} (sequence, type, length): Network Byte Order: ({:#010x}, {:#06x}, {:#06x}); Little Endian: ({:#08x}, {:#06x}, {:#06x})".format(dest_address, sh_no[0], sh_no[1], sh_no[2], sh_le[0], sh_le[1], sh_le[2])

        # Testing switching byte order on the packet type to get the GS to recognize the packet
        #self.logger.debug("Switching byte order of packet type -- old: {}, new: {}".format(sh_no[1], struct.unpack("!H", packet[4:6])[0]))

        #if sh_le[1] == 4097 and False:
        #    pu8Payload = ctypes.create_string_buffer(packet[0:4] + packet[5] + packet[4] + packet[6:])
        #else: 
        #    pu8Payload = ctypes.create_string_buffer(packet)
        pu8Payload = ctypes.create_string_buffer(packet)
        
        self.lib.vSAFE_UDP_RX__UDPPacket(ctypes.byref(pu8Payload), u16PacketLength, u16DestPort)
        
        # Note: If you have a full ethernet packet, you can use the following to inject it. 
        #       vSAFE_UDP_RX__UDPPacket() is much easier here since we are only handling those and we don't have to reconstruct a full ethernet packet
        # self.lib.vETH_WIN32__Ethernet_Input(packet, len(byte_array))  # Just for knowing that this is an option
                
                    
    def MMA8451_readdata_callback(self, u8DeviceIndex, ps16X, ps16Y, ps16Z):
        """ When the MMA8451 wants data from us """

        # Note: the device index indicates which device the MMA8451 is asking for (there are 2 accelerometers, indices 0 and 1. 
        #       We'll just grab the accel data from the sim and write it to the pointers. 

        #typedef void (__cdecl * pMMA8451_WIN32__ReadDataCallback_FuncType)(Luint8 u8DeviceIndex, Lint16 *ps16X, Lint16 *ps16Y, Lint16 *ps16Z);
        # Private Sub MMA8451_WIN32__ReadDataCallback_Sub(u8DeviceIndex As Byte, ps16X As IntPtr, ps16Y As IntPtr, ps16Z As IntPtr)
        #self.logger.debug("Fcu.MMA8451_readdata_callback({}, {}, {}, {})".format(u8DeviceIndex, ps16X.contents, ps16Y.contents, ps16Z.contents))
        
        # @todo: need to get this sending data from the accel sensors. Maybe have a queue to read from? 
        # Note: probably only trigger the interrupts to call this callback when we have data in the queue? 
        #pu8X.contents = ctypes.c_int(4095)
        #pu8Y.contents = ctypes.c_int(0)
        #pu8Z.contents = ctypes.c_int(-4095)
        
        # Get the listener that's queueing data for our accelerometer (and convert it to the proper raw values/types)
        # Note: we only pop one here. The timers and time dialation should make sure that the # samples and the callbacks equalize
        #pre_accel = self.lib.s32FCU_ACCELL__Get_CurrentAccel_mmss(u8DeviceIndex)
        #pre_displacement = self.lib.s32FCU_ACCELL__Get_CurrentDisplacement_mm(ctypes.c_ubyte(u8DeviceIndex))
        try:
            real_data = self.accel_listeners[u8DeviceIndex].pop()
        except IndexError as e:
            self.logger.debug(e)
            return
                        
        # Set the values
        # @TODO: What is the orientation of our accelerometers? We need to know that to be able to provide proper data...
        data = self.sim.sensors['accel'][u8DeviceIndex].to_raw(real_data)
        #self.logger.debug("Accel data from the sensor is {}".format(data))
        # Note: '.contents' and '.raw' do not work for setting the value -- use pu8X[0] = <c value> (e.g. ps16x.contents = something won't set the value)
        
        # NOTE: The physical FCU is rotated 90 degrees such that +y data-wise is +x physical (and +x is -y due to the rotation) -- see http://confluence.rloop.org/display/SD/2.+Determine+Pod+Kinematics, tube frame of reference
        #       ^ This is handled in the accel sensors themselves. See sensor_accel.py.
        ps16X[0] = ctypes.c_int16(data.x)  # Rotated 90 degrees -- +x comes in as -y
        ps16Y[0] = ctypes.c_int16(data.y)   # The data comes in where +x is +y
        ps16Z[0] = ctypes.c_int16(data.z)

        #self.logger.debug("s32FCU_ACCELL__Get_CurrentAccel_mmss({}) -- pre: {}; post: {} (mm/s^2); (should be {})".format(u8DeviceIndex, pre_accel, post_accel, data))
        #self.logger.debug("s32FCU_ACCELL__Get_CurrentDisplacement_mm({}) -- pre: {}; post: {}".format(u8DeviceIndex, pre_displacement, post_displacement))
        #self.logger.debug("Setting pu8 data in MMA8451_readdata_callback: ({}, {}, {}) - q len is now {}".format(pu8X.contents, pu8Y.contents, pu8Z.contents, len(self.accel_listeners[u8DeviceIndex].q)))

    def stepdrive_update_position_callback(self, u8MotorIndex, u8Step, u8Dir, s32Position):
        # Public Delegate Sub STEPDRIVE_WIN32__Set_UpdatePositionCallbackDelegate(u8MotorIndex As Byte, u8Step As Byte, u8Dir As Byte, s32Position As Int32)
        # u8MotorIndex: 0 or 1, left or right
        # Step is just 1, to say that a step has happened. Should probably never have a 0 (could have been falling edge)
        # Direction: 1 or 0 -- extend = 1 or 0 -- one is reversed, one is not. So delegate to the brake and allow that in config
        # Position: current lead screw position that it's moved to -- so I don't have to calculate it.
        self.logger.debug("Fcu.stepdrive_update_position_callback({}, {}, {}, {})".format(u8MotorIndex, u8Step, u8Dir, s32Position))

        pod = self.sim.pod

        # @TODO: Need to call the brake stepdrive move function
        # @todo: put the brake switch code here
        
        # .....
        
        # Brake Linear Position Sensor
        
        # vFCU_BRAKES_MLP_WIN32__ForceADC(0, CUShort(sMLP))
        self.lib.vFCU_BRAKES_MLP_WIN32__ForceADC(u8MotorIndex, pod.brakes[u8MotorIndex].get_mlp_raw())
                
        # Brake Limit Switches
        
        brake_index = u8MotorIndex  # Just for convenience -- the motor index is the same as the brake index (there is 1 motor per brake)
                
        # Note
        #void vFCU_BRAKES_SW_WIN32__Inject_SwitchState(Luint8 u8Brake, Luint8 u8ExtendRetract, Luint8 u8Value)
        
        # For clarity
        EXTEND = 1
        RETRACT = 0

        if pod.brakes[u8DeviceIndex].extend_sw_activated:
            # Inject the extend switch state and hit the ISR
            self.lib.vFCU_BRAKES_SW_WIN32__Inject_SwitchState(brake_index, EXTEND, 1)
            self.lib.vFCU_BRAKES_SW__Left_SwitchExtend_ISR()
        elif pod.brakes[u8DeviceIndex].retract_sw_activated:
            # Inject the retract switch state and hit the ISR
            self.lib.vFCU_BRAKES_SW_WIN32__Inject_SwitchState(brake_index, RETRACT, 1)
            self.lib.vFCU_BRAKES_SW__Left_SwitchRetract_ISR()
        else:
            # Set both to zero
            self.lib.vFCU_BRAKES_SW_WIN32__Inject_SwitchState(brake_index, EXTEND, 0)
            self.lib.vFCU_BRAKES_SW_WIN32__Inject_SwitchState(brake_index, RETRACT, 0)
        
        """
        '75mm
        If s32Position > 750000 Then
            vFCU_BRAKES_SW_WIN32__Inject_SwitchState(0, 1, 1)
            vFCU_BRAKES_SW__Left_SwitchExtend_ISR()
        ElseIf s32Position < -300 Then
            'fake some cal limit
            vFCU_BRAKES_SW_WIN32__Inject_SwitchState(0, 0, 1)
            vFCU_BRAKES_SW__Left_SwitchRetract_ISR()
        Else
            vFCU_BRAKES_SW_WIN32__Inject_SwitchState(0, 1, 0)
            vFCU_BRAKES_SW_WIN32__Inject_SwitchState(0, 0, 0)
        End If        
        """
        

    def SC16IS_txdata_callback(self, u8DeviceIndex, pu8Data, u8Length):
        """ When the SC16 subsystem wants to transmit """
        # Public Delegate Sub SC16IS_WIN32__Set_TxData_CallbackDelegate(u8DeviceIndex As Byte, pu8Data As IntPtr, u8Length As Byte)
        self.logger.debug("Fcu.SC16IS_txdata_callback({}, {}, {})".format(u8DeviceIndex, pu8Data, u8Length))

    def AMC7812_DAC_volts_callback(self, u8Channel, f32Volts):
        """ When the DAC voltage is updated """
        # Public Delegate Sub AMC7812_WIN32__Set_DACVoltsCallbackDelegate(u8Channel As Byte, f32Volts As Single)
        self.logger.debug("Fcu.AMC7812_DAC_volts_callback({}, {})".format(u8Channel, f32Volts))

    def register_callback(self, python_function, dll_function_name, restype, args):

        # Create the callback functype
        callback_functype = ctypes.CFUNCTYPE(restype, *args)

        # Set the attributes on the method
        dll_method = getattr(self.lib, dll_function_name)
        dll_method.argtypes = [callback_functype]
        dll_method.restype = restype
        dll_method.errcheck = self.errcheck_callback   # Maybe don't need/want this? 
        
        # reference the callback to keep it alive
        self.callback_refs[dll_function_name] = callback_functype(python_function)
        
        # Call the method on the dll and pass in our reference
        dll_method(self.callback_refs[dll_function_name])

        """
        Example (manual version):
        vSTEPDRIVE_WIN32__UpdatePositionCallback = ctypes.CFUNCTYPE(None, ctypes.c_ubyte, ctypes.c_ubyte, ctypes.c_ubyte, ctypes.c_int32)
        #vSTEPDRIVE_WIN32__Set_UpdatePositionCallback = lib.vSTEPDRIVE_WIN32__Set_UpdatePositionCallback
        lib.vSTEPDRIVE_WIN32__Set_UpdatePositionCallback.argtypes = [vSTEPDRIVE_WIN32__UpdatePositionCallback]
        vSTEPDRIVE_WIN32__Set_UpdatePositionCallback.restype = None
        
        Ethernet_TxCallback = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint16)
        vETH_WIN32__Set_Ethernet_TxCallback = lib.vETH_WIN32__Set_Ethernet_TxCallback
        vETH_WIN32__Set_Ethernet_TxCallback.argtypes = [Ethernet_TxCallback]
        vETH_WIN32__Set_Ethernet_TxCallback.restype = None
        """

    def register_SC16IS_callback(self, device_index, python_function, dll_function_name, restype, argss):

        # Create the callback functype
        callback_functype = ctypes.CFUNCTYPE(restype, *argss)

        # Set the attributes on the method
        dll_method = getattr(self.lib, dll_function_name)
        dll_method.argtypes = [ctypes.c_uint8, callback_functype]
        dll_method.restype = restype
        dll_method.errcheck = self.errcheck_callback   # Maybe don't need/want this? 
        
        # reference the callback to keep it alive
        self.callback_refs[dll_function_name] = callback_functype(python_function)
        
        # Call the method on the dll and pass in our reference
        dll_method(device_index, self.callback_refs[dll_function_name])
        
    def run_threaded(self):
        self.logger.debug("Starting FCU main thread")

        """ Run the FCU """
        # Basic procedure: setup timers, Init, Process loop

        """
        'create our ASI's
        ReDim Me.m_pASI(C_NUM__ASI)
        For iCounter As Integer = 0 To C_NUM__ASI - 1
            Me.m_pASI(iCounter) = New ASIController()
            AddHandler Me.m_pASI(iCounter).Tx_RS485, AddressOf Me.ASI_Tx_RS485
        Next
        
        Me.m_pSafeUDP = New SIL3.SafeUDP.StdUDPLayer("127.0.0.1", 9100, "FCU_ETH_EMU", True, True)
        AddHandler Me.m_pSafeUDP.UserEvent__UDPSafe__RxPacket, AddressOf Me.InernalEvent__UDPSafe__RxPacket
        AddHandler Me.m_pSafeUDP.UserEvent__NewPacket, AddressOf Me.InternalEvent__NewPacket
        
        # (setup callbacks -- already done in __init__)
        
        'do the threading
        Me.m_pMainThread = New Threading.Thread(AddressOf Me.Thread__Main)
        Me.m_pMainThread.Name = "FCU THREAD"

        'stimers
        Timers__Setup()
        """
        
        # Private Shared Sub vFCU__RTI_10MS_ISR()
        # Private Shared Sub vFCU__RTI_100MS_ISR()
        # Private Shared Sub vSTEPDRIVE_TIMEBASE__ISR()   # Note: 50usec

        self.logger.info("- Creating timers")
        self.timers.append(Timer(Units.seconds("50 usec"), self.lib.vSTEPDRIVE_TIMEBASE__ISR))
        self.timers.append(Timer(Units.seconds("10 ms"), self.lib.vFCU__RTI_10MS_ISR))
        self.timers.append(Timer(Units.seconds("100 ms"), self.lib.vFCU__RTI_100MS_ISR))
        
        # Accelerometers
        self.logger.info("- Creating Sensors")
        self.accel_listeners = []
        for i, accel_config in self.sim.config.sensors.accel.iteritems():
            self.logger.info("  - Creating Accelerometer {} with sampling rate {}".format(i, accel_config['sampling_rate']))
            # Timers
            sampling_rate = Units.SI(accel_config['sampling_rate'])
            timer_delay = 1.0 / sampling_rate  # Hz 
            # Note: in the following lambda function, we bind x=i now so that it will use that value rather than binding at call time
            self.logger.debug("    Accelerometer sampling rate is {}; delay for timer is {}".format(sampling_rate, timer_delay))
            self.timers.append( Timer(timer_delay, lambda x=i: self.lib.vMMA8451_WIN32__TriggerInterrupt(x) ) )

            # Tie it to the appropriate sensor
            self.accel_listeners.append( QueueingListener(self.sim, None) )  # Note: we tie it to the sensor in the next line
            self.sim.sensors['accel'][i].add_step_listener(self.accel_listeners[i])
            # Now we have a handle to a listener for each accel. We'll use those in MMA8451_readdata_callback
    
            
        # Add our timers to the sim's time dialator so that we can stay in sync
        self.logger.info("- Initializing time dialator")
        self.sim.time_dialator.add_timers(self.timers)
        
        # Start the timers
        self.logger.info("- Starting the timers")
        for timer in self.timers:
            self.logger.info("  - Starting {} timer to call {}".format(timer.interval, str(timer.callback)))
            timer.start_threaded()
        

        """
        # Calls to start / stop button (starting and stopping the emu)
        If pB.Text = "Start" Then

            'setup the default values
            Me.m_iAccel0_X = -100
            Me.m_iAccel0_Y = 500
            Me.m_iAccel0_Z = 1024


            'set the flag
            Me.m_bThreadRun = True

            'set the new text
            pB.Text = "Stop"

            'start the thread
            Me.m_pMainThread.Start()

        Else
            'clear the flag
            Me.m_bThreadRun = False

            'stop threading
            Me.m_pMainThread.Abort()

            'reset the text
            pB.Text = "Start"

        End If
        """

        self.logger.debug("FCU starting up")
    
        thread_main = threading.Thread(target=self.main)
        thread_main.daemon = True
        thread_main.start()

        # UDP Injector -- testing only! (networking will need to go in the sim)
        #udp = UdpListener(self.sim, self.sim.config.networking.nodes.flight_control, self.handle_fcu_packet)
        #udp.run_threaded()

        return thread_main
        
    def main(self):
        self.logger.debug("Got to main()!")
        """
        ''' This is the same as Main() in C
        ''' </summary>
        Private Sub Thread__Main()

            'call Init
            vFCU__Init()

            'needs to be done due to WIN32_ETH_Init
            vETH_WIN32__Set_Ethernet_TxCallback(Me.m_pETH_TX__Delegate)

            'force the two motor positions to random so as we can simulate the cal process
            vSTEPDRIVE_WIN32__ForcePosition(0, -34)
            vSTEPDRIVE_WIN32__ForcePosition(1, 175)

            vFCU_BRAKES_MLP_WIN32__ForceADC(0, 0)
            vFCU_BRAKES_MLP_WIN32__ForceADC(1, 0)

            'config the brake switches into some state
            For iBrake As Integer = 0 To 2 - 1
                For iSwitch As Integer = 0 To 2 - 1
                    vFCU_BRAKES_SW_WIN32__Inject_SwitchState(iBrake, iSwitch, 0)
                Next
            Next

            'stay here until thread abort
            While True

                'add here any things that need updating like pod sensor data

                'call process
                Try
                    vFCU__Process()

                Catch ex As Exception
                    Console.Write(ex.ToString)
                End Try

                'just wait a little bit
                Threading.Thread.Sleep(1)
            End While
        End Sub
        """
        self.lib.vFCU__Init()
        
        #'needs to be done due to WIN32_ETH_Init
        #vETH_WIN32__Set_Ethernet_TxCallback(Me.m_pETH_TX__Delegate)
        self.lib.vETH_WIN32__Set_Ethernet_TxCallback(self.callback_refs['vETH_WIN32__Set_Ethernet_TxCallback'])

        # 'force the two motor positions to random so as we can simulate the cal process
        self.lib.vSTEPDRIVE_WIN32__ForcePosition(0, -34)
        self.lib.vSTEPDRIVE_WIN32__ForcePosition(1, 175)

        self.lib.vFCU_BRAKES_MLP_WIN32__ForceADC(0, 0)
        self.lib.vFCU_BRAKES_MLP_WIN32__ForceADC(1, 0)

        # 'config the brake switches into some state
        for iBrake in [0, 1]:
            for iSwitch in [0, 1]:
                self.lib.vFCU_BRAKES_SW_WIN32__Inject_SwitchState(iBrake, iSwitch, 0)
        
        self.logger.debug("Beginning FCU process loop")

        
        # 'stay here until thread abort
        counter = 0
        #while True and counter < 300:
        while True:

            # 'add here any things that need updating like pod sensor data

            # 'call process
            try:
                self.lib.vFCU__Process()
            except Exception as e:
                self.logger.error(e)

            # Testing the accelerometers
            #post_process_accel = self.lib.s32FCU_ACCELL__Get_CurrentAccel_mmss(0)
            #self.logger.debug("After vFCU__Process() s32FCU_ACCELL__Get_CurrentAccel_mmss(0): {}".format(post_process_accel))

            # Testing start accel data 
            if counter == 10 and False:   # 'and False' = Disabled -- let's try and get it from the ground station...
                print "***  Starting accel data  ***"
                #packet = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x02\x00\x00\x00\x45\x00\x00\x36\x1a\x9f\x00\x00\x80\x11\x00\x00\x7f\x00\x00\x01\x7f\x00\x00\x01\xe6\x68\x23\x8c\x00\x22\x6e\xf4\x00\x00\x00\x00\x00\x01\x10\x00\x01\x00\x00\x00\x01\x13\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x76\xaa"
                #packet = b"\x00\x00\x00\x00 \x00\x01 \x10\x00 \x01\x00\x00\x00\x01\x13\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x76\xaa"
                b_packet_type = struct.unpack("!H", b"\x01\x00")[0]
                b_dest_port = struct.unpack("!H", b"\x23\x8c")[0]
                print "b_dest_port: {}".format(b_dest_port)
                safeudp_payload = b"\x01\x00\x00\x00\x01\x13\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x76\xaa"
                safeudp_payload = b"\x01\x00\x00\x00\x01\x13\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                
                safeudp_payload = b"\x00\x00\x00\x00\x00\x01\x10\x00\x01\x00\x00\x00\x01\x13\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x76\xaa"  # <= ! This is it!
                                
                #self.lib.vETH_WIN32__Ethernet_Input(packet, len(packet))
                # void vFCU_NET_RX__RxSafeUDP(Luint8 *pu8Payload, Luint16 u16PayloadLength, Luint16 ePacketType, Luint16 u16DestPort, Luint16 u16Fault)
                #pu8Payload = (ctypes.c_ubyte * len(safeudp_payload))(struct.pack(safeudp_payload))
                #pu8Payload = ctypes.POINTER(ctypes.c_ubyte)
                #pu8Payload.contents = struct.pack(safeudp_payload)
                #pu8Payload = ctypes.create_string_buffer()
                
                #pu8Payload.contents = safeudp_payload
                #self.lib.vSAFE_UDP_RX__UDPPacket(pu8Payload, ctypes.c_uint16(len(safeudp_payload)), ctypes.c_uint16(b_packet_type), ctypes.c_uint16(b_dest_port), ctypes.c_uint16(0))
                # DLL_DECLARATION void vSAFE_UDP_RX__UDPPacket(Luint8 * pu8PacketBuffer, Luint16 u16PacketLength, Luint16 u16DestPort);
                
                u16PacketLength = ctypes.c_uint16(len(safeudp_payload))
                u16DestPort = ctypes.c_uint16(b_dest_port)
                pu8Payload = ctypes.create_string_buffer(safeudp_payload)
                self.lib.vSAFE_UDP_RX__UDPPacket(ctypes.byref(pu8Payload), u16PacketLength, u16DestPort)
                
            #'just wait a little bit
            #time.sleep(0.01)
            time.sleep(0.01 * self.sim.time_dialator.dialation)
            # @todo Question -- isn't this what the 10ms or 100ms timer is for (calling vFCU__Process())? or should we use a timer for that? 
            counter += 1
            
            #DLL_DECLARATION Lint16 s16MMA8451_FILTERING__Get_Average(Luint8 u8DeviceIndex, MMA8451__AXIS_E eAxis);
            # Testing to make sure we're setting the accel values (works!)
            """
            accel_idxs = [0, 1]
            accel_axis_idxs = [0, 1, 2]  # x, y, z
            #self.logger.debug("Accel values after vFCU__Process():")
            a = []
            #get_average.restype = ctypes.c_int16
            for dev_idx in accel_idxs:
                dev_xyz = []
                for axis in accel_axis_idxs:
                    val = self.lib.s16MMA8451_FILTERING__Get_Average(dev_idx, axis)
                    #vv = bitstring.BitArray('int:16={}'.format(val))
                    #v = bitstring.pack('int:12', vv.int)
                    dev_xyz.append(val)
                a.append("accel {}: ({})".format(dev_idx, dev_xyz))
            self.logger.debug("Accel values after vFCU__Process(): {}".format("; ".join(a)))
            """
            
if __name__ == "__main__":
    # For windows admin
    #import admin
    #if not admin.isUserAdmin():
    #    sys.exit(admin.runAsAdmin())  # Run as admin, then exit when the script has finished

    from sim import Sim
    import logging.config
    import yaml

    #logging.basicConfig(level=logging.DEBUG)

    with open('conf/logging.conf') as f:  # @todo: make this work when run from anywhere (this works if run from top directory)
        logging.config.dictConfig(yaml.load(f))
    
    config = Config()
    config.loadfile("conf/sim_config.yaml")

    sim_config = config.sim
    fcu_config = sim_config.fcu

    fcu_config.dll_path = "../eng-software-pod/APPLICATIONS/PROJECT_CODE/DLLS/LDLL174__RLOOP__LCCM655/bin/Debug/"  # Relative to top level of this repo (../)
    fcu_config.dll_filename = "LDLL174__RLOOP__LCCM655.dll"

    sim = Sim(sim_config)

    #fcu = Fcu(sim, fcu_config)  # This is incorporated into the simulator
    
    #sim_thread = sim.run_threaded()
    sim.run()

    #fcu_thread = fcu.run_threaded()  # this is now integrated into the simulator
    #fcu_thread.join()   # For testing -- right now it cuts off after a certain number of steps

    while True:
        try:
            time.sleep(0.1)
        except:
            sys.exit(0)
        
    """
    lib = ctypes.CDLL(dll_filepath)
    
    print dir(lib)
    """