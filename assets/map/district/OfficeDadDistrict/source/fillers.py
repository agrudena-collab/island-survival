# Entrance walkways, shop-front planters, the perimeter hedge with removable sections and the connector anchors, lawn trees and wall shrubs.
FENCE = {}                                     # section name -> list of items (exported as their own O_Fence_<name> chunks, with matching edge* colliders)
SOLID_TAGS = ('street', 'lot', 'plaza', 'paved', 'path', 'park', 'struct', 'bus', 'bld')


def hit_dist(px, pz, vx, vz, tags=SOLID_TAGS, dmax=90.0):
    """distance along (vx, vz) from the door to the near edge of the first occupied rectangle on the door axis (own margin rectangle lies behind the door)"""
    best = (dmax, None)
    for (tag, x0, x1, z0, z1) in OCC:
        if tag not in tags:
            continue
        if vx != 0:
            if not (z0 < pz < z1):
                continue
            d = (x0 - px) if vx > 0 else (px - x1)
        else:
            if not (x0 < px < x1):
                continue
            d = (z0 - pz) if vz > 0 else (pz - z1)
        if 0.6 < d < best[0]:
            best = (d, tag)
    return best


def blocked(x, z, r, tags):
    for (tag, x0, x1, z0, z1) in OCC:
        if tag in tags and x0 - r < x < x1 + r and z0 - r < z < z1 + r:
            return True
    return False


# ---- entrance walkways (6 wide, from the door to the nearest street, plaza or obstacle) + shop-front planters
for _k, (bid, rr, front, uc, wall, dw) in enumerate(META):
    px, pz = lpos(front, rr, uc, 0.0)
    vx, vz = side_out(front, 0)
    d, tag = hit_dist(px, pz, vx, vz)
    if tag in ('bld', 'struct', None):
        d = max(4.0, d - 2.5)
    if vz != 0:
        wx0, wx1 = px - 3.3, px + 3.3
        wz0, wz1 = sorted((pz, pz + vz * d))
        yx0, yx1 = px - 9.0, px + 9.0
        yz0, yz1 = sorted((pz, pz + vz * 14.0))
    else:
        wz0, wz1 = pz - 3.3, pz + 3.3
        wx0, wx1 = sorted((px, px + vx * d))
        yz0, yz1 = pz - 9.0, pz + 9.0
        yx0, yx1 = sorted((px, px + vx * 14.0))
    paved(wx0, wx1, wz0, wz1, name='walkway', zone='p', tile=6.0, tag='path')
    occ('yard', yx0, yx1, yz0, yz1)
    for sg in (-1, 1):
        qx, qz = lpos(front, rr, uc + sg * (dw / 2 + 4.4), 2.4)
        if not blocked(qx, qz, 1.6, ('street', 'lot', 'plaza', 'struct', 'bus', 'path', 'paved', 'park')) and abs(qx) < FI - 3 and abs(qz) < FI - 3:
            planter(qx, qz, 3.0, 3.0, y=GY, col=PAL[('coral', 'teal', 'mustard', 'navy')[_k % 4]])

# ---- perimeter hedge in sections; every section has its own collider (edge*) and exports as its own chunk, gaps (+-22) at the four connectors
GAP = PD.GAP
_acz = AVE_A['c']
_bcx = AVE_B['c']
HEDGE_Z = (GY, GY + 4.2)
SECTIONS = [('N1', -HALF, _bcx - GAP, -HALF, -FI), ('N2', _bcx + GAP, HALF, -HALF, -FI), ('S1', -HALF, _bcx - GAP, FI, HALF), ('S2', _bcx + GAP, HALF, FI, HALF),
            ('W1', -HALF, -FI, -HALF, _acz - GAP), ('W2', -HALF, -FI, _acz + GAP, HALF), ('E1', FI, HALF, -HALF, _acz - GAP), ('E2', FI, HALF, _acz + GAP, HALF)]
for (nm, x0, x1, z0, z1) in SECTIONS:
    n0 = len(D.ITEMS['O'])
    box(x0, x1, GY, GY + 1.0, z0, z1, PAL['stone'])
    box(x0 + 0.3 if x1 - x0 < 6 else x0, x1 - 0.3 if x1 - x0 < 6 else x1, GY + 1.0, GY + 1.2, z0 + (0.3 if z1 - z0 < 6 else 0), z1 - (0.3 if z1 - z0 < 6 else 0), PAL['white'])
    inx0, inx1 = (x0 + 0.3, x1 - 0.3) if x1 - x0 < 6 else (x0, x1)
    inz0, inz1 = (z0 + 0.3, z1 - 0.3) if z1 - z0 < 6 else (z0, z1)
    box(inx0, inx1, GY + 1.2, GY + 4.2, inz0, inz1, PAL['hedge'])
    box(inx0 + 0.15, inx1 - 0.15, GY + 4.2, GY + 4.45, inz0 + 0.15, inz1 - 0.15, '#34B04A')
    # white pillars every ~25 studs along the section
    if x1 - x0 > 6:
        k = x0 + 6
        while k < x1 - 3:
            box(k - 0.9, k + 0.9, GY + 1.0, GY + 5.4, z0 - 0.0, z1, PAL['white'])
            box(k - 1.1, k + 1.1, GY + 5.4, GY + 5.7, z0 - 0.1, z1 + 0.1, PAL['roof'])
            k += 25
    else:
        k = z0 + 6
        while k < z1 - 3:
            box(x0, x1, GY + 1.0, GY + 5.4, k - 0.9, k + 0.9, PAL['white'])
            box(x0 - 0.1, x1 + 0.1, GY + 5.4, GY + 5.7, k - 1.1, k + 1.1, PAL['roof'])
            k += 25
    FENCE[nm] = D.ITEMS['O'][n0:]
    del D.ITEMS['O'][n0:]
    collider(x0, x1, GY, GY + 20, z0, z1, 'edge' + nm)

# ---- connector anchors (end of every avenue, on the border, looking out of the district)
anchor('connector_E', HALF, GY, _acz, 1, 0)
anchor('connector_W', -HALF, GY, _acz, -1, 0)
anchor('connector_N', _bcx, GY, -HALF, 0, -1)
anchor('connector_S', _bcx, GY, HALF, 0, 1)

# ---- lawn trees on jittered grid cells that are free; shrubs along the walls of the buildings
rndf = random.Random(5)
FREE_TAGS = ('street', 'lot', 'plaza', 'paved', 'path', 'yard', 'park', 'struct', 'bed', 'bus', 'bld')


def free(x, z, r):
    if abs(x) > FI - r or abs(z) > FI - r:
        return False
    for (tag, x0, x1, z0, z1) in OCC:
        if tag in FREE_TAGS and x0 - r < x < x1 + r and z0 - r < z < z1 + r:
            return False
    for (tx, tz, tr) in TREES:
        if (tx - x) ** 2 + (tz - z) ** 2 < (tr + r + 1.0) ** 2:
            return False
    return True


for gx in range(-15, 16):
    for gz in range(-15, 16):
        x, z = gx * 16.0 + rndf.uniform(-4, 4), gz * 16.0 + rndf.uniform(-4, 4)
        if free(x, z, 4.4):
            tree(x, z, seed=gx * 31 + gz, h=9 + rndf.randint(0, 3), r=rndf.uniform(4.0, 4.9), pit=False)
BRECTS = [(m[1], m[0]) for m in META] + [(TW, 'TOWER')]
for (bid, rr, front, uc, wall, dw) in META + [('TOWER', TW, 'W', TW_DOOR_U, PAL['tower'], 7.2)]:
    for side in 'SNEW':
        if side == front:
            continue
        L = rr.width(side)
        u = 5.0 + rndf.uniform(0, 3)
        while u < L - 4:
            x, z = lpos(side, rr, u, 2.6)
            ok = True
            for (tag, x0, x1, z0, z1) in OCC:
                if tag in ('street', 'lot', 'plaza', 'paved', 'path', 'yard', 'park', 'struct', 'bed', 'bus') and x0 - 1.4 < x < x1 + 1.4 and z0 - 1.4 < z < z1 + 1.4:
                    ok = False
                    break
            for (o_rr, o_name) in BRECTS:
                if o_name != bid:
                    dx = max(o_rr.x0 - x, 0, x - o_rr.x1)
                    dz = max(o_rr.z0 - z, 0, z - o_rr.z1)
                    if dx * dx + dz * dz < 8.0 ** 2:
                        ok = False
                        break
            if ok and abs(x) < FI - 12 and abs(z) < FI - 12:
                bush(x, z, r=1.7, seed=int(x + z))
            u += 9.0 + rndf.uniform(0, 2)
