#!/usr/bin/env python

# File:     c.py
# Purpose:  Utilities to help with c-style coding
# Author:   Ryan Adams
# Date:     2016-Dec-19

# Quick and dirty: 

class CArray:
    def __init__(self, init_list):
        for v in init_list:
            if isinstance(v, dict):
                self.array.append(CStruct(v))
            elif isinstance(v, list):
                self.array.append(CArray(v))

    def __getattr__(self, name):
        if isinstance(name, int):
            return self.array[int]
        else:
            raise AttributeError    
            
class CStruct:
    
    """ Wrapper to make a dict act like a struct (syntax-wise) """
    
    def __init__(self, init_dict):
        for k, v in init_dict:
            if isinstance(v, dict):
                self.__dict__[k] = CStruct(v)
            elif isinstance(v, list):
                self.__dict__[k] = CArray(v)
            else:
                self.__dict__[k] = v

    def __getattr__(self, name):
        attr = self.__internal.get(name, None)
        if attr is None:
            raise AttributeError

        if isinstance(attr, dict):
            return CStruct(self.__internal.get(name))  # Wrap in a CStruct
        else:
            return attr

    def __str__(self):
        # @todo: fix this to do recursive printing (right now below first level it prints object types/ids)
        return str(self.__internal)

    def __coerce__(self, other):
        # return (str(self.__internal), other)
        if isinstance(other, basestring):
            return (self.__str__(), other)
        else:
            return (self.__internal, other)  # ?


class CStruct2:
    def __init__(self, init):
        if isinstance(init, dict):
            self.__dict__ = init
        else:
            pass  # What to do here? throw an error? 

    def __str__(self):
        return str(self.__dict__)

    def __coerce__(self, other):
        return (str(self.__dict__), other)

class CEnum2:
    def __init__(self, init):
        if isinstance(init, dict):
            self.__dict__ = init
        elif isinstance(init, list):
            # Create a dict from the list (list item is key, position is value)
            for i in xrange(len(init)):
                self.__dict__[ init[i] ] = i

    def __str__(self):
        return str(self.__dict__)

    def __coerce__(self, other):
        return (str(self.__dict__), other)


class CEnum:
    # @todo: some sort of checking that values are integers
    
    def __init__(self, init):
        self.__internal = {}
        if isinstance(init, dict):
            self.__internal = init
        elif isinstance(init, list):
            # Create a dict from the list (list item is key, position is value)
            for i in xrange(len(init)):
                self.__internal[ init[i] ] = i
        
    def __getattr__(self, name):
        print name
        if name == "__internal":
            return self.__internal
        attr = self.__internal.get(name, None)
        if attr is None:
            raise AttributeError
        return attr
            
    def __str__(self):
        return str(self.__internal)
        
    def __coerce__(self, other):
        return (self.__str__(), other)


if __name__ == "__main__":
    cs = CStruct({
        'this': "is", 
        "a": ["test", "of"],
        "the": {
            "emergency": "broadcast"
        },
        "system": ".",
        "only": CStruct({
            "a": "test"
        })
    })
        
    print "CStruct: " + cs
    print "CStruct access ('cs.the.emergency'): " + cs.the.emergency
    
    print ""
    
    ce = CEnum(["this", "is", "another", "test"])
    print "CEnum: {}".format( ce )
    
    ce = CEnum({'trying': 1, 'this': 2, 'out': 4})
    ce.first = 5
    print "CEnum: " + ce
    print "CEnum.trying: {}".format(ce.trying)
    
    cs2 = CStruct2({
        'this': "is", 
        "a": ["test", "of"],
        "the": {
            "emergency": "broadcast"
        },
        "system": ".",
        "only": CStruct({
            "a": "test"
        })
    })
    print "CStruct2: " + cs2

    print ""

    ce = CEnum2({'trying': 1, 'this': 2, 'out': 4})
    ce.first = 5
    print "CEnum: " + ce
    print "CEnum.ou: {}".format(ce.out)
