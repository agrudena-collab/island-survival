

# ----------------------------------------------------------------------------------------------
# cameras / light / renders (real Blender renders; the cameras are stored in data/cameras.json)
# ----------------------------------------------------------------------------------------------
if NORENDER:
    sys.exit(0)
world = bpy.data.worlds.new("GD_World")
SCENE.world = world
world.use_nodes = True
_wn = world.node_tree.nodes
_wl = world.node_tree.links
_bg_a = _wn["Background"]
_bg_a.inputs[0].default_value = (0.90, 0.88, 0.84, 1.0)
_bg_a.inputs[1].default_value = 0.66
_bg_b = _wn.new("ShaderNodeBackground")
_bg_b.inputs[0].default_value = (0.93, 0.91, 0.88, 1.0)
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
SCENE.eevee.taa_render_samples = 8 if QUICK else 48
SCENE.render.image_settings.file_format = 'PNG'
SCENE.view_settings.view_transform = 'Standard'
SCENE.render.film_transparent = False
CAMS = []
RENDERED = []


def cam_look(loc, target, lens=70.0, ortho=None):
    CAM.location = V(loc)
    CAM.rotation_euler = (V(target) - V(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.sensor_width = 36.0
    cam_d.sensor_fit = 'AUTO'
    if ortho:
        cam_d.type, cam_d.ortho_scale = 'ORTHO', ortho
    else:
        cam_d.type, cam_d.lens = 'PERSP', lens


def orbit(target, dist, az_deg, el_deg):
    az, el = math.radians(az_deg), math.radians(el_deg)
    t = V(target)
    return t + V((dist * math.sin(az) * math.cos(el), -dist * math.cos(az) * math.cos(el), dist * math.sin(el)))


def shot(name, loc, target, res=(1000, 1000), lens=70.0, ortho=None, show_only=None, hide=None):
    for pm in PARTS.values():
        hid = (show_only is not None and pm.runtime not in show_only) or (hide is not None and pm.runtime in hide)
        pm.obj.hide_render = hid
    SCENE.render.resolution_x, SCENE.render.resolution_y = res
    cam_look(loc, target, lens, ortho)
    SCENE.render.filepath = os.path.join(OUT, "renders", name)
    bpy.ops.render.render(write_still=True)
    RENDERED.append(name)
    CAMS.append({"name": name, "location": [round(c, 4) for c in CAM.location], "target": [round(c, 4) for c in target], "type": "ORTHO" if ortho else "PERSP", "ortho_scale": ortho, "lens_mm": None if ortho else lens, "resolution": list(res)})
    print("RENDERED", name)


FULL = V((0.0, -0.10, 3.20))
FS = 7.15
if QUICK:
    SZ = (800, 800)
else:
    SZ = (1600, 1600)
shot("01_matching_front.png", orbit(FULL, 30, 0, 7), FULL, res=SZ, ortho=FS)
shot("02_front.png", orbit(FULL, 30, 0, 4), FULL, res=SZ, ortho=FS)
shot("03_back.png", orbit(FULL, 30, 180, 4), FULL, res=SZ, ortho=FS)
shot("04_profile_right.png", orbit(FULL, 30, -90, 4), FULL, res=SZ, ortho=FS)
shot("05_profile_left.png", orbit(FULL, 30, 90, 4), FULL, res=SZ, ortho=FS)
shot("06_front_q34.png", orbit(FULL, 30, -35, 9), FULL, res=SZ, ortho=FS)
shot("07_rear_q34.png", orbit(FULL, 30, 145, 9), FULL, res=SZ, ortho=FS)
DS = (1200, 1200) if not QUICK else (600, 600)
HT = V((0, -0.3, 5.25))
shot("08_face_front.png", orbit(HT, 14, 0, 2), HT, res=DS, ortho=3.2)
shot("09_face_profile_right.png", orbit(HT, 14, -90, 2), HT, res=DS, ortho=3.2)
shot("09b_face_q34.png", orbit(HT, 14, -32, 8), HT, res=DS, ortho=3.2)
shot("08c_head_top.png", orbit(HT, 14, -20, 70), HT, res=DS, ortho=3.2)
shot("08d_head_back.png", orbit(HT, 14, 180, 10), HT, res=DS, ortho=3.2)
BT = V((0, -0.55, 4.75))
shot("10_beard_below.png", orbit(BT, 14, -15, -42), BT, res=DS, ortho=3.0)
shot("10b_beard_side.png", orbit(BT, 14, -90, 3), BT, res=DS, ortho=3.0)
for sd, sx in (("R", -1), ("L", 1)):
    ST = JV[("Right" if sx < 0 else "Left") + "Shoulder"]
    ET = JV[("Right" if sx < 0 else "Left") + "Elbow"]
    shot("11_shoulder_%s.png" % sd, orbit(ST, 14, sx * 40, 12), ST, res=DS, ortho=2.8)
    shot("12_elbow_%s_outer.png" % sd, orbit(ET, 14, sx * 90, 6), ET, res=DS, ortho=2.8)
    shot("12_elbow_%s_front.png" % sd, orbit(ET, 14, 0, 8), ET, res=DS, ortho=2.8)
    shot("12_elbow_%s_back.png" % sd, orbit(ET, 14, 180, 8), ET, res=DS, ortho=2.8)
    shot("12_elbow_%s_top.png" % sd, orbit(ET, 14, sx * 30, 72), ET, res=DS, ortho=2.8)
    shot("12_elbow_%s_bottom.png" % sd, orbit(ET, 14, sx * 30, -60), ET, res=DS, ortho=2.8)
GT = V((-2.05, -1.1, 3.75))
shot("13_grip_front.png", orbit(GT, 10, 0, 6), GT, res=DS, ortho=2.8)
shot("13b_grip_side_inner.png", orbit(GT, 10, 90, 6), GT, res=DS, ortho=2.8)
shot("13c_grip_back.png", orbit(GT, 10, 180, 6), GT, res=DS, ortho=2.8)
shot("13d_grip_top.png", orbit(GT, 10, 0, 80), GT, res=DS, ortho=2.8)
LT = V((1.95, -0.1, 2.4))
shot("14_left_hand.png", orbit(LT, 10, 30, 8), LT, res=DS, ortho=2.8)
SH = V((0, -0.2, 0.7))
shot("15_shoes.png", orbit(SH, 10, 25, 14), SH, res=DS, ortho=4.2)
shot("15b_pelvis_front.png", orbit(V((0, -0.1, 2.0)), 14, 0, 4), V((0, -0.1, 2.0)), res=DS, ortho=4.2)
shot("15c_pelvis_back.png", orbit(V((0, -0.1, 2.0)), 14, 180, 4), V((0, -0.1, 2.0)), res=DS, ortho=4.2)
CT = V((CAN_C.x, CAN_C.y, 3.86))
shot("16_can_front.png", orbit(CT, 10, 0, 4), CT, res=DS, ortho=2.0, show_only=("EnergyCan",))
shot("16b_can_back.png", orbit(CT, 10, 180, 4), CT, res=DS, ortho=2.0, show_only=("EnergyCan",))
shot("16c_can_top.png", orbit(CT, 10, 0, 80), CT, res=DS, ortho=1.2, show_only=("EnergyCan",))
shot("16d_can_bottom.png", orbit(CT, 10, 0, -70), CT, res=DS, ortho=1.2, show_only=("EnergyCan",))
for pm in PARTS.values():
    pm.obj.hide_render = False
json.dump(CAMS, open(os.path.join(OUT, "data", "cameras.json"), "w"), indent=1)
print("ALL_RENDERS_DONE", len(RENDERED))
