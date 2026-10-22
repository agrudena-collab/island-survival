"""Export the whole Regular Dad house scene for Roblox (FBX chunks + palette atlas).

Run: blender -b --factory-startup --python export_roblox.py -- <out_dir>
 - builds the scene with the builder (same coordinates as the renders: Blender X, Y=-z, Z=height, studs)
 - every material is replaced by one flat colour cell of a palette atlas (procedural textures cannot be exported)
 - glass / neon pieces go to their own chunks (named G_ / N_) so Studio can set Transparency / Neon after import
 - geometry is split into spatial chunks of <= MAXT triangles (MeshPart upload limit) and written as several FBX files
"""
import os
import sys
import math

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else os.path.join(HERE, 'roblox_export')
MAXT = int(os.environ.get('RDH_MAXT', '9000'))
CELL = float(os.environ.get('RDH_CELL', '30'))
os.makedirs(OUT, exist_ok=True)

src = open(os.path.join(HERE, 'build_house_v5.py'), encoding='utf-8').read().rstrip()
assert src.endswith('main()')
src = src[:-len('main()')]
sys.argv = [sys.argv[0], '--', os.path.join(HERE, 'audit_tmp')]
ns = {'__name__': 'rbx_export', '__file__': os.path.join(HERE, 'build_house_v5.py')}
exec(compile(src, 'build_house_v5.py', 'exec'), ns)

import bpy
import bmesh
from mathutils import Vector

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
ns['setup_scene']()
ns['build']()
acc, mats, P = ns['acc'], ns['mats'], ns['P']
warp_v = ns['warp_v']

# ---- material -> base colour
inv = {m: k for k, m in mats.items()}


def base_hex(m):
    name, hexcol = inv[m]
    return hexcol or P[name]


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ---- atlas: 16x16 cells of 64 px
cols = {}
for (c, m) in acc:
    cols.setdefault(m, base_hex(m))
cells = {}
order = sorted(set(cols.values()))
for i, h in enumerate(order):
    cells[h] = i
N = 16
W = 1024
img = bpy.data.images.new('RDH_Atlas', W, W, alpha=False)
px = [0.0] * (W * W * 4)
for h, i in cells.items():
    cx, cy = i % N, i // N
    r, g, b = [v / 255.0 for v in rgb(h)]
    # sRGB -> linear is applied by Blender on save; store already linear so the PNG keeps the displayed colour
    for y in range(cy * 64, cy * 64 + 64):
        for x in range(cx * 64, cx * 64 + 64):
            k = (y * W + x) * 4
            px[k], px[k + 1], px[k + 2], px[k + 3] = r, g, b, 1.0
img.pixels = px
img.filepath_raw = os.path.join(OUT, 'RDH_Atlas.png')
img.file_format = 'PNG'
img.save()
amat = bpy.data.materials.new('RDH_Atlas')
amat.use_nodes = True
nt = amat.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL':
        nt.nodes.remove(n)
out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
tex = nt.nodes.new('ShaderNodeTexImage')
tex.image = img
tex.interpolation = 'Closest'
nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])


def lin(h):
    r, g, b = [v / 255.0 for v in rgb(h)]
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b), 1.0)


def kind_of(m):
    name = inv[m][0]
    if name == 'glass':
        return 'G'
    if name in ('lamp',):
        return 'N'
    return 'O'


# ---- collect connected components per (collection, material) and chunk them spatially (vertices stay shared)
GROUP = {'Site': 'Arch', 'Yard': 'Arch', 'Ground': 'Arch', 'Upper': 'Arch', 'Roof': 'Arch', 'Lamps': 'Arch', 'Lamps_U': 'Arch',
         'Furn_G': 'FurnG', 'Furn_U': 'FurnU', 'Furn_Y': 'FurnY'}
chunks = {}   # (group, kind, cx, cz) -> list of components (verts, faces, hex, tris)


def components(nv, fs):
    par = list(range(nv))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for f in fs:
        r0 = find(f[0])
        for i in f[1:]:
            ri = find(i)
            if ri != r0:
                par[ri] = r0
    comp = {}
    for fi, f in enumerate(fs):
        comp.setdefault(find(f[0]), []).append(fi)
    return list(comp.values())


allc = []   # every primitive (connected component) with its collection/material
for (c, m), (vs, fs) in acc.items():
    grp = GROUP.get(c, 'Arch')
    kd = kind_of(m)
    hexc = cols[m]
    wv = [warp_v(v, c) if not c.startswith('Furn') else v for v in vs]
    for fl in components(len(vs), fs):
        remap, verts, faces = {}, [], []
        tris = 0
        for fi in fl:
            f = fs[fi]
            nf = []
            for i in f:
                if i not in remap:
                    remap[i] = len(verts)
                    verts.append(list(wv[i]))
                nf.append(remap[i])
            faces.append(tuple(nf))
            tris += len(f) - 2
        allc.append(dict(grp=grp, kd=kd, hex=hexc, verts=verts, faces=faces, tris=tris))

# ---- layering fix: axis-aligned faces of two different primitives lying in the same plane, same direction and overlapping (z-fighting)
# the smaller one (inlay: mirror in a frame, drawer front, picture panel...) is lifted by EPS along the face normal
EPS = 0.02
buckets = {}
for ci, cp in enumerate(allc):
    vv = cp['verts']
    for f in cp['faces']:
        pts = [vv[i] for i in f]
        if len(pts) < 3:
            continue
        ax = None
        for k in range(3):
            lo = min(p[k] for p in pts)
            hi = max(p[k] for p in pts)
            if hi - lo < 1e-4:
                ax = k
                break
        if ax is None:
            continue
        # outward direction from the primitive centre
        ctr = sum(p[ax] for p in vv) / len(vv)
        sign = 1 if pts[0][ax] >= ctr else -1
        o = [k for k in range(3) if k != ax]
        r = (min(p[o[0]] for p in pts), max(p[o[0]] for p in pts), min(p[o[1]] for p in pts), max(p[o[1]] for p in pts))
        buckets.setdefault((ax, sign, round(pts[0][ax] / 0.01)), []).append((ci, r))
nudge = {}
found = 0
for key, lst in buckets.items():
    if len(lst) < 2:
        continue
    ax, sign = key[0], key[1]
    for i in range(len(lst)):
        ci, ri = lst[i]
        for j in range(i + 1, len(lst)):
            cj, rj = lst[j]
            if ci == cj:
                continue
            ou = min(ri[1], rj[1]) - max(ri[0], rj[0])
            ov = min(ri[3], rj[3]) - max(ri[2], rj[2])
            if ou > 0.02 and ov > 0.02:
                found += 1
                ai = (ri[1] - ri[0]) * (ri[3] - ri[2])
                aj = (rj[1] - rj[0]) * (rj[3] - rj[2])
                small = ci if ai < aj else cj if aj < ai else max(ci, cj)
                nd = nudge.setdefault(small, [0.0, 0.0, 0.0])
                nd[ax] = max(-0.04, min(0.04, nd[ax] + sign * EPS)) if abs(nd[ax]) < 0.04 else nd[ax]
for ci, nd in nudge.items():
    for v in allc[ci]['verts']:
        v[0] += nd[0]
        v[1] += nd[1]
        v[2] += nd[2]
print('LAYER_FIX coplanar pairs', found, 'primitives lifted', len(nudge))

chunks = {}
for cp in allc:
    cen = Vector((0, 0, 0))
    for v in cp['verts']:
        cen += Vector(v)
    cen /= len(cp['verts'])
    key = (cp['grp'], cp['kd'], int(math.floor(cen.x / CELL)), int(math.floor(cen.y / CELL)))
    chunks.setdefault(key, []).append(([tuple(v) for v in cp['verts']], cp['faces'], cp['hex'], cp['tris']))

files = {}
count = 0
for key in sorted(chunks):
    grp, kd, cx, cy = key
    parts, cur, t = [], [], 0
    for comp in chunks[key]:
        if t + comp[3] > MAXT and cur:
            parts.append(cur)
            cur, t = [], 0
        cur.append(comp)
        t += comp[3]
    if cur:
        parts.append(cur)
    for pi, part in enumerate(parts):
        count += 1
        name = '%s_%s_%d_%d_%d' % (kd, grp, cx, cy, pi)
        verts, polys, pcols = [], [], []
        for (cv, cf, hexc, tr) in part:
            base = len(verts)
            verts.extend(cv)
            for f in cf:
                polys.append(tuple(base + i for i in f))
                pcols.append(lin(hexc))
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts, [], polys)
        me.update()
        ca = me.color_attributes.new(name='Col', type='BYTE_COLOR', domain='CORNER')
        li = 0
        for pidx, p in enumerate(me.polygons):
            c4 = pcols[pidx]
            for _ in range(p.loop_total):
                ca.data[li].color = c4
                li += 1
        ns['finish_mesh'](me)
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        files.setdefault(grp, []).append(ob)
        ob.location = (0, 0, 0)

print('chunks', count, {g: len(v) for g, v in files.items()})
FBX_SET = dict(use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y',
               mesh_smooth_type='EDGE', use_mesh_modifiers=False, bake_anim=False, add_leaf_bones=False,
               path_mode='AUTO', embed_textures=False, object_types={'MESH'}, colors_type='SRGB')
stats = {}
allobs = [o for obs in files.values() for o in obs]
bpy.ops.object.select_all(action='DESELECT')
for o in allobs:
    o.select_set(True)
bpy.context.view_layer.objects.active = allobs[0]
fn = os.path.join(OUT, 'RDH_House_VertexColor.fbx')
bpy.ops.export_scene.fbx(filepath=fn, **FBX_SET)
stats['RDH_House_VertexColor.fbx'] = {'meshes': len(allobs), 'tris': sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in allobs)}
import json
json.dump(stats, open(os.path.join(OUT, 'export_stats.json'), 'w'), indent=1)
print('EXPORT DONE', json.dumps(stats))
