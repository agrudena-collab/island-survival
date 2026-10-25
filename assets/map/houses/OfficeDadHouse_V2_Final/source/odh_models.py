"""OfficeDadHouse_V2_Final -- model library (furniture, kitchen/bath fixtures, yard, trees, car, shed, neighbour house).

Adapted copies of the generic model functions of RegularDadHouse_V2_Final (source/build_house_v5.py, yard_hq.py): same geometry code,
re-targeted to the Office Dad core (odh_core) through the thin wrappers below.  Colours are palette names / hex strings (P in odh_core).
Room layouts and every house-specific function are written fresh in odh_rooms.py / odh_site.py.
Local frame of every model: lx right, h up, lz forward (the model front looks along +lz).
"""
import math
import random as _random
from mathutils import Vector
import odh_core as K
from odh_core import P, emit, tf_push, tf_pop, _t, _TF, cover, anchor

COLL = K.COLL      # yard collision proxies (shared with the core) in world space: ('cyl', x, z, r, h) / ('box', x, z, sx, sz, h) / ('fence', x0, z0, x1, z1)


def MT(n):
    return n


def YM(name, hexcol=None, rough=0.7):
    return hexcol or name


def rbox(c, m, cx, cz, y0, sx, sy, sz, r=0.1, seg=3):
    K.rbox(m, cx, cz, y0, sx, sy, sz, r, seg, c=c)


def lathe(c, m, prof, cx, cz, y0=0.0, seg=24, sx=1.0, sz=1.0, caps=True):
    K.lathe(m, prof, cx, cz, y0, seg, sx, sz, caps, c=c)


def cylinder(c, m, cx, cz, y0, h, r, seg=20, r2=None):
    K.cyl(m, cx, cz, y0, h, r, seg, r2, c=c)


def sphere(c, m, cx, cz, cy, rx, ry=None, rz=None, seg=18, rings=10):
    K.sphere(m, cx, cz, cy, rx, ry, rz, seg, rings, c=c)


def tube(c, m, pts, r, seg=8, closed=False, caps=True, r_end=None):
    K.tube(m, pts, r, seg, closed, caps, r_end, c=c)


def torus(c, m, cx, cz, cy, R, r, plane='xz', seg=28, tseg=8):
    K.torus(m, cx, cz, cy, R, r, plane, seg, tseg, c=c)


def leaf(c, m, bx, bh, bz, ang, length, width, lift=0.6, droop=0.9, n=6):
    K.leaf(m, bx, bh, bz, ang, length, width, lift, droop, n, c=c)


def sheet(c, m, x0, x1, y0, y1, z, folds=6, amp=0.18, nx=40, axis='x'):
    K.sheet(m, x0, x1, y0, y1, z, folds, amp, nx, axis, c=c)


def _wpos():
    p = _t(0.0, 0.0, 0.0)
    return (p[0], p[2])


def _wcyl(lx, lz, r, h):
    p = _t(lx, 0.0, lz)
    COLL.append(('cyl', p[0], p[2], r, h))


def _wbox(lx, lz, sx, sz, h):
    p = _t(lx, 0.0, lz)
    if _TF and abs(_TF[-1][4]) > 0.5:
        sx, sz = sz, sx
    COLL.append(('box', p[0], p[2], sx, sz, h))


def curtain_pair(c, ac, wspan, y_top, drop, z, axis='x', col='coral', open_=True):
    """two curtains + rod + finials around a window centred at ac (plot coordinates, absolute)"""
    g = MT(col)
    x0, x1 = ac - wspan / 2, ac + wspan / 2
    if axis == 'x':
        tube(c, 'brass', [(x0 - 0.5, y_top, z), (x1 + 0.5, y_top, z)], 0.08, 8)
        for xx in (x0 - 0.55, x1 + 0.55):
            sphere(c, 'brass', xx, z, y_top, 0.2, 0.2, 0.2, 10, 6)
        sheet(c, g, x0 - 0.3, x0 + 1.5, y_top - drop, y_top - 0.12, z, folds=5, amp=0.16, axis='x')
        sheet(c, g, x1 - 1.5, x1 + 0.3, y_top - drop, y_top - 0.12, z, folds=5, amp=0.16, axis='x')
    else:
        tube(c, 'brass', [(z, y_top, x0 - 0.5), (z, y_top, x1 + 0.5)], 0.08, 8)
        for zz in (x0 - 0.55, x1 + 0.55):
            sphere(c, 'brass', z, zz, y_top, 0.2, 0.2, 0.2, 10, 6)
        sheet(c, g, x0 - 0.3, x0 + 1.5, y_top - drop, y_top - 0.12, z, folds=5, amp=0.16, axis='z')
        sheet(c, g, x1 - 1.5, x1 + 0.3, y_top - drop, y_top - 0.12, z, folds=5, amp=0.16, axis='z')


def sofa(c, w=8.6, d=3.5, col='sofa', col2='sofa2', pillows=('yellow', 'red', 'cream')):
    cover('sofa', w, d, 3.1)
    wd, dk = MT('wood2'), MT('dark')
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, wd, [(0.28, 0), (0.2, 0.25), (0.26, 0.5)], sx * (w / 2 - 0.5), sz * (d / 2 - 0.5), 0, 12)
    rbox(c, MT(col2), 0, 0, 0.5, w - 0.2, 0.75, d - 0.2, 0.18)
    arm = 1.0
    sw = (w - 2 * arm - 0.1) / 3.0
    for k in range(3):
        x = -w / 2 + arm + 0.05 + sw * (k + 0.5)
        rbox(c, MT(col), x, 0.35, 1.1, sw - 0.06, 1.0, d - 1.0, 0.34, 3)
        rbox(c, MT(col), x, -d / 2 + 0.95, 2.0, sw - 0.06, 2.0, 1.0, 0.4, 3)
    rbox(c, MT(col2), 0, -d / 2 + 0.35, 0.5, w, 3.1, 0.75, 0.3, 3)
    for sx in (-1, 1):
        rbox(c, MT(col2), sx * (w / 2 - arm / 2), 0, 0.5, arm, 2.25, d, 0.42, 3)
        cylinder(c, MT(col2), 0, 0, 0, 0.1, 0.1)
    for k, pc in enumerate(pillows):
        tf_push(-2.3 + k * 2.15, 0.15, 1.95, (-25, 12, -8)[k % 3])
        rbox(c, MT(pc), 0, 0, 0, 1.55, 1.55, 0.65, 0.5, 3)
        tf_pop()


def armchair(c, col='orange', col2='orange', w=3.9, d=3.7):
    cover('armchair', w, d, 3.2)
    wd = MT('wood2')
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, wd, [(0.26, 0), (0.18, 0.25), (0.24, 0.55)], sx * (w / 2 - 0.45), sz * (d / 2 - 0.45), 0, 12)
    rbox(c, MT(col2), 0, 0, 0.55, w - 0.2, 0.7, d - 0.2, 0.18)
    rbox(c, MT(col), 0, 0.3, 1.2, w - 1.7, 0.95, d - 1.0, 0.36, 3)
    rbox(c, MT(col), 0, -d / 2 + 0.7, 1.9, w - 1.2, 2.0, 1.1, 0.45, 3)
    rbox(c, MT(col2), 0, -d / 2 + 0.35, 0.55, w, 3.2, 0.75, 0.3, 3)
    for sx in (-1, 1):
        rbox(c, MT(col2), sx * (w / 2 - 0.42), 0.1, 0.55, 0.85, 1.9, d - 0.2, 0.38, 3)


def coffee_table(c, w=5.6, d=2.8, h=1.5):
    wd, w2 = MT('wood'), MT('wood2')
    rbox(c, w2, 0, 0, h - 0.28, w, 0.28, d, 0.12)
    rbox(c, wd, 0, 0, 0.45, w - 0.9, 0.14, d - 0.7, 0.05, 2)
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, wd, [(0.2, 0), (0.15, 0.4), (0.12, 0.8), (0.16, h - 0.28)], sx * (w / 2 - 0.45), sz * (d / 2 - 0.4), 0, 10)


def side_table(c, r=0.95, h=2.4):
    w2 = MT('wood2')
    lathe(c, w2, [(r, h - 0.18), (r, h), (0, h)], 0, 0, 0, 24)
    lathe(c, w2, [(0.1, h - 0.18), (0.18, h - 0.4), (0.1, h - 0.9), (0.28, h - 1.4), (0.14, 0.5), (0.5, 0.2), (0.7, 0.0)], 0, 0, 0, 16)


def table_lamp(c, h=2.0, shade=1.7, base='teal'):
    lathe(c, MT(base), [(0.0, 0), (0.55, 0.0), (0.7, 0.35), (0.62, 0.9), (0.3, 1.25), (0.16, 1.5), (0.1, 1.7)], 0, 0, 0, 20, caps=True)
    lathe(c, MT('lampshade'), [(0.62, 1.55), (shade * 0.5, 2.9)], 0, 0, 0, 24, caps=False)
    lathe(c, MT('lampshade'), [(shade * 0.5, 2.9), (0.62, 1.55)], 0, 0, 0, 24, caps=False)


def floor_lamp(c, h=5.6):
    lathe(c, MT('metal'), [(0.0, 0), (0.7, 0.0), (0.7, 0.12), (0.0, 0.14)], 0, 0, 0, 20)
    cylinder(c, MT('metal'), 0, 0, 0.1, h - 1.6, 0.09, 10)
    lathe(c, MT('lampshade'), [(0.9, h - 1.8), (0.55, h - 0.3)], 0, 0, 0, 24, caps=False)
    lathe(c, MT('lampshade'), [(0.55, h - 0.3), (0.9, h - 1.8)], 0, 0, 0, 24, caps=False)
    sphere(c, MT('lamp'), 0, 0, h - 1.1, 0.28, 0.35, 0.28, 12, 8)


def potted_plant(c, s=1.0, pot='terra', big=False, leaves=11, lcol=('leaf', 'leaf2')):
    lathe(c, MT(pot), [(0.0, 0), (0.55 * s, 0.0), (0.72 * s, 0.1 * s), (0.9 * s, 1.35 * s), (1.0 * s, 1.45 * s), (0.9 * s, 1.5 * s)], 0, 0, 0, 20)
    lathe(c, MT('soil'), [(0.82 * s, 1.35 * s), (0.0, 1.4 * s)], 0, 0, 0, 18)
    rnd = _random.Random(int(s * 100) + leaves)
    for k in range(leaves):
        a = 2 * math.pi * k / leaves + rnd.uniform(-0.2, 0.2)
        L = (1.55 if big else 1.15) * s * rnd.uniform(0.8, 1.15)
        leaf(c, MT(lcol[k % 2]), 0.15 * math.cos(a), 1.4 * s, 0.15 * math.sin(a), a, L, 0.8 * s * (1.3 if big else 1.0), 0.55 + 0.25 * rnd.random(), 0.9)


def mug(c, col='white', s=1.0):
    lathe(c, MT(col), [(0.0, 0), (0.28 * s, 0.0), (0.3 * s, 0.05 * s), (0.32 * s, 0.6 * s), (0.3 * s, 0.62 * s), (0.27 * s, 0.6 * s), (0.27 * s, 0.1 * s), (0.0, 0.08 * s)], 0, 0, 0, 16)
    tube(c, MT(col), [(0.3 * s, 0.5 * s, 0.0), (0.52 * s, 0.5 * s, 0.0), (0.58 * s, 0.35 * s, 0.0), (0.5 * s, 0.18 * s, 0.0), (0.3 * s, 0.14 * s, 0.0)], 0.045 * s, 6)


def vase_flowers(c, vcol='blue', n=7, h=1.3, fcols=('red', 'yellow', 'pink', 'orange')):
    lathe(c, MT(vcol), [(0.0, 0), (0.35, 0.0), (0.5, 0.25), (0.45, 0.7), (0.22, 1.05), (0.28, h), (0.2, h - 0.05), (0.18, h - 0.1)], 0, 0, 0, 16)
    rnd = _random.Random(n)
    for k in range(n):
        a = 2 * math.pi * k / n
        hx_, hz_ = 0.42 * math.cos(a) * rnd.uniform(0.5, 1.0), 0.42 * math.sin(a) * rnd.uniform(0.5, 1.0)
        top = h + 0.8 + rnd.uniform(0.0, 0.7)
        tube(c, MT('leaf'), [(0, h - 0.1, 0), (hx_ * 0.5, h + 0.4, hz_ * 0.5), (hx_, top, hz_)], 0.04, 5)
        sphere(c, MT(fcols[k % len(fcols)]), hx_, hz_, top + 0.12, 0.23, 0.18, 0.23, 10, 6)
        sphere(c, MT('yellow'), hx_, hz_, top + 0.2, 0.09, 0.07, 0.09, 8, 5)


def plate(c, col='white', r=0.62):
    lathe(c, MT(col), [(0.0, 0.0), (r * 0.55, 0.0), (r, 0.12), (r * 1.0, 0.16), (r * 0.62, 0.05), (0.0, 0.04)], 0, 0, 0, 22)


def glass_cup(c, h=0.75, r=0.2):
    lathe(c, MT('glass'), [(0.0, 0.0), (r * 0.8, 0.0), (r, 0.1), (r * 1.1, h), (r * 1.0, h), (r * 0.7, 0.14), (0.0, 0.1)], 0, 0, 0, 14)


def picture(c, w, h, cover='blue', frame='trim', kind='art'):
    """wall picture facing +lz"""
    rbox(c, MT(frame), 0, 0, -h / 2, w, h, 0.16, 0.05, 2)
    rbox(c, MT('white'), 0, 0.06, -h / 2 + 0.18, w - 0.36, h - 0.36, 0.06, 0.02, 1)
    if kind == 'art':
        rbox(c, MT(cover), 0, 0.1, -h / 2 + 0.32, w - 0.7, h - 0.64, 0.05, 0.02, 1)
        sphere(c, MT('yellow'), -w * 0.18, 0.13, h * 0.12, w * 0.12, w * 0.12, 0.03, 10, 6)
        rbox(c, MT('white'), w * 0.1, 0.13, -h * 0.25, w * 0.35, h * 0.12, 0.03, 0.02, 1)
    elif kind == 'family':
        rbox(c, MT('orange'), 0, 0.1, -h / 2 + 0.32, w - 0.7, h - 0.64, 0.05, 0.02, 1)
        for k, (x, s) in enumerate(((-w * 0.2, 1.0), (w * 0.0, 0.8), (w * 0.2, 1.0))):
            sphere(c, MT('skin'), x, 0.14, h * 0.08 + (1 - s) * 0.3, 0.2 * s, 0.22 * s, 0.05, 10, 6)
            rbox(c, MT(('teal', 'pink', 'blue')[k]), x, 0.13, -h * 0.28, 0.4 * s, 0.55 * s, 0.05, 0.05, 2)


def rug(c, w, d, base='red', border='teal', stripe='yellow', fringe=True):
    w, d = w * 1.4, d * 1.4
    rbox(c, MT(border), 0, 0, 0, w, 0.08, d, 0.03, 1)
    rbox(c, MT(base), 0, 0, 0.08, w - 0.9, 0.05, d - 0.9, 0.02, 1)
    sphere(c, MT(stripe), 0, 0, 0.15, min(w, d) * 0.2, 0.03, min(w, d) * 0.2, 20, 4)
    if fringe:
        for sx in (-1, 1):
            for k in range(int(d / 0.28)):
                rbox(c, MT('cream'), sx * (w / 2 + 0.2), -d / 2 + 0.2 + k * 0.28, 0.0, 0.4, 0.04, 0.1, 0.015, 1)


def tv_unit(c, w=7.4, d=1.9, h=2.2):
    wd = MT('wood2')
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, MT('wood'), [(0.2, 0), (0.14, 0.3), (0.2, 0.6)], sx * (w / 2 - 0.4), sz * (d / 2 - 0.35), 0, 10)
    rbox(c, wd, 0, 0, 0.6, w, h - 0.6, d, 0.12, 2)
    for sx in (-1, 1):
        rbox(c, MT('wood'), sx * w / 4, d / 2 - 0.02, 0.85, w / 2 - 0.35, h - 1.15, 0.07, 0.04, 1)
        sphere(c, MT('brass'), sx * (w / 4 - sx * 0.8), d / 2 + 0.06, h - 0.65, 0.09, 0.09, 0.09, 8, 5)
    rbox(c, MT('black'), 0, 0, h, 0.35, 0.45, 0.35, 0.05, 1)
    rbox(c, MT('black'), 0, 0, h + 0.38, 0.9, 0.12, 0.45, 0.04, 1)
    rbox(c, MT('black'), 0, 0, h + 0.5, 5.4, 3.0, 0.22, 0.08, 2)
    rbox(c, MT('screen'), 0, 0.12, h + 0.6, 5.1, 2.8, 0.05, 0.03, 1)
    rbox(c, MT('black'), 0, d / 2 - 0.5, h, 3.0, 0.22, 0.4, 0.05, 1)


def storage_shelf(c, w=6.0, h=7.0, d=1.6, rows=4):
    """utility / garage shelving: open frame, back panel, boards and rows of boxes and bins"""
    wd, w2 = MT('wood'), MT('wood2')
    rbox(c, wd, -w / 2 + 0.15, 0, 0, 0.3, h, d, 0.05, 2)
    rbox(c, wd, w / 2 - 0.15, 0, 0, 0.3, h, d, 0.05, 2)
    rbox(c, w2, 0, -d / 2 + 0.06, 0, w - 0.2, h, 0.12, 0.02, 1)
    gap = (h - 0.4) / rows
    cols = ['cream', 'blue', 'red', 'mustard', 'teal', 'cardboard']
    for k in range(rows + 1):
        rbox(c, wd, 0, 0, k * gap, w - 0.2, 0.28, d, 0.05, 2)
        if k == rows:
            break
        base = k * gap + 0.28
        nb = max(1, int((w - 0.8) / 1.5))
        bw = (w - 0.7) / nb - 0.1
        for j in range(nb):
            x = -(w - 0.7) / 2 + (j + 0.5) * (w - 0.7) / nb
            rbox(c, MT(cols[(j + k) % 6]), x, 0.05, base, bw, gap - 0.5 - 0.25 * ((j * 3 + k) % 3), d - 0.5, 0.1, 2)


def monitor(c, col='black'):
    """desktop monitor on a flat stand: base plate, neck, screen with a lit panel (one group)"""
    rbox(c, MT(col), 0, 0, 0, 1.8, 0.2, 1.2, 0.05, 1)
    rbox(c, MT(col), 0, 0, 0.2, 2.2, 0.7, 0.3, 0.04, 1)
    rbox(c, MT(col), 0, 0, 0.9, 2.6, 1.6, 0.14, 0.05, 1)


def bookshelf(c, w=6.0, h=6.8, d=1.5, rows=5, seed=1, deco=True):
    wd, w2 = MT('wood'), MT('wood2')
    rbox(c, wd, -w / 2 + 0.15, 0, 0, 0.3, h, d, 0.05, 2)
    rbox(c, wd, w / 2 - 0.15, 0, 0, 0.3, h, d, 0.05, 2)
    rbox(c, w2, 0, -d / 2 + 0.06, 0, w - 0.2, h, 0.12, 0.02, 1)
    gap = (h - 0.4) / rows
    rnd = _random.Random(seed)
    cols = ['red', 'blue', 'yellow', 'teal', 'purple', 'orange', 'white', 'leaf', 'pink', 'navy']
    for k in range(rows + 1):
        rbox(c, wd, 0, 0, k * gap, w - 0.2, 0.28, d, 0.05, 2)
        if k == rows:
            break
        x = -w / 2 + 0.45
        base = k * gap + 0.28
        while x < w / 2 - 0.9:
            bw = rnd.uniform(0.2, 0.45)
            bh = gap - 0.5 - rnd.uniform(0.0, 0.7)
            tilt = rnd.random() < 0.06
            if deco and rnd.random() < 0.09 and bw > 0.35:
                sphere(c, MT(rnd.choice(cols)), x + 0.3, 0.0, base + 0.35, 0.3, 0.35, 0.3, 10, 6)
                x += 0.8
                continue
            book(c, MT(rnd.choice(cols)), x + bw / 2, -0.05, base, bw, bh, d - 0.45)
            x += bw + 0.02
            if tilt:
                x += 0.5
    rbox(c, wd, 0, 0, h, w, 0.18, d + 0.12, 0.05, 2)


def dining_chair(c, col='red', seat='cream'):
    wd, w2 = MT('wood'), MT('wood2')
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, wd, [(0.16, 0), (0.1, 0.5), (0.14, 1.0), (0.1, 1.7)], sx * 0.7, sz * 0.7, 0, 10)
    rbox(c, w2, 0, 0, 1.55, 1.8, 0.18, 1.8, 0.06, 2)
    rbox(c, MT(seat), 0, 0.02, 1.7, 1.6, 0.34, 1.6, 0.14, 3)
    for sx in (-1, 1):
        lathe(c, wd, [(0.11, 1.6), (0.09, 2.6), (0.13, 3.9)], sx * 0.7, -0.78, 0, 10)
    for k in range(3):
        rbox(c, MT(col), 0, -0.8, 2.35 + k * 0.45, 1.35, 0.3, 0.14, 0.05, 2)
    rbox(c, wd, 0, -0.78, 3.8, 1.7, 0.28, 0.2, 0.08, 2)


def dining_table(c, w=10.6, d=4.8, h=2.9):
    wd, w2 = MT('wood'), MT('wood2')
    rbox(c, w2, 0, 0, h - 0.34, w, 0.34, d, 0.14, 3)
    rbox(c, wd, 0, 0, h - 0.8, w - 1.0, 0.46, d - 1.0, 0.08, 2)
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, wd, [(0.26, 0), (0.2, 0.3), (0.34, 0.6), (0.2, 1.0), (0.26, 1.5), (0.2, 2.0), (0.28, h - 0.8)], sx * (w / 2 - 0.7), sz * (d / 2 - 0.6), 0, 12)


def place_setting(c, col='teal'):
    plate(c, 'white', 0.62)
    tf_push(0.0, 0.0, 0.16, 0)
    lathe(c, MT(col), [(0.0, 0.0), (0.3, 0.0), (0.46, 0.04), (0.0, 0.02)], 0, 0, 0, 16)
    tf_pop()
    glass_cup(c, 0.75, 0.2) if False else None
    tf_push(0.95, -0.7, 0, 0)
    glass_cup(c, 0.75, 0.2)
    tf_pop()
    rbox(c, MT('metal'), -0.95, 0.0, 0.0, 0.1, 0.05, 0.9, 0.02, 1)
    rbox(c, MT('metal'), 0.95, 0.15, 0.0, 0.1, 0.05, 0.9, 0.02, 1)
    rbox(c, MT('red'), -0.2, 0.9, 0.0, 0.8, 0.07, 0.5, 0.03, 1)


def candle(c, col='white'):
    lathe(c, MT('brass'), [(0.0, 0), (0.28, 0.0), (0.2, 0.1), (0.07, 0.3), (0.1, 0.55), (0.18, 0.62), (0.0, 0.62)], 0, 0, 0, 12)
    cylinder(c, MT(col), 0, 0, 0.55, 0.9, 0.07, 10)
    sphere(c, MT('lamp'), 0, 0, 1.55, 0.07, 0.14, 0.07, 8, 6)


def fruit_bowl(c):
    lathe(c, MT('wood2'), [(0.0, 0.0), (0.4, 0.0), (0.9, 0.35), (1.0, 0.45), (0.92, 0.45), (0.8, 0.3), (0.0, 0.12)], 0, 0, 0, 18)
    rnd = _random.Random(7)
    for k in range(6):
        a = 2 * math.pi * k / 6
        r = 0.36 if k else 0.0
        sphere(c, MT(['red', 'leaf2', 'orange', 'red', 'yellow', 'leaf2'][k]), r * math.cos(a), r * math.sin(a), 0.42 + (0.18 if k == 0 else 0.0), 0.3, 0.28, 0.3, 10, 7)


def chandelier(c, n=6, col='lampshade'):
    cylinder(c, MT('brass'), 0, 0, 0.0, 0.8, 0.05, 8)
    lathe(c, MT('brass'), [(0.0, -0.8), (0.4, -0.8), (0.3, -1.2), (0.12, -1.6), (0.3, -1.9), (0.0, -2.1)], 0, 0, 0, 14)
    for k in range(n):
        a = 2 * math.pi * k / n
        ex, ez = 1.8 * math.cos(a), 1.8 * math.sin(a)
        tube(c, MT('brass'), [(0, -1.4, 0), (ex * 0.5, -1.7, ez * 0.5), (ex, -1.6, ez), (ex, -1.45, ez)], 0.06, 6)
        lathe(c, MT(col), [(0.2, -1.45), (0.36, -0.95), (0.0, -0.95)], ex, ez, 0, 12, caps=False)
        sphere(c, MT('lamp'), ex, ez, -1.3, 0.16, 0.2, 0.16, 8, 6)


def sideboard(c, w=7.0, d=1.8, h=2.8):
    wd, w2 = MT('wood'), MT('wood2')
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, wd, [(0.18, 0), (0.12, 0.5), (0.18, 0.9)], sx * (w / 2 - 0.4), sz * (d / 2 - 0.35), 0, 10)
    rbox(c, w2, 0, 0, 0.9, w, h - 0.9, d, 0.12, 3)
    rbox(c, wd, 0, 0, h, w + 0.2, 0.14, d + 0.12, 0.05, 2)
    for k in range(3):
        x = -w / 3 + k * w / 3
        rbox(c, wd, x, d / 2 - 0.02, 1.15, w / 3 - 0.25, h - 1.45, 0.08, 0.05, 2)
        rbox(c, w2, x, d / 2 + 0.02, 1.4, w / 3 - 0.8, h - 1.95, 0.05, 0.03, 1)
        sphere(c, MT('brass'), x + (0.3 if k % 2 else -0.3), d / 2 + 0.12, h * 0.55, 0.11, 0.11, 0.11, 8, 6)


def console_table(c, w=4.4, d=1.5, h=3.0):
    wd, w2 = MT('wood'), MT('wood2')
    rbox(c, w2, 0, 0, h - 0.24, w, 0.24, d, 0.09, 3)
    rbox(c, wd, 0, 0, h - 0.84, w - 0.5, 0.6, d - 0.3, 0.06, 2)
    rbox(c, MT('wood'), 0, d / 2 - 0.2, h - 0.74, w - 1.2, 0.44, 0.06, 0.03, 1)
    sphere(c, MT('brass'), 0, d / 2 - 0.14, h - 0.52, 0.1, 0.1, 0.1, 8, 6)
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, wd, [(0.18, 0), (0.12, 0.5), (0.2, 1.0), (0.12, 1.6), (0.15, h - 0.84)], sx * (w / 2 - 0.35), sz * (d / 2 - 0.3), 0, 10)


def mirror_round(c, r=1.7):
    torus(c, MT('brass'), 0, 0, 0, r, 0.14, plane='xy', seg=36, tseg=8)
    lathe(c, MT('mirror'), [(0.0, 0.0), (r, 0.0)], 0, 0, 0, 36, caps=False) if False else None
    sphere(c, MT('mirror'), 0, 0, 0, r - 0.05, r - 0.05, 0.06, 36, 4)


def coat_on_hook(c, col):
    tube(c, MT('metal'), [(0, 0, 0), (0, 0.15, -0.05), (0, 0.3, 0.0)], 0.03, 5)
    rbox(c, MT(col), 0, 0.05, -3.0, 1.5, 3.1, 0.55, 0.22, 3)
    rbox(c, MT(col), -0.9, 0.05, -2.6, 0.38, 2.3, 0.45, 0.16, 2)
    rbox(c, MT(col), 0.9, 0.05, -2.6, 0.38, 2.3, 0.45, 0.16, 2)


def shoe(c, col='wood'):
    rbox(c, MT('dark'), 0, 0, 0, 0.55, 0.14, 1.4, 0.05, 2)
    rbox(c, MT(col), 0, -0.05, 0.12, 0.5, 0.42, 1.0, 0.18, 3)
    rbox(c, MT(col), 0, 0.28, 0.12, 0.5, 0.3, 0.55, 0.14, 3)


def umbrella_stand(c):
    lathe(c, MT('blue'), [(0.0, 0), (0.55, 0.0), (0.65, 0.2), (0.7, 2.0), (0.62, 2.0), (0.0, 0.1)], 0, 0, 0, 18)
    for k, col in enumerate(('red', 'yellow')):
        tube(c, MT('dark'), [(0.15 * (k * 2 - 1), 1.6, 0.0), (0.2 * (k * 2 - 1), 3.2, 0.1), (0.25 * (k * 2 - 1), 4.2, 0.1)], 0.05, 6)
        lathe(c, MT(col), [(0.0, 4.2), (0.1, 3.9)], 0.25 * (k * 2 - 1), 0.1, 0, 10, caps=False)


def newel(c, h=4.3):
    lathe(c, MT('wood'), [(0.5, 0), (0.5, 0.35), (0.3, 0.5), (0.34, 1.8), (0.26, 2.0), (0.34, 2.3), (0.4, 3.3), (0.5, 3.6), (0.5, h - 0.1), (0.38, h)], 0, 0, 0, 16)
    sphere(c, MT('brass'), 0, 0, h + 0.18, 0.28, 0.28, 0.28, 12, 8)


def baluster(c, h=3.0):
    lathe(c, MT('trim'), [(0.12, 0), (0.12, 0.3), (0.2, 0.55), (0.1, 0.9), (0.16, 1.4), (0.09, 1.9), (0.12, h)], 0, 0, 0, 10)


def cabinet(c, w, d, h, n=2, col='cab', top='teal', knob='brass', top_t=0.24, sides_open=False, shelf_h=None):
    """base cabinet, front toward +lz. Counter top slab sits on top."""
    rbox(c, MT('dark'), 0, -0.1, 0.0, w - 0.1, 0.5, d - 0.5, 0.04, 1)
    rbox(c, MT(col), 0, 0, 0.5, w, h - 0.5 - top_t, d, 0.06, 2)
    dw = (w - 0.12) / n
    for k in range(n):
        x = -w / 2 + 0.06 + dw * (k + 0.5)
        rbox(c, MT(col), x, d / 2 - 0.02, 0.62, dw - 0.1, h - 0.5 - top_t - 0.24, 0.1, 0.05, 2)
        rbox(c, MT('trim'), x, d / 2 + 0.06, 0.78, dw - 0.46, h - 0.5 - top_t - 0.56, 0.05, 0.03, 1)
        kx = x + (dw / 2 - 0.35) * (1 if k % 2 == 0 else -1)
        cylinder(c, MT(knob), kx, d / 2 + 0.17, h - top_t - 0.5, 0.07, 0.07, 8)
        sphere(c, MT(knob), kx, d / 2 + 0.28, h - top_t - 0.5, 0.13, 0.13, 0.13, 8, 6)
    rbox(c, MT(top), 0, 0.05, h - top_t, w + 0.1, top_t, d + 0.18, 0.07, 2)


def upper_cabinet(c, w, d=1.1, h=2.9, n=2, col='cab'):
    rbox(c, MT(col), 0, 0, 0.0, w, h, d, 0.07, 2)
    dw = (w - 0.1) / n
    for k in range(n):
        x = -w / 2 + 0.05 + dw * (k + 0.5)
        rbox(c, MT(col), x, d / 2 - 0.02, 0.1, dw - 0.1, h - 0.2, 0.09, 0.05, 2)
        rbox(c, MT('trim'), x, d / 2 + 0.05, 0.28, dw - 0.45, h - 0.56, 0.05, 0.03, 1)
        cylinder(c, MT('brass'), x + (dw / 2 - 0.3) * (-1 if k % 2 == 0 else 1), d / 2 + 0.14, 0.2, 0.06, 0.06, 8)


def faucet(c):
    cylinder(c, MT('metal'), 0, 0, 0, 0.25, 0.22, 12)
    tube(c, MT('metal'), [(0, 0.25, 0), (0, 1.1, 0), (0.0, 1.45, 0.25), (0.0, 1.5, 0.75), (0.0, 1.35, 0.95)], 0.1, 8)
    for sx in (-1, 1):
        cylinder(c, MT('metal'), sx * 0.42, 0, 0.0, 0.5, 0.06, 8)
        sphere(c, MT('red' if sx < 0 else 'blue'), sx * 0.42, 0, 0.52, 0.1, 0.08, 0.1, 8, 6)


def sink_unit(c, w, d, h, col='cab', top='teal'):
    cabinet(c, w, d, h, 2, col, top)
    # basin visible as a dark steel tray set into the counter
    tf_push(0, 0.05, h - 0.02, 0)
    rbox(c, MT('metal'), 0, 0, 0.0, w - 0.9, 0.06, d - 0.7, 0.03, 1)
    rbox(c, MT('dark'), 0, 0, 0.05, w - 1.3, 0.03, d - 1.1, 0.02, 1)
    tf_pop()
    tf_push(0, -d / 2 + 0.35, h, 0)
    faucet(c)
    tf_pop()


def stove(c, w=2.8, d=2.4, h=3.1):
    for sx in (-1, 1):
        cylinder(c, MT('dark'), sx * (w / 2 - 0.2), d / 2 - 0.2, 0.0, 0.2, 0.12, 8)
    rbox(c, MT('metal'), 0, 0, 0.2, w, h - 0.2, d, 0.1, 3)
    rbox(c, MT('black'), 0, 0, h, w - 0.1, 0.1, d - 0.1, 0.04, 2)
    for (bx, bz) in ((-0.65, -0.55), (0.65, -0.55), (-0.65, 0.55), (0.65, 0.55)):
        torus(c, MT('dark'), bx, bz, h + 0.16, 0.34, 0.05, 'xz', 20, 6)
        cylinder(c, MT('dark'), bx, bz, h + 0.1, 0.1, 0.13, 10)
    for k in range(5):
        cylinder(c, MT('dark'), -1.0 + k * 0.5, d / 2 + 0.15, h - 0.5, 0.2, 0.1, 10)
        cylinder(c, MT('metal'), -1.0 + k * 0.5, d / 2 + 0.3, h - 0.5, 0.1, 0.06, 8)
    rbox(c, MT('black'), 0, d / 2 - 0.02, 0.5, w - 0.45, h - 1.35, 0.1, 0.07, 2)
    rbox(c, MT('screen'), 0, d / 2 + 0.05, 0.85, w - 0.95, h - 2.1, 0.05, 0.05, 2)
    tube(c, MT('metal'), [(-w / 2 + 0.5, h - 1.0, d / 2 + 0.28), (w / 2 - 0.5, h - 1.0, d / 2 + 0.28)], 0.07, 8)


def range_hood(c, w=3.0, d=2.1):
    rbox(c, MT('metal'), 0, 0, 0.0, w, 0.5, d, 0.1, 2)
    rbox(c, MT('metal'), 0, -d * 0.2, 0.45, w * 0.55, 1.0, d * 0.6, 0.06, 2)
    rbox(c, MT('metal'), 0, -d * 0.3, 1.3, 1.25, 3.2, 1.2, 0.04, 1)
    rbox(c, MT('dark'), 0, 0.15, -0.02, w - 0.7, 0.04, d - 0.7, 0.02, 1)
    sphere(c, MT('lamp'), -0.7, 0.2, -0.04, 0.12, 0.05, 0.12, 8, 4)
    sphere(c, MT('lamp'), 0.7, 0.2, -0.04, 0.12, 0.05, 0.12, 8, 4)


def fridge(c, w=2.8, d=2.4, h=7.1, col='metal'):
    rbox(c, MT(col), 0, 0, 0.1, w, h - 0.1, d, 0.22, 3)
    rbox(c, MT('dark'), 0, d / 2 - 0.01, 2.55, w - 0.1, 0.07, 0.06, 0.02, 1)
    for k, (y0, hh) in enumerate(((0.35, 2.1), (2.7, h - 2.7 - 0.2))):
        pass
    for hx_ in (-w / 2 + 0.35,):
        tube(c, MT('metal'), [(hx_, 3.0, d / 2 + 0.28), (hx_, 5.2, d / 2 + 0.28)], 0.07, 8)
        tube(c, MT('metal'), [(hx_, 1.0, d / 2 + 0.28), (hx_, 2.2, d / 2 + 0.28)], 0.07, 8)
    for k, mc in enumerate(('red', 'blue', 'yellow', 'teal')):
        sphere(c, MT(mc), -0.2 + (k % 2) * 0.6, d / 2 + 0.05, 4.8 + (k // 2) * 0.55, 0.14, 0.14, 0.05, 8, 5)
    rbox(c, MT('white'), 0.4, d / 2 + 0.03, 4.2, 0.7, 0.9, 0.02, 0.01, 1)
    rbox(c, MT('pink'), -0.2, d / 2 + 0.03, 4.2, 0.55, 0.7, 0.02, 0.01, 1)


def stool(c, col='red', h=2.7):
    for k in range(4):
        a = math.pi / 2 * k + math.pi / 4
        tube(c, MT('wood'), [(0.45 * math.cos(a), 0.0, 0.45 * math.sin(a)), (0.32 * math.cos(a), h - 0.3, 0.32 * math.sin(a))], 0.07, 6)
    torus(c, MT('wood'), 0, 0, 0.9, 0.42, 0.045, 'xz', 20, 6)
    lathe(c, MT(col), [(0.0, h - 0.3), (0.62, h - 0.3), (0.66, h - 0.18), (0.6, h), (0.0, h + 0.02)], 0, 0, 0, 20)


def pendant(c, col='red', drop=3.2):
    tube(c, MT('dark'), [(0, 0, 0), (0, -drop + 0.8, 0)], 0.03, 5)
    lathe(c, MT(col), [(0.15, -drop + 0.8), (0.7, -drop + 0.2), (0.78, -drop)], 0, 0, 0, 20, caps=False)
    lathe(c, MT('lampshade'), [(0.78, -drop), (0.15, -drop + 0.8)], 0, 0, 0, 20, caps=False)
    sphere(c, MT('lamp'), 0, 0, -drop + 0.35, 0.22, 0.28, 0.22, 8, 6)


def kettle(c, col='red'):
    lathe(c, MT(col), [(0.0, 0), (0.45, 0.0), (0.52, 0.2), (0.44, 0.9), (0.26, 1.05), (0.08, 1.12), (0.0, 1.14)], 0, 0, 0, 18)
    tube(c, MT(col), [(0.4, 0.55, 0.0), (0.75, 0.6, 0.0), (0.78, 1.0, 0.0), (0.4, 1.0, 0.0)], 0.06, 6)
    tube(c, MT(col), [(-0.44, 0.45, 0.0), (-0.8, 0.8, 0.0)], 0.06, 6)
    sphere(c, MT('black'), 0, 0, 1.16, 0.1, 0.07, 0.1, 8, 5)


def cooking_pot(c, col='metal', s=1.0, lid=True):
    lathe(c, MT(col), [(0.0, 0), (0.55 * s, 0.0), (0.58 * s, 0.05), (0.58 * s, 0.9 * s), (0.62 * s, 0.95 * s), (0.0, 0.95 * s)], 0, 0, 0, 18, caps=False)
    if lid:
        lathe(c, MT(col), [(0.0, 0.95 * s), (0.6 * s, 0.95 * s), (0.45 * s, 1.1 * s), (0.0, 1.15 * s)], 0, 0, 0, 18, caps=False)
        sphere(c, MT('black'), 0, 0, 1.2 * s, 0.1, 0.09, 0.1, 8, 5)
    for sx in (-1, 1):
        tube(c, MT('black'), [(sx * 0.58 * s, 0.7 * s, 0.0), (sx * 0.85 * s, 0.7 * s, 0.0)], 0.05, 6)


def pan(c):
    lathe(c, MT('dark'), [(0.0, 0.0), (0.6, 0.0), (0.72, 0.28), (0.66, 0.28), (0.54, 0.05), (0.0, 0.04)], 0, 0, 0, 20)
    tube(c, MT('black'), [(0.7, 0.26, 0.0), (1.9, 0.3, 0.0)], 0.07, 6)


def toaster(c):
    rbox(c, MT('metal'), 0, 0, 0.0, 1.5, 0.95, 0.95, 0.22, 3)
    for sx in (-1, 1):
        rbox(c, MT('dark'), sx * 0.34, 0.0, 0.92, 0.5, 0.05, 0.12, 0.02, 1) if False else None
    rbox(c, MT('black'), 0, 0, 0.88, 1.1, 0.06, 0.18, 0.02, 1)
    rbox(c, MT('red'), 0.8, 0.0, 0.5, 0.16, 0.12, 0.28, 0.05, 2)


def microwave(c):
    rbox(c, MT('metal'), 0, 0, 0.0, 2.0, 1.3, 1.5, 0.12, 3)
    rbox(c, MT('screen'), -0.2, 0.7, 0.2, 1.2, 0.85, 0.05, 0.04, 1)
    rbox(c, MT('black'), 0.7, 0.7, 0.2, 0.4, 0.85, 0.05, 0.03, 1)
    sphere(c, MT('red'), 0.7, 0.76, 1.0, 0.07, 0.07, 0.03, 6, 4)


def cutting_board(c):
    rbox(c, MT('wood2'), 0, 0, 0.0, 1.6, 0.12, 1.1, 0.05, 2)
    rbox(c, MT('white'), -0.3, 0.1, 0.12, 0.2, 0.14, 0.2, 0.05, 1) if False else None
    sphere(c, MT('red'), 0.3, 0.1, 0.34, 0.2, 0.18, 0.2, 8, 6)
    sphere(c, MT('orange'), -0.3, -0.1, 0.34, 0.2, 0.18, 0.2, 8, 6)
    rbox(c, MT('metal'), 0.0, -0.4, 0.12, 1.0, 0.05, 0.12, 0.02, 1)


def bowl(c, col='white', r=0.9, h=0.5):
    lathe(c, MT(col), [(0.0, 0.0), (r * 0.4, 0.0), (r, h * 0.9), (r, h), (r * 0.9, h), (r * 0.35, 0.1), (0.0, 0.1)], 0, 0, 0, 20)


def wall_clock(c, r=0.8):
    torus(c, MT('red'), 0, 0, 0, r, 0.1, 'xy', 28, 6)
    sphere(c, MT('white'), 0, 0.02, 0, r - 0.05, r - 0.05, 0.06, 24, 4)
    tube(c, MT('black'), [(0, 0.1, 0), (0, 0.1, r * 0.55)] if False else [(0, 0.1, 0), (0.0, r * 0.55, 0.1)], 0.03, 5)
    tube(c, MT('black'), [(0, 0, 0.1), (r * 0.4, 0.0, 0.1)], 0.03, 5)
    for k in range(12):
        a = math.radians(30 * k)
        sphere(c, MT('black'), (r - 0.18) * math.sin(a), 0.1, (r - 0.18) * math.cos(a), 0.03, 0.03, 0.03, 6, 4)


def washer(c, col='white', kind='washer'):
    rbox(c, MT(col), 0, 0, 0.0, 2.7, 3.5, 2.4, 0.16, 3)
    rbox(c, MT('metal'), 0, 1.1, 3.0, 2.5, 0.5, 0.15, 0.06, 2)
    for k in range(3):
        cylinder(c, MT('dark'), -0.8 + k * 0.5, 1.18, 3.2, 0.16, 0.12, 10)
    rbox(c, MT('screen'), 0.75, 1.2, 3.1, 0.5, 0.28, 0.05, 0.03, 1)
    tf_push(0, 1.2, 1.5, 0)
    torus(c, MT('metal'), 0, 0, 0, 0.78, 0.1, 'xy', 28, 8)
    sphere(c, MT('glass'), 0, 0.04, 0, 0.7, 0.7, 0.12, 24, 8)
    sphere(c, MT('navy'), 0, -0.06, 0, 0.62, 0.62, 0.1, 24, 8)
    tf_pop()
    rbox(c, MT('metal'), 1.1, 1.3, 1.6, 0.14, 0.9, 0.08, 0.04, 1)


def bottle(c, col='blue', cap='white', h=1.2, r=0.28):
    lathe(c, MT(col), [(0.0, 0), (r, 0.0), (r * 1.05, 0.1), (r * 1.05, h * 0.65), (r * 0.5, h * 0.82), (r * 0.32, h * 0.9), (r * 0.32, h)], 0, 0, 0, 14)
    cylinder(c, MT(cap), 0, 0, h, 0.16, r * 0.38, 10)


def basket(c, col='wood2', clothes=True):
    lathe(c, MT(col), [(0.0, 0), (0.62, 0.0), (0.86, 1.4), (0.92, 1.55), (0.84, 1.55), (0.0, 0.1)], 0, 0, 0, 20, caps=False)
    for sx in (-1, 1):
        tube(c, MT(col), [(sx * 0.9, 1.35, 0.0), (sx * 1.1, 1.65, 0.0), (sx * 0.9, 1.75, 0.0)], 0.05, 6)
    if clothes:
        for k, cc in enumerate(('red', 'blue', 'yellow', 'white')):
            sphere(c, MT(cc), (k % 2 - 0.5) * 0.7, (k // 2 - 0.5) * 0.6, 1.5, 0.4, 0.3, 0.38, 10, 6)


def ironing_board(c):
    rbox(c, MT('metal'), 0, 0, 3.0, 1.1, 0.1, 4.4, 0.05, 1)
    rbox(c, MT('blue'), 0, 0, 3.08, 1.0, 0.06, 4.3, 0.03, 1)
    for sz in (-1, 1):
        tube(c, MT('metal'), [(-0.45, 3.0, sz * 1.0), (0.45, 0.0, sz * 1.4)], 0.05, 6)
        tube(c, MT('metal'), [(0.45, 3.0, sz * 1.0), (-0.45, 0.0, sz * 1.4)], 0.05, 6)


def drying_rack(c):
    for sx in (-1, 1):
        tube(c, MT('metal'), [(sx * 1.4, 0.0, 0.0), (sx * 1.0, 3.2, 0.0)], 0.05, 6)
    for k in range(6):
        tube(c, MT('metal'), [(-1.1, 1.4 + k * 0.28, 0.0), (1.1, 1.4 + k * 0.28, 0.0)], 0.035, 5)
    for k, cc in enumerate(('red', 'yellow', 'blue')):
        rbox(c, MT(cc), -0.5 + k * 0.5, 0.0, 1.5 + k * 0.1, 0.55, 1.2, 0.12, 0.06, 2)


def toilet(c):
    lathe(c, MT('white'), [(0.0, 0.0), (0.5, 0.0), (0.55, 0.8), (0.7, 1.45), (0.0, 1.45)], 0, 0.15, 0, 20, sx=0.85, sz=1.15, caps=False)
    rbox(c, MT('white'), 0, -0.95, 0.5, 1.5, 1.7, 0.7, 0.14, 3)
    torus(c, MT('white'), 0, 0.15, 1.52, 0.55, 0.1, 'xz', 24, 6)
    sphere(c, MT('white'), 0, -0.95, 2.2, 0.25, 0.1, 0.25, 8, 4)
    lathe(c, MT('white'), [(0.0, 1.55), (0.62, 1.55), (0.62, 1.6), (0.0, 1.62)], 0, 0.15, 0, 20, sx=0.85, sz=1.15)


def pedestal_sink(c):
    lathe(c, MT('white'), [(0.0, 0), (0.55, 0.0), (0.5, 0.2), (0.28, 0.5), (0.3, 2.0), (0.6, 2.2)], 0, 0, 0, 16)
    lathe(c, MT('white'), [(0.0, 2.4), (0.72, 2.6), (1.3, 3.1), (1.35, 3.3), (1.2, 3.3), (0.0, 2.7)], 0, 0.2, 0, 22, sx=1.1, sz=0.85)
    tf_push(0, -0.45, 3.2, 0)
    faucet(c)
    tf_pop()


def bathtub(c):
    rbox(c, MT('white'), 0, 0, 0.5, 3.6, 2.0, 7.4, 0.55, 4)
    rbox(c, MT('mirror'), 0, 0, 2.3, 2.6, 0.12, 6.4, 0.3, 3)
    for sx in (-1, 1):
        cylinder(c, MT('metal'), sx * 1.4, -3.4, 0.0, 0.5, 0.2, 10)
    tf_push(0, -3.1, 2.5, 0)
    faucet(c)
    tf_pop()
    rbox(c, MT('white'), 0, 0.0, 0.0, 3.2, 0.5, 6.9, 0.08, 1)


def bed(c, w=6.4, l=9.4, quilt='pink', sheet='cream', wood='wood2', pillows=('white', 'cream'), stripe='white'):
    cover('bed', w, l, 2.7)
    wd, w2 = MT('wood'), MT(wood)
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, wd, [(0.26, 0), (0.2, 0.3), (0.28, 0.6)], sx * (w / 2 - 0.3), sz * (l / 2 - 0.3), 0, 10)
    rbox(c, w2, 0, 0, 0.5, w, 0.7, l, 0.14, 3)
    rbox(c, MT(sheet), 0, 0.1, 1.2, w - 0.35, 0.95, l - 0.6, 0.38, 3)
    rbox(c, MT(quilt), 0, 1.15, 1.95, w - 0.12, 0.62, l * 0.68, 0.3, 3)
    for k in range(5):
        rbox(c, MT(stripe), 0, 1.15 - l * 0.34 + 0.9 + k * (l * 0.68 - 1.8) / 4, 2.5, w - 0.7, 0.06, 0.28, 0.02, 1)
    rbox(c, MT(quilt), 0, l / 2 - 1.2, 2.0, w - 0.3, 0.6, 1.8, 0.3, 3)
    rbox(c, w2, 0, -l / 2 - 0.1, 0.5, w + 0.5, 3.6, 0.55, 0.28, 4)
    for sx in (-1, 1):
        sphere(c, wd, sx * (w / 2 + 0.05), -l / 2 - 0.1, 4.25, 0.3, 0.3, 0.3, 10, 8)
    rbox(c, w2, 0, l / 2 + 0.1, 0.5, w + 0.3, 1.5, 0.45, 0.2, 3)
    for k, pc in enumerate(pillows):
        tf_push(-1.5 + k * 3.0, -l / 2 + 1.1, 2.1, (-6, 5)[k % 2])
        rbox(c, MT(pc), 0, 0, 0.0, 2.6, 0.9, 1.6, 0.42, 3)
        tf_pop()
    tf_push(0.0, -l / 2 + 1.7, 2.0, 0)
    rbox(c, MT('coral'), 0, 0, 0.0, 1.3, 0.9, 0.7, 0.34, 3)
    tf_pop()


def nightstand(c, col='wood2'):
    wd = MT('wood')
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, wd, [(0.14, 0), (0.1, 0.4), (0.15, 0.8)], sx * 0.75, sz * 0.6, 0, 8)
    rbox(c, MT(col), 0, 0, 0.8, 1.9, 1.5, 1.6, 0.1, 3)
    rbox(c, wd, 0, 0.8, 0.95, 1.6, 0.55, 0.06, 0.04, 1)
    rbox(c, wd, 0, 0.8, 1.65, 1.6, 0.55, 0.06, 0.04, 1)
    sphere(c, MT('brass'), 0, 0.92, 1.2, 0.1, 0.1, 0.1, 8, 6)
    sphere(c, MT('brass'), 0, 0.92, 1.9, 0.1, 0.1, 0.1, 8, 6)
    rbox(c, wd, 0, 0, 2.3, 2.1, 0.14, 1.8, 0.06, 2)


def dresser(c, w=6.0, d=2.4, h=3.7, col='wood2'):
    wd = MT('wood')
    for sx in (-1, 1):
        for sz in (-1, 1):
            lathe(c, wd, [(0.2, 0), (0.14, 0.4), (0.2, 0.8)], sx * (w / 2 - 0.4), sz * (d / 2 - 0.35), 0, 10)
    rbox(c, MT(col), 0, 0, 0.8, w, h - 0.8, d, 0.12, 3)
    rbox(c, wd, 0, 0, h, w + 0.2, 0.14, d + 0.14, 0.05, 2)
    for k in range(3):
        y = 1.0 + k * 0.85
        rbox(c, wd, 0, d / 2 - 0.02, y, w - 0.5, 0.7, 0.08, 0.05, 2)
        for sx in (-1, 1):
            sphere(c, MT('brass'), sx * w * 0.2, d / 2 + 0.12, y + 0.35, 0.12, 0.12, 0.12, 8, 6)
    tf_push(0, -d / 2 + 0.2, h + 0.14, 0)
    rbox(c, MT('brass'), 0, 0, 0.0, w * 0.55, 3.4, 0.14, 0.12, 3)
    rbox(c, MT('mirror'), 0, 0.02, 0.2, w * 0.55 - 0.4, 3.0, 0.1, 0.1, 2)
    tf_pop()
    tf_push(-w * 0.32, 0.2, h + 0.14, 20)
    rbox(c, MT('red'), 0, 0, 0.0, 1.1, 0.5, 0.8, 0.12, 2)
    tf_pop()
    tf_push(w * 0.28, 0.35, h + 0.14, 0)
    bottle(c, 'pink', 'brass', 0.8, 0.2)
    tf_pop()
    tf_push(w * 0.4, 0.2, h + 0.14, 0)
    bottle(c, 'blue', 'white', 0.65, 0.17)
    tf_pop()


def wardrobe(c, w=8.0, d=3.5, h=8.6, open_doors=True):
    wd, w2 = MT('wood'), MT('wood2')
    rbox(c, w2, -w / 2 + 0.2, 0, 0.0, 0.4, h, d, 0.06, 2)
    rbox(c, w2, w / 2 - 0.2, 0, 0.0, 0.4, h, d, 0.06, 2)
    rbox(c, w2, 0, 0, h - 0.4, w, 0.45, d, 0.06, 2)
    rbox(c, w2, 0, 0, 0.0, w, 0.4, d, 0.05, 2)
    rbox(c, wd, 0, -d / 2 + 0.1, 0.3, w - 0.5, h - 0.7, 0.18, 0.04, 1)
    tube(c, MT('metal'), [(-w / 2 + 0.5, h - 2.4, 0.0), (w / 2 - 0.5, h - 2.4, 0.0)], 0.07, 8)
    rbox(c, w2, 0, 0, h - 1.6, w - 0.8, 0.14, d - 0.5, 0.04, 1)
    for k, cc in enumerate(('cream', 'red', 'blue')):
        rbox(c, MT(cc), -2.6 + k * 1.4, 0.0, h - 1.46, 1.2, 0.55, 1.1, 0.14, 2)    # shelf items stay on the left; the right third is free for hiding
    cols = ('red', 'blue', 'yellow', 'teal', 'white', 'purple', 'orange', 'navy', 'pink')
    for k in range(4):
        x = -w / 2 + 0.9 + k * (w - 1.8) / 8.0
        tube(c, MT('metal'), [(x, h - 2.4, 0), (x, h - 2.7, 0), (x + 0.45, h - 3.0, 0), (x - 0.45, h - 3.0, 0), (x, h - 2.7, 0)], 0.025, 5)
        rbox(c, MT(cols[k]), x, 0.0, h - 5.7, 0.55, 2.7 + (k % 3) * 0.2, 1.1, 0.2, 2)
    for k, cc in enumerate(('red', 'dark', 'blue')):
        tf_push(-w / 2 + 1.1 + k * 1.1, 0.5, 0.4, 15 * (k % 2 * 2 - 1))
        shoe(c, cc)
        tf_pop()
    if open_doors:
        for sx in (-1, 1):
            tf_push(sx * (w / 2 - 0.05), d / 2, 0.0, 0)
            tf_push(0, 0.0, 0.0, -sx * 75)
            rbox(c, w2, sx * (w / 4), 0.0, 0.2, w / 2 - 0.1, h - 0.4, 0.22, 0.06, 2)
            rbox(c, wd, sx * (w / 4), 0.14, 0.7, w / 2 - 0.9, h - 1.4, 0.07, 0.04, 1)
            sphere(c, MT('brass'), sx * 0.4 + 0.0, 0.2, h * 0.5, 0.12, 0.12, 0.12, 8, 6)
            tf_pop()
            tf_pop()
    else:       # closed double doors flush with the front: two panelled leaves, metal pulls
        for sx in (-1, 1):
            rbox(c, w2, sx * (w / 4 - 0.02), d / 2 - 0.12, 0.35, w / 2 - 0.25, h - 0.8, 0.22, 0.05, 1)
            rbox(c, wd, sx * (w / 4 - 0.02), d / 2 + 0.0, 1.0, w / 2 - 1.1, h - 2.4, 0.1, 0.04, 1)
            tube(c, MT('metal'), [(sx * 0.35, h * 0.4, d / 2 + 0.2), (sx * 0.35, h * 0.4 + 1.6, d / 2 + 0.2)], 0.08, 6)


def teddy(c, col='orange'):
    g = MT(col)
    sphere(c, g, 0, 0, 0.55, 0.55, 0.6, 0.5, 12, 8)
    sphere(c, g, 0, 0.05, 1.45, 0.42, 0.4, 0.4, 12, 8)
    for sx in (-1, 1):
        sphere(c, g, sx * 0.33, 0, 1.78, 0.14, 0.14, 0.1, 8, 6)
        sphere(c, g, sx * 0.72, 0.1, 0.8, 0.2, 0.3, 0.2, 8, 6)
        sphere(c, g, sx * 0.35, 0.15, 0.1, 0.25, 0.22, 0.32, 8, 6)
    sphere(c, MT('cream'), 0, 0.33, 1.38, 0.18, 0.14, 0.12, 8, 6)
    sphere(c, MT('black'), 0, 0.45, 1.42, 0.06, 0.05, 0.05, 6, 4)
    for sx in (-1, 1):
        sphere(c, MT('black'), sx * 0.14, 0.32, 1.52, 0.05, 0.05, 0.04, 6, 4)


def bunk_bed(c, w=3.8, l=8.0):
    wd = MT('blue')
    for sx in (-1, 1):
        for sz in (-1, 1):
            rbox(c, wd, sx * (w / 2 - 0.2), sz * (l / 2 - 0.2), 0.0, 0.4, 5.2, 0.4, 0.12, 2)
    for y, sc, pc in ((0.6, 'white', 'yellow'), (3.0, 'white', 'red')):
        rbox(c, MT('wood2'), 0, 0, y, w - 0.4, 0.3, l - 0.4, 0.06, 2)
        rbox(c, MT(sc), 0, 0.1, y + 0.3, w - 0.5, 0.7, l - 0.8, 0.28, 3)
        rbox(c, MT(pc), 0, 1.0, y + 0.85, w - 0.45, 0.4, l * 0.6, 0.18, 3)
        rbox(c, MT('white'), 0, -l / 2 + 1.0, y + 0.95, 2.4, 0.5, 1.1, 0.2, 3)
    for z in (-1.6, 0.0, 1.6):
        tube(c, MT('blue'), [(-w / 2 + 0.2, 4.1, z), (-w / 2 + 0.2, 5.0, z)], 0.07, 6)
        tube(c, MT('blue'), [(w / 2 - 0.2, 4.1, z), (w / 2 - 0.2, 5.0, z)], 0.07, 6)
    tube(c, MT('blue'), [(-w / 2 + 0.2, 5.0, -l / 2 + 0.2), (-w / 2 + 0.2, 5.0, l / 2 - 0.2)], 0.1, 6)
    tube(c, MT('blue'), [(w / 2 - 0.2, 5.0, -l / 2 + 0.2), (w / 2 - 0.2, 5.0, l / 2 - 0.2)], 0.1, 6)
    for sx in (-w / 2 + 0.2, w / 2 - 0.2):
        pass
    # ladder on the west side
    for z in (1.9, 3.1):
        tube(c, MT('wood2'), [(-w / 2 - 0.1, 0.0, z), (-w / 2 - 0.1, 3.9, z)], 0.07, 6)
    for k in range(5):
        tube(c, MT('wood2'), [(-w / 2 - 0.1, 0.5 + k * 0.78, 1.9), (-w / 2 - 0.1, 0.5 + k * 0.78, 3.1)], 0.07, 6)
    tf_push(0.3, l * 0.1, 4.2, 0)
    teddy(c, 'orange')
    tf_pop()


def toy_chest(c):
    rbox(c, MT('red'), 0, 0, 0.0, 3.2, 1.6, 1.8, 0.14, 3)
    rbox(c, MT('yellow'), 0, 0.1, 1.55, 3.3, 0.3, 1.9, 0.14, 3)
    for k in range(3):
        sphere(c, MT('yellow'), -0.9 + k * 0.9, 0.95, 0.9, 0.16, 0.16, 0.04, 8, 5)
    tf_push(-0.7, 0, 1.85, 18)
    rbox(c, MT('blue'), 0, 0, 0.0, 0.7, 0.7, 0.7, 0.1, 2)
    tf_pop()
    tf_push(0.6, 0.1, 1.85, -10)
    rbox(c, MT('teal'), 0, 0, 0.0, 0.7, 0.7, 0.7, 0.1, 2)
    tf_pop()


def desk(c, w=5.6, d=2.4, h=2.9):
    wd, w2 = MT('wood'), MT('wood2')
    rbox(c, w2, 0, 0, h - 0.22, w, 0.22, d, 0.08, 2)
    rbox(c, wd, -w / 2 + 0.9, 0, 0.0, 1.6, h - 0.22, d - 0.2, 0.06, 2)
    for k in range(3):
        rbox(c, w2, -w / 2 + 0.9, d / 2 - 0.08, 0.25 + k * 0.85, 1.4, 0.7, 0.07, 0.04, 1)
        sphere(c, MT('brass'), -w / 2 + 0.9, d / 2 + 0.03, 0.6 + k * 0.85, 0.09, 0.09, 0.09, 8, 6)
    for sz in (-1, 1):
        lathe(c, wd, [(0.16, 0), (0.1, 0.9), (0.14, h - 0.22)], w / 2 - 0.35, sz * (d / 2 - 0.3), 0, 10)


def kid_chair(c, col='blue'):
    wd = MT('wood')
    for sx in (-1, 1):
        for sz in (-1, 1):
            tube(c, wd, [(sx * 0.65, 0.0, sz * 0.65), (sx * 0.6, 1.6, sz * 0.6)], 0.07, 6)
    lathe(c, MT(col), [(0.0, 1.55), (0.95, 1.55), (1.0, 1.7), (0.95, 1.85), (0.0, 1.88)], 0, 0, 0, 20)
    for sx in (-1, 1):
        tube(c, wd, [(sx * 0.6, 1.6, -0.62), (sx * 0.6, 3.4, -0.62)], 0.07, 6)
    rbox(c, MT(col), 0, -0.64, 2.6, 1.5, 0.7, 0.14, 0.06, 2)


def globe(c):
    lathe(c, MT('metal'), [(0.0, 0), (0.4, 0.0), (0.3, 0.1), (0.08, 0.2), (0.06, 0.5)], 0, 0, 0, 12)
    sphere(c, MT('blue'), 0, 0, 1.05, 0.6, 0.6, 0.6, 16, 10)
    sphere(c, MT('leaf'), 0.18, 0.2, 1.2, 0.32, 0.25, 0.22, 10, 6)


def trophy(c, col='brass', h=1.0):
    lathe(c, MT('dark'), [(0.0, 0), (0.4, 0.0), (0.4, 0.18), (0.0, 0.18)], 0, 0, 0, 12)
    lathe(c, MT(col), [(0.0, 0.18), (0.1, 0.2), (0.1, h * 0.5), (0.25, h * 0.62), (0.4, h * 0.95), (0.34, h), (0.0, h * 0.5)], 0, 0, 0, 14, caps=False)
    for sx in (-1, 1):
        tube(c, MT(col), [(sx * 0.38, h * 0.88, 0.0), (sx * 0.58, h * 0.78, 0.0), (sx * 0.4, h * 0.65, 0.0)], 0.04, 5)


def dartboard(c, r=1.4):
    lathe(c, MT('black'), [(0.0, 0.0), (r + 0.1, 0.0), (r + 0.1, 0.12), (0.0, 0.12)], 0, 0, 0, 36)
    cols = ('red', 'cream', 'red', 'cream')
    for k, rr in enumerate((r, r * 0.78, r * 0.34, r * 0.16)):
        lathe(c, MT(('leaf', 'cream', 'red', 'cream')[k] if k < 2 else ('red', 'leaf')[k - 2]), [(0.0, 0.13 + k * 0.01), (rr, 0.13 + k * 0.01)], 0, 0, 0, 36, caps=False)


def bar_cart(c):
    for sx in (-1, 1):
        for sz in (-1, 1):
            tube(c, MT('brass'), [(sx * 0.8, 0.3, sz * 0.5), (sx * 0.8, 3.0, sz * 0.5)], 0.06, 6)
    for y in (1.0, 3.0):
        rbox(c, MT('wood2'), 0, 0, y - 0.1, 1.9, 0.14, 1.3, 0.05, 1)
    for sx in (-1, 1):
        cylinder(c, MT('dark'), sx * 0.8, 0.5, 0.0, 0.3, 0.17, 10)
    tf_push(-0.55, 0.0, 3.04, 0)
    bottle(c, 'leaf', 'brass', 1.4, 0.24)
    tf_pop()
    tf_push(0.0, 0.1, 3.04, 0)
    bottle(c, 'orange', 'dark', 1.2, 0.22)
    tf_pop()
    tf_push(0.55, 0.0, 3.04, 0)
    bottle(c, 'red', 'brass', 1.0, 0.2)
    tf_pop()
    tf_push(0.3, -0.3, 1.0, 0)
    glass_cup(c, 0.7, 0.2)
    tf_pop()


def recliner(c):
    armchair(c, 'orange', 'orange', 4.4, 4.0)
    tf_push(0.0, 3.1, 0.0, 0)
    rbox(c, MT('orange'), 0, 0, 0.55, 3.2, 1.0, 2.0, 0.4, 3)
    tf_pop()


def round_table(c, r=1.7, h=2.7, col='white'):
    lathe(c, MT(col), [(r, h - 0.2), (r, h), (0, h)], 0, 0, 0, 24)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.5
        tube(c, MT('dark'), [(0.85 * math.cos(a), 0.0, 0.85 * math.sin(a)), (0.2 * math.cos(a), h - 0.2, 0.2 * math.sin(a))], 0.07, 6)


def folding_chair(c):
    for sx in (-1, 1):
        tube(c, MT('dark'), [(sx * 0.7, 0.0, -0.6), (sx * 0.7, 1.7, 0.6)], 0.05, 6)
        tube(c, MT('dark'), [(sx * 0.7, 0.0, 0.6), (sx * 0.7, 1.7, -0.6)], 0.05, 6)
        tube(c, MT('dark'), [(sx * 0.7, 1.7, -0.7), (sx * 0.7, 3.4, -0.9)], 0.05, 6)
    rbox(c, MT('white'), 0, 0.0, 1.7, 1.6, 0.14, 1.5, 0.05, 1)
    rbox(c, MT('white'), 0, -0.85, 2.7, 1.5, 0.8, 0.08, 0.04, 1)


def book(c, m, cx, cz, y0, w, h, d, r=0.04):
    rbox(c, m, cx, cz, y0, w, h, d, r=r, seg=2)


def blob(c, m, cx, cy, cz, r, rnd, seg=12, rings=8, bump=0.16, sy=0.85):
    """lumpy foliage ball"""
    noise = [[1.0 + rnd.uniform(-bump, bump) for _ in range(seg)] for _ in range(rings + 1)]
    verts, faces = [], []
    for k in range(rings + 1):
        a = math.pi * k / rings
        for i in range(seg):
            b = 2 * math.pi * i / seg
            n = 1.0 if k in (0, rings) else noise[k][i]
            verts.append((cx + r * n * math.sin(a) * math.cos(b), cy - r * sy * n * math.cos(a), cz + r * n * math.sin(a) * math.sin(b)))
    for k in range(rings):
        for i in range(seg):
            a0, a1 = k * seg + i, k * seg + (i + 1) % seg
            faces.append((a0, a1, a1 + seg, a0 + seg))
    emit(c, m, verts, faces)


def tree_oak(c, s=1.5, seed=1, kind='oak'):
    rnd = _random.Random(seed)
    COLL.append(('cyl',) + _wpos() + (1.0 * s, 8.0 * s))
    tr = MT('trunk')
    th = 7.5 * s
    lathe(c, tr, [(0.0, 0.0), (1.3 * s, 0.0), (0.95 * s, 0.9 * s), (0.7 * s, 3.5 * s), (0.6 * s, th)], 0, 0, 0, 12)
    for k in range(4):                                    # root flare
        a = 2 * math.pi * k / 4 + 0.5
        tube(c, tr, [(math.cos(a) * 0.5 * s, 0.9 * s, math.sin(a) * 0.5 * s), (math.cos(a) * 1.5 * s, 0.05, math.sin(a) * 1.5 * s)], 0.28 * s, 6)
    cols = {'oak': ('leaf', 'leaf2'), 'apple': ('leaf', 'leaf2'), 'cherry': ('cherry', 'cherry2'), 'autumn': ('autumn', 'autumn2')}[kind]
    cm = [MT('leaf'), MT('leaf2')] if kind in ('oak', 'apple') else [YM(cols[0], {'cherry': '#FF9FC2', 'autumn': '#F08A2E'}[kind]), YM(cols[1], {'cherry': '#FFC4DA', 'autumn': '#E4573D'}[kind])]
    centres = [(0, th + 2.4 * s, 0, 4.2 * s)]
    for k in range(6):
        a = 2 * math.pi * k / 6 + rnd.uniform(-0.3, 0.3)
        centres.append((math.cos(a) * 3.6 * s, th + (1.0 + rnd.uniform(-0.2, 1.4)) * s, math.sin(a) * 3.6 * s, (3.0 + rnd.uniform(0, 0.8)) * s))
    centres.append((rnd.uniform(-1, 1) * s, th + 5.0 * s, rnd.uniform(-1, 1) * s, 3.0 * s))
    for (x, y, z, r) in centres:
        tube(c, tr, [(0, th * 0.78, 0), (x * 0.5, th * 0.9 + (y - th) * 0.4, z * 0.5), (x * 0.8, y - r * 0.4, z * 0.8)], 0.22 * s, 6)
    for k, (x, y, z, r) in enumerate(centres):
        blob(c, cm[k % 2], x, y, z, r, rnd)
    if kind in ('apple', 'cherry'):
        for k in range(14):
            x, y, z, r = centres[rnd.randrange(len(centres))]
            a, e = rnd.uniform(0, 6.28), rnd.uniform(-0.5, 0.6)
            sphere(c, MT('red') if kind == 'apple' else MT('white'), x + math.cos(a) * r * 0.95, z + math.sin(a) * r * 0.95, y + e * r, 0.28 * s, 0.28 * s, 0.28 * s, 8, 5)


def tree_pine(c, s=1.5, seed=1):
    rnd = _random.Random(seed)
    COLL.append(('cyl',) + _wpos() + (0.9 * s, 8.0 * s))
    lathe(c, MT('trunk'), [(0.0, 0.0), (0.9 * s, 0.0), (0.55 * s, 1.0 * s), (0.45 * s, 4.0 * s)], 0, 0, 0, 10)
    pine = YM('pine', '#2A8A4A')
    pine2 = YM('pine2', '#37A25A')
    for k in range(5):
        r = (4.6 - k * 0.8) * s
        y = (2.2 + k * 2.6) * s
        lathe(c, pine if k % 2 == 0 else pine2, [(0.0, y + 4.0 * s), (r * 0.55, y + 2.0 * s), (r * 0.35, y + 2.0 * s), (r, y), (r * 0.8, y - 0.35 * s), (0.2 * s, y - 0.2 * s)], 0, 0, 0, 14, caps=False)


def hedge(c, length, h=3.0, d=2.0, flowers=True, seed=3, axis='x'):
    """rounded hedge along local x (centred)"""
    rnd = _random.Random(seed)
    g1, g2 = MT('leaf'), MT('leaf2')
    rbox(c, g1, 0, 0, 0.0, length, h * 0.8, d, 0.6, 3)
    n = int(length / 1.6)
    for k in range(n):
        x = -length / 2 + (k + 0.5) * length / n
        blob(c, g2 if k % 2 else g1, x, h * 0.78, 0, d * 0.62, rnd, 8, 6, 0.12, 0.8)
    if flowers:
        for k in range(int(length / 1.1)):
            x = rnd.uniform(-length / 2 + 0.4, length / 2 - 0.4)
            sphere(c, MT(rnd.choice(['pink', 'white', 'yellow'])), x, d / 2 + 0.05, rnd.uniform(0.6, h * 0.8), 0.17, 0.17, 0.17, 6, 4)


def bush(c, s=1.0, seed=1, flowers=None):
    rnd = _random.Random(seed)
    for k in range(5):
        a = 2 * math.pi * k / 5
        blob(c, MT('leaf') if k % 2 else MT('leaf2'), math.cos(a) * 0.9 * s, 0.9 * s, math.sin(a) * 0.9 * s, 1.1 * s, rnd, 8, 6, 0.12, 0.85)
    blob(c, MT('leaf'), 0, 1.4 * s, 0, 1.3 * s, rnd, 8, 6, 0.12, 0.85)
    if flowers:
        for k in range(14):
            a, e = rnd.uniform(0, 6.28), rnd.uniform(0.2, 1.3)
            sphere(c, MT(flowers), math.cos(a) * 1.9 * s * (1 - e * 0.3), math.sin(a) * 1.9 * s * (1 - e * 0.3), 0.3 * s + e * 1.1 * s, 0.17, 0.17, 0.17, 6, 4)


def flower_patch(c, w, d, seed=5, cols=('red', 'yellow', 'pink', 'purple', 'orange', 'white')):
    rnd = _random.Random(seed)
    rbox(c, MT('soil'), 0, 0, 0.0, w, 0.35, d, 0.12, 2)
    for k in range(int(w * d * 0.9)):
        x, z = rnd.uniform(-w / 2 + 0.3, w / 2 - 0.3), rnd.uniform(-d / 2 + 0.3, d / 2 - 0.3)
        h = rnd.uniform(0.9, 1.7)
        tube(c, MT('leaf'), [(x, 0.3, z), (x + rnd.uniform(-0.1, 0.1), h * 0.6, z), (x, h, z)], 0.035, 4)
        sphere(c, MT(rnd.choice(cols)), x, z, h + 0.1, 0.2, 0.15, 0.2, 7, 4)
        sphere(c, MT('yellow'), x, z, h + 0.18, 0.07, 0.05, 0.07, 5, 3)
        if k % 3 == 0:
            leaf(c, MT('leaf2'), x, 0.3, z, rnd.uniform(0, 6.28), 0.7, 0.3, 0.5, 0.8, 4)


def raised_bed(c, w, d, crop='veg', seed=2):
    rnd = _random.Random(seed)
    wd = MT('wood2')
    for sz in (-1, 1):
        rbox(c, wd, 0, sz * (d / 2 - 0.12), 0.0, w, 0.9, 0.24, 0.05, 2)
    for sx in (-1, 1):
        rbox(c, wd, sx * (w / 2 - 0.12), 0, 0.0, 0.24, 0.9, d, 0.05, 2)
    rbox(c, MT('soil'), 0, 0, 0.0, w - 0.3, 0.8, d - 0.3, 0.1, 2)
    nx = max(2, int((w - 0.8) / 0.95))
    for k in range(nx):
        x = -w / 2 + 0.7 + k * (w - 1.4) / max(1, nx - 1)
        for zz in (-d / 4, d / 4):
            if crop == 'veg':
                col = ('orange', 'red', 'leaf', 'purple')[(k + (zz > 0)) % 4]
                for j in range(4):
                    leaf(c, MT('leaf'), x, 0.8, zz, j * 1.57 + rnd.random(), 1.0, 0.5, 0.6, 0.9, 4)
                sphere(c, MT(col), x, zz, 1.0, 0.3, 0.3, 0.3, 8, 5)
            else:
                tube(c, MT('leaf'), [(x, 0.8, zz), (x, 2.0, zz)], 0.05, 4)
                sphere(c, MT(rnd.choice(['yellow', 'pink', 'red'])), x, zz, 2.1, 0.3, 0.24, 0.3, 8, 5)


def picket(c, h=3.3):
    m = MT('fence')
    rbox(c, m, 0, 0, 0.0, 0.5, h, 0.2, 0.05, 1)
    lathe(c, m, [(0.36, h), (0.0, h + 0.45)], 0, 0, 0, 4, caps=False)


def fence_line(c, x0, z0, x1, z1, gap=None, step=1.7):
    """pickets + 2 rails + posts from (x0,z0) to (x1,z1); gap=(a,b) along the line is left open (gate)"""
    L = math.hypot(x1 - x0, z1 - z0)
    ux, uz = (x1 - x0) / L, (z1 - z0) / L
    for (ta, tb) in ([(0.0, L)] if not gap else [(0.0, gap[0]), (gap[1], L)]):
        COLL.append(('fence', x0 + ux * ta, z0 + uz * ta, x0 + ux * tb, z0 + uz * tb))
    rot = math.degrees(math.atan2(-uz, ux))
    tf_push((x0 + x1) / 2, (z0 + z1) / 2, 0.0, rot)
    fm = MT('fence')
    segs = [(0.0, L)] if not gap else [(0.0, gap[0]), (gap[1], L)]
    for (ya, yb) in ((0.6, 0.95), (2.1, 2.45)):
        for (a, b) in segs:
            rbox(c, fm, -L / 2 + (a + b) / 2, 0, ya, b - a, yb - ya, 0.3, 0.04, 1)
    n = int(L / step)
    for k in range(n + 1):
        t = k * L / n
        if gap and gap[0] - 0.3 < t < gap[1] + 0.3:
            continue
        tf_push(-L / 2 + t, 0, 0.0, 0)
        picket(c)
        tf_pop()
    posts = [0.0, L] + (list(gap) if gap else [])
    for t in posts:
        gate = bool(gap) and t in gap
        tf_push(-L / 2 + t, 0, 0.0, 0)
        rbox(c, MT('red') if gate else fm, 0, 0, 0.0, 0.9, 4.4, 0.9, 0.12, 2)
        rbox(c, MT('yellow') if gate else fm, 0, 0, 4.4, 1.2, 0.35, 1.2, 0.08, 1)
        lathe(c, MT('yellow') if gate else fm, [(0.5, 4.75), (0.0, 5.2)], 0, 0, 0, 4, caps=False)
        tf_pop()
    tf_pop()


def lamp_post(c):
    COLL.append(('cyl',) + _wpos() + (0.5, 12.0))
    d = MT('dark')
    lathe(c, d, [(0.0, 0.0), (0.9, 0.0), (0.7, 0.4), (0.3, 1.2), (0.22, 2.0), (0.2, 11.0)], 0, 0, 0, 12)
    torus(c, d, 0, 0, 1.6, 0.3, 0.08, 'xz', 14, 5)
    tube(c, d, [(0, 11.0, 0), (0, 11.8, 0), (0.7, 12.3, 0)], 0.12, 6)
    lathe(c, d, [(0.55, 12.3), (0.75, 12.55), (0.0, 12.85)], 0.7, 0, 0, 12, caps=False)
    lathe(c, MT('lamp'), [(0.0, 11.65), (0.42, 11.75), (0.5, 12.2), (0.0, 12.28)], 0.7, 0, 0, 12)
    lathe(c, d, [(0.0, 11.5), (0.55, 11.55), (0.0, 11.6)], 0.7, 0, 0, 12)


def mailbox(c):
    tube(c, MT('trunk'), [(0, 0, 0), (0, 4.4, 0)], 0.2, 8)
    rbox(c, MT('trunk'), 0, 0, 3.9, 0.9, 0.3, 0.9, 0.08, 1)
    lathe(c, MT('blue'), [(0.62, 0.0), (0.7, 0.9), (0.55, 1.3), (0.0, 1.45)], 0, 0, 0, 14, caps=False, sx=1.0, sz=1.5) if False else None
    rbox(c, MT('blue'), 0, 0, 4.2, 1.5, 1.3, 2.4, 0.5, 4)
    tube(c, MT('red'), [(0.78, 4.8, 0.5), (0.78, 5.9, 0.5)], 0.06, 5)
    rbox(c, MT('red'), 0.82, 0.5, 5.5, 0.1, 0.55, 0.8, 0.03, 1)
    rbox(c, MT('white'), 0, 1.22, 4.55, 0.7, 0.4, 0.05, 0.02, 1)


def hydrant(c):
    r = MT('red')
    lathe(c, r, [(0.0, 0.0), (0.85, 0.0), (0.8, 0.3), (0.55, 0.5), (0.55, 2.1), (0.7, 2.25), (0.7, 2.5), (0.5, 2.7), (0.0, 3.0)], 0, 0, 0, 14)
    for sx in (-1, 1):
        lathe(c, r, [(0.0, 1.5), (0.28, 1.5), (0.28, 1.9), (0.0, 1.9)], sx * 0.75, 0, 0, 10)
        sphere(c, MT('metal'), sx * 1.0, 0, 1.7, 0.2, 0.2, 0.2, 8, 5)
    sphere(c, MT('metal'), 0, 0.7, 1.7, 0.22, 0.22, 0.22, 8, 5)


def bench(c, w=6.0, col='wood2'):
    wd = MT(col)
    for k in range(4):
        rbox(c, wd, 0, -0.55 - k * 0.0, 1.55 + k * 0.45, w, 0.3, 0.2, 0.06, 1)
    for k in range(3):
        rbox(c, wd, 0, 0.1 + k * 0.5 - 0.5, 1.5, w, 0.22, 0.4, 0.06, 1)
    for sx in (-1, 1):
        for sz in (-1, 1):
            rbox(c, MT('dark'), sx * (w / 2 - 0.4), sz * 0.55, 0.0, 0.25, 1.55, 0.25, 0.05, 1)
        tube(c, MT('dark'), [(sx * (w / 2 - 0.2), 1.6, 0.7), (sx * (w / 2 - 0.2), 1.6, -0.7)], 0.08, 5)
        tube(c, MT('dark'), [(sx * (w / 2 - 0.2), 1.6, -0.55), (sx * (w / 2 - 0.2), 3.3, -0.65)], 0.09, 5)


def trash_can(c, col='dark'):
    lathe(c, MT(col), [(0.0, 0.0), (0.7, 0.0), (0.85, 0.2), (0.95, 2.9), (0.0, 2.9)], 0, 0, 0, 14, caps=False)
    lathe(c, MT(col), [(0.0, 3.1), (1.0, 3.0), (1.0, 2.85), (0.0, 2.85)], 0, 0, 0, 14)
    cylinder(c, MT('metal'), 0, 0, 3.1, 0.15, 0.25, 8)
    torus(c, MT('metal'), 0, 0, 3.0, 0.98, 0.05, 'xz', 20, 4)


def car(c, col='red', win='glass'):
    body, dk, tire = MT(col), MT('dark'), MT('black')
    rbox(c, body, 0, 0, 0.9, 4.2, 1.4, 9.6, 0.55, 4)
    rbox(c, body, 0, -0.5, 2.0, 3.7, 1.35, 5.2, 0.6, 4)
    rbox(c, MT(win), 0, 1.9, 2.1, 3.3, 1.05, 0.1, 0.3, 2)
    rbox(c, MT(win), 0, -2.9, 2.1, 3.3, 1.05, 0.1, 0.3, 2)
    for sx in (-1, 1):
        rbox(c, MT(win), sx * 1.88, -0.4, 2.15, 0.1, 1.0, 4.4, 0.2, 2)
        rbox(c, MT('white'), sx * 1.9, 0.35, 1.7, 0.08, 0.12, 0.7, 0.03, 1)
        for sz in (-1, 1):
            tf_push(sx * 1.85, sz * 3.0, 0.8, 0)
            torus(c, tire, 0, 0, 0, 0.72, 0.36, 'zy' if False else 'yz', 18, 8)
            sphere(c, MT('metal'), sx * 0.1, 0, 0, 0.14, 0.6, 0.6, 12, 6)
            tf_pop()
        sphere(c, MT('lamp'), sx * 1.4, 4.78, 1.9, 0.45, 0.35, 0.18, 10, 6)
        sphere(c, MT('red'), sx * 1.5, -4.78, 1.9, 0.4, 0.3, 0.15, 8, 5)
    rbox(c, MT('metal'), 0, 4.85, 1.0, 3.8, 0.5, 0.3, 0.1, 2)
    rbox(c, MT('metal'), 0, -4.85, 1.0, 3.8, 0.5, 0.3, 0.1, 2)
    rbox(c, dk, 0, 4.88, 1.7, 2.0, 0.55, 0.12, 0.05, 1)
    rbox(c, MT('white'), 0, -4.95, 1.2, 1.2, 0.4, 0.06, 0.02, 1)


def bbq(c):
    d = MT('black')
    lathe(c, d, [(0.0, 3.3), (1.4, 3.3), (1.55, 3.9), (1.25, 4.6), (0.0, 4.65)], 0, 0, 0, 18, caps=False)
    lathe(c, d, [(0.0, 3.3), (1.2, 3.2), (0.0, 2.6)], 0, 0, 0, 18, caps=False)
    for k in range(3):
        a = 2 * math.pi * k / 3
        tube(c, MT('metal'), [(0, 2.8, 0), (math.cos(a) * 1.2, 0.0, math.sin(a) * 1.2)], 0.07, 6)
    for sx in (-1, 1):
        tube(c, MT('metal'), [(sx * 1.5, 3.6, 0), (sx * 1.9, 3.5, 0)], 0.06, 5)
    sphere(c, MT('red'), 0, 0, 4.85, 0.18, 0.18, 0.18, 8, 5)
    rbox(c, MT('metal'), 0, 0.2, 3.55, 2.6, 0.06, 1.6, 0.02, 1)


def picnic_table(c, umbrella=True):
    wd = MT('wood2')
    rbox(c, wd, 0, 0, 2.7, 7.0, 0.3, 3.0, 0.08, 2)
    for sz in (-1, 1):
        rbox(c, wd, 0, sz * 2.5, 1.6, 7.0, 0.28, 1.0, 0.08, 2)
    for sx in (-1, 1):
        for sz in (-1, 1):
            tube(c, MT('wood'), [(sx * 2.8, 2.7, sz * 0.9), (sx * 3.1, 0.0, sz * 2.7)], 0.16, 6)
        tube(c, MT('wood'), [(sx * 2.95, 1.6, -2.7), (sx * 2.95, 1.6, 2.7)], 0.16, 6)
    if umbrella:
        tube(c, MT('metal'), [(0, 2.8, 0), (0, 9.5, 0)], 0.1, 6)
        lathe(c, MT('red'), [(0.0, 10.4), (1.9, 9.9), (3.9, 9.3), (4.1, 9.2), (0.0, 9.35)], 0, 0, 0, 16, caps=False)
        lathe(c, MT('white'), [(0.0, 10.38), (0.9, 10.15), (2.0, 9.85), (3.0, 9.55)], 0, 0, 0, 16, caps=False) if False else None
    for k in range(3):
        tf_push(-2.2 + k * 2.0, 0.2 * (k - 1), 3.0, 0)
        plate(c, ('white', 'blue', 'yellow')[k], 0.55)
        tf_pop()


def doghouse(c):
    rbox(c, MT('red'), 0, 0, 0.0, 3.6, 2.6, 3.8, 0.12, 2)
    emit(c, MT('roof_dk'), [(-2.1, 2.5, 2.1), (2.1, 2.5, 2.1), (2.1, 3.9, 0.0), (-2.1, 3.9, 0.0)], [(0, 1, 2, 3)], True)
    emit(c, MT('roof_dk'), [(-2.1, 3.9, 0.0), (2.1, 3.9, 0.0), (2.1, 2.5, -2.1), (-2.1, 2.5, -2.1)], [(0, 1, 2, 3)], True)
    lathe(c, MT('dark'), [(0.0, 0.0), (0.8, 0.0), (0.8, 1.4), (0.0, 1.9)], 0, 1.92, 0, 14, sx=1.0, sz=0.1, caps=False)
    rbox(c, MT('red'), 0, 2.2, 0.0, 1.6, 0.05, 1.0, 0.02, 1)
    lathe(c, MT('blue'), [(0.0, 0.0), (0.9, 0.0), (0.8, 0.3), (0.0, 0.3)], 2.9, 2.0, 0, 14)


def bike(c):
    for z in (-1.7, 1.7):
        torus(c, MT('black'), 0, z, 1.1, 1.05, 0.08, 'yz', 22, 5)
        sphere(c, MT('metal'), 0, z, 1.1, 0.07, 0.12, 0.12, 6, 4)
    tube(c, MT('red'), [(0, 1.1, -1.7), (0, 2.5, -0.5), (0, 2.6, 0.9), (0, 1.1, 1.7)], 0.1, 6)
    tube(c, MT('red'), [(0, 1.1, -1.7), (0, 1.1, -0.1), (0, 2.5, -0.5)], 0.08, 5)
    tube(c, MT('dark'), [(0, 2.5, -0.55), (0, 3.0, -0.6)], 0.07, 5)
    rbox(c, MT('dark'), 0, -0.6, 3.0, 0.4, 0.14, 1.0, 0.05, 1)
    tube(c, MT('dark'), [(-0.6, 3.1, 0.95), (0.6, 3.1, 0.95)], 0.07, 5)
    tube(c, MT('metal'), [(0, 2.6, 0.9), (0, 3.1, 0.95)], 0.07, 5)


def pot_plant(c, col='terra', s=1.0, big=False, leaves=10):
    potted_plant(c, s, col, big, leaves)


def house_nb(c, w, d, h, wall, roof, seed=1):
    COLL.append(('box',) + _wpos() + (w, d, h + 6.0))
    """neighbour house: walls, gable roof along x, windows, door, chimney, porch step"""
    rnd = _random.Random(seed)
    wm = YM('nb' + wall, wall, 0.8)
    rm = YM('nr' + roof, roof, 0.7)
    rbox(c, wm, 0, 0, 0.0, w, h, d, 0.2, 2)
    rise = h * 0.42
    ov = 1.6
    emit(c, rm, [(-w / 2 - ov, h - 0.4, d / 2 + ov), (w / 2 + ov, h - 0.4, d / 2 + ov), (w / 2 + ov, h + rise, 0.0), (-w / 2 - ov, h + rise, 0.0)], [(0, 1, 2, 3)], True)
    emit(c, rm, [(-w / 2 - ov, h + rise, 0.0), (w / 2 + ov, h + rise, 0.0), (w / 2 + ov, h - 0.4, -d / 2 - ov), (-w / 2 - ov, h - 0.4, -d / 2 - ov)], [(0, 1, 2, 3)], True)
    rbox(c, MT('roof_dk'), 0, 0, h + rise - 0.1, w + 2 * ov + 0.3, 0.5, 0.7, 0.1, 1)
    for sx in (-1, 1):
        emit(c, wm, [(sx * w / 2, h - 0.2, -d / 2), (sx * w / 2, h - 0.2, d / 2), (sx * w / 2, h + rise - 0.6, 0.0)], [(0, 1, 2)], True)
    rbox(c, MT('chimney'), w * 0.25, -d * 0.15, h, 2.4, rise + 3.2, 2.4, 0.15, 1)
    rbox(c, MT('dark'), w * 0.25, -d * 0.15, h + rise + 3.0, 3.0, 0.5, 3.0, 0.1, 1)
    fz = d / 2 + 0.05
    for k in range(3):
        x = -w / 2 + w * (k + 0.5) / 3
        if k == 1:
            rbox(c, MT('trim'), x, fz, 0.0, 4.2, 7.6, 0.25, 0.06, 2)
            rbox(c, MT(rnd.choice(['door', 'red', 'blue'])), x, fz + 0.1, 0.0, 3.4, 7.0, 0.2, 0.08, 2)
            sphere(c, MT('brass'), x + 1.2, fz + 0.35, 3.5, 0.17, 0.17, 0.17, 8, 5)
            rbox(c, MT('plinth'), x, fz + 1.4, 0.0, 6.0, 0.5, 3.0, 0.1, 1)
        else:
            rbox(c, MT('trim'), x, fz, 3.5, 4.6, 4.2, 0.25, 0.06, 2)
            rbox(c, MT('glass'), x, fz + 0.1, 3.8, 3.8, 3.5, 0.15, 0.05, 1)
            rbox(c, MT('trim'), x, fz + 0.2, 3.8, 0.2, 3.5, 0.12, 0.02, 1)
            rbox(c, MT('trim'), x, fz + 0.2, 5.5, 3.8, 0.2, 0.12, 0.02, 1)
            rbox(c, MT('shutter'), x - 2.9, fz + 0.1, 3.5, 1.1, 4.2, 0.2, 0.05, 1)
            rbox(c, MT('shutter'), x + 2.9, fz + 0.1, 3.5, 1.1, 4.2, 0.2, 0.05, 1)
        x2 = x
        rbox(c, MT('trim'), x2, fz, h * 0.58 + 3.2, 4.6, 3.8, 0.25, 0.06, 2) if h > 15 else None
        if h > 15:
            rbox(c, MT('glass'), x2, fz + 0.1, h * 0.58 + 3.4, 3.8, 3.2, 0.15, 0.05, 1)


def street_tree(c, s=1.0, seed=1):
    tree_oak(c, s, seed, 'oak')


def crosswalk(c, x0, z0, n=9):
    for k in range(n):
        rbox(c, MT('white'), x0 + k * 1.8, z0, 0.0, 1.0, 0.04, 8.0, 0.01, 1)


def manhole(c):
    cylinder(c, MT('dark'), 0, 0, 0.0, 0.08, 1.2, 18)
    torus(c, MT('metal'), 0, 0, 0.1, 1.15, 0.06, 'xz', 20, 4)


def stepping_stones(c, pts, seed=3):
    rnd = _random.Random(seed)
    for (x, z) in pts:
        rbox(c, MT('walk'), x, z, 0.0, 2.2 + rnd.uniform(-0.2, 0.3), 0.18, 1.8 + rnd.uniform(-0.2, 0.3), 0.3, 2)


def garden_shed(c):
    """walk-in shed (12 x 9, wall 0.6): door opening in the front (+lz) wall, floor, workbench shelf with the spare key spot"""
    sd = MT('door2')
    wd = MT('wood')
    for (lx, lz, sx, sz, h) in ((0.0, -4.2, 12.0, 0.6, 11.0), (-5.7, 0.0, 0.6, 9.0, 11.0), (5.7, 0.0, 0.6, 9.0, 11.0), (-3.85, 4.2, 4.3, 0.6, 11.0), (3.85, 4.2, 4.3, 0.6, 11.0)):
        _wbox(lx, lz, sx, sz, h)
    rbox(c, sd, 0, -4.2, 0.0, 12.0, 8.0, 0.6, 0.1, 2)
    for sx in (-1, 1):
        rbox(c, sd, sx * 5.7, 0, 0.0, 0.6, 8.0, 9.0, 0.1, 2)
    rbox(c, sd, -3.85, 4.2, 0.0, 4.3, 8.0, 0.6, 0.1, 2)
    rbox(c, sd, 3.85, 4.2, 0.0, 4.3, 8.0, 0.6, 0.1, 2)
    rbox(c, sd, 0, 4.2, 6.2, 3.4, 1.8, 0.6, 0.1, 2)
    rbox(c, MT('plinth'), 0, 0, 0.0, 11.4, 0.25, 8.4, 0.05, 1)
    for k in range(12):
        rbox(c, wd, -5.8 + k * 1.06, 4.52, 0.1, 0.07, 7.7, 0.08, 0.02, 1)
    # gable roof
    emit(c, MT('red'), [(-6.7, 7.9, 5.1), (6.7, 7.9, 5.1), (6.7, 11.0, 0.0), (-6.7, 11.0, 0.0)], [(0, 1, 2, 3)], True)
    emit(c, MT('red'), [(-6.7, 11.0, 0.0), (6.7, 11.0, 0.0), (6.7, 7.9, -5.1), (-6.7, 7.9, -5.1)], [(0, 1, 2, 3)], True)
    rbox(c, MT('roof_dk'), 0, 0, 10.9, 13.6, 0.35, 0.6, 0.08, 1)
    for sx in (-1, 1):
        emit(c, MT('door2'), [(sx * 6.0, 8.0, -4.5), (sx * 6.0, 8.0, 4.5), (sx * 6.0, 10.8, 0.0)], [(0, 1, 2)], True)
    # door frame (the leaf itself is an interactive Studio part)
    rbox(c, MT('trim'), -1.85, 4.62, 0.0, 0.3, 6.4, 0.26, 0.05, 1)
    rbox(c, MT('trim'), 1.85, 4.62, 0.0, 0.3, 6.4, 0.26, 0.05, 1)
    rbox(c, MT('trim'), 0, 4.62, 6.2, 4.0, 0.3, 0.26, 0.05, 1)
    rbox(c, MT('plinth'), 0, 5.2, 0.0, 3.8, 0.3, 1.4, 0.08, 1)
    # side window with a flower box
    rbox(c, MT('trim'), -5.98, 0.0, 3.0, 0.2, 2.4, 2.4, 0.06, 2)
    rbox(c, MT('glass'), -5.99, 0.0, 3.2, 0.08, 1.9, 1.9, 0.04, 1)
    # interior: workbench shelf with tools and the key spot, hanging tools, pots
    rbox(c, MT('wood2'), 3.0, -3.7, 2.6, 5.4, 0.25, 1.3, 0.06, 2)
    for sx in (-1, 1):
        rbox(c, MT('wood'), 3.0 + sx * 2.5, -3.7, 0.25, 0.25, 2.4, 1.1, 0.04, 1)
    for k in range(4):
        cylinder(c, MT(('terra', 'red', 'blue', 'yellow')[k]), 0.8 + k * 0.9, -3.8, 2.85, 0.7, 0.34, 10)
    rbox(c, MT('wood2'), -3.0, -3.9, 5.0, 4.4, 0.2, 0.9, 0.05, 2)
    for k in range(5):
        tube(c, MT('metal'), [(-4.6 + k * 0.8, 5.0, -3.5), (-4.6 + k * 0.8, 3.4, -3.5)], 0.06, 5)
    cylinder(c, MT('red'), -4.4, 3.2, 0.25, 1.4, 0.7, 12)
    rbox(c, MT('cardboard'), -4.3, -2.6, 0.25, 1.8, 1.4, 1.4, 0.1, 2)
    anchor('shed_door', 0.0, 0.0, 4.5)
    anchor('shed_key', 4.4, 2.85, -3.7)
    # leaning ladder outside
    for sx in (-0.5, 0.5):
        tube(c, MT('wood'), [(7.3 + sx, 0.0, 5.0), (7.3 + sx, 8.0, 4.6)], 0.1, 5)
    for k in range(7):
        tube(c, MT('wood'), [(6.8, 0.9 + k * 1.0, 4.95 - k * 0.05), (7.8, 0.9 + k * 1.0, 4.95 - k * 0.05)], 0.06, 4)


def swing_set(c):
    for sx in (-1, 1):
        for sz in (-1, 1):
            _wcyl(sx * 5.6, sz * 2.4, 0.3, 7.5)
    m = MT('red')
    for sz in (-1, 1):
        for sx in (-1, 1):
            tube(c, m, [(sx * 4.3, 7.5, 0), (sx * 5.6, 0.0, sz * 2.4)], 0.2, 8)
        tube(c, m, [(-4.3, 7.5, 0), (-4.3, 7.5, 0)], 0.01, 3) if False else None
    tube(c, m, [(-4.4, 7.5, 0), (4.4, 7.5, 0)], 0.24, 8)
    for sx in (-3.0, 0.4):
        for dx in (-0.55, 0.55):
            tube(c, MT('metal'), [(sx + dx, 7.4, 0), (sx + dx, 1.9, 0.0)], 0.05, 4)
        rbox(c, MT('yellow'), sx, 0, 1.7, 1.5, 0.22, 0.7, 0.08, 2)
    tube(c, MT('metal'), [(3.0, 7.4, 0), (3.0, 4.4, 0)], 0.05, 4)
    lathe(c, MT('blue'), [(0.0, 4.4), (0.5, 4.2), (0.8, 4.0), (0.8, 3.6), (0.0, 3.5)], 3.0, 0, 0, 10, caps=False)


def sandbox(c):
    wd = MT('wood2')
    for sz in (-1, 1):
        rbox(c, wd, 0, sz * 3.1, 0.0, 6.6, 0.8, 0.4, 0.08, 2)
    for sx in (-1, 1):
        rbox(c, wd, sx * 3.1, 0, 0.0, 0.4, 0.8, 6.0, 0.08, 2)
    rbox(c, YM('sand', '#F0DCA0'), 0, 0, 0.0, 5.8, 0.65, 5.8, 0.2, 2)
    lathe(c, MT('red'), [(0.0, 0.65), (0.7, 0.65), (0.55, 1.4), (0.0, 1.4)], -1.0, 0.5, 0, 12, caps=False)
    lathe(c, MT('blue'), [(0.0, 0.65), (0.5, 0.65), (0.6, 1.0), (0.0, 1.0)], 1.0, -0.8, 0, 12, caps=False)
    tube(c, MT('yellow'), [(0.5, 0.7, 1.2), (1.7, 1.2, 1.9)], 0.07, 5)
    rbox(c, MT('yellow'), 1.9, 1.95, 1.2, 0.7, 0.18, 0.5, 0.05, 1)


def trampoline(c):
    _wcyl(0.0, 0.0, 3.5, 2.3)
    for k in range(6):
        a = 2 * math.pi * k / 6
        tube(c, MT('metal'), [(math.cos(a) * 3.2, 2.2, math.sin(a) * 3.2), (math.cos(a) * 3.5, 0.0, math.sin(a) * 3.5)], 0.1, 5)
    torus(c, MT('blue'), 0, 0, 2.3, 3.5, 0.28, 'xz', 28, 6)
    lathe(c, MT('black'), [(0.0, 2.2), (3.2, 2.2), (3.4, 2.25), (0.0, 2.25)], 0, 0, 0, 28, caps=False)
    for k in range(18):
        a = 2 * math.pi * k / 18
        tube(c, MT('metal'), [(math.cos(a) * 3.2, 2.2, math.sin(a) * 3.2), (math.cos(a) * 3.5, 2.3, math.sin(a) * 3.5)], 0.04, 4)


def clothesline(c, seed=2):
    rnd = _random.Random(seed)
    for sx in (-1, 1):
        tube(c, MT('metal'), [(sx * 6.0, 0.0, 0), (sx * 6.0, 7.2, 0), (sx * 5.2, 7.2, 0)], 0.14, 6)
    tube(c, MT('white'), [(-5.2, 6.8, 0), (-1.0, 6.4, 0), (3.0, 6.5, 0), (5.2, 6.8, 0)], 0.03, 4)
    for k in range(5):
        x = -4.4 + k * 2.0
        col = ('red', 'blue', 'yellow', 'teal', 'pink')[k]
        sheet(c, MT(col), x - 0.7, x + 0.7, 4.0 + rnd.random() * 0.3, 6.6, 0.0, folds=2, amp=0.1, nx=8, axis='x')


def birdhouse(c):
    tube(c, MT('trunk'), [(0, 0, 0), (0, 6.0, 0)], 0.22, 6)
    rbox(c, MT('yellow'), 0, 0, 6.0, 1.7, 1.5, 1.5, 0.12, 2)
    lathe(c, MT('red'), [(1.4, 7.5), (0.0, 8.5)], 0, 0, 0, 4, caps=False)
    cylinder(c, MT('dark'), 0, 0.77, 6.6, 0.05, 0.35, 12)
    tube(c, MT('trunk'), [(0, 6.6, 0.9), (0, 6.6, 1.5)], 0.06, 4)


def birdbath(c):
    s = MT('plinth')
    lathe(c, s, [(0.0, 0.0), (1.1, 0.0), (0.5, 0.4), (0.4, 2.2), (1.7, 2.8), (1.9, 3.1), (1.6, 3.1), (0.0, 2.9)], 0, 0, 0, 16)
    lathe(c, MT('glass'), [(0.0, 3.0), (1.5, 3.05)], 0, 0, 0, 16, caps=False)
    sphere(c, MT('blue'), 0.4, 0.2, 3.3, 0.28, 0.22, 0.2, 8, 5)


def gnome(c):
    sphere(c, MT('blue'), 0, 0, 0.7, 0.55, 0.7, 0.55, 10, 6)
    sphere(c, MT('skin'), 0, 0.2, 1.5, 0.32, 0.32, 0.32, 8, 5)
    lathe(c, MT('red'), [(0.45, 1.6), (0.0, 2.9)], 0, 0.05, 0, 10, caps=False)
    lathe(c, MT('white'), [(0.4, 1.35), (0.0, 1.0)], 0, 0.3, 0, 8, caps=False)
