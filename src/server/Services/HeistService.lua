-- Server logic of one heist, first house (md: «Подготовка первого ограбления», «Упаковка отца в мешок», «Сила, гантель и
-- перенос мешка», «Поимка и повторная попытка», «Граница участка и доставка»). Built on HouseInteractionService (key,
-- ladder, doors, hiding spots) and FamilyNpcService (chase, catch).
--
-- Player attributes (server-authoritative; the notebook UI only reads them):
--   HasBag            bag obtained (the hardware-store errand grants it: HeistService.GrantBag)
--   HasSpareKey       path A prepared (set when the key is taken in the shed)
--   HasLadder / LadderPlaced   path B: ladder item in hand / ladder set up under the balcony (only the latter counts)
--   HeistReady        bag AND (path A OR path B)  -- the only hard requirement (md)
--   RunStat, StrengthStat      training progress (Gym will call AddRun / AddStrength)
--   HeistTargetDad, RunRecommended (N), StrengthRecommended (M)   advice only, never a lock
--   CarryingDad       id of the father in the bag ("" when none)
--   Packing           true while the hold-to-pack progress is running
--   HeistHint         short text for the notebook / toast (reuses HouseHint for toasts)
--
-- Father model in the house: tag "FamilyFather" + attribute DadId (the prompt is created here). Delivery target: any Part
-- tagged "HeistDelivery" (the mistress' apartment entrance, not built yet) with an optional ProximityPrompt.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local DadCatalog = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("DadCatalog"))
local FamilyNpcService = require(script.Parent.FamilyNpcService)

local HeistService = {}

-- PROVISIONAL: the md leaves every number open ("Конкретные N, темп тренировки и формула ... ещё не выбраны").
local CONFIG = {
	PackSeconds = 4,           -- hold time of «Забрать в мешок» ("несколько секунд")
	MinCarryFactor = 0.3,      -- weakest possible carrying speed factor: "крайне медленно", never zero
	PackDistance = 8,
	RewardMode = "CatalogCost", -- one-time reward for a delivery: the catalog Cost of the father until the owner sets numbers
	FatherRestoreSeconds = 0,  -- md open question: how the target is restored after a delivery (0 = immediately)
	-- recommended run N and strength M by rarity (rarer fathers need more strength)
	Recommended = {
		Common = { run = 10, strength = 10 },
		Uncommon = { run = 20, strength = 25 },
		Rare = { run = 35, strength = 45 },
		Epic = { run = 55, strength = 70 },
		Legendary = { run = 80, strength = 100 },
	},
}

local state = {} -- [Player] = { carrying = { dadId, father, home, bag, baseSpeed } | nil, packing = prompt | nil, frozenSpeed = number | nil }
local packedFolder

HeistService.Delivered = Instance.new("BindableEvent") -- fires (player, dadId, reward)
HeistService.Config = CONFIG

local function catalogEntry(dadId)
	return DadCatalog.GetById(dadId)
end

local function hint(player, text)
	if player and player.Parent then
		player:SetAttribute("HeistHint", text)
		player:SetAttribute("HouseHint", text)
		player:SetAttribute("HouseHintSeq", (player:GetAttribute("HouseHintSeq") or 0) + 1)
	end
end

local function humanoidOf(player)
	local character = player.Character
	return character and character:FindFirstChildOfClass("Humanoid"), character
end

local function recommendedFor(dadId)
	local entry = catalogEntry(dadId)
	return CONFIG.Recommended[entry and entry.Rarity or "Common"] or CONFIG.Recommended.Common
end

local function refreshTarget(player)
	local dadId = player:GetAttribute("HeistTargetDad") or "RegularDad"
	local rec = recommendedFor(dadId)
	player:SetAttribute("HeistTargetDad", dadId)
	player:SetAttribute("RunRecommended", rec.run)
	player:SetAttribute("StrengthRecommended", rec.strength)
end

local function refreshReady(player)
	local pathA = player:GetAttribute("HasSpareKey") == true
	local pathB = player:GetAttribute("LadderPlaced") == true -- md: path B = the ladder is set up under the balcony
	player:SetAttribute("HeistReady", player:GetAttribute("HasBag") == true and (pathA or pathB))
end

-- ------------------------------------------------------------------------------------------------------------
-- movement while carrying
-- ------------------------------------------------------------------------------------------------------------
local function baseSpeed(player)
	local humanoid = humanoidOf(player)
	local base = humanoid and humanoid:GetAttribute("BaseWalkSpeed")
	if not base and humanoid then
		base = humanoid.WalkSpeed
		humanoid:SetAttribute("BaseWalkSpeed", base)
	end
	return base or 16
end

local function carryFactor(player)
	local dadId = player:GetAttribute("CarryingDad")
	local rec = recommendedFor(dadId)
	local strength = player:GetAttribute("StrengthStat") or 0
	return math.clamp(strength / rec.strength, CONFIG.MinCarryFactor, 1)
end

local function applySpeed(player)
	local humanoid = humanoidOf(player)
	if not humanoid then
		return
	end
	local base = baseSpeed(player) -- record the untouched values before anything is changed
	if humanoid:GetAttribute("BaseJumpPower") == nil then
		humanoid:SetAttribute("BaseJumpPower", humanoid.JumpPower)
	end
	local s = state[player]
	if s and s.packing then
		humanoid.WalkSpeed = 0 -- hold-to-pack: no movement
		humanoid.JumpPower = 0
		return
	end
	humanoid.JumpPower = humanoid:GetAttribute("BaseJumpPower")
	if s and s.carrying then
		humanoid.WalkSpeed = base * carryFactor(player)
	else
		humanoid.WalkSpeed = base
	end
end

-- ------------------------------------------------------------------------------------------------------------
-- the bag
-- ------------------------------------------------------------------------------------------------------------
local function makeBag(character)
	local torso = character:FindFirstChild("UpperTorso") or character:FindFirstChild("Torso") or character:FindFirstChild("HumanoidRootPart")
	if not torso then
		return nil
	end
	-- items never take part in detection (md): the bag is not a sight blocker target, it is cosmetic and non-colliding
	local bag = Instance.new("Part")
	bag.Name = "DadBag"
	bag.Size = Vector3.new(2.2, 2.8, 1.6)
	bag.Color = Color3.fromRGB(150, 110, 70)
	bag.Material = Enum.Material.Fabric
	bag.CanCollide, bag.CanQuery, bag.CanTouch, bag.Massless = false, false, false, true
	bag.CFrame = torso.CFrame * CFrame.new(0, 0.2, 1.4)
	bag.Parent = character
	local weld = Instance.new("WeldConstraint")
	weld.Part0, weld.Part1 = torso, bag
	weld.Parent = bag
	return bag
end

local function restoreFather(carry)
	local father = carry.father
	if father then
		father:PivotTo(carry.home)
		father.Parent = carry.parentBefore or workspace
	end
end

local function clearCarry(player, returnFather)
	local s = state[player]
	local carry = s and s.carrying
	if not carry then
		return
	end
	s.carrying = nil
	if carry.bag then
		carry.bag:Destroy()
	end
	if returnFather then
		restoreFather(carry)
	end
	player:SetAttribute("CarryingDad", "")
	applySpeed(player)
end

-- ------------------------------------------------------------------------------------------------------------
-- father: hold to pack
-- ------------------------------------------------------------------------------------------------------------
local function distanceOk(player, part)
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	return root ~= nil and (root.Position - part.Position).Magnitude <= CONFIG.PackDistance
end

local function canPack(player, father)
	local s = state[player]
	if not s or s.carrying then
		return false, "Вы уже несёте отца"
	end
	if player:GetAttribute("HasBag") ~= true then
		return false, "Нужен мешок"
	end
	if father.Parent == nil or father.Parent == packedFolder then
		return false, nil
	end
	return true
end

local function bindFather(father)
	local part = father:FindFirstChild("UpperTorso") or father.PrimaryPart or father:FindFirstChildWhichIsA("BasePart")
	if not part then
		return
	end
	local prompt = part:FindFirstChild("PackPrompt") or Instance.new("ProximityPrompt")
	prompt.Name = "PackPrompt"
	prompt.ActionText = "Забрать в мешок"
	prompt.ObjectText = (catalogEntry(father:GetAttribute("DadId")) or { DisplayName = "Отец" }).DisplayName
	prompt.HoldDuration = CONFIG.PackSeconds
	prompt.MaxActivationDistance = 7
	prompt.RequiresLineOfSight = false
	prompt.KeyboardKeyCode = Enum.KeyCode.E
	prompt.Parent = part
	local home = father:GetPivot()
	local parentBefore = father.Parent

	prompt.PromptButtonHoldBegan:Connect(function(player)
		local ok, why = canPack(player, father)
		if not ok then
			if why then
				hint(player, why)
			end
			return
		end
		local s = state[player]
		s.packing = prompt
		s.packBeganAt, s.packEndedAt = os.clock(), nil
		player:SetAttribute("Packing", true)
		applySpeed(player)
		hint(player, "Упаковка… не двигайтесь")
	end)

	prompt.PromptButtonHoldEnded:Connect(function(player)
		-- the engine may report the end of the hold just before Triggered; Triggered validates through packBeganAt
		local s = state[player]
		if s and s.packing then
			s.packEndedAt = os.clock()
			s.packing = nil
			player:SetAttribute("Packing", false)
			applySpeed(player)
		end
	end)

	prompt.Triggered:Connect(function(player)
		local s = state[player]
		-- the hold must really have run its full time (a Triggered without a validated hold is ignored)
		local began = s and s.packBeganAt
		if not began then
			return
		end
		local held = (s.packEndedAt or os.clock()) - began
		if held < prompt.HoldDuration - 0.4 then
			return
		end
		s.packBeganAt, s.packEndedAt = nil, nil
		s.packing = nil
		player:SetAttribute("Packing", false)
		local ok = canPack(player, father) and distanceOk(player, part)
		if not ok then
			applySpeed(player)
			return
		end
		local dadId = father:GetAttribute("DadId") or "RegularDad"
		father.Parent = packedFolder
		local _, character = humanoidOf(player)
		s.carrying = { dadId = dadId, father = father, home = home, parentBefore = parentBefore, bag = character and makeBag(character) }
		player:SetAttribute("HeistTargetDad", dadId)
		player:SetAttribute("CarryingDad", dadId)
		refreshTarget(player)
		applySpeed(player)
		hint(player, "Отец в мешке")
	end)
end

-- ------------------------------------------------------------------------------------------------------------
-- caught / delivery
-- ------------------------------------------------------------------------------------------------------------
local function onCaught(player)
	local s = state[player]
	if s and s.packing then
		s.packing = nil
		player:SetAttribute("Packing", false)
	end
	local carrying = s and s.carrying
	clearCarry(player, true) -- the father goes back home; preparation attributes are untouched and no cash is taken (md)
	applySpeed(player)
	hint(player, carrying and "Вас поймали. Отец вернулся домой. Подготовка сохранена" or "Вас поймали. Подготовка сохранена")
end

-- Returns "none" (not carrying), "blocked" (the family is still chasing) or "delivered".
local function deliver(player, quietWithoutCarry)
	local s = state[player]
	local carry = s and s.carrying
	if not carry then
		if not quietWithoutCarry then
			hint(player, "Сначала заберите отца")
		end
		return "none"
	end
	if FamilyNpcService.IsPursued(player) then
		hint(player, "Сначала избавься от хвоста")
		return "blocked"
	end
	local entry = catalogEntry(carry.dadId)
	local reward = entry and entry.Cost or 0
	local ok, PlayerDataService = pcall(function()
		return require(script.Parent.PlayerDataService)
	end)
	if ok and PlayerDataService and PlayerDataService.AddCash and reward > 0 then
		PlayerDataService.AddCash(player, reward)
	end
	clearCarry(player, false)
	local father, home, parentBefore = carry.father, carry.home, carry.parentBefore
	local function restore()
		if father and father.Parent == packedFolder then
			father:PivotTo(home)
			father.Parent = parentBefore or workspace
		end
	end
	if CONFIG.FatherRestoreSeconds > 0 then
		task.delay(CONFIG.FatherRestoreSeconds, restore)
	else
		restore()
	end
	hint(player, ("Отец доставлен! Награда: %d"):format(reward))
	HeistService.Delivered:Fire(player, carry.dadId, reward)
	return "delivered"
end

-- Used by the apartment entrance: entering with the bag delivers the father once the chase is over; while pursued the
-- entrance stays closed («Сначала избавься от хвоста»). Without a bag the caller just walks in.
function HeistService.TryDeliver(player)
	return deliver(player, true)
end

local function bindDelivery(part)
	local prompt = part:FindFirstChildOfClass("ProximityPrompt")
	if not prompt then
		prompt = Instance.new("ProximityPrompt")
		prompt.ActionText = "Войти"
		prompt.ObjectText = "Квартира"
		prompt.MaxActivationDistance = 8
		prompt.Parent = part
	end
	prompt.Triggered:Connect(function(player)
		deliver(player, false)
	end)
end

-- errand givers: parts tagged "HeistBagShop" (hardware store: the bag) and "HeistLadderGiver" (workshop worker: the ladder).
-- PROVISIONAL: the real errands (what the mistress asks, prices, conditions) are not defined in the md, so these hand the
-- item over with one prompt press.
local function bindGiver(part, actionText, objectText, grant, doneText)
	local prompt = part:FindFirstChildOfClass("ProximityPrompt") or Instance.new("ProximityPrompt")
	prompt.ActionText = actionText
	prompt.ObjectText = objectText
	prompt.MaxActivationDistance = 8
	prompt.Parent = part
	prompt.Triggered:Connect(function(player)
		grant(player)
		hint(player, doneText)
	end)
end

local function bindBagShop(part)
	bindGiver(part, "Взять мешок", "Хозяйственный магазин", function(player)
		HeistService.GrantBag(player)
	end, "Мешок получен")
end

local function bindLadderGiver(part)
	bindGiver(part, "Взять приставную лестницу", "Мастерская", function(player)
		if player:GetAttribute("LadderPlaced") ~= true then
			HeistService.GrantLadder(player)
		end
	end, "Лестница получена: установите её под балконом")
end

-- ------------------------------------------------------------------------------------------------------------
-- public API / setup
-- ------------------------------------------------------------------------------------------------------------
function HeistService.GrantBag(player)
	player:SetAttribute("HasBag", true)
	refreshReady(player)
end

function HeistService.GrantLadder(player)
	player:SetAttribute("HasLadder", true)
	refreshReady(player)
end

function HeistService.AddRun(player, amount)
	player:SetAttribute("RunStat", (player:GetAttribute("RunStat") or 0) + math.max(0, amount))
end

function HeistService.AddStrength(player, amount)
	player:SetAttribute("StrengthStat", (player:GetAttribute("StrengthStat") or 0) + math.max(0, amount))
	applySpeed(player)
end

function HeistService.IsCarrying(player)
	local s = state[player]
	return s ~= nil and s.carrying ~= nil
end

local function watch(player)
	state[player] = { carrying = nil, packing = nil }
	for _, name in ipairs({ "HasBag", "HasSpareKey", "HasLadder", "LadderPlaced", "Packing" }) do
		if player:GetAttribute(name) == nil then
			player:SetAttribute(name, false)
		end
	end
	player:SetAttribute("RunStat", player:GetAttribute("RunStat") or 0)
	player:SetAttribute("StrengthStat", player:GetAttribute("StrengthStat") or 0)
	player:SetAttribute("CarryingDad", "")
	refreshTarget(player)
	refreshReady(player)
	for _, name in ipairs({ "HasBag", "HasSpareKey", "HasLadder", "LadderPlaced" }) do
		player:GetAttributeChangedSignal(name):Connect(function()
			refreshReady(player)
		end)
	end
	player:GetAttributeChangedSignal("StrengthStat"):Connect(function()
		applySpeed(player)
	end)
	player.CharacterAdded:Connect(function()
		-- a new body: the carried father goes home (the player died or reset), preparation stays
		local s = state[player]
		if s then
			s.packing = nil
			player:SetAttribute("Packing", false)
		end
		clearCarry(player, true)
	end)
end

function HeistService.Initialize()
	packedFolder = ServerStorage:FindFirstChild("PackedDads") or Instance.new("Folder")
	packedFolder.Name = "PackedDads"
	packedFolder.Parent = ServerStorage

	for _, father in ipairs(CollectionService:GetTagged("FamilyFather")) do
		bindFather(father)
	end
	CollectionService:GetInstanceAddedSignal("FamilyFather"):Connect(bindFather)
	for _, part in ipairs(CollectionService:GetTagged("HeistDelivery")) do
		bindDelivery(part)
	end
	CollectionService:GetInstanceAddedSignal("HeistDelivery"):Connect(bindDelivery)
	for _, part in ipairs(CollectionService:GetTagged("HeistBagShop")) do
		bindBagShop(part)
	end
	CollectionService:GetInstanceAddedSignal("HeistBagShop"):Connect(bindBagShop)
	for _, part in ipairs(CollectionService:GetTagged("HeistLadderGiver")) do
		bindLadderGiver(part)
	end
	CollectionService:GetInstanceAddedSignal("HeistLadderGiver"):Connect(bindLadderGiver)

	for _, player in ipairs(Players:GetPlayers()) do
		watch(player)
	end
	Players.PlayerAdded:Connect(watch)
	Players.PlayerRemoving:Connect(function(player)
		clearCarry(player, true) -- leaving mid-carry: the target is restored (what is saved is an open question in the md)
		state[player] = nil
	end)
	FamilyNpcService.PlayerCaught.Event:Connect(onCaught)
end

return HeistService
