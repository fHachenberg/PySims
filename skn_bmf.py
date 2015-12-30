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
Access to BMF and SKN files

SKN files contain definitions of character skins. BMF files are
compressed versions of SKN files. See datastream.py
'''

from .datastream import TextDataStream, BinaryDataStream

class DeformableMesh(object):
    '''
    Ad-hoc class to hold meshes described in BMF/SKN files
    '''
    def __init__(   self, filename, texfilename, bones, faces, bonebindings, uvcoords,
                    blenddata, vertices):
        self.filename = filename                # name of the deformable mesh
        self.texfilename = texfilename          # basename of texture file
        self.bones = bones                      # bone indices used
        self.faces = faces                      # 3-tuples of indices into the vertices list
        self.bonebindings = bonebindings        # specification which vertices are bound to which bone with a weight of 1.0. bones are denoted by their index in bones list
                                                # Important: The list is sorted for the bone idx. So bonebindings[i] is the binding for the bone of index i
        self.uvcoords = uvcoords                # uv coordinates for the vertices
        self.blenddata = blenddata              # (optional) weight specification for vertices
        self.vertices = vertices                # vertex coordinates are relative to their primary bone (propably the one they are bound to unblendedly)11

def read_deformablemesh_from_stream(stream):
    '''
    @param stream Datastream

    Reads Mesh from SKN/BMF stream.
    Does NOT automatically determine whether this is a text or a binary stream!

    SKN files use DOS-style line breaks (\r\n)

    See http://simtech.sourceforge.net/tech/file_formats_skn.htm
    '''
    filename = stream.read_str()
    texfilename = stream.read_str()

    num_bones = stream.read_int()
    assert num_bones >= 0 and num_bones < 1000 #sanity check
    bones = []
    for i in range(num_bones):
        bones.append(stream.read_str())

    num_faces = stream.read_int()
    faces = []
    for i in range(num_faces):
        faces.append(stream.read_ints(3))

    num_bonebindings = stream.read_int()
    bonebindings = []
    for i in range(num_bonebindings):
        bonebindings.append(stream.read_ints(5))

    num_uvcoords = stream.read_int()
    uvcoords = []
    for i in range(num_uvcoords):
        uvcoords.append(stream.read_floats(2))

    num_blenddata = stream.read_int()
    blenddata = []
    for i in range(num_blenddata):
        blenddata.append(stream.read_ints(2))

    num_vertices = stream.read_int()
    vertices = []
    for i in range(num_vertices):
        vertices.append(stream.read_floats(6))

    return DeformableMesh(filename, texfilename, bones, faces, bonebindings, uvcoords, blenddata, vertices)

#Testcode

import os.path

def test_smoketest_germ_skn():
    skn_filepath = os.path.join("TheSims_official_gamedata", "GameData", "Skins", "xskin-c027fa_germ-HEAD-HEAD.skn")
    with open(skn_filepath, "rb") as f:
        data = read_deformablemesh_from_stream(TextDataStream(f))
