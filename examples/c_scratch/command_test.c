/**
 * Purpose: Demonstrate queueable command structure with arguments
 * Author:  Ryan Adams
 * Date:    2017-07-30
 */

#include <stdio.h>

// Each command has different parameters

// Commands
enum {BLAH = 1U, BLOH} E_CMD_T;

// Blah command args
typedef struct 
{
    int test;
    int ing;
} strBlah;

// Bloh command args
typedef struct
{
    int target_speed;
} strBloh;

// Generic command with arguments
typedef struct {

    // Command
    E_CMD_T command;

    // Union of argument structs for various commands
    union {
        strBlah blah;
        strBloh bloh;
    } args;

} strCmd;


void handle_command(strCmd command) 
{
    switch (command.command)
    {
        case BLAH:
            printf("Command BLAH: test=%d, ing=%d\n", command.args.blah.test, command.args.blah.ing);
            break;
        case BLOH:
            printf("Command BLOH: target_speed=%d\n", command.args.bloh.target_speed);
            break;
    }
   
}


strCmd get_blah_command(int test, int ing)
{
    strCmd command;
    command.command = BLAH;
    command.args.blah.test = test;
    command.args.blah.ing = ing;
    return command;
}

strCmd get_bloh_command(int target_speed)
{
    strCmd command;
    command.command = BLOH;
    command.args.bloh.target_speed = target_speed;
    return command;
}

int main(void)
{
    // do nothing
    strCmd cmdBlah;
    strCmd cmdBloh;
    
    // Manual Test
    cmdBlah.command = BLAH;
    cmdBlah.args.blah.test = 2;
    cmdBlah.args.blah.ing = 3;
    
    cmdBloh.command = BLOH;
    cmdBloh.args.bloh.target_speed = 14;
    
    handle_command(cmdBlah);
    handle_command(cmdBloh);

    // Function test
    strCmd blah = get_blah_command(5, 6);
    strCmd bloh = get_bloh_command(56);
    
    handle_command(blah);
    handle_command(bloh);
    
    
}