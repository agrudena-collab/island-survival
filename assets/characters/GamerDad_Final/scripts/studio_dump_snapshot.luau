--!nocheck
-- Dumps the assembled GamerDad_R15 (or a QA copy) as JSON lines "GDSNAP|<stage>|{...}" into the Output (command bar, Edit mode).
-- usage: set STAGE / TARGET below, run in the command bar, copy the Output (ctrl+a, ctrl+c) and parse with parse_studio_output.py
local STAGE = "assembled_HoldCan"
local TARGET = "GamerDad_R15"
local HS = game:GetService("HttpService")
local m = workspace:FindFirstChild(TARGET)
assert(m, "model not found: " .. TARGET)
local function v3(v)
	return { v.X, v.Y, v.Z }
end
local function cf(c)
	return { c:GetComponents() }
end
local hrp = m:FindFirstChild("HumanoidRootPart")
local function emit(kind, t)
	print("GDSNAP|" .. STAGE .. "|" .. kind .. "|" .. HS:JSONEncode(t))
end
local hum = m:FindFirstChildOfClass("Humanoid")
emit("model", { name = m.Name, children = #m:GetChildren(), hipHeight = hum and hum.HipHeight, rigType = hum and tostring(hum.RigType), hrp = hrp and { size = v3(hrp.Size), cf = cf(hrp.CFrame) } })
for _, p in ipairs(m:GetDescendants()) do
	if p:IsA("BasePart") then
		local t = { name = p.Name, class = p.ClassName, parent = p.Parent.Name, size = v3(p.Size), cf = cf(p.CFrame), anchored = p.Anchored, cancollide = p.CanCollide, canquery = p.CanQuery, cantouch = p.CanTouch,
			massless = p.Massless, color = { p.Color.R, p.Color.G, p.Color.B }, transparency = p.Transparency }
		if p:IsA("MeshPart") then
			t.meshId = p.MeshId
			t.textureId = p.TextureID
			t.meshSize = v3(p.MeshSize)
			t.doubleSided = p.DoubleSided
			local sa = p:FindFirstChildOfClass("SurfaceAppearance")
			t.surfaceAppearance = sa and { colorMap = sa.ColorMap } or nil
		end
		emit("part", t)
	elseif p:IsA("Attachment") then
		local t = { name = p.Name, parent = p.Parent.Name, position = v3(p.Position), world = v3(p.WorldPosition) }
		local op = p:FindFirstChild("OriginalPosition")
		if op and op:IsA("Vector3Value") then
			t.originalPosition = v3(op.Value)
		end
		emit("attachment", t)
	elseif p:IsA("JointInstance") or p:IsA("AnimationConstraint") or p:IsA("BallSocketConstraint") or p:IsA("WeldConstraint") or p:IsA("NoCollisionConstraint") then
		local t = { name = p.Name, class = p.ClassName, parent = p.Parent.Name }
		pcall(function()
			t.enabled = p.Enabled
		end)
		pcall(function()
			t.part0 = p.Part0 and p.Part0.Name
			t.part1 = p.Part1 and p.Part1.Name
		end)
		pcall(function()
			t.att0 = p.Attachment0 and p.Attachment0.Name
			t.att1 = p.Attachment1 and p.Attachment1.Name
			t.gap = (p.Attachment0.WorldPosition - p.Attachment1.WorldPosition).Magnitude
		end)
		emit("joint", t)
	elseif p:IsA("Folder") or p:IsA("ModuleScript") or p:IsA("Humanoid") then
		emit("other", { name = p.Name, class = p.ClassName, parent = p.Parent.Name, children = #p:GetChildren() })
	end
end
print("GDSNAP_DONE|" .. STAGE)
