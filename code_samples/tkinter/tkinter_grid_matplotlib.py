# @see http://www.tkdocs.com/tutorial/grid.html

#from Tkinter import *
import ttk
import Tkinter as tk

root = tk.Tk()

content = ttk.Frame(root)
frame = ttk.Frame(content, borderwidth=5, relief="sunken", width=600, height=300)
namelbl = ttk.Label(content, text="Name")
name = ttk.Entry(content)

onevar = tk.BooleanVar()
twovar = tk.BooleanVar()
threevar = tk.BooleanVar()
onevar.set(True)
twovar.set(False)
threevar.set(True)

one = ttk.Checkbutton(content, text="One", variable=onevar, onvalue=True)
two = ttk.Checkbutton(content, text="Two", variable=twovar, onvalue=True)
three = ttk.Checkbutton(content, text="Three", variable=threevar, onvalue=True)
ok = ttk.Button(content, text="Okay")
cancel = ttk.Button(content, text="Cancel", command=root.quit)


content.grid(column=0, row=0)
frame.grid(column=0, row=0, columnspan=3, rowspan=2)
namelbl.grid(column=3, row=0, columnspan=2)
name.grid(column=3, row=1, columnspan=2)
one.grid(column=0, row=3)
two.grid(column=1, row=3)
three.grid(column=2, row=3)
ok.grid(column=3, row=3)
cancel.grid(column=4, row=3)
#root.mainloop()


# ----------
import matplotlib
matplotlib.use('TkAgg')

from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

#import Tkinter as Tk
import sys


f = Figure(figsize=(4,2), dpi=100)
a = f.add_subplot(1, 1, 1)

######################
# the networkx part
import networkx as nx
G=nx.path_graph(8)
pos=nx.spring_layout(G)
nx.draw(G,pos,ax=a)
######################

# a tk.DrawingArea
canvas = FigureCanvasTkAgg(f, master=frame)
canvas.show()
#canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
canvas.get_tk_widget().grid()

#toolbar = NavigationToolbar2TkAgg( canvas, root )
#toolbar.update()
#canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

# -----------


print "Got to the main loop..."
tk.mainloop()