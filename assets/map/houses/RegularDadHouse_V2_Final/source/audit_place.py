"""Placement audit: finds floating / sunk / displaced props and misaligned curtains.

Run: blender -b --factory-startup --python audit_place.py -- <report.txt>
For every top-level model (group) the lowest vertices are ray-cast downwards against the architecture and all other groups:
  FLOAT  - bottom is more than 0.25 above the nearest support although the item is not wall-mounted / ceiling-hung / on a shelf
  SUNK   - bottom is more than 0.35 below the support surface it rests on
Also reports curtains whose centre is more than 1.2 away from the nearest window and items outside the plot lawn.
"""
import os
import re
import sys
import math
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
rep_path = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else os.path.join(HERE, 'audit_place_report.txt')
src = open(os.path.join(HERE, 'build_house_v5.py'), encoding='utf-8').read().rstrip()[:-len('main()')]
sys.argv = [sys.argv[0], '--', os.path.join(HERE, 'audit_tmp')]
ns = {'__name__': 'audit_place', '__file__': os.path.join(HERE, 'build_house_v5.py')}
exec(compile(src, 'build_house_v5.py', 'exec'), ns)
import bpy
import inspect
from mathutils import Vector
from mathutils.bvhtree import BVHTree

names = set()
for fn in ('hq_models1.py', 'hq_rooms1.py', 'hq_rooms2.py', 'hq_rooms3.py', 'yard_hq.py', 'fill_hq.py', 'rooms_extra.py'):
    names |= set(re.findall(r'^def (\w+)', open(os.path.join(HERE, fn), encoding='utf-8').read(), re.M))
names = {n for n in names if not n.startswith('hq_') and n in ns and n not in ('P_', 'PK', 'hq_extra')}
acc = ns['acc']
orig_emit = ns['emit']
groups = []
st = {'d': 0, 'cur': None}


def site():
    f = inspect.currentframe()
    while f:
        if f.f_code.co_name.startswith('hq_'):
            return '%s:%d' % (f.f_code.co_name, f.f_lineno)
        f = f.f_back
    return '?'


def new_group(label):
    g = dict(label=label, site=site(), verts=[], tris=[], coll=None)
    tfs = ns['_TF']
    if tfs:
        g['front'] = (-tfs[-1][4], -tfs[-1][3])      # world (x, y=-z) direction of the model's +lz
    groups.append(g)
    return g


def emit_w(c, m, verts, faces, two_sided=False):
    key = (c, m)
    vs, fs = acc.setdefault(key, ([], []))
    v0, f0 = len(vs), len(fs)
    orig_emit(c, m, verts, faces, two_sided)
    g = st['cur'] or new_group('prim')
    base = len(g['verts'])
    g['verts'] += [tuple(v) for v in vs[v0:]]
    for f in fs[f0:]:
        idx = [base + (i - v0) for i in f]
        for k in range(1, len(idx) - 1):
            g['tris'].append((idx[0], idx[k], idx[k + 1]))
    g['coll'] = c


ns['emit'] = emit_w


def wrap(n):
    fn = ns[n]

    def w(*a, **k):
        top = st['d'] == 0
        if top:
            st['cur'] = new_group(n)
        st['d'] += 1
        try:
            return fn(*a, **k)
        finally:
            st['d'] -= 1
            if top:
                st['cur'] = None
    ns[n] = w


for n in names:
    if n not in ('rbox', 'lathe', 'cylinder', 'sphere', 'tube', 'torus', 'leaf', 'sheet', 'book', 'ring_pts', 'emit', 'blob', 'YM', '_wpos', '_wcyl', '_wbox', 'picket'):
        wrap(n)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
ns['setup_scene']()
ns['build']()
warp_v = ns['warp_v']
HX, HZ, F0, F1 = ns['HX'], ns['HZ'], ns['F0'], ns['F1']

# ---- architecture BVH (everything that is not a furniture/yard group)
grouped = collections.defaultdict(set)
arch_v, arch_f = [], []
gtris = {}
for (c, m), (vs, fs) in acc.items():
    if c.startswith('Furn'):
        continue
    base = len(arch_v)
    arch_v += [warp_v(v, c) for v in vs]
    for f in fs:
        idx = [base + i for i in f]
        for k in range(1, len(idx) - 1):
            arch_f.append((idx[0], idx[k], idx[k + 1]))
arch = BVHTree.FromPolygons([tuple(v) for v in arch_v], arch_f, epsilon=0.0)

gl = []
for g in groups:
    if not g['verts'] or not g['coll'] or not g['coll'].startswith('Furn_'):
        continue
    vs = g['verts']
    zs = [v[2] for v in vs]
    g['mn'] = Vector((min(v[0] for v in vs), min(v[1] for v in vs), min(zs)))
    g['mx'] = Vector((max(v[0] for v in vs), max(v[1] for v in vs), max(zs)))
    g['bvh'] = BVHTree.FromPolygons(vs, g['tris'], epsilon=0.0)
    g['thin'] = (g['mx'].z - g['mn'].z) < 0.2      # rugs / mats / boards: supports only
    gl.append(g)

lines = []


def where(g):
    c = (g['mn'] + g['mx']) / 2
    return 'x=%.1f z=%.1f h=%.1f' % (c.x, -c.y, g['mn'].z)


def support(pt, me):
    """highest surface directly below pt (arch + other groups)"""
    best = -1e9
    o = Vector((pt[0], pt[1], pt[2] + 0.08))
    hit = arch.ray_cast(o, Vector((0, 0, -1)), 60.0)
    if hit[0] is not None:
        best = hit[0].z
    for g in gl:
        if g is me:
            continue
        if g['mn'].x - 0.05 <= pt[0] <= g['mx'].x + 0.05 and g['mn'].y - 0.05 <= pt[1] <= g['mx'].y + 0.05 and g['mn'].z <= pt[2] + 0.08:
            h = g['bvh'].ray_cast(o, Vector((0, 0, -1)), 60.0)
            if h[0] is not None and h[0].z > best:
                best = h[0].z
    return best


def wall_near(g):
    c = (g['mn'] + g['mx']) / 2
    c.z = g['mn'].z + (g['mx'].z - g['mn'].z) * 0.5
    r = max(g['mx'].x - g['mn'].x, g['mx'].y - g['mn'].y) / 2 + 0.6
    for d in (Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0))):
        h = arch.ray_cast(c, d, r)
        if h[0] is not None:
            return True
    return False


def ceiling_near(g):
    c = (g['mn'] + g['mx']) / 2
    o = Vector((c.x, c.y, g['mx'].z - 0.05))
    h = arch.ray_cast(o, Vector((0, 0, 1)), 2.5)
    return h[0] is not None


flags = collections.defaultdict(list)
for g in gl:
    if g['thin']:
        continue
    low = [v for v in g['verts'] if v[2] < g['mn'].z + 0.12]
    step = max(1, len(low) // 30)
    sample = low[::step][:30]
    gaps = []
    for p in sample:
        s = support(p, g)
        gaps.append(p[2] - s)
    gap = min(gaps) if gaps else 0.0
    gmax = max(gaps) if gaps else 0.0
    if gap > 0.25:
        if wall_near(g) or ceiling_near(g):
            continue
        flags['FLOAT'].append((gap, g))
    elif gap < -0.35:
        flags['SUNK'].append((gap, g))

for k in ('FLOAT', 'SUNK'):
    lines.append('=== %s: %d' % (k, len(flags[k])))
    for gap, g in sorted(flags[k], key=lambda t: -abs(t[0])):
        lines.append('  gap=%6.2f  %-16s %-26s %s' % (gap, g['label'], g['site'], where(g)))

# ---- curtains vs windows (glass boxes of the exterior walls)
glass = []
for (c, mn, x0, x1, h0, h1, z0, z1) in ns['BOXLOG']:
    if mn == 'glass' and c in ('Ground', 'Upper'):
        FX, FZ, FH = ns['FX'], ns['FZ'], ns['FH']
        glass.append(((FX(x0) + FX(x1)) / 2, (FZ(z0) + FZ(z1)) / 2, FH(h0), FH(h1), abs(FX(x1) - FX(x0)), abs(FZ(z1) - FZ(z0))))
lines.append('')
lines.append('=== curtains: offset to the nearest window centre')
for g in gl:
    if g['label'] != 'curtain_pair':
        continue
    cx, cz = (g['mn'].x + g['mx'].x) / 2, -(g['mn'].y + g['mx'].y) / 2
    hh = g['mn'].z
    best = None
    for (gx, gz, gh0, gh1, wx, wz) in glass:
        if gh0 - 3 < hh < gh1 + 6:
            d = math.hypot(gx - cx, gz - cz)
            if best is None or d < best[0]:
                best = (d, gx, gz, wx, wz)
    if best:
        lines.append('  %-30s curtain=(%.1f,%.1f) window=(%.1f,%.1f) offset=%.2f %s' % (g['site'], cx, cz, best[1], best[2], best[0], 'MISALIGNED' if best[0] > 1.2 else ''))

# ---- outside the lawn / the lot
lines.append('')
lines.append('=== items beyond the map lawn (x -70..178, z -60..173)')
for g in gl:
    c = (g['mn'] + g['mx']) / 2
    if not (-70 <= c.x <= 178 and -60 <= -c.y <= 173):
        lines.append('  %-16s %-26s %s' % (g['label'], g['site'], where(g)))
FX, FZ, FH = ns['FX'], ns['FZ'], ns['FH']
ROOM_OF = {
    'hq_hall_stairs': [(0, 1.8, 13.5, 22.5, 42.2), (1, 1.8, 13.5, 10.5, 42.2)], 'hq_living': [(0, 14.5, 34.2, 22.5, 42.2)], 'hq_dining': [(0, 14.5, 34.2, 1.8, 21.5)],
    'hq_kitchen': [(0, 1.8, 13.5, 10.5, 21.5)], 'hq_laundry': [(0, 1.8, 13.5, 1.8, 9.5)], 'hq_wc': [(0, 28.5, 34.2, 1.8, 7.5)],
    'hq_upper_hall_bath': [(1, 1.8, 13.5, 1.8, 42.2)], 'hq_master': [(1, 14.5, 34.2, 30.5, 42.2)], 'hq_child': [(1, 14.5, 34.2, 16.5, 29.5)],
    'hq_lounge': [(1, 14.5, 34.2, 1.8, 15.5), (1, 17.8, 32.2, -5.2, 0.0)],
}
lines.append('')
lines.append('=== items outside the room of their function (centre + 1 stud margin)')
cnt = 0
for g in gl:
    fn = g['site'].split(':')[0]
    if fn not in ROOM_OF:
        continue
    c = (g['mn'] + g['mx']) / 2
    ok = False
    for (fl, u0, u1, v0, v1) in ROOM_OF[fn]:
        floor_h = FH(F1) if fl else FH(F0)
        if floor_h - 1.0 <= g['mn'].z <= floor_h + 14.0 and FX(HX + u0) - 1.0 <= c.x <= FX(HX + u1) + 1.0 and FZ(HZ + v0) - 1.0 <= -c.y <= FZ(HZ + v1) + 1.0:
            ok = True
    if not ok:
        cnt += 1
        lines.append('  %-16s %-26s %s' % (g['label'], g['site'], where(g)))
lines.append('  total %d' % cnt)
lines.append('')
lines.append('=== yard props on the road (z 111.4..135.4)')
for g in gl:
    c = (g['mn'] + g['mx']) / 2
    if (g['site'].startswith('hq_yard') or g['site'].startswith('hq_fill')) and 111.4 <= -c.y <= 135.4 and g['label'] not in ('lamp_post', 'manhole', 'tree_oak'):
        lines.append('  %-16s %-26s %s' % (g['label'], g['site'], where(g)))

# ---- orientation: items whose front looks straight into a wall (or a big piece of furniture)
lines.append('')
lines.append('=== front of the item is blocked by a wall within 1.0 stud')
FACING = {'sofa', 'armchair', 'console_table', 'sideboard', 'bookshelf', 'dresser', 'wardrobe', 'tv_unit', 'cabinet', 'sink_unit', 'stove', 'fridge', 'toilet', 'desk', 'dining_chair', 'recliner', 'bench', 'kid_chair', 'bed', 'nightstand', 'washer', 'pedestal_sink'}
for g in gl:
    if g['label'] not in FACING or g['thin'] or 'front' not in g:
        continue
    c = (g['mn'] + g['mx']) / 2
    c.z = g['mn'].z + min(1.5, (g['mx'].z - g['mn'].z) * 0.5)
    fx, fy = g['front']
    half = abs(fx) * (g['mx'].x - g['mn'].x) / 2 + abs(fy) * (g['mx'].y - g['mn'].y) / 2
    d = Vector((fx, fy, 0)).normalized()
    h = arch.ray_cast(c, d, half + 1.0)
    if h[0] is not None and (h[0] - c).length < half + 0.9:
        lines.append('  %-16s %-26s %s  dist_to_wall_in_front=%.2f' % (g['label'], g['site'], where(g), (h[0] - c).length - half))

cb = cf = 0
for g in gl:
    if g['label'] not in FACING or g['thin'] or 'front' not in g:
        continue
    c = (g['mn'] + g['mx']) / 2
    c.z = g['mn'].z + min(1.5, (g['mx'].z - g['mn'].z) * 0.5)
    fx, fy = g['front']
    half = abs(fx) * (g['mx'].x - g['mn'].x) / 2 + abs(fy) * (g['mx'].y - g['mn'].y) / 2
    for sg, name in ((1, 'f'), (-1, 'b')):
        h = arch.ray_cast(c, Vector((fx * sg, fy * sg, 0)).normalized(), half + 1.0)
        if h[0] is not None and (h[0] - c).length < half + 0.9:
            if sg == 1:
                cf += 1
            else:
                cb += 1
lines.append('  control: items with wall at the back=%d, wall in front=%d' % (cb, cf))
open(rep_path, 'w', encoding='utf-8').write('\n'.join(lines))
print('PLACE AUDIT DONE groups=%d FLOAT=%d SUNK=%d' % (len(gl), len(flags['FLOAT']), len(flags['SUNK'])))
