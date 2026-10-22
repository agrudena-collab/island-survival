--!nocheck
-- Studio command-bar script (Edit mode): adds the data FamilyNpcService (src/server/Services) reads from the house.
-- Run on a freshly imported house model (Workspace.RegularDadHouse_V2_Final) after the interactive layer exists.
-- It records exactly what was done by hand on 22.10.2026; the FBX/Blender generator does not produce any of this.
local house = workspace.RegularDadHouse_V2_Final
local CS = game:GetService("CollectionService")

-- 1. furniture meshes are visual only; collision comes from RDH_Collision (merged furniture chunks with precise
--    convex decomposition created invisible walls that trapped NPCs and players)
for _, p in ipairs(house.RDH_House:GetChildren()) do
	if p:IsA("BasePart") and p.CanCollide then
		p.CanCollide = false
	end
end

-- 2. hidden half step beside the lowest stair tread (floor 1.02, tread top 1.97 -> two risers of ~0.5);
--    without it the navmesh has no step into the staircase and the son cannot climb
local step = house.RDH_Collision:FindFirstChild("StairFootStep") or Instance.new("Part")
step.Name = "StairFootStep"
step.Anchored, step.CanCollide, step.CanQuery, step.Transparency = true, true, true, 1
step.Size = Vector3.new(2.4, 0.5, 1.7)
step.Position = Vector3.new(32.0, 1.25, 23.1)
step.Parent = house.RDH_Collision

-- 3. door leaves can be walked through by NPC pathfinding (the NPC opens the door when it gets close)
for _, model in ipairs(house.Interactive:GetChildren()) do
	if model:IsA("Model") and string.sub(model.Name, 1, 5) == "Door_" then
		for _, leaf in ipairs(model:GetChildren()) do
			if leaf:IsA("BasePart") and string.sub(leaf.Name, 1, 4) == "Leaf" and not leaf:FindFirstChildOfClass("PathfindingModifier") then
				local pm = Instance.new("PathfindingModifier")
				pm.PassThrough = true
				pm.Parent = leaf
			end
		end
	end
end

-- 4. routes, lot bounds, caught spawn; points are feet-level and were chosen free of collision (see the spiral search in the log)
local function marker(name, pos, size, parent)
	local p = Instance.new("Part")
	p.Name, p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch, p.Transparency = name, true, false, false, false, 1
	p.Size, p.Position, p.Parent = size, pos, parent
	return p
end
local old = house:FindFirstChild("FamilyRoutes")
if old then old:Destroy() end
local routes = Instance.new("Folder")
routes.Name = "FamilyRoutes"
routes.Parent = house
local function wp(role, i, x, y, z, pause, activity)
	local p = marker(string.format("%s_%02d", role, i), Vector3.new(x, y + 0.1, z), Vector3.new(1, 0.2, 1), routes)
	p:SetAttribute("Pause", pause or 0)
	if activity then
		p:SetAttribute("Activity", activity)
	end
end
local G, U = 1.0, 14.75
wp("Wife", 1, 29, G, -22.6, 5, "Cook")     -- kitchen
wp("Wife", 2, 62, G, -22, 3)               -- dining room
wp("Wife", 3, 59, G, 7.3, 4)               -- living room
wp("Son", 1, 58, U, -8.7, 4, "Fidget")     -- child's room
wp("Son", 2, 34, U, -2.9, 2)               -- upper hall
wp("Son", 3, 59, G, 7.3, 4, "Fidget")      -- living room (via the staircase)
wp("Son", 4, 34, U, -2.9, 2)               -- upper hall
for _, n in ipairs({ "FamilyLotBounds", "CaughtSpawn" }) do
	local o = house:FindFirstChild(n)
	if o then
		o:Destroy()
	end
end
marker("FamilyLotBounds", Vector3.new(49.3, 20, -10.3), Vector3.new(98.6, 60, 99.4), house)
marker("CaughtSpawn", Vector3.new(36, 1, 34), Vector3.new(4, 0.2, 4), house)
-- 5. low-cover proxies for NPC vision (sofa, armchairs, bed, kitchen island): exported by the generator into
--    data/interactive.json ("cover"); serve that folder (python -m http.server) and enable HttpService, or paste the table.
local HttpService = game:GetService("HttpService")
local data = HttpService:JSONDecode(HttpService:GetAsync("http://localhost:8770/interactive.json"))
local cov = house:FindFirstChild("LowCover")
if cov then
	cov:Destroy()
end
cov = Instance.new("Folder")
cov.Name = "LowCover"
cov.Parent = house
for i, c in ipairs(data.cover) do
	local p = Instance.new("Part")
	p.Name = string.format("%s_%02d", c.name, i)
	p.Anchored, p.CanCollide, p.CanTouch, p.CanQuery, p.Transparency = true, false, false, true, 1
	p.Size = Vector3.new(c.w, c.h, c.d)
	p.CFrame = CFrame.new(c.x, c.y + c.h / 2, c.z) * CFrame.Angles(0, -c.yaw, 0)
	p:SetAttribute("CoverHeight", c.h)
	p.Parent = cov
end

CS:AddTag(house, "FamilyHouse")
-- 6. the father the heist packs (HeistService builds the "Забрать в мешок" prompt itself)
if house:FindFirstChild("RegularDad_Father") then
	CS:AddTag(house.RegularDad_Father, "FamilyFather")
	house.RegularDad_Father:SetAttribute("DadId", "RegularDad")
end
print("family data applied")
