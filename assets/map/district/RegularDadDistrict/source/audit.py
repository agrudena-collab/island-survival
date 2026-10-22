# Audit of the generated district (exec'd by build_district.py after layout.py, before the export).
# Writes <out>/audit.txt: overlaps between colliders / canopies / roads and an ASCII occupancy map (8 studs per cell).
import math

CELL_A = 8
ROADS = [('mainEW', -SZ - 6, SZ + 6, -RW, RW), ('mainNS', -RW, RW, -SZ - 6, SZ + 6)]
for zc, x0, x1 in ((-145, -SZ - 6, -SW), (-145, SW, SZ + 6), (145, -SZ - 6, -SW)):
    ROADS.append(('service%d' % zc, x0, x1, zc - 8, zc + 8))
ROADS.append(('driveway', -100, -88, -137, -132))
LOTS = [('parking', 40, 214, -128, -98), ('courtyard', -124, -66, -128, -96), ('fuel', -118.5, -85.5, 52, 92)]   # cars may stand here, furniture too

JOINTS = ('fence', 'courtfence', 'dogfence')
SKIP = ('ground', 'edgeN', 'edgeS', 'edgeW', 'edgeE')
cols = [c for c in D.STATS['colliders'] if c[6] not in SKIP]


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
            if na in JOINTS and nb in JOINTS:
                continue            # fence corners and court fences join at their ends
            # a tree trunk / lamp inside a planter or a table inside its own cafe terrace are intended
            issues.append('COLLIDER %s (%.0f,%.0f) x %s (%.0f,%.0f)' % (na, ca[0], ca[2], nb, cb[0], cb[2]))
# canopies of trees vs buildings / cars / lamps
for (tx, tz, tr) in TREES:
    for (c, b) in bl:
        if c[6] in ('tree', 'ground'):
            continue
        if c[6] in ('lamp', 'bench', 'bin', 'hydrant', 'mailbox', 'bollard', 'planter'):
            continue            # low furniture under a canopy is fine
        nx, nz = min(max(tx, b[0]), b[1]), min(max(tz, b[2]), b[3])
        if (nx - tx) ** 2 + (nz - tz) ** 2 < (tr * 0.8) ** 2 and b[5] > 8.5:
            issues.append('CANOPY tree (%.0f,%.0f r%.1f) x %s (%.0f,%.0f)' % (tx, tz, tr, c[6], c[0], c[2]))
# furniture on asphalt
for (c, b) in bl:
    if c[6] in ('tree', 'lamp', 'bench', 'bin', 'hydrant', 'mailbox', 'bollard', 'tlight', 'cafe_table', 'planter'):
        for (rn, x0, x1, z0, z1) in ROADS:
            if b[0] < x1 and b[1] > x0 and b[2] < z1 and b[3] > z0 and not (rn == 'parking' and c[6] == 'tree'):
                issues.append('ON-ROAD %s (%.0f,%.0f) in %s' % (c[6], c[0], c[2], rn))
# cars must stay on asphalt
for (c, b) in bl:
    if c[6] == 'car':
        ok = any(b[0] >= x0 - 0.1 and b[1] <= x1 + 0.1 and b[2] >= z0 - 0.1 and b[3] <= z1 + 0.1 for (rn, x0, x1, z0, z1) in ROADS + LOTS)
        if not ok:
            issues.append('CAR off asphalt (%.0f,%.0f)' % (c[0], c[2]))

# occupancy map
N = int((SZ + 30) * 2 // CELL_A)
grid = [['.'] * N for _ in range(N)]


def mark(x0, x1, z0, z1, ch):
    for i in range(max(0, int((x0 + SZ + 30) // CELL_A)), min(N, int((x1 + SZ + 30) // CELL_A) + 1)):
        for j in range(max(0, int((z0 + SZ + 30) // CELL_A)), min(N, int((z1 + SZ + 30) // CELL_A) + 1)):
            if grid[j][i] in '.,':
                grid[j][i] = ch


for (c, b) in bl:
    mark(b[0], b[1], b[2], b[3], '#' if c[4] > 9 else 'o')
for z in ZONES_OCC:
    mark(*z[1:5], z[0])
lawn = sum(r.count(',') for r in grid)
for (rn, x0, x1, z0, z1) in ROADS + LOTS:
    mark(x0, x1, z0, z1, '=')
for (tx, tz, tr) in TREES:
    mark(tx - tr, tx + tr, tz - tr, tz + tr, 't')
empty = sum(r.count('.') for r in grid)
with open(os.path.join(OUT, 'audit.txt'), 'w') as fh:
    fh.write('ISSUES %d\n' % len(issues))
    fh.write('\n'.join(issues) + '\n\nEMPTY CELLS %d of %d (cell %d studs), lawn-only cells %d\n' % (empty, N * N, CELL_A, lawn))
    fh.write('\n'.join(''.join(r) for r in grid) + '\n')
print('AUDIT issues', len(issues), 'empty', empty, 'of', N * N)
