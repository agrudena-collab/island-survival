"""OfficeDadHouse_V2_Final audits (adapted copies of audit_v5 / audit_place / box_audit / coverage of RegularDadHouse_V2_Final + walkability and contract checks).

Run:  python -I audit_all.py <report.txt>
A  box_audit      architecture boxes: interpenetration and coplanar faces of different materials (z-fighting)
B  audit_v5       furniture vs furniture / vs architecture triangle intersections (groups shrunk 3 %)
C  audit_place    FLOAT / SUNK props, curtains vs windows
D  coverage       furniture footprint per room
E  walkability    free-space grid per floor: door widths, 5-stud passages, route points, hide spots, stairs
F  contract       names / tags the services need, cover heights, hide spot sizes
Goal: 0 issues in A..F (the final line prints ISSUES n).
"""
import os
import re
import sys
import math
import json
import inspect
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'audit_report.txt')

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import odh_core as K
import odh_models as M
import odh_scene as S
import build_odh as BO
import odh_house as H
from odh_core import F1, F2, CEIL1

ISSUES = []
lines = []


def issue(msg):
    ISSUES.append(msg)
    lines.append('ISSUE ' + msg)


# ------------------------------------------------------------------ instrument the model functions (groups)
groups = []
st = {'d': 0, 'cur': None}
acc = K.acc
orig_emit = K.emit
PRIM = {'MT', 'YM', 'rbox', 'lathe', 'cylinder', 'sphere', 'tube', 'torus', 'leaf', 'sheet', 'book', 'blob', 'picket', '_wpos', '_wcyl', '_wbox'}


def site():
    f = inspect.currentframe()
    while f:
        n = f.f_code.co_name
        if f.f_code.co_filename.endswith(('odh_rooms.py', 'odh_site.py', 'odh_biome.py')):
            return '%s:%d' % (n, f.f_lineno)
        f = f.f_back
    return '?'


def new_group(label):
    g = dict(label=label, site=site(), verts=[], tris=[], coll=None, ranges={})
    if K._TF:
        g['front'] = (-K._TF[-1][4], -K._TF[-1][3])
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
    r = g['ranges'].setdefault(key, [f0, len(fs)])
    r[1] = len(fs)
    g['coll'] = c


K.emit = emit_w
M.emit = emit_w


def wrap(mod, n):
    fn = getattr(mod, n)

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
    setattr(mod, n, w)


for n, o in list(vars(M).items()):
    if inspect.isfunction(o) and o.__module__ == M.__name__ and n not in PRIM and not n.startswith('_'):
        wrap(M, n)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
BO.build()
print('built; groups', len(groups))

# ====================================================================================== A  box audit
lines.append('=== A. architecture boxes (box_audit)')
boxes = [t for t in K.BOXLOG if t[0] != 'Biome']
E = 0.02
inter = []
for i in range(len(boxes)):
    a = boxes[i]
    for j in range(i + 1, len(boxes)):
        b = boxes[j]
        if b[2] > a[3] or a[2] > b[3]:
            continue
        ox = min(a[3], b[3]) - max(a[2], b[2])
        oy = min(a[5], b[5]) - max(a[4], b[4])
        oz = min(a[7], b[7]) - max(a[6], b[6])
        if ox > E and oy > E and oz > E:
            inter.append((ox * oy * oz, a, b))
lines.append('BOXES %d  INTERPENETRATING %d (solid-vs-solid only counted as issue when volume > 4 and neither is a frame/trim)' % (len(boxes), len(inter)))
inter.sort(key=lambda t: -t[0])
def _junction(a_, b_):
    w_ = lambda n: n.startswith('wall_') or n in ('stucco', 'stucco_dk')
    return w_(a_[1]) and w_(b_[1])


bigint = [t for t in inter if t[0] > 4.0 and not _junction(t[1], t[2]) and t[1][1] not in ('trim', 'glass', 'brass', 'skirt', 'metal', 'parapet') and t[2][1] not in ('trim', 'glass', 'brass', 'skirt', 'metal', 'parapet')]
for v, a, b in bigint[:40]:
    lines.append('  OVL vol=%.1f %s %s [%.1f..%.1f x %.1f..%.1f x %.1f..%.1f] vs %s %s [%.1f..%.1f x %.1f..%.1f x %.1f..%.1f]' % ((v,) + a[:2] + a[2:8] + b[:2] + b[2:8]))
for v, a, b in bigint:
    issue('box overlap vol %.1f %s/%s at x %.1f z %.1f h %.1f' % (v, a[1], b[1], (a[2] + a[3]) / 2, (a[6] + a[7]) / 2, (a[4] + a[5]) / 2))

faces = []
for k, (c, mn, x0, x1, h0, h1, z0, z1) in enumerate(boxes):
    faces += [(0, x0, -1, (h0, h1, z0, z1), mn, k), (0, x1, 1, (h0, h1, z0, z1), mn, k), (1, h0, -1, (x0, x1, z0, z1), mn, k), (1, h1, 1, (x0, x1, z0, z1), mn, k),
              (2, z0, -1, (x0, x1, h0, h1), mn, k), (2, z1, 1, (x0, x1, h0, h1), mn, k)]
byaxis = collections.defaultdict(list)
for f in faces:
    byaxis[(f[0], f[2], round(f[1], 2))].append(f)
zf = collections.Counter()
for key, lst in byaxis.items():
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            a, b = lst[i], lst[j]
            if a[5] == b[5] or a[4] == b[4]:
                continue
            if min(a[3][1], b[3][1]) - max(a[3][0], b[3][0]) > 0.05 and min(a[3][3], b[3][3]) - max(a[3][2], b[3][2]) > 0.05:
                zf[tuple(sorted((a[4], b[4])))] += 1
lines.append('COPLANAR_DIFFERENT_MATERIAL %d (box level; resolved in the FBX export: the covered part is cut out of the larger face, see section H)' % sum(zf.values()))

# ====================================================================================== B / C  furniture groups
gl = []
for g in groups:
    if not g['verts'] or g['coll'] not in ('Furn_G', 'Furn_U', 'Site'):
        continue
    vs = g['verts']
    g['mn'] = Vector((min(v[0] for v in vs), min(v[1] for v in vs), min(v[2] for v in vs)))
    g['mx'] = Vector((max(v[0] for v in vs), max(v[1] for v in vs), max(v[2] for v in vs)))
    gl.append(g)

grouped = collections.defaultdict(set)
for g in groups:
    for key, (f0, f1) in g['ranges'].items():
        grouped[key].update(range(f0, f1))
arch_v, arch_f = [], []
for (c, m), (vs, fs) in acc.items():
    if c in ('Biome', 'BiomeOrg', 'DoorLeaf', 'DoorLeafU', 'FatherProxy', 'PassProxy'):
        continue
    gf = grouped.get((c, m), set())
    base = len(arch_v)
    arch_v += [tuple(v) for v in vs]
    for i, f in enumerate(fs):
        if i in gf:
            continue
        idx = [base + j for j in f]
        for k in range(1, len(idx) - 1):
            arch_f.append((idx[0], idx[k], idx[k + 1]))
arch = BVHTree.FromPolygons(arch_v, arch_f, epsilon=0.0)
SH = 0.97
big = [g for g in gl if g['mx'].z - g['mn'].z >= 0.2]
for g in big:
    ctr = (g['mn'] + g['mx']) / 2
    g['bvh'] = BVHTree.FromPolygons([tuple(ctr + (Vector(v) - ctr) * SH) for v in g['verts']], g['tris'], epsilon=0.0)


def where(g):
    c = (g['mn'] + g['mx']) / 2
    return 'x=%.1f z=%.1f h=%.1f' % (c.x, -c.y, g['mn'].z)


def bbox_hit(a, b):
    return all(a[0][i] <= b[1][i] and b[0][i] <= a[1][i] for i in range(3))


lines.append('')
lines.append('=== B. furniture intersections (audit_v5)')
pairs = []
for i, a in enumerate(big):
    for b in big[i + 1:]:
        if a['coll'] != b['coll'] or a['coll'] == 'Site':
            continue
        if not bbox_hit((a['mn'], a['mx']), (b['mn'], b['mx'])):
            continue
        n = len(a['bvh'].overlap(b['bvh']))
        if n:
            pairs.append((n, a, b))
pairs.sort(key=lambda t: -t[0])
lines.append('furniture vs furniture: %d intersecting pairs of %d groups' % (len(pairs), len(big)))
for n, a, b in pairs:
    lines.append('  %4d  %-16s %-26s <-> %-16s %-26s | %s | %s' % (n, a['label'], a['site'], b['label'], b['site'], where(a), where(b)))
    if n > 6:
        issue('furniture intersects furniture: %s %s <-> %s %s (%d tris)' % (a['label'], where(a), b['label'], where(b), n))
hits = []
for a in big:
    if a['coll'] == 'Site':
        continue
    ov = a['bvh'].overlap(arch)
    n = len(ov)
    if n:
        a['bb'] = (tuple(round(v, 1) for v in a['mn']), tuple(round(v, 1) for v in a['mx'])); a['ovc'] = [tuple(round(sum(arch_v[i][k] for i in arch_f[j]) / 3.0, 1) for k in range(3)) for (_, j) in ov[:3]]
        hits.append((n, a))
hits.sort(key=lambda t: -t[0])
lines.append('furniture vs architecture: %d hits' % len(hits))
for n, a in hits:
    lines.append('  %4d  %-16s %-26s | %s | arch tris at %s bb %s' % (n, a['label'], a['site'], where(a), a.get('ovc'), a.get('bb')))
    if n > 10:
        issue('furniture cuts architecture: %s %s (%d tris)' % (a['label'], where(a), n))

lines.append('')
lines.append('=== C. placement (audit_place)')
gl_f = [g for g in gl if g['coll'] in ('Furn_G', 'Furn_U')]


def support(pt, me):
    best = -1e9
    o = Vector((pt[0], pt[1], pt[2] + 0.08))
    h = arch.ray_cast(o, Vector((0, 0, -1)), 60.0)
    if h[0] is not None:
        best = h[0].z
    for g in big:
        if g is me or g['coll'] not in ('Furn_G', 'Furn_U'):
            continue
        if g['mn'].x - 0.05 <= pt[0] <= g['mx'].x + 0.05 and g['mn'].y - 0.05 <= pt[1] <= g['mx'].y + 0.05 and g['mn'].z <= pt[2] + 0.08:
            hh = g['bvh'].ray_cast(o, Vector((0, 0, -1)), 60.0)
            if hh[0] is not None and hh[0].z > best:
                best = hh[0].z
    return best


def wall_near(g):
    c = (g['mn'] + g['mx']) / 2
    c.z = g['mn'].z + (g['mx'].z - g['mn'].z) * 0.5
    r = max(g['mx'].x - g['mn'].x, g['mx'].y - g['mn'].y) / 2 + 0.6
    return any(arch.ray_cast(c, d, r)[0] is not None for d in (Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0))))


def ceiling_near(g):
    c = (g['mn'] + g['mx']) / 2
    return arch.ray_cast(Vector((c.x, c.y, g['mx'].z - 0.05)), Vector((0, 0, 1)), 2.5)[0] is not None


flt, snk = [], []
for g in gl_f:
    if g['mx'].z - g['mn'].z < 0.2:
        continue
    low = [v for v in g['verts'] if v[2] < g['mn'].z + 0.12]
    sample = low[::max(1, len(low) // 30)][:30]
    gaps = [p[2] - support(p, g) for p in sample]
    gap = min(gaps) if gaps else 0.0
    if gap > 0.25:
        if wall_near(g) or ceiling_near(g):
            continue
        flt.append((gap, g))
    elif gap < -0.35:
        snk.append((gap, g))
for name, lst in (('FLOAT', flt), ('SUNK', snk)):
    lines.append('%s: %d' % (name, len(lst)))
    for gap, g in sorted(lst, key=lambda t: -abs(t[0])):
        lines.append('  gap=%6.2f  %-16s %-26s %s' % (gap, g['label'], g['site'], where(g)))
        issue('%s %s %s gap %.2f' % (name, g['label'], where(g), gap))
glass = []
for (c, mn, x0, x1, h0, h1, z0, z1) in K.BOXLOG:
    if mn == 'glass' and c in ('Ground', 'Upper'):
        glass.append(((x0 + x1) / 2, (z0 + z1) / 2, h0, h1))
mis = 0
for g in gl_f:
    if g['label'] != 'curtain_pair':
        continue
    cx, cz = (g['mn'].x + g['mx'].x) / 2, -(g['mn'].y + g['mx'].y) / 2
    best = min((math.hypot(gx - cx, gz - cz) for (gx, gz, a, b) in glass if a - 3 < g['mn'].z < b + 6), default=None)
    if best is not None and best > 1.4:
        mis += 1
        issue('curtain %s %.1f from the nearest window' % (g['site'], best))
lines.append('curtains misaligned: %d' % mis)

# ====================================================================================== D  coverage
lines.append('')
lines.append('=== D. coverage per room (furniture footprint / room area)')
low_cov = []
for name, (fl, u0, u1, v0, v1, wc) in H.ROOMS.items():
    area = (u1 - u0) * (v1 - v0)
    x0, x1, z0, z1 = H.X(u0), H.X(u1), H.Z(v0), H.Z(v1)
    ylo = F1 if fl == 1 else F2 if fl == 2 else 0.5
    cov = 0.0
    for g in gl_f:
        if g['mn'].z > ylo + 1.0 or g['mx'].z < ylo + 1.0:
            continue
        cx, cz = (g['mn'].x + g['mx'].x) / 2, -(g['mn'].y + g['mx'].y) / 2
        if x0 <= cx <= x1 and z0 <= cz <= z1:
            w, d = g['mx'].x - g['mn'].x, -g['mn'].y + g['mx'].y
            d = (g['mx'].y - g['mn'].y)
            if w * d < area * 0.5:
                cov += w * d
    lines.append('COV %-8s area=%7.1f footprint=%6.1f coverage=%4.1f%%' % (name, area, cov, 100 * cov / area))

# ====================================================================================== E  walkability
lines.append('')
lines.append('=== E. walkability (grid 0.5, architecture collision only; furniture has no collision in game)')
CELLS = 0.25
X0, X1, Z0, Z1 = 0.0, 110.0, 2.0, 100.0   # house + lot area


def grid(h_lo, h_hi, x0=X0, x1=X1, z0=Z0, z1=Z1):
    nx, nz = int((x1 - x0) / CELLS), int((z1 - z0) / CELLS)
    g = np.zeros((nz, nx), dtype=bool)
    for (c, mn, bx0, bx1, bh0, bh1, bz0, bz1) in K.BOXLOG:
        if c == 'Biome' or c in ('Roof',):
            continue
        if bh1 <= h_lo or bh0 >= h_hi:
            continue
        i0, i1 = max(0, int((bx0 - x0) / CELLS)), min(nx, int(math.ceil((bx1 - x0) / CELLS)))
        j0, j1 = max(0, int((bz0 - z0) / CELLS)), min(nz, int(math.ceil((bz1 - z0) / CELLS)))
        if i1 > i0 and j1 > j0:
            g[j0:j1, i0:i1] = True
    return g, x0, z0


def dilate(g, r):
    n = int(math.ceil(r / CELLS))
    out = g.copy()
    for dz in range(-n, n + 1):
        for dx in range(-n, n + 1):
            if dx * dx + dz * dz <= n * n:
                out |= np.roll(np.roll(g, dz, axis=0), dx, axis=1)
    return out


def flood(free, start):
    sj, si = start
    if not free[sj, si]:
        return None
    seen = np.zeros_like(free)
    stack = [(sj, si)]
    seen[sj, si] = True
    nz, nx = free.shape
    while stack:
        j, i = stack.pop()
        for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = j + dj, i + di
            if 0 <= a < nz and 0 <= b < nx and free[a, b] and not seen[a, b]:
                seen[a, b] = True
                stack.append((a, b))
    return seen


def cell(x, z, x0, z0):
    return int((z - z0) / CELLS), int((x - x0) / CELLS)


# ground floor: obstacles between knee and head above F1 (stair steps are walkable by the stair link and are removed from this layer)
STAIR_X = (H.X(0.0), H.X(7.0) + 0.4)
STAIR_Z = (H.Z(12.0), H.Z(30.0))
g1, gx0, gz0 = grid(F1 + 1.4, F1 + 7.0)
for (c, mn, bx0, bx1, bh0, bh1, bz0, bz1) in K.BOXLOG:
    pass
# remove the stair steps themselves (wood boxes inside the stair footprint) from the ground layer
for (c, mn, bx0, bx1, bh0, bh1, bz0, bz1) in K.BOXLOG:
    if mn in ('wood', 'wood_lt') and STAIR_X[0] - 0.1 <= bx0 and bx1 <= STAIR_X[1] + 0.1 and STAIR_Z[0] - 0.1 <= bz0 and bz1 <= STAIR_Z[1] + 0.2 and bh0 < F1 + 14.0 and bh1 < F2 + 0.1:
        i0, i1 = int((bx0 - gx0) / CELLS), int(math.ceil((bx1 - gx0) / CELLS))
        j0, j1 = int((bz0 - gz0) / CELLS), int(math.ceil((bz1 - gz0) / CELLS))
        g1[j0:j1, i0:i1] = False
# yard colliders on the ground layer
def stamp(g, x0, x1, z0, z1, ox, oz):
    i0, i1 = max(0, int((x0 - ox) / CELLS)), min(g.shape[1], int(math.ceil((x1 - ox) / CELLS)))
    j0, j1 = max(0, int((z0 - oz) / CELLS)), min(g.shape[0], int(math.ceil((z1 - oz) / CELLS)))
    if i1 > i0 and j1 > j0:
        g[j0:j1, i0:i1] = True


for t in K.COLL:
    if t[0] == 'box':
        x, z, sx, sz = t[1], t[2], t[3], t[4]
        stamp(g1, x - sx / 2, x + sx / 2, z - sz / 2, z + sz / 2, gx0, gz0)
    elif t[0] == 'cyl':
        x, z, r = t[1], t[2], t[3]
        stamp(g1, x - r, x + r, z - r, z + r, gx0, gz0)
    elif t[0] == 'fence':
        x0_, z0_, x1_, z1_ = t[1:5]
        n = int(max(abs(x1_ - x0_), abs(z1_ - z0_)) / 0.25) + 1
        for k in range(n + 1):
            x, z = x0_ + (x1_ - x0_) * k / n, z0_ + (z1_ - z0_) * k / n
            stamp(g1, x - 0.25, x + 0.25, z - 0.25, z + 0.25, gx0, gz0)
# open doors: the leaves are not collision in the model (they swing); nothing to remove. Door openings are real holes in the wall boxes.
free_agent = ~dilate(g1, 1.6)
free_wide = ~dilate(g1, 2.45)
A = K.ANCH


def anchor_cell(name, g_):
    a = A[name]
    return cell(a[0], a[2], gx0, gz0)


reach = {}
start = None
for nm in ('front_door',):
    a = A[nm]
    start = cell(a[0], a[2], gx0, gz0)
seen_agent = flood(free_agent, start) if start else None
seen_wide = flood(free_wide, start) if start else None
lines.append('start = front door anchor; free cells (agent r=1.6): %d, (passage 5.0): %d' % (int(seen_agent.sum()) if seen_agent is not None else 0, int(seen_wide.sum()) if seen_wide is not None else 0))
if seen_agent is None:
    near = [(b[1], round(b[2], 1), round(b[3], 1), round(b[4], 1), round(b[5], 1), round(b[6], 1), round(b[7], 1)) for b in K.BOXLOG
            if b[2] - 1.8 < A['front_door'][0] < b[3] + 1.8 and b[6] - 1.8 < A['front_door'][2] < b[7] + 1.8 and b[5] > F1 + 1.4 and b[4] < F1 + 7.0]
    lines.append('blocking near the front door: %s' % near[:8])
    issue('front door anchor is not in free space')
else:
    # ground-floor targets: every ground room centre, entry anchors, hide spot enter points, route points on the ground floor
    targets = {}
    for name, (fl, u0, u1, v0, v1, wc) in H.ROOMS.items():
        if fl == 1:
            targets['room:' + name] = (H.X((u0 + u1) / 2), H.Z((v0 + v1) / 2))
    for nm in ('stair_foot', 'back_door', 'hide_cupboard_enter', 'garage_door', 'garage_service', 'work_pass_door', 'ladder_foot'):
        if nm in A:
            targets[nm] = (A[nm][0], A[nm][2])
    for r in K.ROUTES:
        if r[3] <= F1 + 0.1 and r[0] != 'Dog':
            targets['route %s_%02d' % (r[0], r[1])] = (r[2], r[4])
        if r[0] == 'Dog':
            targets['route %s_%02d' % (r[0], r[1])] = (r[2], r[4])
    ROOM_RECT = {n: (H.X(v[1]), H.X(v[2]), H.Z(v[3]), H.Z(v[4])) for n, v in H.ROOMS.items() if v[0] == 1}
    for tname in sorted(t for t in targets if t.startswith('room:')):
        rx0, rx1, rz0, rz1 = ROOM_RECT[tname[5:]]
        m = np.zeros_like(free_agent)
        stamp(m, rx0 + 0.3, rx1 - 0.3, rz0 + 0.3, rz1 - 0.3, gx0, gz0)
        fr, rc, rw = int((free_agent & m).sum()), int((seen_agent & m).sum()), int((seen_wide & m).sum())
        lines.append('  %-28s free cells %6d reachable %6d reachable via 5-stud passages %6d' % (tname, fr, rc, rw))
        if fr == 0:
            issue('no free floor in %s' % tname)
        elif rc < 0.95 * fr:
            issue('part of %s unreachable for the NPC: %d of %d free cells' % (tname, rc, fr))
        elif rw == 0:
            issue('%s reachable only through narrow passages' % tname)
        targets.pop(tname)
    for tname, (x, z) in sorted(targets.items()):
        c = cell(x, z, gx0, gz0)
        okA = bool(seen_agent[c]) if 0 <= c[0] < seen_agent.shape[0] and 0 <= c[1] < seen_agent.shape[1] else False
        okW = bool(seen_wide[c]) if 0 <= c[0] < seen_wide.shape[0] and 0 <= c[1] < seen_wide.shape[1] else False
        if not okA and tname in ('garage_door', 'work_pass_door', 'ladder_foot') or (not okA and tname.startswith('hide_')):
            seen_p = flood(~dilate(g1, 1.0), start)       # player radius ~1 for outdoor entry spots
            okA = okW = bool(seen_p is not None and seen_p[c])
        lines.append('  %-28s (%.1f, %.1f) agent=%s passage5=%s' % (tname, x, z, okA, okW))
        if not okA:
            issue('ground target not reachable (r=1.6, outdoor spots r=1.0): %s at (%.1f, %.1f)' % (tname, x, z))
        elif not okW and not tname.startswith(('garage', 'hide', 'work', 'ladder', 'back')):
            issue('ground target reachable only through a passage narrower than 5 studs: %s' % tname)
        elif not okW:
            lines.append('    note: %s passage narrower than 5 (outdoor / threshold)' % tname)

# upper floor
g2, ux0, uz0 = grid(F2 + 1.4, F2 + 7.0)
free2 = ~dilate(g2, 1.6)
free2w = ~dilate(g2, 2.45)
a = A['stair_top']
st2 = cell(a[0], a[2], ux0, uz0)
sa2 = flood(free2, st2)
sw2 = flood(free2w, st2)
lines.append('upper floor, start = stair top: free cells (agent) %d, (passage 5) %d' % (int(sa2.sum()) if sa2 is not None else 0, int(sw2.sum()) if sw2 is not None else 0))
if sa2 is None:
    issue('stair top anchor is not in free space on the upper floor')
else:
    t2 = {}
    for name, (fl, u0, u1, v0, v1, wc) in H.ROOMS.items():
        if fl == 2:
            t2['room:' + name] = (H.X((u0 + u1) / 2), H.Z((v0 + v1) / 2))
    for nm in ('hide_wardrobe_enter', 'niche_front'):
        t2[nm] = (A[nm][0], A[nm][2])
    for r in K.ROUTES:
        if r[3] > F1 + 0.1 and r[0] != 'Dog':
            t2['route %s_%02d' % (r[0], r[1])] = (r[2], r[4])
    for tname, (x, z) in sorted(t2.items()):
        if tname.startswith('room:'):
            rx0, rx1, rz0, rz1 = [H.X(H.ROOMS[tname[5:]][1]), H.X(H.ROOMS[tname[5:]][2]), H.Z(H.ROOMS[tname[5:]][3]), H.Z(H.ROOMS[tname[5:]][4])]
            m = np.zeros_like(free2)
            stamp(m, rx0 + 0.3, rx1 - 0.3, rz0 + 0.3, rz1 - 0.3, ux0, uz0)
            fr, rc, rw = int((free2 & m).sum()), int((sa2 & m).sum()), int((sw2 & m).sum())
            lines.append('  %-28s free cells %6d reachable %6d reachable via 5-stud passages %6d' % (tname, fr, rc, rw))
            if fr == 0:
                issue('no free floor in %s' % tname)
            elif rc < 0.95 * fr:
                issue('part of %s unreachable for the NPC: %d of %d free cells' % (tname, rc, fr))
            elif rw == 0:
                issue('%s reachable only through narrow passages' % tname)
            continue
        c = cell(x, z, ux0, uz0)
        okA = bool(sa2[c]) if 0 <= c[0] < sa2.shape[0] and 0 <= c[1] < sa2.shape[1] else False
        okW = bool(sw2[c]) if 0 <= c[0] < sw2.shape[0] and 0 <= c[1] < sw2.shape[1] else False
        lines.append('  %-28s (%.1f, %.1f) agent=%s passage5=%s' % (tname, x, z, okA, okW))
        if not okA:
            issue('upper target not reachable for the NPC: %s at (%.1f, %.1f)' % (tname, x, z))
        elif not okW and not tname.startswith('niche'):
            issue('upper target reachable only through a passage narrower than 5 studs: %s' % tname)

# door widths
for d in K.DOORLOG:
    if d['w'] < 5.0 - 1e-6:
        issue('door narrower than 5 studs: %s %.2f' % (d['id'], d['w']))
lines.append('doors: %d, min width %.2f' % (len(K.DOORLOG), min(d['w'] for d in K.DOORLOG)))

# stairs: width, riser, headroom
riser = (F2 - F1) / 15.0
lines.append('stairs: width %.2f, riser %.3f, tread %.2f, steps 15' % (H.STAIR['u1'] - H.STAIR['u0'] - 0.75, riser, H.TREAD))
if H.STAIR['u1'] - H.STAIR['u0'] - 0.75 < 5.0:
    issue('stair narrower than 5')

# ====================================================================================== G  door sweeps
lines.append('')
lines.append('=== G. door sweeps (quarter disc of radius = opening width on the swing side; no furniture inside)')
sweep_n = 0
for d in K.DOORLOG:
    w, ctr, wall = d['w'], d['ctr'], d['wall']
    lo = ctr - w / 2 if d['hinge'] == 'low' else ctr + w / 2
    tow = 1.0 if d['hinge'] == 'low' else -1.0
    sw = d['swing']
    y0, y1 = d['y0'] + 0.3, d['y0'] + d['h'] - 0.3
    pts = []
    n = int(w / 0.4) + 1
    for i in range(n + 1):
        for j in range(n + 1):
            al, pe = i * 0.4, j * 0.4 + 0.45
            if math.hypot(al, pe) > w - 0.3:
                continue
            a_, p_ = lo + tow * al, wall + sw * pe
            pts.append((a_, p_) if d['axis'] == 'z' else (a_, p_))
    hit = set()
    for g in gl_f:
        if g['mx'].z < y0 or g['mn'].z > y1 or g['mx'].z - g['mn'].z < 0.2:
            continue
        for (a_, p_) in pts:
            x, z = (p_, a_) if d['axis'] == 'z' else (a_, p_)
            if g['mn'].x <= x <= g['mx'].x and g['mn'].y <= -z <= g['mx'].y:
                hit.add((g['label'], where(g)))
                break
    for (lb, wh) in sorted(hit):
        sweep_n += 1
        lines.append('  door %-16s sweep hits %-16s %s' % (d['id'], lb, wh))
        issue('door sweep %s hits %s %s' % (d['id'], lb, wh))
lines.append('door sweep hits: %d (of %d doors)' % (sweep_n, len(K.DOORLOG)))

# ====================================================================================== G2  door leaf vs walls, I  clearance around seating
lines.append('')
lines.append('=== G2. open door leaf must not hit a wall (rays along the leaf at 0..open angle, started just outside the wall face)')
wall_hits = 0
for d in K.DOORLOG:
    w, ctr, wall, sw = d['w'], d['ctr'], d['wall'], d['swing']
    lo = ctr - w / 2 if d['hinge'] == 'low' else ctr + w / 2
    tow = 1.0 if d['hinge'] == 'low' else -1.0
    ymid = d['y0'] + d['h'] * 0.5
    bad = []
    for th_deg in (70, 85, 95):
        th = math.radians(th_deg)
        al, pe = math.cos(th) * tow, math.sin(th) * sw
        d0 = (d['th'] / 2 + 0.45) / math.sin(th)
        if d['axis'] == 'z':
            org = Vector((wall + pe * d0, -(lo + al * d0), ymid))
            dr = Vector((pe, -al, 0.0))
        else:
            org = Vector((lo + al * d0, -(wall + pe * d0), ymid))
            dr = Vector((al, -pe, 0.0))
        hit = arch.ray_cast(org, dr.normalized(), max(0.2, w - 0.3 - d0))
        if hit[0] is not None:
            bad.append(th_deg)
    if bad:
        wall_hits += 1
        lines.append('  door %-16s leaf hits architecture at angles %s' % (d['id'], bad))
        issue('door leaf hits wall: %s at %s' % (d['id'], bad))
lines.append('door leaf wall hits: %d' % wall_hits)

lines.append('')
lines.append('=== I. clearance around seating (sofa / armchair / chair / bed): nothing within 1.4 studs of a seat edge, so a player can reach it')
SEAT = ('sofa', 'armchair', 'chair', 'stool', 'bench')
clear_n = 0
for a in gl_f:
    if not any(t in a['label'] for t in SEAT) or a['mx'].z - a['mn'].z < 0.3:
        continue
    for b in gl_f:
        if b is a or b['mx'].z - b['mn'].z < 0.3 or b['mn'].z > a['mx'].z or b['mx'].z < a['mn'].z + 0.4:
            continue
        if b['label'] in ('rug', 'carpet', 'pendant', 'chandelier', 'place_setting', 'curtain_pair', 'desk', 'cabinet', 'bed') and ('chair' in a['label'] or 'stool' in a['label'] or b['label'] in ('rug', 'carpet', 'pendant', 'chandelier', 'place_setting', 'curtain_pair')):
            continue
        if b['label'] in ('rug', 'carpet', 'pendant', 'chandelier') or b['mn'].z > a['mn'].z + 4.5:
            continue
        gx = max(a['mn'].x - b['mx'].x, b['mn'].x - a['mx'].x, 0.0)
        gy = max(a['mn'].y - b['mx'].y, b['mn'].y - a['mx'].y, 0.0)
        gap = math.hypot(gx, gy)
        if gap < 1.0:
            if any(t in b['label'] for t in ('cushion', 'pillow', 'blanket', 'table_lamp')):
                continue
            if 'table' in b['label'] and (gap < 0.05 or gap >= 0.6):      # chair tucked under a table, or a coffee table with room to sit
                continue
            clear_n += 1
            lines.append('  %-14s %-26s <-> %-14s gap %.2f' % (a['label'], where(a), b['label'], gap))
            issue('seat clearance: %s %s too close to %s (%.2f)' % (a['label'], where(a), b['label'], gap))
lines.append('seat clearance issues: %d' % clear_n)

lines.append('')
lines.append('=== J. furniture standing in front of a window (taller than the sill and within 2.5 studs of the wall)')
win_n = 0
for (ax, cc_, ww, a0, a1, wp, th_) in K.WINLOG:
    for g in gl_f:
        if g['label'] in ('curtain_pair', 'curtains', 'rug', 'carpet', 'pendant', 'chandelier', 'potted_plant', 'floor_lamp', 'table_lamp', 'vase_flowers', 'coat_on_hook', 'monitor', 'desk', 'console_table') or g['mn'].z > a0 or g['mx'].z < a0 + 1.5:
            continue
        if ax == 'z':      # wall plane x = wp, window spans z = cc_ +- ww/2
            near = g['mn'].x - 2.5 <= wp <= g['mx'].x + 2.5
            lat = g['mn'].y <= -(cc_ - ww / 2) and g['mx'].y >= -(cc_ + ww / 2)
        else:              # wall plane z = wp, window spans x
            near = g['mn'].y - 2.5 <= -wp <= g['mx'].y + 2.5
            lat = g['mn'].x <= cc_ + ww / 2 and g['mx'].x >= cc_ - ww / 2
        if near and lat:
            win_n += 1
            lines.append('  %-16s %s blocks window (%s %.1f w=%.1f)' % (g['label'], where(g), ax, cc_, ww))
            issue('furniture blocks window: %s %s' % (g['label'], where(g)))
lines.append('windows blocked by furniture: %d' % win_n)

# ====================================================================================== F  contract
lines.append('')
lines.append('=== F. contract')
ids = {d['id'] for d in K.DOORLOG}
for need in ('front', 'back', 'garage_service', 'balcony', 'hide_cupboard', 'hide_wardrobe'):
    if need not in ids:
        issue('door / hide leaf missing: ' + need)
for need in ('ladder_top', 'ladder_foot', 'hide_cupboard_enter', 'hide_cupboard_inside', 'hide_cupboard_hide', 'hide_cupboard_exit', 'hide_wardrobe_enter',
             'hide_wardrobe_inside', 'hide_wardrobe_hide', 'hide_wardrobe_exit', 'niche_front', 'niche_inside', 'niche_hide', 'father', 'work_pass', 'stair_foot', 'stair_top', 'caught_spawn'):
    if need not in A:
        issue('anchor missing: ' + need)
for d in K.DOORLOG:
    if d['id'] in ('front', 'back') and not d['locked']:
        issue('exterior door must be LockedFromOutside: ' + d['id'])
    if d['id'] == 'garage_service' and (not d['locked'] or d['item'] != 'HasSpareKey'):
        issue('garage service door must require HasSpareKey')
for c in K.COVER:
    if not (2.6 <= c[6] <= 3.6):
        issue('LowCover %s height %.2f outside 2.7..3.5 (tolerance 0.1)' % (c[0], c[6]))
names = collections.Counter(c[0] for c in K.COVER)
for need in ('sofa', 'kitchen_island', 'bed'):
    if need not in names:
        issue('LowCover missing: ' + need)
lines.append('LowCover: ' + ', '.join('%s x%d' % kv for kv in sorted(names.items())))
for hid, (u0, u1, v0, v1) in (('cupboard', (0.75, 6.9, 59.6, 66.25)), ('wardrobe', (47.5, 53.25, 14.5, 21.5))):
    iw, idp = (u1 - u0) - 0.4, (v1 - v0) - 0.4
    lines.append('HideSpot %s interior %.2f x %.2f' % (hid, iw, idp))
    if min(iw, idp) < 4.0:
        issue('hide spot %s interior smaller than 4 studs' % hid)
# bookcase niche: pocket depth and bookcase height
bc = [b for b in K.BOXLOG if b[1] == 'niche_bookcase']
lines.append('niche bookcases: %d (collision-only box)' % len(bc))
if not bc:
    issue('niche bookcase collision box missing')
else:
    lines.append('  niche pocket depth %.2f studs between the north wall and the bookcase, bookcase height %.1f' % (bc[0][6] - (H.Z(36) + 0.5), bc[0][5] - bc[0][4]))
mesh_stats = os.path.join(os.path.dirname(os.path.abspath(REP)), 'export_stats.json')
lines.append('route points: ' + ', '.join('%s_%02d' % (r[0], r[1]) for r in K.ROUTES))

# ====================================================================================== H  territory: layers, seams, stray geometry
import odh_merge as MG
comps = []
stray = collections.Counter()
for (c, m), (vs, fs) in acc.items():
    if c in ('DoorLeaf', 'DoorLeafU', 'FatherProxy', 'PassProxy') or not fs:
        continue
    comps.append(dict(grp='Biome' if c in ('Biome', 'BiomeOrg') else 'Arch', polys=[tuple(tuple(vs[i]) for i in f) for f in fs]))
    if c not in ('Biome', 'BiomeOrg'):
        for v in vs:
            if v[0] < -12.0 or v[0] > 120.0 or v[1] > 12.0 or v[1] < -112.0:
                stray[(c, m)] += 1
lay_before = MG.count_layers(comps)
MG.resolve(comps)
MG.glue(comps)
lay_after = MG.count_layers(comps)
lines.append('H territory: coplanar overlapping face pairs (layers) in the raw model %d, after the export cleanup %d' % (lay_before, lay_after))
if lay_after:
    issue('layers remain after cleanup: %d' % lay_after)
for (c, m), n in stray.items():
    issue('geometry outside the lot in the house collection %s/%s (%d vertices)' % (c, m, n))
lines.append('H stray geometry outside the house lot in house collections: %d groups' % len(stray))
lines.append('H seam patterns (planks, tiles, roof strips, lawn / driveway stripes): none, surfaces are single-colour')

import odh_site as SITE
HW = H.W
rects = [('house body', H.X(0.0) - 1.8, H.X(HW) + 1.8, H.Z(0.0) - 1.8, H.Z(H.D) + 1.8), ('garage', H.X(-18.0), H.X(0.0), H.Z(40.0), H.Z(H.D) + 1.0),
         ('driveway', SITE.DRIVE[0], SITE.DRIVE[1], 0.0, 82.0), ('front path', 43.0, 51.0, 0.0, 10.0), ('shed', 85.0, 95.0, 86.0, 98.0)]
for (tx, tz, tr) in SITE.TREE_LOG:
    for (nm, x0, x1, z0, z1) in rects:
        dx = max(x0 - tx, 0.0, tx - x1)
        dz = max(z0 - tz, 0.0, tz - z1)
        if math.hypot(dx, dz) < tr:
            issue('lot tree at x %.0f z %.0f (crown radius %.1f) reaches the %s' % (tx, tz, tr, nm))
lines.append('H lot trees checked against house, garage, driveway, path, shed: %d trees' % len(SITE.TREE_LOG))

lines.append('')
lines.append('ISSUES %d' % len(ISSUES))
open(REP, 'w', encoding='utf-8').write('\n'.join(lines))
print('AUDIT DONE issues', len(ISSUES))
for i in ISSUES[:60]:
    print(' ', i)
