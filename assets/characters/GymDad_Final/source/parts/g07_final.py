

# ----------------------------------------------------------------------------------------------
# atlas / material / mesh objects
# ----------------------------------------------------------------------------------------------
os.makedirs(os.path.join(OUT, "textures"), exist_ok=True)
atlas = bpy.data.images.new("GymDad_Atlas", ATLAS_W, ATLAS_H, alpha=False)
atlas.colorspace_settings.name = 'sRGB'
px = [0.0] * (ATLAS_W * ATLAS_H * 4)
fill = hex_rgb(HEXOF["Tank"])
for ty in range(ATLAS_H):
    for tx in range(ATLAS_W):
        idx = (ty // TILE_PX) * COLS + (tx // TILE_PX)
        rgb = hex_rgb(PAL[idx][1]) if idx < len(PAL) else fill
        r, g, b = (c / 255.0 for c in rgb)
        o = ((ATLAS_H - 1 - ty) * ATLAS_W + tx) * 4
        px[o:o + 4] = [r, g, b, 1.0]
atlas.pixels.foreach_set(px)
ATLAS_PATH = os.path.join(OUT, "textures", "GymDad_Atlas.png")
atlas.filepath_raw = ATLAS_PATH
atlas.file_format = 'PNG'
atlas.save()
atlas.pack()

MATP = bpy.data.materials.new("GymDad_Atlas")
MATP.use_nodes = True
nt = MATP.node_tree
bs = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = atlas
tex.interpolation = 'Closest'
nt.links.new(tex.outputs["Color"], bs.inputs["Base Color"])
bs.inputs["Roughness"].default_value = 0.8
try:
    bs.inputs["Specular IOR Level"].default_value = 0.05
except KeyError:
    pass

for pm in PARTS.values():
    bm = pm.bm
    bm.normal_update()
    me = bpy.data.meshes.new(pm.geo)
    bm.to_mesh(me)
    uv = me.uv_layers.new(name="UVMap")
    ca = me.color_attributes.new("Col", 'BYTE_COLOR', 'CORNER')
    attr = me.attributes.get("tile")
    for pi, poly in enumerate(me.polygons):
        t = attr.data[pi].value if attr else 0
        u0, v0, u1, v1 = tile_uv_patch(t)
        corners = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
        r_, g_, b_ = hex_rgb(PAL[t][1])
        for k, li in enumerate(poly.loop_indices):
            uv.data[li].uv = corners[k % 4]
            try:
                ca.data[li].color_srgb = (r_ / 255.0, g_ / 255.0, b_ / 255.0, 1.0)
            except AttributeError:
                ca.data[li].color = (srgb_to_lin(r_), srgb_to_lin(g_), srgb_to_lin(b_), 1.0)
    me.materials.append(MATP)
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new(pm.geo, me)
    EXP_COLL.objects.link(ob)
    off = pm.joint.copy()
    for v in me.vertices:
        v.co -= off
    ob.location = off
    pm.obj = ob
    pm.bm.free()

# ----------------------------------------------------------------------------------------------
# armature (R15 hierarchy, identical to the Regular/Office builders) + rigid 100% weights; pose = rest pose (HoldWeights)
# ----------------------------------------------------------------------------------------------
arm_data = bpy.data.armatures.new("GymDad_Armature")
ARM_OB = bpy.data.objects.new("GymDad_Armature", arm_data)
EXP_COLL.objects.link(ARM_OB)
bpy.context.view_layer.objects.active = ARM_OB
ARM_OB.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones
BONES = [
    ("Root", None, V((0, 0, 0)), V((0, 0, 1.0))),
    ("HumanoidRootNode", "Root", JV["Root"], JV["Root"] + V((0, 0, .5))),
    ("LowerTorso", "HumanoidRootNode", JV["Root"], JV["Waist"]),
    ("UpperTorso", "LowerTorso", JV["Waist"], JV["Neck"]),
    ("Head", "UpperTorso", JV["Neck"], V((0, 0, 6.40))),
]
for side in ("Right", "Left"):
    ank = JV[side + "Ankle"]
    BONES += [
        (side + "UpperArm", "UpperTorso", JV[side + "Shoulder"], JV[side + "Elbow"]),
        (side + "LowerArm", side + "UpperArm", JV[side + "Elbow"], JV[side + "Wrist"]),
        (side + "Hand", side + "LowerArm", JV[side + "Wrist"], JV[side + "Wrist"] + V((0, 0, -.68))),
        (side + "UpperLeg", "LowerTorso", JV[side + "Hip"], JV[side + "Knee"]),
        (side + "LowerLeg", side + "UpperLeg", JV[side + "Knee"], JV[side + "Ankle"]),
        (side + "Foot", side + "LowerLeg", JV[side + "Ankle"], V((ank.x, ank.y - .78, .12))),
    ]
for name, parent, head, tail in BONES:
    b = eb.new(name)
    b.head, b.tail = head, tail
    b.use_connect = False
for name, parent, head, tail in BONES:
    if parent:
        eb[name].parent = eb[parent]
bpy.ops.object.mode_set(mode='OBJECT')
PROPS = ("Dumbbell", "GymBag")
for pm in PARTS.values():
    bone = {"Dumbbell": "RightHand", "GymBag": "LeftHand"}.get(pm.runtime, pm.runtime)
    ob = pm.obj
    vg = ob.vertex_groups.new(name=bone)
    vg.add([v.index for v in ob.data.vertices], 1.0, 'REPLACE')
    md = ob.modifiers.new("Armature", 'ARMATURE')
    md.object = ARM_OB
    ob.parent = ARM_OB
    ob.matrix_parent_inverse = Matrix.Identity(4)
PB = ARM_OB.pose.bones
for pb in PB:
    pb.rotation_mode = 'QUATERNION'
    pb.rotation_quaternion = Quaternion((1, 0, 0, 0))
    pb.location = V((0, 0, 0))
    pb.scale = V((1, 1, 1))
bpy.context.view_layer.update()
POSE_IDENTITY = all(pb.rotation_quaternion.angle < 1e-9 and pb.location.length < 1e-9 for pb in PB)

# ----------------------------------------------------------------------------------------------
# audits
# ----------------------------------------------------------------------------------------------
from collections import Counter


def world_bounds(obs):
    lo = V((1e9, 1e9, 1e9))
    hi = V((-1e9, -1e9, -1e9))
    dg = bpy.context.evaluated_depsgraph_get()
    for o in obs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = ev.matrix_world
        for v in me.vertices:
            w = mw @ v.co
            lo = V((min(lo.x, w.x), min(lo.y, w.y), min(lo.z, w.z)))
            hi = V((max(hi.x, w.x), max(hi.y, w.y), max(hi.z, w.z)))
        ev.to_mesh_clear()
    return lo, hi


def world_verts(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ev.matrix_world
    out = [mw @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    return out


def bvh_of(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    bmx = bmesh.new()
    bmx.from_mesh(me)
    bmx.transform(ev.matrix_world)
    ev.to_mesh_clear()
    bmesh.ops.triangulate(bmx, faces=bmx.faces)
    t = BVHTree.FromBMesh(bmx)
    pts = [v.co.copy() for v in bmx.verts]
    bmx.free()
    return t, pts


BODY = [PARTS[k].obj for k in PARTS if k not in PROPS]
PROP_OB = {k: PARTS[k].obj for k in PROPS}
lo, hi = world_bounds(BODY)
head_lo, head_hi = world_bounds([PARTS["Head"].obj])
ft_lo, _ = world_bounds([PARTS["RightFoot"].obj, PARTS["LeftFoot"].obj])
bounds_all = {k: [[round(c, 4) for c in a] for a in world_bounds([PARTS[k].obj])] for k in PARTS}
body_tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in BODY)
prop_tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in PROP_OB.items()}
print("BOUNDS body", tuple(round(x, 3) for x in lo), tuple(round(x, 3) for x in hi))
print("HEAD", tuple(round(x, 3) for x in head_lo), tuple(round(x, 3) for x in head_hi), "FEET", round(ft_lo.z, 4))
print("TRIS body", body_tris, "props", prop_tris)

AUDIT = {}
for pm in PARTS.values():
    me = pm.obj.data
    bmx = bmesh.new()
    bmx.from_mesh(me)
    bmesh.ops.remove_doubles(bmx, verts=bmx.verts, dist=1e-5)
    cnt = Counter()
    for f in bmx.faces:
        vs = [v.index for v in f.verts]
        for a, b in zip(vs, vs[1:] + vs[:1]):
            cnt[(min(a, b), max(a, b))] += 1
    vol = 0.0
    for f in bmx.faces:
        vv = [v.co for v in f.verts]
        for k in range(1, len(vv) - 1):
            vol += vv[0].dot(vv[k].cross(vv[k + 1])) / 6.0
    uvs = [tuple(l.uv) for l in me.uv_layers.active.data]
    AUDIT[pm.runtime] = {"verts": len(me.vertices), "tris": sum(len(p.vertices) - 2 for p in me.polygons),
                         "open_edges": sum(1 for v in cnt.values() if v == 1), "nonmanifold_edges": sum(1 for v in cnt.values() if v > 2),
                         "zero_area": sum(1 for f in bmx.faces if f.calc_area() < 1e-9), "signed_volume": round(vol, 4),
                         "uv_in_range": all(0 <= u <= 1 and 0 <= v <= 1 for u, v in uvs), "components": len(pm.comps)}
    bmx.free()


def mirror_dev(a, b):
    """max distance of the mirrored (x -> -x) vertices of a from the surface of b."""
    t, _ = bvh_of(b)
    return max((t.find_nearest(V((-p.x, p.y, p.z)))[3] or 0.0) for p in world_verts(a))


SYM = {"UpperLeg_mirror_dev": round(mirror_dev(PARTS["RightUpperLeg"].obj, PARTS["LeftUpperLeg"].obj), 6),
       "LowerLeg_mirror_dev": round(mirror_dev(PARTS["RightLowerLeg"].obj, PARTS["LeftLowerLeg"].obj), 6),
       "Foot_mirror_dev": round(mirror_dev(PARTS["RightFoot"].obj, PARTS["LeftFoot"].obj), 6)}
lens = {}
for side in ("Right", "Left"):
    lens[side] = {"shoulder_elbow": round((JV[side + "Elbow"] - JV[side + "Shoulder"]).length, 6), "elbow_wrist": round((JV[side + "Wrist"] - JV[side + "Elbow"]).length, 6)}
head_c = (head_lo + head_hi) / 2
pel_lo, pel_hi = world_bounds([PARTS["LowerTorso"].obj])
AXES = {"head_centre_x": round(head_c.x, 5), "pelvis_centre_x": round((pel_lo.x + pel_hi.x) / 2, 5)}

# interpenetration / clearance (BVH on the evaluated meshes); contacts listed as hidden-allowed are reported separately
ALLOWED = {"Dumbbell": {"RightHand": "grip passes through the closed palm (hidden, allowed)"},
           "GymBag": {"LeftHand": "handle tops run inside the fist (hidden, allowed)"}}
CLEAR = {}
for prop, others in (("Dumbbell", ("UpperTorso", "RightLowerArm", "RightUpperArm", "RightHand", "LowerTorso", "RightUpperLeg", "LeftHand")),
                     ("GymBag", ("LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "LeftHand", "LeftLowerArm", "LowerTorso", "RightFoot", "LeftUpperArm"))):
    pt, ppts = bvh_of(PROP_OB[prop])
    CLEAR[prop] = {}
    for n in others:
        t, pts = bvh_of(PARTS[n].obj)
        md = min((t.find_nearest(p)[3] or 9e9) for p in ppts)
        mdr = min((pt.find_nearest(p)[3] or 9e9) for p in pts)
        CLEAR[prop][n] = {"overlapping_triangle_pairs": len(pt.overlap(t)), "min_vertex_distance": round(min(md, mdr), 4),
                          "allowed_hidden_contact": ALLOWED.get(prop, {}).get(n)}
print("CLEARANCE", json.dumps(CLEAR))
# shoe vs shin, hand vs forearm sanity
JOINT_GAPS = {}
for side in ("Right", "Left"):
    for a, b, j in (("UpperArm", "LowerArm", "Elbow"), ("LowerArm", "Hand", "Wrist"), ("UpperLeg", "LowerLeg", "Knee"), ("LowerLeg", "Foot", "Ankle")):
        ta, _ = bvh_of(PARTS[side + a].obj)
        tb, pb_ = bvh_of(PARTS[side + b].obj)
        JOINT_GAPS[side + j] = {"overlap_pairs": len(ta.overlap(tb)), "joint_to_surface_a": round((ta.find_nearest(JV[side + j])[3] or 0), 5), "joint_to_surface_b": round((tb.find_nearest(JV[side + j])[3] or 0), 5)}

# ----------------------------------------------------------------------------------------------
# outputs: blend, FBX, data JSON
# ----------------------------------------------------------------------------------------------
os.makedirs(os.path.join(OUT, "export"), exist_ok=True)
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
os.makedirs(os.path.join(OUT, "source"), exist_ok=True)
BLEND = os.path.join(OUT, "source", "GymDad_Review_V2.blend")
FBX_BODY = os.path.join(OUT, "export", "GymDad_V2_Body.fbx")
FBX_PROPS = os.path.join(OUT, "export", "GymDad_V2_Props.fbx")
FBX_SET = dict(use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y',
               mesh_smooth_type='FACE', use_mesh_modifiers=True, bake_anim=False, add_leaf_bones=False,
               path_mode='COPY', embed_textures=True, use_armature_deform_only=False, primary_bone_axis='Y', secondary_bone_axis='X')


def export_fbx(path, objs, types):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, object_types=types, **FBX_SET)


export_fbx(FBX_BODY, [ARM_OB] + BODY, {'MESH', 'ARMATURE'})
copies = []
for k, o in PROP_OB.items():
    cp = bpy.data.objects.new(o.name, o.data.copy())
    cp.data.name = o.data.name + "_export"
    EXP_COLL.objects.link(cp)
    cp.location = PARTS[k].joint
    copies.append(cp)
export_fbx(FBX_PROPS, copies, {'MESH'})
for cp in copies:
    bpy.data.objects.remove(cp, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("EXPORTED", FBX_BODY, FBX_PROPS, BLEND)

uvmap = {"atlas": "GymDad_Atlas.png", "size": [ATLAS_W, ATLAS_H], "tile_px": TILE_PX, "columns": COLS, "inset_px": INSET, "row0_is_top_of_png": True, "tiles": []}
for i, (n_, h_, use) in enumerate(PAL):
    u0, v0, u1, v1 = tile_uv_patch(i)
    uvmap["tiles"].append({"index": i, "name": n_, "hex": h_, "col": i % COLS, "row": i // COLS, "uv_patch": [u0, v0, u1, v1]})
json.dump(uvmap, open(os.path.join(OUT, "data", "palette_uv_map.json"), "w"), indent=1)


def r3(v, nd=4):
    return [round(float(c), nd) for c in v]


def roblox_pos(p):
    return [round(-p[0], 4), round(p[2], 4), round(p[1], 4)]


def logical(p):
    return [round(float(p[0]), 4), round(float(-p[1]), 4), round(float(p[2]), 4)]


RESULT = {"bounds_body": {"min": r3(lo), "max": r3(hi), "height": round(hi.z - lo.z, 4)}, "head_bounds": {"min": r3(head_lo), "max": r3(head_hi)},
          "feet_min_h": round(ft_lo.z, 5), "tris_body": body_tris, "tris_props": prop_tris, "tris_total": body_tris + sum(prop_tris.values()),
          "per_part_bounds_blender": bounds_all, "audit": AUDIT, "symmetry": SYM, "arm_lengths": lens, "axes": AXES, "clearance": CLEAR,
          "joint_overlaps": JOINT_GAPS, "pose_bones_identity": POSE_IDENTITY, "meshes": len(PARTS)}
json.dump(RESULT, open(os.path.join(OUT, "data", "actual_mesh_statistics.json"), "w"), indent=1)
CENTRES = {}
BBOXES = {}
for k in PARTS:
    a_, b_ = world_bounds([PARTS[k].obj])
    CENTRES[k] = [round(float((a_[i] + b_[i]) / 2), 6) for i in range(3)]
    BBOXES[k] = {"size": [round(float(b_[i] - a_[i]), 7) for i in range(3)], "centre": [round(float((a_[i] + b_[i]) / 2), 7) for i in range(3)]}
json.dump(BBOXES, open(os.path.join(OUT, "data", "part_bboxes_blender.json"), "w"), indent=1)
JOINTS_BL = {k: [round(float(v[0]), 6), round(float(v[1]), 6), round(float(v[2]), 6)] for k, v in JV.items()}
def _r(v):
    return [round(float(c), 3) for c in v]


DEVIATIONS = [
    {"id": "V01", "what": "coordinate basis", "plan": "Roblox (x,y,z) = (X, H, -F), X positive = anatomical left", "v2": "Blender (x,y,z) = (X,-F,H) with X<0 = anatomical RIGHT; FBX axis_forward Z / axis_up Y gives Roblox (-X, H, -F): character faces -Z, anatomical right = +X (contract of Regular/Office Dad)",
     "reason": "the plan's literal Roblox formula would put the dumbbell hand on the character's left; verified on 3 basis vectors and both fists in data/basis_check.json"},
    {"id": "V02", "what": "arm lengths and shoulder girdle", "plan": "shoulder (+-1.62, 0, 4.62), L1/L2 = 1.30/1.20", "v2": "shoulders R %s / L %s, L1/L2 = %.2f/%.2f for BOTH arms; elbows by the plan's IK formula: R %s (hint %s), L %s (hint %s)" % (_r(JOINTS["RightShoulder"]), _r(JOINTS["LeftShoulder"]), L1, L2, _r(JOINTS["RightElbow"]), RHINT, _r(JOINTS["LeftElbow"]), LHINT),
     "reason": "the original has wide, low shoulder masses and the left arm hangs along the body; the old shoulder line (4.62) and lengths could not give that silhouette"},
    {"id": "V03", "what": "head", "plan": "skull W2.00 D1.49 H1.42, top 6.40", "v2": "all head components scaled about the top of the skull: width/depth x%.2f, height x%.2f (skull W1.68, beard bottom H%.2f)" % (HS, HZ, 6.40 - (6.40 - 4.76) * HZ), "reason": "head/shoulder-girdle ratio .553 (baseline) vs .343 (original)"},
    {"id": "V04", "what": "torso", "plan": "rows H2.30..4.78, top W2.74", "v2": "8 rows H2.30..5.15 (top W2.74, mid-chest W3.14, belly Ffront 1.00), neckline half width .90 (plan .80) and edge band; back scoop to H4.72", "reason": "short neck and shoulder line at the chin level as on the original"},
    {"id": "V05", "what": "arm sections", "plan": "upper 1.08/1.03 -> .91/.88, forearm .91/.88 -> .70/.68, chamfer .11", "v2": "upper %s, forearm %s, chamfer .17" % (UPPER_SEC, LOWER_SEC), "reason": "original arms are about 1.4x thicker; the forearm end is .84 x .74 so that it clears the outer plate pack"},
    {"id": "V06", "what": "fists", "plan": "right .73/.80/.72, left .73/.72/.71", "v2": "right .78/.98/.98 at %s, left .76/.96/.96 at %s, bevel .13/.14, integrated thumb blocks" % (_r(FIST_R), _r(FIST_L)), "reason": "heavy fists, fist/forearm width ratio .92 (original .93)"},
    {"id": "V07", "what": "legs and stance", "plan": "hips +-.73, knees +-.81, ankles +-.88, shorts leg W1.22", "v2": "hips +-.90, knees +-.98, ankles +-1.04, shorts leg W1.42..1.52 (centres +-.90), pelvis W3.00", "reason": "wide stance and loose shorts of the original (shorts wider than the tank hem)"},
    {"id": "V08", "what": "face", "plan": "rectangular eye whites, flat patches, lip plate, support block", "v2": "oval eyes .41 x .22 (tilted), round iris d.16, pupil d.10, one glint, brows covering the upper lid, nose front F1.14 (0.38 proud), moustache F1.03, curved smile (teeth band + compact crescent), no lip plate / support block", "reason": "points 05.1-05.3 of the V2 order"},
    {"id": "V09", "what": "beard", "plan": "U contour extruded to F.97/1.09", "v2": "6 jaw sections (chin F1.12, cheeks F1.07, back F-.28..+.05) with a cut face window; sideburns end at the ear", "reason": "point 05.4: full beard around the jaw, no frame, no long flat back wall"},
    {"id": "V10", "what": "neck", "plan": "neck .90 x .80 x .46", "v2": "block .86 x .70 x .50 inside the scaled skull / torso / beard (shoulder line at H5.15)", "reason": "short wide neck, no separate block in profile"},
    {"id": "V11", "what": "tank edge", "plan": "armhole rim ribbon, straps as shell remainder", "v2": "no rim ribbon (it showed as a thin loop); neckline walls are a tank-edge band; straps = shell between neckline (.90) and arm, width ~.47, continuous front-to-back", "reason": "point 06: no sharp flaps / thin torn edges"},
    {"id": "V12", "what": "dumbbell", "plan": "r.76/.68/.55, t.27/.22/.18, centre (-1.72,1.78,3.31), axis L2.50", "v2": "r.98/.88/.72, t.34/.28/.24 contiguous (no gaps/washers), grip half %.2f, centre %s; length %.2f, pack thickness/diameter %.2f (abs. thickness .77 -> .98)" % (GRIP_HALF, _r(GRIP_R), 2 * GRIP_HALF + 2 * (.06 + sum(t for t, _ in PLATES) + .06 + .03), (.06 + sum(t for t, _ in PLATES) + .06) / (2 * PLATES[0][1])), "reason": "point 07; the grip gap must exceed the forearm width"},
    {"id": "V13", "what": "bag", "plan": "box 1.32 x 1.02 x 1.24 with flat orange panels, black frame, centre band, end plates", "v2": "soft duffel, 5 rounded sections H.28..1.34, W1.64 max, D1.04 max, orange ends / dark middle, no panels, no frame, no centre band; handles with F converging into the fist", "reason": "point 08 (also removes the coplanar-panel ripple)"},
    {"id": "V14", "what": "shoes", "plan": "flat sole+upper, white bumper step, heel loop behind the shin", "v2": "sole W1.40 x D2.00 x H.34 (bevel .10), upper lofted along F (collar H.86 -> toe), ONE white toe cap, tongue wedge + 2 lace bands on the instep, orange loop on top of the tongue, orange side accent, one rotation (7 deg) about the ankle for the whole set", "reason": "point 09"},
    {"id": "V15", "what": "face materials", "plan": "per-type roughness, baked eyes", "v2": "unchanged from Review: one atlas material (roughness .8), face details are flat geometry", "reason": "Studio gets the atlas as ColorMap"},
]
json.dump(DEVIATIONS, open(os.path.join(OUT, "data", "deviations_from_prompt.json"), "w"), indent=1)
json.dump({"asset": "GymDad_Review", "units": "studs", "height_target": 6.40, "height_built": RESULT["bounds_body"]["height"], "joints_blender": JOINTS_BL, "part_bbox_centres_blender": CENTRES,
           "tables": {"torso_rows_D": TORSO, "skull_rows": SKULL, "nose_rows": NOSE}, "right_bend_hint": list(RHINT), "left_bend_hint": list(LHINT), "L1_L2": [L1, L2], "head_scale": HS,
           "elbow_contours": {k: [list(map(float, p)) for p in v] for k, v in ELBOW_RING.items()}, "palette": [{"index": i, "name": n_, "hex": h_} for i, (n_, h_, _) in enumerate(PAL)],
           "counts": {"body_tris": body_tris, "prop_tris": prop_tris}, "measured": RESULT, "deviations_from_prompt": DEVIATIONS},
          open(os.path.join(OUT, "data", "construction_spec_actual.json"), "w"), indent=1)
json.dump({"pose": "HoldWeights (rest pose == pose)", "joints_logical_XFH": {k: list(v) for k, v in JOINTS.items()}, "joints_blender": JOINTS_BL,
           "grips": {"DumbbellGrip": {"from": "RightHand", "to": "Dumbbell", "centre_logical_XFH": list(GRIP_R), "axis": "X"},
                     "BagGrip": {"from": "LeftHand", "to": "GymBag", "point_logical_XFH": [FIST_L[0], FIST_L[1], 2.0]}},
           "wrist_vs_hand_centre": {"RightWrist": list(JOINTS["RightWrist"]), "RightHandCentre": list(FIST_R), "LeftWrist": list(JOINTS["LeftWrist"]), "LeftHandCentre": list(FIST_L)}},
          open(os.path.join(OUT, "data", "joints_pose_grips.json"), "w"), indent=1)
json.dump({"asset": "GymDad_Review", "components": COMP_LOG,
           "part_totals": {k: {"components": len(v.comps), "tris": AUDIT[k]["tris"], "verts": AUDIT[k]["verts"]} for k, v in PARTS.items()},
           "mesh_names": {k: v.geo for k, v in PARTS.items()}}, open(os.path.join(OUT, "data", "component_registry.json"), "w"), indent=1)
RIG = {"asset": "GymDad_Review", "frame": {"logical": "(X,F,H) anatomical RIGHT = -X, forward = +F", "blender": "(X,-F,H)", "roblox_position": "(-X, H, -F)"},
       "bones": [{"name": n, "parent": p, "head_logical": logical(h), "tail_logical": logical(t), "head_roblox": roblox_pos(h)} for n, p, h, t in BONES],
       "joints_logical": {k: list(v) for k, v in JOINTS.items()},
       "grips": {"DumbbellGrip": {"joint": "RightHand -> Dumbbell", "centre_logical": list(GRIP_R), "axis": "X"}, "BagGrip": {"joint": "LeftHand -> GymBag", "point_logical": [FIST_L[0], FIST_L[1], 2.0]}},
       "weights": "100% own bone (rigid); Dumbbell -> RightHand, GymBag -> LeftHand (props exported as separate meshes without armature)",
       "part_origin_logical": {k: logical(v.joint) for k, v in PARTS.items()}, "part_bbox_centres_blender": CENTRES, "joints_blender": JOINTS_BL, "pose": "HoldWeights == rest pose (built directly, pose bones identity)"}
json.dump(RIG, open(os.path.join(OUT, "data", "rig_manifest.json"), "w"), indent=1)
print("RESULT", json.dumps({k: RESULT[k] for k in ("bounds_body", "tris_body", "tris_props", "symmetry", "arm_lengths", "axes", "pose_bones_identity")}))
