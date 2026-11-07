# FishermanDadDistrict (район 6, build6)

Район приходит готовым извне (генератора в репо нет). Здесь лежат исходник и единый скрипт настройки.

- `source/FishermanDadDistrict.fbx` — FBX build6 (8 906 220 байт).
- `setup/FishermanDad_setup_all.luau` — ОДИН перезапускаемый скрипт, заменяет прежние три файла (apply_fsd_colors, build_studio_colliders_anchors, fix_hitboxes) + biome_setup. Порядок: цвета → коллайдеры и якоря → выравнивание мешей по коллайдерам → пол/вода/спавн/границы → фиксы хитбоксов и камеры. Разделы про соседскую лодку и FrontStep убраны (исправлено в исходнике).

## Как использовать
1. Studio: File → Import 3D (Upload OFF) `source/FishermanDadDistrict.fbx` → `Workspace.FishermanDadDistrict`.
2. Command Bar (Edit): вставить содержимое `setup/FishermanDad_setup_all.luau` (68 КБ). Каждый шаг в pcall, итог OK/ERR печатается в Output.
3. Для постоянного цветного импорта: Explorer → правый клик по модели → Save/Export → Save to File → `model/FishermanDadDistrict.rbxm`, затем подключить в `default.project.json` (пока НЕ подключено: .rbxm ещё нет).

## Статус
Скрипт собран из проверенных на build4/build5 частей. На build6 целиком НЕ запускался: модель в Place1 не импортирована.
