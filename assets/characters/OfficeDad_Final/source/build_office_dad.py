"""Procedural Blender build for the Office Dad redesign ("Steal a Dad!").

Source of truth: OfficeDad_Illustrated_MasterPrompt.pdf (owner's master prompt).
Primary reference: reference/OfficeDad_Reference_Crop.png (327x370, unchanged).

Frames / units
--------------
1 Blender unit = 1 Roblox stud (scene scale_length 0.01).
Logical (X, D, H): X<0 = anatomical RIGHT (briefcase hand), D<0 = front, H up, sole at H=0.
Blender (x, y, z) = (X, D, H).  FBX export axis_forward='Z', axis_up='Y' (project mapping):
Roblox position of logical (X,D,H) = (-X, H, D); the character faces -Z.

Run headless:
    blender -b --factory-startup --python build_office_dad.py -- <output_dir> [--quick] [--norender]
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

# palette: master prompt section 05 (tiles 0..39); BRASS is garbled in the PDF text layer ("#D 8A134") -> #D8A134
PAL = [
    ("SKIN", "#F4A16C", "face, hands, arms"), ("SKIN_LIGHT", "#FFC18E", "lit skin facets"),
    ("SKIN_SHADOW", "#C77D55", "under nose / inner ear / creases"), ("NOSE", "#ED8B56", "nose"),
    ("HAIR", "#4B342D", "hair"), ("HAIR_LIGHT", "#71513D", "hair top planes"), ("HAIR_DARK", "#2C2528", "hair recesses"),
    ("MUSTACHE", "#3A2A24", "mustache"), ("BROW", "#362922", "brows"), ("GLASSES", "#161719", "frames"),
    ("EYE_WHITE", "#FFF6E4", "eye whites"), ("IRIS", "#402B18", "iris"), ("PUPIL", "#0D1111", "pupil"),
    ("MOUTH", "#A86244", "mouth"), ("SHIRT", "#F6E7C8", "shirt"), ("SHIRT_LIGHT", "#FFF3DA", "shirt top/front facets"),
    ("SHIRT_SHADOW", "#DBCAA9", "shirt shade, underside"), ("SHIRT_SEAM", "#B9A88C", "shirt seams"),
    ("TIE", "#91323C", "tie"), ("TIE_LIGHT", "#B9444C", "tie lit"), ("TIE_DARK", "#65242E", "tie shade/fold"),
    ("TROUSER", "#47403F", "trousers"), ("TROUSER_LIGHT", "#59504D", "trouser front planes"), ("TROUSER_DARK", "#302D2F", "trouser seams/shade"),
    ("BELT", "#252326", "belt"), ("SILVER", "#B8B6AD", "buckle"), ("SILVER_LIGHT", "#E4DFD3", "buckle light"),
    ("SHOE", "#202123", "shoes"), ("SHOE_LIGHT", "#333336", "shoe top planes"), ("SOLE", "#101114", "soles"),
    ("CASE", "#4D2E2B", "briefcase"), ("CASE_SIDE", "#754528", "briefcase sides"), ("CASE_EDGE", "#332323", "case seams/edges"),
    ("BRASS", "#D8A134", "brass locks"), ("BRASS_SHADOW", "#9E7024", "brass shade"),
    ("PEN_BLUE", "#116591", "pen"), ("PEN_LIGHT", "#298AB5", "pen light"), ("PEN_DARK", "#06496E", "pen dark"),
    ("EYE_GLINT", "#FFFFFF", "glint"), ("RECESS", "#684331", "recesses"),
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
# containers + shading rules
# ----------------------------------------------------------------------------------------------
PARTS = {}
COMP_LOG = []
SRC_COLL = bpy.data.collections.new("SOURCE_Components")
SCENE.collection.children.link(SRC_COLL)
EXP_COLL = bpy.data.collections.new("EXPORT_OfficeDad")
SCENE.collection.children.link(EXP_COLL)
_H = {n: h for n, h, _ in PAL}
HEXOF = _H


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


def sh_trouser(n, c):
    if n.z < -0.6:
        return "TROUSER_DARK"
    if n.y < -0.62:
        return "TROUSER_LIGHT"
    if n.y > 0.62:
        return "TROUSER_DARK"
    return "TROUSER"


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


def sh_tie(n, c):
    if n.y < -0.6 and n.z > 0.2:
        return "TIE_LIGHT"
    if n.z < -0.5:
        return "TIE_DARK"
    return "TIE"


def sh_case(n, c):
    if abs(n.x) > 0.6:
        return "CASE_SIDE"
    return "CASE"


def sh_nose(n, c):
    if n.z < -0.55:
        return "SKIN_SHADOW"
    if n.z > 0.45:
        return "SKIN_LIGHT"
    return "NOSE"


# ----------------------------------------------------------------------------------------------
# prescribed numeric tables (master prompt sections 07, 10, 11, 12, 18, 23)
# ----------------------------------------------------------------------------------------------
UT_ROWS = [(2.44, 2.58, -.93, .56, .12), (2.72, 2.76, -1.00, .62, .14), (3.15, 2.80, -1.02, .65, .16),
           (3.63, 2.72, -.90, .61, .14), (4.05, 2.80, -.70, .54, .12), (4.30, 2.48, -.57, .49, .10)]
LT_ROWS = [(1.65, 2.25, -.70, .48, .14), (1.92, 2.55, -.82, .55, .14), (2.28, 2.68, -.89, .59, .12), (2.50, 2.62, -.92, .57, .10)]
# head: prescribed W1.80 D1.34 H1.73 (bottom 4.30, top 6.03), front D-.70 back +.64, jaw 1.61 (section 18)
HEAD_ROWS = [(4.30, 1.26, -.60, .44, .14), (4.50, 1.61, -.70, .58, .14), (5.10, 1.80, -.70, .64, .14),
             (5.70, 1.80, -.68, .64, .12), (6.03, 1.62, -.58, .56, .12)]
NOSE_ROWS = [(5.12, .42, -1.05, -.72, .05), (5.25, .55, -1.22, -.72, .06), (5.40, .50, -1.14, -.72, .06),
             (5.52, .26, -.90, -.74, .05), (5.61, .20, -.80, -.74, .04)]
UPPER_SEC = [(0.0, 1.10, 1.00), (.5, 1.07, .98), (1.0, 1.02, .95)]
LOWER_SEC = [(0.0, 1.02, .95), (.5, 1.03, .96), (1.0, 1.03, .98)]
JOINTS = {
    "Root": (0, 0, 2.20), "Waist": (0, 0, 2.47), "Neck": (0, 0, 4.34),
    "RightShoulder": (-1.60, 0, 4.15), "RightElbow": (-1.83, -.02, 3.10), "RightWrist": (-1.98, -.10, 2.25),
    "LeftShoulder": (1.60, 0, 4.15), "LeftElbow": (1.83, -.02, 3.10), "LeftWrist": (1.98, -.10, 2.25),
    "RightHip": (-.66, .02, 1.92), "RightKnee": (-.66, .01, .97), "RightAnkle": (-.66, 0, .40),
    "LeftHip": (.66, .02, 1.92), "LeftKnee": (.66, .01, .97), "LeftAnkle": (.66, 0, .40),
}
JV = {k: V(v) for k, v in JOINTS.items()}
GRIP = V((-2.20, -.25, 1.94))
CASE_O = V((-2.20, -.25, .08))


def ut_front(x, h):
    return front_at(UT_ROWS, min(max(h, 2.44), 4.30), x)


def lt_front(x, h):
    return front_at(LT_ROWS, min(max(h, 1.65), 2.50), x)


def lt_back(x, h):
    return back_at(LT_ROWS, min(max(h, 1.65), 2.50), x)


def hf(h, x=0.0):
    return front_at(HEAD_ROWS, h, x)


def hb(h, x=0.0):
    return back_at(HEAD_ROWS, h, x)


# ----------------------------------------------------------------------------------------------
# UpperTorso: shirt, neck, collar, placket, tie, pocket, pens
# ----------------------------------------------------------------------------------------------
ut = PM("UpperTorso", JV["Waist"])
loft(ut, "UT_shirt_body", [row_ring(r) for r in UT_ROWS], sh_shirt,
     meta={"recipe": "8-point chamfered loft, section 07 rows", "dims": {"rows": UT_ROWS}, "class": "observed+prescribed"})
loft(ut, "UT_neck", [ring8(.29, -.26, .26, .08, 0, 0, 4.11), ring8(.29, -.26, .26, .08, 0, 0, 4.49)], sh_skin,
     meta={"recipe": "neck .58 x .52 x .38 centre H4.30, bevel .08", "class": "prescribed"})
loft(ut, "UT_collar_band", [ring8(.34, -.31, .31, .09, 0, 0, 4.22), ring8(.34, -.31, .31, .09, 0, 0, 4.40)], sh_shirt,
     meta={"recipe": "rear/neck collar band .045 proud", "class": "observed+prescribed"})
for s in (-1, 1):
    pts = [(-.68, 4.24, .0), (-.18, 4.30, .0), (-.06, 4.10, .02), (-.45, 3.83, .04)]
    poly = []
    for x, h, off in pts:
        X = x if s < 0 else -x
        poly.append(V((X, ut_front(X, h) - .0 - off, h)))
    prism_poly(ut, "UT_collar_lobe_" + ("R" if s < 0 else "L"), poly, (0, -.045, 0), lambda n, c: "SHIRT_LIGHT" if n.y < -0.5 else "SHIRT_SHADOW",
               {"recipe": "collar lobe, 4 corners of section 08, .045 thick", "class": "observed+prescribed"})
front_strip(ut, "UT_placket", -.055, .055, [2.61, 3.0, 3.6, 4.17], .012, .01, "SHIRT_SEAM", ffn=ut_front,
            meta={"recipe": "placket .11 wide, H2.61..4.17", "class": "observed+prescribed"})
# tie: knot + blade (+ fold line)
KNOT = [(-.175, 4.29), (.175, 4.29), (.12, 4.02), (-.12, 4.02)]
poly = [V((x, ut_front(x, h) - .025 - .07, h)) for x, h in KNOT]
prism_poly(ut, "UT_tie_knot", [p + V((0, .07, 0)) for p in poly], (0, -.07, 0), sh_tie,
           {"recipe": "tie knot W.35 -> .24, thickness .07", "class": "observed+prescribed"})
def _edge(xa, ha, xb, hb, hs):
    return [(xa + (xb - xa) * (h - ha) / (hb - ha), h) for h in hs]


_MID = [3.63, 3.15, 2.90]
BLADE = [(-.12, 4.03), (.12, 4.03)] + _edge(.12, 4.03, .255, 2.76, _MID) + [(.255, 2.76), (0, 2.56), (-.255, 2.76)] + _edge(-.255, 2.76, -.12, 4.03, _MID[::-1])
layered_plate(ut, "UT_tie_blade", BLADE, ut_front, [(.01, 1.0, 1.0), (-.025, 1.0, 1.0), (-.07, 1.0, 1.0)], sh_tie,
              {"recipe": "tie blade polygon of section 08, .045 proud of the shirt (+.025 gap)", "class": "observed+prescribed"})
_fh = [4.0, 3.8, 3.63, 3.4, 3.15, 2.9, 2.7, 2.58]
thin_polyline(ut, "UT_tie_fold", [V((-.04 + .07 * (4.0 - h) / 1.42, ut_front(-.04 + .07 * (4.0 - h) / 1.42, h) - .076, h)) for h in _fh], .02, .004, .004, sh_const("TIE_DARK"),
              meta={"recipe": "tie fold line", "class": "observed+prescribed"})
# chest pocket on the character's LEFT (X>0) + two pens
PX, PH = .83, 3.46
pf = ut_front(PX, PH) - .035
POCKET = [(PX - .235, 3.695), (PX + .235, 3.695), (PX + .235, 3.28), (PX, 3.225), (PX - .235, 3.28)]
layered_plate(ut, "UT_pocket", POCKET, ut_front, [(.01, 1.0, 1.0), (-.035, 1.0, 1.0)], lambda n, c: "SHIRT_LIGHT" if n.z > .5 else ("SHIRT_SHADOW" if n.z < -.5 else "SHIRT"),
              {"recipe": "chest pocket .47 x .47, thickness .035, H3.225..3.695", "class": "observed+prescribed"})
thin_polyline(ut, "UT_pocket_top_seam", [V((PX - .235, pf - .008, 3.69)), V((PX + .235, pf - .008, 3.69))], .012, .004, .004,
              sh_const("SHIRT_SEAM"), meta={"recipe": "pocket top stitch", "class": "observed+prescribed"})
for px_ in (.71, .88):
    cy = pf - .015 - .0525
    for z0, z1, r, tile in ((3.36, 3.82, .0525, "PEN_BLUE"), (3.82, 3.98, .06, "PEN_DARK")):
        rr = [[V((px_ + r * math.cos(k * math.pi / 4 + math.pi / 8), cy + r * math.sin(k * math.pi / 4 + math.pi / 8), z)) for k in range(8)] for z in (z0, z1)]
        loft(ut, "UT_pen_%s_%s" % (tile, str(px_)), rr, sh_const(tile), meta={"recipe": "pen body/cap, 8-sided", "class": "observed+prescribed"})
    solid_box(ut, "UT_pen_clip_%s" % px_, px_ - .0125, px_ + .0125, cy - .0525 - .025, cy - .0525, 3.67, 3.86, sh_const("PEN_LIGHT"),
              {"recipe": "pen clip .025 x .025 x .19", "class": "observed+prescribed"})

# ----------------------------------------------------------------------------------------------
# LowerTorso: trousers, belt, buckle, loops, fly, pocket seams
# ----------------------------------------------------------------------------------------------
lt = PM("LowerTorso", JV["Root"])
loft(lt, "LT_trouser_pelvis", [row_ring(r) for r in LT_ROWS], sh_trouser,
     meta={"recipe": "8-point chamfered loft, section 10 rows", "dims": {"rows": LT_ROWS}, "class": "observed+prescribed"})
brings = []
for h in (2.34, 2.45, 2.56):
    w, f, b, c = interp_row(LT_ROWS, h)
    brings.append(ring8(w / 2 + .045, f - .045, b + .045, c + .045, 0, 0, h))
loft(lt, "LT_belt", brings, lambda n, c: "BELT", meta={"recipe": "belt H2.34..2.56, .045 thick", "class": "observed+prescribed"})
bf = lt_front(0, 2.45) - .045
bx0, bx1, bz0, bz1 = -.195, .195, 2.45 - .14, 2.45 + .14
ix0, ix1, iz0, iz1 = -.135, .135, 2.45 - .08, 2.45 + .08
for nm, (x0, x1, z0, z1) in {"top": (bx0, bx1, iz1, bz1), "bottom": (bx0, bx1, bz0, iz0), "left": (bx0, ix0, iz0, iz1), "right": (ix1, bx1, iz0, iz1)}.items():
    solid_box(lt, "LT_buckle_" + nm, x0, x1, bf - .055, bf + .005, z0, z1, lambda n, c: "SILVER_LIGHT" if n.z > .5 else "SILVER",
              {"recipe": "buckle frame .39 x .28 x .055, opening .27 x .16", "class": "observed+prescribed"})
solid_box(lt, "LT_buckle_prong", -.12, .15, bf - .045, bf - .01, 2.45 - .0075, 2.45 + .0075, sh_const("SILVER"),
          {"recipe": "buckle prong", "class": "observed+prescribed"})
LOOP = [(2.29, .02), (2.34, .02), (2.345, .065), (2.555, .065), (2.56, .02), (2.61, .02)]
for lx, front in ((-.92, True), (.92, True), (-.78, False), (.78, False)):
    front_strip(lt, "LT_beltloop_%s%+.2f" % ("F" if front else "B", lx), lx - .05, lx + .05, LOOP, 0.0, .012, sh_const("TROUSER_DARK"),
                ffn=(lt_front if front else lt_back), rear=(not front),
                meta={"recipe": "belt loop .10 x .32 x .065", "class": "observed+prescribed" if front else "inferred"})
front_strip(lt, "LT_fly_seam", .064, .076, [1.80, 2.05, 2.30], .006, .01, sh_const("TROUSER_DARK"), ffn=lt_front,
            meta={"recipe": "fly seam .012", "class": "observed+prescribed"})
for s in (-1, 1):
    pts = [V((s * 1.04, lt_front(s * 1.04, 2.24), 2.24)), V((s * .72, lt_front(s * .72, 1.98), 1.98))]
    thin_polyline(lt, "LT_front_pocket_" + ("R" if s < 0 else "L"), pts, .014, .006, .01, sh_const("TROUSER_DARK"),
                  meta={"recipe": "slanted front pocket edge", "class": "observed+prescribed"})
    solid_box(lt, "LT_back_pocket_welt_" + ("R" if s < 0 else "L"), s * .58 - .215, s * .58 + .215, lt_back(s * .58, 2.15) - .005, lt_back(s * .58, 2.15) + .012,
              2.10, 2.20, sh_const("TROUSER_DARK"), {"recipe": "rear pocket welt .43 x .10 (inferred)", "class": "inferred"})

# ----------------------------------------------------------------------------------------------
# Head
# ----------------------------------------------------------------------------------------------
hd = PM("Head", JV["Neck"])
loft(hd, "HD_shell", [row_ring(r, 0, -.03 * 0) for r in HEAD_ROWS], sh_skin,
     meta={"recipe": "closed chamfered loft, section 18 (W1.80 D1.34 H1.73)", "dims": {"rows": HEAD_ROWS}, "class": "observed+prescribed"})
for s in (-1, 1):
    cx, cd, chh = s * .94, -.01, 5.10
    a, b, cc = .15, .235, .055
    o = [(-a + cc, -b), (a - cc, -b), (a, -b + cc), (a, b - cc), (a - cc, b), (-a + cc, b), (-a, b - cc), (-a, -b + cc)]
    x_in, x_out = s * .80, s * 1.065
    nm = "R" if s < 0 else "L"
    body_poly = [V((x_in, cd + d, chh + h)) for d, h in o]
    prism_poly(hd, "HD_ear_body_" + nm, body_poly, (x_out - x_in - s * .035, 0, 0), sh_skin,
               {"recipe": "ear block .25 x .30 x .47 bevel .055 (recessed .035)", "class": "observed+prescribed"})
    xr = x_out - s * .035
    rd, rh = .06, .125
    for part, (d0, d1, h0, h1) in {"top": (-a, a, rh, b), "bottom": (-a, a, -b, -rh), "front": (-a, -rd, -rh, rh), "back": (rd, a, -rh, rh)}.items():
        poly = [V((xr, cd + d0, chh + h0)), V((xr, cd + d1, chh + h0)), V((xr, cd + d1, chh + h1)), V((xr, cd + d0, chh + h1))]
        prism_poly(hd, "HD_ear_rim_%s_%s" % (part, nm), poly, (s * .035, 0, 0), sh_skin, {"recipe": "ear rim", "class": "observed+prescribed"})
    fl = [V((xr, cd - rd, chh - rh)), V((xr, cd + rd, chh - rh)), V((xr, cd + rd, chh + rh)), V((xr, cd - rd, chh + rh))]
    prism_poly(hd, "HD_ear_recess_" + nm, fl, (s * .004, 0, 0), sh_const("SKIN_SHADOW"), {"recipe": "ear recess .12 x .25", "class": "observed+prescribed"})

# eyes (inside the lens openings): white .37 x .34, iris .20, pupil .14, glint
for s in (-1, 1):
    nm = "R" if s < 0 else "L"
    ex, eh = s * .36, 5.36
    f = hf(eh, ex)
    w_, h_ = .37, .34
    loft(hd, "HD_eye_white_" + nm, [[V((ex - w_ / 2, f + .02, eh - h_ / 2)), V((ex + w_ / 2, f + .02, eh - h_ / 2)), V((ex + w_ / 2, f + .02, eh + h_ / 2)), V((ex - w_ / 2, f + .02, eh + h_ / 2))],
                                    [V((ex - w_ / 2 + .02, f - .02, eh - h_ / 2 + .02)), V((ex + w_ / 2 - .02, f - .02, eh - h_ / 2 + .02)),
                                     V((ex + w_ / 2 - .02, f - .02, eh + h_ / 2 - .02)), V((ex - w_ / 2 + .02, f - .02, eh + h_ / 2 - .02))]],
         sh_const("EYE_WHITE"), meta={"recipe": "eye white .37 x .34", "class": "observed+prescribed"})
    ix = ex - s * .02
    for rr_, tile, dd in ((.10, "IRIS", .025), (.07, "PUPIL", .03)):
        p8 = [V((ix + rr_ * math.cos(k * math.pi / 4 + math.pi / 8), f - dd, eh + rr_ * math.sin(k * math.pi / 4 + math.pi / 8))) for k in range(8)]
        prism_poly(hd, "HD_%s_%s" % (tile.lower(), nm), p8, (0, -.008, 0), sh_const(tile), {"recipe": tile + " disc", "class": "observed+prescribed"})
    solid_box(hd, "HD_glint_" + nm, ix + .02, ix + .05, f - .045, f - .036, eh + .03, eh + .06, sh_const("EYE_GLINT"),
              {"recipe": "eye glint", "class": "observed+prescribed"})
    # eyebrow: (-.68,5.65) -> (-.15,5.78), worried slant (inner end higher)
    xa, xb = (-.68, -.15) if s < 0 else (.15, .68)
    ha_, hb_ = (5.65, 5.78) if s < 0 else (5.78, 5.65)
    P0, P1 = V((xa, 0, ha_)), V((xb, 0, hb_))
    L = (P1 - P0)
    n2 = V((-L.z, 0, L.x)).normalized()
    up_half = .055
    fr = hf((ha_ + hb_) / 2, (xa + xb) / 2)
    pts = [P0 - n2 * up_half, P1 - n2 * up_half, P1 + n2 * up_half, P0 + n2 * up_half]
    prism_poly(hd, "HD_brow_" + nm, [V((p.x, fr + .02, p.z)) for p in pts], (0, -.14, 0), lambda n, c: "BROW",
               {"recipe": "eyebrow slanted bar, thickness .14, height .11", "class": "observed+prescribed"})

# glasses: rim around each lens, bridge, temple arms
FR = -.845
for s in (-1, 1):
    nm = "R" if s < 0 else "L"
    cx, ch = s * .37, 5.37
    ow, oh, iw, ih = .64, .56, .53, .45
    for part, (x0, x1, z0, z1) in {"top": (cx - ow / 2, cx + ow / 2, ch + ih / 2, ch + oh / 2), "bottom": (cx - ow / 2, cx + ow / 2, ch - oh / 2, ch - ih / 2),
                                   "in": (cx - ow / 2, cx - iw / 2, ch - ih / 2, ch + ih / 2), "out": (cx + iw / 2, cx + ow / 2, ch - ih / 2, ch + ih / 2)}.items():
        solid_box(hd, "HD_glasses_%s_%s" % (part, nm), x0, x1, FR - .02 + .0 - .045 + .045, FR + .045, z0, z1, sh_const("GLASSES"),
                  {"recipe": "glasses rim, outer .64 x .56, opening .53 x .45", "class": "observed+prescribed"})
    # temple arm: from outer rim back to the ear
    xs = s * .72
    solid_box(hd, "HD_glasses_arm_a_" + nm, min(xs, s * .88), max(xs, s * .88), FR + .02, hb(5.52, s * .88) - .02, 5.52 - .0325, 5.52 + .0325, sh_const("GLASSES"),
              {"recipe": "temple arm along the head side", "class": "observed+prescribed"})
    solid_box(hd, "HD_glasses_arm_b_" + nm, min(s * .88 - .0325, s * .88 + .0325), max(s * .88 - .0325, s * .88 + .0325), hb(5.52, s * .88) - .06, hb(5.52, s * .88) + .03, 5.27, 5.52 + .0325, sh_const("GLASSES"),
              {"recipe": "ear hook", "class": "observed+prescribed"})
solid_box(hd, "HD_glasses_bridge", -.08, .08, FR - .0, FR + .045, 5.52 - .0325, 5.52 + .0325, sh_const("GLASSES"), {"recipe": "bridge .16 x .065", "class": "observed+prescribed"})

# nose
loft(hd, "HD_nose", [ring8(w / 2, f, b, c, 0, 0, h) for h, w, f, b, c in NOSE_ROWS], sh_nose,
     meta={"recipe": "nose bulb/bridge loft, tip D-1.22", "dims": {"rows": NOSE_ROWS}, "class": "observed+prescribed"})
for s in (-1, 1):
    fb = interp_row(NOSE_ROWS, 5.13)[1]
    pts = [V((s * .21 - .0225, fb + .004, 5.13 - .01)), V((s * .21 + .0225, fb + .004, 5.13 - .01)), V((s * .21 + .0225, fb + .004, 5.13 + .01)), V((s * .21 - .0225, fb + .004, 5.13 + .01))]
    prism_poly(hd, "HD_nostril_" + ("R" if s < 0 else "L"), pts, (0, -.012, 0), sh_const("SKIN_SHADOW"), {"recipe": "nostril hint .045 x .020", "class": "observed+prescribed"})

# mustache
MUS = [(-.49, 4.73), (-.51, 4.90), (-.40, 5.06), (-.20, 5.09), (-.02, 4.99), (-.04, 4.78), (-.25, 4.76)]
for s in (-1, 1):
    pts = MUS if s < 0 else [(-x, h) for x, h in MUS][::-1]
    layered_plate(hd, "HD_mustache_" + ("R" if s < 0 else "L"), pts, lambda x, h: hf(h, x),
                  [(.03, 1.0, 1.0), (-.03, 1.0, 1.0), (-.10, .93, .90), (-.17, .78, .72)], lambda n, c: "HAIR_DARK" if n.z < -.3 else "MUSTACHE",
                  {"recipe": "mustache lobe of section 21, depth .18", "class": "observed+prescribed"})
# mouth + chin crease
mp_ = [V((-.215, hf(4.645) - .012, 4.645)), V((0, hf(4.63) - .012, 4.63)), V((.215, hf(4.61) - .012, 4.61))]
P = []
for p in mp_:
    P += [p + V((0, 0, .009)), p - V((0, 0, .009)), p + V((0, .018, .009)), p + V((0, .018, -.009))]
fcs = []
for i in range(len(mp_) - 1):
    a, b = i * 4, (i + 1) * 4
    fcs += [[a, a + 1, b + 1, b], [a + 2, b + 2, b + 3, a + 3], [a, b, b + 2, a + 2], [a + 1, a + 3, b + 3, b + 1]]
e = (len(mp_) - 1) * 4
fcs += [[0, 1, 3, 2], [e, e + 2, e + 3, e + 1]]
hd.solid("HD_mouth", P, fcs, sh_const("MOUTH"), {"recipe": "closed mouth line .018", "class": "observed+prescribed"})
solid_box(hd, "HD_chin_crease", -.14, .14, hf(4.57) - .006, hf(4.57) + .01, 4.5525, 4.5875, sh_const("SKIN_SHADOW"), {"recipe": "chin crease .28 x .035", "class": "observed+prescribed"})

# hair: scalp cap + top blocks (section 22) + sideburn/back clumps
cap_rows = [(5.83, 1.80, -.69, .64, .14), (6.05, 1.76, -.69, .70, .14), (6.19, 1.56, -.62, .70, .12)]
loft(hd, "HD_hair_cap", [row_ring(r, 0, 0) for r in cap_rows], sh_hair, meta={"recipe": "hair mass H5.83..6.19, D-.69..70", "class": "observed+prescribed"})
back_rows = [(5.42, 1.62, .22, .68, .12), (5.60, 1.74, .22, .71, .12), (5.90, 1.78, .22, .72, .12)]
loft(hd, "HD_hair_back_band", [row_ring(r, 0, 0) for r in back_rows], sh_hair, meta={"recipe": "rear hair band H5.42..5.90 (inferred)", "class": "inferred"})
TOP = [((-.76, -.62, 5.91), (-.36, -.66, 6.18), (.10, -.51, 6.26), (.35, -.20, 6.14), .24, .18),
       ((-.48, -.30, 6.12), (-.08, -.28, 6.35), (.29, -.12, 6.40), (.50, .20, 6.22), .28, .20),
       ((-.20, .08, 6.13), (.16, .10, 6.32), (.52, .32, 6.33), (.67, .52, 6.14), .25, .19)]
for ri, row in enumerate(TOP):
    sz, hz = row[4], row[5]
    for ci, (x, d, h) in enumerate(row[:4]):
        top = ring8(sz / 2, -sz * .55, sz * .55, .05, 0, 0, hz / 2)
        mid = ring8(sz / 2 * .95, -sz * .5, sz * .5, .05, 0, 0, 0)
        bot = ring8(sz / 2 * .9, -sz * .5, sz * .5, .05, 0, 0, -hz / 2)
        loft(hd, "HD_hair_top_%d_%d" % (ri, ci), [[p + V((x, d, h - hz / 2)) for p in r] for r in (bot, mid, top)], sh_hair,
             meta={"recipe": "top hair block (section 22 table)", "class": "observed+prescribed"})
SIDE = [((-.88, -.30, 5.84), (-.97, -.10, 5.92), (-.94, .20, 5.78), .29, .17), ((-.91, -.40, 5.60), (-.99, -.10, 5.67), (-.93, .18, 5.54), .27, .16),
        ((.83, -.25, 5.88), (.94, .04, 5.94), (.91, .32, 5.70), .27, .17), ((-.68, .62, 5.83), (0, .72, 5.98), (.68, .60, 5.85), .30, .18)]
for si, row in enumerate(SIDE):
    sz, hz = row[-2], row[-1]
    for ci, (x, d, h) in enumerate(row[:-2]):
        top = ring8(sz / 2, -sz * .5, sz * .5, .045, 0, 0, hz / 2)
        bot = ring8(sz / 2 * .85, -sz * .45, sz * .45, .04, 0, 0, -hz / 2)
        loft(hd, "HD_hair_side_%d_%d" % (si, ci), [[p + V((x, d, h)) for p in r] for r in (bot, top)], sh_hair,
             meta={"recipe": "side/back hair clump (section 22 table)", "class": "observed+prescribed" if si < 3 else "inferred"})
for s in (-1, 1):
    for k, (dd, hh) in enumerate(((-.38, 5.37),)):
        loft(hd, "HD_sideburn_%s" % ("R" if s < 0 else "L"), [[p + V((s * .90, dd, hh - .175)) for p in ring8(.065, -.06, .06, .02, 0, 0, 0)],
                                                              [p + V((s * .90, dd, hh + .175)) for p in ring8(.065, -.06, .06, .02, 0, 0, 0)]],
             lambda n, c: "HAIR_DARK", meta={"recipe": "sideburn .13 x .12 x .35", "class": "observed+prescribed"})

# ----------------------------------------------------------------------------------------------
# arms (sleeves, skin, cuffs) and hands
# ----------------------------------------------------------------------------------------------
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    S, E, W = JV[side + "Shoulder"], JV[side + "Elbow"], JV[side + "Wrist"]
    ax = Axis(S, E)
    ua = PM(side + "UpperArm", S)
    sleeve = [(0.0, .96, .90), (.50, .95, .885), (.74, .94, .87)]
    loft(ua, "UA_sleeve_" + side, [ax.ring(t, w, d, .08) for t, w, d in sleeve], sh_shirt,
         meta={"recipe": "short shirt sleeve t=0..0.74 (section 13)", "class": "observed+prescribed"})
    cuff = [ax.ring(.65, .945 + .05, .875 + .05, .08), ax.ring(.735, .945 + .05, .875 + .05, .08), ax.ring(.74, .95, .88, .08)]
    loft(ua, "UA_sleeve_hem_" + side, cuff, lambda n, c: "SHIRT_SHADOW", meta={"recipe": "sleeve hem band t=.65..74, +.025", "class": "observed+prescribed"})
    skin = [(.70, .82, .76), (1.0, .76, .71), (1.0 + .02 / ax.L, .76, .71)]
    loft(ua, "UA_skin_" + side, [ax.ring(t, w, d, .07) for t, w, d in skin], sh_skin_arm, meta={"recipe": "upper arm skin t=.7..1", "class": "observed+prescribed"})
    la = PM(side + "LowerArm", E)
    ax2 = Axis(E, W)
    lsec = [(-.02 / ax2.L, .75, .70), (0.0, .75, .70), (.48, .70, .66), (1.0, .63, .59), (1.0 + .02 / ax2.L, .63, .59)]
    loft(la, "LA_forearm_" + side, [ax2.ring(t, w, d, .035) for t, w, d in lsec], sh_skin_arm, meta={"recipe": "forearm taper .75x.70 -> .63x.59", "class": "observed+prescribed"})
    LA_AX = ax2


def tile_layer_set(bm, fn):
    tl = bm.faces.layers.int.get("tile") or bm.faces.layers.int.new("tile")
    for f in bm.faces:
        f.normal_update()
        cur = PAL[f[tl]][0]
        if cur in ("SKIN_SHADOW", "RECESS"):
            continue
        f[tl] = TILE[fn(f.normal.copy(), f.calc_center_median())]


def hand_build(side, s):
    W = JV[side + "Wrist"]
    pm = PM(side + "Hand", W)
    if side == "Right":
        # centre (-2.10,-.13,1.96), .70 x .64 x .68, bevel .055 (section 14)
        c = V((-2.10, -.13, 1.96)) - W
        base = box_solid(c.x - .35, c.x + .35, c.y - .32, c.y + .32, c.z - .34, c.z + .34, "SKIN", ch=.055)
        o = bm_to_obj(base, "tmp_hand")
        base.free()
        g = V((-2.20, -.25, 1.94)) - W
        chan = box_solid(c.x - .40, c.x + .40, g.y - .07, g.y + .07, g.z - .065, g.z + .065, "RECESS")
        slot = box_solid(c.x - .40, c.x + .40, c.y - .36, g.y - .0, g.z - .04, g.z + .04, "RECESS")
        thumb = box_solid(-1.81 - .07 - W.x, -1.81 + .07 - W.x, -.32 - .07 - W.y, -.32 + .07 - W.y, 1.97 - .115 - W.z, 1.97 + .115 - W.z, "SKIN", ch=.03)
        for nm, bmx, op in (("chan", chan, 'DIFFERENCE'), ("slot", slot, 'DIFFERENCE'), ("thumb", thumb, 'UNION')):
            co = bm_to_obj(bmx, "tmp_" + nm)
            bmx.free()
            bool_apply(o, co, op)
            bpy.data.objects.remove(co, do_unlink=True)
        for gh in (1.84, 1.95, 2.06):
            gz = gh - W.z
            gb = box_solid(c.x - .17, c.x + .17, c.y - .32 - .001, c.y - .32 + .008, gz - .006, gz + .006, "RECESS")
            co = bm_to_obj(gb, "tmp_g")
            gb.free()
            bool_apply(o, co, 'DIFFERENCE')
            bpy.data.objects.remove(co, do_unlink=True)
    else:
        c = V((2.10, -.13, 1.96)) - W
        base = box_solid(c.x - .35, c.x + .35, c.y - .32, c.y + .32, c.z - .34, c.z + .34, "SKIN", ch=.055)
        o = bm_to_obj(base, "tmp_hand")
        base.free()
        notch = box_solid(c.x - .075, c.x + .075, c.y - .33, c.y - .33 + .22, c.z - .35, c.z - .35 + .22, "RECESS")
        thumb = box_solid(c.x - .45, c.x - .30, c.y - .30, c.y - .08, c.z - .15, c.z + .08, "SKIN", ch=.03)
        for nm, bmx, op in (("notch", notch, 'DIFFERENCE'), ("thumb", thumb, 'UNION')):
            co = bm_to_obj(bmx, "tmp_" + nm)
            bmx.free()
            bool_apply(o, co, op)
            bpy.data.objects.remove(co, do_unlink=True)
    bm = obj_to_bm(o)
    bpy.data.objects.remove(o, do_unlink=True)
    bmesh.ops.translate(bm, vec=W, verts=bm.verts)
    tile_layer_set(bm, sh_skin_arm)
    pm.append_bm("HAND_" + side, bm, None, {"recipe": "block hand (section 14)", "class": "observed+prescribed",
                                          "note": "boolean EXACT: grip channel + slot + thumb + 3 grooves" if side == "Right" else "boolean EXACT: notch + thumb"})
    bm.free()


def bm_to_obj(bm, name, tile_default=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    ob = bpy.data.objects.new(name, me)
    SCENE.collection.objects.link(ob)
    return ob


hand_build("Right", -1)
hand_build("Left", 1)

# ----------------------------------------------------------------------------------------------
# legs + shoes
# ----------------------------------------------------------------------------------------------
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    hip, knee, ank = JV[side + "Hip"], JV[side + "Knee"], JV[side + "Ankle"]
    ul = PM(side + "UpperLeg", hip)
    axu = Axis(hip, knee)
    secs = UPPER_SEC + [(1.0 + .02 / axu.L,) + UPPER_SEC[-1][1:]]
    loft(ul, "UL_thigh_" + side, [axu.ring(t, w, d, .07) for t, w, d in secs], sh_trouser, meta={"recipe": "thigh 1.10x1.00 -> 1.02x.95", "class": "observed+prescribed"})
    # front crease (TROUSER_LIGHT line)
    cp = [V((s * .66, axu.at(t).y - sec_at(UPPER_SEC, t)[1] / 2 - .004, axu.at(t).z)) for t in (.05, .5, .98)]
    thin_polyline(ul, "UL_crease_" + side, cp, .02, .004, .01, sh_const("TROUSER_DARK"), meta={"recipe": "front crease (inferred)", "class": "inferred"})
    ll = PM(side + "LowerLeg", knee)
    axl = Axis(knee, ank)
    loft(ll, "LL_shin_" + side, [axl.ring(t, w, d, .065) for t, w, d in LOWER_SEC], sh_trouser, meta={"recipe": "shin 1.02x.95 -> 1.03x.98", "class": "observed+prescribed"})
    t0 = (knee.z - .61) / (knee.z - ank.z)
    t1 = (knee.z - .43) / (knee.z - ank.z)
    w1, d1 = sec_at(LOWER_SEC, 1.0)
    cuff = [axl.ring(t0, w1 + .02, d1 + .02, .065), axl.ring(t0 + .01, 1.10, 1.04, .07), axl.ring(t1 - .01, 1.10, 1.04, .07), axl.ring(t1, w1 + .02, d1 + .02, .065)]
    loft(ll, "LL_cuff_" + side, cuff, lambda n, c: "TROUSER_DARK" if n.z < -.5 else ("TROUSER_LIGHT" if n.z > .5 or n.y < -.5 else "TROUSER"),
         meta={"recipe": "trouser cuff H.43..61 1.10x1.04", "class": "observed+prescribed"})
    ft = PM(side + "Foot", ank)
    cx = s * .66
    cd = -.15
    rings = []
    for h, g in ((0.0, .02), (.02, 0.0), (.11, 0.0), (.13, .02)):
        rings.append(ring8(.61 - g, -.90 + g, .60 - g, .15, cx, 0, h))
    loft(ft, "FT_sole_" + side, rings, sh_const("SOLE"), meta={"recipe": "sole H0..13, 1.22 x 1.50, D-.90..+.60", "class": "observed+prescribed"})
    up = [ring8(.60, -.89, .58, .15, cx, 0, .13), ring8(.58, -.86, .56, .15, cx, 0, .30), ring8(.54, -.80, .50, .14, cx, 0, .43), ring8(.48, -.66, .42, .11, cx, 0, .47)]
    loft(ft, "FT_upper_" + side, up, sh_shoe, meta={"recipe": "dress shoe upper H.13..47", "class": "observed+prescribed"})
    pts = [V((cx + x, -.28 - .0, .36 + .0)) for x in (-.40, -.2, 0, .2, .40)]
        # heel block
    loft(ft, "FT_heel_" + side, [ring8(.50, .20, .60, .12, cx, 0, .0), ring8(.50, .20, .60, .12, cx, 0, .13)], sh_const("SOLE"), meta={"recipe": "heel block", "class": "inferred"})

# ----------------------------------------------------------------------------------------------
# briefcase (separate prop, rigid on the RightHand)
# ----------------------------------------------------------------------------------------------
bc = PM("Briefcase", CASE_O, geo="Briefcase_Geo")
O = CASE_O


def bx(u0, u1, v0, v1, w0, w1):
    return (O.x + u0, O.x + u1, O.y + v0, O.y + v1, O.z + w0, O.z + w1)


rings = cbox((O.x, O.y, O.z + .765), (1.76, .42, 1.53), .045)
loft(bc, "BC_body", rings, sh_case, meta={"recipe": "case body 1.76 x .42 x 1.53, bevel .045", "class": "observed+prescribed"})
for sv, nm in ((-1, "front"), (1, "back")):
    v0, v1 = (-.2375, -.2125) if sv < 0 else (.2125, .2375)
    solid_box(bc, "BC_panel_" + nm, *bx(-.83, .83, v0, v1, .05, 1.48), sh_const("CASE"), {"recipe": "raised panel 1.66 x 1.43, thickness .025", "class": "observed+prescribed"})
    solid_box(bc, "BC_panel_inset_" + nm, *bx(-.78, .78, v0 - (.012 if sv < 0 else 0), v1 + (0 if sv < 0 else .012), .10, 1.43), lambda n, c: "CASE_EDGE", {"recipe": "panel inner border", "class": "observed+prescribed"})
solid_box(bc, "BC_seam", *bx(-.885, .885, -.215, .215, .465, .485), sh_const("CASE_EDGE"), {"recipe": "lid seam strip .02", "class": "observed+prescribed"})
for ux in (-.55, .55):
    solid_box(bc, "BC_lock_%+.2f" % ux, *bx(ux - .07, ux + .07, -.28, -.245, 1.42, 1.52), lambda n, c: "BRASS_SHADOW" if n.z < -.4 else "BRASS", {"recipe": "brass lock .14 x .035 x .10", "class": "observed+prescribed"})
    solid_box(bc, "BC_lock_slot_%+.2f" % ux, *bx(ux - .0175, ux + .0175, -.2815, -.2695, 1.464, 1.476), sh_const("BRASS_SHADOW"), {"recipe": "lock keyhole", "class": "observed+prescribed"})
    solid_box(bc, "BC_foot_%+.2f" % ux, *bx(ux - .09, ux + .09, -.04, .04, -.0, .06), sh_const("CASE_EDGE"), {"recipe": "foot .18 x .08 x .06", "class": "observed+prescribed"})
    solid_box(bc, "BC_hinge_%+.2f" % ux, *bx(ux - .085, ux + .085, -.10, .10, 1.50, 1.545), sh_const("BRASS"), {"recipe": "plate .17 x .20 x .045", "class": "observed+prescribed"})
# handle: posts at u +/- .30, top bar at w=1.86, section .10 x .11, mounts .18 x .15 x .065
for ux in (-.30, .30):
    solid_box(bc, "BC_handle_post_%+.2f" % ux, *bx(ux - .055, ux + .055, -.05, .05, 1.53, 1.86), sh_const("CASE_EDGE"), {"recipe": "handle post .11 x .10", "class": "observed+prescribed"})
    solid_box(bc, "BC_handle_mount_%+.2f" % ux, *bx(ux - .09, ux + .09, -.075, .075, 1.50, 1.565), sh_const("CASE_SIDE"), {"recipe": "handle mount .18 x .15 x .065", "class": "observed+prescribed"})
solid_box(bc, "BC_handle_bar", *bx(-.355, .355, -.05, .05, 1.805, 1.915), sh_const("CASE_EDGE"), {"recipe": "handle top bar section .10 x .11, centre w1.86", "class": "observed+prescribed"})


# ----------------------------------------------------------------------------------------------
# materials / UV / vertex colors / mesh objects
# ----------------------------------------------------------------------------------------------
atlas = bpy.data.images.new("OfficeDad_Palette", ATLAS_W, ATLAS_H, alpha=False)
atlas.colorspace_settings.name = 'sRGB'   # must be set BEFORE writing pixels
px = [0.0] * (ATLAS_W * ATLAS_H * 4)
fill = hex_rgb(_H["SHIRT"])
for ty in range(ATLAS_H):
    for tx in range(ATLAS_W):
        idx = (ty // TILE_PX) * COLS + (tx // TILE_PX)
        rgb = hex_rgb(PAL[idx][1]) if idx < len(PAL) else fill
        r, g, b = (c / 255.0 for c in rgb)
        o = ((ATLAS_H - 1 - ty) * ATLAS_W + tx) * 4
        px[o:o + 4] = [r, g, b, 1.0]
atlas.pixels.foreach_set(px)
atlas.filepath_raw = os.path.join(OUT, "OfficeDad_Palette.png")
atlas.file_format = 'PNG'
atlas.save()
atlas.pack()

MATP = bpy.data.materials.new("OfficeDad_Palette")
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
# armature (standard-compatible hierarchy) + rigid 100% weights
# ----------------------------------------------------------------------------------------------
arm_data = bpy.data.armatures.new("OfficeDad_Armature")
ARM_OB = bpy.data.objects.new("OfficeDad_Armature", arm_data)
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
    s = -1 if side == "Right" else 1
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
    bone = "RightHand" if pm.runtime == "Briefcase" else pm.runtime
    ob = pm.obj
    vg = ob.vertex_groups.new(name=bone)
    vg.add([v.index for v in ob.data.vertices], 1.0, 'REPLACE')
    md = ob.modifiers.new("Armature", 'ARMATURE')
    md.object = ARM_OB
    ob.parent = ARM_OB
    ob.matrix_parent_inverse = Matrix.Identity(4)
case_ob = PARTS["Briefcase"].obj

PB = ARM_OB.pose.bones


def bone_rest(name):
    return ARM_OB.data.bones[name].matrix_local.copy()


def clear_pose():
    for pb in PB:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion((1, 0, 0, 0))
        pb.location = V((0, 0, 0))
        pb.scale = V((1, 1, 1))
    bpy.context.view_layer.update()


def rot3(axis, deg):
    return Matrix.Rotation(math.radians(deg), 3, axis)


def parent_eff(name):
    par = ARM_OB.data.bones[name].parent
    if par is None:
        return Matrix.Identity(4)
    return PB[par.name].matrix @ bone_rest(par.name).inverted()


def fk(name, R3):
    pb = PB[name]
    rest = bone_rest(name)
    pe = parent_eff(name)
    head = pe @ rest.translation
    pb.matrix = Matrix.Translation(head) @ R3.to_4x4() @ Matrix.Translation(-head) @ pe @ rest
    bpy.context.view_layer.update()


def apply_reference_pose():
    """Display pose of the crop: head yaw +6, roll 1.5 about the neck pivot; everything else neutral."""
    clear_pose()
    fk("Head", rot3('Z', 6.0) @ rot3('Y', 1.5))


# ----------------------------------------------------------------------------------------------
# cameras / light / render helpers
# ----------------------------------------------------------------------------------------------
world = bpy.data.worlds.new("OD_World")
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
sun_d = bpy.data.lights.new("OD_Key", 'SUN')
sun_d.energy = 1.8
sun = bpy.data.objects.new("OD_Key", sun_d)
SCENE.collection.objects.link(sun)
sun.rotation_euler = (math.radians(52), math.radians(8), math.radians(-38))
fill_d = bpy.data.lights.new("OD_Fill", 'SUN')
fill_d.energy = 0.55
fill_d.use_shadow = False
fill = bpy.data.objects.new("OD_Fill", fill_d)
SCENE.collection.objects.link(fill)
fill.rotation_euler = (math.radians(60), 0, math.radians(140))
cam_d = bpy.data.cameras.new("OD_Cam")
CAM = bpy.data.objects.new("OD_Cam", cam_d)
SCENE.collection.objects.link(CAM)
SCENE.camera = CAM
SCENE.render.engine = 'BLENDER_EEVEE'
SCENE.eevee.taa_render_samples = 8 if QUICK else 32
SCENE.render.image_settings.file_format = 'PNG'
SCENE.view_settings.view_transform = 'Standard'
SCENE.render.film_transparent = False


def cam_look(loc, target, lens=70.0):
    CAM.location = V(loc)
    CAM.rotation_euler = (V(target) - V(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.type, cam_d.lens, cam_d.sensor_width = 'PERSP', lens, 36.0


def orbit(target, dist, az_deg, el_deg):
    az, el = math.radians(az_deg), math.radians(el_deg)
    t = V(target)
    return t + V((dist * math.sin(az) * math.cos(el), -dist * math.cos(az) * math.cos(el), dist * math.sin(el)))


RENDERED = []


def shot(name, loc, target, res=(1000, 1000), lens=70.0, show_only=None):
    for pm in PARTS.values():
        pm.obj.hide_render = (show_only is not None and pm.runtime not in show_only)
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


def key_pose(action_name):
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
key_pose("OfficeDad_NeutralBind")
apply_reference_pose()
key_pose("OfficeDad_ReferencePose")
clear_pose()
BODY = [PARTS[k].obj for k in PARTS if k != "Briefcase"]
lo, hi = world_bounds(BODY)
head_lo, head_hi = world_bounds([PARTS["Head"].obj])
ft_lo, _ = world_bounds([PARTS["RightFoot"].obj, PARTS["LeftFoot"].obj])
case_lo, case_hi = world_bounds([case_ob])
body_tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in BODY)
case_tris = sum(len(p.vertices) - 2 for p in case_ob.data.polygons)
print("BOUNDS body", tuple(round(x, 3) for x in lo), tuple(round(x, 3) for x in hi), "case", tuple(round(x, 3) for x in case_lo), tuple(round(x, 3) for x in case_hi))
print("HEAD", tuple(round(x, 3) for x in head_lo), tuple(round(x, 3) for x in head_hi), "FEET", round(ft_lo.z, 4))
print("TRIS body", body_tris, "case", case_tris)

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


# briefcase vs body: exact overlaps (hand grip channel is meant to touch the handle bar only)
CASE_CHECK = {}
ct, cpts = bvh_of(case_ob)
for n in ("RightHand", "RightLowerArm", "RightUpperLeg", "RightLowerLeg", "LeftHand", "LowerTorso", "UpperTorso", "RightFoot"):
    t, pts = bvh_of(PARTS[n].obj)
    CASE_CHECK[n] = {"overlapping_triangle_pairs": len(ct.overlap(t)), "min_distance": round(min((t.find_nearest(p)[3] or 9e9) for p in cpts), 4)}
print("CASECHECK", json.dumps(CASE_CHECK))

# ----------------------------------------------------------------------------------------------
# outputs: blend, FBX, spec JSON
# ----------------------------------------------------------------------------------------------
os.makedirs(os.path.join(OUT, "export"), exist_ok=True)
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
os.makedirs(os.path.join(OUT, "source"), exist_ok=True)
BLEND = os.path.join(OUT, "source", "OfficeDad_Redesign.blend")
FBX_BODY = os.path.join(OUT, "export", "OfficeDad_R15.fbx")
FBX_CASE = os.path.join(OUT, "export", "OfficeDad_Briefcase.fbx")
FBX_SET = dict(use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y',
               mesh_smooth_type='FACE', use_mesh_modifiers=True, bake_anim=False, add_leaf_bones=False,
               path_mode='COPY', embed_textures=True, use_armature_deform_only=False, primary_bone_axis='Y', secondary_bone_axis='X')


def export_fbx(path, objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, object_types={'MESH', 'ARMATURE'}, **FBX_SET)


clear_pose()
for pm in PARTS.values():
    pm.obj.hide_render = False
export_fbx(FBX_BODY, [ARM_OB] + BODY)
cp = bpy.data.objects.new("Briefcase_Geo", case_ob.data.copy())
cp.data.name = "Briefcase_Geo_export"
EXP_COLL.objects.link(cp)
cp.location = CASE_O
export_fbx(FBX_CASE, [cp])
bpy.data.objects.remove(cp, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("EXPORTED", FBX_BODY, FBX_CASE, BLEND)

uvmap = {"atlas": "OfficeDad_Palette.png", "size": [ATLAS_W, ATLAS_H], "tile_px": TILE_PX, "columns": COLS, "inset_px": INSET,
         "row0_is_top_of_png": True, "tiles": []}
for i, (n_, h_, use) in enumerate(PAL):
    u0, v0, u1, v1 = tile_uv_patch(i)
    uvmap["tiles"].append({"index": i, "name": n_, "hex": h_, "use": use, "col": i % COLS, "row": i // COLS, "uv_patch": [u0, v0, u1, v1]})
json.dump(uvmap, open(os.path.join(OUT, "data", "palette_uv_map.json"), "w"), indent=1)


def r3(v):
    return [round(float(c), 4) for c in v]


def roblox_pos(p):
    return [round(-p[0], 4), round(p[2], 4), round(p[1], 4)]


RESULT = {"bounds_neutral": {"min": r3(lo), "max": r3(hi), "height": round(hi.z - lo.z, 4)}, "head_bounds": {"min": r3(head_lo), "max": r3(head_hi)},
          "case_bounds": {"min": r3(case_lo), "max": r3(case_hi)}, "feet_min_h": round(ft_lo.z, 5), "tris_body": body_tris, "tris_case": case_tris,
          "audit": AUDIT, "case_vs_body": CASE_CHECK}
json.dump(RESULT, open(os.path.join(OUT, "data", "_build_result.json"), "w"), indent=1)
SPEC = {"asset": "OfficeDad_Redesign", "character": "Office Dad (02, Common)", "units": "studs", "neutral_height": 6.40, "built_height": RESULT["bounds_neutral"]["height"],
        "tables": {"UpperTorso": UT_ROWS, "LowerTorso": LT_ROWS, "Head": HEAD_ROWS, "Nose": NOSE_ROWS}, "joints": {k: list(v) for k, v in JOINTS.items()},
        "grip_world": r3(GRIP), "case_origin": r3(CASE_O), "palette": [{"index": i, "name": n_, "hex": h_, "use": u_} for i, (n_, h_, u_) in enumerate(PAL)],
        "counts": {"body_tris": body_tris, "case_tris": case_tris},
        "deviations_from_prompt": [
            "PDF text layer lost all Russian text and one hex digit: BRASS #D 8A134 was read as #D8A134; sections were interpreted from numbers and the crop image.",
            "Head loft rows are chosen to match the prescribed W1.80/D1.34/H1.73 box, jaw 1.61 (the rows are not tabulated in the prompt).",
            "Hair top blocks are chamfered blocks centred on the section-22 polyline points; scalp mass is a closed loft H5.83..6.19.",
            "Glasses have no lens geometry (open rims); temple arms are simple two-block arms.",
            "Hand grip: rectangular channel .14 x .13 through the hand along X plus a front slot, three finger grooves; thumb block at X-1.81.",
            "Shoe toe-out is 0 (the toe-out line of section 12 is unreadable)."],
        "measured": RESULT}
json.dump(SPEC, open(os.path.join(OUT, "data", "construction_spec.json"), "w"), indent=1)
json.dump({"asset": "OfficeDad_Redesign", "components": COMP_LOG,
           "part_totals": {k: {"components": len(v.comps), "tris": AUDIT[k]["tris"], "verts": AUDIT[k]["verts"]} for k, v in PARTS.items()},
           "mesh_names": {k: v.geo for k, v in PARTS.items()}}, open(os.path.join(OUT, "data", "component_registry.json"), "w"), indent=1)
RIG = {"asset": "OfficeDad_Redesign", "frame": {"logical": "(X,D,H) forward=-D, anatomical RIGHT=-X", "roblox_position": "(-X, H, D)"},
       "bones": [{"name": n, "parent": p, "head_logical": r3(h), "tail_logical": r3(t), "head_roblox": roblox_pos(h)} for n, p, h, t in BONES],
       "briefcase": {"weight": "RightHand 100%", "grip_world": r3(GRIP), "case_origin": r3(CASE_O), "route": "one WeldConstraint BriefcaseGrip RightHand->Briefcase in Studio"},
       "weights": "100% own bone (rigid style)", "display_pose": {"head_yaw_deg": 6.0, "head_roll_deg": 1.5}}
json.dump(RIG, open(os.path.join(OUT, "data", "rig_manifest.json"), "w"), indent=1)
print("RESULT", json.dumps({k: RESULT[k] for k in ("bounds_neutral", "tris_body", "tris_case")}))
if NORENDER:
    sys.exit(0)

# ----------------------------------------------------------------------------------------------
# renders (section 26)
# ----------------------------------------------------------------------------------------------
apply_reference_pose()
T = V((0, -.10, 3.18))
shot("01_matching_front34.png", (-7.0, -15.0, 7.0), T, res=(327 * 2, 370 * 2), lens=70)
shot("01b_native_327x370.png", (-7.0, -15.0, 7.0), T, res=(327, 370), lens=70)
shot("02_front.png", orbit(T, 18, 0, 4), T, res=(900, 1000))
shot("03_back.png", orbit(T, 18, 180, 4), T, res=(900, 1000))
shot("04_right_profile.png", orbit(T, 18, -90, 4), T, res=(900, 1000))
shot("05_left_profile.png", orbit(T, 18, 90, 4), T, res=(900, 1000))
shot("06_back_right34.png", orbit(T, 18, -150, 10), T, res=(900, 1000))
HT = V((0, -.2, 5.3))
shot("07_head_front.png", orbit(HT, 6.0, 0, 2), HT, res=(900, 900))
shot("08_head_right_profile.png", orbit(HT, 6.0, -90, 2), HT, res=(900, 900))
shot("08b_head_34.png", orbit(HT, 6.0, -30, 8), HT, res=(900, 900))
CT = V((0.2, -.7, 3.7))
shot("09_collar_tie_pocket.png", orbit(CT, 4.5, 8, 6), CT, res=(900, 900))
shot("10_right_arm_side.png", orbit(V((-1.9, -.1, 2.7)), 7, -90, 5), V((-1.9, -.1, 2.7)), res=(900, 1000))
GT = V((-2.15, -.2, 2.0))
shot("11_grip_front.png", orbit(GT, 3.5, 0, 6), GT, res=(900, 900))
shot("11b_grip_side.png", orbit(GT, 3.5, -90, 6), GT, res=(900, 900))
shot("11c_grip_top.png", orbit(GT, 3.5, 0, 80), GT, res=(900, 900))
CC = V((-2.2, -.25, .85))
shot("12_case_front.png", orbit(CC, 5.0, 0, 4), CC, res=(900, 900), show_only=("Briefcase",))
shot("13_case_side.png", orbit(CC, 5.0, -90, 4), CC, res=(900, 900), show_only=("Briefcase",))
shot("14_case_top.png", orbit(CC, 5.0, 0, 85), CC, res=(900, 900), show_only=("Briefcase",))
shot("15_case_back_bottom.png", orbit(CC, 5.0, 180, -35), CC, res=(900, 900), show_only=("Briefcase",))
BK = V((0, -.5, 2.4))
shot("16_buckle.png", orbit(BK, 3.5, 0, 6), BK, res=(900, 700))
SH = V((0, -.2, .5))
shot("16b_shoes.png", orbit(SH, 6.0, 25, 14), SH, res=(1000, 700))
shot("17_gate_full_256.png", (-7.0, -15.0, 7.0), T, res=(256, 256), lens=70)
print("ALL_RENDERS_DONE", len(RENDERED))
