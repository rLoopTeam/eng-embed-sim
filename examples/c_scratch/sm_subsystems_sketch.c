#include <stdio.h>

enum {A_STATE, B_STATE, C_STATE} E_MAIN_STATES_T;
enum {GO_A, GO_B, GO_C} E_MAIN_CMD_T;

enum {X_STATE, Y_STATE, Z_STATE} E_SUBSYSTEM_STATES_T;
enum {GO_X, GO_Y, GO_Z} E_SUBSYSTEM_CMD_T;

void main_sm_init()
{
    
}

void main_sm_process()
{
    
}

void subsystem_sm_init()
{
    
}

void subsystem_sm_process()
{
    
}


void init()
{
    main_sm_init();
    subsystem_sm_init();
}

void process()
{
    main_sm_process();
    subsystem_sm_process();
}

int main(void)
{
    init();
    
    while(1)
    {
        process();
    }
}