# Layout of flat 2 (exec'd by build_flat2.py after furn2.py).  Interior clear sizes (floor top FY = 1, ceiling underside CY = 12):
#   main studio  x -24..24, z -17..17   (hall SW, kitchen W/NW, executive desk N, lounge SE)
#   bedroom      x  25..45, z -17..2
#   bathroom     x  25..45, z   3..17
# Walls are 1.0 thick: north z = -17.5, south z = 17.5, west x = -24.5, partition x = 24.5, far east x = 45.5, bedroom/bath partition z = 2.5.
TH = 1.0
SKY_OBJ = []                                  # skyline boxes (outside the rooms, not audited)


def pick(c, x):
    return c(x) if callable(c) else c


def wall_x(zc, x0, x1, ops, colA, colB, name, brk=()):
    """wall along x; A = the skin at lower z, B = the skin at higher z; ops = [(xa, xb, ya, yb)] openings (absolute y)"""
    xs = sorted(set([x0, x1] + [o[0] for o in ops] + [o[1] for o in ops] + list(brk)))
    for a, b in zip(xs[:-1], xs[1:]):
        mid = (a + b) / 2
        cov = [o for o in ops if o[0] <= mid <= o[1]]
        ca, cb = pick(colA, mid), pick(colB, mid)
        parts = []
        if not cov:
            parts.append((FY - 1, CY + 1))
        else:
            o = cov[0]
            if o[2] > FY:
                parts.append((FY - 1, o[2]))
            if o[3] < CY:
                parts.append((o[3], CY + 1))
        for (ya, yb) in parts:
            box(a, b, ya, yb, zc - TH / 2, zc, ca)
            box(a, b, ya, yb, zc, zc + TH / 2, cb)
            collider(a, b, max(ya, FY), min(yb, CY), zc - TH / 2, zc + TH / 2, name)


def wall_z(xc, z0, z1, ops, colA, colB, name, brk=()):
    """wall along z; A = skin at lower x, B = skin at higher x; ops = [(za, zb, ya, yb)]"""
    zs = sorted(set([z0, z1] + [o[0] for o in ops] + [o[1] for o in ops] + list(brk)))
    for a, b in zip(zs[:-1], zs[1:]):
        mid = (a + b) / 2
        cov = [o for o in ops if o[0] <= mid <= o[1]]
        ca, cb = pick(colA, mid), pick(colB, mid)
        parts = []
        if not cov:
            parts.append((FY - 1, CY + 1))
        else:
            o = cov[0]
            if o[2] > FY:
                parts.append((FY - 1, o[2]))
            if o[3] < CY:
                parts.append((o[3], CY + 1))
        for (ya, yb) in parts:
            box(xc - TH / 2, xc, ya, yb, a, b, ca)
            box(xc, xc + TH / 2, ya, yb, a, b, cb)
            collider(xc - TH / 2, xc + TH / 2, max(ya, FY), min(yb, CY), a, b, name)


def trim_x(zface, s, x0, x1, ops, door_ops):
    """baseboard + crown on a wall face along x (room on the side s of the face)"""
    for (a, b) in split_range(x0, x1, [(o[0], o[1]) for o in door_ops]):
        box(a, b, FY, FY + 0.8, min(zface, zface + s * 0.25), max(zface, zface + s * 0.25), P['white'])
        box(a, b, FY + 0.8, FY + 0.95, min(zface, zface + s * 0.15), max(zface, zface + s * 0.15), shade(P['white'], -0.04))
    box(x0, x1, CY - 0.55, CY, min(zface, zface + s * 0.4), max(zface, zface + s * 0.4), P['white'])
    box(x0, x1, CY - 0.7, CY - 0.55, min(zface, zface + s * 0.25), max(zface, zface + s * 0.25), shade(P['white'], -0.04))


def trim_z(xface, s, z0, z1, door_ops):
    for (a, b) in split_range(z0, z1, [(o[0], o[1]) for o in door_ops]):
        box(min(xface, xface + s * 0.25), max(xface, xface + s * 0.25), FY, FY + 0.8, a, b, P['white'])
        box(min(xface, xface + s * 0.15), max(xface, xface + s * 0.15), FY + 0.8, FY + 0.95, a, b, shade(P['white'], -0.04))
    box(min(xface, xface + s * 0.4), max(xface, xface + s * 0.4), CY - 0.55, CY, z0, z1, P['white'])
    box(min(xface, xface + s * 0.25), max(xface, xface + s * 0.25), CY - 0.7, CY - 0.55, z0, z1, shade(P['white'], -0.04))


def casing_x(zc, xa, xb, top, sides=(-1, 1)):
    """door casing on both faces of a wall along x (white jambs and header, 0.45 wide, 0.3 proud)"""
    for s in sides:
        zf = zc + s * TH / 2
        z0, z1 = (zf, zf + s * 0.3) if s > 0 else (zf + s * 0.3, zf)
        box(xa - 0.45, xa, FY, top + 0.5, z0, z1, P['white'])
        box(xb, xb + 0.45, FY, top + 0.5, z0, z1, P['white'])
        box(xa, xb, top, top + 0.5, z0, z1, P['white'])


def casing_z(xc, za, zb, top, sides=(-1, 1)):
    for s in sides:
        xf = xc + s * TH / 2
        x0, x1 = (xf, xf + s * 0.3) if s > 0 else (xf + s * 0.3, xf)
        box(x0, x1, FY, top + 0.5, za - 0.45, za, P['white'])
        box(x0, x1, FY, top + 0.5, zb, zb + 0.45, P['white'])
        box(x0, x1, top, top + 0.5, za, zb, P['white'])


def window_x(zc, xa, xb, ya, yb, sides=(-1, 1), mull=6.0, frosted=False):
    """window in a wall along x: glass 0.2 thick (collider 0.5), white frame, mullions every `mull`, sill on both sides"""
    gcol = '#DCEBF5' if frosted else P['glass']
    box(xa, xb, ya, yb, zc - 0.1, zc + 0.1, gcol, 'G')
    collider(xa, xb, ya, yb, zc - 0.25, zc + 0.25, 'glass')
    n = max(1, int(round((xb - xa) / mull)))
    for s in sides:
        zf = zc + s * TH / 2
        z0, z1 = (zf, zf + s * 0.3) if s > 0 else (zf + s * 0.3, zf)
        box(xa, xb, ya, ya + 0.35, z0, z1, P['white'])
        box(xa, xb, yb - 0.35, yb, z0, z1, P['white'])
        box(xa, xa + 0.35, ya, yb, z0, z1, P['white'])
        box(xb - 0.35, xb, ya, yb, z0, z1, P['white'])
        for k in range(1, n):
            u = xa + k * (xb - xa) / n
            box(u - 0.16, u + 0.16, ya, yb, z0, z1, P['white'])
        box(xa - 0.3, xb + 0.3, ya - 0.3, ya, min(zf, zf + s * 0.9), max(zf, zf + s * 0.9), shade(P['white'], -0.04))
    # the frame also bridges the wall thickness around the glass
    box(xa, xb, ya, ya + 0.35, zc - TH / 2, zc + TH / 2, P['white']) if False else None


def window_z(xc, za, zb, ya, yb, sides=(-1, 1), mull=6.0, frosted=False):
    gcol = '#DCEBF5' if frosted else P['glass']
    box(xc - 0.1, xc + 0.1, ya, yb, za, zb, gcol, 'G')
    collider(xc - 0.25, xc + 0.25, ya, yb, za, zb, 'glass')
    n = max(1, int(round((zb - za) / mull)))
    for s in sides:
        xf = xc + s * TH / 2
        x0, x1 = (xf, xf + s * 0.3) if s > 0 else (xf + s * 0.3, xf)
        box(x0, x1, ya, ya + 0.35, za, zb, P['white'])
        box(x0, x1, yb - 0.35, yb, za, zb, P['white'])
        box(x0, x1, ya, yb, za, za + 0.35, P['white'])
        box(x0, x1, ya, yb, zb - 0.35, zb, P['white'])
        for k in range(1, n):
            u = za + k * (zb - za) / n
            box(x0, x1, ya, yb, u - 0.16, u + 0.16, P['white'])
        box(min(xf, xf + s * 0.9), max(xf, xf + s * 0.9), ya - 0.3, ya, za - 0.3, zb + 0.3, shade(P['white'], -0.04))


# ---------------------------------------------------------------------------------------------------------------------------------------
# structure
# ---------------------------------------------------------------------------------------------------------------------------------------
X0, X1, Z0, Z1 = -24.5, 45.5, -17.5, 17.5                       # outer faces of the wall centre lines
box(X0 - 0.55, X1 + 0.55, FY - 1.2, FY - 0.04, Z0 - 0.55, Z1 + 0.55, P['joint'])                       # floor slab (tiles / planks sit 0.02 on top)
collider(X0 - 0.55, X1 + 0.55, FY - 1.2, FY, Z0 - 0.55, Z1 + 0.55, 'floor')
box(X0 - 0.55, X1 + 0.55, CY, CY + 1.2, Z0 - 0.55, Z1 + 0.55, P['ceil'])
collider(X0 - 0.55, X1 + 0.55, CY, CY + 1.2, Z0 - 0.55, Z1 + 0.55, 'ceiling')

# openings
PANO = (-5.0, 21.0, FY + 3.4, CY - 1.0)                                     # panoramic window of the studio (north wall)
BEDWIN = (30.0, 40.0, FY + 4.0, CY - 1.5)
EXITD = (-19.0, -13.0, FY, FY + 8.0)                                        # exit door (south wall)
BATHWIN = (38.0, 43.0, FY + 7.0, CY - 1.5)                                  # frosted (south wall)
KWIN = (-12.0, -4.0, FY + 4.4, FY + 8.6)                                    # kitchen window (west wall, over the sink)
BEDDOOR = (-9.5, -2.5, FY, FY + 8.0)                                        # partition x = 24.5
BATHDOOR = (7.5, 14.5, FY, FY + 8.0)

# wall colours: main studio blue-grey, hall cream, TV wall navy, kitchen cream; bedroom steel blue with a navy headboard wall; bathroom white tile
def north_in(x):
    return P['wall2'] if x < -5 else (P['wall'] if x < 24.5 else (P['wall3']))


def south_in(x):
    if x < -8:
        return P['wall2']
    if x < 24.5:
        return P['navy']
    return P['tileW']


wall_x(Z0, X0, X1, [PANO, BEDWIN], P['concrete'], north_in, 'wall_n', brk=(-5.0, 24.5))
wall_x(Z1, X0, X1, [EXITD, BATHWIN], south_in, P['concrete'], 'wall_s', brk=(-8.0, 24.5))
wall_z(X0, Z0, Z1, [(KWIN[0], KWIN[1], KWIN[2], KWIN[3])], P['concrete'], P['wall2'], 'wall_w')
wall_z(24.5, Z0, Z1, [(BEDDOOR[0], BEDDOOR[1], BEDDOOR[2], BEDDOOR[3]), (BATHDOOR[0], BATHDOOR[1], BATHDOOR[2], BATHDOOR[3])],
       P['wall3'], lambda z: P['wall3'] if z < 2.5 else P['tileW'], 'wall_e', brk=(2.5,))
wall_z(X1, Z0, Z1, [], lambda z: P['navy'] if z < 2.5 else P['tileW'], P['concrete'], 'wall_far')
wall_x(2.5, 25.0, 45.0, [], P['wall3'], P['tileW'], 'wall_mid')

# windows, casings, trims
window_x(Z0, PANO[0], PANO[1], PANO[2], PANO[3], sides=(1,), mull=6.5)
window_x(Z0, BEDWIN[0], BEDWIN[1], BEDWIN[2], BEDWIN[3], sides=(1,), mull=5.0)
window_x(Z1, BATHWIN[0], BATHWIN[1], BATHWIN[2], BATHWIN[3], sides=(-1,), mull=5.0, frosted=True)
window_z(X0, KWIN[0], KWIN[1], KWIN[2], KWIN[3], sides=(1,), mull=4.0)
casing_x(Z1, EXITD[0], EXITD[1], EXITD[3], sides=(-1,))
casing_z(24.5, BEDDOOR[0], BEDDOOR[1], BEDDOOR[3])
casing_z(24.5, BATHDOOR[0], BATHDOOR[1], BATHDOOR[3])
trim_x(Z0 + TH / 2, 1, -24.0, 24.0, [PANO], [])
trim_x(Z0 + TH / 2, 1, 25.0, 45.0, [BEDWIN], [])
trim_x(Z1 - TH / 2, -1, -24.0, 24.0, [], [EXITD])
trim_x(Z1 - TH / 2, -1, 25.0, 45.0, [], [])
trim_z(X0 + TH / 2, 1, -17.0, 17.0, [])
trim_z(24.5 - TH / 2, -1, -17.0, 17.0, [(BEDDOOR[0], BEDDOOR[1]), (BATHDOOR[0], BATHDOOR[1])])
trim_z(24.5 + TH / 2, 1, -17.0, 2.0, [(BEDDOOR[0], BEDDOOR[1])])
trim_z(24.5 + TH / 2, 1, 3.0, 17.0, [(BATHDOOR[0], BATHDOOR[1])])
trim_z(X1 - TH / 2, -1, -17.0, 2.0, [])
trim_z(X1 - TH / 2, -1, 3.0, 17.0, [])
trim_x(2.5 - TH / 2, -1, 25.0, 45.0, [], [])
trim_x(2.5 + TH / 2, 1, 25.0, 45.0, [], [])

# exit door leaf (closed, navy with panels and a brass handle on the room side)
ex0, ex1 = EXITD[0] + 0.05, EXITD[1] - 0.05
box(ex0, ex1, FY, EXITD[3] - 0.05, Z1 - 0.2, Z1 + 0.2, P['navy'])
for k in range(2):
    px0 = ex0 + 0.5 + k * 2.75
    box(px0, px0 + 2.45, FY + 0.7, FY + 3.6, Z1 - 0.26, Z1 - 0.2, P['navy2'])
    box(px0, px0 + 2.45, FY + 4.1, FY + 7.0, Z1 - 0.26, Z1 - 0.2, P['navy2'])
box(ex1 - 1.0, ex1 - 0.7, FY + 3.6, FY + 4.4, Z1 - 0.45, Z1 - 0.26, P['brass'])
box(ex1 - 1.15, ex1 - 0.55, FY + 4.0, FY + 4.1, Z1 - 0.45, Z1 - 0.26, P['brass'])
collider(ex0, ex1, FY, EXITD[3] - 0.05, Z1 - 0.2, Z1 + 0.2, 'door_leaf')

# ---- floors: wood (main + bedroom), 3-tone tile (hall, kitchen, bath)
def floor_wood(x0, x1, z0, z1, seed=0):
    r = rnd_of(seed)
    z = z0
    cols = [P['wood'], P['wood2'], P['wood3']]
    row = 0
    while z < z1 - 0.01:
        zw = min(1.7, z1 - z)
        x = x0 + (row % 3) * 2.3 * (-1)
        while x < x1:
            ln = r.uniform(5.5, 11.0)
            a, b = max(x, x0), min(x + ln, x1)
            if b - a > 0.3:
                box(a + 0.03, b - 0.03, FY - 0.02, FY, z + 0.035, z + zw - 0.035, r.choice(cols))
            x += ln
        z += zw
        row += 1


def floor_tile(x0, x1, z0, z1, ca, cb, cc, t=2.8):
    box(x0, x1, FY - 0.04, FY - 0.02, z0, z1, '#D9D6CB')                       # light grout under the tiles
    nx, nz = max(1, int(round((x1 - x0) / t))), max(1, int(round((z1 - z0) / t)))
    dx, dz = (x1 - x0) / nx, (z1 - z0) / nz
    for i in range(nx):
        for j in range(nz):
            c = (ca, cb, cc)[(i + 2 * j) % 3] if (i + j) % 2 == 0 else ca
            box(x0 + i * dx + 0.04, x0 + (i + 1) * dx - 0.04, FY - 0.02, FY, z0 + j * dz + 0.04, z0 + (j + 1) * dz - 0.04, c)


floor_wood(-8.0, 24.0, -17.0, 6.0, 1)
floor_wood(-10.0, 24.0, 6.0, 17.0, 2)
floor_wood(25.0, 45.0, -17.0, 2.0, 3)
floor_tile(-24.0, -8.0, -17.0, 6.0, P['tileA'], P['tileB'], P['tileC'])
floor_tile(-24.0, -10.0, 6.0, 17.0, P['tileA'], P['tileB'], P['tileC'])
floor_tile(25.0, 45.0, 3.0, 17.0, P['tileW'], P['tileG'], P['tileW'], t=2.5)
# brass thresholds where tile meets wood and in the doorways
box(-8.0, -7.6, FY - 0.02, FY + 0.03, -17.0, 6.0, P['brass'])
box(-10.0, -9.6, FY - 0.02, FY + 0.03, 6.0, 17.0, P['brass'])
box(-10.0, -8.0, FY - 0.02, FY + 0.03, 5.6, 6.0, P['brass'])
box(24.0, 25.0, FY - 0.02, FY + 0.03, BEDDOOR[0], BEDDOOR[1], P['brass'])
box(24.0, 25.0, FY - 0.02, FY + 0.03, BATHDOOR[0], BATHDOOR[1], P['brass'])

# ---- ceiling spots (recessed rings + glow), the crown is in trim_*
def downlight(x, z, rng=20, br=0.8):
    cyl(x, z, CY - 0.18, CY, 0.65, P['white'], seg=14)
    cyl(x, z, CY - 0.22, CY - 0.18, 0.45, '#FFF0C8', seg=12, kind='N')
    spot(x, CY - 0.6, z, rng, br)


for gx in (-20, -12):
    for gz in (-12, -4, 3):
        downlight(gx, gz, 18, 0.7)
for gx in (-4, 4, 12, 20):
    for gz in (-12, -4, 4, 12):
        downlight(gx, gz, 18, 0.7)
for gx in (-20, -15):
    downlight(gx, 10.0, 16, 0.7)
for (gx, gz) in ((30, -12), (40, -12), (30, -5), (40, -5), (30, -1), (40, -1)):
    downlight(gx, gz, 16, 0.65)
for (gx, gz) in ((30, 8), (40, 8), (30, 14), (40, 14)):
    downlight(gx, gz, 16, 0.65)

# ---- the city outside (skyline), only seen through the windows: blocks with blue roofs, roads far below
def skyline():
    r = rnd_of(5)
    base = -100.0
    roads = []
    for x in range(-260, 300, 70):
        roads.append((x - 5, x + 5, -420, 120))
    for z in range(-420, 130, 70):
        roads.append((-260, 300, z - 5, z + 5))
    box(-300, 340, base - 3, base, -440, 140, '#6FBF55')
    for (a, b, c, d) in roads:
        box(a, b, base, base + 0.1, c, d, '#464B58')
    wc = ['#A9CBEA', '#F8DCA6', '#9CB8EC', '#F6F4EC', '#C4633F', '#9AD9DA', '#DCD0BB']
    for ix in range(-4, 5):
        for iz in range(-6, 2):
            cx, cz = ix * 70 + 35, iz * 70 + 35
            if abs(cx - 10) < 45 and abs(cz) < 45:
                continue
            for (ox, oz) in ((-16, -14), (14, -16), (-14, 15), (16, 14)):
                bx, bz = cx + ox + r.uniform(-4, 4), cz + oz + r.uniform(-4, 4)
                w, d = r.uniform(18, 26), r.uniform(16, 24)
                h = r.choice([22, 30, 38, 46, 58, 70])
                col = r.choice(wc)
                box(bx - w / 2, bx + w / 2, base, base + h, bz - d / 2, bz + d / 2, col)
                box(bx - w / 2 - 0.4, bx + w / 2 + 0.4, base + h, base + h + 0.9, bz - d / 2 - 0.4, bz + d / 2 + 0.4, P['white'])
                box(bx - w / 2 + 0.3, bx + w / 2 - 0.3, base + h + 0.9, base + h + 1.0, bz - d / 2 + 0.3, bz + d / 2 - 0.3, P['roof'])
                SKY_OBJ.append((bx, bz))
            for k in range(3):
                tx, tz = cx + r.uniform(-30, 30), cz + r.uniform(-30, 30)
                sphere(tx, base + 5, tz, 3, 4, 3, P['leaf'], seg=6, rings=4)


exec(compile(open(os.path.join(HERE, 'view2.py'), encoding='utf-8').read(), 'view2.py', 'exec'))     # the real district seen from the tower

# =======================================================================================================================================
# HALL (SW): console + mirror, shoe bench, coat hooks, umbrella stand, plant
# =======================================================================================================================================
anchor('arrival', -16.0, FY, 12.5, 0, -1)
anchor('exit_door', -16.0, 5.0, Z1 - 0.1, 0, 1)
rect_table(-24.0, -22.3, 7.0, 12.4, 3.0, P['walnut2'], P['black'], 'console')
f = F('E', -24.0, 9.7)
f.b(-2.6, 2.6, FY + 3.0, FY + 3.12, 0.0, 1.7, P['brass'])
wb('E', -24.0, FY + 4.4, 9.7, 5.0, 5.2, 0.28, P['brass'])                           # mirror frame
wb('E', -24.0, FY + 4.65, 9.7, 4.5, 4.7, 0.06, '#DCEBF5', 0.28)                    # mirror
D.lathe(-23.2, 8.2, FY + 3.12, [(0.0, 0), (0.55, 0), (0.45, 0.8), (0.55, 1.5), (0.0, 1.5)], P['teal'], seg=12)
plant(-23.1, 9.0, 1.6, P['teal'], 'bushy', 3, 'console_plant', y=FY + 3.12) if False else None
box(-23.6, -22.6, FY + 3.12, FY + 3.4, 10.4, 11.8, P['navy'])                        # key tray
for k in range(3):
    box(-23.4 + k * 0.25, -23.2 + k * 0.25, FY + 3.4, FY + 3.55, 10.7 + k * 0.3, 11.0 + k * 0.3, P['brass'])
fb = F('S', -22.0, 15.0)                                                            # shoe bench against the south wall
fb.b(-2.0, 2.0, FY + 1.5, FY + 1.9, -1.5, 0.0, P['walnut2'])
for (u, w) in ((-1.8, -1.35), (1.8, -1.35), (-1.8, -0.15), (1.8, -0.15)):
    fb.b(u - 0.12, u + 0.12, FY, FY + 1.5, w - 0.12, w + 0.12, P['black'])
fb.b(-1.5, -0.5, FY + 1.9, FY + 2.4, -1.2, -0.3, P['red'])
fb.b(0.3, 1.3, FY + 1.9, FY + 2.4, -1.2, -0.3, P['navy'])
fb.col('shoe_bench', -2.0, 2.0, FY, FY + 2.4, -1.5, 0.0)
for k in range(4):                                                                  # coat hooks with coats on the south wall
    ux = -23.6 + k * 1.5
    box(ux - 0.15, ux + 0.15, FY + 6.4, FY + 6.7, Z1 - TH / 2 - 0.5, Z1 - TH / 2, P['brass'])
    box(ux - 0.45, ux + 0.45, FY + 3.2, FY + 6.3, Z1 - TH / 2 - 0.45, Z1 - TH / 2 - 0.03, [P['navy'], P['red'], P['mustard'], P['charcoal']][k])
D.lathe(-11.2, 16.2, FY, [(0.0, 0), (0.7, 0), (0.75, 0.2), (0.7, 2.6), (0.0, 2.6)], P['charcoal'], seg=12)
CY_add(-11.2, FY + 1.3, 16.2, 1.6, 2.6, 'umbrella_stand')
for k in range(3):
    box(-11.3 + k * 0.28 - 0.06, -11.3 + k * 0.28 + 0.06, FY + 2.6, FY + 5.4 - k * 0.5, 16.1 + k * 0.1, 16.3 + k * 0.1, [P['red'], P['navy'], P['mustard']][k])
plant(-11.6, 8.4, 6.0, P['pot'], 'fiddle', 4, 'hall_plant')
art('E', -24.0, FY + 6.2, 4.2, 4.2, 3.0, 11) if False else None

# =======================================================================================================================================
# KITCHEN (W / NW): L-shaped run, fridge, hob under a hood, sink under the window, island with stools, pendants
# =======================================================================================================================================
def counter_run(face, ox, oz, u0, u1, depth, name, door_col, top=P['marble']):
    f = F(face, ox, oz)
    f.b(u0, u1, FY + 0.35, FY + 3.0, 0.0, depth - 0.15, door_col)
    f.b(u0, u1, FY, FY + 0.35, 0.0, depth - 0.3, P['charcoal'])
    f.b(u0 - 0.05, u1 + 0.05, FY + 3.0, FY + 3.2, -0.0, depth + 0.1, top)
    n = max(1, int(round((u1 - u0) / 3.0)))
    for k in range(n):
        a = u0 + k * (u1 - u0) / n
        f.b(a + 0.08, a + (u1 - u0) / n - 0.08, FY + 0.45, FY + 2.9, depth - 0.15, depth - 0.08, shade(door_col, 0.12))
        f.b(a + (u1 - u0) / n / 2 - 0.45, a + (u1 - u0) / n / 2 + 0.45, FY + 2.4, FY + 2.5, depth - 0.08, depth + 0.05, P['brass'])
    f.col(name, u0, u1, FY, FY + 3.2, 0.0, depth + 0.1)
    return f


def upper_cabinets(face, ox, oz, u0, u1, name, col):
    f = F(face, ox, oz)
    f.b(u0, u1, FY + 6.2, FY + 9.4, 0.0, 1.4, col)
    n = max(1, int(round((u1 - u0) / 2.6)))
    for k in range(n):
        a = u0 + k * (u1 - u0) / n
        f.b(a + 0.08, a + (u1 - u0) / n - 0.08, FY + 6.3, FY + 9.3, 1.4, 1.46, shade(col, 0.1))
        f.b(a + (u1 - u0) / n - 0.5, a + (u1 - u0) / n - 0.35, FY + 6.4, FY + 7.4, 1.46, 1.58, P['brass'])
    f.col(name, u0, u1, FY + 6.2, FY + 9.4, 0.0, 1.4)


# north run along z = -17 (face 'S': forward = +z into the room), x -21.4 .. -6
fn_ = counter_run('S', 0.0, -17.0, 0.0, 0.0, 0, 'x', P['navy']) if False else None
cr = F('S', 0.0, -17.0)
# base cabinets and counter on the north wall: u runs to the west when facing south, so use absolute boxes
def north_run(x0, x1):
    box(x0, x1, FY + 0.35, FY + 3.0, -17.0, -14.85, P['navy'])
    box(x0, x1, FY, FY + 0.35, -17.0, -14.7, P['charcoal'])
    box(x0 - 0.05, x1 + 0.05, FY + 3.0, FY + 3.2, -17.0, -14.6, P['marble'])
    n = max(1, int(round((x1 - x0) / 3.0)))
    for k in range(n):
        a = x0 + k * (x1 - x0) / n
        box(a + 0.08, a + (x1 - x0) / n - 0.08, FY + 0.45, FY + 2.9, -14.85, -14.78, shade(P['navy'], 0.12))
        box(a + (x1 - x0) / n / 2 - 0.45, a + (x1 - x0) / n / 2 + 0.45, FY + 2.4, FY + 2.5, -14.78, -14.65, P['brass'])
    collider(x0, x1, FY, FY + 3.2, -17.0, -14.6, 'kitchen_n')


north_run(-20.7, -6.0)
# backsplash tile on the north wall and the west wall
for k in range(0, 15):
    x = -20.7 + k * 1.0
    box(x + 0.03, x + 0.97, FY + 3.2, FY + 6.2, -17.0, -16.94, P['tileG'] if k % 4 == 0 else P['tileW'])
for k in range(0, 17):
    z = -13.0 + k * 1.0
    if KWIN[0] - 0.3 < z + 0.5 < KWIN[1] + 0.3 and False:
        continue
    box(-24.0, -23.94, FY + 3.2, FY + 6.2 if not (KWIN[0] - 0.01 <= z <= KWIN[1] + 0.01) else FY + 4.4, z + 0.03, z + 0.97, P['tileG'] if k % 4 == 0 else P['tileW'])


# west run along x = -24
def west_run(z0, z1):
    box(-24.0, -21.65, FY + 0.35, FY + 3.0, z0, z1, P['navy'])
    box(-24.0, -21.8, FY, FY + 0.35, z0, z1, P['charcoal'])
    box(-24.0, -21.4, FY + 3.0, FY + 3.2, z0 - 0.05, z1 + 0.05, P['marble'])
    n = max(1, int(round((z1 - z0) / 3.0)))
    for k in range(n):
        a = z0 + k * (z1 - z0) / n
        box(-21.65, -21.58, FY + 0.45, FY + 2.9, a + 0.08, a + (z1 - z0) / n - 0.08, shade(P['navy'], 0.12))
        box(-21.58, -21.45, FY + 2.4, FY + 2.5, a + (z1 - z0) / n / 2 - 0.45, a + (z1 - z0) / n / 2 + 0.45, P['brass'])
    collider(-24.0, -21.4, FY, FY + 3.2, z0, z1, 'kitchen_w')


west_run(-13.0, 3.8)
# sink in the west run under the window (z -12..-4)
box(-23.6, -21.9, FY + 3.2, FY + 3.55, -9.8, -6.2, P['metal'])
box(-23.4, -22.1, FY + 3.3, FY + 3.62, -9.6, -6.4, '#9AA5AD')
box(-23.9, -23.5, FY + 3.2, FY + 4.7, -8.15, -7.85, P['metal'])
box(-23.9, -22.9, FY + 4.5, FY + 4.7, -8.15, -7.85, P['metal'])
# fridge in the NW corner
box(-24.0, -20.9, FY, FY + 8.9, -17.0, -13.4, '#C9D2D8')
box(-24.0, -20.9, FY + 5.6, FY + 5.7, -13.5, -13.35, P['charcoal'])
box(-21.25, -21.05, FY + 6.0, FY + 8.0, -14.0, -13.35, P['metal2'])
box(-21.25, -21.05, FY + 2.0, FY + 4.8, -14.0, -13.35, P['metal2'])
collider(-24.0, -20.9, FY, FY + 8.9, -17.0, -13.4, 'fridge')
# hob + hood on the north run
box(-15.8, -12.2, FY + 3.2, FY + 3.26, -16.6, -15.2, P['black'])
for (u, w) in ((-15.2, -16.2), (-12.8, -16.2), (-15.2, -15.6), (-12.8, -15.6)):
    D.lathe(u, w, FY + 3.26, [(0.4, 0), (0.45, 0.04), (0.0, 0.05)], P['charcoal'], seg=10)
box(-15.0, -13.0, FY + 7.2, FY + 7.5, -17.0, -14.9, P['metal'])
box(-14.4, -13.6, FY + 7.5, CY, -17.0, -16.2, P['metal'])
box(-15.4, -12.6, FY + 7.0, FY + 7.2, -17.0, -14.7, P['metal2'])
spot(-14.0, FY + 6.8, -15.4, 10, 0.6)
upper_cabinets('S', -6.0, -17.0, 0.0, 0.0, 'x', P['navy']) if False else None
for gi_, (ua, ub) in enumerate(((-20.4, -16.0), (-12.0, -6.2))):
    box(ua, ub, FY + 6.2, FY + 9.4, -17.0, -15.6, P['cream'])
    n_c = int(round((ub - ua) / 2.5))
    for k in range(n_c):
        u0 = ua + k * (ub - ua) / n_c
        box(u0 + 0.08, u0 + (ub - ua) / n_c - 0.08, FY + 6.3, FY + 9.3, -15.6, -15.5, P['white'])
        box(u0 + (ub - ua) / n_c - 0.5, u0 + (ub - ua) / n_c - 0.35, FY + 6.4, FY + 7.4, -15.5, -15.36, P['brass'])
    collider(ua, ub, FY + 6.2, FY + 9.4, -17.0, -15.6, 'kitchen_up%d' % (gi_ + 1))
box(-24.0, -22.6, FY + 6.2, FY + 9.4, -1.2, 3.8, P['cream'])
for k in range(2):
    z0_ = -1.2 + k * 2.5
    box(-22.6, -22.5, FY + 6.3, FY + 9.3, z0_ + 0.08, z0_ + 2.42, P['white'])
    box(-22.5, -22.38, FY + 6.4, FY + 7.4, z0_ + 1.9, z0_ + 2.1, P['brass'])
collider(-24.0, -22.6, FY + 6.2, FY + 9.4, -1.2, 3.8, 'kitchen_up3')
# appliances: coffee machine, kettle, fruit bowl, cutting board, utensils
box(-9.0, -7.0, FY + 3.2, FY + 4.9, -16.8, -15.6, P['charcoal'])
box(-8.7, -7.3, FY + 3.5, FY + 3.6, -16.0, -15.0, P['metal'])
D.lathe(-10.2, -15.8, FY + 3.2, [(0.0, 0), (0.6, 0.0), (0.5, 1.2), (0.0, 1.3)], P['red'], seg=12)
box(-20.2, -18.4, FY + 3.2, FY + 3.35, -16.5, -15.4, P['oak'])
D.lathe(-19.6, -15.9, FY + 3.35, [(0.0, 0), (0.25, 0.0), (0.3, 0.9), (0.0, 0.9)], P['teal'], seg=8)
# island with marble top, 3 stools, fruit bowl
box(-15.6, -11.8, FY + 0.35, FY + 3.0, -8.5, 1.5, P['teal'])
box(-15.6, -12.0, FY, FY + 0.35, -8.5, 1.5, P['charcoal'])
box(-16.0, -11.2, FY + 3.0, FY + 3.25, -8.9, 1.9, P['marble'])
for k in range(4):
    z0_ = -8.4 + k * 2.4
    box(-15.65, -15.58, FY + 0.45, FY + 2.9, z0_ + 0.08, z0_ + 2.3, shade(P['teal'], 0.12))
    box(-15.58, -15.45, FY + 2.4, FY + 2.5, z0_ + 1.0, z0_ + 1.4, P['brass'])
collider(-16.0, -11.2, FY, FY + 3.25, -8.9, 1.9, 'island')
D.lathe(-13.6, -3.0, FY + 3.25, [(0.0, 0), (1.0, 0.0), (1.4, 0.7), (0.0, 0.7)], P['white'], seg=14)
for k, c in enumerate((P['red'], P['mustard'], P['green2'], P['coral'])):
    D.sphere(-13.6 + math.cos(k * 1.6) * 0.5, FY + 4.15, -3.0 + math.sin(k * 1.6) * 0.5, 0.42, 0.42, 0.42, c, seg=8, rings=5)
for z_ in (-6.4, -2.4, 1.0):
    stool(-9.8, z_, [P['red'], P['mustard'], P['coral']][int(z_ > -3) + int(z_ > 0)], 'stool')
pendant(-13.6, -6.0, CY - 2.6, P['navy'], 1)
pendant(-13.6, -1.0, CY - 2.6, P['mustard'], 2)

# =======================================================================================================================================
# EXECUTIVE DESK ZONE (north centre): desk (MistressDesk), her chair behind it, two guest chairs, rug, credenza, bookshelf, curtains
# =======================================================================================================================================
DX, DZ = 6.0, -10.0
rug(-1.5, 13.5, -14.2, -1.8, P['navy'], P['mustard'])
executive_desk('S', DX, DZ)
desk_things('S', DX, DZ)
office_chair('S', DX, -14.6, P['red'], 'mistress_chair')
chair('N', DX, -4.2, P['navy'], P['mustard'], 'guest_chair')
chair('N', DX + 4.2, -4.4, P['navy'], P['mustard'], 'guest_chair2')
briefcase(14.2, -8.6, 'W')
anchor('mistress_seat', DX, FY + 3.2, -14.6, 0, 1)      # seat surface of her chair (she faces the guest)
anchor('guest_seat', DX, FY + 2.55, -4.2, 0, -1)        # seat surface of the guest chair (faces the desk)
anchor('table_top', DX, FY + 3.1, DZ, 0, 1)
SEATFIX = True
# credenza under the window (x 11..20) with decor; bookshelf on the east wall; floor lamp; curtains
f = F('S', 15.5, -17.0)
f.b(-4.5, 4.5, FY + 0.35, FY + 3.0, 0.0, 2.0, P['walnut'])
f.b(-4.5, 4.5, FY, FY + 0.35, 0.0, 1.8, P['charcoal'])
f.b(-4.6, 4.6, FY + 3.0, FY + 3.2, 0.0, 2.1, P['walnut2'])
for k in range(3):
    f.b(-4.4 + k * 3.0, -4.4 + k * 3.0 + 2.9, FY + 0.45, FY + 2.9, 2.0, 2.06, P['walnut2'])
    f.b(-3.4 + k * 3.0, -2.6 + k * 3.0, FY + 2.3, FY + 2.4, 2.06, 2.16, P['brass'])
f.col('credenza', -4.6, 4.6, FY, FY + 3.2, 0.0, 2.1)
f.cyl(-3.4, 1.0, FY + 3.2, FY + 3.7, 0.55, P['white'], seg=12)
f.sphere(-3.4, FY + 4.4, 1.0, 0.7, 0.9, 0.7, P['leaf'], seg=8, rings=5)
f.b(-1.5, 0.6, FY + 3.2, FY + 3.9, 0.7, 1.4, P['navy'])
f.b(-1.4, 0.5, FY + 3.9, FY + 4.5, 0.75, 1.35, P['red'])
f.b(1.6, 3.4, FY + 3.2, FY + 3.3, 0.7, 1.5, P['brass'])
D.lathe(*f.p(2.5, 1.1), FY + 3.4, [(0.0, 0), (0.4, 0.0), (0.2, 0.9), (0.32, 1.7), (0.0, 1.7)], P['teal'], seg=10) if False else None
bookshelf('W', 24.0, -13.3, 6.0, 9.0, 1.6, 'bookshelf', seed=3)
floor_lamp(20.3, -11.4)
curtain('S', -4.0, -17.0, 3.2, FY + 1.0, CY - 0.6, P['cream'], 5) if False else None
curtain('S', 22.1, -17.0, 3.2, FY + 0.5, CY - 0.5, P['cream'], 6)
pendant(DX - 3.0, DZ, CY - 3.4, P['navy'], 3, r=1.6)
pendant(DX + 3.0, DZ, CY - 3.4, P['navy'], 4, r=1.6)
plant(-3.4, -3.0, 6.5, P['pot2'], 'fiddle', 6, 'plant_n')
art('S', -2.0, FY + 5.6, -17.0 + 0.0, 4.0, 3.2, 12) if False else None

# =======================================================================================================================================
# LOUNGE (SE of the studio): red L-sofa facing the TV wall, coffee table, armchair, rug, lamp, plants
# =======================================================================================================================================
rug(3.0, 19.0, 4.6, 14.4, P['navy'], P['red'])
half = sofa('S', 12.0, 8.8, 3, P['red'], P['red2'], 'sofa', chaise=-1)
round_table(9.6, 11.8, 2.4, 1.9, P['marble'], P['brass'], 'coffee_table')
for k in range(3):
    D.sphere(9.6 + math.cos(k * 2.1) * 0.9, FY + 2.3, 11.8 + math.sin(k * 2.1) * 0.9, 0.5, 0.35, 0.5, [P['mustard'], P['white'], P['teal']][k], seg=7, rings=5)
armchair('E', 4.6, 11.4, P['navy'], P['navy2'], 'armchair')
floor_lamp(3.6, 5.4)
plant(4.1, 15.0, 6.0, P['pot'], 'bushy', 7, 'plant_lounge')
f = F('N', 12.0, 17.0)                                                              # TV unit on the south wall
f.b(-6.2, 6.2, FY + 0.5, FY + 2.6, 0.0, 1.9, P['walnut'])
for s in (-1, 1):
    for u in (-5.6, 5.6):
        pass
f.b(-6.2, -6.0, FY, FY + 0.5, 0.2, 0.4, P['black'])
f.b(6.0, 6.2, FY, FY + 0.5, 0.2, 0.4, P['black'])
f.b(-6.2, -6.0, FY, FY + 0.5, 1.5, 1.7, P['black'])
f.b(6.0, 6.2, FY, FY + 0.5, 1.5, 1.7, P['black'])
f.b(-6.3, 6.3, FY + 2.6, FY + 2.8, 0.0, 2.0, P['walnut2'])
for k in range(4):
    f.b(-6.0 + k * 3.0, -6.0 + k * 3.0 + 2.9, FY + 0.6, FY + 2.5, 1.9, 1.96, P['walnut2'])
f.col('tv_unit', -6.3, 6.3, FY, FY + 2.8, 0.0, 2.0)
f.b(-4.4, 4.4, FY + 3.9, FY + 8.3, 0.0, 0.3, P['black'])
f.b(-4.2, 4.2, FY + 4.1, FY + 8.1, 0.3, 0.32, P['screen'])
f.b(-4.2, -0.5, FY + 6.4, FY + 8.1, 0.32, 0.36, '#1F3A66')
f.b(-1.0, 0.8, FY + 2.8, FY + 3.4, 0.5, 1.4, P['charcoal'])                          # soundbar / console
f.b(-3.4, 3.4, FY + 3.1, FY + 3.6, 0.1, 0.5, P['charcoal'])
f.col('tv', -4.4, 4.4, FY + 3.1, FY + 8.3, 0.0, 0.4)
clock('N', 2.2, FY + 7.0, 17.0, 1.5)
art('W', 24.0, FY + 5.0, 0.4, 4.4, 3.4, 14)
art('S', -17.0 + TH / 2 - 0.0, FY + 5.5, -17.0, 0.1, 0.1, 15) if False else None

# =======================================================================================================================================
# BEDROOM (x 25..45, z -17..2)
# =======================================================================================================================================
rug(29.5, 41.5, -14.8, -4.4, P['wall3'], P['mustard'])
b = F('W', 45.0, -9.6)                                                              # bed: head at the far east wall, foot to the west
b.b(-5.4, 5.4, FY + 0.5, FY + 6.4, 0.0, 0.7, P['navy'])                             # headboard panel
for k in range(4):
    for m in range(3):
        b.b(-4.7 + k * 2.45, -4.7 + k * 2.45 + 2.2, FY + 2.0 + m * 1.35, FY + 3.2 + m * 1.35, 0.7, 0.9, P['navy2'])
b.b(-5.0, 5.0, FY + 0.6, FY + 1.5, 0.7, 10.6, P['walnut'])
for (u, w) in ((-4.7, 1.0), (4.7, 1.0), (-4.7, 10.3), (4.7, 10.3)):
    b.b(u - 0.25, u + 0.25, FY, FY + 0.6, w - 0.25, w + 0.25, P['walnut'])
soft(*[0] * 0) if False else None
b.b(-4.8, 4.8, FY + 1.5, FY + 2.7, 0.8, 10.4, P['white'])
b.b(-4.9, 4.9, FY + 2.7, FY + 3.3, 3.4, 10.5, P['wall3'])
b.b(-4.7, 4.7, FY + 3.3, FY + 3.4, 3.6, 10.3, shade(P['wall3'], 0.1))
b.b(-5.0, 5.0, FY + 2.7, FY + 3.35, 8.2, 10.6, P['mustard'])                       # throw blanket on the foot
for k, u in enumerate((-2.6, 2.6)):
    x, z = b.p(u, 1.9)
    cbox(x, FY + 3.4, z, 0.9, 1.6, 3.8, P['white'], rot=0 if True else 90)
    x2, z2 = b.p(u, 1.3)
    cbox(x2, FY + 4.0, z2, 0.7, 1.7, 3.0, [P['coral'], P['teal']][k], rot=0)
b.col('bed', -5.4, 5.4, FY, FY + 3.4, 0.0, 10.6)
for s in (-1, 1):
    n_ = F('W', 45.0, -9.6 + s * 6.4)
    n_.b(-0.95, 0.95, FY, FY + 2.4, 0.0, 1.9, P['walnut2'])
    n_.b(-0.85, 0.85, FY + 0.6, FY + 0.7, 1.9, 1.96, P['walnut'])
    n_.b(-0.85, 0.85, FY + 1.5, FY + 1.6, 1.9, 1.96, P['walnut'])
    n_.b(-0.2, 0.2, FY + 1.0, FY + 1.1, 1.96, 2.1, P['brass'])
    n_.col('nightstand', -0.95, 0.95, FY, FY + 2.4, 0.0, 1.9)
    n_.lathe(0.0, 0.9, FY + 2.4, [(0.0, 0), (0.45, 0), (0.1, 0.25), (0.08, 1.5)], P['brass'], seg=10)
    n_.lathe(0.0, 0.9, FY + 3.7, [(0.55, 0), (0.8, 1.0), (0.78, 1.04), (0.55, 0.04)], P['cream'], seg=12)
    xx, zz = n_.p(0.0, 0.9)
    spot(xx, FY + 4.0, zz, 12, 0.6)
bn = F('W', 33.0, -9.6)                                                             # bench at the foot of the bed
bn.b(-3.6, 3.6, FY + 1.5, FY + 2.1, -0.9, 0.9, P['teal'])
for (u, w) in ((-3.3, -0.6), (3.3, -0.6), (-3.3, 0.6), (3.3, 0.6)):
    bn.b(u - 0.14, u + 0.14, FY, FY + 1.5, w - 0.14, w + 0.14, P['brass'])
bn.col('bench', -3.6, 3.6, FY, FY + 2.1, -0.9, 0.9)
wd = F('N', 35.5, 2.0)                                                              # wardrobe on the bedroom/bath partition
wd.b(-6.5, 6.5, FY, FY + 8.6, 0.0, 2.2, P['wall2'])
for k in range(4):
    a0 = -6.5 + k * 3.25
    wd.b(a0 + 0.06, a0 + 3.25 - 0.06, FY + 0.3, FY + 8.4, 2.2, 2.32, P['white'] if k % 2 == 0 else shade(P['white'], -0.05))
    hu = a0 + 3.25 - 0.5 if k % 2 == 0 else a0 + 0.3
    wd.b(hu, hu + 0.15, FY + 3.6, FY + 5.0, 2.32, 2.46, P['brass'])
wd.col('wardrobe', -6.5, 6.5, FY, FY + 8.6, 0.0, 2.46)
vt = F('S', 28.0, -17.0)                                                            # dressing table with a mirror on the north wall
vt.b(-2.8, 2.8, FY + 2.6, FY + 3.0, 0.0, 1.9, P['walnut2'])
for (u, w) in ((-2.6, 0.2), (2.6, 0.2), (-2.6, 1.7), (2.6, 1.7)):
    vt.b(u - 0.14, u + 0.14, FY, FY + 2.6, w - 0.14, w + 0.14, P['brass'])
vt.b(-2.6, -0.4, FY + 0.6, FY + 2.6, 0.2, 1.8, P['walnut'])
vt.col('vanity', -2.8, 2.8, FY, FY + 3.0, 0.0, 1.9)
wb('S', 28.0, FY + 4.2, -17.0, 3.9, 5.6, 0.25, P['brass'])
wb('S', 28.0, FY + 4.45, -17.0, 3.4, 5.1, 0.06, '#DCEBF5', 0.25)
vt.b(0.6, 1.6, FY + 3.0, FY + 3.5, 0.5, 1.4, P['coral'])
vt.b(-1.8, -0.8, FY + 3.0, FY + 3.2, 0.4, 1.5, P['white'])
chair('N', 29.0, -14.2 + 0.0 + 2.9, P['navy'], P['mustard'], 'vanity_chair') if False else None
stool(28.0, -13.8, P['navy'], 'vanity_stool', 2.6)
plant(43.9, 0.3, 6.5, P['pot'], 'snake', 8, 'plant_bed')
art('W', 45.0, FY + 7.5, -9.6, 6.0, 2.8, 16)
curtain('S', 35.0, -17.0, 3.0, FY + 1.0, CY - 0.6, P['cream'], 5) if False else None
curtain('S', 41.5, -17.0, 3.0, FY + 1.0, CY - 0.6, P['cream'], 5)

# =======================================================================================================================================
# BATHROOM (x 25..45, z 3..17): freestanding tub, toilet, walk-in shower, double vanity with a mirror
# =======================================================================================================================================
tb = F('S', 36.0, 3.2)                                                              # tub along the partition wall (long side), head to the east
tb.b(-5.2, 5.2, FY + 0.4, FY + 2.6, 0.0, 4.4, P['white'])
tb.b(-4.8, 4.8, FY + 0.9, FY + 2.65, 0.4, 4.0, '#DCEFF7')
tb.b(-5.3, 5.3, FY + 2.6, FY + 2.75, -0.05, 4.45, P['white'])
for (u, w) in ((-4.4, 0.5), (4.4, 0.5), (-4.4, 3.9), (4.4, 3.9)):
    tb.b(u - 0.3, u + 0.3, FY, FY + 0.4, w - 0.3, w + 0.3, P['brass'])
tb.b(4.8, 5.1, FY + 2.75, FY + 4.6, 1.9, 2.3, P['brass'])
tb.b(4.0, 5.1, FY + 4.4, FY + 4.6, 1.9, 2.3, P['brass'])
tb.col('tub', -5.3, 5.3, FY, FY + 2.75, -0.05, 4.45)
tw = F('W', 45.0, 8.8)                                                             # toilet, tank on the far east wall
tw.b(-1.0, 1.0, FY + 2.6, FY + 5.4, 0.0, 0.9, P['white'])
tw.lathe(0.0, 1.9, FY, [(0.0, 0), (0.8, 0), (0.95, 0.4), (1.1, 1.8), (0.0, 1.8)], P['white'], seg=16)
tw.lathe(0.0, 1.9, FY + 1.8, [(1.05, 0), (1.1, 0.12), (0.0, 0.12)], shade(P['white'], -0.05), seg=16)
tw.b(-0.4, 0.4, FY + 5.4, FY + 5.55, 0.2, 0.6, P['metal'])
tw.b(-0.5, 0.5, FY + 0.9, FY + 2.6, 0.0, 0.8, P['white'])
tw.col('toilet', -1.2, 1.2, FY, FY + 5.5, 0.0, 3.0)
# walk-in shower in the SE corner: glass panels, tray, rain head
box(39.4, 45.0, FY, FY + 0.18, 12.6, 17.0, P['tileG'])
box(38.9, 39.1, FY, FY + 8.6, 12.6, 13.4, P['sky'], 'G')
box(38.9, 45.0, FY + 8.5, FY + 8.6, 12.5, 12.7, P['sky'], 'G') if False else None
box(43.2, 45.0, FY, FY + 8.6, 12.4, 12.6, P['sky'], 'G')
collider(38.85, 39.15, FY, FY + 8.6, 12.4, 13.4, 'shower_glass')
collider(43.2, 45.0, FY, FY + 8.6, 12.4, 12.7, 'shower_glass')
box(38.8, 39.2, FY, FY + 8.7, 12.3, 12.7, P['metal'])
box(38.8, 39.2, FY + 8.6, FY + 8.7, 12.3, 13.5, P['metal'])
box(44.6, 45.0, FY + 7.4, FY + 7.6, 14.0, 16.4, P['metal'])
D.lathe(44.0, 15.2, FY + 7.6, [(0.0, 0), (1.0, 0.0), (1.0, 0.1), (0.0, 0.1)], P['metal'], seg=14)
box(44.7, 45.0, FY + 3.6, FY + 4.0, 15.0, 15.4, P['brass'])
vn = F('N', 33.5, 17.0)                                                             # double vanity on the south wall
vn.b(-3.6, 3.6, FY + 0.4, FY + 3.0, 0.0, 2.2, P['teal'])
vn.b(-3.6, 3.6, FY, FY + 0.4, 0.0, 2.0, P['charcoal'])
vn.b(-3.8, 3.8, FY + 3.0, FY + 3.2, -0.0, 2.4, P['marble'])
for k in range(2):
    vn.b(-3.5 + k * 3.6, -0.1 + k * 3.6, FY + 0.5, FY + 2.9, 2.2, 2.26, shade(P['teal'], 0.12))
    vn.b(-2.0 + k * 3.6, -1.6 + k * 3.6, FY + 2.2, FY + 2.3, 2.26, 2.4, P['brass'])
for u in (-1.8, 1.8):
    vn.lathe(u, 1.0, FY + 3.2, [(0.0, 0), (1.0, 0), (1.0, 0.25), (0.8, 0.3), (0.0, 0.3)], P['white'], seg=16)
    vn.b(u - 0.1, u + 0.1, FY + 3.2, FY + 4.4, 0.2, 0.4, P['brass'])
    vn.b(u - 0.1, u + 0.1, FY + 4.3, FY + 4.5, 0.2, 0.9, P['brass'])
vn.col('vanity_bath', -3.8, 3.8, FY, FY + 3.2, 0.0, 2.4)
wb('N', 33.5, FY + 4.6, 17.0, 7.4, 4.6, 0.25, P['brass'])
wb('N', 33.5, FY + 4.85, 17.0, 6.9, 4.1, 0.06, '#DCEBF5', 0.25)
for k, c in enumerate((P['white'], P['coral'], P['mustard'])):                       # towels folded on the vanity
    vn.b(2.3 + 0.0, 3.4, FY + 3.2 + k * 0.28, FY + 3.2 + (k + 1) * 0.28, 1.4, 2.2, c)
rug(37.0, 43.5, 8.0, 11.5, P['sky'], P['tileG'], P['white']) if False else None
pass
for k, c in enumerate((P['coral'], P['white'], P['teal'])):                            # towel rail on the partition near the door
    box(25.45, 25.85, FY + 2.6 + k * 0.0, FY + 6.0, 9.2 + k * 1.3, 9.9 + k * 1.3, c) if False else None
plant(27.4, 5.0, 5.0, P['pot2'], 'fiddle', 9, 'plant_bath')
art('E', 25.0 + TH / 2 - 0.0 + 0.0, FY + 5.5, 6.0, 0.1, 0.1, 17) if False else None

exec(compile(open(os.path.join(HERE, 'details2.py'), encoding='utf-8').read(), 'details2.py', 'exec'))
