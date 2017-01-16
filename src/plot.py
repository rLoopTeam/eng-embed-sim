import numpy as np
import matplotlib.pyplot as plt


class PlotPostProcessor:
    
    def __init__(self):
        pass
        
    def process(self, sim):
        working_dir = sim.config.working_dir
        filename = sim.sensors.pod.