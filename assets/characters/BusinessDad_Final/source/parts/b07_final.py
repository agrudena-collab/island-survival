

# ----------------------------------------------------------------------------------------------
# atlas / material / mesh objects
# ----------------------------------------------------------------------------------------------
os.makedirs(os.path.join(OUT, "textures"), exist_ok=True)
atlas = bpy.data.images.new("BusinessDad_Atlas", ATLAS_W, ATLAS_H, alpha=False)
atlas.colorspace_settings.name = 'sRGB'
px = [0.0] * (ATLAS_W * ATLAS_H * 4)
fill = hex_rgb(HEXOF["Navy"])
for ty in range(ATLAS_H):
    for tx in range(ATLAS_W):
        idx = (ty // TILE_PX) * COLS + (tx // TILE_PX)
        rgb = hex_rgb(PAL[idx][1]) if idx < len(PAL) else fill
        r, g, b = (c / 255.0 for c in rgb)
        o = ((ATLAS_H - 1 - ty) * ATLAS_W + tx) * 4
        px[o:o + 4] = [r, g, b, 1.0]
atlas.pixels.foreach_set(px)
ATLAS_PATH = os.path.join(OUT, "textures", "BusinessDad_Atlas.png")
atlas.filepath_raw = ATLAS_PATH
atlas.file_format = 'PNG'
atlas.save()
atlas.pack()

MATP = bpy.data.materials.new("BusinessDad_Atlas")
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
arm_data = bpy.data.armatures.new("BusinessDad_Armature")
ARM_OB = bpy.data.objects.new("BusinessDad_Armature", arm_data)
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
        (side + "Hand", side + "LowerArm", JV[side + "Wrist"], HAND_AX[side].P1),
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
PROPS = ("Phone",)
for pm in PARTS.values():
    bone = {"Phone": "LeftHand"}.get(pm.runtime, pm.runtime)
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
ALLOWED = {"Phone": {"LeftHand": "lower phone edge sits inside the closed fist (hidden, allowed)"}}
CLEAR = {}
for prop, others in (("Phone", ("UpperTorso", "Head", "LeftLowerArm", "LeftUpperArm", "LeftHand", "RightHand", "LowerTorso")),):
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
BLEND = os.path.join(OUT, "source", "BusinessDad_Review.blend")
FBX_BODY = os.path.join(OUT, "export", "BusinessDad_Body.fbx")
FBX_PROPS = os.path.join(OUT, "export", "BusinessDad_Props.fbx")
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

uvmap = {"atlas": "BusinessDad_Atlas.png", "size": [ATLAS_W, ATLAS_H], "tile_px": TILE_PX, "columns": COLS, "inset_px": INSET, "row0_is_top_of_png": True, "tiles": []}
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
json.dump({"asset": "BusinessDad_Review", "units": "studs", "height_target": 6.40, "height_built": RESULT["bounds_body"]["height"], "joints_blender": JOINTS_BL, "part_bbox_centres_blender": CENTRES,
           "tables": {"torso_rows_D": TORSO, "skull_rows": SKULL, "nose_rows": NOSE, "hair_cap_rows": HC}, "right_bend_hint": list(RHINT), "left_bend_hint": list(LHINT), "L1_L2": [L1, L2],
           "elbow_contours": {k: [list(map(float, p)) for p in v] for k, v in ELBOW_RING.items()}, "palette": [{"index": i, "name": n_, "hex": h_} for i, (n_, h_, _) in enumerate(PAL)],
           "counts": {"body_tris": body_tris, "prop_tris": prop_tris}, "measured": RESULT},
          open(os.path.join(OUT, "data", "construction_spec_actual.json"), "w"), indent=1)
json.dump({"pose": "static pocket/phone pose (rest pose == pose)", "joints_logical_XFH": {k: list(v) for k, v in JOINTS.items()}, "joints_blender": JOINTS_BL,
           "grips": {"PhoneGrip": {"from": "LeftHand", "to": "Phone", "centre_logical_XFH": list(PHONE_LOGICAL), "yaw_deg": PHONE_YAW, "roll_deg": PHONE_ROLL}},
           "right_hand": "RightHand is built along the forearm direction and rests at the trouser pocket (part of the RightHand mesh, no prop)",
           "watch": "gold watch baked into the LeftHand mesh (bracelet + bezel + dial), cannot detach"},
          open(os.path.join(OUT, "data", "joints_pose_grips.json"), "w"), indent=1)
json.dump({"asset": "BusinessDad_Review", "components": COMP_LOG,
           "part_totals": {k: {"components": len(v.comps), "tris": AUDIT[k]["tris"], "verts": AUDIT[k]["verts"]} for k, v in PARTS.items()},
           "mesh_names": {k: v.geo for k, v in PARTS.items()}}, open(os.path.join(OUT, "data", "component_registry.json"), "w"), indent=1)
RIG = {"asset": "BusinessDad_Review", "frame": {"logical": "(X,F,H) anatomical RIGHT = -X, forward = +F", "blender": "(X,-F,H)", "roblox_position": "(-X, H, -F)"},
       "bones": [{"name": n, "parent": p, "head_logical": logical(h), "tail_logical": logical(t), "head_roblox": roblox_pos(h)} for n, p, h, t in BONES],
       "joints_logical": {k: list(v) for k, v in JOINTS.items()},
       "grips": {"PhoneGrip": {"joint": "LeftHand -> Phone", "centre_logical": list(PHONE_LOGICAL)}},
       "weights": "100% own bone (rigid); Phone -> LeftHand (prop exported as a separate mesh without armature)",
       "part_origin_logical": {k: logical(v.joint) for k, v in PARTS.items()}, "part_bbox_centres_blender": CENTRES, "joints_blender": JOINTS_BL, "pose": "static pose built directly (pose bones identity)"}
json.dump(RIG, open(os.path.join(OUT, "data", "rig_manifest.json"), "w"), indent=1)
print("RESULT", json.dumps({k: RESULT[k] for k in ("bounds_body", "tris_body", "tris_props", "symmetry", "arm_lengths", "axes", "pose_bones_identity")}))
