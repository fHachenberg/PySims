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
compressed versions of SKN files
'''

class DeformableMesh(object):
    '''
    Ad-hoc class to hold meshes described in BMF/SKN files
    '''
    def __init__(   self, filename, texfilename, bones, faces, bonebindings, uvcoords,
                    blenddata, vertices):
        self.filename = filename                #name of the deformable mesh
        self.texfilename = texfilename          #basename of texture file
        self.bones = bones                      #bone indices used
        self.faces = faces                      #3-tuples of indices into the vertices list
        self.bonebindings = bonebindings        #specification which vertices are bound to which bone with a weight of 1.0. bones are denoted by their index in bones list
        self.uvcoords = uvcoords                #uv coordinates for the vertices
        self.blenddata = blenddata              #(optional) weight specification for vertices
        self.vertices = vertices                #vertex coordinates are relative to their primary bone (propably the one they are bound to unblendedly)11

def read_deformablemesh_from_skn_stream(stream):
    '''
    SKN files use DOS-style line breaks (\r\n)

    See http://simtech.sourceforge.net/tech/file_formats_skn.htm
    '''
    lines = stream.read().decode('ascii').split('\r\n')
    filename = lines[0]
    texfilename = lines[1]

    line_bones = 2
    num_bones = int(lines[line_bones])
    assert num_bones >= 0 and num_bones < 1000 #sanity check
    bones = lines[line_bones+1:line_bones+1+num_bones]

    line_faces = line_bones+num_bones+1 #calc line number where face info starts
    num_faces = int(lines[line_faces])
    faces = [[int(v) for v in line.split(" ")] for line in lines[line_faces+1:line_faces+1+num_faces]]

    line_bonebindings = line_faces+num_faces+1
    num_bonebindings = int(lines[line_bonebindings])
    bonebindings = [[int(v) for v in line.split(" ")] for line in lines[line_bonebindings+1:line_bonebindings+1+num_bonebindings]]

    line_uvcoords = line_bonebindings+num_bonebindings+1
    num_uvcoords = int(lines[line_uvcoords])
    uvcoords = [[float(v) for v in line.split(" ")] for line in lines[line_uvcoords+1:line_uvcoords+1+num_uvcoords]]

    line_blenddata = line_uvcoords+num_uvcoords+1
    num_blenddata = int(lines[line_blenddata])
    blenddata = [[int(v) for v in line.split(" ")] for line in lines[line_blenddata+1:line_blenddata+1+num_blenddata]]

    line_vertices = line_blenddata+num_blenddata+1
    num_vertices = int(lines[line_vertices])
    vertices = [[float(v) for v in line.split(" ")] for line in lines[line_vertices+1:line_vertices+1+num_vertices]]

    return DeformableMesh(filename, texfilename, bones, faces, bonebindings, uvcoords, blenddata, vertices)

#Testcode

if __name__ == "__main__":

    import os.path

    skn_filepath = os.path.join("TheSims_official_gamedata", "GameData", "Skins", "xskin-c027fa_germ-HEAD-HEAD.skn")
    with open(skn_filepath, "rb") as f:
        data = read_deformablemesh_from_skn_stream(f)
