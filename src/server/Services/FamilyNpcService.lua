-- Family NPCs of a family house (first house: wife + son): patrol routes with pauses, vision, chase, search, catch.
-- Data lives in the house model, so the house can be placed anywhere:
--   Model attribute/tag  : tag "FamilyHouse" on the house model
--   Folder "FamilyRoutes": Parts named "<Role>_<nn>" (Role = Wife | Son), ordered by name; feet-level positions.
--                          Attributes: Pause (seconds, default 0), Activity ("Cook" | "Fidget" | nil)
--                          The first part of a route is also the spawn point.
--   Part "FamilyLotBounds": box of the family lot; leaving it ends every chase at once (md: "Граница участка")
--   Part "CaughtSpawn"    : where a caught player reappears (md: "неподалёку от семейного дома")
--   Folder "LowCover"      : invisible boxes of low furniture (CanQuery only); a crouching player behind one is hidden
--   RDH_Collision folder   : walls and floors; together with closed door/cupboard leaves they block the line of sight
-- NPC models: ServerStorage.FamilyNpcModels.<Role> (R15 rigs, tag FamilyNPC). Animation is client side
-- (src/client/Controllers/FamilyAnimationController.lua); this service only moves the Humanoid and sets FamilyActivity.
-- Player attribute FamilyAlert: "Spotted" | "Searching" | "Clear" | "" for the UI (md item "Вас заметили / Вас ищут / Поиск прекращён").
-- Rules taken from the md: the family sees the PLAYER (never carried items); a hiding player is invisible unless the
-- NPC saw them enter the hiding spot; after losing sight the NPC goes to the last seen place and searches, without
-- tracking through walls; leaving the lot ends the chase; a caught attempt ends and the player reappears near the house.
local CollectionService = game:GetService("CollectionService")
local PathfindingService = game:GetService("PathfindingService")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local HouseInteractionService = require(script.Parent.HouseInteractionService)

local FamilyNpcService = {}

-- PROVISIONAL tuning: the md leaves ranges, durations and the capture criterion undefined ("Точные ... не определены").
-- The values below are only starting points for the prototype and must be set by the owner.
local CONFIG = {
	ViewRange = 40,            -- studs
	ViewFovDegrees = 120,      -- total horizontal field of view
	LoseSightSeconds = 1.5,    -- out of sight this long -> go to the last seen place
	SearchSeconds = 6,         -- look around at the last seen place
	CatchRadius = 3.5,         -- studs, while the player is visible
	ChaseSpeedMultiplier = 1.15,
	HideWitnessWindow = 1.5,   -- seconds: seen this recently when the player entered a hiding spot
	DoorOpenRadius = 6,
	DoorCloseAfter = 3,
	RepathInterval = 0.4,
	ArriveRadius = 1.3,        -- horizontal distance that counts as reaching a waypoint (large values cut corners into stair walls)
	ArriveHeight = 1.8,        -- vertical tolerance for the same check
	StuckSeconds = 3,
	TickInterval = 0.1,
	AlertClearSeconds = 3,
}

-- No jumping: with jumps allowed the planner cuts across stair sides. The first stair riser (~0.95 stud) is just above
-- the navmesh step limit, so the house carries a PathfindingLink over it (see the "StairLinks" folder).
local AGENT = { AgentRadius = 1.6, AgentHeight = 6, AgentCanJump = false, WaypointSpacing = 4 }
-- Sight points follow the REAL body (head part, root part, a point just above the soles from the current HipHeight), so a
-- crouching player (lower HipHeight) is shorter for the family and can hide behind low cover (LowCover proxy boxes).
local function bodyPoints(character, root)
	local head = character:FindFirstChild("Head")
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	local points = { root.Position }
	if head then
		table.insert(points, head.Position)
	end
	if humanoid then
		table.insert(points, root.Position - Vector3.new(0, root.Size.Y / 2 + humanoid.HipHeight - 0.3, 0))
	end
	return points
end

local npcs = {}   -- every live NPC record
local houses = {} -- [house Model] = { npcs, rayParams, opaque, bounds, caughtSpawn, nextRefresh }
local alerts = {} -- [Player] = { value, clearAt }

FamilyNpcService.PlayerCaught = Instance.new("BindableEvent") -- fires (player, npcModel); the steal/respawn logic hooks it

local function now()
	return os.clock()
end

local function setAlert(player, value)
	local a = alerts[player]
	if not a then
		a = { value = "" }
		alerts[player] = a
	end
	if a.value ~= value then
		a.value = value
		player:SetAttribute("FamilyAlert", value)
	end
end

local function flat(v)
	return Vector3.new(v.X, 0, v.Z)
end

-- ------------------------------------------------------------------------------------------------------------
-- line of sight
-- ------------------------------------------------------------------------------------------------------------
local function refreshOpaque(h)
	local list = { h.collision }
	local cover = h.house:FindFirstChild("LowCover")
	if cover then
		table.insert(list, cover) -- low furniture proxies (sofa, armchairs, bed, kitchen island): block sight only below their top
	end
	for _, model in ipairs(CollectionService:GetTagged("HouseDoor")) do
		if model:IsDescendantOf(h.house) then
			for _, c in ipairs(model:GetChildren()) do
				if c:IsA("BasePart") and string.sub(c.Name, 1, 4) == "Leaf" then
					table.insert(list, c)
				end
			end
		end
	end
	for _, model in ipairs(CollectionService:GetTagged("HideSpot")) do
		if model:IsDescendantOf(h.house) then
			for _, c in ipairs(model:GetChildren()) do
				if c:IsA("BasePart") and string.sub(c.Name, 1, 4) == "Leaf" then
					table.insert(list, c)
				end
			end
		end
	end
	h.rayParams.FilterDescendantsInstances = list
end

local function playerRoot(player)
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	local hum = character and character:FindFirstChildOfClass("Humanoid")
	if root and hum and hum.Health > 0 then
		return root
	end
	return nil
end

-- Returns true when the NPC can see the player's BODY (items are never considered: only the character's own points).
local function canSee(npc, player)
	local root = playerRoot(player)
	if not root or player:GetAttribute("IsHiding") == true then
		return false
	end
	local eye = npc.head.Position
	local delta = root.Position - eye
	if delta.Magnitude > CONFIG.ViewRange then
		return false
	end
	local fwd = flat(npc.root.CFrame.LookVector)
	local dir = flat(delta)
	if dir.Magnitude > 0.5 and fwd.Magnitude > 0.01 then
		if fwd.Unit:Dot(dir.Unit) < math.cos(math.rad(CONFIG.ViewFovDegrees / 2)) then
			return false
		end
	end
	local h = npc.h
	for _, target in ipairs(bodyPoints(player.Character, root)) do
		local hit = workspace:Raycast(eye, target - eye, h.rayParams)
		if not hit then
			return true
		end
	end
	return false
end

local function insideLot(h, position)
	if not h.bounds then
		return true
	end
	local p = h.bounds.CFrame:PointToObjectSpace(position)
	local s = h.bounds.Size / 2
	return math.abs(p.X) <= s.X and math.abs(p.Z) <= s.Z
end

-- ------------------------------------------------------------------------------------------------------------
-- movement
-- ------------------------------------------------------------------------------------------------------------
local function goTo(npc, target)
	-- compute a path to `target` (feet level position) and remember its waypoints
	local path = PathfindingService:CreatePath(AGENT)
	local ok = pcall(function()
		path:ComputeAsync(npc.root.Position, target + Vector3.new(0, npc.feet, 0))
	end)
	npc.goal = target
	npc.waypoints, npc.wpIndex = {}, 1
	npc.lastRepath = now()
	npc.stuckAt, npc.stuckPos = now(), npc.root.Position
	local standing = target + Vector3.new(0, npc.feet, 0)
	if (flat(standing) - flat(npc.root.Position)).Magnitude < CONFIG.ArriveRadius and math.abs(standing.Y - npc.root.Position.Y) < 3.5 then
		npc.waypoints, npc.wpIndex = {}, 1 -- already there
		npc.pathFailures = 0
		return true
	end
	if ok and path.Status == Enum.PathStatus.Success then
		npc.waypoints = path:GetWaypoints()
		npc.wpIndex = 2 -- the first waypoint is the start
		npc.pathFailures = 0
		return true
	end
	-- no path: never walk a straight line through walls or furniture; stand still and retry shortly
	npc.waypoints = nil
	npc.pathFailures = (npc.pathFailures or 0) + 1
	npc.retryAt = now() + 1
	npc.model:SetAttribute("FamilyPathFailure", ("%s from (%.1f,%.1f,%.1f) to (%.1f,%.1f,%.1f) ok=%s"):format(
		tostring(path.Status), npc.root.Position.X, npc.root.Position.Y, npc.root.Position.Z, standing.X, standing.Y, standing.Z, tostring(ok)))
	return false
end

local function followPath(npc)
	local wps = npc.waypoints
	if not wps or npc.wpIndex > #wps then
		return true -- arrived
	end
	local wp = wps[npc.wpIndex]
	local pos = npc.root.Position
	if (flat(wp.Position) - flat(pos)).Magnitude < CONFIG.ArriveRadius and math.abs(wp.Position.Y + npc.feet - pos.Y) < CONFIG.ArriveHeight + 1.0 then
		npc.wpIndex += 1
		return npc.wpIndex > #wps
	end
	if wp.Action == Enum.PathWaypointAction.Jump then
		npc.hum.Jump = true
	end
	npc.hum:MoveTo(wp.Position)
	return false
end

local function stopMoving(npc)
	npc.hum:MoveTo(npc.root.Position)
	npc.waypoints = nil
end

local function setSpeed(npc, multiplier)
	npc.hum.WalkSpeed = npc.baseSpeed * multiplier
end

local function openDoors(npc)
	HouseInteractionService.OpenDoorsNear(npc.root.Position, CONFIG.DoorOpenRadius, CONFIG.DoorCloseAfter)
end

-- ------------------------------------------------------------------------------------------------------------
-- state machine
-- ------------------------------------------------------------------------------------------------------------
local function setState(npc, state)
	if npc.state == state then
		return
	end
	npc.state = state
	npc.stateAt = now()
	npc.model:SetAttribute("FamilyState", state)
	if state ~= "Patrol" then
		npc.model:SetAttribute("FamilyActivity", nil)
	end
end

local function goPatrol(npc)
	setState(npc, "Patrol")
	setSpeed(npc, 1)
	npc.target = nil
	npc.knownHideSpot = nil
	npc.pauseUntil = nil
	goTo(npc, npc.route[npc.routeIndex].Position)
end

local function catchPlayer(npc, player)
	local h = npc.h
	HouseInteractionService.ReleasePlayer(player)
	setAlert(player, "")
	local root = playerRoot(player)
	if root and h.caughtSpawn then
		root.CFrame = h.caughtSpawn.CFrame + Vector3.new(0, 3, 0)
	end
	for _, other in ipairs(h.npcs) do
		if other.target == player or other.state == "Chase" or other.state == "Search" then
			goPatrol(other)
		end
	end
	FamilyNpcService.PlayerCaught:Fire(player, npc.model)
end

local function witnessHiding(player)
	local spotId = player:GetAttribute("HidingSpot")
	if not spotId or spotId == "" then
		return
	end
	local spot
	for _, model in ipairs(CollectionService:GetTagged("HideSpot")) do
		if model:GetAttribute("SpotId") == spotId then
			spot = model
		end
	end
	if not spot then
		return
	end
	for _, npc in ipairs(npcs) do
		if npc.state == "Chase" and npc.target == player and now() - npc.lastSeenTime <= CONFIG.HideWitnessWindow then
			npc.knownHideSpot = spot
		end
	end
end

local function nearestVisiblePlayer(npc)
	for _, player in ipairs(Players:GetPlayers()) do
		local root = playerRoot(player)
		if root and insideLot(npc.h, root.Position) and canSee(npc, player) then
			return player, root
		end
	end
	return nil
end

local function tick(npc)
	local h = npc.h
	local t = now()
	if npc.model.Parent == nil or npc.hum.Health <= 0 then
		return
	end
	-- debug / UI hooks: current waypoint progress is visible as a model attribute
	npc.model:SetAttribute("FamilyWaypoint", string.format("%d/%d", npc.wpIndex or 0, npc.waypoints and #npc.waypoints or 0))

	-- the chase ends the moment the target leaves the lot
	if npc.target then
		local root = playerRoot(npc.target)
		if not root or not insideLot(h, root.Position) then
			setAlert(npc.target, "Clear")
			alerts[npc.target].clearAt = t + CONFIG.AlertClearSeconds
			goPatrol(npc)
		end
	end

	local seen, seenRoot = nearestVisiblePlayer(npc)
	if seen and npc.state ~= "Chase" then
		setState(npc, "Chase")
		npc.target = seen
		npc.knownHideSpot = nil
		setSpeed(npc, CONFIG.ChaseSpeedMultiplier)
		npc.lastSeenPos, npc.lastSeenTime = seenRoot.Position, t
		setAlert(seen, "Spotted")
		goTo(npc, seenRoot.Position - Vector3.new(0, npc.feet, 0))
	end

	if npc.state == "Patrol" then
		if npc.pauseUntil then
			if t >= npc.pauseUntil then
				npc.pauseUntil = nil
				npc.model:SetAttribute("FamilyActivity", nil)
				npc.routeIndex = npc.routeIndex % #npc.route + 1
				goTo(npc, npc.route[npc.routeIndex].Position)
			end
			return
		end
		openDoors(npc)
		if npc.waypoints == nil then
			if t < (npc.retryAt or 0) then
				return
			end
			if (npc.pathFailures or 0) >= 3 then
				-- this route point is unreachable from here: skip it instead of freezing (fix the point in the house data)
				warn(("FamilyNpcService: %s cannot reach route point %s, skipping"):format(npc.role, npc.route[npc.routeIndex].Name))
				npc.pathFailures = 0
				npc.routeIndex = npc.routeIndex % #npc.route + 1
			end
			goTo(npc, npc.route[npc.routeIndex].Position)
			return
		end
		if followPath(npc) then
			local point = npc.route[npc.routeIndex]
			stopMoving(npc)
			local pause = point:GetAttribute("Pause") or 0
			if pause > 0 then
				npc.pauseUntil = t + pause
				npc.model:SetAttribute("FamilyActivity", point:GetAttribute("Activity"))
			else
				npc.routeIndex = npc.routeIndex % #npc.route + 1
				goTo(npc, npc.route[npc.routeIndex].Position)
			end
		elseif t - npc.stuckAt > CONFIG.StuckSeconds then
			if (npc.root.Position - npc.stuckPos).Magnitude < 0.6 then
				goTo(npc, npc.route[npc.routeIndex].Position)
			end
			npc.stuckAt, npc.stuckPos = t, npc.root.Position
		end
	elseif npc.state == "Chase" then
		local player = npc.target
		local root = player and playerRoot(player)
		if not root then
			goPatrol(npc)
			return
		end
		openDoors(npc)
		if seen == player then
			npc.lastSeenPos, npc.lastSeenTime = root.Position, t
			if (root.Position - npc.root.Position).Magnitude <= CONFIG.CatchRadius then
				catchPlayer(npc, player)
				return
			end
		elseif t - npc.lastSeenTime > CONFIG.LoseSightSeconds then
			setState(npc, "Search")
			setAlert(player, "Searching")
			if npc.knownHideSpot then
				goTo(npc, npc.knownHideSpot.EnterPart.Position - Vector3.new(0, npc.feet + 2, 0))
			else
				goTo(npc, npc.lastSeenPos - Vector3.new(0, npc.feet, 0))
			end
			return
		end
		if t - npc.lastRepath > CONFIG.RepathInterval then
			goTo(npc, (seen == player and root.Position or npc.lastSeenPos) - Vector3.new(0, npc.feet, 0))
		end
		followPath(npc)
	elseif npc.state == "Search" then
		local player = npc.target
		openDoors(npc)
		local arrived = followPath(npc)
		if arrived then
			stopMoving(npc)
			if npc.knownHideSpot then
				-- they saw the player enter this cupboard: open it
				local spot = npc.knownHideSpot
				HouseInteractionService.SetDoorOpen(spot, true)
				npc.knownHideSpot = nil
				if player and player:GetAttribute("HidingSpot") == spot:GetAttribute("SpotId") then
					catchPlayer(npc, player)
					return
				end
				npc.searchStart = t
			end
			npc.searchStart = npc.searchStart or t
			-- look around the place
			npc.root.CFrame = npc.root.CFrame * CFrame.Angles(0, CONFIG.TickInterval * 1.4, 0)
			if t - npc.searchStart > CONFIG.SearchSeconds then
				if player then
					setAlert(player, "Clear")
					alerts[player].clearAt = t + CONFIG.AlertClearSeconds
				end
				npc.searchStart = nil
				goPatrol(npc)
			end
		else
			npc.searchStart = nil
		end
	end
end

-- ------------------------------------------------------------------------------------------------------------
-- spawning
-- ------------------------------------------------------------------------------------------------------------
local function routeFor(folder, role)
	local list = {}
	for _, child in ipairs(folder:GetChildren()) do
		if child:IsA("BasePart") and string.match(child.Name, "^" .. role .. "_%d+$") then
			table.insert(list, child)
		end
	end
	table.sort(list, function(a, b)
		return a.Name < b.Name
	end)
	return list
end

local function spawnNpc(h, role, template)
	local route = routeFor(h.routes, role)
	if #route == 0 then
		return
	end
	local model = template:Clone()
	model.Name = "Family_" .. role
	local feet = model:GetAttribute("FeetOffset") or 3
	local start = route[1].Position
	model:PivotTo(CFrame.new(start + Vector3.new(0, feet + 0.1, 0)))
	model.Parent = h.folder
	local root = model:WaitForChild("HumanoidRootPart")
	local hum = model:WaitForChild("Humanoid")
	root:SetNetworkOwner(nil)
	local npc = {
		h = h, model = model, root = root, hum = hum, head = model:WaitForChild("Head"), role = role, route = route, routeIndex = 1,
		feet = feet, baseSpeed = hum.WalkSpeed, state = "Patrol", stateAt = now(), lastSeenTime = 0, lastRepath = 0, stuckAt = now(), stuckPos = root.Position,
	}
	CollectionService:AddTag(model, "FamilyNPC")
	model:SetAttribute("FamilyState", "Patrol")
	table.insert(h.npcs, npc)
	table.insert(npcs, npc)
	model.Destroying:Connect(function()
		for i, n in ipairs(npcs) do
			if n == npc then
				table.remove(npcs, i)
				break
			end
		end
	end)
	goTo(npc, route[1].Position)
end

local function setupHouse(house)
	if houses[house] then
		return
	end
	local routes = house:FindFirstChild("FamilyRoutes")
	local templates = ServerStorage:FindFirstChild("FamilyNpcModels")
	if not (routes and templates) then
		warn("FamilyNpcService: house without FamilyRoutes or ServerStorage.FamilyNpcModels missing")
		return
	end
	local collision = house:FindFirstChild("RDH_Collision") or house
	local folder = Instance.new("Folder")
	folder.Name = "FamilyNpcs"
	folder.Parent = house
	local h = {
		house = house, routes = routes, folder = folder, collision = collision, npcs = {}, nextRefresh = 0,
		bounds = house:FindFirstChild("FamilyLotBounds"), caughtSpawn = house:FindFirstChild("CaughtSpawn"),
		rayParams = RaycastParams.new(),
	}
	h.rayParams.FilterType = Enum.RaycastFilterType.Include
	houses[house] = h
	refreshOpaque(h)
	for _, role in ipairs({ "Wife", "Son" }) do
		local template = templates:FindFirstChild(role)
		if template then
			spawnNpc(h, role, template)
		end
	end
end

local function whenInWorkspace(house, fn)
	if house:IsDescendantOf(workspace) then
		fn(house)
		return
	end
	local conn
	conn = house.AncestryChanged:Connect(function()
		if house:IsDescendantOf(workspace) then
			conn:Disconnect()
			fn(house)
		end
	end)
end

function FamilyNpcService.Initialize()
	for _, house in ipairs(CollectionService:GetTagged("FamilyHouse")) do
		whenInWorkspace(house, setupHouse)
	end
	CollectionService:GetInstanceAddedSignal("FamilyHouse"):Connect(function(house)
		whenInWorkspace(house, setupHouse)
	end)

	local function watch(player)
		player:GetAttributeChangedSignal("HidingSpot"):Connect(function()
			witnessHiding(player)
		end)
	end
	for _, player in ipairs(Players:GetPlayers()) do
		watch(player)
	end
	Players.PlayerAdded:Connect(watch)
	Players.PlayerRemoving:Connect(function(player)
		alerts[player] = nil
		for _, npc in ipairs(npcs) do
			if npc.target == player then
				goPatrol(npc)
			end
		end
	end)

	local acc = 0
	RunService.Heartbeat:Connect(function(dt)
		acc += dt
		if acc < CONFIG.TickInterval then
			return
		end
		acc = 0
		local t = now()
		for _, h in pairs(houses) do
			if t >= h.nextRefresh then
				h.nextRefresh = t + 1
				refreshOpaque(h)
			end
		end
		for _, npc in ipairs(npcs) do
			local ok, err = pcall(tick, npc)
			if not ok then
				warn("FamilyNpcService tick error: " .. tostring(err))
			end
		end
		for player, a in pairs(alerts) do
			if a.clearAt and t >= a.clearAt and a.value == "Clear" then
				a.clearAt = nil
				setAlert(player, "")
			end
		end
	end)
end

-- True while any family member is chasing or searching for this player (md: delivery stays blocked until the chase ends).
function FamilyNpcService.IsPursued(player)
	for _, npc in ipairs(npcs) do
		if npc.target == player and (npc.state == "Chase" or npc.state == "Search") then
			return true
		end
	end
	return false
end

-- test / tuning access
FamilyNpcService.Config = CONFIG
FamilyNpcService._setupHouse = setupHouse
FamilyNpcService._npcs = npcs

return FamilyNpcService
