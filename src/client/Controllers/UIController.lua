-- Builds the player-facing HUD. Cash is read from leaderstats (server-authoritative,
-- written by PlayerDataService); this controller only displays it.
local Players = game:GetService("Players")

local UIController = {}

local function roundedFrame(parent: Instance, size: UDim2, position: UDim2, color: Color3, rotation: number, corner: number)
	local frame = Instance.new("Frame")
	frame.Size = size
	frame.Position = position
	frame.AnchorPoint = Vector2.new(0.5, 0.5)
	frame.Rotation = rotation
	frame.BackgroundColor3 = color
	frame.BorderSizePixel = 0
	frame.Parent = parent

	local uiCorner = Instance.new("UICorner")
	uiCorner.CornerRadius = UDim.new(0, corner)
	uiCorner.Parent = frame

	local stroke = Instance.new("UIStroke")
	stroke.Color = Color3.new(0, 0, 0)
	stroke.Thickness = 2
	stroke.Parent = frame

	return frame
end

local function buildCashIcon(parent: Instance)
	local holder = Instance.new("Frame")
	holder.Name = "CashIcon"
	holder.Size = UDim2.fromOffset(44, 44)
	holder.BackgroundTransparency = 1
	holder.Parent = parent

	roundedFrame(holder, UDim2.fromOffset(36, 24), UDim2.fromScale(0.42, 0.58), Color3.fromRGB(22, 120, 55), -10, 5)
	local front = roundedFrame(holder, UDim2.fromOffset(36, 24), UDim2.fromScale(0.56, 0.46), Color3.fromRGB(45, 196, 90), 6, 5)

	local band = Instance.new("Frame")
	band.Size = UDim2.new(1, 0, 0, 6)
	band.Position = UDim2.fromScale(0, 0.5)
	band.AnchorPoint = Vector2.new(0, 0.5)
	band.BackgroundColor3 = Color3.fromRGB(242, 201, 76)
	band.BorderSizePixel = 0
	band.Parent = front

	local dollar = Instance.new("TextLabel")
	dollar.Size = UDim2.fromScale(1, 1)
	dollar.BackgroundTransparency = 1
	dollar.Font = Enum.Font.FredokaOne
	dollar.TextColor3 = Color3.fromRGB(255, 255, 255)
	dollar.TextScaled = true
	dollar.Text = "$"
	dollar.Parent = front

	return holder
end

local function buildCashLabel(parent: Instance)
	local label = Instance.new("TextLabel")
	label.Name = "CashLabel"
	label.Size = UDim2.fromOffset(140, 44)
	label.Position = UDim2.fromOffset(44, 0)
	label.BackgroundTransparency = 1
	label.Font = Enum.Font.FredokaOne
	label.TextScaled = true
	label.TextXAlignment = Enum.TextXAlignment.Left
	label.TextColor3 = Color3.fromRGB(86, 255, 120)
	label.Text = "$0"
	label.Parent = parent

	local stroke = Instance.new("UIStroke")
	stroke.Color = Color3.new(0, 0, 0)
	stroke.Thickness = 3
	stroke.Parent = label

	return label
end

local function buildCashHud(player: Player)
	local screenGui = Instance.new("ScreenGui")
	screenGui.Name = "CashHud"
	screenGui.ResetOnSpawn = false
	screenGui.Parent = player:WaitForChild("PlayerGui")

	local container = Instance.new("Frame")
	container.Name = "Container"
	container.Size = UDim2.fromOffset(190, 44)
	container.Position = UDim2.fromOffset(16, 16)
	container.BackgroundTransparency = 1
	container.Parent = screenGui

	buildCashIcon(container)
	local label = buildCashLabel(container)

	local leaderstats = player:WaitForChild("leaderstats")
	local cashValue = leaderstats:WaitForChild("Cash")

	local function refresh()
		label.Text = "$" .. cashValue.Value
	end

	cashValue.Changed:Connect(refresh)
	refresh()
end

function UIController.Initialize()
	buildCashHud(Players.LocalPlayer)
end

return UIController
