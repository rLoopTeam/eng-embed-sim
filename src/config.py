#!/usr/bin/env python

# File:     config.py
# Purpose:  Configuration classes to allow easy access to yaml config
# Author:   Ryan Adams (radams@cyandata.com, @ninetimeout)
# Date:     2016-Dec-28

import yaml
from collections import MutableMapping

# @todo: Add the ability to have a list in the config that contains dicts (should return a list of Configs)

class Config(MutableMapping):
    
    def __init__(self, config_dict=None):
        # Note: need to set __dict__ directly because we're overriding __setattr__
        if config_dict is not None:
            if isinstance(config_dict, Config):
                self.__internal = config_dict.__internal
            else:
                self.__internal = config_dict
        else:
            self.__internal = {}
        
    def loadfile(self, filename):
        stream = file(filename, 'r')
        config_yaml = yaml.load(stream)
        if not self.__internal:  # Note: empty dicts evaluate to False
            self.__internal = config_yaml
        else:
            self.__internal = Config.merge(self.__internal, config_yaml)
        return self  # fluent
    
    def loadfiles(self, filenames):
        for filename in filenames:
            self.loadfile(filename)
    
    def __getattr__(self, name):
        if name in ['_Config__internal']:
            return self.__dict__['__internal']
        val = self.__internal.get(name, None)
        if isinstance(val, dict):
            return Config(val)
        else:
            return val
    
    def __setattr__(self, name, value):
        if self.__dict__.has_key(name) or name == "_Config__internal":       # any normal attributes are handled normally
            object.__setattr__(self, name, value)
        else:
            self.__internal[name] = value
    
    def __iter__(self):
        
        return iter(self.__internal)

    def __contains__(self, value):
        return value in self.__internal

    def __len__(self):
        return len(self.__internal)
    
    def __getitem__(self, key):
        return self.__internal[key]

    def __setitem__(self, key, value):
        self.__internal[key] = value

    def __delitem__(self, key):
        del self.__internal[key]
        
    def __str__(self):
        return yaml.dump(self.__internal, default_flow_style=False)
        
    def __repr__(self):
        return self.__str__()
    
    @classmethod
    def merge(a, b, path=None):
        "merges b into a"
        # @see http://stackoverflow.com/questions/7204805/dictionaries-of-dictionaries-merge
        if path is None: path = []
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    Config.merge(a[key], b[key], path + [str(key)])
                elif a[key] == b[key]:
                    pass # same leaf value
                else:
                    a[key] = b[key]
            else:
                a[key] = b[key]
        return a
