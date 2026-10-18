# BusinessDad_Final — Business Dad (Epic), финальная модель

Утверждённая review-версия (`assets/characters/BusinessDad_Review/`, ревизия 6, 18.10.2026) зафиксирована как Final без изменений: `model/BusinessDad_Final.rbxm` побайтово совпадает с `BusinessDad_Review/model/BusinessDad_Review.rbxm`.

SHA-256 (review = final): `cd2e8aa79ae0753783f14f53b76c6bad6f3420eabcd900bc91bfe1e96dc05a86`. Намеренных отличий нет. Полные хэши всех файлов — `MANIFEST.json`.

## Состав
| Путь | Что |
|---|---|
| `model/BusinessDad_Final.rbxm` | 15 MeshPart R15 + Phone (16 MeshPart) + HumanoidRootPart + Humanoid, 15 AnimationConstraint, `PhoneGrip` (WeldConstraint LeftHand→Phone; CanCollide/CanQuery/CanTouch=false, Massless=true). Часы запечены в LeftHand. Модель статична: папок поз и PoseController нет (не требуются) |
| `source/BusinessDad_Final.blend` | принятая сцена Blender (копия `BusinessDad_Review.blend`) |
| `source/build_business_dad.py`, `source/parts/b00..b08`, `source/assemble.sh`, `source/inputs/camera_tuned.json` | воспроизводимый билдер (`camera_tuned.json` нужен только для рендеров) |
| `export/BusinessDad_Body.fbx`, `BusinessDad_Props.fbx` | FBX тела и телефона (импорт Studio: Scale Unit Stud ×1, World Forward Front, Up Top) |
| `textures/BusinessDad_Atlas.png` | атлас 1024², 52 цвета |
| `data/` | `mesh_asset_ids.json` (MeshId/ColorMap/TextureID), владельцы (`asset_availability_check.*`), риг, суставы/хват, габариты, UV палитры, статистика, `studio_inspect_assembled.json`, `overlap_audit.json`, `reproducibility_summary.json`, `reference_measurements.json` + кроп оригинала |
| `scripts/` | `gen_assembly.py` → `build_review_model.luau` (сборка в Studio из двух FBX), `asset_owner_check.py`, `overlap_audit.py` |
| `MANIFEST.json` | SHA-256 всех файлов папки |

Рендеры, живая `.blend` из MCP, места Studio, итерации и отчёты review остаются в `assets/characters/BusinessDad_Review/` (не в коммите).

## Подключение
- `default.project.json`: `ServerStorage.BusinessDadFinal` → `assets/characters/BusinessDad_Final/model/BusinessDad_Final.rbxm`.
- `src/shared/DadCatalog.lua`: у `BusinessDad` добавлено `ModelAsset = "BusinessDadFinal"`; Rarity Epic, Cost 900, IncomePerSecond 15 и остальное не менялись.
- Спавн штатный: `DadModelBuilder.Build("BusinessDad")` клонирует `ServerStorage.BusinessDadFinal` без процедурных накладок, `PlaceAt` ставит модель по подошвам (атрибут FeetOffset).

## Воспроизведение
`blender -b --factory-startup --python source/build_business_dad.py -- <outdir> [--norender]` (скрипт собирает `source/assemble.sh`; билдер пишет имена review: `BusinessDad_Review.blend`, `BusinessDad_Body.fbx`, `BusinessDad_Props.fbx`). Проверено: вершины 16 мешей, UV и атлас идентичны (`data/reproducibility_summary.json`); байтовое равенство FBX не заявляется. Для Studio: импорт обоих FBX, затем `scripts/build_review_model.luau`.

## Ограничения
- Все 18 ассетов (16 мешей, атлас и автосозданный импортёром `SurfaceAppearance.TexturePack` 90010007756356) принадлежат аккаунту 3938337813 и не публичные; доступ других игроков в опубликованной игре не проверялся.
- Это процедурная low-poly сборка по референсу, а не точная копия картинки (отличия описаны в `BusinessDad_Review/README_RU.md`).
- Проверка (Studio, место `BusinessDadFinal_test.rbxl`, собрано `rojo build`; Rojo к месту не подключался): спавн в Play через путь `DadModelBuilder` (в рабочем дереве — превью владельца `workspace.DadPreview`, в коммит не входит), `data/studio_play_check.json` и `data/studio_carry_check.json`. В Rojo-месте нет пола: перенос/падение проверены на временном полу; игрока и штатной механики кражи в тесте не было.
- Публикации нет.
