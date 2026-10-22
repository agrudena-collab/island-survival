# Regular Dad district: roads, sidewalks, the mistress' apartment tower, neighbour blocks, hardware store, workshop, Gym, a park
# with a fountain and detailed street furniture. Bright toy palette of the Regular Dad house, but modelled, not blocky.
# Run: blender -b --factory-startup --python build_district.py -- <outdir> [--norender]
# Writes: <outdir>/RDD_District.fbx (vertex-colour chunks <= 9000 tris, G_/N_/O_ names), district.json (colliders, anchors, signs, lights),
#         renders/*.png. Coordinates are Studio-like (x east, y up, z south); the FBX is written with Blender (x, -z, y).
import bpy, bmesh, math, os, sys, json, random, time
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dlib as D
from dlib import box, cbox, cyl, lathe, sphere, prism, collider, anchor, shade

args = sys.argv[sys.argv.index('--') + 1:]
OUT = os.path.abspath(args[0])
NORENDER = '--norender' in args
os.makedirs(OUT, exist_ok=True)
random.seed(7)
T0 = time.time()

GY = 1.0                    # ground top
SIGNS = []                  # (text, x, y, z, w, h, facing 'N/S/E/W')
LIGHTS = []                 # (x, y, z, range)
BLD = []                    # (name, item counts at start, item counts at end) of every building() for the audit
TREES = []                # (x, z, canopy radius) for the audit
ZONES_OCC = []              # (char, x0, x1, z0, z1) infrastructure that has no collider (paving, paths, lawns with beds) for the audit map

PAL = dict(asphalt='#4A4D57', asph2='#585B66', curb='#C9C6BE', walk='#DCD6C8', walk2='#CFC8B8', lane='#F4E7A0', white='#F8F8F2', grass='#79C943',
           grass2='#62B336', soil='#7A5638', brick='#E07A5F', brick2='#C9624A', cream='#F6E7C8', teal='#3FB8A8', sky='#8FC8EE', blue='#3FA7FF',
           red='#E4473D', yellow='#FFD24D', navy='#2B3A67', wood='#B97B45', wood2='#8A5A3A', metal='#9AA3AD', dark='#2A2D36', roof='#E4473D',
           glass='#9FD4F5', door='#16B89A', plum='#8E5BA8', green='#2F9E5A', orange='#F28C38', pink='#F29BB5', gray='#8B909A', concrete='#B8B6B0')


# ------------------------------------------------------------------------------------------------------------------
# local wall frames: side S/N run along x (out = +z / -z), E/W run along z (out = +x / -x)
# ------------------------------------------------------------------------------------------------------------------
class R:
    def __init__(self, x0, x1, z0, z1):
        self.x0, self.x1, self.z0, self.z1 = x0, x1, z0, z1

    def width(self, side):
        return (self.x1 - self.x0) if side in 'SN' else (self.z1 - self.z0)


def lb(side, b, u0, u1, y0, y1, o0, o1, col, kind='O'):
    if side == 'S':
        box(b.x0 + u0, b.x0 + u1, y0, y1, b.z1 + o0, b.z1 + o1, col, kind)
    elif side == 'N':
        box(b.x0 + u0, b.x0 + u1, y0, y1, b.z0 - o1, b.z0 - o0, col, kind)
    elif side == 'E':
        box(b.x1 + o0, b.x1 + o1, y0, y1, b.z0 + u0, b.z0 + u1, col, kind)
    else:
        box(b.x0 - o1, b.x0 - o0, y0, y1, b.z0 + u0, b.z0 + u1, col, kind)


def lpos(side, b, u, o):
    """World (x, z) of local (u, o)."""
    if side == 'S':
        return b.x0 + u, b.z1 + o
    if side == 'N':
        return b.x0 + u, b.z0 - o
    if side == 'E':
        return b.x1 + o, b.z0 + u
    return b.x0 - o, b.z0 + u


def window(side, b, uc, y0, w, h, frame=None, glass=None, shutters=None, sill=True, ac=False, flowers=False, arch=False):
    frame = frame or PAL['white']
    glass = glass or PAL['glass']
    t = 0.42
    lb(side, b, uc - w / 2, uc + w / 2, y0, y0 + h, -0.3, 0.05, shade(frame, -0.55))                 # dark reveal
    lb(side, b, uc - w / 2 + t, uc + w / 2 - t, y0 + t, y0 + h - t, 0.0, 0.14, glass, 'G')           # pane
    lb(side, b, uc - w / 2, uc + w / 2, y0, y0 + t, 0.0, 0.5, frame)                                  # frame bars
    lb(side, b, uc - w / 2, uc + w / 2, y0 + h - t, y0 + h, 0.0, 0.5, frame)
    lb(side, b, uc - w / 2, uc - w / 2 + t, y0, y0 + h, 0.0, 0.5, frame)
    lb(side, b, uc + w / 2 - t, uc + w / 2, y0, y0 + h, 0.0, 0.5, frame)
    if w > 3.2:
        lb(side, b, uc - 0.16, uc + 0.16, y0, y0 + h, 0.0, 0.45, frame)                               # mullion
    lb(side, b, uc - w / 2, uc + w / 2, y0 + h * 0.62, y0 + h * 0.62 + 0.26, 0.0, 0.42, frame)       # transom
    if sill:
        lb(side, b, uc - w / 2 - 0.45, uc + w / 2 + 0.45, y0 - 0.5, y0 - 0.03, 0.0, 1.1, shade(frame, -0.08))      # (top just below y0: no z-fight with balcony slabs)
        lb(side, b, uc - w / 2 - 0.35, uc + w / 2 + 0.35, y0 + h, y0 + h + 0.5, 0.0, 0.8, shade(frame, -0.05))   # lintel
    if shutters:
        for s in (-1, 1):
            cu = uc + s * (w / 2 + 0.9)
            lb(side, b, cu - 0.8, cu + 0.8, y0, y0 + h, 0.0, 0.3, shutters)
            for k in range(1, 7):
                yy = y0 + k * h / 7
                lb(side, b, cu - 0.7, cu + 0.7, yy, yy + 0.16, 0.25, 0.4, shade(shutters, -0.2))
    if ac:
        lb(side, b, uc - 1.3, uc + 1.3, y0 - 2.2, y0 - 0.6, 0.0, 1.6, PAL['white'])
        lb(side, b, uc - 1.0, uc + 1.0, y0 - 1.9, y0 - 1.0, 1.6, 1.75, PAL['dark'])
    if flowers:
        lb(side, b, uc - w / 2, uc + w / 2, y0 - 1.1, y0 - 0.2, 0.2, 1.4, PAL['wood2'])
        for k in range(5):
            x, z = lpos(side, b, uc - w / 2 + 0.5 + k * (w - 1) / 4, 1.0)
            D.sphere(x, y0 + 0.3, z, 0.35, 0.35, 0.35, [PAL['pink'], PAL['yellow'], PAL['red'], PAL['white'], PAL['orange']][k], seg=6, rings=4)
            D.sphere(x, y0 - 0.15, z, 0.4, 0.3, 0.4, PAL['green'], seg=6, rings=4)


def balcony(side, b, uc, y0, w, depth=3.4, col=None, rail=None):
    col = col or PAL['concrete']
    rail = rail or PAL['white']
    lb(side, b, uc - w / 2, uc + w / 2, y0 - 0.6, y0, 0.0, depth, col)
    lb(side, b, uc - w / 2, uc + w / 2, y0 - 0.9, y0 - 0.6, 0.0, depth * 0.85, shade(col, -0.12))
    n = int(w / 0.9)
    for k in range(n + 1):
        u = uc - w / 2 + 0.2 + k * (w - 0.4) / n
        lb(side, b, u - 0.1, u + 0.1, y0, y0 + 3.0, depth - 0.25, depth - 0.05, rail)
    for s in (-1, 1):
        u = uc + s * (w / 2 - 0.15)
        for k in range(1, 5):
            oo = depth * k / 5
            lb(side, b, u - 0.1, u + 0.1, y0, y0 + 3.0, oo, oo + 0.18, rail)
        lb(side, b, u - 0.15, u + 0.15, y0 + 3.0, y0 + 3.25, 0.0, depth, rail)
    lb(side, b, uc - w / 2, uc + w / 2, y0 + 3.0, y0 + 3.25, depth - 0.3, depth, rail)
    lb(side, b, uc - w / 2, uc + w / 2, y0 + 0.0, y0 + 0.4, depth - 0.3, depth - 0.0, shade(rail, -0.1))


def cornice(b, y, col, layers=3, out=0.9):
    for k in range(layers):
        o = out * (k + 1) / layers
        for side in 'SNEW':
            L = b.width(side)
            lb(side, b, -o, L + o, y + k * 0.45, y + (k + 1) * 0.45, 0.0, o + 0.05, shade(col, -0.04 * k))
    # corner blocks
    for sx in (b.x0 - out, b.x1):
        for sz in (b.z0 - out, b.z1):
            box(sx, sx + out, y, y + 0.45 * layers, sz, sz + out, shade(col, -0.1))


def roof_details(b, y, rnd, tank=True):
    # parapet
    p = 0.7
    for (x0, x1, z0, z1) in ((b.x0, b.x1, b.z0, b.z0 + p), (b.x0, b.x1, b.z1 - p, b.z1), (b.x0, b.x0 + p, b.z0, b.z1), (b.x1 - p, b.x1, b.z0, b.z1)):
        box(x0, x1, y, y + 2.2, z0, z1, PAL['cream'])
        box(x0 - 0.2, x1 + 0.2, y + 2.2, y + 2.6, z0 - 0.2, z1 + 0.2, PAL['white'])
    box(b.x0 + p, b.x1 - p, y - 0.4, y + 0.1, b.z0 + p, b.z1 - p, PAL['gray'])
    cx, cz = (b.x0 + b.x1) / 2, (b.z0 + b.z1) / 2
    if tank:
        for k in range(3):
            xx = cx + 6 + k * 0.3
        D.lathe(cx + 7, cz - 2, y, [(0, 0), (3.2, 0.1), (3.2, 5.4), (3.0, 5.7), (0, 6.0)], PAL['teal'], seg=24)
        for k in range(4):
            D.lathe(cx + 7, cz - 2, y + 1.0 + k * 1.2, [(3.22, 0), (3.22, 0.18)], PAL['dark'], seg=24)
        for a in range(4):
            ang = a * math.pi / 2 + 0.4
            box(cx + 7 + 2.4 * math.cos(ang) - 0.2, cx + 7 + 2.4 * math.cos(ang) + 0.2, y - 0.2, y + 0.4, cz - 2 + 2.4 * math.sin(ang) - 0.2, cz - 2 + 2.4 * math.sin(ang) + 0.2, PAL['dark'])
    # stair bulkhead + ac units + antenna
    box(cx - 12, cx - 5, y, y + 5, cz - 3, cz + 3, PAL['cream'])
    box(cx - 12.3, cx - 4.7, y + 5, y + 5.5, cz - 3.3, cz + 3.3, PAL['white'])
    box(cx - 9.4, cx - 7.6, y, y + 3.8, cz + 3, cz + 3.15, PAL['door'])
    for k in range(3):
        box(cx - 2 + k * 3.6, cx + 0.6 + k * 3.6, y, y + 1.9, cz + 3, cz + 5.6, PAL['white'])
        cyl(cx - 0.7 + k * 3.6, cz + 4.3, y + 1.9, y + 2.1, 1.0, PAL['dark'], seg=14)
    box(cx - 0.12, cx + 0.12, y, y + 11, cz + 8 - 0.12, cz + 8 + 0.12, PAL['dark'])
    for k in range(4):
        box(cx - 1.5 + 0.2, cx + 1.5 - 0.2, y + 5 + k * 1.5, y + 5.1 + k * 1.5, cz + 8 - 0.05, cz + 8 + 0.05, PAL['metal'])


def storefront(side, b, u0, u1, y0, h, frame, awning=None, sign=None, door_u=None, bulkhead=PAL['navy']):
    """Glass shop window wall with frames, bulkhead, optional awning and a door."""
    n = max(1, int((u1 - u0) / 5.2))
    wseg = (u1 - u0) / n
    lb(side, b, u0, u1, y0, y0 + 1.6, -0.2, 0.7, bulkhead)
    for k in range(n):
        a, c = u0 + k * wseg, u0 + (k + 1) * wseg
        lb(side, b, a + 0.3, c - 0.3, y0 + 1.6, y0 + h, 0.0, 0.14, PAL['glass'], 'G')
        lb(side, b, a, a + 0.3, y0 + 1.6, y0 + h, 0.0, 0.6, frame)
        lb(side, b, a, c, y0 + h - 0.35, y0 + h, 0.0, 0.6, frame)
        lb(side, b, a, c, y0 + 1.6, y0 + 2.0, 0.0, 0.6, frame)
    lb(side, b, u1 - 0.3, u1, y0 + 1.6, y0 + h, 0.0, 0.6, frame)
    if awning:
        a = awning
        stripes = int((u1 - u0) / 1.5)
        for k in range(stripes):
            lb(side, b, u0 + k * (u1 - u0) / stripes, u0 + (k + 1) * (u1 - u0) / stripes, y0 + h + 0.1 - 0.0, y0 + h + 1.6, 0.0, 4.2 - 0.0, a[k % 2])
        lb(side, b, u0, u1, y0 + h + 1.2, y0 + h + 1.9, 4.2, 4.5, a[0])


def door(side, b, uc, y0, w=4.4, h=7.4, col=None, frame=None, glass=True):
    col = col or PAL['door']
    frame = frame or PAL['white']
    lb(side, b, uc - w / 2 - 0.4, uc - w / 2, y0, y0 + h + 0.5, -0.2, 1.0, frame)               # jambs and header (the leaves stay visible)
    lb(side, b, uc + w / 2, uc + w / 2 + 0.4, y0, y0 + h + 0.5, -0.2, 1.0, frame)
    lb(side, b, uc - w / 2 - 0.4, uc + w / 2 + 0.4, y0 + h, y0 + h + 0.5, -0.2, 1.0, frame)
    lb(side, b, uc - w / 2, uc + w / 2, y0, y0 + h, -0.3, 0.1, shade(col, -0.6))
    for s in (-1, 1):
        a = uc + (0.05 if s > 0 else -w / 2 + 0.0)
        lb(side, b, uc if s > 0 else uc - w / 2 + 0.05, uc + w / 2 - 0.05 if s > 0 else uc - 0.05, y0, y0 + h, 0.1, 0.35, col)
        if glass:
            lb(side, b, (uc + 0.4) if s > 0 else (uc - w / 2 + 0.4), (uc + w / 2 - 0.4) if s > 0 else (uc - 0.4), y0 + 1.6, y0 + h - 0.6, 0.35, 0.45, PAL['glass'], 'G')
        hx = uc + s * 0.5
        lb(side, b, hx - 0.07, hx + 0.07, y0 + 3.2, y0 + 4.6, 0.45, 0.8, PAL['metal'])
    lb(side, b, uc - w / 2 - 1.0, uc + w / 2 + 1.0, y0 + h + 0.6, y0 + h + 1.1, 0.0, 3.4, PAL['white'])        # canopy
    lb(side, b, uc - w / 2 - 1.0, uc + w / 2 + 1.0, y0 + h + 0.1, y0 + h + 0.6, 3.1, 3.4, shade(col, -0.15))
    for sx in (-1, 1):
        lb(side, b, uc + sx * (w / 2 + 0.7) - 0.15, uc + sx * (w / 2 + 0.7) + 0.15, y0, y0 + h + 0.6, 3.1, 3.4, PAL['white'])
    lb(side, b, uc - w / 2 - 1.2, uc + w / 2 + 1.2, y0 - 0.1, y0 + 0.05, 0.0, 3.6, PAL['walk2'])             # threshold step


def building(b, floors, wall, trim, fh=11.0, front='S', ground_h=13.0, win_w=3.8, win_h=5.4, balconies=False, shutters=None, ac_prob=0.15, flowers_prob=0.15,
             storefronts=None, entrance_u=None, name='bldg', roof_col=None, tank=True, seed=0):
    rnd = random.Random(seed)
    BLD.append((name, D.counts(), None))
    H = ground_h + (floors - 1) * fh
    y0 = GY
    box(b.x0, b.x1, y0, y0 + H, b.z0, b.z1, wall)
    collider(b.x0, b.x1, y0, y0 + H + 2.5, b.z0, b.z1, name)
    # plinth + pilasters
    for side in 'SNEW':
        L = b.width(side)
        lb(side, b, -0.3, L + 0.3, y0, y0 + 1.8, 0.0, 0.5, shade(wall, -0.18))
        lb(side, b, -0.35, L + 0.35, y0 + 1.8, y0 + 2.1, 0.0, 0.7, shade(wall, 0.12))
        for u in (0.0, L - 1.4):
            lb(side, b, u - 0.0, u + 1.4, y0, y0 + H, 0.0, 0.5, trim)
    # storey bands
    for f in range(1, floors):
        yb = y0 + ground_h + (f - 1) * fh - 0.9
        for side in 'SNEW':
            L = b.width(side)
            lb(side, b, -0.3, L + 0.3, yb, yb + 0.5, 0.0, 0.6, trim)
    # windows on every side, ground floor handled separately on the front
    for side in 'SNEW':
        L = b.width(side)
        n = max(2, int((L - 4) // (win_w + 2.6)))
        step = (L - 4) / n
        for f in range(floors):
            if f == 0 and side == front:
                continue
            yb = y0 + (3.2 if f == 0 else ground_h + (f - 1) * fh + 2.6)
            for k in range(n):
                uc = 2 + step * (k + 0.5)
                if f == 0 and side != front:
                    window(side, b, uc, yb + 0.6, win_w, win_h - 1.2, frame=trim, shutters=shutters, flowers=rnd.random() < flowers_prob)
                    continue
                band = (f == 1 and side == front)       # the shop board hangs under these windows: no AC units / flower boxes there
                window(side, b, uc, yb, win_w, win_h, frame=trim, shutters=shutters, ac=(rnd.random() < ac_prob) and not band, flowers=(rnd.random() < flowers_prob and f < 4) and not band)
                if balconies and f >= 2 and side == front and k % 2 == 0:
                    balcony(side, b, uc, yb, win_w + 1.6, col=shade(wall, 0.15), rail=PAL['white'])
    # front ground floor
    L = b.width(front)
    if storefronts:
        for (a, c, awn) in storefronts:
            storefront(front, b, a, c, y0 + 1.0, ground_h - 4.0, trim, awning=awn)
    if entrance_u is not None:
        door(front, b, entrance_u, y0, w=5.2, h=8.4, col=PAL['door'], frame=trim)
    cornice(b, y0 + H, trim, layers=3, out=1.1)
    roof_details(R(b.x0, b.x1, b.z0, b.z1), y0 + H + 1.35, rnd, tank=tank)
    BLD[-1] = (name, BLD[-1][1], D.counts())
    return H


# ------------------------------------------------------------------------------------------------------------------
# street furniture
# ------------------------------------------------------------------------------------------------------------------
def street_lamp(x, z, facing=0.0, y=GY):
    D.lathe(x, z, y, [(0.55, 0), (0.55, 0.25), (0.4, 0.4), (0.22, 0.8), (0.18, 8.8)], PAL['dark'], seg=14)
    D.lathe(x, z, y + 8.8, [(0.22, 0), (0.3, 0.2), (0.0, 0.25)], PAL['dark'], seg=12)
    ax, az = math.cos(facing) * 2.4, math.sin(facing) * 2.4
    box(min(x, x + ax) - 0.12, max(x, x + ax) + 0.12, y + 8.6, y + 8.9, min(z, z + az) - 0.12, max(z, z + az) + 0.12, PAL['dark'])
    D.lathe(x + ax, z + az, y + 8.0, [(0.0, 0), (0.55, 0.1), (0.95, 0.55), (0.6, 0.62), (0.0, 0.7)], PAL['metal'], seg=14)
    D.sphere(x + ax, y + 8.1, z + az, 0.55, 0.28, 0.55, PAL['yellow'], seg=10, rings=5, kind='N')
    LIGHTS.append((x + ax, y + 7.8, z + az, 30))
    collider(x - 0.55, x + 0.55, y, y + 9, z - 0.55, z + 0.55, 'lamp')


def tree(x, z, h=9.0, r=4.4, seed=0, y=GY, pit=True):
    rnd = random.Random(seed * 13 + int(x * 7 + z * 3))
    TREES.append((x, z, r))
    if pit:
        box(x - 1.5, x + 1.5, y, y + 0.35, z - 1.5, z + 1.5, PAL['soil'])
        for sx in (-1, 1):
            box(x + sx * 1.5 - 0.15, x + sx * 1.5 + 0.15, y, y + 0.55, z - 1.65, z + 1.65, PAL['metal'])
            box(x - 1.65, x + 1.65, y, y + 0.55, z + sx * 1.5 - 0.15, z + sx * 1.5 + 0.15, PAL['metal'])
    D.lathe(x, z, y, [(0.55, 0), (0.42, 1.5), (0.34, h * 0.55), (0.24, h)], PAL['wood2'], seg=10)
    for k in range(3):
        a = rnd.uniform(0, 6.28)
        box(x + math.cos(a) * 0.5 - 0.1, x + math.cos(a) * 1.6 + 0.1, y + h * 0.6 + k * 0.6, y + h * 0.6 + k * 0.6 + 0.2, z + math.sin(a) * 0.5 - 0.1, z + math.sin(a) * 1.6 + 0.1, PAL['wood2'])
    greens = [PAL['grass2'], PAL['green'], PAL['grass'], '#4FB04A']
    for k in range(9):
        a = rnd.uniform(0, 6.28)
        d = rnd.uniform(0, r * 0.62)
        rr = rnd.uniform(0.52, 0.85) * r
        D.sphere(x + math.cos(a) * d, y + h + rnd.uniform(-0.4, r * 0.75), z + math.sin(a) * d, rr, rr * 0.85, rr, greens[k % 4], seg=12, rings=8, jitter=0.06, seed=k + seed)
    collider(x - 0.6, x + 0.6, y, y + h, z - 0.6, z + 0.6, 'tree')


def bench(x, z, rot=0.0, y=GY, col=True):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    def P(lx, lz): return x + lx * c - lz * s, z + lx * s + lz * c
    for lx in (-2.1, 2.1):
        for lz in (-0.55, 0.55):
            px, pz = P(lx, lz)
            cbox(px, y + 0.5, pz, 0.28, 1.0, 0.28, PAL['dark'], rot=-rot)
    for k in range(5):
        px, pz = P(0, -0.7 + k * 0.35)
        cbox(px, y + 1.0, pz, 4.8, 0.14, 0.28, PAL['wood'], rot=-rot)
    for k in range(3):
        px, pz = P(0, -0.82)
        cbox(px, y + 1.5 + k * 0.4, pz, 4.8, 0.3, 0.14, PAL['wood'], rot=-rot)
    for lx in (-2.1, 2.1):
        px, pz = P(lx, -0.8)
        cbox(px, y + 1.4, pz, 0.28, 1.6, 0.28, PAL['dark'], rot=-rot)
        px, pz = P(lx, 0.2)
        cbox(px, y + 1.55, pz, 0.3, 0.2, 1.6, PAL['dark'], rot=-rot)
    if col:
        hx, hz = (2.6, 1.2) if round(rot) % 180 == 0 else (1.2, 2.6)
        collider(x - hx, x + hx, y, y + 3, z - hz, z + hz, 'bench')


def hydrant(x, z, y=GY):
    D.lathe(x, z, y, [(0.55, 0), (0.55, 0.2), (0.42, 0.3), (0.42, 1.6), (0.52, 1.7), (0.52, 1.95), (0.3, 2.1), (0.0, 2.2)], PAL['red'], seg=14)
    for s in (-1, 1):
        cyl(x + s * 0.5, z, y + 1.1, y + 1.5, 0.2, PAL['red'], seg=10)
        cyl(x + s * 0.7, z, y + 1.1, y + 1.5, 0.26, shade(PAL['red'], -0.2), seg=10, caps=True)
    collider(x - 0.6, x + 0.6, y, y + 2.2, z - 0.6, z + 0.6, 'hydrant')


def trash_bin(x, z, y=GY):
    D.lathe(x, z, y, [(0.7, 0), (0.78, 0.1), (0.85, 2.0), (0.9, 2.1), (0.9, 2.3), (0.0, 2.35)], PAL['green'], seg=14)
    for k in range(4):
        D.lathe(x, z, y + 0.4 + k * 0.45, [(0.86, 0), (0.86, 0.1)], PAL['dark'], seg=14)
    collider(x - 0.9, x + 0.9, y, y + 2.4, z - 0.9, z + 0.9, 'bin')


def mailbox(x, z, y=GY):
    box(x - 0.6, x + 0.6, y + 2.0, y + 3.4, z - 0.6, z + 0.6, PAL['blue'])
    cyl(x, z, y + 3.4, y + 3.4 + 0.05, 0.6, PAL['blue'], seg=12)
    D.lathe(x, z, y + 3.4, [(0.6, 0), (0.45, 0.35), (0.0, 0.5)], PAL['blue'], seg=12)
    box(x - 0.2, x + 0.2, y, y + 2.0, z - 0.2, z + 0.2, PAL['dark'])
    box(x - 0.35, x + 0.35, y + 2.6, y + 2.75, z + 0.6, z + 0.7, PAL['dark'])
    collider(x - 0.7, x + 0.7, y, y + 4, z - 0.7, z + 0.7, 'mailbox')


def bollard(x, z, y=GY):
    D.lathe(x, z, y, [(0.35, 0), (0.35, 2.4), (0.0, 2.6)], PAL['yellow'], seg=10)
    cyl(x, z, y + 1.8, y + 2.0, 0.37, PAL['dark'], seg=10)
    collider(x - 0.4, x + 0.4, y, y + 2.6, z - 0.4, z + 0.4, 'bollard')


def traffic_light(x, z, arm_dir, y=GY):
    D.lathe(x, z, y, [(0.45, 0), (0.3, 0.5), (0.2, 11.0)], PAL['dark'], seg=10)
    ax, az = arm_dir
    ex, ez = x + ax * 7.0, z + az * 7.0
    box(min(x, ex) - 0.15, max(x, ex) + 0.15, y + 10.6, y + 10.95, min(z, ez) - 0.15, max(z, ez) + 0.15, PAL['dark'])
    for px, pz in ((ex, ez), (x + ax * 0.4, z + az * 0.4)):
        box(px - 0.5, px + 0.5, y + 8.2, y + 10.6, pz - 0.5, pz + 0.5, PAL['dark'])
        for k, col in enumerate((PAL['red'], PAL['yellow'], PAL['green'])):
            D.sphere(px, y + 10.0 - k * 0.8, pz, 0.34, 0.34, 0.34, col, seg=8, rings=5, kind='N' if k == 2 else 'O')
    collider(x - 0.5, x + 0.5, y, y + 11, z - 0.5, z + 0.5, 'tlight')


def car(x, z, rot, col, y=GY, seed=0):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    def P(lx, lz): return x + lx * c - lz * s, z + lx * s + lz * c
    L, W = 9.4, 4.0
    def B(lx, lz, ly0, ly1, sx, sz, color, kind='O'):
        px, pz = P(lx, lz)
        cbox(px, y + (ly0 + ly1) / 2, pz, sx, ly1 - ly0, sz, color, kind, rot=-rot)
    B(0, 0, 0.9, 2.1, L, W, col)
    B(0.3, 0, 2.1, 3.3, 5.0, W - 0.5, col)
    B(0.3, 0, 2.1, 3.3, 5.0, W - 0.45, PAL['glass'], 'G')
    B(0.3, 0, 3.3, 3.55, 4.6, W - 0.9, shade(col, -0.1))
    B(0, 0, 0.55, 0.9, L - 0.6, W - 0.5, PAL['dark'])
    B(L / 2, 0, 1.2, 1.7, 0.3, W - 0.8, PAL['dark'])
    B(-L / 2, 0, 1.2, 1.7, 0.3, W - 0.8, PAL['dark'])
    for sy in (-1, 1):
        B(L / 2 + 0.05, sy * 1.35, 1.25, 1.65, 0.2, 0.7, PAL['yellow'], 'N')
        B(-L / 2 - 0.05, sy * 1.35, 1.3, 1.6, 0.2, 0.7, PAL['red'], 'N')
        for wx in (-3.1, 3.1):
            px, pz = P(wx, sy * 1.98)
            wheel(px, y + 0.95, pz, rot)
    B(0, 0, 2.0, 2.15, 2.4, W + 0.1, shade(col, 0.2))
    hx, hz = (L / 2, W / 2) if round(rot) % 180 == 0 else (W / 2, L / 2)
    collider(x - hx, x + hx, y, y + 3.6, z - hz, z + hz, 'car')


def wheel(px, py, pz, rot):
    seg = 14
    r = 0.95
    th = 0.7
    v, f = [], []
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    # axis along local z -> world direction (-s, 0, c)
    ax, az = -s, c
    for side in (-1, 1):
        for i in range(seg):
            a = 2 * math.pi * i / seg
            lx, ly = r * math.cos(a), r * math.sin(a)
            v.append((px + lx * c + (side * th / 2) * ax, py + ly, pz + lx * s + (side * th / 2) * az))
    for i in range(seg):
        j = (i + 1) % seg
        f.append((i, j, seg + j, seg + i))
    f.append(tuple(range(seg - 1, -1, -1)))
    f.append(tuple(seg + i for i in range(seg)))
    D._add('O', v, f, PAL['dark'])
    # hub cap
    hub = []
    for i in range(8):
        a = 2 * math.pi * i / 8
        lx, ly = 0.45 * math.cos(a), 0.45 * math.sin(a)
        hub.append((px + lx * c + (th / 2 + 0.05) * ax, py + ly, pz + lx * s + (th / 2 + 0.05) * az))
    hub.append((px + (th / 2 + 0.05) * ax, py, pz + (th / 2 + 0.05) * az))
    D._add('O', hub, [(8, i, (i + 1) % 8) for i in range(8)], PAL['metal'])
    D._add('O', [(h[0] - 0.0 * ax, h[1], h[2]) for h in hub], [(8, (i + 1) % 8, i) for i in range(8)], PAL['metal'])


exec(compile(open(os.path.join(HERE, 'layout.py'), encoding='utf-8').read(), 'layout.py', 'exec'))
exec(compile(open(os.path.join(HERE, 'fillers.py'), encoding='utf-8').read(), 'fillers.py', 'exec'))
exec(compile(open(os.path.join(HERE, 'audit.py'), encoding='utf-8').read(), 'audit.py', 'exec'))
exec(compile(open(os.path.join(HERE, 'audit2.py'), encoding='utf-8').read(), 'audit2.py', 'exec'))
exec(compile(open(os.path.join(HERE, 'export_part.py'), encoding='utf-8').read(), 'export_part.py', 'exec'))
