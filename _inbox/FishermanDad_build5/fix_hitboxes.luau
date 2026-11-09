-- fix_hitboxes.luau — FishermanDadDistrict post-import hitbox/camera fixes.
-- Re-runnable. Run in Studio command bar (Edit) after apply_fsd_colors + build_studio_colliders_anchors.
-- Does: (1) neighbour houses solid so camera can't fly in; (2) small rocks walkable; (3) wall/roof meshes queryable.
local m = workspace:FindFirstChild("FishermanDadDistrict")
assert(m, "no FishermanDadDistrict")
local log = {}

-- (1) CAMERA: neighbour houses are closed shells with only a front-wall collider -> camera enters from sides/roof.
-- Make their meshes solid + queryable so Poppercam stops and player can't pass through.
local nSolid = 0
for _, d in ipairs(m:GetDescendants()) do
	if d:IsA("MeshPart") and d.Name:match("^Neighbors") then
		d.CanCollide = true
		d.CanQuery = true
		nSolid += 1
	end
end
log[#log+1] = "neighbour meshes made solid (camera block): " .. nSolid

-- Fisherman house/roof: keep walkable via existing colliders, just ensure camera-queryable (enterable, do not force CanCollide)
local nQ = 0
for _, d in ipairs(m:GetDescendants()) do
	if d:IsA("MeshPart") and (d.Name:match("^House") or d.Name:match("^HouseRoof")) then
		d.CanQuery = true
		nQ += 1
	end
end
log[#log+1] = "house/roof meshes set CanQuery: " .. nQ

-- (2) ROCKS: colliders are 2.5..5.7 tall -> player hits them like walls.
-- Cap each rock collider height to STEP so the player can walk up / step over. Keep the bottom fixed. Idempotent.
local STEP = 1.5
local rockFixed = 0
for _, d in ipairs(m.Colliders:GetChildren()) do
	if d.Name == "Col_Props_Rock" and d.Size.Y > STEP then
		local bottom = d.Position.Y - d.Size.Y/2
		d.Size = Vector3.new(d.Size.X, STEP, d.Size.Z)
		d.Position = Vector3.new(d.Position.X, bottom + STEP/2, d.Position.Z)
		rockFixed += 1
	end
end
log[#log+1] = string.format("rocks: collider capped to %.1f (steppable) = %d", STEP, rockFixed)

-- (3) Stray neighbour boat placed INSIDE the fisherman house (X~-201.5, Z~350): sits under the deck, half-submerged,
-- its 6 hull layers z-fight -> "a boat that flickers with no model". The father's boat (X~-295.5) stays. Remove the stray.
local removed = 0
for _, d in ipairs(m:GetDescendants()) do
	if d:IsA("MeshPart") and d.Name:match("^Boat")
		and d.Position.X > -212 and d.Position.X < -192 and d.Position.Z > 340 and d.Position.Z < 360 then
		d:Destroy(); removed += 1
	end
end
for _, d in ipairs(m.Colliders:GetChildren()) do
	if d.Name == "Col_Boat_NeighbourBoatDeck"
		and d.Position.X > -212 and d.Position.X < -192 and d.Position.Z > 340 and d.Position.Z < 360 then
		d:Destroy(); removed += 1
	end
end
log[#log+1] = "stray neighbour boat inside house removed: " .. removed .. " parts"

-- (4) INVISIBLE BARRIER road->front deck: Col_Pier_FrontStep is 7.9 studs tall (a wall) at the road/deck junction.
-- Lower it to a real step (top at deck height ~1.0) so you walk onto the deck freely. Idempotent.
local STEPTOP = 1.0
local stepFixed = 0
for _, d in ipairs(m.Colliders:GetChildren()) do
	if d.Name == "Col_Pier_FrontStep" and d.Size.Y > STEPTOP + 0.1 then
		local bottom = d.Position.Y - d.Size.Y/2
		local h = STEPTOP - bottom
		if h < 0.3 then h = 0.3 end
		d.Size = Vector3.new(d.Size.X, h, d.Size.Z)
		d.Position = Vector3.new(d.Position.X, bottom + h/2, d.Position.Z)
		stepFixed += 1
	end
end
log[#log+1] = "road->deck FrontStep barrier lowered to step: " .. stepFixed

-- (5) TREES solid + opaque: canopy meshes had no collider (only thin trunk) -> player walks through foliage.
local treeSolid = 0
for _, d in ipairs(m:GetDescendants()) do
	if d:IsA("MeshPart") and d.Name:match("^Trees") then
		d.CanCollide = true; d.CanQuery = true; d.Transparency = 0
		treeSolid += 1
	end
end
log[#log+1] = "tree meshes made solid+opaque: " .. treeSolid

-- (6) BUSHES solid + opaque: make bush meshes (Biome meshes sitting on a Biome_Bush collider, raised above ground) collidable.
local CELLB = 6
local bgrid = {}
for _, d in ipairs(m:GetDescendants()) do
	if d:IsA("MeshPart") and d.Name:match("^Biome") and (d.Position.Y + d.Size.Y/2) > 1.2 then
		local cx, cz = math.floor(d.Position.X/CELLB), math.floor(d.Position.Z/CELLB)
		local k = cx..","..cz
		bgrid[k] = bgrid[k] or {}; table.insert(bgrid[k], d)
	end
end
local bushMesh, bushCol = 0, 0
for _, c in ipairs(m.Colliders:GetChildren()) do
	if c.Name == "Col_Biome_Bush" then
		c.CanCollide = true; c.CanQuery = true; bushCol += 1
		local p, s = c.Position, c.Size/2
		for cx = math.floor((p.X-s.X)/CELLB), math.floor((p.X+s.X)/CELLB) do
			for cz = math.floor((p.Z-s.Z)/CELLB), math.floor((p.Z+s.Z)/CELLB) do
				for _, d in ipairs(bgrid[cx..","..cz] or {}) do
					if math.abs(d.Position.X-p.X) < s.X+2 and math.abs(d.Position.Z-p.Z) < s.Z+2 then
						d.CanCollide = true; d.CanQuery = true; d.Transparency = 0; bushMesh += 1
					end
				end
			end
		end
	end
end
log[#log+1] = string.format("bushes: colliders ensured=%d, bush meshes made solid+opaque=%d", bushCol, bushMesh)

-- (7) CAMERA through father's house: Poppercam only respects opaque CanCollide=true parts.
-- Thin wall colliders left gaps (esp. south 2nd-floor wall) -> camera flew through solid walls.
-- Make the real house shell meshes camera-solid by precise geometry (keeps door/window openings passable).
-- Windows (Glass) also solid. Yield periodically: PreciseConvexDecomposition is heavy.
local shell, winSolid, i = 0, 0, 0
for _, d in ipairs(m:GetDescendants()) do
	if d:IsA("MeshPart") and (d.Name:match("^House_") or d.Name:match("^HouseRoof")) then
		pcall(function() d.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition end)
		d.CanCollide = true; d.CanQuery = true; shell += 1
		i += 1; if i % 8 == 0 then task.wait() end
	elseif d:IsA("MeshPart") and d.Name:match("^Glass") then -- windows (Water group separate, untouched)
		d.CanCollide = true; d.CanQuery = true; winSolid += 1
	end
end
log[#log+1] = string.format("father house camera-solid: shell meshes(precise)=%d, windows=%d", shell, winSolid)

return table.concat(log, "\n")
