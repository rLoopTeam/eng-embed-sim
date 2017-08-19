#ifndef _STATE_MACHINE_H_
#define _STATE_MACHINE_H_

#define TRUE 1
#define FALSE 0

typedef int bool;


#include <stdio.h>

// State machine management struct
struct StateMachine_s {
    int state;
    int old_state;
    bool state_changed;  // For when we start, to trigger if entry(sm, state) stanzas
    int command;  // Command for altering things in the state machine. 
        // Note: Would like this to be separate since it's really about commanding the subsystems regardless of whether they're a state machine or not, but this is convenient...
    bool suspended;  // Is the state machine suspended? If so don't process any state changes (??)
} sm_default = {-1, -1, TRUE};

typedef struct StateMachine_s StateMachine;

// State Machine Functions

/* Step the state machine -- detect state changes and update sm status */
void sm_step(StateMachine* p_sm) {

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


// Determine if we've just entered test_state on this step (a step is a go-round of the main loop)
bool entering(const StateMachine *sm, int test_state) {
    return sm->state_changed && sm->state == test_state;
}

// Determine if we're marked to exit this state. Put this in your case statements after anything that could cause a state change.
bool exiting(const StateMachine *sm, int test_state) {
    return sm->state != test_state;
}


// Sketch-specific structs

struct _strFCU
{
    
};

#endif //_STATE_MACHINE_H_

