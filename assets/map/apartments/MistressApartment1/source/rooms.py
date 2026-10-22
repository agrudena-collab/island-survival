# Layout of the flat (exec'd by build_flat.py after furn.py).
#   main room x -22..22, z -16..16 (hall SW, kitchen W, dining centre, living E), bedroom wing x 23..46, z -16..3, bathroom x 23..46, z 4..16.
WX0, WX1 = -22.0, 22.0        # main room inner faces
WZ0, WZ1 = -16.0, 16.0
EX1 = 46.0                    # wing east inner face
PZ = 3.0                      # partition inner face (bedroom side); bathroom side starts at 4.0
KEEP = []


# =======================================================================================================================================
# shell: floor, ceiling, walls, trims
# =======================================================================================================================================
box(-23, 47, 0, FY, -17, 17, P['concrete'])
collider(-23, 47, -2, FY, -17, 17, 'floor')
box(-23, 47, CY, CY + 1, -17, 17, P['cream'])
collider(-23, 47, CY, CY + 1, -17, 17, 'ceiling')


def parquet(x0, x1, z0, z1, seed, cols=None, skip=()):
    cols = cols or [P['oak'], P['oak2'], P['oak3'], shade(P['oak'], 0.06)]
    box(x0, x1, FY, FY + 0.02, z0, z1, P['walnut']) if not skip else None
    for (a_, b_) in split_range(x0, x1, []) if not skip else []:
        pass
    if skip:
        for (zz0, zz1) in split_range(z0, z1, [(s[2], s[3]) for s in skip]):
            box(x0, x1, FY, FY + 0.02, zz0, zz1, P['walnut'])
        for s in skip:
            for (xa, xb) in split_range(x0, x1, [(s[0], s[1])]):
                box(xa, xb, FY, FY + 0.02, s[2], s[3], P['walnut'])
    r = rnd_of(seed)
    z = z0
    while z < z1 - 0.01:
        w = min(0.75, z1 - z)
        cuts = [(s[0], s[1]) for s in skip if z < s[3] - 0.01 and z + w > s[2] + 0.01]     # rows that run through a tiled area stop at its edge
        x = x0 - r.uniform(0, 4.0)
        while x < x1:
            ln = r.uniform(3.6, 5.2)
            a, b = max(x, x0), min(x + ln - 0.05, x1)
            if b - a > 0.2:
                for (sa, sb) in split_range(a, b, cuts):
                    if sb - sa > 0.2:
                        box(sa, sb, FY + 0.02, FY + 0.06, z + 0.02, z + w - 0.02, cols[r.randrange(len(cols))])
            x += ln
        z += w


def tiles(x0, x1, z0, z1, c1, c2, s=2.0, seed=0):
    box(x0, x1, FY, FY + 0.02, z0, z1, P['marble2'])
    i = 0
    x = x0
    while x < x1 - 0.01:
        j = 0
        z = z0
        while z < z1 - 0.01:
            box(x + 0.03, min(x + s, x1) - 0.03, FY + 0.02, FY + 0.07, z + 0.03, min(z + s, z1) - 0.03, c1 if (i + j) % 2 == 0 else c2)
            z += s
            j += 1
        x += s
        i += 1


KX1, KZ1 = -9.0, 2.0
HX1, HZ0 = -8.0, 5.0
parquet(-22, 22, -16, 16, 1, skip=[(-22, -9, -16, 2), (-22, -8, 5, 16)])
tiles(-22, KX1, -16, KZ1, P['tileW'], P['tileG'], 2.0)                    # kitchen
tiles(-22, HX1, HZ0, 16, P['marble'], P['marble2'], 2.0)                    # hall
parquet(23, 46, -16, 3, 2, [P['oak3'], shade(P['oak3'], 0.08), P['oak']])      # bedroom
tiles(23, 46, 4, 16, P['tileW'], P['tileG'], 2.0)                           # bathroom
box(22, 23, FY, FY + 0.05, -16, 16, P['brass'])                             # thresholds between main and wing

# --- walls -------------------------------------------------------------------------------------------------------------------------
wall_x(-16.5, -23, 47, [(-14, 14, FY + 3, FY + 9), (28, 38, FY + 3.5, FY + 9)], P['wall'], name='wall_n')
wall_x(16.5, -23, 47, [(-17, -11, FY, FY + 8), (30, 36, FY + 5.5, FY + 9)], P['wall'], name='wall_s')
wall_z(-22.5, -17, 17, [], P['wall'], name='wall_w')
wall_z(46.5, -17, 17, [], P['wall'], name='wall_e')
wall_z(22.5, -17, 17, [(-10, -5, FY, FY + 8), (6.5, 11.5, FY, FY + 8)], P['wall'], name='wall_mid')
wall_x(3.5, 22, 47, [], P['wall'], name='wall_part')

# window glass colliders (the glass is solid)
collider(-14, 14, FY + 3, FY + 9, -16.4, -16.2, 'glass')
collider(28, 38, FY + 3.5, FY + 9, -16.4, -16.2, 'glass')

# accent skins (room colours on the inner faces)
wb('E', -22.0, FY, 0, 32, 4.6, 0.05, P['blush'], kind='O') if False else None
wb('N', 13, FY + 0.8, 16.0, 18, H - 0.8, 0.06, '#C98F8E')                 # TV wall (south wall, x 4..22)
for k in range(4):                                                         # wall panel mouldings on the TV wall
    wb('N', 7.5 + k * 4.6, FY + 1.0, 16.06, 3.9, 8.5, 0.05, shade('#C98F8E', 0.12))
    wb('N', 7.5 + k * 4.6, FY + 1.2, 16.11, 3.5, 8.1, 0.04, '#C98F8E')
wb('S', 0, FY + 0.8, -16.0, 0.01, 0.01, 0.01, P['wall']) if False else None
wb('E', 23.0, FY + 0.8, -6.5, 19.0, H - 0.8, 0.06, '#D4A5A6')              # bedroom west wall (inner face x=23)
wb('W', 46.0, FY + 0.8, -6.5, 19.0, H - 0.8, 0.06, '#BF8C92')              # bedroom east wall / headboard wall
wb('N', 34.5, FY + 0.8, 3.0, 23.0, 0.01, 0.01, P['wall']) if False else None
wb('S', 34.5, FY + 0.8, 4.0, 23.0, 7.0, 0.05, '#BFD3D2')                  # bathroom partition tiles
wb('N', 34.5, FY + 0.8, 16.0, 23.0, 7.0, 0.05, '#BFD3D2')                 # bathroom south tiles
wb('E', 23.0, FY + 0.8, 10.0, 12.0, 7.0, 0.05, '#BFD3D2')
wb('W', 46.0, FY + 0.8, 10.0, 12.0, 7.0, 0.05, '#BFD3D2')
for k in range(1, 12):                                                      # tile grout lines (bathroom, 2-stud grid)
    x = 23 + k * 2.0
    wb('S', x, FY + 0.8, 4.05, 0.05, 7.0, 0.03, P['tileG'])
    wb('N', x, FY + 0.8, 15.95, 0.05, 7.0, 0.03, P['tileG'])
for k in range(1, 4):
    y = FY + 0.8 + k * 2.0
    wb('S', 34.5, y, 4.05, 23.0, 0.05, 0.03, P['tileG'])
    wb('N', 34.5, y, 15.95, 23.0, 0.05, 0.03, P['tileG'])
wb('W', 46.0, FY + 7.7, 10, 12, 0.3, 0.12, P['tileG'])
wb('S', 34.5, FY + 7.7, 4.0, 23, 0.3, 0.12, P['tileG'])
wb('N', 34.5, FY + 7.7, 16.0, 23, 0.3, 0.12, P['tileG'])
# kitchen backsplash (west wall) with a hex-like tile grid
wb('E', -22.0, FY + 3.4, -9.0, 14.0, 4.8, 0.05, '#E7E2D6')
for k in range(1, 14):
    wb('E', -22.0, FY + 3.4, -16 + k * 1.0, 0.04, 4.8, 0.03, P['tileG'])
for k in range(1, 5):
    wb('E', -22.0, FY + 3.4 + k * 0.96, -9.0, 14.0, 0.04, 0.03, P['tileG'])

# --- baseboards, crown moulding, door casings ------------------------------------------------------------------------------------------
def baseboards():
    # wall segments with their door openings: (axis, wall coordinate, inner side sign, range, openings)
    runs = [('x', -16.0, 1, -22, 22, [(-22, -22)]), ('x', 16.0, -1, -22, 46, [(-17, -11), (22, 23)]), ('z', -22.0, 1, -16, 16, []),
            ('z', 23.0, 1, -16, 16, [(-10, -5), (6.5, 11.5)]), ('z', 22.0, -1, -16, 16, [(-10, -5), (6.5, 11.5)]), ('x', -16.0, 1, 23, 46, []), ('z', 46.0, -1, -16, 16, []),
            ('x', 3.0, -1, 23, 46, []), ('x', 4.0, 1, 23, 46, [])]
    for (ax, c, sg, a, b, cuts) in runs:
        for (s0, s1) in split_range(a, b, cuts):
            if ax == 'x':
                box(s0, s1, FY, FY + 0.9, c if sg > 0 else c - 0.28, c + 0.28 if sg > 0 else c, shade(P['wall'], 0.35))
                box(s0, s1, FY + 0.9, FY + 1.0, c if sg > 0 else c - 0.18, c + 0.18 if sg > 0 else c, shade(P['wall'], 0.5))
                box(s0, s1, CY - 0.7, CY, c if sg > 0 else c - 0.5, c + 0.5 if sg > 0 else c, P['cream'])
                box(s0, s1, CY - 0.9, CY - 0.7, c if sg > 0 else c - 0.3, c + 0.3 if sg > 0 else c, shade(P['cream'], -0.08))
            else:
                box(c if sg > 0 else c - 0.28, c + 0.28 if sg > 0 else c, FY, FY + 0.9, s0, s1, shade(P['wall'], 0.35))
                box(c if sg > 0 else c - 0.18, c + 0.18 if sg > 0 else c, FY + 0.9, FY + 1.0, s0, s1, shade(P['wall'], 0.5))
                box(c if sg > 0 else c - 0.5, c + 0.5 if sg > 0 else c, CY - 0.7, CY, s0, s1, P['cream'])
                box(c if sg > 0 else c - 0.3, c + 0.3 if sg > 0 else c, CY - 0.9, CY - 0.7, s0, s1, shade(P['cream'], -0.08))


baseboards()


def casing_x(z, xa, xb, ytop, side, col=None):
    """Door casing on a wall along x (z = wall inner face; side +1: room is on the +z side)."""
    col = col or P['white']
    o0, o1 = (z, z + 0.45) if side > 0 else (z - 0.45, z)
    box(xa - 0.45, xa, FY, ytop + 0.45, o0, o1, col)
    box(xb, xb + 0.45, FY, ytop + 0.45, o0, o1, col)
    box(xa - 0.45, xb + 0.45, ytop, ytop + 0.45, o0, o1, col)
    box(xa - 0.6, xb + 0.6, ytop + 0.45, ytop + 0.7, o0, o1, P['cream'])


def casing_z(x, za, zb, ytop, side, col=None):
    col = col or P['white']
    o0, o1 = (x, x + 0.45) if side > 0 else (x - 0.45, x)
    box(o0, o1, FY, ytop + 0.45, za - 0.45, za, col)
    box(o0, o1, FY, ytop + 0.45, zb, zb + 0.45, col)
    box(o0, o1, ytop, ytop + 0.45, za - 0.45, zb + 0.45, col)
    box(o0, o1, ytop + 0.45, ytop + 0.7, za - 0.6, zb + 0.6, P['cream'])


if ROUND:
    for (za, zb) in ((-10, -5), (6.5, 11.5)):      # round arches over the bedroom and bathroom doorways
        arch_opening('zy', za, zb, FY + 8, 22.0, 23.0, P['wall'])
        arch_casing('zy', za, zb, FY + 8, 21.55, 22.0, P['white'])
        arch_casing('zy', za, zb, FY + 8, 23.0, 23.45, P['white'])
else:
    casing_z(22.0, -10, -5, FY + 8, -1)     # bedroom door, main side
    casing_z(23.0, -10, -5, FY + 8, 1)      # bedroom side
    casing_z(22.0, 6.5, 11.5, FY + 8, -1)
    casing_z(23.0, 6.5, 11.5, FY + 8, 1)
casing_x(16.0, -17, -11, FY + 8, -1, P['white'])

# window frames
window_frame_n(-14, 14, FY + 3, FY + 9, -16.0, P['white'], [-9.4, -4.7, 0, 4.7, 9.4])
window_frame_n(28, 38, FY + 3.5, FY + 9, -16.0, P['white'], [33])
for k in range(4):
    wb('N', 33, FY + 5.2 + k * 0.0, 16.0, 6, 3.4, 0.15, P['white'], off=0.0) if False else None
wb('N', 33, FY + 5.5, 16.0, 6.8, 0.4, 0.5, P['white'])                       # bathroom window frame
wb('N', 33, FY + 9.0, 16.0, 6.8, 0.4, 0.5, P['white'])
wb('N', 29.8, FY + 5.5, 16.0, 0.4, 3.9, 0.5, P['white'])
wb('N', 36.2, FY + 5.5, 16.0, 0.4, 3.9, 0.5, P['white'])
wb('N', 33, FY + 5.9, 16.45, 6.0, 3.1, 0.06, '#F3F8FA', kind='G')            # frosted glass
collider(30, 36, FY + 5.5, FY + 9, 16.2, 16.6, 'glass')

# =======================================================================================================================================
# skyline behind the windows (north), sky plane
# =======================================================================================================================================
box(-120, 160, FY - 40, FY + 120, -112, -111, P['sky'])
for k in range(7):
    band = shade(P['sky'], 0.12 + k * 0.03)
    box(-120, 160, FY + 10 + k * 14, FY + 24 + k * 14, -111, -110.5, band)
rs = rnd_of(5)
x = -70
while x < 100:
    w = rs.uniform(7, 15)
    h = rs.uniform(18, 62)
    z0 = rs.uniform(-62, -44)
    col = rs.choice(['#C7B7C7', '#B8C4D6', '#D9C2B5', '#A9B7C4', '#CDB8A4', '#BBA9C4'])
    box(x, x + w, FY - 30, FY + h, z0 - 9, z0, col)
    box(x - 0.3, x + w + 0.3, FY + h, FY + h + 0.8, z0 - 9.3, z0 + 0.3, shade(col, -0.12))
    nxw = int(w // 2.2)
    for i in range(nxw):
        for j in range(int(h // 3.4)):
            if rs.random() < 0.42:
                box(x + 0.6 + i * 2.2, x + 1.7 + i * 2.2, FY + 1.0 + j * 3.4, FY + 2.4 + j * 3.4, z0, z0 + 0.15, '#FFE2A0' if rs.random() < 0.8 else '#BFE3F2', 'N')
            else:
                box(x + 0.6 + i * 2.2, x + 1.7 + i * 2.2, FY + 1.0 + j * 3.4, FY + 2.4 + j * 3.4, z0, z0 + 0.1, '#6E7C90')
    x += w + rs.uniform(1.5, 5)
for (cx, cy, cz, s) in ((-30, FY + 55, -100, 14), (20, FY + 70, -100, 18), (70, FY + 48, -100, 12), (-60, FY + 75, -100, 16)):
    for k in range(5):
        D.sphere(cx + (k - 2) * s * 0.55, cy + (k % 2) * 2, cz, s * 0.5, s * 0.28, s * 0.3, P['white'], seg=10, rings=6)
ceil_lights = []

# =======================================================================================================================================
# ceiling: cove lighting, recessed spots, medallion
# =======================================================================================================================================
def cove(x0, x1, z0, z1, depth=0.5):
    y = CY - depth
    for (a, b, c, d) in ((x0, x1, z0, z0 + 0.7), (x0, x1, z1 - 0.7, z1), (x0, x0 + 0.7, z0, z1), (x1 - 0.7, x1, z0, z1)):
        box(a, b, y, CY, c, d, P['cream'])
    for (a, b, c, d) in ((x0 + 0.7, x1 - 0.7, z0 + 0.7, z0 + 0.95), (x0 + 0.7, x1 - 0.7, z1 - 0.95, z1 - 0.7), (x0 + 0.7, x0 + 0.95, z0 + 0.7, z1 - 0.7), (x1 - 0.95, x1 - 0.7, z0 + 0.7, z1 - 0.7)):
        box(a, b, y, y + 0.1, c, d, '#FFE9C2', 'N')


cove(-20.5, 20.5, -14.5, 14.5)
cove(24.5, 44.5, -14.5, 1.5)
for (x, z) in ((-18, 12), (-12, 12), (-18, 8), (-6, 12), (-13, -13), (-13, -4), (-5, -13), (10, -13), (18, -13), (18, 0), (9, 10), (19, 10), (6, 0), (27, -13), (42, -13), (34, 0), (27, -3),
               (40, 0), (27, 12), (34, 10), (42, 12)):
    cyl(x, z, CY - 0.12, CY, 0.55, P['white'], seg=14)
    cyl(x, z, CY - 0.16, CY - 0.12, 0.42, '#FFF1C8', seg=14, kind='N')
    if (x + z) % 3 == 0:
        spot(x, CY - 0.6, z, 20, 0.6)
# dining medallion
lathe(2, -5, CY - 0.1, [(4.2, 0), (4.2, -0.2), (3.0, -0.35), (0.6, -0.5), (0.0, -0.5)], P['white'], seg=32)
ring(2, CY - 0.3, -5, 3.6, 0.12, 'xz', P['gold'], seg=36, tseg=6)

_box_sharp = box


def box(x0, x1, y0, y1, z0, z1, col='#CCCCCC', kind='O'):
    """From here on the furniture-sized boxes are real rounded boxes (walls, floors and trims above stay sharp)."""
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    if ROUND and kind == 'O' and min(dx, dy, dz) >= 0.3 and max(dx, dz) < 14 and dy < 12:
        rbox(x0, x1, y0, y1, z0, z1, col, r=min(0.2, 0.22 * min(dx, dz)), rt=min(0.18, 0.28 * dy))
    else:
        _box_sharp(x0, x1, y0, y1, z0, z1, col, kind)


# =======================================================================================================================================
# HALL (SW): exit door, shoe cabinet, coat hooks, console, mirror, bench, plants
# =======================================================================================================================================
# exit door leaf (inside the wall thickness, teal with panels) and handle
box(-16.9, -11.1, FY, FY + 8.0, 16.25, 16.75, P['teal'])
for (xa, xb, ya, yb) in ((-16.3, -14.2, 0.7, 3.5), (-13.8, -11.7, 0.7, 3.5), (-16.3, -14.2, 4.0, 7.4), (-13.8, -11.7, 4.0, 7.4)):
    wb('N', (xa + xb) / 2, FY + ya, 16.25, xb - xa, yb - ya, 0.08, shade(P['teal'], 0.15))
    wb('N', (xa + xb) / 2, FY + ya + 0.3, 16.25, xb - xa - 0.6, yb - ya - 0.6, 0.12, P['teal'])
wb('N', -12.2, FY + 4.0, 16.25, 0.2, 1.4, 0.35, P['brass'])
wb('N', -12.2, FY + 4.0, 16.25, 0.9, 0.2, 0.4, P['brass'])
wb('N', -14, FY + 6.6, 16.25, 0.45, 0.45, 0.15, P['brass'])                    # peephole
wb('N', -14, FY + 7.1, 16.25, 1.6, 0.8, 0.12, P['gold'])                       # number plate
wb('N', -14, FY + 7.2, 16.25, 1.2, 0.6, 0.18, P['white'])
SIGNS.append(('A1', -14, FY + 7.5, 16.0, 1.0, 0.45, 'N'))
rug(-14, 11, 6.4, 8.6, P['rose'], P['rose2'], pattern=2, seed=3)
# shoe cabinet + bench on the west wall
f = F(-20.85, 12.9, 'E')
f.b(-2.6, 2.6, 0.6, 2.6, -1.0, 1.0, P['oak2'])
for i in range(3):
    f.b(-2.5 + i * 1.7, -0.9 + i * 1.7, 0.8, 2.4, 1.0, 1.06, shade(P['oak2'], 0.12))
    handle(f, -1.7 + i * 1.7, 1.6, 1.06)
f.b(-2.8, 2.8, 2.6, 2.85, -1.1, 1.1, P['cream'])
for lx in (-2.4, 2.4):
    for lz in (-0.8, 0.8):
        f.lt(lx, lz, FY, [(0.0, 0), (0.15, 0), (0.1, 0.65)], P['brass'], seg=8)
f.sb(-2.7, 2.7, 2.85, 3.3, -1.0, 1.0, P['rose2'], 0.1)                       # cushion on the bench top
f.col(-2.8, 2.8, 0, 3.4, -1.1, 1.1, 'shoecabinet')
for k in range(3):                                                           # shoes
    f.b(-2.0 + k * 1.4, -1.5 + k * 1.4, 2.85, 3.1, 0.1, 0.7, [P['red'], P['navy'], P['mustard']][k])
mirror('E', -22.0, 12.9, FY + 4.6, 4.2, 5.4, seed=1)
# coat hooks with coats and a hat
wb('E', -22.0, FY + 6.6, 9.2, 0.35, 0.35, 0.3, P['white'], kind='O') if False else None
wb('E', -22.0, FY + 6.2, 7.6, 4.6, 0.4, 0.3, P['walnut'])
for k, (cz, cc) in enumerate(((6.2, '#B98A5A'), (7.6, P['navy']), (9.0, P['rose2']))):
    wb('E', -21.55, FY + 2.9, cz, 1.2, 3.4, 0.5, cc, off=0.1)
    wb('E', -21.55, FY + 4.6, cz, 1.5, 1.2, 0.55, shade(cc, -0.15), off=0.1)
    D.sphere(-21.6, FY + 6.1, cz, 0.12, 0.12, 0.12, P['gold'], seg=6, rings=4)
# console + mirror + lamp on the south wall
c = console_table(-4, 15.2, 'N', 6.2, d=1.4)
table_lamp(-5.6, FY + 2.8, 15.2, base=P['rose2'], h=2.2)
vase(c, 1.0, FY + 2.8, 0, h=1.5, col=P['sky'], seed=4)
c.b(-0.5, 0.8, FY + 2.8, FY + 2.9, -0.4, 0.4, P['gold'])
c.b(-0.4, 0.5, FY + 2.9, FY + 3.1, -0.3, 0.3, P['rose'])
mirror('N', -4, 16.0, FY + 4.4, 4.2, 5.2, seed=2)
art('N', -9.6, 16.0, FY + 5.0, 2.4, 3.2, 32)
plant_pot(F(-8.2, 13.6, 'S'), 0, 0, h=1.7, r=0.8, big=True, seed=5)
CYLC.append((-8.2, FY + 3, 13.6, 1.9, 6, 'plant'))
# umbrella stand and a slim bench by the door
lathe(-9.6, 15.0, FY, [(0.0, 0), (0.55, 0), (0.6, 0.1), (0.55, 2.2), (0.0, 2.2)], P['charcoal'], seg=12)
for k in range(2):
    cyl(-9.5 + k * 0.2, 15.0, FY + 2.2, FY + 4.2 - k * 0.5, 0.06, P['navy'], seg=6)
spot(-14, CY - 1.0, 11, 22, 0.9)
pendant(-14, 10, CY, CY - 3.0, col=P['brass'], r=1.5)

# =======================================================================================================================================
# KITCHEN (west wall) + island
# =======================================================================================================================================
def cab_row(z0, z1, name='kbase'):
    """Base cabinets between z0 and z1 on the west wall: doors, drawers, handles, toe-kick."""
    box(-22, -19.5, FY, FY + 0.5, z0, z1, P['charcoal'])
    box(-22, -19.4, FY + 0.5, FY + 3.2, z0, z1, P['cream'])
    n = max(1, int((z1 - z0) // 1.8))
    w = (z1 - z0) / n
    for i in range(n):
        a = z0 + i * w
        wb('E', -19.4, FY + 0.7, a + w / 2, w - 0.16, 1.45, 0.08, P['white'])
        wb('E', -19.4, FY + 0.85, a + w / 2, w - 0.5, 1.15, 0.12, shade(P['white'], -0.04))
        wb('E', -19.5, FY + 2.3, a + w / 2, w - 0.16, 0.8, 0.08, P['white'])
        wb('E', -19.5, FY + 2.35, a + w / 2, w - 0.5, 0.6, 0.12, shade(P['white'], -0.04))
        wb('E', -19.3, FY + 2.7, a + w / 2, 0.8, 0.1, 0.12, P['brass'])
        wb('E', -19.3, FY + 1.5, a + w / 2 - w * 0.3, 0.1, 0.8, 0.12, P['brass'])
    collider(-22, -19.4, FY, FY + 3.2, z0, z1, name)


def uppers(z0, z1):
    box(-22, -20.6, FY + 6.4, FY + 9.4, z0, z1, P['cream'])
    n = max(1, int((z1 - z0) // 1.8))
    w = (z1 - z0) / n
    for i in range(n):
        a = z0 + i * w
        wb('E', -20.6, FY + 6.6, a + w / 2, w - 0.16, 2.6, 0.08, P['white'])
        wb('E', -20.6, FY + 6.8, a + w / 2, w - 0.5, 2.2, 0.12, P['glass'] if i % 2 == 0 else shade(P['white'], -0.04), kind='G' if i % 2 == 0 else 'O')
        wb('E', -20.5, FY + 6.7, a + w / 2 - w * 0.3, 0.1, 0.7, 0.1, P['brass'])
    box(-22.1, -20.5, FY + 9.4, FY + 9.7, z0, z1, P['white'])
    collider(-22, -20.6, FY + 6.4, FY + 9.7, z0, z1, 'kupper')


cab_row(-15.5, -8.6)
cab_row(-4.5, -1.5) if False else None
# counter with sink opening
for (a, b) in ((-15.5, -13.6), (-10.4, -8.6)):
    box(-22, -19.1, FY + 3.2, FY + 3.45, a, b, P['marble'])
box(-22, -19.1, FY + 3.2, FY + 3.45, -13.6, -13.5, P['marble'])
box(-22, -19.1, FY + 3.2, FY + 3.45, -10.5, -10.4, P['marble'])
box(-22, -20.2, FY + 3.2, FY + 3.45, -13.6, -10.4, P['marble'])
for (x0, x1, z0, z1) in ((-21.4, -19.5, -13.5, -13.3), (-21.4, -19.5, -10.6, -10.4), (-21.4, -21.2, -13.5, -10.4), (-19.7, -19.5, -13.5, -10.4)):
    box(x0, x1, FY + 2.6, FY + 3.3, z0, z1, P['metal'])
box(-21.3, -19.6, FY + 2.55, FY + 2.65, -13.4, -10.5, shade(P['metal'], -0.1))
hcyl(-19.9, FY + 4.5, -12.0, 'x', 0.1, 0.0, P['metal']) if False else None
cyl(-20.2, -12.0, FY + 3.45, FY + 4.6, 0.11, P['metal'], seg=8)
hcyl(-19.8, FY + 4.7, -12.0, 'x', 1.0, 0.1, P['metal'], seg=8)
cyl(-19.4, -12.0, FY + 4.4, FY + 4.7, 0.09, P['metal'], seg=8)
D.sphere(-20.2, FY + 4.7, -12.0, 0.17, 0.12, 0.17, P['metal'], seg=8, rings=4)
collider(-22, -19.1, FY + 3.2, FY + 3.5, -15.5, -8.6, 'kcounter')
# stove with a hood
box(-22, -19.4, FY, FY + 3.2, -8.3, -4.9, P['charcoal'])
box(-22, -19.3, FY + 3.2, FY + 3.4, -8.3, -4.9, P['black'])
for (bz, bx) in ((-7.5, -20.7), (-5.7, -20.7), (-7.5, -19.9), (-5.7, -19.9)):
    cyl(bx, bz, FY + 3.4, FY + 3.48, 0.38, P['metal'], seg=12)
    cyl(bx, bz, FY + 3.48, FY + 3.5, 0.18, P['charcoal'], seg=10)
wb('E', -19.3, FY + 0.6, -6.6, 3.0, 2.2, 0.06, P['black'])
wb('E', -19.3, FY + 0.9, -6.6, 2.6, 1.6, 0.1, P['glass'], kind='G')
wb('E', -19.3, FY + 2.5, -6.6, 2.8, 0.2, 0.2, P['metal'])
for k in range(4):
    wb('E', -19.3, FY + 2.75, -7.6 + k * 0.75, 0.3, 0.3, 0.1, P['metal'])
collider(-22, -19.3, FY, FY + 3.5, -8.3, -4.9, 'stove')
frustum(-21.0, -6.6, 2.0, 3.4, FY + 7.4, 1.8, 0.5, P['metal'])
box(-22, -20.2, FY + 9.2, FY + 11.0, -7.6, -5.6, P['metal'])
collider(-22, -19.9, FY + 7.4, FY + 11, -8.3, -4.9, 'hood')
uppers(-15.5, -8.8)
# pans and utensils on the wall rail
wb('E', -22.0, FY + 7.0, -4.0, 0.15, 0.15, 0.3, P['brass']) if False else None
# fridge (double door, stainless) + cabinet above
box(-22, -19.2, FY, FY + 7.2, -4.5, -1.5, P['metal'])
for z0 in (-4.4, -3.0):
    wb('E', -19.2, FY + 0.2, z0 + 0.7, 1.4, 6.8, 0.1, shade(P['metal'], 0.15))
wb('E', -19.2, FY + 3.6, -3.05, 0.1, 3.0, 0.3, P['black'])
wb('E', -19.2, FY + 3.6, -2.85, 0.1, 3.0, 0.3, P['black'])
for k in range(3):
    wb('E', -19.1, FY + 4.2 + k * 0.6, -2.0 - k * 0.0, 0.5, 0.4, 0.05, [P['rose'], P['mustard'], P['teal2']][k])    # magnets / notes
collider(-22, -19.2, FY, FY + 7.2, -4.5, -1.5, 'fridge')
box(-22, -20.6, FY + 7.5, FY + 9.7, -4.5, -1.5, P['cream'])
wb('E', -20.6, FY + 7.6, -3.0, 2.8, 2.0, 0.08, P['white'])
# counter props: kettle, toaster, coffee machine, cutting board, fruit bowl, herbs, utensils
cyl(-20.6, -9.2, FY + 3.45, FY + 4.35, 0.5, P['red'], seg=12, r2=0.38)
box(-21.2, -20.6, FY + 3.45, FY + 4.0, -15.2, -14.2, P['charcoal'])
box(-21.0, -20.8, FY + 4.0, FY + 4.15, -15.0, -14.4, P['metal'])
box(-21.4, -20.2, FY + 3.45, FY + 4.6, -14.2, -13.8, P['metal']) if False else None
lathe(-20.5, -14.8, FY + 3.45, [(0.0, 0), (0.55, 0), (0.55, 0.8), (0.0, 0.8)], P['white'], seg=10)
box(-21.2, -20.2, FY + 3.45, FY + 3.55, -9.8, -8.9, P['oak2'])
lathe(-20.8, -10.8, FY + 3.45, [(0.0, 0), (0.55, 0), (0.7, 0.4), (0.0, 0.4)], P['white'], seg=14) if False else None
for k in range(4):
    cyl(-21.5 + k * 0.0, -9.9 + k * 0.1, FY + 3.45, FY + 3.46, 0.01, P['white'], seg=4) if False else None
# island with stools and pendants
box(-14.4, -11.2, FY, FY + 0.4, -12, -3.5, P['charcoal'])
box(-14.4, -11.4, FY + 0.4, FY + 3.2, -12, -3.5, P['teal'])
for k in range(5):
    wb('E', -11.4, FY + 0.7, -11.2 + k * 1.7, 1.5, 2.2, 0.08, shade(P['teal'], 0.12))
    wb('E', -11.4, FY + 1.2, -11.2 + k * 1.7, 1.1, 1.3, 0.12, P['teal'])
    wb('W', -11.3, FY + 2.4, -11.2 + k * 1.7, 0.1, 0.7, 0.1, P['brass']) if False else None
box(-14.8, -10.4, FY + 3.2, FY + 3.5, -12.2, -3.3, P['marble'])
box(-14.8, -10.4, FY + 3.15, FY + 3.2, -12.2, -3.3, P['marble2'])
collider(-14.8, -10.4, FY, FY + 3.5, -12.2, -3.3, 'island')
for k in range(3):                                                           # stools on the east side
    sz = -10.4 + k * 2.6
    lathe(-8.8, sz, FY, [(0.0, 0), (0.5, 0), (0.45, 0.1), (0.12, 0.2), (0.12, 2.0), (0.7, 2.15), (0.78, 2.4), (0.0, 2.45)], P['rose2'], seg=14)
    ring(-8.8, FY + 0.9, sz, 0.5, 0.05, 'xz', P['brass'], seg=14, tseg=4)
    CYLC.append((-8.8, FY + 1.2, sz, 1.6, 2.4, 'stool'))
# island decor: bowl of fruit, cutting board with bread, wine glasses
lathe(-12.6, -9.0, FY + 3.5, [(0.0, 0), (0.7, 0.0), (0.95, 0.5), (0.0, 0.5)], P['white'], seg=16)
for k, c in enumerate((P['red'], P['mustard'], P['green2'], P['orange'] if 'orange' in P else '#F28C38', P['red'])):
    a = k * 1.26
    D.sphere(-12.6 + math.cos(a) * 0.35, FY + 4.15, -9.0 + math.sin(a) * 0.35, 0.28, 0.28, 0.28, c, seg=8, rings=5)
box(-13.8, -11.4, FY + 3.5, FY + 3.62, -6.8, -5.4, P['oak2'])
box(-13.4, -12.2, FY + 3.62, FY + 4.0, -6.5, -5.8, '#D9A35F')
for k in range(2):
    lathe(-13.0 + k * 0.7, -4.4, FY + 3.5, [(0.0, 0), (0.28, 0), (0.05, 0.1), (0.05, 0.9), (0.3, 1.2), (0.28, 1.5), (0.0, 1.5)], P['glass'], seg=10, kind='G')
for k in range(3):
    pendant(-12.8, -10.0 + k * 3.3, CY, CY - 3.2, col=P['teal2'] if k % 2 == 0 else P['brass'], r=0.95, glow=(k == 1))

# =======================================================================================================================================
# DINING (centre): table at (2,-5), chairs, chandelier, sideboard under the window, curtains
# =======================================================================================================================================
rug(2, -5, 13.0, 13.0, P['cream'], P['teal'], pattern=1, seed=7)
round_table(2, -5)
tea_set(2, -5)
dining_chair(2, -10.6, 'S', P['rose2'], P['walnut'])
dining_chair(2, 0.6, 'N', P['rose2'], P['walnut'])
dining_chair(-3.6, -5, 'E', P['teal2'], P['walnut'])
dining_chair(7.6, -5, 'W', P['teal2'], P['walnut'])
chandelier(2, -5, CY, CY - 3.6)
f = credenza(2, -15.0, 'S', 9.0, d=1.8, h=2.4)
vase(f, -3.2, FY + 2.55, 0, h=1.6, col=P['rose'], seed=12, big=True)
table_lamp(3.4, FY + 2.55, -15.0, base=P['teal2'], h=2.4)
f.b(-1.0, 0.8, FY + 2.55, FY + 2.7, -0.5, 0.5, P['brass'])
for k in range(3):
    f.sb(-0.8 + k * 0.3, -0.4 + k * 0.3, FY + 2.7 + k * 0.28, FY + 2.98 + k * 0.28, -0.4, 0.4, [P['rose2'], P['cream'], P['teal']][k], 0.04)
f.b(-0.6, 0.5, FY + 3.5, FY + 3.7, -0.3, 0.3, P['gold']) if False else None
curtains('S', 0, -16.0, -13.8, 13.8, FY + 10.2, FY + 0.3, P['rose'])
for k in range(5):                                                           # herbs on the sill
    plant_pot(F(-9.0 + k * 2.2, -15.3, 'S'), 0, 0, h=0.7, r=0.32, seed=20 + k, pot=P['terracotta']) if False else None
for k in range(4):
    x = -10.0 + k * 3.0
    lathe(x, -15.2, FY + 2.6, [(0.0, 0), (0.3, 0), (0.38, 0.6), (0.0, 0.62)], P['pot'], seg=10)
    for j in range(5):
        D.sphere(x + math.cos(j * 1.3) * 0.2, FY + 3.4, -15.2 + math.sin(j * 1.3) * 0.2, 0.2, 0.35, 0.2, P['green2'], seg=6, rings=4)
art('S', -18.0, -16.0, FY + 4.6, 4.0, 3.0, 41) if False else None

# =======================================================================================================================================
# LIVING (east): sofa, armchair, coffee table, TV wall, bookshelf, side tables, plants
# =======================================================================================================================================
rug(14.5, 10, 13.0, 9.6, P['cream'], P['teal2'], pattern=3, seed=14)
sofa(13.5, 4.4, 'S', 9.4, P['rose2'], shade(P['rose2'], 0.08))
coffee_table(14.5, 10.2, 'S', 6.2, 3.2)
armchair(6.6, 10.2, 'E', P['teal'])
side_table(7.8, 4.4, h=2.3, top=P['marble'])
table_lamp(7.8, FY + 2.3, 4.4, base=P['gold'], h=2.3)
side_table(21.0, 4.4, h=2.3, top=P['marble']) if False else None
floor_lamp(4.2, 13.4, h=7.0)
# TV wall
f = credenza(11.0, 15.0, 'N', 11.0, d=1.8, h=2.4, doors=4)
f.b(-3.0, 3.0, FY + 2.55, FY + 2.7, -0.4, 0.4, P['black'])
f.b(-3.9, 3.9, FY + 2.7, FY + 7.1, -0.35, 0.0, P['black'])
f.b(-3.7, 3.7, FY + 2.9, FY + 6.9, 0.0, 0.05, '#1B1F2B', 'G')
f.b(-1.5, 1.5, FY + 2.55, FY + 2.8, 0.6, 1.0, P['charcoal'])
f.b(4.0, 5.0, FY + 2.55, FY + 3.0, -0.4, 0.4, P['charcoal'])
vase(f, -5.0, FY + 2.55, 0, h=1.4, col=P['mustard'], seed=15)
vase(f, 4.8, FY + 3.0, 0, h=1.2, col=P['sky'], seed=16, flowers=False)
for k in range(3):                                                           # floating shelves with decor
    wb('N', 11 + (k - 1) * 4.2, FY + 8.0, 16.0, 3.2, 0.2, 0.9, P['walnut'])
    if k == 0:
        books(F(11 - 4.2, 15.4, 'N'), -1.4, 1.4, FY + 8.2, 0, 0.7, 60, maxh=1.2)
    elif k == 1:
        vase(F(11, 15.5, 'N'), 0, FY + 8.2, 0, h=1.0, col=P['rose'], seed=61)
    else:
        plant_pot(F(15.2, 15.5, 'N'), 0, 0, h=0.0, r=0.01, seed=62) if False else None
        D.sphere(15.2, FY + 8.9, 15.5, 0.55, 0.5, 0.55, P['green2'], seg=8, rings=5)
        lathe(15.2, 15.5, FY + 8.2, [(0.0, 0), (0.4, 0), (0.46, 0.5), (0.0, 0.52)], P['white'], seg=10)
# bookshelves on the east wall
bookshelf(21.3, -0.5, 'W', 6.0, 7.6, 70)
bookshelf(21.3, -14.0, 'W', 3.6, 7.6, 71) if False else None
art('W', 22.0, 4.7, FY + 5.4, 1.8, 2.4, 72) if False else None
# wall gallery on the east wall (north of the bedroom door) and over the credenza
for k, (pz, py, w, h) in enumerate(((-14.4, FY + 4.5, 2.4, 3.2), (-12.0, FY + 5.6, 1.8, 2.2), (-12.4, FY + 3.0, 1.6, 1.6), (-14.2, FY + 8.0, 1.8, 1.8))):
    art('W', 22.0, pz, py, w, h, 80 + k)
art('N', 18.0, 16.0, FY + 5.0, 3.0, 4.0, 90) if False else None
plant_pot(F(20.2, 14.6, 'S'), 0, 0, h=1.9, r=0.9, big=True, seed=90)
CYLC.append((20.2, FY + 3, 14.6, 2.2, 7, 'plant'))
plant_pot(F(20.3, -13.6, 'S'), 0, 0, h=2.0, r=1.0, big=True, seed=91, leaf=P['green'])
CYLC.append((20.3, FY + 3, -13.6, 2.4, 7, 'plant'))
plant_pot(F(-20.6, 1.2, 'S'), 0, 0, h=1.3, r=0.7, seed=92)
art('S', 14.0, -16.0, FY + 5.0, 3.4, 4.4, 93) if False else None
# reading corner: armchair + side table by the window (NE)
armchair(17.0, -13.0, 'S', P['mustard'])
side_table(13.9, -14.6, h=2.3, top=P['marble'])
vase(F(13.9, -14.6, 'S'), 0, FY + 2.3, 0, h=1.0, col=P['glass'], seed=94)
# a velvet ottoman by the armchair
# =======================================================================================================================================
# BEDROOM
# =======================================================================================================================================
rug(39.8, -6.5, 13.0, 11.0, P['blush'], P['rose2'], pattern=1, seed=24)
# bed: frame, tufted headboard, mattress, duvet, pillows, throw  (head toward the east wall; local +z = foot, local x = right)
f = F(41.0, -6.5, 'W')
f.b(-4.2, 4.2, FY + 0.5, FY + 1.6, -4.6, 4.6, P['walnut'])
for lx in (-4.0, 4.0):
    for lz in (-4.4, 4.4):
        f.lt(lx, lz, FY, [(0.0, 0), (0.28, 0), (0.22, 0.5), (0.2, 0.6)], P['walnut'], seg=8)
f.sb(-4.0, 4.0, FY + 1.6, FY + 2.7, -4.4, 4.4, P['white'], 0.2)                          # mattress
f.sb(-4.05, 4.05, FY + 2.7, FY + 3.25, -3.0, 4.5, P['rose'], 0.18)                       # duvet
f.sb(-4.15, 4.15, FY + 2.0, FY + 2.9, 2.6, 4.7, P['rose'], 0.14)                         # hanging foot
for k in range(6):                                                                       # duvet quilting lines
    f.b(-4.0, 4.0, FY + 3.25, FY + 3.3, -2.6 + k * 1.2, -2.5 + k * 1.2, shade(P['rose'], -0.12))
f.sb(-4.05, 4.05, FY + 3.2, FY + 3.4, 1.0, 2.6, P['teal2'], 0.06)                       # runner throw
f.b(-4.2, 4.2, FY + 1.5, FY + 6.4, -5.0, -4.6, P['walnut'])                              # headboard base
f.sb(-4.0, 4.0, FY + 1.9, FY + 6.2, -4.6, -4.25, P['rose2'], 0.2)                       # upholstered panel
for i in range(5):                                                                       # tufting buttons
    for j in range(3):
        f.sp(-3.2 + i * 1.6, FY + 3.2 + j * 1.2, -4.22, 0.12, 0.12, 0.06, P['gold'], seg=6, rings=4)
for i, lx in enumerate((-2.3, -0.4, 2.2)):                                                # pillows
    f.sb(lx - 0.95, lx + 0.95, FY + 3.0, FY + 4.4, -4.2, -2.8, [P['white'], P['cream'], P['white']][i], 0.3)
f.sb(-1.4, 1.4, FY + 3.4, FY + 4.4, -3.0, -2.2, P['teal2'], 0.2)
f.sb(0.5, 1.9, FY + 3.35, FY + 4.15, -3.0, -2.4, P['mustard'], 0.2)
f.col(-4.2, 4.2, FY, FY + 6.4, -5.0, 4.7, 'bed')
art('W', 46.0, -6.5, FY + 7.4, 5.0, 2.4, 100) if False else None
art('W', 46.0, -6.5, FY + 7.0, 4.6, 3.0, 101)
# nightstands with lamps
for k, sz in enumerate((-12.2, -0.8)):
    f2 = F(44.8, sz, 'W')
    f2.b(-1.3, 1.3, FY + 0.5, FY + 2.6, -1.0, 1.0, P['oak2'])
    for lx in (-1.1, 1.1):
        for lz in (-0.8, 0.8):
            f2.lt(lx, lz, FY, [(0.0, 0), (0.14, 0), (0.1, 0.55)], P['brass'], seg=8)
    f2.b(-1.2, 1.2, FY + 0.7, FY + 1.5, 1.0, 1.06, shade(P['oak2'], 0.12))
    f2.b(-1.2, 1.2, FY + 1.6, FY + 2.5, 1.0, 1.06, shade(P['oak2'], 0.12))
    handle(f2, -0.3, FY + 1.1, 1.06)
    handle(f2, -0.3, FY + 2.0, 1.06)
    f2.b(-1.4, 1.4, FY + 2.6, FY + 2.75, -1.1, 1.1, P['marble'])
    table_lamp(44.9, FY + 2.75, sz, base=P['gold'], h=2.5)
    books(f2, -0.8, 0.8, FY + 2.75, 0.2, 0.5, 110 + k, maxh=0.6)
    f2.col(-1.4, 1.4, FY, FY + 2.8, -1.1, 1.1, 'nightstand')
# wardrobe on the partition
f = F(31.0, 1.9, 'N')
f.b(-6.2, 6.2, FY, FY + 9.0, -1.1, 1.1, P['walnut'])
f.b(-6.4, 6.4, FY + 9.0, FY + 9.4, -1.2, 1.2, P['oak2'])
for i in range(4):
    x0 = -6.0 + i * 3.0
    f.b(x0 + 0.08, x0 + 2.92, FY + 0.5, FY + 8.6, 1.1, 1.18, shade(P['walnut'], 0.14))
    f.b(x0 + 0.4, x0 + 2.6, FY + 0.9, FY + 4.3, 1.18, 1.22, shade(P['walnut'], 0.24))
    f.b(x0 + 0.4, x0 + 2.6, FY + 4.7, FY + 8.2, 1.18, 1.22, shade(P['walnut'], 0.24))
    handle(f, x0 + (2.2 if i % 2 == 0 else 0.7), FY + 4.3, 1.22, vertical=True)
f.col(-6.4, 6.4, FY, FY + 9.4, -1.2, 1.2, 'wardrobe')
# dressing table with mirror and stool (west wall, north corner)
f = F(24.0, -10.5, 'E')
f.b(0, 5.0, FY + 2.4, FY + 2.6, -1.1, 1.1, P['white'])
f.b(0.1, 4.9, FY + 1.5, FY + 2.4, -1.0, 1.0, P['white'])
for lx in (0.3, 4.7):
    for lz in (-0.8, 0.8):
        f.lt(lx, lz, FY, [(0.0, 0), (0.16, 0), (0.1, 1.5)], P['brass'], seg=8)
for k in range(2):
    f.b(0.4 + k * 2.3, 2.5 + k * 2.3, FY + 1.6, FY + 2.3, 1.0, 1.06, shade(P['white'], -0.05))
    handle(f, 1.2 + k * 2.3, FY + 1.95, 1.06)
for k, c in enumerate((P['rose'], P['sky'], P['gold'], P['lilac'])):                    # perfumes and cosmetics
    f.lt(0.6 + k * 0.6, 0.2, FY + 2.6, [(0.0, 0), (0.22, 0), (0.24, 0.6), (0.1, 0.9), (0.1, 1.1)], c, seg=8, kind='G' if k % 2 == 0 else 'O')
f.b(3.4, 4.6, FY + 2.6, FY + 2.7, -0.7, 0.7, P['gold'])
f.sb(3.5, 4.5, FY + 2.7, FY + 3.2, -0.4, 0.4, P['rose2'], 0.1)
f.col(0, 5.0, FY, FY + 2.7, -1.1, 1.1, 'dresser')
mirror('E', 23.0, -13.0, FY + 4.0, 3.8, 5.6, seed=3)
for k, sz in enumerate((-11.0, -15.0)):
    wb('E', 23.0, FY + 5.5, sz, 0.5, 0.5, 0.6, P['brass'])
    D.sphere(23.7, FY + 5.9, sz, 0.35, 0.4, 0.35, '#FFF1C8', seg=7, rings=5, kind='N')
spot(24.5, FY + 6.2, -13, 18, 0.6)
lathe(27.2, -13.0, FY, [(0.0, 0), (1.1, 0), (1.0, 0.1), (0.8, 1.3), (1.2, 1.7), (0.0, 1.8)], P['rose2'], seg=16)    # stool
CYLC.append((27.2, FY + 1, -13.0, 2.4, 2, 'stool'))
# window seat armchair + lamp
armchair(31.0, -13.2, 'S', P['teal'])
floor_lamp(35.6, -14.2, h=6.5)
curtains('S', 0, -16.0, 28.5, 37.5, FY + 10.2, FY + 0.3, P['lilac'])
# bench at the foot of the bed
f = F(35.2, -6.5, 'W')
f.sb(-3.4, 3.4, FY + 1.5, FY + 2.1, -0.8, 0.8, P['teal'], 0.12)
for lx in (-3.1, 3.1):
    for lz in (-0.6, 0.6):
        f.lt(lx, lz, FY, [(0.0, 0), (0.15, 0), (0.12, 1.5)], P['brass'], seg=8)
f.col(-3.4, 3.4, FY, FY + 2.1, -0.8, 0.8, 'bench')
# bedroom plants and a laundry basket / slippers / hat boxes
plant_pot(F(41.5, 1.2, 'S'), 0, 0, h=1.9, r=0.9, big=True, seed=120, leaf=P['green'])
CYLC.append((41.5, FY + 3, 1.2, 2.2, 7, 'plant'))
for k, (c, r_) in enumerate(((P['rose'], 1.2), (P['cream'], 1.0), (P['teal'], 0.8))):
    lathe(24.4, -0.8, FY + k * 1.05, [(0.0, 0), (r_, 0), (r_, 0.95), (r_ - 0.1, 1.0), (0.0, 1.0)], c, seg=14)
    ring(24.4, FY + k * 1.05 + 0.5, -0.8, r_, 0.04, 'xz', P['gold'], seg=14, tseg=4)
CYLC.append((24.4, FY + 1.6, -0.8, 2.4, 3.2, 'hatboxes'))
f = F(38.0, -6.5, 'W')
for k in range(2):                                                                         # slippers
    f.sb(-1.9 + k * 3.0, -1.2 + k * 3.0, 0.0, 0.5, 6.0, 7.0, P['rose'], 0.08) if False else None
art('E', 23.0, -3.0, FY + 5.0, 2.6, 3.4, 130)
art('S', 25.0, -16.0, FY + 6.0, 1.8, 2.4, 131) if False else None

# =======================================================================================================================================
# BATHROOM
# =======================================================================================================================================
rug(30.0, 9.5, 7.0, 3.2, P['cream'], P['teal2'], pattern=2, seed=30)
# vanity with two vessel basins, mirrors, sconces
f = F(32.0, 5.1, 'S')
f.b(-5.5, 5.5, FY + 0.6, FY + 3.2, -1.1, 1.1, P['teal'])
for lx in (-5.2, 5.2):
    f.lt(lx, 0.8, FY, [(0.0, 0), (0.15, 0), (0.1, 0.6)], P['brass'], seg=8)
f.b(-5.7, 5.7, FY + 3.2, FY + 3.45, -1.2, 1.2, P['marble'])
for i in range(4):
    f.b(-5.3 + i * 2.7, -3.0 + i * 2.7, FY + 0.8, FY + 3.0, 1.1, 1.16, shade(P['teal'], 0.14))
    handle(f, -4.4 + i * 2.7, FY + 2.0, 1.16, vertical=False) if False else None
    f.b(-4.4 + i * 2.7, -3.9 + i * 2.7, FY + 2.0, FY + 2.1, 1.16, 1.28, P['brass'])
for sx in (-2.6, 2.6):
    f.lt(sx, 0.2, FY + 3.45, [(0.0, 0), (0.7, 0), (0.95, 0.2), (1.0, 0.6), (0.9, 0.6), (0.0, 0.3)], P['white'], seg=18)
    f.cy(sx, -0.7, FY + 3.45, FY + 4.9, 0.1, P['brass'], seg=8)
    f.hc(sx, FY + 4.9, -0.4, 'z', 0.7, 0.09, P['brass'], seg=8)
f.col(-5.7, 5.7, FY, FY + 3.5, -1.2, 1.2, 'vanity')
for sx in (28.6, 35.4):
    mirror('S', sx, 4.0, FY + 4.5, 4.4, 4.8, seed=4)
    for k in (-1, 1):
        wb('S', sx + k * 2.7, FY + 6.0, 4.0, 0.5, 0.5, 0.5, P['brass'])
        D.sphere(sx + k * 2.7, FY + 6.5, 4.8, 0.32, 0.4, 0.32, '#FFF1C8', seg=7, rings=5, kind='N')
spot(32, FY + 7.0, 5.5, 22, 1.0)
# towels, soaps, toothbrush cups, plant on the vanity
f.b(3.8, 5.0, FY + 3.45, FY + 3.75, -0.5, 0.5, P['rose'])
f.b(3.9, 4.9, FY + 3.75, FY + 3.9, -0.4, 0.4, P['cream'])
f.lt(-0.2, 0.3, FY + 3.45, [(0.0, 0), (0.3, 0), (0.3, 0.7), (0.0, 0.7)], P['glass'], seg=10, kind='G')
plant_pot(f, -5.0, 0.0, h=0.0, r=0.01) if False else None
D.sphere(27.6, FY + 4.3, 5.0, 0.4, 0.5, 0.4, P['green2'], seg=8, rings=5)
# freestanding tub under the window
f = F(34.5, 13.2, 'N')
f.b(-3.5, 3.5, FY + 0.35, FY + 2.0, -1.5, 1.5, P['white'])
f.cy(-3.5, 0, FY + 0.35, FY + 2.0, 1.5, P['white'], seg=20)
f.cy(3.5, 0, FY + 0.35, FY + 2.0, 1.5, P['white'], seg=20)
f.b(-3.2, 3.2, FY + 1.98, FY + 2.04, -1.2, 1.2, '#9FD3E6', 'G')
f.cy(-3.2, 0, FY + 1.98, FY + 2.04, 1.2, '#9FD3E6', seg=20, kind='G')
f.cy(3.2, 0, FY + 1.98, FY + 2.04, 1.2, '#9FD3E6', seg=20, kind='G')
for lx in (-3.4, 3.4):
    f.lt(lx, 0.0, FY, [(0.0, 0), (0.4, 0), (0.3, 0.2), (0.3, 0.4)], P['brass'], seg=10)
f.cy(3.9, 0.0, FY + 2.0, FY + 4.0, 0.12, P['brass'], seg=8)
f.hc(3.4, FY + 4.0, 0.0, 'x', 1.0, 0.1, P['brass'], seg=8)
for k in range(3):
    D.sphere(0.8 + k * 0.5, FY + 2.15, 0.2, 0.3, 0.12, 0.3, P['white'], seg=7, rings=4)                    # foam
f.col(-5.0, 5.0, FY, FY + 2.1, -1.5, 1.5, 'tub')
# bath caddy with candles
f.b(-0.4, 0.4, FY + 2.0, FY + 2.12, -1.9, 1.9, P['brass']) if False else None
# shower cabin in the north-east corner
box(41.0, 46.0, FY, FY + 0.3, 4.0, 10.0, P['marble2'])
box(41.0, 41.1, FY + 0.3, FY + 8.6, 4.0, 10.0, P['glass'], 'G')
box(41.0, 46.0, FY + 0.3, FY + 8.6, 9.9, 10.0, P['glass'], 'G')
box(40.9, 41.2, FY + 0.3, FY + 8.8, 9.8, 10.1, P['brass'])
box(40.9, 41.2, FY + 8.6, FY + 8.8, 4.0, 10.1, P['brass'])
box(40.9, 46.0, FY + 8.6, FY + 8.8, 9.8, 10.1, P['brass'])
wb('S', 41.0, FY + 0.3, 4.0, 0.0, 0.0, 0.0, P['wall']) if False else None
box(41.0, 42.0, FY + 0.3, FY + 6.0, 9.9, 10.0, P['white'], 'G') if False else None
box(41.2, 41.7, FY + 3.2, FY + 3.4, 9.7, 9.9, P['brass'])              # door handle
cyl(45.5, 7.0, FY + 7.2, FY + 8.6, 0.1, P['brass'], seg=8)
lathe(45.5, 7.0, FY + 8.5, [(0.0, 0), (0.15, 0.0), (0.9, 0.2), (0.9, 0.3), (0.0, 0.3)], P['brass'], seg=16)
cyl(46.0, 6.0, FY + 3.4, FY + 5.0, 0.1, P['brass'], seg=8) if False else None
box(45.5, 46.0, FY + 3.2, FY + 3.5, 5.0, 6.0, P['brass'])
collider(41.0, 46.0, FY, FY + 8.8, 9.7, 10.2, 'shower_glass')
# toilet (back to the south wall)
f = F(42.5, 15.2, 'N')
f.b(-0.9, 0.9, FY, FY + 3.4, -0.8, 0.0, P['white'])
f.lt(0, 1.0, FY, [(0.0, 0), (0.8, 0), (0.95, 0.3), (0.95, 1.2), (0.8, 2.0), (0.0, 2.0)], P['white'], seg=16)
f.cy(0, 1.0, FY + 2.0, FY + 2.15, 0.95, P['cream'], seg=16)
f.b(-0.7, 0.7, FY + 3.4, FY + 3.55, -0.8, 0.0, P['white'])
f.sp(0.6, FY + 3.6, -0.4, 0.18, 0.1, 0.18, P['brass'], seg=6, rings=4)
f.col(-1.0, 1.0, FY, FY + 3.6, -0.9, 2.0, 'toilet')
# shelves above the toilet and towel rail on the west wall
wb('N', 42.5, FY + 6.0, 16.0, 3.6, 0.2, 0.9, P['walnut'])
wb('N', 42.5, FY + 7.8, 16.0, 3.6, 0.2, 0.9, P['walnut'])
for k in range(3):
    f.lt(-1.2 + k * 1.2, 0.5, 0, [(0.0, 0), (0.3, 0), (0.3, 0.8), (0.0, 0.8)], [P['white'], P['rose'], P['teal2']][k], seg=8) if False else None
    D.sphere(41.3 + k * 1.2, FY + 6.7, 15.5, 0.3, 0.45, 0.3, [P['white'], P['rose'], P['sky']][k], seg=8, rings=5)
for k in range(5):
    wb('E', 23.0, FY + 3.0 + k * 0.9, 13.5, 0.15, 0.15, 0.7, P['brass']) if False else None
    wb('E', 23.0, FY + 3.2 + k * 0.9, 13.5, 2.6, 0.12, 0.35, P['metal'])
wb('E', 23.0, FY + 3.0, 12.3, 0.12, 4.0, 0.35, P['metal'])
wb('E', 23.0, FY + 3.0, 14.7, 0.12, 4.0, 0.35, P['metal'])
for k, c in enumerate((P['rose'], P['cream'], P['teal2'])):
    wb('E', 23.3, FY + 3.8 + k * 0.9, 13.5, 2.2, 0.8, 0.18, c, off=0.1)
lathe(25.2, 5.1, FY, [(0.0, 0), (1.0, 0), (1.1, 2.0), (1.0, 2.1), (0.0, 2.1)], P['oak3'], seg=12)       # laundry basket
CYLC.append((25.2, FY + 1.0, 5.1, 2.2, 2.2, 'basket'))
plant_pot(F(25.4, 14.7, 'S'), 0, 0, h=1.5, r=0.8, big=True, seed=140)
CYLC.append((25.4, FY + 3, 14.7, 1.9, 6, 'plant'))
art('W', 46.0, 13.4, FY + 4.6, 2.6, 3.4, 141) if False else None
spot(34, CY - 1.5, 10, 24, 0.9)
spot(34, CY - 1.5, 1, 22, 0.8)

# =======================================================================================================================================
# extra decor: bar cart, wall sconces, hanging plants, wall shelves, cushions, magazine rack
# =======================================================================================================================================
def sconce(n, px, pz, y, glow=True):
    wb(n, px, y, pz, 0.7, 1.4, 0.18, P['brass'])
    wb(n, px, y + 0.4, pz, 0.14, 0.14, 0.9, P['brass'], off=0.1)
    ox = {'S': (px, pz + 1.0), 'N': (px, pz - 1.0), 'E': (px + 1.0, pz), 'W': (px - 1.0, pz)}[n]
    lathe(ox[0], ox[1], y + 0.6, [(0.0, 0), (0.3, 0), (0.7, 1.2), (0.62, 1.25), (0.25, 0.1)], P['cream'], seg=14)
    D.sphere(ox[0], y + 1.0, ox[1], 0.25, 0.32, 0.25, '#FFF1C8', seg=7, rings=5, kind='N')
    if glow:
        spot(ox[0], y + 1.2, ox[1], 14, 0.6)


for sx in (3.2, 18.8):
    sconce('N', sx, 16.0, FY + 6.2, glow=(sx > 10))
sconce('E', -22.0, 3.0, FY + 5.5, glow=False)
sconce('E', -22.0, 9.5, FY + 7.0, glow=False) if False else None
sconce('S', -8.2, -16.0, FY + 5.6, glow=False)
sconce('S', 8.6, -16.0, FY + 5.6, glow=False)
sconce('W', 22.0, -3.5, FY + 8.6, glow=False) if False else None

# bar cart (between the hall and the dining area)
f = F(0.6, 12.8, 'N')
for lx in (-1.4, 1.4):
    for lz in (-0.7, 0.7):
        f.b(lx - 0.05, lx + 0.05, FY + 0.3, FY + 3.0, lz - 0.05, lz + 0.05, P['brass'])
        f.lt(lx, lz, FY, [(0.0, 0), (0.28, 0), (0.28, 0.3), (0.0, 0.3)], P['black'], seg=10)
for y in (FY + 0.7, FY + 2.0, FY + 3.0):
    f.b(-1.55, 1.55, y, y + 0.12, -0.85, 0.85, P['glass'] if y > FY + 2.5 else P['marble'], 'G' if y > FY + 2.5 else 'O')
    f.b(-1.6, 1.6, y - 0.03, y + 0.15, -0.9, 0.9, P['brass']) if False else None
f.b(1.5, 1.7, FY + 2.0, FY + 3.6, -0.8, 0.8, P['brass'])
for k, c in enumerate((P['green'], P['mustard'], P['rose2'], P['sky'])):
    f.lt(-1.1 + k * 0.5, 0.2, FY + 2.12, [(0.0, 0), (0.18, 0), (0.2, 0.9), (0.1, 1.1), (0.1, 1.5), (0.0, 1.5)], c, seg=10, kind='G')
for k in range(3):
    f.lt(0.5 + k * 0.45, -0.1, FY + 3.12, [(0.0, 0), (0.2, 0), (0.05, 0.3), (0.05, 0.7), (0.22, 0.95), (0.0, 0.95)], P['glass'], seg=10, kind='G')
f.lt(-0.5, 0.0, FY + 3.12, [(0.0, 0), (0.4, 0), (0.45, 0.6), (0.0, 0.62)], P['metal'], seg=12)
f.col(-1.7, 1.7, FY, FY + 3.7, -0.9, 0.9, 'barcart')
# hanging plants (pots on chains with trailing vines)
for (hx, hz, sd) in ((-17.5, -14.8, 150), (8.5, -14.6, 151), (45.0, -14.5, 152)):
    cyl(hx, hz, CY - 3.2, CY, 0.03, P['black'], seg=6)
    lathe(hx, hz, CY - 4.4, [(0.0, 0), (0.5, 0), (0.7, 0.3), (0.78, 1.1), (0.0, 1.1)], P['cream'], seg=14)
    rs_ = rnd_of(sd)
    for k in range(9):
        a = k * 0.7
        ln = rs_.uniform(1.5, 3.4)
        for j in range(int(ln / 0.5)):
            D.sphere(hx + math.cos(a) * (0.5 + j * 0.06), CY - 4.4 - j * 0.5, hz + math.sin(a) * (0.5 + j * 0.06), 0.22, 0.22, 0.22, P['green2'] if j % 2 else P['green'], seg=6, rings=4)
    D.sphere(hx, CY - 3.9, hz, 0.7, 0.45, 0.7, P['green'], seg=8, rings=5)
# floating shelves with jars above the island side and in the hall
for k in range(2):
    wb('E', -22.0, FY + 5.0 + k * 0.0, -1.0 - k * 0.0, 0.01, 0.01, 0.01, P['wall']) if False else None
wb('N', -2.0, FY + 6.0, 16.0, 3.4, 0.2, 0.9, P['walnut'])
wb('N', -2.0, FY + 8.0, 16.0, 3.4, 0.2, 0.9, P['walnut'])
for k in range(3):
    lathe(-3.2 + k * 1.1, 15.4, FY + 6.2, [(0.0, 0), (0.35, 0), (0.4, 0.8), (0.0, 0.85)], P['glass'], seg=10, kind='G')
    D.sphere(-3.2 + k * 1.1, FY + 6.9, 15.4, 0.3, 0.25, 0.3, [P['rose'], P['mustard'], P['cream']][k], seg=8, rings=5)
books(F(-2.0, 15.4, 'N'), -1.4, 1.4, FY + 8.2, 0, 0.7, 160, maxh=1.2)
# floor cushions and a magazine rack by the sofa
for k, c in enumerate((P['mustard'], P['teal2'])):
    lathe(19.0 + k * 0.0, 8.8 - k * 1.8 if False else 11.8 + k * 0.0, FY, [(0.0, 0), (1.0, 0), (1.15, 0.45), (1.0, 0.8), (0.0, 0.85)], c, seg=16) if False else None
f = F(21.0, 12.6, 'W')
f.b(-0.9, 0.9, FY, FY + 1.6, -0.5, 0.5, P['oak2'])
f.b(-0.8, 0.8, FY + 0.3, FY + 1.5, -0.4, 0.4, P['cream'])
for k, c in enumerate((P['rose2'], P['teal'], P['mustard'])):
    f.b(-0.7 + k * 0.5, -0.4 + k * 0.5, FY + 0.5, FY + 1.7, -0.3, 0.05, c)
f.col(-0.9, 0.9, FY, FY + 1.7, -0.5, 0.5, 'magrack')
# throw blanket over the reading chair and a small footstool
f = F(17.0, -13.0, 'S')
f.sb(-1.4, 1.4, FY + 1.5, FY + 1.7, -1.2, 0.4, P['blush'], 0.05)
f.b(-1.4, -0.6, FY + 1.5, FY + 3.4, -1.15, -1.0, P['blush'])
ottoman(17.0, -10.3, P['mustard'], 0.7)

exec(compile(open(os.path.join(HERE, 'details.py'), encoding='utf-8').read(), 'details.py', 'exec'))

# =======================================================================================================================================
# anchors, seats, tags are created in Studio from these
# =======================================================================================================================================
anchor('arrival', -14, FY, 12, 0, -1)
anchor('exit_door', -14, FY + 4, 16.4, 0, 1)
anchor('mistress_seat', 2, FY + 1.8, -10.6, 0, 1)
anchor('guest_seat', 2, FY + 1.8, 0.6, 0, -1)
anchor('table_top', 2, FY + 3.1, -5, 0, 1)
