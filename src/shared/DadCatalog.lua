-- Data for the 8 collectible dads. Native Roblox parts only (no external meshes).
-- Cost/IncomePerSecond are placeholder balance numbers for M4; tune during M5.
local Types = require(script.Parent:WaitForChild("Types"))

type DadDefinition = Types.DadDefinition

local DadCatalog: { DadDefinition } = {
	{
		Id = "RegularDad",
		-- Final approved art: ServerStorage.RegularDadFinal (assets/characters/RegularDad_Final). The overlay fields below are unused for it.
		ModelAsset = "RegularDadFinal",
		DisplayName = "Regular Dad",
		Rarity = "Common",
		Cost = 50,
		IncomePerSecond = 1,
		ColorTheme = {
			Skin = BrickColor.new("Light orange"),
			Shirt = BrickColor.new("Steel blue"),
			Pants = BrickColor.new("Dark stone grey"),
			Accent = BrickColor.new("Medium stone grey"),
		},
		Accessory = { Name = "Mug", Color = BrickColor.new("White"), Shape = "Cylinder", Size = Vector3.new(0.6, 0.8, 0.6) },
		Headwear = { Kind = "Cap", Color = BrickColor.new("Steel blue"), AccentColor = BrickColor.new("Medium stone grey") },
		AccentMaterial = Enum.Material.Plastic,
	},
	{
		Id = "OfficeDad",
		-- Final approved art: ServerStorage.OfficeDadFinal (assets/characters/OfficeDad_Final). The overlay fields below are unused for it.
		ModelAsset = "OfficeDadFinal",
		DisplayName = "Office Dad",
		Rarity = "Common",
		Cost = 75,
		IncomePerSecond = 1.5,
		ColorTheme = {
			Skin = BrickColor.new("Light orange"),
			Shirt = BrickColor.new("Institutional white"),
			Pants = BrickColor.new("Black"),
			Accent = BrickColor.new("Really red"),
		},
		Accessory = { Name = "Briefcase", Color = BrickColor.new("Reddish brown"), Shape = "Block", Size = Vector3.new(1.2, 1, 0.4) },
		Headwear = { Kind = "Brim", Color = BrickColor.new("Black"), AccentColor = BrickColor.new("Really red"), CrownHeight = 0.6, BrimRadius = 1.25 },
		TorsoDetail = { Kind = "Tie", Color = BrickColor.new("Really red") },
		AccentMaterial = Enum.Material.Plastic,
	},
	{
		Id = "GardenerDad",
		-- Third dad slot (Uncommon). Id is kept because saved OwnedDads reference it; the final art is Fisherman Dad (ServerStorage.FishermanDadFinal, assets/characters/FishermanDad_Final).
		ModelAsset = "FishermanDadFinal",
		DisplayName = "Fisherman Dad",
		Rarity = "Uncommon",
		Cost = 150,
		IncomePerSecond = 3,
		ColorTheme = {
			Skin = BrickColor.new("Light orange"),
			Shirt = BrickColor.new("Earth green"),
			Pants = BrickColor.new("Reddish brown"),
			Accent = BrickColor.new("Bright green"),
		},
		Accessory = { Name = "Shovel", Color = BrickColor.new("Dark stone grey"), Shape = "Block", Size = Vector3.new(0.3, 2, 0.3) },
		Headwear = { Kind = "Brim", Color = BrickColor.new("Bright yellow"), AccentColor = BrickColor.new("Earth green"), CrownHeight = 0.4, BrimRadius = 1.6 },
		TorsoDetail = { Kind = "Apron", Color = BrickColor.new("Reddish brown") },
		AccentMaterial = Enum.Material.Plastic,
	},
	{
		Id = "GrillDad",
		-- Final approved art: ServerStorage.GrillDadFinal (assets/characters/GrillDad_Final). The overlay fields below are unused for it.
		ModelAsset = "GrillDadFinal",
		DisplayName = "Grill Dad",
		Rarity = "Uncommon",
		Cost = 220,
		IncomePerSecond = 4,
		ColorTheme = {
			Skin = BrickColor.new("Light orange"),
			Shirt = BrickColor.new("Bright yellow"),
			Pants = BrickColor.new("Dark stone grey"),
			Accent = BrickColor.new("Really red"),
		},
		Accessory = { Name = "BBQTongs", Color = BrickColor.new("Really black"), Shape = "Block", Size = Vector3.new(0.3, 1.4, 0.2) },
		Headwear = { Kind = "Brim", Color = BrickColor.new("White"), AccentColor = BrickColor.new("White"), CrownHeight = 1.1, BrimRadius = 1.1 },
		TorsoDetail = { Kind = "Apron", Color = BrickColor.new("Really red") },
		AccentMaterial = Enum.Material.Plastic,
	},
	{
		Id = "GamerDad",
		-- Final approved art: ServerStorage.GamerDadFinal (assets/characters/GamerDad_Final). The overlay fields below are unused for it.
		ModelAsset = "GamerDadFinal",
		DisplayName = "Gamer Dad",
		Rarity = "Rare",
		Cost = 400,
		IncomePerSecond = 7,
		ColorTheme = {
			Skin = BrickColor.new("Light orange"),
			Shirt = BrickColor.new("Royal purple"),
			Pants = BrickColor.new("Black"),
			Accent = BrickColor.new("Cyan"),
		},
		Accessory = { Name = "EnergyDrink", Color = BrickColor.new("Bright green"), Shape = "Cylinder", Size = Vector3.new(0.5, 0.9, 0.5) },
		Headwear = { Kind = "Cap", Color = BrickColor.new("Royal purple"), AccentColor = BrickColor.new("Cyan") },
		TorsoDetail = { Kind = "Stripe", Color = BrickColor.new("Cyan") },
		AccentMaterial = Enum.Material.SmoothPlastic,
	},
	{
		Id = "GymDad",
		-- Final approved art: ServerStorage.GymDadFinal (assets/characters/GymDad_Final). The overlay fields below are unused for it.
		ModelAsset = "GymDadFinal",
		DisplayName = "Gym Dad",
		Rarity = "Rare",
		Cost = 550,
		IncomePerSecond = 9,
		ColorTheme = {
			Skin = BrickColor.new("Light orange"),
			Shirt = BrickColor.new("Really blue"),
			Pants = BrickColor.new("Black"),
			Accent = BrickColor.new("White"),
		},
		Accessory = { Name = "Dumbbell", Color = BrickColor.new("Dark stone grey"), Shape = "Block", Size = Vector3.new(1.4, 0.4, 0.4) },
		Headwear = { Kind = "Band", Color = BrickColor.new("White"), AccentColor = BrickColor.new("Really blue") },
		TorsoDetail = { Kind = "Stripe", Color = BrickColor.new("White") },
		AccentMaterial = Enum.Material.SmoothPlastic,
	},
	{
		Id = "BusinessDad",
		-- Final approved art: ServerStorage.BusinessDadFinal (assets/characters/BusinessDad_Final). The overlay fields below are unused for it.
		ModelAsset = "BusinessDadFinal",
		DisplayName = "Business Dad",
		Rarity = "Epic",
		Cost = 900,
		IncomePerSecond = 15,
		ColorTheme = {
			Skin = BrickColor.new("Light orange"),
			Shirt = BrickColor.new("Really black"),
			Pants = BrickColor.new("Black"),
			Accent = BrickColor.new("Gold"),
		},
		Accessory = { Name = "Phone", Color = BrickColor.new("Really black"), Shape = "Block", Size = Vector3.new(0.3, 0.6, 0.1) },
		Headwear = { Kind = "Brim", Color = BrickColor.new("Really black"), AccentColor = BrickColor.new("Gold"), CrownHeight = 1.3, BrimRadius = 1.2 },
		TorsoDetail = { Kind = "Tie", Color = BrickColor.new("Gold") },
		AccentMaterial = Enum.Material.Neon,
	},
	{
		Id = "MillionaireDad",
		-- Final approved art: ServerStorage.MillionaireDadFinal (assets/characters/MillionaireDad_Final). The overlay fields below are unused for it.
		ModelAsset = "MillionaireDadFinal",
		DisplayName = "Millionaire Dad",
		Rarity = "Legendary",
		Cost = 1500,
		IncomePerSecond = 25,
		ColorTheme = {
			Skin = BrickColor.new("Light orange"),
			Shirt = BrickColor.new("Gold"),
			Pants = BrickColor.new("Gold"),
			Accent = BrickColor.new("New Yeller"),
		},
		Accessory = { Name = "GoldCase", Color = BrickColor.new("Gold"), Shape = "Block", Size = Vector3.new(1.2, 0.9, 0.5) },
		Headwear = { Kind = "Crown", Color = BrickColor.new("Gold"), AccentColor = BrickColor.new("New Yeller") },
		TorsoDetail = { Kind = "Chain", Color = BrickColor.new("Gold") },
		AccentMaterial = Enum.Material.Neon,
	},
}

local ById: { [string]: DadDefinition } = {}
for _, definition in ipairs(DadCatalog) do
	ById[definition.Id] = definition
end

return {
	List = DadCatalog,
	GetById = function(id: string): DadDefinition?
		return ById[id]
	end,
}
