# MistressFlat4 — квартира любовницы Grill Dad, build 1

Отдельная модель (как у рыбака), спрятана далеко: origin (-16000, 300, 16000). Вход — телепорт перед бирюзовой башней GrillMistressDistrict.
Просторная: 84 x 56 студов, потолок 13 (у квартиры рыбака 64 x 40, потолок 12).

## Комнаты
- Прихожая: дверь выхода (ExitDoor «Выйти»), консоль с зеркалом, крючки, фартук.
- Гостиная: большой угловой диван, круглый столик, ТВ-стена с иконкой гриля, камин с неоновым огнём, портрет Grill Dad с сердечком, кресло с торшером, книжный шкаф.
- Столовая: **стол любовницы** (Table_Top 5.2x5.2, тег MistressDesk, DadId=GrillDad), MistressSeat (север) и GuestSeat (юг) друг напротив друга,
  свечи, тортик-сердечко, люстра, буфет с золотой лопаткой.
- Кухня: столешницы вдоль окон и стены, варочная панель с вытяжкой, большой холодильник с магнитами, остров со встроенным грилем, сосиски, бургер, барные стулья, неон GRILL.
- Спальня: большая кровать, тумбы с лампами, шкаф, туалетный столик с зеркалом.
- Ванная: ванна с пеной и уточкой, двойная раковина, душ со стеклом, туалет, полотенца.
- Гардеробная: вешалки с одеждой, обувь, пуф, большое зеркало.
- Солнечная гостиная за широкой аркой: панорамные окна, бар со стульями и мини-грилем, подвесное кресло, диван, растения.
- За окнами: облегчённый вид района с высоты (земля, дороги, домики, деревья) — только декор, без коллизий.

## Проверки (2026-11-15, `data/audit_report.txt`)
мерцание 0, двери 0, проходимость 0 (r=1.25 и r=2.0 с отцом в мешке, 13 точек, из квартиры наружу не выйти), контракт полный, невидимых блоков 0.
196 мешей, 35 332 трис, FBX 1.4 МБ. 10 превью в `previews/` просмотрены.
**НЕ проверено:** Studio, Play, работа ApartmentService/камеры на этой модели.

## Порядок в Studio (только по команде Ivan)
0. Район уже стоит и прогнан `build_studio_colliders_anchors.luau` (нужны Anchors.ApartmentEntrance / ExitArrival).
1. File > Import 3D: `export/MistressFlat4.fbx` (Upload выкл) -> Workspace.MistressFlat4.
2. ModuleScript, Source = `scripts/studio_setup_flat4.luau`. В Command Bar: `require(путь_к_модулю)(<текст data/flat.json>)`.
   Создаст GrillMistressDistrict.MistressBuilding4: Exterior.Entrance (тег ApartmentEntrance, на телепорте), Exterior.ExitArrival,
   Interior (Arrival, ExitDoor, MistressSeat, GuestSeat, Table_Top, CamBounds с тегом ApartmentCamBounds, Colliders, Lights, WindowView).
3. Если в плейсе ещё нет `StarterPlayerScripts.ApartmentCameraClamp`, вставить LocalScript из `scripts/ApartmentCameraClamp.client.luau` (держит камеру в квартире).
4. Play: встать на телепорт -> «Войти» -> квартира; дверь «Выйти» -> снова у телепорта.
ApartmentId не задан (решает владелец).

## Пересборка
`blender -b --factory-startup --python source/build_flat.py -- <out>`, аудит `python source/audit_flat.py <out>`. Генератор комнат — `source/gm_flat.py`.
