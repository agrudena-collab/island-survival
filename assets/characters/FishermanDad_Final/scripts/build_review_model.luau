--!nocheck
-- FishermanDad_Redesign: reproducible Studio assembly of the review model (static HoldRod pose, rod + bucket props).
-- Run in the Studio command bar of a CLEAN place with Rojo disconnected, after importing three FBX files with
-- "Upload to Roblox" unchecked (3D Importer, "Import Only as a Model" on):
--   export/FishermanDad_R15.fbx    -> model name "FishermanDad_R15"
--   export/FishermanDad_Rod.fbx    -> model name "FishermanDad_Rod"
--   export/FishermanDad_Bucket.fbx -> model name "FishermanDad_Bucket"
-- Result: Workspace.FishermanDad_R15 with FishingRod (RodGrip -> LeftHand), Bucket (BucketMount -> HumanoidRootPart),
-- HoldRodPose folder and PoseController. Logical (X,D,H) -> Roblox position (-X, H, D).
local ws = workspace
local m = ws:FindFirstChild("FishermanDad_R15")
local rodWrap = ws:FindFirstChild("FishermanDad_Rod")
local bucketWrap = ws:FindFirstChild("FishermanDad_Bucket")
assert(m and rodWrap and bucketWrap, "import the three FBX files first")
assert(not m:FindFirstChild("HoldRodPose"), "already assembled")

-- 1. placement: UpperTorso X = 0, HumanoidRootPart Z = 0, soles on Y = 0 (HRP ends at Y 2.92 like the first two dads)
local lowest = math.huge
for _, p in ipairs(m:GetChildren()) do
	if p:IsA("BasePart") and p.Name ~= "HumanoidRootPart" then
		lowest = math.min(lowest, p.Position.Y - p.Size.Y / 2)
	end
end
m:TranslateBy(Vector3.new(-m.UpperTorso.Position.X, -lowest, -m.HumanoidRootPart.Position.Z))

-- 2. props: one MeshPart each, centred on the logical bbox centre of the exported mesh (see data/_build_result.json)
local function takeMesh(wrap, name, cf)
	local mp = wrap:FindFirstChildWhichIsA("MeshPart", true)
	mp.Name = name
	mp.Parent = ws
	wrap:Destroy()
	mp.CFrame = cf
	mp.Parent = m
	mp.Anchored = false
	mp.CanCollide = false
	mp.CanQuery = false
	mp.CanTouch = false
	mp.Massless = true
	return mp
end
-- rod bbox (logical) min (2.105,-.945,.10) max (3.227,-.41,7.353) -> centre (2.666,-.6775,3.7265)
local rod = takeMesh(rodWrap, "FishingRod", CFrame.new(-2.666, 3.7265, -0.6775))
-- bucket bbox (logical) min (2.39,-.496,0) max (3.61,.68,1.16) -> centre (3.0,.092,.58)
local bucket = takeMesh(bucketWrap, "Bucket", CFrame.new(-3.0, 0.58, 0.092))

local grip = Instance.new("WeldConstraint")
grip.Name = "RodGrip"
grip.Part0, grip.Part1 = m.LeftHand, rod
grip.Parent = rod
local mount = Instance.new("WeldConstraint")
mount.Name = "BucketMount"
mount.Part0, mount.Part1 = m.HumanoidRootPart, bucket
mount.Parent = bucket

-- 3. HoldRodPose = every part CFrame relative to HumanoidRootPart (restore data for PoseController)
local hrp = m.HumanoidRootPart
local folder = Instance.new("Folder")
folder.Name = "HoldRodPose"
for _, p in ipairs(m:GetChildren()) do
	if p:IsA("BasePart") then
		local v = Instance.new("CFrameValue")
		v.Name = p.Name .. "_PartCFrame"
		v.Value = hrp.CFrame:ToObjectSpace(p.CFrame)
		v.Parent = folder
	end
end
folder.Parent = m
print("FishermanDad assembled; add scripts/PoseController.luau as ModuleScript 'PoseController' (optional)")
