--!nocheck
-- Studio ModuleScript source (Edit mode): turns the freshly imported FBX model `Workspace.OfficeDadDistrict` (File > Import 3D, "Upload to Roblox" OFF)
-- into the finished district model, with no manual steps afterwards.
-- Usage: ModuleScript.Source = <this file>; require(module)(source [, apartmentModel])
--   source          either the text of out/district.json or an http(s) URL that serves it
--   apartmentModel  optional MistressBuilding2 model (it must hold Interior); its Exterior is rebuilt here. Without it a placeholder
--                   model `MistressBuilding2` with Exterior (Entrance, ExitArrival) is created so the flat can be dropped in later.
-- Steps: rotate 180 deg about Y (FBX axis conversion), white colour + SmoothPlastic / Glass 0.55 / Neon per chunk kind (O_ / G_ / N_), no collision on the meshes,
-- invisible Colliders from the json (CanCollide), Lights (tag DistrictLamp), Signs (SurfaceGui text), Anchors, fence sections as removable folders (Fence_<N1..E2>:
-- mesh + collider, delete a folder to open that part of the border), apartment entrance (tag ApartmentEntrance; ApartmentId is assigned by the project owner).
local HS = game:GetService("HttpService")
local CS = game:GetService("CollectionService")

return function(source, apartment)
	local text = source
	if not source:match("^%s*{") then text = HS:GetAsync(source) end
	local data = HS:JSONDecode(text)
	local old = workspace:FindFirstChild("OfficeDadDistrict")
	if old and old ~= workspace:FindFirstChild("OfficeDadDistrictImport") then old:Destroy() end
	local m = workspace:FindFirstChild("OfficeDadDistrict")
	assert(m, "import the FBX first: it must appear as Workspace.OfficeDadDistrict")
	m:PivotTo(CFrame.Angles(0, math.pi, 0))

	local meshes = Instance.new("Folder") meshes.Name = "Meshes"
	local fenceFolders = {}
	local nO, nG, nN, nF = 0, 0, 0, 0
	for _, c in ipairs(m:GetChildren()) do
		if c:IsA("MeshPart") then
			local k = c.Name:sub(1, 1)
			c.Anchored = true c.CanCollide = false c.CanQuery = false c.CanTouch = false
			c.Color = Color3.new(1, 1, 1)
			c.Material = Enum.Material.SmoothPlastic
			if k == "G" then c.Transparency = 0.55 c.Material = Enum.Material.Glass c.CastShadow = false nG += 1
			elseif k == "N" then c.Material = Enum.Material.Neon c.CastShadow = false nN += 1
			else nO += 1 end
			local sec = c.Name:match("^O_Fence_(%w+)_%d+$")
			if sec then
				local f = fenceFolders[sec]
				if not f then f = Instance.new("Folder") f.Name = "Fence_" .. sec fenceFolders[sec] = f end
				c.Parent = f nF += 1
			else
				c.Parent = meshes
			end
		end
	end
	meshes.Parent = m

	local cols = Instance.new("Folder") cols.Name = "Colliders" cols.Parent = m
	for _, r in ipairs(data.colliders) do
		local p = Instance.new("Part") p.Name = r[7] p.Anchored = true p.CanCollide = true p.CanQuery = true p.Transparency = 1
		p.Size = Vector3.new(r[4], r[5], r[6]) p.Position = Vector3.new(r[1], r[2], r[3])
		p.Material = Enum.Material.SmoothPlastic
		local sec = r[7]:match("^edge(%w+)$")
		if sec and fenceFolders[sec] then p.Parent = fenceFolders[sec] else p.Parent = cols end
	end
	for _, f in pairs(fenceFolders) do f.Parent = m end

	local lamps = Instance.new("Folder") lamps.Name = "Lights" lamps.Parent = m
	for _, l in ipairs(data.lights) do
		local p = Instance.new("Part") p.Name = "LampLight" p.Anchored = true p.CanCollide = false p.CanQuery = false p.CanTouch = false p.Transparency = 1
		p.Size = Vector3.new(0.3, 0.3, 0.3) p.Position = Vector3.new(l[1], l[2], l[3])
		local pl = Instance.new("PointLight") pl.Range = l[4] pl.Brightness = 1 pl.Color = Color3.fromRGB(255, 225, 170) pl.Shadows = false pl.Enabled = false pl.Parent = p
		CS:AddTag(p, "DistrictLamp")
		p.Parent = lamps
	end

	-- sign position in the json = the front face plane of the board; the transparent part sits 0.05 in front of it
	local signs = Instance.new("Folder") signs.Name = "Signs" signs.Parent = m
	local faceOf = { S = Enum.NormalId.Back, N = Enum.NormalId.Front, E = Enum.NormalId.Right, W = Enum.NormalId.Left }
	local off = { Back = Vector3.new(0, 0, 0.05), Front = Vector3.new(0, 0, -0.05), Right = Vector3.new(0.05, 0, 0), Left = Vector3.new(-0.05, 0, 0) }
	for _, s in ipairs(data.signs) do
		local p = Instance.new("Part") p.Name = "Sign_" .. s.text p.Anchored = true p.CanCollide = false p.CanQuery = false p.CanTouch = false p.Transparency = 1
		p.Size = Vector3.new(s.w, s.h, 0.1)
		if s.face == "E" or s.face == "W" then p.Size = Vector3.new(0.1, s.h, s.w) end
		local face = faceOf[s.face] or Enum.NormalId.Back
		p.Position = Vector3.new(s.x, s.y, s.z) + off[face.Name]
		local g = Instance.new("SurfaceGui") g.Face = face g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud g.PixelsPerStud = 40 g.LightInfluence = 0 g.Parent = p
		local t = Instance.new("TextLabel") t.Size = UDim2.fromScale(1, 1) t.BackgroundTransparency = 1 t.Text = s.text t.TextScaled = true t.Font = Enum.Font.FredokaOne t.TextColor3 = Color3.new(1, 1, 1) t.Parent = g
		p.Parent = signs
	end

	local anc = Instance.new("Folder") anc.Name = "Anchors" anc.Parent = m
	for name, a in pairs(data.anchors) do
		local p = Instance.new("Part") p.Name = name p.Anchored = true p.CanCollide = false p.CanQuery = false p.CanTouch = false p.Transparency = 1 p.Size = Vector3.new(4, 0.2, 4)
		p.CFrame = CFrame.lookAt(Vector3.new(a[1], a[2], a[3]), Vector3.new(a[1] + a[4], a[2], a[3] + a[5]))
		p.Parent = anc
	end

	-- the mistress' building: Exterior holds the entrance (tagged ApartmentEntrance, ApartmentId assigned by the owner) and the exit arrival
	local b = apartment
	if not b then
		b = Instance.new("Model") b.Name = "MistressBuilding2"
		local e = Instance.new("Folder") e.Name = "Exterior" e.Parent = b
	end
	local ext = b:FindFirstChild("Exterior") or Instance.new("Folder")
	ext.Name = "Exterior" ext.Parent = b
	for _, c in ipairs(ext:GetChildren()) do c:Destroy() end
	local function mk(name, size, cf, tag)
		local p = Instance.new("Part") p.Name = name p.Anchored = true p.CanCollide = false p.CanQuery = true p.Transparency = 1 p.Size = size p.CFrame = cf p.Parent = ext
		if tag then CS:AddTag(p, tag) end
		return p
	end
	-- the door is 7.2 wide and 9.2 high; the entrance part sits in the doorway just in front of it
	local ae = anc.tower_entrance.CFrame
	mk("Entrance", Vector3.new(7, 9, 1.5), ae + ae.LookVector * 6.0 + Vector3.new(0, 4.5, 0), "ApartmentEntrance")
	mk("ExitArrival", Vector3.new(4, 0.2, 4), anc.tower_exit_arrival.CFrame)
	b.Parent = m
	local na = 0
	for _ in pairs(data.anchors) do na += 1 end
	return string.format("O%d G%d N%d fence %d colliders %d lights %d signs %d anchors %d", nO, nG, nN, nF, #data.colliders, #data.lights, #data.signs, na)
end
