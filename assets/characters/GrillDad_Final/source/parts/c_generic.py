# ---------------------------------------------------------------- generic generators
class Limb:
    """Limb frame proximal P0 -> distal P1. U = world X projected perpendicular to A (width), Q = A x U (depth)."""

    def __init__(self, P0, P1):
        self.P0, self.P1 = V(P0), V(P1)
        d = self.P1 - self.P0
        self.L = d.length
        self.A = d / self.L
        u = V((1, 0, 0)) - self.A * V((1, 0, 0)).dot(self.A)
        if u.length < 1e-4:
            u = V((0, -1, 0)) - self.A * V((0, -1, 0)).dot(self.A)
        self.U = u.normalized()
        self.Q = self.A.cross(self.U).normalized()

    def at(self, t):
        return self.P0 + self.A * (self.L * t)

    def ring(self, t, w, d, c, grow=0.0):
        P = self.at(t)
        a, h = w / 2.0 + grow, d / 2.0 + grow
        c = min(c, a - 1e-4, h - 1e-4)
        pts = [(-a + c, -h), (a - c, -h), (a, -h + c), (a, h - c), (a - c, h), (-a + c, h), (-a, h - c), (-a, -h + c)]
        return [P + self.U * x + self.Q * y for x, y in pts]


def ring_pts(P, B, N, w, t, n=8, c=None):
    """Cross-section ring at P with width dir B, thickness dir N. n==8 -> chamfered rectangle, else ellipse with n points."""
    a, h = w / 2.0, t / 2.0
    if n == 8:
        cc = min(a, h) * 0.45 if c is None else min(c, a - 1e-5, h - 1e-5)
        pts = [(-a + cc, -h), (a - cc, -h), (a, -h + cc), (a, h - cc), (a - cc, h), (-a + cc, h), (-a, h - cc), (-a, -h + cc)]
    else:
        pts = [(a * math.cos(2 * math.pi * k / n + math.pi / n), h * math.sin(2 * math.pi * k / n + math.pi / n)) for k in range(n)]
    return [P + B * x + N * y for x, y in pts]


def frames_along(pts, up=V((1, 0, 0))):
    out = []
    n = len(pts)
    for i, p in enumerate(pts):
        T = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        u = V(up)
        if abs(T.dot(u)) > 0.97:
            u = V((0, -1, 0))
        N = (u - T * T.dot(u)).normalized()
        B = T.cross(N).normalized()
        out.append((p, T, B, N))
    return out


def sweep(pm, cid, pts, wd, th, tile, up=V((1, 0, 0)), n=8, caps=(True, True), c=None, meta_=None):
    """Closed solid swept along pts (list of V); wd/th scalars or per-point lists; ellipse rings (n!=8) or chamfered-rect rings (n==8)."""
    m = len(pts)
    wd = wd if isinstance(wd, (list, tuple)) else [wd] * m
    th = th if isinstance(th, (list, tuple)) else [th] * m
    rings = []
    for (p, T, B, N), w, t in zip(frames_along(pts, up), wd, th):
        rings.append(ring_pts(p, B, N, w, t, n, c))
    loft(pm, cid, rings, tile, caps=caps, meta=meta_ or PRE)
    return rings


def lathe(pm, cid, profile, cx, cd, segs, tile, band_tiles=None, caps=(True, True), meta_=None, rot=0.0):
    """Surface of revolution about the H axis through (cx,cd): profile [(r,h)] open curve + planar caps at both ends."""
    rings = []
    for r, h in profile:
        rings.append([V((cx + r * math.cos(2 * math.pi * k / segs + rot), cd + r * math.sin(2 * math.pi * k / segs + rot), h)) for k in range(segs)])
    loft(pm, cid, rings, tile, caps=caps, band_tiles=band_tiles, meta=meta_ or PRE)


def loop_solid(pm, cid, sections, tile, meta_=None):
    """Periodic loft: list of cross-section point lists closed around the loop (torus-like solid)."""
    n, m = len(sections), len(sections[0])
    P = [p for s in sections for p in s]
    faces = []
    for i in range(n):
        j = (i + 1) % n
        for k in range(m):
            k2 = (k + 1) % m
            faces.append([i * m + k, i * m + k2, j * m + k2, j * m + k])
    pm.solid(cid, P, faces, tile, meta_ or PRE)


def grid_solid(pm, cid, outer, inner, tile, meta_=None):
    """Closed slab from two same-topology grids outer[l][k], inner[l][k] (l: levels, k: columns)."""
    L, K = len(outer), len(outer[0])
    P = [p for r in outer for p in r] + [p for r in inner for p in r]
    off = L * K
    o = lambda l, k: l * K + k
    i_ = lambda l, k: off + l * K + k
    F = []
    for l in range(L - 1):
        for k in range(K - 1):
            F.append([o(l, k), o(l, k + 1), o(l + 1, k + 1), o(l + 1, k)])
            F.append([i_(l, k), i_(l + 1, k), i_(l + 1, k + 1), i_(l, k + 1)])
    for l in range(L - 1):
        F.append([o(l, 0), o(l + 1, 0), i_(l + 1, 0), i_(l, 0)])
        F.append([o(l, K - 1), i_(l, K - 1), i_(l + 1, K - 1), o(l + 1, K - 1)])
    for k in range(K - 1):
        F.append([o(0, k), i_(0, k), i_(0, k + 1), o(0, k + 1)])
        F.append([o(L - 1, k), o(L - 1, k + 1), i_(L - 1, k + 1), i_(L - 1, k)])
    pm.solid(cid, P, F, tile, meta_ or OBS)


def band(pm, cid, levels, pathfn, t_out, t_in, tile, meta_=None):
    """Open ribbon wrapped around a (x,d) path per height level; offsets along the 2D outward normal."""
    outer, inner = [], []
    for h in levels:
        path = pathfn(h)
        cen = sum((V((p[0], p[1], 0)) for p in path), V()) / len(path)
        ro, ri = [], []
        n = len(path)
        for k, p in enumerate(path):
            a = V((path[min(k + 1, n - 1)][0] - path[max(k - 1, 0)][0], path[min(k + 1, n - 1)][1] - path[max(k - 1, 0)][1], 0))
            nn = V((a.y, -a.x, 0)).normalized()
            if nn.dot(V((p[0], p[1], 0)) - cen) < 0:
                nn = -nn
            ro.append(V((p[0] + nn.x * t_out, p[1] + nn.y * t_out, h)))
            ri.append(V((p[0] + nn.x * t_in, p[1] + nn.y * t_in, h)))
        outer.append(ro)
        inner.append(ri)
    grid_solid(pm, cid, outer, inner, tile, meta_)


def poly_rows(outline, hs):
    rows = []
    n = len(outline)
    for h in hs:
        xs = []
        for i in range(n):
            (x1, h1), (x2, h2) = outline[i], outline[(i + 1) % n]
            if abs(h1 - h2) < 1e-9:
                if abs(h1 - h) < 1e-9:
                    xs += [x1, x2]
            elif min(h1, h2) - 1e-9 <= h <= max(h1, h2) + 1e-9:
                xs.append(x1 + (x2 - x1) * (h - h1) / (h2 - h1))
        if xs:
            rows.append((h, min(xs), max(xs)))
    return rows


def auto_hs(outline, step=0.16):
    hv = sorted({round(p[1], 6) for p in outline})
    hs = []
    for a, b in zip(hv, hv[1:]):
        k = max(1, int(math.ceil((b - a) / step)))
        hs += [a + (b - a) * i / k for i in range(k)]
    hs.append(hv[-1])
    return hs


def patch(pm, cid, outline, fit, d_back, d_front, tile, ch=0.0, nx=6, step=0.16, rear=False, meta_=None):
    """Slab hugging the surface fit(x,h)->D over the polygon outline [(x,h)]. d_* = distance along the outward direction
    (forward = -D; rear=True -> +D). The front layer is chamfered inward by ch."""
    sg = 1.0 if rear else -1.0
    rows = poly_rows(outline, auto_hs(outline, step))
    outer, inner = [], []
    for li, (h, lo, hi) in enumerate(rows):
        ro, ri = [], []
        for k in range(nx):
            x = lo + (hi - lo) * k / (nx - 1)
            xf, hf_ = x, h
            if ch:
                if k == 0:
                    xf = x + ch
                if k == nx - 1:
                    xf = x - ch
                if li == 0:
                    hf_ = h + ch
                if li == len(rows) - 1:
                    hf_ = h - ch
            ro.append(V((xf, fit(xf, hf_) + sg * d_front, hf_)))
            ri.append(V((x, fit(x, h) + sg * d_back, h)))
        outer.append(ro)
        inner.append(ri)
    grid_solid(pm, cid, outer, inner, tile, meta_)


def plate(pm, cid, outline, back_fn, front_fn, tile, ch=0.02, meta_=None):
    """Closed plate over polygon outline [(x,h)]: back layer D=back_fn, front chamfer ring, front face D=front_fn (forward=-D)."""
    xs = [p[0] for p in outline]
    hs = [p[1] for p in outline]
    cx, chh = (min(xs) + max(xs)) / 2, (min(hs) + max(hs)) / 2
    wd, ht = max(xs) - min(xs), max(hs) - min(hs)
    sx = max(0.0, 1 - 2 * ch / wd) if wd > 0 else 1
    sh = max(0.0, 1 - 2 * ch / ht) if ht > 0 else 1
    n = len(outline)
    P = []
    for x, h in outline:
        P.append(V((x, back_fn(x, h), h)))
    for x, h in outline:
        P.append(V((x, front_fn(x, h) + ch, h)))
    for x, h in outline:
        xx, hh = cx + (x - cx) * sx, chh + (h - chh) * sh
        P.append(V((xx, front_fn(xx, hh), hh)))
    faces = []
    for r in range(2):
        for k in range(n):
            faces.append([r * n + k, r * n + (k + 1) % n, (r + 1) * n + (k + 1) % n, (r + 1) * n + k])
    faces += cap_tris(P, list(range(n)))
    faces += cap_tris(P, list(range(2 * n, 3 * n)))
    pm.solid(cid, P, faces, tile, meta_ or OBS)


def disc_d(pm, cid, cx, cd, h, r, thick, tile, segs=8, ry=None, embed=0.0):
    """Disc / button facing -D: front face at D=cd, thick towards +D (+embed). ry = vertical radius (ellipse)."""
    ry = ry or r
    rings = []
    for dd in (cd, cd + thick + embed):
        rings.append([V((cx + r * math.cos(2 * math.pi * k / segs + math.pi / segs), dd, h + ry * math.sin(2 * math.pi * k / segs + math.pi / segs))) for k in range(segs)])
    loft(pm, cid, rings, tile, meta=PRE)


def box_c(pm, cid, c, size, tile, ch=0.0, meta_=None, xf=None):
    sx, sd, sh = size
    if ch > 0:
        rings = cbox(c, size, ch, xf=xf)
    else:
        rings = box_rings(c[0] - sx / 2, c[0] + sx / 2, c[1] - sd / 2, c[1] + sd / 2, c[2] - sh / 2, c[2] + sh / 2)
        if xf:
            rings = [[xf(p) for p in r] for r in rings]
    loft(pm, cid, rings, tile, meta=meta_ or PRE)


def mirror_pts(pts):
    return [(-x, h) for x, h in pts]
