-- QA, F5 SERVER context: carry-attachment test of the SPAWNED dad (NOT game stealing; no carry mechanic exists yet).
-- 1) state report, 2) model welded to the player's HumanoidRootPart for 22 s (the CLIENT moves the player: walk, turns, jumps),
-- 3) release + re-place on the floor and re-measure. All drifts are measured relative to LeftHand->GrillTongs (towel/apron/stains are baked into UpperTorso, so torso->towel is constant by construction).
local m = workspace.DadPreview.GrillDad  -- spawned by DadModelBuilder (catalog Id GrillDad, final art GrillDadFinal)
local Builder = require(game.ServerScriptService:FindFirstChild("DadModelBuilder", true))
local hrp, hum = m.HumanoidRootPart, m:FindFirstChildOfClass("Humanoid")
local rod, lh = m.GrillTongs, m.LeftHand
task.wait(1)
local function soles()
	local y = math.huge
	for _, p in ipairs(m:GetChildren()) do
		if p:IsA("BasePart") and p.Name ~= "HumanoidRootPart" and p.Name ~= "GrillTongs" then
			y = math.min(y, p.Position.Y - p.Size.Y / 2)
		end
	end
	return y
end
local function jointErr()
	local w = 0
	for _, c in ipairs(m:GetDescendants()) do
		if c:IsA("AnimationConstraint") then
			w = math.max(w, (c.Attachment0.WorldCFrame.Position - c.Attachment1.WorldCFrame.Position).Magnitude)
		end
	end
	return w
end
local rod0 = lh.CFrame:ToObjectSpace(rod.CFrame)
print("F5 T1 soles", soles(), "HRP", hrp.Position, "state", hum and hum:GetState(), "jointErr", jointErr())
print("F5 T1 tongs rel hand", rod0.Position, "tongsAnch", rod.Anchored, "tongsCollide", rod.CanCollide, "anchoredParts", (function()
	local n = 0
	for _, d in ipairs(m:GetDescendants()) do
		if d:IsA("BasePart") and d.Anchored then
			n += 1
		end
	end
	return n
end)())
local P = game.Players:GetPlayers()[1]
local ph = P.Character:WaitForChild("HumanoidRootPart")
local orig = {}
for _, d in ipairs(m:GetDescendants()) do
	if d:IsA("BasePart") then
		orig[d] = { d.CanCollide, d.Massless, d.Anchored }
		d.Anchored = true -- pivot while anchored (an unanchored Humanoid rig would only move its HumanoidRootPart)
		d.CanCollide = false
		d.Massless = true
	end
end
m:PivotTo(ph.CFrame * CFrame.new(0, 0, -5))
for d, _ in pairs(orig) do
	d.Anchored = false
end
local w = Instance.new("WeldConstraint")
w.Name = "QA_CarryWeld"
w.Part0, w.Part1 = ph, hrp
w.Parent = ph
print("CARRY START")
local base2 = ph.CFrame:ToObjectSpace(hrp.CFrame)
local m1, m2, m3, n = 0, 0, 0, 0
local t0 = os.clock()
while os.clock() - t0 < 22 do
	m1 = math.max(m1, (lh.CFrame:ToObjectSpace(rod.CFrame).Position - rod0.Position).Magnitude)
	m3 = math.max(m3, (ph.CFrame:ToObjectSpace(hrp.CFrame).Position - base2.Position).Magnitude)
	n += 1
	task.wait()
end
print("CARRY samples", n, "tongsDrift", m1, "modelDrift", m3, "jointErr", jointErr(), "upTilt", 1 - hrp.CFrame.UpVector.Y)
w:Destroy()
for d, o in pairs(orig) do
	d.CanCollide, d.Massless = o[1], o[2]
	d.Anchored = true
end
Builder.PlaceAt(m, CFrame.new(-14, 0, 0)) -- production re-placement helper
for d, o in pairs(orig) do
	d.Anchored = o[3]
end
task.wait(1.5)
print("REPLACED soles", soles(), "HRP", hrp.Position, "tongs rel hand drift", (lh.CFrame:ToObjectSpace(rod.CFrame).Position - rod0.Position).Magnitude, "jointErr", jointErr())
