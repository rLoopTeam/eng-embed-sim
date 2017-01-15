#!/usr/bin/env python

import Tkinter as tk
import ttk

import numpy as np

# Note: imports need to be in the right order or it will cra
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import matplotlib.pyplot as plt
import matplotlib.animation as animation


root = tk.Tk()

content = ttk.Frame(root)
frame = ttk.Frame(content, borderwidth=1, relief="sunken", width=300, height=200)
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
cancel = ttk.Button(content, text="Cancel")


n = ttk.Notebook(frame)
f1 = ttk.Frame(n)   # first page, which would get widgets gridded into it
f2 = ttk.Frame(n)   # second page
n.add(f1, text='One', padding=10)
n.add(f2, text='Two')


content.grid(column=0, row=0)
frame.grid(column=0, row=0, columnspan=3, rowspan=2)
n.grid(column=0, row=0)
namelbl.grid(column=3, row=0, columnspan=2)
name.grid(column=3, row=1, columnspan=2)
one.grid(column=0, row=3)
two.grid(column=1, row=3)
three.grid(column=2, row=3)
ok.grid(column=3, row=3)
cancel.grid(column=4, row=3)



root.mainloop()