--!strict
-- Run once in the Studio command bar (edit mode): creates ServerScriptService.GrillMistressCharacterCollision, which puts every
-- character part into the collision group "Players" (they pass through the CameraOccluder meshes, walk on the invisible colliders).
local SSS = game:GetService("ServerScriptService")
local old = SSS:FindFirstChild("GrillMistressCharacterCollision")
if old then old:Destroy() end
local sc = Instance.new("Script")
sc.Name = "GrillMistressCharacterCollision"
sc.Source = [[
local Players = game:GetService("Players")
local function setup(char)
	for _, d in ipairs(char:GetDescendants()) do if d:IsA("BasePart") then d.CollisionGroup = "Players" end end
	char.DescendantAdded:Connect(function(d) if d:IsA("BasePart") then d.CollisionGroup = "Players" end end)
end
local function onPlayer(p) p.CharacterAdded:Connect(setup) if p.Character then setup(p.Character) end end
Players.PlayerAdded:Connect(onPlayer)
for _, p in ipairs(Players:GetPlayers()) do onPlayer(p) end
]]
sc.Parent = SSS
print("GrillMistressCharacterCollision created")
