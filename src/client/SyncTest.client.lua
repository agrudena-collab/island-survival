local RunService = game:GetService("RunService")

-- Temporary smoke test for the Mac -> Rojo -> Studio workflow.
if not RunService:IsStudio() then
	return
end

local Players = game:GetService("Players")
local playerGui = Players.LocalPlayer:WaitForChild("PlayerGui")

local screenGui = Instance.new("ScreenGui")
screenGui.Name = "MacSyncTest"
screenGui.ResetOnSpawn = false
screenGui.DisplayOrder = 100

local label = Instance.new("TextLabel")
label.Name = "Status"
label.AnchorPoint = Vector2.new(0.5, 0)
label.Position = UDim2.new(0.5, 0, 0, 24)
label.Size = UDim2.new(0.8, 0, 0, 64)
label.BackgroundColor3 = Color3.fromRGB(25, 100, 65)
label.TextColor3 = Color3.fromRGB(255, 255, 255)
label.Font = Enum.Font.GothamBold
label.TextSize = 20
label.TextWrapped = true
label.Text = "MAC TEST — синхронизация работает"
label.Parent = screenGui
screenGui.Parent = playerGui

print("[MacSyncTest] Client script from feature/player-work is running in Studio.")

task.delay(15, function()
	screenGui:Destroy()
end)
