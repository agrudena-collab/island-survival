-- Builds the complete lightweight test facility from standard Roblox Parts.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Config = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"))

local signals = ServerStorage:WaitForChild("EscapeFacilitySignals")
local roundReset = signals:WaitForChild("RoundReset")
local mapResetComplete = signals:WaitForChild("MapResetComplete")

local oldMap = workspace:FindFirstChild("EscapeFacilityMap")
if oldMap then
	oldMap:Destroy()
end

local map = Instance.new("Folder")
map.Name = "EscapeFacilityMap"
map.Parent = workspace

local function createPart(parent, name, size, position, color, material)
	local part = Instance.new("Part")
	part.Name = name
	part.Anchored = true
	part.Size = size
	part.Position = position
	part.Color = color
	part.Material = material or Enum.Material.SmoothPlastic
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.Parent = parent
	return part
end

local rooms = Instance.new("Folder")
rooms.Name = "Rooms"
rooms.Parent = map

local function createRoom(name, size, position, color)
	local room = Instance.new("Folder")
	room.Name = name
	room.Parent = rooms

	local floor = createPart(room, "Floor", size, position, color, Enum.Material.Metal)
	floor.CanCollide = false
	return room
end

local foundation = createPart(
	map,
	"FacilityFoundation",
	Vector3.new(140, 2, 80),
	Vector3.new(0, 0, 0),
	Color3.fromRGB(55, 60, 70),
	Enum.Material.Concrete
)

createRoom("StartRoom", Vector3.new(28, 0.2, 30), Vector3.new(-52, 1.1, 0), Color3.fromRGB(45, 70, 95))
createRoom("Corridor", Vector3.new(34, 0.2, 16), Vector3.new(-28, 1.1, 0), Color3.fromRGB(65, 65, 72))
createRoom("RoomA", Vector3.new(34, 0.2, 28), Vector3.new(-6, 1.1, -21), Color3.fromRGB(65, 80, 92))
createRoom("RoomB", Vector3.new(34, 0.2, 28), Vector3.new(-6, 1.1, 21), Color3.fromRGB(65, 80, 92))
createRoom("CentralRoom", Vector3.new(34, 0.2, 50), Vector3.new(27, 1.1, 0), Color3.fromRGB(72, 72, 86))
createRoom("ExitArea", Vector3.new(24, 0.2, 24), Vector3.new(57, 1.1, 0), Color3.fromRGB(55, 90, 65))

local walls = Instance.new("Folder")
walls.Name = "Walls"
walls.Parent = map

local wallColor = Color3.fromRGB(115, 120, 130)
createPart(walls, "NorthWall", Vector3.new(140, 12, 2), Vector3.new(0, 7, -39), wallColor, Enum.Material.Metal)
createPart(walls, "SouthWall", Vector3.new(140, 12, 2), Vector3.new(0, 7, 39), wallColor, Enum.Material.Metal)
createPart(walls, "WestWall", Vector3.new(2, 12, 80), Vector3.new(-69, 7, 0), wallColor, Enum.Material.Metal)
createPart(walls, "EastWall", Vector3.new(2, 12, 80), Vector3.new(69, 7, 0), wallColor, Enum.Material.Metal)

-- These segments leave open passageways between the named parts of the facility.
createPart(walls, "StartDividerNorth", Vector3.new(2, 12, 32), Vector3.new(-36, 7, -23), wallColor, Enum.Material.Metal)
createPart(walls, "StartDividerSouth", Vector3.new(2, 12, 32), Vector3.new(-36, 7, 23), wallColor, Enum.Material.Metal)
createPart(walls, "ExitDividerNorth", Vector3.new(2, 12, 32), Vector3.new(45, 7, -24), wallColor, Enum.Material.Metal)
createPart(walls, "ExitDividerSouth", Vector3.new(2, 12, 32), Vector3.new(45, 7, 24), wallColor, Enum.Material.Metal)

local decorations = Instance.new("Folder")
decorations.Name = "Decorations"
decorations.Parent = map

for index, position in ipairs({
	Vector3.new(-48, 4, -12),
	Vector3.new(-48, 4, 12),
	Vector3.new(8, 4, -34),
	Vector3.new(8, 4, 34),
	Vector3.new(40, 4, -30),
	Vector3.new(40, 4, 30),
}) do
	local lightPost = createPart(
		decorations,
		"LightPost" .. index,
		Vector3.new(1, 6, 1),
		position,
		Color3.fromRGB(120, 225, 255),
		Enum.Material.Neon
	)
	lightPost.CanCollide = false

	local light = Instance.new("PointLight")
	light.Color = lightPost.Color
	light.Brightness = 1.5
	light.Range = 14
	light.Parent = lightPost
end

local spawn = Instance.new("SpawnLocation")
spawn.Name = "StartSpawn"
spawn.Anchored = true
spawn.Neutral = true
spawn.Size = Vector3.new(8, 1, 8)
spawn.Position = Config.START_POSITION
spawn.Color = Color3.fromRGB(70, 170, 255)
spawn.Material = Enum.Material.Neon
spawn.Parent = map

local checkpoints = Instance.new("Folder")
checkpoints.Name = "Checkpoints"
checkpoints.Parent = map

for checkpointId, position in pairs(Config.CHECKPOINTS) do
	local checkpoint = createPart(
		checkpoints,
		checkpointId,
		Vector3.new(7, 0.4, 7),
		position,
		Color3.fromRGB(70, 255, 160),
		Enum.Material.Neon
	)
	checkpoint.CanCollide = false
	checkpoint:SetAttribute("CheckpointId", checkpointId)
end

local interactive = Instance.new("Folder")
interactive.Name = "Interactive"
interactive.Parent = map

local cores = Instance.new("Folder")
cores.Name = "EnergyCores"
cores.Parent = interactive

local terminal = createPart(
	interactive,
	"CentralTerminal",
	Vector3.new(4, 6, 4),
	Config.TERMINAL_POSITION,
	Color3.fromRGB(255, 150, 55),
	Enum.Material.Metal
)

local terminalPrompt = Instance.new("ProximityPrompt")
terminalPrompt.Name = "TerminalPrompt"
terminalPrompt.ActionText = "Requires 3 Energy Cores"
terminalPrompt.ObjectText = "Central Terminal"
terminalPrompt.MaxActivationDistance = Config.PROMPT_DISTANCE
terminalPrompt.RequiresLineOfSight = false
terminalPrompt.Parent = terminal

local exitDoor = createPart(
	interactive,
	"ExitDoor",
	Vector3.new(2, 12, 14),
	Config.EXIT_DOOR_POSITION,
	Color3.fromRGB(190, 70, 70),
	Enum.Material.Metal
)

local exitTrigger = createPart(
	interactive,
	"ExitTrigger",
	Vector3.new(8, 10, 16),
	Config.EXIT_TRIGGER_POSITION,
	Color3.fromRGB(75, 255, 120),
	Enum.Material.ForceField
)
exitTrigger.Transparency = 0.8
exitTrigger.CanCollide = false

local robots = Instance.new("Folder")
robots.Name = "SecurityRobots"
robots.Parent = map

local function createRobot(name, position)
	local robot = Instance.new("Model")
	robot.Name = name
	robot.Parent = robots

	local root = createPart(robot, "HumanoidRootPart", Vector3.new(4, 4, 3), position, Color3.fromRGB(85, 90, 100), Enum.Material.Metal)
	root.CanCollide = false

	local head = createPart(robot, "Head", Vector3.new(3, 2, 3), position + Vector3.new(0, 3, 0), Color3.fromRGB(130, 135, 150), Enum.Material.Metal)
	head.CanCollide = false

	local eye = createPart(robot, "Scanner", Vector3.new(1, 0.6, 0.3), position + Vector3.new(0, 3, -1.6), Color3.fromRGB(255, 70, 70), Enum.Material.Neon)
	eye.CanCollide = false

	local humanoid = Instance.new("Humanoid")
	humanoid.Name = "Humanoid"
	humanoid.DisplayName = "Security Robot"
	humanoid.Parent = robot

	robot.PrimaryPart = root
	robot:SetAttribute("PatrolIndex", 1)
	robot:SetAttribute("PauseUntil", 0)
end

for robotName, robotPosition in pairs(Config.ROBOT_SPAWNS) do
	createRobot(robotName, robotPosition)
end

local function createCore(index, position)
	local core = createPart(
		cores,
		"EnergyCore" .. index,
		Vector3.new(3, 3, 3),
		position,
		Color3.fromRGB(75, 225, 255),
		Enum.Material.Neon
	)
	core.Shape = Enum.PartType.Ball
	core.CanCollide = false
	core:SetAttribute("Collected", false)

	local light = Instance.new("PointLight")
	light.Color = core.Color
	light.Brightness = 2
	light.Range = 12
	light.Parent = core

	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = "CorePrompt"
	prompt.ActionText = "Collect Energy Core"
	prompt.ObjectText = "Energy Core"
	prompt.MaxActivationDistance = Config.PROMPT_DISTANCE
	prompt.RequiresLineOfSight = false
	prompt.Parent = core
end

local closedDoorCFrame = CFrame.new(Config.EXIT_DOOR_POSITION)

local function resetDynamicObjects()
	cores:ClearAllChildren()
	for index, position in ipairs(Config.CORE_POSITIONS) do
		createCore(index, position)
	end

	terminal:SetAttribute("Activated", false)
	terminal.Color = Color3.fromRGB(255, 150, 55)
	terminalPrompt.Enabled = true
	terminalPrompt.ActionText = "Requires 3 Energy Cores"

	exitDoor.CFrame = closedDoorCFrame
	exitDoor.CanCollide = true
	exitDoor.Transparency = 0
	exitDoor.Color = Color3.fromRGB(190, 70, 70)
end

resetDynamicObjects()
mapResetComplete:Fire()

roundReset.Event:Connect(function()
	resetDynamicObjects()
	mapResetComplete:Fire()
end)
