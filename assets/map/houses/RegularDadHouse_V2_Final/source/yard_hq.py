# HQ yard / street / neighbourhood (executed inside build_house_v5.py; coordinates are FINAL plot coordinates, not warped).
# Lot: x 0..98.6, z 0..99.4 (front = south, z grows toward the street), house x 22..76.6, z 18..85.4, sidewalk z 101.4..109.4, road z 111.4..135.4.
FY = 'Furn_Y'
COLL = []     # (kind, x, z, size...) world-space collision proxies for the yard (boxes / cylinders)


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


def YM(name, hexcol=None, rough=0.7):
    return mat(name, hexcol, rough=rough) if hexcol else MT(name)


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


def gazebo(c):
    w = MT('trim')
    lathe(c, MT('plinth'), [(0.0, 0.0), (5.4, 0.0), (5.4, 0.7), (0.0, 0.7)], 0, 0, 0, 8)
    for k in range(8):
        a = 2 * math.pi * k / 8 + math.pi / 8
        x, z = math.cos(a) * 4.6, math.sin(a) * 4.6
        if k != 2:
            tube(c, w, [(x, 0.7, z), (x, 8.2, z)], 0.22, 8)
        rbox(c, w, x, z, 7.6, 0.7, 0.6, 0.7, 0.1, 1)
    for k in range(8):
        a, b = 2 * math.pi * k / 8 + math.pi / 8, 2 * math.pi * (k + 1) / 8 + math.pi / 8
        tube(c, w, [(math.cos(a) * 4.6, 8.0, math.sin(a) * 4.6), (math.cos(b) * 4.6, 8.0, math.sin(b) * 4.6)], 0.18, 6)
        if k != 2:
            tube(c, w, [(math.cos(a) * 4.6, 3.6, math.sin(a) * 4.6), (math.cos(b) * 4.6, 3.6, math.sin(b) * 4.6)], 0.1, 5)
    lathe(c, MT('red'), [(0.0, 11.4), (2.2, 10.2), (5.6, 8.3), (6.0, 8.1), (5.6, 8.0), (0.0, 8.0)], 0, 0, 0, 8, caps=False)
    sphere(c, MT('brass'), 0, 0, 11.6, 0.35, 0.35, 0.35, 8, 5)
    rbox(c, MT('wood2'), 0, -2.5, 0.7, 5.0, 0.9, 0.9, 0.08, 2)
    rbox(c, MT('wood2'), 0, -2.9, 1.6, 5.0, 1.4, 0.2, 0.06, 1)
    tf_push(0, 1.0, 0.7, 0)
    rbox(c, MT('wood'), 0, 0, 0.0, 2.2, 1.9, 2.2, 0.1, 2)
    tf_pop()


def pond(c, seed=3):
    rnd = _random.Random(seed)
    lathe(c, MT('glass'), [(0.0, 0.05), (4.6, 0.05)], 0, 0, 0, 24, sx=1.0, sz=0.72, caps=False)
    for k in range(14):
        a = 2 * math.pi * k / 14
        blob(c, MT('plinth'), math.cos(a) * 4.8, 0.3, math.sin(a) * 4.8 * 0.72, rnd.uniform(0.5, 0.9), rnd, 6, 5, 0.2, 0.7)
    for k in range(4):
        lathe(c, MT('leaf2'), [(0.0, 0.1), (0.55, 0.1)], rnd.uniform(-2.5, 2.5), rnd.uniform(-1.5, 1.5), 0, 8, caps=False)
    sphere(c, MT('pink'), 1.2, 0.5, 0.2, 0.3, 0.2, 0.3, 8, 5)
    for k in range(5):
        x = -3.4 + k * 0.7
        tube(c, MT('leaf'), [(x, 0.0, 2.1), (x + 0.1, 1.8, 2.1), (x + 0.2, 2.6, 2.1)], 0.06, 4)
        sphere(c, MT('trunk'), x + 0.2, 2.1, 2.7, 0.12, 0.35, 0.12, 6, 4)
    sphere(c, MT('yellow'), -1.0, 0.4, 0.45, 0.45, 0.35, 0.55, 10, 6)
    sphere(c, MT('yellow'), -1.0, 0.1, 0.95, 0.25, 0.25, 0.25, 8, 5)
    lathe(c, MT('orange'), [(0.0, 0.0), (0.18, 0.0), (0.0, 0.3)], -1.0, -0.35, 0.8, 6, caps=False)


def hq_yard():
    X1, Z1 = 98.6, 99.4
    S = FY
    rnd = _random.Random(7)

    def at(x, z, rot=0.0, y=0.0):          # lot item: follows the lot shift
        tf_push(x, z + DZ, y, rot)

    def at0(x, z, rot=0.0, y=0.0):         # street / neighbourhood item: fixed on the map
        tf_push(x, z, y, rot)

    # ---------------- fence (front with gate in front of the path, back with gate to the east path)
    fence_line(S, 0.6, Z1 + DZ, X1 - 0.6, Z1 + DZ, gap=(31.5 - 0.6, 40.6 - 0.6))
    fence_line(S, 0.6, 0.6 + DZ, X1 - 0.6, 0.6 + DZ, gap=(80.6 - 0.6, 86.6 - 0.6))
    fence_line(S, 0.6, 0.6 + DZ, 0.6, Z1 + DZ, step=1.7)
    fence_line(S, X1 - 0.6, 0.6 + DZ, X1 - 0.6, Z1 + DZ, step=1.7)
    # front path from the gate across the empty lawn to the sidewalk
    zg, zs = Z1 + DZ, 101.4
    rbox(S, MT('path'), 36.0, (zg + zs) / 2, 0.0, 7.6, 0.12, zs - zg + 0.4, 0.0, 1)
    for k in range(int((zs - zg) / 3.0)):
        rbox(S, MT('walk'), 36.0, zg + 1.5 + k * 3.0, 0.12, 7.4, 0.03, 0.12, 0.0, 1)
    # ---------------- front yard (hedge along the fence, flowers between hedge and the cross path)
    for (x, ln) in ((14.0, 22.0), (62.0, 36.0)):
        at(x, 97.7)
        hedge(S, ln, 3.4, 1.9, True, int(x))
        tf_pop()
    for (x, k) in ((14.0, 11), (26.0, 12), (48.0, 13), (60.0, 14), (74.0, 15)):
        at(x, 95.3)
        flower_patch(S, 7.0, 2.0, k)
        tf_pop()
    at(8.0, 91.5)
    tree_oak(S, 1.3, 3, 'oak')
    tf_pop()
    at(88.0, 93.5)
    tree_oak(S, 1.4, 4, 'apple')
    tf_pop()
    for (x, z, sc, fl) in ((17.0, 87.0, 1.0, 'pink'), (24.0, 88.4, 0.9, 'white'), (80.5, 88.2, 1.0, 'yellow')):
        at(x, z)
        bush(S, sc, int(x), fl)
        tf_pop()
    at(31.0, 90.0)
    pot_plant(S, 'terra', 1.0, True, 12)
    tf_pop()
    at(43.2, 90.0)
    pot_plant(S, 'blue', 1.0, True, 12)
    tf_pop()
    at(20.0, 92.5)
    birdbath(S)
    tf_pop()
    at(14.5, 91.0)
    gnome(S)
    tf_pop()
    at(28.3, 97.0, 90)
    bike(S)
    tf_pop()
    at0(44.5, 101.0, 0)
    mailbox(S)
    tf_pop()
    # ---------------- west side yard
    at(5.0, 26.0)
    tree_pine(S, 0.8, 22)
    tf_pop()
    at(14.0, 24.0, 0)
    raised_bed(S, 9.0, 3.6, 'veg', 5)
    tf_pop()
    at(14.0, 29.5, 0)
    raised_bed(S, 9.0, 3.6, 'veg', 6)
    tf_pop()
    at(12.0, 38.0, 15)
    pond(S)
    tf_pop()
    at(6.0, 51.0)
    tree_oak(S, 1.2, 23, 'autumn')
    tf_pop()
    at(13.0, 66.0)
    gazebo(S)
    tf_pop()
    at(17.0, 80.0)
    bush(S, 1.1, 5, 'pink')
    tf_pop()
    at(17.5, 56.0)
    bush(S, 1.2, 81, 'red')
    tf_pop()
    at(17.0, 47.0)
    bench(S, 6.0, 'wood2')
    tf_pop()
    at(4.0, 64.5)
    birdhouse(S)
    tf_pop()
    # ---------------- back yard (north)
    at(10.0, 9.0, 0)
    garden_shed(S)
    tf_pop()
    at(42.0, 8.0, 0)
    bbq(S)
    tf_pop()
    at(56.0, 8.5, 20)
    picnic_table(S, True)
    tf_pop()
    at(70.0, 9.0)
    trampoline(S)
    tf_pop()
    at(26.0, 11.0)
    doghouse(S)
    tf_pop()
    at(28.0, 5.0)
    trash_can(S, 'teal')
    tf_pop()
    at(31.2, 5.0)
    trash_can(S, 'blue')
    tf_pop()
    for x in (20.0, 47.0, 62.0, 76.0):
        at(x, 3.0)
        bush(S, 1.0, int(x) + 3, 'pink' if int(x) % 2 else 'yellow')
        tf_pop()
    for x in (21.5, 76.8):
        at(x, 13.5)
        bush(S, 0.9, int(x), 'red' if x < 50 else 'pink')
        tf_pop()
    at(36.5, 4.6)
    flower_patch(S, 6.0, 3.0, 71)
    tf_pop()
    at(48.5, 14.5)
    flower_patch(S, 5.0, 2.2, 51)
    tf_pop()
    at(93.5, 4.5)
    tree_pine(S, 0.9, 25)
    tf_pop()
    # ---------------- east side yard: play area, garden, trees (east of the back path x 80.6..86.6)
    at(92.5, 24.0, 90)
    swing_set(S)
    tf_pop()
    at(92.5, 37.0)
    sandbox(S)
    tf_pop()
    at(92.0, 49.0)
    trampoline(S)
    tf_pop()
    at(91.5, 62.0, 0)
    raised_bed(S, 9.0, 3.6, 'veg', 8)
    tf_pop()
    at(91.5, 68.0, 0)
    raised_bed(S, 9.0, 3.6, 'flower', 9)
    tf_pop()
    at(94.0, 77.0)
    tree_oak(S, 1.2, 31, 'cherry')
    tf_pop()
    at(95.5, 56.0)
    birdhouse(S)
    tf_pop()
    at(79.0, 40.0, 90)
    hedge(S, 44.0, 3.2, 1.6, True, 32)
    tf_pop()
    # ---------------- street furniture
    for x in (-30.0, 8.0, 56.0, 100.0, 140.0):
        at0(x, 107.2)
        lamp_post(S)
        tf_pop()
    for x in (-18.0, 22.0, 70.0, 116.0):
        at0(x, 104.6)
        tree_oak(S, 0.8, int(x) + 50, 'oak')
        tf_pop()
    at0(60.0, 104.0, 180)
    bench(S, 6.0)
    tf_pop()
    at0(47.0, 103.5)
    hydrant(S)
    tf_pop()
    at0(66.0, 104.6)
    trash_can(S, 'dark')
    tf_pop()
    at0(104.0, 104.6)
    trash_can(S, 'teal')
    tf_pop()
    at0(-6.0, 123.4)
    manhole(S)
    tf_pop()
    crosswalk(S, 118.0, 110.5, 10) if False else None
    # ---------------- neighbourhood: both sides, behind, across the street
    for (x, z, w, d, h, wall, roof, sd) in ((-34.0, 62.0, 26.0, 22.0, 15.0, '#FF9AA2', '#7C5CBF', 1), (-34.0, 22.0, 22.0, 18.0, 13.0, '#C7F0A8', '#E4473D', 2),
                                          (126.0, 62.0, 28.0, 24.0, 17.0, '#9AD7FF', '#E4473D', 3), (126.0, 22.0, 22.0, 18.0, 13.0, '#FFE9A8', '#3FA7FF', 4),
                                          (22.0, 158.0, 26.0, 22.0, 15.0, '#FFB26B', '#9B6BDB', 5), (74.0, 158.0, 26.0, 22.0, 15.0, '#B8E6FF', '#E4473D', 6),
                                          (122.0, 158.0, 24.0, 20.0, 14.0, '#FFD9E8', '#2E9E7A', 7), (-24.0, 158.0, 24.0, 20.0, 14.0, '#E6D0FF', '#E4473D', 8)):
        at0(x, z, 0 if z < 100 else 180)
        house_nb(S, w, d, h, wall, roof, sd)
        tf_pop()
        fz = (z + d / 2 + 2.0) if z < 100 else (z - d / 2 - 2.0)
        at0(x + (w / 2 + 8.5), z + 3.0)
        tree_oak(S, 1.1, sd * 10 + 5, 'oak' if sd % 2 else 'cherry')
        tf_pop()
        for k in (-1, 1):
            at0(x + k * w * 0.3, fz + 1.2 * (1 if z < 100 else -1))
            bush(S, 0.9, sd + k, 'pink' if k < 0 else 'yellow')
            tf_pop()
