--!strict
-- FishermanMistressHarbor: STUDIO RULES camera fix (same approach as the Fisherman Dad district fix_hitboxes).
-- Run in the Studio command bar AFTER apply_harbor_colors.luau. Makes building and tree-crown meshes solid for the camera
-- (PopperCam only stops at visible CanCollide parts), so the camera can never fly into the tower or neighbour houses.
local root = workspace:FindFirstChild("FishermanMistressHarbor")
assert(root, "import the FBX first: Workspace.FishermanMistressHarbor")
local SOLID = { Neighbors = true, Tower = true, TowerRoof = true, Trees = true }
local n = 0
for _, d in ipairs(root:GetDescendants()) do
	if d:IsA("MeshPart") then
		local group, mat = string.match(d.Name, "^([^_]+)_([^_]+)_")
		if group and SOLID[group] and mat ~= "Glass" then
			d.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition
			d.CanCollide = true
			d.CanQuery = true
			n += 1
		elseif mat == "Glass" and group == "Glass" then
			d.CanQuery = true -- windows stop rays as well (the wall body collider is behind them)
		end
	end
end
print(("camera_block: %d meshes made solid"):format(n))
