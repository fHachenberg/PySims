# -*- coding: utf-8 -*-

#Copyright (C) 2014, 2015 Fabian Hachenberg

#This file is part of PySims Lib.
#PySims Lib is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#More information about the license is provided in the LICENSE file.

#PySims Lib is based on the thorough description of game data formats
#in The Sims™ done by Dave Baum, Greg Noel and Peter Gould (and others).
#Their online documentation and implementation in C is available at
#http://simtech.sourceforge.net/home/welcome.html
#The Sims™ is a trademark of Maxis and Electronic Arts.

'''
Reading of CFP files (compressed animation data)

see
http://simtech.sourceforge.net/tech/cfp.html
http://simtech.sourceforge.net/tech/cfp-research.html
'''

import struct
import math

def read_compressed_floats(stream, num):
    dta = [None]*num
    last_value = None
    count_read = 0
    while count_read < num:
        opcode = struct.unpack("<B", stream.read(1))[0]
        if opcode == 0xff: #raw float
            dta[count_read] = struct.unpack("<f", stream.read(4))[0]
            last_value = dta[count_read]
            count_read += 1
        elif opcode == 0xfe: #repeat
            assert last_value != None
            count = 1 + struct.unpack("<H", stream.read(2))[0] #zero means: repeated once
            dta[count_read:count_read+count] = [last_value]*count
            count_read += count
        elif opcode == 0xfd:
            assert False
        else: #opcode is actually a delta value
            x = float(opcode)
            dta[count_read] = last_value + 3.9676e-10 * (x-126)**3 * math.fabs(x-126)
            last_value = dta[count_read]
            count_read += 1
    assert count_read == num #sanity check
    return dta

def read_animdta_from_cfp_stream(stream, num_px, num_py, num_pz, num_rw, num_rx, num_ry, num_rz):
    '''
    @param stream file-like object
    @param num_** since CFP files are not self-describing, the number of entries of each kind have to be fed to the read routine

    @return tuple of lists of floats: (px, py, pz, rw, rx, ry, rz)
    '''
    dta = read_compressed_floats(stream, num_px+num_py+num_pz+num_rx+num_ry+num_rz+num_rw)

    a,b,c,d,e,f,g,h = 0, \
                      num_px, \
                      num_px+num_py, \
                      num_px+num_py+num_pz, \
                      num_px+num_py+num_pz+num_rx, \
                      num_px+num_py+num_pz+num_rx+num_ry, \
                      num_px+num_py+num_pz+num_rx+num_ry+num_rz, \
                      num_px+num_py+num_pz+num_rx+num_ry+num_rz+num_rw
    fromto = [(a,b), (b,c), (c,d), (g,h), (d,e), (e,f), (f,g)]
    return [dta[f:t] for (f,t) in fromto]
