-- Gym training (md: «Автоматическое занятие дорожки и выход прыжком», «Сила, гантель и перенос мешка»). The Gym building
-- is not built yet, so everything is driven by tagged parts and works wherever those parts are placed.
--
-- Treadmill: a Part tagged "Treadmill" (the belt; its top surface is the running surface) with an optional child Part/Attachment
-- named "StandPoint". Stepping onto it snaps the player to the stand point, facing along the belt's LookVector, and starts
-- training: attribute `TrainingTreadmill` = true, the client runs in place (TreadmillController) while the belt carries the
-- player backwards, RunStat grows steadily with no start button. A normal jump ends it. The same treadmill does not grab the
-- player again until they have left its zone (touch ended) and entered it anew.
--
-- Dumbbell: a Part tagged "DumbbellShop" sells a Tool named "Dumbbell" (price is a prototype value); the tool appears in the
-- normal backpack row, equipping it starts automatic repeated lifts and StrengthStat grows while it stays in hand.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local GymService = {}

-- PROVISIONAL: the md does not set progress rates, price or zone sizes.
local CONFIG = {
	RunPerSecond = 1,
	StrengthPerLift = 1,
	LiftInterval = 1.4,
	DumbbellPrice = 25,
	BeltSpeed = 14,        -- studs/s the belt carries the player backwards (matches the run speed on the spot)
	SnapHeight = 3,
}

local training = {}  -- [Player] = { belt, zone connection data }
local inZone = {}    -- [Player] = { [belt] = true }  zones the player currently touches
local blocked = {}   -- [Player] = { [belt] = true }  zones the player left by jumping: not grabbed again until they exit them
local lifting = {}   -- [Player] = true while a dumbbell loop runs

local function playerFromPart(part)
	local character = part:FindFirstAncestorOfClass("Model")
	return character and Players:GetPlayerFromCharacter(character), character
end

local function humanoidOf(player)
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	return humanoid and humanoid.Health > 0 and humanoid or nil, character
end

local function standCFrame(belt)
	local stand = belt:FindFirstChild("StandPoint")
	local base = stand and (stand:IsA("Attachment") and stand.WorldCFrame or stand.CFrame) or (belt.CFrame * CFrame.new(0, belt.Size.Y / 2, 0))
	local look = belt.CFrame.LookVector
	return CFrame.lookAt(base.Position + Vector3.new(0, CONFIG.SnapHeight, 0), base.Position + Vector3.new(0, CONFIG.SnapHeight, 0) + Vector3.new(look.X, 0, look.Z))
end

-- ------------------------------------------------------------------------------------------------------------
-- treadmill
-- ------------------------------------------------------------------------------------------------------------
local function stopTraining(player, jumpedOff)
	local t = training[player]
	if not t then
		return
	end
	training[player] = nil
	player:SetAttribute("TrainingTreadmill", false)
	t.belt.AssemblyLinearVelocity = Vector3.zero
	if jumpedOff then
		blocked[player] = blocked[player] or {}
		blocked[player][t.belt] = true -- no re-capture until the player has left the zone and comes back
	end
	if t.conn then
		t.conn:Disconnect()
	end
end

local function startTraining(player, belt)
	if training[player] then
		return
	end
	local humanoid, character = humanoidOf(player)
	if not humanoid then
		return
	end
	local root = character.HumanoidRootPart
	root.CFrame = standCFrame(belt) -- a local placement on the machine, not a teleport to another room
	local backwards = -belt.CFrame.LookVector
	belt.AssemblyLinearVelocity = Vector3.new(backwards.X, 0, backwards.Z) * CONFIG.BeltSpeed
	local conn = humanoid.StateChanged:Connect(function(_, new)
		if new == Enum.HumanoidStateType.Jumping then
			stopTraining(player, true)
		end
	end)
	training[player] = { belt = belt, conn = conn, last = os.clock() }
	player:SetAttribute("TrainingTreadmill", true)
	player:SetAttribute("TreadmillForward", belt.CFrame.LookVector)
end

local function bindTreadmill(belt)
	belt.Anchored = true
	belt.Touched:Connect(function(other)
		local player = playerFromPart(other)
		if not player or other.Name ~= "HumanoidRootPart" and other.Name ~= "LowerTorso" and other.Name ~= "UpperTorso" then
			return
		end
		inZone[player] = inZone[player] or {}
		inZone[player][belt] = true
		if not (blocked[player] and blocked[player][belt]) then
			startTraining(player, belt)
		end
	end)
	belt.TouchEnded:Connect(function(other)
		local player = playerFromPart(other)
		if not player then
			return
		end
		-- the zone counts as left only when no body part touches it any more
		task.delay(0.15, function()
			local touching = false
			for _, part in ipairs(workspace:GetPartsInPart(belt)) do
				if playerFromPart(part) == player then
					touching = true
					break
				end
			end
			if not touching then
				if inZone[player] then
					inZone[player][belt] = nil
				end
				if blocked[player] then
					blocked[player][belt] = nil
				end
			end
		end)
	end)
end

-- ------------------------------------------------------------------------------------------------------------
-- dumbbell
-- ------------------------------------------------------------------------------------------------------------
local function makeDumbbell()
	local tool = Instance.new("Tool")
	tool.Name = "Dumbbell"
	tool.RequiresHandle = true
	tool.CanBeDropped = false
	tool.ToolTip = "Гантель"
	local handle = Instance.new("Part")
	handle.Name = "Handle"
	handle.Size = Vector3.new(0.5, 0.5, 2.6)
	handle.Color = Color3.fromRGB(60, 60, 66)
	handle.Material = Enum.Material.Metal
	handle.Parent = tool
	for _, z in ipairs({ -1, 1 }) do
		local weight = Instance.new("Part")
		weight.Name = "Weight"
		weight.Shape = Enum.PartType.Cylinder
		weight.Size = Vector3.new(0.9, 1.6, 1.6)
		weight.Color = Color3.fromRGB(35, 35, 40)
		weight.Material = Enum.Material.Metal
		weight.CanCollide, weight.Massless = false, true
		weight.CFrame = handle.CFrame * CFrame.new(0, 0, z * 1.2) * CFrame.Angles(0, math.rad(90), 0)
		weight.Parent = tool
		local weld = Instance.new("WeldConstraint")
		weld.Part0, weld.Part1 = handle, weight
		weld.Parent = weight
	end
	tool.Grip = CFrame.new(0, -0.2, 0) * CFrame.Angles(0, math.rad(90), 0)
	return tool
end

local function liftLoop(player, tool)
	if lifting[player] then
		return
	end
	lifting[player] = true
	task.spawn(function()
		local phase = 0
		while lifting[player] and tool.Parent == player.Character do
			phase += 1
			-- repeated curls: the grip swings between "down" and "up" (replicates to everyone)
			tool.Grip = (phase % 2 == 0) and CFrame.new(0, -0.2, 0) * CFrame.Angles(0, math.rad(90), 0)
				or CFrame.new(0, 0.6, -0.8) * CFrame.Angles(math.rad(-70), math.rad(90), 0)
			if phase % 2 == 0 then
				player:SetAttribute("StrengthStat", (player:GetAttribute("StrengthStat") or 0) + CONFIG.StrengthPerLift)
			end
			task.wait(CONFIG.LiftInterval / 2)
		end
		lifting[player] = nil
	end)
end

local function giveDumbbell(player)
	local backpack = player:FindFirstChildOfClass("Backpack")
	local character = player.Character
	if not backpack then
		return false
	end
	if backpack:FindFirstChild("Dumbbell") or (character and character:FindFirstChild("Dumbbell")) then
		return false
	end
	local tool = makeDumbbell()
	tool.Equipped:Connect(function()
		liftLoop(player, tool)
	end)
	tool.Unequipped:Connect(function()
		lifting[player] = nil
	end)
	tool.Parent = backpack
	return true
end

function GymService.BuyDumbbell(player)
	local ok, PlayerDataService = pcall(function()
		return require(script.Parent.PlayerDataService)
	end)
	if player:FindFirstChildOfClass("Backpack") and (player.Backpack:FindFirstChild("Dumbbell") or (player.Character and player.Character:FindFirstChild("Dumbbell"))) then
		return false, "Гантель уже есть"
	end
	if ok and PlayerDataService and PlayerDataService.SpendCash then
		if not PlayerDataService.SpendCash(player, CONFIG.DumbbellPrice) then
			return false, "Не хватает денег"
		end
	end
	if not giveDumbbell(player) then
		return false, "Не удалось выдать гантель"
	end
	return true
end

local function bindShop(part)
	local prompt = part:FindFirstChildOfClass("ProximityPrompt") or Instance.new("ProximityPrompt")
	prompt.ActionText = ("Купить гантель (%d)"):format(CONFIG.DumbbellPrice)
	prompt.ObjectText = "Магазин Gym"
	prompt.HoldDuration = 0.3
	prompt.MaxActivationDistance = 8
	prompt.Parent = part
	prompt.Triggered:Connect(function(player)
		local ok, why = GymService.BuyDumbbell(player)
		player:SetAttribute("HouseHint", ok and "Гантель куплена: она в панели инвентаря" or why)
		player:SetAttribute("HouseHintSeq", (player:GetAttribute("HouseHintSeq") or 0) + 1)
	end)
end

-- ------------------------------------------------------------------------------------------------------------
function GymService.Initialize()
	for _, belt in ipairs(CollectionService:GetTagged("Treadmill")) do
		bindTreadmill(belt)
	end
	CollectionService:GetInstanceAddedSignal("Treadmill"):Connect(bindTreadmill)
	for _, part in ipairs(CollectionService:GetTagged("DumbbellShop")) do
		bindShop(part)
	end
	CollectionService:GetInstanceAddedSignal("DumbbellShop"):Connect(bindShop)

	Players.PlayerRemoving:Connect(function(player)
		stopTraining(player, false)
		inZone[player], blocked[player], lifting[player] = nil, nil, nil
	end)
	local acc = 0
	RunService.Heartbeat:Connect(function(dt)
		acc += dt
		if acc < 1 then
			return
		end
		acc -= 1
		for player in pairs(training) do
			player:SetAttribute("RunStat", (player:GetAttribute("RunStat") or 0) + CONFIG.RunPerSecond)
		end
	end)
end

GymService.Config = CONFIG
GymService.StopTraining = stopTraining
return GymService
