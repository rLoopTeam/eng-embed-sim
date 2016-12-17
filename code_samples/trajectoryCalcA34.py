#!/usr/bin/env python
import matplotlib.pyplot as plt
import numpy as np

# File:     trajectoryCalcA34.py
# Purpose:  Plots position, velocity, and acceleration for given parameters
# Author:   Sean @capsulecorpslab 
# Date:     2016-Dec-17

# Notes: 
# Plots position, velocity, and acceleration for given parameters
# Adjusts cruising and deceleration periods based on projected braking trajectory
# Neglects drag due to hover engines

# Parameters
deltax_track = 1400		# total track distance [m]
deltax_accel = 478		# acceleration distance [m]
m_pod = 360			# pod mass [kg]
brakepadgap = 3			# brake pad gap [mm]
gforce_pusher = 2.0		# pusher g-force
g = 9.81			# gravitational constant [m/s^2]
xdot = [0]			# initial velocity [m/s]
dt = 0.05			# time step [s]

# Compute acceleration trajectories
xddot1 = gforce_pusher*g					# acceleration [m/s^2]
deltax1 = deltax_accel
xdot_cruise = (xdot[0]**2 + 2*xddot1*deltax1)**0.5		# cruising velocity is equal to final velocity of acceleration period [m/s]
deltat1 = (xdot_cruise - xdot[0])/xddot1			# acceleration period [s]
x1_data = [0]							# initialize dynamic array for position during acceleration at 0m [m]
xdot1_data = [0]						# initialize dynamic array for velocity during acceleration at 0m [m]
i = 1
while xdot1_data[i-1] < xdot_cruise:
	xdot1_dummy = xdot1_data[i-1] + xddot1*dt		# Solve for velocity due to acceleration [m]
	xdot1_data.append(xdot1_dummy)				# dump item into dynamic array
	x1_dummy = x1_data[i-1] + xdot1_dummy*dt		# Solve for position due to velocity [m]
	x1_data.append(x1_dummy)				# dump item into dynamic array
	#print 'xdot1_dummy', xdot1_dummy, 'x1_dummy', x1_dummy
	i += 1
t = np.arange(0, deltat1+dt, dt)				# acceleration period, time vector
x = np.asarray(x1_data)						# dump position data into numpy array [m]
xdot = np.asarray(xdot1_data)					# dump velocity data into numpyarray [m/s]
xddot = xddot1*np.ones(xdot.shape)				# dump acceleration data into numpyarray [m/s^2]
'''
print 't', t
print 'x', x
print 'xdot', xdot
print 'xddot', xddot
print 't.shape', t.shape
print 'x.shape', x.shape
print 'xdot.shape', xdot.shape
print 'xddot.shape', xddot.shape
'''
# Compute deceleration trajectories
Fdrag_data = []						# define dynamic array for drag force [N]
x3_data = [0]						# initialize dynamic array for position during deceleration at 0m [m]
xdot3_data = [xdot_cruise]				# initialize define dynamic array for velocity during deceleration at cruising velocity [m/s]
i = 1							# initialize counter
while xdot3_data[i-1] > 0.01:
#for i in range(0,100):
	if xdot3_data[i-1] < 8:
		# A34 Eddy brake constants for <8 m/s
		a = -175.92*np.exp(-0.21369*brakepadgap)
		b = 3050.8*np.exp(-0.21398*brakepadgap)
		c = 0
	elif xdot3_data[i-1] > 30:
		# A34 Eddy brake constants for >30 m/s
		a = 0.24153*np.exp(-0.21654*brakepadgap)
		b = -78.783*np.exp(-0.21665*brakepadgap)
		c = 12950*np.exp(-0.21708*brakepadgap)
	else:
		# A34 Eddy brake constants for 8-30 m/s
		a = -3.1692*np.exp(-0.28239*brakepadgap)
		b = -9.2684*np.exp(-0.05037*brakepadgap)
		c = 13507*np.exp(-0.21091*brakepadgap)

	Fdrag_dummy = a*xdot3_data[i-1]**2 + b*xdot3_data[i-1] + c	# Solve for nonlinear drag force
	Fdrag_data.append(Fdrag_dummy)					# dump item into dynamic array
	xddot3_dummy = -Fdrag_dummy/m_pod				# Solve for deceleration dute to nonlinear drag force
	xdot3_dummy = xdot3_data[i-1] + xddot3_dummy*dt
	xdot3_data.append(xdot3_dummy)					# dump item into dynamic array
	x3_dummy = x3_data[i-1] + xdot3_data[i-1]*dt
	x3_data.append(x3_dummy)					# dump item into dynamic array

	i += 1

Fdrag_data.append(0)				# Append 0 N force at end of brake period [N]
Fdrag = np.asarray(Fdrag_data)			# dump drag force during deceleration data into numpy array [N]
xddot3 = -Fdrag/m_pod				# define velocity during deceleration array
xdot3 = np.asarray(xdot3_data)			# dump velocity during deceleration data into numpyarray [m/s]
x3 = np.asarray(x3_data)			# dump position during deceleration data into numpy array [m]
deltax3 = x3_data[i-1]				# deceleration distance [m]
deltat3 = i*dt					# deceleration period [s]
t3 = np.arange(0, deltat3, dt)			# deceleration time vector [s]

# Calculate adjusted cruising trajectory using deceleration calcs
deltax2 = deltax_track - deltax1 - deltax3		# cruising distance [m]
deltat2 = deltax2/xdot_cruise				# cruising period is equal to cruising distance divided by cruising velocity [s]
t2 = np.arange(0, deltat2, dt)				# cruising time vector [s]

x2 = np.arange(deltax1, deltax1 + deltax2, xdot_cruise*dt)	# position trajectory for cruising period [m]
x = np.append(x, x2)						# dump & append position data into numpy array [m]
xdot2 = xdot_cruise*np.ones(x2.shape)
xdot = np.append(xdot, xdot2)					# dump & append velocity data into numpyarray [m/s]
xddot2 = np.zeros(x2.shape)
xddot = np.append(xddot, xddot2)				# dump & append acceleration data into numpyarray [m/s^2]
t2 = np.arange(deltat1 + dt, deltat1 + deltat2 + dt, dt)
#print 't', t
#print 't_cruise', t_cruise
#print 'deltat_cruise', deltat_cruise
t = np.append(t, t2)					# append to total time vector [s]

'''
print 't2', t2
print 'x2', x2
print 'xdot2', xdot2
print 'xddot2', xddot2
print 't2.shape', t2.shape
print 'x2.shape', x2.shape
print 'xdot2.shape', xdot2.shape
print 'xddot2.shape', xddot2.shape
'''

#print 'deltax_track', deltax_track
#print 'deltax1', deltax1
#print 'deltax3', deltax3
#print 'deltax2', deltax2
#print 'deltat_cruise', deltat_cruise

# total trajectory
x3 = np.add(x3, deltax1 + deltax2)
x = np.append(x, x3)
xdot = np.append(xdot, xdot3)
xddot = np.append(xddot, xddot3)
t = np.arange(0, deltat1 + deltat2 + deltat3 + dt, dt)	# total time vector [s]

print 't', t
print 'x', x
print 'xdot', xdot
print 'xddot', xddot
print 't.shape', t.shape
print 'x.shape', x.shape
print 'xdot.shape', xdot.shape
print 'xddot.shape', xddot.shape

#save data to text file
np.savetxt('trajectorysim.csv',
           np.transpose([t,x, xdot, xddot/g]),
           delimiter='\t',
           header='t(s)\t x(m)\t xdot(m/s)\t g-force\t',
           )

plt.figure(1)
plt.subplot(311)
plt.title("rPod Trajectory, 360kg, 3mm constant gap (A34)")
plt.plot(t, x, '.')
plt.ylabel("Position(m)")

plt.subplot(312)
plt.plot(t, xdot, '.')
plt.ylabel("Velocity(m/s)")

plt.subplot(313)
plt.plot(t, xddot/g, '.')
plt.ylabel("Acceleration(g's)")
plt.xlabel("Time(s)")
plt.show()