-- Studio check of the assembled/inserted FishermanDad_R15 (Edit mode). Prints one line per aspect; paste into the command bar.
local m = workspace:FindFirstChild("FishermanDad_R15") or workspace:FindFirstChild("FishermanDad_Review") or game.ServerStorage:FindFirstChild("FishermanDad_R15") or game.ServerStorage:FindFirstChild("FishermanDadFinal")
assert(m, "model not found")
local hrp = m.HumanoidRootPart
local nparts, nmesh, lo = 0, 0, math.huge
local loProp = math.huge
for _, p in ipairs(m:GetChildren()) do
	if p:IsA("BasePart") then
		nparts += 1
		if p:IsA("MeshPart") then
			nmesh += 1
		end
		if p.Name ~= "HumanoidRootPart" and p.Name ~= "FishingRod" and p.Name ~= "Bucket" then
			lo = math.min(lo, p.Position.Y - p.Size.Y / 2)
		end
	end
end
print("CHK parts", nparts, "meshparts", nmesh, "soles", lo, "HRP", tostring(hrp.Position))
local bk = m.Bucket
print("CHK bucketBottom", bk.Position.Y - bk.Size.Y / 2, "rodBottom", m.FishingRod.Position.Y - m.FishingRod.Size.Y / 2, "rodTop", m.FishingRod.Position.Y + m.FishingRod.Size.Y / 2)
local worst, n = 0, 0
local worstOP, nOP, badOP = 0, 0, 0
for _, c in ipairs(m:GetDescendants()) do
	if c:IsA("AnimationConstraint") then
		n += 1
		local d = (c.Attachment0.WorldCFrame.Position - c.Attachment1.WorldCFrame.Position).Magnitude
		worst = math.max(worst, d)
	elseif c:IsA("Attachment") then
		local ov = c:FindFirstChild("OriginalPosition")
		if ov and ov:IsA("Vector3Value") and c.Name ~= "JointRotation" then
			nOP += 1
			local dd = (ov.Value - c.Position).Magnitude
			worstOP = math.max(worstOP, dd)
			if dd > 1e-3 then
				badOP += 1
			end
		end
	end
end
print("CHK animConstraints", n, "worstJointErr", worst, "OriginalPosition checked", nOP, "bad", badOP, "maxdiff", worstOP)
local rod, grip = m.FishingRod, m.FishingRod:FindFirstChild("RodGrip")
local bgrip = bk:FindFirstChild("BucketMount")
print("CHK RodGrip", grip and grip.Part0 and grip.Part0.Name, grip and grip.Part1 and grip.Part1.Name, "BucketMount", bgrip and bgrip.Part0.Name, bgrip and bgrip.Part1.Name)
print("CHK rodFlags", rod.Anchored, rod.CanCollide, rod.CanQuery, rod.CanTouch, rod.Massless, "bucketFlags", bk.Anchored, bk.CanCollide, bk.CanQuery, bk.CanTouch, bk.Massless)
print("CHK rod rel LeftHand", tostring(m.LeftHand.CFrame:ToObjectSpace(rod.CFrame).Position), "bucket rel HRP", tostring(hrp.CFrame:ToObjectSpace(bk.CFrame).Position))
local welds, anch, scripts = 0, 0, 0
for _, d in ipairs(m:GetDescendants()) do
	if d:IsA("WeldConstraint") then
		welds += 1
	end
	if d:IsA("BasePart") and d.Anchored then
		anch += 1
	end
	if d:IsA("LuaSourceContainer") then
		scripts += 1
	end
end
print("CHK welds", welds, "anchoredParts", anch, "scripts", scripts)
local sa, noCM = 0, 0
for _, p in ipairs(m:GetChildren()) do
	if p:IsA("MeshPart") then
		local s = p:FindFirstChildOfClass("SurfaceAppearance")
		if s then
			sa += 1
			if tostring(s.ColorMap) == "" and not s.ColorMapContent then
				noCM += 1
			end
		end
		if p.Name == "Head" or p.Name == "FishingRod" or p.Name == "Bucket" then
			print("CHK colour", p.Name, tostring(p.Color), "SA", s ~= nil, s and tostring(s.ColorMap), "TextureID", p.TextureID)
		end
	end
end
print("CHK surfaceAppearances", sa, "withoutColorMap", noCM)
local hum = m:FindFirstChildOfClass("Humanoid")
print("CHK humanoid", hum and hum.RigType.Name, hum and hum.HipHeight)
local cf, sz = m:GetBoundingBox()
print("CHK bbox", tostring(sz), tostring(cf.Position))
