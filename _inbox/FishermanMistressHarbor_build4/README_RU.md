# Гавань build4 (башня под квартиру 64x40)

Башня увеличена под квартиру любовницы, остров вырос (R 54). Площадь, пальмы, клумбы, скамейки, тайный пирс переставлены.
Аудит: flicker_pairs 1 (известная невидимая грань скалы), door_issues 0, walk_issues 0.

Studio:
1. Удалить старую модель FishermanMistressHarbor, импортировать export/FishermanMistressHarbor.fbx (Upload to Roblox выкл).
2. Command Bar / ModuleScript по очереди: apply_harbor_colors, build_harbor_colliders_anchors, camera_block, biome_setup_harbor.
3. Дальше квартира: см. ../MistressApartmentHarbor/studio/README_RU.md
