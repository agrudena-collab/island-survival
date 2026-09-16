-- A small patrol-and-chase AI for the simple part-based security robots.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"))
local GameState = require(script.Parent:WaitForChild("GameState"))

local remotes = ReplicatedStorage:WaitForChild("EscapeFacilityRemotes")
local notificationEvent = remotes:WaitForChild("NotificationEvent")

local map = workspace:WaitForChild("EscapeFacilityMap")
local robots = map:WaitForChild("SecurityRobots")

local robotState = {}
local detectionTimes = {}

for _, robot in robots:GetChildren() do
	robotState[robot] = {
		nextAttackByPlayer = {},
	}
end

local function horizontalDistance(first, second)
	local difference = Vector3.new(first.X - second.X, 0, first.Z - second.Z)
	return difference.Magnitude, difference
end

local function findClosestPlayer(position)
	local closestPlayer
	local closestRoot
	local closestDistance = Config.ROBOT_DETECTION_DISTANCE

	for _, player in Players:GetPlayers() do
		if not GameState.IsPlayerFinished(player) then
			local character = player.Character
			local humanoid = character and character:FindFirstChildOfClass("Humanoid")
			local root = character and character:FindFirstChild("HumanoidRootPart")
			if humanoid and root and humanoid.Health > 0 then
				local distance = horizontalDistance(position, root.Position)
				if distance < closestDistance then
					closestPlayer = player
					closestRoot = root
					closestDistance = distance
				end
			end
		end
	end

	return closestPlayer, closestRoot, closestDistance
end

local function moveRobot(robot, targetPosition, deltaTime)
	local root = robot.PrimaryPart
	if not root then
		return
	end

	local distance, difference = horizontalDistance(root.Position, targetPosition)
	if distance < 0.05 then
		return
	end

	local step = math.min(Config.ROBOT_SPEED * deltaTime, distance)
	local newPosition = root.Position + difference.Unit * step
	robot:PivotTo(CFrame.lookAt(newPosition, newPosition + difference.Unit))
end

local function notifyDetection(player)
	local currentTime = os.clock()
	if currentTime - (detectionTimes[player] or 0) >= Config.ROBOT_NOTIFICATION_COOLDOWN then
		detectionTimes[player] = currentTime
		notificationEvent:FireClient(player, "Security Robot detected")
	end
end

local function patrol(robot, deltaTime)
	local patrolPoints = Config.ROBOT_PATROLS[robot.Name]
	local root = robot.PrimaryPart
	if not patrolPoints or not root then
		return
	end

	local index = robot:GetAttribute("PatrolIndex") or 1
	local target = patrolPoints[index]
	local distance = horizontalDistance(root.Position, target)
	if distance < 2 then
		index = index % #patrolPoints + 1
		robot:SetAttribute("PatrolIndex", index)
		target = patrolPoints[index]
	end

	moveRobot(robot, target, deltaTime)
end

RunService.Heartbeat:Connect(function(deltaTime)
	local currentTime = os.clock()

	for _, robot in robots:GetChildren() do
		local root = robot.PrimaryPart
		local state = robotState[robot]
		if root and state then
			if currentTime < (robot:GetAttribute("PauseUntil") or 0) then
				continue
			end

			local player, playerRoot, distance = findClosestPlayer(root.Position)
			if not player then
				patrol(robot, deltaTime)
				continue
			end

			notifyDetection(player)
			moveRobot(robot, playerRoot.Position, deltaTime)

			if distance <= Config.ROBOT_ATTACK_DISTANCE then
				local nextAttack = state.nextAttackByPlayer[player] or 0
				if currentTime >= nextAttack then
					local humanoid = player.Character and player.Character:FindFirstChildOfClass("Humanoid")
					if humanoid and humanoid.Health > 0 then
						humanoid:TakeDamage(Config.ROBOT_DAMAGE)
						state.nextAttackByPlayer[player] = currentTime + Config.ROBOT_ATTACK_COOLDOWN
						robot:SetAttribute("PauseUntil", currentTime + Config.ROBOT_POST_ATTACK_PAUSE)
					end
				end
			end
		end
	end
end)
