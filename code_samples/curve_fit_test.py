#!/usr/bin/env python

import numpy as np
from scipy.optimize import curve_fit

 
def func(x, a, b, c, d):
    return a * x + b * x * np.exp(-c * x) + d
    
xdata = [4, 10, 16, 30, 50, 100, 150]
ydata = [8673, 11869, 11652, 10058, 8873, 6797, 5955]

popt, pcov = curve_fit(func, xdata, ydata, maxfev=5000)

import pprint
pprint.pprint(["{:f}".format(x) for x in popt])
#print pcov


def enegx(x, a, b, c):
    return a - np.exp(-(b+c))
    
xdata = [0, 10, 30]
ydata = [0.0, 0.8, 0.9]
popt, pcov = curve_fit(func, xdata, ydata)
print popt