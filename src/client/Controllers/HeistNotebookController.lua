-- The small notebook with the heist tasks (md: «Задания отображаются в небольшом блокноте»). Read-only view of the player
-- attributes written by HeistService / HouseInteractionService; toggled with N or the corner button.
--   required readiness: bag AND (path A OR path B); the run value is shown as current / N and only warns, never blocks.
local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")

local HeistNotebookController = {}

local PAPER = Color3.fromRGB(250, 243, 222)
local INK = Color3.fromRGB(62, 44, 30)
local GOOD = Color3.fromRGB(46, 130, 70)
local BAD = Color3.fromRGB(176, 60, 50)
local WARN = Color3.fromRGB(190, 120, 20)

local function line(parent: Instance, order: number)
	local label = Instance.new("TextLabel")
	label.LayoutOrder = order
	label.BackgroundTransparency = 1
	label.Size = UDim2.new(1, 0, 0, 0)
	label.AutomaticSize = Enum.AutomaticSize.Y
	label.TextWrapped = true
	label.TextXAlignment = Enum.TextXAlignment.Left
	label.Font = Enum.Font.GothamMedium
	label.TextSize = 15
	label.TextColor3 = INK
	label.RichText = true
	label.Parent = parent
	return label
end

local function colored(text: string, color: Color3)
	return string.format('<font color="rgb(%d,%d,%d)">%s</font>', color.R * 255, color.G * 255, color.B * 255, text)
end

function HeistNotebookController.Initialize()
	local player = Players.LocalPlayer
	local gui = Instance.new("ScreenGui")
	gui.Name = "HeistNotebook"
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 10
	gui.Parent = player:WaitForChild("PlayerGui")

	local button = Instance.new("TextButton")
	button.Name = "NotebookButton"
	button.Size = UDim2.fromOffset(120, 36)
	button.Position = UDim2.new(0, 12, 1, -52)
	button.BackgroundColor3 = PAPER
	button.TextColor3 = INK
	button.Font = Enum.Font.GothamBold
	button.TextSize = 15
	button.Text = "Блокнот [N]"
	button.Parent = gui
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 8)
	corner.Parent = button

	local panel = Instance.new("Frame")
	panel.Name = "Panel"
	panel.Size = UDim2.fromOffset(330, 0)
	panel.AutomaticSize = Enum.AutomaticSize.Y
	panel.AnchorPoint = Vector2.new(0, 1)
	panel.Position = UDim2.new(0, 12, 1, -60)
	panel.BackgroundColor3 = PAPER
	panel.Visible = false
	panel.Parent = gui
	local panelCorner = Instance.new("UICorner")
	panelCorner.CornerRadius = UDim.new(0, 10)
	panelCorner.Parent = panel
	local pad = Instance.new("UIPadding")
	pad.PaddingTop, pad.PaddingBottom, pad.PaddingLeft, pad.PaddingRight = UDim.new(0, 12), UDim.new(0, 12), UDim.new(0, 14), UDim.new(0, 14)
	pad.Parent = panel
	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, 6)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = panel

	local title = line(panel, 0)
	title.Font = Enum.Font.GothamBold
	title.TextSize = 18
	title.Text = "Блокнот: ограбление"
	local plan, bag, pathA, pathB, ready, run, strength, carry = line(panel, 1), line(panel, 2), line(panel, 3), line(panel, 4), line(panel, 5), line(panel, 6), line(panel, 7), line(panel, 8)

	local function mark(done: boolean)
		return done and colored("✓", GOOD) or colored("×", BAD)
	end

	local function refresh()
		local hasBag = player:GetAttribute("HasBag") == true
		local key = player:GetAttribute("HasSpareKey") == true
		local ladder = player:GetAttribute("HasLadder") == true
		local placed = player:GetAttribute("LadderPlaced") == true
		local planDone = player:GetAttribute("PlanAccepted") == true
		plan.Text = mark(planDone) .. " План обсуждён" .. (planDone and "" or " — поговорить с любовницей у её стола")
		bag.Text = mark(hasBag) .. " Мешок" .. (hasBag and "" or " — получить в хозяйственном магазине")
		pathA.Text = mark(key) .. " Путь А: запасной ключ" .. (key and "" or " — найти в сарае на участке")
		pathB.Text = mark(placed) .. " Путь Б: приставная лестница" .. (placed and " установлена" or (ladder and " — установить под балконом" or " — получить у работника мастерской"))
		local isReady = player:GetAttribute("HeistReady") == true
		ready.Text = isReady and colored("Можно идти в дом", GOOD) or colored("Нужны мешок и один способ проникнуть (А или Б)", WARN)

		local runNow, runRec = player:GetAttribute("RunStat") or 0, player:GetAttribute("RunRecommended") or 0
		run.Text = ("Бег: %d / %d"):format(runNow, runRec)
		if runNow < runRec then
			run.Text ..= "  " .. colored("ниже рекомендованного: от семьи труднее убежать (это не запрет)", WARN)
		end
		local strNow, strRec = player:GetAttribute("StrengthStat") or 0, player:GetAttribute("StrengthRecommended") or 0
		strength.Text = ("Сила: %d / %d"):format(strNow, strRec)
		if strNow < strRec then
			strength.Text ..= "  " .. colored("ниже рекомендованного: мешок несёте очень медленно (это не запрет)", WARN)
		end
		local carrying = player:GetAttribute("CarryingDad")
		carry.Visible = type(carrying) == "string" and carrying ~= ""
		carry.Text = carry.Visible and ("Несёте отца: " .. carrying .. ". Избавьтесь от погони, затем войдите в квартиру.") or ""
	end

	local function toggle()
		panel.Visible = not panel.Visible
	end
	button.Activated:Connect(toggle)
	ContextActionService:BindAction("HeistNotebook", function(_, state)
		if state == Enum.UserInputState.Begin then
			toggle()
		end
		return Enum.ContextActionResult.Pass
	end, false, Enum.KeyCode.N)

	for _, name in ipairs({
		"PlanAccepted", "HasBag", "HasSpareKey", "HasLadder", "LadderPlaced", "HeistReady", "RunStat", "RunRecommended", "StrengthStat", "StrengthRecommended", "CarryingDad",
	}) do
		player:GetAttributeChangedSignal(name):Connect(refresh)
	end
	refresh()
end

return HeistNotebookController
