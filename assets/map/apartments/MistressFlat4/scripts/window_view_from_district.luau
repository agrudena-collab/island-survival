--!nocheck
-- MistressFlat4: the window view becomes an exact copy of GrillMistressDistrict, seen from the 7th floor of the turquoise tower.
-- The flat itself STAYS at its hidden origin (-16000, 300, 16000); only scenery copies are placed around it.
-- Run in the Studio command bar (Edit) after studio_setup_flat4.luau. Re-runnable (rebuilds Interior.WindowView).
-- Mapping: plan point (x, y, z) of the district -> flat local (x - TX + W/2, y - TY + D/2, z - FLOOR_Z).
local W, D = 84, 56
local TX, TY = 250, 277          -- tower centre in plan coords
local FLOOR_Z = 47               -- top residential floor of the tower (lobby 11 + 6 storeys x 6)
local SKIP = { MTower = true, MTowerRoof = true }   -- we are inside the tower: no copy of its walls/roof
local KEEP_OLD = { Turq = true, White = true }       -- old procedural view: keep only the facade under the flat

local district = workspace:FindFirstChild("GrillMistressDistrict")
assert(district, "Workspace.GrillMistressDistrict not found")
local building = district:FindFirstChild("MistressBuilding4")
local interior = building and building:FindFirstChild("Interior")
assert(interior, "run studio_setup_flat4.luau first")
local view = interior:FindFirstChild("WindowView")
local origin = interior.Arrival.Position - Vector3.new(-41, 0.22, 5.5)   -- Arrival is plan (41, 5.5) in the flat -> Roblox (-41, ., 5.5)
origin = Vector3.new(math.floor(origin.X + 0.5), 300, math.floor(origin.Z + 0.5))
-- district Roblox coords: X = -x, Y = z, Z = y. Flat local -> Roblox: X = O.X - lx, Y = O.Y + lz, Z = O.Z + ly.
-- district X_d = -x  ->  O.X - (x - (TX - W/2)) = X_d + O.X + (TX - W/2)
local offset = Vector3.new(origin.X + (TX - W / 2), origin.Y - FLOOR_Z, origin.Z - (TY - D / 2))

-- 1. drop the old generic backdrop (keep the tower facade under the flat)
local removed = 0
for _, m in ipairs(view:GetChildren()) do
	local _, mat = string.match(m.Name, "^([^_]+)_([^_]+)_")
	if not (mat and KEEP_OLD[mat]) then m:Destroy() removed += 1 end
end
local copy = view:FindFirstChild("DistrictCopy")
if copy then copy:Destroy() end
copy = Instance.new("Folder") copy.Name = "DistrictCopy" copy.Parent = view

-- 2. copy every district mesh (not the flat, not the tower itself), scenery only
local list = {}
for _, d in ipairs(district:GetDescendants()) do
	if d:IsA("MeshPart") and not d:IsDescendantOf(building) then
		local group = string.match(d.Name, "^([^_]+)_")
		if group and not SKIP[group] then table.insert(list, d) end
	end
end
local n = 0
for i = 1, #list, 250 do
	local chunk = Instance.new("Folder") chunk.Name = "Chunk" .. i
	for j = i, math.min(i + 249, #list) do
		local c = list[j]:Clone()
		for _, ch in ipairs(c:GetChildren()) do ch:Destroy() end
		c.CFrame = c.CFrame + offset
		c.Anchored, c.CanCollide, c.CanQuery, c.CanTouch, c.CastShadow = true, false, false, false, false
		c.CollisionGroup = "Default"
		c.Parent = chunk
		n += 1
	end
	chunk.Parent = copy
	task.wait()
end
print(("window view: %d district meshes copied (old backdrop pieces removed: %d), offset %s"):format(n, removed, tostring(offset)))
