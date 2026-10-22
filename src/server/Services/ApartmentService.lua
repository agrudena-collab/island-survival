-- Mistress apartment buildings (md: «Снаружи ... большое здание. При приближении к входу появляется кнопка «Войти»; после
-- нажатия игрок телепортируется непосредственно в квартиру»; the flat has her table and a proper exit).
-- Data lives in the building model (assets/map/apartments/<id>/ -> MistressBuilding1):
--   Part tagged "ApartmentEntrance" (Exterior): the «Войти» prompt is created here; attribute ApartmentId.
--   Interior.Arrival: where the player appears (facing into the flat); Exterior.ExitArrival: where the exit door leads.
--   Part tagged "ApartmentExit" (Interior): the exit door; its prompt «Выйти» sends the player back outside.
-- Entering with the father in the bag is the delivery (HeistService.TryDeliver): blocked while the family still chases the
-- player, so the entrance only opens once the pursuit is over (md: «Сначала избавься от хвоста»).
-- Apartments are personal-looking but the md has not decided whether flats are shared between players; nothing here
-- instantiates per-player copies (open question 8), everyone enters the same interior.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")

local HeistService = require(script.Parent.HeistService)

local ApartmentService = {}

local MAX_DISTANCE = 14
local inside = {} -- [Player] = entrance Part they entered through

local function root(player)
	local character = player.Character
	return character and character:FindFirstChild("HumanoidRootPart")
end

local function near(player, part)
	local r = root(player)
	return r ~= nil and (r.Position - part.Position).Magnitude <= MAX_DISTANCE
end

-- the building model is the nearest ancestor that holds the Interior model
local function building(part)
	local node = part.Parent
	while node and not node:FindFirstChild("Interior") do
		node = node.Parent
	end
	return node
end

local function put(player, anchor)
	local r = root(player)
	if r and anchor then
		r.AssemblyLinearVelocity = Vector3.zero
		r.CFrame = anchor.CFrame + Vector3.new(0, 3.2, 0)
	end
end

local function bindEntrance(entrance)
	local prompt = entrance:FindFirstChildOfClass("ProximityPrompt") or Instance.new("ProximityPrompt")
	prompt.ActionText = "Войти"
	prompt.ObjectText = "Квартира"
	prompt.MaxActivationDistance = 10
	prompt.RequiresLineOfSight = false
	prompt.Parent = entrance
	prompt.Triggered:Connect(function(player)
		if inside[player] or not near(player, entrance) then
			return
		end
		local model = building(entrance)
		local arrival = model and model:FindFirstChild("Arrival", true)
		if not arrival then
			return
		end
		if HeistService.TryDeliver(player) == "blocked" then
			return -- the hint «Сначала избавься от хвоста» is already shown
		end
		inside[player] = entrance
		put(player, arrival)
	end)
end

local function bindExit(door)
	local prompt = door:FindFirstChildOfClass("ProximityPrompt") or Instance.new("ProximityPrompt")
	prompt.ActionText = "Выйти"
	prompt.ObjectText = "Дверь"
	prompt.MaxActivationDistance = 9
	prompt.RequiresLineOfSight = false
	prompt.Parent = door
	prompt.Triggered:Connect(function(player)
		local entrance = inside[player]
		if not entrance or not near(player, door) then
			return
		end
		local model = building(door)
		local exitArrival = model and model:FindFirstChild("ExitArrival", true)
		inside[player] = nil
		put(player, exitArrival)
	end)
end

function ApartmentService.Initialize()
	for _, part in ipairs(CollectionService:GetTagged("ApartmentEntrance")) do
		bindEntrance(part)
	end
	CollectionService:GetInstanceAddedSignal("ApartmentEntrance"):Connect(bindEntrance)
	for _, part in ipairs(CollectionService:GetTagged("ApartmentExit")) do
		bindExit(part)
	end
	CollectionService:GetInstanceAddedSignal("ApartmentExit"):Connect(bindExit)
	Players.PlayerRemoving:Connect(function(player)
		inside[player] = nil
	end)
	-- a new body after a reset appears outside again
	Players.PlayerAdded:Connect(function(player)
		player.CharacterAdded:Connect(function()
			inside[player] = nil
		end)
	end)
end

function ApartmentService.IsInside(player)
	return inside[player] ~= nil
end

return ApartmentService
