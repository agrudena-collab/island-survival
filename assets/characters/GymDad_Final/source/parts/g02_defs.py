

# ----------------------------------------------------------------------------------------------
# containers, coordinate helpers, shading rules, prescribed tables
# ----------------------------------------------------------------------------------------------
PARTS = {}
COMP_LOG = []
SRC_COLL = bpy.data.collections.new("SOURCE_Components")
SCENE.collection.children.link(SRC_COLL)
EXP_COLL = bpy.data.collections.new("EXPORT_GymDad")
SCENE.collection.children.link(EXP_COLL)
HEXOF = {n: h for n, h, _ in PAL}


def Bl(x, f, h):
    """logical (X, F, H) -> Blender point (X, -F, H)."""
    return V((x, -f, h))


def sh_const(name):
    return lambda n, c: name


def sh_skin(n, c):
    if n.z > 0.55:
        return "SkinLight"
    if n.z < -0.55:
        return "SkinShadow"
    return "Skin"


def sh_skin_arm(n, c):
    if n.z > 0.55:
        return "SkinLight"
    if n.z < -0.55:
        return "SkinShadow"
    if n.y < -0.62:
        return "SkinLight"
    return "Skin"


def sh_tank(n, c):
    if n.z > 0.45:
        return "TankLight"
    if n.z < -0.45:
        return "TankShadow"
    return "Tank"


def sh_shorts(n, c):
    if n.z < -0.6:
        return "ShortsShadow"
    if n.y < -0.62 or n.z > 0.6:
        return "ShortsLight"
    if n.y > 0.62:
        return "ShortsShadow"
    return "Shorts"


def sh_beard(n, c):
    if n.z > 0.55:
        return "BeardLight"
    if n.z < -0.55:
        return "BeardShadow"
    return "Beard"


def sh_shoe(n, c):
    if n.z > 0.6:
        return "ShoeGray"
    return "ShoeBlack"


def sh_sole(n, c):
    if n.z < -0.5:
        return "SoleShadow"
    return "Sole"


def sh_plate(n, c):
    if abs(n.x) > 0.8:
        return "Dumbbell"
    return "DumbbellLight"


def sh_bag_dark(n, c):
    if n.z > 0.6:
        return "BagEdge"
    return "BagDark"


def sh_bag_orange(n, c):
    if n.z > 0.6:
        return "BagLight"
    return "BagOrange"


# ---------------------------------------------------------------------------------------------------------------------------
# V2 PARAMETERS. Every value in this block is a V2 decision made against the original crop (see data/v2_00_reference), not a value of the old plan.
# Baseline values: baseline/data_baseline. Logical frame: X<0 = anatomical RIGHT, F>0 = forward, H up; Blender (x, y, z) = (X, -F, H).
# ---------------------------------------------------------------------------------------------------------------------------
HS = 0.84                     # head scale (about the top of the skull, face axis F=.015)
L1, L2 = 1.40, 1.30           # shoulder->elbow, elbow->wrist: SAME for both arms (baseline 1.30 / 1.20)
RHINT = tuple(float(c) for c in os.environ.get("GYM_RHINT", "-0.3,-0.7,-0.2").split(","))    # IK bend hints (X, F, H): right elbow out and back, left elbow behind the arm (no side-opened sharp elbow)
LHINT = (0.4, -0.8, -0.2)
_GF = float(os.environ.get("GYM_GRIPF", "2.20"))
_GX = float(os.environ.get("GYM_GRIPX", "-2.05"))
GRIP_R = (_GX, _GF, 2.85)  # dumbbell centre = right grip frame
FIST_R = (_GX, _GF - .12, 2.80)  # right fist geometric centre (differs from wrist and from grip)
FIST_L = (2.25, 0.15, 2.25)   # left fist centre
BAG_X = 2.62                  # bag centre X (fist X + .34, as in the original)
JOINTS = {
    "Root": (0, 0, 2.6), "Waist": (0, 0, 2.85), "Neck": (0, 0, 5.02),
    "RightShoulder": (-2.20, 0, 4.95), "RightWrist": (_GX, _GF - .57, 2.90),
    "LeftShoulder": (2.03, 0, 4.86), "LeftWrist": (2.25, 0.15, 2.62),
    "RightHip": (-0.90, 0, 2.2), "LeftHip": (0.90, 0, 2.2), "RightKnee": (-0.98, 0.02, 1.35), "LeftKnee": (0.98, 0.02, 1.35),
    "RightAnkle": (-1.04, 0.02, 0.72), "LeftAnkle": (1.04, 0.02, 0.72),
}


def ik_elbow(S, W, L1, L2, hint):
    """two-link IK (plan section 13): E = S + a*u + h*n, n = bend hint projected across u."""
    S, W, hint = V(S), V(W), V(hint)
    dv = W - S
    d = dv.length
    u = dv / d
    a = (L1 ** 2 - L2 ** 2 + d ** 2) / (2 * d)
    h = math.sqrt(max(L1 ** 2 - a ** 2, 0.0))
    n = (hint - u * hint.dot(u)).normalized()
    return tuple(S + u * a + n * h)


JOINTS["RightElbow"] = ik_elbow(JOINTS["RightShoulder"], JOINTS["RightWrist"], L1, L2, RHINT)
JOINTS["LeftElbow"] = ik_elbow(JOINTS["LeftShoulder"], JOINTS["LeftWrist"], L1, L2, LHINT)
JV = {k: Bl(*v) for k, v in JOINTS.items()}
DUMBBELL_C = Bl(*GRIP_R)
BAGGRIP = Bl(FIST_L[0], FIST_L[1], 2.0)
BAG_C = Bl(BAG_X, 0.0, 0.95)
HZ = 0.95                     # head height factor (the original head is narrow but not short)
HEAD_PIVOT = V((0.0, -0.015, 6.40))


def head_xf(p):
    """V2 head scale: every head component (skull, ears, face, beard, neck) shrinks about the top of the skull"""
    p = V(p)
    d = p - HEAD_PIVOT
    return HEAD_PIVOT + V((d.x * HS, d.y * HS, d.z * HZ))


# torso section table: (H, W, Ffront, Fback signed, bevel); V2: taller torso with the shoulder line at H5.15 (the original has very short neck)
_TORSO = [(2.30, 2.70, .74, -.69, .10), (2.48, 2.92, .88, -.76, .12), (2.85, 3.08, .99, -.80, .14), (3.35, 3.16, 1.00, -.82, .15),
          (3.95, 3.14, .92, -.80, .16), (4.45, 3.06, .82, -.75, .16), (4.85, 2.96, .70, -.68, .14), (5.15, 2.74, .58, -.60, .12)]
TORSO = [(h, w, -ff, -fb, c) for h, w, ff, fb, c in _TORSO]          # D coordinates: front negative, back positive
TORSO_TOP = TORSO[-1][0]
LOWER_ROWS = [r for r in TORSO if r[0] <= 2.85 + 1e-9]
UPPER_ROWS = [r for r in TORSO if r[0] >= 2.85 - 1e-9]


def torso_row_at(h):
    return (h,) + tuple(interp_row(TORSO, h))


def cap_tris2(idxs, pts2d):
    """tessellate a planar polygon given in 2D (x, y) -> triangles of vertex ids."""
    tris = mgeo.tessellate_polygon([[V((p[0], p[1], 0.0)) for p in pts2d]])
    return [[idxs[a], idxs[b], idxs[c]] for a, b, c in tris]


def loft_bm(rings, tilefn, caps=(True, True)):
    n = len(rings[0])
    P = [p for r in rings for p in r]
    bm = make_bm_solid(P, loft_faces(len(rings), n, caps))
    tl = bm.faces.layers.int.get("tile") or bm.faces.layers.int.new("tile")
    for f in bm.faces:
        f.normal_update()
        f[tl] = TILE[tilefn(f.normal.copy(), f.calc_center_median())]
    return bm


def bm_boolean(bm, cutter, op='DIFFERENCE'):
    a = bm_to_obj(bm, "tmp_a")
    b = bm_to_obj(cutter, "tmp_b")
    bool_apply(a, b, op)
    res = obj_to_bm(a)
    bpy.data.objects.remove(a, do_unlink=True)
    bpy.data.objects.remove(b, do_unlink=True)
    return res


def prism_xh(pm, cid, poly_xh, f0, f1, tilefn, meta=None):
    """polygon in (X, H) swept between logical F=f0 (rear) and F=f1 (front); caps are tessellated in the 2D (X, H) plane (robust for concave outlines)"""
    n = len(poly_xh)
    P = [Bl(x, f0, h) for x, h in poly_xh] + [Bl(x, f1, h) for x, h in poly_xh]
    faces = [[k, (k + 1) % n, n + (k + 1) % n, n + k] for k in range(n)]
    faces += cap_tris2(list(range(n)), poly_xh) + cap_tris2(list(range(n, 2 * n)), poly_xh)
    pm.solid(cid, P, faces, tilefn, meta)


def patch_box(pm, cid, cx, fc, hc, w, d, hh, tile, embed=0.03, meta=None):
    """thin flat patch: centre (cx, fc, hc) sizes W (X), D (F), H; the rear is embedded `embed` into the surface."""
    solid_box(pm, cid, cx - w / 2, cx + w / 2, -(fc + d / 2), -(fc - d / 2) + embed, hc - hh / 2, hc + hh / 2, tile, meta)


def cyl_x(pm, cid, cx, cy, cz, length, r, segs, tilefn, ch=0.0, meta=None):
    """cylinder along X (Blender coords for the centre), optional end chamfer."""
    x0, x1 = cx - length / 2, cx + length / 2

    def ring(x, rr):
        return [V((x, cy + rr * math.cos(2 * math.pi * k / segs), cz + rr * math.sin(2 * math.pi * k / segs))) for k in range(segs)]
    if ch > 0:
        rings = [ring(x0, r - ch), ring(x0 + ch, r), ring(x1 - ch, r), ring(x1, r - ch)]
    else:
        rings = [ring(x0, r), ring(x1, r)]
    loft(pm, cid, rings, tilefn, meta=meta)


def rot_xf(pivot, deg):
    m = Matrix.Rotation(math.radians(deg), 3, 'Z')
    pv = V(pivot)
    return lambda p: pv + m @ (V(p) - pv)


def offset_poly2d(pts, d):
    """inward offset of a simple 2D polygon (list of (x, y)); mitre limited."""
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n)) / 2.0
    sgn = 1.0 if area > 0 else -1.0
    out = []
    for i in range(n):
        p0, p1, p2 = V((*pts[i - 1], 0)), V((*pts[i], 0)), V((*pts[(i + 1) % n], 0))
        e0, e1 = (p1 - p0).normalized(), (p2 - p1).normalized()
        n0, n1 = V((-e0.y, e0.x, 0)) * sgn, V((-e1.y, e1.x, 0)) * sgn
        bis = (n0 + n1)
        if bis.length < 1e-6:
            bis = n0
        bis.normalize()
        k = max(0.55, bis.dot(n0))
        q = p1 + bis * (d / k)
        out.append((q.x, q.y))
    return out
