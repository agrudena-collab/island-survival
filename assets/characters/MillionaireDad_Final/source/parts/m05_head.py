# ----------------------------------------------------------------------------------------------
# head: faceted skull, ears, square gold sunglasses with dark lenses (eyes NOT modelled: not established by the source), blocky nose,
# voluminous white moustache with curled tips, broad toothy grin, side-swept silver hair mass with grey facets (no beard)
# ----------------------------------------------------------------------------------------------
hd = PM("Head", JV["Neck"])
SKULL = [(4.42, 1.40, .78, -.70, .22), (4.64, 1.78, .95, -.84, .22), (5.00, 1.92, 1.00, -.88, .22), (5.90, 1.92, 1.00, -.88, .20), (6.05, 1.72, .88, -.80, .18)]
SK_ROWS = [(h, w, -ff, -fb, c) for h, w, ff, fb, c in SKULL]


def skull_D(x, h):
    """D coordinate of the skull front surface (front is negative D)"""
    return front_at(SK_ROWS, min(max(h, SK_ROWS[0][0]), SK_ROWS[-1][0]), x)


# revision 3: the grin is a real pocket cut into the face (depth MOUTH_IN below the surface), teeth sit inside it, the lower lip is a ridge - not a decal on the head
MOUTH_IN = .16
GX = .50                           # revision 4: shorter grin (source teeth span ~0.86 studs)
_xs = [-GX + 2 * GX * k / 12 for k in range(13)]
OPENING = [(x, 4.93 + .08 * (x / GX) ** 2) for x in _xs] + [(x, 4.56 + .18 * (x / GX) ** 2) for x in _xs[::-1]]
bm = loft_bm([ring8(w / 2, -ff, -fb, c, 0, 0, h) for h, w, ff, fb, c in SKULL], sh_skin)
_cut = plate_bm(OPENING, skull_D, [(MOUTH_IN, 1.0, 1.0), (-.40, 1.0, 1.0)], "Mouth")
bm = bm_boolean(bm, _cut)
_cut.free()
hd.append_bm("HD_skull", bm, None, {"recipe": "faceted block head W2.02 x D1.88, chin H4.42 (no beard); grin pocket cut .16 into the face (dark walls/floor)", "class": "observed+extrapolated"})
bm.free()
loft(hd, "HD_neck", cbox(Bl(0, -.02, 4.55), (.92, .82, .52), .10), sh_skin, meta={"recipe": "short neck block inside skull/torso", "class": "extrapolated"})
for s, nm in ((-1, "Right"), (1, "Left")):
    loft(hd, "HD_ear_" + nm, cbox(Bl(s * .985, -.02, 5.04), (.30, .50, .58), .10), sh_skin, meta={"recipe": "ear block", "class": "observed"})
    solid_box(hd, "HD_ear_rim_" + nm, min(s * 1.115, s * 1.150), max(s * 1.115, s * 1.150), -.20, .14, 4.84, 5.26, sh_const("SkinLight"), {"recipe": "ear helix rim", "class": "extrapolated"})
    xo = s * 1.135
    solid_box(hd, "HD_concha_" + nm, min(xo + s * .02, xo - s * .035), max(xo + s * .02, xo - s * .035), -(-.02 + .15), -(-.02 - .15), 4.86, 5.20, sh_const("EarInner"), {"recipe": "ear concha patch", "class": "observed"})


FD = 0.12                          # revision 2: the face features (glasses, nose, moustache) are lifted by this much so the grin has room below the moustache
MSX = 0.72                         # moustache x factor: 0.90 base * 0.90 correction made in the LIVE Blender scene through MCP (moustache wider than the face in the source fit)


def rect(x0, x1, h0, h1):
    return [(x0, h0), (x1, h0), (x1, h1), (x0, h1)]


# square oversized sunglasses: thick gold frames, dark lenses, bridge, temple arms
for s, nm in ((-1, "R"), (1, "L")):
    prism_xh(hd, "HD_lens_" + nm, rect(s * .18, s * .76, 5.12 + FD, 5.60 + FD), .80, 1.075, sh_const("Lens"), {"recipe": "dark square lens .58 x .48 (lens depth is a proposal)", "class": "observed+proposal"})
    prism_xh(hd, "HD_lens_shine_" + nm, [(s * .24, 5.56 + FD), (s * .46, 5.56 + FD), (s * .24, 5.34 + FD)], 1.07, 1.092, sh_const("LensShine"), {"recipe": "lens facet highlight", "class": "extrapolated"})
    prism_xh(hd, "HD_lens_streak_a_" + nm, [(s * .22, 5.50 + FD), (s * .30, 5.50 + FD), (s * .62, 5.18 + FD), (s * .54, 5.18 + FD)] if s > 0 else [(s * .54, 5.18 + FD), (s * .62, 5.18 + FD), (s * .30, 5.50 + FD), (s * .22, 5.50 + FD)], 1.07, 1.092, sh_const("LensShine"), {"recipe": "lens reflection streak", "class": "extrapolated"})
    prism_xh(hd, "HD_lens_streak_b_" + nm, [(s * .42, 5.58 + FD), (s * .46, 5.58 + FD), (s * .72, 5.30 + FD), (s * .68, 5.30 + FD)] if s > 0 else [(s * .68, 5.30 + FD), (s * .72, 5.30 + FD), (s * .46, 5.58 + FD), (s * .42, 5.58 + FD)], 1.07, 1.09, sh_const("LensShine"), {"recipe": "second lens streak", "class": "extrapolated"})
    for k, (x0, x1, h0, h1) in enumerate(((.10, .84, 5.60, 5.72), (.10, .84, 5.00, 5.12), (.10, .18, 5.12, 5.60), (.76, .84, 5.12, 5.60))):
        prism_xh(hd, "HD_frame_%s_%d" % (nm, k + 1), rect(s * x0, s * x1, h0 + FD, h1 + FD), .90, 1.15, sh_gold, {"recipe": "thick gold frame bar", "class": "observed"})
    prism_xh(hd, "HD_frame_inner_top_" + nm, rect(s * .18, s * .76, 5.55 + FD, 5.60 + FD), 1.05, 1.17, sh_const("GoldLight"), {"recipe": "light inner frame bevel", "class": "extrapolated"})
    solid_box(hd, "HD_temple_" + nm, min(s * .955, s * 1.04), max(s * .955, s * 1.04), -.92, .08, 5.44 + FD, 5.56 + FD, "Gold", {"recipe": "gold temple arm from the frame back to the ear", "class": "extrapolated"})
prism_xh(hd, "HD_bridge", rect(-.14, .14, 5.44 + FD, 5.58 + FD), .90, 1.15, sh_gold, {"recipe": "gold nose bridge", "class": "observed"})
NOSE = [(4.93 + FD, .52, 1.16, .70, .12), (5.04 + FD, .70, 1.28, .70, .18), (5.22 + FD, .66, 1.26, .70, .18), (5.36 + FD, .46, 1.12, .70, .12), (5.46 + FD, .30, 1.02, .70, .08)]   # revision 6: bigger, rounder nose
loft(hd, "HD_nose", [ring8(w / 2, -ff, -fb, c, 0, 0, h) for h, w, ff, fb, c in NOSE], sh_nose, meta={"recipe": "blocky warm peach nose, front F1.26", "class": "observed"})

# white moustache: three stacked layers per side (shadow underlayer, body, light top ridge), tips curl outward and up
MP = [(0, 4.84), (.22, 4.76), (.60, 4.74), (1.00, 4.82), (1.25, 5.02), (1.34, 5.28), (1.20, 5.36), (1.08, 5.16), (.84, 5.04), (.55, 5.06), (.25, 5.12), (0, 5.10)]
MS = [(0, 4.82), (.25, 4.74), (.62, 4.72), (1.02, 4.80), (1.20, 4.95), (1.10, 5.0), (.84, 4.92), (.55, 4.94), (.25, 4.98), (0, 4.98)]
MT = [(0, 5.08), (.25, 5.10), (.55, 5.04), (.84, 5.02), (1.06, 5.14), (1.18, 5.32), (1.12, 5.30), (1.00, 5.15), (.82, 5.08), (.55, 5.10), (.25, 5.15), (0, 5.14)]
for s, nm in ((-1, "Right"), (1, "Left")):
    def side_poly(P):
        pts = [(s * x * MSX, h + FD) for x, h in P]
        return pts if s > 0 else pts[::-1]
    prism_xh(hd, "HD_moustache_shadow_" + nm, side_poly(MS), .70, 1.12, sh_const("MoustacheShadow"), {"recipe": "moustache underlayer", "class": "observed"})
    prism_xh(hd, "HD_moustache_" + nm, side_poly(MP), .70, 1.20, sh_const("Moustache"), {"recipe": "voluminous white moustache lobe, tip curls outward and up", "class": "observed"})
    prism_xh(hd, "HD_moustache_top_" + nm, side_poly(MT), 1.14, 1.25, sh_const("MoustacheLight"), {"recipe": "light top ridge", "class": "extrapolated"})

for s_, nm in ((-1, "Right"), (1, "Left")):
    TIP = [(1.12, 5.00), (1.30, 5.18), (1.36, 5.42), (1.26, 5.46), (1.20, 5.26), (1.06, 5.10)]
    prism_xh(hd, "HD_moustache_curl_" + nm, [(s_ * x * MSX, h + FD) for x, h in TIP] if s_ > 0 else [(s_ * x * MSX, h + FD) for x, h in TIP][::-1], .90, 1.24, sh_const("MoustacheLight"), {"recipe": "extra curl facet on the moustache tip", "class": "extrapolated"})
# broad toothy grin inside the pocket: teeth recessed .05 below the face surface, two tooth rows, lower-lip ridge, smile creases
TX = .43
_xt = [-TX + 2 * TX * k / 12 for k in range(13)]
TEETH = [(x, 4.89 + .08 * (x / TX) ** 2) for x in _xt] + [(x, 4.61 + .16 * (x / TX) ** 2) for x in _xt[::-1]]
layered_plate(hd, "HD_teeth", TEETH, skull_D, [(MOUTH_IN + .02, 1.0, 1.0), (.05, 1.0, 1.0)], sh_const("Teeth"), {"recipe": "white teeth band set into the grin pocket (front .05 below the face surface)", "class": "observed"})
_mid = [(x, 4.75 + .12 * (x / TX) ** 2) for x in _xt]
layered_plate(hd, "HD_teeth_row_line", [(x, h + .011) for x, h in _mid] + [(x, h - .011) for x, h in _mid[::-1]], lambda x, h: skull_D(x, h) + .05, [(.02, 1.0, 1.0), (-.012, 1.0, 1.0)], sh_const("TeethShadow"), {"recipe": "line between the upper and lower tooth rows", "class": "extrapolated"})
for k, x in enumerate((-.34, -.22, -.11, 0.0, .11, .22, .34)):
    hb, ht = 4.62 + .16 * (x / TX) ** 2, 4.88 + .08 * (x / TX) ** 2
    layered_plate(hd, "HD_tooth_gap_%d" % k, [(x - .007, hb), (x + .007, hb), (x + .007, ht), (x - .007, ht)], lambda x_, h_: skull_D(x_, h_) + .05, [(.02, 1.0, 1.0), (-.012, 1.0, 1.0)], sh_const("TeethShadow"), {"recipe": "tooth gap line", "class": "extrapolated"})
_lip = [(x, 4.56 + .18 * (x / GX) ** 2 - .085) for x in _xs] + [(x, 4.56 + .18 * (x / GX) ** 2 + .01) for x in _xs[::-1]]
layered_plate(hd, "HD_lower_lip", _lip, skull_D, [(.04, 1.0, 1.0), (-.045, 1.0, 1.0)], sh_const("SkinLight"), {"recipe": "lower-lip ridge, proud .045, frames the bottom of the grin pocket", "class": "extrapolated"})
for s_, nm in ((-1, "Right"), (1, "Left")):
    crease = [(s_ * .58, 4.86), (s_ * .66, 4.82), (s_ * .76, 4.93), (s_ * .80, 5.08), (s_ * .74, 5.06), (s_ * .70, 4.98), (s_ * .64, 4.92)]
    layered_plate(hd, "HD_smile_crease_" + nm, crease if s_ > 0 else crease[::-1], skull_D, [(.03, 1.0, 1.0), (.01, 1.0, 1.0)], sh_const("SkinShadow"), {"recipe": "smile crease at the corner of the grin (slightly recessed)", "class": "extrapolated"})
    layered_plate(hd, "HD_cheek_ridge_" + nm, [(s_ * .56, 4.92), (s_ * .70, 4.90), (s_ * .76, 5.08), (s_ * .64, 5.10)] if s_ > 0 else [(s_ * .64, 5.10), (s_ * .76, 5.08), (s_ * .70, 4.90), (s_ * .56, 4.92)], skull_D, [(.04, 1.0, 1.0), (-.035, 1.0, 1.0)], sh_const("SkinLight"), {"recipe": "cheek bulge above the grin corner (frames the smile)", "class": "extrapolated"})

# ---------------------------------------------------------------------------------------------------------------------------
# hair: ONE shell over the whole skull + thick swept locks. Silver Hair / HairLight on top, grey facets underneath and at the sides.
# ---------------------------------------------------------------------------------------------------------------------------
HC = [(5.00, 1.40, -.05, -.82, .16), (5.25, 1.86, .10, -.98, .22), (5.65, 1.94, .35, -1.00, .22), (5.95, 1.94, 1.04, -1.00, .26), (6.12, 1.94, 1.06, -1.02, .30), (6.28, 1.76, .92, -.92, .30), (6.40, 1.30, .60, -.60, .22)]


def sh_hair_shell(n, c):
    if abs(c.x) > .85 and -.2 < -c.y < .55 and 4.95 < c.z < 5.75 and abs(n.x) > .4:
        return "HairGrey" if c.z > 5.40 else "HairGreyDark"
    if n.z < -0.30:
        return "HairGrey"
    return sh_hair(n, c)


loft(hd, "HD_hair_shell", [ring8(w / 2, -ff, -fb, c, 0, 0, h) for h, w, ff, fb, c in HC], sh_hair_shell, meta={"recipe": "single hair shell H5.00..6.40 over the whole skull; grey facets on the sides and underneath", "class": "observed+extrapolated"})


HSX = 0.84                         # hair x factor (the first fit showed the head/hair span 30 px too wide)


def lock(cid, pts, w0, w1, h0, h1, thick=1.0):
    k = 1.5 * thick
    pts = [(x * HSX, f, min(z, 6.40 - h0 * k / 2)) if z > 6.0 else (x * HSX, f, z) for x, f, z in pts]
    path = catmull([Bl(*p_) for p_ in pts], 4)
    sweep(hd, cid, path, lambda t: w0 + (w1 - w0) * t, lambda t: (h0 + (h1 - h0) * t) * k, .09, sh_hair, {"recipe": "broad swept silver lock", "class": "observed+extrapolated"})


# the big side-swept mass: from the front-right of the forehead, over the crown, falling to the character's left (viewer right, as in the source)
lock("HD_wave_1", [(-.90, .70, 5.98), (-.70, .95, 6.18), (-.15, .85, 6.30), (.45, .45, 6.28), (.95, .20, 6.10), (1.20, .20, 5.80), (1.22, .25, 5.55)], .62, .40, .32, .26)
lock("HD_wave_2", [(-1.00, .20, 5.98), (-.85, .40, 6.20), (-.30, .30, 6.30), (.30, -.15, 6.28), (.85, -.40, 6.12), (1.15, -.30, 5.85)], .58, .38, .30, .24)
lock("HD_wave_3", [(-.45, .98, 6.00), (-.20, 1.02, 6.20), (.30, .85, 6.28), (.80, .50, 6.18), (1.12, .35, 5.95), (1.16, .40, 5.70)], .52, .34, .28, .24)
lock("HD_wave_4", [(-.80, -.40, 6.18), (-.30, -.75, 6.26), (.30, -.90, 6.20), (.80, -.80, 6.00), (1.00, -.70, 5.75)], .56, .36, .28, .24)
lock("HD_wave_front_curl", [(-.95, .90, 5.92), (-.70, 1.08, 6.08), (-.30, 1.08, 6.18)], .44, .32, .28, .24)
lock("HD_curl_left_1", [(1.02, .52, 5.95), (1.20, .50, 5.70), (1.25, .45, 5.48), (1.14, .36, 5.32)], .40, .30, .30, .24)
lock("HD_curl_left_2", [(1.02, -.05, 5.90), (1.20, -.10, 5.66), (1.22, -.16, 5.42)], .38, .28, .28, .22)
lock("HD_curl_right_1", [(-1.10, .50, 5.95), (-1.30, .46, 5.70), (-1.34, .38, 5.40), (-1.24, .30, 5.10)], .46, .32, .32, .26)
lock("HD_curl_right_2", [(-1.10, -.08, 5.92), (-1.30, -.14, 5.66), (-1.34, -.22, 5.36), (-1.24, -.28, 5.08)], .44, .30, .30, .24)
lock("HD_curl_right_3", [(-1.06, .22, 5.98), (-1.26, .18, 5.76), (-1.30, .10, 5.52)], .40, .28, .28, .22)
for k, x in enumerate((-.66, -.33, 0.0, .33, .66)):
    lock("HD_back_strand_%d" % (k + 1), [(x * .98, -.88, 6.10), (x, -1.03, 5.80), (x * 1.02, -1.05, 5.45), (x * .96, -.98, 5.12)], .34, .28, .14, .12, 0.75)
