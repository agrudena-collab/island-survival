--!nocheck
-- Builds the first mistress' apartment building (Regular Dad's mistress): a multi-storey building outside and her flat inside.
-- Studio ModuleScript source; call `require(module)(parent, interiorOrigin, exteriorOrigin)` in Edit mode.
-- md: outside = a big building model, near the entrance a «Войти» prompt; pressing it teleports the player into her flat;
-- the flat has the table she sits at (the player walks there, the dialogue starts) and a proper exit.
-- Style: the bright toy palette chosen for the Regular Dad house. Layout numbers are prototype values, not an approved plan.
local CS = game:GetService("CollectionService")

local C = {
	wall = Color3.fromRGB(250, 235, 205), accent = Color3.fromRGB(63, 184, 168), wood = Color3.fromRGB(201, 139, 78),
	dark = Color3.fromRGB(110, 70, 45), rug = Color3.fromRGB(232, 104, 90), sofa = Color3.fromRGB(242, 182, 58),
	chair = Color3.fromRGB(214, 69, 69), cab = Color3.fromRGB(255, 244, 222), counter = Color3.fromRGB(90, 150, 200),
	glass = Color3.fromRGB(150, 205, 240), curtain = Color3.fromRGB(63, 167, 255), plant = Color3.fromRGB(80, 170, 70),
	pot = Color3.fromRGB(190, 90, 60), brick = Color3.fromRGB(226, 120, 96), trim = Color3.fromRGB(255, 255, 255),
	roof = Color3.fromRGB(96, 98, 112), door = Color3.fromRGB(22, 184, 154), light = Color3.fromRGB(255, 240, 200),
}

return function(parent, I, E)
	local model = Instance.new("Model")
	model.Name = "MistressBuilding1"
	model.Parent = parent
	local interior = Instance.new("Model") interior.Name = "Interior" interior.Parent = model
	local exterior = Instance.new("Model") exterior.Name = "Exterior" exterior.Parent = model

	local function part(host, name, pos, size, color, material, opts)
		local p = Instance.new("Part")
		p.Name, p.Anchored, p.Size, p.Position = name, true, size, pos
		p.Color, p.Material = color, material or Enum.Material.SmoothPlastic
		p.TopSurface, p.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
		opts = opts or {}
		if opts.shape then p.Shape = opts.shape end
		if opts.collide == false then p.CanCollide = false end
		if opts.transparency then p.Transparency = opts.transparency end
		if opts.rot then p.CFrame = CFrame.new(pos) * CFrame.Angles(0, math.rad(opts.rot), 0) end
		p.Parent = host
		return p
	end
	local function box(host, name, cx, y0, cz, w, h, d, color, material, opts)
		return part(host, name, Vector3.new(cx, y0 + h / 2, cz), Vector3.new(w, h, d), color, material, opts)
	end
	local function light(p, range, brightness)
		local l = Instance.new("PointLight") l.Range, l.Brightness, l.Color = range, brightness, C.light l.Parent = p
	end

	------------------------------------------------------------------------------------------------------------
	-- interior: 44 x 32 studs, 11 high, floor top at I.Y + 1
	------------------------------------------------------------------------------------------------------------
	local ix, iy, iz = I.X, I.Y, I.Z
	local fy = iy + 1
	local H = 11
	box(interior, "Floor", ix, iy, iz, 46, 1, 34, C.wood, Enum.Material.WoodPlanks)
	box(interior, "Ceiling", ix, fy + H, iz, 46, 1, 34, C.wall)
	-- walls (thickness 1). North = window wall, south = entrance wall with the exit door opening at x -14 (width 6, height 8)
	box(interior, "Wall_W", ix - 22.5, fy, iz, 1, H, 34, C.wall)
	box(interior, "Wall_E", ix + 22.5, fy, iz, 1, H, 34, C.accent)
	box(interior, "Wall_S_L", ix - 20, fy, iz + 16.5, 6, H, 1, C.wall)   -- x -23..-17, left of the door opening
	box(interior, "Wall_S_R", ix + 6, fy, iz + 16.5, 34, H, 1, C.wall)   -- x -11..23, right of the opening
	box(interior, "Wall_S_Head", ix - 14, fy + 8, iz + 16.5, 6, H - 8, 1, C.wall)
	-- window wall with a big opening x -14..14, y 3..9
	box(interior, "Wall_N_L", ix - 18.5, fy, iz - 16.5, 8, H, 1, C.accent)
	box(interior, "Wall_N_R", ix + 18.5, fy, iz - 16.5, 8, H, 1, C.accent)
	box(interior, "Wall_N_Low", ix, fy, iz - 16.5, 29, 3, 1, C.accent)
	box(interior, "Wall_N_High", ix, fy + 9, iz - 16.5, 29, H - 9, 1, C.accent)
	box(interior, "Window_Glass", ix, fy + 3, iz - 16.5, 29, 6, 0.3, C.glass, Enum.Material.Glass, { transparency = 0.6, collide = true })
	for _, x in ipairs({ -14, -4.7, 4.7, 14 }) do
		box(interior, "Window_Mullion", ix + x, fy + 3, iz - 16.5, 0.8, 6, 0.6, C.trim)
	end
	box(interior, "Window_Sill", ix, fy + 2.7, iz - 15.8, 30, 0.4, 1.6, C.trim)
	-- curtains
	box(interior, "Curtain_L", ix - 15.6, fy + 1.5, iz - 15.6, 2.4, 8.5, 0.6, C.curtain, Enum.Material.Fabric, { collide = false })
	box(interior, "Curtain_R", ix + 15.6, fy + 1.5, iz - 15.6, 2.4, 8.5, 0.6, C.curtain, Enum.Material.Fabric, { collide = false })
	box(interior, "Curtain_Rod", ix, fy + 10, iz - 15.6, 34, 0.3, 0.3, C.dark, Enum.Material.Wood, { collide = false })
	-- toy skyline behind the window (decoration, outside the flat)
	local skyline = { { -26, 14, 10 }, { -12, 22, 9 }, { 2, 17, 12 }, { 16, 26, 10 }, { 30, 15, 11 } }
	for i, s in ipairs(skyline) do
		local col = ({ C.brick, C.counter, C.sofa, C.accent, C.chair })[(i % 5) + 1]
		box(interior, "Skyline_" .. i, ix + s[1], fy - 1, iz - 34, s[3], s[2], 8, col, Enum.Material.SmoothPlastic, { collide = false })
	end
	box(interior, "SkylineSky", ix, fy - 2, iz - 40, 90, 50, 1, Color3.fromRGB(170, 215, 245), Enum.Material.SmoothPlastic, { collide = false })

	-- exit door (in the south wall opening) and the arrival point
	local door = box(interior, "ExitDoor", ix - 14, fy, iz + 16.5, 6, 8, 0.6, C.door, Enum.Material.Wood)
	door.CanCollide = false
	local doorFrame = box(interior, "ExitDoor_Frame", ix - 14, fy + 8, iz + 16.3, 6.6, 0.6, 0.9, C.trim)
	local arrival = box(interior, "Arrival", ix - 14, fy, iz + 12, 4, 0.2, 4, C.light, Enum.Material.SmoothPlastic, { collide = false, transparency = 1 })
	arrival.CFrame = CFrame.new(arrival.Position) * CFrame.Angles(0, math.pi, 0) -- facing north (-Z), into the flat
	CS:AddTag(door, "ApartmentExit")
	-- hall rug and shoe rack
	box(interior, "HallRug", ix - 14, fy, iz + 11.5, 6, 0.15, 8, C.rug, Enum.Material.Fabric, { collide = false })
	box(interior, "ShoeRack", ix - 19.5, fy, iz + 14, 3, 1.6, 1.4, C.wood, Enum.Material.Wood)
	box(interior, "CoatHooks", ix - 21.8, fy + 6, iz + 12, 0.5, 0.5, 5, C.dark, Enum.Material.Wood, { collide = false })

	-- dining area: round table where she sits (north) and a free chair for the player (south)
	local tx, tz = ix + 2, iz - 5
	box(interior, "DiningRug", tx, fy, tz, 14, 0.15, 14, C.rug, Enum.Material.Fabric, { collide = false })
	local top = part(interior, "Table_Top", Vector3.new(tx, fy + 2.9, tz), Vector3.new(0.5, 8.4, 8.4), C.dark, Enum.Material.Wood, { shape = Enum.PartType.Cylinder })
	top.CFrame = CFrame.new(tx, fy + 2.9, tz) * CFrame.Angles(0, 0, math.pi / 2)
	local leg = part(interior, "Table_Leg", Vector3.new(tx, fy + 1.4, tz), Vector3.new(2.8, 1.6, 1.6), C.dark, Enum.Material.Wood, { shape = Enum.PartType.Cylinder })
	leg.CFrame = CFrame.new(tx, fy + 1.4, tz) * CFrame.Angles(0, 0, math.pi / 2)
	box(interior, "Table_Base", tx, fy, tz, 4, 0.4, 4, C.dark, Enum.Material.Wood)
	-- tea set on the table
	box(interior, "Teapot", tx - 0.6, fy + 3.15, tz + 0.4, 1.3, 1.2, 1.3, C.chair, Enum.Material.SmoothPlastic)
	box(interior, "Cup_A", tx + 1.8, fy + 3.15, tz - 1.2, 0.8, 0.7, 0.8, C.trim, Enum.Material.SmoothPlastic)
	box(interior, "Cup_B", tx - 1.8, fy + 3.15, tz + 1.8, 0.8, 0.7, 0.8, C.trim, Enum.Material.SmoothPlastic)
	local function chair(name, cx, cz, faceSouth)
		local dz = faceSouth and -1 or 1 -- the backrest sits behind the sitter
		box(interior, name .. "_Seat", cx, fy + 1.5, cz, 2.6, 0.5, 2.6, C.chair, Enum.Material.Fabric)
		box(interior, name .. "_Back", cx, fy + 2.0, cz + dz * 1.2, 2.6, 3, 0.4, C.chair, Enum.Material.Fabric)
		for _, lx in ipairs({ -1, 1 }) do
			for _, lz in ipairs({ -1, 1 }) do
				box(interior, name .. "_Leg", cx + lx * 1.1, fy, cz + lz * 1.1, 0.3, 1.5, 0.3, C.dark, Enum.Material.Wood)
			end
		end
	end
	chair("MistressChair", tx, tz - 5.6, true)
	chair("GuestChair", tx, tz + 5.6, false)
	local seat = box(interior, "MistressSeat", tx, fy + 1.8, tz - 5.6, 1.5, 0.2, 1.5, C.light, Enum.Material.SmoothPlastic, { collide = false, transparency = 1 })
	seat.CFrame = CFrame.new(seat.Position) * CFrame.Angles(0, 0, 0) -- she faces +Z (towards the player)
	-- the desk the dialogue hangs on: the table top itself, with the mistress' father id
	top:SetAttribute("DadId", "RegularDad")
	CS:AddTag(top, "MistressDesk")

	-- kitchen along the west wall
	for i = 0, 3 do
		box(interior, "Kitchen_Base_" .. i, ix - 20.8, fy, iz - 13.5 + i * 3, 2.4, 3.2, 2.9, C.cab, Enum.Material.SmoothPlastic)
	end
	box(interior, "Kitchen_Counter", ix - 20.8, fy + 3.2, iz - 12, 2.6, 0.4, 12.4, C.counter, Enum.Material.Marble)
	box(interior, "Kitchen_Upper", ix - 21.2, fy + 6, iz - 13.5, 1.6, 2.6, 9, C.cab, Enum.Material.SmoothPlastic)
	box(interior, "Fridge", ix - 20.6, fy, iz - 1.2, 2.6, 6.8, 2.6, C.trim, Enum.Material.Metal)
	box(interior, "Stove_Top", ix - 20.8, fy + 3.6, iz - 9, 2, 0.15, 2.4, Color3.fromRGB(40, 40, 46), Enum.Material.Metal, { collide = false })
	box(interior, "Fruit_Bowl", ix - 20.8, fy + 3.6, iz - 12.8, 1.4, 0.8, 1.4, C.chair, Enum.Material.SmoothPlastic, { collide = false })

	-- living area (east): rug, sofa along the east wall, coffee table, TV unit, bookshelf
	box(interior, "LivingRug", ix + 14.5, fy, iz + 6, 12, 0.15, 10, C.accent, Enum.Material.Fabric, { collide = false })
	box(interior, "Sofa_Base", ix + 19.6, fy, iz + 6, 3.4, 1.6, 9, C.sofa, Enum.Material.Fabric)
	box(interior, "Sofa_Back", ix + 21.2, fy + 1.6, iz + 6, 0.8, 2.4, 9, C.sofa, Enum.Material.Fabric)
	box(interior, "Sofa_ArmN", ix + 19.6, fy + 1.6, iz + 10.6, 3.4, 1.3, 0.9, C.sofa, Enum.Material.Fabric)
	box(interior, "Sofa_ArmS", ix + 19.6, fy + 1.6, iz + 1.4, 3.4, 1.3, 0.9, C.sofa, Enum.Material.Fabric)
	for i = 1, 3 do
		box(interior, "Pillow_" .. i, ix + 19.4, fy + 1.6, iz + 3 + i * 2.2, 1.2, 1.2, 1.4, ({ C.chair, C.accent, C.trim })[i], Enum.Material.Fabric, { collide = false })
	end
	box(interior, "CoffeeTable", ix + 14.2, fy + 1.1, iz + 6, 3, 0.4, 5, C.dark, Enum.Material.Wood)
	for _, lz in ipairs({ -1.9, 1.9 }) do
		box(interior, "CoffeeTable_Leg", ix + 14.2, fy, iz + 6 + lz, 2.4, 1.1, 0.4, C.dark, Enum.Material.Wood)
	end
	box(interior, "TV_Unit", ix + 7, fy, iz + 15, 9, 2.2, 1.8, C.wood, Enum.Material.Wood)
	box(interior, "TV", ix + 7, fy + 2.2, iz + 15.2, 6.4, 3.8, 0.4, Color3.fromRGB(20, 22, 28), Enum.Material.SmoothPlastic)
	box(interior, "Bookshelf", ix + 14, fy, iz + 15.5, 5, 7, 1.2, C.wood, Enum.Material.Wood)
	for r = 0, 3 do
		for b = 0, 3 do
			box(interior, "Book", ix + 12.4 + b * 1.1, fy + 0.9 + r * 1.6, iz + 15, 0.8, 1.2, 0.8, ({ C.chair, C.accent, C.sofa, C.counter })[(b + r) % 4 + 1], Enum.Material.SmoothPlastic, { collide = false })
		end
	end
	-- bedroom door (closed prop) in the east wall and decor
	box(interior, "BedroomDoor", ix + 22, fy, iz - 8, 0.6, 8, 4, C.door, Enum.Material.Wood)
	box(interior, "BedroomDoor_Frame", ix + 21.9, fy + 8, iz - 8, 0.9, 0.6, 5, C.trim)
	local pic = { C.sofa, C.chair, C.counter }
	for i = 1, 3 do
		box(interior, "Picture_" .. i, ix + 22, fy + 5, iz + 2.5 + i * 3.4, 0.4, 3, 2.4, pic[i], Enum.Material.SmoothPlastic, { collide = false })
	end
	local function plant(name, x, z)
		part(interior, name .. "_Pot", Vector3.new(x, fy + 0.9, z), Vector3.new(1.8, 1.8, 1.8), C.pot, Enum.Material.SmoothPlastic, { shape = Enum.PartType.Cylinder })
		part(interior, name .. "_Leaves", Vector3.new(x, fy + 3.2, z), Vector3.new(3, 3, 3), C.plant, Enum.Material.Grass, { shape = Enum.PartType.Ball, collide = false })
	end
	plant("PlantA", ix - 19, iz - 14.5)
	plant("PlantB", ix + 18.5, iz - 14.5)
	plant("PlantC", ix - 8, iz + 15)
	-- floor lamp and ceiling lights
	box(interior, "FloorLamp_Pole", ix + 9.5, fy, iz + 12, 0.3, 6, 0.3, C.dark, Enum.Material.Metal)
	local lamp = part(interior, "FloorLamp_Shade", Vector3.new(ix + 9.5, fy + 6.4, iz + 12), Vector3.new(2, 1.6, 2), C.light, Enum.Material.Neon, { collide = false })
	light(lamp, 16, 1.2)
	for i, p in ipairs({ { -10, -4 }, { 8, -4 }, { -10, 8 }, { 8, 8 } }) do
		local cl = box(interior, "CeilingLight_" .. i, ix + p[1], fy + H - 0.5, iz + p[2], 3, 0.4, 3, C.light, Enum.Material.Neon, { collide = false })
		light(cl, 22, 0.9)
	end

	------------------------------------------------------------------------------------------------------------
	-- exterior: lobby + 8-storey tower, 30 x 24 footprint, front (entrance) towards +Z
	------------------------------------------------------------------------------------------------------------
	local ex, ey, ez = E.X, E.Y, E.Z
	local W, D, FL, N = 30, 24, 11, 8
	box(exterior, "Plinth", ex, ey, ez + 4, W + 10, 1, D + 18, Color3.fromRGB(205, 200, 195), Enum.Material.Concrete) -- also carries the entrance, bench and exit arrival
	local by = ey + 1
	-- tower shell (solid mass, decoration: the real flat is the Interior model)
	box(exterior, "Tower", ex, by, ez, W, FL * N, D, C.brick, Enum.Material.Brick)
	box(exterior, "Lobby_Glass", ex, by, ez + D / 2 + 0.2, W - 6, 9, 0.6, C.glass, Enum.Material.Glass, { transparency = 0.45, collide = false })
	box(exterior, "Corner_L", ex - W / 2, by, ez, 1.6, FL * N, D + 0.6, C.trim)
	box(exterior, "Corner_R", ex + W / 2, by, ez, 1.6, FL * N, D + 0.6, C.trim)
	for f = 1, N - 1 do
		box(exterior, "FloorBand_" .. f, ex, by + f * FL - 0.5, ez, W + 1, 1, D + 1, C.trim, Enum.Material.SmoothPlastic, { collide = false })
		for k = -2, 2 do
			if not (f == 0) then
				box(exterior, "Window_" .. f .. "_" .. k, ex + k * 5.4, by + f * FL + 3, ez + D / 2 + 0.1, 3.4, 4.6, 0.4, C.glass, Enum.Material.Glass, { transparency = 0.35, collide = false })
				box(exterior, "Shutter_" .. f .. "_" .. k, ex + k * 5.4, by + f * FL + 3, ez + D / 2 + 0.25, 4.4, 5.4, 0.2, C.curtain, Enum.Material.SmoothPlastic, { collide = false })
			end
		end
	end
	box(exterior, "RoofSlab", ex, by + FL * N, ez, W + 2, 1.4, D + 2, C.roof, Enum.Material.Concrete)
	box(exterior, "RoofTank", ex + 7, by + FL * N + 1.4, ez - 5, 6, 5, 6, C.accent, Enum.Material.Metal)
	box(exterior, "Sign_Post", ex, by + FL * N + 1.4, ez + D / 2 - 1, 22, 5, 0.8, C.chair, Enum.Material.SmoothPlastic)
	local sign = exterior:FindFirstChild("Sign_Post")
	local gui = Instance.new("SurfaceGui") gui.Face = Enum.NormalId.Front gui.Parent = sign
	local lbl = Instance.new("TextLabel") lbl.Size = UDim2.fromScale(1, 1) lbl.BackgroundTransparency = 1 lbl.Text = "APARTMENTS" lbl.TextColor3 = C.trim lbl.Font = Enum.Font.FredokaOne lbl.TextScaled = true lbl.Parent = gui
	-- entrance
	box(exterior, "Door_Frame", ex, by, ez + D / 2 + 0.2, 8, 9, 0.8, C.trim)
	local ed = box(exterior, "EntranceDoor", ex, by, ez + D / 2 + 0.7, 6, 8, 0.4, C.door, Enum.Material.Wood)
	ed.CanCollide = false
	box(exterior, "Awning", ex, by + 10, ez + D / 2 + 3, 16, 0.6, 6, C.chair, Enum.Material.Fabric, { collide = false })
	for _, sx in ipairs({ -7.5, 7.5 }) do
		box(exterior, "Awning_Post", ex + sx, by, ez + D / 2 + 5.4, 0.5, 10, 0.5, C.dark, Enum.Material.Wood)
	end
	local entrance = box(exterior, "Entrance", ex, by, ez + D / 2 + 2.4, 6, 8, 1, C.light, Enum.Material.SmoothPlastic, { collide = false, transparency = 1 })
	entrance:SetAttribute("ApartmentId", "RegularDadMistress")
	CS:AddTag(entrance, "ApartmentEntrance")
	local exitArrival = box(exterior, "ExitArrival", ex, by, ez + D / 2 + 7, 4, 0.2, 4, C.light, Enum.Material.SmoothPlastic, { collide = false, transparency = 1 })
	exitArrival.CFrame = CFrame.new(exitArrival.Position) * CFrame.Angles(0, 0, 0)
	for _, sx in ipairs({ -12, 12 }) do
		part(exterior, "PlanterPot", Vector3.new(ex + sx, by + 0.9, ez + D / 2 + 3), Vector3.new(2.2, 1.8, 2.2), C.pot, Enum.Material.SmoothPlastic, { shape = Enum.PartType.Cylinder })
		part(exterior, "PlanterLeaves", Vector3.new(ex + sx, by + 3.2, ez + D / 2 + 3), Vector3.new(3.4, 3.4, 3.4), C.plant, Enum.Material.Grass, { shape = Enum.PartType.Ball, collide = false })
	end
	local bench = box(exterior, "Bench", ex + 14, by, ez + D / 2 + 6, 5, 1.6, 1.6, C.wood, Enum.Material.Wood)
	return model
end
