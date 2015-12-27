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
More than one file format from TheSims™ exists in a verbose ascii version
and a more dense binary version. Where the verbose files contain
ASCII strings for numbers, the dense files contain binary-coded
integers and floats.
Because the basic structure is identical though, we use the same
functions and the same classes to represent both file contents. The
difference is in how we read in basic numbers and strings. For that
purpose we introduce two classes in this file:
    BinaryDataStream reads little-endian encoded integers and floats as
                     well as strings from an input stream
    TextDataStream   reads ascii-encoded numbers as well as strings from
                     an input string
'''

from .fileiocommon import read_pascal_style_string, read_zero_zerminated_string

import struct

class BinaryDataStream(object):
    '''
    binary version
    '''
    def __init__(self, bytestream):
        self.stream = bytestream

    def read_int(self):
        return struct.unpack("<I", self.stream.read(4))[0]

    def read_ints(self, num):
        return struct.unpack("<" + "".join(["I"]*num), self.stream.read(4*num))

    def read_float(self):
        return struct.unpack("<f", self.stream.read(4))[0]

    def read_floats(self, num):
        return struct.unpack("<" + "".join(["f"]*num), self.stream.read(4*num))

    def read_str(self):
        return read_pascal_style_string(self.stream).decode("ascii")

class TextDataStream(BinaryDataStream):
    '''
    text version
    '''
    def __init__(self, bytestream, skip_lines=0, seq_delim=""):
        '''
        @param skip_lines Some verbose formats like CMX have additional dummy lines in the beginning which have to be skipped
        @param seq_delim in CMX files, sequences of floats are delimited by | (e.g. | 1.0 0.0 0.0 |).
        '''
        #skip lines
        for i in range(skip_lines):
            bytestream.readline()
        BinaryDataStream.__init__(self, bytestream)
        self.seq_delim = seq_delim

    def read_int(self):
        return int(self.stream.readline())

    def read_ints(self, num):
        elements = [a for a in self.stream.readline().decode('ascii').strip(seq_delim).split(" ") if a != ""]
        assert len(elements) == num
        return tuple(int(a) for a in elements)

    def read_float(self):
        return float(self.stream.readline())

    def read_floats(self, num):
        elements = [a for a in self.stream.readline().decode('ascii').strip(seq_delim).split(" ") if a != ""]
        assert len(elements) == num
        return tuple(float(a) for a in elements)

    def read_str(self):
        return self.stream.readline().strip().decode("ascii")

