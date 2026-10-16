-- QA, F5 (Test -> Play) SERVER context: carry-attachment test of the SPAWNED dad (NOT game stealing; no carry mechanic exists yet).
-- 1) state report, 2) model welded to the player's HumanoidRootPart for 22 s (the CLIENT moves the player: walk, turns, jumps),
-- 3) release + re-place on the floor and re-measure. All drifts are measured relative to LeftHand->FishingRod and HRP->Bucket.
local m = workspace.DadPreview.GardenerDad  -- spawned by DadModelBuilder (catalog Id GardenerDad, final art FishermanDadFinal)
local hrp, hum = m.HumanoidRootPart, m:FindFirstChildOfClass("Humanoid")
local rod, bucket, lh = m.FishingRod, m.Bucket, m.LeftHand
task.wait(1)
local Builder = require(game.ServerScriptService:FindFirstChild("DadModelBuilder", true))
local function soles()
	local y = math.huge
	for _, p in ipairs(m:GetChildren()) do
		if p:IsA("BasePart") and p.Name ~= "HumanoidRootPart" and p.Name ~= "FishingRod" and p.Name ~= "Bucket" then
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
local bk0 = hrp.CFrame:ToObjectSpace(bucket.CFrame)
print("F5 T1 soles", soles(), "HRP", hrp.Position, "state", hum and hum:GetState(), "jointErr", jointErr())
print("F5 T1 rod rel hand", rod0.Position, "bucket rel HRP", bk0.Position, "rodAnch", rod.Anchored, "rodCollide", rod.CanCollide, "bucketAnch", bucket.Anchored, "anchoredParts", (function()
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
m:PivotTo(ph.CFrame * CFrame.new(0, 0, -5)) -- pivot while still anchored (see DadModelBuilder.PlaceAt)
for _, d in ipairs(m:GetDescendants()) do
	if d:IsA("BasePart") then
		orig[d] = { d.CanCollide, d.Massless, d.Anchored }
		d.Anchored = false -- QA only: the spawner anchors the dad; a carried dad must follow the carrier
		d.CanCollide = false
		d.Massless = true
	end
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
	m2 = math.max(m2, (hrp.CFrame:ToObjectSpace(bucket.CFrame).Position - bk0.Position).Magnitude)
	m3 = math.max(m3, (ph.CFrame:ToObjectSpace(hrp.CFrame).Position - base2.Position).Magnitude)
	n += 1
	task.wait()
end
print("CARRY samples", n, "rodDrift", m1, "bucketDrift", m2, "modelDrift", m3, "jointErr", jointErr(), "upTilt", 1 - hrp.CFrame.UpVector.Y)
w:Destroy()
for d, o in pairs(orig) do
	d.CanCollide, d.Massless = o[1], o[2]
end
Builder.PlaceAt(m, CFrame.new(-14, 0, 0)) -- re-place through the production helper
task.wait(1.5)
print("REPLACED soles", soles(), "HRP", hrp.Position, "rod rel hand drift", (lh.CFrame:ToObjectSpace(rod.CFrame).Position - rod0.Position).Magnitude, "bucket drift", (hrp.CFrame:ToObjectSpace(bucket.CFrame).Position - bk0.Position).Magnitude, "jointErr", jointErr())
