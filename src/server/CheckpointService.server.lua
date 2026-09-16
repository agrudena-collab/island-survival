-- Saves checkpoint IDs and returns players to the latest checkpoint after death.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameState = require(script.Parent:WaitForChild("GameState"))

local remotes = ReplicatedStorage:WaitForChild("EscapeFacilityRemotes")
local notificationEvent = remotes:WaitForChild("NotificationEvent")

local map = workspace:WaitForChild("EscapeFacilityMap")
local startSpawn = map:WaitForChild("StartSpawn")
local checkpoints = map:WaitForChild("Checkpoints")

local function getCheckpointPosition(player)
	local checkpointId = GameState.GetCheckpoint(player)
	if checkpointId == "Start" then
		return startSpawn.Position
	end

	local checkpoint = checkpoints:FindFirstChild(checkpointId)
	return checkpoint and checkpoint.Position or startSpawn.Position
end

local function moveCharacterToCheckpoint(player, character)
	local root = character:WaitForChild("HumanoidRootPart", 10)
	if not root then
		return
	end

	task.wait(0.15)
	character:PivotTo(CFrame.new(getCheckpointPosition(player) + Vector3.new(0, 4, 0)))
end

local function connectPlayer(player)
	player.CharacterAdded:Connect(function(character)
		moveCharacterToCheckpoint(player, character)
	end)

	if player.Character then
		moveCharacterToCheckpoint(player, player.Character)
	end
end

Players.PlayerAdded:Connect(connectPlayer)
for _, player in Players:GetPlayers() do
	connectPlayer(player)
end

local lastCheckpointTouch = {}

for _, checkpoint in checkpoints:GetChildren() do
	checkpoint.Touched:Connect(function(otherPart)
		local character = otherPart:FindFirstAncestorOfClass("Model")
		local player = character and Players:GetPlayerFromCharacter(character)
		if not player or GameState.IsPlayerFinished(player) then
			return
		end

		local now = os.clock()
		if now - (lastCheckpointTouch[player] or 0) < 1 then
			return
		end
		lastCheckpointTouch[player] = now

		local checkpointId = checkpoint:GetAttribute("CheckpointId")
		if checkpointId and GameState.SetCheckpoint(player, checkpointId) then
			notificationEvent:FireClient(player, checkpointId .. " activated")
		end
	end)
end
