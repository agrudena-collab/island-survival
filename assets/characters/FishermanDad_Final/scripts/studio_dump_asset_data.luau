-- Prints one machine-readable line per part (DATA|...) for data/pose_and_asset_data.json. Run in Edit mode.
local m = workspace:FindFirstChild("FishermanDad_R15") or workspace:FindFirstChild("FishermanDad_Review") or game.ServerStorage:FindFirstChild("FishermanDad_R15") or game.ServerStorage:FindFirstChild("FishermanDadFinal")
local hrp = m.HumanoidRootPart
local function f(n)
	return string.format("%.4f", n)
end
for _, p in ipairs(m:GetChildren()) do
	if p:IsA("BasePart") then
		local s = p:FindFirstChildOfClass("SurfaceAppearance")
		local mesh = p:IsA("MeshPart") and tostring(p.MeshId) or ""
		print("DATA|" .. p.Name .. "|" .. mesh .. "|" .. f(p.Size.X) .. "," .. f(p.Size.Y) .. "," .. f(p.Size.Z) .. "|" .. f(p.Position.X) .. "," .. f(p.Position.Y) .. "," .. f(p.Position.Z)
			.. "|" .. (p:IsA("MeshPart") and tostring(p.TextureID) or "") .. "|" .. (s and tostring(s.ColorMap) or "") .. "|" .. f(p.Color.R) .. "," .. f(p.Color.G) .. "," .. f(p.Color.B))
	end
end
for _, c in ipairs(m:GetDescendants()) do
	if c:IsA("AnimationConstraint") then
		print("JOINT|" .. c.Parent.Name .. "|" .. c.Name .. "|" .. tostring(c.Attachment0.Parent.Name) .. "->" .. tostring(c.Attachment1.Parent.Name) .. "|A0=" .. tostring(c.Attachment0.CFrame.Position) .. "|A1=" .. tostring(c.Attachment1.CFrame.Position))
	end
end
