# Procedural R15 low-poly builder for the Regular Dad family NPCs (wife = variant A, son = variant B).
# Run: blender -b --factory-startup --python build_family.py -- <wife|son> <outdir> [--norender]
# Output: <outdir>/<Name>_R15.fbx (armature + 15 meshes, vertex colours, rigid 100% weights), <Name>.blend, renders/*.png, data/<Name>_spec.json
# Blender coordinates: X = character's left, -Y = forward, Z = up; Roblox model position = (-x, z, y).
import bpy, bmesh, math, sys, os, json, random
from mathutils import Vector as V, Matrix

args = sys.argv[sys.argv.index("--") + 1:]
WHO, OUT = args[0], os.path.abspath(args[1])
NORENDER = "--norender" in args
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)


def lin(h):
    c = [int(h[i:i + 2], 16) / 255.0 for i in (1, 3, 5)]
    f = lambda x: x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), 1.0)


# ----------------------------------------------------------------------------------------------------------------
# palettes and proportions
# ----------------------------------------------------------------------------------------------------------------
SKIN = "#E8B48C"
SKIN_D = "#D29F78"
NOSE = "#D8A07E"
if WHO == "wife":
    NAME = "RegularMom"
    C = dict(top="#C23B6A", top_d="#A8305A", apron="#F1E6C8", apron_d="#DCCB9C", pants="#4C79AE", cuff="#3F6697", shoe="#EE8FAE",
             sole="#C9627F", hair="#6B3E26", hair_hi="#86542F", wood="#8A5A3A", metal="#C4CCD6", metal_d="#9AA4AE")
    P = dict(hip=2.55, knee=1.40, ankle=0.30, waist=3.10, neck=4.30, head_h=1.95, head_w=2.15, head_d=2.0, tw=2.6, td=1.55, hw=2.3,
             arm=0.86, leg=1.02, sho_x=1.55, hip_x=0.62, hand=(0.92, 0.80, 0.86))
    SLEEVE_FRAC = 0.50          # 3/4 sleeve: the sleeve covers the upper arm and half of the forearm
else:
    NAME = "RegularSon"
    C = dict(top="#D64545", top_d="#B93A3A", pants="#2F3F66", cuff="#273556", shoe="#F3F3F3", sole="#D64545", hair="#6A4326", hair_hi="#835733",
             pack="#23304F", pack_hi="#33466F", frame="#2A2A33", lunch="#F2C230", lunch_d="#B98E10", string="#F4F4F4")
    P = dict(hip=1.90, knee=1.05, ankle=0.28, waist=2.35, neck=3.35, head_h=2.0, head_w=2.25, head_d=2.05, tw=2.3, td=1.40, hw=2.05,
             arm=0.78, leg=0.92, sho_x=1.38, hip_x=0.55, hand=(0.86, 0.74, 0.80))
    SLEEVE_FRAC = 1.0           # long sleeves down to the cuff
HEAD_TOP = P["neck"] + P["head_h"]
SH_Z = P["neck"] - 0.22
UA = (SH_Z - (P["neck"] - 0.22 - (P["neck"] - P["waist"]) * 0.92)) if False else None
ARM_LEN = (P["neck"] - P["waist"]) * 0.95          # shoulder to wrist hangs about to the hip joint level
UA_L, LA_L = ARM_LEN * 0.52, ARM_LEN * 0.48
EL_Z = SH_Z - UA_L
WR_Z = EL_Z - LA_L
HAND_L = 0.70

# ----------------------------------------------------------------------------------------------------------------
# geometry helpers (pure python lists -> one mesh per R15 part)
# ----------------------------------------------------------------------------------------------------------------
class PM:
    def __init__(self, name, joint):
        self.name, self.joint = name, V(joint)
        self.verts, self.polys, self.cols = [], [], []

    def add(self, vs, fs, hexc):
        base = len(self.verts)
        self.verts += [V(v) for v in vs]
        for f in fs:
            self.polys.append(tuple(base + i for i in f))
            self.cols.append(lin(hexc))

    def tris(self):
        return sum(len(p) - 2 for p in self.polys)


def bm_out(bm, xf, center):
    bmesh.ops.transform(bm, matrix=xf, verts=bm.verts)
    bmesh.ops.translate(bm, vec=center, verts=bm.verts)
    vs = [v.co.copy() for v in bm.verts]
    idx = {v: i for i, v in enumerate(bm.verts)}
    fs = [[idx[v] for v in f.verts] for f in bm.faces]
    bm.free()
    return vs, fs


def box(pm, c, s, col, bev=0.12, rot=(0, 0, 0), taper=None):
    """Chamfered box centred at c with size s=(x,y,z). taper=(bottom_scale, top_scale) in x and y."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        t = v.co.z + 0.5
        k = 1.0 if taper is None else taper[0] + (taper[1] - taper[0]) * t
        v.co = V((v.co.x * s[0] * k, v.co.y * s[1] * k, v.co.z * s[2]))
    b = min(bev, 0.45 * min(s))
    if b > 0.004:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=b, offset_type='OFFSET', segments=1, profile=0.5, affect='EDGES')
    xf = Matrix.Rotation(math.radians(rot[2]), 4, 'Z') @ Matrix.Rotation(math.radians(rot[1]), 4, 'Y') @ Matrix.Rotation(math.radians(rot[0]), 4, 'X')
    vs, fs = bm_out(bm, xf, V(c))
    pm.add(vs, fs, col)


def lump(pm, c, r, col, seed=0, squash=(1, 1, 1), jit=0.14):
    """Faceted low-poly lump (icosphere, jittered)."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    for v in bm.verts:
        v.co = V((v.co.x * r * squash[0] * (1 + rnd.uniform(-jit, jit)), v.co.y * r * squash[1] * (1 + rnd.uniform(-jit, jit)),
                  v.co.z * r * squash[2] * (1 + rnd.uniform(-jit, jit))))
    vs, fs = bm_out(bm, Matrix.Identity(4), V(c))
    pm.add(vs, fs, col)


# ----------------------------------------------------------------------------------------------------------------
# joints
# ----------------------------------------------------------------------------------------------------------------
JV = {"Root": V((0, 0, P["hip"])), "Waist": V((0, 0, P["waist"])), "Neck": V((0, 0, P["neck"]))}
for side, s in (("Right", -1), ("Left", 1)):
    JV[side + "Shoulder"] = V((s * P["sho_x"], 0, SH_Z))
    JV[side + "Elbow"] = V((s * P["sho_x"], 0, EL_Z))
    JV[side + "Wrist"] = V((s * P["sho_x"], 0, WR_Z))
    JV[side + "Hip"] = V((s * P["hip_x"], 0, P["hip"]))
    JV[side + "Knee"] = V((s * P["hip_x"], 0, P["knee"]))
    JV[side + "Ankle"] = V((s * P["hip_x"], 0, P["ankle"]))
PARTS = {}


def part(name, joint):
    PARTS[name] = PM(name, joint)
    return PARTS[name]


# ----------------------------------------------------------------------------------------------------------------
# body parts (absolute coordinates, converted to joint-local at the end)
# ----------------------------------------------------------------------------------------------------------------
fy = -P["td"] / 2                                       # front face of the torso
ut_h = P["neck"] - P["waist"]
lt_h = P["waist"] - (P["hip"] - 0.30)

lt = part("LowerTorso", JV["Root"])
box(lt, (0, 0, P["hip"] - 0.30 + lt_h / 2), (P["hw"], P["td"] * 0.96, lt_h), C["top"] if WHO == "wife" else C["top"], bev=0.18)
ut = part("UpperTorso", JV["Waist"])
box(ut, (0, 0, P["waist"] + ut_h / 2), (P["tw"], P["td"], ut_h), C["top"], bev=0.22, taper=(0.90, 1.0))
box(ut, (0, 0, P["neck"] + 0.05), (0.80, 0.78, 0.34), SKIN_D, bev=0.06)

if WHO == "wife":
    # apron: bib over the chest, skirt over the hips, pocket, straps, waist tie
    box(lt, (0, fy - 0.03, P["hip"] - 0.30 + lt_h / 2 - 0.02), (P["hw"] - 0.25, 0.10, lt_h + 0.06), C["apron"], bev=0.03)
    box(lt, (0, fy - 0.09, P["hip"] - 0.30 + lt_h / 2 - 0.05), (1.05, 0.08, 0.50), C["apron_d"], bev=0.03)
    box(ut, (0, fy - 0.03, P["waist"] + ut_h * 0.40), (1.75, 0.10, ut_h * 0.82), C["apron"], bev=0.03)
    for sx in (-0.62, 0.62):
        box(ut, (sx, fy - 0.03, P["neck"] - 0.30), (0.26, 0.10, 0.70), C["apron"], bev=0.03)
    box(ut, (0, fy - 0.07, P["waist"] + 0.04), (P["tw"] * 0.92, 0.10, 0.12), C["apron_d"], bev=0.02)
else:
    # hoodie: hood collar behind the neck, kangaroo pocket on the lower torso, two strings, backpack and its straps
    box(ut, (0, 0.32, P["neck"] - 0.18), (1.55, 0.70, 0.40), C["top_d"], bev=0.10)
    box(lt, (0, fy - 0.03, P["hip"] - 0.30 + lt_h / 2 - 0.02), (P["hw"] - 0.35, 0.10, lt_h * 0.9), C["top_d"], bev=0.03)
    for sx in (-0.26, 0.26):
        box(ut, (sx, fy - 0.04, P["neck"] - 0.70), (0.08, 0.08, 0.70), C["string"], bev=0.01)
    for sx in (-0.62, 0.62):
        box(ut, (sx, fy - 0.04, P["waist"] + ut_h * 0.5), (0.24, 0.09, ut_h * 0.98), C["pack"], bev=0.03)
    box(ut, (0, P["td"] / 2 + 0.38, P["waist"] + ut_h * 0.50), (1.95, 0.76, ut_h * 1.05), C["pack"], bev=0.16)
    box(ut, (0, P["td"] / 2 + 0.80, P["waist"] + ut_h * 0.28), (1.35, 0.14, 0.50), C["pack_hi"], bev=0.04)

# head
hz = P["neck"] + P["head_h"] / 2
hw, hd, hh = P["head_w"], P["head_d"], P["head_h"]
head = part("Head", JV["Neck"])
box(head, (0, 0, hz), (hw, hd, hh), SKIN, bev=0.20)
for sx in (-1, 1):
    box(head, (sx * (hw / 2 + 0.05), 0.05, hz - 0.12), (0.16, 0.30, 0.46), SKIN_D, bev=0.04)
front = -hd / 2
for sx in (-1, 1):
    ex = sx * 0.34
    box(head, (ex, front - 0.01, hz + 0.08), (0.44, 0.08, 0.42), "#FFFFFF", bev=0.04)
    box(head, (ex, front - 0.05, hz + 0.05), (0.20, 0.08, 0.28), "#1E1714", bev=0.04)
    box(head, (ex, front - 0.04, hz + 0.42), (0.56, 0.10, 0.15), C["hair"], bev=0.04, rot=(0, 7 * sx, 0))
box(head, (0, front - 0.14, hz - 0.14), (0.42, 0.34, 0.46), NOSE, bev=0.10)
mw = 0.90 if WHO == "wife" else 0.80
box(head, (0, front - 0.01, hz - 0.60), (mw, 0.08, 0.17), "#7A2F2A", bev=0.04)           # smile: dark mouth + raised corners + lower lip
for sx in (-1, 1):
    box(head, (sx * (mw / 2 + 0.05), front - 0.01, hz - 0.50), (0.15, 0.08, 0.20), "#7A2F2A", bev=0.03)
box(head, (0, front - 0.01, hz - 0.75), (mw * 0.55, 0.07, 0.09), SKIN_D, bev=0.02)
if WHO == "wife":
    # hair: faceted cap + bangs + side locks + back + bun
    HC, HH = C["hair"], C["hair_hi"]
    box(head, (0, 0.02, hz + hh / 2 - 0.12), (hw + 0.14, hd + 0.12, 0.62), HC, bev=0.16)
    for i, bx in enumerate((-0.78, -0.40, 0.0, 0.40, 0.78)):
        box(head, (bx, front - 0.02, hz + 0.66 - (0.03 if i % 2 else 0.0)), (0.46, 0.22, 0.30 + (0.06 if i % 2 else 0)), HC, bev=0.06)
    for sx in (-1, 1):
        box(head, (sx * (hw / 2 + 0.05), 0.20, hz + 0.20), (0.24, 1.15, 1.10), HC, bev=0.08)
    box(head, (0, hd / 2 - 0.12, hz + 0.30), (hw + 0.10, 0.42, 1.30), HC, bev=0.10)
    box(head, (-0.35, front + 0.05, hz + hh / 2 + 0.08), (0.80, 0.34, 0.20), HH, bev=0.06)
    lump(head, (0, 0.20, hz + hh / 2 + 0.28), 0.50, HC, seed=3, squash=(1.0, 1.0, 0.85))
    lump(head, (-0.14, 0.10, hz + hh / 2 + 0.44), 0.26, HH, seed=5)
else:
    HC, HH = C["hair"], C["hair_hi"]
    pts = [(-0.70, -0.45, 0.55), (0.0, -0.55, 0.70), (0.70, -0.45, 0.55), (-0.95, 0.15, 0.35), (0.95, 0.15, 0.35), (-0.45, 0.45, 0.55),
           (0.45, 0.45, 0.55), (0.0, 0.05, 0.85), (-0.95, -0.25, 0.05), (0.95, -0.25, 0.05)]
    for i, (px, py, pz) in enumerate(pts):
        lump(head, (px, py, hz + hh / 2 + pz * 0.55 - 0.30), 0.48 + 0.05 * (i % 3), HC if i % 2 else HH, seed=10 + i)
    # round glasses: four bars per lens + bridge
    for sx in (-1, 1):
        gx = sx * 0.40
        gz = hz + 0.04
        box(head, (gx, front - 0.07, gz + 0.34), (0.74, 0.09, 0.09), C["frame"], bev=0.02)
        box(head, (gx, front - 0.07, gz - 0.30), (0.74, 0.09, 0.09), C["frame"], bev=0.02)
        box(head, (gx - sx * 0.33, front - 0.07, gz + 0.02), (0.09, 0.09, 0.70), C["frame"], bev=0.02)
        box(head, (gx + sx * 0.33, front - 0.07, gz + 0.02), (0.09, 0.09, 0.70), C["frame"], bev=0.02)
    box(head, (0, front - 0.07, hz + 0.06), (0.14, 0.09, 0.09), C["frame"], bev=0.02)

# arms and legs
SLEEVE = C["top"]
for side, s in (("Right", -1), ("Left", 1)):
    sx = s * P["sho_x"]
    ua = part(side + "UpperArm", JV[side + "Shoulder"])
    box(ua, (sx, 0, SH_Z - UA_L / 2 + 0.05), (P["arm"] + 0.04, P["arm"] + 0.04, UA_L + 0.18), SLEEVE, bev=0.20)
    la = part(side + "LowerArm", JV[side + "Elbow"])
    sl = LA_L * SLEEVE_FRAC
    box(la, (sx, 0, EL_Z - sl / 2 + 0.04), (P["arm"], P["arm"], sl + 0.10), SLEEVE, bev=0.14)
    if SLEEVE_FRAC < 0.99:
        box(la, (sx, 0, EL_Z - sl - 0.03), (P["arm"] + 0.03, P["arm"] + 0.03, 0.14), C["top_d"], bev=0.03)
        box(la, (sx, 0, (EL_Z - sl + WR_Z) / 2 - 0.02), (P["arm"] - 0.10, P["arm"] - 0.10, EL_Z - sl - WR_Z + 0.04), SKIN, bev=0.10)
    else:
        box(la, (sx, 0, WR_Z + 0.12), (P["arm"] + 0.03, P["arm"] + 0.03, 0.26), C["top_d"], bev=0.04)
    hnd = part(side + "Hand", JV[side + "Wrist"])
    hx, hy, hzz = P["hand"]
    box(hnd, (sx, -0.02, WR_Z - 0.30), (hx, hy, hzz), SKIN, bev=0.22)
    if side == "Right" and WHO == "wife":      # ladle: wooden handle through the fist, steel bowl below
        box(hnd, (sx, -0.04, WR_Z - 0.55), (0.12, 0.12, 2.0), C["wood"], bev=0.02)
        box(hnd, (sx, -0.04, WR_Z - 1.52), (0.70, 0.62, 0.30), C["metal"], bev=0.10)
        box(hnd, (sx, -0.04, WR_Z - 1.40), (0.50, 0.44, 0.12), C["metal_d"], bev=0.04)
    if side == "Right" and WHO == "son":       # lunchbox: yellow case on a short handle under the fist
        box(hnd, (sx, -0.04, WR_Z - 0.86), (0.12, 0.12, 0.34), C["lunch_d"], bev=0.02)
        box(hnd, (sx, -0.04, WR_Z - 1.50), (1.00, 0.46, 0.84), C["lunch"], bev=0.10)
        box(hnd, (sx, -0.28, WR_Z - 1.40), (0.20, 0.06, 0.20), C["lunch_d"], bev=0.02)
    ul = part(side + "UpperLeg", JV[side + "Hip"])
    lx = s * P["hip_x"]
    box(ul, (lx, 0, (P["hip"] + P["knee"]) / 2 - 0.02), (P["leg"] + 0.02, P["leg"] + 0.10, P["hip"] - P["knee"] + 0.14), C["pants"], bev=0.16)
    ll = part(side + "LowerLeg", JV[side + "Knee"])
    box(ll, (lx, 0, (P["knee"] + P["ankle"]) / 2 + 0.06), (P["leg"] - 0.04, P["leg"] + 0.04, P["knee"] - P["ankle"] + 0.18), C["pants"], bev=0.14)
    box(ll, (lx, 0, P["ankle"] + 0.30), (P["leg"] + 0.05, P["leg"] + 0.12, 0.16), C["cuff"], bev=0.03)
    ft = part(side + "Foot", JV[side + "Ankle"])
    box(ft, (lx, -0.30, 0.30), (P["leg"] + 0.06, 1.75, 0.56), C["shoe"], bev=0.16)
    box(ft, (lx, -0.30, 0.06), (P["leg"] + 0.07, 1.77, 0.12), C["sole"], bev=0.03)

# ----------------------------------------------------------------------------------------------------------------
# scene objects
# ----------------------------------------------------------------------------------------------------------------
# overall stature: the wife is a little shorter than the father (6.4 with hair), the son clearly shorter (~10-12 years)
SC = 0.93 if WHO == "wife" else 0.82
for pm in PARTS.values():
    pm.verts = [v * SC for v in pm.verts]
    pm.joint = pm.joint * SC
for k in JV:
    JV[k] = JV[k] * SC
HEAD_TOP *= SC
HAND_L *= SC

EXP = bpy.data.collections.new("EXPORT_" + NAME)
bpy.context.scene.collection.children.link(EXP)
for pm in PARTS.values():
    vs = [v - pm.joint for v in pm.verts]
    me = bpy.data.meshes.new(pm.name + "_mesh")
    me.from_pydata([tuple(v) for v in vs], [], pm.polys)
    me.update()
    ca = me.color_attributes.new(name="Col", type="BYTE_COLOR", domain="CORNER")
    li = 0
    for pi, p in enumerate(me.polygons):
        for _ in range(p.loop_total):
            ca.data[li].color = pm.cols[pi]
            li += 1
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new(pm.name, me)
    ob.location = pm.joint
    EXP.objects.link(ob)
    pm.obj = ob

# armature: same hierarchy as the dads (Root > HumanoidRootNode > LowerTorso ...)
adata = bpy.data.armatures.new(NAME + "_Armature")
ARM = bpy.data.objects.new(NAME + "_Armature", adata)
EXP.objects.link(ARM)
bpy.context.view_layer.objects.active = ARM
ARM.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
eb = adata.edit_bones


def foot_tail(side):
    a = JV[side + "Ankle"]
    return V((a.x, -0.78 * SC, 0.12 * SC))


BONES = [("Root", None, V((0, 0, 0)), V((0, 0, 1.0))), ("HumanoidRootNode", "Root", JV["Root"], JV["Root"] + V((0, 0, .5))),
         ("LowerTorso", "HumanoidRootNode", JV["Root"], JV["Waist"]), ("UpperTorso", "LowerTorso", JV["Waist"], JV["Neck"]),
         ("Head", "UpperTorso", JV["Neck"], V((0, 0, HEAD_TOP)))]
for side in ("Right", "Left"):
    BONES += [(side + "UpperArm", "UpperTorso", JV[side + "Shoulder"], JV[side + "Elbow"]),
              (side + "LowerArm", side + "UpperArm", JV[side + "Elbow"], JV[side + "Wrist"]),
              (side + "Hand", side + "LowerArm", JV[side + "Wrist"], JV[side + "Wrist"] + V((0, 0, -HAND_L))),
              (side + "UpperLeg", "LowerTorso", JV[side + "Hip"], JV[side + "Knee"]),
              (side + "LowerLeg", side + "UpperLeg", JV[side + "Knee"], JV[side + "Ankle"]),
              (side + "Foot", side + "LowerLeg", JV[side + "Ankle"], foot_tail(side))]
for n, par, h, t in BONES:
    b = eb.new(n)
    b.head, b.tail = h, t
    b.use_connect = False
for n, par, h, t in BONES:
    if par:
        eb[n].parent = eb[par]
bpy.ops.object.mode_set(mode='OBJECT')
for pm in PARTS.values():
    ob = pm.obj
    vg = ob.vertex_groups.new(name=pm.name)
    vg.add([v.index for v in ob.data.vertices], 1.0, 'REPLACE')
    md = ob.modifiers.new("Armature", 'ARMATURE')
    md.object = ARM
    ob.parent = ARM
    ob.matrix_parent_inverse = Matrix.Identity(4)

# ----------------------------------------------------------------------------------------------------------------
# export
# ----------------------------------------------------------------------------------------------------------------
FBX = os.path.join(OUT, NAME + "_R15.fbx")
bpy.ops.object.select_all(action='DESELECT')
for o in [ARM] + [pm.obj for pm in PARTS.values()]:
    o.select_set(True)
bpy.context.view_layer.objects.active = ARM
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y',
                         mesh_smooth_type='FACE', use_mesh_modifiers=True, bake_anim=False, add_leaf_bones=False, path_mode='AUTO',
                         embed_textures=False, use_armature_deform_only=False, primary_bone_axis='Y', secondary_bone_axis='X',
                         object_types={'MESH', 'ARMATURE'}, colors_type='SRGB')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, NAME + ".blend"))
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
spec = {"name": NAME, "scale": SC, "height": round(HEAD_TOP, 3), "tris": sum(pm.tris() for pm in PARTS.values()),
        "parts": {n: {"tris": pm.tris(), "joint": [round(c, 4) for c in pm.joint]} for n, pm in PARTS.items()},
        "joints": {k: [round(c, 4) for c in v] for k, v in JV.items()}, "palette": C, "skin": SKIN}
json.dump(spec, open(os.path.join(OUT, "data", NAME + "_spec.json"), "w"), indent=1)
print("EXPORTED", FBX, "tris", spec["tris"], "height", spec["height"])

# ----------------------------------------------------------------------------------------------------------------
# review renders (Workbench, vertex colours)
# ----------------------------------------------------------------------------------------------------------------
if not NORENDER:
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x, sc.render.resolution_y = 900, 1100
    sh = sc.display.shading
    sh.light, sh.color_type, sh.show_cavity = 'STUDIO', 'VERTEX', False
    sh.studio_light = 'paint.sl'
    sh.use_world_space_lighting = False
    sc.display_settings.display_device = 'sRGB'
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new("W")
    w.color = (0.92, 0.91, 0.88)
    sc.world = w
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = HEAD_TOP * 1.45
    os.makedirs(os.path.join(OUT, "renders"), exist_ok=True)
    mid = V((0, 0, HEAD_TOP * 0.50))
    for tag, az in (("front", 0), ("front34", -35), ("side", -90), ("back", 180)):
        a = math.radians(az)
        d = V((math.sin(a), -math.cos(a), 0.12)).normalized() * 30.0
        cam.location = mid + d
        cam.rotation_euler = (mid - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(OUT, "renders", "%s_%s.png" % (NAME, tag))
        bpy.ops.render.render(write_still=True)
    print("RENDERED")
