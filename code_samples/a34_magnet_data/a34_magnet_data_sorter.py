#!/usr/bin/env python

"""
http://stackoverflow.com/questions/16312607/how-to-group-rows-in-a-numpy-2d-matrix-based-on-column-values
http://stackoverflow.com/questions/773/how-do-i-use-pythons-itertools-groupby

Useful Reference:
https://docs.scipy.org/doc/numpy/reference/generated/numpy.loadtxt.html
https://docs.scipy.org/doc/numpy/reference/arrays.dtypes.html
https://docs.scipy.org/doc/numpy/reference/generated/numpy.ndarray.sort.html#numpy.ndarray.sort
"""

import numpy as np
from itertools import groupby
from operator import itemgetter

a = np.loadtxt("a34data.csv", 
        dtype={'names': ('drag', 'lift', 'h', 'v'),
               'formats': ('f16', 'f16', 'f16', 'f16')}, 
        usecols=(1,2,4,5), 
        delimiter=",",
        skiprows=1)
        
# Example: 
# print a[0]['h']

# Note: we MUST sort before using groupby or it won't work
a.sort(order="h")

dict_heights = {}
for k, g in groupby(a, key = itemgetter('h')):
    dict_heights[ round(k, 4) ] = list(g)

import pprint
pprint.pprint(dict_heights)

# Write to files
fmt = '%.6g'  # Print up to 6 decimal places -- see https://docs.scipy.org/doc/numpy/reference/generated/numpy.savetxt.html
for k, rows in dict_heights.iteritems():
    filename = 'test_{}.csv'.format(k)
    np.savetxt(filename, rows, delimiter=',', fmt=(fmt, fmt, fmt, fmt)) 