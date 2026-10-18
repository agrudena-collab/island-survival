# ----------------------------------------------------------------------------------------------
# containers, coordinate helpers, shading rules, parameters, joints
# ----------------------------------------------------------------------------------------------
PARTS = {}
COMP_LOG = []
SRC_COLL = bpy.data.collections.new("SOURCE_Components")
SCENE.collection.children.link(SRC_COLL)
EXP_COLL = bpy.data.collections.new("EXPORT_MillionaireDad")
SCENE.collection.children.link(EXP_COLL)
HEXOF = {n: h for n, h, _ in PAL}


def Bl(x, f, h):
    """logical (X, F, H) -> Blender point (X, -F, H)."""
    return V((x, -f, h))


def sh_const(name):
    return lambda n, c: name


def shade(base, hi=0.55, lo=-0.55):
    """light from above: base+'Light' on up faces, base+'Shadow' on down faces (only if the tile exists)."""
    up, dn = base + "Light", base + "Shadow"

    def fn(n, c):
        if n.z > hi and up in TILE:
            return up
        if n.z < lo and dn in TILE:
            return dn
        return base
    return fn


sh_skin = shade("Skin")
sh_ivory = shade("Ivory")
sh_gold = shade("Gold")
sh_hair = shade("Hair")
sh_shoe = shade("ShoeWhite")
sh_case = shade("Case")
sh_belt = shade("Belt")
sh_shirt = shade("Shirt")


def sh_skin_arm(n, c):
    if n.z > 0.55:
        return "SkinLight"
    if n.z < -0.55:
        return "SkinShadow"
    return "Skin"


def sh_nose(n, c):
    if n.z < -0.55:
        return "SkinShadow"
    if n.z > 0.45:
        return "NoseLight"
    return "Nose"


# ---------------------------------------------------------------------------------------------------------------------------
# PARAMETERS. Layout decided against the crop (63.75 px per stud: A = 408 px hair top..sole = 6.40 PROJECT CONVENTION, not a measurement);
# the crop sits at (1110,530) on the sheet, so sheet landmarks A..E map to crop pixels by subtracting that origin. Hidden surfaces are neutral guesses.
# ---------------------------------------------------------------------------------------------------------------------------
L1, L2 = 1.00, 0.85       # revision 5: shorter, almost straight blocky arms (the source stacks shoulder block, forearm block, cuff and fist vertically)
RHINT = (-1.0, -0.15, 0.0)          # right elbow OUT (not back): the forearm and the case hang almost vertically
LHINT = (1.0, -0.7, -0.2)            # left elbow out and back, the fist rests at the hip
JOINTS = {
    "Root": (0, 0, 2.35), "Waist": (0, 0, 2.80), "Neck": (0, 0, 4.55),
    "RightShoulder": (-1.85, 0, 4.25), "RightWrist": (-2.50, 0.10, 2.70),
    "LeftShoulder": (1.85, 0, 4.25), "LeftWrist": (1.95, 0.75, 2.95),
    "RightHip": (-0.88, 0, 2.25), "LeftHip": (0.88, 0, 2.25),
    "RightKnee": (-0.88, 0.02, 1.30), "LeftKnee": (0.88, 0.02, 1.30),
    "RightAnkle": (-0.88, 0.02, 0.80), "LeftAnkle": (0.88, 0.02, 0.80),
}
RHAND_DIR = V((0.0, -0.06, -1.0)).normalized()                 # Blender coordinates; the case hand hangs straight down
LHAND_DIR = V((-0.15, -0.45, -0.88)).normalized()              # Blender coordinates; the left fist rests on the hip (down, inward, forward)


def ik_elbow(S, W, L1, L2, hint):
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
HEAD_TOP = 6.40

# torso rows (H, W, Ffront, Fback signed, bevel); D coordinates (front negative); long jacket to H2.00
_TORSO = [(2.00, 3.00, .74, -.68, .13), (2.40, 2.88, .74, -.68, .13), (2.80, 2.90, .76, -.70, .14), (3.30, 3.10, .80, -.72, .16),
          (3.85, 3.25, .80, -.72, .17), (4.30, 3.10, .70, -.68, .16), (4.55, 2.80, .58, -.62, .14)]
TORSO = [(h, w, -ff, -fb, c) for h, w, ff, fb, c in _TORSO]
TORSO_TOP = TORSO[-1][0]
TORSO_BOT = TORSO[0][0]
LOWER_ROWS = [r for r in TORSO if r[0] <= 2.80 + 1e-9]
UPPER_ROWS = [r for r in TORSO if r[0] >= 2.80 - 1e-9]


def tfront(x, h):
    return front_at(TORSO, min(max(h, TORSO_BOT), TORSO_TOP), x)


def tback(x, h):
    return back_at(TORSO, min(max(h, TORSO_BOT), TORSO_TOP), x)


def cap_tris2(idxs, pts2d):
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
    """polygon in (X, H) swept between logical F=f0 (rear) and F=f1 (front)."""
    n = len(poly_xh)
    P = [Bl(x, f0, h) for x, h in poly_xh] + [Bl(x, f1, h) for x, h in poly_xh]
    faces = [[k, (k + 1) % n, n + (k + 1) % n, n + k] for k in range(n)]
    faces += cap_tris2(list(range(n)), poly_xh) + cap_tris2(list(range(n, 2 * n)), poly_xh)
    pm.solid(cid, P, faces, tilefn, meta)


def prism_bm(poly_xh, f0, f1, tile):
    n = len(poly_xh)
    P = [Bl(x, f0, h) for x, h in poly_xh] + [Bl(x, f1, h) for x, h in poly_xh]
    faces = [[k, (k + 1) % n, n + (k + 1) % n, n + k] for k in range(n)]
    faces += cap_tris2(list(range(n)), poly_xh) + cap_tris2(list(range(n, 2 * n)), poly_xh)
    return solid_tiled(P, faces, tile)


def plate_bm(outline, fit, layers, tile):
    """closed plate following a surface: layers=[(dD, sx, sh)], first layer = back; used as boolean cutter."""
    cx = sum(p[0] for p in outline) / len(outline)
    ch = sum(p[1] for p in outline) / len(outline)
    n = len(outline)
    P = []
    for dD, sx, sh in layers:
        for x, h in outline:
            xx, hh = cx + (x - cx) * sx, ch + (h - ch) * sh
            P.append(V((xx, fit(xx, hh) + dD, hh)))
    faces = []
    for i in range(len(layers) - 1):
        for k in range(n):
            faces.append([i * n + k, i * n + (k + 1) % n, (i + 1) * n + (k + 1) % n, (i + 1) * n + k])
    faces += cap_tris(P, list(range(n)))
    faces += cap_tris(P, list(range((len(layers) - 1) * n, len(layers) * n)))
    return solid_tiled(P, faces, tile)


def patch_box(pm, cid, cx, fc, hc, w, d, hh, tile, embed=0.03, meta=None):
    solid_box(pm, cid, cx - w / 2, cx + w / 2, -(fc + d / 2), -(fc - d / 2) + embed, hc - hh / 2, hc + hh / 2, tile, meta)


def cyl_y(pm, cid, cx, cz, y0, y1, r, segs, tilefn, meta=None):
    """cylinder along Blender Y (the character's front/back axis) between y0 and y1."""
    def ring(y):
        return [V((cx + r * math.cos(2 * math.pi * k / segs), y, cz + r * math.sin(2 * math.pi * k / segs))) for k in range(segs)]
    loft(pm, cid, [ring(y0), ring(y1)], tilefn, meta=meta)


def cyl_x(pm, cid, cx, cy, cz, length, r, segs, tilefn, ch=0.0, meta=None):
    x0, x1 = cx - length / 2, cx + length / 2

    def ring(x, rr):
        return [V((x, cy + rr * math.cos(2 * math.pi * k / segs), cz + rr * math.sin(2 * math.pi * k / segs))) for k in range(segs)]
    if ch > 0:
        rings = [ring(x0, r - ch), ring(x0 + ch, r), ring(x1 - ch, r), ring(x1, r - ch)]
    else:
        rings = [ring(x0, r), ring(x1, r)]
    loft(pm, cid, rings, tilefn, meta=meta)


def rot_xf(pivot, deg, axis='Z'):
    m = Matrix.Rotation(math.radians(deg), 3, axis)
    pv = V(pivot)
    return lambda p: pv + m @ (V(p) - pv)


def ellipse(cx, cz, rx, rz, n=14, rot=0.0):
    c, s = math.cos(rot), math.sin(rot)
    return [(cx + rx * math.cos(2 * math.pi * k / n) * c - rz * math.sin(2 * math.pi * k / n) * s,
             cz + rx * math.cos(2 * math.pi * k / n) * s + rz * math.sin(2 * math.pi * k / n) * c) for k in range(n)]


class AxisG:
    """Limb frame: L from the proximal to the distal point, U = world X projected across L (width), W = A x U (depth)."""

    def __init__(self, P0, P1):
        self.P0, self.P1 = V(P0), V(P1)
        d = self.P1 - self.P0
        self.L = d.length
        self.A = d / self.L
        u = V((1, 0, 0)) - self.A * V((1, 0, 0)).dot(self.A)
        if u.length < 0.3:
            u = V((0, -1, 0)) - self.A * V((0, -1, 0)).dot(self.A)
        self.U = u.normalized()
        self.W = self.A.cross(self.U).normalized()

    def at(self, t):
        return self.P0 + self.A * (self.L * t)

    def corners(self, w, d, c):
        a, b = w / 2.0, d / 2.0
        c = min(c, a - 1e-4, b - 1e-4)
        return [(-a + c, -b), (a - c, -b), (a, -b + c), (a, b - c), (a - c, b), (-a + c, b), (-a, b - c), (-a, -b + c)]

    def ring(self, t, w, d, c, ox=0.0, oy=0.0):
        P = self.at(t)
        return [P + self.U * (x + ox) + self.W * (y + oy) for x, y in self.corners(w, d, c)]

    def pt(self, t, x, y):
        return self.at(t) + self.U * x + self.W * y


def abox(pm, cid, ax, t0, t1, x0, x1, y0, y1, tile, meta=None):
    """box in the limb frame: t along the axis (fraction of L), x across U, y across W."""
    r0 = [ax.pt(t0, x0, y0), ax.pt(t0, x1, y0), ax.pt(t0, x1, y1), ax.pt(t0, x0, y1)]
    r1 = [ax.pt(t1, x0, y0), ax.pt(t1, x1, y0), ax.pt(t1, x1, y1), ax.pt(t1, x0, y1)]
    loft(pm, cid, [r0, r1], tile, meta=meta)


def sweep(pm, cid, path, wfn, hfn, c, tilefn, meta=None):
    """tube with an octagon section along a path (Blender points); wfn/hfn(t) -> width/height; up reference = world Z."""
    n = len(path)
    rings = []
    for i, p in enumerate(path):
        tg = (path[min(i + 1, n - 1)] - path[max(i - 1, 0)]).normalized()
        side = tg.cross(V((0, 0, 1)))
        if side.length < 1e-4:
            side = V((1, 0, 0))
        side.normalize()
        up = side.cross(tg).normalized()
        t = i / (n - 1)
        a, b = wfn(t) / 2.0, hfn(t) / 2.0
        cc = min(c, a - 1e-4, b - 1e-4)
        pts = [(-a + cc, -b), (a - cc, -b), (a, -b + cc), (a, b - cc), (a - cc, b), (-a + cc, b), (-a, b - cc), (-a, -b + cc)]
        rings.append([p + side * x + up * y for x, y in pts])
    loft(pm, cid, rings, tilefn, meta=meta)
