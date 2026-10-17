"""Procedural Blender build of the simplified Gamer Dad in a sweatshirt ("Steal a Dad!"), Review stage.

Source of truth: GamerDad_Sweatshirt_MasterPrompt_RU + inputs/GamerDad_Sweatshirt_Construction_Spec.json (prescribed plan, not measured geometry).
Primary appearance reference: inputs/GamerDad_Sweatshirt_Approved_Reference.png (middle figure = front view).

Frames / units
--------------
1 Blender unit = 1 Roblox stud. Blender world (x, y, z) = logical (X, D, H): X<0 anatomical RIGHT (the hand with the can), D<0 = front, H up, soles at H = 0.
FBX export axis_forward='Z', axis_up='Y' (project mapping): Roblox model position of (X, D, H) = (-X, H, D), the character faces -Z. det = +1, no mirroring.

Run headless:
    blender -b --factory-startup --python build_gamer_dad_sweatshirt.py -- <output_dir> [--quick] [--norender] [--keepcomp]
The file is concatenated from parts/p00..p06 by assemble.sh.
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
KEEPCOMP = "--keepcomp" in sys.argv
INP = os.path.join(HERE, "inputs")
SPEC_IN = json.load(open(os.path.join(INP, "GamerDad_Sweatshirt_Construction_Spec.json"), encoding="utf-8"))
os.makedirs(os.path.join(OUT, "renders"), exist_ok=True)

for _ob in list(bpy.data.objects):
    bpy.data.objects.remove(_ob, do_unlink=True)
for _blk in (bpy.data.meshes, bpy.data.materials, bpy.data.collections, bpy.data.cameras, bpy.data.lights, bpy.data.images):
    for _it in list(_blk):
        _blk.remove(_it)
SCENE = bpy.context.scene
SCENE.unit_settings.system = 'METRIC'
SCENE.unit_settings.scale_length = 0.01        # project convention (not an additional coordinate multiplier)

# ---- palette: 34 colours of the prescribed plan, index = tile index (col = i % 8, row = i // 8 in the 8x8 grid of 32 px tiles) ----
PAL = [(p["id"], p["hex"]) for p in SPEC_IN["palette"]]
TILE = {n: i for i, (n, _) in enumerate(PAL)}
ATLAS_PX = 1024
TILE_PX = 32
COLS = 8

# UV map ids (per-face int layer "uvm"); 0 = palette tile centre
UVM_TILE, UVM_GAMEPAD, UVM_CANWRAP, UVM_FACE, UVM_CANTOP, UVM_NOSE = 0, 1, 2, 3, 4, 5
CAN_C = V((-1.62, -1.32, 3.86))
PRINT_C = (0.0, 3.76)


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def tile_uv(idx):
    col, row = idx % COLS, idx // COLS
    return (TILE_PX * col + TILE_PX / 2.0) / ATLAS_PX, 1.0 - (TILE_PX * row + TILE_PX / 2.0) / ATLAS_PX


def px_uv(px, py):
    return px / ATLAS_PX, 1.0 - py / ATLAS_PX


def map_uv(uvm, p, face_theta=None):
    """Atlas UV (prescribed formulas, section 20) of a world-space point p for the map id."""
    x, d, h = p
    if uvm == UVM_GAMEPAD:
        return px_uv(384.0 + 204.0 * (x - PRINT_C[0]), 128.0 - 204.0 * (h - PRINT_C[1]))
    if uvm == UVM_FACE:
        return px_uv(256.0 * (x + 1.01) / 2.02, 256.0 + 512.0 * (6.22 - h) / 1.62)
    if uvm == UVM_NOSE:
        return px_uv(384.0 + 256.0 * x / 0.53, 512.0 + 128.0 * (5.45 - h) / 0.46)
    if uvm == UVM_CANTOP:
        return px_uv(384.0 + 128.0 * (x - CAN_C.x) / 0.245, 384.0 + 128.0 * (d - CAN_C.y) / 0.245)
    if uvm == UVM_CANWRAP:
        z = h - CAN_C.z
        return px_uv(768.0 + 512.0 * face_theta / (2.0 * math.pi), 512.0 * (0.54 - z) / 1.15)
    raise ValueError(uvm)


# ---------------------------------------------------------------------------------------------- generic geometry helpers
def tri_count(bm):
    return sum(len(f.verts) - 2 for f in bm.faces)


def make_bm_solid(P, faces, closed=True):
    bm = bmesh.new()
    vs = [bm.verts.new(V(p)) for p in P]
    bm.verts.ensure_lookup_table()
    for f in faces:
        ids = list(dict.fromkeys(f))
        if len(ids) < 3:
            continue
        try:
            fc = bm.faces.new([vs[i] for i in ids])
        except ValueError:
            continue
        fc.normal_update()
        if fc.calc_area() < 1e-9:
            bm.faces.remove(fc)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if closed and bm.verts:
        cen = sum((v.co for v in bm.verts), V()) / len(bm.verts)
        vol = 0.0
        for f in bm.faces:
            vv = [v.co - cen for v in f.verts]
            for k in range(1, len(vv) - 1):
                vol += vv[0].dot(vv[k].cross(vv[k + 1])) / 6.0
        if vol < 0.0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.normal_update()
    return bm


PARTS = {}
COMP_LOG = []


class PM:
    """One runtime body part: a bmesh with per-face palette tile ("tile"), uv-map id ("uvm") and registry index ("comp")."""

    def __init__(self, runtime, joint, xf=None, geo=None):
        self.runtime = runtime
        self.geo = geo or (runtime + "_Geo")
        self.joint = V(joint)
        self.bm = bmesh.new()
        self.tl = self.bm.faces.layers.int.new("tile")
        self.ul = self.bm.faces.layers.int.new("uvm")
        self.cl = self.bm.faces.layers.int.new("comp")
        self.xf = xf
        self.comps = []
        PARTS[runtime] = self

    def _tx(self, p):
        p = V(p)
        return self.xf(p) if self.xf else p

    def append_bm(self, cid, bm, tilefn, meta=None, kind="mesh"):
        """Copy a finished component bmesh into this part (tile chosen per face by tilefn(normal, centre) or taken from the source layer)."""
        meta = dict(meta or {})
        vmap = {}
        n_faces = 0
        tiles = set()
        tl_src = bm.faces.layers.int.get("tile")
        for f in bm.faces:
            vv = []
            for v in f.verts:
                if v.index not in vmap:
                    vmap[v.index] = self.bm.verts.new(self._tx(v.co))
                vv.append(vmap[v.index])
            try:
                nf = self.bm.faces.new(vv)
            except ValueError:
                continue
            nf.normal_update()
            if nf.calc_area() < 1e-10:
                self.bm.faces.remove(nf)
                continue
            if tilefn is None and tl_src is not None:
                t = f[tl_src]
            elif callable(tilefn):
                t = TILE[tilefn(nf.normal.copy(), nf.calc_center_median())]
            else:
                t = TILE[tilefn]
            nf[self.tl] = t
            nf[self.ul] = UVM_TILE
            nf[self.cl] = len(COMP_LOG)
            tiles.add(PAL[t][0])
            n_faces += 1
        self.bm.verts.ensure_lookup_table()
        rec = {"id": cid, "owner": self.runtime, "kind": kind, "tiles": sorted(tiles), "faces": n_faces, "tris": sum(len(f.verts) - 2 for f in bm.faces)}
        rec.update(meta)
        self.comps.append(rec)
        COMP_LOG.append(rec)
        return rec

    def solid(self, cid, P, faces, tilefn, meta=None, closed=True):
        bm = make_bm_solid(P, faces, closed)
        rec = self.append_bm(cid, bm, tilefn, meta)
        bm.free()
        return rec

    def comp_index(self, cid):
        for i, r in enumerate(COMP_LOG):
            if r["id"] == cid and r["owner"] == self.runtime:
                return i
        raise KeyError(cid)

    def faces_of(self, cid):
        ci = self.comp_index(cid)
        return [f for f in self.bm.faces if f[self.cl] == ci]

    def set_map(self, cid, uvm, pred=None, tile=None, note=None):
        """Assign a UV map (and fallback tile) to the faces of a component that satisfy pred(face)."""
        n = 0
        for f in self.faces_of(cid):
            f.normal_update()
            if pred is None or pred(f):
                f[self.ul] = uvm
                if tile is not None:
                    f[self.tl] = TILE[tile]
                n += 1
        return n

    def paint(self, cid, tile, pred, planes=None, only=None):
        """Split the (optionally filtered) faces of a component by planes and tint the faces satisfying pred (flat colour region, no geometry offset)."""
        faces = [f for f in self.faces_of(cid) if only is None or only(f)]
        if planes:
            for co, no in planes:
                geom = list({e for f in faces if f.is_valid for e in f.edges}) + [f for f in faces if f.is_valid] + list({v for f in faces if f.is_valid for v in f.verts})
                res = bmesh.ops.bisect_plane(self.bm, geom=geom, dist=1e-6, plane_co=co, plane_no=no)
                faces = [f for f in self.faces_of(cid) if only is None or only(f)]
        n = 0
        for f in self.faces_of(cid):
            f.normal_update()
            if pred(f):
                f[self.tl] = TILE[tile]
                n += 1
        return n


def cap_tris(P, idxs):
    pts = [P[i] for i in idxs]
    if len(pts) == 3:
        return [list(idxs)]
    tris = mgeo.tessellate_polygon([pts])
    return [[idxs[a], idxs[b], idxs[c]] for a, b, c in tris]


def loft_faces(nrings, n, caps=(True, True)):
    faces = []
    for i in range(nrings - 1):
        for k in range(n):
            a = i * n + k
            b = i * n + (k + 1) % n
            c = (i + 1) * n + (k + 1) % n
            d = (i + 1) * n + k
            faces.append([a, b, c, d])
    if caps[0]:
        faces.append(list(range(n)))
    if caps[1]:
        faces.append(list(range((nrings - 1) * n, nrings * n)))
    return faces


def loft(pm, cid, rings, tilefn, caps=(True, True), meta=None, band_tiles=None):
    """Closed loft through equal-length rings. band_tiles={band_index: tile name} overrides the colour of the quads between ring i and i+1."""
    n = len(rings[0])
    P = [p for r in rings for p in r]
    faces = loft_faces(len(rings), n, caps)
    bm = make_bm_solid(P, faces)
    rec = pm.append_bm(cid, bm, tilefn, meta)
    bm.free()
    if band_tiles:
        # re-tint by band using the ring index of the face vertices
        ring_of = {}
        for i, r in enumerate(rings):
            for p in r:
                ring_of[(round(p.x, 5), round(p.y, 5), round(p.z, 5))] = i
        ci = len(COMP_LOG) - 1
        for f in pm.bm.faces:
            if f[pm.cl] != ci:
                continue
            ids = []
            for v in f.verts:
                k = pm._tx(v.co) if False else v.co
                ids.append(ring_of.get((round(k.x, 5), round(k.y, 5), round(k.z, 5)), -1))
            if -1 in ids or len(set(ids)) != 2:
                continue
            lo = min(ids)
            if max(ids) - lo == 1 and lo in band_tiles:
                f[pm.tl] = TILE[band_tiles[lo]]
    return rec


def ring8(a, f, b, c, cx=0.0, cd=0.0, h=0.0):
    pts = [(-a + c, f), (a - c, f), (a, f + c), (a, b - c), (a - c, b), (-a + c, b), (-a, b - c), (-a, f + c)]
    return [V((cx + x, cd + y, h)) for x, y in pts]


def ring12(W, Df, Db, c, cx=0.0, h=0.0):
    """12-point chamfered ring of the prescribed torso / head tables (section 06)."""
    a = W / 2.0
    pts = [(-a + c, Df), (-W / 4.0, Df), (W / 4.0, Df), (a - c, Df), (a, Df + c), (a, Db - c), (a - c, Db), (W / 4.0, Db), (-W / 4.0, Db), (-a + c, Db), (-a, Db - c), (-a, Df + c)]
    return [V((cx + x, d, h)) for x, d in pts]


def cbox(c, size, ch, rot=None):
    """Chamfered box rings (4 rings of 8 points along local H). size = (sx, sd, sh). rot: optional 3x3 rotation of the local frame (x, d, h)."""
    sx, sd, sh = size
    ch = min(ch, sx / 2 - 1e-4, sd / 2 - 1e-4, sh / 2 - 1e-4)
    out = []
    for dz, sh_in in ((-sh / 2, ch), (-sh / 2 + ch, 0), (sh / 2 - ch, 0), (sh / 2, ch)):
        a, b = sx / 2 - sh_in, sd / 2 - sh_in
        cc = min(ch, a - 1e-4, b - 1e-4)
        ring = []
        for p in ring8(a, -b, b, cc, 0.0, 0.0, dz):
            q = (rot @ p) if rot is not None else p
            ring.append(q + V(c))
        out.append(ring)
    return out


def tile_layer(bm):
    return bm.faces.layers.int.get("tile") or bm.faces.layers.int.new("tile")


def solid_tiled(P, faces, tilename):
    bm = make_bm_solid(P, faces)
    tl = tile_layer(bm)
    for f in bm.faces:
        f[tl] = TILE[tilename]
    return bm


def box_solid(x0, x1, y0, y1, z0, z1, tilename, ch=0.0):
    c = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    rings = cbox(c, (x1 - x0, y1 - y0, z1 - z0), max(ch, 1e-4))
    P = [p for r in rings for p in r]
    return solid_tiled(P, loft_faces(len(rings), 8), tilename)


def cyl_solid(cx, cy, z0, z1, r, tilename, segs=24):
    r0 = [V((cx + r * math.cos(2 * math.pi * k / segs), cy + r * math.sin(2 * math.pi * k / segs), z0)) for k in range(segs)]
    r1 = [p + V((0, 0, z1 - z0)) for p in r0]
    return solid_tiled(r0 + r1, loft_faces(2, segs), tilename)


def bm_to_obj(bm, name):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    ob = bpy.data.objects.new(name, me)
    SCENE.collection.objects.link(ob)
    return ob


def obj_to_bm(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.normal_update()
    return bm


def bool_apply(a_obj, b_obj, op, solver='EXACT'):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = a_obj
    a_obj.select_set(True)
    m = a_obj.modifiers.new("B", 'BOOLEAN')
    m.object = b_obj
    m.operation = op
    m.solver = solver
    bpy.ops.object.modifier_apply(modifier=m.name)


def retile(bm, fn):
    tl = tile_layer(bm)
    for f in bm.faces:
        f.normal_update()
        f[tl] = TILE[fn(f.normal.copy(), f.calc_center_median())]


def interp_rows(rows, h):
    """Linear interpolation of a table [(H, v1, v2, ...)]."""
    if h <= rows[0][0]:
        return rows[0][1:]
    if h >= rows[-1][0]:
        return rows[-1][1:]
    for a, b in zip(rows, rows[1:]):
        if a[0] <= h <= b[0]:
            t = (h - a[0]) / (b[0] - a[0])
            return tuple(a[i] + (b[i] - a[i]) * t for i in range(1, len(a)))


class Limb:
    """Limb frame proximal P0 -> distal P1. U = world X projected perpendicular to A (width), Q = A x U (depth)."""

    def __init__(self, P0, P1):
        self.P0, self.P1 = V(P0), V(P1)
        d = self.P1 - self.P0
        self.L = d.length
        self.A = d / self.L
        u = V((1, 0, 0)) - self.A * V((1, 0, 0)).dot(self.A)
        if u.length < 1e-4:
            u = V((0, -1, 0)) - self.A * V((0, -1, 0)).dot(self.A)
        self.U = u.normalized()
        self.Q = self.A.cross(self.U).normalized()

    def at(self, t):
        return self.P0 + self.A * (self.L * t)

    def ring(self, t, w, d, c, grow=0.0):
        P = self.at(t)
        a, h = w / 2.0 + grow, d / 2.0 + grow
        c = min(c, a - 1e-4, h - 1e-4)
        pts = [(-a + c, -h), (a - c, -h), (a, -h + c), (a, h - c), (a - c, h), (-a + c, h), (-a, h - c), (-a, -h + c)]
        return [P + self.U * x + self.Q * y for x, y in pts]


def clip_halfspace(bm, co, no):
    """Keep the side of the plane opposite to `no`; the closed solid stays closed (the cut is filled with one flat face)."""
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-7, plane_co=co, plane_no=no, clear_outer=True, clear_inner=False)
    bnd = [e for e in bm.edges if e.is_boundary]
    if bnd:
        bmesh.ops.holes_fill(bm, edges=bnd, sides=len(bnd) + 2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()


def rot_about_z(p, pivot, deg):
    a = math.radians(deg)
    q = V(p) - V(pivot)
    return V((pivot[0] + q.x * math.cos(a) - q.y * math.sin(a), pivot[1] + q.x * math.sin(a) + q.y * math.cos(a), q.z + pivot[2]))


def deviate(msg):
    DEVIATIONS.append(msg)


DEVIATIONS = []


# ----------------------------------------------------------------------------------------------
# shading rules (big zones, no per-triangle noise)
# ----------------------------------------------------------------------------------------------
def sh_const(name):
    return lambda n, c: name


def sh_sweat(n, c):
    if n.z > 0.45:
        return "SWEATSHIRT_LIGHT"
    if n.z < -0.45:
        return "SWEATSHIRT_DARK"
    return "SWEATSHIRT"


def sh_shorts(n, c):
    if n.z < -0.6:
        return "SHORTS_DARK"
    if n.z > 0.6:
        return "SHORTS_LIGHT"
    return "SHORTS"


def sh_skin(n, c):
    if n.z > 0.55:
        return "SKIN_LIGHT"
    if n.z < -0.55:
        return "SKIN_SHADOW"
    return "SKIN"


def sh_sole(n, c):
    return "SOLE_SHADOW" if n.z < -0.2 else "SOLE"


def sh_hair(n, c):
    if n.z < -0.30:
        return "HAIR_DARK"
    if n.z > 0.62:
        return "HAIR_LIGHT"
    return "HAIR"


def sh_beard(n, c):
    if n.z < -0.40:
        return "BEARD_DARK"
    if n.z > 0.35 and n.y < 0.2:
        return "BEARD_LIGHT"
    return "BEARD"


# ----------------------------------------------------------------------------------------------
# prescribed joints (HoldCan world frame) and tables
# ----------------------------------------------------------------------------------------------
JOINTS = {k: tuple(float(c) for c in v) for k, v in SPEC_IN["joints_holdcan"].items()}
JV = {k: V(v) for k, v in JOINTS.items()}
UT_ROWS = [tuple(r) for r in SPEC_IN["torso_rows"]]       # H, W, Df, Db, c
HEAD_ROWS = [tuple(r) for r in SPEC_IN["head_rows"]]
COMP_SPEC = {c["id"]: c for c in SPEC_IN["components"]}
UP_LEN, LO_LEN = SPEC_IN["arm_lengths"]["upper"], SPEC_IN["arm_lengths"]["lower"]


def spec_c(cid):
    return COMP_SPEC[cid]


def meta(recipe, cls="prescribed", **kw):
    d = {"recipe": recipe, "class": cls}
    d.update(kw)
    return d


# ----------------------------------------------------------------------------------------------
# UpperTorso: sweatshirt shell (12-point rings), rib hem, crewneck band, flat gamepad print on the real front surface
# ----------------------------------------------------------------------------------------------
ut = PM("UpperTorso", JV["Waist"])
loft(ut, "UT_shell", [ring12(W, Df, Db, c, 0.0, H) for H, W, Df, Db, c in UT_ROWS], sh_sweat,
     meta=meta("closed loft of 7 chamfered 12-point rings (H,W,Df,Db,c from the spec), centre X=0", rows=UT_ROWS))
# gamepad print: cut the front faces by the print window (X +/-.60, H 3.76 +/-.60) and give those faces the gamepad atlas map
PRINT_HALF = 0.60
ut.paint("UT_shell", "SWEATSHIRT", lambda f: False,
         planes=[((PRINT_HALF, 0, 0), (1, 0, 0)), ((-PRINT_HALF, 0, 0), (1, 0, 0)), ((0, 0, PRINT_C[1] + PRINT_HALF), (0, 0, 1)), ((0, 0, PRINT_C[1] - PRINT_HALF), (0, 0, 1))],
         only=lambda f: f.normal.y < -0.5)
n_print = ut.set_map("UT_shell", UVM_GAMEPAD, lambda f: f.normal.y < -0.5 and abs(f.calc_center_median().x) < PRINT_HALF - 1e-4 and abs(f.calc_center_median().z - PRINT_C[1]) < PRINT_HALF - 1e-4, tile="SWEATSHIRT")
COMP_LOG[ut.comp_index("UT_shell")]["print_faces"] = n_print
COMP_LOG.append({"id": "UT_gamepad", "owner": "UpperTorso", "kind": "texture", "recipe": "flat gamepad print: atlas rect 256,0-512,256, px = 384+204x, py = 128-204h on the actual front faces of UT_shell (window X+/-.60, H3.16..4.36)",
                 "faces": n_print, "tris": 0, "class": "prescribed"})
loft(ut, "UT_hem", cbox((0, -0.105, 2.48), (3.02, 1.55, 0.18), 0.06), sh_const("CUFF"), meta=meta("rib hem 3.02 x 1.55 x .18, bevel .06"))
# crewneck: closed elliptical band (rectangle section swept round an ellipse): outer 1.24 x 1.02, inner 1.06 x 0.84, height .10, 16 segments
CN_C = V((0.0, -0.02, 4.47))
sections = []
for k in range(16):
    a = 2 * math.pi * k / 16
    ca, sa = math.cos(a), math.sin(a)
    sections.append([V((CN_C.x + .62 * ca, CN_C.y + .51 * sa, CN_C.z - .05)), V((CN_C.x + .62 * ca, CN_C.y + .51 * sa, CN_C.z + .05)),
                     V((CN_C.x + .53 * ca, CN_C.y + .42 * sa, CN_C.z + .05)), V((CN_C.x + .53 * ca, CN_C.y + .42 * sa, CN_C.z - .05))])
P = [p for s in sections for p in s]
F = []
for i in range(16):
    for j in range(4):
        F.append([i * 4 + j, i * 4 + (j + 1) % 4, ((i + 1) % 16) * 4 + (j + 1) % 4, ((i + 1) % 16) * 4 + j])
ut.solid("UT_crewneck", P, F, sh_const("CUFF"), meta("closed elliptical band, outer 1.24 x 1.02, inner 1.06 x .84, height .10, 16 segments, CUFF"))

# ----------------------------------------------------------------------------------------------
# LowerTorso: pelvis, waistband, flat centre seam
# ----------------------------------------------------------------------------------------------
lt = PM("LowerTorso", JV["Root"])
loft(lt, "LT_pelvis", cbox((0, -0.025, 2.32), (2.80, 1.16, 0.44), 0.13), sh_shorts, meta=meta("inner closed chamfer box 2.80 x 1.16 x .44, bevel .13, centre X=0"))
loft(lt, "LT_waistband", cbox((0, -0.025, 2.47), (2.98, 1.32, 0.16), 0.06), sh_const("SHORTS_DARK"), meta=meta("waistband 2.98 x 1.32 x .16, bevel .06"))
n_seam = lt.paint("LT_pelvis", "SHORTS_DARK",
                  lambda f: f.normal.y < -0.6 and abs(f.calc_center_median().x) < 0.0095 and 2.16 < f.calc_center_median().z < 2.44,
                  planes=[((0.009, 0, 0), (1, 0, 0)), ((-0.009, 0, 0), (1, 0, 0)), ((0, 0, 2.16), (0, 0, 1)), ((0, 0, 2.44), (0, 0, 1))], only=lambda f: f.normal.y < -0.6)
COMP_LOG.append({"id": "LT_seam", "owner": "LowerTorso", "kind": "paint", "recipe": "flat centre seam 0.018 wide x .28 high (H2.16..2.44) painted SHORTS_DARK on the pelvis front, no geometry offset", "faces": n_seam, "tris": 0, "class": "prescribed"})

# ----------------------------------------------------------------------------------------------
# legs: one shorts profile for both sides (mirrored X), open skin shins, hem lip
# ----------------------------------------------------------------------------------------------
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    ul = PM(side + "UpperLeg", JV[side + "Hip"])
    rows = spec_c("UL_shorts_" + side)["rows_H_cx_cD_W_D"]
    rings = [ring8(w / 2.0, cD - dep / 2.0, cD + dep / 2.0, 0.10, cx, 0.0, H) for H, cx, cD, w, dep in rows]
    loft(ul, "UL_shorts_" + side, rings, sh_shorts, meta=meta("shorts leg, 4 chamfered rings, bevel .10, no patch pockets", rows=rows))
    ll = PM(side + "LowerLeg", JV[side + "Knee"])
    loft(ll, "LL_skin_" + side, cbox((s * 1.01, 0.0, 1.00), (0.72, 0.67, 0.52), 0.07), sh_skin, meta=meta("open skin shin .72 x .67 x .52, bevel .07"))
    # technical hem lip: spec centre H1.245 is a hidden slab flush with the UL hem; moved to H1.19..1.23 so that its top sinks .01 into the UpperLeg and the hem line is a clean edge
    loft(ll, "LL_shorts_edge_" + side, cbox((s * 1.00, -0.02, 1.21), (1.48, 1.16, 0.04), 0.02), sh_const("SHORTS"), meta=meta("hem lip 1.48 x 1.16 x .04, bevel .02 (spec centre H1.245 shifted to 1.21, see deviations)"))
deviate("LL_shorts_edge: spec centre H1.245 (1.22..1.27) lies entirely inside the UpperLeg hem and its bottom face is coplanar with the UL bottom cap; the slab is placed at H1.19..1.23 (top sinks .01 into UpperLeg as the text demands) to give a visible, clean hem line without z-fighting.")

# ----------------------------------------------------------------------------------------------
# shoes: every shoe component rotated once about H through the ankle axis (right -8 deg, left +8 deg)
# ----------------------------------------------------------------------------------------------
UP_ROWS = [(0.22, 1.26, -1.10, 0.56), (0.47, 1.22, -1.07, 0.53), (0.72, 1.10, -0.87, 0.47), (0.88, 0.94, -0.48, 0.42)]
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    yaw = 8.0 * s
    pivot = (s * 1.02, 0.0, 0.0)
    ft = PM(side + "Foot", JV[side + "Ankle"])

    def rr(ring, yaw=yaw, pivot=pivot):
        return [rot_about_z(p, pivot, yaw) for p in ring]
    sole = make_bm_solid([p for r in cbox((s * 1.10, -0.275, 0.11), (1.32, 1.75, 0.22), 0.10) for p in r], loft_faces(4, 8))
    toe = make_bm_solid([p for r in cbox((s * 1.10, -1.03, 0.29), (1.16, 0.24, 0.28), 0.07) for p in r], loft_faces(4, 8))
    o1, o2 = bm_to_obj(sole, "tmp_sole"), bm_to_obj(toe, "tmp_toe")
    bool_apply(o1, o2, 'UNION')
    bm_u = obj_to_bm(o1)
    bpy.data.objects.remove(o1, do_unlink=True)
    bpy.data.objects.remove(o2, do_unlink=True)
    sole.free()
    toe.free()
    for v in bm_u.verts:
        v.co = rot_about_z(v.co, pivot, yaw)
    bm_u.normal_update()
    ft.append_bm("FT_sole_" + side, bm_u, sh_sole, meta("sole 1.32 x 1.75 x .22 (bevel .10) fused with the white toe cap 1.16 x .24 x .28 (bevel .07) by boolean union; yaw %+.0f deg about the ankle axis" % yaw))
    bm_u.free()
    COMP_LOG.append({"id": "FT_toe_white_" + side, "owner": side + "Foot", "kind": "merged", "recipe": "white toe cap fused into FT_sole (boolean union, hidden faces removed)", "faces": 0, "tris": 0, "class": "prescribed"})
    rings = [rr(ring8(w / 2.0, f, b, 0.12, s * 1.10, 0.0, h - (0.01 if i == 0 else 0.0))) for i, (h, w, f, b) in enumerate(UP_ROWS)]
    loft(ft, "FT_upper_" + side, rings, sh_const("SHOE"), meta=meta("one closed chamfered loft, 4 rings, bevel .12 (first ring sunk .01 into the sole)", rows=UP_ROWS))
deviate("FT_upper: first ring H0.22 is sunk to H0.21 so that the upper bottom does not coincide with the sole top plane.")


# ----------------------------------------------------------------------------------------------
# arms: sleeves with ONE common elbow contour, rib cuffs, blocky hands (right hand with the open can recess)
# ----------------------------------------------------------------------------------------------
UP_SECS = [(0.0, 0.88, 0.92, 0.10), (0.5, 0.84, 0.87, 0.10), (1.0, 0.78, 0.80, 0.08)]       # t from the shoulder S: width U, depth Q, bevel
LO_SECS = [(0.0, 0.78, 0.80, 0.08), (1.0, 0.70, 0.70, 0.08)]                               # t from the elbow E
ELBOW_LOG = {}


def sec_lin(secs, t):
    """(w, d, c) of a section table at t (clamped linear)."""
    if t <= secs[0][0]:
        return secs[0][1:]
    if t >= secs[-1][0]:
        return secs[-1][1:]
    for a, b in zip(secs, secs[1:]):
        if a[0] <= t <= b[0]:
            u = (t - a[0]) / (b[0] - a[0])
            return tuple(a[i] + (b[i] - a[i]) * u for i in range(1, 4))


def oct_pts(w, d, c):
    a, h = w / 2.0, d / 2.0
    c = min(c, a - 1e-4, h - 1e-4)
    return [(-a + c, -h), (a - c, -h), (a, -h + c), (a, h - c), (a - c, h), (-a + c, h), (-a, h - c), (-a, -h + c)]


def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def build_arm(side, S, E, W):
    """UpperArm along S->E, LowerArm along E->W. Both sleeves end on the common mitre plane through E (normal N = normalize(Au + Al)):
    the upper tube is cut by the plane, its 8-point cut contour K becomes the first ring of the lower tube, which then rolls into its own forearm frame.
    No overlap beyond the joint, no cap or ball at the elbow."""
    ua = PM(side + "UpperArm", S)
    lu = Limb(S, E)
    la = PM(side + "LowerArm", E)
    ll = Limb(E, W)
    L1, L2 = lu.L, ll.L
    Au, Al = lu.A, ll.A
    N = (Au + Al).normalized()
    an = Au.dot(N)
    assert an > 0.2 and Al.dot(N) > 0.2, (side, an, Al.dot(N))

    def sd(p):
        return (p - E).dot(N)
    # ---- upper tube: stations from S-.08 to beyond E, each ring line is cut by the plane
    EXT = 0.60
    base = [(-0.08 / L1, 0.88, 0.92, 0.10)] + UP_SECS + [(1.0 + EXT / L1, 0.78, 0.80, 0.08)]

    def ring_at(t):
        w, d, c = sec_lin([(b[0], b[1], b[2], b[3]) for b in base], t)
        return lu.ring(t, w, d, c)
    ts = [b[0] for b in base]
    cross = []
    for k in range(8):
        found = None
        for t0, t1 in zip(ts, ts[1:]):
            s0, s1 = sd(ring_at(t0)[k]), sd(ring_at(t1)[k])
            if s0 < 0.0 <= s1:
                found = t0 + (t1 - t0) * (-s0) / (s1 - s0)
                break
        assert found is not None, (side, k)
        cross.append(found)
    K = [ring_at(cross[k])[k] for k in range(8)]
    for p in K:
        assert abs(sd(p)) < 1e-5
    stations = sorted(set([round(t, 9) for t in ts if t < max(cross)] + [round(c, 9) for c in cross]))
    rings_u = []
    for t in stations:
        base_ring = ring_at(t)
        rings_u.append([base_ring[k] if t <= cross[k] + 1e-9 else K[k] for k in range(8)])
    # weld coincident points, build the closed solid
    uniq, canon, ids = [], {}, []
    for r in rings_u:
        for p in r:
            key = (round(p.x * 1e5), round(p.y * 1e5), round(p.z * 1e5))
            if key not in canon:
                canon[key] = len(uniq)
                uniq.append(V(p))
            ids.append(canon[key])
    faces = [[ids[i] for i in f] for f in loft_faces(len(rings_u), 8)]
    ua.solid("UA_sleeve_" + side, uniq, faces, sh_sweat,
             meta("sleeve .88x.92 -> .84x.87 -> .78x.80 (bevel .10 -> .08), hidden .08 into the torso, ends on the common elbow mitre plane (8-point contour K)", sections=UP_SECS))
    # ---- lower tube: K -> straight to the axial level of the farthest K point -> roll into the own forearm frame
    ax = [(p - E).dot(Al) for p in K]
    lat = [(p - E) - Al * a for p, a in zip(K, ax)]
    s_hi = max(ax) + 1e-4
    # match every K vertex with a vertex of the forearm octagon by angle (even shifts keep the orientation, odd shifts with reversed order mirror it)
    Ul, Ql = ll.U, ll.Q

    def ang(v):
        return math.atan2(v.dot(Ql), v.dot(Ul))
    w0, d0, c0 = LO_SECS[0][1:]
    tbl0 = oct_pts(w0, d0, c0)
    phi = [math.atan2(y, x) for x, y in tbl0]
    th = [ang(v) for v in lat]
    best = None
    for o in (1, -1):
        for m in range(8):
            if (o == 1 and m % 2) or (o == -1 and m % 2 == 0):
                continue
            err = 0.0
            for i in range(8):
                j = (i + m) % 8 if o == 1 else (m - i) % 8
                dd = (th[i] - phi[j] + math.pi) % (2 * math.pi) - math.pi
                err += abs(dd)
            if best is None or err < best[0]:
                best = (err, o, m)
    _, o_, m_ = best
    jmap = [((i + m_) % 8 if o_ == 1 else (m_ - i) % 8) for i in range(8)]
    t_beta0 = s_hi / L2
    t_beta1 = max(t_beta0 + 0.12, 0.70)

    def lring(t):
        w, d, c = sec_lin(LO_SECS, t)
        tb = oct_pts(w, d, c)
        beta = smooth01((t - t_beta0) / (t_beta1 - t_beta0))
        P = E + Al * (t * L2)
        out = []
        for i in range(8):
            x, y = tb[jmap[i]]
            target = Ul * x + Ql * y
            off = lat[i] * (1.0 - beta) + target * beta
            out.append(P + off)
        return out
    tts = []
    for t in (t_beta0, 0.5 * (t_beta0 + t_beta1), t_beta1, 0.85, 1.0):
        if not tts or t > tts[-1] + 1e-6:
            tts.append(t)
    rings_l = [K] + [lring(t) for t in tts]
    # closing ring at the wrist: a slightly smaller copy .02 further, so the end is a flat closed cap
    rings_l.append([P_ - Al * 0.0 + Al * (0.02) for P_ in rings_l[-1]])
    P = [p for r in rings_l for p in r]
    la.solid("LA_sleeve_" + side, P, loft_faces(len(rings_l), 8), sh_sweat,
             meta("forearm sleeve: first ring = common contour K, rolled into the own frame; .78x.80 -> .70x.70 (bevel .08), beta from t=%.3f to %.3f; K match o=%d m=%d" % (t_beta0, t_beta1, o_, m_), sections=LO_SECS))
    # ---- rib cuff t .77 .. 1.02 (.76 x .76, bevel .045), own forearm frame, CUFF
    cuff = []
    for t, wd in ((0.77, 0.72), (0.785, 0.76), (1.0, 0.76), (1.02, 0.72)):
        cuff.append(ll.ring(t, wd, wd, 0.045))
    loft(la, "LA_cuff_" + side, cuff, sh_const("CUFF"), meta=meta("rib cuff t.77..1.02, .76 x .76, bevel .045, CUFF, no ribs"))
    ELBOW_LOG[side] = {"N": tuple(N), "deflection_deg": math.degrees(math.acos(max(-1, min(1, Au.dot(Al))))), "contour_K": [tuple(p) for p in K], "cross_t_upper": cross,
                       "lower_K_axial": ax, "lower_match": {"orientation": o_, "shift": m_}, "beta_t": [t_beta0, t_beta1], "upper_len": L1, "lower_len": L2}
    return lu, ll


R_UA, R_LA = build_arm("Right", JV["RightShoulder"], JV["RightElbow"], JV["RightWrist"])
L_UA, L_LA = build_arm("Left", JV["LeftShoulder"], JV["LeftElbow"], JV["LeftWrist"])

# ---- hands: chamfer box + fused thumb (boolean union), right hand with the open can recess (cylinder R.328 coaxial with the can), flat finger lines
CAN_AXIS = (-1.62, -1.32)
CAN_RAD_REC = 0.328


def sh_skin_hand(n, c):
    if n.z > 0.55:
        return "SKIN_LIGHT"
    if n.z < -0.55:
        return "SKIN_SHADOW"
    return "SKIN"


def make_hand(side, palm_c, palm_size, thumb_c, thumb_size, cutters):
    hp = PM(side + "Hand", JV[side + "Wrist"])
    palm = make_bm_solid([p for r in cbox(palm_c, palm_size, 0.055) for p in r], loft_faces(4, 8))
    thumb = make_bm_solid([p for r in cbox(thumb_c, thumb_size, 0.04) for p in r], loft_faces(4, 8))
    o = bm_to_obj(palm, "tmp_palm")
    ot = bm_to_obj(thumb, "tmp_thumb")
    bool_apply(o, ot, 'UNION')
    bpy.data.objects.remove(ot, do_unlink=True)
    palm.free()
    thumb.free()
    for cb in cutters:
        co = bm_to_obj(cb, "tmp_cut")
        bool_apply(o, co, 'DIFFERENCE')
        bpy.data.objects.remove(co, do_unlink=True)
        cb.free()
    bm = obj_to_bm(o)
    bpy.data.objects.remove(o, do_unlink=True)
    retile(bm, sh_skin_hand)
    hp.append_bm("HAND_palm_" + side, bm, None, meta("chamfer box %s bevel .055 with the fused thumb block %s bevel .04 (boolean union, one shell)" % (palm_size, thumb_size)))
    bm.free()
    COMP_LOG.append({"id": "HAND_thumb_" + side, "owner": side + "Hand", "kind": "merged", "recipe": "thumb block %s fused with the palm (boolean union)" % (thumb_size,), "faces": 0, "tris": 0, "class": "prescribed"})
    return hp


rh_c, lh_c = SPEC_IN["hand_centers"]["Right"], SPEC_IN["hand_centers"]["Left"]
rec_cut = cyl_solid(CAN_AXIS[0], CAN_AXIS[1], rh_c[2] - 0.7, rh_c[2] + 0.7, CAN_RAD_REC, "SKIN_SHADOW", segs=32)
RHP = make_hand("Right", rh_c, (0.70, 0.64, 0.82), (-1.96, -1.48, 3.93), (0.18, 0.22, 0.26), [rec_cut])
# left hand: small thumb notch open to -X (under the thumb)
lt_notch = box_solid(1.58, 1.70, -0.41, -0.19, 2.268, 2.3215, "SKIN_SHADOW", ch=0.0)
LHP = make_hand("Left", lh_c, (0.70, 0.64, 0.72), (1.68, -0.30, 2.4515283654817543), (0.18, 0.22, 0.26), [lt_notch])
# recess wall in SKIN_SHADOW (inside the can radius), finger lines: exactly two flat lines per hand, width .008, length .35 at H-.14 and H+.12
for hp, side, c in ((RHP, "Right", rh_c), (LHP, "Left", lh_c)):
    cid = "HAND_palm_" + side
    if side == "Right":
        for f in hp.faces_of(cid):
            f.normal_update()
            cc = f.calc_center_median()
            if math.hypot(cc.x - CAN_AXIS[0], cc.y - CAN_AXIS[1]) < CAN_RAD_REC + 0.004 and abs(f.normal.z) < 0.3:
                f[hp.tl] = TILE["SKIN_SHADOW"]
    planes = []
    for dh in (-0.14, 0.12):
        h = c[2] + dh
        planes += [((0, 0, h + 0.004), (0, 0, 1)), ((0, 0, h - 0.004), (0, 0, 1))]
    planes += [((c[0] + 0.175, 0, 0), (1, 0, 0)), ((c[0] - 0.175, 0, 0), (1, 0, 0))]
    fr = lambda f: f.normal.y < -0.9 and f.calc_center_median().y < c[1] - 0.2
    n_g = hp.paint(cid, "SKIN_SHADOW", lambda f: f.normal.y < -0.9 and abs(f.calc_center_median().x - c[0]) < 0.176 and any(abs(f.calc_center_median().z - (c[2] + dh)) < 0.0041 for dh in (-0.14, 0.12)),
                   planes=planes, only=fr)
    COMP_LOG.append({"id": "HAND_grooves_" + side, "owner": side + "Hand", "kind": "paint", "recipe": "two flat SKIN_SHADOW lines .008 x .35 at H-.14 and H+.12 on the front face, no geometry", "faces": n_g, "tris": 0, "class": "prescribed"})


# ----------------------------------------------------------------------------------------------
# Head: neck, shell with the printed face, ears, brows, nose, moustache, ONE U-shaped beard shell, hair cap + 3 locks
# ----------------------------------------------------------------------------------------------
hd = PM("Head", JV["Neck"])
loft(hd, "HD_neck", cbox((0.0, 0.0, 4.53), (0.72, 0.65, 0.26), 0.08), sh_const("SKIN"), meta=meta("neck block .72 x .65 x .26, bevel .08 (top hidden in the head, bottom in the sweatshirt)"))
loft(hd, "HD_shell", [ring12(W, Df, Db, c, 0.0, H) for H, W, Df, Db, c in HEAD_ROWS], sh_skin,
     meta=meta("closed loft of 7 chamfered 12-point rings (spec head_rows), front faces carry the printed face map", rows=HEAD_ROWS))
n_face = hd.set_map("HD_shell", UVM_FACE, lambda f: f.normal.y < -0.35, tile="SKIN")
COMP_LOG[hd.comp_index("HD_shell")]["face_faces"] = n_face
for nm in ("eye_white", "iris", "eye_highlight"):
    for s in ("R", "L"):
        COMP_LOG.append({"id": "HD_%s_%s" % (nm, s), "owner": "Head", "kind": "texture", "recipe": "printed on the actual head front faces, atlas face rect 0,256-256,768 (px = 256(X+1.01)/2.02, py = 256+512(6.22-H)/1.62)", "faces": 0, "tris": 0, "class": "prescribed"})
COMP_LOG.append({"id": "HD_mouth", "owner": "Head", "kind": "texture", "recipe": "flat MOUTH line printed in the skin notch of the beard", "faces": 0, "tris": 0, "class": "prescribed"})

for s, side in ((-1, "R"), (1, "L")):
    # ear block, outer inner-patch painted (SKIN_SHADOW 0.19 along D, 0.25 along H) on the outer face X = +/-1.135
    loft(hd, "HD_ear_" + side, cbox((s * 1.015, 0.005, 5.23), (0.24, 0.40, 0.50), 0.065), sh_const("SKIN"), meta=meta("ear block .24 x .40 x .50, bevel .065, no helix"))
    cx = s * 1.14
    n_e = hd.paint("HD_ear_" + side, "SKIN_SHADOW", lambda f, s=s: f.normal.x * s > 0.9 and abs(f.calc_center_median().y + 0.07) < 0.0951 and abs(f.calc_center_median().z - 5.24) < 0.1251,
                   planes=[((0, -0.07 + 0.095, 0), (0, 1, 0)), ((0, -0.07 - 0.095, 0), (0, 1, 0)), ((0, 0, 5.24 + 0.125), (0, 0, 1)), ((0, 0, 5.24 - 0.125), (0, 0, 1))], only=lambda f, s=s: f.normal.x * s > 0.9)
    COMP_LOG.append({"id": "HD_ear_inner_" + side, "owner": "Head", "kind": "paint", "recipe": "flat SKIN_SHADOW patch .19 x .25 on the outer ear face (no geometry)", "faces": n_e, "tris": 0, "class": "prescribed"})


def head_front_d(h):
    return interp_rows(HEAD_ROWS, h)[1]            # Df of the head table at height h (W, Df, Db, c -> index 1)


# brows: one bevelled bar per side along two given points, thickness .105 along D, .16 across, standing .035 proud of the skin
def brow(side, A, B):
    ax = V((B[0] - A[0], 0.0, B[1] - A[1]))
    L = ax.length
    ex = ax / L
    ey = V((0, 1, 0))
    ez = ex.cross(ey)
    rot = Matrix(((ex.x, ey.x, ez.x), (ex.y, ey.y, ez.y), (ex.z, ey.z, ez.z)))
    mid = ((A[0] + B[0]) / 2.0, (A[1] + B[1]) / 2.0)
    dsk = head_front_d(mid[1])
    c = V((mid[0], dsk - 0.035 + 0.105 / 2.0, mid[1]))
    loft(hd, "HD_brow_" + side, cbox(c, (L, 0.105, 0.16), 0.025, rot=rot), sh_const("BROW"), meta=meta("single bevelled brow bar, endpoints XH %s -> %s, thickness .105, height .16, .035 proud, bevel .025" % (A, B)))


brow("R", (-0.68, 5.70), (-0.10, 5.56))
brow("L", (0.10, 5.56), (0.68, 5.70))

# nose: one closed wedge loft, nostril marks come from the nose atlas map
NOSE_ROWS = [(4.99, 0.36, -0.98, -0.67), (5.13, 0.53, -1.13, -0.67), (5.31, 0.38, -1.02, -0.68), (5.45, 0.25, -0.88, -0.67)]
loft(hd, "HD_nose", [ring8(w / 2.0, f, b, 0.05, 0.0, 0.0, h) for h, w, f, b in NOSE_ROWS], sh_const("NOSE"), meta=meta("closed wedge loft 4 rings, bevel .05", rows=NOSE_ROWS))
hd.set_map("HD_nose", UVM_NOSE, None, tile="NOSE")
COMP_LOG.append({"id": "HD_nostrils", "owner": "Head", "kind": "texture", "recipe": "two flat nostril marks printed through the nose atlas map (px = 384+256X/.53, py = 512+128(5.45-H)/.46)", "faces": 0, "tris": 0, "class": "prescribed"})

# moustache: bevelled lobe .48 x .25 x .19 at (+/-.235,-.93,4.985), outer end dropped .035; BEARD, BEARD_DARK underneath only
for s, side in ((-1, "R"), (1, "L")):
    bmm = make_bm_solid([p for r in cbox((s * 0.235, -0.8775, 4.985), (0.48, 0.355, 0.19), 0.05) for p in r], loft_faces(4, 8))
    for v in bmm.verts:
        t = min(1.0, abs(v.co.x) / 0.475)
        v.co.z -= 0.035 * t
    bmm.normal_update()
    hd.append_bm("HD_moustache_" + side, bmm, lambda n, c: "BEARD_DARK" if n.z < -0.5 else "BEARD", meta("bevelled lobe .48 x .19, front face D-1.055 (spec), back extended to D-.70 to reach the skin, outer end drop .035, bevel .05"))
    bmm.free()
deviate("HD_moustache: spec centre D-.93 / depth .25 leaves a .125 gap to the skin (skin front D-.68); the back face is extended to D-.70 (centre -.8775, depth .355), front face unchanged at D-1.055.")

# beard: ONE closed U-shaped shell: front contour (X,H) lifted to Dfront(X), its copy at Drear(X), bevel .065 on the front rim
BEARD_XH = [list(pt) for pt in spec_c("HD_beard")["contour_XH"]]
# local narrowing of the cheek corners (idx 0, 9: +/-.94 -> +/-.90, idx 10, 16: +/-1.00 -> +/-.93): the mic boom passes the cheek corner at X=1.00 and touched the beard (clearance .004)
for _i, _x in ((0, -0.90), (9, 0.90), (10, 0.93), (16, -0.93)):
    BEARD_XH[_i][0] = _x
deviate("HD_beard: the cheek corners of the contour are pulled in (idx 0/9 |X| .94 -> .90, idx 10/16 |X| 1.00 -> .93, symmetric, widest width 1.86 instead of 2.00) because the mic boom of the spec touched the beard corner (clearance .004, required >= .03). Everything else of the contour and both depth formulas is unchanged.")


def d_front(x):
    return -1.04 + 0.18 * (abs(x) / 1.0) ** 1.5


def d_rear(x):
    return -0.45 + 0.55 * max(0.0, (abs(x) - 0.70) / 0.30)


nb = len(BEARD_XH)
PF = [V((x, d_front(x), h)) for x, h in BEARD_XH]
PB = [V((x, d_rear(x), h)) for x, h in BEARD_XH]
for x, h in BEARD_XH:
    assert d_rear(x) - d_front(x) > 0
P = PF + PB
Fc = [[i, (i + 1) % nb, nb + (i + 1) % nb, nb + i] for i in range(nb)]
poly2d = [V((x, h, 0.0)) for x, h in BEARD_XH]
tri = mgeo.tessellate_polygon([poly2d])
Fc += [[a, b, c] for a, b, c in tri]
Fc += [[nb + a, nb + b, nb + c] for a, b, c in tri]
bb = make_bm_solid(P, Fc)
front_edges = []
for e in bb.edges:
    fs = e.link_faces
    if len(fs) == 2 and any(f.normal.y < -0.5 and len(f.verts) == 3 for f in fs) and any(len(f.verts) == 4 for f in fs):
        front_edges.append(e)
bmesh.ops.bevel(bb, geom=front_edges, offset=0.065, offset_type='OFFSET', segments=1, profile=0.5, affect='EDGES')
bb.normal_update()
hd.append_bm("HD_beard", bb, sh_beard, meta("ONE closed extruded U polygon (17-point XH contour), front D = -1.04+.18(|X|/1)^1.5, rear D = -.45+.55max(0,(|X|-.70)/.30), front rim bevel .065 x 1 segment, no jitter, no shared sup_point",
                                          contour_XH=BEARD_XH))
bb.free()

# hair cap: ONE closed shell hugging the head (spec: 12 angular sections, rim H 6.01 front / 5.29 side / 4.74 back, top H 6.35, apex = ONE vertex, hidden inner surface .04 inward).
# The linear-in-r cone of the spec cuts into the skull at the sides (r=.92 ring sits 0.06 inside the head), so the levels follow the head surface offset outward instead.
HC_C = 0.05
HTOP = 6.35
NSEC = 24


def hrim(phi):
    a = abs((phi + math.pi) % (2 * math.pi) - math.pi)
    if a <= math.pi / 2:
        return 6.01 + (5.29 - 6.01) * a / (math.pi / 2)
    return 5.29 + (4.74 - 5.29) * (a - math.pi / 2) / (math.pi / 2)


def head_ring_xy(H):
    W, Df, Db, c = interp_rows(HEAD_ROWS, H)
    return [(p.x, p.y) for p in ring12(W, Df, Db, c, 0.0, 0.0)], (Df + Db) / 2.0


def head_radius(phi, H):
    poly, dc = head_ring_xy(H)
    dirv = V((math.sin(phi), -math.cos(phi)))
    c0 = V((0.0, dc))
    best = None
    for i in range(len(poly)):
        a, b = V(poly[i]), V(poly[(i + 1) % len(poly)])
        hit = mgeo.intersect_line_line_2d(c0, c0 + dirv * 6.0, a, b)
        if hit is not None:
            r = (hit - c0).length
            best = r if best is None else min(best, r)
    assert best is not None, (phi, H)
    return best, dc, dirv


HEAD_TOP_H = HEAD_ROWS[-1][0]
LV_U = [i / 8.0 for i in range(9)]
LV_T = [0.06 + 0.07 * u * u for u in LV_U]
outer_pts = []
ring_idx = []
for li, (u, tt) in enumerate(zip(LV_U, LV_T)):
    for k in range(NSEC):
        phi = 2 * math.pi * k / NSEC
        H = hrim(phi) + u * (HEAD_TOP_H - hrim(phi))
        r, dc, dv = head_radius(phi, H)
        outer_pts.append(V((dv.x * (r + tt), dc + dv.y * (r + tt), H)))
# dome ring: top ring shrunk to .55 and lifted, then the single apex vertex
for k in range(NSEC):
    phi = 2 * math.pi * k / NSEC
    r, dc, dv = head_radius(phi, HEAD_TOP_H)
    outer_pts.append(V((dv.x * (r + 0.09) * 0.55, dc + dv.y * (r + 0.09) * 0.55, HEAD_TOP_H + 0.075)))
apex = len(outer_pts)
outer_pts.append(V((0.0, head_ring_xy(HEAD_TOP_H)[1], HTOP)))
NLV = len(LV_U) + 1
FO = []
for lv in range(NLV - 1):
    for k in range(NSEC):
        a, b = lv * NSEC + k, lv * NSEC + (k + 1) % NSEC
        FO.append([a, b, b + NSEC, a + NSEC])
for k in range(NSEC):
    FO.append([(NLV - 1) * NSEC + k, (NLV - 1) * NSEC + (k + 1) % NSEC, apex])
aux = make_bm_solid(outer_pts, FO, closed=False)
aux.normal_update()
nrm = [V(v.normal) for v in aux.verts]
if nrm[apex].z < 0:
    nrm = [-n for n in nrm]
aux.free()
inner_pts = [p - n * 0.04 for p, n in zip(outer_pts, nrm)]
no = len(outer_pts)
P = outer_pts + inner_pts
FH = [list(f) for f in FO] + [[no + i for i in reversed(f)] for f in FO]
for k in range(NSEC):
    a, b = k, (k + 1) % NSEC
    FH.append([a, no + a, no + b, b])
hair = make_bm_solid(P, FH)
hd.append_bm("HD_hair_cap", hair, sh_hair, meta("ONE closed cap: 24 sections, rim H 6.01/5.29/4.74 (spec), 4 rings (9 levels) following the head surface offset .06..13, dome ring + ONE apex vertex at H6.35, inner surface .04 inward"))
hair.free()
# base band (first ring pair) = HAIR_DARK
for f in hd.faces_of("HD_hair_cap"):
    f.normal_update()
    cc = f.calc_center_median()
    phi_c = math.atan2(cc.x, -(cc.y - HC_C))
    if f.normal.z < 0.55 and f.normal.z > -0.3 and cc.z < hrim(phi_c) + 0.16:
        f[hd.tl] = TILE["HAIR_DARK"]
deviate("HD_hair_cap: the spec cone (X_r = r X, D_r = .05 + r(D-.05), H_r = 6.35 + r(Hrim-6.35)) lies inside the skull away from the apex (r=.92 side ring at X=.94 vs head X=1.01), so no hair would be visible. The cap uses 24 angular sections instead of 12 (at 30 deg steps the chords cut the chamfered rear corners of the head and skin shows through), the rim heights 6.01/5.29/4.74, the top H6.35 with ONE apex vertex and the .04 inner surface, but its rings follow the head surface offset outward by .06 (rim) .. .10 (top), 9 levels, and a dome ring.")

# three broad bevelled wedge locks over the front edge of the cap
LOCK_FR = [(-0.50, 0.50), (0.25, 0.50), (0.50, 0.05), (0.25, -0.50), (-0.10, -0.35), (-0.35, 0.10)]
for side, key in (("R", "HD_lock_R"), ("C", "HD_lock_C"), ("L", "HD_lock_L")):
    cs = spec_c(key)
    cx, cy, cz = cs["center_XDH"]
    sx, sd, sh = cs["size_XDH"]
    ang = cs["roll_about_D_deg"]
    pts2 = [(cx + fx * sx, cz + fh * sh) for fx, fh in LOCK_FR]
    n6 = len(pts2)
    P = [V((x, cy - sd / 2.0, h)) for x, h in pts2] + [V((x, cy + sd / 2.0, h)) for x, h in pts2]
    F6 = [[i, (i + 1) % n6, n6 + (i + 1) % n6, n6 + i] for i in range(n6)]
    tri6 = mgeo.tessellate_polygon([[V((x, h, 0.0)) for x, h in pts2]])
    F6 += [[a, b, c] for a, b, c in tri6] + [[n6 + a, n6 + b, n6 + c] for a, b, c in tri6]
    lk = make_bm_solid(P, F6)
    ed = [e for e in lk.edges if any(len(f.verts) == 3 for f in e.link_faces) and any(len(f.verts) == 4 for f in e.link_faces)]
    bmesh.ops.bevel(lk, geom=ed, offset=0.045, offset_type='OFFSET', segments=1, profile=0.5, affect='EDGES')
    Rm = Matrix.Rotation(math.radians(ang), 3, 'Y')
    cen = V((cx, cy, cz))
    for v in lk.verts:
        v.co = cen + Rm @ (v.co - cen)
    lk.normal_update()
    hd.append_bm(key, lk, sh_hair, meta("broad bevelled wedge %s x %s, roll %+.0f deg about D, bevel .045, 6-point XH profile" % (cs["size_XDH"], cs["center_XDH"], ang)))
    lk.free()


# ----------------------------------------------------------------------------------------------
# Headset (one export part): cups + pads + flat cyan rings, rectangular band sweep, boom, capsule
# ----------------------------------------------------------------------------------------------
HS_O = V((0.0, 0.0, 5.45))
hs = PM("Headset", HS_O)
A10 = math.radians(10.0)


def cup_frame(s):
    n = V((s * math.cos(A10), -math.sin(A10), 0.0))
    u = V((0, 0, 1))
    w = n.cross(u).normalized()
    return n, u, w


def axial_ring(C, n, u, w, t, r, segs=20):
    return [C + n * t + (u * math.cos(2 * math.pi * k / segs) + w * math.sin(2 * math.pi * k / segs)) * r for k in range(segs)]


for s, side in ((-1, "R"), (1, "L")):
    n, u, w = cup_frame(s)
    Cc = V((s * 1.16, -0.02, 5.44))
    prof = [(-0.12, 0.495), (-0.085, 0.53), (0.085, 0.53), (0.12, 0.495), (0.12, 0.44), (0.12, 0.34)]
    rings = [axial_ring(Cc, n, u, w, t, r) for t, r in prof]
    loft(hs, "HS_cup_" + side, rings, sh_const("HEADSET"), band_tiles={0: "HEADSET_EDGE", 2: "HEADSET_EDGE", 4: "CYAN"},
         meta=meta("cylinder dia 1.06, length .24 along n=(%+.4f,%.4f,0) (10 deg forward), 20 sides, edge bevel .035 (HEADSET_EDGE); flat CYAN ring r .34..44 on the outer end" % (s * math.cos(A10), -math.sin(A10))))
    n_cy = sum(1 for f in hs.faces_of("HS_cup_" + side) if f[hs.tl] == TILE["CYAN"])
    COMP_LOG.append({"id": "HS_cyan_" + side, "owner": "Headset", "kind": "paint", "recipe": "flat annular CYAN colour region r .34..44 on the outer cup end (no torus, no emission)", "faces": n_cy, "tris": 0, "class": "prescribed"})
    Cp = Cc - n * 0.19
    rings = [axial_ring(Cp, n, u, w, -0.07, 0.51), axial_ring(Cp, n, u, w, 0.07, 0.51)]
    loft(hs, "HS_pad_" + side, rings, sh_const("HEADSET_PAD"), meta=meta("soft pad dia 1.02, length .14 along n, centre Ccup-.19n, HEADSET_PAD"))

# band: closed rectangular sweep P(t) = (1.11 sin t, .12, 5.45 + .90 cos t), t -80..+80 deg, 12 segments, width .26 (D), radial thickness .10
sections = []
for k in range(13):
    t = math.radians(-80.0 + 160.0 * k / 12.0)
    P0 = V((1.11 * math.sin(t), 0.12, 5.45 + 0.90 * math.cos(t)))
    nr = V((0.90 * math.sin(t), 0.0, 1.11 * math.cos(t))).normalized()
    dv = V((0, 1, 0))
    sections.append([P0 - nr * 0.05 - dv * 0.13, P0 + nr * 0.05 - dv * 0.13, P0 + nr * 0.05 + dv * 0.13, P0 - nr * 0.05 + dv * 0.13])
loft(hs, "HS_band", sections, sh_const("HEADSET"), meta=meta("single swept rectangular band, 12 segments, width .26, radial thickness .10, top H6.40"))

# boom: 6-sided tube r .035 along the 4-point polyline, corners softened by .04
BOOM = [V(p) for p in ((1.18, -0.08, 5.30), (1.12, -0.61, 4.98), (0.88, -1.06, 4.82), (0.67, -1.12, 4.81))]
poly = [BOOM[0]]
for i in range(1, len(BOOM) - 1):
    d0 = (BOOM[i] - BOOM[i - 1]).normalized()
    d1 = (BOOM[i + 1] - BOOM[i]).normalized()
    poly += [BOOM[i] - d0 * 0.04, BOOM[i] + d1 * 0.04]
poly.append(BOOM[-1])
rings = []
prev_u = None
for i, p in enumerate(poly):
    if i == 0:
        T = (poly[1] - poly[0]).normalized()
    elif i == len(poly) - 1:
        T = (poly[-1] - poly[-2]).normalized()
    else:
        T = ((poly[i] - poly[i - 1]).normalized() + (poly[i + 1] - poly[i]).normalized()).normalized()
    if prev_u is None:
        prev_u = (V((0, 0, 1)) - T * V((0, 0, 1)).dot(T)).normalized()
    uu = (prev_u - T * prev_u.dot(T)).normalized()
    vv = T.cross(uu)
    prev_u = uu
    rings.append([p + (uu * math.cos(2 * math.pi * k / 6) + vv * math.sin(2 * math.pi * k / 6)) * 0.035 for k in range(6)])
loft(hs, "HS_boom", rings, sh_const("HEADSET"), meta=meta("one simple 6-sided tube r .035 along the 4-point polyline, corners cut by .04", points=[tuple(p) for p in BOOM]))
loft(hs, "HS_mic", cbox((0.58, -1.12, 4.81), (0.25, 0.14, 0.15), 0.05), sh_const("HEADSET_PAD"), meta=meta("mic capsule .25 x .14 x .15, bevel .05"))

# ----------------------------------------------------------------------------------------------
# EnergyCan: one closed lathe (20 segments, phi=0 towards -D), blue band wraps the atlas can map, recessed top cap carries the pull tab
# ----------------------------------------------------------------------------------------------
cn = PM("EnergyCan", CAN_C)
CAN_PROF = [(-0.72, 0.255), (-0.70, 0.29), (-0.66, 0.31), (-0.61, 0.31), (0.54, 0.31), (0.62, 0.28), (0.67, 0.25), (0.70, 0.265), (0.72, 0.265), (0.72, 0.245), (0.695, 0.245)]
rings = []
for z, r in CAN_PROF:
    rings.append([V((CAN_C.x + r * math.sin(2 * math.pi * k / 20), CAN_C.y - r * math.cos(2 * math.pi * k / 20), CAN_C.z + z)) for k in range(20)])
loft(cn, "CAN_body", rings, sh_const("SILVER"),
     band_tiles={2: "CAN_DARK", 3: "CAN_BLUE", 4: "CAN_LIGHT", 5: "CAN_LIGHT", 8: "SILVER_LIGHT"},
     meta=meta("closed lathe, 11 profile rings x 20 segments (phi=0 towards -D), blue band z-.61..+.54, CAN_LIGHT shoulder, CAN_DARK thin lower zone, SILVER rims", profile=CAN_PROF))
ci_body = cn.comp_index("CAN_body")
# blue band: wrap map; recessed top cap: can-top map
zc = lambda f: f.calc_center_median().z - CAN_C.z
n_wrap = cn.set_map("CAN_body", UVM_CANWRAP, lambda f: -0.611 < zc(f) < 0.541 and abs(f.normal.z) < 0.3, tile="CAN_BLUE")
n_top = cn.set_map("CAN_body", UVM_CANTOP, lambda f: abs(zc(f) - 0.695) < 1e-4 and f.normal.z > 0.9 and len(f.verts) >= 12, tile="SILVER")
COMP_LOG[ci_body]["wrap_faces"], COMP_LOG[ci_body]["top_faces"] = n_wrap, n_top
COMP_LOG.append({"id": "CAN_top", "owner": "EnergyCan", "kind": "texture", "recipe": "recessed top cap z+.695 (dia .49) with the printed pull tab, atlas can-top rect 256,256-512,512", "faces": n_top, "tris": 0, "class": "prescribed"})
COMP_LOG.append({"id": "CAN_bottom", "owner": "EnergyCan", "kind": "mesh", "recipe": "closed bottom end (existing cap face, dia .51), SILVER", "faces": 1, "tris": 18, "class": "prescribed"})
COMP_LOG.append({"id": "CAN_lightning", "owner": "EnergyCan", "kind": "texture", "recipe": "white lightning printed on the blue band: px = 768+512*theta/2pi, py = 512(.54-z)/1.15, theta = angle from -D", "faces": n_wrap, "tris": 0, "class": "prescribed"})


# ----------------------------------------------------------------------------------------------
# materials / UV (atlas tile centres + prescribed planar and cylindrical maps) / mesh objects
# ----------------------------------------------------------------------------------------------
SRC_COLL = bpy.data.collections.new("SOURCE_Components")
SCENE.collection.children.link(SRC_COLL)
EXP_COLL = bpy.data.collections.new("EXPORT_GamerDad")
SCENE.collection.children.link(EXP_COLL)

atlas = bpy.data.images.load(os.path.join(INP, "GamerDad_Sweatshirt_Atlas.png"))
atlas.name = "GamerDad_Sweatshirt_Atlas"
atlas.colorspace_settings.name = 'sRGB'
atlas.pack()
assert tuple(atlas.size) == (ATLAS_PX, ATLAS_PX), tuple(atlas.size)
_apx = atlas.pixels[:]


def atlas_rgb(px, py):
    o = ((ATLAS_PX - 1 - py) * ATLAS_PX + px) * 4
    return tuple(int(round(_apx[o + i] * 255)) for i in range(3))


# the atlas palette tile centres must equal the 34 hex colours (palette order = tile index)
PAL_CHECK = []
for i, (n_, h_) in enumerate(PAL):
    got = atlas_rgb((i % COLS) * TILE_PX + TILE_PX // 2, (i // COLS) * TILE_PX + TILE_PX // 2)
    PAL_CHECK.append({"index": i, "name": n_, "hex": h_, "atlas_rgb": got, "ok": got == hex_rgb(h_)})
assert all(c["ok"] for c in PAL_CHECK), [c for c in PAL_CHECK if not c["ok"]]

MATP = bpy.data.materials.new("GamerDad_Atlas")
MATP.use_nodes = True
nt = MATP.node_tree
bs = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = atlas
tex.interpolation = 'Closest'
nt.links.new(tex.outputs["Color"], bs.inputs["Base Color"])
bs.inputs["Roughness"].default_value = 0.8
try:
    bs.inputs["Specular IOR Level"].default_value = 0.05
except KeyError:
    pass

TWO_PI = 2.0 * math.pi
UV_STATS = {}
for pm in PARTS.values():
    bm = pm.bm
    bm.normal_update()
    me = bpy.data.meshes.new(pm.geo)
    bm.to_mesh(me)
    uv = me.uv_layers.new(name="UVMap")
    at_t, at_m, at_c = me.attributes.get("tile"), me.attributes.get("uvm"), me.attributes.get("comp")
    for pi, poly in enumerate(me.polygons):
        t = at_t.data[pi].value
        m = at_m.data[pi].value
        UV_STATS[m] = UV_STATS.get(m, 0) + 1
        if m == UVM_TILE:
            u_, v_ = tile_uv(t)
            for li in poly.loop_indices:
                uv.data[li].uv = (u_, v_)
            continue
        if m == UVM_CANWRAP:
            cc = V((0, 0, 0))
            for vi in poly.vertices:
                cc += me.vertices[vi].co
            cc /= len(poly.vertices)
            thc = math.atan2(cc.x - CAN_C.x, -(cc.y - CAN_C.y))
        for li in poly.loop_indices:
            p = me.vertices[me.loops[li].vertex_index].co
            if m == UVM_CANWRAP:
                th = math.atan2(p.x - CAN_C.x, -(p.y - CAN_C.y))
                th += TWO_PI * round((thc - th) / TWO_PI)
                th = max(-math.pi, min(math.pi, th))
                uv.data[li].uv = map_uv(m, p, th)
            else:
                uv.data[li].uv = map_uv(m, p)
    me.materials.append(MATP)
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new(pm.geo, me)
    EXP_COLL.objects.link(ob)
    off = pm.joint.copy()
    for v in me.vertices:
        v.co -= off
    ob.location = off
    pm.obj = ob
    pm.n_faces_final = len(me.polygons)

# per-component face totals (comp attribute is only valid before it is dropped below)
COMP_FACES = {}
for pm in PARTS.values():
    at_c = pm.obj.data.attributes.get("comp")
    for pi in range(len(pm.obj.data.polygons)):
        COMP_FACES[COMP_LOG[at_c.data[pi].value]["id"] + "@" + pm.runtime] = COMP_FACES.get(COMP_LOG[at_c.data[pi].value]["id"] + "@" + pm.runtime, 0) + 1
if not KEEPCOMP:
    for pm in PARTS.values():
        for nm in ("tile", "uvm", "comp"):
            a_ = pm.obj.data.attributes.get(nm)
            if a_ is not None:
                pm.obj.data.attributes.remove(a_)
for pm in PARTS.values():
    pm.bm.free()

# ----------------------------------------------------------------------------------------------
# armature (project-standard hierarchy) + rigid 100% weights; the model is built directly in the HoldCan pose (rest pose == display pose)
# ----------------------------------------------------------------------------------------------
BODY_NAMES = ["Head", "UpperTorso", "LowerTorso", "RightUpperArm", "RightLowerArm", "RightHand", "LeftUpperArm", "LeftLowerArm", "LeftHand",
              "RightUpperLeg", "RightLowerLeg", "RightFoot", "LeftUpperLeg", "LeftLowerLeg", "LeftFoot"]
PROPS = ["Headset", "EnergyCan"]
assert set(BODY_NAMES + PROPS) == set(PARTS), set(PARTS) ^ set(BODY_NAMES + PROPS)
arm_data = bpy.data.armatures.new("GamerDad_Armature")
ARM_OB = bpy.data.objects.new("GamerDad_Armature", arm_data)
EXP_COLL.objects.link(ARM_OB)
bpy.context.view_layer.objects.active = ARM_OB
ARM_OB.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones
BONES = [
    ("Root", None, V((0, 0, 0)), V((0, 0, 1.0))),
    ("HumanoidRootNode", "Root", JV["Root"], JV["Root"] + V((0, 0, .5))),
    ("LowerTorso", "HumanoidRootNode", JV["Root"], JV["Waist"]),
    ("UpperTorso", "LowerTorso", JV["Waist"], JV["Neck"]),
    ("Head", "UpperTorso", JV["Neck"], V((0, 0, 6.40))),
]
for side in ("Right", "Left"):
    ank = JV[side + "Ankle"]
    BONES += [
        (side + "UpperArm", "UpperTorso", JV[side + "Shoulder"], JV[side + "Elbow"]),
        (side + "LowerArm", side + "UpperArm", JV[side + "Elbow"], JV[side + "Wrist"]),
        (side + "Hand", side + "LowerArm", JV[side + "Wrist"], JV[side + "Wrist"] + V((0, 0, -.68))),
        (side + "UpperLeg", "LowerTorso", JV[side + "Hip"], JV[side + "Knee"]),
        (side + "LowerLeg", side + "UpperLeg", JV[side + "Knee"], JV[side + "Ankle"]),
        (side + "Foot", side + "LowerLeg", JV[side + "Ankle"], V((ank.x, ank.y - .78, .12))),
    ]
for name, parent, head, tail in BONES:
    b = eb.new(name)
    b.head, b.tail = head, tail
    b.use_connect = False
for name, parent, head, tail in BONES:
    if parent:
        eb[name].parent = eb[parent]
bpy.ops.object.mode_set(mode='OBJECT')
for pm in PARTS.values():
    bone = "Head" if pm.runtime == "Headset" else ("RightHand" if pm.runtime == "EnergyCan" else pm.runtime)
    ob = pm.obj
    vg = ob.vertex_groups.new(name=bone)
    vg.add([v.index for v in ob.data.vertices], 1.0, 'REPLACE')
    md = ob.modifiers.new("Armature", 'ARMATURE')
    md.object = ARM_OB
    ob.parent = ARM_OB
    ob.matrix_parent_inverse = Matrix.Identity(4)
PB = ARM_OB.pose.bones
for pb in PB:
    pb.rotation_mode = 'QUATERNION'
    pb.rotation_quaternion = Quaternion((1, 0, 0, 0))
    pb.location = V((0, 0, 0))
    pb.scale = V((1, 1, 1))
bpy.context.view_layer.update()
POSE_IDENTITY = all(pb.rotation_quaternion.angle < 1e-9 and pb.location.length < 1e-9 for pb in PB)

# ----------------------------------------------------------------------------------------------
# audits
# ----------------------------------------------------------------------------------------------
def world_verts(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ev.matrix_world
    out = [mw @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    return out


def bbox(pts):
    lo = V((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = V((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def mesh_audit(ob):
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    open_e = sum(1 for e in bm.edges if len(e.link_faces) == 1)
    nm = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    zero = sum(1 for f in bm.faces if f.calc_area() < 1e-8)
    cen = sum((v.co for v in bm.verts), V()) / max(1, len(bm.verts))
    vol = 0.0
    for f in bm.faces:
        vv = [v.co - cen for v in f.verts]
        for k in range(1, len(vv) - 1):
            vol += vv[0].dot(vv[k].cross(vv[k + 1])) / 6.0
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    bm.free()
    uvs = me.uv_layers.active.data
    uv_bad = sum(1 for l in uvs if not (-1e-6 <= l.uv[0] <= 1 + 1e-6 and -1e-6 <= l.uv[1] <= 1 + 1e-6))
    return {"verts": len(me.vertices), "tris": tris, "open_edges": open_e, "nonmanifold_edges": nm, "zero_faces": zero, "signed_volume": round(vol, 5), "uv_outside_0_1": uv_bad}


AUDIT = {pm.runtime: mesh_audit(pm.obj) for pm in PARTS.values()}
ALLV = {pm.runtime: world_verts(pm.obj) for pm in PARTS.values()}
body_lo, body_hi = bbox([p for n in BODY_NAMES for p in ALLV[n]])
all_lo, all_hi = bbox([p for n in BODY_NAMES + PROPS for p in ALLV[n]])
feet_lo, _ = bbox(ALLV["RightFoot"] + ALLV["LeftFoot"])
body_tris = sum(AUDIT[n]["tris"] for n in BODY_NAMES)
prop_tris = sum(AUDIT[n]["tris"] for n in PROPS)
print("AUDIT", json.dumps({k: [v["open_edges"], v["nonmanifold_edges"], v["zero_faces"], v["tris"], v["uv_outside_0_1"]] for k, v in AUDIT.items()}))
print("BOUNDS", [round(c, 4) for c in all_lo], [round(c, 4) for c in all_hi], "feet min H", round(feet_lo.z, 5), "tris body/props", body_tris, prop_tris)


def bvh_world(name):
    ob = PARTS[name].obj
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ev.matrix_world
    verts = [mw @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys), verts


def pair_check(a, b):
    ta, va = bvh_world(a)
    tb, vb = bvh_world(b)
    ov = len(ta.overlap(tb))
    d = 1e9
    for p in va:
        loc, nrm_, idx, dist = tb.find_nearest(p)
        d = min(d, dist)
    for p in vb:
        loc, nrm_, idx, dist = ta.find_nearest(p)
        d = min(d, dist)
    return {"overlapping_triangle_pairs": ov, "min_vertex_to_surface": round(d, 4)}


CHECKS = {}
for a, b in (("EnergyCan", "RightHand"), ("EnergyCan", "RightLowerArm"), ("EnergyCan", "RightUpperArm"), ("EnergyCan", "UpperTorso"), ("EnergyCan", "Head"), ("EnergyCan", "Headset"),
             ("Headset", "Head"), ("Headset", "UpperTorso"), ("LeftHand", "LowerTorso"), ("LeftHand", "LeftUpperLeg"), ("LeftHand", "UpperTorso"),
             ("RightUpperArm", "RightLowerArm"), ("LeftUpperArm", "LeftLowerArm"), ("RightLowerArm", "RightHand"), ("LeftLowerArm", "LeftHand"),
             ("RightUpperLeg", "LeftUpperLeg"), ("RightFoot", "LeftFoot"), ("RightLowerLeg", "RightFoot"), ("UpperTorso", "LowerTorso"), ("UpperTorso", "RightUpperArm"), ("UpperTorso", "LeftUpperArm")):
    CHECKS[a + "_vs_" + b] = pair_check(a, b)


def comp_world_tris(part, cid):
    """triangles (world) of one registered component of a part (needs the comp attribute: only valid with --keepcomp)."""
    return None


def tri_set(ob, prefix_ids=None):
    return None


# ----------------------------------------------------------------------------------------------
# outputs: blend, FBX, data
# ----------------------------------------------------------------------------------------------
for sub in ("export", "data", "source"):
    os.makedirs(os.path.join(OUT, sub), exist_ok=True)
BLEND = os.path.join(OUT, "source", "GamerDad_Sweatshirt_Review.blend")
FBX_BODY = os.path.join(OUT, "export", "GamerDad_R15.fbx")
FBX_PROPS = os.path.join(OUT, "export", "GamerDad_Props.fbx")
FBX_SET = dict(use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y',
               mesh_smooth_type='FACE', use_mesh_modifiers=True, bake_anim=False, add_leaf_bones=False,
               path_mode='COPY', embed_textures=True, use_armature_deform_only=False, primary_bone_axis='Y', secondary_bone_axis='X')


def export_fbx(path, objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, object_types={'MESH', 'ARMATURE'}, **FBX_SET)


export_fbx(FBX_BODY, [ARM_OB] + [PARTS[n].obj for n in BODY_NAMES])
prop_copies = []
for n in PROPS:
    cp = bpy.data.objects.new(n + "_Geo", PARTS[n].obj.data.copy())
    cp.data.name = n + "_Geo_export"
    EXP_COLL.objects.link(cp)
    cp.location = PARTS[n].joint
    prop_copies.append(cp)
export_fbx(FBX_PROPS, prop_copies)
for cp in prop_copies:
    bpy.data.objects.remove(cp, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("EXPORTED", FBX_BODY, FBX_PROPS, BLEND)


def r3(v, n=4):
    return [round(float(c), n) for c in v]


def roblox_pos(p):
    return [round(-p[0], 5), round(p[2], 5), round(p[1], 5)]


os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
shutil_copy = __import__("shutil").copy
shutil_copy(os.path.join(INP, "GamerDad_Sweatshirt_Atlas.png"), os.path.join(OUT, "GamerDad_Sweatshirt_Atlas.png"))
uvmap = {"atlas": "GamerDad_Sweatshirt_Atlas.png", "size": [ATLAS_PX, ATLAS_PX], "tile_px": TILE_PX, "columns": COLS, "palette_rect_px": [0, 0, 256, 256],
         "tile_uv_rule": "u=(32 col+16)/1024, v=1-(32 row+16)/1024", "tiles": [], "maps": {
             "gamepad": "px=384+204x, py=128-204h (x,h relative to the print centre X=0,H=3.76) on the real front faces of UT_shell inside the window X+/-.60, H3.16..4.36",
             "face": "px=256(X+1.01)/2.02, py=256+512(6.22-H)/1.62 on the front faces of HD_shell (normal.y<-.35)",
             "nose": "px=384+256X/.53, py=512+128(5.45-H)/.46 on all faces of HD_nose",
             "can_wrap": "px=768+512 theta/2pi, py=512(.54-z)/1.15 on the blue band z-.61..+.54 (theta=0 towards -D, seam at the back)",
             "can_top": "px=384+128x/.245, py=384+128d/.245 on the recessed cap (x,d relative to the can axis)"}, "palette_check": PAL_CHECK, "uv_face_counts_by_map": UV_STATS}
for i, (n_, h_) in enumerate(PAL):
    u_, v_ = tile_uv(i)
    uvmap["tiles"].append({"index": i, "name": n_, "hex": h_, "col": i % COLS, "row": i // COLS, "uv_centre": [u_, v_]})
json.dump(uvmap, open(os.path.join(OUT, "data", "palette_uv_map.json"), "w"), indent=1)

CENTRES = {}
BBOXES = {}
for n in BODY_NAMES + PROPS:
    lo, hi = bbox(ALLV[n])
    CENTRES[n] = r3((lo + hi) / 2.0, 6)
    BBOXES[n] = {"min": r3(lo, 5), "max": r3(hi, 5), "size": r3(hi - lo, 5), "centre": CENTRES[n]}
RESULT = {"bounds_all": {"min": r3(all_lo), "max": r3(all_hi), "height": round(all_hi.z - all_lo.z, 4)}, "bounds_body": {"min": r3(body_lo), "max": r3(body_hi), "height": round(body_hi.z - body_lo.z, 4)},
          "feet_min_h": round(feet_lo.z, 5), "tris_body": body_tris, "tris_props": prop_tris, "tris_total": body_tris + prop_tris, "audit": AUDIT, "checks": CHECKS, "pose_bones_identity": POSE_IDENTITY,
          "part_bboxes_logical": BBOXES}
json.dump(RESULT, open(os.path.join(OUT, "data", "_build_result.json"), "w"), indent=1)
SPEC = {"asset": "GamerDad_Sweatshirt_Review", "character": "Gamer Dad (05, Rare) - sweatshirt version", "units": "studs", "plan_height": 6.40, "built_height": RESULT["bounds_all"]["height"],
        "joints": {k: list(v) for k, v in JOINTS.items()}, "arm_lengths": {"upper": UP_LEN, "lower": LO_LEN},
        "joint_length_errors": {s + "_" + k: abs((JV[s + a] - JV[s + b]).length - L) for s in ("Right", "Left") for k, a, b, L in (("upper", "Shoulder", "Elbow", UP_LEN), ("lower", "Elbow", "Wrist", LO_LEN))},
        "hand_centres": SPEC_IN["hand_centers"], "can": SPEC_IN["can"], "palette": [{"index": i, "name": n_, "hex": h_} for i, (n_, h_) in enumerate(PAL)],
        "elbow": ELBOW_LOG, "counts": {"body_tris": body_tris, "prop_tris": prop_tris, "parts": len(PARTS), "components_registered": len(COMP_LOG)},
        "deviations_from_prompt": DEVIATIONS, "measured": {k: v for k, v in RESULT.items() if k != "part_bboxes_logical"}}
json.dump(SPEC, open(os.path.join(OUT, "data", "construction_spec.json"), "w"), indent=1, default=str)
json.dump({"asset": "GamerDad_Sweatshirt_Review", "components": COMP_LOG, "faces_by_component": COMP_FACES,
           "part_totals": {k: {"components": len(v.comps), "tris": AUDIT[k]["tris"], "verts": AUDIT[k]["verts"]} for k, v in PARTS.items()},
           "mesh_names": {k: v.geo for k, v in PARTS.items()}}, open(os.path.join(OUT, "data", "component_registry.json"), "w"), indent=1, default=str)
RIG = {"asset": "GamerDad_Sweatshirt_Review", "frame": {"logical": "(X,D,H) forward=-D, anatomical RIGHT=-X", "roblox_position": "(-X, H, D)"},
       "bones": [{"name": n, "parent": p, "head_logical": r3(h, 6), "tail_logical": r3(t, 6), "head_roblox": roblox_pos(h)} for n, p, h, t in BONES],
       "part_origin_logical": {k: r3(v.joint, 6) for k, v in PARTS.items()}, "part_bbox_centres_logical": CENTRES,
       "weights": "100% own bone (rigid); Headset -> Head, EnergyCan -> RightHand (props are exported as separate meshes without armature)", "pose": "HoldCan == rest pose (built directly, pose bones identity)"}
json.dump(RIG, open(os.path.join(OUT, "data", "rig_manifest.json"), "w"), indent=1)
print("RESULT", json.dumps({k: RESULT[k] for k in ("bounds_all", "tris_body", "tris_props", "pose_bones_identity")}))


# ----------------------------------------------------------------------------------------------
# cameras / light / renders (real Blender renders; the cameras are stored in data/cameras.json)
# ----------------------------------------------------------------------------------------------
if NORENDER:
    sys.exit(0)
world = bpy.data.worlds.new("GD_World")
SCENE.world = world
world.use_nodes = True
_wn = world.node_tree.nodes
_wl = world.node_tree.links
_bg_a = _wn["Background"]
_bg_a.inputs[0].default_value = (0.90, 0.88, 0.84, 1.0)
_bg_a.inputs[1].default_value = 0.66
_bg_b = _wn.new("ShaderNodeBackground")
_bg_b.inputs[0].default_value = (0.93, 0.91, 0.88, 1.0)
_bg_b.inputs[1].default_value = 1.0
_lp = _wn.new("ShaderNodeLightPath")
_mix = _wn.new("ShaderNodeMixShader")
_wl.new(_lp.outputs["Is Camera Ray"], _mix.inputs[0])
_wl.new(_bg_a.outputs[0], _mix.inputs[1])
_wl.new(_bg_b.outputs[0], _mix.inputs[2])
_wl.new(_mix.outputs[0], _wn["World Output"].inputs["Surface"])
sun_d = bpy.data.lights.new("GD_Key", 'SUN')
sun_d.energy = 1.8
sun = bpy.data.objects.new("GD_Key", sun_d)
SCENE.collection.objects.link(sun)
sun.rotation_euler = (math.radians(52), math.radians(8), math.radians(-38))
fill_d = bpy.data.lights.new("GD_Fill", 'SUN')
fill_d.energy = 0.55
fill_d.use_shadow = False
fill = bpy.data.objects.new("GD_Fill", fill_d)
SCENE.collection.objects.link(fill)
fill.rotation_euler = (math.radians(60), 0, math.radians(140))
cam_d = bpy.data.cameras.new("GD_Cam")
CAM = bpy.data.objects.new("GD_Cam", cam_d)
SCENE.collection.objects.link(CAM)
SCENE.camera = CAM
SCENE.render.engine = 'BLENDER_EEVEE'
SCENE.eevee.taa_render_samples = 8 if QUICK else 48
SCENE.render.image_settings.file_format = 'PNG'
SCENE.view_settings.view_transform = 'Standard'
SCENE.render.film_transparent = False
CAMS = []
RENDERED = []


def cam_look(loc, target, lens=70.0, ortho=None):
    CAM.location = V(loc)
    CAM.rotation_euler = (V(target) - V(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.sensor_width = 36.0
    cam_d.sensor_fit = 'AUTO'
    if ortho:
        cam_d.type, cam_d.ortho_scale = 'ORTHO', ortho
    else:
        cam_d.type, cam_d.lens = 'PERSP', lens


def orbit(target, dist, az_deg, el_deg):
    az, el = math.radians(az_deg), math.radians(el_deg)
    t = V(target)
    return t + V((dist * math.sin(az) * math.cos(el), -dist * math.cos(az) * math.cos(el), dist * math.sin(el)))


def shot(name, loc, target, res=(1000, 1000), lens=70.0, ortho=None, show_only=None, hide=None):
    for pm in PARTS.values():
        hid = (show_only is not None and pm.runtime not in show_only) or (hide is not None and pm.runtime in hide)
        pm.obj.hide_render = hid
    SCENE.render.resolution_x, SCENE.render.resolution_y = res
    cam_look(loc, target, lens, ortho)
    SCENE.render.filepath = os.path.join(OUT, "renders", name)
    bpy.ops.render.render(write_still=True)
    RENDERED.append(name)
    CAMS.append({"name": name, "location": [round(c, 4) for c in CAM.location], "target": [round(c, 4) for c in target], "type": "ORTHO" if ortho else "PERSP", "ortho_scale": ortho, "lens_mm": None if ortho else lens, "resolution": list(res)})
    print("RENDERED", name)


FULL = V((0.0, -0.10, 3.20))
FS = 7.15
if QUICK:
    SZ = (800, 800)
else:
    SZ = (1600, 1600)
shot("01_matching_front.png", orbit(FULL, 30, 0, 7), FULL, res=SZ, ortho=FS)
shot("02_front.png", orbit(FULL, 30, 0, 4), FULL, res=SZ, ortho=FS)
shot("03_back.png", orbit(FULL, 30, 180, 4), FULL, res=SZ, ortho=FS)
shot("04_profile_right.png", orbit(FULL, 30, -90, 4), FULL, res=SZ, ortho=FS)
shot("05_profile_left.png", orbit(FULL, 30, 90, 4), FULL, res=SZ, ortho=FS)
shot("06_front_q34.png", orbit(FULL, 30, -35, 9), FULL, res=SZ, ortho=FS)
shot("07_rear_q34.png", orbit(FULL, 30, 145, 9), FULL, res=SZ, ortho=FS)
DS = (1200, 1200) if not QUICK else (600, 600)
HT = V((0, -0.3, 5.25))
shot("08_face_front.png", orbit(HT, 14, 0, 2), HT, res=DS, ortho=3.2)
shot("09_face_profile_right.png", orbit(HT, 14, -90, 2), HT, res=DS, ortho=3.2)
shot("09b_face_q34.png", orbit(HT, 14, -32, 8), HT, res=DS, ortho=3.2)
shot("08c_head_top.png", orbit(HT, 14, -20, 70), HT, res=DS, ortho=3.2)
shot("08d_head_back.png", orbit(HT, 14, 180, 10), HT, res=DS, ortho=3.2)
BT = V((0, -0.55, 4.75))
shot("10_beard_below.png", orbit(BT, 14, -15, -42), BT, res=DS, ortho=3.0)
shot("10b_beard_side.png", orbit(BT, 14, -90, 3), BT, res=DS, ortho=3.0)
for sd, sx in (("R", -1), ("L", 1)):
    ST = JV[("Right" if sx < 0 else "Left") + "Shoulder"]
    ET = JV[("Right" if sx < 0 else "Left") + "Elbow"]
    shot("11_shoulder_%s.png" % sd, orbit(ST, 14, sx * 40, 12), ST, res=DS, ortho=2.8)
    shot("12_elbow_%s_outer.png" % sd, orbit(ET, 14, sx * 90, 6), ET, res=DS, ortho=2.8)
    shot("12_elbow_%s_front.png" % sd, orbit(ET, 14, 0, 8), ET, res=DS, ortho=2.8)
    shot("12_elbow_%s_back.png" % sd, orbit(ET, 14, 180, 8), ET, res=DS, ortho=2.8)
    shot("12_elbow_%s_top.png" % sd, orbit(ET, 14, sx * 30, 72), ET, res=DS, ortho=2.8)
    shot("12_elbow_%s_bottom.png" % sd, orbit(ET, 14, sx * 30, -60), ET, res=DS, ortho=2.8)
GT = V((-2.05, -1.1, 3.75))
shot("13_grip_front.png", orbit(GT, 10, 0, 6), GT, res=DS, ortho=2.8)
shot("13b_grip_side_inner.png", orbit(GT, 10, 90, 6), GT, res=DS, ortho=2.8)
shot("13c_grip_back.png", orbit(GT, 10, 180, 6), GT, res=DS, ortho=2.8)
shot("13d_grip_top.png", orbit(GT, 10, 0, 80), GT, res=DS, ortho=2.8)
LT = V((1.95, -0.1, 2.4))
shot("14_left_hand.png", orbit(LT, 10, 30, 8), LT, res=DS, ortho=2.8)
SH = V((0, -0.2, 0.7))
shot("15_shoes.png", orbit(SH, 10, 25, 14), SH, res=DS, ortho=4.2)
shot("15b_pelvis_front.png", orbit(V((0, -0.1, 2.0)), 14, 0, 4), V((0, -0.1, 2.0)), res=DS, ortho=4.2)
shot("15c_pelvis_back.png", orbit(V((0, -0.1, 2.0)), 14, 180, 4), V((0, -0.1, 2.0)), res=DS, ortho=4.2)
CT = V((CAN_C.x, CAN_C.y, 3.86))
shot("16_can_front.png", orbit(CT, 10, 0, 4), CT, res=DS, ortho=2.0, show_only=("EnergyCan",))
shot("16b_can_back.png", orbit(CT, 10, 180, 4), CT, res=DS, ortho=2.0, show_only=("EnergyCan",))
shot("16c_can_top.png", orbit(CT, 10, 0, 80), CT, res=DS, ortho=1.2, show_only=("EnergyCan",))
shot("16d_can_bottom.png", orbit(CT, 10, 0, -70), CT, res=DS, ortho=1.2, show_only=("EnergyCan",))
for pm in PARTS.values():
    pm.obj.hide_render = False
json.dump(CAMS, open(os.path.join(OUT, "data", "cameras.json"), "w"), indent=1)
print("ALL_RENDERS_DONE", len(RENDERED))
