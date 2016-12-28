#!/usr/bin/env python

# @see http://stackoverflow.com/questions/4230725/how-to-execute-a-python-script-file-with-an-argument-from-inside-another-python
# @see https://docs.python.org/3/library/argparse.html

import sys

# print sys.argv[2:]  # Chop off the first 2 arguments

if sys.argv[1] == "test":
    import util_test
    util_test.main(*sys.argv[2:])  