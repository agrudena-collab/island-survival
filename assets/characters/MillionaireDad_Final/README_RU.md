# MillionaireDad_Final — Millionaire Dad (Legendary), финальная модель

Утверждённая владельцем review-версия (`assets/characters/MillionaireDad_Review/`, 18.10.2026) зафиксирована как Final без изменений: `model/MillionaireDad_Final.rbxm` побайтово совпадает с `MillionaireDad_Review/model/MillionaireDad_Review.rbxm`.

SHA-256 (review = final): `3df51ec5f3a7154e9b8ee5a7964b01c98202ef2945b3db40527697d9cea3ae84`. Намеренных отличий нет. Хэши всех файлов — `MANIFEST.json`.

## Состав
| Путь | Что |
|---|---|
| `model/MillionaireDad_Final.rbxm` | 15 MeshPart R15 + `Case` (16 MeshPart) + HumanoidRootPart + Humanoid, 15 AnimationConstraint, `CaseGrip` (WeldConstraint RightHand→Case; CanCollide/CanQuery/CanTouch=false, Massless=true). Часы запечены в LeftHand. Модель статична: папок поз и PoseController нет |
| `source/MillionaireDad_Final.blend` | принятая сцена Blender (копия `MillionaireDad_Review.blend`) |
| `source/build_millionaire_dad.py`, `source/parts/m00..m08`, `source/assemble.sh`, `source/inputs/` | воспроизводимый билдер; `inputs/` — настройка камеры, кроп оригинала и 2D-ориентиры (нужны для рендеров/сверки) |
| `export/MillionaireDad_Body.fbx`, `MillionaireDad_Props.fbx` | FBX тела и кейса (импорт Studio: Scale Unit Stud ×1, World Forward Front, Up Top) |
| `textures/MillionaireDad_Atlas.png` | атлас 1024², 44 цвета |
| `data/` | `mesh_asset_ids.json`, владельцы ассетов, риг и хват, габариты, UV палитры, статистика, `landmark_comparison.json`, `overlap_audit.json`, `studio_inspect_assembled.json`, `studio_f5_carry_check.json`, `reproducibility_summary.json` |
| `scripts/` | `gen_assembly.py` → `build_review_model.luau` (сборка в Studio из двух FBX), `asset_owner_check.py`, `overlap_audit.py`, `fit_camera.py` |

Рендеры, живая `.blend` из MCP, места Studio, итерации и отчёты review остаются в `assets/characters/MillionaireDad_Review/` (не в коммите).

## Подключение
- `default.project.json`: `ServerStorage.MillionaireDadFinal` → `assets/characters/MillionaireDad_Final/model/MillionaireDad_Final.rbxm`.
- `src/shared/DadCatalog.lua`: у `MillionaireDad` добавлено `ModelAsset = "MillionaireDadFinal"`; Legendary, Cost 1500, IncomePerSecond 25 и остальное не менялись.
- Спавн штатный: `DadModelBuilder.Build("MillionaireDad")` клонирует `ServerStorage.MillionaireDadFinal` без процедурных накладок (старая корона и золотой кейс-блок из каталога не используются), `PlaceAt` ставит по подошвам (атрибут FeetOffset).

## Воспроизведение
`blender -b --factory-startup --python source/build_millionaire_dad.py -- <outdir> [--norender]` (скрипт собирает `source/assemble.sh`; билдер пишет имена review). Проверено: вершины 16 мешей, UV и атлас идентичны (`data/reproducibility_summary.json`); байтовое равенство FBX не заявляется. Для Studio: импорт обоих FBX, затем `scripts/build_review_model.luau`.

## Ограничения
- Все 17 ассетов (16 мешей и атлас) принадлежат аккаунту 3938337813 и не публичные; доступ других игроков в опубликованной игре не проверялся.
- Это процедурная low-poly сборка по референсу, не точная копия картинки (отличия — в `MillionaireDad_Review/README_RU.md`). Невидимые места (спина, затылок, задняя сторона кейса, циферблат) — допущения, принятые владельцем вместе с версией.
- Статичная модель: ходьбы/idle нет.
