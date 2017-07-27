#include "fcu_core.h"
#include "state_machine.h"

extern struct sFCU;

void supervisor_sm_init() 
{
    StateMachine *sm = &sFCU.supervisor_sm;
    *sm = sm_default;
    sm->state = NORMAL_OPERATION_STATE;  // Starting state
}

void supervisor_sm_process()
{
    StateMachine *sm = &sFCU.supervisor_sm;
    
    sm_step(sm);

    // NORMAL_OPERATION_STATE, EMERGENCY_SAFE_STATE, MANUAL_OVERRIDE_STATE, EMERGENCY_PWR_OFF_STATE
    switch (sm->state) 
    {
        case NORMAL_OPERATION_STATE:
            if (sm_entering(sm, NORMAL_OPERATION_STATE))
            {
                // Make sure the main state machine is not suspended
                sFCU.sm.suspended = FALSE;

                // @todo: Might need to make sure it's in the right state (e.g. IDLE_STATE) when entering normal operation? 
                // What are the ways it can enter normal operation? From power on and from MANUAL_OVERRIDE_STATE. 
                // MANUAL_OVERRIDE_STATE is likely responsible for returning things to their proper order I think,
                // since it should have discretion (e.g. we should return to a particular state vs. forcing IDLE_STATE or something) 
            }

            // Anything to do during normal operation? 
            //if ( !some_timer.started || some_timer.expired) 
            //{
                // do something like blink a light
                
            //    restart_timer(some_timer);
            //}

            if (sm_exiting(sm, NORMAL_OPERATION_STATE))
            {
                // Anything to do here? 
            }

            break;

        case EMERGENCY_SAFE_STATE:
            // @todo: How do we exit EMERGENCY_SAFE_STATE? To POD_SAFE via ground station command.
            if (sm_entering(sm, EMERGENCY_SAFE_STATE))
            {
                sFCU.sm.suspended = TRUE;

                // Send commands to subsystems to stop everything
                make_pod_safe();

            }
            
            // Handle commands, namely RESUME_POD_SAFE [rename]; also probably monitoring and setting the pod_safe_indicator

            
            if (sm_exiting(sm, EMERGENCY_SAFE_STATE))
            {
                // Un-suspend the main state machine? Maybe -- we need to force it to POD_SAFE mode first; maybe do that in the command processing? 
                sFCU.sm.state = POD_SAFE_STATE;
            }

        case EMERGENCY_PWR_OFF:
            // @todo: Send a command to the power subsystem to turn things off NOW
            // @todo: Also probably suspend the main state machine
            
            break;

    }
    
}


void main_sm_init()
{
    // Initialize the SM and sFCU settings here
    StateMachine *sm = &sFCU.sm;
    *sm = sm_default;
    sm->state = IDLE_STATE;
}

void main_sm_process()
{    
    StateMachine *sm = &sFCU.sm;

    // The main state machine can be suspended by the supervisor -- it will take direct control of the subsystems in that case.
    if (sm->suspended) 
    {
        return;
    }
            
    // Catch any state changes and update our tracker (sm)
    sm_step(sm);

    // State Machine
    switch(sm->state)
    {
        case IDLE_STATE:

            if (sm_entering(sm, IDLE_STATE)) 
            {
                // Runs once each time we enter this state; does not run if we're staying in this state.
                
                // @todo: maybe try to stop movement of the pod? Everything should be generally powered off here. 
                // Also maybe leave things in their current state as much as possible (e.g. lasers on) -- no, generally power down moving items in this state.
                // Do we need to check for failing states? What about interlocks? Remove them when we get to IDLE state? We might just remove them on POD_SAFE exit...
                cmd_brakes_hold();
                cmd_cooling_off();
                cmd_nav_lasers_off();
                cmd_auxprop_stop();
                cmd_pv_hold_pressure();
                
            }

            // Handle commands for IDLE state
            // @todo: These will likely come from the ground station -- something will need to set sFCU.command variable. 
            switch (sm->command) {
                case TEST_MODE:
                    sm->state = TEST_MODE_STATE;
                    break;
                case DRIVE:
                    sm->state = DRIVE_STATE;
                    break;
                case ARMED_WAIT:
                    // Note: you can prevent transition if you want a guard condition like 'verify_mission_profile_pod_match()'. The command will need to be sent again.
                    // Probably should indicate somewhere that the command failed in that case...
                    sm->state = ARMED_WAIT_STATE;
                    break;
                case POD_SAFE:
                    sm->state = POD_SAFE_STATE;
                    break;
                case SHUTDOWN:
                    sm->state = SHUTDOWN_STATE;
                    break;
            }
            sm->command = NO_CMD;  // Reset the command since we've handled it

            // IDLE actions here
            // Runs each loop instance -- does run if we're staying in this state.
            // Note: should generally not send commands to subsystems here since they will be sent every loop -- ok if there is a specific condition around it
                        
            if (sm_exiting(sm, IDLE_STATE))
            {
                // Runs once each time we exit this state; does not run if we're staying in this state.
                // For IDLE_STATE there's not much to do on exit I think
            }
            
        case TEST_MODE_STATE:
        
            // Handle main state machine test mode commands (can only go back to idle. Other commands to the testing subsystem are handled separately)
            switch (sm->command) {
                case IDLE:  // IDLE command
                    // Do anything necessary to clean up from test mode -- stop movement, maybe return things to their original positions
                    // @todo: what happens if that takes time? Do we automatically return to IDLE? In this setup, yes...
                    sm->state = IDLE;
                    break;
            }
            sm->command = NO_CMD;
            
            // Handle test mode -- probably defer to a testing subsystem
            // ...
        
    }

    // Clear the command -- we have processed it by now.
    //sm->command = NO_CMD;
    
}

void subsystem_brakes_init()
{
    StateMachine *sm = &sFCU.brakes.sm;
    *sm = sm_defualt;  // Default starting setup for the state machine
    
    // Set initial state
    sm->state = BRAKES_HOLD_STATE; 
}

void subsystem_brakes_process()
{
    StateMachine *sm = &sFCU.brakes.sm;
    
    // The brakes subsystem may be suspended, but possibly not -- @todo: maybe remove this
    if (sm->suspended) 
    {
        return;
    }
            
    // Catch any state changes and update our tracker (sm)
    sm_step(sm);

    // State Machine
    switch(sm->state)
    {
        case BRAKES_HOLD_STATE:
            // on entry
            // process commands
            // on loop
            // on exit
            break;

        case BRAKES_FREE_STATE:
            // on entry
            // process commands
            // on loop
            // on exit
            break;
            
        case BRAKES_CONTROLLED_BRAKE_STATE:
            // on entry
            // process commands
            // on loop
            // on exit
            break;

        case BRAKES_EMERGENCY_BRAKE_STATE:
            // on entry
            // process commands
            // on loop
            // on exit
            break;
        
        case BRAKES_INTERLOCK_STATE:
            // on entry
            // process commands -- only BRAKES_RELEASE_INTERLOCK will work, and will send it back to BRAKES_HOLD_STATE
            // on loop
            // on exit
            break;

    }

}


void cFCU_Init()
{
    // Supervisor state machine
    supervisor_sm_init();
    
    // Main state machine
    main_sm_init();
    
    // Subsystems
    subsystem_brakes_init();
    
}


void vFCU_Process()
{
    // Supervisor state machine
    supervisor_sm_process();
    
    // Main state machine
    main_sm_process();
    
    // Subsystems
    subsystem_brakes_process();
    //subsystem_flight_control_process();
    //subsystem_cooling_process();
    //subsystem_lg_process();
    // ...
    
    
}