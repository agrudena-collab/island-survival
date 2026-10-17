--!nocheck
-- QA of the PoseController on a free (unanchored) COPY of the model, Edit mode. Prints "GDQA|<tag>|<json>" lines.
local HS = game:GetService("HttpService")
local src = workspace:FindFirstChild("GamerDad_R15")
assert(src, "assembled model missing")
local old = workspace:FindFirstChild("GamerDad_QA_Copy")
if old then
	old:Destroy()
end
local copy = src:Clone()
copy.Name = "GamerDad_QA_Copy"
copy.Parent = workspace
copy:TranslateBy(Vector3.new(-10, 0, 0))
local PC = require(copy.PoseController)
local function emit(tag, t)
	print("GDQA|" .. tag .. "|" .. HS:JSONEncode(t))
end
local function states()
	local a, e, n = {}, {}, 0
	for _, d in ipairs(copy:GetDescendants()) do
		if d:IsA("BasePart") then
			a[d.Name] = d.Anchored
			n += 1
		elseif d:IsA("AnimationConstraint") or d:IsA("BallSocketConstraint") or d:IsA("NoCollisionConstraint") or d:IsA("WeldConstraint") then
			e[d:GetFullName()] = d.Enabled
		end
	end
	return a, e, n
end
local function same(t1, t2)
	for k, v in pairs(t1) do
		if t2[k] ~= v then
			return false
		end
	end
	for k, v in pairs(t2) do
		if t1[k] ~= v then
			return false
		end
	end
	return true
end
local function att(part, name)
	local a = copy[part]:FindFirstChild(name)
	return a and a.WorldPosition
end
local function segs()
	local r = {}
	for _, s in ipairs({ "Right", "Left" }) do
		local S, E, W = att(s .. "UpperArm", s .. "ShoulderRigAttachment"), att(s .. "LowerArm", s .. "ElbowRigAttachment"), att(s .. "Hand", s .. "WristRigAttachment")
		r[s] = { upper = (E - S).Magnitude, lower = (W - E).Magnitude, elbowGap = (att(s .. "UpperArm", s .. "ElbowRigAttachment") - E).Magnitude, wristGap = (att(s .. "LowerArm", s .. "WristRigAttachment") - W).Magnitude }
	end
	return r
end
local function cfs()
	local t = {}
	for _, p in ipairs(copy:GetChildren()) do
		if p:IsA("BasePart") then
			t[p.Name] = p.CFrame
		end
	end
	return t
end
local function dev(a, b)
	local dp, dr = 0, 0
	for k, c in pairs(a) do
		local d = b[k]
		dp = math.max(dp, (c.Position - d.Position).Magnitude)
		local rel = c:ToObjectSpace(d)
		local _, ang = rel:ToAxisAngle()
		dr = math.max(dr, math.abs(ang))
	end
	return dp, dr
end
local a0, e0, n0 = states()
local c0 = cfs()
emit("initial", { parts = n0, anchoredAny = (function()
	for _, v in pairs(a0) do
		if v then
			return true
		end
	end
	return false
end)(), segs = segs() })
PC.Apply(copy, "Neutral")
local a1, e1 = states()
local cN = cfs()
local dpN, drN = dev(c0, cN)
emit("after_neutral", { statesRestored = same(a0, a1) and same(e0, e1), anchoredAny = (function()
	for _, v in pairs(a1) do
		if v then
			return true
		end
	end
	return false
end)(), segs = segs(), maxMoveVsHoldCan = dpN, maxRotVsHoldCan = drN,
	canRelHand = { copy.RightHand.CFrame:ToObjectSpace(copy.EnergyCan.CFrame).Position.X, copy.RightHand.CFrame:ToObjectSpace(copy.EnergyCan.CFrame).Position.Y, copy.RightHand.CFrame:ToObjectSpace(copy.EnergyCan.CFrame).Position.Z }, rightHandY = copy.RightHand.Position.Y, leftHandY = copy.LeftHand.Position.Y })
PC.Apply(copy, "HoldCan")
local a2, e2 = states()
local c2 = cfs()
local dp2, dr2 = dev(c0, c2)
emit("after_holdcan", { statesRestored = same(a0, a2) and same(e0, e2), maxPosDev = dp2, maxRotDev = dr2, segs = segs(),
	canRelHand = { copy.RightHand.CFrame:ToObjectSpace(copy.EnergyCan.CFrame).Position.X, copy.RightHand.CFrame:ToObjectSpace(copy.EnergyCan.CFrame).Position.Y, copy.RightHand.CFrame:ToObjectSpace(copy.EnergyCan.CFrame).Position.Z } })
PC.QAFreeze(copy, true)
local a3 = states()
local allAnch = true
for _, v in pairs(a3) do
	allAnch = allAnch and v
end
PC.QAFreeze(copy, false)
local a4, e4 = states()
emit("qafreeze", { frozenAllAnchored = allAnch, restoredAfter = same(a0, a4) and same(e0, e4) })
-- error path: a copy of the controller whose protected block raises after everything was anchored / disabled -> the states must still be restored
local bad = Instance.new("ModuleScript")
bad.Name = "PoseController_injected"
bad.Source = string.gsub(copy.PoseController.Source, "local target: { %[BasePart%]: CFrame } = {}", "error('injected failure') local target = {}")
bad.Parent = copy
local ok, err = pcall(function()
	require(bad).Apply(copy, "Neutral")
end)
local a5, e5 = states()
emit("error_path", { applyReturnedOk = ok, err = tostring(err), statesRestored = same(a0, a5) and same(e0, e5), injectedSourceChanged = bad.Source ~= copy.PoseController.Source })
bad:Destroy()
PC.Apply(copy, "HoldCan")
local dp6, dr6 = dev(c0, cfs())
emit("final_back_to_holdcan", { maxPosDev = dp6, maxRotDev = dr6 })
print("GDQA_DONE")
