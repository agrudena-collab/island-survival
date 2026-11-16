import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh, mathutils
from gd_lib import Scene, PALETTE, tri_count, TRI_LIMIT
import gm_district, gm_tower

OUT = sys.argv[sys.argv.index("--") + 1]
os.makedirs(os.path.join(OUT, "previews"), exist_ok=True)
os.makedirs(os.path.join(OUT, "export"), exist_ok=True)
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
os.makedirs(os.path.join(OUT, "scripts"), exist_ok=True)
os.makedirs(os.path.join(OUT, "source"), exist_ok=True)

sc = Scene()
gm_district.build(sc)

bpy.ops.wm.read_factory_settings(use_empty=True)
S = bpy.context.scene
S.unit_settings.system = 'METRIC'
S.unit_settings.scale_length = 0.01

MATS = {}
for name, (rgb, rmat, tr) in PALETTE.items():
    m = bpy.data.materials.new("GD_" + name)
    c = tuple((v / 255) ** 2.2 for v in rgb)
    m.diffuse_color = (rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (c[0], c[1], c[2], 1.0)
    bsdf.inputs["Roughness"].default_value = 0.85
    if PALETTE[name][1] == "Neon":
        bsdf.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1.0); bsdf.inputs["Emission Strength"].default_value = 3.0
    if tr > 0:
        bsdf.inputs["Alpha"].default_value = 1.0 - tr
        m.surface_render_method = "BLENDED" if hasattr(m, "surface_render_method") else None
    MATS[name] = m

COLL = {}
def coll(g):
    if g not in COLL:
        c = bpy.data.collections.new(g); S.collection.children.link(c); COLL[g] = c
    return COLL[g]

UV_TILE = 8.0
objs = []
report = {"meshes": 0, "triangles": 0, "by_group": {}, "max_tris": 0}
for (group, mat, cx, cy), solids in sorted(sc.items.items()):
    chunk_v, chunk_f, n = [], [], 0
    def flush():
        global chunk_v, chunk_f, n
        if not chunk_f: return
        me = bpy.data.meshes.new(f"{group}_{mat}_{cx}_{cy}_{n:02d}")
        me.from_pydata(chunk_v, [], chunk_f); me.validate(); me.update()
        bm = bmesh.new(); bm.from_mesh(me)
        if True:
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        t = len(bm.faces)
        # box-projected UVs so Roblox materials (WoodPlanks, Shingles, Sand...) tile instead of smearing
        uvl = bm.loops.layers.uv.new("UVMap")
        bm.normal_update()
        for f in bm.faces:
            nx, ny, nz = (abs(c) for c in f.normal)
            for lp in f.loops:
                co = lp.vert.co
                if nz >= nx and nz >= ny: u, v = co.x, co.y
                elif nx >= ny: u, v = co.y, co.z
                else: u, v = co.x, co.z
                lp[uvl].uv = (u / UV_TILE, v / UV_TILE)
        bm.to_mesh(me); bm.free()
        me.materials.append(MATS[mat])
        ob = bpy.data.objects.new(me.name, me)
        coll(group).objects.link(ob)
        objs.append(ob)
        report["meshes"] += 1; report["triangles"] += t; report["max_tris"] = max(report["max_tris"], t)
        g = report["by_group"].setdefault(group, {"meshes": 0, "triangles": 0}); g["meshes"] += 1; g["triangles"] += t
        chunk_v, chunk_f = [], []; n += 1
    for verts, faces in solids:
        t = tri_count(faces)
        cur = sum(tri_count([f]) for f in chunk_f)
        if cur + t > TRI_LIMIT: flush()
        off = len(chunk_v); chunk_v.extend(verts); chunk_f.extend([tuple(i + off for i in f) for f in faces])
    flush()
sys.stdout.reconfigure(line_buffering=True)
print("BUILD_MESHES", report["meshes"], "TRIS", report["triangles"], "MAX", report["max_tris"])


# ---------- data files ----------
NAME = "GrillMistressDistrict"
json.dump(sc.colliders, open(os.path.join(OUT, "data", "colliders.json"), "w"), indent=1)
json.dump(sc.anchors, open(os.path.join(OUT, "data", "anchors.json"), "w"), indent=1)
manifest = {
    "asset": NAME, "status": "build 1, awaiting owner review", "game": "Steal a Dad!",
    "units": {"blender_unit_equals_roblox_studs": 1.0, "scene_scale_length": 0.01},
    "coordinates": "plan coords: x east, y north, z up. District 0..500 x 0..500, ground top z=0. After FBX import: Roblox X = -Blender x, Y = Blender z, Z = Blender y (same mapping as the other districts).",
    "layout": {"gate": [250, 7], "tower_plaza": [170, 170, 330, 330], "bbq_park": [170, 354, 330, 500], "roads_ew_y": [146, 170, 330, 354], "roads_ns_x": [146, 170, 330, 354], "gate_road_x": [238, 262]},
    "tower": {"body": [gm_tower.TX0, gm_tower.TY0, gm_tower.TX1, gm_tower.TY1], "lobby_floor": gm_tower.ZL, "wall_top": gm_tower.ZT, "roof_deck": gm_tower.ZR,
              "teleport_pad": list(gm_tower.PAD), "note": "closed facade; the flat is a separate hidden model entered via the teleport pad (tag ApartmentEntrance)"},
    "counts": report, "colliders": len(sc.colliders), "anchors": len(sc.anchors),
    "palette": {k: {"rgb": v[0], "roblox_material": v[1], "transparency": v[2]} for k, v in PALETTE.items()},
}
json.dump(manifest, open(os.path.join(OUT, "MANIFEST.json"), "w"), indent=1)

lines = ['--!strict', '-- Generated by build_gd.py. Run in the Studio command bar after importing the FBX (model must be Workspace.GrillMistressDistrict).',
         'local PALETTE: { [string]: { color: Color3, material: Enum.Material, transparency: number } } = {']
for k, (rgb, rm, tr) in PALETTE.items():
    lines.append(f'\t["{k}"] = {{ color = Color3.fromRGB({rgb[0]}, {rgb[1]}, {rgb[2]}), material = Enum.Material.{rm}, transparency = {tr} }},')
lines += ['}',
  'local ROOF = { NeighborRoofs = true, ParkRoof = true }',
  'local n, miss = 0, 0',
  'for _, d in ipairs(workspace:GetDescendants()) do',
  '\tif d:IsA("MeshPart") then',
  '\t\tlocal group, mat = string.match(d.Name, "^([^_]+)_([^_]+)_")',
  '\t\tlocal p = mat and PALETTE[mat]',
  '\t\tif p then',
  '\t\t\tlocal m = p.material',
  '\t\t\tif ROOF[group] and string.sub(mat, 1, 4) == "Roof" then m = Enum.Material.RoofShingles end',
  '\t\t\td.Color, d.Material, d.Transparency = p.color, m, p.transparency',
  '\t\t\td.Anchored = true',
  '\t\t\td.CanCollide = false -- real collision comes from Colliders (build_studio_colliders_anchors.luau); camera_block.luau then makes buildings solid for the camera',
  '\t\t\td.CastShadow = p.transparency < 0.2 and p.material ~= Enum.Material.Neon',
  '\t\t\tn += 1',
  '\t\telse miss += 1 end',
  '\tend',
  'end',
  'print(("painted %d parts, %d unmatched"):format(n, miss))']
open(os.path.join(OUT, "scripts", "apply_gd_colors.luau"), "w").write("\n".join(lines))
open(os.path.join(OUT, "scripts", "camera_block.luau"), "w").write("""--!strict
-- GrillMistressDistrict: STUDIO RULES camera fix. Run in the Studio command bar AFTER apply_gd_colors.luau.
-- PopperCam only stops at visible CanCollide parts, so building / tree / cliff meshes AND the ground meshes are made solid:
-- the camera can never fly into the mistress tower, the neighbour houses, tree crowns, the cliffs, or under the map.
-- All of them go to the collision group "CameraOccluder"; characters ("Players" group, see character_collision.luau) walk through them
-- and use only the invisible box colliders (Colliders folder), which keep every doorway and the gate open.
local PhysicsService = game:GetService("PhysicsService")
local function reg(name: string) pcall(function() PhysicsService:RegisterCollisionGroup(name) end) end
reg("CameraOccluder"); reg("Players")
PhysicsService:CollisionGroupSetCollidable("CameraOccluder", "Players", false)
PhysicsService:CollisionGroupSetCollidable("CameraOccluder", "Default", true)
PhysicsService:CollisionGroupSetCollidable("Players", "Default", true)
local root = workspace:FindFirstChild("GrillMistressDistrict")
assert(root, "import the FBX first: Workspace.GrillMistressDistrict")
local SOLID = { MTower = true, MTowerRoof = true, Kiosk = true, BusStop = true, Teleport = true, Neighbors = true, NeighborRoofs = true, Trees = true, Cliffs = true,
	Gate = true, Truck = true, Tower = true, ParkRoof = true, Billboard = true, Bushes = true, Cars = true, Fences = true }
local GROUND = { Terrain = true, Roads = true, Park = true, Plaza = true }   -- flat ground: Box fidelity is enough, keeps the camera above the ground
local n, g = 0, 0
for _, d in ipairs(root:GetDescendants()) do
	if d:IsA("MeshPart") then
		local group, mat = string.match(d.Name, "^([^_]+)_([^_]+)_")
		if group and SOLID[group] and mat ~= "Glass" then
			d.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition
			d.CanCollide = true
			d.CanQuery = true
			d.CollisionGroup = "CameraOccluder"
			n += 1
		elseif group and GROUND[group] then
			d.CollisionFidelity = Enum.CollisionFidelity.Box
			d.CanCollide = true
			d.CanQuery = true
			d.CollisionGroup = "CameraOccluder"
			g += 1
		elseif group == "Glass" then
			d.CanQuery = true
		end
	end
end
print(("camera_block: %d meshes solid, %d ground meshes (CameraOccluder group)"):format(n, g))
""")
open(os.path.join(OUT, "scripts", "character_collision.luau"), "w").write("""--!strict
-- Run once in the Studio command bar (edit mode): creates ServerScriptService.GrillMistressCharacterCollision, which puts every
-- character part into the collision group "Players" (they pass through the CameraOccluder meshes, walk on the invisible colliders).
local SSS = game:GetService("ServerScriptService")
local old = SSS:FindFirstChild("GrillMistressCharacterCollision")
if old then old:Destroy() end
local sc = Instance.new("Script")
sc.Name = "GrillMistressCharacterCollision"
sc.Source = [[
local Players = game:GetService("Players")
local function setup(char)
	for _, d in ipairs(char:GetDescendants()) do if d:IsA("BasePart") then d.CollisionGroup = "Players" end end
	char.DescendantAdded:Connect(function(d) if d:IsA("BasePart") then d.CollisionGroup = "Players" end end)
end
local function onPlayer(p) p.CharacterAdded:Connect(setup) if p.Character then setup(p.Character) end end
Players.PlayerAdded:Connect(onPlayer)
for _, p in ipairs(Players:GetPlayers()) do onPlayer(p) end
]]
sc.Parent = SSS
print("GrillMistressCharacterCollision created")
""")


# ---------- save + FBX ----------
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "source", NAME + ".blend"))
FBX = os.path.join(OUT, "export", NAME + ".fbx")
bpy.ops.object.select_all(action='DESELECT')
for ob in objs: ob.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, object_types={'MESH'}, apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_UNITS', axis_forward='Z', axis_up='Y', mesh_smooth_type='FACE',
    use_mesh_modifiers=True, bake_anim=False, add_leaf_bones=False, path_mode='COPY', embed_textures=False)
print("BUILD_FBX", FBX, os.path.getsize(FBX))
if os.environ.get("GD_NO_RENDER"):
    print("BUILD_DONE"); sys.exit(0)

# ---------- previews ----------
S.render.engine = 'CYCLES'
S.cycles.device = 'CPU'; S.cycles.samples = int(os.environ.get("GD_SAMPLES", "24")); S.cycles.use_denoising = True
S.cycles.max_bounces = 3; S.cycles.diffuse_bounces = 2
S.view_settings.view_transform = 'Standard'
S.view_settings.look = 'None'
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.36, 0.62, 1.0, 1.0)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.25
S.world = w
sun = bpy.data.lights.new("sun", 'SUN'); sun.energy = 3.6; sun.angle = 0.06
so = bpy.data.objects.new("sun", sun); S.collection.objects.link(so)
so.rotation_euler = (math.radians(46), math.radians(6), math.radians(-28))
cam_d = bpy.data.cameras.new("c"); cam_d.clip_end = 3000; cam_d.clip_start = 0.5
CAM = bpy.data.objects.new("c", cam_d); S.collection.objects.link(CAM); S.camera = CAM
ONLY = os.environ.get("GD_SHOTS")
def shot(name, loc, tgt, lens=35, ortho=None, hide=(), res=(1600, 900), clip=None, sub="previews"):
    if ONLY and not any(k in name for k in ONLY.split(",")): return
    for g in COLL: COLL[g].hide_render = g in hide
    CAM.location = loc
    d = mathutils.Vector(tgt) - mathutils.Vector(loc)
    CAM.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if ortho: cam_d.type, cam_d.ortho_scale = 'ORTHO', ortho
    else: cam_d.type, cam_d.lens = 'PERSP', lens
    S.render.resolution_x, S.render.resolution_y = res
    cam_d.clip_start = clip if clip else 0.5
    os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    S.render.filepath = os.path.join(OUT, sub, name)
    bpy.ops.render.render(write_still=True)
    print("BUILD_SHOT", name)
T = gm_tower
shot("01_district_top.png", (250, 250, 900), (250, 250.01, 0), ortho=540, res=(1300, 1300))
shot("02_biome_aerial.png", (420, 30, 170), (250, 270, 10), lens=30)
shot("03_tower_front.png", (250, 150, 40), (250, 270, 30), lens=28)
shot("04_tower_aerial.png", (330, 190, 110), (250, 276, 30), lens=30)
shot("05_teleport_pad.png", (262, 222, 9), (250, 248, 4), lens=26)
shot("06_roof_terrace.png", (300, 240, 90), (250, 278, 56), lens=28)
shot("07_plaza_kiosk.png", (330, 200, 24), (290, 236, 3), lens=26)
shot("08_bus_stop.png", (214, 160, 8), (198, 181, 4), lens=26)
shot("09_bbq_park.png", (330, 360, 60), (250, 420, 0), lens=28)
shot("10_gazebo_pond.png", (250, 400, 30), (250, 450, 4), lens=30)
shot("11_gate.png", (250, -30, 18), (250, 30, 14), lens=30)
shot("12_lot_fences.png", (215, 330, 110), (80, 250, 0), lens=26)
shot("13_tower_side.png", (360, 340, 30), (276, 276, 30), lens=26)
shot("14_waterfall.png", (250, 430, 16), (250, 486, 20), lens=26)
shot("15_waterfall_side.png", (215, 455, 22), (250, 484, 18), lens=26)
print("BUILD_DONE")
