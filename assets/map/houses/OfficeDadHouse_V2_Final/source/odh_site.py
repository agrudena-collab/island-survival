"""OfficeDadHouse_V2_Final -- lot: lawn, fences, front path, driveway with the car (work pass), back yard (ladder spot, patio, shed, dog house), trees.
Plot coordinates: x east, z toward the back yard, the street is at z < 0.  Lot x 0..LOT_W, z 0..LOT_D."""
import math
import odh_core as K
from odh_core import *
import odh_models as M
import odh_car as CAR
import odh_detail as D
from odh_house import X, Z

LOT_W, LOT_D = 104.0, 100.0
S_ = 'Site'
DRIVE = (4.0, 22.0)          # driveway x range
FRONT_GATE = (43.0, 51.0)    # open gap in the front fence (path to the porch)
BACK_GATE = (58.0, 72.0)     # open gap in the back fence
FZ = 1.5                     # front fence line z


def place(fn, x, z, rot=0.0, *a, c=S_, y0=0.0, **k):
    K.tf_push(x, z, y0, rot)
    r = fn(c, *a, **k)
    K.tf_pop()
    return r


def slab(color, x0, x1, z0, z1, h0=0.0, h1=0.1, solid=False):
    B(S_, color, x0, x1, h0, h1, z0, z1, solid=solid)


def fence_all():
    segs = [(0.0, FZ, DRIVE[0], FZ), (DRIVE[1], FZ, FRONT_GATE[0], FZ), (FRONT_GATE[1], FZ, LOT_W, FZ)]
    for (x0, z0, x1, z1) in segs:
        M.fence_line(S_, x0, z0, x1, z1)
    M.fence_line(S_, 0.0, FZ, 0.0, LOT_D)                    # west side
    M.fence_line(S_, LOT_W, FZ, LOT_W, LOT_D)                # east side
    M.fence_line(S_, 0.0, LOT_D, BACK_GATE[0], LOT_D)
    M.fence_line(S_, BACK_GATE[1], LOT_D, LOT_W, LOT_D)


CAR_SC = 1.0           # scale of the father's car
TREE_LOG = []          # (x, z, crown radius) of the lot trees, checked by the audit


def lot():
    B(S_, 'lawn', 0.0, LOT_W, -1.0, 0.0, 0.0, LOT_D, solid=True)
    # sidewalk across the whole frontage + kerb
    D.pavers(S_, -2.0, LOT_W + 2.0, -6.0, 0.0, -0.2, 0.12, 3.0, seed=1)
    slab('curb', -2.0, LOT_W + 2.0, -6.6, -6.0, -0.2, 0.25, solid=True)
    slab('curb_top', -2.0, LOT_W + 2.0, -6.48, -6.12, 0.25, 0.3)
    slab('gutter', -2.0, LOT_W + 2.0, -7.9, -6.6, 0.0, 0.03)
    D.tactile(S_, 44.0, 50.0, -6.0, -4.0, 0.12)
    # path from the gate to the porch
    D.pavers(S_, 44.0, 50.0, 0.0, 10.0, 0.0, 0.1, 3.0, tones=('walk', 'walk_b'), seed=3, solid=False)
    # driveway to the garage door (door in the garage west wall x = 22, z 65.5..77.5)
    D.pavers(S_, DRIVE[0], DRIVE[1], 0.0, 82.0, 0.0, 0.15, 4.5, tones=('walk_c', 'walk_b', 'walk_c'), seed=4, solid=False)
    slab('concrete', 2.0, 24.0, -0.2, 4.0, -0.1, 0.14)
    # back patio under the balcony and path to the back door
    D.pavers(S_, 56.0, 84.0, 83.8, 94.5, 0.0, 0.12, 3.0, seed=5, solid=False)
    D.pavers(S_, 61.0, 67.0, 94.5, LOT_D, 0.0, 0.1, 3.0, tones=('walk', 'walk_b'), seed=6, solid=False)
    # stepping stones to the shed and the dog house
    M.stepping_stones(S_, [(30.0, 86.0), (26.0, 88.5), (22.0, 90.5), (18.0, 91.5), (14.0, 91.5)], 5)
    fence_all()
    # hedges inside the side fences
    for (x, z0, z1) in ((1.9, 24.0, 58.0), (LOT_W - 1.9, 20.0, 95.0)):
        K.tf_push(x, (z0 + z1) / 2, 0, 90)
        M.hedge(D.ORG, z1 - z0, 3.0, 2.0, True, 3, 'x')
        K.tf_pop()
    # mail box and lamps on the sidewalk
    place(M.mailbox, 38.0, -3.0, 180)
    place(M.lamp_post, 24.0, -4.5, 0)
    place(M.lamp_post, 80.0, -4.5, 0)
    # lawn trees
    for (x, z, s, seed, kind) in ((30.0, 7.0, 1.0, 2, 'cherry'), (70.0, 6.0, 1.0, 7, 'oak'), (4.0, 96.0, 1.4, 9, 'autumn'),
                                  (103.0, 97.5, 0.8, 11, 'cherry'), (100.5, 60.0, 0.5, 12, 'oak'), (100.0, 4.0, 1.0, 4, 'autumn')):
        D.tree_at(x, z, s, seed, {'autumn': 'maple'}.get(kind, kind))
        TREE_LOG.append((x, z, 7.0 * s))
    place(M.flower_patch, 40.0, 5.0, 0, 3.5, 2.0, 5, c=D.ORG)
    place(M.flower_patch, 54.0, 5.0, 0, 3.5, 2.0, 6, c=D.ORG)
    place(M.flower_patch, 37.0, 11.5, 0, 7.0, 2.4, 8, c=D.ORG)
    place(M.flower_patch, 58.0, 11.5, 0, 7.0, 2.4, 9, c=D.ORG)
    D.planter(S_, 20.0, -4.0, 0)
    D.planter(S_, 84.0, -4.0, 0)
    # back yard: patio furniture, shed, dog house, raised bed, clothesline
    place(M.picnic_table, 68.0, 90.0, 0, True) if False else None
    place(M.bbq, 58.5, 91.5, 180)
    place(M.picnic_table, 68.5, 91.0, 90, False)   # clear of the balcony ladder spot at x 75
    place(M.garden_shed, 90.0, 92.0, 180)
    K.ANCH.pop('shed_door', None)
    K.ANCH.pop('shed_key', None)
    place(M.doghouse, 12.0, 90.0, 0)
    place(M.raised_bed, 34.0, 94.0, 0, 8.0, 3.0)
    place(M.raised_bed, 42.0, 94.0, 0, 6.0, 3.0)
    place(M.birdbath, 50.0, 91.0, 0)
    place(M.bench, 58.0, 96.5, 180)
    # play area and garden dressing (front lawn east side, back yard)
    place(M.swing_set, 84.0, 9.0, 0)
    place(M.sandbox, 94.5, 9.0, 0)
    place(M.birdhouse, 60.0, 12.5, 0)
    place(M.gnome, 40.0, 7.4, 0)       # in front of the flower bed (z 4..6), facing it
    place(M.gnome, 54.0, 7.4, 0)
    place(M.clothesline, 27.0, 96.5, 0)


def car_with_pass():
    """navy car on the driveway, nose to the street; the work pass lies on the dashboard (SpareKey part 'WorkPass')"""
    cx, cz = 12.5, 34.0
    K.tf_push(cx, cz, 0.0, 180)
    CAR.dad_car('DadCar', sc=CAR_SC)
    K.COLL.append(('box', cx, cz, 6.6 * CAR_SC, 15.4 * CAR_SC, 4.9 * CAR_SC))
    K.tf_pop()
    K.ANCH['work_pass_door'] = (cx + 4.3, 0.0, cz + 1.0, -1.0, 0.0)     # standing spot at the driver's door (driver side, world +x after the 180 degree turn)
    # a briefcase-sized umbrella on the garden path is decor only
    place(M.trash_can, 28.0, 3.0, 0)


def house_dressing():
    """exterior dressing of the house to match the detailed neighbours: cornices with dentils, quoins, stone base course, downspouts"""
    from odh_core import CEIL1, CEIL2, F2
    from odh_house import W, D as HD
    zf = Z(-0.75)
    D.cornice(S_, X(0.0), X(W), CEIL2 - 3.4, zf, -1, 0, 0)
    D.cornice(S_, X(0.0), X(W), F2 - 1.6, zf, -1, 0, 0)
    D.quoins(S_, X(-0.75), zf, -1, 1.0, CEIL2 - 3.6, 1)
    D.quoins(S_, X(W + 0.75), zf, -1, 1.0, CEIL2 - 3.6, -1)
    for (u0, u1) in ((-0.75, 1.5), (12.5, W + 0.75)):
        B(S_, 'stone_dk', X(u0), X(u1), 1.0, 4.0, Z(-1.15), Z(-0.75), solid=False)
    B(S_, 'stone_dk', X(W + 0.75), X(W + 1.15), 1.0, 4.0, Z(-0.75), Z(HD + 0.75), solid=False)
    for u in (-0.1, W + 0.1):
        D.downspout(S_, X(u), Z(-1.0), CEIL2)


def site():
    lot()
    house_dressing()
    car_with_pass()
    # ladder spot (mark only: the Studio script builds SpotPart / Ladder / ClimbTruss at the anchors)
    K.tf_push(X(35.0), Z(75.0), 0.0, 0)
    K.rbox('plinth', 0, 0, 0.0, 4.4, 0.12, 2.6, 0.04, 1, c=S_)
    K.tf_pop()
    # markers (no geometry): lot bounds, caught spawn
    K.ANCH['lot_centre'] = (LOT_W / 2, 0.0, LOT_D / 2, 0.0, 1.0)
    K.ANCH['caught_spawn'] = (35.0, 1.0, 6.0, 0.0, 1.0)
    K.ROUTES.extend([
        ('Wife', 1, 64.0, F1, 44.5, 5, 'Cook'), ('Wife', 2, 86.5, F1, 44.0, 3, None), ('Wife', 3, 70.0, F1, 30.0, 4, None),
        ('Son', 1, 64.0, F2, 46.0, 4, 'Fidget'), ('Son', 2, 50.5, F2, 30.0, 2, None), ('Son', 3, 72.0, F1, 24.0, 4, 'Fidget'), ('Son', 4, 50.5, F2, 30.0, 2, None),
        ('Dog', 1, 18.0, 0.0, 90.0, 4, None), ('Dog', 2, 40.0, 0.0, 92.0, 3, None), ('Dog', 3, 64.0, 0.0, 90.0, 3, None),
    ])
