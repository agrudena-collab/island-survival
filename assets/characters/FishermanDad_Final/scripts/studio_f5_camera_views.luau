-- F5 CLIENT context command bar: scripted camera views of the spawned dad (DadPreview.GardenerDad, x=20 in the preview row).
local cam = workspace.CurrentCamera
cam.CameraType = Enum.CameraType.Scriptable
cam.FieldOfView = 32
local V = Vector3.new
local views = {
	{ "front", V(19.5, 3.7, -26), V(19.5, 3.7, 0) },
	{ "back", V(19.5, 3.7, 26), V(19.5, 3.7, 0) },
	{ "three_quarter", V(30, 7.2, -17), V(19.6, 3.4, -0.1) },
	{ "grip_closeup", V(17.76, 3.5, -4.2), V(17.76, 3.5, -0.65) },
}
task.spawn(function()
	for _, v in ipairs(views) do
		cam.CFrame = CFrame.lookAt(v[2], v[3])
		print("F5VIEW", v[1])
		task.wait(4)
	end
	print("F5 VIEWS DONE")
end)
