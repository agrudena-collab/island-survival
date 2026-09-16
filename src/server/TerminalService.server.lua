-- Validates terminal activation, opens the exit, and awards each player victory.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Config = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"))
local GameState = require(script.Parent:WaitForChild("GameState"))

local remotes = ReplicatedStorage:WaitForChild("EscapeFacilityRemotes")
local gameEvent = remotes:WaitForChild("GameEvent")
local notificationEvent = remotes:WaitForChild("NotificationEvent")

local map = workspace:WaitForChild("EscapeFacilityMap")
local interactive = map:WaitForChild("Interactive")
local terminal = interactive:WaitForChild("CentralTerminal")
local terminalPrompt = terminal:WaitForChild("TerminalPrompt")
local exitDoor = interactive:WaitForChild("ExitDoor")
local exitTrigger = interactive:WaitForChild("ExitTrigger")

local function broadcastState()
	for _, player in Players:GetPlayers() do
		gameEvent:FireClient(player, "State", GameState.GetClientState(player))
	end
end

terminalPrompt.Triggered:Connect(function(player)
	if GameState.IsPlayerFinished(player) then
		return
	end

	if GameState.IsTerminalActivated() then
		notificationEvent:FireClient(player, "Terminal already activated")
		return
	end

	if not GameState.CanActivateTerminal() then
		notificationEvent:FireClient(player, "Requires 3 Energy Cores")
		return
	end

	if not GameState.ActivateTerminal() then
		return
	end

	terminal:SetAttribute("Activated", true)
	terminal.Color = Color3.fromRGB(70, 255, 130)
	terminalPrompt.ActionText = "Terminal Activated"
	terminalPrompt.Enabled = false

	exitDoor.CanCollide = false
	exitDoor.Transparency = 0.45
	exitDoor.Color = Color3.fromRGB(70, 255, 130)
	exitDoor.CFrame = CFrame.new(Config.EXIT_DOOR_POSITION + Vector3.new(0, 14, 0))

	for _, activePlayer in Players:GetPlayers() do
		notificationEvent:FireClient(activePlayer, "Terminal activated")
		notificationEvent:FireClient(activePlayer, "Exit door unlocked")
	end

	print(player.Name .. " activated the central terminal. Exit door unlocked.")
	broadcastState()
end)

local exitTouchDebounce = {}

local signals = ServerStorage:WaitForChild("EscapeFacilitySignals")
local roundReset = signals:WaitForChild("RoundReset")
roundReset.Event:Connect(function()
	for player in pairs(exitTouchDebounce) do
		exitTouchDebounce[player] = nil
	end
end)

exitTrigger.Touched:Connect(function(otherPart)
	local character = otherPart:FindFirstAncestorOfClass("Model")
	local player = character and Players:GetPlayerFromCharacter(character)
	if not player or exitTouchDebounce[player] or not GameState.IsTerminalActivated() then
		return
	end

	exitTouchDebounce[player] = true
	local escaped, finalTime = GameState.FinishPlayer(player)
	if not escaped then
		return
	end

	gameEvent:FireClient(player, "Victory", {
		elapsedTime = finalTime,
		coresCollected = Config.TOTAL_CORES,
	})
	notificationEvent:FireClient(player, "Facility escaped!")
	print(player.Name .. " escaped Escape Facility in " .. finalTime .. " seconds.")
	broadcastState()
end)
