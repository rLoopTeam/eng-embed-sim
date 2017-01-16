#!/usr/bin/env python

# Test a 10 microsecond timer in python on windows

import time
from datetime import datetime

import numpy as np


class TimerTest:
    
    def __init__(self, n):
        self.n = n
        self.q = []
        self.total_time = 0.0
        self.adjusted_delay = 0.0000005
        
    def run(self):
        start = datetime.now()
        t0 = time.clock()
        for i in xrange(self.n):
            if i == 3:
                start = datetime.now()
            t1 = time.clock()
            if t1 - t0 >= self.adjusted_delay:  # 10 microseconds, minus some amount for processing time
                self.q.append(t1 - t0)
                t0 = t1
        
        self.total_time = datetime.now() - start
        
        print self.results()
        
    def results(self):
        a = []
        #for t in self.q:
        #    a.append("{0:.20f}".format(t))

        a.append("-- Results -----")
        a.append("Timer test completed {} ticks in {}s".format(len(self.q), self.total_time))
        a.append("Average time between calls: {0:.20f} usec".format(np.mean(self.q[3:]) * 1000000))
        
        return "\n".join(a)
        
if __name__ == "__main__":
    print "-- Timer Test -----"

    tt = TimerTest(100000)
    tt.run()

    #print tt.results()
