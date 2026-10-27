--!nocheck
-- Studio ModuleScript source (Edit mode): turns the freshly imported FBX model `Workspace.ForestRoad` (out/ForestRoad.fbx, File > Import 3D,
-- "Upload to Roblox" as for the district) into the finished forest road: road meshes, colliders, invisible walls, trunk colliders,
-- 4757 baked trees cloned from the T_* templates, gate/fork signs and anchors.
-- Usage: ModuleScript.Source = <this file>; require(module)(dataUrl)
--   dataUrl  http(s) URL of out/forest_road.json (served locally, e.g. by `node serve.js`; HttpService.HttpEnabled must be on)
-- The tree templates T_* sit at (i*40, 0, 2000) in the generator frame; their offsets give each template's foot point, so a clone
-- is placed by foot (x, y = ground top, z) whatever the importer chose as the MeshPart pivot.
local HS = game:GetService("HttpService")

local ROT = CFrame.Angles(0, math.pi, 0)

local function flag(p)
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.Material = Enum.Material.SmoothPlastic
	p.Color = Color3.new(1, 1, 1)
end

return function(dataUrl)
	local data = HS:JSONDecode(HS:GetAsync(dataUrl))
	local GY = data.ground_top
	local model = workspace:FindFirstChild("ForestRoad")
	assert(model, "import out/ForestRoad.fbx first (the model must be named ForestRoad)")
	local report = {}

	-- 1. bring the import back into the generator frame. Studio inserts the model at a camera-relative place (translation t) and mirrors it
	--    by 180 deg about Y: observed = ROT * expected + t. Two templates tell both: the bush must be +160 studs from the tall pine in x
	--    (negative in a mirrored import); t comes from the tall pine, whose expected centre is (x, height / 2, z) from the json.
	local tall, bush
	for _, d in ipairs(model:GetDescendants()) do
		if d:IsA("BasePart") and d.Name == "T_pine_tall" then
			tall = d
		elseif d:IsA("BasePart") and d.Name == "T_bush" then
			bush = d
		end
	end
	assert(tall and bush, "templates T_pine_tall / T_bush not found in the import")
	local flipped = (bush.Position.X - tall.Position.X) < 0
	local info = data.templates.T_pine_tall
	local expected = Vector3.new(info.x, tall.Size.Y / 2, info.z)
	local t = tall.Position - (flipped and ROT:PointToWorldSpace(expected) or expected)
	for _, d in ipairs(model:GetDescendants()) do
		if d:IsA("BasePart") then
			local c = CFrame.new(-t) * d.CFrame
			d.CFrame = flipped and (ROT * c) or c
		end
	end
	report[#report + 1] = string.format("flipped=%s offset=(%.1f, %.1f, %.1f)", tostring(flipped), t.X, t.Y, t.Z)

	-- 2. sort the imported parts: road chunks stay, templates leave the model
	local meshes = Instance.new("Folder")
	meshes.Name = "Meshes"
	local templates = {}
	for _, d in ipairs(model:GetChildren()) do
		if d:IsA("BasePart") then
			if string.sub(d.Name, 1, 2) == "T_" then
				templates[d.Name] = d
			else
				flag(d)
				d.Parent = meshes
			end
		end
	end
	meshes.Parent = model
	local nChunks = #meshes:GetChildren()

	-- 3. colliders (ground tiles, gate pillars, fork post)
	local cols = Instance.new("Folder")
	cols.Name = "Colliders"
	cols.Parent = model
	for _, r in ipairs(data.colliders) do
		local p = Instance.new("Part")
		p.Name = r[7]
		p.Anchored = true
		p.CanCollide = true
		p.Transparency = 1
		p.Size = Vector3.new(r[4], r[5], r[6])
		p.Position = Vector3.new(r[1], r[2], r[3])
		p.Parent = cols
	end

	-- 4. invisible walls along the forest corridor
	local walls = Instance.new("Folder")
	walls.Name = "Walls"
	walls.Parent = model
	for _, w in ipairs(data.walls) do
		local p = Instance.new("Part")
		p.Name = "Wall"
		p.Anchored = true
		p.CanCollide = true
		p.CanQuery = false
		p.CanTouch = false
		p.Transparency = 1
		p.Size = Vector3.new(w[3], 60, 3)
		p.CFrame = CFrame.new(w[1], GY + 30, w[2]) * CFrame.Angles(0, -math.rad(w[4]), 0)
		p.Parent = walls
	end

	-- 5. tree trunks as colliders (only trees close to the road)
	local trunks = Instance.new("Folder")
	trunks.Name = "Trunks"
	trunks.Parent = model
	for i, t in ipairs(data.trunks) do
		local p = Instance.new("Part")
		p.Name = "Trunk"
		p.Shape = Enum.PartType.Cylinder
		p.Anchored = true
		p.CanCollide = true
		p.CanQuery = false
		p.CanTouch = false
		p.Transparency = 1
		p.Size = Vector3.new(10, t[3] * 2, t[3] * 2)
		p.CFrame = CFrame.new(t[1], GY + 5, t[2]) * CFrame.Angles(0, 0, math.pi / 2)
		p.Parent = trunks
		if i % 400 == 0 then
			task.wait()
		end
	end

	-- 6. trees: clone the templates, place by foot point
	local rel, base = {}, {}
	for name, tpl in pairs(templates) do
		flag(tpl)
		tpl.CastShadow = (name ~= "T_bush")
		local info = data.templates[name]
		rel[name] = tpl.Position - Vector3.new(info.x, 0, info.z)
		base[name] = tpl.CFrame.Rotation
		report[#report + 1] = string.format("%s foot y=%.2f size=%s", name, tpl.Position.Y - tpl.Size.Y / 2, tostring(tpl.Size))
	end
	local treesFolder = Instance.new("Folder")
	treesFolder.Name = "Trees"
	treesFolder.Parent = model
	local chunk, count = nil, 0
	for i, t in ipairs(data.trees) do
		if (i - 1) % 400 == 0 then
			chunk = Instance.new("Folder")
			chunk.Name = string.format("Trees_%02d", math.floor((i - 1) / 400))
			chunk.Parent = treesFolder
			task.wait()
		end
		local tpl = templates[t[1]]
		if tpl then
			local s, th = t[5], math.rad(t[4])
			local rot = CFrame.Angles(0, th, 0)
			local c = tpl:Clone()
			c.Name = "Tree"
			c.Size = tpl.Size * s
			c.CFrame = CFrame.new(Vector3.new(t[2], GY, t[3]) + rot:VectorToWorldSpace(rel[t[1]] * s)) * rot * base[t[1]]
			c.Parent = chunk
			count += 1
		end
	end
	for _, tpl in pairs(templates) do
		tpl:Destroy()
	end

	-- 7. signs (SurfaceGui text), anchors
	local signs = Instance.new("Folder")
	signs.Name = "Signs"
	signs.Parent = model
	local faceOf = { W = Enum.NormalId.Left, E = Enum.NormalId.Right, S = Enum.NormalId.Back, N = Enum.NormalId.Front }
	for _, s in ipairs(data.signs) do
		local p = Instance.new("Part")
		p.Name = "Sign_" .. s.text
		p.Anchored = true
		p.CanCollide = false
		p.CanQuery = false
		p.Transparency = 1
		if s.face == "E" or s.face == "W" then
			p.Size = Vector3.new(0.2, s.h, s.w)
		else
			p.Size = Vector3.new(s.w, s.h, 0.2)
		end
		p.Position = Vector3.new(s.x, s.y, s.z)
		local g = Instance.new("SurfaceGui")
		g.Face = faceOf[s.face] or Enum.NormalId.Back
		g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		g.PixelsPerStud = 40
		g.LightInfluence = 0
		g.Parent = p
		local l = Instance.new("TextLabel")
		l.Size = UDim2.fromScale(1, 1)
		l.BackgroundTransparency = 1
		l.Text = s.text
		l.TextScaled = true
		l.Font = Enum.Font.FredokaOne
		l.TextColor3 = (s.face == "S") and Color3.fromRGB(58, 42, 26) or Color3.new(1, 1, 1)
		l.Parent = g
		p.Parent = signs
	end
	local anc = Instance.new("Folder")
	anc.Name = "Anchors"
	anc.Parent = model
	for name, a in pairs(data.anchors) do
		local p = Instance.new("Part")
		p.Name = name
		p.Anchored = true
		p.CanCollide = false
		p.CanQuery = false
		p.CanTouch = false
		p.Transparency = 1
		p.Size = Vector3.new(2, 0.2, 2)
		p.Position = Vector3.new(a[1], a[2] + 0.1, a[3])
		p:SetAttribute("FaceX", a[4])
		p:SetAttribute("FaceZ", a[5])
		p.Parent = anc
	end

	model.Name = "ForestRoad"
	report[#report + 1] = string.format("chunks=%d colliders=%d walls=%d trunks=%d trees=%d signs=%d", nChunks, #cols:GetChildren(), #data.walls, #data.trunks, count, #data.signs)
	return table.concat(report, "\n")
end
