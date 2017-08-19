#!/usr/bin/env python

# Ryan Adams
# 2017-Jul-02
# Experimenting with a fault table (table[state][fault_code] = fn_ptr)


def print_fault(state, fault_code, msg):
    print("[{}][{}]: {}".format(state, fault_code, msg))
    
def ignore_fault(state, fault_code, msg):
    print("ignoring [{}][{}]: {}".format(state, fault_code, msg))

states = {'IDLE': 0, 'TEST_MODE': 1, 'OTHER_STATE': 2}

faults = {'TOO_MUCH_CAKE': 1, 'WONKINESS': 2, 'GLADHANDING': 3}

fault_table = {}
for state, state_id in states.iteritems():
    fault_table[state_id] = {}
    
fault_table[states['IDLE']][faults['TOO_MUCH_CAKE']] = print_fault
fault_table[states['IDLE']][faults['WONKINESS']] = print_fault
fault_table[states['IDLE']][faults['GLADHANDING']] = ignore_fault
fault_table[states['TEST_MODE']][faults['TOO_MUCH_CAKE']] = ignore_fault
fault_table[states['TEST_MODE']][faults['WONKINESS']] = ignore_fault
fault_table[states['TEST_MODE']][faults['GLADHANDING']] = print_fault


def main():
    counter = 0
    state = 'IDLE'

    print fault_table

    while True:

        # Switch to TEST_MODE
        if counter > 10:
            if state == 'IDLE':
                state = 'TEST_MODE'
                continue

        if counter > 20:
            break

        fault_handlers = fault_table[states[state]]

        for fault, fault_id in faults.iteritems():
            fault_handlers[fault_id](state, fault, "Handled")
        
        counter += 1
        


if __name__ == '__main__':
    main()        


