#!/usr/bin/env python
# coding=UTF-8

# File:     timers.py
# Purpose:  Timers for the timed FCU callbacks, including time dialation
# Author:   Ryan Adams (radams@cyandata.com, @ninetimeout)
# Date:     2017-Jan-16

import time
from datetime import datetime
import logging
import threading
import numpy as np

from units import Units


class Timer:
    """ 
    Basic timer with callback and time dialation.
    Note: This is a simple timer and must be run in a thread or as 
          the main loop in a process. See CallbackTimer below for
          a more sophisticated generator-based timer. 
    """

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
        """ Run the timer in a separate thread """

        t = threading.Thread(target=self.run, args=())
        t.daemon = True
        t.start()
        return t

    def run(self):
        """ Run the timer """

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
        """ Flag the timer to stop """

        self.stop_flag = True


class TimeDialator(object):
    """ 
    A timer that controls the dialation of time (sim time vs real time) for other timers.
    Note that this can either be run as a timer or stepped directly by the simulation (use either, but not both probably.)
    @todo: Probably split this into two classes: one that can be run as a timer and one that is stepped by the simulator. Stepping will be more accurate. 
    """
    
    def __init__(self, sim, config=None):
        self.sim = sim
        self.logger = logging.getLogger("TimeDialator")
        
        self.timers = []

        self.last_real_time = None
        self.last_sim_time = None

        # Exponential moving average filter to de-jumpify the time dialation
        self.ema_alpha = 0.08  # Lower alpha gives previous values more influence in the current value
        self.ema_previous = 1.0
        self.ema_current = 1.0
        
        # Dialation factor
        self.dialation = 1.0

    def add_timer(self, timer):
        """ Add a timer whose dialation we will control """
        self.timers.append(timer)
    
    def add_timers(self, timers):
        """ Add multiple timers (convenience method) """
        self.timers.extend(timers)
    
    def dialate_time(self, dt_usec=None):
        """ Calculate the time dialation and set it on our timers """

        if self.last_real_time is None:
            # Initialize here so that we can ignore thread startup times and whatnot
            self.last_real_time = time.clock()
            self.last_sim_time = self.sim.elapsed_time_usec * 1000000.0
            return

        real_time_diff = time.clock() - self.last_real_time
        if dt_usec is None:
            # We didn't have one passed in, so calculate it. 
            # This is used if we're running as a timer rather than directly stepped. 
            sim_time_diff = (self.sim.elapsed_time_usec / 1000000.0) - self.last_sim_time 
        else:
            sim_time_diff = dt_usec / 1000000.0
            
        # Dialate time
        # Dialation is the ratio of real time to sim time: 
        # 10s real time to 1s sim time = dialation factor of 10. 
        # Or 1s real time to 2s sim time = dialation factor of .5
        self.dialation = real_time_diff / sim_time_diff

        # Apply an exponential moving average filter so dialation is not so jittery
        self.ema_previous = self.ema_current   # Move us along
        self.ema_current = self.ema_alpha * self.dialation + (1 - self.ema_alpha) * self.ema_previous
        self.dialation = self.ema_current  # We could just set it in the line above, but doing this allows us to separate the code for the filter
        
        # Update dialation factor for all of our timers
        for timer in self.timers:
            timer.update_dialation(self.dialation)
        #self.logger.debug("Set time dialation to {}".format(self.dialation))
        
        # Update our timepoints
        self.last_real_time = time.clock()
        self.last_sim_time = self.sim.elapsed_time_usec / 1000000.0

    def step(self, dt_usec):
        """ step method so that we can be directly stepped instead of used as a timer """
        self.dialate_time(dt_usec)
        
# @todo: add a TimeAdjustor class that adjust delay (and maybe overhead) for timers that are lagging/speeding

class TimeRunner:
    """ Container for operating multiple callback timers simultaneously """

    def __init__(self):
        self.timers = []
        self.logger = logging.getLogger("TimeRunner")
        
        self.end_flag = False

    def add_timer(self, timer):
        self.timers.append(timer)
    
    def end_callback(self, sim):
        """ Called by the simulator when an end condition is triggered """

        self.logger.debug("TimeRunner.end_callback() called.")
        self.end_flag = True

    def run(self):
        while True:

            if self.end_flag:
                # If the simulation has ended, stop the timers and break
                for timer in self.timers:
                    timer.stop()
                break

            for timer in self.timers:
                next(timer)

    def run_threaded(self):
        t = threading.Thread(target=self.run, args=())
        t.daemon = True
        t.start()
        return t    
    
    def get_timers(self):
        return self.timers


class CallbackTimer(object):
    """ Generator-based callback timer """

    def __init__(self, interval_sec, callback, **kwargs):
        self.interval = interval_sec
        self.callback = callback
        self.stop_flag = False
        self.dialation = 1.0

        # Initialize delay
        self.delay = self.interval * self.dialation

        # kwargs
        self.name = kwargs.get('name', "{}s timer".format(self.interval))
        self.debug_callback = kwargs.get('debug_callback', None)

        self.gen = self._create_generator()

    def _create_generator(self):
        """ 
        Create a generator that calls the callback if enough time has
        passed; otherwise just yield. 
        """

        t0 = time.clock()
        while True:
            if self.stop_flag:
                break
            t1 = time.clock()
            # delay = self.interval * self.dialation  # @todo: can we move this out of here for better performance? 
            if t1 - t0 >= self.delay:
                t0 = t1
                if self.debug_callback is not None:
                    self.debug_callback(self)
                yield self.callback()
            else:
                yield
        
    def next(self):
        next(self.gen)

    def stop(self):
        self.stop_flag = True

    def update_dialation(self, dialation):
        """ set the time-dialated delay """
        self.dialation = dialation
        self.delay = self.interval * self.dialation


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

    def debug_print(timer):
        print timer.name        

    def do_nothing():
        pass

    #tt = TimerTest(100000)
    #tt.run()

    tr = TimeRunner()
    tr.add_timer(CallbackTimer(0.01, do_nothing, debug_callback=debug_print, name="0.01 second timer"))
    tr.add_timer(CallbackTimer(0.03, do_nothing, debug_callback=debug_print))
    
    tr.run()
