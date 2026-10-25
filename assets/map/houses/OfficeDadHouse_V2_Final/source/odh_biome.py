"""OfficeDadHouse_V2_Final -- biome around the lot: street grid in the office-house style, EMPTY neighbour houses with their own lots, a supermarket and a bank.
Everything here is look-only (solid blocks, no interiors).  Collection 'Biome'.  Plot coordinates as in odh_site (our lot x 0..104, z 0..100)."""
import math
import random
import odh_core as K
from odh_core import *
import odh_models as M
import odh_detail as D
import odh_car as CAR
from odh_site import LOT_W, LOT_D

BC = 'Biome'
ORG = D.ORG


def place(fn, x, z, rot=0.0, *a, c=BC, y0=0.0, **k):
    K.tf_push(x, z, y0, rot)
    r = fn(c, *a, **k)
    K.tf_pop()
    return r

ROAD_Z0, ROAD_Z1 = -22.0, -6.6          # asphalt between the two rows of lots
SIDE_A = (-6.0, 0.0)                    # sidewalk in front of the south row (our row)
SIDE_B = (-28.0, -22.0)                 # sidewalk in front of the north row
ROW_A_Z0, ROW_B_Z1 = 0.0, -28.0         # lot fronts
BX0, BX1 = -223.0, 327.0                # biome extent (cross streets at both ends)
BZ0, BZ1 = -140.0, 112.0

WALLS = ('stucco', 'stucco_dk', 'wall_hall', 'wall_uph', 'wall_liv', 'siding')
ROOFS = ('roof', 'roof_dk')
CAR_SC = 1.0          # parked cars: same size as the father's car (roomy for Roblox characters)
CARS = ('car', 'red', 'blue', 'white', 'orange', 'teal', 'metal')


def b(color, x0, x1, h0, h1, z0, z1, solid=False):
    B(BC, color, x0, x1, h0, h1, z0, z1, solid=solid)


# ------------------------------------------------------------------ 5x7 pixel font for signs
FONT = {
    'B': ('1111.', '1...1', '1...1', '1111.', '1...1', '1...1', '1111.'), 'A': ('.111.', '1...1', '1...1', '11111', '1...1', '1...1', '1...1'),
    'N': ('1...1', '11..1', '1.1.1', '1..11', '1...1', '1...1', '1...1'), 'K': ('1...1', '1..1.', '1.1..', '11...', '1.1..', '1..1.', '1...1'),
    'S': ('.1111', '1....', '1....', '.111.', '....1', '....1', '1111.'), 'U': ('1...1', '1...1', '1...1', '1...1', '1...1', '1...1', '.111.'),
    'P': ('1111.', '1...1', '1...1', '1111.', '1....', '1....', '1....'), 'E': ('11111', '1....', '1....', '1111.', '1....', '1....', '11111'),
    'R': ('1111.', '1...1', '1...1', '1111.', '1.1..', '1..1.', '1...1'), 'M': ('1...1', '11.11', '1.1.1', '1.1.1', '1...1', '1...1', '1...1'),
    'T': ('11111', '..1..', '..1..', '..1..', '..1..', '..1..', '..1..'),
}


def sign_text(txt, x_c, h0, z, px, color, face=0, depth=0.5):
    """pixel letters centred at x_c on a wall whose outward normal is -z (face 0) or +z (face 180); px = pixel size"""
    n = len(txt)
    w = n * 6 * px
    x = x_c - w / 2
    for ch in txt:
        g = FONT[ch]
        for r, row in enumerate(g):
            for c_, v in enumerate(row):
                if v == '1':
                    xx = x + c_ * px
                    hh = h0 + (6 - r) * px
                    if face == 0:
                        b(color, xx, xx + px, hh, hh + px, z - depth, z)
                    else:
                        b(color, xx, xx + px, hh, hh + px, z, z + depth)
        x += 6 * px


# ------------------------------------------------------------------ streets
def asphalt_strip_x(x0, x1, z0, z1):
    b('asphalt', x0, x1, -0.3, 0.0, z0, z1, solid=True)


def streets():
    asphalt_strip_x(BX0, BX1, ROAD_Z0, ROAD_Z1)                          # main street
    asphalt_strip_x(312.0, 327.0, BZ0, BZ1)                              # east cross street
    asphalt_strip_x(-223.0, -208.0, BZ0, BZ1)                            # west cross street
    # centre line and edge lines
    x = BX0
    while x < BX1:
        if not (300 < x < 330 or -230 < x < -205):
            b('line', x, x + 5.0, 0.0, 0.04, (ROAD_Z0 + ROAD_Z1) / 2 - 0.2, (ROAD_Z0 + ROAD_Z1) / 2 + 0.2)
        x += 10.0
    b('white', BX0, BX1, 0.0, 0.03, ROAD_Z1 - 0.8, ROAD_Z1 - 0.6)
    b('white', BX0, BX1, 0.0, 0.03, ROAD_Z0 + 0.6, ROAD_Z0 + 0.8)
    z = BZ0
    while z < BZ1:
        for cx in (319.5, -215.5):
            if not (ROAD_Z0 - 4 < z < ROAD_Z1 + 4):
                b('line', cx - 0.2, cx + 0.2, 0.0, 0.04, z, z + 5.0)
        z += 10.0
    # crosswalks near the lot of ours
    for x0 in (-6.0, 108.0):
        for k in range(8):
            b('white', x0 + k * 1.8, x0 + k * 1.8 + 1.0, 0.0, 0.04, ROAD_Z0 + 1.2, ROAD_Z1 - 1.2)
    # sidewalks: row A (our row) and row B, plus kerbs
    for (zs, zk0, zk1) in ((SIDE_A, ROAD_Z1, ROAD_Z1 + 0.6), (SIDE_B, ROAD_Z0 - 0.6, ROAD_Z0)):
        for (xa, xb) in ((-208.0, -2.0), (106.0, 312.0)) if zs == SIDE_A else ((-208.0, 312.0),):
            D.pavers(BC, xa, xb, zs[0], zs[1], -0.2, 0.12, 3.0, seed=int(xa) + int(zs[0]))
            b('curb', xa, xb, -0.2, 0.25, zk0, zk1)
            b('curb_top', xa, xb, 0.25, 0.3, zk0 + 0.12, zk1 - 0.12)
            gz = (zk0 - 1.3, zk0) if zs == SIDE_A else (zk1, zk1 + 1.3)          # gutter strip in the road along the kerb
            b('gutter', xa, xb, 0.0, 0.03, gz[0], gz[1])
            xd = xa + 14.0
            while xd < xb - 6.0:                                                  # storm drain grates in the gutter
                b('dark', xd, xd + 3.0, 0.03, 0.08, gz[0] + 0.15, gz[1] - 0.15)
                for g in range(5):
                    b('metal_dk', xd + 0.3 + g * 0.55, xd + 0.45 + g * 0.55, 0.08, 0.1, gz[0] + 0.15, gz[1] - 0.15)
                xd += 52.0
    b('walk', 312.0, 327.0 + 6.0, -0.2, 0.12, BZ0, BZ1) if False else None
    # grass beyond the streets
    b('lawn', BX0 - 80.0, BX1 + 80.0, -1.2, -0.31, BZ0 - 60.0, BZ1 + 60.0, solid=True)
    for x in (-150.0, 60.0, 150.0, 260.0):
        place(M.manhole, x, -14.0, 0)
    for x in range(-200, 320, 52):
        place(M.lamp_post, x + 14.0, -4.8, 0)
        place(M.lamp_post, x + 40.0, -25.0, 180)
    for x in range(-200, 320, 52):
        place(M.hydrant, x + 28.0, -4.4, 0) if x % 104 == 0 else None
    # tactile paving at the crossings, crossings' planters, street / stop signs, bus shelters, bins
    for (xa, xb) in ((-6.0, 8.4), (108.0, 122.4)):
        D.tactile(BC, xa, xb, -23.8, -22.0, 0.12)
    D.tactile(BC, 108.0, 122.4, -6.0, -3.8, 0.12)
    D.tactile(BC, -6.0, -2.0, -6.0, -3.8, 0.12)
    D.planter(BC, -10.0, -4.5, 0)
    D.planter(BC, -10.0, -25.0, 0)
    D.planter(BC, 126.0, -4.5, 0)
    D.planter(BC, 126.0, -25.0, 0)
    D.street_sign(BC, -205.0, -4.0, 0)
    D.street_sign(BC, 309.0, -26.0, 180)
    D.stop_sign(BC, -207.0, -8.5, 0)
    D.stop_sign(BC, 311.0, -20.0, 180)
    D.bus_shelter(BC, -34.0, -25.0, 0)
    D.bus_shelter(BC, 150.0, -3.5, 180)
    for x in range(-190, 300, 104):
        place(M.trash_can, x + 6.0, -1.5, 0)
        place(M.trash_can, x + 58.0, -26.5, 0)
        D.bollard(BC, x + 30.0, -5.2)


# ------------------------------------------------------------------ one lot: lawn, fence, driveway, trees
def lot_ground(x0, row, w=104.0, d=100.0, seed=1):
    """row 'A': lot at z 0..d facing -z (street at z<0); row 'B': lot at z -28-d..-28 facing +z"""
    rnd = random.Random(seed)
    if row == 'A':
        z0, z1 = 0.0, d
    else:
        z0, z1 = ROW_B_Z1 - d, ROW_B_Z1
    b('lawn', x0, x0 + w, -1.0, 0.0, z0, z1, solid=True)
    front = z0 + 1.5 if row == 'A' else z1 - 1.5
    # fence: front (with a gate gap), sides, back
    gx = x0 + rnd.uniform(34.0, 56.0)
    M.fence_line(BC, x0, front, gx, front)
    M.fence_line(BC, gx + 8.0, front, x0 + w, front)
    M.fence_line(BC, x0, z0 if row == 'B' else front, x0, z1 if row == 'A' else z1)
    M.fence_line(BC, x0 + w, z0 if row == 'B' else front, x0 + w, z1 if row == 'A' else z1)
    M.fence_line(BC, x0, z1 if row == 'A' else z0, x0 + w, z1 if row == 'A' else z0)
    return gx, z0, z1


AVOID = []      # rectangles (x0, x1, z0, z1) trees and bushes must keep out of: buildings, driveways, paths, parking


def free_spot(rnd, xa, xb, za, zb, pad=6.0, tries=400):
    """pad = radius that must stay clear around every AVOID rectangle (the tree crown radius for trees)"""
    for _ in range(tries):
        x, z = rnd.uniform(xa, xb), rnd.uniform(za, zb)
        if all(not (r[0] - pad < x < r[1] + pad and r[2] - pad < z < r[3] + pad) for r in AVOID):
            return x, z
    return None


def tree_row(x0, row, w=104.0, d=100.0, seed=1):
    rnd = random.Random(seed + 50)
    z0, z1 = (0.0, d) if row == 'A' else (ROW_B_Z1 - d, ROW_B_Z1)
    for k in range(4):
        kind = rnd.choice(('oak', 'oak', 'maple', 'cherry', 'birch', 'spruce'))
        sc_ = rnd.uniform(0.9, 1.2)
        sd_ = rnd.randint(1, 30)
        p = free_spot(rnd, x0 + 6.0, x0 + w - 6.0, z0 + 6.0, z1 - 6.0, 7.0 * sc_ + 1.5)      # crown radius ~ 7 * scale: stays off houses, driveways, parking
        if p:
            D.tree_at(p[0], p[1], sc_, sd_, kind)
    for k in range(3):
        p = free_spot(rnd, x0 + 6.0, x0 + w - 6.0, z0 + 6.0, z1 - 6.0, 3.0)
        if p:
            place(M.bush, p[0], p[1], 0, rnd.uniform(0.9, 1.3), rnd.randint(1, 20), c=ORG)


# ------------------------------------------------------------------ the empty office-style neighbour house
def office_nb(x0, row, seed, w=None, d=None, floors=None, lot_w=104.0, lot_d=100.0):
    rnd = random.Random(seed)
    w = w or rnd.choice((44.0, 48.0, 52.0, 56.0))
    d = d or rnd.choice((38.0, 42.0, 46.0, 50.0))
    floors = floors or rnd.choice((1, 2, 2))
    wall = rnd.choice(WALLS)
    roof = rnd.choice(ROOFS)
    fh = 13.75
    H = fh * floors
    # world frame: front faces -z for row A, +z for row B; build in local (u east, v away from the street) and map
    if row == 'A':
        zf = 16.0
        zm = lambda v: zf + v
    else:
        zf = ROW_B_Z1 - 16.0
        zm = lambda v: zf - v
    xm = lambda u: x0 + rnd.uniform(0, 0) + u
    bx = x0 + rnd.uniform(14.0, lot_w - w - 14.0)
    X_ = lambda u: bx + u
    Z_ = zm
    b('plinth', X_(-0.6), X_(w + 0.6), 0.0, 1.0, Z_(-0.6), Z_(d + 0.6))
    b(wall, X_(0), X_(w), 1.0, 1.0 + H, Z_(0), Z_(d), solid=True)
    for f in range(1, floors):
        b('trim', X_(-0.4), X_(w + 0.4), 1.0 + fh - 0.4, 1.0 + fh + 0.4, Z_(-0.4), Z_(d + 0.4))
    b(roof, X_(-1.6), X_(w + 1.6), 1.0 + H, 2.0 + H, Z_(-1.6), Z_(d + 1.6))
    for (a, b_, c, d_) in ((-1.6, w + 1.6, -1.6, -0.9), (-1.6, w + 1.6, d + 0.9, d + 1.6), (-1.6, -0.9, -0.9, d + 0.9), (w + 0.9, w + 1.6, -0.9, d + 0.9)):
        b('parapet', X_(a), X_(b_), 2.0 + H, 3.2 + H, Z_(c), Z_(d_))
    for k in range(rnd.randint(1, 3)):
        ux, uz = rnd.uniform(6.0, w - 9.0), rnd.uniform(6.0, d - 8.0)
        b('metal', X_(ux), X_(ux + 5.0), 2.0 + H, 5.0 + H, *sorted((Z_(uz), Z_(uz + 4.0))))
        b('metal_dk', X_(ux + 0.3), X_(ux + 4.7), 5.0 + H, 5.25 + H, *sorted((Z_(uz + 0.3), Z_(uz + 3.7))))
        for g in range(6):
            b('metal_dk', X_(ux + 0.4 + g * 0.75), X_(ux + 0.6 + g * 0.75), 2.4 + H, 4.6 + H, *sorted((Z_(uz - 0.1), Z_(uz))))
    K.tf_push(X_(w * 0.7), Z_(d * 0.5), 2.0 + H, 0)
    M.tube(BC, 'metal_dk', [(0, 0, 0), (0, 2.6, 0)], 0.3, 8)
    M.cylinder(BC, 'metal', 0, 0, 2.6, 0.3, 0.55, 10)
    K.tf_pop()
    b('trim', X_(-1.7), X_(w + 1.7), 3.2 + H, 3.5 + H, *sorted((Z_(-1.7), Z_(-0.8))))
    # facade: framed windows with panes, curtains, shutters and flower boxes; panelled door with porch; cornices, quoins, base course
    fs = _FACE[0]
    shut = rnd.choice((None, 'sign_green', 'navy', 'brick', 'teal'))
    n = max(3, int(w // 11))
    for f in range(floors):
        y0 = 1.0 + f * fh + 4.2
        for k in range(n):
            u = w * (k + 0.5) / n
            if f == 0 and k == n // 2:
                continue
            D.window_det(BC, X_(u), y0, 6.0, 5.2, Z_(0), fs, shutters=shut if floors > 1 or True else None, box=(f == 0), curtain=rnd.randint(0, 2), seed=seed + k)
        for vv in (d * 0.3, d * 0.7):
            window_s(X_(0), y0, 5.0, 5.0, Z_(vv))
            window_s(X_(w), y0, 5.0, 5.0, Z_(vv))
    for f in range(1, floors):
        D.cornice(BC, X_(0), X_(w), 1.0 + f * fh - 0.9, Z_(0), fs, 0, 0)
    D.cornice(BC, X_(0), X_(w), 1.0 + H - 1.7, Z_(0), fs, 0, 0)
    for ux in (0.0, w):
        D.quoins(BC, X_(ux), Z_(0), fs, 1.0, 1.0 + H - 2.0, 1 if ux == 0.0 else -1)
    # base course (stone) around the house, downspouts at the front corners
    for (xa, xb, za, zb) in ((-0.4, w + 0.4, -0.4, 0.0), (-0.4, 0.0, 0.0, d), (w, w + 0.4, 0.0, d)):
        zs_ = sorted((Z_(za), Z_(zb)))
        b('stone_dk', X_(xa), X_(xb), 1.0, 4.0, zs_[0], zs_[1])
    for ux in (1.0, w - 1.0):
        D.downspout(BC, X_(ux), Z_(-0.5), 1.0 + H)
    uc = w * (n // 2 + 0.5) / n
    D.front_door(BC, X_(uc), Z_(0), fs, 1.0, rnd.choice(('door', 'door2', 'navy', 'brick')))
    b('roof', X_(uc - 5.2), X_(uc + 5.2), 12.2, 13.0, Z_(-5.0), Z_(0.0))
    b('trim', X_(uc - 5.4), X_(uc + 5.4), 13.0, 13.4, Z_(-5.2), Z_(0.0))
    for ux in (uc - 4.6, uc + 4.6):
        b('trim', X_(ux - 0.4), X_(ux + 0.4), 1.0, 12.2, Z_(-4.8), Z_(-4.0))
        b('stone', X_(ux - 0.7), X_(ux + 0.7), 1.0, 1.6, Z_(-5.1), Z_(-3.7))
        b('stone', X_(ux - 0.7), X_(ux + 0.7), 11.6, 12.2, Z_(-5.1), Z_(-3.7))
    b('stone', X_(uc - 5.2), X_(uc + 5.2), 0.0, 1.0, Z_(-5.4), Z_(-0.6))
    for k in range(3):
        b('concrete', X_(uc - 5.2 - 0.0), X_(uc + 5.2), 0.0, 0.33 * (3 - k), *sorted((Z_(-5.4 - 1.1 * k), Z_(-6.5 - 1.1 * k))))
    b('trim', X_(uc - 5.4), X_(uc + 5.4), 0.4, 1.0, *sorted((Z_(-5.4), Z_(-5.6)))) if False else None
    # driveway + path from the gate
    dw0 = x0 + 4.0 if rnd.random() < 0.5 else x0 + lot_w - 22.0
    sgn = 1 if row == 'A' else -1
    zs0, zs1 = (0.0, zm(d * 0.8)) if row == 'A' else (zm(d * 0.8), ROW_B_Z1)
    D.pavers(BC, dw0, dw0 + 16.0, min(zs0, zs1), max(zs0, zs1), 0.0, 0.12, 4.0, tones=('walk_c', 'walk_b', 'walk_c'), seed=seed, solid=False)
    D.pavers(BC, X_(uc - 2.6), X_(uc + 2.6), min(Z_(-5.2), (ROW_B_Z1 if row == 'B' else 0.0)), max(Z_(-5.2), ROW_B_Z1 if row == 'B' else 0.0), 0.0, 0.1, 2.6, tones=('walk', 'walk_b'), seed=seed + 5, solid=False)
    # a parked car on some of the driveways
    if rnd.random() < 0.7:
        cz = zm(18.0)
        K.tf_push(dw0 + 8.0, cz, 0, 180 if row == 'A' else 0)
        CAR.dad_car(ORG, rnd.choice(CARS), sc=CAR_SC, trim=False)
        K.tf_pop()
        K.COLL.append(('box', dw0 + 8.0, cz, 6.6 * CAR_SC, 15.4 * CAR_SC, 4.9 * CAR_SC))
    for ux in (6.0, w - 6.0):
        place(M.flower_patch, X_(ux), Z_(-3.4), 0, 7.0, 2.4, seed + int(ux), c=ORG)
    for ux in (-2.0, w + 2.0):
        place(M.bush, X_(ux), Z_(-2.5), 0, 1.0, seed + int(ux), c=ORG)
    place(M.mailbox, x0 + rnd.uniform(10.0, 30.0), -3.0 if row == 'A' else ROW_B_Z1 + 3.0, 180 if row == 'A' else 0)
    za, zb = sorted((Z_(-6.0), Z_(d + 2.0)))
    AVOID.append((bx - 2.0, bx + w + 2.0, za, zb))
    AVOID.append((dw0, dw0 + 16.0, min(zs0, zs1), max(zs0, zs1)))
    AVOID.append((bx + uc - 3.0, bx + uc + 3.0, min(Z_(-6.0), ROW_B_Z1 if row == 'B' else 0.0), max(Z_(-6.0), ROW_B_Z1 if row == 'B' else 0.0)))
    return bx, w, d, H


def window_b(xc, y0, w, h, zf, sgn):
    """front window: trim frame, glass, mullions, sill.  zf = z of the facade; sgn = -1 faces -z, +1 faces +z (we always pass the building's own front sign)"""
    s = -1 if zf is not None else 1
    b('trim', xc - w / 2 - 0.3, xc + w / 2 + 0.3, y0 - 0.4, y0 + h + 0.3, zf - 0.05 if s < 0 else zf, zf if s < 0 else zf + 0.05) if False else None


# real window helpers (front/side) are defined after the facing convention is fixed per call: see _FACE
_FACE = [-1]


def window_b(xc, y0, w, h, zf, sgn):          # noqa: F811
    s = _FACE[0]
    z_in, z_out = (zf, zf + s * 0.35)
    b('trim', xc - w / 2 - 0.35, xc + w / 2 + 0.35, y0 - 0.45, y0 + h + 0.35, min(z_in, z_out), max(z_in, z_out))
    za, zb = (zf + s * 0.1, zf + s * 0.4)
    b('glass', xc - w / 2, xc + w / 2, y0, y0 + h, min(za, zb), max(za, zb))
    b('trim', xc - 0.15, xc + 0.15, y0, y0 + h, min(zf + s * 0.35, zf + s * 0.45), max(zf + s * 0.35, zf + s * 0.45))
    b('trim', xc - w / 2, xc + w / 2, y0 + h * 0.5 - 0.15, y0 + h * 0.5 + 0.15, min(zf + s * 0.35, zf + s * 0.45), max(zf + s * 0.35, zf + s * 0.45))
    za, zb = (zf + s * 0.2, zf + s * 1.0)
    b('trim', xc - w / 2 - 0.5, xc + w / 2 + 0.5, y0 - 0.9, y0 - 0.45, min(za, zb), max(za, zb))


def window_s(xw, y0, w, h, zc):
    for sx in (-1, 1):
        pass
    b('trim', xw - 0.4, xw + 0.4, y0 - 0.45, y0 + h + 0.35, zc - w / 2 - 0.35, zc + w / 2 + 0.35)
    b('glass', xw - 0.5, xw + 0.5, y0, y0 + h, zc - w / 2, zc + w / 2)


# ------------------------------------------------------------------ bank (row B, x -104..0)
def bank(x0=-104.0):
    lot_ground(x0, 'B', 104.0, 100.0, 61)
    bx, bw, bd = x0 + 20.0, 64.0, 44.0
    zf = ROW_B_Z1 - 22.0              # front face of the bank (faces +z)
    X_ = lambda u: bx + u
    Z_ = lambda v: zf - v
    H = 22.0
    # forecourt paving and steps
    D.pavers(BC, x0 + 4.0, x0 + 100.0, ROW_B_Z1 - 1.5, zf, 0.0, 0.1, 3.0, seed=7, solid=False)
    D.planter(BC, X_(6.0), Z_(-8.0), 0)
    D.planter(BC, X_(bw - 6.0), Z_(-8.0), 0)
    D.bike_rack(BC, X_(bw + 6.0), Z_(-4.0), 90)
    for ux in (10.0, bw - 10.0):
        D.bollard(BC, X_(ux), Z_(-12.0))
    b('plinth', X_(-1.0), X_(bw + 1.0), 0.0, 1.0, Z_(-12.0), Z_(bd + 1.0))
    for k in range(5):
        b('concrete', X_(14.0 + k * 0.0), X_(bw - 14.0), 0.0, 0.3 + 0.28 * k, Z_(-9.0 + k * 1.8 + 1.8), Z_(-9.0 + k * 1.8))
    b('stucco_dk', X_(0), X_(bw), 1.0, 1.0 + H, Z_(0), Z_(bd), solid=True)
    b('trim', X_(-0.5), X_(bw + 0.5), 1.0 + H - 1.6, 1.0 + H, Z_(-0.5), Z_(bd + 0.5))
    b('roof', X_(-1.8), X_(bw + 1.8), 1.0 + H, 2.0 + H, Z_(-1.8), Z_(bd + 1.8))
    for (a, b_, c, d_) in ((-1.8, bw + 1.8, -1.8, -1.0), (-1.8, bw + 1.8, bd + 1.0, bd + 1.8), (-1.8, -1.0, -1.0, bd + 1.0), (bw + 1.0, bw + 1.8, -1.0, bd + 1.0)):
        b('parapet', X_(a), X_(b_), 2.0 + H, 3.4 + H, Z_(c), Z_(d_))
    # portico with columns
    b('trim', X_(12.0), X_(bw - 12.0), 1.0 + H - 3.6, 1.0 + H - 2.0, Z_(-9.5), Z_(0.0))
    b('parapet', X_(11.0), X_(bw - 11.0), 1.0 + H - 2.0, 1.0 + H - 0.4, Z_(-10.0), Z_(0.0))
    for k in range(6):
        ux = 14.0 + k * (bw - 28.0) / 5.0
        b('trim', X_(ux - 1.0), X_(ux + 1.0), 1.3, 1.0 + H - 3.6, Z_(-8.2), Z_(-6.2), solid=True)
        b('trim', X_(ux - 1.3), X_(ux + 1.3), 1.3, 2.0, Z_(-8.5), Z_(-5.9))
        b('trim', X_(ux - 1.3), X_(ux + 1.3), 1.0 + H - 4.2, 1.0 + H - 3.6, Z_(-8.5), Z_(-5.9))
    # glass entrance + windows
    b('glass', X_(bw / 2 - 5.0), X_(bw / 2 + 5.0), 1.0, 12.0, Z_(-0.1), Z_(0.0))
    b('door', X_(bw / 2 - 0.2), X_(bw / 2 + 0.2), 1.0, 12.0, Z_(-0.2), Z_(0.0))
    for k in range(6):
        ux = 6.0 + k * 10.0 if k < 3 else bw - 6.0 - (5 - k) * 10.0
        if abs(ux - bw / 2) < 9:
            continue
        b('trim', X_(ux - 3.4), X_(ux + 3.4), 4.2, 15.6, Z_(-0.35), Z_(0.0))
        b('glass', X_(ux - 3.0), X_(ux + 3.0), 4.6, 15.2, Z_(-0.5), Z_(-0.1))
    for ux in (6.0, 16.0, 48.0, 58.0):
        pass
    # sign band + pixel letters
    b('navy', X_(bw / 2 - 16.0), X_(bw / 2 + 16.0), 1.0 + H - 3.4, 1.0 + H + 0.2, Z_(-10.6), Z_(-10.0))
    sign_text('BANK', X(bw / 2) if False else X_(bw / 2), 1.0 + H - 3.2, Z_(-10.6), 0.62, 'brass', 180, 0.4)
    # ATM and flag poles
    b('metal_dk', X_(bw - 9.0), X_(bw - 5.0), 1.0, 7.5, Z_(-0.6), Z_(0.0))
    b('screen', X_(bw - 8.4), X_(bw - 5.6), 4.4, 6.4, Z_(-0.7), Z_(-0.5))
    for ux in (6.0, bw - 6.0):
        K.tf_push(X_(ux), Z_(-14.0), 0, 0)
        K.cyl('metal', 0, 0, 0.0, 22.0, 0.22, 8, c=BC)
        K.rbox('red', 1.3, 0, 19.0, 2.6, 1.6, 0.1, 0.03, 1, c=BC)
        K.tf_pop()
    # small parking at the back, benches and trees in front
    for k in range(5):
        b('white', X_(8.0 + k * 10.0), X_(8.2 + k * 10.0), 0.0, 0.03, Z_(bd + 8.0), Z_(bd + 18.0))
    place(M.bench, X_(10.0), Z_(-14.0), 180)
    place(M.bench, X_(bw - 10.0), Z_(-14.0), 180)
    AVOID.append((bx - 2.0, bx + bw + 2.0, zf - bd - 2.0, zf + 14.0))
    tree_row(x0, 'B', 104.0, 100.0, 61)


# ------------------------------------------------------------------ supermarket (row B, x 0..104)
def supermarket(x0=0.0):
    lot_ground(x0, 'B', 104.0, 100.0, 62)
    sw_, sd_ = 84.0, 44.0
    sx = x0 + 10.0
    zf = ROW_B_Z1 - 54.0              # building front (faces +z); parking lot between it and the sidewalk
    X_ = lambda u: sx + u
    Z_ = lambda v: zf - v
    H = 17.0
    b('asphalt', x0 + 2.0, x0 + 102.0, 0.0, 0.1, zf + 1.0, ROW_B_Z1 - 2.0)
    # parking bays + arrows
    for k in range(18):
        b('white', x0 + 6.0 + k * 5.2, x0 + 6.2 + k * 5.2, 0.1, 0.14, zf + 8.0, zf + 22.0)
    for k in range(14):
        b('white', x0 + 12.0 + k * 5.2, x0 + 12.2 + k * 5.2, 0.1, 0.14, zf + 30.0, zf + 44.0) if zf + 44 < ROW_B_Z1 - 4 else None
    D.pavers(BC, X_(-2.0), X_(sw_ + 2.0), Z_(0.0), Z_(-7.0), 0.0, 0.3, 3.0, seed=9, solid=False)
    D.planter(BC, X_(6.0), Z_(-10.0), 0)
    D.planter(BC, X_(sw_ - 6.0), Z_(-10.0), 0)
    D.bike_rack(BC, X_(sw_ + 8.0), Z_(-4.0), 90)
    b('stucco', X_(0), X_(sw_), 0.3, 0.3 + H, Z_(0), Z_(sd_), solid=True)
    b('navy', X_(0), X_(sw_), 0.3 + H - 5.0, 0.3 + H, Z_(-0.4), Z_(0.0))
    b('roof', X_(-1.2), X_(sw_ + 1.2), 0.3 + H, 1.3 + H, Z_(-1.2), Z_(sd_ + 1.2))
    for (a, b_, c, d_) in ((-1.2, sw_ + 1.2, -1.2, -0.5), (-1.2, sw_ + 1.2, sd_ + 0.5, sd_ + 1.2), (-1.2, -0.5, -0.5, sd_ + 0.5), (sw_ + 0.5, sw_ + 1.2, -0.5, sd_ + 0.5)):
        b('parapet', X_(a), X_(b_), 1.3 + H, 2.5 + H, Z_(c), Z_(d_))
    # glass storefront with automatic doors
    b('glass', X_(6.0), X_(sw_ - 6.0), 1.0, 10.5, Z_(-0.1), Z_(0.0))
    for k in range(0, 15):
        ux = 6.0 + k * (sw_ - 12.0) / 14.0
        b('metal', X_(ux - 0.15), X_(ux + 0.15), 0.3, 10.8, Z_(-0.3), Z_(0.0))
    b('metal', X_(6.0), X_(sw_ - 6.0), 10.5, 11.0, Z_(-0.3), Z_(0.0))
    b('metal', X_(6.0), X_(sw_ - 6.0), 0.3, 1.0, Z_(-0.3), Z_(0.0))
    b('dark', X_(sw_ / 2 - 6.0), X_(sw_ / 2 + 6.0), 0.3, 9.6, Z_(-0.45), Z_(-0.1))
    b('glass', X_(sw_ / 2 - 5.6), X_(sw_ / 2 + 5.6), 0.5, 9.4, Z_(-0.5), Z_(-0.2))
    # canopy
    b('roof', X_(sw_ / 2 - 12.0), X_(sw_ / 2 + 12.0), 12.4, 13.2, Z_(-7.0), Z_(0.0))
    for ux in (sw_ / 2 - 11.0, sw_ / 2 + 11.0):
        b('metal', X_(ux - 0.4), X_(ux + 0.4), 0.3, 12.4, Z_(-6.4), Z_(-5.6), solid=True)
    # big sign
    b('red', X_(sw_ / 2 - 31.0), X_(sw_ / 2 + 31.0), 0.3 + H - 4.6, 0.3 + H - 0.4, Z_(-0.8), Z_(-0.4))
    sign_text('SUPERMARKET', X_(sw_ / 2), 0.3 + H - 4.2, Z_(-0.8), 0.46, 'white', 180, 0.3)
    # shopping carts + lamps + trees
    for k in range(6):
        K.tf_push(X_(sw_ / 2 + 16.0 + (k % 3) * 2.2), Z_(-3.0 - (k // 3) * 1.8), 0.3, 90)
        K.rbox('metal', 0, 0, 1.2, 2.8, 0.18, 1.6, 0.05, 1, c=BC)
        K.rbox('metal_dk', 0, 0, 1.4, 2.8, 1.4, 1.6, 0.1, 1, c=BC)
        for sx_ in (-1, 1):
            K.cyl('dark', sx_ * 0.9, -0.6, 0.0, 0.5, 0.18, 8, c=BC)
            K.cyl('dark', sx_ * 0.9, 0.6, 0.0, 0.5, 0.18, 8, c=BC)
        K.tf_pop()
    for k in range(4):
        place(M.lamp_post, x0 + 10.0 + k * 28.0, zf + 25.0, 0) if zf + 25.0 < ROW_B_Z1 else None
    # parked customer cars
    rnd = random.Random(33)
    for k in range(7):
        K.tf_push(x0 + 8.6 + k * 10.4, zf + 15.0, 0, 0)
        CAR.dad_car(ORG, rnd.choice(CARS), sc=CAR_SC, trim=False)
        K.tf_pop()
        K.COLL.append(('box', x0 + 8.6 + k * 10.4, zf + 15.0, 6.6 * CAR_SC, 15.4 * CAR_SC, 4.9 * CAR_SC))
    AVOID.append((x0, x0 + 104.0, zf - sd_ - 2.0, ROW_B_Z1))
    # delivery dock at the back
    b('concrete', X_(sw_ - 24.0), X_(sw_ - 6.0), 0.0, 3.0, Z_(sd_), Z_(sd_ + 8.0), solid=True)


# ------------------------------------------------------------------ whole biome
def biome():
    streets()
    _FACE[0] = -1
    # row A (our row): x -208..-104, -104..0 (us: 0..104 is OUR lot), 104..208, 208..312
    for k, x0 in enumerate((-208.0, -104.0, 104.0, 208.0)):
        lot_ground(x0, 'A', 104.0, 100.0, 10 + k)
        office_nb(x0, 'A', 100 + k)
        tree_row(x0, 'A', 104.0, 100.0, 10 + k)
    # row B (north of the street): office houses facing +z, bank, supermarket
    _FACE[0] = 1
    for k, x0 in enumerate((-208.0, 104.0, 208.0)):
        lot_ground(x0, 'B', 104.0, 100.0, 30 + k)
        office_nb(x0, 'B', 200 + k)
        tree_row(x0, 'B', 104.0, 100.0, 30 + k)
    bank(-104.0)
    supermarket(0.0)
    _FACE[0] = -1
