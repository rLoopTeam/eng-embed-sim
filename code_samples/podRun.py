from scipy.integrate import ode
from scipy.special import gamma, airy
from numpy import arange
from EddyBrake import EddyBrake
import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import json
from scipy.optimize import minimize_scalar
from scipy.interpolate import interp1d

parser = argparse.ArgumentParser()
parser.add_argument('infile',help='input file')
args = parser.parse_args() 

f = open(args.infile)
raw = f.read()
f.close

inputs = json.loads(raw)

# inputs
##########
m_pod = inputs['m_pod'] #kg 
eddyBrakeDataFile = inputs['eddyBrakeDataFile']

c_d = inputs['c_d']
rho = inputs['rho']
frontal_area = inputs['frontal_area']

t_max = inputs['t_max'] #seconds
t0 = inputs['t0']

x_0 = inputs['x_0'] # pod initial position
v_0 = inputs['v_0'] # pod initial velocity

dt_outer = inputs['dt_outer']
outfile = inputs['outfile']

brakeControllerDict = inputs['brakeController']

plot_title = inputs['plot_title']
##########

def dragForce(v):
  return 0.5*rho*frontal_area*c_d*v**2    #magnitude!

class constantGapBrakeController():

  def __init__(self,params):
    self.gap = params['gap']

  def evaluate(self,t,a,v,x):
    return self.gap,0

class trajectoryPlanController():

  def __init__(self,params,m_pod,eddyBrake):
    self.eb = eddyBrake
    self.m_pod = m_pod
    
    self.state = 'accel'

    self.gap_max = params['gap_max']
    self.gap_min = params['gap_min']

    self.xMaxAccel = params['xMaxAccel']
    self.xMax = params['xMax']
    self.vMax = params['vMax']
    self.accel = params['accel']*9.81
    self.brakingMode = params['brakingMode']

    df = pd.read_csv(params['brakingCurve'])
    df = df[df['velocity [m/s]'].isnull() == False]
    df = df.sort(['velocity [m/s]'])
    self.brakeCurveDispAtSpeed = interp1d(df['velocity [m/s]'],df['position [m]'])
    self.brakeCurveMaxDisp = df['position [m]'].max()
    self.brakeCurveAccelAtSpeed = interp1d(df['velocity [m/s]'],df['accel [g]'])
    self.brakeCurveGapAtPosition = interp1d(df['position [m]'],df['gap [m]'])

  def evaluate(self,t,a,v,x):

    if self.state == 'accel':
      if (v >= self.vMax) or (x >= self.xMaxAccel):
        self.state = 'coast'
        print('accel->coast')
      if self.itsTimeToStartBraking(v,x):
        self.state = 'brake'
        self.brakingCurveOffset = x
        print('accel->brake')
      thrust = self.m_pod*self.accel
      h = self.gap_max

    if self.state == 'coast':
      if self.itsTimeToStartBraking(v,x):
        self.state = 'brake'
        self.brakingCurveOffset = x
        print('coast->brake')
      thrust = 0
      h = self.gap_max

    if self.state == 'brake':
      if self.brakingMode == 'minGap':
        h = self.gap_min
        thrust = 0
      elif self.brakingMode == 'gapVsPosition':
        h = self.brakeCurveGapAtPosition(x-self.brakingCurveOffset)
        # needs work, not correct               ^
        thrust = 0
      else:
        raise Warning("brakingMode was not specified in brakeController params")

    return h,thrust

  def itsTimeToStartBraking(self,v,currentPosition):
    stoppingDistanceNeeded = self.brakeCurveMaxDisp - self.brakeCurveDispAtSpeed(v)
    if (currentPosition + stoppingDistanceNeeded) > self.xMax:
      return True
    else:
      return False
	
	
class PodModel():

  def __init__(self,m_pod):
    self.t = 0
    self.t_old = 0
    self.v = 0
    self.v_old = 0
    self.x = 0
    self.x_older = 0
    self.h = 0.001
    self.m_pod = m_pod
    self.a = 0
    self.thrust = 0

  def setICs(self,y,t):
    self.t = t
    self.t_old = t
    self.v = y[1]
    self.v_old = y[1] 
    self.x = y[0]
    self.x_older = y[0]

  def setEddyBrakeModel(self,model):
    self.eddyBrake = model

  def on_control_loop_timestep(self,h,thrust):
    self.h = h
    self.thrust = thrust
    return None

  def on_integrator_timestep(self,t,y):
    self.t_old = self.t
    self.t = t
    self.v_old = self.v
    self.v = y[1]
    self.x_old = self.x
    self.x = y[0]
    self.a = (self.v - self.v_old)/(self.t-self.t_old)
    # update any coeffecients if needed
    # for example the current rail temp could be calculated
    # here, but now it's purely an output so it's not needed,
    # but if a radiation model were implemented, we'd need to
    # calculate it here. For example:
    #self.T_final = railTemp(eddyBrake.q_max(v,h))
    return None

  def y_dot(self,t,y):
    x = y[0]
    v = y[1]
    a = (self.thrust
         -self.eddyBrake.f_drag(v,self.h)-dragForce(v)
        )/self.m_pod
    return [v,a]
  

t = arange(0, t_max, dt_outer)
n_outerSteps = t_max/dt_outer

# allocate state variables
t = np.ones(n_outerSteps+1)*np.nan
x = np.ones(n_outerSteps+1)*np.nan
v = np.ones(n_outerSteps+1)*np.nan
a = np.ones(n_outerSteps+1)*np.nan

# allocate aux fields
T_final = np.ones(n_outerSteps+1)*np.nan
H_y_max = np.ones(n_outerSteps+1)*np.nan
H_y_mean = np.ones(n_outerSteps+1)*np.nan
accel_g = np.ones(n_outerSteps+1)*np.nan
lift_per_assy = np.ones(n_outerSteps+1)*np.nan
gap = np.ones(n_outerSteps+1)*np.nan


# create state vector for t0
y0 = [x_0, v_0]

# initialize model
eddyBrake = EddyBrake(eddyBrakeDataFile)
model = PodModel(m_pod)
model.setEddyBrakeModel(eddyBrake)
model.setICs(y0,t0)

# instanciate brake controller
if brakeControllerDict['type'] == 'constant_gap':
  controller = constantGapBrakeController(brakeControllerDict['params'])
elif brakeControllerDict['type'] == 'trajectoryPlanController':
  controller = trajectoryPlanController(brakeControllerDict['params'],m_pod,eddyBrake)
else:
  raise Warning('no brake controller specified')

# store state vars for t0
x[0] = x_0
v[0] = v_0
a[0] = 0.0

# evaluate aux variables for t0
lift_per_assy[0] = eddyBrake.f_lift(model.v,model.h)
accel_g[0] = 0
gap[0] = model.h

r = ode(model.y_dot).set_integrator("dopri5")
r.set_solout(model.on_integrator_timestep)
r.set_initial_value(y0, t0)

h,thrust = controller.evaluate(t[0],a[0],v_0,x_0)
model.on_control_loop_timestep(h,thrust)

i=0
while r.successful() and i<n_outerSteps:
  r.integrate(r.t+dt_outer)
  print('time: {}, velocity: {}'.format(r.t,model.v))
  i+=1
  h,thrust = controller.evaluate(r.t,model.a,model.v,model.x)
  model.on_control_loop_timestep(h,thrust)

  t[i] = r.t
  x[i] = r.y[0]
  v[i] = r.y[1]
  a[i] = model.a

  lift_per_assy[i] = eddyBrake.f_lift(v[i],model.h)
  accel_g[i] = model.a/9.81
  gap[i] = model.h

# output

df_out = pd.DataFrame({
    'time [s]':t,
    'position [m]':x,
    'velocity [m/s]':v,
    'accel [g]':accel_g,
    'aerodrag':dragForce(v),
    'gap [m]':h,
    'lift per assy [N]':lift_per_assy
    })

df_out.to_csv(outfile)


plt.figure(figsize=(12,18))

plt.subplot(511)
plt.title(plot_title)
plt.plot(t,x)
plt.xlabel('time [s]')
plt.ylabel('position [m]')
plt.grid()

plt.subplot(512)
plt.plot(t,v)
plt.xlabel('time [s]')
plt.ylabel('velocity [m/s]')
plt.grid()

g1=plt.subplot(513)
plt.plot(t,accel_g)
plt.xlabel('time [s]')
plt.ylabel('accel [g]')
plt.grid()
min, max = g1.get_ylim()
g2 = g1.twinx()
gToForce = 320*9.81
g2.set_ylim(min*gToForce,max*gToForce)
g2.yaxis.set_ticks([-8000,-6000,-4000,-2000,0,2000,4000,6000,8000])
g2.set_ylabel('force [N]')


plt.subplot(514)
plt.plot(t,lift_per_assy)
plt.xlabel('time [s]')
plt.ylabel('normal force per\n assembly [N]')
plt.grid()

gapPlt = plt.subplot(515)
plt.plot(t,gap)
plt.xlabel('time [s]')
plt.ylabel('magnet to I-beam\ngap [m]')
gapPlt.set_ylim(0,0.035)
plt.grid()

plt.savefig('trajectory_plot')
#plt.show()
