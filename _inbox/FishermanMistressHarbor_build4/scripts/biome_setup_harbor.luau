--!strict
-- FishermanMistressHarbor: biome setup (run in the Studio command bar AFTER the colours + colliders scripts).
-- Same idea as biome_setup.luau of the Fisherman Dad district: hide the default Baseplate (it z-fights with the ground at Y=0),
-- water becomes Glass, the spawn goes to PlayerStart facing north, bright kid-friendly lighting.
local root = workspace:FindFirstChild("FishermanMistressHarbor")
assert(root, "import the FBX first: Workspace.FishermanMistressHarbor")

-- 1. Baseplate: invisible, no collision (the district has its own ground and lake-bed colliders)
local bp = workspace:FindFirstChild("Baseplate")
if bp and bp:IsA("BasePart") then
	bp.Transparency = 1
	bp.CanCollide = false
	bp.CanQuery = false
	bp.CanTouch = false
	bp.CFrame = CFrame.new(-250, -30, 250)
end

-- 2. Water: Glass, bright lagoon blue, no collision. Foam lines stay white plastic.
local nWater = 0
for _, d in ipairs(root:GetDescendants()) do
	if d:IsA("MeshPart") then
		local group, mat = string.match(d.Name, "^([^_]+)_([^_]+)_")
		if group == "Water" and (mat == "Water" or mat == "Water2") then
			d.Material = Enum.Material.Glass
			d.Color = Color3.fromRGB(52, 186, 232)
			d.Transparency = 0.3
			d.CanCollide = false
			d.CanQuery = false
			d.CastShadow = false
			nWater += 1
		elseif group == "Backdrop" then
			d.CanCollide = false -- cliffs / waterfall / tunnels are scenery outside the bounds
		end
	end
end

-- 3. Spawn at PlayerStart (south entrance, Avenue B), facing north into the district
local anchors = root:FindFirstChild("Anchors")
local ps = anchors and anchors:FindFirstChild("PlayerStart")
local spawn = workspace:FindFirstChildOfClass("SpawnLocation")
if ps and ps:IsA("BasePart") then
	if not spawn then
		spawn = Instance.new("SpawnLocation")
		spawn.Parent = workspace
	end
	local s = spawn :: SpawnLocation
	s.Anchored = true
	s.Size = Vector3.new(6, 1, 6)
	s.Transparency = 1
	s.CanCollide = false
	local p = Vector3.new(ps.Position.X, 0.75, ps.Position.Z)
	s.CFrame = CFrame.lookAt(p, p + Vector3.new(0, 0, 1))
	local decal = s:FindFirstChildOfClass("Decal")
	if decal then decal:Destroy() end
end

-- 4. Bright, colourful lighting (kids mode). Re-runnable: replaces our own effects only.
local L = game:GetService("Lighting")
L.ClockTime = 13.5
L.Brightness = 3
L.Ambient = Color3.fromRGB(140, 140, 150)
L.OutdoorAmbient = Color3.fromRGB(170, 170, 180)
L.EnvironmentDiffuseScale = 0.6
L.EnvironmentSpecularScale = 0.3
L.GlobalShadows = true
for _, e in ipairs(L:GetChildren()) do
	if e.Name == "HarborColor" or e:IsA("Atmosphere") then e:Destroy() end
end
local cc = Instance.new("ColorCorrectionEffect")
cc.Name = "HarborColor"
cc.Saturation = 0.2
cc.Contrast = 0.05
cc.Brightness = 0.02
cc.Parent = L
local at = Instance.new("Atmosphere")
at.Name = "HarborAtmosphere"
at.Density = 0.22
at.Offset = 0.1
at.Color = Color3.fromRGB(200, 230, 255)
at.Decay = Color3.fromRGB(150, 200, 240)
at.Glare = 0.1
at.Haze = 0.6
at.Parent = L

print(("biome_setup: water %d, spawn %s, baseplate %s"):format(nWater, tostring(ps ~= nil), tostring(bp ~= nil)))
