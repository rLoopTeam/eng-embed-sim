#!/usr/bin/env python

from units import Units

class Tube:

    def __init__(self, sim, config):
        
        self.sim = sim
        self.config = config
        
        # Physical
        # NOTE: @see diagram in http://confluence.rloop.org/display/SD/2.+Determine+Pod+Kinematics
        #       For the tube reference frame, x=0 at the start of the track, and x = length at the end.
        #       For the pod, x=0 is ahead and below the pod, with x+ being toward the read of the pod.
        self.length = Units.SI(config.length)     # meters -- Length from pod start position to end of track
        self.pressure = Units.SI(config.ambient_pressure)   # Pascals (1atm = 101325Pa)

        self.state = "HOLD"  # {HOLD, PUMPDOWN, PRESSURIZE}
        self.pumpdown_time_sec = 2400   # 2400 = 40 minutes
        self.pressurize_time_sec = 600  # 600 = 10 minutes
        self.pumpdown_target_pressure = 12665.63  # Pa -- .125Atm = 12665.63 Pa
        
        # Reference for the reflective stripes
        self.reflective_strip_width = 0.1016      # meters (4 inches)
        self.reflective_pattern_interval = 30.48  # meters (100 feet)
        self.reflective_pattern_spacing = 0.1016  # meters -- distance between stripes in a pattern

        self.track_gap_width = 0.005 # Width of the gap in the subtrack in meters (probably worst scenario, more realistic 1-2 mm)
        self.track_gap_interval = 2  # Interval between the gaps in the subtrack in meters (Length of the aluminium plate)

        self.atmospheric_pressure = 101325.0

        # Initialize 
        self.reflective_strips = []
        self._init_reflective_strips()
        # self._init_strips_distance_remaining()  # @todo: finish this? or put it in the pod? 
        
        self.track_gaps = []
        self._init_track_gaps()

    def _init_track_gaps(self):

        cursor = self.length # not sure if "cursor" can be used again

        while cursor > self.track_gap_interval:  # Note: we'll put one in negative territory if we use 0 here
        cursor -= self.track_gap_interval
        self.track_gaps.append(cursor)

        self.track_gaps = sorted(self.track_gaps)

    def _init_reflective_strips(self):
        # Add in the 100' strips (backwards)

        # Calculate the distance between strip edges in a pattern
        pattern_offset = self.reflective_strip_width + self.reflective_pattern_spacing

        cursor = self.length
        counter = 1  # 1 to account for the end of the tube

        while cursor > self.reflective_pattern_interval:  # Note: we'll put one in negative territory if we use 0 here
            cursor -= self.reflective_pattern_interval
            counter += 1
            self.reflective_strips.append(cursor)

            # Handle 500' pattern (5 strips)
            if counter == 5:
                # Add the other 4 strips (we already added the 100' strip)
                pattern = [cursor + (x+1) * pattern_offset for x in xrange(4)]
                self.reflective_strips.extend(pattern)
            
            # Handle 1000' pattern (10 strips)
            if counter == 10:
                # Add the other 9 strips (we already added the 100' strip)
                pattern = [cursor + (x+1) * pattern_offset for x in xrange(9)]
                self.reflective_strips.extend(pattern)
            
        # Sort and reverse for easy handling during the run
        self.reflective_strips = sorted(self.reflective_strips)

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
            # Reduce the pressure in the tube over self.pumpdown_time_sec seconds

            pass # @todo: do the pumpdown calculations

            state = "HOLD"
            
        elif self.state == "PRESSURIZE":
            # Return the tube to atmospheric pressure over self.pressurize_time_sec seconds

            pass

            self.state = "HOLD"

    def apply_force_to(self, pod):
        """ Apply aero drag force to the pod """

        # @todo: Need to calculate this -- apply force based on pressure in the tube and speed (any other quantities we need? )
        aero_drag = 0.0   
        speed = pod.velocity
        pressure = self.pressure
        
        # @todo: do force calculations here. We can set other things (like area, etc.) in the config.

        pod.apply_force(aero_drag)
        
    
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
        help='length of the tube in meters (from pod start to end of track)')
    args = parser.parse_args()

    tube = Tube(args.length)
    for strip_location in tube.reflective_strips_distance_remaining_mm():
        print strip_location
    
    print tube.to_c_array(tube.reflective_strips_distance_remaining_mm())
