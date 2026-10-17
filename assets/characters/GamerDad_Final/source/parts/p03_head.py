

# ----------------------------------------------------------------------------------------------
# Head: neck, shell with the printed face, ears, brows, nose, moustache, ONE U-shaped beard shell, hair cap + 3 locks
# ----------------------------------------------------------------------------------------------
hd = PM("Head", JV["Neck"])
loft(hd, "HD_neck", cbox((0.0, 0.0, 4.53), (0.72, 0.65, 0.26), 0.08), sh_const("SKIN"), meta=meta("neck block .72 x .65 x .26, bevel .08 (top hidden in the head, bottom in the sweatshirt)"))
loft(hd, "HD_shell", [ring12(W, Df, Db, c, 0.0, H) for H, W, Df, Db, c in HEAD_ROWS], sh_skin,
     meta=meta("closed loft of 7 chamfered 12-point rings (spec head_rows), front faces carry the printed face map", rows=HEAD_ROWS))
n_face = hd.set_map("HD_shell", UVM_FACE, lambda f: f.normal.y < -0.35, tile="SKIN")
COMP_LOG[hd.comp_index("HD_shell")]["face_faces"] = n_face
for nm in ("eye_white", "iris", "eye_highlight"):
    for s in ("R", "L"):
        COMP_LOG.append({"id": "HD_%s_%s" % (nm, s), "owner": "Head", "kind": "texture", "recipe": "printed on the actual head front faces, atlas face rect 0,256-256,768 (px = 256(X+1.01)/2.02, py = 256+512(6.22-H)/1.62)", "faces": 0, "tris": 0, "class": "prescribed"})
COMP_LOG.append({"id": "HD_mouth", "owner": "Head", "kind": "texture", "recipe": "flat MOUTH line printed in the skin notch of the beard", "faces": 0, "tris": 0, "class": "prescribed"})

for s, side in ((-1, "R"), (1, "L")):
    # ear block, outer inner-patch painted (SKIN_SHADOW 0.19 along D, 0.25 along H) on the outer face X = +/-1.135
    loft(hd, "HD_ear_" + side, cbox((s * 1.015, 0.005, 5.23), (0.24, 0.40, 0.50), 0.065), sh_const("SKIN"), meta=meta("ear block .24 x .40 x .50, bevel .065, no helix"))
    cx = s * 1.14
    n_e = hd.paint("HD_ear_" + side, "SKIN_SHADOW", lambda f, s=s: f.normal.x * s > 0.9 and abs(f.calc_center_median().y + 0.07) < 0.0951 and abs(f.calc_center_median().z - 5.24) < 0.1251,
                   planes=[((0, -0.07 + 0.095, 0), (0, 1, 0)), ((0, -0.07 - 0.095, 0), (0, 1, 0)), ((0, 0, 5.24 + 0.125), (0, 0, 1)), ((0, 0, 5.24 - 0.125), (0, 0, 1))], only=lambda f, s=s: f.normal.x * s > 0.9)
    COMP_LOG.append({"id": "HD_ear_inner_" + side, "owner": "Head", "kind": "paint", "recipe": "flat SKIN_SHADOW patch .19 x .25 on the outer ear face (no geometry)", "faces": n_e, "tris": 0, "class": "prescribed"})


def head_front_d(h):
    return interp_rows(HEAD_ROWS, h)[1]            # Df of the head table at height h (W, Df, Db, c -> index 1)


# brows: one bevelled bar per side along two given points, thickness .105 along D, .16 across, standing .035 proud of the skin
def brow(side, A, B):
    ax = V((B[0] - A[0], 0.0, B[1] - A[1]))
    L = ax.length
    ex = ax / L
    ey = V((0, 1, 0))
    ez = ex.cross(ey)
    rot = Matrix(((ex.x, ey.x, ez.x), (ex.y, ey.y, ez.y), (ex.z, ey.z, ez.z)))
    mid = ((A[0] + B[0]) / 2.0, (A[1] + B[1]) / 2.0)
    dsk = head_front_d(mid[1])
    c = V((mid[0], dsk - 0.035 + 0.105 / 2.0, mid[1]))
    loft(hd, "HD_brow_" + side, cbox(c, (L, 0.105, 0.16), 0.025, rot=rot), sh_const("BROW"), meta=meta("single bevelled brow bar, endpoints XH %s -> %s, thickness .105, height .16, .035 proud, bevel .025" % (A, B)))


brow("R", (-0.68, 5.70), (-0.10, 5.56))
brow("L", (0.10, 5.56), (0.68, 5.70))

# nose: one closed wedge loft, nostril marks come from the nose atlas map
NOSE_ROWS = [(4.99, 0.36, -0.98, -0.67), (5.13, 0.53, -1.13, -0.67), (5.31, 0.38, -1.02, -0.68), (5.45, 0.25, -0.88, -0.67)]
loft(hd, "HD_nose", [ring8(w / 2.0, f, b, 0.05, 0.0, 0.0, h) for h, w, f, b in NOSE_ROWS], sh_const("NOSE"), meta=meta("closed wedge loft 4 rings, bevel .05", rows=NOSE_ROWS))
hd.set_map("HD_nose", UVM_NOSE, None, tile="NOSE")
COMP_LOG.append({"id": "HD_nostrils", "owner": "Head", "kind": "texture", "recipe": "two flat nostril marks printed through the nose atlas map (px = 384+256X/.53, py = 512+128(5.45-H)/.46)", "faces": 0, "tris": 0, "class": "prescribed"})

# moustache: bevelled lobe .48 x .25 x .19 at (+/-.235,-.93,4.985), outer end dropped .035; BEARD, BEARD_DARK underneath only
for s, side in ((-1, "R"), (1, "L")):
    bmm = make_bm_solid([p for r in cbox((s * 0.235, -0.8775, 4.985), (0.48, 0.355, 0.19), 0.05) for p in r], loft_faces(4, 8))
    for v in bmm.verts:
        t = min(1.0, abs(v.co.x) / 0.475)
        v.co.z -= 0.035 * t
    bmm.normal_update()
    hd.append_bm("HD_moustache_" + side, bmm, lambda n, c: "BEARD_DARK" if n.z < -0.5 else "BEARD", meta("bevelled lobe .48 x .19, front face D-1.055 (spec), back extended to D-.70 to reach the skin, outer end drop .035, bevel .05"))
    bmm.free()
deviate("HD_moustache: spec centre D-.93 / depth .25 leaves a .125 gap to the skin (skin front D-.68); the back face is extended to D-.70 (centre -.8775, depth .355), front face unchanged at D-1.055.")

# beard: ONE closed U-shaped shell: front contour (X,H) lifted to Dfront(X), its copy at Drear(X), bevel .065 on the front rim
BEARD_XH = [list(pt) for pt in spec_c("HD_beard")["contour_XH"]]
# local narrowing of the cheek corners (idx 0, 9: +/-.94 -> +/-.90, idx 10, 16: +/-1.00 -> +/-.93): the mic boom passes the cheek corner at X=1.00 and touched the beard (clearance .004)
for _i, _x in ((0, -0.90), (9, 0.90), (10, 0.93), (16, -0.93)):
    BEARD_XH[_i][0] = _x
deviate("HD_beard: the cheek corners of the contour are pulled in (idx 0/9 |X| .94 -> .90, idx 10/16 |X| 1.00 -> .93, symmetric, widest width 1.86 instead of 2.00) because the mic boom of the spec touched the beard corner (clearance .004, required >= .03). Everything else of the contour and both depth formulas is unchanged.")


def d_front(x):
    return -1.04 + 0.18 * (abs(x) / 1.0) ** 1.5


def d_rear(x):
    return -0.45 + 0.55 * max(0.0, (abs(x) - 0.70) / 0.30)


nb = len(BEARD_XH)
PF = [V((x, d_front(x), h)) for x, h in BEARD_XH]
PB = [V((x, d_rear(x), h)) for x, h in BEARD_XH]
for x, h in BEARD_XH:
    assert d_rear(x) - d_front(x) > 0
P = PF + PB
Fc = [[i, (i + 1) % nb, nb + (i + 1) % nb, nb + i] for i in range(nb)]
poly2d = [V((x, h, 0.0)) for x, h in BEARD_XH]
tri = mgeo.tessellate_polygon([poly2d])
Fc += [[a, b, c] for a, b, c in tri]
Fc += [[nb + a, nb + b, nb + c] for a, b, c in tri]
bb = make_bm_solid(P, Fc)
front_edges = []
for e in bb.edges:
    fs = e.link_faces
    if len(fs) == 2 and any(f.normal.y < -0.5 and len(f.verts) == 3 for f in fs) and any(len(f.verts) == 4 for f in fs):
        front_edges.append(e)
bmesh.ops.bevel(bb, geom=front_edges, offset=0.065, offset_type='OFFSET', segments=1, profile=0.5, affect='EDGES')
bb.normal_update()
hd.append_bm("HD_beard", bb, sh_beard, meta("ONE closed extruded U polygon (17-point XH contour), front D = -1.04+.18(|X|/1)^1.5, rear D = -.45+.55max(0,(|X|-.70)/.30), front rim bevel .065 x 1 segment, no jitter, no shared sup_point",
                                          contour_XH=BEARD_XH))
bb.free()

# hair cap: ONE closed shell hugging the head (spec: 12 angular sections, rim H 6.01 front / 5.29 side / 4.74 back, top H 6.35, apex = ONE vertex, hidden inner surface .04 inward).
# The linear-in-r cone of the spec cuts into the skull at the sides (r=.92 ring sits 0.06 inside the head), so the levels follow the head surface offset outward instead.
HC_C = 0.05
HTOP = 6.35
NSEC = 24


def hrim(phi):
    a = abs((phi + math.pi) % (2 * math.pi) - math.pi)
    if a <= math.pi / 2:
        return 6.01 + (5.29 - 6.01) * a / (math.pi / 2)
    return 5.29 + (4.74 - 5.29) * (a - math.pi / 2) / (math.pi / 2)


def head_ring_xy(H):
    W, Df, Db, c = interp_rows(HEAD_ROWS, H)
    return [(p.x, p.y) for p in ring12(W, Df, Db, c, 0.0, 0.0)], (Df + Db) / 2.0


def head_radius(phi, H):
    poly, dc = head_ring_xy(H)
    dirv = V((math.sin(phi), -math.cos(phi)))
    c0 = V((0.0, dc))
    best = None
    for i in range(len(poly)):
        a, b = V(poly[i]), V(poly[(i + 1) % len(poly)])
        hit = mgeo.intersect_line_line_2d(c0, c0 + dirv * 6.0, a, b)
        if hit is not None:
            r = (hit - c0).length
            best = r if best is None else min(best, r)
    assert best is not None, (phi, H)
    return best, dc, dirv


HEAD_TOP_H = HEAD_ROWS[-1][0]
LV_U = [i / 8.0 for i in range(9)]
LV_T = [0.06 + 0.07 * u * u for u in LV_U]
outer_pts = []
ring_idx = []
for li, (u, tt) in enumerate(zip(LV_U, LV_T)):
    for k in range(NSEC):
        phi = 2 * math.pi * k / NSEC
        H = hrim(phi) + u * (HEAD_TOP_H - hrim(phi))
        r, dc, dv = head_radius(phi, H)
        outer_pts.append(V((dv.x * (r + tt), dc + dv.y * (r + tt), H)))
# dome ring: top ring shrunk to .55 and lifted, then the single apex vertex
for k in range(NSEC):
    phi = 2 * math.pi * k / NSEC
    r, dc, dv = head_radius(phi, HEAD_TOP_H)
    outer_pts.append(V((dv.x * (r + 0.09) * 0.55, dc + dv.y * (r + 0.09) * 0.55, HEAD_TOP_H + 0.075)))
apex = len(outer_pts)
outer_pts.append(V((0.0, head_ring_xy(HEAD_TOP_H)[1], HTOP)))
NLV = len(LV_U) + 1
FO = []
for lv in range(NLV - 1):
    for k in range(NSEC):
        a, b = lv * NSEC + k, lv * NSEC + (k + 1) % NSEC
        FO.append([a, b, b + NSEC, a + NSEC])
for k in range(NSEC):
    FO.append([(NLV - 1) * NSEC + k, (NLV - 1) * NSEC + (k + 1) % NSEC, apex])
aux = make_bm_solid(outer_pts, FO, closed=False)
aux.normal_update()
nrm = [V(v.normal) for v in aux.verts]
if nrm[apex].z < 0:
    nrm = [-n for n in nrm]
aux.free()
inner_pts = [p - n * 0.04 for p, n in zip(outer_pts, nrm)]
no = len(outer_pts)
P = outer_pts + inner_pts
FH = [list(f) for f in FO] + [[no + i for i in reversed(f)] for f in FO]
for k in range(NSEC):
    a, b = k, (k + 1) % NSEC
    FH.append([a, no + a, no + b, b])
hair = make_bm_solid(P, FH)
hd.append_bm("HD_hair_cap", hair, sh_hair, meta("ONE closed cap: 24 sections, rim H 6.01/5.29/4.74 (spec), 4 rings (9 levels) following the head surface offset .06..13, dome ring + ONE apex vertex at H6.35, inner surface .04 inward"))
hair.free()
# base band (first ring pair) = HAIR_DARK
for f in hd.faces_of("HD_hair_cap"):
    f.normal_update()
    cc = f.calc_center_median()
    phi_c = math.atan2(cc.x, -(cc.y - HC_C))
    if f.normal.z < 0.55 and f.normal.z > -0.3 and cc.z < hrim(phi_c) + 0.16:
        f[hd.tl] = TILE["HAIR_DARK"]
deviate("HD_hair_cap: the spec cone (X_r = r X, D_r = .05 + r(D-.05), H_r = 6.35 + r(Hrim-6.35)) lies inside the skull away from the apex (r=.92 side ring at X=.94 vs head X=1.01), so no hair would be visible. The cap uses 24 angular sections instead of 12 (at 30 deg steps the chords cut the chamfered rear corners of the head and skin shows through), the rim heights 6.01/5.29/4.74, the top H6.35 with ONE apex vertex and the .04 inner surface, but its rings follow the head surface offset outward by .06 (rim) .. .10 (top), 9 levels, and a dome ring.")

# three broad bevelled wedge locks over the front edge of the cap
LOCK_FR = [(-0.50, 0.50), (0.25, 0.50), (0.50, 0.05), (0.25, -0.50), (-0.10, -0.35), (-0.35, 0.10)]
for side, key in (("R", "HD_lock_R"), ("C", "HD_lock_C"), ("L", "HD_lock_L")):
    cs = spec_c(key)
    cx, cy, cz = cs["center_XDH"]
    sx, sd, sh = cs["size_XDH"]
    ang = cs["roll_about_D_deg"]
    pts2 = [(cx + fx * sx, cz + fh * sh) for fx, fh in LOCK_FR]
    n6 = len(pts2)
    P = [V((x, cy - sd / 2.0, h)) for x, h in pts2] + [V((x, cy + sd / 2.0, h)) for x, h in pts2]
    F6 = [[i, (i + 1) % n6, n6 + (i + 1) % n6, n6 + i] for i in range(n6)]
    tri6 = mgeo.tessellate_polygon([[V((x, h, 0.0)) for x, h in pts2]])
    F6 += [[a, b, c] for a, b, c in tri6] + [[n6 + a, n6 + b, n6 + c] for a, b, c in tri6]
    lk = make_bm_solid(P, F6)
    ed = [e for e in lk.edges if any(len(f.verts) == 3 for f in e.link_faces) and any(len(f.verts) == 4 for f in e.link_faces)]
    bmesh.ops.bevel(lk, geom=ed, offset=0.045, offset_type='OFFSET', segments=1, profile=0.5, affect='EDGES')
    Rm = Matrix.Rotation(math.radians(ang), 3, 'Y')
    cen = V((cx, cy, cz))
    for v in lk.verts:
        v.co = cen + Rm @ (v.co - cen)
    lk.normal_update()
    hd.append_bm(key, lk, sh_hair, meta("broad bevelled wedge %s x %s, roll %+.0f deg about D, bevel .045, 6-point XH profile" % (cs["size_XDH"], cs["center_XDH"], ang)))
    lk.free()
