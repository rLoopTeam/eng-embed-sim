#eng-embed-sim

# Installation

1. Be on Windows
..The simulator should work on Mac and probably linux, but the FCU is a compiled DLL and will only work on Windows (tested on 8.1, 10 should be fine)

{:start="2"}
2. Make a directory and check out the following repositories as siblings: 
```
mkdir rloop_or_something
cd rloop_or_something
git clone https://github.com/rLoopTeam/eng-embed-sim.git
git clone https://github.com/rLoopTeam/eng-software-pod.git
git clone https://github.com/rLoopTeam/react-groundstation.git
```

{:start="3"}
3. Install Anaconda 32-bit, Python 2.7. __You must use 32-bit Python or the FCU will not work.__
```
https://repo.continuum.io/archive/Anaconda2-4.2.0-Windows-x86.exe
```

{:start="4"}
4. From the top of this Create the anaconda virtualenv (this will create env 'rloop'). See http://conda.pydata.org/docs/using/envs.html if you need more help.
```
conda env create -f environment.yml
```

{:start="5"}
5. Activate the virtualenv
..You will need to do this at the start of any session working with the simulator.
```
activate rloop
```

{:start="6"}
6. Run the simulator
```
python src/fcu.py conf/sim_config.py
```

(todo: fill in mor documentation)