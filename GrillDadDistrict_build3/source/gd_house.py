"""Grill Dad's Castle (v2): red-brick two-storey keep with a giant kettle-grill lid on the roof, two black smoker towers,
balcony, wide front stairs, 10 rooms with full interiors, and a big walled courtyard (crenellated brick wall, gatehouse with a
raised portcullis and spatula shield, corner towers with flags and spatula banners, built-in grill station, firewood, picnic,
pool behind the keep). World coords; keep local origin (HX, HY) = SW corner of the keep body, front faces south (the park)."""
import math, random
import gd_kit as K
from gd_kit import B, C, COL, FB, FP, wall, stairs, text, icon, pix, ball, ring, hcyl, beam

HX, HY = 218.0, 414.0     # keep body x 218..282, y 414..452
BW, BD = 64.0, 38.0
Z1 = 3.0      # 1F floor top (raised; wide stairs up)
ZC1 = 15.0    # 1F wall top / slab bottom
ZS = 15.9     # slab top
Z2 = 16.1     # 2F floor top
ZW = 28.0     # 2F wall top
TW = (210.0, 421.0)   # west smoker tower centre
TE = (290.0, 421.0)   # east smoker tower centre
TR = 8.5              # smoker tower radius (16-gon, flat faces N/S/E/W)
WALL = (178.0, 366.0, 322.0, 482.0)   # courtyard wall outer bounds
sc = None

DOORS = []    # (name, cx, cy, z, width, axis) world coords, for the audit
TARGETS = {}  # name -> (x, y, z) world, for the walk audit


def h(x0, y0, z0, x1, y1, z1, mat, group="House", col=False, tag=None):
    B(HX + x0, HY + y0, z0, HX + x1, HY + y1, z1, mat, group, col, tag)


def hc(x0, y0, z0, x1, y1, z1, tag, group="House"):
    COL(HX + x0, HY + y0, z0, HX + x1, HY + y1, z1, tag, group)


def hw(axis, fixed, a0, a1, z0, z1, ops, mat, group="House", **kw):
    off = HY if axis == "x" else HX
    aoff = HX if axis == "x" else HY
    wall(axis, fixed + off, a0 + aoff, a1 + aoff, z0, z1, [(u0 + aoff, u1 + aoff, zb, zt, k) for (u0, u1, zb, zt, k) in ops], mat, group, **kw)


def door(name, cx, cy, z, w, axis):
    DOORS.append((name, HX + cx, HY + cy, z, w, axis))


def tgt(name, x, y, z):
    TARGETS[name] = (HX + x, HY + y, z)


# ------------------------------------------------------------------ furniture (world coords, FB frames)
def sofa(cx, cy, z, face, w=9.0, mat="ClothRed", alt="ClothWhite", g="HouseInterior"):
    FB(face, cx, cy, -w / 2, -1.9, z, w / 2, 1.9, z + 1.4, mat, g)
    FB(face, cx, cy, -w / 2, -1.9, z + 1.4, w / 2, -1.0, z + 3.7, mat, g)
    FB(face, cx, cy, -w / 2, -1.0, z + 1.4, -w / 2 + 0.9, 1.9, z + 2.6, mat, g); FB(face, cx, cy, w / 2 - 0.9, -1.0, z + 1.4, w / 2, 1.9, z + 2.6, mat, g)
    n = max(1, int(round((w - 1.8) / 2.6))); cw = (w - 1.8) / n
    for i in range(n):
        a = -w / 2 + 0.9 + i * cw
        FB(face, cx, cy, a + 0.06, -1.0, z + 1.4, a + cw - 0.06, 1.8, z + 1.95, alt if i % 2 else mat, g)
        FB(face, cx, cy, a + 0.2, -1.0, z + 1.95, a + cw - 0.2, -0.5, z + 3.3, alt, g)
    (rx, ry), (nx, ny) = K.FACE[face]
    COL(cx - abs(rx) * w / 2 - abs(nx) * 1.9, cy - abs(ry) * w / 2 - abs(ny) * 1.9, z, cx + abs(rx) * w / 2 + abs(nx) * 1.9, cy + abs(ry) * w / 2 + abs(ny) * 1.9, z + 2.6, "Sofa", g)


def table(x0, y0, x1, y1, z, hh=3.0, top="WoodLight", leg="WoodMid", g="HouseInterior", col=True):
    B(x0, y0, z + hh - 0.3, x1, y1, z + hh, top, g)
    for (lx, ly) in ((x0 + 0.2, y0 + 0.2), (x1 - 0.6, y0 + 0.2), (x0 + 0.2, y1 - 0.6), (x1 - 0.6, y1 - 0.6)):
        B(lx, ly, z, lx + 0.4, ly + 0.4, z + hh - 0.3, leg, g)
    if col: COL(x0, y0, z, x1, y1, z + hh, "Table", g)


def chair(cx, cy, z, face, mat="WoodMid", seat="ClothRed", g="HouseInterior"):
    FB(face, cx, cy, -0.85, -0.85, z + 1.5, 0.85, 0.85, z + 1.8, seat, g)
    for a, d in ((-0.8, -0.8), (0.55, -0.8), (-0.8, 0.55), (0.55, 0.55)):
        FB(face, cx, cy, a, d, z, a + 0.25, d + 0.25, z + 1.5, mat, g)
    FB(face, cx, cy, -0.85, -0.85, z + 1.8, -0.6, -0.6, z + 4.0, mat, g); FB(face, cx, cy, 0.6, -0.85, z + 1.8, 0.85, -0.6, z + 4.0, mat, g)
    FB(face, cx, cy, -0.6, -0.82, z + 3.0, 0.6, -0.64, z + 3.9, mat, g); FB(face, cx, cy, -0.6, -0.82, z + 2.2, 0.6, -0.64, z + 2.6, mat, g)


def bed(cx, cy, z, face, w=7.0, l=10.0, blanket="ClothRed", g="House2F"):
    """Head at the back (d = -l/2), foot towards `face`."""
    FB(face, cx, cy, -w / 2, -l / 2, z, w / 2, l / 2, z + 1.2, "WoodMid", g)
    FB(face, cx, cy, -w / 2, -l / 2 - 0.4, z, w / 2, -l / 2, z + 4.4, "WoodDark", g)
    FB(face, cx, cy, -w / 2, l / 2, z, w / 2, l / 2 + 0.3, z + 2.2, "WoodDark", g)
    FB(face, cx, cy, -w / 2 + 0.2, -l / 2 + 0.1, z + 1.2, w / 2 - 0.2, l / 2 - 0.1, z + 2.0, "ClothWhite", g)
    FB(face, cx, cy, -w / 2 + 0.1, -l / 2 + 3.2, z + 2.0, w / 2 - 0.1, l / 2 - 0.05, z + 2.35, blanket, g)
    FB(face, cx, cy, -w / 2 + 0.1, -l / 2 + 3.2, z + 2.35, w / 2 - 0.1, -l / 2 + 4.2, z + 2.5, "ClothWhite", g)
    pw = (w - 1.0) / 2 if w > 6 else w - 1.0
    for i in range(2 if w > 6 else 1):
        a = -w / 2 + 0.4 + i * (pw + 0.2)
        FB(face, cx, cy, a, -l / 2 + 0.4, z + 2.0, a + pw, -l / 2 + 2.6, z + 2.6, "ClothWhite", g)
    (rx, ry), (nx, ny) = K.FACE[face]
    COL(cx - abs(rx) * w / 2 - abs(nx) * (l / 2 + 0.4), cy - abs(ry) * w / 2 - abs(ny) * (l / 2 + 0.4), z, cx + abs(rx) * w / 2 + abs(nx) * (l / 2 + 0.4), cy + abs(ry) * w / 2 + abs(ny) * (l / 2 + 0.4), z + 2.4, "Bed", g)


def shelf(cx, cy, z, face, w=6.0, hh=8.0, d=1.4, seed=0, g="HouseInterior", mat="WoodDark", items="books"):
    """Bookshelf standing with its back at d=-d/2, open towards `face`."""
    r = random.Random(seed)
    FB(face, cx, cy, -w / 2, -d / 2, z, w / 2, -d / 2 + 0.2, z + hh, mat, g)
    FB(face, cx, cy, -w / 2, -d / 2, z, -w / 2 + 0.25, d / 2, z + hh, mat, g); FB(face, cx, cy, w / 2 - 0.25, -d / 2, z, w / 2, d / 2, z + hh, mat, g)
    lv = max(2, int(hh / 2.0))
    for k in range(lv + 1):
        zz = z + k * (hh - 0.25) / lv
        FB(face, cx, cy, -w / 2 + 0.25, -d / 2 + 0.2, zz, w / 2 - 0.25, d / 2, zz + 0.25, mat, g)
        if k < lv:
            a = -w / 2 + 0.4
            while a < w / 2 - 0.8:
                if items == "books" or r.random() < 0.5:
                    bw = r.uniform(0.3, 0.55); bh = r.uniform(1.0, 1.55)
                    FB(face, cx, cy, a, -d / 2 + 0.3, zz + 0.25, a + bw, d / 2 - 0.25, zz + 0.25 + bh, r.choice(["Red", "Blue", "Green", "Yellow", "Orange", "Purple", "Teal", "White"]), g)
                    a += bw + 0.04
                else:
                    kind = r.choice(["Ketchup", "Mustard", "Gold", "Brown", "Green"])
                    FB(face, cx, cy, a, -d / 2 + 0.4, zz + 0.25, a + 0.5, d / 2 - 0.4, zz + 1.25, kind, g)
                    FB(face, cx, cy, a + 0.15, -d / 2 + 0.55, zz + 1.25, a + 0.35, d / 2 - 0.55, zz + 1.5, "White", g)
                    a += 0.75
                if r.random() < 0.12: a += r.uniform(0.5, 1.2)
    (rx, ry), (nx, ny) = K.FACE[face]
    COL(cx - abs(rx) * w / 2 - abs(nx) * d / 2, cy - abs(ry) * w / 2 - abs(ny) * d / 2, z, cx + abs(rx) * w / 2 + abs(nx) * d / 2, cy + abs(ry) * w / 2 + abs(ny) * d / 2, z + hh, "Shelf", g)


def rug(x0, y0, x1, y1, z, mat="ClothRed", border="ClothWhite", g="HouseInterior"):
    B(x0, y0, z, x1, y1, z + 0.06, border, g); B(x0 + 0.6, y0 + 0.6, z + 0.02, x1 - 0.6, y1 - 0.6, z + 0.1, mat, g)


def plant(x, y, z, g="HouseInterior", s=1.0):
    C(x, y, z, z + 1.3 * s, 0.7 * s, "BrickC", g, 8); C(x, y, z + 1.3 * s, z + 1.45 * s, 0.6 * s, "Dirt", g, 8)
    B(x - 0.1, y - 0.1, z + 1.45 * s, x + 0.1, y + 0.1, z + 3.0 * s, "Trunk", g)
    r = random.Random(int(x * 13 + y * 7))
    for k in range(4):
        ox, oy = r.uniform(-0.6, 0.6) * s, r.uniform(-0.6, 0.6) * s; cs = r.uniform(0.5, 0.8) * s
        B(x + ox - cs, y + oy - cs, z + (2.4 + k * 0.5) * s, x + ox + cs, y + oy + cs, z + (2.4 + k * 0.5) * s + 1.4 * cs, ["Leaf", "LeafB", "LeafC"][k % 3], g)


def floor_lamp(x, y, z, g="HouseInterior"):
    C(x, y, z, z + 0.2, 0.7, "Iron", g, 8); C(x, y, z + 0.2, z + 6.0, 0.12, "Iron", g, 6)
    C(x, y, z + 6.0, z + 7.6, 0.9, "Lamp", g, 8)
    sc.anchor("RoomLight", (x, y, z + 7.0), range=24)


def ceiling_lamp(x, y, zc, g="HouseInterior"):
    B(x - 0.08, y - 0.08, zc - 1.6, x + 0.08, y + 0.08, zc, "Iron", g)
    C(x, y, zc - 2.6, zc - 1.6, 0.9, "Lamp", g, 8)
    sc.anchor("RoomLight", (x, y, zc - 2.2), range=30)


def picture(cx, cy, zc, face, w=4.0, hh=3.0, art="grill", g="HouseInterior", frame="WoodDark"):
    """On a wall whose surface passes through (cx, cy); visible from the `face` side."""
    FB(face, cx, cy, -w / 2, 0, zc - hh / 2, w / 2, 0.18, zc + hh / 2, frame, g)
    bg = {"grill": "SkyBlue", "flame": "Navy", "dad": "Magenta", "plain": "ClothYellow", "kid": "Paper"}[art]
    FB(face, cx, cy, -w / 2 + 0.3, 0.1, zc - hh / 2 + 0.3, w / 2 - 0.3, 0.26, zc + hh / 2 - 0.3, bg, g)
    px, py = FP(face, cx, cy, 0, 0.26)
    cell = min((w - 0.9) / 12.0, (hh - 0.9) / 12.0)
    if art == "grill": icon(K.GRILL_ICON, {"1": "Red"}, px, py, zc, cell, face, 0.0, 0.08, g)
    elif art == "flame": icon(K.FLAME_ICON, {"o": "Fire", "y": "FireY", "w": "White"}, px, py, zc, cell * 1.2, face, 0.0, 0.08, g)
    elif art == "dad": icon(K.DAD_FACE, {"h": "Brown", "y": "Yellow", "b": "Black"}, px, py, zc, cell, face, 0.0, 0.08, g)
    elif art == "kid":
        kid = ["....yyy.....", "...yyyyy....", "....yyy.....", "............", "..b....rrr..", ".bbb..rrrrr.", "..b...r.r.r.", "..b...rrrrr.", ".b.b...r.r..", "gggggggggggg"]
        icon(kid, {"y": "Yellow", "b": "Blue", "r": "Red", "g": "Green"}, px, py, zc, cell, face, 0.0, 0.08, g)


def trophy(x, y, z, s=1.0, g="HouseInterior"):
    B(x - 0.4 * s, y - 0.4 * s, z, x + 0.4 * s, y + 0.4 * s, z + 0.3 * s, "WoodDark", g)
    C(x, y, z + 0.3 * s, z + 0.8 * s, 0.12 * s, "Gold", g, 6)
    C(x, y, z + 0.8 * s, z + 1.5 * s, 0.42 * s, "Gold", g, 8)
    B(x - 0.7 * s, y - 0.06 * s, z + 1.0 * s, x + 0.7 * s, y + 0.06 * s, z + 1.3 * s, "GoldB", g)


def counter(x0, y0, x1, y1, z, g="HouseInterior", body="White", top="StoneC", hh=3.2):
    B(x0, y0, z, x1, y1, z + hh - 0.3, body, g, True, "Counter")
    B(x0 - 0.1, y0 - 0.1, z + hh - 0.3, x1 + 0.1, y1 + 0.1, z + hh, top, g)


def cabinet_doors(face, cx, cy, w, z, n, g="HouseInterior", knob="Red"):
    cw = w / n
    for i in range(n):
        a = -w / 2 + i * cw
        FB(face, cx, cy, a + 0.12, 0.0, z + 0.3, a + cw - 0.12, 0.1, z + 2.6, "WallGrey", g)
        FB(face, cx, cy, a + cw - 0.5, 0.1, z + 1.6, a + cw - 0.3, 0.22, z + 2.0, knob, g)


def fridge(cx, cy, z, face, g="HouseInterior"):
    FB(face, cx, cy, -1.6, -1.5, z, 1.6, 1.5, z + 7.4, "Steel", g, True, "Fridge")
    FB(face, cx, cy, -1.5, 1.5, z + 0.3, 1.5, 1.62, z + 4.6, "Chrome", g); FB(face, cx, cy, -1.5, 1.5, z + 4.8, 1.5, 1.62, z + 7.2, "Chrome", g)
    FB(face, cx, cy, 1.0, 1.62, z + 2.0, 1.2, 1.8, z + 4.2, "Iron", g); FB(face, cx, cy, 1.0, 1.62, z + 5.1, 1.2, 1.8, z + 6.6, "Iron", g)
    px, py = FP(face, cx, cy, -0.5, 1.62)
    icon(K.FLAME_ICON, {"o": "Fire", "y": "FireY", "w": "White"}, px, py, z + 6.0, 0.1, face, 0.0, 0.06, g)
    FB(face, cx, cy, -1.1, 1.62, z + 3.0, -0.3, 1.7, z + 4.0, "Paper", g)


def stove(cx, cy, z, face, g="HouseInterior"):
    FB(face, cx, cy, -1.6, -1.5, z, 1.6, 1.5, z + 3.2, "Iron", g, True, "Stove")
    FB(face, cx, cy, -1.3, 1.5, z + 0.5, 1.3, 1.6, z + 2.3, "Black", g); FB(face, cx, cy, -1.2, 1.6, z + 2.45, 1.2, 1.75, z + 2.65, "Chrome", g)
    for a, d in ((-0.8, -0.7), (0.8, -0.7), (-0.8, 0.7), (0.8, 0.7)):
        px, py = FP(face, cx, cy, a, d)
        C(px, py, z + 3.2, z + 3.3, 0.5, "Black", g, 8); C(px, py, z + 3.3, z + 3.34, 0.3, "Fire", g, 6)
    px, py = FP(face, cx, cy, -0.8, 0.7)
    C(px, py, z + 3.34, z + 4.1, 0.6, "Steel", g, 8); FB(face, cx, cy, -0.9, 1.3, z + 3.8, -0.7, 2.3, z + 3.95, "Black", g)
    # hood
    FB(face, cx, cy, -1.7, -1.5, z + 7.2, 1.7, 1.0, z + 8.2, "Steel", g); FB(face, cx, cy, -0.8, -1.5, z + 8.2, 0.8, -0.2, z + 12.0, "Steel", g)


def wardrobe(cx, cy, z, face, w=5.5, g="House2F", mat="WoodMid"):
    FB(face, cx, cy, -w / 2, -1.0, z, w / 2, 1.0, z + 8.5, mat, g, True, "Wardrobe")
    FB(face, cx, cy, -w / 2 - 0.1, -1.1, z + 8.5, w / 2 + 0.1, 1.1, z + 8.8, "WoodDark", g)
    FB(face, cx, cy, -w / 2 + 0.2, 1.0, z + 0.4, -0.08, 1.12, z + 8.2, "WoodLight", g); FB(face, cx, cy, 0.08, 1.0, z + 0.4, w / 2 - 0.2, 1.12, z + 8.2, "WoodLight", g)
    FB(face, cx, cy, -0.5, 1.12, z + 4.0, -0.3, 1.3, z + 5.0, "Gold", g); FB(face, cx, cy, 0.3, 1.12, z + 4.0, 0.5, 1.3, z + 5.0, "Gold", g)


def tv(cx, cy, z, face, g="HouseInterior"):
    FB(face, cx, cy, -3.5, -0.9, z, 3.5, 0.9, z + 2.2, "WoodDark", g, True, "TvStand")
    FB(face, cx, cy, -3.3, 0.9, z + 0.3, -0.1, 1.0, z + 1.9, "WoodMid", g); FB(face, cx, cy, 0.1, 0.9, z + 0.3, 3.3, 1.0, z + 1.9, "WoodMid", g)
    FB(face, cx, cy, -0.5, -0.3, z + 2.2, 0.5, 0.3, z + 2.7, "Black", g)
    FB(face, cx, cy, -3.0, -0.2, z + 2.7, 3.0, 0.15, z + 6.3, "Black", g)
    FB(face, cx, cy, -2.8, 0.15, z + 2.9, 2.8, 0.22, z + 6.1, "Screen", g)
    px, py = FP(face, cx, cy, 0, 0.22)
    icon(K.GRILL_ICON, {"1": "Fire"}, px, py, z + 4.5, 0.22, face, 0.0, 0.05, g)



# ------------------------------------------------------------------ small geometry helpers
def poly16(cx, cy, r, n=16):
    """16-gon with flat faces towards N/S/E/W (vertices offset by half a step)."""
    return [(cx + r * math.cos(math.radians(360.0 * (i + 0.5) / n)), cy + r * math.sin(math.radians(360.0 * (i + 0.5) / n))) for i in range(n)]


def ellipse(cx, cy, rx, ry, n=40):
    return [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


def disc(c, n, r, th, mat, g, seg=16):
    l = math.sqrt(sum(v * v for v in n)); n = tuple(v / l for v in n)
    a = (1, 0, 0) if abs(n[0]) < 0.9 else (0, 1, 0)
    u = (n[1] * a[2] - n[2] * a[1], n[2] * a[0] - n[0] * a[2], n[0] * a[1] - n[1] * a[0])
    lu = math.sqrt(sum(v * v for v in u)); u = tuple(v / lu for v in u)
    v = (n[1] * u[2] - n[2] * u[1], n[2] * u[0] - n[0] * u[2], n[0] * u[1] - n[1] * u[0])
    def rg(off):
        return [tuple(c[k] + n[k] * off + r * (math.cos(2 * math.pi * i / seg) * u[k] + math.sin(2 * math.pi * i / seg) * v[k]) for k in range(3)) for i in range(seg)]
    sc.loft([rg(0.0), rg(th)], mat, g, True, False)
    return u, v, n


SPAT = [".sss.", "sssss", "sssss", "sssss", ".sss.", "..s..", "..s..", "..s..", "..k..", "..k..", "..k.."]


def shield_grid():
    g = []
    for r in range(17):
        w = 7 if r <= 10 else 7 - (r - 10)
        row = ""
        for c in range(15):
            d = abs(c - 7)
            if d > w: row += "."
            elif d == w or r == 0 or (r > 10 and d >= w - 1): row += "k"
            else: row += "r"
        g.append(row)
    sp = K.spatulas_icon()
    for r, line in enumerate(sp):
        rr = r + 3
        g[rr] = "".join(("w" if (ch == "s" and g[rr][c] == "r") else g[rr][c]) for c, ch in enumerate(line))
    return g


def banner_grid():
    g = []
    for r in range(23):
        row = ""
        for c in range(15):
            if r >= 20 and 5 - (22 - r) * 2 <= c <= 9 + (22 - r) * 2 and abs(c - 7) <= (r - 19) * 2 - 1: row += "."
            elif c in (0, 14) or r == 0: row += "k"
            elif r >= 20 and abs(c - 7) == (r - 19) * 2: row += "k"
            else: row += "r"
        g.append(row)
    for r, line in enumerate(SPAT):
        rr = r + 5
        g[rr] = g[rr][:5] + "".join(("w" if ch == "s" else ("y" if ch == "k" else g[rr][5 + c])) for c, ch in enumerate(line)) + g[rr][10:]
    return g


def banner(face, ox, oy, ztop, cell=0.3, d0=0.0, group="Signs"):
    """Hanging red banner with a white spatula; (ox, oy) = centre of the top edge on the wall surface."""
    g = banner_grid()
    w = len(g[0]) * cell
    (rx, ry), _ = K.FACE[face]
    pix(g, {"k": "Black", "r": "Red", "w": "White", "y": "Gold"}, ox - rx * w / 2, oy - ry * w / 2, ztop, cell, face, d0, d0 + 0.18, group)
    FB(face, ox, oy, -w / 2 - 0.4, d0, ztop, w / 2 + 0.4, d0 + 0.35, ztop + 0.35, "Gold", group)


def lantern(face, ox, oy, z, g="House"):
    """Wall lantern; (ox, oy) on the wall surface, z = lamp bottom."""
    FB(face, ox, oy, -0.2, 0.0, z + 1.5, 0.2, 0.9, z + 1.8, "Iron", g)
    FB(face, ox, oy, -0.55, 0.6, z + 1.8, 0.55, 1.6, z + 2.05, "Iron", g)
    FB(face, ox, oy, -0.45, 0.7, z, 0.45, 1.5, z + 1.8, "Lamp", g)
    FB(face, ox, oy, -0.55, 0.6, z - 0.2, 0.55, 1.6, z, "Iron", g)
    px, py = FP(face, ox, oy, 0, 1.1)
    sc.anchor("LampLight", (px, py, z + 0.9), range=20)


# ------------------------------------------------------------------ the castle
def build(scene):
    global sc
    sc = scene
    shell()
    facade()
    front_stairs_balcony()
    smoker_tower(*TW, "W")
    smoker_tower(*TE, "E")
    roof_grill_lid()
    interior_1f()
    interior_2f()
    castle_wall()
    courtyard()
    backyard()


def planks(x0, x1, y0, y1, z0, z1, g, mats=("Floor", "FloorB")):
    y = y0; k = 0
    while y < y1 - 0.05:
        ye = min(y + 1.0, y1)
        h(x0, y + 0.02, z0, x1, ye - 0.02, z1, mats[k % 2], g)
        y = ye; k += 1


def tiles(x0, x1, y0, y1, z0, z1, g, mats=("Tile", "TileRed"), s=1.9):
    nx = max(1, int(round((x1 - x0) / s))); ny = max(1, int(round((y1 - y0) / s)))
    for i in range(nx):
        for j in range(ny):
            h(x0 + i * (x1 - x0) / nx, y0 + j * (y1 - y0) / ny, z0, x0 + (i + 1) * (x1 - x0) / nx, y0 + (j + 1) * (y1 - y0) / ny, z1, mats[(i + j) % 2], g)


def shell():
    W, D = "win", "door"
    def o1(a, b, k): return (a, b, Z1 + 3.5, Z1 + 9.5, W) if k == W else (a, b, Z1, Z1 + 9.0, k)
    def o2(a, b, k): return (a, b, Z2 + 3.5, Z2 + 9.5, W) if k == W else (a, b, Z2, Z2 + 9.0, k)
    fr = dict(frame="WoodDark")
    # foundation (stone plinth up to the raised 1F floor)
    h(-0.3, -0.3, 0, BW + 0.3, BD + 0.3, Z1 - 0.06, "StoneB", "House", True, "Foundation")
    for (a0, a1) in ((-0.3, 15.6), (48.4, BW + 0.3)):
        n = int((a1 - a0) / 2.05)
        for i in range(n):
            u = a0 + i * (a1 - a0) / n
            h(u + 0.1, -0.42, 0.3 + (i % 2) * 0.9, u + (a1 - a0) / n - 0.1, -0.3, 1.1 + (i % 2) * 0.9, "StoneC" if i % 3 else "Stone", "House")
    hc(0, 0, Z1 - 0.1, BW, BD, Z1, "Floor1")
    # 1F floors: planks everywhere, checker tiles in the kitchen
    G1 = "House"
    planks(0.8, BW - 0.8, 0.8, 20.3, Z1 - 0.1, Z1, G1)
    planks(0.8, 42.3, 20.3, BD - 0.8, Z1 - 0.1, Z1, G1)
    tiles(42.3, BW - 0.8, 20.3, BD - 0.8, Z1 - 0.1, Z1, G1)
    z0 = Z1 - 0.06
    # exterior walls 1F (brick outside, coloured plaster inside)
    hw("x", 0.4, 0, 22, z0, ZC1, [o1(4, 10, W), o1(12, 18, W)], "Brick", inside=1, mat_in="WallYellow", **fr)
    hw("x", 0.4, 22, 42, z0, ZC1, [(27, 37, Z1, Z1 + 10.0, D)], "Brick", inside=1, mat_in="WallPeach", **fr)
    hw("x", 0.4, 42, BW, z0, ZC1, [o1(46, 52, W), o1(54, 60, W)], "Brick", inside=1, mat_in="WallBlue", **fr)
    hw("x", BD - 0.4, 0, 22, z0, ZC1, [o1(6, 16, W)], "Brick", inside=-1, mat_in="WallGreen", **fr)
    hw("x", BD - 0.4, 22, 42, z0, ZC1, [o1(33, 39, D)], "Brick", inside=-1, mat_in="WallPeach", **fr)
    hw("x", BD - 0.4, 42, BW, z0, ZC1, [o1(47, 57, W)], "Brick", inside=-1, mat_in="WallYellow", **fr)
    hw("y", 0.4, 0.8, 20, z0, ZC1, [], "Brick", inside=1, mat_in="WallYellow", **fr)
    hw("y", 0.4, 20, BD - 0.8, z0, ZC1, [o1(24, 32, W)], "Brick", inside=1, mat_in="WallGreen", **fr)
    hw("y", BW - 0.4, 0.8, 20, z0, ZC1, [], "Brick", inside=-1, mat_in="WallBlue", **fr)
    hw("y", BW - 0.4, 20, BD - 0.8, z0, ZC1, [o1(25, 31, D)], "Brick", inside=-1, mat_in="WallYellow", **fr)
    # partitions 1F
    hw("y", 22.0, 0.8, BD - 0.8, Z1, ZC1, [o1(1.2, 7.2, D), o1(30, 36, D)], "WallPeach", t=0.6, **fr)
    hw("y", 42.0, 0.8, BD - 0.8, Z1, ZC1, [o1(4, 11, D), o1(27, 34, D)], "WallPeach", t=0.6, **fr)
    hw("x", 20.0, 0.8, 21.7, Z1, ZC1, [o1(14, 20, D)], "WallYellow", t=0.6, **fr)
    hw("x", 20.0, 42.3, BW - 0.8, Z1, ZC1, [o1(45, 51, D)], "WallBlue", t=0.6, **fr)
    door("front door", 32, 0.4, Z1, 10, "y"); door("back door", 36, BD - 0.4, Z1, 6, "y"); door("kitchen side door", BW - 0.4, 28, Z1, 6, "x")
    door("hall-trophy", 22, 4.2, Z1, 6, "x"); door("hall-dining", 22, 33, Z1, 6, "x"); door("hall-living", 42, 7.5, Z1, 7, "x")
    door("hall-kitchen", 42, 30.5, Z1, 7, "x"); door("trophy-dining", 17, 20, Z1, 6, "y"); door("living-kitchen", 48, 20, Z1, 6, "y")
    # 2F slab with the stair hole (x 22.8..27.8, y 8..28)
    for (x0, y0, x1, y1) in ((0, 0, BW, 8), (0, 28, BW, BD), (0, 8, 22.8, 28), (27.8, 8, BW, 28)):
        h(x0, y0, ZC1, x1, y1, ZS, "Ceiling", "House2F", True, "Floor2")
    G2 = "House2F"
    planks(0.8, BW - 0.8, 0.8, 8.0, ZS, Z2, G2, ("PlankC", "WoodLight"))
    planks(0.8, 22.8, 8.0, 20.3, ZS, Z2, G2, ("PlankC", "WoodLight"))
    planks(0.8, 22.8, 20.3, 28.0, ZS, Z2, G2)
    planks(27.8, BW - 0.8, 8.0, 20.3, ZS, Z2, G2, ("PlankC", "WoodLight"))
    planks(27.8, 42.3, 20.3, 28.0, ZS, Z2, G2)
    planks(0.8, 42.3, 28.0, BD - 0.8, ZS, Z2, G2)
    tiles(42.3, BW - 0.8, 20.3, BD - 0.8, ZS, Z2, G2, ("Tile", "TileB"), 1.75)
    # exterior walls 2F
    g2 = dict(group="House2F", frame="WoodDark")
    hw("x", 0.4, 0, 22, ZS, ZW, [o2(4, 10, W), o2(12, 18, W)], "Brick", inside=1, mat_in="WallPink", **g2)
    hw("x", 0.4, 22, 42, ZS, ZW, [(27, 37, Z2, Z2 + 10.0, D)], "Brick", inside=1, mat_in="WallGreen", **g2)
    hw("x", 0.4, 42, BW, ZS, ZW, [o2(46, 52, W), o2(54, 60, W)], "Brick", inside=1, mat_in="Navy", **g2)
    hw("x", BD - 0.4, 0, 22, ZS, ZW, [o2(6, 16, W)], "Brick", inside=-1, mat_in="WallBlue", **g2)
    hw("x", BD - 0.4, 22, 42, ZS, ZW, [o2(29, 37, W)], "Brick", inside=-1, mat_in="WallGreen", **g2)
    hw("x", BD - 0.4, 42, BW, ZS, ZW, [], "Brick", inside=-1, mat_in="Tile", **g2)
    hw("y", 0.4, 0.8, 20, ZS, ZW, [], "Brick", inside=1, mat_in="WallPink", **g2)
    hw("y", 0.4, 20, BD - 0.8, ZS, ZW, [o2(24, 32, W)], "Brick", inside=1, mat_in="WallBlue", **g2)
    hw("y", BW - 0.4, 0.8, 20, ZS, ZW, [], "Brick", inside=-1, mat_in="Navy", **g2)
    hw("y", BW - 0.4, 20, BD - 0.8, ZS, ZW, [o2(27, 33, W)], "Brick", inside=-1, mat_in="Tile", **g2)
    # partitions 2F
    hw("y", 22.0, 0.8, BD - 0.8, Z2, ZW, [o2(1.2, 7.2, D), o2(30, 36, D)], "WallGreen", t=0.6, **g2)
    hw("y", 42.0, 0.8, BD - 0.8, Z2, ZW, [o2(2, 9, D), o2(29, 35, D)], "WallGreen", t=0.6, **g2)
    hw("x", 20.0, 0.8, 21.7, Z2, ZW, [], "WallPink", t=0.6, **g2)
    hw("x", 20.0, 42.3, BW - 0.8, Z2, ZW, [], "Navy", t=0.6, **g2)
    door("2F master door", 22, 4.2, Z2, 6, "x"); door("2F kid door", 22, 33, Z2, 6, "x"); door("2F cinema door", 42, 5.5, Z2, 7, "x")
    door("2F bath door", 42, 32, Z2, 6, "x"); door("2F balcony door", 32, 0.4, Z2, 10, "y")
    # 2F ceiling
    h(0, 0, ZW, BW, BD, ZW + 0.5, "Ceiling", "HouseRoof", True, "Ceiling2")
    # door leaves (open): front + balcony double doors, back door, kitchen side door
    for (a0, a1) in ((21.9, 26.9), (37.1, 42.1)):   # front doors open outwards onto the landing, flat against the facade
        h(a0, -0.35, Z1, a1, -0.02, Z1 + 9.75, "WoodDark", "House", True, "DoorLeaf")
        h(a0 + 0.6, -0.41, Z1 + 3.0, a1 - 0.6, -0.3, Z1 + 9.0, "Glass", "Glass")
    for (a0, a1) in ((21.9, 26.9), (37.1, 42.1)):   # balcony doors open outwards, flat against the facade
        h(a0, -0.35, Z2, a1, -0.02, Z2 + 9.75, "WoodDark", "House2F", True, "DoorLeaf")
        h(a0 + 0.6, -0.41, Z2 + 3.0, a1 - 0.6, -0.3, Z2 + 9.0, "Glass", "Glass")
    h(32.6, BD - 6.8, Z1, 32.95, BD - 0.85, Z1 + 8.75, "Red", "House", True, "DoorLeaf")
    h(BW + 0.05, 24.6, Z1, BW + 5.6, 24.95, Z1 + 8.75, "Red", "House", True, "DoorLeaf")
    tgt("1F trophy hall", 17, 4, Z1); tgt("1F hall", 34, 4, Z1); tgt("1F living", 46, 16, Z1); tgt("1F dining", 18, 35, Z1)
    tgt("1F kitchen", 59, 27.5, Z1); tgt("stairs bottom", 25.3, 5.5, Z1); tgt("2F landing", 25.3, 32, Z2); tgt("2F lounge", 30.5, 4, Z2)
    tgt("2F master", 16, 9, Z2); tgt("2F kid", 14, 28, Z2); tgt("2F cinema", 45, 5, Z2); tgt("2F bath", 48, 25, Z2)


def facade():
    G = "House"
    # belt course between floors, cornice + crenellated parapet on the flat roof
    for (x0, y0, x1, y1) in ((-0.45, -0.45, BW + 0.45, 0.0), (-0.45, BD, BW + 0.45, BD + 0.45), (-0.45, 0.0, 0.0, BD), (BW, 0.0, BW + 0.45, BD)):
        h(x0, y0, ZC1 - 0.1, x1, y1, ZS + 0.1, "StoneC", G)
    for (x0, y0, x1, y1) in ((-0.6, -0.6, BW + 0.6, 0.2), (-0.6, BD - 0.2, BW + 0.6, BD + 0.6), (-0.6, 0.2, 0.2, BD - 0.2), (BW - 0.2, 0.2, BW + 0.6, BD - 0.2)):
        h(x0, y0, ZW - 0.8, x1, y1, ZW + 0.3, "StoneC", "HouseRoof")
    for (x0, y0, x1, y1) in ((-0.4, -0.4, BW + 0.4, 0.6), (-0.4, BD - 0.6, BW + 0.4, BD + 0.4), (-0.4, 0.6, 0.6, BD - 0.6), (BW - 0.6, 0.6, BW + 0.4, BD - 0.6)):
        h(x0, y0, ZW + 0.3, x1, y1, ZW + 2.8, "Brick", "HouseRoof", True, "Parapet")
    for (a0, a1, f0, f1, ax) in ((-0.4, BW + 0.4, -0.4, 0.6, "x"), (-0.4, BW + 0.4, BD - 0.6, BD + 0.4, "x"), (0.6, BD - 0.6, -0.4, 0.6, "y"), (0.6, BD - 0.6, BW - 0.6, BW + 0.4, "y")):
        n = int((a1 - a0) / 4.0)
        st = (a1 - a0) / n
        for i in range(n):
            u = a0 + i * st + (st - 2.2) / 2
            if ax == "x": h(u, f0, ZW + 2.8, u + 2.2, f1, ZW + 4.6, "StoneC", "HouseRoof")
            else: h(f0, u, ZW + 2.8, f1, u + 2.2, ZW + 4.6, "StoneC", "HouseRoof")
    h(0.6, 0.6, ZW + 0.5, BW - 0.6, BD - 0.6, ZW + 0.7, "RoofGrey", "HouseRoof")
    # quoins on the four corners
    for (cx, cy, sx, sy) in ((0, 0, 1, 1), (BW, 0, -1, 1), (0, BD, 1, -1), (BW, BD, -1, -1)):
        k = 0; z = Z1
        while z < ZW - 1.0:
            zt = min(z + 1.4, ZW - 0.9)
            if zt <= ZC1 - 0.1 or z >= ZS + 0.1:
                la, lb = (2.2, 1.2) if k % 2 else (1.2, 2.2)
                h(min(cx, cx + sx * la), min(cy - 0.15 * sy, cy), z, max(cx, cx + sx * la), max(cy - 0.15 * sy, cy), zt, "StoneC", G)
                h(min(cx - 0.15 * sx, cx), min(cy, cy + sy * lb), z, max(cx - 0.15 * sx, cx), max(cy, cy + sy * lb), zt, "StoneC", G)
            z += 1.6; k += 1
    # stone lintels + sills on the windows (S and N facades)
    for (u0, u1, zb, zt, side) in ((4, 10, Z1 + 3.5, Z1 + 9.5, "S"), (12, 18, Z1 + 3.5, Z1 + 9.5, "S"), (46, 52, Z1 + 3.5, Z1 + 9.5, "S"), (54, 60, Z1 + 3.5, Z1 + 9.5, "S"),
                                   (4, 10, Z2 + 3.5, Z2 + 9.5, "S"), (12, 18, Z2 + 3.5, Z2 + 9.5, "S"), (46, 52, Z2 + 3.5, Z2 + 9.5, "S"), (54, 60, Z2 + 3.5, Z2 + 9.5, "S"),
                                   (6, 16, Z1 + 3.5, Z1 + 9.5, "N"), (47, 57, Z1 + 3.5, Z1 + 9.5, "N"), (6, 16, Z2 + 3.5, Z2 + 9.5, "N"), (29, 37, Z2 + 3.5, Z2 + 9.5, "N"),
                                   (27, 37, Z1, Z1 + 10.0, "S"), (27, 37, Z2, Z2 + 10.0, "S")):
        if side == "S":
            h(u0 - 0.5, -0.5, zt, u1 + 0.5, 0.0, zt + 0.7, "StoneC", G)
            if zb > Z1 + 1 and zb != Z2: h(u0 - 0.3, -0.6, zb - 0.4, u1 + 0.3, 0.0, zb, "StoneC", G)
        else:
            h(u0 - 0.5, BD, zt, u1 + 0.5, BD + 0.5, zt + 0.7, "StoneC", G)
            h(u0 - 0.3, BD, zb - 0.4, u1 + 0.3, BD + 0.6, zb, "StoneC", G)
    # keystone + spatula crest above the front door
    h(30.5, -0.7, Z1 + 10.7, 33.5, 0.0, ZC1 - 0.1, "Stone", G)
    # wall lanterns
    for a in (11.0, 20.0, 44.0, 53.0):
        lantern("S", HX + a, HY, Z1 + 6.0)
    for a in (11.0, 53.0):
        lantern("S", HX + a, HY, Z2 + 6.0)
    for a in (11.0, 33.0, 53.0):
        lantern("N", HX + a + (3 if a == 33.0 else 0), HY + BD, Z1 + 6.0)
    # sparse protruding accent bricks on a grid (never over openings)
    r = random.Random(5)
    opens = [(4, 10), (12, 18), (27, 37), (46, 52), (54, 60), (10.4, 11.6), (19.4, 20.6), (21.5, 27.4), (36.6, 42.5), (43.4, 44.6), (52.4, 53.6)]
    for (zb0, zb1) in ((Z1 + 0.6, ZC1 - 0.6), (ZS + 0.6, ZW - 1.2)):
        for i in range(2, 30):
            for j in range(int((zb1 - zb0) / 0.9)):
                if r.random() > 0.11: continue
                u = i * 2.1 + (j % 2) * 1.05; z = zb0 + j * 0.9
                if any(a - 0.8 < u < b + 0.8 for (a, b) in opens) and z < zb0 + 10.5: continue
                if u + 1.9 > BW - 2.6: continue
                h(u, -0.12, z, u + 1.9, 0.0, z + 0.75, r.choice(["BrickB", "BrickC"]), G)
    # kitchen side door: canopy + lanterns + landing + steps
    sc.plate((HX + BW, HY + 24.0, Z1 + 11.0), (HX + BW, HY + 32.0, Z1 + 11.0), (HX + BW + 4.2, HY + 32.0, Z1 + 9.6), (HX + BW + 4.2, HY + 24.0, Z1 + 9.6), 0.35, "Black", G)
    for yy in (24.3, 31.4):
        beam((HX + BW, HY + yy, Z1 + 8.0), (HX + BW + 3.9, HY + yy, Z1 + 9.7), 0.25, "Iron", G)
    lantern("E", HX + BW, HY + 23.0, Z1 + 6.0); lantern("E", HX + BW, HY + 33.0, Z1 + 6.0)
    B(HX + BW, HY + 25.0, 0, HX + BW + 1.0, HY + 31.0, Z1, "StoneB", "Yard", True, "SideLanding")
    stairs(HX + BW + 1.0, HY + 25.0, HX + BW + 7.0, HY + 31.0, 0.0, Z1, 6, "W", "StoneB", "Yard", "StoneC", "SideStairs")
    # back steps from the hall back door into the backyard
    stairs(HX + 33.0, HY + BD + 0.3, HX + 39.0, HY + BD + 6.3, 0.0, Z1 - 0.06, 6, "S", "StoneB", "Yard", "StoneC", "BackStairs")


def front_stairs_balcony():
    G = "Yard"
    # landing in front of the double doors + wide steps + planters with hedge cubes
    B(234.0, 406.0, 0, 266.0, HY - 0.3, Z1 - 0.12, "StoneB", G)
    B(234.0, 406.0, Z1 - 0.12, 266.0, HY - 0.3, Z1, "StoneC", G)
    COL(234.0, 406.0, 0, 266.0, HY, Z1, "FrontLanding", G)
    stairs(240.0, 397.0, 260.0, 406.0, 0.0, Z1, 6, "N", "StoneB", G, "StoneC", "FrontStairs")
    for (x0, x1) in ((234.0, 240.0), (260.0, 266.0)):
        B(x0, 400.0, 0, x1, 406.0, Z1 + 0.5, "StoneB", G, True, "Planter")
        B(x0 - 0.2, 399.8, Z1 + 0.5, x1 + 0.2, 406.0, Z1 + 0.8, "StoneC", G)
        B(x0 + 0.4, 400.4, Z1 + 0.8, x1 - 0.4, 405.6, Z1 + 3.4, "HedgeB", "Bushes", True, "Hedge")
    # balcony over the entrance: stone slab, two columns, iron railing, flower boxes
    B(236.0, 408.0, ZC1, 264.0, HY, Z2, "StoneC", "House2F", True, "Balcony")
    for k in range(1, 8):
        B(237.0 + k * 3.25, 407.7, ZC1 - 1.2, 238.0 + k * 3.25, 408.6, ZC1, "StoneB", "House2F")
    for x0 in (236.3, 261.7):
        B(x0, 408.3, Z1, x0 + 2.0, 410.3, ZC1, "StoneC", "House", True, "Column")
        B(x0 - 0.3, 408.0, Z1, x0 + 2.3, 410.6, Z1 + 0.8, "Stone", "House")
        B(x0 - 0.3, 408.0, ZC1 - 0.8, x0 + 2.3, 410.6, ZC1, "Stone", "House")
    rail = [(236.0, 408.0, 264.0, 408.6), (236.0, 408.6, 236.6, HY - 0.2), (263.4, 408.6, 264.0, HY - 0.2)]
    for (x0, y0, x1, y1) in rail:
        B(x0, y0, Z2 + 3.2, x1, y1, Z2 + 3.6, "WoodDark", "House2F")
        B(x0, y0, Z2, x1, y1, Z2 + 0.4, "Iron", "House2F")
        COL(x0, y0, Z2, x1, y1, Z2 + 3.6, "BalconyRail", "House2F")
        along_x = (x1 - x0) > (y1 - y0)
        a0, a1 = (x0, x1) if along_x else (y0, y1)
        n = int((a1 - a0) / 0.9)
        for i in range(1, n):
            u = a0 + i * (a1 - a0) / n
            if along_x: B(u - 0.12, y0 + 0.18, Z2 + 0.4, u + 0.12, y1 - 0.18, Z2 + 3.2, "Iron", "House2F")
            else: B(x0 + 0.18, u - 0.12, Z2 + 0.4, x1 - 0.18, u + 0.12, Z2 + 3.2, "Iron", "House2F")
    r = random.Random(17)
    for (a0, a1) in ((237.0, 245.0), (255.0, 263.0)):
        B(a0, 407.2, Z2 + 2.2, a1, 408.0, Z2 + 3.2, "WoodMid", "House2F")
        a = a0
        while a < a1 - 0.3:
            B(a + 0.05, 407.3, Z2 + 3.2, a + 0.55, 407.9, Z2 + 3.6 + r.uniform(0, 0.4), r.choice(["FlowerRed", "FlowerYellow", "FlowerPink", "Leaf"]), "House2F")
            a += 0.6
    K.string_lights((236.4, 408.3, ZC1 - 0.3), (263.6, 408.3, ZC1 - 0.3), 10, 0.9)
    TARGETS["2F balcony"] = (250.0, 411.0, Z2)
    TARGETS["front landing"] = (250.0, 409.0, Z1)


def smoker_tower(cx, cy, side):
    G = "House"
    ap = TR * math.cos(math.radians(11.25))
    sc.prism(poly16(cx, cy, TR + 0.4), 0, Z1 + 0.5, "StoneB", G, False)
    sc.prism(poly16(cx, cy, TR), Z1 + 0.5, 40.0, "Black", G, False)
    for zb in (9.0, 21.0, 33.0):
        sc.prism(poly16(cx, cy, TR + 0.35), zb, zb + 0.9, "Steel", G, False)
        for i in range(16):   # rivets
            t = math.radians(360.0 * i / 16)
            px, py = cx + (TR + 0.42) * math.cos(t), cy + (TR + 0.42) * math.sin(t)
            if side == "W" and px > HX - 0.3: continue
            if side == "E" and px < HX + BW + 0.3: continue
            B(px - 0.18, py - 0.18, zb + 1.1, px + 0.18, py + 0.18, zb + 1.45, "Iron", G)
    sc.prism(poly16(cx, cy, TR + 0.8), 40.0, 41.5, "RoofRed", G, False)
    for i in range(8):   # red merlons on the crown
        t = math.radians(360.0 * i / 8 + 22.5)
        px, py = cx + (TR + 0.1) * math.cos(t), cy + (TR + 0.1) * math.sin(t)
        B(px - 1.1, py - 1.1, 41.5, px + 1.1, py + 1.1, 43.4, "RoofRedB", G)
    sc.prism(poly16(cx, cy, TR - 0.4), 41.5, 42.0, "Iron", G, False)
    C(cx, cy, 42.0, 47.5, 3.0, "Iron", G, 12); C(cx, cy, 47.5, 48.6, 3.7, "Black", G, 12)
    C(cx, cy, 48.6, 48.68, 2.5, "Coal", G, 12)
    K.smoke(cx, cy, 49.2, 6, 1.4, 31 if side == "W" else 37)
    # gauge (thermometer dial) + fire window on the south face, small gauge on the outer face
    yf = cy - ap
    hcyl("y", yf - 0.5, yf + 0.3, cx, 30.0, 2.9, "Chrome", G, 16)
    hcyl("y", yf - 0.75, yf - 0.45, cx, 30.0, 2.5, "White", G, 16)
    for k in range(9):
        t = math.radians(200 - k * 27.5)
        B(cx + 2.0 * math.cos(t) - 0.12, yf - 0.85, 30.0 + 2.0 * math.sin(t) - 0.12, cx + 2.0 * math.cos(t) + 0.12, yf - 0.74, 30.0 + 2.0 * math.sin(t) + 0.12, "Black" if k % 4 else "Red", G)
    beam((cx, yf - 0.9, 30.0), (cx + 1.35, yf - 0.9, 31.35), 0.22, "Red", G)
    hcyl("y", yf - 1.0, yf - 0.75, cx, 30.0, 0.35, "Black", G, 8)
    FB("S", cx, yf, -1.55, -0.05, 17.4, 1.55, 0.3, 21.6, "Iron", G)
    FB("S", cx, yf, -1.2, 0.3, 17.8, 1.2, 0.36, 21.2, "Fire", G)
    for a in (-0.6, 0.0, 0.6):
        FB("S", cx, yf, a - 0.1, 0.36, 17.8, a + 0.1, 0.52, 21.2, "Iron", G)
    FB("S", cx, yf, -1.55, 0.36, 17.4, 1.55, 0.52, 17.8, "Iron", G); FB("S", cx, yf, -1.55, 0.36, 21.2, 1.55, 0.52, 21.6, "Iron", G)
    sc.anchor("GrillFire", (cx, yf - 1.0, 19.5), range=16)
    of = "W" if side == "W" else "E"
    xo = cx - ap if side == "W" else cx + ap
    FB(of, xo, cy, -1.4, -0.05, 12.0, 1.4, 0.3, 15.4, "Iron", G)
    FB(of, xo, cy, -1.1, 0.3, 12.4, 1.1, 0.36, 15.0, "Fire", G)
    for a in (-0.5, 0.5):
        FB(of, xo, cy, a - 0.1, 0.36, 12.4, a + 0.1, 0.5, 15.0, "Iron", G)
    COL(cx - TR, cy - TR, 0, cx + TR, cy + TR, 48.6, "SmokerTower", G)


def roof_grill_lid():
    G = "HouseRoof"
    cx, cy = HX + BW / 2, HY + BD / 2
    rx, ry = 22.0, 16.0
    zb = ZW + 0.7
    sc.prism(ellipse(cx, cy, rx + 0.6, ry + 0.6), zb, zb + 0.8, "Iron", G, False)
    sc.prism(ellipse(cx, cy, rx - 1.2, ry - 1.2), zb + 0.8, zb + 3.3, "Lamp", G, False)
    n = 48
    for i in range(n):
        t = 2 * math.pi * (i + 0.5) / n
        px, py = cx + (rx - 0.5) * math.cos(t), cy + (ry - 0.5) * math.sin(t)
        B(px - 0.35, py - 0.35, zb + 0.8, px + 0.35, py + 0.35, zb + 3.3, "Iron", G)
    for k in range(6):
        sc.anchor("GrillGlow", (cx + rx * 0.85 * math.cos(k * math.pi / 3), cy + ry * 0.85 * math.sin(k * math.pi / 3), zb + 2.0), range=26)
    zl = zb + 3.3
    sc.prism(ellipse(cx, cy, rx + 0.4, ry + 0.4), zl, zl + 1.0, "RedDark", G, False)
    rz = 12.0
    ball(cx, cy, zl + 0.9, rx, "RoofRed", G, 0.0, 90.0, 36, 9, rz, 1.0, ry / rx)
    # handle
    hz = zl + 0.9 + rz * math.sqrt(1 - (9.0 / rx) ** 2)
    for dx in (-9.0, 9.0):
        C(cx + dx, cy, hz - 1.0, hz + 3.6, 0.7, "Chrome", G, 10)
    B(cx - 10.6, cy - 1.0, hz + 3.6, cx + 10.6, cy + 1.0, hz + 5.2, "Black", G)
    # vent on the south slope with three holes
    la = math.radians(38.0)
    p = (cx, cy - ry * math.cos(la), zl + 0.9 + rz * math.sin(la))
    nrm = (0.0, -(math.cos(la)) / ry, math.sin(la) / rz)
    l = math.sqrt(sum(v * v for v in nrm)); nrm = tuple(v / l for v in nrm)
    p = tuple(p[k] - nrm[k] * 0.15 for k in range(3))
    u, v, nn = disc(p, nrm, 2.8, 0.55, "Chrome", G, 20)
    for k in range(3):
        t = 2 * math.pi * k / 3 + math.pi / 2
        q = tuple(p[j] + nn[j] * 0.5 + 1.3 * (math.cos(t) * u[j] + math.sin(t) * v[j]) for j in range(3))
        disc(q, nn, 0.55, 0.12, "Iron", G, 10)
    COL(cx - rx, cy - ry, zb, cx + rx, cy + ry, zl + 0.9 + rz * 0.8, "GrillLid", G)


# ------------------------------------------------------------------ interiors
def interior_1f():
    G = "HouseInterior"
    X, Y = HX, HY
    # stairs along the west wall of the hall + railing
    stairs(X + 22.8, Y + 8.0, X + 27.8, Y + 28.0, Z1, Z2, 16, "N", "WoodMid", G, "WoodLight")
    beam((X + 27.95, Y + 8.0, Z1 + 4.2), (X + 27.95, Y + 28.0, Z2 + 3.4), 0.3, "WoodDark", G)
    for i in range(0, 16, 2):
        yy = 8.0 + (i + 0.5) * 1.25; zz = Z1 + (i + 1) * (Z2 - Z1) / 16
        h(27.82, yy - 0.12, zz, 28.08, yy + 0.12, zz + 3.3, "White", G)
    hc(27.8, 8.0, Z1, 28.1, 28.0, Z2, "StairSide", G)
    # --- trophy hall "HALL OF FLAME" (new room): fireplace, golden trophies, banners
    h(0.8, 6.0, Z1, 3.9, 14.0, Z1 + 0.3, "StoneC", G)
    h(0.8, 6.5, Z1 + 0.3, 2.8, 8.0, Z1 + 5.5, "BrickC", G); h(0.8, 12.0, Z1 + 0.3, 2.8, 13.5, Z1 + 5.5, "BrickC", G)
    h(0.8, 6.5, Z1 + 5.5, 2.8, 13.5, Z1 + 8.0, "BrickC", G); h(0.8, 8.0, Z1 + 0.3, 1.0, 12.0, Z1 + 5.5, "Black", G)
    h(0.8, 6.0, Z1 + 8.0, 3.4, 14.0, Z1 + 8.5, "WoodDark", G)
    for k in range(4):
        hcyl("y", Y + 8.6, Y + 11.4, X + 1.4 + k * 0.35, Z1 + 0.65 + (k % 2) * 0.25, 0.3, "WoodMid", G, 6)
    h(1.2, 8.7, Z1 + 0.95, 2.4, 11.3, Z1 + 2.6, "Fire", G); h(1.4, 9.3, Z1 + 2.6, 2.1, 10.7, Z1 + 3.6, "FireY", G)
    hc(0.8, 6.0, Z1, 3.9, 14.0, Z1 + 8.5, "Fireplace", G)
    sc.anchor("FireplaceFire", (X + 2.0, Y + 10.0, Z1 + 2.0), range=18)
    h(0.8, 6.8, Z1 + 9.0, 1.0, 13.2, Z1 + 11.8, "WoodDark", G)
    icon(K.spatulas_icon(), {"s": "Gold"}, X + 1.0, Y + 10.0, Z1 + 10.4, 0.17, "E", 0.0, 0.1, G)
    sofa(X + 9.0, Y + 6.5, Z1, "W", 4.2, "ClothRed", "ClothYellow", G)
    sofa(X + 9.0, Y + 13.5, Z1, "W", 4.2, "ClothRed", "ClothYellow", G)
    rug(X + 3.9, Y + 4.5, X + 11.4, Y + 15.5, Z1, "ClothRed", "ClothYellow", G)
    h(13.6, 8.5, Z1, 16.6, 11.5, Z1 + 2.6, "StoneC", G, True, "Pedestal"); h(13.4, 8.3, Z1 + 2.6, 16.8, 11.7, Z1 + 2.9, "Stone", G)
    trophy(X + 15.1, Y + 10.0, Z1 + 2.9, 2.4, G)
    shelf(X + 5.0, Y + 19.0, Z1, "S", 7.0, 7.5, 1.4, 61, G, "WoodDark", "none")
    shelf(X + 21.0, Y + 13.5, Z1, "W", 8.0, 7.5, 1.4, 62, G, "WoodDark", "none")
    for k in range(3):
        for j in range(3):
            trophy(X + 2.8 + j * 2.2, Y + 19.0, Z1 + 0.25 + k * 2.42, 0.8 if (k + j) % 2 else 0.95, G)
            trophy(X + 21.0, Y + 11.0 + j * 2.5, Z1 + 0.25 + k * 2.42, 0.95 if (k + j) % 2 else 0.8, G)
    text("HALL OF FLAME", X + 11.0, Y + 19.7, Z1 + 9.8, 0.2, "S", "Gold", 0.0, 0.1, G)
    banner("E", X + 0.8, Y + 3.0, Z1 + 10.5, 0.24, 0.0, G); banner("E", X + 0.8, Y + 17.0, Z1 + 10.5, 0.24, 0.0, G)
    picture(X + 11.0, Y + 0.8, Z1 + 11.6, "N", 3.0, 2.0, "flame", G)
    ceiling_lamp(X + 11, Y + 10, ZC1, G)
    # --- great hall with the stairs
    rug(X + 29.5, Y + 2.5, X + 40.5, Y + 25.0, Z1, "ClothRed", "ClothYellow", G)
    picture(X + 41.7, Y + 19.0, Z1 + 7.5, "W", 6.0, 4.6, "dad", G)
    h(40.2, 15.5, Z1, 41.7, 22.5, Z1 + 3.0, "WoodMid", G, True, "Console"); h(40.1, 15.4, Z1 + 3.0, 41.7, 22.6, Z1 + 3.3, "WoodDark", G)
    trophy(X + 41.0, Y + 17.0, Z1 + 3.3, 1.0, G); plant(X + 41.0, Y + 21.0, Z1 + 3.3, G, 0.7)
    plant(X + 40.6, Y + 1.6, Z1, G, 1.3); plant(X + 29.2, Y + 36.2, Z1, G, 1.3)
    banner("S", X + 30.0, Y + BD - 0.8, Z1 + 10.5, 0.24, 0.0, G)
    # jukebox by the back door
    h(39.2, 35.4, Z1, 41.6, 37.2, Z1 + 5.2, "Red", G, True, "Jukebox"); h(39.4, 35.3, Z1 + 1.0, 41.4, 35.4, Z1 + 4.4, "Lamp", G)
    h(39.1, 35.2, Z1 + 5.2, 41.7, 37.2, Z1 + 5.6, "Gold", G)
    ceiling_lamp(X + 34.5, Y + 12, ZC1, G); ceiling_lamp(X + 34.5, Y + 30, ZC1, G)
    # --- living room
    tv(X + 62.3, Y + 10.0, Z1, "W", G)
    sofa(X + 52.0, Y + 10.0, Z1, "E", 9.0, "ClothRed", "ClothWhite", G)
    rug(X + 48.0, Y + 3.0, X + 61.0, Y + 16.5, Z1, "Cloth", "ClothWhite", G)
    table(X + 55.4, Y + 7.6, X + 58.4, Y + 12.4, Z1, 1.7, "WoodLight", "WoodDark", G)
    K.plate(X + 56.9, Y + 9.0, Z1 + 1.7); K.burger(X + 56.9, Y + 9.0, Z1 + 1.8, 0.7); K.cup(X + 56.9, Y + 11.4, Z1 + 1.7, "Red")
    sofa(X + 58.0, Y + 17.6, Z1, "S", 5.0, "ClothYellow", "ClothWhite", G)
    floor_lamp(X + 44.0, Y + 2.0, Z1, G); plant(X + 62.2, Y + 1.8, Z1, G, 1.2)
    picture(X + 52.0, Y + 19.7, Z1 + 8.5, "S", 5.0, 3.6, "grill", G)
    ceiling_lamp(X + 53, Y + 10, ZC1, G)
    # --- dining room
    table(X + 4.0, Y + 26.0, X + 16.0, Y + 31.0, Z1, 3.0, "WoodLight", "WoodDark", G)
    for a in (6.0, 10.0, 14.0):
        chair(X + a, Y + 24.9, Z1, "N", g=G); chair(X + a, Y + 32.1, Z1, "S", g=G)
        K.plate(X + a, Y + 27.0, Z1 + 3.0); K.plate(X + a, Y + 30.0, Z1 + 3.0)
    chair(X + 2.9, Y + 28.5, Z1, "E", g=G); chair(X + 17.1, Y + 28.5, Z1, "W", g=G)
    C(X + 10.0, Y + 28.5, Z1 + 3.0, Z1 + 3.15, 1.4, "White", G, 10)
    for k in range(4):
        hcyl("x", X + 9.2, X + 10.8, Y + 28.0 + k * 0.33, Z1 + 3.3, 0.15, "Sausage", G, 6)
    K.burger(X + 7.5, Y + 28.5, Z1 + 3.0, 0.9); K.burger(X + 12.5, Y + 28.5, Z1 + 3.0, 0.9)
    h(11.6, 28.8, Z1 + 3.0, 12.0, 29.2, Z1 + 4.0, "Ketchup", G); h(8.0, 28.8, Z1 + 3.0, 8.4, 29.2, Z1 + 4.0, "Mustard", G)
    h(2.5, 35.6, Z1, 9.5, 37.2, Z1 + 3.0, "WoodMid", G, True, "Sideboard"); h(2.4, 35.5, Z1 + 3.0, 9.6, 37.2, Z1 + 3.25, "WoodDark", G)
    cabinet_doors("S", X + 6.0, Y + 35.6, 7.0, Z1, 3, G, "Gold")
    trophy(X + 3.6, Y + 36.4, Z1 + 3.25, 1.0, G); plant(X + 8.4, Y + 36.4, Z1 + 3.25, G, 0.7)
    rug(X + 2.0, Y + 23.0, X + 18.0, Y + 34.0, Z1, "ClothYellow", "ClothRed", G)
    picture(X + 21.7, Y + 25.0, Z1 + 7.5, "W", 4.2, 3.4, "grill", G)
    ceiling_lamp(X + 10, Y + 28.5, ZC1, G)
    # --- kitchen
    counter(X + 47.0, Y + 35.3, X + 58.0, Y + 37.2, Z1, G)
    cabinet_doors("S", X + 52.5, Y + 35.3, 11.0, Z1, 5, G)
    h(51.0, 35.6, Z1 + 3.2, 55.0, 36.9, Z1 + 3.26, "Steel", G); h(52.9, 36.7, Z1 + 3.26, 53.1, 36.95, Z1 + 4.4, "Chrome", G)
    stove(X + 60.6, Y + 35.7, Z1, "S", G)
    fridge(X + 44.6, Y + 35.6, Z1, "S", G)
    counter(X + 50.0, Y + 27.0, X + 57.0, Y + 30.5, Z1, G, "Red", "StoneC")
    for a in (51.2, 53.5, 55.8):
        C(X + a, Y + 25.9, Z1, Z1 + 2.6, 0.18, "Chrome", G, 6); C(X + a, Y + 25.9, Z1 + 2.6, Z1 + 2.9, 0.7, "ClothRed", G, 8)
    K.plate(X + 52.0, Y + 28.6, Z1 + 3.2); K.burger(X + 52.0, Y + 28.6, Z1 + 3.3, 0.7); K.cup(X + 55.0, Y + 28.6, Z1 + 3.2, "Yellow")
    h(61.5, 21.0, Z1, BW - 0.8, 24.0, Z1 + 3.0, "WoodLight", G, True, "ButcherBlock"); h(61.4, 20.9, Z1 + 3.0, BW - 0.8, 24.1, Z1 + 3.35, "WoodMid", G)
    h(61.9, 21.6, Z1 + 3.35, 62.9, 23.2, Z1 + 3.6, "Meat", G)
    shelf(X + 56.0, Y + 21.0, Z1, "N", 5.0, 7.5, 1.4, 31, G, "WoodMid", "jars")
    for i, m in enumerate(["Ketchup", "Mustard", "Green"]):   # sauce row on the counter end
        h(56.0 + i * 0.6, 36.2, Z1 + 3.2, 56.4 + i * 0.6, 36.6, Z1 + 4.1, m, G)
    text("EAT MEAT", X + 52.5, Y + BD - 0.8, Z1 + 10.6, 0.2, "S", "Red", 0.0, 0.1, G)
    rug(X + 49.0, Y + 31.6, X + 58.0, Y + 34.4, Z1, "ClothGreen", "ClothWhite", G)
    ceiling_lamp(X + 53.5, Y + 28.5, ZC1, G)


def interior_2f():
    G = "House2F"
    X, Y = HX, HY
    # railing around the stair well
    h(27.8, 8.0, Z2 + 3.2, 28.1, 28.0, Z2 + 3.5, "WoodDark", G); h(27.8, 8.0, Z2 + 0.3, 28.1, 28.0, Z2 + 0.55, "WoodDark", G)
    h(22.8, 7.7, Z2 + 3.2, 27.8, 8.0, Z2 + 3.5, "WoodDark", G); h(22.8, 7.7, Z2 + 0.3, 27.8, 8.0, Z2 + 0.55, "WoodDark", G)
    for i in range(20):
        yy = 8.5 + i * 1.0
        h(27.84, yy - 0.12, Z2 + 0.55, 28.06, yy + 0.12, Z2 + 3.2, "White", G)
    for i in range(5):
        xx = 23.3 + i * 1.0
        h(xx - 0.12, 7.74, Z2 + 0.55, xx + 0.12, 7.96, Z2 + 3.2, "White", G)
    hc(27.8, 7.7, ZS, 28.15, 28.0, Z2 + 3.5, "StairRail", G); hc(22.8, 7.7, ZS, 27.8, 8.0, Z2 + 3.5, "StairRail", G)
    # --- lounge / dad's office with a pool table
    table(X + 30.0, Y + 33.6, X + 38.0, Y + 36.4, Z2, 3.0, "WoodLight", "WoodDark", G)
    h(33.2, 35.6, Z2 + 3.0, 34.8, 35.9, Z2 + 4.6, "Black", G); h(33.3, 35.5, Z2 + 3.1, 34.7, 35.6, Z2 + 4.5, "Screen", G)
    K.cup(X + 36.3, Y + 34.6, Z2 + 3.0, "Red")
    chair(X + 34.0, Y + 32.1, Z2, "N", g=G)
    h(33.0, 12.0, Z2, 37.6, 20.0, Z2 + 2.4, "WoodDark", G, True, "PoolTable")
    h(32.8, 11.8, Z2 + 2.4, 37.8, 20.2, Z2 + 2.8, "WoodMid", G); h(33.3, 12.3, Z2 + 2.6, 37.3, 19.7, Z2 + 2.85, "ClothGreen", G)
    for (bx, by, m) in ((34.2, 14.0, "Red"), (35.0, 14.6, "Yellow"), (35.8, 14.0, "Blue"), (35.0, 17.6, "White"), (34.4, 15.2, "Black")):
        ball(X + bx, Y + by, Z2 + 3.15, 0.3, m, G, seg=8, rings=4)
    beam((X + 36.2, Y + 18.6, Z2 + 3.0), (X + 33.9, Y + 21.4, Z2 + 3.1), 0.12, "WoodLight", G)
    shelf(X + 41.0, Y + 13.5, Z2, "W", 5.0, 8.0, 1.4, 41, G)
    shelf(X + 41.0, Y + 19.5, Z2, "W", 5.0, 6.0, 1.4, 43, G, "WoodDark", "none")
    for k in range(3):
        for j in range(2):
            trophy(X + 41.0, Y + 18.3 + j * 2.4, Z2 + 0.25 + k * 1.92, 0.8, G)
    shelf(X + 41.0, Y + 25.5, Z2, "W", 5.0, 8.0, 1.4, 44, G)
    picture(X + 30.0, Y + BD - 0.8, Z2 + 7.4, "S", 4.6, 3.6, "dad", G)
    floor_lamp(X + 39.6, Y + 2.0, Z2, G); plant(X + 29.0, Y + 1.8, Z2, G, 1.2)
    ceiling_lamp(X + 35, Y + 16, ZW, G); ceiling_lamp(X + 34, Y + 31, ZW, G)
    # --- master bedroom
    bed(X + 6.6, Y + 11.0, Z2, "E", 7.4, 10.0, "ClothRed", G)
    for a in (5.3, 16.7):
        table(X + 1.2, Y + a - 1.0, X + 3.2, Y + a + 1.0, Z2, 2.4, "WoodLight", "WoodMid", G)
        C(X + 2.2, Y + a, Z2 + 2.4, Z2 + 3.0, 0.2, "Iron", G, 6); C(X + 2.2, Y + a, Z2 + 3.0, Z2 + 3.9, 0.55, "Lamp", G, 8)
    wardrobe(X + 9.0, Y + 18.7, Z2, "S", 5.6, G)
    h(13.0, 0.8, Z2, 18.0, 2.5, Z2 + 3.2, "WoodMid", G, True, "Dresser"); h(12.9, 0.8, Z2 + 3.2, 18.1, 2.6, Z2 + 3.45, "WoodDark", G)
    cabinet_doors("N", X + 15.5, Y + 2.5, 5.0, Z2, 2, G, "Gold")
    rug(X + 12.5, Y + 6.0, X + 20.5, Y + 16.0, Z2, "ClothYellow", "ClothRed", G)
    picture(X + 0.8, Y + 11.0, Z2 + 8.4, "E", 6.0, 3.6, "grill", G)
    plant(X + 20.4, Y + 18.4, Z2, G, 1.2); ceiling_lamp(X + 11, Y + 10, ZW, G)
    # --- kid's room
    bed(X + 5.0, Y + 27.0, Z2, "N", 5.0, 9.6, "Cloth", G)
    table(X + 12.0, Y + 35.0, X + 18.0, Y + BD - 0.8, Z2, 3.0, "WoodLight", "Blue", G)
    chair(X + 15.0, Y + 33.8, Z2, "N", "WoodMid", "Cloth", G)
    h(13.0, 35.6, Z2 + 3.0, 14.4, 36.8, Z2 + 3.06, "Paper", G); h(16.4, 35.8, Z2 + 3.0, 16.8, 36.2, Z2 + 3.9, "Red", G)
    h(9.0, 21.2, Z2, 12.6, 23.6, Z2 + 2.2, "Red", G, True, "ToyChest"); h(8.9, 21.1, Z2 + 2.2, 12.7, 23.7, Z2 + 2.6, "Yellow", G)
    ball(X + 13.5, Y + 27.0, Z2 + 0.9, 0.9, "White", G, seg=8, rings=4); ball(X + 10.5, Y + 30.5, Z2 + 0.7, 0.7, "Orange", G, seg=8, rings=4)
    K.kettle_grill(X + 16.5, Y + 24.5, 0.45, "Blue", False, True, 2, 0, G)
    shelf(X + 21.0, Y + 25.0, Z2, "W", 6.0, 6.0, 1.3, 51, G, "White")
    rug(X + 8.5, Y + 25.5, X + 19.0, Y + 32.5, Z2, "Cloth", "ClothYellow", G)
    text("BBQ KID", X + 15.0, Y + BD - 0.8, Z2 + 10.2, 0.16, "S", "Red", 0.0, 0.1, G)
    picture(X + 0.8, Y + 35.0, Z2 + 7.4, "E", 3.0, 2.8, "kid", G)
    ceiling_lamp(X + 11, Y + 29, ZW, G)
    # --- cinema / game room (new room)
    h(62.9, 3.0, Z2 + 1.8, BW - 0.8, 17.0, Z2 + 10.2, "Black", G)
    h(62.74, 3.4, Z2 + 2.2, 62.9, 16.6, Z2 + 9.8, "Screen", G)
    icon(K.GRILL_ICON, {"1": "Fire"}, X + 62.74, Y + 10.0, Z2 + 6.0, 0.42, "W", 0.0, 0.06, G)
    for (y0, y1) in ((1.2, 3.0), (17.0, 18.8)):
        h(62.2, y0, Z2, BW - 0.8, y1, Z2 + 11.0, "ClothRed", G)
    sofa(X + 56.0, Y + 10.0, Z2, "E", 9.0, "ClothRed", "Black", G)
    h(47.0, 5.0, Z2, 52.0, 15.0, Z2 + 1.0, "ClothRed", G, True, "Riser")
    sofa(X + 49.5, Y + 10.0, Z2 + 1.0, "E", 9.0, "ClothRed", "Black", G)
    for a in (45.6, 49.4):   # arcade cabinets on the partition
        h(a - 1.3, 17.6, Z2, a + 1.3, 19.7, Z2 + 6.6, "Purple", G, True, "Arcade")
        h(a - 1.1, 17.5, Z2 + 3.6, a + 1.1, 17.6, Z2 + 5.8, "Screen", G); h(a - 1.3, 16.8, Z2 + 2.8, a + 1.3, 17.6, Z2 + 3.4, "Black", G)
        h(a - 0.6, 17.1, Z2 + 3.4, a - 0.4, 17.3, Z2 + 3.9, "Red", G); h(a + 0.2, 17.0, Z2 + 3.4, a + 0.6, 17.4, Z2 + 3.55, "Yellow", G)
        h(a - 1.2, 17.45, Z2 + 5.9, a + 1.2, 17.6, Z2 + 6.5, "Lamp", G)
    h(60.2, 17.0, Z2, 62.2, 19.0, Z2 + 3.4, "Red", G, True, "Popcorn"); h(60.3, 17.1, Z2 + 3.4, 62.1, 18.9, Z2 + 5.8, "Glass", "Glass")
    h(60.5, 17.3, Z2 + 3.4, 61.9, 18.7, Z2 + 4.8, "ClothYellow", G); h(60.1, 16.9, Z2 + 5.8, 62.3, 19.1, Z2 + 6.4, "Red", G)
    text("DAD CINEMA", X + 52.0, Y + 0.8, Z2 + 10.4, 0.18, "N", "Gold", 0.0, 0.1, G)
    sc.anchor("RoomLight", (X + 53, Y + 10, ZW - 2.0), range=26)
    # --- bathroom with a hot tub
    h(52.0, 21.4, Z2, 62.6, 30.0, Z2 + 2.6, "White", G, True, "HotTub"); h(52.6, 22.0, Z2 + 1.4, 62.0, 29.4, Z2 + 2.5, "Water", "Water")
    ball(X + 57.0, Y + 25.7, Z2 + 2.7, 0.55, "Yellow", G, seg=8, rings=4)
    h(46.0, 34.6, Z2, 48.2, 37.2, Z2 + 1.6, "White", G, True, "Toilet"); h(46.0, 36.4, Z2 + 1.6, 48.2, 37.2, Z2 + 4.0, "White", G)
    h(46.1, 34.7, Z2 + 1.6, 48.1, 36.4, Z2 + 1.8, "WallGrey", G)
    counter(X + 50.0, Y + 35.4, X + 54.0, Y + BD - 0.8, Z2, G, "TileB", "White")
    C(X + 52.0, Y + 36.3, Z2 + 3.2, Z2 + 3.3, 0.7, "WallGrey", G, 8); h(51.9, 36.8, Z2 + 3.2, 52.1, 37.0, Z2 + 4.2, "Chrome", G)
    h(50.2, 37.04, Z2 + 4.8, 53.8, 37.2, Z2 + 8.6, "White", G); h(50.5, 36.96, Z2 + 5.1, 53.5, 37.04, Z2 + 8.3, "SkyBlue", G)
    h(56.0, 37.0, Z2 + 5.0, 61.0, 37.2, Z2 + 5.25, "Chrome", G); h(56.4, 36.9, Z2 + 2.6, 58.4, 37.0, Z2 + 5.0, "ClothRed", G); h(58.8, 36.9, Z2 + 3.2, 60.6, 37.0, Z2 + 5.0, "ClothWhite", G)
    rug(X + 45.0, Y + 23.0, X + 50.5, Y + 28.0, Z2, "ClothWhite", "Cloth", G)
    ceiling_lamp(X + 53, Y + 29, ZW, G)


# ------------------------------------------------------------------ courtyard wall
def wall_seg(x0, y0, x1, y1, hb, outer):
    G = "CastleWall"
    B(x0, y0, 0, x1, y1, hb, "Brick", G)
    B(x0 - 0.25, y0 - 0.25, 0, x1 + 0.25, y1 + 0.25, 1.2, "StoneB", G)
    B(x0 - 0.3, y0 - 0.3, hb, x1 + 0.3, y1 + 0.3, hb + 0.6, "StoneC", G)
    along_x = (x1 - x0) > (y1 - y0)
    a0, a1 = (x0, x1) if along_x else (y0, y1)
    n = max(1, int((a1 - a0) / 4.0)); st = (a1 - a0) / n
    for i in range(n):
        u = a0 + i * st + (st - 2.4) / 2
        if along_x:
            f0, f1 = (y0 - 0.3, y0 + 1.1) if outer == "S" else (y1 - 1.1, y1 + 0.3)
            B(u, f0, hb + 0.6, u + 2.4, f1, hb + 2.6, "StoneC", G)
        else:
            f0, f1 = (x0 - 0.3, x0 + 1.1) if outer == "W" else (x1 - 1.1, x1 + 0.3)
            B(f0, u, hb + 0.6, f1, u + 2.4, hb + 2.6, "StoneC", G)
    COL(x0 - 0.3, y0 - 0.3, 0, x1 + 0.3, y1 + 0.3, hb + 2.6, "CastleWall", G)


def tower(x0, y0, x1, y1, hb, ban=None, flag=True, quoins=True):
    G = "CastleWall"
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    B(x0, y0, 0, x1, y1, hb, "Brick", G)
    B(x0 - 0.3, y0 - 0.3, 0, x1 + 0.3, y1 + 0.3, 1.6, "StoneB", G)
    B(x0 - 0.4, y0 - 0.4, hb - 2.4, x1 + 0.4, y1 + 0.4, hb - 1.8, "StoneC", G)
    B(x0 - 0.7, y0 - 0.7, hb, x1 + 0.7, y1 + 0.7, hb + 0.9, "StoneC", G)
    for (ax, f) in (("x", y0 - 0.7), ("x", y1 - 0.7), ("y", x0 - 0.7), ("y", x1 - 0.7)):
        a0, a1 = (x0 - 0.7, x1 + 0.7) if ax == "x" else (y0 + 0.7, y1 - 0.7)
        n = max(2, int((a1 - a0) / 3.4)); st = (a1 - a0) / n
        for i in range(n):
            u = a0 + i * st + (st - 1.9) / 2
            if ax == "x": B(u, f, hb + 0.9, u + 1.9, f + 1.4, hb + 3.0, "StoneC", G)
            else: B(f, u, hb + 0.9, f + 1.4, u + 1.9, hb + 3.0, "StoneC", G)
    B(x0 + 0.7, y0 + 0.7, hb + 0.9, x1 - 0.7, y1 - 0.7, hb + 1.1, "StoneB", G)
    # quoins
    for (qx, qy, sx, sy) in [] if not quoins else ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        k = 0; z = 1.8
        while z < hb - 3.0:
            la, lb = (1.8, 1.0) if k % 2 else (1.0, 1.8)
            B(min(qx, qx + sx * la), min(qy - 0.12 * sy, qy), z, max(qx, qx + sx * la), max(qy - 0.12 * sy, qy), z + 1.2, "StoneC", G)
            B(min(qx - 0.12 * sx, qx), min(qy, qy + sy * lb), z, max(qx - 0.12 * sx, qx), max(qy, qy + sy * lb), z + 1.2, "StoneC", G)
            z += 1.4; k += 1
    # lit window + arrow slits
    wz = hb - 7.0
    FB("S", cx, y0, -1.3, -0.05, wz, 1.3, 0.12, wz + 3.0, "WindowWarm", G)
    FB("S", cx, y0, -1.7, -0.05, wz - 0.4, 1.7, 0.3, wz, "StoneC", G); FB("S", cx, y0, -1.7, -0.05, wz + 3.0, 1.7, 0.3, wz + 3.5, "StoneC", G)
    FB("S", cx, y0, -1.7, -0.05, wz, -1.3, 0.3, wz + 3.0, "StoneC", G); FB("S", cx, y0, 1.3, -0.05, wz, 1.7, 0.3, wz + 3.0, "StoneC", G)
    FB("S", cx, y0, -0.08, 0.0, wz, 0.08, 0.2, wz + 3.0, "WoodDark", G)
    for f, ox, oy in (("W", x0, cy), ("E", x1, cy), ("N", cx, y1)):
        FB(f, ox, oy, -0.35, -0.05, wz, 0.35, 0.08, wz + 2.6, "Black", G)
    if ban:
        banner("S", cx, y0, wz - 1.2, 0.3, 0.3, "Signs")
    if flag:
        C(cx, cy, hb + 1.1, hb + 10.5, 0.22, "Iron", G, 6)
        B(cx - 0.35, cy - 0.35, hb + 10.5, cx + 0.35, cy + 0.35, hb + 11.0, "Gold", G)
        B(cx + 0.22, cy - 0.12, hb + 7.6, cx + 5.4, cy + 0.12, hb + 10.2, "Red", "Signs")
        B(cx + 5.4, cy - 0.12, hb + 8.2, cx + 6.4, cy + 0.12, hb + 9.6, "Red", "Signs")
        icon(K.FLAME_ICON, {"o": "Yellow", "y": "White", "w": "White"}, cx + 2.8, cy - 0.12, hb + 8.9, 0.2, "S", 0.0, 0.06, "Signs")
    COL(x0 - 0.7, y0 - 0.7, 0, x1 + 0.7, y1 + 0.7, hb + 3.0, "CastleTower", G)


def castle_wall():
    G = "CastleWall"
    # front wall (lower, so the keep reads from the street), sides + back
    for (a0, a1) in ((191.0, 240.0), (260.0, 309.0)):
        wall_seg(a0, 366.0, a1, 369.0, 7.0, "S")
    wall_seg(178.0, 377.0, 181.0, 472.0, 9.0, "W")
    wall_seg(319.0, 377.0, 322.0, 472.0, 9.0, "E")
    wall_seg(188.0, 479.0, 312.0, 482.0, 9.0, "N")
    tower(177.0, 363.0, 191.0, 377.0, 18.0, ban=True)
    tower(309.0, 363.0, 323.0, 377.0, 18.0, ban=True)
    tower(178.0, 472.0, 188.0, 482.0, 14.0, flag=False, quoins=False)
    tower(312.0, 472.0, 322.0, 482.0, 14.0, flag=False, quoins=False)
    # spatula plaques on the street face
    for x in (203.0, 228.0, 272.0, 297.0):
        FB("S", x, 366.0, -1.5, -0.05, 2.0, 1.5, 0.25, 6.0, "StoneC", G)
        icon(SPAT, {"s": "Steel", "k": "WoodDark"}, x, 366.0 - 0.25, 4.0, 0.3, "S", 0.0, 0.14, G)
    for x in (215.5, 284.5):
        lantern("S", x, 366.0, 4.2, G)
    # gatehouse with a raised portcullis and the spatula shield
    hb = 17.0
    B(240.0, 363.0, 0, 244.0, 372.0, hb, "Brick", G); B(256.0, 363.0, 0, 260.0, 372.0, hb, "Brick", G)
    B(244.0, 363.0, 10.0, 256.0, 372.0, hb, "Brick", G)
    B(244.0, 363.0, 8.6, 245.4, 372.0, 10.0, "Brick", G); B(254.6, 363.0, 8.6, 256.0, 372.0, 10.0, "Brick", G)
    B(239.7, 362.7, 0, 260.3, 372.3, 1.4, "StoneB", G)
    B(239.6, 362.6, hb, 260.4, 372.4, hb + 0.6, "StoneC", G)
    B(240.6, 363.6, hb + 0.6, 259.4, 371.4, hb + 0.8, "StoneB", G)
    for (ax, f) in (("x", 362.6), ("x", 371.0), ("y", 239.6), ("y", 259.0)):
        a0, a1 = (239.6, 260.4) if ax == "x" else (364.0, 371.0)
        n = max(2, int((a1 - a0) / 3.4)); st = (a1 - a0) / n
        for i in range(n):
            u = a0 + i * st + (st - 1.9) / 2
            if ax == "x": B(u, f, hb + 0.6, u + 1.9, f + 1.4, hb + 2.8, "StoneC", G)
            else: B(f, u, hb + 0.6, f + 1.4, u + 1.9, hb + 2.8, "StoneC", G)
    for (fy, d) in ((363.0, -1), (372.0, 1)):   # stone arch trim on both faces
        y0, y1 = (fy - 0.35, fy) if d < 0 else (fy, fy + 0.35)
        B(243.2, y0, 0, 244.0, y1, 8.6, "StoneC", G); B(256.0, y0, 0, 256.8, y1, 8.6, "StoneC", G)
        B(243.2, y0, 8.6, 245.4, y1, 10.0, "StoneC", G); B(254.6, y0, 8.6, 256.8, y1, 10.0, "StoneC", G)
        B(245.4, y0, 10.0, 254.6, y1, 11.0, "StoneC", G); B(249.0, y0, 11.0, 251.0, y1, 11.6, "Stone", G)
    for x in range(12):   # portcullis (raised, teeth hanging above head height)
        xx = 244.6 + x * 0.98
        if xx > 255.6: break
        B(xx - 0.12, 364.5, 7.2, xx + 0.12, 364.8, 10.0, "Iron", G)
        B(xx - 0.06, 364.56, 6.8, xx + 0.06, 364.74, 7.2, "Iron", G)
    B(244.0, 364.45, 8.0, 256.0, 364.85, 8.3, "Iron", G); B(244.0, 364.45, 9.2, 256.0, 364.85, 9.5, "Iron", G)
    for x0 in (244.0, 255.6):   # open wooden gate leaves inside the passage
        B(x0, 367.0, 0.3, x0 + 0.4, 371.6, 7.4, "WoodDark", G, True, "GateLeaf")
        for zz in (1.4, 5.6):
            B(x0 - 0.05 if x0 > 250 else x0 + 0.4, 367.2, zz, x0 if x0 > 250 else x0 + 0.45, 371.4, zz + 0.4, "Iron", G)
    B(244.0, 363.0, 0, 256.0, 372.0, 0.24, "StoneC", "Yard")
    COL(244.0, 363.0, 0, 256.0, 372.0, 0.24, "GateFloor", "Yard")
    COL(239.6, 362.6, 0, 244.0, 372.4, hb + 2.8, "Gatehouse", G); COL(256.0, 362.6, 0, 260.4, 372.4, hb + 2.8, "Gatehouse", G)
    COL(244.0, 362.6, 10.0, 256.0, 372.4, hb + 2.8, "Gatehouse", G)
    COL(244.0, 364.4, 6.8, 256.0, 364.9, 10.0, "Portcullis", G)
    icon(shield_grid(), {"k": "Black", "r": "Red", "w": "Steel"}, 250.0, 363.0 - 0.0, 14.0, 0.3, "S", 0.0, 0.25, "Signs")
    for x in (241.6, 258.4):
        lantern("S", x, 363.0, 7.0, G)
    banner("N", 250.0, 372.0, 15.6, 0.26, 0.0, "Signs")
    # hedge strip along the street face
    for (a0, a1) in ((192.0, 238.5), (261.5, 308.0)):
        K.hedge(a0, 361.6, a1, 365.6, 3.0, int(a0))
    TARGETS["gate passage"] = (250.0, 367.5, 0.24)


# ------------------------------------------------------------------ courtyard
def grill_station(x0, y0):
    """Built-in outdoor kitchen, 24 wide, operator stands south of it."""
    G = "Grill"
    x1 = x0 + 24.0; y1 = y0 + 5.0
    B(x0, y0, 0, x1, y1, 3.4, "Brick", G)
    B(x0 - 0.2, y0 - 0.2, 0, x1 + 0.2, y1 + 0.2, 0.6, "StoneB", G)
    B(x0 - 0.3, y0 - 0.3, 3.4, x1 + 0.3, y1 + 0.2, 3.8, "StoneC", G)
    for k in range(6):   # steel cabinet doors with handles
        a = x0 + 0.8 + k * 3.8
        B(a, y0 - 0.12, 0.9, a + 3.4, y0, 3.0, "Steel", G)
        B(a + 1.5, y0 - 0.25, 2.3, a + 1.9, y0 - 0.12, 2.6, "Chrome", G)
    gx0, gx1 = x0 + 6.0, x0 + 18.0
    B(gx0, y0 + 0.5, 3.8, gx1, y1 - 0.5, 5.0, "Steel", G)
    for k in range(6):
        B(gx0 + 1.0 + k * 1.9, y0 + 0.38, 4.2, gx0 + 1.5 + k * 1.9, y0 + 0.5, 4.6, "Black", G)
    B(gx0 + 0.4, y0 + 1.0, 5.0, gx1 - 0.4, y1 - 1.0, 5.1, "Fire", G)
    for k in range(15):
        xx = gx0 + 0.6 + k * 0.76
        B(xx, y0 + 0.9, 5.1, xx + 0.22, y1 - 0.9, 5.28, "Steel", G)
    for k in range(4):
        B(gx0 + 1.5 + k * 2.6, y0 + 1.6, 5.28, gx0 + 3.3 + k * 2.6, y0 + 3.2, 5.6, "Meat", G)
        B(gx0 + 1.9 + k * 2.6, y0 + 1.6, 5.6, gx0 + 2.1 + k * 2.6, y0 + 3.2, 5.62, "Coal", G)
    hcyl("x", gx1 - 2.4, gx1 - 1.8, y0 + 3.6, 5.42, 0.12, "Sausage", G, 6)
    sc.plate((gx0, y1 - 0.5, 5.0), (gx1, y1 - 0.5, 5.0), (gx1, y1 + 0.7, 9.4), (gx0, y1 + 0.7, 9.4), 0.35, "Steel", G)
    B(gx0 + 3.0, y1 - 0.85, 8.95, gx1 - 3.0, y1 - 0.6, 9.2, "Chrome", G)   # hood handle on the front face
    for hx in (gx0 + 3.2, gx1 - 3.45):
        B(hx, y1 - 0.65, 8.95, hx + 0.25, y1 - 0.35, 9.2, "Chrome", G)
    for (a0, a1) in ((x0, gx0 - 0.4), (gx1 + 0.4, x1)):   # brick backsplash + utensils
        B(a0, y1 - 1.0, 3.8, a1, y1, 7.0, "Brick", G)
        B(a0 - 0.2, y1 - 1.2, 7.0, a1 + 0.2, y1 + 0.2, 7.4, "StoneC", G)
    for i, (m, ln) in enumerate((("Steel", 2.4), ("Black", 2.8), ("Steel", 2.0))):
        B(x0 + 1.0 + i * 1.4, y1 - 1.1, 6.6 - ln, x0 + 1.3 + i * 1.4, y1 - 1.0, 6.6, m, G)
        B(x0 + 0.8 + i * 1.4, y1 - 1.15, 6.6 - ln - 0.8, x0 + 1.5 + i * 1.4, y1 - 1.0, 6.6 - ln, "Steel", G)
    C(x1 - 3.0, y0 + 2.5, 3.8, 3.9, 1.0, "Black", G, 10); C(x1 - 3.0, y0 + 2.5, 3.9, 5.0, 0.8, "Steel", G, 10)
    C(x0 + 3.0, y0 + 2.2, 3.8, 4.3, 1.2, "WoodLight", G, 10); K.plate(x0 + 3.0, y0 + 2.2, 4.3)
    for k in range(3):
        hcyl("x", x0 + 2.4, x0 + 3.6, y0 + 1.8 + k * 0.32, 4.45, 0.13, "Sausage", G, 6)
    B(x0 + 4.4, y0 + 0.6, 3.8, x0 + 4.8, y0 + 1.0, 4.9, "Ketchup", G); B(x0 + 4.9, y0 + 0.6, 3.8, x0 + 5.3, y0 + 1.0, 4.9, "Mustard", G)
    C(x1 + 1.2, y1 - 1.0, 0.0, 12.0, 0.7, "Iron", G, 8); C(x1 + 1.2, y1 - 1.0, 12.0, 12.5, 1.1, "Black", G, 8)
    B(x1, y1 - 1.4, 5.5, x1 + 1.3, y1 - 0.6, 6.0, "Iron", G)
    K.smoke(x1 + 1.2, y1 - 1.0, 13.0, 5, 1.0, 13); K.smoke((gx0 + gx1) / 2, y0 + 2.5, 6.5, 3, 0.7, 14)
    COL(x0 - 0.3, y0 - 0.3, 0, x1 + 0.3, y1 + 0.8, 5.3, "GrillStation", G)
    COL(x1 + 0.4, y1 - 1.8, 0, x1 + 2.0, y1 - 0.2, 12.5, "GrillChimney", G)
    sc.anchor("GrillFire", ((gx0 + gx1) / 2, y0 + 2.5, 5.5), range=20)


def firewood(x0, y0):
    G = "Yard"
    x1, y1 = x0 + 6.0, y0 + 4.5
    for (px, py) in ((x0, y0), (x1 - 0.5, y0), (x0, y1 - 0.5), (x1 - 0.5, y1 - 0.5)):
        B(px, py, 0, px + 0.5, py + 0.5, 6.2, "WoodDark", G)
    B(x0 - 0.4, y0 - 0.4, 6.2, x1 + 0.4, y1 + 0.4, 6.6, "WoodDark", G)
    B(x0 + 0.5, y0 + 0.1, 0.0, x1 - 0.5, y1 - 0.1, 0.4, "WoodMid", G)
    for j in range(5):
        for k in range(5):
            hcyl("y", y0 + 0.2, y1 - 0.2, x0 + 1.0 + k * 1.0 + (j % 2) * 0.25, 0.85 + j * 0.95, 0.46, "WoodLight" if (j + k) % 3 else "WoodMid", G, 6)
    COL(x0, y0, 0, x1, y1, 6.6, "Firewood", G)


def paver_area(x0, y0, x1, y1, s, mats, tag, seed=0):
    nx = max(1, int(round((x1 - x0) / s))); ny = max(1, int(round((y1 - y0) / s)))
    r = random.Random(seed)
    for i in range(nx):
        for j in range(ny):
            B(x0 + i * (x1 - x0) / nx + 0.05, y0 + j * (y1 - y0) / ny + 0.05, 0, x0 + (i + 1) * (x1 - x0) / nx - 0.05, y0 + (j + 1) * (y1 - y0) / ny - 0.05,
              0.2 + (0.02 if (i + j) % 2 else 0.0), mats[(i * 2 + j + r.randint(0, 1)) % len(mats)], "Yard")
    COL(x0, y0, 0, x1, y1, 0.22, tag, "Yard")


def bollard(x, y):
    B(x - 0.4, y - 0.4, 0, x + 0.4, y + 0.4, 1.5, "Iron", "Yard", True, "Bollard")
    B(x - 0.45, y - 0.45, 1.5, x + 0.45, y + 0.45, 2.3, "Lamp", "Yard"); B(x - 0.55, y - 0.55, 2.3, x + 0.55, y + 0.55, 2.55, "Iron", "Yard")
    sc.anchor("LampLight", (x, y, 2.0), range=12)


def courtyard():
    # paving: west grill patio, main path gate -> stairs, path to the kitchen side door
    paver_area(183.0, 372.0, 238.0, 404.0, 3.2, ["PaverC", "StoneC", "SidewalkB"], "Patio", 1)
    paver_area(243.0, 372.0, 257.0, 397.0, 2.8, ["Paver", "PaverC"], "Path", 2)
    paver_area(257.0, 386.0, 300.0, 391.0, 2.5, ["StoneC", "PaverC"], "SidePath", 3)
    paver_area(300.0, 386.0, 305.0, 446.0, 2.5, ["StoneC", "PaverC"], "SidePath", 4)
    paver_area(HX + BW + 7.0, 438.0, 300.0, 446.0, 2.5, ["StoneC", "PaverC"], "SidePath", 5)
    for y in (377.0, 385.0, 393.0):
        bollard(241.4, y); bollard(258.6, y)
    for y in (398.0, 412.0, 426.0):
        bollard(306.6, y)
    # outdoor grill station + firewood + picnic
    grill_station(184.0, 386.0)
    sc.anchor("FatherSpot", (196.0, 383.6, 0.22), note="Grill Dad stands here at the big built-in grill, facing north (character model not included)")
    TARGETS["FatherSpot (grill)"] = (196.0, 383.6, 0.22)
    firewood(210.5, 386.5)
    for (bx, by) in ((185.2, 382.6), (189.0, 382.9)):
        K.charcoal_bag(bx, by, "S")
    K.picnic_table(222.0, 380.0, "x", True, True, 1)
    K.picnic_table(222.0, 397.0, "x", True, True, 2)
    K.umbrella_table(195.0, 398.0, "Red", "White", 4, 3)
    K.kettle_grill(233.5, 386.0, 1.0, "Red", True, True, 4, 3)
    # "DAD GRILLS BEST!" board on posts by the patio
    for px in (184.6, 195.4):
        B(px - 0.3, 405.2, 0, px + 0.3, 405.8, 8.4, "WoodDark", "Signs", True, "SignPost")
    FB("S", 190.0, 405.2, -5.2, 0.0, 4.2, 5.2, 0.3, 8.0, "Paper", "Signs")
    FB("S", 190.0, 405.2, -5.4, 0.0, 4.0, 5.4, 0.36, 4.2, "WoodDark", "Signs"); FB("S", 190.0, 405.2, -5.4, 0.0, 8.0, 5.4, 0.36, 8.2, "WoodDark", "Signs")
    text("DAD GRILLS", 190.0, 404.9, 7.0, 0.15, "S", "Black", 0.0, 0.1)
    text("BEST!", 190.0, 404.9, 5.2, 0.19, "S", "Red", 0.0, 0.1)
    # hedge cubes in front of the keep + along the walls, trees, gnome, flamingo
    for (x0, x1) in ((221.0, 232.0), (268.0, 279.0)):
        K.hedge(x0, 408.0, x1, 411.0, 3.0, int(x0))
    for (x0, y0, x1, y1) in ((183.0, 408.0, 199.0, 411.0), (261.0, 372.0, 266.0, 384.0), (183.0, 372.0, 192.0, 375.0)):
        K.hedge(x0, y0, x1, y1, 2.6, int(x0 + y0))
    K.tree(188.0, 420.0, 1.15, 1); K.tree(190.0, 444.0, 1.25, 2); K.tree(313.0, 412.0, 1.1, 4)
    K.flowerbed(270.0, 396.0, 296.0, 401.0, 21, 0.0, "StoneC")
    K.gnome(262.5, 392.6, "W", 1.2); K.flamingo(237.0, 392.0, "E")
    K.bush(309.0, 440.0, 1.0, 5); K.bush(198.0, 432.0, 1.1, 6); K.bush(284.0, 405.0, 0.9, 7); K.bush(216.0, 405.0, 0.9, 8)
    # pickup on a concrete pad
    B(306.0, 372.5, 0, 317.0, 397.5, 0.3, "Concrete", "Yard", True, "Parking")
    K.car(311.5, 387.5, "S", "Red", "pickup")
    # string lights: gatehouse -> smoker towers, grill patio
    K.string_lights((244.0, 372.3, 12.0), (TW[0] + 2.0, TW[1] - TR + 0.2, 12.0), 16, 2.0)
    K.string_lights((256.0, 372.3, 12.0), (TE[0] - 2.0, TE[1] - TR + 0.2, 12.0), 16, 2.0)
    K.string_lights((181.2, 392.0, 9.4), (238.0, 392.0, 9.4), 16, 1.4)
    TARGETS["west patio"] = (210.0, 398.0, 0.22); TARGETS["side door path"] = (295.0, 442.0, 0.22)
    TARGETS["east path"] = (302.5, 420.0, 0.22); TARGETS["west garden"] = (192.0, 432.0, 0.0)


def backyard():
    # pool with stone rim and a duck, loungers, dog house BUN, veggie beds, tree with swing
    G = "Yard"
    px0, py0, px1, py1 = 264.0, 458.0, 292.0, 474.0
    for (x0, y0, x1, y1) in ((px0, py0, px1, py0 + 1.2), (px0, py1 - 1.2, px1, py1), (px0, py0 + 1.2, px0 + 1.2, py1 - 1.2), (px1 - 1.2, py0 + 1.2, px1, py1 - 1.2)):
        B(x0, y0, 0, x1, y1, 0.8, "StoneC", G)
    B(px0 + 1.2, py0 + 1.2, 0, px1 - 1.2, py1 - 1.2, 0.2, "TileB", G)
    B(px0 + 1.2, py0 + 1.2, 0.2, px1 - 1.2, py1 - 1.2, 0.62, "Water", "Water")
    COL(px0, py0, 0, px1, py1, 0.8, "Pool", G)
    ball(275.0, 466.0, 0.9, 0.7, "Yellow", G, seg=8, rings=4); B(274.9, 465.2, 1.1, 275.1, 465.5, 1.25, "Orange", G)
    for k in range(2):
        x = 296.0 + k * 5.0
        B(x, 460.0, 0, x + 3.0, 468.0, 1.2, "WoodLight", G, True, "Lounger"); B(x + 0.2, 460.2, 1.2, x + 2.8, 466.0, 1.5, "ClothRed" if k else "Cloth", G)
        sc.plate((x + 0.2, 466.0, 1.2), (x + 2.8, 466.0, 1.2), (x + 2.8, 468.2, 3.4), (x + 0.2, 468.2, 3.4), 0.3, "ClothRed" if k else "Cloth", G)
    K.umbrella_table(310.0, 463.0, "Yellow", "White", 2, 5)
    B(196.0, 468.0, 0, 204.0, 475.0, 0.3, "WoodDark", G); B(196.3, 468.3, 0.3, 203.7, 474.7, 4.6, "HouseRed", G, True, "DogHouse")
    sc.gable_y(195.6, 204.4, 467.6, 475.4, 4.6, 7.4, "RoofRedB", G)
    B(198.6, 468.2, 0.3, 201.4, 468.34, 3.2, "Black", G); text("BUN", 200.0, 468.3, 4.0, 0.14, "S", "White", 0.0, 0.08)
    B(205.6, 469.0, 0, 207.6, 471.0, 0.5, "Blue", G); C(206.6, 470.0, 0.5, 0.6, 0.7, "Water", "Water", 8)
    for i in range(3):
        K.flowerbed(214.0 + i * 11.0, 469.0, 223.0 + i * 11.0, 476.0, 20 + i, 0.0, "WoodMid")
        for k in range(4):
            xx = 215.6 + i * 11.0 + k * 1.9
            B(xx, 470.4, 0.6, xx + 0.5, 470.9, 2.4, "Leaf", "Flowers"); B(xx - 0.2, 470.2, 2.0, xx + 0.7, 471.1, 2.9, ["FlowerRed", "Orange", "Yellow"][i], "Flowers")
    K.tree(189.0, 460.0, 1.3, 7)
    beam((192.5, 460.0, 9.0), (192.5, 460.0, 2.6), 0.12, "Paper", G); beam((195.5, 460.0, 9.0), (195.5, 460.0, 2.6), 0.12, "Paper", G)
    B(192.0, 459.3, 2.3, 196.0, 460.7, 2.6, "WoodLight", G); B(188.0, 459.6, 8.8, 196.2, 460.4, 9.4, "Trunk", G)
    K.tree(311.0, 452.0, 1.2, 9)
    K.bush(246.0, 474.0, 1.2, 9); K.bush(258.0, 474.0, 1.1, 10); K.bush(234.0, 458.0, 1.0, 11)
    K.kiddie_pool(232.0, 466.0, 4.0)
    TARGETS["rear yard"] = (250.0, 466.0, 0.0); TARGETS["pool deck"] = (296.0, 456.0, 0.0)
