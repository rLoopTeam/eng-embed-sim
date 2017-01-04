#!/usr/bin/env python

# NOTE: This must be done in a 32 bit version of python!
# @see http://stackoverflow.com/questions/33709391/using-multiple-python-engines-32bit-64bit-and-2-7-3-5

import sys
import os
import ctypes
import pprint


#dll_path = sys.argv[1]
dll_path = "C:\\Users\\radams\\Documents\\rLoop\\code\\eng-software-pod\\APPLICATIONS\\PROJECT_CODE\\DLLS\\LDLL173__RLOOP__LCCM653\\bin\\Debug"
dll_name = "LDLL173__RLOOP__LCCM653.dll"
dll_filename = os.path.join(dll_path, dll_name)
print "DLL {} exists? {}".format(dll_filename, os.path.exists(dll_filename))
lib = ctypes.WinDLL(dll_filename)
print "Lib loaded successfully!"
value = lib.vPWRNODE__Init()
print "Called vPWRNODE__Init()! Got {} in return.".format(value)
try:
    hmm = lib.not_a_real_function()
    print "Called not_a_real_function(), got {} in return.".format(hmm)
except Exception as e:
    print "Called a fake function, got an (expected) exception! ({})".format(e)