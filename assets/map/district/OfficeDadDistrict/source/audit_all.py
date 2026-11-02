# Full audit (exec'd after audit2.py, before the export).  Writes <out>/audit_all.txt.  Targets the defects that cost many fixes in Studio last time:
#   1 COPLANAR   same-direction coplanar overlapping faces of different colours (z-fighting) among ALL axis-aligned boxes
#   2 FLOATING   details that touch nothing (hanging above the ground)
#   3 UNCOVERED  reachable solid objects (y0 < 4) with no collider
#   4 NAV        flood fill on a 1-stud raster of the colliders: reach every anchor with an agent of R=1.6 (pathfinding) and with a 5-wide corridor (first person)
#   5 BUILDGAP   gaps between buildings narrower than 5 studs that are not closed
#   6 CONTRACT   signs, anchors, tags, names, chunk limits
#   7 BELOW      geometry below the ground / outside the border
import collections
import heapq

AUD = []


def log(title, lines, limit=60):
    AUD.append('%s: %d' % (title, len(lines)))
    for ln in sorted(lines)[:limit]:
        AUD.append('   ' + ln)
    if len(lines) > limit:
        AUD.append('   ... +%d more' % (len(lines) - limit))


# ---------------------------------------------------------------------------------------------------- 1 coplanar faces of boxes
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


BOXES = {}                                   # (kind, idx) -> bbox of every axis-aligned box item
BH = collections.defaultdict(list)


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


for _nm, _items in FENCE.items():                # fence sections are exported separately but occlude faces like any other box
    for _k, _it in enumerate(_items):
        _bi = box_info(_it)
        if _bi is not None:
            BOXES[('F' + _nm, _k)] = _bi
            for i in range(int(_bi[0] // 8), int(_bi[1] // 8) + 1):
                for j in range(int(_bi[4] // 8), int(_bi[5] // 8) + 1):
                    BH[(i, j)].append(('F' + _nm, _k))
FACES = collections.defaultdict(list)       # (axis, sign, bucket) -> [(coord, a0, a1, b0, b1, colour, kind, item index)]
nbox = 0
for kind in D.KINDS:
    for idx, it in enumerate(D.ITEMS[kind]):
        bi = box_info(it)
        if bi is None:
            continue
        nbox += 1
        x0, x1, y0, y1, z0, z1 = bi
        BOXES[(kind, idx)] = bi
        for i in range(int(x0 // 8), int(x1 // 8) + 1):
            for j in range(int(z0 // 8), int(z1 // 8) + 1):
                BH[(i, j)].append((kind, idx))
        fl = [(0, -1, x0, y0, y1, z0, z1), (0, 1, x1, y0, y1, z0, z1), (1, -1, y0, x0, x1, z0, z1), (1, 1, y1, x0, x1, z0, z1), (2, -1, z0, x0, x1, y0, y1), (2, 1, z1, x0, x1, y0, y1)]
        for (ax, sg, c, a0, a1, b0, b1) in fl:
            if ax == 1 and sg == -1 and c <= GY + 1e-6:
                continue                        # bottoms standing on the ground
            FACES[(ax, sg, int(round(c / 0.01)))].append((c, a0, a1, b0, b1, it[4], kind, idx))
coplanar = set()
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
                if f[5] == g[5] or f is g or abs(f[0] - g[0]) > 0.0151:
                    continue
                if (f[6], f[7]) == (g[6], g[7]):
                    continue
                oa = min(f[2], g[2]) - max(f[1], g[1])
                ob = min(f[4], g[4]) - max(f[3], g[3])
                if oa > 0.05 and ob > 0.05 and oa * ob > 0.05:
                    cx = (max(f[1], g[1]) + min(f[2], g[2])) / 2
                    cy = (max(f[3], g[3]) + min(f[4], g[4])) / 2
                    if buried(ax, sg, max(f[0], g[0]) if sg > 0 else min(f[0], g[0]), cx, cy, {(f[6], f[7]), (g[6], g[7])}):
                        continue                # both faces are inside other geometry: invisible, no z-fight
                    coplanar.add('axis%s%s at %.3f over (%.1f, %.1f) %.2fx%.2f  %s/%s' % ('xyz'[ax], '-+'[(sg + 1) // 2], f[0], cx, cy, oa, ob, f[5], g[5]))
PAIRS = collections.Counter()
for ln in coplanar:
    parts = ln.split()
    PAIRS[(parts[-1], parts[0][:5])] += 1
log('COPLANAR (z-fight, %d boxes)' % nbox, list(coplanar), limit=0)
open(os.path.join(OUT, 'coplanar_list.txt'), 'w').write(chr(10).join(sorted(coplanar)))
AUD.append('   top colour pairs:')
for (pair, ax), n in PAIRS.most_common(40):
    AUD.append('   %5d  %s  %s' % (n, pair, ax))

# ---------------------------------------------------------------------------------------------------- 2 floating details, 7 below ground
H8 = collections.defaultdict(list)
BB = []
for kind in D.KINDS:
    for idx, it in enumerate(D.ITEMS[kind]):
        v = it[2]
        b = (min(p[0] for p in v), max(p[0] for p in v), min(p[1] for p in v), max(p[1] for p in v), min(p[2] for p in v), max(p[2] for p in v))
        n = len(BB)
        BB.append((kind, idx, b))
        for i in range(int(b[0] // 8), int(b[1] // 8) + 1):
            for j in range(int(b[4] // 8), int(b[5] // 8) + 1):
                H8[(i, j)].append(n)
floating, below = [], []
E = 0.09
for n, (kind, idx, b) in enumerate(BB):
    if b[2] < -0.01 and not (b[3] <= GY + 1e-6):
        below.append('%s item y %.2f..%.2f at (%.0f,%.0f)' % (kind, b[2], b[3], (b[0] + b[1]) / 2, (b[4] + b[5]) / 2))
    if b[2] < GY - 0.05 and b[3] > GY + 0.05 and b[3] - b[2] > 0.3 and not (b[0] <= -HALF + 0.01):
        pass
    if b[2] <= GY + 0.06:
        continue
    touched = False
    seen = set()
    for i in range(int((b[0] - E) // 8), int((b[1] + E) // 8) + 1):
        for j in range(int((b[4] - E) // 8), int((b[5] + E) // 8) + 1):
            for m in H8.get((i, j), ()):
                if m == n or m in seen:
                    continue
                seen.add(m)
                o = BB[m][2]
                if o[0] <= b[1] + E and o[1] >= b[0] - E and o[2] <= b[3] + E and o[3] >= b[2] - E and o[4] <= b[5] + E and o[5] >= b[4] - E:
                    touched = True
                    break
            if touched:
                break
        if touched:
            break
    if not touched:
        floating.append('%s item (%.1f,%.1f,%.1f) size %.1fx%.1fx%.1f' % (kind, (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2, b[1] - b[0], b[3] - b[2], b[5] - b[4]))
log('FLOATING', floating)
log('BELOW-GROUND', below)

# ---------------------------------------------------------------------------------------------------- 3 reachable solids without collider
CBX = [(c[0] - c[3] / 2, c[0] + c[3] / 2, c[2] - c[5] / 2, c[2] + c[5] / 2, c[1] - c[4] / 2, c[1] + c[4] / 2, c[6]) for c in D.STATS['colliders'] if c[6] != 'ground']
CH = collections.defaultdict(list)
for k, c in enumerate(CBX):
    for i in range(int((c[0] - 1.0) // 16), int((c[1] + 1.0) // 16) + 1):
        for j in range(int((c[2] - 1.0) // 16), int((c[3] + 1.0) // 16) + 1):
            CH[(i, j)].append(k)
BNAMES = set(m[0].lower() for m in META) | {'tower'}
uncovered = set()
for kind in ('O',):
    for idx, it in enumerate(D.ITEMS[kind]):
        v = it[2]
        b = (min(p[0] for p in v), max(p[0] for p in v), min(p[1] for p in v), max(p[1] for p in v), min(p[2] for p in v), max(p[2] for p in v))
        if b[3] < GY + 0.9 or b[2] > 4.0 or (b[1] - b[0]) < 0.25 and (b[5] - b[4]) < 0.25:
            continue
        cx, cz = (b[0] + b[1]) / 2, (b[4] + b[5]) / 2
        cov = False
        for k in CH.get((int(cx // 16), int(cz // 16)), ()):
            c = CBX[k]
            m_ = 2.2 if c[6] == 'tree' else (1.8 if (b[2] > 3.0 and c[6] in BNAMES) else 0.6)    # branches / window flower boxes stick out of their collider
            if c[0] - m_ <= cx <= c[1] + m_ and c[2] - m_ <= cz <= c[3] + m_ and c[4] - 0.6 <= (b[2] + b[3]) / 2 <= c[5] + 0.6:
                cov = True
                break
        if not cov:
            uncovered.add('item (%.1f,%.1f) y%.1f..%.1f size %.1fx%.1f col %s' % (cx, cz, b[2], b[3], b[1] - b[0], b[5] - b[4], it[4]))
log('UNCOVERED solid items', list(uncovered))

# ---------------------------------------------------------------------------------------------------- 4 navigation raster
CELLN = 1.0
NN = int(2 * HALF / CELLN)
blocked = [bytearray(NN) for _ in range(NN)]
for c in D.STATS['colliders']:
    nm = c[6]
    if nm == 'ground':
        continue
    top, bot = c[1] + c[4] / 2, c[1] - c[4] / 2
    if not ((top - bot) > 1.0 and top > 2.2 and bot < 6.0):
        continue
    x0, x1, z0, z1 = c[0] - c[3] / 2, c[0] + c[3] / 2, c[2] - c[5] / 2, c[2] + c[5] / 2
    for i in range(max(0, int(x0 + HALF)), min(NN, int(math.ceil(x1 + HALF)))):
        row = blocked
        for j in range(max(0, int(z0 + HALF)), min(NN, int(math.ceil(z1 + HALF)))):
            row[j][i] = 1
for j in range(NN):
    for i in range(NN):
        pass


def dist_field():
    INF = 10 ** 6
    dist = [[INF] * NN for _ in range(NN)]
    dq = collections.deque()
    for j in range(NN):
        for i in range(NN):
            if blocked[j][i] or i in (0, NN - 1) and False:
                dist[j][i] = 0
                dq.append((i, j))
    while dq:
        i, j = dq.popleft()
        d = dist[j][i] + 1
        for (di, dj) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if 0 <= a < NN and 0 <= b < NN and dist[b][a] > d:
                dist[b][a] = d
                dq.append((a, b))
    return dist


DF = dist_field()


def reach(start, rad):
    si, sj = int(start[0] + HALF), int(start[1] + HALF)
    seen = {}
    if DF[sj][si] <= rad:
        return None
    st = [(si, sj)]
    seen[(si, sj)] = 1
    while st:
        i, j = st.pop()
        for (di, dj) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if 0 <= a < NN and 0 <= b < NN and (a, b) not in seen and DF[b][a] > rad:
                seen[(a, b)] = 1
                st.append((a, b))
    return seen


AN = D.STATS['anchors']
nav_lines = []
need = ['tower_entrance', 'connector_E', 'connector_W', 'connector_N', 'connector_S']
for rad, label in ((1.6, 'agent R=1.6'), (2.5, '5-wide corridor')):
    r0 = reach((AN['tower_exit_arrival'][0], AN['tower_exit_arrival'][2]), rad)
    if r0 is None:
        nav_lines.append('%s: tower_exit_arrival is blocked' % label)
        continue
    for nm in need:
        t = AN[nm]
        ok = (int(t[0] + HALF - (1 if t[0] >= HALF else 0)), int(t[2] + HALF - (1 if t[2] >= HALF else 0)))
        if ok not in r0:
            # the connector anchors sit on the border cell: test one stud inside
            ok2 = (int(t[0] - t[3] * 2 + HALF), int(t[2] - t[4] * 2 + HALF))
            if ok2 not in r0:
                nav_lines.append('%s: tower_exit_arrival -> %s NOT reachable' % (label, nm))
    nav_lines.append('%s: reachable cells %d' % (label, len(r0)))
# every door walkway, parking lot and place must belong to the main component (R=1.6) and show the narrow bits at 5-wide
main = reach((AN['tower_exit_arrival'][0], AN['tower_exit_arrival'][2]), 1.6)
main5 = reach((AN['tower_exit_arrival'][0], AN['tower_exit_arrival'][2]), 2.5)
iso = []
for (bid, rr, front, uc, wall, dw) in META:
    px, pz = lpos(front, rr, uc, 0.0)
    ox, oz = side_out(front, 0)
    c = (int(px + ox * 5.0 + HALF), int(pz + oz * 5.0 + HALF))
    if c not in main:
        iso.append('door of %s at (%.0f,%.0f) not reachable (R=1.6)' % (bid, px, pz))
    elif c not in main5:
        iso.append('door of %s at (%.0f,%.0f) reachable only by a corridor narrower than 5' % (bid, px, pz))
for (nm, x0, x1, z0, z1) in LOTS:
    c = (int((x0 + x1) / 2 + HALF), int((z0 + z1) / 2 + HALF))
    probe = [(int(x0 + 4 + HALF), int(z0 + 4 + HALF)), (int(x1 - 4 + HALF), int(z1 - 4 + HALF))]
    if not any(p in main for p in probe):
        iso.append('parking %s not reachable' % nm)
# narrow passages: cells reachable at R=1.6 but cut off at R=2.5, grouped
cut_cells = [k for k in main if k not in main5]
comp = []
seenc = set()
cs = set(cut_cells)
for k in cut_cells:
    if k in seenc:
        continue
    st = [k]
    seenc.add(k)
    pts = []
    while st:
        i, j = st.pop()
        pts.append((i, j))
        for (di, dj) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n_ = (i + di, j + dj)
            if n_ in cs and n_ not in seenc:
                seenc.add(n_)
                st.append(n_)
    comp.append(pts)
def in_lot(i, j):
    x, z = i - HALF, j - HALF
    return any(x0 - 1 <= x <= x1 + 1 and z0 - 1 <= z <= z1 + 1 for (nm, x0, x1, z0, z1) in LOTS) or abs(x) > FI - 7 or abs(z) > FI - 7


big = [[q for q in p if not in_lot(*q)] for p in comp]
big = [p for p in big if len(p) > 120]
for p in sorted(big, key=len, reverse=True)[:25]:
    cx = sum(q[0] for q in p) / len(p) - HALF
    cz = sum(q[1] for q in p) / len(p) - HALF
    iso.append('narrow region (<5 wide) ~%d cells around (%.0f, %.0f)' % (len(p), cx, cz))
log('NAV', nav_lines + iso)
with open(os.path.join(OUT, 'nav_debug.txt'), 'w') as fh:
    for j in range(0, NN, 2):
        fh.write(''.join('#' if blocked[j][i] else ('+' if DF[j][i] <= 2.5 else '.') for i in range(0, NN, 2)) + chr(10))

# ---------------------------------------------------------------------------------------------------- 5 building gaps
bgap = []
brs = [(m[0], m[1]) for m in META] + [('TOWER', TW)]
for a in range(len(brs)):
    for b in range(a + 1, len(brs)):
        (na, ra), (nb, rb) = brs[a], brs[b]
        dx = max(ra.x0 - rb.x1, rb.x0 - ra.x1, 0)
        dz = max(ra.z0 - rb.z1, rb.z0 - ra.z1, 0)
        if (dx > 0 and dz == 0 and dx < 5.0 and min(ra.z1, rb.z1) - max(ra.z0, rb.z0) > 0) or (dz > 0 and dx == 0 and dz < 5.0 and min(ra.x1, rb.x1) - max(ra.x0, rb.x0) > 0):
            bgap.append('%s - %s gap %.1f' % (na, nb, max(dx, dz)))
log('BUILDING GAPS < 5', bgap)

# ---------------------------------------------------------------------------------------------------- 6 contract
con = []
for s in SIGNS:
    if s[0] not in ('APARTMENTS', 'BUS'):
        con.append('sign %s not allowed' % s[0])
for nm in ('tower_entrance', 'tower_exit_arrival', 'connector_N', 'connector_S', 'connector_E', 'connector_W'):
    if nm not in D.STATS['anchors']:
        con.append('anchor %s missing' % nm)
for nm in ('bag_shop', 'ladder_giver'):
    if nm in D.STATS['anchors']:
        con.append('anchor %s must not exist (owner removed the shop and the workshop)' % nm)
gr = [c for c in D.STATS['colliders'] if c[6] == 'ground']
if len(gr) != 1 or abs(gr[0][1] + gr[0][4] / 2 - GY) > 1e-6:
    con.append('ground collider: need exactly one with top y = 1.0')
for c in D.STATS['colliders']:
    if min(c[3], c[4], c[5]) < 0.39 and c[6] not in ('sidewalk', 'walkway', 'plaza', 'parkpath', 'gardpath', 'gardplaza', 'fountain_plaza', 'lamp', 'bollard', 'mailbox', 'hydrant', 'tlight', 'tree', 'buspost', 'column', 'pergola_post', 'bike', 'seesaw'):
        con.append('thin collider %s %.2fx%.2fx%.2f at (%.0f,%.0f)' % (c[6], c[3], c[4], c[5], c[0], c[2]))
log('CONTRACT', con)

with open(os.path.join(OUT, 'audit_all.txt'), 'w', encoding='utf-8') as fh:
    fh.write('FULL AUDIT OfficeDadDistrict\n')
    fh.write('\n'.join(AUD) + '\n')
print('AUDIT_ALL', {l.split(':')[0]: int(l.split(':')[-1]) for l in AUD if not l.startswith('   ')})
