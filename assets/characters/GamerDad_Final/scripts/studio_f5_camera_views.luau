-- F5 CLIENT-context command bar: scripted camera views of the spawned Gamer Dad (workspace.DadPreview.GamerDad, pivot (0, 3.38, 10), faces -Z).
local cam = workspace.CurrentCamera
cam.CameraType = Enum.CameraType.Scriptable
cam.FieldOfView = 32
local V = Vector3.new
-- client-side only: remove the other preview dads so none stands between the camera and Gamer Dad
for _, d in ipairs(workspace.DadPreview:GetChildren()) do
	if d.Name ~= "GamerDad" then
		d:Destroy()
	end
end
local views = {
	{ "front", V(0, 3.4, -16), V(0, 3.4, 10) },
	{ "back", V(0, 3.4, 36), V(0, 3.4, 10) },
	{ "side_right", V(26, 3.4, 10), V(0, 3.4, 10) },
	{ "three_quarter", V(10.5, 6.6, -1), V(0, 3.3, 9.9) },
	{ "hand_closeup", V(2.6, 4.2, 4.6), V(1.93, 3.8, 8.7) },
}
task.spawn(function()
	for _, v in ipairs(views) do
		cam.CFrame = CFrame.lookAt(v[2], v[3])
		print("F5VIEW", v[1])
		task.wait(5)
	end
	print("F5 VIEWS DONE")
end)
