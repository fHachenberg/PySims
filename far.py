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

import struct
import io
from io import SEEK_SET, SEEK_CUR, SEEK_END

class FreeFarFileEntryStream(io.IOBase):
    '''
    Provides a read-only file-like bytes stream 
    to an entry in a FAR file
    '''
    def __init__(self, stream, off, length):
        self.stream = stream
        self.stream.seek(off)
        self.off = off
        self.length = length
        self.end = off + length #offset of byte behind end of file
 
    '''
    def __iter__(self):
        while True:
            line = self.readline()
            if line == "":
                return
            yield line

    def __next__(self):
        line = self.readline()
        if line == "":
            raise StopIteration
        return line
    '''

    def read(self):
        pos = self.stream.tell()
        return self.stream.read(self.end-pos)

    def close(self):
        self.stream.close()

    closed = property(lambda self: self.stream.closed)

    def fileno(self):
        return self.stream.fileno()

    def flush(self):
        return self.stream.flush()

    def isatty(self):
        return False

    def readable(self):
        return self.stream.readable()

    def readline(self, size=-1):
        pos = self.stream.tell()
        if size == -1:
            size = self.length
        size = min(size, self.end - pos)
        return self.stream.readline(size)

    def readlines(self, hint=-1):
        pos = self.stream.tell()
        if hint == -1:
            hint = self.length
        hint = min(hint, self.end - pos)
        return self.stream.readlines(hint)

    def seek(self, offset, whence=SEEK_SET):
        if whence == SEEK_SET:
            self.stream.seek(min(self.end-1, offset + self.off), SEEK_SET)
        elif whence == SEEK_CUR:
            pos = self.stream.tell()
            if offset > 0:
                self.stream.seek(min(self.end-pos, offset), SEEK_CUR)
            else:
                self.stream.seek(max(self.off-pos, offset), SEEK_CUR)
        elif whence == SEEK_END:
            self.stream.seek(max(self.off, self.end+offset), SEEK_SET)

    def seekable(self):
        return self.stream.seekable()

    def tell(self):
        return self.stream.tell() - self.off
     
    def writable(self):
        return False

class FarFile(object):
    '''
    Represents an open FAR file

    Works in 2 possible modes:
        -in the multiple-streams mode, a filename to a FAR file
         must be provided. The FAR file object then can create multiple
         read-only file-like objects to access files within the FAR file
        -in the single-stream mode, the FAR file operates on a given
         stream. In this mode, only one readwrite file-like object 
         to access files within the FAR file can be used at one time

    TODO: implement Context Manager interface
    '''
    class FarFileEntry(object):
        '''
        Helper class to represent the entries in the FAR file
        '''
        def __init__(self, filename, off, len1, len2):
            self.filename = filename
            self.off = off
            self.len1 = len1
            self.len2 = len2

    def __init__(self, filename):
        '''      

        TODO: implement write access
        '''
        databuffer = open(filename, "rb")
        self.filename = filename

        self.__entries = []
        self.access_mode = "multiple"

        signature = databuffer.read(8)
        if bytes(signature) != b"FAR!byAZ":
            raise IOError("FAR signature is missing, propably not a FAR file")
        version, manifest_offset = struct.unpack("<iI", databuffer.read(8))
        #Read the Manifest, create an entry for every file entry

        def read_manifest_entry():
            '''
            helper function to read manifest entry
            '''
            file_len1, file_len2, file_off, filename_len = struct.unpack("<IIII", databuffer.read(16))
            filename = databuffer.read(filename_len).decode('ascii')
            print(filename, file_len1, file_len2, file_off)
            return (filename, file_off, file_len1, file_len2)
        
        databuffer.seek(manifest_offset)
        num_entries, = struct.unpack("<I", databuffer.read(4))
        for i in range(num_entries):
            entry = FarFile.FarFileEntry(*read_manifest_entry())
            self.__entries.append(entry)

    def close(self):
        self.databuffer.close()    

    closed = property(lambda self: self.databuffer.closed)
        
    def __get_files(self):
        if self.access_mode != "multiple":
            raise StandardError("list of files can only be accessed in multiple mode")
        for entry in self.__entries:
            databuffer = open(self.filename, "rb")
            yield FreeFarFileEntryStream(databuffer, entry.off, entry.length1)

    def __getitem__(self, filename):
        if not filename in self.filenames:
            raise IOError("No such file in FAR file: '" + str(filename) + "'")
        for entry in self.__entries:
            if filename == entry.filename:
                databuffer = open(self.filename, "rb")
                return FreeFarFileEntryStream(databuffer, entry.off, entry.len1)

    def __get_filenames(self):
        for entry in self.__entries:
            yield entry.filename        

    def __iter__(self):
        return self.__get_files()

    def __len__(self):
        return len(self.__entries)

    filenames = property(__get_filenames)
    files = property(__get_files)

# Tests

import os.path
import functools
import pdb
import random

official_gamedta_relpath = "TheSims_official_gamedata"

#Testdata
class KnownFarFile(object):
    def __init__(self, filename, contents):
        self.contents = dict(contents)
        self.filename = filename 

    def get_any_filename(self):
        return random.choice(list(self.contents.keys()))

    def get_file_size(self, filename):
        return self.contents[filename][0]
        
known_far_file = KnownFarFile(os.path.join(official_gamedta_relpath, "GameData/Global.far"), 
                 [('PhoneGlobals.iff', (41728, 41728, 16)),
                  ('PersonGlobals.iff', (118356, 118356, 41744)),
                  ('ArtGlobals.iff', (2048, 2048, 160100)),
                  ('CounterGlobals.iff', (12732, 12732, 162148)),
                  ('DoorGlobals.iff', (424, 424, 174880)),
                  ('LevelGlobals.iff', (1129, 1129, 175304)),
                  ('LightGlobals.iff', (3070, 3070, 176433)),
                  ('RentalClerkGlobals.iff', (236262, 236262, 179503)),
                  ('RentalShackGlobals.iff', (25978, 25978, 415765)),
                  ('SalesClerkGlobals.iff', (178265, 178265, 441743)),
                  ('SocialGlobals.iff', (22452, 22452, 620008)),
                  ('SofaGlobals.iff', (29514, 29514, 642460)),
                  ('VacationCarnieGlobals.iff', (147542, 147542, 671974)),
                  ('VacationDirectorGlobals.iff', (149629, 149629, 819516)),
                  ('VacationMascotGlobals.iff', (148920, 148920, 969145)),
                  ('WaiterGlobals.iff', (180204, 180204, 1118065)),
                  ('CarGlobals.iff', (6574, 6574, 1298269)),
                  ('Global.iff', (111003, 111003, 1304843))])

def requires_known_farfile(testfunc):
    @functools.wraps(testfunc)
    def test_decorated():
        testfunc(known_far_file=known_far_file)
    return test_decorated

from nose.tools import assert_raises

def test_invalid_filename():
    assert_raises(IOError, FarFile, "invalidfilename")

def test_empty_file():
    #TODO: Test is Unix-specific
    assert_raises(IOError, FarFile, "/dev/null")

@requires_known_farfile
def test_real_dta_create_fileobj(known_far_file):
    farfile = FarFile(known_far_file.filename)
    assert len(farfile) > 0
    assert known_far_file.get_any_filename() in list(farfile.filenames) 

@requires_known_farfile
def test_open_stream(known_far_file):
    farfile = FarFile(known_far_file.filename)
    fname = known_far_file.get_any_filename()
    strm = farfile[fname]
    strm.seek(known_far_file.get_file_size(fname))
    pos1 = strm.tell()
    strm.seek(known_far_file.get_file_size(fname), SEEK_SET)
    pos2 = strm.tell()
    assert pos1 == pos2
    strm.seek(-known_far_file.get_file_size(fname), SEEK_END)
    print(strm.tell())
    assert strm.tell() == 0
    strm.seek(known_far_file.get_file_size(fname), SEEK_CUR)
    strm.seek(-known_far_file.get_file_size(fname), SEEK_CUR)
    assert strm.tell() == 0

@requires_known_farfile
def test_open_multiple_streams(known_far_file):
    farfile = FarFile(known_far_file.filename)
    fname = known_far_file.get_any_filename()
    strm1 = farfile[fname]
    strm2 = farfile[fname]
    data1 = strm1.read()
    data2 = strm2.read()
    assert data1 == data2
    strm1.seek(-1, SEEK_CUR)
    assert strm1.tell()+1 == strm2.tell()

