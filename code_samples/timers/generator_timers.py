import time
from datetime import datetime
import logging
import threading
import numpy as np

#from units import Units


class ThreadedTimer:
    """ Basic timer with callback and time dialation """

    def __init__(self, interval_sec, callback):
        self.interval = interval_sec
        self.callback = callback

        # Time dialation factor (for adjusting real time to sim time for timers)
        self.dialation = 1.0
        self.delay = self.interval  # Note: this will be adjusted by the set_dialation method

        self.stop_flag = False

    def update_dialation(self, dialation):
        """ set the time-dialated delay """
        self.dialation = dialation
        self.delay = self.interval * self.dialation

    def start_threaded(self):
        t = threading.Thread(target=self.run, args=())
        t.daemon = True
        t.start()
        return t

    def run(self):
        t0 = time.clock()
        while True:
            if self.stop_flag:  # Break out if we need to
                self.stop_flag = False  # so we can restart
                break
            t1 = time.clock()
            if t1 - t0 >= self.delay:
                self.callback()
                t0 = t1        

    def stop(self):
        self.stop_flag = True
        
        
class GeneratorTimer:
    
    def __init__(self, interval_sec, callback):
        self.interval = interval_sec
        self.callback = callback

        # Time dialation factor (for adjusting real time to sim time for timers)
        self.dialation = 1.0
        self.delay = self.interval  # Note: this will be adjusted by the set_dialation method

        self.stop_flag = False

    def update_dialation(self, dialation):
        """ set the time-dialated delay """
        self.dialation = dialation
        self.delay = self.interval * self.dialation

    def start_threaded(self):
        t = threading.Thread(target=self.run, args=())
        t.daemon = True
        t.start()
        return t

    def generator(self):
        t0 = time.clock()
        while True:
            if self.stop_flag:  # Break out if we need to
                self.stop_flag = False  # so we can restart
                break
            t1 = time.clock()
            if t1 - t0 >= self.delay:
                t0 = t1        
                yield self.callback(self)
            else:
                print "(no tick)"
                yield

    def stop(self):
        self.stop_flag = True
        

class MultiTimer:
    def __init__():
        self.stop_flag = False
        self.timers = []
    
    def add_timer(timer):
        self.timers.append(timer)
        
    def generator(self):
        pass

class TMTimer:
    def __init__(self):
        self.timers = []
        self.stop_flag = False
        
        self.dialation = 1.0
        
        # Record of hits and misses (tick/no tick)
        self.record = []  
        
    def timer(self, name, interval_sec, callback):
        self.timers.append(self._generator(name, interval_sec, callback))
                
    def _generator(self, name, interval_sec, callback):
        t0 = time.clock()
        while True:
            delay = interval_sec * self.dialation
            if self.stop_flag:
                break
            t1 = time.clock()
            if t1 - t0 >= delay:
                t0 = t1
                self.record.append(1)
                yield callback(name)
            else:
                yield self.record.append(0)
                #print "no tick"
                #yield
    
    def run(self, n):
        counter = 0
        while counter <= n:
            for timer in self.timers:
                timer.next()
            counter += 1
        print "Done!"
        print self.record
        
def print_callback(name):
    pass
    #print "Timer {} ticked".format(name)
    
if __name__ == "__main__":
    
    t = TMTimer()
    #t.timer("0.001s timer", 0.001, print_callback)
    #t.timer("0.002s timer", 0.002, print_callback)
    #t.timer("0.003s timer", 0.003, print_callback)
    #t.timer("0.004s timer", 0.004, print_callback)
    #t.timer("0.005s timer", 0.005, print_callback)
    #t.timer("0.1s", 0.1, print_callback)
    #t.timer("0.2s", 0.2, print_callback)
    #t.timer("0.3s", 0.3, print_callback)
    #t.timer("0.4s", 0.4, print_callback)
    #t.timer("0.5s", 0.5, print_callback)
    
    t.timer("0.0001", 0.000002, print_callback)
    
    t.run(200)
