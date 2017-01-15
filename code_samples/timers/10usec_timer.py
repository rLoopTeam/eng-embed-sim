#!/usr/bin/env python

# Test a 10 microsecond timer in python on windows

import time
from datetime import datetime

"""
def measure_clock():
    t0 = time.clock()
    t1 = time.clock()
    while t1 == t0:
        t1 = time.clock()
    return (t0, t1, t1-t0)

t = reduce( lambda a,b:a+b, [measure_clock()[2] for i in range(1000000)] )/1000000.0

print "Resolution: {0:.20f}".format(t)

print "Let's try calling a function every 10usec:"

counter = 0
t0 = time.clock()
while counter < 100:
    t1 = time.clock()
    if t1 - t0 >= 0.00001:  # 10 microseconds
        print "{0:.20f}".format(t1 - t0)  # Note: print takes a while...
        t0 = t1
    counter += 1

"""
import numpy as np


class TimerTest:
    
    def __init__(self, n):
        self.n = n
        self.q = []
        self.total_time = 0.0
        
    def run(self):
        start = datetime.now()
        t0 = time.clock()
        for i in xrange(self.n):
            if i == 3:
                start = datetime.now()
            t1 = time.clock()
            if t1 - t0 >= 0.000009:  # 10 microseconds, -.2usec for processing time
                self.q.append(t1 - t0)
                t0 = t1
        
        self.total_time = datetime.now() - start
        
    def results(self):
        a = []
        for t in tt.q:
            a.append("{0:.20f}".format(t))

        a.append("-- Results -----")
        a.append("Timer test completed {} ticks in {}s".format(len(tt.q), tt.total_time))
        a.append("Average time between calls: {0:.20f}".format(np.mean(tt.q[3:])))
        
        return "\n".join(a)
        
if __name__ == "__main__":
    print "-- Timer Test -----"

    tt = TimerTest(100000)
    tt.run()

    print tt.results()
