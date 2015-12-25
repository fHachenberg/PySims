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
Access to IFF files

IFF files are archives of various data files related to each other
See http://simtech.sourceforge.net/tech/iff.html
'''

import re
import struct
from itertools import chain
from io import SEEK_SET, SEEK_END, SEEK_CUR, BytesIO

from .subfile import SubFile

import logging

logger = logging.getLogger("pysim.iff")

class NoMatchingIffResourceFound(IOError):
    def __init__(self):
        IOError.__init__(self, "no matching IFF resource found")

class IffResourceHeader(object):
    '''
    Header for an entry in an IFF file.
    In an IFF file the header is immediately followed by the actual
    resource content
    '''
    def __init__(self, typecode, size, resid, flags, name):
        '''
        stream must point to the beginning of the Resource!
        '''

        self.typecode = typecode
        self.size = size            #Total length header + content
        self.resid = resid
        self.flags = flags
        self.name = name

    length = 76 #Headers have a fixed length of 76 byte

def read_resource_header_from_stream(stream):
    '''
    Creates an IffResourceHeader object from data read from stream
    '''
    typecode_buf = stream.read(4) #In Resource headers, Typecode is encoded as Little-Endian 4byte int. Inside type lists and the resource map, Big-endian is used instead!
    typecode = typecode_buf.decode('ascii')
    size, resid, flags = struct.unpack(">IHH", stream.read(8))
    namebuf = stream.read(64)
    #name string is 64 bytes long at most. If shorter, it is
    #null-terminated. We have to manually cut the byte sequence
    #there, else we will "import" those zeros into the final string
    namestr = namebuf.decode('ascii').rstrip('\0')

    logger.debug("read ResourceHeader typecode=%s, size=%s, id=%d, flags=%s, name='%s'", typecode, size, resid, flags, namestr)

    return IffResourceHeader(typecode, size, resid, flags, namestr)

class IffResourceTypeListEntry(object):
    '''
    Resource maps allow for quickly locating resources. For each resource, almost the same information as
    given inside the resource's header is provided. Exception: Instead of the size of the resource, the offset inside
    the IFF file is given. Therefore we can not equal actual ResourceHeaders with TypeListEntries, though they share almost
    all properties.
    '''
    def __init__(self, typecode, offset, resid, flags, name):
        self.typecode = typecode        #Typecode is not actually explicitely defined in the type list entries in an IFF file but it is
                                        #the same for all entries of one type list. But for efficiency of implementation we use a flat
                                        #list of entries instead of a list of type lists
        self.offset = offset            #Offset of resource entry from start of file
        self.resid = resid              #ID of resource
        self.flags = flags              #flags of resource
        self.name = name                #name of resource

def read_pascal_style_string(stream):
    length = struct.unpack("B", stream.read(1))[0]
    namestr = stream.read(length)
    return namestr

def read_zero_zerminated_string(stream):
    namestr = stream.read(1)
    while namestr[-1] != 0:
        namestr += stream.read(1)
    return namestr

def read_resource_typelist_entry(stream, typecode, version):
    assert version == 1 or version == 0
    if version == 0:
        unpack_str = "<IHH"
    else:
        unpack_str = "<IHI"
    dta = stream.read(struct.calcsize(unpack_str))
    offset, resid, flags = struct.unpack(unpack_str, dta)

    if version == 0: #-> zero-terminated string
        namestr = read_zero_zerminated_string(stream)
    else: #->Pascal-style string
        namestr = read_pascal_style_string(stream)

    padded_debug_str = ""
    logger.debug("%s, %s", stream.tell(), stream.tell() % 2)
    if len(namestr)  % 2 != 0:
        stream.read(1) #padding
        padded_debug_str = "(+1 padding-byte)"

    logger.debug("read ResourceTypeListEntry offset=%s, id=%s, flags=%s, name='%s' %s", offset, resid, flags, namestr.decode('ascii', 'replace'), padded_debug_str)

    return IffResourceTypeListEntry(typecode, offset, resid, flags, namestr.decode('ascii', 'replace'))

def read_resource_typelist(stream, version):
    '''
    Reads list of resource entries of specific type from stream
    @return flat list of resource map entries
    '''
    typecode_buf = struct.pack('<I', struct.unpack('>I', stream.read(4))[0]) #pack-unpack-maneuver is done to switch big-endian typecode into human-readable order
    typecode = typecode_buf.decode('ascii')
    num_entries, = struct.unpack("<I", stream.read(4))
    logger.debug("read ResourceTypeList typecode='%s', num_entries=%s", typecode, num_entries)
    return [read_resource_typelist_entry(stream, typecode, version) for i in range(num_entries)]

def read_resource_map_from_stream(stream):
    '''
    Resource Maps allow for quickly locating resources in an IFF file
    by caching the relevant infos of the resource headers.

    Reads the content of the resource map resource from IFF file
    @return flat list of resource map entries
    '''
    unknown, version = struct.unpack("<II", stream.read(8))
    typecode_buf = struct.pack('<I', struct.unpack('>I', stream.read(4))[0]) #pack-unpack-maneuver is done to switch big-endian typecode into human-readable order
    typecode = typecode_buf.decode('ascii')
    assert typecode == 'rsmp' #"rsmp" means "Resource Map"
    size, num_types = struct.unpack("<II", stream.read(8))
    assert num_types < 100000 #sanity check

    logger.debug("read ResourceMap typecode=%s, version=%s, size=%s, num_types=%s", typecode, version, size, num_types)

    #read_resource_typelist returns list of entries each, so we flatten them into
    #one single list of entries
    gen_of_typelists = (read_resource_typelist(stream, version) for i in range(num_types))
    return list(chain.from_iterable(gen_of_typelists))

class IffFile(object):
    '''
    Represents an IFF file, allows access to individual resource entries.

    Requires an open stream to operate!
    '''

    def __init__(self, stream):
        '''
        @param stream Stream containing the complete IFF file.

        The stream object is NOT stored in the IffFile object
        '''

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
            rsmp_offset, = struct.unpack(">I", stream.read(4))
        elif version == b"2.0":
            logger.debug("IFF file has version 2.0")
            signature_b = rest[0:25] + stream.read(3)
            signature_b_pattern = b" JAMIE DOORNBOS & MAXIS 1996"
            if signature_b != signature_b_pattern:
                raise IOError("IFF file 2.0, but signature part 2 is wrong")
            rsmp_offset = 0
            #skip padding byte
            stream.read(1)
        else:
            raise IOError("Unsupported IFF file version %s" % version)

        self.start = stream.tell() #Where the resource entries start
        if rsmp_offset != 0: #if == 0, no resource map is present
            #read resource map
            logger.debug("Resource map present in IFF file")
            stream.seek(rsmp_offset, SEEK_SET)
            resmapheader = read_resource_header_from_stream(stream)
            if resmapheader.typecode != 'rsmp':
                raise IOError("Expected typecode 'rsmp', found '%s'" % resmapheader.typecode)
            self.resource_map = read_resource_map_from_stream(stream)
        else:
            logger.debug("No resource map present in IFF file")
            self.resource_map = None

    def glob(self, stream):
        '''
        Finds and reads GLOB resource. There can be at most one GLOB resource
        per IFF file. For that reason and because it contains meta-like data,
        we provide a central access routine.

        @return semi-global string or None, if no GLOB resource is available in IFF file
        '''
        def read_glob_from_stream(stream):
            '''
            An IFF file can specify a single semi-global file (GLOB resource), containing common items
            used by files in that IFF file.

            See http://simtech.sourceforge.net/tech/glob.html

            @param stream GLOB resource stream pointing to point before header of GLOB resource
            '''
            #Flavor of GLOB content string is not known previously. We use the
            #following routine: If string contains a null char, we assume it's
            #a zero-terminated string. Else if first character has value < 32,
            #we assume that this is a pascal-style string. Finally, in any other case we
            #interpret it as a raw string
            header = read_resource_header_from_stream(stream)
            #read content of GLOB resource
            data = stream.read(header.size - IffResourceHeader.length)
            if data.find(b'\0') != -1:
                logger.debug("Assuming GLOB resource contains zero-terminated string")
                #assume zero-terminated string
                semiglobal_buf = read_zero_zerminated_string(BytesIO(data))
            elif data[0] < 32:
                logger.debug("Assuming GLOB resource contains pascal-style string")
                #assume pascal-style string
                semiglobal_buf = read_pascal_style_string(BytesIO(data))
            else:
                logger.debug("Assuming GLOB resource contains raw string")
                #assume raw string
                semiglobal_buf = data

            return semiglobal_buf.decode('ascii')

        try:
            globfile = self.open(lambda header: header.typecode == "GLOB", stream)
        except NoMatchingIffResourceFound:
            return None
        return read_glob_from_stream(globfile)

    def open(self, predicate, stream):
        '''
        @return file-like object accessing resource data (including resource header)
        @param predicate a function expecting an object having the following properties:
                          *name
                          *id
                          *flags
                          *typecode
                         and returning either True or False
                         The first match is returned as specified above
        @param stream open Stream which contains the complete IFF file and nothing more! This stream is repositioned
                      and returned to the beginning of the IFF resource content
        '''
        try:
            return next(self.iter_open(predicate, stream))
        except StopIteration:
            raise NoMatchingIffResourceFound()

    def iter_open(self, predicate, stream):
        '''
        Works like open but does find all matches for predicate.
        Opens each with the same stream
        '''

        #If a resource map is present, we first search in there
        rsmp_matches = []   #we remember the matches we found in the resource map so
                            #we can skip them while we traverse the other resources
                            #manually...
        if self.resource_map != None:
            for entry in self.resource_map:
                assert not stream.closed #User must not close the stream during yield
                if predicate(entry) == True:
                    #read header of entry to determine size
                    stream.seek(entry.offset)
                    header = read_resource_header_from_stream(stream)
                    rsmp_matches.append(entry.offset)
                    newsfile = SubFile(stream, entry.offset, header.size)
                    yield newsfile

        #Now we try to manually find the resource by iterating
        #over the actual resource headers (slow due to file access)

        #determine length of IFF file
        stream.seek(0, SEEK_END)
        end_of_file_off = stream.tell()
        #run through all entries until we reach end_of_file_off
        stream.seek(self.start, SEEK_SET)
        while stream.tell() < end_of_file_off:
            assert not stream.closed #User must not close the stream during yield
            resstart = stream.tell()
            header = read_resource_header_from_stream(stream)
            if resstart in rsmp_matches: #resource was yielded already from resource map search
                stream.seek(resstart+header.size, SEEK_SET) #skip
                continue
            elif predicate(header) == True:
                yield SubFile(stream, resstart, header.size)
            stream.seek(resstart+header.size, SEEK_SET) #jump to next resource entry

        raise StopIteration

from os.path import join

def extract_iff(stream, output_path):
    '''
    Creates file for every iff entry in output_path
    '''
    ff = IffFile(stream)
    for entrystream in ff.iter_open(lambda p: True, stream):
        header = read_resource_header_from_stream(entrystream)
        if header.name == "":
            filename = header.typecode + "_" + str(header.resid)
        else:
            filename = header.name.replace("/","\\")
        with open(join(output_path, filename), "wb") as fp:
            fp.write(entrystream.read())

#Testcode

logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

from .gamedata_for_tests import requires_known_iff_file
import os

try:
    from nose.tools import assert_raises

    @requires_known_iff_file
    def test_read_from_sample_iff_file(known_iff_file):
        ifffile = IffFile(open(known_iff_file.filename, "rb"))
        for bmpfile in ifffile.iter_open(lambda header: header.typecode == 'BMP_', open(known_iff_file.filename, "rb")):
            header = read_resource_header_from_stream(bmpfile)
            #Bitmap files start with "BM"
            dta = bmpfile.read()
            assert dta[0:2] == b'BM'

    def test_maid_iff_file():
        stream = open("PySims/TheSims_official_gamedata/GameData/Objects/Objects.far/People/maid.iff", "rb")
        ifffile = IffFile(stream)
        #for entry in ifffile.iter_open(lambda header: True, stream):
        #    assert entry != None

    @requires_known_iff_file
    def test_compare_header_data_with_reference(known_iff_file):
        stream = open(known_iff_file.filename, "rb")
        ifffile = IffFile(stream)
        #check GLOB resource
        print(ifffile.glob(stream))
        assert known_iff_file.glob == ifffile.glob(stream)

        #iterate over all entries in reference. For each, find matching
        #resource in IFF object, then read its header and check if the size
        #matches with the reference as well
        for e in known_iff_file.contents:
            resfile = ifffile.open(lambda header: e["typecode"] == header.typecode and
                                                  e["id"] == header.resid and
                                                  e["flags"] == header.flags and
                                                  e["name"] == header.name, stream)
            header = read_resource_header_from_stream(resfile)
            assert e['size'] == header.size

    #stream = open(os.path.join("PySims/TheSims_official_gamedata", "UserData2", "Houses", "House00.iff"), "rb")
    #ifffile = IffFile(stream)
    #for bmpfile in ifffile.iter_open(lambda header: True, stream):
    #    pass

except ImportError:
    pass

