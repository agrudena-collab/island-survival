# Layout of OfficeDadDistrict, executed by build_district.py after the helpers are defined.
# 500 x 500 (Studio-like x east, z south; the plan's Blender +Y north is z = -Y).  Two avenues (24 asphalt, 9 sidewalks) cross off-centre,
# two side streets (16 asphalt, 7 sidewalks) end at the perimeter hedge.  Order: ground, streets, furniture, tower, buildings, places, fillers.
HALF = PD.HALF
FI = HALF - 3                       # inner face of the perimeter hedge
SWY = GY + 0.27                     # walking surface of the sidewalks / paving (they have colliders)
ASPH = GY + 0.09                    # asphalt top (matches the forest road layers: ground 1.0, shoulder +0.06, asphalt +0.09)
PAL['joint'] = '#C3C7CE'
TONES = ['#DAD7CE', '#E4E7EB', '#D3D8DE']

STREETS = []
for (_nm, _ax, _c, _ah, _sh, _conn) in PD.STREETS:
    STREETS.append(dict(name=_nm, ew=(_ax == 'x'), c=(-_c if _ax == 'x' else _c), ah=_ah, sh=_sh, conn=_conn))
EW = [s for s in STREETS if s['ew']]
NS = [s for s in STREETS if not s['ew']]
AVE_A = EW[0]
AVE_B = NS[0]
DRIVEWAYS = []                      # (street name, side, a, b): gaps in the sidewalk for driveways (along-axis interval)


def cut(a, b, cuts):
    res = [(a, b)]
    for (c0, c1) in cuts:
        nr = []
        for (s, e) in res:
            if c1 <= s or c0 >= e:
                nr.append((s, e))
                continue
            if c0 > s:
                nr.append((s, c0))
            if c1 < e:
                nr.append((c1, e))
        res = nr
    return [(s, e) for (s, e) in res if e - s > 0.05]


def occ(tag, x0, x1, z0, z1):
    OCC.append((tag, min(x0, x1), max(x0, x1), min(z0, z1), max(z0, z1)))


def paved(x0, x1, z0, z1, y=GY, h=0.25, tile=6.0, collide=True, name='paving', zone='p', tag='paved'):
    """Tiled paving: a joint-coloured slab with three-tone tiles 0.02 above it (a collider carries the walking surface)."""
    box(x0, x1, y, y + h, z0, z1, PAL['joint'])
    nx = max(1, int(round((x1 - x0) / tile)))
    nz = max(1, int(round((z1 - z0) / tile)))
    dx, dz = (x1 - x0) / nx, (z1 - z0) / nz
    for i in range(nx):
        for j in range(nz):
            box(x0 + i * dx + 0.06, x0 + (i + 1) * dx - 0.06, y + h, y + h + 0.02, z0 + j * dz + 0.06, z0 + (j + 1) * dz - 0.06, TONES[(i + 2 * j) % 3])
    if collide:
        collider(x0, x1, y, y + h + 0.02, z0, z1, name)
    ZONES_OCC.append((zone, x0, x1, z0, z1))
    if tag:
        occ(tag, x0, x1, z0, z1)


def hline(x0, x1, z, w, col, y0=GY, h=0.06):
    box(x0, x1, y0, y0 + h, z - w / 2, z + w / 2, col)


def vline(z0, z1, x, w, col, y0=GY, h=0.06):
    box(x - w / 2, x + w / 2, y0, y0 + h, z0, z1, col)


def front_face_sign(text, b, side, uc, ground_h, w, col, sh=2.8, text_col=None):
    """Sign board on a wall face (S/N/E/W) in the band between the awnings/canopy and the first-floor windows; never over a window."""
    y0 = GY + ground_h - 0.9
    lb(side, b, uc - w / 2, uc + w / 2, y0, y0 + sh, 0.0, 1.0, col)
    lb(side, b, uc - w / 2 - 0.3, uc + w / 2 + 0.3, y0 - 0.2, y0, 0.0, 1.2, PAL['white'])
    lb(side, b, uc - w / 2 - 0.3, uc + w / 2 + 0.3, y0 + sh, y0 + sh + 0.2, 0.0, 1.2, PAL['white'])
    px, pz = lpos(side, b, uc, 0.0)
    off = 1.0                                    # sign position = front face plane of the board (the text sits 0.05 in front of it)
    if side == 'S':
        SIGNS.append((text, px, y0 + sh / 2, pz + off, w - 1.5, sh - 0.7, 'S'))
    elif side == 'N':
        SIGNS.append((text, px, y0 + sh / 2, pz - off, w - 1.5, sh - 0.7, 'N'))
    elif side == 'E':
        SIGNS.append((text, px + off, y0 + sh / 2, pz, w - 1.5, sh - 0.7, 'E'))
    else:
        SIGNS.append((text, px - off, y0 + sh / 2, pz, w - 1.5, sh - 0.7, 'W'))


# ==================================================================================================================
# ground and streets
# ==================================================================================================================
box(-HALF, HALF, 0, GY, -HALF, HALF, PAL['grass'])
collider(-HALF, HALF, -4, GY, -HALF, HALF, 'ground')

for s in STREETS:
    s['ext'] = HALF if s['conn'] else FI
    s['sw_end'] = (HALF - 6) if s['conn'] else FI
EW_BANDS = [(e['c'] - e['ah'], e['c'] + e['ah']) for e in EW]

# ---- asphalt (east-west streets whole, north-south streets between them: no overlapping coplanar slabs)
for s in EW:
    box(-s['ext'], s['ext'], GY, ASPH, s['c'] - s['ah'], s['c'] + s['ah'], PAL['asphalt'])
    occ('street', -s['ext'], s['ext'], s['c'] - s['sh'], s['c'] + s['sh'])
for s in NS:
    for (a, b) in cut(-s['ext'], s['ext'], EW_BANDS):
        box(s['c'] - s['ah'], s['c'] + s['ah'], GY, ASPH, a, b, PAL['asphalt'])
    occ('street', s['c'] - s['sh'], s['c'] + s['sh'], -s['ext'], s['ext'])
    ZONES_OCC.append(('-', s['c'] - s['sh'], s['c'] + s['sh'], -s['ext'], s['ext']))
for s in EW:
    ZONES_OCC.append(('-', -s['ext'], s['ext'], s['c'] - s['sh'], s['c'] + s['sh']))


def crossing_bands(s):
    """along-axis intervals taken by the streets that cross s (their whole width incl. sidewalks)"""
    return [(o['c'] - o['sh'], o['c'] + o['sh']) for o in (NS if s['ew'] else EW)]


def drive_cuts(s, sg):
    return [(a, b) for (nm, g, a, b) in DRIVEWAYS if nm == s['name'] and g == sg]


# driveways are declared before the sidewalks are built (aprons are laid later in places.py)
DRIVEWAYS += [('Street C', -1, 170, 194), ('Avenue A', -1, 188, 212), ('Avenue B', 1, 148, 166)]

# ---- sidewalks, kerbs, gutters
for s in STREETS:
    for sg in (-1, 1):
        lo, hi = sorted((s['c'] + sg * s['ah'], s['c'] + sg * s['sh']))
        for (a, b) in cut(-s['sw_end'], s['sw_end'], crossing_bands(s) + drive_cuts(s, sg)):
            if s['ew']:
                paved(a, b, lo, hi, name='sidewalk')
                kz = s['c'] + sg * s['ah']
                box(a + 0.03, b - 0.03, GY, GY + 0.32, kz - 0.5, kz + 0.5, PAL['curb'])
                box(a, b, GY, GY + 0.12, (kz - 1.1) if sg > 0 else kz, kz if sg > 0 else (kz + 1.1), PAL['gutter'])
            else:
                paved(lo, hi, a, b, name='sidewalk')
                kx = s['c'] + sg * s['ah']
                box(kx - 0.5, kx + 0.5, GY, GY + 0.32, a + 0.03, b - 0.03, PAL['curb'])
                box((kx - 1.1) if sg > 0 else kx, kx if sg > 0 else (kx + 1.1), GY, GY + 0.12, a, b, PAL['gutter'])

# ---- corner pads and kerb returns at every crossing; tactile pads at the kerb ramps
for e in EW:
    for n in NS:
        for sx in (-1, 1):
            for sz in (-1, 1):
                x0, x1 = sorted((n['c'] + sx * n['ah'], n['c'] + sx * n['sh']))
                z0, z1 = sorted((e['c'] + sz * e['ah'], e['c'] + sz * e['sh']))
                paved(x0, x1, z0, z1, name='sidewalk')
                kz = e['c'] + sz * e['ah']
                kx = n['c'] + sx * n['ah']
                box(x0, x1, GY, GY + 0.32, kz - 0.5, kz + 0.5, PAL['curb'])
                box(kx - 0.5, kx + 0.5, GY, GY + 0.32, z0, z1, PAL['curb'])
                # tactile pads on the ramp sides (just inside the corner, along both kerbs)
                tx0, tx1 = (x0 + 1.0, x0 + 3.4) if sx > 0 else (x1 - 3.4, x1 - 1.0)
                tz0, tz1 = (z0 + 1.0, z0 + 3.4) if sz > 0 else (z1 - 3.4, z1 - 1.0)
                box(tx0, tx1, SWY, SWY + 0.04, z0 + 0.6 if sz > 0 else z1 - 1.0, z0 + 1.0 if sz > 0 else z1 - 0.6, PAL['tactile'])
                box(x0 + 0.6 if sx > 0 else x1 - 1.0, x0 + 1.0 if sx > 0 else x1 - 0.6, SWY, SWY + 0.04, tz0, tz1, PAL['tactile'])

# ---- connector ends: sidewalks stop 6 studs before the border, 2-wide shoulders continue (like the forest road), flush ends
for s in STREETS:
    if not s['conn']:
        continue
    for sg in (-1, 1):
        lo, hi = sorted((s['c'] + sg * s['ah'], s['c'] + sg * (s['ah'] + 2)))
        for end in (-1, 1):
            a, b = sorted((end * (HALF - 6), end * HALF))
            if s['ew']:
                box(a, b, GY, GY + 0.06, lo, hi, PAL['shoulder'])
                # kerb return finishing the sidewalk: 0.4 deep, 0.03 beyond the sidewalk end, 0.03 inside its sides (no coplanar faces)
                e0, e1 = sorted((end * (HALF - 6.4), end * (HALF - 6.0) + end * 0.03))
                l0, l1 = sorted((s['c'] + sg * s['ah'], s['c'] + sg * s['sh']))
                box(e0, e1, GY, GY + 0.32, l0 + 0.03, l1 - 0.03, PAL['curb'])
            else:
                box(lo, hi, GY, GY + 0.06, a, b, PAL['shoulder'])
                e0, e1 = sorted((end * (HALF - 6.4), end * (HALF - 6.0) + end * 0.03))
                l0, l1 = sorted((s['c'] + sg * s['ah'], s['c'] + sg * s['sh']))
                box(l0 + 0.03, l1 - 0.03, GY, GY + 0.32, e0, e1, PAL['curb'])

# ---- road markings
MK = ASPH + 0.03       # marking top
for s in STREETS:
    cuts = [(o['c'] - o['ah'] - 6.5, o['c'] + o['ah'] + 6.5) for o in (NS if s['ew'] else EW)]
    segs = cut(-s['ext'] + 1, s['ext'] - 1, cuts)
    for (a, b) in segs:
        if s['conn']:                      # double yellow centre line
            for off in (-0.3, 0.3):
                if s['ew']:
                    hline(a, b, s['c'] + off, 0.22, PAL['lane'], ASPH, 0.05)
                else:
                    vline(a, b, s['c'] + off, 0.22, PAL['lane'], ASPH, 0.05)
            # edge lines
            for sg in (-1, 1):
                if s['ew']:
                    hline(a, b, s['c'] + sg * (s['ah'] - 0.9), 0.2, PAL['white'], ASPH, 0.05)
                else:
                    vline(a, b, s['c'] + sg * (s['ah'] - 0.9), 0.2, PAL['white'], ASPH, 0.05)
        else:                              # dashed white centre line
            p = a + 2
            while p + 4 < b:
                if s['ew']:
                    hline(p, p + 4, s['c'], 0.2, PAL['white'], ASPH, 0.05)
                else:
                    vline(p, p + 4, s['c'], 0.2, PAL['white'], ASPH, 0.05)
                p += 10

# crosswalks (zebra) and stop lines at every approach
for e in EW:
    for n in NS:
        # across the north-south street, on both sides of the east-west street
        for sz in (-1, 1):
            zc = e['c'] + sz * (e['ah'] + 2.4)
            nb = int(2 * n['ah'] // 2.2) - 1
            for k in range(nb):
                o = n['c'] - n['ah'] + 1.6 + k * 2.2
                box(o - 0.55, o + 0.55, ASPH, ASPH + 0.04, zc - 1.8, zc + 1.8, PAL['white'])
            zs = e['c'] + sz * (e['ah'] + 5.2)
            half = (n['c'] - n['ah'] + 0.4, n['c'] - 0.4) if sz > 0 else (n['c'] + 0.4, n['c'] + n['ah'] - 0.4)
            box(half[0], half[1], ASPH, ASPH + 0.04, zs - 0.3, zs + 0.3, PAL['white'])
        # across the east-west street, on both sides of the north-south street
        for sx in (-1, 1):
            xc = n['c'] + sx * (n['ah'] + 2.4)
            nb = int(2 * e['ah'] // 2.2) - 1
            for k in range(nb):
                o = e['c'] - e['ah'] + 1.6 + k * 2.2
                box(xc - 1.8, xc + 1.8, ASPH, ASPH + 0.04, o - 0.55, o + 0.55, PAL['white'])
            xs = n['c'] + sx * (n['ah'] + 5.2)
            half = (e['c'] + 0.4, e['c'] + e['ah'] - 0.4) if sx > 0 else (e['c'] - e['ah'] + 0.4, e['c'] - 0.4)
            box(xs - 0.3, xs + 0.3, ASPH, ASPH + 0.04, half[0], half[1], PAL['white'])

# manholes and drains
for (x, z) in ((-70, 35), (95, 25), (205, 24), (-190, 36), (35, -75), (45, 100), (40, 205), (-135, 80), (-125, -60), (-136, 210), (60, -122), (-60, -118)):
    s_ok = any((s['ew'] and abs(z - s['c']) < s['ah'] - 2) or ((not s['ew']) and abs(x - s['c']) < s['ah'] - 2) for s in STREETS)
    if s_ok:
        cyl(x, z, ASPH, ASPH + 0.07, 1.25, PAL['dark'], seg=14)
        for k in range(5):
            box(x - 1.0, x + 1.0, ASPH + 0.07, ASPH + 0.1, z - 0.9 + k * 0.45, z - 0.75 + k * 0.45, PAL['asph2'])


# ==================================================================================================================
# street furniture along the sidewalks
# ==================================================================================================================
SKIPS = []


def along(s, sg, start, stop, step, fn, extra_skip=()):
    p = start
    i = 0
    cr = [(o['c'] - o['sh'] - 4, o['c'] + o['sh'] + 4) for o in (NS if s['ew'] else EW)]
    dc = [(a - 3, b + 3) for (a, b) in drive_cuts(s, sg)]
    while p <= stop:
        if not any(c0 < p < c1 for (c0, c1) in cr + dc + list(extra_skip) + SKIPS) and abs(p) < s['sw_end'] - 4:
            off = s['c'] + sg * (s['sh'] - 1.8)
            if s['ew']:
                fn(p, off, i, sg)
            else:
                fn(off, p, i, sg)
        p += step
        i += 1


for s in STREETS:
    for sg in (-1, 1):
        ew = s['ew']
        SKIPS[:] = [(-32, 0)] if (s is AVE_B and sg > 0) else []
        face = (math.pi / 2 * (1 if sg < 0 else -1)) if ew else (0.0 if sg < 0 else math.pi)
        if ew:
            along(s, sg, -s['sw_end'] + 12, s['sw_end'] - 12, 38, lambda x, z, i, sg, face=face: street_lamp(x, z, facing=face, y=SWY))
            along(s, sg, -s['sw_end'] + 31, s['sw_end'] - 12, 38, lambda x, z, i, sg, sd=s['c']: tree(x, z, seed=i + int(sd), h=9 + (i % 3), y=SWY))
            along(s, sg, -s['sw_end'] + 21, s['sw_end'] - 12, 76, lambda x, z, i, sg: bench(x, z + (-1.2 if sg > 0 else 1.2), rot=0 if sg > 0 else 180, y=SWY))
            along(s, sg, -s['sw_end'] + 40, s['sw_end'] - 12, 76, lambda x, z, i, sg: trash_bin(x, z, y=SWY))
        else:
            along(s, sg, -s['sw_end'] + 12, s['sw_end'] - 12, 38, lambda x, z, i, sg, face=face: street_lamp(x, z, facing=face, y=SWY))
            along(s, sg, -s['sw_end'] + 31, s['sw_end'] - 12, 38, lambda x, z, i, sg, sd=s['c']: tree(x, z, seed=i + int(sd), h=9 + (i % 3), y=SWY))
            along(s, sg, -s['sw_end'] + 21, s['sw_end'] - 12, 76, lambda x, z, i, sg: bench(x + (-1.2 if sg > 0 else 1.2), z, rot=90, y=SWY))
            along(s, sg, -s['sw_end'] + 40, s['sw_end'] - 12, 76, lambda x, z, i, sg: trash_bin(x, z, y=SWY))

# traffic lights at the avenue crossing, hydrants and mailboxes at the corners
_a, _b = AVE_A, AVE_B
for sx in (-1, 1):
    for sz in (-1, 1):
        traffic_light(_b['c'] + sx * (_b['ah'] + 2.5), _a['c'] + sz * (_a['ah'] + 2.5), (-sx, 0) if sx * sz > 0 else (0, -sz), y=SWY)
for (x, z) in ((_b['c'] + _b['ah'] + 4.5, _a['c'] + _a['ah'] + 2.0), (_b['c'] - _b['ah'] - 4.5, _a['c'] - _a['ah'] - 2.0), (-118.0, 47.0), (-139.5, 66.0)):
    hydrant(x, z, y=SWY)
for (x, z) in ((_b['c'] + _b['ah'] + 7.0, _a['c'] - _a['ah'] - 6.0), (_b['c'] - _b['ah'] - 7.0, _a['c'] + _a['ah'] + 6.0)):
    mailbox(x, z, y=SWY)

exec(compile(open(os.path.join(HERE, 'tower.py'), encoding='utf-8').read(), 'tower.py', 'exec'))
exec(compile(open(os.path.join(HERE, 'blocks.py'), encoding='utf-8').read(), 'blocks.py', 'exec'))
exec(compile(open(os.path.join(HERE, 'places.py'), encoding='utf-8').read(), 'places.py', 'exec'))
exec(compile(open(os.path.join(HERE, 'fillers.py'), encoding='utf-8').read(), 'fillers.py', 'exec'))
