# OfficeDad_Final — финальная модель Office Dad

Утверждена владельцем 2026-10-16 как финальная (версия из `OfficeDad_Screenshots.pdf`). Внешность, пропорции, очки, волосы, одежда, кисть и дипломат не менялись относительно review-версии `assets/characters/OfficeDad_Redesign/`, которая сохранена нетронутой.

## Состав
| Путь | Назначение |
|---|---|
| `model/OfficeDad_Final.rbxm` | готовая модель (17 частей: 15 MeshPart тела + `HumanoidRootPart` + `Briefcase`), подключается через Rojo |
| `source/OfficeDad_Final.blend` | сцена Blender |
| `source/build_office_dad.py` | процедурный билдер (воспроизводит .blend, оба FBX, палитру, данные) |
| `source/OfficeDad_R15.fbx`, `source/OfficeDad_Briefcase.fbx` | экспорт для импорта в Studio |
| `textures/OfficeDad_Palette.png` | палитра-атлас (ColorMap через SurfaceAppearance) |
| `data/` | размеры, поза, суставы, хват и ID ассетов (`pose_and_asset_data.json`, `rig_manifest.json`, `palette_uv_map.json` и др.) |
| `scripts/build_final_model.luau` | сборка модели в Studio из двух FBX (размещение, `Briefcase`, `BriefcaseGrip`, `NeutralPose`) |
| `scripts/PoseController.luau` | восстановление нейтральной позы из `NeutralPose` |
| `scripts/fit_reference_match.py` | инструмент сравнения с референсом (справочно) |

## Подключение к игре
- `default.project.json`: `ServerStorage.OfficeDadFinal` -> `assets/characters/OfficeDad_Final/model/OfficeDad_Final.rbxm`.
- `src/shared/DadCatalog.lua`: запись `OfficeDad` получила `ModelAsset = "OfficeDadFinal"`; Id, `Common`, цена 75, доход 1.5 без изменений. Поля Accessory/Headwear/TorsoDetail остаются в каталоге, но для финальной модели не используются.
- `src/server/DadModelBuilder.lua` (код не менялся): при `ModelAsset` клонирует модель из ServerStorage, не добавляет накладки (кружку, галстук, шляпу), записывает атрибут `FeetOffset` (2.92) и ставит подошвы на уровень земли через `PlaceAt`.

## Поза и хват
- Статичная поза, анимации ног нет, отец не ходит; переносится целиком.
- Один `WeldConstraint` `BriefcaseGrip`: `Part0 = RightHand`, `Part1 = Briefcase`. У дипломата `CanCollide/CanQuery/CanTouch = false`, `Massless = true`, `Anchored = false` в самой модели.
- Относительное положение RightHand -> Briefcase: (0.105, -0.9225, -0.1355).
- Размер: 6.40 стад в высоту, HRP на Y = 2.92, подошвы на Y = 0. Треугольников: тело 4173, дипломат 276.
- `OriginalPosition` согласованы с положением всех 30 «обычных» вложений; 4 записи `JointRotation` — служебные (вектор поворота плеч, Position = 0 по конвенции импортёра, так же как у Regular Dad).

## Воспроизведение
1. Билдер: `blender -b --factory-startup --python source/build_office_dad.py -- <outdir> [--quick] [--norender]`. Результат: `<outdir>/source/*.blend`, `<outdir>/export/*.fbx`, `<outdir>/data/*.json`, `<outdir>/OfficeDad_Palette.png`. Проверено: палитра и JSON побайтно совпали с сохранёнными, 4173/276 треугольников, высота 6.40. FBX отличаются только заголовком (путь/время экспорта).
2. Studio (чистое место, Rojo отключён): импорт обоих FBX через 3D Importer под именами `OfficeDad_R15` и `OfficeDad_Briefcase`, затем `scripts/build_final_model.luau`. Меши и текстура загружаются на аккаунт импортирующего.
3. ID ассетов (16 MeshId + 1 палитра) записаны в `data/pose_and_asset_data.json`; владелец — аккаунт 3938337813.

## Ограничения
- Мэши/текстура принадлежат аккаунту 3938337813 и не публичны: проверено через economy API, что все 17 существуют; работа у других игроков в опубликованном experience не проверялась (игра не публиковалась).
- Игровая кража/механизм переноса в проекте не реализованы; перенос проверен QA-тестом (WeldConstraint к носителю).
- Модель в игре сейчас спавнится через временный предпросмотр `DadService` (не часть этого коммита).
- Известные замечания review-версии: канал хвата визуально делит кисть; IoU с референсом 0.711/0.782 (цель 0.90 не достигнута).
