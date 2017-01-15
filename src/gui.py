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

import Tkinter as tk
import ttk
import numpy as np

# Note: imports need to be in the right order or it will crash
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import matplotlib.pyplot as plt
import matplotlib.animation as animation

from collections import OrderedDict

import Queue

import random

from matplotlib.font_manager import FontProperties

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


class TkAnimGui:
    def __init__(self, sim):
        self.sim = sim
        self.fig = plt.Figure()
        self.root = tk.Tk()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)

        #self.mat = TkGraphBase(self.fig, self.sim)
        self.mat = TkGraphForces(self.fig, self.sim)

        self.canvas.get_tk_widget().grid(column=0,row=1)
    
    def run(self):
        self.root.mainloop()

class GuiLayout:
    def __init__(self, sim):
        self.sim = sim
        self.root = tk.Tk()

        self.layout()

    def layout1(self):
        # Set up components
        content = ttk.Frame(self.root)
        
        mup = MultiPlot()
        
        graph1 = ttk.Frame(content)
        graph1_fig = mup.fig1
        graph1_canvas = FigureCanvasTkAgg(graph1_fig, master=graph1)
        ani = animation.FuncAnimation(mup.fig1, mup.au.update, blit=False, interval=10, repeat=False)
        graph1_canvas.get_tk_widget().grid(column=0, row=0)


        content.grid(column=0, row=0)
        graph1.grid(column=0, row=0)
        #graph2.grid(column=0, row=1)

    def layout(self):
        
        # Set up components
        content = ttk.Frame(self.root)
        
        graph2 = ttk.Frame(content)
        graph2_fig = plt.Figure()
        graph2_canvas = FigureCanvasTkAgg(graph2_fig, master=graph2)
        TkGraphBase(graph2_fig, self.sim)
        graph2_canvas.show()
        graph2_canvas.get_tk_widget().grid(column=0, row=0)

        graph1 = ttk.Frame(content)
        graph1_fig = plt.Figure()
        graph1_canvas = FigureCanvasTkAgg(graph1_fig, master=graph1)
        TkGraphForces(graph1_fig, self.sim)  # hate this
        graph2_canvas.show()  # Don't forget this!
        graph1_canvas.get_tk_widget().grid(column=0, row=0)
        
        print "graph1_fig: {}; graph2_fig: {}".format(repr(graph1_fig), repr(graph2_fig))
        
        # Place components in the grid
        content.grid(column=0, row=0)
        graph1.grid(column=0, row=0)
        graph2.grid(column=0, row=1)
    
    def run(self):
        self.root.mainloop()


class TkGraphBase:
    def __init__(self, fig, sim):
        self.fig = fig
        self.sim = sim
        self.ax = self.fig.add_subplot(5, 1, 1)
        
        # Make it prettier
        #self.fig.set_facecolor("#2E333A")
        self.ax.get_xaxis().tick_bottom()
        self.ax.get_yaxis().tick_left()
        self.ax.set_frame_on(True)
        self.ax.tick_params(labelsize=8)
        self.ax.set_axis_bgcolor("#2E333A")
        
        self.x = [] # x-array
        self.y = [] # y-array

        #self.ani = animation.FuncAnimation(self.fig, self.animate, np.arange(1, 100), interval=25, blit=False, init_func=self.init)
        self.ani = animation.FuncAnimation(self.fig, self.update, interval=25, blit=False, init_func=self.init)

    def init(self):
        self.line, = self.ax.plot(self.x, self.y, color="#5992F9")  # Initial line (before scrolling)
        self.ax.set_xlim(0, 1270)  # Position
        self.ax.set_ylim(0, 160)   # Velocity

    def update(self, i):
        self.x.append(self.sim.pod.position)
        self.y.append(self.sim.pod.velocity)
        self.line.set_xdata(self.x)
        self.line.set_ydata(self.y)  # update the data

        return self.line,

class TkGraphForces(TkGraphBase):
    def __init__(self, fig, sim):
        TkGraphBase.__init__(self, fig, sim)

        self.xs = []
        self.force_ys = {}
        
        self.dlines = OrderedDict()
        self.lines = []
        
        self.ani = animation.FuncAnimation(self.fig, self.update, interval=25, blit=False, init_func=self.init)

        
    def init(self):
        self.xs.append(0)
        for name, force in self.sim.pod.step_forces.iteritems():
            self.force_ys[name] = [force.x]  # Initialize lists
            self.dlines[name], = self.ax.plot(self.xs, self.force_ys[name], label=name)  # Initial line (before scrolling)
            
        self.ax.set_xlim(0, 1270)  # Position
        self.ax.set_ylim(150, -1400)
        #self.ax.invert_yaxis()
        
        fontP = FontProperties()
        fontP.set_size('small')

        #self.ax.legend(loc='bottom center', ncol=len(self.dlines), prop=fontP)
        
    def update(self, i):
        self.xs.append(self.sim.pod.position)
        for name, force in self.sim.pod.step_forces.iteritems():
            line = self.dlines[name]
            self.force_ys[name].append(force.x)
            line.set_xdata(self.xs)
            line.set_ydata(self.force_ys[name])
         
        #self.ax.relim()
        #self.ax.autoscale()
        
        #return self.lines
        return [line for line in self.dlines.values()]  

class TkGraphVelocity(TkGraphBase):
    # @todo: Move the code from the base to here
    def __init__(self, fig, sim):
        TkGraphBase.__init__(self, fig, sim)
    

class ArtistUpdater:
    def __init__(self):
        self.artists = []
        
    def add_artist(self, artist):
        self.artists.append(artist)
        
    def update(self, i):
        print "Update!"
        lines = []
        for artist in self.artists:
            ret = artist.update(i)
            if isinstance(ret, list):
                lines.extend(ret)
            else:
                lines.append(ret)
        return lines
        
class LineManager:
    def __init__(self, ax):
        self.ax = ax
        self.xs = []
        self.ys = []
        self.line = self.ax.plot(self.xs, self.ys)
    
    def update(self, i):
        self.xs.append(i)
        self.ys.append(random.randint(0,100))
        self.line.set_xdata(self.xs)
        self.line.set_ydata(self.ys)

        self.ax.relim()
        self.ax.autoscale()

        return [self.line]


class MultiPlot:
    def __init__(self):
        self.fig1 = plt.figure()
        self.fig2 = plt.figure()

        self.fig1ax1 = self.fig1.add_subplot(2,1,1)
        self.fig1ax2 = self.fig1.add_subplot(2,1,2)
        
        self.fig2ax1 = self.fig2.add_subplot(1,1,1)
        
        self.fig1lm1 = LineManager(self.fig1ax1)
        self.fig1lm2 = LineManager(self.fig1ax2)    
        self.fig2lm1 = LineManager(self.fig2ax1)
        
        self.au = ArtistUpdater()
        self.au.add_artist(self.fig1lm1)
        self.au.add_artist(self.fig1lm2)
        self.au.add_artist(self.fig2lm1)
        
        

if __name__ == "__main__":
    import argparse
    import threading
    import time
    
    logging.basicConfig(level=logging.DEBUG)

    
    #root = tk.Tk()
    #simgui = SimGui(root)
    #simgui.pack(side="top", fill="both", expand=True)

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
    
    #simgui.sim = sim

    # Set up the gui to listen to the pod
    #sim.pod_sensor.add_step_listener(simgui)

    #simgui.update_plot()
    
    sim_thread = threading.Thread(target=sim.run, args=())
    sim_thread.daemon = True

    from timers import TimerTest
    tt = TimerTest(100000)
    timer_thread = threading.Thread(target=tt.run, args=())
    timer_thread.daemon = True
    #tt.run()

    #print tt.results()

    #while (True):
    #    time.sleep(0.01)
    #sim_thread.join()

    #sim.run()

    sim_thread.start()
    timer_thread.start()

    #gui = TkAnimGui(sim)
    gui = GuiLayout(sim)
    gui.run()

    #root.mainloop()

    """
    gui_thread = threading.Thread(target=root.mainloop, args=())
    gui_thread.start()
    
    gui_thread.join()
    """