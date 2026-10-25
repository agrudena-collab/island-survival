"""OfficeDadHouse_V2_Final -- house architecture: two storeys + garage annex, stairs, balcony, flat roofs, doors and windows.

Plan (u east, v toward the back yard, house origin HX,HZ; the street is at v < 0):
  Ground floor  foyer+hall (stairs) | living | kitchen | dining | library | utility (hide cupboard, back door) | WC | garage annex (west)
  Upper floor   hall | master (wardrobe hide spot) | kid | bath (ensuite) | lounge (niche behind the bookcase) | guest | office + balcony
"""
import math
import odh_core as K
from odh_core import *
import odh_scene as S

A = 'Arch'
ROOMS = {}          # name -> (floor, u0, u1, v0, v1, wall colour name)
RISER, TREAD = (F2 - F1) / 15.0, 1.2
STAIR = dict(u0=0.0, u1=7.0, v_bottom=30.0, v_top=12.0)
GAR_U0 = -18.0      # garage annex west wall
GAR_FLOOR = F1 - 0.5
GAR_CEIL = 11.5


def X(u):
    return HX + u


def Z(v):
    return HZ + v


def room(name, floor, u0, u1, v0, v1, wall, fcol):
    ROOMS[name] = (floor, u0, u1, v0, v1, wall)
    cx, cz = X((u0 + u1) / 2), Z((v0 + v1) / 2)
    base = F1 if floor == 1 else F2
    return dict(name=name, floor=floor, u0=u0, u1=u1, v0=v0, v1=v1, wall=wall, fcol=fcol)


def floor_rect(floor, u0, u1, v0, v1, colr):
    top = F1 if floor == 1 else F2
    u0, u1, v0, v1 = max(u0, 0.75), min(u1, W - 0.75), max(v0, 0.75), min(v1, D - 0.75)
    B(A, colr, X(u0), X(u1), top - 0.5, top, Z(v0), Z(v1))


def ceiling_rect(floor, u0, u1, v0, v1):
    pass


def ox(ops):
    return [(o[0], X(o[1])) + tuple(o[2:]) for o in ops]


def oz(ops):
    return [(o[0], Z(o[1])) + tuple(o[2:]) for o in ops]


# ------------------------------------------------------------------ wall segment helpers
def _seg_ops(ops, a, b, axis_center):
    """filter openings whose centre lies in [a, b)"""
    doors = [(o[1], o[2], o[3]) for o in ops if o[0] == 'd' and a <= o[1] < b]
    wins = [(o[1], o[2], o[3], o[4]) for o in ops if o[0] == 'w' and a <= o[1] < b]
    return doors, wins


def ext_wall_x(zc, outside_low, segs, ops, h0, h1, th=TEXT, floor_ref=None):
    """exterior wall along x at z = zc.  segs = [(x0, x1, wall colour)].  ops = [('d', xc, w, h), ('w', xc, w, sill, top)] (heights above floor_ref)"""
    ref = F1 if floor_ref is None else floor_ref
    sp = 2.0 / 3.0 if outside_low else 1.0 / 3.0
    for (x0, x1, wc) in segs:
        doors, wins = _seg_ops(ops, x0, x1, zc)
        wins = [(w[0], w[1], w[2] + (ref - h0), w[3] + (ref - h0)) for w in wins]
        doors = [(d[0], d[1], d[2] + (ref - h0)) for d in doors]
        ca, cb = ('stucco', wc) if outside_low else (wc, 'stucco')
        wall_x(A, ca, cb, x0, x1, zc, th, h0, h1, doors, wins, split=sp)


def ext_wall_z(xc, outside_low, segs, ops, h0, h1, th=TEXT, floor_ref=None):
    ref = F1 if floor_ref is None else floor_ref
    sp = 2.0 / 3.0 if outside_low else 1.0 / 3.0
    for (z0, z1, wc) in segs:
        doors, wins = _seg_ops(ops, z0, z1, xc)
        wins = [(w[0], w[1], w[2] + (ref - h0), w[3] + (ref - h0)) for w in wins]
        doors = [(d[0], d[1], d[2] + (ref - h0)) for d in doors]
        ca, cb = ('stucco', wc) if outside_low else (wc, 'stucco')
        wall_z(A, ca, cb, z0, z1, xc, th, h0, h1, doors, wins, split=sp)


def draw_windows_x(zc, th, ops, floor_ref):
    for o in ops:
        if o[0] == 'w':
            window_x(A, o[1], o[2], floor_ref, o[3], o[4], zc, th)


def draw_windows_z(xc, th, ops, floor_ref):
    for o in ops:
        if o[0] == 'w':
            window_z(A, o[1], o[2], floor_ref, o[3], o[4], xc, th)


def int_wall_x(zc, x0, x1, segs, doors_at, h0, h1, floor_ref):
    """interior wall along x; segs [(a, b, colour_low_z, colour_high_z)]; doors_at [(xc, id, kind)] opening DOOR_W wide"""
    for (a, b, cl, ch) in segs:
        dd = [(X(d[0]), DOOR_W, DOOR_H) for d in doors_at if a <= d[0] < b]
        wall_x(A, cl, ch, X(a), X(b), Z(zc), TINT, h0, h1, dd, ())
    for (xc, did, kind, hinge, swing) in doors_at:
        door(did, kind, 'x', X(xc), DOOR_W, floor_ref, DOOR_H, Z(zc), TINT, inside=(0, 1), hinge=hinge, swing=swing)


def int_wall_z(xc, z0, z1, segs, doors_at, h0, h1, floor_ref):
    for (a, b, cl, ch) in segs:
        dd = [(Z(d[0]), DOOR_W, DOOR_H) for d in doors_at if a <= d[0] < b]
        wall_z(A, cl, ch, Z(a), Z(b), X(xc), TINT, h0, h1, dd, ())
    for (zc, did, kind, hinge, swing) in doors_at:
        door(did, kind, 'z', Z(zc), DOOR_W, floor_ref, DOOR_H, X(xc), TINT, inside=(1, 0), hinge=hinge, swing=swing)


# ------------------------------------------------------------------ the build
def build_house():
    # ---------------------------------------------------------------- rooms
    R = {}
    for r in [
        room('foyer', 1, 0, 14, 0, 14, 'wall_hall', 'tile_k'), room('hall', 1, 0, 14, 14, 44, 'wall_hall', 'tile_k'),
        room('wc', 1, 0, 7, 36, 44, 'wall_wc', 'tile_b'), room('living', 1, 14, 54, 0, 24, 'wall_liv', 'floor_wood'),
        room('kitchen', 1, 14, 34, 24, 44, 'wall_kit', 'tile_k'), room('dining', 1, 34, 54, 24, 44, 'wall_din', 'floor_wood'),
        room('library', 1, 34, 54, 44, 67, 'wall_lib', 'floor_wood2'), room('utility', 1, 0, 34, 44, 67, 'wall_lau', 'tile'),
        room('garage', 1, GAR_U0, 0, 44, 67, 'wall_gar', 'concrete'),
        room('uphall', 2, 0, 14, 0, 67, 'wall_uph', 'floor_wood2'), room('master', 2, 14, 54, 0, 22, 'wall_bed', 'floor_wood'),
        room('kid', 2, 14, 34, 22, 36, 'wall_kid', 'floor_wood'), room('bath', 2, 34, 54, 22, 36, 'wall_bath', 'tile_b'),
        room('lounge', 2, 14, 36, 36, 52, 'wall_lounge', 'floor_wood'), room('guest', 2, 36, 54, 36, 52, 'wall_gst', 'floor_wood2'),
        room('office', 2, 14, 54, 52, 67, 'wall_off', 'floor_wood2'),
    ]:
        R[r['name']] = r

    # ---------------------------------------------------------------- foundation, floors, slab
    B(A, 'concrete', X(-0.75), X(W + 0.75), 0.0, 0.5, Z(-0.75), Z(D + 0.75))
    B(A, 'concrete', X(GAR_U0 - 0.75), X(-0.75), 0.0, GAR_FLOOR, Z(43.25), Z(D + 0.75))
    # plinth ring (visible band under the walls)
    for (x0, x1, z0, z1) in ((-0.9, W + 0.9, -0.9, -0.6), (-0.9, W + 0.9, D + 0.6, D + 0.9), (-0.9, -0.6, -0.9, D + 0.9), (W + 0.6, W + 0.9, -0.9, D + 0.9)):
        B(A, 'stucco_dk', X(x0), X(x1), 0.0, F1, Z(z0), Z(z1), solid=False)
    floor_rect(1, 0, 14, 0, 36, 'tile_k')
    floor_rect(1, 7, 14, 36, 44, 'tile_k')
    floor_rect(1, 0, 7, 36, 44, 'tile_b')
    floor_rect(1, 14, 54, 0, 24, 'floor_wood')
    floor_rect(1, 14, 34, 24, 44, 'tile_k')
    floor_rect(1, 34, 54, 24, 44, 'floor_wood')
    floor_rect(1, 34, 54, 44, 67, 'floor_wood2')
    floor_rect(1, 0, 34, 44, 67, 'tile')
    B(A, 'concrete', X(GAR_U0), X(0), GAR_FLOOR - 0.0, GAR_FLOOR + 0.0001, Z(44), Z(67), solid=False)
    # upper slab (ceiling of the ground floor) with the stairwell hole u0..7 x v12..30
    for (u0, u1, v0, v1) in ((0.75, W - 0.75, 0.75, 12.0), (7.0, W - 0.75, 12.0, 30.0), (0.75, W - 0.75, 30.0, D - 0.75)):
        B(A, 'ceiling', X(u0), X(u1), CEIL1, F2 - 0.5, Z(v0), Z(v1))
    # upper floor finish
    hall_fl = 'floor_wood2'
    for (u0, u1, v0, v1, c) in ((0, 14, 0, 12, hall_fl), (7, 14, 12, 30, hall_fl), (0, 14, 30, 67, hall_fl), (14, 54, 0, 22, 'floor_wood'),
                                (14, 34, 22, 36, 'floor_wood'), (34, 54, 22, 36, 'tile_b'), (14, 36, 36, 52, 'floor_wood'), (36, 54, 36, 52, 'floor_wood2'),
                                (14, 54, 52, 67, 'floor_wood2')):
        floor_rect(2, u0, u1, v0, v1, c)
    # edge band of the slab on the outside
    for (x0, x1, z0, z1) in ((-0.75, W + 0.75, -0.75, 0.75), (-0.75, W + 0.75, D - 0.75, D + 0.75), (-0.75, 0.75, 0.75, D - 0.75), (W - 0.75, W + 0.75, 0.75, D - 0.75)):
        B(A, 'stucco', X(x0), X(x1), CEIL1, F2, Z(z0), Z(z1))

    # ---------------------------------------------------------------- exterior walls: ground floor
    gh0, gh1 = F1, CEIL1
    ops = [('d', 7, EXT_W, DOOR_H), ('w', 24, 7.0, 3.5, 9.0), ('w', 34, 7.0, 3.5, 9.0), ('w', 44, 7.0, 3.5, 9.0)]
    ext_wall_x(Z(0), True, [(X(-0.75), X(14), 'wall_hall'), (X(14), X(W + 0.75), 'wall_liv')], ox(ops), gh0, gh1)
    draw_windows_x(Z(0), TEXT, [('w', X(o[1]), o[2], o[3], o[4]) for o in ops if o[0] == 'w'], F1)
    door('front', 'front', 'x', X(7), EXT_W, F1, DOOR_H, Z(0), TEXT, inside=(0, 1), hinge='low', swing=1, locked=True, leaf_col='door')

    ops_e = [('w', 34, 6.5, 3.5, 9.0), ('w', 50, 5.5, 3.5, 9.0), ('w', 61, 5.5, 3.5, 9.0)]
    ext_wall_z(X(W), False, [(Z(0.75), Z(24), 'wall_liv'), (Z(24), Z(44), 'wall_din'), (Z(44), Z(D - 0.75), 'wall_lib')], oz(ops_e), gh0, gh1)
    draw_windows_z(X(W), TEXT, oz(ops_e), F1)

    ops_w = [('w', 7, 4.5, 3.5, 9.5), ('w', 25, 6.0, 3.0, 10.5), ('w', 40, 2.5, 6.5, 9.5)]
    ext_wall_z(X(0), True, [(Z(0.75), Z(14), 'wall_hall'), (Z(14), Z(36), 'wall_hall'), (Z(36), Z(44), 'wall_wc')], oz(ops_w), gh0, gh1)
    draw_windows_z(X(0), TEXT, oz(ops_w), F1)

    ops_r = [('d', 24, EXT_W, DOOR_H), ('w', 10, 5.0, 4.0, 9.0), ('w', 44, 7.0, 3.5, 9.0)]
    ext_wall_x(Z(D), False, [(X(-0.75), X(34), 'wall_lau'), (X(34), X(W + 0.75), 'wall_lib')], ox(ops_r), gh0, gh1)
    draw_windows_x(Z(D), TEXT, [('w', X(o[1]), o[2], o[3], o[4]) for o in ops_r if o[0] == 'w'], F1)
    door('back', 'back', 'x', X(24), EXT_W, F1, DOOR_H, Z(D), TEXT, inside=(0, -1), hinge='low', swing=-1, locked=True, leaf_col='door')

    # ---------------------------------------------------------------- exterior walls: upper floor
    uh0, uh1 = F2, CEIL2
    ops2f = [('w', 7, 4.5, 3.5, 9.5), ('w', 24, 7.0, 3.0, 9.0), ('w', 34, 7.0, 3.0, 9.0), ('w', 44, 7.0, 3.0, 9.0)]
    ext_wall_x(Z(0), True, [(X(-0.75), X(14), 'wall_uph'), (X(14), X(W + 0.75), 'wall_bed')], ox(ops2f), uh0, uh1, floor_ref=F2)
    draw_windows_x(Z(0), TEXT, ox(ops2f), F2)

    ops2e = [('w', 11, 7.0, 3.0, 9.0), ('w', 29, 3.5, 6.0, 9.5), ('w', 40.5, 5.5, 3.0, 9.0), ('w', 59.5, 6.0, 3.0, 9.0)]
    ext_wall_z(X(W), False, [(Z(0.75), Z(22), 'wall_bed'), (Z(22), Z(36), 'wall_bath'), (Z(36), Z(52), 'wall_gst'), (Z(52), Z(D - 0.75), 'wall_off')],
               oz(ops2e), uh0, uh1, floor_ref=F2)
    draw_windows_z(X(W), TEXT, oz(ops2e), F2)

    ops2w = [('w', 8, 4.5, 3.5, 10.0), ('w', 25, 6.0, 3.5, 10.5), ('w', 42, 4.5, 3.5, 10.0), ('w', 59, 4.5, 3.5, 10.0)]
    ext_wall_z(X(0), True, [(Z(0.75), Z(D - 0.75), 'wall_uph')], oz(ops2w), uh0, uh1, floor_ref=F2)
    draw_windows_z(X(0), TEXT, oz(ops2w), F2)

    ops2r = [('w', 7, 4.5, 3.5, 9.5), ('w', 22, 6.0, 3.0, 9.5), ('d', 34, 7.0, DOOR_H), ('w', 46, 6.0, 3.0, 9.5)]
    ext_wall_x(Z(D), False, [(X(-0.75), X(14), 'wall_uph'), (X(14), X(W + 0.75), 'wall_off')], ox(ops2r), uh0, uh1, floor_ref=F2)
    draw_windows_x(Z(D), TEXT, [('w', X(o[1]), o[2], o[3], o[4]) for o in ops2r if o[0] == 'w'], F2)
    door('balcony', 'balcony', 'x', X(34), 7.0, F2, DOOR_H, Z(D), TEXT, inside=(0, -1), hinge='low', swing=-1, locked=False, leaf_col='doorin')

    # ---------------------------------------------------------------- interior walls: ground floor
    g0, g1 = F1, CEIL1
    int_wall_z(14, 0.75, 24, [(0.75, 24, 'wall_hall', 'wall_liv')], [(7, 'foyer_living', 'int', 'low', 1)], g0, g1, F1)
    int_wall_z(14, 24, 44, [(24, 44, 'wall_hall', 'wall_kit')], [(34, 'hall_kitchen', 'int', 'low', 1)], g0, g1, F1)
    int_wall_z(34, 24, 44, [(24, 44, 'wall_kit', 'wall_din')], [(34, 'kitchen_dining', 'int', 'low', 1)], g0, g1, F1)
    int_wall_z(34, 44, D - 0.75, [(44, D - 0.75, 'wall_lau', 'wall_lib')], [(58, 'utility_library', 'int', 'low', 1)], g0, g1, F1)
    int_wall_z(7, 36, 44, [(36, 44, 'wall_hall', 'wall_wc')], [(40, 'hall_wc', 'int', 'low', 1)], g0, g1, F1)
    int_wall_z(0, 44, D - 0.75, [(44, D - 0.75, 'wall_gar', 'wall_lau')], [(56, 'garage_utility', 'int', 'low', 1)], g0, g1, F1)
    int_wall_x(24, 14, 54, [(14, 44, 'wall_liv', 'wall_kit'), (44, 54, 'wall_liv', 'wall_din')], [(44, 'living_dining', 'int', 'low', 1)], g0, g1, F1)
    int_wall_x(44, 0.75, 54, [(0.75, 14, 'wall_hall', 'wall_lau'), (14, 34, 'wall_kit', 'wall_lau'), (34, 54, 'wall_din', 'wall_lib')],
               [(10.5, 'hall_utility', 'int', 'low', 1), (24, 'kitchen_utility', 'int', 'low', 1), (44, 'dining_library', 'int', 'low', 1)], g0, g1, F1)
    int_wall_x(36, 0.75, 7, [(0.75, 7, 'wall_hall', 'wall_wc')], [], g0, g1, F1)

    # ---------------------------------------------------------------- interior walls: upper floor
    u0_, u1_ = F2, CEIL2
    int_wall_z(14, 0.75, 22, [(0.75, 22, 'wall_uph', 'wall_bed')], [(10, 'uphall_master', 'int', 'low', 1)], u0_, u1_, F2)
    int_wall_z(14, 22, 36, [(22, 36, 'wall_uph', 'wall_kid')], [(29, 'uphall_kid', 'int', 'low', 1)], u0_, u1_, F2)
    int_wall_z(14, 36, 52, [(36, 52, 'wall_uph', 'wall_lounge')], [(48.5, 'uphall_lounge', 'int', 'low', 1)], u0_, u1_, F2)
    int_wall_z(14, 52, D - 0.75, [(52, D - 0.75, 'wall_uph', 'wall_off')], [(59.5, 'uphall_office', 'int', 'low', 1)], u0_, u1_, F2)
    int_wall_z(34, 22, 36, [(22, 36, 'wall_kid', 'wall_bath')], [], u0_, u1_, F2)
    int_wall_z(36, 36, 52, [(36, 52, 'wall_lounge', 'wall_gst')], [], u0_, u1_, F2)
    int_wall_x(22, 14, 54, [(14, 34, 'wall_bed', 'wall_kid'), (34, 54, 'wall_bed', 'wall_bath')], [(44, 'master_bath', 'int', 'high', 1)], u0_, u1_, F2)
    int_wall_x(36, 14, 54, [(14, 34, 'wall_kid', 'wall_lounge'), (34, 54, 'wall_bath', 'wall_gst')], [], u0_, u1_, F2)
    int_wall_x(52, 14, 54, [(14, 36, 'wall_lounge', 'wall_off'), (36, 54, 'wall_gst', 'wall_off')],
               [(25, 'lounge_office', 'int', 'low', 1), (45, 'guest_office', 'int', 'low', 1)], u0_, u1_, F2)
    # hall side of the stairwell: end wall at the top of the hall (v = 0 side is the exterior wall)

    # ---------------------------------------------------------------- ceilings under the roof
    B('Roof', 'ceiling', X(-0.75), X(W + 0.75), CEIL2 - 0.3, CEIL2, Z(-0.75), Z(D + 0.75), solid=False)

    # ---------------------------------------------------------------- garage annex
    gx = GAR_U0
    gh = GAR_FLOOR
    ext_wall_z(X(gx), True, [(Z(44.75), Z(D - 0.75), 'wall_gar')], [('d', Z(55.5), 12.0, 9.0)], gh, GAR_CEIL, th=TEXT, floor_ref=gh)
    # sectional vehicle door (closed, static): opening v 49.5..61.5, 9 high
    B(A, 'white', X(gx) - 0.2, X(gx) + 0.2, gh, gh + 9.0, Z(49.5), Z(61.5))
    for k in range(1, 5):
        B(A, 'metal', X(gx) - 0.28, X(gx) + 0.28, gh + 1.8 * k - 0.06, gh + 1.8 * k + 0.06, Z(49.5), Z(61.5), solid=False)
    B(A, 'trim', X(gx) - 0.3, X(gx) + 0.3, gh, gh + 9.5, Z(49.2), Z(49.5), solid=False)
    B(A, 'trim', X(gx) - 0.3, X(gx) + 0.3, gh, gh + 9.5, Z(61.5), Z(61.8), solid=False)
    B(A, 'trim', X(gx) - 0.3, X(gx) + 0.3, gh + 9.0, gh + 9.5, Z(49.2), Z(61.8), solid=False)
    anchor_w('garage_door', X(gx) - 2.3, GAR_FLOOR, Z(55.5), -1.0, 0.0)
    # garage north / south walls
    wall_x(A, 'stucco', 'wall_gar', X(gx - 0.75), X(-0.75), Z(44), TEXT, gh, GAR_CEIL, [], [(X(-9), 4.0, 5.5 - 0.0, 8.5)], split=2.0 / 3.0)
    window_x(A, X(-9), 4.0, gh, 5.5, 8.5, Z(44), TEXT)
    wall_x(A, 'wall_gar', 'stucco', X(gx - 0.75), X(-0.75), Z(D), TEXT, gh, GAR_CEIL, [(X(-9), DOOR_W, DOOR_H)], [], split=1.0 / 3.0)
    door('garage_service', 'service', 'x', X(-9), DOOR_W, gh, DOOR_H, Z(D), TEXT, inside=(0, -1), hinge='low', swing=-1, locked=True, item='HasSpareKey', leaf_col='door')
    B('Roof', 'ceiling', X(gx), X(-0.75), GAR_CEIL - 0.3, GAR_CEIL, Z(44), Z(D), solid=False)
    B('Roof', 'roof', X(gx - 1.2), X(-0.75), GAR_CEIL, GAR_CEIL + 1.0, Z(42.8), Z(D + 1.2))
    B('Roof', 'parapet', X(gx - 1.2), X(-0.75), GAR_CEIL + 1.0, GAR_CEIL + 1.8, Z(42.8), Z(43.5))
    B('Roof', 'parapet', X(gx - 1.2), X(-0.75), GAR_CEIL + 1.0, GAR_CEIL + 1.8, Z(D + 0.5), Z(D + 1.2))
    B('Roof', 'parapet', X(gx - 1.2), X(gx - 0.5), GAR_CEIL + 1.0, GAR_CEIL + 1.8, Z(43.5), Z(D + 0.5))

    # ---------------------------------------------------------------- stairs (rising north, u0..7, bottom at v34, top at v16)
    for k in range(15):
        top = F1 + (k + 1) * RISER
        vb = STAIR['v_bottom'] - k * TREAD
        B(A, 'wood', X(STAIR['u0'] + 0.75), X(STAIR['u1']), F1, top - 0.14, Z(vb - TREAD), Z(vb), solid=True)
        B(A, 'wood_lt', X(STAIR['u0'] + 0.75), X(STAIR['u1'] + 0.15), top - 0.14, top, Z(vb - TREAD - 0.0), Z(vb + 0.12), solid=True)
    B(A, 'wood_dk', X(STAIR['u1']), X(STAIR['u1'] + 0.35), F1, F2 - 0.0, Z(STAIR['v_top']), Z(STAIR['v_bottom']), solid=False)
    anchor_w('stair_foot', X(3.5), F1, Z(32.0), 0.0, -1.0)
    anchor_w('stair_top', X(3.5), F2, Z(10.5), 0.0, 1.0)

    # upper floor railings around the stairwell
    def rail_z(u, v0, v1):
        n = int((v1 - v0) / 1.0)
        B(A, 'wood_dk', X(u - 0.18), X(u + 0.18), F2 + 3.5, F2 + 3.8, Z(v0), Z(v1))
        B(A, 'wood_dk', X(u - 0.18), X(u + 0.18), F2, F2 + 0.4, Z(v0), Z(v1))
        for i in range(n + 1):
            vv = v0 + (v1 - v0) * i / n
            B(A, 'wood', X(u - 0.1), X(u + 0.1), F2 + 0.4, F2 + 3.5, Z(vv - 0.1), Z(vv + 0.1), solid=(i % 4 == 0))
        for vv in (v0, v1):
            B(A, 'wood_dk', X(u - 0.3), X(u + 0.3), F2, F2 + 4.0, Z(vv - 0.3), Z(vv + 0.3), solid=False)

    def rail_x(v, u0, u1):
        n = int((u1 - u0) / 1.0)
        B(A, 'wood_dk', X(u0), X(u1), F2 + 3.5, F2 + 3.8, Z(v - 0.18), Z(v + 0.18))
        B(A, 'wood_dk', X(u0), X(u1), F2, F2 + 0.4, Z(v - 0.18), Z(v + 0.18))
        for i in range(n + 1):
            uu = u0 + (u1 - u0) * i / n
            B(A, 'wood', X(uu - 0.1), X(uu + 0.1), F2 + 0.4, F2 + 3.5, Z(v - 0.1), Z(v + 0.1), solid=(i % 4 == 0))

    rail_z(7.0, 12.5, 30.0)
    rail_x(30.0, 0.75, 7.0)

    # ---------------------------------------------------------------- balcony over the back yard (u20..48, v67..73) with a gap in the rail for the ladder
    bu0, bu1, bv1 = 20.0, 48.0, 73.0
    B(A, 'concrete', X(bu0), X(bu1), F2 - 0.9, F2 - 0.5, Z(D + 0.75), Z(bv1))
    B(A, 'wood_lt', X(bu0), X(bu1), F2 - 0.5, F2, Z(D + 0.75), Z(bv1))
    B(A, 'stucco', X(bu0), X(bu1), F2 - 3.2, F2 - 0.9, Z(bv1 - 0.8), Z(bv1), solid=False)
    gap0, gap1 = 33.0, 37.0
    for (a, b) in ((bu0, gap0), (gap1, bu1)):
        B(A, 'wood_dk', X(a), X(b), F2 + 3.5, F2 + 3.8, Z(bv1 - 0.3), Z(bv1))
        B(A, 'wood_dk', X(a), X(b), F2, F2 + 0.4, Z(bv1 - 0.3), Z(bv1))
        n = max(2, int((b - a) / 1.0))
        for i in range(n + 1):
            uu = a + (b - a) * i / n
            B(A, 'wood', X(uu - 0.1), X(uu + 0.1), F2 + 0.4, F2 + 3.5, Z(bv1 - 0.25), Z(bv1 - 0.05), solid=(i % 4 == 0))
    for (a, b) in ((bu0, bu0 + 0.3), (bu1 - 0.3, bu1)):
        B(A, 'wood_dk', X(a), X(b), F2 + 0.4, F2 + 3.8, Z(D + 0.75), Z(bv1))
    for uu in (bu0, bu1, gap0, gap1):
        B(A, 'wood_dk', X(uu - 0.25), X(uu + 0.25), F2, F2 + 4.0, Z(bv1 - 0.4), Z(bv1), solid=False)
    anchor_w('ladder_top', X(35.0), F2, Z(bv1 - 0.5), 0.0, 1.0)
    anchor_w('ladder_foot', X(35.0), 0.0, Z(bv1 + 1.9), 0.0, 1.0)

    # ---------------------------------------------------------------- porch with canopy at the front door, steps at the other outside doors
    B(A, 'concrete', X(0.5), X(13.5), 0.0, 0.5, Z(-6.0), Z(-0.75))
    B(A, 'concrete', X(0.5), X(13.5), 0.5, 1.0, Z(-4.0), Z(-0.75))
    for ux in (1.2, 12.8):
        B(A, 'trim', X(ux - 0.45), X(ux + 0.45), 1.0, 11.0, Z(-4.6), Z(-3.7), solid=True)
    B(A, 'roof', X(-0.8), X(14.8), 11.0, 11.9, Z(-5.6), Z(-0.75))
    B(A, 'parapet', X(-0.8), X(14.8), 11.9, 12.5, Z(-5.6), Z(-5.1), solid=False)
    anchor_w('front_door', X(7), F1, Z(-2.5), 0.0, 1.0)
    B(A, 'concrete', X(24) - 3.6, X(24) + 3.6, 0.0, 0.5, Z(D + 0.75), Z(D + 3.0))
    B(A, 'concrete', X(-9) - 3.2, X(-9) + 3.2, 0.0, 0.3, Z(D + 0.75), Z(D + 2.6))
    anchor_w('back_door', X(24), F1, Z(D + 3.5), 0.0, -1.0)
    anchor_w('garage_service', X(-9), GAR_FLOOR, Z(D + 3.2), 0.0, -1.0)

    # ---------------------------------------------------------------- roof: navy flat roof with overhang and parapet
    B('Roof', 'roof', X(-1.8), X(W + 1.8), CEIL2, CEIL2 + 1.0, Z(-1.8), Z(D + 1.8))
    for (x0, x1, z0, z1) in ((-1.8, W + 1.8, -1.8, -1.0), (-1.8, W + 1.8, D + 1.0, D + 1.8), (-1.8, -1.0, -1.0, D + 1.0), (W + 1.0, W + 1.8, -1.0, D + 1.0)):
        B('Roof', 'parapet', X(x0), X(x1), CEIL2 + 1.0, CEIL2 + 2.2, Z(z0), Z(z1))
        B('Roof', 'trim', X(x0 - 0.2), X(x1 + 0.2), CEIL2 - 0.5, CEIL2, Z(z0 - 0.2), Z(z1 + 0.2), solid=False)
    # rooftop equipment
    for (cx, cz, sx, sz, hh) in ((18, 20, 5, 4, 3.2), (32, 20, 5, 4, 3.2), (42, 48, 3, 3, 2.4)):
        B('Roof', 'metal', X(cx - sx / 2), X(cx + sx / 2), CEIL2 + 1.0, CEIL2 + 1.0 + hh, Z(cz - sz / 2), Z(cz + sz / 2))
        B('Roof', 'metal_dk', X(cx - sx / 2 + 0.2), X(cx + sx / 2 - 0.2), CEIL2 + 1.0 + hh, CEIL2 + 1.3 + hh, Z(cz - sz / 2 + 0.2), Z(cz + sz / 2 - 0.2), solid=False)
    for (cx, cz) in ((10, 40), (12, 44), (46, 8)):
        K.tf_push(X(cx), Z(cz), CEIL2 + 1.0, 0)
        K.cyl('metal_dk', 0, 0, 0, 3.0, 0.45, 12, c='Roof')
        K.cyl('metal', 0, 0, 3.0, 0.3, 0.7, 12, c='Roof')
        K.tf_pop()
    return R


def room_lights():
    for name, (fl, u0, u1, v0, v1, wc) in ROOMS.items():
        base = F1 if fl == 1 else F2
        if name == 'garage':
            h = GAR_FLOOR + 9.5
        else:
            h = base + CH - 1.5
        e = 700 + 0.9 * (u1 - u0) * (v1 - v0)
        S.ROOM_LIGHTS.append((name, X((u0 + u1) / 2), h, Z((v0 + v1) / 2), e))


def draw_door_leaves(open_interior=0.0, open_exterior=0.0):
    """leaf geometry for renders only (collection 'DoorLeaf'): the Studio script rebuilds interactive leaves from DOORLOG"""
    for d in DOORLOG:
        w, h, t = d['w'], d['h'] - 0.15, 0.45
        cn = 'DoorLeafU' if d['y0'] > F2 - 0.5 else 'DoorLeaf'      # upper-floor leaves live in their own collection (hidden in the ground-floor plan view)
        ang = open_exterior if d['kind'] in ('front', 'back', 'service', 'balcony') else open_interior
        sw = d['swing']
        if d['axis'] == 'x':
            lo = d['ctr'] - w / 2
            hx = lo if d['hinge'] == 'low' else d['ctr'] + w / 2
            tf_push(hx, d['wall'], d['y0'], 0 if d['hinge'] == 'low' else 180)
            if d['hinge'] == 'low':
                tf_push(0, 0, 0, sw * ang)
                B_local_leaf(d, w, h, t, cn)
                tf_pop()
            else:
                tf_push(0, 0, 0, -sw * ang)
                B_local_leaf(d, w, h, t, cn)
                tf_pop()
            tf_pop()
        else:
            lo = d['ctr'] - w / 2
            hz = lo if d['hinge'] == 'low' else d['ctr'] + w / 2
            tf_push(d['wall'], hz, d['y0'], 90 if d['hinge'] == 'low' else -90)
            tf_push(0, 0, 0, -sw * ang if d['hinge'] == 'low' else sw * ang)
            B_local_leaf(d, w, h, t, cn)
            tf_pop()
            tf_pop()


def B_local_leaf(d, w, h, t, cn='DoorLeaf'):
    if d['kind'] == 'hide':      # built-in closet front: two tall panels and two metal pulls, not a room door
        K.box(d['leaf'], w / 2, 0, 0.05, w - 0.1, h, t, c=cn)
        for k in (0, 1):
            K.box('doorin', w * (0.27 + 0.46 * k), 0, h * 0.08, w * 0.38, h * 0.84, t + 0.08, c=cn)
        K.box('metal', w / 2 - 0.4, t / 2 + 0.2, h * 0.4, 0.12, 0.9, 0.3, c=cn)
        K.box('metal', w / 2 + 0.4, t / 2 + 0.2, h * 0.4, 0.12, 0.9, 0.3, c=cn)
        return
    K.box(d['leaf'], w / 2, 0, 0.05, w - 0.1, h, t, c=cn)
    K.box('doorin', w / 2, 0, h * 0.55, w * 0.62, h * 0.38, t + 0.08, c=cn)
    K.box('brass', w - 0.55, t / 2 + 0.2, h * 0.45, 0.28, 0.28, 0.4, c=cn)
