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

import os.path
import functools
import pdb
import random

official_gamedta_relpath = "TheSims_official_gamedata"

class KnownFarFile(object):
    '''
    HelperClass for testing, represents the a-priori
    knowledge about a Far file against which the code 
    doing the actual reading can be tested.
    '''
    def __init__(self, filename, contents):
        self.contents = dict(contents)
        self.filename = filename 

    def get_any_filename(self):
        return random.choice(list(self.contents.keys()))

    def get_file_size(self, filename):
        return self.contents[filename][0]
        
known_far_file = KnownFarFile(os.path.join(official_gamedta_relpath, "GameData", "Global.far"), 
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
    '''
    Decorator to access known_far_file object
    in test routine
    '''
    @functools.wraps(testfunc)
    def test_decorated():
        testfunc(known_far_file=known_far_file)
    return test_decorated

class KnownIffFile(object):
    '''
    See description of KnownFarFile
    '''
    def __init__(self, filename, headersize, contents):
        self.filename = filename
        self.headersize = headersize
        self.contents = dict(contents)

    def get_any_resource(self):
        filename = random.choice(self.contents.keys())
        assert False
        
known_iff_file = KnownIffFile(os.path.join(official_gamedta_relpath, "UserData2", "Characters", "User00000.iff"), 3553593, 
                              [])

def requires_known_iff_file(testfunc):
    '''
    Decorator to access known_iff_file object
    in test routine
    '''
    @functools.wraps(testfunc)
    def test_decorated():
        testfunc(known_iff_file=known_iff_file)
    return test_decorated
