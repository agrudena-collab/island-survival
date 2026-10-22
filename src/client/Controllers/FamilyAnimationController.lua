-- Presentation-only animation for the family NPCs (wife, son): idle breathing, a walk cycle driven by the real
-- horizontal speed, and an optional "Busy" fidget (attribute FamilyActivity on the model: "Cook" or "Fidget").
-- The rig is an R15 AnimationConstraint rig, so the joints are posed through `Transform` on the client; no animation
-- assets are needed. Movement itself stays on the server (Humanoid:MoveTo / pathfinding), this only reads velocity.
-- Models opt in with the CollectionService tag "FamilyNPC". Axis facts (measured): +X swings shoulder/hip/elbow forward,
-- the knee bends towards -X.
local CollectionService = game:GetService("CollectionService")
local RunService = game:GetService("RunService")

local FamilyAnimationController = {}

local TAG = "FamilyNPC"
local STRIDE = 2.6 -- studs covered per half step; phase advances by pi per stride
local MIN_SPEED = 0.6
local BLEND_RATE = 9

local rigs = {} -- [Model] = { joints, phase, blend, time }

local function joint(model, partName, jointName)
	local part = model:FindFirstChild(partName)
	return part and part:FindFirstChild(jointName)
end

local function bind(model)
	if rigs[model] then
		return
	end
	local j = {
		root = joint(model, "LowerTorso", "Root"),
		waist = joint(model, "UpperTorso", "Waist"),
		neck = joint(model, "Head", "Neck"),
		rs = joint(model, "RightUpperArm", "RightShoulder"),
		ls = joint(model, "LeftUpperArm", "LeftShoulder"),
		re = joint(model, "RightLowerArm", "RightElbow"),
		le = joint(model, "LeftLowerArm", "LeftElbow"),
		rh = joint(model, "RightUpperLeg", "RightHip"),
		lh = joint(model, "LeftUpperLeg", "LeftHip"),
		rk = joint(model, "RightLowerLeg", "RightKnee"),
		lk = joint(model, "LeftLowerLeg", "LeftKnee"),
	}
	local hrp = model:FindFirstChild("HumanoidRootPart")
	if not (hrp and j.rh and j.lh and j.rs and j.ls) then
		return
	end
	rigs[model] = { j = j, hrp = hrp, phase = 0, blend = 0, time = math.random() * 10 }
	model.Destroying:Connect(function()
		rigs[model] = nil
	end)
end

local function rx(a)
	return CFrame.Angles(a, 0, 0)
end

local function step(model, rig, dt)
	local j = rig.j
	local v = rig.hrp.AssemblyLinearVelocity
	local speed = Vector3.new(v.X, 0, v.Z).Magnitude
	local walking = speed > MIN_SPEED
	rig.blend += ((walking and 1 or 0) - rig.blend) * math.min(1, dt * BLEND_RATE)
	rig.time += dt
	if walking then
		rig.phase += dt * speed / STRIDE * math.pi
	end
	local b, p = rig.blend, rig.phase
	local s, c = math.sin(p), math.cos(p)
	local carry = model:GetAttribute("CarryRightHand") ~= false -- the right hand holds a prop (ladle / lunchbox): swing it less
	local armR = carry and 0.22 or 0.6
	local activity = model:GetAttribute("FamilyActivity")
	local busy = (not walking) and activity ~= nil and activity ~= ""

	-- legs: opposite phase, the knee bends while the leg swings forward
	j.rh.Transform = rx(0.62 * s * b)
	j.lh.Transform = rx(-0.62 * s * b)
	if j.rk and j.lk then
		j.rk.Transform = rx(-1.0 * math.max(0, c) * b)
		j.lk.Transform = rx(-1.0 * math.max(0, -c) * b)
	end
	-- arms swing against the legs
	local elbowIdle = 0.12
	j.ls.Transform = rx(0.60 * s * b)
	j.rs.Transform = rx(-armR * s * b)
	if j.le and j.re then
		j.le.Transform = rx(elbowIdle + (0.25 + 0.25 * math.max(0, s)) * b)
		j.re.Transform = rx(elbowIdle + (carry and 0.55 or 0.25 + 0.25 * math.max(0, -s)) * b)
	end
	-- body: breathing at rest, bob and counter-twist while walking
	local breath = math.sin(rig.time * 2.0) * 0.025
	if j.root then
		j.root.Transform = CFrame.new(0, math.abs(s) * 0.14 * b, 0) * CFrame.Angles(0, 0.06 * s * b, 0)
	end
	if j.waist then
		j.waist.Transform = CFrame.new(0, breath * (1 - b), 0) * CFrame.Angles(0, -0.10 * s * b, 0)
	end
	if j.neck then
		j.neck.Transform = CFrame.Angles(breath * 0.6 * (1 - b), 0, 0)
	end
	-- activities at the pauses
	if busy and activity == "Cook" then
		-- stirring: the right forearm rises and circles
		j.rs.Transform = rx(0.55)
		j.re.Transform = rx(1.1 + 0.18 * math.sin(rig.time * 4.5)) * CFrame.Angles(0, 0, 0.12 * math.cos(rig.time * 4.5))
	elseif busy and activity == "Fidget" then
		-- shifts weight and swings the lunchbox
		j.rs.Transform = rx(0.25 * math.sin(rig.time * 1.6))
		j.rh.Transform = rx(0.06 * math.sin(rig.time * 0.9))
		j.lh.Transform = rx(-0.06 * math.sin(rig.time * 0.9))
	end
end

function FamilyAnimationController.Initialize()
	for _, model in ipairs(CollectionService:GetTagged(TAG)) do
		bind(model)
	end
	CollectionService:GetInstanceAddedSignal(TAG):Connect(function(model)
		task.defer(bind, model)
	end)
	RunService.Heartbeat:Connect(function(dt)
		for model, rig in pairs(rigs) do
			if model.Parent then
				step(model, rig, dt)
			end
		end
	end)
end

return FamilyAnimationController
