# ----------------------------------------------------------------------------------------------
# torso (jacket, shirt window, tie, belt), pelvis, trousers, legs, shoes
# ----------------------------------------------------------------------------------------------
FLOOR_IN = 0.10                                   # depth of the shirt / trouser window below the jacket surface
OPEN_UP = [(-.60, 5.05), (-.92, 4.62), (-.78, 4.10), (-.56, 3.30), (-.56, 2.86), (.56, 2.86), (.56, 3.30), (.78, 4.10), (.92, 4.62), (.60, 5.05)]
OPEN_LOW = [(-.56, 2.86), (-.56, 2.10), (.56, 2.10), (.56, 2.86)]


def floor_front(x, h):
    return tfront(x, h) + FLOOR_IN


def cut_window(bm, poly, floor_tile, wall_tile):
    cutter = plate_bm(poly, tfront, [(FLOOR_IN, 1.0, 1.0), (-.40, 1.0, 1.0)], floor_tile)
    bm = bm_boolean(bm, cutter)
    cutter.free()
    tl_ = bm.faces.layers.int.get("tile")
    for f_ in bm.faces:
        if PAL[f_[tl_]][0] == floor_tile:
            f_.normal_update()
            if abs(f_.normal.y) < 0.7:
                f_[tl_] = TILE[wall_tile]
    return bm


# ---- UpperTorso: jacket shell with the V window (shirt floor), shirt collar band, lapels, tie, pocket square, buttons --------------------
ut = PM("UpperTorso", JV["Waist"], xf=xf_ut)
bm = loft_bm([row_ring(r) for r in UPPER_ROWS], sh_navy)
bm = cut_window(bm, OPEN_UP, "Shirt", "NavyShadow")
ut.append_bm("UT_jacket_shell", bm, None, {"recipe": "7-row octagon loft H2.20..4.86 (upper part from H2.86), V-window boolean (floor .10 under the surface) for the shirt", "class": "measured+extrapolated"})
bm.free()

# shirt collar band around the neck (white) + two pointed collar flaps on the shirt floor
loft(ut, "UT_collar_band", [ring8(.60, -.52, .50, .10, 0, 0, h) for h in (4.80, 4.86)] + [ring8(.60, -.52, .50, .10, 0, 0, 5.08)], sh_shirt, meta={"recipe": "collar band W1.20 around the neck H4.80..5.08", "class": "prescribed"})
for s, nm in ((-1, "R"), (1, "L")):
    flap = [(s * .16, 5.04), (s * .62, 5.04), (s * .70, 4.50), (s * .46, 4.62), (s * .18, 4.58)]
    layered_plate(ut, "UT_collar_flap_" + nm, flap, floor_front, [(+.03, 1.0, 1.0), (-.095, 1.0, 1.0)], sh_const("Shirt"), {"recipe": "pointed collar flap on the shirt floor", "class": "observed"})
    # lapel: navy plate over the jacket surface along the window edge, up to the button line
    lap = [(s * .60, 5.06), (s * .93, 4.62), (s * .79, 4.10), (s * .55, 3.30), (s * .84, 3.36), (s * 1.04, 4.10), (s * 1.28, 4.64), (s * 1.02, 5.00)]
    layered_plate(ut, "UT_lapel_" + nm, lap, tfront, [(+.05, 1.0, 1.0), (-.07, 1.0, 1.0)], sh_const("NavyLight"), {"recipe": "lapel plate .07 proud, notch + peak", "class": "observed"})
    lap_edge = [(s * .93, 4.62), (s * 1.28, 4.64), (s * 1.30, 4.55), (s * .96, 4.50)]
    layered_plate(ut, "UT_lapel_peak_" + nm, lap_edge, tfront, [(+.05, 1.0, 1.0), (-.10, 1.0, 1.0)], sh_const("Navy"), {"recipe": "lapel peak facet", "class": "extrapolated"})

# tie (knot + blade down to H2.86), gold tie bar, pocket square
KNOT = [(-.17, 4.86), (.17, 4.86), (.23, 4.54), (.15, 4.40), (-.15, 4.40), (-.23, 4.54)]
layered_plate(ut, "UT_tie_knot", KNOT, floor_front, [(+.03, 1.0, 1.0), (-.14, 1.0, 1.0)], sh_tie, {"recipe": "tie knot, 0.14 proud of the shirt floor", "class": "observed"})
BLADE = [(-.16, 4.46), (.16, 4.46), (.30, 3.90), (.35, 3.30), (.33, 2.86), (-.33, 2.86), (-.35, 3.30), (-.30, 3.90)]
layered_plate(ut, "UT_tie_blade", BLADE, floor_front, [(+.03, 1.0, 1.0), (-.11, 1.0, 1.0)], sh_tie, {"recipe": "tie blade widening to W.70, 0.11 proud", "class": "observed"})
layered_plate(ut, "UT_tie_bar", [(-.235, 3.86), (.235, 3.86), (.235, 3.78), (-.235, 3.78)], floor_front, [(+.03, 1.0, 1.0), (-.17, 1.0, 1.0)], sh_gold, {"recipe": "narrow horizontal gold tie bar", "class": "observed"})
layered_plate(ut, "UT_pocket_welt", [(1.02, 3.93), (1.44, 3.93), (1.44, 3.88), (1.02, 3.88)], tfront, [(+.05, 1.0, 1.0), (-.06, 1.0, 1.0)], sh_const("NavyShadow"), {"recipe": "breast pocket welt (character left)", "class": "observed"})
layered_plate(ut, "UT_pocket_square", [(1.08, 3.93), (1.40, 3.93), (1.36, 4.18), (1.24, 4.04), (1.14, 4.16)], tfront, [(+.05, 1.0, 1.0), (-.10, 1.0, 1.0)], sh_const("Shirt"), {"recipe": "white pocket square, two folded points", "class": "observed"})
for k, (bx, bh) in enumerate(((-.66, 3.12), (-.64, 2.70))):
    fy = -(tfront(bx, bh) - .01)
    cyl_y(ut, "UT_button_%d" % (k + 1), bx, bh, tfront(bx, bh) - .07, tfront(bx, bh) + .03, .075, 10, sh_const("Button"), {"recipe": "jacket button", "class": "observed"})

# ---- LowerTorso: jacket skirt (H2.20..2.86) with the trouser window, belt, buckle, pelvis / seat ---------------------------------------------
lt = PM("LowerTorso", JV["Root"], xf=xf_lt)
bm = loft_bm([row_ring(r) for r in LOWER_ROWS], sh_navy)
bm = cut_window(bm, OPEN_LOW, "Trouser", "NavyShadow")
_ha = AxisG(JV["RightWrist"], JV["RightWrist"] + RHAND_DIR * .96)


def _lt_old(q):
    """world (Blender) point -> LowerTorso authoring coordinates (inverse of xf_lt)"""
    return V((q.x / LT_SX, q.y / .95, 1.93 + (q.z - 2.25) / .663))


_tun = loft_bm([[_lt_old(q) for q in _ha.ring(t, 1.02, .66, .12)] for t in (.10, .45, .80, 1.12)], sh_const("NavyDeep"))
bm = bm_boolean(bm, _tun)
_tun.free()
lt.append_bm("LT_jacket_skirt", bm, None, {"recipe": "jacket skirt rows H2.20..2.86 with trouser window", "class": "measured+extrapolated"})
bm.free()
PEL = [(1.93, 2.70, .56, -.52, .14), (2.05, 3.14, .70, -.64, .14), (2.20, 3.20, .74, -.66, .13), (2.34, 3.06, .70, -.64, .12)]
loft(lt, "LT_pelvis_trousers", [row_ring((h, w, -ff, -fb, c)) for h, w, ff, fb, c in PEL], sh_trouser, meta={"recipe": "seat / pelvis block H1.93..2.34 (crotch at H1.93 as measured)", "class": "measured+extrapolated"})
layered_plate(lt, "LT_belt", [(-.80, 2.88), (.80, 2.88), (.80, 2.55), (-.80, 2.55)], floor_front, [(+.04, 1.0, 1.0), (-.045, 1.0, 1.0)], sh_const("BeltBlack"), {"recipe": "belt band H2.55..2.88 across the window", "class": "observed"})
BUCK_F = floor_front(0, 2.7) - .045
for nm, x0, x1, h0, h1, tile in (("L", -.30, -.18, 2.55, 2.88, "Silver"), ("R", .18, .30, 2.55, 2.88, "Silver"), ("T", -.30, .30, 2.78, 2.88, "SilverLight"), ("B", -.30, .30, 2.55, 2.65, "SilverShadow")):
    solid_box(lt, "LT_buckle_%s" % nm, x0, x1, BUCK_F - .06, BUCK_F + .05, h0, h1, tile, {"recipe": "silver rectangular buckle frame (4 bars)", "class": "observed"})
solid_box(lt, "LT_buckle_prong", -.045, .045, BUCK_F - .05, BUCK_F + .05, 2.62, 2.82, "Silver", {"recipe": "buckle tongue", "class": "observed"})
TIP = [(-.33, 2.87), (.33, 2.87), (.0, 2.70)]
layered_plate(lt, "LT_tie_tip", TIP, floor_front, [(+.03, 1.0, 1.0), (-.11, 1.0, 1.0)], sh_tie, {"recipe": "tie tip over the belt (continues the blade)", "class": "observed"})
solid_box(lt, "LT_fly_seam", -.012, .012, floor_front(0, 2.2) - .02, floor_front(0, 2.2) + .03, 1.96, 2.55, "TrouserShadow", {"recipe": "fly seam", "class": "extrapolated"})

# ---- legs: trousers (UpperLeg), straight leg + turn-up cuff (LowerLeg), dress shoes (Foot) -------------------------------------------------
LEGX = 0.93                                   # authoring centre; the leg parts are moved/narrowed to X=+-0.80 by xf (revision 5)
LEGN = 0.80
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    hip, knee, ank = JV[side + "Hip"], JV[side + "Knee"], JV[side + "Ankle"]
    _lx = lambda p, s=s: V((s * LEGN + (p.x - s * LEGX) * .84, p.y * .92, p.z))
    ul = PM(side + "UpperLeg", hip, xf=lambda p, s=s: (lambda q: V((q.x, q.y, 1.30 + (q.z - 1.30) * (1.16 / 1.04))))(_lx(V(p))))
    rings = [ring8(.755, -.69, .69, .11, s * LEGX, 0, 1.30), ring8(.795, -.725, .725, .12, s * LEGX, 0, 1.42), ring8(.82, -.75, .75, .12, s * LEGX, 0, 2.20), ring8(.78, -.70, .70, .10, s * LEGX, 0, 2.34)]   # lower rings inset by .015 vs the LowerLeg (no coplanar surfaces)
    loft(ul, "UL_trouser_" + side, rings, sh_trouser, meta={"recipe": "trouser leg W1.62..1.64 x D1.48, hip hidden under the jacket", "class": "measured"})
    solid_box(ul, "UL_crease_" + side, s * LEGX - .016, s * LEGX + .016, -.765, -.735, 1.50, 2.18, "TrouserLight", {"recipe": "front trouser crease", "class": "extrapolated"})
    ll = PM(side + "LowerLeg", knee, xf=lambda p, s=s: _lx(V(p)))
    solid_box(ll, "LL_crease_" + side, s * LEGX - .016, s * LEGX + .016, -.775, -.745, 1.02, 1.45, "TrouserLight", {"recipe": "front trouser crease continues over the shin", "class": "extrapolated"})
    secs = [(1.45, .81, .74), (1.20, .80, .73), (0.98, .79, .72), (0.60, .79, .72)]
    loft(ll, "LL_trouser_" + side, [ring8(a, -.02 - d, -.02 + d, .11, s * LEGX, 0, h) for h, a, d in secs], sh_trouser, meta={"recipe": "straight trouser leg W1.60 x D1.46", "class": "measured"})
    cuff = [ring8(.835, -.02 - .765, -.02 + .765, .11, s * LEGX, 0, h) for h in (0.66, 0.70, 0.96, 1.00)]
    cuff[0] = ring8(.80, -.02 - .73, -.02 + .73, .10, s * LEGX, 0, 0.66)
    loft(ll, "LL_cuff_" + side, cuff, sh_const("Trouser"), band_tiles={2: "TrouserLight"}, meta={"recipe": "turn-up cuff H.66..1.00, 0.045 proud, lighter fold edge", "class": "observed"})

    th = s * 7.0
    _rot = rot_xf(ank, th)
    ft = PM(side + "Foot", ank, xf=lambda p, s=s, _rot=_rot: _rot(V((s * LEGN + (V(p).x - s * LEGX) * .92, V(p).y, V(p).z))))
    cx = s * LEGX
    sole = [ring8(.66, -1.40, .58, .12, cx, 0, 0.0), ring8(.73, -1.50, .63, .13, cx, 0, .10), ring8(.73, -1.50, .63, .13, cx, 0, .30), ring8(.68, -1.44, .60, .12, cx, 0, .38)]
    loft(ft, "FT_sole_" + side, sole, sh_sole, band_tiles={1: "SoleLight"}, meta={"recipe": "sole W1.44 x D2.10 x H.27, bevel .12, welt band", "class": "measured+extrapolated"})

    def ring_xh(f, w, h0, h1, c, cx=cx):
        a = w / 2
        pts = [(-a + c, h0), (a - c, h0), (a, h0 + c), (a, h1 - c), (a - c, h1), (-a + c, h1), (-a, h1 - c), (-a, h0 + c)]
        return [V((cx + x, -f, h)) for x, h in pts]
    UP = [(-.56, .72, 1.22, .16), (-.30, .79, 1.34, .18), (.30, .78, 1.40, .18), (.80, .70, 1.42, .18), (1.15, .58, 1.38, .16), (1.40, .48, 1.22, .14), (1.50, .38, 1.04, .06)]
    loft(ft, "FT_upper_" + side, [ring_xh(f, w, .26, top, c) for f, top, w, c in UP], sh_shoe, meta={"recipe": "oversized dress-shoe block, heel/collar H.72..79 falling to a faceted toe H.38", "class": "measured+extrapolated"})
    patch_box(ft, "FT_top_facet_" + side, cx, .72, .70, .80, 1.00, .02, "ShoeLight", embed=.01, meta={"recipe": "flat lighter top facet", "class": "observed"})
    prism_poly(ft, "FT_toe_shine_" + side, [Bl(cx - .12, 1.12, .60), Bl(cx + .12, 1.12, .60), Bl(cx, 1.30, .55)], V((0, 0, .045)), sh_const("SilverLight"), {"recipe": "small silver facet highlight on the toe top", "class": "observed"})
    solid_box(ft, "FT_heel_band_" + side, cx - .55, cx + .55, .52, .64, .14, .36, "SoleLight", {"recipe": "heel block band", "class": "extrapolated"})


# ---- revision 3 details ----------------------------------------------------------------------------------------------------------
# jacket hip pocket flaps (both sides; the right one frames the hand) + back vent seam
for sx, nm in ((-1, "R"), (1, "L")):
    layered_plate(lt, "LT_pocket_flap_" + nm, [(sx * .72, 2.58), (sx * 1.36, 2.58), (sx * 1.36, 2.38), (sx * .72, 2.38)], tfront, [(+.05, 1.0, 1.0), (-.055, 1.0, 1.0)], sh_const("NavyShadow"), {"recipe": "hip pocket flap", "class": "extrapolated"})
    layered_plate(lt, "LT_pocket_flap_edge_" + nm, [(sx * .72, 2.40), (sx * 1.36, 2.40), (sx * 1.36, 2.375), (sx * .72, 2.375)], tfront, [(+.05, 1.0, 1.0), (-.07, 1.0, 1.0)], sh_const("NavyLight"), {"recipe": "lighter lower edge of the flap", "class": "extrapolated"})
solid_box(lt, "LT_back_vent", -.014, .014, tback(0, 2.5) - .02, tback(0, 2.5) + .028, 2.22, 2.88, "NavyDeep", {"recipe": "centre back vent seam (inferred, one thin seam only)", "class": "extrapolated"})
# navy jacket collar rolling around the back half of the neck (the white shirt collar stays inside it)
loft(ut, "UT_back_collar", [ring8(.70, -.02, .56, .12, 0, 0, h) for h in (4.80, 4.88)] + [ring8(.64, -.02, .50, .10, 0, 0, 5.06)], sh_const("NavyLight"), meta={"recipe": "back collar roll (front edge F-.02, behind the neck)", "class": "extrapolated"})
