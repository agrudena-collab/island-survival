# The view from the panoramic window (exec'd by rooms2.py): the REAL OfficeDadDistrict as seen from the top floor of the red tower.
# The flat sits on the tenth floor behind the tower's west facade, so its "north" (-z) looks WEST over the district: the park with the fountain, the avenues,
# the business blocks and, far away, the border hedge, the forest road and hills.  Layout comes from the district generator (out/skyline.json).
# Mapping district (x_d, y_d, z_d) -> flat (x_f, y_f, z_f):  x_f = -37 - z_d,  z_f = x_d - 117.5,  y_f = y_d - 102   (window plane x_d = 100, floor 10 top y_d = 103).
SKY_JSON = os.path.join(HERE, '..', '..', '..', 'district', 'OfficeDadDistrict', 'out', 'skyline.json')
VY = 102.0


def vb(x0, x1, y0, y1, z0, z1, col, kind='O'):
    """box given in district coordinates, placed in flat coordinates"""
    box(-37.0 - z1, -37.0 - z0, y0 - VY, y1 - VY, x0 - 117.5, x1 - 117.5, col, kind)


def vcyl(x, z, y0, y1, r, col, seg=16, r2=None):
    cyl(-37.0 - z, x - 117.5, y0 - VY, y1 - VY, r, col, seg=seg, r2=r2)


def vsphere(x, y, z, rx, ry, rz, col, seg=7, rings=5):
    D.sphere(-37.0 - z, y - VY, x - 117.5, rz, ry, rx, col, seg=seg, rings=rings)


def vcut(a, b, cuts):
    res = [(a, b)]
    for (c0, c1) in cuts:
        nr = []
        for (s_, e_) in res:
            if c1 <= s_ or c0 >= e_:
                nr.append((s_, e_))
                continue
            if c0 > s_:
                nr.append((s_, c0))
            if c1 < e_:
                nr.append((c1, e_))
        res = nr
    return [(s_, e_) for (s_, e_) in res if e_ - s_ > 0.05]


def view_district():
    if not os.path.exists(SKY_JSON):
        print('skyline.json missing: build the district first; the view stays empty')
        return
    S = json.load(open(SKY_JSON))
    H = S['half']
    GRASS, GRASS2, ASPHALT, WALK, WHITE, ROOF, GLASS = '#5BC247', '#4EB23C', '#464B58', '#DAD7CE', '#FFFFFF', '#2D58B0', '#BFE4F4'
    XMAX = 98.0                                           # everything east of the tower's west face is behind the window
    # ground and the forest beyond the border
    vb(-1500, XMAX, -3, 1.0, -1500, 1500, GRASS)
    vb(-1500, -H - 10, -3, 1.05, -1500, 1500, '#3E9E4A')
    # streets
    streets = S['streets']
    ew = [s_ for s_ in streets if s_['ew']]
    ns = [s_ for s_ in streets if not s_['ew']]
    bands = [(e['c'] - e['ah'], e['c'] + e['ah']) for e in ew]
    for e in ew:
        vb(-1500 if e['name'] == 'Avenue A' else -e['ext'], min(XMAX, e['ext']), 1.0, 1.09, e['c'] - e['ah'], e['c'] + e['ah'], ASPHALT)
        vb(-e['ext'], min(XMAX, e['ext']), 1.09, 1.12, e['c'] - 0.3, e['c'] - 0.1, '#F8D030') if e['ah'] > 10 else None
        vb(-e['ext'], min(XMAX, e['ext']), 1.09, 1.12, e['c'] + 0.1, e['c'] + 0.3, '#F8D030') if e['ah'] > 10 else None
    for n in ns:
        far = 1500 if n['name'] == 'Avenue B' else n['ext']
        for (a, b) in vcut(-far, far, bands):
            vb(n['c'] - n['ah'], n['c'] + n['ah'], 1.0, 1.09, a, b, ASPHALT)
        if n['ah'] > 10:
            for (a, b) in vcut(-far, far, [(c0 - 6.5, c1 + 6.5) for (c0, c1) in bands]):
                vb(n['c'] - 0.3, n['c'] - 0.1, 1.09, 1.12, a, b, '#F8D030')
                vb(n['c'] + 0.1, n['c'] + 0.3, 1.09, 1.12, a, b, '#F8D030')
    # sidewalks (cut where streets cross)
    for s_ in streets:
        for sg in (-1, 1):
            lo, hi = sorted((s_['c'] + sg * s_['ah'], s_['c'] + sg * s_['sh']))
            others = [(o['c'] - o['sh'], o['c'] + o['sh']) for o in (ns if s_['ew'] else ew)]
            end = s_['ext'] - 6 if s_['name'] in ('Avenue A', 'Avenue B') else s_['ext']
            for (a, b) in vcut(-end, end, others):
                if s_['ew']:
                    vb(a, min(b, XMAX), 1.0, 1.27, lo, hi, WALK) if a < XMAX else None
                else:
                    vb(lo, hi, 1.0, 1.27, a, b, WALK)
    for e in ew:
        for n in ns:
            for sx in (-1, 1):
                for sz in (-1, 1):
                    x0, x1 = sorted((n['c'] + sx * n['ah'], n['c'] + sx * n['sh']))
                    z0, z1 = sorted((e['c'] + sz * e['ah'], e['c'] + sz * e['sh']))
                    if x0 < XMAX:
                        vb(x0, min(x1, XMAX), 1.0, 1.27, z0, z1, WALK)
    # the forest road continues west from the avenue (24 asphalt + 2-wide shoulders) and Avenue B leaves north and south
    vb(-1500, -H, 1.0, 1.06, 16, 44, '#A89F8C')
    vb(-1500, -H, 1.0, 1.09, 18, 42, '#3E4147')
    # plaza of the tower, park with paths, fountain, playground and flower beds, gardens, parking lots
    px0, px1, pz0, pz1 = S['plaza']
    vb(px0, min(px1, XMAX), 1.0, 1.27, pz0, pz1, '#E4E7EB')
    k0, k1, kz0, kz1 = S['park']
    vb(k0, k1, 1.0, 1.04, kz0, kz1, GRASS2)
    fx, fz = S['fountain']
    vb(fx - 22, fx + 22, 1.0, 1.27, fz - 22, fz + 22, '#E4E7EB')
    vb(k0, fx - 22, 1.0, 1.27, fz - 4, fz + 4, WALK)
    vb(fx + 22, k1, 1.0, 1.27, fz - 4, fz + 4, WALK)
    vb(fx - 4, fx + 4, 1.0, 1.27, kz0, fz - 22, WALK)
    vb(fx - 4, fx + 4, 1.0, 1.27, fz + 22, kz1, WALK)
    vcyl(fx, fz, 1.27, 2.9, 14.0, '#B9BAB6', seg=24)
    vcyl(fx, fz, 2.4, 2.6, 13.2, '#7DBCF2', seg=24)
    vcyl(fx, fz, 2.6, 7.0, 3.0, '#B9BAB6', seg=12, r2=1.0)
    vb(-100, -72, 1.04, 1.24, -97, -71, '#E9D9A8')                                   # playground
    for (cx, cz) in ((-18, -86), (-2, -86), (-18, -68), (-2, -68)):
        vcyl(cx, cz, 1.04, 1.6, 5.0, '#A44C30', seg=14)
        vcyl(cx, cz, 1.6, 1.7, 4.4, '#6A4A30', seg=14)
        for k in range(8):
            vsphere(cx + math.cos(k * 0.8) * 2.6, 2.3, cz + math.sin(k * 0.8) * 2.6, 0.7, 0.6, 0.7, ['#E43A2E', '#F8D030', '#F48CB2', '#F58A2A'][k % 4])
    for g in S['gardens']:
        vb(g[0], g[1], 1.0, 1.04, g[2], g[3], GRASS2)
        vb(g[0], g[1], 1.04, 1.27, (g[2] + g[3]) / 2 - 4, (g[2] + g[3]) / 2 + 4, WALK)
    for (nm, x0, x1, z0, z1) in S['lots']:
        if x0 < XMAX:
            vb(x0, min(x1, XMAX), 1.0, 1.09, z0, z1, '#525763')
            n_ = int((x1 - x0) // 10.4)
            for k in range(0, int((z1 - z0) // 5.2)):
                vb(x0 + 2, x1 - 2, 1.09, 1.12, z0 + 3 + k * 5.2 - 0.1, z0 + 3 + k * 5.2 + 0.1, '#FFFFFF') if k % 2 == 0 else None
    # buildings: walls, window grids, cornice, white parapet, flat blue roof, roof boxes
    wcols = {}
    for b in S['buildings']:
        if b['x0'] > XMAX or b['name'] == 'tower':
            continue
        x0, x1, z0, z1, top, wall, fl = b['x0'], b['x1'], b['z0'], b['z1'], b['top'], b['wall'], b['floors']
        vb(x0, x1, 1.0, top - 2.6, z0, z1, wall)
        vb(x0 - 0.5, x1 + 0.5, top - 3.95, top - 2.6, z0 - 0.5, z1 + 0.5, WHITE)
        for (qa, qb, qc, qd) in ((x0 + 0.1, x1 - 0.1, z0 + 0.1, z0 + 0.8), (x0 + 0.1, x1 - 0.1, z1 - 0.8, z1 - 0.1), (x0 + 0.1, x0 + 0.8, z0 + 0.8, z1 - 0.8), (x1 - 0.8, x1 - 0.1, z0 + 0.8, z1 - 0.8)):
            vb(qa, qb, top - 2.6, top - 0.4, qc, qd, '#F6F4EC')
        vb(x0 + 0.8, x1 - 0.8, top - 2.6, top - 2.4, z0 + 0.8, z1 - 0.8, ROOF)
        vb(x0 + (x1 - x0) * 0.3, x0 + (x1 - x0) * 0.3 + 7, top - 2.55, top + 2.5, (z0 + z1) / 2 - 3, (z0 + z1) / 2 + 3, '#F6F4EC')
        vb(x1 - 8, x1 - 5.4, top - 2.55, top - 0.7, z0 + 3, z0 + 5.6, WHITE)
        gh = 13.0
        for side in 'ESNW':
            L = (z1 - z0) if side in 'EW' else (x1 - x0)
            n = max(2, int((L - 4) // 6.4))
            step = (L - 4) / n
            for f in range(fl):
                yb = 1.0 + (3.8 if f == 0 else gh + (f - 1) * 11.0 + 2.6)
                for k in range(n):
                    u = 2 + step * (k + 0.5)
                    if side == 'E':
                        vb(x1, x1 + 0.35, yb, yb + 5.0, z0 + u - 1.9, z0 + u + 1.9, GLASS)
                    elif side == 'W':
                        vb(x0 - 0.35, x0, yb, yb + 5.0, z0 + u - 1.9, z0 + u + 1.9, GLASS)
                    elif side == 'S':
                        vb(x0 + u - 1.9, x0 + u + 1.9, yb, yb + 5.0, z1, z1 + 0.35, GLASS)
                    else:
                        vb(x0 + u - 1.9, x0 + u + 1.9, yb, yb + 5.0, z0 - 0.35, z0, GLASS)
    # trees of the district and the forest beyond the border
    for (x, z, r) in S['trees']:
        if x > XMAX:
            continue
        vcyl(x, z, 1.0, 10.0, 0.4, '#6B4524', seg=6, r2=0.3)
        for k in range(3):
            vsphere(x + math.cos(k * 2.1) * r * 0.35, 11.0 + k * 0.5, z + math.sin(k * 2.1) * r * 0.35, r * 0.7, r * 0.6, r * 0.7, ['#2FA84A', '#4DC252', '#34B04A'][k], seg=6, rings=4)
    rf = random.Random(77)
    for k in range(260):
        x = rf.uniform(-1100, -H - 12)
        z = rf.uniform(-420, 420)
        if 14 < z < 46:
            continue
        rr = rf.uniform(5, 9)
        vcyl(x, z, 1.0, rr * 2.0, 0.7, '#6B4524', seg=6)
        vsphere(x, rr * 2.4, z, rr, rr * 1.2, rr, ['#2F8F46', '#3E9E4A', '#2A7F3E'][k % 3], seg=7, rings=5)
    for k in range(120):
        x = rf.uniform(-H, XMAX)
        z = rf.choice((-1, 1)) * rf.uniform(H + 12, 520)
        if abs(z) > 0 and 28 < x < 52:
            continue
        rr = rf.uniform(5, 9)
        vcyl(x, z, 1.0, rr * 2.0, 0.7, '#6B4524', seg=6)
        vsphere(x, rr * 2.4, z, rr, rr * 1.2, rr, ['#2F8F46', '#3E9E4A', '#2A7F3E'][k % 3], seg=7, rings=5)
    # perimeter hedge (west side seen from afar) and distant hills on the horizon
    vb(-H, -H + 3, 1.0, 5.4, -H, H, '#2C9A3A')
    vb(-H, XMAX, 1.0, 5.4, -H, -H + 3, '#2C9A3A')
    vb(-H, XMAX, 1.0, 5.4, H - 3, H, '#2C9A3A')
    # gentle rolling hills on the horizon: wide and low (a dome taller than ~0.25 of its width reads as an egg), green near, hazier blue-green far
    prof = lambda hr, hh: [(hr, 0), (hr * 0.93, hh * 0.10), (hr * 0.80, hh * 0.28), (hr * 0.62, hh * 0.52), (hr * 0.42, hh * 0.76), (hr * 0.2, hh * 0.93), (0.0, hh)]
    for (hx, hz, hr, hh, col) in ((-1850, -950, 760, 170, '#5E9B6E'), (-2000, -150, 900, 230, '#548F66'), (-1900, 750, 800, 190, '#5E9B6E'),
                                  (-1700, 1500, 700, 150, '#6AA67A'), (-1800, -1750, 740, 170, '#6AA67A'),
                                  (-2500, -1350, 980, 260, '#7FAE9A'), (-2650, -300, 1100, 320, '#76A793'), (-2550, 700, 1000, 280, '#7FAE9A'),
                                  (-2450, 1500, 900, 230, '#8CB8A4'), (-2500, -2150, 950, 250, '#8CB8A4')):
        D.lathe(-37.0 - hz, hx - 117.5, 0.0 - VY, prof(hr, hh), col, seg=32)


def view_clouds():
    """puffy cartoon clouds low over the hills, seen through the window: a flat-bottomed row of big puffs with smaller puffs on top, white with a pale cool underside"""
    rc = random.Random(5)
    for k in range(20):
        cx = rc.uniform(-2300, -900)
        cz = rc.uniform(-1500, 1500)
        cy = rc.uniform(190, 420)
        base = rc.uniform(34, 70)
        n = rc.randint(4, 6)
        for j in range(n):
            u = (j - (n - 1) / 2.0) / ((n - 1) / 2.0)
            r = base * (1.0 - 0.35 * abs(u)) * rc.uniform(0.9, 1.15)
            px = cx + rc.uniform(-0.15, 0.15) * base
            pz = cz + u * base * 1.7
            D.sphere(-37.0 - pz, cy + r * 0.45 - VY, px - 117.5, r * 1.25, r * 0.85, r * 1.1, '#F3F7FB', seg=12, rings=8, jitter=0.05, seed=k * 31 + j)
            if j % 2 == 0:
                rt = r * rc.uniform(0.6, 0.8)
                D.sphere(-37.0 - (pz + rc.uniform(-0.3, 0.3) * r), cy + r * 1.1 + rt * 0.5 - VY, px - 117.5, rt * 1.15, rt * 0.85, rt, '#FFFFFF', seg=12, rings=8, jitter=0.05, seed=k * 31 + j + 7)


view_district()
view_clouds()
