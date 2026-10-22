# Furniture and decor generators (exec'd by build_flat.py). Local frame: origin (ox, oz), +z = front, +x = right-hand side; face = S/N/E/W is the world
# direction of the front. Rotations are multiples of 90 degrees so every box stays axis aligned.
class F:
    def __init__(s, ox, oz, face='S'):
        s.ox, s.oz, s.face = ox, oz, face

    def p(s, lx, lz):
        f = s.face
        if f == 'S':
            return s.ox + lx, s.oz + lz
        if f == 'N':
            return s.ox - lx, s.oz - lz
        if f == 'E':
            return s.ox + lz, s.oz - lx
        return s.ox - lz, s.oz + lx

    def swap(s):
        return s.face in 'EW'

    def b(s, x0, x1, y0, y1, z0, z1, col, kind='O'):
        a, c = s.p(x0, z0), s.p(x1, z1)
        X0, X1, Z0, Z1 = min(a[0], c[0]), max(a[0], c[0]), min(a[1], c[1]), max(a[1], c[1])
        dx, dy, dz = X1 - X0, y1 - y0, Z1 - Z0
        if ROUND and kind == 'O' and min(dx, dy, dz) >= 0.3 and max(dx, dz) < 14:
            rbox(X0, X1, y0, y1, Z0, Z1, col, r=min(0.2, 0.22 * min(dx, dz)), rt=min(0.18, 0.28 * dy))
        else:
            box(X0, X1, y0, y1, Z0, Z1, col, kind)

    def sb(s, x0, x1, y0, y1, z0, z1, col, bv=0.14, kind='O'):
        a, c = s.p(x0, z0), s.p(x1, z1)
        soft(min(a[0], c[0]), max(a[0], c[0]), y0, y1, min(a[1], c[1]), max(a[1], c[1]), col, bv, kind)

    def cy(s, x, z, y0, y1, r, col, seg=14, kind='O', r2=None):
        wx, wz = s.p(x, z)
        cyl(wx, wz, y0, y1, r, col, seg, kind, r2)

    def lt(s, x, z, y0, prof, col, seg=16, kind='O'):
        wx, wz = s.p(x, z)
        lathe(wx, wz, y0, prof, col, seg, kind)

    def sp(s, x, y, z, rx, ry, rz, col, seg=10, rings=6, kind='O'):
        wx, wz = s.p(x, z)
        if s.swap():
            rx, rz = rz, rx
        sphere(wx, y, wz, rx, ry, rz, col, seg, rings, kind)

    def hc(s, x, y, z, axis, length, r, col, seg=10, kind='O', r2=None):
        wx, wz = s.p(x, z)
        if s.swap():
            axis = 'z' if axis == 'x' else 'x'
        hcyl(wx, y, wz, axis, length, r, col, seg, kind, r2)

    def rg(s, x, y, z, R, r, plane, col, seg=16, tseg=6):
        wx, wz = s.p(x, z)
        if s.swap() and plane == 'yz':
            plane = 'xy'
        elif s.swap() and plane == 'xy':
            plane = 'yz'
        ring(wx, y, wz, R, r, plane, col, seg, tseg)

    def col(s, x0, x1, y0, y1, z0, z1, name):
        a, c = s.p(x0, z0), s.p(x1, z1)
        collider(min(a[0], c[0]), max(a[0], c[0]), y0, y1, min(a[1], c[1]), max(a[1], c[1]), name)


def rnd_of(seed):
    return random.Random(seed)


def handle(f, x, y, z, vertical=False, col=None):
    col = col or P['brass']
    if vertical:
        f.b(x - 0.05, x + 0.05, y, y + 0.8, z, z + 0.12, col)
        f.b(x - 0.12, x + 0.12, y - 0.05, y + 0.85, z + 0.12, z + 0.22, col)
    else:
        f.b(x, x + 0.8, y - 0.05, y + 0.05, z, z + 0.12, col)
        f.b(x - 0.05, x + 0.85, y - 0.12, y + 0.12, z + 0.12, z + 0.22, col)


def books(f, x0, x1, y, z, depth, seed, maxh=1.6):
    r = rnd_of(seed)
    cols = [P['rose2'], P['teal'], P['navy'], P['mustard'], P['cream'], P['green'], P['plum'], P['red'], P['denim'], P['oak3']]
    x = x0
    while x < x1 - 0.3:
        w = r.uniform(0.18, 0.42)
        if x + w > x1:
            break
        h = r.uniform(0.9, maxh)
        f.b(x, x + w, y, y + h, z, z + depth, cols[r.randrange(len(cols))])
        if r.random() < 0.3:
            f.b(x + 0.03, x + w - 0.03, y + h * 0.6, y + h * 0.66, z - 0.02, z + 0.02, P['gold'])
        x += w + 0.02
        if r.random() < 0.06:
            x += r.uniform(0.6, 1.2)


def vase(f, x, y, z, h=1.4, col=None, flowers=True, seed=1, big=False):
    col = col or P['glass']
    k = 1.5 if big else 1.0
    f.lt(x, z, y, [(0.0, 0), (0.32 * k, 0), (0.4 * k, 0.12 * h), (0.55 * k, 0.45 * h), (0.34 * k, 0.8 * h), (0.28 * k, h), (0.38 * k, h + 0.05)], col, seg=12)
    if flowers:
        r = rnd_of(seed)
        fc = [P['rose'], P['red'], P['cream'], P['mustard'], P['lilac']]
        for i in range(5 if not big else 8):
            a = r.uniform(0, 6.28)
            dx, dz = math.cos(a) * 0.25 * k, math.sin(a) * 0.25 * k
            top = y + h + r.uniform(0.7, 1.4) * k
            f.hc(x + dx * 0.5, y + h + (top - y - h) / 2, z + dz * 0.5, 'x', 0.05, 0.03, P['green']) if False else None
            f.b(x + dx * 0.5 - 0.02, x + dx * 0.5 + 0.02, y + h * 0.7, top, z + dz * 0.5 - 0.02, z + dz * 0.5 + 0.02, P['green'])
            f.sp(x + dx * 0.6, top, z + dz * 0.6, 0.3 * k, 0.26 * k, 0.3 * k, fc[i % len(fc)], seg=8, rings=5)
        for i in range(3):
            a = i * 2.1
            f.sp(x + math.cos(a) * 0.3 * k, y + h + 0.4 * k, z + math.sin(a) * 0.3 * k, 0.28 * k, 0.12 * k, 0.28 * k, P['green2'], seg=7, rings=4)


def plant_pot(f, x, z, h=1.6, r=0.8, leaf=None, big=False, seed=3, pot=None):
    pot = pot or P['pot']
    f.lt(x, z, FY, [(0.0, 0), (r * 0.7, 0), (r, h * 0.15), (r * 1.05, h * 0.9), (r * 1.12, h), (r * 0.9, h), (r * 0.9, h - 0.15), (0.0, h - 0.15)], pot, seg=14)
    f.cy(x, z, FY + h - 0.18, FY + h - 0.1, r * 0.88, P['walnut'], seg=14)
    rn = rnd_of(seed)
    leaf = leaf or P['green2']
    if big:
        f.hc(x, FY + h + 2.2, z, 'x', 0.01, 0.01, leaf) if False else None
        f.cy(x, z, FY + h - 0.1, FY + h + 3.8, 0.13, P['walnut'], seg=8, r2=0.08)
        for i in range(26):
            a = rn.uniform(0, 6.28)
            d = rn.uniform(0.2, 1.5)
            y = FY + h + rn.uniform(2.2, 5.6)
            f.sp(x + math.cos(a) * d, y, z + math.sin(a) * d, 0.9, 0.5, 0.7, leaf if i % 3 else P['green'], seg=10, rings=6)
    else:
        for i in range(11):
            a = i * 0.57 + rn.uniform(-0.2, 0.2)
            d = rn.uniform(0.1, r * 0.8)
            hh = rn.uniform(1.0, 2.6)
            f.sp(x + math.cos(a) * d, FY + h + hh * 0.5, z + math.sin(a) * d, 0.28, hh * 0.5, 0.28, leaf if i % 2 else P['green'], seg=7, rings=5)


def art(n, px, pz, y, w, h, seed, frame=None, abstract=True):
    """Framed picture with a mat and an abstract painting."""
    frame = frame or P['gold']
    t = 0.28
    wb(n, px, y, pz, w, h, 0.18, frame)
    wb(n, px, y + t, pz, w - 2 * t, h - 2 * t, 0.26, P['cream'])
    m = t + 0.45
    r = rnd_of(seed)
    base = r.choice([P['sky'], P['blush'], P['sage'], P['lilac'], P['mustard'], P['cream']])
    wb(n, px, y + m, pz, w - 2 * m, h - 2 * m, 0.30, base)
    cols = [P['rose2'], P['teal'], P['navy'], P['mustard'], P['white'], P['terracotta'], P['green']]
    for i in range(5):
        ww = r.uniform(0.5, (w - 2 * m) * 0.5)
        hh = r.uniform(0.5, (h - 2 * m) * 0.5)
        ox = r.uniform(-(w - 2 * m) / 2 + ww / 2, (w - 2 * m) / 2 - ww / 2)
        oy = r.uniform(0, h - 2 * m - hh)
        px2, pz2 = (px + ox, pz) if n in 'NS' else (px, pz + ox)
        wb(n, px2, y + m + oy, pz2, ww, hh, 0.34 + i * 0.012, cols[r.randrange(len(cols))])


def mirror(n, px, pz, y, w, h, frame=None, seed=0):
    frame = frame or P['brass']
    wb(n, px, y, pz, w, h, 0.22, frame)
    wb(n, px, y + 0.3, pz, w - 0.6, h - 0.6, 0.30, P['sky'], kind='G')
    for k in range(3):
        wb(n, px, y + h - 0.05 - k * 0.0, pz, w - 0.2, 0.1, 0.30, shade(frame, 0.2)) if False else None


def clock(n, px, pz, y, r=1.2):
    cx, cz = (px, pz)
    d = 0.3
    if n == 'S':
        cyl(cx, cz + d / 2 + 0.05, y, y + 0.001, 0.001, P['white']) if False else None
    # round clock: disc as a thin horizontal-axis cylinder
    ax = 'z' if n in 'NS' else 'x'
    off = (0.2 if n in 'SE' else -0.2)
    if ax == 'z':
        hcyl(px, y, pz + off, 'z', 0.25, r, P['brass'], seg=24)
        hcyl(px, y, pz + off + (0.15 if n == 'S' else -0.15), 'z', 0.1, r - 0.18, P['cream'], seg=24)
        wb(n, px, y - 0.05, pz, 0.12, r * 0.8, 0.5, P['black'], off=0.1)
        wb(n, px, y - 0.05, pz, r * 0.6, 0.12, 0.52, P['black'], off=0.1)
    else:
        hcyl(px + off, y, pz, 'x', 0.25, r, P['brass'], seg=24)
        hcyl(px + off + (0.15 if n == 'E' else -0.15), y, pz, 'x', 0.1, r - 0.18, P['cream'], seg=24)
        wb(n, px, y - 0.05, pz, 0.12, r * 0.8, 0.5, P['black'], off=0.1)


def rug(cx, cz, w, d, col, border, pattern=0, y=FY, seed=0):
    box(cx - w / 2, cx + w / 2, y, y + 0.1, cz - d / 2, cz + d / 2, border)
    box(cx - w / 2 + 0.6, cx + w / 2 - 0.6, y + 0.1, y + 0.14, cz - d / 2 + 0.6, cz + d / 2 - 0.6, col)
    r = rnd_of(seed)
    if pattern == 1:       # diamonds
        for i in range(int(w // 2.4)):
            for j in range(int(d // 2.4)):
                x, z = cx - w / 2 + 1.6 + i * 2.4, cz - d / 2 + 1.6 + j * 2.4
                if abs(x - cx) < w / 2 - 1.0 and abs(z - cz) < d / 2 - 1.0:
                    prism([(x - 0.7, z), (x, z - 0.7), (x + 0.7, z), (x, z + 0.7)], y + 0.14, y + 0.17, border)
    elif pattern == 2:     # stripes
        for i in range(int((w - 1.4) // 1.2)):
            box(cx - w / 2 + 0.9 + i * 1.2, cx - w / 2 + 1.3 + i * 1.2, y + 0.14, y + 0.17, cz - d / 2 + 0.9, cz + d / 2 - 0.9, border)
    elif pattern == 3:     # circles
        for i in range(8):
            cyl(cx + r.uniform(-w / 2 + 1.4, w / 2 - 1.4), cz + r.uniform(-d / 2 + 1.4, d / 2 - 1.4), y + 0.14, y + 0.17, r.uniform(0.4, 0.9), border, seg=14)
    for k in range(int(w // 0.5)):      # fringe
        for z in (cz - d / 2 - 0.25, cz + d / 2 + 0.25) if pattern == 2 else ():
            box(cx - w / 2 + k * 0.5, cx - w / 2 + k * 0.5 + 0.1, y, y + 0.06, z - 0.2, z + 0.2, P['cream'])


def table_lamp(x, y, z, shade_col=None, h=2.2, base=None, glow=True):
    shade_col = shade_col or P['cream']
    base = base or P['teal2']
    lathe(x, z, y, [(0.0, 0), (0.5, 0), (0.55, 0.1), (0.35, 0.5), (0.5, 1.1), (0.22, 1.5), (0.12, 1.7), (0.12, h - 0.3)], base, seg=14)
    lathe(x, z, y + h - 0.7, [(0.9, 0), (0.62, 1.1), (0.55, 1.1), (0.82, 0.05)], shade_col, seg=16)
    D.sphere(x, y + h - 0.2, z, 0.28, 0.28, 0.28, '#FFF1C8', seg=8, rings=5, kind='N')
    if glow:
        spot(x, y + h, z, 14, 0.7)


def floor_lamp(x, z, h=7.0, shade_col=None, base=None, glow=True):
    shade_col = shade_col or P['cream']
    base = base or P['brass']
    lathe(x, z, FY, [(0.0, 0), (0.9, 0), (0.9, 0.12), (0.5, 0.25), (0.14, 0.5), (0.1, h - 1.0)], base, seg=14)
    lathe(x, z, FY + h - 1.8, [(1.3, 0), (0.95, 1.6), (0.88, 1.6), (1.22, 0.05)], shade_col, seg=18)
    D.sphere(x, FY + h - 1.1, z, 0.35, 0.35, 0.35, '#FFF1C8', seg=8, rings=5, kind='N')
    collider(x - 0.9, x + 0.9, FY, FY + h, z - 0.9, z + 0.9, 'lamp')
    if glow:
        spot(x, FY + h - 1.0, z, 20, 0.9)


def pendant(x, z, y_top, y_bot, col=None, r=1.2, glow=True):
    col = col or P['brass']
    cyl(x, z, y_bot + 0.9, y_top, 0.05, P['black'], seg=6)
    lathe(x, z, y_bot, [(0.0, 0), (0.3, 0.05), (r, 0.9), (r + 0.08, 0.95), (r * 0.5, 1.2), (0.12, 1.35)], col, seg=18)
    D.sphere(x, y_bot + 0.2, z, 0.35, 0.35, 0.35, '#FFF1C8', seg=8, rings=5, kind='N')
    if glow:
        spot(x, y_bot, z, 20, 0.8)


def chandelier(x, z, y_top, y_bot, arms=8, R=2.6):
    cyl(x, z, y_bot + 1.5, y_top, 0.07, P['gold'], seg=8)
    lathe(x, z, y_bot, [(0.0, 0), (0.35, 0.1), (0.55, 0.5), (0.3, 0.9), (0.4, 1.2), (0.2, 1.6)], P['gold'], seg=14)
    ring(x, y_bot + 0.7, z, R, 0.1, 'xz', P['gold'], seg=32, tseg=6)
    ring(x, y_bot + 1.3, z, R * 0.55, 0.08, 'xz', P['gold'], seg=24, tseg=6)
    for i in range(arms):
        a = 2 * math.pi * i / arms
        px, pz = x + math.cos(a) * R, z + math.sin(a) * R
        cyl(px, pz, y_bot + 0.7, y_bot + 1.35, 0.1, P['cream'], seg=8)
        D.sphere(px, y_bot + 1.55, pz, 0.17, 0.3, 0.17, '#FFF1C8', seg=7, rings=5, kind='N')
        for k in range(4):
            cyl(x + math.cos(a) * (R * 0.3 + k * 0.3), z + math.sin(a) * (R * 0.3 + k * 0.3), y_bot + 0.55 - k * 0.0, y_bot + 0.62, 0.05, P['gold'], seg=6) if False else None
        D.sphere(px, y_bot + 0.35, pz, 0.1, 0.22, 0.1, P['glass'], seg=6, rings=4, kind='G')
    for k in range(10):
        a = 2 * math.pi * k / 10
        D.sphere(x + math.cos(a) * R * 0.55, y_bot + 0.95, z + math.sin(a) * R * 0.55, 0.1, 0.22, 0.1, P['glass'], seg=6, rings=4, kind='G')
    spot(x, y_bot, z, 34, 1.3)


def dining_chair(ox, oz, face, fab, wood):
    f = F(ox, oz, face)
    for lx in (-0.95, 0.95):
        for lz in (-0.95, 0.95):
            f.lt(lx, lz, FY, [(0.0, 0), (0.14, 0), (0.12, 0.6), (0.1, 1.2), (0.16, 1.6), (0.16, 1.9)], wood, seg=8)
    f.b(-1.1, 1.1, FY + 1.5, FY + 1.7, -1.1, 1.1, wood)                      # seat frame
    f.sb(-1.0, 1.0, FY + 1.7, FY + 2.15, -1.0, 1.0, fab, 0.16)                # cushion
    for lx in (-0.95, 0.95):
        f.b(lx - 0.1, lx + 0.1, FY + 1.7, FY + 4.3, -1.15, -0.95, wood)       # back posts
    f.b(-1.1, 1.1, FY + 3.9, FY + 4.25, -1.18, -0.92, wood)
    f.sb(-0.8, 0.8, FY + 2.5, FY + 3.8, -1.05, -0.88, fab, 0.1)
    f.b(-0.8, 0.8, FY + 2.2, FY + 2.4, -1.12, -0.9, wood)
    for lx in (-0.55, 0.0, 0.55):
        f.sp(lx, FY + 4.35, -1.05, 0.1, 0.1, 0.1, P['gold'], seg=6, rings=4) if False else None
    f.col(-1.15, 1.15, FY, FY + 4.3, -1.2, 1.1, 'chair')


def round_table(x, z, r=4.2, th=3.2):
    top_y = FY + th
    lathe(x, z, top_y - 0.45, [(0.0, 0), (r - 0.4, 0), (r, 0.2), (r, 0.45), (r - 0.12, 0.5), (0.0, 0.5)], P['walnut'], seg=40)        # top with a rounded edge
    lathe(x, z, top_y - 0.45, [(r - 0.55, 0), (r - 0.55, -0.35), (r - 0.9, -0.35), (r - 0.9, 0)], P['oak2'], seg=36)                 # apron
    lathe(x, z, FY, [(0.0, 0), (1.9, 0), (2.0, 0.12), (1.5, 0.35), (0.9, 0.5), (0.62, 0.9), (0.5, 1.4), (0.56, 2.0), (0.9, 2.45), (1.5, 2.7), (0.0, 2.75)], P['walnut'], seg=24)
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        cbox(x + math.cos(a) * 1.7, FY + 0.28, z - math.sin(a) * 1.7, 1.6, 0.45, 0.5, P['oak2'], rot=math.degrees(a))
    # brass inlay ring on the top
    lathe(x, z, top_y + 0.05, [(r - 0.7, 0), (r - 0.7, 0.03), (r - 0.9, 0.03), (r - 0.9, 0)], P['brass'], seg=40)
    CYLC.append((x, FY + th / 2, z, 2 * r, th, 'table_round'))


def tea_set(x, z, th=3.2):
    y = FY + th + 0.05
    # lace runner
    lathe(x, z, y, [(0.0, 0), (2.3, 0), (2.3, 0.04), (0.0, 0.04)], P['cream'], seg=30)
    # cake stand with a cake
    lathe(x + 0.2, z - 0.5, y, [(0.0, 0), (0.9, 0), (0.9, 0.08), (0.12, 0.3), (0.12, 0.95), (1.2, 1.05), (1.2, 1.15), (0.0, 1.15)], P['white'], seg=22)
    lathe(x + 0.2, z - 0.5, y + 1.15, [(0.0, 0), (0.95, 0), (0.95, 0.65), (0.0, 0.65)], P['blush'], seg=22)
    lathe(x + 0.2, z - 0.5, y + 1.8, [(0.95, 0), (0.95, 0.12), (0.0, 0.12)], P['rose2'], seg=22)
    for k in range(7):
        a = k * 0.9
        D.sphere(x + 0.2 + math.cos(a) * 0.6, y + 2.0, z - 0.5 + math.sin(a) * 0.6, 0.15, 0.13, 0.15, P['red'] if k % 2 else P['cream'], seg=6, rings=4)
    # teapot
    tx, tz = x - 1.1, z + 0.6
    lathe(tx, tz, y, [(0.0, 0), (0.5, 0), (0.7, 0.2), (0.78, 0.55), (0.6, 0.95), (0.3, 1.1), (0.0, 1.1)], P['white'], seg=18)
    lathe(tx, tz, y + 1.05, [(0.3, 0), (0.26, 0.15), (0.1, 0.22), (0.12, 0.3), (0.0, 0.32)], P['white'], seg=14)
    cbox(tx + 0.95, y + 0.75, tz, 0.9, 0.12, 0.2, P['white'], rot=-25)
    ring(tx - 0.8, y + 0.62, tz, 0.35, 0.07, 'yz', P['white'], seg=14, tseg=5)
    lathe(tx, tz, y + 0.5, [(0.79, 0), (0.79, 0.1), (0.76, 0.1), (0.76, 0)], P['gold'], seg=18)
    # cups with saucers
    for (cx, cz) in ((x + 1.6, z + 0.9), (x - 1.8, z - 0.9), (x + 1.2, z - 1.7)):
        lathe(cx, cz, y, [(0.0, 0), (0.58, 0), (0.58, 0.05), (0.0, 0.05)], P['white'], seg=16)
        lathe(cx, cz, y + 0.05, [(0.0, 0), (0.22, 0), (0.36, 0.3), (0.38, 0.5), (0.3, 0.5), (0.0, 0.1)], P['white'], seg=14)
        lathe(cx, cz, y + 0.45, [(0.3, 0), (0.0, 0)], P['brown'] if 'brown' in P else '#7A4B2A', seg=12)
        ring(cx + 0.4, y + 0.3, cz, 0.12, 0.04, 'yz', P['white'], seg=10, tseg=4)
    # sugar bowl, plate with macarons, vase
    lathe(x + 2.5, z - 0.2, y, [(0.0, 0), (0.3, 0), (0.42, 0.25), (0.36, 0.5), (0.3, 0.55), (0.0, 0.55)], P['gold'], seg=12)
    for k in range(5):
        D.sphere(x - 0.4 + k * 0.26, y + 0.12, z + 1.8, 0.17, 0.1, 0.17, [P['rose'], P['mustard'], P['sage'], P['lilac'], P['cream']][k], seg=7, rings=4)
    vase(F(x - 2.3, z + 0.4, 'S'), 0, y, 0, h=1.6, col=P['sky'], seed=9)


def sofa(ox, oz, face, length, fab, fab2, legs=P['walnut'], depth=3.8):
    f = F(ox, oz, face)
    L2 = length / 2
    f.b(-L2, L2, FY + 0.5, FY + 1.5, -depth / 2, depth / 2, shade(fab, -0.2))                   # base frame
    for lx in (-L2 + 0.5, L2 - 0.5):
        for lz in (-depth / 2 + 0.5, depth / 2 - 0.5):
            f.lt(lx, lz, FY, [(0.0, 0), (0.22, 0), (0.18, 0.2), (0.12, 0.5)], legs, seg=8)
    n = max(2, int((length - 3) // 2.4))
    cw = (length - 2.4) / n
    for i in range(n):                                                                          # seat cushions
        x0 = -L2 + 1.2 + i * cw
        f.sb(x0 + 0.04, x0 + cw - 0.04, FY + 1.5, FY + 2.35, -depth / 2 + 0.9, depth / 2, fab, 0.18)
        f.b(x0 + 0.04, x0 + cw - 0.04, FY + 2.0, FY + 2.05, depth / 2 - 0.01, depth / 2 + 0.01, P['gold'])
        f.sb(x0 + 0.15, x0 + cw - 0.15, FY + 2.35, FY + 4.1, -depth / 2 + 0.55, -depth / 2 + 1.35, fab2, 0.2)   # back cushions
        for k in range(3):
            f.sp(x0 + cw / 2, FY + 2.4 + k * 0.6, -depth / 2 + 1.38, 0.11, 0.11, 0.05, P['gold'], seg=6, rings=4) if k == 1 else None
    f.sb(-L2, -L2 + 1.2, FY + 1.1, FY + 3.2, -depth / 2, depth / 2, fab, 0.22)                 # arms
    f.sb(L2 - 1.2, L2, FY + 1.1, FY + 3.2, -depth / 2, depth / 2, fab, 0.22)
    f.hc(-L2 + 0.6, FY + 3.3, 0, 'z', depth, 0.5, fab, seg=12)
    f.hc(L2 - 0.6, FY + 3.3, 0, 'z', depth, 0.5, fab, seg=12)
    f.sb(-L2 + 0.2, L2 - 0.2, FY + 1.1, FY + 4.4, -depth / 2, -depth / 2 + 0.7, fab, 0.2)       # backrest
    f.b(-L2 + 0.1, L2 - 0.1, FY + 4.3, FY + 4.5, -depth / 2 + 0.05, -depth / 2 + 0.6, P['gold'])
    # throw pillows and a blanket
    rn = rnd_of(int(ox * 7 + oz))
    pc = [P['teal2'], P['mustard'], P['cream'], P['rose2'], P['denim']]
    for i, lx in enumerate((-L2 + 1.9, L2 - 1.9, -L2 + 3.4)):
        f.sb(lx - 0.8, lx + 0.8, FY + 2.35, FY + 4.0, -depth / 2 + 1.35, -depth / 2 + 1.95, pc[(i + int(ox)) % 5], 0.22)
        f.sp(lx, FY + 3.2, -depth / 2 + 1.98, 0.14, 0.14, 0.05, P['gold'], seg=6, rings=4)
    f.sb(L2 - 3.8, L2 - 1.3, FY + 2.35, FY + 2.55, -depth / 2 + 1.0, depth / 2 - 0.2, P['blush'], 0.05)
    f.col(-L2, L2, FY, FY + 4.5, -depth / 2, depth / 2, 'sofa')


def armchair(ox, oz, face, fab, legs=P['walnut']):
    f = F(ox, oz, face)
    f.b(-1.7, 1.7, FY + 0.6, FY + 1.5, -1.7, 1.7, shade(fab, -0.2))
    for lx in (-1.4, 1.4):
        for lz in (-1.4, 1.4):
            f.lt(lx, lz, FY, [(0.0, 0), (0.2, 0), (0.15, 0.2), (0.1, 0.7)], legs, seg=8)
    f.sb(-1.2, 1.2, FY + 1.5, FY + 2.3, -0.8, 1.7, fab, 0.2)
    f.sb(-1.7, 1.7, FY + 1.2, FY + 5.0, -1.7, -0.9, fab, 0.25)
    f.sb(-1.7, -1.1, FY + 1.2, FY + 3.2, -1.1, 1.7, fab, 0.2)
    f.sb(1.1, 1.7, FY + 1.2, FY + 3.2, -1.1, 1.7, fab, 0.2)
    f.sb(-0.9, 0.9, FY + 2.8, FY + 4.4, -0.95, -0.6, shade(fab, 0.15), 0.18)
    f.col(-1.7, 1.7, FY, FY + 5.0, -1.7, 1.7, 'armchair')


def ottoman(x, z, fab, r=1.3):
    lathe(x, z, FY + 0.3, [(0.0, 0), (r, 0), (r, 1.0), (r - 0.1, 1.1), (0.0, 1.12)], fab, seg=20)
    for k in range(3):
        a = k * 2.09
        cyl(x + math.cos(a) * (r - 0.35), z + math.sin(a) * (r - 0.35), FY, FY + 0.3, 0.12, P['gold'], seg=8)
    CYLC.append((x, FY + 0.7, z, 2 * r, 1.4, 'ottoman'))


def coffee_table(ox, oz, face, w=6.0, d=3.2):
    f = F(ox, oz, face)
    f.b(-w / 2, w / 2, FY + 1.35, FY + 1.5, -d / 2, d / 2, P['glass'], 'G')
    f.b(-w / 2 - 0.1, w / 2 + 0.1, FY + 1.25, FY + 1.4, -d / 2 - 0.1, d / 2 + 0.1, P['brass'])
    f.b(-w / 2 + 0.3, w / 2 - 0.3, FY + 0.5, FY + 0.6, -d / 2 + 0.3, d / 2 - 0.3, P['oak2'])
    for lx in (-w / 2 + 0.25, w / 2 - 0.25):
        for lz in (-d / 2 + 0.25, d / 2 - 0.25):
            f.b(lx - 0.1, lx + 0.1, FY, FY + 1.3, lz - 0.1, lz + 0.1, P['brass'])
    # books, candle, tray, small plant
    f.b(-2.0, -0.6, FY + 0.6, FY + 0.75, -0.6, 0.5, P['rose2'])
    f.b(-1.9, -0.7, FY + 0.75, FY + 0.88, -0.5, 0.4, P['cream'])
    f.b(0.6, 2.0, FY + 1.5, FY + 1.62, -0.7, 0.7, P['brass'])
    vase(f, 1.3, FY + 1.62, 0.0, h=0.9, col=P['rose'], seed=21)
    f.lt(-1.2, 0.1, FY + 1.5, [(0.0, 0), (0.36, 0), (0.36, 0.5), (0.3, 0.5), (0.0, 0.1)], P['cream'], seg=10)
    f.sp(-1.2, FY + 2.15, 0.1, 0.07, 0.12, 0.07, '#FFD58A', seg=6, rings=4, kind='N')
    f.sb(-0.4, 0.5, FY + 1.5, FY + 1.7, 0.4, 1.2, P['teal2'], 0.04) if False else None
    f.col(-w / 2, w / 2, FY, FY + 1.6, -d / 2, d / 2, 'coffeetable')


def side_table(x, z, h=2.2, r=0.9, top=None):
    top = top or P['marble']
    lathe(x, z, FY + h - 0.15, [(0.0, 0), (r, 0), (r, 0.15), (0.0, 0.15)], top, seg=18)
    cyl(x, z, FY, FY + h - 0.15, 0.09, P['brass'], seg=8)
    lathe(x, z, FY, [(0.5, 0), (0.5, 0.1), (0.1, 0.25)], P['brass'], seg=12)
    CYLC.append((x, FY + h / 2, z, 2 * r, h, 'sidetable'))


def console_table(ox, oz, face, w, d=1.4, h=2.8, wood=None, top=None):
    f = F(ox, oz, face)
    wood = wood or P['walnut']
    top = top or P['marble']
    f.b(-w / 2, w / 2, FY + h - 0.15, FY + h, -d / 2, d / 2, top)
    f.b(-w / 2 + 0.1, w / 2 - 0.1, FY + h - 0.5, FY + h - 0.15, -d / 2 + 0.1, d / 2 - 0.1, wood)
    for lx in (-w / 2 + 0.2, w / 2 - 0.2):
        for lz in (-d / 2 + 0.2, d / 2 - 0.2):
            f.lt(lx, lz, FY, [(0.0, 0), (0.16, 0), (0.12, 0.3), (0.1, h - 0.5)], wood, seg=8)
    f.b(-w / 2 + 0.3, w / 2 - 0.3, FY + 0.7, FY + 0.8, -d / 2 + 0.25, d / 2 - 0.25, wood)
    f.col(-w / 2, w / 2, FY, FY + h, -d / 2, d / 2, 'console')
    return f


def credenza(ox, oz, face, w, d=1.8, h=2.6, wood=None, doors=3):
    f = F(ox, oz, face)
    wood = wood or P['walnut']
    f.b(-w / 2, w / 2, FY + 0.5, FY + h, -d / 2, d / 2, wood)
    f.b(-w / 2 - 0.1, w / 2 + 0.1, FY + h, FY + h + 0.15, -d / 2 - 0.1, d / 2 + 0.1, P['marble'])
    for lx in (-w / 2 + 0.4, w / 2 - 0.4):
        for lz in (-d / 2 + 0.3, d / 2 - 0.3):
            f.lt(lx, lz, FY, [(0.0, 0), (0.15, 0), (0.1, 0.5)], P['brass'], seg=8)
    dw = w / doors
    for i in range(doors):
        x0 = -w / 2 + i * dw
        f.b(x0 + 0.1, x0 + dw - 0.1, FY + 0.7, FY + h - 0.15, d / 2, d / 2 + 0.06, shade(wood, 0.1))
        f.b(x0 + 0.3, x0 + dw - 0.3, FY + 0.9, FY + h - 0.35, d / 2 + 0.06, d / 2 + 0.1, shade(wood, 0.2))
        handle(f, x0 + dw / 2 - 0.4, FY + h / 2 + 0.2, d / 2 + 0.1)
    f.col(-w / 2, w / 2, FY, FY + h + 0.15, -d / 2, d / 2, 'credenza')
    return f


def bookshelf(ox, oz, face, w, h, seed, d=1.3):
    f = F(ox, oz, face)
    f.b(-w / 2, w / 2, FY, FY + h, -d / 2, -d / 2 + 0.12, P['walnut'])          # back
    for lx in (-w / 2, w / 2 - 0.2):
        f.b(lx, lx + 0.2, FY, FY + h, -d / 2, d / 2, P['walnut'])
    n = int(h // 1.9)
    step = (h - 0.3) / n
    rn = rnd_of(seed)
    for i in range(n + 1):
        y = FY + i * step
        f.b(-w / 2, w / 2, y, y + 0.2, -d / 2, d / 2, P['oak2'])
        if i < n:
            kind = rn.random()
            if kind < 0.62:
                books(f, -w / 2 + 0.3, w / 2 - 0.3, y + 0.2, -d / 2 + 0.2, d - 0.5, seed * 13 + i, maxh=step - 0.45)
            elif kind < 0.82:
                vase(f, -w / 4, y + 0.2, 0.0, h=1.0, col=P['sky'], seed=seed + i)
                f.sb(w / 6, w / 6 + 1.2, y + 0.2, y + 0.9, -0.5, 0.5, P['rose2'], 0.05)
                f.sp(w / 6 + 0.6, y + 1.2, 0, 0.35, 0.35, 0.35, P['green2'], seg=8, rings=5)
            else:
                books(f, -w / 2 + 0.3, 0.0, y + 0.2, -d / 2 + 0.2, d - 0.5, seed * 7 + i, maxh=step - 0.5)
                f.lt(w / 4, 0, y + 0.2, [(0.0, 0), (0.6, 0), (0.7, 0.1), (0.15, 0.2), (0.15, 0.7), (0.5, 0.75), (0.5, 0.95)], P['brass'], seg=14)
    f.b(-w / 2 - 0.1, w / 2 + 0.1, FY + h, FY + h + 0.2, -d / 2 - 0.1, d / 2 + 0.1, P['walnut'])
    f.col(-w / 2, w / 2, FY, FY + h + 0.2, -d / 2, d / 2, 'bookshelf')
    return f


def curtains(n, px, pz, x0, x1, y_top, y_bot, col, sheer=True):
    """Curtain pair on the north wall (n = 'S'): folds as alternating strips, rod with finials."""
    if ROUND:
        for side in (0, 1):
            for k in range(9):
                c = (x0 + 0.3 + k * 0.4) if side == 0 else (x1 - 0.3 - k * 0.4)
                d = 0.35 + (0.2 if k % 2 else 0.0)
                cyl(c, pz + 0.7 + d * 0.5, y_bot, y_top, 0.26 + (0.05 if k % 2 else 0), col if k % 2 else shade(col, -0.1), seg=8)
    else:
        for side in (0, 1):
            for k in range(7):
                w = 0.45
                a = (x0 + k * 0.42) if side == 0 else (x1 - k * 0.42 - w)
                c = a + w / 2
                d = 0.35 + (0.12 if k % 2 else 0.0)
                wb(n, c, y_bot, pz, w, y_top - y_bot, d, col if k % 2 else shade(col, -0.1), off=0.55)
    hcyl((x0 + x1) / 2, y_top + 0.3, pz + 0.85, 'x', x1 - x0 + 3.4, 0.12, P['brass'], seg=8)
    for sx in (x0 - 1.7, x1 + 1.7):
        D.sphere(sx, y_top + 0.3, pz + 0.85, 0.28, 0.28, 0.28, P['gold'], seg=8, rings=5)


def window_frame_n(x0, x1, ya, yb, zf, col, mullions):
    """Window on the north wall (z = zf face), frame facing +z."""
    t = 0.5
    box(x0 - t, x1 + t, ya - t, ya, zf, zf + 0.7, col)
    box(x0 - t, x1 + t, yb, yb + t, zf, zf + 0.7, col)
    box(x0 - t, x0, ya, yb, zf, zf + 0.7, col)
    box(x1, x1 + t, ya, yb, zf, zf + 0.7, col)
    box(x0, x1, ya, yb, zf + 0.2, zf + 0.3, P['glass'], 'G')
    for m in mullions:
        box(m - 0.18, m + 0.18, ya, yb, zf + 0.1, zf + 0.5, col)
    box(x0, x1, yb - 3.0, yb - 2.8, zf + 0.1, zf + 0.5, col)
    box(x0 - 0.9, x1 + 0.9, ya - 0.4, ya - 0.1, zf, zf + 1.6, col)       # sill
