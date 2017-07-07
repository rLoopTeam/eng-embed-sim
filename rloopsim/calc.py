from config import Config
from pint import UnitRegistry
import numpy as np

import argparse
parser = argparse.ArgumentParser(description="rPod Simulation")
parser.add_argument('configfile', metavar='config', type=str, nargs='+', default="None",
    help='Simulation configuration file(s) -- later files overlay on previous files')
args = parser.parse_args()

config = Config()
config.loadfiles(args.configfile)

ureg = UnitRegistry()

qs = config.sim.tube

P = ureg.parse_expression(qs.air_pressure).to("Pa")
R = ureg.parse_expression(qs.air_specific_gas_constant)
#T = ureg.parse_expression(qs.air_temperature)

T = 5/9 * ( qs.air_temperature - 32) + 273

Q_ = ureg.Quantity

pressures = np.linspace(0.125, 12.5, 4)
for pressure in pressures:
    p_psi = Q_(pressure, ureg.psi)
    p_pa = p_psi.to(ureg.pascal)
    print "{} = {}".format(p_psi, p_pa)
    

#print qs.air_temperature
#print ureg.parse_expression(qs.air_temperature)


print P
print R
print T
