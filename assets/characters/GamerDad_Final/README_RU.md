# GamerDad_Final — Gamer Dad в фиолетовом свитшоте (финальная модель)

Принятая владельцем версия (визуально принята 17.10.2026) зафиксирована как Final. Модель побайтово совпадает с принятой Review (`GamerDad_Sweatshirt_Review/model/GamerDad_Sweatshirt_Review.rbxm`, SHA-256 `2594a7ad…c8b7`, полный хэш в `MANIFEST.json`). Геометрия, пропорции, борода, лицо, волосы, материалы, гарнитура, свитшот, шорты, обувь, банка и поза не менялись. Капюшона, шнурков, кармана-кенгуру и карго-карманов нет.

## Состав
| Путь | Что |
|---|---|
| `model/GamerDad_Final.rbxm` | готовая модель: HumanoidRootPart + 15 MeshPart R15 + Headset + EnergyCan (17 MeshPart), 15 AnimationConstraint, папки HoldCanPose/NeutralPose, ModuleScript PoseController |
| `source/GamerDad_Final.blend` | принятая сцена Blender (rest-поза = HoldCan) |
| `source/GamerDad_R15.fbx`, `source/GamerDad_Props.fbx` | FBX тела и предметов (импорт Studio: Scale Unit Stud ×1, Forward Front, Up Top) |
| `source/build_gamer_dad_sweatshirt.py`, `source/parts/p00..p06`, `source/assemble.sh`, `source/inputs/` | воспроизводимый билдер (спека, атлас, референс) |
| `textures/GamerDad_Sweatshirt_Atlas.png` | атлас 1024², палитра 34 цвета + принты |
| `data/` | `pose_and_asset_data.json` (размеры, transforms, суставы, attachments, поза, точки хвата/гарнитуры, MeshId/TextureId/ColorMap, владельцы), `construction_spec`, `component_registry`, `rig_manifest`, `palette_uv_map`, `gap_checks`, `studio_snapshot_*`, `studio_raw/` (сырой Output Studio), `asset_availability_check.txt`, `reproducibility_summary.json`, `reference_comparison/` |
| `scripts/` | сборка в Studio (`build_review_model.luau`, `gen_assembly.py`), `PoseController.luau`, QA-скрипты (`studio_final_qa.luau` — F5-спавн + перенос; `studio_f5_camera_views.luau`; `studio_qa_*`), анализ (`measure_gaps.py`, `compare_reference.py`, `dump_geometry.py` …) |
| `evidence/` | `control_frames/` (кадры принятой версии: Blender и Studio), `f5_frames/` (штатный спавн, F5) |
| `MANIFEST.json` | SHA-256 всех файлов папки |
| `VERIFICATION_RU.md` | проверки, числа, ограничения |

Review-папка `assets/characters/GamerDad_Sweatshirt_Review/` и архив `.zip` остаются отдельно (не в коммите).

## Подключение
- `default.project.json`: `ServerStorage.GamerDadFinal` → `assets/characters/GamerDad_Final/model/GamerDad_Final.rbxm`.
- `src/shared/DadCatalog.lua`: запись `Id = "GamerDad"` получила `ModelAsset = "GamerDadFinal"`; Rarity Rare, Cost 400, IncomePerSecond 7 не менялись.
- Спавн идёт штатно: `DadModelBuilder.Build("GamerDad")` клонирует `ServerStorage.GamerDadFinal` (без процедурных накладок), `PlaceAt` ставит модель по подошвам (FeetOffset 3.38).

## Крепления
- Банка: `WeldConstraint CanGrip` (Part0 = RightHand, Part1 = EnergyCan); положение относительно кисти (−0.5, 0.12, −0.135); CanCollide/CanQuery/CanTouch = false, Massless = true.
- Гарнитура: `WeldConstraint HeadsetMount` (Part0 = Head, Part1 = Headset); относительно Head (0, 0.2175, −0.1474); те же флаги.

## Воспроизведение
`blender -b --factory-startup --python source/build_gamer_dad_sweatshirt.py -- <outdir> [--quick] [--norender] [--keepcomp]` (см. `source/assemble.sh`). Проверено: JSON-результаты побайтово идентичны, хэши геометрии `.blend` и FBX совпадают (`data/reproducibility_summary.json`); байтовое равенство самих FBX не заявляется. Для Studio: импорт обоих FBX, затем `scripts/build_review_model.luau` (генерируется `gen_assembly.py`).

## Ограничения
Neutral-поза PoseController — QA-поза, в Edit-режиме не удерживается (в Run/Play держится). Доступ к ассетам у других игроков в опубликованной игре не проверялся. Подробнее — `VERIFICATION_RU.md`.
