local Controllers = script.Parent:WaitForChild("Controllers")

local controllerNames = {
	"UIController",
	"PromptController",
	"CameraController",
	"FamilyAnimationController",
	"FamilyAlertController",
	"CrouchController",
	"HeistNotebookController",
	"TreadmillController",
	"DialogueController",
}

for _, controllerName in ipairs(controllerNames) do
	local controller = require(Controllers:WaitForChild(controllerName))
	if type(controller) == "table" and type(controller.Initialize) == "function" then
		controller.Initialize()
	end
end
