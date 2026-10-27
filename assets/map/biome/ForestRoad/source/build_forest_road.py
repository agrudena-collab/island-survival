# Forest road between the mistress district and the father district (Blender, run through Blender MCP or `blender -b --python`).
# Design: the owner-approved sketch (artifact "Дорога между районами: эскиз"): winding road with a fork towards two reserved plots
# for future father districts; road length is tuned so a car of 24 stud/s needs 5:00 and a car of 60 stud/s needs 2:00.
# Coordinates are STUDIO-LIKE (x east, y up, z south) as in the district generator; converted to Blender (x, -z, y) at write time.
# Output: out/ForestRoad.fbx (road/gate/sign chunks O_*, tree templates T_*), out/forest_road.json (colliders, walls, trees, signs, anchors),
# out/renders/*.png (Workbench previews with all trees instanced).
import math
import os
import sys
import json
import random
import time

import bpy
import bmesh
from mathutils import Vector

ROOT = os.environ.get('FOREST_ROOT', r'C:\Users\agrud\Documents\RobloxProjects\MyRobloxGame\assets\map\biome\ForestRoad')
DLIB = r'C:\Users\agrud\Documents\RobloxProjects\MyRobloxGame\assets\map\district\RegularDadDistrict\source'
OUT = os.path.join(ROOT, 'out')
os.makedirs(os.path.join(OUT, 'renders'), exist_ok=True)
if DLIB not in sys.path:
    sys.path.insert(0, DLIB)
import importlib
import dlib as D
importlib.reload(D)

T0 = time.time()
GY = 1.0                    # walking height of both districts
XA, XB = 250.0, 5550.0
DISTRICT_EDGE_X = 226.0     # end of the district ground and avenues      # gate A (district edge) and gate B (father district west edge)
TARGET_LEN = 7200.0         # 24 stud/s * 300 s
K_WAVES = 3.5
STEP = 6.0                  # sampling step of the road, studs
ASPHALT_HALF, SHOULDER_HALF, VERGE_HALF = 12.0, 14.0, 20.0
FOREST_HALF, WALL_HALF = 105.0, 110.0
CHUNK_SEGS = 40

C = dict(asphalt='#3E4147', line='#F2E9C9', shoulder='#A89F8C', verge='#B7D79B', grass='#86B96A',
         trunk='#6B4A33', birch='#E9E4D6', birch_mark='#3A3A3A', stone='#8A8F99', wood='#6B4A33', board='#2F6B4A', sign='#F2E9C9')

# ------------------------------------------------------------------ path
def win(t):
    return min(1.0, 6 * t, 6 * (1 - t))


def main_pts(A, n=360):
    return [(XA + (i / n) * (XB - XA), A * math.sin(2 * math.pi * K_WAVES * (i / n)) * win(i / n)) for i in range(n + 1)]


def plen(pts):
    return sum(math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]) for i in range(1, len(pts)))


lo, hi = 0.0, 1500.0
for _ in range(40):
    mid = (lo + hi) / 2
    if plen(main_pts(mid)) < TARGET_LEN:
        lo = mid
    else:
        hi = mid
AMP = (lo + hi) / 2
coarse = main_pts(AMP)
fi = round(0.7 * (len(coarse) - 1))
FORK = coarse[fi]


def bez(a, b, c, n):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u * u * a[0] + 2 * u * t * b[0] + t * t * c[0], u * u * a[1] + 2 * u * t * b[1] + t * t * c[1]))
    return out


N_END = (FORK[0] - 80, FORK[1] - 800)
S_END = (FORK[0] + 90, FORK[1] + 800)
coarse_n = bez(FORK, (FORK[0] - 220, FORK[1] - 400), N_END, 160)
coarse_s = bez(FORK, (FORK[0] + 240, FORK[1] + 400), S_END, 160)


def resample(pts, step):
    out = [pts[0]]
    acc = 0.0
    for i in range(1, len(pts)):
        a, b = pts[i - 1], pts[i]
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        d = step - acc
        while d <= seg:
            t = d / seg
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
            d += step
        acc = seg - (d - step)
    if math.hypot(out[-1][0] - pts[-1][0], out[-1][1] - pts[-1][1]) > 0.5:
        out.append(pts[-1])
    return out


PATHS = {'main': resample(coarse, STEP), 'north': resample(coarse_n, STEP), 'south': resample(coarse_s, STEP),
         'connector': resample([(DISTRICT_EDGE_X, 0.0), (XA, 0.0)], STEP)}   # district avenue end (x 226) -> start of the winding road
LEN = {k: plen(v) for k, v in PATHS.items()}


def normals(pts):
    ns = []
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        dx, dz = b[0] - a[0], b[1] - a[1]
        l = math.hypot(dx, dz) or 1.0
        ns.append((-dz / l, dx / l))   # left-hand normal in (x, z) plane
    return ns


NORM = {k: normals(v) for k, v in PATHS.items()}

# ------------------------------------------------------------------ road geometry (closed slabs so normals recalc consistently)
def slab(pa, na, pb, nb, h0, h1, y_top, thick, col):
    """Closed prism between two cross sections: offsets h0..h1 across the road (left normal positive)."""
    ax0 = (pa[0] + na[0] * h0, pa[1] + na[1] * h0)
    ax1 = (pa[0] + na[0] * h1, pa[1] + na[1] * h1)
    bx0 = (pb[0] + nb[0] * h0, pb[1] + nb[1] * h0)
    bx1 = (pb[0] + nb[0] * h1, pb[1] + nb[1] * h1)
    ring = [ax0, ax1, bx1, bx0]
    yb = y_top - thick
    v = [(x, yb, z) for (x, z) in ring] + [(x, y_top, z) for (x, z) in ring]
    D._add('O', v, D._BOXF, col)


def build_road(name, pts, ns, skip_dash_near=None):
    for i in range(len(pts) - 1):
        pa, pb, na, nb = pts[i], pts[i + 1], ns[i], ns[i + 1]
        slab(pa, na, pb, nb, -VERGE_HALF, VERGE_HALF, GY + 0.03, 0.3, C['verge'])
        slab(pa, na, pb, nb, -SHOULDER_HALF, SHOULDER_HALF, GY + 0.06, 0.3, C['shoulder'])
        slab(pa, na, pb, nb, -ASPHALT_HALF, ASPHALT_HALF, GY + 0.09, 0.3, C['asphalt'])
        if i % 3 == 0:
            mx, mz = (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2
            if skip_dash_near and any(math.hypot(mx - q[0], mz - q[1]) < 34 for q in skip_dash_near):
                continue
            # dash 3 studs long, 0.5 wide, centred on the axis
            slab(pa, na, pb, nb, -0.25, 0.25, GY + 0.12, 0.2, C['line'])


build_road('main', PATHS['main'], NORM['main'], skip_dash_near=[FORK])
build_road('north', PATHS['north'], NORM['north'], skip_dash_near=[FORK])
build_road('south', PATHS['south'], NORM['south'], skip_dash_near=[FORK])
build_road('connector', PATHS['connector'], NORM['connector'])
# big ground sheet, visual only (walls keep players inside the corridor)
# (tiles of at most ~1000 studs: Roblox parts cannot exceed 2048 studs per axis)
_gx = DISTRICT_EDGE_X
while _gx < XB + 6:
    _gx1 = min(_gx + 1000.0, XB + 6)   # last tile ends 6 studs behind gate B
    for _gz in (-1560.0, -520.0, 520.0):
        D.box(_gx, _gx1, GY - 1.0, GY, _gz, _gz + 1040.0, C['grass'])
        D.collider(_gx, _gx1, GY - 5.0, GY, _gz, _gz + 1040.0, 'ForestGround')
    _gx = _gx1

# ------------------------------------------------------------------ gates and signpost
SIGNS = []


def gate(x, face, text, name):
    # arch over the road: two pillars outside the shoulders, beam, board; `face` = 'W' (visible from the west) or 'E'
    for sgn in (-1, 1):
        z = sgn * (SHOULDER_HALF + 4.0)
        D.box(x - 2.5, x + 2.5, GY, GY + 17, z - 2.5, z + 2.5, C['stone'])
        D.box(x - 3.0, x + 3.0, GY + 17, GY + 18.2, z - 3.0, z + 3.0, D.shade(C['stone'], 0.12))
        D.collider(x - 2.5, x + 2.5, GY, GY + 17, z - 2.5, z + 2.5, name + '_pillar')
    D.box(x - 2.0, x + 2.0, GY + 17.2, GY + 19.4, -(SHOULDER_HALF + 6.5), SHOULDER_HALF + 6.5, C['wood'])
    D.box(x - 2.3, x + 2.3, GY + 12.5, GY + 17.0, -(ASPHALT_HALF + 4), ASPHALT_HALF + 4, C['board'])
    SIGNS.append(dict(text=text, x=x + (-2.4 if face == 'W' else 2.4), y=GY + 14.8, z=0.0, w=(ASPHALT_HALF + 4) * 2 - 1, h=4.0, face=face))
    D.anchor(name, x, GY, 0.0, 1.0, 0.0)


gate(XA + 14, 'W', 'CITY DISTRICT', 'GateA')
gate(XB - 14, 'E', "REGULAR DAD'S", 'GateB')

# signpost at the fork on the outside of the main bend (Regular Dad -> east; two reserved plots -> SOON)
# free corner of the junction: nearest point on a circle around the fork that keeps >= 20 studs from every road centre line
_allp = [p for pts in PATHS.values() for p in pts]
px = pz = None
for rad in (34, 40, 46, 54):
    for k in range(48):
        ang = 2 * math.pi * k / 48
        cx, cz = FORK[0] + rad * math.cos(ang), FORK[1] + rad * math.sin(ang)
        if min(math.hypot(cx - q[0], cz - q[1]) for q in _allp) >= 20.0:
            px, pz = cx, cz
            break
    if px is not None:
        break
D.box(px - 0.5, px + 0.5, GY, GY + 11, pz - 0.5, pz + 0.5, C['wood'])
D.collider(px - 0.5, px + 0.5, GY, GY + 11, pz - 0.5, pz + 0.5, 'ForkPost')
for k, (txt, off, yaw) in enumerate((("REGULAR DAD'S", 0, 0), ('SOON', 2.0, 55), ('SOON', 4.0, -55))):
    D.cbox(px, GY + 9.2 - k * 2.0, pz, 8.0, 1.5, 0.3, C['sign'], rot=yaw if False else 0)
    SIGNS.append(dict(text=txt, x=px, y=GY + 9.2 - k * 2.0, z=pz + 0.2, w=7.6, h=1.3, face='S'))
D.anchor('Fork', FORK[0], GY, FORK[1], 1.0, 0.0)
D.anchor('PlotNorthEntry', N_END[0], GY, N_END[1], 0.0, -1.0)
D.anchor('PlotSouthEntry', S_END[0], GY, S_END[1], 0.0, 1.0)
D.anchor('RoadStartA', XA, GY, 0.0, 1.0, 0.0)
D.anchor('RoadEndB', XB, GY, 0.0, 1.0, 0.0)

ROAD_ITEMS = D.ITEMS['O']
D.ITEMS['O'] = []

# ------------------------------------------------------------------ tree templates (origin at the foot)
TEMPLATES = {}


def finish(name):
    TEMPLATES[name] = D.ITEMS['O']
    D.ITEMS['O'] = []


def pine(name, layers, trunk_h, seed):
    D.cyl(0, 0, 0, trunk_h, 1.1, C['trunk'], seg=6)
    greens = ['#2F6B4A', '#3A7652', '#46825B', '#528E64', '#5E9A70']
    for i, (y0, y1, r) in enumerate(layers):
        D.cyl(0, 0, y0, y1, r, greens[min(i, 4)], seg=7, r2=0.0)
    finish(name)


pine('T_pine_tall', [(4, 11, 6.5), (9, 17, 5.2), (14, 23, 4.0), (19, 29, 2.6)], 6, 1)
pine('T_pine_short', [(3, 8.5, 5.6), (7, 13.5, 4.2), (11, 18, 2.8)], 4, 2)
D.cyl(0, 0, 0, 9, 1.5, C['trunk'], seg=7)
D.sphere(0, 12.5, 0, 7.0, 6.0, 7.0, '#6FA659', seg=9, rings=6, jitter=0.12, seed=3)
D.sphere(-3.6, 10.0, 2.0, 5.0, 4.2, 5.0, '#5A9048', seg=8, rings=5, jitter=0.12, seed=4)
D.sphere(3.4, 14.8, -1.8, 4.6, 4.0, 4.6, '#86B96A', seg=8, rings=5, jitter=0.12, seed=5)
finish('T_oak')
D.cyl(0, 0, 0, 12, 0.9, C['birch'], seg=6)
for h in (2.5, 5.0, 7.8, 10.2):
    D.cyl(0, 0, h, h + 0.5, 0.96, C['birch_mark'], seg=6)
D.sphere(0, 14.5, 0, 4.4, 5.6, 4.4, '#9BC878', seg=8, rings=6, jitter=0.1, seed=6)
D.sphere(1.8, 11.6, 1.2, 3.0, 3.0, 3.0, '#86B96A', seg=7, rings=4, jitter=0.1, seed=7)
finish('T_birch')
D.sphere(0, 1.8, 0, 3.2, 2.4, 3.2, '#4F8D66', seg=8, rings=5, jitter=0.15, seed=8)
D.sphere(2.4, 1.2, 1.4, 2.2, 1.7, 2.2, '#6FA659', seg=7, rings=4, jitter=0.15, seed=9)
D.sphere(-2.0, 1.3, -1.3, 2.0, 1.6, 2.0, '#3F7A57', seg=7, rings=4, jitter=0.15, seed=10)
finish('T_bush')

# ------------------------------------------------------------------ forest placement
# father district = the house model's footprint (ground sheet x -70..179, z -61..173) shifted so its street starts at gate B
DISTRICTS = [(-258, 258, -258, 258), (XB - 4, XB + 260, -200, 66),
             (N_END[0] - 128, N_END[0] + 128, N_END[1] - 250, N_END[1] + 8),
             (S_END[0] - 128, S_END[0] + 128, S_END[1] - 8, S_END[1] + 250)]
ALLPTS = [(name, p) for name, pts in PATHS.items() for p in pts]
BUCKET = 120
hashed = {}
for name, p in ALLPTS:
    hashed.setdefault((int(p[0] // BUCKET), int(p[1] // BUCKET)), []).append((name, p))


def nearest(x, z, skip=None):
    bi, bj = int(x // BUCKET), int(z // BUCKET)
    best, who = 1e9, None
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for name, p in hashed.get((bi + di, bj + dj), ()):
                if skip and name == skip:
                    continue
                d = math.hypot(p[0] - x, p[1] - z)
                if d < best:
                    best, who = d, name
    return best, who


rnd = random.Random(20261027)
CELL = 300 ** 0.5   # one tree per 300 studs^2
CROWN = {'T_pine_tall': 6.5, 'T_pine_short': 5.6, 'T_oak': 8.5, 'T_birch': 5.2, 'T_bush': 4.4}   # crown radius at scale 1
TRUNK = {'T_pine_tall': 1.1, 'T_pine_short': 1.1, 'T_oak': 1.5, 'T_birch': 0.9, 'T_bush': 0.0}
# footprints of the gates (pillars, caps, beam) and the fork signpost: a crown must not reach them
GATE_BOXES = [(g - 3.6, g + 3.6, -(SHOULDER_HALF + 8), SHOULDER_HALF + 8) for g in (XA + 14, XB - 14)]
POST = (px, pz)
trees, trunks = [], []
th = {}                      # trunk spacing hash
removed = {'near-gate-or-post': 0, 'trunk-spacing': 0}
gx0, gx1 = int((XA - 120) // CELL), int((XB + 120) // CELL)
gz0, gz1 = int(-1400 // CELL), int(1400 // CELL)
for gi in range(gx0, gx1 + 1):
    for gj in range(gz0, gz1 + 1):
        x = (gi + 0.5 + rnd.uniform(-0.42, 0.42)) * CELL
        z = (gj + 0.5 + rnd.uniform(-0.42, 0.42)) * CELL
        if any(r[0] < x < r[1] and r[2] < z < r[3] for r in DISTRICTS):
            continue
        d, who = nearest(x, z)
        if d < VERGE_HALF + 2 or d > FOREST_HALF:
            continue
        near = d < 45
        u = rnd.random()
        if near:
            kind = 'T_bush' if u < 0.35 else ('T_birch' if u < 0.6 else ('T_oak' if u < 0.8 else 'T_pine_short'))
        else:
            kind = 'T_pine_tall' if u < 0.45 else ('T_pine_short' if u < 0.65 else ('T_oak' if u < 0.85 else 'T_birch'))
        s_ = rnd.uniform(0.8, 1.3)
        yaw_ = rnd.uniform(0, 360)
        cr, tr = CROWN[kind] * s_, TRUNK[kind] * s_
        # crown circle against the gate footprints and the signpost
        hit = any(b[0] - cr - 1 < x < b[1] + cr + 1 and b[2] - cr - 1 < z < b[3] + cr + 1 for b in GATE_BOXES) or math.hypot(x - POST[0], z - POST[1]) < cr + 3
        if hit:
            removed['near-gate-or-post'] += 1
            continue
        # trunks must not touch: centre distance >= both trunk radii + 0.8 (crowns may overlap, as in a forest)
        ok = True
        kx, kz = int(x // 12), int(z // 12)
        for ax in (-1, 0, 1):
            for az in (-1, 0, 1):
                for (ox, oz, otr) in th.get((kx + ax, kz + az), ()):
                    if math.hypot(ox - x, oz - z) < otr + tr + 0.8 + (0 if tr and otr else 2.5):
                        ok = False
        if not ok:
            removed['trunk-spacing'] += 1
            continue
        th.setdefault((kx, kz), []).append((x, z, tr))
        trees.append([kind, round(x, 2), round(z, 2), round(yaw_, 1), round(s_, 2)])
        if d < 60 and kind != 'T_bush':
            trunks.append([round(x, 2), round(z, 2), round(1.3 * s_, 2)])

# trees whose trunk would stand in a branch-end cap wall (post filter, so nothing else changes)
CAP_LINES = [(N_END[0], N_END[1] + 9), (S_END[0], S_END[1] - 9)]
def _in_cap(x, z):
    return any(abs(x - cx) < WALL_HALF + 2 and abs(z - cz) < 5.5 for cx, cz in CAP_LINES)
removed_cap_trees = [[t[1], t[2]] for t in trees if _in_cap(t[1], t[2])]
trees = [t for t in trees if not _in_cap(t[1], t[2])]
trunks = [t for t in trunks if not _in_cap(t[0], t[1])]
removed['cap-wall'] = len(removed_cap_trees)

# invisible walls at +-WALL_HALF along each path; not where another branch (or a district) is closer than the wall
walls = []
for name, pts in PATHS.items():
    if name == 'connector':
        continue
    ns = NORM[name]
    for i in range(0, len(pts) - 1, 5):   # one wall every 30 studs
        pa, pb = pts[i], pts[min(i + 5, len(pts) - 1)]
        mx, mz = (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2
        yaw = math.degrees(math.atan2(pb[1] - pa[1], pb[0] - pa[0]))
        ln = math.hypot(pb[0] - pa[0], pb[1] - pa[1]) + 1.5
        for sgn in (-1, 1):
            n = ns[i]
            wx, wz = mx + n[0] * sgn * WALL_HALF, mz + n[1] * sgn * WALL_HALF
            d2, who = nearest(wx, wz, skip=name)
            if who is not None and d2 < WALL_HALF + 14:
                continue
            if any(r[0] - m < wx < r[1] + m and r[2] - m < wz < r[3] + m for r, m in zip(DISTRICTS, (0, 0, 30, 30))):
                continue
            walls.append([round(wx, 2), round(wz, 2), round(ln, 2), round(yaw, 2)])
# cap the two branch ends so players cannot leave through the reserved plots
for end, face in ((N_END, -1), (S_END, 1)):
    walls.append([round(end[0], 2), round(end[1] - face * 9, 2), 2 * WALL_HALF, 0.0, 'cap'])   # across the road end (long side along x), 9 studs short of the plot edge

# ------------------------------------------------------------------ audit: overlaps and layering (target: every count 0)
ISSUES = {}
def _count(name, n, sample=None):
    ISSUES[name] = (n, sample or [])


_tt, _hash = [], {}
for t in trees:
    _hash.setdefault((int(t[1] // 12), int(t[2] // 12)), []).append(t)
for t in trees:
    r1 = TRUNK[t[0]] * t[4]
    for ax in (-1, 0, 1):
        for az in (-1, 0, 1):
            for u in _hash.get((int(t[1] // 12) + ax, int(t[2] // 12) + az), ()):
                if u is t or (u[1], u[2]) <= (t[1], t[2]):
                    continue
                r2 = TRUNK[u[0]] * u[4]
                if r1 + r2 > 0 and math.hypot(u[1] - t[1], u[2] - t[2]) < r1 + r2 + 0.3:
                    _tt.append((t[1:3], u[1:3]))
_count('TRUNK-TRUNK', len(_tt), _tt[:3])
_tr = [t[1:3] for t in trees if nearest(t[1], t[2])[0] < SHOULDER_HALF + TRUNK[t[0]] * t[4] + 0.5]
_count('TRUNK-ON-ROAD', len(_tr), _tr[:3])
_cg = [t[1:3] for t in trees if any(b[0] - CROWN[t[0]] * t[4] < t[1] < b[1] + CROWN[t[0]] * t[4] and b[2] - CROWN[t[0]] * t[4] < t[2] < b[3] + CROWN[t[0]] * t[4] for b in GATE_BOXES)
       or math.hypot(t[1] - POST[0], t[2] - POST[1]) < CROWN[t[0]] * t[4] + 1]
_count('CROWN-IN-GATE-OR-POST', len(_cg), _cg[:3])
_td = [t[1:3] for t in trees if any(r[0] < t[1] < r[1] and r[2] < t[2] < r[3] for r in DISTRICTS)]
_count('TREE-IN-DISTRICT-OR-PLOT', len(_td), _td[:3])
_tc = [c[6] for c in D.STATS['colliders'] if c[6] != 'ForestGround' and any(abs(tk[0] - c[0]) < c[3] / 2 + tk[2] and abs(tk[1] - c[2]) < c[5] / 2 + tk[2] for tk in trunks)]
_count('TRUNK-COLLIDER-IN-GATE-COLLIDER', len(_tc), _tc[:3])
_wr = [w[:2] for w in walls if len(w) == 4 and min(math.hypot(q[0] - w[0], q[1] - w[1]) for _n, q in ALLPTS if abs(q[0] - w[0]) < 140 and abs(q[1] - w[1]) < 140) < SHOULDER_HALF + 8] if walls else []
_count('WALL-ON-ROAD', len(_wr), _wr[:3])
_wd = [w[:2] for w in walls if any(r[0] < w[0] < r[1] and r[2] < w[1] < r[3] for r in DISTRICTS)]
_wd += [w[:2] for w in walls if len(w) == 5 and any(r[2] < w[1] < r[3] and r[0] - 5 < w[0] + 110 and w[0] - 110 < r[1] + 5 for r in DISTRICTS[2:])]   # caps must stay outside the plot rectangles
_count('WALL-IN-DISTRICT-OR-PLOT', len(_wd), _wd[:3])
_gp = [c[6] for c in D.STATS['colliders'] if c[6].endswith('_pillar') and min(math.hypot(q[0] - c[0], q[1] - c[2]) for _n, q in ALLPTS if abs(q[0] - c[0]) < 60 and abs(q[1] - c[2]) < 60) < SHOULDER_HALF + 2.5]
_count('GATE-PILLAR-ON-ROAD', len(_gp), _gp[:3])
_levels = sorted({GY, GY + 0.03, GY + 0.06, GY + 0.09, GY + 0.12})
_zf = [1 for i in range(1, len(_levels)) if _levels[i] - _levels[i - 1] < 0.025]
_count('LAYER-GAP-TOO-SMALL', len(_zf))
_gs = [1 for c in D.STATS['colliders'] if c[6] == 'ForestGround' and c[0] - c[3] / 2 < DISTRICT_EDGE_X - 1e-6]
_count('GROUND-OVERLAPS-DISTRICT-GROUND', len(_gs))
_dup = len(trunks) - len({(t[0], t[1]) for t in trunks})
_count('DUPLICATE-TRUNK-COLLIDERS', _dup)
AUDIT_TXT = '\n'.join('%-34s %d %s' % (k, v[0], v[1] if v[0] else '') for k, v in ISSUES.items())
AUDIT_TXT += '\nremoved while placing: %s\ntrees %d trunk colliders %d walls %d' % (removed, len(trees), len(trunks), len(walls))
open(os.path.join(OUT, 'audit_forest.txt'), 'w', encoding='utf-8').write(AUDIT_TXT + '\n')
print('AUDIT\n' + AUDIT_TXT)

print('PATH lengths',{k: round(v) for k, v in LEN.items()}, 'AMP', round(AMP, 1), 'trees', len(trees), 'trunks', len(trunks), 'walls', len(walls))

# ------------------------------------------------------------------ Blender objects
scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
coll = bpy.data.collections.new('ForestRoad')
scene.collection.children.link(coll)


def lin(h):
    c = [v / 255.0 for v in D.hexc(h)]
    f = lambda x: x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), 1.0)


def make_object(name, verts, polys, cols, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x, -z, y) for (x, y, z) in verts], [], polys)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ca = me.color_attributes.new(name='Col', type='BYTE_COLOR', domain='CORNER')
    li = 0
    for pi, p in enumerate(me.polygons):
        c4 = lin(cols[pi])
        for _ in range(p.loop_total):
            ca.data[li].color = c4
            li += 1
        p.use_smooth = False
    ob = bpy.data.objects.new(name, me)
    ob.location = Vector((loc[0], -loc[2], loc[1]))
    coll.objects.link(ob)
    return ob


def merge(items):
    verts, polys, cols = [], [], []
    for (_, _, v, f, col) in items:
        base = len(verts)
        verts.extend(v)
        for p in f:
            polys.append(tuple(base + i for i in p))
            cols.append(col)
    return verts, polys, cols


made = []
tris_total = 0
# road, gates, signpost: chunk by 48 stud cells; a chunk never exceeds 9000 triangles
cells = {}
for it in ROAD_ITEMS:
    cells.setdefault((int(it[0] // 48), int(it[1] // 48)), []).append(it)
MAXT = 9000
for (ci, cj), items in sorted(cells.items()):
    group, tris, gi = [], 0, 0
    for it in items:
        t = sum(len(p) - 2 for p in it[3])
        if tris + t > MAXT and group:
            made.append(make_object('O_%d_%d_%d' % (ci + 20, cj + 40, gi), *merge(group)))
            group, tris, gi = [], 0, gi + 1
        group.append(it)
        tris += t
    if group:
        made.append(make_object('O_%d_%d_%d' % (ci + 20, cj + 40, gi), *merge(group)))
road_chunks = len(made)
# tree templates in a row south of everything (Studio script moves them into a template folder)
tpl_objs = {}
for i, (name, items) in enumerate(TEMPLATES.items()):
    ob = make_object(name, *merge(items), loc=(i * 40.0, 0, 2000.0))
    made.append(ob)
    tpl_objs[name] = ob
for ob in made:
    tris_total += sum(len(p.vertices) - 2 for p in ob.data.polygons)
tpl_tris = {n: sum(len(p.vertices) - 2 for p in o.data.polygons) for n, o in tpl_objs.items()}
print('CHUNKS', len(made), 'road', road_chunks, 'TRIS', tris_total, 'templates', tpl_tris, 'elapsed %.1fs' % (time.time() - T0))

# ------------------------------------------------------------------ export
bpy.ops.object.select_all(action='DESELECT')
for o in made:
    o.select_set(True)
bpy.context.view_layer.objects.active = made[0]
FBX = os.path.join(OUT, 'ForestRoad.fbx')
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y',
                         mesh_smooth_type='FACE', use_mesh_modifiers=False, bake_anim=False, add_leaf_bones=False, path_mode='AUTO', embed_textures=False,
                         object_types={'MESH'}, colors_type='SRGB')
json.dump({
    'ground_top': GY, 'gate_a_x': XA, 'gate_b_x': XB, 'fork': [round(FORK[0], 2), round(FORK[1], 2)], 'amp': round(AMP, 2),
    'length': {k: round(v, 1) for k, v in LEN.items()},
    'paths': {k: [[round(x, 1), round(z, 1)] for (x, z) in v[::5]] for k, v in PATHS.items()},
    'colliders': D.STATS['colliders'], 'anchors': D.STATS['anchors'], 'signs': SIGNS,
    'trunks': trunks, 'walls': walls, 'trees': trees, 'removed_cap_trees': removed_cap_trees,
    'templates': {n: {'x': i * 40.0, 'z': 2000.0, 'tris': tpl_tris[n]} for i, n in enumerate(TEMPLATES)},
    'tris': tris_total, 'chunks': len(made),
}, open(os.path.join(OUT, 'forest_road.json'), 'w'))
print('EXPORTED', FBX)

# ------------------------------------------------------------------ preview renders (trees instanced from the templates)
prev = bpy.data.collections.new('Preview')
scene.collection.children.link(prev)
for k, (kind, x, z, yaw, s) in enumerate(trees):
    ob = bpy.data.objects.new('p%d' % k, tpl_objs[kind].data)
    ob.location = Vector((x, -z, 0))
    ob.rotation_euler = (0, 0, math.radians(yaw))
    ob.scale = (s, s, s)
    prev.objects.link(ob)

sc = scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
sh = sc.display.shading
sh.light, sh.color_type, sh.show_cavity = 'STUDIO', 'VERTEX', False
sh.studio_light = 'paint.sl'
sc.display_settings.display_device = 'sRGB'
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('W')
w.color = (0.62, 0.80, 0.96)
sc.world = w
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.clip_end = 20000


def shot(name, loc, target, lens=35, ortho=None):
    cam.location = Vector((loc[0], -loc[2], loc[1]))
    tgt = Vector((target[0], -target[2], target[1]))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    if ortho:
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = ortho
    else:
        cam.data.type = 'PERSP'
        cam.data.lens = lens
    sc.render.filepath = os.path.join(OUT, 'renders', name + '.png')
    bpy.ops.render.render(write_still=True)


mid = ((XA + XB) / 2, 0, 0)
shot('plan', (mid[0], 9000, 0.001), mid, ortho=6200)
shot('fork_aerial', (FORK[0] - 120, 90, FORK[1] + 160), (FORK[0], 4, FORK[1]), lens=32)
p = PATHS['main']
j = len(p) // 5
a = p[j]
b = p[j + 6]
shot('drive_view', (a[0], 7.5, a[1]), (b[0] + (b[0] - a[0]) * 8, 7, b[1] + (b[1] - a[1]) * 8), lens=28)
shot('gate_a', (XA - 70, 9, 28), (XA + 14, 12, 0), lens=30)
shot('gate_b', (XB - 70, 8, 2), (XB - 14, 12, 0), lens=30)
print('RENDERED elapsed %.1fs' % (time.time() - T0))
