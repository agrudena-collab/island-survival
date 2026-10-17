--!nocheck
-- F5 (Play with a player) QA of the UNANCHORED model: carry QA (welded to the player, 30 s with turns and jumps) and placement on a known plane.
-- This is a QA weld of the model to the player, NOT an implemented theft mechanic.
-- Install: paste this file into the command bar (creates ServerScriptService.GD_QA_F5 and moves the SpawnLocation away from the model), then press F5, wait ~50 s, copy the Output, Stop.
local SRC = [==[
local HS = game:GetService("HttpService")
local Players = game:GetService("Players")
local RS = game:GetService("RunService")
local function emit(tag, t)
	print("GDF5|" .. tag .. "|" .. HS:JSONEncode(t))
end
local template = workspace:WaitForChild("GamerDad_R15")
local function run(plr)
	local char = plr.Character or plr.CharacterAdded:Wait()
	local hum = char:WaitForChild("Humanoid")
	local phrp = char:WaitForChild("HumanoidRootPart")
	task.wait(3)
	local dad = template:Clone()
	dad.Name = "GamerDad_QA_F5"
	dad.Parent = workspace
	local hold = {}
	for _, v in ipairs(dad.HoldCanPose:GetChildren()) do
		hold[(string.gsub(v.Name, "_PartCFrame$", ""))] = v.Value
	end
	dad:PivotTo(dad:GetPivot() + Vector3.new(0, 0, 0))
	local dh = dad.HumanoidRootPart
	local anch = 0
	for _, p in ipairs(dad:GetDescendants()) do
		if p:IsA("BasePart") and p.Anchored then
			anch += 1
		end
	end
	emit("setup", { player = plr.Name, anchoredPartsInDad = anch, playerHrpY = phrp.Position.Y, dadHipHeight = dad.Humanoid.HipHeight })
	-- 1. free standing: relative frames must stay put while the dad stands by itself
	local function worstRel()
		local wp, wr, name = 0, 0, ""
		for n, c in pairs(hold) do
			local part = dad:FindFirstChild(n)
			if part and part:IsA("BasePart") then
				local rel = dh.CFrame:ToObjectSpace(part.CFrame)
				local dp = (rel.Position - c.Position).Magnitude
				local _, ang = (rel:Inverse() * c):ToAxisAngle()
				if dp > wp then
					wp, name = dp, n
				end
				wr = math.max(wr, math.abs(ang))
			end
		end
		return wp, wr, name
	end
	task.wait(2)
	local w0, r0, n0 = worstRel()
	local lowest = 1e9
	for _, n in ipairs({ "RightFoot", "LeftFoot" }) do
		local f = dad[n]
		lowest = math.min(lowest, f.Position.Y - f.Size.Y / 2)
	end
	emit("free_standing", { worstPosDev = w0, worstRotDev = r0, part = n0, lowestSoleY = lowest, hrpY = dh.Position.Y, state = tostring(dad.Humanoid:GetState()), floorMaterial = tostring(dad.Humanoid.FloorMaterial) })
	-- 2. carry QA: weld the dad's HumanoidRootPart to the player's (QA only), place it 5 studs behind
	dh.CFrame = phrp.CFrame * CFrame.new(0, 0, 5)
	local weld = Instance.new("WeldConstraint")
	weld.Name = "QA_CarryWeld"
	weld.Part0, weld.Part1 = phrp, dh
	weld.Parent = dh
	task.wait(1)
	local relRoot0 = phrp.CFrame:ToObjectSpace(dh.CFrame)
	local startPos = phrp.Position
	local maxRoot, maxPos, maxRot, samples, worstName = 0, 0, 0, 0, ""
	local conn = RS.Heartbeat:Connect(function()
		samples += 1
		local rr = phrp.CFrame:ToObjectSpace(dh.CFrame)
		maxRoot = math.max(maxRoot, (rr.Position - relRoot0.Position).Magnitude)
		local wp, wr, nm = worstRel()
		if wp > maxPos then
			maxPos, worstName = wp, nm
		end
		maxRot = math.max(maxRot, wr)
	end)
	-- the player's client controller overrides Humanoid:Move on the server, so the motion is driven explicitly: yaw jumps (turns) of the player root + forward velocity + jumps
	local script_ = { { 90, 4.5, true }, { -90, 4.5, true }, { 180, 4.5, true }, { 90, 4.5, true }, { -135, 4.0, true }, { 135, 4.0, true }, { 180, 4.0, true }, { 0, 2.0, false } }
	local t0 = os.clock()
	local yawTotal, lastLook = 0, phrp.CFrame.LookVector
	local jumps, turnsDeg = 0, 0
	for _, step in ipairs(script_) do
		if step[1] ~= 0 then
			phrp.CFrame = phrp.CFrame * CFrame.Angles(0, math.rad(step[1]), 0)
			turnsDeg += math.abs(step[1])
		end
		if step[3] then
			hum.Jump = true
			jumps += 1
		end
		local tEnd = os.clock() + step[2]
		while os.clock() < tEnd do
			task.wait(0.1)
			local lv = phrp.CFrame.LookVector
			yawTotal += math.abs(math.atan2(lastLook:Cross(lv).Y, lastLook:Dot(lv)))
			lastLook = lv
			local v = phrp.AssemblyLinearVelocity
			local f = Vector3.new(lv.X, 0, lv.Z).Unit * 14
			phrp.AssemblyLinearVelocity = Vector3.new(f.X, v.Y, f.Z)
			if step[3] and hum:GetState() == Enum.HumanoidStateType.Landed then
				hum.Jump = true
				jumps += 1
			end
		end
	end
	hum:Move(Vector3.zero, false)
	local dur = os.clock() - t0
	task.wait(1)
	conn:Disconnect()
	emit("carry", { seconds = dur, samples = samples, jumps = jumps, totalYawRad = yawTotal, commandedTurnsDeg = turnsDeg, travelledStuds = (phrp.Position - startPos).Magnitude, maxRootRelShift = maxRoot, maxPartRelPosDev = maxPos, maxPartRelRotDev = maxRot, worstPart = worstName,
		canRelHand = { dad.RightHand.CFrame:ToObjectSpace(dad.EnergyCan.CFrame).Position.X, dad.RightHand.CFrame:ToObjectSpace(dad.EnergyCan.CFrame).Position.Y, dad.RightHand.CFrame:ToObjectSpace(dad.EnergyCan.CFrame).Position.Z } })
	-- 3. release and place on the known plane (Baseplate top, Y = 0): move the dad so that its lowest sole point is on Y = 0
	weld:Destroy()
	task.wait(1.5)
	local function lowestSole()
		local y = 1e9
		for _, n in ipairs({ "RightFoot", "LeftFoot" }) do
			local f = dad[n]
			y = math.min(y, f.Position.Y - f.Size.Y / 2)
		end
		return y
	end
	local low1 = lowestSole()
	dad:PivotTo(dad:GetPivot() + Vector3.new(15, -low1 + 0.0, 0))
	task.wait(2)
	local low2 = lowestSole()
	local w2, r2, n2 = worstRel()
	emit("placed", { lowestBeforePlacement = low1, lowestAfterPlacementAndSettle = low2, error = math.abs(low2), worstPosDev = w2, worstRotDev = r2, part = n2, state = tostring(dad.Humanoid:GetState()) })
	local a2 = 0
	for _, p in ipairs(dad:GetDescendants()) do
		if p:IsA("BasePart") and p.Anchored then
			a2 += 1
		end
	end
	emit("end", { anchoredParts = a2 })
	print("GDF5_DONE")
end
Players.PlayerAdded:Connect(function(p)
	task.spawn(run, p)
end)
for _, p in ipairs(Players:GetPlayers()) do
	task.spawn(run, p)
end
]==]
local old = game.ServerScriptService:FindFirstChild("GD_QA_F5")
if old then
	old:Destroy()
end
local s = Instance.new("Script")
s.Name = "GD_QA_F5"
s.Source = SRC
s.Parent = game.ServerScriptService
local sp = game.ServerStorage:FindFirstChildOfClass("SpawnLocation") or workspace:FindFirstChildOfClass("SpawnLocation")
if sp then
	sp.Parent = workspace
	sp.Position = Vector3.new(40, 0.5, 40)
end
print("GD_QA_F5 installed")
