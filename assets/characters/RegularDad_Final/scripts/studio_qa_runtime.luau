-- Studio QA for RegularDad_Redesign: run in Run mode (F8) from the command bar, with a ground part below the model.
-- Used on 2026-10-16; its output is shown in Studio_Review/screenshots/13_runtime_test_report.jpg
task.spawn(function()
	local ws = workspace
	local m = ws:WaitForChild("RegularDad_R15")
	local hum = m:FindFirstChildOfClass("Humanoid")
	local hrp = m:FindFirstChild("HumanoidRootPart")
	task.wait(2)
	local function lo()
		local y = 1e9
		for _, p in ipairs(m:GetChildren()) do
			if p:IsA("BasePart") and p.Name ~= "HumanoidRootPart" then
				y = math.min(y, p.Position.Y - p.Size.Y / 2)
			end
		end
		return y
	end
	print("T1 settled HRP", hrp.Position, "state", hum:GetState(), "floor", hum.FloorMaterial, "lowestY", lo())
	local function rel()
		return m.RightHand.CFrame:ToObjectSpace(m.Mug.CFrame).Position
	end
	local r0 = rel()
	local p0 = hrp.Position
	hum:MoveTo(Vector3.new(0, 3, -20))
	local t0 = os.clock()
	hum.MoveToFinished:Wait()
	print("T2 walk dist", (hrp.Position - p0).Magnitude, "time", os.clock() - t0, "state", hum:GetState(), "lowestY", lo())
	print("T3 mug rel hand before", r0, "after walk", rel())
	m.RightUpperArm.RightShoulder.Transform = CFrame.Angles(-1.2, 0, 0)
	task.wait(1)
	print("T4 shoulder raised: hand Y", m.RightHand.Position.Y, "mug rel", rel(), "mug worldY", m.Mug.Position.Y)
	m.RightUpperArm.RightShoulder.Transform = CFrame.new()
	m.LeftUpperLeg.LeftHip.Transform = CFrame.Angles(0.6, 0, 0)
	m.LeftLowerLeg.LeftKnee.Transform = CFrame.Angles(-1.0, 0, 0)
	task.wait(1)
	print("T5 hip/knee: LeftFoot Y", m.LeftFoot.Position.Y, "RightFoot Y", m.RightFoot.Position.Y)
	m.LeftUpperLeg.LeftHip.Transform = CFrame.new()
	m.LeftLowerLeg.LeftKnee.Transform = CFrame.new()
	hrp.CFrame = hrp.CFrame * CFrame.Angles(0, math.rad(90), 0)
	task.wait(1.5)
	print("T6 after yaw 90: mug rel", rel(), "weld", m.Mug.MugGrip.Part0.Name, "anchored", m.Mug.Anchored,
		"cancollide", m.Mug.CanCollide, "massless", m.Mug.Massless)
	local n, a = 0, 0
	for _, d in ipairs(m:GetDescendants()) do
		if d:IsA("LuaSourceContainer") then
			n += 1
		end
		if d:IsA("BasePart") and d.Anchored then
			a += 1
		end
	end
	print("T7 scripts", n, "anchoredParts", a)
end)
