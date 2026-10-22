# Geometry-level audit (exec'd after audit.py): every mesh primitive against colliders, roads, district bounds and coplanar slabs.
# Appends to <out>/audit.txt. Ownership: items made between two collider() calls belong to the later collider; building() items to their building.
import bisect

ALLC = D.STATS['colliders']
MARKS = D.STATS['marks']
NK = len(D.KINDS)


def bbox(it):
    v = it[2]
    return (min(p[0] for p in v), max(p[0] for p in v), min(p[1] for p in v), max(p[1] for p in v), min(p[2] for p in v), max(p[2] for p in v))


def owner_of(ki, idx):
    for (name, a, b) in BLD:
        if b is not None and a[ki] <= idx < b[ki]:
            return 'B:' + name
    lo, hi = 0, len(MARKS)
    while lo < hi:
        m = (lo + hi) // 2
        if MARKS[m][ki] > idx:
            hi = m
        else:
            lo = m + 1
    return lo if lo < len(MARKS) else None


# colliders as boxes, spatial hash 16 studs
CB = []
for j, c in enumerate(ALLC):
    if c[6] in SKIP:
        continue
    CB.append((j, c[6], c[0] - c[3] / 2, c[0] + c[3] / 2, c[2] - c[5] / 2, c[2] + c[5] / 2, c[1] - c[4] / 2, c[1] + c[4] / 2))
HASH = {}
for e in CB:
    for i in range(int((e[2] + 300) // 16), int((e[3] + 300) // 16) + 1):
        for k in range(int((e[4] + 300) // 16), int((e[5] + 300) // 16) + 1):
            HASH.setdefault((i, k), []).append(e)
bname = {}
for e in CB:
    bname.setdefault(e[1], []).append(e)

issues2 = {'ITEM-IN-COLLIDER': set(), 'CANOPY-FURNITURE': set(), 'ON-ROAD': set(), 'OVERHANG': set(), 'OUT-OF-BOUNDS': set(), 'Z-FIGHT': set(), 'FLOATING': set()}
slabs = {}
nitems = 0
for ki, kind in enumerate(D.KINDS):
    for idx, it in enumerate(D.ITEMS[kind]):
        nitems += 1
        bb = bbox(it)
        x0, x1, y0, y1, z0, z1 = bb
        own = owner_of(ki, idx)
        # --- coplanar slabs (z-fight): thin flat O boxes
        if kind == 'O' and y1 - y0 < 0.7 and y0 >= GY - 0.01 and (x1 - x0) > 0.6 and (z1 - z0) > 0.6:
            slabs.setdefault(round(y1, 3), []).append((x0, x1, z0, z1, it[4]))
        if y1 - y0 < 0.0 or y1 < GY + 0.8:
            continue
        # --- out of the district (hedge ring is the outer edge)
        if (x0 < -SZ - 6.2 or x1 > SZ + 6.2 or z0 < -SZ - 6.2 or z1 > SZ + 6.2):
            issues2['OUT-OF-BOUNDS'].add('item (%.0f..%.0f, %.0f..%.0f) y%.1f' % (x0, x1, z0, z1, y1))
        # --- roads
        for (rn, rx0, rx1, rz0, rz1) in ROADS:
            if x1 > rx0 + 0.05 and x0 < rx1 - 0.05 and z1 > rz0 + 0.05 and z0 < rz1 - 0.05:
                if not (isinstance(own, int) and ALLC[own][6].startswith('edge')):
                    inside = min(x1, rx1) - max(x0, rx0), min(z1, rz1) - max(z0, rz0)
                    if y0 > 3.0 and min(inside) < 1.6:
                        pass            # canopy overhang below 1.6 studs
                    elif y0 > 3.0:
                        issues2['OVERHANG'].add('%s: overhang %.1f studs over %s at (%.0f,%.0f) owner %s' % ('canopy/arm', min(inside), rn, (x0 + x1) / 2, (z0 + z1) / 2, own))
                    elif not (isinstance(own, int) and ALLC[own][6] in ('car',)):
                        issues2['ON-ROAD'].add('%s at (%.0f,%.0f) y%.1f..%.1f owner %s' % (rn, (x0 + x1) / 2, (z0 + z1) / 2, y0, y1, ALLC[own][6] if isinstance(own, int) else own))
        # --- against colliders of other objects
        seen = set()
        for i in range(int((x0 + 300) // 16), int((x1 + 300) // 16) + 1):
            for k in range(int((z0 + 300) // 16), int((z1 + 300) // 16) + 1):
                for e in HASH.get((i, k), ()):
                    if e[0] in seen:
                        continue
                    seen.add(e[0])
                    if own == e[0] or (isinstance(own, str) and own == 'B:' + e[1]):
                        continue
                    m = 0.45                # trims may sit up to 0.4 into a wall on purpose
                    if isinstance(own, int) and ALLC[own][6] in JOINTS and e[1] in JOINTS:
                        continue
                    if isinstance(own, int) and ALLC[own][6].startswith('edge'):
                        continue
                    if x0 < e[3] - m and x1 > e[2] + m and z0 < e[5] - m and z1 > e[4] + m and y0 < e[7] - m and y1 > e[6] + m:
                        oname = ALLC[own][6] if isinstance(own, int) else own
                        if oname == 'tree' and e[1] in ('lamp', 'bench', 'bin', 'hydrant', 'mailbox', 'bollard', 'tlight') and y0 > 4:
                            issues2['CANOPY-FURNITURE'].add('tree canopy (%.0f,%.0f) x %s (%.0f,%.0f)' % ((x0 + x1) / 2, (z0 + z1) / 2, e[1], (e[2] + e[3]) / 2, (e[4] + e[5]) / 2))
                        else:
                            issues2['ITEM-IN-COLLIDER'].add('%s item (%.0f,%.0f) y%.1f..%.1f inside %s (%.0f,%.0f)' % (oname, (x0 + x1) / 2, (z0 + z1) / 2, y0, y1, e[1], (e[2] + e[3]) / 2, (e[4] + e[5]) / 2))
# coplanar slabs: same top height, overlapping footprint, different colour
for yt, lst in slabs.items():
    g = {}
    for s in lst:
        for i in range(int((s[0] + 300) // 24), int((s[1] + 300) // 24) + 1):
            for k in range(int((s[2] + 300) // 24), int((s[3] + 300) // 24) + 1):
                g.setdefault((i, k), []).append(s)
    done = set()
    for cell in g.values():
        for a in range(len(cell)):
            for b in range(a + 1, len(cell)):
                s, t = cell[a], cell[b]
                if (id(s), id(t)) in done or s[4] == t[4]:
                    continue
                ox, oz = min(s[1], t[1]) - max(s[0], t[0]), min(s[3], t[3]) - max(s[2], t[2])
                if ox > 0.3 and oz > 0.3 and ox * oz > 1.0:
                    done.add((id(s), id(t)))
                    issues2['Z-FIGHT'].add('y%.2f (%.0f..%.0f, %.0f..%.0f) x (%.0f..%.0f, %.0f..%.0f)' % (yt, s[0], s[1], s[2], s[3], t[0], t[1], t[2], t[3]))
with open(os.path.join(OUT, 'audit.txt'), 'a') as fh:
    fh.write('\n=== GEOMETRY AUDIT (%d primitives) ===\n' % nitems)
    for k, v in issues2.items():
        fh.write('%s: %d\n' % (k, len(v)))
        for line in sorted(v)[:80]:
            fh.write('   ' + line + '\n')
print('AUDIT2', {k: len(v) for k, v in issues2.items()}, 'items', nitems)
