# Квартира любовницы #3 (Гавань) — Studio пак (v2, под прежнюю башню build3)

Башня в биоме — прежняя, тонкая (FishermanMistressHarbor_build3). build4 (широкая башня) НЕ использовать.
Квартира — отдельная модель, спрятана далеко: origin (-15000, 300, 15000), игрок её не видит. В окнах облегчённая копия Гавани build3
(без коллизий и теней) — вид как с верхушки башни. Стены/пол/потолок/стекло твёрдые для камеры.
Вид за окнами: копия Гавани build3 с мелкими деталями (VIEW_MIN 1.5) + фасад башни под квартирой (как будто ты на верхнем этаже). ~288k tris вместе с видом.
Аудит: flicker 0, walk 0, doors 0, invisible 0.

Порядок:
0. В плейсе стоит биом build3 и уже запущен его build_harbor_colliders_anchors (нужны Anchors.tower_entrance / tower_exit_arrival).
1. File > Import 3D: export/MistressFlat3.fbx (Upload to Roblox выкл) -> Workspace.MistressFlat3.
2. ModuleScript, Source = scripts/studio_setup_flat3.luau. В Command Bar:
   require(путь_к_модулю)(<текст data/flat.json>, Vector3.new(-15000, 300, 15000))
   Создаст FishermanMistressHarbor.MistressBuilding3: Exterior.Entrance (тег ApartmentEntrance, кнопка «Войти» у двери башни),
   Exterior.ExitArrival, Interior (Arrival, ExitDoor тег ApartmentExit «Выйти», MistressSeat, GuestSeat, Table_Top тег MistressDesk, DadId=GardenerDad).
3. Play: подойти к двери башни -> «Войти» -> квартира; дверь «Выйти» -> снова у башни.

Заметки: ApartmentId не задан (решает владелец). Душевая — декор. Восточный проход у кровати узковат с мешком.
Перезапуск: удалить MistressBuilding3.Interior, импортировать FBX заново, запустить снова.
