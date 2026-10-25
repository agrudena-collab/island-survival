"""OfficeDad's car: a separate, detailed model (mid-size sedan, navy, one scale unit = about 0.3 m).

Local frame (same as every model): lx right, h up, lz forward (front bumper at +lz).  Origin = centre of the car on the ground.
Overall: length 15.2, width 6.3, height 4.8, wheelbase 9.2, wheel diameter 2.5.  Only vertex colours, no seams / panel lines.
Built as lofted cross-sections (rounded boxes) for the body and the glass house, with separate lamps, grille, bumpers, mirrors, wheels and interior.
"""
import math
import odh_core as K
from odh_core import tf_pop
SC = [1.0]          # global scale of the model (1.0 = full size 15.2 long); every primitive below goes through the scaled wrappers


def emit(c, col, verts, faces, two=False):
    k = SC[0]
    K.emit(c, col, [(x * k, y * k, z * k) for (x, y, z) in verts], faces, two)


def rbox(col, cx, cz, y0, sx, sy, sz, r=0.1, seg=2, c=None):
    k = SC[0]
    K.rbox(col, cx * k, cz * k, y0 * k, sx * k, sy * k, sz * k, r * k, seg, c=c)


def sphere(col, cx, cz, cy, rx, ry=None, rz=None, seg=16, rings=9, c=None):
    k = SC[0]
    K.sphere(col, cx * k, cz * k, cy * k, rx * k, (ry if ry is not None else rx) * k, (rz if rz is not None else rx) * k, seg, rings, c=c)


def tube(col, pts, r, seg=8, closed=False, caps=True, r_end=None, c=None):
    k = SC[0]
    K.tube(col, [(x * k, y * k, z * k) for (x, y, z) in pts], r * k, seg, closed, caps, None if r_end is None else r_end * k, c=c)


def torus(col, cx, cz, cy, R, r, plane='xz', seg=24, tseg=7, c=None):
    k = SC[0]
    K.torus(col, cx * k, cz * k, cy * k, R * k, r * k, plane, seg, tseg, c=c)


def tf_push(x, z, y0=0.0, rot=0.0):
    k = SC[0]
    K.tf_push(x * k, z * k, y0 * k, rot)


def MT(n):
    return n

L, W, HGT, WB = 15.2, 6.3, 4.8, 9.2
N = 36


def _ring(z, hw, yb, yt, n=3.4):
    ym, hh = (yb + yt) / 2, (yt - yb) / 2
    pts = []
    for i in range(N):
        a = 2 * math.pi * i / N
        cs, sn = math.cos(a), math.sin(a)
        pts.append((hw * math.copysign(abs(cs) ** (2.0 / n), cs), ym + hh * math.copysign(abs(sn) ** (2.0 / n), sn), z))
    return pts


def loft(c, col, secs, n=3.4):
    """secs = [(z, half width, y bottom, y top)] from the rear to the front; closed with end caps"""
    rings = [_ring(*s, n=n) for s in secs]
    verts = [p for r in rings for p in r]
    faces = []
    for k in range(len(rings) - 1):
        for i in range(N):
            j = (i + 1) % N
            faces.append((k * N + i, k * N + j, (k + 1) * N + j, (k + 1) * N + i))
    faces.append(tuple(reversed(range(N))))
    faces.append(tuple(range((len(rings) - 1) * N, len(rings) * N)))
    emit(c, MT(col), verts, faces)


def revolve_x(c, col, prof, cxl, seg=40):
    """surface of revolution about the local x axis through (cxl, y=0, z=0): prof = [(x offset, radius)] -> closed shell"""
    verts, faces = [], []
    for (dx, r) in prof:
        for i in range(seg):
            a = 2 * math.pi * i / seg
            verts.append((cxl + dx, math.sin(a) * r, math.cos(a) * r))
    for k in range(len(prof) - 1):
        for i in range(seg):
            j = (i + 1) % seg
            faces.append((k * seg + i, (k + 1) * seg + i, (k + 1) * seg + j, k * seg + j))
    if prof[0][1] > 0.001:
        faces.append(tuple(range(seg - 1, -1, -1)))
    if prof[-1][1] > 0.001:
        faces.append(tuple(range((len(prof) - 1) * seg, len(prof) * seg)))
    emit(c, col, verts, faces)


def wheel(c, sx, z):
    """tyre, rim, dark dish, spokes, hub: all revolved around the axle (x axis); sx = side (+1 / -1), outer face looks to sx"""
    tf_push(sx * 2.86, z, 1.25, 0)
    o = sx
    revolve_x(c, MT('black'), [(-0.34 * o, 0.66), (-0.36 * o, 0.98), (-0.27 * o, 1.2), (-0.1 * o, 1.26), (0.1 * o, 1.26), (0.27 * o, 1.2), (0.36 * o, 0.98), (0.34 * o, 0.66)], 0.0, 44)
    revolve_x(c, MT('metal'), [(0.4 * o, 0.0), (0.4 * o, 0.7), (0.38 * o, 0.84), (0.3 * o, 0.84), (0.3 * o, 0.0)], 0.0, 36)   # rim face
    revolve_x(c, MT('metal_dk'), [(0.44 * o, 0.0), (0.44 * o, 0.62), (0.3 * o, 0.62), (0.3 * o, 0.0)], 0.0, 36)
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.3
        tube(MT('dark'), [(o * 0.5, math.sin(a) * 0.2, math.cos(a) * 0.2), (o * 0.5, math.sin(a) * 0.74, math.cos(a) * 0.74)], 0.12, 5, c=c)
    sphere(MT('metal'), o * 0.52, 0, 0, 0.08, 0.24, 0.24, 14, 5, c=c)
    tf_pop()


def interior(c):
    """full interior trim, all on top of the belt line (the body below is solid): carpet, headliner, door cards, pillar trim, dashboard
    with cluster / screen / vents / glove box, steering wheel, pedals, console with shifter, front seats and rear bench with belts, parcel shelf"""
    D_, CR, BK = MT('dark'), MT('cream'), MT('black')
    rbox(MT('burg'), 0, -0.6, 3.3, 4.5, 0.05, 8.4, 0.02, 1, c=c)                      # floor carpet
    loft(c, 'cream', [(-3.5, 2.0, 4.2, 4.4), (-2.6, 2.1, 4.2, 4.42), (1.0, 2.1, 4.2, 4.42), (1.6, 2.0, 4.2, 4.38)], n=4.0)   # headliner
    rbox(BK, 0, 1.55, 4.18, 1.2, 0.12, 0.35, 0.04, 1, c=c)                            # sun-visor strip / light
    for sx in (-1, 1):
        # door cards: front and rear, armrest, handle, speaker, window switch
        for (z0, z1) in ((2.1, -0.1), (-0.6, -3.9)):
            zc, dz = (z0 + z1) / 2, abs(z0 - z1)
            rbox(CR, sx * 2.14, zc, 3.3, 0.14, 0.8, dz, 0.05, 1, c=c)
            rbox(D_, sx * 2.02, zc, 3.62, 0.2, 0.14, dz - 0.4, 0.05, 1, c=c)
            rbox(MT('metal'), sx * 2.0, zc - dz * 0.25, 3.84, 0.12, 0.1, 0.45, 0.03, 1, c=c)
            sphere(BK, sx * 2.04, zc + dz * 0.2, 3.5, 0.06, 0.2, 0.2, 10, 5, c=c)
        # pillar trim
        rbox(D_, sx * 2.22, 2.2, 3.35, 0.14, 0.7, 0.3, 0.04, 1, c=c)
        rbox(D_, sx * 2.2, -4.2, 3.35, 0.14, 0.5, 0.35, 0.04, 1, c=c)
        # seat belts
        tube(BK, [(sx * 2.0, 4.15, -0.55), (sx * 0.95 if sx < 0 else sx * 0.8, 3.55, 0.2)], 0.05, 5, c=c)
    # dashboard
    rbox(D_, 0, 2.55, 3.3, 4.5, 0.32, 1.15, 0.1, 2, c=c)
    rbox(D_, 0, 2.2, 3.55, 4.4, 0.18, 0.55, 0.08, 2, c=c)
    rbox(BK, -0.95, 2.6, 3.62, 1.3, 0.3, 0.45, 0.1, 2, c=c)                            # instrument cluster hood
    rbox(MT('lamp'), -0.95, 2.37, 3.78, 0.95, 0.1, 0.05, 0.02, 1, c=c)                 # lit gauges
    rbox(BK, 0.2, 2.65, 3.64, 0.95, 0.42, 0.1, 0.04, 1, c=c)                           # centre screen
    rbox(MT('blue'), 0.2, 2.6, 3.68, 0.8, 0.3, 0.04, 0.02, 1, c=c)
    for vx in (-0.9, 0.0, 1.0, 1.9):
        rbox(MT('metal'), vx, 2.6, 3.5, 0.5, 0.1, 0.06, 0.02, 1, c=c)                  # air vents
    rbox(CR, 1.45, 2.78, 3.38, 1.5, 0.3, 0.06, 0.03, 1, c=c)                           # glove box lid (colour block, no seam)
    # steering wheel, column, pedals
    tf_push(-0.95, 2.05, 3.78, 0)
    torus(BK, 0, 0, 0, 0.5, 0.07, 'xz', 24, 6, c=c)
    sphere(BK, 0, 0, 0, 0.16, 0.08, 0.16, 10, 5, c=c)
    for sa in (0.0, 2.1, 4.2):
        tube(BK, [(0, 0, 0), (math.cos(sa) * 0.45, 0, math.sin(sa) * 0.45)], 0.05, 4, c=c)
    tf_pop()
    tube(BK, [(-0.95, 3.7, 2.4), (-0.95, 3.4, 2.0)], 0.09, 6, c=c)
    for px in (-1.35, -0.95, -0.55):
        rbox(MT('metal_dk'), px, 2.35, 3.33, 0.28, 0.14, 0.12, 0.03, 1, c=c)
    # centre console with shifter and armrest
    rbox(D_, 0, 0.5, 3.33, 0.75, 0.38, 2.6, 0.1, 2, c=c)
    tube(BK, [(0, 3.7, 1.4), (0, 4.0, 1.4)], 0.06, 6, c=c)
    sphere(BK, 0, 1.4, 4.04, 0.14, 0.14, 0.14, 8, 5, c=c)
    rbox(CR, 0, -0.55, 3.7, 0.7, 0.16, 1.0, 0.06, 2, c=c)
    # seats (cushion, backrest, headrest, side bolsters) and the rear bench
    for sx in (-1, 1):
        rbox(CR, sx * 1.15, 0.45, 3.33, 1.55, 0.55, 1.5, 0.14, 2, c=c)
        rbox(CR, sx * 1.15, -0.2, 3.6, 1.55, 0.72, 0.4, 0.14, 2, c=c)
        rbox(CR, sx * 1.15, -0.2, 4.05, 0.75, 0.22, 0.32, 0.1, 2, c=c)
        for bx in (-0.7, 0.7):
            rbox(MT('beige') if False else CR, sx * 1.15 + bx, 0.2, 3.5, 0.18, 0.4, 1.0, 0.05, 1, c=c)
    rbox(CR, 0, -2.3, 3.33, 4.5, 0.5, 1.6, 0.14, 2, c=c)
    rbox(CR, 0, -3.15, 3.55, 4.5, 0.72, 0.4, 0.14, 2, c=c)
    for sx in (-1, 1):
        rbox(CR, sx * 1.3, -3.2, 4.0, 0.7, 0.2, 0.3, 0.1, 2, c=c)
    rbox(D_, 0, -4.0, 3.68, 4.2, 0.12, 0.7, 0.05, 1, c=c)                              # parcel shelf
    rbox(MT('metal'), 0, 1.05, 4.0, 0.8, 0.2, 0.1, 0.04, 1, c=c)                       # rear-view mirror


def _mono(xs, ys):
    """monotone cubic (Fritsch-Carlson) through the table: smooth profile curves without overshoot"""
    n = len(xs)
    d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(n - 1)]
    m = [d[0]] + [0.0 if d[i - 1] * d[i] <= 0 else (d[i - 1] + d[i]) / 2 for i in range(1, n - 1)] + [d[-1]]
    for i in range(n - 1):
        if abs(d[i]) < 1e-12:
            m[i] = m[i + 1] = 0.0
            continue
        a, b = m[i] / d[i], m[i + 1] / d[i]
        if a * a + b * b > 9:
            t = 3 / math.sqrt(a * a + b * b)
            m[i], m[i + 1] = t * a * d[i], t * b * d[i]

    def f(x):
        x = min(max(x, xs[0]), xs[-1])
        k = max(0, min(n - 2, next((i for i in range(n - 1) if x <= xs[i + 1]), n - 2)))
        h = xs[k + 1] - xs[k]
        t = (x - xs[k]) / h
        h00, h10, h01, h11 = 2 * t**3 - 3 * t**2 + 1, t**3 - 2 * t**2 + t, -2 * t**3 + 3 * t**2, t**3 - t**2
        return h00 * ys[k] + h10 * h * m[k] + h01 * ys[k + 1] + h11 * h * m[k + 1]
    return f


# profile tables along z (rear -> front)
HB = _mono([-7.6, -7.4, -6.9, -6.0, -2.0, 3.0, 5.2, 6.6, 7.25, 7.45, 7.6], [2.2, 2.65, 2.95, 3.08, 3.14, 3.12, 3.05, 2.9, 2.7, 2.45, 2.15])       # half width of the body
YB = _mono([-7.6, -7.45, -6.8, -6.0, 6.0, 6.9, 7.45, 7.6], [1.2, 0.98, 0.85, 0.9, 0.9, 0.85, 0.98, 1.2])                                              # underside
YD = _mono([-7.6, -7.4, -6.9, -6.0, -5.0, -3.0, 0.0, 3.0, 3.9, 5.2, 6.6, 7.35, 7.6], [2.85, 3.08, 3.28, 3.38, 3.36, 3.32, 3.3, 3.28, 3.25, 3.05, 2.75, 2.45, 2.2])   # belt / deck line
YR = _mono([-7.6, -5.4, -5.0, -4.1, -3.25, -2.0, 0.0, 1.75, 2.75, 3.75, 4.0, 7.6], [2.85, 3.3, 3.42, 4.1, 4.62, 4.75, 4.78, 4.66, 4.2, 3.4, 3.2, 2.2])      # roof line (rear window, roof, windshield)


def yr_at(z):
    return max(YR(z), YD(z))


def _smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def _half_ring(z):
    """right half of the cross-section at z, bottom centre -> top centre (13 points: 6 lower body, 7 upper = belt, sill, glass, roof edge, rail, roof)"""
    hb, yb, yd = HB(z), YB(z), YD(z)
    H = max(0.0, YR(z) - yd)
    w = _smooth(H / 0.5)
    hcb = hb - 0.5
    hct = hcb - 0.5
    low = [(0.0, yb), (hb - 0.6, yb), (hb - 0.05, yb + 0.28), (hb, yb + 0.8), (hb, yd - 0.45), (hb - 0.15, yd - 0.1)]
    cab = [(hcb, yd), (hcb - (hcb - hct) * 0.2, yd + 0.2 * (H - 0.2) + 0.06), (hcb - (hcb - hct) * 0.6, yd + 0.6 * (H - 0.2) + 0.06),
           (hct, yd + max(H - 0.2, 0.0)), (hct - 0.4, yd + max(H - 0.05, 0.0)), (hct * 0.5, yd + H - 0.01), (0.0, yd + H)]
    flat = [(hcb * (1 - j / 6.0), yd + 0.03 * math.sin(math.pi * j / 6.0)) for j in range(7)]
    up = [(w * a[0] + (1 - w) * b[0], w * a[1] + (1 - w) * b[1]) for a, b in zip(cab, flat)]
    return low + up


def _stations():
    zs = set()
    k = -29
    while k <= 29:
        zs.add(round(k * 0.25, 3))
        k += 1
    zs.update([-7.6, -7.5, -7.4, 7.4, 7.5, 7.6])
    return sorted(zs)


# glass ranges (z) on the body shell: side windows and the front / rear screen
SIDE_FRONT, SIDE_REAR = (-0.5, 3.0), (-4.0, -1.0)
SCREEN_FRONT, SCREEN_REAR = (2.0, 3.5), (-4.75, -3.5)


def body_shell(c, body, glass):
    """whole car body as ONE closed shell: lower body, shoulders, cabin with tumblehome, roof, screens.  Windows, skirts and bumper valances are
    colour-coded faces of the same surface (no separate plates, no overhang)."""
    zs = _stations()
    rings = []
    for z in zs:
        r = _half_ring(z)
        pts = [(x, y, z) for (x, y) in r]                              # P0 .. u6 (13)
        pts += [(-x, y, z) for (x, y) in reversed(r[1:-1])]            # mirrored (11) -> 24 points
        rings.append(pts)
    n = len(rings[0])
    verts = [p for r in rings for p in r]
    groups = {}

    def seg_of(i):
        return i if i < 12 else 23 - i
    for k in range(len(rings) - 1):
        zm = (zs[k] + zs[k + 1]) / 2
        for i in range(n):
            j = (i + 1) % n
            sg = seg_of(i)
            col = body
            if sg in (0, 1, 2) or (sg == 3 and abs(zm) > 6.9):
                col = 'dark'
            elif sg in (7, 8) and (SIDE_FRONT[0] <= zm <= SIDE_FRONT[1] or SIDE_REAR[0] <= zm <= SIDE_REAR[1]):
                col = glass
            elif sg in (10, 11) and (SCREEN_FRONT[0] <= zm <= SCREEN_FRONT[1] or SCREEN_REAR[0] <= zm <= SCREEN_REAR[1]):
                col = glass
            groups.setdefault(col, []).append((k * n + i, k * n + j, (k + 1) * n + j, (k + 1) * n + i))
    groups.setdefault('dark', []).append(tuple(reversed(range(n))))                              # rear face
    groups['dark'].append(tuple(range((len(rings) - 1) * n, len(rings) * n)))                    # front face
    for col, faces in groups.items():
        used = sorted({v for f in faces for v in f})
        rm = {v: q for q, v in enumerate(used)}
        emit(c, MT(col), [verts[v] for v in used], [tuple(rm[v] for v in f) for f in faces])


def dad_car(c, body='navy', glass='glass', pass_on_dash=True, sc=1.0, trim=True):
    SC[0] = sc
    B_, D_ = MT(body), MT('dark')
    body_shell(c, body, glass)
    for sx in (-1, 1):
        # headlamps (slim housing + lens), fog lamps, tail lamps
        sphere(D_, sx * 1.95, 7.3, 2.38, 0.72, 0.26, 0.12, 14, 7, c=c)
        sphere(MT('lamp'), sx * 1.95, 7.36, 2.38, 0.5, 0.17, 0.09, 14, 7, c=c)
        sphere(MT('lamp'), sx * 1.95, 7.55, 1.3, 0.3, 0.12, 0.1, 10, 5, c=c)
        sphere(MT('red'), sx * 2.0, -7.32, 2.55, 0.75, 0.22, 0.12, 14, 7, c=c)
        # mirrors and door handles
        rbox(B_, sx * 3.2, 2.5, 3.5, 0.5, 0.38, 0.42, 0.14, 2, c=c)
        tube(D_, [(sx * 2.7, 3.45, 2.7), (sx * 3.0, 3.58, 2.55)], 0.07, 5, c=c)
        rbox(MT('metal'), sx * 3.14, 0.9, 2.95, 0.06, 0.12, 0.8, 0.04, 1, c=c)
        rbox(MT('metal'), sx * 3.14, -2.5, 2.95, 0.06, 0.12, 0.8, 0.04, 1, c=c)
        # wheel arches (dark well + body-colour flare) and wheels
        for z in (WB / 2, -WB / 2):
            for (R, r, col) in ((1.37, 0.07, MT('black')), (1.46, 0.08, B_)):          # arch: dark lip + body-colour flare (upper arc only)
                arc = [(sx * 3.13, 1.25 + R * math.sin(math.radians(a)), z + R * math.cos(math.radians(a))) for a in range(-15, 196, 10)]
                tube(col, arc, r, 6, c=c)
            wheel(c, sx, z)
    # grille, plates
    rbox(D_, 0, 7.5, 1.5, 3.0, 0.55, 0.2, 0.1, 2, c=c)
    rbox(MT('metal'), 0, 7.62, 1.72, 2.8, 0.07, 0.06, 0.02, 1, c=c)
    rbox(MT('metal'), 0, 7.62, 1.95, 2.8, 0.07, 0.06, 0.02, 1, c=c)
    sphere(MT('metal'), 0, 7.66, 1.83, 0.26, 0.26, 0.05, 12, 6, c=c)
    rbox(MT('white'), 0, -7.66, 1.2, 1.9, 0.5, 0.06, 0.02, 1, c=c)
    rbox(MT('blue'), 0, -7.7, 1.3, 1.7, 0.1, 0.04, 0.01, 1, c=c)
    # exhaust and antenna
    tube(MT('metal_dk'), [(1.5, 0.95, -7.3), (1.5, 0.9, -7.9)], 0.18, 8, c=c)
    tube(D_, [(-1.2, 3.4, -5.9), (-1.2, 4.3, -6.1)], 0.04, 5, c=c)
    if trim:
        interior(c)
    if pass_on_dash:
        # work pass (render-only geometry 'PassProxy': Studio builds the SpareKey part from the anchor)
        rbox(MT('white'), -0.7, 2.3, 3.64, 0.95, 0.07, 1.35, 0.03, 1, c='PassProxy')
        rbox(MT('navy'), -0.7, 2.3, 3.98, 0.95, 0.075, 0.3, 0.02, 1, c='PassProxy')
        rbox(MT('skin'), -0.7, 2.3, 4.18, 0.3, 0.08, 0.4, 0.02, 1, c='PassProxy')
        tube(MT('navy'), [(-0.7, 3.6, 2.3), (-0.7, 3.4, 2.6)], 0.03, 5, c='PassProxy')
        K.anchor('work_pass', -0.7 * sc, 3.75 * sc, 2.3 * sc)
    SC[0] = 1.0
