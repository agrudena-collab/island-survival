# Geometry library of the district generator: python-list meshes (fast), spatial chunking, vertex colours.
# Coordinates are STUDIO-LIKE: x east, y up, z south. They are converted to Blender (x, -z, y) only at write time.
import math
import random

KINDS = ('O', 'G', 'N')          # opaque, glass (Transparency in Studio), neon (Material Neon in Studio)
ITEMS = {k: [] for k in KINDS}   # each item: (cx, cz, verts[(x,y,z)], faces[[i..]], (r,g,b) linear-ish hex)
STATS = {'colliders': [], 'anchors': {}, 'lights': []}


def hexc(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(h, k):
    r, g, b = hexc(h) if isinstance(h, str) else h
    if k >= 0:
        r, g, b = (int(c + (255 - c) * k) for c in (r, g, b))
    else:
        r, g, b = (int(c * (1 + k)) for c in (r, g, b))
    return '#%02X%02X%02X' % (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


def _add(kind, verts, faces, col):
    xs = [v[0] for v in verts]
    zs = [v[2] for v in verts]
    ITEMS[kind].append(((min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2, verts, faces, col))


_BOXF = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3)]  # -y +y ... outward winding is fixed by Blender recalc


def box(x0, x1, y0, y1, z0, z1, col='#CCCCCC', kind='O'):
    if x1 - x0 <= 0 or y1 - y0 <= 0 or z1 - z0 <= 0:
        return
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1), (x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]
    _add(kind, v, _BOXF, col)


def cbox(cx, cy, cz, sx, sy, sz, col, kind='O', rot=0.0):
    """Box by centre and size, rotated about Y by rot degrees."""
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for dx in (-0.5, 0.5):
        for dz in (-0.5, 0.5):
            pass
    base = [(-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, -0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5)]
    v = []
    for (x, y, z) in base:
        x, y, z = x * sx, y * sy, z * sz
        v.append((cx + x * ca + z * sa, cy + y, cz - x * sa + z * ca))
    _add(kind, v, _BOXF, col)


def cyl(cx, cz, y0, y1, r, col, seg=16, kind='O', r2=None, caps=True):
    r2 = r if r2 is None else r2
    v, f = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        v.append((cx + r * math.cos(a), y0, cz + r * math.sin(a)))
    for i in range(seg):
        a = 2 * math.pi * i / seg
        v.append((cx + r2 * math.cos(a), y1, cz + r2 * math.sin(a)))
    for i in range(seg):
        j = (i + 1) % seg
        f.append((i, j, seg + j, seg + i))
    if caps:
        f.append(tuple(range(seg - 1, -1, -1)))
        f.append(tuple(seg + i for i in range(seg)))
    _add(kind, v, f, col)


def lathe(cx, cz, y0, prof, col, seg=20, kind='O'):
    """Surface of revolution: prof = [(radius, height), ...] bottom to top (height relative to y0)."""
    v, f = [], []
    n = len(prof)
    for (r, h) in prof:
        for i in range(seg):
            a = 2 * math.pi * i / seg
            v.append((cx + r * math.cos(a), y0 + h, cz + r * math.sin(a)))
    for k in range(n - 1):
        for i in range(seg):
            j = (i + 1) % seg
            f.append((k * seg + i, k * seg + j, (k + 1) * seg + j, (k + 1) * seg + i))
    if prof[0][0] > 0:
        f.append(tuple(range(seg - 1, -1, -1)))
    if prof[-1][0] > 0:
        f.append(tuple((n - 1) * seg + i for i in range(seg)))
    _add(kind, v, f, col)


def sphere(cx, cy, cz, rx, ry, rz, col, seg=12, rings=8, kind='O', jitter=0.0, seed=0):
    rnd = random.Random(seed)
    v, f = [], []
    for k in range(rings + 1):
        phi = math.pi * k / rings
        for i in range(seg):
            a = 2 * math.pi * i / seg
            j = 1 + rnd.uniform(-jitter, jitter) if 0 < k < rings else 1
            v.append((cx + rx * j * math.sin(phi) * math.cos(a), cy + ry * j * math.cos(phi), cz + rz * j * math.sin(phi) * math.sin(a)))
    for k in range(rings):
        for i in range(seg):
            j2 = (i + 1) % seg
            f.append((k * seg + i, (k + 1) * seg + i, (k + 1) * seg + j2, k * seg + j2))
    _add(kind, v, f, col)


def prism(poly, y0, y1, col, kind='O'):
    """Extruded convex/concave-free polygon given as [(x,z), ...] (counter-clockwise from above)."""
    n = len(poly)
    v = [(x, y0, z) for (x, z) in poly] + [(x, y1, z) for (x, z) in poly]
    f = [tuple(range(n - 1, -1, -1)), tuple(n + i for i in range(n))]
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, n + j, n + i))
    _add(kind, v, f, col)


def slope(x0, x1, y0, y1, z0, z1, col, axis='z', kind='O'):
    """Wedge: rises from y0 at the low side to y1 at the high side along the given axis; thickness is y0 -> everything below."""
    if axis == 'z':
        v = [(x0, 0, z0), (x1, 0, z0), (x1, 0, z1), (x0, 0, z1), (x0, y1, z0), (x1, y1, z0), (x1, y0, z1), (x0, y0, z1)]
    else:
        v = [(x0, 0, z0), (x1, 0, z0), (x1, 0, z1), (x0, 0, z1), (x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1)]
    _add(kind, v, _BOXF, col)


def counts():
    return tuple(len(ITEMS[k]) for k in KINDS)


STATS['marks'] = []     # item counts at every collider() call: items made since the previous call belong to that collider (audit ownership)


def collider(x0, x1, y0, y1, z0, z1, name='c'):
    STATS['marks'].append(counts())
    STATS['colliders'].append([round((x0 + x1) / 2, 3), round((y0 + y1) / 2, 3), round((z0 + z1) / 2, 3), round(x1 - x0, 3), round(y1 - y0, 3), round(z1 - z0, 3), name])


def anchor(name, x, y, z, fx=0.0, fz=1.0):
    STATS['anchors'][name] = [round(x, 3), round(y, 3), round(z, 3), fx, fz]


def tri_count():
    return {k: sum(sum(len(f) - 2 for f in it[3]) for it in ITEMS[k]) for k in KINDS}
