#include "fcu_core.h"

extern struct sFCU;


void push_subsystem_command(int *command_var, int command)
{
    command_var = command;
}

int pop_subsystem_command(int *command_var)
{
    int command = command_var;
    command_var = NO_CMD;
    return command;
}

bool has_subsystem_command(int *command_var)
{
    return command_var >= 0;
}


// Brakes subsystem stuff
void cmd_brakes(E_CMD_BRAKES_T command)
{
    // Handle setting the command for the brakes
    push_
}

bool brakes_has_cmd()
{
    // Is there a command for the brakes?
    return sFCU.brakes.command >= 0;
}

int brakes_cmd_pop()
{
    int cmd = sFCU.brakes.command;
    sFCU.brakes.command = NO_CMD; // Wait-- will this work with the enum? Maybe have it as the first element of each enum...
    return cmd;
}


// Brakes-specific methods
void cmd_brakes_seek_pos(int position)
{
    // Set the position and register the command
    sFCU.brakes.target_pos = position;
    cmd_brakes(CMD_BRAKES_SEEK);
}

void cmd_brakes_hold()
{
    // Set anything that needs to be set for the brakes to hold
    // ...
    cmd_brakes(CMD_BRAKES_HOLD);  // Register the command
}


