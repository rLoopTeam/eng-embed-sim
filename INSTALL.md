# Installation

1. Be on Windows

    The simulator should work on Mac and probably linux, but the FCU is a compiled DLL and will only work on Windows (tested on 8.1, 10.x should also be fine). I've had good success with parallels and Windows 8.1.

2. Make a directory and check out the following repositories as siblings: 
    
    ```
    mkdir rloopsim
    cd rloopsim
    git clone https://github.com/rLoopTeam/eng-embed-sim.git
    git clone https://github.com/rLoopTeam/eng-software-pod.git
    git clone https://github.com/rLoopTeam/react-groundstation.git
    ```

3. Install Python 2.7 (32 bit version). __You must use 32-bit Python or the FCU DLL will not work.__ I'm using Python 2.7.13, but other versions will likely work just fine. 

    ```
    https://www.python.org/ftp/python/2.7.13/python-2.7.13.msi
    ```

    By default, this will install to C:\Python27\ -- if you change the install location, make sure to change 
    the appropriate arguments when setting up your virtualenv as well (see below).

4. Install virtualenv
    
    ```
    pip install virtualenv
    ```

5. Create your virtualenv under your rloopsim directory (we're still in the same directory as step 2). 
    
    ```
    virtualenv --prompt="(rloopsim)" --no-site-packages --python=C:\Python27\python.exe env
    ```

6. Activate the virtualenv
__Remember: You will need to do this at the start of any session working with the simulator.__ See the above link or http://docs.python-guide.org/en/latest/dev/virtualenvs/ for more details.

    Note: you will likely need to relax restrictions on running scripts for this to work. 
    - From powershell, use the following to run a new shell as administrator: 'Start-Process powershell -Verb runAs'
    - From the administrator powershell, run the following: 'Set-ExecutionPolicy RemoteSigned'

    Now you can activate your virtualenv like so: 

    ```
    .\env\Scripts\activate
    ```

7. Use pip to install the simulator in development mode

    ```
    cd eng-embed-sim
    pip install -e .
    ```

8. Run the simulator (from the top level of eng-embed-sim)

    ```
    python rloopsim/sim.py conf/sim_config.py
    ```

(todo: fill in mor documentation)