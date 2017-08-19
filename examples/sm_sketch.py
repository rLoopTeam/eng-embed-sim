#!/usr/bin/env python


def state1():
    print('State 1')
    return state2
    
def state2():
    print('State 2')
    return state3
    
def state3():
    print('State 3')
    return done
    
def done():
    sm_done = True
    print("Done!")
    
def main():
    print("Entering main()")
    while not sm_done:
        state = state()
    print("Exiting main()")
    
state = state1


if __name__ == '__main__':
    sm_done = False
    main()