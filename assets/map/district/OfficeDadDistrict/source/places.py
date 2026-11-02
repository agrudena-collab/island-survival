# Open places: park with fountain and kiosk, parking lots with driveways, the two gardens (all coordinates Studio-like, z = -plan Y).
LOTS = []                                      # (name, x0, x1, z0, z1): cars and lot furniture may stand here
CARC = ['#2F63B8', '#F4F3EE', '#8F959E', '#E43A2E', '#12AC9C', '#2C4C94', '#F4BA3A', '#F4705C', '#3A88E4', '#3CB44E']


def lawn(x0, x1, z0, z1, col=None, zone=','):
    box(x0, x1, GY, GY + 0.04, z0, z1, col or PAL['grass2'])
    ZONES_OCC.append((zone, x0, x1, z0, z1))


def flower_bed(cx, cz, r, seed=0, y=GY + 0.04):
    rnd = random.Random(seed)
    cyl(cx, cz, y, y + 0.55, r, PAL['brick2'], seg=22)
    cyl(cx, cz, y + 0.55, y + 0.65, r - 0.5, PAL['soil'], seg=22)
    cs = [PAL['red'], PAL['yellow'], PAL['pink'], PAL['orange'], PAL['white'], PAL['plum']]
    for k in range(int(r * 3)):
        a = k * 2.399
        rr = (r - 1.0) * math.sqrt((k + 0.5) / (r * 3))
        D.sphere(cx + rr * math.cos(a), y + 1.1, cz + rr * math.sin(a), 0.5, 0.42, 0.5, cs[k % 6], seg=6, rings=4)
    collider(cx - r, cx + r, y, y + 1.4, cz - r, cz + r, 'flowerbed')
    occ('bed', cx - r - 0.5, cx + r + 0.5, cz - r - 0.5, cz + r + 0.5)


def hedge(x0, x1, z0, z1, h=1.6, name='hedge'):
    box(x0, x1, GY, GY + h, z0, z1, PAL['hedge'])
    box(x0 + 0.1, x1 - 0.1, GY + h, GY + h + 0.2, z0 + 0.1, z1 - 0.1, '#34B04A')
    collider(x0, x1, GY, GY + h + 0.2, z0, z1, name)


def pergola(cx, cz, w=12.0, d=8.0, y=SWY):
    for sx in (-1, 1):
        for sz in (-1, 1):
            box(cx + sx * (w / 2 - 0.4) - 0.3, cx + sx * (w / 2 - 0.4) + 0.3, y, y + 8.0, cz + sz * (d / 2 - 0.4) - 0.3, cz + sz * (d / 2 - 0.4) + 0.3, PAL['white'])
    for k in range(9):
        xx = cx - w / 2 + k * w / 8
        box(xx - 0.25, xx + 0.25, y + 8.0, y + 8.4, cz - d / 2 - 0.5, cz + d / 2 + 0.5, PAL['white'])
    for sz in (-1, 1):
        box(cx - w / 2 - 0.4, cx + w / 2 + 0.4, y + 8.4, y + 8.9, cz + sz * (d / 2 - 0.3) - 0.3, cz + sz * (d / 2 - 0.3) + 0.3, PAL['navy'])
    for sx in (-1, 1):
        for sz in (-1, 1):
            collider(cx + sx * (w / 2 - 0.4) - 0.45, cx + sx * (w / 2 - 0.4) + 0.45, y, y + 8.9, cz + sz * (d / 2 - 0.4) - 0.45, cz + sz * (d / 2 - 0.4) + 0.45, 'pergola_post')
    occ('struct', cx - w / 2 - 1, cx + w / 2 + 1, cz - d / 2 - 1, cz + d / 2 + 1)


def kiosk(cx, cz, y=GY):
    """newspaper kiosk without a sign: body, glazed counter, awning, blue flat roof"""
    w, d = 7.0, 5.0
    box(cx - w / 2, cx + w / 2, y, y + 0.4, cz - d / 2, cz + d / 2, PAL['walk3'])
    box(cx - w / 2 + 0.2, cx + w / 2 - 0.2, y + 0.4, y + 7.6, cz - d / 2 + 0.2, cz + d / 2 - 0.2, PAL['teal'])
    box(cx - w / 2 + 0.75, cx + w / 2 - 0.75, y + 3.6, y + 6.55, cz + d / 2 - 0.2, cz + d / 2 - 0.05, PAL['glass'], 'G')
    box(cx - w / 2 + 0.4, cx + w / 2 - 0.4, y + 3.3, y + 3.6, cz + d / 2 - 0.2, cz + d / 2 + 0.7, PAL['white'])
    box(cx - w / 2 + 0.6, cx - w / 2 + 0.9, y + 3.6, y + 6.6, cz + d / 2 - 0.2, cz + d / 2 - 0.0, PAL['white'])
    box(cx + w / 2 - 0.9, cx + w / 2 - 0.6, y + 3.6, y + 6.6, cz + d / 2 - 0.2, cz + d / 2 - 0.0, PAL['white'])
    for k in range(6):
        box(cx - w / 2 + 0.2 + k * (w - 0.4) / 6, cx - w / 2 + 0.2 + (k + 1) * (w - 0.4) / 6, y + 6.8, y + 7.6, cz + d / 2 - 0.2, cz + d / 2 + 2.2, (PAL['coral'], PAL['white'])[k % 2])
    box(cx - w / 2 - 0.3, cx + w / 2 + 0.3, y + 7.6, y + 8.3, cz - d / 2 - 0.3, cz + d / 2 + 0.3, PAL['roof'])
    box(cx - w / 2 - 0.4, cx + w / 2 + 0.4, y + 8.3, y + 8.55, cz - d / 2 - 0.4, cz + d / 2 + 0.4, PAL['white'])
    box(cx - 1.0, cx + 1.0, y + 0.4, y + 6.4, cz - d / 2 + 0.05, cz - d / 2 + 0.2, PAL['door'])
    collider(cx - w / 2 - 0.3, cx + w / 2 + 0.3, y, y + 8.55, cz - d / 2 - 0.3, cz + d / 2 + 2.3, 'kiosk')
    occ('struct', cx - w / 2 - 1, cx + w / 2 + 1, cz - d / 2 - 1, cz + d / 2 + 3)


def playground(cx, cz, w=36.0, d=24.0, y=GY + 0.04, seed=0):
    """sand field with a swing frame, a climbing tower with a slide, a sandbox and a see-saw"""
    box(cx - w / 2, cx + w / 2, y, y + 0.2, cz - d / 2, cz + d / 2, '#E9D9A8')
    box(cx - w / 2 - 0.4, cx + w / 2 + 0.4, y, y + 0.5, cz - d / 2 - 0.4, cz - d / 2, PAL['brick2'])
    box(cx - w / 2 - 0.4, cx + w / 2 + 0.4, y, y + 0.5, cz + d / 2, cz + d / 2 + 0.4, PAL['brick2'])
    box(cx - w / 2 - 0.4, cx - w / 2, y, y + 0.5, cz - d / 2, cz + d / 2, PAL['brick2'])
    box(cx + w / 2, cx + w / 2 + 0.4, y, y + 0.5, cz - d / 2, cz + d / 2, PAL['brick2'])
    ty = y + 0.2
    # swing frame
    sx0, sz0 = cx - w / 2 + 6, cz - d / 2 + 6
    for sx in (-6, 6):
        for sz in (-0.7, 0.7):
            box(sx0 + sx - 0.2, sx0 + sx + 0.2, ty, ty + 8, sz0 + sz * 3 - 0.2, sz0 + sz * 3 + 0.2, PAL['coral'])
    box(sx0 - 6.4, sx0 + 6.4, ty + 8, ty + 8.4, sz0 - 2.3, sz0 - 1.9, PAL['dark'])
    box(sx0 - 6.4, sx0 + 6.4, ty + 8, ty + 8.4, sz0 + 1.9, sz0 + 2.3, PAL['dark'])
    for k in (-3, 3):
        for sz in (-0.1, 0.1):
            box(sx0 + k - 0.04, sx0 + k + 0.04, ty + 2, ty + 8, sz0 - 2 + 2 * 0 + sz, sz0 - 2 + 2 * 0 + sz + 0.08, PAL['metal2'])
        box(sx0 + k - 0.9, sx0 + k + 0.9, ty + 1.8, ty + 2.1, sz0 - 2.4, sz0 - 1.6, PAL['yellow'])
    collider(sx0 - 6.5, sx0 + 6.5, ty, ty + 8.4, sz0 - 2.5, sz0 + 2.5, 'swings')
    # tower with platform, roof and slide
    tx0, tz0 = cx + 3, cz - 4
    for sx in (0, 5):
        for sz in (0, 5):
            box(tx0 + sx - 0.25, tx0 + sx + 0.25, ty, ty + 9, tz0 + sz - 0.25, tz0 + sz + 0.25, PAL['teal'])
    box(tx0 - 0.4, tx0 + 5.4, ty + 4.0, ty + 4.4, tz0 - 0.4, tz0 + 5.4, PAL['wood'])
    box(tx0 - 0.6, tx0 + 5.6, ty + 9.0, ty + 9.5, tz0 - 0.6, tz0 + 5.6, PAL['red'])
    for sx in (0.3, 4.7):
        box(tx0 + sx - 0.1, tx0 + sx + 0.1, ty + 4.4, ty + 6.4, tz0 - 0.1, tz0 + 5.1, PAL['white'])
    D._add('O', [(tx0 + 5.4, ty + 4.0, tz0 + 1), (tx0 + 5.4, ty + 4.0, tz0 + 4), (tx0 + 5.4, ty + 3.7, tz0 + 4), (tx0 + 5.4, ty + 3.7, tz0 + 1),
                 (tx0 + 12.5, ty + 0.4, tz0 + 1), (tx0 + 12.5, ty + 0.4, tz0 + 4), (tx0 + 12.5, ty + 0.1, tz0 + 4), (tx0 + 12.5, ty + 0.1, tz0 + 1)], D._BOXF, PAL['blue'])
    for sz in (0.9, 4.1):
        D._add('O', [(tx0 + 5.4, ty + 4.0, tz0 + sz - 0.1), (tx0 + 5.4, ty + 4.0, tz0 + sz + 0.1), (tx0 + 5.4, ty + 5.0, tz0 + sz + 0.1), (tx0 + 5.4, ty + 5.0, tz0 + sz - 0.1),
                     (tx0 + 12.5, ty + 0.4, tz0 + sz - 0.1), (tx0 + 12.5, ty + 0.4, tz0 + sz + 0.1), (tx0 + 12.5, ty + 1.2, tz0 + sz + 0.1), (tx0 + 12.5, ty + 1.2, tz0 + sz - 0.1)], D._BOXF, PAL['white'])
    # ladder
    for sz in (1.2, 3.8):
        box(tx0 - 0.25 - 1.6, tx0 - 0.25 - 1.45, ty, ty + 4.0, tz0 + sz - 0.15, tz0 + sz + 0.15, PAL['metal2'])
    for k in range(6):
        box(tx0 - 1.9, tx0 - 1.4, ty + 0.5 + k * 0.6, ty + 0.65 + k * 0.6, tz0 + 1.0, tz0 + 4.0, PAL['metal2'])
    collider(tx0 - 2.2, tx0 + 12.6, ty, ty + 9.5, tz0 - 0.7, tz0 + 5.7, 'playtower')
    # sandbox + see-saw
    box(cx - w / 2 + 3, cx - w / 2 + 11, ty, ty + 0.9, cz + d / 2 - 9, cz + d / 2 - 2, PAL['wood'])
    box(cx - w / 2 + 3.3, cx - w / 2 + 10.7, ty + 0.9, ty + 1.0, cz + d / 2 - 8.7, cz + d / 2 - 2.3, '#D9B36A')
    collider(cx - w / 2 + 3, cx - w / 2 + 11, ty, ty + 1.0, cz + d / 2 - 9, cz + d / 2 - 2, 'sandbox')
    wx, wz = cx - 4, cz + 6
    box(wx - 0.3, wx + 0.3, ty, ty + 1.6, wz - 0.8, wz + 0.8, PAL['dark'])
    D._add('O', [(wx - 5, ty + 0.4, wz - 0.7), (wx + 5, ty + 2.6, wz - 0.7), (wx + 5, ty + 2.6, wz + 0.7), (wx - 5, ty + 0.4, wz + 0.7),
                 (wx - 5, ty + 0.9, wz - 0.7), (wx + 5, ty + 3.1, wz - 0.7), (wx + 5, ty + 3.1, wz + 0.7), (wx - 5, ty + 0.9, wz + 0.7)], D._BOXF, PAL['yellow'])
    collider(wx - 5, wx + 5, ty, ty + 3.2, wz - 0.9, wz + 0.9, 'seesaw')
    occ('struct', cx - w / 2 - 2, cx + w / 2 + 2, cz - d / 2 - 2, cz + d / 2 + 2)


def fountain(cx, cz, y=SWY):
    D.lathe(cx, cz, y, [(14, 0), (14, 1.6), (13.2, 1.6), (13.2, 0.4)], PAL['concrete'], seg=40)
    D.lathe(cx, cz, y, [(13.2, 0.4), (13.2, 1.3)], PAL['sky'], seg=40, kind='G')
    cyl(cx, cz, y + 1.2, y + 1.3, 13.2, PAL['sky'], seg=40, kind='G')
    D.lathe(cx, cz, y, [(5.0, 0), (5.0, 1.2), (4.2, 1.2), (3.2, 4.2), (2.4, 4.8), (2.4, 5.1), (0.0, 5.1)], PAL['concrete'], seg=28)
    cyl(cx, cz, y + 4.9, y + 5.0, 3.0, PAL['sky'], seg=24, kind='G')
    D.lathe(cx, cz, y + 5.1, [(1.0, 0), (0.7, 1.6), (1.2, 2.6), (0.5, 3.4), (0.3, 6.2), (0.0, 6.4)], PAL['concrete'], seg=16)
    for k in range(8):
        a = k * math.pi / 4
        D.sphere(cx + 8.5 * math.cos(a), y + 2.2, cz + 8.5 * math.sin(a), 0.4, 1.0, 0.4, PAL['sky'], seg=6, rings=4, kind='G')
    collider(cx - 14, cx + 14, y, y + 7, cz - 14, cz + 14, 'fountain')


# ==================================================================================================================
# the park: x -115..19, z -105..9 (plan y -9..105); fountain at (-48, -48), paths on both axes, playground, flower beds, picnic corner, kiosk (without a sign)
# ==================================================================================================================
PK = (-115.0, 19.0, -105.0, 9.0)
PC = (-48.0, -48.0)
lawn(PK[0], PK[1], PK[2], PK[3])
occ('park', *PK)
paved(PC[0] - 22, PC[0] + 22, PC[1] - 22, PC[1] + 22, name='fountain_plaza', tag='plaza')       # square plaza round the basin
fountain(PC[0], PC[1])
for (x0, x1, z0, z1) in ((PK[0], PC[0] - 22, PC[1] - 4, PC[1] + 4), (PC[0] + 22, PK[1], PC[1] - 4, PC[1] + 4), (PC[0] - 4, PC[0] + 4, PK[2], PC[1] - 22), (PC[0] - 4, PC[0] + 4, PC[1] + 22, PK[3])):
    paved(x0, x1, z0, z1, name='parkpath', tile=8.0)
# plaza ring: benches facing the fountain, lamps at the corners
for (dx, dz, r_) in ((-17, -17, 0), (17, -17, 0), (-17, 17, 180), (17, 17, 180)):
    bench(PC[0] + dx, PC[1] + dz, rot=r_, y=SWY)
for (dx, dz) in ((-20, -20), (20, -20), (-20, 20), (20, 20)):
    street_lamp(PC[0] + dx, PC[1] + dz, facing=math.atan2(-dz, -dx), y=SWY)
for (dx, dz) in ((-9, -17), (9, -17), (-9, 17), (9, 17)):
    planter(PC[0] + dx, PC[1] + dz, 4.0, 4.0, y=SWY, col=PAL['brick2'])
# NW: playground
playground(-86.0, -84.0, w=40.0, d=26.0)
# NE: flower beds and trees
for k, (x, z) in enumerate(((-18, -86), (-2, -86), (-18, -68), (-2, -68))):
    flower_bed(x, z, 5.0, seed=k)
for (x, z) in ((-30, -98), (9, -98), (-18, -60), (9, -60), (-12, -77)):
    tree(x, z, seed=int(x - z), h=10, r=4.8, pit=False)
# SW: pergola with benches, trees
pergola(-80.0, -16.0, 14.0, 8.0)
bench(-80.0, -16.0, rot=0, y=SWY)
for (x, z) in ((-104, -34), (-100, 2), (-58, -12), (-62, 3), (-94, -38)):
    tree(x, z, seed=int(x + z), h=10, r=4.8, pit=False)
for (x, z, r_) in ((-100, -22, 90), (-60, -22, 270)):
    bench(x, z, rot=r_)
for k, (x, z) in enumerate(((-100, -6), (-66, -8))):
    flower_bed(x, z, 4.0, seed=10 + k)
# SE: kiosk (south edge, next to Avenue A), picnic tables, bike racks
kiosk(-30.0, 2.0)
for (x, z) in ((-8.0, -28.0), (-8.0, -14.0)):
    box(x - 3, x + 3, GY + 2.8, GY + 3.1, z - 1.2, z + 1.2, PAL['wood'])
    for sx in (-2, 2):
        box(x + sx - 0.25, x + sx + 0.25, GY, GY + 2.8, z - 1.0, z + 1.0, PAL['dark'])
    for sz in (-1, 1):
        box(x - 3, x + 3, GY + 1.5, GY + 1.75, z + sz * 2.0 - 0.45, z + sz * 2.0 + 0.45, PAL['wood'])
        for sx in (-2, 2):
            box(x + sx - 0.25, x + sx + 0.25, GY, GY + 1.5, z + sz * 2.0 - 0.2, z + sz * 2.0 + 0.2, PAL['dark'])
    collider(x - 3.4, x + 3.4, GY, GY + 3.1, z - 2.6, z + 2.6, 'picnic')
    occ('struct', x - 4, x + 4, z - 3.2, z + 3.2)
for (x, z) in ((-20, -30), (12, -30), (13, -6), (-14, 4)):
    tree(x, z, seed=int(x * 3 - z), h=10, r=4.6, pit=False)
bike_rack(-10, 4, 0)

# ==================================================================================================================
# parking lots (plan P1, P2, P3) with driveways
# ==================================================================================================================
def parking_lot(name, x0, x1, z0, z1, axis, lo, hi, gaps=(), car_prob=0.55, seed=0):
    """axis 'x': bays spaced along x (cars point along z); axis 'z': bays spaced along z (cars point along x).  Pairs of rows: bay 10 + aisle 14 + bay 10."""
    box(x0, x1, GY, ASPH, z0, z1, PAL['asph2'])
    LOTS.append((name, x0, x1, z0, z1))
    occ('lot', x0, x1, z0, z1)
    ZONES_OCC.append(('P', x0, x1, z0, z1))
    a0, a1 = (x0, x1) if axis == 'x' else (z0, z1)
    c0, c1 = (z0, z1) if axis == 'x' else (x0, x1)
    n = max(1, int((c1 - c0 - lo - hi) // 34))
    spare = (c1 - c0 - lo - hi) - n * 34
    rnd = random.Random(seed)
    nb = int((a1 - a0 - 6) // 5.2)
    ci = seed
    for k in range(n):
        base = c0 + lo + spare / 2 + k * 34
        for (rb0, rb1, nose) in ((base, base + 10, 1), (base + 24, base + 34, -1)):
            for j in range(nb + 1):
                u = a0 + 3 + j * 5.2
                if any(g0 - 0.2 <= u <= g1 + 0.2 for (g0, g1) in gaps):
                    continue
                if axis == 'x':
                    box(u - 0.12, u + 0.12, ASPH, ASPH + 0.03, rb0, rb1, PAL['white'])
                else:
                    box(rb0, rb1, ASPH, ASPH + 0.03, u - 0.12, u + 0.12, PAL['white'])
            for j in range(nb):
                u = a0 + 3 + (j + 0.5) * 5.2
                if any(g0 <= u <= g1 for (g0, g1) in gaps):
                    continue
                if rnd.random() > car_prob:
                    continue
                cc = (rb0 + rb1) / 2 + (0.15 if nose > 0 else -0.15)
                ci += 1
                if axis == 'x':
                    car(u, cc, 90 if nose > 0 else 270, CARC[ci % len(CARC)], y=GY + 0.09, seed=ci)
                else:
                    car(cc, u, 0 if nose > 0 else 180, CARC[ci % len(CARC)], y=GY + 0.09, seed=ci)
            # row edge line
            edge = rb0 if nose > 0 else rb1
            if axis == 'x':
                box(a0 + 2.9, a0 + 3 + nb * 5.2 + 0.1, ASPH, ASPH + 0.03, (rb0 - 0.12) if nose > 0 else rb1 - 0.12, (rb0 + 0.12) if nose > 0 else rb1 + 0.12, PAL['white'])
            else:
                box((rb0 - 0.12) if nose > 0 else rb1 - 0.12, (rb0 + 0.12) if nose > 0 else rb1 + 0.12, ASPH, ASPH + 0.03, a0 + 2.9, a0 + 3 + nb * 5.2 + 0.1, PAL['white'])
        # lamps along the aisle
        for j in range(0, nb, 8):
            u = a0 + 3 + (j + 4) * 5.2
            if u > a1 - 3 or any(g0 <= u <= g1 for (g0, g1) in gaps):
                continue
            if axis == 'x':
                street_lamp(u, base + 17.0, facing=0.0, y=ASPH)
            else:
                street_lamp(base + 17.0, u, facing=math.pi / 2, y=ASPH)
    # kerb around the lot edge (not where an apron or lane meets it) and trees in the margins
    return n


# P1: rows along z, entry from Street C on the east edge; P2: rows along x, entry from Avenue A on the south edge; P3: rows along x, entry lane from Avenue B on the west
parking_lot('P1', -245.0, -150.0, 120.0, 245.0, 'z', 13.5, 13.5, gaps=[(172, 192)], seed=3)
parking_lot('P2', 150.0, 240.0, -50.0, 4.0, 'x', 10.0, 10.0, gaps=[(190, 210)], seed=7)
parking_lot('P3', 150.0, 240.0, 150.0, 240.0, 'x', 14.0, 8.0, gaps=[(150, 163)], seed=11)
# aprons / lane (asphalt, same level as the street)
box(-150.0, -138.0, GY, ASPH, 170.0, 194.0, PAL['asphalt'])                         # P1 <-> Street C
box(188.0, 212.0, GY, ASPH, 4.0, 18.0, PAL['asphalt'])                              # P2 <-> Avenue A
box(52.0, 150.0, GY, ASPH, 150.0, 164.0, PAL['asphalt'])                            # lane Avenue B -> P3 (14 wide)
for (x0, x1, z0, z1) in ((-150.0, -138.0, 170.0, 194.0), (188.0, 212.0, 4.0, 18.0), (52.0, 150.0, 150.0, 164.0)):
    occ('street', x0, x1, z0, z1)
    ZONES_OCC.append(('=', x0, x1, z0, z1))
# dashed centre line of the lane
_p = 56.0
while _p + 4 < 148:
    hline(_p, _p + 4, 157.0, 0.2, PAL['white'], ASPH, 0.03)
    _p += 10
# trees and bushes in the lot margins, planter islands at the row ends
for (x, z) in ((-236, 128), (-236, 240), (-160, 128), (-160, 240), (-236, 185), (-160, 150), (-160, 215)):
    tree(x, z, seed=int(x + z), h=9, r=4.2, y=GY + 0.09, pit=False)
for (x, z) in ((158, -44), (232, -44), (158, -1), (232, -1), (196, -46)):
    tree(x, z, seed=int(x + z), h=9, r=4.2, y=GY + 0.09, pit=False)
for (x, z) in ((158, 236), (232, 236), (232, 157), (196, 236)):
    tree(x, z, seed=int(x - z), h=9, r=4.2, y=GY + 0.09, pit=False)

# ==================================================================================================================
# gardens: GARD1 (plan -45..12 x -200..-130) as a courtyard garden with a pergola, GARD2 (plan 135..245 x 205..245) as a playground garden
# ==================================================================================================================
G1 = (-45.0, 12.0, 130.0, 200.0)
lawn(*G1)
occ('park', *G1)
paved(G1[0], -26.0, 160.0, 168.0, name='gardpath', tile=8.0)
paved(-2.0, G1[1], 160.0, 168.0, name='gardpath', tile=8.0)
paved(-18.0, -10.0, G1[2], 152.0, name='gardpath', tile=8.0)
paved(-18.0, -10.0, 176.0, G1[3], name='gardpath', tile=8.0)
paved(-26.0, -2.0, 152.0, 176.0, name='gardplaza', tile=6.0)
pergola(-14.0, 164.0, 12.0, 8.0)
for k, (x, z) in enumerate(((-36, 138), (4, 138), (-36, 192), (4, 192))):
    flower_bed(x, z, 4.5, seed=20 + k)
for (x, z) in ((-38, 150), (6, 150), (-38, 178), (6, 178), (-30, 196), (-2, 196), (-30, 134), (-2, 134)):
    tree(x, z, seed=int(x + z), h=10, r=4.6, pit=False)
for (x, z, r_) in ((-22, 150, 0), (-6, 150, 0), (-22, 178, 180), (-6, 178, 180)):
    bench(x, z, rot=r_, y=SWY)
for (x, z) in ((-28, 152.5), (0, 152.5), (-28, 175.5), (0, 175.5)):
    planter(x, z, 3.2, 3.2, y=SWY, col=PAL['brick2'])
hedge(G1[0] + 1, G1[0] + 2.4, G1[2] + 1, 158.0)
hedge(G1[0] + 1, G1[0] + 2.4, 170.0, G1[3] - 1)
hedge(G1[1] - 2.4, G1[1] - 1, G1[2] + 1, 158.0)
hedge(G1[1] - 2.4, G1[1] - 1, 170.0, G1[3] - 1)

G2 = (135.0, 245.0, -245.0, -205.0)
lawn(*G2)
occ('park', *G2)
playground(167.0, -224.0, w=40.0, d=26.0)
paved(G2[0], G2[1], G2[3] - 6.0, G2[3], name='gardpath', tile=8.0)
for (x, z) in ((210, -240), (225, -240), (238, -240), (214, -212), (232, -214), (141, -240), (141, -222)):
    tree(x, z, seed=int(x + z), h=10, r=4.6, pit=False)
for (x, z, r_) in ((203, -226, 90), (203, -218, 90), (214, -226, 270)):
    bench(x, z, rot=r_)
for k, (x, z) in enumerate(((222, -226), (236, -226))):
    flower_bed(x, z, 4.2, seed=40 + k)
bike_rack(176, -209, 0, y=SWY)
