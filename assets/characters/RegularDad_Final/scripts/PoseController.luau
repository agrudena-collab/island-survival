--!strict
-- RegularDad PoseController (ModuleScript inside the RegularDad_R15 model).
-- The model ships in the HoldMug pose by default (parts + RigAttachment CFrames of the right arm chain are baked).
-- This module switches between the two stored poses without touching the mesh data or the MugGrip weld:
--   NeutralPose  : original importer rest pose (separate copy, never edited)
--   HoldMugPose  : right arm bent and raised, mug upright in front of the chest
-- Usage:  require(model.PoseController).Apply(model, "Neutral")  /  .Apply(model, "HoldMug")
local M = {}

-- HumanoidRootPart world CFrame at the moment the poses were captured (model at the origin)
local HRP0 = CFrame.new(0, 3.0500097274780273, 0)
local JOINTS = {
	{ "RightUpperArm", "RightShoulder" },
	{ "RightLowerArm", "RightElbow" },
	{ "RightHand", "RightWrist" },
}

function M.Apply(model: Model, which: string)
	local folder = model:FindFirstChild(which == "Neutral" and "NeutralPose" or "HoldMugPose")
	assert(folder, "pose folder missing: " .. which)
	local root = model:FindFirstChild("HumanoidRootPart") :: BasePart
	local toWorld = root.CFrame * HRP0:Inverse()

	-- freeze the rig while we place parts (setting a CFrame would otherwise drag the whole assembly)
	local anchored: { [BasePart]: boolean } = {}
	local enabled: { [Instance]: boolean } = {}
	for _, d in ipairs(model:GetDescendants()) do
		if d:IsA("BasePart") then
			anchored[d] = d.Anchored
			d.Anchored = true
		elseif d:IsA("AnimationConstraint") or d:IsA("BallSocketConstraint") or d:IsA("NoCollisionConstraint") then
			enabled[d] = d.Enabled
			d.Enabled = false
		end
	end

	local mug = model:FindFirstChild("Mug") :: BasePart?
	for _, j in ipairs(JOINTS) do
		local part = model[j[1]] :: BasePart
		local pc = folder:FindFirstChild(j[1] .. "_PartCFrame") :: CFrameValue
		part.CFrame = toWorld * pc.Value
	end
	if mug then
		local mc = folder:FindFirstChild("Mug_PartCFrame") :: CFrameValue?
		if mc then
			mug.CFrame = toWorld * mc.Value
		end
	end
	for _, j in ipairs(JOINTS) do
		local c = (model[j[1]] :: BasePart):FindFirstChild(j[2]) :: AnimationConstraint
		local av = folder:FindFirstChild(j[2] .. "_Attachment1CFrame") :: CFrameValue
		c.Attachment1.CFrame = av.Value
		-- the R15 avatar scaling system rebuilds attachment positions from OriginalPosition: keep it in sync
		local op = c.Attachment1:FindFirstChild("OriginalPosition")
		if op and op:IsA("Vector3Value") then
			op.Value = av.Value.Position
		end
	end

	for c, v in pairs(enabled) do
		(c :: any).Enabled = v
	end
	for p, v in pairs(anchored) do
		p.Anchored = v
	end
end

return M
