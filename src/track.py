#!/usr/bin/env python

import logging
import numpy as np
from distutils.util import strtobool  # For reading configuration

from units import Units

class Track:

    def __init__(self, sim, config):
        
        self.sim = sim
        self.config = config
        
        # Physical
        # NOTE: @see diagram in http://confluence.rloop.org/display/SD/2.+Determine+Pod+Kinematics
        #       For the track/tube reference frame, x=0 at the start of the track, and x = length at the end.
        #       For the pod, x=0 is ahead and below the pod, with x+ being toward the read of the pod.
        self.length = Units.SI(config.length)     # meters -- Length from pod start position to end of track
        
        # Reference for the reflective stripes
        self.reflective_strip_width = Units.SI(config.reflective_strip_width)      # meters (4 inches)
        self.reflective_pattern_interval = Units.SI(config.reflective_pattern_interval)  # meters (100 feet)
        self.reflective_pattern_spacing = Units.SI(config.reflective_pattern_spacing)  # meters -- distance between stripes in a pattern

        self.track_gap_width = Units.SI(config.track_gap_width) # Width of the gap in the subtrack in meters (probably worst scenario, more realistic 1-2 mm)
        self.track_gap_interval = Units.SI(config.track_gap_interval)  # Interval between the gaps in the subtrack in meters (Length of the aluminium plate)

        # Initialize 
        self.reflective_strips = None  # Will be a numpy array after initialization
        self._init_reflective_strips(config.enable_strip_patterns)
        self.reflective_strip_ends = self.reflective_strips + self.reflective_strip_width   # Pre-calc the ends for use in LaserContrastSensor

        self.track_gaps = []
        self._init_track_gaps()

    def _init_track_gaps(self):

        cursor = self.length

        while cursor > self.track_gap_interval:  # Note: we'll put one in negative territory if we use 0 here
            cursor -= self.track_gap_interval
            self.track_gaps.append(cursor)

        self.track_gaps = sorted(self.track_gaps)

    def _init_reflective_strips(self, enable_patterns):
        # Add in the 100' strips (backwards)

        # Calculate the distance between strip edges in a pattern
        pattern_offset = self.reflective_strip_width + self.reflective_pattern_spacing

        cursor = self.length
        counter = 1  # 1 to account for the end of the track
        
        reflective_strips = []
        while cursor > self.reflective_pattern_interval:  # Note: we'll put one in negative territory if we use 0 here
            cursor -= self.reflective_pattern_interval
            counter += 1
            reflective_strips.append(cursor)

            # If we have the 500' and 1000' patterns (SpaceX may or may not have these for the competition -- we may be able to choose)
            if enable_patterns:
                # Handle 500' pattern (5 strips)
                if counter == 5:
                    # Add the other 4 strips (we already added the 100' strip)
                    pattern = [cursor + (x+1) * pattern_offset for x in xrange(4)]
                    reflective_strips.extend(pattern)
            
                # Handle 1000' pattern (10 strips)
                if counter == 10:
                    # Add the other 9 strips (we already added the 100' strip)
                    pattern = [cursor + (x+1) * pattern_offset for x in xrange(9)]
                    reflective_strips.extend(pattern)
            
        # Sort and reverse for easy handling during the run
        self.reflective_strips = np.array(sorted(reflective_strips))

    def reflective_strips_distance_remaining_mm(self):
        # @todo: rename this or move it to a utils class/script
        strips_trf = [int((self.length - x) * 1000) for x in self.reflective_strips]
        strips_trf.append(0)  # Add the last strip (the track end position) -- distance remaining = 0. @todo: is there a strip there? 
        return strips_trf

    def to_c_array(self, strips, strips_size_varname="TUBE_STRIP_COUNT", strips_array_varname="TubeStripDistanceRemaining"):
        # @todo: rename this or move it to a utils class/script
        s = []
        s.append("{} = {};".format(strips_size_varname, len(strips)))
        s.append("")
        s.append("int {}[TUBE_STRIP_COUNT] = ".format(strips_array_varname))
        s.append("{")
        strip_locs = ["\t{}".format(strip) for strip in strips]
        s.append(",\n".join(strip_locs))
        s.append("};")
        
        return "\n".join(s)


    # -------------------------
    # Simulation
    # -------------------------
        
    def step(self, dt_usec):
        if self.state == "HOLD":
            pass  # Not much to do
        elif self.state == "PUMPDOWN":
            # Reduce the pressure in the track over self.pumpdown_time_sec seconds

            pass # @todo: do the pumpdown calculations, or remove the pumpdown phase

            state = "HOLD"
            
        elif self.state == "PRESSURIZE":
            # Return the track to atmospheric pressure over self.pressurize_time_sec seconds (or remove this)

            pass

            self.state = "HOLD"
        
    
    # -------------------------
    # Control hooks
    # -------------------------

    def start_pumpdown(self):
        self.state = "PUMPDOWN"
        
    def start_pressurize(self):
        self.state = "PRESSURIZE"
        
    def hold_pressure(self):
        self.state = "HOLD"


if __name__ == "__main__":
    # Testing

    import argparse
    parser = argparse.ArgumentParser(description="Reflective strip locations, distance remaining until end of track, mm")
    parser.add_argument('length', metavar='N', type=int, nargs='?', default=1500, 
        help='length of the track in meters (from pod start to end of track)')
    args = parser.parse_args()

    track = Track(args.length)
    for strip_location in track.reflective_strips_distance_remaining_mm():
        print strip_location
    
    print track.to_c_array(track.reflective_strips_distance_remaining_mm())
