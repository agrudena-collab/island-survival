# ----------------------------------------------------------------------------------------------
# torso (long ivory jacket, black open-neck shirt window, gold buttons, pocket square), belt, pelvis, trousers, chunky shoes
# ----------------------------------------------------------------------------------------------
FLOOR_IN = 0.10                                   # depth of the shirt / trouser window below the jacket surface
OPEN_UP = [(-1.00, 4.90), (-.82, 4.35), (-.66, 3.75), (-.57, 3.05), (-.56, 2.80), (.56, 2.80), (.57, 3.05), (.66, 3.75), (.82, 4.35), (1.00, 4.90)]
OPEN_LOW = [(-.56, 2.80), (-.58, 1.90), (.58, 1.90), (.56, 2.80)]


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


# ---- UpperTorso: ivory jacket shell with the V window (black shirt floor), lapels, collar flaps, buttons, pocket square -------------------------
ut = PM("UpperTorso", JV["Waist"])
bm = loft_bm([row_ring(r) for r in UPPER_ROWS], sh_ivory)
bm = cut_window(bm, OPEN_UP, "Shirt", "IvoryShadow")
ut.append_bm("UT_jacket_shell", bm, None, {"recipe": "7-row octagon loft, V window (floor .10 below the surface) for the black open-neck shirt", "class": "observed+extrapolated"})
bm.free()
for s, nm in ((-1, "R"), (1, "L")):
    lap = [(s * 1.00, 4.52), (s * .82, 4.35), (s * .66, 3.75), (s * .57, 3.05), (s * .90, 3.10), (s * 1.02, 3.75), (s * 1.24, 4.28), (s * 1.40, 4.50)]      # revision 5: lapels end below the chin, no vertical sheet above the torso
    layered_plate(ut, "UT_lapel_" + nm, lap, tfront, [(+.05, 1.0, 1.0), (-.075, 1.0, 1.0)], sh_const("IvoryLight"), {"recipe": "angular notch lapel plate .075 proud", "class": "observed"})
    layered_plate(ut, "UT_lapel_peak_" + nm, [(s * 1.08, 4.46), (s * 1.38, 4.48), (s * 1.30, 4.34), (s * 1.12, 4.30)], tfront, [(+.05, 1.0, 1.0), (-.105, 1.0, 1.0)], sh_const("Ivory"), {"recipe": "lapel peak facet", "class": "extrapolated"})
    flap = [(s * .12, 4.40), (s * .74, 4.42), (s * .62, 3.95), (s * .34, 4.12)]      # shirt collar flaps lie on the chest below the chin (no intersection with the head)
    layered_plate(ut, "UT_collar_flap_" + nm, flap, floor_front, [(+.03, 1.0, 1.0), (-.08, 1.0, 1.0)], sh_const("ShirtLight"), {"recipe": "open black shirt collar flap on the shirt floor", "class": "observed"})
layered_plate(ut, "UT_placket", [(-.035, 4.40), (.035, 4.40), (.035, 2.80), (-.035, 2.80)], floor_front, [(+.03, 1.0, 1.0), (-.045, 1.0, 1.0)], sh_const("ShirtLight"), {"recipe": "shirt placket strip", "class": "extrapolated"})
for k, hh in enumerate((3.80, 3.27)):
    fy = floor_front(0, hh)
    cyl_y(ut, "UT_shirt_button_%d" % (k + 1), 0.0, hh, fy + .02, fy - .075, .075, 10, sh_gold, {"recipe": "gold shirt button (two visible in the source)", "class": "observed"})
for k, sx in enumerate((-1, 1)):
    bx, bh = sx * .74, 3.05
    fy = tfront(bx, bh)
    cyl_y(ut, "UT_jacket_button_%d" % (k + 1), bx, bh, fy + .03, fy - .10, .115, 12, sh_gold, {"recipe": "gold jacket button on the front panel edge", "class": "observed"})
layered_plate(ut, "UT_pocket_welt", [(1.00, 3.92), (1.50, 3.92), (1.50, 3.87), (1.00, 3.87)], tfront, [(+.05, 1.0, 1.0), (-.055, 1.0, 1.0)], sh_const("IvoryShadow"), {"recipe": "breast pocket welt (anatomical left)", "class": "observed"})
layered_plate(ut, "UT_pocket_square", [(1.06, 3.90), (1.46, 3.90), (1.40, 4.16), (1.27, 4.00), (1.14, 4.18)], tfront, [(+.05, 1.0, 1.0), (-.10, 1.0, 1.0)], sh_gold, {"recipe": "small folded gold pocket square, two points", "class": "observed"})

# ---- LowerTorso: long jacket fronts (H2.00..2.80) with the trouser window, belt, gold buckle, hip flaps, pelvis ---------------------------------
lt = PM("LowerTorso", JV["Root"])
bm = loft_bm([row_ring(r) for r in LOWER_ROWS], sh_ivory)
bm = cut_window(bm, OPEN_LOW, "Ivory", "IvoryShadow")
lt.append_bm("LT_jacket_skirt", bm, None, {"recipe": "long jacket skirt rows H2.00..2.80 with the trouser window", "class": "observed+extrapolated"})
bm.free()
PEL = [(1.85, 2.60, .56, -.52, .14), (2.00, 3.00, .70, -.64, .14), (2.15, 3.00, .72, -.66, .13), (2.35, 2.90, .70, -.64, .12)]
loft(lt, "LT_pelvis_trousers", [row_ring((h, w, -ff, -fb, c)) for h, w, ff, fb, c in PEL], sh_ivory, meta={"recipe": "trouser seat block H1.85..2.35", "class": "extrapolated"})
layered_plate(lt, "LT_belt", [(-.95, 2.83), (.95, 2.83), (.95, 2.52), (-.95, 2.52)], floor_front, [(+.04, 1.0, 1.0), (-.045, 1.0, 1.0)], sh_belt, {"recipe": "dark brown belt band H2.52..2.83 across the window", "class": "observed"})
BUCK_F = floor_front(0, 2.67) - .045
for nm, x0, x1, h0, h1 in (("L", -.34, -.22, 2.49, 2.86), ("R", .22, .34, 2.49, 2.86), ("T", -.34, .34, 2.74, 2.86), ("B", -.34, .34, 2.49, 2.61)):
    solid_box(lt, "LT_buckle_%s" % nm, x0, x1, BUCK_F - .07, BUCK_F + .05, h0, h1, "Gold" if nm in "LR" else "GoldLight", {"recipe": "rectangular gold buckle frame (4 bars)", "class": "observed"})
solid_box(lt, "LT_buckle_prong", -.04, .04, BUCK_F - .05, BUCK_F + .05, 2.58, 2.78, "GoldShadow", {"recipe": "buckle tongue", "class": "extrapolated"})
solid_box(lt, "LT_fly_seam", -.012, .012, floor_front(0, 2.2) - .02, floor_front(0, 2.2) + .03, 1.92, 2.50, "IvoryShadow", {"recipe": "fly seam", "class": "extrapolated"})
for sx, nm in ((-1, "R"), (1, "L")):
    layered_plate(lt, "LT_pocket_flap_" + nm, [(sx * .75, 2.50), (sx * 1.38, 2.50), (sx * 1.38, 2.28), (sx * .75, 2.28)], tfront, [(+.05, 1.0, 1.0), (-.05, 1.0, 1.0)], sh_const("IvoryShadow"), {"recipe": "hip pocket flap", "class": "extrapolated"})
solid_box(lt, "LT_back_vent", -.014, .014, tback(0, 2.4) - .02, tback(0, 2.4) + .028, 2.02, 2.78, "IvoryDeep", {"recipe": "centre back vent seam (inferred, neutral)", "class": "extrapolated"})

# ---- legs: wide ivory trousers (UpperLeg), straight leg + turn-up cuff (LowerLeg), chunky white shoes on dark soles (Foot) -------------------
LEGX = 0.88
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    hip, knee, ank = JV[side + "Hip"], JV[side + "Knee"], JV[side + "Ankle"]
    ul = PM(side + "UpperLeg", hip)
    rings = [ring8(.70, -.72, .72, .12, s * LEGX, 0, 1.25), ring8(.715, -.74, .74, .12, s * LEGX, 0, 1.38), ring8(.74, -.76, .76, .12, s * LEGX, 0, 2.30), ring8(.70, -.72, .72, .10, s * LEGX, 0, 2.42)]
    loft(ul, "UL_trouser_" + side, rings, sh_ivory, meta={"recipe": "wide trouser leg W1.35 x D1.40, hip hidden under the jacket", "class": "observed+extrapolated"})
    solid_box(ul, "UL_crease_" + side, s * LEGX - .016, s * LEGX + .016, -.735, -.705, 1.45, 2.26, "IvoryShadow", {"recipe": "front trouser crease", "class": "extrapolated"})
    ll = PM(side + "LowerLeg", knee)
    secs = [(1.40, .725, .73), (1.10, .715, .72), (0.92, .705, .71), (0.76, .705, .71)]
    loft(ll, "LL_trouser_" + side, [ring8(a, -.02 - d, -.02 + d, .11, s * LEGX, 0, h) for h, a, d in secs], sh_ivory, meta={"recipe": "straight trouser leg", "class": "observed+extrapolated"})
    solid_box(ll, "LL_crease_" + side, s * LEGX - .016, s * LEGX + .016, -.755, -.725, 1.00, 1.30, "IvoryShadow", {"recipe": "front crease over the shin", "class": "extrapolated"})
    cuff = [ring8(.74, -.02 - .75, -.02 + .75, .10, s * LEGX, 0, 0.76)] + [ring8(.765, -.02 - .765, -.02 + .765, .11, s * LEGX, 0, h) for h in (0.80, 1.06, 1.10)]
    loft(ll, "LL_cuff_" + side, cuff, sh_const("Ivory"), band_tiles={2: "IvoryLight"}, meta={"recipe": "turn-up cuff H.62..0.96, lighter fold edge", "class": "extrapolated"})

    th = s * 6.0
    ft = PM(side + "Foot", ank, xf=rot_xf(ank, th))
    cx = s * LEGX
    sole = [ring8(.72, -1.66, .72, .14, cx, 0, 0.0), ring8(.80, -1.76, .76, .16, cx, 0, .10), ring8(.80, -1.76, .76, .16, cx, 0, .26), ring8(.76, -1.70, .72, .14, cx, 0, .34)]
    loft(ft, "FT_sole_" + side, sole, sh_const("Sole"), band_tiles={1: "SoleLight"}, meta={"recipe": "dark chunky sole slab H0..0.30 (thick, as in the source)", "class": "observed+extrapolated"})

    def ring_xh(f, w, h0, h1, c, cx=cx):
        a = w / 2
        pts = [(-a + c, h0), (a - c, h0), (a, h0 + c), (a, h1 - c), (a - c, h1), (-a + c, h1), (-a, h1 - c), (-a, h0 + c)]
        return [V((cx + x, -f, h)) for x, h in pts]
    UP = [(-.66, .86, 1.46, .20), (-.30, .88, 1.60, .22), (.30, .84, 1.66, .22), (.85, .76, 1.66, .22), (1.22, .68, 1.60, .20), (1.52, .58, 1.42, .17), (1.70, .46, 1.10, .10)]
    loft(ft, "FT_upper_" + side, [ring_xh(f, w, .30, top, c) for f, top, w, c in UP], sh_shoe, meta={"recipe": "oversized chunky white shoe block, heel/collar H.86..92 falling to a faceted toe H.42", "class": "observed+extrapolated"})
    patch_box(ft, "FT_top_facet_" + side, cx, .70, .80, .90, 1.20, .02, "ShoeLight", embed=.01, meta={"recipe": "flat lighter top facet", "class": "observed"})
    solid_box(ft, "FT_toe_band_" + side, cx - .52, cx + .52, -1.64, -1.58, .34, .52, "ShoeShadow", {"recipe": "toe cap shadow band", "class": "extrapolated"})
    solid_box(ft, "FT_heel_band_" + side, cx - .62, cx + .62, .60, .72, .30, .58, "ShoeShadow", {"recipe": "heel block band", "class": "extrapolated"})
