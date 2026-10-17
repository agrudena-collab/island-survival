--!nocheck
-- F5 (Play with a player) QA of the Gamer Dad SPAWNED by the production path DadModelBuilder.Build("GamerDad") -> PlaceAt.
-- Part 1: spawned-state checks. Part 2: isolated QA carry harness (weld to the player, >= 30 s of turns + jumps) - NOT a game mechanic, NOT part of the Final.
-- Part 3: release, production re-placement (DadModelBuilder.PlaceAt) and re-measurement.
-- Install: paste this file into the command bar (Edit mode, ctrl+Return) -> it creates ServerScriptService.GD_FINAL_QA; then press F5, wait ~60 s, copy the Output, Stop.
-- SPAWN_MODE = "preview": the dad is taken from workspace.DadPreview (temporary preview of the working tree); "builder": the script builds it itself with DadModelBuilder.
local SRC = [==[
local SPAWN_MODE = "__MODE__"
local HS = game:GetService("HttpService")
local RS = game:GetService("RunService")
local function emit(tag, t)
	print("GDFIN|" .. tag .. "|" .. HS:JSONEncode(t))
end
local Builder = require(game.ServerScriptService:WaitForChild("DadModelBuilder"))
-- QA-only ground (the Rojo place has no baseplate); top surface at Y = 0, never part of the Final
local floor = Instance.new("Part")
floor.Name = "QA_Floor"
floor.Anchored = true
floor.Size = Vector3.new(4000, 2, 4000)
floor.Position = Vector3.new(0, -1, 0)
floor.Parent = workspace
local m
if SPAWN_MODE == "preview" then
	m = workspace:WaitForChild("DadPreview"):WaitForChild("GamerDad")
else
	m = Builder.Build("GamerDad")
	m.Parent = workspace
	Builder.PlaceAt(m, CFrame.new(0, 0, 0))
end
task.wait(2)
local hrp, hum = m.HumanoidRootPart, m:FindFirstChildOfClass("Humanoid")
local expected = { HumanoidRootPart = true, Head = true, UpperTorso = true, LowerTorso = true, LeftUpperArm = true, LeftLowerArm = true, LeftHand = true, RightUpperArm = true, RightLowerArm = true, RightHand = true,
	LeftUpperLeg = true, LeftLowerLeg = true, LeftFoot = true, RightUpperLeg = true, RightLowerLeg = true, RightFoot = true, Headset = true, EnergyCan = true }
local function counts()
	local parts, anch, extra, lo = 0, 0, {}, math.huge
	for _, c in ipairs(m:GetChildren()) do
		if c:IsA("BasePart") then
			parts += 1
			if c.Anchored then
				anch += 1
			end
			if not expected[c.Name] then
				table.insert(extra, c.Name)
			end
			if c.Name ~= "HumanoidRootPart" and c.Name ~= "Headset" and c.Name ~= "EnergyCan" then
				lo = math.min(lo, c.Position.Y - c.Size.Y / 2)
			end
		end
	end
	return parts, anch, extra, lo
end
local function jointErr()
	local w, n = 0, 0
	for _, c in ipairs(m:GetDescendants()) do
		if c:IsA("AnimationConstraint") then
			n += 1
			w = math.max(w, (c.Attachment0.WorldCFrame.Position - c.Attachment1.WorldCFrame.Position).Magnitude)
		end
	end
	return w, n
end
local parts, anch, extra, lo = counts()
local old = {}
for _, d in ipairs(m:GetDescendants()) do
	local n = d.Name
	if n == "ShirtFront" or n == "ShirtBack" or n:find("Sleeve$") or n:find("PantBand$") or n:find("PantCuff$") or n:find("^Headwear") or n == "EnergyDrink" or n == "Accessory" or n == "Mug" or n == "Briefcase" or n == "FishingRod" or n == "BBQTongs" then
		table.insert(old, d:GetFullName())
	end
end
local welds = {}
for _, d in ipairs(m:GetDescendants()) do
	if d:IsA("WeldConstraint") or d:IsA("Weld") or d:IsA("Motor6D") then
		table.insert(welds, d.ClassName .. ":" .. d.Name .. ":" .. d.Parent.Name .. ":" .. (d.Part0 and d.Part0.Name or "?") .. "->" .. (d.Part1 and d.Part1.Name or "?"))
	end
end
local nOP, badOP = 0, 0
for _, a in ipairs(m:GetDescendants()) do
	if a:IsA("Attachment") and a.Name ~= "JointRotation" then
		local ov = a:FindFirstChild("OriginalPosition")
		if ov then
			nOP += 1
			if (ov.Value - a.Position).Magnitude > 1e-3 then
				badOP += 1
			end
		end
	end
end
local je, nj = jointErr()
local sa, tex = 0, 0
for _, p in ipairs(m:GetChildren()) do
	if p:IsA("MeshPart") then
		if p:FindFirstChildOfClass("SurfaceAppearance") then
			sa += 1
		end
		if p.TextureID ~= "" then
			tex += 1
		end
	end
end
local labels = {}
for _, d in ipairs(m:GetDescendants()) do
	if d:IsA("TextLabel") then
		table.insert(labels, d.Text)
	end
end
local can, rh, hs, hd = m.EnergyCan, m.RightHand, m.Headset, m.Head
emit("spawned", { mode = SPAWN_MODE, parts = parts, anchoredParts = anch, extraParts = extra, soles = lo, feetOffset = m:GetAttribute("FeetOffset"), oldOverlayHits = old, welds = welds,
	joints = nj, jointWorstErr = je, originalPosition = nOP, originalPositionBad = badOP, surfaceAppearanceParts = sa, textureIdParts = tex, labels = labels, pivot = { m:GetPivot().Position.X, m:GetPivot().Position.Y, m:GetPivot().Position.Z },
	canFlags = { can.CanCollide, can.CanQuery, can.CanTouch, can.Massless, can.Anchored }, headsetFlags = { hs.CanCollide, hs.CanQuery, hs.CanTouch, hs.Massless, hs.Anchored },
	canRelHand = { rh.CFrame:ToObjectSpace(can.CFrame).Position.X, rh.CFrame:ToObjectSpace(can.CFrame).Position.Y, rh.CFrame:ToObjectSpace(can.CFrame).Position.Z },
	headsetRelHead = { hd.CFrame:ToObjectSpace(hs.CFrame).Position.X, hd.CFrame:ToObjectSpace(hs.CFrame).Position.Y, hd.CFrame:ToObjectSpace(hs.CFrame).Position.Z },
	headColor = { m.Head.Color.R, m.Head.Color.G, m.Head.Color.B }, humanoidDisplayName = hum and hum.DisplayName, modelName = m.Name })
-- ---- carry harness
local player = game.Players:GetPlayers()[1] or game.Players.PlayerAdded:Wait()
local pch = player.Character or player.CharacterAdded:Wait()
local ph = pch:WaitForChild("HumanoidRootPart")
local phum = pch:WaitForChild("Humanoid")
task.wait(2)
local orig = {}
for _, d in ipairs(m:GetDescendants()) do
	if d:IsA("BasePart") then
		orig[d] = { d.CanCollide, d.Massless, d.Anchored }
		d.Anchored = true
		d.CanCollide = false
		d.Massless = true
	end
end
m:PivotTo(ph.CFrame * CFrame.new(0, 0, 5))
for d in pairs(orig) do
	d.Anchored = false
end
local weld = Instance.new("WeldConstraint")
weld.Name = "QA_CarryWeld"
weld.Part0, weld.Part1 = ph, hrp
weld.Parent = ph
task.wait(1.5)
local base = {}
for _, p in ipairs(m:GetChildren()) do
	if p:IsA("BasePart") then
		base[p] = hrp.CFrame:ToObjectSpace(p.CFrame)
	end
end
local rel = function(a, b)
	return a.CFrame:ToObjectSpace(b.CFrame)
end
local canBase, hsBase, handBase, headBase = rel(rh, can), rel(hd, hs), rel(m.RightLowerArm, rh), rel(m.UpperTorso, hd)
local carrierBase = ph.CFrame:ToObjectSpace(hrp.CFrame)
local mx = { part = 0, rot = 0, can = 0, headset = 0, hand = 0, head = 0, carrier = 0, joint = 0, tilt = 0 }
local worstName, samples = "", 0
local conn = RS.Heartbeat:Connect(function()
	samples += 1
	for p, b in pairs(base) do
		local r = hrp.CFrame:ToObjectSpace(p.CFrame)
		local dp = (r.Position - b.Position).Magnitude
		if dp > mx.part then
			mx.part, worstName = dp, p.Name
		end
		local _, ang = (r:Inverse() * b):ToAxisAngle()
		mx.rot = math.max(mx.rot, math.abs(ang))
	end
	mx.can = math.max(mx.can, (rel(rh, can).Position - canBase.Position).Magnitude)
	mx.headset = math.max(mx.headset, (rel(hd, hs).Position - hsBase.Position).Magnitude)
	mx.hand = math.max(mx.hand, (rel(m.RightLowerArm, rh).Position - handBase.Position).Magnitude)
	mx.head = math.max(mx.head, (rel(m.UpperTorso, hd).Position - headBase.Position).Magnitude)
	mx.carrier = math.max(mx.carrier, (ph.CFrame:ToObjectSpace(hrp.CFrame).Position - carrierBase.Position).Magnitude)
	mx.tilt = math.max(mx.tilt, 1 - hrp.CFrame.UpVector.Y)
end)
local plan = { { 90, 4.5, true }, { -90, 4.5, true }, { 180, 4.5, true }, { 90, 4.5, true }, { -135, 4.0, true }, { 135, 4.0, true }, { 180, 4.0, true }, { 0, 2.0, false } }
local t0 = os.clock()
local startPos = ph.Position
local yawTotal, last = 0, ph.CFrame.LookVector
local jumps, turns = 0, 0
for _, st in ipairs(plan) do
	if st[1] ~= 0 then
		ph.CFrame = ph.CFrame * CFrame.Angles(0, math.rad(st[1]), 0)
		turns += math.abs(st[1])
	end
	if st[3] then
		phum.Jump = true
		jumps += 1
	end
	local tEnd = os.clock() + st[2]
	while os.clock() < tEnd do
		task.wait(0.1)
		local lv = ph.CFrame.LookVector
		yawTotal += math.abs(math.atan2(last:Cross(lv).Y, last:Dot(lv)))
		last = lv
		local v = ph.AssemblyLinearVelocity
		local f = Vector3.new(lv.X, 0, lv.Z).Unit * 14
		ph.AssemblyLinearVelocity = Vector3.new(f.X, v.Y, f.Z)
		mx.joint = math.max(mx.joint, (jointErr()))
		if st[3] and phum:GetState() == Enum.HumanoidStateType.Landed then
			phum.Jump = true
			jumps += 1
		end
	end
end
phum:Move(Vector3.zero, false)
task.wait(1)
conn:Disconnect()
emit("carry", { seconds = os.clock() - t0, samples = samples, jumps = jumps, commandedTurnsDeg = turns, totalYawRad = yawTotal, travelledStuds = (ph.Position - startPos).Magnitude,
	maxPartRelPosDev = mx.part, worstPart = worstName, maxPartRelRotDevRad = mx.rot, maxCanRelHandDrift = mx.can, maxHeadsetRelHeadDrift = mx.headset, maxHandRelForearmDrift = mx.hand,
	maxHeadRelTorsoDrift = mx.head, maxModelRelCarrierDrift = mx.carrier, maxJointErr = mx.joint, maxUpTilt = mx.tilt })
-- ---- release + production re-placement
weld:Destroy()
for d, o in pairs(orig) do
	d.CanCollide, d.Massless = o[1], o[2]
	d.Anchored = true
end
task.wait(0.5)
Builder.PlaceAt(m, CFrame.new(-14, 0, 10))
for d, o in pairs(orig) do
	d.Anchored = o[3]
end
task.wait(2)
local _, _, _, lo2 = counts()
local je2 = jointErr()
local worst2 = 0
for p, b in pairs(base) do
	local r = hrp.CFrame:ToObjectSpace(p.CFrame)
	worst2 = math.max(worst2, (r.Position - b.Position).Magnitude)
end
emit("replaced", { soles = lo2, hrp = { hrp.Position.X, hrp.Position.Y, hrp.Position.Z }, partRelDev = worst2, canRelHandDrift = (rel(rh, can).Position - canBase.Position).Magnitude,
	headsetRelHeadDrift = (rel(hd, hs).Position - hsBase.Position).Magnitude, jointErr = je2, state = tostring(hum and hum:GetState()) })
local a3 = 0
for _, d in ipairs(m:GetDescendants()) do
	if d:IsA("BasePart") and d.Anchored then
		a3 += 1
	end
end
emit("end", { anchoredPartsAfterProductionPlaceAt = a3 })
print("GDFIN_DONE")
]==]
SRC = string.gsub(SRC, "__MODE__", "preview") -- use "builder" to spawn through DadModelBuilder.Build directly
local old = game.ServerScriptService:FindFirstChild("GD_FINAL_QA")
if old then
	old:Destroy()
end
local s = Instance.new("Script")
s.Name = "GD_FINAL_QA"
s.Source = SRC
s.Parent = game.ServerScriptService
print("GD_FINAL_QA installed")
