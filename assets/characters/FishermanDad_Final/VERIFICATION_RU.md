# VERIFICATION_RU — Fisherman Dad Final (16.10.2026)

| Проверка | Результат |
|---|---|
| `git diff --check` | PASS (только предупреждения LF→CRLF) |
| `rojo build default.project.json` | PASS (дважды: до и после правки `PlaceAt`) |
| Билдер воспроизводит принятую модель | PASS: палитра и 5 JSON побайтово совпали; 6 840 / 2 084 / 588 тр.; `.rbxm` Final = `.rbxm` review (cmp) |
| Появление через штатный путь (`DadModelBuilder.Build("GardenerDad")` → `PlaceAt`, F5) | PASS: 18 частей, лишних частей 0, старых накладок (Mug/Briefcase/Shovel/Apron/Brim/Tie) 0, подпись «Fisherman Dad (Uncommon)», FeetOffset 2.92 |
| Подошвы на полу | PASS: −3e-08 (`TestGround` на Y=0, только в тестовом place) |
| Целостность позы / суставы | PASS: 15 AnimationConstraint, ошибка ≤ 1.9e-06; OriginalPosition 30 проверено, 0 расхождений (JointRotation — служебные) |
| Цвета | PASS: 15 SurfaceAppearance (ColorMap), удочка и ведро — TextureID палитры; MeshPart.Color (0.639,0.635,0.647) как у Regular/Office; кадры F5 показывают корректные цвета |
| Крепления | PASS: RodGrip LeftHand→FishingRod, BucketMount HRP→Bucket; rod rel hand (−0.431, 0.2265, −0.0125), bucket rel HRP (−3, −2.34, 0.092) неизменны после спавна |
| Коллизии реквизита | PASS: CanCollide/CanQuery/CanTouch = false, Massless = true; QA-перенос шёл с CanCollide=false всех частей |
| Перенос — QA-тест приваривания к игроку (НЕ игровая механика; механики переноса в проекте нет) | PASS: 22 с, 4 перехода по 14 стад, повороты, 3 прыжка, ~1 200 замеров: дрейф удочка↔кисть 7.7e-06, HRP↔ведро 6.7e-06, модель↔носитель 7.6e-06, наклон 0, ошибка суставов 3.9e-06; отпускание и повторная постановка через `DadModelBuilder.PlaceAt`: подошвы −3e-08, HRP (−14, 2.92, 0), дрейф удочки 3.8e-06, ведра 7e-09 |
| Сохранение review-place, закрытие, повторное открытие того же файла | PASS: `Desktop\FishermanDad_Final_Evidence\FishermanDad_Final_Review.rbxl` (Rojo-сборка проекта, 336 759 Б); после повторного открытия `ServerStorage.FishermanDadFinal`: 18 частей, подошвы −6e-08, стык 2.4e-07, OriginalPosition 30/0, крепления, цвета |
| Вставка `.rbxm` во второе чистое место | PASS: Baseplate, Import Roblox Model: 18 частей, 15 стыков 1.2e-07, OriginalPosition 30/0, RodGrip/BucketMount, цвета, относительные смещения те же (Studio поднял модель на 1.0 — относительные величины совпали) |
| Ассеты (owner, существование) | PASS по economy API: 18 ассетов (17 мешей + `base_color_texture`), владелец 3938337813, не публичные (`data/asset_availability_check.txt`) |
| Доступность у других игроков | **НЕ проверена**: приватный тестовый experience опубликован (PlaceId 140670601883840, UniverseId 10771195781), вход вторым аккаунтом не выполнялся; по правилам Roblox ассеты владельца должны грузиться в его experience, но это не тест |
| Регрессия Regular/Office | модели не менялись; общая правка `PlaceAt` проверена: после неё в ряду предпросмотра все отцы стоят на своих позициях (кадры `F5_*`) |
| Видео | `FishermanDad_Final_F5_carry_test.mp4` — склейка кадров экрана, PowerShell CopyFromScreen ≈ 4 кадра/с, кадры обрезаны до окна Studio (Game Bar не разрешён) |

## Найденный и исправленный дефект
При размещении через `PlaceAt` у финальных отцов двигался только `HumanoidRootPart` (в F5: HRP x=20, голова x=0, `Bucket` остался в x=−3; суставная ошибка 20 стад; то же для Regular/Office). Эксперимент в Studio: «якорить → PivotTo» двигает все части, «PivotTo → якорить» — только корень. Порядок в `PlaceAt` исправлен.

## Зависимость от незакоммиченных файлов
Сборка и Rojo-mapping воспроизводятся из коммита. Для визуального появления в F5 нужен вызывающий код: в проекте им служит временный предпросмотр в незакоммиченном `src/server/Services/DadService.lua` (чужое изменение, не в коммите). Без него модель в ServerStorage есть, но никто её не спавнит.
