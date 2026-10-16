-- Edit-mode camera tour for the real Studio review frames (one view every 4 s; screenshots are taken from outside).
-- Logical (X,D,H) -> Roblox (-X, H, D); the model faces -Z. Run in the command bar.
local cam = workspace.CurrentCamera
cam.FieldOfView = 30
local V = Vector3.new
local views = {
	{ "01_matching34", V(7, 7, -15), V(-0.4, 3.5, -0.1) },
	{ "02_front", V(-0.5, 3.7, -24), V(-0.5, 3.7, 0) },
	{ "03_back", V(-0.5, 3.7, 24), V(-0.5, 3.7, 0) },
	{ "04_left_profile_rod_side", V(-24, 3.7, 0), V(0, 3.7, 0) },
	{ "05_right_profile", V(24, 3.7, 0), V(0, 3.7, 0) },
	{ "06_back34", V(14, 7, 16), V(-0.5, 3.5, 0) },
	{ "07_face_front", V(0, 5.3, -8), V(0, 5.2, 0) },
	{ "07b_face_34", V(3.8, 5.8, -6.5), V(0, 5.2, 0) },
	{ "08_hat_top", V(0, 13, -3), V(0, 6, 0) },
	{ "08b_hat_back_side", V(6, 6.4, 6), V(0, 5.9, 0) },
	{ "09_vest_front", V(0, 3.4, -9), V(0, 3.4, 0) },
	{ "09b_vest_back", V(0, 3.4, 9), V(0, 3.4, 0) },
	{ "10_left_arm_side", V(-8, 3.4, 0), V(-1.9, 3.3, 0) },
	{ "11_grip_front", V(-2.24, 3.5, -4), V(-2.24, 3.5, -0.65) },
	{ "11b_grip_side", V(-6, 3.5, -0.65), V(-2.24, 3.5, -0.65) },
	{ "11c_grip_back", V(-2.24, 3.5, 3), V(-2.24, 3.5, -0.65) },
	{ "12_rod_full_front", V(-2.5, 3.7, -19), V(-2.5, 3.7, -0.65) },
	{ "13_reel_front", V(-2.95, 2.84, -4), V(-2.95, 2.84, -0.65) },
	{ "14_float", V(-3.03, 5.7, -4), V(-3.03, 5.7, -0.65) },
	{ "15_bucket_front", V(-3, 0.9, -5), V(-3, 0.6, 0.09) },
	{ "15b_bucket_top", V(-3, 6, -1), V(-3, 0.6, 0.09) },
	{ "16_boots_cargo", V(4, 1.5, -6), V(0, 1.0, 0) },
}
task.spawn(function()
	for _, v in ipairs(views) do
		cam.CFrame = CFrame.lookAt(v[2], v[3])
		cam.Focus = CFrame.new(v[3])
		print("VIEW", v[1])
		task.wait(4)
	end
	print("TOUR DONE")
end)
