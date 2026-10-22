HQ_LIB = '''
# ====================================================================================================
# HQ modelling library: real (non-block) geometry. Coordinates are plot space (x east, h up, z south);
# models are built in a local frame (lx right, h up, lz forward) and placed with tf_push / tf_pop.
# ====================================================================================================
import random as _random

_TF = []


def tf_push(x, z, y0=0.0, rot=0.0):
    a = math.radians(rot)
    _TF.append((x, z, y0, math.cos(a), math.sin(a)))


def tf_pop():
    _TF.pop()


def _t(lx, h, lz):
    if not _TF:
        return (lx, h, lz)
    x, z, y0, c, s = _TF[-1]
    return (x + lx * c - lz * s, h + y0, z + lx * s + lz * c)


def emit(c, m, verts, faces, two_sided=False):
    key = (c, m)
    vs, fs = acc.setdefault(key, ([], []))
    base = len(vs)
    for (lx, h, lz) in verts:
        px, ph, pz = _t(lx, h, lz)
        vs.append((px, -pz, ph))
    for f in faces:
        fs.append(tuple(base + i for i in f))
        if two_sided:
            fs.append(tuple(base + i for i in reversed(f)))


def _bm_out(bm):
    bm.verts.index_update()
    verts = [tuple(v.co) for v in bm.verts]
    faces = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    return verts, faces


def rbox(c, m, cx, cz, y0, sx, sy, sz, r=0.1, seg=3):
    """rounded box centred on (cx, cz), base at y0 (local)."""
    r = max(0.001, min(r, 0.46 * min(sx, sy, sz)))
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = cx + v.co.x * sx
        v.co.y = y0 + sy / 2 + v.co.y * sy
        v.co.z = cz + v.co.z * sz
    bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts), offset=r, offset_type='OFFSET', segments=seg, profile=0.5, affect='EDGES')
    v, f = _bm_out(bm)
    emit(c, m, v, f)


def lathe(c, m, prof, cx, cz, y0=0.0, seg=24, sx=1.0, sz=1.0, caps=True):
    """revolve profile [(radius, height), ...] about the vertical axis through (cx, cz)."""
    verts = []
    rings = []
    for (r, h) in prof:
        if r < 1e-6:
            verts.append((cx, y0 + h, cz))
            rings.append([len(verts) - 1])
        else:
            idx = []
            for i in range(seg):
                a = 2 * math.pi * i / seg
                verts.append((cx + r * sx * math.cos(a), y0 + h, cz + r * sz * math.sin(a)))
                idx.append(len(verts) - 1)
            rings.append(idx)
    faces = []
    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for i in range(seg):
                faces.append((a[0], b[(i + 1) % seg], b[i]))
        elif len(b) == 1:
            for i in range(seg):
                faces.append((a[i], a[(i + 1) % seg], b[0]))
        else:
            for i in range(seg):
                faces.append((a[i], a[(i + 1) % seg], b[(i + 1) % seg], b[i]))
    if caps:
        for ring, up in ((rings[0], False), (rings[-1], True)):
            if len(ring) > 1:
                faces.append(tuple(ring) if up else tuple(reversed(ring)))
    emit(c, m, verts, faces)


def cylinder(c, m, cx, cz, y0, h, r, seg=20, r2=None):
    lathe(c, m, [(r, 0.0), (r if r2 is None else r2, h)], cx, cz, y0, seg)


def sphere(c, m, cx, cz, cy, rx, ry=None, rz=None, seg=18, rings=10):
    ry = ry or rx
    rz = rz or rx
    prof = []
    for k in range(rings + 1):
        a = math.pi * k / rings
        prof.append((math.sin(a), cy - ry * math.cos(a)))
    lathe(c, m, prof, cx, cz, 0.0, seg, sx=rx, sz=rz, caps=False)


def tube(c, m, pts, r, seg=8, closed=False, caps=True, r_end=None):
    n = len(pts)
    P_ = [Vector(p) for p in pts]
    up = Vector((0, 1, 0))
    rings = []
    verts = []
    for i in range(n):
        if closed:
            t = (P_[(i + 1) % n] - P_[(i - 1) % n]).normalized()
        else:
            t = (P_[min(i + 1, n - 1)] - P_[max(i - 1, 0)]).normalized()
        nn = t.cross(up)
        if nn.length < 1e-4:
            nn = t.cross(Vector((1, 0, 0)))
        nn.normalize()
        bb = t.cross(nn).normalized()
        rr = r if r_end is None else r + (r_end - r) * i / max(1, n - 1)
        idx = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            p = P_[i] + (nn * math.cos(a) + bb * math.sin(a)) * rr
            verts.append((p.x, p.y, p.z))
            idx.append(len(verts) - 1)
        rings.append(idx)
    faces = []
    last = n if closed else n - 1
    for i in range(last):
        a, b = rings[i], rings[(i + 1) % n]
        for k in range(seg):
            faces.append((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    if caps and not closed:
        faces.append(tuple(reversed(rings[0])))
        faces.append(tuple(rings[-1]))
    emit(c, m, verts, faces)


def torus(c, m, cx, cz, cy, R, r, plane='xz', seg=28, tseg=8):
    pts = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        if plane == 'xz':
            pts.append((cx + R * math.cos(a), cy, cz + R * math.sin(a)))
        elif plane == 'xy':
            pts.append((cx + R * math.cos(a), cy + R * math.sin(a), cz))
        else:
            pts.append((cx, cy + R * math.sin(a), cz + R * math.cos(a)))
    tube(c, m, pts, r, tseg, closed=True)


def leaf(c, m, bx, bh, bz, ang, length, width, lift=0.6, droop=0.9, n=6):
    """curved pointed leaf card (double sided) growing from (bx, bh, bz) toward angle ang (radians, plan view)"""
    dx, dz = math.cos(ang), math.sin(ang)
    verts = []
    for i in range(n + 1):
        u = i / n
        w = width * math.sin(math.pi * (u ** 0.75)) * 0.5
        cxp = bx + dx * length * u
        czp = bz + dz * length * u
        ch = bh + length * (lift * u - droop * u * u * 0.7)
        for sgn in (-1, 1):
            verts.append((cxp - dz * w * sgn, ch, czp + dx * w * sgn))
    faces = []
    for i in range(n):
        a = 2 * i
        faces.append((a, a + 1, a + 3, a + 2))
    emit(c, m, verts, faces, two_sided=True)


def sheet(c, m, x0, x1, y0, y1, z, folds=6, amp=0.18, nx=40, axis='x'):
    """hanging curtain panel with sine folds; axis 'x': panel spans x, z is depth; 'z': spans z, x is depth"""
    verts = []
    for i in range(nx + 1):
        u = i / nx
        for j in (0, 1):
            h = y0 + (y1 - y0) * j
            off = amp * math.sin(2 * math.pi * folds * u) * (1 - 0.35 * j)
            if axis == 'x':
                verts.append((x0 + (x1 - x0) * u, h, z + off))
            else:
                verts.append((z + off, h, x0 + (x1 - x0) * u))
    faces = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(nx)]
    emit(c, m, verts, faces, two_sided=True)


def book(c, m, cx, cz, y0, w, h, d, r=0.04):
    rbox(c, m, cx, cz, y0, w, h, d, r=r, seg=2)


def ring_pts(cx, cy, cz, R, n, plane='xz', a0=0.0):
    out = []
    for i in range(n):
        a = a0 + 2 * math.pi * i / n
        out.append((cx + R * math.cos(a), cy, cz + R * math.sin(a)) if plane == 'xz' else (cx + R * math.cos(a), cy + R * math.sin(a), cz))
    return out


# ---------------------------------------------------------------- finishing: smooth shading with sharp edges by angle
def finish_mesh(me, angle_deg=38.0):
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    lim = math.radians(angle_deg)
    for e in bm.edges:
        if len(e.link_faces) == 2:
            e.smooth = e.calc_face_angle(0.0) < lim
        else:
            e.smooth = False
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
'''
