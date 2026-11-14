"""Grill Dad District 500x500: ground, road grid, sidewalks, gate arch, Grill Dad Park, ten closed-facade neighbours,
grill water tower, billboard, cliffs with a waterfall, street props and scattered vegetation."""
import math, random
import gd_kit as K
from gd_kit import B, C, COL, FB, FP, text, icon, pix, ball, ring, hcyl, beam, roof_gable, FACE, OPP
import gd_house

sc = None
KEEP = []          # keep-out rectangles for scattered vegetation
TARGETS = {}
ROADS_H = (146.0, 330.0)   # y0 of the two east-west roads (24 wide)
ROADS_V = (146.0, 330.0)   # x0 of the two north-south roads
RW = 24.0


def keep(x0, y0, x1, y1):
    KEEP.append((min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)))


def build(scene):
    global sc
    sc = scene
    K.init(scene)
    ground()
    roads()
    gate()
    park()
    gd_house.build(scene)
    keep(170, 354, 330, 500)
    neighbours()
    landmarks()
    perimeter()
    street()
    scatter()
    TARGETS.update(gd_house.TARGETS)


# ------------------------------------------------------------------ ground + roads
def ground():
    r = random.Random(11)
    for i in range(20):
        for j in range(20):
            n = math.sin(i * 0.9 + j * 0.5) + math.cos(j * 0.8 - i * 0.35) + r.uniform(-0.5, 0.5)
            m = "GrassC" if n > 0.9 else ("GrassB" if n < -0.7 else "Grass")
            sc.box(i * 25, j * 25, -6, i * 25 + 25, j * 25 + 25, 0, m, "Terrain", True, "Ground")
    # darker / lighter mowing patches for texture
    for _ in range(170):
        x, y = r.uniform(14, 486), r.uniform(14, 486)
        if on_road(x, y, 9) or (170 < x < 330 and 354 < y < 500 and r.random() < 0.7): continue
        w, d = r.uniform(3, 8), r.uniform(3, 8)
        B(x - w, y - d, -0.2, x + w, y + d, 0.03 + r.uniform(0, 0.02), r.choice(["GrassB", "GrassC"]), "Terrain")


def on_road(x, y, m=0.0):
    for v in ROADS_V:
        if v - 6 - m < x < v + RW + 6 + m: return True
    for hh in ROADS_H:
        if hh - 6 - m < y < hh + RW + 6 + m: return True
    if 232 - m < x < 268 + m and y < 146: return True
    return False


def roads():
    G = "Roads"
    def road(x0, y0, x1, y1):
        B(x0, y0, -0.1, x1, y1, 0.2, "Asphalt", G, True, "Road")
    for y0 in ROADS_H: road(0.05, y0, 499.95, y0 + RW)
    for x0 in ROADS_V:
        for (a, b) in ((0.05, 146), (170, 330), (354, 499.95)): road(x0, a, x0 + RW, b)
    road(238, 0.05, 262, 146)
    # dashed centre lines
    def dash(axis, c, a0, a1, mat="RoadYellow"):
        a = a0 + 2
        while a + 4 <= a1 - 1:
            if axis == "x": B(a, c - 0.3, 0.1, a + 4, c + 0.3, 0.24, mat, G)
            else: B(c - 0.3, a, 0.1, c + 0.3, a + 4, 0.24, mat, G)
            a += 8
    for y0 in ROADS_H:
        for (a, b) in ((8, 136), (180, 228 if y0 < 200 else 320), (272 if y0 < 200 else 320, 320), (364, 492)):
            if b > a: dash("x", y0 + 12, a, b)
    for x0 in ROADS_V:
        for (a, b) in ((8, 136), (180, 320), (364, 492)): dash("y", x0 + 12, a, b)
    dash("y", 250, 16, 134)
    # zebra crossings at the four park corners + gate junction
    def zebra_over_h(xa, xb, y0):   # pedestrians cross an east-west road
        y = y0 + 1.2
        while y + 1.6 < y0 + RW:
            B(xa, y, 0.1, xb, y + 1.6, 0.25, "RoadLine", G); y += 3.1
    def zebra_over_v(ya, yb, x0):
        x = x0 + 1.2
        while x + 1.6 < x0 + RW:
            B(x, ya, 0.1, x + 1.6, yb, 0.25, "RoadLine", G); x += 3.1
    for x0 in ROADS_V:
        for y0 in ROADS_H:
            zebra_over_h(x0 - 8, x0 - 2, y0); zebra_over_h(x0 + RW + 2, x0 + RW + 8, y0)
            zebra_over_v(y0 - 8, y0 - 2, x0); zebra_over_v(y0 + RW + 2, y0 + RW + 8, x0)
    zebra_over_v(136, 142, 238)
    zebra_over_h(244, 256, 146); zebra_over_h(244, 256, 330)
    zebra_over_v(244, 256, 146); zebra_over_v(244, 256, 330)
    # sidewalks: 6 wide inside every block edge that touches a road
    blocks = [(0, 0, 146, 146, "NE"), (354, 0, 500, 146, "NW"), (0, 354, 146, 500, "SE"), (354, 354, 500, 500, "SW"),
              (170, 0, 238, 146, "NWE"), (262, 0, 330, 146, "NWE"), (170, 354, 330, 500, "SWE"),
              (0, 170, 146, 330, "NSE"), (354, 170, 500, 330, "NSW"), (170, 170, 330, 330, "NSWE")]
    def strip(x0, y0, x1, y1, axis, road_side):
        COL(x0, y0, 0, x1, y1, 0.48, "Sidewalk", G)
        # curb on the road side, slabs on the rest
        if axis == "x":
            cy0, cy1 = (y0, y0 + 0.6) if road_side < 0 else (y1 - 0.6, y1)
            B(x0, cy0, 0, x1, cy1, 0.52, "Curb", G)
            s0, s1 = (y0 + 0.6, y1) if road_side < 0 else (y0, y1 - 0.6)
            n = max(1, int(round((x1 - x0) / 6.0))); st = (x1 - x0) / n
            for i in range(n):
                B(x0 + i * st + 0.04, s0, 0, x0 + (i + 1) * st - 0.04, s1, 0.45, "Sidewalk" if i % 2 else "SidewalkB", G)
        else:
            cx0, cx1 = (x0, x0 + 0.6) if road_side < 0 else (x1 - 0.6, x1)
            B(cx0, y0, 0, cx1, y1, 0.52, "Curb", G)
            s0, s1 = (x0 + 0.6, x1) if road_side < 0 else (x0, x1 - 0.6)
            n = max(1, int(round((y1 - y0) / 6.0))); st = (y1 - y0) / n
            for i in range(n):
                B(s0, y0 + i * st + 0.04, 0, s1, y0 + (i + 1) * st - 0.04, 0.45, "Sidewalk" if i % 2 else "SidewalkB", G)
    for (x0, y0, x1, y1, sides) in blocks:
        if "S" in sides: strip(x0, y0, x1, y0 + 6, "x", -1)
        if "N" in sides: strip(x0, y1 - 6, x1, y1, "x", 1)
        ya = y0 + 6 if "S" in sides else y0
        yb = y1 - 6 if "N" in sides else y1
        if "W" in sides: strip(x0, ya, x0 + 6, yb, "y", -1)
        if "E" in sides: strip(x1 - 6, ya, x1, yb, "y", 1)


# ------------------------------------------------------------------ gate arch
def gate():
    G = "Gate"
    r = random.Random(21)
    for (x0, x1, art) in ((226.0, 236.0, "flame"), (264.0, 274.0, "dad")):
        B(x0 - 0.8, 3.2, 0, x1 + 0.8, 11.8, 2.0, "StoneB", G, True, "GatePillar")
        B(x0, 4, 2.0, x1, 11, 15.0, "Stone", G, True, "GatePillar")
        B(x0 - 0.6, 3.4, 15.0, x1 + 0.6, 11.6, 16.2, "StoneC", G)
        B(x0 + 1.0, 5.0, 16.2, x1 - 1.0, 10.0, 16.8, "StoneB", G)
        used = set()
        for k in range(40):   # protruding stone blocks on a grid (no overlaps)
            row = r.randint(0, 7); slot = r.randint(0, 2); south = r.random() < 0.5
            if (row, slot, south) in used: continue
            used.add((row, slot, south))
            z = 2.4 + row * 1.5; a = x0 + 0.5 + slot * 3.1 + (0.6 if row % 2 else 0.0)
            m = r.choice(["StoneC", "StoneB"])
            if 6.0 < z + 1.1 and z < 12.8 and slot == 1: continue
            if south: B(a, 3.9, z, a + 2.4, 4.02, z + 1.1, m, G)
            else: B(a, 10.98, z, a + 2.4, 11.1, z + 1.1, m, G)
        cx = (x0 + x1) / 2
        B(cx - 1.4, 6.1, 16.8, cx + 1.4, 8.9, 17.1, "Iron", G); B(cx - 1.0, 6.5, 17.1, cx + 1.0, 8.5, 19.6, "Lamp", G)
        for (dx, dy) in ((-1.15, -1.15), (1.15, -1.15), (-1.15, 1.15), (1.15, 1.15)):
            B(cx + dx - 0.15, 7.5 + dy - 0.15, 17.1, cx + dx + 0.15, 7.5 + dy + 0.15, 19.6, "Iron", G)
        sc.pyramid_roof(cx - 1.7, 5.8, cx + 1.7, 9.2, 19.6, 21.2, "Iron", G)
        sc.anchor("LampLight", (cx, 7.5, 18.4), range=40)
        for face, yy in (("S", 3.98), ("N", 11.02)):
            B(cx - 3.2, yy - 0.12 if face == "S" else yy, 6.4, cx + 3.2, yy if face == "S" else yy + 0.12, 12.6, "Navy", G)
            if art == "dad": icon(K.DAD_FACE, {"h": "Brown", "y": "Yellow", "b": "Black"}, cx, yy - 0.12 if face == "S" else yy + 0.12, 9.5, 0.42, face, 0.0, 0.14)
            else: icon(K.FLAME_ICON, {"o": "Fire", "y": "FireY", "w": "White"}, cx, yy - 0.12 if face == "S" else yy + 0.12, 9.5, 0.55, face, 0.0, 0.14)
    # sign board with stepped arched top
    B(233.0, 6.7, 14.8, 267.0, 8.3, 23.2, "Brown", G)
    B(237.0, 6.7, 23.2, 263.0, 8.3, 24.4, "Brown", G); B(242.0, 6.7, 24.4, 258.0, 8.3, 25.3, "Brown", G)
    for (a, b, z0, z1) in ((233.0, 267.0, 14.3, 14.8), (232.6, 237.0, 23.2, 23.7), (263.0, 267.4, 23.2, 23.7), (236.6, 242.0, 24.4, 24.9), (258.0, 263.4, 24.4, 24.9), (241.6, 258.4, 25.3, 25.8)):
        B(a, 6.5, z0, b, 8.5, z1, "Gold", G)
    COL(232.6, 6.5, 14.3, 267.4, 8.5, 25.8, "GateSign", G)
    for face, yy in (("S", 6.7), ("N", 8.3)):
        text("GRILL DAD", 250, yy, 20.8, 0.5, face, "White", -0.02, 0.22)
        text("DISTRICT", 250, yy, 16.9, 0.42, face, "FireY", -0.02, 0.22)
        for a in (234.9, 265.1):
            icon(K.FLAME_ICON, {"o": "Fire", "y": "FireY", "w": "White"}, a, yy, 20.6, 0.4, face, -0.02, 0.24)
    icon(K.spatulas_icon(), {"s": "Chrome"}, 250, 7.5, 28.0, 0.36, "S", -0.35, 0.35)
    # low stone walls, hedges and flower beds beside the gate
    for (a, b) in ((178.0, 225.0), (275.0, 322.0)):
        B(a, 5.5, 0, b, 8.5, 3.0, "Stone", G, True, "GateWall"); B(a - 0.2, 5.3, 3.0, b + 0.2, 8.7, 3.5, "StoneC", G)
        K.hedge(a + 1, 9.0, b - 1, 11.6, 4.2, 5)
        K.flowerbed(a + 2, 13.5, b - 2, 17.0, 6)
        keep(a - 2, 0, b + 2, 20)
    sc.anchor("PlayerStart", (250, 24, 1.5))
    sc.anchor("DistrictEntrance", (250, 2, 0.2), note="south gate: connector to the city / forest road (to be wired by the owner)")
    TARGETS["gate"] = (250, 24, 0.2)


# ------------------------------------------------------------------ park
def park():
    G = "Park"
    # paths
    def path(x0, y0, x1, y1, axis):
        COL(x0, y0, 0, x1, y1, 0.28, "ParkPath", G)
        if axis == "y":
            B(x0, y0, 0, x0 + 0.6, y1, 0.3, "PaverB", G); B(x1 - 0.6, y0, 0, x1, y1, 0.3, "PaverB", G)
            n = int(round((y1 - y0) / 4.0)); st = (y1 - y0) / n
            for i in range(n): B(x0 + 0.6, y0 + i * st + 0.04, 0, x1 - 0.6, y0 + (i + 1) * st - 0.04, 0.25, "Paver" if i % 2 else "PaverC", G)
        else:
            B(x0, y0, 0, x1, y0 + 0.6, 0.3, "PaverB", G); B(x0, y1 - 0.6, 0, x1, y1, 0.3, "PaverB", G)
            n = int(round((x1 - x0) / 4.0)); st = (x1 - x0) / n
            for i in range(n): B(x0 + i * st + 0.04, y0 + 0.6, 0, x0 + (i + 1) * st - 0.04, y1 - 0.6, 0.25, "Paver" if i % 2 else "PaverC", G)
    path(245, 176, 255, 224, "y"); path(245, 276, 255, 324, "y"); path(176, 245, 224, 255, "x"); path(276, 245, 324, 255, "x")
    # plaza rings
    for (r0, r1, m, zt) in ((8.0, 14.0, "Paver", 0.3), (14.0, 20.0, "PaverC", 0.3), (20.0, 25.0, "Paver", 0.3), (25.0, 27.5, "PaverB", 0.36)):
        for k in range(24):
            ring(250, 250, r0, r1, 0, zt + (0.02 if (k % 2 and m != "PaverB") else 0.0), m if (k % 2 or m == "PaverB") else ("PaverC" if m == "Paver" else "Paver"), G, 24, k * 15, (k + 1) * 15)
    COL(226, 226, 0, 274, 274, 0.3, "Plaza", G)
    monument()
    # planters around the monument
    for k in range(8):
        a = math.radians(22.5 + k * 45)
        px, py = 250 + 13.5 * math.cos(a), 250 + 13.5 * math.sin(a)
        K.flowerbed(px - 2.0, py - 2.0, px + 2.0, py + 2.0, 30 + k, 0.3, "StoneC")
    # benches facing the monument
    for (bx, by, f) in ((238, 271.5, "S"), (262, 271.5, "S"), (238, 228.5, "N"), (262, 228.5, "N"), (271.5, 238, "W"), (271.5, 262, "W"), (228.5, 238, "E"), (228.5, 262, "E")):
        K.bench(bx, by, f)
    # banner lamps at the four entries + plain lamps on the diagonals
    for (lx, ly, f) in ((242.6, 181, "S"), (257.4, 181, "N"), (242.6, 319, "S"), (257.4, 319, "N"), (181, 242.6, "E"), (181, 257.4, "W"), (319, 242.6, "E"), (319, 257.4, "W")):
        K.lamp_post(lx, ly, f)
    for (lx, ly) in ((229.5, 229.5), (270.5, 229.5), (229.5, 270.5), (270.5, 270.5)):
        K.lamp_post(lx, ly, None, 11.0)
    # border hedges with gaps at the entries
    for (a, b) in ((178.0, 240.0), (260.0, 322.0)):
        K.hedge(a, 177.2, b, 179.6, 3.0, 1); K.hedge(a, 320.4, b, 322.8, 3.0, 2)
        K.hedge(177.2, a + 2.4 if a < 200 else a, 179.6, b if a < 200 else b - 2.4, 3.0, 3); K.hedge(320.4, a + 2.4 if a < 200 else a, 322.8, b if a < 200 else b - 2.4, 3.0, 4)
    gazebo(205, 296)
    pond(205, 206)
    food_truck(296, 204)
    picnic_lawn()
    # park trees + bushes
    for (tx, ty, s) in ((186, 236, 1.2), (236, 186, 1.1), (264, 186, 1.15), (314, 236, 1.2), (186, 264, 1.2), (236, 314, 1.1), (264, 314, 1.15), (314, 264, 1.2), (184, 184, 1.0), (316, 316, 1.0), (316, 184, 1.0)):
        K.tree(tx, ty, s, int(tx + ty))
    for (bx, by) in ((240.5, 190), (259.5, 190), (240.5, 206), (259.5, 206), (240.5, 294), (259.5, 294), (240.5, 310), (259.5, 310), (190, 240.5), (206, 240.5), (294, 259.5), (310, 259.5), (190, 259.5), (310, 240.5)):
        K.bush(bx, by, 0.9, int(bx * 3 + by))
    for (x0, y0, x1, y1) in ((238.0, 194, 242.0, 202), (258.0, 194, 262.0, 202), (238.0, 298, 242.0, 306), (258.0, 298, 262.0, 306), (194, 238.0, 202, 242.0), (298, 258.0, 306, 262.0), (194, 258.0, 202, 262.0), (298, 238.0, 306, 242.0)):
        K.flowerbed(x0, y0, x1, y1, int(x0 + y0))
    sc.anchor("ParkCenter", (250, 232, 0.3))
    TARGETS["park plaza"] = (250, 232, 0.3); TARGETS["park south entry"] = (250, 180, 0.25); TARGETS["park north entry"] = (250, 320, 0.25)


def monument():
    G = "Monument"
    for k in range(8):
        ring(250, 250, 0.0, 9.0, 0.3, 1.3, "StoneC" if k % 2 else "Stone", G, 8, k * 45 + 22.5, (k + 1) * 45 + 22.5)
    B(244.5, 244.5, 1.3, 255.5, 255.5, 7.0, "Stone", G); B(243.9, 243.9, 7.0, 256.1, 256.1, 7.8, "StoneC", G)
    B(244.1, 244.1, 1.32, 255.9, 255.9, 2.1, "StoneB", G)
    COL(242, 242, 0, 258, 258, 1.3, "MonumentBase", G); COL(243.9, 243.9, 1.3, 256.1, 256.1, 7.8, "Monument", G)
    for face, (px, py) in (("S", (250, 244.5)), ("N", (250, 255.5)), ("E", (255.5, 250)), ("W", (244.5, 250))):
        FB(face, px, py, -5.0, 0.0, 2.5, 5.0, 0.16, 6.4, "Navy", G)
        for (z0, z1) in ((2.3, 2.5), (6.4, 6.6)): FB(face, px, py, -5.2, 0.0, z0, 5.2, 0.22, z1, "Gold", G)
        qx, qy = FP(face, px, py, 0, 0.16)
        text("GRILL DAD", qx, qy, 5.2, 0.17, face, "Gold", 0.0, 0.1)
        text("PARK", qx, qy, 3.5, 0.17, face, "GoldC", 0.0, 0.1)
    # golden kettle grill
    for k in range(3):
        a = math.radians(90 + 120 * k)
        beam((250 + 4.6 * math.cos(a), 250 + 4.6 * math.sin(a), 7.8), (250 + 3.0 * math.cos(a), 250 + 3.0 * math.sin(a), 12.6), 0.7, "GoldB", G)
        B(250 + 4.6 * math.cos(a) - 0.7, 250 + 4.6 * math.sin(a) - 0.7, 7.8, 250 + 4.6 * math.cos(a) + 0.7, 250 + 4.6 * math.sin(a) + 0.7, 8.3, "GoldB", G)
    ball(250, 250, 16.2, 7.2, "Gold", G, lat0=-90, lat1=0, seg=16, rings=6, rz=5.6)
    ring(250, 250, 7.0, 7.7, 15.9, 16.5, "GoldB", G, 16)
    C(250, 250, 16.2, 16.9, 6.5, "Fire", G, 16)
    ring(250, 250, 7.0, 7.6, 16.9, 17.3, "GoldB", G, 16)
    ball(250, 250, 17.1, 7.2, "GoldC", G, lat0=0, lat1=90, seg=16, rings=6, rz=5.0)
    C(250, 250, 22.0, 22.6, 1.4, "GoldB", G, 10)
    B(249.5, 248.6, 22.6, 250.5, 249.0, 23.8, "GoldB", G); B(249.5, 251.0, 22.6, 250.5, 251.4, 23.8, "GoldB", G); B(249.4, 248.5, 23.8, 250.6, 251.5, 24.4, "Black", G)
    for sgn in (-1, 1):
        B(250 + sgn * 7.4, 249.0, 15.2, 250 + sgn * 8.8, 251.0, 15.7, "GoldB", G)
        B(250 + sgn * 8.3, 248.6, 15.1, 250 + sgn * 8.9, 251.4, 15.9, "Black", G)
        K.smoke(250 + sgn * 3.2, 250 + sgn * 1.4, 22.2, 4, 0.9, 4 + sgn)
    K.smoke(250, 250, 24.8, 5, 1.0, 3)
    COL(243, 243, 10.6, 257, 257, 22.5, "GoldenGrill", G)
    sc.anchor("MonumentLight", (250, 250, 17.0), range=60)
    for (lx, ly) in ((240.6, 240.6), (259.4, 240.6), (240.6, 259.4), (259.4, 259.4)):   # small up-lights
        B(lx - 0.5, ly - 0.5, 0.3, lx + 0.5, ly + 0.5, 0.9, "Iron", G); B(lx - 0.35, ly - 0.35, 0.9, lx + 0.35, ly + 0.35, 1.1, "Lamp", G)


def gazebo(cx, cy):
    G = "Park"
    x0, x1, y0, y1 = cx - 14, cx + 14, cy - 11, cy + 11
    B(x0, y0, 0, x1, y1, 0.3, "StoneB", G)
    COL(x0, y0, 0, x1, y1, 0.55, "GazeboDeck", G)
    for k in range(22):
        B(x0 + 0.05, y0 + k * 1.0 + 0.04, 0.3, x1 - 0.05, y0 + (k + 1) * 1.0 - 0.04, 0.55, ["Plank", "PlankB", "PlankC"][k % 3], G)
    posts = [(x0 + 0.8, y0 + 0.8), (x1 - 0.8, y0 + 0.8), (x0 + 0.8, y1 - 0.8), (x1 - 0.8, y1 - 0.8), (cx, y1 - 0.8), (x0 + 0.8, cy), (x1 - 0.8, cy)]
    for (px, py) in posts:
        B(px - 0.75, py - 0.75, 0.55, px + 0.75, py + 0.75, 1.8, "StoneC", G, True, "GazeboPost")
        B(px - 0.45, py - 0.45, 1.8, px + 0.45, py + 0.45, 11.6, "WoodMid", G, True, "GazeboPost")
        B(px - 0.7, py - 0.7, 11.6, px + 0.7, py + 0.7, 12.0, "WoodDark", G)
    # rails on the west, north and east sides
    def rail(a0, b0, a1, b1):
        B(a0, b0, 3.4, a1, b1, 3.7, "WoodDark", G); B(a0, b0, 1.0, a1, b1, 1.25, "WoodDark", G)
        COL(a0, b0, 0.55, a1, b1, 3.7, "GazeboRail", G)
        if a1 - a0 > b1 - b0:
            n = int((a1 - a0) / 1.0)
            for i in range(n):
                u = a0 + (i + 0.5) * (a1 - a0) / n; B(u - 0.14, b0 + 0.03, 1.25, u + 0.14, b1 - 0.03, 3.4, "WoodLight", G)
        else:
            n = int((b1 - b0) / 1.0)
            for i in range(n):
                u = b0 + (i + 0.5) * (b1 - b0) / n; B(a0 + 0.03, u - 0.14, 1.25, a1 - 0.03, u + 0.14, 3.4, "WoodLight", G)
    rail(x0 + 1.4, y1 - 0.95, cx - 0.6, y1 - 0.65); rail(cx + 0.6, y1 - 0.95, x1 - 1.4, y1 - 0.65)
    rail(x0 + 0.65, y0 + 1.4, x0 + 0.95, cy - 0.6); rail(x0 + 0.65, cy + 0.6, x0 + 0.95, y1 - 1.4)
    rail(x1 - 0.95, y0 + 1.4, x1 - 0.65, cy - 0.6); rail(x1 - 0.95, cy + 0.6, x1 - 0.65, y1 - 1.4)
    # roof: beams, tiered hip roof, finial
    B(x0 - 0.2, y0 - 0.2, 12.0, x1 + 0.2, y1 + 0.2, 12.7, "WoodDark", "ParkRoof")
    sc.pyramid_roof(x0 - 2.6, y0 - 2.6, x1 + 2.6, y1 + 2.6, 12.7, 18.2, "RoofRed", "ParkRoof")
    sc.pyramid_roof(x0 + 5.0, y0 + 4.0, x1 - 5.0, y1 - 4.0, 16.2, 21.0, "RoofRedC", "ParkRoof")
    for (px, py) in ((x0 - 2.6, y0 - 2.6), (x1 + 2.6, y0 - 2.6), (x0 - 2.6, y1 + 2.6), (x1 + 2.6, y1 + 2.6)):
        beam((px, py, 12.9), (cx, cy, 18.5), 0.7, "RoofRedD", "ParkRoof")
    B(cx - 0.3, cy - 0.3, 20.6, cx + 0.3, cy + 0.3, 22.4, "Gold", "ParkRoof"); ball(cx, cy, 23.0, 0.9, "Gold", "ParkRoof", seg=8, rings=4)
    for (a, b, c_, d) in ((x0 - 2.7, y0 - 2.75, x1 + 2.7, y0 - 2.5), (x0 - 2.7, y1 + 2.5, x1 + 2.7, y1 + 2.75), (x0 - 2.75, y0 - 2.5, x0 - 2.5, y1 + 2.5), (x1 + 2.5, y0 - 2.5, x1 + 2.75, y1 + 2.5)):
        B(a, b, 12.3, c_, d, 13.0, "White", "ParkRoof")
    COL(x0 - 2.6, y0 - 2.6, 12.0, x1 + 2.6, y1 + 2.6, 15.0, "GazeboRoof", "ParkRoof")
    K.string_lights((x0 - 2.4, y0 - 2.8, 12.4), (x1 + 2.4, y0 - 2.8, 12.4), 16, 1.0)
    K.string_lights((x0 - 2.8, y0 - 2.4, 12.4), (x0 - 2.8, y1 + 2.4, 12.4), 12, 1.0)
    K.string_lights((x1 + 2.8, y0 - 2.4, 12.4), (x1 + 2.8, y1 + 2.4, 12.4), 12, 1.0)
    K.picnic_table(cx - 7, cy + 2, "x", True, True, 3); K.picnic_table(cx + 7, cy + 2, "x", True, True, 4)
    # tables stand on the deck: lift is small (0.55), acceptable overlap with planks is hidden by the legs
    sc.anchor("LampLight", (cx, cy, 11.0), range=44)
    # stepping stones from the plaza
    for k in range(5):
        px, py = 231 - k * 3.4, 268 + k * 3.2
        C(px, py, 0, 0.16, 1.5, "StoneC", G, 8)
    TARGETS["gazebo"] = (cx, cy - 6, 0.55)


def pond(cx, cy):
    G = "Park"
    for k in range(18):
        ring(cx, cy, 12.6, 14.6 + (0.3 if k % 2 else 0.0), 0, 1.0 + (0.25 if k % 3 == 0 else 0.0), ["StoneC", "Stone", "StoneB"][k % 3], G, 18, k * 20, (k + 1) * 20)
    C(cx, cy, 0, 0.25, 12.7, "Sand", G, 18); C(cx, cy, 0.25, 0.7, 12.65, "Water", "Water", 18)
    for (a, b, c_, d) in ((cx - 14.4, cy - 14.4, cx + 14.4, cy - 11.6), (cx - 14.4, cy + 11.6, cx + 14.4, cy + 14.4), (cx - 14.4, cy - 11.6, cx - 11.6, cy + 11.6), (cx + 11.6, cy - 11.6, cx + 14.4, cy + 11.6)):
        COL(a, b, 0, c_, d, 1.1, "PondRim", G)
    COL(cx - 11.6, cy - 11.6, 0, cx + 11.6, cy + 11.6, 0.7, "PondWater", G)
    # fountain
    C(cx, cy, 0.25, 2.2, 1.6, "StoneC", G, 10, True, "Fountain"); C(cx, cy, 2.2, 2.6, 2.6, "Stone", G, 10); C(cx, cy, 2.6, 5.4, 0.35, "Foam", "Water", 6)
    for k in range(6):
        a = math.radians(k * 60)
        beam((cx, cy, 5.2), (cx + 2.0 * math.cos(a), cy + 2.0 * math.sin(a), 3.0), 0.22, "Foam", "Water")
    # flamingo float, duck, lily pads
    fx, fy = cx - 5.5, cy + 3.5
    ring(fx, fy, 1.5, 3.0, 0.7, 1.7, "Pink", G, 12)
    B(fx + 2.4, fy - 0.35, 1.2, fx + 3.1, fy + 0.35, 4.6, "Pink", G); B(fx + 2.3, fy - 0.5, 4.6, fx + 3.9, fy + 0.5, 5.6, "Pink", G)
    B(fx + 3.9, fy - 0.25, 4.7, fx + 4.5, fy + 0.25, 5.2, "Yellow", G); B(fx + 4.5, fy - 0.2, 4.5, fx + 4.9, fy + 0.2, 5.0, "Black", G)
    B(fx + 3.0, fy - 0.55, 5.1, fx + 3.5, fy + 0.55, 5.4, "Black", G)
    ball(cx + 5.0, cy - 4.0, 1.25, 0.9, "Yellow", G, seg=8, rings=4, rz=0.7); ball(cx + 5.6, cy - 4.0, 2.1, 0.55, "Yellow", G, seg=8, rings=4)
    B(cx + 6.0, cy - 4.2, 1.95, cx + 6.5, cy - 3.8, 2.15, "Orange", G)
    for (lx, ly, rr) in ((cx + 3, cy + 6, 1.1), (cx - 2, cy - 7, 0.9), (cx + 7.5, cy + 2, 0.8), (cx - 7, cy - 3, 1.0)):
        C(lx, ly, 0.7, 0.78, rr, "LeafB", G, 8); B(lx - 0.25, ly - 0.25, 0.78, lx + 0.25, ly + 0.25, 1.1, "FlowerPink", G)
    K.bench(cx, cy + 17.5, "S"); K.bench(cx + 17.5, cy, "W")
    K.bush(cx - 13, cy - 15, 0.9, 5); K.bush(cx + 15, cy - 13, 0.9, 6)
    TARGETS["pond bench"] = (cx, cy + 20.5, 0.0)


def food_truck(cx, cy):
    G = "Truck"
    x0, x1, y0, y1 = cx - 12, cx + 10, cy - 4.5, cy + 4.5
    B(x0, y0, 1.8, x1, y1, 11.2, "SkyBlue", G)
    B(x0 - 0.05, y0 - 0.05, 1.75, x1 + 0.05, y1 + 0.05, 3.4, "Blue", G); B(x0 - 0.05, y0 - 0.05, 10.6, x1 + 0.05, y1 + 0.05, 11.3, "Blue", G)
    B(x0 + 0.5, y0 + 0.5, 11.2, x1 - 0.5, y1 - 0.5, 11.6, "White", G)
    # cab
    B(x1, y0 + 0.2, 1.8, x1 + 6.0, y1 - 0.2, 7.6, "Blue", G); B(x1 + 6.0, y0 + 0.5, 1.8, x1 + 6.4, y1 - 0.5, 3.4, "Chrome", G)
    B(x1 + 1.2, y0 + 0.12, 4.6, x1 + 5.0, y0 + 0.24, 7.0, "Glass", "Glass"); B(x1 + 1.2, y1 - 0.24, 4.6, x1 + 5.0, y1 - 0.12, 7.0, "Glass", "Glass")
    B(x1 + 5.98, y0 + 0.8, 4.4, x1 + 6.1, y1 - 0.8, 7.0, "Glass", "Glass")
    for yy in (y0 + 0.9, y1 - 1.9):
        B(x1 + 6.35, yy, 3.4, x1 + 6.5, yy + 1.0, 4.2, "Lamp", G)
    for wx in (x0 + 3.5, x1 - 2.5, x1 + 4.0):
        for (ya, yb) in ((y0 - 0.25, y0 + 0.9), (y1 - 0.9, y1 + 0.25)):
            hcyl("y", ya, yb, wx, 1.6, 1.6, "Tire", G, 10)
        hcyl("y", y0 - 0.35, y0 - 0.2, wx, 1.6, 0.8, "Chrome", G, 8); hcyl("y", y1 + 0.2, y1 + 0.35, wx, 1.6, 0.8, "Chrome", G, 8)
    COL(x0, y0, 0, x1 + 6.4, y1, 11.4, "FoodTruck", G)
    # serving window on the north side
    B(x0 + 3, y1 - 0.05, 5.2, x1 - 3, y1 + 0.08, 9.6, "Navy", G)
    B(x0 + 2.6, y1, 4.7, x1 - 2.6, y1 + 1.6, 5.2, "Steel", G); COL(x0 + 2.6, y1, 4.4, x1 - 2.6, y1 + 1.6, 5.2, "TruckCounter", G)
    for k, m in enumerate(["Red", "White"] * 4):
        a0 = x0 + 2.4 + k * 2.15
        sc.plate((a0, y1 + 0.05, 10.3), (a0 + 2.15, y1 + 0.05, 10.3), (a0 + 2.15, y1 + 3.4, 9.0), (a0, y1 + 3.4, 9.0), 0.22, m, G)
        B(a0, y1 + 3.3, 8.3, a0 + 2.15, y1 + 3.5, 9.0, m, G)
    for a in (x0 + 2.5, x1 - 2.7):
        beam((a + 0.1, y1 + 3.3, 8.9), (a + 0.1, y1 + 0.1, 6.0), 0.16, "Iron", G)
    K.burger(cx - 5, y1 + 0.8, 5.2, 0.9); K.burger(cx - 2.6, y1 + 0.8, 5.2, 0.9); K.cup(cx + 1, y1 + 0.7, 5.2, "Red"); K.cup(cx + 2.2, y1 + 0.9, 5.2, "Yellow")
    B(cx + 4, y1 + 0.5, 5.2, cx + 4.4, y1 + 0.9, 6.3, "Ketchup", G); B(cx + 4.8, y1 + 0.5, 5.2, cx + 5.2, y1 + 0.9, 6.3, "Mustard", G)
    # roof sign on both sides + flames + vent with smoke
    B(cx - 9.5, cy - 0.5, 11.6, cx + 8.5, cy + 0.5, 15.6, "Red", G)
    B(cx - 9.8, cy - 0.65, 15.6, cx + 8.8, cy + 0.65, 16.0, "Gold", G); B(cx - 9.8, cy - 0.65, 11.6, cx + 8.8, cy + 0.65, 11.9, "Gold", G)
    for face, yy in (("N", cy + 0.5), ("S", cy - 0.5)):
        text("DAD BBQ", cx - 0.5, yy, 13.8, 0.36, face, "FireY", -0.02, 0.2)
        for a in (cx - 8.6, cx + 7.6):
            icon(K.FLAME_ICON, {"o": "Fire", "y": "FireY", "w": "White"}, a, yy, 13.7, 0.2, face, -0.02, 0.2)
    icon(K.GRILL_ICON, {"1": "White"}, x0 + 1.6, y1 + 0.05, 7.4, 0.22, "N", 0.0, 0.14)
    icon(K.GRILL_ICON, {"1": "White"}, cx - 1, y0 - 0.05, 7.0, 0.5, "S", 0.0, 0.14)
    text("DAD BBQ", cx - 1, y0 - 0.05, 3.0, 0.16, "S", "White", 0.0, 0.12)
    C(x0 + 2.5, cy + 2.2, 11.6, 13.4, 0.7, "Steel", G, 8); K.smoke(x0 + 2.5, cy + 2.2, 13.8, 5, 1.2, 12)
    # menu board, tables, bin, lights
    B(cx - 16.5, y1 + 3.0, 0, cx - 13.5, y1 + 3.5, 5.0, "WoodDark", G, True, "MenuBoard")
    B(cx - 16.2, y1 + 3.5, 0.6, cx - 13.8, y1 + 3.62, 4.6, "Black", G)
    text("MENU", cx - 15.0, y1 + 3.62, 3.9, 0.08, "N", "White", 0.0, 0.06)
    for k, m in enumerate(["FireY", "White", "Red"]):
        B(cx - 16.0, y1 + 3.62, 2.9 - k * 0.7, cx - 14.4 + (k % 2) * 0.4, y1 + 3.68, 3.1 - k * 0.7, m, G)
    K.umbrella_table(cx - 12, cy + 22, "Yellow", "White", 4); K.umbrella_table(cx + 8, cy + 24, "Red", "White", 4)
    K.trash_can(cx + 14, y1 + 5)
    for (px, py) in ((cx - 20, cy + 14), (cx + 18, cy + 14)):
        B(px - 0.3, py - 0.3, 0, px + 0.3, py + 0.3, 12.5, "WoodDark", G, True, "LightPole")
    K.string_lights((cx - 20, cy + 14, 12.3), (x0 + 1, y1, 11.4), 8, 1.2); K.string_lights((cx + 18, cy + 14, 12.3), (x1 - 1, y1, 11.4), 8, 1.2)
    K.string_lights((cx - 20, cy + 14, 12.3), (cx + 18, cy + 14, 12.3), 16, 2.2)
    sc.anchor("FoodTruckWindow", (cx - 1, y1 + 4.5, 0.2)); sc.anchor("LampLight", (cx - 1, y1 + 2.0, 8.0), range=30)
    TARGETS["food truck window"] = (cx - 1, y1 + 5.0, 0.0)


def picnic_lawn():
    G = "Park"
    K.picnic_table(274, 302, "x", True, True, 5); K.picnic_table(300, 304, "y", True, True, 6); K.picnic_table(288, 282, "x", True, True, 7)
    K.kettle_grill(266, 290, 1.25, "Red", True, True, 8, 4); K.kettle_grill(312, 290, 1.25, "Blue", True, True, 9, 3)
    # giant fork with a sausage
    fx, fy = 302, 270
    C(fx, fy, 0, 0.8, 3.0, "StoneC", G, 10, True, "ForkBase"); C(fx, fy, 0.8, 1.2, 2.4, "Stone", G, 10)
    B(fx - 0.5, fy - 0.35, 1.2, fx + 0.5, fy + 0.35, 11.0, "Steel", G, True, "Fork")
    B(fx - 2.2, fy - 0.35, 11.0, fx + 2.2, fy + 0.35, 12.0, "Steel", G)
    for a in (-2.2, -0.4, 1.4):
        B(fx + a, fy - 0.3, 12.0, fx + a + 0.8, fy + 0.3, 17.5, "Chrome", G)
    hcyl("x", fx - 5.0, fx + 5.0, fy, 15.0, 1.5, "Sausage", G, 10)
    ball(fx - 5.0, fy, 15.0, 1.5, "Sausage", G, seg=10, rings=4); ball(fx + 5.0, fy, 15.0, 1.5, "Sausage", G, seg=10, rings=4)
    for k in range(4):
        B(fx - 3.6 + k * 2.2, fy - 1.56, 14.2, fx - 3.2 + k * 2.2, fy + 1.56, 15.8, "Meat", G)
    K.trash_can(262, 262); K.trash_can(238, 262)
    TARGETS["picnic lawn"] = (288, 292, 0.0)


# ------------------------------------------------------------------ neighbours (closed facades)
def nb_bounds(face, ox, oy, a0, d0, a1, d1):
    p = FP(face, ox, oy, a0, d0); q = FP(face, ox, oy, a1, d1)
    return min(p[0], q[0]), min(p[1], q[1]), max(p[0], q[0]), max(p[1], q[1])


def nb_roof(face, ox, oy, a0, a1, d0, d1, za, zr, mats, along, seed, under, group="NeighborRoofs", solid=None, inset=1.4, rows=7):
    x0, y0, x1, y1 = nb_bounds(face, ox, oy, a0, d0, a1, d1)
    a_axis = "x" if face in ("S", "N") else "y"
    axis = a_axis if along == "a" else ("y" if a_axis == "x" else "x")
    if axis == "x":
        if solid: sc.gable_x(x0 + inset, x1 - inset, y0 + inset, y1 - inset, za, zr - inset * (zr - za) / ((y1 - y0) / 2) - 0.2, solid, group)
        roof_gable(group, "x", x0, x1, y0, y1, za - 0.5, zr, mats, rows=rows, seed=seed, under=under)
    else:
        if solid: sc.gable_y(x0 + inset, x1 - inset, y0 + inset, y1 - inset, za, zr - inset * (zr - za) / ((x1 - x0) / 2) - 0.2, solid, group)
        roof_gable(group, "y", y0, y1, x0, x1, za - 0.5, zr, mats, rows=rows, seed=seed, under=under)


SIDE_R = {"S": "E", "N": "W", "E": "N", "W": "S"}   # world direction of the viewer's right


def neighbour(idx, ox, oy, face, W, D, wallm, roofs, storeys=2, gar=0, yard=28.0, door="Red", along="a", props="grill"):
    """Closed-facade house. (ox, oy) = front-left corner as seen from the street; a = along the front, d = towards the street."""
    G = "Neighbors"
    r = random.Random(100 + idx)
    ZB = 1.2
    ZT = ZB + (22.0 if storeys == 2 else 12.0)
    under = roofs[1]
    def f(a0, d0, z0, a1, d1, z1, m, g=G, col=False, tag=None): FB(face, ox, oy, a0, d0, z0, a1, d1, z1, m, g, col, tag)
    def P(a, d): return FP(face, ox, oy, a, d)
    def fcol(a0, d0, z0, a1, d1, z1, tag):
        x0, y0, x1, y1 = nb_bounds(face, ox, oy, a0, d0, a1, d1); COL(x0, y0, z0, x1, y1, z1, tag, G)
    rightf = SIDE_R[face]; leftf = OPP[rightf]; backf = OPP[face]
    # body
    f(-0.3, -D - 0.3, 0, W + 0.3, 0.3, ZB, "StoneB")
    f(0, -D, ZB, W, 0, ZT, wallm)
    fcol(-0.3, -D - 0.3, 0, W + 0.3, 0.3, ZT + 4, "NeighborHouse")
    for (a, d) in ((0, 0), (W, 0), (0, -D), (W, -D)):
        f(a - 0.4, d - 0.4, ZB, a + 0.4, d + 0.4, ZT + 0.25, "White")
    if storeys == 2:
        f(-0.12, 0.0, ZB + 10.6, W + 0.12, 0.14, ZB + 11.4, "White"); f(-0.12, -D - 0.14, ZB + 10.6, W + 0.12, -D, ZB + 11.4, "White")
        f(-0.14, -D, ZB + 10.6, 0, 0, ZB + 11.4, "White"); f(W, -D, ZB + 10.6, W + 0.14, 0, ZB + 11.4, "White")
    # siding shadow lines on the front
    k = ZB + 1.6
    while k < ZT - 0.5:
        f(0.45, 0.0, k, W - 0.45, 0.05, k + 0.12, "White"); k += 2.2
    # roof
    rise = (D if along == "a" else W) * 0.3
    nb_roof(face, ox, oy, -1.6, W + 1.6, -D - 1.6, 1.6, ZT, ZT + rise + 1.2, roofs, along, idx, under, solid=wallm, inset=1.6)
    x0, y0, x1, y1 = nb_bounds(face, ox, oy, 2, -D + 2, W - 2, -2)
    COL(x0, y0, ZT, x1, y1, ZT + rise * 0.6, "NeighborRoof", "NeighborRoofs")
    # chimney
    ca = W * (0.78 if idx % 2 else 0.2)
    f(ca - 1.6, -D * 0.5 - 1.6, ZT, ca + 1.6, -D * 0.5 + 1.6, ZT + rise + 4.5, "Brick", "NeighborRoofs")
    f(ca - 1.9, -D * 0.5 - 1.9, ZT + rise + 4.5, ca + 1.9, -D * 0.5 + 1.9, ZT + rise + 5.2, "StoneC", "NeighborRoofs")
    # porch (centre or left third)
    pc = W / 2 if idx % 3 else W * 0.3
    pw = 7.0
    f(pc - pw, 0.3, 0, pc + pw, 6.0, 0.9, "StoneB"); f(pc - pw + 0.1, 0.3, 0.9, pc + pw - 0.1, 5.9, ZB, "Plank")
    f(pc - 3.2, 6.0, 0, pc + 3.2, 7.4, 0.6, "StoneC")
    fcol(pc - pw, 0, 0, pc + pw, 6.0, ZB, "NeighborPorch"); fcol(pc - 3.2, 6.0, 0, pc + 3.2, 7.4, 0.6, "NeighborStep")
    for a in (pc - pw + 0.7, pc + pw - 0.7):
        f(a - 0.5, 4.8, ZB, a + 0.5, 5.8, ZB + 9.0, "White", G, True, "PorchPost")
        f(a - 0.7, 4.6, ZB + 9.0, a + 0.7, 6.0, ZB + 9.4, "White")
    f(pc - pw - 0.6, 0.14, ZB + 9.4, pc + pw + 0.6, 6.6, ZB + 10.0, "White", "NeighborRoofs")
    f(pc - pw - 0.9, 0.14, ZB + 10.0, pc + pw + 0.9, 6.9, ZB + 10.5, roofs[0], "NeighborRoofs")
    for (a0, a1) in ((pc - pw + 1.2, pc - 3.6), (pc + 3.6, pc + pw - 1.2)):   # porch rails
        f(a0, 5.15, ZB + 2.7, a1, 5.45, ZB + 3.0, "White"); f(a0, 5.15, ZB + 0.4, a1, 5.45, ZB + 0.65, "White")
        n = int((a1 - a0) / 0.9)
        for i in range(n):
            u = a0 + (i + 0.5) * (a1 - a0) / n; f(u - 0.13, 5.18, ZB + 0.65, u + 0.13, 5.42, ZB + 2.7, "White")
        fcol(a0, 5.1, ZB, a1, 5.5, ZB + 3.0, "PorchRail")
    # door (closed)
    f(pc - 2.3, 0.0, ZB, pc + 2.3, 0.2, ZB + 8.6, "White")
    f(pc - 1.9, 0.14, ZB, pc + 1.9, 0.34, ZB + 8.2, door)
    f(pc - 1.2, 0.3, ZB + 5.0, pc + 1.2, 0.4, ZB + 7.4, "WindowWarm"); f(pc + 1.2, 0.34, ZB + 3.8, pc + 1.5, 0.55, ZB + 4.3, "Gold")
    f(pc - 1.6, 0.4, ZB, pc + 1.6, 3.2, ZB + 0.07, "ClothRed")
    px, py = P(pc - 3.4, 0.0)
    FB(face, px, py, -0.3, 0.0, ZB + 5.6, 0.3, 0.7, ZB + 6.8, "Lamp", G)
    lx, ly = P(pc - 3.4, 0.4); sc.anchor("LampLight", (lx, ly, ZB + 6.2), range=20)
    # windows: front, sides, back
    shut = roofs[0]
    front = [a for a in ((W * 0.16, W * 0.84) if idx % 3 else (W * 0.62, W * 0.86)) if abs(a - pc) > pw + 2.5 or True]
    for a in front:
        if abs(a - pc) < 5.0: continue
        px, py = P(a, 0.0)
        K.swindow(px, py, ZB + 3.4, ZB + 8.4, 5.0, face, G, True, shut, True)
    if storeys == 2:
        for a in (W * 0.16, W * 0.5, W * 0.84):
            px, py = P(a, 0.0)
            K.swindow(px, py, ZB + 14.2, ZB + 19.2, 4.6, face, G, True, shut, False)
    for (sf, sa) in ((leftf, 0.0), (rightf, W)):
        for dd in (-D * 0.28, -D * 0.72):
            px, py = P(sa, dd)
            for lv in range(storeys):
                if gar and ((gar > 0 and sf == rightf) or (gar < 0 and sf == leftf)) and lv == 0: continue
                K.swindow(px, py, ZB + 3.4 + lv * 10.8, ZB + 8.4 + lv * 10.8, 4.4, sf, G, r.random() < 0.7)
    for a in (W * 0.25, W * 0.75):
        px, py = P(a, -D)
        for lv in range(storeys):
            K.swindow(px, py, ZB + 3.4 + lv * 10.8, ZB + 8.4 + lv * 10.8, 4.6, backf, G, r.random() < 0.6)
    # garage wing
    lot_a0, lot_a1 = -8.0, W + 8.0
    if gar:
        g0, g1 = (W, W + 14.0) if gar > 0 else (-14.0, 0.0)
        f(g0, -20.0, 0, g1, -1.0, 0.5, "StoneB"); f(g0, -20.0, 0.5, g1, -1.0, 11.5, wallm)
        fcol(g0, -20.0, 0, g1, -1.0, 14.0, "NeighborGarage")
        nb_roof(face, ox, oy, g0 - (0 if gar > 0 else 1.2), g1 + (1.2 if gar > 0 else 0), -21.2, 0.2, 11.5, 15.8, roofs, "a", idx + 50, under, solid=wallm, inset=1.2, rows=5)
        f(g0 + 1.5, -1.0, 0.5, g1 - 1.5, -0.8, 9.2, "White")
        for k in range(5):
            f(g0 + 1.9, -0.82, 0.9 + k * 1.65, g1 - 1.9, -0.7, 2.3 + k * 1.65, "WallGrey")
        ge = g1 if gar > 0 else g0
        f(ge - 0.3, -1.3, 0.5, ge + 0.3, -0.7, 11.7, "White")
        gx, gy = P((g0 + g1) / 2, -0.7)
        FB(face, gx, gy, -0.4, 0.0, 9.6, 0.4, 0.6, 10.6, "Lamp", G)
        # driveway + car
        f(g0 + 1.0, -1.0, 0, g1 - 1.0, yard, 0.3, "Concrete", "Yard", False)
        fcol(g0 + 1.0, -1.0, 0, g1 - 1.0, yard, 0.3, "Driveway")
        if idx % 2 == 0:
            cxw, cyw = P((g0 + g1) / 2, yard * 0.48)
            K.car(cxw, cyw, face, ["Blue", "Yellow", "White", "Green", "Orange"][idx % 5], "suv" if idx % 4 else "pickup")
        if gar > 0: lot_a1 = g1 + 3.0
        else: lot_a0 = g0 - 3.0
    # front path, picket fence along the sidewalk with gaps, side returns
    f(pc - 2.4, 7.4, 0, pc + 2.4, yard, 0.24, "PaverC", "Yard"); fcol(pc - 2.4, 7.4, 0, pc + 2.4, yard, 0.24, "Path")
    k = 9.0
    while k < yard - 2:
        f(pc - 2.4, k, 0.2, pc + 2.4, k + 0.25, 0.27, "PaverB", "Yard"); k += 3.2
    gaps = [(pc - 3.4, pc + 3.4)]
    if gar: gaps.append(((W + 0.6, W + 13.4) if gar > 0 else (-13.4, -0.6)))
    edges = sorted(gaps)
    cur = lot_a0
    a_axis = "x" if face in ("S", "N") else "y"
    def fence_run(a0, a1):
        if a1 - a0 < 1.5: return
        p = P(a0, yard - 0.8); q = P(a1, yard - 0.8)
        if a_axis == "x": K.picket_fence("x", p[1], min(p[0], q[0]), max(p[0], q[0]))
        else: K.picket_fence("y", p[0], min(p[1], q[1]), max(p[1], q[1]))
    for (g0_, g1_) in edges:
        fence_run(cur, g0_); cur = g1_
    fence_run(cur, lot_a1)
    for a in (lot_a0, lot_a1):
        p = P(a, yard - 0.8); q = P(a, 0.5)
        if a_axis == "x": K.picket_fence("y", p[0], min(p[1], q[1]), max(p[1], q[1]))
        else: K.picket_fence("x", p[1], min(p[0], q[0]), max(p[0], q[0]))
    mx, my = P(pc + 4.6, yard - 2.6)
    K.mailbox(mx, my, face, None, ["White", "Red", "Blue", "Yellow"][idx % 4])
    # bushes along the facade, yard props
    for a in (2.5, 6.5, W - 6.5, W - 2.5):
        if abs(a - pc) < pw + 2.0: continue
        bx, by = P(a, 3.2); K.bush(bx, by, r.uniform(0.8, 1.05), idx * 7 + int(a))
    side = 1 if pc < W / 2 else (-1 if idx % 2 else 1)
    ya = W * 0.5 + side * W * 0.3
    if props == "grill":
        gx, gy = P(ya, yard * 0.6); K.kettle_grill(gx, gy, 1.0, ["Red", "Blue", "Green", "Black"][idx % 4], True, True, idx, 3)
        tx, ty = P(ya - side * 9.0, yard * 0.58); K.picnic_table(tx, ty, a_axis, True, True, idx)
    elif props == "umbrella":
        tx, ty = P(ya, yard * 0.55); K.umbrella_table(tx, ty, ["Red", "Blue", "Yellow", "Green"][idx % 4], "White", 4)
        gx, gy = P(ya - side * 10.5, yard * 0.62); K.kettle_grill(gx, gy, 0.9, "Black", True, True, idx, 2)
    elif props == "pool":
        tx, ty = P(ya, yard * 0.55); K.kiddie_pool(tx, ty, 4.6)
        gx, gy = P(ya - side * 10.0, yard * 0.62); K.kettle_grill(gx, gy, 0.9, "Red", True, False, idx, 3)
    if idx % 2:
        gx, gy = P(pc - 5.0, yard - 5.0); K.gnome(gx, gy, face, 1.0)
    else:
        gx, gy = P(pc - 5.4, yard - 5.5); K.flamingo(gx, gy, SIDE_R[face], False, False)
    fx0, fy0, fx1, fy1 = nb_bounds(face, ox, oy, W * 0.5 - side * W * 0.42, 1.2, W * 0.5 - side * W * 0.2, 2.8)
    # back yard tree
    tx, ty = P(W * (0.3 if idx % 2 else 0.7), -D - 12.0)
    if 14 < tx < 486 and 14 < ty < 486: K.tree(tx, ty, r.uniform(1.0, 1.3), idx)
    x0, y0, x1, y1 = nb_bounds(face, ox, oy, lot_a0 - 1, -D - 3, lot_a1 + 1, yard + 1)
    keep(x0, y0, x1, y1)
    tgx, tgy = P(pc, 3.0)
    TARGETS["neighbour %d porch" % idx] = (tgx, tgy, ZB)


def neighbours():
    grey = ["RoofGrey", "RoofGreyB", "RoofGreyC", "RoofGrey"]; brown = ["RoofBrown", "RoofBrownB", "RoofBrownC", "RoofBrown"]
    red = ["RoofRed", "RoofRedB", "RoofRedC", "RoofRed"]
    # west block (face east)
    neighbour(0, 112, 191, "E", 44, 32, "HouseBlue", grey, 2, -1, 28, "Red", "a", "grill")
    neighbour(1, 112, 265, "E", 44, 32, "HouseYellow", brown, 2, 1, 28, "Blue", "d", "umbrella")
    # east block (face west)
    neighbour(2, 388, 235, "W", 44, 32, "HouseGreen", brown, 2, 1, 28, "Yellow", "a", "pool")
    neighbour(3, 388, 309, "W", 44, 32, "HouseRed", grey, 2, -1, 28, "White", "d", "grill")
    # south corners (face north)
    neighbour(4, 100, 112, "N", 48, 32, "HouseTeal", grey, 2, 1, 28, "Orange", "a", "umbrella")
    neighbour(5, 448, 112, "N", 48, 32, "HouseOrange", brown, 2, -1, 28, "Blue", "a", "grill")
    # north corners (face south)
    neighbour(6, 52, 388, "S", 48, 32, "HousePurple", grey, 2, 1, 28, "Yellow", "d", "pool")
    neighbour(7, 400, 388, "S", 48, 32, "HouseBlue", red, 2, -1, 28, "Red", "a", "umbrella")
    # gate road (face each other)
    neighbour(8, 214, 58, "E", 46, 28, "HouseYellow", red, 1, 0, 18, "Green", "a", "grill")
    neighbour(9, 286, 104, "W", 46, 28, "HousePink", grey, 1, 0, 18, "Blue", "a", "grill")


# ------------------------------------------------------------------ landmarks
def landmarks():
    water_tower(458, 458)
    billboard()


def water_tower(cx, cy):
    G = "Tower"
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        beam((cx + sx * 10, cy + sy * 10, 0), (cx + sx * 6.5, cy + sy * 6.5, 36), 1.2, "Iron", G)
        B(cx + sx * 10 - 1.4, cy + sy * 10 - 1.4, 0, cx + sx * 10 + 1.4, cy + sy * 10 + 1.4, 1.0, "Concrete", G)
        COL(cx + sx * 10 - 1.6, cy + sy * 10 - 1.6, 0, cx + sx * 8.5 + 1.6 * sx, cy + sy * 8.5 + 1.6 * sy, 18, "TowerLeg", G)
    for (z0, z1) in ((2, 13), (13, 24), (24, 35)):
        def pt(sx, sy, z):
            t = z / 36.0
            return (cx + sx * (10 - 3.5 * t), cy + sy * (10 - 3.5 * t), z)
        for (a, b) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
            beam(pt(a[0], a[1], z0), pt(b[0], b[1], z1), 0.45, "Iron", G); beam(pt(b[0], b[1], z0), pt(a[0], a[1], z1), 0.45, "Iron", G)
            beam(pt(a[0], a[1], z1), pt(b[0], b[1], z1), 0.5, "Iron", G)
    C(cx, cy, 36, 37, 11.0, "Iron", G, 12)
    ring(cx, cy, 10.6, 11.0, 40.0, 40.4, "Iron", G, 12)
    for k in range(12):
        a = math.radians(k * 30 + 15)
        B(cx + 10.8 * math.cos(a) - 0.15, cy + 10.8 * math.sin(a) - 0.15, 37, cx + 10.8 * math.cos(a) + 0.15, cy + 10.8 * math.sin(a) + 0.15, 40.0, "Iron", G)
    C(cx, cy, 37, 40, 3.0, "Iron", G, 8)
    # kettle-grill tank
    ball(cx, cy, 51, 13, "Red", G, lat0=-90, lat1=0, seg=16, rings=6, rz=11)
    ring(cx, cy, 12.8, 13.7, 50.6, 51.6, "Chrome", G, 16)
    ball(cx, cy, 51.6, 13, "RedDark", G, lat0=0, lat1=90, seg=16, rings=6, rz=8.5)
    C(cx, cy, 60.0, 60.8, 2.2, "Black", G, 10); B(cx - 0.6, cy - 2.6, 60.8, cx + 0.6, cy - 1.8, 62.6, "Chrome", G); B(cx - 0.6, cy + 1.8, 60.8, cx + 0.6, cy + 2.6, 62.6, "Chrome", G)
    B(cx - 0.8, cy - 2.8, 62.6, cx + 0.8, cy + 2.8, 63.6, "Black", G)
    # badges with the grill icon on all four sides
    for face in ("S", "W", "N", "E"):
        (rx, ry), (nx, ny) = FACE[face]
        px, py = cx + nx * 12.3, cy + ny * 12.3
        FB(face, px, py, -5.6, 0.0, 41.6, 5.6, 0.9, 50.4, "Red", G)
        qx, qy = FP(face, px, py, 0, 0.9)
        icon(K.GRILL_ICON, {"1": "White"}, qx, qy, 46.0, 0.66, face, 0.0, 0.25)
    # ladder
    for k in range(18):
        B(cx - 1.0, cy - 11.6 + k * 0.1, 1.0 + k * 2.0, cx + 1.0, cy - 11.3 + k * 0.1, 1.3 + k * 2.0, "Steel", G)
    beam((cx - 1.0, cy - 11.5, 0), (cx - 1.0, cy - 9.7, 36), 0.25, "Steel", G); beam((cx + 1.0, cy - 11.5, 0), (cx + 1.0, cy - 9.7, 36), 0.25, "Steel", G)
    for (ox_, oy_, s) in ((-4, 2, 2.2), (3, -3, 2.6), (2, 4, 2.0)):
        K.smoke(cx + ox_, cy + oy_, 60.5, 5, s, int(ox_ * 7 + oy_))
    sc.anchor("WaterTower", (cx, cy, 36)); sc.anchor("LampLight", (cx, cy, 30), range=50)
    keep(cx - 14, cy - 14, cx + 14, cy + 14)


def billboard():
    G = "Billboard"
    y = 468.0
    for px in (32.0, 64.0):
        B(px - 1.0, y - 1.0, 0, px + 1.0, y + 1.0, 22.0, "Iron", G, True, "BillboardPost")
        beam((px, y + 1.0, 14), (px, y + 6.0, 0.5), 0.6, "Iron", G)
    B(22.0, y - 1.6, 20.5, 74.0, y + 1.6, 21.3, "Iron", G)
    B(22.0, y - 0.6, 21.3, 74.0, y + 0.6, 43.3, "Magenta", G)
    for (a, b, z0, z1) in ((21.4, 74.6, 21.0, 21.9), (21.4, 74.6, 42.7, 43.6), (21.4, 22.3, 21.9, 42.7), (73.7, 74.6, 21.9, 42.7)):
        B(a, y - 0.8, z0, b, y + 0.8, z1, "Yellow", G)
    COL(21.4, y - 1.6, 20.5, 74.6, y + 1.6, 43.6, "Billboard", G)
    B(24.6, y - 0.72, 23.6, 42.6, y - 0.6, 41.0, "Orange", G)
    icon(K.DAD_FACE, {"h": "Brown", "y": "Yellow", "b": "Black"}, 33.6, y - 0.72, 32.3, 1.3, "S", 0.0, 0.2)
    text("STEAL A", 58.6, y - 0.6, 36.8, 0.64, "S", "White", -0.02, 0.26)
    text("DAD!", 58.6, y - 0.6, 28.2, 1.05, "S", "Yellow", -0.02, 0.3)
    for px in (28, 40, 52, 64, 70):   # spot lights
        beam((px, y - 0.6, 43.4), (px, y - 3.4, 45.0), 0.25, "Iron", G); B(px - 0.8, y - 4.2, 44.6, px + 0.8, y - 3.2, 45.4, "Lamp", G)
    sc.anchor("LampLight", (48, y - 4, 44), range=50)
    keep(20, y - 4, 76, y + 8)


# ------------------------------------------------------------------ perimeter cliffs
def perimeter():
    G = "Cliffs"
    r = random.Random(77)
    mouths = [(140.0, 176.0), (324.0, 360.0)]
    def runs(extra=None):
        ms = sorted(mouths + (extra or []))
        out = []; cur = 0.0
        for (a, b) in ms:
            out.append((cur, a)); cur = b
        out.append((cur, 500.0))
        return out
    def chunk(side, a0, a1, tall):
        """Rock chunk along an edge. side S/N/W/E; a along the edge."""
        hgt = r.uniform(*tall)
        def bx(u0, u1, d0, d1, z0, z1, mat, grp=G):
            if side == "S": B(u0, d0, z0, u1, d1, z1, mat, grp)
            elif side == "N": B(u0, 500 - d1, z0, u1, 500 - d0, z1, mat, grp)
            elif side == "W": B(d0, u0, z0, d1, u1, z1, mat, grp)
            else: B(500 - d1, u0, z0, 500 - d0, u1, z1, mat, grp)
        tiers = 4 if hgt > 28 else (3 if hgt > 15 else 2)
        mats = ["Rock", "RockB", "RockC"]
        zprev = 0.0; d1 = 10.5
        for t in range(tiers):
            d1 = 10.5 - t * (7.0 / tiers) - r.uniform(0.0, 0.8)
            z1 = hgt * (t + 1) / tiers + r.uniform(-1.2, 1.2)
            m = mats[(t + r.randint(0, 2)) % 3]
            bx(a0, a1, r.uniform(0.0, 0.18), d1, zprev, z1, m)
            bx(a0 - 0.12, a1 + 0.12, 0.2 + r.uniform(0.0, 0.5), d1 + 0.35, z1, z1 + 0.9, r.choice(["Grass", "GrassB", "GrassC"]))
            for k in range(r.randint(2, 4)):   # rock blocks sticking out of the face
                w = r.uniform(1.6, 4.0); u = r.uniform(a0, max(a0 + 0.1, a1 - w)); hh = r.uniform(1.2, 3.2)
                zz = r.uniform(zprev + 0.3, max(zprev + 0.4, z1 - hh - 0.3))
                bx(u, min(a1, u + w), d1 - 0.3, d1 + r.uniform(0.5, 1.5), zz, zz + hh, r.choice([q for q in mats if q != m]))
            if t < tiers - 1 and r.random() < 0.5:   # bush on the ledge
                u = r.uniform(a0 + 1, a1 - 1); dd = d1 - 1.4
                bx(u - 1.1, u + 1.1, dd - 1.1, dd + 1.1, z1 + 0.9, z1 + 2.9, r.choice(["Hedge", "HedgeB", "LeafB"]))
            zprev = z1 + 0.9
        if r.random() < 0.85:
            ua = r.uniform(a0 + 2, a1 - 2); ud = r.uniform(2.2, max(2.3, d1 - 2.2))
            if side == "S": px, py = ua, ud
            elif side == "N": px, py = ua, 500 - ud
            elif side == "W": px, py = ud, ua
            else: px, py = 500 - ud, ua
            K.pine(px, py, r.uniform(0.7, 1.0), False, int(ua), zprev, "Cliffs")
    for side in ("S", "N", "W", "E"):
        for (ra, rb) in runs([(226.0, 274.0)] if side == "S" else None):
            if rb - ra < 4: continue
            tall = (30.0, 44.0) if (side == "N" and ra > 170 and rb < 330) else ((16.0, 30.0) if side == "N" else (10.0, 20.0))
            a = ra
            while a < rb - 0.5:
                w = min(r.uniform(7, 13), rb - a)
                if rb - (a + w) < 5: w = rb - a
                chunk(side, a, a + w, tall); a += w
            if side == "S": COL(ra, 0, 0, rb, 10.5, 60, "Cliff", G)
            elif side == "N": COL(ra, 489.5, 0, rb, 500, 60, "Cliff", G)
            elif side == "W": COL(0, ra, 0, 10.5, rb, 60, "Cliff", G)
            else: COL(489.5, ra, 0, 500, rb, 60, "Cliff", G)
    # road mouths: striped barriers + invisible bound walls + connector anchors
    def barrier(axis, a0, a1, c, name):
        n = int((a1 - a0) / 2.0)
        for i in range(n):
            u0 = a0 + i * (a1 - a0) / n; u1 = a0 + (i + 1) * (a1 - a0) / n
            m = "Red" if i % 2 else "White"
            if axis == "x": B(u0, c - 0.3, 2.2, u1, c + 0.3, 3.6, m, "Props")
            else: B(c - 0.3, u0, 2.2, c + 0.3, u1, 3.6, m, "Props")
        for u in (a0 + 1.5, (a0 + a1) / 2, a1 - 1.5):
            if axis == "x": B(u - 0.3, c - 1.2, 0.2, u + 0.3, c + 1.2, 3.6, "Iron", "Props"); B(u - 0.4, c - 0.4, 3.6, u + 0.4, c + 0.4, 4.4, "FireY", "Props")
            else: B(c - 1.2, u - 0.3, 0.2, c + 1.2, u + 0.3, 3.6, "Iron", "Props"); B(c - 0.4, u - 0.4, 3.6, c + 0.4, u + 0.4, 4.4, "FireY", "Props")
        if axis == "x": COL(a0 - 6, c - 0.5, 0, a1 + 6, c + 0.5, 60, "Bounds", "Bounds"); sc.anchor(name, ((a0 + a1) / 2, c, 0.2), note="road connector (closed by a barrier for now)")
        else: COL(c - 0.5, a0 - 6, 0, c + 0.5, a1 + 6, 60, "Bounds", "Bounds"); sc.anchor(name, (c, (a0 + a1) / 2, 0.2), note="road connector (closed by a barrier for now)")
    for i, x0 in enumerate(ROADS_V):
        barrier("x", x0, x0 + RW, 3.0, "ConnectorS%d" % (i + 1)); barrier("x", x0, x0 + RW, 497.0, "ConnectorN%d" % (i + 1))
    for i, y0 in enumerate(ROADS_H):
        barrier("y", y0, y0 + RW, 3.0, "ConnectorW%d" % (i + 1)); barrier("y", y0, y0 + RW, 497.0, "ConnectorE%d" % (i + 1))
    COL(226, -1.0, 0, 274, 0.0, 60, "Bounds", "Bounds")
    # waterfall behind Grill Dad's house + carved dad face
    B(236.0, 487.6, 0, 264.0, 489.2, 46.0, "RockB", G)
    for k in range(7):
        x0 = 238.0 + k * 3.45
        B(x0, 486.9 - (k % 2) * 0.25, 0.5, x0 + 3.3, 487.7, 45.0 + (k % 3) * 0.5, "Water" if k % 2 else "WaterB", "Water")
    B(237.0, 486.0, 44.5, 263.0, 489.0, 46.4, "WaterB", "Water")
    for k in range(9):
        B(237.0 + k * 3.0 + r.uniform(0, 1), 485.2, 0.4, 239.2 + k * 3.0, 487.0, 1.6 + r.uniform(0, 1.6), "Foam", "Water")
    B(232.0, 476.6, 0, 268.0, 487.6, 0.5, "Water", "Water"); COL(232, 476.6, 0, 268, 489.5, 1.0, "WaterfallPool", G)
    for (a, b) in ((230.0, 232.0), (268.0, 270.0)):
        B(a, 475.4, 0, b, 489.0, 1.4, "StoneC", G)
    B(232.0, 475.4, 0, 268.0, 476.6, 1.5, "Stone", G)
    B(193.0, 487.9, 13.0, 221.0, 489.4, 40.0, "Rock", G)
    icon(K.DAD_FACE, {"h": "RockB", "y": "RockC", "b": "Black"}, 207.0, 487.9, 26.5, 1.9, "S", -0.1, 0.5, "Cliffs")
    sc.anchor("Waterfall", (250, 484, 2))


# ------------------------------------------------------------------ street props + vegetation
def street():
    # banner lamps on the gate road and around the park block
    for y in (34, 74, 114):
        K.lamp_post(235.0, y, "S"); K.lamp_post(265.0, y, "N")
    for a in (196, 304):
        K.lamp_post(a, 173.2, "S"); K.lamp_post(a, 326.8, "N"); K.lamp_post(173.2, a, "E"); K.lamp_post(326.8, a, "W")
    for a in (40, 100, 400, 460):
        K.lamp_post(a, 143.0, None, 12.0); K.lamp_post(a, 357.0, None, 12.0); K.lamp_post(143.0, a, None, 12.0); K.lamp_post(357.0, a, None, 12.0)
    K.hydrant(173.0, 142.5); K.hydrant(327.0, 357.5); K.hydrant(143.0, 327.5); K.hydrant(357.5, 173.0)
    K.trash_can(232.6, 142.6); K.trash_can(267.4, 142.6); K.trash_can(173.0, 357.6); K.trash_can(326.8, 142.6)
    # cars on the roads
    K.car(300.0, 151.5, "E", "Blue", "suv"); K.car(349.0, 292.0, "N", "Yellow", "suv"); K.car(60.0, 348.5, "W", "White", "pickup")
    K.car(151.0, 60.0, "S", "Green", "suv"); K.car(420.0, 164.0, "W", "Orange", "suv")
    # stop signs at the gate junction
    for (sx, sy) in ((235.0, 142.0),):
        C(sx, sy, 0.45, 8.0, 0.2, "Steel", "Props", 6, True, "Sign")
        for face, yy in (("S", sy - 0.15), ("N", sy + 0.15)):
            B(sx - 1.5, sy - 0.15, 8.0, sx + 1.5, sy + 0.15, 11.0, "Red", "Props")
            text("STOP", sx, yy, 9.5, 0.11, face, "White", 0.0, 0.08)


def scatter():
    r = random.Random(5)
    placed = []
    def ok(x, y, m):
        if x < 14 or x > 486 or y < 14 or y > 486: return False
        if on_road(x, y, m - 4): return False
        if 168 < x < 332 and 168 < y < 332: return False
        for (x0, y0, x1, y1) in KEEP:
            if x0 - m < x < x1 + m and y0 - m < y < y1 + m: return False
        for (px, py) in placed:
            if (px - x) ** 2 + (py - y) ** 2 < 16 ** 2: return False
        return True
    n = 0; tries = 0
    while n < 60 and tries < 6000:
        tries += 1
        x, y = r.uniform(14, 486), r.uniform(14, 486)
        if not ok(x, y, 7): continue
        placed.append((x, y)); n += 1
        if r.random() < 0.35: K.pine(x, y, r.uniform(1.0, 1.4), True, n)
        else: K.tree(x, y, r.uniform(1.0, 1.45), n)
    placed2 = []
    n = 0; tries = 0
    while n < 70 and tries < 6000:
        tries += 1
        x, y = r.uniform(14, 486), r.uniform(14, 486)
        if not ok(x, y, 4): continue
        if any((px - x) ** 2 + (py - y) ** 2 < 49 for (px, py) in placed2): continue
        placed2.append((x, y)); n += 1
        if r.random() < 0.25: K.flowerbed(x - 2.5, y - 1.5, x + 2.5, y + 1.5, n)
        else: K.bush(x, y, r.uniform(0.8, 1.3), n)
