"""MistressFlat4: the spacious flat of Grill Dad's mistress (separate hidden model, entered via the teleport pad of the tower).
Plan coords (local): x east, y north, z up, 1 unit = 1 stud. Floor top z=0, ceiling z=CH. Outer walls on x=0, x=W, y=0, y=D.

Layout (84 x 56, ceiling 13):
  south half  y 0..32 : living room (x 0..34) | entry vestibule (x 34..48, y 0..10) + dining (x 34..56) | kitchen (x 56..84)
  north half  y 32..56: bedroom (x 0..32) | bathroom (x 32..50) | dressing room (x 50..62) | sun lounge with grill bar (x 62..84)
Contract (ApartmentService / DialogueService): Arrival, ExitDoor (tag ApartmentExit), Table_Top (tag MistressDesk, DadId GrillDad),
MistressSeat, GuestSeat; CamBounds (tag ApartmentCamBounds)."""
import math, random
import gd_kit as K
from gd_kit import B, C, COL, FB, FP, text, icon, ball, ring, hcyl, beam

sc = None
W, D, CH = 84.0, 56.0, 13.0
WT = 1.0
DOOR_H = 9.0
ANCH = {}
LIGHTS = []        # (x, y, z, range, brightness, (r, g, b))
TARGETS = {}
DOORS = []         # (name, cx, cy, width, axis) axis = wall direction
R = random.Random(404)

G_W, G_F, G_C, G_P = "FlatWalls", "FlatFloor", "FlatCeil", "FlatProps"


def build(scene):
    global sc
    sc = scene
    K.init(scene)
    shell()
    vestibule()
    living()
    dining()
    kitchen()
    bedroom()
    bathroom()
    dressing()
    lounge()
    view()


def anchor(name, x, y, z, look):
    ANCH[name] = {"pos": (x, y, z), "look": look}


def light(x, y, z, rng=18.0, br=0.7, col=(255, 222, 170)):
    LIGHTS.append((x, y, z, rng, br, col))


# ------------------------------------------------------------------ shell: floor, ceiling, walls with openings
def floor_planks(x0, y0, x1, y1, mats=("FloorOak", "FloorOakB", "FloorOakC"), axis="x"):
    if axis == "x":
        n = max(1, int((y1 - y0) / 1.6)); st = (y1 - y0) / n
        for i in range(n):
            B(x0, y0 + i * st + 0.02, 0, x1, y0 + (i + 1) * st - 0.02, 0.12, mats[i % len(mats)], G_F)
    else:
        n = max(1, int((x1 - x0) / 1.6)); st = (x1 - x0) / n
        for i in range(n):
            B(x0 + i * st + 0.02, y0, 0, x0 + (i + 1) * st - 0.02, y1, 0.12, mats[i % len(mats)], G_F)


def floor_tiles(x0, y0, x1, y1, a, b, size=2.0):
    nx = max(1, int(round((x1 - x0) / size))); ny = max(1, int(round((y1 - y0) / size)))
    sx = (x1 - x0) / nx; sy = (y1 - y0) / ny
    for i in range(nx):
        for j in range(ny):
            B(x0 + i * sx + 0.03, y0 + j * sy + 0.03, 0, x0 + (i + 1) * sx - 0.03, y0 + (j + 1) * sy - 0.03, 0.12, a if (i + j) % 2 else b, G_F)


def shell():
    # structural slab + ceiling (solid for the camera), one floor collider
    B(-0.5, -0.5, -1.0, W + 0.5, D + 0.5, -0.02, "WoodDark", G_F)
    COL(-0.5, -0.5, -1.0, W + 0.5, D + 0.5, 0.12, "Floor", G_F)
    B(-0.5, -0.5, CH, W + 0.5, D + 0.5, CH + 1.0, "Ceiling", G_C)
    COL(-0.5, -0.5, CH, W + 0.5, D + 0.5, CH + 1.0, "Ceiling", G_C)
    # floor finishes per room
    floor_planks(0.5, 0.5, 33.5, 31.5)                        # living
    floor_tiles(34.5, 0.5, 47.5, 9.5, "Marble", "MarbleB")     # vestibule
    floor_planks(33.5, 9.5, 55.5, 31.5, axis="y")              # dining
    floor_tiles(55.5, 0.5, 83.5, 31.5, "TileW", "TileT", 2.5)  # kitchen
    floor_planks(0.5, 32.5, 31.5, 55.5)                        # bedroom
    floor_tiles(32.5, 32.5, 49.5, 55.5, "TileW", "TileP", 2.0) # bathroom
    floor_planks(50.5, 32.5, 61.5, 55.5, ("FloorOakC", "FloorOak"))
    floor_tiles(62.5, 32.5, 83.5, 55.5, "MarbleB", "Marble", 3.0)  # lounge
    # fill strips under the interior walls so no floor gap shows
    for (x0, y0, x1, y1) in ((0.5, 31.6, 83.5, 32.4), (31.6, 32.4, 32.4, 55.5), (49.6, 32.4, 50.4, 55.5), (61.6, 32.4, 62.4, 55.5),
                             (33.6, 0.5, 34.4, 9.0), (47.6, 0.5, 48.4, 9.0), (55.5, 9.5, 56.0, 31.5)):
        B(x0, y0, 0, x1, y1, 0.1, "WoodDark", G_F)
    # outer walls (outside face turquoise, inside per room) with windows
    win = lambda u0, u1: (u0, u1, 3.0, 10.5, "win")
    # south wall y=0: living windows, exit door, kitchen windows
    K.wall("x", 0.0, 0.0, 34.0, 0.0, CH, [win(5, 13), win(20, 28)], "Turq", G_W, WT, 1, "WallTurq", "White", "Wall")
    K.wall("x", 0.0, 34.0, 48.0, 0.0, CH, [(39.0, 45.0, 0.0, DOOR_H, "door")], "Turq", G_W, WT, 1, "WallCream", "White", "Wall")
    K.wall("x", 0.0, 48.0, 56.0, 0.0, CH, [], "Turq", G_W, WT, 1, "WallCream", "White", "Wall")
    K.wall("x", 0.0, 56.0, 84.0, 0.0, CH, [win(60, 68), win(72, 80)], "Turq", G_W, WT, 1, "WallCream", "White", "Wall")
    # north wall y=D
    K.wall("x", D, 0.0, 32.0, 0.0, CH, [win(6, 14), win(18, 26)], "Turq", G_W, WT, -1, "WallLilac", "White", "Wall")
    K.wall("x", D, 32.0, 50.0, 0.0, CH, [(37.0, 45.0, 6.0, 10.5, "win")], "Turq", G_W, WT, -1, "TileW", "White", "Wall")
    K.wall("x", D, 50.0, 62.0, 0.0, CH, [], "Turq", G_W, WT, -1, "WallRose", "White", "Wall")
    K.wall("x", D, 62.0, 84.0, 0.0, CH, [(64.0, 82.0, 1.5, 12.0, "win")], "Turq", G_W, WT, -1, "WallTurq", "White", "Wall")
    # west wall x=0
    K.wall("y", 0.0, 0.0, 32.0, 0.0, CH, [win(8, 16), win(20, 28)], "Turq", G_W, WT, 1, "WallTurq", "White", "Wall")
    K.wall("y", 0.0, 32.0, 56.0, 0.0, CH, [win(38, 48)], "Turq", G_W, WT, 1, "WallLilac", "White", "Wall")
    # east wall x=W
    K.wall("y", W, 0.0, 32.0, 0.0, CH, [win(4, 10)], "Turq", G_W, WT, -1, "WallCream", "White", "Wall")
    K.wall("y", W, 32.0, 56.0, 0.0, CH, [(35.0, 53.0, 1.5, 12.0, "win")], "Turq", G_W, WT, -1, "WallTurq", "White", "Wall")
    # interior wall y=32 between the halves: doors to bedroom, bathroom, dressing; wide arch to the lounge
    ops = [(13.0, 19.0, 0.0, DOOR_H, "door"), (38.0, 43.0, 0.0, DOOR_H, "door"), (53.0, 58.0, 0.0, DOOR_H, "door"), (65.0, 81.0, 0.0, 11.0, "open")]
    K.wall("x", 32.0, 0.5, 32.0, 0.0, CH, [o for o in ops if o[1] <= 32], "WallTurq", G_W, WT, 1, "WallLilac", "White", "Wall")
    K.wall("x", 32.0, 32.0, 50.0, 0.0, CH, [o for o in ops if 32 <= o[0] and o[1] <= 50], "WallCream", G_W, WT, 1, "TileW", "White", "Wall")
    K.wall("x", 32.0, 50.0, 62.0, 0.0, CH, [o for o in ops if 50 <= o[0] and o[1] <= 62], "WallCream", G_W, WT, 1, "WallRose", "White", "Wall")
    K.wall("x", 32.0, 62.0, 83.5, 0.0, CH, [o for o in ops if o[0] >= 62], "WallCream", G_W, WT, 1, "WallTurq", "White", "Wall")
    for (n, cx, w) in (("bedroom door", 16.0, 6.0), ("bathroom door", 40.5, 5.0), ("dressing door", 55.5, 5.0), ("lounge arch", 73.0, 16.0)):
        DOORS.append((n, cx, 32.0, w, "x"))
    DOORS.append(("exit door", 42.0, 0.0, 6.0, "x"))
    # north-half partitions
    K.wall("y", 32.0, 32.5, 55.5, 0.0, CH, [], "WallLilac", G_W, WT, 1, "TileW", "White", "Wall")
    K.wall("y", 50.0, 32.5, 55.5, 0.0, CH, [], "TileW", G_W, WT, 1, "WallRose", "White", "Wall")
    K.wall("y", 62.0, 32.5, 55.5, 0.0, CH, [], "WallRose", G_W, WT, 1, "WallTurq", "White", "Wall")
    # vestibule side walls (open towards the flat in the north), with a niche
    K.wall("y", 34.0, 0.5, 9.0, 0.0, CH, [], "WallTurq", G_W, 1.0, 1, "WallCream", "White", "Wall")
    K.wall("y", 48.0, 0.5, 9.0, 0.0, CH, [], "WallCream", G_W, 1.0, 1, "WallCream", "White", "Wall")
    for x in (33.5, 47.5):
        B(x - 0.1, 8.6, 0, x + 1.1, 9.6, CH, "White", G_W)
    # skirting boards along the main walls (small, above the floor finish)
    for (x0, y0, x1, y1) in ((0.5, 0.5, 34.0, 0.7), (48.5, 0.5, 83.5, 0.7), (0.5, 0.7, 0.7, 31.5), (83.3, 0.7, 83.5, 31.5)):
        B(x0, y0, 0.12, x1, y1, 0.8, "White", G_P)
    # crown moulding on the ceiling edge of the open south half
    for (x0, y0, x1, y1) in ((0.5, 0.5, 83.5, 1.1), (0.5, 30.9, 83.5, 31.5), (0.5, 1.1, 1.1, 30.9), (82.9, 1.1, 83.5, 30.9)):
        B(x0, y0, CH - 0.6, x1, y1, CH - 0.02, "White", G_P)
    TARGETS["living"] = (6.5, 15.0, 0.12)


# ------------------------------------------------------------------ furniture helpers
def rug(x0, y0, x1, y1, mats, border="White"):
    B(x0, y0, 0.12, x1, y1, 0.18, border, G_P)
    n = len(mats); st = (x1 - x0 - 1.0) / n
    for i, m in enumerate(mats):
        B(x0 + 0.5 + i * st, y0 + 0.5, 0.18, x0 + 0.5 + (i + 1) * st, y1 - 0.5, 0.22, m, G_P)


def plant(x, y, s=1.0, pot="Coral"):
    C(x, y, 0.12, 0.12 + 1.8 * s, 0.9 * s, pot, G_P, 10)
    C(x, y, 0.12 + 1.8 * s, 0.12 + 2.0 * s, 0.8 * s, "Dirt", G_P, 10)
    for k in range(5):
        a = math.radians(k * 72 + 20)
        ball(x + 0.7 * s * math.cos(a), y + 0.7 * s * math.sin(a), 3.0 * s + (k % 2) * 0.8 * s, 1.0 * s, ("Leaf", "LeafB", "LeafC")[k % 3], G_P, seg=8, rings=4)
    ball(x, y, 4.4 * s, 1.1 * s, "LeafB", G_P, seg=8, rings=4)
    COL(x - 1.0 * s, y - 1.0 * s, 0.12, x + 1.0 * s, y + 1.0 * s, 4.0 * s, "Plant", G_P)


def ceiling_lamp(x, y, mat="LampSoft", rim="Gold", r=1.6):
    C(x, y, CH - 0.35, CH, r + 0.3, rim, G_P, 12)
    C(x, y, CH - 0.75, CH - 0.35, r, mat, G_P, 12)
    light(x, y, CH - 2.0)


def pendant(x, y, z=8.2, shade="Coral"):
    B(x - 0.05, y - 0.05, z + 1.2, x + 0.05, y + 0.05, CH, "Iron", G_P)
    ball(x, y, z + 1.2, 1.2, shade, G_P, lat0=0, lat1=90, seg=10, rings=3, rz=1.0)
    C(x, y, z + 0.9, z + 1.2, 0.6, "LampSoft", G_P, 8)


def picture(axis, line, side, u0, u1, z0, z1, kind="dad"):
    """Framed picture on a wall; side = +1/-1 the room side of the wall line."""
    def fb(a0, a1, d0, d1, za, zb, m):
        if axis == "x": B(a0, line + side * d0, za, a1, line + side * d1, zb, m, G_P)
        else: B(line + side * d0, a0, za, line + side * d1, a1, zb, m, G_P)
    fb(u0, u1, 0.5, 0.62, z0, z1, "Gold")
    fb(u0 + 0.3, u1 - 0.3, 0.6, 0.66, z0 + 0.3, z1 - 0.3, "Paper" if kind != "sea" else "SkyBlue")
    face = {("x", 1): "N", ("x", -1): "S", ("y", 1): "E", ("y", -1): "W"}[(axis, side)]
    cu = (u0 + u1) / 2; zc = (z0 + z1) / 2
    px, py = (cu, line + side * 0.66) if axis == "x" else (line + side * 0.66, cu)
    if kind == "dad":
        cell = min((u1 - u0 - 1.0) / 12.0, (z1 - z0 - 1.0) / 12.0)
        icon(K.DAD_FACE, {"h": "Brown", "y": "Skin", "b": "Black"}, px, py, zc, cell, face, 0.0, 0.06, G_P)
    elif kind == "heart":
        heart(px, py, zc, (z1 - z0) / 11.0, face)
    elif kind == "grill":
        icon(K.GRILL_ICON, {"1": "Black"}, px, py, zc, min((u1 - u0 - 1.0) / 11.0, (z1 - z0 - 1.0) / 12.0), face, 0.0, 0.06, G_P)
    else:
        fb(u0 + 0.3, u1 - 0.3, 0.62, 0.68, z0 + 0.3, zc - 0.4, "Water")


HEART = [".11...11.", "1111.1111", "111111111", "111111111", ".1111111.", "..11111..", "...111...", "....1...."]


def heart(px, py, zc, cell, face, mat="Pink"):
    icon(HEART, {"1": mat}, px, py, zc, cell, face, 0.0, 0.06, G_P)


def curtains(axis, line, side, a0, a1, zt=11.4, mat="VelvetPink"):
    def fb(u0, u1, d0, d1, za, zb, m):
        if axis == "x": B(u0, line + side * d0, za, u1, line + side * d1, zb, m, G_P)
        else: B(line + side * d0, u0, za, line + side * d1, u1, zb, m, G_P)
    fb(a0 - 1.2, a1 + 1.2, 0.75, 0.9, zt, zt + 0.25, "Gold")
    for (u0, u1) in ((a0 - 1.2, a0 + 0.6), (a1 - 0.6, a1 + 1.2)):
        k = 0; u = u0
        while u < u1 - 0.05:
            fb(u, min(u1, u + 0.45), 0.6 + (k % 2) * 0.12, 0.85 + (k % 2) * 0.12, 0.5, zt, mat); u += 0.45; k += 1
        fb(u0 - 0.05, u1 + 0.05, 0.55, 1.05, 4.6, 5.0, "Gold")


def sofa(x0, y0, x1, y1, face, body="Velvet", cushion="VelvetPink", pillows=("Yellow", "White", "Coral")):
    """Sofa in the rectangle; sitters look towards `face` (the open side)."""
    B(x0, y0, 0.12, x1, y1, 2.0, body, G_P)
    COL(x0, y0, 0.12, x1, y1, 3.2, "Sofa", G_P)   # above step height: pathfinding and walkers go around, not over
    t = 1.2
    if face == "N": back = (x0, y0, x1, y0 + t); arms = ((x0, y0, x0 + t, y1), (x1 - t, y0, x1, y1)); seat = (x0 + t, y0 + t, x1 - t, y1 - 0.1)
    elif face == "S": back = (x0, y1 - t, x1, y1); arms = ((x0, y0, x0 + t, y1), (x1 - t, y0, x1, y1)); seat = (x0 + t, y0 + 0.1, x1 - t, y1 - t)
    elif face == "E": back = (x0, y0, x0 + t, y1); arms = ((x0, y0, x1, y0 + t), (x0, y1 - t, x1, y1)); seat = (x0 + t, y0 + t, x1 - 0.1, y1 - t)
    else: back = (x1 - t, y0, x1, y1); arms = ((x0, y0, x1, y0 + t), (x0, y1 - t, x1, y1)); seat = (x0 + 0.1, y0 + t, x1 - t, y1 - t)
    B(back[0], back[1], 2.0, back[2], back[3], 4.6, body, G_P)
    COL(back[0], back[1], 2.0, back[2], back[3], 4.6, "Sofa", G_P)
    for a in arms: B(a[0], a[1], 2.0, a[2], a[3], 3.2, body, G_P)
    B(seat[0], seat[1], 2.0, seat[2], seat[3], 2.5, cushion, G_P)
    # pillows against the back
    horiz = face in ("N", "S")
    n = len(pillows)
    for i, m in enumerate(pillows):
        if horiz:
            u = seat[0] + (i + 0.5) * (seat[2] - seat[0]) / n
            yy = back[3] + 0.1 if face == "N" else back[1] - 0.9
            B(u - 1.0, yy, 2.5, u + 1.0, yy + 0.8, 4.2, m, G_P)
        else:
            u = seat[1] + (i + 0.5) * (seat[3] - seat[1]) / n
            xx = back[2] + 0.1 if face == "E" else back[0] - 0.9
            B(xx, u - 1.0, 2.5, xx + 0.8, u + 1.0, 4.2, m, G_P)
    for (lx, ly) in ((x0 + 0.4, y0 + 0.4), (x1 - 0.4, y0 + 0.4), (x0 + 0.4, y1 - 0.4), (x1 - 0.4, y1 - 0.4)):
        C(lx, ly, 0.12, 0.13, 0.25, "Gold", G_P, 6)


def chair(x, y, face, seat="VelvetPink", frame="Gold"):
    """Dining chair centred at (x, y); the sitter looks towards `face`."""
    for (dx, dy) in ((-0.8, -0.8), (0.8, -0.8), (-0.8, 0.8), (0.8, 0.8)):
        B(x + dx - 0.12, y + dy - 0.12, 0.12, x + dx + 0.12, y + dy + 0.12, 2.6, frame, G_P)
    B(x - 1.0, y - 1.0, 2.6, x + 1.0, y + 1.0, 3.1, seat, G_P)
    (rx, ry), (nx, ny) = K.FACE[face]
    bx, by = x - nx * 0.9, y - ny * 0.9
    if face in ("N", "S"): B(x - 1.0, by - 0.15, 3.1, x + 1.0, by + 0.15, 6.2, seat, G_P)
    else: B(bx - 0.15, y - 1.0, 3.1, bx + 0.15, y + 1.0, 6.2, seat, G_P)
    COL(x - 1.0, y - 1.0, 0.12, x + 1.0, y + 1.0, 3.1, "Chair", G_P)


def stool(x, y, seat="Velvet"):
    C(x, y, 0.12, 0.4, 0.9, "Chrome", G_P, 10); C(x, y, 0.4, 4.2, 0.18, "Chrome", G_P, 6)
    ring(x, y, 0.55, 0.75, 1.6, 1.8, "Chrome", G_P, 10)
    C(x, y, 4.2, 4.7, 1.0, seat, G_P, 12)
    COL(x - 0.9, y - 0.9, 0.12, x + 0.9, y + 0.9, 4.7, "Stool", G_P)


def vase(x, y, z, m="TurqC"):
    C(x, y, z, z + 1.2, 0.4, m, G_P, 8)
    for k, fm in enumerate(("FlowerPink", "FlowerYellow", "FlowerRed", "FlowerWhite")):
        a = math.radians(k * 90)
        beam((x, y, z + 1.0), (x + 0.5 * math.cos(a), y + 0.5 * math.sin(a), z + 2.4), 0.08, "Leaf", G_P)
        ball(x + 0.5 * math.cos(a), y + 0.5 * math.sin(a), z + 2.5, 0.32, fm, G_P, seg=6, rings=3)


def books(x0, x1, y0, y1, z, axis="x"):
    u = x0 if axis == "x" else y0
    end = x1 if axis == "x" else y1
    cols = ("Red", "Blue", "Yellow", "Teal", "Pink", "Green", "Purple", "Orange")
    while u < end - 0.3:
        w = R.uniform(0.25, 0.45); h = R.uniform(1.0, 1.6)
        m = R.choice(cols)
        if axis == "x": B(u, y0, z, u + w - 0.03, y1, z + h, m, G_P)
        else: B(x0, u, z, x1, u + w - 0.03, z + h, m, G_P)
        u += w


# ------------------------------------------------------------------ rooms
def vestibule():
    # exit door (closed leaf) in the south wall, mat, coat hooks, mirror, console
    B(39.25, 0.5, 0.12, 44.75, 0.62, 8.8, "TurqDark", G_P)
    COL(39.0, -0.5, 0.12, 45.0, 0.62, DOOR_H, "ExitDoorLeaf", G_P)   # closed leaf: nobody walks out of the flat
    for (a, b) in ((39.7, 41.8), (42.2, 44.3)):
        B(a, 0.62, 1.0, b, 0.7, 4.2, "TurqB", G_P); B(a, 0.62, 4.8, b, 0.7, 8.2, "TurqB", G_P)
    B(43.6, 0.62, 3.9, 44.0, 1.1, 4.3, "Gold", G_P)
    B(40.0, 1.2, 0.12, 44.0, 3.6, 0.2, "Coral", G_P)
    B(34.5, 3.0, 2.8, 35.6, 7.0, 3.2, "WoodLight", G_P)         # console shelf
    COL(34.5, 3.0, 0.12, 35.6, 7.0, 3.2, "Console", G_P)
    B(34.5, 3.2, 0.12, 35.4, 3.5, 2.8, "Gold", G_P); B(34.5, 6.5, 0.12, 35.4, 6.8, 2.8, "Gold", G_P)
    vase(35.05, 5.0, 3.2)
    B(34.5, 3.4, 4.6, 34.62, 6.6, 9.2, "Gold", G_P); B(34.62, 3.6, 4.8, 34.68, 6.4, 9.0, "Mirror", "Glass")
    for k in range(4):
        B(47.4, 2.5 + k * 1.6, 6.6, 47.5, 2.8 + k * 1.6, 7.4, "Gold", G_P)
    B(46.9, 5.6, 4.6, 47.4, 6.5, 7.2, "Coral", G_P)          # hanging apron: DAD
    plant(46.5, 8.0, 0.8, "TurqB")
    ceiling_lamp(41.0, 5.0)
    anchor("arrival", 41.0, 5.5, 0.12, (0, 0, 1))                       # Roblox look +Z = plan +y
    anchor("exit_door", 42.0, 0.6, 4.4, (0, 0, 1))
    TARGETS["vestibule"] = (41.0, 6.0, 0.12)


def living():
    # big corner sofa facing the TV wall (west), coffee table, rug, armchairs, shelves, electric "grill fireplace"
    rug(8.0, 7.0, 24.0, 23.0, ("TurqC", "PinkB", "TurqC", "PinkB", "TurqC"))
    sofa(18.0, 6.0, 25.0, 24.0, "W")
    sofa(6.5, 2.4, 15.5, 8.0, "N", "Velvet", "VelvetPink", ("White", "Yellow"))
    C(14.0, 15.0, 0.22, 1.9, 0.4, "Gold", G_P, 8)
    C(14.0, 15.0, 1.9, 2.3, 3.0, "Marble", G_P, 16)
    COL(11.0, 12.0, 0.12, 17.0, 18.0, 2.3, "CoffeeTable", G_P)
    vase(14.6, 15.4, 2.3, "Coral")
    B(12.6, 14.2, 2.3, 13.8, 15.0, 2.5, "Navy", G_P); B(12.5, 14.4, 2.5, 13.6, 15.2, 2.7, "Pink", G_P)
    # TV wall on the west: low cabinet + big screen + speakers
    B(0.5, 8.0, 0.12, 2.6, 22.0, 2.6, "White", G_P)
    COL(0.5, 8.0, 0.12, 2.6, 22.0, 2.6, "TvCabinet", G_P)
    for k in range(4):
        B(2.6, 8.4 + k * 3.4, 0.5, 2.66, 11.4 + k * 3.4, 2.2, "TurqC", G_P)
    B(0.5, 10.0, 4.0, 0.9, 20.0, 9.8, "Black", G_P); B(0.9, 10.3, 4.3, 0.96, 19.7, 9.5, "Screen", G_P)
    icon(K.GRILL_ICON, {"1": "White"}, 0.97, 15.0, 6.9, 0.32, "E", 0.0, 0.04, G_P)
    for yy in (8.6, 20.6):
        B(0.6, yy, 2.6, 1.6, yy + 0.8, 6.6, "Black", G_P)
    # "grill fireplace" in the south-west corner: marble surround with neon flames
    B(0.5, 25.0, 0.12, 3.0, 31.0, 6.0, "Marble", G_P)
    B(2.9, 26.0, 0.8, 3.02, 30.0, 4.6, "Black", G_P)
    for k in range(5):
        B(2.95, 26.4 + k * 0.7, 0.9, 3.05, 26.9 + k * 0.7, 1.6 + (k % 3) * 0.7, "Fire" if k % 2 else "FireY", G_P)
    for k in range(4):
        B(3.0, 26.1 + k * 1.1, 2.6, 3.1, 26.3 + k * 1.1, 2.7, "Iron", G_P)
    B(0.5, 24.6, 6.0, 3.5, 31.4, 6.5, "MarbleB", G_P)
    COL(0.5, 25.0, 0.12, 3.5, 31.4, 6.5, "Fireplace", G_P)
    picture("y", 0.0, 1, 25.6, 30.4, 7.5, 11.4, "dad")
    heart(1.2, 28.0, 12.2, 0.1, "E")
    # reading lamp by the north window side (armchair removed on request)
    B(11.0, 27.0, 0.12, 12.0, 28.0, 0.3, "Gold", G_P); B(11.4, 27.4, 0.3, 11.6, 27.6, 7.6, "Gold", G_P)
    ball(11.5, 27.5, 7.6, 1.1, "Linen", G_P, lat0=-30, lat1=60, seg=10, rings=3)
    light(11.5, 27.5, 7.0, 12.0, 0.45)
    # bookshelf along the vestibule wall
    B(30.0, 1.0, 0.12, 33.4, 9.0, 10.0, "White", G_P)
    COL(30.0, 1.0, 0.12, 33.4, 9.0, 10.0, "Shelf", G_P)
    for z in (2.4, 4.8, 7.2):
        B(29.9, 1.1, z, 30.05, 8.9, z + 0.18, "WoodLight", G_P)
        books(29.85, 30.0, 1.4, 8.6, z + 0.18, "y")
    for (px, py) in ((2.0, 3.0), (27.5, 3.0), (31.5, 30.0)):
        plant(px, py, 1.0, "Coral")
    curtains("x", 0.0, 1, 5, 13); curtains("x", 0.0, 1, 20, 28)
    ceiling_lamp(14.0, 15.0, "LampSoft", "Gold", 2.4)
    ceiling_lamp(26.0, 26.0)
    TARGETS["living sofa front"] = (14.0, 20.5, 0.12)
    TARGETS["fireplace"] = (6.0, 18.0, 0.12)


def dining():
    # the mistress's dining table = contract Table_Top (5.2 x 5.2 top, height 3.4), two seats facing each other
    tx, ty = 44.0, 21.0
    rug(37.0, 14.0, 51.0, 28.0, ("Coral", "PinkB", "Coral"), "Gold")
    B(tx - 2.6, ty - 2.6, 3.2, tx + 2.6, ty + 2.6, 3.6, "Marble", G_P)
    B(tx - 2.7, ty - 2.7, 3.0, tx + 2.7, ty + 2.7, 3.2, "Gold", G_P)
    C(tx, ty, 0.22, 0.5, 1.6, "Gold", G_P, 12); C(tx, ty, 0.5, 3.0, 0.45, "Gold", G_P, 8)
    COL(tx - 2.7, ty - 2.7, 0.12, tx + 2.7, ty + 2.7, 3.6, "DiningTable", G_P)
    # table setting: candles, plates, a little heart cake
    for (dx, dy) in ((0.0, -1.7), (0.0, 1.7)):
        C(tx + dx, ty + dy, 3.6, 3.7, 0.8, "White", G_P, 10); C(tx + dx, ty + dy, 3.7, 3.75, 0.5, "PinkB", G_P, 10)
    for dx in (-1.6, 1.6):
        C(tx + dx, ty, 3.6, 3.75, 0.3, "Gold", G_P, 8); C(tx + dx, ty, 3.75, 4.9, 0.14, "White", G_P, 6); B(tx + dx - 0.07, ty - 0.07, 4.9, tx + dx + 0.07, ty + 0.07, 5.2, "FireY", G_P)
    C(tx, ty, 3.6, 4.1, 0.55, "PinkB", G_P, 10); ball(tx, ty, 4.25, 0.18, "Red", G_P, seg=6, rings=3)
    chair(tx, ty + 4.0, "S", "VelvetPink")     # mistress (north side, looks south)
    chair(tx, ty - 4.0, "N", "Velvet")         # guest / player with the dad (south side, looks north)
    anchor("table_top", tx, ty, 3.6, (0, 0, 1))
    anchor("mistress_seat", tx, ty + 4.0, 3.1, (0, 0, -1))
    anchor("guest_seat", tx, ty - 4.0, 3.1, (0, 0, 1))
    # side chairs
    chair(tx - 4.0, ty, "E", "Linen"); chair(tx + 4.0, ty, "W", "Linen")
    # chandelier
    B(tx - 0.06, ty - 0.06, 10.4, tx + 0.06, ty + 0.06, CH, "Gold", G_P)
    ring(tx, ty, 2.2, 2.5, 9.9, 10.4, "Gold", G_P, 14)
    for k in range(8):
        a = math.radians(k * 45)
        C(tx + 2.35 * math.cos(a), ty + 2.35 * math.sin(a), 10.4, 11.0, 0.18, "LampSoft", G_P, 6)
    ball(tx, ty, 10.1, 0.7, "Gold", G_P, seg=8, rings=4)
    light(tx, ty, 9.0, 18.0, 0.8)
    # sideboard on the dining wall (south), with the golden spatula on a stand
    B(48.6, 1.0, 0.12, 55.4, 3.4, 3.6, "White", G_P)
    COL(48.6, 1.0, 0.12, 55.4, 3.4, 3.6, "Sideboard", G_P)
    for k in range(3):
        B(48.9 + k * 2.2, 3.4, 0.6, 50.9 + k * 2.2, 3.46, 3.2, "TurqC", G_P)
    B(50.8, 1.8, 3.6, 53.2, 2.6, 3.9, "Navy", G_P)
    beam((52.0, 2.2, 3.9), (52.0, 2.2, 6.6), 0.16, "Gold", G_P); B(51.2, 2.0, 6.6, 52.8, 2.4, 8.4, "Gold", G_P)
    picture("x", 0.0, 1, 49.0, 55.0, 7.0, 11.4, "heart")
    plant(37.0, 30.0, 0.9, "TurqB"); plant(51.6, 29.5, 0.9, "Coral")
    TARGETS["dining guest seat"] = (tx, ty - 6.5, 0.12)
    TARGETS["dining"] = (40.0, 12.0, 0.12)


def kitchen():
    # counters along the east and south walls, tall fridge, hood, island with an indoor grill + bar stools
    x0, x1, y0, y1 = 56.0, 83.5, 0.5, 31.5
    # south counter run (y 0.5..3.5) under the windows
    B(57.0, 0.5, 0.12, 82.0, 3.5, 3.4, "White", G_P); B(56.8, 0.5, 3.4, 82.2, 3.8, 3.7, "Marble", G_P)
    COL(56.8, 0.5, 0.12, 82.2, 3.8, 3.7, "Counter", G_P)
    for k in range(10):
        B(57.2 + k * 2.48, 3.5, 0.5, 59.5 + k * 2.48, 3.56, 3.1, "TurqC" if k % 2 else "Turq", G_P)
        B(58.0 + k * 2.48, 3.56, 2.6, 58.8 + k * 2.48, 3.7, 2.8, "Gold", G_P)
    # sink under the window + tap
    B(62.0, 1.0, 3.5, 66.0, 3.0, 3.72, "Steel", G_P)
    B(63.8, 0.8, 3.7, 64.2, 1.2, 5.0, "Chrome", G_P); B(63.8, 0.8, 4.8, 64.2, 2.0, 5.1, "Chrome", G_P)
    # east counter run (x 80.5..83.5) with the hob and hood
    B(80.5, 3.8, 0.12, 83.5, 22.0, 3.4, "White", G_P); B(80.2, 3.8, 3.4, 83.5, 22.2, 3.7, "Marble", G_P)
    COL(80.2, 3.8, 0.12, 83.5, 22.2, 3.7, "Counter", G_P)
    for k in range(7):
        B(80.44, 4.2 + k * 2.5, 0.5, 80.5, 6.5 + k * 2.5, 3.1, "Turq" if k % 2 else "TurqC", G_P)
    B(80.8, 11.0, 3.7, 83.2, 15.0, 3.78, "Black", G_P)
    for (cy_, r) in ((12.0, 0.6), (14.0, 0.5)):
        ring(82.0, cy_, r - 0.12, r, 3.78, 3.8, "Fire", G_P, 10)
    B(81.2, 10.5, 8.0, 83.5, 15.5, 9.0, "Steel", G_P); B(82.4, 12.0, 9.0, 83.5, 14.0, CH, "Steel", G_P)
    # wall cabinets
    for (a, b) in ((16.0, 22.0),):   # no cabinet in front of the east window (y 4..10)
        B(81.8, a, 7.4, 83.5, b, 11.0, "White", G_P)
        B(81.74, a + 0.2, 7.6, 81.8, (a + b) / 2 - 0.1, 10.8, "TurqC", G_P); B(81.74, (a + b) / 2 + 0.1, 7.6, 81.8, b - 0.2, 10.8, "TurqC", G_P)
    # tall fridge in the north-east corner
    B(79.0, 24.0, 0.12, 83.5, 29.0, 10.0, "Chrome", G_P)
    B(78.94, 24.3, 6.2, 79.0, 28.7, 6.3, "Steel", G_P)
    for (z0, z1) in ((1.0, 5.8), (6.6, 9.6)):
        B(78.7, 26.6, z0 + 1.0, 78.94, 27.0, z1 - 1.0, "Steel", G_P)
    for (k, m) in enumerate(("Pink", "Yellow", "Teal")):
        heart(78.93, 25.0 + k * 1.2, 8.4 - (k % 2) * 0.6, 0.08, "W", m)
    COL(78.7, 24.0, 0.12, 83.5, 29.0, 10.0, "Fridge", G_P)
    # island with the indoor grill and stools on the west side
    ix0, ix1, iy0, iy1 = 63.0, 73.0, 12.0, 19.0
    B(ix0, iy0, 0.12, ix1, iy1, 3.4, "Turq", G_P); B(ix0 - 1.0, iy0 - 0.3, 3.4, ix1 + 0.3, iy1 + 0.3, 3.8, "Marble", G_P)
    COL(ix0 - 1.0, iy0 - 0.3, 0.12, ix1 + 0.3, iy1 + 0.3, 3.8, "Island", G_P)
    for k in range(5):
        B(ix0 + 0.4 + k * 1.9, iy0 - 0.06, 0.5, ix0 + 1.9 + k * 1.9, iy0, 3.1, "TurqC", G_P)
    # indoor grill: black steel box, glowing grate, sausages, burgers
    B(67.0, 13.5, 3.8, 72.0, 17.5, 4.5, "Black", G_P)
    for k in range(6):
        B(67.3 + k * 0.8, 13.8, 4.5, 67.55 + k * 0.8, 17.2, 4.6, "Fire" if k % 2 else "Iron", G_P)
    for k in range(3):
        hcyl("y", 14.2, 16.8, 67.9 + k * 1.6, 4.85, 0.3, "Sausage", G_P, 8)
    C(64.6, 15.5, 3.8, 3.9, 1.25, "White", G_P, 14); ring(64.6, 15.5, 1.05, 1.3, 3.9, 3.98, "TurqC", G_P, 14)
    K.burger(64.6, 15.5, 3.9, 0.8)
    for yy in (13.0, 15.5, 18.0):
        stool(60.6, yy, "Velvet" if yy != 15.5 else "VelvetPink")
    # pendants over the island, fruit bowl, coffee machine
    for xx in (65.0, 70.0):
        pendant(xx, 15.5, 8.4, "Turq")
    light(67.5, 15.5, 8.0, 16.0, 0.7)
    C(75.0, 2.0, 3.7, 4.2, 1.1, "White", G_P, 10)
    for k, m in enumerate(("Red", "Yellow", "Orange", "Green")):
        ball(74.6 + (k % 2) * 0.8, 1.6 + (k // 2) * 0.8, 4.5, 0.42, m, G_P, seg=6, rings=3)
    B(70.0, 1.0, 3.7, 71.8, 2.6, 6.0, "Black", G_P); B(70.4, 2.6, 4.2, 71.4, 2.7, 4.8, "Coral", G_P)
    ceiling_lamp(70.0, 8.0); ceiling_lamp(70.0, 24.0)
    plant(60.5, 29.6, 0.9, "Coral")
    kitchen_details()
    TARGETS["kitchen"] = (66.0, 8.0, 0.12)
    TARGETS["kitchen fridge front"] = (75.5, 27.0, 0.12)


def bedroom():
    # king bed against the north wall, nightstands, wardrobe, vanity, rug, curtains
    bx0, bx1, by0, by1 = 9.0, 23.0, 42.0, 55.5
    B(bx0, by0, 0.12, bx1, by1, 2.0, "White", G_P)
    COL(bx0, by0, 0.12, bx1, by1, 3.2, "Bed", G_P)
    B(bx0 + 0.3, by0 + 0.3, 2.0, bx1 - 0.3, by1 - 1.0, 3.0, "Linen", G_P)
    B(bx0 + 0.2, by0 + 0.2, 3.0, bx1 - 0.2, by0 + 7.5, 3.3, "VelvetPink", G_P)        # blanket
    B(bx0 + 0.15, by0 + 0.15, 2.2, bx1 - 0.15, by0 + 7.6, 3.05, "VelvetPink", G_P)
    for xx in (bx0 + 1.0, (bx0 + bx1) / 2 + 0.3):
        B(xx, by1 - 4.0, 3.0, xx + 5.6, by1 - 1.4, 4.0, "White", G_P)
    B((bx0 + bx1) / 2 - 1.3, by1 - 5.0, 3.0, (bx0 + bx1) / 2 + 1.3, by1 - 4.0, 4.4, "Pink", G_P)
    B(bx0 - 0.4, by1 - 0.9, 0.12, bx1 + 0.4, by1 - 0.1, 8.0, "Velvet", G_P)          # headboard
    COL(bx0 - 0.4, by1 - 0.9, 0.12, bx1 + 0.4, by1 - 0.1, 8.0, "Headboard", G_P)
    heart(16.0, by1 - 0.95, 6.4, 0.22, "S", "PinkB")
    for xx in (5.0, 27.0):
        B(xx - 1.6, 51.5, 0.12, xx + 1.6, 54.6, 2.8, "White", G_P)
        B(xx - 1.4, 51.44, 1.0, xx + 1.4, 51.5, 2.4, "TurqC", G_P)
        COL(xx - 1.6, 51.5, 0.12, xx + 1.6, 54.6, 2.8, "Nightstand", G_P)
        C(xx, 53.0, 2.8, 3.0, 0.5, "Gold", G_P, 8); C(xx, 53.0, 3.0, 4.4, 0.12, "Gold", G_P, 6)
        ball(xx, 53.0, 4.4, 0.9, "LampSoft", G_P, lat0=-20, lat1=70, seg=8, rings=3)
        light(xx, 53.0, 4.8, 10.0, 0.45, (255, 200, 210))
    rug(7.0, 36.0, 25.0, 43.5, ("PinkB", "White", "PinkB", "White"), "Coral")
    # wardrobe along the west wall
    B(0.5, 33.5, 0.12, 3.6, 41.0, 10.5, "White", G_P)
    COL(0.5, 33.5, 0.12, 3.6, 41.0, 10.5, "Wardrobe", G_P)
    for (a, b) in ((33.8, 37.2), (37.3, 40.7)):
        B(3.6, a, 0.5, 3.66, b, 10.1, "WallRose", G_P)
        B(3.66, b - 0.6 if a < 37 else a + 0.3, 4.6, 3.8, b - 0.3 if a < 37 else a + 0.6, 6.0, "Gold", G_P)
    # vanity table with mirror on the partition wall (east), stool
    B(29.0, 36.0, 0.12, 31.5, 42.0, 3.2, "White", G_P)
    COL(29.0, 36.0, 0.12, 31.5, 42.0, 3.2, "Vanity", G_P)
    B(31.3, 36.6, 4.0, 31.5, 41.4, 9.6, "Gold", G_P); B(31.24, 37.0, 4.4, 31.3, 41.0, 9.2, "Mirror", "Glass")
    C(27.2, 39.0, 0.12, 2.6, 0.9, "VelvetPink", G_P, 12); COL(26.3, 38.1, 0.12, 28.1, 39.9, 2.6, "Stool", G_P)
    for k, m in enumerate(("Pink", "Teal", "Gold", "Coral")):
        C(29.6 + (k % 2) * 0.8, 36.8 + k * 1.3, 3.2, 3.9 + (k % 2) * 0.4, 0.22, m, G_P, 6)
    vase(30.2, 41.2, 3.2, "PinkB")
    curtains("x", D, -1, 6, 14, mat="Velvet"); curtains("x", D, -1, 18, 26, mat="Velvet")
    plant(28.5, 33.8, 0.8, "TurqB")
    ceiling_lamp(16.0, 40.0, "LampSoft", "Gold", 2.0)
    TARGETS["bedroom"] = (16.0, 36.0, 0.12)


def bathroom():
    # freestanding tub, double sink, toilet, shower corner with glass, towels, mirror
    x0, x1, y0, y1 = 32.5, 49.5, 32.5, 55.5
    tub()
    # double vanity on the west partition
    B(32.5, 36.0, 0.12, 35.5, 46.0, 3.4, "Turq", G_P); B(32.5, 35.8, 3.4, 35.8, 46.2, 3.7, "Marble", G_P)
    COL(32.5, 35.8, 0.12, 35.8, 46.2, 3.7, "Vanity", G_P)
    for yy in (38.5, 43.5):
        C(34.2, yy, 3.6, 3.75, 1.0, "White", G_P, 10)
        B(32.6, yy - 0.2, 3.7, 33.2, yy + 0.2, 5.2, "Gold", G_P); B(32.6, yy - 0.2, 5.0, 33.9, yy + 0.2, 5.3, "Gold", G_P)
    B(32.5, 35.5, 5.6, 32.7, 46.5, 10.8, "Gold", G_P); B(32.7, 35.9, 6.0, 32.76, 46.1, 10.4, "Mirror", "Glass")
    # toilet
    tx, ty = 47.6, 39.0
    B(tx - 1.0, ty - 1.2, 0.12, tx + 1.9, ty + 1.2, 1.6, "White", G_P)
    C(tx - 0.2, ty, 1.6, 1.9, 1.2, "White", G_P, 12)
    B(48.5, ty - 1.6, 1.9, 49.5, ty + 1.6, 4.4, "White", G_P)
    COL(tx - 1.4, ty - 1.6, 0.12, 49.5, ty + 1.6, 4.4, "Toilet", G_P)
    # shower in the south-east corner: tiled tray, glass, rain head
    B(44.0, 32.5, 0.12, 49.5, 36.5, 0.3, "TileT", G_P)
    B(44.0, 36.4, 0.3, 49.0, 36.5, 9.5, "Glass", "Glass")
    COL(44.0, 36.3, 0.12, 49.0, 36.6, 9.5, "ShowerGlass", G_P)
    B(49.0, 34.0, 0.3, 49.5, 34.4, 9.6, "Chrome", G_P); B(47.2, 33.6, 9.6, 49.5, 34.8, 9.8, "Chrome", G_P)
    # towels on rails
    for (yy, m) in ((40.5, "PinkB"), (42.5, "TurqC")):
        B(49.0, yy, 4.6, 49.5, yy + 1.6, 7.6, m, G_P)
    B(49.2, 40.0, 7.5, 49.5, 44.6, 7.7, "Gold", G_P)
    plant(36.0, 34.0, 0.7, "PinkB")
    B(39.0, 37.0, 0.12, 44.0, 41.0, 0.2, "PinkB", G_P)
    ceiling_lamp(41.0, 44.0)
    TARGETS["bathroom"] = (40.5, 43.0, 0.12)


def dressing():
    # walk-in wardrobe: open hanging rails with clothes, shoe shelves, pouf, long mirror
    x0, x1 = 50.5, 61.5
    for (side, xx0, xx1) in ((-1, 50.5, 52.6), (1, 59.4, 61.5)):
        B(xx0, 36.0, 0.12, xx1, 55.0, 0.6, "White", G_P)
        B(xx0, 36.0, 10.0, xx1, 55.0, 10.4, "White", G_P)
        COL(xx0, 36.0, 0.12, xx1, 55.0, 10.4, "Wardrobe", G_P)
        rx = (xx0 + xx1) / 2
        B(rx - 0.08, 36.2, 8.6, rx + 0.08, 54.8, 8.8, "Gold", G_P)
        y = 36.6
        cols = ("Pink", "Turq", "Coral", "White", "Purple", "Yellow", "PinkB", "Teal", "Red")
        k = 0
        while y < 54.4:
            m = cols[(k * 4 + (1 if side > 0 else 0)) % len(cols)]
            B(rx - 0.9, y, 4.6 + (k % 3) * 0.5, rx + 0.9, y + 0.5, 8.6, m, G_P)
            y += 0.75; k += 1
    for k in range(6):
        for (a, b) in ((50.8, 52.3), (59.7, 61.2)):
            B(a, 36.4 + k * 3.0, 0.6, b, 37.4 + k * 3.0, 1.1, ("Red", "Black", "Pink", "Gold", "White", "Coral")[k], G_P)
    # pouf + rug + long mirror on the north wall
    C(56.0, 44.0, 0.12, 2.0, 1.4, "VelvetPink", G_P, 14); COL(54.6, 42.6, 0.12, 57.4, 45.4, 2.0, "Pouf", G_P)
    C(56.0, 44.0, 0.12, 0.18, 3.2, "PinkB", G_P, 16)
    B(54.0, 55.0, 0.6, 58.0, 55.5, 11.0, "Gold", G_P); B(54.3, 54.94, 0.9, 57.7, 55.0, 10.7, "Mirror", "Glass")
    ceiling_lamp(56.0, 44.0, "LampSoft", "Gold", 1.4)
    TARGETS["dressing"] = (56.0, 38.0, 0.12)


def lounge():
    # sun lounge behind the wide arch: huge windows, grill bar with neon, plants, swing chair, lounge sofa
    rug(68.5, 36.5, 77.5, 47.5, ("TurqC", "White", "TurqC"), "Gold")
    sofa(63.0, 36.0, 67.8, 47.0, "E", "Velvet", "Linen", ("Coral", "Yellow", "PinkB"))
    C(71.0, 41.0, 0.22, 1.6, 0.4, "Gold", G_P, 8); C(71.0, 41.0, 1.6, 2.0, 2.0, "Marble", G_P, 14)
    COL(69.0, 39.0, 0.12, 73.0, 43.0, 2.0, "CoffeeTable", G_P)
    vase(71.0, 41.0, 2.0, "Coral")
    # bar along the east window wall
    B(80.0, 40.0, 0.12, 82.8, 52.0, 3.8, "TurqDark", G_P); B(79.6, 39.8, 3.8, 83.0, 52.2, 4.2, "Marble", G_P)
    COL(79.6, 39.8, 0.12, 83.0, 52.2, 4.2, "Bar", G_P)
    for k in range(4):
        B(79.94, 40.4 + k * 2.9, 0.5, 80.0, 42.9 + k * 2.9, 3.4, "Turq", G_P)
    for yy in (42.0, 46.0, 50.0):
        stool(78.4, yy, "VelvetPink")
    # bottles / glasses on the bar, little grill
    for k, m in enumerate(("Teal", "Pink", "Gold", "Coral", "Purple", "Green")):
        C(82.0, 40.6 + k * 0.7, 4.2, 5.6 + (k % 2) * 0.5, 0.22, m, G_P, 6)
    K.sc.dz = 4.2
    K.kettle_grill(81.4, 48.6, 0.45, "Pink", True, True, 61, 2, G_P)
    K.sc.dz = 0.0
    # neon sign above the bar (on the north wall corner)
    egg_chair(66.0, 51.0)
    # big plants
    for (px, py, s) in ((63.8, 34.5, 1.1), (82.0, 34.5, 1.0), (63.8, 54.0, 1.2), (72.0, 54.0, 1.0), (82.0, 54.0, 1.1)):
        plant(px, py, s, "TurqB" if px < 70 else "Coral")
    # framed grill art + heart on the partition wall
    picture("y", 62.0, 1, 40.0, 46.0, 5.0, 10.0, "grill")
    heart(62.66, 43.0, 11.2, 0.12, "E", "NeonPink")
    for xx in (68.0, 78.0):
        ceiling_lamp(xx, 45.0, "LampSoft", "Gold", 1.8)
    TARGETS["lounge"] = (73.0, 48.0, 0.12)
    TARGETS["lounge bar"] = (76.0, 46.0, 0.12)


# ------------------------------------------------------------------ window view (scenery: the district from the 8th floor)
def view():
    """Lighter backdrop seen from the windows: ground far below, roads, block houses, trees and the turquoise tower walls.
    Scenery only (no collision, no queries, no shadows in Studio)."""
    G = "View"
    zg = -48.0
    B(-220, -220, zg - 2, W + 220, D + 220, zg, "Grass", G)
    for (x0, y0, x1, y1) in ((-220, -60, W + 220, -36), (-220, D + 60, W + 220, D + 84), (-80, -220, -56, D + 220), (W + 56, -220, W + 80, D + 220)):
        B(x0, y0, zg, x1, y1, zg + 0.3, "Asphalt", G)
    r = random.Random(77)
    cols = ("HouseBlue", "HouseRed", "HouseYellow", "HouseGreen", "HousePink", "HouseOrange", "HousePurple", "HouseTeal")
    roofs = ("RoofRed", "RoofGrey", "RoofBrown")
    for k in range(34):
        while True:
            x, y = r.uniform(-200, W + 200), r.uniform(-200, D + 200)
            if not (-30 < x < W + 30 and -30 < y < D + 30) and not any(a - 8 < x < b + 8 for (a, b) in ((-80, -56), (W + 56, W + 80))) \
                    and not any(a - 8 < y < b + 8 for (a, b) in ((-60, -36), (D + 60, D + 84))):
                break
        w, d, h = r.uniform(18, 30), r.uniform(14, 24), r.uniform(12, 22)
        B(x - w / 2, y - d / 2, zg, x + w / 2, y + d / 2, zg + h, r.choice(cols), G)
        sc.pyramid_roof(x - w / 2 - 1, y - d / 2 - 1, x + w / 2 + 1, y + d / 2 + 1, zg + h, zg + h + 7, r.choice(roofs), G)
    for k in range(60):
        x, y = r.uniform(-210, W + 210), r.uniform(-210, D + 210)
        if -40 < x < W + 40 and -40 < y < D + 40: continue
        B(x - 0.8, y - 0.8, zg, x + 0.8, y + 0.8, zg + 7, "Trunk", G)
        ball(x, y, zg + 10, 5.0, r.choice(("Leaf", "LeafB", "LeafC")), G, seg=8, rings=4)
    # the tower's own facade just below the flat, so a glance down looks right
    B(-1.0, -1.0, zg, W + 1.0, D + 1.0, -1.02, "Turq", G)
    for k in range(6):
        z = zg + 4 + k * 7.0
        B(-1.4, -1.4, z, W + 1.4, D + 1.4, z + 0.5, "White", G)


def kitchen_details():
    """Small kitchen props: backsplash, pots, utensils, knife block, cutting board, toaster, kettle, dish rack, spices, oven, herbs, bottles, clock, bin."""
    # backsplash tiles on the east wall between counter and wall cabinet (y 10..22)
    for i in range(12):
        for j in range(3):
            B(83.38, 10.0 + i, 3.72 + j * 1.2, 83.5, 11.0 + i - 0.04, 4.88 + j * 1.2, "TileT" if (i + j) % 2 else "TileW", G_P)
    # pot with lid and a frying pan on the hob
    C(82.0, 12.0, 3.8, 4.9, 0.6, "Steel", G_P, 12); C(82.0, 12.0, 4.9, 5.0, 0.64, "Chrome", G_P, 12); C(82.0, 12.0, 5.0, 5.25, 0.12, "Black", G_P, 6)
    for dy in (-0.75, 0.75):
        B(81.9, 12.0 + dy - 0.1, 4.5, 82.1, 12.0 + dy + 0.1, 4.7, "Black", G_P)
    C(82.0, 14.0, 3.8, 4.0, 0.65, "Black", G_P, 12); beam((81.4, 14.0, 3.95), (79.9, 14.0, 4.05), 0.18, "Black", G_P)
    C(82.0, 14.0, 4.0, 4.06, 0.3, "FireY", G_P, 8)          # fried egg
    C(82.0, 14.0, 4.0, 4.04, 0.52, "White", G_P, 10)
    # utensil rail with hanging tools under the wall cabinet
    B(83.25, 16.4, 6.6, 83.4, 21.6, 6.75, "Gold", G_P)
    for k, (kind, m) in enumerate((("spatula", "Black"), ("tongs", "Steel"), ("ladle", "Steel"), ("whisk", "Chrome"), ("spatula", "Coral"))):
        y = 17.0 + k * 1.05
        B(83.2, y - 0.05, 5.0, 83.3, y + 0.05, 6.6, m, G_P)
        if kind == "spatula": B(83.18, y - 0.3, 4.2, 83.3, y + 0.3, 5.0, m, G_P)
        elif kind == "ladle": ball(83.0, y, 4.8, 0.32, m, G_P, lat0=-90, lat1=0, seg=8, rings=3)
        elif kind == "whisk": ball(83.1, y, 4.7, 0.3, m, G_P, seg=6, rings=3, rz=0.5)
        else: B(83.18, y + 0.12, 4.2, 83.3, y + 0.22, 5.0, m, G_P)
    # knife block + cutting board with vegetables
    B(81.2, 19.0, 3.7, 82.2, 20.0, 5.0, "WoodMid", G_P)
    for k in range(3):
        B(81.35 + k * 0.3, 19.3, 5.0, 81.55 + k * 0.3, 19.7, 5.6, "Black", G_P)
    B(80.6, 5.6, 3.7, 82.4, 8.6, 3.85, "WoodLight", G_P)
    for k in range(3):
        ball(81.0 + k * 0.6, 6.2, 4.1, 0.28, "Red", G_P, seg=6, rings=3)
    for k in range(4):
        C(81.0 + k * 0.42, 7.6, 3.85, 3.95, 0.18, "Lettuce", G_P, 6)
    B(80.9, 8.0, 3.85, 82.0, 8.15, 3.95, "Chrome", G_P); B(82.0, 7.98, 3.85, 82.4, 8.17, 4.0, "Black", G_P)
    # oven door in the east counter front + towel on the handle
    B(80.36, 11.0, 0.6, 80.44, 15.0, 3.0, "Black", G_P)
    B(80.32, 11.4, 1.0, 80.37, 14.6, 2.4, "Screen", G_P)
    B(80.1, 11.3, 2.55, 80.32, 14.7, 2.75, "Chrome", G_P)
    B(80.02, 12.4, 1.4, 80.1, 13.6, 2.8, "Coral", G_P)
    # spice shelf + toaster at the west end of the south counter
    B(56.9, 0.5, 6.0, 59.7, 1.3, 6.15, "WoodLight", G_P)
    for k, m in enumerate(("Red", "Yellow", "Green", "Orange", "Brown", "White")):
        C(57.3 + k * 0.45, 0.9, 6.15, 6.85, 0.18, "Glass", "Glass", 6); C(57.3 + k * 0.45, 0.9, 6.15, 6.6, 0.15, m, G_P, 6)
        C(57.3 + k * 0.45, 0.9, 6.85, 6.95, 0.2, "Gold", G_P, 6)
    B(57.6, 1.4, 3.7, 59.2, 2.6, 4.9, "Chrome", G_P)
    for x in (58.0, 58.7):
        B(x, 1.6, 4.9, x + 0.4, 2.4, 4.92, "Black", G_P); B(x + 0.05, 1.7, 4.92, x + 0.35, 2.3, 5.3, "Bun", G_P)
    # kettle at the east end of the south counter
    C(81.0, 2.0, 3.7, 5.0, 0.6, "Coral", G_P, 10); C(81.0, 2.0, 5.0, 5.2, 0.35, "White", G_P, 8)
    beam((80.45, 2.0, 4.4), (79.9, 2.0, 5.0), 0.16, "Coral", G_P)
    B(81.5, 1.92, 4.0, 81.85, 2.08, 5.1, "White", G_P)
    # dish rack with plates next to the sink
    B(66.4, 1.0, 3.7, 69.2, 3.0, 3.85, "Chrome", G_P)
    for k in range(5):
        C(66.9 + k * 0.5, 2.0, 3.85, 4.0, 0.08, "Chrome", G_P, 4)
        B(66.75 + k * 0.5, 1.2, 3.85, 66.85 + k * 0.5, 2.8, 5.3, ("White", "TurqC", "White", "PinkB", "White")[k], G_P)
    # herbs on the counter under the second window
    for k, x in enumerate((77.3, 78.5, 79.7)):
        C(x, 1.4, 3.7, 4.4, 0.4, ("TurqB", "Coral", "Yellow")[k], G_P, 8)
        for j in range(3):
            ball(x + (j - 1) * 0.2, 1.4, 4.7 + (j % 2) * 0.25, 0.3, "Leaf" if j % 2 else "LeafB", G_P, seg=6, rings=3)
    # sauces, salt and pepper on the island
    for (x, y, m, cap) in ((72.6, 12.4, "Ketchup", "White"), (72.6, 13.1, "Mustard", "Red")):
        C(x, y, 3.8, 4.9, 0.25, m, G_P, 8); C(x, y, 4.9, 5.2, 0.12, cap, G_P, 6)
    C(62.6, 18.6, 3.8, 4.4, 0.18, "White", G_P, 6); C(63.1, 18.6, 3.8, 4.4, 0.18, "Black", G_P, 6)
    # clock between the south windows, sink mat, pedal bin
    B(69.2, 0.5, 6.8, 70.8, 0.62, 8.4, "Gold", G_P); B(69.35, 0.62, 6.95, 70.65, 0.66, 8.25, "White", G_P)
    B(69.96, 0.66, 7.6, 70.04, 0.7, 8.1, "Black", G_P); B(70.0, 0.66, 7.56, 70.4, 0.7, 7.64, "Black", G_P)
    B(61.5, 4.2, 0.12, 66.5, 6.2, 0.18, "Coral", G_P)
    C(57.8, 5.0, 0.12, 2.6, 0.75, "Steel", G_P, 10); C(57.8, 5.0, 2.6, 2.8, 0.8, "Chrome", G_P, 10)
    COL(57.0, 4.2, 0.12, 58.6, 5.8, 2.8, "Bin", G_P)


def tub():
    """Square bath against the north wall with a real basin: shell walls, inner floor, water, rim, stepped backrest, faucet, caddy, feet."""
    x0, x1, y0, y1 = 36.0, 46.0, 48.0, 54.5
    t, zb, zt = 0.7, 0.75, 3.2
    # feet (gold, ball-and-paw) under the shell
    for (fx, fy) in ((x0 + 0.6, y0 + 0.6), (x1 - 0.6, y0 + 0.6), (x0 + 0.6, y1 - 0.6), (x1 - 0.6, y1 - 0.6)):
        C(fx, fy, 0.12, 0.42, 0.42, "Gold", G_P, 8); ball(fx, fy, 0.6, 0.32, "GoldB", G_P, seg=8, rings=3)
    # shell: bottom slab + four walls
    B(x0, y0, zb, x1, y1, zb + 0.45, "White", G_P)
    B(x0, y0, zb + 0.45, x1, y0 + t, zt, "White", G_P)
    B(x0, y1 - t, zb + 0.45, x1, y1, zt, "White", G_P)
    B(x0, y0 + t, zb + 0.45, x0 + t, y1 - t, zt, "White", G_P)
    B(x1 - t, y0 + t, zb + 0.45, x1, y1 - t, zt, "White", G_P)
    COL(x0, y0, 0.12, x1, y1, zt + 0.25, "Tub", G_P)
    # rim cap (marble, slightly wider)
    B(x0 - 0.12, y0 - 0.12, zt, x1 + 0.12, y0 + t + 0.05, zt + 0.25, "Marble", G_P)
    B(x0 - 0.12, y1 - t - 0.05, zt, x1 + 0.12, y1 + 0.02, zt + 0.25, "Marble", G_P)
    B(x0 - 0.12, y0 + t + 0.05, zt, x0 + t + 0.05, y1 - t - 0.05, zt + 0.25, "Marble", G_P)
    B(x1 - t - 0.05, y0 + t + 0.05, zt, x1 + 0.12, y1 - t - 0.05, zt + 0.25, "Marble", G_P)
    # front panel: three tiled inlays with gold trim
    for k in range(3):
        a = x0 + 0.5 + k * (x1 - x0 - 1.0) / 3
        b = a + (x1 - x0 - 1.0) / 3 - 0.3
        B(a, y0 - 0.06, zb + 0.6, b, y0, zt - 0.4, "TurqC", G_P)
        B(a - 0.12, y0 - 0.1, zt - 0.5, b + 0.12, y0, zt - 0.38, "Gold", G_P)
    # inside: stepped (sloped-looking) backrest at the west end, water, foam, duck
    for k in range(4):
        B(x0 + t + k * 0.4, y0 + t + 0.03, zb + 0.45, x0 + t + (k + 1) * 0.4, y1 - t - 0.03, zb + 0.45 + 0.55 * (4 - k), "White", G_P)
    B(x0 + t + 0.03, y0 + t + 0.03, zb + 0.45, x1 - t - 0.03, y1 - t - 0.03, 2.35, "Water", "Water")
    for (bx, by, r) in ((43.6, 50.0, 0.55), (44.2, 51.2, 0.45), (43.2, 52.3, 0.6), (44.4, 52.9, 0.4), (42.4, 50.6, 0.35), (42.9, 53.2, 0.38)):
        ball(bx, by, 2.35, r, "Foam", "Water", lat0=0, lat1=90, seg=8, rings=3)
    ball(40.6, 51.0, 2.55, 0.42, "Yellow", G_P, seg=8, rings=3, rz=0.32); ball(40.95, 51.0, 2.95, 0.26, "Yellow", G_P, seg=6, rings=3)
    B(41.18, 50.92, 2.9, 41.4, 51.08, 2.98, "Orange", G_P)
    # headrest pillow on the west rim
    B(x0 + 0.1, 50.0, zt + 0.25, x0 + 1.0, 52.5, zt + 0.95, "Linen", G_P)
    # faucet on the north rim: spout + hot/cold knobs
    beam((41.0, y1 - 0.35, zt + 0.25), (41.0, y1 - 0.35, zt + 1.6), 0.22, "Gold", G_P)
    beam((41.0, y1 - 0.35, zt + 1.6), (41.0, y1 - 1.3, zt + 1.6), 0.2, "Gold", G_P)
    beam((41.0, y1 - 1.3, zt + 1.6), (41.0, y1 - 1.3, zt + 1.25), 0.18, "Gold", G_P)
    for (kx, m) in ((40.0, "Red"), (42.0, "Blue")):
        C(kx, y1 - 0.35, zt + 0.25, zt + 0.7, 0.16, "Gold", G_P, 6); C(kx, y1 - 0.35, zt + 0.7, zt + 0.85, 0.28, m, G_P, 8)
    # bath caddy across the tub: candle, sponge, soap, little plant
    B(41.4, y0 - 0.05, zt + 0.25, 42.8, y1, zt + 0.45, "WoodLight", G_P)
    C(42.1, 49.4, zt + 0.45, zt + 0.95, 0.22, "White", G_P, 8); B(42.06, 49.36, zt + 0.95, 42.14, 49.44, zt + 1.15, "FireY", G_P)
    B(41.6, 50.4, zt + 0.45, 42.6, 51.1, zt + 0.8, "Yellow", G_P)
    B(41.7, 51.6, zt + 0.45, 42.5, 52.1, zt + 0.65, "PinkB", G_P)
    C(42.1, 53.0, zt + 0.45, zt + 0.85, 0.25, "Coral", G_P, 8); ball(42.1, 53.0, zt + 1.05, 0.3, "LeafB", G_P, seg=6, rings=3)
    # towel draped over the front rim + bath mat
    B(37.2, y0 - 0.2, zt - 1.6, 39.0, y0 - 0.13, zt + 0.3, "PinkB", G_P)
    B(37.2, y0 - 0.13, zt + 0.25, 39.0, y0 + 0.6, zt + 0.32, "PinkB", G_P)
    B(38.5, 46.0, 0.12, 43.5, 47.6, 0.2, "TurqC", G_P)


def egg_chair(cx, cy):
    """Hanging rattan egg chair: woven ribs + hoops, open front facing the room, cushions, chain to a ceiling mount."""
    G = G_P
    face = math.degrees(math.atan2(42.0 - cy, 73.0 - cx))   # opening looks at the coffee table
    open_half = 58.0
    z0, z1, R = 1.6, 8.2, 2.5
    prof = [k / 10.0 for k in range(11)]
    def rad(h): return max(0.25, R * math.sin(math.pi * (0.08 + 0.84 * h)) ** 0.85)
    def zz(h): return z0 + (z1 - z0) * h
    n = 18
    for i in range(n):
        a = i * 360.0 / n
        d = (a - face + 180.0) % 360.0 - 180.0
        top = 1.0 if abs(d) >= open_half else 0.45           # the front is cut low: a seat opening
        pts = [(cx + rad(h) * math.cos(math.radians(a)), cy + rad(h) * math.sin(math.radians(a)), zz(h)) for h in prof if h <= top + 1e-6]
        for p0, p1 in zip(pts[:-1], pts[1:]):
            beam(p0, p1, 0.16, "WoodMid" if i % 3 else "WoodLight", G)
    for h in (0.12, 0.25, 0.38, 0.52, 0.66, 0.8, 0.92):
        r = rad(h)
        if h <= 0.45:
            ring(cx, cy, r - 0.12, r + 0.04, zz(h) - 0.08, zz(h) + 0.08, "WoodLight", G, 20)
        else:
            ring(cx, cy, r - 0.12, r + 0.04, zz(h) - 0.08, zz(h) + 0.08, "WoodLight", G, 20, face + open_half, face + 360.0 - open_half)
    # closed woven shell behind the ribs (so the back reads as a basket, not a cage)
    for k in range(10):
        h0, h1 = k / 10.0, (k + 1) / 10.0
        r = min(rad(h0), rad(h1)) - 0.1
        if r < 0.3: continue
        if h1 <= 0.45: ring(cx, cy, r - 0.08, r, zz(h0), zz(h1), "Plank" if k % 2 else "PlankC", G, 20)
        else: ring(cx, cy, r - 0.08, r, zz(h0), zz(h1), "Plank" if k % 2 else "PlankC", G, 20, face + open_half + 4, face + 360.0 - open_half - 4)
    C(cx, cy, z0 - 0.05, zz(0.1), rad(0.05), "Plank", G, 16)
    ring(cx, cy, rad(0.45) - 0.18, rad(0.45) + 0.1, zz(0.45) - 0.12, zz(0.45) + 0.12, "WoodMid", G, 20)
    ring(cx, cy, 0.1, 0.5, z1 - 0.1, z1 + 0.25, "WoodMid", G, 12)
    # cushions: round seat, back cushion, two little pillows
    C(cx, cy, zz(0.36), zz(0.36) + 0.6, rad(0.36) - 0.2, "VelvetPink", G, 16)
    fx, fy = math.cos(math.radians(face)), math.sin(math.radians(face))
    ball(cx - 1.2 * fx, cy - 1.2 * fy, zz(0.6), 1.4, "VelvetPink", G, seg=10, rings=4, sx=0.55, sy=0.55)
    for s_ in (-1, 1):
        a = math.radians(face + 90 * s_)
        ball(cx + 0.9 * math.cos(a) - 0.4 * fx, cy + 0.9 * math.sin(a) - 0.4 * fy, zz(0.5), 0.5, "TurqC" if s_ > 0 else "White", G, seg=8, rings=3)
    # chain to the ceiling + mount plate + hook
    k = 0; z = z1 + 0.25
    while z < CH - 0.6:
        if k % 2: B(cx - 0.05, cy - 0.18, z, cx + 0.05, cy + 0.18, z + 0.5, "Gold", G)
        else: B(cx - 0.18, cy - 0.05, z, cx + 0.18, cy + 0.05, z + 0.5, "Gold", G)
        z += 0.45; k += 1
    C(cx, cy, CH - 0.6, CH - 0.25, 0.22, "Gold", G, 8)
    C(cx, cy, CH - 0.25, CH - 0.02, 0.7, "GoldB", G, 12)
    COL(cx - R, cy - R, 0.12, cx + R, cy + R, 6.0, "SwingChair", G)
