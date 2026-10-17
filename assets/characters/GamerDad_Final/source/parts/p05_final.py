

# ----------------------------------------------------------------------------------------------
# materials / UV (atlas tile centres + prescribed planar and cylindrical maps) / mesh objects
# ----------------------------------------------------------------------------------------------
SRC_COLL = bpy.data.collections.new("SOURCE_Components")
SCENE.collection.children.link(SRC_COLL)
EXP_COLL = bpy.data.collections.new("EXPORT_GamerDad")
SCENE.collection.children.link(EXP_COLL)

atlas = bpy.data.images.load(os.path.join(INP, "GamerDad_Sweatshirt_Atlas.png"))
atlas.name = "GamerDad_Sweatshirt_Atlas"
atlas.colorspace_settings.name = 'sRGB'
atlas.pack()
assert tuple(atlas.size) == (ATLAS_PX, ATLAS_PX), tuple(atlas.size)
_apx = atlas.pixels[:]


def atlas_rgb(px, py):
    o = ((ATLAS_PX - 1 - py) * ATLAS_PX + px) * 4
    return tuple(int(round(_apx[o + i] * 255)) for i in range(3))


# the atlas palette tile centres must equal the 34 hex colours (palette order = tile index)
PAL_CHECK = []
for i, (n_, h_) in enumerate(PAL):
    got = atlas_rgb((i % COLS) * TILE_PX + TILE_PX // 2, (i // COLS) * TILE_PX + TILE_PX // 2)
    PAL_CHECK.append({"index": i, "name": n_, "hex": h_, "atlas_rgb": got, "ok": got == hex_rgb(h_)})
assert all(c["ok"] for c in PAL_CHECK), [c for c in PAL_CHECK if not c["ok"]]

MATP = bpy.data.materials.new("GamerDad_Atlas")
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

TWO_PI = 2.0 * math.pi
UV_STATS = {}
for pm in PARTS.values():
    bm = pm.bm
    bm.normal_update()
    me = bpy.data.meshes.new(pm.geo)
    bm.to_mesh(me)
    uv = me.uv_layers.new(name="UVMap")
    at_t, at_m, at_c = me.attributes.get("tile"), me.attributes.get("uvm"), me.attributes.get("comp")
    for pi, poly in enumerate(me.polygons):
        t = at_t.data[pi].value
        m = at_m.data[pi].value
        UV_STATS[m] = UV_STATS.get(m, 0) + 1
        if m == UVM_TILE:
            u_, v_ = tile_uv(t)
            for li in poly.loop_indices:
                uv.data[li].uv = (u_, v_)
            continue
        if m == UVM_CANWRAP:
            cc = V((0, 0, 0))
            for vi in poly.vertices:
                cc += me.vertices[vi].co
            cc /= len(poly.vertices)
            thc = math.atan2(cc.x - CAN_C.x, -(cc.y - CAN_C.y))
        for li in poly.loop_indices:
            p = me.vertices[me.loops[li].vertex_index].co
            if m == UVM_CANWRAP:
                th = math.atan2(p.x - CAN_C.x, -(p.y - CAN_C.y))
                th += TWO_PI * round((thc - th) / TWO_PI)
                th = max(-math.pi, min(math.pi, th))
                uv.data[li].uv = map_uv(m, p, th)
            else:
                uv.data[li].uv = map_uv(m, p)
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
    pm.n_faces_final = len(me.polygons)

# per-component face totals (comp attribute is only valid before it is dropped below)
COMP_FACES = {}
for pm in PARTS.values():
    at_c = pm.obj.data.attributes.get("comp")
    for pi in range(len(pm.obj.data.polygons)):
        COMP_FACES[COMP_LOG[at_c.data[pi].value]["id"] + "@" + pm.runtime] = COMP_FACES.get(COMP_LOG[at_c.data[pi].value]["id"] + "@" + pm.runtime, 0) + 1
if not KEEPCOMP:
    for pm in PARTS.values():
        for nm in ("tile", "uvm", "comp"):
            a_ = pm.obj.data.attributes.get(nm)
            if a_ is not None:
                pm.obj.data.attributes.remove(a_)
for pm in PARTS.values():
    pm.bm.free()

# ----------------------------------------------------------------------------------------------
# armature (project-standard hierarchy) + rigid 100% weights; the model is built directly in the HoldCan pose (rest pose == display pose)
# ----------------------------------------------------------------------------------------------
BODY_NAMES = ["Head", "UpperTorso", "LowerTorso", "RightUpperArm", "RightLowerArm", "RightHand", "LeftUpperArm", "LeftLowerArm", "LeftHand",
              "RightUpperLeg", "RightLowerLeg", "RightFoot", "LeftUpperLeg", "LeftLowerLeg", "LeftFoot"]
PROPS = ["Headset", "EnergyCan"]
assert set(BODY_NAMES + PROPS) == set(PARTS), set(PARTS) ^ set(BODY_NAMES + PROPS)
arm_data = bpy.data.armatures.new("GamerDad_Armature")
ARM_OB = bpy.data.objects.new("GamerDad_Armature", arm_data)
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
for pm in PARTS.values():
    bone = "Head" if pm.runtime == "Headset" else ("RightHand" if pm.runtime == "EnergyCan" else pm.runtime)
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
def world_verts(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ev.matrix_world
    out = [mw @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    return out


def bbox(pts):
    lo = V((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = V((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def mesh_audit(ob):
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    open_e = sum(1 for e in bm.edges if len(e.link_faces) == 1)
    nm = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    zero = sum(1 for f in bm.faces if f.calc_area() < 1e-8)
    cen = sum((v.co for v in bm.verts), V()) / max(1, len(bm.verts))
    vol = 0.0
    for f in bm.faces:
        vv = [v.co - cen for v in f.verts]
        for k in range(1, len(vv) - 1):
            vol += vv[0].dot(vv[k].cross(vv[k + 1])) / 6.0
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    bm.free()
    uvs = me.uv_layers.active.data
    uv_bad = sum(1 for l in uvs if not (-1e-6 <= l.uv[0] <= 1 + 1e-6 and -1e-6 <= l.uv[1] <= 1 + 1e-6))
    return {"verts": len(me.vertices), "tris": tris, "open_edges": open_e, "nonmanifold_edges": nm, "zero_faces": zero, "signed_volume": round(vol, 5), "uv_outside_0_1": uv_bad}


AUDIT = {pm.runtime: mesh_audit(pm.obj) for pm in PARTS.values()}
ALLV = {pm.runtime: world_verts(pm.obj) for pm in PARTS.values()}
body_lo, body_hi = bbox([p for n in BODY_NAMES for p in ALLV[n]])
all_lo, all_hi = bbox([p for n in BODY_NAMES + PROPS for p in ALLV[n]])
feet_lo, _ = bbox(ALLV["RightFoot"] + ALLV["LeftFoot"])
body_tris = sum(AUDIT[n]["tris"] for n in BODY_NAMES)
prop_tris = sum(AUDIT[n]["tris"] for n in PROPS)
print("AUDIT", json.dumps({k: [v["open_edges"], v["nonmanifold_edges"], v["zero_faces"], v["tris"], v["uv_outside_0_1"]] for k, v in AUDIT.items()}))
print("BOUNDS", [round(c, 4) for c in all_lo], [round(c, 4) for c in all_hi], "feet min H", round(feet_lo.z, 5), "tris body/props", body_tris, prop_tris)


def bvh_world(name):
    ob = PARTS[name].obj
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ev.matrix_world
    verts = [mw @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys), verts


def pair_check(a, b):
    ta, va = bvh_world(a)
    tb, vb = bvh_world(b)
    ov = len(ta.overlap(tb))
    d = 1e9
    for p in va:
        loc, nrm_, idx, dist = tb.find_nearest(p)
        d = min(d, dist)
    for p in vb:
        loc, nrm_, idx, dist = ta.find_nearest(p)
        d = min(d, dist)
    return {"overlapping_triangle_pairs": ov, "min_vertex_to_surface": round(d, 4)}


CHECKS = {}
for a, b in (("EnergyCan", "RightHand"), ("EnergyCan", "RightLowerArm"), ("EnergyCan", "RightUpperArm"), ("EnergyCan", "UpperTorso"), ("EnergyCan", "Head"), ("EnergyCan", "Headset"),
             ("Headset", "Head"), ("Headset", "UpperTorso"), ("LeftHand", "LowerTorso"), ("LeftHand", "LeftUpperLeg"), ("LeftHand", "UpperTorso"),
             ("RightUpperArm", "RightLowerArm"), ("LeftUpperArm", "LeftLowerArm"), ("RightLowerArm", "RightHand"), ("LeftLowerArm", "LeftHand"),
             ("RightUpperLeg", "LeftUpperLeg"), ("RightFoot", "LeftFoot"), ("RightLowerLeg", "RightFoot"), ("UpperTorso", "LowerTorso"), ("UpperTorso", "RightUpperArm"), ("UpperTorso", "LeftUpperArm")):
    CHECKS[a + "_vs_" + b] = pair_check(a, b)


def comp_world_tris(part, cid):
    """triangles (world) of one registered component of a part (needs the comp attribute: only valid with --keepcomp)."""
    return None


def tri_set(ob, prefix_ids=None):
    return None


# ----------------------------------------------------------------------------------------------
# outputs: blend, FBX, data
# ----------------------------------------------------------------------------------------------
for sub in ("export", "data", "source"):
    os.makedirs(os.path.join(OUT, sub), exist_ok=True)
BLEND = os.path.join(OUT, "source", "GamerDad_Sweatshirt_Review.blend")
FBX_BODY = os.path.join(OUT, "export", "GamerDad_R15.fbx")
FBX_PROPS = os.path.join(OUT, "export", "GamerDad_Props.fbx")
FBX_SET = dict(use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y',
               mesh_smooth_type='FACE', use_mesh_modifiers=True, bake_anim=False, add_leaf_bones=False,
               path_mode='COPY', embed_textures=True, use_armature_deform_only=False, primary_bone_axis='Y', secondary_bone_axis='X')


def export_fbx(path, objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, object_types={'MESH', 'ARMATURE'}, **FBX_SET)


export_fbx(FBX_BODY, [ARM_OB] + [PARTS[n].obj for n in BODY_NAMES])
prop_copies = []
for n in PROPS:
    cp = bpy.data.objects.new(n + "_Geo", PARTS[n].obj.data.copy())
    cp.data.name = n + "_Geo_export"
    EXP_COLL.objects.link(cp)
    cp.location = PARTS[n].joint
    prop_copies.append(cp)
export_fbx(FBX_PROPS, prop_copies)
for cp in prop_copies:
    bpy.data.objects.remove(cp, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("EXPORTED", FBX_BODY, FBX_PROPS, BLEND)


def r3(v, n=4):
    return [round(float(c), n) for c in v]


def roblox_pos(p):
    return [round(-p[0], 5), round(p[2], 5), round(p[1], 5)]


os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
shutil_copy = __import__("shutil").copy
shutil_copy(os.path.join(INP, "GamerDad_Sweatshirt_Atlas.png"), os.path.join(OUT, "GamerDad_Sweatshirt_Atlas.png"))
uvmap = {"atlas": "GamerDad_Sweatshirt_Atlas.png", "size": [ATLAS_PX, ATLAS_PX], "tile_px": TILE_PX, "columns": COLS, "palette_rect_px": [0, 0, 256, 256],
         "tile_uv_rule": "u=(32 col+16)/1024, v=1-(32 row+16)/1024", "tiles": [], "maps": {
             "gamepad": "px=384+204x, py=128-204h (x,h relative to the print centre X=0,H=3.76) on the real front faces of UT_shell inside the window X+/-.60, H3.16..4.36",
             "face": "px=256(X+1.01)/2.02, py=256+512(6.22-H)/1.62 on the front faces of HD_shell (normal.y<-.35)",
             "nose": "px=384+256X/.53, py=512+128(5.45-H)/.46 on all faces of HD_nose",
             "can_wrap": "px=768+512 theta/2pi, py=512(.54-z)/1.15 on the blue band z-.61..+.54 (theta=0 towards -D, seam at the back)",
             "can_top": "px=384+128x/.245, py=384+128d/.245 on the recessed cap (x,d relative to the can axis)"}, "palette_check": PAL_CHECK, "uv_face_counts_by_map": UV_STATS}
for i, (n_, h_) in enumerate(PAL):
    u_, v_ = tile_uv(i)
    uvmap["tiles"].append({"index": i, "name": n_, "hex": h_, "col": i % COLS, "row": i // COLS, "uv_centre": [u_, v_]})
json.dump(uvmap, open(os.path.join(OUT, "data", "palette_uv_map.json"), "w"), indent=1)

CENTRES = {}
BBOXES = {}
for n in BODY_NAMES + PROPS:
    lo, hi = bbox(ALLV[n])
    CENTRES[n] = r3((lo + hi) / 2.0, 6)
    BBOXES[n] = {"min": r3(lo, 5), "max": r3(hi, 5), "size": r3(hi - lo, 5), "centre": CENTRES[n]}
RESULT = {"bounds_all": {"min": r3(all_lo), "max": r3(all_hi), "height": round(all_hi.z - all_lo.z, 4)}, "bounds_body": {"min": r3(body_lo), "max": r3(body_hi), "height": round(body_hi.z - body_lo.z, 4)},
          "feet_min_h": round(feet_lo.z, 5), "tris_body": body_tris, "tris_props": prop_tris, "tris_total": body_tris + prop_tris, "audit": AUDIT, "checks": CHECKS, "pose_bones_identity": POSE_IDENTITY,
          "part_bboxes_logical": BBOXES}
json.dump(RESULT, open(os.path.join(OUT, "data", "_build_result.json"), "w"), indent=1)
SPEC = {"asset": "GamerDad_Sweatshirt_Review", "character": "Gamer Dad (05, Rare) - sweatshirt version", "units": "studs", "plan_height": 6.40, "built_height": RESULT["bounds_all"]["height"],
        "joints": {k: list(v) for k, v in JOINTS.items()}, "arm_lengths": {"upper": UP_LEN, "lower": LO_LEN},
        "joint_length_errors": {s + "_" + k: abs((JV[s + a] - JV[s + b]).length - L) for s in ("Right", "Left") for k, a, b, L in (("upper", "Shoulder", "Elbow", UP_LEN), ("lower", "Elbow", "Wrist", LO_LEN))},
        "hand_centres": SPEC_IN["hand_centers"], "can": SPEC_IN["can"], "palette": [{"index": i, "name": n_, "hex": h_} for i, (n_, h_) in enumerate(PAL)],
        "elbow": ELBOW_LOG, "counts": {"body_tris": body_tris, "prop_tris": prop_tris, "parts": len(PARTS), "components_registered": len(COMP_LOG)},
        "deviations_from_prompt": DEVIATIONS, "measured": {k: v for k, v in RESULT.items() if k != "part_bboxes_logical"}}
json.dump(SPEC, open(os.path.join(OUT, "data", "construction_spec.json"), "w"), indent=1, default=str)
json.dump({"asset": "GamerDad_Sweatshirt_Review", "components": COMP_LOG, "faces_by_component": COMP_FACES,
           "part_totals": {k: {"components": len(v.comps), "tris": AUDIT[k]["tris"], "verts": AUDIT[k]["verts"]} for k, v in PARTS.items()},
           "mesh_names": {k: v.geo for k, v in PARTS.items()}}, open(os.path.join(OUT, "data", "component_registry.json"), "w"), indent=1, default=str)
RIG = {"asset": "GamerDad_Sweatshirt_Review", "frame": {"logical": "(X,D,H) forward=-D, anatomical RIGHT=-X", "roblox_position": "(-X, H, D)"},
       "bones": [{"name": n, "parent": p, "head_logical": r3(h, 6), "tail_logical": r3(t, 6), "head_roblox": roblox_pos(h)} for n, p, h, t in BONES],
       "part_origin_logical": {k: r3(v.joint, 6) for k, v in PARTS.items()}, "part_bbox_centres_logical": CENTRES,
       "weights": "100% own bone (rigid); Headset -> Head, EnergyCan -> RightHand (props are exported as separate meshes without armature)", "pose": "HoldCan == rest pose (built directly, pose bones identity)"}
json.dump(RIG, open(os.path.join(OUT, "data", "rig_manifest.json"), "w"), indent=1)
print("RESULT", json.dumps({k: RESULT[k] for k in ("bounds_all", "tris_body", "tris_props", "pose_bones_identity")}))
