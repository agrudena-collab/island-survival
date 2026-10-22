-- Crouch input: toggled with C on PC, with an on-screen button on touch devices (md: proposal "кнопкой C на ПК и
-- экранная кнопка на телефоне"; the exact control is not an owner decision yet). The client only requests the state;
-- the server validates it (CrouchService) and publishes the player attribute `Crouching`.
local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local CrouchController = {}

local ACTION = "Crouch"
local TITLE_STAND = "Присесть"
local TITLE_CROUCH = "Встать"

function CrouchController.Initialize()
	local player = Players.LocalPlayer
	local remotes = ReplicatedStorage:WaitForChild("Remotes")
	local remote = remotes:WaitForChild("SetCrouch")

	local function handle(_, state)
		if state ~= Enum.UserInputState.Begin then
			return Enum.ContextActionResult.Pass
		end
		remote:FireServer(player:GetAttribute("Crouching") ~= true)
		return Enum.ContextActionResult.Sink
	end

	ContextActionService:BindAction(ACTION, handle, true, Enum.KeyCode.C)
	ContextActionService:SetPosition(ACTION, UDim2.new(1, -150, 1, -190))
	ContextActionService:SetTitle(ACTION, TITLE_STAND)

	player:GetAttributeChangedSignal("Crouching"):Connect(function()
		ContextActionService:SetTitle(ACTION, player:GetAttribute("Crouching") == true and TITLE_CROUCH or TITLE_STAND)
	end)
end

return CrouchController
