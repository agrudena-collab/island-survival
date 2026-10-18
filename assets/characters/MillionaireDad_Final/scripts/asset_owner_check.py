"""Writes data/mesh_asset_ids.json from the Studio inspection of the assembled model (data/studio_inspect_assembled.json) and asks the public economy API
(asset details, no login) for creator/type of every id (retry with back-off on HTTP 429).  python asset_owner_check.py <package_dir>"""
import json, re, sys, time, urllib.request
root = sys.argv[1]
snap = json.load(open(root + "/data/studio_inspect_assembled.json"))
ids = {}
for name, e in snap["ids"].items():
    ids[name] = {"MeshId": e["mesh"], **({"ColorMap": e["colorMap"]} if e.get("colorMap") else {}), **({"TextureID": e["tex"]} if e.get("tex") else {})}
json.dump(dict(sorted(ids.items())), open(root + "/data/mesh_asset_ids.json", "w"), indent=1)
uniq = sorted({re.sub(r"\D", "", v) for e in ids.values() for v in e.values() if v})
out = {}
for i in uniq:
    for attempt in range(8):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request("https://economy.roblox.com/v2/assets/%s/details" % i, headers={"User-Agent": "businessdad-qa"}), timeout=20))
            out[i] = {"name": d.get("Name"), "assetTypeId": d.get("AssetTypeId"), "creatorId": d.get("Creator", {}).get("Id"), "creatorType": d.get("Creator", {}).get("CreatorType"), "isPublicDomain": d.get("IsPublicDomain")}
            break
        except Exception as ex:
            out[i] = {"error": str(ex)}
            time.sleep(3 * (attempt + 1))
    time.sleep(1.0)
json.dump(out, open(root + "/data/asset_availability_check.json", "w"), indent=1)
with open(root + "/data/asset_availability_check.txt", "w") as f:
    for i, d in out.items():
        f.write("%s %s type=%s creator=%s public=%s\n" % (i, d.get("name"), d.get("assetTypeId"), d.get("creatorId"), d.get("isPublicDomain")) if "error" not in d else "%s ERROR %s\n" % (i, d["error"]))
print(len(uniq), "ids;", sum(1 for d in out.values() if "error" in d), "errors")
