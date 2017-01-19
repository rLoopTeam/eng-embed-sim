#!/usr/bin/env python

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

# Our stuff
from config import Config
from units import Units
from networking import PodComms
from sensors import QueueingListener

# IMPORTANT: This must be run as administrator (PowerShell on Windows) or it will encounter a write error.

class Fcu:
    
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config
        
        self.logger = logging.getLogger("FCU")

        # Timers for various callbacks 
        self.timers = []

        # TESTING ONLY @todo: this should probably come from self.sim.networking
        self.comms = PodComms(self, self.sim.config.networking)

        # Load the DLL
        self.dll_path = self.config.dll_path
        self.dll_filename = self.config.dll_filename
        self.dll_filepath = (os.path.join(self.dll_path, self.dll_filename))
        self.logger.info("Loading dll '{}'".format(self.dll_filepath))
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

    def errcheck_callback(self, result, func, arguments):
        self.logger.debug("Fcu.errcheck_callback({}, {}, {})".format(result, func, arguments))
        
    def debug_printf_callback(self, message):
        # Public Delegate Sub DEBUG_PRINTF__CallbackDelegate(ByVal pu8String As IntPtr)
        self.logger.debug("Fcu.debug_printf('{}')".format(message))

    def eth_tx_callback(self, pu8Buffer, u16BufferLength):
        # Public Delegate Sub ETH_WIN32__TxCallbackDelegate(ByVal pu8Buffer As IntPtr, ByVal u16BufferLength As UInt16)
        # @todo: Format the buffer so it's readable (bytes)
        #self.logger.debug("Fcu.eth_tx_callback('{}', {})".format(pu8Buffer, u16BufferLength))
        #test = SafeUDP.spacex_payload_from_eth2(pu8Buffer, u16BufferLength)
        test = self.comms.send(pu8Buffer, u16BufferLength)
        try:
            self.logger.debug("Fcu.eth_tx_callback: {}".format(test))
        except Exception as e:
            self.logger.error(e)
        
    def MMA8451_readdata_callback(self, u8DeviceIndex, pu8X, pu8Y, pu8Z):
        """ When the MMA8451 wants data from us """
        # Public Delegate Sub MMA8451_WIN32__ReadDataCallbackDelegate(u8DeviceIndex As Byte, pu8X As IntPtr, pu8Y As IntPtr, pu8Z As IntPtr)
        self.logger.debug("Fcu.MMA8451_readdata_callback({}, {}, {}, {})".format(u8DeviceIndex, pu8X.contents, pu8Y.contents, pu8Z.contents))
        
        # @todo: need to get this sending data from the accel sensors. Maybe have a queue to read from? 
        # Note: probably only trigger the interrupts to call this callback when we have data in the queue? 
        #pu8X.contents = ctypes.c_int(4095)
        #pu8Y.contents = ctypes.c_int(0)
        #pu8Z.contents = ctypes.c_int(-4095)
        
        # Get the listener that's queueing data for our accelerometer (and convert it to the proper raw values/types)
        # Note: we only pop one here. The timers and time dialation should make sure that the # samples and the callbacks equalize
        pre_accel = self.lib.s32FCU_ACCELL__Get_CurrentAccel_mmss()
        try:
            real_data = self.accel_listeners[u8DeviceIndex].pop()
        except IndexError as e:
            self.logger.debug(e)
            return
        post_accel = self.lib.s32FCU_ACCELL__Get_CurrentAccel_mmss()
        self.logger.debug("Pre and post accel from the FCU: {}, {} (mm/s^2)".format(pre_accel, post_accel))

            
        # @TODO: gotta put something in there...
        data = self.sim.sensors['accel'][u8DeviceIndex].to_raw(real_data)
        # @ TODO: we need to get the proper data for the FCU (e.g. -2048 -- 2048). Should we do that here? Or call back to the sensor? Can we call back to the sensor? 
        pu8X.contents = ctypes.c_int(data.x)
        pu8Y.contents = ctypes.c_int(data.y)
        pu8Z.contents = ctypes.c_int(data.z)
        
        self.logger.debug("Setting pu8 data in MMA8451_readdata_callback: ({}, {}, {}) - q len is now {}".format(pu8X.contents, pu8Y.contents, pu8Z.contents, len(self.accel_listeners[u8DeviceIndex].q)))
        
        # Note: the device index indicates which device the MMA8451 is asking for. Just grab the data from the sim and write it to the pointers. 

    def stepdrive_update_position_callback(self, u8MotorIndex, u8Step, u8Dir, s32Position):
        # Public Delegate Sub STEPDRIVE_WIN32__Set_UpdatePositionCallbackDelegate(u8MotorIndex As Byte, u8Step As Byte, u8Dir As Byte, s32Position As Int32)
        self.logger.debug("Fcu.stepdrive_update_position_callback({}, {}, {}, {})".format(u8MotorIndex, u8Step, u8Dir, s32Position))

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
        vSTEPDRIVE_WIN32__Set_UpdatePositionCallback = lib.vSTEPDRIVE_WIN32__Set_UpdatePositionCallback
        vSTEPDRIVE_WIN32__Set_UpdatePositionCallback.argtypes = [vSTEPDRIVE_WIN32__UpdatePositionCallback]
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
        self.logger.debug("Got to run_threaded()!")

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

        self.timers.append(Timer(Units.seconds("50 usec"), self.lib.vSTEPDRIVE_TIMEBASE__ISR))
        self.timers.append(Timer(Units.seconds("10 ms"), self.lib.vFCU__RTI_10MS_ISR))
        self.timers.append(Timer(Units.seconds("100 ms"), self.lib.vFCU__RTI_100MS_ISR))
        
        # Accelerometers
        self.accel_listeners = []
        for i, accel_config in enumerate(self.sim.config.sensors.accel):
            # Timers
            sampling_rate = Units.SI(accel_config['sampling_rate'])
            timer_delay = 1.0 / sampling_rate  # Hz
            # Note: in the following lambda function, we bind x=i now so that it will use that value rather than binding at call time
            self.timers.append( Timer(timer_delay, lambda x=i: self.lib.vMMA8451_WIN32__TriggerInterrupt(x) ) )

            # Tie it to the appropriate sensor
            self.accel_listeners.append( QueueingListener(self.sim, None) )  # Note: we tie it to the sensor in the next line
            self.sim.sensors['accel'][i].add_step_listener(self.accel_listeners[i])
            # Now we have a handle to a listener for each accel. We'll use those in MMA8451_readdata_callback
    
        print self.timers
        
        # Add our timers to the sim's time dialator so that we can stay in sync
        self.sim.time_dialator.add_timers(self.timers)
        
        # Start the timers
        for timer in self.timers:
            timer.start_threaded()
        
        self.logger.debug("Started the timers...")

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

        self.logger.debug("Running the main thread...")
    
        thread_main = threading.Thread(target=self.main)
        thread_main.daemon = True
        thread_main.start()
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
        
        self.logger.debug("Made it this far; entering process loop. Here goes...")

        
        # 'stay here until thread abort
        counter = 0
        while True and counter < 100:

            # 'add here any things that need updating like pod sensor data

            # 'call process
            try:
                self.lib.vFCU__Process()

            except Exception as e:
                self.logger.error(e)

            #'just wait a little bit
            #time.sleep(0.01)
            time.sleep(0.01)  # @todo Question -- isn't this what the 10ms or 100ms timer is for (calling vFCU__Process())? or should we use a timer for that? 
            counter += 1

        
if __name__ == "__main__":
    from sim import Sim
    logging.basicConfig(level=logging.DEBUG)
    
    config = Config()
    config.loadfile("conf/sim_config.yaml")

    sim_config = config.sim
    fcu_config = sim_config.fcu

    fcu_config.dll_path = "../eng-software-pod/APPLICATIONS/PROJECT_CODE/DLLS/LDLL174__RLOOP__LCCM655/bin/Debug/"  # Relative to top level of this repo (../)
    fcu_config.dll_filename = "LDLL174__RLOOP__LCCM655.dll"

    sim = Sim(sim_config)

    fcu = Fcu(sim, fcu_config)
    
    sim_thread = sim.run_threaded()
    fcu_thread = fcu.run_threaded()

    #sim_thread.join()
    fcu_thread.join()   # For testing -- right now it cuts off after a certain number of steps
    
    """
    lib = ctypes.CDLL(dll_filepath)
    
    print dir(lib)
    """