#!/usr/bin/env python

from units import Units

class LaserOptoSensor: 
    
    def __init__(self, sim, config):
        self.sim = sim
        self.config = config
            
        self.sample_overflow = 0.  # Our timestep won't always yield a clean number (e.g. 'we should take 8.6 samples for this dt_usec'. Store the remainder here.)
        
        # Configuration
        self.sampling_rate_hz = Units.SI("250 hz")
        self.pod_ref_sensor_height = Units.SI("-10mm")
        self.sensor_builtin_offset = Units.SI("25mm")

        self.gap_ptr = 0

    def measure(self, dt_usec):
        # Figure out the number of samples that we need
        n_samples = self.sample_overflow + self.sampling_rate_hz * dt_usec / 1000000.0
        self.sample_overflow = n_samples - int(n_samples)  # Save off the remainder
        n_samples = int(n_samples)  # Discard the remainder

        noise_amplitude = 0.1  # @todo: get this from somewhere (config? calculate? use stdev from the real data? )

        # Lerp between the last and current position values, with noise
        samples = np.random.normal(np.linspace(self.sim.pod.last_height, self.sim.pod.height, n_samples), noise_amplitude)
                
        # Determine if we crossed one or more gaps during this step
        # (we'll lerp to get the positions there)