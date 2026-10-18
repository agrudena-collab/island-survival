

# ----------------------------------------------------------------------------------------------
# arms: two-segment IK limbs with a shared mitre contour at the elbow (no gap on the outer side of the bend)
# ----------------------------------------------------------------------------------------------
class AxisG:
    """Limb frame (section 14): L from the proximal to the distal joint, U = world X projected across L (width), W = L x U."""

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
        return [(-a + c, -b), (a - c, -b), (a, -b + c), (a, b - c), (a - c, b), (-a + c, b), (-a, b - c), (-a, -b + c)]

    def ring(self, t, w, d, c):
        P = self.at(t)
        return [P + self.U * x + self.W * y for x, y in self.corners(w, d, c)]


# V2 sections (W, D): massive shoulder mass -> elbow transition -> wide forearm; same for both arms (the pose alone makes the projections differ)
UPPER_SEC = [(0.0, 1.55, 1.45), (.30, 1.58, 1.46), (.70, 1.38, 1.30), (1.0, 1.20, 1.15)]
_FW, _FD = (float(c) for c in os.environ.get("GYM_FAEND", ".84,.74").split(","))
LOWER_SEC = [(0.0, 1.20, 1.15), (.40, 1.15, 1.10), (.75, (1.02 + _FW) / 2, (.98 + _FD) / 2), (1.0, _FW, _FD)]
ARM_C = .17
OVERLAP = .04
ARM_AX = {}
ELBOW_RING = {}
for s in (-1, 1):
    side = "Right" if s < 0 else "Left"
    S, E, W_ = JV[side + "Shoulder"], JV[side + "Elbow"], JV[side + "Wrist"]
    ax1, ax2 = AxisG(S, E), AxisG(E, W_)
    ARM_AX[side] = (ax1, ax2)
    N = (ax1.A + ax2.A).normalized()
    # shared mitre contour K: the end section of the upper arm cut by the bisector plane through the elbow
    K = []
    for x, y in ax1.corners(UPPER_SEC[-1][1], UPPER_SEC[-1][2], ARM_C):
        p = E + ax1.U * x + ax1.W * y
        K.append(p - ax1.A * (((p - E).dot(N)) / ax1.A.dot(N)))
    ELBOW_RING[side] = K
    ua = PM(side + "UpperArm", S)
    t0 = -OVERLAP / ax1.L
    rings = [ax1.ring(t0, UPPER_SEC[0][1], UPPER_SEC[0][2], ARM_C)] + [ax1.ring(t, w, d, ARM_C) for t, w, d in UPPER_SEC[1:-1]] + [K]
    loft(ua, "UA_arm_" + side, rings, sh_skin_arm, meta={"recipe": "upper arm W/D 1.08/1.03 -> .91/.88, rectangular section chamfer .11, ends overlap .04, elbow end = mitre contour", "class": "prescribed"})
    la = PM(side + "LowerArm", E)
    ts = [.14, .40, .75, 1.0 + OVERLAP / ax2.L]
    secw = lambda t: sec_at(LOWER_SEC, min(t, 1.0))
    lr = [ax2.ring(t, *secw(t), ARM_C) for t in ts]
    best = min(range(8), key=lambda sh: sum((K[k] - lr[0][(k + sh) % 8]).length for k in range(8)))
    lr = [[r[(k + best) % 8] for k in range(8)] for r in lr]
    loft(la, "LA_forearm_" + side, [K] + lr, sh_skin_arm, meta={"recipe": "forearm W/D .91/.88 -> .70/.68, first ring = shared elbow contour (ring order shift %d), end overlap .04" % best, "class": "prescribed"})

# ----------------------------------------------------------------------------------------------
# hands: heavy solid fists, separate wrist / geometric centre / grip frames
# ----------------------------------------------------------------------------------------------
FR, FL = FIST_R, FIST_L
rh = PM("RightHand", JV["RightWrist"])
loft(rh, "HAND_palm_Right", cbox(Bl(*FR), (.78, .98, .98), .13), sh_skin_arm, meta={"recipe": "right fist centre %s size .78/.98/.98 bevel .13 (closed; the grip passes through hidden)" % (FR,), "class": "v2"})
loft(rh, "HAND_thumb_Right", cbox(Bl(FR[0] + .42, FR[1] - .02, FR[2] + .26), (.30, .50, .38), .08), sh_const("SkinLight"), meta={"recipe": "integrated thumb block on the inner side, overlaps the fist", "class": "v2"})
for k, h in enumerate((FR[2] - .10, FR[2] + .10)):
    patch_box(rh, "HAND_fingerline_Right_%d" % (k + 1), FR[0], FR[1] + .48 + .003, h, .56, .012, .014, "SkinShadow", meta={"recipe": "flat finger crease", "class": "v2"})
lh = PM("LeftHand", JV["LeftWrist"])
loft(lh, "HAND_palm_Left", cbox(Bl(*FL), (.76, .96, .96), .14), sh_skin_arm, meta={"recipe": "left fist centre %s size .76/.96/.96 bevel .14, bag loops held below centre" % (FL,), "class": "v2"})
loft(lh, "HAND_thumb_Left", cbox(Bl(FL[0] - .47, FL[1] + .06, FL[2] + .08), (.26, .46, .40), .08), sh_const("SkinLight"), meta={"recipe": "integrated thumb block on the inner side", "class": "v2"})
for k, h in enumerate((FL[2] - .10, FL[2] + .10)):
    patch_box(lh, "HAND_fingerline_Left_%d" % (k + 1), FL[0], FL[1] + .48 + .003, h, .56, .012, .014, "SkinShadow", meta={"recipe": "flat finger crease", "class": "v2"})
