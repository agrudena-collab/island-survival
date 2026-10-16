# Steal a Dad! — Dad character assets

## Live asset

- `models/DadBaseRig.rbxm` — the single realistic Rthro R15 rig used by `src/server/DadModelBuilder.lua`.
  It was built in Studio via Avatar → Character → Rig Type R15, Rthro, Masculine, then saved to this file.
  `DadModelBuilder` clones it per dad and dresses it with welded colored overlay parts
  (shirt/pants bands, headwear, held accessory) driven by `src/shared/DadCatalog.lua`.

## Archived reference (not wired into the game)

- `tools/build_dads.py` — a Blender script that procedurally built 8 custom low-poly FBX
  bodies plus 11 prop meshes. That approach was replaced by the Rthro base rig above.
  Kept only as a reference for prop geometry ideas (mug, briefcase, shovel, etc.) if
  held props are ever upgraded from primitive parts to real meshes.
- `previews/` — renders from that script, for the same reference purpose.

Do not re-run `tools/build_dads.py` without explicit approval — it was last used to generate
assets that are no longer part of the project.
