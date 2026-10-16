"""Procedural Blender build for the Grill Dad review package ("Steal a Dad!").

Source of truth: GrillDad_MasterPrompt_RU_UTF8.txt (34 sections) + GrillDad_Construction_Spec.json.
Primary reference: reference/GrillDad_Reference_Crop.png (416 x 382, unchanged).

Frames / units
--------------
1 Blender unit = 1 Roblox stud (scene scale_length 0.01).
Logical (X, D, H): X<0 = anatomical RIGHT (free hand, towel), X>0 = anatomical LEFT (tongs hand),
D<0 = front, H up, soles at H=0.  Blender (x, y, z) = (X, D, H).
FBX export axis_forward='Z', axis_up='Y' (project mapping): Roblox position of logical (X,D,H) = (-X, H, D).

The left arm is built directly in the HoldTongs pose (rest == pose); neutral bind joints are stored in the data files.

Run headless:
    blender -b --factory-startup --python build_grill_dad.py -- <output_dir> [--quick] [--norender]
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
OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else os.path.dirname(os.path.abspath(__file__))
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

# palette: master prompt section 06 (tiles 0..43), atlas 256 x 256, 8 x 8 tiles of 32 px, rest filled with APRON
PAL = [
    ('SKIN', '#F2A16E', 'tile 0'),
    ('SKIN_LIGHT', '#FFBC89', 'tile 1'),
    ('SKIN_SHADOW', '#CC7D50', 'tile 2'),
    ('NOSE', '#EF8A61', 'tile 3'),
    ('SHIRT', '#C6252C', 'tile 4'),
    ('SHIRT_LIGHT', '#E64442', 'tile 5'),
    ('SHIRT_DARK', '#951B24', 'tile 6'),
    ('SHIRT_SEAM', '#AF2029', 'tile 7'),
    ('APRON', '#29272B', 'tile 8'),
    ('APRON_LIGHT', '#38353A', 'tile 9'),
    ('APRON_DARK', '#1F1E22', 'tile 10'),
    ('APRON_SEAM', '#454047', 'tile 11'),
    ('STAIN', '#51443F', 'tile 12'),
    ('STAIN_LIGHT', '#605047', 'tile 13'),
    ('STAIN_DARK', '#403737', 'tile 14'),
    ('PANTS', '#242328', 'tile 15'),
    ('PANTS_LIGHT', '#343238', 'tile 16'),
    ('PANTS_DARK', '#19191E', 'tile 17'),
    ('SHOE', '#222126', 'tile 18'),
    ('SHOE_LIGHT', '#39363C', 'tile 19'),
    ('SOLE', '#151519', 'tile 20'),
    ('HAIR', '#242026', 'tile 21'),
    ('HAIR_LIGHT', '#373037', 'tile 22'),
    ('HAIR_DARK', '#17161B', 'tile 23'),
    ('BROW', '#252126', 'tile 24'),
    ('EYE_WHITE', '#FFF2DD', 'tile 25'),
    ('PUPIL', '#151516', 'tile 26'),
    ('IRIS', '#4A3930', 'tile 27'),
    ('MOUTH', '#63362A', 'tile 28'),
    ('LIP', '#CF815B', 'tile 29'),
    ('GOLD', '#DBAC3C', 'tile 30'),
    ('GOLD_LIGHT', '#F4D064', 'tile 31'),
    ('GOLD_DARK', '#9D7126', 'tile 32'),
    ('TOWEL', '#F3EADD', 'tile 33'),
    ('TOWEL_LIGHT', '#FFF9ED', 'tile 34'),
    ('TOWEL_SHADOW', '#CFC5B7', 'tile 35'),
    ('TOWEL_RED', '#C93532', 'tile 36'),
    ('WOOD', '#71431F', 'tile 37'),
    ('WOOD_LIGHT', '#925D2D', 'tile 38'),
    ('WOOD_DARK', '#492B18', 'tile 39'),
    ('STEEL', '#92929D', 'tile 40'),
    ('STEEL_LIGHT', '#C4C4CA', 'tile 41'),
    ('STEEL_DARK', '#656571', 'tile 42'),
    ('STEEL_EDGE', '#E0DDE1', 'tile 43'),
]
TILE = {n: i for i, (n, _, _) in enumerate(PAL)}
ATLAS_W, ATLAS_H, TILE_PX, COLS = 256, 256, 32, 8
INSET = 6
