#include "fcu_core.h"
#include "state_machine.h"

extern struct sFCU;

void supervisor_sm_init() 
{
    StateMachine *sm = &sFCU.supervisor_sm;
    *sm = sm_default;
    sm->state = NORMAL_OPERATION_STATE;  // Starting state
}

// Notes
/*
at spindown: 
- need to lower the LG before shutting off HE's, the cool for a bit
    - use get_is_busy() for this

*/


void supervisor_sm_process()
{
    // L: maybe monitor network interactions and abort/fault if it's lost -- 
    // L: Maybe have these settable (whether or not you can execute an emergency safe) in the Mission Profile -- to satisfy SpaceX
    // L: have something like 'test track mode' -- able to click the button to translate to any particular state -- maybe a key to set mode (hardware interlock)
    
    StateMachine *sm = &sFCU.supervisor.sm;
    
    sm_step(sm);

    // NORMAL_OPERATION_STATE, EMERGENCY_SAFE_STATE, MANUAL_OVERRIDE_STATE, EMERGENCY_PWR_OFF_STATE
    switch (sm->state) 
    {
        case NORMAL_OPERATION_STATE:
            if (sm_entering(sm, NORMAL_OPERATION_STATE))
            {
                // Make sure the main state machine is not suspended
                sFCU.main.sm.suspended = FALSE;
                // @todo: Clear any commands that might be in the queue for the main sm here? We could be powering up or coming from MANUAL_OVERRIDE...
                sFCU.main.sm.command = NO_CMD;

                // @todo: Might need to make sure it's in the right state (e.g. IDLE_STATE) when entering normal operation? 
                // What are the ways it can enter normal operation? From power on and from MANUAL_OVERRIDE_STATE. 
                // MANUAL_OVERRIDE_STATE is likely responsible for returning things to their proper order I think,
                // since it should have discretion (e.g. we should return to a particular state vs. forcing IDLE_STATE or something) 
            }

            // Handle commands, esp. EMERGENCY_SAFE, EMERGENCY_PWR_OFF, and MANUAL_OVERRIDE


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
                sFCU.main.sm.state = POD_SAFE_STATE;
                sFCU.main.sm.command = NO_CMD;  // Clear any commands so we don't jump states
            }

        case EMERGENCY_PWR_OFF_STATE:
            // @todo: Send a command to the power subsystem to turn things off NOW
            // @todo: Also probably suspend the main state machine (and try to send things to pod safe in case pwr_off doesn't work?)
            
            break;

        case MANUAL_OVERRIDE_STATE:
            // Try to keep things as they were when we entered this state, as much as possible
            // Hover engines on if they were alreay on, brakes stopped, landing gear stopped, cooling on (?), sensors as they were, etc.

            if (sm_entering(sm, MANUAL_OVERRIDE_STATE))
            {
                // Suspend the main state machine
                sFCU.sm.suspended = TRUE;
            }

            // Handle commands from the ground station to operation subsystems. 
            // @todo: handle command to resume operation -- note that we may force a state in the main SM or we might resume in the state we left off in; need to work this out
            //  ^^ RESUME_NORMAL_OPERATION -- note that you may have updated the main_sm state before executing that command...
            // @todo: work out how/what commands get passed through -- what's the format? These may need to be enum'd, but I'd rather avoid that if possible...
            // @todo: probably need to clear any command that's queued up for the main sm here so we don't jump into unknown territory...
            //   ... and set which state we want the main SM to be in when it starts back up
            //   ... and maybe tell it whether or not to start over in that state or pick up where it left off 
            //       ^ (we can do that by manipulating the old_state and state_changed, if we need to -- e.g. resume_prev_state() and restart_prev_state() or something)

            break;

    }
    
}

// Main State Machine

void main_sm_init()
{
    // Initialize the SM and sFCU settings here
    StateMachine *sm = &sFCU.main.sm;
    *sm = sm_default;
    sm->state = IDLE_STATE;
}

void main_sm_process()
{    
    StateMachine *sm = &sFCU.main.sm;

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

            // IMPORTANT NOTE: sm_entering() and sm_exiting() are simply convenience functions. The 'main' code ALWAYS runs for a state.
            // IMPORTANT NOTE: Make sure that you will not be overwriting commands to subsystems. In general, send commands on entering,
            //                 during the main code block if using a timer, and avoid sending commands when exiting (let the next state)
            //                 take care of it. 
            if (sm_entering(sm, IDLE_STATE)) 
            {
                // Runs once each time we enter this state; does not run if we're staying in this state.
                
                // @todo: maybe try to stop movement of the pod? Everything should be generally powered off here. 
                // Also maybe leave things in their current state as much as possible (e.g. lasers on) -- no, generally power down moving items in this state.
                // Do we need to check for failing states? What about interlocks? Remove them when we get to IDLE state? We might just remove them on POD_SAFE exit...
                
                cmd_brakes_hold();  // note: brake system may be faulted out
                //sFCU.brakes.sm.command = BRAKES_HOLD;
                cmd_cooling_off();
                cmd_nav_lasers_off();
                cmd_auxprop_stop();
                cmd_pv_hold_pressure();
                
            }

            // Note: this code executes always (even if we're entering/exiting) -- "fall on"
            // Lachlan: why not do these three in three process loops? 

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

            //on_busy_IDLE_STATE();

            // IDLE actions here
            // Runs each loop instance -- does run if we're staying in this state.
            // Note: should generally not send commands to subsystems here since they will be sent every loop -- ok if there is a specific condition around it
            
            // IMPORTANT NOTE: The sm_exiting()  method is provided for convenience -- generally, don't send 
            //                 commands in this block if you're using it, just notifications and cleanup. 
            if (sm_exiting(sm, IDLE_STATE))
            {
                //on_exit_IDLE_STATE();  // ?
                // Runs once each time we exit this state; does not run if we're staying in this state.
                // For IDLE_STATE there's not much to do on exit I think
            } 
            
        case TEST_MODE_STATE:
        
            // Do test mode stuff here
            
            // Note: we're not using sm_entering() and sm_exiting() here -- this is an example of a simple case. 
            
            // Handle main state machine test mode commands (can only go back to idle. Other commands to the testing subsystem are handled separately)
            switch (sm->command) {
                case IDLE:  // IDLE command
                    // Do anything necessary to clean up from test mode -- stop movement, maybe return things to their original positions
                    // @todo: what happens if that takes time? Do we automatically return to IDLE? In this setup, yes...
                    if (some_coditions_met()) {
                        sm->state = IDLE;
                    }
                    break;
            }
            sm->command = NO_CMD;
            
            // Handle test mode -- probably defer to a testing subsystem
            // ...
        
        case DRIVE_STATE:
            // ...
            // Need to check to make sure the pod isn't moving too fast? that the 
            break;
    }

    // Clear the command -- we have processed it by now.
    //sm->command = NO_CMD;
    
}


// Brakes Subsystem

void subsystem_brakes_init()
{
    StateMachine *sm = &sFCU.brakes.sm;
    *sm = sm_defualt;  // Default starting setup for the state machine
    
    // Set initial state
    sm->state = BRAKES_HOLD_STATE; 
    
    // Interlock
    sFCU.brakes.interlocked = FALSE;

}

void subsystem_brakes_command_helper()
{
    // Most states in the brakes subsystem can be reached from any other state using a command, except if the brakes are interlocked.
    // This method helps consolidate the logic for that.

    StateMachine *sm = &sFCU.brakes.sm;
    
    // States: BRAKES_FREE_STATE, BRAKES_MANUAL_STATE, BRAKES_CONTROLLED_BRAKE_STATE, BRAKES_EMERGENCY_BRAKE_STATE, BRAKES_HOLD_STATE
    // Commands: BRAKES_FREE, BRAKES_MANUAL, BRAKES_SEEK, BRAKES_HOLD, BRAKES_CONTROLLED_BRAKE, BRAKES_EMERGENCY_BRAKE, BRAKES_INTERLOCK, BRAKES_RELEASE_INTERLOCK
    if (sFCU.brakes.interlocked)
    {
        // Only listen for BRAKES_RELEASE_INTERLOCK when we're in an interlocked state
        if(sm->command == BRAKES_RELEASE_INTERLOCK)
        {
            sm->state = BRAKES_HOLD;
            sm->command = NO_CMD;
            sm->interlocked = FALSE;
        }
    } else {
        
        // If we're not interlocked, we can go to any state from any state
        switch(sm->command)
        {
            case BRAKES_INTERLOCK:
                sm->state = BRAKES_HOLD_STATE;
                sm->command = NO_CMD;  // Make sure we clear the command. This is redundant but will ensure no command gets executed.
                sm->interlocked = TRUE;
                break;
            
            case BRAKES_MANUAL:
                sm->state = BRAKES_MANUAL_STATE;
                break;

            case BRAKES_FREE:
                sm->state = BRAKES_FREE_STATE;
                break;
            
            case BRAKES_SEEK:
                // Note: you have to set your targets before you send the command -- no data comes with commands.
                sm->state = BRAKES_SEEK_STATE;
                break;
            
            case BRAKES_HOLD:
                sm->state = BRAKES_HOLD_STATE;
                break;
            
            case BRAKES_CONTROLLED_BRAKE:
                // Note: get_is_busy (check to see if a state machine is busy -- if not, automatically transfer control to an upper level state machine)
                // Note: this should have control until we're at a complete stop -- maybe mark a variable that we've stopped? poll "are we stopped?" -- when true, continue
                sm->state = BRAKES_CONTROLLED_BRAKE_STATE;
                break;

            case BRAKES_EMERGENCY_BRAKE:
                sm->state = BRAKES_EMERGENCY_BRAKE_STATE;
                break;
        }
        sm->command = NO_CMD;

    }

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
    // Note: anything that can change the state (e.g. commands) must be handled within a state to ensure the entry and exit functions work properly.
    sm_step(sm);

    // State Machine
    switch(sm->state)
    {
        case BRAKES_HOLD_STATE:
            // Note: on entry, give the brakes a short period of time to stop before checking for stoppage/raising a fault
            // on entry
            // process commands
            // on loop
            subsystem_brakes_command_helper();
            // on exit
            break;

        case BRAKES_MANUAL_STATE:
            // on entry
            // process commands
            subsystem_brakes_command_helper();
            // on loop
            // on exit
            break;

        case BRAKES_SEEK_STATE:
            // on entry
            // process commands
            subsystem_brakes_command_helper();
            // on loop
            // on exit
            break;

        case BRAKES_FREE_STATE:
            // on entry
            // process commands
            subsystem_brakes_command_helper();
            // on loop
            // on exit
            break;
            
        case BRAKES_CONTROLLED_BRAKE_STATE:
            // on entry
            // process commands
            subsystem_brakes_command_helper();
            // on loop
            // on exit
            break;

        case BRAKES_EMERGENCY_BRAKE_STATE:
            // on entry
            // process commands
            subsystem_brakes_command_helper();
            // on loop
            // on exit
            break;
        
        case BRAKES_INTERLOCK_STATE:
            // on entry
            // process commands -- only BRAKES_RELEASE_INTERLOCK will work, and will send it back to BRAKES_HOLD_STATE
            subsystem_brakes_command_helper();
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
    // ...
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