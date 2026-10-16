# VERIFICATION_RU — Grill Dad Final (16.10.2026)

| Проверка | Результат |
|---|---|
| `git diff --check` | PASS (только предупреждения LF→CRLF) |
| `rojo build default.project.json` | PASS |
| Билдер воспроизводит принятую модель | PASS: палитра и 5 JSON побайтово совпали; 5 776 / 572 тр.; `.rbxm` Final = `.rbxm` review (cmp) |
| Появление через штатный путь (`DadModelBuilder.Build("GrillDad")` → `PlaceAt`, F5) | PASS: 17 частей (16 MeshPart + HRP), лишних частей 0, старых накладок (BBQTongs/Apron/Brim/Mug/Briefcase/FishingRod/Bucket) 0, подпись «Grill Dad (Uncommon)», FeetOffset 3.05 |
| Подошвы на полу | PASS: 0.0 (`TestGround` на Y=0, только в тестовом place) |
| Суставы / поза после спавна Humanoid | PASS: 15 AnimationConstraint, ошибка ≤ 2.0e-06; OriginalPosition 30 проверено, 0 расхождений; tongs rel hand (0, 0.71, 0.01) неизменно |
| Цвета | PASS: 15 SurfaceAppearance (ColorMap), щипцы — TextureID палитры; MeshPart.Color (0.639,0.635,0.647) как у предыдущих отцов; кадры F5 показывают корректные цвета (сталь и фартук темнее/синее, чем в Blender, из-за освещения Studio, но не чёрные) |
| Крепление | PASS: `TongsGrip` LeftHand→GrillTongs; щипцы CanCollide/CanQuery/CanTouch=false, Massless=true; закреплённого в мире реквизита нет |
| Перенос — QA-тест приваривания к игроку (НЕ игровая механика; её в проекте нет) | PASS: ~1 255 замеров за 22 с (ходьба 4×14 стад, повороты, 3 прыжка носителя): дрейф щипцов относительно LeftHand 6.3e-06, модель↔носитель 7.6e-06, наклон 0, ошибка суставов 4.8e-07; отпускание и повторная постановка через `DadModelBuilder.PlaceAt`: подошвы 0, HRP (−14, 3.05, 0), дрейф щипцов 3.4e-07, суставы 2.1e-06; все части `CanCollide=false` на время теста |
| Коллизии реквизита | PASS: щипцы CanCollide/CanQuery/CanTouch = false; на проверенном переносе реквизит не мешал носителю |
| Сохранение review-place, закрытие, повторное открытие того же файла | PASS: `Desktop\GrillDad_Final_Evidence\GrillDad_Final_Review.rbxl` (Rojo-сборка проекта, 387 653 Б); после повторного открытия `ServerStorage.GrillDadFinal`: 17 частей, подошвы 6e-08, стык 4.8e-07, OriginalPosition 30/0, крепление, цвета |
| Вставка `.rbxm` во второе чистое место | PASS: Baseplate, Import Roblox Model: 17 частей, стыки 4.8e-07, OriginalPosition 30/0, TongsGrip, цвета, относительные смещения те же (Studio поднял модель на 1.0) |
| Ассеты (owner, существование) | PASS по economy API: 17 ассетов (16 мешей + `base_color_texture` 81619007545015), владелец 3938337813, не публичные (`data/asset_availability_check.txt`) |
| Доступность у других игроков | **НЕ проверена**: загрузка вторым аккаунтом / в опубликованном experience не выполнялась. Для проверки есть приватный тестовый place `AssetAccessTest_Private` (PlaceId 140670601883840), но вход вторым аккаунтом невозможен без вашего участия; по правилам Roblox ассеты владельца должны грузиться в его experience — это правило платформы, не мой тест |
| Регрессия предыдущих отцов | модели и их файлы не менялись; ряд предпросмотра в F5 показал Regular, Office, Fisherman, Grill на своих позициях |
| Видео | `GrillDad_Final_F5_carry_test.mp4` — склейка кадров экрана (PowerShell CopyFromScreen, ≈4 кадра/с), Game Bar не использовался |
| Кадры | Studio (Edit, чистое место): `Studio_01..13`; F5 (штатный спавн): `F5_front/back/three_quarter/hand_closeup`; на кадре F5 «сзади» часть фигуры закрыта соседним отцом предпросмотра — чистая спина см. `Studio_03_back.png` |

## Зависимость от незакоммиченных файлов
Сборка и Rojo-mapping воспроизводятся из коммита. Для появления модели в F5 нужен вызывающий код: им служит временный предпросмотр в незакоммиченном `src/server/Services/DadService.lua` (чужое изменение, не в коммите). Без него `GrillDadFinal` лежит в ServerStorage, но никто его не спавнит.
