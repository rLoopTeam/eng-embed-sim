#!/usr/bin/env python
# coding=UTF-8

# File:     env.py
# Purpose:  Runtime environment management for the simulator (OS environment, not physical)
# Author:   Ryan Adams (radams@cyandata.com, @ninetimeout)
# Date:     2017-Jan-23

import logging
import os

class Env:
    """ Simple runtime environment manager """

    def __init__(self, working_dir=None):
        self.logger = logging.getLogger("Env")
        
        # Used for context manager
        self._working_dir = working_dir
        self._saved_path = None
        
    def cwd(self):
        """ Get current working directory """
        return os.getcwd()
        
    def cd(self, path):
        oldPath = self.cwd()
        print oldPath
        try:
            os.chdir(os.path.expanduser(path))
        except Exception as e:
            self.logger.error(e)
            print os.getcwd()
            raise e

        return oldPath

    def mkdir(self, path):
        """ Make a directory, with, 'mkdir -p' type functionality """
        pass
    
    def __enter__(self):
        self._saved_path = self.cwd()
        self.cd(self._working_dir)

    def __exit__(self, etype, value, traceback):
        self.cd(self._saved_path)
        self._saved_path = None  # Just cleaning up


if __name__ == "__main__":
    env = Env()
    env.cd("./test")
    print "cwd is {}".format(env.cwd())
    env.cd("..")
    print "Should be back to start: {}".format(os.getcwd())
    with Env("test"):
        print os.getcwd()
        
    print os.getcwd()