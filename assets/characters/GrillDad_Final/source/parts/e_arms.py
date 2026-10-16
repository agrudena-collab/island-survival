

# ----------------------------------------------------------------------------------------------
# tongs branch centres u(H) (section 24): X = 2.30 +/- u
# ----------------------------------------------------------------------------------------------
TONG_U = [(2.56, .055), (3.10, .080), (3.50, .100), (4.25, .145), (4.30, .150), (4.72, .210), (5.05, .265), (5.45, .310), (5.92, .325)]


def branch_u(h):
    if h <= TONG_U[0][0]:
        return TONG_U[0][1]
    for (h0, u0), (h1, u1) in zip(TONG_U, TONG_U[1:]):
        if h0 <= h <= h1:
            return u0 + (u1 - u0) * (h - h0) / (h1 - h0)
    return TONG_U[-1][1]


def tile_layer_set(bm, fn, keep=("SKIN_SHADOW",)):
    tl = bm.faces.layers.int.get("tile") or bm.faces.layers.int.new("tile")
    for f in bm.faces:
        f.normal_update()
        cur = PAL[f[tl]][0]
        if cur in keep:
            continue
        f[tl] = TILE[fn(f.normal.copy(), f.calc_center_median())]


UP_SKIN = [(0.0, .94, .88), (.70, .84, .79), (1.0, .78, .73)]
LO_SEC = [(0.0, .77, .72), (.50, .70, .65), (1.0, .64, .59)]


def build_arm(side, S, E, W):
    ua = PM(side + "UpperArm", S)
    lu = Limb(S, E)
    L1 = lu.L
    sl = [(-.02, .99, .93), (0.0, .99, .93), (.63, .89, .84), (.73, .885, .835)]
    loft(ua, "UA_sleeve_" + side, [lu.ring(t, w, d, .09) for t, w, d in sl], sh_shirt, meta=meta("short red sleeve t0..0.73, skin section + .05"))
    cuff = [lu.ring(.63, .89, .84, .08), lu.ring(.64, .89, .84, .08, .02), lu.ring(.715, .885, .835, .08, .02), lu.ring(.73, .885, .835, .08)]
    loft(ua, "UA_cuff_" + side, cuff, lambda n, c: "SHIRT_LIGHT" if n.z > .55 else "SHIRT_DARK", meta=meta("sleeve cuff band .10 along the segment, SHIRT_DARK"))
    sec = [(0.0, .94, .88), (.70, .84, .79), (1.0, .78, .73), (1.0 + .02 / L1, .78, .73)]
    loft(ua, "UA_skin_" + side, [lu.ring(t, w, d, .09) for t, w, d in sec], sh_skin_arm, meta=meta("upper-arm skin .94x.88 -> .84x.79 -> .78x.73"))
    la = PM(side + "LowerArm", E)
    ll = Limb(E, W)
    ext = .02 if side == "Right" else -.03
    lsec = [(-.02 / ll.L, .77, .72), (0.0, .77, .72), (.50, .70, .65), (1.0, .64, .59), (1.0 + ext / ll.L, .64, .59)]
    loft(la, "LA_forearm_" + side, [ll.ring(t, w, d, .08) for t, w, d in lsec], sh_skin_arm, meta=meta("forearm .77x.72 -> .70x.65 -> .64x.59, closed caps"))
    return lu, ll


LUA, LLA = build_arm("Right", JV["RightShoulder"], JV["RightElbow"], JV["RightWrist"])
RUA, RLA = build_arm("Left", JV["LeftShoulder"], JV["LeftElbow"], JV["LeftWrist"])


def cutter(P, faces, tile="SKIN_SHADOW"):
    bm = solid_tiled(P, faces, tile)
    ob = bm_to_obj(bm, "tmp_cut")
    bm.free()
    return ob


def apply_cut(o, co, op):
    bool_apply(o, co, op)
    bpy.data.objects.remove(co, do_unlink=True)


def finish_hand(pm, cid, o, meta_):
    bm = obj_to_bm(o)
    bpy.data.objects.remove(o, do_unlink=True)
    tile_layer_set(bm, sh_skin_arm)
    pm.append_bm(cid, bm, None, meta_)
    bm.free()


# free right hand: centre (-2.13,-.10,1.97), W.75 D.68 H.73, inner thumb, lower notch W.14 H.19 D.18
hr = PM("RightHand", JV["RightWrist"])
c = V((-2.13, -.10, 1.97))
base = box_solid(c.x - .375, c.x + .375, c.y - .34, c.y + .34, c.z - .365, c.z + .365, "SKIN", ch=.055)
o = bm_to_obj(base, "tmp_hand")
base.free()
notch = box_solid(c.x - .07, c.x + .07, c.y - .35, c.y - .35 + .19, c.z - .375, c.z - .375 + .20, "SKIN_SHADOW")
thumb = box_solid(-1.80 - .075, -1.80 + .075, -.33 - .075, -.33 + .075, 2.03 - .15, 2.03 + .15, "SKIN", ch=.03)
for nm, bmx, op in (("notch", notch, 'DIFFERENCE'), ("thumb", thumb, 'UNION')):
    co = bm_to_obj(bmx, "tmp_" + nm)
    bmx.free()
    apply_cut(o, co, op)
finish_hand(hr, "HAND_Right", o, meta("free right hand block .75 x .68 x .73, inner thumb, lower notch .14 x .19 x .18 (boolean EXACT)"))

# left grip hand: G=(2.30,-.62,3.50), .78 x .74 x .82; hidden capsule channel following the branch divergence, rear slot W.06
hl = PM("LeftHand", JV["LeftWrist"])
G = GRIP_C
base = box_solid(G.x - .39, G.x + .39, G.y - .37, G.y + .37, G.z - .41, G.z + .41, "SKIN", ch=.055)
o = bm_to_obj(base, "tmp_hand")
base.free()
HLV = [3.04, 3.20, 3.35, 3.50, 3.65, 3.80, 3.96]
chan_rings, slot_rings = [], []
for h in HLV:
    u = branch_u(h)
    hw = u + .075 + .02
    chan_rings.append(ring8(hw, G.y - .115, G.y + .115, .035, G.x, 0, h))
    slot_rings.append([V((G.x - .03, G.y, h)), V((G.x + .03, G.y, h)), V((G.x + .03, G.y + .37 + .05, h)), V((G.x - .03, G.y + .37 + .05, h))])
for nm, rings in (("chan", chan_rings), ("slot", slot_rings)):
    n_ = len(rings[0])
    P = [p for r in rings for p in r]
    co = cutter(P, loft_faces(len(rings), n_))
    apply_cut(o, co, 'DIFFERENCE')
tb = box_solid(2.02 - .075, 2.02 + .075, -.935 - .075, -.935 + .075, 3.58 - .15, 3.58 + .15, "SKIN", ch=.035)
co = bm_to_obj(tb, "tmp_thumb")
tb.free()
apply_cut(o, co, 'UNION')
for gh in (3.29, 3.47, 3.65):
    gb = box_solid(G.x - .155, G.x + .155, G.y - .37 - .01, G.y - .37 + .008, gh - .006, gh + .006, "SKIN_SHADOW")
    co = bm_to_obj(gb, "tmp_g")
    gb.free()
    apply_cut(o, co, 'DIFFERENCE')
finish_hand(hl, "HAND_Left", o, meta("grip hand .78 x .74 x .82 at G; capsule channel (W.40 D.23, widening with the branches, clearance .02), rear slot W.06, thumb pad, 3 finger grooves (boolean EXACT)"))


def carve_forearm():
    pm = PARTS["LeftLowerArm"]
    me = bpy.data.meshes.new("tmp_fa")
    pm.bm.to_mesh(me)
    fo = bpy.data.objects.new("tmp_fa", me)
    SCENE.collection.objects.link(fo)
    P = [p for r in chan_rings for p in r]
    co = cutter(P, loft_faces(len(chan_rings), len(chan_rings[0])))
    apply_cut(fo, co, 'DIFFERENCE')
    bm2 = obj_to_bm(fo)
    bpy.data.objects.remove(fo, do_unlink=True)
    tile_layer_set(bm2, sh_skin_arm)
    pm.bm.free()
    pm.bm = bm2
    pm.tl = bm2.faces.layers.int.get("tile")


carve_forearm()
