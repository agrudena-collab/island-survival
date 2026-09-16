-- Server-authoritative collection logic for the three shared Energy Cores.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Config = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"))
local GameState = require(script.Parent:WaitForChild("GameState"))

local remotes = ReplicatedStorage:WaitForChild("EscapeFacilityRemotes")
local gameEvent = remotes:WaitForChild("GameEvent")
local notificationEvent = remotes:WaitForChild("NotificationEvent")

local signals = ServerStorage:WaitForChild("EscapeFacilitySignals")
local mapResetComplete = signals:WaitForChild("MapResetComplete")

local map = workspace:WaitForChild("EscapeFacilityMap")
local interactive = map:WaitForChild("Interactive")
local cores = interactive:WaitForChild("EnergyCores")
local terminalPrompt = interactive:WaitForChild("CentralTerminal"):WaitForChild("TerminalPrompt")

local function broadcastState()
	for _, player in Players:GetPlayers() do
		gameEvent:FireClient(player, "State", GameState.GetClientState(player))
	end
end

local function connectCore(core)
	local prompt = core:FindFirstChild("CorePrompt")
	if not prompt then
		return
	end

	prompt.Triggered:Connect(function(player)
		if GameState.IsPlayerFinished(player) or core:GetAttribute("Collected") then
			return
		end

		-- Set this before changing the score to reject simultaneous prompt triggers.
		core:SetAttribute("Collected", true)
		prompt.Enabled = false

		local collected, total = GameState.CollectCore()
		if not collected then
			return
		end

		notificationEvent:FireClient(player, "Energy Core collected")
		core:Destroy()

		if total == Config.TOTAL_CORES then
			terminalPrompt.ActionText = "Activate Terminal"
			for _, activePlayer in Players:GetPlayers() do
				notificationEvent:FireClient(activePlayer, "3/3 Cores collected")
			end
		end

		broadcastState()
	end)
end

local function connectCurrentCores()
	for _, core in cores:GetChildren() do
		connectCore(core)
	end
end

connectCurrentCores()
mapResetComplete.Event:Connect(connectCurrentCores)
