"""Blender build of MistressFlat4 (Grill Dad's mistress flat): FBX + data/flat.json + Studio setup module + previews.
Run: blender -b --factory-startup --python build_flat.py -- <out>   (GD_NO_RENDER=1 skips previews)"""
import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh, mathutils
from gd_lib import Scene, PALETTE, tri_count, TRI_LIMIT
import gm_flat

OUT = sys.argv[sys.argv.index("--") + 1]
for d in ("previews", "export", "data", "scripts", "source"):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)
NAME = "MistressFlat4"

sc = Scene()
gm_flat.build(sc)

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
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (c[0], c[1], c[2], 1.0)
    bsdf.inputs["Roughness"].default_value = 0.8
    if rmat == "Neon":
        bsdf.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1.0); bsdf.inputs["Emission Strength"].default_value = 2.0
    if tr > 0:
        bsdf.inputs["Alpha"].default_value = 1.0 - tr
        if hasattr(m, "surface_render_method"): m.surface_render_method = "BLENDED"
    MATS[name] = m
COLL = {}
def coll(g):
    if g not in COLL:
        c = bpy.data.collections.new(g); S.collection.children.link(c); COLL[g] = c
    return COLL[g]

UV_TILE = 8.0
objs = []
report = {"meshes": 0, "triangles": 0, "by_group": {}, "max_tris": 0}
allv = []
for (group, mat, cx, cy), solids in sorted(sc.items.items()):
    chunk_v, chunk_f, n = [], [], 0
    def flush():
        global chunk_v, chunk_f, n
        if not chunk_f: return
        me = bpy.data.meshes.new(f"{group}_{mat}_{cx}_{cy}_{n:02d}")
        me.from_pydata(chunk_v, [], chunk_f); me.validate(); me.update()
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        t = len(bm.faces)
        uvl = bm.loops.layers.uv.new("UVMap"); bm.normal_update()
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
        ob = bpy.data.objects.new(me.name, me); coll(group).objects.link(ob); objs.append(ob)
        report["meshes"] += 1; report["triangles"] += t; report["max_tris"] = max(report["max_tris"], t)
        g = report["by_group"].setdefault(group, {"meshes": 0, "triangles": 0}); g["meshes"] += 1; g["triangles"] += t
        chunk_v, chunk_f = [], []; n += 1
    for verts, faces in solids:
        t = tri_count(faces)
        if sum(tri_count([f]) for f in chunk_f) + t > TRI_LIMIT: flush()
        off = len(chunk_v); chunk_v.extend(verts); chunk_f.extend([tuple(i + off for i in f) for f in faces])
        allv.extend(verts)
    flush()
sys.stdout.reconfigure(line_buffering=True)
print("BUILD_MESHES", report["meshes"], "TRIS", report["triangles"], "MAX", report["max_tris"])

# ---------- data (Roblox axes relative to the flat origin: X = -x, Y = z, Z = y) ----------
def rb(x, y, z): return [round(-x, 3), round(z, 3), round(y, 3)]
xs = [v[0] for v in allv]; ys = [v[1] for v in allv]; zs = [v[2] for v in allv]
mesh_center = rb((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2)
mesh_size = [round(max(xs) - min(xs), 3), round(max(zs) - min(zs), 3), round(max(ys) - min(ys), 3)]
cols = []
for c in sc.colliders:
    (x0, y0, z0), (x1, y1, z1) = c["min"], c["max"]
    cols.append(rb((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) + [round(x1 - x0, 3), round(z1 - z0, 3), round(y1 - y0, 3), c["tag"]])
lights = [rb(x, y, z) + [r, b, col[0], col[1], col[2]] for (x, y, z, r, b, col) in gm_flat.LIGHTS]
anchors = {k: {"pos": rb(*v["pos"]), "look": list(v["look"])} for k, v in gm_flat.ANCH.items()}
W, D, CH = gm_flat.W, gm_flat.D, gm_flat.CH
cam = {"center": rb(W / 2, D / 2, CH / 2), "size": [W - 1.0, CH, D - 1.0]}
flat = {"asset": NAME, "dad": "GrillDad (DadId GrillDad)", "mapping": "Roblox X=-x, Y=z, Z=y relative to origin",
        "mesh_center": mesh_center, "mesh_size": mesh_size, "colliders": cols, "lights": lights, "anchors": anchors, "cam_bounds": cam}
json.dump(flat, open(os.path.join(OUT, "data", "flat.json"), "w"), separators=(",", ":"))
manifest = {"asset": NAME, "status": "build 1, awaiting owner review", "game": "Steal a Dad!", "dad": "GrillDad",
            "size_studs": [W, D, CH], "rooms": ["vestibule", "living room", "dining (MistressDesk)", "kitchen with indoor grill", "bedroom", "bathroom", "dressing room", "sun lounge with bar"],
            "counts": report, "colliders": len(cols), "lights": len(lights), "anchors": sorted(anchors),
            "hidden_origin": [-16000, 300, 16000]}
json.dump(manifest, open(os.path.join(OUT, "MANIFEST.json"), "w"), indent=1)

# ---------- Studio setup module ----------
pal = "\n".join(f'\t["{k}"] = {{ Color3.fromRGB({rgb[0]}, {rgb[1]}, {rgb[2]}), Enum.Material.{rm}, {tr} }},' for k, (rgb, rm, tr) in PALETTE.items())
setup = '''--!nocheck
-- MistressFlat4 (Grill Dad mistress, turquoise tower of GrillMistressDistrict). Generated by build_flat.py.
-- Studio, Edit mode. Usage (ModuleScript.Source = this file):
--   require(module)(flatJsonText, origin)
--     flatJsonText  text of data/flat.json
--     origin        Vector3 of the hidden flat origin (default -16000, 300, 16000: far away, never visible from any biome)
-- What it does:
--   1. Moves the imported FBX model Workspace.MistressFlat4 to the hidden origin (aligned by its bounding box).
--   2. Colours/materials (procedural, no images). Walls, floor, ceiling, glass are solid for the camera; the window view is scenery only.
--   3. Builds Workspace.GrillMistressDistrict.MistressBuilding4:
--        Exterior: Entrance (tag ApartmentEntrance -> ApartmentService adds «Войти» and teleports) on the TELEPORT pad, ExitArrival in front of it.
--        Interior: Meshes, WindowView, Colliders, Lights, Arrival, ExitDoor (tag ApartmentExit), MistressSeat, GuestSeat,
--                  Table_Top (tag MistressDesk, DadId = "GrillDad"), CamBounds (tag ApartmentCamBounds, used by ApartmentCameraClamp).
--   ApartmentId is NOT set (owner decides). Re-run: delete MistressBuilding4.Interior, import the FBX again, run again.
local HS = game:GetService("HttpService")
local CS = game:GetService("CollectionService")
local PALETTE = {
%s
}
local SOLID = { FlatWalls = true, FlatCeil = true, FlatFloor = true, Glass = true }

return function(text, origin)
	origin = origin or Vector3.new(-16000, 300, 16000)
	pcall(function() game:GetService("PhysicsService"):RegisterCollisionGroup("CameraOccluder") end)
	local data = HS:JSONDecode(text)
	local src = workspace:FindFirstChild("MistressFlat4")
	assert(src, "import export/MistressFlat4.fbx first (File > Import 3D, Upload to Roblox off): it must appear as Workspace.MistressFlat4")
	local district = workspace:FindFirstChild("GrillMistressDistrict")
	assert(district, "the district (Workspace.GrillMistressDistrict) must be in the place, with its Anchors built")
	for _, d in ipairs(src:GetDescendants()) do if d:IsA("BasePart") then d.Anchored = true end end
	local cf, size = src:GetBoundingBox()
	local mc, ms = data.mesh_center, data.mesh_size
	local delta = origin + Vector3.new(mc[1], mc[2], mc[3]) - cf.Position
	local warn = ""
	if math.abs(size.X - ms[1]) > 3 or math.abs(size.Y - ms[2]) > 3 or math.abs(size.Z - ms[3]) > 3 then
		warn = (" | WARNING size %%.0f,%%.0f,%%.0f expected %%.0f,%%.0f,%%.0f (import scale/rotation changed?)"):format(size.X, size.Y, size.Z, ms[1], ms[2], ms[3])
	end
	local building = district:FindFirstChild("MistressBuilding4")
	if not building then building = Instance.new("Model") building.Name = "MistressBuilding4" building.Parent = district end
	local old = building:FindFirstChild("Interior") if old then old:Destroy() end
	local interior = Instance.new("Model") interior.Name = "Interior"
	local meshes = Instance.new("Folder") meshes.Name = "Meshes" meshes.Parent = interior
	local view = Instance.new("Folder") view.Name = "WindowView" view.Parent = interior
	local n, nSolid, nView = 0, 0, 0
	for _, d in ipairs(src:GetDescendants()) do
		if d:IsA("MeshPart") then
			d.CFrame = d.CFrame + delta
			local group, mat = string.match(d.Name, "^([^_]+)_([^_]+)_")
			local p = mat and PALETTE[mat]
			if p then d.Color, d.Material, d.Transparency = p[1], p[2], p[3] end
			d.CanTouch = false
			d.CastShadow = not (p and (p[2] == Enum.Material.Neon or p[3] > 0.2))
			if group == "View" then
				d.CanCollide, d.CanQuery, d.CastShadow = false, false, false
				d.Parent = view nView += 1
			else
				if SOLID[group] then
					d.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition
					d.CanCollide, d.CanQuery = true, true
					d.CollisionGroup = "CameraOccluder"
					nSolid += 1
				else
					d.CanCollide, d.CanQuery = false, false
				end
				if mat == "Glass" or mat == "Mirror" then d.Material = Enum.Material.Glass d.CastShadow = false end
				if mat == "Water" then d.Material = Enum.Material.Glass d.Transparency = 0.3 end
				d.Parent = meshes
			end
			n += 1
		end
	end
	src:Destroy()
	local function rel(v) return origin + Vector3.new(v[1], v[2], v[3]) end
	local colf = Instance.new("Folder") colf.Name = "Colliders" colf.Parent = interior
	for _, r in ipairs(data.colliders) do
		local c = Instance.new("Part") c.Name = r[7] c.Anchored = true c.CanCollide = true c.CanQuery = true c.CanTouch = false c.Transparency = 1
		c.Size = Vector3.new(math.max(r[4], 0.05), math.max(r[5], 0.05), math.max(r[6], 0.05)) c.Position = rel(r) c.Parent = colf
	end
	local lamps = Instance.new("Folder") lamps.Name = "Lights" lamps.Parent = interior
	for _, l in ipairs(data.lights) do
		local c = Instance.new("Part") c.Name = "Light" c.Anchored = true c.CanCollide = false c.CanQuery = false c.CanTouch = false c.Transparency = 1
		c.Size = Vector3.new(0.3, 0.3, 0.3) c.Position = rel(l)
		local pl = Instance.new("PointLight") pl.Range = l[4] pl.Brightness = l[5] pl.Color = Color3.fromRGB(l[6], l[7], l[8]) pl.Shadows = false pl.Parent = c
		c.Parent = lamps
	end
	local A = data.anchors
	local function mk(name, sz, an, up)
		local pos = rel(an.pos) + Vector3.new(0, up or 0, 0)
		local c = Instance.new("Part") c.Name = name c.Anchored = true c.CanCollide = false c.CanQuery = true c.CanTouch = false c.Transparency = 1
		c.Size = sz c.CFrame = CFrame.lookAt(pos, pos + Vector3.new(an.look[1], an.look[2], an.look[3])) c.Parent = interior
		return c
	end
	mk("Arrival", Vector3.new(4, 0.2, 4), A.arrival, 0.1)
	local door = mk("ExitDoor", Vector3.new(6, 8.6, 0.8), A.exit_door) CS:AddTag(door, "ApartmentExit")
	mk("MistressSeat", Vector3.new(1.5, 0.2, 1.5), A.mistress_seat, 0.1)
	mk("GuestSeat", Vector3.new(1.5, 0.2, 1.5), A.guest_seat, 0.1)
	local top = mk("Table_Top", Vector3.new(5.2, 0.5, 5.2), A.table_top, -0.25)
	top:SetAttribute("DadId", "GrillDad")
	CS:AddTag(top, "MistressDesk")
	local cb = Instance.new("Part") cb.Name = "CamBounds" cb.Anchored = true cb.CanCollide = false cb.CanQuery = false cb.CanTouch = false cb.Transparency = 1
	cb.Size = Vector3.new(data.cam_bounds.size[1], data.cam_bounds.size[2], data.cam_bounds.size[3]) cb.Position = rel(data.cam_bounds.center) cb.Parent = interior
	CS:AddTag(cb, "ApartmentCamBounds")
	interior.Parent = building
	-- exterior: «Войти» on the teleport pad in front of the tower
	local ext = building:FindFirstChild("Exterior") if ext then ext:Destroy() end
	ext = Instance.new("Model") ext.Name = "Exterior" ext.Parent = building
	local anchors = district:FindFirstChild("Anchors")
	local te = anchors and anchors:FindFirstChild("ApartmentEntrance")
	local tx = anchors and anchors:FindFirstChild("ExitArrival")
	assert(te and tx, "run build_studio_colliders_anchors.luau of GrillMistressDistrict first (Anchors.ApartmentEntrance / ExitArrival)")
	local ent = Instance.new("Part") ent.Name = "Entrance" ent.Anchored = true ent.CanCollide = false ent.CanQuery = false ent.CanTouch = false ent.Transparency = 1
	ent.Size = Vector3.new(7, 6, 7) ent.CFrame = CFrame.new(te.Position + Vector3.new(0, 3, 0)) ent.Parent = ext
	CS:AddTag(ent, "ApartmentEntrance")
	local ea = Instance.new("Part") ea.Name = "ExitArrival" ea.Anchored = true ea.CanCollide = false ea.CanQuery = false ea.CanTouch = false ea.Transparency = 1
	ea.Size = Vector3.new(4, 0.2, 4) ea.CFrame = CFrame.lookAt(tx.Position, tx.Position + Vector3.new(0, 0, -1)) ea.Parent = ext
	return ("MistressFlat4: meshes %%d (solid %%d, view %%d) colliders %%d lights %%d | entrance at %%s | flat origin %%s%%s"):format(
		n, nSolid, nView, #data.colliders, #data.lights, tostring(ent.Position), tostring(origin), warn)
end
''' % pal
open(os.path.join(OUT, "scripts", "studio_setup_flat4.luau"), "w", encoding="utf-8").write(setup)

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
S.cycles.device = 'CPU'; S.cycles.samples = int(os.environ.get("GD_SAMPLES", "32")); S.cycles.use_denoising = True
S.cycles.max_bounces = 4; S.cycles.diffuse_bounces = 3
S.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new("w"); w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.42, 0.66, 1.0, 1.0); bg.inputs[1].default_value = 1.0
S.world = w
sun = bpy.data.lights.new("sun", 'SUN'); sun.energy = 3.0; sun.angle = 0.08
so = bpy.data.objects.new("sun", sun); S.collection.objects.link(so); so.rotation_euler = (math.radians(50), math.radians(8), math.radians(-30))
for (x, y, z, r, b, col) in gm_flat.LIGHTS:   # soft interior fill like the Studio PointLights
    L = bpy.data.lights.new("p", 'POINT'); L.energy = 900 * b; L.color = tuple(c / 255 for c in col); L.shadow_soft_size = 1.5
    o = bpy.data.objects.new("p", L); S.collection.objects.link(o); o.location = (x, y, z)
cam_d = bpy.data.cameras.new("c"); cam_d.clip_end = 2000
CAM = bpy.data.objects.new("c", cam_d); S.collection.objects.link(CAM); S.camera = CAM
ONLY = os.environ.get("GD_SHOTS")
def shot(name, loc, tgt, lens=20, ortho=None, hide=(), res=(1600, 900)):
    if ONLY and not any(k in name for k in ONLY.split(",")): return
    for g in COLL: COLL[g].hide_render = g in hide
    CAM.location = loc
    d = mathutils.Vector(tgt) - mathutils.Vector(loc)
    CAM.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if ortho: cam_d.type, cam_d.ortho_scale = 'ORTHO', ortho
    else: cam_d.type, cam_d.lens = 'PERSP', lens
    S.render.resolution_x, S.render.resolution_y = res
    S.render.filepath = os.path.join(OUT, "previews", name)
    bpy.ops.render.render(write_still=True)
    print("BUILD_SHOT", name)
shot("01_plan.png", (42, 28, 200), (42, 28.01, 0), ortho=92, hide=("FlatCeil", "View"), res=(1600, 1100))
shot("02_aerial_cut.png", (42, -40, 90), (42, 30, 0), lens=24, hide=("FlatCeil", "View"))
shot("03_vestibule_view.png", (41, 3.5, 6), (30, 30, 4), lens=16)
shot("04_living.png", (27, 2.5, 8.5), (8, 22, 3), lens=16)
shot("05_dining.png", (52, 11, 8), (44, 21, 3.5), lens=18)
shot("06_kitchen.png", (58, 28, 8.5), (74, 8, 3), lens=16)
shot("07_bedroom.png", (28, 35, 8.5), (12, 50, 3), lens=16)
shot("08_bathroom.png", (48, 34, 9), (36, 50, 2), lens=15)
shot("09_dressing.png", (56, 34, 8), (56, 54, 4), lens=16)
shot("10_lounge.png", (70, 33, 8), (78, 52, 4), lens=16)
shot("11_kitchen_counter.png", (72, 10, 8), (83, 14, 4), lens=18)
shot("12_tub.png", (41, 42, 8.5), (41, 51, 2.5), lens=20)
shot("13_egg_chair.png", (72, 44, 7), (66, 51, 5), lens=22)
print("BUILD_DONE")
