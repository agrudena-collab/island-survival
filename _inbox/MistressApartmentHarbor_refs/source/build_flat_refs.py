"""Reference renders for mistress apartment #3 (Harbor tower). Usage:
  python -I build_flat_refs.py -- <out> [--only=name,name] [--samples=N] [--nobiome]
"""
import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh, mathutils
import fsd_lib
from fsd_lib import Scene, PALETTE, tri_count, TRI_LIMIT
import flat3

args = sys.argv[sys.argv.index("--") + 1:]
OUT = args[0]
ONLY = None; SAMPLES = 48; BIOME = True; SCALE = 100
for a in args[1:]:
    if a.startswith("--only="): ONLY = set(a[7:].split(","))
    elif a.startswith("--samples="): SAMPLES = int(a[10:])
    elif a == "--nobiome": BIOME = False
    elif a.startswith("--scale="): SCALE = int(a[8:])
os.makedirs(OUT, exist_ok=True)

sc = Scene()
if BIOME:
    import harbor
    harbor.build(sc)
    # drop the tower body above the plinth: the flat sits where the top of the tower is
    fx0, fy0, fx1, fy1 = flat3.CX - 36, flat3.CY - 30, flat3.CX + 36, flat3.CY + 30
    for key in list(sc.items):
        g = key[0]
        keep = []
        cut = flat3.OZ - 1.0
        for (v, f) in sc.items[key]:
            if g in ("Tower", "TowerRoof"):
                zmin = min(p[2] for p in v); zmax = max(p[2] for p in v)
                if zmin >= cut - 0.05: continue
                if zmax > cut:
                    v = [(p[0], p[1], min(p[2], cut)) for p in v]
                keep.append((v, f)); continue
            mx = sum(p[0] for p in v) / len(v); my = sum(p[1] for p in v) / len(v); mz = sum(p[2] for p in v) / len(v)
            if (fx0 < mx < fx1 and fy0 < my < fy1 and mz > flat3.OZ - 2.0) or (g in ("Tower", "TowerRoof") and mz > flat3.OZ - 2.0):
                continue
            keep.append((v, f))
        if keep: sc.items[key] = keep
        else: del sc.items[key]
else:
    import vivid
    vivid.apply_palette()
n_biome = sum(len(v) for v in sc.items.values())
flat3.build(sc)

bpy.ops.wm.read_factory_settings(use_empty=True)
S = bpy.context.scene
S.unit_settings.system = 'METRIC'
S.unit_settings.scale_length = 0.01

MATS = {}
for name, (rgb, rmat, tr) in PALETTE.items():
    m = bpy.data.materials.new("FSD_" + name)
    c = tuple((v / 255) ** 2.2 for v in rgb)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (c[0], c[1], c[2], 1.0)
    bsdf.inputs["Roughness"].default_value = 0.8
    if rmat == "Neon":
        bsdf.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1.0); bsdf.inputs["Emission Strength"].default_value = 4.0
    if rmat in ("Metal",):
        bsdf.inputs["Metallic"].default_value = 0.7; bsdf.inputs["Roughness"].default_value = 0.35
    if rmat in ("Marble", "CeramicTiles"):
        bsdf.inputs["Roughness"].default_value = 0.3
    if name == "Frost":      # mirrors: glossy, no refraction (stacked glass would go black in Cycles)
        bsdf.inputs["Metallic"].default_value = 0.9; bsdf.inputs["Roughness"].default_value = 0.08
    elif rmat == "Glass" or name in ("Water", "Water2"):
        bsdf.inputs["Alpha"].default_value = {"Glass": 0.12, "WaterTank": 0.35}.get(name, 0.6)
        bsdf.inputs["Roughness"].default_value = 0.05
    MATS[name] = m

COLL = {}
def coll(g):
    if g not in COLL:
        c = bpy.data.collections.new(g); S.collection.children.link(c); COLL[g] = c
    return COLL[g]

report = {"meshes": 0, "triangles": 0, "flat_triangles": 0}
for (group, mat, cx, cy), solids in sorted(sc.items.items()):
    chunk_v, chunk_f, n = [], [], 0
    def flush():
        global chunk_v, chunk_f, n
        if not chunk_f: return
        me = bpy.data.meshes.new(f"{group}_{mat}_{cx}_{cy}_{n:02d}")
        me.from_pydata(chunk_v, [], chunk_f); me.validate(); me.update()
        bm = bmesh.new(); bm.from_mesh(me)
        if group != "Boat": bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        t = len(bm.faces)
        bm.to_mesh(me); bm.free()
        me.materials.append(MATS[mat])
        ob = bpy.data.objects.new(me.name, me)
        coll(group).objects.link(ob)
        report["meshes"] += 1; report["triangles"] += t
        if group.startswith("Flat") or (group == "Glass" and abs(cx * 125 - 250) < 200): report["flat_triangles"] += t if group.startswith("Flat") else 0
        chunk_v, chunk_f = [], []; n += 1
    for verts, faces in solids:
        t = tri_count(faces)
        cur = sum(tri_count([f]) for f in chunk_f)
        if cur + t > TRI_LIMIT: flush()
        off = len(chunk_v); chunk_v.extend(verts); chunk_f.extend([tuple(i + off for i in f) for f in faces])
    flush()
sys.stdout.reconfigure(line_buffering=True)
print("BUILD_MESHES", report, "biome solids", n_biome)

# ---- lights: sun + sky + interior point lights
S.render.engine = 'CYCLES'
S.cycles.device = 'CPU'; S.cycles.samples = SAMPLES
S.cycles.use_denoising = True
try: S.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
S.cycles.max_bounces = 6; S.cycles.diffuse_bounces = 3; S.cycles.transmission_bounces = 6; S.cycles.glossy_bounces = 2
S.cycles.transparent_max_bounces = 24; S.cycles.caustics_reflective = False; S.cycles.caustics_refractive = False
S.view_settings.view_transform = 'Standard'
S.view_settings.look = 'None'
S.render.resolution_percentage = SCALE
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.78, 0.95, 1.0)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.2
S.world = w
sun = bpy.data.lights.new("sun", 'SUN'); sun.energy = 3.5; sun.angle = 0.08
so = bpy.data.objects.new("sun", sun); S.collection.objects.link(so)
so.rotation_euler = (math.radians(50), math.radians(10), math.radians(160))   # sun from the south-west, low: enters the panoramic window
LIGHT_POWER = float(os.environ.get("FLAT_LIGHT", "500"))
for i, (x, y, z, col, p) in enumerate(flat3.LIGHTS):
    ld = bpy.data.lights.new(f"pl{i}", 'POINT'); ld.energy = LIGHT_POWER * p; ld.color = col; ld.shadow_soft_size = 1.5
    lo = bpy.data.objects.new(f"pl{i}", ld); lo.location = (x, y, z); S.collection.objects.link(lo)
# soft fill per room (area light under the ceiling) so rooms read bright and kid-friendly
FILL = float(os.environ.get("FLAT_FILL", "1200"))
for name, (x0, y0, x1, y1) in flat3.ROOMS.items():
    cxx, cyy = flat3.T((x0 + x1) / 2, (y0 + y1) / 2)
    ad = bpy.data.lights.new("fill_" + name, 'AREA'); ad.shape = 'RECTANGLE'
    ad.size = (x1 - x0) * 0.8; ad.size_y = (y1 - y0) * 0.8
    ad.energy = FILL * (x1 - x0) * (y1 - y0) / 400.0; ad.color = (1.0, 0.95, 0.9)
    ao = bpy.data.objects.new("fill_" + name, ad); ao.location = (cxx, cyy, flat3.OZ + flat3.H - 0.3)
    S.collection.objects.link(ao)
    ad.cycles.is_caustics_light = False
    ao.visible_camera = False

cam_d = bpy.data.cameras.new("c"); cam_d.clip_end = 4000; cam_d.clip_start = 0.3
CAM = bpy.data.objects.new("c", cam_d); S.collection.objects.link(CAM); S.camera = CAM


def L(x, y, z):
    wx, wy = flat3.T(x, y)
    return (wx, wy, flat3.OZ + z)


def shot(name, loc, tgt, lens=20, ortho=None, hide=(), res=(1600, 1000), clip=0.3, local=True):
    if ONLY and name.split(".")[0] not in ONLY: return
    for g in COLL: COLL[g].hide_render = g in hide
    if local: loc, tgt = L(*loc), L(*tgt)
    CAM.location = loc
    d = mathutils.Vector(tgt) - mathutils.Vector(loc)
    CAM.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if ortho: cam_d.type, cam_d.ortho_scale = 'ORTHO', ortho
    else: cam_d.type, cam_d.lens = 'PERSP', lens
    S.render.resolution_x, S.render.resolution_y = res
    cam_d.clip_start = clip
    S.render.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)
    print("BUILD_SHOT", name, flush=True)


EYE = 6.2
# plan: top-down, no ceiling. Rotated 180: local south (hall) is at world north; camera up = local north for readability
if not ONLY or "R00_plan_top" in ONLY:
    for g in COLL: COLL[g].hide_render = g in ("FlatCeil", "FlatLamps")
    cx, cy = flat3.T(32, 24)
    CAM.location = (cx, cy, flat3.OZ + 120)
    CAM.rotation_euler = (0, 0, math.pi if flat3.ROT else 0)
    cam_d.type = 'ORTHO'; cam_d.ortho_scale = 72; cam_d.clip_start = 100.0 - 0.0
    cam_d.clip_start = 106.0
    S.render.resolution_x, S.render.resolution_y = (1600, 1250)
    S.render.filepath = os.path.join(OUT, "R00_plan_top.png")
    bpy.ops.render.render(write_still=True); print("BUILD_SHOT R00_plan_top", flush=True)
shot("R01_plan_oblique.png", (32, -34, 70), (32, 22, 0), lens=30, hide=("FlatCeil", "FlatLamps"), res=(1600, 1100))
shot("R02_hall_arrival.png", (23.0, 1.6, EYE), (23.0, 30.0, 3.6), lens=16)
shot("R03_living_wide.png", (42.0, 15.5, 8.4), (22.0, 34.0, 2.6), lens=14)
shot("R04_tea_table_guest.png", (24.5, 23.5, 7.0), (24.5, 34.5, 3.4), lens=18)
shot("R05_living_tv_aquarium.png", (20.0, 38.4, 7.4), (40.0, 20.0, 3.4), lens=15)
shot("R06_kitchen.png", (15.0, 15.4, 8.0), (2.0, 34.0, 3.0), lens=14)
shot("R07_bedroom.png", (58.5, 38.6, 8.2), (52.0, 4.0, 3.0), lens=14)
shot("R08_bedroom_window_seat.png", (47.0, 9.0, 7.0), (63.0, 26.0, 3.0), lens=15)
shot("R09_bathroom.png", (14.6, 12.6, 8.0), (4.0, 2.0, 2.6), lens=14)
shot("R10_dressing.png", (42.6, 12.4, 7.8), (32.0, 3.0, 3.0), lens=14)
shot("R11_view_town_from_balcony.png", (27.0, 46.4, 6.6), (34.0, 170.0, -66.0), lens=20)
shot("R14_view_ferris_wheel.png", (62.6, 20.25, 7.4), (274.0, -24.0, -56.0), lens=30)
shot("R12_balcony.png", (44.0, 66.0, 15.0), (38.0, 42.0, 3.0), lens=20)
print("BUILD_DONE", flush=True)
