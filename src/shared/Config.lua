local Config = {
	GAME_TITLE = "Escape Facility",
	TOTAL_CORES = 3,
	GAME_TIME = 300,
	PLAYER_MAX_HEALTH = 100,
	ROBOT_DAMAGE = 20,
	ROBOT_DETECTION_DISTANCE = 30,
	ROBOT_ATTACK_DISTANCE = 6,
	ROBOT_ATTACK_COOLDOWN = 1.5,
	ROBOT_POST_ATTACK_PAUSE = 1,
	ROBOT_SPEED = 8,
	ROBOT_NOTIFICATION_COOLDOWN = 4,
	PROMPT_DISTANCE = 10,
}

Config.CORE_POSITIONS = {
	Vector3.new(-8, 4, -22),
	Vector3.new(-6, 4, 22),
	Vector3.new(29, 4, -15),
}

Config.CHECKPOINTS = {
	Checkpoint1 = Vector3.new(-22, 2, 0),
	Checkpoint2 = Vector3.new(27, 2, 0),
}

Config.ROBOT_SPAWNS = {
	SecurityRobot1 = Vector3.new(-4, 4, -12),
	SecurityRobot2 = Vector3.new(31, 4, 14),
}

Config.ROBOT_PATROLS = {
	SecurityRobot1 = {
		Vector3.new(-18, 4, -24),
		Vector3.new(2, 4, -24),
		Vector3.new(-2, 4, -6),
	},
	SecurityRobot2 = {
		Vector3.new(18, 4, 16),
		Vector3.new(36, 4, 16),
		Vector3.new(32, 4, -10),
	},
}

Config.TERMINAL_POSITION = Vector3.new(28, 4, 0)
Config.EXIT_DOOR_POSITION = Vector3.new(45, 7, 0)
Config.EXIT_TRIGGER_POSITION = Vector3.new(57, 5, 0)
Config.START_POSITION = Vector3.new(-54, 3, 0)

return Config
