# ----------------------------------------------------------------------------------------------
# arms: navy sleeves (shared mitre contour at the elbow), white cuffs, hands; left wrist watch
# ----------------------------------------------------------------------------------------------
UPPER_SEC = [(0.0, 1.30, 1.30), (.28, 1.36, 1.34), (.70, 1.22, 1.18), (1.0, 1.12, 1.08)]   # D +.04 at the shoulder so the sleeve back never coincides with the jacket back
LOWER_SEC = [(0.0, 1.12, 1.08), (.45, 1.04, 1.00), (.80, .98, .94), (1.0, .96, .92)]
ARM_C = .20
SLEEVE_END = .80
OVERLAP = .04
ARM_AX = {}
ELBOW_RING = {}
HAND_AX = {}
HAND_LEN = .96
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    S, E, W_ = JV[side + "Shoulder"], JV[side + "Elbow"], JV[side + "Wrist"]
    ax1, ax2 = AxisG(S, E), AxisG(E, W_)
    ARM_AX[side] = (ax1, ax2)
    N = (ax1.A + ax2.A).normalized()
    K = []
    for x, y in ax1.corners(UPPER_SEC[-1][1], UPPER_SEC[-1][2], ARM_C):
        p = E + ax1.U * x + ax1.W * y
        K.append(p - ax1.A * (((p - E).dot(N)) / ax1.A.dot(N)))
    ELBOW_RING[side] = K
    ua = PM(side + "UpperArm", S)
    t0 = -OVERLAP / ax1.L
    rings = [ax1.ring(t0, UPPER_SEC[0][1], UPPER_SEC[0][2], ARM_C)] + [ax1.ring(t, w, d, ARM_C) for t, w, d in UPPER_SEC[1:-1]] + [K]
    loft(ua, "UA_sleeve_" + side, rings, sh_navy, meta={"recipe": "angular jacket sleeve W1.30->1.12, chamfer .20, elbow end = shared mitre contour", "class": "measured+extrapolated"})
    la = PM(side + "LowerArm", E)
    ts = [.14, .45, SLEEVE_END]
    lr = [ax2.ring(t, *sec_at(LOWER_SEC, t), ARM_C) for t in ts]
    best = min(range(8), key=lambda sh: sum((K[k] - lr[0][(k + sh) % 8]).length for k in range(8)))
    lr = [[r[(k + best) % 8] for k in range(8)] for r in lr]
    loft(la, "LA_sleeve_" + side, [K] + lr, sh_navy, meta={"recipe": "forearm sleeve W1.12->.98, ends at t=.80; ring order shift %d" % best, "class": "measured+extrapolated"})
    cuffs = [ax2.ring(t, w, d, .12) for t, w, d in ((SLEEVE_END - .03, .86, .82), (SLEEVE_END + .03, .86, .82), (1.0, .86, .82), (1.0 + OVERLAP / ax2.L, .80, .76))]
    loft(la, "LA_cuff_" + side, cuffs, sh_shirt, meta={"recipe": "white shirt cuff W.86 x .82, ~.26 visible beyond the sleeve", "class": "observed"})
    # sleeve buttons on the outer face (two tiny dark blocks)
    for k, t in enumerate((.60, .70)):
        abox(la, "LA_cuff_button_%s_%d" % (side, k + 1), ax2, t, t + .045, s * (.5 * sec_at(LOWER_SEC, t)[0] - .01), s * (.5 * sec_at(LOWER_SEC, t)[0] + .035), -.07, .07, "Button", {"recipe": "tiny dark sleeve button", "class": "observed"})

# ---- hands: large square hands built along the forearm direction ---------------------------------------------------------------------
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    Wp = JV[side + "Wrist"]
    dirv = RHAND_DIR if side == "Right" else (JV[side + "Wrist"] - JV[side + "Elbow"]).normalized()
    hx = AxisG(Wp, Wp + dirv * HAND_LEN)
    HAND_AX[side] = hx
    hp = PM(side + "Hand", Wp)
    DK = .62 if side == "Right" else 1.0      # the pocket hand is thinner front-to-back so that it disappears inside the jacket
    rings = [hx.ring(-.06, .64, .58 * DK, .10), hx.ring(.30, .68, .62 * DK, .11), hx.ring(.44, .94, .90 * DK, .15), hx.ring(.94, .96, .90 * DK, .16), hx.ring(1.0, .80, .76 * DK, .13)]
    loft(hp, "HAND_fist_" + side, rings, sh_skin_arm, meta={"recipe": "square fist .96 x .90 x %.2f along the forearm, wrist neck .64 x .58" % (HAND_LEN * .66), "class": "measured+extrapolated"})
    # thumb block on the inner side (toward the body)
    if side == "Left": abox(hp, "HAND_thumb_" + side, hx, .50, .92, -s * .50, -s * .36, -.34, .12, "SkinLight", {"recipe": "thumb block on the inner side, overlaps the fist", "class": "extrapolated"})
    # knuckle creases on the outer/front face (+W): four stacked finger blocks read as three crease lines
    for k, t in enumerate((.60, .72, .84) if side == "Left" else ()):
        abox(hp, "HAND_crease_%s_%d" % (side, k + 1), hx, t, t + .028, -.40, .40, .445, .465, "SkinShadow", {"recipe": "finger crease", "class": "observed"})
    if side == "Left": abox(hp, "HAND_knuckle_band_" + side, hx, .46, .94, -.47, .47, .435, .455, "SkinLight", {"recipe": "lighter finger-top band", "class": "extrapolated"})

# left wrist watch (revision 4, after the turnaround close-up): gold octagonal case with a black dial, 12 tick marks, two hands, crown, gold link bracelet
hxl = HAND_AX["Left"]
lh = PARTS["LeftHand"]
# watch face frame: the hand frame rotated by -160 deg about the hand axis (dial faces front-down-outward, towards the camera; set in the live Blender scene via MCP)
_wa = math.radians(-160)
hxw = AxisG(hxl.P0, hxl.P1)
hxw.U, hxw.W = hxl.U * math.cos(_wa) + hxl.W * math.sin(_wa), hxl.W * math.cos(_wa) - hxl.U * math.sin(_wa)
WT_C = .17                                    # case centre along the hand axis (fraction of its length)


def oct_ring(ax, tc, r, y, rot=22.5):
    return [ax.pt(tc + r * math.cos(math.radians(rot + 45 * k)) / ax.L, r * math.sin(math.radians(rot + 45 * k)), y) for k in range(8)]


def bar(ax, cid, tc, xc, length, width, ang_deg, y0, y1, tile):
    """thin rectangular bar in the (axis, U) plane of the watch face, centre (tc, xc), rotated by ang_deg, between face offsets y0..y1"""
    a_ = math.radians(ang_deg)
    dt, dx = math.cos(a_), math.sin(a_)
    nt, nx = -dx, dt
    pts = []
    for sl, sw in ((-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)):
        pts.append((tc + (dt * sl * length + nt * sw * width) / ax.L, xc + dx * sl * length + nx * sw * width))
    r0 = [ax.pt(t_, x_, y0) for t_, x_ in pts]
    r1 = [ax.pt(t_, x_, y1) for t_, x_ in pts]
    loft(lh, cid, [r0, r1], tile, meta={"recipe": "watch hand / tick", "class": "observed"})


links = [hxl.ring(t, .84, .78, .13) for t in (-.03, .02, .07, .12, .17, .22, .27, .32, .37)]
loft(lh, "WATCH_bracelet", links, sh_gold, band_tiles={0: "GoldShadow", 2: "GoldShadow", 4: "GoldShadow", 6: "GoldShadow"}, meta={"recipe": "gold link bracelet W.84 x .78, 4 link gaps", "class": "observed"})
loft(lh, "WATCH_case", [oct_ring(hxw, WT_C, .40, .36), oct_ring(hxw, WT_C, .40, .50), oct_ring(hxw, WT_C, .35, .57)], sh_gold, meta={"recipe": "octagonal gold case r.40, bevelled top", "class": "observed"})
loft(lh, "WATCH_dial", [oct_ring(hxw, WT_C, .27, .55), oct_ring(hxw, WT_C, .27, .595)], "WatchDial", meta={"recipe": "black octagonal dial inset into the case", "class": "observed"})
for k in range(12):
    a_ = math.radians(30 * k)
    big = k % 3 == 0
    bar(hxw, "WATCH_tick_%d" % k, WT_C + .215 * math.cos(a_) / hxl.L, .215 * math.sin(a_), .06 if big else .035, .03 if big else .02, math.degrees(a_), .59, .615, "WatchTick")
bar(hxw, "WATCH_hand_hour", WT_C, 0.0, .24, .035, 60, .595, .62, "GoldLight")
bar(hxw, "WATCH_hand_minute", WT_C, 0.0, .34, .025, -35, .60, .635, "GoldLight")
abox(lh, "WATCH_crown", hxw, WT_C - .035, WT_C + .035, .385, .46, .40, .50, "Gold", {"recipe": "crown on the case side", "class": "observed"})
