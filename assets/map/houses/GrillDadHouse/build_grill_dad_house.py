"""Procedural build script for GrillDadHouse ("Steal a Dad!").

Single-storey family bungalow with chamfered front corners, cream walls, brick
accents, charcoal hip roof, brick chimney and a rear barbecue patio with a
hero grill that cooks exactly ONE tiny sausage.

Working asset name only -- this does not create or change any Dad character,
rarity or catalog entry.

Frame / units
-------------
1 Blender unit = 1 Roblox stud (scene scale_length 0.01 like the other houses).
Logical coordinates are (X, D, H): X left/right (left negative), D property
depth (front 0, rear 48), H height above the walking surface.
Blender (x, y, z) = (X, D - 24, H): the model pivot (0, 0, 0) is logical
(0, 24, 0), the centre of the property at walking height.

Run headless:
    blender -b --factory-startup --python build_grill_dad_house.py -- <output_dir>
"""

import json
import math
import os
import sys

import bmesh
import bpy
import mathutils

D_OFFSET = 24.0
ASSET = "GrillDadHouse"
PFX = "GDH"


def Y(d):
    """Logical depth D -> Blender Y."""
    return d - D_OFFSET


OUT_DIR = os.path.abspath(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else os.path.dirname(os.path.abspath(__file__))


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
HEX = {}


def srgb_to_linear(rgb255):
    out = []
    for v in rgb255:
        c = v / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


def mat(code, hexstr, rough=0.75, alpha=1.0):
    r, g, b = (int(hexstr[i:i + 2], 16) for i in (1, 3, 5))
    name = "%s_%s" % (PFX, code)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    lin = srgb_to_linear((r, g, b))
    bsdf.inputs["Base Color"].default_value = (*lin, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Specular IOR Level"].default_value = 0.15
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        m.surface_render_method = 'BLENDED'
    m.diffuse_color = (*lin, alpha)
    MATERIALS[name] = {"linear": lin, "srgb_hex": hexstr.upper(), "srgb255": (r, g, b), "alpha": alpha}
    HEX[code] = m
    return m


# Palette from the master prompt section 4 (target sRGB hex).
CREAM = mat("CREAM", "#E8DCC3")
TRIM = mat("TRIM", "#F3E9D6")
BRICK = mat("BRICK", "#B96843")
BRICK_DARK = mat("BRICK_DARK", "#8D4935")
MORTAR = mat("MORTAR", "#D2B99A")
ROOF = mat("ROOF", "#41454D")
ROOF_EDGE = mat("ROOF_EDGE", "#30343B")
WOOD = mat("WOOD", "#A87849")
WOOD_DARK = mat("WOOD_DARK", "#6B4B35")
PATIO = mat("PATIO", "#C98560")
PATIO_LIGHT = mat("PATIO_LIGHT", "#D99E77")
STONE = mat("STONE", "#B6B2A6")
IRON = mat("IRON", "#343A40", rough=0.55)
RED = mat("RED", "#B65E4D")
BLUE = mat("BLUE", "#789FAE")
GREEN = mat("GREEN", "#759650")
GREEN_DARK = mat("GREEN_DARK", "#486B43")
SAND = mat("SAND", "#CDBB94")
SILVER = mat("SILVER", "#A8AFB2", rough=0.4)
WHITE = mat("WHITE", "#F1EFE3")
BLACK = mat("BLACK", "#20252A")
GOLD = mat("GOLD", "#D7A342", rough=0.5)
SAUSAGE = mat("SAUSAGE", "#B87942")
GLASS = mat("GLASS", "#CFE3EA", rough=0.1, alpha=0.35)   # Roblox transparency 0.65

ROOT = bpy.data.collections.new(ASSET)
SCENE.collection.children.link(ROOT)
GROUPS = {}
for gname in ("Structure", "Roof", "Openings", "Living", "Kitchen", "Dining", "Preparation",
              "StoryProps", "Entry", "Patio", "Grill", "Garden", "Fence", "ReferenceHelpers"):
    c = bpy.data.collections.new(gname)
    ROOT.children.link(c)
    GROUPS[gname] = c

BOX_FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]

OBJECT_MATERIAL = {}
OBJECT_GROUP = {}
OBJECT_ORDER = []
NONCOLLIDE = set()
CUR = {"group": "Structure"}
REGISTRY_NOTES = {}


def G(name):
    CUR["group"] = name
    return GROUPS[name]


def _finish(name, verts, faces, material, loc=(0, 0, 0), rot=None, smooth=False):
    base = name
    n = 1
    while name in OBJECT_MATERIAL:
        n += 1
        name = "%s_%d" % (base, n)
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
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    if rot:
        ob.rotation_euler = rot
    GROUPS[CUR["group"]].objects.link(ob)
    OBJECT_MATERIAL[name] = material.name
    OBJECT_GROUP[name] = CUR["group"]
    OBJECT_ORDER.append(name)
    return ob


def nc(ob):
    NONCOLLIDE.add(ob.name)
    return ob


def corners(x0, x1, y0, y1, z0, z1):
    return [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
            (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]


def box(name, xs, ys, zs, material, coll=True):
    """Axis-aligned box in LOGICAL bounds: xs=(X0,X1), ys=(D0,D1), zs=(H0,H1)."""
    x0, x1 = sorted(xs)
    d0, d1 = sorted(ys)
    h0, h1 = sorted(zs)
    ob = _finish(name, corners(x0, x1, Y(d0), Y(d1), h0, h1), BOX_FACES, material)
    if not coll:
        nc(ob)
    return ob


def bc(name, c, size, material, coll=True, rotz=0.0):
    """Box by logical centre (X, D, H) and size (sx, sd, sh); optional rotation
    about the vertical axis (degrees, CCW seen from above)."""
    sx, sd, sh = size
    x, d, h = c
    pts = corners(-sx / 2, sx / 2, -sd / 2, sd / 2, -sh / 2, sh / 2)
    if rotz:
        a = math.radians(rotz)
        ca, sa = math.cos(a), math.sin(a)
        pts = [(px * ca - py * sa, px * sa + py * ca, pz) for px, py, pz in pts]
    ob = _finish(name, pts, BOX_FACES, material, loc=(x, Y(d), h))
    if not coll:
        nc(ob)
    return ob


def merged(name, boxes, material, coll=True):
    """One mesh from many axis-aligned logical boxes [(x0,x1,d0,d1,h0,h1), ...]."""
    verts, faces = [], []
    for (x0, x1, d0, d1, h0, h1) in boxes:
        o = len(verts)
        verts += corners(x0, x1, Y(d0), Y(d1), h0, h1)
        faces += [tuple(i + o for i in f) for f in BOX_FACES]
    ob = _finish(name, verts, faces, material)
    if not coll:
        nc(ob)
    return ob


def mesh_from(name, verts_xdh, faces, material, coll=True):
    """Arbitrary mesh from LOGICAL (X, D, H) vertices."""
    v = [(x, Y(d), h) for x, d, h in verts_xdh]
    ob = _finish(name, v, faces, material)
    if not coll:
        nc(ob)
    return ob


def prism_poly(name, pts, h0, h1, material, coll=True):
    """Extruded CONVEX polygon (X,D) points between heights h0..h1."""
    n = len(pts)
    # ensure CCW
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    if area < 0:
        pts = list(reversed(pts))
    v = [(x, d, h0) for x, d in pts] + [(x, d, h1) for x, d in pts]
    f = []
    for i in range(1, n - 1):
        f.append((0, i + 1, i))
        f.append((n, n + i, n + i + 1))
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, n + j, n + i))
    return mesh_from(name, v, f, material, coll)


def slab3(name, pts3, thick, material, coll=True):
    """Planar polygon facet (logical X,D,H points, CCW seen from above)
    extruded `thick` studs along its downward normal (roof panels)."""
    P = [mathutils.Vector((x, d, h)) for x, d, h in pts3]
    n = (P[1] - P[0]).cross(P[2] - P[0]).normalized()
    if n.z < 0:
        n = -n
    top = P
    bot = [p - n * thick for p in P]
    k = len(P)
    v = [(p.x, p.y, p.z) for p in top] + [(p.x, p.y, p.z) for p in bot]
    f = []
    for i in range(1, k - 1):
        f.append((0, i, i + 1))
        f.append((k, k + i + 1, k + i))
    for i in range(k):
        j = (i + 1) % k
        f.append((i, k + i, k + j, j))
    return mesh_from(name, v, f, material, coll)


def cyl(name, c, r_bot, r_top, h, material, coll=True, segs=12, h0_is_bottom=True):
    """Upright frustum; c=(X, D, H_bottom)."""
    x, d, hb = c
    v, f = [], []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        v.append((x + r_bot * math.cos(a), d + r_bot * math.sin(a), hb))
    for i in range(segs):
        a = 2 * math.pi * i / segs
        v.append((x + r_top * math.cos(a), d + r_top * math.sin(a), hb + h))
    for i in range(segs):
        j = (i + 1) % segs
        f.append((i, j, j + segs, i + segs))
    f.append(tuple(range(segs - 1, -1, -1)))
    f.append(tuple(range(segs, segs * 2)))
    return mesh_from(name, v, f, material, coll)


def hollow(name, c, r_bot, r_top, h, wall, bottom, material, coll=False, segs=12):
    """Open-top hollow frustum (bowl, mug, pot, dish): outer shell, inner
    cavity, rim, thick floor.  c=(X, D, H_bottom)."""
    x, d, hb = c
    ri_b, ri_t = max(r_bot - wall, 0.01), max(r_top - wall, 0.01)
    v, f = [], []

    def ring(r, hh):
        return [(x + r * math.cos(2 * math.pi * i / segs), d + r * math.sin(2 * math.pi * i / segs), hh)
                for i in range(segs)]
    ob_bot, ob_top = ring(r_bot, hb), ring(r_top, hb + h)
    in_top, in_bot = ring(ri_t, hb + h), ring(ri_b, hb + bottom)
    v = ob_bot + ob_top + in_top + in_bot
    S = segs
    for i in range(S):
        j = (i + 1) % S
        f.append((i, j, S + j, S + i))                       # outer wall
        f.append((S + i, S + j, 2 * S + j, 2 * S + i))        # rim
        f.append((2 * S + i, 2 * S + j, 3 * S + j, 3 * S + i))  # inner wall
    f.append(tuple(range(S - 1, -1, -1)))                      # outer bottom
    f.append(tuple(range(3 * S, 4 * S)))                       # inner floor
    return mesh_from(name, v, f, material, coll)


def bevel(ob, width=0.06, segments=1):
    m = ob.modifiers.new("Bevel", 'BEVEL')
    m.width = width
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(40)
    return ob


# ---- oriented-frame helpers ----------------------------------------------

def frame_box(name, origin, T, N, t0, t1, n0, n1, h0, h1, material, coll=True):
    """Box in a wall/leaf frame: origin (X,D), unit tangent T, unit normal N
    (2D), intervals along T, N and vertical h."""
    tc, nc_, hc = (t0 + t1) / 2, (n0 + n1) / 2, (h0 + h1) / 2
    cx = origin[0] + T[0] * tc + N[0] * nc_
    cd = origin[1] + T[1] * tc + N[1] * nc_
    ang = math.degrees(math.atan2(T[1], T[0]))
    return bc(name, (cx, cd, hc), (t1 - t0, n1 - n0, h1 - h0), material, coll, rotz=ang)


def frame_pt(origin, T, N, t, n):
    return (origin[0] + T[0] * t + N[0] * n, origin[1] + T[1] * t + N[1] * n)


FACE = {'-D': ((1, 0), (0, 1)), '+D': ((-1, 0), (0, -1)),
        '-X': ((0, -1), (1, 0)), '+X': ((0, 1), (-1, 0))}


class Basis:
    """Furniture basis: u along the front width, v from FRONT towards BACK,
    w upward; origin is the centre of the horizontal envelope at base height."""

    def __init__(self, X, D, face, H=0.0):
        self.X, self.D, self.face, self.H = X, D, face, H
        self.U, self.V = FACE[face]

    def pt(self, u, v):
        return (self.X + u * self.U[0] + v * self.V[0], self.D + u * self.U[1] + v * self.V[1])

    def box(self, name, u, v, w0, a, b, h, material, coll=True):
        X, D = self.pt(u, v)
        if self.U[0] != 0:
            sx, sd = a, b
        else:
            sx, sd = b, a
        return bc(name, (X, D, self.H + w0 + h / 2), (sx, sd, h), material, coll)

    def xz(self, name, f, u0, u1, v0, v1, h0, h1, material, coll=True):
        """Box whose 8 corners are mapped through f(u, v, w) -> (X, D, H)."""
        cs = corners(u0, u1, v0, v1, h0, h1)
        pts = [f(*c) for c in cs]
        ob = _finish(name, [(x, Y(d), h) for x, d, h in pts], BOX_FACES, material)
        if not coll:
            nc(ob)
        return ob

    def plain(self, u, v):
        return self.pt(u, v)


def unit(dx, dy):
    L = math.hypot(dx, dy)
    return (dx / L, dy / L)


# ==========================================================================
# 1. Shell: layout constants (section 5/6 of the master prompt)
# ==========================================================================

PROP_X0, PROP_X1, PROP_D0, PROP_D1 = -22.0, 22.0, 0.0, 48.0
WALL_T = 0.4
WALL_H = 11.5
PLATE_H = 0.3
POLY = [(-12, 4), (-5, 4), (-5, 5.2), (5, 5.2), (5, 4), (12, 4), (15, 7), (15, 30), (-15, 30), (-15, 7)]
FOOT = [(-12, 4), (12, 4), (15, 7), (15, 30), (-15, 30), (-15, 7)]      # convex footprint before the recess
EAVE = [(-12.6, 3), (12.6, 3), (15.8, 6.2), (15.8, 30.8), (-15.8, 30.8), (-15.8, 6.2)]
EAVE_H, RIDGE_H = 11.8, 16.4
RIDGE = ((-4.0, 17.0), (4.0, 17.0))
DOOR_W, DOOR_H = 8.4, 9.4
CH = 0.7071067811865476   # cos 45

# clearance record (measured/derived, reported in the manifest)
CLEAR = {}


def edge_frame(i):
    p0 = POLY[i]
    p1 = POLY[(i + 1) % len(POLY)]
    T = unit(p1[0] - p0[0], p1[1] - p0[1])
    N = (T[1], -T[0])                      # outward (polygon is CCW)
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    return p0, T, N, L


# apertures per polygon edge, in tangent coordinates (t0, t1, h0, h1, kind, tag)
DIAG = math.hypot(3, 3)
APERT = {
    0: [(1.0, 5.6, 3.4, 8.2, 'win', 'FrontL')],
    2: [(0.8, 9.2, 0.0, DOOR_H, 'door', 'Front')],
    4: [(1.4, 6.0, 3.4, 8.2, 'win', 'FrontR')],
    5: [(DIAG / 2 - 1.5, DIAG / 2 + 1.5, 3.4, 8.2, 'win', 'ChamferR')],
    6: [(5.5, 12.5, 4.4, 8.8, 'win', 'Right')],
    7: [(4.2, 9.2, 4.4, 8.8, 'win', 'RearR'), (10.8, 19.2, 0.0, DOOR_H, 'door', 'Rear'),
        (20.5, 27.5, 4.2, 8.6, 'win', 'RearL')],
    8: [(9.5, 16.5, 4.2, 8.6, 'win', 'Left')],
    9: [(DIAG / 2 - 1.5, DIAG / 2 + 1.5, 3.4, 8.2, 'win', 'ChamferL')],
}


# ==========================================================================
# 2. Tiles / clipped patterns
# ==========================================================================

def clip_poly(subject, clip):
    """Sutherland-Hodgman, convex CCW clip polygon."""
    out = subject
    n = len(clip)
    for i in range(n):
        a, b = clip[i], clip[(i + 1) % n]
        inp, out = out, []
        if not inp:
            break
        for j in range(len(inp)):
            p, q = inp[j], inp[(j + 1) % len(inp)]

            def side(pt):
                return (b[0] - a[0]) * (pt[1] - a[1]) - (b[1] - a[1]) * (pt[0] - a[0])
            sp, sq = side(p), side(q)
            if sp >= 0:
                out.append(p)
            if (sp >= 0) != (sq >= 0):
                tt = sp / (sp - sq)
                out.append((p[0] + (q[0] - p[0]) * tt, p[1] + (q[1] - p[1]) * tt))
    return out


def poly_area(p):
    return 0.5 * sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))


def merged_prisms(name, polys, h0, h1, material, coll=True):
    verts, faces = [], []
    for pts in polys:
        n = len(pts)
        if poly_area(pts) < 0:
            pts = list(reversed(pts))
        o = len(verts)
        verts += [(x, Y(d), h0) for x, d in pts] + [(x, Y(d), h1) for x, d in pts]
        for i in range(1, n - 1):
            faces.append((o, o + i + 1, o + i))
            faces.append((o + n, o + n + i, o + n + i + 1))
        for i in range(n):
            j = (i + 1) % n
            faces.append((o + i, o + j, o + n + j, o + n + i))
    ob = _finish(name, verts, faces, material)
    if not coll:
        nc(ob)
    return ob


def tile_pattern(prefix, x0, x1, d0, d1, pitch, gap, top, thick, base_mat, mat_a, mat_b,
                 rule, clip=None, coll=True, tile_h=0.04):
    """Base slab + two merged tile objects.  rule(row, col) -> True picks mat_b."""
    rect = [(x0, d0), (x1, d0), (x1, d1), (x0, d1)]
    base = clip if clip else rect
    prism_poly("%s_Base" % prefix, base, top - thick, top - tile_h, base_mat, coll)
    A, Bp = [], []
    nrow = int(math.ceil((d1 - d0) / pitch - 1e-9))
    ncol = int(math.ceil((x1 - x0) / pitch - 1e-9))
    for r in range(nrow):
        for c in range(ncol):
            xa, xb = x0 + c * pitch + gap / 2, min(x0 + (c + 1) * pitch, x1) - gap / 2
            da, db = d0 + r * pitch + gap / 2, min(d0 + (r + 1) * pitch, d1) - gap / 2
            cell = [(xa, da), (xb, da), (xb, db), (xa, db)]
            if clip:
                cell = clip_poly(cell, clip)
            if len(cell) < 3 or abs(poly_area(cell)) < 0.01:
                continue
            (Bp if rule(r, c) else A).append(cell)
    if A:
        merged_prisms("%s_TilesA" % prefix, A, top - tile_h, top, mat_a, coll)
    if Bp:
        merged_prisms("%s_TilesB" % prefix, Bp, top - tile_h, top, mat_b, coll)


# ==========================================================================
# 3. Structure
# ==========================================================================

G("Structure")
# floor slab: STONE base, top H=0, 0.30 thick including the 2x2 tile finish
tile_pattern("Structure_Floor", -15, 15, 4, 30, 2.0, 0.0, 0.0, 0.30, STONE, WHITE, STONE,
             lambda r, c: (r + c) % 2 == 0, clip=FOOT)
# supported recessed entry (floor stays under the notch)
box("Structure_Floor_EntryNotch", (-5, 5), (4, 5.2), (-0.30, 0.0), STONE)

# --- walls ---------------------------------------------------------------
for ei in range(len(POLY)):
    p0, T, N, L = edge_frame(ei)
    aps = sorted(APERT.get(ei, []))
    cur = 0.0
    k = 0
    for (t0, t1, h0, h1, kind, tag) in aps:
        if t0 - cur > 1e-6:
            k += 1
            frame_box("Structure_Wall_E%d_%02d" % (ei, k), p0, T, N, cur, t0, -WALL_T, 0.0, 0.0, WALL_H, CREAM)
        if h0 > 1e-6:
            k += 1
            frame_box("Structure_Wall_E%d_%02d" % (ei, k), p0, T, N, t0, t1, -WALL_T, 0.0, 0.0, h0, CREAM)
        k += 1
        frame_box("Structure_Wall_E%d_%02d" % (ei, k), p0, T, N, t0, t1, -WALL_T, 0.0, h1, WALL_H, CREAM)
        cur = t1
    if L - cur > 1e-6:
        k += 1
        frame_box("Structure_Wall_E%d_%02d" % (ei, k), p0, T, N, cur, L, -WALL_T, 0.0, 0.0, WALL_H, CREAM)
    # top plate band, continuous along the wall centreline, H 11.5..11.8
    frame_box("Structure_WallPlate_E%d" % ei, p0, T, N, 0.0, L, -WALL_T, 0.0, WALL_H, WALL_H + PLATE_H, WOOD_DARK)

# structural corner posts
for vi, (px, pd) in enumerate(POLY):
    ang = 0.0
    if vi in (5, 6):
        ang = 45.0
    elif vi in (9, 0):
        ang = -45.0
    bc("Structure_CornerPost_%02d" % (vi + 1), (px, pd, WALL_H / 2), (0.6, 0.6, WALL_H), TRIM, True, rotz=ang)


def frame_corners(origin, T, N, t0, t1, n0, n1, h0, h1):
    return [(*frame_pt(origin, T, N, t, n), h) for (t, n, h) in
            ((t0, n0, h0), (t1, n0, h0), (t1, n1, h0), (t0, n1, h0),
             (t0, n0, h1), (t1, n0, h1), (t1, n1, h1), (t0, n1, h1))]


def merged_frame(name, origin, T, N, boxes, material, coll=True):
    verts, faces = [], []
    for (t0, t1, n0, n1, h0, h1) in boxes:
        o = len(verts)
        verts += [(x, Y(d), h) for x, d, h in frame_corners(origin, T, N, t0, t1, n0, n1, h0, h1)]
        faces += [tuple(i + o for i in f) for f in BOX_FACES]
    ob = _finish(name, verts, faces, material)
    if not coll:
        nc(ob)
    return ob


# --- exterior brick base band ---------------------------------------------
for ei in range(len(POLY)):
    p0, T, N, L = edge_frame(ei)
    gaps = [(a[0] - 0.25, a[1] + 0.25) for a in APERT.get(ei, []) if a[4] == 'door']
    spans, cur = [], 0.0
    for g0, g1 in sorted(gaps):
        spans.append((cur, g0))
        cur = g1
    spans.append((cur, L))
    for (s0, s1) in spans:
        if s1 - s0 < 0.05:
            continue
        light, dark = [], []
        frame_box("Structure_BrickMortar_E%d_%d" % (ei, int(s0 * 10)), p0, T, N, s0, s1, 0.0, 0.10, 0.0, 1.4, MORTAR)
        for course in range(4):
            shift = 0.0 if course % 2 == 0 else 0.4
            hb0, hb1 = course * 0.35 + 0.0125, (course + 1) * 0.35 - 0.0125
            col = -1
            tpos = s0 - shift
            while tpos < s1:
                col += 1
                a, b = max(tpos + 0.0125, s0), min(tpos + 0.8 - 0.0125, s1)
                tpos += 0.8
                if b - a < 0.05:
                    continue
                (dark if (course + col) % 4 == 0 else light).append((a, b, 0.0, 0.12, hb0, hb1))
        if light:
            merged_frame("Structure_Brick_E%d_%d_Light" % (ei, int(s0 * 10)), p0, T, N, light, BRICK)
        if dark:
            merged_frame("Structure_Brick_E%d_%d_Dark" % (ei, int(s0 * 10)), p0, T, N, dark, BRICK_DARK)

# ==========================================================================
# 4. Roof, fascia, ridge, chimney
# ==========================================================================

G("Roof")
rb = (RIDGE[0][0], RIDGE[0][1], RIDGE_H), (RIDGE[1][0], RIDGE[1][1], RIDGE_H)
E = [(x, d, EAVE_H) for x, d in EAVE]
ROOF_T = 0.22
slab3("Roof_Hip_Front", [E[0], E[1], rb[1], rb[0]], ROOF_T, ROOF)
slab3("Roof_Hip_Rear", [E[3], E[4], rb[0], rb[1]], ROOF_T, ROOF)
slab3("Roof_Hip_Right", [E[2], E[3], rb[1]], ROOF_T, ROOF)
slab3("Roof_Hip_Left", [E[4], E[5], rb[0]], ROOF_T, ROOF)
slab3("Roof_Hip_ChamferR", [E[1], E[2], rb[1]], ROOF_T, ROOF)
slab3("Roof_Hip_ChamferL", [E[5], E[0], rb[0]], ROOF_T, ROOF)
for ei in range(len(EAVE)):
    a, b = EAVE[ei], EAVE[(ei + 1) % len(EAVE)]
    T = unit(b[0] - a[0], b[1] - a[1])
    N = (T[1], -T[0])
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    frame_box("Roof_Fascia_%02d" % (ei + 1), a, T, N, 0.0, L, -0.25, 0.0, EAVE_H - 0.45, EAVE_H, ROOF_EDGE)
box("Roof_Ridge_Cap", (RIDGE[0][0], RIDGE[1][0]), (17 - 0.175, 17 + 0.175), (RIDGE_H, RIDGE_H + 0.12), ROOF_EDGE)

CHIM_X, CHIM_D = 12.0, 28.4
box("Roof_Chimney_Body", (CHIM_X - 0.7, CHIM_X + 0.7), (CHIM_D - 0.7, CHIM_D + 0.7), (11.8, 17.6), BRICK)
bands = []
h = 11.8 + 0.35 * 2
while h < 17.6 - 0.2:
    bands.append((CHIM_X - 0.72, CHIM_X + 0.72, CHIM_D - 0.72, CHIM_D + 0.72, h, h + 0.35))
    h += 0.35 * 3
merged("Roof_Chimney_Bands", bands, BRICK_DARK)
box("Roof_Chimney_Cap", (CHIM_X - 0.85, CHIM_X + 0.85), (CHIM_D - 0.85, CHIM_D + 0.85), (17.6, 17.8), IRON)
box("Roof_Chimney_Opening", (CHIM_X - 0.35, CHIM_X + 0.35), (CHIM_D - 0.35, CHIM_D + 0.35), (17.8, 17.82), BLACK, False)

# ==========================================================================
# 5. Openings: windows and double doors
# ==========================================================================

G("Openings")


def window(tag, ei, t0, t1, h0, h1):
    p0, T, N, L = edge_frame(ei)
    A = t1 - t0
    nm = "Window_%s" % tag
    frame_box(nm + "_FrameLow", p0, T, N, t0 - 0.2, t1 + 0.2, 0.0, 0.18, h0 - 0.2, h0, TRIM)
    frame_box(nm + "_FrameHigh", p0, T, N, t0 - 0.2, t1 + 0.2, 0.0, 0.18, h1, h1 + 0.2, TRIM)
    frame_box(nm + "_FrameL", p0, T, N, t0 - 0.2, t0, 0.0, 0.18, h0, h1, TRIM)
    frame_box(nm + "_FrameR", p0, T, N, t1, t1 + 0.2, 0.0, 0.18, h0, h1, TRIM)
    frame_box(nm + "_Sill", p0, T, N, t0 - 0.25, t1 + 0.25, 0.0, 0.40, h0 - 0.45, h0 - 0.2, TRIM)
    nc(frame_box(nm + "_Glass", p0, T, N, t0, t1, -0.215, -0.185, h0, h1, GLASS, False))
    centers = [0.0] if A < 6.0 else [-A / 6.0, A / 6.0]
    for k, mc in enumerate(centers):
        tc = (t0 + t1) / 2 + mc
        frame_box("%s_Mullion_%d" % (nm, k + 1), p0, T, N, tc - 0.06, tc + 0.06, -0.30, -0.10, h0, h1, TRIM)


def door(tag, ei, t0, t1, h1):
    p0, T, N, L = edge_frame(ei)
    nm = "Door_%s" % tag
    fj = 0.25
    frame_box(nm + "_FrameL", p0, T, N, t0 - fj, t0, -WALL_T + 0.02, 0.10, 0.0, h1 + fj, WOOD_DARK)
    frame_box(nm + "_FrameR", p0, T, N, t1, t1 + fj, -WALL_T + 0.02, 0.10, 0.0, h1 + fj, WOOD_DARK)
    frame_box(nm + "_FrameHead", p0, T, N, t0 - fj, t1 + fj, -WALL_T + 0.02, 0.10, h1, h1 + fj, WOOD_DARK)
    nc(box_flat_threshold(nm, p0, T, N, t0, t1))
    leaf_w, leaf_t, ang = 4.05, 0.20, math.radians(110.0)
    for side, th, sgn in (("L", t0, +1), ("R", t1, -1)):
        hinge = frame_pt(p0, T, N, th, -0.2)
        # closed direction is sgn*T; open outward (towards +N) by 110 degrees
        d = (sgn * T[0] * math.cos(ang) + N[0] * math.sin(ang), sgn * T[1] * math.cos(ang) + N[1] * math.sin(ang))
        dn = unit(*d)
        pn = (-dn[1], dn[0])                       # perpendicular (rotate +90)
        name = "%s_Leaf%s" % (nm, side)
        # stiles/rails (WOOD) around the 2.6 x 6.2 glass opening (bottom H=1.8)
        parts = [("StileHinge", 0.0, 0.725, 0.1, 9.3), ("StileFree", 3.325, 4.05, 0.1, 9.3),
                 ("RailLow", 0.725, 3.325, 0.1, 1.8), ("RailHigh", 0.725, 3.325, 8.0, 9.3)]
        for pn_name, s0, s1, hh0, hh1 in parts:
            nc(frame_box("%s_%s" % (name, pn_name), hinge, dn, pn, s0, s1, -leaf_t / 2, leaf_t / 2, hh0, hh1, WOOD, False))
        nc(frame_box("%s_Glass" % name, hinge, dn, pn, 0.725, 3.325, -0.015, 0.015, 1.8, 8.0, GLASS, False))
        # hardware on the exterior face (faces away from the lane when open)
        nc(frame_box("%s_Pull" % name, hinge, dn, pn, 3.70 - 0.05, 3.70 + 0.05, -leaf_t / 2 - 0.35, -leaf_t / 2,
                     4.5 - 0.325, 4.5 + 0.325, IRON, False))
        for hh, tg in ((1.2, "Low"), (8.0, "High")):
            nc(frame_box("%s_Hinge%s" % (name, tg), hinge, dn, pn, 0.0, 0.12, -0.14, 0.14, hh - 0.09, hh + 0.09, IRON, False))
        # record the open leaf footprint for the protected-lane audit
        tip = (hinge[0] + dn[0] * leaf_w, hinge[1] + dn[1] * leaf_w)
        CLEAR.setdefault("door_leaf_tips", {})["%s_%s" % (nm, side)] = {
            "hinge_XD": [round(hinge[0], 3), round(hinge[1], 3)], "tip_XD": [round(tip[0], 3), round(tip[1], 3)],
            "dir": [round(dn[0], 4), round(dn[1], 4)]}


def box_flat_threshold(nm, p0, T, N, t0, t1):
    # flush threshold H=0 (thin, does not steal headroom)
    return frame_box(nm + "_Threshold", p0, T, N, t0, t1, -WALL_T, 0.0, -0.01, 0.0, STONE, False)


for ei, aps in APERT.items():
    for (t0, t1, h0, h1, kind, tag) in aps:
        if kind == 'win':
            window(tag, ei, t0, t1, h0, h1)
        else:
            door(tag, ei, t0, t1, h1)

G("Structure")


# ==========================================================================
# 6. Shared prop recipes (section 16 of the master prompt)
# ==========================================================================

def tilted_box(name, c, size, yaw, pitch, material, coll=False):
    """Box about its centre c=(X,D,H); pitch tilts the long (first) axis up."""
    L, W, T = size
    ya, pa = math.radians(yaw), math.radians(pitch)
    pts = []
    for (px, py, pz) in corners(-L / 2, L / 2, -W / 2, W / 2, -T / 2, T / 2):
        x1 = px * math.cos(pa) - pz * math.sin(pa)
        z1 = px * math.sin(pa) + pz * math.cos(pa)
        x2 = x1 * math.cos(ya) - py * math.sin(ya)
        y2 = x1 * math.sin(ya) + py * math.cos(ya)
        pts.append((c[0] + x2, Y(c[1] + y2), c[2] + z1))
    ob = _finish(name, pts, BOX_FACES, material)
    if not coll:
        nc(ob)
    return ob


def dish(name, X, D, H0, d, material=None, rim_h=0.06):
    return hollow(name, (X, D, H0), d / 2 * 0.78, d / 2, rim_h, 0.04, 0.02, material or WHITE, coll=False)


def plant(prefix, X, D, H0, pot_d, pot_h, total_h, n_leaves, leaf_lo, leaf_hi, pot_mat=None, leaf_mat=None, pot_segs=12):
    """Hollow pot, soil, short stem, N broad leaves from a common stem."""
    hollow("%s_Pot" % prefix, (X, D, H0), pot_d / 2, pot_d / 2 * 1.08, pot_h, 0.06, 0.06, pot_mat or PATIO, coll=False, segs=pot_segs)
    cyl("%s_Soil" % prefix, (X, D, H0 + pot_h - 0.08), pot_d / 2 - 0.06, pot_d / 2 - 0.06, 0.02, GREEN_DARK, False, segs=10)
    stem_h = max(total_h * 0.35, 0.1)
    box("%s_Stem" % prefix, (X - 0.025, X + 0.025), (D - 0.025, D + 0.025), (H0 + pot_h - 0.08, H0 + pot_h + stem_h), GREEN_DARK, False)
    for i in range(n_leaves):
        ang = i * 360.0 / n_leaves
        ln = leaf_lo + (leaf_hi - leaf_lo) * ((i * 37) % 10) / 9.0
        a = math.radians(ang)
        pitch = 35.0
        cx = X + math.cos(a) * ln * 0.5 * math.cos(math.radians(pitch))
        cd = D + math.sin(a) * ln * 0.5 * math.cos(math.radians(pitch))
        ch = H0 + pot_h + stem_h + ln * 0.5 * math.sin(math.radians(pitch))
        top_h = ch + 0.5 * ln * math.sin(math.radians(pitch))
        if top_h - H0 > total_h + pot_h * 0 + 1e-6 and total_h:
            ch -= (top_h - (H0 + total_h)) if top_h > H0 + total_h else 0
        tilted_box("%s_Leaf_%d" % (prefix, i + 1), (cx, cd, ch), (ln, ln * 0.35, 0.03), ang, pitch, leaf_mat or GREEN, False)


def table(prefix, X, D, W, L, T, top_t, mat_top=WOOD, mat_frame=WOOD_DARK, face='-D', apron=True):
    b = Basis(X, D, face)
    b.box("%s_Top" % prefix, 0, 0, T - top_t, W, L, top_t, mat_top)
    for sx in (-1, 1):
        for sv in (-1, 1):
            b.box("%s_Leg_%s%s" % (prefix, 'L' if sx < 0 else 'R', 'F' if sv < 0 else 'B'),
                  sx * (W / 2 - 0.30), sv * (L / 2 - 0.30), 0.0, 0.20, 0.20, T - top_t, mat_frame)
    if apron:
        ah = 0.25
        wz = T - top_t - ah
        for sv, nm in ((-1, "Front"), (1, "Back")):
            b.box("%s_Apron_%s" % (prefix, nm), 0, sv * (L / 2 - 0.30), wz, W - 0.60 - 0.20, 0.10, ah, mat_frame)
        for sx, nm in ((-1, "L"), (1, "R")):
            b.box("%s_Apron_%s" % (prefix, nm), sx * (W / 2 - 0.30), 0, wz, 0.10, L - 0.60 - 0.20, ah, mat_frame)
    return b


def chair(prefix, X, D, face, seat_mat):
    """1.3 x 1.4 x 2.9 chair (recipe): legs, seat, uprights, two back rails."""
    b = Basis(X, D, face)
    for sx in (-1, 1):
        for sv in (-1, 1):
            b.box("%s_Leg_%s%s" % (prefix, 'L' if sx < 0 else 'R', 'F' if sv < 0 else 'B'),
                  sx * 0.48, sv * 0.52, 0.0, 0.13, 0.13, 1.20, WOOD)
    b.box("%s_Seat" % prefix, 0, -0.05, 1.20, 1.30, 1.20, 0.15, seat_mat)
    for sx in (-1, 1):
        b.box("%s_Upright_%s" % (prefix, 'L' if sx < 0 else 'R'), sx * 0.48, 0.52, 1.35, 0.13, 0.13, 1.55, WOOD)
    b.box("%s_BackRailLow" % prefix, 0, 0.52, 1.79, 1.05, 0.12, 0.22, WOOD)
    b.box("%s_BackRailHigh" % prefix, 0, 0.52, 2.59, 1.05, 0.12, 0.22, WOOD)
    return b


def upholstered_sofa(prefix, W, L, X, D, face, n_seat, loose):
    """SOFA recipe.  loose = [(u, v, material), ...] loose cushions."""
    b = Basis(X, D, face)
    for sx in (-1, 1):
        for sv in (-1, 1):
            b.box("%s_Foot_%s%s" % (prefix, 'L' if sx < 0 else 'R', 'F' if sv < 0 else 'B'),
                  sx * (W / 2 - 0.35), sv * (L / 2 - 0.35), 0.0, 0.18, 0.18, 0.25, WOOD_DARK)
    b.box("%s_Frame" % prefix, 0, 0, 0.25, W, L, 0.35, WOOD_DARK)
    bevel(b.box("%s_Base" % prefix, 0, 0, 0.60, W - 0.08, L - 0.08, 0.45, CREAM), 0.1, 2)
    for sx in (-1, 1):
        bevel(b.box("%s_Arm_%s" % (prefix, 'L' if sx < 0 else 'R'), sx * (W / 2 - 0.225), 0, 0.60, 0.45, L, 1.65, CREAM), 0.1, 2)
    bevel(b.box("%s_Back" % prefix, 0, L / 2 - 0.15, 1.05, W - 0.90, 0.30, 2.05, CREAM), 0.1, 2)
    usable = W - 0.90
    cw = (usable - (n_seat - 1) * 0.04) / n_seat
    for k in range(n_seat):
        uc = -usable / 2 + cw / 2 + k * (cw + 0.04)
        nc(bevel(b.box("%s_SeatCushion_%d" % (prefix, k + 1), uc, -0.10, 1.05, cw, L - 0.48, 0.30, CREAM), 0.08, 2))
    s, c = math.sin(math.radians(12)), math.cos(math.radians(12))
    for k, (uc, vc, m) in enumerate(loose):
        def f(u, v, w, uc=uc, vc=vc):
            dv, dw = v * c + w * s, -v * s + w * c
            X2, D2 = b.pt(uc + u, vc + dv)
            return (X2, D2, 1.85 + dw)
        nc(bevel(b.xz("%s_LooseCushion_%d" % (prefix, k + 1), f, -0.425, 0.425, -0.125, 0.125, -0.425, 0.425, m, False), 0.05, 1))
    return b


# ==========================================================================
# 7.1 Living area, left side
# ==========================================================================

G("Living")
upholstered_sofa("Sofa_Rear", 6.6, 2.2, -10.0, 24.5, '-D', 3, [(-2.25, 0.58, GREEN_DARK), (2.25, 0.58, RED)])
upholstered_sofa("Sofa_Side", 4.6, 2.0, -6.2, 18.5, '-X', 2, [(-1.20, 0.50, SAND), (1.20, 0.50, BLUE)])

table("CoffeeTable", -10.0, 19.7, 3.6, 2.2, 1.6, 0.16)
plant("CoffeePlant", -10.8, 19.5, 1.6, 0.30, 0.30, 0.35, 5, 0.25, 0.40)
hollow("CoffeeFruitBowl", (-9.4, 19.7, 1.6), 0.25, 0.30, 0.18, 0.05, 0.03, WHITE, coll=False)
for k, (fx, fd, fh, dm, m) in enumerate(((-0.12, -0.05, 0.17, 0.22, RED), (0.10, -0.04, 0.16, 0.20, GREEN), (0.0, 0.12, 0.17, 0.18, GOLD))):
    cyl("CoffeeFruit_%d" % (k + 1), (-9.4 + fx, 19.7 + fd, 1.6 + fh - dm / 2 + 0.01), dm / 2, dm / 2 * 0.8, dm, m, False, segs=8)

# living rug: SAND centre with 0.25 STONE border, flat, noncollide
rx, rd, rw, rl = -10.0, 20.2, 8.4, 8.8
nc(box("Rug_Living_Centre", (rx - rw / 2 + 0.25, rx + rw / 2 - 0.25), (rd - rl / 2 + 0.25, rd + rl / 2 - 0.25), (0.0, 0.02), SAND, False))
for nm, xs, ds in (("N", (rx - rw / 2, rx + rw / 2), (rd + rl / 2 - 0.25, rd + rl / 2)),
                   ("S", (rx - rw / 2, rx + rw / 2), (rd - rl / 2, rd - rl / 2 + 0.25)),
                   ("W", (rx - rw / 2, rx - rw / 2 + 0.25), (rd - rl / 2 + 0.25, rd + rl / 2 - 0.25)),
                   ("E", (rx + rw / 2 - 0.25, rx + rw / 2), (rd - rl / 2 + 0.25, rd + rl / 2 - 0.25))):
    box("Rug_Living_Border_%s" % nm, xs, ds, (0.0, 0.02), STONE, False)

# TV cabinet (local W=5 along D, L=1.5 along X, T=1.7), faces +X
tvc = Basis(-13.65, 17.0, '+X')
for sx in (-1, 1):
    for sv in (-1, 1):
        tvc.box("TVCabinet_Foot_%s%s" % ('A' if sx < 0 else 'B', 'F' if sv < 0 else 'B'), sx * 2.2, sv * 0.55, 0.0, 0.12, 0.12, 0.12, WOOD_DARK)
tvc.box("TVCabinet_Top", 0, 0, 1.55, 5.0, 1.5, 0.15, WOOD)
tvc.box("TVCabinet_Bottom", 0, 0, 0.12, 5.0, 1.5, 0.12, WOOD)
for sx in (-1, 1):
    tvc.box("TVCabinet_Side_%s" % ('A' if sx < 0 else 'B'), sx * 2.44, 0, 0.24, 0.12, 1.5, 1.31, WOOD)
tvc.box("TVCabinet_Back", 0, 0.71, 0.24, 4.76, 0.08, 1.31, WOOD)
tvc.box("TVCabinet_Shelf", 0, 0, 0.80, 4.76, 1.4, 0.10, WOOD)
for sx in (-1, 1):
    tvc.box("TVCabinet_Divider_%s" % ('A' if sx < 0 else 'B'), sx * 0.825, -0.7, 0.24, 0.10, 0.06, 1.31, WOOD_DARK)
tvc.box("TVCabinet_PanelClosed", 1.65, -0.72, 0.24, 1.50, 0.06, 1.31, WOOD)
tvc.box("TVCabinet_Handle", 1.0, -0.78, 0.8, 0.08, 0.06, 0.35, IRON, False)
# TV: screen 4.2 along D x 0.18 along X x 2.5 tall, base H 1.85
tvb = Basis(-13.45, 17.0, '+X')
tvb.box("TV_Stand_L", -1.25, 0, 1.70, 0.30, 0.18, 0.15, IRON)
tvb.box("TV_Stand_R", 1.25, 0, 1.70, 0.30, 0.18, 0.15, IRON)
tvb.box("TV_Frame", 0, 0, 1.85, 4.2, 0.18, 2.5, IRON)
nc(tvb.box("TV_Display", 0, -0.09 - 0.01, 1.97, 3.96, 0.03, 2.26, BLACK, False))

# floor lamp (-13.3, 26.8)
cyl("FloorLamp_Base", (-13.3, 26.8, 0.0), 0.25, 0.25, 0.08, WOOD_DARK, True, segs=10)
cyl("FloorLamp_Stem", (-13.3, 26.8, 0.08), 0.05, 0.05, 3.72, WOOD_DARK, False, segs=6)
nc(hollow("FloorLamp_Shade", (-13.3, 26.8, 3.8), 0.40, 0.225, 0.7, 0.03, 0.0, WHITE, False, segs=10))

# storage shelf (local W=2.8 along D, L=1.2 along X, T=3.8) faces +X
sh = Basis(-13.65, 11.0, '+X')
for sx in (-1, 1):
    sh.box("Shelf_Side_%s" % ('A' if sx < 0 else 'B'), sx * 1.34, 0, 0.0, 0.12, 1.2, 3.8 - 0.12, WOOD)
sh.box("Shelf_Back", 0, 0.56, 0.0, 2.56, 0.08, 3.8, WOOD)
for lvl, tp in (("Low", 1.1), ("Mid", 2.3), ("Top", 3.8)):
    sh.box("Shelf_Board_%s" % lvl, 0, 0, tp - 0.12, 2.8, 1.2, 0.12, WOOD)
for k, (uc, cov) in enumerate(((-0.65, RED), (-0.35, BLUE), (-0.05, GREEN))):
    nm = "Book_%d" % (k + 1)
    sh.box(nm + "_CoverA", uc - 0.095, -0.25, 1.1, 0.03, 0.50, 0.70, cov, False)
    sh.box(nm + "_CoverB", uc + 0.095, -0.25, 1.1, 0.03, 0.50, 0.70, cov, False)
    sh.box(nm + "_Spine", uc, -0.25 + 0.235, 1.1, 0.22, 0.03, 0.70, cov, False)
    sh.box(nm + "_Pages", uc, -0.25 - 0.015, 1.13, 0.16, 0.44, 0.64, WHITE, False)
# basket 0.65 x 0.80 x 0.55 on H=2.3 at u=0.60, v=-0.10
bu, bv = 0.60, -0.10
sh.box("Basket_Bottom", bu, bv, 2.3, 0.65, 0.80, 0.06, SAND, False)
for nm, du, dv, a, bb in (("Front", 0, -0.36, 0.65, 0.08), ("Back", 0, 0.36, 0.65, 0.08), ("L", -0.285, 0, 0.08, 0.64), ("R", 0.285, 0, 0.08, 0.64)):
    sh.box("Basket_Wall_%s" % nm, bu + du, bv + dv, 2.36, a, bb, 0.49, SAND, False)
for k, hh in enumerate((2.5, 2.7)):
    sh.box("Basket_Band_%d" % (k + 1), bu, bv - 0.405, hh, 0.66, 0.02, 0.10, WOOD, False)

# toys outside lanes -- ~2.2x the first pass (car 1.32 long), clear of shelf, TV cabinet and family pads
CAR_X, CAR_D = -12.4, 13.0
toy = Basis(CAR_X, CAR_D, '-D')
toy.box("ToyCar_Body", 0, 0, 0.22, 1.32, 0.75, 0.22, RED, False)
toy.box("ToyCar_Cabin", 0.05, 0.0, 0.44, 0.62, 0.66, 0.22, BLUE, False)
toy.box("ToyCar_Bumper", 0, -0.40, 0.22, 1.1, 0.06, 0.12, WHITE, False)
for sx in (-1, 1):
    for sv in (-1, 1):
        cx, cd = CAR_X + sx * 0.46, CAR_D + sv * 0.40
        vv, ff = [], []
        for side in (-0.08, 0.08):
            for i in range(10):
                a = 2 * math.pi * i / 10
                vv.append((cx + side, cd + 0.14 * math.cos(a), 0.14 + 0.14 * math.sin(a)))
        for i in range(10):
            j = (i + 1) % 10
            ff.append((i, j, j + 10, i + 10))
        ff.append(tuple(range(9, -1, -1)))
        ff.append(tuple(range(10, 20)))
        mesh_from("ToyCar_Wheel_%s%s" % ('A' if sx < 0 else 'B', 'F' if sv < 0 else 'B'), vv, ff, BLACK, False)
for k, (bx_, bd_, m) in enumerate(((-12.5, 11.6, GOLD), (-11.8, 11.7, BLUE), (-12.15, 12.3, RED))):
    bevel(box("ToyBlock_%d" % (k + 1), (bx_ - 0.28, bx_ + 0.28), (bd_ - 0.28, bd_ + 0.28), (0.0, 0.56), m, False), 0.06, 1)

# ==========================================================================
# 7.2 Kitchen, right front / middle
# ==========================================================================

G("Kitchen")
# refrigerator: local W=2.2 along D, L=2.4 along X, T=5.8, faces -X
fr = Basis(13.4, 8.8, '-X')
for sx in (-1, 1):
    for sv in (-1, 1):
        fr.box("Fridge_Foot_%s%s" % ('A' if sx < 0 else 'B', 'F' if sv < 0 else 'B'), sx * 0.95, sv * 1.0, 0.0, 0.08, 0.08, 0.08, IRON)
bevel(fr.box("Fridge_Body", 0, 0.04, 0.08, 2.2, 2.3, 5.64, SILVER), 0.06, 1)
bevel(fr.box("Fridge_DoorLow", 0, -1.17, 0.15, 2.1, 0.08, 3.71, SILVER), 0.04, 1)
bevel(fr.box("Fridge_DoorHigh", 0, -1.17, 3.94, 2.1, 0.08, 1.78, SILVER), 0.04, 1)
fr.box("Fridge_Seam", 0, -1.20, 3.86, 2.1, 0.03, 0.05, BLACK, False)
for k, hc in enumerate((3.30, 4.45)):
    fr.box("Fridge_Handle_%d" % (k + 1), -0.70, -1.27, hc - 0.325, 0.10, 0.10, 0.65, SILVER, False)

# counter cabinet: W=6 along D, L=1.8 along X, T=3, faces -X, base (13.7, 14)
kc = Basis(13.7, 14.0, '-X')
SINK_X, SINK_D = 13.7, 12.3
kc.box("Kitchen_Counter_ToeKick", 0, -0.04, 0.0, 5.8, 1.5, 0.12, WOOD_DARK)
kc.box("Kitchen_Counter_Base", 0, 0.04, 0.12, 5.8, 1.5, 0.12, SAND)
for i, uc in enumerate((-3.0 + 0.06, -1.0, 1.0, 3.0 - 0.06)):
    kc.box("Kitchen_Counter_Divider_%d" % (i + 1), uc, 0, 0.24, 0.12, 1.7, 2.58, SAND)
kc.box("Kitchen_Counter_Back", 0, 0.84, 0.24, 6.0, 0.08, 2.58, SAND)
# front panels (3 bays of 2.0 along D), fronts at v=-L/2 = -0.9
for k, uc in enumerate((-2.0, 0.0, 2.0)):
    if k == 0:
        kc.box("Kitchen_Counter_Drawer_1", uc, -0.93, 2.28, 1.8, 0.06, 0.45, WOOD, False)
        kc.box("Kitchen_Counter_Door_1", uc, -0.93, 0.30, 1.8, 0.06, 1.90, WOOD, False)
        kc.box("Kitchen_Counter_Handle_Drawer", uc, -1.00, 2.45, 0.35, 0.08, 0.07, IRON, False)
        kc.box("Kitchen_Counter_Handle_1", uc + 0.7, -1.00, 1.7, 0.35, 0.08, 0.07, IRON, False)
    else:
        kc.box("Kitchen_Counter_Door_%d" % (k + 1), uc, -0.93, 0.30, 1.8, 0.06, 2.4, WOOD, False)
        kc.box("Kitchen_Counter_Handle_%d" % (k + 1), uc + 0.7, -1.00, 1.7, 0.35, 0.08, 0.07, IRON, False)
# countertop (0.18 thick, top H=3.0) with a REAL sink opening: world centre (13.7,12.3), clear 1.09 x 0.89
ct_x0, ct_x1 = 13.7 - 0.9, 13.7 + 0.9
ct_d0, ct_d1 = 11.0, 17.0
hole_x0, hole_x1 = SINK_X - 0.545, SINK_X + 0.545
hole_d0, hole_d1 = SINK_D - 0.445, SINK_D + 0.445
for nm, xs, ds in (("D0", (ct_x0, ct_x1), (ct_d0, hole_d0)), ("D1", (ct_x0, ct_x1), (hole_d1, ct_d1)),
                   ("X0", (ct_x0, hole_x0), (hole_d0, hole_d1)), ("X1", (hole_x1, ct_x1), (hole_d0, hole_d1))):
    box("Kitchen_Countertop_%s" % nm, xs, ds, (2.82, 3.0), WOOD)
# sink: rim strips 0.08 wide top H=3.04 thick 0.05, walls 0.04 down to 2.72, bottom 0.04
for nm, xs, ds in (("N", (SINK_X - 0.625, SINK_X + 0.625), (SINK_D + 0.445, SINK_D + 0.525)),
                   ("S", (SINK_X - 0.625, SINK_X + 0.625), (SINK_D - 0.525, SINK_D - 0.445)),
                   ("W", (SINK_X - 0.625, SINK_X - 0.545), (SINK_D - 0.445, SINK_D + 0.445)),
                   ("E", (SINK_X + 0.545, SINK_X + 0.625), (SINK_D - 0.445, SINK_D + 0.445))):
    box("Kitchen_Sink_Rim_%s" % nm, xs, ds, (2.99, 3.04), SILVER)
for nm, xs, ds in (("N", (hole_x0, hole_x1), (hole_d1 - 0.04, hole_d1)), ("S", (hole_x0, hole_x1), (hole_d0, hole_d0 + 0.04)),
                   ("W", (hole_x0, hole_x0 + 0.04), (hole_d0, hole_d1)), ("E", (hole_x1 - 0.04, hole_x1), (hole_d0, hole_d1))):
    box("Kitchen_Sink_Wall_%s" % nm, xs, ds, (2.72, 3.0), SILVER)
box("Kitchen_Sink_Bottom", (hole_x0, hole_x1), (hole_d0, hole_d1), (2.68, 2.72), SILVER)
# faucet: riser (14.2,12.3) H 3.04..3.69, connected spout to (13.85,12.3,3.64), control at (14.2,12.55)
box("Kitchen_Faucet_Riser", (14.2 - 0.04, 14.2 + 0.04), (12.3 - 0.04, 12.3 + 0.04), (3.04, 3.69), SILVER)
box("Kitchen_Faucet_Spout", (13.85 - 0.04, 14.2 + 0.04), (12.3 - 0.04, 12.3 + 0.04), (3.60, 3.68), SILVER)
box("Kitchen_Faucet_Nozzle", (13.85 - 0.04, 13.85 + 0.04), (12.3 - 0.04, 12.3 + 0.04), (3.52, 3.68), SILVER)
cyl("Kitchen_Faucet_Control", (14.2, 12.55, 3.04), 0.06, 0.06, 0.12, SILVER, False, segs=8)
# hob + pan
box("Kitchen_Hob_Plate", (13.7 - 0.65, 13.7 + 0.65), (15.2 - 0.625, 15.2 + 0.625), (3.0, 3.08), IRON)
for k, dd in enumerate((14.9, 15.5)):
    cyl("Kitchen_Hob_Burner_%d" % (k + 1), (13.7, dd, 3.08), 0.19, 0.19, 0.02, BLACK, False, segs=12)
for k, dd in enumerate((14.9, 15.5)):
    cyl("Kitchen_Hob_Control_%d" % (k + 1), (13.25, dd, 3.08), 0.05, 0.05, 0.02, SILVER, False, segs=8)
hollow("Kitchen_Pan", (13.7, 15.5, 3.11), 0.20, 0.225, 0.12, 0.03, 0.02, IRON, coll=False)
box("Kitchen_Pan_Handle", (13.7 - 0.03, 13.7 + 0.03), (15.5 + 0.225, 15.5 + 0.225 + 0.35), (3.18, 3.22), IRON, False)
# wall cupboard (local W=2.2 along D, L=0.7 along X, T=1.6), base (14.25,11.1,5.7), faces -X
wc = Basis(14.25, 11.1, '-X', 5.7)
wc.box("Kitchen_Cupboard_Top", 0, 0, 1.50, 2.2, 0.7, 0.10, SAND)
wc.box("Kitchen_Cupboard_Base", 0, 0, 0.0, 2.2, 0.7, 0.10, SAND)
for sx in (-1, 1):
    wc.box("Kitchen_Cupboard_Side_%s" % ('A' if sx < 0 else 'B'), sx * 1.05, 0, 0.10, 0.10, 0.7, 1.40, SAND)
wc.box("Kitchen_Cupboard_Back", 0, 0.31, 0.10, 2.0, 0.08, 1.40, SAND)
for sx in (-1, 1):
    wc.box("Kitchen_Cupboard_Door_%s" % ('A' if sx < 0 else 'B'), sx * 0.55, -0.35 - 0.03, 0.125, 1.0, 0.06, 1.35, WOOD, False)
    wc.box("Kitchen_Cupboard_Handle_%s" % ('A' if sx < 0 else 'B'), sx * 0.10, -0.46, 0.70, 0.08, 0.08, 0.35, IRON, False)
# dish shelf (14.275,20.7) top 5.42 + two brackets
box("Kitchen_DishShelf", (13.95, 14.6), (20.0, 21.4), (5.30, 5.42), WOOD)
for k, dd in enumerate((20.25, 21.15)):
    box("Kitchen_DishShelf_Bracket_%d" % (k + 1), (14.4, 14.6), (dd - 0.04, dd + 0.04), (5.10, 5.30), WOOD_DARK)
# mugs on the shelf (hollow, attached C handles pointing -X)
for k, (dd, dm, mh, m) in enumerate(((20.25, 0.30, 0.38, RED), (20.7, 0.30, 0.38, WHITE), (21.15, 0.24, 0.30, BLUE))):
    hollow("Kitchen_Mug_%d" % (k + 1), (14.15, dd, 5.42), dm / 2, dm / 2, mh, 0.04, 0.04, m, coll=False, segs=10)
    r = dm / 2
    box("Kitchen_Mug_%d_HandleTop" % (k + 1), (14.15 - r - 0.12, 14.15 - r + 0.02), (dd - 0.03, dd + 0.03), (5.42 + mh - 0.10, 5.42 + mh - 0.04), m, False)
    box("Kitchen_Mug_%d_HandleOuter" % (k + 1), (14.15 - r - 0.12, 14.15 - r - 0.06), (dd - 0.03, dd + 0.03), (5.42 + 0.06, 5.42 + mh - 0.04), m, False)
    box("Kitchen_Mug_%d_HandleBottom" % (k + 1), (14.15 - r - 0.12, 14.15 - r + 0.02), (dd - 0.03, dd + 0.03), (5.42 + 0.06, 5.42 + 0.12), m, False)
# towel on a front rail (X=12.75, D=16.4)
box("Kitchen_TowelRail", (12.75 - 0.03, 12.75 + 0.03), (16.4 - 0.325, 16.4 + 0.325), (2.62, 2.68), WOOD_DARK)
for k, dd in enumerate((16.4 - 0.30, 16.4 + 0.30)):
    box("Kitchen_TowelRail_Mount_%d" % (k + 1), (12.75, 12.8), (dd - 0.03, dd + 0.03), (2.60, 2.70), WOOD_DARK)
nc(box("Kitchen_Towel", (12.71, 12.75), (16.4 - 0.275, 16.4 + 0.275), (1.8, 2.66), WHITE, False))
nc(box("Kitchen_Towel_Fold", (12.70, 12.82), (16.4 - 0.275, 16.4 + 0.275), (2.62, 2.74), WHITE, False))
for k, hh in enumerate((2.0, 2.4)):
    nc(box("Kitchen_Towel_Band_%d" % (k + 1), (12.70, 12.71), (16.4 - 0.275, 16.4 + 0.275), (hh, hh + 0.08), BLUE, False))
# counter jar
cyl("Kitchen_Jar_Body", (13.7, 11.3, 3.0), 0.175, 0.175, 0.43, TRIM, False, segs=10)
cyl("Kitchen_Jar_Lid", (13.7, 11.3, 3.43), 0.18, 0.18, 0.07, WOOD, False, segs=10)

# ==========================================================================
# 7.3 Indoor family dining (right zone)
# ==========================================================================

G("Dining")
table("DiningTable", 8.5, 19.7, 5.6, 3.2, 2.5, 0.20)
for nm, (cx, cd, fc) in {"FrontA": (7.0, 17.0, '+D'), "FrontB": (10.0, 17.0, '+D'),
                         "RearA": (7.0, 22.4, '-D'), "RearB": (10.0, 22.4, '-D')}.items():
    chair("DiningChair_%s" % nm, cx, cd, fc, RED)
nc(box("Rug_Dining_Centre", (4.8 + 0.25, 12.2 - 0.25), (15.7 + 0.25, 23.7 - 0.25), (0.0, 0.02), SAND, False))
for nm, xs, ds in (("N", (4.8, 12.2), (23.45, 23.7)), ("S", (4.8, 12.2), (15.7, 15.95)),
                   ("W", (4.8, 5.05), (15.95, 23.45)), ("E", (11.95, 12.2), (15.95, 23.45))):
    box("Rug_Dining_Border_%s" % nm, xs, ds, (0.0, 0.02), STONE, False)
for k, (px, pd) in enumerate(((7.2, 18.7), (9.6, 18.7), (7.2, 20.7))):
    dish("DiningPlate_%d" % (k + 1), px, pd, 2.5, 0.55)
dish("DiningPlate_Dad", 9.6, 20.7, 2.5, 1.0, rim_h=0.07)
plant("DiningPlant", 8.5, 19.7, 2.5, 0.32, 0.28, 0.35, 5, 0.25, 0.40)
for k, (nx, nd, m) in enumerate(((7.8, 18.7, BLUE), (10.4, 20.5, RED))):
    nc(bevel(box("DiningNapkin_%d_A" % (k + 1), (nx - 0.225, nx + 0.225), (nd - 0.175, nd + 0.175), (2.5, 2.515), m, False), 0.03, 1))
    nc(box("DiningNapkin_%d_B" % (k + 1), (nx - 0.225, nx + 0.225), (nd - 0.175, nd + 0.175), (2.515, 2.53), m, False))

# ==========================================================================
# 7.4 Dad's indoor preparation counter and chimney connection
# ==========================================================================

G("Preparation")
pc = Basis(9.5, 28.4, '-D')
pc.box("Prep_Counter_ToeKick", 0, 0.0, 0.0, 7.8, 1.4, 0.12, WOOD_DARK)
pc.box("Prep_Counter_Base", 0, 0.0, 0.12, 7.84, 1.44, 0.12, SAND)
for i, uc in enumerate((-3.94, -2.0, 0.0, 2.0, 3.94)):
    pc.box("Prep_Counter_Divider_%d" % (i + 1), uc, 0, 0.24, 0.12, 1.5, 2.56, SAND)
pc.box("Prep_Counter_Back", 0, 0.76, 0.24, 8.0, 0.08, 2.56, SAND)
pc.box("Prep_Counter_Top", 0, 0, 2.80, 8.0, 1.6, 0.20, WOOD)
for k, uc in enumerate((-3.0, -1.0, 1.0, 3.0)):
    pc.box("Prep_Counter_Drawer_%d" % (k + 1), uc, -0.83, 2.30, 1.8, 0.06, 0.45, WOOD, False)
    pc.box("Prep_Counter_Door_%d" % (k + 1), uc, -0.83, 0.30, 1.8, 0.06, 1.90, WOOD, False)
    pc.box("Prep_Counter_HandleDrawer_%d" % (k + 1), uc, -0.90, 2.48, 0.35, 0.08, 0.07, IRON, False)
    pc.box("Prep_Counter_HandleDoor_%d" % (k + 1), uc, -0.90, 1.9, 0.35, 0.08, 0.07, IRON, False)
bevel(box("Prep_CuttingBoard", (7.0 - 0.7, 7.0 + 0.7), (28.0 - 0.45, 28.0 + 0.45), (3.0, 3.10), WOOD, False), 0.04, 1)
hollow("Prep_Bowl", (8.4, 28.2, 3.0), 0.30, 0.30, 0.25, 0.04, 0.04, WHITE, coll=False, segs=12)
# tongs on the board: two 0.06 x 0.72 arms joined at a hinge, RED grips, broad tips (assembly lies on the board)
tx0, td = 7.0, 28.0
box("Prep_Tongs_Hinge", (tx0 - 0.40 - 0.05, tx0 - 0.40 + 0.05), (td - 0.08, td + 0.08), (3.10, 3.16), SILVER, False)
for k, s in enumerate((-1, 1)):
    box("Prep_Tongs_Arm_%d" % (k + 1), (tx0 - 0.40, tx0 + 0.32), (td + s * 0.09 - 0.03, td + s * 0.09 + 0.03), (3.10, 3.16), SILVER, False)
    box("Prep_Tongs_Grip_%d" % (k + 1), (tx0 - 0.40, tx0 - 0.20), (td + s * 0.09 - 0.035, td + s * 0.09 + 0.035), (3.10, 3.17), RED, False)
    box("Prep_Tongs_Tip_%d" % (k + 1), (tx0 + 0.32, tx0 + 0.47), (td + s * 0.09 - 0.06, td + s * 0.09 + 0.06), (3.10, 3.14), SILVER, False)
# spice jars (5) and the secret jar
for k, (jx, lid) in enumerate(((6.4, GREEN), (7.0, BLUE), (7.6, RED), (8.2, GOLD), (8.8, IRON))):
    cyl("Prep_SpiceJar_%d_Body" % (k + 1), (jx, 28.9, 3.0), 0.12, 0.12, 0.31, TRIM, False, segs=8)
    cyl("Prep_SpiceJar_%d_Lid" % (k + 1), (jx, 28.9, 3.31), 0.125, 0.125, 0.07, lid, False, segs=8)
    nc(box("Prep_SpiceJar_%d_Label" % (k + 1), (jx - 0.06, jx + 0.06), (28.9 - 0.12 - 0.01, 28.9 - 0.12), (3.08, 3.24), WHITE, False))
cyl("Prep_SecretJar_Body", (9.6, 28.8, 3.0), 0.17, 0.17, 0.46, TRIM, False, segs=10)
cyl("Prep_SecretJar_Lid", (9.6, 28.8, 3.46), 0.175, 0.175, 0.09, GOLD, False, segs=10)
nc(box("Prep_SecretJar_StarVert", (9.6 - 0.02, 9.6 + 0.02), (28.8 - 0.17 - 0.02, 28.8 - 0.17), (3.12, 3.40), RED, False))
nc(box("Prep_SecretJar_StarHoriz", (9.6 - 0.07, 9.6 + 0.07), (28.8 - 0.17 - 0.02, 28.8 - 0.17), (3.24, 3.28), RED, False))
tilted_box("Prep_SecretJar_StarDiagA", (9.6, 28.8 - 0.17 - 0.01, 3.26), (0.14, 0.02, 0.03), 0, 0, RED)
# indoor cooktop + hood + flue (centered X=12, D=28.4)
box("Prep_Cooktop_Plate", (12.0 - 0.75, 12.0 + 0.75), (28.4 - 0.6, 28.4 + 0.6), (3.0, 3.08), IRON)
for k, bx_ in enumerate((11.65, 12.35)):
    cyl("Prep_Cooktop_Burner_%d" % (k + 1), (bx_, 28.4, 3.08), 0.175, 0.175, 0.02, BLACK, False, segs=12)
# hood: hollow tapered lower 1.8 x 1.4 (H 4.6) to upper 0.6 x 0.6 (H 5.4)
hv = []
for (hw, hd, hh) in ((0.9, 0.7, 4.6), (0.3, 0.3, 5.4)):
    hv += [(12.0 - hw, 28.4 - hd, hh), (12.0 + hw, 28.4 - hd, hh), (12.0 + hw, 28.4 + hd, hh), (12.0 - hw, 28.4 + hd, hh)]
hood_faces = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)]
mesh_from("Prep_Hood_Shell", hv, hood_faces, IRON)
box("Prep_Hood_Rim", (12.0 - 0.9, 12.0 + 0.9), (28.4 - 0.7, 28.4 - 0.64), (4.55, 4.60), IRON)
box("Prep_Flue", (12.0 - 0.225, 12.0 + 0.225), (28.4 - 0.225, 28.4 + 0.225), (5.4, 12.5), IRON)
for k, dx in enumerate((-0.2, 0.2)):
    box("Prep_Hood_Bracket_%d" % (k + 1), (12.0 + dx - 0.04, 12.0 + dx + 0.04), (28.4 + 0.7, 29.6), (5.0, 5.1), IRON)
# utensil rail + hanging utensils
box("Prep_UtensilRail", (9.1, 10.9), (29.5 - 0.05, 29.5 + 0.05), (3.75, 3.85), IRON)
for k, bx_ in enumerate((9.2, 10.8)):
    box("Prep_UtensilRail_Mount_%d" % (k + 1), (bx_ - 0.03, bx_ + 0.03), (29.55, 29.6), (3.72, 3.88), IRON)
for k, (ux, kind) in enumerate(((9.4, "Spoon"), (10.0, "Spatula"), (10.6, "Tongs"))):
    box("Prep_Utensil_%s_Hook" % kind, (ux - 0.02, ux + 0.02), (29.5 - 0.05, 29.5 + 0.0), (3.76, 3.80), SILVER, False)
    if kind == "Spoon":
        box("Prep_Utensil_Spoon_Handle", (ux - 0.02, ux + 0.02), (29.42 - 0.025, 29.42 + 0.025), (3.40, 3.76), SILVER, False)
        box("Prep_Utensil_Spoon_Head", (ux - 0.07, ux + 0.07), (29.42 - 0.05, 29.42 + 0.05), (3.21, 3.42), SILVER, False)
    elif kind == "Spatula":
        box("Prep_Utensil_Spatula_Handle", (ux - 0.02, ux + 0.02), (29.42 - 0.025, 29.42 + 0.025), (3.40, 3.76), SILVER, False)
        box("Prep_Utensil_Spatula_Head", (ux - 0.10, ux + 0.10), (29.42 - 0.025, 29.42 + 0.025), (3.22, 3.42), SILVER, False)
    else:
        for s in (-1, 1):
            box("Prep_Utensil_Tongs_Arm_%d" % (1 if s < 0 else 2), (ux + s * 0.05 - 0.025, ux + s * 0.05 + 0.025),
                (29.42 - 0.025, 29.42 + 0.025), (3.21, 3.76), SILVER, False)
            box("Prep_Utensil_Tongs_Grip_%d" % (1 if s < 0 else 2), (ux + s * 0.05 - 0.028, ux + s * 0.05 + 0.028),
                (29.42 - 0.03, 29.42 + 0.03), (3.55, 3.75), RED, False)


# ==========================================================================
# 8.1 Story props: trophy, drawing, family photos, aprons
# ==========================================================================

G("StoryProps")
# Sausage trophy on the storage shelf (top H=3.8 at (-13.65, 11.0))
TX, TD = -13.65, 11.0
box("Trophy_Base", (TX - 0.225, TX + 0.225), (TD - 0.35, TD + 0.35), (3.8, 3.95), IRON, False)
cyl("Trophy_Stem", (TX, TD, 3.95), 0.06, 0.06, 0.35, GOLD, False, segs=8)
# curved sausage 0.85 long x 0.22 thick, centre H 4.40, ends curving up to 4.75
sx_pts = [(-0.425, 4.62), (-0.30, 4.50), (-0.12, 4.42), (0.12, 4.42), (0.30, 4.50), (0.425, 4.62)]
for k in range(len(sx_pts) - 1):
    (d0, h0), (d1, h1) = sx_pts[k], sx_pts[k + 1]
    ang = math.degrees(math.atan2(h1 - h0, d1 - d0))
    ln = math.hypot(d1 - d0, h1 - h0) + 0.06
    tilted_box("Trophy_Sausage_%d" % (k + 1), (TX, TD + (d0 + d1) / 2, (h0 + h1) / 2),
               (ln, 0.22, 0.22), 90, ang, GOLD)
for k, dd in enumerate((-0.18, 0.18)):
    nc(box("Trophy_SausageBand_%d" % (k + 1), (TX - 0.113, TX + 0.113), (TD + dd - 0.015, TD + dd + 0.015), (4.30, 4.52), GOLD, False))

# Child drawing on the left interior wall, backing X=-14.58, centre D=11, H=6.0 (2.4 x 1.8)
DX = -14.58
box("Drawing_Backing", (DX - 0.02, DX + 0.0), (11 - 1.2, 11 + 1.2), (6.0 - 0.9, 6.0 + 0.9), WOOD_DARK, False)
box("Drawing_Paper", (DX, DX + 0.04), (11 - 1.2, 11 + 1.2), (6.0 - 0.9, 6.0 + 0.9), WHITE, False)
for nm, ds, hs in (("N", (11 - 1.32, 11 + 1.32), (6.9, 7.02)), ("S", (11 - 1.32, 11 + 1.32), (4.98, 5.1)),
                   ("W", (11 - 1.32, 11 - 1.2), (5.1, 6.9)), ("E", (11 + 1.2, 11 + 1.32), (5.1, 6.9))):
    box("Drawing_Border_%s" % nm, (DX, DX + 0.10), ds, hs, WOOD, False)


def drawing_box(nm, u, w, du, dw, mat, depth=0.02, base=DX + 0.04, cu=11.0, ch=6.0):
    return box(nm, (base, base + depth), (cu + u - du / 2, cu + u + du / 2), (ch + w - dw / 2, ch + w + dw / 2), mat, False)


drawing_box("Drawing_Dad_Head", 0.0, 0.35, 0.22, 0.22, SAUSAGE)
drawing_box("Drawing_Dad_Body", 0.0, -0.04, 0.30, 0.55, BLUE)
for k, s in enumerate((-1, 1)):
    drawing_box("Drawing_Dad_Leg_%d" % (k + 1), s * 0.07, -0.35, 0.06, 0.30, BLUE)
    # connected arm: shoulder (s*0.18, 0.18) -> hand (s*0.42, 0.52), a tilted strip in the wall plane
    tilted_box("Drawing_Dad_Arm_%d" % (k + 1), (DX + 0.05, 11.0 + s * 0.30, 6.0 + 0.35),
               (math.hypot(0.24, 0.34) + 0.04, 0.06, 0.02), 90, math.degrees(math.atan2(0.34, 0.24)) * s, SAUSAGE)
drawing_box("Drawing_Dad_Tongs", 0.47, 0.62, 0.05, 0.18, IRON)
for k, s in enumerate((-1, 1)):
    uc = s * 0.65
    drawing_box("Drawing_Figure_%d_Head" % (k + 1), uc, -0.35 + 0.12, 0.12, 0.12, SAUSAGE)
    drawing_box("Drawing_Figure_%d_Body" % (k + 1), uc, -0.35 - 0.05, 0.16, 0.26, RED if s < 0 else GREEN)
    drawing_box("Drawing_Figure_%d_Legs" % (k + 1), uc, -0.35 - 0.23, 0.10, 0.15, BLUE)
drawing_box("Drawing_Sun", -0.85, 0.60, 0.22, 0.22, GOLD)
for k, (ru, rw_, a, b) in enumerate(((-0.85, 0.82, 0.04, 0.07), (-0.85, 0.38, 0.04, 0.07), (-1.07, 0.60, 0.07, 0.04),
                                     (-0.63, 0.60, 0.07, 0.04), (-1.01, 0.76, 0.05, 0.05), (-0.69, 0.44, 0.05, 0.05))):
    drawing_box("Drawing_SunRay_%d" % (k + 1), ru, rw_, a, b, GOLD)
drawing_box("Drawing_Grill_Body", 0.90, -0.55, 0.30, 0.18, IRON)
drawing_box("Drawing_Grill_Front", 0.90, -0.55, 0.30, 0.06, RED, depth=0.03)
for k, s in enumerate((-1, 1)):
    drawing_box("Drawing_Grill_Leg_%d" % (k + 1), 0.90 + s * 0.10, -0.74, 0.04, 0.12, IRON)

# Family photos (3) on the left wall: D=22.0, 23.8, 25.6, H=6.2, 1.2 x 1.0
for k, pdc in enumerate((22.0, 23.8, 25.6)):
    nm = "Photo_%d" % (k + 1)
    box(nm + "_Backing", (DX - 0.02, DX), (pdc - 0.6, pdc + 0.6), (6.2 - 0.5, 6.2 + 0.5), CREAM, False)
    box(nm + "_Paper", (DX, DX + 0.05), (pdc - 0.5, pdc + 0.5), (6.2 - 0.4, 6.2 + 0.4), TRIM, False)
    for bnm, ds, hs in (("N", (pdc - 0.6, pdc + 0.6), (6.6, 6.7)), ("S", (pdc - 0.6, pdc + 0.6), (5.7, 5.8)),
                        ("W", (pdc - 0.6, pdc - 0.5), (5.8, 6.6)), ("E", (pdc + 0.5, pdc + 0.6), (5.8, 6.6))):
        box("%s_Border_%s" % (nm, bnm), (DX, DX + 0.09), ds, hs, WOOD, False)
    for hk, du in enumerate((-0.30, 0.0, 0.30)):
        clothes = (CREAM, RED, BLUE)[hk]
        box("%s_Head_%d" % (nm, hk + 1), (DX + 0.05, DX + 0.08), (pdc + du - 0.08, pdc + du + 0.08), (6.2 + 0.12 - 0.08, 6.2 + 0.12 + 0.08), SAUSAGE, False)
        box("%s_Torso_%d" % (nm, hk + 1), (DX + 0.05, DX + 0.08), (pdc + du - 0.10, pdc + du + 0.10), (6.2 - 0.16, 6.2 + 0.04 - 0.0), clothes, False)

# Apron display on the right wall (X=14.6): rail + hooks + garments (face -X)
box("Apron_Rail", (14.44, 14.60), (24.7 - 1.3, 24.7 + 1.3), (6.0, 6.22), WOOD, False)
for k, dd in enumerate((23.7, 24.6, 25.6)):
    box("Apron_Hook_%d" % (k + 1), (14.28, 14.44), (dd - 0.04, dd + 0.04), (6.07, 6.15), IRON, False)
# adult apron
AX, AD = 14.30, 24.6
box("Apron_Adult_Loop", (AX - 0.03, AX + 0.03), (AD - 0.12, AD + 0.12), (5.98, 6.14), RED, False)
box("Apron_Adult_Bib", (AX - 0.04, AX + 0.04), (AD - 0.25, AD + 0.25), (5.45, 6.0), RED, False)
box("Apron_Adult_Skirt", (AX - 0.04, AX + 0.04), (AD - 0.475, AD + 0.475), (4.25, 5.45), RED, False)
box("Apron_Adult_Pocket", (AX - 0.06, AX - 0.04), (AD - 0.225, AD + 0.225), (4.55, 4.90), RED, False)
for k, s in enumerate((-1, 1)):
    box("Apron_Adult_Tie_%d" % (k + 1), (AX - 0.04, AX + 0.04), (AD + s * 0.475, AD + s * 0.475 + s * 0.10), (5.30, 5.35), RED, False)
# child apron
CD = 25.6
box("Apron_Child_Loop", (AX - 0.03, AX + 0.03), (CD - 0.09, CD + 0.09), (5.98, 6.12), BLUE, False)
box("Apron_Child_Bib", (AX - 0.03, AX + 0.03), (CD - 0.16, CD + 0.16), (5.50, 6.0), BLUE, False)
box("Apron_Child_Skirt", (AX - 0.03, AX + 0.03), (CD - 0.30, CD + 0.30), (4.90, 5.50), BLUE, False)
box("Apron_Child_Pocket", (AX - 0.05, AX - 0.03), (CD - 0.14, CD + 0.14), (5.05, 5.27), BLUE, False)
# spare oven mitt
MD = 23.7
box("Apron_Mitt_Loop", (AX - 0.03, AX + 0.03), (MD - 0.05, MD + 0.05), (5.95, 6.07), RED, False)
box("Apron_Mitt_Body", (AX - 0.06, AX + 0.06), (MD - 0.175, MD + 0.175), (5.40, 5.95), SAND, False)
box("Apron_Mitt_Thumb", (AX - 0.06, AX + 0.06), (MD + 0.175, MD + 0.175 + 0.12), (5.55, 5.75), RED, False)

# ==========================================================================
# 8.2 Entry and exterior fixtures
# ==========================================================================

G("Entry")
# Entry shoe tray, shoes and bag: ~1.9x the first pass so they read at the avatar's scale
# (doors are 8.4 x 9.4).  Tray stays at X -7.8..-4.6 (outside the X -4..4 lane).
TRX0, TRX1, TRD0, TRD1 = -7.8, -4.6, 6.3, 8.3
box("Entry_ShoeTray_Base", (TRX0, TRX1), (TRD0, TRD1), (0.0, 0.06), WOOD_DARK, False)
for nm, xs, ds in (("N", (TRX0, TRX1), (TRD1 - 0.12, TRD1)), ("S", (TRX0, TRX1), (TRD0, TRD0 + 0.12)),
                   ("W", (TRX0, TRX0 + 0.12), (TRD0 + 0.12, TRD1 - 0.12)), ("E", (TRX1 - 0.12, TRX1), (TRD0 + 0.12, TRD1 - 0.12))):
    box("Entry_ShoeTray_Rim_%s" % nm, xs, ds, (0.06, 0.18), WOOD_DARK, False)
for k, sx in enumerate((-7.1, -6.15)):
    nc(bevel(box("Entry_ShoeAdult_%d" % (k + 1), (sx - 0.425, sx + 0.425), (7.3 - 0.7, 7.3 + 0.7), (0.20, 0.62), IRON, False), 0.08, 1))
    nc(box("Entry_ShoeAdult_%d_Sole" % (k + 1), (sx - 0.425, sx + 0.425), (7.3 - 0.7, 7.3 + 0.7), (0.06, 0.20), SAND, False))
for k, sd in enumerate((6.9, 7.75)):
    nc(bevel(box("Entry_ShoeChild_%d" % (k + 1), (-5.25 - 0.25, -5.25 + 0.25), (sd - 0.4, sd + 0.4), (0.18, 0.42), RED, False), 0.05, 1))
    nc(box("Entry_ShoeChild_%d_Sole" % (k + 1), (-5.25 - 0.25, -5.25 + 0.25), (sd - 0.4, sd + 0.4), (0.06, 0.18), WHITE, False))
# shopping bag (1.2 x 0.85 x 1.2 body, loops to 1.5), moved clear of the tray
BGX, BGD = -9.4, 7.3
bevel(box("Entry_Bag_Body", (BGX - 0.6, BGX + 0.6), (BGD - 0.425, BGD + 0.425), (0.0, 1.2), SAND, False), 0.06, 1)
for k, s in enumerate((-1, 1)):
    box("Entry_Bag_Loop_%d" % (k + 1), (BGX + s * 0.3 - 0.07, BGX + s * 0.3 + 0.07), (BGD - 0.38, BGD + 0.38), (1.2, 1.5), WOOD, False)
# coat hooks on the left recess return wall (X=-5.4..-5.0 return at X=-5; room side is X<-5.4)
box("Entry_CoatStrip", (-5.0 - 0.0, -5.0 + 0.15), (4.6 - 0.35, 4.6 + 0.35), (4.9, 5.1), WOOD, False)
for k, dd in enumerate((4.35, 4.60, 4.85)):
    box("Entry_CoatPeg_%d" % (k + 1), (-4.85, -4.70), (dd - 0.03, dd + 0.03), (5.07, 5.13), IRON, False)
# key shelf on the same return wall
box("Entry_KeyShelf", (-5.0, -4.70), (4.6 - 0.35, 4.6 + 0.35), (3.5, 3.6), WOOD, False)
for k, dd in enumerate((4.45, 4.72)):
    box("Entry_Key_%d_Shaft" % (k + 1), (-4.95, -4.75), (dd - 0.03, dd + 0.03), (3.6, 3.64), IRON, False)
    box("Entry_Key_%d_Loop" % (k + 1), (-4.97, -4.89), (dd - 0.03, dd + 0.03), (3.6, 3.66), IRON, False)
# door lanterns (4): two front on exterior front wall face D=4, two rear on D=30
for k, (lx, ld, side) in enumerate(((-5.6, 3.8, -1), (5.6, 3.8, -1), (-5.2, 30.25, 1), (5.2, 30.25, 1))):
    wall_d = 4.0 if side < 0 else 30.0
    nm = "Entry_Lantern_%d" % (k + 1)
    bx_ = box(nm + "_Body", (lx - 0.25, lx + 0.25), (ld - 0.125, ld + 0.125), (5.5 - 0.325 + 0.06, 5.5 + 0.325 - 0.06), IRON, False)
    box(nm + "_Cap", (lx - 0.25, lx + 0.25), (ld - 0.125, ld + 0.125), (5.5 + 0.325 - 0.06, 5.5 + 0.325), IRON, False)
    box(nm + "_Base", (lx - 0.25, lx + 0.25), (ld - 0.125, ld + 0.125), (5.5 - 0.325, 5.5 - 0.325 + 0.06), IRON, False)
    sgn = -1 if side < 0 else 1
    nc(box(nm + "_Lens", (lx - 0.16, lx + 0.16), (ld + sgn * (0.125), ld + sgn * 0.155) if sgn > 0 else (ld - 0.155, ld - 0.125),
           (5.5 - 0.215, 5.5 + 0.215), WHITE, False))
    box(nm + "_Bracket", (lx - 0.05, lx + 0.05), (min(wall_d, ld) if sgn < 0 else wall_d, max(wall_d, ld) if sgn > 0 else wall_d) if False else
        (ld + 0.125, wall_d) if sgn < 0 else (wall_d, ld - 0.125), (5.5 + 0.20, 5.5 + 0.30), IRON, False)
    nc(box(nm + "_Glow", (lx - 0.08, lx + 0.08), (ld + sgn * 0.15 - 0.01, ld + sgn * 0.15 + 0.01) if sgn > 0 else (ld - 0.16, ld - 0.14),
           (5.5 - 0.1, 5.5 + 0.1), GOLD, False))
# front planters (2)
for k, px in enumerate((-6.6, 6.6)):
    plant("Entry_Planter_%d" % (k + 1), px, 2.6, 0.0, 1.0, 0.9, 2.5, 6, 0.8, 1.2, pot_mat=CREAM, pot_segs=8)

# ==========================================================================
# 9. Rear patio, pergola, patio furniture
# ==========================================================================

G("Patio")
tile_pattern("Patio_Paving", -15, 15, 30, 40, 1.5, 0.025, 0.0, 0.20, MORTAR, PATIO, PATIO_LIGHT,
             lambda r, c: (r + c) % 4 == 0)
tile_pattern("Patio_RearPath", -4, 4, 40, 47.6, 2.0, 0.03, 0.0, 0.20, MORTAR, STONE, PATIO,
             lambda r, c: (r + c) % 4 == 0)
G("Entry")
tile_pattern("Entry_FrontPath", -4, 4, 0, 4, 2.0, 0.03, 0.0, 0.20, MORTAR, STONE, STONE,
             lambda r, c: False)
G("Patio")

# pergola
for k, (px, pd) in enumerate(((-14.2, 30.7), (14.2, 30.7), (-14.2, 39.2), (14.2, 39.2))):
    box("Pergola_Post_%d" % (k + 1), (px - 0.2, px + 0.2), (pd - 0.2, pd + 0.2), (0.0, 9.6), WOOD_DARK)
for nm, xs, ds in (("Front", (-14.6, 14.6), (30.2, 30.5)), ("Rear", (-14.6, 14.6), (39.2, 39.5)),
                   ("Left", (-14.6, -14.3), (30.2, 39.5)), ("Right", (14.3, 14.6), (30.2, 39.5))):
    box("Pergola_Beam_%s" % nm, xs, ds, (9.6, 9.95), WOOD)
for k in range(10):
    dd = 30.7 + k * (39.2 - 30.7) / 9
    box("Pergola_Slat_%d" % (k + 1), (-14.2, 14.2), (dd - 0.11, dd + 0.11), (9.95, 10.11), WOOD, False)

# patio table, chairs, plates
table("PatioTable", -9.0, 35.6, 6.0, 3.4, 2.6, 0.20)
for nm, (cx, cd, fc) in {"FrontA": (-10.6, 32.9, '+D'), "FrontB": (-7.4, 32.9, '+D'),
                         "RearA": (-10.6, 38.3, '-D'), "RearB": (-7.4, 38.3, '-D')}.items():
    chair("PatioChair_%s" % nm, cx, cd, fc, SAND)
for k, (px, pd) in enumerate(((-10.5, 34.6), (-7.6, 34.6), (-10.5, 36.6))):
    dish("PatioPlate_%d" % (k + 1), px, pd, 2.6, 0.55)
dish("PatioPlate_Dad", -7.6, 36.6, 2.6, 1.0, rim_h=0.07)
plant("PatioCenterPlant", -9.0, 35.6, 2.6, 0.35, 0.30, 0.35, 5, 0.25, 0.40)
for k, px in enumerate((-12.8, 12.8)):
    plant("PatioPot_%d" % (k + 1), px, 31.4, 0.0, 0.8, 0.7, 2.1, 6, 0.8, 1.3, pot_mat=CREAM)

# patio preparation cabinet: W=2 along X, L=1.6 along D, T=2.8, base (6.0, 35.6)
pcab = Basis(6.0, 35.6, '-D')
pcab.box("PatioCabinet_Base", 0, 0, 0.0, 2.0, 1.6, 0.12, WOOD_DARK)
for sx in (-1, 1):
    pcab.box("PatioCabinet_Side_%s" % ('A' if sx < 0 else 'B'), sx * 0.94, 0, 0.12, 0.12, 1.6, 2.53, SAND)
pcab.box("PatioCabinet_Back", 0, 0.76, 0.12, 1.76, 0.08, 2.53, SAND)
pcab.box("PatioCabinet_Divider", 0, 0, 0.12, 0.06, 1.5, 2.53, SAND)
pcab.box("PatioCabinet_Top", 0, 0, 2.65, 2.0, 1.6, 0.15, WOOD)
for k, uc in enumerate((-0.5, 0.5)):
    pcab.box("PatioCabinet_Door_%d" % (k + 1), uc, -0.83, 0.20, 0.94, 0.06, 2.35, WOOD, False)
    pcab.box("PatioCabinet_Handle_%d" % (k + 1), uc + (0.38 if uc < 0 else -0.38), -0.90, 1.2, 0.07, 0.08, 0.35, IRON, False)
for k, (bx_, m) in enumerate(((5.7, RED), (6.3, GOLD))):
    cyl("PatioSauce_%d_Body" % (k + 1), (bx_, 35.6, 2.8), 0.125, 0.125, 0.48, m, False, segs=8)
    cyl("PatioSauce_%d_Neck" % (k + 1), (bx_, 35.6, 3.28), 0.05, 0.05, 0.10, m, False, segs=6)
    cyl("PatioSauce_%d_Cap" % (k + 1), (bx_, 35.6, 3.38), 0.06, 0.06, 0.07, IRON, False, segs=6)

# ==========================================================================
# 9.2 Main grill (front-facing -D basis, origin (10, 35.6))
# ==========================================================================

G("Grill")
gb = Basis(10.0, 35.6, '-D')
# cart
for k, uc in enumerate((-1.0, 1.0)):
    gb.box("Grill_Cart_Door_%d" % (k + 1), uc, -0.97, 0.70, 1.85, 0.06, 1.30, RED)
    gb.box("Grill_Cart_Handle_%d" % (k + 1), uc + (0.8 if uc < 0 else -0.8), -1.05, 1.575, 0.07, 0.08, 0.35, IRON, False)
for sx in (-1, 1):
    gb.box("Grill_Cart_Side_%s" % ('A' if sx < 0 else 'B'), sx * 2.0, 0, 0.55, 0.10, 1.9, 1.65, IRON)
gb.box("Grill_Cart_Back", 0, 0.9, 0.55, 3.9, 0.10, 1.65, IRON)
gb.box("Grill_Cart_Bottom", 0, 0, 0.55, 3.9, 1.7, 0.10, IRON)
gb.box("Grill_Cart_FrontRail", 0, -0.92, 2.0, 3.9, 0.10, 0.20, IRON)
for sx in (-1, 1):
    gb.box("Grill_Axle_%s" % ('A' if sx < 0 else 'B'), sx * 1.70, 0.70, 0.19, 0.10, 0.10, 0.10, SILVER, False)
    # wheel: axis along u -> thin cylinder built as a short tilted frustum with segs 10
    wx, wd = gb.pt(sx * 1.70, 0.70)
    verts, faces = [], []
    segs = 10
    for side in (-0.075, 0.075):
        for i in range(segs):
            a = 2 * math.pi * i / segs
            verts.append((wx + side, wd + 0.225 * math.cos(a), 0.225 + 0.225 * math.sin(a)))
    for i in range(segs):
        j = (i + 1) % segs
        faces.append((i, j, j + segs, i + segs))
    faces.append(tuple(range(segs - 1, -1, -1)))
    faces.append(tuple(range(segs, 2 * segs)))
    mesh_from("Grill_Wheel_%s" % ('A' if sx < 0 else 'B'), verts, faces, BLACK)
    gb.box("Grill_Foot_%s" % ('A' if sx < 0 else 'B'), sx * 1.70, -0.70, 0.0, 0.18, 0.18, 0.55, IRON)
# firebox: hollow, walls 0.10, H 2.2..2.85
gb.box("Grill_Firebox_Bottom", 0, 0, 2.2, 3.4, 1.8, 0.10, IRON)
gb.box("Grill_Firebox_Front", 0, -0.85, 2.3, 3.4, 0.10, 0.55, IRON)
gb.box("Grill_Firebox_Back", 0, 0.85, 2.3, 3.4, 0.10, 0.55, IRON)
for sx in (-1, 1):
    gb.box("Grill_Firebox_Side_%s" % ('A' if sx < 0 else 'B'), sx * 1.65, 0, 2.3, 0.10, 1.6, 0.55, IRON)
for k, sv in enumerate((-0.65, 0.65)):
    gb.box("Grill_Grate_Rail_%d" % (k + 1), 0, sv, 2.74, 3.15, 0.06, 0.06, SILVER, False)
bars = []
for i in range(16):
    uc = -1.5 + i * 0.2
    X0, D0 = gb.pt(uc - 0.025, -0.775)
    X1, D1 = gb.pt(uc + 0.025, 0.775)
    bars.append((min(X0, X1), max(X0, X1), min(D0, D1), max(D0, D1), 2.80, 2.88))
merged("Grill_Grate_Bars", bars, SILVER, False)
# side shelves
for sx in (-1, 1):
    gb.box("Grill_SideShelf_%s" % ('A' if sx < 0 else 'B'), sx * 2.05, 0, 2.73, 0.70, 1.80, 0.12, IRON)
# control knobs (3) on the front upper panel
for k, uc in enumerate((-0.65, 0.0, 0.65)):
    gb.box("Grill_Knob_%d" % (k + 1), uc, -1.03, 2.31, 0.18, 0.08, 0.18, SILVER, False)
    gb.box("Grill_Knob_%d_Mark" % (k + 1), uc, -1.07, 2.37, 0.05, 0.02, 0.07, BLACK, False)


# lid: hinge axis along u at v=0.90, H=2.85; 3.6 x 1.95 x 0.8, wall 0.08, underside open; rotated 100deg
def lid_f(u, v, w):
    dv, dw = v - 0.90, w - 2.85
    a = math.radians(-100.0)
    dv2 = dv * math.cos(a) - dw * math.sin(a)
    dw2 = dv * math.sin(a) + dw * math.cos(a)
    X, D = gb.pt(u, 0.90 + dv2)
    return (X, D, 2.85 + dw2)


LID_PARTS = [("Top", -1.8, 1.8, -1.05, 0.90, 3.57, 3.65),
             ("Front", -1.8, 1.8, -1.05, -0.97, 2.85, 3.57),
             ("Back", -1.8, 1.8, 0.82, 0.90, 2.85, 3.57),
             ("EndA", -1.8, -1.72, -0.97, 0.82, 2.85, 3.57),
             ("EndB", 1.72, 1.8, -0.97, 0.82, 2.85, 3.57)]
for nm, u0, u1, v0, v1, h0, h1 in LID_PARTS:
    gb.xz("Grill_Lid_%s" % nm, lid_f, u0, u1, v0, v1, h0, h1, IRON)
# lid handle (1.2 x 0.12) with two brackets on the lid front, same lid transform
gb.xz("Grill_LidHandle_Bar", lid_f, -0.6, 0.6, -1.20, -1.08, 3.20, 3.32, SILVER, False)
for k, uc in enumerate((-0.55, 0.55)):
    gb.xz("Grill_LidHandle_Bracket_%d" % (k + 1), lid_f, uc - 0.075, uc + 0.075, -1.20, -1.05, 3.20, 3.32, SILVER, False)
for k, uc in enumerate((-1.2, 1.2)):
    gb.box("Grill_LidHinge_%d" % (k + 1), uc, 0.90, 2.75, 0.20, 0.20, 0.15, IRON)
# the ONE tiny sausage on the grate, centre (10.0, 35.5), bottom H=2.88
sx0, sd0 = gb.pt(0.0, -0.10)
def capsule_x(name, c, length, dia, material, bend=0.025, segs=8):
    """Broad bent capsule along X: rounded (tapered) ends, centre c=(X,D,H_centre);
    both ends lift by `bend` so the sausage reads as gently curved."""
    r = dia / 2
    rings = [(-length / 2, 0.45 * r, bend), (-length / 2 + 0.07, r, bend * 0.35),
             (0.0, r, 0.0), (length / 2 - 0.07, r, bend * 0.35), (length / 2, 0.45 * r, bend)]
    v, f = [], []
    for (dx, rr, dz) in rings:
        for i in range(segs):
            a = 2 * math.pi * i / segs
            v.append((c[0] + dx, c[1] + rr * math.cos(a), c[2] + dz + rr * math.sin(a)))
    for k in range(len(rings) - 1):
        for i in range(segs):
            j = (i + 1) % segs
            f.append((k * segs + i, k * segs + j, (k + 1) * segs + j, (k + 1) * segs + i))
    f.append(tuple(range(segs - 1, -1, -1)))
    f.append(tuple((len(rings) - 1) * segs + i for i in range(segs)))
    return mesh_from(name, v, f, material, False)


capsule_x("Grill_Sausage", (sx0, sd0, 2.88 + 0.07), 0.55, 0.14, SAUSAGE)
for k, du in enumerate((-0.12, 0.12)):
    X, D = gb.pt(du, -0.10)
    nc(box("Grill_Sausage_Band_%d" % (k + 1), (X - 0.0125, X + 0.0125), (D - 0.071, D + 0.071), (2.88, 3.025), BLACK, False))
# side tongs + mitt on side hooks
gb.box("Grill_TongHook", -2.30, 0.30, 2.55, 0.06, 0.06, 0.06, IRON, False)
gb.box("Grill_Tongs_Hinge", -2.30, 0.30, 2.40, 0.08, 0.08, 0.14, SILVER, False)
for k, sv in enumerate((-1, 1)):
    gb.box("Grill_Tongs_Arm_%d" % (k + 1), -2.30 + sv * 0.07, 0.30, 1.95, 0.05, 0.05, 0.50, SILVER, False)
    gb.box("Grill_Tongs_Grip_%d" % (k + 1), -2.30 + sv * 0.07, 0.30, 2.25, 0.055, 0.055, 0.20, RED, False)
gb.box("Grill_MittHook", 2.30, 0.30, 2.5, 0.06, 0.06, 0.06, IRON, False)
gb.box("Grill_Mitt_Loop", 2.30, 0.30, 2.40, 0.04, 0.04, 0.10, RED, False)
gb.box("Grill_Mitt_Body", 2.30, 0.30, 1.90, 0.38, 0.12, 0.50, SAND, False)
gb.box("Grill_Mitt_Thumb", 2.30 + 0.24, 0.30, 2.10, 0.12, 0.10, 0.20, RED, False)


# ==========================================================================
# 10. Garden, path lanterns, fences
# ==========================================================================

G("Garden")


def shrub(prefix, cx, cd, W, Dp, H, rot_idx):
    """Three broad faceted masses (nominal local centres scaled to the
    listed envelope, deterministic rotation) on a connected base."""
    nominal = ((-0.35, -0.20, 0.60), (0.30, 0.15, 0.70), (0.0, 0.35, 0.90))
    heights = (0.78 * H, 0.88 * H, 1.0 * H)
    R = 0.34 * min(W, Dp)
    ang = math.radians(90 * rot_idx)
    ca, sa = math.cos(ang), math.sin(ang)
    box(prefix + "_Base", (cx - W * 0.4, cx + W * 0.4), (cd - Dp * 0.4, cd + Dp * 0.4), (0.0, 0.12), GREEN_DARK, False)
    for k, ((u, v, _h), hh) in enumerate(zip(nominal, heights)):
        uu, vv = u * W * 0.5, v * Dp * 0.5
        x = cx + uu * ca - vv * sa
        d = cd + uu * sa + vv * ca
        cyl("%s_Mass_%d" % (prefix, k + 1), (x, d, 0.0), R, R * 0.72, hh, GREEN if k != 1 else GREEN_DARK, False, segs=7)


for k, (sx_, sd_) in enumerate(((-10, 1.7), (-16.8, 4.0), (10, 1.7), (16.8, 4.0))):
    shrub("Shrub_Front_%d" % (k + 1), sx_, sd_, 2.0, 1.4, 1.2, k)
for k, (sx_, sd_) in enumerate(((-18.7, 12), (-18.7, 25), (18.7, 12), (18.7, 25))):
    shrub("Shrub_Side_%d" % (k + 1), sx_, sd_, 1.6, 2.0, 1.3, k)


def tree(prefix, tx, td):
    box(prefix + "_Trunk", (tx - 0.175, tx + 0.175), (td - 0.175, td + 0.175), (0.0, 3.1), WOOD_DARK, False)
    clusters = ((-0.45, 0.0, 3.4), (0.45, 0.10, 3.7), (0.0, 0.0, 4.9))
    for k, (u, v, h) in enumerate(clusters):
        cyl("%s_Crown_%d" % (prefix, k + 1), (tx + u, td + v, h - 0.9), 0.9, 0.65, 1.8, GREEN if k != 1 else GREEN_DARK, False, segs=7)
    for k, (u, v, h) in enumerate(clusters[:2]):
        bx_ = tx + u * 0.5
        box("%s_Branch_%d" % (prefix, k + 1), (min(tx, tx + u) - 0.08, max(tx, tx + u) + 0.08),
            (td - 0.08 + v * 0.5, td + 0.08 + v * 0.5), (2.6, 3.1 + 0.0), WOOD_DARK, False)


tree("Tree_1", -19.0, 6.5)
tree("Tree_2", 19.0, 27.0)

for k, lx in enumerate((-4.9, 4.9)):
    G("Entry")
    box("PathLantern_%d_Stem" % (k + 1), (lx - 0.06, lx + 0.06), (1.4 - 0.06, 1.4 + 0.06), (0.0, 0.8), IRON)
    box("PathLantern_%d_Housing" % (k + 1), (lx - 0.2, lx + 0.2), (1.4 - 0.2, 1.4 + 0.2), (0.8, 1.3), IRON, False)
    nc(box("PathLantern_%d_Lens" % (k + 1), (lx - 0.15, lx + 0.15), (1.4 - 0.21, 1.4 + 0.21), (0.87, 1.23), WHITE, False))
    nc(box("PathLantern_%d_Inset" % (k + 1), (lx - 0.07, lx + 0.07), (1.4 - 0.215, 1.4 + 0.215), (0.98, 1.12), GOLD, False))

G("Fence")


def fence_run(prefix, axis, a0, a1, fixed):
    """Outer faces a0..a1 along `axis` ('X' or 'D'), centred on `fixed`.
    Posts 0.4 x 0.4 x 2.2, rails 0.12 x 0.30 at H~0.7 and 1.6."""
    p = 0.4
    S = a1 - a0
    N = max(1, int(math.ceil((S - p) / 3.8)))
    step = (S - p) / N
    centers = [a0 + p / 2 + i * step for i in range(N + 1)]
    posts, rails = [], []
    for c in centers:
        if axis == 'X':
            posts.append((c - 0.2, c + 0.2, fixed - 0.2, fixed + 0.2, 0.0, 2.2))
        else:
            posts.append((fixed - 0.2, fixed + 0.2, c - 0.2, c + 0.2, 0.0, 2.2))
    for i in range(N):
        s0, s1 = centers[i] + 0.2, centers[i + 1] - 0.2
        for hc in (0.7, 1.6):
            if axis == 'X':
                rails.append((s0, s1, fixed - 0.06, fixed + 0.06, hc - 0.15, hc + 0.15))
            else:
                rails.append((fixed - 0.06, fixed + 0.06, s0, s1, hc - 0.15, hc + 0.15))
    merged(prefix + "_Posts", posts, TRIM)
    merged(prefix + "_Rails", rails, WOOD)
    return centers


FENCE_INFO = {}
FENCE_INFO["front_left"] = fence_run("Fence_Front_L", 'X', -21.8, -4.2, 0.6)
FENCE_INFO["front_right"] = fence_run("Fence_Front_R", 'X', 4.2, 21.8, 0.6)
FENCE_INFO["side_left"] = fence_run("Fence_Side_L", 'D', 0.8, 38.0, -21.6)
FENCE_INFO["side_right"] = fence_run("Fence_Side_R", 'D', 0.8, 38.0, 21.6)
FENCE_INFO["rear"] = fence_run("Fence_Rear", 'X', -14.0, 14.0, 47.8)

# ==========================================================================
# 11. Reference helpers (not exported)
# ==========================================================================

HELPERS = {
    "DadSpawnPoint": (8.5, 25.5, 0.0),
    "FamilySpawn_01": (-8.5, 11.0, 0.0),
    "FamilySpawn_02": (-9.5, 15.0, 0.0),
    "FamilySpawn_03": (6.5, 11.0, 0.0),
    "FrontEntrance": (0.0, 5.2, 0.0),
    "RearEntrance": (0.0, 30.0, 0.0),
    "BackyardExit_Left": (-18.0, 43.8, 0.0),
    "BackyardExit_Right": (18.0, 43.8, 0.0),
}
for hname, (hx, hd, hh) in HELPERS.items():
    e = bpy.data.objects.new(hname, None)
    e.empty_display_type = 'PLAIN_AXES'
    e.empty_display_size = 1.0
    e.location = (hx, Y(hd), hh)
    GROUPS["ReferenceHelpers"].objects.link(e)

PROTECTED = {
    "FrontApproach": ((-4, 4), (0.0, 5.2), (0, 9)),
    "InteriorMainLane": ((-4, 4), (5.2, 30.0), (0, 9)),
    "PatioCentralLane": ((-4, 4), (30.0, 44.0), (0, 9)),
    "RearCrossConnection": ((-22, 22), (39.6, 47.6), (0, 9)),
    "RearLeftExit": ((-22, -14), (39.6, 48.0), (0, 9)),
    "RearRightExit": ((14, 22), (39.6, 48.0), (0, 9)),
    "DadInteractionPad": ((5, 12), (24, 27.3), (0, 9)),
    "FamilyPad_01": ((-10, -7), (9.5, 12.5), (0, 9)),
    "FamilyPad_02": ((-11, -8), (13.5, 16.5), (0, 9)),
    "FamilyPad_03": ((5, 8), (9.5, 12.5), (0, 9)),
    "Connector_Dad": ((4, 5), (24, 27.3), (0, 9)),
    "Connector_Family01": ((-7, -4), (9.5, 12.5), (0, 9)),
    "Connector_Family02": ((-8, -4), (13.1, 16.1), (0, 9)),
    "Connector_Family03": ((4, 5), (9.5, 12.5), (0, 9)),
}

# ==========================================================================
# 12. Ground: lawn with true cut-outs (no coplanar overlap with floors/paving)
# ==========================================================================

G("Structure")
ground = box("Structure_Ground", (PROP_X0, PROP_X1), (PROP_D0, PROP_D1), (-0.25, 0.0), GREEN)
CUTTERS = []


def cutter(pts, nm):
    n = len(pts)
    v = [(x, Y(d), -1.0) for x, d in pts] + [(x, Y(d), 1.0) for x, d in pts]
    f = []
    for i in range(1, n - 1):
        f.append((0, i + 1, i))
        f.append((n, n + i, n + i + 1))
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, n + j, n + i))
    me = bpy.data.meshes.new(nm)
    me.from_pydata(v, [], f)
    me.validate()
    ob = bpy.data.objects.new(nm, me)
    SCENE.collection.objects.link(ob)
    return ob


for nm, pts in (("cut_house", FOOT), ("cut_notch", [(-5, 4), (5, 4), (5, 5.2), (-5, 5.2)]),
                ("cut_patio", [(-15, 30), (15, 30), (15, 40), (-15, 40)]),
                ("cut_front", [(-4, 0), (4, 0), (4, 4), (-4, 4)]),
                ("cut_rear", [(-4, 40), (4, 40), (4, 47.6), (-4, 47.6)])):
    cutter_ob = cutter(pts, nm)
    CUTTERS.append(cutter_ob)
    bpy.context.view_layer.objects.active = ground
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ground.select_set(True)
    m = ground.modifiers.new("Cut_" + nm, 'BOOLEAN')
    m.object = cutter_ob
    m.operation = 'DIFFERENCE'
    m.solver = 'EXACT'
    bpy.ops.object.modifier_apply(modifier=m.name)
for c in CUTTERS:
    bpy.data.objects.remove(c, do_unlink=True)

# ==========================================================================
# 13. Preview rig, save, export, audit, manifest, registry, Studio script
# ==========================================================================

world = bpy.data.worlds.new("GDH_Daylight")
SCENE.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.70, 0.80, 0.86, 1.0)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.5
_sun = bpy.data.lights.new("GDH_Sun", 'SUN')
_sun.energy = 2.0
_sun.angle = math.radians(6)
SUN = bpy.data.objects.new("GDH_Sun", _sun)
SCENE.collection.objects.link(SUN)
SUN.rotation_euler = (math.radians(50), 0, math.radians(30))
_fill = bpy.data.lights.new("GDH_Fill", 'SUN')
_fill.energy = 0.6
_fill.use_shadow = False
FILL = bpy.data.objects.new("GDH_Fill", _fill)
SCENE.collection.objects.link(FILL)
FILL.rotation_euler = (math.radians(60), 0, math.radians(-130))
CAM_D = bpy.data.cameras.new("GDH_PreviewCam")
CAM = bpy.data.objects.new("GDH_PreviewCam", CAM_D)
SCENE.collection.objects.link(CAM)
SCENE.camera = CAM
SCENE.render.engine = 'BLENDER_EEVEE'
SCENE.eevee.taa_render_samples = 32
SCENE.render.image_settings.file_format = 'PNG'
SCENE.view_settings.view_transform = 'Standard'


def mesh_objects():
    return [o for o in bpy.data.objects if o.type == 'MESH' and o.name in OBJECT_MATERIAL]


def bbox_logical(o):
    ws = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
    return (min(w.x for w in ws), max(w.x for w in ws), min(w.y for w in ws) + D_OFFSET,
            max(w.y for w in ws) + D_OFFSET, min(w.z for w in ws), max(w.z for w in ws))


def tri_count():
    dg = bpy.context.evaluated_depsgraph_get()
    n = 0
    for o in mesh_objects():
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        n += sum(max(len(p.vertices) - 2, 0) for p in me.polygons)
        ev.to_mesh_clear()
    return n


os.makedirs(os.path.join(OUT_DIR, "previews"), exist_ok=True)
BLEND_PATH = os.path.join(OUT_DIR, "GrillDadHouse.blend")
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

# ---- clearance audit -------------------------------------------------------
REG = {}
for o in mesh_objects():
    REG[o.name] = bbox_logical(o)
VIOL = []
for pname, ((px0, px1), (pd0, pd1), (ph0, ph1)) in PROTECTED.items():
    for nme, (x0, x1, d0, d1, h0, h1) in REG.items():
        if h1 <= 0.12:        # flat rugs / paving / thresholds are not blockers
            continue
        if x1 > px0 + 0.005 and x0 < px1 - 0.005 and d1 > pd0 + 0.005 and d0 < pd1 - 0.005 and h1 > ph0 and h0 < ph1:
            VIOL.append({"volume": pname, "object": nme, "collidable": nme not in NONCOLLIDE,
                         "bbox": [round(v, 3) for v in (x0, x1, d0, d1, h0, h1)]})
print("AUDIT_VIOLATIONS", len(VIOL))
for v in VIOL[:60]:
    print("AUDIT", v["volume"], v["object"], "collide" if v["collidable"] else "nocollide", v["bbox"])

# ---- property / building bounds ---------------------------------------------
allx0 = min(b[0] for b in REG.values())
allx1 = max(b[1] for b in REG.values())
alld0 = min(b[2] for b in REG.values())
alld1 = max(b[3] for b in REG.values())
print("BOUNDS X", round(allx0, 3), round(allx1, 3), "D", round(alld0, 3), round(alld1, 3))
roof_b = [REG[n] for n in REG if OBJECT_GROUP[n] == "Roof" and n.startswith("Roof_Hip") or n.startswith("Roof_Fascia")]
print("ROOF X", round(min(b[0] for b in roof_b), 3), round(max(b[1] for b in roof_b), 3),
      "D", round(min(b[2] for b in roof_b), 3), round(max(b[3] for b in roof_b), 3),
      "Hmax", round(max(b[5] for b in roof_b), 3))

# ---- FBX export -------------------------------------------------------------
FBX_PATH = os.path.join(OUT_DIR, "GrillDadHouse.fbx")
bpy.ops.object.select_all(action='DESELECT')
_sel = mesh_objects()
for ob in _sel:
    ob.select_set(True)
bpy.context.view_layer.objects.active = _sel[0]
FBX_SETTINGS = dict(use_selection=True, object_types={'MESH'}, apply_unit_scale=True,
                    apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y',
                    mesh_smooth_type='FACE', use_mesh_modifiers=True, bake_anim=False,
                    add_leaf_bones=False, path_mode='COPY', embed_textures=False)
bpy.ops.export_scene.fbx(filepath=FBX_PATH, **FBX_SETTINGS)
print("BUILD_EXPORTED_FBX", FBX_PATH)


# ---- previews --------------------------------------------------------------
def look_at(loc, target, lens=35.0, ortho=None):
    CAM.location = loc
    d = mathutils.Vector((target[0] - loc[0], target[1] - loc[1], target[2] - loc[2]))
    CAM.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if ortho:
        CAM_D.type, CAM_D.ortho_scale = 'ORTHO', ortho
    else:
        CAM_D.type, CAM_D.lens = 'PERSP', lens


def shot(name, loc, target, res=(1500, 1000), lens=35.0, ortho=None, hide_roof=False):
    for n, o in bpy.data.objects.items():
        if o.name in OBJECT_MATERIAL and OBJECT_GROUP[o.name] == "Roof":
            o.hide_render = hide_roof
    look_at(loc, target, lens, ortho)
    SCENE.render.resolution_x, SCENE.render.resolution_y = res
    SCENE.render.filepath = os.path.join(OUT_DIR, "previews", name)
    bpy.ops.render.render(write_still=True)
    print("BUILD_RENDERED", name)


def B(x, d, h):
    return (x, Y(d), h)


if "--noprev" not in sys.argv:
    shot("front.png", B(26, -34, 16), B(0, 14, 5), lens=34)
    shot("rear_patio.png", B(24, 62, 16), B(0, 34, 3), lens=32)
    shot("interior_plan.png", B(0, 17, 70), B(0, 17, 0), res=(1400, 1500), ortho=40.0, hide_roof=True)
    shot("top.png", B(0, 24, 90), B(0, 24, 0), res=(1500, 1500), ortho=62.0)
    shot("grill_closeup.png", B(10, 31.0, 4.4), B(10, 35.6, 3.0), lens=38)
    shot("family_story.png", B(-4.0, 11.0, 6.2), B(-14.6, 11.0, 5.0), lens=40, hide_roof=True)
    shot("photos_aprons.png", B(0.0, 24.6, 7.0), B(14.6, 24.6, 5.4), lens=40, hide_roof=True)
    shot("photos_left.png", B(-4.0, 24.0, 6.4), B(-14.6, 24.0, 5.8), lens=40, hide_roof=True)
    shot("kitchen.png", B(8.0, 12.0, 5.5), B(14.0, 14.0, 3.5), lens=32, hide_roof=True)
    for o in bpy.data.objects:
        if o.name in OBJECT_MATERIAL and OBJECT_GROUP[o.name] == "Roof":
            o.hide_render = False

# ---- manifest --------------------------------------------------------------
GROUP_STATS = {}
for gname, coll in GROUPS.items():
    GROUP_STATS[gname] = {"objects": len(coll.objects), "meshes": len([o for o in coll.objects if o.type == 'MESH'])}

LOGIC = {n: [round(v, 3) for v in b] for n, b in REG.items()}
MANIFEST = {
    "asset": ASSET,
    "variant": "GrillDadHouse (build %s)" % "2026-10-11",
    "game": "Steal a Dad!",
    "note": "Working asset name only; no Dad character, rarity or catalog change.",
    "units": {"blender_unit_equals_roblox_studs": 1.0, "scale_length": 0.01},
    "coordinate_mapping": {
        "logical": "(X,D,H): X left/right (left negative), D depth front 0 -> rear 48, H height above walking surface",
        "blender": "(x, y, z) = (X, D - 24, H); pivot (0,0,0) = logical (0, 24, 0)",
        "roblox_after_fbx": "Roblox X = -Blender x, Roblox Y = Blender z, Roblox Z = Blender y (proven FBX axis settings); "
                            "viewed from the front the logical +X is the owner's right.",
        "pivot_logical": [0, 24, 0],
        "pivot_relative_depth": "D - 24",
    },
    "dimensions_studs": {
        "property": {"x": [-22, 22], "d": [0, 48]},
        "house_body": {"x": [-15, 15], "d": [4, 30], "wall_height": WALL_H, "wall_thickness": WALL_T,
                       "footprint_polygon": POLY},
        "roof_eave_polygon": EAVE, "eave_h": EAVE_H, "ridge_h": RIDGE_H, "ridge": [list(RIDGE[0]), list(RIDGE[1])],
        "doors_clear": {"width": DOOR_W, "height": DOOR_H, "front_center": [0, 5.2], "rear_center": [0, 30]},
        "chimney": {"center": [CHIM_X, CHIM_D], "body_h": [11.8, 17.6]},
        "measured_bounds_all_objects": {"X": [round(allx0, 3), round(allx1, 3)], "D": [round(alld0, 3), round(alld1, 3)]},
        "measured_roof_envelope": {"X": [round(min(b[0] for b in roof_b), 3), round(max(b[1] for b in roof_b), 3)],
                                   "D": [round(min(b[2] for b in roof_b), 3), round(max(b[3] for b in roof_b), 3)],
                                   "Hmax": round(max(b[5] for b in roof_b), 3)},
    },
    "protected_volumes": {k: {"x": list(v[0]), "d": list(v[1]), "h": list(v[2])} for k, v in PROTECTED.items()},
    "protected_audit": {"violations": VIOL, "count": len(VIOL)},
    "door_leaf_open_positions": CLEAR.get("door_leaf_tips", {}),
    "reference_helpers": {k: {"logical_XDH": list(v)} for k, v in HELPERS.items()},
    "reference_ratios_design": {
        "house_width_over_property": round(30 / 44, 3), "house_depth_over_property": round(26 / 48, 3),
        "wall_height_over_width": round(11.5 / 30, 3), "ridge_over_width": round(16.4 / 30, 3),
        "lane_over_width": round(8 / 30, 3), "apron_adult_child": round(0.95 / 0.60, 3),
        "plate_dad_ordinary": round(1.0 / 0.55, 3), "firebox_over_sausage": round(3.4 / 0.55, 3),
        "sofa_ratio": round(6.6 / 4.6, 3)},
    "materials": {k: {"srgb_hex": v["srgb_hex"], "srgb255": list(v["srgb255"]), "linear": [round(c, 5) for c in v["linear"]],
                      "alpha": v["alpha"]} for k, v in sorted(MATERIALS.items())},
    "object_groups": GROUP_STATS,
    "counts": {"mesh_objects_exported": len(mesh_objects()), "triangles_exported": tri_count(),
               "noncollide_objects": len(NONCOLLIDE),
               "triangle_method": "sum(max(vertices-2,0)) over evaluated meshes with modifiers applied"},
    "collision_hint": {"noncollide_note": "Objects in noncollide_objects are set CanCollide=false by the Studio script; "
                                          "structural floor/walls/dry ground/main furniture/grill/fence bodies stay collidable.",
                       "mesh_fidelity": "Roblox MeshPart CollisionFidelity left at Default; see VERIFICATION_RU.md"},
    "fbx_export_settings": {k: (sorted(v) if isinstance(v, set) else v) for k, v in FBX_SETTINGS.items()},
    "previews": sorted(os.listdir(os.path.join(OUT_DIR, "previews"))),
    "fence_post_centres": FENCE_INFO,
    "documented_adjustments": [
        "Side fences start at D=0.8 (not 0.6) so their first post abuts the front-fence corner post instead of overlapping it.",
        "Connector for FamilyPad_02 uses D=13.1..16.1 (3 wide) to stay clear of the side loveseat (starts D=16.2).",
        "Backing frames for story graphics sit at X=-14.60 (wall face) .. -14.58 so they touch the room-side wall plane.",
    ],
}
MANIFEST["object_materials"] = dict(sorted(OBJECT_MATERIAL.items()))
MANIFEST["object_groups_map"] = dict(sorted(OBJECT_GROUP.items()))
MANIFEST["noncollide_objects"] = sorted(NONCOLLIDE)
with open(os.path.join(OUT_DIR, "manifest.json"), "w", encoding="utf-8") as fh:
    json.dump(MANIFEST, fh, indent=1)
with open(os.path.join(OUT_DIR, "component_registry.json"), "w", encoding="utf-8") as fh:
    json.dump({"note": "bbox = [Xmin,Xmax,Dmin,Dmax,Hmin,Hmax] in logical studs",
               "components": [{"name": n, "group": OBJECT_GROUP[n], "material": OBJECT_MATERIAL[n],
                               "collision": "noncollide" if n in NONCOLLIDE else "collide", "bbox": LOGIC[n]}
                              for n in OBJECT_ORDER if n in LOGIC]}, fh, indent=0)
print("BUILD_MANIFEST_TRIS", MANIFEST["counts"]["triangles_exported"], "OBJECTS", MANIFEST["counts"]["mesh_objects_exported"],
      "NONCOLLIDE", len(NONCOLLIDE))


# ---- Studio colour / anchor / collision script -------------------------------
def srgb255(lin):
    out = []
    for v in lin:
        v = min(max(v, 0.0), 1.0)
        s = v * 12.92 if v <= 0.0031308 else 1.055 * (v ** (1 / 2.4)) - 0.055
        out.append(int(round(s * 255)))
    return out


assert len(OBJECT_ORDER) == len(set(OBJECT_ORDER)), "duplicate object names"
lines = [
    "--!strict",
    "-- Generated by build_grill_dad_house.py -- do not edit by hand.",
    "-- Roblox's FBX importer drops plain material colours, so every MeshPart of an imported",
    "-- GrillDadHouse arrives default grey. Run this once in the Studio command bar after import.",
    "",
    "local PALETTE: { [string]: { color: Color3, material: Enum.Material, transparency: number } } = {",
]
for mname in sorted(MATERIALS):
    r, g, b = srgb255(MATERIALS[mname]["linear"])
    rm = "Glass" if mname.endswith("GLASS") else "SmoothPlastic"
    lines.append('\t["%s"] = { color = Color3.fromRGB(%d, %d, %d), material = Enum.Material.%s, transparency = %s },' % (
        mname, r, g, b, rm, round(1.0 - MATERIALS[mname]["alpha"], 2)))
lines += ["}", "", "local PARTS: { [string]: string } = {"]
for n in OBJECT_ORDER:
    lines.append('\t["%s"] = "%s",' % (n, OBJECT_MATERIAL[n]))
lines += ["}", "", "local NONCOLLIDE: { [string]: boolean } = {"]
for n in sorted(NONCOLLIDE):
    lines.append('\t["%s"] = true,' % n)
lines += [
    "}", "",
    'local model = workspace:FindFirstChild("GrillDadHouse", true)',
    'assert(model, "GrillDadHouse not found in Workspace -- import the FBX first")',
    "",
    "local painted, noncollided, missed = 0, 0, {}",
    "for _, inst in ipairs(model:GetDescendants()) do",
    '\tif inst:IsA("BasePart") then',
    '\t\tlocal entry = PALETTE[PARTS[inst.Name] or ""]',
    "\t\tif entry then",
    "\t\t\tinst.Color = entry.color",
    "\t\t\tinst.Material = entry.material",
    "\t\t\tinst.Transparency = entry.transparency",
    "\t\t\tinst.Anchored = true",
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
    'print(string.format("GrillDadHouse: painted %d parts (%d set non-colliding), %d unmatched", painted, noncollided, #missed))',
    "if #missed > 0 then",
    '\twarn("unmatched parts: " .. table.concat(missed, ", "))',
    "end",
    "",
]
with open(os.path.join(OUT_DIR, "apply_grill_dad_house_colors.luau"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
print("BUILD_LUAU", len(OBJECT_ORDER), "parts", len(NONCOLLIDE), "noncollide")
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("BUILD_DONE")
