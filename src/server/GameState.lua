local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"))

local GameState = {}

local playerStates = {}
local roundState = {
	coresCollected = 0,
	terminalActivated = false,
	roundNumber = 1,
}

local function now()
	return workspace:GetServerTimeNow()
end

local function newPlayerState()
	return {
		checkpointId = "Start",
		startTime = now(),
		finished = false,
		finalTime = 0,
	}
end

local function getPlayerState(player)
	if not playerStates[player] then
		playerStates[player] = newPlayerState()
	end

	return playerStates[player]
end

function GameState.AddPlayer(player)
	return getPlayerState(player)
end

function GameState.RemovePlayer(player)
	playerStates[player] = nil
end

function GameState.GetElapsedTime(player)
	local state = getPlayerState(player)
	if state.finished then
		return state.finalTime
	end

	return math.clamp(math.floor(now() - state.startTime), 0, Config.GAME_TIME)
end

function GameState.GetClientState(player)
	local state = getPlayerState(player)

	return {
		coresCollected = roundState.coresCollected,
		totalCores = Config.TOTAL_CORES,
		terminalActivated = roundState.terminalActivated,
		checkpointId = state.checkpointId,
		startTime = state.startTime,
		elapsedTime = GameState.GetElapsedTime(player),
		timerRunning = not state.finished,
		finished = state.finished,
		finalTime = state.finalTime,
		roundNumber = roundState.roundNumber,
	}
end

function GameState.GetCoresCollected()
	return roundState.coresCollected
end

function GameState.CollectCore()
	if roundState.coresCollected >= Config.TOTAL_CORES then
		return false, roundState.coresCollected
	end

	roundState.coresCollected += 1
	return true, roundState.coresCollected
end

function GameState.CanActivateTerminal()
	return roundState.coresCollected >= Config.TOTAL_CORES and not roundState.terminalActivated
end

function GameState.ActivateTerminal()
	if not GameState.CanActivateTerminal() then
		return false
	end

	roundState.terminalActivated = true
	return true
end

function GameState.IsTerminalActivated()
	return roundState.terminalActivated
end

function GameState.SetCheckpoint(player, checkpointId)
	local state = getPlayerState(player)
	if state.checkpointId == checkpointId then
		return false
	end

	state.checkpointId = checkpointId
	return true
end

function GameState.GetCheckpoint(player)
	return getPlayerState(player).checkpointId
end

function GameState.FinishPlayer(player)
	local state = getPlayerState(player)
	if state.finished or not roundState.terminalActivated then
		return false, state.finalTime
	end

	state.finalTime = GameState.GetElapsedTime(player)
	state.finished = true
	return true, state.finalTime
end

function GameState.IsPlayerFinished(player)
	return getPlayerState(player).finished
end

function GameState.ResetRound()
	roundState.coresCollected = 0
	roundState.terminalActivated = false
	roundState.roundNumber += 1

	for player in pairs(playerStates) do
		playerStates[player] = newPlayerState()
	end
end

return GameState
