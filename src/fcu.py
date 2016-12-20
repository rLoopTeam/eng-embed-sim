#!/usr/bin/env python

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