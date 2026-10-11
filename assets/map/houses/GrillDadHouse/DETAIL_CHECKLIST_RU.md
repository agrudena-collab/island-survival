# GrillDadHouse — чек-лист деталей (EVERY specified object / group)

Автоматически собран из `component_registry.json` (940 объектов) + ручная сверка с мастер-промптом.
Статус «построено» = объект с таким префиксом есть в билдере, FBX и в сохранённом `.rbxlx` (940 MeshPart, все заякорены).
Доказательства: реальные скриншоты Studio `GrillDadHouse_Studio_Review/screenshots/` (номера 01–18) и Blender-превью `previews/`.

## Сводка по группам

| Группа | Содержание |
|---|---|
| Structure | газон с вырезами, пол/плитка 2×2, стены с реальными проёмами, верхняя обвязка, угловые стойки, кирпичный цоколь |
| Roof | 6 пологих граней walm-крыши, свес/фасция, коньковый колпак, кирпичный дымоход с колпаком |
| Openings | 9 окон (рама/подоконник/импосты/стекло), 2 двойные двери (рама, створки, ручки, петли) |
| Living / Kitchen / Dining / Preparation | мебель и мелкие предметы по разделам 7.1–7.4 |
| StoryProps | колбасный трофей, детский рисунок, 3 семейных фото, фартуки и прихватка |
| Entry | прихожая (поднос, обувь, пакет, крючки, полка, ключи), 4 фонаря, 2 кашпо, дорожка |
| Patio | плитка, 4 столба/балки/10 планок перголы, стол, 4 стула, тарелки, шкафчик с соусами |
| Grill | тележка, колёса, топка, решётка, открытая крышка, ручка, полки, рукоятки, ОДНА сосиска |
| Garden / Fence | 8 кустов, 2 дерева, 2 фонаря, заборы с проходами 8,4 и 8,0 |
| ReferenceHelpers | 8 пустых-маркеров (в FBX не экспортируются) |

## Каждый префикс имён (количество реальных объектов)

| Префикс имён | Объектов | Группа | Статус | Доказательство |
|---|---|---|---|---|
| `Apron_Adult*` | 6 | StoryProps | построено | 11 + previews/photos_aprons.png |
| `Apron_Child*` | 4 | StoryProps | построено | 11 + previews/photos_aprons.png |
| `Apron_Hook*` | 3 | StoryProps | построено | 11 + previews/photos_aprons.png |
| `Apron_Mitt*` | 3 | StoryProps | построено | 11 + previews/photos_aprons.png |
| `Apron_Rail*` | 1 | StoryProps | построено | 11 + previews/photos_aprons.png |
| `Basket_Band*` | 2 | Living | построено | 07 |
| `Basket_Bottom*` | 1 | Living | построено | 07 |
| `Basket_Wall*` | 4 | Living | построено | 07 |
| `Book_1*` | 4 | Living | построено | 07 |
| `Book_2*` | 4 | Living | построено | 07 |
| `Book_3*` | 4 | Living | построено | 07 |
| `CoffeeFruit_1*` | 1 | Living | построено | — |
| `CoffeeFruit_2*` | 1 | Living | построено | — |
| `CoffeeFruit_3*` | 1 | Living | построено | — |
| `CoffeeFruitBowl*` | 1 | Living | построено | — |
| `CoffeePlant_Leaf*` | 5 | Living | построено | — |
| `CoffeePlant_Pot*` | 1 | Living | построено | — |
| `CoffeePlant_Soil*` | 1 | Living | построено | — |
| `CoffeePlant_Stem*` | 1 | Living | построено | — |
| `CoffeeTable_Apron*` | 4 | Living | построено | — |
| `CoffeeTable_Leg*` | 4 | Living | построено | — |
| `CoffeeTable_Top*` | 1 | Living | построено | — |
| `DiningChair_FrontA*` | 9 | Dining | построено | — |
| `DiningChair_FrontB*` | 9 | Dining | построено | — |
| `DiningChair_RearA*` | 9 | Dining | построено | — |
| `DiningChair_RearB*` | 9 | Dining | построено | — |
| `DiningNapkin_1*` | 2 | Dining | построено | — |
| `DiningNapkin_2*` | 2 | Dining | построено | — |
| `DiningPlant_Leaf*` | 5 | Dining | построено | — |
| `DiningPlant_Pot*` | 1 | Dining | построено | — |
| `DiningPlant_Soil*` | 1 | Dining | построено | — |
| `DiningPlant_Stem*` | 1 | Dining | построено | — |
| `DiningPlate_1*` | 1 | Dining | построено | — |
| `DiningPlate_2*` | 1 | Dining | построено | — |
| `DiningPlate_3*` | 1 | Dining | построено | — |
| `DiningPlate_Dad*` | 1 | Dining | построено | — |
| `DiningTable_Apron*` | 4 | Dining | построено | — |
| `DiningTable_Leg*` | 4 | Dining | построено | — |
| `DiningTable_Top*` | 1 | Dining | построено | — |
| `Door_Front*` | 20 | Openings | построено | 05,06 (+числа) |
| `Door_Rear*` | 20 | Openings | построено | 05,06 (+числа) |
| `Drawing_Backing*` | 1 | StoryProps | построено | 07,12 + previews/family_story.png |
| `Drawing_Border*` | 4 | StoryProps | построено | 07,12 + previews/family_story.png |
| `Drawing_Dad*` | 7 | StoryProps | построено | 07,12 + previews/family_story.png |
| `Drawing_Figure*` | 6 | StoryProps | построено | 07,12 + previews/family_story.png |
| `Drawing_Grill*` | 4 | StoryProps | построено | 07,12 + previews/family_story.png |
| `Drawing_Paper*` | 1 | StoryProps | построено | 07,12 + previews/family_story.png |
| `Drawing_Sun*` | 1 | StoryProps | построено | 07,12 + previews/family_story.png |
| `Drawing_SunRay*` | 6 | StoryProps | построено | 07,12 + previews/family_story.png |
| `Entry_Bag*` | 3 | Entry | построено | 01,05 |
| `Entry_CoatPeg*` | 3 | Entry | построено | 01,05 |
| `Entry_CoatStrip*` | 1 | Entry | построено | 01,05 |
| `Entry_FrontPath*` | 2 | Entry | построено | 01,05 |
| `Entry_Key*` | 4 | Entry | построено | 01,05 |
| `Entry_KeyShelf*` | 1 | Entry | построено | 01,05 |
| `Entry_Lantern*` | 24 | Entry | построено | 01,05 |
| `Entry_Planter*` | 18 | Entry | построено | 01,05 |
| `Entry_ShoeAdult*` | 4 | Entry | построено | 01,05 |
| `Entry_ShoeChild*` | 4 | Entry | построено | 01,05 |
| `Entry_ShoeTray*` | 5 | Entry | построено | 01,05 |
| `Fence_Front*` | 4 | Fence | построено | 01,15 |
| `Fence_Rear*` | 2 | Fence | построено | 01,15 |
| `Fence_Side*` | 4 | Fence | построено | 01,15 |
| `FloorLamp_Base*` | 1 | Living | построено | 07 |
| `FloorLamp_Shade*` | 1 | Living | построено | 07 |
| `FloorLamp_Stem*` | 1 | Living | построено | 07 |
| `Fridge_Body*` | 1 | Kitchen | построено | 08 |
| `Fridge_DoorHigh*` | 1 | Kitchen | построено | 08 |
| `Fridge_DoorLow*` | 1 | Kitchen | построено | 08 |
| `Fridge_Foot*` | 4 | Kitchen | построено | 08 |
| `Fridge_Handle*` | 2 | Kitchen | построено | 08 |
| `Fridge_Seam*` | 1 | Kitchen | построено | 08 |
| `Grill_Axle*` | 2 | Grill | построено | 13 + previews/grill_closeup.png |
| `Grill_Cart*` | 9 | Grill | построено | 13 + previews/grill_closeup.png |
| `Grill_Firebox*` | 5 | Grill | построено | 13 + previews/grill_closeup.png |
| `Grill_Foot*` | 2 | Grill | построено | 13 + previews/grill_closeup.png |
| `Grill_Grate*` | 3 | Grill | построено | 13 + previews/grill_closeup.png |
| `Grill_Knob*` | 6 | Grill | построено | 13 + previews/grill_closeup.png |
| `Grill_Lid*` | 5 | Grill | построено | 13 + previews/grill_closeup.png |
| `Grill_LidHandle*` | 3 | Grill | построено | 13 + previews/grill_closeup.png |
| `Grill_LidHinge*` | 2 | Grill | построено | 13 + previews/grill_closeup.png |
| `Grill_Mitt*` | 3 | Grill | построено | 13 + previews/grill_closeup.png |
| `Grill_MittHook*` | 1 | Grill | построено | 13 + previews/grill_closeup.png |
| `Grill_Sausage*` | 3 | Grill | построено | 13 + previews/grill_closeup.png |
| `Grill_SideShelf*` | 2 | Grill | построено | 13 + previews/grill_closeup.png |
| `Grill_TongHook*` | 1 | Grill | построено | 13 + previews/grill_closeup.png |
| `Grill_Tongs*` | 5 | Grill | построено | 13 + previews/grill_closeup.png |
| `Grill_Wheel*` | 2 | Grill | построено | 13 + previews/grill_closeup.png |
| `Kitchen_Counter*` | 15 | Kitchen | построено | 08 |
| `Kitchen_Countertop*` | 4 | Kitchen | построено | 08 |
| `Kitchen_Cupboard*` | 9 | Kitchen | построено | 08 |
| `Kitchen_DishShelf*` | 3 | Kitchen | построено | 08 |
| `Kitchen_Faucet*` | 4 | Kitchen | построено | 08 |
| `Kitchen_Hob*` | 5 | Kitchen | построено | 08 |
| `Kitchen_Jar*` | 2 | Kitchen | построено | 08 |
| `Kitchen_Mug*` | 12 | Kitchen | построено | 08 |
| `Kitchen_Pan*` | 2 | Kitchen | построено | 08 |
| `Kitchen_Sink*` | 9 | Kitchen | построено | 08 |
| `Kitchen_Towel*` | 4 | Kitchen | построено | 08 |
| `Kitchen_TowelRail*` | 3 | Kitchen | построено | 08 |
| `PathLantern_1*` | 4 | Entry | построено | 01,05 |
| `PathLantern_2*` | 4 | Entry | построено | 01,05 |
| `Patio_Paving*` | 3 | Patio | построено | 02,14,15 |
| `Patio_RearPath*` | 3 | Patio | построено | 02,14,15 |
| `PatioCabinet_Back*` | 1 | Patio | построено | — |
| `PatioCabinet_Base*` | 1 | Patio | построено | — |
| `PatioCabinet_Divider*` | 1 | Patio | построено | — |
| `PatioCabinet_Door*` | 2 | Patio | построено | — |
| `PatioCabinet_Handle*` | 2 | Patio | построено | — |
| `PatioCabinet_Side*` | 2 | Patio | построено | — |
| `PatioCabinet_Top*` | 1 | Patio | построено | — |
| `PatioCenterPlant_Leaf*` | 5 | Patio | построено | — |
| `PatioCenterPlant_Pot*` | 1 | Patio | построено | — |
| `PatioCenterPlant_Soil*` | 1 | Patio | построено | — |
| `PatioCenterPlant_Stem*` | 1 | Patio | построено | — |
| `PatioChair_FrontA*` | 9 | Patio | построено | — |
| `PatioChair_FrontB*` | 9 | Patio | построено | — |
| `PatioChair_RearA*` | 9 | Patio | построено | — |
| `PatioChair_RearB*` | 9 | Patio | построено | — |
| `PatioPlate_1*` | 1 | Patio | построено | — |
| `PatioPlate_2*` | 1 | Patio | построено | — |
| `PatioPlate_3*` | 1 | Patio | построено | — |
| `PatioPlate_Dad*` | 1 | Patio | построено | — |
| `PatioPot_1*` | 9 | Patio | построено | — |
| `PatioPot_2*` | 9 | Patio | построено | — |
| `PatioSauce_1*` | 3 | Patio | построено | — |
| `PatioSauce_2*` | 3 | Patio | построено | — |
| `PatioTable_Apron*` | 4 | Patio | построено | — |
| `PatioTable_Leg*` | 4 | Patio | построено | — |
| `PatioTable_Top*` | 1 | Patio | построено | — |
| `Pergola_Beam*` | 4 | Patio | построено | 02,14 |
| `Pergola_Post*` | 4 | Patio | построено | 02,14 |
| `Pergola_Slat*` | 10 | Patio | построено | 02,14 |
| `Photo_1*` | 12 | StoryProps | построено | 07,04 + previews/photos_left.png |
| `Photo_2*` | 12 | StoryProps | построено | 07,04 + previews/photos_left.png |
| `Photo_3*` | 12 | StoryProps | построено | 07,04 + previews/photos_left.png |
| `Prep_Bowl*` | 1 | Preparation | построено | 10 + preview kitchen |
| `Prep_Cooktop*` | 3 | Preparation | построено | 10 + preview kitchen |
| `Prep_Counter*` | 25 | Preparation | построено | 10 + preview kitchen |
| `Prep_CuttingBoard*` | 1 | Preparation | построено | 10 + preview kitchen |
| `Prep_Flue*` | 1 | Preparation | построено | 10 + preview kitchen |
| `Prep_Hood*` | 4 | Preparation | построено | 10 + preview kitchen |
| `Prep_SecretJar*` | 5 | Preparation | построено | 10 + preview kitchen |
| `Prep_SpiceJar*` | 15 | Preparation | построено | 10 + preview kitchen |
| `Prep_Tongs*` | 7 | Preparation | построено | 10 + preview kitchen |
| `Prep_Utensil*` | 11 | Preparation | построено | 10 + preview kitchen |
| `Prep_UtensilRail*` | 3 | Preparation | построено | 10 + preview kitchen |
| `Roof_Chimney*` | 4 | Roof | построено | 01,16,06 |
| `Roof_Fascia*` | 6 | Roof | построено | 01,16,06 |
| `Roof_Hip*` | 6 | Roof | построено | 01,16,06 |
| `Roof_Ridge*` | 1 | Roof | построено | 01,16,06 |
| `Rug_Dining*` | 5 | Dining | построено | 07,09 |
| `Rug_Living*` | 5 | Living | построено | 07,09 |
| `Shelf_Back*` | 1 | Living | построено | 07,12 |
| `Shelf_Board*` | 3 | Living | построено | 07,12 |
| `Shelf_Side*` | 2 | Living | построено | 07,12 |
| `Shrub_Front*` | 16 | Garden | построено | 01,02 |
| `Shrub_Side*` | 16 | Garden | построено | 01,02 |
| `Sofa_Rear*` | 14 | Living | построено | 07,04 |
| `Sofa_Side*` | 13 | Living | построено | 07,04 |
| `Structure_Brick*` | 24 | Structure | построено | screens 01,02,03,16 + previews/front.png |
| `Structure_BrickMortar*` | 12 | Structure | построено | screens 01,02,03,16 + previews/front.png |
| `Structure_CornerPost*` | 10 | Structure | построено | screens 01,02,03,16 + previews/front.png |
| `Structure_Floor*` | 4 | Structure | построено | screens 01,02,03,16 + previews/front.png |
| `Structure_Ground*` | 1 | Structure | построено | screens 01,02,03,16 + previews/front.png |
| `Structure_Wall*` | 38 | Structure | построено | screens 01,02,03,16 + previews/front.png |
| `Structure_WallPlate*` | 10 | Structure | построено | screens 01,02,03,16 + previews/front.png |
| `ToyBlock_1*` | 1 | Living | построено | 07 |
| `ToyBlock_2*` | 1 | Living | построено | 07 |
| `ToyBlock_3*` | 1 | Living | построено | 07 |
| `ToyCar_Body*` | 1 | Living | построено | 07 |
| `ToyCar_Cabin*` | 1 | Living | построено | 07 |
| `ToyCar_Wheel*` | 4 | Living | построено | 07 |
| `Tree_1*` | 6 | Garden | построено | 01,02 |
| `Tree_2*` | 6 | Garden | построено | 01,02 |
| `Trophy_Base*` | 1 | StoryProps | построено | 07,12 |
| `Trophy_Sausage*` | 5 | StoryProps | построено | 07,12 |
| `Trophy_SausageBand*` | 2 | StoryProps | построено | 07,12 |
| `Trophy_Stem*` | 1 | StoryProps | построено | 07,12 |
| `TV_Display*` | 1 | Living | построено | 07,12 |
| `TV_Frame*` | 1 | Living | построено | 07,12 |
| `TV_Stand*` | 2 | Living | построено | 07,12 |
| `TVCabinet_Back*` | 1 | Living | построено | — |
| `TVCabinet_Bottom*` | 1 | Living | построено | — |
| `TVCabinet_Divider*` | 2 | Living | построено | — |
| `TVCabinet_Foot*` | 4 | Living | построено | — |
| `TVCabinet_Handle*` | 1 | Living | построено | — |
| `TVCabinet_PanelClosed*` | 1 | Living | построено | — |
| `TVCabinet_Shelf*` | 1 | Living | построено | — |
| `TVCabinet_Side*` | 2 | Living | построено | — |
| `TVCabinet_Top*` | 1 | Living | построено | — |
| `Window_ChamferL*` | 7 | Openings | построено | 01,02,04 |
| `Window_ChamferR*` | 7 | Openings | построено | 01,02,04 |
| `Window_FrontL*` | 7 | Openings | построено | 01,02,04 |
| `Window_FrontR*` | 7 | Openings | построено | 01,02,04 |
| `Window_Left*` | 8 | Openings | построено | 01,02,04 |
| `Window_RearL*` | 8 | Openings | построено | 01,02,04 |
| `Window_RearR*` | 7 | Openings | построено | 01,02,04 |
| `Window_Right*` | 8 | Openings | построено | 01,02,04 |

## Известные приближения / отклонения (см. также manifest.json → documented_adjustments)

- Боковые заборы начинаются на D=0,8 (а не 0,6), чтобы первая стойка стояла вплотную к угловой стойке переднего забора, а не пересекала её.
- Коннектор семейной площадки 02 смещён на D=13,1..16,1 (ширина 3), чтобы не упираться в боковой диван (его край D=16,2).
- Графика на стенах стоит на плоскости опоры X=−14,58 (рисунок/фото) и X=14,52 (рейка фартуков), как в спецификации; рамка-основание касается стены X=±14,6.
- Сосиска-трофей собрана из пяти соединённых наклонных сегментов (изогнутая форма), сосиска на гриле — одна капсула 0,55×0,14 с двумя полосами.
- Дымоход внутри комнаты открыт до коньковой зоны; воздуховод 0,45 входит в его низ (H 11,8..12,5) без зазора.
- Прозрачность стекла: Roblox Transparency 0,65 (Material=Glass).
