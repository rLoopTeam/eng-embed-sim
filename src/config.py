#!/usr/bin/env python

import yaml

class Config:
    
    def __init__(self, config_dict=None):
        if config_dict is not None:
            self.__internal = config_dict
        else:
            self.__internal = {}
        
    def loadfile(self, filename):
        stream = file(filename, 'r')
        config_yaml = yaml.load(stream)
        self.__internal = config_yaml
        return self  # fluent
    
    def __getattr__(self, name):
        val = self.__internal.get(name, None)
        if isinstance(val, dict):
            return Config(val)
        else:
            return val
            
    def __str__(self):
        return str(self.__internal)