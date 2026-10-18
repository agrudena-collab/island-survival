# ----------------------------------------------------------------------------------------------
# arms: broad blocky ivory sleeves (shared mitre contour at the elbow), black shirt cuffs, gold sleeve buttons, fists; left wrist watch
# ----------------------------------------------------------------------------------------------
UPPER_SEC = [(0.0, 1.70, 1.50), (.30, 1.76, 1.54), (.75, 1.56, 1.40), (1.0, 1.44, 1.30)]
LOWER_SEC = [(0.0, 1.38, 1.30), (.50, 1.32, 1.24), (.78, 1.26, 1.20), (1.0, 1.24, 1.18)]
ARM_C = .24                       # large chamfer: blocky, faceted shoulders as in the source
SLEEVE_END = .76
OVERLAP = .04
ARM_AX = {}
ELBOW_RING = {}
HAND_AX = {}
HAND_LEN = .90
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
    loft(ua, "UA_sleeve_" + side, rings, sh_ivory, meta={"recipe": "broad blocky sleeve W1.60->1.38, chamfer .24, elbow end = shared mitre contour", "class": "observed+extrapolated"})
    abox(ua, "UA_button_" + side, ax1, .74, .74 + .06 / ax1.L, s * (UPPER_SEC[-1][1] / 2 - .02), s * (UPPER_SEC[-1][1] / 2 + .05), -.10, .10, "Gold", {"recipe": "small gold dot on the outer sleeve (source: right sleeve)", "class": "observed"})
    la = PM(side + "LowerArm", E)
    ts = [.14, .50, SLEEVE_END]
    lr = [ax2.ring(t, *sec_at(LOWER_SEC, t), ARM_C) for t in ts]
    best = min(range(8), key=lambda sh: sum((K[k] - lr[0][(k + sh) % 8]).length for k in range(8)))
    lr = [[r[(k + best) % 8] for k in range(8)] for r in lr]
    loft(la, "LA_sleeve_" + side, [K] + lr, sh_ivory, meta={"recipe": "forearm sleeve block W1.38->1.26 ends at t=.76; ring order shift %d" % best, "class": "observed+extrapolated"})
    cuffs = [ax2.ring(t, w, d, .12) for t, w, d in ((SLEEVE_END - .03, 1.04, .98), (SLEEVE_END + .03, 1.04, .98), (1.0, 1.04, .98), (1.0 + OVERLAP / ax2.L, .96, .90))]
    loft(la, "LA_cuff_" + side, cuffs, sh_shirt, meta={"recipe": "black shirt cuff W1.04 x .98, ~.29 visible beyond the sleeve", "class": "observed"})
    abox(la, "LA_button_" + side, ax2, .52, .52 + .06 / ax2.L, s * (sec_at(LOWER_SEC, .52)[0] / 2 - .02), s * (sec_at(LOWER_SEC, .52)[0] / 2 + .05), -.10, .10, "Gold", {"recipe": "small gold sleeve dot", "class": "observed"})

# ---- hands: closed fists built along their own axis (right: hanging, holds the case handle; left: rests on the hip) ------------------------------
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    Wp = JV[side + "Wrist"]
    dirv = (JV[side + "Wrist"] - JV[side + "Elbow"]).normalized()      # the fist continues the forearm axis: cuff and fist exit the sleeve in line (revision 5)
    hx = AxisG(Wp, Wp + dirv * HAND_LEN)
    HAND_AX[side] = hx
    hp = PM(side + "Hand", Wp)
    rings = [hx.ring(-.06, .72, .64, .10), hx.ring(.20, .76, .68, .11), hx.ring(.30, 1.00, .94, .15), hx.ring(.94, 1.02, .94, .16), hx.ring(1.0, .86, .80, .13)]
    loft(hp, "HAND_fist_" + side, rings, sh_skin_arm, meta={"recipe": "square closed fist 1.02 x .94 x %.2f, wrist neck .72 x .64" % (HAND_LEN * .64), "class": "observed+extrapolated"})
    for k, t in enumerate((.50, .64, .78)):
        abox(hp, "HAND_crease_%s_%d" % (side, k + 1), hx, t, t + .028, -.42, .42, .465, .485, "SkinShadow", {"recipe": "finger crease", "class": "observed"})
    abox(hp, "HAND_knuckle_band_" + side, hx, .34, .94, -.50, .50, .455, .475, "SkinLight", {"recipe": "lighter finger-top band", "class": "extrapolated"})
    if side == "Left":
        abox(hp, "HAND_thumb_Left", hx, .44, .90, -s * .54, -s * .38, -.34, .12, "SkinLight", {"recipe": "thumb block on the inner side, overlaps the fist", "class": "extrapolated"})

# ---- left wrist watch (visible in the source on the wrist at the hip): gold octagonal case, cream dial, ticks, hands, crown, black strap ------------
hxl = HAND_AX["Left"]
lh = PARTS["LeftHand"]
WATCH_NORMAL = V((-0.35, -0.90, 0.20))        # Blender coords: forward and slightly towards the midline - the dial faces the source camera (right-front)
_w = (WATCH_NORMAL - hxl.A * WATCH_NORMAL.dot(hxl.A)).normalized()
hxw = AxisG(hxl.P0, hxl.P1)
hxw.W = _w
hxw.U = _w.cross(hxl.A).normalized()
WT_C = .20                                    # case centre along the hand axis (fraction of its length)


def oct_ring(ax, tc, r, y, rot=22.5):
    return [ax.pt(tc + r * math.cos(math.radians(rot + 45 * k)) / ax.L, r * math.sin(math.radians(rot + 45 * k)), y) for k in range(8)]


def bar(ax, cid, tc, xc, length, width, ang_deg, y0, y1, tile):
    a_ = math.radians(ang_deg)
    dt, dx = math.cos(a_), math.sin(a_)
    nt, nx = -dx, dt
    pts = []
    for sl, sw in ((-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)):
        pts.append((tc + (dt * sl * length + nt * sw * width) / ax.L, xc + dx * sl * length + nx * sw * width))
    r0 = [ax.pt(t_, x_, y0) for t_, x_ in pts]
    r1 = [ax.pt(t_, x_, y1) for t_, x_ in pts]
    loft(lh, cid, [r0, r1], tile, meta={"recipe": "watch hand / tick", "class": "extrapolated"})


loft(lh, "WATCH_strap", [hxl.ring(t, .84, .78, .13) for t in (-.03, .06, .15, .24, .33, .40)], sh_const("Strap"), band_tiles={0: "CaseLight", 2: "CaseLight", 4: "CaseLight"}, meta={"recipe": "black strap around the wrist neck W.84 x .78 (source shows a black strap)", "class": "observed"})
loft(lh, "WATCH_case", [oct_ring(hxw, WT_C, .40, .36), oct_ring(hxw, WT_C, .40, .50), oct_ring(hxw, WT_C, .35, .58)], sh_gold, meta={"recipe": "octagonal gold case r.40, bevelled top", "class": "observed"})
loft(lh, "WATCH_dial", [oct_ring(hxw, WT_C, .27, .56), oct_ring(hxw, WT_C, .27, .60)], "WatchDial", meta={"recipe": "cream dial (dial design is a proposal)", "class": "design-proposal"})
for k in range(12):
    a_ = math.radians(30 * k)
    big = k % 3 == 0
    bar(hxw, "WATCH_tick_%d" % k, WT_C + .215 * math.cos(a_) / hxl.L, .215 * math.sin(a_), .06 if big else .035, .03 if big else .02, math.degrees(a_), .595, .62, "WatchTick")
bar(hxw, "WATCH_hand_hour", WT_C, 0.0, .22, .035, 60, .60, .625, "GoldShadow")
bar(hxw, "WATCH_hand_minute", WT_C, 0.0, .32, .025, -35, .605, .64, "GoldShadow")
abox(lh, "WATCH_crown", hxw, WT_C - .045, WT_C + .045, .385, .48, .40, .52, "Gold", {"recipe": "crown on the case side", "class": "extrapolated"})
for sg, nm in ((-1, "a"), (1, "b")):
    abox(lh, "WATCH_lug_" + nm, hxw, WT_C + sg * (.40 + .06) / hxl.L - .12 / hxl.L, WT_C + sg * (.40 + .06) / hxl.L + .12 / hxl.L, -.30, .30, .32, .50, "Gold", {"recipe": "lug where the strap meets the case", "class": "extrapolated"})
for k in range(8):
    phi = 45 * k + 22.5
    bar(hxw, "WATCH_bezel_bar_%d" % k, WT_C + .335 * math.cos(math.radians(phi)) / hxl.L, .335 * math.sin(math.radians(phi)), .27, .075, phi + 90, .575, .63, "GoldLight")
