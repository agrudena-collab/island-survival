# ----------------------------------------------------------------------------------------------
# head: faceted skull, ears, hooded eyes, brows, nose, curled moustache, mouth, swept hair wave with grey temples
# ----------------------------------------------------------------------------------------------
hd = PM("Head", JV["Neck"], xf=xf_head)
# moustache correction made in the LIVE Blender scene through MCP (reference: thicker, narrower lobes, ~64% of the face width): X x0.82, H x1.15 about H5.12
MSX, MSZ, MZC = 0.82, 1.15, 5.12
SKULL = [(4.75, 1.22, .74, -.70, .20), (4.93, 1.58, .88, -.80, .20), (5.20, 1.66, .93, -.84, .20), (5.90, 1.66, .93, -.84, .18), (6.04, 1.52, .80, -.74, .14)]
loft(hd, "HD_skull", [ring8(w / 2, -ff, -fb, c, 0, 0, h) for h, w, ff, fb, c in SKULL], sh_skin, meta={"recipe": "faceted block head W1.66 x D1.77, bevel .20 at the jaw/cheeks, chin H4.75", "class": "measured+extrapolated"})
loft(hd, "HD_neck", cbox(Bl(0, -.02, 4.82), (.84, .78, .52), .10), sh_skin, meta={"recipe": "short neck block mostly inside skull/collar", "class": "extrapolated"})
for s, nm in ((-1, "Right"), (1, "Left")):
    loft(hd, "HD_ear_" + nm, cbox(Bl(s * .93, -.02, 5.20), (.26, .44, .50), .08), sh_skin, meta={"recipe": "ear block .26 x .44 x .50", "class": "observed"})
    xo = s * 1.065
    solid_box(hd, "HD_concha_" + nm, min(xo + s * .02, xo - s * .035), max(xo + s * .02, xo - s * .035), -(-.02 + .11), -(-.02 - .11), 5.07, 5.32, sh_const("EarInner"), {"recipe": "ear concha patch", "class": "observed"})
    # hooded eyes (revision 2): small whites, large pupil touching the heavy brow, gaze to the character's left; the brow covers the upper lid
    ex = s * .34
    prism_xh(hd, "HD_eyewhite_" + nm, ellipse(ex, 5.455, .120, .072, 16, rot=s * -0.10), .76, .965, sh_const("EyeWhite"), {"recipe": "narrow eye white .24 x .14, tilted, upper lid hidden by the brow", "class": "observed"})
    prism_xh(hd, "HD_pupil_" + nm, ellipse(ex + .052, 5.452, .056, .062, 12), .76, .978, sh_const("Pupil"), {"recipe": "black pupil d.11, looking to the character's left", "class": "observed"})
    prism_xh(hd, "HD_glint_" + nm, ellipse(ex + .072, 5.478, .014, .015, 8), .76, .988, sh_const("Glint"), {"recipe": "one glint per eye", "class": "observed"})
    brow = [(s * .05, 5.50), (s * .05, 5.72), (s * .38, 5.83), (s * .68, 5.93), (s * .74, 5.77), (s * .44, 5.62), (s * .26, 5.53)]
    prism_xh(hd, "HD_brow_" + nm, brow, .74, 1.03, sh_const("Brow"), {"recipe": "thick brow wedge, inner end low (H5.50) over the eye, outer end H5.93", "class": "observed"})
    mp = [(0.0, 5.13), (.14, 5.07), (.38, 5.04), (.60, 5.09), (.72, 5.22), (.76, 5.40), (.66, 5.45), (.60, 5.31), (.46, 5.25), (.24, 5.28), (0.0, 5.27)]
    prism_xh(hd, "HD_moustache_" + nm, [(s * x * MSX, MZC + (h - MZC) * MSZ) for x, h in mp] if s > 0 else [(s * x * MSX, MZC + (h - MZC) * MSZ) for x, h in mp][::-1], .70, 1.05, sh_const("Moustache"), {"recipe": "curled moustache lobe: raised, tapered, tip curls up", "class": "observed"})
    mt = [(0.0, 5.25), (.24, 5.26), (.46, 5.23), (.62, 5.31), (.58, 5.28), (.46, 5.19), (.24, 5.22), (0.0, 5.19)]
    prism_xh(hd, "HD_moustache_top_" + nm, [(s * x * MSX, MZC + (h - MZC) * MSZ) for x, h in mt] if s > 0 else [(s * x * MSX, MZC + (h - MZC) * MSZ) for x, h in mt][::-1], 1.03, 1.08, sh_const("MoustacheLight"), {"recipe": "lighter top ridge of the moustache", "class": "extrapolated"})
# nose raised by 0.10 in the LIVE Blender scene (MCP) so the moustache centre stays visible below the nose
NOSE = [(5.12, .34, 1.10, .70, .09), (5.20, .46, 1.20, .70, .15), (5.34, .53, 1.27, .70, .20), (5.52, .47, 1.20, .70, .18), (5.68, .30, 1.02, .70, .11)]   # revision 4: rounder nose (as in the turnaround close-up)
loft(hd, "HD_nose", [ring8(w / 2, -ff, -fb, c, 0, 0, h) for h, w, ff, fb, c in NOSE], sh_nose, meta={"recipe": "large faceted nose, front F1.24 (0.31 proud)", "class": "observed"})
prism_xh(hd, "HD_mouth", [(-.24, 4.93), (.0, 4.89), (.28, 4.96), (.32, 5.01), (-.0, 4.98), (-.24, 5.01)], .70, .95, sh_const("Mouth"), {"recipe": "small calm smirk line under the moustache", "class": "observed"})

# ---------------------------------------------------------------------------------------------------------------------------
# hair (revision 2): low scalp cap + a swept wave of broad locks rising at the front-left of the forehead, rolling over the crown and falling to the back right;
# the character's right side keeps a longer stepped block with the grey temple, the left side is shorter. Locks are separate sweeps, tops reach H6.40.
# ---------------------------------------------------------------------------------------------------------------------------
# ONE hair shell wraps the whole skull (no separate boxes sticking out, no bare back of the head): the front edge of the lower rows sits at F.05..0.32, so
# the sides come down to the ear and the nape, while the front edge rises diagonally to the forehead hairline H5.90 (visible as the sloped temple edge).
HC = [(5.06, 1.36, -.05, -.74, .16), (5.26, 1.74, .10, -.90, .20), (5.62, 1.78, .32, -.92, .20), (5.90, 1.78, .98, -.92, .20), (6.02, 1.78, 1.00, -.92, .20), (6.10, 1.64, .88, -.84, .18), (6.15, 1.30, .60, -.54, .12)]
def sh_hair_shell(n, c):
    """grey temples/sideburns are part of the shell surface (stepped bands on the side faces in front of the ear), not separate boxes"""
    if abs(c.x) > .70 and -.15 < -c.y < .50 and 5.15 < c.z < 5.85 and abs(n.x) > .4:
        return "HairGrey" if c.z > 5.52 else ("HairGreyLight" if c.z > 5.28 else "HairGreyShadow")
    return sh_hair(n, c)


loft(hd, "HD_hair_shell", [ring8(w / 2, -ff, -fb, c, 0, 0, h) for h, w, ff, fb, c in HC], sh_hair_shell, meta={"recipe": "single hair shell H5.06..6.15 over the whole skull; replaces the earlier cap + back/side boxes", "class": "observed+extrapolated"})
# face relief: cheek planes, nostril shadows, chin facet, eyelid shadow wedge
for s_, nm in ((-1, "Right"), (1, "Left")):
    prism_xh(hd, "HD_nostril_" + nm, ellipse(s_ * .11, 5.17, .055, .03, 8), .70, 1.17, sh_const("SkinShadow"), {"recipe": "nostril shadow under the nose", "class": "observed"})
    prism_xh(hd, "HD_eyelid_" + nm, ellipse(s_ * .34, 5.375, .12, .03, 10), .76, .962, sh_const("SkinShadow"), {"recipe": "lower eyelid shadow", "class": "extrapolated"})
prism_xh(hd, "HD_chin_facet", [(-.30, 4.78), (.30, 4.78), (.22, 4.92), (-.22, 4.92)], .70, .90, sh_const("SkinLight"), {"recipe": "chin facet", "class": "extrapolated"})


def lock(cid, pts, w0, w1, h0, h1, thick=1.0):
    # revision 4: thicker locks (pompadour volume); the centre line is clamped so that the top surface never exceeds H6.40
    k = 1.4 * thick
    pts = [(x, f, min(z, 6.40 - h0 * k / 2)) if z > 6.0 else (x, f, z) for x, f, z in pts]
    path = catmull([Bl(*p_) for p_ in pts], 4)
    sweep(hd, cid, path, lambda t: w0 + (w1 - w0) * t, lambda t: (h0 + (h1 - h0) * t) * k, .08, sh_hair, {"recipe": "broad swept lock", "class": "observed+extrapolated"})


# path points are (X, F, H) of the lock centre line; height 0.30 means the top surface is 0.15 above the path
lock("HD_wave_1", [(-.74, .98, 5.98), (-.58, 1.08, 6.14), (-.18, .76, 6.25), (.32, .30, 6.23), (.74, -.22, 6.12), (.86, -.60, 5.98)], .54, .36, .30, .24)
lock("HD_wave_2", [(-.86, .52, 5.98), (-.74, .56, 6.16), (-.34, .32, 6.24), (.14, -.16, 6.22), (.58, -.52, 6.12), (.80, -.76, 5.98)], .50, .34, .28, .22)
lock("HD_wave_3", [(-.22, .98, 5.98), (.02, .98, 6.12), (.40, .64, 6.19), (.74, .16, 6.14), (.88, -.34, 6.02)], .50, .30, .26, .22)
lock("HD_wave_4", [(-.56, -.10, 6.14), (-.16, -.44, 6.22), (.30, -.70, 6.18), (.64, -.82, 6.04)], .50, .32, .26, .22)
lock("HD_wave_5", [(.24, .94, 5.98), (.46, .86, 6.08), (.76, .56, 6.10), (.92, .22, 6.02)], .40, .26, .24, .20)
lock("HD_wave_front_curl", [(-.80, 1.00, 5.94), (-.60, 1.10, 6.08), (-.28, 1.04, 6.16)], .40, .30, .26, .22)

# back-of-head strands (revision 3): vertical broad locks along the nape so the back reads as hair, not as a plain block
for k, x in enumerate((-.62, -.31, 0.0, .31, .62)):
    lock("HD_back_strand_%d" % (k + 1), [(x * .98, -.80, 6.06), (x, -.95, 5.80), (x * 1.02, -.97, 5.50), (x * .96, -.90, 5.20)], .30, .26, .14, .12, 0.75)
