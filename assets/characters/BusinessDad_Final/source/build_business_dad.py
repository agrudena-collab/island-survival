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
# ---- generic helpers (identical to the Regular/Office Dad builders: bmesh solids, lofts, rings, strips) ----
# ---- helpers (shared with the Regular Dad builder) ----
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
               "faces": n_faces, "tris": sum(len(f.verts) - 2 for f in bm.faces),
               "open_edges": sum(1 for e in bm.edges if e.is_boundary), "nonmanifold_edges": sum(1 for e in bm.edges if len(e.link_faces) > 2)}
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


def front_strip(pm, cid, x0, x1, hs, out, embed, tile, ffn=None, rear=False, meta=None):
    """Strip hugging a surface: hs = [h] or [(h, out)]; ffn(x,h)->surface D; rear=True offsets towards +D."""
    ffn = ffn or tfront_default
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
# ----------------------------------------------------------------------------------------------
# containers, coordinate helpers, shading rules, parameters, joints
# ----------------------------------------------------------------------------------------------
PARTS = {}
COMP_LOG = []
SRC_COLL = bpy.data.collections.new("SOURCE_Components")
SCENE.collection.children.link(SRC_COLL)
EXP_COLL = bpy.data.collections.new("EXPORT_BusinessDad")
SCENE.collection.children.link(EXP_COLL)
HEXOF = {n: h for n, h, _ in PAL}


def Bl(x, f, h):
    """logical (X, F, H) -> Blender point (X, -F, H)."""
    return V((x, -f, h))


def sh_const(name):
    return lambda n, c: name


def shade(base, hi=0.55, lo=-0.55):
    """light from above: base+'Light' on up faces, base+'Shadow' on down faces (only if the tile exists)."""
    up, dn = base + "Light", base + "Shadow"

    def fn(n, c):
        if n.z > hi and up in TILE:
            return up
        if n.z < lo and dn in TILE:
            return dn
        return base
    return fn


sh_skin = shade("Skin")
sh_navy = shade("Navy")
sh_trouser = shade("Trouser")
sh_hair = shade("Hair")
sh_shoe = shade("Shoe")
sh_tie = shade("Tie")
sh_gold = shade("Gold")
sh_silver = shade("Silver")
sh_shirt = shade("Shirt", hi=2.0)


def sh_skin_arm(n, c):
    if n.z > 0.55:
        return "SkinLight"
    if n.z < -0.55:
        return "SkinShadow"
    return "Skin"


def sh_nose(n, c):
    if n.z < -0.55:
        return "SkinShadow"
    if n.z > 0.45:
        return "NoseLight"
    return "Nose"


def sh_sole(n, c):
    return "SoleLight" if n.z > 0.6 else "Sole"


# ---------------------------------------------------------------------------------------------------------------------------
# PARAMETERS. Values were derived from the reference crop (63.6 px per stud: hair top y13 .. sole y420 = 6.40 studs, body axis x192) -
# see data/reference_measurements.json; hidden surfaces are coherent extrapolation.
# ---------------------------------------------------------------------------------------------------------------------------
L1, L2 = 1.30, 1.18          # revision 5: shorter, chunkier arms (turnaround); the same for both arms
RHINT = (-0.5, -0.45, -0.1)
LHINT = (0.5, -0.3, -1.0)
JOINTS = {
    "Root": (0, 0, 2.40), "Waist": (0, 0, 2.88), "Neck": (0, 0, 4.60),
    "RightShoulder": (-1.22, 0, 4.18), "RightWrist": (-1.80, 0.05, 2.72),
    "LeftShoulder": (1.22, 0, 4.18), "LeftWrist": (1.95, 0.95, 3.60),
    "RightHip": (-0.80, 0, 2.30), "LeftHip": (0.80, 0, 2.30),
    "RightKnee": (-0.80, 0.02, 1.40), "LeftKnee": (0.80, 0.02, 1.40),
    "RightAnkle": (-0.80, 0.02, 0.72), "LeftAnkle": (0.80, 0.02, 0.72),
}   # revision 5: body proportions re-measured on the turnaround FRONT view (shoulder line H4.45, chin H4.55, crotch H2.25, torso ~2.6-3.0 wide, legs 1.36 each)


def ik_elbow(S, W, L1, L2, hint):
    S, W, hint = V(S), V(W), V(hint)
    dv = W - S
    d = dv.length
    u = dv / d
    a = (L1 ** 2 - L2 ** 2 + d ** 2) / (2 * d)
    h = math.sqrt(max(L1 ** 2 - a ** 2, 0.0))
    n = (hint - u * hint.dot(u)).normalized()
    return tuple(S + u * a + n * h)


JOINTS["RightElbow"] = ik_elbow(JOINTS["RightShoulder"], JOINTS["RightWrist"], L1, L2, RHINT)
JOINTS["LeftElbow"] = ik_elbow(JOINTS["LeftShoulder"], JOINTS["LeftWrist"], L1, L2, LHINT)
JV = {k: Bl(*v) for k, v in JOINTS.items()}
HEAD_TOP = 6.40


LT_SX = 1.0                                   # LowerTorso width factor (the jacket skirt must cover the trouser tops)


def xf_ut(p):
    """UpperTorso is authored in the old coordinates (shoulder line H4.86); revision 5 compresses it to the turnaround proportions (shoulder line H4.45, narrower)"""
    p = V(p)
    return V((p.x * .87, p.y * .95, 2.88 + (p.z - 2.88) * .785))


def xf_lt(p):
    """LowerTorso: crotch H1.93 -> 2.25, belt/hem compressed accordingly; the skirt is wide enough to cover the trouser tops (revision 6)"""
    p = V(p)
    return V((p.x * LT_SX, p.y * .95, 2.25 + (p.z - 1.93) * .663))


def xf_head(p):
    """Head: ~12% taller (chin at H4.55, top stays at H6.40) and ~10% narrower"""
    p = V(p)
    return V((p.x * .90, p.y, 6.40 - (6.40 - p.z) * 1.12))
RHAND_DIR = V((0.97, 0.14, -0.05)).normalized()     # revision 6: the right hand points horizontally into the jacket pocket tunnel (fist stays inside the skirt)

# torso rows (H, W, Ffront, Fback signed, bevel); D coordinates (front negative)
_TORSO = [(2.20, 3.10, .76, -.68, .13), (2.50, 2.98, .74, -.68, .13), (2.86, 3.02, .76, -.70, .14), (3.40, 3.26, .82, -.72, .16),
          (4.00, 3.36, .80, -.72, .17), (4.50, 3.20, .70, -.66, .16), (4.86, 2.90, .58, -.60, .14)]
TORSO = [(h, w, -ff, -fb, c) for h, w, ff, fb, c in _TORSO]
TORSO_TOP = TORSO[-1][0]
TORSO_BOT = TORSO[0][0]
LOWER_ROWS = [r for r in TORSO if r[0] <= 2.86 + 1e-9]
UPPER_ROWS = [r for r in TORSO if r[0] >= 2.86 - 1e-9]


def torso_row_at(h):
    return (h,) + tuple(interp_row(TORSO, h))


def tfront(x, h):
    return front_at(TORSO, min(max(h, TORSO_BOT), TORSO_TOP), x)


def tback(x, h):
    return back_at(TORSO, min(max(h, TORSO_BOT), TORSO_TOP), x)


def cap_tris2(idxs, pts2d):
    tris = mgeo.tessellate_polygon([[V((p[0], p[1], 0.0)) for p in pts2d]])
    return [[idxs[a], idxs[b], idxs[c]] for a, b, c in tris]


def loft_bm(rings, tilefn, caps=(True, True)):
    n = len(rings[0])
    P = [p for r in rings for p in r]
    bm = make_bm_solid(P, loft_faces(len(rings), n, caps))
    tl = bm.faces.layers.int.get("tile") or bm.faces.layers.int.new("tile")
    for f in bm.faces:
        f.normal_update()
        f[tl] = TILE[tilefn(f.normal.copy(), f.calc_center_median())]
    return bm


def bm_boolean(bm, cutter, op='DIFFERENCE'):
    a = bm_to_obj(bm, "tmp_a")
    b = bm_to_obj(cutter, "tmp_b")
    bool_apply(a, b, op)
    res = obj_to_bm(a)
    bpy.data.objects.remove(a, do_unlink=True)
    bpy.data.objects.remove(b, do_unlink=True)
    return res


def prism_xh(pm, cid, poly_xh, f0, f1, tilefn, meta=None):
    """polygon in (X, H) swept between logical F=f0 (rear) and F=f1 (front)."""
    n = len(poly_xh)
    P = [Bl(x, f0, h) for x, h in poly_xh] + [Bl(x, f1, h) for x, h in poly_xh]
    faces = [[k, (k + 1) % n, n + (k + 1) % n, n + k] for k in range(n)]
    faces += cap_tris2(list(range(n)), poly_xh) + cap_tris2(list(range(n, 2 * n)), poly_xh)
    pm.solid(cid, P, faces, tilefn, meta)


def prism_bm(poly_xh, f0, f1, tile):
    n = len(poly_xh)
    P = [Bl(x, f0, h) for x, h in poly_xh] + [Bl(x, f1, h) for x, h in poly_xh]
    faces = [[k, (k + 1) % n, n + (k + 1) % n, n + k] for k in range(n)]
    faces += cap_tris2(list(range(n)), poly_xh) + cap_tris2(list(range(n, 2 * n)), poly_xh)
    return solid_tiled(P, faces, tile)


def plate_bm(outline, fit, layers, tile):
    """closed plate following a surface: layers=[(dD, sx, sh)], first layer = back; used as boolean cutter."""
    cx = sum(p[0] for p in outline) / len(outline)
    ch = sum(p[1] for p in outline) / len(outline)
    n = len(outline)
    P = []
    for dD, sx, sh in layers:
        for x, h in outline:
            xx, hh = cx + (x - cx) * sx, ch + (h - ch) * sh
            P.append(V((xx, fit(xx, hh) + dD, hh)))
    faces = []
    for i in range(len(layers) - 1):
        for k in range(n):
            faces.append([i * n + k, i * n + (k + 1) % n, (i + 1) * n + (k + 1) % n, (i + 1) * n + k])
    faces += cap_tris(P, list(range(n)))
    faces += cap_tris(P, list(range((len(layers) - 1) * n, len(layers) * n)))
    return solid_tiled(P, faces, tile)


def patch_box(pm, cid, cx, fc, hc, w, d, hh, tile, embed=0.03, meta=None):
    solid_box(pm, cid, cx - w / 2, cx + w / 2, -(fc + d / 2), -(fc - d / 2) + embed, hc - hh / 2, hc + hh / 2, tile, meta)


def cyl_y(pm, cid, cx, cz, y0, y1, r, segs, tilefn, meta=None):
    """cylinder along Blender Y (the character's front/back axis) between y0 and y1."""
    def ring(y):
        return [V((cx + r * math.cos(2 * math.pi * k / segs), y, cz + r * math.sin(2 * math.pi * k / segs))) for k in range(segs)]
    loft(pm, cid, [ring(y0), ring(y1)], tilefn, meta=meta)


def cyl_x(pm, cid, cx, cy, cz, length, r, segs, tilefn, ch=0.0, meta=None):
    x0, x1 = cx - length / 2, cx + length / 2

    def ring(x, rr):
        return [V((x, cy + rr * math.cos(2 * math.pi * k / segs), cz + rr * math.sin(2 * math.pi * k / segs))) for k in range(segs)]
    if ch > 0:
        rings = [ring(x0, r - ch), ring(x0 + ch, r), ring(x1 - ch, r), ring(x1, r - ch)]
    else:
        rings = [ring(x0, r), ring(x1, r)]
    loft(pm, cid, rings, tilefn, meta=meta)


def rot_xf(pivot, deg, axis='Z'):
    m = Matrix.Rotation(math.radians(deg), 3, axis)
    pv = V(pivot)
    return lambda p: pv + m @ (V(p) - pv)


def ellipse(cx, cz, rx, rz, n=14, rot=0.0):
    c, s = math.cos(rot), math.sin(rot)
    return [(cx + rx * math.cos(2 * math.pi * k / n) * c - rz * math.sin(2 * math.pi * k / n) * s,
             cz + rx * math.cos(2 * math.pi * k / n) * s + rz * math.sin(2 * math.pi * k / n) * c) for k in range(n)]


class AxisG:
    """Limb frame: L from the proximal to the distal point, U = world X projected across L (width), W = A x U (depth)."""

    def __init__(self, P0, P1):
        self.P0, self.P1 = V(P0), V(P1)
        d = self.P1 - self.P0
        self.L = d.length
        self.A = d / self.L
        u = V((1, 0, 0)) - self.A * V((1, 0, 0)).dot(self.A)
        if u.length < 0.3:
            u = V((0, -1, 0)) - self.A * V((0, -1, 0)).dot(self.A)
        self.U = u.normalized()
        self.W = self.A.cross(self.U).normalized()

    def at(self, t):
        return self.P0 + self.A * (self.L * t)

    def corners(self, w, d, c):
        a, b = w / 2.0, d / 2.0
        c = min(c, a - 1e-4, b - 1e-4)
        return [(-a + c, -b), (a - c, -b), (a, -b + c), (a, b - c), (a - c, b), (-a + c, b), (-a, b - c), (-a, -b + c)]

    def ring(self, t, w, d, c, ox=0.0, oy=0.0):
        P = self.at(t)
        return [P + self.U * (x + ox) + self.W * (y + oy) for x, y in self.corners(w, d, c)]

    def pt(self, t, x, y):
        return self.at(t) + self.U * x + self.W * y


def abox(pm, cid, ax, t0, t1, x0, x1, y0, y1, tile, meta=None):
    """box in the limb frame: t along the axis (fraction of L), x across U, y across W."""
    r0 = [ax.pt(t0, x0, y0), ax.pt(t0, x1, y0), ax.pt(t0, x1, y1), ax.pt(t0, x0, y1)]
    r1 = [ax.pt(t1, x0, y0), ax.pt(t1, x1, y0), ax.pt(t1, x1, y1), ax.pt(t1, x0, y1)]
    loft(pm, cid, [r0, r1], tile, meta=meta)


def sweep(pm, cid, path, wfn, hfn, c, tilefn, meta=None):
    """tube with an octagon section along a path (Blender points); wfn/hfn(t) -> width/height; up reference = world Z."""
    n = len(path)
    rings = []
    for i, p in enumerate(path):
        tg = (path[min(i + 1, n - 1)] - path[max(i - 1, 0)]).normalized()
        side = tg.cross(V((0, 0, 1)))
        if side.length < 1e-4:
            side = V((1, 0, 0))
        side.normalize()
        up = side.cross(tg).normalized()
        t = i / (n - 1)
        a, b = wfn(t) / 2.0, hfn(t) / 2.0
        cc = min(c, a - 1e-4, b - 1e-4)
        pts = [(-a + cc, -b), (a - cc, -b), (a, -b + cc), (a, b - cc), (a - cc, b), (-a + cc, b), (-a, b - cc), (-a, -b + cc)]
        rings.append([p + side * x + up * y for x, y in pts])
    loft(pm, cid, rings, tilefn, meta=meta)
# ----------------------------------------------------------------------------------------------
# torso (jacket, shirt window, tie, belt), pelvis, trousers, legs, shoes
# ----------------------------------------------------------------------------------------------
FLOOR_IN = 0.10                                   # depth of the shirt / trouser window below the jacket surface
OPEN_UP = [(-.60, 5.05), (-.92, 4.62), (-.78, 4.10), (-.56, 3.30), (-.56, 2.86), (.56, 2.86), (.56, 3.30), (.78, 4.10), (.92, 4.62), (.60, 5.05)]
OPEN_LOW = [(-.56, 2.86), (-.56, 2.10), (.56, 2.10), (.56, 2.86)]


def floor_front(x, h):
    return tfront(x, h) + FLOOR_IN


def cut_window(bm, poly, floor_tile, wall_tile):
    cutter = plate_bm(poly, tfront, [(FLOOR_IN, 1.0, 1.0), (-.40, 1.0, 1.0)], floor_tile)
    bm = bm_boolean(bm, cutter)
    cutter.free()
    tl_ = bm.faces.layers.int.get("tile")
    for f_ in bm.faces:
        if PAL[f_[tl_]][0] == floor_tile:
            f_.normal_update()
            if abs(f_.normal.y) < 0.7:
                f_[tl_] = TILE[wall_tile]
    return bm


# ---- UpperTorso: jacket shell with the V window (shirt floor), shirt collar band, lapels, tie, pocket square, buttons --------------------
ut = PM("UpperTorso", JV["Waist"], xf=xf_ut)
bm = loft_bm([row_ring(r) for r in UPPER_ROWS], sh_navy)
bm = cut_window(bm, OPEN_UP, "Shirt", "NavyShadow")
ut.append_bm("UT_jacket_shell", bm, None, {"recipe": "7-row octagon loft H2.20..4.86 (upper part from H2.86), V-window boolean (floor .10 under the surface) for the shirt", "class": "measured+extrapolated"})
bm.free()

# shirt collar band around the neck (white) + two pointed collar flaps on the shirt floor
loft(ut, "UT_collar_band", [ring8(.60, -.52, .50, .10, 0, 0, h) for h in (4.80, 4.86)] + [ring8(.60, -.52, .50, .10, 0, 0, 5.08)], sh_shirt, meta={"recipe": "collar band W1.20 around the neck H4.80..5.08", "class": "prescribed"})
for s, nm in ((-1, "R"), (1, "L")):
    flap = [(s * .16, 5.04), (s * .62, 5.04), (s * .70, 4.50), (s * .46, 4.62), (s * .18, 4.58)]
    layered_plate(ut, "UT_collar_flap_" + nm, flap, floor_front, [(+.03, 1.0, 1.0), (-.095, 1.0, 1.0)], sh_const("Shirt"), {"recipe": "pointed collar flap on the shirt floor", "class": "observed"})
    # lapel: navy plate over the jacket surface along the window edge, up to the button line
    lap = [(s * .60, 5.06), (s * .93, 4.62), (s * .79, 4.10), (s * .55, 3.30), (s * .84, 3.36), (s * 1.04, 4.10), (s * 1.28, 4.64), (s * 1.02, 5.00)]
    layered_plate(ut, "UT_lapel_" + nm, lap, tfront, [(+.05, 1.0, 1.0), (-.07, 1.0, 1.0)], sh_const("NavyLight"), {"recipe": "lapel plate .07 proud, notch + peak", "class": "observed"})
    lap_edge = [(s * .93, 4.62), (s * 1.28, 4.64), (s * 1.30, 4.55), (s * .96, 4.50)]
    layered_plate(ut, "UT_lapel_peak_" + nm, lap_edge, tfront, [(+.05, 1.0, 1.0), (-.10, 1.0, 1.0)], sh_const("Navy"), {"recipe": "lapel peak facet", "class": "extrapolated"})

# tie (knot + blade down to H2.86), gold tie bar, pocket square
KNOT = [(-.17, 4.86), (.17, 4.86), (.23, 4.54), (.15, 4.40), (-.15, 4.40), (-.23, 4.54)]
layered_plate(ut, "UT_tie_knot", KNOT, floor_front, [(+.03, 1.0, 1.0), (-.14, 1.0, 1.0)], sh_tie, {"recipe": "tie knot, 0.14 proud of the shirt floor", "class": "observed"})
BLADE = [(-.16, 4.46), (.16, 4.46), (.30, 3.90), (.35, 3.30), (.33, 2.86), (-.33, 2.86), (-.35, 3.30), (-.30, 3.90)]
layered_plate(ut, "UT_tie_blade", BLADE, floor_front, [(+.03, 1.0, 1.0), (-.11, 1.0, 1.0)], sh_tie, {"recipe": "tie blade widening to W.70, 0.11 proud", "class": "observed"})
layered_plate(ut, "UT_tie_bar", [(-.235, 3.86), (.235, 3.86), (.235, 3.78), (-.235, 3.78)], floor_front, [(+.03, 1.0, 1.0), (-.17, 1.0, 1.0)], sh_gold, {"recipe": "narrow horizontal gold tie bar", "class": "observed"})
layered_plate(ut, "UT_pocket_welt", [(1.02, 3.93), (1.44, 3.93), (1.44, 3.88), (1.02, 3.88)], tfront, [(+.05, 1.0, 1.0), (-.06, 1.0, 1.0)], sh_const("NavyShadow"), {"recipe": "breast pocket welt (character left)", "class": "observed"})
layered_plate(ut, "UT_pocket_square", [(1.08, 3.93), (1.40, 3.93), (1.36, 4.18), (1.24, 4.04), (1.14, 4.16)], tfront, [(+.05, 1.0, 1.0), (-.10, 1.0, 1.0)], sh_const("Shirt"), {"recipe": "white pocket square, two folded points", "class": "observed"})
for k, (bx, bh) in enumerate(((-.66, 3.12), (-.64, 2.70))):
    fy = -(tfront(bx, bh) - .01)
    cyl_y(ut, "UT_button_%d" % (k + 1), bx, bh, tfront(bx, bh) - .07, tfront(bx, bh) + .03, .075, 10, sh_const("Button"), {"recipe": "jacket button", "class": "observed"})

# ---- LowerTorso: jacket skirt (H2.20..2.86) with the trouser window, belt, buckle, pelvis / seat ---------------------------------------------
lt = PM("LowerTorso", JV["Root"], xf=xf_lt)
bm = loft_bm([row_ring(r) for r in LOWER_ROWS], sh_navy)
bm = cut_window(bm, OPEN_LOW, "Trouser", "NavyShadow")
_ha = AxisG(JV["RightWrist"], JV["RightWrist"] + RHAND_DIR * .96)


def _lt_old(q):
    """world (Blender) point -> LowerTorso authoring coordinates (inverse of xf_lt)"""
    return V((q.x / LT_SX, q.y / .95, 1.93 + (q.z - 2.25) / .663))


_tun = loft_bm([[_lt_old(q) for q in _ha.ring(t, 1.02, .66, .12)] for t in (.10, .45, .80, 1.12)], sh_const("NavyDeep"))
bm = bm_boolean(bm, _tun)
_tun.free()
lt.append_bm("LT_jacket_skirt", bm, None, {"recipe": "jacket skirt rows H2.20..2.86 with trouser window", "class": "measured+extrapolated"})
bm.free()
PEL = [(1.93, 2.70, .56, -.52, .14), (2.05, 3.14, .70, -.64, .14), (2.20, 3.20, .74, -.66, .13), (2.34, 3.06, .70, -.64, .12)]
loft(lt, "LT_pelvis_trousers", [row_ring((h, w, -ff, -fb, c)) for h, w, ff, fb, c in PEL], sh_trouser, meta={"recipe": "seat / pelvis block H1.93..2.34 (crotch at H1.93 as measured)", "class": "measured+extrapolated"})
layered_plate(lt, "LT_belt", [(-.80, 2.88), (.80, 2.88), (.80, 2.55), (-.80, 2.55)], floor_front, [(+.04, 1.0, 1.0), (-.045, 1.0, 1.0)], sh_const("BeltBlack"), {"recipe": "belt band H2.55..2.88 across the window", "class": "observed"})
BUCK_F = floor_front(0, 2.7) - .045
for nm, x0, x1, h0, h1, tile in (("L", -.30, -.18, 2.55, 2.88, "Silver"), ("R", .18, .30, 2.55, 2.88, "Silver"), ("T", -.30, .30, 2.78, 2.88, "SilverLight"), ("B", -.30, .30, 2.55, 2.65, "SilverShadow")):
    solid_box(lt, "LT_buckle_%s" % nm, x0, x1, BUCK_F - .06, BUCK_F + .05, h0, h1, tile, {"recipe": "silver rectangular buckle frame (4 bars)", "class": "observed"})
solid_box(lt, "LT_buckle_prong", -.045, .045, BUCK_F - .05, BUCK_F + .05, 2.62, 2.82, "Silver", {"recipe": "buckle tongue", "class": "observed"})
TIP = [(-.33, 2.87), (.33, 2.87), (.0, 2.70)]
layered_plate(lt, "LT_tie_tip", TIP, floor_front, [(+.03, 1.0, 1.0), (-.11, 1.0, 1.0)], sh_tie, {"recipe": "tie tip over the belt (continues the blade)", "class": "observed"})
solid_box(lt, "LT_fly_seam", -.012, .012, floor_front(0, 2.2) - .02, floor_front(0, 2.2) + .03, 1.96, 2.55, "TrouserShadow", {"recipe": "fly seam", "class": "extrapolated"})

# ---- legs: trousers (UpperLeg), straight leg + turn-up cuff (LowerLeg), dress shoes (Foot) -------------------------------------------------
LEGX = 0.93                                   # authoring centre; the leg parts are moved/narrowed to X=+-0.80 by xf (revision 5)
LEGN = 0.80
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    hip, knee, ank = JV[side + "Hip"], JV[side + "Knee"], JV[side + "Ankle"]
    _lx = lambda p, s=s: V((s * LEGN + (p.x - s * LEGX) * .84, p.y * .92, p.z))
    ul = PM(side + "UpperLeg", hip, xf=lambda p, s=s: (lambda q: V((q.x, q.y, 1.30 + (q.z - 1.30) * (1.16 / 1.04))))(_lx(V(p))))
    rings = [ring8(.755, -.69, .69, .11, s * LEGX, 0, 1.30), ring8(.795, -.725, .725, .12, s * LEGX, 0, 1.42), ring8(.82, -.75, .75, .12, s * LEGX, 0, 2.20), ring8(.78, -.70, .70, .10, s * LEGX, 0, 2.34)]   # lower rings inset by .015 vs the LowerLeg (no coplanar surfaces)
    loft(ul, "UL_trouser_" + side, rings, sh_trouser, meta={"recipe": "trouser leg W1.62..1.64 x D1.48, hip hidden under the jacket", "class": "measured"})
    solid_box(ul, "UL_crease_" + side, s * LEGX - .016, s * LEGX + .016, -.765, -.735, 1.50, 2.18, "TrouserLight", {"recipe": "front trouser crease", "class": "extrapolated"})
    ll = PM(side + "LowerLeg", knee, xf=lambda p, s=s: _lx(V(p)))
    solid_box(ll, "LL_crease_" + side, s * LEGX - .016, s * LEGX + .016, -.775, -.745, 1.02, 1.45, "TrouserLight", {"recipe": "front trouser crease continues over the shin", "class": "extrapolated"})
    secs = [(1.45, .81, .74), (1.20, .80, .73), (0.98, .79, .72), (0.60, .79, .72)]
    loft(ll, "LL_trouser_" + side, [ring8(a, -.02 - d, -.02 + d, .11, s * LEGX, 0, h) for h, a, d in secs], sh_trouser, meta={"recipe": "straight trouser leg W1.60 x D1.46", "class": "measured"})
    cuff = [ring8(.835, -.02 - .765, -.02 + .765, .11, s * LEGX, 0, h) for h in (0.66, 0.70, 0.96, 1.00)]
    cuff[0] = ring8(.80, -.02 - .73, -.02 + .73, .10, s * LEGX, 0, 0.66)
    loft(ll, "LL_cuff_" + side, cuff, sh_const("Trouser"), band_tiles={2: "TrouserLight"}, meta={"recipe": "turn-up cuff H.66..1.00, 0.045 proud, lighter fold edge", "class": "observed"})

    th = s * 7.0
    _rot = rot_xf(ank, th)
    ft = PM(side + "Foot", ank, xf=lambda p, s=s, _rot=_rot: _rot(V((s * LEGN + (V(p).x - s * LEGX) * .92, V(p).y, V(p).z))))
    cx = s * LEGX
    sole = [ring8(.66, -1.40, .58, .12, cx, 0, 0.0), ring8(.73, -1.50, .63, .13, cx, 0, .10), ring8(.73, -1.50, .63, .13, cx, 0, .30), ring8(.68, -1.44, .60, .12, cx, 0, .38)]
    loft(ft, "FT_sole_" + side, sole, sh_sole, band_tiles={1: "SoleLight"}, meta={"recipe": "sole W1.44 x D2.10 x H.27, bevel .12, welt band", "class": "measured+extrapolated"})

    def ring_xh(f, w, h0, h1, c, cx=cx):
        a = w / 2
        pts = [(-a + c, h0), (a - c, h0), (a, h0 + c), (a, h1 - c), (a - c, h1), (-a + c, h1), (-a, h1 - c), (-a, h0 + c)]
        return [V((cx + x, -f, h)) for x, h in pts]
    UP = [(-.56, .72, 1.22, .16), (-.30, .79, 1.34, .18), (.30, .78, 1.40, .18), (.80, .70, 1.42, .18), (1.15, .58, 1.38, .16), (1.40, .48, 1.22, .14), (1.50, .38, 1.04, .06)]
    loft(ft, "FT_upper_" + side, [ring_xh(f, w, .26, top, c) for f, top, w, c in UP], sh_shoe, meta={"recipe": "oversized dress-shoe block, heel/collar H.72..79 falling to a faceted toe H.38", "class": "measured+extrapolated"})
    patch_box(ft, "FT_top_facet_" + side, cx, .72, .70, .80, 1.00, .02, "ShoeLight", embed=.01, meta={"recipe": "flat lighter top facet", "class": "observed"})
    prism_poly(ft, "FT_toe_shine_" + side, [Bl(cx - .12, 1.12, .60), Bl(cx + .12, 1.12, .60), Bl(cx, 1.30, .55)], V((0, 0, .045)), sh_const("SilverLight"), {"recipe": "small silver facet highlight on the toe top", "class": "observed"})
    solid_box(ft, "FT_heel_band_" + side, cx - .55, cx + .55, .52, .64, .14, .36, "SoleLight", {"recipe": "heel block band", "class": "extrapolated"})


# ---- revision 3 details ----------------------------------------------------------------------------------------------------------
# jacket hip pocket flaps (both sides; the right one frames the hand) + back vent seam
for sx, nm in ((-1, "R"), (1, "L")):
    layered_plate(lt, "LT_pocket_flap_" + nm, [(sx * .72, 2.58), (sx * 1.36, 2.58), (sx * 1.36, 2.38), (sx * .72, 2.38)], tfront, [(+.05, 1.0, 1.0), (-.055, 1.0, 1.0)], sh_const("NavyShadow"), {"recipe": "hip pocket flap", "class": "extrapolated"})
    layered_plate(lt, "LT_pocket_flap_edge_" + nm, [(sx * .72, 2.40), (sx * 1.36, 2.40), (sx * 1.36, 2.375), (sx * .72, 2.375)], tfront, [(+.05, 1.0, 1.0), (-.07, 1.0, 1.0)], sh_const("NavyLight"), {"recipe": "lighter lower edge of the flap", "class": "extrapolated"})
solid_box(lt, "LT_back_vent", -.014, .014, tback(0, 2.5) - .02, tback(0, 2.5) + .028, 2.22, 2.88, "NavyDeep", {"recipe": "centre back vent seam (inferred, one thin seam only)", "class": "extrapolated"})
# navy jacket collar rolling around the back half of the neck (the white shirt collar stays inside it)
loft(ut, "UT_back_collar", [ring8(.70, -.02, .56, .12, 0, 0, h) for h in (4.80, 4.88)] + [ring8(.64, -.02, .50, .10, 0, 0, 5.06)], sh_const("NavyLight"), meta={"recipe": "back collar roll (front edge F-.02, behind the neck)", "class": "extrapolated"})
# ----------------------------------------------------------------------------------------------
# arms: navy sleeves (shared mitre contour at the elbow), white cuffs, hands; left wrist watch
# ----------------------------------------------------------------------------------------------
UPPER_SEC = [(0.0, 1.30, 1.30), (.28, 1.36, 1.34), (.70, 1.22, 1.18), (1.0, 1.12, 1.08)]   # D +.04 at the shoulder so the sleeve back never coincides with the jacket back
LOWER_SEC = [(0.0, 1.12, 1.08), (.45, 1.04, 1.00), (.80, .98, .94), (1.0, .96, .92)]
ARM_C = .20
SLEEVE_END = .80
OVERLAP = .04
ARM_AX = {}
ELBOW_RING = {}
HAND_AX = {}
HAND_LEN = .96
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    S, E, W_ = JV[side + "Shoulder"], JV[side + "Elbow"], JV[side + "Wrist"]
    ax1, ax2 = AxisG(S, E), AxisG(E, W_)
    ARM_AX[side] = (ax1, ax2)
    N = (ax1.A + ax2.A).normalized()
    K = []
    for x, y in ax1.corners(UPPER_SEC[-1][1], UPPER_SEC[-1][2], ARM_C):
        p = E + ax1.U * x + ax1.W * y
        K.append(p - ax1.A * (((p - E).dot(N)) / ax1.A.dot(N)))
    ELBOW_RING[side] = K
    ua = PM(side + "UpperArm", S)
    t0 = -OVERLAP / ax1.L
    rings = [ax1.ring(t0, UPPER_SEC[0][1], UPPER_SEC[0][2], ARM_C)] + [ax1.ring(t, w, d, ARM_C) for t, w, d in UPPER_SEC[1:-1]] + [K]
    loft(ua, "UA_sleeve_" + side, rings, sh_navy, meta={"recipe": "angular jacket sleeve W1.30->1.12, chamfer .20, elbow end = shared mitre contour", "class": "measured+extrapolated"})
    la = PM(side + "LowerArm", E)
    ts = [.14, .45, SLEEVE_END]
    lr = [ax2.ring(t, *sec_at(LOWER_SEC, t), ARM_C) for t in ts]
    best = min(range(8), key=lambda sh: sum((K[k] - lr[0][(k + sh) % 8]).length for k in range(8)))
    lr = [[r[(k + best) % 8] for k in range(8)] for r in lr]
    loft(la, "LA_sleeve_" + side, [K] + lr, sh_navy, meta={"recipe": "forearm sleeve W1.12->.98, ends at t=.80; ring order shift %d" % best, "class": "measured+extrapolated"})
    cuffs = [ax2.ring(t, w, d, .12) for t, w, d in ((SLEEVE_END - .03, .86, .82), (SLEEVE_END + .03, .86, .82), (1.0, .86, .82), (1.0 + OVERLAP / ax2.L, .80, .76))]
    loft(la, "LA_cuff_" + side, cuffs, sh_shirt, meta={"recipe": "white shirt cuff W.86 x .82, ~.26 visible beyond the sleeve", "class": "observed"})
    # sleeve buttons on the outer face (two tiny dark blocks)
    for k, t in enumerate((.60, .70)):
        abox(la, "LA_cuff_button_%s_%d" % (side, k + 1), ax2, t, t + .045, s * (.5 * sec_at(LOWER_SEC, t)[0] - .01), s * (.5 * sec_at(LOWER_SEC, t)[0] + .035), -.07, .07, "Button", {"recipe": "tiny dark sleeve button", "class": "observed"})

# ---- hands: large square hands built along the forearm direction ---------------------------------------------------------------------
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    Wp = JV[side + "Wrist"]
    dirv = RHAND_DIR if side == "Right" else (JV[side + "Wrist"] - JV[side + "Elbow"]).normalized()
    hx = AxisG(Wp, Wp + dirv * HAND_LEN)
    HAND_AX[side] = hx
    hp = PM(side + "Hand", Wp)
    DK = .62 if side == "Right" else 1.0      # the pocket hand is thinner front-to-back so that it disappears inside the jacket
    rings = [hx.ring(-.06, .64, .58 * DK, .10), hx.ring(.30, .68, .62 * DK, .11), hx.ring(.44, .94, .90 * DK, .15), hx.ring(.94, .96, .90 * DK, .16), hx.ring(1.0, .80, .76 * DK, .13)]
    loft(hp, "HAND_fist_" + side, rings, sh_skin_arm, meta={"recipe": "square fist .96 x .90 x %.2f along the forearm, wrist neck .64 x .58" % (HAND_LEN * .66), "class": "measured+extrapolated"})
    # thumb block on the inner side (toward the body)
    if side == "Left": abox(hp, "HAND_thumb_" + side, hx, .50, .92, -s * .50, -s * .36, -.34, .12, "SkinLight", {"recipe": "thumb block on the inner side, overlaps the fist", "class": "extrapolated"})
    # knuckle creases on the outer/front face (+W): four stacked finger blocks read as three crease lines
    for k, t in enumerate((.60, .72, .84) if side == "Left" else ()):
        abox(hp, "HAND_crease_%s_%d" % (side, k + 1), hx, t, t + .028, -.40, .40, .445, .465, "SkinShadow", {"recipe": "finger crease", "class": "observed"})
    if side == "Left": abox(hp, "HAND_knuckle_band_" + side, hx, .46, .94, -.47, .47, .435, .455, "SkinLight", {"recipe": "lighter finger-top band", "class": "extrapolated"})

# left wrist watch (revision 4, after the turnaround close-up): gold octagonal case with a black dial, 12 tick marks, two hands, crown, gold link bracelet
hxl = HAND_AX["Left"]
lh = PARTS["LeftHand"]
# watch face frame: the hand frame rotated by -160 deg about the hand axis (dial faces front-down-outward, towards the camera; set in the live Blender scene via MCP)
_wa = math.radians(-160)
hxw = AxisG(hxl.P0, hxl.P1)
hxw.U, hxw.W = hxl.U * math.cos(_wa) + hxl.W * math.sin(_wa), hxl.W * math.cos(_wa) - hxl.U * math.sin(_wa)
WT_C = .17                                    # case centre along the hand axis (fraction of its length)


def oct_ring(ax, tc, r, y, rot=22.5):
    return [ax.pt(tc + r * math.cos(math.radians(rot + 45 * k)) / ax.L, r * math.sin(math.radians(rot + 45 * k)), y) for k in range(8)]


def bar(ax, cid, tc, xc, length, width, ang_deg, y0, y1, tile):
    """thin rectangular bar in the (axis, U) plane of the watch face, centre (tc, xc), rotated by ang_deg, between face offsets y0..y1"""
    a_ = math.radians(ang_deg)
    dt, dx = math.cos(a_), math.sin(a_)
    nt, nx = -dx, dt
    pts = []
    for sl, sw in ((-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)):
        pts.append((tc + (dt * sl * length + nt * sw * width) / ax.L, xc + dx * sl * length + nx * sw * width))
    r0 = [ax.pt(t_, x_, y0) for t_, x_ in pts]
    r1 = [ax.pt(t_, x_, y1) for t_, x_ in pts]
    loft(lh, cid, [r0, r1], tile, meta={"recipe": "watch hand / tick", "class": "observed"})


links = [hxl.ring(t, .84, .78, .13) for t in (-.03, .02, .07, .12, .17, .22, .27, .32, .37)]
loft(lh, "WATCH_bracelet", links, sh_gold, band_tiles={0: "GoldShadow", 2: "GoldShadow", 4: "GoldShadow", 6: "GoldShadow"}, meta={"recipe": "gold link bracelet W.84 x .78, 4 link gaps", "class": "observed"})
loft(lh, "WATCH_case", [oct_ring(hxw, WT_C, .40, .36), oct_ring(hxw, WT_C, .40, .50), oct_ring(hxw, WT_C, .35, .57)], sh_gold, meta={"recipe": "octagonal gold case r.40, bevelled top", "class": "observed"})
loft(lh, "WATCH_dial", [oct_ring(hxw, WT_C, .27, .55), oct_ring(hxw, WT_C, .27, .595)], "WatchDial", meta={"recipe": "black octagonal dial inset into the case", "class": "observed"})
for k in range(12):
    a_ = math.radians(30 * k)
    big = k % 3 == 0
    bar(hxw, "WATCH_tick_%d" % k, WT_C + .215 * math.cos(a_) / hxl.L, .215 * math.sin(a_), .06 if big else .035, .03 if big else .02, math.degrees(a_), .59, .615, "WatchTick")
bar(hxw, "WATCH_hand_hour", WT_C, 0.0, .24, .035, 60, .595, .62, "GoldLight")
bar(hxw, "WATCH_hand_minute", WT_C, 0.0, .34, .025, -35, .60, .635, "GoldLight")
abox(lh, "WATCH_crown", hxw, WT_C - .035, WT_C + .035, .385, .46, .40, .50, "Gold", {"recipe": "crown on the case side", "class": "observed"})
# ----------------------------------------------------------------------------------------------
# head: faceted skull, ears, hooded eyes, brows, nose, curled moustache, mouth, swept hair wave with grey temples
# ----------------------------------------------------------------------------------------------
hd = PM("Head", JV["Neck"], xf=xf_head)
# moustache correction made in the LIVE Blender scene through MCP (reference: thicker, narrower lobes, ~64% of the face width): X x0.82, H x1.15 about H5.12
MSX, MSZ, MZC = 0.82, 1.15, 5.12
SKULL = [(4.75, 1.22, .74, -.70, .20), (4.93, 1.58, .88, -.80, .20), (5.20, 1.66, .93, -.84, .20), (5.90, 1.66, .93, -.84, .18), (6.04, 1.52, .80, -.74, .14)]
loft(hd, "HD_skull", [ring8(w / 2, -ff, -fb, c, 0, 0, h) for h, w, ff, fb, c in SKULL], sh_skin, meta={"recipe": "faceted block head W1.66 x D1.77, bevel .20 at the jaw/cheeks, chin H4.75", "class": "measured+extrapolated"})
loft(hd, "HD_neck", cbox(Bl(0, -.02, 4.82), (.84, .78, .52), .10), sh_skin, meta={"recipe": "short neck block mostly inside skull/collar", "class": "extrapolated"})
for s, nm in ((-1, "Right"), (1, "Left")):
    loft(hd, "HD_ear_" + nm, cbox(Bl(s * .93, -.02, 5.20), (.26, .44, .50), .08), sh_skin, meta={"recipe": "ear block .26 x .44 x .50", "class": "observed"})
    xo = s * 1.065
    solid_box(hd, "HD_concha_" + nm, min(xo + s * .02, xo - s * .035), max(xo + s * .02, xo - s * .035), -(-.02 + .11), -(-.02 - .11), 5.07, 5.32, sh_const("EarInner"), {"recipe": "ear concha patch", "class": "observed"})
    # hooded eyes (revision 2): small whites, large pupil touching the heavy brow, gaze to the character's left; the brow covers the upper lid
    ex = s * .34
    prism_xh(hd, "HD_eyewhite_" + nm, ellipse(ex, 5.455, .120, .072, 16, rot=s * -0.10), .76, .965, sh_const("EyeWhite"), {"recipe": "narrow eye white .24 x .14, tilted, upper lid hidden by the brow", "class": "observed"})
    prism_xh(hd, "HD_pupil_" + nm, ellipse(ex + .052, 5.452, .056, .062, 12), .76, .978, sh_const("Pupil"), {"recipe": "black pupil d.11, looking to the character's left", "class": "observed"})
    prism_xh(hd, "HD_glint_" + nm, ellipse(ex + .072, 5.478, .014, .015, 8), .76, .988, sh_const("Glint"), {"recipe": "one glint per eye", "class": "observed"})
    brow = [(s * .05, 5.50), (s * .05, 5.72), (s * .38, 5.83), (s * .68, 5.93), (s * .74, 5.77), (s * .44, 5.62), (s * .26, 5.53)]
    prism_xh(hd, "HD_brow_" + nm, brow, .74, 1.03, sh_const("Brow"), {"recipe": "thick brow wedge, inner end low (H5.50) over the eye, outer end H5.93", "class": "observed"})
    mp = [(0.0, 5.13), (.14, 5.07), (.38, 5.04), (.60, 5.09), (.72, 5.22), (.76, 5.40), (.66, 5.45), (.60, 5.31), (.46, 5.25), (.24, 5.28), (0.0, 5.27)]
    prism_xh(hd, "HD_moustache_" + nm, [(s * x * MSX, MZC + (h - MZC) * MSZ) for x, h in mp] if s > 0 else [(s * x * MSX, MZC + (h - MZC) * MSZ) for x, h in mp][::-1], .70, 1.05, sh_const("Moustache"), {"recipe": "curled moustache lobe: raised, tapered, tip curls up", "class": "observed"})
    mt = [(0.0, 5.25), (.24, 5.26), (.46, 5.23), (.62, 5.31), (.58, 5.28), (.46, 5.19), (.24, 5.22), (0.0, 5.19)]
    prism_xh(hd, "HD_moustache_top_" + nm, [(s * x * MSX, MZC + (h - MZC) * MSZ) for x, h in mt] if s > 0 else [(s * x * MSX, MZC + (h - MZC) * MSZ) for x, h in mt][::-1], 1.03, 1.08, sh_const("MoustacheLight"), {"recipe": "lighter top ridge of the moustache", "class": "extrapolated"})
# nose raised by 0.10 in the LIVE Blender scene (MCP) so the moustache centre stays visible below the nose
NOSE = [(5.12, .34, 1.10, .70, .09), (5.20, .46, 1.20, .70, .15), (5.34, .53, 1.27, .70, .20), (5.52, .47, 1.20, .70, .18), (5.68, .30, 1.02, .70, .11)]   # revision 4: rounder nose (as in the turnaround close-up)
loft(hd, "HD_nose", [ring8(w / 2, -ff, -fb, c, 0, 0, h) for h, w, ff, fb, c in NOSE], sh_nose, meta={"recipe": "large faceted nose, front F1.24 (0.31 proud)", "class": "observed"})
prism_xh(hd, "HD_mouth", [(-.24, 4.93), (.0, 4.89), (.28, 4.96), (.32, 5.01), (-.0, 4.98), (-.24, 5.01)], .70, .95, sh_const("Mouth"), {"recipe": "small calm smirk line under the moustache", "class": "observed"})

# ---------------------------------------------------------------------------------------------------------------------------
# hair (revision 2): low scalp cap + a swept wave of broad locks rising at the front-left of the forehead, rolling over the crown and falling to the back right;
# the character's right side keeps a longer stepped block with the grey temple, the left side is shorter. Locks are separate sweeps, tops reach H6.40.
# ---------------------------------------------------------------------------------------------------------------------------
# ONE hair shell wraps the whole skull (no separate boxes sticking out, no bare back of the head): the front edge of the lower rows sits at F.05..0.32, so
# the sides come down to the ear and the nape, while the front edge rises diagonally to the forehead hairline H5.90 (visible as the sloped temple edge).
HC = [(5.06, 1.36, -.05, -.74, .16), (5.26, 1.74, .10, -.90, .20), (5.62, 1.78, .32, -.92, .20), (5.90, 1.78, .98, -.92, .20), (6.02, 1.78, 1.00, -.92, .20), (6.10, 1.64, .88, -.84, .18), (6.15, 1.30, .60, -.54, .12)]
def sh_hair_shell(n, c):
    """grey temples/sideburns are part of the shell surface (stepped bands on the side faces in front of the ear), not separate boxes"""
    if abs(c.x) > .70 and -.15 < -c.y < .50 and 5.15 < c.z < 5.85 and abs(n.x) > .4:
        return "HairGrey" if c.z > 5.52 else ("HairGreyLight" if c.z > 5.28 else "HairGreyShadow")
    return sh_hair(n, c)


loft(hd, "HD_hair_shell", [ring8(w / 2, -ff, -fb, c, 0, 0, h) for h, w, ff, fb, c in HC], sh_hair_shell, meta={"recipe": "single hair shell H5.06..6.15 over the whole skull; replaces the earlier cap + back/side boxes", "class": "observed+extrapolated"})
# face relief: cheek planes, nostril shadows, chin facet, eyelid shadow wedge
for s_, nm in ((-1, "Right"), (1, "Left")):
    prism_xh(hd, "HD_nostril_" + nm, ellipse(s_ * .11, 5.17, .055, .03, 8), .70, 1.17, sh_const("SkinShadow"), {"recipe": "nostril shadow under the nose", "class": "observed"})
    prism_xh(hd, "HD_eyelid_" + nm, ellipse(s_ * .34, 5.375, .12, .03, 10), .76, .962, sh_const("SkinShadow"), {"recipe": "lower eyelid shadow", "class": "extrapolated"})
prism_xh(hd, "HD_chin_facet", [(-.30, 4.78), (.30, 4.78), (.22, 4.92), (-.22, 4.92)], .70, .90, sh_const("SkinLight"), {"recipe": "chin facet", "class": "extrapolated"})


def lock(cid, pts, w0, w1, h0, h1, thick=1.0):
    # revision 4: thicker locks (pompadour volume); the centre line is clamped so that the top surface never exceeds H6.40
    k = 1.4 * thick
    pts = [(x, f, min(z, 6.40 - h0 * k / 2)) if z > 6.0 else (x, f, z) for x, f, z in pts]
    path = catmull([Bl(*p_) for p_ in pts], 4)
    sweep(hd, cid, path, lambda t: w0 + (w1 - w0) * t, lambda t: (h0 + (h1 - h0) * t) * k, .08, sh_hair, {"recipe": "broad swept lock", "class": "observed+extrapolated"})


# path points are (X, F, H) of the lock centre line; height 0.30 means the top surface is 0.15 above the path
lock("HD_wave_1", [(-.74, .98, 5.98), (-.58, 1.08, 6.14), (-.18, .76, 6.25), (.32, .30, 6.23), (.74, -.22, 6.12), (.86, -.60, 5.98)], .54, .36, .30, .24)
lock("HD_wave_2", [(-.86, .52, 5.98), (-.74, .56, 6.16), (-.34, .32, 6.24), (.14, -.16, 6.22), (.58, -.52, 6.12), (.80, -.76, 5.98)], .50, .34, .28, .22)
lock("HD_wave_3", [(-.22, .98, 5.98), (.02, .98, 6.12), (.40, .64, 6.19), (.74, .16, 6.14), (.88, -.34, 6.02)], .50, .30, .26, .22)
lock("HD_wave_4", [(-.56, -.10, 6.14), (-.16, -.44, 6.22), (.30, -.70, 6.18), (.64, -.82, 6.04)], .50, .32, .26, .22)
lock("HD_wave_5", [(.24, .94, 5.98), (.46, .86, 6.08), (.76, .56, 6.10), (.92, .22, 6.02)], .40, .26, .24, .20)
lock("HD_wave_front_curl", [(-.80, 1.00, 5.94), (-.60, 1.10, 6.08), (-.28, 1.04, 6.16)], .40, .30, .26, .22)

# back-of-head strands (revision 3): vertical broad locks along the nape so the back reads as hair, not as a plain block
for k, x in enumerate((-.62, -.31, 0.0, .31, .62)):
    lock("HD_back_strand_%d" % (k + 1), [(x * .98, -.80, 6.06), (x, -.95, 5.80), (x * 1.02, -.97, 5.50), (x * .96, -.90, 5.20)], .30, .26, .14, .12, 0.75)
# ----------------------------------------------------------------------------------------------
# phone (separate rigid prop in the left hand): near-black slab, rounded corners, two lenses + flash, no UI / text / logo
# ----------------------------------------------------------------------------------------------
PHONE_LOGICAL = (2.15, 1.52, 4.60)
PHONE_C = Bl(*PHONE_LOGICAL)
PHONE_YAW = 28.0                              # screen turned towards his face
PHONE_ROLL = 10.0                             # top leans outward (towards +X) as in the reference
_yaw, _roll = rot_xf(PHONE_C, PHONE_YAW, "Z"), rot_xf(PHONE_C, PHONE_ROLL, "Y")
PW, PT_, PH = .62, .12, 1.12                    # width X, thickness F, height H (revision 2: larger, as in the reference where the phone is ~0.7 of the fist width)
ph = PM("Phone", PHONE_C, geo="Phone_Geo", xf=lambda p: _yaw(_roll(p)))
PX, PY, PZ = PHONE_C.x, PHONE_C.y, PHONE_C.z
PR = .17


def phone_ring(y, grow=0.0):
    """rounded rectangle outline, 4 arcs x 4 points (revision 4: rounder corners as in the turnaround close-up)"""
    a, hh = PW / 2 + grow, PH / 2 + grow
    r = PR + grow
    pts = []
    for cxq, czq, a0 in ((a - r, hh - r, 0), (-a + r, hh - r, 90), (-a + r, -hh + r, 180), (a - r, -hh + r, 270)):
        for k in range(4):
            th = math.radians(a0 + 90 * k / 3)
            pts.append((cxq + r * math.cos(th), czq + r * math.sin(th)))
    return [V((PX + x, y, PZ + z)) for x, z in pts]


# body: front/back half-thickness PT_/2; edge frame slightly lighter, back dark; screen side faces -F (towards his face)
loft(ph, "PH_body", [phone_ring(PY - PT_ / 2 + .012, -.012), phone_ring(PY - PT_ / 2 + .02), phone_ring(PY + PT_ / 2 - .02), phone_ring(PY + PT_ / 2 - .012, -.012)], sh_const("PhoneBody"), band_tiles={1: "PhoneEdge"},
     meta={"recipe": "slab .50 x .09 x .92, corner radius .11 (octagon), edge band lighter", "class": "observed"})
back = PY - PT_ / 2                              # logical back of the phone faces +F = Blender -Y
for k, (lx, lz, r_) in enumerate(((-.15, .38, .075), (-.15, .22, .070))):
    cyl_y(ph, "PH_lens_ring_%d" % (k + 1), PX + lx, PZ + lz, back + .02, back - .034, r_ + .018, 10, sh_const("LensRing"), {"recipe": "lens ring", "class": "observed"})
    cyl_y(ph, "PH_lens_%d" % (k + 1), PX + lx, PZ + lz, back + .02, back - .042, r_, 10, sh_const("Lens"), {"recipe": "dark lens", "class": "observed"})
cyl_y(ph, "PH_flash", PX - .06, PZ + .45, back + .02, back - .030, .026, 8, sh_const("Flash"), {"recipe": "tiny flash", "class": "observed"})
# revision 3: raised camera island behind the lenses, two side buttons, thin glass inset on the back (all separate shells embedded in the slab, no coplanar faces)
solid_box(ph, "PH_camera_island", PX - .29, PX - .01, back - .020, back + .030, PZ + .13, PZ + .51, "PhoneEdge", {"recipe": "raised camera island .28 x .38, proud .02", "class": "observed"})
solid_box(ph, "PH_side_button_1", PX + PW / 2 - .01, PX + PW / 2 + .028, PY - .035, PY + .020, PZ + .12, PZ + .30, "PhoneEdge", {"recipe": "side button", "class": "extrapolated"})
solid_box(ph, "PH_side_button_2", PX + PW / 2 - .01, PX + PW / 2 + .028, PY - .035, PY + .020, PZ - .12, PZ + .02, "PhoneEdge", {"recipe": "side button", "class": "extrapolated"})
solid_box(ph, "PH_back_inset", PX - .22, PX + .22, back - .006, back + .030, PZ - .46, PZ + .06, "PhoneEdge", {"recipe": "slightly lighter back glass panel, proud .006", "class": "extrapolated"})


# ----------------------------------------------------------------------------------------------
# atlas / material / mesh objects
# ----------------------------------------------------------------------------------------------
os.makedirs(os.path.join(OUT, "textures"), exist_ok=True)
atlas = bpy.data.images.new("BusinessDad_Atlas", ATLAS_W, ATLAS_H, alpha=False)
atlas.colorspace_settings.name = 'sRGB'
px = [0.0] * (ATLAS_W * ATLAS_H * 4)
fill = hex_rgb(HEXOF["Navy"])
for ty in range(ATLAS_H):
    for tx in range(ATLAS_W):
        idx = (ty // TILE_PX) * COLS + (tx // TILE_PX)
        rgb = hex_rgb(PAL[idx][1]) if idx < len(PAL) else fill
        r, g, b = (c / 255.0 for c in rgb)
        o = ((ATLAS_H - 1 - ty) * ATLAS_W + tx) * 4
        px[o:o + 4] = [r, g, b, 1.0]
atlas.pixels.foreach_set(px)
ATLAS_PATH = os.path.join(OUT, "textures", "BusinessDad_Atlas.png")
atlas.filepath_raw = ATLAS_PATH
atlas.file_format = 'PNG'
atlas.save()
atlas.pack()

MATP = bpy.data.materials.new("BusinessDad_Atlas")
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

for pm in PARTS.values():
    bm = pm.bm
    bm.normal_update()
    me = bpy.data.meshes.new(pm.geo)
    bm.to_mesh(me)
    uv = me.uv_layers.new(name="UVMap")
    ca = me.color_attributes.new("Col", 'BYTE_COLOR', 'CORNER')
    attr = me.attributes.get("tile")
    for pi, poly in enumerate(me.polygons):
        t = attr.data[pi].value if attr else 0
        u0, v0, u1, v1 = tile_uv_patch(t)
        corners = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
        r_, g_, b_ = hex_rgb(PAL[t][1])
        for k, li in enumerate(poly.loop_indices):
            uv.data[li].uv = corners[k % 4]
            try:
                ca.data[li].color_srgb = (r_ / 255.0, g_ / 255.0, b_ / 255.0, 1.0)
            except AttributeError:
                ca.data[li].color = (srgb_to_lin(r_), srgb_to_lin(g_), srgb_to_lin(b_), 1.0)
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
    pm.bm.free()

# ----------------------------------------------------------------------------------------------
# armature (R15 hierarchy, identical to the Regular/Office builders) + rigid 100% weights; pose = rest pose (HoldWeights)
# ----------------------------------------------------------------------------------------------
arm_data = bpy.data.armatures.new("BusinessDad_Armature")
ARM_OB = bpy.data.objects.new("BusinessDad_Armature", arm_data)
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
        (side + "Hand", side + "LowerArm", JV[side + "Wrist"], HAND_AX[side].P1),
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
PROPS = ("Phone",)
for pm in PARTS.values():
    bone = {"Phone": "LeftHand"}.get(pm.runtime, pm.runtime)
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
from collections import Counter


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


def world_verts(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ev.matrix_world
    out = [mw @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    return out


def bvh_of(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    bmx = bmesh.new()
    bmx.from_mesh(me)
    bmx.transform(ev.matrix_world)
    ev.to_mesh_clear()
    bmesh.ops.triangulate(bmx, faces=bmx.faces)
    t = BVHTree.FromBMesh(bmx)
    pts = [v.co.copy() for v in bmx.verts]
    bmx.free()
    return t, pts


BODY = [PARTS[k].obj for k in PARTS if k not in PROPS]
PROP_OB = {k: PARTS[k].obj for k in PROPS}
lo, hi = world_bounds(BODY)
head_lo, head_hi = world_bounds([PARTS["Head"].obj])
ft_lo, _ = world_bounds([PARTS["RightFoot"].obj, PARTS["LeftFoot"].obj])
bounds_all = {k: [[round(c, 4) for c in a] for a in world_bounds([PARTS[k].obj])] for k in PARTS}
body_tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in BODY)
prop_tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in PROP_OB.items()}
print("BOUNDS body", tuple(round(x, 3) for x in lo), tuple(round(x, 3) for x in hi))
print("HEAD", tuple(round(x, 3) for x in head_lo), tuple(round(x, 3) for x in head_hi), "FEET", round(ft_lo.z, 4))
print("TRIS body", body_tris, "props", prop_tris)

AUDIT = {}
for pm in PARTS.values():
    me = pm.obj.data
    bmx = bmesh.new()
    bmx.from_mesh(me)
    bmesh.ops.remove_doubles(bmx, verts=bmx.verts, dist=1e-5)
    cnt = Counter()
    for f in bmx.faces:
        vs = [v.index for v in f.verts]
        for a, b in zip(vs, vs[1:] + vs[:1]):
            cnt[(min(a, b), max(a, b))] += 1
    vol = 0.0
    for f in bmx.faces:
        vv = [v.co for v in f.verts]
        for k in range(1, len(vv) - 1):
            vol += vv[0].dot(vv[k].cross(vv[k + 1])) / 6.0
    uvs = [tuple(l.uv) for l in me.uv_layers.active.data]
    AUDIT[pm.runtime] = {"verts": len(me.vertices), "tris": sum(len(p.vertices) - 2 for p in me.polygons),
                         "open_edges": sum(1 for v in cnt.values() if v == 1), "nonmanifold_edges": sum(1 for v in cnt.values() if v > 2),
                         "zero_area": sum(1 for f in bmx.faces if f.calc_area() < 1e-9), "signed_volume": round(vol, 4),
                         "uv_in_range": all(0 <= u <= 1 and 0 <= v <= 1 for u, v in uvs), "components": len(pm.comps)}
    bmx.free()


def mirror_dev(a, b):
    """max distance of the mirrored (x -> -x) vertices of a from the surface of b."""
    t, _ = bvh_of(b)
    return max((t.find_nearest(V((-p.x, p.y, p.z)))[3] or 0.0) for p in world_verts(a))


SYM = {"UpperLeg_mirror_dev": round(mirror_dev(PARTS["RightUpperLeg"].obj, PARTS["LeftUpperLeg"].obj), 6),
       "LowerLeg_mirror_dev": round(mirror_dev(PARTS["RightLowerLeg"].obj, PARTS["LeftLowerLeg"].obj), 6),
       "Foot_mirror_dev": round(mirror_dev(PARTS["RightFoot"].obj, PARTS["LeftFoot"].obj), 6)}
lens = {}
for side in ("Right", "Left"):
    lens[side] = {"shoulder_elbow": round((JV[side + "Elbow"] - JV[side + "Shoulder"]).length, 6), "elbow_wrist": round((JV[side + "Wrist"] - JV[side + "Elbow"]).length, 6)}
head_c = (head_lo + head_hi) / 2
pel_lo, pel_hi = world_bounds([PARTS["LowerTorso"].obj])
AXES = {"head_centre_x": round(head_c.x, 5), "pelvis_centre_x": round((pel_lo.x + pel_hi.x) / 2, 5)}

# interpenetration / clearance (BVH on the evaluated meshes); contacts listed as hidden-allowed are reported separately
ALLOWED = {"Phone": {"LeftHand": "lower phone edge sits inside the closed fist (hidden, allowed)"}}
CLEAR = {}
for prop, others in (("Phone", ("UpperTorso", "Head", "LeftLowerArm", "LeftUpperArm", "LeftHand", "RightHand", "LowerTorso")),):
    pt, ppts = bvh_of(PROP_OB[prop])
    CLEAR[prop] = {}
    for n in others:
        t, pts = bvh_of(PARTS[n].obj)
        md = min((t.find_nearest(p)[3] or 9e9) for p in ppts)
        mdr = min((pt.find_nearest(p)[3] or 9e9) for p in pts)
        CLEAR[prop][n] = {"overlapping_triangle_pairs": len(pt.overlap(t)), "min_vertex_distance": round(min(md, mdr), 4),
                          "allowed_hidden_contact": ALLOWED.get(prop, {}).get(n)}
print("CLEARANCE", json.dumps(CLEAR))
# shoe vs shin, hand vs forearm sanity
JOINT_GAPS = {}
for side in ("Right", "Left"):
    for a, b, j in (("UpperArm", "LowerArm", "Elbow"), ("LowerArm", "Hand", "Wrist"), ("UpperLeg", "LowerLeg", "Knee"), ("LowerLeg", "Foot", "Ankle")):
        ta, _ = bvh_of(PARTS[side + a].obj)
        tb, pb_ = bvh_of(PARTS[side + b].obj)
        JOINT_GAPS[side + j] = {"overlap_pairs": len(ta.overlap(tb)), "joint_to_surface_a": round((ta.find_nearest(JV[side + j])[3] or 0), 5), "joint_to_surface_b": round((tb.find_nearest(JV[side + j])[3] or 0), 5)}


# ----------------------------------------------------------------------------------------------
# outputs: blend, FBX, data JSON
# ----------------------------------------------------------------------------------------------
os.makedirs(os.path.join(OUT, "export"), exist_ok=True)
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
os.makedirs(os.path.join(OUT, "source"), exist_ok=True)
BLEND = os.path.join(OUT, "source", "BusinessDad_Review.blend")
FBX_BODY = os.path.join(OUT, "export", "BusinessDad_Body.fbx")
FBX_PROPS = os.path.join(OUT, "export", "BusinessDad_Props.fbx")
FBX_SET = dict(use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y',
               mesh_smooth_type='FACE', use_mesh_modifiers=True, bake_anim=False, add_leaf_bones=False,
               path_mode='COPY', embed_textures=True, use_armature_deform_only=False, primary_bone_axis='Y', secondary_bone_axis='X')


def export_fbx(path, objs, types):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, object_types=types, **FBX_SET)


export_fbx(FBX_BODY, [ARM_OB] + BODY, {'MESH', 'ARMATURE'})
copies = []
for k, o in PROP_OB.items():
    cp = bpy.data.objects.new(o.name, o.data.copy())
    cp.data.name = o.data.name + "_export"
    EXP_COLL.objects.link(cp)
    cp.location = PARTS[k].joint
    copies.append(cp)
export_fbx(FBX_PROPS, copies, {'MESH'})
for cp in copies:
    bpy.data.objects.remove(cp, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("EXPORTED", FBX_BODY, FBX_PROPS, BLEND)

uvmap = {"atlas": "BusinessDad_Atlas.png", "size": [ATLAS_W, ATLAS_H], "tile_px": TILE_PX, "columns": COLS, "inset_px": INSET, "row0_is_top_of_png": True, "tiles": []}
for i, (n_, h_, use) in enumerate(PAL):
    u0, v0, u1, v1 = tile_uv_patch(i)
    uvmap["tiles"].append({"index": i, "name": n_, "hex": h_, "col": i % COLS, "row": i // COLS, "uv_patch": [u0, v0, u1, v1]})
json.dump(uvmap, open(os.path.join(OUT, "data", "palette_uv_map.json"), "w"), indent=1)


def r3(v, nd=4):
    return [round(float(c), nd) for c in v]


def roblox_pos(p):
    return [round(-p[0], 4), round(p[2], 4), round(p[1], 4)]


def logical(p):
    return [round(float(p[0]), 4), round(float(-p[1]), 4), round(float(p[2]), 4)]


RESULT = {"bounds_body": {"min": r3(lo), "max": r3(hi), "height": round(hi.z - lo.z, 4)}, "head_bounds": {"min": r3(head_lo), "max": r3(head_hi)},
          "feet_min_h": round(ft_lo.z, 5), "tris_body": body_tris, "tris_props": prop_tris, "tris_total": body_tris + sum(prop_tris.values()),
          "per_part_bounds_blender": bounds_all, "audit": AUDIT, "symmetry": SYM, "arm_lengths": lens, "axes": AXES, "clearance": CLEAR,
          "joint_overlaps": JOINT_GAPS, "pose_bones_identity": POSE_IDENTITY, "meshes": len(PARTS)}
json.dump(RESULT, open(os.path.join(OUT, "data", "actual_mesh_statistics.json"), "w"), indent=1)
CENTRES = {}
BBOXES = {}
for k in PARTS:
    a_, b_ = world_bounds([PARTS[k].obj])
    CENTRES[k] = [round(float((a_[i] + b_[i]) / 2), 6) for i in range(3)]
    BBOXES[k] = {"size": [round(float(b_[i] - a_[i]), 7) for i in range(3)], "centre": [round(float((a_[i] + b_[i]) / 2), 7) for i in range(3)]}
json.dump(BBOXES, open(os.path.join(OUT, "data", "part_bboxes_blender.json"), "w"), indent=1)
JOINTS_BL = {k: [round(float(v[0]), 6), round(float(v[1]), 6), round(float(v[2]), 6)] for k, v in JV.items()}
json.dump({"asset": "BusinessDad_Review", "units": "studs", "height_target": 6.40, "height_built": RESULT["bounds_body"]["height"], "joints_blender": JOINTS_BL, "part_bbox_centres_blender": CENTRES,
           "tables": {"torso_rows_D": TORSO, "skull_rows": SKULL, "nose_rows": NOSE, "hair_cap_rows": HC}, "right_bend_hint": list(RHINT), "left_bend_hint": list(LHINT), "L1_L2": [L1, L2],
           "elbow_contours": {k: [list(map(float, p)) for p in v] for k, v in ELBOW_RING.items()}, "palette": [{"index": i, "name": n_, "hex": h_} for i, (n_, h_, _) in enumerate(PAL)],
           "counts": {"body_tris": body_tris, "prop_tris": prop_tris}, "measured": RESULT},
          open(os.path.join(OUT, "data", "construction_spec_actual.json"), "w"), indent=1)
json.dump({"pose": "static pocket/phone pose (rest pose == pose)", "joints_logical_XFH": {k: list(v) for k, v in JOINTS.items()}, "joints_blender": JOINTS_BL,
           "grips": {"PhoneGrip": {"from": "LeftHand", "to": "Phone", "centre_logical_XFH": list(PHONE_LOGICAL), "yaw_deg": PHONE_YAW, "roll_deg": PHONE_ROLL}},
           "right_hand": "RightHand is built along the forearm direction and rests at the trouser pocket (part of the RightHand mesh, no prop)",
           "watch": "gold watch baked into the LeftHand mesh (bracelet + bezel + dial), cannot detach"},
          open(os.path.join(OUT, "data", "joints_pose_grips.json"), "w"), indent=1)
json.dump({"asset": "BusinessDad_Review", "components": COMP_LOG,
           "part_totals": {k: {"components": len(v.comps), "tris": AUDIT[k]["tris"], "verts": AUDIT[k]["verts"]} for k, v in PARTS.items()},
           "mesh_names": {k: v.geo for k, v in PARTS.items()}}, open(os.path.join(OUT, "data", "component_registry.json"), "w"), indent=1)
RIG = {"asset": "BusinessDad_Review", "frame": {"logical": "(X,F,H) anatomical RIGHT = -X, forward = +F", "blender": "(X,-F,H)", "roblox_position": "(-X, H, -F)"},
       "bones": [{"name": n, "parent": p, "head_logical": logical(h), "tail_logical": logical(t), "head_roblox": roblox_pos(h)} for n, p, h, t in BONES],
       "joints_logical": {k: list(v) for k, v in JOINTS.items()},
       "grips": {"PhoneGrip": {"joint": "LeftHand -> Phone", "centre_logical": list(PHONE_LOGICAL)}},
       "weights": "100% own bone (rigid); Phone -> LeftHand (prop exported as a separate mesh without armature)",
       "part_origin_logical": {k: logical(v.joint) for k, v in PARTS.items()}, "part_bbox_centres_blender": CENTRES, "joints_blender": JOINTS_BL, "pose": "static pose built directly (pose bones identity)"}
json.dump(RIG, open(os.path.join(OUT, "data", "rig_manifest.json"), "w"), indent=1)
print("RESULT", json.dumps({k: RESULT[k] for k in ("bounds_body", "tris_body", "tris_props", "symmetry", "arm_lengths", "axes", "pose_bones_identity")}))

PREVIEW = "--preview" in sys.argv
if NORENDER:
    sys.exit(0)

# ----------------------------------------------------------------------------------------------
# cameras / light / render helpers (real Blender renders of the built scene)
# ----------------------------------------------------------------------------------------------
world = bpy.data.worlds.new("BD_World")
SCENE.world = world
world.use_nodes = True
_wn = world.node_tree.nodes
_wl = world.node_tree.links
_bg_a = _wn["Background"]
_bg_a.inputs[0].default_value = (0.90, 0.88, 0.84, 1.0)
_bg_a.inputs[1].default_value = 0.66
_bg_b = _wn.new("ShaderNodeBackground")
_bg_b.inputs[0].default_value = (0.94, 0.91, 0.86, 1.0)      # backdrop #F0E8DC-like
_bg_b.inputs[1].default_value = 1.0
_lp = _wn.new("ShaderNodeLightPath")
_mix = _wn.new("ShaderNodeMixShader")
_wl.new(_lp.outputs["Is Camera Ray"], _mix.inputs[0])
_wl.new(_bg_a.outputs[0], _mix.inputs[1])
_wl.new(_bg_b.outputs[0], _mix.inputs[2])
_wl.new(_mix.outputs[0], _wn["World Output"].inputs["Surface"])
sun_d = bpy.data.lights.new("BD_Key", 'SUN')
sun_d.energy = 1.8
sun = bpy.data.objects.new("BD_Key", sun_d)
SCENE.collection.objects.link(sun)
sun.rotation_euler = (math.radians(52), math.radians(8), math.radians(-38))
fill_d = bpy.data.lights.new("BD_Fill", 'SUN')
fill_d.energy = 0.55
fill_d.use_shadow = False
fill = bpy.data.objects.new("BD_Fill", fill_d)
SCENE.collection.objects.link(fill)
fill.rotation_euler = (math.radians(60), 0, math.radians(140))
cam_d = bpy.data.cameras.new("BD_Cam")
CAM = bpy.data.objects.new("BD_Cam", cam_d)
SCENE.collection.objects.link(CAM)
SCENE.camera = CAM
SCENE.render.engine = 'BLENDER_EEVEE'
SCENE.eevee.taa_render_samples = 8 if QUICK else 32
SCENE.render.image_settings.file_format = 'PNG'
SCENE.view_settings.view_transform = 'Standard'
SCENE.render.film_transparent = False

FLATM = bpy.data.materials.new("BD_Flat")
FLATM.use_nodes = True
FLATM.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.42, 0.42, 0.44, 1.0)
FLATM.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0


def cam_persp(loc, target, lens=70.0):
    CAM.location = V(loc)
    CAM.rotation_euler = (V(target) - V(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.type, cam_d.lens, cam_d.sensor_width = 'PERSP', lens, 36.0


def cam_ortho(loc, target, scale, roll_deg=0.0):
    CAM.location = V(loc)
    q = (V(target) - V(loc)).to_track_quat('-Z', 'Y')
    CAM.rotation_euler = q.to_euler()
    if roll_deg:
        CAM.rotation_euler = (q @ Quaternion((0, 0, -1), math.radians(roll_deg))).to_euler()
    cam_d.type, cam_d.ortho_scale = 'ORTHO', scale
    cam_d.clip_start, cam_d.clip_end = 0.1, 200.0


def orbit(target, dist, az_deg, el_deg):
    az, el = math.radians(az_deg), math.radians(el_deg)
    t = V(target)
    return t + V((dist * math.sin(az) * math.cos(el), -dist * math.cos(az) * math.cos(el), dist * math.sin(el)))


RENDERED = []
RDIR = os.path.join(OUT, "renders")


def shot(name, loc, target, res=(900, 1000), lens=70.0, ortho=None, show_only=None, hide=(), flat=False, roll=0.0):
    for pm in PARTS.values():
        vis = (show_only is None or pm.runtime in show_only) and pm.runtime not in hide
        pm.obj.hide_render = not vis
    bpy.context.view_layer.material_override = FLATM if flat else None
    SCENE.render.resolution_x, SCENE.render.resolution_y = res
    if ortho:
        cam_ortho(loc, target, ortho, roll)
    else:
        cam_persp(loc, target, lens)
    SCENE.render.filepath = os.path.join(RDIR, name)
    bpy.ops.render.render(write_still=True)
    bpy.context.view_layer.material_override = None
    RENDERED.append(name)
    print("RENDERED", name)


# matching camera: orthographic, 385x425 crop frame of the reference (figure y13..y420 of 425 = 6.40 studs -> ortho scale 6.683, target H3.26), azimuth tuned to the reference turn
CAMCFG = {"type": "ORTHO", "target_h": 3.26, "azimuth_deg": -18.0, "elevation_deg": 5.0, "ortho_scale": 425.0 / 407.0 * 6.40, "res": [385, 425],
          "note": "reference crop 385x425 at x750..1135, y525..950 of the 1536x1024 sheet; 63.6 px per stud"}
if os.path.exists(os.path.join(HERE, "inputs", "camera_tuned.json")):
    CAMCFG.update(json.load(open(os.path.join(HERE, "inputs", "camera_tuned.json"))))
MT = V((0, 0, CAMCFG["target_h"]))
MATCH_LOC = orbit(MT, 40, CAMCFG["azimuth_deg"], CAMCFG["elevation_deg"])
json.dump(CAMCFG, open(os.path.join(OUT, "data", "camera.json"), "w"), indent=1)
K = 3
cam_d.shift_x = CAMCFG.get("shift_x", 0.0)
shot("match_view_%dx%d.png" % (CAMCFG["res"][0] * K, CAMCFG["res"][1] * K), MATCH_LOC, MT, res=(CAMCFG["res"][0] * K, CAMCFG["res"][1] * K), ortho=CAMCFG["ortho_scale"])
cam_d.shift_x = 0.0
if PREVIEW:
    T = V((0, 0, 3.25))
    shot("pv_front.png", orbit(T, 40, 0, 0), T, res=(700, 900), ortho=7.0)
    shot("pv_34R.png", orbit(T, 40, -35, 8), T, res=(700, 900), ortho=7.0)
    shot("pv_34L.png", orbit(T, 40, 35, 8), T, res=(700, 900), ortho=7.0)
    shot("pv_back.png", orbit(T, 40, 180, 0), T, res=(700, 900), ortho=7.0)
    shot("pv_Lside.png", orbit(T, 40, 90, 0), T, res=(700, 900), ortho=7.0)
    HT = V((0, -.2, 5.45))
    shot("pv_face.png", orbit(HT, 20, -10, 3), HT, res=(900, 900), ortho=3.0)
    sys.exit(0)

# ---- full review set: all main views at identical pixel height (700x900, ortho 7.0, same target) ----
T = V((0, 0, 3.25))
SC = 7.0
FULL = (700, 900)
shot("full_front.png", orbit(T, 40, 0, 0), T, res=FULL, ortho=SC)
shot("full_back.png", orbit(T, 40, 180, 0), T, res=FULL, ortho=SC)
shot("full_left_side.png", orbit(T, 40, 90, 0), T, res=FULL, ortho=SC)      # character's left (phone side)
shot("full_right_side.png", orbit(T, 40, -90, 0), T, res=FULL, ortho=SC)    # character's right (pocket side)
shot("full_front_left_34.png", orbit(T, 40, 35, 8), T, res=FULL, ortho=SC)
shot("full_front_right_34.png", orbit(T, 40, -35, 8), T, res=FULL, ortho=SC)
shot("full_top.png", orbit(T, 40, 20, 70), T, res=FULL, ortho=SC)
shot("full_low_angle.png", orbit(T, 40, -25, -22), T, res=FULL, ortho=SC)
# close-ups
HT = V((0, -.2, 5.45))
shot("close_face_front.png", orbit(HT, 20, 0, 3), HT, res=(900, 900), ortho=3.0)
shot("close_face_34_right.png", orbit(HT, 20, -30, 5), HT, res=(900, 900), ortho=3.0)
shot("close_face_34_left.png", orbit(HT, 20, 30, 5), HT, res=(900, 900), ortho=3.0)
shot("close_hair_top.png", orbit(HT, 20, 20, 55), HT, res=(900, 900), ortho=3.0)
shot("close_hair_back.png", orbit(HT, 20, 180, 10), HT, res=(900, 900), ortho=3.0)
shot("close_moustache.png", orbit(V((0, -1.1, 5.2)), 20, 0, 3), V((0, -1.1, 5.2)), res=(900, 900), ortho=1.6)
PT = V((2.35, -1.5, 4.55))
shot("close_phone_front.png", orbit(PT, 20, 0, 4), PT, res=(900, 900), ortho=2.8)
shot("close_phone_back_cameras.png", orbit(PT, 20, -20, 4), PT, res=(900, 900), ortho=2.8)
shot("close_phone_side.png", orbit(PT, 20, 90, 4), PT, res=(900, 900), ortho=2.8)
shot("close_phone_behind_screen.png", orbit(PT, 20, 180, 6), PT, res=(900, 900), ortho=2.8, hide=("Head", "UpperTorso"))
WT = V((2.15, -1.2, 3.95))
shot("close_watch_cuff.png", orbit(WT, 20, -10, 12), WT, res=(900, 900), ortho=2.4)
shot("close_watch_top.png", orbit(WT, 20, 20, 60), WT, res=(900, 900), ortho=2.4)
TT = V((0, -.6, 3.85))
shot("close_tie_bar.png", orbit(TT, 20, 0, 4), TT, res=(900, 900), ortho=2.6)
shot("close_pocket_square.png", orbit(V((1.25, -.7, 4.05)), 20, 0, 4), V((1.25, -.7, 4.05)), res=(900, 900), ortho=1.8)
shot("close_belt_buckle.png", orbit(V((0, -.7, 2.65)), 20, 0, 4), V((0, -.7, 2.65)), res=(900, 900), ortho=1.8)
RT = V((-1.55, -.5, 2.45))
shot("close_right_hand_pocket.png", orbit(RT, 20, -25, 8), RT, res=(900, 900), ortho=2.8)
shot("close_right_hand_front.png", orbit(RT, 20, 0, 4), RT, res=(900, 900), ortho=2.8)
shot("close_right_arm_side.png", orbit(V((-2.0, -.3, 3.5)), 20, -90, 4), V((-2.0, -.3, 3.5)), res=(900, 900), ortho=3.6)
FT_ = V((0, -.4, .45))
shot("close_shoes_front.png", orbit(FT_, 20, 0, 6), FT_, res=(900, 700), ortho=3.8, show_only=("RightFoot", "LeftFoot", "RightLowerLeg", "LeftLowerLeg"))
shot("close_shoes_34.png", orbit(FT_, 20, -35, 14), FT_, res=(900, 700), ortho=3.8, show_only=("RightFoot", "LeftFoot", "RightLowerLeg", "LeftLowerLeg"))
shot("close_shoes_top.png", orbit(FT_, 20, 0, 85), FT_, res=(900, 700), ortho=3.8, show_only=("RightFoot", "LeftFoot"))
shot("close_shoes_sole.png", orbit(FT_, 20, 0, -85), FT_, res=(900, 700), ortho=3.8, show_only=("RightFoot", "LeftFoot"))
shot("close_shoe_right_side.png", orbit(V((-.93, -.4, .45)), 20, -90, 4), V((-.93, -.4, .45)), res=(900, 700), ortho=3.0, show_only=("RightFoot", "RightLowerLeg"))
shot("close_shoe_left_side.png", orbit(V((.93, -.4, .45)), 20, 90, 4), V((.93, -.4, .45)), res=(900, 700), ortho=3.0, show_only=("LeftFoot", "LeftLowerLeg"))
shot("close_collar_neck_front.png", orbit(V((0, -.6, 4.75)), 20, 0, 6), V((0, -.6, 4.75)), res=(900, 900), ortho=2.6)
shot("close_jacket_back.png", orbit(V((0, 0.6, 3.6)), 20, 180, 4), V((0, .6, 3.6)), res=(900, 900), ortho=4.2)
print("ALL_RENDERS_DONE", len(RENDERED))
