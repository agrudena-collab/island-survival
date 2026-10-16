

# ----------------------------------------------------------------------------------------------
# materials / UV / vertex colors / mesh objects
# ----------------------------------------------------------------------------------------------
atlas = bpy.data.images.new("GrillDad_Palette", ATLAS_W, ATLAS_H, alpha=False)
atlas.colorspace_settings.name = 'sRGB'   # must be set BEFORE writing pixels
px = [0.0] * (ATLAS_W * ATLAS_H * 4)
fill = hex_rgb(_H["APRON"])
for ty in range(ATLAS_H):
    for tx in range(ATLAS_W):
        idx = (ty // TILE_PX) * COLS + (tx // TILE_PX)
        rgb = hex_rgb(PAL[idx][1]) if idx < len(PAL) else fill
        r, g, b = (c / 255.0 for c in rgb)
        o = ((ATLAS_H - 1 - ty) * ATLAS_W + tx) * 4
        px[o:o + 4] = [r, g, b, 1.0]
atlas.pixels.foreach_set(px)
atlas.filepath_raw = os.path.join(OUT, "GrillDad_Palette.png")
atlas.file_format = 'PNG'
atlas.save()
atlas.pack()

MATP = bpy.data.materials.new("GrillDad_Palette")
MATP.use_nodes = True
nt = MATP.node_tree
bs = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = atlas
tex.interpolation = 'Closest'
nt.links.new(tex.outputs["Color"], bs.inputs["Base Color"])
bs.inputs["Roughness"].default_value = 0.9
try:
    bs.inputs["Specular IOR Level"].default_value = 0.05
except KeyError:
    pass

PROPS = ("GrillTongs",)
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
# armature (standard-compatible hierarchy) + rigid 100% weights for the 15 body parts
# ----------------------------------------------------------------------------------------------
arm_data = bpy.data.armatures.new("GrillDad_Armature")
ARM_OB = bpy.data.objects.new("GrillDad_Armature", arm_data)
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
    hand_tail = GRIP_C if side == "Left" else JV["RightWrist"] + V((0, 0, -.68))
    BONES += [
        (side + "UpperArm", "UpperTorso", JV[side + "Shoulder"], JV[side + "Elbow"]),
        (side + "LowerArm", side + "UpperArm", JV[side + "Elbow"], JV[side + "Wrist"]),
        (side + "Hand", side + "LowerArm", JV[side + "Wrist"], hand_tail),
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
    if pm.runtime in PROPS:
        continue
    ob = pm.obj
    vg = ob.vertex_groups.new(name=pm.runtime)
    vg.add([v.index for v in ob.data.vertices], 1.0, 'REPLACE')
    md = ob.modifiers.new("Armature", 'ARMATURE')
    md.object = ARM_OB
    ob.parent = ARM_OB
    ob.matrix_parent_inverse = Matrix.Identity(4)
tongs_ob = PARTS["GrillTongs"].obj
PB = ARM_OB.pose.bones

# ----------------------------------------------------------------------------------------------
# cameras / light / render helpers
# ----------------------------------------------------------------------------------------------
world = bpy.data.worlds.new("FD_World")
SCENE.world = world
world.use_nodes = True
_wn = world.node_tree.nodes
_wl = world.node_tree.links
_bg_a = _wn["Background"]
_bg_a.inputs[0].default_value = (0.90, 0.88, 0.84, 1.0)
_bg_a.inputs[1].default_value = 0.66
_bg_b = _wn.new("ShaderNodeBackground")
_bg_b.inputs[0].default_value = (0.92, 0.90, 0.87, 1.0)
_bg_b.inputs[1].default_value = 1.0
_lp = _wn.new("ShaderNodeLightPath")
_mix = _wn.new("ShaderNodeMixShader")
_wl.new(_lp.outputs["Is Camera Ray"], _mix.inputs[0])
_wl.new(_bg_a.outputs[0], _mix.inputs[1])
_wl.new(_bg_b.outputs[0], _mix.inputs[2])
_wl.new(_mix.outputs[0], _wn["World Output"].inputs["Surface"])
sun_d = bpy.data.lights.new("FD_Key", 'SUN')
sun_d.energy = 1.8
sun = bpy.data.objects.new("FD_Key", sun_d)
SCENE.collection.objects.link(sun)
sun.rotation_euler = (math.radians(52), math.radians(8), math.radians(-38))
fill_d = bpy.data.lights.new("FD_Fill", 'SUN')
fill_d.energy = 0.55
fill_d.use_shadow = False
fill = bpy.data.objects.new("FD_Fill", fill_d)
SCENE.collection.objects.link(fill)
fill.rotation_euler = (math.radians(60), 0, math.radians(140))
cam_d = bpy.data.cameras.new("FD_Cam")
CAM = bpy.data.objects.new("FD_Cam", cam_d)
SCENE.collection.objects.link(CAM)
SCENE.camera = CAM
SCENE.render.engine = 'BLENDER_EEVEE'
SCENE.eevee.taa_render_samples = 8 if QUICK else 32
SCENE.render.image_settings.file_format = 'PNG'
SCENE.view_settings.view_transform = 'Standard'
SCENE.render.film_transparent = False
# floor shadow catcher is omitted (clean neutral background like the first two dads)


def cam_look(loc, target, lens=70.0):
    CAM.location = V(loc)
    CAM.rotation_euler = (V(target) - V(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.type, cam_d.lens, cam_d.sensor_width = 'PERSP', lens, 36.0


def orbit(target, dist, az_deg, el_deg):
    az, el = math.radians(az_deg), math.radians(el_deg)
    t = V(target)
    return t + V((dist * math.sin(az) * math.cos(el), -dist * math.cos(az) * math.cos(el), dist * math.sin(el)))


RENDERED = []


def shot(name, loc, target, res=(1000, 1000), lens=70.0, show_only=None, hide=None):
    for pm in PARTS.values():
        hid = (show_only is not None and pm.runtime not in show_only) or (hide is not None and pm.runtime in hide)
        pm.obj.hide_render = hid
    SCENE.render.resolution_x, SCENE.render.resolution_y = res
    cam_look(loc, target, lens)
    SCENE.render.filepath = os.path.join(OUT, "renders", name)
    bpy.ops.render.render(write_still=True)
    RENDERED.append(name)
    print("RENDERED", name)


# ----------------------------------------------------------------------------------------------
# audits
# ----------------------------------------------------------------------------------------------
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


BODY = [PARTS[k].obj for k in PARTS if k not in PROPS]
lo, hi = world_bounds(BODY)
head_lo, head_hi = world_bounds([PARTS["Head"].obj])
ft_lo, _ = world_bounds([PARTS["RightFoot"].obj, PARTS["LeftFoot"].obj])
tg_lo, tg_hi = world_bounds([tongs_ob])
body_tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in BODY)
tongs_tris = sum(len(p.vertices) - 2 for p in tongs_ob.data.polygons)
print("BOUNDS body", tuple(round(x, 3) for x in lo), tuple(round(x, 3) for x in hi))
print("TONGS", tuple(round(x, 3) for x in tg_lo), tuple(round(x, 3) for x in tg_hi))
print("HEAD", tuple(round(x, 3) for x in head_lo), tuple(round(x, 3) for x in head_hi), "FEET", round(ft_lo.z, 4))
print("TRIS body", body_tris, "tongs", tongs_tris)

from collections import Counter
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
    AUDIT[pm.runtime] = {"verts": len(me.vertices), "tris": sum(len(p.vertices) - 2 for p in me.polygons),
                         "open_edges": sum(1 for v in cnt.values() if v == 1), "zero_area": sum(1 for f in bmx.faces if f.calc_area() < 1e-9),
                         "signed_volume": round(vol, 4)}
    bmx.free()


def bvh_of(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    bmx = bmesh.new()
    bmx.from_mesh(me)
    bmx.transform(ev.matrix_world)
    ev.to_mesh_clear()
    t = BVHTree.FromBMesh(bmx)
    pts = [v.co.copy() for v in bmx.verts]
    bmx.free()
    return t, pts


def pair_check(a_name, names):
    res = {}
    ta, pa = bvh_of(PARTS[a_name].obj)
    for n in names:
        t, pts = bvh_of(PARTS[n].obj)
        res[n] = {"overlapping_triangle_pairs": len(ta.overlap(t)), "min_distance": round(min((t.find_nearest(p)[3] or 9e9) for p in pa), 4)}
    return res


TONGS_CHECK = pair_check("GrillTongs", ["LeftHand", "LeftLowerArm", "LeftUpperArm", "UpperTorso", "Head", "LowerTorso", "RightHand", "LeftUpperLeg", "LeftFoot"])
HAND_CHECK = pair_check("LeftHand", ["LeftLowerArm", "UpperTorso", "Head", "LeftUpperArm"])
UT_CHECK = {}
for n in ("Head", "LowerTorso", "LeftUpperArm", "RightUpperArm", "RightUpperLeg", "LeftUpperLeg"):
    ta, pa = bvh_of(PARTS["UpperTorso"].obj)
    t, pts = bvh_of(PARTS[n].obj)
    UT_CHECK[n] = {"overlapping_triangle_pairs": len(ta.overlap(t))}
print("TONGSCHECK", json.dumps(TONGS_CHECK))
print("HANDCHECK", json.dumps(HAND_CHECK))
print("UTCHECK", json.dumps(UT_CHECK))
th_, tp_ = bvh_of(PARTS["LeftHand"].obj)
grip_clear = []
for h in [3.09 + .1 * i for i in range(9)]:
    for sgn in (-1, 1):
        p = V((GRIP_C.x + sgn * branch_u(h), GRIP_C.y, h))
        d = th_.find_nearest(p)[3]
        grip_clear.append(round((d if d is not None else 9e9), 4))
print("GRIP wood-axis -> hand surface distance (H3.09..3.89, both branches):", grip_clear)

# ----------------------------------------------------------------------------------------------
# outputs: blend, FBX, spec JSON
# ----------------------------------------------------------------------------------------------
os.makedirs(os.path.join(OUT, "export"), exist_ok=True)
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
os.makedirs(os.path.join(OUT, "source"), exist_ok=True)
BLEND = os.path.join(OUT, "source", "GrillDad_Redesign.blend")
FBX_BODY = os.path.join(OUT, "export", "GrillDad_R15.fbx")
FBX_TONGS = os.path.join(OUT, "export", "GrillDad_Tongs.fbx")
FBX_SET = dict(use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y',
               mesh_smooth_type='FACE', use_mesh_modifiers=True, bake_anim=False, add_leaf_bones=False,
               path_mode='COPY', embed_textures=True, use_armature_deform_only=False, primary_bone_axis='Y', secondary_bone_axis='X')


def export_fbx(path, objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, object_types={'MESH', 'ARMATURE'}, **FBX_SET)


for pm in PARTS.values():
    pm.obj.hide_render = False
export_fbx(FBX_BODY, [ARM_OB] + BODY)
for nm, path in (("GrillTongs", FBX_TONGS),):
    src = PARTS[nm].obj
    cp = bpy.data.objects.new(nm + "_Geo", src.data.copy())
    cp.data.name = nm + "_Geo_export"
    EXP_COLL.objects.link(cp)
    cp.location = PARTS[nm].joint
    export_fbx(path, [cp])
    bpy.data.objects.remove(cp, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("EXPORTED", FBX_BODY, FBX_TONGS, BLEND)

uvmap = {"atlas": "GrillDad_Palette.png", "size": [ATLAS_W, ATLAS_H], "tile_px": TILE_PX, "columns": COLS, "inset_px": INSET,
         "row0_is_top_of_png": True, "unused_tiles_filled_with": "APRON", "tiles": []}
for i, (n_, h_, use) in enumerate(PAL):
    u0, v0, u1, v1 = tile_uv_patch(i)
    uvmap["tiles"].append({"index": i, "name": n_, "hex": h_, "use": use, "col": i % COLS, "row": i // COLS, "uv_patch": [u0, v0, u1, v1]})
json.dump(uvmap, open(os.path.join(OUT, "data", "palette_uv_map.json"), "w"), indent=1, ensure_ascii=False)


def r3(v):
    return [round(float(c), 4) for c in v]


def roblox_pos(p):
    return [round(-p[0], 4), round(p[2], 4), round(p[1], 4)]


RESULT = {"bounds_neutral": {"min": r3(lo), "max": r3(hi), "height": round(hi.z - lo.z, 4)}, "head_bounds": {"min": r3(head_lo), "max": r3(head_hi)},
          "tongs_bounds": {"min": r3(tg_lo), "max": r3(tg_hi)}, "feet_min_h": round(ft_lo.z, 5), "tris_body": body_tris, "tris_tongs": tongs_tris,
          "audit": AUDIT, "tongs_vs_body": TONGS_CHECK, "hand_vs_body": HAND_CHECK, "torso_vs_parts": UT_CHECK, "grip_wood_axis_to_hand_surface": grip_clear}
json.dump(RESULT, open(os.path.join(OUT, "data", "_build_result.json"), "w"), indent=1)
SPEC = {"asset": "GrillDad_Redesign", "character": "Grill Dad (04, Uncommon)", "units": "studs", "neutral_height": 6.40, "built_height": RESULT["bounds_neutral"]["height"],
        "tables": {"UpperTorso": UT_ROWS, "LowerTorso": LT_ROWS, "Head": HEAD_ROWS, "Apron": APRON_ROWS, "Stains": STAINS},
        "joints_built": {k: list(v) for k, v in JOINTS.items()}, "joints_bind_neutral": {k: r3(v) for k, v in BIND.items()},
        "left_arm_ik": {"shoulder": r3(LEFT_S), "wrist_target": r3(LEFT_W), "pole": r3(LEFT_POLE), "elbow": [round(float(c), 9) for c in LEFT_E],
                        "upper_len": round(SEG_UP, 10), "lower_len": round(SEG_LO, 10),
                        "check_len_upper": round((LEFT_E - LEFT_S).length, 10), "check_len_lower": round((LEFT_W - LEFT_E).length, 10)},
        "grip_center": r3(GRIP_C), "tongs_branch_u": [list(a) for a in TONG_U], "tongs_origin": r3(GRIP_C),
        "palette": [{"index": i, "name": n_, "hex": h_} for i, (n_, h_, _u) in enumerate(PAL)],
        "counts": {"body_tris": body_tris, "tongs_tris": tongs_tris},
        "deviations_from_prompt": [
            "Left arm is built directly in the HoldTongs pose (rest == pose); the neutral bind joints are stored in joints_bind_neutral.",
            "Forearm end is buried -0.03 behind the wrist and carved by the same channel as the hand.",
            "Thumb pad centre D is -.935 instead of -.91 so that it protrudes .035 from the front face.",
            "Paddles are not yawed by +/-8 deg and the wooden top ends are not tilted by 5 deg (both optional in the prompt).",
            "Rear hair U band keeps a constant top H5.98 (the prompt lowers it to 5.88 at the centre).",
            "No spring coils on the bridge (optional).",
            "Apron belt is a closed wrap of the whole torso at H2.57..2.77; the towel rear tail is a short hidden sheet.",
            "Strap front ends follow the real apron surface (D computed) instead of the literal key point D-.86."],
        "measured": RESULT}
json.dump(SPEC, open(os.path.join(OUT, "data", "construction_spec.json"), "w"), indent=1, ensure_ascii=False)
json.dump({"asset": "GrillDad_Redesign", "components": COMP_LOG,
           "part_totals": {k: {"components": len(v.comps), "tris": AUDIT[k]["tris"], "verts": AUDIT[k]["verts"]} for k, v in PARTS.items()},
           "mesh_names": {k: v.geo for k, v in PARTS.items()}}, open(os.path.join(OUT, "data", "component_registry.json"), "w"), indent=1, ensure_ascii=False)
RIG = {"asset": "GrillDad_Redesign", "frame": {"logical": "(X,D,H) forward=-D, anatomical LEFT=+X (tongs hand), towel on the anatomical RIGHT (X<0)", "roblox_position": "(-X, H, D)"},
       "bones": [{"name": n, "parent": p, "head_logical": r3(h), "tail_logical": r3(t), "head_roblox": roblox_pos(h)} for n, p, h, t in BONES],
       "props": {"GrillTongs": {"mount": "TongsGrip WeldConstraint LeftHand -> GrillTongs", "origin_logical": r3(GRIP_C), "grip_world": r3(GRIP_C)}},
       "weights": "100% own bone (rigid style); rest pose == HoldTongs"}
json.dump(RIG, open(os.path.join(OUT, "data", "rig_manifest.json"), "w"), indent=1)
print("RESULT", json.dumps({k: RESULT[k] for k in ("bounds_neutral", "tris_body", "tris_tongs")}))
if NORENDER:
    sys.exit(0)

# ----------------------------------------------------------------------------------------------
# renders (section 31)
# ----------------------------------------------------------------------------------------------
T = V((.45, -.2, 3.30))
MC = V((.25, -.20, 3.30))
shot("01_matching_34.png", (-7.0, -15.0, 7.0), MC, res=(416 * 2, 382 * 2), lens=70)
shot("01b_native_416x382.png", (-7.0, -15.0, 7.0), MC, res=(416, 382), lens=70)
shot("02_front.png", orbit(T, 17, 0, 4), T, res=(1000, 1000))
shot("03_back.png", orbit(T, 17, 180, 4), T, res=(1000, 1000))
shot("04_left_profile.png", orbit(T, 17, 90, 4), T, res=(1000, 1000))
shot("05_right_profile.png", orbit(T, 17, -90, 4), T, res=(1000, 1000))
shot("06_back_right34.png", orbit(T, 17, -150, 12), T, res=(1000, 1000))
HT = V((0, -.2, 5.6))
shot("07_head_front.png", orbit(HT, 6.0, 0, 2), HT, res=(900, 900), hide=("GrillTongs",))
shot("07b_head_34.png", orbit(HT, 6.0, -30, 8), HT, res=(900, 900), hide=("GrillTongs",))
shot("08_head_top.png", orbit(HT, 6.0, 0, 78), HT, res=(900, 900), hide=("GrillTongs",))
shot("08b_head_back.png", orbit(HT, 6.0, 180, 8), HT, res=(900, 900), hide=("GrillTongs",))
AT = V((0, -.3, 2.9))
shot("09_apron_front.png", orbit(AT, 8.0, 0, 4), AT, res=(900, 900), hide=("GrillTongs",))
shot("09b_apron_side.png", orbit(AT, 8.0, -70, 8), AT, res=(900, 900), hide=("GrillTongs",))
shot("09c_apron_back.png", orbit(AT, 8.0, 180, 4), AT, res=(900, 900), hide=("GrillTongs",))
TW = V((-.95, -1.1, 2.15))
shot("10_towel_front.png", orbit(TW, 3.6, -10, 4), TW, res=(900, 900), hide=("GrillTongs",))
shot("10b_towel_side.png", orbit(TW, 3.6, -80, 6), TW, res=(900, 900), hide=("GrillTongs",))
shot("10c_towel_bottom.png", orbit(TW, 3.6, -20, -40), TW, res=(900, 900), hide=("GrillTongs",))
GT = V((2.30, -.62, 3.50))
shot("11_hand_front.png", orbit(GT, 3.2, 0, 4), GT, res=(900, 900))
shot("11b_hand_back.png", orbit(GT, 3.2, 180, 4), GT, res=(900, 900))
shot("11c_hand_top.png", orbit(GT, 3.2, 0, 80), GT, res=(900, 900))
shot("11d_hand_side.png", orbit(GT, 3.2, 90, 4), GT, res=(900, 900))
TT = V((2.30, -.62, 4.20))
shot("12_tongs_front.png", orbit(TT, 6.0, 0, 3), TT, res=(900, 900), show_only=("GrillTongs",))
shot("12b_tongs_side.png", orbit(TT, 6.0, 90, 3), TT, res=(900, 900), show_only=("GrillTongs",))
shot("12c_tongs_back.png", orbit(TT, 6.0, 180, 3), TT, res=(900, 900), show_only=("GrillTongs",))
BT = V((0, -.2, 1.0))
shot("13_shoes.png", orbit(BT, 6.5, -30, 10), BT, res=(1000, 800), hide=("GrillTongs",))
shot("14_gate_full_256.png", (-7.0, -15.0, 7.0), MC, res=(256, 256), lens=70)
print("ALL_RENDERS_DONE", len(RENDERED))
