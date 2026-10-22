-- On-screen messages driven by player attributes written on the server:
--   FamilyAlert (FamilyNpcService): "Spotted" -> «Вас заметили», "Searching" -> «Вас ищут», "Clear" -> «Поиск прекращён»
--   HouseHint   (HouseInteractionService): short hints such as a locked door or a taken key
-- Presentation only; the server stays authoritative and this never writes the attributes.
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")

local FamilyAlertController = {}

local ALERTS = {
	Spotted = { text = "Вас заметили!", color = Color3.fromRGB(214, 69, 69), pulse = true },
	Searching = { text = "Вас ищут…", color = Color3.fromRGB(230, 160, 40), pulse = false },
	Clear = { text = "Поиск прекращён", color = Color3.fromRGB(70, 170, 100), pulse = false },
}
local HINT_SECONDS = 3

local function makeLabel(parent: Instance, size: UDim2, position: UDim2, textSize: number)
	local label = Instance.new("TextLabel")
	label.AnchorPoint = Vector2.new(0.5, 0)
	label.Size = size
	label.Position = position
	label.BackgroundTransparency = 1
	label.Font = Enum.Font.FredokaOne
	label.TextSize = textSize
	label.TextColor3 = Color3.new(1, 1, 1)
	label.TextTransparency = 1
	label.Parent = parent

	local stroke = Instance.new("UIStroke")
	stroke.Color = Color3.new(0, 0, 0)
	stroke.Thickness = 2.5
	stroke.Transparency = 1
	stroke.Parent = label
	return label, stroke
end

function FamilyAlertController.Initialize()
	local player = Players.LocalPlayer

	local gui = Instance.new("ScreenGui")
	gui.Name = "FamilyAlertHud"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.DisplayOrder = 20
	gui.Parent = player:WaitForChild("PlayerGui")

	local banner, bannerStroke = makeLabel(gui, UDim2.fromOffset(420, 56), UDim2.fromScale(0.5, 0.11), 36)
	local hint, hintStroke = makeLabel(gui, UDim2.fromOffset(520, 36), UDim2.fromScale(0.5, 0.80), 24)
	-- the banner is a coloured plate with white text so it stays readable on any background
	banner.BackgroundTransparency = 1
	local plateCorner = Instance.new("UICorner")
	plateCorner.CornerRadius = UDim.new(0, 14)
	plateCorner.Parent = banner

	local pulse
	local function show(label: TextLabel, stroke: UIStroke, text: string, color: Color3)
		label.Text = text
		if label == banner then
			label.BackgroundColor3 = color
			TweenService:Create(label, TweenInfo.new(0.15), { TextTransparency = 0, BackgroundTransparency = 0.12 }):Play()
		else
			label.TextColor3 = color
			TweenService:Create(label, TweenInfo.new(0.15), { TextTransparency = 0 }):Play()
		end
		TweenService:Create(stroke, TweenInfo.new(0.15), { Transparency = 0 }):Play()
	end
	local function hide(label: TextLabel, stroke: UIStroke)
		local goal = { TextTransparency = 1 }
		if label == banner then
			goal.BackgroundTransparency = 1
		end
		TweenService:Create(label, TweenInfo.new(0.35), goal):Play()
		TweenService:Create(stroke, TweenInfo.new(0.35), { Transparency = 1 }):Play()
	end

	local function refreshAlert()
		if pulse then
			pulse:Cancel()
			pulse = nil
			banner.Rotation = 0
		end
		local alert = ALERTS[player:GetAttribute("FamilyAlert")]
		if not alert then
			hide(banner, bannerStroke)
			return
		end
		show(banner, bannerStroke, alert.text, alert.color)
		if alert.pulse then
			banner.Rotation = -2
			pulse = TweenService:Create(banner, TweenInfo.new(0.35, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true), { Rotation = 2 })
			pulse:Play()
		end
	end

	local hintToken = 0
	local function refreshHint()
		local text = player:GetAttribute("HouseHint")
		if type(text) ~= "string" or text == "" then
			return
		end
		hintToken += 1
		local token = hintToken
		show(hint, hintStroke, text, Color3.fromRGB(255, 236, 170))
		task.delay(HINT_SECONDS, function()
			if token == hintToken then
				hide(hint, hintStroke)
			end
		end)
	end

	player:GetAttributeChangedSignal("FamilyAlert"):Connect(refreshAlert)
	player:GetAttributeChangedSignal("HouseHintSeq"):Connect(refreshHint)
	refreshAlert()
end

return FamilyAlertController
