-- Creates the shared remote folder and named endpoints on the server.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Remotes = {
	Events = {
		PurchaseDad = "PurchaseDad",
		StealDad = "StealDad",
		BaseUpdated = "BaseUpdated",
		DataUpdated = "DataUpdated",
	},
	Functions = {
		GetPlayerData = "GetPlayerData",
	},
}

function Remotes.Initialize()
	local folder = ReplicatedStorage:FindFirstChild("Remotes")
	if not folder then
		folder = Instance.new("Folder")
		folder.Name = "Remotes"
		folder.Parent = ReplicatedStorage
	end

	for _, name in pairs(Remotes.Events) do
		if not folder:FindFirstChild(name) then
			local remote = Instance.new("RemoteEvent")
			remote.Name = name
			remote.Parent = folder
		end
	end
	for _, name in pairs(Remotes.Functions) do
		if not folder:FindFirstChild(name) then
			local remote = Instance.new("RemoteFunction")
			remote.Name = name
			remote.Parent = folder
		end
	end
	return folder
end

return Remotes
