/**
 * Purpose: Demonstrate queueable command structure with arguments
 * Author:  Ryan Adams
 * Date:    2017-07-30
 */

#include <stdio.h>

// Each command has different parameters

// Commands
typedef enum {BRAKES_BLAH = 1U, BRAKES_BLOH} E_BRAKES_CMD_T;

// Blah command args
typedef struct 
{
    int test;
    int ing;
} strBrakesBlah;

// Bloh command args
typedef struct
{
    int target_speed;
} strBrakesBloh;

// Brakes command with arguments
typedef struct strBrakesCmd {

    // Command
    E_BRAKES_CMD_T command;

    // For queueing
    struct strBrakesCmd *next;

    // Union of argument structs for various commands
    union {
        strBrakesBlah blah;
        strBrakesBloh bloh;
    } args;

} strBrakesCmd;

// Brakes command queue
typedef struct 
{
    strBrakesCmd *head;
    strBrakesCmd *tail;
} strBrakesCmdQueue;


void exec_brakes_command(strBrakesCmd command) 
{
    switch (command.command)
    {
        case BRAKES_BLAH:
            printf("Command BRAKES_BLAH: test=%d, ing=%d\n", command.args.blah.test, command.args.blah.ing);
            break;
        case BRAKES_BLOH:
            printf("Command BRAKES_BLOH: target_speed=%d\n", command.args.bloh.target_speed);
            break;
    }
   
}

strBrakesCmdQueue *newBrakesCmdQueue(void)
{
    
}

void enque_brakes_command(strBrakesCmd command)
{
    
}

void deque_command(strBrakesCmd command)
{
    
}

strBrakesCmd get_blah_command(int test, int ing)
{
    strBrakesCmd command;
    command.command = BRAKES_BLAH;
    command.args.blah.test = test;
    command.args.blah.ing = ing;
    return command;
}

strBrakesCmd get_bloh_command(int target_speed)
{
    strBrakesCmd command;
    command.command = BRAKES_BLOH;
    command.args.bloh.target_speed = target_speed;
    return command;
}

int main(void)
{
    // do nothing
    strBrakesCmd cmdBlah;
    strBrakesCmd cmdBloh;
    
    // Manual Test
    cmdBlah.command = BRAKES_BLAH;
    cmdBlah.args.blah.test = 2;
    cmdBlah.args.blah.ing = 3;
    
    cmdBloh.command = BRAKES_BLOH;
    cmdBloh.args.bloh.target_speed = 14;
    
    exec_brakes_command(cmdBlah);
    exec_brakes_command(cmdBloh);

    // Function test
    strBrakesCmd blah = get_blah_command(5, 6);
    strBrakesCmd bloh = get_bloh_command(56);
    
    exec_brakes_command(blah);
    exec_brakes_command(bloh);
        
}