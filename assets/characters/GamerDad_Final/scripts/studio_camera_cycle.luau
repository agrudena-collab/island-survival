--!nocheck
-- Cycles the Studio edit camera through fixed views (5 s each) so that screenshots can be taken in a batch. Run in the command bar (ctrl+Return).
-- Roblox model space: the character faces -Z, its anatomical right (the can) is +X.
local views = {
	{ "01_front", Vector3.new(0, 3.9, -26), Vector3.new(0, 3.2, 0), 25 },
	{ "02_front_q34", Vector3.new(15, 6.5, -21), Vector3.new(0, 3.2, 0), 25 },
	{ "03_profile_right", Vector3.new(26, 3.9, -0.5), Vector3.new(0, 3.2, 0), 25 },
	{ "04_back", Vector3.new(0, 3.9, 26), Vector3.new(0, 3.2, 0), 25 },
	{ "05_rear_q34", Vector3.new(-16, 6.5, 22), Vector3.new(0, 3.2, 0), 25 },
	{ "06_profile_left", Vector3.new(-26, 3.9, -0.5), Vector3.new(0, 3.2, 0), 25 },
	{ "07_face", Vector3.new(0, 5.4, -13), Vector3.new(0, 5.2, 0), 18 },
	{ "08_beard_profile", Vector3.new(13, 5.0, -3), Vector3.new(0, 4.9, -0.6), 18 },
	{ "09_grip", Vector3.new(-3, 4.5, -11), Vector3.new(2.1, 3.7, -1.0), 20 },
	{ "10_right_elbow", Vector3.new(11, 4.5, 6), Vector3.new(2.0, 3.5, -0.3), 20 },
}
local cam = workspace.CurrentCamera
cam.CameraType = Enum.CameraType.Scriptable
for _, v in ipairs(views) do
	cam.FieldOfView = v[4]
	cam.CFrame = CFrame.lookAt(v[2], v[3])
	print("VIEW", v[1])
	task.wait(5)
end
print("VIEWS_DONE")
