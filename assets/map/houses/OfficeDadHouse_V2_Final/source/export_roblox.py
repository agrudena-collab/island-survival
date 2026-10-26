"""Export OfficeDadHouse_V2_Final for Roblox: vertex-colour FBX chunks (<= 9000 triangles each) + data JSON.

Run:  python -I export_roblox.py <out_dir>        (Blender as the pip module bpy, same pipeline as the Regular Dad house)
  <out>/export/OfficeDadHouse_V2_Final.fbx   house + lot + furniture (groups Arch / FurnG / FurnU)
  <out>/export/OfficeDadBiome_V2.fbx         biome (streets, empty neighbour houses, supermarket, bank) + the father's car parked on the driveway
  <out>/data/*.json                          doors, anchors, cover, routes, collision boxes, yard colliders
Geometry of the door leaves and the father proxy is NOT exported (leaves are rebuilt in Studio, the father is OfficeDad_Final).
"""
import os
import sys
import json
import math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'out')
SC = float(os.environ.get('ODH_SCALE', '1.275'))      # uniform world scale: the whole lot, biome and car are made SC times bigger for Roblox characters
KC = float(os.environ.get('ODH_CAR_EXTRA', '1.0'))  # extra scale of the car (roomy cabin), on top of SC
MAXT = int(os.environ.get('ODH_MAXT', '9000'))
CELL = float(os.environ.get('ODH_CELL', '30'))
CELL_HOUSE = float(os.environ.get('ODH_CELL_HOUSE', '18'))
for sub in ('export', 'data'):
    os.makedirs(os.path.join(OUT, sub), exist_ok=True)

import bpy
import odh_core as K
import odh_scene as S
import build_odh as BO
from odh_core import P, GLASS_COLORS, NEON_COLORS, hexrgb
from mathutils import Vector

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
BO.build()
acc = K.acc

SKIP = ('DoorLeaf', 'DoorLeafU', 'FatherProxy', 'PassProxy', 'DadCar')
GROUP = {'Car': 'Car', 'Site': 'Arch', 'Ground': 'Arch', 'Upper': 'Arch', 'Roof': 'Arch', 'Furn_G': 'FurnG', 'Furn_U': 'FurnU', 'Biome': 'Biome', 'BiomeOrg': 'Biome', 'DadCar': 'Car'}


def hx(name):
    return P[name] if name in P else name


def lin(h):
    r, g, b = hexrgb(h)
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b), 1.0)


def kind_of(m):
    return 'G' if m in GLASS_COLORS else 'N' if m in NEON_COLORS else 'O'


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


# the father's car is a separate model: rebuilt at the origin (car-local frame, nose to +z of the plot frame), no work pass geometry
import odh_car as CAR
_stash = dict(acc)
acc.clear()
import odh_site as _ST
CAR.dad_car('Car', pass_on_dash=False, sc=_ST.CAR_SC)
_car = dict(acc)
acc.clear()
acc.update(_stash)
acc.update(_car)
allc = []
for (c, m), (vs, fs) in acc.items():
    if c in SKIP or not fs:
        continue
    grp = GROUP.get(c, 'Arch')
    for fl in components(len(vs), fs):
        remap, verts, faces, tris = {}, [], [], 0
        for fi in fl:
            f = fs[fi]
            nf = []
            for i in f:
                if i not in remap:
                    remap[i] = len(verts)
                    verts.append(list(vs[i]))
                nf.append(remap[i])
            faces.append(tuple(nf))
            tris += len(f) - 2
        allc.append(dict(grp=grp, kd=kind_of(m), hex=hx(m), verts=verts, faces=faces, tris=tris))

# ---- layer cleanup: coplanar overlapping faces are cut out of the larger one, neighbours glued, vertices welded (odh_merge)
import odh_merge as MG
for cp in allc:
    cp['polys'] = [tuple(tuple(cp['verts'][i]) for i in f) for f in cp['faces']]
before = MG.count_layers(allc)
pairs, removed, cutn = MG.resolve(allc)
glued = MG.glue(allc)
after = MG.count_layers(allc)
for cp in allc:
    cp['verts'], cp['faces'] = MG.weld(cp)
    cp['tris'] = sum(len(f) - 2 for f in cp['faces'])
allc = [cp for cp in allc if cp['faces']]
print('LAYER_CLEANUP overlapping coplanar pairs before', before, 'after', after, 'faces removed', removed, 'cut', cutn, 'glued', glued)

# ---- spatial chunks <= MAXT triangles
chunks = {}
for cp in allc:
    cen = Vector((0, 0, 0))
    for v in cp['verts']:
        cen += Vector(v)
    cen /= len(cp['verts'])
    cl_ = CELL if cp['grp'] == 'Biome' else 1000.0 if cp['grp'] == 'Car' else CELL_HOUSE
    key = (cp['grp'], cp['kd'], int(math.floor(cen.x / cl_)), int(math.floor(cen.y / cl_)))
    chunks.setdefault(key, []).append(([tuple(v) for v in cp['verts']], cp['faces'], cp['hex'], cp['tris']))

objs = {'house': [], 'biome': [], 'car': []}
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
        if grp == 'Car':      # car joins the biome file, parked on the driveway (plot x 12.5, z 34, turned 180 deg)
            verts = [(SC * (-x * KC + 12.5), SC * (-y * KC - 34.0), SC * z * KC) for (x, y, z) in verts]
        else:
            verts = [(SC * x, SC * y, SC * z) for (x, y, z) in verts]
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts, [], polys)
        me.update()
        ca = me.color_attributes.new(name='Col', type='BYTE_COLOR', domain='CORNER')
        li = 0
        for pidx, p in enumerate(me.polygons):
            for _ in range(p.loop_total):
                ca.data[li].color = pcols[pidx]
                li += 1
        K.finish_mesh(me)
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        objs['biome' if grp in ('Biome', 'Car') else 'house'].append(ob)

FBX_SET = dict(use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y',
               mesh_smooth_type='EDGE', use_mesh_modifiers=False, bake_anim=False, add_leaf_bones=False,
               path_mode='AUTO', embed_textures=False, object_types={'MESH'}, colors_type='SRGB')
stats = {}
for key, fname in (('house', 'OfficeDadHouse_V2_Final.fbx'), ('biome', 'OfficeDadBiome_V2.fbx')):
    obs = objs[key]
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'export', fname), **FBX_SET)
    tr = [sum(len(p.vertices) - 2 for p in o.data.polygons) for o in obs]
    stats[fname] = {'meshes': len(obs), 'triangles': sum(tr), 'max_triangles_per_mesh': max(tr),
                    'glass_chunks': sum(1 for o in obs if o.name.startswith('G_')), 'neon_chunks': sum(1 for o in obs if o.name.startswith('N_'))}
stats['layer_cleanup'] = {'coplanar_overlaps_before': before, 'coplanar_overlaps_after': after, 'faces_removed': removed, 'faces_cut': cutn, 'faces_glued': glued}
print('FBX', json.dumps(stats))


# ---- collision: merge coplanar-neighbour boxes of the same coll group
def merge_boxes(boxes):
    boxes = [list(b) for b in boxes]
    changed = True
    while changed:
        changed = False
        boxes.sort(key=lambda b: (b[0], b[3], b[4], b[1], b[2]))
        out = []
        used = [False] * len(boxes)
        for i, a in enumerate(boxes):
            if used[i]:
                continue
            for j in range(i + 1, len(boxes)):
                if used[j]:
                    continue
                b = boxes[j]
                # a, b = [x0, x1, h0, h1, z0, z1]
                for ax in (0, 2, 4):
                    oth = [k for k in (0, 2, 4) if k != ax]
                    if all(abs(a[k] - b[k]) < 1e-3 and abs(a[k + 1] - b[k + 1]) < 1e-3 for k in oth):
                        if abs(a[ax + 1] - b[ax]) < 1e-3 or abs(b[ax + 1] - a[ax]) < 1e-3 or (a[ax] <= b[ax] + 1e-3 and b[ax + 1] <= a[ax + 1] + 1e-3) \
                                or (b[ax] <= a[ax] + 1e-3 and a[ax + 1] <= b[ax + 1] + 1e-3) or (min(a[ax + 1], b[ax + 1]) > max(a[ax], b[ax])):
                            a[ax] = min(a[ax], b[ax])
                            a[ax + 1] = max(a[ax + 1], b[ax + 1])
                            used[j] = True
                            changed = True
                            break
            out.append(a)
        boxes = out
    return boxes


by = {}
for (coll, color, x0, x1, h0, h1, z0, z1) in K.BOXLOG:
    if coll in SKIP:
        continue
    key = 'biome' if coll == 'Biome' else 'house'
    if x1 - x0 < 0.05 or z1 - z0 < 0.05 or h1 - h0 < 0.05:
        continue
    by.setdefault(key, []).append(tuple(SC * v for v in (x0, x1, h0, h1, z0, z1)))
cbx = [('cbox', *t) for t in []]
col = {k: merge_boxes(v) for k, v in by.items()}
print('COLLISION boxes', {k: (len(by[k]), len(v)) for k, v in col.items()})

import math as _m


def door_geometry(d):
    """closed leaf centre / size, hinge point and the Roblox OpenAngle (degrees, rotation about +Y) derived from the Blender swing convention"""
    w, h, t = d['w'], d['h'] - 0.15, 0.45
    y = d['y0'] + 0.05 + h / 2
    s = 1 if d['swing'] >= 0 else -1
    ang = 100.0 if d['kind'] == 'hide' else (100.0 if d['kind'] in ('front', 'back', 'service', 'balcony') else 95.0)
    lo = d['hinge'] == 'low'
    if d['axis'] == 'x':
        hx_ = d['ctr'] - w / 2 if lo else d['ctr'] + w / 2
        hinge = [hx_, y, d['wall']]
        centre = [d['ctr'], y, d['wall']]
        size = [w - 0.1, h, t]
        theta = -s * ang if lo else s * ang
    else:
        hz_ = d['ctr'] - w / 2 if lo else d['ctr'] + w / 2
        hinge = [d['wall'], y, hz_]
        centre = [d['wall'], y, d['ctr']]
        size = [t, h, w - 0.1]
        theta = s * ang if lo else -s * ang
    return dict(hinge=hinge, centre=centre, size=size, open_deg=theta)


doors = []
for d in K.DOORLOG:
    dd = {k: (list(v) if isinstance(v, tuple) else v) for k, v in d.items()}
    g = door_geometry(d)
    dd['hinge_side'] = d['hinge']
    dd['hinge_pt'] = [v * SC for v in g['hinge']]
    dd['centre'] = [v * SC for v in g['centre']]
    dd['size'] = [v * SC for v in g['size']]
    dd['open_deg'] = g['open_deg']
    for k in ('ctr', 'w', 'y0', 'h', 'wall'):
        dd[k] = dd[k] * SC
    del dd['hinge']
    doors.append(dd)
def _anch(k, v):
    x, h, z = v[0], v[1], v[2]
    if k.startswith('work_pass') and k != 'work_pass_door':     # lies on the dashboard: follows the car's extra scale
        x, z, h = 12.5 + (x - 12.5) * KC, 34.0 + (z - 34.0) * KC, h * KC
    return [x * SC, h * SC, z * SC] + list(v[3:])


K.ANCH['work_pass'] = (12.5 + 0.7 * _ST.CAR_SC, 3.35 * _ST.CAR_SC, 34.0 - 2.6 * _ST.CAR_SC, 0.0, 1.0)     # flat on the dashboard of the car on the driveway (car turned 180 deg: local -x -> plot +x, local +z -> plot -z)
anch = {k: _anch(k, v) for k, v in K.ANCH.items()}
cover = [dict(name=n, x=x * SC, y=y * SC, z=z * SC, w=w * SC, d=d * SC, h=h * SC, yaw=yw) for (n, x, y, z, w, d, h, yw) in K.COVER]
routes = [dict(role=r, i=i, x=x * SC, y=y * SC, z=z * SC, pause=p, activity=a) for (r, i, x, y, z, p, a) in K.ROUTES]
def in_lot(t):
    if t[0] == 'fence':
        x, z = t[1], t[2]
    else:
        x, z = t[1], t[2]
    return -6.0 <= x <= 110.0 and -8.0 <= z <= 106.0


def _scaled(t):
    t = list(t)
    if t[0] == 'box' and abs(t[1] - 12.5) < 1e-6 and abs(t[2] - 34.0) < 1e-6:     # the father's car: collision box follows the car's extra scale
        t[3:6] = [v * KC for v in t[3:6]]
    n = {'cyl': 5, 'box': 6, 'fence': 5}.get(t[0], 1)
    return [t[0]] + [v * SC for v in t[1:n]] + t[n:]


yard = [_scaled(t) for t in K.COLL if in_lot(t)]
yard_biome = [_scaled(t) for t in K.COLL if not in_lot(t)]
lights = [[t[0], t[1] * SC, t[2] * SC, t[3] * SC] + list(t[4:]) for t in S.ROOM_LIGHTS]
wins = [list(w) if isinstance(w, tuple) else w for w in K.WINLOG]
json.dump({'doors': doors, 'anchors': anch, 'cover': cover, 'routes': routes, 'lights': lights}, open(os.path.join(OUT, 'data', 'interactive.json'), 'w'), indent=1)
json.dump({'house': [[round(v, 3) for v in b] for b in col.get('house', [])], 'biome': [[round(v, 3) for v in b] for b in col.get('biome', [])]},
          open(os.path.join(OUT, 'data', 'collision_boxes.json'), 'w'))
json.dump({'house': yard, 'biome': yard_biome}, open(os.path.join(OUT, 'data', 'yard_colliders.json'), 'w'))
stats['collision_house'] = len(col.get('house', []))
stats['collision_biome'] = len(col.get('biome', []))
stats['doors'] = len(doors)
stats['anchors'] = len(anch)
stats['cover'] = len(cover)
stats['routes'] = len(routes)
stats['yard_colliders'] = len(yard)
stats['yard_colliders_biome'] = len(yard_biome)
stats['room_lights'] = len(lights)
json.dump(stats, open(os.path.join(OUT, 'data', 'export_stats.json'), 'w'), indent=1)
print('EXPORT DONE', json.dumps(stats))
