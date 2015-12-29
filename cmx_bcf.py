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
Access to BCF and CMX files

CMX files contain definitions of characters. BCF files are
compressed versions of CMX files. Where CMX files contains
ASCII strings for numbers, the CMX files contain binary-coded
integers and floats.
Because the basic structure is identical, we use the same
functions and the same classes to represent both file types. The
difference is in how we read in basic numbers and strings. For the
CMX variant, we read and interpret lines of text, for the BCF variant,
we read in blocks of 4 bytes.

Also see
http://www.donhopkins.com/drupal/node/19
http://www.donhopkins.com/drupal/node/20
http://www.donhopkins.com/drupal/node/21
for additional details of the sceleton description in The Sims™
'''

from .datastream import TextDataStream, BinaryDataStream

import struct

class simplereprobject(object):
    '''
    Mixin for generic repr
    '''
    def __repr__(self):
        return type(self).__qualname__ + "(**" + repr(vars(self)) + ")"

class CharacterData(simplereprobject):
    '''
    Describes content of a bcf/cmx file
    '''
    def __init__(self, sceletons, suits, skills):
        self.sceletons = sceletons
        self.suits = suits
        self.skills = skills

    class Skill(simplereprobject):
        def __init__(self, name, ani_name, duration, distance, move_flag, num_pos, num_rot, motions):
            self.name = name
            self.ani_name = ani_name        # basename of the animation file containing all keyframes
            self.duration = duration        # if played in normal speed, propably given in milliseconds?
            self.distance = distance        # the distance a walking loop should travel forward
            self.move_flag = move_flag      # tell if it's moving (like a walking loop)
            self.num_pos = num_pos          # number of positions in animation file
            self.num_rot = num_rot          # number of rotations in animation file
            self.motions = motions          # list of motions

    class Motion(simplereprobject):
        def __init__(self, bone_name, num_frames, duration, pos_used, rot_used, pos_off, rot_off, props, timelines):
            self.bone_name = bone_name      # bone which is animated in this motion
            self.num_frames = num_frames    # how many (key?)frames the animation consists of
            self.duration = duration        # it seems this is always identical to the duration value of the Skill object this Motion belongs to
            self.pos_used = pos_used        # flag if position is animated (if 0, pos_off == -1)
            self.rot_used = rot_used        # flag if rotation is animated (if 0, rot_off == -1)
            self.pos_off = pos_off          # offset into animation file of skill
            self.rot_off = rot_off          # offset into animation file of skill
            self.props = props              # assuming here, that unknown integer describes property list
            self.timelines = timelines

    class Sceleton(simplereprobject):
        def __init__(self, name, bones):
            self.name = name                # name of sceleton. In TheSims there are only 4 sceletons present: adult, child, dog, kat
            self.bones = bones              # list of bones

    class Bone(simplereprobject):
        '''
        Quote from http://www.donhopkins.com/drupal/node/19
            Each Bone inherits its parent's coordinate system, then adds its translation followed by its rotation, to calculate the coordinate system in which the skins are rendered, then passes that transformation on to its children.
        '''
        def __init__(self, name, parent_name, props, pos, quat, can_trans, can_rot, suits_can_blend, wiggle_value, wiggle_power):
            self.name = name                # name of bone
            self.parent_name = parent_name
            self.props = props
            self.pos = pos                  # position of bone: list [x,y,z]
            self.quat = quat                # rotation quaternion of bone: list [w,x,y,z]
            self.can_trans = can_trans      # if bone is allowed to be translated
            self.can_rot = can_rot          # if bone is allowed to be rotated
            self.suits_can_blend = suits_can_blend #whether bone allows to blend multiple animations
            #wiggle properties are leftovers from an attempt to use perlin noise to introduce randomness into animations
            self.wiggle_value = wiggle_value
            self.wiggle_power = wiggle_power

    class Suit(simplereprobject):
        '''
        Used to attach meshes (+textures) to a sceleton. Normally at least the body mesh is attached as a skin, but
        there can be additional accessoires attached to the sceleton.

        Quote from http://simtech.sourceforge.net/tech/bcf.html:
            Originally, skins were wrapped around a single bone, so to wrap the entire body, a suit would
            normally specify a list of skins covering most of the bones.  With the advent of deformable meshes,
            skins needed to attach to more than one bone, so bone names are now specified in the mesh itself.
            (Each mesh is suspended in space relative to the bone(s) and is then draped with the texture.)

            Although the suit is still used to attach a whole-body skin, the suit is now primarily used to attach accessories.
            Multiple accessories may be attached to the same bone (for example, adding both a clown hat and a clown nose to the head)
            or accessories may be attached to different bones (for example, adding a dust pan to one hand and a brush to the other).
            Some special effects are done by attaching and detaching skins (the roach can may or may not have spray, but the skin for
            the can is unchanged).  Presumably, all of these can be mixed-and-matched in any combination.
        '''
        def __init__(self, name, stype, skins, props):
            self.name = name
            self.stype = stype              # integer denoting type of skin. Only value 0 and 1 are used in TheSims.
                                            #   0 - normal suit
                                            #   1 - censorship (relation with censor_flag in skin not clear)
            self.skins = skins              # list of skins
            self.props = props

    class Skin(simplereprobject):
        '''
        Binds a deformable mesh to a sceleton. For accessoires, this can be understood as
        binding a rigid acessoire (like a pipe) to a single bone
        '''
        def __init__(self, bone_name, skin_name, censor_flag, props):
            self.bone_name = bone_name      # not used anymore. leftover from time where TheSims game engine could only animate segmented rigid body parts (no deformable mesh)
                                            # but according to http://www.donhopkins.com/drupal/node/19 the bone name still has to be validly set in order for the game to correctly load the skin
            self.skin_name = skin_name      # basename of the file containing the actual deformable mesh description (a SKN or BMF format file)
            self.censor_flag = censor_flag  # is this a real skin or a bounding box used to draw the pixelation over a nude character?
            self.props = props #assuming here, that unknown integer describes property list

def read_characterdata_from_stream(stream):
    '''
    @arg stream file-like object

    This routine automatically determines whether this is a cmx stream (text) or a bcf stream
    '''
    def read_sublist(stream):
        '''
        @arg stream DataStream
        Property sublist as in http://simtech.sourceforge.net/tech/bcf.html
        '''
        num_props = stream.read_int()
        props = []
        for i in range(num_props):
            prop_name  = stream.read_str()
            prop_value = stream.read_str()
            props.append((prop_name, prop_value))
        return props

    def read_proplist(stream):
        '''
        @param stream DataStream
        The property list as in http://simtech.sourceforge.net/tech/bcf.html
        '''

        num_sublists = stream.read_int()
        sublists = []
        for i in range(num_sublists):
            sublists.append(read_sublist(stream))
        return sublists

    def read_sceleton(stream):
        '''
        @param stream DataStream
        '''
        def read_bone(stream):
            '''
            @param stream DataStream
            '''
            name = stream.read_str()
            parent_name = stream.read_str()
            props = read_proplist(stream)
            x,y,z = stream.read_floats(3)
            pos = x,y,z
            w,x,y,z = stream.read_floats(4)
            quat = w,x,y,z
            can_trans = stream.read_int()
            can_rot = stream.read_int()
            can_blend = stream.read_int()
            wiggle_value = stream.read_float()
            wiggle_power = stream.read_float()
            return CharacterData.Bone(name, parent_name, props, pos, quat, can_trans, can_rot, can_blend, wiggle_value, wiggle_power)

        name = stream.read_str()
        num_bones = stream.read_int()
        bones = []
        for i in range(num_bones):
            bones.append(read_bone(stream))
        return CharacterData.Sceleton(name, bones)

    #We don't know yet if the stream contains cmx or bcf data. And because
    #we don't want to impose the requirement that the stream is random-access,
    #we will now read the first 4 bytes. Cmx file always start with 2 lines
    #   // Character File. Copyright 1997, Maxis Inc.
    #   version 300
    first4bytes = stream.read(4)
    if first4bytes ==  b'// C':
        #TextStream
        stream = TextDataStream(stream, skip_lines=2, seq_delim='|')
        num_sceletons = stream.read_int()
    else:
        #BinaryStream
        stream = BinaryDataStream(stream)
        num_sceletons = struct.unpack("<I", first4bytes)[0]

    #Sceletons
    assert num_sceletons < 100 #sanity check (if this is not a cmx file, we will proprably get something absurd here)
    sceletons = []
    for i in range(num_sceletons):
        sceletons.append(read_sceleton(stream))

    def read_suit(stream):
        '''
        @param stream DataStream
        @return Suit object
        '''
        def read_skin(stream):
            '''
            @param stream DataStream
            @return Skin object
            '''
            bone_name = stream.read_str()
            skin_name = stream.read_str()
            censor_flag = stream.read_int()
            props = read_proplist(stream) #assuming here, that unknown integer describes property list
            return CharacterData.Skin(bone_name, skin_name, censor_flag, props)

        name = stream.read_str()
        stype = stream.read_int()
        props = read_proplist(stream) #assuming here, that unknown integer describes property list
        num_skins = stream.read_int()
        skins = []
        for i in range(num_skins):
            skins.append(read_skin(stream))
        return CharacterData.Suit(name, stype, skins, props)

    #Suits
    num_suits = stream.read_int()
    suits = []
    for i in range(num_suits):
        suits.append(read_suit(stream))

    def read_skill(stream):
        '''
        @param stream DataStream
        @return Skill object
        '''
        def read_motion(stream):
            '''
            @param stream DataStream
            @return Motion object
            '''
            def read_timeline(stream):
                '''
                @param stream DataStream
                @return [(<time>, <events>), (<time>, <events>), ...]
                '''
                def read_moment(stream):
                    '''
                    @param stream DataStream
                    @return tuple(<time>, <list of events>)
                    Quote from http://www.donhopkins.com/drupal/node/19 concerning the possible events:

                        xevt event sends numeric argument to animate primitive false branch.
                        interruptable and interruptible events set practice interruptable flag.
                        anchor event on bone anchors that bone.
                        dress event dresses named suit on skeleton.
                        undress event undresses named suit from skeleton.
                        lefthand event sets left hand to integer argument.
                        righthand event sets right hand to integer argument.
                        censor event sets censorship mask.
                        sound event plays named sound.
                        selectedsound event plays named sound if character is selected.
                        delselectedsound event plays named sound if character is not selected.
                        footstep event plays footstep, integer argument tells if left or right, but is ignored.
                        discontinuity event tells us to expect a snap in root location or rotation, so kill the last practice and don't blend.

                    '''
                    time = stream.read_int()
                    events = read_sublist(stream)
                    return (time, events)

                #we deviate from term 'timelist' used in http://simtech.sourceforge.net/tech/bcf.html
                #and call it a 'moment' here, because it is a collection of events for a given point in time
                num_moments = stream.read_int()
                moments = []
                for i in range(num_moments):
                    moments.append(read_moment(stream))
                return moments

            bone_name  = stream.read_str()
            num_frames = stream.read_int()
            duration   = stream.read_float()
            pos_used   = stream.read_int()
            rot_used   = stream.read_int()
            pos_off    = stream.read_int()
            rot_off    = stream.read_int()
            props      = read_proplist(stream)
            #we deviate from term 'timeprop' used in http://simtech.sourceforge.net/tech/bcf.html
            #and call it a 'time line' here, because it is a sequence of 'moments'
            num_timelines = stream.read_int()
            timelines = []
            for i in range(num_timelines):
                timelines.append(read_timeline(stream))
            return CharacterData.Motion(bone_name, num_frames, duration, pos_used != 0, rot_used != 0, pos_off, rot_off, props, timelines)

        skill_name  = stream.read_str()
        ani_name    = stream.read_str()
        duration    = stream.read_float()
        distance    = stream.read_float()
        move_flag   = stream.read_int()
        num_pos     = stream.read_int()
        num_rot     = stream.read_int()
        num_motions = stream.read_int()
        motions = []
        for i in range(num_motions):
            motions.append(read_motion(stream))
        return CharacterData.Skill(skill_name, ani_name, duration, distance, move_flag, num_pos, num_rot, motions)

    #Skills
    num_skills = stream.read_int()
    skills = []
    for i in range(num_skills):
        skills.append(read_skill(stream))

    return CharacterData(sceletons, suits, skills)

#Command-line utility
if __name__ == "__main__":
    import sys
    from pprint import pprint

    def do_list(args):
        cdta = read_characterdata_from_stream(args.instream)
        print("Skeletons:")
        for skeleton in cdta.sceletons:
            print("  " + skeleton.name)
            for bone in skeleton.bones:
                print("    " + bone.name)
        print("Suits:")
        for suit in cdta.suits:
            print("  " + suit.name)
            for skin in suit.skins:
                print("    " + skin.skin_name)
        print("Skills:")
        for skill in cdta.skills:
            print("  " + skill.name)

    import argparse

    parser = argparse.ArgumentParser(prog='far')
    subparsers = parser.add_subparsers(help='sub-command help')

    parser_list = subparsers.add_parser('list', help='list data in cmx/bcf file (expected from stdin)')
    parser_list.set_defaults(func=do_list)

    args = parser.parse_args()

    #We do not require random-access to input stream here,
    #so we just use stdin directly!
    args.instream = sys.stdin.buffer

    args.func(args)

# Testcode

from .gamedata_for_tests import official_gamedta_relpath
import os.path
from pprint import pprint

def test_read_female_wizard_cmx():
    known_filename = os.path.join(official_gamedta_relpath, "GameData", "Skins", "B013FCChd_wizd.cmx")
    known_file = CharacterData([], [CharacterData.Suit("b013fcchd_wizd", 0, [   CharacterData.Skin("PELVIS", "xskin-b013fcchd_wizd-PELVIS-BODY", 0, 0),
                                                                                CharacterData.Skin("PELVIS", "xskin-b013fcchd_wizd-PELVIS-CAPE", 0, 0)], [])], [])
    chardta = read_characterdata_from_datastream(TextDataStream(open(known_filename, "rb"), skip_lines=2))
    assert type(chardta) == CharacterData
    assert pprint(chardta.sceletons) == pprint(known_file.sceletons)
    assert pprint(chardta.suits)     == pprint(known_file.suits)
    assert pprint(chardta.skills)    == pprint(known_file.skills)

