

# ----------------------------------------------------------------------------------------------
# shading rules (big zones, no per-triangle noise)
# ----------------------------------------------------------------------------------------------
def sh_const(name):
    return lambda n, c: name


def sh_sweat(n, c):
    if n.z > 0.45:
        return "SWEATSHIRT_LIGHT"
    if n.z < -0.45:
        return "SWEATSHIRT_DARK"
    return "SWEATSHIRT"


def sh_shorts(n, c):
    if n.z < -0.6:
        return "SHORTS_DARK"
    if n.z > 0.6:
        return "SHORTS_LIGHT"
    return "SHORTS"


def sh_skin(n, c):
    if n.z > 0.55:
        return "SKIN_LIGHT"
    if n.z < -0.55:
        return "SKIN_SHADOW"
    return "SKIN"


def sh_sole(n, c):
    return "SOLE_SHADOW" if n.z < -0.2 else "SOLE"


def sh_hair(n, c):
    if n.z < -0.30:
        return "HAIR_DARK"
    if n.z > 0.62:
        return "HAIR_LIGHT"
    return "HAIR"


def sh_beard(n, c):
    if n.z < -0.40:
        return "BEARD_DARK"
    if n.z > 0.35 and n.y < 0.2:
        return "BEARD_LIGHT"
    return "BEARD"


# ----------------------------------------------------------------------------------------------
# prescribed joints (HoldCan world frame) and tables
# ----------------------------------------------------------------------------------------------
JOINTS = {k: tuple(float(c) for c in v) for k, v in SPEC_IN["joints_holdcan"].items()}
JV = {k: V(v) for k, v in JOINTS.items()}
UT_ROWS = [tuple(r) for r in SPEC_IN["torso_rows"]]       # H, W, Df, Db, c
HEAD_ROWS = [tuple(r) for r in SPEC_IN["head_rows"]]
COMP_SPEC = {c["id"]: c for c in SPEC_IN["components"]}
UP_LEN, LO_LEN = SPEC_IN["arm_lengths"]["upper"], SPEC_IN["arm_lengths"]["lower"]


def spec_c(cid):
    return COMP_SPEC[cid]


def meta(recipe, cls="prescribed", **kw):
    d = {"recipe": recipe, "class": cls}
    d.update(kw)
    return d


# ----------------------------------------------------------------------------------------------
# UpperTorso: sweatshirt shell (12-point rings), rib hem, crewneck band, flat gamepad print on the real front surface
# ----------------------------------------------------------------------------------------------
ut = PM("UpperTorso", JV["Waist"])
loft(ut, "UT_shell", [ring12(W, Df, Db, c, 0.0, H) for H, W, Df, Db, c in UT_ROWS], sh_sweat,
     meta=meta("closed loft of 7 chamfered 12-point rings (H,W,Df,Db,c from the spec), centre X=0", rows=UT_ROWS))
# gamepad print: cut the front faces by the print window (X +/-.60, H 3.76 +/-.60) and give those faces the gamepad atlas map
PRINT_HALF = 0.60
ut.paint("UT_shell", "SWEATSHIRT", lambda f: False,
         planes=[((PRINT_HALF, 0, 0), (1, 0, 0)), ((-PRINT_HALF, 0, 0), (1, 0, 0)), ((0, 0, PRINT_C[1] + PRINT_HALF), (0, 0, 1)), ((0, 0, PRINT_C[1] - PRINT_HALF), (0, 0, 1))],
         only=lambda f: f.normal.y < -0.5)
n_print = ut.set_map("UT_shell", UVM_GAMEPAD, lambda f: f.normal.y < -0.5 and abs(f.calc_center_median().x) < PRINT_HALF - 1e-4 and abs(f.calc_center_median().z - PRINT_C[1]) < PRINT_HALF - 1e-4, tile="SWEATSHIRT")
COMP_LOG[ut.comp_index("UT_shell")]["print_faces"] = n_print
COMP_LOG.append({"id": "UT_gamepad", "owner": "UpperTorso", "kind": "texture", "recipe": "flat gamepad print: atlas rect 256,0-512,256, px = 384+204x, py = 128-204h on the actual front faces of UT_shell (window X+/-.60, H3.16..4.36)",
                 "faces": n_print, "tris": 0, "class": "prescribed"})
loft(ut, "UT_hem", cbox((0, -0.105, 2.48), (3.02, 1.55, 0.18), 0.06), sh_const("CUFF"), meta=meta("rib hem 3.02 x 1.55 x .18, bevel .06"))
# crewneck: closed elliptical band (rectangle section swept round an ellipse): outer 1.24 x 1.02, inner 1.06 x 0.84, height .10, 16 segments
CN_C = V((0.0, -0.02, 4.47))
sections = []
for k in range(16):
    a = 2 * math.pi * k / 16
    ca, sa = math.cos(a), math.sin(a)
    sections.append([V((CN_C.x + .62 * ca, CN_C.y + .51 * sa, CN_C.z - .05)), V((CN_C.x + .62 * ca, CN_C.y + .51 * sa, CN_C.z + .05)),
                     V((CN_C.x + .53 * ca, CN_C.y + .42 * sa, CN_C.z + .05)), V((CN_C.x + .53 * ca, CN_C.y + .42 * sa, CN_C.z - .05))])
P = [p for s in sections for p in s]
F = []
for i in range(16):
    for j in range(4):
        F.append([i * 4 + j, i * 4 + (j + 1) % 4, ((i + 1) % 16) * 4 + (j + 1) % 4, ((i + 1) % 16) * 4 + j])
ut.solid("UT_crewneck", P, F, sh_const("CUFF"), meta("closed elliptical band, outer 1.24 x 1.02, inner 1.06 x .84, height .10, 16 segments, CUFF"))

# ----------------------------------------------------------------------------------------------
# LowerTorso: pelvis, waistband, flat centre seam
# ----------------------------------------------------------------------------------------------
lt = PM("LowerTorso", JV["Root"])
loft(lt, "LT_pelvis", cbox((0, -0.025, 2.32), (2.80, 1.16, 0.44), 0.13), sh_shorts, meta=meta("inner closed chamfer box 2.80 x 1.16 x .44, bevel .13, centre X=0"))
loft(lt, "LT_waistband", cbox((0, -0.025, 2.47), (2.98, 1.32, 0.16), 0.06), sh_const("SHORTS_DARK"), meta=meta("waistband 2.98 x 1.32 x .16, bevel .06"))
n_seam = lt.paint("LT_pelvis", "SHORTS_DARK",
                  lambda f: f.normal.y < -0.6 and abs(f.calc_center_median().x) < 0.0095 and 2.16 < f.calc_center_median().z < 2.44,
                  planes=[((0.009, 0, 0), (1, 0, 0)), ((-0.009, 0, 0), (1, 0, 0)), ((0, 0, 2.16), (0, 0, 1)), ((0, 0, 2.44), (0, 0, 1))], only=lambda f: f.normal.y < -0.6)
COMP_LOG.append({"id": "LT_seam", "owner": "LowerTorso", "kind": "paint", "recipe": "flat centre seam 0.018 wide x .28 high (H2.16..2.44) painted SHORTS_DARK on the pelvis front, no geometry offset", "faces": n_seam, "tris": 0, "class": "prescribed"})

# ----------------------------------------------------------------------------------------------
# legs: one shorts profile for both sides (mirrored X), open skin shins, hem lip
# ----------------------------------------------------------------------------------------------
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    ul = PM(side + "UpperLeg", JV[side + "Hip"])
    rows = spec_c("UL_shorts_" + side)["rows_H_cx_cD_W_D"]
    rings = [ring8(w / 2.0, cD - dep / 2.0, cD + dep / 2.0, 0.10, cx, 0.0, H) for H, cx, cD, w, dep in rows]
    loft(ul, "UL_shorts_" + side, rings, sh_shorts, meta=meta("shorts leg, 4 chamfered rings, bevel .10, no patch pockets", rows=rows))
    ll = PM(side + "LowerLeg", JV[side + "Knee"])
    loft(ll, "LL_skin_" + side, cbox((s * 1.01, 0.0, 1.00), (0.72, 0.67, 0.52), 0.07), sh_skin, meta=meta("open skin shin .72 x .67 x .52, bevel .07"))
    # technical hem lip: spec centre H1.245 is a hidden slab flush with the UL hem; moved to H1.19..1.23 so that its top sinks .01 into the UpperLeg and the hem line is a clean edge
    loft(ll, "LL_shorts_edge_" + side, cbox((s * 1.00, -0.02, 1.21), (1.48, 1.16, 0.04), 0.02), sh_const("SHORTS"), meta=meta("hem lip 1.48 x 1.16 x .04, bevel .02 (spec centre H1.245 shifted to 1.21, see deviations)"))
deviate("LL_shorts_edge: spec centre H1.245 (1.22..1.27) lies entirely inside the UpperLeg hem and its bottom face is coplanar with the UL bottom cap; the slab is placed at H1.19..1.23 (top sinks .01 into UpperLeg as the text demands) to give a visible, clean hem line without z-fighting.")

# ----------------------------------------------------------------------------------------------
# shoes: every shoe component rotated once about H through the ankle axis (right -8 deg, left +8 deg)
# ----------------------------------------------------------------------------------------------
UP_ROWS = [(0.22, 1.26, -1.10, 0.56), (0.47, 1.22, -1.07, 0.53), (0.72, 1.10, -0.87, 0.47), (0.88, 0.94, -0.48, 0.42)]
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    yaw = 8.0 * s
    pivot = (s * 1.02, 0.0, 0.0)
    ft = PM(side + "Foot", JV[side + "Ankle"])

    def rr(ring, yaw=yaw, pivot=pivot):
        return [rot_about_z(p, pivot, yaw) for p in ring]
    sole = make_bm_solid([p for r in cbox((s * 1.10, -0.275, 0.11), (1.32, 1.75, 0.22), 0.10) for p in r], loft_faces(4, 8))
    toe = make_bm_solid([p for r in cbox((s * 1.10, -1.03, 0.29), (1.16, 0.24, 0.28), 0.07) for p in r], loft_faces(4, 8))
    o1, o2 = bm_to_obj(sole, "tmp_sole"), bm_to_obj(toe, "tmp_toe")
    bool_apply(o1, o2, 'UNION')
    bm_u = obj_to_bm(o1)
    bpy.data.objects.remove(o1, do_unlink=True)
    bpy.data.objects.remove(o2, do_unlink=True)
    sole.free()
    toe.free()
    for v in bm_u.verts:
        v.co = rot_about_z(v.co, pivot, yaw)
    bm_u.normal_update()
    ft.append_bm("FT_sole_" + side, bm_u, sh_sole, meta("sole 1.32 x 1.75 x .22 (bevel .10) fused with the white toe cap 1.16 x .24 x .28 (bevel .07) by boolean union; yaw %+.0f deg about the ankle axis" % yaw))
    bm_u.free()
    COMP_LOG.append({"id": "FT_toe_white_" + side, "owner": side + "Foot", "kind": "merged", "recipe": "white toe cap fused into FT_sole (boolean union, hidden faces removed)", "faces": 0, "tris": 0, "class": "prescribed"})
    rings = [rr(ring8(w / 2.0, f, b, 0.12, s * 1.10, 0.0, h - (0.01 if i == 0 else 0.0))) for i, (h, w, f, b) in enumerate(UP_ROWS)]
    loft(ft, "FT_upper_" + side, rings, sh_const("SHOE"), meta=meta("one closed chamfered loft, 4 rings, bevel .12 (first ring sunk .01 into the sole)", rows=UP_ROWS))
deviate("FT_upper: first ring H0.22 is sunk to H0.21 so that the upper bottom does not coincide with the sole top plane.")
