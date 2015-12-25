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
Some integration tests based on original Game data
'''

from . import gamedata_for_tests
from .iff import IffFile
from .far import FarFile

def test_smoketest_maid_iff_file():
    stream = open(gamedata_for_tests.objects_far_filename, "rb")
    farfile = FarFile(stream)
    maid_stream = farfile.open("People\\maid.iff", stream)
    ifffile = IffFile(maid_stream)
    for entry in ifffile.iter_open(lambda header: True, maid_stream):
        print(entry)


