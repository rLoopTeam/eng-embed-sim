#include <stdio.h>

#include "fcu_core.h"
#include "state_machine.h"

struct _strFCU sFCU;

int main(void) 
{
    sFCU.brakes.brake[0].limit[0].eSwitchState = 1;

    // Test creation of a pointer to a state machine
    StateMachine *main_sm = &sFCU.sm;
    main_sm->state = 4;
    printf("main sm state: %d", sFCU.sm.state);  // should be 4
    
}