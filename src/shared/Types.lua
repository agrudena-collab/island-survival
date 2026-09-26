-- Luau types shared by server and client modules.
export type PlayerData = {
	Cash: number,
	OwnedDads: { string },
	BaseId: string?,
}

export type PlayerProfile = PlayerData

export type DadDefinition = {
	Id: string,
	DisplayName: string,
	Cost: number,
	IncomePerSecond: number,
}

return {}
