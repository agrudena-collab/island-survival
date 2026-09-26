local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")

local PlayerDataService = require(script.Parent:WaitForChild("PlayerDataService"))

local BaseService = {}
local assignments = {}
local reservedBases = {}
local characterConnections = {}
local initialized = false

local function findFreeBase()
	local map = Workspace:FindFirstChild("MapBlockout")
	if not map or not map:IsA("Model") then
		warn("BaseService: Workspace.MapBlockout model is missing")
		return nil
	end

	local bases = map:FindFirstChild("Bases")
	if not bases or not bases:IsA("Folder") then
		warn("BaseService: Workspace.MapBlockout.Bases folder is missing")
		return nil
	end

	for index = 1, 8 do
		local baseName = string.format("Base_%02d", index)
		local base = bases:FindFirstChild(baseName)
		if not base or not base:IsA("Model") then
			warn("BaseService: missing base model " .. baseName)
		else
			local spawn = base:FindFirstChild("PlayerSpawn")
			if not spawn or not spawn:IsA("BasePart") then
				warn("BaseService: missing PlayerSpawn part in " .. baseName)
			elseif not reservedBases[base] then
				return base, spawn
			end
		end
	end

	warn("BaseService: no free valid base is available")
	return nil
end

local function moveCharacter(player, character)
	local assignment = assignments[player.UserId]
	if not assignment then
		return
	end

	local root = character:WaitForChild("HumanoidRootPart", 5)
	if not root or player.Parent ~= Players or player.Character ~= character then
		return
	end
	if assignments[player.UserId] ~= assignment or not assignment.Spawn:IsDescendantOf(Workspace) then
		warn("BaseService: assigned PlayerSpawn is unavailable for " .. player.Name)
		return
	end
	character:PivotTo(assignment.Spawn.CFrame + Vector3.new(0, 4, 0))
end

local function assignBase(player)
	if player.Parent ~= Players or assignments[player.UserId] then
		return
	end
	if not PlayerDataService.GetData(player) then
		return
	end

	-- Reservation and profile update do not yield, so another player cannot claim this base.
	local base, spawn = findFreeBase()
	if not base then
		return
	end
	reservedBases[base] = player.UserId
	if not PlayerDataService.SetBaseId(player, base.Name) then
		reservedBases[base] = nil
		return
	end
	assignments[player.UserId] = { Base = base, Spawn = spawn }
	base:SetAttribute("OwnerUserId", player.UserId)
	base:SetAttribute("OwnerName", player.Name)

	if player.Character then
		task.spawn(moveCharacter, player, player.Character)
	end
end

local function trackPlayer(player)
	if characterConnections[player.UserId] then
		return
	end
	characterConnections[player.UserId] = player.CharacterAdded:Connect(function(character)
		task.spawn(moveCharacter, player, character)
	end)
end

local function releaseBase(player)
	local userId = player.UserId
	local connection = characterConnections[userId]
	if connection then
		connection:Disconnect()
		characterConnections[userId] = nil
	end

	local assignment = assignments[userId]
	if assignment then
		assignments[userId] = nil
		reservedBases[assignment.Base] = nil
		if assignment.Base:GetAttribute("OwnerUserId") == userId then
			assignment.Base:SetAttribute("OwnerUserId", nil)
			assignment.Base:SetAttribute("OwnerName", nil)
		end
	end
	PlayerDataService.SetBaseId(player, nil)
end

function BaseService.Initialize()
	if initialized then
		return
	end
	initialized = true

	Players.PlayerAdded:Connect(trackPlayer)
	Players.PlayerRemoving:Connect(releaseBase)
	for _, player in ipairs(Players:GetPlayers()) do
		trackPlayer(player)
	end
	PlayerDataService.OnProfileLoaded(assignBase)
end

return BaseService
