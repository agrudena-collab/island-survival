local Workspace = game:GetService("Workspace")

local DadModelBuilder = require(script.Parent.Parent:WaitForChild("DadModelBuilder"))

local DadService = {}

-- TEMPORARY: spawns all 8 catalog dads in a visible row for art review.
-- Remove this preview once BaseService (M3) provides real Dad slots to spawn into.
function DadService.Initialize()
	local preview = Workspace:FindFirstChild("DadPreview") or Instance.new("Folder")
	preview.Name = "DadPreview"
	preview.Parent = Workspace
	preview:ClearAllChildren()

	DadModelBuilder.BuildAll(preview)
end

return DadService
