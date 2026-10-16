

# ----------------------------------------------------------------------------------------------
# Head: skull shell, ears, eyes, brows, nose, smile, teeth, moustache, side/back hair, bucket hat
# ----------------------------------------------------------------------------------------------
hd = PM("Head", JV["Neck"])
loft(hd, "HD_shell", [row_ring(r) for r in HEAD_ROWS], sh_skin,
     meta=meta("head shell W1.80 D1.36 H1.56 (4.22..5.78), cuts .10..14", dims={"rows": HEAD_ROWS}))
for s in (-1, 1):
    nm = "R" if s < 0 else "L"
    box_c(hd, "HD_ear_" + nm, (s * .93, -.02, 5.08), (.25, .30, .44), sh_skin, ch=.05, meta_=meta("ear .25 x .30 x .44, bevel .05"))
    box_c(hd, "HD_ear_recess_" + nm, (s * (.93 + .125 + .002), -.02, 5.08), (.012, .12, .23), sh_const("SKIN_SHADOW"), meta_=meta("ear recess W.12 H.23 depth .03 (flat shadow facet)", "prescribed"))
    # eyes
    ex, eh = s * .35, 5.20
    disc_d(hd, "HD_eye_white_" + nm, ex, -.725, eh, .18, .03, "EYE_WHITE", segs=12, ry=.16, embed=.0 + .0)
    nx_ = ex - s * .015
    disc_d(hd, "HD_iris_" + nm, nx_, -.742, eh, .095, .02, "IRIS", segs=10)
    disc_d(hd, "HD_pupil_" + nm, nx_, -.749, eh, .065, .02, "PUPIL", segs=8)
    disc_d(hd, "HD_glint_" + nm, nx_ + .03, -.753, eh + .03, .015, .02, "EYE_WHITE", segs=6)
    # brows
    bo = [(-.63, 5.41), (-.17, 5.45), (-.17, 5.55), (-.63, 5.51)]
    bo = [(x * -s if False else (x if s < 0 else -x), h) for x, h in bo]
    if s > 0:
        bo = bo[::-1]
    plate(hd, "HD_brow_" + nm, bo, lambda x, h: hf(h, x) + .01, lambda x, h: hf(h, x) - .045, "BROW", ch=.012,
          meta_=meta("brow thickness .10, proud .045, X-.63..-.17 H5.46..5.50 (cheerful, raised)"))
    # nose wing + nostril facet
    box_c(hd, "HD_nose_wing_" + nm, (s * .20, -.93, 4.95), (.12, .16, .11), sh_nose, ch=.03, meta_=meta("alar wing at X+/-.20, H4.94, D-.94"))
    box_c(hd, "HD_nostril_" + nm, (s * .085, -1.04, 4.895), (.04, .05, .018), sh_const("SKIN_SHADOW"), meta_=meta("nostril facet .04 x .018", "prescribed"))

NOSE_ROWS_ = [(4.89, .34, -1.00, -.60, .05), (4.95, .43, -1.15, -.60, .055), (5.05, .40, -1.13, -.60, .055),
              (5.20, .30, -1.00, -.60, .05), (5.38, .19, -.76, -.60, .04)]
loft(hd, "HD_nose", [row_ring(r) for r in NOSE_ROWS_], sh_nose, meta=meta("nose wedge: root H5.35 W.19, tip H4.95 W.43, front D-1.15, bevel .055", dims={"rows": NOSE_ROWS_}))

# smile cavity, teeth strip, lower lip edge
SMILE = [(-.43, 4.765), (-.215, 4.75), (0, 4.742), (.215, 4.75), (.43, 4.765), (.38, 4.66), (.26, 4.52), (.12, 4.42), (0, 4.39), (-.12, 4.42), (-.26, 4.52), (-.38, 4.66)]
plate(hd, "HD_mouth", SMILE, lambda x, h: hf(h, x) + .012, lambda x, h: hf(h, x) - .006, "MOUTH", ch=.012,
      meta_=meta("open smile cavity W.86 H.36, centre H4.57, corners raised, corner cut .06"))
TEETH = [(-.35, 4.645), (-.17, 4.62), (0, 4.614), (.17, 4.62), (.35, 4.645), (.35, 4.735), (.17, 4.728), (0, 4.724), (-.17, 4.728), (-.35, 4.735)]
plate(hd, "HD_teeth", TEETH, lambda x, h: hf(h, x) + .004, lambda x, h: hf(h, x) - .025, "TEETH", ch=.006,
      meta_=meta("upper teeth strip W.70 H.11, thickness .025, no individual teeth"))
plate(hd, "HD_lower_lip", [(-.22, 4.37), (.22, 4.37), (.22, 4.405), (-.22, 4.405)], lambda x, h: hf(h, x) + .004, lambda x, h: hf(h, x) - .012, "LIP", ch=.006,
      meta_=meta("lower lip edge at H4.39", "prescribed"))

# moustache: two bushy lobes, prescribed outline (section 14), depth .23 at the centre -> .14 at the tips
MUS = [(-.04, 5.02), (-.23, 5.10), (-.48, 5.06), (-.72, 5.11), (-.86, 5.25), (-.84, 5.02), (-.66, 4.88), (-.42, 4.84), (-.18, 4.93)]


def mus_depth(x):
    return max(.14, .23 - .09 * max(0.0, abs(x) - .25) / .61)


for s in (-1, 1):
    ol = MUS if s < 0 else [(-x, h) for x, h in MUS][::-1]
    plate(hd, "HD_moustache_" + ("R" if s < 0 else "L"), ol, lambda x, h: hf(h, x) + .03, lambda x, h: hf(h, x) - mus_depth(x), sh_hair, ch=.025,
          meta_=meta("moustache lobe, section 14 outline, depth .23..14, bevel .025"))

# hair base: horseshoe above the ears and rear band (never the face front)
A_, C_ = .90, .14


def hpath_full(h):
    w, f, b, c = interp_row(HEAD_ROWS, h)
    a = w / 2.0
    return [(-a + c, f), (-a, f + c), (-a, b - c), (-a + c, b), (a - c, b), (a, b - c), (a, f + c), (a - c, f)]


def hpath_back(h):
    w, f, b, c = interp_row(HEAD_ROWS, h)
    a = w / 2.0
    return [(-a, b - c), (-a + c, b), (a - c, b), (a, b - c)]


band(hd, "HD_hair_upper", [5.22, 5.40, 5.55, 5.68], hpath_full, .06, -.01, sh_hair, meta_=meta("grey hair base above the ears, H5.22..5.68, thickness .07"))
band(hd, "HD_hair_back", [4.66, 4.84, 5.02, 5.22], hpath_back, .07, -.01, sh_hair, meta_=meta("rear hair band H4.66..5.22", "prescribed"))
TUFTS = {  # right axis (X,D,H), width, thickness; left mirrored
    "temple_upper": ([(-.84, -.22, 5.46), (-1.02, -.12, 5.40), (-1.10, .02, 5.27)], .24, .15),
    "outer_mid": ([(-.88, -.04, 5.18), (-1.12, .04, 5.07), (-1.17, .15, 5.13)], .28, .17),
    "cheek_lower": ([(-.85, -.12, 4.96), (-1.06, .02, 4.80), (-1.15, .15, 4.85)], .26, .16),
    "rear_lower": ([(-.78, .30, 4.94), (-.98, .45, 4.73), (-1.09, .51, 4.80)], .27, .17),
}
for nm, (pts, w, t) in TUFTS.items():
    for s in (-1, 1):
        P = catmull([V((s * -p[0] if s > 0 else p[0], p[1], p[2])) if False else V((p[0] if s < 0 else -p[0], p[1], p[2])) for p in pts], 2)
        k = len(P)
        ws = [w * f for f in (1.0, 1.0, .92, .78, .55)][:k]
        ts = [t * f for f in (1.0, 1.0, .95, .85, .65)][:k]
        sweep(hd, "HD_hair_tuft_%s_%s" % (nm, "R" if s < 0 else "L"), P, ws, ts, sh_hair, up=V((1, 0, 0)), meta_=meta("hair tuft ribbon, 5 sections, tapering, bevel", "prescribed"))
for row, (xlist, top, bots) in enumerate((((-.78, -.52, -.26, 0.0, .26, .52, .78), 5.64, (4.80, 4.90, 4.82, 4.92, 4.82, 4.90, 4.80)),
                                         ((-.65, -.39, -.13, .13, .39, .65), 5.20, (4.64, 4.72, 4.66, 4.66, 4.72, 4.64)))):
    for i, xs in enumerate(xlist):
        lo = bots[i]
        hs_ = [top, top - (top - lo) * .35, top - (top - lo) * .7, lo]
        dd = .075 + .035 * row
        P = [V((xs * (1 + .05 * (5.64 - h)), hb(h, xs) + dd, h)) for h in hs_]
        sweep(hd, "HD_hair_back_strand_%d_%d" % (row, i), P, [.30, .30, .27, .20], [.15, .15, .13, .09], sh_hair, up=V((0, 1, 0)),
              meta_=meta("broad rear strand row %d" % row, "prescribed"))

# moustache tip curls (rise up and outward, per the reference)
for s in (-1, 1):
    pts = [V((s * .80, -.80, 5.12)), V((s * .93, -.77, 5.28)), V((s * 1.00, -.70, 5.40))]
    sweep(hd, "HD_moustache_curl_" + ("R" if s < 0 else "L"), catmull(pts, 2), [.20, .18, .15, .12, .08], [.16, .14, .12, .10, .07], sh_hair, up=V((0, 1, 0)),
          meta_=meta("moustache tip curl rising outward", "inferred"))

# ---- bucket hat (section 16)
N_H = 16
D0 = -.02


def ell(a, b, h, cd=D0, jitter=None):
    pts = []
    for k in range(N_H):
        th = 2 * math.pi * k / N_H
        z = h + (jitter[k] if jitter else 0.0)
        pts.append(V((a * math.cos(th), cd + b * math.sin(th), z)))
    return pts


def tul_dims(h):
    t = (h - 5.78) / (6.32 - 5.78)
    return (1.98 + (1.76 - 1.98) * t) / 2.0, (1.62 + (1.42 - 1.62) * t) / 2.0


JIT = [(((k * 7) % 5) - 2) * .012 for k in range(N_H)]
tul_rings = [ell(.99, .81, 5.78), ell(*tul_dims(6.255), 6.255), ell(.815, .645, 6.32), ell(.55, .45, 6.37, jitter=JIT), ell(.20, .16, 6.40)]
loft(hd, "HD_hat_crown", tul_rings, sh_vest, meta=meta("bucket hat crown: base W1.98 D1.62 at H5.78 -> top W1.76 D1.42 at H6.32 (bevel .065), peak H6.40, 16-gon, faceted cap"))


def brim_h(d):
    u = (d - D0) / 1.05
    return 5.64 + (.11 if u < 0 else .08) * u


sections = []
for k in range(N_H):
    th = 2 * math.pi * k / N_H
    ca, sa = math.cos(th), math.sin(th)
    ho = brim_h(D0 + 1.05 * sa)
    sections.append([V((.99 * ca * 1.0, D0 + .81 * sa, 5.835)), V((1.40 * ca, D0 + 1.05 * sa, ho + .055)),
                     V((1.40 * ca, D0 + 1.05 * sa, ho)), V((.99 * ca, D0 + .81 * sa, 5.78))])
loop_solid(hd, "HD_hat_brim", sections, lambda n, c: "VEST_LIGHT" if n.z > .4 else "VEST_DARK",
           meta_=meta("annular brim thickness .055: inner W1.98 D1.62, outer W2.80 D2.10; front edge H5.53, sides H5.64, rear H5.72"))
bd = []
for h, g in ((5.83, 0.0), (5.842, .025), (6.0, .025), (6.01, 0.0)):
    a, b = tul_dims(h)
    bd.append(ell(a + g, b + g, h))
loft(hd, "HD_hat_band", bd, sh_const("VEST_DARK"), meta=meta("hat band H5.83..6.01, thickness .025, follows the sloped crown"))
a_, b_ = tul_dims(5.92)
box_c(hd, "HD_hat_band_seam", (0, D0 + b_ + .03, 5.92), (.025, .02, .18), sh_const("VEST_SEAM"), meta_=meta("single small seam at the back, no bow", "prescribed"))

# red lure badge on the anatomical RIGHT fore-side of the crown (X<0), plate in the local tangent plane
a6, b6 = tul_dims(6.00)
ux, ud = -.85, -.85 + 0.02
s_ = 1.0 / math.sqrt((ux / (a6 + .025)) ** 2 + (ud / (b6 + .025)) ** 2)
LP = V((ux * s_, D0 + ud * s_, 6.00))
n_ = V((LP.x / (a6 + .025) ** 2, (LP.y - D0) / (b6 + .025) ** 2, 0)).normalized()
n_ = V((n_.x, n_.y, .20)).normalized()
t_ = V((-n_.y, n_.x, 0)).normalized()
u_ = n_.cross(t_).normalized()
if u_.z < 0:
    u_ = -u_
rot = Matrix.Rotation(math.radians(20), 3, n_)


def lure_ring(dn, rx, ry, k=10):
    return [LP + n_ * dn + rot @ (t_ * (rx * math.cos(2 * math.pi * i / k)) + u_ * (ry * math.sin(2 * math.pi * i / k))) for i in range(k)]


loft(hd, "HD_lure_body", [lure_ring(.0, .115, .15), lure_ring(.03, .115, .15), lure_ring(.035, .095, .125)], sh_const("FLOAT_RED"), meta=meta("red lure oval W.23 H.30 D.035 tilted 20 deg"))
loft(hd, "HD_lure_centre", [lure_ring(.034, .0375, .0375, 8), lure_ring(.042, .0375, .0375, 8)], sh_const("BUTTON"), meta=meta("yellow centre dia .075", "prescribed"))
loft(hd, "HD_lure_dot", [lure_ring(.041, .0125, .0125, 6), lure_ring(.046, .0125, .0125, 6)], sh_const("BELT"), meta=meta("dark dot .025", "prescribed"))
tail = [LP + n_ * .02 + u_ * .15, LP + n_ * .005 + u_ * .205, LP - n_ * .005 + u_ * .25]
sweep(hd, "HD_lure_tail", tail, .04, .02, sh_const("BUTTON"), up=n_, meta_=meta("short yellow tail .10 behind the top edge", "prescribed"))
