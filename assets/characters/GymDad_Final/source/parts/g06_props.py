

# ----------------------------------------------------------------------------------------------
# V2 props: heavy dumbbell (right hand) and a compact soft sports bag (left hand) - separate rigid meshes
# ----------------------------------------------------------------------------------------------
db = PM("Dumbbell", DUMBBELL_C, geo="Dumbbell_Geo")
DX, DY, DZ = DUMBBELL_C.x, DUMBBELL_C.y, DUMBBELL_C.z
GRIP_HALF = float(os.environ.get("GYM_GRIPHALF", ".58"))
cyl_x(db, "DB_grip", DX, DY, DZ, 2 * GRIP_HALF + .04, .115, 12, sh_const("Grip"), meta={"recipe": "grip L1.08 d.23, 12 sides, axis X (visible .13 beyond the fist)", "class": "v2"})
cyl_x(db, "DB_axle", DX, DY, DZ, 3.10, .07, 12, sh_const("DumbbellDark"), meta={"recipe": "hidden axle through both packs", "class": "v2"})


def sh_plate_face(n, c):
    if abs(n.x) > .8:
        return "Dumbbell"
    if abs(n.x) < .2:
        return "Dumbbell"
    return "DumbbellLight"


# V2 plate packs: contiguous (no gaps), thicker (pack thickness / diameter = .53), stepped radii .98 / .88 / .72
PLATES = [(.34, .98), (.28, .88), (.24, .72)]
for sx, nm in ((-1, "Outer"), (1, "Inner")):
    cyl_x(db, "DB_%s_collar" % nm, DX + sx * (GRIP_HALF + .03), DY, DZ, .06, .22, 12, sh_const("DumbbellDark"), meta={"recipe": "inner stop", "class": "v2"})
    off = GRIP_HALF + .06
    for i, (t, r) in enumerate(PLATES):
        cyl_x(db, "DB_%s_plate_%d" % (nm, i + 1), DX + sx * (off + t / 2), DY, DZ, t, r, 20, sh_plate_face, ch=.05,
              meta={"recipe": "plate r%.2f t%.2f, 20 sides, bevel .05, touching the neighbours" % (r, t), "class": "v2"})
        off += t
    cyl_x(db, "DB_%s_cap" % nm, DX + sx * (off + .03), DY, DZ, .06, .28, 12, sh_const("DumbbellDark"), meta={"recipe": "end cap", "class": "v2"})
    cyl_x(db, "DB_%s_boss" % nm, DX + sx * (off + .075), DY, DZ, .03, .10, 12, sh_const("DumbbellLight"), meta={"recipe": "central boss", "class": "v2"})

bg = PM("GymBag", BAG_C, geo="GymBag_Geo")
BX = BAG_X


def sh_bag(n, c):
    if n.z < -0.5:
        return "BagDark"
    if abs(c.x - BX) > .48 and c.z < 1.30:
        return "BagLight" if n.z > .6 else "BagOrange"
    return "BagEdge" if n.z > .6 else "BagDark"


# soft duffel: wide base, rounded sides, rounded top; orange ends, dark middle (as on the original)
BAGROWS = [(.28, .66, .42, .14), (.46, .80, .51, .18), (.95, .82, .52, .20), (1.20, .74, .48, .20), (1.34, .56, .36, .14)]
loft(bg, "BG_body", [ring8(a, -d, d, c, BX, 0, h) for h, a, d, c in BAGROWS], sh_bag, meta={"recipe": "soft body: 5 rounded sections (H.28..1.34, W1.52 max, D1.02 max); ends orange, middle dark", "class": "v2"})
solid_box(bg, "BG_zipper_track", BX - .30, BX + .30, -.02, .02, 1.32, 1.365, sh_const("Zipper"), {"recipe": "zipper track on the top", "class": "v2"})
solid_box(bg, "BG_zipper_pull", BX + .26, BX + .38, -.03, .03, 1.34, 1.395, sh_const("Steel"), {"recipe": "zipper pull", "class": "v2"})
HPATH = catmull([V((2.26, 0, 1.33)), V((2.30, 0, 1.68)), V((2.45, 0, 2.05)), V((2.65, 0, 2.05)), V((2.86, 0, 1.33))], 4)


def smooth01(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


for sf, nm in ((1, "front"), (-1, "back")):
    for ax in (2.26, 2.86):
        patch_box(bg, "BG_anchor_%s_%.2f" % (nm, ax), ax, sf * .25, 1.32, .17, .10, .14, "BagEdge", embed=.05, meta={"recipe": "handle anchor", "class": "v2"})
    rings = []
    for k, p in enumerate(HPATH):
        tg = (HPATH[min(k + 1, len(HPATH) - 1)] - HPATH[max(k - 1, 0)])
        tg = V((tg.x, 0, tg.z)).normalized()
        nx, nz = -tg.z, tg.x
        fabs = .25 - .13 * smooth01((p.z - 1.45) / .55)
        f = sf * fabs
        xl, zl = p.x + nx * .0475, p.z + nz * .0475
        xr, zr = p.x - nx * .0475, p.z - nz * .0475
        rings.append([Bl(xl, f - .0375, zl), Bl(xr, f - .0375, zr), Bl(xr, f + .0375, zr), Bl(xl, f + .0375, zl)])
    loft(bg, "BG_handle_" + nm, rings, sh_const("BagDark"), meta={"recipe": "handle ribbon .095 x .075; F converges from +-.25 to +-.12 inside the left fist", "class": "v2"})
