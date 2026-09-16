-- Shows transient notifications sent by server-authoritative game services.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local player = Players.LocalPlayer
local remotes = ReplicatedStorage:WaitForChild("EscapeFacilityRemotes")
local notificationEvent = remotes:WaitForChild("NotificationEvent")

local screenGui = player:WaitForChild("PlayerGui"):WaitForChild("EscapeFacilityUI")
local notificationLabel = screenGui:WaitForChild("NotificationLabel")

local messageVersion = 0

notificationEvent.OnClientEvent:Connect(function(message)
	messageVersion += 1
	local thisMessageVersion = messageVersion

	notificationLabel.Text = message
	notificationLabel.TextTransparency = 0
	notificationLabel.BackgroundTransparency = 0.15
	notificationLabel.Visible = true

	task.delay(2.8, function()
		if thisMessageVersion ~= messageVersion then
			return
		end

		local fade = TweenService:Create(notificationLabel, TweenInfo.new(0.25), {
			TextTransparency = 1,
			BackgroundTransparency = 1,
		})
		fade:Play()
		fade.Completed:Wait()
		if thisMessageVersion == messageVersion then
			notificationLabel.Visible = false
		end
	end)
end)
