#!/usr/bin/env python

from multiprocessing import Process, Manager

def f(d):
    d[1] += '1'
    d['2'] += 2
    d[3]['testing'] = 19

if __name__ == '__main__':
    manager = Manager()

    d = manager.dict()
    d[1] = '1'
    d['2'] = 2
    d[3] = {"testing": 13, "this": 14}  

    p1 = Process(target=f, args=(d,))
    p2 = Process(target=f, args=(d,))
    p1.start()
    p2.start()
    p1.join()
    p2.join()

    print d
