
PREVIEW = "--preview" in sys.argv
if NORENDER:
    sys.exit(0)

# ----------------------------------------------------------------------------------------------
# cameras / light / render helpers (real Blender renders of the built scene)
# ----------------------------------------------------------------------------------------------
world = bpy.data.worlds.new("BD_World")
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
sun_d = bpy.data.lights.new("BD_Key", 'SUN')
sun_d.energy = 1.8
sun = bpy.data.objects.new("BD_Key", sun_d)
SCENE.collection.objects.link(sun)
sun.rotation_euler = (math.radians(52), math.radians(8), math.radians(-38))
fill_d = bpy.data.lights.new("BD_Fill", 'SUN')
fill_d.energy = 0.55
fill_d.use_shadow = False
fill = bpy.data.objects.new("BD_Fill", fill_d)
SCENE.collection.objects.link(fill)
fill.rotation_euler = (math.radians(60), 0, math.radians(140))
cam_d = bpy.data.cameras.new("BD_Cam")
CAM = bpy.data.objects.new("BD_Cam", cam_d)
SCENE.collection.objects.link(CAM)
SCENE.camera = CAM
SCENE.render.engine = 'BLENDER_EEVEE'
SCENE.eevee.taa_render_samples = 8 if QUICK else 32
SCENE.render.image_settings.file_format = 'PNG'
SCENE.view_settings.view_transform = 'Standard'
SCENE.render.film_transparent = False

FLATM = bpy.data.materials.new("BD_Flat")
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


# matching camera: orthographic, 385x425 crop frame of the reference (figure y13..y420 of 425 = 6.40 studs -> ortho scale 6.683, target H3.26), azimuth tuned to the reference turn
CAMCFG = {"type": "ORTHO", "target_h": 3.26, "azimuth_deg": -18.0, "elevation_deg": 5.0, "ortho_scale": 425.0 / 407.0 * 6.40, "res": [385, 425],
          "note": "reference crop 385x425 at x750..1135, y525..950 of the 1536x1024 sheet; 63.6 px per stud"}
if os.path.exists(os.path.join(HERE, "inputs", "camera_tuned.json")):
    CAMCFG.update(json.load(open(os.path.join(HERE, "inputs", "camera_tuned.json"))))
MT = V((0, 0, CAMCFG["target_h"]))
MATCH_LOC = orbit(MT, 40, CAMCFG["azimuth_deg"], CAMCFG["elevation_deg"])
json.dump(CAMCFG, open(os.path.join(OUT, "data", "camera.json"), "w"), indent=1)
K = 3
cam_d.shift_x = CAMCFG.get("shift_x", 0.0)
shot("match_view_%dx%d.png" % (CAMCFG["res"][0] * K, CAMCFG["res"][1] * K), MATCH_LOC, MT, res=(CAMCFG["res"][0] * K, CAMCFG["res"][1] * K), ortho=CAMCFG["ortho_scale"])
cam_d.shift_x = 0.0
if PREVIEW:
    T = V((0, 0, 3.25))
    shot("pv_front.png", orbit(T, 40, 0, 0), T, res=(700, 900), ortho=7.0)
    shot("pv_34R.png", orbit(T, 40, -35, 8), T, res=(700, 900), ortho=7.0)
    shot("pv_34L.png", orbit(T, 40, 35, 8), T, res=(700, 900), ortho=7.0)
    shot("pv_back.png", orbit(T, 40, 180, 0), T, res=(700, 900), ortho=7.0)
    shot("pv_Lside.png", orbit(T, 40, 90, 0), T, res=(700, 900), ortho=7.0)
    HT = V((0, -.2, 5.45))
    shot("pv_face.png", orbit(HT, 20, -10, 3), HT, res=(900, 900), ortho=3.0)
    sys.exit(0)

# ---- full review set: all main views at identical pixel height (700x900, ortho 7.0, same target) ----
T = V((0, 0, 3.25))
SC = 7.0
FULL = (700, 900)
shot("full_front.png", orbit(T, 40, 0, 0), T, res=FULL, ortho=SC)
shot("full_back.png", orbit(T, 40, 180, 0), T, res=FULL, ortho=SC)
shot("full_left_side.png", orbit(T, 40, 90, 0), T, res=FULL, ortho=SC)      # character's left (phone side)
shot("full_right_side.png", orbit(T, 40, -90, 0), T, res=FULL, ortho=SC)    # character's right (pocket side)
shot("full_front_left_34.png", orbit(T, 40, 35, 8), T, res=FULL, ortho=SC)
shot("full_front_right_34.png", orbit(T, 40, -35, 8), T, res=FULL, ortho=SC)
shot("full_top.png", orbit(T, 40, 20, 70), T, res=FULL, ortho=SC)
shot("full_low_angle.png", orbit(T, 40, -25, -22), T, res=FULL, ortho=SC)
# close-ups
HT = V((0, -.2, 5.45))
shot("close_face_front.png", orbit(HT, 20, 0, 3), HT, res=(900, 900), ortho=3.0)
shot("close_face_34_right.png", orbit(HT, 20, -30, 5), HT, res=(900, 900), ortho=3.0)
shot("close_face_34_left.png", orbit(HT, 20, 30, 5), HT, res=(900, 900), ortho=3.0)
shot("close_hair_top.png", orbit(HT, 20, 20, 55), HT, res=(900, 900), ortho=3.0)
shot("close_hair_back.png", orbit(HT, 20, 180, 10), HT, res=(900, 900), ortho=3.0)
shot("close_moustache.png", orbit(V((0, -1.1, 5.2)), 20, 0, 3), V((0, -1.1, 5.2)), res=(900, 900), ortho=1.6)
PT = V((2.35, -1.5, 4.55))
shot("close_phone_front.png", orbit(PT, 20, 0, 4), PT, res=(900, 900), ortho=2.8)
shot("close_phone_back_cameras.png", orbit(PT, 20, -20, 4), PT, res=(900, 900), ortho=2.8)
shot("close_phone_side.png", orbit(PT, 20, 90, 4), PT, res=(900, 900), ortho=2.8)
shot("close_phone_behind_screen.png", orbit(PT, 20, 180, 6), PT, res=(900, 900), ortho=2.8, hide=("Head", "UpperTorso"))
WT = V((2.15, -1.2, 3.95))
shot("close_watch_cuff.png", orbit(WT, 20, -10, 12), WT, res=(900, 900), ortho=2.4)
shot("close_watch_top.png", orbit(WT, 20, 20, 60), WT, res=(900, 900), ortho=2.4)
TT = V((0, -.6, 3.85))
shot("close_tie_bar.png", orbit(TT, 20, 0, 4), TT, res=(900, 900), ortho=2.6)
shot("close_pocket_square.png", orbit(V((1.25, -.7, 4.05)), 20, 0, 4), V((1.25, -.7, 4.05)), res=(900, 900), ortho=1.8)
shot("close_belt_buckle.png", orbit(V((0, -.7, 2.65)), 20, 0, 4), V((0, -.7, 2.65)), res=(900, 900), ortho=1.8)
RT = V((-1.55, -.5, 2.45))
shot("close_right_hand_pocket.png", orbit(RT, 20, -25, 8), RT, res=(900, 900), ortho=2.8)
shot("close_right_hand_front.png", orbit(RT, 20, 0, 4), RT, res=(900, 900), ortho=2.8)
shot("close_right_arm_side.png", orbit(V((-2.0, -.3, 3.5)), 20, -90, 4), V((-2.0, -.3, 3.5)), res=(900, 900), ortho=3.6)
FT_ = V((0, -.4, .45))
shot("close_shoes_front.png", orbit(FT_, 20, 0, 6), FT_, res=(900, 700), ortho=3.8, show_only=("RightFoot", "LeftFoot", "RightLowerLeg", "LeftLowerLeg"))
shot("close_shoes_34.png", orbit(FT_, 20, -35, 14), FT_, res=(900, 700), ortho=3.8, show_only=("RightFoot", "LeftFoot", "RightLowerLeg", "LeftLowerLeg"))
shot("close_shoes_top.png", orbit(FT_, 20, 0, 85), FT_, res=(900, 700), ortho=3.8, show_only=("RightFoot", "LeftFoot"))
shot("close_shoes_sole.png", orbit(FT_, 20, 0, -85), FT_, res=(900, 700), ortho=3.8, show_only=("RightFoot", "LeftFoot"))
shot("close_shoe_right_side.png", orbit(V((-.93, -.4, .45)), 20, -90, 4), V((-.93, -.4, .45)), res=(900, 700), ortho=3.0, show_only=("RightFoot", "RightLowerLeg"))
shot("close_shoe_left_side.png", orbit(V((.93, -.4, .45)), 20, 90, 4), V((.93, -.4, .45)), res=(900, 700), ortho=3.0, show_only=("LeftFoot", "LeftLowerLeg"))
shot("close_collar_neck_front.png", orbit(V((0, -.6, 4.75)), 20, 0, 6), V((0, -.6, 4.75)), res=(900, 900), ortho=2.6)
shot("close_jacket_back.png", orbit(V((0, 0.6, 3.6)), 20, 180, 4), V((0, .6, 3.6)), res=(900, 900), ortho=4.2)
print("ALL_RENDERS_DONE", len(RENDERED))
