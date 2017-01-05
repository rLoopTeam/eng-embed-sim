
from pod import Pod
from tube import Tube
from pusher import Pusher
#from fcu import fcu

import time
import logging
from units import *

class Sim:
    
    def __init__(self, config):
        self.logger = logging.getLogger("Sim")

        self.logger.info("Initializing simulation")
        
        self.config = config

        self.fixed_timestep_usec = Units.usec(config.fixed_timestep)  # Convert to usec

        self.pusher = Pusher(self, self.config.pusher)
        self.tube = Tube(self, self.config.tube)
        self.pod = Pod(self, self.config.pod)      
        #self.fcu = Fcu(self, self.config.fcu)  

        # Initial setup
        self.pusher.start_push()

        # Volatile
        self.elapsed_time_usec = 0
        self.n_steps_taken = 0
        
        # Testing only
        from sensors import LaserOptoSensor, SensorConsoleWriter, LaserOptoTestListener  # @todo: move this to the top once we're done testing
        self.laser_opto_1 = LaserOptoSensor(self, self.config.sensors.laser_opto_1)
        #self.laser_opto_1.register_step_listener(SensorConsoleWriter())  # Write data directly to the console
        self.lotl = LaserOptoTestListener()
        self.laser_opto_1.register_step_listener(self.lotl) 
        
    def step(self, dt_usec):        
        # Step the pusher first (will apply pressure and handle disconnection)
        self.pusher.step(dt_usec)

        # Step the pod (will handle all other forces and pod physics)
        self.pod.step(dt_usec)
        
        #self.fcu.step(dt_usec)
        self.laser_opto_1.step(dt_usec)
        #self.logger.debug(list(self.laser_opto_1.pop_all()))
        
        self.elapsed_time_usec += dt_usec
        self.n_steps_taken += 1

    def run(self):
        self.logger.info("Starting simulation")
        
        sim_start_t = time.time()
        while(True):
            self.step(self.fixed_timestep_usec)
            # @todo: Add in a stop condition for when the pod stops before the end
            if self.pod.position > self.tube.length:
                break
        sim_end_t = time.time()
        sim_time = sim_end_t - sim_start_t
        print "LaserOptoTestListener: detected {} gaps".format(self.lotl.n_gaps)
        print "Simulated {} steps/{} seconds in {} actual seconds.".format(self.n_steps_taken, self.elapsed_time_usec/1000000, sim_time)
        

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    from config import *

    import pprint
    
    import argparse
    parser = argparse.ArgumentParser(description="rPod Simulation")
    parser.add_argument('configfile', metavar='config', type=str, nargs='+', default="None",
        help='Simulation configuration file(s) -- later files overlay on previous files')
    args = parser.parse_args()

    sim_config = Config()
    for configfile in args.configfile:
        sim_config.loadfile(configfile)
    
    pprint.pprint(sim_config)
    
    # print sim_config.sim.world.tube.length

    sim = Sim(sim_config.sim)
    
    sim.run()

        
