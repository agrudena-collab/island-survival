--!strict
-- GrillDadDistrict: STUDIO RULES camera fix. Run in the Studio command bar AFTER apply_gd_colors.luau.
-- PopperCam only stops at visible CanCollide parts, so building / tree / cliff meshes are made solid:
-- the camera can never fly into Grill Dad's house, the neighbour houses, tree crowns or the cliffs.
local root = workspace:FindFirstChild("GrillDadDistrict")
assert(root, "import the FBX first: Workspace.GrillDadDistrict")
local SOLID = { CastleWall = true, Grill = true, Neighbors = true, NeighborRoofs = true, House = true, House2F = true, HouseRoof = true, Trees = true, Cliffs = true,
	Gate = true, Truck = true, Monument = true, ParkRoof = true, Billboard = true, Bushes = true, Cars = true, Fences = true }
local n = 0
for _, d in ipairs(root:GetDescendants()) do
	if d:IsA("MeshPart") then
		local group, mat = string.match(d.Name, "^([^_]+)_([^_]+)_")
		if group and SOLID[group] and mat ~= "Glass" then
			d.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition
			d.CanCollide = true
			d.CanQuery = true
			n += 1
		elseif group == "Glass" then
			d.CanQuery = true
		end
	end
end
print(("camera_block: %d meshes made solid"):format(n))
