"""Procedural Blender build for the Fisherman Dad review package ("Steal a Dad!").

Source of truth: FishermanDad_Illustrated_MasterPrompt (owner's master prompt, 33 sections).
Primary reference: reference/FishermanDad_Reference_Crop.png (unchanged).

Frames / units
--------------
1 Blender unit = 1 Roblox stud (scene scale_length 0.01).
Logical (X, D, H): X<0 = anatomical RIGHT (free hand), X>0 = anatomical LEFT (rod hand, bucket side),
D<0 = front, H up, soles at H=0.  Blender (x, y, z) = (X, D, H).
FBX export axis_forward='Z', axis_up='Y' (project mapping): Roblox position of logical (X,D,H) = (-X, H, D).

The left arm is built directly in the HoldRod pose (rest == pose); the neutral bind joints are stored in the data files.

Run headless:
    blender -b --factory-startup --python build_fisherman_dad.py -- <output_dir> [--quick] [--norender]
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

# palette: master prompt section 06 (tiles 0..48, six HEX digits each); atlas 256 x 256, 8 x 8 tiles of 32 px
PAL = [
    ('SKIN', '#F2A06B', 'Лицо, шея, руки'),
    ('SKIN_LIGHT', '#FFBF88', 'Широкие верхние грани кожи'),
    ('SKIN_SHADOW', '#C77D4F', 'Уши/нижние плоскости'),
    ('NOSE', '#EE8D56', 'Тёплый крупный нос'),
    ('SHIRT', '#E6B341', 'Жёлтая рубашка'),
    ('SHIRT_LIGHT', '#F4C758', 'Плечи/воротник/верхние грани'),
    ('SHIRT_SHADOW', '#B88429', 'Манжеты и подмышки'),
    ('SHIRT_SEAM', '#A97424', 'Планка и редкие швы'),
    ('VEST', '#65703A', 'Оливковый жилет'),
    ('VEST_LIGHT', '#7D8547', 'Верх клапанов и полей панамы'),
    ('VEST_DARK', '#444D29', 'Боковые грани карманов/лента панамы'),
    ('VEST_SEAM', '#394022', 'Тонкие швы'),
    ('PANTS', '#5B6335', 'Брюки'),
    ('PANTS_LIGHT', '#707A42', 'Широкие фасеты брюк'),
    ('PANTS_DARK', '#3D4428', 'Внутренние стороны/швы'),
    ('CUFF', '#889052', 'Узкий край отворота'),
    ('BOOT', '#424A2D', 'Резиновые сапоги'),
    ('BOOT_LIGHT', '#5A6340', 'Верх носка и голенище'),
    ('BOOT_SOLE', '#2D3423', 'Подошва'),
    ('HAIR', '#A6A29A', 'Седые волосы и усы'),
    ('HAIR_LIGHT', '#C7C3BA', 'Верхние пучки усов'),
    ('HAIR_SHADOW', '#7E7E79', 'Между пучками/затылок'),
    ('BROW', '#3B3025', 'Брови'),
    ('EYE_WHITE', '#FFF7E5', 'Белки'),
    ('IRIS', '#4E3821', 'Радужка'),
    ('PUPIL', '#151819', 'Зрачок'),
    ('TEETH', '#FFF7DE', 'Верхняя полоса зубов'),
    ('MOUTH', '#6D3828', 'Полость улыбки'),
    ('LIP', '#BF774C', 'Нижний край улыбки'),
    ('BELT', '#272923', 'Ремень'),
    ('SILVER', '#AEB7B6', 'Пряжка и мелкая фурнитура'),
    ('SILVER_LIGHT', '#D4D9D5', 'Светлые грани металла'),
    ('BUTTON', '#D5B04D', 'Пуговицы и кнопки'),
    ('ROD', '#222427', 'Удилище'),
    ('ROD_LIGHT', '#454848', 'Фасеты/обоймы'),
    ('REEL', '#191D1F', 'Корпус катушки'),
    ('REEL_LIGHT', '#343A3D', 'Грани корпуса катушки'),
    ('GOLD', '#CF9B31', 'Шпуля'),
    ('GOLD_LIGHT', '#EDC253', 'Верх шпули'),
    ('CORK', '#A36B2B', 'Пробковая рукоять'),
    ('CORK_LIGHT', '#C38D43', 'Широкие светлые грани пробки'),
    ('CORK_DARK', '#795021', 'Несколько крупных отметин пробки'),
    ('LINE', '#C2D471', 'Леска и нижний стержень поплавка'),
    ('FLOAT_RED', '#E94F24', 'Красные зоны поплавка/приманка'),
    ('FLOAT_WHITE', '#FFF3D9', 'Светлая полоса поплавка'),
    ('BUCKET', '#406C84', 'Ведро'),
    ('BUCKET_LIGHT', '#5E8BA1', 'Светлая сторона/обод'),
    ('BUCKET_DARK', '#274C62', 'Внутренние стенки и низ ведра'),
    ('WIRE', '#A7B2B3', 'Дужка ведра/скоба катушки'),
]
TILE = {n: i for i, (n, _, _) in enumerate(PAL)}
ATLAS_W, ATLAS_H, TILE_PX, COLS = 256, 256, 32, 8
INSET = 6
