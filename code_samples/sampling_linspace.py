#!/usr/bin/env python

import numpy as np

stripe_locations = np.arange(0, 1000., 90)
print "Stripe locations: {}".format(stripe_locations)

stripe_location_ends = stripe_locations + .05
print "Stripe locations ends: {}".format(stripe_location_ends)

print zip(stripe_locations, stripe_location_ends)

print np.stack((stripe_locations, stripe_location_ends), axis=1).flatten()


print "----------"


dt = 0.5  # seconds
sampling_rate = 9  #hz

overflow = 0.0
total_samples = 0

for i in xrange(10):
    n_samples = overflow + sampling_rate * dt
    overflow = n_samples - int(n_samples)
    n_samples = int(n_samples)
    
    total_samples += n_samples
    
    print "t: {}, n_samples: {}, overflow: {}, total samples: {}".format(dt*(i+1), n_samples, overflow, total_samples)
    
print "----------"

samples_per_second = 2500
dt_sec = .00123

samples_per_step = samples_per_second * dt_sec
print samples_per_step
sample_pct_of_step = 1/samples_per_step

value_start = 10.2
value_end = 13.9

next_start = 0.0
for i in xrange(1000):
    if next_start >= 1.0:
        # If our next start falls in another step, subtract a step and skip this one
        next_start -= 1.
        #return None  # @todo: return an empty array?
    else:
        a = np.arange(next_start, 1, sample_pct_of_step)
        next_start = sample_pct_of_step - (1- a[-1])
        print "{}: {}".format((i+1)*dt_sec, len(a))
    
        # Do a quick lerp between the start and end values for this step. Remember 'a' is a vector
        print value_start + a * (value_end - value_start)
    
    
    """
    print overflow
    n_samples = overflow + sampling_rate * dt
    overflow = n_samples - int(n_samples)
    n_samples = int(n_samples)
    """

"""
>>> import numpy as np
>>> np.linspace(0, 1, 3, endpoint=False)
array([ 0.        ,  0.33333333,  0.66666667])
>>> np.linspace(0, 1, 3, endpoint=True)
array([ 0. ,  0.5,  1. ])
>>> np.arange(0, 1, .21)
array([ 0.  ,  0.21,  0.42,  0.63,  0.84])
>>> np.arange(0, 1, .2)
array([ 0. ,  0.2,  0.4,  0.6,  0.8])
>>> np.arange(0, 1, .22)
array([ 0.  ,  0.22,  0.44,  0.66,  0.88])
>>> np.arange(0, 1, .23)
array([ 0.  ,  0.23,  0.46,  0.69,  0.92])
>>> np.arange(0, 1, .24)
array([ 0.  ,  0.24,  0.48,  0.72,  0.96])
>>> np.arange(0, 1, .25)
array([ 0.  ,  0.25,  0.5 ,  0.75])
>>> np.arange(0, 1, .249)
array([ 0.   ,  0.249,  0.498,  0.747,  0.996])
>>> a = np.arange(0, 1, .249)
>>> a[-1]
0.996
>>> .249 - a[-1]
-0.747
>>> .249 - (1-a[-1])
0.245
>>> arange(.245, 1, .249)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
NameError: name 'arange' is not defined
>>> np.arange(.245, 1, .249)
array([ 0.245,  0.494,  0.743,  0.992])
>>> np.arange(0, 1, 2)
array([0])
>>> np.arange(.243, 1, 2)
array([ 0.243])
>>> np.arange(0, 1, 2)
array([0])
>>> np.array([])
array([], dtype=float64)
>>> a
array([ 0.   ,  0.249,  0.498,  0.747,  0.996])
>>> start = 4
>>> end = 8
>>> start + a *(end - start)
array([ 4.   ,  4.996,  5.992,  6.988,  7.984])

"""