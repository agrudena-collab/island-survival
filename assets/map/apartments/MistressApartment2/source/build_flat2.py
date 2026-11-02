# Mistress apartment 2 (Office Dad's mistress): a detailed procedural flat in the style of the Office Dad biome (blue-grey stucco, white trim, navy, red accent,
# mustard and teal) — an open studio with a panoramic window, an executive desk, a kitchen bar, a lounge, a bedroom and a bathroom.
# Run: blender -b --factory-startup --python build_flat2.py -- <outdir> [--norender] [--only=<shot>]
# Coordinates are Studio-like (x east, y up, z south) relative to the flat origin; floor top FY = 1.  Contract with ApartmentService / DialogueService (same as flat 1):
#   Arrival, ExitDoor (tag ApartmentExit), MistressDesk (attribute DadId = OfficeDad), MistressSeat, GuestSeat.
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
T0 = time.time()
random.seed(21)

# every lathe / cylinder / sphere gets ~1.8x the segments: curved parts are not low poly
_lathe, _cyl, _sphere = D.lathe, D.cyl, D.sphere
SM = 1.8


def lathe(cx, cz, y0, prof, col, seg=20, kind='O'):
    _lathe(cx, cz, y0, prof, col, min(64, int(seg * SM)), kind)


def cyl(cx, cz, y0, y1, r, col, seg=16, kind='O', r2=None, caps=True):
    _cyl(cx, cz, y0, y1, r, col, min(64, int(seg * SM)), kind, r2, caps)


def sphere(cx, cy, cz, rx, ry, rz, col, seg=12, rings=8, kind='O', jitter=0.0, seed=0):
    _sphere(cx, cy, cz, rx, ry, rz, col, min(40, int(seg * SM)), min(24, int(rings * 1.5)), kind, jitter, seed)


D.lathe, D.cyl, D.sphere = lathe, cyl, sphere

FY = 1.0            # floor top
H = 11.0            # clear height
CY = FY + H         # ceiling underside
SIGNS = []
LIGHTS = []         # (x, y, z, range, brightness)
CYLC = []           # round colliders (cx, cy, cz, diameter, height, name)

# Office Dad interior palette (vivid): blue-grey stucco, white trim, navy, red, mustard, teal, warm wood
P = dict(wall='#BCD3EA', wall2='#F2EEE4', wall3='#9CB8EC', navy='#2C4C94', navy2='#21397A', white='#FFFFFF', cream='#F6F4EC', ceil='#FBFAF4',
         red='#D8402F', red2='#B5301F', coral='#F4705C', mustard='#F4BA3A', teal='#12AC9C', teal2='#0E8A7D', blue='#3A88E4', sky='#BFE4F4',
         wood='#C98534', wood2='#E0A24E', wood3='#B97626', walnut='#6B4524', walnut2='#8A5A33', oak='#D9A566', black='#25262B', charcoal='#3A3D46',
         metal='#BFC5CA', metal2='#7E868C', brass='#E0B040', glass='#BFE4F4', tileA='#F2EBD6', tileB='#8FB4C0', tileC='#E6D6A6', tileW='#F4F6F8', tileG='#A8C8D4',
         green='#3CB44E', green2='#5AC65A', leaf='#2FA84A', pot='#F4705C', pot2='#12AC9C', pink='#F48CB2', plum='#8C60D4', brick='#C4633F', concrete='#B9BAB6',
         marble='#EDEBE6', marble2='#D5D3CE', joint='#9C6A2E', skin='#E8B58C', paper='#F4F1E8', screen='#1B1F27', screen2='#3A88E4', roof='#2D58B0')


# ---------------------------------------------------------------------------------------------------------------------------------------
# local frame: an object stands at (ox, oz) and faces FACE ('N' = -z, 'S' = +z, 'E' = +x, 'W' = -x).  u = to its right, w = forward, y = up.
# ---------------------------------------------------------------------------------------------------------------------------------------
FW = {'N': (0, -1), 'S': (0, 1), 'E': (1, 0), 'W': (-1, 0)}


def to_world(face, ox, oz, u, w):
    fx, fz = FW[face]
    rx, rz = -fz, fx
    return ox + u * rx + w * fx, oz + u * rz + w * fz


class F:
    """frame of an object: f.b(u0, u1, y0, y1, w0, w1, col) places an axis-aligned box in local coordinates"""

    def __init__(self, face, ox, oz):
        self.face, self.ox, self.oz = face, ox, oz

    def p(self, u, w):
        return to_world(self.face, self.ox, self.oz, u, w)

    def b(self, u0, u1, y0, y1, w0, w1, col, kind='O'):
        xa, za = self.p(u0, w0)
        xb, zb = self.p(u1, w1)
        box(min(xa, xb), max(xa, xb), y0, y1, min(za, zb), max(za, zb), col, kind)

    def cyl(self, u, w, y0, y1, r, col, seg=16, r2=None, kind='O', caps=True):
        x, z = self.p(u, w)
        cyl(x, z, y0, y1, r, col, seg=seg, r2=r2, kind=kind, caps=caps)

    def lathe(self, u, w, y0, prof, col, seg=20, kind='O'):
        x, z = self.p(u, w)
        lathe(x, z, y0, prof, col, seg=seg, kind=kind)

    def sphere(self, u, y, w, rx, ry, rz, col, seg=12, rings=8, kind='O', jitter=0.0, seed=0):
        x, z = self.p(u, w)
        if self.face in 'EW':
            rx, rz = rz, rx
        sphere(x, y, z, rx, ry, rz, col, seg=seg, rings=rings, kind=kind, jitter=jitter, seed=seed)

    def col(self, name, u0, u1, y0, y1, w0, w1):
        xa, za = self.p(u0, w0)
        xb, zb = self.p(u1, w1)
        collider(min(xa, xb), max(xa, xb), y0, y1, min(za, zb), max(za, zb), name)

    def xyz(self, u, w):
        return self.p(u, w)


def rnd_of(seed):
    return random.Random(seed)


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


def soft(x0, x1, y0, y1, z0, z1, col, b=0.14, kind='O'):
    """cushion: a box with a stepped chamfer on the top edges"""
    b = min(b, (x1 - x0) / 3, (z1 - z0) / 3, (y1 - y0) / 2)
    box(x0, x1, y0, y1 - b, z0, z1, col, kind)
    box(x0 + b, x1 - b, y1 - b, y1, z0 + b, z1 - b, col, kind)


def split_range(a, b, cuts):
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


def spot(x, y, z, rng=18, br=0.9):
    LIGHTS.append((x, y, z, rng, br))


exec(compile(open(os.path.join(HERE, 'furn2.py'), encoding='utf-8').read(), 'furn2.py', 'exec'))
exec(compile(open(os.path.join(HERE, 'rooms2.py'), encoding='utf-8').read(), 'rooms2.py', 'exec'))
exec(compile(open(os.path.join(HERE, 'audit_flat2.py'), encoding='utf-8').read(), 'audit_flat2.py', 'exec'))
exec(compile(open(os.path.join(HERE, 'export_flat2.py'), encoding='utf-8').read(), 'export_flat2.py', 'exec'))
