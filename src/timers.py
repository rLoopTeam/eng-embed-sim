#!/usr/bin/env python

# File:     timers.py
# Purpose:  Provide timers for the timed FCU callbacks
# Author:   Ryan Adams (radams@cyandata.com, @ninetimeout)
# Date:     2017-Jan-16

import time
from datetime import datetime
import threading

import numpy as np

class TimerMs:
    def __init__(self, interval_ms, callback):
        self.interval_ms = interval_ms
        self.callback = callback
        
        self.delay = self.interval_ms / 1000.0
        
        # Note: no need to calibrate, ms timing is pretty accurate without it.
        
        self.stop_flag = False

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


class TimerUsec: 
    def __init__(self, interval_usec, callback):
        self.interval_usec = interval_usec
        self.callback = callback

        self.requested_delay = interval_usec / 1000000.0
        #self.overhead = 0.0000005  # This is a decent guess
        self.overhead = 0.0
        self.delay = self.requested_delay - self.overhead
        
        self.stop_flag = False
        
    def start_threaded(self):
        t = threading.Thread(target=self.start, args=())
        t.daemon = True
        t.start()
        return t

    def calibrate(self, samples):
        cal_times = []
        
        t0 = time.clock()
        while len(cal_times) < samples:
            if self.stop_flag:
                pass   # Don't do anything, but we need the if statement to be consistent with the run method timing
            t1 = time.clock()
            if t1 - t0 >= self.delay:
                cal_times.append(t1 - t0)  # Hopefully this is about the same amount of time as the call, but it doesn't really matter as we've already calculated t1
                t0 = t1
        
        tl_time = 0.0
        n_times = 0
        for t in cal_times:
            #print "{:.20f}, {:.20f}".format(t, self.requested_delay)
            if t <= (self.requested_delay * 3) or True:  # Skip the outliers
                tl_time += t
                n_times += 1
        
        if n_times == 0:
            print "Hmm -- got {} but all were outliers...".format(len(cal_times))
            exit()
        
        avg_time = tl_time / n_times
        print "Calibration: target is {:.20f}, measured is {:.20f} with {} samples and {} outliers.".format(self.interval_usec, avg_time, samples, len(cal_times) - n_times)
        adjustor = 25 * (avg_time - self.requested_delay)  # Note: 25 because windows. Not a great thing to have a magic number, but it works
        old_overhead = self.overhead
        self.overhead += adjustor  # Adjust overhead
        print "Adjusting overhead by {:.20f} from {:.20f} to {:.20f}".format(adjustor, old_overhead, self.overhead)
        self.delay = self.requested_delay - self.overhead  # Recalculate delay
        print "Delay is now {:.20f} (target {:.20f})".format(self.delay, self.requested_delay)
        


    def start(self):
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
        

class TimerUsecTest:
    def __init__(self, timer_usec):
        self.timer_usec = timer_usec
        self.timer_usec.callback = self.callback

        self.times = []

        self.run_t0 = None
        self.t0 = None
        self.t1 = None
    

    def run(self, seconds):
        #t0 = datetime.now()

        self.times = []
        self.run_t0 = time.clock()

        self.timer_usec.callback = self.callback
        self.timer_usec.run_threaded()
        
        print "Running TimerUsecTest with TimerUsec.delay {:.20f}".format(self.timer_usec.delay)
        
        # Wait for the appropriate number of seconds
        while time.clock() - self.run_t0 <= seconds:
            pass
        
        self.timer_usec.stop()

        tl_time = 0.0
        n_times = 0
        
        for t in self.times:
            if t <= 3 * self.timer_usec.requested_delay:
                tl_time += t
                n_times += 1
        
        avg_time = (tl_time / n_times)
        n_outliers = len(self.times) - n_times
        
        print "{} calls completed in {} seconds with {} outliers; average of {:.20f} (target {:.20f})".format(n_times, seconds, n_outliers, avg_time, self.timer_usec.requested_delay)
        
        
    def callback(self):
        if self.t0 is None:
            self.t0 = time.clock()
            return 
            
        self.t1 = time.clock()
        self.times.append(self.t1 - self.t0)
        self.t0 = self.t1
        
    
    
class TimeSync:
    def __init__(self, sim):
        """ Threaded clock synchronizer """
        self.sim = sim

        self.last_step_t = 0.0
        self.last_step_duration = None
    
    def step_callback(self, sensor, step_samples):
        """ Gets called during every step. Samples are the elapsed simulator time """
        new_step_t = time.clock()
        if self.last_step_duration is None:
            self.last_step_t = new_step_t
            return
        
        self.last_step_duration = time.clock() - self.last_step_t
        
        
    def run(self):
        pass

class TimerTest:
    # Test a 10 microsecond timer in python on windows
    
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

    #tt = TimerTest(100000)
    #tt.run()

    #print tt.results()

    tu = TimerUsec(50, None)
    tut = TimerUsecTest(tu)
    tut.run(5)

    tu.calibrate(1000)
    
    tut.run(5)
