-- F5 SERVER context: check the dad built by DadModelBuilder from ServerStorage.FishermanDadFinal (catalog Id GardenerDad).
local f = workspace:WaitForChild("DadPreview")
local names = {}
for _, c in ipairs(f:GetChildren()) do
	table.insert(names, c.Name)
end
print("SPAWN preview children", table.concat(names, ","))
local m = f:FindFirstChild("GardenerDad")
assert(m, "GardenerDad model not spawned")
local expected = { HumanoidRootPart = true, Head = true, LeftFoot = true, LeftHand = true, LeftLowerArm = true, LeftLowerLeg = true, LeftUpperArm = true, LeftUpperLeg = true,
	LowerTorso = true, RightFoot = true, RightHand = true, RightLowerArm = true, RightLowerLeg = true, RightUpperArm = true, RightUpperLeg = true, UpperTorso = true, FishingRod = true, Bucket = true }
local extra, parts, anch, lo = {}, 0, 0, math.huge
for _, c in ipairs(m:GetChildren()) do
	if c:IsA("BasePart") then
		parts += 1
		if c.Anchored then
			anch += 1
		end
		if not expected[c.Name] then
			table.insert(extra, c.Name)
		end
		if c.Name ~= "HumanoidRootPart" and c.Name ~= "FishingRod" and c.Name ~= "Bucket" then
			lo = math.min(lo, c.Position.Y - c.Size.Y / 2)
		end
	end
end
print("SPAWN GardenerDad parts", parts, "anchored", anch, "extraParts", #extra, table.concat(extra, ","), "soles", lo, "FeetOffset", m:GetAttribute("FeetOffset"))
local ov = {}
for _, d in ipairs(m:GetDescendants()) do
	if d.Name == "Mug" or d.Name == "Briefcase" or d.Name == "Shovel" or d.Name == "Apron" or d.Name == "Brim" or d.Name == "Tie" then
		table.insert(ov, d:GetFullName())
	end
end
print("SPAWN overlays (old accessory/headwear/detail)", #ov, table.concat(ov, ","))
local w, n = 0, 0
for _, c in ipairs(m:GetDescendants()) do
	if c:IsA("AnimationConstraint") then
		n += 1
		w = math.max(w, (c.Attachment0.WorldCFrame.Position - c.Attachment1.WorldCFrame.Position).Magnitude)
	end
end
local nOP, badOP = 0, 0
for _, a in ipairs(m:GetDescendants()) do
	if a:IsA("Attachment") and a.Name ~= "JointRotation" then
		local ovv = a:FindFirstChild("OriginalPosition")
		if ovv then
			nOP += 1
			if (ovv.Value - a.Position).Magnitude > 1e-3 then
				badOP += 1
			end
		end
	end
end
print("SPAWN joints", n, "worstErr", w, "OriginalPosition", nOP, "bad", badOP)
local rod, bk, lh, hrp = m.FishingRod, m.Bucket, m.LeftHand, m.HumanoidRootPart
print("SPAWN rod rel hand", lh.CFrame:ToObjectSpace(rod.CFrame).Position, "bucket rel HRP", hrp.CFrame:ToObjectSpace(bk.CFrame).Position)
print("SPAWN rodGrip", rod:FindFirstChild("RodGrip") and rod.RodGrip.Part0.Name, "BucketMount", bk:FindFirstChild("BucketMount") and bk.BucketMount.Part0.Name,
	"rod flags", rod.CanCollide, rod.CanQuery, rod.CanTouch, rod.Massless, "bucket flags", bk.CanCollide, bk.CanQuery, bk.CanTouch, bk.Massless)
local sa, cm = 0, 0
for _, p in ipairs(m:GetChildren()) do
	if p:IsA("MeshPart") then
		local s = p:FindFirstChildOfClass("SurfaceAppearance")
		if s then
			sa += 1
		end
		if p.TextureID ~= "" then
			cm += 1
		end
	end
end
print("SPAWN colours: SurfaceAppearance", sa, "TextureID parts", cm, "Head.Color", m.Head.Color)
print("SPAWN scripts in model", (function()
	local k = 0
	for _, d in ipairs(m:GetDescendants()) do
		if d:IsA("LuaSourceContainer") then
			k += 1
		end
	end
	return k
end)(), "billboard", m:FindFirstChildWhichIsA("BillboardGui", true) and m:FindFirstChildWhichIsA("BillboardGui", true).Name)
for _, c in ipairs(m:GetDescendants()) do
	if c:IsA("TextLabel") then
		print("SPAWN label", c.Text)
	end
end
print("SPAWN pivot", m:GetPivot().Position)
