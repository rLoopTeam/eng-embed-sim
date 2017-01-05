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
        if not self.__internal:  # Note: empty dicts evaluate to False
            self.__internal = config_yaml
        else:
            self.__internal = self.merge(self.__internal, config_yaml)
        return self  # fluent
    
    def __getattr__(self, name):
        val = self.__internal.get(name, None)
        if isinstance(val, dict):
            return Config(val)
        else:
            return val
            
    def __str__(self):
        return yaml.dump(self.__internal, default_flow_style=False)
        
    def __repr__(self):
        return self.__str__()
        
    def merge(self, a, b, path=None):
        "merges b into a"
        # @see http://stackoverflow.com/questions/7204805/dictionaries-of-dictionaries-merge
        if path is None: path = []
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    self.merge(a[key], b[key], path + [str(key)])
                elif a[key] == b[key]:
                    pass # same leaf value
                else:
                    a[key] = b[key]
            else:
                a[key] = b[key]
        return a
