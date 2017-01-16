#!/usr/bin/env python

from pod import Pod
from tube import Tube
from pusher import Pusher
from sim import Sim

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

#from matplotlib.font_manager import FontProperties

# IMPORTANT: If you're getting one or more graphs that fail to initialize properly, clear fontList.cache from the following directory.
# ^ This happened on Windows; hasn't happened on mac. Probably should file a bug. 
print "Cachedir: {}".format(matplotlib.get_cachedir())

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
    def __init__(self, simrunner):
        self.simrunner = simrunner
        self.sim = simrunner.sim
        self.root = tk.Tk()

        self.layout()

    def layout(self):
        
        self.root.geometry('800x700')
        
        # Set up components
        content = ttk.Frame(self.root, width=1240, height=1000)
        
        graph2 = ttk.Frame(content, width=200, height=60)
        graph2_fig = plt.figure(1, figsize=(8,1.5), dpi=100)
        graph2_canvas = FigureCanvasTkAgg(graph2_fig, master=graph2)
        TkGraphBase(graph2_fig, self.sim)
        graph2_canvas.show()
        graph2_canvas.get_tk_widget().grid(column=0, row=0)

        graph1 = ttk.Frame(content, width=200, height=60)
        graph1_fig = plt.figure(2, figsize=(8,1.5), dpi=100)
        graph1_canvas = FigureCanvasTkAgg(graph1_fig, master=graph1)
        TkGraphForces(graph1_fig, self.sim)  # hate this
        graph2_canvas.show()  # Don't forget this!
        graph1_canvas.get_tk_widget().grid(column=0, row=0)

        graph_brakes = ttk.Frame(content, width=200, height=60)
        graph_brakes_fig = plt.figure(3, figsize=(8,1), dpi=100)
        graph_brakes_canvas = FigureCanvasTkAgg(graph_brakes_fig, master=graph_brakes)
        TkGraphBrakes(graph_brakes_fig, self.sim)
        graph_brakes_canvas.show()  # Don't forget this!
        graph_brakes_canvas.get_tk_widget().grid(column=0, row=0)

        graph_height = ttk.Frame(content, width=200, height=60)
        graph_height_fig = plt.figure(4, figsize=(8,1), dpi=100)
        graph_height_canvas = FigureCanvasTkAgg(graph_height_fig, master=graph_height)
        TkGraphHeight(graph_height_fig, self.sim)
        graph_height_canvas.show()  # Don't forget this!
        graph_height_canvas.get_tk_widget().grid(column=0, row=0)

        graph_accel = ttk.Frame(content, width=200, height=60)
        graph_accel_fig = plt.figure(5, figsize=(8,1.5), dpi=100)
        graph_accel_canvas = FigureCanvasTkAgg(graph_accel_fig, master=graph_accel)
        TkGraphAccel(graph_accel_fig, self.sim)
        graph_accel_canvas.show()  # Don't forget this!
        graph_accel_canvas.get_tk_widget().grid(column=0, row=0)
        
        #print "graph1_fig: {}; graph2_fig: {}".format(repr(graph1_fig), repr(graph2_fig))
        
        buttons = ttk.Frame(content, width=300, height=100)
        btnStart = ttk.Button(buttons, text="Start", command=self.simrunner.run_threaded)
        btnCancel = ttk.Button(buttons, text="Exit", command=self.root.destroy)
        btnBrakeNow = ttk.Button(buttons, text="Brake NOW", command=self.sim.pod.brakes.close_now)
        btnBrake = ttk.Button(buttons, text="Brake Regular", command= lambda: self.sim.pod.brakes._move_to_gap_target(0.0025))
        
        # Place components in the grid
        content.grid(column=0, row=0)
        graph1.grid(column=0, row=0)
        graph2.grid(column=0, row=1)
        graph_brakes.grid(column=0, row=2)
        graph_height.grid(column=0, row=3)
        graph_accel.grid(column=0, row=4)
    
        buttons.grid(row=5)
        btnStart.grid(column=1, row=0)
        btnCancel.grid(column=2, row=0)
        btnBrakeNow.grid(column=3, row=0)
        btnBrake.grid(column=4, row=0)
    
    def run(self):
        self.root.mainloop()


class TkGraphBase:
    def __init__(self, fig, sim):
        self.fig = fig
        self.sim = sim
        self.ax = self.fig.add_subplot(1, 1, 1)
        
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
        self.ax.set_xlim(-50, 1270)  # Position
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
        
        self.ani = animation.FuncAnimation(self.fig, self.update, interval=10, blit=False, init_func=self.init)

        
    def init(self):
        self.xs.append(0)
        for name, force in self.sim.pod.step_forces.iteritems():
            self.force_ys[name] = [force.x]  # Initialize lists
            self.dlines[name], = self.ax.plot(self.xs, self.force_ys[name], label=name)  # Initial line (before scrolling)
            
        self.ax.set_xlim(-50, 1270)  # Position
        self.ax.set_ylim(150, -1400)
        #self.ax.invert_yaxis()
        
        #fontP = FontProperties()
        #fontP.set_size('small')

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


class TkGraphBrakes(TkGraphBase):
    def __init__(self, fig, sim):
        TkGraphBase.__init__(self, fig, sim)

        self.xs = []
        self.gap_ys = [] # This will be a list of lists (one for each brake)
        
        self.lines = []
        
        #self.ani = animation.FuncAnimation(self.fig, self.update, interval=10, blit=False, init_func=self.init)

    def init(self):
        print "TkGraphBrakes init!"
        self.xs.append(0)
        brakes = self.sim.pod.brakes
        self.gap_ys.append( [brakes[0].gap] )
        self.gap_ys.append( [-brakes[1].gap] )  # Negative so that it shows on the bottom of the graph
        
        b0line, = self.ax.plot(self.xs, self.gap_ys[0], color="#DDDD33")
        self.lines.append( b0line )

        b1line, = self.ax.plot(self.xs, self.gap_ys[1], color="#DDDD33")
        self.lines.append( b1line )
            
        self.ax.set_xlim(-50, 1270)  # Position
        self.ax.set_ylim(-0.035, 0.035)
        #self.ax.invert_yaxis()
        
        #fontP = FontProperties()
        #fontP.set_size('small')

        #self.ax.legend(loc='bottom center', ncol=len(self.dlines), prop=fontP)
        
    def update(self, i):
        self.xs.append(self.sim.pod.position)

        brakes = self.sim.pod.brakes

        # Brake 0
        self.gap_ys[0].append(brakes[0].gap)
        self.lines[0].set_xdata(self.xs)
        self.lines[0].set_ydata(self.gap_ys[0])

        # Brake 1 -- use negative brake gap to show it on the bottom of the graph
        self.gap_ys[1].append(-brakes[1].gap)
        self.lines[1].set_xdata(self.xs)
        self.lines[1].set_ydata(self.gap_ys[1])
         
        #self.ax.relim()
        #self.ax.autoscale()
        
        return self.lines


class TkGraphHeight(TkGraphBase):
    def __init__(self, fig, sim):
        TkGraphBase.__init__(self, fig, sim)

        self.xs = []
        self.height_ys = [] # This will be a list of lists (one for the actual height and one for each sensor)
        
        self.lines = []
        
        self.ani = animation.FuncAnimation(self.fig, self.update, interval=10, blit=False, init_func=self.init)

    def init(self):
        print "TkGraphHeight init!"

        self.xs.append(0)
        height = self.sim.pod.he_height
        self.height_ys.append( [height] )
        
        h0line, = self.ax.plot(self.xs, self.height_ys[0], label="Actual Height", color="g")
        self.lines.append( h0line )
            
        self.ax.set_xlim(-50, 1270)  # Position
        self.ax.set_ylim(0.0, 0.016)
        #self.ax.invert_yaxis()
        
        #fontP = FontProperties()
        #fontP.set_size('small')

        #self.ax.legend(loc='bottom center', ncol=len(self.dlines), prop=fontP)
        
    def update(self, i):
        self.xs.append(self.sim.pod.position)

        height = self.sim.pod.he_height

        # Actual height
        line = self.lines[0]
        self.height_ys[0].append(height)
        line.set_xdata(self.xs)
        line.set_ydata(self.height_ys[0])
         
        #self.ax.relim()
        #self.ax.autoscale()
        
        return self.lines


class TkGraphAccel(TkGraphBase):
    def __init__(self, fig, sim):
        TkGraphBase.__init__(self, fig, sim)

        self.xs = []
        self.ys = [] # This will be a list of lists (one for the actual height and one for each sensor)
        
        self.lines = []
        
        self.ani = animation.FuncAnimation(self.fig, self.update, interval=10, blit=False, init_func=self.init)

    def init(self):
        print "TkGraphAccel init!"

        self.xs.append(0)
        acceleration = self.sim.pod.acceleration
        self.ys.append( [acceleration] )
        
        h0line, = self.ax.plot(self.xs, self.ys[0], label="Actual Accel", color="g")
        self.lines.append( h0line )
            
        self.ax.set_xlim(-50, 1270)  # Position
        self.ax.set_ylim(-50, 30)
        #self.ax.invert_yaxis()
        
        #fontP = FontProperties()
        #fontP.set_size('small')

        #self.ax.legend(loc='bottom center', ncol=len(self.dlines), prop=fontP)
        
    def update(self, i):
        self.xs.append(self.sim.pod.position)

        acceleration = self.sim.pod.acceleration

        # Actual height
        line = self.lines[0]
        self.ys[0].append(acceleration)
        line.set_xdata(self.xs)
        line.set_ydata(self.ys[0])
         
        #self.ax.relim()
        #self.ax.autoscale()
        
        return self.lines


class TkGraphVelocity(TkGraphBase):
    # @todo: Move the code from the base to here
    def __init__(self, fig, sim):
        TkGraphBase.__init__(self, fig, sim)
    

        

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

    # Create the timer test
    from timers import TimerTest
    tt = TimerTest(100000)
    timer_thread = threading.Thread(target=tt.run, args=())
    timer_thread.daemon = True

    # Create the sim runner
    sim = Sim( Sim.load_config_files(args.configfile) )
    sim.set_working_dir('data/test')

    # Run the threads
    # simrunner.run_threaded()  # This will be handled by the 'Start' button of the simulator
    timer_thread.start()

    #gui = TkAnimGui(sim)
    # Run the gui
    gui = GuiLayout(simrunner)
    gui.run()


    """
    gui_thread = threading.Thread(target=root.mainloop, args=())
    gui_thread.start()
    
    gui_thread.join()
    """