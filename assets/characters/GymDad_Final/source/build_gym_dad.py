"""Procedural Blender build for Gym Dad (character 06, Rare) of "Steal a Dad!".

Source: GymDad_MasterPrompt_RU_UTF8.txt + GymDad_Construction_Spec.json (assigned plan, NOT measured geometry),
art reference visuals/GymDad_Original_Poster.jpg (bottom row, second from the left) and visuals/GymDad_Reference_Crop.png.

Frames / units
--------------
Logical (X, F, H): X<0 anatomical RIGHT (dumbbell hand), X>0 LEFT (bag hand), F>0 forward, H up, soles at H=0.
Blender (x, y, z) = (X, -F, H)  (the plan's own mapping).  FBX export axis_forward='Z', axis_up='Y' (project mapping used by
Regular/Office Dad) puts logical (X,F,H) at Roblox (-X, H, -F)... the character faces -Z with its anatomical right on +X.
1 Blender unit = 1 stud (scene scale_length 0.01).

Run headless:
    blender -b --factory-startup --python build_gym_dad.py -- <output_dir> [--quick] [--norender]
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

# palette: master prompt section 05 (order = tile index)
_SPEC_PATH = os.path.join(HERE, "inputs", "GymDad_Construction_Spec.json")
if not os.path.exists(_SPEC_PATH):
    _SPEC_PATH = os.path.join(os.path.dirname(HERE), "inputs", "GymDad_Construction_Spec.json")
PLAN = json.load(open(_SPEC_PATH, encoding="utf8"))
PAL = [(n, h.upper(), n) for n, h in PLAN["palette"].items()]
TILE = {n: i for i, (n, _, _) in enumerate(PAL)}
ATLAS_W, ATLAS_H, TILE_PX, COLS = 1024, 1024, 128, 8
INSET = 16

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
# containers, coordinate helpers, shading rules, prescribed tables
# ----------------------------------------------------------------------------------------------
PARTS = {}
COMP_LOG = []
SRC_COLL = bpy.data.collections.new("SOURCE_Components")
SCENE.collection.children.link(SRC_COLL)
EXP_COLL = bpy.data.collections.new("EXPORT_GymDad")
SCENE.collection.children.link(EXP_COLL)
HEXOF = {n: h for n, h, _ in PAL}


def Bl(x, f, h):
    """logical (X, F, H) -> Blender point (X, -F, H)."""
    return V((x, -f, h))


def sh_const(name):
    return lambda n, c: name


def sh_skin(n, c):
    if n.z > 0.55:
        return "SkinLight"
    if n.z < -0.55:
        return "SkinShadow"
    return "Skin"


def sh_skin_arm(n, c):
    if n.z > 0.55:
        return "SkinLight"
    if n.z < -0.55:
        return "SkinShadow"
    if n.y < -0.62:
        return "SkinLight"
    return "Skin"


def sh_tank(n, c):
    if n.z > 0.45:
        return "TankLight"
    if n.z < -0.45:
        return "TankShadow"
    return "Tank"


def sh_shorts(n, c):
    if n.z < -0.6:
        return "ShortsShadow"
    if n.y < -0.62 or n.z > 0.6:
        return "ShortsLight"
    if n.y > 0.62:
        return "ShortsShadow"
    return "Shorts"


def sh_beard(n, c):
    if n.z > 0.55:
        return "BeardLight"
    if n.z < -0.55:
        return "BeardShadow"
    return "Beard"


def sh_shoe(n, c):
    if n.z > 0.6:
        return "ShoeGray"
    return "ShoeBlack"


def sh_sole(n, c):
    if n.z < -0.5:
        return "SoleShadow"
    return "Sole"


def sh_plate(n, c):
    if abs(n.x) > 0.8:
        return "Dumbbell"
    return "DumbbellLight"


def sh_bag_dark(n, c):
    if n.z > 0.6:
        return "BagEdge"
    return "BagDark"


def sh_bag_orange(n, c):
    if n.z > 0.6:
        return "BagLight"
    return "BagOrange"


# ---------------------------------------------------------------------------------------------------------------------------
# V2 PARAMETERS. Every value in this block is a V2 decision made against the original crop (see data/v2_00_reference), not a value of the old plan.
# Baseline values: baseline/data_baseline. Logical frame: X<0 = anatomical RIGHT, F>0 = forward, H up; Blender (x, y, z) = (X, -F, H).
# ---------------------------------------------------------------------------------------------------------------------------
HS = 0.84                     # head scale (about the top of the skull, face axis F=.015)
L1, L2 = 1.40, 1.30           # shoulder->elbow, elbow->wrist: SAME for both arms (baseline 1.30 / 1.20)
RHINT = tuple(float(c) for c in os.environ.get("GYM_RHINT", "-0.3,-0.7,-0.2").split(","))    # IK bend hints (X, F, H): right elbow out and back, left elbow behind the arm (no side-opened sharp elbow)
LHINT = (0.4, -0.8, -0.2)
_GF = float(os.environ.get("GYM_GRIPF", "2.20"))
_GX = float(os.environ.get("GYM_GRIPX", "-2.05"))
GRIP_R = (_GX, _GF, 2.85)  # dumbbell centre = right grip frame
FIST_R = (_GX, _GF - .12, 2.80)  # right fist geometric centre (differs from wrist and from grip)
FIST_L = (2.25, 0.15, 2.25)   # left fist centre
BAG_X = 2.62                  # bag centre X (fist X + .34, as in the original)
JOINTS = {
    "Root": (0, 0, 2.6), "Waist": (0, 0, 2.85), "Neck": (0, 0, 5.02),
    "RightShoulder": (-2.20, 0, 4.95), "RightWrist": (_GX, _GF - .57, 2.90),
    "LeftShoulder": (2.03, 0, 4.86), "LeftWrist": (2.25, 0.15, 2.62),
    "RightHip": (-0.90, 0, 2.2), "LeftHip": (0.90, 0, 2.2), "RightKnee": (-0.98, 0.02, 1.35), "LeftKnee": (0.98, 0.02, 1.35),
    "RightAnkle": (-1.04, 0.02, 0.72), "LeftAnkle": (1.04, 0.02, 0.72),
}


def ik_elbow(S, W, L1, L2, hint):
    """two-link IK (plan section 13): E = S + a*u + h*n, n = bend hint projected across u."""
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
DUMBBELL_C = Bl(*GRIP_R)
BAGGRIP = Bl(FIST_L[0], FIST_L[1], 2.0)
BAG_C = Bl(BAG_X, 0.0, 0.95)
HZ = 0.95                     # head height factor (the original head is narrow but not short)
HEAD_PIVOT = V((0.0, -0.015, 6.40))


def head_xf(p):
    """V2 head scale: every head component (skull, ears, face, beard, neck) shrinks about the top of the skull"""
    p = V(p)
    d = p - HEAD_PIVOT
    return HEAD_PIVOT + V((d.x * HS, d.y * HS, d.z * HZ))


# torso section table: (H, W, Ffront, Fback signed, bevel); V2: taller torso with the shoulder line at H5.15 (the original has very short neck)
_TORSO = [(2.30, 2.70, .74, -.69, .10), (2.48, 2.92, .88, -.76, .12), (2.85, 3.08, .99, -.80, .14), (3.35, 3.16, 1.00, -.82, .15),
          (3.95, 3.14, .92, -.80, .16), (4.45, 3.06, .82, -.75, .16), (4.85, 2.96, .70, -.68, .14), (5.15, 2.74, .58, -.60, .12)]
TORSO = [(h, w, -ff, -fb, c) for h, w, ff, fb, c in _TORSO]          # D coordinates: front negative, back positive
TORSO_TOP = TORSO[-1][0]
LOWER_ROWS = [r for r in TORSO if r[0] <= 2.85 + 1e-9]
UPPER_ROWS = [r for r in TORSO if r[0] >= 2.85 - 1e-9]


def torso_row_at(h):
    return (h,) + tuple(interp_row(TORSO, h))


def cap_tris2(idxs, pts2d):
    """tessellate a planar polygon given in 2D (x, y) -> triangles of vertex ids."""
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
    """polygon in (X, H) swept between logical F=f0 (rear) and F=f1 (front); caps are tessellated in the 2D (X, H) plane (robust for concave outlines)"""
    n = len(poly_xh)
    P = [Bl(x, f0, h) for x, h in poly_xh] + [Bl(x, f1, h) for x, h in poly_xh]
    faces = [[k, (k + 1) % n, n + (k + 1) % n, n + k] for k in range(n)]
    faces += cap_tris2(list(range(n)), poly_xh) + cap_tris2(list(range(n, 2 * n)), poly_xh)
    pm.solid(cid, P, faces, tilefn, meta)


def patch_box(pm, cid, cx, fc, hc, w, d, hh, tile, embed=0.03, meta=None):
    """thin flat patch: centre (cx, fc, hc) sizes W (X), D (F), H; the rear is embedded `embed` into the surface."""
    solid_box(pm, cid, cx - w / 2, cx + w / 2, -(fc + d / 2), -(fc - d / 2) + embed, hc - hh / 2, hc + hh / 2, tile, meta)


def cyl_x(pm, cid, cx, cy, cz, length, r, segs, tilefn, ch=0.0, meta=None):
    """cylinder along X (Blender coords for the centre), optional end chamfer."""
    x0, x1 = cx - length / 2, cx + length / 2

    def ring(x, rr):
        return [V((x, cy + rr * math.cos(2 * math.pi * k / segs), cz + rr * math.sin(2 * math.pi * k / segs))) for k in range(segs)]
    if ch > 0:
        rings = [ring(x0, r - ch), ring(x0 + ch, r), ring(x1 - ch, r), ring(x1, r - ch)]
    else:
        rings = [ring(x0, r), ring(x1, r)]
    loft(pm, cid, rings, tilefn, meta=meta)


def rot_xf(pivot, deg):
    m = Matrix.Rotation(math.radians(deg), 3, 'Z')
    pv = V(pivot)
    return lambda p: pv + m @ (V(p) - pv)


def offset_poly2d(pts, d):
    """inward offset of a simple 2D polygon (list of (x, y)); mitre limited."""
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n)) / 2.0
    sgn = 1.0 if area > 0 else -1.0
    out = []
    for i in range(n):
        p0, p1, p2 = V((*pts[i - 1], 0)), V((*pts[i], 0)), V((*pts[(i + 1) % n], 0))
        e0, e1 = (p1 - p0).normalized(), (p2 - p1).normalized()
        n0, n1 = V((-e0.y, e0.x, 0)) * sgn, V((-e1.y, e1.x, 0)) * sgn
        bis = (n0 + n1)
        if bis.length < 1e-6:
            bis = n0
        bis.normalize()
        k = max(0.55, bis.dot(n0))
        q = p1 + bis * (d / k)
        out.append((q.x, q.y))
    return out


# ----------------------------------------------------------------------------------------------
# torso (tank top), pelvis, shorts, legs, shoes
# ----------------------------------------------------------------------------------------------
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


def tfront(x, h):
    return front_at(TORSO, min(max(h, 2.30), TORSO_TOP), x)


def tback(x, h):
    return back_at(TORSO, min(max(h, 2.30), TORSO_TOP), x)


def wall_ring(pm, cid, side, pts_fh, width, out, embed, tile, meta=None):
    """closed rectangular ribbon around the torso side wall (X = side * w(h)/2): path in (F, H)."""
    n = len(pts_fh)
    P = []
    for i, (f, h) in enumerate(pts_fh):
        pf, ph_ = pts_fh[i - 1]
        nf, nh = pts_fh[(i + 1) % n]
        t = V((nf - pf, nh - ph_, 0)).normalized()
        nrm = V((-t.y, t.x, 0))
        for sgn in (1, -1):
            ff, hh = f + sgn * nrm.x * width / 2, h + sgn * nrm.y * width / 2
            wx = interp_row(TORSO, min(max(hh, 2.30), TORSO_TOP))[0] / 2.0
            P.append(V((side * (wx + out), -ff, hh)))
            P.append(V((side * (wx - embed), -ff, hh)))
    faces = []
    for i in range(n):
        a, b = i * 4, ((i + 1) % n) * 4
        faces += [[a, a + 2, b + 2, b], [a + 1, b + 1, b + 3, a + 3], [a, b, b + 1, a + 1], [a + 2, a + 3, b + 3, b + 2]]
    pm.solid(cid, P, faces, tile, meta)


# ---- UpperTorso: tank shell with front neckline and shallow back scoop, armhole rims -----------------
ut = PM("UpperTorso", JV["Waist"])
bm = loft_bm([row_ring(r) for r in UPPER_ROWS], sh_tank)
NECK_FRONT = [(-.90, 5.45), (-.90, 4.58), (-.75, 4.38), (.75, 4.38), (.90, 4.58), (.90, 5.45)]
cut_f = plate_bm(NECK_FRONT, tfront, [(+.045, 1.0, 1.0), (-.30, 1.0, 1.0)], "Skin")
bm = bm_boolean(bm, cut_f)
cut_f.free()
NECK_BACK = [(-.85, 5.45), (-.85, 5.05), (-.62, 4.80), (-.40, 4.72), (.40, 4.72), (.62, 4.80), (.85, 5.05), (.85, 5.45)]
cut_b = plate_bm(NECK_BACK, tback, [(-.045, 1.0, 1.0), (+.30, 1.0, 1.0)], "Skin")
bm = bm_boolean(bm, cut_b)
cut_b.free()
tl_ = bm.faces.layers.int.get("tile")
for f_ in bm.faces:                      # V2: neckline walls are the thin tank-edge band; only the floors stay skin (chest / back)
    if PAL[f_[tl_]][0] == "Skin":
        f_.normal_update()
        if abs(f_.normal.y) < 0.7:
            f_[tl_] = TILE["TankEdge"]
ut.append_bm("UT_tank_shell", bm, None, {"recipe": "8-row octagon loft to H5.15 (shoulder line), boolean notches: front neckline (half width .90, depth .045, skin floor) and back scoop; straps are the shell between the neckline and the arm (width .47) and continue over the shoulder to the back", "class": "v2"})
bm.free()

# ---- LowerTorso: lower tank, hem, pelvis shorts ----------------------------------------------------
lt = PM("LowerTorso", JV["Root"])
loft(lt, "LT_tank_lower", [row_ring(r) for r in LOWER_ROWS], sh_tank, meta={"recipe": "section 06 rows H2.30..2.85", "class": "prescribed"})
hem = []
for h, g in ((2.31, 0.0), (2.335, .035), (2.40, .035), (2.44, 0.0)):
    r = torso_row_at(h)
    hem.append(ring8(r[1] / 2 + g, r[2] - g, r[3] + g, r[4] + g * .5, 0, 0, h))
loft(lt, "LT_waist_hem", hem, sh_const("TankEdge"), meta={"recipe": "hem ring .035 proud, H2.30..2.44", "class": "prescribed"})
PA, PD = 1.50, .73
prings = [ring8(PA - .08, -PD + .08, PD - .08, .06, 0, 0, 2.065), ring8(PA, -PD, PD, .08, 0, 0, 2.145), ring8(PA, -PD, PD, .08, 0, 0, 2.355), ring8(PA - .06, -PD + .06, PD - .06, .06, 0, 0, 2.435)]
loft(lt, "LT_pelvis_shorts", prings, sh_shorts, band_tiles={2: "ShortsShadow"},
     meta={"recipe": "pelvis block W2.62 x D1.42 x H.37 (plan 2.64 x 1.46), top band = waistband", "class": "prescribed"})

# ---- legs: shorts (UpperLeg), knee + shin (LowerLeg), sneakers (Foot) -----------------------------------
LEGHW = lambda h: .71 + .05 * (h - 1.24) / 1.10       # half width of the shorts leg (taper 1.18 -> 1.28)
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    hip, knee, ank = JV[side + "Hip"], JV[side + "Knee"], JV[side + "Ankle"]
    cxl = s * .90
    ul = PM(side + "UpperLeg", hip)
    LD0, LD1 = -.725, .695
    rings = [ring8(.71 - .05, LD0 + .05, LD1 - .05, .06, cxl, 0, 1.24), ring8(.71, LD0, LD1, .06, cxl, 0, 1.29),
             ring8(.76, LD0, LD1, .06, cxl, 0, 2.29), ring8(.76 - .05, LD0 + .05, LD1 - .05, .06, cxl, 0, 2.34)]
    loft(ul, "UL_shorts_" + side, rings, sh_shorts, band_tiles={0: "ShortsShadow"},
         meta={"recipe": "tapered beveled box W1.18->1.28 x D1.42 x H1.10, bevel .06", "class": "prescribed"})
    hs = [1.34 + .94 * k / 6 for k in range(7)]
    srings = []
    for h in hs:
        xo = s * (.90 + LEGHW(h))
        srings.append([V((xo + s * .014, -(.03 - .075), h)), V((xo + s * .014, -(.03 + .075), h)), V((xo - s * .02, -(.03 + .075), h)), V((xo - s * .02, -(.03 - .075), h))])
    loft(ul, "UL_side_stripe_" + side, srings, sh_const("SideStripe"), meta={"recipe": "stripe .15 wide on the outer face, H1.34..2.28, proud .014", "class": "prescribed"})
    ll = PM(side + "LowerLeg", knee)
    secs = [(1.42, .98, .98, .09, -.98), (1.20, .95, .96, .09, -1.00), (1.00, .90, .92, .08, -1.03), (.66, .84, .86, .07, -1.04), (.62, .84, .86, .07, -1.10)]
    # logical X of the leg centre is s * (-x); D centre of the leg is -F = -.02
    rings = [ring8(w / 2, -.02 - d / 2, -.02 + d / 2, c, s * -x, 0, h) for h, w, d, c, x in secs]
    loft(ll, "LL_knee_shin_" + side, rings, sh_skin, meta={"recipe": "knee skin W.91 (H1.12..1.42) + shin tapering to .73 x .77, hidden .03 in the shoe", "class": "prescribed"})

    # V2_03 foot: tall sneaker authored unrotated, then ONE rotation of the whole foot set about the ankle (7 deg outward)
    th = s * 7.0
    ft = PM(side + "Foot", ank, xf=rot_xf(ank, th))
    cx = s * 1.04
    sole = [ring8(.60, -1.16, .64, .10, cx, 0, 0.0), ring8(.70, -1.26, .74, .10, cx, 0, .10), ring8(.70, -1.26, .74, .10, cx, 0, .26), ring8(.62, -1.18, .66, .10, cx, 0, .34)]
    loft(ft, "FT_sole_" + side, sole, sh_sole, band_tiles={0: "SoleShadow"}, meta={"recipe": "sole W1.40 x D2.00 x H.34, bevel .10, outsole band", "class": "v2"})

    def ring_xh(f, w, h0, h1, c, cx=cx):
        a = w / 2
        pts = [(-a + c, h0), (a - c, h0), (a, h0 + c), (a, h1 - c), (a - c, h1), (-a + c, h1), (-a, h1 - c), (-a, h0 + c)]
        return [V((cx + x, -f, h)) for x, h in pts]

    def top_at(f):
        for (f0, t0, _, _), (f1, t1, _, _) in zip(UP, UP[1:]):
            if f0 <= f <= f1:
                return t0 + (t1 - t0) * (f - f0) / (f1 - f0)
        return UP[-1][1]
    UP = [(-.66, .62, .96, .14), (-.52, .78, 1.20, .16), (-.15, .86, 1.30, .16), (.28, .84, 1.32, .16), (.58, .72, 1.32, .15), (.80, .62, 1.28, .13)]
    loft(ft, "FT_upper_" + side, [ring_xh(f, w, .30, top, c) for f, top, w, c in UP], sh_shoe, meta={"recipe": "upper lofted along F: high ankle collar (H1.04) falling to the toe, W1.30", "class": "v2"})
    CAP = [(.80, .52, 1.30, .14), (1.02, .54, 1.26, .16), (1.16, .46, 1.10, .14), (1.23, .38, .90, .12), (1.25, .34, .74, .02)]
    loft(ft, "FT_toe_cap_" + side, [ring_xh(f, w, .30, top, c) for f, top, w, c in CAP], sh_const("Sole"), meta={"recipe": "ONE rounded white toe cap wrapping the toe from the sole upwards", "class": "v2"})
    patch_box(ft, "FT_toe_notch_" + side, cx, 1.262, .17, .55, .012, .12, "ShoeBlack", meta={"recipe": "dark centre on the sole front face", "class": "v2"})

    def tongue_top(f):
        return .96 + (.78 - .96) * (f - .26) / (.60 - .26)
    prism_poly(ft, "FT_tongue_" + side, [Bl(cx - .30, f, h) for f, h in ((.26, .96), (.60, .78), (.60, .66), (.26, .84))], V((.60, 0, 0)), sh_const("ShoeGray"), {"recipe": "tongue wedge on the instep in front of the shin", "class": "v2"})
    for k, f in enumerate((.37, .50)):
        f0, f1 = f - .035, f + .035
        prism_poly(ft, "FT_lace_%d_%s" % (k + 1, side), [Bl(cx - .31, ff, hh) for ff, hh in ((f0, tongue_top(f0) - .02), (f1, tongue_top(f1) - .02), (f1, tongue_top(f1) + .035), (f0, tongue_top(f0) + .035))],
                   V((.62, 0, 0)), sh_const("Sole"), {"recipe": "flat lace band on the tongue", "class": "v2"})
    LOOPP = [(-.09, 0), (-.045, 0), (-.045, .07), (.045, .07), (.045, 0), (.09, 0), (.09, .14), (-.09, .14)]
    prism_xh(ft, "FT_orange_loop_" + side, [(cx + x, .91 + h) for x, h in LOOPP], .26, .31, sh_const("ShoeOrange"), {"recipe": "orange loop at the TOP of the tongue, in front of the shin", "class": "v2"})
    trim = []
    for f in (-.35, 0.0, .30, .55):
        xi, xo = cx + s * .62, cx + s * .682
        trim.append([V((xi, -f, .50)), V((xo, -f, .50)), V((xo, -f, .64)), V((xi, -f, .64))])
    loft(ft, "FT_orange_side_trim_" + side, trim, sh_const("ShoeOrange"), meta={"recipe": "orange side accent on the outer side of the upper", "class": "v2"})


# ----------------------------------------------------------------------------------------------
# arms: two-segment IK limbs with a shared mitre contour at the elbow (no gap on the outer side of the bend)
# ----------------------------------------------------------------------------------------------
class AxisG:
    """Limb frame (section 14): L from the proximal to the distal joint, U = world X projected across L (width), W = L x U."""

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
        return [(-a + c, -b), (a - c, -b), (a, -b + c), (a, b - c), (a - c, b), (-a + c, b), (-a, b - c), (-a, -b + c)]

    def ring(self, t, w, d, c):
        P = self.at(t)
        return [P + self.U * x + self.W * y for x, y in self.corners(w, d, c)]


# V2 sections (W, D): massive shoulder mass -> elbow transition -> wide forearm; same for both arms (the pose alone makes the projections differ)
UPPER_SEC = [(0.0, 1.55, 1.45), (.30, 1.58, 1.46), (.70, 1.38, 1.30), (1.0, 1.20, 1.15)]
_FW, _FD = (float(c) for c in os.environ.get("GYM_FAEND", ".84,.74").split(","))
LOWER_SEC = [(0.0, 1.20, 1.15), (.40, 1.15, 1.10), (.75, (1.02 + _FW) / 2, (.98 + _FD) / 2), (1.0, _FW, _FD)]
ARM_C = .17
OVERLAP = .04
ARM_AX = {}
ELBOW_RING = {}
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    S, E, W_ = JV[side + "Shoulder"], JV[side + "Elbow"], JV[side + "Wrist"]
    ax1, ax2 = AxisG(S, E), AxisG(E, W_)
    ARM_AX[side] = (ax1, ax2)
    N = (ax1.A + ax2.A).normalized()
    # shared mitre contour K: the end section of the upper arm cut by the bisector plane through the elbow
    K = []
    for x, y in ax1.corners(UPPER_SEC[-1][1], UPPER_SEC[-1][2], ARM_C):
        p = E + ax1.U * x + ax1.W * y
        K.append(p - ax1.A * (((p - E).dot(N)) / ax1.A.dot(N)))
    ELBOW_RING[side] = K
    ua = PM(side + "UpperArm", S)
    t0 = -OVERLAP / ax1.L
    rings = [ax1.ring(t0, UPPER_SEC[0][1], UPPER_SEC[0][2], ARM_C)] + [ax1.ring(t, w, d, ARM_C) for t, w, d in UPPER_SEC[1:-1]] + [K]
    loft(ua, "UA_arm_" + side, rings, sh_skin_arm, meta={"recipe": "upper arm W/D 1.08/1.03 -> .91/.88, rectangular section chamfer .11, ends overlap .04, elbow end = mitre contour", "class": "prescribed"})
    la = PM(side + "LowerArm", E)
    ts = [.14, .40, .75, 1.0 + OVERLAP / ax2.L]
    secw = lambda t: sec_at(LOWER_SEC, min(t, 1.0))
    lr = [ax2.ring(t, *secw(t), ARM_C) for t in ts]
    best = min(range(8), key=lambda sh: sum((K[k] - lr[0][(k + sh) % 8]).length for k in range(8)))
    lr = [[r[(k + best) % 8] for k in range(8)] for r in lr]
    loft(la, "LA_forearm_" + side, [K] + lr, sh_skin_arm, meta={"recipe": "forearm W/D .91/.88 -> .70/.68, first ring = shared elbow contour (ring order shift %d), end overlap .04" % best, "class": "prescribed"})

# ----------------------------------------------------------------------------------------------
# hands: heavy solid fists, separate wrist / geometric centre / grip frames
# ----------------------------------------------------------------------------------------------
FR, FL = FIST_R, FIST_L
rh = PM("RightHand", JV["RightWrist"])
loft(rh, "HAND_palm_Right", cbox(Bl(*FR), (.78, .98, .98), .13), sh_skin_arm, meta={"recipe": "right fist centre %s size .78/.98/.98 bevel .13 (closed; the grip passes through hidden)" % (FR,), "class": "v2"})
loft(rh, "HAND_thumb_Right", cbox(Bl(FR[0] + .42, FR[1] - .02, FR[2] + .26), (.30, .50, .38), .08), sh_const("SkinLight"), meta={"recipe": "integrated thumb block on the inner side, overlaps the fist", "class": "v2"})
for k, h in enumerate((FR[2] - .10, FR[2] + .10)):
    patch_box(rh, "HAND_fingerline_Right_%d" % (k + 1), FR[0], FR[1] + .48 + .003, h, .56, .012, .014, "SkinShadow", meta={"recipe": "flat finger crease", "class": "v2"})
lh = PM("LeftHand", JV["LeftWrist"])
loft(lh, "HAND_palm_Left", cbox(Bl(*FL), (.76, .96, .96), .14), sh_skin_arm, meta={"recipe": "left fist centre %s size .76/.96/.96 bevel .14, bag loops held below centre" % (FL,), "class": "v2"})
loft(lh, "HAND_thumb_Left", cbox(Bl(FL[0] - .47, FL[1] + .06, FL[2] + .08), (.26, .46, .40), .08), sh_const("SkinLight"), meta={"recipe": "integrated thumb block on the inner side", "class": "v2"})
for k, h in enumerate((FL[2] - .10, FL[2] + .10)):
    patch_box(lh, "HAND_fingerline_Left_%d" % (k + 1), FL[0], FL[1] + .48 + .003, h, .56, .012, .014, "SkinShadow", meta={"recipe": "flat finger crease", "class": "v2"})


# ----------------------------------------------------------------------------------------------
# V2 head: bald skull, short neck, ears, oval eyes, protruding nose, curved smile, jaw-wrapping beard (all scaled by HS about the top of the skull)
# ----------------------------------------------------------------------------------------------
def sh_nose(n, c):
    if n.z < -0.55:
        return "SkinShadow"
    if n.z > 0.45:
        return "NoseLight"
    return "Nose"


def prism_bm(poly_xh, f0, f1, tile):
    """closed prism of a polygon in (X, H) swept between logical F=f0 and F=f1 (boolean cutter)"""
    n = len(poly_xh)
    P = [Bl(x, f0, h) for x, h in poly_xh] + [Bl(x, f1, h) for x, h in poly_xh]
    faces = [[k, (k + 1) % n, n + (k + 1) % n, n + k] for k in range(n)]
    faces += cap_tris2(list(range(n)), poly_xh) + cap_tris2(list(range(n, 2 * n)), poly_xh)
    return solid_tiled(P, faces, tile)


def ellipse(cx, cz, rx, rz, n=14, rot=0.0):
    c, s = math.cos(rot), math.sin(rot)
    return [(cx + rx * math.cos(2 * math.pi * k / n) * c - rz * math.sin(2 * math.pi * k / n) * s, cz + rx * math.cos(2 * math.pi * k / n) * s + rz * math.sin(2 * math.pi * k / n) * c) for k in range(n)]


hd = PM("Head", JV["Neck"], xf=head_xf)
SKULL = [(4.97, 1.66, .60, -.57, .12), (5.13, 2.00, .76, -.73, .16), (6.23, 2.00, .76, -.73, .16), (6.34, 1.80, .66, -.63, .12), (6.40, 1.34, .46, -.44, .10)]
loft(hd, "HD_skull", [ring8(w / 2, -ff, -fb, c, 0, 0, h) for h, w, ff, fb, c in SKULL], sh_skin,
     meta={"recipe": "skull W2.00 x D1.49 bevel .16 with low dome to H6.40 (scaled by HS)", "class": "v2"})
loft(hd, "HD_neck", cbox(Bl(0, 0, 4.90), (.86, .70, .50), .10), sh_skin, meta={"recipe": "short wide neck block, mostly inside skull/torso/beard (no separate visible neck block in profile)", "class": "v2"})
for s, nm in ((-1, "Right"), (1, "Left")):
    loft(hd, "HD_ear_" + nm, cbox(Bl(s * 1.015, -.015, 5.62), (.30, .42, .50), .08), sh_skin, meta={"recipe": "ear .30 x .42 x .50", "class": "v2"})
    x_out = s * 1.165
    solid_box(hd, "HD_concha_" + nm, min(x_out + s * .02, x_out - s * .035), max(x_out + s * .02, x_out - s * .035), -(.05 + .10), -(.05 - .10), 5.50, 5.74, sh_const("EarInner"),
              {"recipe": "ear concha patch, proud .02", "class": "v2"})
    # eyes: oval whites, round iris/pupil, glint; the brow covers the upper edge
    ex = s * .40
    prism_xh(hd, "HD_eyewhite_" + nm, ellipse(ex, 5.80, .205, .108, 16, rot=s * -0.10), .72, .785, sh_const("EyeWhite"), {"recipe": "oval eye white .41 x .22, tilted (narrowed)", "class": "v2"})
    prism_xh(hd, "HD_iris_" + nm, ellipse(s * .362, 5.792, .078, .086, 14), .72, .800, sh_const("Iris"), {"recipe": "round iris d.16", "class": "v2"})
    prism_xh(hd, "HD_pupil_" + nm, ellipse(s * .360, 5.792, .046, .052, 12), .72, .813, sh_const("Pupil"), {"recipe": "pupil d.13", "class": "v2"})
    prism_xh(hd, "HD_glint_" + nm, ellipse(s * .378, 5.822, .020, .022, 8), .72, .822, sh_const("EyeGlint"), {"recipe": "one glint per eye", "class": "v2"})
    xi, xo, t = s * .10, s * .72, .15
    prism_xh(hd, "HD_brow_" + nm, [(xi, 5.915 - t / 2), (xo, 6.05 - t / 2), (xo, 6.05 + t / 2), (xi, 5.915 + t / 2)], .70, .865, sh_const("Brow"),
             {"recipe": "brow wedge, thickness .13, inner end H5.985 (covers the eye top), outer H6.10", "class": "v2"})
    # moustache half: follows the smile, tapered towards the mouth corner
    mp = [(-s * .02, 5.50), (-s * .02, 5.72), (s * .30, 5.68), (s * .58, 5.58), (s * .66, 5.46), (s * .56, 5.43), (s * .28, 5.48)]
    prism_xh(hd, "HD_moustache_" + nm, mp, .70, 1.03, sh_beard, {"recipe": "moustache half under the nose, front F1.03 (nose front 1.20)", "class": "v2"})

NOSE = [(5.45, .30, .98, .70, .08), (5.58, .44, 1.14, .70, .10), (5.78, .42, 1.04, .70, .10), (5.98, .26, .84, .70, .07)]
loft(hd, "HD_nose", [ring8(w / 2, -ff, -fb, c, 0, 0, h) for h, w, ff, fb, c in NOSE], sh_nose, meta={"recipe": "short wide nose, front F1.14, 0.38 in front of the face plane, above the moustache", "class": "v2"})

# smile: dark compact crescent + ONE curved teeth band, corners lifted; no lip plate, no support block (the beard window leaves the skin floor)
xs = [-.60 + 1.20 * k / 10 for k in range(11)]
cav = [(x, 5.19 + .16 * (x / .60) ** 2) for x in xs] + [(x, 5.47 + .17 * (x / .60) ** 2) for x in xs[::-1]]
prism_xh(hd, "HD_mouth_cavity", cav, .70, .785, sh_const("Mouth"), {"recipe": "compact dark crescent under the teeth", "class": "v2"})
xt = [-.54 + 1.08 * k / 10 for k in range(11)]
teeth = [(x, 5.28 + .16 * (x / .54) ** 2) for x in xt] + [(x, 5.44 + .17 * (x / .54) ** 2) for x in xt[::-1]]
prism_xh(hd, "HD_teeth", teeth, .70, .805, sh_const("Teeth"), {"recipe": "one continuous curved teeth band, corners up", "class": "v2"})

# beard: dense closed volume built from several jaw sections (not a front contour pushed forward), then the face window is cut out (cheeks, nose, mouth)
BEARD_ROWS = [(4.76, .50, .78, .05, .18), (4.84, .80, 1.05, .00, .22), (5.02, .97, 1.12, -.15, .22), (5.30, 1.06, 1.07, -.28, .20), (5.55, 1.07, 1.00, -.30, .18), (5.80, 1.02, .92, -.28, .15)]
bm = loft_bm([ring8(a, -ff, -fb, c, 0, 0, h) for h, a, ff, fb, c in BEARD_ROWS], sh_beard)
WINDOW = [(-.88, 6.30), (-.88, 5.92), (-.62, 5.52), (-.60, 5.22), (0, 5.12), (.60, 5.22), (.62, 5.52), (.88, 5.92), (.88, 6.30)]
win = prism_bm(WINDOW, .745, 1.60, "Beard")
bm = bm_boolean(bm, win)
win.free()
hd.append_bm("HD_beard", bm, None, {"recipe": "6 jaw sections (chin F1.12, cheeks wrap to sideburns), face window cut at the beard top line; walls remain beard colour", "class": "v2"})
bm.free()


# ----------------------------------------------------------------------------------------------
# V2 props: heavy dumbbell (right hand) and a compact soft sports bag (left hand) - separate rigid meshes
# ----------------------------------------------------------------------------------------------
db = PM("Dumbbell", DUMBBELL_C, geo="Dumbbell_Geo")
DX, DY, DZ = DUMBBELL_C.x, DUMBBELL_C.y, DUMBBELL_C.z
GRIP_HALF = float(os.environ.get("GYM_GRIPHALF", ".58"))
cyl_x(db, "DB_grip", DX, DY, DZ, 2 * GRIP_HALF + .04, .115, 12, sh_const("Grip"), meta={"recipe": "grip L1.08 d.23, 12 sides, axis X (visible .13 beyond the fist)", "class": "v2"})
cyl_x(db, "DB_axle", DX, DY, DZ, 3.10, .07, 12, sh_const("DumbbellDark"), meta={"recipe": "hidden axle through both packs", "class": "v2"})


def sh_plate_face(n, c):
    if abs(n.x) > .8:
        return "Dumbbell"
    if abs(n.x) < .2:
        return "Dumbbell"
    return "DumbbellLight"


# V2 plate packs: contiguous (no gaps), thicker (pack thickness / diameter = .53), stepped radii .98 / .88 / .72
PLATES = [(.34, .98), (.28, .88), (.24, .72)]
for sx, nm in ((-1, "Outer"), (1, "Inner")):
    cyl_x(db, "DB_%s_collar" % nm, DX + sx * (GRIP_HALF + .03), DY, DZ, .06, .22, 12, sh_const("DumbbellDark"), meta={"recipe": "inner stop", "class": "v2"})
    off = GRIP_HALF + .06
    for i, (t, r) in enumerate(PLATES):
        cyl_x(db, "DB_%s_plate_%d" % (nm, i + 1), DX + sx * (off + t / 2), DY, DZ, t, r, 20, sh_plate_face, ch=.05,
              meta={"recipe": "plate r%.2f t%.2f, 20 sides, bevel .05, touching the neighbours" % (r, t), "class": "v2"})
        off += t
    cyl_x(db, "DB_%s_cap" % nm, DX + sx * (off + .03), DY, DZ, .06, .28, 12, sh_const("DumbbellDark"), meta={"recipe": "end cap", "class": "v2"})
    cyl_x(db, "DB_%s_boss" % nm, DX + sx * (off + .075), DY, DZ, .03, .10, 12, sh_const("DumbbellLight"), meta={"recipe": "central boss", "class": "v2"})

bg = PM("GymBag", BAG_C, geo="GymBag_Geo")
BX = BAG_X


def sh_bag(n, c):
    if n.z < -0.5:
        return "BagDark"
    if abs(c.x - BX) > .48 and c.z < 1.30:
        return "BagLight" if n.z > .6 else "BagOrange"
    return "BagEdge" if n.z > .6 else "BagDark"


# soft duffel: wide base, rounded sides, rounded top; orange ends, dark middle (as on the original)
BAGROWS = [(.28, .66, .42, .14), (.46, .80, .51, .18), (.95, .82, .52, .20), (1.20, .74, .48, .20), (1.34, .56, .36, .14)]
loft(bg, "BG_body", [ring8(a, -d, d, c, BX, 0, h) for h, a, d, c in BAGROWS], sh_bag, meta={"recipe": "soft body: 5 rounded sections (H.28..1.34, W1.52 max, D1.02 max); ends orange, middle dark", "class": "v2"})
solid_box(bg, "BG_zipper_track", BX - .30, BX + .30, -.02, .02, 1.32, 1.365, sh_const("Zipper"), {"recipe": "zipper track on the top", "class": "v2"})
solid_box(bg, "BG_zipper_pull", BX + .26, BX + .38, -.03, .03, 1.34, 1.395, sh_const("Steel"), {"recipe": "zipper pull", "class": "v2"})
HPATH = catmull([V((2.26, 0, 1.33)), V((2.30, 0, 1.68)), V((2.45, 0, 2.05)), V((2.65, 0, 2.05)), V((2.86, 0, 1.33))], 4)


def smooth01(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


for sf, nm in ((1, "front"), (-1, "back")):
    for ax in (2.26, 2.86):
        patch_box(bg, "BG_anchor_%s_%.2f" % (nm, ax), ax, sf * .25, 1.32, .17, .10, .14, "BagEdge", embed=.05, meta={"recipe": "handle anchor", "class": "v2"})
    rings = []
    for k, p in enumerate(HPATH):
        tg = (HPATH[min(k + 1, len(HPATH) - 1)] - HPATH[max(k - 1, 0)])
        tg = V((tg.x, 0, tg.z)).normalized()
        nx, nz = -tg.z, tg.x
        fabs = .25 - .13 * smooth01((p.z - 1.45) / .55)
        f = sf * fabs
        xl, zl = p.x + nx * .0475, p.z + nz * .0475
        xr, zr = p.x - nx * .0475, p.z - nz * .0475
        rings.append([Bl(xl, f - .0375, zl), Bl(xr, f - .0375, zr), Bl(xr, f + .0375, zr), Bl(xl, f + .0375, zl)])
    loft(bg, "BG_handle_" + nm, rings, sh_const("BagDark"), meta={"recipe": "handle ribbon .095 x .075; F converges from +-.25 to +-.12 inside the left fist", "class": "v2"})


# ----------------------------------------------------------------------------------------------
# atlas / material / mesh objects
# ----------------------------------------------------------------------------------------------
os.makedirs(os.path.join(OUT, "textures"), exist_ok=True)
atlas = bpy.data.images.new("GymDad_Atlas", ATLAS_W, ATLAS_H, alpha=False)
atlas.colorspace_settings.name = 'sRGB'
px = [0.0] * (ATLAS_W * ATLAS_H * 4)
fill = hex_rgb(HEXOF["Tank"])
for ty in range(ATLAS_H):
    for tx in range(ATLAS_W):
        idx = (ty // TILE_PX) * COLS + (tx // TILE_PX)
        rgb = hex_rgb(PAL[idx][1]) if idx < len(PAL) else fill
        r, g, b = (c / 255.0 for c in rgb)
        o = ((ATLAS_H - 1 - ty) * ATLAS_W + tx) * 4
        px[o:o + 4] = [r, g, b, 1.0]
atlas.pixels.foreach_set(px)
ATLAS_PATH = os.path.join(OUT, "textures", "GymDad_Atlas.png")
atlas.filepath_raw = ATLAS_PATH
atlas.file_format = 'PNG'
atlas.save()
atlas.pack()

MATP = bpy.data.materials.new("GymDad_Atlas")
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
arm_data = bpy.data.armatures.new("GymDad_Armature")
ARM_OB = bpy.data.objects.new("GymDad_Armature", arm_data)
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
PROPS = ("Dumbbell", "GymBag")
for pm in PARTS.values():
    bone = {"Dumbbell": "RightHand", "GymBag": "LeftHand"}.get(pm.runtime, pm.runtime)
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
ALLOWED = {"Dumbbell": {"RightHand": "grip passes through the closed palm (hidden, allowed)"},
           "GymBag": {"LeftHand": "handle tops run inside the fist (hidden, allowed)"}}
CLEAR = {}
for prop, others in (("Dumbbell", ("UpperTorso", "RightLowerArm", "RightUpperArm", "RightHand", "LowerTorso", "RightUpperLeg", "LeftHand")),
                     ("GymBag", ("LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "LeftHand", "LeftLowerArm", "LowerTorso", "RightFoot", "LeftUpperArm"))):
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
BLEND = os.path.join(OUT, "source", "GymDad_Review_V2.blend")
FBX_BODY = os.path.join(OUT, "export", "GymDad_V2_Body.fbx")
FBX_PROPS = os.path.join(OUT, "export", "GymDad_V2_Props.fbx")
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

uvmap = {"atlas": "GymDad_Atlas.png", "size": [ATLAS_W, ATLAS_H], "tile_px": TILE_PX, "columns": COLS, "inset_px": INSET, "row0_is_top_of_png": True, "tiles": []}
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
def _r(v):
    return [round(float(c), 3) for c in v]


DEVIATIONS = [
    {"id": "V01", "what": "coordinate basis", "plan": "Roblox (x,y,z) = (X, H, -F), X positive = anatomical left", "v2": "Blender (x,y,z) = (X,-F,H) with X<0 = anatomical RIGHT; FBX axis_forward Z / axis_up Y gives Roblox (-X, H, -F): character faces -Z, anatomical right = +X (contract of Regular/Office Dad)",
     "reason": "the plan's literal Roblox formula would put the dumbbell hand on the character's left; verified on 3 basis vectors and both fists in data/basis_check.json"},
    {"id": "V02", "what": "arm lengths and shoulder girdle", "plan": "shoulder (+-1.62, 0, 4.62), L1/L2 = 1.30/1.20", "v2": "shoulders R %s / L %s, L1/L2 = %.2f/%.2f for BOTH arms; elbows by the plan's IK formula: R %s (hint %s), L %s (hint %s)" % (_r(JOINTS["RightShoulder"]), _r(JOINTS["LeftShoulder"]), L1, L2, _r(JOINTS["RightElbow"]), RHINT, _r(JOINTS["LeftElbow"]), LHINT),
     "reason": "the original has wide, low shoulder masses and the left arm hangs along the body; the old shoulder line (4.62) and lengths could not give that silhouette"},
    {"id": "V03", "what": "head", "plan": "skull W2.00 D1.49 H1.42, top 6.40", "v2": "all head components scaled about the top of the skull: width/depth x%.2f, height x%.2f (skull W1.68, beard bottom H%.2f)" % (HS, HZ, 6.40 - (6.40 - 4.76) * HZ), "reason": "head/shoulder-girdle ratio .553 (baseline) vs .343 (original)"},
    {"id": "V04", "what": "torso", "plan": "rows H2.30..4.78, top W2.74", "v2": "8 rows H2.30..5.15 (top W2.74, mid-chest W3.14, belly Ffront 1.00), neckline half width .90 (plan .80) and edge band; back scoop to H4.72", "reason": "short neck and shoulder line at the chin level as on the original"},
    {"id": "V05", "what": "arm sections", "plan": "upper 1.08/1.03 -> .91/.88, forearm .91/.88 -> .70/.68, chamfer .11", "v2": "upper %s, forearm %s, chamfer .17" % (UPPER_SEC, LOWER_SEC), "reason": "original arms are about 1.4x thicker; the forearm end is .84 x .74 so that it clears the outer plate pack"},
    {"id": "V06", "what": "fists", "plan": "right .73/.80/.72, left .73/.72/.71", "v2": "right .78/.98/.98 at %s, left .76/.96/.96 at %s, bevel .13/.14, integrated thumb blocks" % (_r(FIST_R), _r(FIST_L)), "reason": "heavy fists, fist/forearm width ratio .92 (original .93)"},
    {"id": "V07", "what": "legs and stance", "plan": "hips +-.73, knees +-.81, ankles +-.88, shorts leg W1.22", "v2": "hips +-.90, knees +-.98, ankles +-1.04, shorts leg W1.42..1.52 (centres +-.90), pelvis W3.00", "reason": "wide stance and loose shorts of the original (shorts wider than the tank hem)"},
    {"id": "V08", "what": "face", "plan": "rectangular eye whites, flat patches, lip plate, support block", "v2": "oval eyes .41 x .22 (tilted), round iris d.16, pupil d.10, one glint, brows covering the upper lid, nose front F1.14 (0.38 proud), moustache F1.03, curved smile (teeth band + compact crescent), no lip plate / support block", "reason": "points 05.1-05.3 of the V2 order"},
    {"id": "V09", "what": "beard", "plan": "U contour extruded to F.97/1.09", "v2": "6 jaw sections (chin F1.12, cheeks F1.07, back F-.28..+.05) with a cut face window; sideburns end at the ear", "reason": "point 05.4: full beard around the jaw, no frame, no long flat back wall"},
    {"id": "V10", "what": "neck", "plan": "neck .90 x .80 x .46", "v2": "block .86 x .70 x .50 inside the scaled skull / torso / beard (shoulder line at H5.15)", "reason": "short wide neck, no separate block in profile"},
    {"id": "V11", "what": "tank edge", "plan": "armhole rim ribbon, straps as shell remainder", "v2": "no rim ribbon (it showed as a thin loop); neckline walls are a tank-edge band; straps = shell between neckline (.90) and arm, width ~.47, continuous front-to-back", "reason": "point 06: no sharp flaps / thin torn edges"},
    {"id": "V12", "what": "dumbbell", "plan": "r.76/.68/.55, t.27/.22/.18, centre (-1.72,1.78,3.31), axis L2.50", "v2": "r.98/.88/.72, t.34/.28/.24 contiguous (no gaps/washers), grip half %.2f, centre %s; length %.2f, pack thickness/diameter %.2f" % (GRIP_HALF, _r(GRIP_R), 2 * GRIP_HALF + 2 * (.06 + sum(t for t, _ in PLATES) + .06 + .03), (.06 + sum(t for t, _ in PLATES) + .06) / (2 * PLATES[0][1])), "reason": "point 07; the grip gap must exceed the forearm width"},
    {"id": "V13", "what": "bag", "plan": "box 1.32 x 1.02 x 1.24 with flat orange panels, black frame, centre band, end plates", "v2": "soft duffel, 5 rounded sections H.28..1.34, W1.64 max, D1.04 max, orange ends / dark middle, no panels, no frame, no centre band; handles with F converging into the fist", "reason": "point 08 (also removes the coplanar-panel ripple)"},
    {"id": "V14", "what": "shoes", "plan": "flat sole+upper, white bumper step, heel loop behind the shin", "v2": "sole W1.40 x D2.00 x H.34 (bevel .10), upper lofted along F (collar H.86 -> toe), ONE white toe cap, tongue wedge + 2 lace bands on the instep, orange loop on top of the tongue, orange side accent, one rotation (7 deg) about the ankle for the whole set", "reason": "point 09"},
    {"id": "V15", "what": "face materials", "plan": "per-type roughness, baked eyes", "v2": "unchanged from Review: one atlas material (roughness .8), face details are flat geometry", "reason": "Studio gets the atlas as ColorMap"},
]
json.dump(DEVIATIONS, open(os.path.join(OUT, "data", "deviations_from_prompt.json"), "w"), indent=1)
json.dump({"asset": "GymDad_Review", "units": "studs", "height_target": 6.40, "height_built": RESULT["bounds_body"]["height"], "joints_blender": JOINTS_BL, "part_bbox_centres_blender": CENTRES,
           "tables": {"torso_rows_D": TORSO, "skull_rows": SKULL, "nose_rows": NOSE}, "right_bend_hint": list(RHINT), "left_bend_hint": list(LHINT), "L1_L2": [L1, L2], "head_scale": HS,
           "elbow_contours": {k: [list(map(float, p)) for p in v] for k, v in ELBOW_RING.items()}, "palette": [{"index": i, "name": n_, "hex": h_} for i, (n_, h_, _) in enumerate(PAL)],
           "counts": {"body_tris": body_tris, "prop_tris": prop_tris}, "measured": RESULT, "deviations_from_prompt": DEVIATIONS},
          open(os.path.join(OUT, "data", "construction_spec_actual.json"), "w"), indent=1)
json.dump({"pose": "HoldWeights (rest pose == pose)", "joints_logical_XFH": {k: list(v) for k, v in JOINTS.items()}, "joints_blender": JOINTS_BL,
           "grips": {"DumbbellGrip": {"from": "RightHand", "to": "Dumbbell", "centre_logical_XFH": list(GRIP_R), "axis": "X"},
                     "BagGrip": {"from": "LeftHand", "to": "GymBag", "point_logical_XFH": [FIST_L[0], FIST_L[1], 2.0]}},
           "wrist_vs_hand_centre": {"RightWrist": list(JOINTS["RightWrist"]), "RightHandCentre": list(FIST_R), "LeftWrist": list(JOINTS["LeftWrist"]), "LeftHandCentre": list(FIST_L)}},
          open(os.path.join(OUT, "data", "joints_pose_grips.json"), "w"), indent=1)
json.dump({"asset": "GymDad_Review", "components": COMP_LOG,
           "part_totals": {k: {"components": len(v.comps), "tris": AUDIT[k]["tris"], "verts": AUDIT[k]["verts"]} for k, v in PARTS.items()},
           "mesh_names": {k: v.geo for k, v in PARTS.items()}}, open(os.path.join(OUT, "data", "component_registry.json"), "w"), indent=1)
RIG = {"asset": "GymDad_Review", "frame": {"logical": "(X,F,H) anatomical RIGHT = -X, forward = +F", "blender": "(X,-F,H)", "roblox_position": "(-X, H, -F)"},
       "bones": [{"name": n, "parent": p, "head_logical": logical(h), "tail_logical": logical(t), "head_roblox": roblox_pos(h)} for n, p, h, t in BONES],
       "joints_logical": {k: list(v) for k, v in JOINTS.items()},
       "grips": {"DumbbellGrip": {"joint": "RightHand -> Dumbbell", "centre_logical": list(GRIP_R), "axis": "X"}, "BagGrip": {"joint": "LeftHand -> GymBag", "point_logical": [FIST_L[0], FIST_L[1], 2.0]}},
       "weights": "100% own bone (rigid); Dumbbell -> RightHand, GymBag -> LeftHand (props exported as separate meshes without armature)",
       "part_origin_logical": {k: logical(v.joint) for k, v in PARTS.items()}, "part_bbox_centres_blender": CENTRES, "joints_blender": JOINTS_BL, "pose": "HoldWeights == rest pose (built directly, pose bones identity)"}
json.dump(RIG, open(os.path.join(OUT, "data", "rig_manifest.json"), "w"), indent=1)
print("RESULT", json.dumps({k: RESULT[k] for k in ("bounds_body", "tris_body", "tris_props", "symmetry", "arm_lengths", "axes", "pose_bones_identity")}))

if NORENDER:
    sys.exit(0)

# ----------------------------------------------------------------------------------------------
# cameras / light / render helpers (real Blender renders of the built scene)
# ----------------------------------------------------------------------------------------------
world = bpy.data.worlds.new("GD_World")
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
SCENE.eevee.taa_render_samples = 8 if QUICK else 32
SCENE.render.image_settings.file_format = 'PNG'
SCENE.view_settings.view_transform = 'Standard'
SCENE.render.film_transparent = False

FLATM = bpy.data.materials.new("GD_Flat")
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


# matching camera: ortho, view from logical (8,12,7) = Blender (8,-12,7), target (0,0,3.15), Ortho Scale 7.8 (start values of the plan)
MATCH_DIR = V((8, -12, 7)).normalized()
MATCH_T = V((0, 0, 3.15))
MATCH_LOC = MATCH_T + MATCH_DIR * 40
CAMCFG = {"type": "ORTHO", "target": [0, 0, 3.15], "direction_blender": list(MATCH_DIR), "distance": 40.0, "ortho_scale": 7.8, "roll_deg": 0.0,
          "note": "start camera of the plan; tuned values are written below if a tuning pass was done"}
if os.path.exists(os.path.join(HERE, "inputs", "camera_tuned.json")):
    CAMCFG.update(json.load(open(os.path.join(HERE, "inputs", "camera_tuned.json"))))
    MATCH_DIR = V(CAMCFG["direction_blender"]).normalized()
    MATCH_T = V(CAMCFG.get("target", [0, 0, 3.15]))
    MATCH_LOC = MATCH_T + MATCH_DIR * CAMCFG["distance"]
json.dump(CAMCFG, open(os.path.join(OUT, "data", "camera.json"), "w"), indent=1)

T = V((0, 0, 3.2))
SC = 7.6
# stage views (the model is built in one pass; these are the staged views of the finished scene)
shot("stage01_silhouette.png", MATCH_LOC, MATCH_T, res=(880, 860), ortho=CAMCFG["ortho_scale"], flat=True, show_only=[k for k in PARTS if k not in PROPS], roll=CAMCFG["roll_deg"])
shot("stage02_face_clothes.png", MATCH_LOC, MATCH_T, res=(880, 860), ortho=CAMCFG["ortho_scale"], hide=PROPS, roll=CAMCFG["roll_deg"])
shot("stage03_props_grips.png", MATCH_LOC, MATCH_T, res=(880, 860), ortho=CAMCFG["ortho_scale"], roll=CAMCFG["roll_deg"])
shot("match_crop_size_440x430.png", MATCH_LOC, MATCH_T, res=(440, 430), ortho=CAMCFG["ortho_scale"], roll=CAMCFG["roll_deg"])
shot("match_view_full_uncropped.png", MATCH_LOC, V((MATCH_T.x, MATCH_T.y, 3.2)), res=(1000, 1000), ortho=7.6, roll=CAMCFG["roll_deg"])   # same direction as the matching camera, scale 7.6 so nothing is cropped
# full body orthographic (anatomical names)
shot("full_front_ortho.png", orbit(T, 40, 0, 0), T, ortho=SC)
shot("full_back_ortho.png", orbit(T, 40, 180, 0), T, ortho=SC)
shot("full_right_profile_dumbbell_ortho.png", orbit(T, 40, -90, 0), T, ortho=SC)
shot("full_left_profile_bag_ortho.png", orbit(T, 40, 90, 0), T, ortho=SC)
shot("full_front34_right.png", orbit(T, 40, -35, 8), T, ortho=SC)
shot("full_front34_left.png", orbit(T, 40, 35, 8), T, ortho=SC)
shot("full_back34_right.png", orbit(T, 40, -145, 8), T, ortho=SC)
shot("full_back34_left.png", orbit(T, 40, 145, 8), T, ortho=SC)
shot("full_top_oblique.png", orbit(T, 40, 30, 52), T, ortho=SC)
# faces
HT = V((0, -.2, 5.3))
shot("face_front.png", orbit(HT, 20, 0, 2), HT, res=(900, 900), ortho=2.6)
shot("face_34.png", orbit(HT, 20, -32, 6), HT, res=(900, 900), ortho=2.6)
shot("face_profile_right.png", orbit(HT, 20, -90, 2), HT, res=(900, 900), ortho=2.6)
shot("face_profile_left.png", orbit(HT, 20, 90, 2), HT, res=(900, 900), ortho=2.6)
# neckline / armholes, back, shoulders / elbows / wrists
NT = V((0, -.4, 4.4))
shot("neckline_front.png", orbit(NT, 20, 0, 8), NT, res=(900, 900), ortho=3.8)
shot("neckline_back.png", orbit(NT, 20, 180, 8), NT, res=(900, 900), ortho=3.8, hide=("Dumbbell",))
shot("armhole_right.png", orbit(V((-1.5, 0, 4.4)), 20, -90, 10), V((-1.5, 0, 4.4)), res=(900, 900), ortho=3.2)
shot("armhole_left.png", orbit(V((1.5, 0, 4.4)), 20, 90, 10), V((1.5, 0, 4.4)), res=(900, 900), ortho=3.2)
shot("right_arm_side.png", orbit(V((-2.0, -.7, 3.9)), 20, -90, 4), V((-2.0, -.7, 3.9)), res=(900, 900), ortho=3.6)
shot("right_arm_top.png", orbit(V((-2.0, -.7, 3.9)), 20, -40, 70), V((-2.0, -.7, 3.9)), res=(900, 900), ortho=3.6)
shot("left_arm_front.png", orbit(V((2.2, 0, 3.6)), 20, 15, 5), V((2.2, 0, 3.6)), res=(900, 900), ortho=3.6)
shot("left_arm_side.png", orbit(V((2.2, 0, 3.6)), 20, 90, 5), V((2.2, 0, 3.6)), res=(900, 900), ortho=3.6)
# grips
GT = V((-1.72, -1.7, 3.3))
shot("grip_right_front.png", orbit(GT, 20, 0, 6), GT, res=(900, 900), ortho=3.4)
shot("grip_right_back.png", orbit(GT, 20, 180, 6), GT, res=(900, 900), ortho=3.4, hide=("UpperTorso", "LowerTorso", "Head", "RightUpperArm", "LeftUpperArm", "LeftLowerArm", "LeftHand", "GymBag"))
shot("grip_right_top.png", orbit(GT, 20, 0, 80), GT, res=(900, 900), ortho=3.4)
DT = V((-1.72, -1.78, 3.31))
shot("dumbbell_front_axis.png", orbit(DT, 20, 0, 6), DT, res=(900, 900), ortho=3.4, show_only=("Dumbbell",))
shot("dumbbell_end.png", orbit(DT, 20, -90, 6), DT, res=(900, 900), ortho=3.4, show_only=("Dumbbell",))
shot("dumbbell_34.png", orbit(DT, 20, -40, 24), DT, res=(900, 900), ortho=3.8, show_only=("Dumbbell",))
LT = V((2.23, -.17, 2.1))
shot("grip_left_front.png", orbit(LT, 20, 0, 6), LT, res=(900, 900), ortho=2.4)
shot("grip_left_back.png", orbit(LT, 20, 180, 6), LT, res=(900, 900), ortho=2.4, hide=("LowerTorso",))
BT = V((2.56, 0, 1.0))
shot("bag_front.png", orbit(BT, 20, 0, 4), BT, res=(900, 900), ortho=2.6, show_only=("GymBag",))
shot("bag_back.png", orbit(BT, 20, 180, 4), BT, res=(900, 900), ortho=2.6, show_only=("GymBag",))
shot("bag_top.png", orbit(BT, 20, 0, 85), BT, res=(900, 900), ortho=2.6, show_only=("GymBag",))
shot("bag_34.png", orbit(BT, 20, 35, 22), BT, res=(900, 900), ortho=2.8, show_only=("GymBag",))
# feet
FT_ = V((0, 0, .4))
shot("feet_front.png", orbit(FT_, 20, 0, 6), FT_, res=(900, 700), ortho=3.6, show_only=("RightFoot", "LeftFoot", "RightLowerLeg", "LeftLowerLeg"))
shot("foot_side_right.png", orbit(V((-.88, 0, .4)), 20, -90, 6), V((-.88, 0, .4)), res=(900, 700), ortho=3.2, show_only=("RightFoot", "RightLowerLeg"))
shot("feet_top.png", orbit(FT_, 20, 0, 88), FT_, res=(900, 700), ortho=3.6, show_only=("RightFoot", "LeftFoot"))
shot("feet_sole.png", orbit(FT_, 20, 0, -88), FT_, res=(900, 700), ortho=3.6, show_only=("RightFoot", "LeftFoot"))
shot("legs_front_ortho.png", orbit(V((0, 0, 1.4)), 20, 0, 0), V((0, 0, 1.4)), res=(900, 800), ortho=3.4, hide=("Dumbbell", "GymBag"))
print("ALL_RENDERS_DONE", len(RENDERED))
