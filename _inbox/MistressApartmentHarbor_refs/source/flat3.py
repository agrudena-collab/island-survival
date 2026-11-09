"""Mistress apartment #3 (Fisherman Dad / "Harbor" tower) - REFERENCE concept (Ivan 2026-11-08).
Bright, kid-friendly, lots of detail. Procedural geometry + colours only (no images).

Local coords: x 0..64 (local east), y 0..40 (local north = panoramic window + balcony side), floor z=0, ceiling z=12.
For the reference renders the flat is placed on top of the harbor tower (world z 78) and rotated 180 deg so the
panoramic window and balcony look SOUTH over the colourful town, beach and Ferris wheel.
Rooms (clear space):
  Bath     x 0..16  y 0..14      Hall   x 16..30 y 0..14 (exit door south)   Dressing x 30..44 y 0..14
  Kitchen  x 0..16  y 14..40 (open to living)   Living x 16..44 y 14..40      Bedroom  x 44..64 y 0..40
  Balcony  x 17..63 y 41..48 (outside the panoramic wall)
"""
import math, random
import fsd_lib
from fsd_lib import PALETTE

W, D, H = 64.0, 40.0, 12.0
CX, CY, OZ = 290.0, 418.0, 78.0
ROT = True
R = random.Random(2026)
_sc = None

EXTRA = {
    "WallPink":   ((255, 214, 228), "Plaster", 0.0),
    "WallPeach":  ((255, 226, 200), "Plaster", 0.0),
    "WallMint":   ((196, 242, 224), "Plaster", 0.0),
    "WallSky":    ((200, 232, 255), "Plaster", 0.0),
    "WallLilac":  ((232, 216, 255), "Plaster", 0.0),
    "WallButter": ((255, 242, 196), "Plaster", 0.0),
    "WainPink":   ((255, 160, 196), "Wood", 0.0),
    "WainTeal":   ((70, 200, 196), "Wood", 0.0),
    "WainLilac":  ((176, 140, 236), "Wood", 0.0),
    "WainYellow": ((255, 200, 70), "Wood", 0.0),
    "Rose":       ((240, 84, 140), "Fabric", 0.0),
    "Lilac":      ((186, 146, 240), "Fabric", 0.0),
    "Peach":      ((255, 178, 140), "Fabric", 0.0),
    "Aqua":       ((70, 222, 232), "SmoothPlastic", 0.0),
    "SofaCoral":  ((255, 120, 128), "Fabric", 0.0),
    "SofaTeal":   ((40, 190, 186), "Fabric", 0.0),
    "TileP":      ((255, 186, 210), "CeramicTiles", 0.0),
    "TileW":      ((255, 250, 244), "CeramicTiles", 0.0),
    "TileT":      ((110, 222, 214), "CeramicTiles", 0.0),
    "TileY":      ((255, 222, 120), "CeramicTiles", 0.0),
    "Marble":     ((248, 244, 240), "Marble", 0.0),
    "Chrome":     ((206, 212, 222), "Metal", 0.0),
    "Grout":      ((214, 206, 204), "SmoothPlastic", 0.0),
    "FloorOak":   ((236, 186, 128), "WoodPlanks", 0.0),
    "FloorOakB":  ((224, 172, 116), "WoodPlanks", 0.0),
    "FloorOakC":  ((246, 200, 144), "WoodPlanks", 0.0),
    "Slab":       ((150, 120, 96), "SmoothPlastic", 0.0),
    "Ceiling":    ((255, 250, 246), "SmoothPlastic", 0.0),
    "Screen":     ((24, 30, 46), "SmoothPlastic", 0.0),
    "ScreenOn":   ((90, 200, 255), "Neon", 0.0),
    "LampPink":   ((255, 150, 200), "Neon", 0.0),
    "LampTeal":   ((110, 240, 230), "Neon", 0.0),
    "Plush":      ((196, 140, 96), "Fabric", 0.0),
    "WaterTank":  ((90, 200, 240), "Glass", 0.35),
    "Frost":      ((236, 246, 255), "Glass", 0.25),
}

LIGHTS = []        # (x, y, z, colour, power) world coords, render-only point lights
ROOMS = {
    "Bath": (0, 0, 16, 14), "Hall": (16, 0, 30, 14), "Dressing": (30, 0, 44, 14),
    "Kitchen": (0, 14, 16, 40), "Living": (16, 14, 44, 40), "Bedroom": (44, 0, 64, 40),
}


def setup_palette():
    PALETTE.update(EXTRA)


# ---------------------------------------------------------------- transforms
def T(x, y):
    if ROT:
        return (CX - (x - W / 2), CY - (y - D / 2))
    return (CX - W / 2 + x, CY - D / 2 + y)


CUR = ["FlatProps"]


def B(x0, y0, z0, x1, y1, z1, mat, group="FlatProps", col=False, tag=None):
    if group == "FlatProps": group = CUR[0]
    a = T(x0, y0); b = T(x1, y1)
    _sc.box(min(a[0], b[0]), min(a[1], b[1]), OZ + min(z0, z1), max(a[0], b[0]), max(a[1], b[1]), OZ + max(z0, z1), mat, group, col, tag)


def Cy(x, y, z0, z1, r, mat, group="FlatProps", seg=12):
    if group == "FlatProps": group = CUR[0]
    wx, wy = T(x, y)
    _sc.cyl(wx, wy, OZ + z0, OZ + z1, r, mat, group, seg, False)


def Co(x, y, z0, z1, r, mat, group="FlatProps", seg=12):
    if group == "FlatProps": group = CUR[0]
    wx, wy = T(x, y)
    _sc.cone(wx, wy, OZ + z0, OZ + z1, r, mat, group, seg, False)


def P(pts, z0, z1, mat, group="FlatProps"):
    _sc.prism([T(*p) for p in pts], OZ + z0, OZ + z1, mat, group, False)


def light(x, y, z, col=(1.0, 0.85, 0.65), power=1.0):
    wx, wy = T(x, y)
    LIGHTS.append((wx, wy, OZ + z, col, power))


def anchor(name, x, y, z, face):
    wx, wy = T(x, y)
    _sc.anchor(name, (wx, wy, OZ + z), face=face, local=[x, y, z])


# ---------------------------------------------------------------- shell
# openings: (axis, line, a0, a1, z0, z1, kind)  axis 'x' = wall runs along x at y=line
OPEN = [
    ("x", 0, 20, 26, 0, 8.6, "door"),          # exit (south)
    ("x", 14, 19, 28, 0, 9.4, "arch"),         # hall -> living
    ("y", 16, 6, 11, 0, 8.4, "door"),          # hall -> bath
    ("y", 30, 3, 9, 0, 8.4, "door"),           # hall -> dressing
    ("y", 44, 9.5, 13.5, 0, 8.4, "door"),      # dressing -> bedroom
    ("y", 44, 22, 29, 0, 8.6, "door"),         # living -> bedroom
    ("y", 16, 17, 39, 0, 10.4, "open"),        # kitchen <-> living
    ("x", 40, 34, 40, 0, 9.0, "glassdoor"),    # living -> balcony
    ("x", 40, 50, 56, 0, 9.0, "glassdoor"),    # bedroom -> balcony
    ("x", 40, 17, 32.5, 1.2, 10.6, "window"),  # panoramic
    ("x", 40, 41.2, 43.2, 2.5, 10.0, "window"),
    ("x", 40, 3, 13, 4.2, 9.6, "window"),      # kitchen
    ("y", 0, 20, 32, 4.2, 9.6, "window"),      # kitchen west (sink)
    ("x", 40, 46, 48.6, 2.5, 10.0, "window"),  # bedroom
    ("x", 40, 57.5, 62.5, 2.5, 10.0, "window"),
    ("y", 64, 15, 29, 3.0, 10.0, "window"),    # bedroom east (window seat)
    ("y", 0, 4, 9, 6.0, 10.0, "frost"),        # bath
]


def _cut(a0, a1, z0, z1, ops):
    """Split wall span a0..a1 x z0..z1 into rectangles around openings ops=[(oa0,oa1,oz0,oz1)]."""
    rects = [(a0, a1, z0, z1)]
    for (oa0, oa1, oz0, oz1) in ops:
        nr = []
        for (b0, b1, c0, c1) in rects:
            if oa1 <= b0 or oa0 >= b1 or oz1 <= c0 or oz0 >= c1:
                nr.append((b0, b1, c0, c1)); continue
            if oa0 > b0: nr.append((b0, oa0, c0, c1))
            if oa1 < b1: nr.append((oa1, b1, c0, c1))
            m0, m1 = max(b0, oa0), min(b1, oa1)
            if oz0 > c0: nr.append((m0, m1, c0, oz0))
            if oz1 < c1: nr.append((m0, m1, oz1, c1))
        rects = nr
    return rects


def ops_on(axis, line, a0, a1):
    return [(max(o[2], a0), min(o[3], a1), o[4], o[5]) for o in OPEN if o[0] == axis and abs(o[1] - line) < 0.01 and o[3] > a0 and o[2] < a1]


def wall(axis, line, a0, a1, t=1.0, mat="White", z0=0.0, z1=H):
    for (b0, b1, c0, c1) in _cut(a0, a1, z0, z1, ops_on(axis, line, a0, a1)):
        if axis == "x":
            B(b0, line - t / 2, c0, b1, line + t / 2, c1, mat, "FlatWalls", True, "Wall")
        else:
            B(line - t / 2, b0, c0, line + t / 2, b1, c1, mat, "FlatWalls", True, "Wall")


def lining(axis, line, side, a0, a1, upper, wain, rail="White", base="White", wain_h=3.6, t_half=0.5):
    """Paint one room side of a wall: wainscot panels + chair rail + upper paint + skirting + crown, all cut by openings."""
    ops = [(o[0] - 0.25, o[1] + 0.25, o[2] - 0.25, o[3] + 0.25) for o in ops_on(axis, line, a0, a1)]
    f = line + side * t_half
    def strip(z0, z1, th, mat, inset=0.0):
        for (b0, b1, c0, c1) in _cut(a0 + inset, a1 - inset, z0, z1, ops):
            if axis == "x":
                B(b0, f, c0, b1, f + side * th, c1, mat, "FlatWalls")
            else:
                B(f, b0, c0, f + side * th, b1, c1, mat, "FlatWalls")
    strip(0.0, wain_h, 0.12, wain)
    strip(wain_h + 0.35, H - 0.6, 0.06, upper)
    strip(wain_h, wain_h + 0.35, 0.22, rail)
    strip(0.0, 0.6, 0.2, base)
    strip(H - 0.6, H, 0.25, rail)
    # vertical panel battens on the wainscot (cut by openings)
    k = a0 + 2.0
    while k < a1 - 1.0:
        if not any(o[0] - 0.4 < k < o[1] + 0.4 and o[2] < wain_h for o in ops):
            if axis == "x":
                B(k - 0.15, f, 0.6, k + 0.15, f + side * 0.2, wain_h, rail, "FlatWalls")
            else:
                B(f, k - 0.15, 0.6, f + side * 0.2, k + 0.15, wain_h, rail, "FlatWalls")
        k += 2.5


def room_linings(name, upper, wain, rail="White"):
    x0, y0, x1, y1 = ROOMS[name]
    lining("x", y0, +1, x0 + 0.5 * (x0 > 0), x1 - 0.5 * (x1 < W), upper, wain, rail)
    lining("x", y1, -1, x0 + 0.5 * (x0 > 0), x1 - 0.5 * (x1 < W), upper, wain, rail)
    lining("y", x0, +1, y0 + 0.5 * (y0 > 0), y1 - 0.5 * (y1 < D), upper, wain, rail)
    lining("y", x1, -1, y0 + 0.5 * (y0 > 0), y1 - 0.5 * (y1 < D), upper, wain, rail)


def floor_tiles(x0, y0, x1, y1, a, b, size=2.0, diag=False):
    B(x0, y0, -0.3, x1, y1, -0.13, "Grout", "FlatFloor", True, "Floor")
    i = 0
    y = y0
    while y < y1 - 0.01:
        x = x0; j = 0
        while x < x1 - 0.01:
            m = a if (i + j) % 2 == 0 else b
            B(x + 0.06, y + 0.06, -0.13, min(x + size, x1) - 0.06, min(y + size, y1) - 0.06, 0.0, m, "FlatFloor")
            x += size; j += 1
        y += size; i += 1


def floor_planks(x0, y0, x1, y1, seed=0):
    wx0, wy0 = T(x0, y0); wx1, wy1 = T(x1, y1)
    fsd_lib.planks(_sc, min(wx0, wx1), min(wy0, wy1), max(wx0, wx1), max(wy0, wy1), OZ + 0.0, 0.18, "x", "FlatFloor",
                   mats=("FloorOak", "FloorOakB", "FloorOakC"), gap=0.08, width=1.4, collide=False, seed=seed)
    B(x0, y0, -0.4, x1, y1, -0.18, "Slab", "FlatFloor", True, "Floor")


def shell():
    # exterior walls (pink plaster outside like the tower) + interior partitions
    for (axis, line, a0, a1) in (("x", 0, -0.5, W + 0.5), ("x", D, -0.5, W + 0.5), ("y", 0, 0, D), ("y", W, 0, D)):
        wall(axis, line, a0, a1, 1.0, "TowerPink")
    wall("x", 14, 0.5, 15.5); wall("x", 14, 16.5, 43.5)        # bath|kitchen, hall/dressing|living
    wall("y", 16, 0.5, 13.5); wall("y", 16, 14.5, 39.5)        # bath|hall, kitchen|living (mostly open)
    wall("y", 30, 0.5, 13.5)                                   # hall|dressing
    wall("y", 44, 0.5, 39.5)                                   # bedroom
    # floors
    floor_tiles(0.5, 0.5, 15.5, 13.5, "TileT", "TileW", 1.75)                  # bath
    floor_tiles(16.5, 0.5, 29.5, 13.5, "TileY", "TileW", 1.75)                 # hall
    floor_tiles(0.5, 14.5, 16.0, 39.5, "TileP", "TileW", 2.0)                  # kitchen
    floor_planks(16.0, 14.5, 43.5, 39.5, 1)                                    # living
    floor_planks(44.5, 0.5, 63.5, 39.5, 2)                                     # bedroom
    floor_planks(30.5, 0.5, 43.5, 13.5, 3)                                     # dressing
    for (x0, y0, x1, y1, ch) in ((16.5, 13.5, 29.5, 14.5, "arch"), (15.5, 6, 16.5, 11, "d"), (29.5, 3, 30.5, 9, "d"),
                                 (43.5, 9.5, 44.5, 13.5, "d"), (43.5, 22, 44.5, 29, "d"), (19, 13.5, 28, 14.5, "a")):
        B(x0, y0, -0.15, x1, y1, 0.02, "WoodLight", "FlatFloor")             # thresholds
    # ceilings (hidden in the plan shot) with a cove strip
    for name, (x0, y0, x1, y1) in ROOMS.items():
        B(x0 - 0.5, y0 - 0.5, H, x1 + 0.5, y1 + 0.5, H + 0.6, "Ceiling", "FlatCeil")
    B(-0.5, -0.5, H + 0.6, W + 0.5, D + 0.5, H + 1.4, "TowerPink", "FlatCeil")
    # room paint
    room_linings("Hall", "WallButter", "WainYellow")
    room_linings("Living", "WallPink", "WainPink")
    room_linings("Kitchen", "WallMint", "WainTeal")
    room_linings("Bath", "WallSky", "WainTeal")
    room_linings("Dressing", "WallLilac", "WainLilac")
    room_linings("Bedroom", "WallPeach", "WainPink")
    # opening trims (door casings, window frames, glass)
    for (axis, line, a0, a1, z0, z1, kind) in OPEN:
        trim(axis, line, a0, a1, z0, z1, kind)


def trim(axis, line, a0, a1, z0, z1, kind):
    t = 0.8
    def bx(u0, u1, v0, v1, z_0, z_1, mat, grp="FlatWalls"):
        if axis == "x": B(u0, line + v0, z_0, u1, line + v1, z_1, mat, grp)
        else: B(line + v0, u0, z_0, line + v1, u1, z_1, mat, grp)
    if kind == "open":
        bx(a0 - 0.05, a1 + 0.05, -0.6, 0.6, z1 - 0.07, z1 + 0.6, "WoodLight")
        return
    casing = "White"
    if kind in ("door", "arch"):
        for (u0, u1) in ((a0 - 0.45, a0 + 0.07), (a1 - 0.07, a1 + 0.45)):
            bx(u0, u1, -t, t, 0, z1, casing)
        bx(a0 - 0.55, a1 + 0.55, -t - 0.05, t + 0.05, z1 - 0.07, z1 + 0.5, casing)
        if kind == "arch":   # scalloped arch top
            n = 7
            for i in range(n):
                u = a0 + (i + 0.5) * (a1 - a0) / n
                hh = 0.9 * math.sin(math.pi * (i + 0.5) / n) ** 0.5
                bx(u - (a1 - a0) / n / 2, u + (a1 - a0) / n / 2, -0.5, 0.5, z1 - 1.3 + hh, z1, "WallPink")
        return
    if kind in ("window", "frost", "glassdoor"):
        glass = "Frost" if kind == "frost" else "Glass"
        bx(a0, a1, -0.12, 0.12, z0, z1, glass, "Glass")
        bx(a0 - 0.4, a0 + 0.07, -t, t, z0 + 0.07, z1 - 0.07, "White")
        bx(a1 - 0.07, a1 + 0.4, -t, t, z0 + 0.07, z1 - 0.07, "White")
        bx(a0 - 0.5, a1 + 0.5, -t - 0.05, t + 0.05, z1 - 0.07, z1 + 0.45, "White")
        if kind != "glassdoor":
            bx(a0 - 0.65, a1 + 0.65, -1.0, 1.0, z0 - 0.45, z0 + 0.07, "White")       # sill
        else:
            bx(a0 - 0.5, a1 + 0.5, -t - 0.05, t + 0.05, -0.05, 0.25, "White")
            bx(a0 - 0.4, a0 + 0.07, -t, t, 0.25, z1 - 0.07, "White"); bx(a1 - 0.07, a1 + 0.4, -t, t, 0.25, z1 - 0.07, "White")
        # mullions
        n = max(1, int(round((a1 - a0) / 3.2)))
        for i in range(1, n):
            u = a0 + i * (a1 - a0) / n
            bx(u - 0.12, u + 0.12, -0.2, 0.2, z0, z1, "White")
        if kind != "glassdoor" and z1 - z0 > 4:
            bx(a0, a1, -0.2, 0.2, z0 + (z1 - z0) * 0.68, z0 + (z1 - z0) * 0.68 + 0.22, "White")


# ---------------------------------------------------------------- furniture kit
def rug(x0, y0, x1, y1, mats, border="White", stripes_axis="x"):
    B(x0, y0, 0.0, x1, y1, 0.08, border, "FlatProps")
    n = len(mats)
    if stripes_axis == "x":
        s = (y1 - y0 - 0.8) / n
        for i, m in enumerate(mats):
            B(x0 + 0.4, y0 + 0.4 + i * s, 0.08, x1 - 0.4, y0 + 0.4 + (i + 1) * s, 0.12, m, "FlatProps")
    else:
        s = (x1 - x0 - 0.8) / n
        for i, m in enumerate(mats):
            B(x0 + 0.4 + i * s, y0 + 0.4, 0.08, x0 + 0.4 + (i + 1) * s, y1 - 0.4, 0.12, m, "FlatProps")


def round_rug(cx, cy, r, mats):
    for i, m in enumerate(mats):
        Cy(cx, cy, 0.0 + i * 0.03, 0.06 + i * 0.03, r * (1 - i / (len(mats) + 0.5)), m, "FlatProps", 20)


def heart_px(cx, cy, z, s, mat, axis, face_off, group="FlatProps", depth=0.2, rows=None):
    """Pixel heart on a vertical plane. axis 'x': plane along x at y=cy; 'y': plane along y at x=cx."""
    HEART = rows or ["0110110", "1111111", "1111111", "0111110", "0011100", "0001000"]
    for r, row in enumerate(HEART):
        for c, ch in enumerate(row):
            if ch != "1": continue
            u = (c - 3.5) * s
            zz = z - r * s
            if axis == "x":
                B(cx + u, cy + face_off, zz - s, cx + u + s, cy + face_off + depth, zz, mat, group)
            else:
                B(cx + face_off, cy + u, zz - s, cx + face_off + depth, cy + u + s, zz, mat, group)


def heart_flat(cx, cy, z, s, mat, group="FlatProps", th=0.1):
    HEART = ["0110110", "1111111", "1111111", "0111110", "0011100", "0001000"]
    for r, row in enumerate(HEART):
        for c, ch in enumerate(row):
            if ch == "1":
                B(cx + (c - 3.5) * s, cy + (2.5 - r) * s, z, cx + (c - 2.5) * s, cy + (3.5 - r) * s, z + th, mat, group)


def plant(x, y, s=1.0, pot="Coral", leaf=("Leaf", "LeafB", "Green")):
    B(x - 0.9 * s, y - 0.9 * s, 0, x + 0.9 * s, y + 0.9 * s, 1.6 * s, pot)
    B(x - 1.0 * s, y - 1.0 * s, 1.4 * s, x + 1.0 * s, y + 1.0 * s, 1.7 * s, "White")
    B(x - 0.8 * s, y - 0.8 * s, 1.7 * s, x + 0.8 * s, y + 0.8 * s, 1.8 * s, "DirtDark")
    for (dx, dy, dz, r) in ((0, 0, 2.6, 1.0), (0.6, 0.3, 3.6, 0.8), (-0.5, -0.4, 3.3, 0.75), (0.1, -0.2, 4.4, 0.6), (-0.3, 0.5, 2.3, 0.7)):
        m = R.choice(leaf)
        B(x + (dx - r) * s, y + (dy - r) * s, (dz - r) * s, x + (dx + r) * s, y + (dy + r) * s, (dz + r) * s, m)


def flowers_vase(x, y, z, vase="Aqua"):
    Cy(x, y, z, z + 1.1, 0.35, vase, seg=10)
    for (dx, dy, c) in ((0, 0, "Pink"), (0.25, 0.1, "Yellow"), (-0.2, 0.2, "Red"), (0.1, -0.25, "Purple"), (-0.15, -0.15, "White")):
        B(x + dx - 0.03, y + dy - 0.03, z + 1.0, x + dx + 0.03, y + dy + 0.03, z + 1.7, "Green")
        B(x + dx - 0.2, y + dy - 0.2, z + 1.6, x + dx + 0.2, y + dy + 0.2, z + 1.95, c)


def books_row(x0, x1, y0, y1, z, axis="x", hmin=0.9, hmax=1.5):
    cols = ["Rose", "Aqua", "Yellow", "Lilac", "Orange", "Teal", "Pink", "Blue", "Lime", "Coral", "White"]
    a = x0 if axis == "x" else y0
    end = x1 if axis == "x" else y1
    while a < end - 0.25:
        w = R.uniform(0.22, 0.45)
        h = R.uniform(hmin, hmax)
        m = R.choice(cols)
        if axis == "x": B(a, y0, z, min(a + w, end), y1, z + h, m)
        else: B(x0, a, z, x1, min(a + w, end), z + h, m)
        a += w + 0.03


def shelf_unit(x0, y0, x1, y1, h, levels, face, wood="White", fill=True):
    """Open shelving; face = direction the open side looks ('+y','-y','+x','-x')."""
    t = 0.25
    B(x0, y0, 0, x0 + (t if face in ("+y", "-y") else x1 - x0), y1, h, wood) if face in ("+y", "-y") else None
    if face in ("+y", "-y"):
        B(x0, y0, 0, x0 + t, y1, h, wood); B(x1 - t, y0, 0, x1, y1, h, wood)
        back = (y0, y0 + 0.15) if face == "+y" else (y1 - 0.15, y1)
        B(x0, back[0], 0, x1, back[1], h, wood)
    else:
        B(x0, y0, 0, x1, y0 + t, h, wood); B(x0, y1 - t, 0, x1, y1, h, wood)
        back = (x0, x0 + 0.15) if face == "+x" else (x1 - 0.15, x1)
        B(back[0], y0, 0, back[1], y1, h, wood)
    for i in range(levels + 1):
        z = 0.3 + i * (h - 0.6) / levels
        B(x0, y0, z, x1, y1, z + 0.18, wood)
        if fill and i < levels:
            if face in ("+y", "-y"):
                books_row(x0 + 0.4, x1 - 0.4, y0 + 0.3, y1 - 0.3, z + 0.18, "x", 0.8, min(1.6, (h - 0.6) / levels - 0.3))
            else:
                books_row(x0 + 0.3, x1 - 0.3, y0 + 0.4, y1 - 0.4, z + 0.18, "y", 0.8, min(1.6, (h - 0.6) / levels - 0.3))


def pendant(x, y, mat="LampPink", shade="Yellow", drop=3.0):
    CUR[0] = "FlatLamps"
    Cy(x, y, H - drop, H, 0.06, "Iron", seg=6)
    Co(x, y, H - drop - 1.0, H - drop + 0.2, 1.2, shade, seg=12)
    Cy(x, y, H - drop - 1.1, H - drop - 0.7, 0.5, mat, seg=10)
    light(x, y, H - drop - 1.6, (1.0, 0.82, 0.7), 1.0)
    CUR[0] = "FlatProps"


def ceiling_lamp(x, y, r=1.6, mat="Lamp", ring="Gold"):
    CUR[0] = "FlatLamps"
    Cy(x, y, H - 0.5, H, r + 0.3, ring, seg=16)
    Cy(x, y, H - 0.8, H - 0.5, r, mat, seg=16)
    light(x, y, H - 1.5, (1.0, 0.88, 0.75), 1.4)
    CUR[0] = "FlatProps"


def chandelier(x, y):
    CUR[0] = "FlatLamps"
    Cy(x, y, H - 2.2, H, 0.08, "Gold", seg=6)
    Cy(x, y, H - 2.6, H - 2.2, 1.6, "Gold", seg=16)
    for i in range(8):
        a = i * math.pi / 4
        px, py = x + 1.8 * math.cos(a), y + 1.8 * math.sin(a)
        Cy(px, py, H - 2.6, H - 2.4, 0.25, "Gold", seg=6)
        Cy(px, py, H - 2.4, H - 1.8, 0.22, "Lamp", seg=8)
        B(px - 0.08, py - 0.08, H - 3.4, px + 0.08, py + 0.08, H - 2.6, "Frost")
    Cy(x, y, H - 3.4, H - 2.6, 0.5, "LampPink", seg=10)
    light(x, y, H - 3.6, (1.0, 0.85, 0.8), 1.8)
    CUR[0] = "FlatProps"


def floor_lamp(x, y, shade="Coral"):
    Cy(x, y, 0, 0.25, 0.8, "Gold", seg=12)
    Cy(x, y, 0.25, 6.0, 0.1, "Gold", seg=6)
    Co(x, y, 5.6, 7.4, 1.1, shade, seg=12)
    Cy(x, y, 5.7, 6.1, 0.45, "Lamp", seg=8)
    light(x, y, 5.2, (1.0, 0.8, 0.6), 0.35)


def table_lamp(x, y, z, shade="Pink", base="Aqua"):
    Cy(x, y, z, z + 0.25, 0.45, "Gold", seg=10)
    Cy(x, y, z + 0.25, z + 1.2, 0.3, base, seg=10)
    Co(x, y, z + 1.1, z + 2.3, 0.85, shade, seg=12)
    Cy(x, y, z + 1.2, z + 1.5, 0.3, "Lamp", seg=8)
    light(x, y, z + 1.0, (1.0, 0.8, 0.6), 0.2)


def picture(axis, line, side, u0, u1, z0, z1, kind="sea"):
    """Framed picture made of boxes, on a wall. side=+1 room is on the +side of the line."""
    f = line + side * 0.62
    def px(a0, a1, b0, b1, d, mat):
        if axis == "x": B(a0, f + side * (d - 0.1), b0, a1, f + side * d, b1, mat)
        else: B(f + side * (d - 0.1), a0, b0, f + side * d, a1, b1, mat)
    px(u0, u1, z0, z1, 0.18, "Gold")
    px(u0 + 0.3, u1 - 0.3, z0 + 0.3, z1 - 0.3, 0.26, "White")
    a0, a1, b0, b1 = u0 + 0.45, u1 - 0.45, z0 + 0.45, z1 - 0.45
    hz = b0 + (b1 - b0) * 0.45
    if kind == "sea":
        px(a0, a1, hz, b1, 0.32, "Sky")
        px(a0, a1, b0, hz, 0.32, "Water")
        px(a0, a1, b0, b0 + (b1 - b0) * 0.12, 0.36, "Sand")
        sx = a0 + (a1 - a0) * 0.62
        px(sx - 0.7, sx + 0.7, hz + (b1 - hz) * 0.55, hz + (b1 - hz) * 0.55 + 1.0, 0.36, "Yellow")
        bx = a0 + (a1 - a0) * 0.3
        px(bx - 0.8, bx + 0.8, hz - 0.2, hz + 0.25, 0.38, "Red")
        px(bx - 0.05, bx + 0.05, hz + 0.25, hz + 1.6, 0.38, "White")
        px(bx + 0.05, bx + 0.8, hz + 0.4, hz + 1.5, 0.38, "White")
    elif kind == "fish":
        px(a0, a1, b0, b1, 0.32, "Aqua")
        cx = (a0 + a1) / 2; cz = (b0 + b1) / 2
        px(cx - 1.4, cx + 0.8, cz - 0.6, cz + 0.6, 0.38, "Orange")
        px(cx + 0.8, cx + 1.6, cz - 0.9, cz + 0.9, 0.38, "Orange")
        px(cx - 1.1, cx - 0.8, cz + 0.1, cz + 0.35, 0.42, "Black")
        for k in range(3):
            px(a0 + 0.4 + k * 0.6, a0 + 0.7 + k * 0.6, cz + 0.8 + k * 0.4, cz + 1.1 + k * 0.4, 0.38, "White")
    elif kind == "heart":
        px(a0, a1, b0, b1, 0.32, "WallPink")
        s = min(a1 - a0, b1 - b0) / 8
        cx = (a0 + a1) / 2; top = (b0 + b1) / 2 + 3 * s
        HEART = ["0110110", "1111111", "1111111", "0111110", "0011100", "0001000"]
        for r, row in enumerate(HEART):
            for c, ch in enumerate(row):
                if ch == "1":
                    px(cx + (c - 3.5) * s, cx + (c - 2.5) * s, top - (r + 1) * s, top - r * s, 0.38, "Rose")
    elif kind == "anchor":
        px(a0, a1, b0, b1, 0.32, "Navy")
        cx = (a0 + a1) / 2
        px(cx - 0.15, cx + 0.15, b0 + 0.6, b1 - 0.8, 0.38, "Gold")
        px(cx - 1.0, cx + 1.0, b1 - 1.5, b1 - 1.2, 0.38, "Gold")
        px(cx - 1.4, cx + 1.4, b0 + 0.5, b0 + 0.8, 0.38, "Gold")
        px(cx - 1.4, cx - 1.1, b0 + 0.5, b0 + 1.5, 0.38, "Gold")
        px(cx + 1.1, cx + 1.4, b0 + 0.5, b0 + 1.5, 0.38, "Gold")
        Cy(0, 0, 0, 0, 0, "Gold") if False else None
    elif kind == "sunset":
        bands = ["Purple", "Rose", "Orange", "Yellow"]
        hh = (b1 - hz) / len(bands)
        for i, m in enumerate(bands):
            px(a0, a1, hz + i * hh, hz + (i + 1) * hh, 0.32, m)
        px(a0, a1, b0, hz, 0.32, "Navy")
        cx = (a0 + a1) / 2
        px(cx - 1.0, cx + 1.0, hz, hz + 1.0, 0.36, "Yellow")
        for i in range(3):
            px(cx - 1.4 + i * 0.4, cx + 1.4 - i * 0.4, hz - 0.4 - i * 0.5, hz - 0.25 - i * 0.5, 0.36, "Orange")


def curtains(axis, line, side, a0, a1, zt, mat="Rose", tie="Gold"):
    f = line + side * 1.1
    if axis == "x":
        B(a0 - 1.2, f - 0.06, zt + 0.5, a1 + 1.2, f + 0.06, zt + 0.7, "Gold")
    else:
        B(f - 0.06, a0 - 1.2, zt + 0.5, f + 0.06, a1 + 1.2, zt + 0.7, "Gold")
    for (u0, u1) in ((a0 - 1.1, a0 + 0.6), (a1 - 0.6, a1 + 1.1)):
        for k in range(4):     # pleats
            uu0 = u0 + k * (u1 - u0) / 4; uu1 = uu0 + (u1 - u0) / 4 - 0.02
            dd = 0.25 if k % 2 else 0.05
            if axis == "x": B(uu0, f + side * dd - 0.12, 0.3, uu1, f + side * dd + 0.12, zt + 0.5, mat)
            else: B(f + side * dd - 0.12, uu0, 0.3, f + side * dd + 0.12, uu1, zt + 0.5, mat)
        if axis == "x": B(u0 - 0.05, f + side * 0.1 - 0.25, 3.6, u1 + 0.05, f + side * 0.1 + 0.25, 4.0, tie)
        else: B(f + side * 0.1 - 0.25, u0 - 0.05, 3.6, f + side * 0.1 + 0.25, u1 + 0.05, 4.0, tie)
    # valance with scallops
    for k in range(int((a1 - a0 + 2.4) / 1.2)):
        u = a0 - 1.2 + k * 1.2
        if axis == "x": B(u, f - 0.1, zt - 0.5 - 0.25 * (k % 2), u + 1.15, f + side * 0.3, zt + 0.5, mat if k % 2 else "White")
        else: B(f - 0.1, u, zt - 0.5 - 0.25 * (k % 2), f + side * 0.3, u + 1.15, zt + 0.5, mat if k % 2 else "White")


def sofa(x0, y0, x1, y1, face, body="SofaCoral", cushion="Pink", pillows=("Yellow", "Aqua", "Lilac", "White")):
    """Box sofa; face = '+y' etc. = direction the sitter looks."""
    B(x0 + 0.3, y0 + 0.3, 0, x1 - 0.3, y1 - 0.3, 0.5, "Gold")              # plinth/legs
    B(x0, y0, 0.5, x1, y1, 1.9, body)
    if face in ("+y", "-y"):
        by = (y0, y0 + 1.4) if face == "+y" else (y1 - 1.4, y1)
        B(x0, by[0], 1.9, x1, by[1], 4.4, body)                            # back
        for xa in ((x0, x0 + 1.2), (x1 - 1.2, x1)):
            B(xa[0], y0, 1.9, xa[1], y1, 3.2, body)                        # arms
            B(xa[0] - 0.05, y0 + 0.2, 3.2, xa[1] + 0.05, y1 - 0.2, 3.45, cushion)
        n = max(2, int((x1 - x0 - 2.4) / 3.2))
        w = (x1 - x0 - 2.4) / n
        sy = (by[1], y1 - 0.1) if face == "+y" else (y0 + 0.1, by[0])
        for i in range(n):
            a = x0 + 1.2 + i * w
            B(a + 0.05, sy[0], 1.9, a + w - 0.05, sy[1], 2.6, cushion)      # seat cushions
            pb = (by[1], by[1] + 0.7) if face == "+y" else (by[0] - 0.7, by[0])
            B(a + 0.2, pb[0], 2.6, a + w - 0.2, pb[1], 4.3, cushion)        # back cushions
        for i, m in enumerate(pillows[:n + 1]):
            a = x0 + 1.6 + i * (x1 - x0 - 3.6) / max(1, len(pillows[:n + 1]) - 1) if len(pillows) > 1 else x0 + 2
            pb = (by[1] + 0.7, by[1] + 1.3) if face == "+y" else (by[0] - 1.3, by[0] - 0.7)
            B(a - 0.7, pb[0], 2.6, a + 0.7, pb[1], 4.0, m)
    else:
        bx = (x0, x0 + 1.4) if face == "+x" else (x1 - 1.4, x1)
        B(bx[0], y0, 1.9, bx[1], y1, 4.4, body)
        for ya in ((y0, y0 + 1.2), (y1 - 1.2, y1)):
            B(x0, ya[0], 1.9, x1, ya[1], 3.2, body)
            B(x0 + 0.2, ya[0] - 0.05, 3.2, x1 - 0.2, ya[1] + 0.05, 3.45, cushion)
        n = max(2, int((y1 - y0 - 2.4) / 3.2))
        w = (y1 - y0 - 2.4) / n
        sx = (bx[1], x1 - 0.1) if face == "+x" else (x0 + 0.1, bx[0])
        for i in range(n):
            a = y0 + 1.2 + i * w
            B(sx[0], a + 0.05, 1.9, sx[1], a + w - 0.05, 2.6, cushion)
            pb = (bx[1], bx[1] + 0.7) if face == "+x" else (bx[0] - 0.7, bx[0])
            B(pb[0], a + 0.2, 2.6, pb[1], a + w - 0.2, 4.3, cushion)


def armchair(x, y, face, body="SofaTeal", cushion="Mint"):
    s = 2.0
    B(x - s, y - s, 0, x + s, y + s, 0.4, "Gold")
    B(x - s, y - s, 0.4, x + s, y + s, 1.8, body)
    back = {"+y": (x - s, y - s, x + s, y - s + 1.0), "-y": (x - s, y + s - 1.0, x + s, y + s),
            "+x": (x - s, y - s, x - s + 1.0, y + s), "-x": (x + s - 1.0, y - s, x + s, y + s)}[face]
    B(back[0], back[1], 1.8, back[2], back[3], 4.6, body)
    if face in ("+y", "-y"):
        for a in (x - s, x + s - 0.9):
            B(a, y - s, 1.8, a + 0.9, y + s, 3.0, body)
        B(x - s + 0.9, y - s + 0.2, 1.8, x + s - 0.9, y + s - 0.2, 2.5, cushion)
    else:
        for a in (y - s, y + s - 0.9):
            B(x - s, a, 1.8, x + s, a + 0.9, 3.0, body)
        B(x - s + 0.2, y - s + 0.9, 1.8, x + s - 0.2, y + s - 0.9, 2.5, cushion)


def chair(x, y, face, seat="Pink", frame="White", heart=True):
    s = 1.0
    for (dx, dy) in ((-0.8, -0.8), (0.8, -0.8), (-0.8, 0.8), (0.8, 0.8)):
        Cy(x + dx, y + dy, 0, 2.2, 0.13, frame, seg=6)
    B(x - s, y - s, 2.2, x + s, y + s, 2.55, frame)
    B(x - s + 0.1, y - s + 0.1, 2.55, x + s - 0.1, y + s - 0.1, 2.85, seat)
    o = {"+y": (0, -1), "-y": (0, 1), "+x": (-1, 0), "-x": (1, 0)}[face]
    if o[1]:
        yy = y + o[1] * 0.85
        B(x - s, yy - 0.15, 2.55, x + s, yy + 0.15, 5.4, frame)
        if heart: heart_px(x + 0.05, yy, 5.0, 0.25, "Rose", "x", -0.2 * o[1] - 0.05, depth=0.12)
    else:
        xx = x + o[0] * 0.85
        B(xx - 0.15, y - s, 2.55, xx + 0.15, y + s, 5.4, frame)
        if heart: heart_px(xx, y + 0.05, 5.0, 0.25, "Rose", "y", -0.2 * o[0] - 0.05, depth=0.12)


def stool(x, y, seat="Aqua"):
    Cy(x, y, 0, 0.15, 0.7, "Chrome")
    Cy(x, y, 0.15, 3.0, 0.12, "Chrome", seg=6)
    Cy(x, y, 1.2, 1.3, 0.55, "Chrome", seg=10)
    Cy(x, y, 3.0, 3.5, 0.8, seat, seg=14)


def cake(x, y, z):
    Cy(x, y, z, z + 0.15, 0.9, "Gold", seg=14)
    Cy(x, y, z + 0.15, z + 0.75, 0.75, "Pink", seg=14)
    Cy(x, y, z + 0.75, z + 1.2, 0.55, "White", seg=14)
    for i in range(6):
        a = i * math.pi / 3
        B(x + 0.6 * math.cos(a) - 0.08, y + 0.6 * math.sin(a) - 0.08, z + 0.75, x + 0.6 * math.cos(a) + 0.08, y + 0.6 * math.sin(a) + 0.08, z + 0.95, "Red")
    B(x - 0.1, y - 0.1, z + 1.2, x + 0.1, y + 0.1, z + 1.4, "Red")


def teaset(x, y, z):
    Cy(x, y, z, z + 0.8, 0.45, "White", seg=12)
    Cy(x, y, z + 0.8, z + 0.95, 0.25, "Rose", seg=8)
    B(x + 0.4, y - 0.08, z + 0.3, x + 0.9, y + 0.08, z + 0.5, "White")
    B(x - 0.75, y - 0.08, z + 0.2, x - 0.4, y + 0.08, z + 0.65, "White")


def cup(x, y, z, c="Pink"):
    Cy(x, y, z, z + 0.06, 0.35, "White", seg=10)
    Cy(x, y, z + 0.06, z + 0.4, 0.2, c, seg=8)


def fruit_bowl(x, y, z):
    Cy(x, y, z, z + 0.35, 0.8, "Aqua", seg=14)
    for (dx, dy, c) in ((0, 0, "Orange"), (0.35, 0.2, "Red"), (-0.3, 0.25, "Lime"), (0.1, -0.35, "Yellow"), (-0.2, -0.2, "Red")):
        B(x + dx - 0.22, y + dy - 0.22, z + 0.3, x + dx + 0.22, y + dy + 0.22, z + 0.74, c)


def plush(x, y, z, c="Plush", s=1.0, face="+y"):
    """Teddy bear from boxes."""
    B(x - 0.6 * s, y - 0.5 * s, z, x + 0.6 * s, y + 0.5 * s, z + 1.2 * s, c)
    B(x - 0.5 * s, y - 0.45 * s, z + 1.2 * s, x + 0.5 * s, y + 0.45 * s, z + 2.0 * s, c)
    for dx in (-0.45, 0.45):
        B(x + dx * s - 0.18 * s, y - 0.15 * s, z + 1.9 * s, x + dx * s + 0.18 * s, y + 0.15 * s, z + 2.3 * s, c)
        B(x + dx * 1.6 * s - 0.2 * s, y - 0.3 * s, z + 0.2 * s, x + dx * 1.6 * s + 0.2 * s, y + 0.3 * s, z + 1.0 * s, c)
    sg = 1 if face == "+y" else -1
    fy = y + sg * 0.45 * s
    B(x - 0.22 * s, fy - 0.05, z + 1.3 * s, x + 0.22 * s, fy + sg * 0.15 * s, z + 1.6 * s, "Cream")
    for dx in (-0.2, 0.2):
        B(x + dx * s - 0.06, fy, z + 1.65 * s, x + dx * s + 0.06, fy + sg * 0.08, z + 1.8 * s, "Black")
    B(x - 0.15 * s, fy, z + 0.9 * s, x + 0.15 * s, fy + sg * 0.1, z + 1.15 * s, "Rose")


# ---------------------------------------------------------------- rooms
def hall():
    x0, y0, x1, y1 = ROOMS["Hall"]
    # exit door leaf (closed, teal with porthole window and gold heart knocker)
    B(20.1, 0.05, 0.02, 25.9, 0.35, 8.5, "WainTeal", "FlatProps", True, "ExitDoor")
    for (a, b) in ((20.6, 22.8), (23.2, 25.4)):
        B(a, 0.35, 0.8, b, 0.45, 3.6, "TealDark"); B(a, 0.35, 4.2, b, 0.45, 6.4, "TealDark")
    Cy(23, 0.42, 6.8, 6.9, 0.1, "Gold") if False else None
    B(22.3, 0.35, 6.6, 23.7, 0.5, 8.0, "Gold"); B(22.5, 0.4, 6.8, 23.5, 0.55, 7.8, "Glass", "Glass")
    B(25.2, 0.35, 3.9, 25.5, 0.75, 4.3, "Gold")
    heart_px(23.0, 0.5, 6.2, 0.15, "Gold", "x", 0.0, depth=0.1, rows=["0110110", "1111111", "0111110", "0011100", "0001000"])
    B(20.5, 0.6, 0.0, 25.5, 3.0, 0.14, "Coral")                                   # door mat
    heart_flat(23.0, 1.8, 0.14, 0.25, "White")
    # shoe bench + mirror (west wall)
    B(16.6, 1.0, 0, 18.6, 5.2, 0.3, "White"); B(16.6, 1.0, 1.6, 18.6, 5.2, 1.85, "White")
    B(16.6, 1.0, 1.85, 18.6, 5.2, 2.3, "WainYellow")
    for k, (c) in enumerate(("Pink", "Aqua", "Red", "Yellow")):
        B(16.9, 1.3 + k * 0.95, 0.3, 18.1, 1.95 + k * 0.95, 0.75, c)               # shoes on the rack
    for k, c in enumerate(("Rose", "Lilac")):
        B(17.0, 1.6 + k * 1.8, 2.3, 18.3, 2.9 + k * 1.8, 2.75, c)                  # cushions
    Cy(16.62 + 0.0, 3.1, 4.0, 4.0, 0.01, "Gold") if False else None
    # round mirror = gold ring of boxes + glass
    for i in range(16):
        a = i * math.pi / 8
        B(16.55, 3.1 + 1.6 * math.cos(a) - 0.25, 6.6 + 1.6 * math.sin(a) - 0.25, 16.8, 3.1 + 1.6 * math.cos(a) + 0.25, 6.6 + 1.6 * math.sin(a) + 0.25, "Gold")
    B(16.55, 2.0, 5.5, 16.68, 4.2, 7.7, "Frost", "Glass")
    # coat hooks (east wall, beside the dressing door)
    B(29.3, 9.6, 6.8, 29.45, 13.4, 7.3, "WainYellow")
    for k, c in enumerate(("Red", "Aqua", "Pink")):
        yy = 10.3 + k * 1.2
        B(28.9, yy - 0.1, 6.9, 29.3, yy + 0.1, 7.1, "Gold")
        B(28.5, yy - 0.5, 3.2, 29.2, yy + 0.5, 6.9, c)                              # coats
        B(28.6, yy - 0.35, 2.6, 29.1, yy + 0.35, 3.2, c)
    B(28.4, 9.9, 7.3, 29.3, 10.9, 7.9, "Yellow")                                    # sun hat
    Cy(28.8, 10.4, 7.3, 7.35, 0.9, "Yellow") if False else None
    # umbrella stand + umbrellas
    Cy(28.4, 1.3, 0, 2.2, 0.65, "Aqua")
    for (dx, c) in ((-0.2, "Rose"), (0.2, "Yellow")):
        Cy(28.4 + dx, 1.3, 2.2, 4.6, 0.12, c, seg=6); Co(28.4 + dx, 1.3, 2.0, 3.5, 0.4, c, seg=8)
    # console with shell bowl + vase, beside the arch
    B(26.4, 12.2, 0, 29.4, 13.4, 3.0, "White"); B(26.3, 12.1, 3.0, 29.5, 13.45, 3.3, "WainYellow")
    Cy(27.2, 12.8, 3.3, 3.6, 0.5, "Aqua")
    for (dx, c) in ((-0.15, "Shell"), (0.2, "Pink")):
        B(27.2 + dx - 0.15, 12.7, 3.6, 27.2 + dx + 0.15, 12.95, 3.75, c)
    flowers_vase(28.6, 12.8, 3.3, "Rose")
    plant(17.6, 12.3, 0.8, "Aqua")
    # yellow-striped round rug + arrival marker area
    round_rug(23, 6.5, 4.2, ["Yellow", "White", "Coral", "White", "Yellow"])
    # porthole decor (fisherman touch)
    for (u, z) in ((19.0, 7.0),):
        for i in range(12):
            a = i * math.pi / 6
            B(u + 1.0 * math.cos(a) - 0.2, 13.4, z + 1.0 * math.sin(a) - 0.2, u + 1.0 * math.cos(a) + 0.2, 13.5, z + 1.0 * math.sin(a) + 0.2, "Gold")
    picture("x", 14, -1, 17.0, 18.6, 9.0, 10.6, "fish") if False else None
    ceiling_lamp(23, 7, 1.4, "Lamp", "Gold")
    anchor("arrival", 23.0, 4.0, 0.0, "N")
    anchor("exit_door", 23.0, 0.2, 4.2, "S")


def living():
    x0, y0, x1, y1 = ROOMS["Living"]
    # TV wall (on the hall/dressing wall, y=14, x 30..43) with teal panels, shelves and decor
    B(30.0, 14.6, 0.6, 43.4, 14.8, 11.4, "WainTeal")
    for k in range(5):
        B(30.6 + k * 2.6, 14.8, 1.0, 32.6 + k * 2.6, 14.9, 11.0, "TealDark")
    B(31.5, 14.6, 0, 41.5, 16.6, 2.2, "White")                                     # TV console
    for k in range(3):
        B(31.8 + k * 3.3, 16.6, 0.3, 34.8 + k * 3.3, 16.7, 1.9, ["Yellow", "Rose", "Aqua"][k])
        B(33.0 + k * 3.3, 16.7, 1.0, 33.6 + k * 3.3, 16.85, 1.2, "Gold")
    B(32.5, 14.9, 3.4, 40.5, 15.3, 8.0, "Screen")                                 # TV
    B(32.8, 15.3, 3.7, 40.2, 15.35, 7.7, "ScreenOn")
    for (dx, dz, c) in ((1.5, 1.0, "Yellow"), (3.6, 2.0, "Lime"), (5.5, 0.8, "Rose")):  # cartoon on the screen
        B(32.8 + dx, 15.35, 3.7 + dz, 33.8 + dx, 15.4, 4.7 + dz, c)
    B(32.8, 15.35, 3.7, 40.2, 15.4, 4.3, "Green")
    for (sx, sz) in ((30.3, 3.8), (30.3, 6.6), (41.6, 3.8), (41.6, 6.6)):          # side shelves
        B(sx, 14.8, sz, sx + 1.6, 16.2, sz + 0.2, "White")
    B(30.6, 15.2, 4.0, 31.2, 15.8, 5.2, "Coral"); B(31.3, 15.3, 4.0, 31.7, 15.7, 4.6, "Yellow")      # shell & vase
    teaset(41.9 + 0.5, 15.5, 4.0)
    plush(30.9, 15.5, 6.8, "Pink", 0.45, "+y")
    B(41.8, 15.0, 6.8, 43.0, 15.9, 7.4, "Lilac"); B(41.8, 15.0, 7.4, 43.0, 15.9, 7.8, "Aqua")
    # sofa (coral) facing the TV, back to the window side
    sofa(29.0, 21.0, 41.0, 25.0, "-y", "SofaCoral", "Pink", ("Yellow", "Aqua", "Lilac", "White"))
    armchair(26.0, 19.5, "+x", "SofaTeal", "Mint")
    # round coffee table with fruit, books, remote
    Cy(35, 18.2, 0, 1.2, 0.35, "Gold", seg=8)
    Cy(35, 18.2, 1.2, 1.55, 2.0, "WainYellow", seg=20)
    fruit_bowl(35.2, 18.2, 1.55)
    B(33.6, 17.4, 1.55, 34.6, 18.6, 1.75, "Rose"); B(33.7, 17.5, 1.75, 34.5, 18.5, 1.9, "Aqua")
    B(36.3, 18.8, 1.55, 36.9, 19.1, 1.65, "Black")
    rug(27.5, 15.6, 42.5, 26.5, ["Pink", "White", "Aqua", "White", "Yellow", "White", "Pink"], "Rose", "y")
    # big aquarium on the bedroom wall (x=44), y 30..39 - colourful fish, castle, plants
    ax0, ax1, ay0, ay1 = 40.2, 43.4, 30.0, 39.4
    B(ax0, ay0, 0, ax1, ay1, 2.8, "White")                                        # cabinet
    for k in range(3):
        B(ax0 - 0.08, ay0 + 0.4 + k * 3.0, 0.4, ax0, ay0 + 3.0 + k * 3.0, 2.4, ["Aqua", "Rose", "Yellow"][k])
    B(ax0 + 0.1, ay0 + 0.1, 2.8, ax1 - 0.1, ay1 - 0.1, 3.4, "Sand")
    B(ax0 + 0.15, ay0 + 0.15, 3.4, ax1 - 0.15, ay1 - 0.15, 7.6, "WaterTank", "Glass")
    for (yy, c, h) in ((31, "Lime", 2.6), (32.3, "Green", 3.6), (37.8, "Lime", 3.0), (38.6, "Green", 2.2), (34.7, "LeafB", 1.8)):
        B(41.2, yy - 0.2, 3.4, 41.6, yy + 0.2, 3.4 + h, c)                      # weed
    B(41.4, 35.2, 3.4, 42.8, 36.8, 5.0, "TileP")                                 # castle
    for (yy) in (35.2, 36.4):
        B(41.4, yy, 5.0, 41.8, yy + 0.4, 5.4, "TileP"); B(42.4, yy, 5.0, 42.8, yy + 0.4, 5.4, "TileP")
    B(41.35, 35.8, 3.4, 41.4, 36.2, 4.2, "Black")
    for (yy, zz, c) in ((31.8, 6.2, "Orange"), (33.5, 5.0, "Yellow"), (35.0, 6.6, "Rose"), (36.8, 5.8, "Aqua"), (38.2, 6.8, "Orange"), (33.0, 7.0, "Purple"), (37.5, 4.2, "Red")):
        B(41.3, yy - 0.5, zz - 0.25, 41.9, yy + 0.4, zz + 0.25, c)
        B(41.4, yy + 0.4, zz - 0.4, 41.8, yy + 0.8, zz + 0.4, c)
        B(41.25, yy - 0.4, zz, 41.3, yy - 0.25, zz + 0.12, "Black")
    for k in range(6):
        B(41.6, 34.0 + k * 0.1, 4.0 + k * 0.6, 41.8, 34.2 + k * 0.1, 4.2 + k * 0.6, "Foam")   # bubbles
    B(ax0, ay0, 7.6, ax1, ay1, 8.2, "White")
    B(ax0 + 0.6, ay0 + 0.5, 7.5, ax1 - 0.6, ay1 - 0.5, 7.6, "LampTeal")
    light(41.8, 34.7, 6.0, (0.6, 0.95, 1.0), 0.35)
    # tea table by the panoramic window = MistressDesk contract (round table, two heart chairs)
    tx, ty = 24.5, 32.5
    round_rug(tx, ty, 5.2, ["Rose", "White", "Pink", "White"])
    Cy(tx, ty, 0, 0.3, 1.2, "Gold", seg=12)
    Cy(tx, ty, 0.3, 3.4, 0.3, "Gold", seg=8)
    Cy(tx, ty, 3.4, 3.75, 2.6, "Marble", seg=24)
    Cy(tx, ty, 3.32, 3.4, 2.7, "Gold", seg=24)
    cake(tx - 0.2, ty + 0.3, 3.75)
    teaset(tx + 1.4, ty - 0.6, 3.75)
    cup(tx - 0.3, ty + 1.8, 3.75, "Pink"); cup(tx + 0.2, ty - 1.9, 3.75, "Aqua")
    flowers_vase(tx - 1.5, ty - 0.9, 3.75, "Aqua")
    chair(tx, ty + 3.6, "-y", "Rose", "White")             # mistress (back to the window, faces the guest)
    chair(tx, ty - 3.6, "+y", "Aqua", "White")             # guest
    anchor("table_top", tx, ty, 3.75, "N")
    anchor("mistress_seat", tx, ty + 3.6, 2.85, "S")
    anchor("guest_seat", tx, ty - 3.6, 2.85, "N")
    # window side: curtains + window bench plants
    curtains("x", 40, -1, 17.4, 32.0, 10.6, "Rose")
    plant(18.4, 38.0, 1.0, "Yellow")
    plant(31.4, 38.4, 0.85, "Aqua")
    # bookshelf + floor lamp near the kitchen opening/corner
    shelf_unit(17.0, 14.8, 23.0, 16.8, 8.5, 4, "+y", "White")
    plush(18.4, 15.8, 6.75, "Plush", 0.42, "+y")
    floor_lamp(42.4, 27.0, "Yellow")
    floor_lamp(18.0, 27.0, "Coral")
    # wall art
    picture("y", 44, -1, 30.6, 33.6, 8.8, 11.0, "heart") if False else None
    picture("x", 14, 1, 24.2, 27.4, 5.0, 8.4, "sea") if False else None
    picture("y", 16, 1, 17.0, 17.0, 0, 0) if False else None
    chandelier(30.0, 27.0)
    pendant(24.5, 32.5, "LampPink", "Yellow", 3.2)


def kitchen():
    x0, y0, x1, y1 = ROOMS["Kitchen"]
    # L counter: west wall (y 18..38) + north wall (x 0.5..14)
    def counter(cx0, cy0, cx1, cy1, door_axis):
        B(cx0, cy0, 0, cx1, cy1, 0.45, "TealDark")                                  # toe kick
        B(cx0, cy0, 0.45, cx1, cy1, 3.4, "WainYellow")                              # cabinets
        B(cx0 - 0.05, cy0 - 0.05, 3.4, cx1 + 0.05, cy1 + 0.05, 3.8, "Marble")      # top
        if door_axis == "y":
            a = cy0
            while a < cy1 - 1.0:
                b = min(a + 2.4, cy1)
                B(cx1, a + 0.1, 0.7, cx1 + 0.08, b - 0.1, 3.1, "Yellow")
                B(cx1 + 0.08, a + 0.9, 2.5, cx1 + 0.25, b - 0.9, 2.7, "Chrome")
                a = b
        else:
            a = cx0
            while a < cx1 - 1.0:
                b = min(a + 2.4, cx1)
                B(a + 0.1, cy0 - 0.08, 0.7, b - 0.1, cy0, 3.1, "Yellow")
                B(a + 0.9, cy0 - 0.25, 2.5, b - 0.9, cy0 - 0.08, 2.7, "Chrome")
                a = b
    counter(0.6, 18.0, 3.2, 37.2, "y")
    counter(0.6, 37.2, 14.0, 39.4, "x")
    # tile backsplash (pink/white checker) above the counters
    for i in range(10):
        for j in range(3):
            yy = 18.0 + i * 1.9; zz = 3.8 + j * 1.0
            B(0.62, yy + 0.04, zz + 0.04, 0.75, yy + 1.86, zz + 0.96, "TileP" if (i + j) % 2 else "TileW", "FlatWalls")
    for i in range(7):
        for j in range(3):
            xx = 0.6 + i * 1.9; zz = 3.8 + j * 1.0
            if 3 < xx < 13 and zz > 4.0: continue                                   # window
            B(xx + 0.04, 39.25, zz + 0.04, xx + 1.86, 39.38, zz + 0.96, "TileT" if (i + j) % 2 else "TileW", "FlatWalls")
    # sink under the west window
    B(0.9, 24.0, 3.5, 2.8, 28.0, 3.82, "Chrome"); B(1.1, 24.2, 3.0, 2.6, 27.8, 3.83, "Chrome")
    Cy(0.95, 26.0, 3.8, 5.2, 0.12, "Chrome", seg=6); B(0.9, 25.9, 5.0, 1.9, 26.1, 5.2, "Chrome")
    flowers_vase(1.6, 30.0, 3.8, "Yellow")
    for k, c in enumerate(("Aqua", "Rose", "Yellow")):
        Cy(1.4, 21.0 + k * 0.8, 3.8, 4.6 + k * 0.15, 0.3, c, seg=8)               # jars
    # stove + hood on the north counter
    B(6.0, 37.4, 3.8, 9.6, 39.2, 3.9, "Black")
    for (bx, by) in ((6.8, 37.9), (8.8, 37.9), (6.8, 38.7), (8.8, 38.7)):
        Cy(bx, by, 3.9, 3.95, 0.35, "Red", seg=10)
    B(6.0, 37.15, 0.7, 9.6, 37.25, 3.1, "Chrome"); B(6.3, 37.1, 2.7, 9.3, 37.15, 2.9, "Black")
    P([(5.6, 39.4), (10.0, 39.4), (9.4, 37.6), (6.2, 37.6)], 8.2, 9.0, "Aqua")
    B(6.6, 38.4, 9.0, 9.0, 39.4, 11.4, "Aqua")
    Cy(7.8, 38.2, 3.95, 4.8, 0.6, "Rose", seg=12)                                 # pot
    B(8.4, 38.1, 4.5, 9.2, 38.3, 4.6, "Rose")
    # wall shelf with cups + hanging utensils
    B(10.5, 38.6, 6.2, 13.8, 39.4, 6.4, "White")
    for k, c in enumerate(("Pink", "Aqua", "Yellow", "Lilac")):
        cup(11.0 + k * 0.8, 39.0, 6.4, c)
    B(0.6, 31.0, 7.2, 1.4, 36.0, 7.4, "White")
    for k in range(4):
        Cy(1.0, 31.6 + k * 1.2, 7.4, 8.2 + (k % 2) * 0.4, 0.3, ["Rose", "Yellow", "Aqua", "Lime"][k], seg=8)
    B(0.62, 18.6, 7.6, 0.8, 22.6, 7.75, "Gold")
    for k in range(4):
        B(0.8, 18.9 + k * 1.0, 5.6, 0.95, 19.2 + k * 1.0, 7.6, "Chrome")
    # retro fridge (mint) in the SW corner
    B(0.6, 14.6, 0, 4.4, 17.6, 9.0, "Mint")
    B(4.4, 14.8, 0.4, 4.5, 17.4, 5.4, "Mint"); B(4.4, 14.8, 5.6, 4.5, 17.4, 8.8, "Mint")
    B(4.5, 17.0, 6.0, 4.75, 17.2, 7.8, "Chrome"); B(4.5, 17.0, 2.4, 4.75, 17.2, 4.6, "Chrome")
    for (yy, zz, c) in ((15.4, 7.2, "Yellow"), (16.2, 6.4, "Rose"), (15.2, 3.4, "Lime")):
        B(4.5, yy, zz, 4.62, yy + 0.6, zz + 0.6, c)                                 # magnets
    heart_px(4.55, 16.1, 8.6, 0.12, "Red", "y", 0.0, depth=0.08)
    # island with 3 bar stools facing the living room
    B(6.5, 23.0, 0, 11.0, 33.0, 0.45, "TealDark")
    B(6.5, 23.0, 0.45, 11.0, 33.0, 3.4, "WainTeal")
    B(6.3, 22.8, 3.4, 12.6, 33.2, 3.8, "Marble")
    for k in range(4):
        B(6.5 + 0.0, 23.4 + k * 2.4, 0.8, 6.45, 25.4 + k * 2.4, 3.0, "Mint")
    for yy in (24.8, 28.0, 31.2):
        stool(13.6, yy, ["Aqua", "Rose", "Yellow"][int((yy - 24.8) / 3.2)])
    fruit_bowl(8.6, 26.0, 3.8)
    cake(9.0, 30.4, 3.8)
    B(7.0, 27.6, 3.8, 8.6, 28.8, 3.9, "WoodLight")                                 # cutting board
    for (dx, c) in ((0.3, "Orange"), (0.9, "Red")):
        B(7.0 + dx, 28.0, 3.9, 7.4 + dx, 28.4, 4.2, c)
    # pantry shelf (south wall, x 5..14) with jars and cookbooks
    shelf_unit(5.2, 14.6, 10.4, 16.2, 7.6, 3, "+y", "White")
    B(11.0, 14.6, 0, 15.4, 16.6, 3.4, "WainYellow"); B(10.9, 14.5, 3.4, 15.5, 16.7, 3.8, "Marble")
    Cy(12.0, 15.6, 3.8, 4.8, 0.55, "Rose", seg=10); Cy(13.5, 15.6, 3.8, 5.2, 0.45, "White", seg=10)
    B(14.2, 15.0, 3.8, 15.2, 16.2, 4.6, "Chrome")                                 # toaster
    # rug runner + pendant lamps over the island
    rug(3.6, 19.0, 6.0, 36.4, ["Yellow", "Aqua", "Yellow"], "Rose", "y")
    for yy in (25.0, 28.0, 31.0):
        pendant(8.8, yy, "Lamp", ["Rose", "Aqua", "Yellow"][int((yy - 25) / 3)], 3.6)
    curtains("x", 40, -1, 3.0, 13.0, 9.6, "Aqua")
    ceiling_lamp(8.0, 20.0, 1.2)


def bath():
    x0, y0, x1, y1 = ROOMS["Bath"]
    # wall tiles up to 6 studs (teal/white checker) on the tub wall
    for i in range(8):
        for j in range(4):
            xx = 2.0 + i * 1.6; zz = 0.6 + j * 1.4
            B(xx + 0.04, 0.62, zz + 0.04, xx + 1.56, 0.74, zz + 1.36, "TileT" if (i + j) % 2 else "TileW", "FlatWalls")
    # clawfoot bathtub (pink) along the south wall
    tx0, tx1, ty0, ty1 = 3.0, 12.0, 0.9, 5.4
    for (fx, fy) in ((tx0 + 0.6, ty0 + 0.5), (tx1 - 0.6, ty0 + 0.5), (tx0 + 0.6, ty1 - 0.5), (tx1 - 0.6, ty1 - 0.5)):
        B(fx - 0.3, fy - 0.3, 0, fx + 0.3, fy + 0.3, 0.7, "Gold")
    B(tx0, ty0, 0.7, tx1, ty1, 1.3, "TileP")
    for (a, b, c, d) in ((tx0, ty0, tx1, ty0 + 0.6), (tx0, ty1 - 0.6, tx1, ty1), (tx0, ty0 + 0.6, tx0 + 0.6, ty1 - 0.6), (tx1 - 0.6, ty0 + 0.6, tx1, ty1 - 0.6)):
        B(a, b, 1.3, c, d, 3.2, "TileP")
    for (a, b, c, d) in ((tx0 - 0.2, ty0 - 0.2, tx1 + 0.2, ty0 + 0.5), (tx0 - 0.2, ty1 - 0.5, tx1 + 0.2, ty1 + 0.2), (tx0 - 0.2, ty0 + 0.5, tx0 + 0.5, ty1 - 0.5), (tx1 - 0.5, ty0 + 0.5, tx1 + 0.2, ty1 - 0.5)):
        B(a, b, 3.2, c, d, 3.5, "White")
    B(tx0 + 0.6, ty0 + 0.6, 1.3, tx1 - 0.6, ty1 - 0.6, 2.7, "Aqua")
    B(tx0 + 0.6, ty0 + 0.6, 2.7, tx1 - 0.6, ty1 - 0.6, 2.9, "Water")
    for (dx, dy) in ((1.5, 1.0), (2.5, 2.4), (4.0, 1.5), (5.2, 2.6), (6.4, 1.2), (3.4, 3.0)):       # foam
        B(tx0 + dx - 0.45, ty0 + dy - 0.45, 2.75, tx0 + dx + 0.45, ty0 + dy + 0.45, 3.4, "Foam")
    # rubber duck
    B(7.2, 3.0, 2.85, 8.0, 3.7, 3.45, "Yellow"); B(7.0, 3.1, 3.45, 7.5, 3.6, 3.9, "Yellow"); B(6.7, 3.25, 3.5, 7.0, 3.45, 3.65, "Orange")
    Cy(11.4, 1.4, 3.5, 5.2, 0.12, "Gold", seg=6); B(11.0, 1.3, 5.0, 11.5, 1.5, 5.2, "Gold")
    # shower corner (NW) with glass, rain head, mat
    B(0.6, 9.4, 0, 5.4, 13.4, 0.2, "TileW")
    B(5.3, 9.4, 0.2, 5.45, 13.4, 8.4, "Glass", "Glass")
    B(0.6, 9.3, 0.2, 3.2, 9.45, 8.4, "Glass", "Glass")
    B(5.25, 9.3, 0.2, 5.5, 9.5, 8.6, "Chrome")
    Cy(1.2, 11.4, 6.0, 9.6, 0.1, "Chrome", seg=6); B(1.2, 11.0, 9.4, 2.6, 11.8, 9.6, "Chrome"); Cy(2.6, 11.4, 9.0, 9.4, 0.6, "Chrome", seg=10)
    B(0.62, 10.0, 4.0, 0.9, 13.0, 4.2, "White")
    for k, c in enumerate(("Rose", "Aqua", "Yellow")):
        Cy(0.9, 10.6 + k * 0.9, 4.2, 5.0, 0.25, c, seg=8)
    # toilet (west wall)
    B(0.6, 6.0, 0, 1.5, 8.4, 4.2, "White")                                          # cistern
    B(1.5, 6.4, 0, 3.4, 8.0, 1.6, "White"); B(1.4, 6.3, 1.6, 3.6, 8.1, 1.85, "Pink")
    B(0.7, 6.3, 4.2, 1.6, 8.1, 4.35, "Pink"); B(1.0, 6.9, 4.35, 1.4, 7.5, 4.6, "Gold")
    # double vanity (north wall) with shell mirror
    B(6.0, 11.8, 0.45, 13.5, 13.5, 3.2, "WainTeal"); B(6.0, 11.8, 0, 13.5, 13.5, 0.45, "TealDark")
    B(5.9, 11.6, 3.2, 13.6, 13.55, 3.55, "Marble")
    for xx in (7.9, 11.6):
        Cy(xx, 12.6, 3.3, 3.58, 0.9, "White", seg=14)
        Cy(xx, 13.2, 3.55, 4.5, 0.1, "Gold", seg=6); B(xx - 0.1, 12.6, 4.3, xx + 0.1, 13.2, 4.5, "Gold")
        B(xx - 1.0, 11.75, 0.8, xx + 1.0, 11.8, 2.9, "Mint"); B(xx - 0.3, 11.65, 2.3, xx + 0.3, 11.75, 2.5, "Gold")
    # scallop shell mirror: fan of gold-framed slats
    cx, cz = 9.75, 7.5
    for i in range(7):
        a = math.pi * (i + 0.5) / 7
        px, pz = cx + 2.6 * math.cos(a), cz + 2.6 * math.sin(a)
        B(px - 0.55, 13.35, cz, px + 0.55, 13.45, pz + 0.3, "Gold")
        B(px - 0.45, 13.3, cz + 0.1, px + 0.45, 13.35, pz, "Frost", "Glass")
    B(cx - 3.0, 13.3, cz - 0.4, cx + 3.0, 13.45, cz, "Gold")
    for k in range(5):                                                              # bulbs above the mirror
        B(6.8 + k * 1.5, 13.0, 10.6, 7.2 + k * 1.5, 13.4, 11.0, "Lamp")
    B(12.5, 12.4, 3.55, 13.1, 13.0, 4.4, "Pink"); B(6.6, 12.5, 3.55, 7.1, 13.0, 4.1, "Aqua")
    # towel ladder + towels (east wall, beside the door)
    for yy in (2.0, 4.6):
        B(15.0, yy, 0, 15.3, yy + 0.25, 7.0, "Gold")
    for k, c in enumerate(("Rose", "Aqua", "Yellow")):
        B(14.8, 2.0, 1.6 + k * 1.8, 15.4, 4.85, 1.85 + k * 1.8, "Gold")
        B(14.7, 2.3, 0.6 + k * 1.8, 15.5, 4.5, 2.1 + k * 1.8, c)
    # bath mats + plant + laundry basket
    for (xx, yy, c) in ((6.2, 6.2, "Rose"), (9.75, 9.4, "Aqua")):
        B(xx - 1.7, yy - 0.9, 0, xx + 1.7, yy + 0.9, 0.14, c)
    heart_flat(6.2, 6.2, 0.14, 0.2, "White")
    plant(13.8, 7.8, 0.65, "Rose")
    Cy(13.8, 10.4, 0, 2.0, 0.8, "WoodLight", seg=10); B(13.3, 10.0, 2.0, 14.4, 10.9, 2.4, "Aqua")
    ceiling_lamp(8.0, 7.0, 1.2, "Lamp", "White")


def dressing():
    x0, y0, x1, y1 = ROOMS["Dressing"]
    # long clothes rail along the south wall with colourful dresses
    B(30.8, 0.6, 0, 43.2, 3.0, 0.4, "White")
    for xx in (31.0, 43.0):
        B(xx - 0.12, 1.6, 0.4, xx + 0.12, 1.9, 8.2, "Gold")
    B(31.0, 1.65, 7.6, 43.0, 1.85, 7.8, "Gold")
    cols = ["Rose", "Aqua", "Yellow", "Lilac", "Coral", "Lime", "Pink", "Teal", "White", "Orange", "Purple", "Sky"]
    xx = 31.5; k = 0
    while xx < 42.4:
        c = cols[k % len(cols)]
        B(xx, 1.2, 4.0, xx + 0.55, 2.3, 7.4, c)                                     # bodice
        B(xx - 0.15, 0.9, 2.6 + (k % 3) * 0.4, xx + 0.7, 2.6, 4.0, c)              # skirt
        B(xx + 0.2, 1.7, 7.4, xx + 0.35, 1.8, 7.8, "Chrome")                      # hanger
        xx += 0.9; k += 1
    for k in range(5):
        B(31.5 + k * 2.3, 0.8, 0.4, 32.9 + k * 2.3, 1.8, 0.8, ["Rose", "Gold", "Aqua", "Yellow", "Red"][k])   # shoes
    B(30.8, 0.6, 8.6, 43.2, 2.8, 8.8, "White")
    for k in range(4):
        B(31.4 + k * 3.0, 0.9, 8.8, 33.4 + k * 3.0, 2.5, 10.2, ["Pink", "Aqua", "Lilac", "Yellow"][k])        # hat boxes
        B(31.3 + k * 3.0, 0.8, 9.9, 33.5 + k * 3.0, 2.6, 10.3, "White")
    # shoe tower (west, beside the hall door)
    shelf_unit(30.6, 9.6, 32.4, 13.4, 7.0, 5, "+x", "White", False)
    for lv in range(5):
        z = 0.48 + lv * 6.4 / 5
        for k in range(2):
            B(31.0, 9.9 + k * 1.7, z, 32.1, 11.3 + k * 1.7, z + 0.55, R.choice(cols))
    # vanity with Hollywood-bulb mirror (north wall)
    B(33.5, 12.0, 0, 40.5, 13.5, 3.2, "White"); B(33.4, 11.9, 3.2, 40.6, 13.55, 3.5, "WainLilac")
    for k in range(3):
        B(34.0 + k * 2.2, 11.95, 1.2, 35.8 + k * 2.2, 12.0, 2.8, "Lilac")
        B(34.7 + k * 2.2, 11.85, 2.3, 35.1 + k * 2.2, 11.95, 2.5, "Gold")
    B(34.4, 13.3, 4.0, 39.6, 13.45, 9.6, "Gold"); B(34.8, 13.25, 4.4, 39.2, 13.3, 9.2, "Frost", "Glass")
    for k in range(5):
        B(34.6 + k * 1.15, 13.0, 9.65, 35.0 + k * 1.15, 13.3, 10.05, "Lamp")
    for k in range(4):
        for xx in (34.15, 39.85):
            B(xx - 0.2, 13.0, 4.6 + k * 1.3, xx + 0.2, 13.3, 5.0 + k * 1.3, "Lamp")
    light(37.0, 12.0, 8.0, (1.0, 0.9, 0.8), 0.3)
    for (dx, c, h) in ((0.0, "Rose", 0.9), (0.6, "Aqua", 0.7), (1.1, "Gold", 0.5), (1.6, "Pink", 1.1)):
        Cy(35.0 + dx, 12.8, 3.5, 3.5 + h, 0.2, c, seg=8)                         # perfume
    B(38.0, 12.4, 3.5, 39.4, 13.2, 3.9, "Lilac"); B(38.1, 12.5, 3.9, 39.3, 13.1, 4.0, "Gold")
    Cy(37.0, 10.2, 0, 2.4, 1.0, "Rose", seg=14); Cy(37.0, 10.2, 2.4, 2.9, 1.05, "Pink", seg=14)   # pouf
    # full-length mirror (east wall)
    B(43.3, 2.6, 0.6, 43.5, 7.0, 9.4, "Gold"); B(43.25, 3.0, 1.0, 43.3, 6.6, 9.0, "Frost", "Glass")
    round_rug(37.2, 7.0, 3.6, ["Lilac", "White", "Pink"])
    chandelier(37.0, 7.0)


def bedroom():
    x0, y0, x1, y1 = ROOMS["Bedroom"]
    # bed: headboard on the south wall, big heart, coral duvet, lots of pillows
    bx0, bx1, by0, by1 = 49.0, 59.0, 0.6, 12.0
    B(bx0, by0, 0, bx1, by1, 0.5, "Gold")
    B(bx0, by0, 0.5, bx1, by1, 2.2, "White")
    B(bx0 + 0.1, by0 + 0.6, 2.2, bx1 - 0.1, by1 - 0.1, 3.2, "Cream")           # mattress
    B(bx0 - 0.15, by0 + 3.6, 2.6, bx1 + 0.15, by1 + 0.1, 3.6, "SofaCoral")     # duvet
    B(bx0 - 0.2, by1 - 3.0, 2.6, bx1 + 0.2, by1 + 0.15, 3.75, "Pink")        # fold/bed runner
    for k in range(6):
        B(bx0 + 0.6 + k * 1.5, by1 - 2.6, 3.75, bx0 + 1.1 + k * 1.5, by1 - 0.4, 3.8, "White")
    B(bx0 - 0.4, 0.55, 0, bx1 + 0.4, 1.3, 8.0, "Rose")                          # padded headboard
    for i in range(5):
        for j in range(3):
            B(bx0 + 0.4 + i * 2.0, 1.3, 3.2 + j * 1.5, bx0 + 1.8 + i * 2.0, 1.45, 4.5 + j * 1.5, "Pink")
    heart_px(54.0, 1.3, 11.4, 0.55, "Red", "x", 0.15, depth=0.3)
    for (px, c) in ((50.8, "White"), (53.0, "Aqua"), (55.0, "Yellow"), (57.2, "White")):
        B(px - 1.2, 1.6, 3.2, px + 1.2, 2.6, 5.0, c)                             # pillows
    B(53.2, 2.7, 3.2, 54.8, 3.4, 4.6, "Rose")
    heart_px(54.0, 3.3, 4.5, 0.2, "Red", "x", 0.0, depth=0.15, rows=["0110110", "1111111", "0111110", "0011100", "0001000"])
    plush(51.0, 4.2, 3.2, "Plush", 0.8, "+y")
    plush(57.2, 4.4, 3.2, "Pink", 0.7, "+y")
    # bench at the foot of the bed
    B(50.0, 12.6, 0, 58.0, 14.4, 0.5, "Gold"); B(50.0, 12.6, 0.5, 58.0, 14.4, 2.2, "Lilac")
    for k in range(4):
        B(50.3 + k * 2.0, 12.9, 2.2, 51.9 + k * 2.0, 14.1, 2.35, "Pink")
    # nightstands + lamps
    for nx in (46.0, 59.6):
        B(nx, 0.6, 0, nx + 2.6, 3.2, 3.0, "White"); B(nx - 0.05, 0.55, 3.0, nx + 2.65, 3.25, 3.3, "WainPink")
        B(nx + 0.2, 3.2, 1.6, nx + 2.4, 3.25, 2.7, "Aqua"); B(nx + 1.1, 3.25, 2.1, nx + 1.5, 3.4, 2.3, "Gold")
        table_lamp(nx + 1.3, 1.6, 3.3, "Pink", "Aqua")
    B(46.4, 2.3, 3.3, 47.4, 2.9, 3.6, "Lilac")                                    # book
    Cy(61.8, 2.6, 3.3, 3.8, 0.3, "Yellow", seg=10)                               # alarm clock
    # window seat on the east window with cushions
    B(61.4, 15.0, 0, 63.5, 29.0, 2.6, "White")
    for k in range(4):
        B(61.6, 15.4 + k * 3.4, 0.4, 61.65, 18.2 + k * 3.4, 2.2, "WainPink")
    B(61.2, 15.0, 2.6, 63.5, 29.0, 3.2, "Aqua")
    for (yy, c) in ((16.2, "Rose"), (19.0, "Yellow"), (25.2, "Lilac"), (27.8, "Pink")):
        B(62.2, yy - 1.0, 3.2, 63.3, yy + 1.0, 5.0, c)
    plush(62.2, 22.2, 3.2, "Lilac", 0.6, "-y")
    curtains("y", 64, -1, 15.0, 29.0, 10.0, "Peach")
    # dresser with mirror (west wall, y 31..38)
    B(44.6, 31.0, 0, 47.0, 38.4, 3.8, "White")
    for k in range(3):
        for j in range(2):
            B(47.0, 31.3 + j * 3.6, 0.4 + k * 1.1, 47.08, 34.6 + j * 3.6, 1.3 + k * 1.1, ["Pink", "Aqua", "Yellow"][k])
            B(47.08, 32.6 + j * 3.6, 0.75 + k * 1.1, 47.25, 33.3 + j * 3.6, 0.95 + k * 1.1, "Gold")
    B(44.5, 30.9, 3.8, 47.1, 38.5, 4.1, "WainPink")
    for i in range(14):
        a = i * math.pi / 7
        B(44.6, 34.7 + 2.2 * math.cos(a) - 0.3, 7.4 + 2.2 * math.sin(a) - 0.3, 44.85, 34.7 + 2.2 * math.cos(a) + 0.3, 7.4 + 2.2 * math.sin(a) + 0.3, "Gold")
    B(44.6, 33.2, 5.9, 44.72, 36.2, 8.9, "Frost", "Glass")
    flowers_vase(45.8, 31.8, 4.1, "Rose")
    B(45.2, 37.0, 4.1, 46.4, 38.0, 4.9, "Aqua"); B(45.3, 37.1, 4.9, 46.3, 37.9, 5.0, "Gold")   # jewellery box
    # armchair + side table + toy chest by the window seat
    armchair(57.0, 25.0, "+x" if False else "-x", "Rose", "Pink")
    B(57.0, 28.2, 0, 59.0, 30.2, 2.6, "Gold"); B(56.8, 28.0, 2.6, 59.2, 30.4, 2.85, "White")
    teaset(58.0, 29.2, 2.85)
    B(45.0, 16.0, 0, 48.6, 19.2, 2.8, "Aqua"); B(44.9, 15.9, 2.8, 48.7, 19.3, 3.3, "Yellow")
    heart_px(48.62, 17.6, 2.3, 0.22, "Rose", "y", 0.0, depth=0.1)
    plush(46.6, 17.6, 3.3, "Plush", 0.55, "+y" if False else "-y")
    # wall shelf with seashells above the toy chest
    B(44.6, 15.6, 7.0, 45.6, 19.8, 7.2, "White")
    for k, c in enumerate(("Shell", "Coral", "Pink", "Shell")):
        B(44.8, 16.0 + k * 0.95, 7.2, 45.4, 16.6 + k * 0.95, 7.7 + 0.15 * (k % 2), c)
    # rug, plants, string lights above the bed
    rug(48.0, 13.6, 60.0, 24.0, ["Pink", "White", "Peach", "White", "Pink"], "Rose", "x")
    plant(62.4, 31.6, 1.0, "Yellow")
    plant(45.6, 26.0, 0.8, "Aqua")
    for k in range(18):
        x = 47.0 + k * 0.85
        z = 10.6 - 0.9 * math.sin(math.pi * k / 17)
        B(x - 0.15, 0.8, z - 0.4, x + 0.15, 1.1, z, ["Lamp", "LampPink", "LampTeal", "Lamp"][k % 4])
    for k in range(17):
        x = 47.0 + k * 0.85
        z = 10.6 - 0.9 * math.sin(math.pi * (k + 0.5) / 17)
        B(x, 0.9, z + 0.1, x + 0.85, 1.0, z + 0.18, "Iron")
    curtains("x", 40, -1, 50.0, 56.0, 9.0, "Peach")
    ceiling_lamp(54.0, 20.0, 1.8, "Lamp", "Gold")
    ceiling_lamp(54.0, 7.0, 1.2, "LampPink", "Gold")


def balcony():
    """Balcony outside the panoramic wall (local y 40..48): deck, glass railing with heart posts, loungers, telescope."""
    y0, y1, x0, x1 = 41.0, 48.0, 17.0, 63.0
    wx0, wy0 = T(x0, y0); wx1, wy1 = T(x1, y1)
    fsd_lib.planks(_sc, min(wx0, wx1), min(wy0, wy1), max(wx0, wx1), max(wy0, wy1), OZ + 0.0, 0.5, "y", "FlatBalcony", collide=False, seed=7)
    B(x0, 40.5, -1.6, x1, y1, -0.5, "White", "FlatBalcony")
    B(x0, y1 - 0.3, -1.6, x1, y1, 0.3, "White", "FlatBalcony")
    # glass railing + white top rail + posts with lamps
    B(x0 + 0.3, y1 - 0.4, 0.3, x1 - 0.3, y1 - 0.25, 3.6, "Glass", "Glass")
    for (xa, xb) in ((x0, x0 + 0.3), (x1 - 0.3, x1)):
        B(xa, 40.6, 0.3, xb, y1, 3.6, "Glass", "Glass")
        B(xa - 0.05, 40.6, 3.6, xb + 0.05, y1, 4.0, "White", "FlatBalcony")
    B(x0, y1 - 0.5, 3.6, x1, y1 - 0.15, 4.0, "White", "FlatBalcony")
    xx = x0
    k = 0
    while xx <= x1 + 0.01:
        B(xx - 0.25, y1 - 0.6, 0.3, xx + 0.25, y1 - 0.05, 4.3, "White", "FlatBalcony")
        B(xx - 0.2, y1 - 0.55, 4.3, xx + 0.2, y1 - 0.1, 4.7, ["Lamp", "LampPink", "LampTeal"][k % 3], "FlatBalcony")
        xx += 5.75; k += 1
    # loungers with towels + parasol
    for (lx, c) in ((20.0, "Aqua"), (24.6, "Rose")):
        B(lx, 42.0, 0, lx + 3.2, 47.0, 1.4, "White")
        P([(lx, 42.0), (lx + 3.2, 42.0), (lx + 3.2, 43.4), (lx, 43.4)], 1.4, 3.6, "White")
        B(lx + 0.3, 43.4, 1.4, lx + 2.9, 46.8, 1.6, c)
        for k in range(4):
            B(lx + 0.3, 43.6 + k * 0.85, 1.6, lx + 2.9, 43.9 + k * 0.85, 1.65, "White")
    Cy(23.4, 45.2, 0, 7.2, 0.12, "White", seg=6)
    for i in range(8):
        a0, a1 = i * math.pi / 4, (i + 1) * math.pi / 4
        P([(23.4, 45.2), (23.4 + 3.6 * math.cos(a0), 45.2 + 3.6 * math.sin(a0)), (23.4 + 3.6 * math.cos(a1), 45.2 + 3.6 * math.sin(a1))], 6.6, 7.2, "Rose" if i % 2 else "White", "FlatBalcony")
    # bistro table + 2 chairs
    Cy(37.0, 44.6, 0, 3.0, 0.2, "White", seg=8); Cy(37.0, 44.6, 3.0, 3.3, 1.4, "Aqua", seg=16)
    cup(36.6, 44.3, 3.3, "Pink"); flowers_vase(37.5, 45.0, 3.3, "Yellow")
    chair(34.6, 44.6, "+x", "Yellow", "White", False); chair(39.4, 44.6, "-x", "Yellow", "White", False)
    # telescope looking over the lagoon + lifebuoy decor + plants
    Cy(44.0, 46.0, 0, 0.3, 0.9, "Gold", seg=10)
    for (dx, dy) in ((-0.6, -0.4), (0.6, -0.4), (0.0, 0.6)):
        B(44.0 + dx - 0.1, 46.0 + dy - 0.1, 0.3, 44.0 + dx * 0.2 + 0.1, 46.0 + dy * 0.2 + 0.1, 3.6, "Gold")
    _sc.loft([[(lambda p: (p[0], p[1], OZ + p2))(T(44.0 + 0.35 * math.cos(a), 45.4 + 0.0)) for a in [0]] for p2 in [0]], "Gold") if False else None
    B(43.6, 44.6, 3.6, 44.4, 47.6, 4.4, "Navy"); B(43.5, 47.6, 3.5, 44.5, 47.9, 4.5, "Gold")
    for i in range(12):
        a = i * math.pi / 6
        B(55.0 + 1.3 * math.cos(a) - 0.35, y1 - 0.75, 2.2 + 1.3 * math.sin(a) - 0.35, 55.0 + 1.3 * math.cos(a) + 0.35, y1 - 0.62, 2.2 + 1.3 * math.sin(a) + 0.35, "Red" if (i // 3) % 2 else "White", "FlatBalcony")
    plant(61.5, 42.3, 0.9, "Coral"); plant(18.5, 42.4, 0.8, "Yellow"); plant(48.5, 42.3, 0.7, "Aqua")
    # flower boxes on the railing
    for (fx0, fx1) in ((27.6, 32.4), (57.0, 61.6)):
        B(fx0, y1 - 1.4, 3.0, fx1, y1 - 0.6, 3.8, "WoodMid", "FlatBalcony")
        for k in range(int((fx1 - fx0) / 0.6)):
            B(fx0 + 0.1 + k * 0.6, y1 - 1.3, 3.8, fx0 + 0.5 + k * 0.6, y1 - 0.7, 4.3, ["Pink", "Yellow", "Red", "White", "Purple"][k % 5], "FlatBalcony")
    # string lights along the facade above the balcony
    for k in range(54):
        x = x0 + 0.5 + k * 0.85
        z = 11.0 - 0.6 * abs(math.sin(math.pi * k / 9))
        B(x - 0.15, 41.0, z - 0.4, x + 0.15, 41.3, z, ["Lamp", "LampPink", "LampTeal"][k % 3], "FlatBalcony")
    # awning (pink/white stripes) over the balcony doors
    for k in range(10):
        B(33.0 + k * 0.85, 40.6, 9.6, 33.85 + k * 0.85, 43.0, 10.0, "Rose" if k % 2 else "White", "FlatBalcony")
    for k in range(8):
        B(49.2 + k * 0.95, 40.6, 9.6, 50.15 + k * 0.95, 43.0, 10.0, "Aqua" if k % 2 else "White", "FlatBalcony")


def outside_facade():
    """Pink plaster outer skin + teal/yellow bands so the flat reads like the tower top from the balcony."""
    for z0, m in ((-1.6, "Yellow"), (12.4, "Teal")):
        B(-0.7, D + 0.5, z0, W + 0.7, D + 0.75, z0 + 0.8, m, "FlatWalls")
    heart_px(46.0 if False else 40.5, D + 0.75, 15.5, 0.6, "Red", "x", 0.0, depth=0.3) if False else None


def build(sc):
    global _sc
    _sc = sc
    setup_palette()
    shell()
    hall(); living(); kitchen(); bath(); dressing(); bedroom(); balcony(); outside_facade()
