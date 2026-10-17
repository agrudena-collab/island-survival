

# ----------------------------------------------------------------------------------------------
# Headset (one export part): cups + pads + flat cyan rings, rectangular band sweep, boom, capsule
# ----------------------------------------------------------------------------------------------
HS_O = V((0.0, 0.0, 5.45))
hs = PM("Headset", HS_O)
A10 = math.radians(10.0)


def cup_frame(s):
    n = V((s * math.cos(A10), -math.sin(A10), 0.0))
    u = V((0, 0, 1))
    w = n.cross(u).normalized()
    return n, u, w


def axial_ring(C, n, u, w, t, r, segs=20):
    return [C + n * t + (u * math.cos(2 * math.pi * k / segs) + w * math.sin(2 * math.pi * k / segs)) * r for k in range(segs)]


for s, side in ((-1, "R"), (1, "L")):
    n, u, w = cup_frame(s)
    Cc = V((s * 1.16, -0.02, 5.44))
    prof = [(-0.12, 0.495), (-0.085, 0.53), (0.085, 0.53), (0.12, 0.495), (0.12, 0.44), (0.12, 0.34)]
    rings = [axial_ring(Cc, n, u, w, t, r) for t, r in prof]
    loft(hs, "HS_cup_" + side, rings, sh_const("HEADSET"), band_tiles={0: "HEADSET_EDGE", 2: "HEADSET_EDGE", 4: "CYAN"},
         meta=meta("cylinder dia 1.06, length .24 along n=(%+.4f,%.4f,0) (10 deg forward), 20 sides, edge bevel .035 (HEADSET_EDGE); flat CYAN ring r .34..44 on the outer end" % (s * math.cos(A10), -math.sin(A10))))
    n_cy = sum(1 for f in hs.faces_of("HS_cup_" + side) if f[hs.tl] == TILE["CYAN"])
    COMP_LOG.append({"id": "HS_cyan_" + side, "owner": "Headset", "kind": "paint", "recipe": "flat annular CYAN colour region r .34..44 on the outer cup end (no torus, no emission)", "faces": n_cy, "tris": 0, "class": "prescribed"})
    Cp = Cc - n * 0.19
    rings = [axial_ring(Cp, n, u, w, -0.07, 0.51), axial_ring(Cp, n, u, w, 0.07, 0.51)]
    loft(hs, "HS_pad_" + side, rings, sh_const("HEADSET_PAD"), meta=meta("soft pad dia 1.02, length .14 along n, centre Ccup-.19n, HEADSET_PAD"))

# band: closed rectangular sweep P(t) = (1.11 sin t, .12, 5.45 + .90 cos t), t -80..+80 deg, 12 segments, width .26 (D), radial thickness .10
sections = []
for k in range(13):
    t = math.radians(-80.0 + 160.0 * k / 12.0)
    P0 = V((1.11 * math.sin(t), 0.12, 5.45 + 0.90 * math.cos(t)))
    nr = V((0.90 * math.sin(t), 0.0, 1.11 * math.cos(t))).normalized()
    dv = V((0, 1, 0))
    sections.append([P0 - nr * 0.05 - dv * 0.13, P0 + nr * 0.05 - dv * 0.13, P0 + nr * 0.05 + dv * 0.13, P0 - nr * 0.05 + dv * 0.13])
loft(hs, "HS_band", sections, sh_const("HEADSET"), meta=meta("single swept rectangular band, 12 segments, width .26, radial thickness .10, top H6.40"))

# boom: 6-sided tube r .035 along the 4-point polyline, corners softened by .04
BOOM = [V(p) for p in ((1.18, -0.08, 5.30), (1.12, -0.61, 4.98), (0.88, -1.06, 4.82), (0.67, -1.12, 4.81))]
poly = [BOOM[0]]
for i in range(1, len(BOOM) - 1):
    d0 = (BOOM[i] - BOOM[i - 1]).normalized()
    d1 = (BOOM[i + 1] - BOOM[i]).normalized()
    poly += [BOOM[i] - d0 * 0.04, BOOM[i] + d1 * 0.04]
poly.append(BOOM[-1])
rings = []
prev_u = None
for i, p in enumerate(poly):
    if i == 0:
        T = (poly[1] - poly[0]).normalized()
    elif i == len(poly) - 1:
        T = (poly[-1] - poly[-2]).normalized()
    else:
        T = ((poly[i] - poly[i - 1]).normalized() + (poly[i + 1] - poly[i]).normalized()).normalized()
    if prev_u is None:
        prev_u = (V((0, 0, 1)) - T * V((0, 0, 1)).dot(T)).normalized()
    uu = (prev_u - T * prev_u.dot(T)).normalized()
    vv = T.cross(uu)
    prev_u = uu
    rings.append([p + (uu * math.cos(2 * math.pi * k / 6) + vv * math.sin(2 * math.pi * k / 6)) * 0.035 for k in range(6)])
loft(hs, "HS_boom", rings, sh_const("HEADSET"), meta=meta("one simple 6-sided tube r .035 along the 4-point polyline, corners cut by .04", points=[tuple(p) for p in BOOM]))
loft(hs, "HS_mic", cbox((0.58, -1.12, 4.81), (0.25, 0.14, 0.15), 0.05), sh_const("HEADSET_PAD"), meta=meta("mic capsule .25 x .14 x .15, bevel .05"))

# ----------------------------------------------------------------------------------------------
# EnergyCan: one closed lathe (20 segments, phi=0 towards -D), blue band wraps the atlas can map, recessed top cap carries the pull tab
# ----------------------------------------------------------------------------------------------
cn = PM("EnergyCan", CAN_C)
CAN_PROF = [(-0.72, 0.255), (-0.70, 0.29), (-0.66, 0.31), (-0.61, 0.31), (0.54, 0.31), (0.62, 0.28), (0.67, 0.25), (0.70, 0.265), (0.72, 0.265), (0.72, 0.245), (0.695, 0.245)]
rings = []
for z, r in CAN_PROF:
    rings.append([V((CAN_C.x + r * math.sin(2 * math.pi * k / 20), CAN_C.y - r * math.cos(2 * math.pi * k / 20), CAN_C.z + z)) for k in range(20)])
loft(cn, "CAN_body", rings, sh_const("SILVER"),
     band_tiles={2: "CAN_DARK", 3: "CAN_BLUE", 4: "CAN_LIGHT", 5: "CAN_LIGHT", 8: "SILVER_LIGHT"},
     meta=meta("closed lathe, 11 profile rings x 20 segments (phi=0 towards -D), blue band z-.61..+.54, CAN_LIGHT shoulder, CAN_DARK thin lower zone, SILVER rims", profile=CAN_PROF))
ci_body = cn.comp_index("CAN_body")
# blue band: wrap map; recessed top cap: can-top map
zc = lambda f: f.calc_center_median().z - CAN_C.z
n_wrap = cn.set_map("CAN_body", UVM_CANWRAP, lambda f: -0.611 < zc(f) < 0.541 and abs(f.normal.z) < 0.3, tile="CAN_BLUE")
n_top = cn.set_map("CAN_body", UVM_CANTOP, lambda f: abs(zc(f) - 0.695) < 1e-4 and f.normal.z > 0.9 and len(f.verts) >= 12, tile="SILVER")
COMP_LOG[ci_body]["wrap_faces"], COMP_LOG[ci_body]["top_faces"] = n_wrap, n_top
COMP_LOG.append({"id": "CAN_top", "owner": "EnergyCan", "kind": "texture", "recipe": "recessed top cap z+.695 (dia .49) with the printed pull tab, atlas can-top rect 256,256-512,512", "faces": n_top, "tris": 0, "class": "prescribed"})
COMP_LOG.append({"id": "CAN_bottom", "owner": "EnergyCan", "kind": "mesh", "recipe": "closed bottom end (existing cap face, dia .51), SILVER", "faces": 1, "tris": 18, "class": "prescribed"})
COMP_LOG.append({"id": "CAN_lightning", "owner": "EnergyCan", "kind": "texture", "recipe": "white lightning printed on the blue band: px = 768+512*theta/2pi, py = 512(.54-z)/1.15, theta = angle from -D", "faces": n_wrap, "tris": 0, "class": "prescribed"})
