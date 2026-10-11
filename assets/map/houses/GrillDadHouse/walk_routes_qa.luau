-- GrillDadHouse QA: continuous controlled-avatar walk (run in Studio PLAY, client command bar).
-- Model pivot (logical (0,24,0)) is placed at the Workspace origin, so logical (X, D, H)
-- maps to Roblox (-X, H, D - 24).  Humanoid:MoveTo drives the real character controller:
-- no teleports between legs, no jumping.  The only placement is the initial spawn point.
local Players = game:GetService("Players")
local RS = game:GetService("RunService")
local plr = Players.LocalPlayer
local char = plr.Character or plr.CharacterAdded:Wait()
local hum: Humanoid = char:WaitForChild("Humanoid")
local hrp: BasePart = char:WaitForChild("HumanoidRootPart")

local function R(X: number, D: number): Vector3
	return Vector3.new(-X, 0, D - 24)
end

-- Make jumping impossible: a PASS therefore proves the routes need no jumping.
hum.AutoJumpEnabled = false
hum.UseJumpPower = true
hum.JumpPower = 0
hum.WalkSpeed = 16
local minY, maxY = math.huge, -math.huge

local startPos = R(0, 1.5)
char:PivotTo(CFrame.new(startPos.X, 5, startPos.Z))
task.wait(1.5)

local legs = {
	{ "front approach -> door", 0, 5.2 },
	{ "door -> interior lane middle", 0, 15 },
	{ "lane -> Dad pad (8.5,25.5)", 8.5, 25.5 },
	{ "Dad pad -> lane rear", 0, 27 },
	{ "lane -> rear door", 0, 30 },
	{ "rear door -> patio centre", 0, 36.5 },
	{ "patio -> cross band", 0, 43.8 },
	{ "cross band -> rear-left exit", -18, 43.8 },
	{ "rear-left exit -> outside", -18, 47.8 },
	{ "outside -> cross band", -18, 43.8 },
	{ "cross band -> rear-right exit", 18, 43.8 },
	{ "rear-right exit -> outside", 18, 47.8 },
	{ "outside -> cross band centre", 0, 43.8 },
	{ "cross band -> patio", 0, 33 },
	{ "patio -> grill front (10,32.5)", 10, 32.5 },
	{ "grill front -> patio table front", -4.5, 32.0 },
	{ "table -> rear door", 0, 31 },
	{ "rear door -> lane", 0, 26 },
	{ "lane -> family pad 03 (6.5,11)", 6.5, 11 },
	{ "pad 03 -> lane", 0, 11 },
	{ "lane -> family pad 01 (-8.5,11)", -8.5, 11 },
	{ "pad 01 -> pad 02 (-9.5,15)", -9.5, 14.6 },
	{ "pad 02 -> lane", 0, 14.6 },
	{ "lane -> front door", 0, 5.4 },
	{ "door -> front approach", 0, 1.5 },
}

local results = {}
for _, leg in ipairs(legs) do
	local name, X, D = leg[1], leg[2], leg[3]
	local target = R(X, D)
	local t0 = os.clock()
	local reached = false
	local lastPos, stuckT = hrp.Position, os.clock()
	hum:MoveTo(target)
	while os.clock() - t0 < 40 do
		RS.Heartbeat:Wait()
		local p = hrp.Position
		minY, maxY = math.min(minY, p.Y), math.max(maxY, p.Y)
		local flat = Vector3.new(p.X - target.X, 0, p.Z - target.Z).Magnitude
		if flat < 1.2 then
			reached = true
			break
		end
		if (p - lastPos).Magnitude > 0.3 then
			lastPos, stuckT = p, os.clock()
		elseif os.clock() - stuckT > 4 then
			break
		end
		if os.clock() - t0 > 6 and math.floor((os.clock() - t0) * 2) % 12 == 0 then
			hum:MoveTo(target) -- MoveTo times out after 8 s; re-issue (no teleport)
		end
	end
	local p = hrp.Position
	local flat = Vector3.new(p.X - target.X, 0, p.Z - target.Z).Magnitude
	table.insert(results, { name, reached, flat, os.clock() - t0 })
	print(string.format("LEG %-38s %s  dist=%.2f  t=%.1fs  y=%.2f", name, reached and "OK  " or "FAIL", flat, os.clock() - t0, p.Y))
end
local ok = 0
for _, r in ipairs(results) do
	if r[2] then ok += 1 end
end
local summary = string.format("WALK_RESULT %d/%d legs reached; JumpPower=0; HRP height range %.2f..%.2f (span %.2f); no teleports after spawn",
	ok, #results, minY, maxY, maxY - minY)
print(summary)

-- on-screen report (for the review screenshot)
local lines = { summary }
for _, r in ipairs(results) do
	table.insert(lines, string.format("%s  %s  dist=%.2f  t=%.1fs", r[2] and "OK  " or "FAIL", r[1], r[3], r[4]))
end
local gui = Instance.new("ScreenGui")
gui.Name = "WalkReport"
gui.ResetOnSpawn = false
gui.Parent = plr:WaitForChild("PlayerGui")
local tl = Instance.new("TextLabel")
tl.Size = UDim2.new(0, 760, 0, 470)
tl.Position = UDim2.new(0, 10, 0, 60)
tl.BackgroundColor3 = Color3.new(0, 0, 0)
tl.BackgroundTransparency = 0.25
tl.TextColor3 = Color3.new(1, 1, 1)
tl.TextXAlignment = Enum.TextXAlignment.Left
tl.TextYAlignment = Enum.TextYAlignment.Top
tl.Font = Enum.Font.Code
tl.TextSize = 13
tl.Text = table.concat(lines, "\n")
tl.Parent = gui
