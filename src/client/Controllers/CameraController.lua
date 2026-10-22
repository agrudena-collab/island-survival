-- Hiding camera: while the server marks the local player as hidden (attribute IsHiding), the camera sits inside the
-- hiding spot and looks out through a narrow slit; the spot's doors become see-through for this player only.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local CameraController = {}

local EYE_HEIGHT = 1.6 -- above the player's root part while hidden
local LOOK_YAW = math.rad(35)
local LOOK_PITCH = math.rad(15)
local SENSITIVITY = 0.003
local SLIT_HEIGHT = 0.22 -- fraction of the screen left open
local RENDER_NAME = "HideCamera"

local player = Players.LocalPlayer
local active = false
local yaw, pitch = 0, 0
local spotParts = {}
local savedCameraType = Enum.CameraType.Custom
local gui

local function findSpot()
	local id = player:GetAttribute("HidingSpot")
	for _, spot in ipairs(CollectionService:GetTagged("HideSpot")) do
		if (spot:GetAttribute("SpotId") or spot.Name) == id then
			return spot
		end
	end
	return nil
end

local function makeSlit()
	local screen = Instance.new("ScreenGui")
	screen.Name = "HideSlit"
	screen.IgnoreGuiInset = true
	screen.ResetOnSpawn = false
	for _, top in ipairs({ true, false }) do
		local bar = Instance.new("Frame")
		bar.BackgroundColor3 = Color3.new(0, 0, 0)
		bar.BorderSizePixel = 0
		bar.Size = UDim2.fromScale(1, (1 - SLIT_HEIGHT) / 2)
		bar.Position = top and UDim2.fromScale(0, 0) or UDim2.fromScale(0, 1 - (1 - SLIT_HEIGHT) / 2)
		bar.Parent = screen
	end
	screen.Parent = player:WaitForChild("PlayerGui")
	return screen
end

local function setSpotVisible(spot, visible)
	if not visible then
		for _, d in ipairs(spot:GetChildren()) do
			if d:IsA("BasePart") and string.sub(d.Name, 1, 4) == "Leaf" then
				d.LocalTransparencyModifier = 1
				table.insert(spotParts, d)
			end
		end
	else
		for _, d in ipairs(spotParts) do
			d.LocalTransparencyModifier = 0
		end
		table.clear(spotParts)
	end
end

local function stop()
	if not active then
		return
	end
	active = false
	RunService:UnbindFromRenderStep(RENDER_NAME)
	UserInputService.MouseBehavior = Enum.MouseBehavior.Default
	if gui then
		gui:Destroy()
		gui = nil
	end
	local camera = workspace.CurrentCamera
	camera.CameraType = savedCameraType
	for _, d in ipairs(spotParts) do
		d.LocalTransparencyModifier = 0
	end
	table.clear(spotParts)
end

local function start()
	local spot = findSpot()
	local hidePoint = spot and spot:FindFirstChild("HidePoint")
	local exitPoint = spot and spot:FindFirstChild("ExitPoint")
	if not (hidePoint and exitPoint) then
		return
	end
	local out = (exitPoint.Position - hidePoint.Position) * Vector3.new(1, 0, 1)
	if out.Magnitude < 0.01 then
		return
	end
	active = true
	yaw, pitch = 0, 0
	local base = CFrame.lookAt(Vector3.zero, out.Unit)
	local eye = hidePoint.Position + Vector3.new(0, 3 + EYE_HEIGHT, 0)
	local camera = workspace.CurrentCamera
	savedCameraType = camera.CameraType
	camera.CameraType = Enum.CameraType.Scriptable
	UserInputService.MouseBehavior = Enum.MouseBehavior.LockCenter
	setSpotVisible(spot, false)
	gui = makeSlit()
	RunService:BindToRenderStep(RENDER_NAME, Enum.RenderPriority.Camera.Value + 1, function()
		local delta = UserInputService:GetMouseDelta()
		yaw = math.clamp(yaw - delta.X * SENSITIVITY, -LOOK_YAW, LOOK_YAW)
		pitch = math.clamp(pitch - delta.Y * SENSITIVITY, -LOOK_PITCH, LOOK_PITCH)
		camera.CFrame = CFrame.new(eye) * base.Rotation * CFrame.Angles(0, yaw, 0) * CFrame.Angles(pitch, 0, 0)
	end)
end

function CameraController.Initialize()
	player:GetAttributeChangedSignal("IsHiding"):Connect(function()
		if player:GetAttribute("IsHiding") == true then
			start()
		else
			stop()
		end
	end)
end

-- Test helper: current hiding state.
function CameraController.IsActive()
	return active
end

return CameraController
