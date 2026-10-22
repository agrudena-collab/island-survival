-- Server-authoritative interactions of the family house: swinging doors (with outside locks), hiding spots
-- (wardrobe, laundry cupboard), the spare key in the shed and the balcony ladder.
-- Objects are plain instances found through CollectionService tags, so the house model can be placed anywhere:
--   HouseDoor  : Model  { Leaf* Parts (attrs Hinge:Vector3, OpenAngle:number, ClosedCFrame:CFrame), PromptPart }; attrs DoorId, Open, LockedFromOutside, RequiresItem, InsideDir
--   HideSpot   : Model  { Leaf* Parts, HidePoint, ExitPoint, EnterPart, InsidePart }; attrs SpotId
--   SpareKey   : Part   (ProximityPrompt inside)
--   LadderSpot : Model  { SpotPart (prompt), Ladder Model (hidden until placed), ClimbTruss }
-- Player attributes used: HasSpareKey, HasLadder, IsHiding, HidingSpot, HouseHint. NPC code can call SetDoorOpen / IsPlayerHidden.

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")

local HouseInteractionService = {}

local TAGS = {
	Door = "HouseDoor",
	Hide = "HideSpot",
	Key = "SpareKey",
	Ladder = "LadderSpot",
}
local MAX_DISTANCE = 14
local SWING_TIME = 0.45

local bound = {}
local hiddenIn = {} -- [Player] = spot Model

local function hint(player, text)
	if player and player.Parent then
		player:SetAttribute("HouseHint", text)
		-- the sequence number lets the client show the same hint again (an unchanged attribute fires no event)
		player:SetAttribute("HouseHintSeq", (player:GetAttribute("HouseHintSeq") or 0) + 1)
	end
end

local function distanceOk(player, part)
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	return root ~= nil and part ~= nil and (root.Position - part.Position).Magnitude <= MAX_DISTANCE
end

local function leaves(model)
	local list = {}
	for _, child in ipairs(model:GetChildren()) do
		if child:IsA("BasePart") and string.sub(child.Name, 1, 4) == "Leaf" then
			table.insert(list, child)
		end
	end
	return list
end

local function swingLeaf(leaf, open)
	local hinge = leaf:GetAttribute("Hinge")
	local closed = leaf:GetAttribute("ClosedCFrame")
	local angle = math.rad(leaf:GetAttribute("OpenAngle") or 90)
	if not hinge or not closed then
		return
	end
	local value = leaf:FindFirstChild("Angle")
	if not value then
		value = Instance.new("NumberValue")
		value.Name = "Angle"
		value.Parent = leaf
		value.Changed:Connect(function(a)
			leaf.CFrame = CFrame.new(hinge) * CFrame.Angles(0, a, 0) * CFrame.new(-hinge) * closed
		end)
	end
	-- An open leaf must never block a passage (it would trap players and NPCs against the frame): it is solid only
	-- while closed. Opening releases it at once; it becomes solid again when the closing swing has finished.
	local token = (leaf:GetAttribute("SwingToken") or 0) + 1
	leaf:SetAttribute("SwingToken", token)
	if open then
		leaf.CanCollide = false
	else
		task.delay(SWING_TIME, function()
			if leaf.Parent and leaf:GetAttribute("SwingToken") == token then
				leaf.CanCollide = true
			end
		end)
	end
	TweenService:Create(value, TweenInfo.new(SWING_TIME, Enum.EasingStyle.Quad), { Value = open and angle or 0 }):Play()
end

local function setLeavesOpen(model, open)
	model:SetAttribute("Open", open)
	for _, leaf in ipairs(leaves(model)) do
		swingLeaf(leaf, open)
	end
end

-- Public: open or close a door/hiding-spot model. Server side only (NPCs call this directly).
function HouseInteractionService.SetDoorOpen(model, open)
	if model and model.Parent then
		setLeavesOpen(model, open)
	end
end

-- NPC helper: opens every tagged door whose centre is within `radius` of `position`, and closes it again after
-- `closeAfter` seconds unless another call has re-armed it. Door leaves carry a PassThrough PathfindingModifier,
-- so a path may cross a closed door; the NPC calls this when it gets near one. Returns the doors it opened.
function HouseInteractionService.OpenDoorsNear(position, radius, closeAfter)
	local opened = {}
	for _, model in ipairs(CollectionService:GetTagged(TAGS.Door)) do
		local promptPart = model:FindFirstChild("PromptPart")
		if promptPart and (promptPart.Position - position).Magnitude <= radius then
			setLeavesOpen(model, true)
			table.insert(opened, model)
			local token = (model:GetAttribute("CloseToken") or 0) + 1
			model:SetAttribute("CloseToken", token)
			task.delay(closeAfter or 4, function()
				if model.Parent and model:GetAttribute("CloseToken") == token then
					setLeavesOpen(model, false)
				end
			end)
		end
	end
	return opened
end

-- Server side: pulls a hidden player out of their hiding spot (used when the family catches them).
function HouseInteractionService.ReleasePlayer(player)
	if hiddenIn[player] then
		HouseInteractionService._leaveSpot(player)
	end
end

function HouseInteractionService.IsPlayerHidden(player)
	return player:GetAttribute("IsHiding") == true
end

local function isOutside(model, player)
	local inside = model:GetAttribute("InsideDir")
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	local prompt = model:FindFirstChild("PromptPart")
	if not (inside and root and prompt) then
		return false
	end
	return (root.Position - prompt.Position):Dot(inside) < 0
end

local function bindDoor(model)
	local promptPart = model:FindFirstChild("PromptPart")
	local prompt = promptPart and promptPart:FindFirstChildOfClass("ProximityPrompt")
	if not prompt then
		return
	end
	prompt.Triggered:Connect(function(player)
		if not distanceOk(player, promptPart) then
			return
		end
		local isOpen = model:GetAttribute("Open") == true
		if not isOpen and model:GetAttribute("LockedFromOutside") == true and isOutside(model, player) then
			local item = model:GetAttribute("RequiresItem")
			if not item or player:GetAttribute(item) ~= true then
				hint(player, item and "Дверь заперта. Нужен ключ" or "Дверь заперта")
				return
			end
		end
		setLeavesOpen(model, not isOpen)
	end)
end

local function placeInside(player, spot, point)
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if root and point then
		root.Anchored = true
		root.CFrame = point.CFrame * CFrame.new(0, 3, 0)
	end
end

local function leaveSpot(player)
	local spot = hiddenIn[player]
	if not spot then
		return
	end
	hiddenIn[player] = nil
	player:SetAttribute("IsHiding", false)
	player:SetAttribute("HidingSpot", "")
	setLeavesOpen(spot, true)
	-- Only one of the two prompts may be live: the entry prompt would otherwise win the E button over the exit one.
	local insidePart = spot:FindFirstChild("InsidePart")
	local exitPrompt = insidePart and insidePart:FindFirstChildOfClass("ProximityPrompt")
	local enterPart = spot:FindFirstChild("EnterPart")
	local enterPrompt = enterPart and enterPart:FindFirstChildOfClass("ProximityPrompt")
	if exitPrompt then
		exitPrompt.Enabled = false
	end
	if enterPrompt then
		enterPrompt.Enabled = true
	end
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	local exitPoint = spot:FindFirstChild("ExitPoint")
	if root then
		if exitPoint then
			root.CFrame = exitPoint.CFrame * CFrame.new(0, 3, 0)
		end
		root.Anchored = false
	end
end

local function bindHideSpot(model)
	local enterPart = model:FindFirstChild("EnterPart")
	local insidePart = model:FindFirstChild("InsidePart")
	local enter = enterPart and enterPart:FindFirstChildOfClass("ProximityPrompt")
	local exit = insidePart and insidePart:FindFirstChildOfClass("ProximityPrompt")
	if exit then
		exit.Enabled = false
	end
	if enter then
		enter.Triggered:Connect(function(player)
			if hiddenIn[player] or not distanceOk(player, enterPart) then
				return
			end
			for _, other in pairs(hiddenIn) do
				if other == model then
					hint(player, "Здесь уже кто-то прячется")
					return
				end
			end
			hiddenIn[player] = model
			enter.Enabled = false
			if exit then
				exit.Enabled = true
			end
			setLeavesOpen(model, true)
			task.delay(SWING_TIME, function()
				if hiddenIn[player] == model then
					placeInside(player, model, model:FindFirstChild("HidePoint"))
					setLeavesOpen(model, false)
					player:SetAttribute("IsHiding", true)
					player:SetAttribute("HidingSpot", model:GetAttribute("SpotId") or model.Name)
				end
			end)
		end)
	end
	if exit then
		exit.Triggered:Connect(function(player)
			if hiddenIn[player] == model then
				leaveSpot(player)
			end
		end)
	end
end

local function hideItem(item)
	for _, d in ipairs(item:GetDescendants()) do
		if d:IsA("BasePart") then
			d:SetAttribute("T0", d.Transparency)
			d:SetAttribute("C0", d.CanCollide)
			d.Transparency = 1
			d.CanCollide = false
		end
	end
end

local function showItem(item)
	for _, d in ipairs(item:GetDescendants()) do
		if d:IsA("BasePart") then
			local t0 = d:GetAttribute("T0")
			d.Transparency = (d.Name == "ClimbTruss") and 1 or (t0 or 0)
			d.CanCollide = d:GetAttribute("C0") == true
		end
	end
end

local function bindKey(part)
	local prompt = part:FindFirstChildOfClass("ProximityPrompt")
	if not prompt then
		return
	end
	prompt.Triggered:Connect(function(player)
		if not distanceOk(player, part) or part:GetAttribute("Taken") == true then
			return
		end
		player:SetAttribute("HasSpareKey", true)
		hint(player, "Запасной ключ взят")
		part:SetAttribute("Taken", true)
		prompt.Enabled = false
		for _, d in ipairs(part:GetDescendants()) do
			if d:IsA("BasePart") then
				d.Transparency = 1
			end
		end
		part.Transparency = 1
	end)
end

local function bindLadder(model)
	local spot = model:FindFirstChild("SpotPart")
	local ladder = model:FindFirstChild("Ladder")
	local prompt = spot and spot:FindFirstChildOfClass("ProximityPrompt")
	if not (spot and ladder and prompt) then
		return
	end
	hideItem(ladder)
	model:SetAttribute("Placed", false)
	prompt.Triggered:Connect(function(player)
		if model:GetAttribute("Placed") == true or not distanceOk(player, spot) then
			return
		end
		if player:GetAttribute("HasLadder") ~= true then
			hint(player, "Нужна приставная лестница")
			return
		end
		player:SetAttribute("HasLadder", false)
		player:SetAttribute("LadderPlaced", true) -- path B stays prepared after the ladder item is used
		model:SetAttribute("Placed", true)
		prompt.Enabled = false
		showItem(ladder)
		hint(player, "Лестница установлена")
	end)
end

local binders = {
	[TAGS.Door] = bindDoor,
	[TAGS.Hide] = bindHideSpot,
	[TAGS.Key] = bindKey,
	[TAGS.Ladder] = bindLadder,
}

local function bind(tag, instance)
	if bound[instance] then
		return
	end
	bound[instance] = true
	binders[tag](instance)
end

function HouseInteractionService.Initialize()
	for tag in pairs(binders) do
		for _, instance in ipairs(CollectionService:GetTagged(tag)) do
			bind(tag, instance)
		end
		CollectionService:GetInstanceAddedSignal(tag):Connect(function(instance)
			bind(tag, instance)
		end)
	end
	Players.PlayerRemoving:Connect(function(player)
		local spot = hiddenIn[player]
		if spot then
			hiddenIn[player] = nil
			local enterPart = spot:FindFirstChild("EnterPart")
			local enterPrompt = enterPart and enterPart:FindFirstChildOfClass("ProximityPrompt")
			local insidePart = spot:FindFirstChild("InsidePart")
			local exitPrompt = insidePart and insidePart:FindFirstChildOfClass("ProximityPrompt")
			if enterPrompt then
				enterPrompt.Enabled = true
			end
			if exitPrompt then
				exitPrompt.Enabled = false
			end
			setLeavesOpen(spot, true)
		end
	end)
end

-- Test helpers (server): bind everything that is tagged right now.
HouseInteractionService._bind = bind
HouseInteractionService._leaveSpot = leaveSpot

return HouseInteractionService
