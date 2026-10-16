-- F5 CLIENT context command bar: scripted camera views of the spawned dad (DadPreview.GrillDad, x=30 in the preview row).
local cam = workspace.CurrentCamera
cam.CameraType = Enum.CameraType.Scriptable
cam.FieldOfView = 32
local V = Vector3.new
local views = {
	{ "front", V(29.7, 3.7, -26), V(29.7, 3.7, 0) },
	{ "back", V(29.7, 3.7, 26), V(29.7, 3.7, 0) },
	{ "three_quarter", V(40, 7.2, -17), V(29.7, 3.4, -0.1) },
	{ "hand_closeup", V(27.7, 3.5, -4.2), V(27.7, 3.5, -0.62) },
}
task.spawn(function()
	for _, v in ipairs(views) do
		cam.CFrame = CFrame.lookAt(v[2], v[3])
		print("F5VIEW", v[1])
		task.wait(4)
	end
	print("F5 VIEWS DONE")
end)
