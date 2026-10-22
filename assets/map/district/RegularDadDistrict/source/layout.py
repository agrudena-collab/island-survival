# Layout of the district: executed by build_district.py after the helpers are defined.
# 440 x 440, two crossing streets (asphalt 24, sidewalks 9 each side), four blocks:
#   NW mistress tower + neighbours + garden   NE hardware store, workshop, cafe
#   SW Gym + cafe                             SE park with fountain, bakery, florist
SZ = 220                     # half size
RW = 12                      # half asphalt width
SW = 21                      # half street width including sidewalks (asphalt 12 + 9)


def front_sign(text, x, z_face, w, ground_h, face, col, sh=2.8):
    """Shop board in the band between the awnings (top ~GY+ground_h-1.1) and the first-floor windows (sills ~GY+ground_h+1.1): never over a window."""
    y0 = GY + ground_h - 0.9
    sgn = 1 if face == 'S' else -1
    box(x - w / 2, x + w / 2, y0, y0 + sh, min(z_face, z_face + sgn * 1.0), max(z_face, z_face + sgn * 1.0), col)
    box(x - w / 2 - 0.3, x + w / 2 + 0.3, y0 - 0.2, y0, min(z_face, z_face + sgn * 1.2), max(z_face, z_face + sgn * 1.2), PAL['white'])
    box(x - w / 2 - 0.3, x + w / 2 + 0.3, y0 + sh, y0 + sh + 0.2, min(z_face, z_face + sgn * 1.2), max(z_face, z_face + sgn * 1.2), PAL['white'])
    SIGNS.append((text, x, y0 + sh / 2, z_face + sgn * 0.1, w - 1.5, sh - 0.7, face))     # (studio_setup moves the text 0.9 out: onto the board face)


def hline(x0, x1, z, w, col, y0=GY, h=0.06):
    box(x0, x1, y0, y0 + h, z - w / 2, z + w / 2, col)


def vline(z0, z1, x, w, col, y0=GY, h=0.06):
    box(x - w / 2, x + w / 2, y0, y0 + h, z0, z1, col)


ZONES_OCC += [('-', -SZ - 30, SZ + 30, -21, 21), ('-', -21, 21, -SZ - 30, SZ + 30), ('-', -226, -21, -158, -132), ('-', 21, 226, -158, -132), ('-', -226, -21, 132, 158),
              (',', 28, 212, 28, 212)]    # sidewalks, service-street sidewalks, park (the park only counts where nothing is built)
# ---- ground, roads, sidewalks ---------------------------------------------------------------------------------
box(-SZ - 6, SZ + 6, 0, GY, -SZ - 6, SZ + 6, PAL['grass'])
collider(-SZ - 6, SZ + 6, -4, GY, -SZ - 6, SZ + 6, 'ground')
box(-SZ - 6, SZ + 6, GY, GY + 0.1, -RW, RW, PAL['asphalt'])                 # east-west road
box(-RW, RW, GY, GY + 0.1, -SZ - 6, SZ + 6, PAL['asphalt'])                 # north-south road
box(-SZ - 6, SZ + 6, GY, GY + 0.12, -RW, RW, PAL['asphalt'])
for sgn in (-1, 1):
    # sidewalks along the E-W road (leave the crossing open)
    for (x0, x1) in ((-SZ - 6, -SW), (SW, SZ + 6)):
        z0, z1 = (RW, SW) if sgn > 0 else (-SW, -RW)
        box(x0, x1, GY, GY + 0.55, z0, z1, PAL['walk'])
        cz = z0 if sgn > 0 else z1
        box(x0, x1, GY, GY + 0.62, (z0 - 0.5) if sgn > 0 else (z1 - 0.5), (z0 + 0.5) if sgn > 0 else (z1 + 0.5), PAL['curb'])
    # along the N-S road
    for (z0, z1) in ((-SZ - 6, -SW), (SW, SZ + 6)):
        x0, x1 = (RW, SW) if sgn > 0 else (-SW, -RW)
        box(x0, x1, GY, GY + 0.55, z0, z1, PAL['walk'])
        box((x0 - 0.5) if sgn > 0 else (x1 - 0.5), (x0 + 0.5) if sgn > 0 else (x1 + 0.5), GY, GY + 0.62, z0, z1, PAL['curb'])
# corner pads and curb returns at the crossing
for sx in (-1, 1):
    for sz in (-1, 1):
        x0, x1 = (RW, SW) if sx > 0 else (-SW, -RW)
        z0, z1 = (RW, SW) if sz > 0 else (-SW, -RW)
        box(x0, x1, GY, GY + 0.55, z0, z1, PAL['walk'])
        box(x0, x1, GY, GY + 0.62, z0 - 0.5 if sz > 0 else z1 - 0.5, z0 + 0.5 if sz > 0 else z1 + 0.5, PAL['curb'])
        box(x0 - 0.5 if sx > 0 else x1 - 0.5, x0 + 0.5 if sx > 0 else x1 + 0.5, GY, GY + 0.62, z0, z1, PAL['curb'])
        # tactile pad of the kerb ramp
        for k in range(6):
            box(x0 + 1 + k * 1.2 if sx > 0 else x1 - 1 - k * 1.2 - 0.9, (x0 + 1.9 + k * 1.2) if sx > 0 else x1 - 1 - k * 1.2, GY + 0.55, GY + 0.62, z0 + 1 if sz > 0 else z1 - 2, z0 + 3 if sz > 0 else z1 - 1, PAL['yellow'])

# paving joints on the sidewalks
for k in range(-SZ // 8, SZ // 8 + 1):
    p = k * 8.0
    for (zz0, zz1) in ((RW + 0.6, SW - 0.2), (-SW + 0.2, -RW - 0.6)):
        if abs(p) > SW:
            box(p - 0.05, p + 0.05, GY + 0.55, GY + 0.57, zz0, zz1, PAL['walk2'])
    for (xx0, xx1) in ((RW + 0.6, SW - 0.2), (-SW + 0.2, -RW - 0.6)):
        if abs(p) > SW:
            box(xx0, xx1, GY + 0.55, GY + 0.57, p - 0.05, p + 0.05, PAL['walk2'])

# ---- road markings ----------------------------------------------------------------------------------------------
for sgn in (-1, 1):
    # double yellow centre lines
    for off in (-0.3, 0.3):
        for (a, b) in ((SW + 14, SZ + 28), (-SZ - 28, -SW - 14)):
            hline(a, b, off, 0.22, PAL['lane'], GY + 0.12)
            vline(a, b, off, 0.22, PAL['lane'], GY + 0.12)
    break
for k in range(int(SZ / 10)):
    for sgn in (-1, 1):
        for (xx) in (sgn * (SW + 16 + k * 10),):
            pass
# parking bay ticks along both kerbs
for sg in (-1, 1):
    for k in range(-22, 23):
        p = k * 10.0 + 5
        if abs(p) > SW + 4:
            box(p - 0.1, p + 0.1, GY + 0.12, GY + 0.18, sg * (RW - 5.5), sg * (RW - 0.2), PAL['white'])
            box(sg * (RW - 5.5), sg * (RW - 0.2), GY + 0.12, GY + 0.18, p - 0.1, p + 0.1, PAL['white'])
# crosswalks and stop lines
for sgn in (-1, 1):
    for k in range(10):
        o = -RW + 1.6 + k * 2.2
        box(o - 0.55, o + 0.55, GY + 0.12, GY + 0.19, sgn * (RW + 2.2) - 1.8 if sgn < 0 else sgn * (RW + 2.2) - 1.8, sgn * (RW + 2.2) + 1.8, PAL['white'])
        box(sgn * (RW + 2.2) - 1.8, sgn * (RW + 2.2) + 1.8, GY + 0.12, GY + 0.19, o - 0.55, o + 0.55, PAL['white'])
    box(sgn * (RW + 4.6) - 0.3, sgn * (RW + 4.6) + 0.3, GY + 0.12, GY + 0.19, 0 if sgn < 0 else -RW, RW if sgn < 0 else 0, PAL['white'])
    box(-RW if sgn < 0 else 0, 0 if sgn < 0 else RW, GY + 0.12, GY + 0.19, sgn * (RW + 4.6) - 0.3, sgn * (RW + 4.6) + 0.3, PAL['white'])
# manholes, drains
for (x, z) in ((-60, 5), (60, -5), (5, -90), (-5, 100), (-140, -4), (150, 4), (4, 160), (-4, -150)):
    cyl(x, z, GY + 0.12, GY + 0.2, 1.25, PAL['dark'], seg=18)
    for k in range(5):
        box(x - 1.0, x + 1.0, GY + 0.2, GY + 0.24, z - 0.9 + k * 0.45, z - 0.75 + k * 0.45, PAL['asph2'])
for (x, z) in ((-90, RW - 0.3), (110, -RW + 0.3), (RW - 0.3, 70), (-RW + 0.3, -120), (-170, -RW + 0.3), (170, RW - 0.3)):
    box(x - 1.4, x + 1.4, GY + 0.1, GY + 0.16, z - 0.35, z + 0.35, PAL['dark'])

# ---- street furniture along the sidewalks --------------------------------------------------------------------
def along(axis, sign, start, stop, step, fn):
    p = start
    i = 0
    while p <= stop:
        if not (axis == 'z' and (abs(p + 145) < 14 or abs(p - 145) < 14)):      # nothing at the mouths of the service streets
            fn(p, i)
        p += step
        i += 1


for sg in (-1, 1):
    zc = sg * (SW - 1.8)
    for (a, b) in ((-SZ + 10, -SW - 12), (SW + 12, SZ - 10)):
        along('x', sg, a, b, 38, lambda p, i, zc=zc, sg=sg: street_lamp(p, zc, facing=(math.pi / 2) * (1 if sg < 0 else -1)))
        along('x', sg, a + 19, b, 38, lambda p, i, zc=zc, sg=sg: (tree(p, zc, seed=i, h=9 + (i % 3)), None))
        along('x', sg, a + 9, b, 76, lambda p, i, zc=zc, sg=sg: (bench(p, zc + (-1.0 if sg > 0 else 1.0), rot=0 if sg > 0 else 180), None))
        along('x', sg, a + 28, b, 76, lambda p, i, zc=zc, sg=sg: (trash_bin(p, zc), None))
    xc = sg * (SW - 1.8)
    for (a, b) in ((-SZ + 10, -SW - 12), (SW + 12, SZ - 10)):
        along('z', sg, a, b, 38, lambda p, i, xc=xc, sg=sg: street_lamp(xc, p, facing=(math.pi) * (1 if sg < 0 else 0)))
        along('z', sg, a + 19, b, 38, lambda p, i, xc=xc, sg=sg: (tree(xc, p, seed=i + 5, h=9 + (i % 3)), None))
        along('z', sg, a + 9, b, 76, lambda p, i, xc=xc, sg=sg: (bench(xc + (-1.0 if sg > 0 else 1.0), p, rot=90), None))
for (x, z) in ((SW + 14, RW + 4), (-SW - 14, -RW - 4), (RW + 4, -SW - 14), (-RW - 4, SW + 14)):
    hydrant(x, z)
for (x, z) in ((SW + 3, SW - 2), (-SW - 3, -SW + 2), (SW - 2, -SW - 3), (-SW + 2, SW + 3)):
    mailbox(x, z)
for sx in (-1, 1):
    for sz in (-1, 1):
        for k in range(5):
            bollard(sx * (RW + 1.5 + k * 0.0), sz * (RW + 1.5 + 0.0) + sz * 0.0 + (k - 2) * 0.0 + 0, GY + 0.0)
            break
traffic_light(RW + 2.5, RW + 2.5, (-1, 0))
traffic_light(-RW - 2.5, -RW - 2.5, (1, 0))
traffic_light(-RW - 2.5, RW + 2.5, (0, -1))
traffic_light(RW + 2.5, -RW - 2.5, (0, 1))
# bus stop on the south sidewalk of the E-W road, east of the crossing
bx, bz = 100, RW + 4.5
box(bx - 4.5, bx + 4.5, GY + 0.55, GY + 0.62, bz - 1.8, bz + 1.8, PAL['walk2'])
for sx in (-4.2, 4.2):
    box(bx + sx - 0.12, bx + sx + 0.12, GY + 0.62, GY + 8.5, bz - 1.6, bz - 1.4, PAL['dark'])
    box(bx + sx - 0.12, bx + sx + 0.12, GY + 0.62, GY + 8.5, bz + 1.4, bz + 1.6, PAL['dark'])
box(bx - 4.8, bx + 4.8, GY + 8.5, GY + 9.2, bz - 2.2, bz + 2.2, PAL['teal'])
box(bx - 4.5, bx + 4.5, GY + 9.2, GY + 9.5, bz - 1.9, bz + 1.9, PAL['white'])
box(bx - 4.1, bx + 4.1, GY + 2.8, GY + 8.3, bz + 1.5, bz + 1.6, PAL['glass'], 'G')
box(bx - 4.1, bx - 4.0, GY + 2.8, GY + 8.3, bz - 1.6, bz + 1.5, PAL['glass'], 'G')
bench(bx, bz + 0.6, rot=180, col=False)
box(bx - 0.1, bx + 0.1, GY + 0.62, GY + 12.5, bz - 2.8, bz - 2.6, PAL['dark'])
box(bx - 1.6, bx + 1.6, GY + 10.0, GY + 12.5, bz - 2.9, bz - 2.55, PAL['blue'])
SIGNS.append(('BUS', bx, GY + 11.3, bz - 2.9, 3.0, 2.2, 'S'))
collider(bx - 4.8, bx + 4.8, GY, GY + 9.5, bz - 2.2, bz + 2.2, 'busstop')

# ---- cars parked along the kerbs ----------------------------------------------------------------------------
CARC = [PAL['red'], PAL['blue'], PAL['yellow'], PAL['teal'], PAL['orange'], PAL['white'], PAL['plum'], PAL['green']]
ci = 0
for (xs, zs, rot) in ((-170, RW - 3.2, 0), (-95, RW - 3.2, 0), (-35, RW - 3.2, 0), (95, RW - 3.2, 180), (160, RW - 3.2, 180), (-150, -RW + 3.2, 180),
                      (-70, -RW + 3.2, 180), (130, -RW + 3.2, 0), (190, -RW + 3.2, 0), (RW - 3.2, -140, 90), (-RW + 3.2, -90, 270), (RW - 3.2, 110, 90), (-RW + 3.2, 150, 270),
                      (20, 6, 0)):
    if (xs, zs) == (20, 6):
        continue
    ci += 1      # (no cars on the streets: they stand only in the parking lots)

# ==================================================================================================================
# BLOCK NW: the mistress' tower (10 storeys), neighbours, garden
# ==================================================================================================================
TOWER = R(-120, -80, -92, -62)
H_T = building(TOWER, 10, PAL['cream'], PAL['white'], fh=11, front='S', ground_h=14, balconies=True, shutters=PAL['blue'], entrance_u=20, name='tower', seed=11,
               storefronts=[(2.5, 14, (PAL['red'], PAL['white'])), (26, 37.5, (PAL['red'], PAL['white']))])
front_sign('APARTMENTS', -100, -62, 22, 14, 'S', PAL['red'])
anchor('tower_entrance', -100, GY + 0.55, -62 + 3.4, 0, 1)
anchor('tower_exit_arrival', -95, GY + 0.55, -62 + 9.0, 0, 1)    # not on the axis: the flagpole stands there
# neighbours
N1 = R(-198, -150, -88, -62)
building(N1, 6, PAL['brick'], PAL['white'], fh=11, front='S', ground_h=13, shutters=PAL['green'], entrance_u=24, name='block_w', seed=3, tank=False)
N2 = R(-62, -26, -88, -62)
building(N2, 5, '#F2C078', PAL['white'], fh=11, front='S', ground_h=13, shutters=PAL['teal'], entrance_u=18, name='block_e', seed=5, tank=False,
         storefronts=[(2, 10, (PAL['green'], PAL['white'])), (24, 32, (PAL['green'], PAL['white']))])
# garden in front of the tower: lawn, paved plaza, planters, fountain-less sitting area, lamps
box(-148, -30, GY, GY + 0.04, -61.5, -22, PAL['grass'])
box(-134, -66, GY, GY + 0.3, -61.5, -38, PAL['walk'])                      # plaza
box(-110, -90, GY + 0.3, GY + 0.34, -61.5, -22, PAL['walk2'])             # path to the street
for x in range(-134, -66, 4):
    box(x, x + 0.08, GY + 0.3, GY + 0.33, -61.5, -38, PAL['walk2'])
for z in range(-61, -38, 4):
    box(-134, -66, GY + 0.3, GY + 0.33, z, z + 0.08, PAL['walk2'])
for (x, z) in ((-128, -56), (-72, -56), (-128, -44), (-72, -44)):
    box(x - 2.2, x + 2.2, GY + 0.3, GY + 1.8, z - 2.2, z + 2.2, PAL['brick2'])
    box(x - 2.0, x + 2.0, GY + 1.8, GY + 2.0, z - 2.0, z + 2.0, PAL['soil'])
    for k in range(7):
        a = k * 0.9
        D.sphere(x + 1.1 * math.cos(a), GY + 2.6, z + 1.1 * math.sin(a), 0.9, 0.8, 0.9, [PAL['red'], PAL['yellow'], PAL['pink'], PAL['orange']][k % 4], seg=7, rings=5)
    D.sphere(x, GY + 2.5, z, 1.2, 0.9, 1.2, PAL['green'], seg=8, rings=5)
    collider(x - 2.2, x + 2.2, GY, GY + 2.6, z - 2.2, z + 2.2, 'planter')
for (x, z, r) in ((-118, -40, 0), (-82, -40, 0), (-100, -50, 180)):
    bench(x, z, rot=r)
for (x, z) in ((-140, -48), (-60, -48), (-100, -30)):
    street_lamp(x, z, facing=0.7)
for (x, z) in ((-142, -30), (-58, -34), (-150, -52), (-48, -52), (-137, -57), (-68, -70)):
    tree(x, z, seed=int(x + z), h=10, r=4.8, pit=False)     # (no pits: several stand on paving, a pit slab would z-fight with it)
# flag pole with a flag
box(-78.15, -77.85, GY + 0.3, GY + 21, -48.15, -47.85, PAL['metal'])           # (moved off the tower axis: the flag no longer hangs in front of the windows)
box(-77.85, -70.5, GY + 17, GY + 20.5, -48.05, -47.95, PAL['red'])
box(-77.85, -70.5, GY + 18.2, GY + 19.0, -48.0, -47.9, PAL['white'])
collider(-78.5, -77.5, GY, GY + 21, -48.5, -47.5, 'flagpole')
# (the back of the block is built after the service streets, at the end of this file)

# ==================================================================================================================
# BLOCK NE: hardware store, workshop, cafe
# ==================================================================================================================
HW = R(40, 98, -90, -52)
building(HW, 2, '#F2D16B', PAL['white'], fh=11, front='S', ground_h=14, win_w=4.2, name='hardware', seed=21, tank=False,
         storefronts=[(2.5, 22, (PAL['red'], PAL['white'])), (34, 55, (PAL['red'], PAL['white']))], entrance_u=28)
front_sign('HARDWARE', 69, -52, 28, 14, 'S', PAL['red'])
anchor('bag_shop', 69, GY + 0.55, -52 + 5.0, 0, 1)
WS = R(110, 160, -90, -52)
building(WS, 2, PAL['concrete'], PAL['white'], fh=11, front='S', ground_h=14, name='workshop', seed=23, tank=False)
for k in range(3):
    ux = 6 + k * 14
    lb('S', WS, ux, ux + 11, GY + 0.1, GY + 10.4, -0.3, 0.8, PAL['white'])
    for r_ in range(12):
        lb('S', WS, ux + 0.4, ux + 10.6, GY + 0.2 + r_ * 0.85, GY + 0.2 + r_ * 0.85 + 0.7, 0.8, 1.1, PAL['gray'])
    lb('S', WS, ux + 0.4, ux + 10.6, GY + 10.2, GY + 10.7, 0.8, 1.4, PAL['dark'])
front_sign('WORKSHOP', 135, -52, 28, 14, 'S', PAL['teal'])
anchor('ladder_giver', 135, GY + 0.55, -52 + 6.0, 0, 1)
# ladders leaning on the workshop wall, wheelbarrow, paint cans, crates in front of the stores
for k in range(3):
    xx = 112 + k * 5.5
    for s in (-0.55, 0.55):
        box(xx + s - 0.1, xx + s + 0.1, GY + 0.55, GY + 11, -52 + 0.4 - 0.0, -52 + 0.5 + 3.0, PAL['red']) if False else None
    for s in (-0.6, 0.6):
        D._add('O', [(xx + s - 0.1, GY + 0.55, -50.5), (xx + s + 0.1, GY + 0.55, -50.5), (xx + s + 0.1, GY + 0.55, -50.5 - 0.0), (xx + s - 0.1, GY + 0.55, -50.5),
                     (xx + s - 0.1, GY + 14, -51.7), (xx + s + 0.1, GY + 14, -51.7), (xx + s + 0.1, GY + 14, -51.5), (xx + s - 0.1, GY + 14, -51.5)], D._BOXF, PAL['orange'])
    for r_ in range(10):
        yy = GY + 1.6 + r_ * 1.25
        zz = -50.5 - (yy - GY) * 1.2 / 14
        box(xx - 0.6, xx + 0.6, yy, yy + 0.14, zz - 0.1, zz + 0.1, PAL['wood'])
for k in range(5):
    cyl(50 + k * 2.2, -47, GY + 0.55, GY + 1.5, 0.8, [PAL['red'], PAL['blue'], PAL['green'], PAL['yellow'], PAL['orange']][k], seg=12)
    cyl(50 + k * 2.2, -47, GY + 1.5, GY + 1.6, 0.6, PAL['metal'], seg=12)
for k in range(4):
    box(84 + (k % 2) * 3.2, 86.8 + (k % 2) * 3.2, GY + 0.55 + (k // 2) * 2.0, GY + 2.5 + (k // 2) * 2.0, -48 - 0.0, -45.5, PAL['wood'])
# wheelbarrow
box(90, 95, GY + 1.6, GY + 2.6, -47.8, -45.6, PAL['red'])
cyl(95.8, -46.7, GY + 0.55, GY + 1.55, 0.0, PAL['dark'], seg=3) if False else None
wheel(95.4, GY + 1.5, -46.7, 0)
CAFE = R(168, 214, -88, -56)
building(CAFE, 3, PAL['pink'], PAL['white'], fh=11, front='S', ground_h=13, shutters=PAL['teal'], name='cafe_n', seed=29, tank=False,
         storefronts=[(2.5, 20, (PAL['teal'], PAL['white'])), (26, 43, (PAL['teal'], PAL['white']))], entrance_u=23)
front_sign('CAFE', 191, -56, 16, 13, 'S', PAL['teal'])
for k in range(4):
    x = 176 + k * 9
    cyl(x, -50, GY + 0.55, GY + 3.2, 0.12, PAL['dark'], seg=8)
    cyl(x, -50, GY + 3.2, GY + 3.35, 2.1, PAL['white'], seg=18)
    D.lathe(x, -50, GY + 3.35, [(2.2, 0), (2.0, 0.5), (0.0, 1.1)], [PAL['teal'], PAL['red']][k % 2], seg=18)
    for s in (-1, 1):
        box(x + s * 2.0 - 0.45, x + s * 2.0 + 0.45, GY + 0.55, GY + 2.5, -50.6, -49.4, PAL['wood2'])
    collider(x - 2.4, x + 2.4, GY, GY + 4.5, -52.4, -47.6, 'cafe_table')
# parking lot behind the stores, a row of trees, fences
box(40, 214, GY, GY + 0.08, -128, -98, PAL['asph2'])
for k in range(14):
    box(46 + k * 12, 46.2 + k * 12, GY + 0.08, GY + 0.14, -126, -102, PAL['white'])
for k in range(6):
    car(52 + k * 24, -114, 90, CARC[(k + 2) % 8], seed=k)

# ==================================================================================================================
# BLOCK SW: Gym and cafe
# ==================================================================================================================
GYM = R(-190, -120, 50, 94)
building(GYM, 2, PAL['navy'], PAL['white'], fh=12, front='N', ground_h=16, win_w=6.0, win_h=6.0, name='gym', seed=31, tank=False)
lb('N', GYM, 3, 67, GY + 2.0, GY + 13.5, 0.0, 0.14, PAL['glass'], 'G')
for k in range(0, 65, 8):
    lb('N', GYM, 3 + k, 3.5 + k, GY + 2.0, GY + 13.5, 0.0, 0.7, PAL['white'])
lb('N', GYM, 3, 67, GY + 6.6, GY + 7.0, 0.0, 0.7, PAL['white'])
door('N', GYM, 35, GY, w=7.0, h=9.0, col=PAL['red'], frame=PAL['white'])
front_sign('GYM', -155, 50, 26, 16, 'N', PAL['red'], sh=3.6)
anchor('gym_door', -155, GY + 0.55, 50 - 5.0, 0, -1)
CAFE2 = R(-84, -38, 50, 82)
building(CAFE2, 3, PAL['teal'], PAL['white'], fh=11, front='N', ground_h=13, shutters=PAL['yellow'], name='cafe_s', seed=33, tank=False,
         storefronts=[(2.5, 20, (PAL['yellow'], PAL['white'])), (26, 43, (PAL['yellow'], PAL['white']))], entrance_u=23)
front_sign('PIZZA', -61, 50, 16, 13, 'N', PAL['red'])
# bike racks and a fountain-less plaza in front of the gym
for k in range(6):
    xx = -176 + k * 7
    for s in range(4):
        D.lathe(xx + s * 1.0, 40, GY + 0.55, [(0.1, 0), (0.1, 2.0)], PAL['metal'], seg=6)
    box(xx - 0.1, xx + 3.1, GY + 2.4, GY + 2.55, 39.9, 40.1, PAL['metal'])
box(-190, -120, GY, GY + 0.3, 22, 50, PAL['walk'])
for k in range(10):
    box(-190, -120, GY + 0.3, GY + 0.33, 24 + k * 2.8, 24.08 + k * 2.8, PAL['walk2'])
for (x, z) in ((-140, 36), (-170, 36)):
    street_lamp(x, z, facing=1.57)
ZONES_OCC.append(('p', -190, -120, 22, 50))
ZONES_OCC.append(('p', -134, -66, -61.5, -38))

# ==================================================================================================================
# BLOCK SE: park with fountain, bakery, florist
# ==================================================================================================================
box(28, 212, GY, GY + 0.05, 28, 212, PAL['grass2'])
PARK_C = (120, 122)
# paths: cross + ring around the fountain
box(112, 128, GY, GY + 0.12, 28, 212, PAL['walk'])
box(28, 212, GY, GY + 0.12, 114, 130, PAL['walk'])
cyl(PARK_C[0], PARK_C[1], GY + 0.0, GY + 0.14, 24, PAL['walk'], seg=48)
for k in range(24):
    a = k * math.pi / 12
    box(PARK_C[0] + 24 * math.cos(a) - 0.5, PARK_C[0] + 24 * math.cos(a) + 0.5, GY + 0.14, GY + 0.2, PARK_C[1] + 24 * math.sin(a) - 0.5, PARK_C[1] + 24 * math.sin(a) + 0.5, PAL['walk2'])
# fountain: stepped basin, water ring, tiers, statue-like spout
D.lathe(PARK_C[0], PARK_C[1], GY + 0.14, [(14, 0), (14, 1.6), (13.2, 1.6), (13.2, 0.4)], PAL['concrete'], seg=40)
D.lathe(PARK_C[0], PARK_C[1], GY + 0.14, [(13.2, 0.4), (13.2, 1.3)], PAL['sky'], seg=40, kind='G')
cyl(PARK_C[0], PARK_C[1], GY + 1.2, GY + 1.3, 13.2, PAL['sky'], seg=40, kind='G')
D.lathe(PARK_C[0], PARK_C[1], GY + 0.14, [(5.0, 0), (5.0, 1.2), (4.2, 1.2), (3.2, 4.2), (2.4, 4.8), (2.4, 5.1), (0.0, 5.1)], PAL['concrete'], seg=32)
cyl(PARK_C[0], PARK_C[1], GY + 4.9, GY + 5.0, 3.0, PAL['sky'], seg=28, kind='G')
D.lathe(PARK_C[0], PARK_C[1], GY + 5.1, [(1.0, 0), (0.7, 1.6), (1.2, 2.6), (0.5, 3.4), (0.3, 6.2), (0.0, 6.4)], PAL['concrete'], seg=20)
for k in range(8):
    a = k * math.pi / 4
    D.sphere(PARK_C[0] + 8.5 * math.cos(a), GY + 2.2, PARK_C[1] + 8.5 * math.sin(a), 0.4, 1.0, 0.4, PAL['sky'], seg=6, rings=4, kind='G')
collider(PARK_C[0] - 14, PARK_C[0] + 14, GY, GY + 7, PARK_C[1] - 14, PARK_C[1] + 14, 'fountain')
# benches and lamps around the ring, flower beds in the lawn quadrants
for k in range(8):
    a = k * math.pi / 4 + math.pi / 8
    bench(PARK_C[0] + 19 * math.cos(a), PARK_C[1] + 19 * math.sin(a), rot=-math.degrees(a) + 90)
for k in range(8):
    a = k * math.pi / 4
    street_lamp(PARK_C[0] + 27 * math.cos(a), PARK_C[1] + 27 * math.sin(a), facing=a + 3.14)
for (qx, qz) in ((72, 72), (170, 72), (72, 170), (188, 150)):
    for k in range(40):
        a = k * 2.399
        rr = 2.0 + (k % 7) * 1.6
        D.sphere(qx + rr * math.cos(a), GY + 0.4, qz + rr * math.sin(a), 0.55, 0.45, 0.55, [PAL['red'], PAL['yellow'], PAL['pink'], PAL['orange'], PAL['white'], PAL['plum']][k % 6], seg=6, rings=4)
    cyl(qx, qz, GY, GY + 0.45, 11, PAL['soil'], seg=30)
    cyl(qx, qz, GY + 0.45, GY + 0.5, 11, PAL['grass'], seg=30) if False else None
    for k in range(10):
        tx_, tz_ = qx + 17 * math.cos(k * 0.63), qz + 17 * math.sin(k * 0.63)
        if k % 3 == 0 and tz_ > 70 and tx_ < 200:       # (the northern bakery/florist strip and the east path are not planted)
            tree(tx_, tz_, seed=k + qx, h=10 + (k % 3), r=4.6, pit=False)
# playground in the south-east corner
PG = (172, 190)
box(PG[0] - 18, PG[0] + 18, GY, GY + 0.2, PG[1] - 12, PG[1] + 12, '#E9D9A8')
box(PG[0] - 8, PG[0] - 6, GY + 0.2, GY + 9, PG[1] - 6, PG[1] - 4.4, PAL['red'])
box(PG[0] - 8, PG[0] - 6, GY + 0.2, GY + 9, PG[1] - 1.6, PG[1] + 0.0, PAL['red'])
box(PG[0] - 8.3, PG[0] + 8, GY + 8.6, GY + 9.2, PG[1] - 6, PG[1] - 4.4, PAL['dark'])
box(PG[0] - 8.3, PG[0] + 8, GY + 8.6, GY + 9.2, PG[1] - 1.6, PG[1], PAL['dark'])
for k in range(2):
    for s in (-1, 1):
        px = PG[0] + (-5 if k == 0 else 4)
        box(px - 0.05, px + 0.05, GY + 1.8, GY + 8.6, PG[1] - 5.2 + s * 2.2 + 0.0, PG[1] - 5.1 + s * 2.2, PAL['metal'])
    box(px - 1.1, px + 1.1, GY + 1.6, GY + 1.9, PG[1] - 7.7, PG[1] - 2.7, [PAL['yellow'], PAL['teal']][k])
for k in range(10):
    box(PG[0] - 6 + k * 1.5, PG[0] - 5.2 + k * 1.5, GY + 0.2, GY + 7 - k * 0.55, PG[1] + 4, PG[1] + 8, PAL['blue']) if False else None
slope_pts = [(PG[0] + 6, PG[1] + 4), (PG[0] + 12, PG[1] + 4), (PG[0] + 12, PG[1] + 8), (PG[0] + 6, PG[1] + 8)]
D.slope(PG[0] + 6, PG[0] + 12, GY + 0.4, GY + 6.5, PG[1] + 4, PG[1] + 8, PAL['blue'], axis='x') if False else None
D._add('O', [(PG[0] + 6, GY + 0.2, PG[1] + 4), (PG[0] + 14, GY + 0.2, PG[1] + 4), (PG[0] + 14, GY + 0.2, PG[1] + 8), (PG[0] + 6, GY + 0.2, PG[1] + 8),
             (PG[0] + 6, GY + 6.5, PG[1] + 4), (PG[0] + 14, GY + 0.6, PG[1] + 4), (PG[0] + 14, GY + 0.6, PG[1] + 8), (PG[0] + 6, GY + 6.5, PG[1] + 8)], D._BOXF, PAL['blue'])
box(PG[0] + 14, PG[0] + 14.3, GY + 0.6, GY + 1.6, PG[1] + 4, PG[1] + 8, PAL['blue'])
box(PG[0] - 14, PG[0] - 9, GY + 0.2, GY + 1.0, PG[1] + 5, PG[1] + 10, '#D9B36A')        # sandbox
box(PG[0] - 14, PG[0] - 9, GY + 1.0, GY + 1.15, PG[1] + 5, PG[1] + 10, '#E6CC8A')
for s in (-1, 1):
    box(PG[0] + 0 - 0.3, PG[0] + 0.3, GY + 0.2, GY + 1.5, PG[1] + 6 + s * 0.0 - 0.1, PG[1] + 6.1, PAL['dark']) if False else None
box(PG[0] - 3, PG[0] + 3, GY + 1.0, GY + 1.25, PG[1] + 6.5, PG[1] + 7.3, PAL['yellow'])
box(PG[0] - 0.4, PG[0] + 0.4, GY + 0.2, GY + 1.2, PG[1] + 6.3, PG[1] + 7.5, PAL['dark'])
collider(PG[0] - 18, PG[0] + 18, GY, GY + 9, PG[1] - 12, PG[1] + 12, 'playground')
# bakery and florist on the north edge of the park block (fronts to the E-W road)
BAK = R(36, 84, 36, 62)
building(BAK, 2, PAL['orange'], PAL['white'], fh=11, front='N', ground_h=13, shutters=PAL['red'], name='bakery', seed=41, tank=False,
         storefronts=[(2.5, 20, (PAL['red'], PAL['white'])), (26, 44, (PAL['red'], PAL['white']))], entrance_u=23)
front_sign('BAKERY', 60, 36, 18, 13, 'N', PAL['red'])
FLO = R(140, 186, 36, 62)
building(FLO, 2, PAL['green'], PAL['white'], fh=11, front='N', ground_h=13, shutters=PAL['pink'], name='florist', seed=43, tank=False,
         storefronts=[(2.5, 18, (PAL['pink'], PAL['white'])), (26, 43, (PAL['pink'], PAL['white']))], entrance_u=22)
front_sign('FLOWERS', 163, 36, 18, 13, 'N', PAL['pink'])
# ==================================================================================================================
# plazas in front of the stores, service streets and the second row of buildings
# ==================================================================================================================
def paving(x0, x1, z0, z1, y=GY, h=0.35):
    ZONES_OCC.append(('p', x0, x1, z0, z1))
    box(x0, x1, y, y + h, z0, z1, PAL['walk'])
    for k in range(1, int((x1 - x0) // 6) + 1):
        box(x0 + k * 6, x0 + k * 6 + 0.08, y + h, y + h + 0.03, z0, z1, PAL['walk2'])
    for k in range(1, int((z1 - z0) // 6) + 1):
        box(x0, x1, y + h, y + h + 0.03, z0 + k * 6, z0 + k * 6 + 0.08, PAL['walk2'])


paving(36, 100, -52, -21.2)
paving(106, 164, -52, -21.2)
paving(166, 218, -56, -21.2)
paving(-200, -148, -62, -21.2)
paving(-66, -24, -62, -21.2)
paving(-86, -36, 21.2, 50)
paving(34, 90, 21.2, 36)
paving(136, 190, 21.2, 36)


def service_street(zc, x0, x1, seed):
    A, S = 8, 5
    box(x0, x1, GY, GY + 0.1, zc - A, zc + A, PAL['asphalt'])
    for sg in (-1, 1):
        z0, z1 = (zc + A, zc + A + S) if sg > 0 else (zc - A - S, zc - A)
        box(x0, x1, GY, GY + 0.5, z0, z1, PAL['walk'])
        box(x0, x1, GY, GY + 0.58, (z0 - 0.4) if sg > 0 else (z1 - 0.4), (z0 + 0.4) if sg > 0 else (z1 + 0.4), PAL['curb'])
        for k in range(int((x1 - x0) // 8)):
            box(x0 + k * 8, x0 + k * 8 + 0.08, GY + 0.5, GY + 0.52, z0 + 0.5, z1 - 0.2, PAL['walk2'])
    p = x0 + 6
    while p < x1 - 6:
        box(p, p + 4, GY + 0.1, GY + 0.16, zc - 0.15, zc + 0.15, PAL['white'])
        p += 10
    i = 0
    p = x0 + 14
    while p < x1 - 8:
        for sg in (-1, 1):
            zz = zc + sg * (A + S - 1.6)
            if zc == -145 and sg > 0 and -108 < p < -80:
                continue            # driveway of the tower courtyard
            if i % 2 == 0:
                street_lamp(p, zz, facing=-sg * 1.57)
            else:
                tree(p, zc + sg * (A + S - 0.9), seed=seed + i, h=8.5 + (i % 3), r=3.4)     # narrow crown: the sidewalk is only 5 wide
        p += 17
        i += 1


PASTEL = [('#F2C078', PAL['teal']), ('#E07A5F', PAL['green']), ('#9AD1D4', PAL['red']), ('#F6E7C8', PAL['blue']), ('#F29BB5', PAL['teal']), ('#B9D96C', PAL['red']),
          ('#C3B1E1', PAL['yellow']), ('#F7D794', PAL['navy'])]


def row(z0, z1, front, xs, seed):
    for i, (x0, x1, fl) in enumerate(xs):
        wall, shut = PASTEL[(i + seed) % len(PASTEL)]
        b = R(x0, x1, z0, z1)
        sf = [(2.5, 12, (shut, PAL['white']))] if (i + seed) % 3 == 0 else None
        building(b, fl, wall, PAL['white'], fh=11, front=front, ground_h=13, shutters=shut, name='row_%d_%d_%d' % (seed, i, int(z0)), seed=seed * 10 + i, tank=False,
                 storefronts=sf, entrance_u=(x1 - x0) / 2 + 3, balconies=(i % 2 == 0 and fl >= 5))


service_street(-145, -SZ - 6, -SW, 1)
service_street(-145, SW, SZ + 6, 2)
service_street(145, -SZ - 6, -SW, 3)
row(-205, -162, 'S', [(-214, -176, 5), (-170, -132, 7), (-126, -88, 4), (-82, -44, 6)], 1)
row(-205, -162, 'S', [(26, 64, 6), (70, 110, 4), (116, 156, 7), (162, 206, 5)], 2)
row(-126, -100, 'N', [(-210, -172, 3), (-166, -128, 3), (-62, -30, 3)], 3)
row(100, 127, 'S', [(-210, -172, 4), (-166, -128, 3), (-122, -84, 4), (-78, -34, 3)], 4)
row(165, 210, 'N',[(-210, -172, 5), (-166, -128, 6), (-122, -84, 4), (-78, -34, 7)], 5)
# courtyards: trees and hedges between the rows, a small plaza with benches
for (cx, cz) in ((-150, -112), (-26 - 20, -112), (-100, 112), (-150, 150)):
    pass
for k in range(22):
    tree(-210 + (k * 37) % 180, -98 + (k * 7) % 4 * 0 - 0, seed=k + 90, h=9 + (k % 3), r=4.4, pit=False) if False else None
for sx in (-1, 1):
    for k in range(6):
        hz = -96 if sx < 0 else -96
# boundary hedge ring and ornamental fence segments
for (x0, x1, z0, z1) in ((-SZ - 6, SZ + 6, -SZ - 6, -SZ - 3), (-SZ - 6, SZ + 6, SZ + 3, SZ + 6), (-SZ - 6, -SZ - 3, -SZ - 6, SZ + 6), (SZ + 3, SZ + 6, -SZ - 6, SZ + 6)):
    box(x0, x1, GY, GY + 4.6, z0, z1, PAL['green'])
    box(x0 - 0.1, x1 + 0.1, GY + 4.6, GY + 4.9, z0 - 0.1, z1 + 0.1, PAL['grass2'])
collider(-SZ - 6, SZ + 6, GY, GY + 20, -SZ - 6, -SZ - 3, 'edgeN')
collider(-SZ - 6, SZ + 6, GY, GY + 20, SZ + 3, SZ + 6, 'edgeS')
collider(-SZ - 6, -SZ - 3, GY, GY + 20, -SZ - 6, SZ + 6, 'edgeW')
collider(SZ + 3, SZ + 6, GY, GY + 20, -SZ - 6, SZ + 6, 'edgeE')
