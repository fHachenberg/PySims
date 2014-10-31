# -*- coding: utf-8 -*-

#Copyright (C) 2014 Fabian Hachenberg

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

import re
import struct
from io import SEEK_SET

class IffFile(object):
    '''
    Represents an open IFF file 
    '''
    def __init__(self, stream):
        self.stream = stream

        def chop_next_string(data):
            '''
            for a byte stream data, identifies position of next
            zero character and cuts the stream into two peaces at
            that position, returns both
            '''
            end = next(i for i,k in enumerate(data) if k == 0)
            return data[:end], data[end+1:]

        max_signature_size = 0x60
        data = stream.read(max_signature_size)
        signature_a, data = chop_next_string(data)
       
        signature_a_pattern = r"IFF FILE ([0-9].[0-9]):TYPE FOLLOWED BY SIZE"
        match = re.search(signature_a_pattern, str(signature_a))
        if match == None:
            raise IOError("IFF signature is missing, propably not an IFF file")
    
        version = match.group(1)
        #In the original game files, versions 2.0 and 2.5 can be found
        if version == "2.5":
            signature_b = data[0:25]
            signature_b_pattern = "JAMIE DOORNBOS & MAXIS 1"
            if signature_b != signature_b_pattern:
                raise IOError("IFF file 2.5, but signature part 2 is wrong")
        
        stream.seek(60, SEEK_SET)
        manifest_offset, = struct.unpack("<I", stream.read(4))
        print(manifest_offset)

import os.path
import functools
import pdb
import random

official_gamedta_relpath = "TheSims_official_gamedata"

#Testdata
class KnownIffFile(object):
    def __init__(self, filename, contents):
        self.contents = dict(contents)
        self.filename = filename 

    def get_any_filestream(self):
        filename = random.choice(self.contents.keys())
        assert False

    def get_file_size(self, filename):
        return self.contents[filename][0]

def requires_known_iff_file(testfunc):
    @functools.wraps(testfunc)
    def test_decorated():
        testfunc(known_iff_file=known_iff_file)
    return test_decorated

from nose.tools import assert_raises

ifffile = IffFile(open(os.path.join(official_gamedta_relpath, "UserData2", "Houses", "House00.iff"), "rb"))

