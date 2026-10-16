--!nocheck
-- RegularDad_Final: reproducible Studio assembly of the final model (HoldMug pose + raised hand).
-- Run in the Studio command bar of a CLEAN place after importing, with Rojo disconnected:
--   1) Import source/RegularDad_R15.fbx  (3D Importer, model name "RegularDad_R15")
--   2) Import source/RegularDad_Mug.fbx  (model name "RegularDad_Mug")
--   3) Run this script. Result: Workspace.RegularDad_R15 identical to model/RegularDad_Final.rbxm
--      (same part CFrames, NeutralPose / HoldMugPose folders, Animations, PoseController, MugGrip).
-- Note: the importer uploads the meshes/texture to the importing account (see README).
local ws = workspace
local m = ws:FindFirstChild("RegularDad_R15")
local wrap = ws:FindFirstChild("RegularDad_Mug")
assert(m and wrap, "import RegularDad_R15.fbx and RegularDad_Mug.fbx first")
assert(not m:FindFirstChild("NeutralPose"), "already assembled")

-- 1. place the model: HumanoidRootPart at (0, 3.05, 0) => soles on Y = 0
m:TranslateBy(Vector3.new(0, 3.0500097274780273, 0) - m.HumanoidRootPart.Position)

-- 2. mug: single MeshPart named "Mug" inside the model, neutral grip position, ONE WeldConstraint to RightHand
local mug = wrap:FindFirstChildWhichIsA("MeshPart", true)
mug.Name = "Mug"
mug.Parent = ws
wrap:Destroy()
mug.CFrame = CFrame.new(1.5275, 1.94, -0.13)
mug.Parent = m

-- 3. freeze rig while placing parts (CFrame writes would drag the whole assembly)
local anchored, enabled = {}, {}
for _, d in ipairs(m:GetDescendants()) do
	if d:IsA("BasePart") then
		anchored[d] = d.Anchored
		d.Anchored = true
	elseif d:IsA("AnimationConstraint") or d:IsA("BallSocketConstraint") or d:IsA("NoCollisionConstraint") then
		enabled[d] = d.Enabled
		d.Enabled = false
	end
end

-- 4. two-bone IK for the raised right arm (logical->Roblox: (X,D,H) -> (-X,H,D))
local S, En, Wn = Vector3.new(1.65, 4.35, 0), Vector3.new(1.90, 3.28, 0), Vector3.new(2.02, 2.30, 0)
local Wt, P = Vector3.new(2.45, 3.81, -1.42), Vector3.new(3.40, 3.20, 0.25)
local L1, L2 = (En - S).Magnitude, (Wn - En).Magnitude
local d = (Wt - S).Magnitude
local e = (Wt - S) / d
local a = (L1 * L1 - L2 * L2 + d * d) / (2 * d)
local h = math.sqrt(L1 * L1 - a * a)
local pe = (P - S) - e * (P - S):Dot(e)
local E = S + e * a + pe.Unit * h
local function arc(u, v)
	u, v = u.Unit, v.Unit
	local ax = u:Cross(v)
	if ax.Magnitude < 1e-6 then
		return CFrame.new()
	end
	return CFrame.fromAxisAngle(ax.Unit, math.acos(math.clamp(u:Dot(v), -1, 1)))
end
local function about(cf, piv, R)
	return CFrame.new(piv) * R * CFrame.new(-piv) * cf
end
local function strip(cf)
	return cf - cf.Position
end
local function frame(v) -- orthonormal frame: Y = bone, X = world X made orthogonal
	v = v.Unit
	local u = (Vector3.xAxis - Vector3.xAxis:Dot(v) * v).Unit
	return CFrame.fromMatrix(Vector3.zero, u, v, u:Cross(v))
end
local Ru = arc(En - S, E - S)
local Rl = frame((Wt - E)) * frame((Wn - En)):Inverse() -- forearm roll aligned with the hand

local joints = { { "RightUpperArm", "RightShoulder" }, { "RightLowerArm", "RightElbow" }, { "RightHand", "RightWrist" } }
local function store(f, n, cf)
	local v = Instance.new("CFrameValue")
	v.Name = n
	v.Value = cf
	v.Parent = f
end

-- 5. neutral pose is stored separately
local nf = Instance.new("Folder")
nf.Name = "NeutralPose"
for _, j in ipairs(joints) do
	store(nf, j[1] .. "_PartCFrame", m[j[1]].CFrame)
	store(nf, j[2] .. "_Attachment1CFrame", m[j[1]][j[2]].Attachment1.CFrame)
end
store(nf, "Mug_PartCFrame", mug.CFrame)
nf.Parent = m

-- 6. HoldMug pose: upper arm, forearm (about the elbow), hand + mug translation
m.RightUpperArm.CFrame = about(m.RightUpperArm.CFrame, S, Ru)
m.RightLowerArm.CFrame = about(m.RightLowerArm.CFrame, En, Rl) + (E - En)
local dv = Wt - Wn
m.RightHand.CFrame = m.RightHand.CFrame + dv
mug.CFrame = mug.CFrame + dv
for _, j in ipairs(joints) do
	local c = m[j[1]][j[2]]
	local a0 = c.Attachment0
	c.Attachment1.CFrame = m[j[1]].CFrame:Inverse() * (a0.Parent.CFrame * a0.CFrame)
end

-- 7. hand raise: hand centre on the forearm axis extension (0.34 up, 0.33 forward), joint world position unchanged
do
	local hand, la = m.RightHand, m.RightLowerArm
	local W = la.RightWristRigAttachment.WorldPosition
	local target = Vector3.new(hand.Position.X, W.Y, W.Z - (hand.Size.Z / 2 - 0.02))
	local dv2 = target - hand.Position
	hand.CFrame = hand.CFrame + dv2
	mug.CFrame = mug.CFrame + dv2
	local c = hand.RightWrist
	local a0 = c.Attachment0
	c.Attachment1.CFrame = hand.CFrame:Inverse() * (a0.Parent.CFrame * a0.CFrame)
	-- Humanoid avatar scaling rebuilds attachment positions from OriginalPosition on spawn: keep it equal
	c.Attachment1.OriginalPosition.Value = c.Attachment1.CFrame.Position
end

-- 8. single mug attachment route: MugGrip WeldConstraint RightHand -> Mug
local weld = Instance.new("WeldConstraint")
weld.Name = "MugGrip"
weld.Part0 = m.RightHand
weld.Part1 = mug
weld.Parent = mug
mug.CanCollide, mug.CanQuery, mug.CanTouch, mug.Massless = false, false, false, true

local pf = Instance.new("Folder")
pf.Name = "HoldMugPose"
for _, j in ipairs(joints) do
	store(pf, j[1] .. "_PartCFrame", m[j[1]].CFrame)
	store(pf, j[2] .. "_Attachment1CFrame", m[j[1]][j[2]].Attachment1.CFrame)
end
store(pf, "Mug_PartCFrame", mug.CFrame)
pf.Parent = m

-- 9. animation data (not published, not played): one-frame KeyframeSequence with the joint rotations
local ks = Instance.new("KeyframeSequence")
ks.Name = "RegularDad_HoldMug_Pose"
ks.Loop = true
ks.Priority = Enum.AnimationPriority.Action
local kf = Instance.new("Keyframe")
kf.Time = 0
kf.Parent = ks
local function pose(n, par, cf)
	local p = Instance.new("Pose")
	p.Name, p.CFrame, p.Weight, p.Parent = n, cf, 1, par
	return p
end
local r = pose("HumanoidRootPart", kf, CFrame.new())
local lt = pose("LowerTorso", r, CFrame.new())
local ut = pose("UpperTorso", lt, CFrame.new())
local p1 = pose("RightUpperArm", ut, strip(Ru))
local p2 = pose("RightLowerArm", p1, strip(Ru:Inverse() * Rl))
pose("RightHand", p2, strip(Rl:Inverse()))
local af = Instance.new("Folder")
af.Name = "Animations"
ks.Parent = af
af.Parent = m

-- 10. unfreeze
for c, v in pairs(enabled) do
	c.Enabled = v
end
for p, v in pairs(anchored) do
	p.Anchored = v
end
mug.Anchored = false
print("RegularDad_Final assembled; now add scripts/PoseController.luau as ModuleScript 'PoseController' inside the model")
