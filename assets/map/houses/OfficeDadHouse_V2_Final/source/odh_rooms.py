"""OfficeDadHouse_V2_Final -- furniture, hide spots, niche, father proxy.  u east, v toward the back yard.
Local frame of every piece: it FACES +v at rot 0, +u at rot -90, -u at rot 90, -v at rot 180."""
import math
import odh_core as K
from odh_core import *
import odh_models as M
from odh_house import X, Z, GAR_FLOOR, GAR_CEIL, A

FG, FU = 'Furn_G', 'Furn_U'


class at:
    """with at(u, v, rot, floor): furniture helpers inside draw into the local frame of that spot"""
    def __init__(self, u, v, rot=0, floor=1, dy=0.0):
        self.u, self.v, self.rot, self.floor, self.dy = u, v, rot, floor, dy

    def __enter__(self):
        base = {1: F1, 2: F2, 0: GAR_FLOOR}[self.floor]
        K.CUR[0] = FU if self.floor == 2 else FG
        K.tf_push(X(self.u), Z(self.v), base + self.dy, self.rot)
        return K.CUR[0]

    def __exit__(self, *a):
        K.tf_pop()


def curtains(u, v, w, floor, axis='x', col='coral', wall_z=None):
    base = F1 if floor == 1 else F2
    c = FU if floor == 2 else FG
    M.curtain_pair(c, X(u) if axis == 'x' else Z(v), w, base + 9.8, 7.0, Z(v) if axis == 'x' else X(u), axis, col)


def wall_art(u, v, rot, floor, w, h, y, **k):
    with at(u, v, rot, floor) as c:
        K.tf_push(0, 0, y, 0)
        M.picture(c, w, h, **k)
        K.tf_pop()


# ---------------------------------------------------------------------------------------------------- ground floor
# Interior faces: west wall u0.75, east wall u53.25, partitions +-0.5 around their axis.  Door leaves sweep a quarter circle of radius = opening width
# on their swing side: no furniture there (checked by audit_all.py, section G).
def art(u, v, rot, floor, w, h, y, **k):
    wall_art(u, v, rot, floor, w, h, y, **k)


def pend(u, v, floor, col='brass', drop=2.2):
    with at(u, v, 0, floor) as c:
        K.tf_push(0, 0, CH - 0.35, 0); M.pendant(c, col, drop); K.tf_pop()


def chand(u, v, floor, n=6):
    with at(u, v, 0, floor) as c:
        K.tf_push(0, 0, CH - (0.85 if floor == 1 else 1.15), 0); M.chandelier(c, n); K.tf_pop()


def foyer():
    with at(1.9, 7.0, -90) as c:
        M.console_table(c, 4.0, 1.5, 3.0)
        K.tf_push(0, 0.1, 3.0, 0); M.vase_flowers(c, 'blue', 7, 1.2); K.tf_pop()
    for k, col in enumerate(('navy', 'burg')):
        with at(1.5, 1.95 + k * 2.25, -90) as c:
            K.tf_push(0, 0, 6.8, 0); M.coat_on_hook(c, col); K.tf_pop()
    with at(12.6, 1.9, 0) as c:
        M.umbrella_stand(c)
    with at(12.2, 4.8, 180) as c:
        M.shoe(c, 'dark'); K.tf_push(1.2, 0.3, 0, 20); M.shoe(c, 'red'); K.tf_pop()
    with at(7.0, 6.2, 0) as c:
        M.rug(c, 6.0, 8.0, 'navy', 'cream', 'brass')
    with at(11.8, 10.6, 0) as c:
        M.potted_plant(c, 1.0, 'terra', True)
    with at(12.6, 12.6, 0) as c:
        M.floor_lamp(c)
    with at(13.4, 8.0, 90) as c:
        K.tf_push(0, 0, 5.0, 0); M.mirror_round(c, 1.4); K.tf_pop()
    pend(7.0, 6.0, 1)


def hall():
    with at(7.0, 29.0, 0) as c:
        pass
    with at(10.8, 23.0, 0) as c:
        M.rug(c, 4.2, 14.0, 'burg', 'cream', 'brass')
    with at(12.7, 19.0, 90) as c:
        M.console_table(c, 4.4, 1.2, 3.0)
        K.tf_push(-1.0, 0.1, 3.0, 0); M.table_lamp(c, 2.0, 1.6, 'teal'); K.tf_pop()
    art(13.4, 19.0, 90, 1, 3.0, 2.2, 8.0, cover='teal')
    art(13.4, 25.6, 90, 1, 2.6, 3.2, 6.6, cover='orange', kind='family')
    with at(12.7, 26.6, 90) as c:
        M.bench(c, 3.0)
    with at(12.0, 31.0, 0) as c:
        M.floor_lamp(c)
    with at(2.8, 33.8, 0) as c:
        M.potted_plant(c, 1.0, 'terra', True)
    art(13.4, 40.5, 90, 1, 2.8, 3.4, 6.8, cover='blue', kind='family')
    pend(10.5, 20.0, 1)
    pend(10.5, 34.0, 1)


def wc():
    with at(4.5, 42.2, 180) as c:
        M.toilet(c)
    with at(1.9, 39.5, -90) as c:
        M.pedestal_sink(c)
    with at(0.95, 39.5, -90) as c:
        K.tf_push(0, 0, 4.6, 0); M.mirror_round(c, 0.9); K.tf_pop()
    art(3.5, 37.0, 0, 1, 1.8, 2.4, 6.3, cover='teal')
    with at(4.0, 40.0, 0) as c:
        M.rug(c, 2.4, 3.0, 'teal', 'white', 'cream', False)
    pend(3.6, 40.0, 1, 'metal', 1.4)


def living():
    with at(52.0, 12.0, 90) as c:
        M.tv_unit(c, 8.6, 2.0, 2.4)
    with at(52.45, 20.0, 90) as c:
        M.bookshelf(c, 3.4, 7.4, 1.3, 5, 4)
    with at(52.45, 4.0, 90) as c:
        M.bookshelf(c, 3.4, 7.4, 1.3, 5, 6)
    with at(31.0, 12.0, -90) as c:
        M.sofa(c, 9.2, 3.6, 'sofa', 'sofa2')
    with at(41.0, 4.3, 0) as c:
        M.sofa(c, 7.0, 3.4, 'burg', 'burg', ('cream', 'teal', 'mustard'))
    with at(41.0, 19.4, 180) as c:
        M.armchair(c, 'olive', 'olive')
    with at(37.0, 11.5, 0) as c:
        M.coffee_table(c, 3.2, 6.2, 1.5)
        K.tf_push(0, 0, 1.5, 0); M.vase_flowers(c, 'blue', 7, 1.1); K.tf_pop()
    with at(38.5, 11.5, 0) as c:
        M.rug(c, 14.0, 10.0, 'navy', 'cream', 'teal')
    with at(29.0, 21.6, 0) as c:
        M.floor_lamp(c)
    with at(29.4, 3.0, 0) as c:
        M.potted_plant(c, 1.2, 'terra', True)
    with at(17.8, 21.8, 180) as c:
        M.side_table(c)
        K.tf_push(0, 0, 2.4, 0); M.table_lamp(c, 2.0, 1.6, 'teal'); K.tf_pop()
    art(27.0, 23.3, 180, 1, 5.0, 3.4, 7.0, cover='teal')
    art(20.0, 23.3, 180, 1, 3.0, 3.8, 6.8, cover='orange', kind='family')
    for u in (24, 34, 44):
        curtains(u, 1.35, 7.0, 1, 'x', 'coral')
    chand(24.0, 12.0, 1, 5)
    chand(38.5, 11.5, 1, 6)


def kitchen():
    # counters on the north wall (back to v24.5), fridge at the east end; island in the middle; south wall cabinet
    with at(16.9, 25.9, 0) as c:
        M.stove(c, 2.8, 2.4, 3.1)
        K.tf_push(0, 0, 3.3, 0); M.cooking_pot(c, 'metal', 0.9, True); K.tf_pop()
    with at(16.9, 25.75, 0) as c:
        K.tf_push(0, 0.2, 6.2, 0); M.range_hood(c, 3.0, 2.1); K.tf_pop()
    with at(20.6, 25.9, 0) as c:
        M.cabinet(c, 4.0, 2.2, 3.0, 2, 'cab', 'teal')
        K.tf_push(0.8, 0.2, 3.0, 0); M.toaster(c); K.tf_pop()
    with at(24.6, 25.9, 0) as c:
        M.sink_unit(c, 4.0, 2.2, 3.0)
    with at(28.2, 25.9, 0) as c:
        M.cabinet(c, 3.0, 2.2, 3.0, 2, 'cab', 'teal')
        K.tf_push(0, 0.3, 3.0, 0); M.kettle(c, 'red'); K.tf_pop()
    with at(31.2, 25.9, 0) as c:
        M.fridge(c)
    with at(24.0, 25.2, 0) as c:
        K.tf_push(0, 0, 5.6, 0); M.upper_cabinet(c, 11.0, 1.1, 2.9, 5); K.tf_pop()
    with at(24.0, 33.5, 0) as c:
        M.cabinet(c, 5.4, 3.0, 3.4, 3, 'cab', 'counter')
        K.cover('kitchen_island', 5.4, 3.0, 3.5)
        K.lcbox(0, 0, 5.4, 3.0, 3.4, 'island')
        K.tf_push(-1.5, 0, 3.4, 0); M.fruit_bowl(c); K.tf_pop()
        K.tf_push(1.4, 0.4, 3.4, 0); M.cutting_board(c); K.tf_pop()
    for k in range(3):
        with at(21.4 + k * 2.6, 36.7, 180) as c:
            M.stool(c, 'red', 2.7)
    with at(24.0, 33.5, 0) as c:
        K.tf_push(0, 0, CH - 0.35, 0); M.pendant(c, 'red', 3.2); K.tf_pop()
    with at(17.0, 42.4, 180) as c:
        M.cabinet(c, 4.0, 1.6, 3.0, 2, 'cab', 'teal')
    with at(31.8, 41.2, 0) as c:
        M.potted_plant(c, 0.9, 'terra', False)
    with at(17.4, 34.0, 0) as c:
        pass
    pend(18.0, 38.0, 1, 'red', 2.4)


def dining():
    with at(45.6, 34.0, 0) as c:
        M.rug(c, 13.0, 11.0, 'burg', 'cream', 'brass')
    with at(45.6, 34.0, 0) as c:
        M.dining_table(c, 10.6, 4.8, 2.9)
        K.lcbox(0, 0, 10.6, 4.8, 2.9, 'dining_table')
        for k in range(3):
            K.tf_push(-3.6 + k * 3.6, 1.1, 2.9, 0); M.place_setting(c, 'teal'); K.tf_pop()
            K.tf_push(-3.6 + k * 3.6, -1.1, 2.9, 180); M.place_setting(c, 'teal'); K.tf_pop()
        K.tf_push(0, 0, 2.9, 0); M.candle(c); K.tf_pop()
        K.tf_push(2.0, 0, 2.9, 0); M.vase_flowers(c, 'blue', 7, 1.0); K.tf_pop()
    for k in range(3):
        with at(42.0 + k * 3.6, 30.9, 0) as c:
            M.dining_chair(c, 'red', 'cream')
        with at(42.0 + k * 3.6, 37.1, 180) as c:
            M.dining_chair(c, 'red', 'cream')
    chand(45.6, 34.0, 1, 8)
    with at(52.3, 27.4, 90) as c:
        M.sideboard(c, 5.0, 1.8, 2.8)
        K.tf_push(0, 0, 2.94, 0); M.vase_flowers(c, 'blue', 7, 1.3); K.tf_pop()
    art(53.0, 27.4, 90, 1, 3.6, 3.0, 7.2, cover='teal')
    with at(51.0, 40.8, 0) as c:
        M.potted_plant(c, 1.2, 'terra', True)
    with at(36.2, 41.0, 0) as c:
        M.floor_lamp(c)


def library():
    with at(52.45, 55.5, 90) as c:
        M.bookshelf(c, 4.4, 8.4, 1.5, 6, 11)
    with at(38.0, 45.3, 0) as c:
        M.bookshelf(c, 5.4, 8.4, 1.5, 6, 12)
    with at(37.6, 65.4, 180) as c:
        M.bookshelf(c, 3.0, 8.4, 1.5, 6, 14)
    with at(50.2, 65.4, 180) as c:
        M.bookshelf(c, 4.0, 8.4, 1.5, 6, 15)
    with at(44.0, 56.0, 0) as c:
        M.rug(c, 9.0, 7.0, 'teal', 'cream', 'brass')
    with at(38.5, 50.0, -90) as c:
        M.armchair(c, 'burg', 'burg')
    with at(47.0, 61.0, 180) as c:
        M.armchair(c, 'olive', 'olive')
    with at(43.0, 53.8, 0) as c:
        M.round_table(c, 1.5, 2.4, 'wood2')
        K.tf_push(0, 0, 2.4, 0); M.table_lamp(c, 2.0, 1.6, 'teal'); K.tf_pop()
    with at(36.8, 62.4, 0) as c:
        M.globe(c)
    with at(52.4, 61.6, 0) as c:
        M.floor_lamp(c)
    pend(44.0, 56.0, 1, 'brass', 2.4)


def utility():
    for k, kind in enumerate(('washer', 'dryer')):
        with at(15.2 + k * 3.0, 65.0, 180) as c:
            M.washer(c, 'white', kind)
    with at(30.8, 65.2, 180) as c:
        M.cabinet(c, 5.0, 2.0, 3.0, 3, 'cab', 'counter')
        K.tf_push(0, 0, 3.0, 0); M.basket(c, 'wood2', True); K.tf_pop()
    with at(30.8, 65.5, 180) as c:
        K.tf_push(0, 0, 5.4, 0); M.upper_cabinet(c, 5.0, 1.1, 2.9, 3); K.tf_pop()
    with at(16.2, 65.5, 180) as c:
        K.tf_push(0, 0, 5.8, 0); M.upper_cabinet(c, 6.0, 1.1, 2.9, 3); K.tf_pop()
    with at(32.8, 52.0, 90) as c:
        M.drying_rack(c)
    with at(30.0, 47.8, 0) as c:
        M.ironing_board(c)
    with at(27.5, 52.6, 0) as c:
        M.cabinet(c, 6.0, 2.4, 3.0, 3, 'cab', 'counter')
        K.lcbox(0, 0, 6.0, 2.4, 3.0, 'folding_table')
        K.cover('folding_table', 6.0, 2.4, 3.0)
        K.tf_push(-1.4, 0, 3.0, 0); M.basket(c, 'wood2', True); K.tf_pop()
    with at(17.5, 45.4, 0) as c:
        shelving(c, 6.0, 8.4)
    with at(4.6, 48.2, 0) as c:
        M.potted_plant(c, 1.0, 'terra', False)
    with at(2.8, 46.2, 0) as c:
        M.trash_can(c)
    pend(21.5, 57.0, 1, 'metal', 2.0)
    pend(8.0, 52.0, 1, 'metal', 2.0)


def shelving(c, w, h):
    """tall storage shelf (blocks sight): faces +lz, collision box"""
    M.storage_shelf(c, w, h, 1.6)
    K.lcbox(0, 0, w, 1.6, h, 'util_shelving')


def garage_fill():
    with at(-16.1, 64.0, -90, 0) as c:
        M.cabinet(c, 4.2, 2.0, 3.0, 3, 'cab_dk', 'metal_dk')
    with at(-3.9, 65.2, 180, 0) as c:
        M.cabinet(c, 3.4, 2.0, 3.0, 2, 'cab_dk', 'metal_dk')
        K.tf_push(0, 0.2, 3.0, 0); M.cutting_board(c); K.tf_pop()
    with at(-1.95, 61.6, 90, 0) as c:
        shelving(c, 4.6, 7.0)
    with at(-14.5, 48.2, 0, 0) as c:
        M.bike(c)
    with at(-12.0, 45.9, 0, 0) as c:
        M.trash_can(c)
        K.tf_push(2.4, 0, 0, 0); M.trash_can(c, 'dark'); K.tf_pop()
    with at(-9.0, 56.0, 0, 0) as c:
        K.tf_push(0, 0, GAR_CEIL - GAR_FLOOR - 0.5, 0); M.pendant(c, 'metal', 1.4); K.tf_pop()


# ---------------------------------------------------------------------------------------------------- upper floor
def uphall():
    with at(10.8, 21.0, 0, 2) as c:
        M.rug(c, 4.2, 13.0, 'burg', 'cream', 'brass')
    with at(12.7, 4.3, 90, 2) as c:
        M.console_table(c, 3.4, 1.2, 3.0)
        K.tf_push(0, 0.1, 3.0, 0); M.vase_flowers(c, 'blue', 7, 1.1); K.tf_pop()
    art(13.4, 4.3, 90, 2, 2.4, 3.4, 8.2, cover='teal', kind='family')
    art(13.4, 24.0, 90, 2, 3.2, 2.4, 6.4, cover='orange')
    with at(2.7, 4.0, 0, 2) as c:
        M.potted_plant(c, 1.1, 'terra', True)
    with at(10.8, 47.0, 0, 2) as c:
        M.rug(c, 4.2, 13.0, 'burg', 'cream', 'brass')
    with at(12.7, 64.4, 90, 2) as c:
        M.console_table(c, 2.4, 1.2, 3.0)
    art(13.4, 64.4, 90, 2, 2.0, 3.0, 7.0, cover='blue')
    with at(2.2, 62.0, 0, 2) as c:
        M.floor_lamp(c)
    pend(7.0, 40.0, 2)
    pend(10.8, 20.0, 2)
    pend(10.8, 6.0, 2)


def master():
    # bed head on the south wall (v21.25), wardrobe nook in the SE corner (u47.5-53.25, v14.5-21.5)
    with at(28.0, 15.9, 180, 2) as c:
        M.bed(c, 8.0, 10.6, 'burg', 'cream', 'wood', ('white', 'cream'))
    for u in (21.9, 34.1):
        with at(u, 20.3, 180, 2) as c:
            M.nightstand(c)
            K.tf_push(0, 0, 2.4, 0); M.table_lamp(c, 2.0, 1.6, 'teal'); K.tf_pop()
    with at(28.0, 15.0, 0, 2) as c:
        M.rug(c, 12.0, 9.0, 'navy', 'cream', 'teal')
    with at(15.8, 16.8, -90, 2) as c:
        M.dresser(c, 6.0, 2.4, 3.7)
        K.tf_push(0, 0, 3.84, 0); M.vase_flowers(c, 'blue', 7, 1.0); K.tf_pop()
    art(28.0, 21.4, 180, 2, 4.4, 3.0, 8.4, cover='orange', kind='family')
    with at(50.0, 3.2, 0, 2) as c:
        M.armchair(c, 'olive', 'olive')
    with at(38.0, 3.0, 0, 2) as c:
        M.potted_plant(c, 1.2, 'terra', True)
    for u in (24, 34, 44):
        curtains(u, 1.35, 7.0, 2, 'x', 'olive')
    chand(28.0, 10.0, 2, 6)


def master_wardrobe():
    """HideSpot 'wardrobe': walk-in nook, door faces west (-u).  Interior u48.0-53.25 x v15.0-21.5."""
    u0, u1, v0, v1 = 47.5, 53.25, 14.5, 21.5
    h0, h1 = F2, CEIL2 - 0.45
    B(FU, 'wood2', X(u0), X(u1), h0, h1, Z(v0), Z(v0 + 0.5))
    B(FU, 'wood2', X(u0), X(u0 + 0.5), h0 + 9.6, h1, Z(v0), Z(v1))
    B(FU, 'wood2', X(u0), X(u1), h1, h1 + 0.4, Z(v0), Z(v1))
    B(FU, 'wood_dk', X(u0), X(u0 + 0.5), h0, h0 + 0.4, Z(v0 + 0.5), Z(v1))
    K.tf_push(X(u1 - 0.9), Z((v0 + v1) / 2), F2, 90)
    K.tube('metal', [(-3.0, 8.0, 0), (3.0, 8.0, 0)], 0.09, 8, c=FU)
    for k in range(8):
        K.rbox(('red', 'blue', 'cream', 'navy', 'teal', 'olive', 'burg', 'mustard')[k], -2.6 + k * 0.75, 0.0, 4.4, 0.5, 3.4, 1.4, 0.14, 2, c=FU)
    K.tf_pop()
    K.tf_push(X(u0 + 2.0), Z(v0 + 2.0), F2, 0)
    K.rbox('cab', 0, 0, 0.0, 2.4, 1.0, 1.6, 0.1, 1, c=FU)
    K.tf_pop()
    zc = (v0 + v1) / 2
    anchor_w('hide_wardrobe_enter', X(u0 - 1.6), F2, Z(zc), 1.0, 0.0)
    anchor_w('hide_wardrobe_inside', X(u0 + 2.2), F2, Z(zc), 1.0, 0.0)
    anchor_w('hide_wardrobe_hide', X(u1 - 2.4), F2, Z(zc), -1.0, 0.0)
    anchor_w('hide_wardrobe_exit', X(u0 - 2.4), F2, Z(zc), -1.0, 0.0)
    DOORLOG.append(dict(id='hide_wardrobe', kind='hide', axis='z', ctr=Z(zc + 0.25), w=6.4, y0=F2, h=9.6, wall=X(u0), th=0.4,
                        inside=[1, 0], hinge='low', swing=-1, locked=False, item=None, leaf='wood'))


def kid():
    with at(27.5, 25.1, 90, 2) as c:
        M.bunk_bed(c, 4.0, 8.4)
        K.cover('bunk_bed', 8.4, 4.0, 3.4)
    with at(28.0, 34.3, 180, 2) as c:
        M.desk(c, 5.6, 2.4, 2.9)
    with at(28.0, 32.0, 0, 2) as c:
        M.kid_chair(c, 'blue')
    with at(22.0, 34.3, 180, 2) as c:
        M.toy_chest(c)
        K.cover('toy_chest', 3.4, 2.0, 2.8)
    with at(26.0, 29.5, 0, 2) as c:
        M.rug(c, 7.0, 7.0, 'blue', 'yellow', 'white')
        K.tf_push(0, 0, 0.16, 0); M.teddy(c, 'orange'); K.tf_pop()
    with at(32.2, 29.0, 90, 2) as c:
        M.dresser(c, 3.8, 1.9, 3.4)
    pend(25.0, 29.0, 2, 'yellow', 2.2)


def bath():
    with at(51.4, 31.2, 180, 2) as c:
        M.bathtub(c)
    with at(37.0, 34.2, 180, 2) as c:
        M.toilet(c)
    with at(35.5, 28.0, -90, 2) as c:
        M.pedestal_sink(c)
    with at(35.0, 28.0, -90, 2) as c:
        K.tf_push(0, 0, 5.6, 0); M.mirror_round(c, 1.1); K.tf_pop()
    with at(43.5, 31.5, 0, 2) as c:
        M.rug(c, 6.0, 4.0, 'teal', 'white', 'cream', False)
    with at(51.9, 25.2, 90, 2) as c:
        M.basket(c, 'wood2', True)
    pend(44.0, 30.0, 2, 'metal', 1.6)


def lounge():
    # pocket u14.75-22.0 x v36.75-41.0 behind the bookcase (v41.0-42.6): the geometric niche
    with at(31.6, 50.5, 180, 2) as c:
        M.tv_unit(c, 6.4, 2.0, 2.4)
    with at(29.0, 43.8, 0, 2) as c:
        M.sofa(c, 8.0, 3.5, 'teal', 'teal', ('cream', 'yellow', 'orange'))
    with at(29.0, 47.4, 0, 2) as c:
        M.coffee_table(c, 5.0, 2.0, 1.5)
    with at(29.0, 46.5, 0, 2) as c:
        M.rug(c, 11.0, 8.0, 'burg', 'cream', 'navy')
    with at(33.0, 38.9, 90, 2) as c:
        M.armchair(c, 'orange', 'orange')
    with at(34.4, 48.0, 0, 2) as c:
        M.floor_lamp(c)
    with at(23.5, 49.6, 0, 2) as c:
        M.potted_plant(c, 1.0, 'terra', True)
    art(29.0, 37.1, 0, 2, 4.0, 3.0, 7.0, cover='teal')
    chand(29.0, 44.0, 2, 5)
    with at(18.4, 41.8, 0, 2) as c:
        M.bookshelf(c, 7.4, 9.0, 1.5, 6, 31)
        K.lcbox(0, 0, 7.4, 1.5, 9.0, 'niche_bookcase')
    anchor_w('niche_front', X(24.0), F2, Z(38.8), -1.0, 0.0)
    anchor_w('niche_inside', X(18.0), F2, Z(38.9), -1.0, 0.0)
    anchor_w('niche_hide', X(16.8), F2, Z(38.9), 1.0, 0.0)
    with at(18.4, 38.9, 0, 2) as c:
        M.rug(c, 6.0, 3.0, 'olive', 'cream', 'cream', False)


def guest():
    with at(45.0, 41.7, 0, 2) as c:
        M.bed(c, 6.4, 9.4, 'blue', 'cream', 'wood2')
    for sx in (-1, 1):
        with at(45.0 + sx * 4.7, 37.5, 0, 2) as c:
            M.nightstand(c)
            K.tf_push(0, 0, 2.4, 0); M.table_lamp(c, 2.0, 1.6, 'teal'); K.tf_pop()
    with at(51.17, 47.3, 90, 2) as c:
        M.wardrobe(c, 6.6, 3.0, 8.6, False)
    with at(37.7, 47.0, -90, 2) as c:
        M.desk(c, 4.4, 2.0, 2.9)
    with at(39.6, 47.0, 90, 2) as c:
        M.kid_chair(c, 'red')
    with at(45.0, 43.0, 0, 2) as c:
        M.rug(c, 8.0, 7.0, 'coral', 'cream', 'blue')
    pend(45.0, 44.0, 2)


def office():
    # desk under the back windows; the father stands in front of it facing the window (OfficeDad_Final placed in Studio)
    with at(23.5, 64.3, 180, 2) as c:
        M.desk(c, 9.0, 3.0, 3.0)
        K.lcbox(0, 0, 9.0, 3.0, 3.0, 'office_desk')
        K.tf_push(-2.4, 0, 3.0, 0); M.book(c, 'navy', 0, 0, 0, 1.6, 0.25, 2.1); K.tf_pop()
        K.tf_push(0.6, 0, 3.0, 0); M.monitor(c); K.tf_pop()
        K.tf_push(3.3, 0, 3.0, 0); M.table_lamp(c, 2.0, 1.6, 'teal'); K.tf_pop()
    for k, v in enumerate((54.6, 64.4)):
        with at(52.45, v, 90, 2) as c:
            M.bookshelf(c, 3.0, 8.4, 1.3, 6, 41 + k)
    with at(49.6, 53.7, 0, 2) as c:
        M.bookshelf(c, 3.2, 8.4, 1.3, 6, 43)
    with at(33.0, 54.3, 0, 2) as c:
        M.sofa(c, 7.0, 3.2, 'sofa2', 'sofa2', ('cream', 'burg'))
    with at(38.9, 54.8, 0, 2) as c:
        M.side_table(c)
    with at(28.0, 60.0, 0, 2) as c:
        M.rug(c, 11.0, 9.0, 'navy', 'cream', 'brass')
    art(33.0, 52.9, 0, 2, 4.4, 3.0, 7.4, cover='navy')
    with at(46.5, 64.0, 0, 2) as c:
        M.potted_plant(c, 1.2, 'terra', True)
    with at(16.6, 53.9, 0, 2) as c:
        M.floor_lamp(c)
    chand(26.0, 59.0, 2, 5)
    anchor_w('father', X(23.5), F2, Z(61.2), 0.0, 1.0)
    anchor_w('office_window', X(22), F2 + 3.0, Z(D), 0.0, 1.0)


def father_proxy():
    c = 'FatherProxy'
    K.tf_push(X(23.5), Z(61.2), F2, 0)
    K.rbox('navy', 0, 0, 0.0, 1.6, 3.0, 1.0, 0.2, 2, c=c)
    K.rbox('navy', 0, 0, 2.8, 2.4, 2.6, 1.3, 0.3, 2, c=c)
    K.sphere('skin', 0, 0, 6.2, 0.8, 0.9, 0.8, 12, 8, c=c)
    K.rbox('cardboard', 1.35, 0.7, 1.4, 1.7, 1.3, 0.5, 0.1, 1, c=c)
    K.tf_pop()


def utility_cupboard():
    """HideSpot 'cupboard_utility': walk-in cupboard in the SW corner of the utility room, door faces east (+u).  Interior u0.75-6.5 x v60.0-66.25."""
    u0, u1, v0, v1 = 0.75, 6.9, 59.6, 66.25
    h0, h1 = F1, CEIL1 - 0.45
    B(FG, 'wood2', X(u0), X(u1), h0, h1, Z(v0), Z(v0 + 0.4))              # north wall
    B(FG, 'wood2', X(u1 - 0.4), X(u1), h0 + 9.6, h1, Z(v0), Z(v1))        # lintel above the door
    B(FG, 'wood2', X(u0), X(u1), h1, h1 + 0.4, Z(v0), Z(v1))              # roof
    B(FG, 'wood_dk', X(u1 - 0.4), X(u1), h0, h0 + 0.4, Z(v0 + 0.4), Z(v1))  # threshold
    B(FG, 'wood2', X(u0), X(u0 + 1.8), h0 + 6.95, h0 + 7.2, Z(v0 + 0.4), Z(v1))   # bottle shelf
    K.tf_push(X(u0 + 0.9), Z((v0 + v1) / 2), F1, -90)
    for k in range(3):
        K.rbox('wood', 0, 0, 7.0 + k * 0.0, 5.6, 0.2, 1.5, 0.04, 1, c=FG) if k == 0 else None
    K.tf_pop()
    K.tf_push(X(u0 + 1.2), Z(v0 + 1.4), F1, 0)
    K.cyl('metal', 0, 0, 0.0, 0.9, 0.9, 14, c=FG)       # bucket
    K.tube('wood', [(1.6, 0.0, 0.0), (1.8, 6.4, 0.0)], 0.12, 6, c=FG)   # mop
    K.rbox('cab', 0.0, 1.4, 0.0, 1.6, 4.8, 1.0, 0.1, 1, c=FG)
    K.tf_pop()
    for k, cc in enumerate(('blue', 'cream', 'red', 'teal')):
        K.tf_push(X(u0 + 0.9), Z(v0 + 1.6 + k * 1.4), F1 + 7.2, 0)
        M.bottle(FG, cc, 'white', 1.4, 0.3)
        K.tf_pop()
    zc = (v0 + v1) / 2
    anchor_w('hide_cupboard_enter', X(u1 + 1.6), F1, Z(zc), -1.0, 0.0)
    anchor_w('hide_cupboard_inside', X(u1 - 2.6), F1, Z(zc), -1.0, 0.0)
    anchor_w('hide_cupboard_hide', X(u0 + 2.4), F1, Z(zc), 1.0, 0.0)
    anchor_w('hide_cupboard_exit', X(u1 + 2.6), F1, Z(zc), 1.0, 0.0)
    DOORLOG.append(dict(id='hide_cupboard', kind='hide', axis='z', ctr=Z(zc + 0.0), w=6.0, y0=F1, h=9.6, wall=X(u1), th=0.4,
                        inside=[-1, 0], hinge='low', swing=1, locked=False, item=None, leaf='wood'))


def rooms():
    foyer(); hall(); wc(); living(); kitchen(); dining(); library(); utility(); utility_cupboard(); garage_fill()
    uphall(); master(); master_wardrobe(); kid(); bath(); lounge(); guest(); office()
    father_proxy()
