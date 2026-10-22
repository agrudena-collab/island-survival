--!nocheck
-- Studio ModuleScript source (Edit mode): turns the freshly imported FBX model `Workspace.MistressFlat` into the Interior of a MistressBuilding1.
-- Usage: ModuleScript.Source = <this file>; require(module)(dataUrl, building, origin)
--   dataUrl   URL of out/flat.json (served locally, e.g. by `node serve.js`)
--   building  the MistressBuilding1 model; its old `Interior` is destroyed and replaced
--   origin    Vector3 of the flat origin (ix, iy, iz); the generator coordinates are relative to it (floor top = iy + 1)
-- Contract with ApartmentService / DialogueService: Interior.Arrival, a part tagged ApartmentExit (the door prompt), a part tagged MistressDesk (attribute DadId).
local HS = game:GetService("HttpService")
local CS = game:GetService("CollectionService")

return function(dataUrl, building, origin)
	local data = HS:JSONDecode(HS:GetAsync(dataUrl))
	local old = building:FindFirstChild("Interior")
	if old then old:Destroy() end
	local src = workspace.MistressFlat
	src:PivotTo(CFrame.new(origin) * CFrame.Angles(0, math.pi, 0))      -- FBX axis conversion: rotate 180 deg about Y around the flat origin
	local interior = Instance.new("Model") interior.Name = "Interior"
	local meshes = Instance.new("Folder") meshes.Name = "Meshes" meshes.Parent = interior
	local nO, nG, nN = 0, 0, 0
	for _, c in ipairs(src:GetChildren()) do
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
	src:Destroy()
	local function rel(x, y, z) return origin + Vector3.new(x, y, z) end
	local cols = Instance.new("Folder") cols.Name = "Colliders" cols.Parent = interior
	for _, r in ipairs(data.colliders) do
		local p = Instance.new("Part") p.Name = r[7] p.Anchored = true p.CanCollide = true p.Transparency = 1
		p.Size = Vector3.new(r[4], r[5], r[6]) p.Position = rel(r[1], r[2], r[3]) p.Parent = cols
	end
	for _, r in ipairs(data.cyl_colliders) do      -- {cx, cy, cz, diameter, height, name}
		local p = Instance.new("Part") p.Name = r[6] p.Shape = Enum.PartType.Cylinder p.Anchored = true p.CanCollide = true p.Transparency = 1
		p.Size = Vector3.new(r[5], r[4], r[4]) p.CFrame = CFrame.new(rel(r[1], r[2], r[3])) * CFrame.Angles(0, 0, math.pi / 2) p.Parent = cols
	end
	local lamps = Instance.new("Folder") lamps.Name = "Lights" lamps.Parent = interior
	for _, l in ipairs(data.lights) do
		local p = Instance.new("Part") p.Name = "Light" p.Anchored = true p.CanCollide = false p.CanQuery = false p.CanTouch = false p.Transparency = 1
		p.Size = Vector3.new(0.3, 0.3, 0.3) p.Position = rel(l[1], l[2], l[3])
		local pl = Instance.new("PointLight") pl.Range = l[4] pl.Brightness = l[5] * 0.4 pl.Color = Color3.fromRGB(255, 226, 170) pl.Shadows = false pl.Parent = p
		p.Parent = lamps
	end
	local signs = Instance.new("Folder") signs.Name = "Signs" signs.Parent = interior
	local faceOf = { S = Enum.NormalId.Back, N = Enum.NormalId.Front, E = Enum.NormalId.Right, W = Enum.NormalId.Left }
	local off = { Back = Vector3.new(0, 0, 0.9), Front = Vector3.new(0, 0, -0.9), Right = Vector3.new(0.9, 0, 0), Left = Vector3.new(-0.9, 0, 0) }
	for _, s in ipairs(data.signs) do
		local p = Instance.new("Part") p.Name = "Sign_" .. s.text p.Anchored = true p.CanCollide = false p.CanQuery = false p.Transparency = 1
		p.Size = Vector3.new(s.w, s.h, 0.2)
		local face = faceOf[s.face] or Enum.NormalId.Back
		p.Position = rel(s.x, s.y, s.z) + off[face.Name] * 0.3
		local g = Instance.new("SurfaceGui") g.Face = face g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud g.PixelsPerStud = 50 g.LightInfluence = 0 g.Parent = p
		local t = Instance.new("TextLabel") t.Size = UDim2.fromScale(1, 1) t.BackgroundTransparency = 1 t.Text = s.text t.TextScaled = true t.Font = Enum.Font.FredokaOne t.TextColor3 = Color3.fromRGB(60, 40, 20) t.Parent = g
		p.Parent = signs
	end
	local a = data.anchors
	local function mk(name, size, cf)
		local p = Instance.new("Part") p.Name = name p.Anchored = true p.CanCollide = false p.CanQuery = false p.Transparency = 1 p.Size = size p.CFrame = cf p.Parent = interior
		return p
	end
	local arr = a.arrival
	mk("Arrival", Vector3.new(4, 0.2, 4), CFrame.lookAt(rel(arr[1], arr[2], arr[3]), rel(arr[1] + arr[4], arr[2], arr[3] + arr[5])))
	local ed = a.exit_door
	local door = mk("ExitDoor", Vector3.new(6, 8, 0.8), CFrame.new(rel(ed[1], ed[2], ed[3])))
	CS:AddTag(door, "ApartmentExit")
	local ms = a.mistress_seat
	mk("MistressSeat", Vector3.new(1.5, 0.2, 1.5), CFrame.new(rel(ms[1], ms[2], ms[3])))
	local gs = a.guest_seat
	mk("GuestSeat", Vector3.new(1.5, 0.2, 1.5), CFrame.new(rel(gs[1], gs[2], gs[3])) * CFrame.Angles(0, math.pi, 0))
	local tt = a.table_top
	local top = Instance.new("Part") top.Name = "Table_Top" top.Shape = Enum.PartType.Cylinder top.Anchored = true top.CanCollide = false top.Transparency = 1
	top.Size = Vector3.new(0.5, 8.4, 8.4) top.CFrame = CFrame.new(rel(tt[1], tt[2], tt[3])) * CFrame.Angles(0, 0, math.pi / 2) top.Parent = interior
	top:SetAttribute("DadId", "RegularDad")
	CS:AddTag(top, "MistressDesk")
	interior.PrimaryPart = nil
	interior.Parent = building
	return string.format("O%d G%d N%d colliders %d+%d lights %d signs %d", nO, nG, nN, #data.colliders, #data.cyl_colliders, #data.lights, #data.signs)
end
