-- Grill Dad: soften glare on white surfaces, keep lamps (Neon) glowing.
local Lighting = game:GetService("Lighting")
local bloom = Lighting:FindFirstChildOfClass("BloomEffect") or Instance.new("BloomEffect")
bloom.Parent = Lighting
bloom.Intensity = 0.25; bloom.Size = 16; bloom.Threshold = 1.4  -- only Neon (emissive > 1) blooms
for _, cc in ipairs(Lighting:GetChildren()) do
	if cc:IsA("ColorCorrectionEffect") then cc.Brightness = math.min(cc.Brightness, 0) end
end
Lighting.ExposureCompensation = -0.25
Lighting.EnvironmentSpecularScale = 0.25
Lighting.EnvironmentDiffuseScale = 0.6
-- tone down pure-white / pale materials (named Group_Material_cx_cy_nn)
local soft = {
	White = Color3.fromRGB(226, 220, 208), Tile = Color3.fromRGB(176, 180, 182), TileB = Color3.fromRGB(96, 168, 212),
	ClothWhite = Color3.fromRGB(224, 220, 210),
}
local model = workspace:FindFirstChild("GrillDadDistrict")
local nParts, nLights = 0, 0
for _, d in ipairs(model:GetDescendants()) do
	if d:IsA("MeshPart") then
		local mat = string.match(d.Name, "^[^_]+_([^_]+)_")
		local c = mat and soft[mat]
		if c then d.Color = c; d.Material = Enum.Material.Plastic; nParts += 1 end
		if d.Material == Enum.Material.SmoothPlastic then d.Reflectance = 0 end
	elseif d:IsA("PointLight") or d:IsA("SpotLight") then
		local p = d.Parent
		local pos = p and p:IsA("BasePart") and p.Position
		-- keep (house) interior: X in [-282,-218], Z in [414,452], Y < 30
		if pos and pos.X > -282 and pos.X < -218 and pos.Z > 414 and pos.Z < 452 and pos.Y < 30 then
			d.Brightness = math.min(d.Brightness, 0.3); d.Range = math.min(d.Range, 12); nLights += 1
		end
	end
end
print("lighting_soft: parts", nParts, "interior lights", nLights)
