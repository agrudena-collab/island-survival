"""Grill Mistress District: the central block. Turquoise apartment tower of Grill Dad's mistress (closed facade,
the flat itself is a separate hidden model), roof grill terrace, teleport pad at the front door, plaza, bus stop, BBQ kiosk.
Plan coords: x east, y north, z up, 1 unit = 1 stud. The block is x 170..330, y 170..330 (plaza 176..324)."""
import math, random
import gd_kit as K
from gd_kit import B, C, COL, FB, FP, text, icon, ball, ring, hcyl, beam

sc = None
TARGETS = {}
KEEPS = []

# tower body
TX0, TX1, TY0, TY1 = 224.0, 276.0, 258.0, 296.0
ZL = 1.0            # lobby floor (top of the marble plinth)
ZB = 11.0           # top of the lobby, first residential floor
FH = 6.0            # storey height
NF = 7              # residential storeys
ZT = ZB + FH * NF   # 53: top of the walls
ZR = ZT + 1.5       # roof deck top
PAD = (250.0, 244.0)   # teleport pad centre
BAY = 6.5


def build(scene):
    global sc
    sc = scene
    plaza()
    tower()
    roof_terrace()
    teleport_pad()
    bus_stop(196.0, 179.0)
    bbq_kiosk(304.0, 236.0)
    garden()


# ------------------------------------------------------------------ plaza paving
def plaza():
    G = "Plaza"
    # main walk from the south road to the tower steps, 10 wide
    COL(176, 176, 0, 324, 324, 0.3, "Plaza", G)
    for (x0, y0, x1, y1) in ((176, 176, 324, 324),):
        n = 37
        st = (x1 - x0) / n
        for i in range(n):
            for j in range(n):
                xa, ya = x0 + i * st, y0 + j * st
                if TX0 - 0.5 < xa + st and xa < TX1 + 0.5 and TY0 - 8.5 < ya + st and ya < TY1 + 0.5:
                    continue   # under the tower and its steps
                m = ("Paver", "PaverC", "Marble")[(i * 3 + j * 5) % 3] if 244 <= xa + st / 2 <= 256 else ("PaverC" if (i + j) % 2 else "MarbleB")
                B(xa + 0.03, ya + 0.03, 0, xa + st - 0.03, ya + st - 0.03, 0.3, m, G)
    # turquoise borders of the main walk
    for xx in (243.4, 256.0):
        B(xx, 177.0, 0.3, xx + 0.6, 236.0, 0.38, "TurqB", G)
    KEEPS.append((176, 176, 324, 324))
    TARGETS["plaza south"] = (250, 182, 0.3)


# ------------------------------------------------------------------ the tower
def tower():
    G, R = "MTower", "MTowerRoof"
    W = TX1 - TX0
    # marble plinth + two steps in front
    B(TX0 - 1.2, TY0 - 1.2, 0.3, TX1 + 1.2, TY1 + 1.2, ZL, "MarbleB", G)
    B(236.0, TY0 - 4.4, 0.3, 264.0, TY0 - 1.2, 0.65, "Marble", G)
    B(236.0, TY0 - 2.8, 0.65, 264.0, TY0 - 1.2, ZL - 0.02, "Marble", G)
    COL(236.0, TY0 - 4.4, 0.3, 264.0, TY0 - 1.2, 0.65, "TowerStep", G)
    COL(236.0, TY0 - 2.8, 0.3, 264.0, TY0 - 1.2, ZL, "TowerStep", G)
    COL(TX0 - 1.2, TY0 - 1.2, 0.3, TX1 + 1.2, TY1 + 1.2, ZL, "TowerPlinth", G)
    # one solid collider for the whole closed building (the flat is a separate model)
    COL(TX0, TY0, ZL, TX1, TY1, ZR + 3.0, "MistressTower", G)
    # lobby (darker turquoise, slightly outset) and residential body
    B(TX0 - 0.2, TY0 - 0.2, ZL, TX1 + 0.2, TY1 + 0.2, ZB, "TurqB", G)
    B(TX0, TY0, ZB, TX1, TY1, ZT, "Turq", G)
    # corner columns
    for (cx, cy) in ((TX0, TY0), (TX1, TY0), (TX0, TY1), (TX1, TY1)):
        B(cx - 0.9, cy - 0.9, ZL, cx + 0.9, cy + 0.9, ZT + 0.6, "TurqDark", G)
    # floor bands
    for k in range(NF + 1):
        z = ZB + k * FH
        B(TX0 - 0.45, TY0 - 0.45, z - 0.25, TX1 + 0.45, TY1 + 0.45, z + 0.25, "White", G)
    # cornice
    B(TX0 - 1.4, TY0 - 1.4, ZT, TX1 + 1.4, TY1 + 1.4, ZT + 0.9, "White", R)
    B(TX0 - 1.0, TY0 - 1.0, ZT + 0.9, TX1 + 1.0, TY1 + 1.0, ZR, "TurqC", R)
    # facades: pilasters + windows on all four sides
    faces = (("S", TY0, "x"), ("N", TY1, "x"), ("W", TX0, "y"), ("E", TX1, "y"))
    for face, c, ax in faces:
        a0, a1 = (TX0, TX1) if ax == "x" else (TY0, TY1)
        nb = int(round((a1 - a0) / BAY)); bw = (a1 - a0) / nb
        for i in range(1, nb):
            u = a0 + i * bw
            if ax == "x":
                yy0, yy1 = (c - 0.35, c + 0.01) if face == "S" else (c - 0.01, c + 0.35)
                B(u - 0.4, yy0, ZB + 0.25, u + 0.4, yy1, ZT - 0.01, "TurqC", G)
            else:
                xx0, xx1 = (c - 0.35, c + 0.01) if face == "W" else (c - 0.01, c + 0.35)
                B(xx0, u - 0.4, ZB + 0.25, xx1, u + 0.4, ZT - 0.01, "TurqC", G)
        for k in range(NF):
            z = ZB + k * FH
            for i in range(nb):
                u = a0 + (i + 0.5) * bw
                px, py = (u, c) if ax == "x" else (c, u)
                shutters = "Coral" if (k + i) % 3 == 0 else None
                K.swindow(px, py, z + 1.4, z + 4.7, 3.4, face, G, lit=(k * 7 + i * 3) % 5 != 0, shutters=None, box=(face == "S" and k % 2 == 0 and i % 2 == 1))
                if shutters and face != "S":
                    FB(face, px, py, -3.0, -0.05, z + 1.3, -2.1, 0.16, z + 4.8, "Coral", G)
                    FB(face, px, py, 2.1, -0.05, z + 1.3, 3.0, 0.16, z + 4.8, "Coral", G)
    # front balconies on storeys 2, 4, 6 (two middle bays each)
    for k in (1, 3, 5):
        z = ZB + k * FH
        x0, x1 = 237.0, 263.0
        B(x0, TY0 - 3.2, z - 0.35, x1, TY0 + 0.3, z + 0.05, "White", G)
        B(x0 + 0.1, TY0 - 3.1, z + 0.05, x1 - 0.1, TY0 - 0.46, z + 0.15, "PlankC", G)
        for (a, b) in ((x0, x0 + 0.25), (x1 - 0.25, x1)):
            B(a, TY0 - 3.2, z + 0.15, b, TY0 - 0.46, z + 3.3, "White", G)
        B(x0, TY0 - 3.2, z + 3.1, x1, TY0 - 2.9, z + 3.4, "White", G)
        u = x0 + 0.9
        while u < x1 - 0.6:
            B(u - 0.08, TY0 - 3.12, z + 0.15, u + 0.08, TY0 - 2.98, z + 3.1, "White", G); u += 0.8
        B(x0 + 0.25, TY0 - 3.07, z + 0.15, x1 - 0.25, TY0 - 3.03, z + 2.9, "Glass", "Glass")
        # flower pots and a little grill on the balcony
        K.sc.dz = z + 0.15
        for xx in (x0 + 1.6, x1 - 1.6):
            C(xx, TY0 - 1.6, 0.0, 1.0, 0.6, "Coral", G, 8); ball(xx, TY0 - 1.6, 1.6, 0.8, "LeafB", G, seg=8, rings=4)
        K.kettle_grill(250.0, TY0 - 1.8, 0.55, "Pink", False, True, k, 0, G)
        K.sc.dz = 0.0
        COL(x0, TY0 - 3.2, z - 0.35, x1, TY0, z + 3.4, "Balcony", G)
    # lobby front: glass-look storefront (closed), double door, awning, APARTMENTS sign
    for (a, b) in ((TX0 + 2.0, 244.6), (255.4, TX1 - 2.0)):
        n = int((b - a) / 4.0)
        for i in range(n):
            u0 = a + i * (b - a) / n; u1 = a + (i + 1) * (b - a) / n
            B(u0 + 0.25, TY0 - 0.32, ZL + 1.0, u1 - 0.25, TY0 - 0.2, ZL + 7.6, "WindowWarm", G)
            B(u0, TY0 - 0.5, ZL + 0.5, u0 + 0.25, TY0 - 0.2, ZL + 8.0, "White", G)
            B(u1 - 0.25, TY0 - 0.5, ZL + 0.5, u1, TY0 - 0.2, ZL + 8.0, "White", G)
        B(a, TY0 - 0.5, ZL + 0.5, b, TY0 - 0.21, ZL + 1.0, "White", G)
        B(a, TY0 - 0.5, ZL + 7.6, b, TY0 - 0.21, ZL + 8.0, "White", G)
        for u in ((a + 3, b - 6) if b < 250 else (a + 6, b - 3)):
            C(u, TY0 - 2.6, ZL, ZL + 1.2, 1.1, "Coral", G, 10); ball(u, TY0 - 2.6, ZL + 2.6, 1.5, "Hedge", G, seg=8, rings=4)
            COL(u - 1.2, TY0 - 3.8, ZL, u + 1.2, TY0 - 1.4, ZL + 3.8, "Planter", G)
    # door (decorative, the entrance is the teleport pad)
    B(244.6, TY0 - 0.6, ZL, 255.4, TY0 - 0.2, ZL + 8.6, "White", G)
    B(245.2, TY0 - 0.75, ZL, 249.9, TY0 - 0.55, ZL + 8.0, "TurqDark", G)
    B(250.1, TY0 - 0.75, ZL, 254.8, TY0 - 0.55, ZL + 8.0, "TurqDark", G)
    for (a, b) in ((245.7, 249.4), (250.6, 254.3)):
        B(a, TY0 - 0.85, ZL + 2.0, b, TY0 - 0.74, ZL + 7.4, "WindowWarm", G)
    for xx in (249.3, 250.7):
        B(xx - 0.12, TY0 - 1.1, ZL + 3.4, xx + 0.12, TY0 - 0.74, ZL + 4.8, "Gold", G)
    # striped awning
    for i in range(10):
        a0 = 240.0 + i * 2.0
        sc.plate((a0, TY0 - 0.25, ZL + 9.6), (a0 + 2.0, TY0 - 0.25, ZL + 9.6), (a0 + 2.0, TY0 - 4.0, ZL + 8.4), (a0, TY0 - 4.0, ZL + 8.4), 0.2, "Coral" if i % 2 else "White", G)
    B(240.0, TY0 - 4.1, ZL + 7.7, 260.0, TY0 - 3.9, ZL + 8.5, "Coral", G)
    COL(240.0, TY0 - 4.2, ZL + 7.7, 260.0, TY0 - 0.2, ZL + 9.9, "Awning", G)
    # APARTMENTS sign above the awning (lobby top band)
    B(236.0, TY0 - 0.7, ZL + 9.6, 264.0, TY0 - 0.2, ZB - 0.3, "Navy", "Signs")
    text("APARTMENTS", 250.0, TY0 - 0.7, (ZL + 9.6 + ZB - 0.3) / 2 - 0.05, 0.14, "S", "NeonTurq", -0.02, 0.12)
    sc.anchor("LampLight", (250.0, TY0 - 5.0, ZL + 7.0), range=26)
    # roof sign facing the gate, big
    B(234.0, TY0 + 1.0, ZR, 266.0, TY0 + 2.0, ZR + 9.0, "Navy", R)
    for (a, b, z0, z1) in ((233.6, 266.4, ZR + 9.0, ZR + 9.5), (233.6, 266.4, ZR - 0.01, ZR + 0.5)):
        B(a, TY0 + 0.9, z0, b, TY0 + 2.1, z1, "NeonPink", R)
    text("APARTMENTS", 250.0, TY0 + 0.9, ZR + 4.75, 0.42, "S", "NeonTurq", -0.02, 0.2, R)
    for xx in (236.0, 264.0):
        beam((xx, TY0 + 2.0, ZR), (xx, TY0 + 6.0, ZR), 0.4, "Iron", R)
    TARGETS["tower steps"] = (250.0, TY0 - 3.6, 0.65)
    KEEPS.append((TX0 - 6, TY0 - 8, TX1 + 6, TY1 + 6))


# ------------------------------------------------------------------ roof grill terrace (decor, seen from the street)
def roof_terrace():
    G = "MTowerRoof"
    sc.group_override = G   # every prop on the roof (string lights, tables, smoke) belongs to the tower roof group
    z = ZR
    B(TX0 - 1.0, TY0 - 1.0, z, TX1 + 1.0, TY0 - 0.2, z + 3.0, "TurqC", G)
    B(TX0 - 1.0, TY1 + 0.2, z, TX1 + 1.0, TY1 + 1.0, z + 3.0, "TurqC", G)
    B(TX0 - 1.0, TY0 - 0.2, z, TX0 - 0.2, TY1 + 0.2, z + 3.0, "TurqC", G)
    B(TX1 + 0.2, TY0 - 0.2, z, TX1 + 1.0, TY1 + 0.2, z + 3.0, "TurqC", G)
    for (a, b, c_, d) in ((TX0 - 1.2, TY0 - 1.2, TX1 + 1.2, TY0), (TX0 - 1.2, TY1, TX1 + 1.2, TY1 + 1.2),
                          (TX0 - 1.2, TY0, TX0, TY1), (TX1, TY0, TX1 + 1.2, TY1)):
        B(a, b, z + 3.0, c_, d, z + 3.3, "White", G)
    # deck planks
    n = int((TY1 - TY0) / 1.2)
    for k in range(n):
        y0 = TY0 + 0.2 + k * (TY1 - TY0 - 0.4) / n
        y1 = TY0 + 0.2 + (k + 1) * (TY1 - TY0 - 0.4) / n
        B(TX0 + 0.25, y0 + 0.03, z, TX1 - 0.25, y1 - 0.03, z + 0.22, ("Plank", "PlankB", "PlankC")[k % 3], G)
    # pergola over the grill corner
    px0, px1, py0, py1 = 228.0, 252.0, 278.0, 292.0
    for (x, y) in ((px0, py0), (px1, py0), (px0, py1), (px1, py1), ((px0 + px1) / 2, py0), ((px0 + px1) / 2, py1)):
        B(x - 0.4, y - 0.4, z + 0.22, x + 0.4, y + 0.4, z + 9.0, "White", G)
    for y in (py0, py1):
        B(px0 - 0.8, y - 0.3, z + 9.0, px1 + 0.8, y + 0.3, z + 9.6, "White", G)
    u = px0
    while u <= px1 + 0.01:
        B(u - 0.18, py0 - 0.9, z + 9.6, u + 0.18, py1 + 0.9, z + 10.0, "WoodLight", G); u += 2.0
    # golden grill (her gift from Grill Dad) + props, placed on the deck
    sc.dz = z + 0.22
    K.picnic_table(240.0, 285.0, "x", True, True, 71)   # big golden grill removed on request
    K.umbrella_table(262.0, 270.0, "Coral", "White", 4, 3)
    K.umbrella_table(264.0, 286.0, "Teal", "White", 4, 4)
    for (x, y) in ((232.0, 266.0), (238.0, 266.0)):
        lounger(x, y)
    K.flamingo(270.5, 262.5, "W", True, True)
    for (x, y) in ((TX0 + 2.0, TY0 + 2.0), (TX1 - 2.0, TY0 + 2.0), (TX0 + 2.0, TY1 - 2.0), (TX1 - 2.0, TY1 - 2.0)):
        C(x, y, 0, 1.4, 1.0, "Coral", G, 10); K.bush(x, y + 0.01, 0.7, int(x + y), False, G)
    K.kiddie_pool(252.0, 264.5, 3.6, True)
    sc.anchor("LampLight", (250.0, 277.0, 6.0), range=40)
    sc.dz = 0.0
    sc.group_override = None


def lounger(x, y):
    G = "MTowerRoof"
    B(x - 1.0, y - 3.0, 0.0, x + 1.0, y + 3.0, 0.9, "White", G)
    B(x - 0.9, y - 2.9, 0.9, x + 0.9, y + 1.4, 1.2, "Coral", G)
    sc.plate((x - 0.9, y + 1.4, 1.2), (x + 0.9, y + 1.4, 1.2), (x + 0.9, y + 3.0, 2.8), (x - 0.9, y + 3.0, 2.8), 0.3, "Coral", G)


def golden_grill(cx, cy, s):
    G = "MTowerRoof"
    for k in range(3):
        a = math.radians(90 + 120 * k)
        beam((cx + 4.6 * s * math.cos(a), cy + 4.6 * s * math.sin(a), 0.0), (cx + 3.0 * s * math.cos(a), cy + 3.0 * s * math.sin(a), 4.8 * s), 0.7 * s, "GoldB", G)
    ball(cx, cy, 8.4 * s, 7.2 * s, "Gold", G, lat0=-90, lat1=0, seg=16, rings=6, rz=5.6 * s)
    ring(cx, cy, 7.0 * s, 7.7 * s, 8.1 * s, 8.7 * s, "GoldB", G, 16)
    C(cx, cy, 8.4 * s, 9.1 * s, 6.5 * s, "Fire", G, 16)
    for k in range(5):
        u = cx - 4.0 * s + k * 2.0 * s
        hcyl("y", cy - 2.0 * s, cy + 2.0 * s, u, 9.4 * s, 0.45 * s, "Sausage", G, 8)
    # open lid leaning back
    K.open_lid(cx, cy, 8.7 * s, 7.2 * s, s, "GoldC", G)
    K.smoke(cx, cy, 11.5 * s, 4, 0.8, 21, "Smoke")
    COL(cx - 5.5 * s, cy - 5.5 * s, 0, cx + 5.5 * s, cy + 5.5 * s, 9.2 * s, "GoldenGrill", G)


# ------------------------------------------------------------------ teleport pad in front of the tower
def teleport_pad():
    G = "Teleport"
    cx, cy = PAD
    C(cx, cy, 0.3, 0.5, 4.6, "Chrome", G, 20)
    ring(cx, cy, 3.4, 4.0, 0.5, 0.6, "NeonTurq", G, 20)
    C(cx, cy, 0.5, 0.55, 3.4, "TurqDark", G, 20)
    ring(cx, cy, 1.2, 1.6, 0.55, 0.62, "NeonPink", G, 16)
    COL(cx - 4.6, cy - 4.6, 0.3, cx + 4.6, cy + 4.6, 0.55, "TeleportPad", G)
    # arch over the pad with a sign
    for xx in (cx - 5.6, cx + 5.6):
        B(xx - 0.6, cy - 0.6, 0.3, xx + 0.6, cy + 0.6, 1.0, "TurqDark", G)
        B(xx - 0.35, cy - 0.35, 1.0, xx + 0.35, cy + 0.35, 10.0, "Chrome", G)
        B(xx - 0.12, cy - 0.5, 1.4, xx + 0.12, cy - 0.34, 9.6, "NeonTurq", G)
        COL(xx - 0.6, cy - 0.6, 0.3, xx + 0.6, cy + 0.6, 10.0, "TeleportPost", G)
    B(cx - 6.2, cy - 0.5, 10.0, cx + 6.2, cy + 0.5, 12.6, "Navy", G)
    B(cx - 6.4, cy - 0.6, 12.6, cx + 6.4, cy + 0.6, 12.9, "NeonPink", G)
    B(cx - 6.4, cy - 0.6, 9.7, cx + 6.4, cy + 0.6, 10.0, "NeonPink", G)
    for face, yy in (("S", cy - 0.5), ("N", cy + 0.5)):
        text("TELEPORT", cx, yy, 11.3, 0.17, face, "NeonTurq", -0.02, 0.12)
    COL(cx - 6.4, cy - 0.6, 9.7, cx + 6.4, cy + 0.6, 12.9, "TeleportSign", G)
    sc.anchor("ApartmentEntrance", (cx, cy, 0.55), note="teleport pad: Exterior.Entrance (tag ApartmentEntrance, prompt «Войти»)")
    sc.anchor("ExitArrival", (cx, cy - 8.0, 0.3), note="where the flat's exit door brings the player (facing south)")
    sc.anchor("LampLight", (cx, cy, 8.0), range=22)
    TARGETS["teleport pad"] = (cx, cy, 0.55)
    TARGETS["exit arrival"] = (cx, cy - 8.0, 0.3)


# ------------------------------------------------------------------ bus stop (sign BUS)
def bus_stop(cx, cy):
    G = "BusStop"
    x0, x1, y0, y1 = cx - 6, cx + 6, cy, cy + 3.4
    B(x0, y0, 0.3, x1, y1, 0.5, "Concrete", G)
    for xx in (x0 + 0.3, x1 - 0.3):
        B(xx - 0.2, y1 - 0.5, 0.5, xx + 0.2, y1 - 0.1, 8.0, "Steel", G)
        COL(xx - 0.3, y1 - 0.6, 0.3, xx + 0.3, y1, 8.0, "BusStop", G)
    B(x0 + 0.5, y1 - 0.32, 1.0, x1 - 0.5, y1 - 0.26, 7.4, "Glass", "Glass")
    COL(x0, y1 - 0.4, 0.3, x1, y1 - 0.2, 8.0, "BusStop", G)
    sc.plate((x0 - 0.4, y1 + 0.2, 8.0), (x1 + 0.4, y1 + 0.2, 8.0), (x1 + 0.4, y0 - 0.6, 7.6), (x0 - 0.4, y0 - 0.6, 7.6), 0.3, "TurqDark", G)
    B(x0 + 1.0, y1 - 1.2, 1.9, x1 - 1.0, y1 - 0.5, 2.2, "WoodLight", G)
    for xx in (x0 + 1.5, x1 - 1.5):
        B(xx - 0.15, y1 - 1.1, 0.5, xx + 0.15, y1 - 0.6, 1.9, "Iron", G)
    COL(x0 + 1.0, y1 - 1.2, 0.3, x1 - 1.0, y1 - 0.5, 2.2, "BusBench", G)
    # pole with BUS sign
    C(x1 + 2.0, y0 + 0.4, 0.3, 9.5, 0.18, "Steel", G, 6, True, "Sign")
    B(x1 + 0.6, y0 + 0.25, 8.0, x1 + 3.4, y0 + 0.55, 10.4, "Blue", "Signs")
    for face, yy in (("S", y0 + 0.25), ("N", y0 + 0.55)):
        text("BUS", x1 + 2.0, yy, 9.2, 0.13, face, "White", 0.0, 0.08)
    sc.anchor("BusStop", (cx, y0 - 1.5, 0.3))
    KEEPS.append((x0 - 2, y0 - 2, x1 + 4, y1 + 2))
    TARGETS["bus stop"] = (cx, y0 - 1.6, 0.3)


# ------------------------------------------------------------------ BBQ kiosk on the plaza
def bbq_kiosk(cx, cy):
    G = "Kiosk"
    x0, x1, y0, y1 = cx - 7, cx + 7, cy - 4, cy + 4
    B(x0, y0, 0.34, x1, y1, 8.0, "Coral", G, True, "Kiosk")
    B(x0 - 0.05, y0 - 0.05, 0.3, x1 + 0.05, y1 + 0.05, 1.6, "White", G)
    B(x0 - 0.8, y0 - 0.8, 8.0, x1 + 0.8, y1 + 0.8, 8.6, "White", G)
    for i in range(7):
        a0 = x0 + i * 2.0
        sc.plate((a0, y0, 7.4), (a0 + 2.0, y0, 7.4), (a0 + 2.0, y0 - 2.8, 6.4), (a0, y0 - 2.8, 6.4), 0.18, "Turq" if i % 2 else "White", G)
    B(x0 + 1.2, y0 - 0.05, 3.6, x1 - 1.2, y0 + 0.02, 6.6, "Navy", G)
    B(x0 + 1.0, y0 - 1.4, 3.3, x1 - 1.0, y0, 3.6, "Steel", G)
    K.burger(cx - 3, y0 - 0.7, 3.6, 0.8); K.burger(cx - 1, y0 - 0.7, 3.6, 0.8); K.cup(cx + 1.5, y0 - 0.6, 3.6, "Coral"); K.cup(cx + 3, y0 - 0.6, 3.6, "Teal")
    B(cx - 6.0, cy - 0.5, 8.6, cx + 6.0, cy + 0.5, 11.6, "Navy", G)
    for face, yy in (("S", cy - 0.5), ("N", cy + 0.5)):
        text("BBQ", cx, yy, 10.1, 0.3, face, "NeonPink", -0.02, 0.18)
    C(x1 - 2.0, cy + 1.5, 8.6, 10.6, 0.5, "Steel", G, 8); K.smoke(x1 - 2.0, cy + 1.5, 11.0, 4, 0.9, 31)
    sc.dz = 0.3
    K.umbrella_table(cx - 8, cy - 14, "Coral", "White", 4, 5); K.umbrella_table(cx + 6, cy - 14, "Teal", "White", 4, 6)
    K.kettle_grill(cx + 13.5, cy - 4, 1.1, "Pink", True, True, 33, 3)
    K.trash_can(cx - 11, cy - 3)
    sc.dz = 0.0
    sc.anchor("LampLight", (cx, y0 - 2.5, 6.0), range=24)
    TARGETS["bbq kiosk"] = (cx, y0 - 8.0, 0.3)


# ------------------------------------------------------------------ garden around the tower
def garden():
    # fountain pond west of the walk (explicit plaza height)
    pond_lite(204.0, 222.0)
    sc.dz = 0.3   # everything below stands on the plaza pavers
    # flowerbeds and benches along the main walk
    for y in (196.0, 214.0):
        for (x0, x1) in ((236.0, 242.6), (257.4, 264.0)):
            K.flowerbed(x0, y, x1, y + 6.0, int(x0 + y), 0.0, "TurqC")
    for (bx, by, f) in ((239.0, 228.0, "E"), (261.0, 228.0, "W"), (239.0, 188.0, "E"), (261.0, 188.0, "W")):
        K.bench(bx, by, f)
    for (lx, ly) in ((242.0, 180.0), (258.0, 180.0), (242.0, 236.0), (258.0, 236.0), (230.0, 252.0), (270.0, 252.0)):
        K.lamp_post(lx, ly, None, 12.0)
    # trees and hedges framing the tower (crowns are solid for the camera)
    for (tx, ty, s) in ((184, 262, 1.15), (186, 300, 1.2), (206, 316, 1.1), (294, 316, 1.1), (316, 300, 1.2), (316, 262, 1.15), (186, 190, 1.0), (214, 186, 1.0)):
        K.tree(tx, ty, s, int(tx * 3 + ty))
    K.hedge(TX0 - 4.0, TY1 + 4.0, TX1 + 4.0, TY1 + 6.4, 3.2, 41)
    K.hedge(TX0 - 6.4, TY0 + 4.0, TX0 - 4.0, TY1 + 4.0, 3.2, 42)
    K.hedge(TX1 + 4.0, TY0 + 4.0, TX1 + 6.4, TY1 + 4.0, 3.2, 43)
    for (bx, by) in ((222.0, 252.0), (278.0, 252.0), (232.0, 246.0), (268.0, 246.0)):
        K.bush(bx, by, 0.9, int(bx + by))
    sc.dz = 0.0
    TARGETS["pond"] = (204.0, 222.0 + 17.0, 0.3)


def pond_lite(cx, cy):
    G = "Plaza"
    for k in range(16):
        ring(cx, cy, 9.0, 10.6 + (0.25 if k % 2 else 0.0), 0.3, 1.2 + (0.2 if k % 3 == 0 else 0.0), ["TurqC", "Marble", "TurqB"][k % 3], G, 16, k * 22.5, (k + 1) * 22.5)
    C(cx, cy, 0.3, 0.5, 9.1, "Sand", G, 16); C(cx, cy, 0.5, 0.95, 9.05, "Water", "Water", 16)
    COL(cx - 10.7, cy - 10.7, 0.3, cx + 10.7, cy + 10.7, 1.3, "PondRim", G)
    C(cx, cy, 0.5, 2.4, 1.4, "Marble", G, 10); C(cx, cy, 2.4, 2.8, 2.4, "TurqC", G, 10); C(cx, cy, 2.8, 5.6, 0.3, "Foam", "Water", 6)
    for k in range(6):
        a = math.radians(k * 60)
        beam((cx, cy, 5.4), (cx + 1.8 * math.cos(a), cy + 1.8 * math.sin(a), 3.2), 0.2, "Foam", "Water")
    # heart-shaped flamingo float
    ring(cx - 4.0, cy + 2.5, 1.2, 2.4, 0.95, 1.8, "Pink", G, 12)
    K.bench(cx, cy + 14.0, "S")
