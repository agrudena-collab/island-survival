"""render the review frames: python -I render_review.py OUTDIR [which...]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import odh_core as K, odh_scene as S, build_odh as BO
from odh_core import F1, F2
from odh_house import X, Z
import bpy

out = sys.argv[1]
only = set(sys.argv[2:])
os.makedirs(out, exist_ok=True)
BO.build()
S.clear(); S.materialize(); S.setup_scene(res=(1280, 800), samples=int(os.environ.get('SAMPLES', '16')), sun_energy=3.0)
S.add_room_lights(True, 1.6)
G, U = F1, F2
SHOTS = {
    '01_street_front': ((30, 24, -36), (60, 10, 16), 24, ()),
    '02_back_yard_ladder': ((10, 42, 132), (66, 10, 72), 26, ()),
    '03_driveway_car_pass': ((6, 14, 10), (14, 3, 36), 30, ()),
    '04_biome_overview': ((52, 230, -150), (52, 0, -10), 30, ()),
    '05_supermarket_bank': ((52, 90, -10), (-10, 4, -90), 30, ()),
    '10_foyer': ((X(9.5), G + 5.5, Z(13.5)), (X(3), G + 4, Z(2.5)), 18, ()),
    '11_hall_stairs': ((X(12.5), G + 6.0, Z(43)), (X(5), G + 5, Z(22)), 20, ()),
    '12_living': ((X(52), G + 6.0, Z(2)), (X(30), G + 4, Z(14)), 20, ()),
    '13_kitchen': ((X(32.5), G + 6.0, Z(42.5)), (X(20), G + 3.5, Z(30)), 20, ()),
    '14_dining': ((X(36), G + 6.0, Z(42)), (X(48), G + 3.5, Z(32)), 20, ()),
    '15_library': ((X(36.5), G + 6.0, Z(46)), (X(48), G + 4, Z(58)), 20, ()),
    '16_utility_cupboard': ((X(32.5), G + 6.0, Z(46)), (X(10), G + 4, Z(60)), 20, ()),
    '17_garage': ((X(-2), 6.0, Z(46)), (X(-12), 3, Z(60)), 20, ()),
    '20_master': ((X(44), U + 6.5, Z(2.8)), (X(26), U + 3.5, Z(16)), 20, ()),
    '21_master_wardrobe': ((X(40), U + 5.5, Z(10)), (X(50), U + 4, Z(18)), 22, ()),
    '22_kid': ((X(32.5), U + 6.0, Z(23.5)), (X(20), U + 3, Z(32)), 20, ()),
    '23_bath': ((X(35.5), U + 6.0, Z(23.5)), (X(48), U + 3, Z(32)), 20, ()),
    '24_lounge_niche': ((X(16), U + 7.0, Z(50.5)), (X(30), U + 3.5, Z(42)), 20, ()),
    '25_guest': ((X(37), U + 6.0, Z(51)), (X(46), U + 3, Z(40)), 20, ()),
    '26_office_father': ((X(47), U + 6.5, Z(56.0)), (X(24), U + 4, Z(63.5)), 20, ()),
    '27_upper_hall': ((X(12), U + 6.0, Z(66)), (X(7), U + 3, Z(35)), 20, ()),
    '30_plan_ground': ((58, 170, 42), (58, 0, 42.01), 50, ('Roof', 'Upper', 'Furn_U', 'FatherProxy', 'DoorLeafU')),
    '31_plan_upper': ((67, 170, 36), (67, 0, 36.01), 50, ('Roof', 'FatherProxy')),
}
for name, (loc, tgt, lens, hide) in SHOTS.items():
    if only and not any(name.startswith(o) for o in only):
        continue
    S.shot(os.path.join(out, name + '.png'), loc, tgt, lens=lens, hide=hide)
print('done')
