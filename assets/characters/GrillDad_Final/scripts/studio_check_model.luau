-- Studio check of the assembled/inserted GrillDad_R15 (Edit mode). One CHK line per aspect; paste into the command bar.
local m = workspace:FindFirstChild("GrillDad_R15") or game.ServerStorage:FindFirstChild("GrillDad_R15") or game.ServerStorage:FindFirstChild("GrillDadFinal")
assert(m, "model not found")
local hrp = m.HumanoidRootPart
local nparts, nmesh, lo = 0, 0, math.huge
for _, p in ipairs(m:GetChildren()) do
	if p:IsA("BasePart") then
		nparts += 1
		if p:IsA("MeshPart") then
			nmesh += 1
		end
		if p.Name ~= "HumanoidRootPart" and p.Name ~= "GrillTongs" then
			lo = math.min(lo, p.Position.Y - p.Size.Y / 2)
		end
	end
end
print("CHK parts", nparts, "meshparts", nmesh, "soles", lo, "HRP", tostring(hrp.Position))
local tg = m.GrillTongs
print("CHK tongsBottom", tg.Position.Y - tg.Size.Y / 2, "tongsTop", tg.Position.Y + tg.Size.Y / 2)
local worst, n = 0, 0
local worstOP, nOP, badOP = 0, 0, 0
for _, c in ipairs(m:GetDescendants()) do
	if c:IsA("AnimationConstraint") then
		n += 1
		worst = math.max(worst, (c.Attachment0.WorldCFrame.Position - c.Attachment1.WorldCFrame.Position).Magnitude)
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
local grip = tg:FindFirstChild("TongsGrip")
print("CHK TongsGrip", grip and grip.Part0 and grip.Part0.Name, grip and grip.Part1 and grip.Part1.Name)
print("CHK tongsFlags", tg.Anchored, tg.CanCollide, tg.CanQuery, tg.CanTouch, tg.Massless)
print("CHK tongs rel LeftHand", tostring(m.LeftHand.CFrame:ToObjectSpace(tg.CFrame).Position))
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
			if tostring(s.ColorMap) == "" then
				noCM += 1
			end
		end
		if p.Name == "Head" or p.Name == "GrillTongs" or p.Name == "UpperTorso" then
			print("CHK colour", p.Name, tostring(p.Color), "SA", s ~= nil, s and tostring(s.ColorMap), "TextureID", p.TextureID)
		end
	end
end
print("CHK surfaceAppearances", sa, "withoutColorMap", noCM)
local hum = m:FindFirstChildOfClass("Humanoid")
print("CHK humanoid", hum and hum.RigType.Name, hum and hum.HipHeight)
local cf, sz = m:GetBoundingBox()
print("CHK bbox", tostring(sz), tostring(cf.Position))
