--!nocheck
-- Run-mode (F8) pose check on the free QA copy: Neutral and HoldCan must hold while the copy is simulated and the constraints are enabled.
-- Install: paste this whole file into the command bar (it creates ServerScriptService.GD_QA_PoseRuntime), then press Run (F8); read the Output; Stop.
local SRC = [==[
local HS = game:GetService("HttpService")
local function emit(tag, t)
	print("GDRT|" .. tag .. "|" .. HS:JSONEncode(t))
end
task.wait(3)
local m = workspace:WaitForChild("GamerDad_QA_Copy")
local PC = require(m.PoseController)
local root = m.HumanoidRootPart
local function worst(which)
	local folder = m[(which == "Neutral") and "NeutralPose" or "HoldCanPose"]
	local w, wn = 0, ""
	for _, v in ipairs(folder:GetChildren()) do
		local name = string.gsub(v.Name, "_PartCFrame$", "")
		local part = m:FindFirstChild(name)
		if part and part:IsA("BasePart") then
			local act = root.CFrame:ToObjectSpace(part.CFrame)
			local d = (act.Position - v.Value.Position).Magnitude
			if d > w then
				w, wn = d, name
			end
		end
	end
	return w, wn
end
local function anchoredCount()
	local n = 0
	for _, p in ipairs(m:GetDescendants()) do
		if p:IsA("BasePart") and p.Anchored then
			n += 1
		end
	end
	return n
end
local function seg()
	local function att(part, name)
		return m[part][name].WorldPosition
	end
	local r = {}
	for _, s in ipairs({ "Right", "Left" }) do
		r[s] = { upper = (att(s .. "LowerArm", s .. "ElbowRigAttachment") - att(s .. "UpperArm", s .. "ShoulderRigAttachment")).Magnitude, lower = (att(s .. "Hand", s .. "WristRigAttachment") - att(s .. "LowerArm", s .. "ElbowRigAttachment")).Magnitude }
	end
	return r
end
local w0, n0 = worst("HoldCan")
emit("start_holdcan", { worstVsHoldCan = w0, part = n0, anchored = anchoredCount(), segs = seg(), hrpY = root.Position.Y, state = tostring(m.Humanoid:GetState()) })
PC.Apply(m, "Neutral")
task.wait(1.5)
local wN, nN = worst("Neutral")
local wH, nH = worst("HoldCan")
emit("neutral_held", { worstVsNeutral = wN, part = nN, worstVsHoldCan = wH, anchored = anchoredCount(), segs = seg(), rightHandY = m.RightHand.Position.Y, canRelHand = { m.RightHand.CFrame:ToObjectSpace(m.EnergyCan.CFrame).Position.X, m.RightHand.CFrame:ToObjectSpace(m.EnergyCan.CFrame).Position.Y, m.RightHand.CFrame:ToObjectSpace(m.EnergyCan.CFrame).Position.Z } })
PC.Apply(m, "HoldCan")
task.wait(1.5)
local w1, n1 = worst("HoldCan")
emit("holdcan_restored", { worstVsHoldCan = w1, part = n1, anchored = anchoredCount(), segs = seg(), rightHandY = m.RightHand.Position.Y, canRelHand = { m.RightHand.CFrame:ToObjectSpace(m.EnergyCan.CFrame).Position.X, m.RightHand.CFrame:ToObjectSpace(m.EnergyCan.CFrame).Position.Y, m.RightHand.CFrame:ToObjectSpace(m.EnergyCan.CFrame).Position.Z } })
print("GDRT_DONE")
]==]
local old = game.ServerScriptService:FindFirstChild("GD_QA_PoseRuntime")
if old then
	old:Destroy()
end
local s = Instance.new("Script")
s.Name = "GD_QA_PoseRuntime"
s.Source = SRC
s.Parent = game.ServerScriptService
print("GD_QA_PoseRuntime installed")
