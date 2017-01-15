# @see http://stackoverflow.com/questions/29832055/animated-subplots-using-matplotlib

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

def data_gen():
    t = data_gen.t
    cnt = 0
    while cnt < 1000:
        cnt+=1
        t += 0.05
        y1 = np.sin(2*np.pi*t) * np.exp(-t/10.)
        y2 = np.cos(2*np.pi*t) * np.exp(-t/10.)
        # adapted the data generator to yield both sin and cos
        yield t, y1, y2

def fig2_data_gen():
    t = data_gen.t
    cnt = 0
    while cnt < 1000:
        cnt+=1
        t += 0.05
        y1 = np.sin(2*np.pi*t) * np.exp(-t/10.)
        y2 = np.cos(2*np.pi*t) * np.exp(-t/10.)
        # adapted the data generator to yield both sin and cos
        yield t, y1, y2

data_gen.t = 0
fig2_data_gen.t = 0

# create a figure with two subplots
#fig, (ax1, ax2) = plt.subplots(2,1)
fig = plt.figure()
ax1 = fig.add_subplot(2,1,1)
ax2 = fig.add_subplot(2,1,2)
#ax1, ax2 = fig.subplots(nrows=2, ncols=1)

fig2 = plt.figure()
fig2ax1 = fig2.add_subplot(2,1,1)
fig2ax2 = fig2.add_subplot(2,1,2)


# intialize two line objects (one in each axes)
line1, = ax1.plot([], [], lw=2)
line2, = ax2.plot([], [], lw=2, color='r')
line = [line1, line2]

fig2line1, = fig2ax1.plot([], [], lw=2)
fig2line2, = fig2ax2.plot([], [], lw=2, color='g')
fig2line = [fig2line1, fig2line2]


# the same axes initalizations as before (just now we do it for both of them)
for ax in [ax1, ax2]:
    ax.set_ylim(-1.1, 1.1)
    ax.set_xlim(0, 5)
    ax.grid()

for ax in [fig2ax1, fig2ax2]:
    ax.set_ylim(-1.1, 1.1)
    ax.set_xlim(0, 5)
    ax.grid()


# initialize the data arrays 
xdata, y1data, y2data = [], [], []
def run(data):
    # update the data
    t, y1, y2 = data
    xdata.append(t)
    y1data.append(y1)
    y2data.append(y2)

    # axis limits checking. Same as before, just for both axes
    for ax in [ax1, ax2]:
        xmin, xmax = ax.get_xlim()
        if t >= xmax:
            ax.set_xlim(xmin, 2*xmax)
            ax.figure.canvas.draw()

    # update the data of both line objects
    line[0].set_data(xdata, y1data)
    line[1].set_data(xdata, y2data)

    return line

fig2xdata, fig2y1data, fig2y2data = [], [], []
def fig2run(data):
    # update the data
    t, y1, y2 = data
    fig2xdata.append(t)
    fig2y1data.append(y1)
    fig2y2data.append(y2)

    # axis limits checking. Same as before, just for both axes
    for ax in [fig2ax1, fig2ax2]:
        xmin, xmax = ax.get_xlim()
        if t >= xmax:
            ax.set_xlim(xmin, 2*xmax)
            ax.figure.canvas.draw()

    # update the data of both line objects
    fig2line[0].set_data(fig2xdata, fig2y1data)
    fig2line[1].set_data(fig2xdata, fig2y2data)

    return fig2line
    

ani2 = animation.FuncAnimation(fig2, fig2run, fig2_data_gen, blit=False, interval=10, repeat=False)
ani = animation.FuncAnimation(fig, run, data_gen, blit=False, interval=10, repeat=False)
plt.show()