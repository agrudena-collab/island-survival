-- Places the Regular Dad family house into its own district, apart from the mistress district.
-- md/owner decision 2026-10-24: the father district and the mistress district are two separate districts that will be
-- joined by roads and a forest biome; the father district sits east of the mistress district with a ~400 stud gap.
-- The house model keeps its authored coordinates (lot x 0..98.6, z -60..39.4, pivot at the origin of the generator);
-- it is cloned from ServerStorage and shifted by LOT_OFFSET before it enters Workspace, so every tag binder
-- (HouseInteractionService, FamilyNpcService, HeistService) sees the final positions.
local CollectionService = game:GetService("CollectionService")
local ServerStorage = game:GetService("ServerStorage")

local FatherDistrictService = {}

local HOUSE_TEMPLATE = "RegularDadHouseFinal"
local HOUSE_NAME = "RegularDadHouse_V2_Final"
-- The house model carries its own street (24 wide, along z = 123 in model space, x -70..179). The offset puts the west end of that
-- street at x = 5550 on z = 0, exactly where the forest road ends (ForestRoad gate B), so the road continues into the street.
local LOT_OFFSET = Vector3.new(5620, 0, -123) -- lot centre (49.3, -10.3) -> about (5669, -133)
local GROUND_TOP = 1.0 -- same walking height as Colliders.ground of the mistress district
local GROUND_THICKNESS = 5

-- Attributes written by the house build that hold world positions (door hinges and closed poses).
-- Direction attributes (InsideDir) must NOT be shifted.
local CFRAME_ATTRIBUTES = { "ClosedCFrame" }
local POSITION_ATTRIBUTES = { "Hinge" }

local function shiftHouse(house)
	for _, instance in ipairs(house:GetDescendants()) do
		if instance:IsA("BasePart") then
			instance.CFrame += LOT_OFFSET
		end
		for _, name in ipairs(CFRAME_ATTRIBUTES) do
			local value = instance:GetAttribute(name)
			if typeof(value) == "CFrame" then
				instance:SetAttribute(name, value + LOT_OFFSET)
			end
		end
		for _, name in ipairs(POSITION_ATTRIBUTES) do
			local value = instance:GetAttribute(name)
			if typeof(value) == "Vector3" then
				instance:SetAttribute(name, value + LOT_OFFSET)
			end
		end
	end
end

local function addGround(house)
	local boxCFrame, boxSize = house:GetBoundingBox()
	local ground = Instance.new("Part")
	ground.Name = "FatherDistrictGround"
	ground.Anchored = true
	ground.CanCollide = true
	ground.CanQuery = true
	ground.CanTouch = false
	ground.Transparency = 1
	ground.Size = Vector3.new(boxSize.X + 40, GROUND_THICKNESS, boxSize.Z + 40)
	ground.Position = Vector3.new(boxCFrame.Position.X, GROUND_TOP - GROUND_THICKNESS / 2, boxCFrame.Position.Z)
	ground.Parent = house
end

function FatherDistrictService.Initialize()
	if workspace:FindFirstChild(HOUSE_NAME) then
		return -- a hand-placed copy (Studio test place) wins
	end
	local template = ServerStorage:FindFirstChild(HOUSE_TEMPLATE)
	if not template then
		warn("FatherDistrictService: ServerStorage." .. HOUSE_TEMPLATE .. " is missing")
		return
	end
	local house = template:Clone()
	house.Name = HOUSE_NAME
	shiftHouse(house)
	-- the saved house model carries no tags: HeistService finds the father by FamilyFather and FamilyNpcService the house by FamilyHouse
	CollectionService:AddTag(house, "FamilyHouse")
	local father = house:FindFirstChild("RegularDad_Father")
	if father then
		CollectionService:AddTag(father, "FamilyFather")
		father:SetAttribute("DadId", "RegularDad")
	end
	addGround(house)
	house.Parent = workspace
end

return FatherDistrictService
