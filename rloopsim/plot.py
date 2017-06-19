import logging

import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
# Import FigureCanvas
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.backends.backend_pdf import PdfPages, FigureCanvas
from matplotlib.figure import Figure
from collections import OrderedDict

import env

class PlotPostProcessor:
    
    def __init__(self, sim, config, working_dir):
        self.sim = sim
        self.config = config
        self.logger = logging.getLogger("PlotPostProcessor")

        self.logger.info("Initializing PlotPostProcessor")

        # @todo: change this to use env? 
        self.working_dir = working_dir
        
    def process(self, sim):
        #working_dir = sim.env.cwd()  # @todo: make an environment for the simulator
        #filename = sim.sensors.pod.    # @todo: get this from env? config? both? 
        #with env.Env("data"):
        self.create_plots()
        
    def create_plots(self):
        self.create_main_plot()
        
    def create_main_plot(self):
        """ Create the main plot (position, velocity, accel, etc.) """
        n_axes = 5
        axis_counter = 1  # So we can easily rearrange the ordering

        axes = OrderedDict()

        data = np.genfromtxt(os.path.join(self.working_dir, 'pod.csv'), delimiter=',', dtype=None, names=True)
        print data.dtype.names
        """
        t_usec
        pod_position
        pod_velocity
        pod_acceleration
        he_height
        F_aero_x
        F_aero_y
        F_aero_z
        F_brakes_x
        F_brakes_y
        F_brakes_z
        F_gimbals_x
        F_gimbals_y
        F_gimbals_z
        F_hover_engines_x
        F_hover_engines_y
        F_hover_engines_z
        F_lateral_stability_x
        F_lateral_stability_y
        F_lateral_stability_z
        F_landing_gear_x
        F_landing_gear_y
        F_landing_gear_z
        """

        t = data['t_usec'] / 1000000.0
        p = data['pod_position']
        #print t
        v = data['pod_velocity']
        a = data['pod_acceleration']
        h = data['he_height']
    

        fig = Figure(figsize=(16,12), dpi=100)
        canvas = FigureCanvas(fig)
        
        axes['v'] = fig.add_subplot(n_axes, 1, axis_counter)
        ax = axes['v']
        l1 = (p, v, 'b-')
        #ax.set_ylabel('Position (m)')
        ax.set_ylabel('Velocity (m/s)')
        ax.plot(*l1)

        axis_counter += 1
        axes['a'] = fig.add_subplot(n_axes, 1, axis_counter)
        ax = axes['a']
        ax.set_ylabel('Accel (m/s^2)')
        l2 = (p, a, 'g-')
        ax.plot(*l2)

        lines = []
        lines.append([p, data['F_brakes_x']])
        lines.append([p, data['F_aero_x']])
        lines.append([p, data['F_brakes_x']])
        lines.append([p, data['F_gimbals_x']])
        lines.append([p, data['F_hover_engines_x'], 'b'])
        lines.append([p, data['F_lateral_stability_x']])
        lines.append([p, data['F_landing_gear_x']])
        axis_counter += 1
        axes['f'] = fig.add_subplot(n_axes, 1, axis_counter)
        ax = axes['f']
        ax.set_ylabel('Forces (N)')
        
        for i, line in enumerate(lines):
            ax.plot(*line)

        axis_counter += 1
        axes['h'] = fig.add_subplot(n_axes, 1, axis_counter)
        ax = axes['h']
        ax.set_ylabel('Height (mm)')
        l2 = (p, h*1000, 'b-')
        ax.plot(*l2)

        """
        axis_counter += 1
        axes['f'] = fig.add_subplot(n_axes, 1, axis_counter)
        ax = axes['f']
        ax.set_ylabel('Brake Gaps (mm)')
        ax.set_xlabel('Position (m)')
        l2 = (t, v, 'r-')
        ax.plot(*l2)
        """
        
        fig.tight_layout()

        # fig.savefig('foo.png', bbox_inches='tight')  # Tight spacing
        fig.savefig(os.path.join(self.working_dir, 'run.png'))  # Tight spacing
        
        # ----
        # Parasitic drag (drag x position)
        fig = Figure(figsize=(16,6), dpi=100)
        fig.suptitle("Parasitic Brake Drag (Force / Position)", fontsize=20)
        canvas = FigureCanvas(fig)
        
        ax = fig.add_subplot(1, 1, 1)
        #l1 = (p, data['F_hover_engines_x'], 'b-')
        l2 = (p, 2*data['F_brakes_x'], 'b-')  # 2* data to include both brakes
        #ax.set_xlabel('Velocity (m/s)')
        ax.set_xlabel('Position along track (m)')
        ax.set_ylabel('Drag (N)')
        #ax.plot(*l1)
        ax.plot(*l2, label="Brake drag (both brakes)")
        ax.legend()

        #fig.tight_layout()

        fig.savefig(os.path.join(self.working_dir, 'parasitic_drag_position.png')) 

        # Parasitic drag (drag x velocity)
        fig = Figure(figsize=(16,6), dpi=100)
        fig.suptitle("Parasitic Brake Drag (Force / Velocity)", fontsize=20)
        canvas = FigureCanvas(fig)

        ax = fig.add_subplot(1, 1, 1)
        #l1 = (p, data['F_hover_engines_x'], 'b-')
        l2 = (v, 2*data['F_brakes_x'], 'b-')  # 2* data to include both brakes
        ax.set_xlabel('Velocity (m/s)')
        #ax.set_xlabel('Position along track (m)')
        ax.set_ylabel('Drag (N)')
        #ax.plot(*l1)
        ax.plot(*l2, label="Brake drag (both brakes)")
        ax.legend()

        #fig.tight_layout()

        # fig.savefig('foo.png', bbox_inches='tight')  # Tight spacing
        fig.savefig(os.path.join(self.working_dir, 'parasitic_drag_velocity.png')) 

        
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    p = PlotPostProcessor(None, None, './data/test')
    p.create_plots()
    