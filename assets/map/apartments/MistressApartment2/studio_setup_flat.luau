--!nocheck
-- Studio ModuleScript source (Edit mode): turns the freshly imported FBX model `Workspace.MistressFlat2` into the Interior of a MistressBuilding2.
-- Usage: ModuleScript.Source = <this file>; require(module)(source, building, origin)
--   source    the text of out/flat.json or an http(s) URL that serves it
--   building  the MistressBuilding2 model (it holds Exterior; the old Interior, if any, is replaced)
--   origin    Vector3 of the flat origin; the generator coordinates are relative to it (floor top = origin.Y + 1)
-- Contract with ApartmentService / DialogueService (same as flat 1): Interior.Arrival, a part tagged ApartmentExit (the door prompt), a part tagged MistressDesk
-- (attribute DadId = OfficeDad), MistressSeat, GuestSeat.  Meshes: white colour, SmoothPlastic / Glass 0.55 / Neon per chunk kind (O_ / G_ / N_), no collision.
local HS = game:GetService("HttpService")
local CS = game:GetService("CollectionService")

return function(source, building, origin)
	local text = source
	if not source:match("^%s*{") then text = HS:GetAsync(source) end
	local data = HS:JSONDecode(text)
	local old = building:FindFirstChild("Interior")
	if old then old:Destroy() end
	local src = workspace:FindFirstChild("MistressFlat2")
	assert(src, "import the FBX first: it must appear as Workspace.MistressFlat2")
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
	local a = data.anchors
	local function mk(name, size, cf)
		local p = Instance.new("Part") p.Name = name p.Anchored = true p.CanCollide = false p.CanQuery = true p.Transparency = 1 p.Size = size p.CFrame = cf p.Parent = interior
		return p
	end
	local arr = a.arrival
	mk("Arrival", Vector3.new(4, 0.2, 4), CFrame.lookAt(rel(arr[1], arr[2], arr[3]), rel(arr[1] + arr[4], arr[2], arr[3] + arr[5])))
	local ed = a.exit_door
	local door = mk("ExitDoor", Vector3.new(6, 8, 0.8), CFrame.new(rel(ed[1], ed[2], ed[3])))
	CS:AddTag(door, "ApartmentExit")
	local ms = a.mistress_seat
	mk("MistressSeat", Vector3.new(1.5, 0.2, 1.5), CFrame.lookAt(rel(ms[1], ms[2], ms[3]), rel(ms[1] + ms[4], ms[2], ms[3] + ms[5])))
	local gs = a.guest_seat
	mk("GuestSeat", Vector3.new(1.5, 0.2, 1.5), CFrame.lookAt(rel(gs[1], gs[2], gs[3]), rel(gs[1] + gs[4], gs[2], gs[3] + gs[5])))
	local tt = a.table_top
	local top = Instance.new("Part") top.Name = "Table_Top" top.Anchored = true top.CanCollide = false top.Transparency = 1
	top.Size = Vector3.new(12.4, 0.5, 5.2) top.CFrame = CFrame.new(rel(tt[1], tt[2], tt[3]))
	top:SetAttribute("DadId", "OfficeDad")
	CS:AddTag(top, "MistressDesk")
	top.Parent = interior
	interior.PrimaryPart = nil
	interior.Parent = building
	return string.format("O%d G%d N%d colliders %d+%d lights %d", nO, nG, nN, #data.colliders, #data.cyl_colliders, #data.lights)
end
