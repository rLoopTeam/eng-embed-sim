#!/usr/bin/env python

import numpy as np

P = np.array([[  1.51367225e-07],
      [ -5.01144003e-05],
      [  5.59122062e-03],
      [ -2.48111525e-01],
      [  3.97197808e+00],
      [  2.18749402e+00]])
            
# @see http://stackoverflow.com/questions/4455076/numpy-access-an-array-by-column
coefficients = P[:,0]  # Get the 0th column

print coefficients

r = 150
d_len = 200
x = np.linspace(0, r, d_len)

print x

for idx, coefficient in enumerate(coefficients):
    power = len(coefficients) - idx - 1  # length of coefficients (in this case, 6) - the list index (0 to 5) - 1
    y += coefficient * x**power 

