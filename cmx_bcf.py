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
Access to BCF and CMX files

CMX files contain definitions of characters. BCF files are
compressed versions of CMX files
'''

def read_sceleton_from_cmx_stream(stream):
    '''
    CMX files use DOS-style line breaks (\r\n)

    See http://simtech.sourceforge.net/tech/bcf.html
    '''
    lines = stream.read().decode('ascii').split('\r\n')
    filename = lines[0]
    texfilename = lines[1]
