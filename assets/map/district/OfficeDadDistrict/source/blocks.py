# The 20 neighbour buildings of the plan (decorative facades without interiors and WITHOUT signs).
# Kinds: торговое (retail: shop windows + awnings), деловое (office: lobby glass, navy bands), жилое (residential: balconies), смещанное (retail ground + balconies).
AWN = [(PAL['coral'], PAL['white']), (PAL['teal'], PAL['white']), (PAL['mustard'], PAL['white']), (PAL['navy'], PAL['white'])]


def side_out(side, d):
    """unit vector pointing out of a wall"""
    return {'S': (0, 1), 'N': (0, -1), 'E': (1, 0), 'W': (-1, 0)}[side]


for _i, (bid, bx0, bx1, by0, by1, fl, kind, fac, front) in enumerate(PD.B):
    if bid == 'TOWER':
        continue
    rr = rect_bl(bx0, bx1, by0, by1)
    wall = FACADE[fac]
    L = rr.width(front)
    dw = 6.4 if kind == 'деловое' else 5.2
    uc = round(L / 2.0, 1)
    sf = []
    if kind in ('торговое', 'смешанное', 'деловое'):
        a0, a1 = 2.5, uc - dw / 2 - 1.6
        b0, b1 = uc + dw / 2 + 1.6, L - 2.5
        awn = AWN[_i % 4] if kind != 'деловое' else None
        if a1 - a0 >= 5.5:
            sf.append((a0, a1, awn))
        if b1 - b0 >= 5.5:
            sf.append((b0, b1, awn))
    kw = dict(fh=PD.FLOOR_H, front=front, ground_h=PD.GROUND_H, entrance_u=uc, door_w=dw, name=bid.lower(), seed=100 + _i, tank=(fl >= 5), tall=(fl >= 7),
              storefronts=sf or None, canopy=PAL['roof'], front_bulk=PAL['navy'] if kind == 'деловое' else PAL[('coral', 'teal', 'mustard', 'navy')[_i % 4]])
    if kind == 'деловое':
        kw.update(win_w=4.4, win_h=5.8, band=PAL['navy'], band_h=0.8, door_h=9.0, door_depth=4.2, flowers_prob=0.0, ac_prob=0.14)
    elif kind == 'жилое':
        kw.update(balconies=True, win_w=3.8, win_h=5.4, flowers_prob=0.2)
    elif kind == 'смешанное':
        kw.update(balconies=True, flowers_prob=0.1)
    else:
        kw.update(flowers_prob=0.15, ac_prob=0.1)
    building(rr, fl, wall, PAL['white'], **kw)
    occ('bld', rr.x0 - 1.5, rr.x1 + 1.5, rr.z0 - 1.5, rr.z1 + 1.5)
    META.append((bid, rr, front, uc, wall, dw))
