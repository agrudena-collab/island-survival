# Mistress apartment (Regular Dad's mistress): a detailed procedural flat, modelled (not boxes). Blender -> FBX, vertex colours, chunks <= 9000 tris.
# Run: blender -b --factory-startup --python build_flat.py -- <outdir> [--norender]
# Coordinates are Studio-like (x east, y up, z south) relative to the flat origin (ix, iz); floor top y = FY. Same contract as the old flat:
#   Arrival (-14, 12) facing north, exit door in the south wall at x=-14, round table at (2, -5) (MistressDesk), she sits at (2, -10.6).
import bpy, bmesh, math, os, sys, json, random, time
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'district', 'RegularDadDistrict', 'source'))
import dlib as D
from dlib import box, cbox, cyl, lathe, sphere, prism, slope, collider, anchor, shade

args = sys.argv[sys.argv.index('--') + 1:]
OUT = os.path.abspath(args[0])
NORENDER = '--norender' in args
os.makedirs(OUT, exist_ok=True)
T0 = time.time()
random.seed(11)

# smoother curved parts than the district: every lathe / cylinder / sphere gets ~1.8x the segments (not low poly)
_lathe, _cyl, _sphere = D.lathe, D.cyl, D.sphere
ROUND = False        # rounded furniture / smooth shading / arches were NOT requested: off (set True to get the soft variant)
SM = 2.4 if ROUND else 1.8


def lathe(cx, cz, y0, prof, col, seg=20, kind='O'):
    _lathe(cx, cz, y0, prof, col, min(64, int(seg * SM)), kind)


def cyl(cx, cz, y0, y1, r, col, seg=16, kind='O', r2=None, caps=True):
    _cyl(cx, cz, y0, y1, r, col, min(64, int(seg * SM)), kind, r2, caps)


def sphere(cx, cy, cz, rx, ry, rz, col, seg=12, rings=8, kind='O', jitter=0.0, seed=0):
    _sphere(cx, cy, cz, rx, ry, rz, col, min(40, int(seg * SM)), min(24, int(rings * 1.5)), kind, jitter, seed)


D.lathe, D.cyl, D.sphere = lathe, cyl, sphere

FY = 1.0            # floor top
H = 11.0            # ceiling height above the floor
CY = FY + H         # ceiling underside
SIGNS = []
LIGHTS = []         # (x, y, z, range, brightness)
CYLC = []           # round colliders (cx, cy, cz, diameter, height, name)

P = dict(wall='#D4BC9C', blush='#EBCFC6', rose='#D98A94', rose2='#B8566B', teal='#2E6B6F', teal2='#3FA79B', gold='#D4A94A', walnut='#6B4430', oak='#B98A5A',
         oak2='#A67847', oak3='#C9A06E', cream='#EFE2CB', white='#FAFAF5', black='#23242B', charcoal='#3A3D46', navy='#2B3A67', sage='#8DAA8B', glass='#BFE3F2',
         metal='#A8AEB5', brass='#C9A24E', marble='#EDEBE6', marble2='#D5D3CE', tileW='#F2F4F5', tileG='#B7C9CF', red='#C94A44', plum='#7A4B7D', green='#3E8E55',
         green2='#5FAE5A', pot='#C46A4A', sky='#A9D8F5', concrete='#B8B6B0', denim='#4C6D9A', mustard='#E0B04A', terracotta='#D9825E', lilac='#B9A4D6', skin='#E7B997')


# ---------------------------------------------------------------------------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------------------------------------------------------------------------
def rbox(x0, x1, y0, y1, z0, z1, col, r=None, rt=None, kind='O', m=3, n=3):
    """Real rounded box: rounded vertical corners (radius r) and rounded top edges (radius rt), flat bottom. Smooth-shaded at export."""
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    if dx <= 0 or dy <= 0 or dz <= 0:
        return
    r = min(0.2 if r is None else r, dx / 2.2, dz / 2.2)
    rt = min(0.2 if rt is None else rt, dy / 2.2, dx / 2.2, dz / 2.2)
    cx, cz, hx, hz = (x0 + x1) / 2, (z0 + z1) / 2, dx / 2, dz / 2
    layers = [(y0, 0.0)]
    if y1 - rt > y0 + 1e-6:
        layers.append((y1 - rt, 0.0))
    for k in range(1, n + 1):
        th = k * math.pi / 2 / n
        layers.append((y1 - rt + rt * math.sin(th), rt * (1 - math.cos(th))))
    v, f = [], []
    for (y, ins) in layers:
        rc = max(r - ins, 0.002)
        ax, az = hx - ins - rc, hz - ins - rc
        for (sx, sz, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
            for i in range(m + 1):
                a = math.radians(a0 + 90.0 * i / m)
                v.append((cx + sx * ax + rc * math.cos(a), y, cz + sz * az + rc * math.sin(a)))
    P = 4 * (m + 1)
    for l in range(len(layers) - 1):
        for i in range(P):
            j = (i + 1) % P
            f.append((l * P + i, l * P + j, (l + 1) * P + j, (l + 1) * P + i))
    f.append(tuple(range(P - 1, -1, -1)))
    f.append(tuple((len(layers) - 1) * P + i for i in range(P)))
    D._add(kind, v, f, col)


def soft(x0, x1, y0, y1, z0, z1, col, b=0.14, kind='O'):
    """Cushions / mattresses: a box with a stepped chamfer on the top edges (or a pillowy rounded box when ROUND)."""
    if ROUND:
        rbox(x0, x1, y0, y1, z0, z1, col, r=max(b * 2.6, 0.12), rt=max(b * 2.2, 0.1), kind=kind)
        return
    b = min(b, (x1 - x0) / 3, (z1 - z0) / 3, (y1 - y0) / 2)
    box(x0, x1, y0, y1 - b, z0, z1, col, kind)
    box(x0 + b, x1 - b, y1 - b, y1, z0 + b, z1 - b, col, kind)


def extrude(poly, plane, n0, n1, col, kind='O'):
    """Extrude a polygon given in (u, y) along the wall normal: plane 'xy' -> along z in [n0, n1]; 'zy' -> along x."""
    Pn = len(poly)
    v = []
    for nn in (n0, n1):
        for (u, w) in poly:
            v.append((u, w, nn) if plane == 'xy' else (nn, w, u))
    f = [tuple(range(Pn - 1, -1, -1)), tuple(Pn + i for i in range(Pn))]
    for i in range(Pn):
        j = (i + 1) % Pn
        f.append((i, j, Pn + j, Pn + i))
    D._add(kind, v, f, col)


def arc_pts(cu, cy, r, a0, a1, n=10):
    return [(cu + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def arch_opening(plane, u0, u1, y_top, n0, n1, col):
    """Fill the top corners of a rectangular wall opening so it becomes a round arch."""
    r = (u1 - u0) / 2
    cy = y_top - r
    left = [(u0, y_top)] + arc_pts(u0 + r, cy, r, 180, 90)
    right = [(u1, y_top)] + arc_pts(u0 + r, cy, r, 0, 90)[::-1][::-1]
    extrude(left, plane, n0, n1, col)
    extrude([(u1, y_top)] + arc_pts(u0 + r, cy, r, 90, 0), plane, n0, n1, col)


def arch_casing(plane, u0, u1, y_top, n0, n1, col, w=0.45):
    r = (u1 - u0) / 2
    cu = (u0 + u1) / 2
    ys = y_top - r
    outer = arc_pts(cu, ys, r + w, 180, 0, 14)
    inner = arc_pts(cu, ys, r, 0, 180, 14)
    poly = [(u0 - w, FY), (u0 - w, ys)] + outer[1:-1] + [(u1 + w, ys), (u1 + w, FY), (u1, FY), (u1, ys)] + inner[1:-1] + [(u0, ys), (u0, FY)]
    extrude(poly, plane, n0, n1, col)


def hcyl(x, y, z, axis, length, r, col, seg=10, kind='O', r2=None):
    r2 = r if r2 is None else r2
    v, f = [], []
    for end, rr in ((0, r), (1, r2)):
        for i in range(seg):
            a = 2 * math.pi * i / seg
            c, s = math.cos(a) * rr, math.sin(a) * rr
            o = length * end - length / 2
            v.append((x + o, y + c, z + s) if axis == 'x' else (x + c, y + s, z + o))
    for i in range(seg):
        j = (i + 1) % seg
        f.append((i, j, seg + j, seg + i))
    f.append(tuple(range(seg - 1, -1, -1)))
    f.append(tuple(seg + i for i in range(seg)))
    D._add(kind, v, f, col)


def ring(cx, cy, cz, R, r, plane, col, seg=18, tseg=6, kind='O'):
    v, f = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        for j in range(tseg):
            b = 2 * math.pi * j / tseg
            rr = R + r * math.cos(b)
            u, w, h = rr * math.cos(a), rr * math.sin(a), r * math.sin(b)
            if plane == 'xz':
                v.append((cx + u, cy + h, cz + w))
            elif plane == 'xy':
                v.append((cx + u, cy + w, cz + h))
            else:
                v.append((cx + h, cy + u, cz + w))
    for i in range(seg):
        for j in range(tseg):
            i2, j2 = (i + 1) % seg, (j + 1) % tseg
            f.append((i * tseg + j, i * tseg + j2, i2 * tseg + j2, i2 * tseg + j))
    D._add(kind, v, f, col)


def frustum(cx, cz, w, d, y0, h, ins, col, kind='O'):
    x0, x1, z0, z1 = cx - w / 2, cx + w / 2, cz - d / 2, cz + d / 2
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1), (x0 + ins, y0 + h, z0 + ins), (x1 - ins, y0 + h, z0 + ins), (x1 - ins, y0 + h, z1 - ins), (x0 + ins, y0 + h, z1 - ins)]
    D._add(kind, v, D._BOXF, col)


def wb(n, px, y0, pz, w, h, d, col, off=0.0, kind='O'):
    """Box on a wall. n = direction the wall surface faces (into the room); (px, pz) = point on the wall plane; w along the wall, d out of it."""
    if n == 'S':
        box(px - w / 2, px + w / 2, y0, y0 + h, pz + off, pz + off + d, col, kind)
    elif n == 'N':
        box(px - w / 2, px + w / 2, y0, y0 + h, pz - off - d, pz - off, col, kind)
    elif n == 'E':
        box(px + off, px + off + d, y0, y0 + h, pz - w / 2, pz + w / 2, col, kind)
    else:
        box(px - off - d, px - off, y0, y0 + h, pz - w / 2, pz + w / 2, col, kind)


def split_range(a, b, cuts):
    """[a,b] minus the ranges in cuts."""
    out, cur = [], a
    for (c0, c1) in sorted(cuts):
        if c1 <= cur or c0 >= b:
            continue
        if c0 > cur:
            out.append((cur, c0))
        cur = max(cur, c1)
    if cur < b:
        out.append((cur, b))
    return out


def wall_x(z, x0, x1, ops, col, th=1.0, name='wall'):
    """Wall along x with centre line z; ops = [(xa, xb, ya, yb)] openings (absolute y)."""
    xs = sorted(set([x0, x1] + [o[0] for o in ops] + [o[1] for o in ops]))
    y0, y1 = FY, CY
    for a, b in zip(xs[:-1], xs[1:]):
        mid = (a + b) / 2
        cov = [o for o in ops if o[0] <= mid <= o[1]]
        if not cov:
            box(a, b, y0 - 1, y1 + 1, z - th / 2, z + th / 2, col)
            collider(a, b, y0, y1, z - th / 2, z + th / 2, name)
        else:
            o = cov[0]
            if o[2] > y0:
                box(a, b, y0 - 1, o[2], z - th / 2, z + th / 2, col)
                collider(a, b, y0, o[2], z - th / 2, z + th / 2, name)
            if o[3] < y1:
                box(a, b, o[3], y1 + 1, z - th / 2, z + th / 2, col)
                collider(a, b, o[3], y1, z - th / 2, z + th / 2, name)


def wall_z(x, z0, z1, ops, col, th=1.0, name='wall'):
    zs = sorted(set([z0, z1] + [o[0] for o in ops] + [o[1] for o in ops]))
    y0, y1 = FY, CY
    for a, b in zip(zs[:-1], zs[1:]):
        mid = (a + b) / 2
        cov = [o for o in ops if o[0] <= mid <= o[1]]
        if not cov:
            box(x - th / 2, x + th / 2, y0 - 1, y1 + 1, a, b, col)
            collider(x - th / 2, x + th / 2, y0, y1, a, b, name)
        else:
            o = cov[0]
            if o[2] > y0:
                box(x - th / 2, x + th / 2, y0 - 1, o[2], a, b, col)
                collider(x - th / 2, x + th / 2, y0, o[2], a, b, name)
            if o[3] < y1:
                box(x - th / 2, x + th / 2, o[3], y1 + 1, a, b, col)
                collider(x - th / 2, x + th / 2, o[3], y1, a, b, name)


def spot(x, y, z, rng=18, br=0.9):
    LIGHTS.append((x, y, z, rng, br))


exec(compile(open(os.path.join(HERE, 'furn.py'), encoding='utf-8').read(), 'furn.py', 'exec'))
exec(compile(open(os.path.join(HERE, 'rooms.py'), encoding='utf-8').read(), 'rooms.py', 'exec'))
exec(compile(open(os.path.join(HERE, 'audit_flat.py'), encoding='utf-8').read(), 'audit_flat.py', 'exec'))
exec(compile(open(os.path.join(HERE, 'export_flat.py'), encoding='utf-8').read(), 'export_flat.py', 'exec'))
