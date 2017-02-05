#!/usr/bin/env python

import os
import csv

def csv_gen(output_filename):

    with open(output_filename, 'wb') as f:   # Note: need to use wb since windows
        w = csv.writer(f, lineterminator=os.linesep)  # Also lineterminator=os.linesep for cross platform compatibility

        headers_written = False
        enabled = True

        while True:
            sensor, step_samples = (yield)   # Wait for step_callback to send us the a sample

            #print "step_callback_gen: got {} with {} samples".format(sensor, len(step_samples))

            if not headers_written: 
                w.writerow(sensor.get_csv_headers())
                headers_written = True
            
            if enabled:
                for sample in step_samples:
                    w.writerow(list(sample))  # Note: each sample is assumed to be a namedtuple of some sort

class Sensor:
    def __init__(self):
        pass
        
    def get_csv_headers(self):
        return ['a', 'b', 'c']

if __name__ == "__main__":

    sensor = Sensor()

    g = csv_gen("test.csv")
    next(g)  # Should create the file
    for i in xrange(100):
        g.send( (sensor, [[i, i+1, i*2]]) )