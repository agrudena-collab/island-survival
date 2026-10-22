# RegularDadDistrict — район вокруг дома любовницы Regular Dad

Процедурно собранный район 500×500 стад. (Blender → FBX → Studio). Все числа и расстановка — прототип, на согласование.

## Состав
- `source/dlib.py` — геометрическая библиотека (боксы, цилиндры, тела вращения, сферы, призмы).
- `source/build_district.py` — палитра, окна/балконы/карнизы/витрины/двери, здание, уличная мебель, машины.
- `source/layout.py` — раскладка: дороги, кварталы, парк, площади, служебные улицы, второй ряд домов.
- `source/export_part.py` — разбиение на чанки ≤ 9000 треугольников, экспорт FBX, `district.json`, рендеры.
- `out/` — `RDD_District.fbx`, `district.json`, `renders/`.
- `model/RegularDadDistrict.rbxm` — готовая модель для Rojo (`Workspace.RegularDadDistrict`).

## Пересборка
```
blender -b --factory-startup --python source\build_district.py -- <абсолютный путь к out>
```
Затем в Studio: Ctrl+M → `out/RDD_District.fbx` → Import; модель повернуть на 180° вокруг Y в начале координат
(`PivotTo(CFrame.Angles(0, math.pi, 0))`), раскрасить MeshPart в белый, `G_*` — Glass 0.55, `N_*` — Neon,
коллайдеры/вывески/фонари/якоря создать из `district.json`.

## Содержимое модели
- `Meshes` — 314 MeshPart (`O_` непрозрачные, `G_` стекло, `N_` неон), без коллизий.
- `Colliders` — невидимые боксы для физики; `Signs`, `Lights` (теги `DistrictLamp`), `Anchors`.
- `MistressBuilding1` — `Interior` (квартира, смещена на (800,0,800)) и `Exterior`: `Entrance` (`ApartmentEntrance`),
  `ExitArrival`, `BagShop` (`HeistBagShop`), `LadderGiver` (`HeistLadderGiver`).
- Башня любовницы: прямоугольник x −120…−80, z −92…−62, вход (−100, 1.55, −58.6).

## Аудит и заполнение
- `source/audit.py` запускается автоматически: пишет `out/audit.txt` (пересечения коллайдеров, кроны, мебель на дороге, машины вне асфальта, карта занятости). Цель — `ISSUES 0`.
- `source/fillers.py` — инфраструктура для пустот: заправка, двор-парковка, проходы, огород, воркаут, корты, беседка, скейт, площадка для собак, периметр.
- `studio_setup.luau` — воспроизводимая настройка модели в Studio после импорта FBX (см. заголовок файла).

## Известные ограничения
- ≈1.37 млн треугольников: для слабых устройств нужен StreamingEnabled/упрощение.
- Фонарные PointLight выключены (ночного цикла нет).
- Gym-сервис к зданию спортзала пока не привязан; дом Regular Dad в район не встроен.
