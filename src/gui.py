#!/usr/bin/env python

from pod import Pod
from tube import Tube
from pusher import Pusher
from sim import Sim, SimEndListener
#from fcu import fcu

import time
import logging
from units import *
from config import Config

import Queue

import Tkinter as tk

import random

class ServoDrive(object):
    # simulate values
    #def getVelocity(self): return random.randint(0,50)
    #def getTorque(self): return random.randint(50,100)
    def getVelocity(self): return 1
    def getTorque(self): return 0

class SimGui(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        
        self.root = args[0]
                
        self.servo = ServoDrive()
        self.canvas = tk.Canvas(self, background="#333333")
        self.canvas.pack(side="top", fill="both", expand=True)

        # create lines for velocity and torque
        self.velocity_line = self.canvas.create_line(0,0,0,0, fill="red")
        self.acceleration_line = self.canvas.create_line(0,0,0,0, fill="green")

        # start the update process
        #self.update_plot()
        
        self.data_queue = Queue.Queue()
    
    def step_callback(self, sensor, step_samples):
        for sample in step_samples:
            self.data_queue.put(sample)
    
    def update_plot(self):
        self.handle_data()
        #v = self.sim.pod.velocity
        #a = self.sim.pod.acceleration
        #v = 0
        #print "v: {}".format(v)
        #v = self.servo.getVelocity()
        #a = self.servo.getTorque()
        #print "v2: {}".format(v)
        #self.add_point(self.velocity_line, v)
        #self.add_point(self.acceleration_line, a)
        self.canvas.xview_moveto(1.0)
        self.after(100, self.update_plot)

    def handle_data(self):
        # Clear the queue
        size = self.data_queue.qsize()
        v_samples = []
        a_samples = []
        for i in xrange(size):
            sample = self.data_queue.get(False)
            v_samples.append(sample.v)
            a_samples.append(sample.a)

        self.add_points(self.velocity_line, v_samples)
        self.add_points(self.acceleration_line, a_samples)
            
    def add_points(self, line, data):
        coords = self.canvas.coords(line)
        for value in data: 
            x = coords[-2] + 1
            coords.append(x)
            coords.append(value)
            #coords = coords[-1200:] # keep # of points to a manageable size
        self.canvas.coords(line, *coords)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def add_point(self, line, y):
        coords = self.canvas.coords(line)
        x = coords[-2] + 1
        coords.append(x)
        coords.append(y)
        coords = coords[-1200:] # keep # of points to a manageable size
        self.canvas.coords(line, *coords)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))        


if __name__ == "__main__":
    import argparse
    import threading
    import time
    
    logging.basicConfig(level=logging.DEBUG)

    
    root = tk.Tk()
    simgui = SimGui(root)
    simgui.pack(side="top", fill="both", expand=True)

    # Handle arguments and simulator setup
    parser = argparse.ArgumentParser(description="rPod Simulation")
    parser.add_argument('configfile', metavar='config', type=str, nargs='+', default="None",
        help='Simulation configuration file(s) -- later files overlay on previous files')
    args = parser.parse_args()

    sim_config = Config()
    for configfile in args.configfile:
        sim_config.loadfile(configfile)
        
    sim = Sim(sim_config.sim)


    sim.pusher.start_push()
    
    simgui.sim = sim

    # Set up the gui to listen to the pod
    sim.pod_sensor.add_step_listener(simgui)

    simgui.update_plot()
    
    sim_thread = threading.Thread(target=sim.run, args=())
    sim_thread.daemon = True
    sim_thread.start()

    #while (True):
    #    time.sleep(0.01)
    #sim_thread.join()

    #sim.run()

    root.mainloop()

    """
    gui_thread = threading.Thread(target=root.mainloop, args=())
    gui_thread.start()
    
    gui_thread.join()
    """