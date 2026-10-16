

# ----------------------------------------------------------------------------------------------
# Head: bald shell, ears, eyes, heavy brows, nose, closed mouth, big curled moustache, side hair
# ----------------------------------------------------------------------------------------------
hd = PM("Head", JV["Neck"])
loft(hd, "HD_shell", [row_ring(r) for r in HEAD_ROWS], sh_skin, meta=meta("head shell W1.88 D1.50 H1.66 (4.74..6.40), front plane D-.74, cheeks -.78 at H5.12, jaw to X+/-.83", dims={"rows": HEAD_ROWS}))
for s in (-1, 1):
    nm = "R" if s < 0 else "L"
    box_c(hd, "HD_ear_" + nm, (s * 1.00, -.02, 5.44), (.27, .32, .43), sh_skin, ch=.045, meta_=meta("ear .27 x .32 x .43, bevel .045"))
    box_c(hd, "HD_ear_recess_" + nm, (s * (1.00 + .135 + .002), -.02, 5.44), (.012, .12, .22), sh_const("SKIN_SHADOW"), meta_=meta("ear recess W.12 H.22 depth .045 (flat shadow facet)", "prescribed"))
    ex, eh = s * .34, 5.80
    disc_d(hd, "HD_eye_white_" + nm, ex, -.78, eh, .17, .045, "EYE_WHITE", segs=12, ry=.15)
    nx_ = ex - s * .012
    disc_d(hd, "HD_iris_" + nm, nx_, -.795, eh, .08, .02, "IRIS", segs=10)
    disc_d(hd, "HD_pupil_" + nm, nx_, -.802, eh, .0525, .02, "PUPIL", segs=8)
    disc_d(hd, "HD_glint_" + nm, nx_ - .02, -.806, eh + .02, .0175, .02, "EYE_WHITE", segs=4, ry=.0225)
    # heavy brows: outer (-.73,6.08) -> inner (-.13,5.98), thickness .18, depth .09
    bo = [(-.73, 6.17), (-.13, 6.07), (-.13, 5.89), (-.73, 5.99)]
    if s > 0:
        bo = [(-x, h) for x, h in bo][::-1]
    plate(hd, "HD_brow_" + nm, bo, lambda x, h: hf(h, x) + .01, lambda x, h: hf(h, x) - .09, "BROW", ch=.02, meta_=meta("heavy brow W.60 H.18, depth .09, inner end lowered (stern)"))
    box_c(hd, "HD_nostril_" + nm, (s * .075, -.995, 5.40), (.035, .04, .02), sh_const("SKIN_SHADOW"), meta_=meta("nostril facet .035 x .02", "prescribed"))

NOSE_ROWS_ = [(5.39, .40, -1.00, -.60, .06), (5.52, .42, -1.02, -.60, .06), (5.62, .34, -.90, -.60, .05), (5.70, .20, -.80, -.60, .04)]
loft(hd, "HD_nose", [row_ring(r) for r in NOSE_ROWS_], sh_nose, meta=meta("nose: root (0,-.78,5.70), tip (0,-1.02,5.52), W.42 H.31 proud .28", dims={"rows": NOSE_ROWS_}))
plate(hd, "HD_mouth", [(-.225, 5.0675), (.225, 5.0675), (.225, 5.0325), (-.225, 5.0325)], lambda x, h: hf(h, x) + .01, lambda x, h: hf(h, x) - .004, "MOUTH", ch=.004,
      meta_=meta("closed mouth line W.45 H.035 at H5.05"))
plate(hd, "HD_lip", [(-.225, 5.0325), (.225, 5.0325), (.225, 4.9975), (-.225, 4.9975)], lambda x, h: hf(h, x) + .01, lambda x, h: hf(h, x) - .006, "LIP", ch=.004, meta_=meta("lower lip .035 at H5.00"))

# massive moustache: right lobe outline from section 20, three depth levels D -.79 / -.96 / -1.04
MUS = [(-.03, 5.35), (-.25, 5.40), (-.45, 5.31), (-.62, 5.35), (-.71, 5.50), (-.80, 5.43), (-.82, 5.23), (-.70, 5.10), (-.44, 5.08), (-.19, 5.15), (-.03, 5.22)]
mc = (sum(p[0] for p in MUS) / len(MUS), sum(p[1] for p in MUS) / len(MUS))
for s in (-1, 1):
    for lvl, (kscale, dfront) in enumerate(((1.0, -.79), (.80, -.96), (.52, -1.04))):
        ol = [(mc[0] + (x - mc[0]) * kscale, mc[1] + (h - mc[1]) * kscale) for x, h in MUS]
        if s > 0:
            ol = [(-x, h) for x, h in ol][::-1]
        plate(hd, "HD_moustache_%s_L%d" % ("R" if s < 0 else "L", lvl + 1), ol, lambda x, h: hf(h, x) + .01, lambda x, h, d=dfront: d, sh_hair, ch=.025,
              meta_=meta("moustache lobe level %d (outline x%.2f, front D%.2f), upturned outer tip" % (lvl + 1, kscale, dfront)))

# side hair: temple blocks (two layers), lower sideburn, low rear U band; bald crown stays free
for s in (-1, 1):
    nm = "R" if s < 0 else "L"
    box_c(hd, "HD_hair_side_low_" + nm, (s * .91, -.02, 5.88 - .1175), (.20, .56, .235), sh_hair, ch=.035, meta_=meta("temple block layer 1, D-.30..+.26"))
    box_c(hd, "HD_hair_side_up_" + nm, (s * .91, .00, 5.88 + .1175), (.20, .50, .235), sh_hair, ch=.035, meta_=meta("temple block layer 2, top H6.10"))
    box_c(hd, "HD_sideburn_" + nm, (s * .93, .20, 5.675), (.14, .22, .31), sh_hair, ch=.03, meta_=meta("lower sideburn H5.52..5.83, behind the ear"))


def hpath_back(h):
    w, f, b, c = interp_row(HEAD_ROWS, h)
    a = w / 2.0
    return [(-a, b - c), (-a + c, b), (a - c, b), (a, b - c)]


band(hd, "HD_hair_rear_U", [5.65, 5.78, 5.90, 5.98], hpath_back, .07, -.01, sh_hair, meta_=meta("low rear U band H5.65..5.98, thickness .07", "prescribed"))
