# Audit of the flat (exec'd by build_flat.py before the export): writes <out>/audit.txt.
#  1. furniture colliders vs each other and vs walls   2. mesh primitives inside other objects' colliders   3. objects poking through the walls / out of the rooms
#  4. objects not standing on the floor (floating)      5. coplanar slabs (z-fight)                          6. door and path clearance
ALLC = D.STATS['colliders']
MARKS = D.STATS['marks']
STRUCT = ('wall_n', 'wall_s', 'wall_w', 'wall_e', 'wall_mid', 'wall_part', 'floor', 'ceiling', 'glass')
WALLISH = STRUCT
ROOMS = [(-22.0, 22.0, -16.0, 16.0, 'main'), (23.0, 46.0, -16.0, 3.0, 'bedroom'), (23.0, 46.0, 4.0, 16.0, 'bath')]
issues = {k: [] for k in ('COLLIDER-OVERLAP', 'ITEM-IN-COLLIDER', 'OUT-OF-ROOM', 'FLOATING', 'Z-FIGHT', 'DOOR-BLOCKED')}


def cbox_of(c):
    return (c[0] - c[3] / 2, c[0] + c[3] / 2, c[2] - c[5] / 2, c[2] + c[5] / 2, c[1] - c[4] / 2, c[1] + c[4] / 2)


def ovl(a, b, m=0.05):
    return a[0] < b[1] - m and b[0] < a[1] - m and a[2] < b[3] - m and b[2] < a[3] - m and a[4] < b[5] - m and b[4] < a[5] - m


def cyl_box(c):
    r = c[3] / 2
    return (c[0] - r, c[0] + r, c[2] - r, c[2] + r, c[1] - c[4] / 2, c[1] + c[4] / 2)


furn = [(c[6], cbox_of(c)) for c in ALLC if c[6] not in STRUCT]
furn += [(c[5], cyl_box(c)) for c in CYLC]
for i in range(len(furn)):
    for j in range(i + 1, len(furn)):
        (na, a), (nb, b) = furn[i], furn[j]
        if ovl(a, b, 0.12):
            issues['COLLIDER-OVERLAP'].append('%s (%.1f,%.1f) x %s (%.1f,%.1f)' % (na, (a[0] + a[1]) / 2, (a[2] + a[3]) / 2, nb, (b[0] + b[1]) / 2, (b[2] + b[3]) / 2))
walls = [(c[6], cbox_of(c)) for c in ALLC if c[6] in WALLISH and c[6] not in ('floor', 'ceiling', 'glass')]
for (na, a) in furn:
    for (nw, w) in walls:
        if ovl(a, w, 0.12):
            issues['COLLIDER-OVERLAP'].append('%s (%.1f,%.1f) in %s' % (na, (a[0] + a[1]) / 2, (a[2] + a[3]) / 2, nw))
    inroom = any(a[0] >= r[0] - 0.15 and a[1] <= r[1] + 0.15 and a[2] >= r[2] - 0.15 and a[3] <= r[3] + 0.15 for r in ROOMS)
    if not inroom:
        issues['OUT-OF-ROOM'].append('%s collider (%.1f..%.1f, %.1f..%.1f)' % (na, a[0], a[1], a[2], a[3]))
    if a[4] > FY + 0.15 and na not in ('kupper', 'hood', 'shower_glass', 'kcounter'):
        issues['FLOATING'].append('%s collider starts at y=%.2f (floor %.1f)' % (na, a[4], FY))


def bb_of(it):
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


slabs = {}
for ki, kind in enumerate(D.KINDS):
    for idx, it in enumerate(D.ITEMS[kind]):
        a = bb_of(it)
        own = owner_idx(ki, idx)
        oname = ALLC[own][6] if own is not None else None
        if kind == 'O' and a[5] - a[4] < 0.7 and a[4] >= FY - 0.01 and (a[1] - a[0]) > 0.6 and (a[3] - a[2]) > 0.6:
            slabs.setdefault(round(a[5], 3), []).append((a[0], a[1], a[2], a[3], it[4]))
        if a[2] < -17.5 or a[5] > CY + 0.5 or a[4] < FY - 0.5:
            continue                                  # skyline / ceiling / floor structure
        if oname in STRUCT:
            continue
        if -17.2 <= a[0] and a[1] <= -10.8 and 16.0 <= a[2] and a[3] <= 17.0:
            continue                                  # the exit door leaf sits in the wall thickness on purpose
        # object poking through the walls: its box must stay within one room (+0.6 for trims and casings)
        ok = any(a[0] >= r[0] - 0.6 and a[1] <= r[1] + 0.6 and a[2] >= r[2] - 0.6 and a[3] <= r[3] + 0.6 for r in ROOMS)
        if not ok and (a[1] - a[0]) < 12 and (a[3] - a[2]) < 12:
            issues['OUT-OF-ROOM'].append('%s item (%.1f..%.1f, %.1f..%.1f) y%.1f..%.1f' % (oname, a[0], a[1], a[2], a[3], a[4], a[5]))
        # inside another object's collider
        if a[5] - a[4] < 0.6:
            continue
        for j, c in enumerate(ALLC):
            if j == own or c[6] in STRUCT or c[6] == oname:
                continue
            if ovl(a, cbox_of(c), 0.4):
                issues['ITEM-IN-COLLIDER'].append('%s item (%.1f,%.1f) y%.1f..%.1f inside %s (%.1f,%.1f)' % (oname, (a[0] + a[1]) / 2, (a[2] + a[3]) / 2, a[4], a[5], c[6], c[0], c[2]))
                break
for yt, lst in slabs.items():
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            s, t = lst[i], lst[j]
            if s[4] == t[4]:
                continue
            ox, oz = min(s[1], t[1]) - max(s[0], t[0]), min(s[3], t[3]) - max(s[2], t[2])
            if ox > 0.3 and oz > 0.3 and ox * oz > 1.0:
                issues['Z-FIGHT'].append('y%.2f (%.0f..%.0f, %.0f..%.0f) x (%.0f..%.0f, %.0f..%.0f)' % (yt, s[0], s[1], s[2], s[3], t[0], t[1], t[2], t[3]))
# doorways must stay clear of furniture (3.4 wide corridors in front of / behind each door)
for (nm, zone) in (('exit door', (-17.0, -11.0, 11.0, 16.0)), ('bedroom door', (21.0, 25.0, -10.0, -5.0)), ('bath door', (21.0, 25.0, 6.5, 11.5))):
    zb = (zone[0], zone[1], zone[2], zone[3], FY + 0.2, FY + 6)
    for (nf, a) in furn:
        if ovl(a, zb, 0.05):
            issues['DOOR-BLOCKED'].append('%s blocked by %s (%.1f,%.1f)' % (nm, nf, (a[0] + a[1]) / 2, (a[2] + a[3]) / 2))
with open(os.path.join(OUT, 'audit.txt'), 'w') as fh:
    for k, v in issues.items():
        v = sorted(set(v))
        fh.write('%s: %d\n' % (k, len(v)))
        for line in v[:100]:
            fh.write('   ' + line + '\n')
print('AUDIT', {k: len(set(v)) for k, v in issues.items()})
