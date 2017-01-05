
from pod import Pod
from tube import Tube
from pusher import Pusher
#from fcu import fcu

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
        
        # Testing only
        from sensors import LaserOptoSensor, SensorConsoleWriter, LaserOptoTestListener  # @todo: move this to the top once we're done testing
        self.laser_opto_1 = LaserOptoSensor(self, self.config.sensors.laser_opto_1)
        #self.laser_opto_1.register_step_listener(SensorConsoleWriter())  # Write data directly to the console
        self.laser_opto_1.register_step_listener(LaserOptoTestListener())
        
    def step(self, dt_usec):        
        # Step the pusher first (will apply pressure and handle disconnection)
        self.pusher.step(dt_usec)

        # Step the pod (will handle all other forces and pod physics)
        self.pod.step(dt_usec)
        
        #self.fcu.step(dt_usec)
        self.laser_opto_1.step(dt_usec)
        #self.logger.debug(list(self.laser_opto_1.pop_all()))
        
        self.elapsed_time_usec += dt_usec

    def run(self):
        self.logger.info("Starting simulation")
        while(True):
            self.step(self.fixed_timestep_usec)
            # @todo: Add in a stop condition for when the pod stops before the end
            if self.pod.position > self.tube.length:
                break
        

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    from config import *

    import pprint
    
    import argparse
    parser = argparse.ArgumentParser(description="rPod Simulation")
    parser.add_argument('configfile', metavar='config', type=str, nargs='?', default="None",
        help='Simulation configuration file(s)')
    args = parser.parse_args()

    sim_config = Config()
    sim_config.loadfile(args.configfile)
    
    # print sim_config.sim.world.tube.length

    sim = Sim(sim_config.sim)
    
    sim.run()

        
