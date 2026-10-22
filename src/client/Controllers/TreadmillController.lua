-- Client half of treadmill training: while the server marks the local player as training (attribute TrainingTreadmill)
-- the character keeps running forward on the spot (the belt carries it backwards). Jumping ends the training; that is
-- decided on the server (GymService), this script only stops pushing once the attribute goes false.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local TreadmillController = {}

function TreadmillController.Initialize()
	local player = Players.LocalPlayer
	local connection

	local function stop()
		if connection then
			connection:Disconnect()
			connection = nil
		end
	end

	local function start()
		stop()
		connection = RunService.RenderStepped:Connect(function()
			local character = player.Character
			local humanoid = character and character:FindFirstChildOfClass("Humanoid")
			local forward = player:GetAttribute("TreadmillForward")
			if not (humanoid and typeof(forward) == "Vector3") then
				return
			end
			humanoid:Move(Vector3.new(forward.X, 0, forward.Z), false)
		end)
	end

	player:GetAttributeChangedSignal("TrainingTreadmill"):Connect(function()
		if player:GetAttribute("TrainingTreadmill") == true then
			start()
		else
			stop()
		end
	end)
end

return TreadmillController
