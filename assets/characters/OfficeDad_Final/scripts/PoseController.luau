--!strict
-- OfficeDad PoseController (also inside the model): restores the stored default pose (holding the briefcase).
-- NeutralPose stores every part CFrame relative to HumanoidRootPart.
local M = {}
function M.Apply(model: Model, which: string?)
	local folder = model:FindFirstChild("NeutralPose")
	assert(folder, "NeutralPose folder missing")
	local root = model:FindFirstChild("HumanoidRootPart") :: BasePart
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
	for _, v in ipairs(folder:GetChildren()) do
		local partName = string.gsub(v.Name, "_PartCFrame$", "")
		local part = model:FindFirstChild(partName)
		if part and part:IsA("BasePart") and v:IsA("CFrameValue") then
			part.CFrame = root.CFrame * v.Value
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
