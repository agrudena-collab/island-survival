--!nocheck
-- Studio ModuleScript source (Edit mode): turns the freshly imported FBX model `Workspace.RDD_District` into `Workspace.RegularDadDistrict`.
-- Usage: ModuleScript.Source = <this file>; require(module)(dataUrl, apartmentModel)
--   dataUrl        http(s) URL of out/district.json (served locally, e.g. by `node serve.js`)
--   apartmentModel the MistressBuilding1 model (Interior + Exterior) that is moved into the district, or nil
-- Steps: rotate 180 deg about Y (the FBX axis conversion), white colour + SmoothPlastic/Glass/Neon per chunk kind (O_/G_/N_), no collision on
-- meshes, invisible Colliders from the json, Lights (tag DistrictLamp), Signs (SurfaceGui text), Anchors, entrance/exit/givers.
local HS = game:GetService("HttpService")
local CS = game:GetService("CollectionService")

return function(dataUrl, apartment)
	local data = HS:JSONDecode(HS:GetAsync(dataUrl))
	local old = workspace:FindFirstChild("RegularDadDistrict")
	if old then old:Destroy() end
	local m = workspace.RDD_District
	m.Name = "RegularDadDistrict"
	m:PivotTo(CFrame.Angles(0, math.pi, 0))
	local meshes = Instance.new("Folder") meshes.Name = "Meshes"
	local nO, nG, nN = 0, 0, 0
	for _, c in ipairs(m:GetChildren()) do
		if c:IsA("MeshPart") then
			local k = c.Name:sub(1, 1)
			c.Anchored = true c.CanCollide = false c.CanQuery = false c.CanTouch = false
			c.Color = Color3.new(1, 1, 1)
			c.Material = Enum.Material.SmoothPlastic
			if k == "G" then c.Transparency = 0.55 c.Material = Enum.Material.Glass c.CastShadow = false nG += 1
			elseif k == "N" then c.Material = Enum.Material.Neon c.CastShadow = false nN += 1
			else nO += 1 end
			c.Parent = meshes
		end
	end
	meshes.Parent = m
	local cols = Instance.new("Folder") cols.Name = "Colliders" cols.Parent = m
	for _, r in ipairs(data.colliders) do
		local p = Instance.new("Part") p.Name = r[7] p.Anchored = true p.CanCollide = true p.Transparency = 1
		p.Size = Vector3.new(r[4], r[5], r[6]) p.Position = Vector3.new(r[1], r[2], r[3]) p.Parent = cols
	end
	local lamps = Instance.new("Folder") lamps.Name = "Lights" lamps.Parent = m
	for _, l in ipairs(data.lights) do
		local p = Instance.new("Part") p.Name = "LampLight" p.Anchored = true p.CanCollide = false p.CanQuery = false p.CanTouch = false p.Transparency = 1
		p.Size = Vector3.new(0.3, 0.3, 0.3) p.Position = Vector3.new(l[1], l[2], l[3])
		local pl = Instance.new("PointLight") pl.Range = l[4] pl.Brightness = 1 pl.Color = Color3.fromRGB(255, 225, 170) pl.Shadows = false pl.Enabled = false pl.Parent = p
		CS:AddTag(p, "DistrictLamp")
		p.Parent = lamps
	end
	local signs = Instance.new("Folder") signs.Name = "Signs" signs.Parent = m
	local faceOf = { S = Enum.NormalId.Back, N = Enum.NormalId.Front, E = Enum.NormalId.Right, W = Enum.NormalId.Left }
	local off = { Back = Vector3.new(0, 0, 0.9), Front = Vector3.new(0, 0, -0.9), Right = Vector3.new(0.9, 0, 0), Left = Vector3.new(-0.9, 0, 0) }
	for _, s in ipairs(data.signs) do
		local p = Instance.new("Part") p.Name = "Sign_" .. s.text p.Anchored = true p.CanCollide = false p.CanQuery = false p.Transparency = 1
		p.Size = Vector3.new(s.w, s.h, 0.2)
		if s.face == "E" or s.face == "W" then p.Size = Vector3.new(0.2, s.h, s.w) end
		local face = faceOf[s.face] or Enum.NormalId.Back
		p.Position = Vector3.new(s.x, s.y, s.z) + off[face.Name]
		local g = Instance.new("SurfaceGui") g.Face = face g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud g.PixelsPerStud = 40 g.LightInfluence = 0 g.Parent = p
		local t = Instance.new("TextLabel") t.Size = UDim2.fromScale(1, 1) t.BackgroundTransparency = 1 t.Text = s.text t.TextScaled = true t.Font = Enum.Font.FredokaOne t.TextColor3 = Color3.new(1, 1, 1) t.Parent = g
		p.Parent = signs
	end
	local anc = Instance.new("Folder") anc.Name = "Anchors" anc.Parent = m
	for name, a in pairs(data.anchors) do
		local p = Instance.new("Part") p.Name = name p.Anchored = true p.CanCollide = false p.CanQuery = false p.Transparency = 1 p.Size = Vector3.new(4, 0.2, 4)
		p.CFrame = CFrame.lookAt(Vector3.new(a[1], a[2], a[3]), Vector3.new(a[1] + a[4], a[2], a[3] + a[5]))
		p.Parent = anc
	end
	if apartment then
		local b = apartment
		local ext = b:FindFirstChild("Exterior")
		for _, c in ipairs(ext:GetChildren()) do c:Destroy() end
		local function mk(name, size, cf, tag)
			local p = Instance.new("Part") p.Name = name p.Anchored = true p.CanCollide = false p.Transparency = 1 p.Size = size p.CFrame = cf p.Parent = ext
			if tag then CS:AddTag(p, tag) end
			return p
		end
		local ent = mk("Entrance", Vector3.new(6, 8, 1.5), anc.tower_entrance.CFrame + Vector3.new(0, 4, 0), "ApartmentEntrance")
		ent:SetAttribute("ApartmentId", "RegularDadMistress")
		mk("ExitArrival", Vector3.new(4, 0.2, 4), anc.tower_exit_arrival.CFrame)
		mk("BagShop", Vector3.new(4, 6, 4), anc.bag_shop.CFrame + Vector3.new(0, 3, 0), "HeistBagShop")
		mk("LadderGiver", Vector3.new(4, 6, 4), anc.ladder_giver.CFrame + Vector3.new(0, 3, 0), "HeistLadderGiver")
		b.Parent = m
	end
	return string.format("O%d G%d N%d colliders %d lights %d signs %d", nO, nG, nN, #data.colliders, #data.lights, #data.signs)
end
