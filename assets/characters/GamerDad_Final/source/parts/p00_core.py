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
