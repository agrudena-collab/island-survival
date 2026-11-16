--!strict
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
