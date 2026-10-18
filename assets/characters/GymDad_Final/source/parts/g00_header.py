"""Procedural Blender build for Gym Dad (character 06, Rare) of "Steal a Dad!".

Source: GymDad_MasterPrompt_RU_UTF8.txt + GymDad_Construction_Spec.json (assigned plan, NOT measured geometry),
art reference visuals/GymDad_Original_Poster.jpg (bottom row, second from the left) and visuals/GymDad_Reference_Crop.png.

Frames / units
--------------
Logical (X, F, H): X<0 anatomical RIGHT (dumbbell hand), X>0 LEFT (bag hand), F>0 forward, H up, soles at H=0.
Blender (x, y, z) = (X, -F, H)  (the plan's own mapping).  FBX export axis_forward='Z', axis_up='Y' (project mapping used by
Regular/Office Dad) puts logical (X,F,H) at Roblox (-X, H, -F)... the character faces -Z with its anatomical right on +X.
1 Blender unit = 1 stud (scene scale_length 0.01).

Run headless:
    blender -b --factory-startup --python build_gym_dad.py -- <output_dir> [--quick] [--norender]
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

# palette: master prompt section 05 (order = tile index)
_SPEC_PATH = os.path.join(HERE, "inputs", "GymDad_Construction_Spec.json")
if not os.path.exists(_SPEC_PATH):
    _SPEC_PATH = os.path.join(os.path.dirname(HERE), "inputs", "GymDad_Construction_Spec.json")
PLAN = json.load(open(_SPEC_PATH, encoding="utf8"))
PAL = [(n, h.upper(), n) for n, h in PLAN["palette"].items()]
TILE = {n: i for i, (n, _, _) in enumerate(PAL)}
ATLAS_W, ATLAS_H, TILE_PX, COLS = 1024, 1024, 128, 8
INSET = 16

