"""Layer / seam cleanup on the final geometry (used by the FBX export and the audit).

Works on components: dict(polys=[tuple of (x, y, z)], hex=colour, grp=..., kd=...).
1. axis-aligned rectangular faces on one plane that face the same way and overlap (z-fighting layers, duplicates) -> the smaller face stays,
   the covered part is cut out of the larger one (same material duplicates collapse to one face);
2. neighbouring rectangles of the same colour on one plane are glued into bigger rectangles (no tessellation seams);
3. all vertices of a component are welded (1e-4).
"""
import collections

TOL = 0.011      # planes closer than this count as one plane
MIN_A = 1e-4


def _rect(poly):
    """-> (axis, sign, plane, a0, a1, b0, b1) for an axis-aligned rectangle face, else None"""
    if len(poly) != 4:
        return None
    for ax in range(3):
        lo = min(p[ax] for p in poly)
        hi = max(p[ax] for p in poly)
        if hi - lo < 1e-4:
            o = [k for k in range(3) if k != ax]
            o = {0: (1, 2), 1: (2, 0), 2: (0, 1)}[ax]
            a0, a1 = min(p[o[0]] for p in poly), max(p[o[0]] for p in poly)
            b0, b1 = min(p[o[1]] for p in poly), max(p[o[1]] for p in poly)
            area = (a1 - a0) * (b1 - b0)
            if area < MIN_A:
                return None
            # polygon area (shoelace in the o0/o1 plane) must equal the rect area
            s = 0.0
            for i in range(4):
                p, q = poly[i], poly[(i + 1) % 4]
                s += p[o[0]] * q[o[1]] - q[o[0]] * p[o[1]]
            if abs(abs(s) / 2 - area) > 1e-3 * max(1.0, area):
                return None
            sign = 1 if s > 0 else -1          # (o0, o1) is right-handed around +ax
            return (ax, sign, sum(p[ax] for p in poly) / 4, a0, a1, b0, b1)
    return None


def _quad(ax, sign, pl, a0, a1, b0, b1):
    o = {0: (1, 2), 1: (2, 0), 2: (0, 1)}[ax]
    pts = []
    for (a, b) in ((a0, b0), (a1, b0), (a1, b1), (a0, b1)):
        p = [0.0, 0.0, 0.0]
        p[ax] = pl
        p[o[0]] = a
        p[o[1]] = b
        pts.append(tuple(p))
    return tuple(pts) if sign > 0 else tuple(reversed(pts))


def _sub(r, c):
    """rect r minus rect c -> list of rects ((a0,a1,b0,b1))"""
    a0, a1, b0, b1 = r
    c0, c1, d0, d1 = c
    if c1 <= a0 + 1e-6 or c0 >= a1 - 1e-6 or d1 <= b0 + 1e-6 or d0 >= b1 - 1e-6:
        return [r]
    out = []
    if c0 > a0 + 1e-6:
        out.append((a0, c0, b0, b1))
    if c1 < a1 - 1e-6:
        out.append((c1, a1, b0, b1))
    m0, m1 = max(a0, c0), min(a1, c1)
    if d0 > b0 + 1e-6:
        out.append((m0, m1, b0, d0))
    if d1 < b1 - 1e-6:
        out.append((m0, m1, d1, b1))
    return [x for x in out if (x[1] - x[0]) * (x[3] - x[2]) > MIN_A]


def _ov(r, c):
    return min(r[1], c[1]) - max(r[0], c[0]) > 0.01 and min(r[3], c[3]) - max(r[2], c[2]) > 0.01


def _buckets(comps, skip_kd=()):
    """(grp-side, axis, sign, plane-cluster) -> list of [comp, face index, rect4, plane]"""
    raw = collections.defaultdict(list)
    for ci, cp in enumerate(comps):
        for fi, poly in enumerate(cp['polys']):
            r = _rect(poly)
            if r is None:
                continue
            raw[(cp['grp'] if cp['grp'] in ('Biome', 'Car') else 'house', r[0], r[1])].append((r[2], ci, fi, r[3:]))
    out = []
    for key, lst in raw.items():
        lst.sort(key=lambda t: t[0])
        cl = [lst[0]]
        for t in lst[1:]:
            if t[0] - cl[-1][0] > TOL:
                if len(cl) > 1:
                    out.append((key, cl))
                cl = []
            cl.append(t)
        if len(cl) > 1:
            out.append((key, cl))
    return out


def count_layers(comps):
    n = 0
    for key, cl in _buckets(comps):
        cl = sorted(cl, key=lambda t: t[3][0])
        for i in range(len(cl)):
            for j in range(i + 1, len(cl)):
                if cl[j][3][0] >= cl[i][3][1]:
                    break
                if cl[i][1:3] != cl[j][1:3] and _ov(cl[i][3], cl[j][3]):
                    n += 1
    return n


def resolve(comps):
    """cut overlapped parts out of the larger coplanar face; returns (pairs found, faces removed, faces cut)"""
    pairs = removed = cut = 0
    for key, cl in _buckets(comps):
        area = lambda t: (t[3][1] - t[3][0]) * (t[3][3] - t[3][2])
        order = sorted(range(len(cl)), key=lambda i: (area(cl[i]), cl[i][1], cl[i][2]))
        frag = {i: [cl[i][3]] for i in range(len(cl))}
        for ii, i in enumerate(order):
            ri = cl[i][3]
            for j in order[ii + 1:]:
                if cl[i][1:3] == cl[j][1:3] or not frag[j]:
                    continue
                if _ov(ri, cl[j][3]):
                    pairs += 1
                    new = []
                    for f in frag[j]:
                        new += _sub(f, ri)
                    frag[j] = new
        for i, t in enumerate(cl):
            if frag[i] == [t[3]]:
                continue
            ci, fi = t[1], t[2]
            cp = comps[ci]
            old = cp['polys'][fi]
            if not frag[i]:
                cp['polys'][fi] = None
                removed += 1
            else:
                cut += 1
                ax, sign = key[1], key[2]
                cp['polys'][fi] = None
                cp.setdefault('extra', []).extend(_quad(ax, sign, t[0], *f) for f in frag[i])
    for cp in comps:
        cp['polys'] = [p for p in cp['polys'] if p is not None] + cp.pop('extra', [])
    return pairs, removed, cut


def glue(comps):
    """merge same-colour neighbouring coplanar rectangles inside a component (identical edge extent) -> fewer faces"""
    merged = 0
    for cp in comps:
        rects = collections.defaultdict(list)
        rest = []
        for poly in cp['polys']:
            r = _rect(poly)
            if r is None:
                rest.append(poly)
            else:
                rects[(r[0], r[1], round(r[2], 4))].append(list(r[3:]))
        out = rest
        for (ax, sign, pl), lst in rects.items():
            ch = True
            while ch:
                ch = False
                lst.sort()
                res = []
                used = [False] * len(lst)
                for i, a in enumerate(lst):
                    if used[i]:
                        continue
                    for j in range(i + 1, len(lst)):
                        if used[j]:
                            continue
                        b = lst[j]
                        if abs(a[2] - b[2]) < 1e-4 and abs(a[3] - b[3]) < 1e-4 and (abs(a[1] - b[0]) < 1e-4 or abs(b[1] - a[0]) < 1e-4):
                            a = [min(a[0], b[0]), max(a[1], b[1]), a[2], a[3]]
                            used[j] = True
                            ch = True
                            merged += 1
                        elif abs(a[0] - b[0]) < 1e-4 and abs(a[1] - b[1]) < 1e-4 and (abs(a[3] - b[2]) < 1e-4 or abs(b[3] - a[2]) < 1e-4):
                            a = [a[0], a[1], min(a[2], b[2]), max(a[3], b[3])]
                            used[j] = True
                            ch = True
                            merged += 1
                    res.append(a)
                lst[:] = res
            out += [_quad(ax, sign, pl, *r) for r in lst]
        cp['polys'] = out
    return merged


def weld(cp, d=1e-4):
    """-> verts, faces of the component with welded vertices (degenerate faces dropped)"""
    idx, verts, faces = {}, [], []
    for poly in cp['polys']:
        f = []
        for p in poly:
            k = (round(p[0] / d), round(p[1] / d), round(p[2] / d))
            if k not in idx:
                idx[k] = len(verts)
                verts.append(tuple(p))
            if not f or f[-1] != idx[k]:
                f.append(idx[k])
        if len(f) > 1 and f[0] == f[-1]:
            f.pop()
        if len(f) >= 3 and len(set(f)) == len(f):
            faces.append(tuple(f))
    return verts, faces
