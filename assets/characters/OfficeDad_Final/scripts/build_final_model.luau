--!nocheck
-- OfficeDad_Final: reproducible Studio assembly of the final static model (fixed pose + BriefcaseGrip).
-- Run in the Studio command bar of a CLEAN place with Rojo disconnected:
--   1) Import source/OfficeDad_R15.fbx      (3D Importer, model name "OfficeDad_R15")
--   2) Import source/OfficeDad_Briefcase.fbx (model name "OfficeDad_Briefcase")
--   3) Run this script. Result matches model/OfficeDad_Final.rbxm (Workspace.OfficeDad_R15).
-- Note: the importer uploads meshes/texture to the importing account (see README_RU.md).
local ws = workspace
local m = ws:FindFirstChild("OfficeDad_R15")
local wrap = ws:FindFirstChild("OfficeDad_Briefcase")
assert(m and wrap, "import both FBX first")
assert(not m:FindFirstChild("NeutralPose"), "already assembled")

-- 1. placement: Head center Y=5.35, UpperTorso X=0, Head Z=-0.175 (soles on Y=0)
local head, ut = m.Head, m.UpperTorso
m:TranslateBy(Vector3.new(-ut.Position.X, 5.35 - head.Position.Y, -0.175 - head.Position.Z))

-- 2. briefcase: one MeshPart "Briefcase" inside the model, ONE WeldConstraint BriefcaseGrip RightHand -> Briefcase
local case = wrap:FindFirstChildWhichIsA("MeshPart", true)
case.Name = "Briefcase"
case.Parent = ws
wrap:Destroy()
case.CFrame = CFrame.new(2.2, 1.0375, -0.2655)
case.Parent = m
for _, p in ipairs(m:GetDescendants()) do
	if p:IsA("BasePart") then
		p.Anchored = false
	end
end
case.CanCollide, case.CanQuery, case.CanTouch, case.Massless = false, false, false, true
local grip = Instance.new("WeldConstraint")
grip.Name = "BriefcaseGrip"
grip.Part0, grip.Part1 = m.RightHand, case
grip.Parent = case

-- 3. NeutralPose = part CFrames relative to HumanoidRootPart (restore data used by PoseController)
local hrp = m.HumanoidRootPart
local folder = Instance.new("Folder")
folder.Name = "NeutralPose"
for _, p in ipairs(m:GetChildren()) do
	if p:IsA("BasePart") then
		local v = Instance.new("CFrameValue")
		v.Name = p.Name .. "_PartCFrame"
		v.Value = hrp.CFrame:ToObjectSpace(p.CFrame)
		v.Parent = folder
	end
end
folder.Parent = m
print("OfficeDad_Final assembled; add scripts/PoseController.luau as ModuleScript 'PoseController' if needed")
