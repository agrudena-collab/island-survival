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
EXP_COLL = bpy.data.collections.new("EXPORT_FishermanDad")
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
    if n.z < -0.45:
        return "SHIRT_SHADOW"
    return "SHIRT"


def sh_vest(n, c):
    if n.z > 0.55:
        return "VEST_LIGHT"
    if n.z < -0.5 or abs(n.x) > 0.8:
        return "VEST_DARK"
    return "VEST"


def sh_pants(n, c):
    if n.z < -0.6:
        return "PANTS_DARK"
    if n.y < -0.62 or n.z > 0.6:
        return "PANTS_LIGHT"
    return "PANTS"


def sh_boot(n, c):
    if n.z < -0.5:
        return "BOOT_SOLE"
    if n.z > 0.55:
        return "BOOT_LIGHT"
    return "BOOT"


def sh_hair(n, c):
    if n.z < -0.30:
        return "HAIR_SHADOW"
    if n.z > 0.62:
        return "HAIR_LIGHT"
    return "HAIR"


def sh_nose(n, c):
    if n.z < -0.55:
        return "SKIN_SHADOW"
    if n.z > 0.45:
        return "SKIN_LIGHT"
    return "NOSE"


def sh_bucket(n, c):
    if n.z > 0.5:
        return "BUCKET_LIGHT"
    if n.z < -0.5:
        return "BUCKET_DARK"
    if n.y < -0.6:
        return "BUCKET_LIGHT"
    return "BUCKET"


def sh_rod(n, c):
    return "ROD_LIGHT" if n.z > 0.75 else "ROD"


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
# prescribed numeric tables (master prompt sections 08..18)
# ----------------------------------------------------------------------------------------------
UT_ROWS = [(2.12, 2.60, -.93, .55, .13), (2.45, 2.82, -1.02, .62, .16), (2.95, 2.90, -1.04, .65, .17),
           (3.50, 2.78, -.92, .62, .14), (3.98, 2.85, -.72, .55, .12), (4.25, 2.48, -.58, .49, .10)]
LT_ROWS = [(1.55, 2.24, -.68, .48, .12), (1.92, 2.52, -.82, .56, .14), (2.18, 2.62, -.90, .56, .12)]
HEAD_ROWS = [(4.22, 1.40, -.58, .50, .10), (4.40, 1.72, -.70, .62, .12), (4.70, 1.80, -.70, .66, .14),
             (5.40, 1.80, -.70, .66, .14), (5.68, 1.72, -.64, .62, .12), (5.78, 1.56, -.56, .54, .10)]

BIND = {  # neutral bind joints (section 17)
    "RightShoulder": V((-1.65, 0, 4.15)), "RightElbow": V((-1.88, -.03, 3.05)), "RightWrist": V((-2.03, -.08, 2.18)),
    "LeftShoulder": V((1.65, 0, 4.15)), "LeftElbow": V((1.88, -.03, 3.05)), "LeftWrist": V((2.03, -.08, 2.18)),
}


def two_bone_ik(S, Wt, pole, Ebind, Wbind):
    """Section 18: E = S + t*u + sqrt(a^2-t^2)*q with bind segment lengths."""
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
LEFT_W = V((1.98, -.57, 3.44))
LEFT_POLE = V((2.25, .65, 2.70))
LEFT_E, SEG_UP, SEG_LO = two_bone_ik(LEFT_S, LEFT_W, LEFT_POLE, BIND["LeftElbow"], BIND["LeftWrist"])
GRIP_C = V((2.24, -.65, 3.50))          # geometric centre of the grip hand = rod axis point A3
JOINTS = {
    "Root": (0, 0, 1.92), "Waist": (0, 0, 2.18), "Neck": (0, 0, 4.30),
    "RightShoulder": tuple(BIND["RightShoulder"]), "RightElbow": tuple(BIND["RightElbow"]), "RightWrist": tuple(BIND["RightWrist"]),
    "LeftShoulder": tuple(LEFT_S), "LeftElbow": tuple(LEFT_E), "LeftWrist": tuple(LEFT_W),
    "RightHip": (-.66, .02, 1.92), "RightKnee": (-.66, .01, .98), "RightAnkle": (-.66, 0, .45),
    "LeftHip": (.66, .02, 1.92), "LeftKnee": (.66, .01, .98), "LeftAnkle": (.66, 0, .45),
}
JV = {k: V(v) for k, v in JOINTS.items()}


def ut_front(x, h):
    return front_at(UT_ROWS, min(max(h, 2.12), 4.25), x)


def ut_back(x, h):
    return back_at(UT_ROWS, min(max(h, 2.12), 4.25), x)


def lt_front(x, h):
    return front_at(LT_ROWS, min(max(h, 1.55), 2.18), x)


def lt_back(x, h):
    return back_at(LT_ROWS, min(max(h, 1.55), 2.18), x)


def hf(h, x=0.0):
    return front_at(HEAD_ROWS, min(max(h, 4.22), 5.78), x)


def hb(h, x=0.0):
    return back_at(HEAD_ROWS, min(max(h, 4.22), 5.78), x)


VEST_OUT, VEST_IN = .065, .010


def vest_front(x, h):
    return ut_front(x, h) - VEST_OUT


def vest_back(x, h):
    return ut_back(x, h) + VEST_OUT


# belt rows: outside both the trouser hip (+.045) and the shirt hem (+.03)
def _belt_row(h):
    lw, lf, lb, lc = interp_row(LT_ROWS, min(max(h, 1.55), 2.18))
    uw, uf, ub, uc = interp_row(UT_ROWS, min(max(h, 2.12), 4.25))
    if h < 2.12:
        uw, uf, ub = 0, 0, 0
        return (h, lw + .09, lf - .045, lb + .045, lc + .03)
    return (h, max(lw, uw) + .09, min(lf, uf) - .045, max(lb, ub) + .045, max(lc, uc) + .03)


BELT_ROWS = [_belt_row(2.02), _belt_row(2.12), _belt_row(2.24)]


def belt_front(x, h):
    return front_at(BELT_ROWS, min(max(h, 2.02), 2.24), x)


# ----------------------------------------------------------------------------------------------
# UpperTorso: shirt, neck, collar, placket, buttons, vest (front/back/straps), four pockets
# ----------------------------------------------------------------------------------------------
ut = PM("UpperTorso", JV["Waist"])
loft(ut, "UT_shirt_body", [row_ring(r) for r in UT_ROWS], sh_shirt,
     meta=meta("8-point chamfered loft, section 08 rows", dims={"rows": UT_ROWS}))
loft(ut, "UT_neck", [ring8(.30, -.27, .27, .07, 0, 0, 4.11), ring8(.30, -.27, .27, .07, 0, 0, 4.43)], sh_skin,
     meta=meta("neck .60 x .54 x .32, centre H4.27, bevel .07", "prescribed"))
for s in (-1, 1):
    pts = [(-.58, 4.18), (-.18, 4.25), (-.04, 4.05), (-.43, 3.82)]
    poly = []
    for x, h in pts:
        X = x if s < 0 else -x
        poly.append(V((X, ut_front(X, h) - .025, h)))
    prism_poly(ut, "UT_collar_lobe_" + ("R" if s < 0 else "L"), poly, (0, -.045, 0),
               lambda n, c: "SHIRT_LIGHT" if n.y < -0.5 else "SHIRT_SHADOW",
               meta("collar lobe, 4 vertices of section 08, .045 thick, .025 ahead of the shirt"))
front_strip(ut, "UT_placket", -.05, .05, [2.20, 2.8, 3.5, 4.12], .012, .01, "SHIRT_SEAM", ffn=ut_front,
            meta=meta("placket W.10, H2.20..4.12, proud .012"))
for i, hb_ in enumerate((3.92, 3.55, 3.18, 2.80, 2.42)):
    disc_d(ut, "UT_shirt_button_%d" % (i + 1), 0.0, ut_front(0, hb_) - .012 - .025, hb_, .0375, .025, "BUTTON", segs=8, embed=.012)

# ---- vest: wrapped band (front panels open in the middle) + back + shoulder straps
VEST_LEVELS = [2.16, 2.45, 2.95, 3.50, 3.98, 4.20]


def vest_open_half(h):
    # inner edge |X|: .35 at the belly, opening to .47 at the top (section 09)
    if h <= 3.90:
        return .35 + (h - 2.16) * 0.0057 / 1.0 * 0.2
    return .36 + (h - 3.90) * (.47 - .36) / (4.20 - 3.90)


def vest_path(h):
    w, f, b, c = interp_row(UT_ROWS, h)
    a = w / 2.0
    ho = vest_open_half(h)
    return [(ho, f), (a - c, f), (a, f + c), (a, b - c), (a - c, b), (-a + c, b), (-a, b - c), (-a, f + c), (-a + c, f), (-ho, f)]


band(ut, "UT_vest_body", VEST_LEVELS, vest_path, VEST_OUT, VEST_IN, sh_vest,
     meta_=meta("open vest: wrapped band over the shirt, thickness .055, front opening |X|=.35..47, hem H2.16, top H4.20"))
for s in (-1, 1):
    x0, x1 = (s * .585, s * 1.015)
    xa, xb = min(x0, x1), max(x0, x1)
    poly = [V((xa, -.62, 4.185)), V((xb, -.62, 4.185)), V((xb, .52, 4.185)), V((xa, .52, 4.185))]
    prism_poly(ut, "UT_vest_strap_" + ("R" if s < 0 else "L"), poly, (0, 0, .085), sh_vest,
               meta("shoulder strap W.43 across the shoulder from front panel to back"))
front_strip(ut, "UT_vest_back_seam", -.006, .006, [2.28, 3.0, 3.6, 4.2], .012, .02, "VEST_SEAM", ffn=vest_back, rear=True,
            meta=meta("shallow centre back seam .012"))

# ---- four patch pockets with flaps and brass buttons
POCKETS = [  # (name, cx, cH, W, H, proud, flap_top, flap_bot, button_h, folds)
    ("RU", -.91, 3.43, .62, .60, .10, 3.73, 3.51, 3.59, (0.0,)),
    ("LU", .91, 3.43, .62, .60, .10, 3.73, 3.51, 3.59, (0.0,)),
    ("RL", -1.00, 2.65, .78, .72, .13, 3.01, 2.76, 2.84, (-.17, .17)),
    ("LL", 1.00, 2.65, .78, .72, .13, 3.01, 2.76, 2.84, (-.17, .17)),
]
for nm, cx, chh, pw, ph, proud, ftop, fbot, bh, folds in POCKETS:
    x0, x1, h0, h1 = cx - pw / 2, cx + pw / 2, chh - ph / 2, chh + ph / 2
    patch(ut, "UT_pocket_" + nm, [(x0, h0), (x1, h0), (x1, h1), (x0, h1)], vest_front, -.015, proud, sh_vest, ch=.025, nx=4, step=.25,
          meta_=meta("patch pocket %.2f x %.2f, proud %.2f" % (pw, ph, proud)))
    fx0, fx1 = x0 - .0175, x1 + .0175
    flap = [(fx0, ftop), (fx1, ftop), (fx1, fbot + .045), (cx, fbot), (fx0, fbot + .045)]
    patch(ut, "UT_flap_" + nm, flap, vest_front, proud - .002, proud + .035, sh_vest, ch=.012, nx=5, step=.25,
          meta_=meta("pocket flap, pentagon with centre tip .045, thickness .035"))
    disc_d(ut, "UT_flap_button_" + nm, cx, vest_front(cx, bh) - proud - .035 - .018, bh, .0325, .018, "BUTTON", segs=8, embed=.02)
    for fo in folds:
        patch(ut, "UT_pocket_fold_%s_%+.2f" % (nm, fo), [(cx + fo - .006, h0 + .04), (cx + fo + .006, h0 + .04), (cx + fo + .006, fbot), (cx + fo - .006, fbot)],
              vest_front, proud - .004, proud + .004, sh_const("VEST_SEAM"), nx=2, step=.4, meta_=meta("shallow vertical fold .012", "inferred"))

# ----------------------------------------------------------------------------------------------
# LowerTorso: trousers hip, belt, buckle, loops, fly, rear slit pockets
# ----------------------------------------------------------------------------------------------
lt = PM("LowerTorso", JV["Root"])
loft(lt, "LT_hip", [row_ring(r) for r in LT_ROWS], sh_pants, meta=meta("8-point loft, section 11 rows", dims={"rows": LT_ROWS}))
loft(lt, "LT_belt", [row_ring(r) for r in BELT_ROWS], sh_const("BELT"),
     meta=meta("belt H2.02..2.24 proud of hip and shirt hem", dims={"rows": BELT_ROWS}))
# buckle: outer .37 x .27 x .055, opening .25 x .15, centre (0,-.99,2.13)
BK = V((0, -.99, 2.13))
for nm, c, sz in (("top", (0, BK.y, BK.z + .105), (.37, .055, .06)), ("bottom", (0, BK.y, BK.z - .105), (.37, .055, .06)),
                  ("left", (-.155, BK.y, BK.z), (.06, .055, .15)), ("right", (.155, BK.y, BK.z), (.06, .055, .15))):
    box_c(lt, "LT_buckle_" + nm, c, sz, lambda n, c_: "SILVER_LIGHT" if n.z > .5 else "SILVER", ch=.008,
          meta_=meta("buckle bar", "prescribed"))
box_c(lt, "LT_buckle_tongue", (-.0425, BK.y - .004, BK.z), (.135, .02, .025), sh_const("SILVER"), meta_=meta("prong W.025 from X-.11 to +.025", "prescribed"))
for x in (-1.23, -.91, .91, 1.23):
    front_strip(lt, "LT_loop_front_%+.2f" % x, x - .045, x + .045, [1.99, 2.13, 2.28], .02, .03, "PANTS_DARK", ffn=belt_front,
                meta=meta("belt loop W.09, H1.99..2.28"))
for x in (-.72, .72):
    front_strip(lt, "LT_loop_back_%+.2f" % x, x - .045, x + .045, [1.99, 2.28], .06, .03, "PANTS_DARK", ffn=lambda xx, hh: lt_back(xx, hh) + .045, rear=True,
                meta=meta("rear belt loop", "prescribed"))
front_strip(lt, "LT_fly", .054, .066, [1.68, 1.9, 2.08], .006, .01, "PANTS_DARK", ffn=lt_front, meta=meta("fly line W.012 at X=.06, H1.68..2.08"))
for x in (-.56, .56):
    front_strip(lt, "LT_back_slit_%+.2f" % x, x - .21, x + .21, [1.88, 1.98], .012, .01, "PANTS_DARK", ffn=lt_back, rear=True,
                meta=meta("rear slit pocket W.42 H.10 at H1.93", "prescribed"))

# ----------------------------------------------------------------------------------------------
# legs, trouser cuffs, rubber boots, cargo pocket on the anatomical RIGHT thigh
# ----------------------------------------------------------------------------------------------
THIGH_TOP, THIGH_BOT = (1.12, 1.02), (1.04, .96)
SHIN_TOP, SHIN_BOT = (1.04, .96), (1.05, 1.00)


def thigh_front(side_x):
    def f(x, h):
        t = (1.92 - h) / (1.92 - .98)
        t = min(max(t, 0.0), 1.0)
        dc = .02 + (.01 - .02) * t
        d = 1.02 + (.96 - 1.02) * t
        return dc - d / 2.0
    return f


for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    hip, knee, ank = JV[side + "Hip"], JV[side + "Knee"], JV[side + "Ankle"]
    ul = PM(side + "UpperLeg", hip)
    lu = Limb(hip, knee)
    t0 = (hip.z - 1.99) / (hip.z - knee.z)
    t1 = (hip.z - .95) / (hip.z - knee.z)
    loft(ul, "UL_thigh_" + side, [lu.ring(t0, *THIGH_TOP, .09), lu.ring((t0 + t1) / 2, 1.08, .99, .09), lu.ring(t1, *THIGH_BOT, .08)], sh_pants,
         meta=meta("thigh H1.99..0.95, 1.12 x 1.02 -> 1.04 x .96"))
    ll = PM(side + "LowerLeg", knee)
    lk = Limb(knee, ank)
    k0 = (knee.z - 1.02) / (knee.z - ank.z)
    k1 = (knee.z - .62) / (knee.z - ank.z)
    loft(ll, "LL_shin_" + side, [lk.ring(k0, *SHIN_TOP, .08), lk.ring(k1, *SHIN_BOT, .09)], sh_pants,
         meta=meta("shin H1.02..0.62, 1.04 x .96 -> 1.05 x 1.00"))
    cuff = [lk.ring((knee.z - .67) / (knee.z - ank.z), 1.07, 1.02, .08), lk.ring((knee.z - .685) / (knee.z - ank.z), 1.10, 1.05, .09),
            lk.ring((knee.z - .815) / (knee.z - ank.z), 1.10, 1.05, .09), lk.ring((knee.z - .83) / (knee.z - ank.z), 1.07, 1.02, .08)]
    loft(ll, "LL_cuff_" + side, cuff, lambda n, c: "CUFF" if n.z > .55 else ("PANTS_DARK" if n.z < -.5 else "PANTS_LIGHT"),
         meta=meta("trouser cuff H.67..0.83, 1.10 x 1.05, thickness .04, CUFF edge on top"))
    ft = PM(side + "Foot", ank)
    cx = s * .66
    rings = [ring8(.63 - g, -.935 + g, .615 - g, .11, cx, 0, h) for h, g in ((0.0, .025), (.02, 0.0), (.12, 0.0), (.14, .0))]
    loft(ft, "FT_sole_" + side, rings, sh_const("BOOT_SOLE"), meta=meta("sole H0..0.14, W1.26, D-.935..+.615"))
    up = [ring8(.62, -.925, .60, .11, cx, 0, .14), ring8(.60, -.90, .59, .11, cx, 0, .30), ring8(.57, -.80, .57, .11, cx, 0, .45),
          ring8(.52, -.55, .57, .10, cx, 0, .52)]
    loft(ft, "FT_upper_" + side, up, sh_boot, meta=meta("boot foot H.14..0.52, toe bevel .11, broad top facet"))
    sh_ = [ring8(.54, -.45, .61, .11, cx, 0, .45), ring8(.54, -.45, .61, .11, cx, 0, .70), ring8(.53, -.44, .60, .10, cx, 0, .72)]
    loft(ft, "FT_shaft_" + side, sh_, sh_boot, band_tiles={1: "BOOT_LIGHT"}, meta=meta("boot shaft H.45..0.72, W1.08 D1.06, light top edge"))

# cargo pocket, anatomical RIGHT thigh (X<0)
tf = thigh_front(-.66)
patch(PARTS["RightUpperLeg"], "UL_cargo_pocket", [(-1.15, 1.04), (-.61, 1.04), (-.61, 1.62), (-1.15, 1.62)], tf, -.015, .10, sh_pants, ch=.025, nx=4, step=.25,
      meta_=meta("cargo pocket .54 x .58, proud .10, centre (-.88,-.58,1.33)"))
patch(PARTS["RightUpperLeg"], "UL_cargo_flap", [(-1.165, 1.62), (-.595, 1.62), (-.595, 1.465), (-.88, 1.42), (-1.165, 1.465)], tf, .098, .135, sh_const("VEST_DARK"), ch=.012, nx=5, step=.25,
      meta_=meta("cargo flap W.57 H.18, top 1.62, tip 1.42"))
disc_d(PARTS["RightUpperLeg"], "UL_cargo_button", -.88, tf(-.88, 1.48) - .135 - .015, 1.48, .025, .015, "BUTTON", segs=8, embed=.02)
patch(PARTS["RightUpperLeg"], "UL_cargo_seam", [(-.886, 1.06), (-.874, 1.06), (-.874, 1.42), (-.886, 1.42)], tf, .096, .104, sh_const("PANTS_DARK"), nx=2, step=.4,
      meta_=meta("seam .012", "inferred"))


# ----------------------------------------------------------------------------------------------
# rod axis (section 20) - needed by the grip channel in the left hand and by the rod itself
# ----------------------------------------------------------------------------------------------
ROD_A = [  # (X, D, H, outer diameter)
    (2.20, -.65, .10, .18), (2.20, -.65, 2.20, .15), (2.22, -.65, 2.70, .115), (2.24, -.65, 3.50, .095),
    (2.30, -.65, 4.20, .080), (2.42, -.65, 5.20, .064), (2.67, -.65, 6.35, .043), (2.88, -.65, 7.35, .028)]
ROD_PTS = [V(a[:3]) for a in ROD_A]
ROD_DENSE = catmull(ROD_PTS, 6)          # smooth axis through the A points (passes exactly through every A_i)


def rod_axis(h):
    """Axis point (X,-.65,h) of the smoothed rod axis (X, D interpolated on the dense polyline, monotonic in H)."""
    pts = ROD_DENSE
    if h <= pts[0].z:
        return V((pts[0].x, pts[0].y, h))
    for a, b in zip(pts, pts[1:]):
        if a.z <= h <= b.z and b.z > a.z:
            t = (h - a.z) / (b.z - a.z)
            return V((a.x + (b.x - a.x) * t, a.y, h))
    return V((pts[-1].x, pts[-1].y, h))


def rod_diam(h):
    for a, b in zip(ROD_A, ROD_A[1:]):
        if a[2] <= h <= b[2]:
            return a[3] + (b[3] - a[3]) * (h - a[2]) / (b[2] - a[2])
    return ROD_A[-1][3] if h > ROD_A[-1][2] else ROD_A[0][3]


def rod_tangent(h):
    a, b = rod_axis(h - .01), rod_axis(h + .01)
    return (b - a).normalized()


# ----------------------------------------------------------------------------------------------
# arm shells: shoulder / elbow / wrist (right arm neutral, left arm directly in the HoldRod pose)
# ----------------------------------------------------------------------------------------------
UP_SKIN = [(0.0, .88, .82), (.70, .81, .76), (1.0, .76, .70)]
LO_SEC = [(0.0, .75, .69), (.48, .70, .65), (1.0, .64, .59)]


def tile_layer_set(bm, fn, keep=("SKIN_SHADOW",)):
    tl = bm.faces.layers.int.get("tile") or bm.faces.layers.int.new("tile")
    for f in bm.faces:
        f.normal_update()
        cur = PAL[f[tl]][0]
        if cur in keep:
            continue
        f[tl] = TILE[fn(f.normal.copy(), f.calc_center_median())]


def build_arm(side, S, E, W):
    s = -1 if side == "Right" else 1
    ua = PM(side + "UpperArm", S)
    lu = Limb(S, E)
    L1 = lu.L
    sl = [(-.02, .98, .91), (0.0, .98, .91), (.64, .954, .886), (.73, .95, .88)]
    loft(ua, "UA_sleeve_" + side, [lu.ring(t, w, d, .10) for t, w, d in sl], sh_shirt,
         meta=meta("short yellow sleeve t0..0.73, .98 x .91 -> .95 x .88"))
    cuff = [lu.ring(.64, .954, .886, .09), lu.ring(.652, .954, .886, .09, .025), lu.ring(.718, .95, .88, .09, .025), lu.ring(.73, .95, .88, .09)]
    loft(ua, "UA_cuff_" + side, cuff, lambda n, c: "SHIRT_SHADOW" if n.z < -.45 else ("SHIRT_LIGHT" if n.z > .55 else "SHIRT"),
         meta=meta("sleeve cuff t.64..0.73, proud .025, SHIRT_SHADOW underside"))
    sec = [(-.0, .88, .82), (.70, .81, .76), (1.0, .76, .70), (1.0 + .02 / L1, .76, .70)]
    loft(ua, "UA_skin_" + side, [lu.ring(t, w, d, .09) for t, w, d in sec], sh_skin_arm,
         meta=meta("upper-arm skin .88x.82 -> .81x.76 -> .76x.70"))
    la = PM(side + "LowerArm", E)
    ll = Limb(E, W)
    ext = .02 if side == "Right" else -.03
    lsec = [(-.02 / ll.L, .75, .69), (0.0, .75, .69), (.48, .70, .65), (1.0, .64, .59), (1.0 + ext / ll.L, .64, .59)]
    loft(la, "LA_forearm_" + side, [ll.ring(t, w, d, .08) for t, w, d in lsec], sh_skin_arm,
         meta=meta("forearm .75x.69 -> .70x.65 -> .64x.59, closed caps"))
    return lu, ll


LUA, LLA = build_arm("Right", JV["RightShoulder"], JV["RightElbow"], JV["RightWrist"])
RUA, RLA = build_arm("Left", JV["LeftShoulder"], JV["LeftElbow"], JV["LeftWrist"])


# ----------------------------------------------------------------------------------------------
# hands (sections 18, 19)
# ----------------------------------------------------------------------------------------------
def cutter(P, faces, tile="SKIN_SHADOW"):
    bm = solid_tiled(P, faces, tile)
    ob = bm_to_obj(bm, "tmp_cut")
    bm.free()
    return ob


def apply_cut(o, co, op):
    bool_apply(o, co, op)
    bpy.data.objects.remove(co, do_unlink=True)


def finish_hand(pm, cid, o, joint, side, meta_):
    bm = obj_to_bm(o)
    bpy.data.objects.remove(o, do_unlink=True)
    tile_layer_set(bm, sh_skin_arm)
    pm.append_bm(cid, bm, None, meta_)
    bm.free()


# free right hand: centre (-2.08,-.12,1.89), W .72 D .66 H .70, bevel .055, thumb on the inner side, lower notch .15 x .22 x .20
hr = PM("RightHand", JV["RightWrist"])
c = V((-2.08, -.12, 1.89))
base = box_solid(c.x - .36, c.x + .36, c.y - .33, c.y + .33, c.z - .35, c.z + .35, "SKIN", ch=.055)
o = bm_to_obj(base, "tmp_hand")
base.free()
notch = box_solid(c.x - .075, c.x + .075, c.y - .34, c.y - .34 + .21, c.z - .36, c.z - .36 + .23, "SKIN_SHADOW")
thumb = box_solid(-1.76 - .08, -1.76 + .08, -.31 - .07, -.31 + .07, 1.97 - .14, 1.97 + .14, "SKIN", ch=.03)
for nm, bmx, op in (("notch", notch, 'DIFFERENCE'), ("thumb", thumb, 'UNION')):
    co = bm_to_obj(bmx, "tmp_" + nm)
    bmx.free()
    apply_cut(o, co, op)
finish_hand(hr, "HAND_Right", o, JV["RightWrist"], "Right",
            meta("free right hand block .72 x .66 x .70, inner thumb .16 x .14 x .28, lower notch .15 x .22 x .20 (boolean EXACT)"))

# left grip hand: centre G=(2.24,-.65,3.50), .72 x .68 x .80; rod channel r=.065 sweeping along the real rod axis,
# slot W .07 opening only to the REAR face, thumb pad, three finger grooves on the front face
hl = PM("LeftHand", JV["LeftWrist"])
G = GRIP_C
base = box_solid(G.x - .36, G.x + .36, G.y - .34, G.y + .34, G.z - .40, G.z + .40, "SKIN", ch=.055)
o = bm_to_obj(base, "tmp_hand")
base.free()
HLV = [3.04 + .12 * i for i in range(8)]                      # H 3.04 .. 3.88 + (hand spans 3.10..3.90)
HLV = [3.04, 3.20, 3.35, 3.50, 3.65, 3.80, 3.96]
R_CH = .065
chan_rings, slot_rings = [], []
for h in HLV:
    a = rod_axis(h)
    ca = abs(rod_tangent(h).z)
    chan_rings.append([V((a.x + (R_CH / ca) * math.cos(2 * math.pi * k / 12), a.y + R_CH * math.sin(2 * math.pi * k / 12), h)) for k in range(12)])
    slot_rings.append([V((a.x - .035, a.y, h)), V((a.x + .035, a.y, h)), V((a.x + .035, G.y + .34 + .05, h)), V((a.x - .035, G.y + .34 + .05, h))])
for nm, rings in (("chan", chan_rings), ("slot", slot_rings)):
    n_ = len(rings[0])
    P = [p for r in rings for p in r]
    co = cutter(P, loft_faces(len(rings), n_))
    apply_cut(o, co, 'DIFFERENCE')
tb = box_solid(1.95 - .08, 1.95 + .08, -.95 - .07, -.95 + .07, 3.60 - .14, 3.60 + .14, "SKIN", ch=.03)
co = bm_to_obj(tb, "tmp_thumb")
tb.free()
apply_cut(o, co, 'UNION')
for gh in (3.30, 3.48, 3.66):
    gb = box_solid(G.x - .165, G.x + .165, G.y - .34 - .01, G.y - .34 + .008, gh - .006, gh + .006, "SKIN_SHADOW")
    co = bm_to_obj(gb, "tmp_g")
    gb.free()
    apply_cut(o, co, 'DIFFERENCE')
finish_hand(hl, "HAND_Left", o, JV["LeftWrist"], "Left",
            meta("grip hand .72 x .68 x .80 at G; 12-gon rod channel r.065 (clearance .0175) sweeping the rod axis, rear slot W.07, thumb pad, 3 finger grooves (boolean EXACT)"))


# the forearm stub ends inside the grip hand: carve the same rod channel through it so the rod never enters skin
def carve_forearm():
    pm = PARTS["LeftLowerArm"]
    me = bpy.data.meshes.new("tmp_fa")
    pm.bm.to_mesh(me)
    fo = bpy.data.objects.new("tmp_fa", me)
    SCENE.collection.objects.link(fo)
    rings = chan_rings
    P = [p for r in rings for p in r]
    co = cutter(P, loft_faces(len(rings), len(rings[0])))
    apply_cut(fo, co, 'DIFFERENCE')
    bm2 = obj_to_bm(fo)
    bpy.data.objects.remove(fo, do_unlink=True)
    tile_layer_set(bm2, sh_skin_arm)
    pm.bm.free()
    pm.bm = bm2
    pm.tl = bm2.faces.layers.int.get("tile")


carve_forearm()


# ----------------------------------------------------------------------------------------------
# Head: skull shell, ears, eyes, brows, nose, smile, teeth, moustache, side/back hair, bucket hat
# ----------------------------------------------------------------------------------------------
hd = PM("Head", JV["Neck"])
loft(hd, "HD_shell", [row_ring(r) for r in HEAD_ROWS], sh_skin,
     meta=meta("head shell W1.80 D1.36 H1.56 (4.22..5.78), cuts .10..14", dims={"rows": HEAD_ROWS}))
for s in (-1, 1):
    nm = "R" if s < 0 else "L"
    box_c(hd, "HD_ear_" + nm, (s * .93, -.02, 5.08), (.25, .30, .44), sh_skin, ch=.05, meta_=meta("ear .25 x .30 x .44, bevel .05"))
    box_c(hd, "HD_ear_recess_" + nm, (s * (.93 + .125 + .002), -.02, 5.08), (.012, .12, .23), sh_const("SKIN_SHADOW"), meta_=meta("ear recess W.12 H.23 depth .03 (flat shadow facet)", "prescribed"))
    # eyes
    ex, eh = s * .35, 5.20
    disc_d(hd, "HD_eye_white_" + nm, ex, -.725, eh, .18, .03, "EYE_WHITE", segs=12, ry=.16, embed=.0 + .0)
    nx_ = ex - s * .015
    disc_d(hd, "HD_iris_" + nm, nx_, -.742, eh, .095, .02, "IRIS", segs=10)
    disc_d(hd, "HD_pupil_" + nm, nx_, -.749, eh, .065, .02, "PUPIL", segs=8)
    disc_d(hd, "HD_glint_" + nm, nx_ + .03, -.753, eh + .03, .015, .02, "EYE_WHITE", segs=6)
    # brows
    bo = [(-.63, 5.41), (-.17, 5.45), (-.17, 5.55), (-.63, 5.51)]
    bo = [(x * -s if False else (x if s < 0 else -x), h) for x, h in bo]
    if s > 0:
        bo = bo[::-1]
    plate(hd, "HD_brow_" + nm, bo, lambda x, h: hf(h, x) + .01, lambda x, h: hf(h, x) - .045, "BROW", ch=.012,
          meta_=meta("brow thickness .10, proud .045, X-.63..-.17 H5.46..5.50 (cheerful, raised)"))
    # nose wing + nostril facet
    box_c(hd, "HD_nose_wing_" + nm, (s * .20, -.93, 4.95), (.12, .16, .11), sh_nose, ch=.03, meta_=meta("alar wing at X+/-.20, H4.94, D-.94"))
    box_c(hd, "HD_nostril_" + nm, (s * .085, -1.04, 4.895), (.04, .05, .018), sh_const("SKIN_SHADOW"), meta_=meta("nostril facet .04 x .018", "prescribed"))

NOSE_ROWS_ = [(4.89, .34, -1.00, -.60, .05), (4.95, .43, -1.15, -.60, .055), (5.05, .40, -1.13, -.60, .055),
              (5.20, .30, -1.00, -.60, .05), (5.38, .19, -.76, -.60, .04)]
loft(hd, "HD_nose", [row_ring(r) for r in NOSE_ROWS_], sh_nose, meta=meta("nose wedge: root H5.35 W.19, tip H4.95 W.43, front D-1.15, bevel .055", dims={"rows": NOSE_ROWS_}))

# smile cavity, teeth strip, lower lip edge
SMILE = [(-.43, 4.765), (-.215, 4.75), (0, 4.742), (.215, 4.75), (.43, 4.765), (.38, 4.66), (.26, 4.52), (.12, 4.42), (0, 4.39), (-.12, 4.42), (-.26, 4.52), (-.38, 4.66)]
plate(hd, "HD_mouth", SMILE, lambda x, h: hf(h, x) + .012, lambda x, h: hf(h, x) - .006, "MOUTH", ch=.012,
      meta_=meta("open smile cavity W.86 H.36, centre H4.57, corners raised, corner cut .06"))
TEETH = [(-.35, 4.645), (-.17, 4.62), (0, 4.614), (.17, 4.62), (.35, 4.645), (.35, 4.735), (.17, 4.728), (0, 4.724), (-.17, 4.728), (-.35, 4.735)]
plate(hd, "HD_teeth", TEETH, lambda x, h: hf(h, x) + .004, lambda x, h: hf(h, x) - .025, "TEETH", ch=.006,
      meta_=meta("upper teeth strip W.70 H.11, thickness .025, no individual teeth"))
plate(hd, "HD_lower_lip", [(-.22, 4.37), (.22, 4.37), (.22, 4.405), (-.22, 4.405)], lambda x, h: hf(h, x) + .004, lambda x, h: hf(h, x) - .012, "LIP", ch=.006,
      meta_=meta("lower lip edge at H4.39", "prescribed"))

# moustache: two bushy lobes, prescribed outline (section 14), depth .23 at the centre -> .14 at the tips
MUS = [(-.04, 5.02), (-.23, 5.10), (-.48, 5.06), (-.72, 5.11), (-.86, 5.25), (-.84, 5.02), (-.66, 4.88), (-.42, 4.84), (-.18, 4.93)]


def mus_depth(x):
    return max(.14, .23 - .09 * max(0.0, abs(x) - .25) / .61)


for s in (-1, 1):
    ol = MUS if s < 0 else [(-x, h) for x, h in MUS][::-1]
    plate(hd, "HD_moustache_" + ("R" if s < 0 else "L"), ol, lambda x, h: hf(h, x) + .03, lambda x, h: hf(h, x) - mus_depth(x), sh_hair, ch=.025,
          meta_=meta("moustache lobe, section 14 outline, depth .23..14, bevel .025"))

# hair base: horseshoe above the ears and rear band (never the face front)
A_, C_ = .90, .14


def hpath_full(h):
    w, f, b, c = interp_row(HEAD_ROWS, h)
    a = w / 2.0
    return [(-a + c, f), (-a, f + c), (-a, b - c), (-a + c, b), (a - c, b), (a, b - c), (a, f + c), (a - c, f)]


def hpath_back(h):
    w, f, b, c = interp_row(HEAD_ROWS, h)
    a = w / 2.0
    return [(-a, b - c), (-a + c, b), (a - c, b), (a, b - c)]


band(hd, "HD_hair_upper", [5.22, 5.40, 5.55, 5.68], hpath_full, .06, -.01, sh_hair, meta_=meta("grey hair base above the ears, H5.22..5.68, thickness .07"))
band(hd, "HD_hair_back", [4.66, 4.84, 5.02, 5.22], hpath_back, .07, -.01, sh_hair, meta_=meta("rear hair band H4.66..5.22", "prescribed"))
TUFTS = {  # right axis (X,D,H), width, thickness; left mirrored
    "temple_upper": ([(-.84, -.22, 5.46), (-1.02, -.12, 5.40), (-1.10, .02, 5.27)], .24, .15),
    "outer_mid": ([(-.88, -.04, 5.18), (-1.12, .04, 5.07), (-1.17, .15, 5.13)], .28, .17),
    "cheek_lower": ([(-.85, -.12, 4.96), (-1.06, .02, 4.80), (-1.15, .15, 4.85)], .26, .16),
    "rear_lower": ([(-.78, .30, 4.94), (-.98, .45, 4.73), (-1.09, .51, 4.80)], .27, .17),
}
for nm, (pts, w, t) in TUFTS.items():
    for s in (-1, 1):
        P = catmull([V((s * -p[0] if s > 0 else p[0], p[1], p[2])) if False else V((p[0] if s < 0 else -p[0], p[1], p[2])) for p in pts], 2)
        k = len(P)
        ws = [w * f for f in (1.0, 1.0, .92, .78, .55)][:k]
        ts = [t * f for f in (1.0, 1.0, .95, .85, .65)][:k]
        sweep(hd, "HD_hair_tuft_%s_%s" % (nm, "R" if s < 0 else "L"), P, ws, ts, sh_hair, up=V((1, 0, 0)), meta_=meta("hair tuft ribbon, 5 sections, tapering, bevel", "prescribed"))
for row, (xlist, top, bots) in enumerate((((-.78, -.52, -.26, 0.0, .26, .52, .78), 5.64, (4.80, 4.90, 4.82, 4.92, 4.82, 4.90, 4.80)),
                                         ((-.65, -.39, -.13, .13, .39, .65), 5.20, (4.64, 4.72, 4.66, 4.66, 4.72, 4.64)))):
    for i, xs in enumerate(xlist):
        lo = bots[i]
        hs_ = [top, top - (top - lo) * .35, top - (top - lo) * .7, lo]
        dd = .075 + .035 * row
        P = [V((xs * (1 + .05 * (5.64 - h)), hb(h, xs) + dd, h)) for h in hs_]
        sweep(hd, "HD_hair_back_strand_%d_%d" % (row, i), P, [.30, .30, .27, .20], [.15, .15, .13, .09], sh_hair, up=V((0, 1, 0)),
              meta_=meta("broad rear strand row %d" % row, "prescribed"))

# moustache tip curls (rise up and outward, per the reference)
for s in (-1, 1):
    pts = [V((s * .80, -.80, 5.12)), V((s * .93, -.77, 5.28)), V((s * 1.00, -.70, 5.40))]
    sweep(hd, "HD_moustache_curl_" + ("R" if s < 0 else "L"), catmull(pts, 2), [.20, .18, .15, .12, .08], [.16, .14, .12, .10, .07], sh_hair, up=V((0, 1, 0)),
          meta_=meta("moustache tip curl rising outward", "inferred"))

# ---- bucket hat (section 16)
N_H = 16
D0 = -.02


def ell(a, b, h, cd=D0, jitter=None):
    pts = []
    for k in range(N_H):
        th = 2 * math.pi * k / N_H
        z = h + (jitter[k] if jitter else 0.0)
        pts.append(V((a * math.cos(th), cd + b * math.sin(th), z)))
    return pts


def tul_dims(h):
    t = (h - 5.78) / (6.32 - 5.78)
    return (1.98 + (1.76 - 1.98) * t) / 2.0, (1.62 + (1.42 - 1.62) * t) / 2.0


JIT = [(((k * 7) % 5) - 2) * .012 for k in range(N_H)]
tul_rings = [ell(.99, .81, 5.78), ell(*tul_dims(6.255), 6.255), ell(.815, .645, 6.32), ell(.55, .45, 6.37, jitter=JIT), ell(.20, .16, 6.40)]
loft(hd, "HD_hat_crown", tul_rings, sh_vest, meta=meta("bucket hat crown: base W1.98 D1.62 at H5.78 -> top W1.76 D1.42 at H6.32 (bevel .065), peak H6.40, 16-gon, faceted cap"))


def brim_h(d):
    u = (d - D0) / 1.05
    return 5.64 + (.11 if u < 0 else .08) * u


sections = []
for k in range(N_H):
    th = 2 * math.pi * k / N_H
    ca, sa = math.cos(th), math.sin(th)
    ho = brim_h(D0 + 1.05 * sa)
    sections.append([V((.99 * ca * 1.0, D0 + .81 * sa, 5.835)), V((1.40 * ca, D0 + 1.05 * sa, ho + .055)),
                     V((1.40 * ca, D0 + 1.05 * sa, ho)), V((.99 * ca, D0 + .81 * sa, 5.78))])
loop_solid(hd, "HD_hat_brim", sections, lambda n, c: "VEST_LIGHT" if n.z > .4 else "VEST_DARK",
           meta_=meta("annular brim thickness .055: inner W1.98 D1.62, outer W2.80 D2.10; front edge H5.53, sides H5.64, rear H5.72"))
bd = []
for h, g in ((5.83, 0.0), (5.842, .025), (6.0, .025), (6.01, 0.0)):
    a, b = tul_dims(h)
    bd.append(ell(a + g, b + g, h))
loft(hd, "HD_hat_band", bd, sh_const("VEST_DARK"), meta=meta("hat band H5.83..6.01, thickness .025, follows the sloped crown"))
a_, b_ = tul_dims(5.92)
box_c(hd, "HD_hat_band_seam", (0, D0 + b_ + .03, 5.92), (.025, .02, .18), sh_const("VEST_SEAM"), meta_=meta("single small seam at the back, no bow", "prescribed"))

# red lure badge on the anatomical RIGHT fore-side of the crown (X<0), plate in the local tangent plane
a6, b6 = tul_dims(6.00)
ux, ud = -.85, -.85 + 0.02
s_ = 1.0 / math.sqrt((ux / (a6 + .025)) ** 2 + (ud / (b6 + .025)) ** 2)
LP = V((ux * s_, D0 + ud * s_, 6.00))
n_ = V((LP.x / (a6 + .025) ** 2, (LP.y - D0) / (b6 + .025) ** 2, 0)).normalized()
n_ = V((n_.x, n_.y, .20)).normalized()
t_ = V((-n_.y, n_.x, 0)).normalized()
u_ = n_.cross(t_).normalized()
if u_.z < 0:
    u_ = -u_
rot = Matrix.Rotation(math.radians(20), 3, n_)


def lure_ring(dn, rx, ry, k=10):
    return [LP + n_ * dn + rot @ (t_ * (rx * math.cos(2 * math.pi * i / k)) + u_ * (ry * math.sin(2 * math.pi * i / k))) for i in range(k)]


loft(hd, "HD_lure_body", [lure_ring(.0, .115, .15), lure_ring(.03, .115, .15), lure_ring(.035, .095, .125)], sh_const("FLOAT_RED"), meta=meta("red lure oval W.23 H.30 D.035 tilted 20 deg"))
loft(hd, "HD_lure_centre", [lure_ring(.034, .0375, .0375, 8), lure_ring(.042, .0375, .0375, 8)], sh_const("BUTTON"), meta=meta("yellow centre dia .075", "prescribed"))
loft(hd, "HD_lure_dot", [lure_ring(.041, .0125, .0125, 6), lure_ring(.046, .0125, .0125, 6)], sh_const("BELT"), meta=meta("dark dot .025", "prescribed"))
tail = [LP + n_ * .02 + u_ * .15, LP + n_ * .005 + u_ * .205, LP - n_ * .005 + u_ * .25]
sweep(hd, "HD_lure_tail", tail, .04, .02, sh_const("BUTTON"), up=n_, meta_=meta("short yellow tail .10 behind the top edge", "prescribed"))


# ----------------------------------------------------------------------------------------------
# FishingRod (sections 20..23) and Bucket (sections 24, 25): separate rigid props
# ----------------------------------------------------------------------------------------------
ROD_O = V((2.20, -.65, .10))
BUCKET_O = V((3.00, .10, 0.0))
rod = PM("FishingRod", ROD_O)
CORK_MARKS = [(0, .30, .035), (2.5, .62, .03), (4.1, 1.05, .04), (1.2, 1.40, .028), (5.4, 1.72, .045), (3.3, 1.95, .03), (0.7, 2.08, .025)]


def cork_tile(n, c):
    ang = math.atan2(n.y, n.x)
    sec = int(((ang + math.pi) / (2 * math.pi)) * 12) % 12
    return "CORK_LIGHT" if sec in (2, 6, 10) else "CORK"


lathe(rod, "ROD_plug", [(.095, .10), (.095, .16)], 2.20, -.65, 10, sh_const("ROD"), meta_=meta("bottom plug H.10..0.16 dia .19", "prescribed"))
lathe(rod, "ROD_cork", [(.09, .12), (.075, 2.20)], 2.20, -.65, 12, cork_tile, meta_=meta("cork grip H.12..2.20 dia .18 -> .15, 3 light facets", "observed+prescribed"))
for i, (ang, h, sz) in enumerate(CORK_MARKS):
    r_ = .09 + (.075 - .09) * (h - .12) / 2.08
    box_c(rod, "ROD_cork_mark_%d" % i, (2.20 + (r_ + .002) * math.cos(ang), -.65 + (r_ + .002) * math.sin(ang), h), (sz, sz, sz), sh_const("CORK_DARK"), meta_=meta("cork mark", "inferred"))
lathe(rod, "ROD_ferrule", [(.085, 2.16), (.085, 2.23)], 2.20, -.65, 10, sh_const("ROD"), meta_=meta("black upper collar H2.16..2.23 dia .17", "prescribed"))
shaft = [p for i, p in enumerate(ROD_DENSE) if p.z >= 2.20 - 1e-6 and (i % 2 == 0 or i == len(ROD_DENSE) - 1)]
sweep(rod, "ROD_shaft", shaft, [rod_diam(p.z) for p in shaft], [rod_diam(p.z) for p in shaft], sh_rod, up=V((0, -1, 0)), n=8,
      meta_=meta("rod shaft along the smoothed axis A1..A7, 8-sided, closed tip", "observed+prescribed"))
for hh in (4.20, 5.20, 6.35):
    pts = [rod_axis(hh - .035), rod_axis(hh), rod_axis(hh + .035)]
    sweep(rod, "ROD_wrap_%.2f" % hh, pts, rod_diam(hh) + .025, rod_diam(hh) + .025, sh_const("ROD_LIGHT"), up=V((0, -1, 0)), n=8,
          meta_=meta("black wrap W.07 at H%.2f, dia rod+.025" % hh, "prescribed"))

GUIDES = [(4.20, .10, .075), (5.20, .09, .065), (6.35, .08, .055), (7.23, .07, .045)]
GUIDE_C = []
for hh, off, ro in GUIDES:
    c = rod_axis(hh) + V((off, 0, 0))
    GUIDE_C.append(c)
    T = rod_tangent(hh)
    Bv = V((1, 0, 0)) - T * T.dot(V((1, 0, 0)))
    Bv.normalize()
    Nv = T.cross(Bv).normalized()
    secs = []
    for k in range(9):
        ph = 2 * math.pi * k / 9
        e = Bv * math.cos(ph) + Nv * math.sin(ph)
        secs.append([c + e * ro + T * .01, c + e * ro - T * .01, c + e * (ro - .018) - T * .01, c + e * (ro - .018) + T * .01])
    loop_solid(rod, "ROD_guide_%.2f" % hh, secs, sh_const("ROD"), meta("guide ring R%.3f rim .018, centre offset +X %.2f, axis parallel to the rod tangent" % (ro, off), "prescribed"))
    r_rod = (rod_diam(hh) + .025) / 2 if hh < 7 else rod_diam(hh) / 2
    x0 = rod_axis(hh).x + r_rod * .5
    x1 = c.x - ro + .02
    box_c(rod, "ROD_guide_foot_%.2f" % hh, ((x0 + x1) / 2, -.65, hh), (max(x1 - x0, .02), .035, .035), sh_const("ROD"), meta_=meta("guide foot .035 x .035", "prescribed"))

# reel (section 22)
RC = V((2.95, -.65, 2.84))
lathe(rod, "REEL_spool", [(.20, 2.75), (.20, 2.83), (.192, 2.84), (.20, 2.85), (.20, 2.95), (.192, 2.96), (.20, 2.97), (.20, 3.07)], 2.95, -.65, 12,
      lambda n, c: "GOLD_LIGHT" if n.z > .9 else "GOLD", meta_=meta("gold spool R.20 H.32 with two shallow grooves", "observed+prescribed"))
lathe(rod, "REEL_flange_top", [(.24, 3.0625), (.24, 3.1175)], 2.95, -.65, 12, lambda n, c: "REEL_LIGHT" if n.z > .9 else "REEL", meta_=meta("upper flange R.24 H.055 at H3.09", "prescribed"))
lathe(rod, "REEL_flange_bottom", [(.24, 2.7025), (.24, 2.7575)], 2.95, -.65, 12, sh_const("REEL"), meta_=meta("lower flange R.24 H.055 at H2.73", "prescribed"))
lathe(rod, "REEL_cap", [(.09, 3.12), (.09, 3.18)], 2.95, -.65, 10, sh_const("REEL_LIGHT"), meta_=meta("top cap R.09 H.06 at H3.15", "prescribed"))
box_c(rod, "REEL_body", (2.90, -.65, 2.58), (.36, .32, .31), lambda n, c: "REEL_LIGHT" if n.z > .5 else "REEL", ch=.06, meta_=meta("reel housing .36 x .32 x .31, bevel .06", "observed+prescribed"))
box_c(rod, "REEL_foot", (2.305, -.65, 2.735), (.10, .13, .37), sh_const("REEL"), ch=.02, meta_=meta("mounting foot .10 x .13 x .37 along the rod", "prescribed"))
sweep(rod, "REEL_arm", catmull([V((2.23, -.65, 2.78)), V((2.61, -.65, 2.46)), V((2.90, -.65, 2.58))], 4), .10, .10, sh_const("REEL"), up=V((0, -1, 0)),
      meta_=meta("curved support through (2.61,-.65,2.46), section .10 x .10", "prescribed"))
sweep(rod, "REEL_crank_a", [V((3.06, -.65, 2.57)), V((3.20, -.74, 2.51))], .055, .055, sh_const("REEL"), up=V((0, 0, 1)), meta_=meta("crank segment 1", "prescribed"))
sweep(rod, "REEL_crank_b", [V((3.20, -.74, 2.51)), V((3.16, -.84, 2.35))], .055, .055, sh_const("REEL"), up=V((1, 0, 0)), meta_=meta("crank segment 2", "prescribed"))
box_c(rod, "REEL_crank_knob", (3.16, -.84, 2.35), (.13, .16, .16), sh_const("REEL"), ch=.03, meta_=meta("crank knob .13 x .16 x .16", "prescribed"))
bail = [V((2.95, -.65 - .28 * math.sin(ph), 2.97 + .19 * math.cos(ph))) for ph in [math.pi * i / 8 for i in range(9)]]
sweep(rod, "REEL_bail", bail, .035, .035, sh_const("WIRE"), up=V((1, 0, 0)), n=6, meta_=meta("open line-roller wire arc, dia .035, R.28, H2.78..3.16", "prescribed"))
for sx in (-1, 1):
    box_c(rod, "REEL_bail_post_%d" % sx, (2.95 + sx * .06, -.65, 2.775), (.03, .03, .05), sh_const("REEL"), meta_=meta("bail support post", "prescribed"))

# float (section 23) + fishing line
FLOAT_XD = (3.03, -.65)
lathe(rod, "FLOAT_body", [(.0225, 5.38), (.09, 5.45), (.15, 5.62), (.15, 5.68), (.125, 5.81), (.06, 5.91), (.02, 5.96)], FLOAT_XD[0], FLOAT_XD[1], 12,
      sh_const("FLOAT_RED"), band_tiles={3: "FLOAT_WHITE"}, meta_=meta("float: 12-gon revolution, max dia .30, red/white/red", "observed+prescribed"))
lathe(rod, "FLOAT_stem", [(.0175, 5.22), (.0175, 5.38)], FLOAT_XD[0], FLOAT_XD[1], 6, sh_const("LINE"), meta_=meta("lower stem H5.22..5.38 dia .035", "prescribed"))
lathe(rod, "FLOAT_antenna", [(.0175, 5.96), (.0175, 6.08)], FLOAT_XD[0], FLOAT_XD[1], 6, sh_const("FLOAT_RED"), meta_=meta("upper antenna H5.96..6.08 dia .035", "prescribed"))
LINE_W = .012
LINE_UP = [V((2.95, -.65, 3.15)), V((2.95, -.65, 3.98)), GUIDE_C[0], GUIDE_C[1], GUIDE_C[2], GUIDE_C[3]]
LINE_DN = [GUIDE_C[3], V((FLOAT_XD[0], -.65, 6.08)), V((FLOAT_XD[0], -.65, 5.22)), V((FLOAT_XD[0], -.65, 3.30))]
for nm, pts in (("up", LINE_UP), ("down", LINE_DN)):
    for i in range(len(pts) - 1):
        sweep(rod, "LINE_%s_%d" % (nm, i), [pts[i], pts[i + 1]], LINE_W, LINE_W, sh_const("LINE"), up=V((1, 0, 0)), n=4, meta_=meta("fishing line segment dia .012", "prescribed"))

# ---------------------------------------------------------------- bucket
bk = PM("Bucket", BUCKET_O)
BK_PROFILE = [(.44, 0.0), (.46, .02), (.48, .08), (.56, 1.08), (.58, 1.10), (.58, 1.14), (.55, 1.16), (.49, 1.16), (.50, 1.08), (.40, .08)]


def bucket_tile(n, c):
    if n.z < -.5 or (n.z > .5 and abs(c.z - .08) < .002):
        return "BUCKET_DARK"
    if n.z > .5:
        return "BUCKET_LIGHT"
    if n.y < -.65:
        return "BUCKET_LIGHT"
    return "BUCKET"


lathe(bk, "BK_shell", BK_PROFILE, 3.00, .10, 12, bucket_tile,
      band_tiles={0: "BUCKET_DARK", 1: "BUCKET_DARK", 3: "BUCKET_LIGHT", 4: "BUCKET_LIGHT", 5: "BUCKET_LIGHT", 6: "BUCKET_LIGHT", 7: "BUCKET_DARK", 8: "BUCKET_DARK"},
      meta_=meta("hollow bucket, 12-gon, outer R.46->.56 (H.02..1.08), inner R.40..50, floor .08 thick, rolled rim H1.08..1.16 R.58", "observed+prescribed"))
for sx in (-1, 1):
    ex = 3.00 + sx * .55
    box_c(bk, "BK_ear_%d" % sx, (ex, .10, .98), (.09, .10, .14), sh_const("BUCKET_DARK"), ch=.015, meta_=meta("handle ear .09 x .10 x .14", "prescribed"))
    sweep(bk, "BK_axle_%d" % sx, [V((ex - .06, .10, .98)), V((ex + .06, .10, .98))], .045, .045, sh_const("SILVER"), up=V((0, 0, 1)), n=8, meta_=meta("axle dia .045", "prescribed"))
hp = [V((3.00 + .55 * math.cos(th), .10 - .58 * math.sin(th), .98 - .33 * math.sin(th))) for th in [math.pi * i / 14 for i in range(15)]]
sweep(bk, "BK_wire_handle", hp, .036, .036, sh_const("WIRE"), up=V((0, 0, 1)), n=6, meta_=meta("wire handle through the ears: X=3+.55cos, D=.10-.58 sin, H=.98-.33 sin", "prescribed"))


# ----------------------------------------------------------------------------------------------
# materials / UV / vertex colors / mesh objects
# ----------------------------------------------------------------------------------------------
atlas = bpy.data.images.new("FishermanDad_Palette", ATLAS_W, ATLAS_H, alpha=False)
atlas.colorspace_settings.name = 'sRGB'   # must be set BEFORE writing pixels
px = [0.0] * (ATLAS_W * ATLAS_H * 4)
fill = hex_rgb(_H["VEST"])
for ty in range(ATLAS_H):
    for tx in range(ATLAS_W):
        idx = (ty // TILE_PX) * COLS + (tx // TILE_PX)
        rgb = hex_rgb(PAL[idx][1]) if idx < len(PAL) else fill
        r, g, b = (c / 255.0 for c in rgb)
        o = ((ATLAS_H - 1 - ty) * ATLAS_W + tx) * 4
        px[o:o + 4] = [r, g, b, 1.0]
atlas.pixels.foreach_set(px)
atlas.filepath_raw = os.path.join(OUT, "FishermanDad_Palette.png")
atlas.file_format = 'PNG'
atlas.save()
atlas.pack()

MATP = bpy.data.materials.new("FishermanDad_Palette")
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

PROPS = ("FishingRod", "Bucket")
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
arm_data = bpy.data.armatures.new("FishermanDad_Armature")
ARM_OB = bpy.data.objects.new("FishermanDad_Armature", arm_data)
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
rod_ob, bucket_ob = PARTS["FishingRod"].obj, PARTS["Bucket"].obj
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
rod_lo, rod_hi = world_bounds([rod_ob])
bk_lo, bk_hi = world_bounds([bucket_ob])
body_tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in BODY)
rod_tris = sum(len(p.vertices) - 2 for p in rod_ob.data.polygons)
bk_tris = sum(len(p.vertices) - 2 for p in bucket_ob.data.polygons)
print("BOUNDS body", tuple(round(x, 3) for x in lo), tuple(round(x, 3) for x in hi))
print("ROD", tuple(round(x, 3) for x in rod_lo), tuple(round(x, 3) for x in rod_hi), "BUCKET", tuple(round(x, 3) for x in bk_lo), tuple(round(x, 3) for x in bk_hi))
print("HEAD", tuple(round(x, 3) for x in head_lo), tuple(round(x, 3) for x in head_hi), "FEET", round(ft_lo.z, 4))
print("TRIS body", body_tris, "rod", rod_tris, "bucket", bk_tris)

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


ROD_CHECK = pair_check("FishingRod", ["LeftHand", "LeftLowerArm", "LeftUpperArm", "UpperTorso", "Head", "LeftUpperLeg", "LeftFoot", "RightHand", "Bucket"])
BUCKET_CHECK = pair_check("Bucket", ["LeftFoot", "LeftLowerLeg", "LeftUpperLeg", "RightFoot", "LowerTorso", "FishingRod"])
HAND_CHECK = pair_check("LeftHand", ["LeftLowerArm", "UpperTorso", "Head", "LeftUpperArm"])
print("RODCHECK", json.dumps(ROD_CHECK))
print("BUCKETCHECK", json.dumps(BUCKET_CHECK))
print("HANDCHECK", json.dumps(HAND_CHECK))

# rod axis clearance in the grip channel: distance from the rod surface samples to the hand surface
th_, tp_ = bvh_of(PARTS["LeftHand"].obj)
rod_dist = []
for h in [3.10 + .05 * i for i in range(17)]:
    a = rod_axis(h)
    d = (th_.find_nearest(a)[3] or 9e9) if th_.find_nearest(a)[3] else 9e9
    rod_dist.append(round(d - rod_diam(h) / 2.0, 4))
print("GRIP clearance (axis->hand surface minus rod radius), H3.10..3.90:", rod_dist)

# ----------------------------------------------------------------------------------------------
# outputs: blend, FBX, spec JSON
# ----------------------------------------------------------------------------------------------
os.makedirs(os.path.join(OUT, "export"), exist_ok=True)
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
os.makedirs(os.path.join(OUT, "source"), exist_ok=True)
BLEND = os.path.join(OUT, "source", "FishermanDad_Redesign.blend")
FBX_BODY = os.path.join(OUT, "export", "FishermanDad_R15.fbx")
FBX_ROD = os.path.join(OUT, "export", "FishermanDad_Rod.fbx")
FBX_BUCKET = os.path.join(OUT, "export", "FishermanDad_Bucket.fbx")
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
for nm, path in (("FishingRod", FBX_ROD), ("Bucket", FBX_BUCKET)):
    src = PARTS[nm].obj
    cp = bpy.data.objects.new(nm + "_Geo", src.data.copy())
    cp.data.name = nm + "_Geo_export"
    EXP_COLL.objects.link(cp)
    cp.location = PARTS[nm].joint
    export_fbx(path, [cp])
    bpy.data.objects.remove(cp, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("EXPORTED", FBX_BODY, FBX_ROD, FBX_BUCKET, BLEND)

uvmap = {"atlas": "FishermanDad_Palette.png", "size": [ATLAS_W, ATLAS_H], "tile_px": TILE_PX, "columns": COLS, "inset_px": INSET,
         "row0_is_top_of_png": True, "unused_tiles_filled_with": "VEST", "tiles": []}
for i, (n_, h_, use) in enumerate(PAL):
    u0, v0, u1, v1 = tile_uv_patch(i)
    uvmap["tiles"].append({"index": i, "name": n_, "hex": h_, "use": use, "col": i % COLS, "row": i // COLS, "uv_patch": [u0, v0, u1, v1]})
json.dump(uvmap, open(os.path.join(OUT, "data", "palette_uv_map.json"), "w"), indent=1, ensure_ascii=False)


def r3(v):
    return [round(float(c), 4) for c in v]


def roblox_pos(p):
    return [round(-p[0], 4), round(p[2], 4), round(p[1], 4)]


RESULT = {"bounds_neutral": {"min": r3(lo), "max": r3(hi), "height": round(hi.z - lo.z, 4)}, "head_bounds": {"min": r3(head_lo), "max": r3(head_hi)},
          "rod_bounds": {"min": r3(rod_lo), "max": r3(rod_hi)}, "bucket_bounds": {"min": r3(bk_lo), "max": r3(bk_hi)},
          "feet_min_h": round(ft_lo.z, 5), "tris_body": body_tris, "tris_rod": rod_tris, "tris_bucket": bk_tris,
          "audit": AUDIT, "rod_vs_body": ROD_CHECK, "bucket_vs_body": BUCKET_CHECK, "hand_vs_body": HAND_CHECK, "grip_clearance_h3.10_3.90": rod_dist}
json.dump(RESULT, open(os.path.join(OUT, "data", "_build_result.json"), "w"), indent=1)
SPEC = {"asset": "FishermanDad_Redesign", "character": "Fisherman Dad (03, Uncommon)", "units": "studs", "neutral_height": 6.40, "built_height": RESULT["bounds_neutral"]["height"],
        "tables": {"UpperTorso": UT_ROWS, "LowerTorso": LT_ROWS, "Head": HEAD_ROWS, "Belt": BELT_ROWS},
        "joints_built": {k: list(v) for k, v in JOINTS.items()}, "joints_bind_neutral": {k: r3(v) for k, v in BIND.items()},
        "left_arm_ik": {"shoulder": r3(LEFT_S), "wrist_target": r3(LEFT_W), "pole": r3(LEFT_POLE), "elbow": [round(float(c), 8) for c in LEFT_E],
                        "upper_len": round(SEG_UP, 10), "lower_len": round(SEG_LO, 10),
                        "check_len_upper": round((LEFT_E - LEFT_S).length, 10), "check_len_lower": round((LEFT_W - LEFT_E).length, 10)},
        "grip_center": r3(GRIP_C), "rod_axis": [list(a) for a in ROD_A], "rod_origin": r3(ROD_O), "bucket_origin": r3(BUCKET_O),
        "palette": [{"index": i, "name": n_, "hex": h_, "use": u_} for i, (n_, h_, u_) in enumerate(PAL)],
        "counts": {"body_tris": body_tris, "rod_tris": rod_tris, "bucket_tris": bk_tris},
        "deviations_from_prompt": [
            "Left arm is built directly in the HoldRod pose (rest == pose); the neutral bind joints are stored in joints_bind_neutral.",
            "Forearm end is buried 0.16 inside the grip hand (the prescribed wrist lies only .10 inside the hand's inner face).",
            "Rod shaft uses 8-sided rings throughout (prompt: 8..12 low, 8 top).",
            "Guide-ring centre lies .025..0.025 from the rod surface for H4.2..6.35 (prescribed offsets): rims overlap the rod wraps; only the top ring has a visible foot.",
            "The lure centre (-.85,-.85,6.00) lies outside the crown ellipse; it was projected radially onto the crown surface.",
            "Fishing line runs spool top -> vertical to H3.98 -> guides (so it does not cross the fist) and has dia .012.",
            "Channel rings are horizontal (not normal) sections: radius .065/cos(tilt) in X, tilt <= 5 deg."],
        "measured": RESULT}
json.dump(SPEC, open(os.path.join(OUT, "data", "construction_spec.json"), "w"), indent=1, ensure_ascii=False)
json.dump({"asset": "FishermanDad_Redesign", "components": COMP_LOG,
           "part_totals": {k: {"components": len(v.comps), "tris": AUDIT[k]["tris"], "verts": AUDIT[k]["verts"]} for k, v in PARTS.items()},
           "mesh_names": {k: v.geo for k, v in PARTS.items()}}, open(os.path.join(OUT, "data", "component_registry.json"), "w"), indent=1, ensure_ascii=False)
RIG = {"asset": "FishermanDad_Redesign", "frame": {"logical": "(X,D,H) forward=-D, anatomical LEFT=+X (rod hand, bucket)", "roblox_position": "(-X, H, D)"},
       "bones": [{"name": n, "parent": p, "head_logical": r3(h), "tail_logical": r3(t), "head_roblox": roblox_pos(h)} for n, p, h, t in BONES],
       "props": {"FishingRod": {"mount": "RodGrip WeldConstraint LeftHand -> FishingRod", "origin_logical": r3(ROD_O), "grip_world": r3(GRIP_C)},
                 "Bucket": {"mount": "BucketMount WeldConstraint HumanoidRootPart -> Bucket", "origin_logical": r3(BUCKET_O)}},
       "weights": "100% own bone (rigid style); rest pose == HoldRod"}
json.dump(RIG, open(os.path.join(OUT, "data", "rig_manifest.json"), "w"), indent=1)
print("RESULT", json.dumps({k: RESULT[k] for k in ("bounds_neutral", "tris_body", "tris_rod", "tris_bucket")}))
if NORENDER:
    sys.exit(0)

# ----------------------------------------------------------------------------------------------
# renders (section 29)
# ----------------------------------------------------------------------------------------------
T = V((.55, -.2, 3.70))
shot("01_matching_34.png", (-7.0, -15.0, 7.0), V((.40, -.10, 3.50)), res=(384 * 2, 428 * 2), lens=70)
shot("01b_native_384x428.png", (-7.0, -15.0, 7.0), V((.40, -.10, 3.50)), res=(384, 428), lens=70)
shot("01c_matching_34_full.png", orbit(T, 21, -32, 12), T, res=(900, 1000))
shot("02_front.png", orbit(T, 21, 0, 4), T, res=(1000, 1000))
shot("03_back.png", orbit(T, 21, 180, 4), T, res=(1000, 1000))
shot("04_left_profile_rod_side.png", orbit(T, 21, 90, 4), T, res=(1000, 1000))
shot("05_right_profile.png", orbit(T, 21, -90, 4), T, res=(1000, 1000))
shot("06_back_right34.png", orbit(T, 21, -150, 12), T, res=(1000, 1000))
HT = V((0, -.2, 5.2))
shot("07_face_front.png", orbit(HT, 6.0, 0, 2), HT, res=(900, 900), hide=("FishingRod", "Bucket"))
shot("07b_face_34.png", orbit(HT, 6.0, -30, 8), HT, res=(900, 900), hide=("FishingRod", "Bucket"))
shot("07c_face_right_profile.png", orbit(HT, 6.0, -90, 2), HT, res=(900, 900), hide=("FishingRod", "Bucket"))
HH = V((0, -.1, 5.9))
shot("08_hat_top.png", orbit(HH, 6.5, 0, 75), HH, res=(900, 900), hide=("FishingRod", "Bucket"))
shot("08b_hat_back.png", orbit(HH, 6.5, 180, 12), HH, res=(900, 900), hide=("FishingRod", "Bucket"))
shot("08c_hat_side.png", orbit(HH, 6.5, -90, 6), HH, res=(900, 900), hide=("FishingRod", "Bucket"))
VT = V((0, -.2, 3.2))
shot("09_vest_front.png", orbit(VT, 8.0, 0, 4), VT, res=(900, 900), hide=("FishingRod", "Bucket"))
shot("09b_vest_back.png", orbit(VT, 8.0, 180, 4), VT, res=(900, 900), hide=("FishingRod", "Bucket"))
AT = V((1.9, -.2, 3.3))
shot("10_left_arm_side.png", orbit(AT, 6.0, 90, 4), AT, res=(900, 900), hide=("FishingRod", "Bucket"))
shot("10b_left_arm_top.png", orbit(AT, 6.0, 0, 80), AT, res=(900, 900), hide=("FishingRod", "Bucket"))
GT = V((2.24, -.65, 3.5))
shot("11_grip_front.png", orbit(GT, 3.0, 0, 4), GT, res=(900, 900))
shot("11b_grip_side.png", orbit(GT, 3.0, 90, 4), GT, res=(900, 900))
shot("11c_grip_back.png", orbit(GT, 3.0, 180, 4), GT, res=(900, 900))
shot("11d_grip_hand_only.png", orbit(GT, 3.0, 150, 8), GT, res=(900, 900), hide=("FishingRod",))
RT = V((2.55, -.65, 3.75))
shot("12_rod_full_front.png", orbit(RT, 18, 0, 2), RT, res=(700, 1100), lens=70, show_only=("FishingRod",))
shot("12b_rod_full_side.png", orbit(RT, 18, 90, 2), RT, res=(700, 1100), lens=70, show_only=("FishingRod",))
RL = V((2.95, -.65, 2.85))
shot("13_reel_front.png", orbit(RL, 2.8, 0, 6), RL, res=(900, 900), show_only=("FishingRod",))
shot("13b_reel_side.png", orbit(RL, 2.8, 90, 6), RL, res=(900, 900), show_only=("FishingRod",))
shot("13c_reel_back.png", orbit(RL, 2.8, 180, 6), RL, res=(900, 900), show_only=("FishingRod",))
FL = V((3.0, -.65, 5.7))
shot("14_float.png", orbit(FL, 2.6, 0, 4), FL, res=(800, 800), show_only=("FishingRod",))
BKT = V((3.0, .10, .6))
shot("15_bucket_front.png", orbit(BKT, 4.2, 0, 10), BKT, res=(900, 900), show_only=("Bucket",))
shot("15b_bucket_top.png", orbit(BKT, 4.2, 0, 80), BKT, res=(900, 900), show_only=("Bucket",))
shot("15c_bucket_bottom.png", orbit(BKT, 4.2, 0, -60), BKT, res=(900, 900), show_only=("Bucket",))
BT = V((.3, -.3, 1.1))
shot("16_boots_cargo.png", orbit(BT, 7.0, -35, 10), BT, res=(1000, 800), hide=("FishingRod", "Bucket"))
shot("17_gate_full_256.png", (-7.0, -15.0, 7.0), V((.40, -.10, 3.50)), res=(256, 256), lens=70)
print("ALL_RENDERS_DONE", len(RENDERED))
