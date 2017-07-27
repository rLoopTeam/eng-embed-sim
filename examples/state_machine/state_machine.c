#include <stdio.h>

/**
 * Working sketch of a state machine in c with entry, exit, and state tracking
 * Ryan Adams, 2017-Jul-25
 * Compiling: gcc c_state_machine_sketch.c -o c_state_machine_sketch
 */

typedef int bool;
#define TRUE 1
#define FALSE 0

#define DEBUGGING 1




struct statemachine_s {
    int state;
    int old_state;
    int command;   // command(s?) for the state machine -- mostly used for subsystems
    bool state_changed;  // For when we start, to trigger if entry(sm, state) stanzas
    bool kill_switch;  // @todo: get rid of this.
} sm_default = {-1, -1, -1, TRUE, FALSE};

typedef struct statemachine_s statemachine;

//statemachine sm = sm_default;
//statemachine sm;  // works; trying out mem_s

typedef struct
{
    // base members
} SubSystem;

typedef struct
{
    SubSystem base;
    
}


/*
// Desired usage:
sFCU.brakes.sm -- state machine for the brakes
sFCU.main.sm -- main state machine
sFCU.brakes.data -- data structure for the brakes. may be different from data structure for main

*/


struct mem_s {
    statemachine main_sm;
    statemachine brakes_sm; 
    
    struct {
        int idle_counter;
        int test_mode_counter;
    } main_sm_data;
    
};

typedef struct mem_s mem;

mem sFCU;


// Main state machine states
enum {IDLE, TEST_MODE, DRIVE, ARMED_WAIT, FLIGHT_PREP, READY, ACCEL, COAST_INTERLOCK, BRAKE, SPINDOWN, POD_SAFE, SHUTDOWN} E_MAIN_STATES_T;
// Main state machine commands
enum {CMD_TEST_MODE, CMD_DRIVE, CMD_ARMED_WAIT, CMD_FLIGHT_PREP, CMD_POD_SAFE, CMD_IDLE, CMD_SHUTDOWN, CMD_INTERLOCK, CMD_RELEASE_INTERLOCK} E_MAIN_CMD_T;

// Brakes subsystem states
enum {BRAKES_FREE, BRAKES_SEEK, BRAKES_HOLD} E_BRAKE_STATES_T;
// Brake commands
enum {CMD_BRAKES_FREE, CMD_BRAKES_SEEK, CMD_BRAKES_HOLD, CMD_CONTROLLED_BRAKE, CMD_EMERGENCY_BRAKE, CMD_BRAKES_INTERLOCK, CMD_BRAKES_RELEASE_INTERLOCK} E_BRAKE_CMD_T;


// Cooling subsystem states
enum {LCO2_AUTO, LCO2_MANUAL, LCO2_OFF} E_LCO2_STATES_T;

/* Step the state machine -- detect state changes and update sm status */
void sm_step(statemachine* p_sm) {

    // Update old state and signal that a state change has occurred 
    if (p_sm->old_state != p_sm->state) {
        printf("State changed! %d to %d\n", p_sm->old_state, p_sm->state);
        p_sm->state_changed = TRUE;
        p_sm->old_state = p_sm->state;
    } else if (p_sm->state_changed) {
        // the 'else' means that we go through the loop exactly once with the 'state_changed' variable set to true once a state change has occured
        // Note that if the state changes again on the next loop, the old_state != state stanza gets triggered and starts this over again, which is what we want
        p_sm->state_changed = FALSE;
    }

}

bool entering(const statemachine *sm, int test_state) {
    // Determine if we've just entered test_state on this step (a step is a go-round of the main loop)
    return sm->state_changed && sm->state == test_state;
}

bool exiting(const statemachine *sm, int test_state) {
    // Determine if we're marked to exit this state. Put this in your case statements after anything that could cause a state change.
    return sm->state != test_state;
}

bool has_cmd(const statemachine *sm) {
    return sm->command != -1;
}

void push_cmd(statemachine *sm, int command) {
    // @todo: think about making this a queue, or returning a failure code if a command is already there
    sm->command = command;
}

int pop_cmd(statemachine *sm) {
    int command = sm->command;
    sm->command = -1;
    return command;
}

int print(const char * str) {
    return printf("%s\n", str);
}

void process_main_sm(void) {
    
    statemachine *sm = &sFCU.main_sm;
    statemachine *sm_brakes = &sFCU.brakes_sm;

    // Step the state machine
    //printf("Before step: changed=%d, old=%d, new=%d\n", sm->state_changed, sm->old_state, sm->state);
    sm_step(sm);
    //printf("After step: changed=%d, old=%d, new=%d\n", sm->state_changed, sm->old_state, sm->state);

    switch (sm->state) {
        
        case IDLE:
            if (entering(sm, IDLE)) {
                #if DEBUGGING == 1
                print("Entering IDLE");
                #endif
                sFCU.main_sm_data.idle_counter = 0;

                // Send some commands to the subsystems
                push_cmd(brakes, CMD_BRAKES_HOLD);
                push_cmd(cooling, CMD_COOLING_OFF);
                push_cmd()

            } else {
                //print("In IDLE but not entering.");
            }

            print("In IDLE state.");

            if (sFCU.main_sm_data.idle_counter >= 2) {
                print("Signaling switch to TEST_MODE");
                push_cmd(sm, CMD_TEST_MODE);
            }

            sFCU.main_sm_data.idle_counter++;

            // Handle commands for IDLE state
            if (has_cmd(sm)) {
                int command = pop_cmd(sm);
                switch (command) {
                    case CMD_TEST_MODE:
                        sm->state = TEST_MODE;
                        break;
                    case CMD_DRIVE:
                        sm->state = DRIVE;
                        break;
                    case CMD_ARMED_WAIT:
                        sm->state = ARMED_WAIT;
                        break;
                    case CMD_POD_SAFE:
                        sm->state = POD_SAFE;
                        break;
                    case CMD_SHUTDOWN:
                        sm->state = SHUTDOWN;
                        break;
                }
            }

            if (exiting(sm, IDLE)) {
                print("Exiting IDLE");
            } else {
                //print("In IDLE but not exiting.");
            }
            break;
            
        case TEST_MODE:
        
            if (entering(sm, TEST_MODE)) {
                print("Entering TEST_MODE");
            }

            printf("In TEST_MODE state.\n");
            
            if (sFCU.main_sm_data.test_mode_counter == 2) {
                // Note: the test_mode_counter will still get incremented enen though we're changing the state...
                sm->state = IDLE;
            }
            if (sFCU.main_sm_data.test_mode_counter == 3) {
                sm->kill_switch = TRUE;
            } 

            sFCU.main_sm_data.test_mode_counter++;
            
            if (exiting(sm, TEST_MODE)) {
                print("Exiting TEST_MODE");
            }
            break;
    }

    if (sm->kill_switch) {
        print("State machine kill switch activated.");
    }

    
}


void cmd_brakes_hold(void) {
    // Command the brakes to hold
    
}

void process_brakes_subsystem(void) {
    // do brakes processing
    
}


int main(void) {
    
    //struct StateMachine sm;

    sFCU.main_sm = sm_default;
    sFCU.brakes_sm = sm_default;

    sFCU.main_sm.state = IDLE;

    sFCU.main_sm_data.idle_counter = 0;
    sFCU.main_sm_data.test_mode_counter = 0;

    int while_counter = 0;

    while (!sFCU.main_sm.kill_switch && while_counter <= 50) {
        process_main_sm();
        while_counter++;
    }
}