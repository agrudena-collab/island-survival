

# ----------------------------------------------------------------------------------------------
# prescribed numeric tables (master prompt sections 08..22, 28)
# ----------------------------------------------------------------------------------------------
UT_ROWS = [(2.20, 2.72, -.86, .56, .13), (2.65, 2.92, -1.00, .64, .17), (3.10, 2.95, -1.05, .68, .17),
           (3.65, 2.88, -.95, .64, .16), (4.15, 2.87, -.74, .58, .12), (4.46, 2.65, -.60, .51, .11), (4.72, 2.12, -.49, .45, .09)]
LT_ROWS = [(1.82, 2.30, -.70, .48, .12), (2.10, 2.55, -.80, .56, .14), (2.34, 2.66, -.84, .58, .14)]
APRON_ROWS = [(1.10, 2.78, -.83, .06), (1.70, 2.91, -.98, .07), (2.30, 2.95, -1.06, .07), (2.63, 2.91, -1.08, .07),
              (3.12, 2.83, -1.12, .07), (3.62, 2.48, -.99, .06), (4.03, 2.10, -.83, .04)]
HEAD_ROWS = [(4.74, 1.50, -.62, .60, .13), (4.98, 1.74, -.74, .76, .14), (5.12, 1.86, -.78, .76, .14), (5.40, 1.88, -.74, .76, .14),
             (6.28, 1.88, -.74, .76, .12), (6.40, 1.62, -.62, .64, .12)]
STAINS = [(-0.52, 3.29, 0.43, 0.28), (0.54, 3.14, 0.48, 0.48), (1.12, 3.48, 0.35, 0.43), (0.95, 2.91, 0.40, 0.23), (-0.12, 2.57, 0.38, 0.26),
          (0.74, 2.16, 0.48, 0.40), (0.39, 1.60, 0.74, 0.55), (0.85, 1.47, 0.39, 0.38), (1.10, 1.87, 0.38, 0.52), (0.08, 1.38, 0.40, 0.26),
          (-0.34, 1.83, 0.28, 0.27), (-0.64, 2.01, 0.25, 0.20)]

BIND = {
    "RightShoulder": V((-1.70, 0, 4.46)), "RightElbow": V((-1.92, -.02, 3.23)), "RightWrist": V((-2.08, -.06, 2.28)),
    "LeftShoulder": V((1.70, 0, 4.46)), "LeftElbow": V((1.92, -.02, 3.23)), "LeftWrist": V((2.08, -.06, 2.28)),
}


def two_bone_ik(S, Wt, pole, Ebind, Wbind):
    S, Wt, pole = V(S), V(Wt), V(pole)
    a = (V(Ebind) - S).length
    b = (V(Wbind) - V(Ebind)).length
    d = (Wt - S).length
    u = (Wt - S) / d
    assert abs(a - b) <= d <= a + b
    q = (pole - S - u * (pole - S).dot(u)).normalized()
    t = (a * a - b * b + d * d) / (2 * d)
    return S + u * t + q * math.sqrt(a * a - t * t), a, b


LEFT_S = BIND["LeftShoulder"]
LEFT_W = V((2.04, -.54, 3.44))
LEFT_POLE = V((2.60, .70, 3.25))
LEFT_E, SEG_UP, SEG_LO = two_bone_ik(LEFT_S, LEFT_W, LEFT_POLE, BIND["LeftElbow"], BIND["LeftWrist"])
GRIP_C = V((2.30, -.62, 3.50))
JOINTS = {
    "Root": (0, 0, 2.05), "Waist": (0, 0, 2.32), "Neck": (0, 0, 4.70),
    "RightShoulder": tuple(BIND["RightShoulder"]), "RightElbow": tuple(BIND["RightElbow"]), "RightWrist": tuple(BIND["RightWrist"]),
    "LeftShoulder": tuple(LEFT_S), "LeftElbow": tuple(LEFT_E), "LeftWrist": tuple(LEFT_W),
    "RightHip": (-.66, .02, 2.05), "RightKnee": (-.66, .02, 1.05), "RightAnkle": (-.66, .02, .45),
    "LeftHip": (.66, .02, 2.05), "LeftKnee": (.66, .02, 1.05), "LeftAnkle": (.66, .02, .45),
}
JV = {k: V(v) for k, v in JOINTS.items()}


def ut_front(x, h):
    return front_at(UT_ROWS, min(max(h, 2.20), 4.72), x)


def ut_back(x, h):
    return back_at(UT_ROWS, min(max(h, 2.20), 4.72), x)


def hf(h, x=0.0):
    return front_at(HEAD_ROWS, min(max(h, 4.74), 6.40), x)


def hb(h, x=0.0):
    return back_at(HEAD_ROWS, min(max(h, 4.74), 6.40), x)


def apron_wd(h):
    h = min(max(h, 1.10), 4.03)
    for a, b in zip(APRON_ROWS, APRON_ROWS[1:]):
        if a[0] <= h <= b[0]:
            t = (h - a[0]) / (b[0] - a[0])
            return a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t
    return APRON_ROWS[-1][1], APRON_ROWS[-1][2]


def apron_front(x, h):
    w, d = apron_wd(h)
    ax = abs(x)
    if ax <= .33 * w:
        return d
    return d + .12 * min(1.0, (ax - .33 * w) / max(1e-6, .5 * w - .33 * w))


# ----------------------------------------------------------------------------------------------
# UpperTorso: shirt, neck, collar, placket, apron (front, belt, straps, knot), rivets, stains, towel
# ----------------------------------------------------------------------------------------------
ut = PM("UpperTorso", JV["Waist"])
loft(ut, "UT_shirt_body", [row_ring(r) for r in UT_ROWS], sh_shirt, meta=meta("8-point chamfered loft, section 08 rows", dims={"rows": UT_ROWS}))
loft(ut, "UT_neck", [ring8(.36, -.28, .32, .07, 0, 0, 4.51), ring8(.36, -.28, .32, .07, 0, 0, 4.81)], sh_skin,
     meta=meta("neck W.72 D.60 H.30 centre (0,.02,4.66)", "prescribed"))
for s in (-1, 1):
    pts = [(-.73, 4.64), (-.14, 4.48), (-.40, 4.18)]
    poly = []
    for x, h in pts:
        X = x if s < 0 else -x
        poly.append(V((X, ut_front(X, h) - .035, h)))
    prism_poly(ut, "UT_collar_" + ("R" if s < 0 else "L"), poly, (0, -.045, 0), sh_shirt, meta("collar half, 3 vertices of section 09, .045 thick, .035 ahead of the shirt"))
front_strip(ut, "UT_placket", -.065, .065, [4.10, 4.24, 4.38], .015, .01, "SHIRT_DARK", ffn=ut_front, meta=meta("short placket W.13 H.28 at H4.24"))

# ---- apron front: closed slab following the section 10 table
AP_H = [1.10, 1.40, 1.70, 2.00, 2.30, 2.63, 2.88, 3.12, 3.37, 3.62, 3.83, 4.03]
NXA = 7
a_out, a_in = [], []
for li, h in enumerate(AP_H):
    w, _ = apron_wd(h)
    ro, ri = [], []
    for k in range(NXA):
        x = -w / 2 + w * k / (NXA - 1)
        hh = h
        if li == 0:
            hh = 1.10 + .04 * (abs(x) / (w / 2)) ** 2
        if li == len(AP_H) - 1:
            hh = 4.03
        d = apron_front(x, hh)
        ro.append(V((x, d, hh)))
        ri.append(V((x, d + .045, hh)))
    a_out.append(ro)
    a_in.append(ri)
grid_solid(ut, "UT_apron_front", a_out, a_in, sh_apron, meta("apron slab .045 thick, section 10 table, flat |X|<=.33W then +.12 to the edges, bottom edge arc 1.10 centre / 1.14 corners", dims={"rows": APRON_ROWS}))
w43, d43 = apron_wd(4.03)
grid_solid(ut, "UT_apron_top_seam", [[V((-w43 / 2 + w43 * k / 6, apron_front(-w43 / 2 + w43 * k / 6, 4.03) - .008, 4.03)) for k in range(7)],
                                      [V((-w43 / 2 + w43 * k / 6, apron_front(-w43 / 2 + w43 * k / 6, 3.985) - .008, 3.985)) for k in range(7)]],
           [[V((-w43 / 2 + w43 * k / 6, apron_front(-w43 / 2 + w43 * k / 6, 4.03) + .03, 4.03)) for k in range(7)],
             [V((-w43 / 2 + w43 * k / 6, apron_front(-w43 / 2 + w43 * k / 6, 3.985) + .03, 3.985)) for k in range(7)]], sh_const("APRON_SEAM"),
           meta("apron top edge W2.10 H.045 APRON_SEAM"))

# ---- apron belt (wraps the whole torso) H2.57..2.77
belt_rows = []
for h in (2.57, 2.67, 2.77):
    aw, ad = apron_wd(h)
    uw, uf, ub, uc = interp_row(UT_ROWS, h)
    belt_rows.append((h, aw + .12, ad - .055, ub + .06, uc + .05))
loft(ut, "UT_apron_belt", [row_ring(r) for r in belt_rows], lambda n, c: "APRON_SEAM" if n.z > .55 else "APRON_DARK",
     meta=meta("apron waistband H2.57..2.77 thick .055, wraps the torso, no buckle", dims={"rows": belt_rows}))

# ---- shoulder straps (front end on the apron, over the shoulder, down the back to the belt) + back knot
STRAP_L = [(.88, -.86, 3.86), (1.00, -.76, 4.24), (1.14, -.36, 4.58), (1.10, .32, 4.66), (.98, .58, 4.10), (.93, .67, 2.72)]
for s in (-1, 1):
    pts = []
    for i, (x, d, h) in enumerate(STRAP_L):
        if i == 0:
            d = apron_front(x, h) - .03
        pts.append(V((s * x, d, h)))
    pts = catmull(pts, 3)
    rings = []
    for i, p in enumerate(pts):
        T = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        Bx = V((1, 0, 0)) - T * T.dot(V((1, 0, 0)))
        Bx = Bx.normalized() if Bx.length > 1e-4 else V((0, 1, 0))
        N = T.cross(Bx).normalized()
        rings.append(ring_pts(p, Bx, N, .24, .05, 8))
    loft(ut, "UT_strap_" + ("R" if s < 0 else "L"), rings, sh_apron, meta=meta("shoulder strap W.24 thick .05 along the section 11 key points, mirrored", dims={"pts": STRAP_L}))
    for d_ in (-1, 1):
        pass
box_c(ut, "UT_back_knot", (0, .76, 2.67), (.22, .12, .18), sh_apron, ch=.02, meta_=meta("apron back knot .22 x .12 x .18", "prescribed"))
for sx in (-1, 1):
    box_c(ut, "UT_back_tie_end_%d" % sx, (sx * .10, .76, 2.67 - .09 - .225), (.14, .035, .45), sh_apron, meta_=meta("flat tie end .14 x .035 x .45 hanging from the knot", "prescribed"))

# ---- two gold rivets on the front strap ends
for s in (-1, 1):
    nm = "R" if s < 0 else "L"
    cx = s * .88
    cd = apron_front(cx, 3.86) - .045
    disc_d(ut, "UT_rivet_base_" + nm, cx, cd + .012, 3.86, .11, .02, "GOLD_DARK", segs=12, embed=.03)
    disc_d(ut, "UT_rivet_head_" + nm, cx, cd - .022, 3.86, .105, .045, "GOLD", segs=12, embed=.012)
    disc_d(ut, "UT_rivet_facet_" + nm, cx - .04, cd - .026, 3.86 + .04, .028, .01, "GOLD_LIGHT", segs=6)

# ---- 12 stains (16-ray outlines projected on the apron with offset .003)
RAY = [.92, .64, .83, .56, 1, .70, .87, .55, .95, .61, .85, .67, .96, .58, .80, .65]
STAIN_TILES = ("STAIN", "STAIN_DARK", "STAIN_LIGHT")
for i, (cx, ch_, w, h) in enumerate(STAINS):
    ph = (i % 3) * .17
    big = w * h > .12
    outline = []
    for k in range(16):
        r = RAY[k]
        if big and k in ((i * 3) % 16, (i * 5 + 7) % 16, (i * 11 + 3) % 16):
            r *= 1.22
        a = k * 2 * math.pi / 16 + ph
        x = cx + .5 * w * r * math.cos(a)
        hh = ch_ + .5 * h * r * math.sin(a)
        outline.append((x, hh))
    if max(p[1] for p in outline) > 2.55 and min(p[1] for p in outline) < 2.55:
        # the waistband (H2.57..2.77) covers this field: compress the outline below it instead of clamping (no degenerate faces)
        lo_, hi_ = min(p[1] for p in outline), max(p[1] for p in outline)
        outline = [(x, lo_ + (hh - lo_) * (2.55 - lo_) / (hi_ - lo_)) for x, hh in outline]
    plate(ut, "UT_stain_%02d" % (i + 1), outline, lambda x, h: apron_front(x, h) + .001, lambda x, h: apron_front(x, h) - .003, STAIN_TILES[i % 3], ch=.001,
          meta_=meta("stain %d: 16-ray outline, centre (%.2f,%.2f) bbox %.2f x %.2f" % (i + 1, cx, ch_, w, h), "observed+prescribed"))

# ---- towel on the anatomical RIGHT (X<0): relief across u, two red stripes
TW_C = V((-.95, -1.16, 2.155))
TW_REL = [(-.315, 0), (-.24, -.025), (-.13, .008), (-.03, -.020), (.09, .010), (.21, -.020), (.315, 0)]
TW_H = [1.44, 1.66, 1.74, 1.82, 1.90, 2.30, 2.58, 2.87]
t_out, t_in = [], []
for li, h in enumerate(TW_H):
    ro, ri = [], []
    for k, (u, off) in enumerate(TW_REL):
        wscale = 1.0 - .08 * (h - 1.44) / (2.87 - 1.44)
        hh = h + (.025 * math.sin(u * 17.0) if li == 0 else 0.0)
        ro.append(V((TW_C.x + u * wscale, TW_C.y + off, hh)))
        ri.append(V((TW_C.x + u * wscale, TW_C.y + off + .03, hh)))
    t_out.append(ro)
    t_in.append(ri)


def towel_tile(n, c):
    if n.y < -.4 and ((1.66 <= c.z <= 1.74) or (1.82 <= c.z <= 1.90)):
        return "TOWEL_RED"
    if n.y < -.4:
        rel = c.y - TW_C.y
        if rel < -.012:
            return "TOWEL_LIGHT"
        if rel > .004:
            return "TOWEL_SHADOW"
        return "TOWEL"
    return "TOWEL_SHADOW" if n.z < -.5 else "TOWEL"


grid_solid(ut, "UT_towel_front", t_out, t_in, towel_tile, meta("towel front hanging part W.63 H1.43 (H1.44..2.87), relief per section 14, two TOWEL_RED stripes H1.66..1.74 and H1.82..1.90", dims={"relief": TW_REL, "rows": TW_H}))
# short rear tail over the waistband (H2.58..2.87), prescribed
TX0, TX1 = TW_C.x - .26, TW_C.x + .26
grid_solid(ut, "UT_towel_tail", [[V((TX0, TW_C.y + .04, 2.87)), V((TX1, TW_C.y + .04, 2.87))], [V((TX0, TW_C.y + .15, 2.58)), V((TX1, TW_C.y + .15, 2.58))]],
           [[V((TX0, TW_C.y + .075, 2.87)), V((TX1, TW_C.y + .075, 2.87))], [V((TX0, TW_C.y + .185, 2.58)), V((TX1, TW_C.y + .185, 2.58))]], sh_const("TOWEL_SHADOW"),
           meta("short rear tail of the towel H2.58..2.87 (hidden behind the front part)", "prescribed"))

# ----------------------------------------------------------------------------------------------
# LowerTorso, legs, trouser cuffs, boots
# ----------------------------------------------------------------------------------------------
lt = PM("LowerTorso", JV["Root"])
loft(lt, "LT_hip", [row_ring(r) for r in LT_ROWS], sh_pants, meta=meta("pants hip, section 15 rows", dims={"rows": LT_ROWS}))
front_strip(lt, "LT_centre_seam", -.0125, .0125, [1.77, 1.98, 2.18], .008, .01, "PANTS_DARK", ffn=lambda x, h: front_at(LT_ROWS, min(max(h, 1.82), 2.34), x), meta=meta("crotch seam W.025 H1.77..2.18"))

for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    hip, knee, ank = JV[side + "Hip"], JV[side + "Knee"], JV[side + "Ankle"]
    ul = PM(side + "UpperLeg", hip)
    lu = Limb(hip, knee)
    t0, t1 = (hip.z - 2.10) / (hip.z - knee.z), (hip.z - 1.01) / (hip.z - knee.z)
    loft(ul, "UL_thigh_" + side, [lu.ring(t0, 1.10, 1.00, .09), lu.ring((t0 + t1) / 2, 1.06, .965, .09), lu.ring(t1, 1.02, .93, .09)], sh_pants, meta=meta("thigh H1.01..2.10, 1.10 x 1.00 -> 1.02 x .93"))
    ll = PM(side + "LowerLeg", knee)
    lk = Limb(knee, ank)
    k0, k1 = (knee.z - 1.10) / (knee.z - ank.z), (knee.z - .48) / (knee.z - ank.z)
    loft(ll, "LL_shin_" + side, [lk.ring(k0, 1.01, .95, .07), lk.ring(k1, 1.01, .95, .07)], sh_pants, meta=meta("shin H.48..1.10, 1.01 x .95"))
    cuff = [lk.ring((knee.z - .60) / (knee.z - ank.z), 1.03, .97, .07), lk.ring((knee.z - .615) / (knee.z - ank.z), 1.06, 1.0, .08),
            lk.ring((knee.z - .755) / (knee.z - ank.z), 1.06, 1.0, .08), lk.ring((knee.z - .77) / (knee.z - ank.z), 1.03, .97, .07)]
    loft(ll, "LL_cuff_" + side, cuff, lambda n, c: "PANTS_LIGHT" if n.z > .55 else "PANTS_DARK", meta=meta("trouser hem H.60..0.77, 1.06 x 1.00, .025 PANTS_DARK edge"))
    ft = PM(side + "Foot", ank)
    cx = s * .67
    loft(ft, "FT_sole_" + side, [ring8(.625 - g, -.935 + g, .615 - g, .11, cx, 0, h) for h, g in ((0.0, .025), (.02, 0), (.11, 0), (.13, 0))], sh_const("SOLE"), meta=meta("sole H0..0.13, W1.25, D-.935..+.615"))
    up = [ring8(.62, -.93, .60, .11, cx, 0, .13), ring8(.60, -.90, .58, .11, cx, 0, .30), ring8(.58, -.80, .57, .11, cx, 0, .46),
          ring8(.55, -.34, .56, .10, cx, 0, .54), ring8(.54, -.20, .55, .10, cx, 0, .66)]
    loft(ft, "FT_upper_" + side, up, sh_shoe, meta=meta("boot: toe D-.94..-.20 H.13..46, instep/shaft D-.20..55 H.13..66, W1.25 -> 1.08"))
