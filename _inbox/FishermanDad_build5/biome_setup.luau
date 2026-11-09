-- biome_setup.luau — FishermanDadDistrict scene setup after import + align (run in Edit).
-- Baseplate -> invisible floor under the district; water visible; spawn in district; map bounds.
local m = workspace:FindFirstChild("FishermanDadDistrict")
assert(m, "no model")
local log = {}

-- district footprint from ground collider: X[-520,20], Z[-20,520]
local bp = workspace:FindFirstChild("Baseplate")
if bp then
	for _, c in ipairs(bp:GetChildren()) do if c:IsA("Texture") or c:IsA("Decal") then c:Destroy() end end
	bp.Size = Vector3.new(540, 16, 540)
	bp.Position = Vector3.new(-250, -8, 250)
	bp.Transparency = 1; bp.CanCollide = true; bp.Anchored = true; bp.CastShadow = false
	bp.Material = Enum.Material.SmoothPlastic
	log[#log+1] = "Baseplate -> invisible floor 540x540 top Y=0"
else log[#log+1] = "Baseplate: none" end

local sp = workspace:FindFirstChild("SpawnLocation")
if sp then
	sp.Anchored = true; sp.CanCollide = true
	sp.CFrame = CFrame.lookAt(Vector3.new(-250, 3, 20), Vector3.new(-250, 3, 120))
	log[#log+1] = "SpawnLocation -> (-250,3,20) facing north"
end

local wn = 0
for _, d in ipairs(m:GetDescendants()) do
	if d:IsA("MeshPart") and (d.Name:match("Water") or d.Name:match("Lake")) then
		d.Material = Enum.Material.Glass
		d.Color = Color3.new(0.18, 0.45, 0.55)
		d.Transparency = 0.30; d.Reflectance = 0.05
		d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = false
		wn += 1
	end
end
log[#log+1] = "water meshes styled: " .. wn

local old = workspace:FindFirstChild("FishermanDadDistrict_Bounds")
if old then old:Destroy() end
local bf = Instance.new("Folder"); bf.Name = "FishermanDadDistrict_Bounds"; bf.Parent = workspace
local function wall(name, cx, cy, cz, sx, sy, sz)
	local p = Instance.new("Part"); p.Name = name; p.Anchored = true; p.CanCollide = true; p.CanQuery = true
	p.Transparency = 1; p.CastShadow = false; p.Material = Enum.Material.SmoothPlastic
	p.Size = Vector3.new(sx, sy, sz); p.Position = Vector3.new(cx, cy, cz); p.Parent = bf
end
wall("BoundW", -521, 21, 250, 2, 60, 544)
wall("BoundE", 21, 21, 250, 2, 60, 544)
wall("BoundS", -250, 21, -21, 544, 60, 2)
wall("BoundN", -250, 21, 521, 544, 60, 2)
log[#log+1] = "bounds: 4 walls h60"

return table.concat(log, "\n")
