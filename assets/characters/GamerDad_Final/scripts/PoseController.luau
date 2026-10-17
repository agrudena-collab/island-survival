--!strict
-- GamerDad PoseController (ModuleScript, also stored inside the model).
--   Apply(model, "HoldCan" | "Neutral")   HoldCan = stored display pose (default), Neutral = QA control pose (arms straight down, can follows the right hand).
--   QAFreeze(model, true [, pose])        explicit, intentional freeze for inspection: anchors every part, keeps the constraints off and (optionally) shows a pose.
--   QAFreeze(model, false)                restores the exact previous Anchored / Enabled states.
-- Both pose folders store every part CFrame relative to HumanoidRootPart.
-- Apply sets the part CFrames AND the AnimationConstraint.Transform of every joint (so the pose also holds while the model is simulated and the constraints
-- are enabled again), then ALWAYS restores the input Anchored states of every BasePart and the Enabled states of every constraint it touched, also when an
-- error occurs. It never leaves a part anchored by itself (the old Gamer Dad controller left the model anchored after Neutral).
local M = {}

local frozen: { [Model]: { anchored: { [BasePart]: boolean }, enabled: { [Instance]: boolean } } } = {}

local function isConstraint(d: Instance): boolean
	return d:IsA("AnimationConstraint") or d:IsA("BallSocketConstraint") or d:IsA("NoCollisionConstraint") or d:IsA("WeldConstraint")
end

local function snapshot(model: Model)
	local anchored: { [BasePart]: boolean } = {}
	local enabled: { [Instance]: boolean } = {}
	for _, d in ipairs(model:GetDescendants()) do
		if d:IsA("BasePart") then
			anchored[d] = d.Anchored
		elseif isConstraint(d) then
			enabled[d] = (d :: any).Enabled
		end
	end
	return anchored, enabled
end

local function restore(anchored: { [BasePart]: boolean }, enabled: { [Instance]: boolean })
	for c, v in pairs(enabled) do
		(c :: any).Enabled = v
	end
	for p, v in pairs(anchored) do
		p.Anchored = v
	end
end

function M.Apply(model: Model, which: string?)
	local folder = model:FindFirstChild((which == "Neutral") and "NeutralPose" or "HoldCanPose")
	assert(folder, "pose folder missing")
	local root = model:FindFirstChild("HumanoidRootPart") :: BasePart
	assert(root, "HumanoidRootPart missing")
	local anchored, enabled = snapshot(model)
	local ok, err = pcall(function()
		for p in pairs(anchored) do
			p.Anchored = true
		end
		for c in pairs(enabled) do
			(c :: any).Enabled = false
		end
		local target: { [BasePart]: CFrame } = {}
		for _, v in ipairs(folder:GetChildren()) do
			local partName = string.gsub(v.Name, "_PartCFrame$", "")
			local part = model:FindFirstChild(partName)
			if part and part:IsA("BasePart") and v:IsA("CFrameValue") then
				target[part] = root.CFrame * v.Value
				part.CFrame = target[part]
			end
		end
		-- joint transforms: Part1 attachment frame = Part0 attachment frame * Transform
		for c in pairs(enabled) do
			if c:IsA("AnimationConstraint") then
				local ac = c :: AnimationConstraint
				local p0, p1, a0, a1 = ac.Part0, ac.Part1, ac.Attachment0, ac.Attachment1
				if p0 and p1 and a0 and a1 and target[p0] and target[p1] then
					ac.Transform = a0.CFrame:Inverse() * target[p0]:Inverse() * target[p1] * a1.CFrame
				end
			end
		end
	end)
	restore(anchored, enabled)
	if not ok then
		error(err, 2)
	end
end

function M.QAFreeze(model: Model, on: boolean, which: string?)
	if on then
		if not frozen[model] then
			local anchored, enabled = snapshot(model)
			frozen[model] = { anchored = anchored, enabled = enabled }
			for p in pairs(anchored) do
				p.Anchored = true
			end
			for c in pairs(enabled) do
				(c :: any).Enabled = false
			end
		end
		if which then
			local folder = model:FindFirstChild((which == "Neutral") and "NeutralPose" or "HoldCanPose")
			local root = model:FindFirstChild("HumanoidRootPart") :: BasePart
			assert(folder and root, "pose folder / root missing")
			for _, v in ipairs(folder:GetChildren()) do
				local part = model:FindFirstChild((string.gsub(v.Name, "_PartCFrame$", "")))
				if part and part:IsA("BasePart") and v:IsA("CFrameValue") then
					part.CFrame = root.CFrame * v.Value
				end
			end
		end
	else
		local s = frozen[model]
		if s then
			restore(s.anchored, s.enabled)
			frozen[model] = nil
		end
	end
end

return M
