# FishermanDad_Final — финальная модель Fisherman Dad (персонаж 03, Uncommon)

Внешность утверждена владельцем 16.10.2026. Модель — **побайтовая копия** принятой review-версии `assets/characters/FishermanDad_Redesign/model/FishermanDad_Review.rbxm` (проверено `cmp`); внешность, пропорции, лицо, одежда, поза, хват, удочка и ведро не менялись. Review-версия (`FishermanDad_Redesign`) сохранена.

## Состав
| Путь | Что |
|---|---|
| `model/FishermanDad_Final.rbxm` | окончательная модель (98 725 Б), подключается Rojo |
| `source/FishermanDad_Final.blend` | сцена Blender (копия принятой) |
| `source/build_fisherman_dad.py`, `source/parts/*.py`, `source/assemble.sh` | билдер (`assemble.sh` склеивает части в `build_fisherman_dad.py`) |
| `source/FishermanDad_R15.fbx`, `FishermanDad_Rod.fbx`, `FishermanDad_Bucket.fbx` | FBX, из которых импортирована принятая модель |
| `textures/FishermanDad_Palette.png` | палитра 256×256, 49 цветов |
| `data/` | `pose_and_asset_data.json` (размеры, позиции, MeshId, текстуры, суставы, локальные крепления), `construction_spec.json` (суставы bind/поза, IK, ось удилища, отступления от ТЗ), `rig_manifest.json`, `component_registry.json`, `palette_uv_map.json`, `_build_result.json`, `asset_availability_check.txt`, `reference_comparison/` |
| `scripts/` | `build_review_model.luau` (сборка модели в Studio из FBX), `PoseController.luau` (`Apply(model)` восстанавливает статичную позу из `HoldRodPose`), проверки Studio (`studio_check_model`, `studio_check_spawned`, `studio_qa_carry_spawned`, `studio_qa_client_move`, `studio_f5_camera_views`, `studio_dump_asset_data`, `studio_camera_tour`, `studio_qa_runtime`), `compare_reference.py` |

Рендеры Blender, кадры Studio, видео и review-place лежат вне Git (архив `FishermanDad_Final.zip` на рабочем столе).

## Воспроизводимость
Билдер из `source/` повторно запущен: палитра, `palette_uv_map`, `construction_spec`, `component_registry`, `rig_manifest`, `_build_result` побайтово совпали с сохранёнными, 6 840 / 2 084 / 588 треугольников, высота 6.40 (FBX отличаются только заголовком с путём/временем). Билдер в `source/` — тот же, что выпустил принятую версию; blend сохранён с именем `FishermanDad_Final.blend`, а повторный запуск пишет `FishermanDad_Redesign.blend` в `<out>/source/` (имя файла внутри билдера не менялось).

Восстановление модели: `blender -b --factory-startup --python source/build_fisherman_dad.py -- <outdir>` → импорт трёх FBX в Studio (3D Importer, «Import Only as a Model») → `scripts/build_review_model.luau` → `PoseController`. Меши и текстура при этом загружаются на аккаунт импортирующего, поэтому для проекта источником правды остаётся `model/FishermanDad_Final.rbxm` с уже загруженными `rbxassetid` (`data/pose_and_asset_data.json`).

## Подключение к проекту
- `default.project.json`: `ServerStorage.FishermanDadFinal` → `assets/characters/FishermanDad_Final/model/FishermanDad_Final.rbxm`.
- `src/shared/DadCatalog.lua`: у записи третьего отца (`Id = "GardenerDad"`, Uncommon, цена 150, доход 3) добавлено `ModelAsset = "FishermanDadFinal"` и `DisplayName = "Fisherman Dad"`. **Id не переименован**: в репозитории нет отдельной записи рыбака, `GardenerDad` — заглушка третьего слота (щит/фартук/шляпа, без модели), а Id используется сохранёнными `OwnedDads`; новых Id/дублей не создавалось. Цена, доход, редкость, ColorTheme и старые поля не менялись (для финальной модели `Accessory/Headwear/TorsoDetail` не используются).
- `src/server/DadModelBuilder.lua`: уже поддерживает `ModelAsset`. Исправлен общий баг порядка в `PlaceAt`: сначала якорение всех частей, потом `PivotTo` (до этого при перемещении незаякоренного Humanoid-рига двигался только `HumanoidRootPart`, а конечности и реквизит оставались в старой точке; это касалось и Regular/Office при размещении через `PlaceAt`). Файлы моделей Regular/Office не менялись.
- Спавн: штатный `DadModelBuilder.Build("GardenerDad")` → `PlaceAt`. Сейчас единственный вызывающий — временный предпросмотр в **незакоммиченном** `src/server/Services/DadService.lua` (владелец), в коммит он не входит.

## Статичная поза и реквизит
Анимации ходьбы нет. `RodGrip` (WeldConstraint LeftHand → FishingRod), `BucketMount` (WeldConstraint HumanoidRootPart → Bucket); у реквизита `CanCollide/CanQuery/CanTouch = false`, `Massless = true`; внутри модели нет заякоренных деталей (якорит только `PlaceAt` при постановке в мир — перед переносом механика должна снять якоря). Леска и поплавок — часть меша `FishingRod`.

## Проверки и ограничения
См. `VERIFICATION_RU.md`. Главные ограничения: загрузка ассетов другими игроками не проверена (нужен второй аккаунт); механики переноса/кражи в проекте нет — тест переноса это QA-приваривание к игроку; видео — склейка кадров экрана (~4 кадра/с).
