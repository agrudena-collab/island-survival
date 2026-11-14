"""Building kit for the Grill Dad District: block font, pixel art, walls with openings, roofs, stairs and props.
Pure python (no bpy). All geometry is boxes/prisms/lofts in plan coords: x east, y north, z up, 1 unit = 1 stud."""
import math, random

sc = None


def init(scene):
    global sc
    sc = scene


# viewer standing on that side sees: right vector, outward normal
FACE = {"S": ((1, 0), (0, -1)), "N": ((-1, 0), (0, 1)), "E": ((0, 1), (1, 0)), "W": ((0, -1), (-1, 0))}
OPP = {"S": "N", "N": "S", "E": "W", "W": "E"}


def B(x0, y0, z0, x1, y1, z1, mat, group="Props", col=False, tag=None):
    sc.box(x0, y0, z0, x1, y1, z1, mat, group, col, tag)


def C(x, y, z0, z1, r, mat, group="Props", seg=8, col=False, tag=None):
    sc.cyl(x, y, z0, z1, r, mat, group, seg, col, tag)


def COL(x0, y0, z0, x1, y1, z1, tag, group="Col"):
    sc.col(x0, y0, z0, x1, y1, z1, tag, group)


def FB(face, ox, oy, a0, d0, z0, a1, d1, z1, mat, group="Props", col=False, tag=None):
    """Box in a face frame: a along the viewer's right, d along the outward normal, from origin (ox, oy)."""
    (rx, ry), (nx, ny) = FACE[face]
    B(ox + rx * a0 + nx * d0, oy + ry * a0 + ny * d0, z0, ox + rx * a1 + nx * d1, oy + ry * a1 + ny * d1, z1, mat, group, col, tag)


def FP(face, ox, oy, a, d):
    (rx, ry), (nx, ny) = FACE[face]
    return (ox + rx * a + nx * d, oy + ry * a + ny * d)


# ------------------------------------------------------------------ font + pixel art
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    " ": ["00000"] * 7,
}

GRILL_ICON = ["...1.1.1...", "..1.1.1....", "...1.1.1...", "...........", ".111111111.", "11111111111",
              "...........", "11111111111", ".111111111.", "..1111111..", "..1.....1..", ".1.......1."]
FLAME_ICON = ["...o...", "..oo...", "..ooo..", ".ooyo..", ".oyyoo.", "ooyyyoo", "oyyyyyo", "oyywyyo", ".oyyyo."]
DAD_FACE = ["..hhhhhhhh..", ".hhhhhhhhhh.", ".hyyyyyyyyh.", ".yyyyyyyyyy.", ".bbbbbbbbbb.", ".ybbbyybbby.",
            ".yyyyyyyyyy.", ".yyyyyyyyyy.", ".yybyyyybyy.", ".yyybbbbyyy.", ".yyyyyyyyyy.", "..yyyyyyyy.."]


def spatulas_icon():
    g = [["."] * 15 for _ in range(11)]
    for i in range(9):
        g[10 - i][2 + i] = "s"; g[10 - i][12 - i] = "s"
    for r in range(0, 3):
        for c in range(10, 14): g[r][c] = "s"
        for c in range(1, 5): g[r][c] = "s"
    return ["".join(r) for r in g]


def pix(grid, cmap, ox, oy, ztop, cell, face, d0=-0.05, d1=0.18, group="Signs"):
    """Pixel art from boxes. (ox, oy) = viewer's left edge on the sign plane; rows go top -> bottom."""
    for r, row in enumerate(grid):
        c = 0
        while c < len(row):
            ch = row[c]; k = c
            while k < len(row) and row[k] == ch: k += 1
            m = cmap.get(ch)
            if m:
                FB(face, ox, oy, c * cell, d0, ztop - (r + 1) * cell, k * cell, d1, ztop - r * cell, m, group)
            c = k


def text_grid(s):
    return ["0".join(FONT[ch][r] for ch in s) for r in range(7)]


def text(s, cx, cy, zc, cell, face, mat, d0=-0.05, d1=0.18, group="Signs"):
    g = text_grid(s)
    w = len(g[0]) * cell
    (rx, ry), _ = FACE[face]
    pix(g, {"1": mat}, cx - rx * w / 2, cy - ry * w / 2, zc + 3.5 * cell, cell, face, d0, d1, group)
    return w


def icon(grid, cmap, cx, cy, zc, cell, face, d0=-0.05, d1=0.18, group="Signs"):
    w = len(grid[0]) * cell; h = len(grid) * cell
    (rx, ry), _ = FACE[face]
    pix(grid, cmap, cx - rx * w / 2, cy - ry * w / 2, zc + h / 2, cell, face, d0, d1, group)


# ------------------------------------------------------------------ curved solids
def ring(cx, cy, r0, r1, z0, z1, mat, group="Props", seg=16, a0=0.0, a1=360.0):
    n = max(1, int(round(seg * (a1 - a0) / 360.0)))
    for i in range(n):
        t0 = math.radians(a0 + (a1 - a0) * i / n); t1 = math.radians(a0 + (a1 - a0) * (i + 1) / n)
        q = [(cx + r0 * math.cos(t0), cy + r0 * math.sin(t0)), (cx + r1 * math.cos(t0), cy + r1 * math.sin(t0)),
             (cx + r1 * math.cos(t1), cy + r1 * math.sin(t1)), (cx + r0 * math.cos(t1), cy + r0 * math.sin(t1))]
        sc.prism(q, z0, z1, mat, group, False)


def ball(cx, cy, cz, r, mat, group="Props", lat0=-90.0, lat1=90.0, seg=10, rings=5, rz=None, sx=1.0, sy=1.0):
    rz = r if rz is None else rz
    secs = []
    for k in range(rings + 1):
        la = math.radians(lat0 + (lat1 - lat0) * k / rings)
        rr = max(r * math.cos(la), 0.02); z = cz + rz * math.sin(la)
        secs.append([(cx + rr * sx * math.cos(2 * math.pi * i / seg), cy + rr * sy * math.sin(2 * math.pi * i / seg), z) for i in range(seg)])
    sc.loft(secs, mat, group, True, False)


def hcyl(axis, a0, a1, c, z, r, mat, group="Props", seg=8):
    """Horizontal cylinder along axis ('x' or 'y') from a0 to a1; c = the other plan coordinate."""
    def sec(a):
        out = []
        for i in range(seg):
            t = 2 * math.pi * (i + 0.5) / seg
            p = (c + r * math.cos(t), z + r * math.sin(t))
            out.append((a, p[0], p[1]) if axis == "x" else (p[0], a, p[1]))
        return out
    sc.loft([sec(a0), sec(a1)], mat, group, True, False)


def beam(p0, p1, w, mat, group="Props"):
    """Square bar between two 3D points (posts, braces, legs)."""
    dx, dy, dz = (p1[i] - p0[i] for i in range(3))
    l = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
    d = (dx / l, dy / l, dz / l)
    up = (0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0)
    a = (d[1] * up[2] - d[2] * up[1], d[2] * up[0] - d[0] * up[2], d[0] * up[1] - d[1] * up[0])
    la = math.sqrt(sum(v * v for v in a)); a = tuple(v / la * w / 2 for v in a)
    b = (d[1] * a[2] - d[2] * a[1], d[2] * a[0] - d[0] * a[2], d[0] * a[1] - d[1] * a[0])
    lb = math.sqrt(sum(v * v for v in b)); b = tuple(v / lb * w / 2 for v in b)
    def s(p): return [tuple(p[i] + sa * a[i] + sb * b[i] for i in range(3)) for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    sc.loft([s(p0), s(p1)], mat, group, True, False)


# ------------------------------------------------------------------ walls / roofs / stairs
def wall(axis, fixed, a0, a1, z0, z1, ops, mat, group="House", t=0.8, inside=0, mat_in=None, frame="White", tag="Wall",
         glass="Glass", collide=True):
    """Wall along `axis` centred on `fixed`. ops: (u0, u1, zb, zt, kind) kind = door | win | open.
    inside = +1/-1: which side of the centreline is the room (gets mat_in)."""
    lo, hi = fixed - t / 2, fixed + t / 2

    def bx(u0, u1, f0, f1, za, zb, m, g=group):
        if axis == "x": B(u0, f0, za, u1, f1, zb, m, g)
        else: B(f0, u0, za, f1, u1, zb, m, g)

    def piece(u0, u1, za, zb):
        if u1 - u0 < 0.02 or zb - za < 0.02: return
        if mat_in and inside:
            if inside > 0:
                bx(u0, u1, lo, fixed, za, zb, mat); bx(u0, u1, fixed, hi, za, zb, mat_in)
            else:
                bx(u0, u1, lo, fixed, za, zb, mat_in); bx(u0, u1, fixed, hi, za, zb, mat)
        else:
            bx(u0, u1, lo, hi, za, zb, mat)

    def col(u0, u1, za, zb):
        if not collide or u1 - u0 < 0.02 or zb - za < 0.02: return
        if axis == "x": COL(u0, lo, za, u1, hi, zb, tag, group)
        else: COL(lo, u0, za, hi, u1, zb, tag, group)

    cur = a0
    for (u0, u1, zb, zt, kind) in sorted(ops):
        piece(cur, u0, z0, z1); col(cur, u0, z0, z1)
        piece(u0, u1, z0, zb); piece(u0, u1, zt, z1)
        if kind == "win":
            col(u0, u1, z0, z1)
        else:
            col(u0, u1, z0, zb); col(u0, u1, zt, z1)
        if kind != "open":
            e = 0.16; f0, f1 = lo - e, hi + e; th = 0.22
            bx(u0, u0 + th, f0, f1, zb, zt, frame); bx(u1 - th, u1, f0, f1, zb, zt, frame)
            bx(u0 + th, u1 - th, f0, f1, zt - th, zt, frame)
            if kind == "win":
                bx(u0 + th, u1 - th, f0 - 0.14, f1 + 0.14, zb, zb + th, frame)
                bx(u0 + th, u1 - th, fixed - 0.07, fixed + 0.07, zb + th, zt - th, "Glass", glass)
                um = (u0 + u1) / 2; zm = (zb + zt) / 2
                bx(um - 0.09, um + 0.09, fixed - 0.16, fixed + 0.16, zb + th, zt - th, frame)
                bx(u0 + th, um - 0.09, fixed - 0.16, fixed + 0.16, zm - 0.09, zm + 0.09, frame)
                bx(um + 0.09, u1 - th, fixed - 0.16, fixed + 0.16, zm - 0.09, zm + 0.09, frame)
        cur = u1
    piece(cur, a1, z0, z1); col(cur, a1, z0, z1)


def roof_gable(group, axis, r0, r1, c0, c1, za, zr, mats, rows=7, seed=1, th=0.3, under="RoofRedD", cap=None, wmin=3.0, wmax=6.5):
    """Gable roof, ridge along `axis` from r0..r1, eaves at c0 and c1 (height za), ridge height zr. Shingle rows of plates."""
    rng = random.Random(seed)
    cm = (c0 + c1) / 2

    def P(r, c, z):
        return (r, c, z) if axis == "x" else (c, r, z)

    for side in (0, 1):
        ce = c0 if side == 0 else c1

        def pt(r, s, dz=0.0):
            return P(r, ce + (cm - ce) * s, za + (zr - za) * s + dz)
        sc.plate(pt(r0, 0), pt(r1, 0), pt(r1, 1), pt(r0, 1), 0.25, under, group)
        for k in range(rows):
            s0 = k / rows + 0.01; s1 = (k + 1) / rows - 0.01
            rs = r0
            first = True
            while rs < r1 - 0.2:
                w = rng.uniform(wmin, wmax) * (0.5 if (first and k % 2) else 1.0)
                first = False
                re = min(r1, rs + w)
                if r1 - re < 1.2: re = r1
                m = rng.choice(mats)
                sc.plate(pt(rs + 0.05, s0, 0.3), pt(re - 0.05, s0, 0.3), pt(re - 0.05, s1, 0.3), pt(rs + 0.05, s1, 0.3), th + 0.05 * (k % 2), m, group)
                rs = re
    cap = cap or under
    if axis == "x": B(r0 - 0.1, cm - 0.55, zr + 0.25, r1 + 0.1, cm + 0.55, zr + 0.95, cap, group)
    else: B(cm - 0.55, r0 - 0.1, zr + 0.25, cm + 0.55, r1 + 0.1, zr + 0.95, cap, group)


def gable_solid(group, axis, r0, r1, c0, c1, zb, zr, mat):
    if axis == "x": sc.gable_x(r0, r1, c0, c1, zb, zr, mat, group)
    else: sc.gable_y(c0, c1, r0, r1, zb, zr, mat, group)


def stairs(x0, y0, x1, y1, z0, z1, n, direction, mat="WoodMid", group="HouseInterior", tread="WoodLight", tag="Stair"):
    """n steps filling the rectangle, ascending towards `direction` (N/S/E/W)."""
    rise = (z1 - z0) / n
    for i in range(n):
        if direction in ("N", "S"):
            run = (y1 - y0) / n
            ya = y0 + i * run if direction == "N" else y1 - (i + 1) * run
            bx = (x0, ya, x1, ya + run)
        else:
            run = (x1 - x0) / n
            xa = x0 + i * run if direction == "E" else x1 - (i + 1) * run
            bx = (xa, y0, xa + run, y1)
        zt = z0 + (i + 1) * rise
        B(bx[0], bx[1], z0, bx[2], bx[3], zt - 0.18, mat, group)
        B(bx[0], bx[1], zt - 0.18, bx[2], bx[3], zt, tread, group)
        COL(bx[0], bx[1], z0, bx[2], bx[3], zt, tag, group)


def swindow(cx, cy, zb, zt, w, face, group="Neighbors", lit=True, shutters=None, box=False):
    """Surface window for closed facades: warm pane + white frame + muntins (+ shutters / flower box)."""
    h = w / 2
    FB(face, cx, cy, -h, -0.05, zb, h, 0.1, zt, "WindowWarm" if lit else "SkyBlue", group)
    FB(face, cx, cy, -h - 0.35, -0.05, zb - 0.35, h + 0.35, 0.24, zb, "White", group)
    FB(face, cx, cy, -h - 0.35, -0.05, zt, h + 0.35, 0.24, zt + 0.35, "White", group)
    FB(face, cx, cy, -h - 0.35, -0.05, zb, -h, 0.24, zt, "White", group)
    FB(face, cx, cy, h, -0.05, zb, h + 0.35, 0.24, zt, "White", group)
    FB(face, cx, cy, -0.1, 0.0, zb, 0.1, 0.2, zt, "White", group)
    zm = (zb + zt) / 2
    FB(face, cx, cy, -h, 0.0, zm - 0.1, -0.1, 0.19, zm + 0.1, "White", group)
    FB(face, cx, cy, 0.1, 0.0, zm - 0.1, h, 0.19, zm + 0.1, "White", group)
    if shutters:
        FB(face, cx, cy, -h - 1.6, -0.05, zb - 0.1, -h - 0.4, 0.16, zt + 0.1, shutters, group)
        FB(face, cx, cy, h + 0.4, -0.05, zb - 0.1, h + 1.6, 0.16, zt + 0.1, shutters, group)
    if box:
        FB(face, cx, cy, -h - 0.2, 0.24, zb - 1.1, h + 0.2, 1.0, zb - 0.36, "WoodMid", group)
        rr = random.Random(int(cx * 3 + cy * 7))
        a = -h
        while a < h - 0.3:
            FB(face, cx, cy, a + 0.05, 0.3, zb - 0.36, a + 0.5, 0.9, zb + rr.uniform(0.0, 0.35), rr.choice(["FlowerRed", "FlowerYellow", "FlowerPink", "Leaf"]), group)
            a += 0.55


# ------------------------------------------------------------------ vegetation
def tree(x, y, s=1.0, seed=0):
    r = random.Random(seed * 131 + int(x) * 7 + int(y))
    th = 7.0 * s; w = 1.0 * s
    B(x - w, y - w, 0, x + w, y + w, th + 1, "Trunk", "Trees", True, "TreeTrunk")
    cw = 5.2 * s
    mats = ["Leaf", "LeafB", "LeafC"]
    m0 = r.choice(mats)
    B(x - cw, y - cw, th, x + cw, y + cw, th + 8.5 * s, m0, "Trees")
    COL(x - cw, y - cw, th, x + cw, y + cw, th + 8.5 * s, "TreeCrown", "Trees")
    for k in range(4):
        ang = k * math.pi / 2 + r.uniform(-0.5, 0.5)
        d = cw * r.uniform(0.75, 1.0); cs = cw * r.uniform(0.5, 0.72)
        ox, oy = x + d * math.cos(ang), y + d * math.sin(ang); zb = th + r.uniform(0.6, 3.2) * s
        m = r.choice([q for q in mats if q != m0])
        B(ox - cs, oy - cs, zb, ox + cs, oy + cs, zb + 2 * cs * r.uniform(0.8, 1.0), m, "Trees")
        COL(ox - cs, oy - cs, zb, ox + cs, oy + cs, zb + 2 * cs, "TreeCrown", "Trees")
    ts = cw * 0.62
    ox, oy = x + r.uniform(-1, 1), y + r.uniform(-1, 1)
    B(ox - ts, oy - ts, th + 8.5 * s - 0.4, ox + ts, oy + ts, th + 8.5 * s + ts * 1.5, r.choice(mats), "Trees")
    COL(ox - ts, oy - ts, th + 8.5 * s, ox + ts, oy + ts, th + 8.5 * s + ts * 1.5, "TreeCrown", "Trees")


def pine(x, y, s=1.0, col=True, seed=0, z=0.0, group="Trees"):
    r = random.Random(seed * 17 + int(x) * 3 + int(y) * 5)
    B(x - 0.8 * s, y - 0.8 * s, z, x + 0.8 * s, y + 0.8 * s, z + 5 * s, "Trunk", group, col, "TreeTrunk")
    zz = z + 4 * s; w = 5.0 * s
    for k in range(4):
        h = 4.2 * s
        m = "Pine" if (k + r.randint(0, 1)) % 2 == 0 else "PineB"
        j = r.uniform(-0.15, 0.15) * s
        B(x - w + j, y - w - j, zz, x + w + j, y + w - j, zz + h, m, group)
        if col: COL(x - w, y - w, zz, x + w, y + w, zz + h, "TreeCrown", "Trees")
        zz += h - 0.3 * s; w *= 0.7
    B(x - 0.5 * s, y - 0.5 * s, zz, x + 0.5 * s, y + 0.5 * s, zz + 1.6 * s, "PineB", group)


def bush(x, y, s=1.0, seed=0, col=True, group="Bushes"):
    r = random.Random(seed * 53 + int(x * 3) + int(y * 11))
    w = 1.9 * s
    m = r.choice(["Hedge", "HedgeB", "Leaf"])
    B(x - w, y - w, 0, x + w, y + w, 3.0 * s, m, group, col, "Bush")
    for k in range(r.randint(1, 3)):
        ox, oy = x + r.uniform(-1.6, 1.6) * s, y + r.uniform(-1.6, 1.6) * s; cs = w * r.uniform(0.55, 0.8)
        m2 = r.choice([q for q in ["Hedge", "HedgeB", "LeafB"] if q != m])
        B(ox - cs, oy - cs, r.uniform(0.3, 1.2) * s, ox + cs, oy + cs, 3.0 * s + cs * r.uniform(0.3, 0.9), m2, group)


def hedge(x0, y0, x1, y1, h=3.2, seed=0):
    """Blocky clipped hedge filling the rectangle (cubes of varying height)."""
    r = random.Random(seed + int(x0 * 3 + y0 * 5))
    COL(x0, y0, 0, x1, y1, h, "Hedge", "Bushes")
    alongx = (x1 - x0) >= (y1 - y0)
    a0, a1 = (x0, x1) if alongx else (y0, y1)
    a = a0; k = 0
    while a < a1 - 0.05:
        w = min(r.uniform(2.6, 4.2), a1 - a)
        if a1 - (a + w) < 1.2: w = a1 - a
        m = ["Hedge", "HedgeB", "Leaf"][(k + r.randint(0, 1)) % 3]
        hh = h + r.uniform(-0.5, 0.5)
        j = r.uniform(0.0, 0.25)
        if alongx: B(a, y0 - j, 0, a + w, y1 + j, hh, m, "Bushes")
        else: B(x0 - j, a, 0, x1 + j, a + w, hh, m, "Bushes")
        a += w; k += 1


def flowerbed(x0, y0, x1, y1, seed=0, z=0.0, border="StoneC"):
    r = random.Random(seed + int(x0 * 7 + y0 * 3))
    B(x0, y0, z, x1, y1, z + 0.5, border, "Flowers", True, "FlowerBed")
    B(x0 + 0.4, y0 + 0.4, z + 0.3, x1 - 0.4, y1 - 0.4, z + 0.62, "Dirt", "Flowers")
    n = int((x1 - x0) * (y1 - y0) / 2.4)
    for _ in range(n):
        fx, fy = r.uniform(x0 + 0.8, x1 - 0.8), r.uniform(y0 + 0.8, y1 - 0.8)
        hh = r.uniform(0.9, 1.7)
        B(fx - 0.09, fy - 0.09, z + 0.6, fx + 0.09, fy + 0.09, z + hh, "Leaf", "Flowers")
        m = r.choice(["FlowerRed", "FlowerRed", "FlowerYellow", "FlowerPink", "FlowerWhite"])
        B(fx - 0.32, fy - 0.32, z + hh, fx + 0.32, fy + 0.32, z + hh + 0.5, m, "Flowers")


# ------------------------------------------------------------------ fences
def picket_fence(axis, fixed, a0, a1, z=0.0, h=3.2, mat="White", group="Fences", col=True):
    def bx(u0, u1, f0, f1, za, zb, m=mat):
        if axis == "x": B(u0, f0, za, u1, f1, zb, m, group)
        else: B(f0, u0, za, f1, u1, zb, m, group)
    if a1 - a0 < 0.6: return
    if col:
        if axis == "x": COL(a0, fixed - 0.3, z, a1, fixed + 0.3, z + h, "PicketFence", group)
        else: COL(fixed - 0.3, a0, z, fixed + 0.3, a1, z + h, "PicketFence", group)
    bx(a0, a1, fixed - 0.1, fixed + 0.1, z + 0.8, z + 1.2); bx(a0, a1, fixed - 0.1, fixed + 0.1, z + h - 1.3, z + h - 0.9)
    n = max(1, int(round((a1 - a0) / 1.25)))
    st = (a1 - a0) / n
    for i in range(n):
        u = a0 + i * st + st / 2
        bx(u - 0.38, u + 0.38, fixed - 0.22, fixed + 0.22, z + 0.15, z + h - 0.35)
        bx(u - 0.2, u + 0.2, fixed - 0.22, fixed + 0.22, z + h - 0.35, z + h)
    for u in (a0, a1):
        bx(u - 0.42, u + 0.42, fixed - 0.42, fixed + 0.42, z, z + h + 0.5)
        bx(u - 0.55, u + 0.55, fixed - 0.55, fixed + 0.55, z + h + 0.5, z + h + 0.8)


def plank_fence(axis, fixed, a0, a1, z=0.0, h=6.5, group="Fences", seed=0):
    r = random.Random(seed + int(fixed * 3 + a0))
    def bx(u0, u1, f0, f1, za, zb, m):
        if axis == "x": B(u0, f0, za, u1, f1, zb, m, group)
        else: B(f0, u0, za, f1, u1, zb, m, group)
    if axis == "x": COL(a0, fixed - 0.35, z, a1, fixed + 0.35, z + h, "PlankFence", group)
    else: COL(fixed - 0.35, a0, z, fixed + 0.35, a1, z + h, "PlankFence", group)
    n = max(1, int(round((a1 - a0) / 1.5)))
    st = (a1 - a0) / n
    for i in range(n):
        u = a0 + i * st
        m = "Fence" if (i + r.randint(0, 3)) % 3 else "FenceB"
        bx(u + 0.04, u + st - 0.04, fixed - 0.2, fixed + 0.2, z + 0.1, z + h - r.uniform(0.0, 0.3), m)
    bx(a0, a1, fixed - 0.34, fixed + 0.34, z + h - 1.5, z + h - 1.1, "WoodDark")
    bx(a0, a1, fixed - 0.34, fixed + 0.34, z + 1.0, z + 1.4, "WoodDark")
    k = a0
    while k <= a1 + 0.01:
        bx(k - 0.4, k + 0.4, fixed - 0.4, fixed + 0.4, z, z + h + 0.5, "WoodDark")
        k += max(6.0, (a1 - a0) / max(1, round((a1 - a0) / 9.0)))


# ------------------------------------------------------------------ street furniture
def lamp_post(x, y, banner=None, h=13.0, light=True):
    B(x - 0.6, y - 0.6, 0, x + 0.6, y + 0.6, 1.4, "Iron", "Props", True, "LampPost")
    C(x, y, 1.4, h, 0.3, "Iron", "Props", 6)
    COL(x - 0.35, y - 0.35, 1.4, x + 0.35, y + 0.35, h, "LampPost", "Props")
    B(x - 0.8, y - 0.8, h, x + 0.8, y + 0.8, h + 0.3, "Iron")
    B(x - 0.65, y - 0.65, h + 0.3, x + 0.65, y + 0.65, h + 2.0, "Lamp")
    sc.pyramid_roof(x - 1.0, y - 1.0, x + 1.0, y + 1.0, h + 2.0, h + 3.0, "Iron", "Props")
    if light: sc.anchor("LampLight", (x, y, h + 1.2), range=36)
    if banner:
        (rx, ry), (nx, ny) = FACE[banner]
        # arm sticks out to the viewer's right, banner hangs under it, readable from both sides
        ax, ay = x + rx * 0.3, y + ry * 0.3
        FB(banner, ax, ay, 0, -0.12, h - 1.6, 3.4, 0.12, h - 1.3, "Iron")
        FB(banner, ax, ay, 0.5, -0.1, h - 7.6, 3.3, 0.1, h - 1.6, "Red")
        FB(banner, ax, ay, 0.5, -0.14, h - 8.0, 3.3, 0.14, h - 7.6, "Gold")
        icon(GRILL_ICON, {"1": "White"}, ax + rx * 1.9, ay + ry * 1.9, h - 4.4, 0.2, banner, 0.05, 0.2)
        icon(GRILL_ICON, {"1": "White"}, ax + rx * 1.9, ay + ry * 1.9, h - 4.4, 0.2, OPP[banner], 0.05, 0.2)


def bench(x, y, face):
    """Park bench centred at x,y; sitters look towards `face`."""
    FB(face, x, y, -3, -0.9, 1.3, 3, 0.9, 1.65, "WoodMid", "Props")
    for a in (-2.1, -0.7, 0.7, 2.1):
        FB(face, x, y, a - 0.62, -0.95, 1.65, a + 0.62, 0.95, 1.8, "WoodLight", "Props")
    FB(face, x, y, -3, -1.2, 2.2, 3, -0.85, 2.9, "WoodLight", "Props"); FB(face, x, y, -3, -1.2, 3.1, 3, -0.85, 3.8, "WoodLight", "Props")
    for a in (-2.8, 2.5):
        FB(face, x, y, a, -1.25, 0, a + 0.3, 1.0, 1.3, "Iron", "Props"); FB(face, x, y, a, -1.3, 1.3, a + 0.3, -0.9, 4.0, "Iron", "Props")
        FB(face, x, y, a, -0.9, 2.5, a + 0.3, 1.0, 2.75, "Iron", "Props")
    (rx, ry), (nx, ny) = FACE[face]
    COL(x - abs(rx) * 3 - abs(nx) * 1.3, y - abs(ry) * 3 - abs(ny) * 1.3, 0, x + abs(rx) * 3 + abs(nx) * 1.3, y + abs(ry) * 3 + abs(ny) * 1.3, 2.0, "Bench", "Props")


def burger(x, y, z, s=1.0):
    C(x, y, z, z + 0.3 * s, 0.75 * s, "Bun", seg=8); C(x, y, z + 0.3 * s, z + 0.5 * s, 0.82 * s, "Meat", seg=8)
    B(x - 0.8 * s, y - 0.8 * s, z + 0.5 * s, x + 0.8 * s, y + 0.8 * s, z + 0.6 * s, "Cheese")
    C(x, y, z + 0.6 * s, z + 0.72 * s, 0.86 * s, "Lettuce", seg=8)
    ball(x, y, z + 0.72 * s, 0.75 * s, "Bun", lat0=0, lat1=90, seg=8, rings=3, rz=0.55 * s)


def cup(x, y, z, mat="Red"):
    C(x, y, z, z + 1.1, 0.34, mat, seg=6); C(x, y, z + 1.1, z + 1.2, 0.4, "White", seg=6)
    B(x - 0.06, y - 0.06, z + 1.2, x + 0.06, y + 0.06, z + 1.9, "White")


def plate(x, y, z):
    C(x, y, z, z + 0.1, 0.7, "White", seg=8)


def picnic_table(x, y, axis="x", cloth=True, food=True, seed=0, wood="WoodMid", top="WoodLight"):
    """Table 8 long along `axis` with two benches. Top at z 3.1."""
    def bx(u0, v0, za, u1, v1, zb, m, g="Props"):
        if axis == "x": B(x + u0, y + v0, za, x + u1, y + v1, zb, m, g)
        else: B(x + v0, y + u0, za, x + v1, y + u1, zb, m, g)
    for i in range(4):
        v0 = -2.0 + i * 1.0
        bx(-4, v0 + 0.04, 2.8, 4, v0 + 0.96, 3.1, top if i % 2 else wood)
    for v in (-3.9, 2.7):
        bx(-4, v, 1.5, 4, v + 1.2, 1.8, top)
    for u in (-3.2, 2.7):
        bx(u, -3.7, 1.2, u + 0.5, 3.7, 1.5, wood)
        bx(u, -1.6, 0, u + 0.5, -1.1, 2.8, wood); bx(u, 1.1, 0, u + 0.5, 1.6, 2.8, wood)
        bx(u, -3.6, 0, u + 0.5, -3.1, 1.2, wood); bx(u, 3.1, 0, u + 0.5, 3.6, 1.2, wood)
    if axis == "x": COL(x - 4, y - 3.9, 0, x + 4, y + 3.9, 1.8, "PicnicTable", "Props"); COL(x - 4, y - 2, 1.8, x + 4, y + 2, 3.1, "PicnicTable", "Props")
    else: COL(x - 3.9, y - 4, 0, x + 3.9, y + 4, 1.8, "PicnicTable", "Props"); COL(x - 2, y - 4, 1.8, x + 2, y + 4, 3.1, "PicnicTable", "Props")
    zt = 3.1
    if cloth:
        for i in range(6):
            for j in range(4):
                bx(-3 + i * 1.0, -2.1 + j * 1.05, 3.1, -2 + i * 1.0, -1.05 + j * 1.05, 3.2, "Red" if (i + j) % 2 else "White")
        zt = 3.2
    if food:
        r = random.Random(seed)
        px, py = (x - 1.6, y + 0.3) if axis == "x" else (x + 0.3, y - 1.6)
        plate(px, py, zt); burger(px, py, zt + 0.1, 0.8)
        qx, qy = (x + 1.4, y - 0.6) if axis == "x" else (x - 0.6, y + 1.4)
        cup(qx, qy, zt, r.choice(["Red", "Blue", "Yellow"]))
        qx, qy = (x + 0.2, y + 1.0) if axis == "x" else (x + 1.0, y + 0.2)
        B(qx - 0.2, qy - 0.2, zt, qx + 0.2, qy + 0.2, zt + 1.0, "Ketchup"); B(qx - 0.08, qy - 0.08, zt + 1.0, qx + 0.08, qy + 0.08, zt + 1.3, "White")
        B(qx + 0.5, qy - 0.2, zt, qx + 0.9, qy + 0.2, zt + 1.0, "Mustard"); B(qx + 0.62, qy - 0.08, zt + 1.0, qx + 0.78, qy + 0.08, zt + 1.3, "White")


def smoke(x, y, z, n=5, s=1.0, seed=0, group="Smoke"):
    r = random.Random(seed + int(x * 5 + y * 3))
    ox = oy = 0.0
    for k in range(n):
        w = (0.45 + 0.17 * k) * s
        B(x + ox - w, y + oy - w, z, x + ox + w, y + oy + w, z + 1.5 * w, "Smoke", group)
        z += 1.5 * w + 0.35 * s
        ox += r.uniform(-0.2, 0.9) * s; oy += r.uniform(-0.5, 0.5) * s


def kettle_grill(x, y, s=1.0, color="Red", fire=True, lid=True, seed=0, sausages=3, group="Props"):
    """Round kettle grill on three legs. Bowl radius 1.9*s at z ~3.4*s."""
    r = 1.9 * s; zc = 3.6 * s
    for k in range(3):
        a = math.radians(90 + 120 * k)
        beam((x + 1.5 * s * math.cos(a), y + 1.5 * s * math.sin(a), 0), (x + 0.9 * s * math.cos(a), y + 0.9 * s * math.sin(a), zc - 1.2 * s), 0.22 * s, "Iron", group)
    ball(x, y, zc, r, color, group, lat0=-90, lat1=0, seg=10, rings=4, rz=1.6 * s)
    ring(x, y, r - 0.02, r + 0.16 * s, zc - 0.12 * s, zc + 0.1 * s, "Chrome", group, 10)
    C(x, y, zc - 0.5 * s, zc - 0.12 * s, r * 0.93, "Coal", group, 10)
    if fire:
        C(x, y, zc - 0.12 * s, zc - 0.05 * s, r * 0.8, "Fire", group, 8)
    C(x, y, zc - 0.05 * s, zc + 0.02 * s, r * 0.95, "Iron", group, 10)
    rr = random.Random(seed)
    for k in range(sausages):
        yy = y - 0.8 * s + k * 0.7 * s
        hcyl("x", x - 0.75 * s, x + 0.75 * s, yy, zc + 0.16 * s, 0.14 * s, "Sausage", group, 6)
    if lid:
        # lid leaning on the back
        ball(x, y + r * 1.02, zc + 0.5 * s, r * 0.98, color, group, lat0=0, lat1=90, seg=10, rings=3, rz=1.3 * s, sy=0.45)
        B(x - 0.3 * s, y + r * 1.0 - 0.1, zc + 1.8 * s, x + 0.3 * s, y + r * 1.0 + 0.1, zc + 2.1 * s, "Black", group)
    COL(x - r, y - r, 0, x + r, y + r, zc + 0.2, "Grill", "Props")
    if fire: smoke(x, y - 0.2, zc + 0.9 * s, 4, 0.8 * s, seed)


def umbrella_table(x, y, color="Red", alt="White", chairs=4, seed=0):
    C(x, y, 0, 0.3, 1.0, "Iron", seg=8); C(x, y, 0.3, 2.7, 0.25, "Iron", seg=6)
    C(x, y, 2.7, 3.0, 2.7, "White", seg=10)
    COL(x - 2.5, y - 2.5, 0, x + 2.5, y + 2.5, 3.0, "Table", "Props")
    C(x, y, 3.0, 10.2, 0.16, "WoodLight", seg=6)
    n = 8
    for i in range(n):
        t0 = 2 * math.pi * i / n; t1 = 2 * math.pi * (i + 1) / n
        v = [(x + 6.2 * math.cos(t0), y + 6.2 * math.sin(t0), 8.6), (x + 6.2 * math.cos(t1), y + 6.2 * math.sin(t1), 8.6), (x, y, 10.6),
             (x + 6.2 * math.cos(t0), y + 6.2 * math.sin(t0), 8.3), (x + 6.2 * math.cos(t1), y + 6.2 * math.sin(t1), 8.3), (x, y, 10.2)]
        sc.add("Props", color if i % 2 == 0 else alt, v, [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)])
    B(x - 0.25, y - 0.25, 10.5, x + 0.25, y + 0.25, 11.1, color)
    for k in range(chairs):
        a = math.pi / 4 + k * 2 * math.pi / chairs
        cx, cy = x + 4.0 * math.cos(a), y + 4.0 * math.sin(a)
        B(cx - 0.9, cy - 0.9, 1.4, cx + 0.9, cy + 0.9, 1.7, "WoodLight", "Props", True, "Chair")
        for dx, dy in ((-0.75, -0.75), (0.75, -0.75), (-0.75, 0.75), (0.75, 0.75)):
            B(cx + dx - 0.12, cy + dy - 0.12, 0, cx + dx + 0.12, cy + dy + 0.12, 1.4, "WoodMid")
        bx_, by_ = cx + 0.8 * math.cos(a), cy + 0.8 * math.sin(a)
        if abs(math.cos(a)) > abs(math.sin(a)): B(bx_ - 0.12, cy - 0.9, 1.7, bx_ + 0.12, cy + 0.9, 3.6, "WoodMid")
        else: B(cx - 0.9, by_ - 0.12, 1.7, cx + 0.9, by_ + 0.12, 3.6, "WoodMid")
    plate(x - 1.0, y + 0.6, 3.0); burger(x - 1.0, y + 0.6, 3.1, 0.7); cup(x + 1.1, y - 0.7, 3.0, "Blue")


def mailbox(x, y, face, label=None, color="White"):
    B(x - 0.3, y - 0.3, 0, x + 0.3, y + 0.3, 3.6, "WoodMid", "Props", True, "Mailbox")
    FB(face, x, y, -1.0, -1.6, 3.6, 1.0, 1.6, 4.9, color, "Props")
    hc = "x" if face in ("E", "W") else "y"
    if hc == "x": hcyl("x", x - 1.6, x + 1.6, y, 4.9, 1.0, color, "Props", 8)
    else: hcyl("y", y - 1.6, y + 1.6, x, 4.9, 1.0, color, "Props", 8)
    FB(face, x, y, 0.95, 0.4, 4.6, 1.15, 0.7, 6.4, "Red", "Props"); FB(face, x, y, 0.95, 0.4, 5.8, 1.15, 1.5, 6.4, "Red", "Props")
    if label:
        s = "E" if face in ("N", "S") else "S"
        for side in (s, OPP[s]):
            (rx, ry), (nx, ny) = FACE[side]
            icon(FLAME_ICON, {"o": "Fire", "y": "FireY", "w": "White"}, x + nx * 1.0, y + ny * 1.0, 4.6, 0.14, side, 0.0, 0.1)


def gnome(x, y, face, s=1.0):
    FB(face, x, y, -0.7 * s, -0.55 * s, 0, 0.7 * s, 0.55 * s, 0.5 * s, "Black", "Props")
    FB(face, x, y, -0.8 * s, -0.6 * s, 0.5 * s, 0.8 * s, 0.6 * s, 1.9 * s, "Blue", "Props", True, "Gnome")
    FB(face, x, y, -0.8 * s, 0.55 * s, 0.9 * s, 0.8 * s, 0.68 * s, 1.1 * s, "Leather", "Props")
    FB(face, x, y, -0.7 * s, -0.55 * s, 1.9 * s, 0.7 * s, 0.6 * s, 3.0 * s, "Skin", "Props")
    FB(face, x, y, -0.7 * s, 0.55 * s, 1.5 * s, 0.7 * s, 0.85 * s, 2.3 * s, "White", "Props")
    FB(face, x, y, -0.45 * s, 0.8 * s, 1.2 * s, 0.45 * s, 0.95 * s, 1.6 * s, "White", "Props")
    FB(face, x, y, -0.75 * s, 0.56 * s, 2.45 * s, 0.75 * s, 0.75 * s, 2.75 * s, "Black", "Props")
    FB(face, x, y, -0.15 * s, 0.6 * s, 2.25 * s, 0.15 * s, 0.9 * s, 2.5 * s, "Skin", "Props")
    sc.cone(x, y, 3.0 * s, 5.4 * s, 1.0 * s, "Red", "Props", 6)
    FB(face, x, y, -1.2 * s, -0.2 * s, 1.0 * s, -0.8 * s, 0.2 * s, 1.8 * s, "Blue", "Props")
    FB(face, x, y, 0.8 * s, -0.2 * s, 1.1 * s, 1.2 * s, 0.6 * s, 1.5 * s, "Blue", "Props")
    FB(face, x, y, 1.25 * s, 0.3 * s, 1.2 * s, 1.4 * s, 0.45 * s, 3.0 * s, "WoodLight", "Props")
    FB(face, x, y, 0.95 * s, 0.28 * s, 3.0 * s, 1.7 * s, 0.47 * s, 3.9 * s, "Steel", "Props")


def flamingo(x, y, face, chef=True, apron=True):
    C(x, y, 0, 0.25, 0.9, "Hedge", seg=6)
    B(x - 0.08, y - 0.08, 0.25, x + 0.08, y + 0.08, 3.0, "Black", "Props", True, "Flamingo")
    ball(x, y, 3.8, 1.25, "Pink", "Props", seg=8, rings=4, rz=1.0)
    FB(face, x, y, -1.5, -0.25, 3.6, -0.9, 0.25, 4.4, "PinkB", "Props")
    FB(face, x, y, 0.75, -0.22, 4.0, 1.2, 0.22, 6.2, "Pink", "Props")
    FB(face, x, y, 0.7, -0.4, 6.2, 1.6, 0.4, 7.1, "Pink", "Props")
    FB(face, x, y, 1.6, -0.2, 6.3, 2.1, 0.2, 6.7, "Yellow", "Props"); FB(face, x, y, 2.1, -0.2, 6.1, 2.4, 0.2, 6.6, "Black", "Props")
    FB(face, x, y, 0.95, -0.45, 6.6, 1.65, 0.45, 6.9, "Black", "Props")
    if chef:
        FB(face, x, y, 0.75, -0.38, 7.1, 1.55, 0.38, 7.7, "White", "Props"); FB(face, x, y, 0.55, -0.55, 7.7, 1.75, 0.55, 8.5, "White", "Props")
    if apron:
        FB(face, x, y, -0.8, 1.05, 2.3, 0.8, 1.2, 4.3, "Red", "Props")
        icon(GRILL_ICON, {"1": "White"}, *FP(face, x, y, 0, 1.2), 3.3, 0.11, face, 0.0, 0.1)


def kiddie_pool(x, y, r=5.0, duck=True):
    ring(x, y, r - 0.7, r, 0, 1.5, "SkyBlue", "Props", 14)
    ring(x, y, r - 0.75, r + 0.05, 0.5, 0.9, "Blue", "Props", 14)
    C(x, y, 0, 0.3, r - 0.6, "Blue", seg=14); C(x, y, 0.3, 1.0, r - 0.65, "Water", "Water", 14)
    COL(x - r * 0.72, y - r * 0.72, 0, x + r * 0.72, y + r * 0.72, 1.5, "Pool", "Props")
    if duck:
        ball(x + 1.0, y - 0.4, 1.5, 1.0, "Yellow", seg=8, rings=4, rz=0.75)
        ball(x + 1.7, y - 0.4, 2.5, 0.6, "Yellow", seg=8, rings=4)
        B(x + 2.2, y - 0.6, 2.3, x + 2.7, y - 0.2, 2.5, "Orange"); B(x + 2.0, y - 0.75, 2.55, x + 2.25, y - 0.05, 2.75, "Black")


def charcoal_bag(x, y, face, z=0.0, lean=0.0):
    FB(face, x, y, -1.5, -0.7, z, 1.5, 0.7, z + 4.0, "Paper", "Props", True, "CharcoalBag")
    FB(face, x, y, -1.53, -0.72, z + 3.2, 1.53, 0.72, z + 3.5, "Leather", "Props")
    FB(face, x, y, -1.3, -0.5, z + 4.0, 1.3, 0.5, z + 4.5, "Paper", "Props")
    fx, fy = FP(face, x, y, 0, 0.7)
    icon(FLAME_ICON, {"o": "Fire", "y": "FireY", "w": "White"}, fx, fy, z + 1.5, 0.2, face, 0.0, 0.08)
    text("COAL", fx, fy, z + 2.9, 0.1, face, "Black", 0.0, 0.08)


def string_lights(p0, p1, n=10, sag=1.5, group="Lights"):
    cols = ["Lamp", "BulbRed", "Lamp", "BulbBlue", "Lamp", "BulbGreen"]
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t, p0[2] + (p1[2] - p0[2]) * t - sag * 4 * t * (1 - t)))
    for a, b in zip(pts[:-1], pts[1:]):
        beam(a, b, 0.09, "Black", group)
    for i, p in enumerate(pts[1:-1]):
        B(p[0] - 0.22, p[1] - 0.22, p[2] - 0.55, p[0] + 0.22, p[1] + 0.22, p[2] - 0.08, cols[i % len(cols)], group)


def hydrant(x, y):
    C(x, y, 0, 0.3, 0.7, "RedDark", seg=8); C(x, y, 0.3, 2.0, 0.5, "Red", seg=8, col=True, tag="Hydrant")
    ball(x, y, 2.0, 0.55, "Red", lat0=0, lat1=90, seg=8, rings=3); B(x - 0.85, y - 0.2, 1.2, x + 0.85, y + 0.2, 1.6, "RedDark"); B(x - 0.15, y - 0.15, 2.5, x + 0.15, y + 0.15, 2.8, "Chrome")


def trash_can(x, y):
    C(x, y, 0, 2.6, 0.9, "Green", seg=8, col=True, tag="TrashCan"); C(x, y, 2.6, 2.85, 1.0, "Iron", seg=8); B(x - 0.3, y - 0.1, 2.85, x + 0.3, y + 0.1, 3.1, "Iron")


def car(x, y, face, color="Red", kind="suv", group="Cars"):
    """Car centred at (x, y), nose towards `face`. Local frame: l forward, w to the side."""
    (nx, ny) = FACE[face][1]
    (rx, ry) = FACE[face][0]

    def lb(l0, w0, z0, l1, w1, z1, m, g=group):
        B(x + nx * l0 + rx * w0, y + ny * l0 + ry * w0, z0, x + nx * l1 + rx * w1, y + ny * l1 + ry * w1, z1, m, g)
    L = 9.0 if kind == "pickup" else 8.0   # half length
    W = 3.6
    lb(-L, -W, 1.3, L, W, 3.9, color)
    lb(-L - 0.3, -W + 0.1, 1.2, -L, W - 0.1, 2.2, "Chrome"); lb(L, -W + 0.1, 1.2, L + 0.3, W - 0.1, 2.2, "Chrome")
    lb(-L + 0.2, -W - 0.12, 1.25, L - 0.2, W + 0.12, 1.7, "Black")
    if kind == "pickup":
        c0, c1 = -1.0, 4.2
        lb(c0, -W + 0.25, 3.9, c1, W - 0.25, 6.6, color)
        lb(c0 - 0.1, -W + 0.6, 4.3, c0, W - 0.6, 6.1, "Glass", "Glass"); lb(c1, -W + 0.6, 4.3, c1 + 0.12, W - 0.6, 6.1, "Glass", "Glass")
        for sgn in (-1, 1):
            lb(c0 + 0.5, sgn * (W - 0.25), 4.3, c1 - 0.5, sgn * (W - 0.12), 6.1, "Glass", "Glass")
            lb(-L + 0.1, sgn * (W - 0.5), 3.9, c0 - 0.1, sgn * W, 4.9, color)
        lb(-L + 0.1, -W + 0.5, 3.9, -L + 0.55, W - 0.5, 4.9, color)
        lb(-L + 0.55, -W + 0.5, 3.9, c0 - 0.1, W - 0.5, 4.05, "Iron")
        lb(c0 + 0.3, -W + 0.4, 6.6, c1 - 0.3, W - 0.4, 6.8, "RedDark" if color == "Red" else "Black")
    else:
        c0, c1 = -L + 1.0, 3.6
        lb(c0, -W + 0.25, 3.9, c1, W - 0.25, 6.7, color)
        lb(c0 - 0.1, -W + 0.6, 4.4, c0, W - 0.6, 6.2, "Glass", "Glass"); lb(c1, -W + 0.6, 4.4, c1 + 0.12, W - 0.6, 6.2, "Glass", "Glass")
        for sgn in (-1, 1):
            lb(c0 + 0.5, sgn * (W - 0.25), 4.4, -1.5, sgn * (W - 0.12), 6.2, "Glass", "Glass")
            lb(-1.0, sgn * (W - 0.25), 4.4, c1 - 0.5, sgn * (W - 0.12), 6.2, "Glass", "Glass")
        lb(c0 + 0.6, -W + 0.9, 6.7, c1 - 0.6, -W + 1.2, 7.0, "Iron"); lb(c0 + 0.6, W - 1.2, 6.7, c1 - 0.6, W - 0.9, 7.0, "Iron")
    for sgn in (-1, 1):
        lb(L, sgn * (W - 1.5), 2.6, L + 0.15, sgn * (W - 0.3), 3.4, "Lamp")
        lb(-L - 0.15, sgn * (W - 1.3), 2.7, -L, sgn * (W - 0.3), 3.4, "BulbRed")
        for l in (-L + 3.0, L - 3.0):
            wx, wy = x + nx * l, y + ny * l
            a0 = sgn * (W - 0.9); a1 = sgn * (W + 0.25)
            if face in ("N", "S"):
                hcyl("x", x + rx * a0, x + rx * a1, wy, 1.45, 1.45, "Tire", group, 10)
                hcyl("x", x + rx * (a1 - sgn * 0.02), x + rx * (a1 + sgn * 0.1), wy, 1.45, 0.7, "Chrome", group, 8)
            else:
                hcyl("y", y + ry * a0, y + ry * a1, wx, 1.45, 1.45, "Tire", group, 10)
                hcyl("y", y + ry * (a1 - sgn * 0.02), y + ry * (a1 + sgn * 0.1), wx, 1.45, 0.7, "Chrome", group, 8)
    lb(L, -1.6, 2.4, L + 0.2, 1.6, 3.5, "Black")
    if face in ("N", "S"): COL(x - W, y - L - 0.3, 0, x + W, y + L + 0.3, 3.9, "Car", group); COL(x - W + 0.25, y - L + 1, 3.9, x + W - 0.25, y + L - 1, 6.6, "Car", group)
    else: COL(x - L - 0.3, y - W, 0, x + L + 0.3, y + W, 3.9, "Car", group); COL(x - L + 1, y - W + 0.25, 3.9, x + L - 1, y + W - 0.25, 6.6, "Car", group)
