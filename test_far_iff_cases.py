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

from .skn_bmf import read_deformablemesh_from_stream
from .cmx_bcf import read_characterdata_from_datastream
from .cfp import read_animdta_from_cfp_stream
from .datastream import BinaryDataStream

def test_smoketest_maid_iff_file():
    stream = open(gamedata_for_tests.objects_far_filename, "rb")
    farfile = FarFile(stream)
    maid_stream = farfile.open("People\\maid.iff", stream)
    ifffile = IffFile(maid_stream)
    for entry in ifffile.iter_open(lambda header: True, maid_stream):
        print(entry)

def test_smoketest_bones_iff_file():
    stream = open(gamedata_for_tests.objects_far_filename, "rb")
    farfile = FarFile(stream)
    bones_stream = farfile.open("People\\Bones.iff", stream)
    ifffile = IffFile(bones_stream)
    for entry in ifffile.iter_open(lambda header: True, bones_stream):
        print(entry)

def test_smoketest_bmf_file_from_far_archive():
    stream = open(gamedata_for_tests.animation_far_filename, "rb")
    farfile = FarFile(stream)
    bmf_stream = farfile.open("xskin-b006fafat_01-PELVIS-BODY.bmf", stream)
    mesh = read_deformablemesh_from_stream(BinaryDataStream(bmf_stream))
    assert len(mesh.faces) == 538

def test_smoketest_bcf_file_for_adult_skeleton():
    stream = open(gamedata_for_tests.animation_far_filename, "rb")
    farfile = FarFile(stream)
    bcf_stream = farfile.open("adult-skeleton.cmx.bcf", stream)
    obj = read_characterdata_from_datastream(BinaryDataStream(bcf_stream))
    assert len(obj.sceletons) == 1

def test_smoketest_cfp_file_for_sink_wash_dishes_start():
    stream = open(gamedata_for_tests.animation_far_filename, "rb")
    farfile = FarFile(stream)
    cfp_stream = farfile.open("xskill-a2o-sink-washdishes-start.cfp", stream)
    obj = read_animdta_from_cfp_stream(cfp_stream, 48, 48, 48, 696, 696, 696, 696)

def test_smoketest_cfp_file_for_sink_wash_dishes_loop():
    stream = open(gamedata_for_tests.animation_far_filename, "rb")
    farfile = FarFile(stream)
    cfp_stream = farfile.open("xskill-a2o-sink-washdishes-loop.cfp", stream)
    obj = read_animdta_from_cfp_stream(cfp_stream, 48, 48, 48, 696, 696, 696, 696)

def test_smoketest_cfp_file_for_sink_wash_dishes_stop():
    stream = open(gamedata_for_tests.animation_far_filename, "rb")
    farfile = FarFile(stream)
    cfp_stream = farfile.open("xskill-a2o-sink-washdishes-stop.cfp", stream)
    obj = read_animdta_from_cfp_stream(cfp_stream, 48, 48, 48, 696, 696, 696, 696)
