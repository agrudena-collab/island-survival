

# ----------------------------------------------------------------------------------------------
# rod axis (section 20) - needed by the grip channel in the left hand and by the rod itself
# ----------------------------------------------------------------------------------------------
ROD_A = [  # (X, D, H, outer diameter)
    (2.20, -.65, .10, .18), (2.20, -.65, 2.20, .15), (2.22, -.65, 2.70, .115), (2.24, -.65, 3.50, .095),
    (2.30, -.65, 4.20, .080), (2.42, -.65, 5.20, .064), (2.67, -.65, 6.35, .043), (2.88, -.65, 7.35, .028)]
ROD_PTS = [V(a[:3]) for a in ROD_A]
ROD_DENSE = catmull(ROD_PTS, 6)          # smooth axis through the A points (passes exactly through every A_i)


def rod_axis(h):
    """Axis point (X,-.65,h) of the smoothed rod axis (X, D interpolated on the dense polyline, monotonic in H)."""
    pts = ROD_DENSE
    if h <= pts[0].z:
        return V((pts[0].x, pts[0].y, h))
    for a, b in zip(pts, pts[1:]):
        if a.z <= h <= b.z and b.z > a.z:
            t = (h - a.z) / (b.z - a.z)
            return V((a.x + (b.x - a.x) * t, a.y, h))
    return V((pts[-1].x, pts[-1].y, h))


def rod_diam(h):
    for a, b in zip(ROD_A, ROD_A[1:]):
        if a[2] <= h <= b[2]:
            return a[3] + (b[3] - a[3]) * (h - a[2]) / (b[2] - a[2])
    return ROD_A[-1][3] if h > ROD_A[-1][2] else ROD_A[0][3]


def rod_tangent(h):
    a, b = rod_axis(h - .01), rod_axis(h + .01)
    return (b - a).normalized()


# ----------------------------------------------------------------------------------------------
# arm shells: shoulder / elbow / wrist (right arm neutral, left arm directly in the HoldRod pose)
# ----------------------------------------------------------------------------------------------
UP_SKIN = [(0.0, .88, .82), (.70, .81, .76), (1.0, .76, .70)]
LO_SEC = [(0.0, .75, .69), (.48, .70, .65), (1.0, .64, .59)]


def tile_layer_set(bm, fn, keep=("SKIN_SHADOW",)):
    tl = bm.faces.layers.int.get("tile") or bm.faces.layers.int.new("tile")
    for f in bm.faces:
        f.normal_update()
        cur = PAL[f[tl]][0]
        if cur in keep:
            continue
        f[tl] = TILE[fn(f.normal.copy(), f.calc_center_median())]


def build_arm(side, S, E, W):
    s = -1 if side == "Right" else 1
    ua = PM(side + "UpperArm", S)
    lu = Limb(S, E)
    L1 = lu.L
    sl = [(-.02, .98, .91), (0.0, .98, .91), (.64, .954, .886), (.73, .95, .88)]
    loft(ua, "UA_sleeve_" + side, [lu.ring(t, w, d, .10) for t, w, d in sl], sh_shirt,
         meta=meta("short yellow sleeve t0..0.73, .98 x .91 -> .95 x .88"))
    cuff = [lu.ring(.64, .954, .886, .09), lu.ring(.652, .954, .886, .09, .025), lu.ring(.718, .95, .88, .09, .025), lu.ring(.73, .95, .88, .09)]
    loft(ua, "UA_cuff_" + side, cuff, lambda n, c: "SHIRT_SHADOW" if n.z < -.45 else ("SHIRT_LIGHT" if n.z > .55 else "SHIRT"),
         meta=meta("sleeve cuff t.64..0.73, proud .025, SHIRT_SHADOW underside"))
    sec = [(-.0, .88, .82), (.70, .81, .76), (1.0, .76, .70), (1.0 + .02 / L1, .76, .70)]
    loft(ua, "UA_skin_" + side, [lu.ring(t, w, d, .09) for t, w, d in sec], sh_skin_arm,
         meta=meta("upper-arm skin .88x.82 -> .81x.76 -> .76x.70"))
    la = PM(side + "LowerArm", E)
    ll = Limb(E, W)
    ext = .02 if side == "Right" else -.03
    lsec = [(-.02 / ll.L, .75, .69), (0.0, .75, .69), (.48, .70, .65), (1.0, .64, .59), (1.0 + ext / ll.L, .64, .59)]
    loft(la, "LA_forearm_" + side, [ll.ring(t, w, d, .08) for t, w, d in lsec], sh_skin_arm,
         meta=meta("forearm .75x.69 -> .70x.65 -> .64x.59, closed caps"))
    return lu, ll


LUA, LLA = build_arm("Right", JV["RightShoulder"], JV["RightElbow"], JV["RightWrist"])
RUA, RLA = build_arm("Left", JV["LeftShoulder"], JV["LeftElbow"], JV["LeftWrist"])


# ----------------------------------------------------------------------------------------------
# hands (sections 18, 19)
# ----------------------------------------------------------------------------------------------
def cutter(P, faces, tile="SKIN_SHADOW"):
    bm = solid_tiled(P, faces, tile)
    ob = bm_to_obj(bm, "tmp_cut")
    bm.free()
    return ob


def apply_cut(o, co, op):
    bool_apply(o, co, op)
    bpy.data.objects.remove(co, do_unlink=True)


def finish_hand(pm, cid, o, joint, side, meta_):
    bm = obj_to_bm(o)
    bpy.data.objects.remove(o, do_unlink=True)
    tile_layer_set(bm, sh_skin_arm)
    pm.append_bm(cid, bm, None, meta_)
    bm.free()


# free right hand: centre (-2.08,-.12,1.89), W .72 D .66 H .70, bevel .055, thumb on the inner side, lower notch .15 x .22 x .20
hr = PM("RightHand", JV["RightWrist"])
c = V((-2.08, -.12, 1.89))
base = box_solid(c.x - .36, c.x + .36, c.y - .33, c.y + .33, c.z - .35, c.z + .35, "SKIN", ch=.055)
o = bm_to_obj(base, "tmp_hand")
base.free()
notch = box_solid(c.x - .075, c.x + .075, c.y - .34, c.y - .34 + .21, c.z - .36, c.z - .36 + .23, "SKIN_SHADOW")
thumb = box_solid(-1.76 - .08, -1.76 + .08, -.31 - .07, -.31 + .07, 1.97 - .14, 1.97 + .14, "SKIN", ch=.03)
for nm, bmx, op in (("notch", notch, 'DIFFERENCE'), ("thumb", thumb, 'UNION')):
    co = bm_to_obj(bmx, "tmp_" + nm)
    bmx.free()
    apply_cut(o, co, op)
finish_hand(hr, "HAND_Right", o, JV["RightWrist"], "Right",
            meta("free right hand block .72 x .66 x .70, inner thumb .16 x .14 x .28, lower notch .15 x .22 x .20 (boolean EXACT)"))

# left grip hand: centre G=(2.24,-.65,3.50), .72 x .68 x .80; rod channel r=.065 sweeping along the real rod axis,
# slot W .07 opening only to the REAR face, thumb pad, three finger grooves on the front face
hl = PM("LeftHand", JV["LeftWrist"])
G = GRIP_C
base = box_solid(G.x - .36, G.x + .36, G.y - .34, G.y + .34, G.z - .40, G.z + .40, "SKIN", ch=.055)
o = bm_to_obj(base, "tmp_hand")
base.free()
HLV = [3.04 + .12 * i for i in range(8)]                      # H 3.04 .. 3.88 + (hand spans 3.10..3.90)
HLV = [3.04, 3.20, 3.35, 3.50, 3.65, 3.80, 3.96]
R_CH = .065
chan_rings, slot_rings = [], []
for h in HLV:
    a = rod_axis(h)
    ca = abs(rod_tangent(h).z)
    chan_rings.append([V((a.x + (R_CH / ca) * math.cos(2 * math.pi * k / 12), a.y + R_CH * math.sin(2 * math.pi * k / 12), h)) for k in range(12)])
    slot_rings.append([V((a.x - .035, a.y, h)), V((a.x + .035, a.y, h)), V((a.x + .035, G.y + .34 + .05, h)), V((a.x - .035, G.y + .34 + .05, h))])
for nm, rings in (("chan", chan_rings), ("slot", slot_rings)):
    n_ = len(rings[0])
    P = [p for r in rings for p in r]
    co = cutter(P, loft_faces(len(rings), n_))
    apply_cut(o, co, 'DIFFERENCE')
tb = box_solid(1.95 - .08, 1.95 + .08, -.95 - .07, -.95 + .07, 3.60 - .14, 3.60 + .14, "SKIN", ch=.03)
co = bm_to_obj(tb, "tmp_thumb")
tb.free()
apply_cut(o, co, 'UNION')
for gh in (3.30, 3.48, 3.66):
    gb = box_solid(G.x - .165, G.x + .165, G.y - .34 - .01, G.y - .34 + .008, gh - .006, gh + .006, "SKIN_SHADOW")
    co = bm_to_obj(gb, "tmp_g")
    gb.free()
    apply_cut(o, co, 'DIFFERENCE')
finish_hand(hl, "HAND_Left", o, JV["LeftWrist"], "Left",
            meta("grip hand .72 x .68 x .80 at G; 12-gon rod channel r.065 (clearance .0175) sweeping the rod axis, rear slot W.07, thumb pad, 3 finger grooves (boolean EXACT)"))


# the forearm stub ends inside the grip hand: carve the same rod channel through it so the rod never enters skin
def carve_forearm():
    pm = PARTS["LeftLowerArm"]
    me = bpy.data.meshes.new("tmp_fa")
    pm.bm.to_mesh(me)
    fo = bpy.data.objects.new("tmp_fa", me)
    SCENE.collection.objects.link(fo)
    rings = chan_rings
    P = [p for r in rings for p in r]
    co = cutter(P, loft_faces(len(rings), len(rings[0])))
    apply_cut(fo, co, 'DIFFERENCE')
    bm2 = obj_to_bm(fo)
    bpy.data.objects.remove(fo, do_unlink=True)
    tile_layer_set(bm2, sh_skin_arm)
    pm.bm.free()
    pm.bm = bm2
    pm.tl = bm2.faces.layers.int.get("tile")


carve_forearm()
