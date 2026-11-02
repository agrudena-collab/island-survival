# Audit of the generated district (exec'd by build_district.py after layout.py, before the export).
# Writes <out>/audit.txt: overlaps between colliders / canopies / roads and an ASCII occupancy map (8 studs per cell).
import math

CELL_A = 8
ROADS = []
for _s in STREETS:
    if _s['ew']:
        ROADS.append((_s['name'], -_s['ext'], _s['ext'], _s['c'] - _s['ah'], _s['c'] + _s['ah']))
    else:
        ROADS.append((_s['name'], _s['c'] - _s['ah'], _s['c'] + _s['ah'], -_s['ext'], _s['ext']))
ROADS += [('apronC', -150.0, -138.0, 170.0, 194.0), ('apronA', 188.0, 212.0, 4.0, 18.0), ('laneB', 52.0, 150.0, 150.0, 164.0)]
LOT_RECTS = [(n, x0, x1, z0, z1) for (n, x0, x1, z0, z1) in LOTS]

SKIP = ('ground',) + tuple('edge' + sec[0] for sec in SECTIONS)
PAVING = ('walkway', 'sidewalk', 'plaza', 'parkpath', 'gardpath', 'gardplaza', 'fountain_plaza')
cols = [c for c in D.STATS['colliders'] if c[6] not in SKIP]
FURN = ('tree', 'lamp', 'bench', 'bin', 'hydrant', 'mailbox', 'bollard', 'tlight', 'planter', 'bush', 'bike', 'flowerbed')


def box_of(c):
    return (c[0] - c[3] / 2, c[0] + c[3] / 2, c[2] - c[5] / 2, c[2] + c[5] / 2, c[1] - c[4] / 2, c[1] + c[4] / 2)


def ov(a, b, m=0.0):
    return a[0] < b[1] - m and b[0] < a[1] - m and a[2] < b[3] - m and b[2] < a[3] - m and a[4] < b[5] - m and b[4] < a[5] - m


issues = []
bl = [(c, box_of(c)) for c in cols]
for i in range(len(bl)):
    for j in range(i + 1, len(bl)):
        (ca, ba), (cb, bb) = bl[i], bl[j]
        if ov(ba, bb, 0.05):
            na, nb = ca[6], cb[6]
            if na in PAVING and nb in PAVING:
                issues.append('PAVING %s (%.0f,%.0f) x %s (%.0f,%.0f)' % (na, ca[0], ca[2], nb, cb[0], cb[2]))
                continue
            issues.append('COLLIDER %s (%.0f,%.0f) x %s (%.0f,%.0f)' % (na, ca[0], ca[2], nb, cb[0], cb[2]))
for (tx, tz, tr) in TREES:
    for (c, b) in bl:
        if c[6] in ('tree', 'ground') or c[6] in FURN:
            continue
        nx, nz = min(max(tx, b[0]), b[1]), min(max(tz, b[2]), b[3])
        if (nx - tx) ** 2 + (nz - tz) ** 2 < (tr * 0.8) ** 2 and b[5] > 8.5:
            issues.append('CANOPY tree (%.0f,%.0f r%.1f) x %s (%.0f,%.0f)' % (tx, tz, tr, c[6], c[0], c[2]))
for (c, b) in bl:
    if c[6] in FURN:
        for (rn, x0, x1, z0, z1) in ROADS:
            if b[0] < x1 and b[1] > x0 and b[2] < z1 and b[3] > z0:
                issues.append('ON-ROAD %s (%.0f,%.0f) in %s' % (c[6], c[0], c[2], rn))
for (c, b) in bl:
    if c[6] == 'car':
        ok = any(b[0] >= x0 - 0.1 and b[1] <= x1 + 0.1 and b[2] >= z0 - 0.1 and b[3] <= z1 + 0.1 for (rn, x0, x1, z0, z1) in LOT_RECTS)
        if not ok:
            issues.append('CAR off parking (%.0f,%.0f)' % (c[0], c[2]))

N = int(HALF * 2 // CELL_A) + 1
grid = [['.'] * N for _ in range(N)]


def mark(x0, x1, z0, z1, ch):
    for i in range(max(0, int((x0 + HALF) // CELL_A)), min(N, int((x1 + HALF) // CELL_A) + 1)):
        for j in range(max(0, int((z0 + HALF) // CELL_A)), min(N, int((z1 + HALF) // CELL_A) + 1)):
            if grid[j][i] in '.,':
                grid[j][i] = ch


for (c, b) in bl:
    mark(b[0], b[1], b[2], b[3], '#' if c[4] > 9 else 'o')
for z in ZONES_OCC:
    mark(*z[1:5], z[0])
lawn_cells = sum(r.count(',') for r in grid)
for (rn, x0, x1, z0, z1) in ROADS + LOT_RECTS:
    mark(x0, x1, z0, z1, '=')
for (tx, tz, tr) in TREES:
    mark(tx - tr, tx + tr, tz - tr, tz + tr, 't')
empty = sum(r.count('.') for r in grid)
with open(os.path.join(OUT, 'audit.txt'), 'w') as fh:
    fh.write('ISSUES %d\n' % len(issues))
    fh.write('\n'.join(issues) + '\n\nEMPTY CELLS %d of %d (cell %d studs), lawn-only cells %d\n' % (empty, N * N, CELL_A, lawn_cells))
    fh.write('\n'.join(''.join(r) for r in grid) + '\n')
print('AUDIT issues', len(issues), 'empty', empty, 'of', N * N)
