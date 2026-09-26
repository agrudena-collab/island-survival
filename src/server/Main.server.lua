local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Remotes = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Remotes"))
local Services = script.Parent:WaitForChild("Services")

Remotes.Initialize()

local serviceNames = {
	"PlayerDataService",
	"EconomyService",
	"DadService",
	"BaseService",
	"StealService",
	"RoundService",
}

for _, serviceName in ipairs(serviceNames) do
	local serviceModule = require(Services:WaitForChild(serviceName))
	if type(serviceModule) == "table" and type(serviceModule.Initialize) == "function" then
		serviceModule.Initialize()
	end
end
