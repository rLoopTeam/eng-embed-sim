#!/usr/bin/env python

"""
This should really be a wrapper (or similar) around the DLL that is our actual firmware.
- What to call when? The timers (10ms and 100ms) for processing loops? 
- How to get data in and out? How does the firmware pick up what we're dropping off? What about interrupts?
- We want to log data independent of what the FCU/firmware is going, and we want to log data *about* the fcu/firmware
- The sensors will likely need to put data directly to the firmware by calling c functions. Maybe wrap those functions so we can do our own logging separately? 
    - Or sometimes the sensor get called back by the FCU to give up their data. They'll probably need a queue of some sort...
- Also we'll want to do things like check state in the FCU from time to time. How to do that? Can we access the strFCU from python? How often? 10ms? 
- 
"""



from c import *

class FcuMemWrapper:
    
    """ Wrapper to make a dict act like a struct (syntax-wise) """
    
    def __init__(self, mem):
        self.mem = mem

    def __getattr__(self, name):
        attr = self.mem.get(name, None)
        if isinstance(attr, dict):
            return FcuMemWrapper(self.mem.get(name))
        else:
            return attr


class Brake:
    def __init__(self, pod):
        self.pod = pod


class Fcu:
    
    def __init__(self, pod):
        self.pod = pod
        self.mem_init = {
            'strBrakes': [
                Brake(self.pod),
                Brake(self.pod)
            ],        
            'strSomething': {
                'other': ['a', 'b']
            }
        }
        self.mem = FcuMemWrapper(self.mem_init)
            
if __name__ == "__main__":
    fcu = Fcu(None)
    print fcu.mem.strBrakes[0]
    print fcu.mem.strSomething.other[0]