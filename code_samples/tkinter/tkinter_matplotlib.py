# @see https://groups.google.com/forum/#!topic/networkx-discuss/lTVyrmFoURQ

#!/usr/bin/env python
import matplotlib
matplotlib.use('TkAgg')

from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

import Tkinter as Tk
import sys

def destroy(e): sys.exit()

root = Tk.Tk()
root.wm_title("Embedding in TK")
#root.bind("<Destroy>", destroy)


f = Figure(figsize=(5,4), dpi=100)
a = f.add_subplot(1, 5, 1)

######################
# the networkx part
import networkx as nx
G=nx.path_graph(8)
pos=nx.spring_layout(G)
nx.draw(G,pos,ax=a)
######################

# a tk.DrawingArea
canvas = FigureCanvasTkAgg(f, master=root)
canvas.show()
canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

toolbar = NavigationToolbar2TkAgg( canvas, root )
toolbar.update()
canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

#button = Tk.Button(master=root, text='Quit', command=sys.exit)
#button.pack(side=Tk.BOTTOM)

Tk.mainloop()