

# ----------------------------------------------------------------------------------------------
# FishingRod (sections 20..23) and Bucket (sections 24, 25): separate rigid props
# ----------------------------------------------------------------------------------------------
ROD_O = V((2.20, -.65, .10))
BUCKET_O = V((3.00, .10, 0.0))
rod = PM("FishingRod", ROD_O)
CORK_MARKS = [(0, .30, .035), (2.5, .62, .03), (4.1, 1.05, .04), (1.2, 1.40, .028), (5.4, 1.72, .045), (3.3, 1.95, .03), (0.7, 2.08, .025)]


def cork_tile(n, c):
    ang = math.atan2(n.y, n.x)
    sec = int(((ang + math.pi) / (2 * math.pi)) * 12) % 12
    return "CORK_LIGHT" if sec in (2, 6, 10) else "CORK"


lathe(rod, "ROD_plug", [(.095, .10), (.095, .16)], 2.20, -.65, 10, sh_const("ROD"), meta_=meta("bottom plug H.10..0.16 dia .19", "prescribed"))
lathe(rod, "ROD_cork", [(.09, .12), (.075, 2.20)], 2.20, -.65, 12, cork_tile, meta_=meta("cork grip H.12..2.20 dia .18 -> .15, 3 light facets", "observed+prescribed"))
for i, (ang, h, sz) in enumerate(CORK_MARKS):
    r_ = .09 + (.075 - .09) * (h - .12) / 2.08
    box_c(rod, "ROD_cork_mark_%d" % i, (2.20 + (r_ + .002) * math.cos(ang), -.65 + (r_ + .002) * math.sin(ang), h), (sz, sz, sz), sh_const("CORK_DARK"), meta_=meta("cork mark", "inferred"))
lathe(rod, "ROD_ferrule", [(.085, 2.16), (.085, 2.23)], 2.20, -.65, 10, sh_const("ROD"), meta_=meta("black upper collar H2.16..2.23 dia .17", "prescribed"))
shaft = [p for i, p in enumerate(ROD_DENSE) if p.z >= 2.20 - 1e-6 and (i % 2 == 0 or i == len(ROD_DENSE) - 1)]
sweep(rod, "ROD_shaft", shaft, [rod_diam(p.z) for p in shaft], [rod_diam(p.z) for p in shaft], sh_rod, up=V((0, -1, 0)), n=8,
      meta_=meta("rod shaft along the smoothed axis A1..A7, 8-sided, closed tip", "observed+prescribed"))
for hh in (4.20, 5.20, 6.35):
    pts = [rod_axis(hh - .035), rod_axis(hh), rod_axis(hh + .035)]
    sweep(rod, "ROD_wrap_%.2f" % hh, pts, rod_diam(hh) + .025, rod_diam(hh) + .025, sh_const("ROD_LIGHT"), up=V((0, -1, 0)), n=8,
          meta_=meta("black wrap W.07 at H%.2f, dia rod+.025" % hh, "prescribed"))

GUIDES = [(4.20, .10, .075), (5.20, .09, .065), (6.35, .08, .055), (7.23, .07, .045)]
GUIDE_C = []
for hh, off, ro in GUIDES:
    c = rod_axis(hh) + V((off, 0, 0))
    GUIDE_C.append(c)
    T = rod_tangent(hh)
    Bv = V((1, 0, 0)) - T * T.dot(V((1, 0, 0)))
    Bv.normalize()
    Nv = T.cross(Bv).normalized()
    secs = []
    for k in range(9):
        ph = 2 * math.pi * k / 9
        e = Bv * math.cos(ph) + Nv * math.sin(ph)
        secs.append([c + e * ro + T * .01, c + e * ro - T * .01, c + e * (ro - .018) - T * .01, c + e * (ro - .018) + T * .01])
    loop_solid(rod, "ROD_guide_%.2f" % hh, secs, sh_const("ROD"), meta("guide ring R%.3f rim .018, centre offset +X %.2f, axis parallel to the rod tangent" % (ro, off), "prescribed"))
    r_rod = (rod_diam(hh) + .025) / 2 if hh < 7 else rod_diam(hh) / 2
    x0 = rod_axis(hh).x + r_rod * .5
    x1 = c.x - ro + .02
    box_c(rod, "ROD_guide_foot_%.2f" % hh, ((x0 + x1) / 2, -.65, hh), (max(x1 - x0, .02), .035, .035), sh_const("ROD"), meta_=meta("guide foot .035 x .035", "prescribed"))

# reel (section 22)
RC = V((2.95, -.65, 2.84))
lathe(rod, "REEL_spool", [(.20, 2.75), (.20, 2.83), (.192, 2.84), (.20, 2.85), (.20, 2.95), (.192, 2.96), (.20, 2.97), (.20, 3.07)], 2.95, -.65, 12,
      lambda n, c: "GOLD_LIGHT" if n.z > .9 else "GOLD", meta_=meta("gold spool R.20 H.32 with two shallow grooves", "observed+prescribed"))
lathe(rod, "REEL_flange_top", [(.24, 3.0625), (.24, 3.1175)], 2.95, -.65, 12, lambda n, c: "REEL_LIGHT" if n.z > .9 else "REEL", meta_=meta("upper flange R.24 H.055 at H3.09", "prescribed"))
lathe(rod, "REEL_flange_bottom", [(.24, 2.7025), (.24, 2.7575)], 2.95, -.65, 12, sh_const("REEL"), meta_=meta("lower flange R.24 H.055 at H2.73", "prescribed"))
lathe(rod, "REEL_cap", [(.09, 3.12), (.09, 3.18)], 2.95, -.65, 10, sh_const("REEL_LIGHT"), meta_=meta("top cap R.09 H.06 at H3.15", "prescribed"))
box_c(rod, "REEL_body", (2.90, -.65, 2.58), (.36, .32, .31), lambda n, c: "REEL_LIGHT" if n.z > .5 else "REEL", ch=.06, meta_=meta("reel housing .36 x .32 x .31, bevel .06", "observed+prescribed"))
box_c(rod, "REEL_foot", (2.305, -.65, 2.735), (.10, .13, .37), sh_const("REEL"), ch=.02, meta_=meta("mounting foot .10 x .13 x .37 along the rod", "prescribed"))
sweep(rod, "REEL_arm", catmull([V((2.23, -.65, 2.78)), V((2.61, -.65, 2.46)), V((2.90, -.65, 2.58))], 4), .10, .10, sh_const("REEL"), up=V((0, -1, 0)),
      meta_=meta("curved support through (2.61,-.65,2.46), section .10 x .10", "prescribed"))
sweep(rod, "REEL_crank_a", [V((3.06, -.65, 2.57)), V((3.20, -.74, 2.51))], .055, .055, sh_const("REEL"), up=V((0, 0, 1)), meta_=meta("crank segment 1", "prescribed"))
sweep(rod, "REEL_crank_b", [V((3.20, -.74, 2.51)), V((3.16, -.84, 2.35))], .055, .055, sh_const("REEL"), up=V((1, 0, 0)), meta_=meta("crank segment 2", "prescribed"))
box_c(rod, "REEL_crank_knob", (3.16, -.84, 2.35), (.13, .16, .16), sh_const("REEL"), ch=.03, meta_=meta("crank knob .13 x .16 x .16", "prescribed"))
bail = [V((2.95, -.65 - .28 * math.sin(ph), 2.97 + .19 * math.cos(ph))) for ph in [math.pi * i / 8 for i in range(9)]]
sweep(rod, "REEL_bail", bail, .035, .035, sh_const("WIRE"), up=V((1, 0, 0)), n=6, meta_=meta("open line-roller wire arc, dia .035, R.28, H2.78..3.16", "prescribed"))
for sx in (-1, 1):
    box_c(rod, "REEL_bail_post_%d" % sx, (2.95 + sx * .06, -.65, 2.775), (.03, .03, .05), sh_const("REEL"), meta_=meta("bail support post", "prescribed"))

# float (section 23) + fishing line
FLOAT_XD = (3.03, -.65)
lathe(rod, "FLOAT_body", [(.0225, 5.38), (.09, 5.45), (.15, 5.62), (.15, 5.68), (.125, 5.81), (.06, 5.91), (.02, 5.96)], FLOAT_XD[0], FLOAT_XD[1], 12,
      sh_const("FLOAT_RED"), band_tiles={3: "FLOAT_WHITE"}, meta_=meta("float: 12-gon revolution, max dia .30, red/white/red", "observed+prescribed"))
lathe(rod, "FLOAT_stem", [(.0175, 5.22), (.0175, 5.38)], FLOAT_XD[0], FLOAT_XD[1], 6, sh_const("LINE"), meta_=meta("lower stem H5.22..5.38 dia .035", "prescribed"))
lathe(rod, "FLOAT_antenna", [(.0175, 5.96), (.0175, 6.08)], FLOAT_XD[0], FLOAT_XD[1], 6, sh_const("FLOAT_RED"), meta_=meta("upper antenna H5.96..6.08 dia .035", "prescribed"))
LINE_W = .012
LINE_UP = [V((2.95, -.65, 3.15)), V((2.95, -.65, 3.98)), GUIDE_C[0], GUIDE_C[1], GUIDE_C[2], GUIDE_C[3]]
LINE_DN = [GUIDE_C[3], V((FLOAT_XD[0], -.65, 6.08)), V((FLOAT_XD[0], -.65, 5.22)), V((FLOAT_XD[0], -.65, 3.30))]
for nm, pts in (("up", LINE_UP), ("down", LINE_DN)):
    for i in range(len(pts) - 1):
        sweep(rod, "LINE_%s_%d" % (nm, i), [pts[i], pts[i + 1]], LINE_W, LINE_W, sh_const("LINE"), up=V((1, 0, 0)), n=4, meta_=meta("fishing line segment dia .012", "prescribed"))

# ---------------------------------------------------------------- bucket
bk = PM("Bucket", BUCKET_O)
BK_PROFILE = [(.44, 0.0), (.46, .02), (.48, .08), (.56, 1.08), (.58, 1.10), (.58, 1.14), (.55, 1.16), (.49, 1.16), (.50, 1.08), (.40, .08)]


def bucket_tile(n, c):
    if n.z < -.5 or (n.z > .5 and abs(c.z - .08) < .002):
        return "BUCKET_DARK"
    if n.z > .5:
        return "BUCKET_LIGHT"
    if n.y < -.65:
        return "BUCKET_LIGHT"
    return "BUCKET"


lathe(bk, "BK_shell", BK_PROFILE, 3.00, .10, 12, bucket_tile,
      band_tiles={0: "BUCKET_DARK", 1: "BUCKET_DARK", 3: "BUCKET_LIGHT", 4: "BUCKET_LIGHT", 5: "BUCKET_LIGHT", 6: "BUCKET_LIGHT", 7: "BUCKET_DARK", 8: "BUCKET_DARK"},
      meta_=meta("hollow bucket, 12-gon, outer R.46->.56 (H.02..1.08), inner R.40..50, floor .08 thick, rolled rim H1.08..1.16 R.58", "observed+prescribed"))
for sx in (-1, 1):
    ex = 3.00 + sx * .55
    box_c(bk, "BK_ear_%d" % sx, (ex, .10, .98), (.09, .10, .14), sh_const("BUCKET_DARK"), ch=.015, meta_=meta("handle ear .09 x .10 x .14", "prescribed"))
    sweep(bk, "BK_axle_%d" % sx, [V((ex - .06, .10, .98)), V((ex + .06, .10, .98))], .045, .045, sh_const("SILVER"), up=V((0, 0, 1)), n=8, meta_=meta("axle dia .045", "prescribed"))
hp = [V((3.00 + .55 * math.cos(th), .10 - .58 * math.sin(th), .98 - .33 * math.sin(th))) for th in [math.pi * i / 14 for i in range(15)]]
sweep(bk, "BK_wire_handle", hp, .036, .036, sh_const("WIRE"), up=V((0, 0, 1)), n=6, meta_=meta("wire handle through the ears: X=3+.55cos, D=.10-.58 sin, H=.98-.33 sin", "prescribed"))
