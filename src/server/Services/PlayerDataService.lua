local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"))

local PlayerDataService = {}
local profiles = {}
local initialized = false

local function isValidPositiveAmount(amount)
	return type(amount) == "number" and amount == amount and amount > 0 and amount < math.huge
end

local function createProfile(player)
	local userId = player.UserId
	if profiles[userId] then
		return profiles[userId]
	end

	local profile = {
		Cash = Config.StartingCash,
		OwnedDads = {},
		BaseId = nil,
	}
	profiles[userId] = profile

	local leaderstats = player:FindFirstChild("leaderstats")
	if not leaderstats then
		leaderstats = Instance.new("Folder")
		leaderstats.Name = "leaderstats"
		leaderstats.Parent = player
	end

	local cashValue = leaderstats:FindFirstChild("Cash")
	if not cashValue then
		cashValue = Instance.new("IntValue")
		cashValue.Name = "Cash"
		cashValue.Parent = leaderstats
	end
	cashValue.Value = profile.Cash

	return profile
end

local function getProfile(player)
	if typeof(player) ~= "Instance" or not player:IsA("Player") then
		return nil
	end
	return profiles[player.UserId]
end

function PlayerDataService.Initialize()
	if initialized then
		return
	end
	initialized = true

	Players.PlayerAdded:Connect(createProfile)
	Players.PlayerRemoving:Connect(function(player)
		profiles[player.UserId] = nil
	end)

	for _, player in ipairs(Players:GetPlayers()) do
		createProfile(player)
	end
end

function PlayerDataService.GetData(player)
	return getProfile(player)
end

function PlayerDataService.GetCash(player)
	local profile = getProfile(player)
	return profile and profile.Cash or nil
end

function PlayerDataService.AddCash(player, amount)
	local profile = getProfile(player)
	if not profile or not isValidPositiveAmount(amount) then
		return false
	end

	local newCash = profile.Cash + amount
	if newCash ~= newCash or newCash >= math.huge then
		return false
	end

	profile.Cash = newCash
	local leaderstats = player:FindFirstChild("leaderstats")
	local cashValue = leaderstats and leaderstats:FindFirstChild("Cash")
	if cashValue and cashValue:IsA("IntValue") then
		cashValue.Value = math.floor(profile.Cash)
	end
	return true
end

function PlayerDataService.CanAfford(player, amount)
	local profile = getProfile(player)
	return profile ~= nil and isValidPositiveAmount(amount) and profile.Cash >= amount
end

function PlayerDataService.SpendCash(player, amount)
	local profile = getProfile(player)
	if not profile or not isValidPositiveAmount(amount) or profile.Cash < amount then
		return false
	end

	profile.Cash -= amount
	local leaderstats = player:FindFirstChild("leaderstats")
	local cashValue = leaderstats and leaderstats:FindFirstChild("Cash")
	if cashValue and cashValue:IsA("IntValue") then
		cashValue.Value = math.floor(profile.Cash)
	end
	return true
end

return PlayerDataService
