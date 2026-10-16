# RegularDad_Final — final Regular Dad (Common)

Approved final model of the first dad (`RegularDad`, rarity Common, cost 50, income 1/s - unchanged catalog values).
Look: slim tapered right forearm, raised aligned hand, vertical mug at chest height (`MugGrip` RightHand -> Mug).

## Layout
| Path | What |
|---|---|
| `model/RegularDad_Final.rbxm` | Roblox model (Model `RegularDad_R15`: 15 R15 MeshParts, HumanoidRootPart, Humanoid, `Mug`, `NeutralPose`, `HoldMugPose`, `Animations`, `PoseController`). Mapped by Rojo to `ServerStorage.RegularDadFinal`. |
| `source/RegularDad_Final.blend` | Blender source (geometry + armature + neutral/reference pose actions) |
| `source/build_regular_dad_redesign.py` | procedural builder (final geometry is the default, `--slim-forearm` is on) |
| `source/RegularDad_R15.fbx`, `RegularDad_Mug.fbx` | exports (texture atlas embedded) |
| `source/RegularDad_Palette.png`, `RegularDad_Palette_UVMap.json` | 256x128 palette atlas + UV map |
| `scripts/PoseController.luau` | ModuleScript (also inside the model): `Apply(model, "Neutral" \| "HoldMug")` |
| `scripts/build_final_model.luau` | Studio command-bar script that assembles the model from the two FBX imports (pose, mug weld, pose folders) |
| `scripts/studio_qa_runtime.luau` | optional runtime QA (not part of the model) |
| `data/pose_and_asset_data.json` | stored pose CFrames (Neutral / HoldMug) and MeshId/TextureID/ColorMap per part, read from the final model |
| `data/RegularDad_Reference_Crop.png` | approved reference crop |

## Wiring
- `default.project.json`: `ServerStorage.RegularDadFinal` -> `assets/characters/RegularDad_Final/model/RegularDad_Final.rbxm`.
- `src/shared/DadCatalog.lua`: `RegularDad.ModelAsset = "RegularDadFinal"` (Id/Rarity/Cost/Income unchanged).
- `src/server/DadModelBuilder.lua`: if `ModelAsset` is set the finished model is cloned (no overlay parts, no placeholder mug); `PlaceAt` adds the stored `FeetOffset` so the soles are on the floor.
- Spawning stays in the existing `DadService` -> `DadModelBuilder.Build/BuildAll` path.
- Pose is baked into part CFrames and `Attachment1` CFrames of the right arm, so no runtime script is needed; neutral pose lives in `NeutralPose`.

## Reproduce
1. `blender -b --factory-startup --python source/build_regular_dad_redesign.py -- <out>` rebuilds the .blend/.fbx (compare with `source/`).
2. Clean place, Rojo disconnected: import both FBX (3D Importer, Upload to Roblox ON for a real experience), run `scripts/build_final_model.luau`, add `PoseController`, save as .rbxm.

## Known limitations
- MeshId / ColorMap are `rbxassetid://` assets uploaded by the importing account (listed in `data/pose_and_asset_data.json`). They load in that account's experiences; if the game is owned by a different creator or group, re-import the FBX there and re-save the .rbxm.
- No walk/idle animation clips; the raised pose is static and the legs do not swing.
- `PoseController` is not started at runtime by anything (the pose is baked); it is only a switch for tools.
