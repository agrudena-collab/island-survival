-- Displays the player HUD, local health, elapsed time, and victory panel.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local player = Players.LocalPlayer
local Config = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"))

local remotes = ReplicatedStorage:WaitForChild("EscapeFacilityRemotes")
local gameEvent = remotes:WaitForChild("GameEvent")
local replayEvent = remotes:WaitForChild("ReplayEvent")

local playerGui = player:WaitForChild("PlayerGui")
local previousGui = playerGui:FindFirstChild("EscapeFacilityUI")
if previousGui then
	previousGui:Destroy()
end

local screenGui = Instance.new("ScreenGui")
screenGui.Name = "EscapeFacilityUI"
screenGui.ResetOnSpawn = false
screenGui.Parent = playerGui

local function createLabel(parent, name, text, position, size)
	local label = Instance.new("TextLabel")
	label.Name = name
	label.Position = position
	label.Size = size
	label.BackgroundColor3 = Color3.fromRGB(20, 25, 34)
	label.BackgroundTransparency = 0.15
	label.TextColor3 = Color3.fromRGB(240, 245, 255)
	label.Font = Enum.Font.GothamBold
	label.TextSize = 19
	label.Text = text
	label.Parent = parent

	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 8)
	corner.Parent = label
	return label
end

local hud = Instance.new("Frame")
hud.Name = "HUD"
hud.BackgroundTransparency = 1
hud.Position = UDim2.fromOffset(18, 18)
hud.Size = UDim2.fromOffset(620, 48)
hud.Parent = screenGui

local coresLabel = createLabel(hud, "CoresLabel", "Energy Cores: 0/3", UDim2.fromOffset(0, 0), UDim2.fromOffset(205, 46))
coresLabel.TextColor3 = Color3.fromRGB(100, 230, 255)

local healthLabel = createLabel(hud, "HealthLabel", "Health: 100", UDim2.fromOffset(214, 0), UDim2.fromOffset(170, 46))
healthLabel.TextColor3 = Color3.fromRGB(115, 255, 155)

local timeLabel = createLabel(hud, "TimeLabel", "Time: 00:00", UDim2.fromOffset(393, 0), UDim2.fromOffset(170, 46))
timeLabel.TextColor3 = Color3.fromRGB(255, 225, 125)

local notificationLabel = createLabel(
	screenGui,
	"NotificationLabel",
	"",
	UDim2.new(0.5, -180, 0.84, 0),
	UDim2.fromOffset(360, 46)
)
notificationLabel.AnchorPoint = Vector2.new(0, 0.5)
notificationLabel.TextSize = 18
notificationLabel.Visible = false

local victoryPanel = Instance.new("Frame")
victoryPanel.Name = "VictoryPanel"
victoryPanel.AnchorPoint = Vector2.new(0.5, 0.5)
victoryPanel.Position = UDim2.fromScale(0.5, 0.5)
victoryPanel.Size = UDim2.fromOffset(440, 260)
victoryPanel.BackgroundColor3 = Color3.fromRGB(20, 55, 38)
victoryPanel.Visible = false
victoryPanel.Parent = screenGui

local victoryCorner = Instance.new("UICorner")
victoryCorner.CornerRadius = UDim.new(0, 16)
victoryCorner.Parent = victoryPanel

local victoryTitle = Instance.new("TextLabel")
victoryTitle.Name = "VictoryTitle"
victoryTitle.BackgroundTransparency = 1
victoryTitle.Position = UDim2.fromOffset(0, 28)
victoryTitle.Size = UDim2.new(1, 0, 0, 65)
victoryTitle.Text = "ESCAPED!"
victoryTitle.TextColor3 = Color3.fromRGB(115, 255, 155)
victoryTitle.Font = Enum.Font.GothamBlack
victoryTitle.TextSize = 50
victoryTitle.Parent = victoryPanel

local victoryDetails = Instance.new("TextLabel")
victoryDetails.Name = "VictoryDetails"
victoryDetails.BackgroundTransparency = 1
victoryDetails.Position = UDim2.fromOffset(0, 102)
victoryDetails.Size = UDim2.new(1, 0, 0, 55)
victoryDetails.TextColor3 = Color3.fromRGB(245, 250, 255)
victoryDetails.Font = Enum.Font.GothamMedium
victoryDetails.TextSize = 22
victoryDetails.Text = "Time: 00:00\nEnergy Cores: 3/3"
victoryDetails.Parent = victoryPanel

local replayButton = Instance.new("TextButton")
replayButton.Name = "PlayAgainButton"
replayButton.AnchorPoint = Vector2.new(0.5, 0)
replayButton.Position = UDim2.fromScale(0.5, 0.72)
replayButton.Size = UDim2.fromOffset(210, 48)
replayButton.BackgroundColor3 = Color3.fromRGB(70, 180, 105)
replayButton.TextColor3 = Color3.fromRGB(255, 255, 255)
replayButton.Font = Enum.Font.GothamBold
replayButton.TextSize = 21
replayButton.Text = "PLAY AGAIN"
replayButton.Parent = victoryPanel

local replayCorner = Instance.new("UICorner")
replayCorner.CornerRadius = UDim.new(0, 10)
replayCorner.Parent = replayButton

local currentState = {
	coresCollected = 0,
	totalCores = Config.TOTAL_CORES,
	startTime = workspace:GetServerTimeNow(),
	elapsedTime = 0,
	timerRunning = true,
	finished = false,
}

local function formatTime(seconds)
	seconds = math.max(0, math.floor(seconds))
	return string.format("%02d:%02d", math.floor(seconds / 60), seconds % 60)
end

local function updateCoreLabel()
	coresLabel.Text = string.format("Energy Cores: %d/%d", currentState.coresCollected, currentState.totalCores)
end

local function showVictory(elapsedTime, coresCollected)
	victoryDetails.Text = string.format(
		"Time: %s\nEnergy Cores: %d/%d",
		formatTime(elapsedTime),
		coresCollected,
		Config.TOTAL_CORES
	)
	victoryPanel.Visible = true
	replayButton.Text = "PLAY AGAIN"
end

local function applyState(state)
	currentState = state
	updateCoreLabel()

	if state.finished then
		showVictory(state.finalTime, state.coresCollected)
	else
		victoryPanel.Visible = false
		replayButton.Text = "PLAY AGAIN"
	end
end

local function bindHumanoid(character)
	local humanoid = character:WaitForChild("Humanoid", 10)
	if not humanoid then
		return
	end

	local function updateHealth(health)
		healthLabel.Text = "Health: " .. math.max(0, math.ceil(health))
	end

	updateHealth(humanoid.Health)
	humanoid.HealthChanged:Connect(updateHealth)
end

player.CharacterAdded:Connect(bindHumanoid)
if player.Character then
	bindHumanoid(player.Character)
end

gameEvent.OnClientEvent:Connect(function(eventName, payload)
	if eventName == "State" then
		applyState(payload)
	elseif eventName == "Health" then
		healthLabel.Text = "Health: " .. math.max(0, math.ceil(payload))
	elseif eventName == "Victory" then
		currentState.finished = true
		currentState.timerRunning = false
		currentState.elapsedTime = payload.elapsedTime
		showVictory(payload.elapsedTime, payload.coresCollected)
	end
end)

replayButton.Activated:Connect(function()
	if not currentState.finished then
		return
	end

	replayButton.Text = "RESTARTING..."
	replayEvent:FireServer()
end)

RunService.RenderStepped:Connect(function()
	local elapsed = currentState.elapsedTime or 0
	if currentState.timerRunning then
		elapsed = math.clamp(math.floor(workspace:GetServerTimeNow() - currentState.startTime), 0, Config.GAME_TIME)
	end
	timeLabel.Text = "Time: " .. formatTime(elapsed)
end)

gameEvent:FireServer("RequestState")
