# Отчёт для коллеги — биом рыбака-отца и биом любовницы («Гавань»), 2026-11-09

Ветка: `feature/fisherman-dad-district`. Place1 в Studio сохраняет вручную Ivan (Ctrl+S); `.rbxl` в репо не лежит.

## Что сделано

| Блок | Где в репо |
|---|---|
| Биом отца-рыбака FishermanDadDistrict, сборки build4–6 (FBX, цвета, коллайдеры, якоря, хитбоксы, камера) | `_inbox/FishermanDad_build4..6`, отчёт `_inbox/FISHERMAN_DAD_BIOME_REPORT.md` |
| Биом любовницы «Гавань» FishermanMistressHarbor, сборки build1–4 | `_inbox/FishermanMistressHarbor_build1..4` |
| Квартира любовницы MistressFlat3 (вынесена на -15000,300,15000) и референсы | `_inbox/MistressFlat3`, `_inbox/MistressApartmentHarbor_refs` |
| Правила хитбоксов/камеры для биомов | `AGENTS.md` |
| Журнал | `docs/STEAL_A_DAD_PROJECT.md`, A5, запись 2026-11-09 |

## Последняя правка: камера в квартире любовницы

- **Проблема:** камера вылетала за границы квартиры. Оконные `WindowGlass` невидимые (Transparency=1) с коллизией: игрока держат, а стандартная камера Roblox сквозь прозрачное проходит.
- **Решение (в Studio):**
  - невидимый Part `Workspace.FishermanMistressHarbor.MistressBuilding3.CamBounds` (≈65×14.4×41 по стенам; Anchored, CanCollide/CanQuery/CanTouch=false) с тегом `ApartmentCamBounds`;
  - LocalScript `StarterPlayer.StarterPlayerScripts.ApartmentCameraClamp`: пока игрок внутри бокса, камера зажимается внутри с отступом 1.5. Копия: `_inbox/FishermanMistressHarbor_build3/ApartmentCameraClamp.client.luau`;
  - временная заглушка двери `Interior.CamSeal_TEMP/DoorCamSeal` удалена.
- **Проверено:** в Play камера принудительно уводилась наружу и зажималась у стены; вид в окно на гавань цел. Ivan подтвердил.
- **Для других квартир:** добавить такой же бокс с тегом `ApartmentCamBounds`.
- Скрипт — именно LocalScript в `StarterPlayerScripts`: `Script` с `RunContext=Client` под Workspace в Play Solo со стримингом не запускался.

## Не проверено / открыто

- Мультиплеер и публикуемый place; другие квартиры.
- `ApartmentCameraClamp` и `CamBounds` живут только в Place1 (в Rojo/`src/` не подключены). Нужно сохранить place либо перенести скрипт в `src/client` (решение владельца).
- Сцены в Place1 не сохранены до Ctrl+S; иначе сборку повторять скриптами из `_inbox/*`.
- Push и PR не делались.

## Пересборка «Гавани»

Импорт FBX из `_inbox/FishermanMistressHarbor_build*/` → `apply_harbor_colors` → `build_harbor_colliders_anchors` → `camera_block` → `biome_setup_harbor` (порядок в README_RU.md сборки). После импорта сразу выровнять MeshParts по коллайдерам.
