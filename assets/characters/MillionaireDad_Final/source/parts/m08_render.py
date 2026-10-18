
PREVIEW = "--preview" in sys.argv
if NORENDER:
    sys.exit(0)

# ----------------------------------------------------------------------------------------------
# cameras / light / render helpers (real Blender renders of the built scene)
# ----------------------------------------------------------------------------------------------
world = bpy.data.worlds.new("MD_World")
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
sun_d = bpy.data.lights.new("MD_Key", 'SUN')
sun_d.energy = 1.8
sun = bpy.data.objects.new("MD_Key", sun_d)
SCENE.collection.objects.link(sun)
sun.rotation_euler = (math.radians(52), math.radians(8), math.radians(-38))
fill_d = bpy.data.lights.new("MD_Fill", 'SUN')
fill_d.energy = 0.55
fill_d.use_shadow = False
fill = bpy.data.objects.new("MD_Fill", fill_d)
SCENE.collection.objects.link(fill)
fill.rotation_euler = (math.radians(60), 0, math.radians(140))
cam_d = bpy.data.cameras.new("MD_Cam")
CAM = bpy.data.objects.new("MD_Cam", cam_d)
SCENE.collection.objects.link(CAM)
SCENE.camera = CAM
SCENE.render.engine = 'BLENDER_EEVEE'
SCENE.eevee.taa_render_samples = 8 if QUICK else 32
SCENE.render.image_settings.file_format = 'PNG'
SCENE.view_settings.view_transform = 'Standard'
SCENE.render.film_transparent = False

FLATM = bpy.data.materials.new("MD_Flat")
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


# matching camera: orthographic, 422x425 frame = the unaltered crop (figure y5..413 of 425 = 6.40 studs PROJECT CONVENTION -> ortho scale 6.667, target H3.15);
# azimuth / elevation / x shift are fitted to the crop silhouette by scripts/fit_camera.py and read from inputs/camera_tuned.json
CAMCFG = {"type": "ORTHO", "target_h": 3.15, "azimuth_deg": 28.0, "elevation_deg": 3.0, "ortho_scale": 425.0 / 408.0 * 6.40, "res": [422, 425], "shift_x": 0.0,
          "note": "crop of the sheet at x1110..1532, y530..955; 63.75 px per stud at the 6.40 convention"}
if os.path.exists(os.path.join(HERE, "inputs", "camera_tuned.json")):
    CAMCFG.update(json.load(open(os.path.join(HERE, "inputs", "camera_tuned.json"))))
MT = V((0, 0, CAMCFG["target_h"]))
MATCH_LOC = orbit(MT, 40, CAMCFG["azimuth_deg"], CAMCFG["elevation_deg"])
json.dump(CAMCFG, open(os.path.join(OUT, "data", "camera.json"), "w"), indent=1)
K = 3
cam_d.shift_x = CAMCFG.get("shift_x", 0.0)
shot("match_view_%dx%d.png" % (CAMCFG["res"][0] * K, CAMCFG["res"][1] * K), MATCH_LOC, MT, res=(CAMCFG["res"][0] * K, CAMCFG["res"][1] * K), ortho=CAMCFG["ortho_scale"])
cam_d.shift_x = 0.0
T = V((0, 0, 3.2))
SC = 7.0
FULL = (700, 900)
if PREVIEW:
    shot("pv_front.png", orbit(T, 40, 0, 0), T, res=FULL, ortho=SC)
    shot("pv_34L.png", orbit(T, 40, 35, 8), T, res=FULL, ortho=SC)
    shot("pv_34R.png", orbit(T, 40, -35, 8), T, res=FULL, ortho=SC)
    shot("pv_back.png", orbit(T, 40, 180, 0), T, res=FULL, ortho=SC)
    shot("pv_Rside.png", orbit(T, 40, -90, 0), T, res=FULL, ortho=SC)
    HT = V((0, -.2, 5.35))
    shot("pv_face.png", orbit(HT, 20, 20, 3), HT, res=(900, 900), ortho=3.4)
    sys.exit(0)
# ---- technical views of the SAME built mesh: identical pixel height (700x900, ortho 7.0, target H3.2, camera distance 40) ----
shot("full_front.png", orbit(T, 40, 0, 0), T, res=FULL, ortho=SC)
shot("full_back.png", orbit(T, 40, 180, 0), T, res=FULL, ortho=SC)
shot("full_right_side.png", orbit(T, 40, -90, 0), T, res=FULL, ortho=SC)      # anatomical right (case side)
shot("full_left_side.png", orbit(T, 40, 90, 0), T, res=FULL, ortho=SC)        # anatomical left (watch side)
shot("full_front_left_34.png", orbit(T, 40, 35, 8), T, res=FULL, ortho=SC)
shot("full_front_right_34.png", orbit(T, 40, -35, 8), T, res=FULL, ortho=SC)
shot("full_top.png", orbit(T, 40, 20, 70), T, res=FULL, ortho=SC)
shot("full_low_angle.png", orbit(T, 40, -25, -22), T, res=FULL, ortho=SC)
# close-ups
HT = V((0, -.2, 5.35))
shot("close_face_front.png", orbit(HT, 20, 0, 3), HT, res=(900, 900), ortho=3.4)
shot("close_face_34_left.png", orbit(HT, 20, 30, 5), HT, res=(900, 900), ortho=3.4)
shot("close_face_34_right.png", orbit(HT, 20, -30, 5), HT, res=(900, 900), ortho=3.4)
shot("close_face_profile_left.png", orbit(HT, 20, 90, 3), HT, res=(900, 900), ortho=3.4)
shot("close_face_profile_right.png", orbit(HT, 20, -90, 3), HT, res=(900, 900), ortho=3.4)
shot("close_hair_top.png", orbit(HT, 20, 20, 55), HT, res=(900, 900), ortho=3.4)
shot("close_hair_back.png", orbit(HT, 20, 180, 10), HT, res=(900, 900), ortho=3.4)
shot("close_glasses_moustache.png", orbit(V((0, -1.1, 5.1)), 20, 0, 3), V((0, -1.1, 5.1)), res=(900, 900), ortho=2.4)
shot("close_grin.png", orbit(V((0, -1.0, 4.75)), 20, 0, 3), V((0, -1.0, 4.75)), res=(900, 900), ortho=1.8)
CT = V((-2.0, -.2, 1.5))
shot("close_case_front.png", orbit(CT, 20, 0, 4), CT, res=(900, 900), ortho=3.6)
shot("close_case_side_outer.png", orbit(CT, 20, -90, 4), CT, res=(900, 900), ortho=3.6)
shot("close_case_34.png", orbit(CT, 20, -35, 14), CT, res=(900, 900), ortho=3.6)
shot("close_case_back.png", orbit(CT, 20, 180, 6), CT, res=(900, 900), ortho=3.6)
GT = V((-2.0, -.25, 2.2))
shot("close_grip_front.png", orbit(GT, 20, 0, 6), GT, res=(900, 900), ortho=2.2)
shot("close_grip_outer.png", orbit(GT, 20, -90, 6), GT, res=(900, 900), ortho=2.2)
shot("close_grip_top.png", orbit(GT, 20, 0, 80), GT, res=(900, 900), ortho=2.2)
WT = V((1.85, -.45, 2.75))
shot("close_watch_outer.png", orbit(WT, 20, 60, 8), WT, res=(900, 900), ortho=2.0)
shot("close_watch_front.png", orbit(WT, 20, 20, 8), WT, res=(900, 900), ortho=2.0)
shot("close_left_hand_hip.png", orbit(V((1.7, -.5, 2.6)), 20, 0, 4), V((1.7, -.5, 2.6)), res=(900, 900), ortho=2.6)
shot("close_belt_buckle.png", orbit(V((0, -.8, 2.67)), 20, 0, 4), V((0, -.8, 2.67)), res=(900, 900), ortho=1.8)
shot("close_chest_buttons_square.png", orbit(V((0.5, -.8, 3.7)), 20, 0, 4), V((0.5, -.8, 3.7)), res=(900, 900), ortho=3.0)
FT_ = V((0, -.4, .5))
shot("close_shoes_front.png", orbit(FT_, 20, 0, 6), FT_, res=(900, 700), ortho=3.8, show_only=("RightFoot", "LeftFoot", "RightLowerLeg", "LeftLowerLeg"))
shot("close_shoes_34.png", orbit(FT_, 20, -35, 14), FT_, res=(900, 700), ortho=3.8, show_only=("RightFoot", "LeftFoot", "RightLowerLeg", "LeftLowerLeg"))
shot("close_shoes_top.png", orbit(FT_, 20, 0, 85), FT_, res=(900, 700), ortho=3.8, show_only=("RightFoot", "LeftFoot"))
shot("close_shoes_sole.png", orbit(FT_, 20, 0, -85), FT_, res=(900, 700), ortho=3.8, show_only=("RightFoot", "LeftFoot"))
shot("close_jacket_back.png", orbit(V((0, 0.6, 3.6)), 20, 180, 4), V((0, .6, 3.6)), res=(900, 900), ortho=4.4)
print("ALL_RENDERS_DONE", len(RENDERED))
