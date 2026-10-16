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
# containers + shading rules + generators specific to Fisherman Dad
# ----------------------------------------------------------------------------------------------
PARTS = {}
COMP_LOG = []
SRC_COLL = bpy.data.collections.new("SOURCE_Components")
SCENE.collection.children.link(SRC_COLL)
EXP_COLL = bpy.data.collections.new("EXPORT_GrillDad")
SCENE.collection.children.link(EXP_COLL)
_H = {n: h for n, h, _ in PAL}
HEXOF = _H
OBS = {"class": "observed+prescribed"}
PRE = {"class": "prescribed"}


def meta(recipe, cls="observed+prescribed", **kw):
    d = {"recipe": recipe, "class": cls}
    d.update(kw)
    return d




def sh_const(name):
    return lambda n, c: name


def sh_skin(n, c):
    if n.z > 0.55:
        return "SKIN_LIGHT"
    if n.z < -0.55:
        return "SKIN_SHADOW"
    return "SKIN"


def sh_skin_arm(n, c):
    if n.z > 0.55:
        return "SKIN_LIGHT"
    if n.z < -0.55:
        return "SKIN_SHADOW"
    if n.y < -0.62:
        return "SKIN_LIGHT"
    return "SKIN"


def sh_shirt(n, c):
    if n.z > 0.45:
        return "SHIRT_LIGHT"
    if abs(n.x) > 0.75 or n.z < -0.45:
        return "SHIRT_DARK"
    return "SHIRT"


def sh_pants(n, c):
    if n.z < -0.6 or abs(n.x) > 0.85:
        return "PANTS_DARK"
    if n.z > 0.6 or n.y < -0.62:
        return "PANTS_LIGHT"
    return "PANTS"


def sh_shoe(n, c):
    if n.z < -0.5:
        return "SOLE"
    if n.z > 0.55 or abs(n.x) > 0.8:
        return "SHOE_LIGHT"
    return "SHOE"


def sh_hair(n, c):
    if n.z < -0.30:
        return "HAIR_DARK"
    if n.z > 0.62:
        return "HAIR_LIGHT"
    return "HAIR"


def sh_nose(n, c):
    if n.z < -0.55:
        return "SKIN_SHADOW"
    if n.z > 0.45:
        return "SKIN_LIGHT"
    return "NOSE"


def sh_apron(n, c):
    if n.y < -0.6:
        # sparse large lighter facets on the front face, chosen deterministically from the face centre
        k = (int(math.floor(c.x * 2.6)) * 7 + int(math.floor(c.z * 2.6)) * 13) % 11
        return "APRON_LIGHT" if k == 0 else "APRON"
    return "APRON_DARK"


def sh_wood(n, c):
    if n.z < -0.5:
        return "WOOD_DARK"
    if n.x * (1 if c.x >= 0 else -1) > 0.55:
        return "WOOD_LIGHT"
    if n.x * (1 if c.x >= 0 else -1) < -0.55:
        return "WOOD_DARK"
    return "WOOD"


def sh_steel(n, c):
    if n.z > 0.7:
        return "STEEL_LIGHT"
    if abs(n.x) > 0.75:
        return "STEEL_DARK"
    if n.y > 0.5:
        return "STEEL_DARK"
    return "STEEL"
# ---------------------------------------------------------------- generic generators
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


def ring_pts(P, B, N, w, t, n=8, c=None):
    """Cross-section ring at P with width dir B, thickness dir N. n==8 -> chamfered rectangle, else ellipse with n points."""
    a, h = w / 2.0, t / 2.0
    if n == 8:
        cc = min(a, h) * 0.45 if c is None else min(c, a - 1e-5, h - 1e-5)
        pts = [(-a + cc, -h), (a - cc, -h), (a, -h + cc), (a, h - cc), (a - cc, h), (-a + cc, h), (-a, h - cc), (-a, -h + cc)]
    else:
        pts = [(a * math.cos(2 * math.pi * k / n + math.pi / n), h * math.sin(2 * math.pi * k / n + math.pi / n)) for k in range(n)]
    return [P + B * x + N * y for x, y in pts]


def frames_along(pts, up=V((1, 0, 0))):
    out = []
    n = len(pts)
    for i, p in enumerate(pts):
        T = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        u = V(up)
        if abs(T.dot(u)) > 0.97:
            u = V((0, -1, 0))
        N = (u - T * T.dot(u)).normalized()
        B = T.cross(N).normalized()
        out.append((p, T, B, N))
    return out


def sweep(pm, cid, pts, wd, th, tile, up=V((1, 0, 0)), n=8, caps=(True, True), c=None, meta_=None):
    """Closed solid swept along pts (list of V); wd/th scalars or per-point lists; ellipse rings (n!=8) or chamfered-rect rings (n==8)."""
    m = len(pts)
    wd = wd if isinstance(wd, (list, tuple)) else [wd] * m
    th = th if isinstance(th, (list, tuple)) else [th] * m
    rings = []
    for (p, T, B, N), w, t in zip(frames_along(pts, up), wd, th):
        rings.append(ring_pts(p, B, N, w, t, n, c))
    loft(pm, cid, rings, tile, caps=caps, meta=meta_ or PRE)
    return rings


def lathe(pm, cid, profile, cx, cd, segs, tile, band_tiles=None, caps=(True, True), meta_=None, rot=0.0):
    """Surface of revolution about the H axis through (cx,cd): profile [(r,h)] open curve + planar caps at both ends."""
    rings = []
    for r, h in profile:
        rings.append([V((cx + r * math.cos(2 * math.pi * k / segs + rot), cd + r * math.sin(2 * math.pi * k / segs + rot), h)) for k in range(segs)])
    loft(pm, cid, rings, tile, caps=caps, band_tiles=band_tiles, meta=meta_ or PRE)


def loop_solid(pm, cid, sections, tile, meta_=None):
    """Periodic loft: list of cross-section point lists closed around the loop (torus-like solid)."""
    n, m = len(sections), len(sections[0])
    P = [p for s in sections for p in s]
    faces = []
    for i in range(n):
        j = (i + 1) % n
        for k in range(m):
            k2 = (k + 1) % m
            faces.append([i * m + k, i * m + k2, j * m + k2, j * m + k])
    pm.solid(cid, P, faces, tile, meta_ or PRE)


def grid_solid(pm, cid, outer, inner, tile, meta_=None):
    """Closed slab from two same-topology grids outer[l][k], inner[l][k] (l: levels, k: columns)."""
    L, K = len(outer), len(outer[0])
    P = [p for r in outer for p in r] + [p for r in inner for p in r]
    off = L * K
    o = lambda l, k: l * K + k
    i_ = lambda l, k: off + l * K + k
    F = []
    for l in range(L - 1):
        for k in range(K - 1):
            F.append([o(l, k), o(l, k + 1), o(l + 1, k + 1), o(l + 1, k)])
            F.append([i_(l, k), i_(l + 1, k), i_(l + 1, k + 1), i_(l, k + 1)])
    for l in range(L - 1):
        F.append([o(l, 0), o(l + 1, 0), i_(l + 1, 0), i_(l, 0)])
        F.append([o(l, K - 1), i_(l, K - 1), i_(l + 1, K - 1), o(l + 1, K - 1)])
    for k in range(K - 1):
        F.append([o(0, k), i_(0, k), i_(0, k + 1), o(0, k + 1)])
        F.append([o(L - 1, k), o(L - 1, k + 1), i_(L - 1, k + 1), i_(L - 1, k)])
    pm.solid(cid, P, F, tile, meta_ or OBS)


def band(pm, cid, levels, pathfn, t_out, t_in, tile, meta_=None):
    """Open ribbon wrapped around a (x,d) path per height level; offsets along the 2D outward normal."""
    outer, inner = [], []
    for h in levels:
        path = pathfn(h)
        cen = sum((V((p[0], p[1], 0)) for p in path), V()) / len(path)
        ro, ri = [], []
        n = len(path)
        for k, p in enumerate(path):
            a = V((path[min(k + 1, n - 1)][0] - path[max(k - 1, 0)][0], path[min(k + 1, n - 1)][1] - path[max(k - 1, 0)][1], 0))
            nn = V((a.y, -a.x, 0)).normalized()
            if nn.dot(V((p[0], p[1], 0)) - cen) < 0:
                nn = -nn
            ro.append(V((p[0] + nn.x * t_out, p[1] + nn.y * t_out, h)))
            ri.append(V((p[0] + nn.x * t_in, p[1] + nn.y * t_in, h)))
        outer.append(ro)
        inner.append(ri)
    grid_solid(pm, cid, outer, inner, tile, meta_)


def poly_rows(outline, hs):
    rows = []
    n = len(outline)
    for h in hs:
        xs = []
        for i in range(n):
            (x1, h1), (x2, h2) = outline[i], outline[(i + 1) % n]
            if abs(h1 - h2) < 1e-9:
                if abs(h1 - h) < 1e-9:
                    xs += [x1, x2]
            elif min(h1, h2) - 1e-9 <= h <= max(h1, h2) + 1e-9:
                xs.append(x1 + (x2 - x1) * (h - h1) / (h2 - h1))
        if xs:
            rows.append((h, min(xs), max(xs)))
    return rows


def auto_hs(outline, step=0.16):
    hv = sorted({round(p[1], 6) for p in outline})
    hs = []
    for a, b in zip(hv, hv[1:]):
        k = max(1, int(math.ceil((b - a) / step)))
        hs += [a + (b - a) * i / k for i in range(k)]
    hs.append(hv[-1])
    return hs


def patch(pm, cid, outline, fit, d_back, d_front, tile, ch=0.0, nx=6, step=0.16, rear=False, meta_=None):
    """Slab hugging the surface fit(x,h)->D over the polygon outline [(x,h)]. d_* = distance along the outward direction
    (forward = -D; rear=True -> +D). The front layer is chamfered inward by ch."""
    sg = 1.0 if rear else -1.0
    rows = poly_rows(outline, auto_hs(outline, step))
    outer, inner = [], []
    for li, (h, lo, hi) in enumerate(rows):
        ro, ri = [], []
        for k in range(nx):
            x = lo + (hi - lo) * k / (nx - 1)
            xf, hf_ = x, h
            if ch:
                if k == 0:
                    xf = x + ch
                if k == nx - 1:
                    xf = x - ch
                if li == 0:
                    hf_ = h + ch
                if li == len(rows) - 1:
                    hf_ = h - ch
            ro.append(V((xf, fit(xf, hf_) + sg * d_front, hf_)))
            ri.append(V((x, fit(x, h) + sg * d_back, h)))
        outer.append(ro)
        inner.append(ri)
    grid_solid(pm, cid, outer, inner, tile, meta_)


def plate(pm, cid, outline, back_fn, front_fn, tile, ch=0.02, meta_=None):
    """Closed plate over polygon outline [(x,h)]: back layer D=back_fn, front chamfer ring, front face D=front_fn (forward=-D)."""
    xs = [p[0] for p in outline]
    hs = [p[1] for p in outline]
    cx, chh = (min(xs) + max(xs)) / 2, (min(hs) + max(hs)) / 2
    wd, ht = max(xs) - min(xs), max(hs) - min(hs)
    sx = max(0.0, 1 - 2 * ch / wd) if wd > 0 else 1
    sh = max(0.0, 1 - 2 * ch / ht) if ht > 0 else 1
    n = len(outline)
    P = []
    for x, h in outline:
        P.append(V((x, back_fn(x, h), h)))
    for x, h in outline:
        P.append(V((x, front_fn(x, h) + ch, h)))
    for x, h in outline:
        xx, hh = cx + (x - cx) * sx, chh + (h - chh) * sh
        P.append(V((xx, front_fn(xx, hh), hh)))
    faces = []
    for r in range(2):
        for k in range(n):
            faces.append([r * n + k, r * n + (k + 1) % n, (r + 1) * n + (k + 1) % n, (r + 1) * n + k])
    faces += cap_tris(P, list(range(n)))
    faces += cap_tris(P, list(range(2 * n, 3 * n)))
    pm.solid(cid, P, faces, tile, meta_ or OBS)


def disc_d(pm, cid, cx, cd, h, r, thick, tile, segs=8, ry=None, embed=0.0):
    """Disc / button facing -D: front face at D=cd, thick towards +D (+embed). ry = vertical radius (ellipse)."""
    ry = ry or r
    rings = []
    for dd in (cd, cd + thick + embed):
        rings.append([V((cx + r * math.cos(2 * math.pi * k / segs + math.pi / segs), dd, h + ry * math.sin(2 * math.pi * k / segs + math.pi / segs))) for k in range(segs)])
    loft(pm, cid, rings, tile, meta=PRE)


def box_c(pm, cid, c, size, tile, ch=0.0, meta_=None, xf=None):
    sx, sd, sh = size
    if ch > 0:
        rings = cbox(c, size, ch, xf=xf)
    else:
        rings = box_rings(c[0] - sx / 2, c[0] + sx / 2, c[1] - sd / 2, c[1] + sd / 2, c[2] - sh / 2, c[2] + sh / 2)
        if xf:
            rings = [[xf(p) for p in r] for r in rings]
    loft(pm, cid, rings, tile, meta=meta_ or PRE)


def mirror_pts(pts):
    return [(-x, h) for x, h in pts]


# ----------------------------------------------------------------------------------------------
# prescribed numeric tables (master prompt sections 08..22, 28)
# ----------------------------------------------------------------------------------------------
UT_ROWS = [(2.20, 2.72, -.86, .56, .13), (2.65, 2.92, -1.00, .64, .17), (3.10, 2.95, -1.05, .68, .17),
           (3.65, 2.88, -.95, .64, .16), (4.15, 2.87, -.74, .58, .12), (4.46, 2.65, -.60, .51, .11), (4.72, 2.12, -.49, .45, .09)]
LT_ROWS = [(1.82, 2.30, -.70, .48, .12), (2.10, 2.55, -.80, .56, .14), (2.34, 2.66, -.84, .58, .14)]
APRON_ROWS = [(1.10, 2.78, -.83, .06), (1.70, 2.91, -.98, .07), (2.30, 2.95, -1.06, .07), (2.63, 2.91, -1.08, .07),
              (3.12, 2.83, -1.12, .07), (3.62, 2.48, -.99, .06), (4.03, 2.10, -.83, .04)]
HEAD_ROWS = [(4.74, 1.50, -.62, .60, .13), (4.98, 1.74, -.74, .76, .14), (5.12, 1.86, -.78, .76, .14), (5.40, 1.88, -.74, .76, .14),
             (6.28, 1.88, -.74, .76, .12), (6.40, 1.62, -.62, .64, .12)]
STAINS = [(-0.52, 3.29, 0.43, 0.28), (0.54, 3.14, 0.48, 0.48), (1.12, 3.48, 0.35, 0.43), (0.95, 2.91, 0.40, 0.23), (-0.12, 2.57, 0.38, 0.26),
          (0.74, 2.16, 0.48, 0.40), (0.39, 1.60, 0.74, 0.55), (0.85, 1.47, 0.39, 0.38), (1.10, 1.87, 0.38, 0.52), (0.08, 1.38, 0.40, 0.26),
          (-0.34, 1.83, 0.28, 0.27), (-0.64, 2.01, 0.25, 0.20)]

BIND = {
    "RightShoulder": V((-1.70, 0, 4.46)), "RightElbow": V((-1.92, -.02, 3.23)), "RightWrist": V((-2.08, -.06, 2.28)),
    "LeftShoulder": V((1.70, 0, 4.46)), "LeftElbow": V((1.92, -.02, 3.23)), "LeftWrist": V((2.08, -.06, 2.28)),
}


def two_bone_ik(S, Wt, pole, Ebind, Wbind):
    S, Wt, pole = V(S), V(Wt), V(pole)
    a = (V(Ebind) - S).length
    b = (V(Wbind) - V(Ebind)).length
    d = (Wt - S).length
    u = (Wt - S) / d
    assert abs(a - b) <= d <= a + b
    q = (pole - S - u * (pole - S).dot(u)).normalized()
    t = (a * a - b * b + d * d) / (2 * d)
    return S + u * t + q * math.sqrt(a * a - t * t), a, b


LEFT_S = BIND["LeftShoulder"]
LEFT_W = V((2.04, -.54, 3.44))
LEFT_POLE = V((2.60, .70, 3.25))
LEFT_E, SEG_UP, SEG_LO = two_bone_ik(LEFT_S, LEFT_W, LEFT_POLE, BIND["LeftElbow"], BIND["LeftWrist"])
GRIP_C = V((2.30, -.62, 3.50))
JOINTS = {
    "Root": (0, 0, 2.05), "Waist": (0, 0, 2.32), "Neck": (0, 0, 4.70),
    "RightShoulder": tuple(BIND["RightShoulder"]), "RightElbow": tuple(BIND["RightElbow"]), "RightWrist": tuple(BIND["RightWrist"]),
    "LeftShoulder": tuple(LEFT_S), "LeftElbow": tuple(LEFT_E), "LeftWrist": tuple(LEFT_W),
    "RightHip": (-.66, .02, 2.05), "RightKnee": (-.66, .02, 1.05), "RightAnkle": (-.66, .02, .45),
    "LeftHip": (.66, .02, 2.05), "LeftKnee": (.66, .02, 1.05), "LeftAnkle": (.66, .02, .45),
}
JV = {k: V(v) for k, v in JOINTS.items()}


def ut_front(x, h):
    return front_at(UT_ROWS, min(max(h, 2.20), 4.72), x)


def ut_back(x, h):
    return back_at(UT_ROWS, min(max(h, 2.20), 4.72), x)


def hf(h, x=0.0):
    return front_at(HEAD_ROWS, min(max(h, 4.74), 6.40), x)


def hb(h, x=0.0):
    return back_at(HEAD_ROWS, min(max(h, 4.74), 6.40), x)


def apron_wd(h):
    h = min(max(h, 1.10), 4.03)
    for a, b in zip(APRON_ROWS, APRON_ROWS[1:]):
        if a[0] <= h <= b[0]:
            t = (h - a[0]) / (b[0] - a[0])
            return a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t
    return APRON_ROWS[-1][1], APRON_ROWS[-1][2]


def apron_front(x, h):
    w, d = apron_wd(h)
    ax = abs(x)
    if ax <= .33 * w:
        return d
    return d + .12 * min(1.0, (ax - .33 * w) / max(1e-6, .5 * w - .33 * w))


# ----------------------------------------------------------------------------------------------
# UpperTorso: shirt, neck, collar, placket, apron (front, belt, straps, knot), rivets, stains, towel
# ----------------------------------------------------------------------------------------------
ut = PM("UpperTorso", JV["Waist"])
loft(ut, "UT_shirt_body", [row_ring(r) for r in UT_ROWS], sh_shirt, meta=meta("8-point chamfered loft, section 08 rows", dims={"rows": UT_ROWS}))
loft(ut, "UT_neck", [ring8(.36, -.28, .32, .07, 0, 0, 4.51), ring8(.36, -.28, .32, .07, 0, 0, 4.81)], sh_skin,
     meta=meta("neck W.72 D.60 H.30 centre (0,.02,4.66)", "prescribed"))
for s in (-1, 1):
    pts = [(-.73, 4.64), (-.14, 4.48), (-.40, 4.18)]
    poly = []
    for x, h in pts:
        X = x if s < 0 else -x
        poly.append(V((X, ut_front(X, h) - .035, h)))
    prism_poly(ut, "UT_collar_" + ("R" if s < 0 else "L"), poly, (0, -.045, 0), sh_shirt, meta("collar half, 3 vertices of section 09, .045 thick, .035 ahead of the shirt"))
front_strip(ut, "UT_placket", -.065, .065, [4.10, 4.24, 4.38], .015, .01, "SHIRT_DARK", ffn=ut_front, meta=meta("short placket W.13 H.28 at H4.24"))

# ---- apron front: closed slab following the section 10 table
AP_H = [1.10, 1.40, 1.70, 2.00, 2.30, 2.63, 2.88, 3.12, 3.37, 3.62, 3.83, 4.03]
NXA = 7
a_out, a_in = [], []
for li, h in enumerate(AP_H):
    w, _ = apron_wd(h)
    ro, ri = [], []
    for k in range(NXA):
        x = -w / 2 + w * k / (NXA - 1)
        hh = h
        if li == 0:
            hh = 1.10 + .04 * (abs(x) / (w / 2)) ** 2
        if li == len(AP_H) - 1:
            hh = 4.03
        d = apron_front(x, hh)
        ro.append(V((x, d, hh)))
        ri.append(V((x, d + .045, hh)))
    a_out.append(ro)
    a_in.append(ri)
grid_solid(ut, "UT_apron_front", a_out, a_in, sh_apron, meta("apron slab .045 thick, section 10 table, flat |X|<=.33W then +.12 to the edges, bottom edge arc 1.10 centre / 1.14 corners", dims={"rows": APRON_ROWS}))
w43, d43 = apron_wd(4.03)
grid_solid(ut, "UT_apron_top_seam", [[V((-w43 / 2 + w43 * k / 6, apron_front(-w43 / 2 + w43 * k / 6, 4.03) - .008, 4.03)) for k in range(7)],
                                      [V((-w43 / 2 + w43 * k / 6, apron_front(-w43 / 2 + w43 * k / 6, 3.985) - .008, 3.985)) for k in range(7)]],
           [[V((-w43 / 2 + w43 * k / 6, apron_front(-w43 / 2 + w43 * k / 6, 4.03) + .03, 4.03)) for k in range(7)],
             [V((-w43 / 2 + w43 * k / 6, apron_front(-w43 / 2 + w43 * k / 6, 3.985) + .03, 3.985)) for k in range(7)]], sh_const("APRON_SEAM"),
           meta("apron top edge W2.10 H.045 APRON_SEAM"))

# ---- apron belt (wraps the whole torso) H2.57..2.77
belt_rows = []
for h in (2.57, 2.67, 2.77):
    aw, ad = apron_wd(h)
    uw, uf, ub, uc = interp_row(UT_ROWS, h)
    belt_rows.append((h, aw + .12, ad - .055, ub + .06, uc + .05))
loft(ut, "UT_apron_belt", [row_ring(r) for r in belt_rows], lambda n, c: "APRON_SEAM" if n.z > .55 else "APRON_DARK",
     meta=meta("apron waistband H2.57..2.77 thick .055, wraps the torso, no buckle", dims={"rows": belt_rows}))

# ---- shoulder straps (front end on the apron, over the shoulder, down the back to the belt) + back knot
STRAP_L = [(.88, -.86, 3.86), (1.00, -.76, 4.24), (1.14, -.36, 4.58), (1.10, .32, 4.66), (.98, .58, 4.10), (.93, .67, 2.72)]
for s in (-1, 1):
    pts = []
    for i, (x, d, h) in enumerate(STRAP_L):
        if i == 0:
            d = apron_front(x, h) - .03
        pts.append(V((s * x, d, h)))
    pts = catmull(pts, 3)
    rings = []
    for i, p in enumerate(pts):
        T = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        Bx = V((1, 0, 0)) - T * T.dot(V((1, 0, 0)))
        Bx = Bx.normalized() if Bx.length > 1e-4 else V((0, 1, 0))
        N = T.cross(Bx).normalized()
        rings.append(ring_pts(p, Bx, N, .24, .05, 8))
    loft(ut, "UT_strap_" + ("R" if s < 0 else "L"), rings, sh_apron, meta=meta("shoulder strap W.24 thick .05 along the section 11 key points, mirrored", dims={"pts": STRAP_L}))
    for d_ in (-1, 1):
        pass
box_c(ut, "UT_back_knot", (0, .76, 2.67), (.22, .12, .18), sh_apron, ch=.02, meta_=meta("apron back knot .22 x .12 x .18", "prescribed"))
for sx in (-1, 1):
    box_c(ut, "UT_back_tie_end_%d" % sx, (sx * .10, .76, 2.67 - .09 - .225), (.14, .035, .45), sh_apron, meta_=meta("flat tie end .14 x .035 x .45 hanging from the knot", "prescribed"))

# ---- two gold rivets on the front strap ends
for s in (-1, 1):
    nm = "R" if s < 0 else "L"
    cx = s * .88
    cd = apron_front(cx, 3.86) - .045
    disc_d(ut, "UT_rivet_base_" + nm, cx, cd + .012, 3.86, .11, .02, "GOLD_DARK", segs=12, embed=.03)
    disc_d(ut, "UT_rivet_head_" + nm, cx, cd - .022, 3.86, .105, .045, "GOLD", segs=12, embed=.012)
    disc_d(ut, "UT_rivet_facet_" + nm, cx - .04, cd - .026, 3.86 + .04, .028, .01, "GOLD_LIGHT", segs=6)

# ---- 12 stains (16-ray outlines projected on the apron with offset .003)
RAY = [.92, .64, .83, .56, 1, .70, .87, .55, .95, .61, .85, .67, .96, .58, .80, .65]
STAIN_TILES = ("STAIN", "STAIN_DARK", "STAIN_LIGHT")
for i, (cx, ch_, w, h) in enumerate(STAINS):
    ph = (i % 3) * .17
    big = w * h > .12
    outline = []
    for k in range(16):
        r = RAY[k]
        if big and k in ((i * 3) % 16, (i * 5 + 7) % 16, (i * 11 + 3) % 16):
            r *= 1.22
        a = k * 2 * math.pi / 16 + ph
        x = cx + .5 * w * r * math.cos(a)
        hh = ch_ + .5 * h * r * math.sin(a)
        outline.append((x, hh))
    if max(p[1] for p in outline) > 2.55 and min(p[1] for p in outline) < 2.55:
        # the waistband (H2.57..2.77) covers this field: compress the outline below it instead of clamping (no degenerate faces)
        lo_, hi_ = min(p[1] for p in outline), max(p[1] for p in outline)
        outline = [(x, lo_ + (hh - lo_) * (2.55 - lo_) / (hi_ - lo_)) for x, hh in outline]
    plate(ut, "UT_stain_%02d" % (i + 1), outline, lambda x, h: apron_front(x, h) + .001, lambda x, h: apron_front(x, h) - .003, STAIN_TILES[i % 3], ch=.001,
          meta_=meta("stain %d: 16-ray outline, centre (%.2f,%.2f) bbox %.2f x %.2f" % (i + 1, cx, ch_, w, h), "observed+prescribed"))

# ---- towel on the anatomical RIGHT (X<0): relief across u, two red stripes
TW_C = V((-.95, -1.16, 2.155))
TW_REL = [(-.315, 0), (-.24, -.025), (-.13, .008), (-.03, -.020), (.09, .010), (.21, -.020), (.315, 0)]
TW_H = [1.44, 1.66, 1.74, 1.82, 1.90, 2.30, 2.58, 2.87]
t_out, t_in = [], []
for li, h in enumerate(TW_H):
    ro, ri = [], []
    for k, (u, off) in enumerate(TW_REL):
        wscale = 1.0 - .08 * (h - 1.44) / (2.87 - 1.44)
        hh = h + (.025 * math.sin(u * 17.0) if li == 0 else 0.0)
        ro.append(V((TW_C.x + u * wscale, TW_C.y + off, hh)))
        ri.append(V((TW_C.x + u * wscale, TW_C.y + off + .03, hh)))
    t_out.append(ro)
    t_in.append(ri)


def towel_tile(n, c):
    if n.y < -.4 and ((1.66 <= c.z <= 1.74) or (1.82 <= c.z <= 1.90)):
        return "TOWEL_RED"
    if n.y < -.4:
        rel = c.y - TW_C.y
        if rel < -.012:
            return "TOWEL_LIGHT"
        if rel > .004:
            return "TOWEL_SHADOW"
        return "TOWEL"
    return "TOWEL_SHADOW" if n.z < -.5 else "TOWEL"


grid_solid(ut, "UT_towel_front", t_out, t_in, towel_tile, meta("towel front hanging part W.63 H1.43 (H1.44..2.87), relief per section 14, two TOWEL_RED stripes H1.66..1.74 and H1.82..1.90", dims={"relief": TW_REL, "rows": TW_H}))
# short rear tail over the waistband (H2.58..2.87), prescribed
TX0, TX1 = TW_C.x - .26, TW_C.x + .26
grid_solid(ut, "UT_towel_tail", [[V((TX0, TW_C.y + .04, 2.87)), V((TX1, TW_C.y + .04, 2.87))], [V((TX0, TW_C.y + .15, 2.58)), V((TX1, TW_C.y + .15, 2.58))]],
           [[V((TX0, TW_C.y + .075, 2.87)), V((TX1, TW_C.y + .075, 2.87))], [V((TX0, TW_C.y + .185, 2.58)), V((TX1, TW_C.y + .185, 2.58))]], sh_const("TOWEL_SHADOW"),
           meta("short rear tail of the towel H2.58..2.87 (hidden behind the front part)", "prescribed"))

# ----------------------------------------------------------------------------------------------
# LowerTorso, legs, trouser cuffs, boots
# ----------------------------------------------------------------------------------------------
lt = PM("LowerTorso", JV["Root"])
loft(lt, "LT_hip", [row_ring(r) for r in LT_ROWS], sh_pants, meta=meta("pants hip, section 15 rows", dims={"rows": LT_ROWS}))
front_strip(lt, "LT_centre_seam", -.0125, .0125, [1.77, 1.98, 2.18], .008, .01, "PANTS_DARK", ffn=lambda x, h: front_at(LT_ROWS, min(max(h, 1.82), 2.34), x), meta=meta("crotch seam W.025 H1.77..2.18"))

for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    hip, knee, ank = JV[side + "Hip"], JV[side + "Knee"], JV[side + "Ankle"]
    ul = PM(side + "UpperLeg", hip)
    lu = Limb(hip, knee)
    t0, t1 = (hip.z - 2.10) / (hip.z - knee.z), (hip.z - 1.01) / (hip.z - knee.z)
    loft(ul, "UL_thigh_" + side, [lu.ring(t0, 1.10, 1.00, .09), lu.ring((t0 + t1) / 2, 1.06, .965, .09), lu.ring(t1, 1.02, .93, .09)], sh_pants, meta=meta("thigh H1.01..2.10, 1.10 x 1.00 -> 1.02 x .93"))
    ll = PM(side + "LowerLeg", knee)
    lk = Limb(knee, ank)
    k0, k1 = (knee.z - 1.10) / (knee.z - ank.z), (knee.z - .48) / (knee.z - ank.z)
    loft(ll, "LL_shin_" + side, [lk.ring(k0, 1.01, .95, .07), lk.ring(k1, 1.01, .95, .07)], sh_pants, meta=meta("shin H.48..1.10, 1.01 x .95"))
    cuff = [lk.ring((knee.z - .60) / (knee.z - ank.z), 1.03, .97, .07), lk.ring((knee.z - .615) / (knee.z - ank.z), 1.06, 1.0, .08),
            lk.ring((knee.z - .755) / (knee.z - ank.z), 1.06, 1.0, .08), lk.ring((knee.z - .77) / (knee.z - ank.z), 1.03, .97, .07)]
    loft(ll, "LL_cuff_" + side, cuff, lambda n, c: "PANTS_LIGHT" if n.z > .55 else "PANTS_DARK", meta=meta("trouser hem H.60..0.77, 1.06 x 1.00, .025 PANTS_DARK edge"))
    ft = PM(side + "Foot", ank)
    cx = s * .67
    loft(ft, "FT_sole_" + side, [ring8(.625 - g, -.935 + g, .615 - g, .11, cx, 0, h) for h, g in ((0.0, .025), (.02, 0), (.11, 0), (.13, 0))], sh_const("SOLE"), meta=meta("sole H0..0.13, W1.25, D-.935..+.615"))
    up = [ring8(.62, -.93, .60, .11, cx, 0, .13), ring8(.60, -.90, .58, .11, cx, 0, .30), ring8(.58, -.80, .57, .11, cx, 0, .46),
          ring8(.55, -.34, .56, .10, cx, 0, .54), ring8(.54, -.20, .55, .10, cx, 0, .66)]
    loft(ft, "FT_upper_" + side, up, sh_shoe, meta=meta("boot: toe D-.94..-.20 H.13..46, instep/shaft D-.20..55 H.13..66, W1.25 -> 1.08"))


# ----------------------------------------------------------------------------------------------
# tongs branch centres u(H) (section 24): X = 2.30 +/- u
# ----------------------------------------------------------------------------------------------
TONG_U = [(2.56, .055), (3.10, .080), (3.50, .100), (4.25, .145), (4.30, .150), (4.72, .210), (5.05, .265), (5.45, .310), (5.92, .325)]


def branch_u(h):
    if h <= TONG_U[0][0]:
        return TONG_U[0][1]
    for (h0, u0), (h1, u1) in zip(TONG_U, TONG_U[1:]):
        if h0 <= h <= h1:
            return u0 + (u1 - u0) * (h - h0) / (h1 - h0)
    return TONG_U[-1][1]


def tile_layer_set(bm, fn, keep=("SKIN_SHADOW",)):
    tl = bm.faces.layers.int.get("tile") or bm.faces.layers.int.new("tile")
    for f in bm.faces:
        f.normal_update()
        cur = PAL[f[tl]][0]
        if cur in keep:
            continue
        f[tl] = TILE[fn(f.normal.copy(), f.calc_center_median())]


UP_SKIN = [(0.0, .94, .88), (.70, .84, .79), (1.0, .78, .73)]
LO_SEC = [(0.0, .77, .72), (.50, .70, .65), (1.0, .64, .59)]


def build_arm(side, S, E, W):
    ua = PM(side + "UpperArm", S)
    lu = Limb(S, E)
    L1 = lu.L
    sl = [(-.02, .99, .93), (0.0, .99, .93), (.63, .89, .84), (.73, .885, .835)]
    loft(ua, "UA_sleeve_" + side, [lu.ring(t, w, d, .09) for t, w, d in sl], sh_shirt, meta=meta("short red sleeve t0..0.73, skin section + .05"))
    cuff = [lu.ring(.63, .89, .84, .08), lu.ring(.64, .89, .84, .08, .02), lu.ring(.715, .885, .835, .08, .02), lu.ring(.73, .885, .835, .08)]
    loft(ua, "UA_cuff_" + side, cuff, lambda n, c: "SHIRT_LIGHT" if n.z > .55 else "SHIRT_DARK", meta=meta("sleeve cuff band .10 along the segment, SHIRT_DARK"))
    sec = [(0.0, .94, .88), (.70, .84, .79), (1.0, .78, .73), (1.0 + .02 / L1, .78, .73)]
    loft(ua, "UA_skin_" + side, [lu.ring(t, w, d, .09) for t, w, d in sec], sh_skin_arm, meta=meta("upper-arm skin .94x.88 -> .84x.79 -> .78x.73"))
    la = PM(side + "LowerArm", E)
    ll = Limb(E, W)
    ext = .02 if side == "Right" else -.03
    lsec = [(-.02 / ll.L, .77, .72), (0.0, .77, .72), (.50, .70, .65), (1.0, .64, .59), (1.0 + ext / ll.L, .64, .59)]
    loft(la, "LA_forearm_" + side, [ll.ring(t, w, d, .08) for t, w, d in lsec], sh_skin_arm, meta=meta("forearm .77x.72 -> .70x.65 -> .64x.59, closed caps"))
    return lu, ll


LUA, LLA = build_arm("Right", JV["RightShoulder"], JV["RightElbow"], JV["RightWrist"])
RUA, RLA = build_arm("Left", JV["LeftShoulder"], JV["LeftElbow"], JV["LeftWrist"])


def cutter(P, faces, tile="SKIN_SHADOW"):
    bm = solid_tiled(P, faces, tile)
    ob = bm_to_obj(bm, "tmp_cut")
    bm.free()
    return ob


def apply_cut(o, co, op):
    bool_apply(o, co, op)
    bpy.data.objects.remove(co, do_unlink=True)


def finish_hand(pm, cid, o, meta_):
    bm = obj_to_bm(o)
    bpy.data.objects.remove(o, do_unlink=True)
    tile_layer_set(bm, sh_skin_arm)
    pm.append_bm(cid, bm, None, meta_)
    bm.free()


# free right hand: centre (-2.13,-.10,1.97), W.75 D.68 H.73, inner thumb, lower notch W.14 H.19 D.18
hr = PM("RightHand", JV["RightWrist"])
c = V((-2.13, -.10, 1.97))
base = box_solid(c.x - .375, c.x + .375, c.y - .34, c.y + .34, c.z - .365, c.z + .365, "SKIN", ch=.055)
o = bm_to_obj(base, "tmp_hand")
base.free()
notch = box_solid(c.x - .07, c.x + .07, c.y - .35, c.y - .35 + .19, c.z - .375, c.z - .375 + .20, "SKIN_SHADOW")
thumb = box_solid(-1.80 - .075, -1.80 + .075, -.33 - .075, -.33 + .075, 2.03 - .15, 2.03 + .15, "SKIN", ch=.03)
for nm, bmx, op in (("notch", notch, 'DIFFERENCE'), ("thumb", thumb, 'UNION')):
    co = bm_to_obj(bmx, "tmp_" + nm)
    bmx.free()
    apply_cut(o, co, op)
finish_hand(hr, "HAND_Right", o, meta("free right hand block .75 x .68 x .73, inner thumb, lower notch .14 x .19 x .18 (boolean EXACT)"))

# left grip hand: G=(2.30,-.62,3.50), .78 x .74 x .82; hidden capsule channel following the branch divergence, rear slot W.06
hl = PM("LeftHand", JV["LeftWrist"])
G = GRIP_C
base = box_solid(G.x - .39, G.x + .39, G.y - .37, G.y + .37, G.z - .41, G.z + .41, "SKIN", ch=.055)
o = bm_to_obj(base, "tmp_hand")
base.free()
HLV = [3.04, 3.20, 3.35, 3.50, 3.65, 3.80, 3.96]
chan_rings, slot_rings = [], []
for h in HLV:
    u = branch_u(h)
    hw = u + .075 + .02
    chan_rings.append(ring8(hw, G.y - .115, G.y + .115, .035, G.x, 0, h))
    slot_rings.append([V((G.x - .03, G.y, h)), V((G.x + .03, G.y, h)), V((G.x + .03, G.y + .37 + .05, h)), V((G.x - .03, G.y + .37 + .05, h))])
for nm, rings in (("chan", chan_rings), ("slot", slot_rings)):
    n_ = len(rings[0])
    P = [p for r in rings for p in r]
    co = cutter(P, loft_faces(len(rings), n_))
    apply_cut(o, co, 'DIFFERENCE')
tb = box_solid(2.02 - .075, 2.02 + .075, -.935 - .075, -.935 + .075, 3.58 - .15, 3.58 + .15, "SKIN", ch=.035)
co = bm_to_obj(tb, "tmp_thumb")
tb.free()
apply_cut(o, co, 'UNION')
for gh in (3.29, 3.47, 3.65):
    gb = box_solid(G.x - .155, G.x + .155, G.y - .37 - .01, G.y - .37 + .008, gh - .006, gh + .006, "SKIN_SHADOW")
    co = bm_to_obj(gb, "tmp_g")
    gb.free()
    apply_cut(o, co, 'DIFFERENCE')
finish_hand(hl, "HAND_Left", o, meta("grip hand .78 x .74 x .82 at G; capsule channel (W.40 D.23, widening with the branches, clearance .02), rear slot W.06, thumb pad, 3 finger grooves (boolean EXACT)"))


def carve_forearm():
    pm = PARTS["LeftLowerArm"]
    me = bpy.data.meshes.new("tmp_fa")
    pm.bm.to_mesh(me)
    fo = bpy.data.objects.new("tmp_fa", me)
    SCENE.collection.objects.link(fo)
    P = [p for r in chan_rings for p in r]
    co = cutter(P, loft_faces(len(chan_rings), len(chan_rings[0])))
    apply_cut(fo, co, 'DIFFERENCE')
    bm2 = obj_to_bm(fo)
    bpy.data.objects.remove(fo, do_unlink=True)
    tile_layer_set(bm2, sh_skin_arm)
    pm.bm.free()
    pm.bm = bm2
    pm.tl = bm2.faces.layers.int.get("tile")


carve_forearm()


# ----------------------------------------------------------------------------------------------
# Head: bald shell, ears, eyes, heavy brows, nose, closed mouth, big curled moustache, side hair
# ----------------------------------------------------------------------------------------------
hd = PM("Head", JV["Neck"])
loft(hd, "HD_shell", [row_ring(r) for r in HEAD_ROWS], sh_skin, meta=meta("head shell W1.88 D1.50 H1.66 (4.74..6.40), front plane D-.74, cheeks -.78 at H5.12, jaw to X+/-.83", dims={"rows": HEAD_ROWS}))
for s in (-1, 1):
    nm = "R" if s < 0 else "L"
    box_c(hd, "HD_ear_" + nm, (s * 1.00, -.02, 5.44), (.27, .32, .43), sh_skin, ch=.045, meta_=meta("ear .27 x .32 x .43, bevel .045"))
    box_c(hd, "HD_ear_recess_" + nm, (s * (1.00 + .135 + .002), -.02, 5.44), (.012, .12, .22), sh_const("SKIN_SHADOW"), meta_=meta("ear recess W.12 H.22 depth .045 (flat shadow facet)", "prescribed"))
    ex, eh = s * .34, 5.80
    disc_d(hd, "HD_eye_white_" + nm, ex, -.78, eh, .17, .045, "EYE_WHITE", segs=12, ry=.15)
    nx_ = ex - s * .012
    disc_d(hd, "HD_iris_" + nm, nx_, -.795, eh, .08, .02, "IRIS", segs=10)
    disc_d(hd, "HD_pupil_" + nm, nx_, -.802, eh, .0525, .02, "PUPIL", segs=8)
    disc_d(hd, "HD_glint_" + nm, nx_ - .02, -.806, eh + .02, .0175, .02, "EYE_WHITE", segs=4, ry=.0225)
    # heavy brows: outer (-.73,6.08) -> inner (-.13,5.98), thickness .18, depth .09
    bo = [(-.73, 6.17), (-.13, 6.07), (-.13, 5.89), (-.73, 5.99)]
    if s > 0:
        bo = [(-x, h) for x, h in bo][::-1]
    plate(hd, "HD_brow_" + nm, bo, lambda x, h: hf(h, x) + .01, lambda x, h: hf(h, x) - .09, "BROW", ch=.02, meta_=meta("heavy brow W.60 H.18, depth .09, inner end lowered (stern)"))
    box_c(hd, "HD_nostril_" + nm, (s * .075, -.995, 5.40), (.035, .04, .02), sh_const("SKIN_SHADOW"), meta_=meta("nostril facet .035 x .02", "prescribed"))

NOSE_ROWS_ = [(5.39, .40, -1.00, -.60, .06), (5.52, .42, -1.02, -.60, .06), (5.62, .34, -.90, -.60, .05), (5.70, .20, -.80, -.60, .04)]
loft(hd, "HD_nose", [row_ring(r) for r in NOSE_ROWS_], sh_nose, meta=meta("nose: root (0,-.78,5.70), tip (0,-1.02,5.52), W.42 H.31 proud .28", dims={"rows": NOSE_ROWS_}))
plate(hd, "HD_mouth", [(-.225, 5.0675), (.225, 5.0675), (.225, 5.0325), (-.225, 5.0325)], lambda x, h: hf(h, x) + .01, lambda x, h: hf(h, x) - .004, "MOUTH", ch=.004,
      meta_=meta("closed mouth line W.45 H.035 at H5.05"))
plate(hd, "HD_lip", [(-.225, 5.0325), (.225, 5.0325), (.225, 4.9975), (-.225, 4.9975)], lambda x, h: hf(h, x) + .01, lambda x, h: hf(h, x) - .006, "LIP", ch=.004, meta_=meta("lower lip .035 at H5.00"))

# massive moustache: right lobe outline from section 20, three depth levels D -.79 / -.96 / -1.04
MUS = [(-.03, 5.35), (-.25, 5.40), (-.45, 5.31), (-.62, 5.35), (-.71, 5.50), (-.80, 5.43), (-.82, 5.23), (-.70, 5.10), (-.44, 5.08), (-.19, 5.15), (-.03, 5.22)]
mc = (sum(p[0] for p in MUS) / len(MUS), sum(p[1] for p in MUS) / len(MUS))
for s in (-1, 1):
    for lvl, (kscale, dfront) in enumerate(((1.0, -.79), (.80, -.96), (.52, -1.04))):
        ol = [(mc[0] + (x - mc[0]) * kscale, mc[1] + (h - mc[1]) * kscale) for x, h in MUS]
        if s > 0:
            ol = [(-x, h) for x, h in ol][::-1]
        plate(hd, "HD_moustache_%s_L%d" % ("R" if s < 0 else "L", lvl + 1), ol, lambda x, h: hf(h, x) + .01, lambda x, h, d=dfront: d, sh_hair, ch=.025,
              meta_=meta("moustache lobe level %d (outline x%.2f, front D%.2f), upturned outer tip" % (lvl + 1, kscale, dfront)))

# side hair: temple blocks (two layers), lower sideburn, low rear U band; bald crown stays free
for s in (-1, 1):
    nm = "R" if s < 0 else "L"
    box_c(hd, "HD_hair_side_low_" + nm, (s * .91, -.02, 5.88 - .1175), (.20, .56, .235), sh_hair, ch=.035, meta_=meta("temple block layer 1, D-.30..+.26"))
    box_c(hd, "HD_hair_side_up_" + nm, (s * .91, .00, 5.88 + .1175), (.20, .50, .235), sh_hair, ch=.035, meta_=meta("temple block layer 2, top H6.10"))
    box_c(hd, "HD_sideburn_" + nm, (s * .93, .20, 5.675), (.14, .22, .31), sh_hair, ch=.03, meta_=meta("lower sideburn H5.52..5.83, behind the ear"))


def hpath_back(h):
    w, f, b, c = interp_row(HEAD_ROWS, h)
    a = w / 2.0
    return [(-a, b - c), (-a + c, b), (a - c, b), (a, b - c)]


band(hd, "HD_hair_rear_U", [5.65, 5.78, 5.90, 5.98], hpath_back, .07, -.01, sh_hair, meta_=meta("low rear U band H5.65..5.98, thickness .07", "prescribed"))


# ----------------------------------------------------------------------------------------------
# GrillTongs (sections 24..27): two wooden handles, two steel stems, two paddles, lower bridge
# ----------------------------------------------------------------------------------------------
tg = PM("GrillTongs", GRIP_C)
BLADE_PROFILE = [(-.055, 5.03), (-.18, 5.30), (-.19, 5.67), (-.07, 5.92), (.10, 5.82), (.18, 5.50), (.11, 5.20), (.055, 5.03)]


def blade_u(h):
    return .265 + (.325 - .265) * (h - 5.03) / (5.92 - 5.03)


for s in (-1, 1):
    nm = "R" if s < 0 else "L"
    wood_h = [2.56, 3.10, 3.50, 3.90, 4.25]
    P = [V((GRIP_C.x + s * branch_u(h), GRIP_C.y, h)) for h in wood_h]
    sweep(tg, "TG_wood_" + nm, P, [.13, .15, .15, .155, .16], [.16, .17, .17, .175, .18], sh_wood, up=V((0, -1, 0)), n=8, c=.02,
          meta_=meta("wooden handle H2.56..4.25, section .13x.16 -> .16x.18, centre u=+/-.055..+.145", dims={"levels": wood_h}))
    box_c(tg, "TG_cap_" + nm, (GRIP_C.x + s * .055, GRIP_C.y, 2.53), (.13, .16, .06), sh_const("WOOD_DARK"), ch=.012, meta_=meta("dark end cap H2.50..2.56 W.13 D.16", "observed+prescribed"))
    st_h = [4.17, 4.30, 4.72, 5.05, 5.11]
    P = [V((GRIP_C.x + s * branch_u(h), GRIP_C.y, h)) for h in st_h]
    sweep(tg, "TG_stem_" + nm, P, [.075, .075, .08, .105, .105], [.085] * 5, sh_steel, up=V((0, -1, 0)), n=8, c=.012,
          meta_=meta("steel stem H4.17..5.11 (enters the wood .08 and the paddle .06), .075..105 x .085", dims={"levels": st_h}))
    pts = []
    for px, h in BLADE_PROFILE:
        pts.append((GRIP_C.x + s * (blade_u(h) + px), h))
    if s < 0:
        pts = pts[::-1]
    xs = [p[0] for p in pts]
    xmin, xmax = min(xs), max(xs)

    def front_fn(x, h, _xmin=xmin, _xmax=xmax, _s=s):
        t = (x - _xmin) / (_xmax - _xmin)
        if _s < 0:
            t = 1 - t
        return GRIP_C.y - .0425 + (.02 * (t - .35) / .65 if t > .35 else 0.0)

    def btile(n, c, _xmin=xmin, _xmax=xmax, _s=s):
        if abs(n.y) < .35:
            return "STEEL_EDGE" if n.z > .3 else "STEEL_LIGHT"
        if n.y < -.5:
            t = (c.x - _xmin) / (_xmax - _xmin)
            if _s < 0:
                t = 1 - t
            return "STEEL_DARK" if t > .35 else "STEEL"
        return "STEEL_DARK"

    plate(tg, "TG_blade_" + nm, pts, lambda x, h: GRIP_C.y + .0425, front_fn, btile, ch=.012, meta_=meta("steel paddle thickness .085, profile of section 27, one plane break at 35% width (dD .02)", dims={"profile": BLADE_PROFILE}))
box_c(tg, "TG_bridge", (GRIP_C.x, GRIP_C.y, 2.58), (.12, .07, .08), sh_const("STEEL"), ch=.012, meta_=meta("lower bridge W.12 D.07 H.08", "prescribed"))


# ----------------------------------------------------------------------------------------------
# materials / UV / vertex colors / mesh objects
# ----------------------------------------------------------------------------------------------
atlas = bpy.data.images.new("GrillDad_Palette", ATLAS_W, ATLAS_H, alpha=False)
atlas.colorspace_settings.name = 'sRGB'   # must be set BEFORE writing pixels
px = [0.0] * (ATLAS_W * ATLAS_H * 4)
fill = hex_rgb(_H["APRON"])
for ty in range(ATLAS_H):
    for tx in range(ATLAS_W):
        idx = (ty // TILE_PX) * COLS + (tx // TILE_PX)
        rgb = hex_rgb(PAL[idx][1]) if idx < len(PAL) else fill
        r, g, b = (c / 255.0 for c in rgb)
        o = ((ATLAS_H - 1 - ty) * ATLAS_W + tx) * 4
        px[o:o + 4] = [r, g, b, 1.0]
atlas.pixels.foreach_set(px)
atlas.filepath_raw = os.path.join(OUT, "GrillDad_Palette.png")
atlas.file_format = 'PNG'
atlas.save()
atlas.pack()

MATP = bpy.data.materials.new("GrillDad_Palette")
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

PROPS = ("GrillTongs",)
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
# armature (standard-compatible hierarchy) + rigid 100% weights for the 15 body parts
# ----------------------------------------------------------------------------------------------
arm_data = bpy.data.armatures.new("GrillDad_Armature")
ARM_OB = bpy.data.objects.new("GrillDad_Armature", arm_data)
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
    hand_tail = GRIP_C if side == "Left" else JV["RightWrist"] + V((0, 0, -.68))
    BONES += [
        (side + "UpperArm", "UpperTorso", JV[side + "Shoulder"], JV[side + "Elbow"]),
        (side + "LowerArm", side + "UpperArm", JV[side + "Elbow"], JV[side + "Wrist"]),
        (side + "Hand", side + "LowerArm", JV[side + "Wrist"], hand_tail),
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
    if pm.runtime in PROPS:
        continue
    ob = pm.obj
    vg = ob.vertex_groups.new(name=pm.runtime)
    vg.add([v.index for v in ob.data.vertices], 1.0, 'REPLACE')
    md = ob.modifiers.new("Armature", 'ARMATURE')
    md.object = ARM_OB
    ob.parent = ARM_OB
    ob.matrix_parent_inverse = Matrix.Identity(4)
tongs_ob = PARTS["GrillTongs"].obj
PB = ARM_OB.pose.bones

# ----------------------------------------------------------------------------------------------
# cameras / light / render helpers
# ----------------------------------------------------------------------------------------------
world = bpy.data.worlds.new("FD_World")
SCENE.world = world
world.use_nodes = True
_wn = world.node_tree.nodes
_wl = world.node_tree.links
_bg_a = _wn["Background"]
_bg_a.inputs[0].default_value = (0.90, 0.88, 0.84, 1.0)
_bg_a.inputs[1].default_value = 0.66
_bg_b = _wn.new("ShaderNodeBackground")
_bg_b.inputs[0].default_value = (0.92, 0.90, 0.87, 1.0)
_bg_b.inputs[1].default_value = 1.0
_lp = _wn.new("ShaderNodeLightPath")
_mix = _wn.new("ShaderNodeMixShader")
_wl.new(_lp.outputs["Is Camera Ray"], _mix.inputs[0])
_wl.new(_bg_a.outputs[0], _mix.inputs[1])
_wl.new(_bg_b.outputs[0], _mix.inputs[2])
_wl.new(_mix.outputs[0], _wn["World Output"].inputs["Surface"])
sun_d = bpy.data.lights.new("FD_Key", 'SUN')
sun_d.energy = 1.8
sun = bpy.data.objects.new("FD_Key", sun_d)
SCENE.collection.objects.link(sun)
sun.rotation_euler = (math.radians(52), math.radians(8), math.radians(-38))
fill_d = bpy.data.lights.new("FD_Fill", 'SUN')
fill_d.energy = 0.55
fill_d.use_shadow = False
fill = bpy.data.objects.new("FD_Fill", fill_d)
SCENE.collection.objects.link(fill)
fill.rotation_euler = (math.radians(60), 0, math.radians(140))
cam_d = bpy.data.cameras.new("FD_Cam")
CAM = bpy.data.objects.new("FD_Cam", cam_d)
SCENE.collection.objects.link(CAM)
SCENE.camera = CAM
SCENE.render.engine = 'BLENDER_EEVEE'
SCENE.eevee.taa_render_samples = 8 if QUICK else 32
SCENE.render.image_settings.file_format = 'PNG'
SCENE.view_settings.view_transform = 'Standard'
SCENE.render.film_transparent = False
# floor shadow catcher is omitted (clean neutral background like the first two dads)


def cam_look(loc, target, lens=70.0):
    CAM.location = V(loc)
    CAM.rotation_euler = (V(target) - V(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.type, cam_d.lens, cam_d.sensor_width = 'PERSP', lens, 36.0


def orbit(target, dist, az_deg, el_deg):
    az, el = math.radians(az_deg), math.radians(el_deg)
    t = V(target)
    return t + V((dist * math.sin(az) * math.cos(el), -dist * math.cos(az) * math.cos(el), dist * math.sin(el)))


RENDERED = []


def shot(name, loc, target, res=(1000, 1000), lens=70.0, show_only=None, hide=None):
    for pm in PARTS.values():
        hid = (show_only is not None and pm.runtime not in show_only) or (hide is not None and pm.runtime in hide)
        pm.obj.hide_render = hid
    SCENE.render.resolution_x, SCENE.render.resolution_y = res
    cam_look(loc, target, lens)
    SCENE.render.filepath = os.path.join(OUT, "renders", name)
    bpy.ops.render.render(write_still=True)
    RENDERED.append(name)
    print("RENDERED", name)


# ----------------------------------------------------------------------------------------------
# audits
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


BODY = [PARTS[k].obj for k in PARTS if k not in PROPS]
lo, hi = world_bounds(BODY)
head_lo, head_hi = world_bounds([PARTS["Head"].obj])
ft_lo, _ = world_bounds([PARTS["RightFoot"].obj, PARTS["LeftFoot"].obj])
tg_lo, tg_hi = world_bounds([tongs_ob])
body_tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in BODY)
tongs_tris = sum(len(p.vertices) - 2 for p in tongs_ob.data.polygons)
print("BOUNDS body", tuple(round(x, 3) for x in lo), tuple(round(x, 3) for x in hi))
print("TONGS", tuple(round(x, 3) for x in tg_lo), tuple(round(x, 3) for x in tg_hi))
print("HEAD", tuple(round(x, 3) for x in head_lo), tuple(round(x, 3) for x in head_hi), "FEET", round(ft_lo.z, 4))
print("TRIS body", body_tris, "tongs", tongs_tris)

from collections import Counter
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
    AUDIT[pm.runtime] = {"verts": len(me.vertices), "tris": sum(len(p.vertices) - 2 for p in me.polygons),
                         "open_edges": sum(1 for v in cnt.values() if v == 1), "zero_area": sum(1 for f in bmx.faces if f.calc_area() < 1e-9),
                         "signed_volume": round(vol, 4)}
    bmx.free()


def bvh_of(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    bmx = bmesh.new()
    bmx.from_mesh(me)
    bmx.transform(ev.matrix_world)
    ev.to_mesh_clear()
    t = BVHTree.FromBMesh(bmx)
    pts = [v.co.copy() for v in bmx.verts]
    bmx.free()
    return t, pts


def pair_check(a_name, names):
    res = {}
    ta, pa = bvh_of(PARTS[a_name].obj)
    for n in names:
        t, pts = bvh_of(PARTS[n].obj)
        res[n] = {"overlapping_triangle_pairs": len(ta.overlap(t)), "min_distance": round(min((t.find_nearest(p)[3] or 9e9) for p in pa), 4)}
    return res


TONGS_CHECK = pair_check("GrillTongs", ["LeftHand", "LeftLowerArm", "LeftUpperArm", "UpperTorso", "Head", "LowerTorso", "RightHand", "LeftUpperLeg", "LeftFoot"])
HAND_CHECK = pair_check("LeftHand", ["LeftLowerArm", "UpperTorso", "Head", "LeftUpperArm"])
UT_CHECK = {}
for n in ("Head", "LowerTorso", "LeftUpperArm", "RightUpperArm", "RightUpperLeg", "LeftUpperLeg"):
    ta, pa = bvh_of(PARTS["UpperTorso"].obj)
    t, pts = bvh_of(PARTS[n].obj)
    UT_CHECK[n] = {"overlapping_triangle_pairs": len(ta.overlap(t))}
print("TONGSCHECK", json.dumps(TONGS_CHECK))
print("HANDCHECK", json.dumps(HAND_CHECK))
print("UTCHECK", json.dumps(UT_CHECK))
th_, tp_ = bvh_of(PARTS["LeftHand"].obj)
grip_clear = []
for h in [3.09 + .1 * i for i in range(9)]:
    for sgn in (-1, 1):
        p = V((GRIP_C.x + sgn * branch_u(h), GRIP_C.y, h))
        d = th_.find_nearest(p)[3]
        grip_clear.append(round((d if d is not None else 9e9), 4))
print("GRIP wood-axis -> hand surface distance (H3.09..3.89, both branches):", grip_clear)

# ----------------------------------------------------------------------------------------------
# outputs: blend, FBX, spec JSON
# ----------------------------------------------------------------------------------------------
os.makedirs(os.path.join(OUT, "export"), exist_ok=True)
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
os.makedirs(os.path.join(OUT, "source"), exist_ok=True)
BLEND = os.path.join(OUT, "source", "GrillDad_Redesign.blend")
FBX_BODY = os.path.join(OUT, "export", "GrillDad_R15.fbx")
FBX_TONGS = os.path.join(OUT, "export", "GrillDad_Tongs.fbx")
FBX_SET = dict(use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y',
               mesh_smooth_type='FACE', use_mesh_modifiers=True, bake_anim=False, add_leaf_bones=False,
               path_mode='COPY', embed_textures=True, use_armature_deform_only=False, primary_bone_axis='Y', secondary_bone_axis='X')


def export_fbx(path, objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, object_types={'MESH', 'ARMATURE'}, **FBX_SET)


for pm in PARTS.values():
    pm.obj.hide_render = False
export_fbx(FBX_BODY, [ARM_OB] + BODY)
for nm, path in (("GrillTongs", FBX_TONGS),):
    src = PARTS[nm].obj
    cp = bpy.data.objects.new(nm + "_Geo", src.data.copy())
    cp.data.name = nm + "_Geo_export"
    EXP_COLL.objects.link(cp)
    cp.location = PARTS[nm].joint
    export_fbx(path, [cp])
    bpy.data.objects.remove(cp, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("EXPORTED", FBX_BODY, FBX_TONGS, BLEND)

uvmap = {"atlas": "GrillDad_Palette.png", "size": [ATLAS_W, ATLAS_H], "tile_px": TILE_PX, "columns": COLS, "inset_px": INSET,
         "row0_is_top_of_png": True, "unused_tiles_filled_with": "APRON", "tiles": []}
for i, (n_, h_, use) in enumerate(PAL):
    u0, v0, u1, v1 = tile_uv_patch(i)
    uvmap["tiles"].append({"index": i, "name": n_, "hex": h_, "use": use, "col": i % COLS, "row": i // COLS, "uv_patch": [u0, v0, u1, v1]})
json.dump(uvmap, open(os.path.join(OUT, "data", "palette_uv_map.json"), "w"), indent=1, ensure_ascii=False)


def r3(v):
    return [round(float(c), 4) for c in v]


def roblox_pos(p):
    return [round(-p[0], 4), round(p[2], 4), round(p[1], 4)]


RESULT = {"bounds_neutral": {"min": r3(lo), "max": r3(hi), "height": round(hi.z - lo.z, 4)}, "head_bounds": {"min": r3(head_lo), "max": r3(head_hi)},
          "tongs_bounds": {"min": r3(tg_lo), "max": r3(tg_hi)}, "feet_min_h": round(ft_lo.z, 5), "tris_body": body_tris, "tris_tongs": tongs_tris,
          "audit": AUDIT, "tongs_vs_body": TONGS_CHECK, "hand_vs_body": HAND_CHECK, "torso_vs_parts": UT_CHECK, "grip_wood_axis_to_hand_surface": grip_clear}
json.dump(RESULT, open(os.path.join(OUT, "data", "_build_result.json"), "w"), indent=1)
SPEC = {"asset": "GrillDad_Redesign", "character": "Grill Dad (04, Uncommon)", "units": "studs", "neutral_height": 6.40, "built_height": RESULT["bounds_neutral"]["height"],
        "tables": {"UpperTorso": UT_ROWS, "LowerTorso": LT_ROWS, "Head": HEAD_ROWS, "Apron": APRON_ROWS, "Stains": STAINS},
        "joints_built": {k: list(v) for k, v in JOINTS.items()}, "joints_bind_neutral": {k: r3(v) for k, v in BIND.items()},
        "left_arm_ik": {"shoulder": r3(LEFT_S), "wrist_target": r3(LEFT_W), "pole": r3(LEFT_POLE), "elbow": [round(float(c), 9) for c in LEFT_E],
                        "upper_len": round(SEG_UP, 10), "lower_len": round(SEG_LO, 10),
                        "check_len_upper": round((LEFT_E - LEFT_S).length, 10), "check_len_lower": round((LEFT_W - LEFT_E).length, 10)},
        "grip_center": r3(GRIP_C), "tongs_branch_u": [list(a) for a in TONG_U], "tongs_origin": r3(GRIP_C),
        "palette": [{"index": i, "name": n_, "hex": h_} for i, (n_, h_, _u) in enumerate(PAL)],
        "counts": {"body_tris": body_tris, "tongs_tris": tongs_tris},
        "deviations_from_prompt": [
            "Left arm is built directly in the HoldTongs pose (rest == pose); the neutral bind joints are stored in joints_bind_neutral.",
            "Forearm end is buried -0.03 behind the wrist and carved by the same channel as the hand.",
            "Thumb pad centre D is -.935 instead of -.91 so that it protrudes .035 from the front face.",
            "Paddles are not yawed by +/-8 deg and the wooden top ends are not tilted by 5 deg (both optional in the prompt).",
            "Rear hair U band keeps a constant top H5.98 (the prompt lowers it to 5.88 at the centre).",
            "No spring coils on the bridge (optional).",
            "Apron belt is a closed wrap of the whole torso at H2.57..2.77; the towel rear tail is a short hidden sheet.",
            "Strap front ends follow the real apron surface (D computed) instead of the literal key point D-.86."],
        "measured": RESULT}
json.dump(SPEC, open(os.path.join(OUT, "data", "construction_spec.json"), "w"), indent=1, ensure_ascii=False)
json.dump({"asset": "GrillDad_Redesign", "components": COMP_LOG,
           "part_totals": {k: {"components": len(v.comps), "tris": AUDIT[k]["tris"], "verts": AUDIT[k]["verts"]} for k, v in PARTS.items()},
           "mesh_names": {k: v.geo for k, v in PARTS.items()}}, open(os.path.join(OUT, "data", "component_registry.json"), "w"), indent=1, ensure_ascii=False)
RIG = {"asset": "GrillDad_Redesign", "frame": {"logical": "(X,D,H) forward=-D, anatomical LEFT=+X (tongs hand), towel on the anatomical RIGHT (X<0)", "roblox_position": "(-X, H, D)"},
       "bones": [{"name": n, "parent": p, "head_logical": r3(h), "tail_logical": r3(t), "head_roblox": roblox_pos(h)} for n, p, h, t in BONES],
       "props": {"GrillTongs": {"mount": "TongsGrip WeldConstraint LeftHand -> GrillTongs", "origin_logical": r3(GRIP_C), "grip_world": r3(GRIP_C)}},
       "weights": "100% own bone (rigid style); rest pose == HoldTongs"}
json.dump(RIG, open(os.path.join(OUT, "data", "rig_manifest.json"), "w"), indent=1)
print("RESULT", json.dumps({k: RESULT[k] for k in ("bounds_neutral", "tris_body", "tris_tongs")}))
if NORENDER:
    sys.exit(0)

# ----------------------------------------------------------------------------------------------
# renders (section 31)
# ----------------------------------------------------------------------------------------------
T = V((.45, -.2, 3.30))
MC = V((.25, -.20, 3.30))
shot("01_matching_34.png", (-7.0, -15.0, 7.0), MC, res=(416 * 2, 382 * 2), lens=70)
shot("01b_native_416x382.png", (-7.0, -15.0, 7.0), MC, res=(416, 382), lens=70)
shot("02_front.png", orbit(T, 17, 0, 4), T, res=(1000, 1000))
shot("03_back.png", orbit(T, 17, 180, 4), T, res=(1000, 1000))
shot("04_left_profile.png", orbit(T, 17, 90, 4), T, res=(1000, 1000))
shot("05_right_profile.png", orbit(T, 17, -90, 4), T, res=(1000, 1000))
shot("06_back_right34.png", orbit(T, 17, -150, 12), T, res=(1000, 1000))
HT = V((0, -.2, 5.6))
shot("07_head_front.png", orbit(HT, 6.0, 0, 2), HT, res=(900, 900), hide=("GrillTongs",))
shot("07b_head_34.png", orbit(HT, 6.0, -30, 8), HT, res=(900, 900), hide=("GrillTongs",))
shot("08_head_top.png", orbit(HT, 6.0, 0, 78), HT, res=(900, 900), hide=("GrillTongs",))
shot("08b_head_back.png", orbit(HT, 6.0, 180, 8), HT, res=(900, 900), hide=("GrillTongs",))
AT = V((0, -.3, 2.9))
shot("09_apron_front.png", orbit(AT, 8.0, 0, 4), AT, res=(900, 900), hide=("GrillTongs",))
shot("09b_apron_side.png", orbit(AT, 8.0, -70, 8), AT, res=(900, 900), hide=("GrillTongs",))
shot("09c_apron_back.png", orbit(AT, 8.0, 180, 4), AT, res=(900, 900), hide=("GrillTongs",))
TW = V((-.95, -1.1, 2.15))
shot("10_towel_front.png", orbit(TW, 3.6, -10, 4), TW, res=(900, 900), hide=("GrillTongs",))
shot("10b_towel_side.png", orbit(TW, 3.6, -80, 6), TW, res=(900, 900), hide=("GrillTongs",))
shot("10c_towel_bottom.png", orbit(TW, 3.6, -20, -40), TW, res=(900, 900), hide=("GrillTongs",))
GT = V((2.30, -.62, 3.50))
shot("11_hand_front.png", orbit(GT, 3.2, 0, 4), GT, res=(900, 900))
shot("11b_hand_back.png", orbit(GT, 3.2, 180, 4), GT, res=(900, 900))
shot("11c_hand_top.png", orbit(GT, 3.2, 0, 80), GT, res=(900, 900))
shot("11d_hand_side.png", orbit(GT, 3.2, 90, 4), GT, res=(900, 900))
TT = V((2.30, -.62, 4.20))
shot("12_tongs_front.png", orbit(TT, 6.0, 0, 3), TT, res=(900, 900), show_only=("GrillTongs",))
shot("12b_tongs_side.png", orbit(TT, 6.0, 90, 3), TT, res=(900, 900), show_only=("GrillTongs",))
shot("12c_tongs_back.png", orbit(TT, 6.0, 180, 3), TT, res=(900, 900), show_only=("GrillTongs",))
BT = V((0, -.2, 1.0))
shot("13_shoes.png", orbit(BT, 6.5, -30, 10), BT, res=(1000, 800), hide=("GrillTongs",))
shot("14_gate_full_256.png", (-7.0, -15.0, 7.0), MC, res=(256, 256), lens=70)
print("ALL_RENDERS_DONE", len(RENDERED))
