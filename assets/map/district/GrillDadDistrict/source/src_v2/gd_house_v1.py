"""Grill Dad's House: two storeys, cream walls, red roof, brick chimney, porch with sign, garage, balcony,
full interior on both floors and the grill backyard. World coords; house local origin (HX, HY) = SW corner of the garage wing,
front faces south (towards the park)."""
import math, random
import gd_kit as K
from gd_kit import B, C, COL, FB, FP, wall, roof_gable, gable_solid, stairs, text, icon, pix, ball, ring, hcyl, beam

HX, HY = 206.0, 396.0
Z1 = 1.0      # 1F floor top
ZC1 = 13.0    # 1F wall top / slab bottom
Z2 = 14.1     # 2F floor top
ZW = 26.0     # 2F wall top
REDS = ["RoofRed", "RoofRedB", "RoofRedC", "RoofRed"]
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


# ------------------------------------------------------------------ the house
def build(scene):
    global sc
    sc = scene
    shell()
    garage()
    porch()
    roofs()
    balcony_chimney()
    interior_1f()
    interior_2f()
    yard()


def shell():
    W, D = "win", "door"
    def o1(a, b, k): return (a, b, Z1 + 3.2, Z1 + 8.6, W) if k == W else (a, b, Z1, Z1 + 9.0, k)
    def o2(a, b, k): return (a, b, Z2 + 3.2, Z2 + 8.6, W) if k == W else (a, b, Z2, Z2 + 9.0, k)
    # foundation + 1F floor
    h(21.7, -0.3, 0, 66.3, 40.3, 0.94, "StoneB", "House", True, "Foundation")
    for i in range(22):   # stone course pattern on the foundation front
        h(21.7 + i * 2.03 + 0.1, -0.42, 0.1 + (i % 2) * 0.42, 21.7 + i * 2.03 + 1.6, -0.3, 0.46 + (i % 2) * 0.42, "StoneC" if i % 3 else "Stone", "House")
    hc(22, 0, 0.9, 66, 40, Z1, "Floor1")
    # 1F floors: wood planks in living + dining, checker tiles in the kitchen
    for k in range(21):
        y0 = 0.8 + k * 1.0
        h(22.8, y0 + 0.02, 0.9, 65.2, min(y0 + 1.0, 21.7) - 0.02, Z1, "Floor" if k % 2 else "FloorB", "House")
    for k in range(17):
        y0 = 22.3 + k * 1.0
        h(22.8, y0 + 0.02, 0.9, 43.7, min(y0 + 1.0, 39.2) - 0.02, Z1, "Floor" if k % 2 else "FloorB", "House")
    for i in range(11):
        for j in range(9):
            x0 = 44.3 + i * 1.9; y0 = 22.3 + j * 1.88
            h(x0, y0, 0.9, min(x0 + 1.9, 65.2), min(y0 + 1.88, 39.2), Z1, "Tile" if (i + j) % 2 else "TileRed", "House")
    h(22, 21.7, 0.9, 66, 22.3, Z1 - 0.02, "WoodDark", "House"); h(43.7, 22.3, 0.9, 44.3, 39.2, Z1 - 0.02, "WoodDark", "House")
    z0 = 0.94
    # exterior walls 1F
    hw("x", 0.4, 22, 66, z0, ZC1, [o1(27, 35, W), o1(40, 48, D), o1(53, 61, W)], "Cream", inside=1, mat_in="WallPeach")
    hw("x", 39.6, 22, 44, z0, ZC1, [o1(28, 36, W)], "Cream", inside=-1, mat_in="WallYellow")
    hw("x", 39.6, 44, 66, z0, ZC1, [o1(51, 59, W)], "Cream", inside=-1, mat_in="WallBlue")
    hw("y", 22.4, 0.8, 22, z0, ZC1, [], "Cream", inside=1, mat_in="WallPeach")
    hw("y", 22.4, 22, 39.2, z0, ZC1, [o1(27, 33, D)], "Cream", inside=1, mat_in="WallYellow")
    hw("y", 65.6, 0.8, 22, z0, ZC1, [], "Cream", inside=-1, mat_in="WallPeach")
    hw("y", 65.6, 22, 39.2, z0, ZC1, [o1(28, 36, D)], "Cream", inside=-1, mat_in="WallBlue")
    # partitions 1F
    hw("x", 22.0, 28.1, 65.2, Z1, ZC1, [o1(31, 39, D), o1(51, 59, D)], "WallPeach", t=0.6)
    hw("y", 44.0, 22.3, 39.2, Z1, ZC1, [o1(27, 35, D)], "WallYellow", t=0.6)
    door("front door", 44, 0.4, Z1, 8, "y"); door("living-dining", 35, 22, Z1, 8, "y"); door("living-kitchen", 55, 22, Z1, 8, "y")
    door("dining-kitchen", 44, 31, Z1, 8, "x"); door("kitchen-patio", 65.6, 32, Z1, 8, "x"); door("dining-garage", 22.4, 30, Z1, 6, "x")
    # 2F slab with the stair hole (x 22.8..27.8, y 0.8..21.2)
    for (x0, y0, x1, y1) in ((27.8, 0, 66, 40), (22, 26.8, 27.8, 40), (22, 0, 22.8, 26.8), (22.8, 0, 27.8, 0.8)):
        h(x0, y0, ZC1, x1, y1, 14.0, "Ceiling", "House2F", True, "Floor2")
    # 2F floors
    for k in range(39):
        y0 = 0.8 + k * 1.0
        m = "Floor" if k % 2 else "FloorB"
        h(27.8 if y0 < 26.7 else 22.8, y0 + 0.02, 14.0, 43.7, min(y0 + 1.0, 31.7) - 0.02, Z2, m, "House2F") if y0 < 31.7 else None
        if y0 < 21.7: h(44.3, y0 + 0.02, 14.0, 65.2, min(y0 + 1.0, 21.7) - 0.02, Z2, "PlankC" if k % 2 else "WoodLight", "House2F")
    for k in range(17):
        y0 = 22.3 + k * 1.0
        h(44.3, y0 + 0.02, 14.0, 65.2, min(y0 + 1.0, 39.2) - 0.02, Z2, "Floor" if k % 2 else "FloorB", "House2F")
    for i in range(11):
        for j in range(4):
            x0 = 22.8 + i * 1.9; y0 = 32.3 + j * 1.73
            h(x0, y0, 14.0, min(x0 + 1.9, 43.7), min(y0 + 1.73, 39.2), Z2, "Tile" if (i + j) % 2 else "TileB", "House2F")
    h(43.7, 0.8, 14.0, 44.3, 39.2, Z2 - 0.02, "WoodDark", "House2F"); h(22.8, 31.7, 14.0, 43.7, 32.3, Z2 - 0.02, "WoodDark", "House2F")
    h(44.3, 21.7, 14.0, 65.2, 22.3, Z2 - 0.02, "WoodDark", "House2F")
    # exterior walls 2F
    g2 = dict(group="House2F")
    hw("x", 0.4, 22, 44, 14.0, ZW, [o2(29, 37, W)], "Cream", inside=1, mat_in="WallGreen", **g2)
    hw("x", 0.4, 44, 66, 14.0, ZW, [o2(51, 59, W)], "Cream", inside=1, mat_in="WallPink", **g2)
    hw("x", 39.6, 22, 44, 14.0, ZW, [o2(30, 38, W)], "Cream", inside=-1, mat_in="WallBlue", **g2)
    hw("x", 39.6, 44, 66, 14.0, ZW, [o2(51, 59, W)], "Cream", inside=-1, mat_in="WallYellow", **g2)
    hw("y", 22.4, 0.8, 32, 14.0, ZW, [(8, 16, Z2 + 4.4, Z2 + 9.4, W)], "Cream", inside=1, mat_in="WallGreen", **g2)
    hw("y", 22.4, 32, 39.2, 14.0, ZW, [(33.5, 37.5, Z2 + 4.6, Z2 + 9.0, W)], "Cream", inside=1, mat_in="WallBlue", **g2)
    hw("y", 65.6, 0.8, 22, 14.0, ZW, [o2(9, 17, D)], "Cream", inside=-1, mat_in="WallPink", **g2)
    hw("y", 65.6, 22, 39.2, 14.0, ZW, [o2(27, 35, W)], "Cream", inside=-1, mat_in="WallYellow", **g2)
    # partitions 2F
    hw("y", 44.0, 0.8, 39.2, Z2, ZW, [o2(7.5, 14.5, D), o2(22.6, 29.4, D)], "WallGreen", t=0.6, **g2)
    hw("x", 22.0, 44.3, 65.2, Z2, ZW, [], "WallPink", t=0.6, **g2)
    hw("x", 32.0, 22.8, 43.7, Z2, ZW, [(32, 38, Z2, Z2 + 8.88, D)], "WallBlue", t=0.6, **g2)   # opening top 0.12 below Z2+9 so the White frame doesn't z-fight the trim at 23.1
    door("2F master door", 44, 11, Z2, 7, "x"); door("2F kid door", 44, 26, Z2, 6.8, "x"); door("2F bath door", 35, 32, Z2, 6, "y")
    door("2F balcony door", 65.6, 13, Z2, 8, "x")
    # exterior trim: corner boards, belt course, shutters, flower boxes
    for (cx, cy) in ((22, 0), (66, 0), (22, 40), (66, 40)):
        h(cx - 0.35, cy - 0.35, 0.94, cx + 0.35, cy + 0.35, ZW, "White", "House")
    h(22.3, -0.14, 13.1, 65.7, 0.0, 13.9, "White", "House"); h(22.3, 40.0, 13.1, 65.7, 40.14, 13.9, "White", "House")
    h(66.0, 21.0, 13.12, 66.14, 39.7, 13.9, "White", "House"); h(66.0, 0.3, 13.12, 66.14, 3.0, 13.9, "White", "House"); h(21.86, 0.3, 13.1, 22.0, 39.7, 13.9, "White", "House")
    for (u0, u1, zb, zt) in ((27, 35, Z1 + 3.2, Z1 + 8.6), (53, 61, Z1 + 3.2, Z1 + 8.6), (29, 37, Z2 + 3.2, Z2 + 8.6), (51, 59, Z2 + 3.2, Z2 + 8.6)):
        for a in (u0 - 1.7, u1 + 0.3):
            h(a, -0.2, zb - 0.1, a + 1.4, -0.02, zt + 0.1, "RoofRed", "House")
            for k in range(5):
                h(a + 0.15, -0.27, zb + 0.3 + k * (zt - zb - 0.5) / 5, a + 1.25, -0.2, zb + 0.55 + k * (zt - zb - 0.5) / 5, "RoofRedD", "House")
        h(u0 - 0.2, -1.1, zb - 1.2, u1 + 0.2, -0.3, zb - 0.4, "WoodMid", "House")
        r = random.Random(int(u0 * 7 + zb))
        a = u0
        while a < u1 - 0.3:
            h(a + 0.05, -1.0, zb - 0.4, a + 0.55, -0.4, zb + r.uniform(0.0, 0.4), r.choice(["FlowerRed", "FlowerYellow", "FlowerPink", "Leaf"]), "House")
            a += 0.6
    # wall lanterns by the front door
    for a in (38.2, 49.8):
        h(a - 0.25, -0.35, 7.4, a + 0.25, -0.0, 7.7, "Iron", "House"); h(a - 0.4, -0.9, 6.2, a + 0.4, -0.2, 7.4, "Lamp", "House")
        h(a - 0.5, -1.0, 7.4, a + 0.5, -0.1, 7.6, "Iron", "House"); h(a - 0.5, -1.0, 6.0, a + 0.5, -0.1, 6.2, "Iron", "House")
        sc.anchor("LampLight", (HX + a, HY - 0.6, 6.8), range=22)
    # door leaves: front (red, open inward), patio (red, open outward)
    h(39.55, 0.85, Z1, 39.9, 8.3, Z1 + 8.75, "Red", "House", True, "DoorLeaf")
    h(39.9, 1.6, Z1 + 5.2, 40.0, 6.9, Z1 + 8.0, "Glass", "Glass"); h(39.9, 7.4, Z1 + 4.0, 40.15, 7.8, Z1 + 4.6, "Gold", "House")
    h(66.05, 27.62, Z1, 73.6, 27.92, Z1 + 8.75, "Red", "House", True, "DoorLeaf")
    h(67.0, 27.92, Z1 + 5.0, 72.6, 28.02, Z1 + 8.0, "Glass", "Glass")
    # 2F ceiling
    h(22, 0, ZW, 66, 40, ZW + 0.5, "Ceiling", "HouseRoof", True, "Ceiling2")
    tgt("1F living", 50, 8, Z1); tgt("1F dining", 34, 27, Z1); tgt("1F kitchen", 55, 30, Z1); tgt("stairs bottom", 25.3, 3.0, Z1)
    tgt("2F landing", 25.3, 29.3, Z2); tgt("2F lounge", 36, 14, Z2); tgt("2F master", 50, 7, Z2); tgt("2F kid", 50, 30, Z2); tgt("2F bath", 35, 35, Z2)
    tgt("2F balcony", 70, 13, 14.0)


def garage():
    # floor, walls, ceiling
    h(0, 6, 0, 22, 34, 0.5, "Concrete", "House", True, "GarageFloor")
    hw("x", 6.4, 0, 22, 0.5, 12.0, [(3, 19, 0.5, 9.8, "door")], "Cream", inside=1, mat_in="WallGrey")
    hw("x", 33.6, 0, 22, 0.5, 12.0, [(8, 14, 4.2, 8.4, "win")], "Cream", inside=-1, mat_in="WallGrey")
    hw("y", 0.4, 6.8, 33.2, 0.5, 12.0, [(16, 24, 4.2, 8.4, "win")], "Cream", inside=1, mat_in="WallGrey")
    h(0, 6, 12.0, 22, 34, 12.5, "Ceiling", "HouseRoof", True, "GarageCeiling")
    for (cx, cy) in ((0, 6), (0, 34), (22, 6)):
        h(cx - 0.3, cy - 0.3, 0.5, cx + 0.3, cy + 0.3, 12.0, "White", "House")
    door("garage door", 11, 6.4, 0.5, 16, "y")
    tgt("garage", 11, 20, 0.5)
    # rolled-up door under the ceiling + tracks
    for k in range(6):
        h(3.3, 7.2 + k * 2.1, 10.9, 18.7, 9.2 + k * 2.1, 11.15, "White" if k % 2 else "WallGrey", "House")
    h(3.0, 7.0, 10.5, 3.25, 20, 10.9, "Iron", "House"); h(18.75, 7.0, 10.5, 19.0, 20, 10.9, "Iron", "House")
    # step up into the dining room
    h(19.6, 27.2, 0.5, 22.0, 32.8, 0.78, "WoodMid", "House", True, "GarageStep")
    G = "HouseInterior"
    # workbench with vice, tools pegboard (north wall)
    table(HX + 12.2, HY + 30.6, HX + 18.8, HY + 33.0, 0.5, 3.4, "WoodLight", "WoodDark", G)
    h(12.6, 33.1, 4.6, 18.6, 33.2, 9.0, "WoodMid", G)
    for i, m in enumerate(["Steel", "Red", "Steel", "Yellow", "Steel", "Blue", "Steel"]):
        h(13.0 + i * 0.8, 32.95, 5.2 + (i % 3) * 0.5, 13.35 + i * 0.8, 33.1, 7.8 + (i % 2) * 0.6, m, G)
    h(13.4, 31.0, 3.9, 14.8, 32.2, 4.5, "Red", G); h(16.2, 31.2, 3.9, 18.2, 32.4, 4.3, "Blue", G)
    # shelves with sauce + charcoal (west wall)
    shelf(HX + 1.6, HY + 28.5, 0.5, "E", 7.0, 8.5, 1.5, 11, G, "Steel", "jars")
    K.charcoal_bag(HX + 2.0, HY + 12.0, "E", 0.5); K.charcoal_bag(HX + 2.0, HY + 9.0, "E", 0.5)
    # propane tank, lawn mower, kid's bike, spare kettle grill
    C(HX + 5.0, HY + 32.0, 0.5, 3.4, 0.9, "White", G, 8, True, "Propane"); ball(HX + 5.0, HY + 32.0, 3.4, 0.9, "White", G, lat0=0, lat1=90, seg=8, rings=3)
    C(HX + 5.0, HY + 32.0, 4.2, 4.6, 0.5, "Red", G, 8)
    h(7.6, 24.2, 1.0, 10.8, 26.6, 2.2, "Red", G, True, "Mower"); h(8.4, 24.8, 2.2, 10.0, 26.0, 2.9, "Black", G)
    beam((HX + 7.8, HY + 24.4, 2.2), (HX + 6.4, HY + 22.2, 5.0), 0.16, "Iron", G); beam((HX + 7.8, HY + 26.4, 2.2), (HX + 6.4, HY + 24.2, 5.0), 0.16, "Iron", G)
    for (wx, wy) in ((7.6, 24.2), (10.8, 24.2), (7.6, 26.6), (10.8, 26.6)):
        hcyl("y", HY + wy - 0.2, HY + wy + 0.2, HX + wx, 1.1, 0.6, "Tire", G, 8)
    K.kettle_grill(HX + 19.4, HY + 14.0, 0.8, "Blue", False, True, 3, 0, G)
    # tyre stack + oil cans
    for k in range(3):
        ring(HX + 2.2, HY + 20.5, 0.6, 1.3, 0.5 + k * 0.75, 1.2 + k * 0.75, "Tire", G, 10)
    COL(HX + 0.9, HY + 19.2, 0.5, HX + 3.5, HY + 21.8, 2.75, "Tyres", G)
    h(1.2, 15.2, 0.5, 2.2, 16.0, 1.8, "Yellow", G); h(1.2, 16.4, 0.5, 2.2, 17.2, 1.8, "Red", G)
    ceiling_lamp(HX + 11, HY + 20, 12.0, G)
    text("BBQ", HX + 11, HY + 33.2, 9.6, 0.22, "S", "Red", 0.0, 0.1, G)


def porch():
    # stone base + plank deck (top at Z1), steps, columns, rails
    h(31, -9, 0, 57, -0.3, 0.7, "StoneB", "House")
    hc(31, -9, 0, 57, 0, Z1, "Porch")
    for k in range(9):
        y0 = -9 + k * 0.97
        h(31.05, y0 + 0.03, 0.7, 56.95, y0 + 0.94, Z1, ["Plank", "PlankB", "PlankC"][k % 3], "House")
    h(38, -10.4, 0, 50, -9, 0.5, "StoneC", "House", True, "PorchStep")
    h(37.6, -11.9, 0, 50.4, -10.4, 0.26, "StoneC", "House", True, "PorchStep")
    for a in (32.2, 39.4, 48.6, 55.8):
        h(a - 0.8, -8.8, Z1, a + 0.8, -7.2, Z1 + 2.4, "StoneC", "House", True, "PorchColumn")
        h(a - 0.9, -8.9, Z1 + 2.4, a + 0.9, -7.1, Z1 + 2.7, "White", "House")
        h(a - 0.5, -8.5, Z1 + 2.7, a + 0.5, -7.5, 12.0, "White", "House", True, "PorchColumn")
        h(a - 0.75, -8.75, 12.0, a + 0.75, -7.25, 12.4, "White", "House")
    # rails (front between outer columns, both sides)
    def rail(x0, y0, x1, y1):
        h(x0, y0, Z1 + 2.9, x1, y1, Z1 + 3.2, "White", "House"); h(x0, y0, Z1 + 0.5, x1, y1, Z1 + 0.75, "White", "House")
        hc(x0, y0, Z1, x1, y1, Z1 + 3.2, "PorchRail")
        if x1 - x0 > y1 - y0:
            n = int((x1 - x0) / 0.9)
            for i in range(n):
                u = x0 + (i + 0.5) * (x1 - x0) / n
                h(u - 0.14, y0 + 0.03, Z1 + 0.75, u + 0.14, y1 - 0.03, Z1 + 2.9, "White", "House")
        else:
            n = int((y1 - y0) / 0.9)
            for i in range(n):
                u = y0 + (i + 0.5) * (y1 - y0) / n
                h(x0 + 0.03, u - 0.14, Z1 + 0.75, x1 - 0.03, u + 0.14, Z1 + 2.9, "White", "House")
    rail(33.0, -8.15, 38.6, -7.85); rail(49.4, -8.15, 55.0, -7.85)
    rail(31.5, -7.2, 31.8, -0.3); rail(56.2, -7.2, 56.5, -0.3)
    # porch beam + ceiling
    h(30.6, -9.4, 12.4, 57.4, -0.02, 13.0, "White", "HouseRoof")
    # hanging sign
    h(34.5, -9.72, 10.0, 53.5, -9.42, 13.3, "RoofRedB", "House")
    h(34.2, -9.8, 9.8, 53.8, -9.5, 10.0, "Gold", "House"); h(34.2, -9.8, 13.3, 53.8, -9.5, 13.5, "Gold", "House")
    text("GRILL DAD'S", HX + 44, HY - 9.72, 12.35, 0.2, "S", "White", -0.02, 0.14)
    text("HOUSE", HX + 44, HY - 9.72, 10.75, 0.2, "S", "FireY", -0.02, 0.14)
    for a in (35.9, 52.1):
        icon(K.FLAME_ICON, {"o": "Fire", "y": "FireY", "w": "White"}, HX + a, HY - 9.72, 11.65, 0.3, "S", -0.02, 0.16)
    # crossed spatulas in the gable
    icon(K.spatulas_icon(), {"s": "Chrome"}, HX + 44, HY - 9.32, 15.4, 0.3, "S", -0.02, 0.2)
    # door mat with a steak, potted plants, porch bench, lanterns
    h(41, -4.4, Z1, 47, -1.0, Z1 + 0.08, "Orange", "House"); h(41.4, -4.0, Z1 + 0.02, 46.6, -1.4, Z1 + 0.12, "WallYellow", "House")
    h(42.6, -3.5, Z1 + 0.1, 45.4, -1.9, Z1 + 0.18, "Meat", "House"); h(43.2, -3.1, Z1 + 0.16, 44.2, -2.4, Z1 + 0.22, "PinkB", "House")
    plant(HX + 37.4, HY - 1.6, Z1, "House", 1.2); plant(HX + 50.6, HY - 1.6, Z1, "House", 1.2)
    h(32.4, -2.2, Z1 + 1.3, 36.4, -0.5, Z1 + 1.7, "WoodLight", "House", True, "PorchBench"); h(32.4, -0.75, Z1 + 1.7, 36.4, -0.45, Z1 + 3.9, "WoodMid", "House")
    for a in (32.5, 36.0):
        h(a, -2.1, Z1, a + 0.3, -0.6, Z1 + 1.3, "WoodDark", "House")
    tgt("front porch", 44, -5, Z1)


def roofs():
    # main roof
    sc.gable_x(HX + 22, HX + 66, HY + 0, HY + 40, ZW + 0.5, 36.5, "Cream", "HouseRoof")
    roof_gable("HouseRoof", "x", HX + 20.6, HX + 67.4, HY - 1.7, HY + 41.7, 26.1, 38.1, REDS, rows=10, seed=3)
    for yy in (-1.85, 41.6):
        h(20.6, yy, 25.7, 67.4, yy + 0.25, 26.5, "White", "HouseRoof")
    for xx in (21.9, 66.02):   # attic vents on the gable ends
        h(xx, 17.5, 29.5, xx + 0.1, 22.5, 33.0, "White", "HouseRoof"); h(xx - 0.03, 18.0, 30.0, xx + 0.13, 22.0, 32.5, "RoofRedD", "HouseRoof")
    COL(HX + 22, HY + 6, ZW + 0.5, HX + 66, HY + 34, 31.5, "Roof", "HouseRoof"); COL(HX + 22, HY + 13, 31.5, HX + 66, HY + 27, 36.5, "Roof", "HouseRoof")
    _porch_roof()
    # garage roof
    sc.gable_x(HX + 0, HX + 22, HY + 6, HY + 34, 12.5, 18.0, "Cream", "HouseRoof")
    roof_gable("HouseRoof", "x", HX - 1.3, HX + 22.0, HY + 4.7, HY + 35.3, 12.1, 19.0, REDS, rows=7, seed=9)
    for yy in (4.55, 35.2):
        h(-1.3, yy, 11.7, 22.0, yy + 0.25, 12.5, "White", "HouseRoof")
    COL(HX, HY + 9, 12.5, HX + 22, HY + 31, 16.5, "Roof", "HouseRoof")


def _porch_roof():
    sc.gable_y(HX + 31, HX + 57, HY - 9.3, HY + 0.0, 13.0, 19.0, "Brown", "HouseRoof")
    roof_gable("HouseRoof", "y", HY - 10.3, HY + 0.0, HX + 29.4, HX + 58.6, 12.5, 20.0, REDS, rows=6, seed=5)
    COL(HX + 31, HY - 9.3, 12.4, HX + 57, HY, 15.5, "Roof", "HouseRoof")


def balcony_chimney():
    # balcony on the east side of the master bedroom
    for k in range(8):
        h(66.05 + k * 1.0, 3, 13.6, 66.05 + (k + 1) * 1.0 - 0.06, 21, 14.0, ["Plank", "PlankB", "PlankC"][k % 3], "House2F")
    h(66.05, 3.1, 13.1, 74, 20.9, 13.6, "WoodDark", "House2F")
    hc(66, 3, 13.1, 74, 21, 14.0, "Balcony", "House2F")
    for (px, py) in ((73.4, 3.6), (73.4, 20.4)):
        h(px - 0.45, py - 0.45, 0.3, px + 0.45, py + 0.45, 13.1, "WoodMid", "House", True, "BalconyPost")
    def brail(x0, y0, x1, y1):
        h(x0, y0, 17.1, x1, y1, 17.5, "WoodDark", "House2F"); h(x0, y0, 14.4, x1, y1, 14.7, "WoodDark", "House2F")
        hc(x0, y0, 14.0, x1, y1, 17.5, "BalconyRail", "House2F")
        if x1 - x0 > y1 - y0:
            n = int((x1 - x0) / 0.8)
            for i in range(n):
                u = x0 + (i + 0.5) * (x1 - x0) / n
                h(u - 0.15, y0 + 0.04, 14.7, u + 0.15, y1 - 0.04, 17.1, "WoodMid", "House2F")
        else:
            n = int((y1 - y0) / 0.8)
            for i in range(n):
                u = y0 + (i + 0.5) * (y1 - y0) / n
                h(x0 + 0.04, u - 0.15, 14.7, x1 - 0.04, u + 0.15, 17.1, "WoodMid", "House2F")
    brail(66.2, 3.0, 74, 3.4); brail(66.2, 20.6, 74, 21.0); brail(73.6, 3.4, 74, 20.6)
    for (px, py) in ((73.8, 3.2), (73.8, 20.8), (73.8, 12)):
        h(px - 0.3, py - 0.3, 14.0, px + 0.3, py + 0.3, 17.9, "WoodDark", "House2F")
    # red grill flag hanging from the balcony front
    h(67.6, 2.78, 7.6, 72.6, 2.94, 12.9, "Red", "House"); h(67.4, 2.72, 12.9, 72.8, 2.98, 13.08, "WoodDark", "House")
    h(67.6, 2.74, 7.2, 72.6, 2.98, 7.6, "Gold", "House")
    icon(K.GRILL_ICON, {"1": "White"}, HX + 70.1, HY + 2.78, 10.4, 0.32, "S", -0.02, 0.12)
    # balcony furniture
    G = "House2F"
    table(HX + 69.2, HY + 6.0, HX + 71.6, HY + 8.4, 14.0, 2.6, "WoodLight", "WoodMid", G)
    K.cup(HX + 70.4, HY + 7.2, 16.6, "Red")
    chair(HX + 70.4, HY + 10.4, 14.0, "S", g=G); plant(HX + 72.2, HY + 18.6, 14.0, G, 1.1)
    # chimney
    r = random.Random(4)
    h(66.0, 22.0, 0, 70.4, 27.6, 30.0, "Brick", "House", True, "Chimney")
    h(66.6, 22.6, 30.0, 69.8, 27.0, 43.0, "Brick", "House", True, "Chimney")
    h(66.3, 22.3, 30.0, 70.1, 27.3, 30.6, "StoneC", "House")
    h(66.2, 22.2, 43.0, 70.2, 27.4, 43.9, "StoneC", "House"); h(67.2, 23.4, 43.9, 69.2, 26.2, 45.4, "BrickB", "House")
    used = set()
    for k in range(90):
        row = r.randint(1, 68); slot = r.randint(0, 2); side = r.random() < 0.6
        if (row, slot, side) in used or (row - 1, slot, side) in used or (row + 1, slot, side) in used: continue
        used.add((row, slot, side))
        z = row * 0.62; m = r.choice(["BrickB", "BrickC"]); top = z > 29.4
        if 29.0 < z < 31.0: continue
        if side:
            yy = (22.8 if top else 22.3) + slot * 1.45 + (0.5 if row % 2 else 0.0); xf = 69.8 if top else 70.4
            h(xf - 0.02, yy, z, xf + 0.09, yy + 1.2, z + 0.5, m, "House")
        elif slot < 2:
            xx = 66.8 + slot * 1.4 + (0.3 if row % 2 else 0.0); yf = 22.6 if top else 22.0
            h(xx, yf - 0.09, z, xx + 1.2, yf + 0.02, z + 0.5, m, "House")
    K.smoke(HX + 68.2, HY + 24.8, 46.0, 5, 1.4, 2)


# ------------------------------------------------------------------ interiors
def interior_1f():
    G = "HouseInterior"
    X, Y = HX, HY
    # stairs along the west wall + railing
    stairs(X + 22.8, Y + 7.0, X + 27.8, Y + 26.8, Z1, Z2, 16, "N", "WoodMid", G, "WoodLight")
    beam((X + 27.95, Y + 7.0, Z1 + 4.2), (X + 27.95, Y + 26.8, Z2 + 3.4), 0.3, "WoodDark", G)
    for i in range(0, 16, 2):
        yy = 7.0 + (i + 0.5) * 1.2375; zz = Z1 + (i + 1) * (Z2 - Z1) / 16
        h(27.82, yy - 0.12, zz, 28.08, yy + 0.12, zz + 3.3, "White", G)
    hc(27.8, 7.0, Z1, 28.1, 26.8, Z2, "StairSide", G)
    h(27.8, 22.3, Z1, 28.1, 26.8, ZC1, "WallYellow", G)
    # --- living room
    rug(X + 40.6, Y + 1.4, X + 47.4, Y + 6.4, Z1, "ClothRed", "ClothYellow", G)
    sofa(X + 53.5, Y + 12, Z1, "E", 9.0, "ClothRed", "ClothWhite", G)
    rug(X + 56.2, Y + 7.0, X + 62.4, Y + 17.0, Z1, "Cloth", "ClothWhite", G)
    table(X + 58.0, Y + 9.6, X + 60.6, Y + 14.4, Z1, 1.7, "WoodLight", "WoodDark", G)
    K.plate(X + 59.3, Y + 11.0, Z1 + 1.7); K.burger(X + 59.3, Y + 11.0, Z1 + 1.8, 0.7); K.cup(X + 59.3, Y + 13.4, Z1 + 1.7, "Red")
    tv(X + 64.2, Y + 12, Z1, "W", G)
    sofa(X + 58.5, Y + 3.2, Z1, "N", 4.2, "ClothYellow", "ClothWhite", G)
    floor_lamp(X + 63.8, Y + 2.2, Z1, G); plant(X + 50.4, Y + 2.2, Z1, G, 1.3)
    picture(X + 56, Y + 21.7, Z1 + 8.2, "S", 5.0, 3.6, "dad", G)
    picture(X + 64.8 + 0.4, Y + 19.0, Z1 + 7.0, "W", 3.2, 2.6, "flame", G)
    # trophy cabinet by the stairs + family wall
    shelf(X + 29.3, Y + 13.4, Z1, "E", 8.0, 6.5, 1.5, 21, G, "WoodDark", "none")
    for k in range(3):
        for j in range(3):
            trophy(X + 29.3, Y + 10.8 + j * 2.6, Z1 + 0.25 + k * 2.08, 0.75 if (k + j) % 2 else 0.9, G)
    # reading chair + side table under the front window, shoe rack + coat hooks by the door
    sofa(X + 35.0, Y + 3.2, Z1, "N", 4.2, "ClothGreen", "ClothWhite", G)
    h(48.6, 1.0, Z1, 51.0, 2.2, Z1 + 1.4, "WoodMid", G, True, "ShoeRack")
    for i, m in enumerate(["Red", "Blue", "White"]):
        h(48.8 + i * 0.75, 1.1, Z1 + 1.4, 49.4 + i * 0.75, 2.0, Z1 + 1.8, m, G)
    h(48.6, 0.8, Z1 + 6.4, 51.6, 0.95, Z1 + 6.8, "WoodDark", G)
    for i, m in enumerate(["RedDark", "Navy", "Yellow"]):
        h(48.9 + i * 0.9, 0.95, Z1 + 4.0, 49.6 + i * 0.9, 1.25, Z1 + 6.6, m, G)
    picture(X + 31.5, Y + 0.8, Z1 + 0.0 + 9.9, "N", 3.0, 1.6, "plain", G)
    picture(X + 22.8, Y + 30.0 - 18.0, Z1 + 9.8, "E", 3.4, 2.8, "kid", G)
    ceiling_lamp(X + 44, Y + 11, ZC1, G); ceiling_lamp(X + 58, Y + 12, ZC1, G)
    # --- dining room
    table(X + 28.0, Y + 33.4, X + 38.0, Y + 37.8, Z1, 3.0, "WoodLight", "WoodDark", G)
    for a in (29.6, 33.0, 36.4):
        chair(X + a, Y + 32.3, Z1, "N", g=G)
        K.plate(X + a, Y + 34.3, Z1 + 3.0)
    chair(X + 26.9, Y + 35.6, Z1, "E", g=G); chair(X + 39.1, Y + 35.6, Z1, "W", g=G)
    h(28.4, 38.1, Z1, 37.6, 39.2, Z1 + 1.7, "WoodMid", G); h(28.4, 38.05, Z1 + 1.7, 37.6, 39.2, Z1 + 1.95, "ClothRed", G)
    C(X + 33.0, Y + 36.2, Z1 + 3.0, Z1 + 3.15, 1.3, "White", G, 10)
    for k in range(4):
        hcyl("x", X + 32.2, X + 33.8, Y + 35.7 + k * 0.33, Z1 + 3.3, 0.15, "Sausage", G, 6)
    K.cup(X + 30.6, Y + 36.6, Z1 + 3.0, "Blue"); K.cup(X + 35.6, Y + 36.6, Z1 + 3.0, "Yellow")
    h(34.6, 36.9, Z1 + 3.0, 35.0, 37.3, Z1 + 4.0, "Ketchup", G); h(31.0, 36.9, Z1 + 3.0, 31.4, 37.3, Z1 + 4.0, "Mustard", G)
    ceiling_lamp(X + 33, Y + 35.6, ZC1, G)
    h(23.0, 34.2, Z1, 24.6, 39.0, Z1 + 3.2, "WoodMid", G, True, "Sideboard"); h(22.9, 34.1, Z1 + 3.2, 24.7, 39.1, Z1 + 3.45, "WoodDark", G)
    cabinet_doors("E", X + 24.6, Y + 36.6, 4.6, Z1, 2, G, "Gold")
    for k in range(5):
        C(X + 23.8, Y + 35.2, Z1 + 3.45 + k * 0.12, Z1 + 3.53 + k * 0.12, 0.65, "White", G, 8)
    trophy(X + 23.8, Y + 37.6, Z1 + 3.45, 1.2, G); plant(X + 41.9, Y + 23.6, Z1, G, 1.1)
    picture(X + 22.8, Y + 36.6, Z1 + 7.6, "E", 4.2, 3.4, "grill", G)
    rug(X + 27.0, Y + 31.0, X + 39.0, Y + 39.0, Z1, "ClothYellow", "ClothRed", G)
    # --- kitchen
    counter(X + 48.6, Y + 37.3, X + 59.6, Y + 39.2, Z1, G)
    cabinet_doors("S", X + 54.1, Y + 37.3, 11.0, Z1, 5, G)
    h(53.0, 37.6, Z1 + 3.2, 57.0, 38.9, Z1 + 3.26, "Steel", G); h(54.9, 38.7, Z1 + 3.26, 55.1, 38.95, Z1 + 4.4, "Chrome", G)
    h(54.9, 38.2, Z1 + 4.2, 55.1, 38.8, Z1 + 4.4, "Chrome", G)
    stove(X + 61.4, Y + 37.7, Z1, "S", G)
    counter(X + 63.1, Y + 37.3, X + 65.2, Y + 39.2, Z1, G)
    fridge(X + 46.3, Y + 37.6, Z1, "S", G)
    # upper cabinets + pan rack
    h(48.6, 38.0, Z1 + 9.3, 50.8, 39.2, Z1 + 11.6, "White", G); h(59.4, 38.0, Z1 + 9.3, 59.8, 39.2, Z1 + 11.6, "White", G)
    h(49.0, 38.9, Z1 + 6.0, 50.6, 39.2, Z1 + 6.2, "Iron", G)
    for i in range(3):
        C(X + 49.2 + i * 0.6, Y + 38.9, Z1 + 4.6 + 0.2 * i, Z1 + 5.9, 0.28, "Steel" if i % 2 else "Black", G, 8)
    for i, m in enumerate(["Ketchup", "Mustard", "Green", "Brown", "Orange"]):   # sauce row
        h(63.3 + (i % 3) * 0.6, 38.2 + (i // 3) * 0.5, Z1 + 3.2, 63.7 + (i % 3) * 0.6, 38.6 + (i // 3) * 0.5, Z1 + 4.1, m, G)
    # butcher block + spice shelf + brick oven on the chimney wall
    h(62.6, 22.7, Z1, 65.0, 25.4, Z1 + 3.0, "WoodLight", G, True, "ButcherBlock"); h(62.5, 22.6, Z1 + 3.0, 65.1, 25.5, Z1 + 3.35, "WoodMid", G)
    h(63.0, 23.2, Z1 + 3.35, 64.4, 24.4, Z1 + 3.6, "Meat", G); h(64.5, 23.0, Z1 + 3.35, 64.7, 25.0, Z1 + 3.45, "Steel", G)
    shelf(X + 45.2, Y + 24.6, Z1, "E", 4.0, 7.5, 1.4, 31, G, "WoodMid", "jars")
    h(64.7, 25.9, Z1, 65.2, 27.6, Z1 + 6.2, "BrickC", G); h(64.6, 26.2, Z1 + 1.2, 64.75, 27.3, Z1 + 3.6, "Black", G)
    h(64.52, 26.4, Z1 + 1.2, 64.62, 27.1, Z1 + 2.2, "Fire", G)
    text("EAT", X + 55, Y + 22.3, Z1 + 10.6, 0.2, "N", "Red", 0.0, 0.1, G)
    ceiling_lamp(X + 55, Y + 30, ZC1, G)
    rug(X + 51.5, Y + 34.6, X + 58.5, Y + 36.8, Z1, "ClothGreen", "ClothWhite", G)


def interior_2f():
    G = "House2F"
    X, Y = HX, HY
    # railing around the stair well
    h(27.8, 0.8, Z2 + 3.2, 28.1, 26.8, Z2 + 3.5, "WoodDark", G); h(27.8, 0.8, Z2 + 0.3, 28.1, 26.8, Z2 + 0.55, "WoodDark", G)
    for i in range(25):
        yy = 1.3 + i * 1.02
        h(27.84, yy - 0.12, Z2 + 0.55, 28.06, yy + 0.12, Z2 + 3.2, "White", G)
    hc(27.8, 0.8, 14.0, 28.15, 26.8, Z2 + 3.5, "StairRail", G)
    # --- lounge / dad's office
    table(X + 30.0, Y + 1.0, X + 37.0, Y + 3.6, Z2, 3.0, "WoodLight", "WoodDark", G)
    h(34.2, 1.3, Z2 + 3.0, 35.8, 1.6, Z2 + 4.6, "Black", G); h(34.3, 1.6, Z2 + 3.1, 35.7, 1.66, Z2 + 4.5, "Screen", G)
    K.cup(X + 36.3, Y + 2.8, Z2 + 3.0, "Red")
    chair(X + 33.5, Y + 4.9, Z2, "S", g=G)
    shelf(X + 42.9, Y + 18.8, Z2, "W", 5.0, 8.0, 1.4, 41, G)
    shelf(X + 42.9, Y + 3.6, Z2, "W", 5.0, 6.0, 1.4, 43, G, "WoodDark", "none")
    for k in range(3):
        for j in range(2):
            trophy(X + 42.9, Y + 2.4 + j * 2.4, Z2 + 0.25 + k * 1.92, 0.8, G)
    sofa(X + 30.6, Y + 13.0, Z2, "E", 4.2, "Cloth", "ClothWhite", G)
    rug(X + 33.0, Y + 8.5, X + 41.0, Y + 17.5, Z2, "ClothGreen", "ClothYellow", G)
    table(X + 35.4, Y + 11.6, X + 38.2, Y + 14.4, Z2, 1.7, "WoodLight", "WoodDark", G)
    trophy(X + 36.8, Y + 13.0, Z2 + 1.7, 1.2, G)
    picture(X + 39.5, Y + 31.7, Z2 + 7.2, "S", 4.6, 3.6, "dad", G)
    floor_lamp(X + 38.6, Y + 2.4, Z2, G); plant(X + 29.4, Y + 22.4, Z2, G, 1.2)
    ceiling_lamp(X + 36, Y + 13, ZW, G)
    # --- master bedroom
    bed(X + 55, Y + 16.4, Z2, "S", 7.4, 10.0, "ClothRed", G)
    for a in (50.2, 59.8):
        table(X + a - 0.9, Y + 19.6, X + a + 0.9, Y + 21.5, Z2, 2.4, "WoodLight", "WoodMid", G)
        C(X + a, Y + 20.6, Z2 + 2.4, Z2 + 3.0, 0.2, "Iron", G, 6); C(X + a, Y + 20.6, Z2 + 3.0, Z2 + 3.9, 0.55, "Lamp", G, 8)
    wardrobe(X + 47.6, Y + 1.9, Z2, "N", 5.6, G)
    h(60.4, 1.0, Z2, 65.0, 2.7, Z2 + 3.2, "WoodMid", G, True, "Dresser"); h(60.3, 0.95, Z2 + 3.2, 65.1, 2.8, Z2 + 3.45, "WoodDark", G)
    cabinet_doors("N", X + 62.7, Y + 2.7, 4.4, Z2, 2, G, "Gold")
    h(61.2, 0.82, Z2 + 4.2, 64.2, 0.98, Z2 + 8.2, "WoodDark", G); h(61.5, 0.98, Z2 + 4.5, 63.9, 1.04, Z2 + 7.9, "SkyBlue", G)
    rug(X + 49.0, Y + 3.6, X + 61.0, Y + 10.6, Z2, "ClothYellow", "ClothRed", G)
    picture(X + 55, Y + 21.7, Z2 + 8.4, "S", 6.0, 3.6, "grill", G)
    plant(X + 46.0, Y + 20.2, Z2, G, 1.2); ceiling_lamp(X + 55, Y + 9, ZW, G)
    # --- kid's room
    bed(X + 59.9, Y + 36.4, Z2, "W", 5.0, 9.6, "Cloth", G)
    table(X + 62.6, Y + 27.4, X + 65.0, Y + 33.0, Z2, 3.0, "WoodLight", "Blue", G)
    chair(X + 61.2, Y + 30.2, Z2, "E", "WoodMid", "Cloth", G)
    h(63.2, 28.2, Z2 + 3.0, 64.6, 29.6, Z2 + 3.06, "Paper", G); h(63.4, 31.0, Z2 + 3.0, 63.8, 31.4, Z2 + 3.9, "Red", G)
    h(45.0, 36.4, Z2, 48.6, 38.9, Z2 + 2.2, "Red", G, True, "ToyChest"); h(44.9, 36.3, Z2 + 2.2, 48.7, 39.0, Z2 + 2.6, "Yellow", G)
    ball(X + 51.5, Y + 37.4, Z2 + 0.9, 0.9, "White", G, seg=8, rings=4); ball(X + 46.5, Y + 33.6, Z2 + 0.7, 0.7, "Orange", G, seg=8, rings=4)
    K.kettle_grill(X + 51.0, Y + 33.0, 0.45, "Blue", False, True, 2, 0, G)
    shelf(X + 56, Y + 23.1, Z2, "N", 7.0, 6.0, 1.3, 51, G, "White")
    rug(X + 48.5, Y + 26.0, X + 58.5, Y + 33.5, Z2, "Cloth", "ClothYellow", G)
    picture(X + 64.8 + 0.4, Y + 24.6, Z2 + 7.4, "W", 3.2, 3.0, "kid", G)
    text("BBQ KID", X + 55, Y + 39.2, Z2 + 10.2, 0.16, "S", "Red", 0.0, 0.1, G)
    ceiling_lamp(X + 54, Y + 30, ZW, G)
    # --- bathroom
    h(23.2, 35.4, Z2, 31.4, 39.0, Z2 + 2.4, "White", G, True, "Tub"); h(23.7, 35.9, Z2 + 1.2, 30.9, 38.5, Z2 + 2.3, "Water", "Water")
    h(23.4, 37.0, Z2 + 2.4, 23.7, 37.4, Z2 + 3.6, "Chrome", G); h(23.4, 37.0, Z2 + 3.4, 24.6, 37.4, Z2 + 3.6, "Chrome", G)
    ball(X + 27.0, Y + 37.2, Z2 + 2.6, 0.55, "Yellow", G, seg=8, rings=4)
    h(40.4, 36.4, Z2, 42.6, 39.0, Z2 + 1.6, "White", G, True, "Toilet"); h(40.4, 38.2, Z2 + 1.6, 42.6, 39.0, Z2 + 4.0, "White", G)
    h(40.5, 36.5, Z2 + 1.6, 42.5, 38.2, Z2 + 1.8, "WallGrey", G)
    counter(X + 41.8, Y + 32.6, X + 43.6, Y + 35.6, Z2, G, "TileB", "White")
    C(X + 42.7, Y + 34.1, Z2 + 3.2, Z2 + 3.3, 0.7, "WallGrey", G, 8); h(43.3, 34.0, Z2 + 3.2, 43.5, 34.2, Z2 + 4.2, "Chrome", G)
    h(43.52, 32.7, Z2 + 4.8, 43.68, 35.5, Z2 + 8.6, "White", G); h(43.44, 33.0, Z2 + 5.1, 43.56, 35.2, Z2 + 8.3, "SkyBlue", G)
    h(26.0, 32.3, Z2 + 5.0, 30.6, 32.5, Z2 + 5.25, "Chrome", G); h(26.4, 32.3, Z2 + 2.6, 28.0, 32.6, Z2 + 5.1, "ClothRed", G); h(28.4, 32.3, Z2 + 3.2, 30.0, 32.6, Z2 + 5.1, "ClothWhite", G)
    rug(X + 32.0, Y + 33.0, X + 38.0, Y + 35.2, Z2, "ClothWhite", "Cloth", G)
    ceiling_lamp(X + 33, Y + 34.6, ZW, G)


# ------------------------------------------------------------------ yard
def smoker(x, y):
    """Big offset smoker, operator stands south of it. Exactly one tiny sausage on the grate."""
    G = "Grill"
    # barrel (octagon along x), bottom half; lid half tilted open at the back
    def sec(xx, cy, cz, r, a0, a1, n=5):
        return [(xx, cy + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cz + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    zc = 4.6; r = 2.6
    sc.loft([sec(x - 5, y, zc, r, 180, 360), sec(x + 5, y, zc, r, 180, 360)], "Black", G, True)
    sc.loft([sec(x - 5, y + 2.9, zc + 2.2, r, 60, 240), sec(x + 5, y + 2.9, zc + 2.2, r, 60, 240)], "Black", G, True)
    B(x - 1.2, y + 0.5, zc + 3.7, x + 1.2, y + 0.9, zc + 4.0, "WoodLight", G)
    B(x - 5.05, y - 2.75, zc - 0.25, x + 5.05, y + 2.75, zc - 0.05, "Coal", G)
    B(x - 4.6, y - 2.3, zc - 0.05, x + 4.6, y + 2.3, zc + 0.02, "Fire", G)
    for k in range(9):
        B(x - 4.9 + k * 1.15, y - 2.55, zc + 0.02, x - 4.75 + k * 1.15, y + 2.55, zc + 0.14, "Steel", G)
    B(x - 5.0, y - 2.6, zc + 0.02, x + 5.0, y - 2.45, zc + 0.14, "Steel", G); B(x - 5.0, y + 2.45, zc + 0.02, x + 5.0, y + 2.6, zc + 0.14, "Steel", G)
    hcyl("x", x - 0.3, x + 0.3, y - 0.3, zc + 0.24, 0.1, "Sausage", G, 6)     # the one tiny sausage
    # firebox on the right, chimney stack on the left
    B(x + 5.0, y - 1.8, zc - 3.0, x + 8.2, y + 1.8, zc + 0.2, "Black", G); B(x + 8.2, y - 1.0, zc - 2.2, x + 8.32, y + 1.0, zc - 0.6, "Fire", G)
    B(x + 5.6, y - 1.9, zc + 0.2, x + 7.6, y + 1.9, zc + 0.4, "Iron", G)
    C(x - 4.0, y + 1.2, zc + 1.0, zc + 7.6, 0.6, "Black", G, 8); C(x - 4.0, y + 1.2, zc + 7.6, zc + 7.9, 0.85, "Iron", G, 8)
    # legs, wheels, front shelf, thermometer, handle
    for (lx, ly) in ((x - 4.4, y - 1.8), (x - 4.4, y + 1.8), (x + 4.4, y - 1.8), (x + 4.4, y + 1.8)):
        B(lx - 0.18, ly - 0.18, 0.3, lx + 0.18, ly + 0.18, zc - 1.6, "Iron", G)
    B(x - 4.6, y - 2.0, 1.6, x + 4.6, y + 2.0, 1.8, "Iron", G)
    for ly in (y - 2.2, y + 2.0):
        hcyl("y", ly, ly + 0.3, x + 4.4, 1.4, 1.1, "Tire", G, 10)
    B(x - 4.6, y - 4.4, zc - 0.5, x + 4.6, y - 2.7, zc - 0.25, "WoodLight", G)
    for lx in (x - 4.2, x + 4.0):
        beam((lx, y - 4.2, zc - 0.5), (lx, y - 2.4, zc - 2.0), 0.16, "Iron", G)
    K.plate(x - 2.8, y - 3.5, zc - 0.25)
    for k in range(3):
        hcyl("x", x - 3.4, x - 2.2, y - 3.8 + k * 0.3, zc - 0.03, 0.13, "Sausage", G, 6)
    B(x + 1.6, y - 3.9, zc - 0.25, x + 3.4, y - 3.2, zc - 0.1, "Steel", G); B(x + 3.4, y - 3.65, zc - 0.22, x + 4.4, y - 3.45, zc - 0.12, "Black", G)
    COL(x - 5.2, y - 4.4, 0, x + 8.3, y + 2.8, zc + 0.3, "Smoker", G)
    K.smoke(x - 4.0, y + 1.2, zc + 8.4, 5, 1.0, 7); K.smoke(x + 1.5, y + 0.6, zc + 1.0, 3, 0.8, 9)
    sc.anchor("GrillFire", (x, y, zc + 0.5), range=18)


def yard():
    X, Y = HX, HY
    # front path with lanterns, driveway, pickup
    for k in range(9):
        B(245, 360 + k * 2.85, 0, 255, 360 + (k + 1) * 2.85 - 0.12, 0.22, "Paver" if k % 2 else "PaverC", "Yard")   # slightly below the 0.26 porch step so they don't z-fight where the path meets it
    COL(245, 360, 0, 255, 385.6, 0.26, "Path", "Yard")
    for yy in (365, 373, 381):
        for xx in (243.6, 256.4):
            B(xx - 0.4, yy - 0.4, 0, xx + 0.4, yy + 0.4, 1.6, "WoodDark", "Yard", True, "PathLantern")
            B(xx - 0.5, yy - 0.5, 1.6, xx + 0.5, yy + 0.5, 2.5, "Lamp", "Yard"); B(xx - 0.6, yy - 0.6, 2.5, xx + 0.6, yy + 0.6, 2.7, "WoodDark", "Yard")
            sc.anchor("LampLight", (xx, yy, 2.2), range=12)
    B(208, 360, 0, 228, Y + 6.0, 0.32, "Concrete", "Yard", True, "Driveway")
    for k in range(5):
        B(208, 368 + k * 7.0, 0.3, 228, 368.2 + k * 7.0, 0.34, "Curb", "Yard")
    K.car(218, 378, "S", "Red", "pickup")
    # front picket fence + mailbox + flamingo + gnome + bushes
    for (a0, a1) in ((178.6, 206.6), (229.4, 244.0), (256.0, 321.4)):
        K.picket_fence("x", 362.6, a0, a1)
    K.picket_fence("y", 178.6, 362.6, 403.4)
    K.picket_fence("y", 321.4, 362.6, 391.6)
    K.mailbox(241.2, 365.2, "S", "GRILL DAD")
    K.flamingo(236.5, 374.0, "E")
    K.gnome(314.0, 367.5, "S", 1.25)
    for (bx, by, s) in ((231.5, 392.0, 1.1), (235.0, 391.4, 0.9), (265.5, 392.2, 1.0), (269.5, 391.8, 1.15), (283.0, 366.0, 1.0), (262.0, 366.0, 0.9), (232.5, 366.0, 0.9)):
        K.bush(bx, by, s, 3)
    K.tree(300.0, 376.0, 1.3, 1); K.tree(191.0, 382.0, 1.15, 2)
    # backyard fence (plank) with the "DAD GRILLS BEST!" sign
    K.plank_fence("x", 392.0, 289.5, 322.0, seed=1)
    K.plank_fence("y", 322.0, 392.0, 474.0, seed=2)
    K.plank_fence("x", 474.0, 178.0, 322.0, seed=3)
    K.plank_fence("y", 178.0, 404.0, 474.0, seed=4)
    K.plank_fence("x", 404.0, 178.0, 205.6, seed=5)
    FB("W", 321.6, 410.0, -5.2, 0.0, 3.4, 5.2, 0.3, 7.6, "Paper", "Signs")
    FB("W", 321.6, 410.0, -5.4, 0.0, 3.2, 5.4, 0.36, 3.4, "WoodDark", "Signs"); FB("W", 321.6, 410.0, -5.4, 0.0, 7.6, 5.4, 0.36, 7.8, "WoodDark", "Signs")
    text("DAD GRILLS", 321.3, 410.0, 6.4, 0.15, "W", "Black", 0.0, 0.1)
    text("BEST!", 321.3, 410.0, 4.6, 0.19, "W", "Red", 0.0, 0.1)
    # same sign on the front part of the fence so it reads from the street
    FB("S", 305.5, 391.65, -5.2, 0.0, 3.4, 5.2, 0.3, 7.6, "Paper", "Signs")
    text("DAD GRILLS", 305.5, 391.35, 6.4, 0.15, "S", "Black", 0.0, 0.1)
    text("BEST!", 305.5, 391.35, 4.6, 0.19, "S", "Red", 0.0, 0.1)
    # patio pavers
    for i in range(12):
        for j in range(12):
            x0 = 274.0 + i * 3.9; y0 = 394.0 + j * 3.9
            if x0 < 276.5 and 417.5 < y0 < 424.0: continue
            B(x0 + 0.05, y0 + 0.05, 0, x0 + 3.85, y0 + 3.85, 0.3, ["Paver", "PaverC", "PaverB"][(i * 2 + j) % 3], "Yard")
    COL(274, 394, 0, 320.8, 440.8, 0.3, "Patio", "Yard")
    B(272.2, 424.2, 0, 280, 432.0, 0.62, "StoneC", "Yard", True, "PatioStep")   # step to the kitchen door
    # grill zone
    smoker(304.0, 432.5)
    sc.anchor("FatherSpot", (304.0, 426.0, 0.3), note="Grill Dad stands here, facing north to the smoker (character model not included)")
    TARGETS["FatherSpot (grill)"] = (304.0, 426.0, 0.3)
    table(292.0, 431.0, 297.6, 434.2, 0.3, 3.3, "WoodLight", "WoodDark", "Yard")
    for k in range(6):
        C(293.2, 432.6, 3.6 + k * 0.12, 3.68 + k * 0.12, 0.75, "White", "Yard", 8)
    B(294.6, 432.0, 3.6, 295.0, 432.4, 4.7, "Ketchup", "Yard"); B(295.3, 432.0, 3.6, 295.7, 432.4, 4.7, "Mustard", "Yard")
    C(296.8, 433.0, 3.6, 4.9, 0.5, "White", "Yard", 8); C(296.8, 433.0, 3.6, 5.0, 0.15, "Paper", "Yard", 6)
    K.plate(296.4, 431.7, 3.6); K.burger(296.4, 431.7, 3.7, 0.75)
    # tool rack on the east fence
    FB("W", 321.6, 428.0, -4.0, 0.0, 6.0, 4.0, 0.25, 6.5, "WoodDark", "Yard")
    for i, (m, ln) in enumerate((("Steel", 2.6), ("Black", 3.0), ("Steel", 2.2), ("Red", 2.8), ("Steel", 2.5))):
        FB("W", 321.6, 428.0, -3.2 + i * 1.6, 0.25, 6.2 - ln, -2.9 + i * 1.6, 0.4, 6.2, m, "Yard")
        FB("W", 321.6, 428.0, -3.5 + i * 1.6, 0.25, 6.2 - ln - 0.9, -2.6 + i * 1.6, 0.42, 6.2 - ln, "Steel", "Yard")
    for (bx, by) in ((319.0, 418.0), (319.0, 421.4), (316.4, 419.6)):
        K.charcoal_bag(bx, by, "W")
    K.umbrella_table(290.0, 410.0, "Red", "White", 4)
    K.picnic_table(306.0, 402.0, "x", True, True, 1)
    K.kettle_grill(316.0, 399.0, 1.0, "Red", True, True, 4, 3)
    # string lights over the patio
    K.string_lights((X + 73.4, Y + 20.4, 12.8), (321.6, 414.0, 7.8), 12, 1.6)
    K.string_lights((X + 66.2, Y + 39.8, 12.6), (321.6, 440.0, 7.8), 14, 1.8)
    K.string_lights((321.6, 394.0, 7.6), (321.6, 440.0, 7.6), 14, 0.9)
    K.string_lights((290.0, 392.0, 7.6), (321.6, 392.4, 7.6), 9, 0.8)
    # rear yard: pool with duck, dog house, veggie beds, tree with swing, laundry
    K.kiddie_pool(292.0, 456.0, 6.0)
    K.tree(190.0, 452.0, 1.3, 7)
    beam((193.5, 452.0, 9.0), (193.5, 452.0, 2.6), 0.12, "Paper", "Yard"); beam((196.5, 452.0, 9.0), (196.5, 452.0, 2.6), 0.12, "Paper", "Yard")
    B(193.0, 451.3, 2.3, 197.0, 452.7, 2.6, "WoodLight", "Yard"); B(189, 451.6, 8.8, 197.2, 452.4, 9.4, "Trunk", "Yard")
    # dog house
    B(226, 460, 0, 234, 467, 0.3, "WoodDark", "Yard"); B(226.3, 460.3, 0.3, 233.7, 466.7, 4.6, "HouseRed", "Yard", True, "DogHouse")
    sc.gable_y(225.6, 234.4, 459.6, 467.4, 4.6, 7.4, "RoofRedB", "Yard")
    B(228.6, 460.2, 0.3, 231.4, 460.34, 3.2, "Black", "Yard"); text("BUN", 230.0, 460.3, 4.0, 0.14, "S", "White", 0.0, 0.08)
    B(222.6, 461.0, 0, 224.6, 463.0, 0.5, "Blue", "Yard"); C(223.6, 462.0, 0.5, 0.6, 0.7, "Water", "Water", 8)
    for i in range(3):
        K.flowerbed(240.0 + i * 12.0, 464.0, 249.0 + i * 12.0, 471.0, 20 + i, 0.0, "WoodMid")
        for k in range(4):
            xx = 241.6 + i * 12.0 + k * 1.9
            B(xx, 465.4, 0.6, xx + 0.5, 465.9, 2.4, "Leaf", "Flowers"); B(xx - 0.2, 465.2, 2.0, xx + 0.7, 466.1, 2.9, ["FlowerRed", "Orange", "Yellow"][i], "Flowers")
    B(206, 446, 0, 206.6, 446.6, 8.0, "WoodMid", "Yard", True, "LaundryPost"); B(224, 446, 0, 224.6, 446.6, 8.0, "WoodMid", "Yard", True, "LaundryPost")
    beam((206.3, 446.3, 7.8), (224.3, 446.3, 7.8), 0.1, "Paper", "Yard")
    for i, m in enumerate(["Red", "ClothWhite", "Cloth", "ClothYellow", "Red"]):
        B(208 + i * 3.2, 446.2, 4.6 + (i % 2) * 0.6, 210.4 + i * 3.2, 446.4, 7.7, m, "Yard")
    K.bush(184.0, 468.0, 1.2, 9); K.bush(316.0, 468.0, 1.2, 10); K.bush(268.0, 444.0, 1.0, 11)
    B(271.2, 437.0, 0, 278.0, 439.0, 2.6, "Trunk", "Yard", True, "Firewood")
    for k in range(5):
        for j in range(3):
            hcyl("y", 437.0 - 0.05, 439.05, 271.9 + k * 1.3, 0.55 + j * 0.85, 0.42, "WoodLight", "Yard", 6)
    TARGETS["patio"] = (296, 420, 0.3); TARGETS["rear yard"] = (250, 456, 0.0); TARGETS["driveway"] = (218, 364, 0.3)
    TARGETS["west yard"] = (190, 430, 0.0)
