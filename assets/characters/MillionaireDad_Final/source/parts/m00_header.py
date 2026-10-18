"""Procedural Blender build for Millionaire Dad (character 08, Legendary) of "Steal a Dad!" - REVIEW model.

Primary appearance authority: source/inputs/Original_Character_Sheet.jpeg (bottom-right character) and its unaltered crop
source/inputs/MillionaireDad_Source_Crop_Unaltered.png (exact crop of the sheet at x1110..1532, y530..955).
The generated concept sheets are NOT evidence; unseen surfaces are simple neutral extrapolation.

Frames / units (same contract as the finished dads)
---------------------------------------------------
Logical (X, F, H): X<0 anatomical RIGHT (case hand), X>0 anatomical LEFT (watch hand), F>0 forward, H up, soles at H=0.
Blender (x, y, z) = (X, -F, H).  FBX export axis_forward='Z', axis_up='Y' puts logical (X,F,H) at Roblox (-X, H, -F): the character faces -Z.
1 Blender unit = 1 stud (scene scale_length 0.01); 6.40 studs is the PROJECT CONVENTION for height, not a reference measurement.

Run headless:
    blender -b --factory-startup --python build_millionaire_dad.py -- <output_dir> [--quick] [--norender] [--preview]
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

# Palette (tile index = order): modelling swatches chosen by eye against the crop (white-lavender suit, black shirt, brass/gold, silver hair),
# NOT measured source colours (the sheet has baked light and shadow).
PALETTE = [
    ("Skin", "#F2B188"), ("SkinLight", "#F8C3A0"), ("SkinShadow", "#D58F68"), ("Nose", "#EE9A78"), ("NoseLight", "#F6AE90"), ("EarInner", "#D58A63"),
    ("Ivory", "#EDE8EC"), ("IvoryLight", "#FBF8FA"), ("IvoryShadow", "#C7C0CA"), ("IvoryDeep", "#9F98A6"),
    ("Shirt", "#26232B"), ("ShirtLight", "#3A3641"), ("ShirtShadow", "#17151B"),
    ("Gold", "#D9A935"), ("GoldLight", "#F3CD5E"), ("GoldShadow", "#A87D1F"), ("Brass", "#C8992B"),
    ("Belt", "#4A3326"), ("BeltLight", "#5E4435"), ("BeltShadow", "#33231A"),
    ("Hair", "#CBCBD3"), ("HairLight", "#E7E7EE"), ("HairShadow", "#A3A3AE"), ("HairGrey", "#8C8C98"), ("HairGreyDark", "#6C6C79"),
    ("Moustache", "#EDEDF3"), ("MoustacheLight", "#FFFFFF"), ("MoustacheShadow", "#BEBEC9"),
    ("Lens", "#121116"), ("LensShine", "#2C2A33"), ("Teeth", "#FFFFFF"), ("TeethShadow", "#D9D9E0"), ("Mouth", "#5E2626"),
    ("ShoeWhite", "#F2EFF2"), ("ShoeLight", "#FFFFFF"), ("ShoeShadow", "#CDC8D0"), ("Sole", "#19181C"), ("SoleLight", "#2B2A30"),
    ("Case", "#1E1D22"), ("CaseLight", "#2F2E35"), ("CaseShadow", "#121115"), ("Strap", "#1E1D22"), ("WatchDial", "#F0E2A8"), ("WatchTick", "#7A5A12"),
]
PAL = [(n, h.upper(), n) for n, h in PALETTE]
TILE = {n: i for i, (n, _, _) in enumerate(PAL)}
ATLAS_W, ATLAS_H, TILE_PX, COLS = 1024, 1024, 128, 8
INSET = 16
assert len(PAL) <= COLS * (ATLAS_H // TILE_PX)
