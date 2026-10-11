"""Procedural build script for LakesideCabinHouse ("Steal a Dad!").

A wooden fisherman's-cabin-style family home with its own small lake, pier
and rowboat. Built deliberately different in silhouette from
RegularDadHouse_Final (symmetrical suburban) and OfficeDadHouse_Final
(L-shaped modern): a broad single-volume timber cabin with an OFF-CENTER
gable ridge, a longer roof slope on one side, deep eaves and a wide
lake-facing deck feeding a pier.

Working asset name only -- "LakesideCabinHouse" does not imply a new Dad
character type; no Dad catalog or rarity changes are made here.

Units / orientation
--------------------
1 Blender unit = 1 Roblox stud. Scene unit system is METRIC with
scale_length = 0.01, matching every other house asset in this project.

Asset origin is (0, 0, 0): ground level, centred on the property footprint.
FRONT of the house faces -Y (matching every other house). Ground top
surface is Z = 0. Interior walking surface is also Z = 0 (flush deck/pier).

Logical-to-Blender coordinate contract (see manifest.json "orientation"):
    Blender_X = logical X (left/right, unchanged)
    Blender_Y = logical D - 24   (D = depth from front boundary toward lake;
                                   D=0 front boundary -> Y=-24;
                                   D=48 lake boundary -> Y=+24)
    Blender_Z = logical H (height above the common walking surface)

Run headless:
    blender -b --factory-startup --python build_lakeside_cabin_house.py -- <output_dir>
"""

import json
import math
import os
import sys

import bmesh
import bpy
import mathutils

# --------------------------------------------------------------------------
# 0. Logical layout constants (studs) -- taken directly from the owner's
#    master prompt, in LOGICAL (X, D, H) space. D_TO_Y converts D -> Y.
# --------------------------------------------------------------------------

D_OFFSET = 24.0


def Y(d):
    """Convert logical depth D (0=front boundary, 48=lake boundary) to Blender Y."""
    return d - D_OFFSET


PROP_W, PROP_D = 44.0, 48.0
PROP_X0, PROP_X1 = -PROP_W / 2, PROP_W / 2          # -22 .. 22
PROP_Y0, PROP_Y1 = Y(0.0), Y(48.0)                  # -24 .. 24

WALL_T = 0.45
FLOOR_T = 0.35

# Main cabin footprint
CAB_X0, CAB_X1 = -15.0, 15.0                        # 30 wide
CAB_D0, CAB_D1 = 4.0, 28.0                          # 24 deep
CAB_Y0, CAB_Y1 = Y(CAB_D0), Y(CAB_D1)               # -20 .. 4
CAB_IN_X0, CAB_IN_X1 = CAB_X0 + WALL_T, CAB_X1 - WALL_T
CAB_IN_Y0, CAB_IN_Y1 = CAB_Y0 + WALL_T, CAB_Y1 - WALL_T

WALL_H = 11.5
RIDGE_X = -3.0
RIDGE_H = 16.8
ROOF_T = 0.4
ROOF_OVH = 1.0                                       # side overhangs
ROOF_D0 = Y(1.2)                                      # front eave line, D=1.2
ROOF_D1 = Y(29.0)                                     # rear overhang line, D=29.0

# Doorways (clear apertures, AFTER frame/leaf -- frame sits outside these)
FRONT_DOOR_X0, FRONT_DOOR_X1 = -4.0, 4.0
FRONT_DOOR_D = 4.0                                    # wall at Y = CAB_Y0
FRONT_DOOR_Y = CAB_Y0
REAR_DOOR_X0, REAR_DOOR_X1 = 4.0, 12.0
REAR_DOOR_D = 28.0
REAR_DOOR_Y = CAB_Y1
DOOR_CLEAR_H = 9.05                                   # small margin above the 9.0 floor so
                                                       # export/import rounding never dips below
                                                       # the required clear height (see Fix C)
DOOR_LEAF_PHI = 94.0                                  # open past 90 for a visible gap

# Windows
FRONT_WIN_Z0, FRONT_WIN_Z1 = 5.7 - 2.0, 5.7 + 2.0     # 4.0 tall, center H=5.7
FRONT_WIN_W = 4.5
FRONT_WIN_XC_L, FRONT_WIN_XC_R = -10.0, 10.0
REAR_WIN_XC = -8.0
REAR_WIN_W, REAR_WIN_H = 7.0, 4.5
REAR_WIN_Z0, REAR_WIN_Z1 = 5.8 - REAR_WIN_H / 2, 5.8 + REAR_WIN_H / 2
SIDE_WIN_W, SIDE_WIN_H = 4.0, 4.0
SIDE_WIN_Z0, SIDE_WIN_Z1 = 4.0, 8.0
SIDE_WIN_YC_L = Y(9.0)                                 # left wall, kitchen area
SIDE_WIN_YC_R = Y(17.0)                                # right wall, fishing corner

# window() casing overhang beyond the clear glass opening -- the sill/head/
# jambs built by window() extend this far past the bare glass width/height,
# coplanar with the solid wall behind them. Every wall cutout MUST widen by
# these same amounts, or the casing ends up partly embedded in solid board
# (z-fighting -- "wall render bleeding over the white trim"). Fix D.
WIN_JAMB_W = 0.3
WIN_SILL_T = 0.25
WIN_HEAD_T = 0.35

# Circulation reservations (manifest only; walls/props are kept clear of these)
LANE_X0, LANE_X1 = -4.0, 4.0
LANE_Y0, LANE_Y1 = CAB_Y0, CAB_Y1                     # -20..4, 8 wide
REAR_TURN_X0, REAR_TURN_X1 = -4.0, 12.0
REAR_TURN_Y0, REAR_TURN_Y1 = Y(20.0), Y(28.0)         # -4..4
DECK_Y0, DECK_Y1 = Y(28.0), Y(36.0)                   # 4..12
BANK_L_X0, BANK_L_X1 = -22.0, -14.0
BANK_R_X0, BANK_R_X1 = 14.0, 22.0
BANK_Y0, BANK_Y1 = Y(36.0), Y(48.0)                   # 12..24
EXIT_L_X0, EXIT_L_X1 = BANK_L_X0, BANK_L_X1
EXIT_R_X0, EXIT_R_X1 = BANK_R_X0, BANK_R_X1

DAD_X0, DAD_X1 = 4.5, 11.5
DAD_Y0, DAD_Y1 = Y(14.0), Y(20.0)                      # -10..-4
DAD_REF = (7.0, Y(17.0), 0.0)                          # (7, -7, 0)

FAM1_REF = (-9.0, Y(10.0), 0.0)                        # (-9, -14, 0) kitchen
FAM2_REF = (-9.0, Y(21.0), 0.0)                        # (-9, -3, 0)  seating
FAM3_REF = (6.3, Y(12.0), 0.0)                         # (6.3, -12, 0) sleeping alcove

# Kitchen zone
KITCH_X0, KITCH_X1 = -14.0, -10.0
KITCH_Y0, KITCH_Y1 = Y(6.0), Y(12.0)                   # -18..-12

# Sleeping alcove
ALC_X0, ALC_X1 = 8.0, 14.0
ALC_Y0, ALC_Y1 = Y(6.0), Y(12.0)                       # -18..-12

# Family table
FTABLE_X, FTABLE_Y = -8.2, Y(15.2)                     # (-8.2, -8.8)

# Stove
STOVE_X, STOVE_Y = -12.0, Y(16.0)                      # (-12, -8)
BENCH_X, BENCH_Y = -9.4, Y(22.0)                       # bench centre, along left wall (-4)

# Fishing workbench
BENCH2_X, BENCH2_Y = 13.2, Y(17.0)                     # (13.2, -7)

# Lake / pier (logical D -> Y)
WATER_X0, WATER_X1 = -13.0, 13.0
WATER_D0, WATER_D1 = 36.5, 47.0
WATER_Y0, WATER_Y1 = Y(WATER_D0), Y(WATER_D1)          # 12.5 .. 23
PIER_X0, PIER_X1 = -4.0, 4.0
PIER_D0, PIER_D1 = 32.0, 44.0
PIER_Y0, PIER_Y1 = Y(PIER_D0), Y(PIER_D1)              # 8 .. 20
PLAT_X0, PLAT_X1 = -6.0, 6.0
PLAT_D0, PLAT_D1 = 42.0, 46.0
PLAT_Y0, PLAT_Y1 = Y(PLAT_D0), Y(PLAT_D1)              # 18 .. 22

OUT_DIR = os.path.abspath(sys.argv[-1]) if "--" in sys.argv else os.path.dirname(__file__)

# --------------------------------------------------------------------------
# Scene / material helpers (same conventions as RegularDadHouse_Final /
# OfficeDadHouse_Final)
# --------------------------------------------------------------------------


def reset_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.collections,
                bpy.data.cameras, bpy.data.lights):
        for item in list(blk):
            blk.remove(item)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 0.01
    return sc


SCENE = reset_scene()

MATERIALS = {}


def mat(name, rgb, rough=0.7, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.2
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = 'BLENDED'
    m.diffuse_color = (*rgb, alpha)
    MATERIALS[name] = (rgb, alpha)
    return m


def srgb_to_linear(rgb255):
    out = []
    for v in rgb255:
        c = v / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


# Palette from the master prompt (sRGB hex -> linear for Blender)
TIMBER_MAIN = mat("LKC_TimberMain", srgb_to_linear((0xA9, 0x79, 0x4F)))
TIMBER_LIGHT = mat("LKC_TimberLight", srgb_to_linear((0xC4, 0x9A, 0x69)))
BEAM_DARK = mat("LKC_BeamDark", srgb_to_linear((0x68, 0x4B, 0x36)))
ROOF_GREEN = mat("LKC_RoofGreen", srgb_to_linear((0x45, 0x6B, 0x59)))
TRIM_PALE = mat("LKC_TrimPale", srgb_to_linear((0xE9, 0xD9, 0xB9)))
LAKE_BLUE = mat("LKC_LakeBlue", srgb_to_linear((0x63, 0xB6, 0xB3)), rough=0.15, alpha=0.78)
SAND = mat("LKC_Sand", srgb_to_linear((0xCA, 0xBB, 0x8D)))
GROUND = mat("LKC_Ground", srgb_to_linear((0x91, 0xAB, 0x78)))
STONE = mat("LKC_Stone", srgb_to_linear((0xA3, 0xAB, 0xA4)))
IRON = mat("LKC_Iron", srgb_to_linear((0x46, 0x53, 0x5A)))
RUST = mat("LKC_Rust", srgb_to_linear((0xB6, 0x67, 0x4E)))
CLOTH_BLUE = mat("LKC_ClothBlue", srgb_to_linear((0x78, 0x9E, 0xAC)))
GLASS = mat("LKC_Glass", (0.74, 0.85, 0.90), rough=0.1, alpha=0.3)
PAPER = mat("LKC_Paper", (0.92, 0.90, 0.85))
FOLIAGE = mat("LKC_Foliage", (0.30, 0.46, 0.33))
BED_WHITE = mat("LKC_BedWhite", (0.90, 0.89, 0.86))

# --------------------------------------------------------------------------
# Collections (section 13 of the prompt)
# --------------------------------------------------------------------------

ROOT = bpy.data.collections.new("LakesideCabinHouse")
SCENE.collection.children.link(ROOT)

GROUPS = {}
for gname in ("Structure", "Roof", "Openings", "Kitchen", "FamilyLiving",
              "SleepingAlcove", "FishingCorner", "Deck", "Pier", "Lake",
              "Yard", "StoryProps", "ReferenceHelpers"):
    c = bpy.data.collections.new(gname)
    ROOT.children.link(c)
    GROUPS[gname] = c

# --------------------------------------------------------------------------
# Geometry helpers -- identical conventions to Regular/OfficeDadHouse
# --------------------------------------------------------------------------

BOX_FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]

OBJECT_MATERIAL = {}
OBJECT_ORDER = []
NONCOLLIDE = set()


def _finish(name, verts, faces, material, coll, loc=(0, 0, 0), rot=None):
    base = name
    n = 1
    while name in OBJECT_MATERIAL:
        n += 1
        name = "%s_dup%d" % (base, n)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    me.materials.append(material)
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    if rot:
        ob.rotation_euler = rot
    coll.objects.link(ob)
    OBJECT_MATERIAL[name] = material.name
    OBJECT_ORDER.append(name)
    return ob


def box(name, xs, ys, zs, material, coll):
    x0, x1 = sorted(xs)
    y0, y1 = sorted(ys)
    z0, z1 = sorted(zs)
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    return _finish(name, v, BOX_FACES, material, coll)


def box_c(name, center, size, material, coll, rot=None):
    sx, sy, sz = (s / 2.0 for s in size)
    v = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
         (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
    return _finish(name, v, BOX_FACES, material, coll, loc=center, rot=rot)


def cyl(name, center, r_bot, r_top, height, material, coll, segs=12, rot=None):
    hz = height / 2.0
    verts, faces = [], []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        verts.append((r_bot * math.cos(a), r_bot * math.sin(a), -hz))
    for i in range(segs):
        a = 2 * math.pi * i / segs
        verts.append((r_top * math.cos(a), r_top * math.sin(a), hz))
    for i in range(segs):
        j = (i + 1) % segs
        faces.append((i, j, j + segs, i + segs))
    faces.append(tuple(range(segs - 1, -1, -1)))
    faces.append(tuple(range(segs, segs * 2)))
    return _finish(name, verts, faces, material, coll, loc=center, rot=rot)


def tri_prism(name, verts, faces, material, coll, loc=(0, 0, 0), rot=None):
    return _finish(name, verts, faces, material, coll, loc=loc, rot=rot)


def bevel(ob, width=0.08, segments=2):
    m = ob.modifiers.new("Bevel", 'BEVEL')
    m.width = width
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(40)
    return ob


def noncollide(ob):
    NONCOLLIDE.add(ob.name)
    return ob


def empty(name, loc, size=1.5):
    o = bpy.data.objects.new(name, None)
    o.empty_display_size = size
    o.empty_display_type = 'PLAIN_AXES'
    o.location = loc
    GROUPS["ReferenceHelpers"].objects.link(o)
    return o


def board_wall(prefix, axis, a0, a1, fixed, z0, z1, coll, board_h=1.0, thick=None):
    """A wall segment built as stacked horizontal board courses, alternating
    the two timber tones, per the owner's 'board courses ... alternated
    between the two wood tones' requirement. axis='X' runs along world X at
    fixed Y; axis='Y' runs along world Y at fixed X. Returns the list of
    created board objects (collidable structural wall -- NOT noncollide)."""
    t = thick if thick is not None else WALL_T
    # Courses sit on ONE global grid (k*board_h, parity-coloured), so every
    # wall segment -- below/above-window pieces and partitions included --
    # lines up course-for-course with its neighbours instead of re-dividing
    # its own height (which produced stepped, mismatched seams).
    k0 = int(math.floor(z0 / board_h + 1e-6))
    k1 = int(math.ceil(z1 / board_h - 1e-6))
    spans = []
    for k in range(k0, k1):
        a, b = max(z0, k * board_h), min(z1, (k + 1) * board_h)
        if b - a > 1e-6:
            spans.append([k, a, b])
    if len(spans) > 1 and spans[-1][2] - spans[-1][1] < 0.3:
        spans[-2][2] = spans[-1][2]       # no thin sliver course at the top
        spans.pop()
    out = []
    for i, (k, zc0, zc1) in enumerate(spans):
        m = TIMBER_LIGHT if k % 2 == 0 else TIMBER_MAIN
        nm = "%s_Board_%02d" % (prefix, i + 1)
        if axis == 'X':
            ob = box(nm, (a0, a1), (fixed - t / 2, fixed + t / 2), (zc0, zc1), m, coll)
        else:
            ob = box(nm, (fixed - t / 2, fixed + t / 2), (a0, a1), (zc0, zc1), m, coll)
        out.append(ob)
    return out


# --------------------------------------------------------------------------
# 1. Structure -- foundation, walls, corner posts (section 7)
# --------------------------------------------------------------------------

S = GROUPS["Structure"]

# Structural deck (below Z=0) + visual floor-board finish strips (above
# ground, at Z=0..floor_finish_t) so there is one solid walkable surface
# with no physical seam in the route.
box("Cabin_Foundation_Slab", (CAB_X0, CAB_X1), (CAB_Y0, CAB_Y1), (-FLOOR_T, 0.0), BEAM_DARK, S)
_FLOOR_T2 = 0.08
_n_strips = 20
for i in range(_n_strips):
    x0 = CAB_X0 + i * (CAB_X1 - CAB_X0) / _n_strips
    x1 = CAB_X0 + (i + 1) * (CAB_X1 - CAB_X0) / _n_strips
    m = TIMBER_MAIN if i % 2 == 0 else TIMBER_LIGHT
    noncollide(box("Cabin_Floor_Strip_%02d" % (i + 1), (x0, x1), (CAB_Y0, CAB_Y1),
                    (0.0, _FLOOR_T2), m, S))
# Short foundation skirt/support visible outside the slab edge (illusion of
# support, no stairs required to reach the flush Z=0 floor)
for _fx in (CAB_X0 + 2.0, CAB_X0 + 10.0, CAB_X1 - 10.0, CAB_X1 - 2.0):
    box("Cabin_Foundation_Skirt_%d" % int(_fx), (_fx - 0.4, _fx + 0.4),
        (CAB_Y0 - 0.3, CAB_Y0 + 0.1), (-FLOOR_T - 0.3, -FLOOR_T), BEAM_DARK, S)

# Corner posts (broad, square, outside the apertures)
_POST = 0.6
for _cx, _cy, _tag in ((CAB_X0, CAB_Y0, "FL"), (CAB_X1, CAB_Y0, "FR"),
                       (CAB_X0, CAB_Y1, "RL"), (CAB_X1, CAB_Y1, "RR")):
    sx = 1 if _cx == CAB_X0 else -1
    sy = 1 if _cy == CAB_Y0 else -1
    box("Cabin_CornerPost_%s" % _tag, (_cx, _cx + sx * _POST),
        (_cy, _cy + sy * _POST), (0.0, WALL_H), BEAM_DARK, S)

# Continuous top beam (wall plate) running the full perimeter
box("Cabin_TopBeam_Front", (CAB_X0, CAB_X1), (CAB_Y0, CAB_Y0 + WALL_T),
    (WALL_H, WALL_H + 0.5), BEAM_DARK, S)
box("Cabin_TopBeam_Rear", (CAB_X0, CAB_X1), (CAB_Y1 - WALL_T, CAB_Y1),
    (WALL_H, WALL_H + 0.5), BEAM_DARK, S)
box("Cabin_TopBeam_Left", (CAB_X0, CAB_X0 + WALL_T), (CAB_Y0, CAB_Y1),
    (WALL_H, WALL_H + 0.5), BEAM_DARK, S)
box("Cabin_TopBeam_Right", (CAB_X1 - WALL_T, CAB_X1), (CAB_Y0, CAB_Y1),
    (WALL_H, WALL_H + 0.5), BEAM_DARK, S)

# Front wall: two segments flanking the front door, each FURTHER split
# around its own window -- the baseline only split the front/rear walls
# around the DOOR (unlike the left/right walls, which were correctly split
# around their SIDE windows with an A/B/C/D below/above pattern). That left
# the front windows and the rear window built flush against, and hidden
# behind, a solid uncut board wall. Apply the same below/above technique
# used for the side walls here too.
# Each wall cutout below is widened by WIN_JAMB_W beyond the bare glass
# width, and the below/above Z-bands stop short by WIN_SILL_T/WIN_HEAD_T,
# so the window casing (sill/head/jambs) lands entirely inside the open
# gap instead of overlapping the solid wall boards next to it (Fix D: the
# casing previously extended WIN_JAMB_W/SILL_T/HEAD_T past a cutout sized
# to the glass alone, so it was coplanar with -- and z-fought against --
# the solid board on either side).
_DJT = 0.35   # door jamb width (see door_frame): walls stop at the jamb instead of running behind it
_fw_l_x0, _fw_l_x1 = CAB_X0 + _POST, FRONT_DOOR_X0 - _DJT
_fwl_win_x0 = FRONT_WIN_XC_L - FRONT_WIN_W / 2 - WIN_JAMB_W
_fwl_win_x1 = FRONT_WIN_XC_L + FRONT_WIN_W / 2 + WIN_JAMB_W
board_wall("Cabin_Wall_Front_L1", 'X', _fw_l_x0, _fwl_win_x0, CAB_Y0, 0.0, WALL_H, S)
board_wall("Cabin_Wall_Front_L_Below", 'X', _fwl_win_x0, _fwl_win_x1, CAB_Y0, 0.0, FRONT_WIN_Z0 - WIN_SILL_T, S)
board_wall("Cabin_Wall_Front_L_Above", 'X', _fwl_win_x0, _fwl_win_x1, CAB_Y0, FRONT_WIN_Z1 + WIN_HEAD_T, WALL_H, S)
board_wall("Cabin_Wall_Front_L2", 'X', _fwl_win_x1, _fw_l_x1, CAB_Y0, 0.0, WALL_H, S)

_fw_r_x0, _fw_r_x1 = FRONT_DOOR_X1 + _DJT, CAB_X1 - _POST
_fwr_win_x0 = FRONT_WIN_XC_R - FRONT_WIN_W / 2 - WIN_JAMB_W
_fwr_win_x1 = FRONT_WIN_XC_R + FRONT_WIN_W / 2 + WIN_JAMB_W
board_wall("Cabin_Wall_Front_R1", 'X', _fw_r_x0, _fwr_win_x0, CAB_Y0, 0.0, WALL_H, S)
board_wall("Cabin_Wall_Front_R_Below", 'X', _fwr_win_x0, _fwr_win_x1, CAB_Y0, 0.0, FRONT_WIN_Z0 - WIN_SILL_T, S)
board_wall("Cabin_Wall_Front_R_Above", 'X', _fwr_win_x0, _fwr_win_x1, CAB_Y0, FRONT_WIN_Z1 + WIN_HEAD_T, WALL_H, S)
board_wall("Cabin_Wall_Front_R2", 'X', _fwr_win_x1, _fw_r_x1, CAB_Y0, 0.0, WALL_H, S)
# Lintel above the front door (outside the clear height)
box("Cabin_Wall_Front_DoorHead", (FRONT_DOOR_X0, FRONT_DOOR_X1), (CAB_Y0, CAB_Y0 + WALL_T),
    (DOOR_CLEAR_H, WALL_H), BEAM_DARK, S)

# Rear wall: two segments flanking the rear door; the left one is further
# split around the rear picture window (same reasoning as the front wall).
_rw_l_x0, _rw_l_x1 = CAB_X0 + _POST, REAR_DOOR_X0 - _DJT
_rwl_win_x0 = REAR_WIN_XC - REAR_WIN_W / 2 - WIN_JAMB_W
_rwl_win_x1 = REAR_WIN_XC + REAR_WIN_W / 2 + WIN_JAMB_W
board_wall("Cabin_Wall_Rear_L1", 'X', _rw_l_x0, _rwl_win_x0, CAB_Y1, 0.0, WALL_H, S)
board_wall("Cabin_Wall_Rear_L_Below", 'X', _rwl_win_x0, _rwl_win_x1, CAB_Y1, 0.0, REAR_WIN_Z0 - WIN_SILL_T, S)
board_wall("Cabin_Wall_Rear_L_Above", 'X', _rwl_win_x0, _rwl_win_x1, CAB_Y1, REAR_WIN_Z1 + WIN_HEAD_T, WALL_H, S)
board_wall("Cabin_Wall_Rear_L2", 'X', _rwl_win_x1, _rw_l_x1, CAB_Y1, 0.0, WALL_H, S)
board_wall("Cabin_Wall_Rear_R", 'X', REAR_DOOR_X1 + _DJT, CAB_X1 - _POST, CAB_Y1, 0.0, WALL_H, S)
box("Cabin_Wall_Rear_DoorHead", (REAR_DOOR_X0, REAR_DOOR_X1), (CAB_Y1 - WALL_T, CAB_Y1),
    (DOOR_CLEAR_H, WALL_H), BEAM_DARK, S)

# Left wall (kitchen side): below/above the side window band, widened the
# same way as the front/rear cutouts above.
_lw_win_y0 = SIDE_WIN_YC_L - SIDE_WIN_W / 2 - WIN_JAMB_W
_lw_win_y1 = SIDE_WIN_YC_L + SIDE_WIN_W / 2 + WIN_JAMB_W
board_wall("Cabin_Wall_Left_A", 'Y', CAB_Y0 + _POST, _lw_win_y0, CAB_X0, 0.0, WALL_H, S)
board_wall("Cabin_Wall_Left_B", 'Y', _lw_win_y0, _lw_win_y1, CAB_X0, 0.0, SIDE_WIN_Z0 - WIN_SILL_T, S)
board_wall("Cabin_Wall_Left_C", 'Y', _lw_win_y0, _lw_win_y1, CAB_X0, SIDE_WIN_Z1 + WIN_HEAD_T, WALL_H, S)
board_wall("Cabin_Wall_Left_D", 'Y', _lw_win_y1, CAB_Y1 - _POST, CAB_X0, 0.0, WALL_H, S)

# Right wall (fishing-corner side)
_rtw_win_y0 = SIDE_WIN_YC_R - SIDE_WIN_W / 2 - WIN_JAMB_W
_rtw_win_y1 = SIDE_WIN_YC_R + SIDE_WIN_W / 2 + WIN_JAMB_W
board_wall("Cabin_Wall_Right_A", 'Y', CAB_Y0 + _POST, _rtw_win_y0, CAB_X1, 0.0, WALL_H, S)
board_wall("Cabin_Wall_Right_B", 'Y', _rtw_win_y0, _rtw_win_y1, CAB_X1, 0.0, SIDE_WIN_Z0 - WIN_SILL_T, S)
board_wall("Cabin_Wall_Right_C", 'Y', _rtw_win_y0, _rtw_win_y1, CAB_X1, SIDE_WIN_Z1 + WIN_HEAD_T, WALL_H, S)
board_wall("Cabin_Wall_Right_D", 'Y', _rtw_win_y1, CAB_Y1 - _POST, CAB_X1, 0.0, WALL_H, S)

# --------------------------------------------------------------------------
# 2. Gable + roof (section 7.4, 7.6)
# --------------------------------------------------------------------------

R = GROUPS["Roof"]

# Gable end-frame triangles (front and rear), exposed chunky members, clear
# of required passage headroom (door clear height 9.0 << wall_h 11.5)
_GM = 0.4


def gable_frame(tag, y_center):
    # Bottom chord (wall-plate level), two rafters to ridge, ridge post
    box("Gable_%s_BottomChord" % tag, (CAB_X0, CAB_X1), (y_center - _GM / 2, y_center + _GM / 2),
        (WALL_H, WALL_H + _GM), BEAM_DARK, R)
    # left rafter: from (CAB_X0, WALL_H) to (RIDGE_X, RIDGE_H)
    _rafter("Gable_%s_RafterL" % tag, CAB_X0, WALL_H, RIDGE_X, RIDGE_H, y_center, R)
    _rafter("Gable_%s_RafterR" % tag, RIDGE_X, RIDGE_H, CAB_X1, WALL_H, y_center, R)
    box("Gable_%s_RidgePost" % tag, (RIDGE_X - _GM / 2, RIDGE_X + _GM / 2),
        (y_center - _GM / 2, y_center + _GM / 2), (WALL_H, RIDGE_H), BEAM_DARK, R)
    # Thin infill panel under each rafter (triangular gable wall), modest
    _gable_infill("Gable_%s_InfillL" % tag, CAB_X0, RIDGE_X, WALL_H, RIDGE_H, y_center, R)
    _gable_infill("Gable_%s_InfillR" % tag, RIDGE_X, CAB_X1, WALL_H, RIDGE_H, y_center, R)


def _rafter(name, x0, z0, x1, z1, yc, coll):
    length = math.hypot(x1 - x0, z1 - z0)
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    ang = math.atan2(z1 - z0, x1 - x0)
    sx, sy, sz = length, _GM, _GM
    v = [(-sx / 2, -sy / 2, -sz / 2), (sx / 2, -sy / 2, -sz / 2),
         (sx / 2, sy / 2, -sz / 2), (-sx / 2, sy / 2, -sz / 2),
         (-sx / 2, -sy / 2, sz / 2), (sx / 2, -sy / 2, sz / 2),
         (sx / 2, sy / 2, sz / 2), (-sx / 2, sy / 2, sz / 2)]
    return _finish(name, v, BOX_FACES, BEAM_DARK, coll, loc=(cx, yc, cz), rot=(0, -ang, 0))


def _gable_infill(name, xa, xb, za, zb, yc, coll):
    x0, x1 = sorted((xa, xb))
    v = [(x0, -0.08, za), (x1, -0.08, za), (x1, -0.08, zb if x1 == RIDGE_X else za),
         (x0, -0.08, za),
         (x0, 0.08, za), (x1, 0.08, za), (x1, 0.08, zb if x1 == RIDGE_X else za),
         (x0, 0.08, za)]
    # Build as a simple triangular wedge (two verts coincide at the ridge end)
    if xb == RIDGE_X or xa == RIDGE_X:
        ridge_is_b = (xb == RIDGE_X)
        low_x = xa if ridge_is_b else xb
        v = [(low_x, -0.08, za), (RIDGE_X, -0.08, za), (RIDGE_X, -0.08, zb),
             (low_x, 0.08, za), (RIDGE_X, 0.08, za), (RIDGE_X, 0.08, zb)]
        faces = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
        return noncollide(_finish(name, v, faces, TIMBER_MAIN, coll, loc=(0, yc, 0)))


gable_frame("Front", CAB_Y0 + WALL_T / 2)
gable_frame("Rear", CAB_Y1 - WALL_T / 2)

# Roof planes: two sloping boxes meeting at the ridge, one noticeably
# longer span than the other (the asymmetric silhouette requirement)
_ROOF_RUN_L = RIDGE_X - (CAB_X0 - ROOF_OVH)            # ~12.7
_ROOF_RUN_R = (CAB_X1 + ROOF_OVH) - RIDGE_X            # ~18.7
_ROOF_RISE = RIDGE_H - WALL_H


def roof_plane(name, x_low, x_high, rise_sign, coll):
    run = x_high - x_low
    length = math.hypot(run, _ROOF_RISE)
    ang = math.atan2(_ROOF_RISE, run) * rise_sign
    depth = ROOF_D1 - ROOF_D0
    cx = (x_low + x_high) / 2
    cz = WALL_H + (RIDGE_H - WALL_H) / 2
    cy = (ROOF_D0 + ROOF_D1) / 2
    sx, sy, sz = length, depth, ROOF_T
    v = [(-sx / 2, -sy / 2, -sz / 2), (sx / 2, -sy / 2, -sz / 2),
         (sx / 2, sy / 2, -sz / 2), (-sx / 2, sy / 2, -sz / 2),
         (-sx / 2, -sy / 2, sz / 2), (sx / 2, -sy / 2, sz / 2),
         (sx / 2, sy / 2, sz / 2), (-sx / 2, sy / 2, sz / 2)]
    return _finish(name, v, BOX_FACES, ROOF_GREEN, coll, loc=(cx, cy, cz), rot=(0, -ang, 0))


roof_plane("Roof_Left", CAB_X0 - ROOF_OVH, RIDGE_X, 1, R)
roof_plane("Roof_Right", RIDGE_X, CAB_X1 + ROOF_OVH, -1, R)


def roof_seam(tag, idx, x_low, x_high, rise_sign, frac, coll):
    """A shallow seam strip lying ON the sloped roof surface, following its
    own slope normal -- NOT a vertical world-Z fin. The baseline built seams
    with a fixed world-Z span (WALL_H-0.3 .. RIDGE_H+0.3, ~5.9 studs tall)
    that stood straight up regardless of the slope's rotation, producing the
    tall brown fin plates visible in the review screenshots. This computes
    the exact point on the slope's centreline and offsets only ~0.03-0.08
    studs along the surface's own normal (Fix B)."""
    run = x_high - x_low
    length = math.hypot(run, _ROOF_RISE)
    ang = math.atan2(_ROOF_RISE, run) * rise_sign
    cx = (x_low + x_high) / 2
    cz = WALL_H + (RIDGE_H - WALL_H) / 2
    cy = (ROOF_D0 + ROOF_D1) / 2
    depth = ROOF_D1 - ROOF_D0
    seam_w = 0.16
    seam_h = 0.06
    local_x = (frac - 0.5) * length
    rot_mat = mathutils.Euler((0, -ang, 0)).to_matrix()
    local_z = ROOF_T / 2 + seam_h / 2
    off_pos = rot_mat @ mathutils.Vector((local_x, 0, local_z))
    off_neg = rot_mat @ mathutils.Vector((local_x, 0, -local_z))
    off = off_pos if off_pos.z >= off_neg.z else off_neg  # pick the outward (sky-facing) face
    loc = (cx + off.x, cy, cz + off.z)
    return noncollide(box_c("%s_Seam_%d" % (tag, idx), loc, (seam_w, depth - 0.6, seam_h), BEAM_DARK, coll,
                             rot=(0, -ang, 0)))


for i in range(1, 5):
    roof_seam("Roof_Left", i, CAB_X0 - ROOF_OVH, RIDGE_X, 1, i / 5.0, R)
for i in range(1, 6):
    roof_seam("Roof_Right", i, RIDGE_X, CAB_X1 + ROOF_OVH, -1, i / 6.0, R)

box("Roof_RidgeCap", (RIDGE_X - 0.45, RIDGE_X + 0.45), (ROOF_D0, ROOF_D1),
    (RIDGE_H - 0.1, RIDGE_H + 0.5), BEAM_DARK, R)
box("Roof_Fascia_Front", (CAB_X0 - ROOF_OVH, CAB_X1 + ROOF_OVH), (ROOF_D0, ROOF_D0 + 0.4),
    (WALL_H - 0.4, WALL_H + 0.1), TRIM_PALE, R)
box("Roof_Fascia_Rear", (CAB_X0 - ROOF_OVH, CAB_X1 + ROOF_OVH), (ROOF_D1 - 0.4, ROOF_D1),
    (WALL_H - 0.4, WALL_H + 0.1), TRIM_PALE, R)

# --------------------------------------------------------------------------
# 3. Eaves / entry shelter (section 7.5)
# --------------------------------------------------------------------------

for _ex in (-12.0, 12.0):
    box("Eave_Post_%d" % int(_ex), (_ex - 0.275, _ex + 0.275), (Y(2.2) - 0.275, Y(2.2) + 0.275),
        (0.0, WALL_H), BEAM_DARK, S)
    # one diagonal knee brace per post, toward the wall
    _brace_x1 = _ex + (-1.4 if _ex > 0 else 1.4)
    _rafter("Eave_KneeBrace_%d" % int(_ex), _ex, WALL_H - 2.2, _brace_x1, WALL_H - 0.3,
            Y(2.2), S)

# --------------------------------------------------------------------------
# 4. Chimney (section 7.7)
# --------------------------------------------------------------------------

_CHIM_X, _CHIM_Y = STOVE_X, STOVE_Y - 1.5
box("Chimney_Shaft", (_CHIM_X - 0.4, _CHIM_X + 0.4), (_CHIM_Y - 0.4, _CHIM_Y + 0.4),
    (0.0, RIDGE_H + 2.0), STONE, S)
box("Chimney_Cap", (_CHIM_X - 0.55, _CHIM_X + 0.55), (_CHIM_Y - 0.55, _CHIM_Y + 0.55),
    (RIDGE_H + 2.0, RIDGE_H + 2.35), IRON, S)

# --------------------------------------------------------------------------
# 5. Openings -- doors, windows, shutters, hardware (section 8)
# --------------------------------------------------------------------------

O = GROUPS["Openings"]


def door_frame(tag, x0, x1, wall_y, open_toward):
    """Jambs + head OUTSIDE the clear aperture; two leaves hinged at the
    outer jambs, opening outward (+open_toward in Y)."""
    jt = 0.35
    box("Door_%s_Frame_Left" % tag, (x0 - jt, x0), (wall_y - WALL_T / 2 - 0.05, wall_y + WALL_T / 2 + 0.05),
        (0.0, DOOR_CLEAR_H + jt), TRIM_PALE, O)
    box("Door_%s_Frame_Right" % tag, (x1, x1 + jt), (wall_y - WALL_T / 2 - 0.05, wall_y + WALL_T / 2 + 0.05),
        (0.0, DOOR_CLEAR_H + jt), TRIM_PALE, O)
    box("Door_%s_Frame_Head" % tag, (x0 - jt, x1 + jt), (wall_y - WALL_T / 2 - 0.05, wall_y + WALL_T / 2 + 0.05),
        (DOOR_CLEAR_H, DOOR_CLEAR_H + jt), TRIM_PALE, O)
    leaf_w = (x1 - x0) / 2
    # Swing angle measured from the closed (flat-against-the-wall) position,
    # shared by both leaves. The baseline recomputed a per-leaf "phi" with
    # the sign folded in BEFORE the abs(), which produced the correct 86 for
    # the Left leaf (abs(94-90)=4 -> 90-4=86) but a broken 184 for the Right
    # leaf (abs(-94-90)=184 -> 90-184=-94) -- a totally different angle than
    # its own (separately, correctly mirrored) rotation used. The leaf's
    # CENTER then landed on the interior side of the hinge instead of
    # swung outward, i.e. the door appeared to "stick into the room"
    # (Fix E). Using one shared, sign-free swing angle for position AND
    # rotation removes the discrepancy.
    swing = math.radians(90) - abs(math.radians(DOOR_LEAF_PHI) - math.radians(90))  # = 86 deg
    for side, hinge_x, sign in (("Left", x0, 1), ("Right", x1, -1)):
        # leaf pivots at hinge_x, swings open toward +open_toward*Y
        leaf = box_c("Door_%s_Leaf_%s" % (tag, side),
                      (hinge_x + sign * (leaf_w / 2) * math.cos(swing),
                       wall_y + open_toward * (leaf_w / 2) * math.sin(swing),
                       DOOR_CLEAR_H / 2),
                      (leaf_w, 0.22, DOOR_CLEAR_H),
                      TIMBER_MAIN, O,
                      rot=(0, 0, sign * open_toward * swing))
        noncollide(leaf)
        noncollide(box_c("Door_%s_Leaf_%s_Panel" % (tag, side), leaf.location,
                          (leaf_w * 0.6, 0.26, DOOR_CLEAR_H * 0.75), BEAM_DARK, O, rot=leaf.rotation_euler))
        noncollide(box_c("Door_%s_Leaf_%s_Handle" % (tag, side),
                          (leaf.location.x - sign * leaf_w * 0.32, leaf.location.y + open_toward * 0.16, DOOR_CLEAR_H / 2),
                          (0.1, 0.45, 0.1), IRON, O))
        noncollide(box_c("Door_%s_Leaf_%s_HingeLo" % (tag, side),
                          (hinge_x, wall_y, 1.0), (0.12, 0.3, 0.2), IRON, O))
        noncollide(box_c("Door_%s_Leaf_%s_HingeHi" % (tag, side),
                          (hinge_x, wall_y, DOOR_CLEAR_H - 1.0), (0.12, 0.3, 0.2), IRON, O))
    # Threshold flush with the walking surface (top AT Z=0.0, not above it) --
    # the baseline raised the threshold top to Z=0.05 without compensating the
    # frame head, silently eating 0.05 studs of clear height. Fix C.
    box("Door_%s_Threshold" % tag, (x0, x1), (wall_y - WALL_T / 2, wall_y + WALL_T / 2),
        (-0.04, 0.0), BEAM_DARK, O)


door_frame("Front", FRONT_DOOR_X0, FRONT_DOOR_X1, FRONT_DOOR_Y, -1)   # opens outward, toward front (-Y)
door_frame("Rear", REAR_DOOR_X0, REAR_DOOR_X1, REAR_DOOR_Y, 1)        # opens outward, toward rear (+Y)


def window(tag, xc, wall_y, w, h, z0, z1, axis='X'):
    sill_t = WIN_SILL_T
    if axis == 'X':
        box("Window_%s_Sill" % tag, (xc - w / 2 - WIN_JAMB_W, xc + w / 2 + WIN_JAMB_W),
            (wall_y - WALL_T / 2 - 0.1, wall_y + WALL_T / 2 + 0.1), (z0 - sill_t, z0), TRIM_PALE, O)
        box("Window_%s_Head" % tag, (xc - w / 2 - WIN_JAMB_W, xc + w / 2 + WIN_JAMB_W),
            (wall_y - WALL_T / 2, wall_y + WALL_T / 2), (z1, z1 + WIN_HEAD_T), TRIM_PALE, O)
        box("Window_%s_JambL" % tag, (xc - w / 2 - WIN_JAMB_W, xc - w / 2), (wall_y - WALL_T / 2, wall_y + WALL_T / 2),
            (z0, z1), TRIM_PALE, O)
        box("Window_%s_JambR" % tag, (xc + w / 2, xc + w / 2 + WIN_JAMB_W), (wall_y - WALL_T / 2, wall_y + WALL_T / 2),
            (z0, z1), TRIM_PALE, O)
        box("Window_%s_Mullion" % tag, (xc - 0.08, xc + 0.08), (wall_y - WALL_T / 2, wall_y + WALL_T / 2),
            (z0, z1), TRIM_PALE, O)
        noncollide(box("Window_%s_Pane" % tag, (xc - w / 2, xc + w / 2), (wall_y - 0.06, wall_y + 0.06),
                        (z0, z1), GLASS, O))
    else:
        box("Window_%s_Sill" % tag, (wall_y - WALL_T / 2 - 0.1, wall_y + WALL_T / 2 + 0.1),
            (xc - w / 2 - WIN_JAMB_W, xc + w / 2 + WIN_JAMB_W), (z0 - sill_t, z0), TRIM_PALE, O)
        box("Window_%s_Head" % tag, (wall_y - WALL_T / 2, wall_y + WALL_T / 2),
            (xc - w / 2 - WIN_JAMB_W, xc + w / 2 + WIN_JAMB_W), (z1, z1 + WIN_HEAD_T), TRIM_PALE, O)
        box("Window_%s_JambF" % tag, (wall_y - WALL_T / 2, wall_y + WALL_T / 2), (xc - w / 2 - WIN_JAMB_W, xc - w / 2),
            (z0, z1), TRIM_PALE, O)
        box("Window_%s_JambR" % tag, (wall_y - WALL_T / 2, wall_y + WALL_T / 2), (xc + w / 2, xc + w / 2 + WIN_JAMB_W),
            (z0, z1), TRIM_PALE, O)
        box("Window_%s_Mullion" % tag, (wall_y - WALL_T / 2, wall_y + WALL_T / 2), (xc - 0.08, xc + 0.08),
            (z0, z1), TRIM_PALE, O)
        noncollide(box("Window_%s_Pane" % tag, (wall_y - 0.06, wall_y + 0.06), (xc - w / 2, xc + w / 2),
                        (z0, z1), GLASS, O))


window("FrontL", FRONT_WIN_XC_L, CAB_Y0, FRONT_WIN_W, FRONT_WIN_Z1 - FRONT_WIN_Z0, FRONT_WIN_Z0, FRONT_WIN_Z1)
window("FrontR", FRONT_WIN_XC_R, CAB_Y0, FRONT_WIN_W, FRONT_WIN_Z1 - FRONT_WIN_Z0, FRONT_WIN_Z0, FRONT_WIN_Z1)
window("Rear", REAR_WIN_XC, CAB_Y1, REAR_WIN_W, REAR_WIN_Z1 - REAR_WIN_Z0, REAR_WIN_Z0, REAR_WIN_Z1)
window("SideL", SIDE_WIN_YC_L, CAB_X0, SIDE_WIN_W, SIDE_WIN_H, SIDE_WIN_Z0, SIDE_WIN_Z1, axis='Y')
window("SideR", SIDE_WIN_YC_R, CAB_X1, SIDE_WIN_W, SIDE_WIN_H, SIDE_WIN_Z0, SIDE_WIN_Z1, axis='Y')

# Shutters: one open pair per front window, parked flat against the wall
# beside the frame (clear of the leaves and support posts)
for _tag, _xc, _side in (("FrontL", FRONT_WIN_XC_L, -1), ("FrontR", FRONT_WIN_XC_R, 1)):
    for _k, _sign in ((1, -1), (2, 1)):
        sx = _xc + _sign * (FRONT_WIN_W / 2 + 0.25)
        noncollide(box_c("Shutter_%s_%d" % (_tag, _k), (sx, CAB_Y0 - 0.2, (FRONT_WIN_Z0 + FRONT_WIN_Z1) / 2),
                          (0.25, 0.15, FRONT_WIN_Z1 - FRONT_WIN_Z0), TIMBER_LIGHT, O,
                          rot=(0, 0, math.radians(8 * _sign))))
        noncollide(box_c("Shutter_%s_%d_Brace" % (_tag, _k), (sx, CAB_Y0 - 0.2, (FRONT_WIN_Z0 + FRONT_WIN_Z1) / 2),
                          (0.3, 0.08, 0.1), BEAM_DARK, O, rot=(0, 0, math.radians(35))))

# Entry lantern, beside the front door (opposite the mailbox)
noncollide(box_c("EntryLantern_Housing", (FRONT_DOOR_X1 + 1.0, CAB_Y0 - 0.3, 7.0), (0.7, 0.7, 1.0), IRON, O))
noncollide(box_c("EntryLantern_Lens", (FRONT_DOOR_X1 + 1.0, CAB_Y0 - 0.64, 7.0), (0.4, 0.1, 0.6), TRIM_PALE, O))
noncollide(box_c("EntryLantern_Bracket", (FRONT_DOOR_X1 + 1.0, CAB_Y0 - 0.1, 7.55), (0.12, 0.4, 0.12), IRON, O))

# Wall mailbox, beside entrance, outside the door swing
noncollide(box_c("Mailbox_Box", (FRONT_DOOR_X0 - 1.3, CAB_Y0 - 0.25, 4.0), (1.2, 0.5, 0.5), TIMBER_LIGHT, O))
noncollide(box_c("Mailbox_Lid", (FRONT_DOOR_X0 - 1.3, CAB_Y0 - 0.25, 4.3), (1.2, 0.55, 0.08), BEAM_DARK, O,
                  rot=(math.radians(10), 0, 0)))
noncollide(box_c("Mailbox_Slot", (FRONT_DOOR_X0 - 1.3, CAB_Y0 - 0.51, 4.0), (0.6, 0.02, 0.12), IRON, O))

# Boot tray, far side of the front shelter (opposite the mailbox/lantern)
_BT_X, _BT_Y = CAB_X0 + 2.2, CAB_Y0 - 0.9
box("BootTray_Tray", (_BT_X - 1.1, _BT_X + 1.1), (_BT_Y - 0.65, _BT_Y + 0.65), (0.0, 0.15), IRON, O)
for _bi, (_bx, _adult) in enumerate(((-0.7, True), (-0.15, True), (0.35, False), (0.7, False))):
    tag = "Adult" if _adult else "Child"
    sx, sy, sz = (0.65, 1.0, 1.0) if _adult else (0.3, 0.5, 0.5)
    cz = 0.15 + sz / 2
    side = "L" if _bi % 2 == 0 else "R"
    noncollide(box_c("Boot_%s_%s_Sole" % (tag, side), (_BT_X + _bx, _BT_Y, 0.15 + 0.06), (sx, sy, 0.12),
                      BEAM_DARK, O))
    noncollide(box_c("Boot_%s_%s_Shaft" % (tag, side), (_BT_X + _bx, _BT_Y - sy * 0.12, cz + 0.1),
                      (sx * 0.8, sy * 0.7, sz * 0.75), RUST if _adult else CLOTH_BLUE, O))
    noncollide(box_c("Boot_%s_%s_Toe" % (tag, side), (_BT_X + _bx, _BT_Y + sy * 0.35, 0.15 + sz * 0.22),
                      (sx * 0.85, sy * 0.4, sz * 0.4), RUST if _adult else CLOTH_BLUE, O))

# --------------------------------------------------------------------------
# 6. Kitchen (section 9, left front)
# --------------------------------------------------------------------------

K = GROUPS["Kitchen"]
_KCX = CAB_IN_X0 + 0.9
_KCY0, _KCY1 = KITCH_Y0 + 0.3, KITCH_Y0 + 0.3 + 4.8
_SINK_Y = _KCY0 + 2.6
_SINK_HX, _SINK_HY = 0.65, 0.5  # half-extents of the sink rim cutout below

box("Kitchen_Counter_Body", (_KCX - 0.9, _KCX + 0.9), (_KCY0, _KCY1), (0.3, 2.78), TIMBER_MAIN, K)
# The counter top used to be ONE solid slab spanning the full run at the
# same Z band as the sink rim (2.78-2.96 inside 2.78-3.0), so the drop-in
# sink was entirely buried under solid wood -- only the free-standing
# faucet poked out above it, which read as "the sink is off somewhere away
# from the tap" (Fix G). Cut a rim-sized opening out of the top, the same
# below/above-the-gap technique used for the wall windows.
_ctY0, _ctY1 = _KCY0 - 0.05, _KCY1 + 0.05
_sY0, _sY1 = _SINK_Y - _SINK_HY, _SINK_Y + _SINK_HY
_sX0, _sX1 = _KCX - _SINK_HX, _KCX + _SINK_HX
box("Kitchen_Counter_Top_Front", (_KCX - 0.95, _KCX + 0.95), (_ctY0, _sY0), (2.78, 3.0), TIMBER_LIGHT, K)
box("Kitchen_Counter_Top_Back", (_KCX - 0.95, _KCX + 0.95), (_sY1, _ctY1), (2.78, 3.0), TIMBER_LIGHT, K)
box("Kitchen_Counter_Top_Left", (_KCX - 0.95, _sX0), (_sY0, _sY1), (2.78, 3.0), TIMBER_LIGHT, K)
box("Kitchen_Counter_Top_Right", (_sX1, _KCX + 0.95), (_sY0, _sY1), (2.78, 3.0), TIMBER_LIGHT, K)
box("Kitchen_Counter_ToeKick", (_KCX - 0.75, _KCX + 0.75), (_KCY0, _KCY0 + 0.15), (0.0, 0.3), BEAM_DARK, K)
noncollide(box_c("Kitchen_Counter_Door_1", (_KCX + 0.91, _KCY0 + 1.0, 1.5), (0.03, 1.5, 2.2), TIMBER_LIGHT, K))
noncollide(box_c("Kitchen_Counter_Door_2", (_KCX + 0.91, _KCY0 + 2.6, 1.5), (0.03, 1.5, 2.2), TIMBER_LIGHT, K))
noncollide(box_c("Kitchen_Counter_Drawer", (_KCX + 0.91, _KCY0 + 3.9, 2.2), (0.03, 0.7, 0.8), TIMBER_LIGHT, K))
for _hy in (_KCY0 + 1.0, _KCY0 + 2.6, _KCY0 + 3.9):
    noncollide(box_c("Kitchen_Counter_Handle_%d" % int(_hy * 10), (_KCX + 0.96, _hy, 1.5), (0.1, 0.35, 0.1), IRON, K))

box("Kitchen_Sink_Rim", (_KCX - 0.65, _KCX + 0.65), (_SINK_Y - 0.5, _SINK_Y + 0.5), (2.78, 2.96), IRON, K)
noncollide(box("Kitchen_Sink_Basin", (_KCX - 0.55, _KCX + 0.55), (_SINK_Y - 0.4, _SINK_Y + 0.4), (2.6, 2.78), IRON, K))
noncollide(box_c("Kitchen_Faucet_Riser", (_KCX - 0.5, _SINK_Y, 3.3), (0.1, 0.1, 0.65), IRON, K))
noncollide(box_c("Kitchen_Faucet_Spout", (_KCX - 0.2, _SINK_Y, 3.6), (0.5, 0.1, 0.1), IRON, K))
noncollide(box_c("Kitchen_Faucet_Handle", (_KCX - 0.5, _SINK_Y + 0.25, 3.3), (0.06, 0.2, 0.06), IRON, K))

_COOK_Y = _KCY0 + 1.0
noncollide(box_c("Kitchen_CookingSurface", (_KCX, _COOK_Y, 3.02), (1.2, 1.1, 0.04), IRON, K))
for _dx, _dy in ((-0.3, -0.25), (0.3, 0.25)):
    noncollide(cyl("Kitchen_CookDisc_%d_%d" % (int(_dx * 10), int(_dy * 10)),
                    (_KCX + _dx, _COOK_Y + _dy, 3.05), 0.28, 0.28, 0.03, IRON, K, segs=12))
for _dx, _dy in ((-0.5, 0.35), (0.5, 0.35)):
    noncollide(box_c("Kitchen_CookControl_%d" % int(_dx * 10), (_KCX + _dx, _COOK_Y + _dy, 3.03),
                      (0.12, 0.12, 0.03), TRIM_PALE, K))

# The wall cupboard used to hang IN the left-wall window opening (and half
# inside the wall). It now hangs on the solid wall between the front corner
# post and the window casing (y -19.4 .. -17.3), flush on the inner face.
_CUP_Y = _KCY0 - 0.65                       # centre; spans -19.2 .. -17.5
_CUP_FACE = CAB_X0 + WALL_T / 2             # inner wall face
_CUP_XC = _CUP_FACE + 0.35
box_c("Kitchen_Cupboard", (_CUP_XC, _CUP_Y, 5.5), (0.7, 1.7, 1.7), TIMBER_MAIN, K)
noncollide(box_c("Kitchen_Cupboard_Door_1", (_CUP_FACE + 0.715, _CUP_Y - 0.4, 5.5), (0.03, 0.75, 1.5), TIMBER_LIGHT, K))
noncollide(box_c("Kitchen_Cupboard_Door_2", (_CUP_FACE + 0.715, _CUP_Y + 0.4, 5.5), (0.03, 0.75, 1.5), TIMBER_LIGHT, K))
noncollide(box_c("Kitchen_Cupboard_Handle_1", (_CUP_FACE + 0.76, _CUP_Y - 0.1, 5.5), (0.08, 0.3, 0.08), IRON, K))
noncollide(box_c("Kitchen_Cupboard_Handle_2", (_CUP_FACE + 0.76, _CUP_Y + 0.1, 5.5), (0.08, 0.3, 0.08), IRON, K))

for _mi, (_mx, _my, _r, _h) in enumerate(((0.3, _COOK_Y - 0.6, 0.32, 0.4),
                                            (0.65, _COOK_Y - 0.6, 0.32, 0.4),
                                            (0.0, _COOK_Y - 0.95, 0.25, 0.3))):
    tag = "Adult" if _r > 0.28 else "Child"
    noncollide(cyl("Kitchen_Mug_%d" % (_mi + 1), (_KCX + _mx, _my, 3.0 + _h / 2), _r, _r, _h, TRIM_PALE, K, segs=10))
    noncollide(box_c("Kitchen_Mug_%d_Handle" % (_mi + 1), (_KCX + _mx + _r + 0.08, _my, 3.0 + _h / 2),
                      (0.1, 0.1, _h * 0.5), TRIM_PALE, K))
noncollide(box_c("Kitchen_DishTowel", (_KCX + 0.5, _KCY0 - 0.2, 2.95), (0.7, 0.1, 0.9), CLOTH_BLUE, K,
                  rot=(math.radians(8), 0, 0)))

# --------------------------------------------------------------------------
# 7. Stove + family seating (section 9, left strip)
# --------------------------------------------------------------------------

L = GROUPS["FamilyLiving"]

box("Stove_Hearth", (STOVE_X - 1.2, STOVE_X + 1.2), (STOVE_Y - 1.2, STOVE_Y + 1.2), (-0.0, 0.05), STONE, L)
box("Stove_Body", (STOVE_X - 0.75, STOVE_X + 0.75), (STOVE_Y - 0.65, STOVE_Y + 0.65), (0.05, 2.25), IRON, L)
for _fx in (-0.5, 0.5):
    for _fy in (-0.4, 0.4):
        box_c("Stove_Foot_%d_%d" % (int(_fx * 10), int(_fy * 10)), (STOVE_X + _fx, STOVE_Y + _fy, 0.1),
              (0.15, 0.15, 0.2), IRON, L)
noncollide(box_c("Stove_Door", (STOVE_X, STOVE_Y - 0.66, 1.1), (0.9, 0.04, 0.9), BEAM_DARK, L))
noncollide(box_c("Stove_Handle", (STOVE_X, STOVE_Y - 0.72, 1.1), (0.3, 0.08, 0.08), TRIM_PALE, L))
noncollide(box_c("Stove_Vent", (STOVE_X, STOVE_Y + 0.66, 1.8), (0.5, 0.05, 0.3), RUST, L))
# The baseline flue sat at Y=STOVE_Y-1.0 while the chimney shaft is centred
# at _CHIM_Y=STOVE_Y-1.5 -- only a 0.075-stud sliver of real overlap, a
# near-detached pipe. Build it as a straight riser above the stove plus a
# short horizontal elbow that actually meets the chimney shaft's footprint
# (the shaft itself spans Z 0..RIDGE_H+2, so the elbow only needs to reach
# its X/Y column to be a genuine connection).
box("Stove_Flue_Lower", (STOVE_X - 0.175, STOVE_X + 0.175), (STOVE_Y - 0.175, STOVE_Y + 0.175),
    (2.25, 3.0), IRON, L)
box("Stove_Flue_Elbow", (STOVE_X - 0.175, STOVE_X + 0.175), (_CHIM_Y, STOVE_Y), (3.0, 3.35), IRON, L)
noncollide(box_c("Stove_Flue_Clamp", (STOVE_X, STOVE_Y, 2.7), (0.42, 0.42, 0.12), TRIM_PALE, L))

box_c("FirewoodRack_FrameL", (STOVE_X - 2.4, STOVE_Y - 2.0, 0.65), (0.12, 0.9, 1.3), BEAM_DARK, L)
box_c("FirewoodRack_FrameR", (STOVE_X - 2.4, STOVE_Y - 2.0, 0.65), (0.12, 0.9, 1.3), BEAM_DARK, L)
for _li in range(6):
    noncollide(cyl("FirewoodRack_Log_%d" % (_li + 1),
                    (STOVE_X - 2.4, STOVE_Y - 2.3 + _li * 0.08, 0.3 + (_li % 3) * 0.25),
                    0.18, 0.18, 0.8, BEAM_DARK, L, segs=8, rot=(0, math.radians(90), 0)))

# Bench rebuilt per owner request: the baseline's cushions and blanket were
# three flat, equal-thickness, hard-edged slabs (the blanket was even the
# SAME colour and thickness as the blue cushion, reading as a third square
# cushion, not folded cloth). Fix M: a coherent wooden frame (seat + rail +
# backrest + bevelled end supports), two layered/bevelled cushions with a
# raised centre, and a separate multi-layer folded blanket with a rolled
# edge and darker stripe accents.
_bench_seat = box_c("Bench_Seat", (BENCH_X, BENCH_Y, 1.8), (4.8, 1.8, 0.18), TIMBER_MAIN, L)
bevel(_bench_seat, width=0.035, segments=2)
_bench_back = box_c("Bench_Back", (BENCH_X, BENCH_Y + 0.82, 2.65), (4.8, 0.16, 1.7), TIMBER_MAIN, L)
bevel(_bench_back, width=0.03, segments=2)
for _bx in (BENCH_X - 1.9, BENCH_X + 1.9):
    _sup = box_c("Bench_EndSupport_%d" % int(_bx * 10), (_bx, BENCH_Y, 0.9), (0.2, 1.7, 1.8), BEAM_DARK, L)
    bevel(_sup, width=0.03, segments=2)
# stretcher rail connecting both end supports, under the seat
box_c("Bench_SupportRail", (BENCH_X, BENCH_Y, 1.0), (4.4, 0.12, 0.12), BEAM_DARK, L)


def soft_cushion(name, center, size, material, coll):
    """A two-layer cushion (wider bevelled base + smaller bevelled raised
    top) instead of one flat slab -- gives bevelled/softened corners and a
    gently raised centre within the house's box-primitive toolkit."""
    cx, cy, cz = center
    sx, sy, sz = size
    base_h, top_h = sz * 0.58, sz * 0.42
    base = box_c("%s_Base" % name, (cx, cy, cz - sz / 2 + base_h / 2), (sx, sy, base_h), material, coll)
    bevel(base, width=min(0.05, base_h * 0.4), segments=2)
    top = box_c("%s_Top" % name, (cx, cy, cz - sz / 2 + base_h + top_h / 2),
                (sx * 0.86, sy * 0.86, top_h), material, coll)
    bevel(top, width=min(0.04, top_h * 0.4), segments=2)
    noncollide(base)
    noncollide(top)


_CUSHION_Z0 = 1.8 + 0.09  # seat top surface
soft_cushion("Bench_Cushion_Blue", (BENCH_X - 1.2, BENCH_Y, _CUSHION_Z0 + 0.12), (2.0, 1.5, 0.24), CLOTH_BLUE, L)
soft_cushion("Bench_Cushion_Rust", (BENCH_X + 0.55, BENCH_Y, _CUSHION_Z0 + 0.11), (1.5, 1.5, 0.22), RUST, L)

BLANKET_STRIPE = mat("LKC_BlanketStripe", srgb_to_linear((0x4E, 0x72, 0x87)))


def folded_blanket(name, center, size, coll, base_color, stripe_color):
    """A stacked, slightly-offset multi-layer blanket with a rolled fold
    edge and darker stripe accents -- reads as folded cloth, not a flat
    slab or a third cushion."""
    cx, cy, cz = center
    sx, sy, total_h = size
    layer_h = total_h / 3.0
    layer_defs = [(0.0, 0.0, sx, sy), (0.035, -0.02, sx * 0.9, sy * 0.88), (-0.025, 0.03, sx * 0.78, sy * 0.76)]
    z0 = cz - total_h / 2
    for _i, (_ox, _oy, _lx, _ly) in enumerate(layer_defs):
        _lz = z0 + layer_h * _i + layer_h / 2
        _lob = box_c("%s_Layer%d" % (name, _i + 1), (cx + _ox, cy + _oy, _lz), (_lx, _ly, layer_h * 0.92),
                      base_color, coll)
        bevel(_lob, width=0.025, segments=2)
        noncollide(_lob)
    # rolled fold edge at one end of the top layer
    _roll_x = cx - layer_defs[2][2] / 2 + 0.03
    noncollide(cyl("%s_FoldRoll" % name, (_roll_x, cy + layer_defs[2][1], z0 + total_h - layer_h * 0.25),
                    layer_h * 0.55, layer_h * 0.55, sy * 0.72, base_color, coll, segs=10,
                    rot=(math.radians(90), 0, 0)))
    # restrained darker stripe accents on the top layer
    for _sdx in (-0.12, 0.10):
        noncollide(box_c("%s_Stripe_%d" % (name, int(_sdx * 100)), (cx + _sdx, cy, z0 + total_h - 0.005),
                          (0.045, sy * 0.7, 0.01), stripe_color, coll))


folded_blanket("Bench_Blanket", (BENCH_X + 2.0, BENCH_Y, _CUSHION_Z0 + 0.14), (1.3, 0.9, 0.28), L,
                CLOTH_BLUE, BLANKET_STRIPE)

# Enlarged (1.3 -> 1.6) and nudged away from the bench's right edge so the
# boat, books, map and worm jar added below all fit without overlapping
# each other or the bench.
SIDETABLE_CX, SIDETABLE_CY = BENCH_X + 3.6, BENCH_Y - 1.3
SIDETABLE_SURF_Z = 1.95
box_c("SideTable_Top", (SIDETABLE_CX, SIDETABLE_CY, 1.9), (1.6, 1.6, 0.1), TIMBER_LIGHT, L)
for _lx, _ly in ((-0.65, -0.65), (0.65, -0.65), (-0.65, 0.65), (0.65, 0.65)):
    box_c("SideTable_Leg_%d_%d" % (int(_lx * 10), int(_ly * 10)),
          (SIDETABLE_CX + _lx, SIDETABLE_CY + _ly, 0.9), (0.12, 0.12, 1.8), BEAM_DARK, L)

# Family table (left middle)
box_c("FamilyTable_Top", (FTABLE_X, FTABLE_Y, 2.4), (3.4, 3.0, 0.2), TIMBER_MAIN, L)
box_c("FamilyTable_Apron", (FTABLE_X, FTABLE_Y, 2.2), (3.0, 2.6, 0.15), TIMBER_LIGHT, L)
for _lx, _ly in ((-1.5, -1.2), (1.5, -1.2), (-1.5, 1.2), (1.5, 1.2)):
    box_c("FamilyTable_Leg_%d_%d" % (int(_lx * 10), int(_ly * 10)),
          (FTABLE_X + _lx, FTABLE_Y + _ly, 1.1), (0.18, 0.18, 2.2), BEAM_DARK, L)
# Two stools on the near (-Y) side, one on the FAR (+Y) side, facing back
# across the table -- the baseline put all three at the same Y offset, i.e.
# lined up side-by-side off one edge like a bar, never facing each other.
for _si, (_sx, _sy) in enumerate(((-0.9, -2.3), (0.9, -2.3), (0.0, 2.3))):
    box_c("FamilyStool_%d_Seat" % (_si + 1), (FTABLE_X + _sx, FTABLE_Y + _sy, 1.5), (1.1, 1.1, 0.12), TIMBER_LIGHT, L)
    for _lx, _ly in ((-0.4, -0.4), (0.4, -0.4), (-0.4, 0.4), (0.4, 0.4)):
        box_c("FamilyStool_%d_Leg_%d_%d" % (_si + 1, int(_lx * 10), int(_ly * 10)),
              (FTABLE_X + _sx + _lx, FTABLE_Y + _sy + _ly, 0.72), (0.1, 0.1, 1.44), BEAM_DARK, L)
# Long cutting board with a cleaned fish -- body and head separated, knife
# stuck in the gap between them -- replacing the plain bread board (owner
# request). Built from many small parts (tapered body segments, forked
# tail, dorsal/pectoral fins, back stripe, belly stripe, scale flecks, eye
# with pupil, mouth, gill slit, and a flesh-coloured cut face on BOTH the
# body's front and the head's back) for close-up detail.
BOARD_CX, BOARD_CY = FTABLE_X, FTABLE_Y + 0.3
BOARD_SURF_Z = 2.59
box_c("FamilyTable_CuttingBoard", (BOARD_CX, BOARD_CY, 2.545), (2.2, 0.9, 0.09), TIMBER_LIGHT, L)
# Rectangular groove border (the owner's reference photo shows a full inset
# frame near the board's edges, not a single line near one side) -- Fix J.
_bgx0, _bgx1, _bgy0, _bgy1, _bgt = -0.95, 0.95, -0.30, 0.30, 0.035
noncollide(box_c("FamilyTable_CuttingBoard_GrooveTop", (BOARD_CX, BOARD_CY + _bgy1, BOARD_SURF_Z - 0.008),
                  (_bgx1 - _bgx0 + _bgt, _bgt, 0.014), BEAM_DARK, L))
noncollide(box_c("FamilyTable_CuttingBoard_GrooveBottom", (BOARD_CX, BOARD_CY + _bgy0, BOARD_SURF_Z - 0.008),
                  (_bgx1 - _bgx0 + _bgt, _bgt, 0.014), BEAM_DARK, L))
noncollide(box_c("FamilyTable_CuttingBoard_GrooveLeft", (BOARD_CX + _bgx0, BOARD_CY, BOARD_SURF_Z - 0.008),
                  (_bgt, _bgy1 - _bgy0 + _bgt, 0.014), BEAM_DARK, L))
noncollide(box_c("FamilyTable_CuttingBoard_GrooveRight", (BOARD_CX + _bgx1, BOARD_CY, BOARD_SURF_Z - 0.008),
                  (_bgt, _bgy1 - _bgy0 + _bgt, 0.014), BEAM_DARK, L))

# --- fish, rebuilt a FIFTH time: stacking separate box segments (even with
# guaranteed overlap) produced a visible staircase of flat-topped blocks,
# not a fish -- a box has no internal taper, so every junction where width
# changes is a hard vertical cliff. The owner's spec explicitly asks for
# "connected cross-sections, not a pile of intersecting cubes", which is
# exactly what the Skin modifier gives (smooth interpolation of the radius
# BETWEEN chain vertices). The problem before was only that a Skin mesh
# has ONE material. Fix: build the Skin tube, BAKE the modifier into a
# real mesh (so it's an ordinary static mesh, nothing Studio-side needs to
# evaluate), then colour each generated face by its own height fraction --
# a real two-material split on one connected surface.
# NOTE on unseen geometry: the reference photo shows one side only; the
# opposite side/back are a mirror continuation of the visible profile, not
# confirmed against any photo of that side.
_FY = BOARD_CY - 0.05
# A dedicated OPAQUE blue -- LAKE_BLUE is deliberately translucent
# (alpha=0.78, rough=0.15) for the lake's water surface, which made the
# fish look glassy/see-through when first reused here by mistake.
FISH_TOP = mat("LKC_FishBlue", srgb_to_linear((0x3E, 0x6B, 0x8A)), rough=0.4, alpha=1.0)
FISH_BOT = mat("LKC_FishCream", srgb_to_linear((0xE8, 0xDC, 0xC4)), rough=0.45, alpha=1.0)


def skin_chain_twotone(name, origin, chain, top_mat, bot_mat, coll, bottom_frac=0.42):
    """A connected-cross-section tube (Skin modifier: `chain` is (dx, ry,
    rz) tuples, vertex Z=rz keeps every ring bottom-flush) baked into a
    real static mesh, then coloured per-face: any face whose centre sits
    in the bottom `bottom_frac` of the LOCAL cross-section height (looked
    up by interpolating the chain's rz at that face's X) gets bot_mat,
    everything else gets top_mat. Flat-shaded (no smoothing) throughout."""
    me = bpy.data.meshes.new(name)
    verts = [(dx, 0.0, rz) for dx, ry, rz in chain]
    edges = [(i, i + 1) for i in range(len(verts) - 1)]
    me.from_pydata(verts, edges, [])
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob.modifiers.new("Skin", 'SKIN')
    sk = me.skin_vertices[0]
    for i, (dx, ry, rz) in enumerate(chain):
        sk.data[i].radius = (ry, rz)
    deps = bpy.context.evaluated_depsgraph_get()
    baked = bpy.data.meshes.new_from_object(ob.evaluated_get(deps))
    old_me = ob.data
    ob.modifiers.clear()
    ob.data = baked
    bpy.data.meshes.remove(old_me)
    ob.data.materials.append(top_mat)
    ob.data.materials.append(bot_mat)

    xs = [c[0] for c in chain]
    rzs = [c[2] for c in chain]

    def rz_at(x):
        if x <= xs[0]:
            return rzs[0]
        if x >= xs[-1]:
            return rzs[-1]
        for i in range(len(xs) - 1):
            if xs[i] <= x <= xs[i + 1]:
                t = (x - xs[i]) / (xs[i + 1] - xs[i])
                return rzs[i] * (1 - t) + rzs[i + 1] * t
        return rzs[-1]

    for p in ob.data.polygons:
        rz = rz_at(p.center.x)
        frac = (p.center.z / (2 * rz)) if rz > 1e-6 else 0.5
        p.material_index = 1 if frac < bottom_frac else 0
        p.use_smooth = False
    ob.location = origin
    base = name
    n = 1
    while name in OBJECT_MATERIAL:
        n += 1
        name = "%s_dup%d" % (base, n)
    OBJECT_MATERIAL[name] = top_mat.name
    OBJECT_ORDER.append(name)
    return noncollide(ob)


def skin_chain_flat(name, origin, chain, material, coll):
    """Same construction as skin_chain_twotone's tube (Skin modifier only,
    no Subsurf/shade_smooth -- stays a hard-edged low-poly facet tube) but
    with a single material, for the smaller belly tube below."""
    me = bpy.data.meshes.new(name)
    verts = [(dx, 0.0, rz) for dx, ry, rz in chain]
    edges = [(i, i + 1) for i in range(len(verts) - 1)]
    me.from_pydata(verts, edges, [])
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob.modifiers.new("Skin", 'SKIN')
    sk = me.skin_vertices[0]
    for i, (dx, ry, rz) in enumerate(chain):
        sk.data[i].radius = (ry, rz)
    me.materials.append(material)
    ob.location = origin
    base = name
    n = 1
    while name in OBJECT_MATERIAL:
        n += 1
        name = "%s_dup%d" % (base, n)
    OBJECT_MATERIAL[name] = material.name
    OBJECT_ORDER.append(name)
    return noncollide(ob)


# +dx = toward the head/snout, -dx = toward the tail. Widest around
# dx=0.08 (front-body/head boundary), per "broad chunky head and front
# body tapering towards a narrow tail connection".
_FISH_CHAIN = [
    (-1.00, 0.015, 0.02),
    (-0.85, 0.035, 0.045),
    (-0.68, 0.065, 0.085),
    (-0.50, 0.105, 0.135),
    (-0.30, 0.135, 0.175),
    (-0.10, 0.145, 0.19),
    (0.08, 0.15, 0.20),
    (0.26, 0.135, 0.175),
    (0.42, 0.08, 0.10),
    # Chain stops BLUNT at dx=0.56 -- the baseline tapered on to a sharp
    # needle point (dx=0.68, rz=0.018), and the separate "lower jaw" box
    # was glued on next to that point without touching it, reading as a
    # disconnected floating stick rather than a mouth (Fix L). The actual
    # snout-cap/jaw/mouth-notch assembly below picks up from this blunt end.
    (0.56, 0.05, 0.06),
]
skin_chain_twotone("Fish_Body", (BOARD_CX, _FY, BOARD_SURF_Z), _FISH_CHAIN, FISH_TOP, FISH_BOT, L, bottom_frac=0.42)

# The per-face colouring above works geometrically, but the Skin modifier's
# un-subdivided cross-section is only a 4-face diamond (bottom/left/right/
# top), so "below 42% height" only ever matches the single bottom strip --
# nearly invisible. Add a second, smaller cream tube along the same spine,
# shifted toward the camera-facing side and sized to the lower portion, so
# the belly actually reads as a visible band (Fix K).
_BELLY_CHAIN = [(dx, ry * 0.60, rz * 0.46) for dx, ry, rz in _FISH_CHAIN]
skin_chain_flat("Fish_Belly", (BOARD_CX, _FY - 0.065, BOARD_SURF_Z), _BELLY_CHAIN, FISH_BOT, L)

# forked tail: two chunky angular lobes with real thickness, spreading
# above and below the narrow tail-tip connection
_TAIL_X = BOARD_CX - 1.10
for _sign in (1, -1):
    _tv = [(0, 0, -0.012), (0, 0.20 * _sign, -0.09), (0.19, 0.11 * _sign, -0.045),
           (0, 0, 0.012), (0, 0.20 * _sign, 0.09), (0.19, 0.11 * _sign, 0.045)]
    noncollide(tri_prism("Fish_TailFin_%s" % ("Upper" if _sign > 0 else "Lower"), _tv,
                          [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)],
                          FISH_TOP, L, loc=(_TAIL_X, _FY, BOARD_SURF_Z + 0.04)))

# 1. dorsal fin, on top, base sunk into the Crown segment (widest point)
noncollide(tri_prism("Fish_DorsalFin",
                      [(-0.10, -0.011, 0), (0.12, -0.011, 0), (0.01, -0.011, 0.15),
                       (-0.10, 0.011, 0), (0.12, 0.011, 0), (0.01, 0.011, 0.15)],
                      [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)],
                      FISH_TOP, L, loc=(BOARD_CX + 0.08, _FY, BOARD_SURF_Z + 0.36)))

# 2. blue side (pectoral) fin, near the front, root sunk into the body
noncollide(box_c("Fish_PectoralFin", (BOARD_CX - 0.02, _FY - 0.14, BOARD_SURF_Z + 0.12), (0.17, 0.11, 0.016),
                  FISH_TOP, L, rot=(math.radians(28), math.radians(-8), math.radians(5))))

# 3. small lower (pelvic) fin near the front, below the pectoral fin
noncollide(box_c("Fish_PelvicFin", (BOARD_CX - 0.14, _FY - 0.10, BOARD_SURF_Z + 0.03), (0.10, 0.075, 0.012),
                  FISH_TOP, L, rot=(math.radians(40), math.radians(-6), math.radians(4))))

# 4. lower (anal) fin closer to the tail
noncollide(box_c("Fish_AnalFin", (BOARD_CX - 0.58, _FY - 0.08, BOARD_SURF_Z + 0.02), (0.09, 0.065, 0.011),
                  FISH_TOP, L, rot=(math.radians(35), math.radians(-5), math.radians(3))))

# two eyes, one on EACH side of the head (mirrored in Y) -- small flat
# black squares, slightly tilted
for _eye_sign in (1, -1):
    noncollide(box_c("Fish_Head_Eye_%s" % ("L" if _eye_sign > 0 else "R"),
                      (BOARD_CX + 0.28, _FY + 0.085 * _eye_sign, BOARD_SURF_Z + 0.20), (0.014, 0.032, 0.032),
                      IRON, L, rot=(math.radians(10 * _eye_sign), 0, 0)))

# snout cap + lower jaw + mouth notch, built as ONE physically touching
# assembly picking up from the chain's blunt end (dx=0.56) -- the baseline
# built a disconnected cream box floating next to a separate needle-point
# tip, with no shared surface between the "jaw" and the actual snout
# (Fix L). Each piece below is sized to overlap the one before it.
_SNOUT_CAP_X = BOARD_CX + 0.60
noncollide(box_c("Fish_SnoutCap", (_SNOUT_CAP_X, _FY, BOARD_SURF_Z + 0.085), (0.11, 0.10, 0.07), FISH_TOP, L))
noncollide(box_c("Fish_Head_MouthGap", (_SNOUT_CAP_X, _FY, BOARD_SURF_Z + 0.052), (0.05, 0.085, 0.018),
                  BEAM_DARK, L))
noncollide(box_c("Fish_Head_LowerJaw", (BOARD_CX + 0.63, _FY, BOARD_SURF_Z + 0.025), (0.12, 0.08, 0.05),
                  FISH_BOT, L))

# --- knife: broad light-grey blade narrowing toward its lower tip near the
# board, plain black rectangular handle connecting directly to the blade
# (no guard, no rivets), a slight lean.
# The knife belongs beside the TAIL (dx~-1.00, the forked-fin end), not
# the snout/head (dx~+0.7, where the eye and mouth are) -- it was wrongly
# placed next to the head in the previous pass. Offset sideways in Y
# (not further out in X) so it clears the tail fin without running the
# board's X extent past its edge (the fin's own tip already sits right at
# the board's edge at X=BOARD_CX-1.1).
_KNIFE_X, _KNIFE_Y = BOARD_CX - 1.00, _FY + 0.35
_kn_p0 = (_KNIFE_X, BOARD_SURF_Z - 0.02)          # tip, embedded slightly in the board
_kn_p1 = (_KNIFE_X + 0.035, BOARD_SURF_Z + 0.28)  # blade/handle junction
_kn_p2 = (_KNIFE_X + 0.075, BOARD_SURF_Z + 0.50)  # handle top

KNIFE_BLACK = mat("LKC_KnifeBlack", srgb_to_linear((0x1E, 0x1E, 0x22)))
KNIFE_GREY = mat("LKC_KnifeGrey", srgb_to_linear((0xC6, 0xC9, 0xCC)), rough=0.3, alpha=1.0)


def _knife_segment(name, p0, p1, width, height, material):
    x0, z0 = p0
    x1, z1 = p1
    length = math.hypot(x1 - x0, z1 - z0)
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    ang = math.atan2(z1 - z0, x1 - x0)
    sx, sy, sz = length, width, height
    v = [(-sx / 2, -sy / 2, -sz / 2), (sx / 2, -sy / 2, -sz / 2),
         (sx / 2, sy / 2, -sz / 2), (-sx / 2, sy / 2, -sz / 2),
         (-sx / 2, -sy / 2, sz / 2), (sx / 2, -sy / 2, sz / 2),
         (sx / 2, sy / 2, sz / 2), (-sx / 2, sy / 2, sz / 2)]
    return noncollide(_finish(name, v, BOX_FACES, material, L, loc=(cx, _KNIFE_Y, cz), rot=(0, -ang, 0)))


_knife_segment("Knife_Blade", _kn_p0, _kn_p1, 0.085, 0.03, KNIFE_GREY)
_knife_segment("Knife_Handle", _kn_p1, _kn_p2, 0.07, 0.055, KNIFE_BLACK)

# --------------------------------------------------------------------------
# 8. Sleeping alcove (section 9, right front)
# --------------------------------------------------------------------------

AL = GROUPS["SleepingAlcove"]
_BED_X, _BED_Y0 = ALC_X1 - 2.2, ALC_Y0 + 0.6

box_c("Bed_Frame", (_BED_X, _BED_Y0 + 2.6, 0.5), (3.5, 5.2, 1.0), BEAM_DARK, AL)
box_c("Bed_Mattress", (_BED_X, _BED_Y0 + 2.6, 1.3), (3.3, 5.0, 0.6), BED_WHITE, AL)
box_c("Bed_Headboard", (_BED_X, _BED_Y0 + 5.0, 1.9), (3.5, 0.2, 2.8), TIMBER_MAIN, AL)
box_c("Bed_FootRail", (_BED_X, _BED_Y0 + 0.2, 1.5), (3.5, 0.15, 0.7), TIMBER_MAIN, AL)
noncollide(box_c("Bed_Blanket", (_BED_X, _BED_Y0 + 2.2, 1.68), (3.2, 3.6, 0.25), CLOTH_BLUE, AL))
noncollide(box_c("Bed_Blanket_Stripe", (_BED_X, _BED_Y0 + 2.2, 1.69), (3.2, 0.4, 0.26), RUST, AL))
noncollide(box_c("Bed_Pillow_1", (_BED_X - 0.9, _BED_Y0 + 4.5, 1.65), (1.2, 0.8, 0.35), BED_WHITE, AL))
noncollide(box_c("Bed_Pillow_2", (_BED_X + 0.9, _BED_Y0 + 4.5, 1.65), (1.2, 0.8, 0.35), BED_WHITE, AL))

_COT_X, _COT_YC = 7.5, Y(8.2)
box_c("Cot_Frame", (_COT_X, _COT_YC, 0.5), (2.2, 3.7, 1.0), TIMBER_LIGHT, AL)
box_c("Cot_SideL", (_COT_X - 1.0, _COT_YC, 1.15), (0.1, 3.5, 0.5), TIMBER_LIGHT, AL)
box_c("Cot_SideR", (_COT_X + 1.0, _COT_YC, 1.15), (0.1, 3.5, 0.5), TIMBER_LIGHT, AL)
box_c("Cot_EndFoot", (_COT_X, _COT_YC - 1.75, 1.0), (2.0, 0.1, 0.4), TIMBER_LIGHT, AL)
box_c("Cot_EndHead", (_COT_X, _COT_YC + 1.75, 1.1), (2.0, 0.1, 0.6), TIMBER_LIGHT, AL)
noncollide(box_c("Cot_Pillow", (_COT_X, _COT_YC + 1.3, 1.05), (0.9, 0.5, 0.2), BED_WHITE, AL))
noncollide(box_c("Cot_Blanket", (_COT_X, _COT_YC - 0.2, 1.02), (1.9, 2.2, 0.12), RUST, AL))
noncollide(box_c("Cot_Shelf", (_COT_X + 1.3, _COT_YC + 1.4, 1.2), (0.6, 0.5, 0.08), TIMBER_LIGHT, AL))

# The coat pegs used to float at ALC_Y0-0.3 (~1.5 studs off the front wall) and
# directly in front of the front-right window. Mount them flush on the front
# wall's inner face, in the clear span between the front door jamb (x=4.35)
# and that window's casing (x=7.45).
_PEG_X = 4.7                                  # left edge of the coat group
_PEG_Y = CAB_Y0 + WALL_T / 2 + 0.1            # peg centre (flush on the wall face)
_PEG_C = _PEG_X + 0.75                        # centre of the adult coat
for _pi, _px in enumerate((_PEG_C, _PEG_C + 0.6, _PEG_C + 1.2)):
    noncollide(box_c("WallPeg_%d" % (_pi + 1), (_px, _PEG_Y, 6.0), (0.08, 0.2, 0.08), BEAM_DARK, AL))
box_c("WallPeg_Strip", (_PEG_C + 0.6, _PEG_Y - 0.02, 6.0), (2.6, 0.08, 0.2), TIMBER_LIGHT, AL)
noncollide(box_c("WallPeg_AdultCoat_Torso", (_PEG_C, _PEG_Y + 0.2, 4.6), (0.75, 0.2, 1.6), RUST, AL))
noncollide(box_c("WallPeg_AdultCoat_SleeveL", (_PEG_C - 0.55, _PEG_Y + 0.15, 4.3), (0.2, 0.18, 1.1), RUST, AL,
                  rot=(0, math.radians(15), 0)))
noncollide(box_c("WallPeg_AdultCoat_SleeveR", (_PEG_C + 0.55, _PEG_Y + 0.15, 4.3), (0.2, 0.18, 1.1), RUST, AL,
                  rot=(0, math.radians(-15), 0)))
noncollide(box_c("WallPeg_AdultCoat_Collar", (_PEG_C, _PEG_Y + 0.2, 5.3), (0.5, 0.22, 0.2), RUST, AL))
noncollide(box_c("WallPeg_ChildCoat_Torso", (_PEG_C + 0.6, _PEG_Y + 0.2, 5.0), (0.5, 0.18, 1.0), CLOTH_BLUE, AL))
noncollide(box_c("WallPeg_ChildCoat_Collar", (_PEG_C + 0.6, _PEG_Y + 0.2, 5.45), (0.35, 0.2, 0.14), CLOTH_BLUE, AL))
noncollide(cyl("WallPeg_Hat", (_PEG_C + 1.2, _PEG_Y + 0.2, 5.5), 0.28, 0.32, 0.18, BEAM_DARK, AL, segs=12))

# --------------------------------------------------------------------------
# 9. Fishing corner (section 9, right middle)
# --------------------------------------------------------------------------

F = GROUPS["FishingCorner"]

box_c("Fishing_Workbench_Top", (BENCH2_X, BENCH2_Y, 2.9), (1.4, 4.0, 0.2), TIMBER_MAIN, F)
for _wy in (BENCH2_Y - 1.7, BENCH2_Y + 1.7):
    box_c("Fishing_Workbench_Support_%d" % int(_wy * 10), (BENCH2_X, _wy, 1.4), (1.2, 0.2, 2.6), BEAM_DARK, F)
noncollide(box_c("Fishing_Workbench_Drawer", (BENCH2_X - 0.6, BENCH2_Y, 2.5), (0.2, 1.2, 0.6), TIMBER_LIGHT, F))

noncollide(box_c("Fishing_TackleBox_Body", (BENCH2_X - 0.2, BENCH2_Y - 1.5, 3.3), (1.1, 0.7, 0.55), TIMBER_MAIN, F))
noncollide(box_c("Fishing_TackleBox_Lid", (BENCH2_X - 0.2, BENCH2_Y - 1.5, 3.6), (1.1, 0.7, 0.1), TIMBER_MAIN, F))
noncollide(box_c("Fishing_TackleBox_Handle", (BENCH2_X - 0.2, BENCH2_Y - 1.5, 3.7), (0.4, 0.08, 0.1), IRON, F))
for _lx in (-0.4, 0.4):
    noncollide(box_c("Fishing_TackleBox_Latch_%d" % int(_lx * 10), (BENCH2_X + 0.36, BENCH2_Y - 1.5 + _lx, 3.35),
                      (0.05, 0.14, 0.14), IRON, F))

box_c("Fishing_RodRack_SupportL", (CAB_X1 - 0.5, BENCH2_Y - 1.3, 4.5), (0.15, 0.2, 2.0), BEAM_DARK, F)
box_c("Fishing_RodRack_SupportR", (CAB_X1 - 0.5, BENCH2_Y + 1.3, 4.5), (0.15, 0.2, 2.0), BEAM_DARK, F)


def rod_assembly(tag, z_butt, coll):
    """One coherent rod: grip -> tapered two-segment bent shaft -> reel,
    resting between the rack's two support posts (overhanging the far one a
    little, like a real rod in a cradle). The baseline placed a lone 4-stud
    shaft at Z=5.5 and a lone grip at Z=3.6 with no connecting geometry --
    a 1.9-stud gap -- which is what the review saw as a disconnected rod
    (Fix C). Everything here is built end-to-end from explicit 3D points,
    the same way _rafter() already does for the gable, just rotated about
    the X axis since the rod runs mostly along Y, not X."""
    support_l_y, support_r_y = BENCH2_Y - 1.3, BENCH2_Y + 1.3
    rod_x = CAB_X1 - 0.5
    by = support_l_y - 0.4                      # overhangs the near support slightly
    ty = by + 4.0                                # ~4.0-stud total rod length (spec: 3.5-4.5)
    bz = z_butt
    tz = z_butt + 0.3                            # gentle upward lean toward the far support
    my = (by + ty) / 2
    mz = (bz + tz) / 2 + 0.12                     # slight kink -> "two-segment bent" silhouette

    def psi_of(y0, z0, y1, z1):
        return math.atan2(-(y1 - y0), z1 - z0)

    grip_len = 0.55
    psi0 = psi_of(by, bz, my, mz)
    uy0, uz0 = -math.sin(psi0), math.cos(psi0)
    gy, gz = by + uy0 * grip_len / 2, bz + uz0 * grip_len / 2
    noncollide(cyl("Fishing_Rod_%s_Grip" % tag, (rod_x, gy, gz), 0.095, 0.08, grip_len, IRON, coll, segs=8,
                    rot=(psi0, 0, 0)))
    sy0, sz0 = by + uy0 * grip_len, bz + uz0 * grip_len
    len0 = math.hypot(my - sy0, mz - sz0)
    noncollide(cyl("Fishing_Rod_%s_ShaftLower" % tag, (rod_x, (sy0 + my) / 2, (sz0 + mz) / 2), 0.055, 0.035, len0,
                    BEAM_DARK, coll, segs=6, rot=(psi0, 0, 0)))
    psi1 = psi_of(my, mz, ty, tz)
    len1 = math.hypot(ty - my, tz - mz)
    noncollide(cyl("Fishing_Rod_%s_ShaftUpper" % tag, (rod_x, (my + ty) / 2, (mz + tz) / 2), 0.035, 0.016, len1,
                    BEAM_DARK, coll, segs=6, rot=(psi1, 0, 0)))
    noncollide(cyl("Fishing_Rod_%s_ReelDisc" % tag, (rod_x, sy0 - uz0 * 0.17, sz0 + uy0 * 0.17), 0.17, 0.17, 0.09,
                    IRON, coll, segs=10, rot=(psi0 + math.radians(90), 0, 0)))


for _ri, _zb in enumerate((4.0, 4.6, 5.2)):
    rod_assembly(str(_ri + 1), _zb, F)

noncollide(box_c("Fishing_LandingNet_Handle", (CAB_X1 - 0.3, BENCH2_Y - 2.6, 4.2), (0.08, 0.08, 1.8), BEAM_DARK, F))
noncollide(cyl("Fishing_LandingNet_Hoop", (CAB_X1 - 0.3, BENCH2_Y - 2.6, 5.4), 0.45, 0.45, 0.08, IRON, F, segs=14,
                rot=(math.radians(90), 0, 0)))
noncollide(box_c("Fishing_LandingNet_Mesh", (CAB_X1 - 0.3, BENCH2_Y - 2.6, 5.4), (0.75, 0.04, 0.75), TRIM_PALE, F))

box_c("Fishing_Shelf_Body", (CAB_X1 - 0.35, BENCH2_Y + 2.8, 2.0), (0.7, 2.4, 2.0), TIMBER_MAIN, F)
for _sz in (1.0, 1.8):
    box_c("Fishing_Shelf_%d" % int(_sz * 10), (CAB_X1 - 0.5, BENCH2_Y + 2.8, _sz), (0.4, 2.3, 0.08), TIMBER_LIGHT, F)
noncollide(cyl("Fishing_Shelf_Jar", (CAB_X1 - 0.6, BENCH2_Y + 2.0, 1.3), 0.22, 0.22, 0.55, GLASS, F, segs=10))
noncollide(box_c("Fishing_Shelf_Book_1", (CAB_X1 - 0.6, BENCH2_Y + 3.0, 1.25), (0.08, 0.5, 0.4), ROOF_GREEN, F))
noncollide(box_c("Fishing_Shelf_Book_2", (CAB_X1 - 0.6, BENCH2_Y + 3.5, 1.22), (0.08, 0.45, 0.35), RUST, F))

# --------------------------------------------------------------------------
# 9b. Interior zoning -- two short, low partitions (owner request)
# --------------------------------------------------------------------------
# These visually separate the kitchen from the stove/seating area (left
# wall) and the sleeping alcove from the fishing corner (right wall). They
# are deliberately SHORT (stop well inside the room) and LOW (3.2 studs,
# under WALL_H=11.5) so this stays "one open communal room" per the design
# spec -- not an enclosed bedroom/kitchen -- and never approach the
# mandatory central lane (X=-4..4) or rear turn area. Positions were picked
# by hand from every nearby prop's actual bounds (kitchen counter ends at
# Y=-12.9, firewood rack spans Y=-10.45..-9.55, stove hearth Y=-9.2..-6.8,
# side windows' jambs end at Y=-12.7/-9.3) and are re-checked numerically
# after the build (see verify script) so the walls don't clip any model.
PART_H = 3.2
PART_T = 0.2
board_wall("Partition_Kitchen", 'X', CAB_X0, CAB_X0 + 2.3, -11.3, 0.0, PART_H, S, thick=PART_T)
box("Partition_Kitchen_Cap", (CAB_X0, CAB_X0 + 2.3), (-11.3 - PART_T / 2 - 0.05, -11.3 + PART_T / 2 + 0.05),
    (PART_H, PART_H + 0.12), BEAM_DARK, S)

board_wall("Partition_Alcove", 'X', CAB_X1 - 2.7, CAB_X1, -10.8, 0.0, PART_H, S, thick=PART_T)
box("Partition_Alcove_Cap", (CAB_X1 - 2.7, CAB_X1), (-10.8 - PART_T / 2 - 0.05, -10.8 + PART_T / 2 + 0.05),
    (PART_H, PART_H + 0.12), BEAM_DARK, S)

# --------------------------------------------------------------------------
# 10. Story props (section 10)
# --------------------------------------------------------------------------

ST = GROUPS["StoryProps"]
# Left wall boards are centred on CAB_X0 with half-thickness WALL_T/2, so
# the inner (room-facing) face is at CAB_X0+WALL_T/2 -- NOT CAB_X0 itself.
# The baseline's CAB_X0+0.08 landed INSIDE the solid board (wall spans
# CAB_X0-WALL_T/2..CAB_X0+WALL_T/2 = roughly CAB_X0-0.225..+0.225), so the
# portrait and dream-fish plaque were embedded in, and hidden behind, the
# wall -- exactly the bug the owner spotted on the new trophy fish (Fix F).
# Portrait and dream-fish used to sit beside the window at the same height as
# the cupboard, overlapping the corner post, the window casing and each other.
# They now hang together on the clear wall ABOVE the left window (head casing
# tops out at z=8.35).
_PORTRAIT_X, _PORTRAIT_Y, _PORTRAIT_Z = CAB_X0 + WALL_T / 2 + 0.04, SIDE_WIN_YC_L - 1.5, 9.8
noncollide(box_c("Story_TinyFishPortrait_Frame", (_PORTRAIT_X, _PORTRAIT_Y, _PORTRAIT_Z), (0.1, 1.6, 1.2), BEAM_DARK, ST))
noncollide(box_c("Story_TinyFishPortrait_Backing", (_PORTRAIT_X + 0.03, _PORTRAIT_Y, _PORTRAIT_Z), (0.04, 1.4, 1.0),
                  LAKE_BLUE, ST))
noncollide(box_c("Story_TinyFishPortrait_Fish", (_PORTRAIT_X + 0.06, _PORTRAIT_Y, _PORTRAIT_Z), (0.02, 0.22, 0.1),
                  TRIM_PALE, ST))

_DREAM_Y = SIDE_WIN_YC_L + 1.3
noncollide(box_c("Story_DreamCatchFish_Body", (_PORTRAIT_X + 0.03, _DREAM_Y, _PORTRAIT_Z), (0.08, 2.0, 1.0),
                  TRIM_PALE, ST))
noncollide(box_c("Story_DreamCatchFish_Tail", (_PORTRAIT_X + 0.03, _DREAM_Y - 1.2, _PORTRAIT_Z), (0.08, 0.6, 0.7),
                  TRIM_PALE, ST, rot=(math.radians(20), 0, 0)))
noncollide(box_c("Story_DreamCatchFish_Eye", (_PORTRAIT_X + 0.1, _DREAM_Y + 0.8, _PORTRAIT_Z + 0.2), (0.02, 0.1, 0.1),
                  IRON, ST))

# Fishing trophies -- three mounted fish, on the REAR wall, to the right of
# the rear window as seen by someone walking in from the front door and
# facing the back wall (facing +Y, "right" = +X): the rear window is
# centred at REAR_WIN_XC=-8, so these sit in the clear Cabin_Wall_Rear_L2
# span between the window's jamb (~-4.2) and the rear door frame (X=4.0).
# Added per owner request; mounted the same way as the portrait/dream-fish
# above but rotated for a wall that runs along X, not Y.
# Rear wall boards are centred on CAB_Y1 with half-thickness WALL_T/2, so
# the inner (room-facing) face is at CAB_Y1-WALL_T/2 -- NOT CAB_Y1 itself.
# Mount proud of that face (toward the room, i.e. smaller Y), not merely
# "close to CAB_Y1", or the prop ends up embedded inside the solid board
# and invisible from inside (Fix F -- see also the portrait/dream-fish fix
# just above, which had the identical bug on the left wall).
_TROPHY_Y = CAB_Y1 - WALL_T / 2 - 0.04
_TROPHY_Z = 6.0
for _ti, (_tx, _tscale) in enumerate(((-2.6, 0.6), (-0.9, 0.85), (0.9, 0.5))):
    _tw, _th = 0.9 * _tscale, 0.5 * _tscale
    noncollide(box_c("Story_Trophy_%d_Plaque" % (_ti + 1), (_tx, _TROPHY_Y + 0.02, _TROPHY_Z),
                      (_tw + 0.25, 0.06, _th + 0.3), BEAM_DARK, ST))
    noncollide(box_c("Story_Trophy_%d_Body" % (_ti + 1), (_tx, _TROPHY_Y, _TROPHY_Z),
                      (_tw, 0.1, _th), TRIM_PALE, ST))
    noncollide(box_c("Story_Trophy_%d_Tail" % (_ti + 1), (_tx - _tw * 0.55, _TROPHY_Y, _TROPHY_Z),
                      (_tw * 0.35, 0.1, _th * 0.75), TRIM_PALE, ST, rot=(math.radians(18), 0, 0)))
    noncollide(box_c("Story_Trophy_%d_Eye" % (_ti + 1), (_tx + _tw * 0.38, _TROPHY_Y - 0.06, _TROPHY_Z + _th * 0.15),
                      (0.05, 0.05, 0.05), IRON, ST))

# The child's drawing used to float in mid-air (y = FTABLE_Y+2.2, there is no
# wall there -- it was a horizontal sheet hovering at z=4 with a few vertical
# scribbles). It is now a real vertical sheet taped to the LEFT wall's inner
# face, level with the family table.
_DR_FACE = CAB_X0 + WALL_T / 2              # inner face of the left wall
_DR_Y = FTABLE_Y                            # centre of the sheet along the wall
noncollide(box_c("Story_ChildDrawing_Paper", (_DR_FACE + 0.025, _DR_Y, 4.0), (0.03, 1.5, 1.2), PAPER, ST))
for _tk in (-0.5, 0.5):
    noncollide(box_c("Story_ChildDrawing_Tape_%d" % int(_tk * 10), (_DR_FACE + 0.03, _DR_Y + _tk, 4.55),
                      (0.04, 0.25, 0.12), TRIM_PALE, ST))
noncollide(box_c("Story_ChildDrawing_Cabin", (_DR_FACE + 0.05, _DR_Y - 0.4, 3.75), (0.01, 0.5, 0.35), TIMBER_MAIN,
                  ST))
for _fi, _fx in enumerate((-0.05, 0.1, 0.25)):
    noncollide(box_c("Story_ChildDrawing_Figure_%d" % (_fi + 1), (_DR_FACE + 0.05, _DR_Y + _fx, 3.85),
                      (0.01, 0.05, 0.35), TIMBER_LIGHT, ST))
noncollide(box_c("Story_ChildDrawing_BigFish", (_DR_FACE + 0.05, _DR_Y + 0.45, 4.1), (0.01, 0.5, 0.3), LAKE_BLUE,
                  ST))

def toy_boat(prefix, cx, cy, surface_z, coll, hull_len=0.6, hull_w=0.32, hull_h=0.15):
    """A small standalone toy-sailboat assembly (hull + rim + hollow
    interior + pointed bow + mast + sail), built the same way as the real
    Rowboat (hull/rim/interior/bow-prism pattern) instead of the baseline's
    two flat boxes. Previously the hull sat half a stud INSIDE the side
    table's top (clipping) and had no boat silhouette at all (Fix H)."""
    hull_cz = surface_z + hull_h / 2
    box_c("%s_Hull" % prefix, (cx, cy, hull_cz), (hull_w, hull_len, hull_h), TIMBER_LIGHT, coll)
    noncollide(box_c("%s_HullRim" % prefix, (cx, cy, hull_cz + hull_h / 2 + 0.01),
                      (hull_w + 0.04, hull_len + 0.04, 0.02), BEAM_DARK, coll))
    noncollide(box_c("%s_Interior" % prefix, (cx, cy, hull_cz + hull_h * 0.15),
                      (hull_w * 0.72, hull_len * 0.72, hull_h * 0.5), BEAM_DARK, coll))
    bow_hw, bow_len, bow_y0 = hull_w / 2, hull_len * 0.3, hull_len / 2
    bow_v = [(-bow_hw, bow_y0, -hull_h / 2), (bow_hw, bow_y0, -hull_h / 2), (0, bow_y0 + bow_len, -hull_h * 0.3),
             (-bow_hw, bow_y0, hull_h / 2), (bow_hw, bow_y0, hull_h / 2), (0, bow_y0 + bow_len, hull_h * 0.6)]
    faces = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    noncollide(tri_prism("%s_Bow" % prefix, bow_v, faces, TIMBER_LIGHT, coll, loc=(cx, cy, hull_cz)))
    mast_h = 0.36
    noncollide(box_c("%s_Mast" % prefix, (cx, cy, hull_cz + hull_h / 2 + mast_h / 2), (0.035, 0.035, mast_h),
                      BEAM_DARK, coll))
    sail_v = [(0, -0.008, 0), (0, -0.008, mast_h * 0.8), (mast_h * 0.55, -0.008, 0),
              (0, 0.008, 0), (0, 0.008, mast_h * 0.8), (mast_h * 0.55, 0.008, 0)]
    noncollide(tri_prism("%s_Sail" % prefix, sail_v, faces, TRIM_PALE, coll,
                          loc=(cx, cy, hull_cz + hull_h / 2 + 0.03)))


toy_boat("Story_ToyBoat", SIDETABLE_CX, SIDETABLE_CY + 0.25, SIDETABLE_SURF_Z, ST)

# Two books, a spread-open map and a jar of bait worms on the same side
# table, laid out to each other's side (not overlapping the boat).
_SB_X, _SB_Y = SIDETABLE_CX - 0.45, SIDETABLE_CY - 0.42
noncollide(box_c("Story_SideTable_Book_1", (_SB_X, _SB_Y, SIDETABLE_SURF_Z + 0.05), (0.32, 0.22, 0.09),
                  ROOF_GREEN, ST))
noncollide(box_c("Story_SideTable_Book_2", (_SB_X + 0.03, _SB_Y + 0.03, SIDETABLE_SURF_Z + 0.135), (0.28, 0.19, 0.07),
                  RUST, ST))

_MAP_X, _MAP_Y = SIDETABLE_CX + 0.15, SIDETABLE_CY - 0.4
noncollide(box_c("Story_Map_Paper", (_MAP_X, _MAP_Y, SIDETABLE_SURF_Z + 0.015), (0.65, 0.5, 0.02), PAPER, ST,
                  rot=(0, 0, math.radians(-7))))
noncollide(box_c("Story_Map_RouteLine", (_MAP_X - 0.05, _MAP_Y + 0.05, SIDETABLE_SURF_Z + 0.03), (0.4, 0.03, 0.01),
                  LAKE_BLUE, ST, rot=(0, 0, math.radians(18))))
noncollide(box_c("Story_Map_Marker", (_MAP_X + 0.15, _MAP_Y - 0.1, SIDETABLE_SURF_Z + 0.03), (0.07, 0.07, 0.015),
                  RUST, ST, rot=(0, 0, math.radians(45))))
for _wx, _wy in ((-0.28, -0.18), (0.26, 0.16)):
    noncollide(box_c("Story_Map_Weight_%d" % int((_wx + _wy) * 100), (_MAP_X + _wx, _MAP_Y + _wy,
                      SIDETABLE_SURF_Z + 0.04), (0.08, 0.08, 0.06), STONE, ST))

_JAR_X, _JAR_Y = SIDETABLE_CX + 0.58, SIDETABLE_CY
noncollide(cyl("Story_WormJar_Glass", (_JAR_X, _JAR_Y, SIDETABLE_SURF_Z + 0.2), 0.16, 0.17, 0.4, GLASS, ST, segs=12))
noncollide(cyl("Story_WormJar_Rim", (_JAR_X, _JAR_Y, SIDETABLE_SURF_Z + 0.405), 0.18, 0.18, 0.03, IRON, ST, segs=12))
noncollide(cyl("Story_WormJar_Dirt", (_JAR_X, _JAR_Y, SIDETABLE_SURF_Z + 0.14), 0.145, 0.145, 0.22, BEAM_DARK, ST,
                segs=12))
for _wi, (_wdx, _wdy) in enumerate(((-0.05, 0.03), (0.04, -0.05), (0.0, 0.06))):
    noncollide(cyl("Story_WormJar_Worm_%d" % (_wi + 1), (_JAR_X + _wdx, _JAR_Y + _wdy, SIDETABLE_SURF_Z + 0.27),
                    0.015, 0.015, 0.16, RUST, ST, segs=6,
                    rot=(math.radians(70 + _wi * 15), math.radians(_wi * 40), 0)))

# --------------------------------------------------------------------------
# 11. Deck + pier + boat (section 11)
# --------------------------------------------------------------------------

DK = GROUPS["Deck"]
PR = GROUPS["Pier"]

box("Deck_Surface", (CAB_X0, CAB_X1), (DECK_Y0, DECK_Y1), (-0.25, 0.0), TIMBER_MAIN, DK)
for i in range(18):
    y0 = DECK_Y0 + i * (DECK_Y1 - DECK_Y0) / 18
    y1 = DECK_Y0 + (i + 1) * (DECK_Y1 - DECK_Y0) / 18
    m = TIMBER_LIGHT if i % 2 == 0 else TIMBER_MAIN
    noncollide(box("Deck_Plank_%02d" % (i + 1), (CAB_X0, CAB_X1), (y0, y1), (0.0, 0.03), m, DK))
box("Deck_Joist_Edge_Front", (CAB_X0, CAB_X1), (DECK_Y0 - 0.1, DECK_Y0), (-0.25, -0.05), BEAM_DARK, DK)
box("Deck_Joist_Edge_Rear", (CAB_X0, CAB_X1), (DECK_Y1, DECK_Y1 + 0.1), (-0.25, -0.05), BEAM_DARK, DK)
for _dx in (CAB_X0 + 3, -6, 6, CAB_X1 - 3):
    box("Deck_Post_%d" % int(_dx), (_dx - 0.25, _dx + 0.25), (DECK_Y0 + 0.3, DECK_Y0 + 0.8), (-2.0, -0.25), BEAM_DARK, DK)

# Rail segments on safe outer edges only -- never across the pier mouth
# (PIER_X0..PIER_X1) or the rear-door approach / bank connections.
def rail_run(name, x0, x1, y, coll):
    for i, px in enumerate((x0, (x0 + x1) / 2, x1)):
        box("%s_Post_%d" % (name, i + 1), (px - 0.175, px + 0.175), (y - 0.175, y + 0.175), (0.0, 2.5), BEAM_DARK, coll)
    box("%s_RailLo" % name, (x0, x1), (y - 0.1, y + 0.1), (0.9, 1.15), TIMBER_LIGHT, coll)
    box("%s_RailHi" % name, (x0, x1), (y - 0.1, y + 0.1), (2.0, 2.25), TIMBER_LIGHT, coll)


rail_run("DeckRail_Left", CAB_X0, PIER_X0 - 0.3, DECK_Y1 - 0.15, DK)
rail_run("DeckRail_Right", PIER_X1 + 0.3, CAB_X1, DECK_Y1 - 0.15, DK)

# Pier stem: no rails, full 8-stud clear width maintained
box("Pier_Stem_Surface", (PIER_X0, PIER_X1), (PIER_Y0, PIER_Y1), (-0.3, 0.0), TIMBER_LIGHT, PR)
for i in range(16):
    y0 = PIER_Y0 + i * (PIER_Y1 - PIER_Y0) / 16
    y1 = PIER_Y0 + (i + 1) * (PIER_Y1 - PIER_Y0) / 16
    m = TIMBER_MAIN if i % 2 == 0 else TIMBER_LIGHT
    noncollide(box("Pier_Plank_%02d" % (i + 1), (PIER_X0, PIER_X1), (y0, y1), (0.0, 0.03), m, PR))
box("Pier_Joist_L", (PIER_X0 + 0.3, PIER_X0 + 0.5), (PIER_Y0, PIER_Y1), (-0.3, -0.05), BEAM_DARK, PR)
box("Pier_Joist_R", (PIER_X1 - 0.5, PIER_X1 - 0.3), (PIER_Y0, PIER_Y1), (-0.3, -0.05), BEAM_DARK, PR)
for _py in (PIER_Y0 + 1, PIER_Y0 + 5, (PIER_Y0 + PIER_Y1) / 2, PIER_Y1 - 5, PIER_Y1 - 1):
    for _px in (PIER_X0 + 0.3, PIER_X1 - 0.3):
        cyl("Pier_Pile_%d_%d" % (int(_px * 10), int(_py * 10)), (_px, _py, -2.0), 0.22, 0.22, 3.6, BEAM_DARK, PR, segs=8)

box("PierPlatform_Surface", (PLAT_X0, PLAT_X1), (PLAT_Y0, PLAT_Y1), (-0.3, 0.0), TIMBER_MAIN, PR)
for i in range(8):
    x0 = PLAT_X0 + i * (PLAT_X1 - PLAT_X0) / 8
    x1 = PLAT_X0 + (i + 1) * (PLAT_X1 - PLAT_X0) / 8
    m = TIMBER_LIGHT if i % 2 == 0 else TIMBER_MAIN
    noncollide(box("PierPlatform_Plank_%02d" % (i + 1), (x0, x1), (PLAT_Y0, PLAT_Y1), (0.0, 0.03), m, PR))
# Short corner rails only -- central pier-mouth connection and the full
# standing zone remain clear
rail_run("PierPlatform_RailBack", PLAT_X0 + 0.3, PLAT_X0 + 2.0, PLAT_Y1 - 0.15, PR)
rail_run("PierPlatform_RailBack2", PLAT_X1 - 2.0, PLAT_X1 - 0.3, PLAT_Y1 - 0.15, PR)
for _py in (PLAT_Y0 + 0.5, PLAT_Y1 - 0.5):
    for _px in (PLAT_X0 + 0.3, PLAT_X1 - 0.3):
        cyl("PierPlatform_Pile_%d_%d" % (int(_px * 10), int(_py * 10)), (_px, _py, -2.0), 0.22, 0.22, 3.6, BEAM_DARK,
            PR, segs=8)

# Pier props, on the +X side of the end platform only
_PP_X = PLAT_X1 - 0.9
noncollide(cyl("Pier_Bucket_Body", (_PP_X, PLAT_Y0 + 0.9, 0.5), 0.5, 0.45, 1.0, IRON, PR, segs=14))
noncollide(cyl("Pier_Bucket_Rim", (_PP_X, PLAT_Y0 + 0.9, 1.0), 0.52, 0.52, 0.08, IRON, PR, segs=14))
noncollide(box_c("Pier_Bucket_Handle", (_PP_X, PLAT_Y0 + 0.9, 1.3), (0.7, 0.06, 0.06), IRON, PR))
noncollide(box_c("Pier_Bucket_Fish", (_PP_X, PLAT_Y0 + 0.9, 0.15), (0.12, 0.45, 0.12), TRIM_PALE, PR))

box_c("Pier_Stool_Seat", (_PP_X, PLAT_Y0 + 2.0, 1.3), (0.9, 0.9, 0.12), TIMBER_LIGHT, PR)
for _lx, _ly in ((-0.3, -0.3), (0.3, -0.3), (-0.3, 0.3), (0.3, 0.3)):
    box_c("Pier_Stool_Leg_%d_%d" % (int(_lx * 10), int(_ly * 10)), (_PP_X + _lx, PLAT_Y0 + 2.0 + _ly, 0.62),
          (0.1, 0.1, 1.24), BEAM_DARK, PR)

# Propped pier rod, built end-to-end like the rack rods: the baseline shaft
# (centre Z=1.5) and grip (centre Z=0.4) had the same ~1.1-stud gap bug as
# the rack rods (Fix C). The line now actually starts at the rod tip and
# drops into the visible water just past the platform edge.
_pp_by, _pp_bz = PLAT_Y1 - 1.1, 0.15
_pp_ty, _pp_tz = PLAT_Y1 - 0.2, 2.5
_pp_grip_len = 0.5
_pp_psi0 = math.atan2(-(_pp_ty - _pp_by), _pp_tz - _pp_bz)
_pp_uy0, _pp_uz0 = -math.sin(_pp_psi0), math.cos(_pp_psi0)
_pp_gy, _pp_gz = _pp_by + _pp_uy0 * _pp_grip_len / 2, _pp_bz + _pp_uz0 * _pp_grip_len / 2
noncollide(cyl("Pier_PropRod_Grip", (_PP_X, _pp_gy, _pp_gz), 0.095, 0.08, _pp_grip_len, IRON, PR, segs=8,
                rot=(_pp_psi0, 0, 0)))
_pp_sy0, _pp_sz0 = _pp_by + _pp_uy0 * _pp_grip_len, _pp_bz + _pp_uz0 * _pp_grip_len
_pp_shaft_len = math.hypot(_pp_ty - _pp_sy0, _pp_tz - _pp_sz0)
noncollide(cyl("Pier_PropRod_Shaft", (_PP_X, (_pp_sy0 + _pp_ty) / 2, (_pp_sz0 + _pp_tz) / 2), 0.045, 0.02,
                _pp_shaft_len, BEAM_DARK, PR, segs=6, rot=(_pp_psi0, 0, 0)))
_pp_ly1, _pp_lz1 = _pp_ty + 0.5, _pp_tz - 3.0
_pp_line_len = math.hypot(_pp_ly1 - _pp_ty, _pp_lz1 - _pp_tz)
_pp_line_psi = math.atan2(-(_pp_ly1 - _pp_ty), _pp_lz1 - _pp_tz)
noncollide(cyl("Pier_PropRod_Line", (_PP_X, (_pp_ty + _pp_ly1) / 2, (_pp_tz + _pp_lz1) / 2), 0.02, 0.02,
                _pp_line_len, IRON, PR, segs=6, rot=(_pp_line_psi, 0, 0)))

for _ci, _cx in enumerate((PLAT_X0 + 0.5, PLAT_X1 - 0.5)):
    noncollide(box_c("Pier_MooringCleat_%d" % (_ci + 1), (_cx, PLAT_Y1 - 0.3, 0.1), (0.4, 0.2, 0.15), IRON, PR))
for _ri in range(3):
    noncollide(cyl("Pier_CoiledRope_Loop_%d" % (_ri + 1), (PLAT_X0 + 0.6, PLAT_Y1 - 0.6, 0.08 + _ri * 0.1),
                    0.35 - _ri * 0.05, 0.35 - _ri * 0.05, 0.06, TIMBER_LIGHT, PR, segs=12))

# Rowboat -- static prop, beside the pier platform, inside the lake
_BOAT_X, _BOAT_Y = PLAT_X0 - 2.2, PLAT_Y0 + 1.0
box_c("Rowboat_Hull", (_BOAT_X, _BOAT_Y, -0.3), (1.8, 3.8, 0.7), TIMBER_MAIN, PR)
noncollide(box_c("Rowboat_HullRim", (_BOAT_X, _BOAT_Y, 0.02), (1.9, 3.9, 0.1), BEAM_DARK, PR))
noncollide(box_c("Rowboat_Interior", (_BOAT_X, _BOAT_Y, -0.1), (1.5, 3.4, 0.35), BEAM_DARK, PR))
_bow_v = [(-0.9, 1.9, -0.35), (0.9, 1.9, -0.35), (0, 2.6, -0.1),
          (-0.9, 1.9, 0.35), (0.9, 1.9, 0.35), (0, 2.6, 0.2)]
noncollide(tri_prism("Rowboat_Bow", _bow_v,
                      [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)],
                      TIMBER_MAIN, PR, loc=(_BOAT_X, _BOAT_Y, -0.3)))
for _sy in (-0.8, 0.6):
    noncollide(box_c("Rowboat_BenchSeat_%d" % int(_sy * 10), (_BOAT_X, _BOAT_Y + _sy, 0.05), (1.4, 0.3, 0.1),
                      TIMBER_LIGHT, PR))
noncollide(box_c("Rowboat_Oar", (_BOAT_X + 0.6, _BOAT_Y - 0.3, 0.15), (0.08, 2.4, 0.06), TIMBER_LIGHT, PR,
                  rot=(0, 0, math.radians(12))))
noncollide(box_c("Rowboat_MooringRope", (_BOAT_X + 0.9, (_BOAT_Y + PLAT_Y0) / 2, 0.1),
                  (0.03, abs(PLAT_Y0 - _BOAT_Y), 0.03), TIMBER_LIGHT, PR))

# --------------------------------------------------------------------------
# 12. Lake + shoreline (section 12)
# --------------------------------------------------------------------------

LK = GROUPS["Lake"]

noncollide(box("Lake_Water_Surface", (WATER_X0, WATER_X1), (WATER_Y0, WATER_Y1), (-0.55, -0.5), LAKE_BLUE, LK))
box("Lake_Bed", (WATER_X0, WATER_X1), (WATER_Y0, WATER_Y1), (-1.1, -1.0), SAND, LK)
box("Shore_BankRing_Front", (WATER_X0 - 0.6, WATER_X1 + 0.6), (WATER_Y0 - 0.6, WATER_Y0), (-0.55, -0.1), SAND, LK)
box("Shore_BankRing_Left", (WATER_X0 - 0.6, WATER_X0), (WATER_Y0, WATER_Y1), (-0.55, -0.1), SAND, LK)
box("Shore_BankRing_Right", (WATER_X1, WATER_X1 + 0.6), (WATER_Y0, WATER_Y1), (-0.55, -0.1), SAND, LK)

_SHORE_PTS = ((-11.0, WATER_Y0 - 0.3), (-7.0, WATER_Y0 - 0.5), (9.0, WATER_Y0 - 0.4),
              (-12.0, WATER_Y1 - 1.0), (11.5, WATER_Y1 - 1.2))
for _ri, (_rx, _ry) in enumerate(_SHORE_PTS):
    _rs = 0.6 + (_ri % 3) * 0.3
    noncollide(bevel(box_c("Shore_Rock_%d" % (_ri + 1), (_rx, _ry, _rs * 0.3), (_rs, _rs * 0.9, _rs * 0.6),
                            STONE, LK), width=0.1, segments=2))

for _gi, (_gx, _gy) in enumerate(((-10.5, WATER_Y0 + 1.0), (8.0, WATER_Y0 + 1.5), (-8.0, WATER_Y1 - 1.5))):
    for _bi in range(5):
        _bx = _gx + (_bi - 2) * 0.25
        _bh = 1.2 + (_bi % 3) * 0.3
        noncollide(box_c("Reeds_%d_Blade_%d" % (_gi + 1, _bi + 1), (_bx, _gy, _bh / 2), (0.06, 0.06, _bh), FOLIAGE, LK,
                          rot=(math.radians(6 * (_bi - 2)), 0, 0)))
    noncollide(box_c("Reeds_%d_SeedHead" % (_gi + 1), (_gx, _gy, 1.3), (0.1, 0.1, 0.25), BEAM_DARK, LK))

# --------------------------------------------------------------------------
# 13. Yard (section 12 cont.)
# --------------------------------------------------------------------------

YD = GROUPS["Yard"]

# The baseline ground was ONE solid slab covering the entire property,
# including the lake footprint -- Lake_Water_Surface (top Z=-0.5) sat a
# full 0.5 studs *below* this ground's top (Z=0.0), so the water, bed and
# shore geometry from section 12 all existed but were completely hidden
# under opaque ground (Fix A). Partition the ground into four dry pieces
# that leave an open rectangle exactly matching the shore ring's outer
# footprint (WATER_*  +/- 0.6), so the lake is visible while every dry
# walking surface (front yard, both banks, the strip beyond the lake)
# stays solid and collidable, same as before.
_LAKE_CUT_X0, _LAKE_CUT_X1 = WATER_X0 - 0.6, WATER_X1 + 0.6
_LAKE_CUT_Y0, _LAKE_CUT_Y1 = WATER_Y0 - 0.6, WATER_Y1
# Front ground used to run all the way to _LAKE_CUT_Y0, including under
# the ENTIRE deck (X=CAB_X0..CAB_X1, Y=DECK_Y0..DECK_Y1) -- both the green
# ground and the wooden Deck_Surface/Deck_Plank strips sit with their top
# face at the exact same Z=0.0, so they z-fought/visibly crosshatched
# wherever the deck planking was thin enough to show the seam (Fix N:
# "входная часть... доски наслаиваются"). Stop the front ground short of
# the deck, and only re-cover the ground strips either SIDE of it (the
# deck itself already provides the walking surface in between).
box("Yard_Ground_Front", (PROP_X0, PROP_X1), (PROP_Y0, DECK_Y0), (-0.2, 0.0), GROUND, YD)
box("Yard_Ground_DeckFlankLeft", (PROP_X0, CAB_X0), (DECK_Y0, _LAKE_CUT_Y0), (-0.2, 0.0), GROUND, YD)
box("Yard_Ground_DeckFlankRight", (CAB_X1, PROP_X1), (DECK_Y0, _LAKE_CUT_Y0), (-0.2, 0.0), GROUND, YD)
# BankLeft/Right used to start at _LAKE_CUT_Y0 (11.9) across their FULL X
# range, but their inner edge (X=CAB_X0..-13.6 / 13.6..CAB_X1) sits inside
# the deck's own X span, so that corner (X -15..-13.6 / 13.6..15,
# Y 11.9..12, a 1.4x0.1 sliver) was still coplanar with Deck_Surface at
# Z=0.0 -- the same bug as Fix N, just a much smaller leftover corner.
# Split each bank piece so its deck-adjacent corner starts only after the
# deck ends (Y=DECK_Y1), closing that overlap too.
box("Yard_Ground_BankLeft_Outer", (PROP_X0, CAB_X0), (_LAKE_CUT_Y0, PROP_Y1), (-0.2, 0.0), GROUND, YD)
box("Yard_Ground_BankLeft_Inner", (CAB_X0, _LAKE_CUT_X0), (DECK_Y1, PROP_Y1), (-0.2, 0.0), GROUND, YD)
box("Yard_Ground_BankRight_Outer", (CAB_X1, PROP_X1), (_LAKE_CUT_Y0, PROP_Y1), (-0.2, 0.0), GROUND, YD)
box("Yard_Ground_BankRight_Inner", (_LAKE_CUT_X1, CAB_X1), (DECK_Y1, PROP_Y1), (-0.2, 0.0), GROUND, YD)
box("Yard_Ground_Rear", (_LAKE_CUT_X0, _LAKE_CUT_X1), (_LAKE_CUT_Y1, PROP_Y1), (-0.2, 0.0), GROUND, YD)
box("Yard_FrontPath_A", (LANE_X0, 0.0), (PROP_Y0, CAB_Y0), (0.0, 0.05), STONE, YD)
box("Yard_FrontPath_B", (0.0, LANE_X1), (PROP_Y0, CAB_Y0), (0.0, 0.05), SAND, YD)

_TREE_X, _TREE_Y = PROP_X0 + 2.5, Y(2.0)
box_c("Yard_Tree_Trunk", (_TREE_X, _TREE_Y, 2.0), (0.6, 0.6, 4.0), BEAM_DARK, YD)
for _ti, (_tz, _tr) in enumerate(((4.5, 1.5), (5.6, 1.1), (6.4, 0.7))):
    noncollide(cyl("Yard_Tree_Foliage_%d" % (_ti + 1), (_TREE_X, _TREE_Y, _tz), _tr, _tr * 0.15, 1.1, FOLIAGE, YD,
                    segs=10))

box_c("Yard_LogRack_Body", (CAB_X0 - 1.6, CAB_Y0 + 2.0, 0.9), (1.3, 3.0, 1.8), BEAM_DARK, YD)
for _li in range(7):
    noncollide(cyl("Yard_LogRack_Log_%d" % (_li + 1), (CAB_X0 - 1.6, CAB_Y0 + 0.6 + _li * 0.42, 1.0),
                    0.18, 0.18, 1.1, TIMBER_MAIN, YD, segs=8, rot=(0, math.radians(90), 0)))
box("Yard_LogRack_Roof", (CAB_X0 - 2.3, CAB_X0 - 0.9), (CAB_Y0 + 0.3, CAB_Y0 + 3.3), (1.85, 2.0), ROOF_GREEN, YD)


def fence_run(name, axis, a0, a1, fixed, coll):
    length = a1 - a0
    n = max(2, int(round(length / 4.2)) + 1)
    for i in range(n):
        a = a0 + i * length / (n - 1)
        if axis == 'X':
            box("%s_Post_%02d" % (name, i + 1), (a, a + 0.3), (fixed - 0.15, fixed + 0.15), (0.0, 2.2), TIMBER_MAIN,
                coll)
        else:
            box("%s_Post_%02d" % (name, i + 1), (fixed - 0.15, fixed + 0.15), (a, a + 0.3), (0.0, 2.2), TIMBER_MAIN,
                coll)
    for z0, z1 in ((0.7, 1.0), (1.6, 1.9)):
        if axis == 'X':
            box("%s_Rail" % name + "_%d" % int(z0 * 10), (a0, a1), (fixed - 0.08, fixed + 0.08), (z0, z1),
                TIMBER_LIGHT, coll)
        else:
            box("%s_Rail" % name + "_%d" % int(z0 * 10), (fixed - 0.08, fixed + 0.08), (a0, a1), (z0, z1),
                TIMBER_LIGHT, coll)


# Short FRONT/OUTER segments only -- entrance, both rear exits and both
# bank routes all remain clear (no gate across any exit).
fence_run("Fence_Front_L", 'X', PROP_X0, FRONT_DOOR_X0 - 3.0, PROP_Y0 + 0.3, YD)
fence_run("Fence_Front_R", 'X', FRONT_DOOR_X1 + 3.0, PROP_X1, PROP_Y0 + 0.3, YD)
fence_run("Fence_Outer_L", 'Y', PROP_Y0, BANK_Y0 - 1.0, PROP_X0 + 0.3, YD)
fence_run("Fence_Outer_R", 'Y', PROP_Y0, BANK_Y0 - 1.0, PROP_X1 - 0.3, YD)

# --------------------------------------------------------------------------
# 14. Reference helpers (section 13 -- design references only)
# --------------------------------------------------------------------------

HELPERS = {
    "DadSpawnPoint": DAD_REF,
    "FamilySpawn_01": FAM1_REF,
    "FamilySpawn_02": FAM2_REF,
    "FamilySpawn_03": FAM3_REF,
    "FrontEntrance": ((FRONT_DOOR_X0 + FRONT_DOOR_X1) / 2, CAB_Y0, 0.0),
    "RearEntrance": ((REAR_DOOR_X0 + REAR_DOOR_X1) / 2, CAB_Y1, 0.0),
    "BackyardExit_Left": ((EXIT_L_X0 + EXIT_L_X1) / 2, PROP_Y1, 0.0),
    "BackyardExit_Right": ((EXIT_R_X0 + EXIT_R_X1) / 2, PROP_Y1, 0.0),
    "PierBranch": (0.0, (PIER_Y0 + PIER_Y1) / 2, 0.0),
}
for hname, hloc in HELPERS.items():
    empty(hname, hloc)
for ob in GROUPS["ReferenceHelpers"].objects:
    ob.hide_render = True

# --------------------------------------------------------------------------
# 15. Preview cameras and neutral daylight
# --------------------------------------------------------------------------

world = bpy.data.worlds.new("LKC_Daylight")
SCENE.world = world
world.use_nodes = True
_bg = world.node_tree.nodes["Background"]
_bg.inputs[0].default_value = (0.70, 0.80, 0.84, 1.0)
_bg.inputs[1].default_value = 0.45

_sun_d = bpy.data.lights.new("LKC_Sun", 'SUN')
_sun_d.energy = 1.8
_sun_d.angle = math.radians(6)
_sun_d.color = (1.0, 0.97, 0.90)
SUN = bpy.data.objects.new("LKC_Sun", _sun_d)
SCENE.collection.objects.link(SUN)
SUN.rotation_euler = (math.radians(52), 0, math.radians(35))

_fill_d = bpy.data.lights.new("LKC_Fill", 'SUN')
_fill_d.energy = 0.5
_fill_d.angle = math.radians(30)
_fill_d.color = (0.88, 0.93, 1.0)
_fill_d.use_shadow = False
FILL = bpy.data.objects.new("LKC_Fill", _fill_d)
SCENE.collection.objects.link(FILL)
FILL.rotation_euler = (math.radians(60), 0, math.radians(-130))

CAM_D = bpy.data.cameras.new("LKC_PreviewCam")
CAM = bpy.data.objects.new("LKC_PreviewCam", CAM_D)
SCENE.collection.objects.link(CAM)
SCENE.camera = CAM

SCENE.render.engine = 'BLENDER_EEVEE'
SCENE.eevee.taa_render_samples = 48
SCENE.eevee.use_shadows = True
SCENE.eevee.use_raytracing = True
SCENE.render.image_settings.file_format = 'PNG'
SCENE.view_settings.view_transform = 'Standard'
SCENE.view_settings.exposure = 0.0

# --------------------------------------------------------------------------
# 16. Save, export, render, manifest
# --------------------------------------------------------------------------

EXPORT_GROUPS = ("Structure", "Roof", "Openings", "Kitchen", "FamilyLiving",
                 "SleepingAlcove", "FishingCorner", "Deck", "Pier", "Lake", "Yard", "StoryProps")


def mesh_objects():
    out = []
    for gname in EXPORT_GROUPS:
        out.extend([o for o in GROUPS[gname].objects if o.type == 'MESH'])
    return out


def tri_count():
    total = 0
    deps = bpy.context.evaluated_depsgraph_get()
    for ob in mesh_objects():
        me = ob.evaluated_get(deps).to_mesh()
        me.calc_loop_triangles()
        total += len(me.loop_triangles)
        ob.evaluated_get(deps).to_mesh_clear()
    return total


os.makedirs(os.path.join(OUT_DIR, "previews"), exist_ok=True)

BLEND_PATH = os.path.join(OUT_DIR, "LakesideCabinHouse.blend")
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("BUILD_SAVED_BLEND", BLEND_PATH)

FBX_PATH = os.path.join(OUT_DIR, "LakesideCabinHouse.fbx")
bpy.ops.object.select_all(action='DESELECT')
_sel = mesh_objects()
for ob in _sel:
    ob.select_set(True)
bpy.context.view_layer.objects.active = _sel[0]
FBX_SETTINGS = dict(
    use_selection=True,
    object_types={'MESH'},
    apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_UNITS',
    axis_forward='Z',
    axis_up='Y',
    mesh_smooth_type='FACE',
    use_mesh_modifiers=True,
    bake_anim=False,
    add_leaf_bones=False,
    path_mode='COPY',
    embed_textures=False,
)
bpy.ops.export_scene.fbx(filepath=FBX_PATH, **FBX_SETTINGS)
print("BUILD_EXPORTED_FBX", FBX_PATH)


def look_at(cam, loc, target, lens=40.0, ortho=None):
    cam.location = loc
    d = mathutils.Vector((target[0] - loc[0], target[1] - loc[1], target[2] - loc[2]))
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if ortho:
        cam.data.type, cam.data.ortho_scale = 'ORTHO', ortho
    else:
        cam.data.type, cam.data.lens = 'PERSP', lens


def shot(name, loc, target, res=(1600, 1100), lens=40.0, ortho=None, hide_roof=False):
    GROUPS["Roof"].hide_render = hide_roof
    look_at(CAM, loc, target, lens=lens, ortho=ortho)
    SCENE.render.resolution_x, SCENE.render.resolution_y = res
    SCENE.render.filepath = os.path.join(OUT_DIR, "previews", name)
    bpy.ops.render.render(write_still=True)
    GROUPS["Roof"].hide_render = False
    print("BUILD_RENDERED", name)


shot("front.png", (30.0, -42.0, 18.0), (0.0, -16.0, 6.0), lens=36)
shot("lake_side.png", (30.0, 26.0, 16.0), (0.0, 16.0, 2.0), lens=36)
shot("interior.png", (0.0, -26.0, 42.0), (0.0, -10.0, 1.0), lens=35, hide_roof=True)
shot("top.png", (0.0, 0.0, 85.0), (0.0, 0.0, 0.0), res=(1600, 1700), ortho=58.0, hide_roof=True)

# --- manifest -------------------------------------------------------------
GROUP_STATS = {}
for gname, coll in GROUPS.items():
    meshes = [o for o in coll.objects if o.type == 'MESH']
    GROUP_STATS[gname] = {"objects": len(coll.objects), "meshes": len(meshes)}

MANIFEST = {
    "asset": "LakesideCabinHouse",
    "variant": "LakesideCabinHouse_Final",
    "status": "FINAL, owner-accepted 2026-10-09 (built %s)" % "2026-10-09",
    "game": "Steal a Dad!",
    "note_on_working_name": "LakesideCabinHouse is a neutral asset name only. It does not "
                             "create or rename a Fisherman Dad character, change rarity, "
                             "or edit the Dad catalog.",
    "description": "A broad wooden fisherman's-cabin-style family home with an off-center "
                   "gable ridge, a longer roof slope on one side, deep eaves, exposed "
                   "end-frame beams, a wide lake-facing deck feeding an 8-wide pier, and "
                   "a small private lake with a static rowboat. Deliberately different "
                   "silhouette from RegularDadHouse_Final and OfficeDadHouse_Final.",
    "units": {
        "blender_unit_equals_roblox_studs": 1.0,
        "scene_unit_system": "METRIC",
        "scene_scale_length": 0.01,
        "note": "1 BU = 1 FBX centimetre = 1 Roblox stud, matching every other house asset.",
    },
    "orientation": {
        "front_direction": "-Y",
        "up_axis": "+Z (Blender)",
        "asset_origin": "(0, 0, 0) = ground level, centre of the property footprint",
        "ground_top_z": 0.0,
        "walking_surface_z": 0.0,
        "logical_to_blender": "Blender_X = logical X; Blender_Y = logical D - 24 "
                              "(D=0 front boundary -> Y=-24, D=48 lake boundary -> Y=+24); "
                              "Blender_Z = logical H.",
    },
    "dimensions_studs": {
        "property": {"width_x": PROP_W, "depth_y": PROP_D, "x": [PROP_X0, PROP_X1], "y": [PROP_Y0, PROP_Y1]},
        "cabin_footprint": {"width_x": CAB_X1 - CAB_X0, "depth_y": CAB_Y1 - CAB_Y0,
                            "x": [CAB_X0, CAB_X1], "y": [CAB_Y0, CAB_Y1], "wall_height": WALL_H,
                            "ridge_x": RIDGE_X, "ridge_height": RIDGE_H},
        "roof_overhang_envelope": {"x": [CAB_X0 - ROOF_OVH, CAB_X1 + ROOF_OVH], "y": [ROOF_D0, ROOF_D1],
                                   "left_run": _ROOF_RUN_L, "right_run": _ROOF_RUN_R},
        "wall_thickness": WALL_T,
        "front_entrance": {"clear_width": FRONT_DOOR_X1 - FRONT_DOOR_X0, "clear_height": DOOR_CLEAR_H,
                           "x": [FRONT_DOOR_X0, FRONT_DOOR_X1], "wall_y": FRONT_DOOR_Y},
        "rear_entrance": {"clear_width": REAR_DOOR_X1 - REAR_DOOR_X0, "clear_height": DOOR_CLEAR_H,
                          "x": [REAR_DOOR_X0, REAR_DOOR_X1], "wall_y": REAR_DOOR_Y},
        "backyard_exits": [{"name": "BackyardExit_Left", "x": [EXIT_L_X0, EXIT_L_X1],
                            "clear_width": EXIT_L_X1 - EXIT_L_X0, "boundary_y": PROP_Y1},
                           {"name": "BackyardExit_Right", "x": [EXIT_R_X0, EXIT_R_X1],
                            "clear_width": EXIT_R_X1 - EXIT_R_X0, "boundary_y": PROP_Y1}],
        "central_lane": {"x": [LANE_X0, LANE_X1], "y": [LANE_Y0, LANE_Y1], "clear_width": 8.0, "clear_height": 9.0},
        "rear_turn_area": {"x": [REAR_TURN_X0, REAR_TURN_X1], "y": [REAR_TURN_Y0, REAR_TURN_Y1]},
        "deck_apron": {"y": [DECK_Y0, DECK_Y1], "clear_depth": DECK_Y1 - DECK_Y0},
        "bank_routes": {"left": {"x": [BANK_L_X0, BANK_L_X1], "y": [BANK_Y0, BANK_Y1]},
                        "right": {"x": [BANK_R_X0, BANK_R_X1], "y": [BANK_Y0, BANK_Y1]}},
        "pier_stem": {"x": [PIER_X0, PIER_X1], "y": [PIER_Y0, PIER_Y1], "clear_width": PIER_X1 - PIER_X0,
                      "note": "No rails on the stem -- full 8-stud clear width."},
        "pier_platform": {"x": [PLAT_X0, PLAT_X1], "y": [PLAT_Y0, PLAT_Y1]},
        "water_envelope": {"x": [WATER_X0, WATER_X1], "y": [WATER_Y0, WATER_Y1],
                           "surface_z": -0.55, "bed_z": -1.0},
        "dad_standing_area": {"x": [DAD_X0, DAD_X1], "y": [DAD_Y0, DAD_Y1]},
    },
    "materials": {k: {"base_color_linear": list(v[0]), "alpha": v[1]} for k, v in sorted(MATERIALS.items())},
    "object_groups": GROUP_STATS,
    "counts": {"mesh_objects_exported": len(mesh_objects()), "triangles_exported": tri_count()},
    "reference_helpers": {k: {"location": list(v)} for k, v in HELPERS.items()},
    "collision_hint": {
        "walkable_and_structural": ["Structure", "Yard (ground, path, fences)", "Deck", "Pier (stem/platform/piles)",
                                    "Lake (bed, bank ring)"],
        "small_decorative": ["Kitchen", "FamilyLiving", "SleepingAlcove", "FishingCorner", "StoryProps furniture "
                             "carcasses stay collidable; small props are in noncollide_objects"],
        "noncollide_note": "All objects listed in noncollide_objects below are set CanCollide=false by "
                           "apply_lakeside_cabin_house_colors.luau -- door leaves/hardware, window panes, "
                           "shutters, mugs, books, reeds, the drawing/portraits, boots, rods, the toy boat, "
                           "the rowboat's rim/interior/oar/rope, the bucket, and similar small/parked props.",
        "water_flag_note": "Lake_Water_Surface is a decorative visual plane (CanCollide=false); it is NOT a "
                           "walkable floor and NOT a swim volume. Swimming/fall/NPC-in-water behavior is "
                           "UNVERIFIED and not implemented here.",
        "note": "Blender has no Roblox collision data. Set CanCollide/CollisionFidelity in Studio after "
                "import; this is only a grouping hint.",
    },
    "fbx_export_settings": {k: (sorted(v) if isinstance(v, set) else v) for k, v in FBX_SETTINGS.items()},
    "previews": ["previews/front.png", "previews/lake_side.png", "previews/interior.png", "previews/top.png"],
}

MANIFEST["object_materials"] = dict(sorted(OBJECT_MATERIAL.items()))
MANIFEST["noncollide_objects"] = sorted(NONCOLLIDE)

with open(os.path.join(OUT_DIR, "manifest.json"), "w", encoding="utf-8") as fh:
    json.dump(MANIFEST, fh, indent=2)
print("BUILD_MANIFEST_TRIS", MANIFEST["counts"]["triangles_exported"],
      "OBJECTS", MANIFEST["counts"]["mesh_objects_exported"], "NONCOLLIDE", len(NONCOLLIDE))

# --------------------------------------------------------------------------
# 17. Studio colour / anchor / collision script
# --------------------------------------------------------------------------


def srgb255(linear):
    out = []
    for v in linear:
        v = min(max(v, 0.0), 1.0)
        s = v * 12.92 if v <= 0.0031308 else 1.055 * (v ** (1 / 2.4)) - 0.055
        out.append(int(round(s * 255)))
    return out


ROBLOX_MATERIAL = {"LKC_Glass": "Glass"}

assert len(OBJECT_ORDER) == len(set(OBJECT_ORDER)), "duplicate object names"

_lines = [
    "--!strict",
    "-- Generated by build_lakeside_cabin_house.py -- do not edit by hand.",
    "--",
    "-- Roblox's FBX importer drops plain material colours, so every MeshPart of an",
    "-- imported LakesideCabinHouse arrives as default grey. Paste this into the Studio",
    "-- command bar (or run it as a Script once) after importing the FBX.",
    "",
    "local ANCHOR = true -- imported parts arrive unanchored; anchor them too",
    "",
    "local PALETTE: { [string]: { color: Color3, material: Enum.Material, transparency: number } } = {",
]
for mname in sorted(MATERIALS):
    rgb, alpha = MATERIALS[mname]
    r, g, b = srgb255(rgb)
    rmat = ROBLOX_MATERIAL.get(mname, "SmoothPlastic")
    _lines.append('\t["%s"] = { color = Color3.fromRGB(%d, %d, %d), material = Enum.Material.%s, '
                  'transparency = %s },' % (mname, r, g, b, rmat, round(1.0 - alpha, 2)))
_lines += ["}", "", "local PARTS: { [string]: string } = {"]
for oname in OBJECT_ORDER:
    _lines.append('\t["%s"] = "%s",' % (oname, OBJECT_MATERIAL[oname]))
_lines += ["}", "", "local NONCOLLIDE: { [string]: boolean } = {"]
for oname in sorted(NONCOLLIDE):
    _lines.append('\t["%s"] = true,' % oname)
_lines += [
    "}",
    "",
    "local model = workspace:FindFirstChild(\"LakesideCabinHouse\", true)",
    "assert(model, \"LakesideCabinHouse not found in Workspace -- import the FBX first\")",
    "",
    "local painted, noncollided, missed = 0, 0, {}",
    "for _, inst in ipairs(model:GetDescendants()) do",
    "\tif inst:IsA(\"BasePart\") then",
    "\t\tlocal entry = PALETTE[PARTS[inst.Name] or \"\"]",
    "\t\tif entry then",
    "\t\t\tinst.Color = entry.color",
    "\t\t\tinst.Material = entry.material",
    "\t\t\tinst.Transparency = entry.transparency",
    "\t\t\tif ANCHOR then inst.Anchored = true end",
    "\t\t\tif NONCOLLIDE[inst.Name] then",
    "\t\t\t\tinst.CanCollide = false",
    "\t\t\t\tnoncollided += 1",
    "\t\t\tend",
    "\t\t\tpainted += 1",
    "\t\telse",
    "\t\t\ttable.insert(missed, inst.Name)",
    "\t\tend",
    "\tend",
    "end",
    "",
    "print(string.format(\"LakesideCabinHouse: painted %d parts (%d set non-colliding), %d unmatched\", "
    "painted, noncollided, #missed))",
    "if #missed > 0 then",
    "\twarn(\"unmatched parts: \" .. table.concat(missed, \", \"))",
    "end",
    "",
]
LUAU_PATH = os.path.join(OUT_DIR, "apply_lakeside_cabin_house_colors.luau")
with open(LUAU_PATH, "w", encoding="utf-8") as fh:
    fh.write("\n".join(_lines))
print("BUILD_LUAU", LUAU_PATH, len(OBJECT_ORDER), "parts", len(NONCOLLIDE), "noncollide")

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("BUILD_DONE")
