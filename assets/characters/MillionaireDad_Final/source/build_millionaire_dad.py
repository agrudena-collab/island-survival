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
EXP_COLL = bpy.data.collections.new("EXPORT_MillionaireDad")
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
sh_ivory = shade("Ivory")
sh_gold = shade("Gold")
sh_hair = shade("Hair")
sh_shoe = shade("ShoeWhite")
sh_case = shade("Case")
sh_belt = shade("Belt")
sh_shirt = shade("Shirt")


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


# ---------------------------------------------------------------------------------------------------------------------------
# PARAMETERS. Layout decided against the crop (63.75 px per stud: A = 408 px hair top..sole = 6.40 PROJECT CONVENTION, not a measurement);
# the crop sits at (1110,530) on the sheet, so sheet landmarks A..E map to crop pixels by subtracting that origin. Hidden surfaces are neutral guesses.
# ---------------------------------------------------------------------------------------------------------------------------
L1, L2 = 1.00, 0.85       # revision 5: shorter, almost straight blocky arms (the source stacks shoulder block, forearm block, cuff and fist vertically)
RHINT = (-1.0, -0.15, 0.0)          # right elbow OUT (not back): the forearm and the case hang almost vertically
LHINT = (1.0, -0.7, -0.2)            # left elbow out and back, the fist rests at the hip
JOINTS = {
    "Root": (0, 0, 2.35), "Waist": (0, 0, 2.80), "Neck": (0, 0, 4.55),
    "RightShoulder": (-1.85, 0, 4.25), "RightWrist": (-2.50, 0.10, 2.70),
    "LeftShoulder": (1.85, 0, 4.25), "LeftWrist": (1.95, 0.75, 2.95),
    "RightHip": (-0.88, 0, 2.25), "LeftHip": (0.88, 0, 2.25),
    "RightKnee": (-0.88, 0.02, 1.30), "LeftKnee": (0.88, 0.02, 1.30),
    "RightAnkle": (-0.88, 0.02, 0.80), "LeftAnkle": (0.88, 0.02, 0.80),
}
RHAND_DIR = V((0.0, -0.06, -1.0)).normalized()                 # Blender coordinates; the case hand hangs straight down
LHAND_DIR = V((-0.15, -0.45, -0.88)).normalized()              # Blender coordinates; the left fist rests on the hip (down, inward, forward)


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

# torso rows (H, W, Ffront, Fback signed, bevel); D coordinates (front negative); long jacket to H2.00
_TORSO = [(2.00, 3.00, .74, -.68, .13), (2.40, 2.88, .74, -.68, .13), (2.80, 2.90, .76, -.70, .14), (3.30, 3.10, .80, -.72, .16),
          (3.85, 3.25, .80, -.72, .17), (4.30, 3.10, .70, -.68, .16), (4.55, 2.80, .58, -.62, .14)]
TORSO = [(h, w, -ff, -fb, c) for h, w, ff, fb, c in _TORSO]
TORSO_TOP = TORSO[-1][0]
TORSO_BOT = TORSO[0][0]
LOWER_ROWS = [r for r in TORSO if r[0] <= 2.80 + 1e-9]
UPPER_ROWS = [r for r in TORSO if r[0] >= 2.80 - 1e-9]


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
# torso (long ivory jacket, black open-neck shirt window, gold buttons, pocket square), belt, pelvis, trousers, chunky shoes
# ----------------------------------------------------------------------------------------------
FLOOR_IN = 0.10                                   # depth of the shirt / trouser window below the jacket surface
OPEN_UP = [(-1.00, 4.90), (-.82, 4.35), (-.66, 3.75), (-.57, 3.05), (-.56, 2.80), (.56, 2.80), (.57, 3.05), (.66, 3.75), (.82, 4.35), (1.00, 4.90)]
OPEN_LOW = [(-.56, 2.80), (-.58, 1.90), (.58, 1.90), (.56, 2.80)]


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


# ---- UpperTorso: ivory jacket shell with the V window (black shirt floor), lapels, collar flaps, buttons, pocket square -------------------------
ut = PM("UpperTorso", JV["Waist"])
bm = loft_bm([row_ring(r) for r in UPPER_ROWS], sh_ivory)
bm = cut_window(bm, OPEN_UP, "Shirt", "IvoryShadow")
ut.append_bm("UT_jacket_shell", bm, None, {"recipe": "7-row octagon loft, V window (floor .10 below the surface) for the black open-neck shirt", "class": "observed+extrapolated"})
bm.free()
for s, nm in ((-1, "R"), (1, "L")):
    lap = [(s * 1.00, 4.52), (s * .82, 4.35), (s * .66, 3.75), (s * .57, 3.05), (s * .90, 3.10), (s * 1.02, 3.75), (s * 1.24, 4.28), (s * 1.40, 4.50)]      # revision 5: lapels end below the chin, no vertical sheet above the torso
    layered_plate(ut, "UT_lapel_" + nm, lap, tfront, [(+.05, 1.0, 1.0), (-.075, 1.0, 1.0)], sh_const("IvoryLight"), {"recipe": "angular notch lapel plate .075 proud", "class": "observed"})
    layered_plate(ut, "UT_lapel_peak_" + nm, [(s * 1.08, 4.46), (s * 1.38, 4.48), (s * 1.30, 4.34), (s * 1.12, 4.30)], tfront, [(+.05, 1.0, 1.0), (-.105, 1.0, 1.0)], sh_const("Ivory"), {"recipe": "lapel peak facet", "class": "extrapolated"})
    flap = [(s * .12, 4.40), (s * .74, 4.42), (s * .62, 3.95), (s * .34, 4.12)]      # shirt collar flaps lie on the chest below the chin (no intersection with the head)
    layered_plate(ut, "UT_collar_flap_" + nm, flap, floor_front, [(+.03, 1.0, 1.0), (-.08, 1.0, 1.0)], sh_const("ShirtLight"), {"recipe": "open black shirt collar flap on the shirt floor", "class": "observed"})
layered_plate(ut, "UT_placket", [(-.035, 4.40), (.035, 4.40), (.035, 2.80), (-.035, 2.80)], floor_front, [(+.03, 1.0, 1.0), (-.045, 1.0, 1.0)], sh_const("ShirtLight"), {"recipe": "shirt placket strip", "class": "extrapolated"})
for k, hh in enumerate((3.80, 3.27)):
    fy = floor_front(0, hh)
    cyl_y(ut, "UT_shirt_button_%d" % (k + 1), 0.0, hh, fy + .02, fy - .075, .075, 10, sh_gold, {"recipe": "gold shirt button (two visible in the source)", "class": "observed"})
for k, sx in enumerate((-1, 1)):
    bx, bh = sx * .74, 3.05
    fy = tfront(bx, bh)
    cyl_y(ut, "UT_jacket_button_%d" % (k + 1), bx, bh, fy + .03, fy - .10, .115, 12, sh_gold, {"recipe": "gold jacket button on the front panel edge", "class": "observed"})
layered_plate(ut, "UT_pocket_welt", [(1.00, 3.92), (1.50, 3.92), (1.50, 3.87), (1.00, 3.87)], tfront, [(+.05, 1.0, 1.0), (-.055, 1.0, 1.0)], sh_const("IvoryShadow"), {"recipe": "breast pocket welt (anatomical left)", "class": "observed"})
layered_plate(ut, "UT_pocket_square", [(1.06, 3.90), (1.46, 3.90), (1.40, 4.16), (1.27, 4.00), (1.14, 4.18)], tfront, [(+.05, 1.0, 1.0), (-.10, 1.0, 1.0)], sh_gold, {"recipe": "small folded gold pocket square, two points", "class": "observed"})

# ---- LowerTorso: long jacket fronts (H2.00..2.80) with the trouser window, belt, gold buckle, hip flaps, pelvis ---------------------------------
lt = PM("LowerTorso", JV["Root"])
bm = loft_bm([row_ring(r) for r in LOWER_ROWS], sh_ivory)
bm = cut_window(bm, OPEN_LOW, "Ivory", "IvoryShadow")
lt.append_bm("LT_jacket_skirt", bm, None, {"recipe": "long jacket skirt rows H2.00..2.80 with the trouser window", "class": "observed+extrapolated"})
bm.free()
PEL = [(1.85, 2.60, .56, -.52, .14), (2.00, 3.00, .70, -.64, .14), (2.15, 3.00, .72, -.66, .13), (2.35, 2.90, .70, -.64, .12)]
loft(lt, "LT_pelvis_trousers", [row_ring((h, w, -ff, -fb, c)) for h, w, ff, fb, c in PEL], sh_ivory, meta={"recipe": "trouser seat block H1.85..2.35", "class": "extrapolated"})
layered_plate(lt, "LT_belt", [(-.95, 2.83), (.95, 2.83), (.95, 2.52), (-.95, 2.52)], floor_front, [(+.04, 1.0, 1.0), (-.045, 1.0, 1.0)], sh_belt, {"recipe": "dark brown belt band H2.52..2.83 across the window", "class": "observed"})
BUCK_F = floor_front(0, 2.67) - .045
for nm, x0, x1, h0, h1 in (("L", -.34, -.22, 2.49, 2.86), ("R", .22, .34, 2.49, 2.86), ("T", -.34, .34, 2.74, 2.86), ("B", -.34, .34, 2.49, 2.61)):
    solid_box(lt, "LT_buckle_%s" % nm, x0, x1, BUCK_F - .07, BUCK_F + .05, h0, h1, "Gold" if nm in "LR" else "GoldLight", {"recipe": "rectangular gold buckle frame (4 bars)", "class": "observed"})
solid_box(lt, "LT_buckle_prong", -.04, .04, BUCK_F - .05, BUCK_F + .05, 2.58, 2.78, "GoldShadow", {"recipe": "buckle tongue", "class": "extrapolated"})
solid_box(lt, "LT_fly_seam", -.012, .012, floor_front(0, 2.2) - .02, floor_front(0, 2.2) + .03, 1.92, 2.50, "IvoryShadow", {"recipe": "fly seam", "class": "extrapolated"})
for sx, nm in ((-1, "R"), (1, "L")):
    layered_plate(lt, "LT_pocket_flap_" + nm, [(sx * .75, 2.50), (sx * 1.38, 2.50), (sx * 1.38, 2.28), (sx * .75, 2.28)], tfront, [(+.05, 1.0, 1.0), (-.05, 1.0, 1.0)], sh_const("IvoryShadow"), {"recipe": "hip pocket flap", "class": "extrapolated"})
solid_box(lt, "LT_back_vent", -.014, .014, tback(0, 2.4) - .02, tback(0, 2.4) + .028, 2.02, 2.78, "IvoryDeep", {"recipe": "centre back vent seam (inferred, neutral)", "class": "extrapolated"})

# ---- legs: wide ivory trousers (UpperLeg), straight leg + turn-up cuff (LowerLeg), chunky white shoes on dark soles (Foot) -------------------
LEGX = 0.88
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    hip, knee, ank = JV[side + "Hip"], JV[side + "Knee"], JV[side + "Ankle"]
    ul = PM(side + "UpperLeg", hip)
    rings = [ring8(.70, -.72, .72, .12, s * LEGX, 0, 1.25), ring8(.715, -.74, .74, .12, s * LEGX, 0, 1.38), ring8(.74, -.76, .76, .12, s * LEGX, 0, 2.30), ring8(.70, -.72, .72, .10, s * LEGX, 0, 2.42)]
    loft(ul, "UL_trouser_" + side, rings, sh_ivory, meta={"recipe": "wide trouser leg W1.35 x D1.40, hip hidden under the jacket", "class": "observed+extrapolated"})
    solid_box(ul, "UL_crease_" + side, s * LEGX - .016, s * LEGX + .016, -.735, -.705, 1.45, 2.26, "IvoryShadow", {"recipe": "front trouser crease", "class": "extrapolated"})
    ll = PM(side + "LowerLeg", knee)
    secs = [(1.40, .725, .73), (1.10, .715, .72), (0.92, .705, .71), (0.76, .705, .71)]
    loft(ll, "LL_trouser_" + side, [ring8(a, -.02 - d, -.02 + d, .11, s * LEGX, 0, h) for h, a, d in secs], sh_ivory, meta={"recipe": "straight trouser leg", "class": "observed+extrapolated"})
    solid_box(ll, "LL_crease_" + side, s * LEGX - .016, s * LEGX + .016, -.755, -.725, 1.00, 1.30, "IvoryShadow", {"recipe": "front crease over the shin", "class": "extrapolated"})
    cuff = [ring8(.74, -.02 - .75, -.02 + .75, .10, s * LEGX, 0, 0.76)] + [ring8(.765, -.02 - .765, -.02 + .765, .11, s * LEGX, 0, h) for h in (0.80, 1.06, 1.10)]
    loft(ll, "LL_cuff_" + side, cuff, sh_const("Ivory"), band_tiles={2: "IvoryLight"}, meta={"recipe": "turn-up cuff H.62..0.96, lighter fold edge", "class": "extrapolated"})

    th = s * 6.0
    ft = PM(side + "Foot", ank, xf=rot_xf(ank, th))
    cx = s * LEGX
    sole = [ring8(.72, -1.66, .72, .14, cx, 0, 0.0), ring8(.80, -1.76, .76, .16, cx, 0, .10), ring8(.80, -1.76, .76, .16, cx, 0, .26), ring8(.76, -1.70, .72, .14, cx, 0, .34)]
    loft(ft, "FT_sole_" + side, sole, sh_const("Sole"), band_tiles={1: "SoleLight"}, meta={"recipe": "dark chunky sole slab H0..0.30 (thick, as in the source)", "class": "observed+extrapolated"})

    def ring_xh(f, w, h0, h1, c, cx=cx):
        a = w / 2
        pts = [(-a + c, h0), (a - c, h0), (a, h0 + c), (a, h1 - c), (a - c, h1), (-a + c, h1), (-a, h1 - c), (-a, h0 + c)]
        return [V((cx + x, -f, h)) for x, h in pts]
    UP = [(-.66, .86, 1.46, .20), (-.30, .88, 1.60, .22), (.30, .84, 1.66, .22), (.85, .76, 1.66, .22), (1.22, .68, 1.60, .20), (1.52, .58, 1.42, .17), (1.70, .46, 1.10, .10)]
    loft(ft, "FT_upper_" + side, [ring_xh(f, w, .30, top, c) for f, top, w, c in UP], sh_shoe, meta={"recipe": "oversized chunky white shoe block, heel/collar H.86..92 falling to a faceted toe H.42", "class": "observed+extrapolated"})
    patch_box(ft, "FT_top_facet_" + side, cx, .70, .80, .90, 1.20, .02, "ShoeLight", embed=.01, meta={"recipe": "flat lighter top facet", "class": "observed"})
    solid_box(ft, "FT_toe_band_" + side, cx - .52, cx + .52, -1.64, -1.58, .34, .52, "ShoeShadow", {"recipe": "toe cap shadow band", "class": "extrapolated"})
    solid_box(ft, "FT_heel_band_" + side, cx - .62, cx + .62, .60, .72, .30, .58, "ShoeShadow", {"recipe": "heel block band", "class": "extrapolated"})
# ----------------------------------------------------------------------------------------------
# arms: broad blocky ivory sleeves (shared mitre contour at the elbow), black shirt cuffs, gold sleeve buttons, fists; left wrist watch
# ----------------------------------------------------------------------------------------------
UPPER_SEC = [(0.0, 1.70, 1.50), (.30, 1.76, 1.54), (.75, 1.56, 1.40), (1.0, 1.44, 1.30)]
LOWER_SEC = [(0.0, 1.38, 1.30), (.50, 1.32, 1.24), (.78, 1.26, 1.20), (1.0, 1.24, 1.18)]
ARM_C = .24                       # large chamfer: blocky, faceted shoulders as in the source
SLEEVE_END = .76
OVERLAP = .04
ARM_AX = {}
ELBOW_RING = {}
HAND_AX = {}
HAND_LEN = .90
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
    loft(ua, "UA_sleeve_" + side, rings, sh_ivory, meta={"recipe": "broad blocky sleeve W1.60->1.38, chamfer .24, elbow end = shared mitre contour", "class": "observed+extrapolated"})
    abox(ua, "UA_button_" + side, ax1, .74, .74 + .06 / ax1.L, s * (UPPER_SEC[-1][1] / 2 - .02), s * (UPPER_SEC[-1][1] / 2 + .05), -.10, .10, "Gold", {"recipe": "small gold dot on the outer sleeve (source: right sleeve)", "class": "observed"})
    la = PM(side + "LowerArm", E)
    ts = [.14, .50, SLEEVE_END]
    lr = [ax2.ring(t, *sec_at(LOWER_SEC, t), ARM_C) for t in ts]
    best = min(range(8), key=lambda sh: sum((K[k] - lr[0][(k + sh) % 8]).length for k in range(8)))
    lr = [[r[(k + best) % 8] for k in range(8)] for r in lr]
    loft(la, "LA_sleeve_" + side, [K] + lr, sh_ivory, meta={"recipe": "forearm sleeve block W1.38->1.26 ends at t=.76; ring order shift %d" % best, "class": "observed+extrapolated"})
    cuffs = [ax2.ring(t, w, d, .12) for t, w, d in ((SLEEVE_END - .03, 1.04, .98), (SLEEVE_END + .03, 1.04, .98), (1.0, 1.04, .98), (1.0 + OVERLAP / ax2.L, .96, .90))]
    loft(la, "LA_cuff_" + side, cuffs, sh_shirt, meta={"recipe": "black shirt cuff W1.04 x .98, ~.29 visible beyond the sleeve", "class": "observed"})
    abox(la, "LA_button_" + side, ax2, .52, .52 + .06 / ax2.L, s * (sec_at(LOWER_SEC, .52)[0] / 2 - .02), s * (sec_at(LOWER_SEC, .52)[0] / 2 + .05), -.10, .10, "Gold", {"recipe": "small gold sleeve dot", "class": "observed"})

# ---- hands: closed fists built along their own axis (right: hanging, holds the case handle; left: rests on the hip) ------------------------------
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    Wp = JV[side + "Wrist"]
    dirv = (JV[side + "Wrist"] - JV[side + "Elbow"]).normalized()      # the fist continues the forearm axis: cuff and fist exit the sleeve in line (revision 5)
    hx = AxisG(Wp, Wp + dirv * HAND_LEN)
    HAND_AX[side] = hx
    hp = PM(side + "Hand", Wp)
    rings = [hx.ring(-.06, .72, .64, .10), hx.ring(.20, .76, .68, .11), hx.ring(.30, 1.00, .94, .15), hx.ring(.94, 1.02, .94, .16), hx.ring(1.0, .86, .80, .13)]
    loft(hp, "HAND_fist_" + side, rings, sh_skin_arm, meta={"recipe": "square closed fist 1.02 x .94 x %.2f, wrist neck .72 x .64" % (HAND_LEN * .64), "class": "observed+extrapolated"})
    for k, t in enumerate((.50, .64, .78)):
        abox(hp, "HAND_crease_%s_%d" % (side, k + 1), hx, t, t + .028, -.42, .42, .465, .485, "SkinShadow", {"recipe": "finger crease", "class": "observed"})
    abox(hp, "HAND_knuckle_band_" + side, hx, .34, .94, -.50, .50, .455, .475, "SkinLight", {"recipe": "lighter finger-top band", "class": "extrapolated"})
    if side == "Left":
        abox(hp, "HAND_thumb_Left", hx, .44, .90, -s * .54, -s * .38, -.34, .12, "SkinLight", {"recipe": "thumb block on the inner side, overlaps the fist", "class": "extrapolated"})

# ---- left wrist watch (visible in the source on the wrist at the hip): gold octagonal case, cream dial, ticks, hands, crown, black strap ------------
hxl = HAND_AX["Left"]
lh = PARTS["LeftHand"]
WATCH_NORMAL = V((-0.35, -0.90, 0.20))        # Blender coords: forward and slightly towards the midline - the dial faces the source camera (right-front)
_w = (WATCH_NORMAL - hxl.A * WATCH_NORMAL.dot(hxl.A)).normalized()
hxw = AxisG(hxl.P0, hxl.P1)
hxw.W = _w
hxw.U = _w.cross(hxl.A).normalized()
WT_C = .20                                    # case centre along the hand axis (fraction of its length)


def oct_ring(ax, tc, r, y, rot=22.5):
    return [ax.pt(tc + r * math.cos(math.radians(rot + 45 * k)) / ax.L, r * math.sin(math.radians(rot + 45 * k)), y) for k in range(8)]


def bar(ax, cid, tc, xc, length, width, ang_deg, y0, y1, tile):
    a_ = math.radians(ang_deg)
    dt, dx = math.cos(a_), math.sin(a_)
    nt, nx = -dx, dt
    pts = []
    for sl, sw in ((-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)):
        pts.append((tc + (dt * sl * length + nt * sw * width) / ax.L, xc + dx * sl * length + nx * sw * width))
    r0 = [ax.pt(t_, x_, y0) for t_, x_ in pts]
    r1 = [ax.pt(t_, x_, y1) for t_, x_ in pts]
    loft(lh, cid, [r0, r1], tile, meta={"recipe": "watch hand / tick", "class": "extrapolated"})


loft(lh, "WATCH_strap", [hxl.ring(t, .84, .78, .13) for t in (-.03, .06, .15, .24, .33, .40)], sh_const("Strap"), band_tiles={0: "CaseLight", 2: "CaseLight", 4: "CaseLight"}, meta={"recipe": "black strap around the wrist neck W.84 x .78 (source shows a black strap)", "class": "observed"})
loft(lh, "WATCH_case", [oct_ring(hxw, WT_C, .40, .36), oct_ring(hxw, WT_C, .40, .50), oct_ring(hxw, WT_C, .35, .58)], sh_gold, meta={"recipe": "octagonal gold case r.40, bevelled top", "class": "observed"})
loft(lh, "WATCH_dial", [oct_ring(hxw, WT_C, .27, .56), oct_ring(hxw, WT_C, .27, .60)], "WatchDial", meta={"recipe": "cream dial (dial design is a proposal)", "class": "design-proposal"})
for k in range(12):
    a_ = math.radians(30 * k)
    big = k % 3 == 0
    bar(hxw, "WATCH_tick_%d" % k, WT_C + .215 * math.cos(a_) / hxl.L, .215 * math.sin(a_), .06 if big else .035, .03 if big else .02, math.degrees(a_), .595, .62, "WatchTick")
bar(hxw, "WATCH_hand_hour", WT_C, 0.0, .22, .035, 60, .60, .625, "GoldShadow")
bar(hxw, "WATCH_hand_minute", WT_C, 0.0, .32, .025, -35, .605, .64, "GoldShadow")
abox(lh, "WATCH_crown", hxw, WT_C - .045, WT_C + .045, .385, .48, .40, .52, "Gold", {"recipe": "crown on the case side", "class": "extrapolated"})
for sg, nm in ((-1, "a"), (1, "b")):
    abox(lh, "WATCH_lug_" + nm, hxw, WT_C + sg * (.40 + .06) / hxl.L - .12 / hxl.L, WT_C + sg * (.40 + .06) / hxl.L + .12 / hxl.L, -.30, .30, .32, .50, "Gold", {"recipe": "lug where the strap meets the case", "class": "extrapolated"})
for k in range(8):
    phi = 45 * k + 22.5
    bar(hxw, "WATCH_bezel_bar_%d" % k, WT_C + .335 * math.cos(math.radians(phi)) / hxl.L, .335 * math.sin(math.radians(phi)), .27, .075, phi + 90, .575, .63, "GoldLight")
# ----------------------------------------------------------------------------------------------
# head: faceted skull, ears, square gold sunglasses with dark lenses (eyes NOT modelled: not established by the source), blocky nose,
# voluminous white moustache with curled tips, broad toothy grin, side-swept silver hair mass with grey facets (no beard)
# ----------------------------------------------------------------------------------------------
hd = PM("Head", JV["Neck"])
SKULL = [(4.42, 1.40, .78, -.70, .22), (4.64, 1.78, .95, -.84, .22), (5.00, 1.92, 1.00, -.88, .22), (5.90, 1.92, 1.00, -.88, .20), (6.05, 1.72, .88, -.80, .18)]
SK_ROWS = [(h, w, -ff, -fb, c) for h, w, ff, fb, c in SKULL]


def skull_D(x, h):
    """D coordinate of the skull front surface (front is negative D)"""
    return front_at(SK_ROWS, min(max(h, SK_ROWS[0][0]), SK_ROWS[-1][0]), x)


# revision 3: the grin is a real pocket cut into the face (depth MOUTH_IN below the surface), teeth sit inside it, the lower lip is a ridge - not a decal on the head
MOUTH_IN = .16
GX = .50                           # revision 4: shorter grin (source teeth span ~0.86 studs)
_xs = [-GX + 2 * GX * k / 12 for k in range(13)]
OPENING = [(x, 4.93 + .08 * (x / GX) ** 2) for x in _xs] + [(x, 4.56 + .18 * (x / GX) ** 2) for x in _xs[::-1]]
bm = loft_bm([ring8(w / 2, -ff, -fb, c, 0, 0, h) for h, w, ff, fb, c in SKULL], sh_skin)
_cut = plate_bm(OPENING, skull_D, [(MOUTH_IN, 1.0, 1.0), (-.40, 1.0, 1.0)], "Mouth")
bm = bm_boolean(bm, _cut)
_cut.free()
hd.append_bm("HD_skull", bm, None, {"recipe": "faceted block head W2.02 x D1.88, chin H4.42 (no beard); grin pocket cut .16 into the face (dark walls/floor)", "class": "observed+extrapolated"})
bm.free()
loft(hd, "HD_neck", cbox(Bl(0, -.02, 4.55), (.92, .82, .52), .10), sh_skin, meta={"recipe": "short neck block inside skull/torso", "class": "extrapolated"})
for s, nm in ((-1, "Right"), (1, "Left")):
    loft(hd, "HD_ear_" + nm, cbox(Bl(s * .985, -.02, 5.04), (.30, .50, .58), .10), sh_skin, meta={"recipe": "ear block", "class": "observed"})
    solid_box(hd, "HD_ear_rim_" + nm, min(s * 1.115, s * 1.150), max(s * 1.115, s * 1.150), -.20, .14, 4.84, 5.26, sh_const("SkinLight"), {"recipe": "ear helix rim", "class": "extrapolated"})
    xo = s * 1.135
    solid_box(hd, "HD_concha_" + nm, min(xo + s * .02, xo - s * .035), max(xo + s * .02, xo - s * .035), -(-.02 + .15), -(-.02 - .15), 4.86, 5.20, sh_const("EarInner"), {"recipe": "ear concha patch", "class": "observed"})


FD = 0.12                          # revision 2: the face features (glasses, nose, moustache) are lifted by this much so the grin has room below the moustache
MSX = 0.72                         # moustache x factor: 0.90 base * 0.90 correction made in the LIVE Blender scene through MCP (moustache wider than the face in the source fit)


def rect(x0, x1, h0, h1):
    return [(x0, h0), (x1, h0), (x1, h1), (x0, h1)]


# square oversized sunglasses: thick gold frames, dark lenses, bridge, temple arms
for s, nm in ((-1, "R"), (1, "L")):
    prism_xh(hd, "HD_lens_" + nm, rect(s * .18, s * .76, 5.12 + FD, 5.60 + FD), .80, 1.075, sh_const("Lens"), {"recipe": "dark square lens .58 x .48 (lens depth is a proposal)", "class": "observed+proposal"})
    prism_xh(hd, "HD_lens_shine_" + nm, [(s * .24, 5.56 + FD), (s * .46, 5.56 + FD), (s * .24, 5.34 + FD)], 1.07, 1.092, sh_const("LensShine"), {"recipe": "lens facet highlight", "class": "extrapolated"})
    prism_xh(hd, "HD_lens_streak_a_" + nm, [(s * .22, 5.50 + FD), (s * .30, 5.50 + FD), (s * .62, 5.18 + FD), (s * .54, 5.18 + FD)] if s > 0 else [(s * .54, 5.18 + FD), (s * .62, 5.18 + FD), (s * .30, 5.50 + FD), (s * .22, 5.50 + FD)], 1.07, 1.092, sh_const("LensShine"), {"recipe": "lens reflection streak", "class": "extrapolated"})
    prism_xh(hd, "HD_lens_streak_b_" + nm, [(s * .42, 5.58 + FD), (s * .46, 5.58 + FD), (s * .72, 5.30 + FD), (s * .68, 5.30 + FD)] if s > 0 else [(s * .68, 5.30 + FD), (s * .72, 5.30 + FD), (s * .46, 5.58 + FD), (s * .42, 5.58 + FD)], 1.07, 1.09, sh_const("LensShine"), {"recipe": "second lens streak", "class": "extrapolated"})
    for k, (x0, x1, h0, h1) in enumerate(((.10, .84, 5.60, 5.72), (.10, .84, 5.00, 5.12), (.10, .18, 5.12, 5.60), (.76, .84, 5.12, 5.60))):
        prism_xh(hd, "HD_frame_%s_%d" % (nm, k + 1), rect(s * x0, s * x1, h0 + FD, h1 + FD), .90, 1.15, sh_gold, {"recipe": "thick gold frame bar", "class": "observed"})
    prism_xh(hd, "HD_frame_inner_top_" + nm, rect(s * .18, s * .76, 5.55 + FD, 5.60 + FD), 1.05, 1.17, sh_const("GoldLight"), {"recipe": "light inner frame bevel", "class": "extrapolated"})
    solid_box(hd, "HD_temple_" + nm, min(s * .955, s * 1.04), max(s * .955, s * 1.04), -.92, .08, 5.44 + FD, 5.56 + FD, "Gold", {"recipe": "gold temple arm from the frame back to the ear", "class": "extrapolated"})
prism_xh(hd, "HD_bridge", rect(-.14, .14, 5.44 + FD, 5.58 + FD), .90, 1.15, sh_gold, {"recipe": "gold nose bridge", "class": "observed"})
NOSE = [(4.93 + FD, .52, 1.16, .70, .12), (5.04 + FD, .70, 1.28, .70, .18), (5.22 + FD, .66, 1.26, .70, .18), (5.36 + FD, .46, 1.12, .70, .12), (5.46 + FD, .30, 1.02, .70, .08)]   # revision 6: bigger, rounder nose
loft(hd, "HD_nose", [ring8(w / 2, -ff, -fb, c, 0, 0, h) for h, w, ff, fb, c in NOSE], sh_nose, meta={"recipe": "blocky warm peach nose, front F1.26", "class": "observed"})

# white moustache: three stacked layers per side (shadow underlayer, body, light top ridge), tips curl outward and up
MP = [(0, 4.84), (.22, 4.76), (.60, 4.74), (1.00, 4.82), (1.25, 5.02), (1.34, 5.28), (1.20, 5.36), (1.08, 5.16), (.84, 5.04), (.55, 5.06), (.25, 5.12), (0, 5.10)]
MS = [(0, 4.82), (.25, 4.74), (.62, 4.72), (1.02, 4.80), (1.20, 4.95), (1.10, 5.0), (.84, 4.92), (.55, 4.94), (.25, 4.98), (0, 4.98)]
MT = [(0, 5.08), (.25, 5.10), (.55, 5.04), (.84, 5.02), (1.06, 5.14), (1.18, 5.32), (1.12, 5.30), (1.00, 5.15), (.82, 5.08), (.55, 5.10), (.25, 5.15), (0, 5.14)]
for s, nm in ((-1, "Right"), (1, "Left")):
    def side_poly(P):
        pts = [(s * x * MSX, h + FD) for x, h in P]
        return pts if s > 0 else pts[::-1]
    prism_xh(hd, "HD_moustache_shadow_" + nm, side_poly(MS), .70, 1.12, sh_const("MoustacheShadow"), {"recipe": "moustache underlayer", "class": "observed"})
    prism_xh(hd, "HD_moustache_" + nm, side_poly(MP), .70, 1.20, sh_const("Moustache"), {"recipe": "voluminous white moustache lobe, tip curls outward and up", "class": "observed"})
    prism_xh(hd, "HD_moustache_top_" + nm, side_poly(MT), 1.14, 1.25, sh_const("MoustacheLight"), {"recipe": "light top ridge", "class": "extrapolated"})

for s_, nm in ((-1, "Right"), (1, "Left")):
    TIP = [(1.12, 5.00), (1.30, 5.18), (1.36, 5.42), (1.26, 5.46), (1.20, 5.26), (1.06, 5.10)]
    prism_xh(hd, "HD_moustache_curl_" + nm, [(s_ * x * MSX, h + FD) for x, h in TIP] if s_ > 0 else [(s_ * x * MSX, h + FD) for x, h in TIP][::-1], .90, 1.24, sh_const("MoustacheLight"), {"recipe": "extra curl facet on the moustache tip", "class": "extrapolated"})
# broad toothy grin inside the pocket: teeth recessed .05 below the face surface, two tooth rows, lower-lip ridge, smile creases
TX = .43
_xt = [-TX + 2 * TX * k / 12 for k in range(13)]
TEETH = [(x, 4.89 + .08 * (x / TX) ** 2) for x in _xt] + [(x, 4.61 + .16 * (x / TX) ** 2) for x in _xt[::-1]]
layered_plate(hd, "HD_teeth", TEETH, skull_D, [(MOUTH_IN + .02, 1.0, 1.0), (.05, 1.0, 1.0)], sh_const("Teeth"), {"recipe": "white teeth band set into the grin pocket (front .05 below the face surface)", "class": "observed"})
_mid = [(x, 4.75 + .12 * (x / TX) ** 2) for x in _xt]
layered_plate(hd, "HD_teeth_row_line", [(x, h + .011) for x, h in _mid] + [(x, h - .011) for x, h in _mid[::-1]], lambda x, h: skull_D(x, h) + .05, [(.02, 1.0, 1.0), (-.012, 1.0, 1.0)], sh_const("TeethShadow"), {"recipe": "line between the upper and lower tooth rows", "class": "extrapolated"})
for k, x in enumerate((-.34, -.22, -.11, 0.0, .11, .22, .34)):
    hb, ht = 4.62 + .16 * (x / TX) ** 2, 4.88 + .08 * (x / TX) ** 2
    layered_plate(hd, "HD_tooth_gap_%d" % k, [(x - .007, hb), (x + .007, hb), (x + .007, ht), (x - .007, ht)], lambda x_, h_: skull_D(x_, h_) + .05, [(.02, 1.0, 1.0), (-.012, 1.0, 1.0)], sh_const("TeethShadow"), {"recipe": "tooth gap line", "class": "extrapolated"})
_lip = [(x, 4.56 + .18 * (x / GX) ** 2 - .085) for x in _xs] + [(x, 4.56 + .18 * (x / GX) ** 2 + .01) for x in _xs[::-1]]
layered_plate(hd, "HD_lower_lip", _lip, skull_D, [(.04, 1.0, 1.0), (-.045, 1.0, 1.0)], sh_const("SkinLight"), {"recipe": "lower-lip ridge, proud .045, frames the bottom of the grin pocket", "class": "extrapolated"})
for s_, nm in ((-1, "Right"), (1, "Left")):
    crease = [(s_ * .58, 4.86), (s_ * .66, 4.82), (s_ * .76, 4.93), (s_ * .80, 5.08), (s_ * .74, 5.06), (s_ * .70, 4.98), (s_ * .64, 4.92)]
    layered_plate(hd, "HD_smile_crease_" + nm, crease if s_ > 0 else crease[::-1], skull_D, [(.03, 1.0, 1.0), (.01, 1.0, 1.0)], sh_const("SkinShadow"), {"recipe": "smile crease at the corner of the grin (slightly recessed)", "class": "extrapolated"})
    layered_plate(hd, "HD_cheek_ridge_" + nm, [(s_ * .56, 4.92), (s_ * .70, 4.90), (s_ * .76, 5.08), (s_ * .64, 5.10)] if s_ > 0 else [(s_ * .64, 5.10), (s_ * .76, 5.08), (s_ * .70, 4.90), (s_ * .56, 4.92)], skull_D, [(.04, 1.0, 1.0), (-.035, 1.0, 1.0)], sh_const("SkinLight"), {"recipe": "cheek bulge above the grin corner (frames the smile)", "class": "extrapolated"})

# ---------------------------------------------------------------------------------------------------------------------------
# hair: ONE shell over the whole skull + thick swept locks. Silver Hair / HairLight on top, grey facets underneath and at the sides.
# ---------------------------------------------------------------------------------------------------------------------------
HC = [(5.00, 1.40, -.05, -.82, .16), (5.25, 1.86, .10, -.98, .22), (5.65, 1.94, .35, -1.00, .22), (5.95, 1.94, 1.04, -1.00, .26), (6.12, 1.94, 1.06, -1.02, .30), (6.28, 1.76, .92, -.92, .30), (6.40, 1.30, .60, -.60, .22)]


def sh_hair_shell(n, c):
    if abs(c.x) > .85 and -.2 < -c.y < .55 and 4.95 < c.z < 5.75 and abs(n.x) > .4:
        return "HairGrey" if c.z > 5.40 else "HairGreyDark"
    if n.z < -0.30:
        return "HairGrey"
    return sh_hair(n, c)


loft(hd, "HD_hair_shell", [ring8(w / 2, -ff, -fb, c, 0, 0, h) for h, w, ff, fb, c in HC], sh_hair_shell, meta={"recipe": "single hair shell H5.00..6.40 over the whole skull; grey facets on the sides and underneath", "class": "observed+extrapolated"})


HSX = 0.84                         # hair x factor (the first fit showed the head/hair span 30 px too wide)


def lock(cid, pts, w0, w1, h0, h1, thick=1.0):
    k = 1.5 * thick
    pts = [(x * HSX, f, min(z, 6.40 - h0 * k / 2)) if z > 6.0 else (x * HSX, f, z) for x, f, z in pts]
    path = catmull([Bl(*p_) for p_ in pts], 4)
    sweep(hd, cid, path, lambda t: w0 + (w1 - w0) * t, lambda t: (h0 + (h1 - h0) * t) * k, .09, sh_hair, {"recipe": "broad swept silver lock", "class": "observed+extrapolated"})


# the big side-swept mass: from the front-right of the forehead, over the crown, falling to the character's left (viewer right, as in the source)
lock("HD_wave_1", [(-.90, .70, 5.98), (-.70, .95, 6.18), (-.15, .85, 6.30), (.45, .45, 6.28), (.95, .20, 6.10), (1.20, .20, 5.80), (1.22, .25, 5.55)], .62, .40, .32, .26)
lock("HD_wave_2", [(-1.00, .20, 5.98), (-.85, .40, 6.20), (-.30, .30, 6.30), (.30, -.15, 6.28), (.85, -.40, 6.12), (1.15, -.30, 5.85)], .58, .38, .30, .24)
lock("HD_wave_3", [(-.45, .98, 6.00), (-.20, 1.02, 6.20), (.30, .85, 6.28), (.80, .50, 6.18), (1.12, .35, 5.95), (1.16, .40, 5.70)], .52, .34, .28, .24)
lock("HD_wave_4", [(-.80, -.40, 6.18), (-.30, -.75, 6.26), (.30, -.90, 6.20), (.80, -.80, 6.00), (1.00, -.70, 5.75)], .56, .36, .28, .24)
lock("HD_wave_front_curl", [(-.95, .90, 5.92), (-.70, 1.08, 6.08), (-.30, 1.08, 6.18)], .44, .32, .28, .24)
lock("HD_curl_left_1", [(1.02, .52, 5.95), (1.20, .50, 5.70), (1.25, .45, 5.48), (1.14, .36, 5.32)], .40, .30, .30, .24)
lock("HD_curl_left_2", [(1.02, -.05, 5.90), (1.20, -.10, 5.66), (1.22, -.16, 5.42)], .38, .28, .28, .22)
lock("HD_curl_right_1", [(-1.10, .50, 5.95), (-1.30, .46, 5.70), (-1.34, .38, 5.40), (-1.24, .30, 5.10)], .46, .32, .32, .26)
lock("HD_curl_right_2", [(-1.10, -.08, 5.92), (-1.30, -.14, 5.66), (-1.34, -.22, 5.36), (-1.24, -.28, 5.08)], .44, .30, .30, .24)
lock("HD_curl_right_3", [(-1.06, .22, 5.98), (-1.26, .18, 5.76), (-1.30, .10, 5.52)], .40, .28, .28, .22)
for k, x in enumerate((-.66, -.33, 0.0, .33, .66)):
    lock("HD_back_strand_%d" % (k + 1), [(x * .98, -.88, 6.10), (x, -1.03, 5.80), (x * 1.02, -1.05, 5.45), (x * .96, -.98, 5.12)], .34, .28, .14, .12, 0.75)
# ----------------------------------------------------------------------------------------------
# hard case (separate rigid prop in the RIGHT hand, ONE grip): black rectangular case, gold/brass corner and edge fittings, top handle
# Orientation (hidden-side choice): long axis along F, thin along X, hanging beside the right thigh. Locks / interior are NOT in the source: omitted.
# ----------------------------------------------------------------------------------------------
_hxR = HAND_AX["Right"]
_tbar = (2.04 - _hxR.P0.z) / (_hxR.A.z * _hxR.L)                  # parameter along the fist axis where it crosses the handle-bar height H2.04
_bar = _hxR.at(_tbar)
HANDLE_BAR = (round(_bar.x, 4), round(-_bar.y, 4), 2.04)          # handle bar centre (X, F, H): on the real fist axis, inside the closed fist (hidden)
CASE_LOGICAL = (HANDLE_BAR[0], HANDLE_BAR[1], 0.965)               # case hangs straight below the bar
CASE_T, CASE_L, CASE_H = .80, 2.70, 1.55   # thickness X, length F, height H (source: visible width ~2.35, height ~1.65 in the projection; revised after the landmark fit)
CASE_C = Bl(*CASE_LOGICAL)
cs = PM("Case", CASE_C, geo="Case_Geo")
CX, CY, CZ = CASE_C.x, CASE_C.y, CASE_C.z
hx_, hy_, hz_ = CASE_T / 2, CASE_L / 2, CASE_H / 2
loft(cs, "CASE_body", cbox((CX, CY, CZ), (CASE_T, CASE_L, CASE_H), .09), sh_case, meta={"recipe": "black rectangular hard case .80 x 2.70 x 1.55, chamfer .09", "class": "observed"})
GOLD_T = .05                               # fittings are proud by this much
# vertical gold edge bars near both short ends (both broad faces)
for sx in (-1, 1):
    for sy in (-1, 1):
        solid_box(cs, "CASE_edge_bar_%d_%d" % (sx, sy), CX + sx * (hx_ - .02), CX + sx * (hx_ + GOLD_T), CY + sy * (hy_ - .36), CY + sy * (hy_ - .20), CZ - hz_ + .02, CZ + hz_ - .02, "Gold", {"recipe": "vertical gold edge bar on the broad face", "class": "observed"})
# corner brackets (8 corners): small gold/brass cubes wrapping the edges, proud by .03
for sx in (-1, 1):
    for sy in (-1, 1):
        for sz in (-1, 1):
            cx_, cy_, cz_ = CX + sx * (hx_ - .10), CY + sy * (hy_ - .10), CZ + sz * (hz_ - .10)
            solid_box(cs, "CASE_corner_%d_%d_%d" % (sx, sy, sz), cx_ - .13, cx_ + .13, cy_ - .13, cy_ + .13, cz_ - .13, cz_ + .13, "Brass" if (sx + sy + sz) % 2 else "Gold", {"recipe": "gold/brass corner fitting", "class": "observed"})
# gold top / bottom rails on the long edges
for sx in (-1, 1):
    solid_box(cs, "CASE_rail_top_%d" % sx, CX + sx * (hx_ - .03) - .04, CX + sx * (hx_ - .03) + .04, CY - hy_ + .40, CY + hy_ - .40, CZ + hz_ - .045, CZ + hz_ + .03, "GoldShadow", {"recipe": "brass top rail", "class": "extrapolated"})
# top handle: loop (two legs + bar) in the (F, H) plane at X = hand axis; the bar passes through the closed fist
HX = HANDLE_BAR[0]
path = catmull([Bl(HX, HANDLE_BAR[1] - .42, CZ + hz_ - .04), Bl(HX, HANDLE_BAR[1] - .42, HANDLE_BAR[2] - .05), Bl(HX, HANDLE_BAR[1] - .30, HANDLE_BAR[2] + .02), Bl(HX, HANDLE_BAR[1] + .30, HANDLE_BAR[2] + .02),
                Bl(HX, HANDLE_BAR[1] + .42, HANDLE_BAR[2] - .05), Bl(HX, HANDLE_BAR[1] + .42, CZ + hz_ - .04)], 4)
sweep(cs, "CASE_handle", path, lambda t: .13, lambda t: .13, .035, sh_const("Case"), {"recipe": "black handle loop; bar H2.04 sits inside the fist", "class": "observed+extrapolated"})
for sy in (-1, 1):
    solid_box(cs, "CASE_handle_mount_%d" % sy, HX - .13, HX + .13, -(HANDLE_BAR[1] + sy * .42) - .09, -(HANDLE_BAR[1] + sy * .42) + .09, CZ + hz_ - .02, CZ + hz_ + .06, "Gold", {"recipe": "gold handle mount", "class": "extrapolated"})


# ----------------------------------------------------------------------------------------------
# atlas / material / mesh objects
# ----------------------------------------------------------------------------------------------
os.makedirs(os.path.join(OUT, "textures"), exist_ok=True)
atlas = bpy.data.images.new("MillionaireDad_Atlas", ATLAS_W, ATLAS_H, alpha=False)
atlas.colorspace_settings.name = 'sRGB'
px = [0.0] * (ATLAS_W * ATLAS_H * 4)
fill = hex_rgb(HEXOF["Ivory"])
for ty in range(ATLAS_H):
    for tx in range(ATLAS_W):
        idx = (ty // TILE_PX) * COLS + (tx // TILE_PX)
        rgb = hex_rgb(PAL[idx][1]) if idx < len(PAL) else fill
        r, g, b = (c / 255.0 for c in rgb)
        o = ((ATLAS_H - 1 - ty) * ATLAS_W + tx) * 4
        px[o:o + 4] = [r, g, b, 1.0]
atlas.pixels.foreach_set(px)
ATLAS_PATH = os.path.join(OUT, "textures", "MillionaireDad_Atlas.png")
atlas.filepath_raw = ATLAS_PATH
atlas.file_format = 'PNG'
atlas.save()
atlas.pack()

MATP = bpy.data.materials.new("MillionaireDad_Atlas")
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
arm_data = bpy.data.armatures.new("MillionaireDad_Armature")
ARM_OB = bpy.data.objects.new("MillionaireDad_Armature", arm_data)
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
PROPS = ("Case",)
for pm in PARTS.values():
    bone = {"Case": "RightHand"}.get(pm.runtime, pm.runtime)
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
ALLOWED = {"Case": {"RightHand": "the handle bar passes through the closed fist (hidden, allowed)"}}
CLEAR = {}
for prop, others in (("Case", ("RightUpperLeg", "RightLowerLeg", "RightFoot", "RightHand", "RightLowerArm", "RightUpperArm", "LowerTorso", "LeftFoot", "LeftUpperLeg")),):
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
BLEND = os.path.join(OUT, "source", "MillionaireDad_Review.blend")
FBX_BODY = os.path.join(OUT, "export", "MillionaireDad_Body.fbx")
FBX_PROPS = os.path.join(OUT, "export", "MillionaireDad_Props.fbx")
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

uvmap = {"atlas": "MillionaireDad_Atlas.png", "size": [ATLAS_W, ATLAS_H], "tile_px": TILE_PX, "columns": COLS, "inset_px": INSET, "row0_is_top_of_png": True, "tiles": []}
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
json.dump({"asset": "MillionaireDad_Review", "units": "studs", "height_target": 6.40, "height_built": RESULT["bounds_body"]["height"], "joints_blender": JOINTS_BL, "part_bbox_centres_blender": CENTRES,
           "tables": {"torso_rows_D": TORSO, "skull_rows": SKULL, "nose_rows": NOSE, "hair_cap_rows": HC}, "right_bend_hint": list(RHINT), "left_bend_hint": list(LHINT), "L1_L2": [L1, L2],
           "elbow_contours": {k: [list(map(float, p)) for p in v] for k, v in ELBOW_RING.items()}, "palette": [{"index": i, "name": n_, "hex": h_} for i, (n_, h_, _) in enumerate(PAL)],
           "counts": {"body_tris": body_tris, "prop_tris": prop_tris}, "measured": RESULT},
          open(os.path.join(OUT, "data", "construction_spec_actual.json"), "w"), indent=1)
json.dump({"pose": "static: case in the right hand, left hand at the hip (rest pose == pose)", "joints_logical_XFH": {k: list(v) for k, v in JOINTS.items()}, "joints_blender": JOINTS_BL,
           "grips": {"CaseGrip": {"from": "RightHand", "to": "Case", "centre_logical_XFH": list(CASE_LOGICAL), "handle_bar_logical_XFH": list(HANDLE_BAR)}},
           "left_hand": "LeftHand rests at the hip",
           "watch": "gold watch with black strap baked into the LeftHand mesh, cannot detach"},
          open(os.path.join(OUT, "data", "joints_pose_grips.json"), "w"), indent=1)
json.dump({"asset": "MillionaireDad_Review", "components": COMP_LOG,
           "part_totals": {k: {"components": len(v.comps), "tris": AUDIT[k]["tris"], "verts": AUDIT[k]["verts"]} for k, v in PARTS.items()},
           "mesh_names": {k: v.geo for k, v in PARTS.items()}}, open(os.path.join(OUT, "data", "component_registry.json"), "w"), indent=1)
RIG = {"asset": "MillionaireDad_Review", "frame": {"logical": "(X,F,H) anatomical RIGHT = -X, forward = +F", "blender": "(X,-F,H)", "roblox_position": "(-X, H, -F)"},
       "bones": [{"name": n, "parent": p, "head_logical": logical(h), "tail_logical": logical(t), "head_roblox": roblox_pos(h)} for n, p, h, t in BONES],
       "joints_logical": {k: list(v) for k, v in JOINTS.items()},
       "grips": {"CaseGrip": {"joint": "RightHand -> Case", "centre_logical": list(CASE_LOGICAL)}},
       "weights": "100% own bone (rigid); Case -> RightHand (prop exported as a separate mesh without armature)",
       "part_origin_logical": {k: logical(v.joint) for k, v in PARTS.items()}, "part_bbox_centres_blender": CENTRES, "joints_blender": JOINTS_BL, "pose": "static pose built directly (pose bones identity)"}
json.dump(RIG, open(os.path.join(OUT, "data", "rig_manifest.json"), "w"), indent=1)
print("RESULT", json.dumps({k: RESULT[k] for k in ("bounds_body", "tris_body", "tris_props", "symmetry", "arm_lengths", "axes", "pose_bones_identity")}))

PREVIEW = "--preview" in sys.argv
if NORENDER:
    sys.exit(0)

# ----------------------------------------------------------------------------------------------
# cameras / light / render helpers (real Blender renders of the built scene)
# ----------------------------------------------------------------------------------------------
world = bpy.data.worlds.new("MD_World")
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
sun_d = bpy.data.lights.new("MD_Key", 'SUN')
sun_d.energy = 1.8
sun = bpy.data.objects.new("MD_Key", sun_d)
SCENE.collection.objects.link(sun)
sun.rotation_euler = (math.radians(52), math.radians(8), math.radians(-38))
fill_d = bpy.data.lights.new("MD_Fill", 'SUN')
fill_d.energy = 0.55
fill_d.use_shadow = False
fill = bpy.data.objects.new("MD_Fill", fill_d)
SCENE.collection.objects.link(fill)
fill.rotation_euler = (math.radians(60), 0, math.radians(140))
cam_d = bpy.data.cameras.new("MD_Cam")
CAM = bpy.data.objects.new("MD_Cam", cam_d)
SCENE.collection.objects.link(CAM)
SCENE.camera = CAM
SCENE.render.engine = 'BLENDER_EEVEE'
SCENE.eevee.taa_render_samples = 8 if QUICK else 32
SCENE.render.image_settings.file_format = 'PNG'
SCENE.view_settings.view_transform = 'Standard'
SCENE.render.film_transparent = False

FLATM = bpy.data.materials.new("MD_Flat")
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


# matching camera: orthographic, 422x425 frame = the unaltered crop (figure y5..413 of 425 = 6.40 studs PROJECT CONVENTION -> ortho scale 6.667, target H3.15);
# azimuth / elevation / x shift are fitted to the crop silhouette by scripts/fit_camera.py and read from inputs/camera_tuned.json
CAMCFG = {"type": "ORTHO", "target_h": 3.15, "azimuth_deg": 28.0, "elevation_deg": 3.0, "ortho_scale": 425.0 / 408.0 * 6.40, "res": [422, 425], "shift_x": 0.0,
          "note": "crop of the sheet at x1110..1532, y530..955; 63.75 px per stud at the 6.40 convention"}
if os.path.exists(os.path.join(HERE, "inputs", "camera_tuned.json")):
    CAMCFG.update(json.load(open(os.path.join(HERE, "inputs", "camera_tuned.json"))))
MT = V((0, 0, CAMCFG["target_h"]))
MATCH_LOC = orbit(MT, 40, CAMCFG["azimuth_deg"], CAMCFG["elevation_deg"])
json.dump(CAMCFG, open(os.path.join(OUT, "data", "camera.json"), "w"), indent=1)
K = 3
cam_d.shift_x = CAMCFG.get("shift_x", 0.0)
shot("match_view_%dx%d.png" % (CAMCFG["res"][0] * K, CAMCFG["res"][1] * K), MATCH_LOC, MT, res=(CAMCFG["res"][0] * K, CAMCFG["res"][1] * K), ortho=CAMCFG["ortho_scale"])
cam_d.shift_x = 0.0
T = V((0, 0, 3.2))
SC = 7.0
FULL = (700, 900)
if PREVIEW:
    shot("pv_front.png", orbit(T, 40, 0, 0), T, res=FULL, ortho=SC)
    shot("pv_34L.png", orbit(T, 40, 35, 8), T, res=FULL, ortho=SC)
    shot("pv_34R.png", orbit(T, 40, -35, 8), T, res=FULL, ortho=SC)
    shot("pv_back.png", orbit(T, 40, 180, 0), T, res=FULL, ortho=SC)
    shot("pv_Rside.png", orbit(T, 40, -90, 0), T, res=FULL, ortho=SC)
    HT = V((0, -.2, 5.35))
    shot("pv_face.png", orbit(HT, 20, 20, 3), HT, res=(900, 900), ortho=3.4)
    sys.exit(0)
# ---- technical views of the SAME built mesh: identical pixel height (700x900, ortho 7.0, target H3.2, camera distance 40) ----
shot("full_front.png", orbit(T, 40, 0, 0), T, res=FULL, ortho=SC)
shot("full_back.png", orbit(T, 40, 180, 0), T, res=FULL, ortho=SC)
shot("full_right_side.png", orbit(T, 40, -90, 0), T, res=FULL, ortho=SC)      # anatomical right (case side)
shot("full_left_side.png", orbit(T, 40, 90, 0), T, res=FULL, ortho=SC)        # anatomical left (watch side)
shot("full_front_left_34.png", orbit(T, 40, 35, 8), T, res=FULL, ortho=SC)
shot("full_front_right_34.png", orbit(T, 40, -35, 8), T, res=FULL, ortho=SC)
shot("full_top.png", orbit(T, 40, 20, 70), T, res=FULL, ortho=SC)
shot("full_low_angle.png", orbit(T, 40, -25, -22), T, res=FULL, ortho=SC)
# close-ups
HT = V((0, -.2, 5.35))
shot("close_face_front.png", orbit(HT, 20, 0, 3), HT, res=(900, 900), ortho=3.4)
shot("close_face_34_left.png", orbit(HT, 20, 30, 5), HT, res=(900, 900), ortho=3.4)
shot("close_face_34_right.png", orbit(HT, 20, -30, 5), HT, res=(900, 900), ortho=3.4)
shot("close_face_profile_left.png", orbit(HT, 20, 90, 3), HT, res=(900, 900), ortho=3.4)
shot("close_face_profile_right.png", orbit(HT, 20, -90, 3), HT, res=(900, 900), ortho=3.4)
shot("close_hair_top.png", orbit(HT, 20, 20, 55), HT, res=(900, 900), ortho=3.4)
shot("close_hair_back.png", orbit(HT, 20, 180, 10), HT, res=(900, 900), ortho=3.4)
shot("close_glasses_moustache.png", orbit(V((0, -1.1, 5.1)), 20, 0, 3), V((0, -1.1, 5.1)), res=(900, 900), ortho=2.4)
shot("close_grin.png", orbit(V((0, -1.0, 4.75)), 20, 0, 3), V((0, -1.0, 4.75)), res=(900, 900), ortho=1.8)
CT = V((-2.0, -.2, 1.5))
shot("close_case_front.png", orbit(CT, 20, 0, 4), CT, res=(900, 900), ortho=3.6)
shot("close_case_side_outer.png", orbit(CT, 20, -90, 4), CT, res=(900, 900), ortho=3.6)
shot("close_case_34.png", orbit(CT, 20, -35, 14), CT, res=(900, 900), ortho=3.6)
shot("close_case_back.png", orbit(CT, 20, 180, 6), CT, res=(900, 900), ortho=3.6)
GT = V((-2.0, -.25, 2.2))
shot("close_grip_front.png", orbit(GT, 20, 0, 6), GT, res=(900, 900), ortho=2.2)
shot("close_grip_outer.png", orbit(GT, 20, -90, 6), GT, res=(900, 900), ortho=2.2)
shot("close_grip_top.png", orbit(GT, 20, 0, 80), GT, res=(900, 900), ortho=2.2)
WT = V((1.85, -.45, 2.75))
shot("close_watch_outer.png", orbit(WT, 20, 60, 8), WT, res=(900, 900), ortho=2.0)
shot("close_watch_front.png", orbit(WT, 20, 20, 8), WT, res=(900, 900), ortho=2.0)
shot("close_left_hand_hip.png", orbit(V((1.7, -.5, 2.6)), 20, 0, 4), V((1.7, -.5, 2.6)), res=(900, 900), ortho=2.6)
shot("close_belt_buckle.png", orbit(V((0, -.8, 2.67)), 20, 0, 4), V((0, -.8, 2.67)), res=(900, 900), ortho=1.8)
shot("close_chest_buttons_square.png", orbit(V((0.5, -.8, 3.7)), 20, 0, 4), V((0.5, -.8, 3.7)), res=(900, 900), ortho=3.0)
FT_ = V((0, -.4, .5))
shot("close_shoes_front.png", orbit(FT_, 20, 0, 6), FT_, res=(900, 700), ortho=3.8, show_only=("RightFoot", "LeftFoot", "RightLowerLeg", "LeftLowerLeg"))
shot("close_shoes_34.png", orbit(FT_, 20, -35, 14), FT_, res=(900, 700), ortho=3.8, show_only=("RightFoot", "LeftFoot", "RightLowerLeg", "LeftLowerLeg"))
shot("close_shoes_top.png", orbit(FT_, 20, 0, 85), FT_, res=(900, 700), ortho=3.8, show_only=("RightFoot", "LeftFoot"))
shot("close_shoes_sole.png", orbit(FT_, 20, 0, -85), FT_, res=(900, 700), ortho=3.8, show_only=("RightFoot", "LeftFoot"))
shot("close_jacket_back.png", orbit(V((0, 0.6, 3.6)), 20, 180, 4), V((0, .6, 3.6)), res=(900, 900), ortho=4.4)
print("ALL_RENDERS_DONE", len(RENDERED))
