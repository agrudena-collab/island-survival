# GymDad_Final — Gym Dad (финальная модель)

Принятая владельцем версия Gym Dad Review V2 зафиксирована как Final без изменений: `model/GymDad_Final.rbxm` побайтово совпадает с `GymDad_Redesign_V2/model/GymDad_Review_V2.rbxm` (SHA-256 в `MANIFEST.json`). Внешность, поза, гантель, хват, риг и идентификаторы ассетов не менялись. Gym Dad статичен: анимаций нет, при переносе держит позу HoldWeights.

## Состав
| Путь | Что |
|---|---|
| `model/GymDad_Final.rbxm` | HumanoidRootPart + 15 MeshPart R15 + Dumbbell + GymBag (17 MeshPart), 15 AnimationConstraint, `DumbbellGrip` (RightHand→Dumbbell) и `BagGrip` (LeftHand→GymBag) — WeldConstraint, папки HoldWeightsPose/NeutralPose, ModuleScript PoseController |
| `source/GymDad_Final.blend` | принятая сцена Blender (rest-поза = HoldWeights) |
| `export/GymDad_V2_Body.fbx`, `export/GymDad_V2_Props.fbx` | FBX тела и предметов (импорт Studio: Scale Unit Stud ×1, World Forward Front, Up Top) |
| `source/build_gym_dad.py`, `source/parts/g00..g08`, `source/assemble.sh`, `source/inputs/GymDad_Construction_Spec.json` | воспроизводимый билдер Blender (палитра/спека, атлас) |
| `textures/GymDad_Atlas.png` | атлас 1024² |
| `data/` | MeshId/ColorMap всех 17 мешей (`mesh_asset_ids.json`), владельцы ассетов (`asset_availability_check.txt`), риг, суставы/хваты, габариты, UV палитры, воспроизводимость |
| `scripts/` | `gen_assembly.py` → `build_review_model.luau` (сборка в Studio из двух FBX), `PoseController.luau` |

Рендеры, тестовые места, видео, отчёты и итерации Review остаются в `assets/characters/GymDad_Redesign_V2/` (не в коммите).

## Подключение
- `default.project.json`: `ServerStorage.GymDadFinal` → `assets/characters/GymDad_Final/model/GymDad_Final.rbxm`.
- `src/shared/DadCatalog.lua`: у `GymDad` добавлено `ModelAsset = "GymDadFinal"`; Rarity Rare, Cost 550, IncomePerSecond 9 не менялись.
- Спавн штатный: `DadModelBuilder.Build("GymDad")` клонирует `ServerStorage.GymDadFinal` без процедурных накладок, `PlaceAt` ставит по подошвам (атрибут FeetOffset).

## Воспроизведение
`blender -b --factory-startup --python source/build_gym_dad.py -- <outdir>` (скрипт собирается `source/assemble.sh`). Для Studio: импорт обоих FBX, затем `scripts/build_review_model.luau`. Подробные проверки — `assets/characters/GymDad_Redesign_V2/VERIFICATION_RU.md`.

## Ограничения
Все 18 ассетов (17 мешей + атлас) принадлежат аккаунту 3938337813 и не публичные; доступ других аккаунтов в опубликованной игре не проверялся. Neutral-поза PoseController — QA-поза, в Run/Play для этой модели не проверялась.
