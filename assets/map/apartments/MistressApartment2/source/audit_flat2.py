# Audit of flat 2 (exec'd by build_flat2.py before the export): writes <out>/audit.txt.
#  COLLIDER-OVERLAP, OUT-OF-ROOM, FLOATING (colliders and mesh items), ITEM-IN-COLLIDER, COPLANAR (z-fight among all axis-aligned boxes, buried faces ignored),
#  DOOR-BLOCKED, NAV (flood fill on a 1-stud raster: arrival -> chairs, bedroom, bathroom, exit door; agent R = 1.6 and a 5-wide corridor), UNCOVERED, CONTRACT.
import collections

ALLC = D.STATS['colliders']
MARKS = D.STATS['marks']
STRUCT = ('wall_n', 'wall_s', 'wall_w', 'wall_e', 'wall_far', 'wall_mid', 'floor', 'ceiling', 'glass', 'door_leaf', 'shower_glass')
ROOMS = [(-24.0, 24.0, -17.0, 17.0, 'main'), (25.0, 45.0, -17.0, 2.0, 'bedroom'), (25.0, 45.0, 3.0, 17.0, 'bath')]
issues = collections.OrderedDict((k, []) for k in ('COLLIDER-OVERLAP', 'OUT-OF-ROOM', 'FLOATING', 'ITEM-IN-COLLIDER', 'ITEM-IN-WALL', 'COPLANAR', 'DOOR-BLOCKED', 'NAV', 'TIGHT-PASSAGE', 'INVISIBLE-COLLIDER', 'UNCOVERED', 'CONTRACT'))


def cbox_of(c):
    return (c[0] - c[3] / 2, c[0] + c[3] / 2, c[2] - c[5] / 2, c[2] + c[5] / 2, c[1] - c[4] / 2, c[1] + c[4] / 2)


def cyl_box(c):
    r = c[3] / 2
    return (c[0] - r, c[0] + r, c[2] - r, c[2] + r, c[1] - c[4] / 2, c[1] + c[4] / 2)


def ovl(a, b, m=0.05):
    return a[0] < b[1] - m and b[0] < a[1] - m and a[2] < b[3] - m and b[2] < a[3] - m and a[4] < b[5] - m and b[4] < a[5] - m


def in_flat(b):
    """(x0, x1, z0, z1, y0, y1) lies inside the flat (skyline and outer slab edges are not audited)"""
    return b[0] > -25.2 and b[1] < 46.2 and b[2] > -18.2 and b[3] < 18.2 and b[4] > FY - 0.6 and b[5] < CY + 1.4


furn = [(c[6], cbox_of(c)) for c in ALLC if c[6] not in STRUCT]
furn += [(c[5], cyl_box(c)) for c in CYLC]
walls = [(c[6], cbox_of(c)) for c in ALLC if c[6] in STRUCT and c[6] not in ('floor', 'ceiling', 'glass')]
FLOATOK = ('kitchen_up1', 'kitchen_up2', 'kitchen_up3', 'tv', 'shower_glass')
for i in range(len(furn)):
    for j in range(i + 1, len(furn)):
        (na, a), (nb, b) = furn[i], furn[j]
        if ovl(a, b, 0.12):
            issues['COLLIDER-OVERLAP'].append('%s (%.1f,%.1f) x %s (%.1f,%.1f)' % (na, (a[0] + a[1]) / 2, (a[2] + a[3]) / 2, nb, (b[0] + b[1]) / 2, (b[2] + b[3]) / 2))
for (na, a) in furn:
    for (nw, w) in walls:
        if ovl(a, w, 0.12):
            issues['COLLIDER-OVERLAP'].append('%s (%.1f,%.1f) in %s' % (na, (a[0] + a[1]) / 2, (a[2] + a[3]) / 2, nw))
    if not any(a[0] >= r[0] - 0.15 and a[1] <= r[1] + 0.15 and a[2] >= r[2] - 0.15 and a[3] <= r[3] + 0.15 for r in ROOMS):
        issues['OUT-OF-ROOM'].append('%s collider (%.1f..%.1f, %.1f..%.1f)' % (na, a[0], a[1], a[2], a[3]))
    if a[4] > FY + 0.15 and na not in FLOATOK:
        issues['FLOATING'].append('%s collider starts at y=%.2f' % (na, a[4]))


def bbox_it(it):
    v = it[2]
    return (min(p[0] for p in v), max(p[0] for p in v), min(p[2] for p in v), max(p[2] for p in v), min(p[1] for p in v), max(p[1] for p in v))


def owner_idx(ki, idx):
    lo, hi = 0, len(MARKS)
    while lo < hi:
        m = (lo + hi) // 2
        if MARKS[m][ki] > idx:
            hi = m
        else:
            lo = m + 1
    return lo if lo < len(MARKS) else None


# mesh items: inside another object's collider, floating details
H8 = collections.defaultdict(list)
BB = []
for ki, kind in enumerate(D.KINDS):
    for idx, it in enumerate(D.ITEMS[kind]):
        a = bbox_it(it)
        n = len(BB)
        BB.append((kind, idx, a, it))
        if not (a[0] > -26 and a[1] < 47 and a[2] > -19 and a[3] < 19 and a[4] > FY - 2.5 and a[5] < CY + 2.5):
            continue
        for i in range(int(a[0] // 8), int(a[1] // 8) + 1):
            for j in range(int(a[2] // 8), int(a[3] // 8) + 1):
                H8[(i, j)].append(n)
E = 0.09
for n, (kind, idx, a, it) in enumerate(BB):
    if not in_flat(a):
        continue
    own = owner_idx(D.KINDS.index(kind), idx)
    oname = ALLC[own][6] if own is not None else None
    if False:
        for j, c in enumerate(ALLC):
            if j == own or c[6] in STRUCT or c[6] == oname:
                continue
            if ovl(a, cbox_of(c), 0.4):
                issues['ITEM-IN-COLLIDER'].append('%s item (%.1f,%.1f) y%.1f..%.1f inside %s (%.1f,%.1f)' % (oname, (a[0] + a[1]) / 2, (a[2] + a[3]) / 2, a[4], a[5], c[6], c[0], c[2]))
                break
    if a[4] <= FY + 0.06:
        continue
    touched = False
    seen = set()
    for i in range(int((a[0] - E) // 8), int((a[1] + E) // 8) + 1):
        for j in range(int((a[2] - E) // 8), int((a[3] + E) // 8) + 1):
            for m in H8.get((i, j), ()):
                if m == n or m in seen:
                    continue
                seen.add(m)
                o = BB[m][2]
                if o[0] <= a[1] + E and o[1] >= a[0] - E and o[2] <= a[3] + E and o[3] >= a[2] - E and o[4] <= a[5] + E and o[5] >= a[4] - E:
                    touched = True
                    break
            if touched:
                break
        if touched:
            break
    if not touched:
        issues['FLOATING'].append('%s item (%.1f,%.1f,%.1f) size %.1fx%.1fx%.1f' % (kind, (a[0] + a[1]) / 2, (a[4] + a[5]) / 2, (a[2] + a[3]) / 2, a[1] - a[0], a[5] - a[4], a[3] - a[2]))

# coplanar faces of boxes (different colours, same direction, overlapping, visible)
BOXES = {}
BH = collections.defaultdict(list)
FACES = collections.defaultdict(list)


def box_info(it):
    v = it[2]
    if len(v) != 8:
        return None
    x0, x1 = min(p[0] for p in v), max(p[0] for p in v)
    y0, y1 = min(p[1] for p in v), max(p[1] for p in v)
    z0, z1 = min(p[2] for p in v), max(p[2] for p in v)
    for p in v:
        if not ((abs(p[0] - x0) < 1e-4 or abs(p[0] - x1) < 1e-4) and (abs(p[1] - y0) < 1e-4 or abs(p[1] - y1) < 1e-4) and (abs(p[2] - z0) < 1e-4 or abs(p[2] - z1) < 1e-4)):
            return None
    return (x0, x1, y0, y1, z0, z1)


for ki, kind in enumerate(D.KINDS):
    for idx, it in enumerate(D.ITEMS[kind]):
        bi = box_info(it)
        if bi is None:
            continue
        if not (bi[0] > -25.2 and bi[1] < 46.2 and bi[4] > -18.2 and bi[5] < 18.2 and bi[2] > FY - 1.3 and bi[3] < CY + 1.4):
            continue
        BOXES[(kind, idx)] = bi
        x0, x1, y0, y1, z0, z1 = bi
        for i in range(int(x0 // 8), int(x1 // 8) + 1):
            for j in range(int(z0 // 8), int(z1 // 8) + 1):
                BH[(i, j)].append((kind, idx))
        for (ax, sg, c, a0, a1, b0, b1) in ((0, -1, x0, y0, y1, z0, z1), (0, 1, x1, y0, y1, z0, z1), (1, -1, y0, x0, x1, z0, z1), (1, 1, y1, x0, x1, z0, z1), (2, -1, z0, x0, x1, y0, y1), (2, 1, z1, x0, x1, y0, y1)):
            if ax == 1 and sg == -1 and c <= FY + 1e-6:
                continue                                                  # bottoms standing on the floor
            FACES[(ax, sg, int(round(c / 0.01)))].append((c, a0, a1, b0, b1, it[4], kind, idx))


def buried(ax, sg, c, am, bm, ex):
    p = [0, 0, 0]
    p[ax] = c + sg * 0.03
    q = [x for x in (0, 1, 2) if x != ax]
    p[q[0]], p[q[1]] = am, bm
    for key in BH.get((int(p[0] // 8), int(p[2] // 8)), ()):
        if key in ex:
            continue
        b = BOXES[key]
        if b[0] + 1e-3 < p[0] < b[1] - 1e-3 and b[2] + 1e-3 < p[1] < b[3] - 1e-3 and b[4] + 1e-3 < p[2] < b[5] - 1e-3:
            return True
    return False


cop = set()
for (ax, sg, bk), lst in list(FACES.items()):
    cand = list(lst)
    for dk in (-1, 1):
        cand += [f for f in FACES.get((ax, sg, bk + dk), ()) if abs(f[0] - lst[0][0]) < 0.0151]
    if len(cand) < 2:
        continue
    grid = collections.defaultdict(list)
    for f in cand:
        for i in range(int(f[1] // 8), int(f[2] // 8) + 1):
            for j in range(int(f[3] // 8), int(f[4] // 8) + 1):
                grid[(i, j)].append(f)
    for cell in grid.values():
        for a in range(len(cell)):
            for b in range(a + 1, len(cell)):
                f, g = cell[a], cell[b]
                if f is g or f[5] == g[5] or abs(f[0] - g[0]) > 0.0151 or (f[6], f[7]) == (g[6], g[7]):
                    continue
                oa = min(f[2], g[2]) - max(f[1], g[1])
                ob = min(f[4], g[4]) - max(f[3], g[3])
                if oa > 0.05 and ob > 0.05 and oa * ob > 0.05:
                    cx = (max(f[1], g[1]) + min(f[2], g[2])) / 2
                    cy = (max(f[3], g[3]) + min(f[4], g[4])) / 2
                    if buried(ax, sg, max(f[0], g[0]) if sg > 0 else min(f[0], g[0]), cx, cy, {(f[6], f[7]), (g[6], g[7])}):
                        continue
                    cop.add('axis%s%s at %.3f over (%.1f, %.1f) %.2fx%.2f  %s/%s' % ('xyz'[ax], '-+'[(sg + 1) // 2], f[0], cx, cy, oa, ob, f[5], g[5]))
issues['COPLANAR'] = list(cop)

# doorways must stay clear of furniture
for (nm, zone) in (('exit door', (-19.5, -12.5, 11.0, 16.5)), ('bedroom door', (21.0, 25.5, -10.0, -2.0)), ('bath door', (21.0, 25.5, 7.0, 15.0))):
    zb = (zone[0], zone[1], zone[2], zone[3], FY + 0.2, FY + 6)
    for (nf, a) in furn:
        if ovl(a, zb, 0.05):
            issues['DOOR-BLOCKED'].append('%s blocked by %s (%.1f,%.1f)' % (nm, nf, (a[0] + a[1]) / 2, (a[2] + a[3]) / 2))

# reachability: raster 1 stud over x -25..46, z -18..18
NX, NZ, OX, OZ = 71, 36, 25, 18
blocked = [bytearray(NX) for _ in range(NZ)]
for c in ALLC:
    if c[6] in ('floor', 'ceiling'):
        continue
    top, bot = c[1] + c[4] / 2, c[1] - c[4] / 2
    if c[6] in ('glass', 'shower_glass'):
        pass
    elif not ((top - bot) > 1.0 and top > FY + 1.4 and bot < FY + 6.5):
        continue
    for i in range(max(0, int(math.floor(c[0] - c[3] / 2 + OX))), min(NX, int(math.ceil(c[0] + c[3] / 2 + OX)))):
        for j in range(max(0, int(math.floor(c[2] - c[5] / 2 + OZ))), min(NZ, int(math.ceil(c[2] + c[5] / 2 + OZ)))):
            blocked[j][i] = 1
for c in CYLC:
    r = c[3] / 2
    for i in range(max(0, int(math.floor(c[0] - r + OX))), min(NX, int(math.ceil(c[0] + r + OX)))):
        for j in range(max(0, int(math.floor(c[2] - r + OZ))), min(NZ, int(math.ceil(c[2] + r + OZ)))):
            if (i + 0.5 - OX - c[0]) ** 2 + (j + 0.5 - OZ - c[2]) ** 2 <= (r + 0.4) ** 2 and (c[4] > 1.0 and c[1] + c[4] / 2 > FY + 1.4):
                blocked[j][i] = 1
INF = 10 ** 6
DF = [[INF] * NX for _ in range(NZ)]
dq = collections.deque()
for j in range(NZ):
    for i in range(NX):
        if blocked[j][i]:
            DF[j][i] = 0
            dq.append((i, j))
while dq:
    i, j = dq.popleft()
    d = DF[j][i] + 1
    for (di, dj) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        a, b = i + di, j + dj
        if 0 <= a < NX and 0 <= b < NZ and DF[b][a] > d:
            DF[b][a] = d
            dq.append((a, b))


def reach(sx, sz, rad):
    si, sj = int(sx + OX), int(sz + OZ)
    if DF[sj][si] <= rad:
        return None
    seen = {(si, sj)}
    st = [(si, sj)]
    while st:
        i, j = st.pop()
        for (di, dj) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if 0 <= a < NX and 0 <= b < NZ and (a, b) not in seen and DF[b][a] > rad:
                seen.add((a, b))
                st.append((a, b))
    return seen


with open(os.path.join(OUT, 'nav_debug.txt'), 'w') as fh:
    for j in range(NZ):
        fh.write(''.join('#' if blocked[j][i] else ('+' if DF[j][i] <= 1.6 else ('o' if DF[j][i] <= 2.5 else '.')) for i in range(NX)) + chr(10))
A = D.STATS['anchors']
targets = [('guest chair front', DX, 0.8), ('desk west side', -3.5, -10.0), ('bedroom', 28.5, -6.0), ('bathroom', 28.5, 10.5), ('exit door', -16.0, 14.0), ('lounge', 14.0, 0.8), ('kitchen', -18.5, -1.0), ('bed side', 39.0, -2.4)]
for rad, label in ((1.6, 'agent R=1.6'), (2.5, '5-wide corridor')):
    r0 = reach(A['arrival'][0], A['arrival'][2], rad)
    if r0 is None:
        issues['NAV'].append('%s: arrival blocked' % label)
        continue
    for (nm, tx, tz) in targets:
        k = (int(tx + OX), int(tz + OZ))
        if k not in r0:
            issues['NAV'].append('%s: arrival -> %s NOT reachable' % (label, nm))
    issues['NAV'].append('%s: reachable cells %d' % (label, len(r0)))
issues['NAV'] = [l for l in issues['NAV']]
for k in ('NAV',):
    pass

_r = reach(A['arrival'][0], A['arrival'][2], 1.6) or set()
with open(os.path.join(OUT, 'nav_reach.txt'), 'w') as fh:
    for j in range(NZ):
        fh.write(''.join('#' if blocked[j][i] else ('R' if (i, j) in _r else ('+' if DF[j][i] <= 1.6 else '.')) for i in range(NX)) + chr(10))

# ---------------------------------------------------------------------------------------------------------------------------------------
# objects stick into each other / into walls; colliders bigger than what is seen (invisible walls); solid things without a collider
# ---------------------------------------------------------------------------------------------------------------------------------------
FURN_BOXES = [(c[6], cbox_of(c)) for c in ALLC if c[6] not in STRUCT] + [(c[5], cyl_box(c)) for c in CYLC]
WALL_BOXES = [(c[6], cbox_of(c)) for c in ALLC if c[6] in ('wall_n', 'wall_s', 'wall_w', 'wall_e', 'wall_far', 'wall_mid')]


def ov3(a, b):
    return (min(a[1], b[1]) - max(a[0], b[0]), min(a[3], b[3]) - max(a[2], b[2]), min(a[5], b[5]) - max(a[4], b[4]))


def inside_pt(b, x, z, y, m=0.05):
    return b[0] - m <= x <= b[1] + m and b[2] - m <= z <= b[3] + m and b[4] - m <= y <= b[5] + m


vis = collections.defaultdict(list)         # collider name -> visible items belonging to it (centre inside)
FH = collections.defaultdict(list)
for k, (nm, b) in enumerate(FURN_BOXES):
    for i in range(int((b[0] - 1) // 8), int((b[1] + 1) // 8) + 1):
        for j in range(int((b[2] - 1) // 8), int((b[3] + 1) // 8) + 1):
            FH[(i, j)].append(k)
sticks = set()
inwall = set()
for (kind, idx, a, it) in BB:
    if not in_flat(a) or a[4] < FY - 0.5:
        continue
    cx, cz, cy = (a[0] + a[1]) / 2, (a[2] + a[3]) / 2, (a[4] + a[5]) / 2
    # structural items (walls, floor, ceiling, casings, skirting) sit inside / on the wall colliders: not audited here
    if any(inside_pt(w, cx, cz, cy, 0.05) for (nw, w) in WALL_BOXES):
        continue
    owners = []
    for k in FH.get((int(cx // 8), int(cz // 8)), ()):
        nm, b = FURN_BOXES[k]
        if inside_pt(b, cx, cz, cy, 0.3):
            owners.append(k)
    for k in owners:
        vis[k].append(a)
    cand = set()
    for i in range(int(a[0] // 8), int(a[1] // 8) + 1):
        for j in range(int(a[2] // 8), int(a[3] // 8) + 1):
            cand.update(FH.get((i, j), ()))
    for k in cand:
        if k in owners:
            continue
        nm, b = FURN_BOXES[k]
        ox, oz, oy = ov3(a, b)
        if ox > 0.3 and oz > 0.3 and oy > 0.3:
            oname = FURN_BOXES[owners[0]][0] if owners else 'loose item'
            sticks.add('%s item (%.1f,%.1f) y%.1f..%.1f sticks into %s (%.1f,%.1f) by %.2f x %.2f x %.2f' % (oname, cx, cz, a[4], a[5], nm, (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, ox, oz, oy))
    for (nw, w) in WALL_BOXES:
        ox, oz, oy = ov3(a, w)
        if ox > 0.35 and oz > 0.35 and oy > 0.35:
            inwall.add('%s item (%.1f,%.1f) y%.1f..%.1f inside %s by %.2f x %.2f' % (FURN_BOXES[owners[0]][0] if owners else 'loose', cx, cz, a[4], a[5], nw, ox, oz))
issues['ITEM-IN-COLLIDER'] = list(sticks)
issues['ITEM-IN-WALL'] = list(inwall)

# invisible colliders: the collider reaches further than the visible geometry it belongs to
for k, (nm, b) in enumerate(FURN_BOXES):
    its = vis.get(k, [])
    if not its:
        issues['INVISIBLE-COLLIDER'].append('%s (%.1f,%.1f): no visible geometry inside' % (nm, (b[0] + b[1]) / 2, (b[2] + b[3]) / 2))
        continue
    ux0, ux1 = min(i_[0] for i_ in its), max(i_[1] for i_ in its)
    uz0, uz1 = min(i_[2] for i_ in its), max(i_[3] for i_ in its)
    uy1 = max(i_[5] for i_ in its)
    over = (ux0 - b[0], b[1] - ux1, uz0 - b[2], b[3] - uz1, b[5] - uy1)
    if nm in ('floor', 'ceiling') or nm.startswith('plant'):
        pass
    if max(over[:4]) > 0.7 or over[4] > 0.9:
        issues['INVISIBLE-COLLIDER'].append('%s (%.1f,%.1f): collider reaches beyond the visible parts by W%.1f E%.1f N%.1f S%.1f top%.1f' % (nm, (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, over[0], over[1], over[2], over[3], over[4]))

# solid things (reachable, > 0.8 high) without any collider
cov_all = [b for (nm, b) in FURN_BOXES] + [b for (nm, b) in WALL_BOXES] + [cbox_of(c) for c in ALLC if c[6] in ('door_leaf', 'shower_glass', 'glass')]
for (kind, idx, a, it) in BB:
    if kind != 'O' or not in_flat(a) or a[4] < FY - 0.5:
        continue
    if a[5] < FY + 0.9 or a[4] > FY + 3.0 or ((a[1] - a[0]) < 0.3 and (a[3] - a[2]) < 0.3):
        continue
    cx, cz, cy = (a[0] + a[1]) / 2, (a[2] + a[3]) / 2, (a[4] + a[5]) / 2
    if any(inside_pt(b, cx, cz, cy, 0.7) for b in cov_all):
        continue
    if any(b[0] - 0.1 <= cx <= b[1] + 0.1 and b[2] - 0.1 <= cz <= b[3] + 0.1 and abs(b[5] - a[4]) <= 0.2 for b in cov_all):
        continue                                                    # stands on top of a collider (supported)
    if a[4] <= FY + 0.2 and a[5] < FY + 1.4:
        continue
    issues['UNCOVERED'].append('item (%.1f,%.1f) y%.1f..%.1f size %.1fx%.1f col %s' % (cx, cz, a[4], a[5], a[1] - a[0], a[3] - a[2], it[4]))

# tight passages: free cells (distance field) that sit between obstacles closer than 4 studs on the main route, and dead-end pockets
r16 = reach(A['arrival'][0], A['arrival'][2], 1.0) or set()
free_all = set((i, j) for j in range(NZ) for i in range(NX) if not blocked[j][i] and 0 < i < NX - 1 and 0 < j < NZ - 1)
pockets = free_all - r16
pk_small = [c for c in pockets if DF[c[1]][c[0]] >= 2]
groups = []
seenp = set()
for c in pk_small:
    if c in seenp:
        continue
    st = [c]
    seenp.add(c)
    pts = []
    while st:
        i, j = st.pop()
        pts.append((i, j))
        for (di, dj) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n_ = (i + di, j + dj)
            if n_ in pockets and n_ not in seenp and n_ in free_all and DF[n_[1]][n_[0]] >= 2:
                seenp.add(n_)
                st.append(n_)
    groups.append(pts)
for pts in groups:
    if len(pts) >= 4:
        cx = sum(p[0] for p in pts) / len(pts) - OX
        cz = sum(p[1] for p in pts) / len(pts) - OZ
        issues['TIGHT-PASSAGE'].append('pocket of %d free cells around (%.0f, %.0f) is cut off from the rest of the flat (agent R=1.0)' % (len(pts), cx, cz))

# contract
need = ('arrival', 'exit_door', 'mistress_seat', 'guest_seat', 'table_top')
for nm in need:
    if nm not in A:
        issues['CONTRACT'].append('anchor %s missing' % nm)
if len(D.STATS['colliders']) < 5:
    issues['CONTRACT'].append('too few colliders')
for c in ALLC:
    if min(c[3], c[4], c[5]) < 0.39 and c[6] not in ('glass', 'shower_glass', 'tv', 'door_leaf', 'console', 'bench', 'credenza') and c[3] * c[4] * c[5] < 0.5 and c[6] not in STRUCT:
        pass

with open(os.path.join(OUT, 'audit.txt'), 'w', encoding='utf-8') as fh:
    for k, v in issues.items():
        v = sorted(set(v)) if k != 'NAV' else v
        fh.write('%s: %d' % (k, len(v)) + chr(10))
        for line in v[:80]:
            fh.write('   ' + line + chr(10))
print('AUDIT', {k: len(set(v)) for k, v in issues.items()})
