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
Access to FAR files

FAR files are archives of various data files, often IFF archives themselves
http://simtech.sourceforge.net/tech/far.html
'''

import struct

from .subfile import SubFile as FreeFarFileEntryStream

class FarFile(object):
    '''
    Represents a FAR file

    During object creation, the content is indexed. The interface
    then allows for read-only access of individual entries via
    a file-like object.

    This is the base class which is agnostic whether we operate on a
    physical FAR file or just some data stream.

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

    def _create_stream(self):
        '''
        Has to be provided by the derived classes.
        For accessing a physical file, this simply opens another
        file stream. For accessing a data stream, this could reposition
        the file pointer or something like that...
        '''
        raise StandardError("implementation missing!")

    def __init__(self, databuffer):
        '''
        @param databuffer open stream containing the FAR file and nothing more!

        NOTE: The stream is not closed

        TODO: implement write access
        '''

        self.__entries = []

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
            #print(filename, file_len1, file_len2, file_off)
            return (filename, file_off, file_len1, file_len2)

        databuffer.seek(manifest_offset)
        num_entries, = struct.unpack("<I", databuffer.read(4))
        for i in range(num_entries):
            entry = FarFile.FarFileEntry(*read_manifest_entry())
            self.__entries.append(entry)

    def open(self, filename, stream):
        '''
        @param stream open Stream which contains the complete FAR file and nothing more! This stream is repositioned and returned
                      to point to the file entry.

        NOTE: It is not checked whether the stream is actually equivalent to the one the FAR file object was created with
        '''
        if not filename in self.filenames:
            raise IOError("No such file in FAR file: '" + str(filename) + "'")
        for entry in self.__entries:
            if filename == entry.filename:
                return FreeFarFileEntryStream(stream, entry.off, entry.len1)

    def __get_filenames(self):
        for entry in self.__entries:
            yield entry.filename

    def __len__(self):
        return len(self.__entries)

    filenames = property(__get_filenames)

from os.path import join

def extract_far(stream, output_path):
    '''
    Creates file for every far entry in output_path
    '''
    ff = FarFile(stream)
    for filename in ff.filenames:
        entrystream = ff.open(filename, stream)
        with open(join(output_path, filename), "wb") as fp:
            fp.write(entrystream.read())

#Command-line utility
if __name__ == "__main__":
    import sys

    def do_list(args):
        ff = FarFile(args.instream)
        for filename in ff.filenames:
            print(filename)

    def do_cat(args):
        ff = FarFile(args.instream)
        if args.filename not in ff.filenames:
            print("ERROR -- %s not found in %s" % (args.filename, ff.filenames))
            raise SystemExit(1)
        stream = ff.open(args.filename, args.instream)
        sys.stdout.buffer.write(stream.read())

    import argparse

    parser = argparse.ArgumentParser(prog='far')
    subparsers = parser.add_subparsers(help='sub-command help')

    parser_list = subparsers.add_parser('list', help='list files in FAR archive (expected from stdin)')
    parser_list.set_defaults(func=do_list)

    parser_extract = subparsers.add_parser('cat', help='cat file from FAR archive (expected from stdin) to stdout')
    parser_extract.add_argument('filename', type=str, help='filename in FAR archive')
    parser_extract.set_defaults(func=do_cat)

    args = parser.parse_args()

    if sys.stdin.buffer.seekable():
        args.instream = sys.stdin.buffer
    else:
        #Because stdin is not seekable, we have to buffer it
        buf = sys.stdin.buffer.read(2000000000) #2gb limit
        args.instream = io.BytesIO(buf)

    args.func(args)

#Testcode

from .gamedata_for_tests import requires_known_farfile
from io import SEEK_SET, SEEK_CUR, SEEK_END

try:
    from nose.tools import assert_raises

    def test_empty_file():
        #TODO: Test is Unix-specific
        assert_raises(IOError, FarFile, open("/dev/null", "rb"))

    @requires_known_farfile
    def test_real_dta_create_fileobj(known_far_file):
        farfile = FarFile(open(known_far_file.filename, "rb"))
        assert len(farfile) > 0
        assert known_far_file.get_any_filename() in list(farfile.filenames)

    @requires_known_farfile
    def test_open_stream(known_far_file):
        farfile = FarFile(open(known_far_file.filename, "rb"))
        fname = known_far_file.get_any_filename()
        strm = farfile.open(fname, open(known_far_file.filename, "rb"))
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
        farfile = FarFile(open(known_far_file.filename, "rb"))
        fname = known_far_file.get_any_filename()
        strm1 = farfile.open(fname, open(known_far_file.filename, "rb"))
        strm2 = farfile.open(fname, open(known_far_file.filename, "rb"))
        data1 = strm1.read()
        data2 = strm2.read()
        assert data1 == data2
        strm1.seek(-1, SEEK_CUR)
        assert strm1.tell()+1 == strm2.tell()

except ImportError:
    pass
