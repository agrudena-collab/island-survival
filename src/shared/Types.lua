-- Luau types shared by server and client modules.
export type PlayerData = {
	Cash: number,
	OwnedDads: { string },
	BaseId: string?,
}

export type PlayerProfile = PlayerData

export type DadRarity = "Common" | "Uncommon" | "Rare" | "Epic" | "Legendary"

export type DadColorTheme = {
	Skin: BrickColor,
	Shirt: BrickColor,
	Pants: BrickColor,
	Accent: BrickColor,
}

export type DadAccessory = {
	Name: string,
	Color: BrickColor,
	Shape: "Block" | "Cylinder",
	Size: Vector3,
}

export type DadHeadwear = {
	Kind: "Cap" | "Brim" | "Band" | "Crown",
	Color: BrickColor,
	AccentColor: BrickColor?,
	CrownHeight: number?,
	BrimRadius: number?,
}

export type DadTorsoDetail = {
	Kind: "Tie" | "Apron" | "Stripe" | "Chain",
	Color: BrickColor,
}

export type DadDefinition = {
	Id: string,
	DisplayName: string,
	Rarity: DadRarity,
	Cost: number,
	IncomePerSecond: number,
	ColorTheme: DadColorTheme,
	Accessory: DadAccessory?,
	Headwear: DadHeadwear?,
	TorsoDetail: DadTorsoDetail?,
	AccentMaterial: Enum.Material,
	-- Name of a finished Model in ServerStorage (mapped by Rojo). When set, the dad is that model instead of DadBaseRig + overlays.
	ModelAsset: string?,
}

return {}
