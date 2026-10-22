-- Server side of crouching (md: "кнопка приседания": the player crouches to hide behind low furniture; pressing the
-- button does not make the player invisible, only the lowered body height matters for the family's line of sight).
-- The client requests the state through the SetCrouch remote; the server validates it, lowers Humanoid.HipHeight (so the
-- real body, camera and the NPC sight points all drop) and publishes the player attribute `Crouching`.
-- Walking speed is NOT changed: the md says changes to walking/crouching speed are not approved.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Remotes = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Remotes"))

local CrouchService = {}

-- PROVISIONAL: the crouched hip height is a prototype value (the md only asks that the real crouched height counts).
local CROUCH_HIP_HEIGHT = 0.1
local TWEEN_SECONDS = 0.18
local MIN_INTERVAL = 0.25

local lastRequest = {} -- [Player] = os.clock()

local function humanoidOf(player)
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if humanoid and humanoid.Health > 0 then
		return humanoid
	end
	return nil
end

function CrouchService.SetCrouching(player, crouching)
	local humanoid = humanoidOf(player)
	if not humanoid then
		return false
	end
	if crouching and player:GetAttribute("IsHiding") == true then
		return false -- hidden in a cupboard: the hiding spot owns the pose
	end
	if (player:GetAttribute("Crouching") == true) == crouching then
		return true
	end
	if crouching then
		humanoid:SetAttribute("BaseHipHeight", humanoid.HipHeight)
	end
	local target = crouching and CROUCH_HIP_HEIGHT or humanoid:GetAttribute("BaseHipHeight") or humanoid.HipHeight
	player:SetAttribute("Crouching", crouching)
	TweenService:Create(humanoid, TweenInfo.new(TWEEN_SECONDS, Enum.EasingStyle.Quad), { HipHeight = target }):Play()
	return true
end

local function watch(player)
	player:SetAttribute("Crouching", false)
	player.CharacterAdded:Connect(function()
		player:SetAttribute("Crouching", false)
	end)
	player:GetAttributeChangedSignal("IsHiding"):Connect(function()
		if player:GetAttribute("IsHiding") == true then
			CrouchService.SetCrouching(player, false)
		end
	end)
end

function CrouchService.Initialize()
	local folder = ReplicatedStorage:WaitForChild("Remotes")
	local remote = folder:WaitForChild(Remotes.Events.SetCrouch)
	remote.OnServerEvent:Connect(function(player, crouching)
		if type(crouching) ~= "boolean" then
			return
		end
		local now = os.clock()
		if now - (lastRequest[player] or 0) < MIN_INTERVAL then
			return
		end
		lastRequest[player] = now
		CrouchService.SetCrouching(player, crouching)
	end)
	for _, player in ipairs(Players:GetPlayers()) do
		watch(player)
	end
	Players.PlayerAdded:Connect(watch)
	Players.PlayerRemoving:Connect(function(player)
		lastRequest[player] = nil
	end)
end

return CrouchService
