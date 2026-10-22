"""Intersection audit for build_house_v5.py (no rendering).

Run: blender -b --factory-startup --python audit_v5.py -- <report.txt>
Every top-level furniture/prop model emitted by the HQ library becomes a "group". Groups are shrunk 3% about their bbox centre (so resting
contact is not flagged), then tested pairwise (same floor collection) and against the architecture with BVH triangle overlap.
"""
import os
import re
import sys
import inspect
import math

HERE = os.path.dirname(os.path.abspath(__file__))
rep_path = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else os.path.join(HERE, 'audit_report.txt')
src = open(os.path.join(HERE, 'build_house_v5.py'), encoding='utf-8').read()
assert src.rstrip().endswith('main()')
src = src.rstrip()[:-len('main()')]
sys.argv = [sys.argv[0], '--', os.path.join(HERE, 'audit_tmp')]
ns = {'__name__': 'audit_ns', '__file__': os.path.join(HERE, 'build_house_v5.py')}
exec(compile(src, 'build_house_v5.py', 'exec'), ns)

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

# model-function names (wrapped so nested calls collapse into one group)
names = set()
for fn in ('hq_models1.py', 'hq_rooms1.py', 'hq_rooms2.py', 'hq_rooms3.py', 'yard_hq.py'):
    names |= set(re.findall(r'^def (\w+)', open(os.path.join(HERE, fn), encoding='utf-8').read(), re.M))
names = {n for n in names if not n.startswith('hq_') and n in ns and n != 'P_'}

groups = []   # dict(label, coll, ranges{(c,m):[v0,v1,f0,f1]})
state = {'depth': 0, 'cur': None}
acc = ns['acc']
orig_emit = ns['emit']


def room_site():
    f = inspect.currentframe()
    while f:
        if f.f_code.co_name.startswith('hq_'):
            return '%s:%d' % (f.f_code.co_name, f.f_lineno)
        f = f.f_back
    return '?'


def new_group(label):
    g = dict(label=label, site=room_site(), ranges={})
    groups.append(g)
    return g


def emit_w(c, m, verts, faces, two_sided=False):
    key = (c, m)
    vs, fs = acc.setdefault(key, ([], []))
    v0, f0 = len(vs), len(fs)
    orig_emit(c, m, verts, faces, two_sided)
    g = state['cur']
    if g is None:
        g = new_group('prim')
        single = True
    else:
        single = False
    r = g['ranges'].setdefault(key, [v0, len(vs), f0, len(fs)])
    r[1], r[3] = len(vs), len(fs)
    g['coll'] = c


ns['emit'] = emit_w


def wrap(name):
    fn = ns[name]

    def w(*a, **k):
        top = state['depth'] == 0
        if top:
            state['cur'] = new_group(name)
        state['depth'] += 1
        try:
            return fn(*a, **k)
        finally:
            state['depth'] -= 1
            if top:
                state['cur'] = None
    w.__name__ = name
    ns[name] = w


for n in names:
    if n not in ('rbox', 'lathe', 'cylinder', 'sphere', 'tube', 'torus', 'leaf', 'sheet', 'book', 'ring_pts', 'emit'):
        wrap(n)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
ns['setup_scene']()
ns['build']()

# ----- collect geometry
grouped_faces = {}
for g in groups:
    for key, (v0, v1, f0, f1) in g['ranges'].items():
        grouped_faces.setdefault(key, set()).update(range(f0, f1))


def tris(vs, faces):
    out = []
    for f in faces:
        for i in range(1, len(f) - 1):
            out.append((f[0], f[i], f[i + 1]))
    return out


def bvh_from(vs, faces):
    return BVHTree.FromPolygons([tuple(v) for v in vs], tris(vs, faces), epsilon=0.0)


# architecture BVH per collection (everything not in a group)
arch = {}
for (c, m), (vs, fs) in acc.items():
    gf = grouped_faces.get((c, m), set())
    rest = [f for i, f in enumerate(fs) if i not in gf]
    if rest:
        arch.setdefault(c, []).append((vs, rest))
arch_bvh = {}
for c, lst in arch.items():
    allv, allf = [], []
    for vs, fs in lst:
        base = len(allv)
        allv.extend([ns['warp_v'](v, c) for v in vs])
        allf.extend([tuple(base + i for i in f) for f in fs])
    arch_bvh[c] = (bvh_from(allv, allf), Vector((min(v[0] for v in allv), min(v[1] for v in allv), min(v[2] for v in allv))), Vector((max(v[0] for v in allv), max(v[1] for v in allv), max(v[2] for v in allv))))

HX, HZ = ns['HX'], ns['HZ']
SH = 0.97
gdata = []
for g in groups:
    allv, allf = [], []
    for key, (v0, v1, f0, f1) in g['ranges'].items():
        vs, fs = acc[key]
        base = len(allv)
        allv.extend(vs[v0:v1])
        for f in fs[f0:f1]:
            allf.append(tuple(base + (i - v0) for i in f))
    if not allv:
        continue
    mn = Vector((min(v[0] for v in allv), min(v[1] for v in allv), min(v[2] for v in allv)))
    mx = Vector((max(v[0] for v in allv), max(v[1] for v in allv), max(v[2] for v in allv)))
    if (mx.z - mn.z) < 0.2:    # rugs / mats lying on the floor
        continue
    ctr = (mn + mx) / 2
    sv = [ctr + (Vector(v) - ctr) * SH for v in allv]
    g['mn'], g['mx'] = mn, mx
    g['bvh'] = bvh_from(sv, allf)
    g['ntri'] = len(allf)
    gdata.append(g)


def where(g):
    c = (g['mn'] + g['mx']) / 2
    return 'u=%.1f v=%.1f h=%.1f' % (c.x - HX, -c.y - HZ, c.z)


def bbox_hit(a, b):
    return all(a[0][i] <= b[1][i] and b[0][i] <= a[1][i] for i in range(3))


lines = []
pairs = []
for i, a in enumerate(gdata):
    for b in gdata[i + 1:]:
        if a['coll'] != b['coll']:
            continue
        if not bbox_hit((a['mn'], a['mx']), (b['mn'], b['mx'])):
            continue
        n = len(a['bvh'].overlap(b['bvh']))
        if n:
            pairs.append((n, a, b))
pairs.sort(key=lambda t: -t[0])
lines.append('=== furniture vs furniture: %d intersecting pairs (of %d groups)' % (len(pairs), len(gdata)))
for n, a, b in pairs:
    lines.append('%4d  %-16s %-28s <-> %-16s %-28s | %s | %s' % (n, a['label'], a['site'], b['label'], b['site'], where(a), where(b)))

hits = []
for a in gdata:
    for c, (bv, bmn, bmx) in arch_bvh.items():
        if not bbox_hit((a['mn'], a['mx']), (bmn, bmx)):
            continue
        n = len(a['bvh'].overlap(bv))
        if n:
            hits.append((n, a, c))
hits.sort(key=lambda t: -t[0])
lines.append('')
lines.append('=== furniture vs architecture: %d hits' % len(hits))
for n, a, c in hits:
    lines.append('%4d  %-16s %-28s x %-10s | %s' % (n, a['label'], a['site'], c, where(a)))

# out of room bounds (interior free faces u 1.8..34.2, v 1.8..42.2) for ground/upper furniture
lines.append('')
lines.append('=== furniture outside interior footprint')
for a in gdata:
    if a['coll'] not in ('Furn_G', 'Furn_U'):
        continue
    u0, u1 = a['mn'].x - HX, a['mx'].x - HX
    v0, v1 = -a['mx'].y - HZ, -a['mn'].y - HZ
    FX_, FZ_ = ns['FX'], ns['FZ']
    lo_u, hi_u, lo_v, hi_v = FX_(HX + 1.8) - HX - 0.1, FX_(HX + 34.2) - HX + 0.1, FZ_(HZ + 1.8) - HZ - 0.1, FZ_(HZ + 42.2) - HZ + 0.1
    if u0 < lo_u or u1 > hi_u or v0 < lo_v or v1 > hi_v:
        lines.append('  %-16s %-28s u %.1f..%.1f v %.1f..%.1f' % (a['label'], a['site'], u0, u1, v0, v1))
    if a['mx'].z > (ns['FH'](22.0) - 0.3 if a['coll'] == 'Furn_U' else ns['FH'](12.0) - 0.3):
        lines.append('  TALL %-16s %-28s top h=%.2f' % (a['label'], a['site'], a['mx'].z))

open(rep_path, 'w', encoding='utf-8').write('\n'.join(lines))
print('AUDIT DONE', len(gdata), 'groups', len(pairs), 'pairs', len(hits), 'arch hits')
