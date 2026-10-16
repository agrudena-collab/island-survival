# GrillDad_Final — финальная модель Grill Dad (персонаж 04, Uncommon)

Внешность утверждена владельцем 16.10.2026. Модель — **побайтовая копия** принятой review-версии `assets/characters/GrillDad_Redesign/model/GrillDad_Review.rbxm` (проверено `cmp`); внешность, пропорции, лицо, фартук, полотенце, поза, кисть и щипцы не менялись. Review-версия (`GrillDad_Redesign`) сохранена отдельно.

## Состав
| Путь | Что |
|---|---|
| `model/GrillDad_Final.rbxm` | окончательная модель (69 583 Б), подключается Rojo |
| `source/GrillDad_Final.blend` | сцена Blender (копия принятой) |
| `source/build_grill_dad.py`, `source/parts/*.py`, `source/assemble.sh` | билдер (`assemble.sh` склеивает части в `build_grill_dad.py`) |
| `source/GrillDad_R15.fbx`, `source/GrillDad_Tongs.fbx` | FBX, из которых импортирована принятая модель |
| `textures/GrillDad_Palette.png` | палитра 256×256, 44 цвета |
| `data/` | `pose_and_asset_data.json` (размеры, позиции, MeshId, текстуры, суставы, крепления), `construction_spec.json` (суставы bind/поза, IK, отступления), `rig_manifest.json`, `component_registry.json`, `palette_uv_map.json`, `_build_result.json`, `asset_availability_check.txt`, `reference_comparison/` |
| `scripts/` | `build_review_model.luau` (сборка модели в Studio из FBX), `PoseController.luau` (`Apply(model)` восстанавливает статичную позу из `HoldTongsPose`), проверки Studio: `studio_check_model`, `studio_check_spawned`, `studio_qa_carry_spawned`, `studio_qa_client_move`, `studio_f5_camera_views`, `studio_dump_asset_data`, `studio_qa_runtime`, `compare_reference.py` |

Рендеры Blender, кадры Studio, видео и review-place лежат вне Git (архив `GrillDad_Final.zip` на рабочем столе).

## Воспроизводимость
Билдер из `source/` повторно запущен: палитра, `palette_uv_map`, `construction_spec`, `component_registry`, `rig_manifest`, `_build_result` побайтово совпали с сохранёнными (5 776 / 572 треугольника, высота 6.40); FBX отличаются только заголовком. Повторный запуск билдера пишет `GrillDad_Redesign.blend` в `<out>/source/` (имя файла внутри билдера не менялось); в репозитории тот же файл сохранён как `GrillDad_Final.blend`.

Восстановление: `bash source/assemble.sh` → `blender -b --factory-startup --python source/build_grill_dad.py -- <outdir>` → импорт FBX в Studio (3D Importer, «Import Only as a Model», имена `GrillDad_R15` и `GrillDad_Tongs`) → `scripts/build_review_model.luau` → `PoseController`. Меши и текстура при этом загружаются на аккаунт импортирующего, поэтому источником правды для проекта остаётся `model/GrillDad_Final.rbxm` с уже загруженными `rbxassetid` (`data/pose_and_asset_data.json`).

## Подключение к проекту
- `default.project.json`: `ServerStorage.GrillDadFinal` → `assets/characters/GrillDad_Final/model/GrillDad_Final.rbxm`.
- `src/shared/DadCatalog.lua`: у существующей записи `Id = "GrillDad"` (Uncommon, цена 220, доход 4) добавлено только `ModelAsset = "GrillDadFinal"`; остальные поля (Accessory/Headwear/TorsoDetail остаются в каталоге, но для финальной модели не используются), экономика и Id не менялись.
- `src/server/DadModelBuilder.lua` не менялся (поддержка `ModelAsset` и исправленный `PlaceAt` уже в основе ветки из коммита `512b0ee`).
- Спавн: `DadModelBuilder.Build("GrillDad")` → `PlaceAt`. Сейчас единственный вызывающий — временный предпросмотр в **незакоммиченном** `src/server/Services/DadService.lua`; в коммит он не входит.

## Статичная поза и реквизит
Анимации ходьбы нет. `TongsGrip` (WeldConstraint LeftHand → GrillTongs); у щипцов `CanCollide/CanQuery/CanTouch = false`, `Massless = true`, `Anchored = false` в самой модели (якорит только `PlaceAt` при постановке в мир; перед переносом механика должна снять якоря). Фартук, полотенце, пятна, лямки — геометрия `UpperTorso`.

## Проверки и ограничения
См. `VERIFICATION_RU.md`.
