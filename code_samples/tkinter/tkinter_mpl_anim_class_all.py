# @see http://stackoverflow.com/questions/21197728/embedding-a-matplotlib-animation-into-a-tkinter-frame
# @see http://stackoverflow.com/questions/32019556/matplotlib-crashing-tkinter-application for fix to ^
 
#---------Imports
from numpy import arange, sin, pi


import Tkinter as Tk
import numpy as np

# Note: imports need to be in the right order or it will cra
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import matplotlib.pyplot as plt
import matplotlib.animation as animation

from matplotlib import style
style.use('fivethirtyeight')

#---------End of imports

class MplAnimTest:
    def __init__(self, fig):
        self.fig = fig
        self.ax = self.fig.add_subplot(2, 1, 1)
        self.bx = self.fig.add_subplot(2, 1, 2)

        self.x = np.arange(0, 2*np.pi, 0.01)        # x-array

        print "AnimTest __init__"
        
        #self.ani = animation.FuncAnimation(self.fig, self.animate, np.arange(1, 100), interval=25, blit=False, init_func=self.init)
        self.ani = animation.FuncAnimation(self.fig, self.animate, interval=25, blit=False, init_func=self.init)

    def init(self):
        print "Init!"
        linea, = self.ax.plot(self.x, np.sin(self.x))  # Initial line (before scrolling)
        #lineb, = self.bx.plot(self.x, np.cos(self.x))
        #self.line = [linea, lineb]
        self.line = [linea]

    def animate(self, i):
        print "Animate!"
        self.line[0].set_ydata(np.sin(self.x+i/10.0))  # update the data
        #self.line[1].set_ydata(np.cos(self.x+i/10.0))  # update the data
        return self.line


"""
fig = plt.Figure()

x = np.arange(0, 2*np.pi, 0.01)        # x-array

def animate(i):
    line.set_ydata(np.sin(x+i/10.0))  # update the data
    return line,

root = Tk.Tk()

label = Tk.Label(root,text="SHM Simulation").grid(column=0, row=0)

canvas = FigureCanvasTkAgg(fig, master=root)

ax = fig.add_subplot(111)
line, = ax.plot(x, np.sin(x))
ani = animation.FuncAnimation(fig, animate, np.arange(1, 200), interval=25, blit=False)

"""

class MplAnimGui:
    def __init__(self):
        self.fig = plt.Figure()
        self.root = Tk.Tk()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)

        mat = MplAnimTest(self.fig)

        self.canvas.get_tk_widget().grid(column=0,row=1)
    
    def run(self):
        self.root.mainloop()


# NOTE: Ordering is important here! Passing fig to FigureCanvasTkAgg fills it out somehow -- 'new_timer' becomes available on the figure...
"""
fig = plt.Figure()
root = Tk.Tk()

canvas = FigureCanvasTkAgg(fig, master=root)

mat = MplAnimTest(fig)


canvas.get_tk_widget().grid(column=0,row=1)

Tk.mainloop()
"""

MplAnimGui().run()