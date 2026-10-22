-- Server side of the mistress dialogue (md: the player walks to her table, a dialogue with a choice of phrases starts).
-- A Part tagged "MistressDesk" (the desk she sits at; attribute DadId, default RegularDad) gets a «Поговорить» prompt.
-- The server owns the session: it sends the current node and validates every choice index, so a client can only pick the
-- phrases that node actually offers. Effects: AcceptPlan sets the player attribute PlanAccepted (shown in the notebook).
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Remotes = require(Shared:WaitForChild("Remotes"))
local Dialogue = require(Shared:WaitForChild("MistressDialogue"))

local DialogueService = {}

local MAX_DISTANCE = 12
local sessions = {} -- [Player] = { node = id, desk = Part }

local function fill(text, player)
	return (string.gsub(text, "{(%w+)}", function(key)
		if key == "N" then
			return tostring(player:GetAttribute("RunRecommended") or "?")
		elseif key == "M" then
			return tostring(player:GetAttribute("StrengthRecommended") or "?")
		end
		return "{" .. key .. "}"
	end))
end

local function nearDesk(player, desk)
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	return root ~= nil and desk.Parent ~= nil and (root.Position - desk.Position).Magnitude <= MAX_DISTANCE
end

local function send(player, nodeId)
	local node = Dialogue.Nodes[nodeId]
	local remote = ReplicatedStorage.Remotes[Remotes.Events.DialogueNode]
	if not node then
		sessions[player] = nil
		remote:FireClient(player, nil)
		return
	end
	local choices = {}
	for _, choice in ipairs(node.choices) do
		table.insert(choices, choice.text)
	end
	if node.ends then
		sessions[player] = nil
	end
	remote:FireClient(player, { text = fill(node.text, player), choices = choices, ends = node.ends == true })
end

local function open(player, desk)
	if sessions[player] or not nearDesk(player, desk) then
		return
	end
	player:SetAttribute("HeistTargetDad", desk:GetAttribute("DadId") or player:GetAttribute("HeistTargetDad") or "RegularDad")
	sessions[player] = { node = Dialogue.Start, desk = desk }
	send(player, Dialogue.Start)
end

local function choose(player, index)
	local session = sessions[player]
	if not session or type(index) ~= "number" or index % 1 ~= 0 then
		return
	end
	if not nearDesk(player, session.desk) then
		sessions[player] = nil
		ReplicatedStorage.Remotes[Remotes.Events.DialogueNode]:FireClient(player, nil)
		return
	end
	local node = Dialogue.Nodes[session.node]
	local choice = node and node.choices[index]
	if not choice then
		return
	end
	if choice.effect == "AcceptPlan" then
		player:SetAttribute("PlanAccepted", true)
	end
	session.node = choice.next
	send(player, choice.next)
end

local function bindDesk(desk)
	local prompt = desk:FindFirstChildOfClass("ProximityPrompt") or Instance.new("ProximityPrompt")
	prompt.ActionText = "Поговорить"
	prompt.ObjectText = "Любовница"
	prompt.MaxActivationDistance = 9
	prompt.RequiresLineOfSight = false -- the tea set on the table must not hide the prompt
	prompt.Parent = desk
	prompt.Triggered:Connect(function(player)
		open(player, desk)
	end)
end

function DialogueService.Initialize()
	local folder = ReplicatedStorage:WaitForChild("Remotes")
	folder:WaitForChild(Remotes.Events.DialogueChoose).OnServerEvent:Connect(choose)
	for _, desk in ipairs(CollectionService:GetTagged("MistressDesk")) do
		bindDesk(desk)
	end
	CollectionService:GetInstanceAddedSignal("MistressDesk"):Connect(bindDesk)
	Players.PlayerRemoving:Connect(function(player)
		sessions[player] = nil
	end)
end

-- closing from the client (leaving the dialogue panel) is also validated: the session just ends
function DialogueService.Close(player)
	sessions[player] = nil
end

return DialogueService
