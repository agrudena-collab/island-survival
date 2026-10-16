"""Procedural Blender build for the Regular Dad redesign ("Steal a Dad!").

Source of truth: RegularDad_Illustrated_MasterPrompt.pdf (owner's master prompt).
Primary reference: reference/RegularDad_Reference_Crop.png (384x395, unchanged).

Frames / units
--------------
1 Blender unit = 1 Roblox stud (scene scale_length 0.01, like the houses).
Logical (X, D, H): X<0 = anatomical RIGHT (mug side), D<0 = front, H up, sole at H=0.
Blender (x, y, z) = (X, D, H).  FBX export axis_forward='Z', axis_up='Y' (the project's
proven mapping): Roblox position of logical (X,D,H) = (-X, H, D); the character faces -Z.

Run headless:
    blender -b --factory-startup --python build_regular_dad_redesign.py -- <output_dir> [--quick]
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
SLIM_FOREARM = "--no-slim-forearm" not in sys.argv   # final model: right forearm slimmer, tapered towards the wrist (default ON)
os.makedirs(os.path.join(OUT, "previews"), exist_ok=True)

# ----------------------------------------------------------------------------------------------
# scene
# ----------------------------------------------------------------------------------------------
for _ob in list(bpy.data.objects):
    bpy.data.objects.remove(_ob, do_unlink=True)
for _blk in (bpy.data.meshes, bpy.data.materials, bpy.data.collections, bpy.data.cameras, bpy.data.lights, bpy.data.images):
    for _it in list(_blk):
        _blk.remove(_it)
SCENE = bpy.context.scene
SCENE.unit_settings.system = 'METRIC'
SCENE.unit_settings.scale_length = 0.01

# ----------------------------------------------------------------------------------------------
# palette (section 4) + derived shades required by the prompt text
# ----------------------------------------------------------------------------------------------
PAL = [
    ("SKIN", "#EEA16D", "Main face, hands, exposed arms"),
    ("SKIN_LIGHT", "#FFC18A", "Upward and broad lit skin facets"),
    ("SKIN_DARK", "#CD7D4C", "Under nose, inner ears, broad creases"),
    ("TEAL", "#187B84", "Main polo"),
    ("TEAL_LIGHT", "#258E96", "Shoulder/top-facing polo facets"),
    ("TEAL_DARK", "#12616B", "Sleeve cuffs, underarm and hem shade"),
    ("JEANS", "#28558F", "Main denim"),
    ("JEANS_LIGHT", "#366AA8", "Broad front denim planes, cuffs"),
    ("JEANS_DARK", "#1D3D68", "Inner legs, seams and pocket shadow"),
    ("HAIR", "#52301D", "Side hair and eyebrows"),
    ("HAIR_DARK", "#3A2317", "Mustache lower facets and hair recesses"),
    ("HAIR_LIGHT", "#6C4227", "A few broad hair top planes"),
    ("BELT", "#432B1D", "Belt leather"),
    ("GOLD", "#D7A53D", "Buckle, polo button"),
    ("SHOE", "#6C462D", "Shoe uppers"),
    ("SHOE_LIGHT", "#855B3C", "Broad toe/vamp top planes"),
    ("SOLE", "#3B291D", "Sole and heel"),
    ("EYE_WHITE", "#F7F1E5", "Fitted eye whites"),
    ("EYE_BLACK", "#171715", "Pupils and thin eyelid edge"),
    ("MUG", "#EDE5D3", "Ivory ceramic"),
    ("MUG_INNER", "#CEC3AE", "Inner walls and underside shade"),
    ("COFFEE", "#4D2B18", "Plain dark coffee surface"),
    ("MOUTH", "#9A5434", "Closed smirk and lower-lip crease"),
    ("SHADOW", "#6A4734", "Restrained seams only"),
]


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def hex_shift(h, f):
    """f<1 darkens (multiply), f>1 lightens towards white by (f-1)."""
    r, g, b = hex_rgb(h)
    if f <= 1.0:
        r, g, b = (int(round(c * f)) for c in (r, g, b))
    else:
        t = f - 1.0
        r, g, b = (int(round(c + (255 - c) * t)) for c in (r, g, b))
    return "#%02X%02X%02X" % (min(r, 255), min(g, 255), min(b, 255))


_H = {n: h for n, h, _ in PAL}
PAL += [
    ("BELT_LIGHT", hex_shift(_H["BELT"], 1.14), "DERIVED: BELT lightened 14% (broad top edge)"),
    ("MOUTH_LIGHT", hex_shift(_H["MOUTH"], 1.20), "DERIVED: MOUTH lightened 20% (under-lip crease)"),
    ("COFFEE_DARK", hex_shift(_H["COFFEE"], 0.92), "DERIVED: COFFEE darkened 8% (meniscus)"),
    ("TEAL_HEM", hex_shift(_H["TEAL_DARK"], 0.95), "DERIVED: TEAL_DARK -5% (hem)"),
]
TILE = {n: i for i, (n, _, _) in enumerate(PAL)}
HEXOF = {n: h for n, h, _ in PAL}
ATLAS_W, ATLAS_H, TILE_PX, COLS = 256, 128, 32, 8
INSET = 6


def tile_uv_patch(idx):
    col, row = idx % COLS, idx // COLS
    u0 = (col * TILE_PX + INSET) / ATLAS_W
    u1 = (col * TILE_PX + TILE_PX - INSET) / ATLAS_W
    # image row 0 is the TOP row of the PNG; Blender UV v=0 is the bottom edge
    v1 = 1.0 - (row * TILE_PX + INSET) / ATLAS_H
    v0 = 1.0 - (row * TILE_PX + TILE_PX - INSET) / ATLAS_H
    return u0, v0, u1, v1


def srgb_to_lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


# ----------------------------------------------------------------------------------------------
# geometry containers
# ----------------------------------------------------------------------------------------------
PARTS = {}
COMP_LOG = []
SRC_COLL = bpy.data.collections.new("SOURCE_Components")
SCENE.collection.children.link(SRC_COLL)
EXP_COLL = bpy.data.collections.new("EXPORT_RegularDad")
SCENE.collection.children.link(EXP_COLL)


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


class PM:
    """One runtime body part (or the mug): a bmesh with a per-face palette tile."""

    def __init__(self, runtime, joint, xf=None, geo=None):
        self.runtime = runtime
        self.geo = geo or (runtime + "_Geo")
        self.joint = V(joint)
        self.bm = bmesh.new()
        self.tl = self.bm.faces.layers.int.new("tile")
        self.xf = xf
        self.comps = []
        PARTS[runtime] = self

    def _tx(self, p):
        p = V(p)
        return self.xf(p) if self.xf else p

    def append_bm(self, cid, bm, tilefn, meta):
        """Copy a finished component bmesh into this part (tile chosen per face)."""
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
            tiles.add(PAL[t][0])
            n_faces += 1
        self.bm.verts.ensure_lookup_table()
        rec = {"id": cid, "owner": self.runtime, "tiles": sorted(tiles),
               "faces": n_faces, "tris": sum(len(f.verts) - 2 for f in bm.faces)}
        rec.update(meta)
        self.comps.append(rec)
        COMP_LOG.append(rec)

    def solid(self, cid, P, faces, tilefn, meta=None, closed=True):
        bm = make_bm_solid(P, faces, closed)
        self.append_bm(cid, bm, tilefn, meta)
        bm.free()


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


def loft(pm, cid, rings, tilefn, caps=(True, True), band_tiles=None, meta=None):
    """Closed loft through equal-length rings. band_tiles={band_index: tile name}."""
    n = len(rings[0])
    P = [p for r in rings for p in r]
    faces = loft_faces(len(rings), n, caps)
    if band_tiles:
        fn0 = tilefn
        # build a per-face override by tagging faces through a lookup of (ring band)
        bm = make_bm_solid(P, faces)
        # find band for each face by the mean of its vertices' ring index
        ring_of = {}
        for i, r in enumerate(rings):
            for k in range(n):
                ring_of[(round(P[i * n + k].x, 6), round(P[i * n + k].y, 6), round(P[i * n + k].z, 6))] = i

        def pick(nf_n, nf_c, _fn=fn0):
            return _fn(nf_n, nf_c)
        # append face by face with override
        vmap = {}
        tiles = set()
        nfaces = 0
        for f in bm.faces:
            ids = []
            for v in f.verts:
                key = (round(v.co.x, 6), round(v.co.y, 6), round(v.co.z, 6))
                ids.append(ring_of.get(key, -1))
            tile_name = None
            if len(set(ids)) == 2 and -1 not in ids:
                lo = min(ids)
                if abs(max(ids) - lo) == 1 and lo in band_tiles:
                    tile_name = band_tiles[lo]
            vv = []
            for v in f.verts:
                if v.index not in vmap:
                    vmap[v.index] = pm.bm.verts.new(pm._tx(v.co))
                vv.append(vmap[v.index])
            try:
                nf = pm.bm.faces.new(vv)
            except ValueError:
                continue
            nf.normal_update()
            if nf.calc_area() < 1e-10:
                pm.bm.faces.remove(nf)
                continue
            if tile_name is None:
                tile_name = tilefn(nf.normal.copy(), nf.calc_center_median()) if callable(tilefn) else tilefn
            nf[pm.tl] = TILE[tile_name]
            tiles.add(tile_name)
            nfaces += 1
        pm.bm.verts.ensure_lookup_table()
        rec = {"id": cid, "owner": pm.runtime, "tiles": sorted(tiles), "faces": nfaces,
               "tris": sum(len(f.verts) - 2 for f in bm.faces)}
        rec.update(meta or {})
        pm.comps.append(rec)
        COMP_LOG.append(rec)
        bm.free()
        return
    pm.solid(cid, P, faces, tilefn, meta)


def ring8(a, f, b, c, cx=0.0, cd=0.0, h=0.0):
    pts = [(-a + c, f), (a - c, f), (a, f + c), (a, b - c), (a - c, b), (-a + c, b), (-a, b - c), (-a, f + c)]
    return [V((cx + x, cd + y, h)) for x, y in pts]


def row_ring(row, cx=0.0, cd=0.0):
    h, w, f, b, c = row
    return ring8(w / 2.0, f, b, c, cx, cd, h)


def interp_row(rows, h):
    if h <= rows[0][0]:
        return rows[0][1:]
    if h >= rows[-1][0]:
        return rows[-1][1:]
    for a, b in zip(rows, rows[1:]):
        if a[0] <= h <= b[0]:
            t = (h - a[0]) / (b[0] - a[0])
            return tuple(a[i] + (b[i] - a[i]) * t for i in range(1, 5))


def front_at(rows, h, x=0.0, cx=0.0):
    w, f, b, c = interp_row(rows, h)
    a = w / 2.0
    ax = abs(x - cx)
    if ax <= a - c:
        return f
    return f + min(ax - (a - c), c)


def back_at(rows, h, x=0.0, cx=0.0):
    w, f, b, c = interp_row(rows, h)
    a = w / 2.0
    ax = abs(x - cx)
    if ax <= a - c:
        return b
    return b - min(ax - (a - c), c)


class Axis:
    """Limb frame: proximal P0 -> distal P1. U = F x A (width), Q = backwards (+D)."""

    def __init__(self, P0, P1):
        self.P0, self.P1 = V(P0), V(P1)
        d = self.P1 - self.P0
        self.L = d.length
        self.A = d / self.L
        self.U = V((0, -1, 0)).cross(self.A).normalized()
        self.Q = -(self.A.cross(self.U).normalized())

    def at(self, t):
        return self.P0 + self.A * (self.L * t)

    def ring(self, t, w, d, c, grow=0.0):
        P = self.at(t)
        a, h = w / 2.0 + grow, d / 2.0 + grow
        c = c + grow * 0.0
        pts = [(-a + c, -h), (a - c, -h), (a, -h + c), (a, h - c), (a - c, h), (-a + c, h), (-a, h - c), (-a, -h + c)]
        return [P + self.U * x + self.Q * y for x, y in pts]

    def surf_back(self, t, d):
        return self.at(t) + self.Q * (d / 2.0)


def sec_at(secs, t):
    if t <= secs[0][0]:
        return secs[0][1:]
    if t >= secs[-1][0]:
        return secs[-1][1:]
    for a, b in zip(secs, secs[1:]):
        if a[0] <= t <= b[0]:
            u = (t - a[0]) / (b[0] - a[0])
            return tuple(a[i] + (b[i] - a[i]) * u for i in range(1, len(a)))


def cbox(c, size, ch, xf=None, order="xyz"):
    """Chamfered box: rings in H at z0 (shrunk), z0+ch, z1-ch, z1 (shrunk). size=(sx,sd,sh)."""
    sx, sd, sh = size
    ch = min(ch, sx / 2 - 1e-4, sd / 2 - 1e-4, sh / 2 - 1e-4)
    rings = []
    for dz, sh_in in ((-sh / 2, ch), (-sh / 2 + ch, 0), (sh / 2 - ch, 0), (sh / 2, ch)):
        a, b = sx / 2 - sh_in, sd / 2 - sh_in
        cc = min(ch, a - 1e-4, b - 1e-4)
        rings.append(ring8(a, -b, b, cc, 0.0, 0.0, dz))
    out = []
    for r in rings:
        out.append([(xf(p) if xf else p) + V(c) for p in r])
    return out


def box_rings(x0, x1, d0, d1, h0, h1):
    a = [V((x0, d0, h0)), V((x1, d0, h0)), V((x1, d1, h0)), V((x0, d1, h0))]
    b = [V((x0, d0, h1)), V((x1, d0, h1)), V((x1, d1, h1)), V((x0, d1, h1))]
    return [a, b]


def solid_box(pm, cid, x0, x1, d0, d1, h0, h1, tilefn, meta=None):
    loft(pm, cid, box_rings(x0, x1, d0, d1, h0, h1), tilefn, meta=meta)


def prism_poly(pm, cid, poly, vec, tilefn, meta=None):
    """Closed prism: planar polygon (list of 3D points) swept by vec."""
    n = len(poly)
    P = list(poly) + [p + V(vec) for p in poly]
    faces = []
    for k in range(n):
        faces.append([k, (k + 1) % n, n + (k + 1) % n, n + k])
    faces += cap_tris(P, list(range(n)))
    faces += cap_tris(P, list(range(n, 2 * n)))
    pm.solid(cid, P, faces, tilefn, meta)


def layered_plate(pm, cid, outline, fit, layers, tilefn, meta=None):
    """Closed plate over a surface. outline: [(X,H)], fit(X,H)->D of the surface,
    layers: [(dD, sx, sh)] first layer is the back (embedded), last the front."""
    cx = sum(p[0] for p in outline) / len(outline)
    ch = sum(p[1] for p in outline) / len(outline)
    n = len(outline)
    P = []
    for dD, sx, sh in layers:
        for x, h in outline:
            xx = cx + (x - cx) * sx
            hh = ch + (h - ch) * sh
            P.append(V((xx, fit(xx, hh) + dD, hh)))
    faces = []
    for i in range(len(layers) - 1):
        for k in range(n):
            faces.append([i * n + k, i * n + (k + 1) % n, (i + 1) * n + (k + 1) % n, (i + 1) * n + k])
    faces += cap_tris(P, list(range(n)))
    faces += cap_tris(P, list(range((len(layers) - 1) * n, len(layers) * n)))
    pm.solid(cid, P, faces, tilefn, meta)


def rot_about(p, pivot, axis, deg):
    m = Matrix.Rotation(math.radians(deg), 3, axis)
    return pivot + m @ (p - pivot)


# ----------------------------------------------------------------------------------------------
# shading rules (normal-dependent palette variants)
# ----------------------------------------------------------------------------------------------
def sh_skin(n, c):
    if n.z > 0.55:
        return "SKIN_LIGHT"
    if n.z < -0.55:
        return "SKIN_DARK"
    return "SKIN"


def sh_skin_arm(n, c):
    if n.z > 0.55:
        return "SKIN_LIGHT"
    if n.z < -0.55 or n.y > 0.80:
        return "SKIN_DARK" if n.z < -0.55 else "SKIN"
    if n.y < -0.62:
        return "SKIN_LIGHT"
    return "SKIN"


def sh_teal(n, c):
    if n.z > 0.30:
        return "TEAL_LIGHT"
    if n.z < -0.30:
        return "TEAL_DARK"
    return "TEAL"


def sh_teal_fold(n, c):
    if n.y < -0.5:
        return "TEAL_LIGHT"
    if n.y > 0.5:
        return "TEAL_DARK"
    return "TEAL"


def sh_jeans(side=0):
    def f(n, c):
        if n.z < -0.6:
            return "JEANS_DARK"
        if n.y < -0.62:
            return "JEANS_LIGHT"
        if n.y > 0.62:
            return "JEANS_DARK"
        if side and n.x * side < -0.6:
            return "JEANS_DARK"
        return "JEANS"
    return f


def sh_const(name):
    return lambda n, c: name


def sh_hair(n, c):
    if n.z < -0.30:
        return "HAIR_DARK"
    if n.z > 0.62:
        return "HAIR_LIGHT"
    return "HAIR"


def sh_shoe(n, c):
    if n.z < -0.5:
        return "SOLE"
    if n.z > 0.55:
        return "SHOE_LIGHT"
    return "SHOE"


def sh_belt(n, c):
    return "BELT_LIGHT" if n.z > 0.6 else "BELT"


def sh_nose(n, c):
    if n.z < -0.55:
        return "SKIN_DARK"
    if n.z > 0.45:
        return "SKIN_LIGHT"
    return "SKIN"


# ----------------------------------------------------------------------------------------------
# prescribed numeric tables (master prompt sections 6, 7, 15, 16, 18)
# ----------------------------------------------------------------------------------------------
UT_ROWS = [(2.58, 2.60, -1.00, .54, .16), (2.90, 2.90, -1.08, .61, .18), (3.35, 3.00, -1.05, .66, .20),
           (3.95, 2.90, -.88, .68, .16), (4.35, 3.05, -.72, .61, .14), (4.60, 2.96, -.60, .60, .14)]
LT_ROWS = [(1.97, 2.10, -.49, .43, .14), (2.15, 2.45, -.64, .49, .16), (2.40, 2.72, -.91, .54, .16),
           (2.62, 2.60, -.98, .54, .16)]
HEAD_ROWS = [(4.82, 1.05, -.58, .40, .12), (4.93, 1.40, -.72, .52, .14), (5.18, 1.72, -.76, .60, .17),
             (5.60, 1.64, -.70, .63, .14), (6.20, 1.60, -.61, .62, .12), (6.40, 1.38, -.50, .50, .12)]
SHOE_ROWS = [(.13, 1.18, -1.00, .48, .13), (.28, 1.16, -.98, .47, .13), (.43, 1.02, -.90, .43, .14),
             (.52, .76, -.56, .33, .11)]
NOSE_ROWS = [(5.40, .30, -1.00, -.75, .045), (5.48, .50, -1.13, -.70, .045), (5.65, .42, -1.10, -.68, .045),
             (5.77, .18, -.88, -.69, .045)]
MUG_OUT = [(0.0, .72, .58, .070), (.04, .74, .60, .075), (.96, .82, .68, .080), (1.10, .82, .68, .080)]
MUG_IN = [(1.10, .70, .56, .060), (.96, .70, .56, .060), (.14, .60, .46, .055)]
HANDLE_PTS = [(-.42, 0, .87), (-.58, 0, .93), (-.78, 0, .84), (-.87, 0, .66), (-.87, 0, .43), (-.78, 0, .27),
              (-.58, 0, .21), (-.39, 0, .28)]

JOINTS = {  # logical (X,D,H) neutral joint pivots (section 18)
    "Root": (0, 0, 2.28), "Waist": (0, 0, 2.62), "Neck": (0, 0, 4.78),
    "RightShoulder": (-1.65, 0, 4.35), "RightElbow": (-1.90, 0, 3.28), "RightWrist": (-2.02, 0, 2.30),
    "LeftShoulder": (1.65, 0, 4.35), "LeftElbow": (1.90, 0, 3.28), "LeftWrist": (2.02, 0, 2.30),
    "RightHip": (-.64, 0, 2.05), "RightKnee": (-.64, .03, 1.14), "RightAnkle": (-.64, 0, .44),
    "LeftHip": (.64, 0, 2.05), "LeftKnee": (.64, .03, 1.14), "LeftAnkle": (.64, 0, .44),
}
JV = {k: V(v) for k, v in JOINTS.items()}
GRIP_LOCAL = V((-.12, -.13, -.36))
GRIP_TARGET = V((-2.57, -1.55, 3.45))
MUG_FROM_GRIP = V((.87, 0, -.55))
MUG_ORIGIN_REF = GRIP_TARGET + MUG_FROM_GRIP
WRIST_TARGET = GRIP_TARGET - GRIP_LOCAL
POLE = V((-3.40, .25, 3.20))
TOE_OUT = {-1: -6.0, 1: 6.0}


def solve_two_bone(S, W, P, L1, L2):
    d = (W - S).length
    e = (W - S) / d
    a = (L1 * L1 - L2 * L2 + d * d) / (2 * d)
    h = math.sqrt(max(L1 * L1 - a * a, 0.0))
    pe = (P - S) - e * (P - S).dot(e)
    q = pe.normalized()
    return S + e * a + q * h


# ----------------------------------------------------------------------------------------------
# build: UpperTorso
# ----------------------------------------------------------------------------------------------
ut = PM("UpperTorso", JV["Waist"])
ut_rows = [UT_ROWS[0]]
hem_h = 2.67
hw = interp_row(UT_ROWS, hem_h)
ut_rows.append((hem_h,) + tuple(hw))
ut_rows += UT_ROWS[1:]
loft(ut, "UT_polo_body", [row_ring(r) for r in ut_rows], sh_teal, band_tiles={0: "TEAL_HEM"},
     meta={"recipe": "8-point chamfered-rectangle loft, rows of master prompt section 6 (+ interpolated hem ring H2.67)",
           "dims": {"rows": UT_ROWS}, "class": "observed+prescribed"})
loft(ut, "UT_neck", [ring8(.29, -.26, .26, .09, 0, 0, 4.55), ring8(.29, -.26, .26, .09, 0, 0, 4.94)], sh_skin,
     meta={"recipe": "8-sided rounded cuboid .58 x .52, H4.55..4.94", "class": "prescribed"})
loft(ut, "UT_collar_band", [ring8(.365, -.335, .335, .10, 0, 0, 4.58), ring8(.365, -.335, .335, .10, 0, 0, 4.74)], sh_teal,
     meta={"recipe": "rear/neck collar band .075 thick, H4.58..4.74 (closed ring around the neck)", "class": "prescribed"})


def ut_front(x, h):
    return front_at(UT_ROWS, min(max(h, 2.58), 4.60), x)


for s in (-1, 1):
    corners = [(-.62, 4.62, .02), (-.12, 4.61, .04), (-.40, 4.23, .16), (-.78, 4.56, .03)]
    poly = []
    for x, h, off in corners:
        X = s * -x if False else (x if s < 0 else -x)
        poly.append(V((X, ut_front(X, h) - off, h)))
    prism_poly(ut, "UT_collar_lobe_" + ("R" if s < 0 else "L"), poly, (0, .035, 0), sh_teal_fold,
               meta={"recipe": "collar fold: 4 corners (X,H,offset) from section 11, .035 thick", "class": "observed+prescribed",
                     "note": "bevel .015 not applied (flat folded plate)"})

# placket (X -.14..+.14, H4.02..4.61), follows the piecewise-linear front
ph = [4.02, 4.35, 4.60, 4.61]


def front_strip(pm, cid, x0, x1, hs, out, embed, tile, ffn=None, rear=False, meta=None):
    """Strip hugging a surface: hs = [h] or [(h, out)]; ffn(x,h)->surface D; rear=True offsets towards +D."""
    ffn = ffn or ut_front
    sgn = 1.0 if rear else -1.0
    P = []
    for hh in hs:
        h, o_ = (hh if isinstance(hh, tuple) else (hh, out))
        for x in (x0, x1):
            f = ffn(x, h)
            P.append(V((x, f + sgn * o_, h)))
            P.append(V((x, f - sgn * embed, h)))
    faces = []
    nh = len(hs)
    # P layout per h: [x0 out, x0 emb, x1 out, x1 emb]
    for i in range(nh - 1):
        b0, b1 = i * 4, (i + 1) * 4
        faces.append([b0 + 0, b0 + 2, b1 + 2, b1 + 0])   # front
        faces.append([b0 + 1, b1 + 1, b1 + 3, b0 + 3])   # back
        faces.append([b0 + 0, b1 + 0, b1 + 1, b0 + 1])   # side x0
        faces.append([b0 + 2, b0 + 3, b1 + 3, b1 + 2])   # side x1
    faces.append([0, 1, 3, 2])
    e = (nh - 1) * 4
    faces.append([e + 0, e + 2, e + 3, e + 1])
    pm.solid(cid, P, faces, tile, meta or {"recipe": "strip following the surface", "class": "observed+prescribed"})


front_strip(ut, "UT_placket_L", .07, .14, ph, .018, .01, "TEAL_DARK")
front_strip(ut, "UT_placket_R", -.14, -.07, ph, .018, .01, "TEAL_DARK")
front_strip(ut, "UT_placket_C", -.07, .07, ph, .018, .01, "TEAL")
front_strip(ut, "UT_placket_seam", -.005, .005, ph, .022, .01, "TEAL_DARK")

# button: diameter .115, thickness .025 at (0, H4.10), normal fitted to the front slope
bh = 4.10
bf = ut_front(0, bh) - .018
slope = (ut_front(0, 4.35) - ut_front(0, 3.95)) / (4.35 - 3.95)       # dD/dH
nrm = V((0, -1.0, slope * -1.0 * -1.0)).normalized()
# front surface D(H) = f0 + slope*(H-h0): outward normal ~ (0,-1,slope)... n.D*dD + n.H*dH = 0 -> n = (0,-1, slope)
nrm = V((0, -1.0, slope)).normalized()
ux = V((1, 0, 0))
wy = nrm.cross(ux).normalized()
rings = []
for dz, r in ((0.0, .0575), (.012, .0575), (.025, .0455)):
    cen = V((0, bf, bh)) + nrm * dz
    rings.append([cen + ux * (r * math.cos(k * math.pi / 4 + math.pi / 8)) + wy * (r * math.sin(k * math.pi / 4 + math.pi / 8)) for k in range(8)])
loft(ut, "UT_button", rings, sh_const("GOLD"), meta={"recipe": "one gold button d.115 t.025, rim .012", "class": "observed+prescribed",
                                                        "note": "two .015 center holes omitted (below visible size)"})

# ----------------------------------------------------------------------------------------------
# LowerTorso: denim pelvis, belt, buckle, loops, fly, pocket edges
# ----------------------------------------------------------------------------------------------
lt = PM("LowerTorso", JV["Root"])
loft(lt, "LT_denim_pelvis", [row_ring(r) for r in LT_ROWS], sh_jeans(0),
     meta={"recipe": "8-point chamfered-rectangle loft, rows of section 6 (LowerTorso)", "dims": {"rows": LT_ROWS}, "class": "observed+prescribed"})


def lt_front(x, h):
    return front_at(LT_ROWS, h, x)


def lt_back(x, h):
    return back_at(LT_ROWS, h, x)


belt_h = [2.24, 2.40, 2.47]
brings = []
for h in belt_h:
    w, f, b, c = interp_row(LT_ROWS, h)
    brings.append(ring8(w / 2 + .055, f - .055, b + .055, c + .055, 0, 0, h))
loft(lt, "LT_belt", brings, sh_belt,
     meta={"recipe": "belt H2.24..2.47, .055 thick, follows the pelvis perimeter", "class": "observed+prescribed"})

# buckle: outer .46 x .30, thickness .06, opening .33 x .18, pin .028 x .31
bk_h = 2.355
bk_f = lt_front(0, bk_h) - .095
bx0, bx1 = -.23, .23
bz0, bz1 = bk_h - .15, bk_h + .15
ix0, ix1 = -.165, .165
iz0, iz1 = bk_h - .09, bk_h + .09
T = .06
for nm, (x0, x1, z0, z1) in {
    "top": (bx0, bx1, iz1, bz1), "bottom": (bx0, bx1, bz0, iz0),
    "left": (bx0, ix0, iz0, iz1), "right": (ix1, bx1, iz0, iz1),
}.items():
    solid_box(lt, "LT_buckle_" + nm, x0, x1, bk_f, bk_f + T, z0, z1, sh_const("GOLD"),
              {"recipe": "buckle frame bar (real opening .33 x .18)", "class": "observed+prescribed"})
solid_box(lt, "LT_buckle_pin", ix0, ix0 + .31, bk_f + .016, bk_f + .016 + .028, bk_h - .014, bk_h + .014, sh_const("GOLD"),
          {"recipe": "pin .028 high x .31 long, attached at the left inner side", "class": "prescribed"})

# belt loops (5): .12 w x .34 h x .035 thick; the strap rises over the belt (.055) and both ends touch the denim
LOOP_HS = [(2.185, .035), (2.235, .035), (2.245, .090), (2.465, .090), (2.475, .035), (2.525, .035)]
for lx, front in ((-1.10, True), (1.10, True), (-.70, False), (0.0, False), (.70, False)):
    cid = "LT_beltloop_%s%+.2f" % ("F" if front else "B", lx)
    front_strip(lt, cid, lx - .06, lx + .06, LOOP_HS, 0.0, .012, sh_const("JEANS"), ffn=(lt_front if front else lt_back),
                rear=(not front),
                meta={"recipe": "belt loop .12 x .34 x .035 over the belt, ends on the denim",
                      "class": "observed+prescribed" if front else "inferred"})

# fly seam X=.08, H1.99..2.24, .012 wide, projection .006 (follows the sloped front)
front_strip(lt, "LT_fly_seam", .074, .086, [1.99, 2.15, 2.24], .006, .01, sh_const("JEANS_DARK"), ffn=lt_front,
            meta={"recipe": "fly seam strip .012 wide", "class": "observed+prescribed"})
# pocket-edge curves (split at the hip boundary H2.05): LowerTorso owns H>=2.05
HIP_H = 2.05


def thin_polyline(pm, cid, pts, width, out, embed, tile, up=V((0, 0, 1)), frontfn=None, meta=None):
    """Thin ribbon along a polyline lying on a surface: width across the line, proud by `out`."""
    n = len(pts)
    P = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)])
        t.normalize()
        side = t.cross(V((0, -1, 0))).normalized() * (width / 2.0)
        if side.length < 1e-6:
            side = V((width / 2, 0, 0))
        P.append(p + side + V((0, -out, 0)))
        P.append(p - side + V((0, -out, 0)))
        P.append(p + side + V((0, embed, 0)))
        P.append(p - side + V((0, embed, 0)))
    faces = []
    for i in range(n - 1):
        a, b = i * 4, (i + 1) * 4
        faces += [[a, a + 1, b + 1, b], [a + 2, b + 2, b + 3, a + 3], [a, b, b + 2, a + 2], [a + 1, a + 3, b + 3, b + 1]]
    faces += [[0, 1, 3, 2]]
    e = (n - 1) * 4
    faces += [[e, e + 2, e + 3, e + 1]]
    pm.solid(cid, P, faces, tile, meta or {"recipe": "seam ribbon on surface", "class": "observed+prescribed"})


for s in (-1, 1):
    x_a, h_a = s * .62, 2.12
    x_b = s * (.62 + .50 * (2.12 - HIP_H) / .10)
    pts = [V((x_a, lt_front(x_a, h_a) - .0, h_a)), V((x_b, lt_front(x_b, HIP_H + .0), HIP_H))]
    thin_polyline(lt, "LT_pocket_edge_" + ("R" if s < 0 else "L"), pts, .012, .006, .01, sh_const("JEANS_DARK"),
                  meta={"recipe": "front pocket edge, upper segment (LowerTorso side of the hip boundary)", "class": "observed+prescribed"})

# ----------------------------------------------------------------------------------------------
# Head
# ----------------------------------------------------------------------------------------------
hd = PM("Head", JV["Neck"])
loft(hd, "HD_shell", [row_ring(r) for r in HEAD_ROWS], sh_skin,
     meta={"recipe": "closed chamfered loft, rows of section 7; flat bald crown H6.40", "dims": {"rows": HEAD_ROWS},
           "class": "observed+prescribed"})


def hf(h, x=0.0):
    return front_at(HEAD_ROWS, h, x)


def hb(h, x=0.0):
    return back_at(HEAD_ROWS, h, x)


def ha(h):
    return interp_row(HEAD_ROWS, h)[0] / 2.0


# ears
for s in (-1, 1):
    cx, cd, chh = s * .88, .02, 5.48
    # outline in the D-H plane: .30 (D) x .48 (H), octagonal, chamfer .09, extruded along X by .30 (root penetrates)
    a, b, cc = .15, .24, .085
    o = [(-a + cc, -b), (a - cc, -b), (a, -b + cc), (a, b - cc), (a - cc, b), (-a + cc, b), (-a, b - cc), (-a, -b + cc)]
    x_in = s * .73
    x_out = s * 1.03
    # frame: outer ring (flat face with the recess), body behind
    # body block (outer face recessed by .035)
    body_poly = [V((x_in, cd + d, chh + h)) for d, h in o]
    prism_poly(hd, "HD_ear_body_" + ("R" if s < 0 else "L"), body_poly, (x_out - x_in - s * .035, 0, 0), sh_skin,
               {"recipe": "ear octagonal block .30 x .30 x .48 (outer face recessed .035)", "class": "observed+prescribed"})
    # outer rim frame around the recess (recess .13 wide x .25 high)
    rd, rh = .065, .125
    frame = {"top": (-a, a, rh, b), "bottom": (-a, a, -b, -rh + .0),
             "front": (-a, -rd, -rh, rh), "back": (rd, a, -rh, rh)}
    for nm, (d0, d1, h0, h1) in frame.items():
        xs = sorted((x_out - s * .035, x_out))
        # outline in D-H, thin plate .035 along X
        poly = [V((x_out - s * .035, cd + d0, chh + h0)), V((x_out - s * .035, cd + d1, chh + h0)),
                V((x_out - s * .035, cd + d1, chh + h1)), V((x_out - s * .035, cd + d0, chh + h1))]
        tf = sh_skin
        prism_poly(hd, "HD_ear_rim_%s_%s" % (nm, "R" if s < 0 else "L"), poly, (s * .035, 0, 0), tf,
                   {"recipe": "ear outer rim around the inner recess", "class": "observed+prescribed"})
    # recess floor + lower lobe plane
    floor = [V((x_out - s * .035, cd - rd, chh - rh)), V((x_out - s * .035, cd + rd, chh - rh)),
             V((x_out - s * .035, cd + rd, chh + rh)), V((x_out - s * .035, cd - rd, chh + rh))]
    prism_poly(hd, "HD_ear_recess_" + ("R" if s < 0 else "L"), floor, (s * .004, 0, 0), sh_const("SKIN_DARK"),
               {"recipe": "ear inner recess .13 x .25, depth .035", "class": "observed+prescribed"})
    lobe = [V((x_out - s * .035, cd - rd, chh - rh - .0)), V((x_out - s * .035, cd + rd, chh - rh)),
            V((x_out - s * .035, cd + rd, chh - rh + .06)), V((x_out - s * .035, cd - rd, chh - rh + .06))]
    prism_poly(hd, "HD_ear_lobe_" + ("R" if s < 0 else "L"), lobe, (s * .006, 0, 0), sh_const("SKIN"),
               {"recipe": "small SKIN lower-lobe plane inside the recess", "class": "inferred"})

# eyes: sclera, pupil, lid, lid line, lower rim
EYES = {-1: (-.34, 5.74), 1: (.34, 5.72)}
for s, (ex, eh) in EYES.items():
    nm = "R" if s < 0 else "L"
    f = hf(eh)
    w_, h_ = .28, .21
    x0, x1 = ex - w_ / 2, ex + w_ / 2
    y0, y1 = eh - h_ / 2, eh + h_ / 2
    d_front = f - .025
    # sclera: capped patch (front at f-.025, back embedded)
    loft(hd, "HD_eye_white_" + nm, [[V((x0, f + .01, y0)), V((x1, f + .01, y0)), V((x1, f + .01, y1)), V((x0, f + .01, y1))],
                                    [V((x0 + .01, d_front, y0 + .01)), V((x1 - .01, d_front, y0 + .01)),
                                     V((x1 - .01, d_front, y1 - .01)), V((x0 + .01, d_front, y1 - .01))]],
         sh_const("EYE_WHITE"), meta={"recipe": "fitted eye patch .28 x .21", "class": "observed+prescribed",
                                      "note": "back embedded .01 so the patch is attached to the shell"})
    # lid boundary: outer end at -.075 below patch top, medial end -.100
    med = (x1 if s < 0 else x0)     # medial = towards nose (X=0)
    out_ = (x0 if s < 0 else x1)

    def lid_y(x, _out=out_, _med=med, _top=y1):
        t = (x - _out) / (_med - _out)
        return _top - .075 - .025 * t
    # pupil: .10 x .125, shifted -.025 in X (glance toward the mug), clipped at the lid
    px = ex - .025
    px0, px1 = px - .05, px + .05
    py0 = eh - .0625
    pty0, pty1 = lid_y(px0), lid_y(px1)
    pp = [V((px0, d_front + .004, py0)), V((px1, d_front + .004, py0)), V((px1, d_front + .004, min(py0 + .125, pty1))),
          V((px0, d_front + .004, min(py0 + .125, pty0)))]
    prism_poly(hd, "HD_pupil_" + nm, pp, (0, -.012, 0), sh_const("EYE_BLACK"),
               {"recipe": "pupil .10 x .125, clipped by the eyelid", "class": "observed+prescribed"})
    # upper lid panel (SKIN) covering the top .075.. and slightly beyond the patch, front .005 ahead of the sclera
    lp = [V((x0 - .01, d_front - .006, y1 + .015)), V((x1 + .01, d_front - .006, y1 + .015)),
          V((x1 + .01, d_front - .006, lid_y(x1 + .01))), V((x0 - .01, d_front - .006, lid_y(x0 - .01)))]
    prism_poly(hd, "HD_eyelid_" + nm, lp, (0, f + .01 - (d_front - .006), 0), sh_skin,
               {"recipe": "half-lid SKIN panel overlapping the upper .075, boundary slopes .025 to the nose",
                "class": "observed+prescribed"})
    ll = [V((x0 - .005, d_front + .004, lid_y(x0 - .005) - .012)), V((x1 + .005, d_front + .004, lid_y(x1 + .005) - .012)),
          V((x1 + .005, d_front + .004, lid_y(x1 + .005))), V((x0 - .005, d_front + .004, lid_y(x0 - .005)))]
    prism_poly(hd, "HD_lidline_" + nm, ll, (0, -.0155, 0), sh_const("EYE_BLACK"),
               {"recipe": "thin upper lid line .012 high", "class": "observed+prescribed"})
    lr = [V((x0, d_front + .004, y0 - .012)), V((x1, d_front + .004, y0 - .012)),
          V((x1, d_front + .004, y0)), V((x0, d_front + .004, y0))]
    prism_poly(hd, "HD_lowerrim_" + nm, lr, (0, -.0085, 0), sh_const("SKIN_LIGHT"),
               {"recipe": "lower eye rim .012", "class": "observed+prescribed"})

# eyebrows: .47 x .12 x .16, medial end .035 lower
for s, (bx, bh) in {-1: (-.34, 6.02), 1: (.34, 5.97)}.items():
    nm = "R" if s < 0 else "L"
    f = hf(bh)
    cen = V((bx, f - .060, bh))
    ang = math.degrees(math.atan2(.035, .47))
    # medial end is the one nearer X=0: right brow (X<0) medial = +X side -> that end lower
    sign = -1.0 if s < 0 else 1.0
    rings = cbox((0, 0, 0), (.47, .15, .16), .025, xf=lambda p, _a=ang * sign: V(Matrix.Rotation(math.radians(_a), 3, 'Y') @ p))
    rings = [[p + cen for p in r] for r in rings]
    loft(hd, "HD_brow_" + nm, rings, sh_hair,
         meta={"recipe": "solid brow .47 x .15 x .16, bevel .025, medial end .035 lower", "class": "observed+prescribed",
               "note": "depth .15 instead of .12: front stays at f-.135, back embedded .015 so the brow is attached"})

# nose: bridge + bulb (closed loft)
nose_rings = []
for h, w, f, b, c in NOSE_ROWS:
    nose_rings.append(ring8(w / 2, f, b, c, 0, 0, h))
loft(hd, "HD_nose_bulb", nose_rings, sh_nose, meta={"recipe": "bulb rings of section 9.1", "dims": {"rows": NOSE_ROWS},
                                                    "class": "observed+prescribed"})
bridge = [V((-.10, -.66, 5.65)), V((.10, -.66, 5.65)), V((.10, -.66, 5.93)), V((-.10, -.66, 5.93))]
prism_poly(hd, "HD_nose_bridge", bridge, (0, -.18, 0), sh_nose,
           {"recipe": "bridge .20 wide H5.65..5.93, joins the face near D-.71 and projects to -.84", "class": "observed+prescribed",
            "note": "starts at D-.66 (embedded .05) and ends at -.84"})
for s in (-1, 1):
    h0 = 5.435
    wbulb, fb, _, _ = interp_row(NOSE_ROWS, h0)
    pts = [V((s * .14 - .0275, fb + .004, h0 - .0125)), V((s * .14 + .0275, fb + .004, h0 - .0125)),
           V((s * .14 + .0275, fb + .004, h0 + .0125)), V((s * .14 - .0275, fb + .004, h0 + .0125))]
    prism_poly(hd, "HD_nostril_" + ("R" if s < 0 else "L"), pts, (0, -.010, 0), sh_const("SKIN_DARK"),
               {"recipe": "nostril hint .055 x .025 fitted to the actual bulb surface", "class": "observed+prescribed",
                "note": "prescribed D-1.015 lies inside the bulb; placed on the real front surface"})

# mustache (two lobes)
MUS = [(-.03, 5.37), (-.18, 5.46), (-.38, 5.43), (-.57, 5.50), (-.69, 5.38), (-.65, 5.24), (-.45, 5.21), (-.23, 5.26), (-.05, 5.29)]
for s in (-1, 1):
    pts = [(x, h) for x, h in MUS]
    if s > 0:
        pts = [(-x, h + (.015 if i in (3, 4) else 0.0)) for i, (x, h) in enumerate(MUS)]
        pts = pts[::-1]
    layered_plate(hd, "HD_mustache_" + ("R" if s < 0 else "L"), pts, lambda x, h: hf(h, x),
                  [(.02, 1.0, 1.0), (-.03, 1.0, 1.0), (-.10, .93, .90), (-.135, .78, .72)], sh_hair,
                  {"recipe": "mustache lobe outline of section 9.2, depth .14 + ridge via shrinking layers", "class": "observed+prescribed"})

# mouth: strip + under-lip highlight + chin crease
mpts = [V((-.24, hf(5.13) - .012, 5.13)), V((0.0, hf(5.10) - .012, 5.10)), V((.28, hf(5.17) - .012, 5.17))]
n = len(mpts)
P = []
for i, p in enumerate(mpts):
    P += [p + V((0, 0, .009)), p - V((0, 0, .009)), p + V((0, .016, .009)), p + V((0, .016, -.009))]
faces = []
for i in range(n - 1):
    a, b = i * 4, (i + 1) * 4
    faces += [[a, a + 1, b + 1, b], [a + 2, b + 2, b + 3, a + 3], [a, b, b + 2, a + 2], [a + 1, a + 3, b + 3, b + 1]]
faces += [[0, 1, 3, 2]]
e = (n - 1) * 4
faces += [[e, e + 2, e + 3, e + 1]]
hd.solid("HD_mouth_smirk", P, faces, sh_const("MOUTH"), {"recipe": "closed smirk strip .018 wide", "class": "observed+prescribed"})
solid_box(hd, "HD_lip_highlight", -.12, .18, hf(5.075) - .008, hf(5.075) + .01, 5.0575, 5.0925, sh_const("SKIN_LIGHT"),
          {"recipe": "under-lip highlight .30 x .035", "class": "observed+prescribed"})
solid_box(hd, "HD_chin_crease", -.14, .20, hf(5.02) - .006, hf(5.02) + .01, 5.015, 5.025, sh_const("MOUTH_LIGHT"),
          {"recipe": "chin crease .34 x .010", "class": "observed+prescribed"})

# hair: side tufts (4 per side) + inferred back band
TUFTS = [((.80, -.04, 6.05), (.28, .30, .18)), ((.86, .11, 5.94), (.32, .34, .20)),
         ((.88, .29, 5.83), (.30, .34, .20)), ((.76, .45, 6.07), (.29, .32, .19))]
for s in (-1, 1):
    for i, ((cx, cd, chh), (w_, d_, h_)) in enumerate(TUFTS):
        cx *= s
        nm = "HD_hair_side%02d_%s" % (i + 1, "R" if s < 0 else "L")
        bot_shift = V((s * .06 * w_ / .3, 0, 0))
        top = ring8(w_ / 2, -d_ / 2, d_ / 2, .045, 0, 0, h_ / 2)
        bot = ring8(w_ * .30, -d_ * .40, d_ * .40, .04, 0, 0, -h_ / 2)
        mid = ring8(w_ / 2, -d_ / 2, d_ / 2, .045, 0, 0, h_ / 2 - .045)
        rings = [[p + V((cx, cd, chh)) + bot_shift for p in bot],
                 [p + V((cx, cd, chh)) + bot_shift * .4 for p in ring8(w_ * .45, -d_ * .47, d_ * .47, .04, 0, 0, -h_ / 2 + .045)],
                 [p + V((cx, cd, chh)) for p in mid],
                 [p + V((cx, cd, chh)) for p in top]]
        loft(hd, nm, rings, sh_hair, meta={"recipe": "chunky tapered side tuft (section 10)", "class": "observed+prescribed"})

HB = [(-.72, 6.00), (-.72, 5.86), (-.62, 5.73), (-.52, 5.73), (-.40, 5.60), (-.28, 5.73), (-.12, 5.73), (0.0, 5.60),
      (.12, 5.73), (.28, 5.73), (.40, 5.60), (.52, 5.73), (.62, 5.73), (.72, 5.86), (.72, 6.00), (.55, 6.14), (-.55, 6.14)]
layered_plate(hd, "HD_hair_back_band", HB, lambda x, h: hb(h, x), [(-.05, 1.0, 1.0), (.0, 1.0, 1.0), (.09, .96, .94), (.115, .90, .86)],
              sh_hair, {"recipe": "inferred rear hair band D.57..73, H5.73..6.14 with three low lobes", "class": "inferred"})

# ----------------------------------------------------------------------------------------------
# arms and hands
# ----------------------------------------------------------------------------------------------
ARM = {}
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    S, E, W = JV[side + "Shoulder"], JV[side + "Elbow"], JV[side + "Wrist"]
    ARM[side] = (S, E, W)
    ax = Axis(S, E)
    ua = PM(side + "UpperArm", S)
    sleeve = [(0.0, .92, .88), (.15, .94, .88), (.60, .92, .84), (.73, .86, .82)]
    loft(ua, "UA_sleeve_" + side, [ax.ring(t, w, d, .07) for t, w, d in sleeve], sh_teal,
         meta={"recipe": "polo sleeve shell t=0..0.73 (section 11)", "class": "observed+prescribed"})
    cuff = []
    for t in (.64, .725, .73):
        w, d = sec_at(sleeve, t)
        g = .025 if t < .73 else .01
        cuff.append(ax.ring(t, w + 2 * g, d + 2 * g, .07))
    loft(ua, "UA_cuff_" + side, cuff, sh_const("TEAL_DARK"),
         meta={"recipe": "cuff band t=.64..73, .025 proud, TEAL_DARK", "class": "observed+prescribed"})
    t_ext = 1.0 + .02 / ax.L
    skin = [(.70, .88, .82), (1.0, .78, .76), (t_ext, .78, .76)]
    loft(ua, "UA_skin_" + side, [ax.ring(t, w, d, .07) for t, w, d in skin], sh_skin_arm,
         meta={"recipe": "exposed upper-arm skin t=.70..1.0 (+.02 joint overlap)", "class": "observed+prescribed"})

    la = PM(side + "LowerArm", E)
    ax2 = Axis(E, W)
    lsec = [(0.0, .78, .76), (.50, .80, .75), (1.0, .76, .70)]
    if SLIM_FOREARM and s < 0:
        # slimmer, smoothly tapering forearm (mid x0.85, wrist x0.79 of the approved values); elbow end nearly matches the upper-arm skin ring
        lsec = [(0.0, .76, .72), (.40, .68, .64), (1.0, .60, .56)]
    t_ext2 = 1.0 + .02 / ax2.L
    rings = [ax2.ring(t, w, d, .035) for t, w, d in lsec] + [ax2.ring(t_ext2, lsec[-1][1], lsec[-1][2], .035)]
    loft(la, "LA_forearm_" + side, rings, sh_skin_arm,
         meta={"recipe": "forearm sections of section 12, bevel .035", "class": "observed+prescribed"})

# hands (booleans)
MAT_BOOL = []


def bm_to_obj(bm, name, tile_default=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    ob = bpy.data.objects.new(name, me)
    SCENE.collection.objects.link(ob)
    return ob


def tile_layer(bm):
    return bm.faces.layers.int.get("tile") or bm.faces.layers.int.new("tile")


def solid_tiled(P, faces, tilename):
    bm = make_bm_solid(P, faces)
    tl = tile_layer(bm)
    for f in bm.faces:
        f[tl] = TILE[tilename]
    return bm


def box_solid(x0, x1, y0, y1, z0, z1, tilename, ch=0.0):
    if ch > 0:
        c = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        rings = cbox(c, (x1 - x0, y1 - y0, z1 - z0), ch)
        P = [p for r in rings for p in r]
        faces = loft_faces(len(rings), 8)
    else:
        rings = box_rings(x0, x1, y0, y1, z0, z1)
        P = [p for r in rings for p in r]
        faces = loft_faces(2, 4)
    return solid_tiled(P, faces, tilename)


def cyl_solid(cx, cy, z0, z1, r, tilename, segs=16):
    r0 = [V((cx + r * math.cos(2 * math.pi * k / segs), cy + r * math.sin(2 * math.pi * k / segs), z0)) for k in range(segs)]
    r1 = [p + V((0, 0, z1 - z0)) for p in r0]
    P = r0 + r1
    return solid_tiled(P, loft_faces(2, segs), tilename)


def bool_apply(a_obj, b_obj, op):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = a_obj
    a_obj.select_set(True)
    m = a_obj.modifiers.new("B", 'BOOLEAN')
    m.object = b_obj
    m.operation = op
    m.solver = 'EXACT'
    bpy.ops.object.modifier_apply(modifier=m.name)


def obj_to_bm(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.normal_update()
    return bm


def hand_build(side, s):
    W = JV[side + "Wrist"]
    pm = PM(side + "Hand", W)
    # local (u,v,w) = (X,D,H) relative to the wrist
    if side == "Right":
        base = box_solid(-.37, .37, -.35, .35, -.68, 0.0, "SKIN", ch=.035)
        o = bm_to_obj(base, "tmp_hand")
        base.free()
        cut = cyl_solid(-.12, -.13, -.60, -.10, .065, "SKIN_DARK", 16)
        slot = box_solid(-.12, .40, -.205, -.055, -.60, -.10, "SKIN_DARK")
        thumb = box_solid(.16, .38, -.11, .14, -.22, -.02, "SKIN", ch=.02)
        for nm, bmx, op in (("cut", cut, 'DIFFERENCE'), ("slot", slot, 'DIFFERENCE'), ("thumb", thumb, 'UNION')):
            co = bm_to_obj(bmx, "tmp_" + nm)
            bmx.free()
            bool_apply(o, co, op)
            bpy.data.objects.remove(co, do_unlink=True)
        # finger grooves on the front finger band: three shallow SKIN_DARK grooves, depth .008
        for gw in (-.20, -.36, -.52):
            g = box_solid(-.19, .19, -.35 - .001, -.35 + .008, gw - .006, gw + .006, "SKIN_DARK")
            co = bm_to_obj(g, "tmp_groove")
            g.free()
            bool_apply(o, co, 'DIFFERENCE')
            bpy.data.objects.remove(co, do_unlink=True)
    else:
        base = box_solid(-.35, .35, -.32, .32, -.68, 0.0, "SKIN", ch=.035)
        o = bm_to_obj(base, "tmp_hand")
        base.free()
        notch = box_solid(-.08, .12, -.36, -.10, -.69, -.42, "SKIN_DARK")
        thumb = box_solid(-.40, -.18, -.36, -.08, -.48, -.15, "SKIN", ch=.03)
        for nm, bmx, op in (("notch", notch, 'DIFFERENCE'), ("thumb", thumb, 'UNION')):
            co = bm_to_obj(bmx, "tmp_" + nm)
            bmx.free()
            bool_apply(o, co, op)
            bpy.data.objects.remove(co, do_unlink=True)
    bm = obj_to_bm(o)
    bpy.data.objects.remove(o, do_unlink=True)
    # translate to the wrist
    bmesh.ops.translate(bm, vec=W, verts=bm.verts)
    # shading by normal (skin variants); grooves/channel keep SKIN_DARK
    tl = bm.faces.layers.int.get("tile")
    for f in bm.faces:
        f.normal_update()
        cur = PAL[f[tl]][0] if tl is not None else "SKIN"
        if cur == "SKIN_DARK":
            continue
        f[tl] = TILE[sh_skin_arm(f.normal.copy(), f.calc_center_median())]
    pm.append_bm("HAND_" + side, bm, None,
                 {"recipe": "block hand (section 12.%d)" % (1 if side == "Right" else 2),
                  "class": "observed+prescribed",
                  "note": "boolean EXACT: grip channel r.065 + slot + thumb pad + 3 grooves" if side == "Right"
                  else "boolean EXACT: front-bottom notch + merged thumb volume"})
    bm.free()


hand_build("Right", -1)
hand_build("Left", 1)

# ----------------------------------------------------------------------------------------------
# legs and shoes
# ----------------------------------------------------------------------------------------------
LEG = {}
UPPER_SEC = [(0.0, 1.10, 1.02), (.50, 1.12, 1.02), (1.0, 1.02, .96)]
LOWER_SEC = [(0.0, 1.02, .96), (.70, 1.04, .98), (1.0, 1.06, 1.00)]
POCKET_PENT = [(-.25, .20), (.25, .20), (.25, -.20), (0.0, -.25), (-.25, -.20)]


def leg_build(s):
    side = "Right" if s < 0 else "Left"
    hip, knee, ank = JV[side + "Hip"], JV[side + "Knee"], JV[side + "Ankle"]
    shade = sh_jeans(s)
    ul = PM(side + "UpperLeg", hip)
    axu = Axis(hip, knee)
    t_ext = 1.0 + .02 / axu.L
    secs = UPPER_SEC + [(t_ext,) + UPPER_SEC[-1][1:]]
    loft(ul, "UL_thigh_" + side, [axu.ring(t, w, d, .07) for t, w, d in secs], shade,
         meta={"recipe": "thigh sections of section 14", "class": "observed+prescribed"})
    # outer seam .012 wide: strip along the outside face
    pts = []
    for t in (0.0, .5, 1.0):
        w, d = sec_at(UPPER_SEC, t)
        pts.append(axu.at(t) + axu.U * (s * (w / 2 + .0)) )
    P = []
    for p in pts:
        P += [p + axu.Q * .006 + axu.U * (s * .004), p - axu.Q * .006 + axu.U * (s * .004),
              p + axu.Q * .006 - axu.U * (s * .02), p - axu.Q * .006 - axu.U * (s * .02)]
    faces = []
    for i in range(len(pts) - 1):
        a, b = i * 4, (i + 1) * 4
        faces += [[a, a + 1, b + 1, b], [a + 2, b + 2, b + 3, a + 3], [a, b, b + 2, a + 2], [a + 1, a + 3, b + 3, b + 1]]
    faces += [[0, 1, 3, 2]]
    e = (len(pts) - 1) * 4
    faces += [[e, e + 2, e + 3, e + 1]]
    ul.solid("UL_seam_" + side, P, faces, sh_const("JEANS_DARK"),
             {"recipe": "outer seam .012 wide, JEANS_DARK, proud .004", "class": "observed+prescribed"})
    # front pocket-edge lower segment (hip boundary split)
    x_a = s * (.62 + .50 * (2.12 - HIP_H) / .10)
    pts = [V((x_a, front_at(LT_ROWS, HIP_H + 0.0, x_a), HIP_H))]
    xb, hb_ = s * 1.12, 2.02
    xc, hc = s * 1.15, 1.85
    for xx, hh in ((xb, hb_), (xc, hc)):
        t = (hip.z - hh) / (hip.z - knee.z)
        w, d = sec_at(UPPER_SEC, t)
        c0 = axu.at(t)
        a = w / 2
        xr = min(abs(xx - c0.x), a)
        fd = c0.y - d / 2 + max(0.0, xr - (a - .07))
        pts.append(V((xx, fd, hh)))
    thin_polyline(ul, "UL_pocket_edge_" + side, pts, .012, .006, .01, sh_const("JEANS_DARK"),
                  meta={"recipe": "front pocket edge, lower segment on the thigh", "class": "observed+prescribed"})
    # rear pocket patch (inferred)
    cx, ch_ = s * .64, 1.72
    t = (hip.z - ch_) / (hip.z - knee.z)
    w, d = sec_at(UPPER_SEC, t)
    c0 = axu.at(t)
    bdep = c0.y + d / 2
    poly = [V((cx + px, bdep + .015, ch_ + py)) for px, py in POCKET_PENT]
    prism_poly(ul, "UL_rear_pocket_" + side, poly, (0, .010, 0), sh_const("JEANS"),
               {"recipe": "five-sided rear pocket patch (inferred), thickness .010", "class": "inferred"})
    ins = .025
    seam = [V((cx + px * (1 - ins / .25 if abs(px) > 0 else 1), bdep + .025, ch_ + py * (1 - ins / .2 if abs(py) > .1 else 1)))
            for px, py in POCKET_PENT]
    for k in range(len(seam)):
        p0, p1 = seam[k], seam[(k + 1) % len(seam)]
        m = (p1 - p0)
        ln = m.length
        if ln < 1e-5:
            continue
        tdir = m / ln
        nrm = V((0, 1, 0))
        sd = tdir.cross(nrm).normalized() * .004
        rect = [p0 - sd, p1 - sd, p1 + sd, p0 + sd]
        prism_poly(ul, "UL_pocket_seam_%s_%d" % (side, k), rect, (0, .006, 0), sh_const("JEANS_DARK"),
                   {"recipe": "pocket edge seam strip .008 (inset .025)", "class": "inferred"})

    ll = PM(side + "LowerLeg", knee)
    axl = Axis(knee, ank)
    t_ext2 = 1.0 + .0 / axl.L
    rings = [axl.ring(t, w, d, .065) for t, w, d in LOWER_SEC]
    loft(ll, "LL_shin_" + side, rings, shade,
         meta={"recipe": "shin sections of section 14", "class": "observed+prescribed"})
    # cuff: last .14 of the bone length, outer expansion .025
    t0 = 1.0 - .14 / axl.L
    w0, d0 = sec_at(LOWER_SEC, t0)
    w1, d1 = sec_at(LOWER_SEC, 1.0)
    cuff = [axl.ring(t0, w0, d0, .065), axl.ring(t0 + .012, w0 + .05, d0 + .05, .07),
            axl.ring(1.0 - .01, w1 + .05, d1 + .05, .07), axl.ring(1.0, w1 + .01, d1 + .01, .065)]

    def sh_cuff(n, c):
        if n.z < -0.5:
            return "JEANS_DARK"
        if n.z > 0.5 or n.y < -0.5:
            return "JEANS_LIGHT"
        return "JEANS"
    loft(ll, "LL_cuff_" + side, cuff, sh_cuff,
         meta={"recipe": "trouser cuff, last .14 of the bone length, +.025", "class": "observed+prescribed"})
    LEG[side] = (hip, knee, ank)

    ft = PM(side + "Foot", ank, xf=lambda p, _s=s: V(rot_about(p, V((_s * .64, 0, 0)), 'Z', TOE_OUT[_s])))
    cx = s * .64
    # sole: outline w1.22 x d1.52, centre D-.26, chamfer .14, H0..13 bevel .02
    ow = ring8(.61, -1.02, .50, .14, cx, 0, 0.0)
    rings = []
    for h, g in ((0.0, .02), (.02, 0.0), (.11, 0.0), (.13, .02)):
        rings.append(ring8(.61 - g, -1.02 + g, .50 - g, .14, cx, 0, h))
    # bottom with the heel recess: build the closed sole manually
    n = 8
    P = [p for r in rings for p in r]
    faces = []
    for i in range(3):
        for k in range(n):
            faces.append([i * n + k, i * n + (k + 1) % n, (i + 1) * n + (k + 1) % n, (i + 1) * n + k])
    top = list(range(3 * n, 4 * n))
    faces.append(top)
    # underside annulus + recess (.30 x .18 x .015 near the rear centre)
    rc = [V((cx - .15, .23, 0.0)), V((cx + .15, .23, 0.0)), V((cx + .15, .41, 0.0)), V((cx - .15, .41, 0.0))]
    rcu = [p + V((0, 0, .015)) for p in rc]
    base_n = len(P)
    P += rc + rcu
    outer = list(range(n))
    inner = list(range(base_n, base_n + 4))
    tris = mgeo.tessellate_polygon([[P[i] for i in outer], [P[i] for i in inner]])
    allidx = outer + inner
    for a, b, c in tris:
        faces.append([allidx[a], allidx[b], allidx[c]])
    for k in range(4):
        faces.append([base_n + k, base_n + (k + 1) % 4, base_n + 4 + (k + 1) % 4, base_n + 4 + k])
    faces.append(list(range(base_n + 4, base_n + 8)))
    ft.solid("FT_sole_" + side, P, faces, sh_const("SOLE"),
             {"recipe": "sole outline 1.22 x 1.52, H0..13, heel recess .30 x .18 x .015 (inferred underside)", "class": "observed+prescribed"})
    # heel block D.14..50, H.13..21
    loft(ft, "FT_heel_" + side, [ring8(.60, .14, .50, .12, cx, 0, .13), ring8(.60, .14, .50, .12, cx, 0, .21)], sh_const("SOLE"),
         meta={"recipe": "dark heel block rear quarter D.14..50", "class": "observed+prescribed"})
    # upper loft
    urings = [row_ring(r, cx, 0) for r in SHOE_ROWS]
    loft(ft, "FT_upper_" + side, urings, sh_shoe,
         meta={"recipe": "shoe upper loft of section 15", "dims": {"rows": SHOE_ROWS}, "class": "observed+prescribed"})

    def usurf(x, d_):
        """Height of the upper at lateral offset x (from shoe centre) for D=d_ (flat region)."""
        ax_ = abs(x)
        pts_ = [(r[0], r[1] / 2.0) for r in SHOE_ROWS]
        if ax_ <= pts_[-1][1]:
            return SHOE_ROWS[-1][0]
        for (h0, a0), (h1, a1) in zip(pts_, pts_[1:]):
            if a1 <= ax_ <= a0:
                tt = (a0 - ax_) / (a0 - a1)
                return h0 + (h1 - h0) * tt
        return pts_[0][0]
    # transverse vamp seam at D=-.32 across X +-.47 (polyline up and over)
    seam_xs = [-.47, -.42, -.38, 0.0, .38, .42, .47]
    pts = [V((cx + x, -.32, usurf(x, -.32) + .003)) for x in seam_xs]
    P = []
    for p in pts:
        P += [p + V((0, -.007, .0)), p + V((0, .007, 0)), p + V((0, -.007, -.008)), p + V((0, .007, -.008))]
    faces = []
    for i in range(len(pts) - 1):
        a, b = i * 4, (i + 1) * 4
        faces += [[a, a + 1, b + 1, b], [a + 2, b + 2, b + 3, a + 3], [a, b, b + 2, a + 2], [a + 1, a + 3, b + 3, b + 1]]
    faces += [[0, 1, 3, 2]]
    e = (len(pts) - 1) * 4
    faces += [[e, e + 2, e + 3, e + 1]]
    ft.solid("FT_vamp_seam_" + side, P, faces, sh_const("SOLE"),
             {"recipe": "transverse vamp seam at D-.32 across X+-.47, .014 wide", "class": "observed+prescribed"})
    for sx in (-1, 1):
        x_ = sx * .524
        pts = [V((cx + x_, -.32, .40)), V((cx + x_, -.08, .40))]
        P = []
        for p in pts:
            P += [p + V((sx * .006, 0, .007)), p + V((sx * .006, 0, -.007)), p + V((-sx * .01, 0, .007)), p + V((-sx * .01, 0, -.007))]
        faces = [[0, 1, 5, 4], [2, 6, 7, 3], [0, 4, 6, 2], [1, 3, 7, 5], [0, 2, 3, 1], [4, 5, 7, 6]]
        ft.solid("FT_side_seam_%s_%d" % (side, sx), P, faces, sh_const("SOLE"),
                 {"recipe": "short continuation seam along the upper side edge, .24 long", "class": "observed+prescribed"})


leg_build(-1)
leg_build(1)

# ----------------------------------------------------------------------------------------------
# mug (mug-local origin = centre of the lowest underside; placed at the reference-pose origin)
# ----------------------------------------------------------------------------------------------
mug = PM("Mug", MUG_ORIGIN_REF, geo="Mug_Geo")
MO = MUG_ORIGIN_REF


def mring(w, d, c, z):
    return ring8(w / 2, -d / 2, d / 2, c, MO.x, MO.y, MO.z + z)


# ceramic body: outer sidewall + rim + inner walls + floor, closed
rings_out = [mring(w, d, c, z) for z, w, d, c in MUG_OUT]
rings_in = [mring(w, d, c, z) for z, w, d, c in MUG_IN]
n = 8
P = []
for r in rings_out:
    P += r
for r in rings_in:
    P += r
faces = []
nr = len(rings_out) + len(rings_in)
for i in range(nr - 1):
    for k in range(n):
        faces.append([i * n + k, i * n + (k + 1) % n, (i + 1) * n + (k + 1) % n, (i + 1) * n + k])
# floor cap (inner floor ring)
faces.append(list(range((nr - 1) * n, nr * n)))
# bottom with foot recess .56 x .42 depth .015
rcw, rcd = .56, .42
rec = ring8(rcw / 2, -rcd / 2, rcd / 2, .05, MO.x, MO.y, MO.z + 0.0)
rec_up = [p + V((0, 0, .015)) for p in rec]
base_n = len(P)
P += rec + rec_up
outer = list(range(n))
inner = list(range(base_n, base_n + n))
tr = mgeo.tessellate_polygon([[P[i] for i in outer], [P[i] for i in inner]])
allidx = outer + inner
for a, b, c in tr:
    faces.append([allidx[a], allidx[b], allidx[c]])
for k in range(n):
    faces.append([base_n + k, base_n + (k + 1) % n, base_n + n + (k + 1) % n, base_n + n + k])
faces.append(list(range(base_n + n, base_n + 2 * n)))


def sh_mug(n_, c):
    # inside faces (normals pointing to the cavity axis) and the underside use MUG_INNER
    rel = c - V((MO.x, MO.y, MO.z))
    if n_.z < -0.5:
        return "MUG_INNER"
    if rel.z < 1.095 and rel.z > .13:
        horiz = V((n_.x, n_.y, 0))
        if horiz.length > .3:
            toward_axis = -(V((rel.x, rel.y, 0)).normalized().dot(horiz.normalized()))
            if toward_axis > 0.3 and abs(rel.x) < .36 and abs(rel.y) < .29:
                return "MUG_INNER"
    if n_.z > 0.5 and rel.z < .2:
        return "MUG_INNER"
    return "MUG"


mug.solid("MUG_ceramic", P, faces, sh_mug,
          {"recipe": "ceramic wall volume from the ring profiles of section 16.1, walls .06 / floor .14, foot recess .56x.42x.015",
           "class": "observed+prescribed", "dims": {"outer": MUG_OUT, "inner": MUG_IN}})


# handle: planar centerline swept with a rounded-square section (Catmull-Rom 2 segments per interval)
def catmull(pts, seg=2):
    out = []
    n_ = len(pts)
    for i in range(n_ - 1):
        p0 = pts[max(i - 1, 0)]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[min(i + 2, n_ - 1)]
        for k in range(seg):
            t = k / seg
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(pts[-1])
    return out


hp = [V(p) for p in HANDLE_PTS]
curve = catmull(hp, 2)
rings = []
for i, p in enumerate(curve):
    t = (curve[min(i + 1, len(curve) - 1)] - curve[max(i - 1, 0)]).normalized()
    B = V((0, 1, 0))
    N = B.cross(t).normalized()
    hw_, c_ = .055, .02
    pts_ = [(-hw_ + c_, -hw_), (hw_ - c_, -hw_), (hw_, -hw_ + c_), (hw_, hw_ - c_), (hw_ - c_, hw_), (-hw_ + c_, hw_),
            (-hw_, hw_ - c_), (-hw_, -hw_ + c_)]
    rings.append([MO + p + B * x + N * y for x, y in pts_])
loft(mug, "MUG_handle", rings, sh_const("MUG"),
     meta={"recipe": "C-handle: rounded-square .11 section swept along the 8-point centerline (Catmull-Rom, 2 seg/bend)",
           "class": "observed+prescribed", "dims": {"centerline": HANDLE_PTS}})
for nm, wz in (("upper", .87), ("lower", .28)):
    solid_box(mug, "MUG_rootpad_" + nm, MO.x - .48, MO.x - .40, MO.y - .07, MO.y + .07, MO.z + wz - .07, MO.z + wz + .07, sh_const("MUG"),
              {"recipe": "root pad .14 w x .14 h x .07 deep on the side wall", "class": "observed+prescribed"})

# coffee: closed volume fitted to the inner cavity with .008 clearance, top at w=.98
cof = [mring(.60 - .016, .46 - .016, .05, .14), mring(.70 - .016, .56 - .016, .05, .98)]
loft(mug, "MUG_coffee", cof, sh_const("COFFEE"),
     meta={"recipe": "coffee volume w=.14..0.98 (top .12 below rim), clearance .008", "class": "observed+prescribed"})
# meniscus band .012 darker at the perimeter (thin slab on top)
cm = [mring(.70 - .016, .56 - .016, .05, .978), mring(.70 - .016, .56 - .016, .05, .98)]
loft(mug, "MUG_meniscus", [cm[0], cm[1]], sh_const("COFFEE_DARK"),
     meta={"recipe": "meniscus shade band", "class": "prescribed"})

# ----------------------------------------------------------------------------------------------
# materials / UV / vertex colors / mesh objects
# ----------------------------------------------------------------------------------------------
atlas = bpy.data.images.new("RegularDad_Palette", ATLAS_W, ATLAS_H, alpha=False)
atlas.colorspace_settings.name = 'sRGB'   # must be set BEFORE writing pixels (a later change resets the buffer)
px = [0.0] * (ATLAS_W * ATLAS_H * 4)
ivory = hex_rgb(_H["MUG"])
for ty in range(ATLAS_H):
    for tx in range(ATLAS_W):
        idx = (ty // TILE_PX) * COLS + (tx // TILE_PX)
        rgb = hex_rgb(PAL[idx][1]) if idx < len(PAL) else ivory
        r, g, b = (c / 255.0 for c in rgb)
        # PNG row 0 is the top: Blender image row 0 is the bottom
        by = ATLAS_H - 1 - ty
        o = (by * ATLAS_W + tx) * 4
        px[o:o + 4] = [r, g, b, 1.0]
atlas.pixels.foreach_set(px)
atlas.filepath_raw = os.path.join(OUT, "RegularDad_Palette.png")
atlas.file_format = 'PNG'
atlas.save()
atlas.pack()

MATP = bpy.data.materials.new("RegularDad_Palette")
MATP.use_nodes = True
nt = MATP.node_tree
bs = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = atlas
tex.interpolation = 'Closest'
nt.links.new(tex.outputs["Color"], bs.inputs["Base Color"])
bs.inputs["Roughness"].default_value = 0.9
try:
    bs.inputs["Specular IOR Level"].default_value = 0.05
except KeyError:
    pass

for pm in PARTS.values():
    bm = pm.bm
    bm.normal_update()
    me = bpy.data.meshes.new(pm.geo)
    bm.to_mesh(me)
    uv = me.uv_layers.new(name="UVMap")
    ca = me.color_attributes.new("Col", 'BYTE_COLOR', 'CORNER')
    tl = bm.faces.layers.int.get("tile")
    # mesh attribute "tile" per face (bm.to_mesh copies it)
    attr = me.attributes.get("tile")
    for pi, poly in enumerate(me.polygons):
        t = attr.data[pi].value if attr else 0
        u0, v0, u1, v1 = tile_uv_patch(t)
        corners = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
        r_, g_, b_ = hex_rgb(PAL[t][1])
        for k, li in enumerate(poly.loop_indices):
            uv.data[li].uv = corners[k % 4] if k < 4 else corners[k % 4]
            el = ca.data[li]
            try:
                el.color_srgb = (r_ / 255.0, g_ / 255.0, b_ / 255.0, 1.0)
            except AttributeError:
                el.color = (srgb_to_lin(r_), srgb_to_lin(g_), srgb_to_lin(b_), 1.0)
    me.materials.append(MATP)
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new(pm.geo, me)
    EXP_COLL.objects.link(ob)
    # object origin at the part's pivot (child joint), mesh stored relative to it
    off = pm.joint.copy()
    for v in me.vertices:
        v.co -= off
    ob.location = off
    pm.obj = ob
    pm.bm.free()

# editable per-component source objects (not exported)
# (components were merged into the part meshes; the registry records their ids/tiles/counts)

# ----------------------------------------------------------------------------------------------
# armature (standard-compatible hierarchy) + rigid 100% weights
# ----------------------------------------------------------------------------------------------
arm_data = bpy.data.armatures.new("RegularDad_Armature")
ARM_OB = bpy.data.objects.new("RegularDad_Armature", arm_data)
EXP_COLL.objects.link(ARM_OB)
bpy.context.view_layer.objects.active = ARM_OB
ARM_OB.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones


def foot_tail(side, s):
    ank = JV[side + "Ankle"]
    th = math.radians(TOE_OUT[s])
    off = Matrix.Rotation(th, 3, 'Z') @ V((0, -.78, 0))
    return V((ank.x + off.x, ank.y + off.y, .12))


BONES = [
    ("Root", None, V((0, 0, 0)), V((0, 0, 1.0))),
    ("HumanoidRootNode", "Root", JV["Root"], JV["Root"] + V((0, 0, .5))),
    ("LowerTorso", "HumanoidRootNode", JV["Root"], JV["Waist"]),
    ("UpperTorso", "LowerTorso", JV["Waist"], JV["Neck"]),
    ("Head", "UpperTorso", JV["Neck"], V((0, 0, 6.40))),
]
for side in ("Right", "Left"):
    s = -1 if side == "Right" else 1
    BONES += [
        (side + "UpperArm", "UpperTorso", JV[side + "Shoulder"], JV[side + "Elbow"]),
        (side + "LowerArm", side + "UpperArm", JV[side + "Elbow"], JV[side + "Wrist"]),
        (side + "Hand", side + "LowerArm", JV[side + "Wrist"], JV[side + "Wrist"] + V((0, 0, -.68))),
        (side + "UpperLeg", "LowerTorso", JV[side + "Hip"], JV[side + "Knee"]),
        (side + "LowerLeg", side + "UpperLeg", JV[side + "Knee"], JV[side + "Ankle"]),
        (side + "Foot", side + "LowerLeg", JV[side + "Ankle"], foot_tail(side, s)),
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
    if pm.runtime == "Mug":
        continue
    ob = pm.obj
    vg = ob.vertex_groups.new(name=pm.runtime)
    vg.add([v.index for v in ob.data.vertices], 1.0, 'REPLACE')
    md = ob.modifiers.new("Armature", 'ARMATURE')
    md.object = ARM_OB
    ob.parent = ARM_OB
    ob.matrix_parent_inverse = Matrix.Identity(4)

# the mug is rigid to the RightHand bone: 100% weight on RightHand (single attachment route),
# placed at the neutral grip frame (the bind pose); the reference pose carries it to MUG_ORIGIN_REF
mug_ob = PARTS["Mug"].obj
mug_neutral_loc = JV["RightWrist"] + GRIP_LOCAL + MUG_FROM_GRIP
mug_ob.location = mug_neutral_loc
vgm = mug_ob.vertex_groups.new(name="RightHand")
vgm.add([v.index for v in mug_ob.data.vertices], 1.0, 'REPLACE')
mdm = mug_ob.modifiers.new("Armature", 'ARMATURE')
mdm.object = ARM_OB
mug_ob.parent = ARM_OB
mug_ob.matrix_parent_inverse = Matrix.Identity(4)


# ----------------------------------------------------------------------------------------------
# poses (display pose from the prompt's two-bone IK) and articulation tests
# ----------------------------------------------------------------------------------------------
def bone_rest(name):
    return ARM_OB.data.bones[name].matrix_local.copy()


PB = ARM_OB.pose.bones
ORDER = [b[0] for b in BONES]


def clear_pose():
    for pb in PB:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion((1, 0, 0, 0))
        pb.location = V((0, 0, 0))
        pb.scale = V((1, 1, 1))
    bpy.context.view_layer.update()


def pose_world(name, R3, pivot=None, extra_T=None):
    """Set a bone so that its rest matrix is rotated by R3 (world axes) about `pivot`
    (default: its head), on top of whatever its parent already does."""
    pb = PB[name]
    rest = bone_rest(name)
    piv = pivot if pivot is not None else rest.translation
    M = Matrix.Translation(piv) @ R3.to_4x4() @ Matrix.Translation(-piv) @ rest
    if extra_T is not None:
        M = Matrix.Translation(extra_T) @ M
    pb.matrix = M
    bpy.context.view_layer.update()


def rot3(axis, deg):
    return Matrix.Rotation(math.radians(deg), 3, axis)


def parent_eff(name):
    """Current world matrix of the parent's pose relative to its rest (transform applied to this bone's rest)."""
    par = ARM_OB.data.bones[name].parent
    if par is None:
        return Matrix.Identity(4)
    return PB[par.name].matrix @ bone_rest(par.name).inverted()


def fk(name, R3):
    """Rotate bone `name` by world-axis rotation R3 about its (already moved) head, composed with parents."""
    pb = PB[name]
    rest = bone_rest(name)
    pe = parent_eff(name)
    head = pe @ rest.translation
    M = Matrix.Translation(head) @ R3.to_4x4() @ Matrix.Translation(-head) @ pe @ rest
    pb.matrix = M
    bpy.context.view_layer.update()


L1 = (JV["RightElbow"] - JV["RightShoulder"]).length
L2 = (JV["RightWrist"] - JV["RightElbow"]).length
ELBOW_REF = solve_two_bone(JV["RightShoulder"], WRIST_TARGET, POLE, L1, L2)


def shortest_arc(a, b):
    return a.normalized().rotation_difference(b.normalized()).to_matrix()


def apply_reference_pose():
    clear_pose()
    S = JV["RightShoulder"]
    Ru = shortest_arc(JV["RightElbow"] - S, ELBOW_REF - S)
    fk("RightUpperArm", Ru)
    # lower arm: its rest axis is carried by the upper arm rotation
    a_l = Ru @ (JV["RightWrist"] - JV["RightElbow"])
    Rl = shortest_arc(a_l, WRIST_TARGET - ELBOW_REF)
    fk("RightLowerArm", Rl)
    # hand keeps its neutral orientation: pure translation to the wrist target
    pb = PB["RightHand"]
    rest = bone_rest("RightHand")
    pb.matrix = Matrix.Translation(WRIST_TARGET - JV["RightWrist"]) @ rest
    bpy.context.view_layer.update()
    # head display pose: ~8 deg tilt toward anatomical right, ~3 deg yaw toward the mug
    neck = JV["Neck"]
    R = rot3('Z', -3.0) @ rot3('Y', -8.0)
    pbh = PB["Head"]
    pe = parent_eff("Head")
    resth = bone_rest("Head")
    pbh.matrix = Matrix.Translation(neck) @ R.to_4x4() @ Matrix.Translation(-neck) @ pe @ resth
    bpy.context.view_layer.update()


# ----------------------------------------------------------------------------------------------
# cameras / light / render helpers
# ----------------------------------------------------------------------------------------------
world = bpy.data.worlds.new("RD_World")
SCENE.world = world
world.use_nodes = True
_wn = world.node_tree.nodes
_wl = world.node_tree.links
_bg_a = _wn["Background"]                       # ambient (what lights the model)
_bg_a.inputs[0].default_value = (0.85, 0.84, 0.82, 1.0)
_bg_a.inputs[1].default_value = 0.66
_bg_b = _wn.new("ShaderNodeBackground")         # what the camera sees (light studio grey, like the reference)
_bg_b.inputs[0].default_value = (0.80, 0.79, 0.76, 1.0)
_bg_b.inputs[1].default_value = 1.0
_lp = _wn.new("ShaderNodeLightPath")
_mix = _wn.new("ShaderNodeMixShader")
_wl.new(_lp.outputs["Is Camera Ray"], _mix.inputs[0])
_wl.new(_bg_a.outputs[0], _mix.inputs[1])
_wl.new(_bg_b.outputs[0], _mix.inputs[2])
_wl.new(_mix.outputs[0], _wn["World Output"].inputs["Surface"])
sun_d = bpy.data.lights.new("RD_Key", 'SUN')
sun_d.energy = 1.80
sun = bpy.data.objects.new("RD_Key", sun_d)
SCENE.collection.objects.link(sun)
sun.rotation_euler = (math.radians(52), math.radians(8), math.radians(-38))
fill_d = bpy.data.lights.new("RD_Fill", 'SUN')
fill_d.energy = 0.55
fill_d.use_shadow = False
fill = bpy.data.objects.new("RD_Fill", fill_d)
SCENE.collection.objects.link(fill)
fill.rotation_euler = (math.radians(60), 0, math.radians(140))
cam_d = bpy.data.cameras.new("RD_Cam")
CAM = bpy.data.objects.new("RD_Cam", cam_d)
SCENE.collection.objects.link(CAM)
SCENE.camera = CAM
SCENE.render.engine = 'BLENDER_EEVEE'
SCENE.eevee.taa_render_samples = 8 if QUICK else 32
SCENE.render.image_settings.file_format = 'PNG'
SCENE.view_settings.view_transform = 'Standard'
SCENE.render.film_transparent = False


def cam_look(loc, target, lens=70.0, ortho=None):
    CAM.location = V(loc)
    d = V(target) - V(loc)
    CAM.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if ortho:
        cam_d.type, cam_d.ortho_scale = 'ORTHO', ortho
    else:
        cam_d.type, cam_d.lens = 'PERSP', lens
    cam_d.sensor_width = 36.0


def orbit(target, dist, az_deg, el_deg):
    """az 0 = straight in front (camera at -D), positive az -> camera moves to +X (character's left)."""
    az, el = math.radians(az_deg), math.radians(el_deg)
    t = V(target)
    return t + V((dist * math.sin(az) * math.cos(el), -dist * math.cos(az) * math.cos(el), dist * math.sin(el)))


RENDERED = []


def shot(name, loc, target, res=(1000, 1000), lens=70.0, ortho=None, hide=(), show_only=None):
    for pm in PARTS.values():
        pm.obj.hide_render = (pm.runtime in hide) or (show_only is not None and pm.runtime not in show_only)
    SCENE.render.resolution_x, SCENE.render.resolution_y = res
    cam_look(loc, target, lens, ortho)
    SCENE.render.filepath = os.path.join(OUT, "previews", name)
    bpy.ops.render.render(write_still=True)
    RENDERED.append(name)
    print("RENDERED", name)


# ----------------------------------------------------------------------------------------------
# audits: bounds, counts, closure, orientation, cover checks
# ----------------------------------------------------------------------------------------------
def world_bounds(obs):
    lo = V((1e9, 1e9, 1e9))
    hi = V((-1e9, -1e9, -1e9))
    dg = bpy.context.evaluated_depsgraph_get()
    for o in obs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = ev.matrix_world
        for v in me.vertices:
            w = mw @ v.co
            lo = V((min(lo.x, w.x), min(lo.y, w.y), min(lo.z, w.z)))
            hi = V((max(hi.x, w.x), max(hi.y, w.y), max(hi.z, w.z)))
        ev.to_mesh_clear()
    return lo, hi


def key_pose(action_name):
    """Store the current pose bones as a one-frame action (editable pose source in the .blend)."""
    if ARM_OB.animation_data is None:
        ARM_OB.animation_data_create()
    act = bpy.data.actions.new(action_name)
    act.use_fake_user = True
    ARM_OB.animation_data.action = act
    for pb in PB:
        pb.keyframe_insert("location", frame=1)
        pb.keyframe_insert("rotation_quaternion", frame=1)
        pb.keyframe_insert("scale", frame=1)
    ARM_OB.animation_data.action = None


clear_pose()
key_pose("RegularDad_NeutralBind")
apply_reference_pose()
key_pose("RegularDad_ReferencePose")
clear_pose()
BODY = [PARTS[k].obj for k in PARTS if k != "Mug"]
lo, hi = world_bounds(BODY)
head_lo, head_hi = world_bounds([PARTS["Head"].obj])
ft_lo, ft_hi = world_bounds([PARTS["RightFoot"].obj, PARTS["LeftFoot"].obj])
mug_lo, mug_hi = world_bounds([PARTS["Mug"].obj])
body_tris = sum(tri_count_from_mesh for tri_count_from_mesh in
                (sum(len(p.vertices) - 2 for p in o.data.polygons) for o in BODY))
mug_tris = sum(len(p.vertices) - 2 for p in PARTS["Mug"].obj.data.polygons)
print("BOUNDS_NEUTRAL body", tuple(round(x, 3) for x in lo), tuple(round(x, 3) for x in hi))
print("HEAD", tuple(round(x, 3) for x in head_lo), tuple(round(x, 3) for x in head_hi))
print("FEET_H0", round(ft_lo.z, 4))
print("TRIS body", body_tris, "mug", mug_tris)


def check_closed(me):
    from collections import Counter
    cnt = Counter()
    for p in me.polygons:
        vs = p.vertices
        for a, b in zip(vs, list(vs[1:]) + [vs[0]]):
            cnt[(min(a, b), max(a, b))] += 1
    open_e = sum(1 for k, v in cnt.items() if v == 1)
    nm_e = sum(1 for k, v in cnt.items() if v > 2)
    return open_e, nm_e


AUDIT = {}
for pm in PARTS.values():
    me = pm.obj.data
    # shells are not welded across components, so edges are checked per mesh via position welding
    bmx = bmesh.new()
    bmx.from_mesh(me)
    bmesh.ops.remove_doubles(bmx, verts=bmx.verts, dist=1e-5)
    from collections import Counter
    cnt = Counter()
    for f in bmx.faces:
        vs = [v.index for v in f.verts]
        for a, b in zip(vs, vs[1:] + vs[:1]):
            cnt[(min(a, b), max(a, b))] += 1
    open_e = sum(1 for v in cnt.values() if v == 1)
    zero = sum(1 for f in bmx.faces if f.calc_area() < 1e-9)
    # signed volume per part (should be > 0 overall)
    vol = 0.0
    for f in bmx.faces:
        vv = [v.co for v in f.verts]
        for k in range(1, len(vv) - 1):
            vol += vv[0].dot(vv[k].cross(vv[k + 1])) / 6.0
    AUDIT[pm.runtime] = {"verts": len(me.vertices), "tris": sum(len(p.vertices) - 2 for p in me.polygons),
                         "open_edges": open_e, "zero_area": zero, "signed_volume": round(vol, 4)}
    bmx.free()

# ----------------------------------------------------------------------------------------------
# outputs: blend, FBX, spec JSON
# ----------------------------------------------------------------------------------------------
BLEND = os.path.join(OUT, "RegularDad_Redesign.blend")
FBX_BODY = os.path.join(OUT, "RegularDad_R15.fbx")
FBX_MUG = os.path.join(OUT, "RegularDad_Mug.fbx")
FBX_SET = dict(use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y',
               mesh_smooth_type='FACE', use_mesh_modifiers=True, bake_anim=False, add_leaf_bones=False,
               path_mode='COPY', embed_textures=True, use_armature_deform_only=False, primary_bone_axis='Y', secondary_bone_axis='X')


def export_fbx(path, objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, object_types={'MESH', 'ARMATURE'}, **FBX_SET)


def do_exports():
    clear_pose()
    for pm in PARTS.values():
        pm.obj.hide_render = False
    export_fbx(FBX_BODY, [ARM_OB] + [PARTS[k].obj for k in PARTS if k != "Mug"])
    # mug-only FBX: an unskinned copy in the reference position (mug-local origin = underside centre)
    cp = bpy.data.objects.new("Mug_Geo", mug_ob.data.copy())
    cp.data.name = "Mug_Geo_export"
    EXP_COLL.objects.link(cp)
    cp.location = MUG_ORIGIN_REF
    export_fbx(FBX_MUG, [cp])
    bpy.data.objects.remove(cp, do_unlink=True)


do_exports()
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("EXPORTED", FBX_BODY, FBX_MUG, BLEND)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for ch in iter(lambda: fh.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


# palette uv map json
uvmap = {"atlas": "RegularDad_Palette.png", "size": [ATLAS_W, ATLAS_H], "tile_px": TILE_PX, "columns": COLS,
         "inset_px": INSET, "row0_is_top_of_png": True, "tiles": []}
for i, (n_, h_, use) in enumerate(PAL):
    u0, v0, u1, v1 = tile_uv_patch(i)
    uvmap["tiles"].append({"index": i, "name": n_, "hex": h_, "use": use, "col": i % COLS, "row": i // COLS,
                           "uv_patch": [u0, v0, u1, v1],
                           "pixel_rect": [(i % COLS) * TILE_PX + INSET, (i // COLS) * TILE_PX + INSET,
                                          (i % COLS) * TILE_PX + TILE_PX - INSET, (i // COLS) * TILE_PX + TILE_PX - INSET]})
json.dump(uvmap, open(os.path.join(OUT, "RegularDad_Palette_UVMap.json"), "w"), indent=1)

RESULT = {
    "bounds_neutral": {"min": list(lo), "max": list(hi), "height": hi.z - lo.z},
    "head_bounds": {"min": list(head_lo), "max": list(head_hi)},
    "ear_to_ear": head_hi.x - head_lo.x,
    "feet_min_h": ft_lo.z,
    "tris_body": body_tris, "tris_mug": mug_tris,
    "audit": AUDIT,
    "elbow_ref": list(ELBOW_REF),
    "wrist_target": list(WRIST_TARGET),
    "mug_origin_ref": list(MUG_ORIGIN_REF),
    "L1": L1, "L2": L2,
    "ik_check": {"|S-E|": (ELBOW_REF - JV["RightShoulder"]).length, "|E-W|": (WRIST_TARGET - ELBOW_REF).length},
}
json.dump(RESULT, open(os.path.join(OUT, "_build_result.json"), "w"), indent=1)
json.dump(COMP_LOG, open(os.path.join(OUT, "_component_log.json"), "w"), indent=1)
print("RESULT", json.dumps({k: RESULT[k] for k in ("bounds_neutral", "tris_body", "tris_mug", "ik_check")}))

if NORENDER:
    sys.exit(0)

# ----------------------------------------------------------------------------------------------
# renders
# ----------------------------------------------------------------------------------------------
cx_body = V((0, 0, 3.2))
R_ALL = (1000, 1000)
apply_reference_pose()
SCENE.render.film_transparent = False
shot("01_ref_front34.png", orbit((-.4, 0, 3.0), 17.0, 24, 8), (-.4, 0, 3.0), res=(768, 790), lens=75)
shot("02_front.png", orbit((0, 0, 3.2), 18, 0, 4), (0, 0, 3.2), res=(900, 1000), lens=70)
shot("03_back.png", orbit((0, 0, 3.2), 18, 180, 4), (0, 0, 3.2), res=(900, 1000), lens=70)
shot("04_right_profile_mug_side.png", orbit((0, 0, 3.2), 18, -90, 4), (0, 0, 3.2), res=(900, 1000), lens=70)
shot("05_left_profile.png", orbit((0, 0, 3.2), 18, 90, 4), (0, 0, 3.2), res=(900, 1000), lens=70)
shot("06_back34.png", orbit((0, 0, 3.2), 18, 150, 10), (0, 0, 3.2), res=(900, 1000), lens=70)
shot("07_head_front.png", orbit((0, -.2, 5.55), 6.0, 0, 2), (0, -.2, 5.55), res=(900, 900), lens=70)
shot("08_head_34.png", orbit((0, -.2, 5.55), 6.0, 30, 6), (0, -.2, 5.55), res=(900, 900), lens=70)
shot("09_head_profile.png", orbit((0, 0, 5.5), 6.0, -90, 2), (0, 0, 5.5), res=(900, 900), lens=70)
shot("10_grip_front.png", orbit(V((-2.2, -1.2, 3.3)), 5.0, 0, 6), (-2.2, -1.2, 3.3), res=(900, 900), lens=70)
shot("11_grip_side.png", orbit(V((-2.2, -1.2, 3.3)), 5.0, -90, 6), (-2.2, -1.2, 3.3), res=(900, 900), lens=70)
shot("12_grip_top.png", orbit(V((-2.2, -1.2, 3.3)), 5.0, 0, 80), (-2.2, -1.2, 3.3), res=(900, 900), lens=70)
shot("13_belt_buckle.png", orbit((0, -.9, 2.35), 3.5, 0, 6), (0, -.9, 2.35), res=(900, 700), lens=70)
shot("14_collar_button.png", orbit((0, -.7, 4.4), 3.5, 0, 6), (0, -.7, 4.4), res=(900, 700), lens=70)
shot("15_shoes_cuffs.png", orbit((0, -.3, .7), 6.0, 20, 14), (0, -.3, .7), res=(1000, 700), lens=70)
clear_pose()
shot("16_bind_front.png", orbit((0, 0, 3.2), 18, 0, 3), (0, 0, 3.2), res=(900, 1000), lens=70, hide=())
shot("17_bind_side.png", orbit((0, 0, 3.2), 18, -90, 3), (0, 0, 3.2), res=(900, 1000), lens=70)
# mug isolated views (reference pose puts the skinned mug at MUG_ORIGIN_REF)
apply_reference_pose()
for nm, az, el in (("18_mug_front", 0, 8), ("19_mug_handle_side", -90, 8), ("20_mug_top", 0, 85), ("21_mug_under", 0, -80)):
    shot(nm + ".png", orbit(MUG_ORIGIN_REF + V((-.2, 0, .55)), 3.0, az, el), MUG_ORIGIN_REF + V((-.2, 0, .55)),
         res=(800, 800), lens=70, show_only=("Mug",))
# 256 px recognition renders
apply_reference_pose()
shot("22_gate_full_256x256tall.png", orbit((-.4, 0, 3.2), 20, 22, 6), (-.4, 0, 3.2), res=(256, 256), lens=70)
shot("23_gate_head_mug_256.png", orbit((-1.2, -.6, 4.4), 7.5, 20, 8), (-1.2, -.6, 4.4), res=(256, 256), lens=70)
# native-resolution crop match
shot("24_native_384x395.png", orbit((-.4, 0, 3.0), 17.0, 24, 8), (-.4, 0, 3.0), res=(384, 395), lens=75)
print("ALL_RENDERS_DONE", len(RENDERED))


# ----------------------------------------------------------------------------------------------
# articulation tests (Blender-only evidence): FK poses on the real rig + joint-cover checks
# ----------------------------------------------------------------------------------------------
def inside_mesh(ob, p):
    """Ray-parity point-in-mesh test on the evaluated object (3 axes, majority) + nearest distance."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    bmx = bmesh.new()
    bmx.from_mesh(me)
    bmx.transform(ev.matrix_world)
    ev.to_mesh_clear()
    bvh = BVHTree.FromBMesh(bmx)
    votes = 0
    for d in (V((1, 0.0137, 0.0071)), V((0.0071, 1, 0.0137)), V((0.0137, 0.0071, 1)),
              V((-1, 0.0113, 0.0059)), V((0.0059, -1, 0.0113)), V((0.0113, 0.0059, -1))):
        # union of closed outward-oriented shells: if the FIRST surface hit faces away from the ray, the point is inside
        loc, nrm, idx, dist = bvh.ray_cast(V(p), d)
        if loc is not None and nrm.dot(d) > 0:
            votes += 1
    near = bvh.find_nearest(V(p))[3]
    bmx.free()
    return votes >= 4, (near if near is not None else 9e9)


JOINT_TABLE = [  # (joint name, parent part, child part, bone whose head is the joint)
    ("Root", "HumanoidRootPart", "LowerTorso", "LowerTorso"),
    ("Waist", "LowerTorso", "UpperTorso", "UpperTorso"),
    ("Neck", "UpperTorso", "Head", "Head"),
    ("RightShoulder", "UpperTorso", "RightUpperArm", "RightUpperArm"),
    ("RightElbow", "RightUpperArm", "RightLowerArm", "RightLowerArm"),
    ("RightWrist", "RightLowerArm", "RightHand", "RightHand"),
    ("LeftShoulder", "UpperTorso", "LeftUpperArm", "LeftUpperArm"),
    ("LeftElbow", "LeftUpperArm", "LeftLowerArm", "LeftLowerArm"),
    ("LeftWrist", "LeftLowerArm", "LeftHand", "LeftHand"),
    ("RightHip", "LowerTorso", "RightUpperLeg", "RightUpperLeg"),
    ("RightKnee", "RightUpperLeg", "RightLowerLeg", "RightLowerLeg"),
    ("RightAnkle", "RightLowerLeg", "RightFoot", "RightFoot"),
    ("LeftHip", "LowerTorso", "LeftUpperLeg", "LeftUpperLeg"),
    ("LeftKnee", "LeftUpperLeg", "LeftLowerLeg", "LeftLowerLeg"),
    ("LeftAnkle", "LeftLowerLeg", "LeftFoot", "LeftFoot"),
]


def _world_bvh(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    bmx = bmesh.new()
    bmx.from_mesh(me)
    bmx.transform(ev.matrix_world)
    ev.to_mesh_clear()
    bvh = BVHTree.FromBMesh(bmx)
    pts = [v.co.copy() for v in bmx.verts]
    bmx.free()
    return bvh, pts


def _inside_union(bvh, p):
    """Point inside a union of closed outward shells: the first surface hit faces away from the ray (2 rays)."""
    n = 0
    for d in (V((0.0137, 0.0071, 1)), V((0.0113, 0.0059, -1))):
        loc, nrm, idx, dist = bvh.ray_cast(p, d)
        if loc is not None and nrm.dot(d) > 0:
            n += 1
    return n == 2


def cover_report():
    """For every joint: do the two adjacent parts interpenetrate (or touch within .01) after posing?"""
    bpy.context.view_layer.update()
    rep = []
    cache = {}
    for jn, par, ch, bone in JOINT_TABLE:
        head_w = ARM_OB.matrix_world @ PB[bone].head
        row = {"joint": jn, "pivot_world": [round(c, 4) for c in head_w]}
        if par == "HumanoidRootPart":
            row.update({"child_verts_inside_parent": None, "parent_verts_inside_child": None, "min_gap": None,
                        "covered": True, "note": "HumanoidRootPart is an invisible helper (no mesh)"})
            rep.append(row)
            continue
        for part in (par, ch):
            if part not in cache:
                cache[part] = _world_bvh(PARTS[part].obj)
        bp, pp_ = cache[par]
        bc, pc_ = cache[ch]
        n_c_in_p = sum(1 for p in pc_ if _inside_union(bp, p))
        n_p_in_c = sum(1 for p in pp_ if _inside_union(bc, p))
        mind = min((bp.find_nearest(p)[3] or 9e9) for p in pc_)
        row.update({"child_verts_inside_parent": n_c_in_p, "parent_verts_inside_child": n_p_in_c,
                    "min_gap": round(mind, 4)})
        row["covered"] = bool(n_c_in_p > 0 or n_p_in_c > 0 or mind < 0.01)
        rep.append(row)
    return rep


ARTIC = {}


def pose_A():   # shoulders, elbows, waist, neck
    fk("UpperTorso", rot3('Z', 12.0))
    fk("Head", rot3('Z', -10.0))
    fk("RightUpperArm", rot3('X', -70.0))
    fk("RightLowerArm", rot3('X', -90.0))
    fk("LeftUpperArm", rot3('Y', -60.0))
    fk("LeftLowerArm", rot3('Y', -30.0))


def pose_B():   # hip swing 35, knee 60, ankle 20 (a mid-stride)
    fk("RightUpperLeg", rot3('X', -35.0))
    fk("RightLowerLeg", rot3('X', 10.0))
    fk("RightFoot", rot3('X', -20.0))
    fk("LeftUpperLeg", rot3('X', 35.0))
    fk("LeftLowerLeg", rot3('X', 60.0))
    fk("LeftFoot", rot3('X', 20.0))
    fk("RightUpperArm", rot3('X', 30.0))
    fk("LeftUpperArm", rot3('X', -30.0))


def pose_C():   # wrist rotation + 90 deg elbows
    fk("RightUpperArm", rot3('X', -30.0))
    fk("RightLowerArm", rot3('X', -90.0))
    fk("RightHand", Matrix.Rotation(math.radians(60.0), 3, V((0, -1, 0))))
    fk("LeftUpperArm", rot3('X', -30.0))
    fk("LeftLowerArm", rot3('X', -90.0))
    fk("LeftHand", Matrix.Rotation(math.radians(-45.0), 3, V((0, -1, 0))))


for nm, fn in (("A_shoulders_elbows_waist_neck", pose_A), ("B_hips_knees_ankles", pose_B), ("C_wrist_rotation_elbows", pose_C)):
    clear_pose()
    fn()
    ARTIC[nm] = cover_report()
clear_pose()
ARTIC_SUMMARY = {k: {"joints": len(v), "covered": sum(1 for r in v if r["covered"]),
                     "uncovered": [r["joint"] for r in v if not r["covered"]]} for k, v in ARTIC.items()}
print("ARTIC", json.dumps(ARTIC_SUMMARY))

if not NORENDER:
    for nm, fn, az, el, tgt in (("25_artic_A_arms.png", pose_A, 28, 8, (0, 0, 3.3)),
                                ("26_artic_B_legs.png", pose_B, -70, 6, (0, 0, 3.0)),
                                ("27_artic_C_wrists.png", pose_C, 20, 10, (0, 0, 3.3))):
        clear_pose()
        fn()
        shot(nm, orbit(tgt, 19, az, el), tgt, res=(900, 1000), lens=70)
    clear_pose()


# ----------------------------------------------------------------------------------------------
# machine-readable records
# ----------------------------------------------------------------------------------------------
def r3(v):
    return [round(float(c), 4) for c in v]


def roblox_pos(p):
    """logical (X,D,H) -> Roblox (-X, H, D)"""
    return [round(-p[0], 4), round(p[2], 4), round(p[1], 4)]


BONE_TABLE = []
for name, parent, head, tail in BONES:
    BONE_TABLE.append({"name": name, "parent": parent, "head_logical": r3(head), "tail_logical": r3(tail),
                       "length": round((tail - head).length, 4), "head_roblox": roblox_pos(head)})

RIG = {
    "asset": "RegularDad_Redesign",
    "tested_where": {"blender_fk": "yes (3 pose sets, joint-cover check)",
                     "studio_rig": "see Studio_Review/IMPORT_VERIFICATION_RU.md",
                     "runtime_movement": "see Studio_Review/IMPORT_VERIFICATION_RU.md"},
    "frame": {"logical": "(X,D,H): forward=-D, up=H, anatomical RIGHT=-X",
              "blender": "(x,y,z)=(X,D,H)", "fbx_axes": {"forward": "Z", "up": "Y"},
              "roblox_position": "(-X, H, D); character faces -Z; anatomical right = +X"},
    "runtime_parts": [k for k in PARTS if k != "Mug"],
    "mug": {"object": "Mug_Geo", "weight": "RightHand 100%", "mug_origin_reference_pose": r3(MUG_ORIGIN_REF),
            "mug_origin_neutral": r3(mug_neutral_loc), "grip_local_to_wrist": r3(GRIP_LOCAL),
            "grip_target": r3(GRIP_TARGET), "mug_from_grip": r3(MUG_FROM_GRIP),
            "handle_grasp_segment_mug_local": [-.87, 0, .55],
            "attachment_route": "one rigid route: Motor6D/weld to RightHand only (no Tool RightGrip, no weld to torso/world)"},
    "bones": BONE_TABLE,
    "joints": [{"joint": jn, "parent_part": par, "child_part": ch,
                "pivot_logical": r3(JV[jn]) if jn in JV else None,
                "pivot_roblox": roblox_pos(JV[jn]) if jn in JV else None,
                "class_planned": "Motor6D (C0=Part0.CFrame^-1*J, C1=Part1.CFrame^-1*J)"} for jn, par, ch, _ in JOINT_TABLE],
    "ik": {"S": r3(JV["RightShoulder"]), "W": r3(WRIST_TARGET), "P": r3(POLE), "L1": round(L1, 6), "L2": round(L2, 6),
           "elbow_E": r3(ELBOW_REF), "check_S_E": round((ELBOW_REF - JV["RightShoulder"]).length, 6),
           "check_E_W": round((WRIST_TARGET - ELBOW_REF).length, 6)},
    "display_pose": {"head_tilt_deg": -8.0, "head_yaw_deg": -3.0,
                     "note": "applied on the Head bone only; the neutral bind is untouched"},
    "weights": "every vertex of a part is 100% on its own bone (rigid segmented style); Root/HumanoidRootNode are non-deforming helpers",
    "toe_out_deg": {"Right": -6.0, "Left": 6.0},
    "articulation_tests_blender": ARTIC_SUMMARY,
    "articulation_detail": ARTIC,
}
json.dump(RIG, open(os.path.join(OUT, "rig_manifest.json"), "w"), indent=1)

SPEC = {
    "asset": "RegularDad_Redesign", "character": "Regular Dad (01, Common)", "units": "studs",
    "neutral_height": 6.40, "built_height": round(hi.z - lo.z, 4),
    "tables": {"UpperTorso": UT_ROWS, "LowerTorso": LT_ROWS, "Head": HEAD_ROWS, "ShoeUpper": SHOE_ROWS, "Nose": NOSE_ROWS,
               "MugOuter": MUG_OUT, "MugInner": MUG_IN, "HandleCenterline": HANDLE_PTS},
    "joints": {k: list(v) for k, v in JOINTS.items()},
    "upper_arm_sections": [(0, .82, .78), (.15, .94, .88), (.70, .88, .82), (1.0, .78, .76)],
    "lower_arm_sections": [(0, .78, .76), (.5, .80, .75), (1.0, .76, .70)],
    "upper_leg_sections": UPPER_SEC, "lower_leg_sections": LOWER_SEC,
    "palette": [{"index": i, "name": n_, "hex": h_, "use": u_} for i, (n_, h_, u_) in enumerate(PAL)],
    "atlas": {"size": [ATLAS_W, ATLAS_H], "tile_px": TILE_PX, "columns": COLS, "inset_px": INSET},
    "counts": {"body_tris": body_tris, "mug_tris": mug_tris, "body_budget": 9000, "mug_budget": 900},
    "deviations_from_prompt": [
        "Palette tiles 24-27 are DERIVED shades the prompt text asks for (belt top edge lighter, mouth crease +20%, coffee meniscus -8%, hem -5%); the remaining tiles are ivory.",
        "Eye whites stand .025 proud with the back embedded .01 into the shell (the prescribed .012 thickness would float off the face).",
        "Eyebrow depth .15 instead of .12: the front stays at f-.135 and the back is embedded .015 so the brow is attached.",
        "Nostril hints are fitted to the actual bulb front surface (the prescribed D-1.015 lies inside the bulb).",
        "Collar-fold bevel .015 and the two .015 button holes were not modelled (below visible size).",
        "Heel block is 1.20 wide so that it reads as a dark heel band outside the upper.",
        "Arm sleeve rings use the larger of the sleeve and skin widths (they disagree by up to .02 in the prompt); the skin ring is buried under the cuff band.",
        "The head display pose and the held-mug pose live on pose bones; the exported bind is the neutral I-pose.",
        "Joint overlaps: skin of the upper arm and thigh extend .02 past the elbow/knee, the forearm .02 into the hand.",
        "Normal-dependent skin/teal/denim facet colours are baked from the NEUTRAL pose normals; in the reference pose a few facets keep the neutral shading.",
    ],
    "measured": RESULT,
}
json.dump(SPEC, open(os.path.join(OUT, "construction_spec.json"), "w"), indent=1)

REG = {"asset": "RegularDad_Redesign", "components": COMP_LOG,
       "part_totals": {k: {"components": len(v.comps), "tris": AUDIT[k]["tris"], "verts": AUDIT[k]["verts"]} for k, v in PARTS.items()},
       "mesh_names": {k: v.geo for k, v in PARTS.items()},
       "classification_legend": {
           "observed+prescribed": "visible in the crop and given numerically by the prompt",
           "inferred": "hidden side / underside completion (rear hair band, rear pockets, rear belt loops, sole underside)"}}
json.dump(REG, open(os.path.join(OUT, "component_registry.json"), "w"), indent=1)
print("RECORDS_WRITTEN", len(COMP_LOG))
