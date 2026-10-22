HQ_MODELS_1 = '''
# ---------------------------------------------------------------- generic furniture models (local frame: +lz is the front)
def P_(u, v, fl, rot=0.0):
    tf_push(HX + u, HZ + v, fl, rot)


def sofa(c, w=8.6, d=3.5, col='sofa', col2='sofa2', pillows=('yellow', 'red', 'cream')):
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
        L = (2.2 if big else 1.5) * s * rnd.uniform(0.8, 1.2)
        leaf(c, MT(lcol[k % 2]), 0.15 * math.cos(a), 1.4 * s, 0.15 * math.sin(a), a, L, 0.85 * s * (1.4 if big else 1.0), 0.55 + 0.25 * rnd.random(), 0.9)


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
    rbox(c, MT(border), 0, 0, 0, w, 0.08, d, 0.03, 1)
    rbox(c, MT(base), 0, 0, 0.08, w - 0.9, 0.05, d - 0.9, 0.02, 1)
    for k in range(5):
        rbox(c, MT(stripe), 0, -d / 2 + 1.2 + k * (d - 2.4) / 4, 0.13, w - 1.6, 0.03, 0.12, 0.01, 1)
    sphere(c, MT(stripe), 0, 0, 0.15, min(w, d) * 0.2, 0.03, min(w, d) * 0.2, 20, 4)
    if fringe:
        for sx in (-1, 1):
            for k in range(int(d / 0.28)):
                rbox(c, MT('cream'), sx * (w / 2 + 0.2), -d / 2 + 0.2 + k * 0.28, 0.0, 0.4, 0.04, 0.1, 0.015, 1)


def curtain_pair(c, ac, wspan, y_top, drop, z, axis='x', col='coral', open_=True):
    """two curtains + rod + finials around a window centred at ac"""
    g = MT(col)
    x0, x1 = ac - wspan / 2, ac + wspan / 2
    if axis == 'x':
        tube(c, MT('brass'), [(x0 - 0.5, y_top, z), (x1 + 0.5, y_top, z)], 0.08, 8)
        for xx in (x0 - 0.55, x1 + 0.55):
            sphere(c, MT('brass'), xx, z, y_top, 0.2, 0.2, 0.2, 10, 6)
        sheet(c, g, x0 - 0.3, x0 + 1.5, y_top - drop, y_top - 0.12, z, folds=5, amp=0.16, axis='x')
        sheet(c, g, x1 - 1.5, x1 + 0.3, y_top - drop, y_top - 0.12, z, folds=5, amp=0.16, axis='x')
    else:
        tube(c, MT('brass'), [(z, y_top, x0 - 0.5), (z, y_top, x1 + 0.5)], 0.08, 8)
        for zz in (x0 - 0.55, x1 + 0.55):
            sphere(c, MT('brass'), z, zz, y_top, 0.2, 0.2, 0.2, 10, 6)
        sheet(c, g, x0 - 0.3, x0 + 1.5, y_top - drop, y_top - 0.12, z, folds=5, amp=0.16, axis='z')
        sheet(c, g, x1 - 1.5, x1 + 0.3, y_top - drop, y_top - 0.12, z, folds=5, amp=0.16, axis='z')


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
'''
