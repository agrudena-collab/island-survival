-- Grill Mistress District + MistressFlat4: soften glare on white surfaces, keep lamps (Neon) glowing (same rule as the Grill Dad district:
-- Bloom only on Neon lamps, soft interior light). Run in the command bar after the district (and, if present, the flat) are set up.
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
-- tone down pure-white / pale materials (meshes are named Group_Material_cx_cy_nn)
local soft = {
	White = Color3.fromRGB(226, 220, 208), Tile = Color3.fromRGB(176, 180, 182), TileB = Color3.fromRGB(96, 168, 212),
	ClothWhite = Color3.fromRGB(224, 220, 210), TileW = Color3.fromRGB(232, 228, 220), Ceiling = Color3.fromRGB(236, 230, 220),
}
local model = workspace:FindFirstChild("GrillMistressDistrict")
assert(model, "Workspace.GrillMistressDistrict not found")
local flat = model:FindFirstChild("MistressBuilding4")
local interior = flat and flat:FindFirstChild("Interior")
local nParts, nLights = 0, 0
for _, d in ipairs(model:GetDescendants()) do
	if d:IsA("MeshPart") then
		local mat = string.match(d.Name, "^[^_]+_([^_]+)_")
		local c = mat and soft[mat]
		if c then d.Color = c; if d.Material == Enum.Material.SmoothPlastic then d.Material = Enum.Material.Plastic end; nParts += 1 end
		if d.Material == Enum.Material.SmoothPlastic then d.Reflectance = 0 end
	elseif (d:IsA("PointLight") or d:IsA("SpotLight")) and interior and d:IsDescendantOf(interior) then
		d.Brightness = math.min(d.Brightness, 0.6); d.Range = math.min(d.Range, 18); nLights += 1
	end
end
print("lighting_soft: parts", nParts, "flat interior lights", nLights)
