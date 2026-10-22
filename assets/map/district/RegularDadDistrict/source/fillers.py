# Infrastructure for the empty parts of the district (exec'd by build_district.py after layout.py, before the audit).
# Fuel station, courtyard parking behind the tower, alleys with dumpsters, community gardens, street-workout park, courts, gazebo, skate plaza,
# dog park, kiosk, perimeter tree line. Every object registers a collider (the audit checks them) and, where it has none, a map zone.


def zone(ch, x0, x1, z0, z1):
    ZONES_OCC.append((ch, x0, x1, z0, z1))


def slab(x0, x1, z0, z1, col, h=0.12, ch='f', y=GY):
    box(x0, x1, y, y + h, z0, z1, col)
    zone(ch, x0, x1, z0, z1)


def fence_line(x0, z0, x1, z1, h=3.2, col=None, glass=False, name='fence'):
    col = col or PAL['white']
    n = max(1, int(math.hypot(x1 - x0, z1 - z0) // 3))
    for i in range(n + 1):
        px, pz = x0 + (x1 - x0) * i / n, z0 + (z1 - z0) * i / n
        box(px - 0.15, px + 0.15, GY, GY + h, pz - 0.15, pz + 0.15, col)
    for yy in (0.7, h - 0.4):
        box(min(x0, x1) - 0.1, max(x0, x1) + 0.1, GY + yy, GY + yy + 0.2, min(z0, z1) - 0.1, max(z0, z1) + 0.1, col)
    if glass:
        box(min(x0, x1) - 0.04, max(x0, x1) + 0.04, GY + 0.9, GY + h - 0.5, min(z0, z1) - 0.04, max(z0, z1) + 0.04, PAL['glass'], 'G')
    collider(min(x0, x1) - 0.25, max(x0, x1) + 0.25, GY, GY + h, min(z0, z1) - 0.25, max(z0, z1) + 0.25, name)


def dumpster(x, z, along='x', col=None):
    col = col or PAL['green']
    hx, hz = (2.2, 1.1) if along == 'x' else (1.1, 2.2)
    box(x - hx, x + hx, GY + 0.45, GY + 3.0, z - hz, z + hz, col)
    box(x - hx - 0.12, x + hx + 0.12, GY + 3.0, GY + 3.25, z - hz - 0.12, z + hz + 0.12, PAL['dark'])
    for (sx, sz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        cyl(x + sx * (hx - 0.45), z + sz * (hz - 0.45), GY, GY + 0.45, 0.3, PAL['dark'], seg=8)
    box(x - hx, x + hx, GY + 1.6, GY + 1.75, z - hz - 0.05, z + hz + 0.05, shade(col, -0.25))
    collider(x - hx - 0.1, x + hx + 0.1, GY, GY + 3.3, z - hz - 0.1, z + hz + 0.1, 'dumpster')


def garage_block(x0, x1, z0, z1, front, n, col, name='garage'):
    b = R(x0, x1, z0, z1)
    box(x0, x1, GY, GY + 9, z0, z1, col)
    box(x0 - 0.3, x1 + 0.3, GY + 9, GY + 9.5, z0 - 0.3, z1 + 0.3, PAL['white'])
    box(x0 + 0.5, x1 - 0.5, GY + 9.5, GY + 9.7, z0 + 0.5, z1 - 0.5, PAL['dark'])
    w = (b.width(front) - 2.0) / n
    for k in range(n):
        u0, u1 = 1.0 + k * w + 0.6, 1.0 + (k + 1) * w - 0.6
        lb(front, b, u0, u1, GY + 0.1, GY + 7.4, 0.0, 0.35, PAL['white'])
        for r_ in range(8):
            lb(front, b, u0 + 0.25, u1 - 0.25, GY + 0.35 + r_ * 0.9, GY + 0.35 + r_ * 0.9 + 0.7, 0.35, 0.6, PAL['gray'])
        lb(front, b, u0, u1, GY + 7.4, GY + 7.7, 0.0, 0.6, PAL['dark'])
    collider(x0, x1, GY, GY + 9.7, z0, z1, name)


def substation(x, z, w=6.0, d=5.0):
    box(x - w / 2, x + w / 2, GY, GY + 6.5, z - d / 2, z + d / 2, PAL['concrete'])
    box(x - w / 2 - 0.3, x + w / 2 + 0.3, GY + 6.5, GY + 7.0, z - d / 2 - 0.3, z + d / 2 + 0.3, PAL['gray'])
    box(x - 1.2, x + 1.2, GY, GY + 4.6, z + d / 2, z + d / 2 + 0.3, PAL['dark'])
    for k in range(4):
        box(x - 2.4 + k * 1.6, x - 1.6 + k * 1.6, GY + 5.0, GY + 6.0, z + d / 2, z + d / 2 + 0.2, PAL['metal'])
    box(x - 0.8, x + 0.8, GY + 2.2, GY + 3.4, z + d / 2 + 0.3, z + d / 2 + 0.38, PAL['yellow'])
    collider(x - w / 2 - 0.3, x + w / 2 + 0.3, GY, GY + 7.0, z - d / 2 - 0.3, z + d / 2 + 0.3, 'substation')


def bike_shelter(x0, x1, z, depth=4.0):
    for px in (x0 + 0.3, x1 - 0.3):
        for pz in (z - depth / 2 + 0.2, z + depth / 2 - 0.2):
            box(px - 0.15, px + 0.15, GY, GY + 5.0, pz - 0.15, pz + 0.15, PAL['dark'])
    box(x0 - 0.4, x1 + 0.4, GY + 5.0, GY + 5.35, z - depth / 2 - 0.4, z + depth / 2 + 0.4, PAL['teal'])
    box(x0 - 0.4, x1 + 0.4, GY + 5.35, GY + 5.5, z - depth / 2 - 0.4, z + depth / 2 + 0.4, PAL['white'])
    n = int((x1 - x0 - 1.0) // 1.6)
    for k in range(n):
        px = x0 + 1.0 + k * 1.6
        box(px - 0.06, px + 0.06, GY, GY + 1.6, z - 0.9, z - 0.78, PAL['metal'])
        box(px - 0.06, px + 0.06, GY, GY + 1.6, z + 0.78, z + 0.9, PAL['metal'])
        box(px - 0.06, px + 0.06, GY + 1.5, GY + 1.66, z - 0.9, z + 0.9, PAL['metal'])
    collider(x0 - 0.4, x1 + 0.4, GY, GY + 5.5, z - depth / 2 - 0.4, z + depth / 2 + 0.4, 'bikeshelter')


def kiosk(x, z, w, d, col, awn, text=None, face='S'):
    box(x - w / 2, x + w / 2, GY, GY + 9.0, z - d / 2, z + d / 2, col)
    box(x - w / 2 - 0.5, x + w / 2 + 0.5, GY + 9.0, GY + 9.5, z - d / 2 - 0.5, z + d / 2 + 0.5, PAL['white'])
    sgn = 1 if face == 'S' else -1
    zf = z + sgn * d / 2
    box(x - w / 2 + 0.8, x + w / 2 - 0.8, GY + 2.6, GY + 6.8, zf, zf + sgn * 0.12, PAL['glass'], 'G')
    box(x - w / 2 + 0.7, x + w / 2 - 0.7, GY + 2.3, GY + 2.6, zf, zf + sgn * 0.7, PAL['wood'])
    for k in range(int(w // 1.6)):
        box(x - w / 2 + 0.2 + k * 1.6, x - w / 2 + 1.0 + k * 1.6, GY + 7.0, GY + 8.3, zf, zf + sgn * 1.6, awn[k % 2])
    box(x - 0.9, x + 0.9, GY, GY + 5.4, zf - sgn * 0.02, zf + sgn * 0.05, PAL['door']) if False else None
    if text:
        SIGNS.append((text, x, GY + 10.8, zf + sgn * 0.3, w, 2.0, face))
        box(x - w / 2, x + w / 2, GY + 9.8, GY + 11.8, zf + sgn * 0.1, zf + sgn * 0.25, PAL['navy'])
    collider(x - w / 2 - 0.5, x + w / 2 + 0.5, GY, GY + 9.5, z - d / 2 - 0.5, z + d / 2 + 1.0, 'kiosk')


def gazebo(x, z, r=5.0):
    cyl(x, z, GY, GY + 0.5, r, PAL['walk'], seg=8)
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        px, pz = x + (r - 0.6) * math.cos(a), z + (r - 0.6) * math.sin(a)
        cyl(px, pz, GY + 0.5, GY + 7.5, 0.25, PAL['white'], seg=8)
        if k % 2 == 0:
            box(px - 0.35, px + 0.35, GY + 0.5, GY + 1.0, pz - 0.35, pz + 0.35, PAL['white'])
    D.lathe(x, z, GY + 7.5, [(r + 0.9, 0), (r + 0.9, 0.4), (r - 0.3, 0.6), (r * 0.55, 1.8), (0.4, 3.6), (0.0, 3.9)], PAL['teal'], seg=8)
    D.sphere(x, GY + 11.6, z, 0.4, 0.4, 0.4, PAL['yellow'], seg=8, rings=5)
    for k in range(4):
        a = k * math.pi / 2
        bench(x + (r - 2.2) * math.cos(a), z + (r - 2.2) * math.sin(a), rot=-math.degrees(a) + 90) if False else None
    cyl(x, z, GY + 0.5, GY + 1.0, 1.5, PAL['wood'], seg=12)
    collider(x - r, x + r, GY, GY + 11.9, z - r, z + r, 'gazebo')


def picnic(x, z, along='x'):
    hx, hz = (2.2, 1.0) if along == 'x' else (1.0, 2.2)
    box(x - hx, x + hx, GY + 1.7, GY + 1.95, z - hz, z + hz, PAL['wood'])
    if along == 'x':
        for sz in (-1, 1):
            box(x - hx, x + hx, GY + 1.0, GY + 1.2, z + sz * 1.6 - 0.5, z + sz * 1.6 + 0.5, PAL['wood2'])
        for sx in (-1, 1):
            box(x + sx * 1.6 - 0.12, x + sx * 1.6 + 0.12, GY, GY + 1.7, z - 1.7, z + 1.7, PAL['wood2'])
        collider(x - hx, x + hx, GY, GY + 2, z - 2.1, z + 2.1, 'picnic')
    else:
        for sx in (-1, 1):
            box(x + sx * 1.6 - 0.5, x + sx * 1.6 + 0.5, GY + 1.0, GY + 1.2, z - hz, z + hz, PAL['wood2'])
        for sz in (-1, 1):
            box(x - 1.7, x + 1.7, GY, GY + 1.7, z + sz * 1.6 - 0.12, z + sz * 1.6 + 0.12, PAL['wood2'])
        collider(x - 2.1, x + 2.1, GY, GY + 2, z - hz, z + hz, 'picnic')


def court_lines(x0, x1, z0, z1, col=None):
    col = col or PAL['white']
    t = 0.22
    for (a, b, c, d) in ((x0, x1, z0, z0 + t), (x0, x1, z1 - t, z1), (x0, x0 + t, z0, z1), (x1 - t, x1, z0, z1)):
        box(a, b, GY + 0.2, GY + 0.26, c, d, col)


def basketball(x0, x1, z0, z1):
    box(x0 - 1.5, x1 + 1.5, GY, GY + 0.2, z0 - 1.5, z1 + 1.5, '#6B7A8F')
    box(x0, x1, GY + 0.2, GY + 0.22, z0, z1, '#C8523E')
    court_lines(x0, x1, z0, z1)
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    box(cx - 0.11, cx + 0.11, GY + 0.22, GY + 0.28, z0, z1, PAL['white'])
    cyl(cx, cz, GY + 0.22, GY + 0.28, 3.0, PAL['white'], seg=24) if False else None
    for sx in (-1, 1):
        px = x0 + 1.2 if sx < 0 else x1 - 1.2
        box(px - 0.18, px + 0.18, GY + 0.2, GY + 10.0, cz - 0.18, cz + 0.18, PAL['dark'])
        bx = px + (0.9 if sx < 0 else -0.9)
        box(min(px, bx) - 0.1, max(px, bx) + 0.1, GY + 9.6, GY + 9.8, cz - 0.1, cz + 0.1, PAL['dark'])
        bx2 = px + (1.2 if sx < 0 else -1.2)
        box(bx2 - 0.1, bx2 + 0.1, GY + 8.6, GY + 11.4, cz - 2.0, cz + 2.0, PAL['glass'], 'G')
        box(bx2 - 0.12, bx2 + 0.12, GY + 8.6, GY + 11.4, cz - 2.05, cz - 1.95, PAL['white'])
        cyl(bx2 + (0.9 if sx < 0 else -0.9), cz, GY + 9.2, GY + 9.28, 0.9, PAL['orange'], seg=16)
        collider(px - 0.3, px + 0.3, GY, GY + 10.0, cz - 0.3, cz + 0.3, 'hoop')
    for sx in (-1, 1):
        xx = (x0 - 1.4) if sx < 0 else (x1 + 1.4)
        fence_line(xx, z0 - 1.4, xx, z1 + 1.4, h=7.0, glass=True, name='courtfence')
    zone('f', x0 - 1.5, x1 + 1.5, z0 - 1.5, z1 + 1.5)


def tennis(x0, x1, z0, z1):
    box(x0 - 2, x1 + 2, GY, GY + 0.2, z0 - 2, z1 + 2, '#3E7E55')
    box(x0, x1, GY + 0.2, GY + 0.22, z0, z1, '#5BA877')
    court_lines(x0, x1, z0, z1)
    cx = (x0 + x1) / 2
    box(x0 + 3.5, x1 - 3.5, GY + 0.22, GY + 0.27, (z0 + z1) / 2 - 0.1, (z0 + z1) / 2 + 0.1, PAL['white'])
    box(cx - 0.11, cx + 0.11, GY + 0.22, GY + 0.27, z0 + 3.5, z1 - 3.5, PAL['white'])
    box(cx - 0.11, cx + 0.11, GY + 0.22, GY + 0.27, z0, z1, PAL['white'])
    box(cx - 0.2, cx + 0.2, GY, GY + 3.0, z0 - 1.2, z0 - 0.8, PAL['dark'])
    box(cx - 0.2, cx + 0.2, GY, GY + 3.0, z1 + 0.8, z1 + 1.2, PAL['dark'])
    box(cx - 0.04, cx + 0.04, GY + 1.0, GY + 3.0, z0 - 1.0, z1 + 1.0, PAL['dark'], 'G')
    box(cx - 0.08, cx + 0.08, GY + 2.8, GY + 3.05, z0 - 1.0, z1 + 1.0, PAL['white'])
    collider(cx - 0.3, cx + 0.3, GY, GY + 3.0, z0 - 1.3, z1 + 1.3, 'net')
    for sx in (-1, 1):
        xx = (x0 - 1.8) if sx < 0 else (x1 + 1.8)
        fence_line(xx, z0 - 1.8, xx, z1 + 1.8, h=8.0, glass=True, name='courtfence')
    for sz in (-1, 1):
        zz = (z0 - 1.8) if sz < 0 else (z1 + 1.8)
        fence_line(x0 - 1.8, zz, x1 + 1.8, zz, h=8.0, glass=True, name='courtfence')
    zone('f', x0 - 2, x1 + 2, z0 - 2, z1 + 2)


def frustum(cx, cz, w, d, h, ins, col, y=GY):
    x0, x1, z0, z1 = cx - w / 2, cx + w / 2, cz - d / 2, cz + d / 2
    v = [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1), (x0 + ins, y + h, z0 + ins), (x1 - ins, y + h, z0 + ins), (x1 - ins, y + h, z1 - ins), (x0 + ins, y + h, z1 - ins)]
    D._add('O', v, D._BOXF, col)


def skate_plaza(x0, x1, z0, z1):
    slab(x0, x1, z0, z1, '#B9B6AE', h=0.25)
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    frustum(cx, cz, 8, 8, 1.6, 2.4, '#8C9099', y=GY + 0.25)
    collider(cx - 4, cx + 4, GY, GY + 1.85, cz - 4, cz + 4, 'skate_pyramid')
    D.slope(x0 + 2, x0 + 9, GY + 0.25, GY + 3.2, z0 + 2, z0 + 8, '#8C9099', axis='x')
    collider(x0 + 2, x0 + 9, GY, GY + 2.0, z0 + 2, z0 + 8, 'skate_ramp')
    D.slope(x1 - 9, x1 - 2, GY + 3.2, GY + 0.25, z1 - 8, z1 - 2, '#8C9099', axis='x')
    collider(x1 - 9, x1 - 2, GY, GY + 2.0, z1 - 8, z1 - 2, 'skate_ramp')
    box(x0 + 3, x0 + 12, GY + 0.25, GY + 1.3, z1 - 6, z1 - 4, '#6F7480')
    box(x0 + 3, x0 + 12, GY + 1.3, GY + 1.45, z1 - 6.1, z1 - 3.9, PAL['yellow'])
    collider(x0 + 3, x0 + 12, GY, GY + 1.5, z1 - 6.1, z1 - 3.9, 'skate_box')
    for k in range(2):
        box(x1 - 12, x1 - 4, GY + 0.25 + 1.0 + k * 0.0, GY + 1.45, z0 + 4 + k * 2.2, z0 + 4.12 + k * 2.2, PAL['metal'])
        for sx in (x1 - 12, x1 - 4.1):
            box(sx, sx + 0.12, GY + 0.25, GY + 1.45, z0 + 4 + k * 2.2, z0 + 4.12 + k * 2.2, PAL['metal'])
    collider(x1 - 12, x1 - 4, GY, GY + 1.5, z0 + 4, z0 + 8.4, 'skate_rail')


def workout_park(x0, x1, z0, z1):
    slab(x0, x1, z0, z1, '#9C4E46', h=0.25)
    n = 4
    for k in range(n):
        zz = z0 + 6 + k * ((z1 - z0 - 12) / (n - 1))
        for px in (x0 + 4, x0 + 8.5):
            box(px - 0.18, px + 0.18, GY + 0.25, GY + 8.0, zz - 0.18, zz + 0.18, PAL['metal'])
        box(x0 + 3.8, x0 + 8.7, GY + 7.6, GY + 7.9, zz - 0.15, zz + 0.15, PAL['metal'])
        collider(x0 + 3.7, x0 + 8.8, GY, GY + 8.0, zz - 0.4, zz + 0.4, 'pullup')
    for k in range(3):
        zz = z0 + 8 + k * 14
        for dz in (-0.7, 0.7):
            box(x1 - 9.2, x1 - 5.2, GY + 3.2, GY + 3.4, zz + dz - 0.1, zz + dz + 0.1, PAL['metal'])
            for px in (x1 - 9.1, x1 - 5.3):
                box(px - 0.1, px + 0.1, GY + 0.25, GY + 3.4, zz + dz - 0.1, zz + dz + 0.1, PAL['metal'])
        collider(x1 - 9.3, x1 - 5.1, GY, GY + 3.4, zz - 0.9, zz + 0.9, 'parbars')
    box(x0 + 1.0, x0 + 3.0, GY + 0.25, GY + 1.2, z0 + 1.5, z0 + 6.0, PAL['dark'])
    collider(x0 + 1.0, x0 + 3.0, GY, GY + 1.2, z0 + 1.5, z0 + 6.0, 'bench_press')
    box(x0 + 1.0, x0 + 1.4, GY + 1.2, GY + 2.2, z0 + 1.5, z0 + 6.0, PAL['red'])
    SIGNS.append(('WORKOUT', (x0 + x1) / 2, GY + 6.0, z1 + 0.35, 10, 2.4, 'S')) if False else None


def garden_bed(x0, x1, z0, z1, seed, along='z'):
    box(x0, x1, GY, GY + 0.5, z0, z1, PAL['wood2'])
    box(x0 + 0.3, x1 - 0.3, GY + 0.5, GY + 0.62, z0 + 0.3, z1 - 0.3, PAL['soil'])
    rnd = random.Random(seed)
    cols = [PAL['green'], PAL['grass'], '#C9D654', PAL['red'], PAL['orange'], PAL['plum']]
    L = (z1 - z0) if along == 'z' else (x1 - x0)
    for k in range(int(L // 1.6)):
        c = cols[(k + seed) % len(cols)]
        px = (x0 + x1) / 2 + (rnd.uniform(-0.5, 0.5) if along == 'z' else 0)
        pz = z0 + 0.8 + k * 1.6 if along == 'z' else (z0 + z1) / 2
        if along == 'x':
            px = x0 + 0.8 + k * 1.6
        D.sphere(px, GY + 1.05, pz, 0.62, 0.45, 0.62, c, seg=7, rings=5, jitter=0.05, seed=k)
    collider(x0, x1, GY, GY + 1.2, z0, z1, 'gardenbed')


def greenhouse(x, z, w=9.0, d=6.0):
    box(x - w / 2, x + w / 2, GY, GY + 0.6, z - d / 2, z + d / 2, PAL['concrete'])
    box(x - w / 2 + 0.2, x + w / 2 - 0.2, GY + 0.6, GY + 4.6, z - d / 2 + 0.2, z + d / 2 - 0.2, PAL['glass'], 'G')
    for k in range(int(w // 1.5) + 1):
        px = x - w / 2 + 0.1 + k * (w - 0.2) / int(w // 1.5)
        box(px - 0.08, px + 0.08, GY + 0.6, GY + 4.8, z - d / 2, z + d / 2, PAL['white'])
    for pz in (z - d / 2, z + d / 2 - 0.1):
        box(x - w / 2, x + w / 2, GY + 4.6, GY + 4.8, pz, pz + 0.1, PAL['white'])
    D._add('G', [(x - w / 2, GY + 4.6, z - d / 2), (x + w / 2, GY + 4.6, z - d / 2), (x + w / 2, GY + 4.6, z + d / 2), (x - w / 2, GY + 4.6, z + d / 2),
                 (x - w / 2, GY + 6.4, z), (x + w / 2, GY + 6.4, z), (x + w / 2, GY + 6.4, z), (x - w / 2, GY + 6.4, z)], D._BOXF, PAL['glass'])
    box(x - w / 2, x + w / 2, GY + 6.3, GY + 6.5, z - 0.1, z + 0.1, PAL['white'])
    for k in range(4):
        D.sphere(x - w / 2 + 1.4 + k * 2.0, GY + 1.2, z, 0.6, 0.6, 0.6, [PAL['red'], PAL['green'], PAL['orange'], PAL['plum']][k], seg=7, rings=5)
    collider(x - w / 2, x + w / 2, GY, GY + 6.5, z - d / 2, z + d / 2, 'greenhouse')


def shed(x, z, w=6.0, d=5.0, col=None):
    box(x - w / 2, x + w / 2, GY, GY + 5.0, z - d / 2, z + d / 2, col or PAL['wood'])
    D._add('O', [(x - w / 2 - 0.4, GY + 5.0, z - d / 2 - 0.4), (x + w / 2 + 0.4, GY + 5.0, z - d / 2 - 0.4), (x + w / 2 + 0.4, GY + 5.0, z + d / 2 + 0.4), (x - w / 2 - 0.4, GY + 5.0, z + d / 2 + 0.4),
                 (x - w / 2 - 0.4, GY + 6.6, z - d / 2 - 0.4), (x + w / 2 + 0.4, GY + 6.6, z - d / 2 - 0.4), (x + w / 2 + 0.4, GY + 5.4, z + d / 2 + 0.4), (x - w / 2 - 0.4, GY + 5.4, z + d / 2 + 0.4)],
            D._BOXF, PAL['red'])
    box(x - 1.0, x + 1.0, GY, GY + 3.6, z + d / 2, z + d / 2 + 0.15, PAL['wood2'])
    box(x + w / 2 - 1.6, x + w / 2 - 0.5, GY + 2.0, GY + 3.4, z + d / 2, z + d / 2 + 0.1, PAL['glass'], 'G')
    collider(x - w / 2 - 0.4, x + w / 2 + 0.4, GY, GY + 6.6, z - d / 2 - 0.4, z + d / 2 + 0.4, 'shed')


def fuel_station(x0, x1, z0, z1):
    cx = (x0 + x1) / 2
    slab(x0, x1, z0, z1, '#7C7F88', h=0.12, ch='f')
    for zz in range(int(z0) + 4, int(z1) - 2, 6):
        box(x0 + 2, x1 - 2, GY + 0.12, GY + 0.16, zz, zz + 0.2, PAL['yellow']) if False else None
    cz = (z0 + z1) / 2 - 2
    cw, cd = 26, 16
    for sx in (-1, 1):
        for sz in (-1, 1):
            box(cx + sx * (cw / 2 - 1.5) - 0.6, cx + sx * (cw / 2 - 1.5) + 0.6, GY, GY + 12.0, cz + sz * (cd / 2 - 1.5) - 0.6, cz + sz * (cd / 2 - 1.5) + 0.6, PAL['white'])
            collider(cx + sx * (cw / 2 - 1.5) - 0.7, cx + sx * (cw / 2 - 1.5) + 0.7, GY, GY + 12, cz + sz * (cd / 2 - 1.5) - 0.7, cz + sz * (cd / 2 - 1.5) + 0.7, 'fuel_col')
    box(cx - cw / 2, cx + cw / 2, GY + 12.0, GY + 13.4, cz - cd / 2, cz + cd / 2, PAL['white'])
    box(cx - cw / 2 - 0.1, cx + cw / 2 + 0.1, GY + 12.0, GY + 12.9, cz - cd / 2 - 0.1, cz + cd / 2 + 0.1, PAL['red'])
    box(cx - cw / 2, cx + cw / 2, GY + 11.7, GY + 12.0, cz - cd / 2 + 0.3, cz + cd / 2 - 0.3, PAL['light'] if 'light' in PAL else PAL['white'], 'N')
    for sx in (-1, 1):
        ix = cx + sx * 6.0
        box(ix - 1.1, ix + 1.1, GY + 0.12, GY + 0.6, cz - 5.5, cz + 5.5, PAL['concrete'])
        for sz in (-1, 1):
            pz = cz + sz * 2.7
            box(ix - 0.7, ix + 0.7, GY + 0.6, GY + 5.6, pz - 0.6, pz + 0.6, PAL['red'])
            box(ix - 0.75, ix + 0.75, GY + 3.2, GY + 4.6, pz - 0.62, pz + 0.62, PAL['dark'])
            box(ix - 0.5, ix + 0.5, GY + 3.4, GY + 4.4, pz - 0.65, pz - 0.7 if False else pz + 0.64, PAL['glass'], 'G')
            box(ix - 0.1, ix + 0.1, GY + 2.6, GY + 3.0, pz + 0.6, pz + 0.9, PAL['dark'])
            box(ix - 0.8, ix + 0.8, GY + 5.6, GY + 5.9, pz - 0.7, pz + 0.7, PAL['white'])
        collider(ix - 1.1, ix + 1.1, GY, GY + 5.9, cz - 4.0, cz + 4.0, 'pump')
    kx0, kx1, kz0, kz1 = x0 + 2, x0 + 11, z1 - 8, z1 - 2
    kiosk(cx, kz1 - 3 if False else (kz0 + kz1) / 2 + 3, 10, 6, PAL['cream'], (PAL['red'], PAL['white']), text='SHOP', face='N')
    # price sign pole
    box(x1 - 2.2, x1 - 1.8, GY, GY + 14, z0 + 1.8, z0 + 2.2, PAL['dark'])
    box(x1 - 3.4, x1 - 0.6, GY + 11, GY + 15, z0 + 1.7, z0 + 2.3, PAL['red'])
    for k in range(3):
        box(x1 - 3.1, x1 - 0.9, GY + 11.4 + k * 1.15, GY + 12.2 + k * 1.15, z0 + 2.3, z0 + 2.38, PAL['yellow'], 'N')
    collider(x1 - 3.4, x1 - 0.6, GY, GY + 15, z0 + 1.7, z0 + 2.3, 'fuel_sign')
    car(cx, cz + 0.0, 90, PAL['teal'], seed=3)
    # tyre stack and air pump at the corner
    for k in range(3):
        D.lathe(x0 + 3, z0 + 3, GY + k * 0.9, [(0.8, 0), (0.8, 0.8), (0.4, 0.8), (0.4, 0.0)], PAL['dark'], seg=12)
    collider(x0 + 2.0, x0 + 4.0, GY, GY + 2.7, z0 + 2.0, z0 + 4.0, 'tyres')


def pocket_perimeter_trees():
    for side in 'NSEW':
        p = -214
        while p <= 214:
            x, z = (p, -219.5) if side == 'N' else (p, 219.5) if side == 'S' else (-219.5, p) if side == 'W' else (219.5, p)
            on_axis = abs(p) < 21 + 6
            on_serv = (side in 'WE' and abs(p + 145) < 16) or (side == 'W' and abs(p - 145) < 16)
            if not on_axis and not on_serv:
                tree(x, z, seed=int(p) + 7, h=8.0, r=3.6, pit=False)
            p += 12


# ---- courtyard behind the tower: parking, substation, bin enclosure, bike shelter ---------------------------------------------------------------
slab(-124, -66, -128, -96, PAL['asph2'], h=0.1, ch='=')
box(-100, -88, GY, GY + 0.6, -137, -132, PAL['asph2'])
D.slope(-100, -88, GY + 0.1, GY + 0.6, -132, -128, PAL['asph2'], axis='z')
for k in range(12):
    px = -123 + k * 5
    box(px - 0.1, px + 0.1, GY + 0.1, GY + 0.16, -128, -118.5, PAL['white'])
    box(px - 0.1, px + 0.1, GY + 0.1, GY + 0.16, -105.5, -96, PAL['white'])
for k, px in enumerate((-120.5, -115.5, -110.5, -105.5, -85.5, -80.5)):
    car(px, -123.2, 90, CARC[(k + 1) % 8], seed=k + 40)
for k, px in enumerate((-107, -96, -91, -84, -79.5)):
    car(px, -100.8, 270, CARC[(k + 3) % 8], seed=k + 60)
box(-124, -66, GY + 0.1, GY + 0.14, -111.9, -111.7, PAL['lane'])
for px in (-118, -78):
    street_lamp(px, -112.5, facing=1.57)
substation(-70.5, -98.5)
fence_line(-75.5, -102.5, -65.5, -102.5, h=3.0)
fence_line(-75.5, -102.5, -75.5, -95.5, h=3.0)
bike_shelter(-110, -96, -93.5, depth=3.0) if False else None
for k in range(2):
    dumpster(-95 + k * 5.0, -126.5, 'x', [PAL['green'], PAL['blue']][k]) if False else None
dumpster(-70.0, -125.5, 'x')
dumpster(-70.0, -121.5, 'x', PAL['blue'])
fence_line(-75.2, -127.5, -75.2, -119.5, h=4.0, col=PAL['wood2'])
fence_line(-75.2, -127.5, -65.0, -127.5, h=4.0, col=PAL['wood2'])
fence_line(-75.2, -119.5, -65.0, -119.5, h=4.0, col=PAL['wood2'])
garage_block(-124, -108, -96.0, -92.2, 'S', 3, PAL['concrete']) if False else None
bike_shelter(-123, -112, -98.4, depth=3.2)

# ---- alleys: paving, dumpsters, bins ------------------------------------------------------------------------------------------------------------------
slab(-214, -130, -100, -88, PAL['walk2'], h=0.1, ch='a')
for k, x in enumerate((-190, -168, -146)):
    dumpster(x, -94.0, 'x', [PAL['green'], PAL['blue'], PAL['green']][k])
for x in (-180, -158):
    trash_bin(x, -94.0)
slab(-190, -120, 94, 100, PAL['walk2'], h=0.1, ch='a')
for x in (-178, -150, -126):
    trash_bin(x, 97.0)
slab(-84, -34, 82, 100, PAL['walk2'], h=0.1, ch='a')
for k, x in enumerate((-76, -64)):
    dumpster(x, 90.0, 'x', [PAL['green'], PAL['blue']][k])
trash_bin(-48, 90.0)
bike_shelter(-58, -42, 96.0, depth=3.2) if False else None
for k in range(8):
    xx = -50 + k * 0
    break

# ---- fuel station between the Gym and the pizza cafe -----------------------------------------------------------------------------------------------
paving(-120, -84, 21.2, 50)
fuel_station(-118.5, -85.5, 52, 92)

# ---- kiosk and pocket park between the neighbour block and the tower -----------------------------------------------------------------------
kiosk(-135, -76, 8, 6, PAL['yellow'], (PAL['blue'], PAL['white']), text='NEWS')
for (x, z) in ((-143, -84), (-128, -86)):
    tree(x, z, seed=int(x), h=9, r=4.0, pit=False)
bench(-135, -66.5, rot=0)
street_lamp(-144, -68, facing=0.0)
box(-146, -122, GY, GY + 0.05, -62, -61, PAL['grass2'])

# ---- community garden (NW perimeter), street workout (SW perimeter) ------------------------------------------------------------------------------
box(-216, -198, GY, GY + 0.04, -100, -34, PAL['grass2'])
zone('g', -216, -198, -100, -34)
for k in range(3):
    xx = -215 + k * 5.5
    garden_bed(xx, xx + 3.6, -96, -66, seed=k, along='z')
greenhouse(-207.0, -56, 9.0, 6.0)
shed(-212, -44, 6, 5)
for k in range(3):
    garden_bed(-205 + k * 0.0, -201, -40 - k * 0, -39, seed=k + 9) if False else None
fence_line(-217, -100, -217, -34, h=3.0, col=PAL['wood2'])
fence_line(-217, -34, -197, -34, h=3.0, col=PAL['wood2'])
workout_park(-214, -194, 38, 94)
street_lamp(-196, 36, facing=3.14)
street_lamp(-196, 96, facing=3.14)

# ---- parking lot behind the stores: lamps and chargers ---------------------------------------------------------------------------------------------
for k in range(6):
    street_lamp(58 + k * 28, -124.5, facing=1.57)
for k in range(5):
    px = 194 + k * 4.2
    box(px - 0.4, px + 0.4, GY, GY + 4.0, -122.4, -121.6, PAL['white'])
    box(px - 0.5, px + 0.5, GY + 2.0, GY + 3.6, -122.5, -121.5, PAL['teal'])
    box(px - 0.3, px + 0.3, GY + 2.5, GY + 3.3, -121.5, -121.4, PAL['green'], 'N')
    collider(px - 0.5, px + 0.5, GY, GY + 4.0, -122.5, -121.5, 'charger')
car(196.0, -114.0, 90, PAL['blue'], seed=5)

# ---- park additions ---------------------------------------------------------------------------------------------------------------------------------
gazebo(52, 100, 5.0)
basketball(150, 178, 94, 109)
tennis(40, 64, 192, 204)
for k, (x, z, al) in enumerate(((40, 138, 'x'), (52, 138, 'x'), (46, 146, 'x'))):
    picnic(x, z, al)
skate_plaza(144, 174, 134, 160)
# dog park fence and agility toys
fence_line(190, 70, 205, 70, h=3.4, glass=False, name='dogfence')
fence_line(190, 108, 205, 108, h=3.4, name='dogfence')
fence_line(205, 70, 205, 108, h=3.4, name='dogfence')
fence_line(190, 70, 190, 90, h=3.4, name='dogfence')
fence_line(190, 98, 190, 108, h=3.4, name='dogfence')
for k in range(5):
    cyl(194 + k * 2.2, 80, GY, GY + 2.4, 0.12, PAL['orange'], seg=6)
    collider(194 + k * 2.2 - 0.2, 194 + k * 2.2 + 0.2, GY, GY + 2.4, 79.8, 80.2, 'dogpole')
D.slope(194, 200, GY + 0.2, GY + 3.0, 94, 97, PAL['blue'], axis='x')
collider(194, 200, GY, GY + 1.6, 94, 97, 'dogramp')
zone('f', 190, 205, 70, 108)
slab(30, 33, 66, 209, PAL['walk'], h=0.1, ch='p')
slab(30, 212, 206, 209, PAL['walk'], h=0.1, ch='p')
slab(207, 210, 66, 206, PAL['walk'], h=0.1, ch='p')
for z in range(80, 206, 28):
    street_lamp(36, z, facing=3.14)
    bench(35.5, z + 12, rot=90)
for x in (90, 120, 150):
    street_lamp(x, 202, facing=-1.57)

pocket_perimeter_trees()
