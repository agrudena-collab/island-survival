

# ----------------------------------------------------------------------------------------------
# torso (tank top), pelvis, shorts, legs, shoes
# ----------------------------------------------------------------------------------------------
def plate_bm(outline, fit, layers, tile):
    """closed plate following a surface: layers=[(dD, sx, sh)], first layer = back; used as boolean cutter."""
    cx = sum(p[0] for p in outline) / len(outline)
    ch = sum(p[1] for p in outline) / len(outline)
    n = len(outline)
    P = []
    for dD, sx, sh in layers:
        for x, h in outline:
            xx, hh = cx + (x - cx) * sx, ch + (h - ch) * sh
            P.append(V((xx, fit(xx, hh) + dD, hh)))
    faces = []
    for i in range(len(layers) - 1):
        for k in range(n):
            faces.append([i * n + k, i * n + (k + 1) % n, (i + 1) * n + (k + 1) % n, (i + 1) * n + k])
    faces += cap_tris(P, list(range(n)))
    faces += cap_tris(P, list(range((len(layers) - 1) * n, len(layers) * n)))
    return solid_tiled(P, faces, tile)


def tfront(x, h):
    return front_at(TORSO, min(max(h, 2.30), TORSO_TOP), x)


def tback(x, h):
    return back_at(TORSO, min(max(h, 2.30), TORSO_TOP), x)


def wall_ring(pm, cid, side, pts_fh, width, out, embed, tile, meta=None):
    """closed rectangular ribbon around the torso side wall (X = side * w(h)/2): path in (F, H)."""
    n = len(pts_fh)
    P = []
    for i, (f, h) in enumerate(pts_fh):
        pf, ph_ = pts_fh[i - 1]
        nf, nh = pts_fh[(i + 1) % n]
        t = V((nf - pf, nh - ph_, 0)).normalized()
        nrm = V((-t.y, t.x, 0))
        for sgn in (1, -1):
            ff, hh = f + sgn * nrm.x * width / 2, h + sgn * nrm.y * width / 2
            wx = interp_row(TORSO, min(max(hh, 2.30), TORSO_TOP))[0] / 2.0
            P.append(V((side * (wx + out), -ff, hh)))
            P.append(V((side * (wx - embed), -ff, hh)))
    faces = []
    for i in range(n):
        a, b = i * 4, ((i + 1) % n) * 4
        faces += [[a, a + 2, b + 2, b], [a + 1, b + 1, b + 3, a + 3], [a, b, b + 1, a + 1], [a + 2, a + 3, b + 3, b + 2]]
    pm.solid(cid, P, faces, tile, meta)


# ---- UpperTorso: tank shell with front neckline and shallow back scoop, armhole rims -----------------
ut = PM("UpperTorso", JV["Waist"])
bm = loft_bm([row_ring(r) for r in UPPER_ROWS], sh_tank)
NECK_FRONT = [(-.90, 5.45), (-.90, 4.58), (-.75, 4.38), (.75, 4.38), (.90, 4.58), (.90, 5.45)]
cut_f = plate_bm(NECK_FRONT, tfront, [(+.045, 1.0, 1.0), (-.30, 1.0, 1.0)], "Skin")
bm = bm_boolean(bm, cut_f)
cut_f.free()
NECK_BACK = [(-.85, 5.45), (-.85, 5.05), (-.62, 4.80), (-.40, 4.72), (.40, 4.72), (.62, 4.80), (.85, 5.05), (.85, 5.45)]
cut_b = plate_bm(NECK_BACK, tback, [(-.045, 1.0, 1.0), (+.30, 1.0, 1.0)], "Skin")
bm = bm_boolean(bm, cut_b)
cut_b.free()
tl_ = bm.faces.layers.int.get("tile")
for f_ in bm.faces:                      # V2: neckline walls are the thin tank-edge band; only the floors stay skin (chest / back)
    if PAL[f_[tl_]][0] == "Skin":
        f_.normal_update()
        if abs(f_.normal.y) < 0.7:
            f_[tl_] = TILE["TankEdge"]
ut.append_bm("UT_tank_shell", bm, None, {"recipe": "8-row octagon loft to H5.15 (shoulder line), boolean notches: front neckline (half width .90, depth .045, skin floor) and back scoop; straps are the shell between the neckline and the arm (width .47) and continue over the shoulder to the back", "class": "v2"})
bm.free()

# ---- LowerTorso: lower tank, hem, pelvis shorts ----------------------------------------------------
lt = PM("LowerTorso", JV["Root"])
loft(lt, "LT_tank_lower", [row_ring(r) for r in LOWER_ROWS], sh_tank, meta={"recipe": "section 06 rows H2.30..2.85", "class": "prescribed"})
hem = []
for h, g in ((2.31, 0.0), (2.335, .035), (2.40, .035), (2.44, 0.0)):
    r = torso_row_at(h)
    hem.append(ring8(r[1] / 2 + g, r[2] - g, r[3] + g, r[4] + g * .5, 0, 0, h))
loft(lt, "LT_waist_hem", hem, sh_const("TankEdge"), meta={"recipe": "hem ring .035 proud, H2.30..2.44", "class": "prescribed"})
PA, PD = 1.50, .73
prings = [ring8(PA - .08, -PD + .08, PD - .08, .06, 0, 0, 2.065), ring8(PA, -PD, PD, .08, 0, 0, 2.145), ring8(PA, -PD, PD, .08, 0, 0, 2.355), ring8(PA - .06, -PD + .06, PD - .06, .06, 0, 0, 2.435)]
loft(lt, "LT_pelvis_shorts", prings, sh_shorts, band_tiles={2: "ShortsShadow"},
     meta={"recipe": "pelvis block W2.62 x D1.42 x H.37 (plan 2.64 x 1.46), top band = waistband", "class": "prescribed"})

# ---- legs: shorts (UpperLeg), knee + shin (LowerLeg), sneakers (Foot) -----------------------------------
LEGHW = lambda h: .71 + .05 * (h - 1.24) / 1.10       # half width of the shorts leg (taper 1.18 -> 1.28)
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    hip, knee, ank = JV[side + "Hip"], JV[side + "Knee"], JV[side + "Ankle"]
    cxl = s * .90
    ul = PM(side + "UpperLeg", hip)
    LD0, LD1 = -.725, .695
    rings = [ring8(.71 - .05, LD0 + .05, LD1 - .05, .06, cxl, 0, 1.24), ring8(.71, LD0, LD1, .06, cxl, 0, 1.29),
             ring8(.76, LD0, LD1, .06, cxl, 0, 2.29), ring8(.76 - .05, LD0 + .05, LD1 - .05, .06, cxl, 0, 2.34)]
    loft(ul, "UL_shorts_" + side, rings, sh_shorts, band_tiles={0: "ShortsShadow"},
         meta={"recipe": "tapered beveled box W1.18->1.28 x D1.42 x H1.10, bevel .06", "class": "prescribed"})
    hs = [1.34 + .94 * k / 6 for k in range(7)]
    srings = []
    for h in hs:
        xo = s * (.90 + LEGHW(h))
        srings.append([V((xo + s * .014, -(.03 - .075), h)), V((xo + s * .014, -(.03 + .075), h)), V((xo - s * .02, -(.03 + .075), h)), V((xo - s * .02, -(.03 - .075), h))])
    loft(ul, "UL_side_stripe_" + side, srings, sh_const("SideStripe"), meta={"recipe": "stripe .15 wide on the outer face, H1.34..2.28, proud .014", "class": "prescribed"})
    ll = PM(side + "LowerLeg", knee)
    secs = [(1.42, .98, .98, .09, -.98), (1.20, .95, .96, .09, -1.00), (1.00, .90, .92, .08, -1.03), (.66, .84, .86, .07, -1.04), (.62, .84, .86, .07, -1.10)]
    # logical X of the leg centre is s * (-x); D centre of the leg is -F = -.02
    rings = [ring8(w / 2, -.02 - d / 2, -.02 + d / 2, c, s * -x, 0, h) for h, w, d, c, x in secs]
    loft(ll, "LL_knee_shin_" + side, rings, sh_skin, meta={"recipe": "knee skin W.91 (H1.12..1.42) + shin tapering to .73 x .77, hidden .03 in the shoe", "class": "prescribed"})

    # V2_03 foot: tall sneaker authored unrotated, then ONE rotation of the whole foot set about the ankle (7 deg outward)
    th = s * 7.0
    ft = PM(side + "Foot", ank, xf=rot_xf(ank, th))
    cx = s * 1.04
    sole = [ring8(.60, -1.16, .64, .10, cx, 0, 0.0), ring8(.70, -1.26, .74, .10, cx, 0, .10), ring8(.70, -1.26, .74, .10, cx, 0, .26), ring8(.62, -1.18, .66, .10, cx, 0, .34)]
    loft(ft, "FT_sole_" + side, sole, sh_sole, band_tiles={0: "SoleShadow"}, meta={"recipe": "sole W1.40 x D2.00 x H.34, bevel .10, outsole band", "class": "v2"})

    def ring_xh(f, w, h0, h1, c, cx=cx):
        a = w / 2
        pts = [(-a + c, h0), (a - c, h0), (a, h0 + c), (a, h1 - c), (a - c, h1), (-a + c, h1), (-a, h1 - c), (-a, h0 + c)]
        return [V((cx + x, -f, h)) for x, h in pts]

    def top_at(f):
        for (f0, t0, _, _), (f1, t1, _, _) in zip(UP, UP[1:]):
            if f0 <= f <= f1:
                return t0 + (t1 - t0) * (f - f0) / (f1 - f0)
        return UP[-1][1]
    UP = [(-.66, .62, .96, .14), (-.52, .78, 1.20, .16), (-.15, .86, 1.30, .16), (.28, .84, 1.32, .16), (.58, .72, 1.32, .15), (.80, .62, 1.28, .13)]
    loft(ft, "FT_upper_" + side, [ring_xh(f, w, .30, top, c) for f, top, w, c in UP], sh_shoe, meta={"recipe": "upper lofted along F: high ankle collar (H1.04) falling to the toe, W1.30", "class": "v2"})
    CAP = [(.80, .52, 1.30, .14), (1.02, .54, 1.26, .16), (1.16, .46, 1.10, .14), (1.23, .38, .90, .12), (1.25, .34, .74, .02)]
    loft(ft, "FT_toe_cap_" + side, [ring_xh(f, w, .30, top, c) for f, top, w, c in CAP], sh_const("Sole"), meta={"recipe": "ONE rounded white toe cap wrapping the toe from the sole upwards", "class": "v2"})
    patch_box(ft, "FT_toe_notch_" + side, cx, 1.262, .17, .55, .012, .12, "ShoeBlack", meta={"recipe": "dark centre on the sole front face", "class": "v2"})

    def tongue_top(f):
        return .96 + (.78 - .96) * (f - .26) / (.60 - .26)
    prism_poly(ft, "FT_tongue_" + side, [Bl(cx - .30, f, h) for f, h in ((.26, .96), (.60, .78), (.60, .66), (.26, .84))], V((.60, 0, 0)), sh_const("ShoeGray"), {"recipe": "tongue wedge on the instep in front of the shin", "class": "v2"})
    for k, f in enumerate((.37, .50)):
        f0, f1 = f - .035, f + .035
        prism_poly(ft, "FT_lace_%d_%s" % (k + 1, side), [Bl(cx - .31, ff, hh) for ff, hh in ((f0, tongue_top(f0) - .02), (f1, tongue_top(f1) - .02), (f1, tongue_top(f1) + .035), (f0, tongue_top(f0) + .035))],
                   V((.62, 0, 0)), sh_const("Sole"), {"recipe": "flat lace band on the tongue", "class": "v2"})
    LOOPP = [(-.09, 0), (-.045, 0), (-.045, .07), (.045, .07), (.045, 0), (.09, 0), (.09, .14), (-.09, .14)]
    prism_xh(ft, "FT_orange_loop_" + side, [(cx + x, .91 + h) for x, h in LOOPP], .26, .31, sh_const("ShoeOrange"), {"recipe": "orange loop at the TOP of the tongue, in front of the shin", "class": "v2"})
    trim = []
    for f in (-.35, 0.0, .30, .55):
        xi, xo = cx + s * .62, cx + s * .682
        trim.append([V((xi, -f, .50)), V((xo, -f, .50)), V((xo, -f, .64)), V((xi, -f, .64))])
    loft(ft, "FT_orange_side_trim_" + side, trim, sh_const("ShoeOrange"), meta={"recipe": "orange side accent on the outer side of the upper", "class": "v2"})
