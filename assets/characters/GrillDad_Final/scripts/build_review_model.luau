--!nocheck
-- GrillDad_Redesign: reproducible Studio assembly of the review model (static HoldTongs pose, GrillTongs prop).
-- Run in the Studio command bar of a CLEAN place with Rojo disconnected, after importing two FBX files with
-- "Upload to Roblox" unchecked (3D Importer, "Import Only as a Model" on):
--   export/GrillDad_R15.fbx    -> model name "GrillDad_R15"
--   export/GrillDad_Tongs.fbx  -> model name "GrillDad_Tongs"
-- Result: Workspace.GrillDad_R15 with GrillTongs (TongsGrip -> LeftHand), HoldTongsPose folder and (optional) PoseController.
-- Logical (X,D,H) -> Roblox position (-X, H, D).
local ws = workspace
local m = ws:FindFirstChild("GrillDad_R15")
local wrap = ws:FindFirstChild("GrillDad_Tongs")
assert(m and wrap, "import both FBX files first")
assert(not m:FindFirstChild("HoldTongsPose"), "already assembled")

-- 1. placement: UpperTorso X = 0, HumanoidRootPart Z = 0, soles on Y = 0
local lowest = math.huge
for _, p in ipairs(m:GetChildren()) do
	if p:IsA("BasePart") and p.Name ~= "HumanoidRootPart" then
		lowest = math.min(lowest, p.Position.Y - p.Size.Y / 2)
	end
end
m:TranslateBy(Vector3.new(-m.UpperTorso.Position.X, -lowest, -m.HumanoidRootPart.Position.Z))

-- 2. prop: one MeshPart, centred on the logical bbox centre of the exported mesh (data/_build_result.json):
-- tongs bbox (logical) min (1.823,-.71,2.50) max (2.777,-.53,5.92) -> centre (2.30,-.62,4.21)
local tongs = wrap:FindFirstChildWhichIsA("MeshPart", true)
tongs.Name = "GrillTongs"
tongs.Parent = ws
wrap:Destroy()
tongs.CFrame = CFrame.new(-2.30, 4.21, -0.62)
tongs.Parent = m
tongs.Anchored = false
tongs.CanCollide = false
tongs.CanQuery = false
tongs.CanTouch = false
tongs.Massless = true
local grip = Instance.new("WeldConstraint")
grip.Name = "TongsGrip"
grip.Part0, grip.Part1 = m.LeftHand, tongs
grip.Parent = tongs

-- 3. HoldTongsPose = every part CFrame relative to HumanoidRootPart (restore data for PoseController)
local hrp = m.HumanoidRootPart
local folder = Instance.new("Folder")
folder.Name = "HoldTongsPose"
for _, p in ipairs(m:GetChildren()) do
	if p:IsA("BasePart") then
		local v = Instance.new("CFrameValue")
		v.Name = p.Name .. "_PartCFrame"
		v.Value = hrp.CFrame:ToObjectSpace(p.CFrame)
		v.Parent = folder
	end
end
folder.Parent = m
print("GrillDad assembled; add scripts/PoseController.luau as ModuleScript 'PoseController' (optional)")
