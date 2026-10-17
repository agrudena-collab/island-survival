

# ----------------------------------------------------------------------------------------------
# arms: sleeves with ONE common elbow contour, rib cuffs, blocky hands (right hand with the open can recess)
# ----------------------------------------------------------------------------------------------
UP_SECS = [(0.0, 0.88, 0.92, 0.10), (0.5, 0.84, 0.87, 0.10), (1.0, 0.78, 0.80, 0.08)]       # t from the shoulder S: width U, depth Q, bevel
LO_SECS = [(0.0, 0.78, 0.80, 0.08), (1.0, 0.70, 0.70, 0.08)]                               # t from the elbow E
ELBOW_LOG = {}


def sec_lin(secs, t):
    """(w, d, c) of a section table at t (clamped linear)."""
    if t <= secs[0][0]:
        return secs[0][1:]
    if t >= secs[-1][0]:
        return secs[-1][1:]
    for a, b in zip(secs, secs[1:]):
        if a[0] <= t <= b[0]:
            u = (t - a[0]) / (b[0] - a[0])
            return tuple(a[i] + (b[i] - a[i]) * u for i in range(1, 4))


def oct_pts(w, d, c):
    a, h = w / 2.0, d / 2.0
    c = min(c, a - 1e-4, h - 1e-4)
    return [(-a + c, -h), (a - c, -h), (a, -h + c), (a, h - c), (a - c, h), (-a + c, h), (-a, h - c), (-a, -h + c)]


def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def build_arm(side, S, E, W):
    """UpperArm along S->E, LowerArm along E->W. Both sleeves end on the common mitre plane through E (normal N = normalize(Au + Al)):
    the upper tube is cut by the plane, its 8-point cut contour K becomes the first ring of the lower tube, which then rolls into its own forearm frame.
    No overlap beyond the joint, no cap or ball at the elbow."""
    ua = PM(side + "UpperArm", S)
    lu = Limb(S, E)
    la = PM(side + "LowerArm", E)
    ll = Limb(E, W)
    L1, L2 = lu.L, ll.L
    Au, Al = lu.A, ll.A
    N = (Au + Al).normalized()
    an = Au.dot(N)
    assert an > 0.2 and Al.dot(N) > 0.2, (side, an, Al.dot(N))

    def sd(p):
        return (p - E).dot(N)
    # ---- upper tube: stations from S-.08 to beyond E, each ring line is cut by the plane
    EXT = 0.60
    base = [(-0.08 / L1, 0.88, 0.92, 0.10)] + UP_SECS + [(1.0 + EXT / L1, 0.78, 0.80, 0.08)]

    def ring_at(t):
        w, d, c = sec_lin([(b[0], b[1], b[2], b[3]) for b in base], t)
        return lu.ring(t, w, d, c)
    ts = [b[0] for b in base]
    cross = []
    for k in range(8):
        found = None
        for t0, t1 in zip(ts, ts[1:]):
            s0, s1 = sd(ring_at(t0)[k]), sd(ring_at(t1)[k])
            if s0 < 0.0 <= s1:
                found = t0 + (t1 - t0) * (-s0) / (s1 - s0)
                break
        assert found is not None, (side, k)
        cross.append(found)
    K = [ring_at(cross[k])[k] for k in range(8)]
    for p in K:
        assert abs(sd(p)) < 1e-5
    stations = sorted(set([round(t, 9) for t in ts if t < max(cross)] + [round(c, 9) for c in cross]))
    rings_u = []
    for t in stations:
        base_ring = ring_at(t)
        rings_u.append([base_ring[k] if t <= cross[k] + 1e-9 else K[k] for k in range(8)])
    # weld coincident points, build the closed solid
    uniq, canon, ids = [], {}, []
    for r in rings_u:
        for p in r:
            key = (round(p.x * 1e5), round(p.y * 1e5), round(p.z * 1e5))
            if key not in canon:
                canon[key] = len(uniq)
                uniq.append(V(p))
            ids.append(canon[key])
    faces = [[ids[i] for i in f] for f in loft_faces(len(rings_u), 8)]
    ua.solid("UA_sleeve_" + side, uniq, faces, sh_sweat,
             meta("sleeve .88x.92 -> .84x.87 -> .78x.80 (bevel .10 -> .08), hidden .08 into the torso, ends on the common elbow mitre plane (8-point contour K)", sections=UP_SECS))
    # ---- lower tube: K -> straight to the axial level of the farthest K point -> roll into the own forearm frame
    ax = [(p - E).dot(Al) for p in K]
    lat = [(p - E) - Al * a for p, a in zip(K, ax)]
    s_hi = max(ax) + 1e-4
    # match every K vertex with a vertex of the forearm octagon by angle (even shifts keep the orientation, odd shifts with reversed order mirror it)
    Ul, Ql = ll.U, ll.Q

    def ang(v):
        return math.atan2(v.dot(Ql), v.dot(Ul))
    w0, d0, c0 = LO_SECS[0][1:]
    tbl0 = oct_pts(w0, d0, c0)
    phi = [math.atan2(y, x) for x, y in tbl0]
    th = [ang(v) for v in lat]
    best = None
    for o in (1, -1):
        for m in range(8):
            if (o == 1 and m % 2) or (o == -1 and m % 2 == 0):
                continue
            err = 0.0
            for i in range(8):
                j = (i + m) % 8 if o == 1 else (m - i) % 8
                dd = (th[i] - phi[j] + math.pi) % (2 * math.pi) - math.pi
                err += abs(dd)
            if best is None or err < best[0]:
                best = (err, o, m)
    _, o_, m_ = best
    jmap = [((i + m_) % 8 if o_ == 1 else (m_ - i) % 8) for i in range(8)]
    t_beta0 = s_hi / L2
    t_beta1 = max(t_beta0 + 0.12, 0.70)

    def lring(t):
        w, d, c = sec_lin(LO_SECS, t)
        tb = oct_pts(w, d, c)
        beta = smooth01((t - t_beta0) / (t_beta1 - t_beta0))
        P = E + Al * (t * L2)
        out = []
        for i in range(8):
            x, y = tb[jmap[i]]
            target = Ul * x + Ql * y
            off = lat[i] * (1.0 - beta) + target * beta
            out.append(P + off)
        return out
    tts = []
    for t in (t_beta0, 0.5 * (t_beta0 + t_beta1), t_beta1, 0.85, 1.0):
        if not tts or t > tts[-1] + 1e-6:
            tts.append(t)
    rings_l = [K] + [lring(t) for t in tts]
    # closing ring at the wrist: a slightly smaller copy .02 further, so the end is a flat closed cap
    rings_l.append([P_ - Al * 0.0 + Al * (0.02) for P_ in rings_l[-1]])
    P = [p for r in rings_l for p in r]
    la.solid("LA_sleeve_" + side, P, loft_faces(len(rings_l), 8), sh_sweat,
             meta("forearm sleeve: first ring = common contour K, rolled into the own frame; .78x.80 -> .70x.70 (bevel .08), beta from t=%.3f to %.3f; K match o=%d m=%d" % (t_beta0, t_beta1, o_, m_), sections=LO_SECS))
    # ---- rib cuff t .77 .. 1.02 (.76 x .76, bevel .045), own forearm frame, CUFF
    cuff = []
    for t, wd in ((0.77, 0.72), (0.785, 0.76), (1.0, 0.76), (1.02, 0.72)):
        cuff.append(ll.ring(t, wd, wd, 0.045))
    loft(la, "LA_cuff_" + side, cuff, sh_const("CUFF"), meta=meta("rib cuff t.77..1.02, .76 x .76, bevel .045, CUFF, no ribs"))
    ELBOW_LOG[side] = {"N": tuple(N), "deflection_deg": math.degrees(math.acos(max(-1, min(1, Au.dot(Al))))), "contour_K": [tuple(p) for p in K], "cross_t_upper": cross,
                       "lower_K_axial": ax, "lower_match": {"orientation": o_, "shift": m_}, "beta_t": [t_beta0, t_beta1], "upper_len": L1, "lower_len": L2}
    return lu, ll


R_UA, R_LA = build_arm("Right", JV["RightShoulder"], JV["RightElbow"], JV["RightWrist"])
L_UA, L_LA = build_arm("Left", JV["LeftShoulder"], JV["LeftElbow"], JV["LeftWrist"])

# ---- hands: chamfer box + fused thumb (boolean union), right hand with the open can recess (cylinder R.328 coaxial with the can), flat finger lines
CAN_AXIS = (-1.62, -1.32)
CAN_RAD_REC = 0.328


def sh_skin_hand(n, c):
    if n.z > 0.55:
        return "SKIN_LIGHT"
    if n.z < -0.55:
        return "SKIN_SHADOW"
    return "SKIN"


def make_hand(side, palm_c, palm_size, thumb_c, thumb_size, cutters):
    hp = PM(side + "Hand", JV[side + "Wrist"])
    palm = make_bm_solid([p for r in cbox(palm_c, palm_size, 0.055) for p in r], loft_faces(4, 8))
    thumb = make_bm_solid([p for r in cbox(thumb_c, thumb_size, 0.04) for p in r], loft_faces(4, 8))
    o = bm_to_obj(palm, "tmp_palm")
    ot = bm_to_obj(thumb, "tmp_thumb")
    bool_apply(o, ot, 'UNION')
    bpy.data.objects.remove(ot, do_unlink=True)
    palm.free()
    thumb.free()
    for cb in cutters:
        co = bm_to_obj(cb, "tmp_cut")
        bool_apply(o, co, 'DIFFERENCE')
        bpy.data.objects.remove(co, do_unlink=True)
        cb.free()
    bm = obj_to_bm(o)
    bpy.data.objects.remove(o, do_unlink=True)
    retile(bm, sh_skin_hand)
    hp.append_bm("HAND_palm_" + side, bm, None, meta("chamfer box %s bevel .055 with the fused thumb block %s bevel .04 (boolean union, one shell)" % (palm_size, thumb_size)))
    bm.free()
    COMP_LOG.append({"id": "HAND_thumb_" + side, "owner": side + "Hand", "kind": "merged", "recipe": "thumb block %s fused with the palm (boolean union)" % (thumb_size,), "faces": 0, "tris": 0, "class": "prescribed"})
    return hp


rh_c, lh_c = SPEC_IN["hand_centers"]["Right"], SPEC_IN["hand_centers"]["Left"]
rec_cut = cyl_solid(CAN_AXIS[0], CAN_AXIS[1], rh_c[2] - 0.7, rh_c[2] + 0.7, CAN_RAD_REC, "SKIN_SHADOW", segs=32)
RHP = make_hand("Right", rh_c, (0.70, 0.64, 0.82), (-1.96, -1.48, 3.93), (0.18, 0.22, 0.26), [rec_cut])
# left hand: small thumb notch open to -X (under the thumb)
lt_notch = box_solid(1.58, 1.70, -0.41, -0.19, 2.268, 2.3215, "SKIN_SHADOW", ch=0.0)
LHP = make_hand("Left", lh_c, (0.70, 0.64, 0.72), (1.68, -0.30, 2.4515283654817543), (0.18, 0.22, 0.26), [lt_notch])
# recess wall in SKIN_SHADOW (inside the can radius), finger lines: exactly two flat lines per hand, width .008, length .35 at H-.14 and H+.12
for hp, side, c in ((RHP, "Right", rh_c), (LHP, "Left", lh_c)):
    cid = "HAND_palm_" + side
    if side == "Right":
        for f in hp.faces_of(cid):
            f.normal_update()
            cc = f.calc_center_median()
            if math.hypot(cc.x - CAN_AXIS[0], cc.y - CAN_AXIS[1]) < CAN_RAD_REC + 0.004 and abs(f.normal.z) < 0.3:
                f[hp.tl] = TILE["SKIN_SHADOW"]
    planes = []
    for dh in (-0.14, 0.12):
        h = c[2] + dh
        planes += [((0, 0, h + 0.004), (0, 0, 1)), ((0, 0, h - 0.004), (0, 0, 1))]
    planes += [((c[0] + 0.175, 0, 0), (1, 0, 0)), ((c[0] - 0.175, 0, 0), (1, 0, 0))]
    fr = lambda f: f.normal.y < -0.9 and f.calc_center_median().y < c[1] - 0.2
    n_g = hp.paint(cid, "SKIN_SHADOW", lambda f: f.normal.y < -0.9 and abs(f.calc_center_median().x - c[0]) < 0.176 and any(abs(f.calc_center_median().z - (c[2] + dh)) < 0.0041 for dh in (-0.14, 0.12)),
                   planes=planes, only=fr)
    COMP_LOG.append({"id": "HAND_grooves_" + side, "owner": side + "Hand", "kind": "paint", "recipe": "two flat SKIN_SHADOW lines .008 x .35 at H-.14 and H+.12 on the front face, no geometry", "faces": n_g, "tris": 0, "class": "prescribed"})
