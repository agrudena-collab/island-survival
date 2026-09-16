-- Creates shared remotes, manages player state, and restarts the shared test round.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Config = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"))
local GameState = require(script.Parent:WaitForChild("GameState"))

local function getOrCreate(parent, className, name)
	local existing = parent:FindFirstChild(name)
	if existing then
		return existing
	end

	local instance = Instance.new(className)
	instance.Name = name
	instance.Parent = parent
	return instance
end

local remotes = getOrCreate(ReplicatedStorage, "Folder", "EscapeFacilityRemotes")
local gameEvent = getOrCreate(remotes, "RemoteEvent", "GameEvent")
local notificationEvent = getOrCreate(remotes, "RemoteEvent", "NotificationEvent")
local replayEvent = getOrCreate(remotes, "RemoteEvent", "ReplayEvent")

local signals = getOrCreate(ServerStorage, "Folder", "EscapeFacilitySignals")
local roundReset = getOrCreate(signals, "BindableEvent", "RoundReset")
getOrCreate(signals, "BindableEvent", "MapResetComplete")

local function sendState(player)
	gameEvent:FireClient(player, "State", GameState.GetClientState(player))
end

local function broadcastState()
	for _, player in Players:GetPlayers() do
		sendState(player)
	end
end

local function prepareCharacter(player, character)
	local humanoid = character:WaitForChild("Humanoid", 10)
	if not humanoid then
		return
	end

	humanoid.MaxHealth = Config.PLAYER_MAX_HEALTH
	humanoid.Health = Config.PLAYER_MAX_HEALTH

	humanoid.HealthChanged:Connect(function(health)
		gameEvent:FireClient(player, "Health", math.max(0, math.ceil(health)))
	end)

	sendState(player)
end

local function onPlayerAdded(player)
	GameState.AddPlayer(player)

	player.CharacterAdded:Connect(function(character)
		prepareCharacter(player, character)
	end)

	if player.Character then
		prepareCharacter(player, player.Character)
	end
end

Players.PlayerAdded:Connect(onPlayerAdded)
Players.PlayerRemoving:Connect(GameState.RemovePlayer)

for _, player in Players:GetPlayers() do
	onPlayerAdded(player)
end

gameEvent.OnServerEvent:Connect(function(player, action)
	if action == "RequestState" then
		sendState(player)
	end
end)

replayEvent.OnServerEvent:Connect(function(player)
	if not GameState.IsPlayerFinished(player) then
		return
	end

	GameState.ResetRound()
	roundReset:Fire()

	for _, activePlayer in Players:GetPlayers() do
		notificationEvent:FireClient(activePlayer, "New escape attempt started")
		sendState(activePlayer)
		activePlayer:LoadCharacter()
	end
end)
