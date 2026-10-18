# ----------------------------------------------------------------------------------------------
# hard case (separate rigid prop in the RIGHT hand, ONE grip): black rectangular case, gold/brass corner and edge fittings, top handle
# Orientation (hidden-side choice): long axis along F, thin along X, hanging beside the right thigh. Locks / interior are NOT in the source: omitted.
# ----------------------------------------------------------------------------------------------
_hxR = HAND_AX["Right"]
_tbar = (2.04 - _hxR.P0.z) / (_hxR.A.z * _hxR.L)                  # parameter along the fist axis where it crosses the handle-bar height H2.04
_bar = _hxR.at(_tbar)
HANDLE_BAR = (round(_bar.x, 4), round(-_bar.y, 4), 2.04)          # handle bar centre (X, F, H): on the real fist axis, inside the closed fist (hidden)
CASE_LOGICAL = (HANDLE_BAR[0], HANDLE_BAR[1], 0.965)               # case hangs straight below the bar
CASE_T, CASE_L, CASE_H = .80, 2.70, 1.55   # thickness X, length F, height H (source: visible width ~2.35, height ~1.65 in the projection; revised after the landmark fit)
CASE_C = Bl(*CASE_LOGICAL)
cs = PM("Case", CASE_C, geo="Case_Geo")
CX, CY, CZ = CASE_C.x, CASE_C.y, CASE_C.z
hx_, hy_, hz_ = CASE_T / 2, CASE_L / 2, CASE_H / 2
loft(cs, "CASE_body", cbox((CX, CY, CZ), (CASE_T, CASE_L, CASE_H), .09), sh_case, meta={"recipe": "black rectangular hard case .80 x 2.70 x 1.55, chamfer .09", "class": "observed"})
GOLD_T = .05                               # fittings are proud by this much
# vertical gold edge bars near both short ends (both broad faces)
for sx in (-1, 1):
    for sy in (-1, 1):
        solid_box(cs, "CASE_edge_bar_%d_%d" % (sx, sy), CX + sx * (hx_ - .02), CX + sx * (hx_ + GOLD_T), CY + sy * (hy_ - .36), CY + sy * (hy_ - .20), CZ - hz_ + .02, CZ + hz_ - .02, "Gold", {"recipe": "vertical gold edge bar on the broad face", "class": "observed"})
# corner brackets (8 corners): small gold/brass cubes wrapping the edges, proud by .03
for sx in (-1, 1):
    for sy in (-1, 1):
        for sz in (-1, 1):
            cx_, cy_, cz_ = CX + sx * (hx_ - .10), CY + sy * (hy_ - .10), CZ + sz * (hz_ - .10)
            solid_box(cs, "CASE_corner_%d_%d_%d" % (sx, sy, sz), cx_ - .13, cx_ + .13, cy_ - .13, cy_ + .13, cz_ - .13, cz_ + .13, "Brass" if (sx + sy + sz) % 2 else "Gold", {"recipe": "gold/brass corner fitting", "class": "observed"})
# gold top / bottom rails on the long edges
for sx in (-1, 1):
    solid_box(cs, "CASE_rail_top_%d" % sx, CX + sx * (hx_ - .03) - .04, CX + sx * (hx_ - .03) + .04, CY - hy_ + .40, CY + hy_ - .40, CZ + hz_ - .045, CZ + hz_ + .03, "GoldShadow", {"recipe": "brass top rail", "class": "extrapolated"})
# top handle: loop (two legs + bar) in the (F, H) plane at X = hand axis; the bar passes through the closed fist
HX = HANDLE_BAR[0]
path = catmull([Bl(HX, HANDLE_BAR[1] - .42, CZ + hz_ - .04), Bl(HX, HANDLE_BAR[1] - .42, HANDLE_BAR[2] - .05), Bl(HX, HANDLE_BAR[1] - .30, HANDLE_BAR[2] + .02), Bl(HX, HANDLE_BAR[1] + .30, HANDLE_BAR[2] + .02),
                Bl(HX, HANDLE_BAR[1] + .42, HANDLE_BAR[2] - .05), Bl(HX, HANDLE_BAR[1] + .42, CZ + hz_ - .04)], 4)
sweep(cs, "CASE_handle", path, lambda t: .13, lambda t: .13, .035, sh_const("Case"), {"recipe": "black handle loop; bar H2.04 sits inside the fist", "class": "observed+extrapolated"})
for sy in (-1, 1):
    solid_box(cs, "CASE_handle_mount_%d" % sy, HX - .13, HX + .13, -(HANDLE_BAR[1] + sy * .42) - .09, -(HANDLE_BAR[1] + sy * .42) + .09, CZ + hz_ - .02, CZ + hz_ + .06, "Gold", {"recipe": "gold handle mount", "class": "extrapolated"})
