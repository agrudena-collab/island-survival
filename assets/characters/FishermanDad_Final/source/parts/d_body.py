

# ----------------------------------------------------------------------------------------------
# prescribed numeric tables (master prompt sections 08..18)
# ----------------------------------------------------------------------------------------------
UT_ROWS = [(2.12, 2.60, -.93, .55, .13), (2.45, 2.82, -1.02, .62, .16), (2.95, 2.90, -1.04, .65, .17),
           (3.50, 2.78, -.92, .62, .14), (3.98, 2.85, -.72, .55, .12), (4.25, 2.48, -.58, .49, .10)]
LT_ROWS = [(1.55, 2.24, -.68, .48, .12), (1.92, 2.52, -.82, .56, .14), (2.18, 2.62, -.90, .56, .12)]
HEAD_ROWS = [(4.22, 1.40, -.58, .50, .10), (4.40, 1.72, -.70, .62, .12), (4.70, 1.80, -.70, .66, .14),
             (5.40, 1.80, -.70, .66, .14), (5.68, 1.72, -.64, .62, .12), (5.78, 1.56, -.56, .54, .10)]

BIND = {  # neutral bind joints (section 17)
    "RightShoulder": V((-1.65, 0, 4.15)), "RightElbow": V((-1.88, -.03, 3.05)), "RightWrist": V((-2.03, -.08, 2.18)),
    "LeftShoulder": V((1.65, 0, 4.15)), "LeftElbow": V((1.88, -.03, 3.05)), "LeftWrist": V((2.03, -.08, 2.18)),
}


def two_bone_ik(S, Wt, pole, Ebind, Wbind):
    """Section 18: E = S + t*u + sqrt(a^2-t^2)*q with bind segment lengths."""
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
LEFT_W = V((1.98, -.57, 3.44))
LEFT_POLE = V((2.25, .65, 2.70))
LEFT_E, SEG_UP, SEG_LO = two_bone_ik(LEFT_S, LEFT_W, LEFT_POLE, BIND["LeftElbow"], BIND["LeftWrist"])
GRIP_C = V((2.24, -.65, 3.50))          # geometric centre of the grip hand = rod axis point A3
JOINTS = {
    "Root": (0, 0, 1.92), "Waist": (0, 0, 2.18), "Neck": (0, 0, 4.30),
    "RightShoulder": tuple(BIND["RightShoulder"]), "RightElbow": tuple(BIND["RightElbow"]), "RightWrist": tuple(BIND["RightWrist"]),
    "LeftShoulder": tuple(LEFT_S), "LeftElbow": tuple(LEFT_E), "LeftWrist": tuple(LEFT_W),
    "RightHip": (-.66, .02, 1.92), "RightKnee": (-.66, .01, .98), "RightAnkle": (-.66, 0, .45),
    "LeftHip": (.66, .02, 1.92), "LeftKnee": (.66, .01, .98), "LeftAnkle": (.66, 0, .45),
}
JV = {k: V(v) for k, v in JOINTS.items()}


def ut_front(x, h):
    return front_at(UT_ROWS, min(max(h, 2.12), 4.25), x)


def ut_back(x, h):
    return back_at(UT_ROWS, min(max(h, 2.12), 4.25), x)


def lt_front(x, h):
    return front_at(LT_ROWS, min(max(h, 1.55), 2.18), x)


def lt_back(x, h):
    return back_at(LT_ROWS, min(max(h, 1.55), 2.18), x)


def hf(h, x=0.0):
    return front_at(HEAD_ROWS, min(max(h, 4.22), 5.78), x)


def hb(h, x=0.0):
    return back_at(HEAD_ROWS, min(max(h, 4.22), 5.78), x)


VEST_OUT, VEST_IN = .065, .010


def vest_front(x, h):
    return ut_front(x, h) - VEST_OUT


def vest_back(x, h):
    return ut_back(x, h) + VEST_OUT


# belt rows: outside both the trouser hip (+.045) and the shirt hem (+.03)
def _belt_row(h):
    lw, lf, lb, lc = interp_row(LT_ROWS, min(max(h, 1.55), 2.18))
    uw, uf, ub, uc = interp_row(UT_ROWS, min(max(h, 2.12), 4.25))
    if h < 2.12:
        uw, uf, ub = 0, 0, 0
        return (h, lw + .09, lf - .045, lb + .045, lc + .03)
    return (h, max(lw, uw) + .09, min(lf, uf) - .045, max(lb, ub) + .045, max(lc, uc) + .03)


BELT_ROWS = [_belt_row(2.02), _belt_row(2.12), _belt_row(2.24)]


def belt_front(x, h):
    return front_at(BELT_ROWS, min(max(h, 2.02), 2.24), x)


# ----------------------------------------------------------------------------------------------
# UpperTorso: shirt, neck, collar, placket, buttons, vest (front/back/straps), four pockets
# ----------------------------------------------------------------------------------------------
ut = PM("UpperTorso", JV["Waist"])
loft(ut, "UT_shirt_body", [row_ring(r) for r in UT_ROWS], sh_shirt,
     meta=meta("8-point chamfered loft, section 08 rows", dims={"rows": UT_ROWS}))
loft(ut, "UT_neck", [ring8(.30, -.27, .27, .07, 0, 0, 4.11), ring8(.30, -.27, .27, .07, 0, 0, 4.43)], sh_skin,
     meta=meta("neck .60 x .54 x .32, centre H4.27, bevel .07", "prescribed"))
for s in (-1, 1):
    pts = [(-.58, 4.18), (-.18, 4.25), (-.04, 4.05), (-.43, 3.82)]
    poly = []
    for x, h in pts:
        X = x if s < 0 else -x
        poly.append(V((X, ut_front(X, h) - .025, h)))
    prism_poly(ut, "UT_collar_lobe_" + ("R" if s < 0 else "L"), poly, (0, -.045, 0),
               lambda n, c: "SHIRT_LIGHT" if n.y < -0.5 else "SHIRT_SHADOW",
               meta("collar lobe, 4 vertices of section 08, .045 thick, .025 ahead of the shirt"))
front_strip(ut, "UT_placket", -.05, .05, [2.20, 2.8, 3.5, 4.12], .012, .01, "SHIRT_SEAM", ffn=ut_front,
            meta=meta("placket W.10, H2.20..4.12, proud .012"))
for i, hb_ in enumerate((3.92, 3.55, 3.18, 2.80, 2.42)):
    disc_d(ut, "UT_shirt_button_%d" % (i + 1), 0.0, ut_front(0, hb_) - .012 - .025, hb_, .0375, .025, "BUTTON", segs=8, embed=.012)

# ---- vest: wrapped band (front panels open in the middle) + back + shoulder straps
VEST_LEVELS = [2.16, 2.45, 2.95, 3.50, 3.98, 4.20]


def vest_open_half(h):
    # inner edge |X|: .35 at the belly, opening to .47 at the top (section 09)
    if h <= 3.90:
        return .35 + (h - 2.16) * 0.0057 / 1.0 * 0.2
    return .36 + (h - 3.90) * (.47 - .36) / (4.20 - 3.90)


def vest_path(h):
    w, f, b, c = interp_row(UT_ROWS, h)
    a = w / 2.0
    ho = vest_open_half(h)
    return [(ho, f), (a - c, f), (a, f + c), (a, b - c), (a - c, b), (-a + c, b), (-a, b - c), (-a, f + c), (-a + c, f), (-ho, f)]


band(ut, "UT_vest_body", VEST_LEVELS, vest_path, VEST_OUT, VEST_IN, sh_vest,
     meta_=meta("open vest: wrapped band over the shirt, thickness .055, front opening |X|=.35..47, hem H2.16, top H4.20"))
for s in (-1, 1):
    x0, x1 = (s * .585, s * 1.015)
    xa, xb = min(x0, x1), max(x0, x1)
    poly = [V((xa, -.62, 4.185)), V((xb, -.62, 4.185)), V((xb, .52, 4.185)), V((xa, .52, 4.185))]
    prism_poly(ut, "UT_vest_strap_" + ("R" if s < 0 else "L"), poly, (0, 0, .085), sh_vest,
               meta("shoulder strap W.43 across the shoulder from front panel to back"))
front_strip(ut, "UT_vest_back_seam", -.006, .006, [2.28, 3.0, 3.6, 4.2], .012, .02, "VEST_SEAM", ffn=vest_back, rear=True,
            meta=meta("shallow centre back seam .012"))

# ---- four patch pockets with flaps and brass buttons
POCKETS = [  # (name, cx, cH, W, H, proud, flap_top, flap_bot, button_h, folds)
    ("RU", -.91, 3.43, .62, .60, .10, 3.73, 3.51, 3.59, (0.0,)),
    ("LU", .91, 3.43, .62, .60, .10, 3.73, 3.51, 3.59, (0.0,)),
    ("RL", -1.00, 2.65, .78, .72, .13, 3.01, 2.76, 2.84, (-.17, .17)),
    ("LL", 1.00, 2.65, .78, .72, .13, 3.01, 2.76, 2.84, (-.17, .17)),
]
for nm, cx, chh, pw, ph, proud, ftop, fbot, bh, folds in POCKETS:
    x0, x1, h0, h1 = cx - pw / 2, cx + pw / 2, chh - ph / 2, chh + ph / 2
    patch(ut, "UT_pocket_" + nm, [(x0, h0), (x1, h0), (x1, h1), (x0, h1)], vest_front, -.015, proud, sh_vest, ch=.025, nx=4, step=.25,
          meta_=meta("patch pocket %.2f x %.2f, proud %.2f" % (pw, ph, proud)))
    fx0, fx1 = x0 - .0175, x1 + .0175
    flap = [(fx0, ftop), (fx1, ftop), (fx1, fbot + .045), (cx, fbot), (fx0, fbot + .045)]
    patch(ut, "UT_flap_" + nm, flap, vest_front, proud - .002, proud + .035, sh_vest, ch=.012, nx=5, step=.25,
          meta_=meta("pocket flap, pentagon with centre tip .045, thickness .035"))
    disc_d(ut, "UT_flap_button_" + nm, cx, vest_front(cx, bh) - proud - .035 - .018, bh, .0325, .018, "BUTTON", segs=8, embed=.02)
    for fo in folds:
        patch(ut, "UT_pocket_fold_%s_%+.2f" % (nm, fo), [(cx + fo - .006, h0 + .04), (cx + fo + .006, h0 + .04), (cx + fo + .006, fbot), (cx + fo - .006, fbot)],
              vest_front, proud - .004, proud + .004, sh_const("VEST_SEAM"), nx=2, step=.4, meta_=meta("shallow vertical fold .012", "inferred"))

# ----------------------------------------------------------------------------------------------
# LowerTorso: trousers hip, belt, buckle, loops, fly, rear slit pockets
# ----------------------------------------------------------------------------------------------
lt = PM("LowerTorso", JV["Root"])
loft(lt, "LT_hip", [row_ring(r) for r in LT_ROWS], sh_pants, meta=meta("8-point loft, section 11 rows", dims={"rows": LT_ROWS}))
loft(lt, "LT_belt", [row_ring(r) for r in BELT_ROWS], sh_const("BELT"),
     meta=meta("belt H2.02..2.24 proud of hip and shirt hem", dims={"rows": BELT_ROWS}))
# buckle: outer .37 x .27 x .055, opening .25 x .15, centre (0,-.99,2.13)
BK = V((0, -.99, 2.13))
for nm, c, sz in (("top", (0, BK.y, BK.z + .105), (.37, .055, .06)), ("bottom", (0, BK.y, BK.z - .105), (.37, .055, .06)),
                  ("left", (-.155, BK.y, BK.z), (.06, .055, .15)), ("right", (.155, BK.y, BK.z), (.06, .055, .15))):
    box_c(lt, "LT_buckle_" + nm, c, sz, lambda n, c_: "SILVER_LIGHT" if n.z > .5 else "SILVER", ch=.008,
          meta_=meta("buckle bar", "prescribed"))
box_c(lt, "LT_buckle_tongue", (-.0425, BK.y - .004, BK.z), (.135, .02, .025), sh_const("SILVER"), meta_=meta("prong W.025 from X-.11 to +.025", "prescribed"))
for x in (-1.23, -.91, .91, 1.23):
    front_strip(lt, "LT_loop_front_%+.2f" % x, x - .045, x + .045, [1.99, 2.13, 2.28], .02, .03, "PANTS_DARK", ffn=belt_front,
                meta=meta("belt loop W.09, H1.99..2.28"))
for x in (-.72, .72):
    front_strip(lt, "LT_loop_back_%+.2f" % x, x - .045, x + .045, [1.99, 2.28], .06, .03, "PANTS_DARK", ffn=lambda xx, hh: lt_back(xx, hh) + .045, rear=True,
                meta=meta("rear belt loop", "prescribed"))
front_strip(lt, "LT_fly", .054, .066, [1.68, 1.9, 2.08], .006, .01, "PANTS_DARK", ffn=lt_front, meta=meta("fly line W.012 at X=.06, H1.68..2.08"))
for x in (-.56, .56):
    front_strip(lt, "LT_back_slit_%+.2f" % x, x - .21, x + .21, [1.88, 1.98], .012, .01, "PANTS_DARK", ffn=lt_back, rear=True,
                meta=meta("rear slit pocket W.42 H.10 at H1.93", "prescribed"))

# ----------------------------------------------------------------------------------------------
# legs, trouser cuffs, rubber boots, cargo pocket on the anatomical RIGHT thigh
# ----------------------------------------------------------------------------------------------
THIGH_TOP, THIGH_BOT = (1.12, 1.02), (1.04, .96)
SHIN_TOP, SHIN_BOT = (1.04, .96), (1.05, 1.00)


def thigh_front(side_x):
    def f(x, h):
        t = (1.92 - h) / (1.92 - .98)
        t = min(max(t, 0.0), 1.0)
        dc = .02 + (.01 - .02) * t
        d = 1.02 + (.96 - 1.02) * t
        return dc - d / 2.0
    return f


for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    hip, knee, ank = JV[side + "Hip"], JV[side + "Knee"], JV[side + "Ankle"]
    ul = PM(side + "UpperLeg", hip)
    lu = Limb(hip, knee)
    t0 = (hip.z - 1.99) / (hip.z - knee.z)
    t1 = (hip.z - .95) / (hip.z - knee.z)
    loft(ul, "UL_thigh_" + side, [lu.ring(t0, *THIGH_TOP, .09), lu.ring((t0 + t1) / 2, 1.08, .99, .09), lu.ring(t1, *THIGH_BOT, .08)], sh_pants,
         meta=meta("thigh H1.99..0.95, 1.12 x 1.02 -> 1.04 x .96"))
    ll = PM(side + "LowerLeg", knee)
    lk = Limb(knee, ank)
    k0 = (knee.z - 1.02) / (knee.z - ank.z)
    k1 = (knee.z - .62) / (knee.z - ank.z)
    loft(ll, "LL_shin_" + side, [lk.ring(k0, *SHIN_TOP, .08), lk.ring(k1, *SHIN_BOT, .09)], sh_pants,
         meta=meta("shin H1.02..0.62, 1.04 x .96 -> 1.05 x 1.00"))
    cuff = [lk.ring((knee.z - .67) / (knee.z - ank.z), 1.07, 1.02, .08), lk.ring((knee.z - .685) / (knee.z - ank.z), 1.10, 1.05, .09),
            lk.ring((knee.z - .815) / (knee.z - ank.z), 1.10, 1.05, .09), lk.ring((knee.z - .83) / (knee.z - ank.z), 1.07, 1.02, .08)]
    loft(ll, "LL_cuff_" + side, cuff, lambda n, c: "CUFF" if n.z > .55 else ("PANTS_DARK" if n.z < -.5 else "PANTS_LIGHT"),
         meta=meta("trouser cuff H.67..0.83, 1.10 x 1.05, thickness .04, CUFF edge on top"))
    ft = PM(side + "Foot", ank)
    cx = s * .66
    rings = [ring8(.63 - g, -.935 + g, .615 - g, .11, cx, 0, h) for h, g in ((0.0, .025), (.02, 0.0), (.12, 0.0), (.14, .0))]
    loft(ft, "FT_sole_" + side, rings, sh_const("BOOT_SOLE"), meta=meta("sole H0..0.14, W1.26, D-.935..+.615"))
    up = [ring8(.62, -.925, .60, .11, cx, 0, .14), ring8(.60, -.90, .59, .11, cx, 0, .30), ring8(.57, -.80, .57, .11, cx, 0, .45),
          ring8(.52, -.55, .57, .10, cx, 0, .52)]
    loft(ft, "FT_upper_" + side, up, sh_boot, meta=meta("boot foot H.14..0.52, toe bevel .11, broad top facet"))
    sh_ = [ring8(.54, -.45, .61, .11, cx, 0, .45), ring8(.54, -.45, .61, .11, cx, 0, .70), ring8(.53, -.44, .60, .10, cx, 0, .72)]
    loft(ft, "FT_shaft_" + side, sh_, sh_boot, band_tiles={1: "BOOT_LIGHT"}, meta=meta("boot shaft H.45..0.72, W1.08 D1.06, light top edge"))

# cargo pocket, anatomical RIGHT thigh (X<0)
tf = thigh_front(-.66)
patch(PARTS["RightUpperLeg"], "UL_cargo_pocket", [(-1.15, 1.04), (-.61, 1.04), (-.61, 1.62), (-1.15, 1.62)], tf, -.015, .10, sh_pants, ch=.025, nx=4, step=.25,
      meta_=meta("cargo pocket .54 x .58, proud .10, centre (-.88,-.58,1.33)"))
patch(PARTS["RightUpperLeg"], "UL_cargo_flap", [(-1.165, 1.62), (-.595, 1.62), (-.595, 1.465), (-.88, 1.42), (-1.165, 1.465)], tf, .098, .135, sh_const("VEST_DARK"), ch=.012, nx=5, step=.25,
      meta_=meta("cargo flap W.57 H.18, top 1.62, tip 1.42"))
disc_d(PARTS["RightUpperLeg"], "UL_cargo_button", -.88, tf(-.88, 1.48) - .135 - .015, 1.48, .025, .015, "BUTTON", segs=8, embed=.02)
patch(PARTS["RightUpperLeg"], "UL_cargo_seam", [(-.886, 1.06), (-.874, 1.06), (-.874, 1.42), (-.886, 1.42)], tf, .096, .104, sh_const("PANTS_DARK"), nx=2, step=.4,
      meta_=meta("seam .012", "inferred"))
