"""Parses raw Studio Output (GDSNAP lines) into data/studio_snapshot_<stage>.json and compares it with the Blender data.
python parse_studio_output.py <review_dir> <raw_output.txt> <stage>"""
import json
import math
import re
import sys

root, raw, stage = sys.argv[1], sys.argv[2], sys.argv[3]
text = open(raw, encoding="utf-8", errors="replace").read()
seen = set()
snap = {"stage": stage, "model": None, "parts": [], "attachments": [], "joints": [], "other": []}
for line in text.splitlines():
    m = re.search(r"GDSNAP\|([^|]+)\|([^|]+)\|(\{.*\})", line)
    if not m or m.group(1) != stage:
        continue
    key = m.group(0)
    if key in seen:
        continue
    seen.add(key)
    d = json.loads(m.group(3))
    k = m.group(2)
    if k == "model":
        snap["model"] = d
    else:
        snap[{"part": "parts", "attachment": "attachments", "joint": "joints", "other": "other"}[k]].append(d)
rig = json.load(open(root + "/data/rig_manifest.json"))
res = json.load(open(root + "/data/_build_result.json"))
spec = json.load(open(root + "/data/construction_spec.json"))
R = lambda p: [-p[0], p[2], p[1]]
cmp_rows = []
for p in snap["parts"]:
    n = p["name"]
    if n not in res["part_bboxes_logical"]:
        continue
    bb = res["part_bboxes_logical"][n]
    exp_size = [bb["size"][0], bb["size"][2], bb["size"][1]]
    exp_ctr = R(bb["centre"])
    ds = max(abs(a - b) for a, b in zip(p["size"], exp_size))
    dc = max(abs(a - b) for a, b in zip(p["cf"][:3], exp_ctr))
    cmp_rows.append({"part": n, "class": p["class"], "size": [round(x, 5) for x in p["size"]], "expected_size": [round(x, 5) for x in exp_size], "max_size_diff": ds,
                     "centre": [round(x, 5) for x in p["cf"][:3]], "expected_centre": [round(x, 5) for x in exp_ctr], "max_centre_diff": dc, "anchored": p["anchored"]})
snap["comparison_to_blender"] = cmp_rows
snap["max_size_diff"] = max((r["max_size_diff"] for r in cmp_rows), default=None)
snap["max_centre_diff"] = max((r["max_centre_diff"] for r in cmp_rows), default=None)
# joint attachments vs Blender bone heads
heads = {b["name"]: b["head_roblox"] for b in rig["bones"]}
jm = {"RightShoulder": "RightUpperArm", "RightElbow": "RightLowerArm", "RightWrist": "RightHand", "LeftShoulder": "LeftUpperArm", "LeftElbow": "LeftLowerArm", "LeftWrist": "LeftHand",
      "RightHip": "RightUpperLeg", "RightKnee": "RightLowerLeg", "RightAnkle": "RightFoot", "LeftHip": "LeftUpperLeg", "LeftKnee": "LeftLowerLeg", "LeftAnkle": "LeftFoot",
      "Waist": "UpperTorso", "Neck": "Head"}
att_rows = []
for a in snap["attachments"]:
    nm = a["name"]
    if not nm.endswith("RigAttachment"):
        continue
    j = nm[:-len("RigAttachment")]
    if j in jm and a["parent"] == jm[j]:
        exp = heads[jm[j]]
        att_rows.append({"joint": j, "parent": a["parent"], "world": [round(x, 5) for x in a["world"]], "expected_bone_head": exp, "diff": max(abs(x - y) for x, y in zip(a["world"], exp)),
                         "position": a["position"], "originalPosition": a.get("originalPosition")})
snap["attachments_vs_bones"] = att_rows
snap["max_attachment_diff"] = max((r["diff"] for r in att_rows), default=None)
snap["joint_gap_max"] = max((j.get("gap", 0.0) for j in snap["joints"]), default=None)
snap["anchored_parts"] = [p["name"] for p in snap["parts"] if p["anchored"]]
json.dump(snap, open("%s/data/studio_snapshot_%s.json" % (root, stage), "w"), indent=1)
print("parts", len(snap["parts"]), "attachments", len(snap["attachments"]), "joints", len(snap["joints"]))
print("max size diff", snap["max_size_diff"], "max centre diff", snap["max_centre_diff"], "max attachment diff", snap["max_attachment_diff"], "joint gap max", snap["joint_gap_max"])
print("anchored", snap["anchored_parts"])
for r in cmp_rows:
    print(r["part"], r["class"], "size", r["max_size_diff"], "centre", r["max_centre_diff"])
