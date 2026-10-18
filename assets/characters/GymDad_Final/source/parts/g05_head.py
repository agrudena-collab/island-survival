

# ----------------------------------------------------------------------------------------------
# V2 head: bald skull, short neck, ears, oval eyes, protruding nose, curved smile, jaw-wrapping beard (all scaled by HS about the top of the skull)
# ----------------------------------------------------------------------------------------------
def sh_nose(n, c):
    if n.z < -0.55:
        return "SkinShadow"
    if n.z > 0.45:
        return "NoseLight"
    return "Nose"


def prism_bm(poly_xh, f0, f1, tile):
    """closed prism of a polygon in (X, H) swept between logical F=f0 and F=f1 (boolean cutter)"""
    n = len(poly_xh)
    P = [Bl(x, f0, h) for x, h in poly_xh] + [Bl(x, f1, h) for x, h in poly_xh]
    faces = [[k, (k + 1) % n, n + (k + 1) % n, n + k] for k in range(n)]
    faces += cap_tris2(list(range(n)), poly_xh) + cap_tris2(list(range(n, 2 * n)), poly_xh)
    return solid_tiled(P, faces, tile)


def ellipse(cx, cz, rx, rz, n=14, rot=0.0):
    c, s = math.cos(rot), math.sin(rot)
    return [(cx + rx * math.cos(2 * math.pi * k / n) * c - rz * math.sin(2 * math.pi * k / n) * s, cz + rx * math.cos(2 * math.pi * k / n) * s + rz * math.sin(2 * math.pi * k / n) * c) for k in range(n)]


hd = PM("Head", JV["Neck"], xf=head_xf)
SKULL = [(4.97, 1.66, .60, -.57, .12), (5.13, 2.00, .76, -.73, .16), (6.23, 2.00, .76, -.73, .16), (6.34, 1.80, .66, -.63, .12), (6.40, 1.34, .46, -.44, .10)]
loft(hd, "HD_skull", [ring8(w / 2, -ff, -fb, c, 0, 0, h) for h, w, ff, fb, c in SKULL], sh_skin,
     meta={"recipe": "skull W2.00 x D1.49 bevel .16 with low dome to H6.40 (scaled by HS)", "class": "v2"})
loft(hd, "HD_neck", cbox(Bl(0, 0, 4.90), (.86, .70, .50), .10), sh_skin, meta={"recipe": "short wide neck block, mostly inside skull/torso/beard (no separate visible neck block in profile)", "class": "v2"})
for s, nm in ((-1, "Right"), (1, "Left")):
    loft(hd, "HD_ear_" + nm, cbox(Bl(s * 1.015, -.015, 5.62), (.30, .42, .50), .08), sh_skin, meta={"recipe": "ear .30 x .42 x .50", "class": "v2"})
    x_out = s * 1.165
    solid_box(hd, "HD_concha_" + nm, min(x_out + s * .02, x_out - s * .035), max(x_out + s * .02, x_out - s * .035), -(.05 + .10), -(.05 - .10), 5.50, 5.74, sh_const("EarInner"),
              {"recipe": "ear concha patch, proud .02", "class": "v2"})
    # eyes: oval whites, round iris/pupil, glint; the brow covers the upper edge
    ex = s * .40
    prism_xh(hd, "HD_eyewhite_" + nm, ellipse(ex, 5.80, .205, .108, 16, rot=s * -0.10), .72, .785, sh_const("EyeWhite"), {"recipe": "oval eye white .41 x .22, tilted (narrowed)", "class": "v2"})
    prism_xh(hd, "HD_iris_" + nm, ellipse(s * .362, 5.792, .078, .086, 14), .72, .800, sh_const("Iris"), {"recipe": "round iris d.16", "class": "v2"})
    prism_xh(hd, "HD_pupil_" + nm, ellipse(s * .360, 5.792, .046, .052, 12), .72, .813, sh_const("Pupil"), {"recipe": "pupil d.13", "class": "v2"})
    prism_xh(hd, "HD_glint_" + nm, ellipse(s * .378, 5.822, .020, .022, 8), .72, .822, sh_const("EyeGlint"), {"recipe": "one glint per eye", "class": "v2"})
    xi, xo, t = s * .10, s * .72, .15
    prism_xh(hd, "HD_brow_" + nm, [(xi, 5.915 - t / 2), (xo, 6.05 - t / 2), (xo, 6.05 + t / 2), (xi, 5.915 + t / 2)], .70, .865, sh_const("Brow"),
             {"recipe": "brow wedge, thickness .13, inner end H5.985 (covers the eye top), outer H6.10", "class": "v2"})
    # moustache half: follows the smile, tapered towards the mouth corner
    mp = [(-s * .02, 5.50), (-s * .02, 5.72), (s * .30, 5.68), (s * .58, 5.58), (s * .66, 5.46), (s * .56, 5.43), (s * .28, 5.48)]
    prism_xh(hd, "HD_moustache_" + nm, mp, .70, 1.03, sh_beard, {"recipe": "moustache half under the nose, front F1.03 (nose front 1.20)", "class": "v2"})

NOSE = [(5.45, .30, .98, .70, .08), (5.58, .44, 1.14, .70, .10), (5.78, .42, 1.04, .70, .10), (5.98, .26, .84, .70, .07)]
loft(hd, "HD_nose", [ring8(w / 2, -ff, -fb, c, 0, 0, h) for h, w, ff, fb, c in NOSE], sh_nose, meta={"recipe": "short wide nose, front F1.14, 0.38 in front of the face plane, above the moustache", "class": "v2"})

# smile: dark compact crescent + ONE curved teeth band, corners lifted; no lip plate, no support block (the beard window leaves the skin floor)
xs = [-.60 + 1.20 * k / 10 for k in range(11)]
cav = [(x, 5.19 + .16 * (x / .60) ** 2) for x in xs] + [(x, 5.47 + .17 * (x / .60) ** 2) for x in xs[::-1]]
prism_xh(hd, "HD_mouth_cavity", cav, .70, .785, sh_const("Mouth"), {"recipe": "compact dark crescent under the teeth", "class": "v2"})
xt = [-.54 + 1.08 * k / 10 for k in range(11)]
teeth = [(x, 5.28 + .16 * (x / .54) ** 2) for x in xt] + [(x, 5.44 + .17 * (x / .54) ** 2) for x in xt[::-1]]
prism_xh(hd, "HD_teeth", teeth, .70, .805, sh_const("Teeth"), {"recipe": "one continuous curved teeth band, corners up", "class": "v2"})

# beard: dense closed volume built from several jaw sections (not a front contour pushed forward), then the face window is cut out (cheeks, nose, mouth)
BEARD_ROWS = [(4.76, .50, .78, .05, .18), (4.84, .80, 1.05, .00, .22), (5.02, .97, 1.12, -.15, .22), (5.30, 1.06, 1.07, -.28, .20), (5.55, 1.07, 1.00, -.30, .18), (5.80, 1.02, .92, -.28, .15)]
bm = loft_bm([ring8(a, -ff, -fb, c, 0, 0, h) for h, a, ff, fb, c in BEARD_ROWS], sh_beard)
WINDOW = [(-.88, 6.30), (-.88, 5.92), (-.62, 5.52), (-.60, 5.22), (0, 5.12), (.60, 5.22), (.62, 5.52), (.88, 5.92), (.88, 6.30)]
win = prism_bm(WINDOW, .745, 1.60, "Beard")
bm = bm_boolean(bm, win)
win.free()
hd.append_bm("HD_beard", bm, None, {"recipe": "6 jaw sections (chin F1.12, cheeks wrap to sideburns), face window cut at the beard top line; walls remain beard colour", "class": "v2"})
bm.free()
