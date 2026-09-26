local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local DataStoreService = game:GetService("DataStoreService")

local Config = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"))

local PlayerDataService = {}
local profiles = {}
local loading = {}
local saving = {}
local removing = {}
local pendingRemovals = 0
local initialized = false
local dataStore = DataStoreService:GetDataStore("StealADad_PlayerData_v1")

local MAX_DATASTORE_ATTEMPTS = 3
local RETRY_DELAY_SECONDS = 1

local function retryDataStoreOperation(operation, description)
	local lastError
	for attempt = 1, MAX_DATASTORE_ATTEMPTS do
		local success, result = pcall(operation)
		if success then
			return true, result
		end

		lastError = result
		warn(string.format("PlayerDataService %s failed (attempt %d/%d): %s", description, attempt, MAX_DATASTORE_ATTEMPTS, tostring(result)))
		if attempt < MAX_DATASTORE_ATTEMPTS then
			task.wait(RETRY_DELAY_SECONDS * attempt)
		end
	end
	return false, lastError
end

local function isValidCash(value)
	return type(value) == "number"
		and value == value
		and value >= 0
		and value < math.huge
		and value <= 9007199254740991
end

local function decodeStoredData(value)
	if value == nil then
		return { Version = 1, Cash = Config.StartingCash }
	end
	if type(value) ~= "table"
		or type(value.Version) ~= "number"
		or value.Version ~= 1
		or not isValidCash(value.Cash) then
		return nil
	end
	return { Version = 1, Cash = value.Cash }
end

local function isValidPositiveAmount(amount)
	return type(amount) == "number" and amount == amount and amount > 0 and amount < math.huge
end

local function createLeaderstats(player, cash)
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
		cashValue.Value = math.floor(cash)
end

local function loadProfile(player)
	local userId = player.UserId
	if profiles[userId] or loading[userId] then
		return profiles[userId]
	end
	loading[userId] = true

	local key = "player_" .. tostring(userId)
	local success, storedValue = retryDataStoreOperation(function()
		return dataStore:GetAsync(key)
	end, "load for " .. key)
	if not success then
		loading[userId] = nil
		if player.Parent == Players then
			player:Kick("Your data could not be loaded. Please rejoin in a moment.")
		end
		return nil
	end

	local savedData = decodeStoredData(storedValue)
	if not savedData then
		loading[userId] = nil
		warn("PlayerDataService rejected invalid saved data for " .. key)
		if player.Parent == Players then
			player:Kick("Your saved data is invalid and was not changed. Please contact the game team.")
		end
		return nil
	end
	if player.Parent ~= Players then
		loading[userId] = nil
		return nil
	end

	local profile = {
		Version = savedData.Version,
		Cash = savedData.Cash,
		OwnedDads = {},
		BaseId = nil,
	}
	profiles[userId] = profile
	createLeaderstats(player, profile.Cash)
	loading[userId] = nil

	return profile
end

local function saveProfile(player)
	local userId = player.UserId
	local inFlightSave = saving[userId]
	if inFlightSave then
		while not inFlightSave.Done do
			task.wait()
		end
		return inFlightSave.Success
	end
	local profile = profiles[userId]
	if not profile then
		return true
	end
	local saveState = { Done = false, Success = false }
	saving[userId] = saveState

	local key = "player_" .. tostring(userId)
	local success, err = pcall(function()
		local payload = {
			Version = 1,
			Cash = profile.Cash,
		}
		return retryDataStoreOperation(function()
			dataStore:SetAsync(key, payload)
		end, "save for " .. key)
	end)
	saveState.Success = success and err == true
	saveState.Done = true
	saving[userId] = nil
	if not success then
		warn(string.format("PlayerDataService save for %s failed unexpectedly: %s", key, tostring(err)))
	end
	return saveState.Success
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

	Players.PlayerAdded:Connect(function(player)
		task.spawn(loadProfile, player)
	end)
	Players.PlayerRemoving:Connect(function(player)
		local userId = player.UserId
		pendingRemovals += 1
		removing[userId] = true
		while loading[userId] do
			task.wait()
		end
		local profile = profiles[userId]
		if profile then
			local success = saveProfile(player)
			if not success then
				warn("PlayerDataService could not save data before removing profile for " .. tostring(userId))
			end
			profiles[userId] = nil
		end
		removing[userId] = nil
		pendingRemovals -= 1
	end)
	game:BindToClose(function()
		while pendingRemovals > 0 do
			task.wait()
		end
		while next(loading) ~= nil do
			task.wait()
		end

		local pendingSaves = 0
		for _, player in ipairs(Players:GetPlayers()) do
			local userId = player.UserId
			if profiles[userId] and not removing[userId] then
				pendingSaves += 1
				task.spawn(function()
					local success = saveProfile(player)
					if not success then
						warn("PlayerDataService shutdown save failed for " .. tostring(userId))
					end
					pendingSaves -= 1
				end)
			end
		end
		while pendingSaves > 0 do
			task.wait()
		end
	end)

	for _, player in ipairs(Players:GetPlayers()) do
		task.spawn(loadProfile, player)
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
	if not isValidCash(newCash) then
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
