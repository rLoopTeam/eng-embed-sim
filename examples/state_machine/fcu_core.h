#ifndef _FCU_CORE_H_
#define _FCU_CORE_H_

#include "state_machine.h"

#define NO_CMD -1

// @todo: fix these -- just setting them to int for now for testing
typedef int Luint8;
typedef int Luint16;

// Supervisor
enum {NORMAL_OPERATION_STATE, EMERGENCY_SAFE_STATE, MANUAL_OVERRIDE_STATE, EMERGENCY_PWR_OFF_STATE} E_SUPERVISOR_STATE_T;
enum {EMERGENCY_SAFE, MANUAL_OVERRIDE, NORMAL_OPERATION, EMERGENCY_PWR_OFF, RESUME_POD_SAFE} E_SUPERVISOR_CMD_T;

// Main state machine states
enum {IDLE_STATE, TEST_MODE_STATE, DRIVE_STATE, ARMED_WAIT_STATE, FLIGHT_PREP_STATE, READY_STATE, ACCEL_STATE, COAST_INTERLOCK_STATE, BRAKE_STATE, SPINDOWN_STATE, POD_SAFE_STATE, SHUTDOWN_STATE} E_MAIN_STATES_T;
// Main state machine commands
enum {SUSPEND, RESUME, TEST_MODE, DRIVE, ARMED_WAIT, FLIGHT_PREP, POD_SAFE, IDLE, SHUTDOWN, EMERGENCY_SAFE} E_MAIN_CMD_T;
// Note: suspend will cause the main state machine to relenquish control of the subsystems until resumed. 
// Basically the subsystems should always be run, whether the main SM has control or something else does (like the supervisor)

// Brakes subsystem states
enum {BRAKES_FREE_STATE, BRAKES_CONTROLLED_BRAKE_STATE, BRAKES_EMERGENCY_BRAKE_STATE, BRAKES_HOLD_STATE} E_BRAKE_STATES_T;
// Brake subsystem commands
enum {BRAKES_FREE, BRAKES_SEEK, BRAKES_HOLD, BRAKES_CONTROLLED_BRAKE, BRAKES_EMERGENCY_BRAKE, BRAKES_INTERLOCK, BRAKES_RELEASE_INTERLOCK} E_BRAKES_CMD_T;


// Command handling convenience methods
bool has_cmd(int *p_command)
{
    return p_command >= 0;
}

bool pop_cmd(int *p_command)
{
    int command = *p_command;
    *p_command = NO_CMD;
    return command;
}

void set_cmd(int *p_command, int command)
{
    *p_command = command;
}

int get_cmd(int *p_command)
{
    return *p_command;
}

// Pod data structure

#define C_FCU__NUM_BRAKES 2
#define BRAKE_SW__MAX_SWITCHES 2


struct _strFCU {
    
    // Supervisor state machine
    StateMachine supervisor_sm;

    // Main state machine
    StateMachine sm;

    // Pod Safe Indicator
    // This is the source of truth for whether or not the pod is safe
    // Note that entering POD_SAFE does not necessarily mean that the pod is safe, just that it's trying to get there.
    // This variable will be set by the POD_SAFE state once everything is confirmed to be safe.
    int pod_safe_indicator;

    // Data members
    int idle_counter;
    int test_mode_counter;



    // Subsystems

    // Brakes
    // e.g. sFCU.brakes.brake[0].some_setting
    struct {
        StateMachine sm;
        int command;

        // Individual brakes
        struct {

            /** Limit switch structure
             * There are two limit switches per brake assy
             */
            struct
            {
                // Some example data members

                /** An edge was captured on the interrupt subsystem
                 * Its up to some other layer to clear the flag once its used.
                 */
                Luint8 u8EdgeSeen;

                #if C_LOCALDEF__LCCM655__ENABLE_DEBUG_BRAKES == 1U
                        /** Debugs how many interrupts have been received
                         */
                    Luint32 u8EdgeSeenCnt;
                #endif

                /** The program index for N2HET, even if not used on both channels */
                Luint16 u16N2HET_Prog;

                /** The current state of the switch */
                // E_FCU__SWITCH_STATE_T eSwitchState;
                int eSwitchState; // just for testing

                #ifdef WIN32
                    /** Allow us to inject swiches on WIN32 */
                    Luint8 u8InjectedValue;
                #endif

            } limit[BRAKE_SW__MAX_SWITCHES];        
        
        } brake[C_FCU__NUM_BRAKES];

    } brakes;
    
    struct {
        StateMachine sm;
        int command;
        
        // Data members go here
        
    } cooling;
    
    struct {
        StateMachine sm;
        int command;

        // Data members go here

    } lg;

    // ...

};


#endif //_FCU_CORE_H_