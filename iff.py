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

import logging

logger = logging.getLogger("pysim.iff")

class IffResourceHeader(object):
    '''
    Represents an entry in an IFF file
    '''
    def __init__(self, typecode, size, resid, flags, name):
        '''
        stream must point to the beginning of the Resource!
        '''
        assert type(typecode) == bytes
        
        self.typecode = typecode
        self.size = size
        self.resid = resid
        self.flags = flags
        self.name = name
        
def read_resource_header_from_stream(stream):
    typecode = stream.read(4)        
    size, resid, flags = struct.unpack(">IHH", stream.read(8))
    namestr = stream.read(64)
    return IffResourceHeader(typecode, size, resid, flags, namestr.decode('ascii'))
    
class IffResourceTypeListEntry(object):
    def __init__(self, offset, rid, flags, name):
        self.offset = offset
        self.rid = rid
        self.flags = flags
        self.name = name
        
def read_resource_typelistentry(stream, version):
    assert version == 1 or version == 0
    if version == 0:
        unpack_str = "<IHH"        
    else:
        unpack_str = "<IHI"        
    dta = stream.read(struct.calcsize(unpack_str))    
    offset, resid, flags = struct.unpack(unpack_str, dta)
    
    if version == 0: #-> zero-terminated string
        namestr = stream.read(1)       
        while namestr[-1] != 0:
            namestr += stream.read(1)
        if stream.tell() % 2 != 0:
            stream.read(1) #padding
    else: #->Pascal-style string
        length = struct.unpack("B", stream.read(1))
        namestr = stream.read(length)
        if stream.tell() % 2 != 0:
            stream.read(1) #padding
        
    logger.debug("read ResourceMap TypeListeEntry offset=%s, id=%s, flags=%s, name='%s'", offset, resid, flags, namestr.decode('ascii'))
    
    return IffResourceTypeListEntry(offset, resid, flags, namestr.decode('ascii'))
    
def read_resource_typelist(stream, version):
    typecode = stream.read(4)    
    num_entries, = struct.unpack("<I", stream.read(4))    
    logger.debug("read ResourceTypeList typecode='%s', num_entries=%s", typecode, num_entries)
    return typecode, [read_resource_typelistentry(stream, version) for i in range(num_entries)]
    
def read_resource_map_from_stream(stream):
    '''    
    '''
    unknown, version = struct.unpack("<II", stream.read(8))
    typecode = stream.read(4)    
    assert typecode == b'pmsr'
    size, num_entries = struct.unpack("<II", stream.read(8))    
    assert num_entries < 100000 #recognize utterly wrong value...
    
    logger.debug("read ResourceMap typecode='%s', version=%s, size=%s, num_entries=%s", typecode, version, size, num_entries)
    
    return [read_resource_typelist(stream, version) for i in range(num_entries)]        

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

        min_signature_size = 60
        data = stream.read(min_signature_size)
        signature_a, rest = chop_next_string(data)
       
        signature_a_pattern = b"IFF FILE ([0-9].[0-9]):TYPE FOLLOWED BY SIZE"
        match = re.search(signature_a_pattern, signature_a)
        if match == None:
            raise IOError("IFF signature is missing, propably not an IFF file")                
        version = match.group(1)
        
        #In the original game files, versions 2.0 and 2.5 can be found
        if version == b"2.5":   
            logger.debug("IFF file has version 2.5")         
            signature_b = rest[0:25]
            signature_b_pattern = b" JAMIE DOORNBOS & MAXIS 1"            
            if signature_b != signature_b_pattern:
                raise IOError("IFF file 2.5, but signature part 2 is wrong")
                        
            manifest_offset, = struct.unpack(">I", stream.read(4))
            if manifest_offset != 0: #if == 0, no resource map is present
                #read manifest
                stream.seek(manifest_offset, SEEK_SET)
                resmapheader = read_resource_header_from_stream(stream)
                if resmapheader.typecode != b'rsmp':
                    raise IOError("Expected typecode 'rsmp', found '%s'" % resmapheader.typecode)
                self.resource_map = dict(read_resource_map_from_stream(stream))
            else:
                self.resource_map = None                
                    
        elif version == b"2.0":
            logger.debug("IFF file has version 2.5")
            signature_b = rest[0:25] + stream.read(4)
            signature_b_pattern = b" JAMIE DOORNBOS & MAXIS 1996"
            if signature_b != signature_b_pattern:
                raise IOError("IFF file 2.0, but signature part 2 is wrong")
            raise StandardError("unimplemented")
        else:
            raise IOError("Unsupported IFF file version %s" % version)
            
        def access_resource(self, predicate):
            pass

#Testdata

from nose.tools import assert_raises

import os

ifffile = IffFile(open(os.path.join("TheSims_official_gamedata", "UserData2", "Characters", "User00000.iff"), "rb"))

