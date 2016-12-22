#!/usr/bin/env python

class Tube:

    def __init__(self, length):
        
        # Physical
        self.length = length   # Length from start to end
        self.pod_start_position = -self.length   # Pod reference frame is reverse of tube in x direction

        # Reference
        self.reflective_strip_width = 0.1016      # meters (4 inches)
        self.reflective_pattern_interval = 30.48  # meters (100 feet)
        self.reflective_pattern_spacing = 0.1016  # meters -- distance between stripes in a pattern

        # Initialize 
        self.reflective_strips = []
        self._init_reflective_strips()
        
        
    def _init_reflective_strips(self):
        # Add in the 100' strips (backwards)

        # Calculate the distance between strip edges in a pattern
        pattern_offset = self.reflective_strip_width + self.reflective_pattern_spacing

        cursor = self.length
        counter = 0
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


if __name__ == "__main__":
    # Testing

    import argparse
    parser = argparse.ArgumentParser(description="Example of processing laser sensor data function")
    parser.add_argument('length', metavar='N', type=int, nargs='?', default=1500, 
        help='length of the tube in meters (from pod start to end of track)')
    args = parser.parse_args()    

    tube = Tube(args.length)
    for strip_location in tube.reflective_strips:
        print strip_location
    
