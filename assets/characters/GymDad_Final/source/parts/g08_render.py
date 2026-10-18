
if NORENDER:
    sys.exit(0)

# ----------------------------------------------------------------------------------------------
# cameras / light / render helpers (real Blender renders of the built scene)
# ----------------------------------------------------------------------------------------------
world = bpy.data.worlds.new("GD_World")
SCENE.world = world
world.use_nodes = True
_wn = world.node_tree.nodes
_wl = world.node_tree.links
_bg_a = _wn["Background"]
_bg_a.inputs[0].default_value = (0.90, 0.88, 0.84, 1.0)
_bg_a.inputs[1].default_value = 0.66
_bg_b = _wn.new("ShaderNodeBackground")
_bg_b.inputs[0].default_value = (0.94, 0.91, 0.86, 1.0)      # backdrop #F0E8DC-like
_bg_b.inputs[1].default_value = 1.0
_lp = _wn.new("ShaderNodeLightPath")
_mix = _wn.new("ShaderNodeMixShader")
_wl.new(_lp.outputs["Is Camera Ray"], _mix.inputs[0])
_wl.new(_bg_a.outputs[0], _mix.inputs[1])
_wl.new(_bg_b.outputs[0], _mix.inputs[2])
_wl.new(_mix.outputs[0], _wn["World Output"].inputs["Surface"])
sun_d = bpy.data.lights.new("GD_Key", 'SUN')
sun_d.energy = 1.8
sun = bpy.data.objects.new("GD_Key", sun_d)
SCENE.collection.objects.link(sun)
sun.rotation_euler = (math.radians(52), math.radians(8), math.radians(-38))
fill_d = bpy.data.lights.new("GD_Fill", 'SUN')
fill_d.energy = 0.55
fill_d.use_shadow = False
fill = bpy.data.objects.new("GD_Fill", fill_d)
SCENE.collection.objects.link(fill)
fill.rotation_euler = (math.radians(60), 0, math.radians(140))
cam_d = bpy.data.cameras.new("GD_Cam")
CAM = bpy.data.objects.new("GD_Cam", cam_d)
SCENE.collection.objects.link(CAM)
SCENE.camera = CAM
SCENE.render.engine = 'BLENDER_EEVEE'
SCENE.eevee.taa_render_samples = 8 if QUICK else 32
SCENE.render.image_settings.file_format = 'PNG'
SCENE.view_settings.view_transform = 'Standard'
SCENE.render.film_transparent = False

FLATM = bpy.data.materials.new("GD_Flat")
FLATM.use_nodes = True
FLATM.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.42, 0.42, 0.44, 1.0)
FLATM.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0


def cam_persp(loc, target, lens=70.0):
    CAM.location = V(loc)
    CAM.rotation_euler = (V(target) - V(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.type, cam_d.lens, cam_d.sensor_width = 'PERSP', lens, 36.0


def cam_ortho(loc, target, scale, roll_deg=0.0):
    CAM.location = V(loc)
    q = (V(target) - V(loc)).to_track_quat('-Z', 'Y')
    CAM.rotation_euler = q.to_euler()
    if roll_deg:
        CAM.rotation_euler = (q @ Quaternion((0, 0, -1), math.radians(roll_deg))).to_euler()
    cam_d.type, cam_d.ortho_scale = 'ORTHO', scale
    cam_d.clip_start, cam_d.clip_end = 0.1, 200.0


def orbit(target, dist, az_deg, el_deg):
    az, el = math.radians(az_deg), math.radians(el_deg)
    t = V(target)
    return t + V((dist * math.sin(az) * math.cos(el), -dist * math.cos(az) * math.cos(el), dist * math.sin(el)))


RENDERED = []
RDIR = os.path.join(OUT, "renders")


def shot(name, loc, target, res=(900, 1000), lens=70.0, ortho=None, show_only=None, hide=(), flat=False, roll=0.0):
    for pm in PARTS.values():
        vis = (show_only is None or pm.runtime in show_only) and pm.runtime not in hide
        pm.obj.hide_render = not vis
    bpy.context.view_layer.material_override = FLATM if flat else None
    SCENE.render.resolution_x, SCENE.render.resolution_y = res
    if ortho:
        cam_ortho(loc, target, ortho, roll)
    else:
        cam_persp(loc, target, lens)
    SCENE.render.filepath = os.path.join(RDIR, name)
    bpy.ops.render.render(write_still=True)
    bpy.context.view_layer.material_override = None
    RENDERED.append(name)
    print("RENDERED", name)


# matching camera: ortho, view from logical (8,12,7) = Blender (8,-12,7), target (0,0,3.15), Ortho Scale 7.8 (start values of the plan)
MATCH_DIR = V((8, -12, 7)).normalized()
MATCH_T = V((0, 0, 3.15))
MATCH_LOC = MATCH_T + MATCH_DIR * 40
CAMCFG = {"type": "ORTHO", "target": [0, 0, 3.15], "direction_blender": list(MATCH_DIR), "distance": 40.0, "ortho_scale": 7.8, "roll_deg": 0.0,
          "note": "start camera of the plan; tuned values are written below if a tuning pass was done"}
if os.path.exists(os.path.join(HERE, "inputs", "camera_tuned.json")):
    CAMCFG.update(json.load(open(os.path.join(HERE, "inputs", "camera_tuned.json"))))
    MATCH_DIR = V(CAMCFG["direction_blender"]).normalized()
    MATCH_T = V(CAMCFG.get("target", [0, 0, 3.15]))
    MATCH_LOC = MATCH_T + MATCH_DIR * CAMCFG["distance"]
json.dump(CAMCFG, open(os.path.join(OUT, "data", "camera.json"), "w"), indent=1)

T = V((0, 0, 3.2))
SC = 7.6
# stage views (the model is built in one pass; these are the staged views of the finished scene)
shot("stage01_silhouette.png", MATCH_LOC, MATCH_T, res=(880, 860), ortho=CAMCFG["ortho_scale"], flat=True, show_only=[k for k in PARTS if k not in PROPS], roll=CAMCFG["roll_deg"])
shot("stage02_face_clothes.png", MATCH_LOC, MATCH_T, res=(880, 860), ortho=CAMCFG["ortho_scale"], hide=PROPS, roll=CAMCFG["roll_deg"])
shot("stage03_props_grips.png", MATCH_LOC, MATCH_T, res=(880, 860), ortho=CAMCFG["ortho_scale"], roll=CAMCFG["roll_deg"])
shot("match_crop_size_440x430.png", MATCH_LOC, MATCH_T, res=(440, 430), ortho=CAMCFG["ortho_scale"], roll=CAMCFG["roll_deg"])
shot("match_view_full_uncropped.png", MATCH_LOC, V((MATCH_T.x, MATCH_T.y, 3.2)), res=(1000, 1000), ortho=7.6, roll=CAMCFG["roll_deg"])   # same direction as the matching camera, scale 7.6 so nothing is cropped
# full body orthographic (anatomical names)
shot("full_front_ortho.png", orbit(T, 40, 0, 0), T, ortho=SC)
shot("full_back_ortho.png", orbit(T, 40, 180, 0), T, ortho=SC)
shot("full_right_profile_dumbbell_ortho.png", orbit(T, 40, -90, 0), T, ortho=SC)
shot("full_left_profile_bag_ortho.png", orbit(T, 40, 90, 0), T, ortho=SC)
shot("full_front34_right.png", orbit(T, 40, -35, 8), T, ortho=SC)
shot("full_front34_left.png", orbit(T, 40, 35, 8), T, ortho=SC)
shot("full_back34_right.png", orbit(T, 40, -145, 8), T, ortho=SC)
shot("full_back34_left.png", orbit(T, 40, 145, 8), T, ortho=SC)
shot("full_top_oblique.png", orbit(T, 40, 30, 52), T, ortho=SC)
# faces
HT = V((0, -.2, 5.3))
shot("face_front.png", orbit(HT, 20, 0, 2), HT, res=(900, 900), ortho=2.6)
shot("face_34.png", orbit(HT, 20, -32, 6), HT, res=(900, 900), ortho=2.6)
shot("face_profile_right.png", orbit(HT, 20, -90, 2), HT, res=(900, 900), ortho=2.6)
shot("face_profile_left.png", orbit(HT, 20, 90, 2), HT, res=(900, 900), ortho=2.6)
# neckline / armholes, back, shoulders / elbows / wrists
NT = V((0, -.4, 4.4))
shot("neckline_front.png", orbit(NT, 20, 0, 8), NT, res=(900, 900), ortho=3.8)
shot("neckline_back.png", orbit(NT, 20, 180, 8), NT, res=(900, 900), ortho=3.8, hide=("Dumbbell",))
shot("armhole_right.png", orbit(V((-1.5, 0, 4.4)), 20, -90, 10), V((-1.5, 0, 4.4)), res=(900, 900), ortho=3.2)
shot("armhole_left.png", orbit(V((1.5, 0, 4.4)), 20, 90, 10), V((1.5, 0, 4.4)), res=(900, 900), ortho=3.2)
shot("right_arm_side.png", orbit(V((-2.0, -.7, 3.9)), 20, -90, 4), V((-2.0, -.7, 3.9)), res=(900, 900), ortho=3.6)
shot("right_arm_top.png", orbit(V((-2.0, -.7, 3.9)), 20, -40, 70), V((-2.0, -.7, 3.9)), res=(900, 900), ortho=3.6)
shot("left_arm_front.png", orbit(V((2.2, 0, 3.6)), 20, 15, 5), V((2.2, 0, 3.6)), res=(900, 900), ortho=3.6)
shot("left_arm_side.png", orbit(V((2.2, 0, 3.6)), 20, 90, 5), V((2.2, 0, 3.6)), res=(900, 900), ortho=3.6)
# grips
GT = V((-1.72, -1.7, 3.3))
shot("grip_right_front.png", orbit(GT, 20, 0, 6), GT, res=(900, 900), ortho=3.4)
shot("grip_right_back.png", orbit(GT, 20, 180, 6), GT, res=(900, 900), ortho=3.4, hide=("UpperTorso", "LowerTorso", "Head", "RightUpperArm", "LeftUpperArm", "LeftLowerArm", "LeftHand", "GymBag"))
shot("grip_right_top.png", orbit(GT, 20, 0, 80), GT, res=(900, 900), ortho=3.4)
DT = V((-1.72, -1.78, 3.31))
shot("dumbbell_front_axis.png", orbit(DT, 20, 0, 6), DT, res=(900, 900), ortho=3.4, show_only=("Dumbbell",))
shot("dumbbell_end.png", orbit(DT, 20, -90, 6), DT, res=(900, 900), ortho=3.4, show_only=("Dumbbell",))
shot("dumbbell_34.png", orbit(DT, 20, -40, 24), DT, res=(900, 900), ortho=3.8, show_only=("Dumbbell",))
LT = V((2.23, -.17, 2.1))
shot("grip_left_front.png", orbit(LT, 20, 0, 6), LT, res=(900, 900), ortho=2.4)
shot("grip_left_back.png", orbit(LT, 20, 180, 6), LT, res=(900, 900), ortho=2.4, hide=("LowerTorso",))
BT = V((2.56, 0, 1.0))
shot("bag_front.png", orbit(BT, 20, 0, 4), BT, res=(900, 900), ortho=2.6, show_only=("GymBag",))
shot("bag_back.png", orbit(BT, 20, 180, 4), BT, res=(900, 900), ortho=2.6, show_only=("GymBag",))
shot("bag_top.png", orbit(BT, 20, 0, 85), BT, res=(900, 900), ortho=2.6, show_only=("GymBag",))
shot("bag_34.png", orbit(BT, 20, 35, 22), BT, res=(900, 900), ortho=2.8, show_only=("GymBag",))
# feet
FT_ = V((0, 0, .4))
shot("feet_front.png", orbit(FT_, 20, 0, 6), FT_, res=(900, 700), ortho=3.6, show_only=("RightFoot", "LeftFoot", "RightLowerLeg", "LeftLowerLeg"))
shot("foot_side_right.png", orbit(V((-.88, 0, .4)), 20, -90, 6), V((-.88, 0, .4)), res=(900, 700), ortho=3.2, show_only=("RightFoot", "RightLowerLeg"))
shot("feet_top.png", orbit(FT_, 20, 0, 88), FT_, res=(900, 700), ortho=3.6, show_only=("RightFoot", "LeftFoot"))
shot("feet_sole.png", orbit(FT_, 20, 0, -88), FT_, res=(900, 700), ortho=3.6, show_only=("RightFoot", "LeftFoot"))
shot("legs_front_ortho.png", orbit(V((0, 0, 1.4)), 20, 0, 0), V((0, 0, 1.4)), res=(900, 800), ortho=3.4, hide=("Dumbbell", "GymBag"))
print("ALL_RENDERS_DONE", len(RENDERED))
