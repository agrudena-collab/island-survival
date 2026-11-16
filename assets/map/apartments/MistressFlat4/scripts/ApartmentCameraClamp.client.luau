--!nonstrict
-- ApartmentCameraClamp (LocalScript, Studio: StarterPlayer.StarterPlayerScripts.ApartmentCameraClamp)
-- Копия из Studio (2026-11-09). Не подключена в Rojo.
-- Держит камеру внутри квартиры любовницы: окна-стёкла невидимые, и стандартная камера улетала в окно/дверь.
-- В каждой квартире один невидимый Part (Anchored, CanCollide/CanQuery/CanTouch=false, Transparency=1)
-- с тегом "ApartmentCamBounds" по AABB стен (Wall/Floor/Ceiling из Interior.Colliders).
-- Пока игрок внутри бокса (+pad), позиция камеры зажимается внутрь бокса с отступом.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local CollectionService = game:GetService("CollectionService")

local TAG = "ApartmentCamBounds"
local MARGIN = 1.5
local INSIDE_PAD = 4

local player = Players.LocalPlayer

local boxes = {}
for _, p in ipairs(CollectionService:GetTagged(TAG)) do
	boxes[p] = true
end
CollectionService:GetInstanceAddedSignal(TAG):Connect(function(p)
	boxes[p] = true
end)
CollectionService:GetInstanceRemovedSignal(TAG):Connect(function(p)
	boxes[p] = nil
end)

local function clampInBox(part, worldPos, half)
	local lp = part.CFrame:PointToObjectSpace(worldPos)
	local c = Vector3.new(math.clamp(lp.X, -half.X, half.X), math.clamp(lp.Y, -half.Y, half.Y), math.clamp(lp.Z, -half.Z, half.Z))
	return part.CFrame:PointToWorldSpace(c)
end

RunService:BindToRenderStep("ApartmentCamClamp", Enum.RenderPriority.Camera.Value + 1, function()
	local camera = workspace.CurrentCamera
	local char = player.Character
	local root = char and char:FindFirstChild("HumanoidRootPart")
	if not camera or not root then
		return
	end
	for part in pairs(boxes) do
		if part.Parent then
			local half = part.Size / 2
			local rl = part.CFrame:PointToObjectSpace(root.Position)
			if math.abs(rl.X) <= half.X + INSIDE_PAD and math.abs(rl.Y) <= half.Y + INSIDE_PAD and math.abs(rl.Z) <= half.Z + INSIDE_PAD then
				local inner = Vector3.new(math.max(half.X - MARGIN, 0), math.max(half.Y - MARGIN, 0), math.max(half.Z - MARGIN, 0))
				local cf = camera.CFrame
				local pos = cf.Position
				local newPos = clampInBox(part, pos, inner)
				if (newPos - pos).Magnitude > 1e-4 then
					camera.CFrame = cf - pos + newPos
				end
				return
			end
		end
	end
end)
