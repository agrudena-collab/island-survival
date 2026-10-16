-- CLIENT context command bar during the carry test: walk, turn, jump (the server welds the model to this player).
local c = game.Players.LocalPlayer.Character
local h, r = c.Humanoid, c.HumanoidRootPart
task.spawn(function()
	local p = r.Position
	local function go(v)
		h:MoveTo(p + v)
		local t = os.clock()
		while os.clock() - t < 4 and (r.Position - (p + v)).Magnitude > 3 do
			task.wait()
		end
		p = r.Position
	end
	task.wait(1)
	go(Vector3.new(0, 0, -14))
	h.Jump = true
	task.wait(1)
	go(Vector3.new(14, 0, 0))
	h.Jump = true
	task.wait(1)
	go(Vector3.new(0, 0, 14))
	go(Vector3.new(-14, 0, 0))
	h.Jump = true
	print("client path done")
end)
