-- Dialogue panel for the mistress' table: shows the node text and one button per phrase. The server decides what each
-- choice leads to (DialogueService); this panel only displays it and reports the picked index.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local DialogueController = {}

local PAPER = Color3.fromRGB(32, 30, 38)
local TEXT = Color3.fromRGB(246, 240, 226)
local ACCENT = Color3.fromRGB(214, 160, 70)

function DialogueController.Initialize()
	local player = Players.LocalPlayer
	local remotes = ReplicatedStorage:WaitForChild("Remotes")
	local nodeRemote = remotes:WaitForChild("DialogueNode")
	local chooseRemote = remotes:WaitForChild("DialogueChoose")

	local gui = Instance.new("ScreenGui")
	gui.Name = "MistressDialogue"
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 30
	gui.Parent = player:WaitForChild("PlayerGui")

	local panel = Instance.new("Frame")
	panel.AnchorPoint = Vector2.new(0.5, 1)
	panel.Position = UDim2.new(0.5, 0, 1, -64) -- above the notebook button row
	panel.Size = UDim2.fromOffset(620, 0)
	panel.AutomaticSize = Enum.AutomaticSize.Y
	panel.BackgroundColor3 = PAPER
	panel.BackgroundTransparency = 0.05
	panel.Visible = false
	panel.Parent = gui
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 14)
	corner.Parent = panel
	local pad = Instance.new("UIPadding")
	pad.PaddingTop, pad.PaddingBottom, pad.PaddingLeft, pad.PaddingRight = UDim.new(0, 16), UDim.new(0, 16), UDim.new(0, 18), UDim.new(0, 18)
	pad.Parent = panel
	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, 8)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = panel

	local speaker = Instance.new("TextLabel")
	speaker.LayoutOrder = 0
	speaker.BackgroundTransparency = 1
	speaker.Size = UDim2.new(1, 0, 0, 20)
	speaker.TextXAlignment = Enum.TextXAlignment.Left
	speaker.Font = Enum.Font.GothamBold
	speaker.TextSize = 16
	speaker.TextColor3 = ACCENT
	speaker.Text = "Любовница"
	speaker.Parent = panel

	local body = Instance.new("TextLabel")
	body.LayoutOrder = 1
	body.BackgroundTransparency = 1
	body.Size = UDim2.new(1, 0, 0, 0)
	body.AutomaticSize = Enum.AutomaticSize.Y
	body.TextWrapped = true
	body.TextXAlignment = Enum.TextXAlignment.Left
	body.Font = Enum.Font.GothamMedium
	body.TextSize = 18
	body.TextColor3 = TEXT
	body.Parent = panel

	local buttons = {}
	local token = 0

	local function clear()
		for _, b in ipairs(buttons) do
			b:Destroy()
		end
		table.clear(buttons)
	end

	nodeRemote.OnClientEvent:Connect(function(node)
		token += 1
		local mine = token
		clear()
		if type(node) ~= "table" then
			panel.Visible = false
			return
		end
		body.Text = node.text
		panel.Visible = true
		for i, text in ipairs(node.choices) do
			local button = Instance.new("TextButton")
			button.LayoutOrder = 10 + i
			button.Size = UDim2.new(1, 0, 0, 36)
			button.BackgroundColor3 = Color3.fromRGB(58, 54, 70)
			button.TextColor3 = TEXT
			button.Font = Enum.Font.Gotham
			button.TextSize = 16
			button.TextXAlignment = Enum.TextXAlignment.Left
			button.Text = "  " .. text
			button.AutoButtonColor = true
			button.Parent = panel
			local c = Instance.new("UICorner")
			c.CornerRadius = UDim.new(0, 8)
			c.Parent = button
			button.Activated:Connect(function()
				chooseRemote:FireServer(i)
			end)
			table.insert(buttons, button)
		end
		if node.ends then
			task.delay(2.5, function()
				if token == mine then
					panel.Visible = false
				end
			end)
		end
	end)
end

return DialogueController
