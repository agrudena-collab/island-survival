-- Clones the single realistic Rthro base rig (ServerStorage.DadBaseRig) and dresses it
-- per catalog entry using welded colored overlay parts (no custom body meshes, no
-- uploaded clothing textures). Server-only: ServerStorage is not visible to the client.
local ServerStorage = game:GetService("ServerStorage")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local DadCatalog = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("DadCatalog"))

local DadModelBuilder = {}

-- Finished, approved models live in ServerStorage under the catalog's ModelAsset name.
local function getFinalModel(assetName: string): Model
	local asset = ServerStorage:WaitForChild(assetName, 10)
	assert(asset and asset:IsA("Model"), `ServerStorage.{assetName} must be a Model (check default.project.json)`)
	return asset
end

local function getBaseRig(): Model
	local rig = ServerStorage:WaitForChild("DadBaseRig")
	assert(rig:IsA("Model"), "ServerStorage.DadBaseRig must be a Model")
	return rig
end

local function weldTo(model: Model, anchor: BasePart, part: BasePart)
	part.CanCollide = false
	part.CastShadow = false
	part.Parent = model
	local weld = Instance.new("WeldConstraint")
	weld.Part0 = anchor
	weld.Part1 = part
	weld.Parent = part
end

-- A flat colored plate welded to the front or back face of a body part (shirt/apron look).
local function platePart(model: Model, name: string, anchor: BasePart, color: BrickColor, material: Enum.Material, size: Vector3, localOffset: CFrame)
	local plate = Instance.new("Part")
	plate.Name = name
	plate.Size = size
	plate.BrickColor = color
	plate.Material = material
	plate.TopSurface = Enum.SurfaceType.Smooth
	plate.BottomSurface = Enum.SurfaceType.Smooth
	plate.CFrame = anchor.CFrame * localOffset
	weldTo(model, anchor, plate)
	return plate
end

-- A colored band wrapped around a limb (sleeve cuff / pant leg look).
local function bandPart(model: Model, name: string, anchor: BasePart, color: BrickColor, material: Enum.Material, heightFraction: number, radiusScale: number)
	local band = Instance.new("Part")
	band.Name = name
	band.Shape = Enum.PartType.Cylinder
	local radius = math.max(anchor.Size.X, anchor.Size.Z) / 2 * radiusScale
	band.Size = Vector3.new(anchor.Size.Y * heightFraction, radius * 2, radius * 2)
	band.BrickColor = color
	band.Material = material
	band.TopSurface = Enum.SurfaceType.Smooth
	band.BottomSurface = Enum.SurfaceType.Smooth
	band.CFrame = anchor.CFrame * CFrame.Angles(0, 0, math.rad(90))
	weldTo(model, anchor, band)
	return band
end

-- Dresses the torso (front + back shirt plates) and upper legs (pant bands).
local function dressBody(model: Model, definition)
	local theme = definition.ColorTheme
	local material = definition.AccentMaterial

	local upperTorso = model:FindFirstChild("UpperTorso")
	if upperTorso then
		local size = Vector3.new(upperTorso.Size.X * 0.88, upperTorso.Size.Y * 0.8, 0.1)
		platePart(model, "ShirtFront", upperTorso, theme.Shirt, material, size, CFrame.new(0, 0.05, -upperTorso.Size.Z / 2 - 0.02))
		platePart(model, "ShirtBack", upperTorso, theme.Shirt, material, size, CFrame.new(0, 0.05, upperTorso.Size.Z / 2 + 0.02))
	end

	for _, side in ipairs({ "Left", "Right" }) do
		local upperArm = model:FindFirstChild(side .. "UpperArm")
		if upperArm then
			bandPart(model, side .. "Sleeve", upperArm, theme.Shirt, material, 0.55, 1.12)
		end

		local upperLeg = model:FindFirstChild(side .. "UpperLeg")
		if upperLeg then
			bandPart(model, side .. "PantBand", upperLeg, theme.Pants, material, 0.9, 1.08)
		end

		local lowerLeg = model:FindFirstChild(side .. "LowerLeg")
		if lowerLeg then
			bandPart(model, side .. "PantCuff", lowerLeg, theme.Pants, material, 0.6, 1.1)
		end
	end
end

-- Builds a distinct silhouette on top of the head so dads read apart at a glance.
local function addHeadwear(model: Model, head: BasePart, material: Enum.Material, headwear)
	local headTop = head.Position.Y + head.Size.Y / 2

	if headwear.Kind == "Cap" then
		local crown = Instance.new("Part")
		crown.Name = "Headwear_Crown"
		crown.Size = Vector3.new(head.Size.X * 0.95, 0.5, head.Size.Z * 0.95)
		crown.BrickColor = headwear.Color
		crown.Material = material
		crown.CFrame = CFrame.new(head.Position.X, headTop + 0.25, head.Position.Z)
		weldTo(model, head, crown)

		local bill = Instance.new("Part")
		bill.Name = "Headwear_Bill"
		bill.Size = Vector3.new(head.Size.X * 0.5, 0.1, head.Size.Z * 0.4)
		bill.BrickColor = headwear.AccentColor or headwear.Color
		bill.Material = material
		bill.CFrame = CFrame.new(head.Position.X, headTop, head.Position.Z - head.Size.Z * 0.55)
		weldTo(model, head, bill)
	elseif headwear.Kind == "Brim" then
		local crownHeight = headwear.CrownHeight or 0.6
		local brimRadius = headwear.BrimRadius or (head.Size.X * 0.85)

		local crown = Instance.new("Part")
		crown.Name = "Headwear_Crown"
		crown.Shape = Enum.PartType.Cylinder
		crown.Size = Vector3.new(crownHeight, head.Size.X * 0.9, head.Size.X * 0.9)
		crown.BrickColor = headwear.Color
		crown.Material = material
		crown.CFrame = CFrame.new(head.Position.X, headTop + crownHeight / 2, head.Position.Z) * CFrame.Angles(0, 0, math.rad(90))
		weldTo(model, head, crown)

		local brim = Instance.new("Part")
		brim.Name = "Headwear_Brim"
		brim.Shape = Enum.PartType.Cylinder
		brim.Size = Vector3.new(0.15, brimRadius * 2, brimRadius * 2)
		brim.BrickColor = headwear.AccentColor or headwear.Color
		brim.Material = material
		brim.CFrame = CFrame.new(head.Position.X, headTop + 0.05, head.Position.Z) * CFrame.Angles(0, 0, math.rad(90))
		weldTo(model, head, brim)
	elseif headwear.Kind == "Band" then
		local band = Instance.new("Part")
		band.Name = "Headwear_Band"
		band.Size = Vector3.new(head.Size.X * 1.05, 0.3, head.Size.Z * 1.05)
		band.BrickColor = headwear.AccentColor or headwear.Color
		band.Material = material
		band.CFrame = CFrame.new(head.Position.X, head.Position.Y + head.Size.Y * 0.1, head.Position.Z)
		weldTo(model, head, band)
	elseif headwear.Kind == "Crown" then
		local base = Instance.new("Part")
		base.Name = "Headwear_CrownBase"
		base.Shape = Enum.PartType.Cylinder
		base.Size = Vector3.new(0.5, head.Size.X * 0.95, head.Size.X * 0.95)
		base.BrickColor = headwear.Color
		base.Material = material
		base.CFrame = CFrame.new(head.Position.X, headTop + 0.25, head.Position.Z) * CFrame.Angles(0, 0, math.rad(90))
		weldTo(model, head, base)

		for i = 0, 4 do
			local angle = (i / 5) * math.pi * 2
			local radius = head.Size.X * 0.35
			local spike = Instance.new("Part")
			spike.Name = "Headwear_Spike"
			spike.Size = Vector3.new(0.25, 0.5, 0.25)
			spike.BrickColor = headwear.AccentColor or headwear.Color
			spike.Material = Enum.Material.Neon
			spike.CFrame = CFrame.new(
				head.Position.X + math.cos(angle) * radius,
				headTop + 0.75,
				head.Position.Z + math.sin(angle) * radius
			)
			weldTo(model, head, spike)
		end
	end
end

function DadModelBuilder.Build(dadId: string): Model
	local definition = DadCatalog.GetById(dadId)
	assert(definition, `Unknown dad id: {dadId}`)

	local isFinal = definition.ModelAsset ~= nil
	local model = (if isFinal then getFinalModel(definition.ModelAsset) else getBaseRig()):Clone()
	model.Name = definition.Id

	local rootPart = model:FindFirstChild("HumanoidRootPart")
	if rootPart and rootPart:IsA("BasePart") then
		model.PrimaryPart = rootPart
	end

	local humanoid = model:FindFirstChildOfClass("Humanoid")
	if humanoid then
		humanoid.DisplayName = definition.DisplayName
	end

	if isFinal then
		-- Final model: pose, colours and held mug are baked into the asset; record where the feet are.
		local cf, size = model:GetBoundingBox()
		local root = model.PrimaryPart
		model:SetAttribute("FeetOffset", if root then root.Position.Y - (cf.Position.Y - size.Y / 2) else 0)
	else
		dressBody(model, definition)
	end

	local head = model:FindFirstChild("Head")
	if head then
		if definition.Headwear and not isFinal then
			addHeadwear(model, head, definition.AccentMaterial, definition.Headwear)
		end

		local nameTag = Instance.new("BillboardGui")
		nameTag.Name = "NameTag"
		nameTag.Size = UDim2.fromOffset(140, 32)
		nameTag.StudsOffset = Vector3.new(0, 1.2, 0)
		nameTag.MaxDistance = 40
		nameTag.AlwaysOnTop = true
		nameTag.Adornee = head
		nameTag.Parent = head

		local label = Instance.new("TextLabel")
		label.BackgroundTransparency = 1
		label.Size = UDim2.fromScale(1, 1)
		label.Font = Enum.Font.FredokaOne
		label.TextScaled = true
		label.TextColor3 = Color3.new(1, 1, 1)
		label.TextStrokeTransparency = 0.4
		label.Text = `{definition.DisplayName} ({definition.Rarity})`
		label.Parent = nameTag
	end

	local rightHand = model:FindFirstChild("RightHand")
	if rightHand and definition.Accessory and not isFinal then
		local accessory = definition.Accessory
		local prop = Instance.new("Part")
		prop.Name = accessory.Name
		prop.Size = accessory.Size
		prop.BrickColor = accessory.Color
		prop.Material = definition.AccentMaterial
		prop.Shape = if accessory.Shape == "Cylinder" then Enum.PartType.Cylinder else Enum.PartType.Block
		prop.CFrame = rightHand.CFrame * CFrame.new(0, -rightHand.Size.Y / 2 - accessory.Size.Y / 2, 0)
		weldTo(model, rightHand, prop)
	end

	return model
end

-- Moves the model to the given position (feet at the CFrame's Y) and freezes it there.
-- The rig's parts are unanchored by default, so without this physics can topple it.
function DadModelBuilder.PlaceAt(model: Model, cframe: CFrame)
	model:PivotTo(cframe * CFrame.new(0, model:GetAttribute("FeetOffset") or 0, 0))
	for _, descendant in ipairs(model:GetDescendants()) do
		if descendant:IsA("BasePart") then
			descendant.Anchored = true
		end
	end
end

-- Convenience for visual review: builds every catalog dad in a grid, spaced apart.
function DadModelBuilder.BuildAll(parent: Instance, spacing: number?): { Model }
	local gap = spacing or 10
	local columns = 4
	local models = {}
	for index, definition in ipairs(DadCatalog.List) do
		local model = DadModelBuilder.Build(definition.Id)
		model.Parent = parent
		local column = (index - 1) % columns
		local row = math.floor((index - 1) / columns)
		DadModelBuilder.PlaceAt(model, CFrame.new(column * gap, 0, row * gap))
		table.insert(models, model)
	end
	return models
end

return DadModelBuilder
