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

import io
from io import SEEK_SET, SEEK_CUR, SEEK_END

class SubFile(io.IOBase):
    '''
    Provides a read-only file-like bytes stream
    to a subrange in side a given stream

    If for a given stream there exist multiple SubFile instanes,
    there's the possibility that they issue read operations in
    parallel (not in a multithreading sense but in the way that
    instance A does some reading and before it's finished, instance B
    does some reading). To prevent errors originating from this, we
    -if necessary- reposition the stream pointer before any read operation
    '''
    def __init__(self, stream, off, length):
        io.IOBase.__init__(self)
        self.stream = stream
        #reposition stream
        self.stream.seek(off)
        self.off = off
        self.length = length
        self.end = off + length #offset of byte behind end of file
        self.last_readpos = self.off #used reposition stream before any read operation

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

    def read(self, readlen=-1):
        pos = self.stream.tell()
        if pos != self.last_readpos: #reposition
            self.stream.seek(self.last_readpos)
            pos = self.last_readpos
        if readlen == -1: #read the rest available
            result = self.stream.read(self.end-pos)
        else:
            result = self.stream.read(min(self.end-pos, readlen))
        self.last_readpos = self.stream.tell()
        return result

    #...Interesting: If I include this close routine, the stream is
    #automatically closed as soon as the object is destroyed. Python
    #obviously auto-calls "close" on destruction
    #def close(self):
    #    self.stream.close()

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
        if pos != self.last_readpos: #reposition
            self.stream.seek(self.last_readpos)
            pos = self.last_readpos
        if size == -1:
            size = self.length
        size = min(size, self.end - pos)
        result = self.stream.readline(size)
        self.last_readpos = self.stream.tell()
        return result

    def readlines(self, hint=-1):
        pos = self.stream.tell()
        if pos != self.last_readpos: #reposition
            self.stream.seek(self.last_readpos)
            pos = self.last_readpos
        if hint == -1:
            hint = self.length
        hint = min(hint, self.end - pos)
        result = self.stream.readlines(hint)
        self.last_readpos = self.stream.tell()
        return result

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
        self.last_readpos = self.stream.tell()

    def seekable(self):
        return self.stream.seekable()

    def tell(self):
        return self.last_readpos - self.off
        #return self.stream.tell() - self.off

    def writable(self):
        return False
