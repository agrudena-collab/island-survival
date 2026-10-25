"""Detail helpers shared by the lot and the biome: pavers, detailed trees, window / door / cornice dressing, street furniture.
Plot coordinates (x east, z toward the back yard); heights are y above the ground."""
import math
import random
import odh_core as K
from odh_core import B
import odh_models as M

ORG = 'BiomeOrg'        # smooth-shaded organic things (trees, bushes, flowers, cars)


def pavers(c, x0, x1, z0, z1, h0, h1, size=3.0, gap=0.05, tones=('walk', 'walk_b', 'walk_c'), grout='walk_dk', seed=0, solid=True):
    """slab in the grout colour with flush paving plates (3 tones, 0.05 joints)"""
    B(c, grout, x0, x1, h0, h1 - 0.03, z0, z1, solid=solid)
    rnd = random.Random(seed)
    nx = max(1, int(round((x1 - x0) / size)))
    nz = max(1, int(round((z1 - z0) / size)))
    sx, sz = (x1 - x0) / nx, (z1 - z0) / nz
    for i in range(nx):
        for j in range(nz):
            B(c, tones[rnd.randrange(len(tones))], x0 + i * sx + gap / 2, x0 + (i + 1) * sx - gap / 2, h1 - 0.03, h1,
              z0 + j * sz + gap / 2, z0 + (j + 1) * sz - gap / 2, solid=False)


def tree(c, s=1.0, seed=1, kind='oak'):
    """detailed tree: flared trunk, branches, three tiers of lumpy foliage (smooth shaded in the organic collection)"""
    rnd = random.Random(seed)
    K.COLL.append(('cyl',) + M._wpos() + (1.0 * s, 8.0 * s))
    tr = 'trunk' if kind != 'birch' else 'white'
    th = 7.5 * s
    M.lathe(c, tr, [(0.0, 0.0), (1.6 * s, 0.0), (1.2 * s, 0.5 * s), (0.9 * s, 1.5 * s), (0.7 * s, 4.0 * s), (0.6 * s, th)], 0, 0, 0, 18)
    for k in range(5):                                                           # root flare
        a = 2 * math.pi * k / 5 + 0.4
        M.tube(c, tr, [(math.cos(a) * 0.5 * s, 1.0 * s, math.sin(a) * 0.5 * s), (math.cos(a) * 1.9 * s, 0.05, math.sin(a) * 1.9 * s)], 0.3 * s, 7)
    if kind == 'birch':
        for k in range(7):
            M.rbox(c, 'dark', math.cos(k * 2.4) * 0.62 * s, math.sin(k * 2.4) * 0.62 * s, (1.0 + k * 0.9) * s, 0.5 * s, 0.22 * s, 0.1 * s, 0.03, 1)
    cols = {'oak': ('leaf', 'leaf2', 'leaf3'), 'maple': ('autumn', 'autumn2', 'orange'), 'cherry': ('cherry', 'cherry2', 'pink'), 'birch': ('leaf3', 'leaf', 'lawn')}.get(kind, ('leaf', 'leaf2', 'leaf3'))
    if kind == 'spruce':
        for k in range(6):
            r = (4.2 - k * 0.62) * s
            M.lathe(ORG, 'foliage' if k % 2 else 'foliage2', [(0.0, th * 0.35 + k * 2.2 * s), (r, th * 0.35 + k * 2.2 * s - 0.1 * s), (r * 0.55, th * 0.35 + k * 2.2 * s + 1.8 * s), (0.0, th * 0.35 + k * 2.2 * s + 3.0 * s)], 0, 0, 0, 20, caps=False)
        return
    cen = [(0, th + 2.7 * s, 0, 4.4 * s)]
    for k in range(7):                                                           # lower ring
        a = 2 * math.pi * k / 7 + rnd.uniform(-0.25, 0.25)
        cen.append((math.cos(a) * 3.9 * s, th + (0.9 + rnd.uniform(-0.2, 1.0)) * s, math.sin(a) * 3.9 * s, (2.8 + rnd.uniform(0, 1.0)) * s))
    for k in range(5):                                                           # upper ring
        a = 2 * math.pi * k / 5 + rnd.uniform(-0.3, 0.3)
        cen.append((math.cos(a) * 2.5 * s, th + (4.0 + rnd.uniform(0, 0.8)) * s, math.sin(a) * 2.5 * s, (2.4 + rnd.uniform(0, 0.7)) * s))
    cen.append((rnd.uniform(-0.6, 0.6) * s, th + 6.0 * s, rnd.uniform(-0.6, 0.6) * s, 2.3 * s))
    for k in range(6):                                                           # outer fillers
        a = 2 * math.pi * k / 6 + rnd.uniform(-0.3, 0.3)
        cen.append((math.cos(a) * 5.2 * s, th + (0.0 + rnd.uniform(0, 0.8)) * s, math.sin(a) * 5.2 * s, 1.8 * s))
    for (x, y, z, r) in cen[:9]:
        M.tube(c, tr, [(0, th * 0.78, 0), (x * 0.5, th * 0.9 + (y - th) * 0.4, z * 0.5), (x * 0.8, y - r * 0.4, z * 0.8)], 0.24 * s, 7)
    for k, (x, y, z, r) in enumerate(cen):
        M.blob(ORG, cols[k % 3], x, y, z, r, rnd, 14, 8, 0.12, 0.84)
    if kind == 'cherry':
        for k in range(18):
            x, y, z, r = cen[rnd.randrange(len(cen))]
            a, e = rnd.uniform(0, 6.28), rnd.uniform(-0.5, 0.6)
            M.sphere(ORG, 'white', x + math.cos(a) * r * 0.95, z + math.sin(a) * r * 0.95, y + e * r, 0.26 * s, 0.26 * s, 0.26 * s, 8, 5)


def tree_at(x, z, s, seed, kind='oak'):
    K.tf_push(x, z, 0, 0)
    tree(ORG, s, seed, kind)
    K.tf_pop()


def pl(c, fn, x, z, rot=0.0, *a, **k):
    K.tf_push(x, z, 0.0, rot)
    fn(c, *a, **k)
    K.tf_pop()


# ------------------------------------------------------------------ street furniture
def stop_sign(c, x, z, rot=0.0):
    K.tf_push(x, z, 0.0, rot)
    M.tube(c, 'metal_dk', [(0, 0, 0), (0, 8.0, 0)], 0.16, 8)
    M.cylinder(c, 'sign_red', 0, 0.2, 7.0, 0.12, 1.5, 8)
    M.cylinder(c, 'white', 0, 0.12, 7.08, 0.06, 1.25, 8)
    M.cylinder(c, 'sign_red', 0, 0.14, 7.14, 0.05, 1.12, 8)
    K.tf_pop()


def street_sign(c, x, z, rot=0.0):
    K.tf_push(x, z, 0.0, rot)
    M.tube(c, 'metal_dk', [(0, 0, 0), (0, 9.5, 0)], 0.15, 8)
    M.rbox(c, 'sign_green', 0, 0, 8.6, 5.0, 0.9, 0.18, 0.05, 1)
    M.rbox(c, 'white', 0, 0.11, 8.82, 4.2, 0.12, 0.05, 0.02, 1)
    M.rbox(c, 'sign_green', 0.0, 0, 7.5, 0.1, 1.1, 0.18, 0.02, 1)
    K.tf_pop()


def bus_shelter(c, x, z, rot=0.0):
    K.tf_push(x, z, 0.0, rot)
    for sx in (-1, 1):
        M.rbox(c, 'metal_dk', sx * 4.2, 0, 0.0, 0.35, 8.0, 0.35, 0.06, 1)
        M.rbox(c, 'glass', sx * 4.2, 0.0, 1.2, 0.15, 5.5, 2.4, 0.04, 1)
    M.rbox(c, 'glass', 0, -1.2, 1.2, 8.0, 5.5, 0.15, 0.04, 1)
    M.rbox(c, 'metal', 0, 0, 8.0, 9.4, 0.4, 3.8, 0.12, 2)
    M.rbox(c, 'sign_red', 0, 1.7, 7.2, 9.0, 0.7, 0.2, 0.05, 1)
    M.rbox(c, 'white', 3.2, -1.05, 2.2, 2.0, 3.4, 0.1, 0.04, 1)
    M.rbox(c, 'blue', 3.2, -1.0, 2.5, 1.6, 2.8, 0.06, 0.03, 1)
    M.rbox(c, 'wood2', -0.6, -0.4, 1.7, 5.2, 0.28, 1.2, 0.08, 1)
    M.rbox(c, 'metal_dk', -0.6, -0.9, 1.7, 5.2, 1.2, 0.18, 0.05, 1)
    K.tf_pop()


def planter(c, x, z, rot=0.0, w=4.0, d=2.4):
    K.tf_push(x, z, 0.0, rot)
    M.rbox(c, 'stone', 0, 0, 0.0, w, 1.6, d, 0.2, 2)
    M.rbox(c, 'soil', 0, 0, 1.55, w - 0.5, 0.2, d - 0.5, 0.05, 1)
    rnd = random.Random(int(x * 7 + z))
    for k in range(9):
        fx, fz = rnd.uniform(-w / 2 + 0.5, w / 2 - 0.5), rnd.uniform(-d / 2 + 0.5, d / 2 - 0.5)
        col = ('flower_r', 'flower_y', 'pink', 'flower_p', 'white')[k % 5]
        M.sphere(ORG, 'leaf2', fx, fz, 1.95, 0.5, 0.35, 0.5, 8, 5)
        M.sphere(ORG, col, fx, fz, 2.35, 0.27, 0.27, 0.27, 8, 5)
    K.tf_pop()


def bike_rack(c, x, z, rot=0.0, n=5):
    K.tf_push(x, z, 0.0, rot)
    for k in range(n):
        px = (k - (n - 1) / 2) * 1.5
        M.torus(c, 'metal', px, 0, 1.4, 1.1, 0.1, 'yz' if False else 'xy', 16, 5)
    K.tf_pop()


def bollard(c, x, z):
    K.tf_push(x, z, 0.0, 0)
    M.lathe(c, 'metal_dk', [(0.0, 0.0), (0.45, 0.0), (0.4, 0.2), (0.35, 2.6), (0.45, 2.7), (0.0, 2.9)], 0, 0, 0, 12)
    M.rbox(c, 'yellow', 0, 0, 2.0, 0.8, 0.25, 0.8, 0.1, 1)
    K.tf_pop()


def tactile(c, x0, x1, z0, z1, h):
    """yellow tactile paving with a dot grid (blind-person crossing mark)"""
    B(c, 'tactile', x0, x1, h, h + 0.04, z0, z1, solid=False)
    nx, nz = int((x1 - x0) / 0.8), int((z1 - z0) / 0.8)
    for i in range(nx):
        for j in range(nz):
            B(c, 'tactile', x0 + 0.3 + i * 0.8, x0 + 0.5 + i * 0.8, h + 0.04, h + 0.1, z0 + 0.3 + j * 0.8, z0 + 0.5 + j * 0.8, solid=False)


# ------------------------------------------------------------------ house dressing (neighbour houses, bank)
def window_det(c, xc, y0, w, h, zf, s, shutters=None, box=False, curtain=0, seed=0):
    """facade window at z = zf on a wall that faces s (-1: -z, +1: +z): frame, 2x2 panes, sill, lintel, curtains, optional shutters and flower box"""
    def zz(a, b_):
        return (min(zf + s * a, zf + s * b_), max(zf + s * a, zf + s * b_))
    za, zb = zz(0.0, 0.55)
    B(c, 'trim', xc - w / 2 - 0.45, xc + w / 2 + 0.45, y0 - 0.45, y0 + h + 0.45, *zz(0.0, 0.3))                      # frame
    B(c, 'glass', xc - w / 2, xc + w / 2, y0, y0 + h, *zz(0.06, 0.2), solid=False)
    cur = ('curtain_a', 'curtain_b', 'curtain_c')[curtain % 3]
    B(c, cur, xc - w / 2 + 0.1, xc - w / 2 + w * 0.34, y0 + 0.1, y0 + h - 0.1, *zz(0.02, 0.06), solid=False)
    B(c, cur, xc + w / 2 - w * 0.34, xc + w / 2 - 0.1, y0 + 0.1, y0 + h - 0.1, *zz(0.02, 0.06), solid=False)
    B(c, 'trim', xc - 0.12, xc + 0.12, y0, y0 + h, *zz(0.2, 0.32), solid=False)                                       # mullions
    B(c, 'trim', xc - w / 2, xc + w / 2, y0 + h * 0.5 - 0.12, y0 + h * 0.5 + 0.12, *zz(0.2, 0.32), solid=False)
    B(c, 'stone', xc - w / 2 - 0.9, xc + w / 2 + 0.9, y0 + h + 0.45, y0 + h + 1.05, *zz(0.0, 0.5), solid=False)       # lintel
    B(c, 'stone', xc - w / 2 - 0.7, xc + w / 2 + 0.7, y0 - 0.95, y0 - 0.45, *zz(0.0, 0.9), solid=False)               # sill
    if shutters:
        for sx in (-1, 1):
            xs = xc + sx * (w / 2 + 0.45 + 0.9)
            B(c, shutters, xs - 0.85, xs + 0.85, y0 - 0.45, y0 + h + 0.45, *zz(0.0, 0.35), solid=False)
            for k in range(5):
                B(c, 'trim', xs - 0.7, xs + 0.7, y0 + 0.2 + k * (h / 5.0), y0 + 0.28 + k * (h / 5.0), *zz(0.35, 0.42), solid=False)
    if box:
        B(c, 'wood2', xc - w / 2 - 0.2, xc + w / 2 + 0.2, y0 - 1.9, y0 - 0.95, *zz(0.0, 1.3), solid=False)
        rnd = random.Random(seed)
        for k in range(7):
            col = ('flower_r', 'flower_y', 'pink', 'flower_p', 'white')[rnd.randrange(5)]
            fx = xc - w / 2 + 0.4 + k * (w - 0.8) / 6.0
            M.sphere(ORG, 'leaf2', fx, zf + s * 0.7, y0 - 0.9, 0.45, 0.32, 0.45, 8, 5)
            M.sphere(ORG, col, fx, zf + s * 0.7, y0 - 0.5, 0.26, 0.26, 0.26, 8, 5)


def cornice(c, x0, x1, y, zf, s, depth_z, z_far, dent=True):
    """cornice band with dentils along the front (and along a side if needed by the caller)"""
    za, zb = min(zf, zf + s * 0.9), max(zf, zf + s * 0.9)
    B(c, 'trim', x0 - 0.5, x1 + 0.5, y, y + 1.0, za, zb, solid=False)
    B(c, 'stone', x0 - 0.9, x1 + 0.9, y + 1.0, y + 1.6, min(zf, zf + s * 1.3), max(zf, zf + s * 1.3), solid=False)
    if dent:
        n = int((x1 - x0) / 1.6)
        for k in range(n):
            xx = x0 + 0.3 + k * 1.6
            B(c, 'trim', xx, xx + 0.7, y - 0.55, y, min(zf, zf + s * 0.7), max(zf, zf + s * 0.7), solid=False)


def quoins(c, x, zf, s, y0, y1, side=1):
    """alternating corner blocks on a facade corner at x"""
    k = 0
    y = y0
    while y < y1 - 0.5:
        w = 1.8 if k % 2 else 1.1
        xa, xb = (x, x + side * w) if side > 0 else (x - w, x)
        B(c, 'stone', xa, xb, y, y + 1.2, min(zf, zf + s * 0.25), max(zf, zf + s * 0.25), solid=False)
        y += 1.3
        k += 1


def front_door(c, xc, zf, s, y0=1.0, color='door', lamp=True, num='12'):
    """panelled door with transom, frame, knob, lamp, doormat and 3 steps"""
    def zz(a, b_):
        return (min(zf + s * a, zf + s * b_), max(zf + s * a, zf + s * b_))
    B(c, 'trim', xc - 3.6, xc + 3.6, y0, y0 + 10.8, *zz(0.0, 0.4), solid=False)
    B(c, color, xc - 3.0, xc + 3.0, y0, y0 + 9.4, *zz(0.35, 0.65), solid=False)
    for (dx, dy) in ((-1.5, 0.6), (1.5, 0.6), (-1.5, 4.8), (1.5, 4.8)):
        B(c, 'door2', xc + dx - 1.1, xc + dx + 1.1, y0 + dy + 0.4, y0 + dy + (3.6 if dy < 2 else 3.6), *zz(0.65, 0.78), solid=False)
    B(c, 'glass', xc - 2.8, xc + 2.8, y0 + 9.4, y0 + 10.5, *zz(0.1, 0.3), solid=False)
    B(c, 'trim', xc - 0.12, xc + 0.12, y0 + 9.4, y0 + 10.5, *zz(0.3, 0.4), solid=False)
    B(c, 'brass', xc + 2.0, xc + 2.5, y0 + 4.6, y0 + 5.1, *zz(0.78, 1.0), solid=False)
    B(c, 'burg', xc - 2.6, xc + 2.6, y0, y0 + 0.08, *zz(1.0, 3.2), solid=False)
    for k in range(3):
        B(c, 'stone', xc - 4.4 - 0.4 * k, xc + 4.4 + 0.4 * k, 0.0, y0 - 0.33 * k, *zz(1.5 + k * 1.2, 2.7 + k * 1.2), solid=False) if False else None
    if lamp:
        for sx in (-1, 1):
            xl = xc + sx * 4.8
            B(c, 'metal_dk', xl - 0.25, xl + 0.25, y0 + 8.0, y0 + 9.2, *zz(0.0, 0.6), solid=False)
            B(c, 'lamp', xl - 0.35, xl + 0.35, y0 + 8.2, y0 + 9.0, *zz(0.4, 1.0), solid=False)


def roof_detail(c, x0, x1, z0, z1, ytop, rnd, n=2):
    """parapet cap, AC units with fans, vent pipes"""
    B(c, 'trim', x0 - 1.0, x1 + 1.0, ytop, ytop + 0.35, z0 - 1.0, z1 + 1.0, solid=False) if False else None
    for k in range(n):
        ux, uz = rnd.uniform(x0 + 6.0, x1 - 9.0), rnd.uniform(z0 + 6.0, z1 - 8.0)
        B(c, 'metal', ux, ux + 5.0, ytop, ytop + 3.0, uz, uz + 4.0)
        B(c, 'metal_dk', ux + 0.3, ux + 4.7, ytop + 3.0, ytop + 3.25, uz + 0.3, uz + 3.7, solid=False)
        M.cylinder('Biome', 'dark', ux + 2.5, uz + 2.0, ytop + 3.25, 0.1, 1.5, 14) if False else None
        for g in range(6):
            B(c, 'metal_dk', ux + 0.4 + g * 0.75, ux + 0.6 + g * 0.75, ytop + 0.4, ytop + 2.6, uz - 0.1, uz, solid=False)
    px, pz = rnd.uniform(x0 + 4.0, x1 - 4.0), rnd.uniform(z0 + 4.0, z1 - 4.0)
    K.tf_push(px, pz, ytop, 0)
    M.tube(c, 'metal_dk', [(0, 0, 0), (0, 2.6, 0)], 0.3, 8)
    M.cylinder(c, 'metal', 0, 0, 2.6, 0.3, 0.55, 10)
    K.tf_pop()


def downspout(c, x, z, h):
    B(c, 'metal', x - 0.25, x + 0.25, 0.0, h, z - 0.25, z + 0.25, solid=False)
