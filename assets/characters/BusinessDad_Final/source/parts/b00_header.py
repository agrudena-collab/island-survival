"""Procedural Blender build for Business Dad (character 07, Epic) of "Steal a Dad!" - REVIEW model.

Source: assets/characters/BusinessDad_Review/source/inputs/BusinessDad_Original_Reference.png (bottom row, third character) and the crop
data/BusinessDad_Reference_Crop.png; measured landmarks in data/reference_measurements.json. The turnaround concept sheet is only a planning aid.

Frames / units (same contract as Regular/Office/Gamer/Gym Dad)
--------------------------------------------------------------
Logical (X, F, H): X<0 anatomical RIGHT (pocket hand), X>0 anatomical LEFT (phone hand), F>0 forward, H up, soles at H=0.
Blender (x, y, z) = (X, -F, H).  FBX export axis_forward='Z', axis_up='Y' puts logical (X,F,H) at Roblox (-X, H, -F): the character faces -Z.
1 Blender unit = 1 stud (scene scale_length 0.01).

Run headless:
    blender -b --factory-startup --python build_business_dad.py -- <output_dir> [--quick] [--norender]
"""
import hashlib
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector
from mathutils import geometry as mgeo
from mathutils.bvhtree import BVHTree

V = Vector
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else HERE
QUICK = "--quick" in sys.argv
NORENDER = "--norender" in sys.argv
os.makedirs(os.path.join(OUT, "renders"), exist_ok=True)

for _ob in list(bpy.data.objects):
    bpy.data.objects.remove(_ob, do_unlink=True)
for _blk in (bpy.data.meshes, bpy.data.materials, bpy.data.collections, bpy.data.cameras, bpy.data.lights, bpy.data.images):
    for _it in list(_blk):
        _blk.remove(_it)
SCENE = bpy.context.scene
SCENE.unit_settings.system = 'METRIC'
SCENE.unit_settings.scale_length = 0.01

# Palette (tile index = order). Modelling swatches from the master prompt, checked against the colour sampling sheet
# (data/reference_measurements.json); the reference carries baked light and shadow, so these are NOT measured source colours.
PALETTE = [
    ("Skin", "#F4AD7B"), ("SkinLight", "#F9BE93"), ("SkinShadow", "#D78C60"), ("Nose", "#EA8E69"), ("NoseLight", "#F3A07A"), ("EarInner", "#D58A5E"),
    ("Navy", "#24345E"), ("NavyLight", "#304680"), ("NavyShadow", "#192748"), ("NavyDeep", "#121B35"),
    ("Trouser", "#22315A"), ("TrouserLight", "#2D4072"), ("TrouserShadow", "#172343"),
    ("Shirt", "#F8F4EA"), ("ShirtShadow", "#DAD5C8"),
    ("Tie", "#842F43"), ("TieLight", "#9D4157"), ("TieShadow", "#5F1F31"),
    ("Gold", "#D9A535"), ("GoldLight", "#F2CB62"), ("GoldShadow", "#A87B1F"),
    ("Silver", "#A5A6AA"), ("SilverLight", "#C9CACE"), ("SilverShadow", "#76777C"), ("BeltBlack", "#1D1C21"),
    ("Hair", "#2B2528"), ("HairLight", "#463B3F"), ("HairShadow", "#1B1719"),
    ("HairGrey", "#8D8D93"), ("HairGreyLight", "#B4B4BA"), ("HairGreyShadow", "#68686E"),
    ("Brow", "#1B1A1F"), ("Moustache", "#201F25"), ("MoustacheLight", "#34333C"),
    ("EyeWhite", "#FFFFFF"), ("Pupil", "#14131A"), ("Glint", "#FFFFFF"), ("Mouth", "#6A2B2B"),
    ("Shoe", "#26252C"), ("ShoeLight", "#3F3E47"), ("ShoeTop", "#55545D"), ("ShoeShadow", "#18171C"), ("Sole", "#141318"), ("SoleLight", "#2B2A31"),
    ("PhoneBody", "#18181D"), ("PhoneEdge", "#2D2D36"), ("Lens", "#0A0A0D"), ("LensRing", "#41414B"), ("Flash", "#ECE8D2"),
    ("WatchDial", "#17171B"), ("Button", "#10131F"), ("WatchTick", "#E8C766"),
]
PAL = [(n, h.upper(), n) for n, h in PALETTE]
TILE = {n: i for i, (n, _, _) in enumerate(PAL)}
ATLAS_W, ATLAS_H, TILE_PX, COLS = 1024, 1024, 128, 8
INSET = 16
assert len(PAL) <= COLS * (ATLAS_H // TILE_PX)
