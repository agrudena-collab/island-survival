"""Pure-python solid builder for the Grill Dad District (no bpy here).
Coordinates: x east, y north , z up; 1 unit = 1 stud."""
import math, json
from collections import defaultdict

from gd_palette import PALETTE

CELL = 125.0
TRI_LIMIT = 9000

# Groups of densely packed, non-collider decoration that are prone to cosmetic z-fighting.
# Only these get the micro-nudge below; structural / collider geometry is never touched.
_NUDGE_GROUPS = ("Terrain", "Flowers", "Bushes", "Cliffs")
_NUDGE_AMP = 0.015   # studs; sub-visible. Larger values open faint gaps between stacked cliff rocks,
#                      so this stays well under the ~0.05-stud threshold where Roblox actually z-fights.


def _micro_nudge(x0, y0, z0, x1, y1, z1):
    """Deterministic +-_NUDGE_AMP offset from the box's own coords (no RNG, no str hash)."""
    s = int(abs(x0 * 131.07 + y0 * 57.71 + z0 * 19.33 + x1 * 7.13 + y1 * 3.37 + z1 * 2.11) * 1000.0) & 0x7fffffff
    out = []
    for _ in range(3):
        s = (s * 1103515245 + 12345) & 0x7fffffff
        out.append(((s % 1000) / 1000.0 - 0.5) * 2.0 * _NUDGE_AMP)
    return out


class Scene:
    def __init__(self):
        self.items = defaultdict(list)   # (group, mat, cx, cy) -> [(verts, faces)]
        self.colliders = []              # dicts
        self.anchors = []                # dicts
        self.stats = defaultdict(int)
        self.boxes = []                  # every axis-aligned box, for the z-fighting audit
        self._planes = defaultdict(list) # (axis, sign, round(coord/0.01), cell u, cell v) -> [(u0, v0, u1, v1, mat)]

    # ---- low level -------------------------------------------------
    def add(self, group, mat, verts, faces, collide=False, bbox=True, tag=None):
        assert mat in PALETTE, mat
        cx = int(sum(v[0] for v in verts) / len(verts) // CELL)
        cy = int(sum(v[1] for v in verts) / len(verts) // CELL)
        self.items[(group, mat, cx, cy)].append((verts, faces))
        self.stats["solids"] += 1
        if collide and bbox:
            xs = [v[0] for v in verts]; ys = [v[1] for v in verts]; zs = [v[2] for v in verts]
            self.colliders.append({
                "group": group, "tag": tag or group,
                "min": [round(min(xs), 3), round(min(ys), 3), round(min(zs), 3)],
                "max": [round(max(xs), 3), round(max(ys), 3), round(max(zs), 3)],
            })

    def box(self, x0, y0, z0, x1, y1, z1, mat, group="Env", collide=True, tag=None):
        if x1 < x0: x0, x1 = x1, x0
        if y1 < y0: y0, y1 = y1, y0
        if z1 < z0: z0, z1 = z1, z0
        if x1 - x0 < 1e-4 or y1 - y0 < 1e-4 or z1 - z0 < 1e-4:
            return
        # Anti z-fighting: nudge non-collider decoration by a tiny, fully deterministic
        # offset derived from the box's own coordinates (NOT from the random stream, so the
        # layout is unchanged). Two different boxes get different offsets, so coplanar faces
        # of densely packed rocks / grass / flowers / bushes stop sharing a plane.
        nudge = group in _NUDGE_GROUPS and not collide
        if nudge:
            dx, dy, dz = _micro_nudge(x0, y0, z0, x1, y1, z1)
            x0 += dx; x1 += dx; y0 += dy; y1 += dy; z0 += dz; z1 += dz
            # second guard: if a face still lands on an existing face plane (same direction, nearby), pull it in by 0.02
            c = [x0, y0, z0, x1, y1, z1]
            for _ in range(3):
                moved = False
                for a in range(3):
                    for sgn, k in ((-1, a), (1, a + 3)):
                        if self._plane_hit(a, sgn, c[k], c, mat):
                            c[k] += 0.02 * (1 if sgn < 0 else -1); moved = True
                if not moved: break
            x0, y0, z0, x1, y1, z1 = c
            if x1 - x0 < 1e-3 or y1 - y0 < 1e-3 or z1 - z0 < 1e-3:
                return
        self._plane_add(x0, y0, z0, x1, y1, z1, mat)
        self.boxes.append((x0, y0, z0, x1, y1, z1, mat, group, tag or ""))
        v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self.add(group, mat, v, f, collide, True, tag)

    def _cells(self, a, c):
        o = [b for b in range(3) if b != a]
        u0, v0, u1, v1 = c[o[0]], c[o[1]], c[o[0] + 3], c[o[1] + 3]
        for cu in range(int(u0 // 20), int(u1 // 20) + 1):
            for cv in range(int(v0 // 20), int(v1 // 20) + 1):
                yield cu, cv, (u0, v0, u1, v1)

    def _plane_add(self, x0, y0, z0, x1, y1, z1, mat):
        c = [x0, y0, z0, x1, y1, z1]
        for a in range(3):
            for sgn, k in ((-1, a), (1, a + 3)):
                q = round(c[k] / 0.01)
                for cu, cv, r in self._cells(a, c):
                    self._planes[(a, sgn, q, cu, cv)].append(r + (mat,))

    def _plane_hit(self, a, sgn, coord, c, mat):
        q = round(coord / 0.01)
        for cu, cv, (u0, v0, u1, v1) in self._cells(a, c):
            for qq in (q - 1, q, q + 1):
                for (p0, r0, p1, r1, m) in self._planes.get((a, sgn, qq, cu, cv), ()):
                    if m != mat and min(u1, p1) - max(u0, p0) > 0.02 and min(v1, r1) - max(v0, r0) > 0.02:
                        return True
        return False

    def prism(self, pts, z0, z1, mat, group="Env", collide=True, bbox=True, tag=None):
        """Convex polygon (x,y) extruded in z."""
        n = len(pts)
        a = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
        if a < 0: pts = pts[::-1]
        v = [(p[0], p[1], z0) for p in pts] + [(p[0], p[1], z1) for p in pts]
        f = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
        for i in range(n):
            j = (i + 1) % n
            f.append((i, j, n + j, n + i))
        self.add(group, mat, v, f, collide, bbox, tag)

    def cyl(self, cx, cy, z0, z1, r, mat, group="Env", seg=8, collide=False, tag=None):
        pts = [(cx + r * math.cos(2 * math.pi * i / seg), cy + r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
        self.prism(pts, z0, z1, mat, group, collide, True, tag)

    def cone(self, cx, cy, z0, z1, r, mat, group="Env", seg=8, collide=False):
        pts = [(cx + r * math.cos(2 * math.pi * i / seg), cy + r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
        v = [(p[0], p[1], z0) for p in pts] + [(cx, cy, z1)]
        f = [tuple(range(seg - 1, -1, -1))] + [(i, (i + 1) % seg, seg) for i in range(seg)]
        self.add(group, mat, v, f, collide, True)

    def pyramid_roof(self, x0, y0, x1, y1, z0, z1, mat, group="Roof"):
        v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), ((x0 + x1) / 2, (y0 + y1) / 2, z1)]
        f = [(0, 3, 2, 1), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]
        self.add(group, mat, v, f, False)

    def gable_x(self, x0, x1, y0, y1, zb, zr, mat, group="Roof", zt=None):
        """Triangular prism, ridge along x at the middle of y0..y1."""
        ym = (y0 + y1) / 2
        zt = zb if zt is None else zt
        v = [(x0, y0, zb), (x0, y1, zb), (x0, ym, zr), (x1, y0, zb), (x1, y1, zb), (x1, ym, zr)]
        f = [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (0, 3, 5, 2), (1, 2, 5, 4)]
        self.add(group, mat, v, f, False)

    def gable_y(self, x0, x1, y0, y1, zb, zr, mat, group="Roof"):
        xm = (x0 + x1) / 2
        v = [(x0, y0, zb), (x1, y0, zb), (xm, y0, zr), (x0, y1, zb), (x1, y1, zb), (xm, y1, zr)]
        f = [(0, 1, 2)[::-1], (3, 4, 5), (0, 3, 4, 1)[::-1], (0, 2, 5, 3), (1, 4, 5, 2)[::-1]]
        self.add(group, mat, v, f, False)

    def plate(self, p0, p1, p2, p3, th, mat, group="Roof", normal_up=True):
        """Quad plate extruded by th along its normal (for roof patches)."""
        ax, ay, az = [p1[i] - p0[i] for i in range(3)]
        bx, by, bz = [p3[i] - p0[i] for i in range(3)]
        n = (ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx)
        l = math.sqrt(sum(c * c for c in n)) or 1
        n = tuple(c / l * th for c in n)
        if n[2] < 0: n = tuple(-c for c in n)
        top = [tuple(p[i] + n[i] for i in range(3)) for p in (p0, p1, p2, p3)]
        v = [p0, p1, p2, p3] + top
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self.add(group, mat, v, f, False)

    def loft(self, sections, mat, group="Env", caps=True, collide=False):
        """sections: list of rings (list of 3D pts, same count)."""
        n = len(sections[0]); m = len(sections)
        v = [p for s in sections for p in s]
        f = []
        for k in range(m - 1):
            for i in range(n):
                j = (i + 1) % n
                f.append((k * n + i, k * n + j, (k + 1) * n + j, (k + 1) * n + i))
        if caps:
            f.append(tuple(range(n - 1, -1, -1)))
            f.append(tuple((m - 1) * n + i for i in range(n)))
        self.add(group, mat, v, f, collide)

    # ---- helpers ----------------------------------------------------
    def anchor(self, name, pos, **kw):
        d = {"name": name, "pos": [round(c, 3) for c in pos]}
        d.update(kw)
        self.anchors.append(d)

    def ribbon(self, pts, width, z0, z1, mat, group="Env", collide=True, tag=None):
        """Strip along a polyline, built from trapezoid prisms."""
        for a, b in zip(pts[:-1], pts[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            l = math.hypot(dx, dy) or 1
            nx, ny = -dy / l * width / 2, dx / l * width / 2
            quad = [(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)]
            self.prism(quad, z0, z1, mat, group, collide, True, tag)


def tri_count(faces):
    return sum(max(len(f) - 2, 0) for f in faces)



def _col(self, x0, y0, z0, x1, y1, z1, tag, group="Col"):
    self.colliders.append({"group": group, "tag": tag,
        "min": [round(min(x0, x1), 3), round(min(y0, y1), 3), round(min(z0, z1), 3)],
        "max": [round(max(x0, x1), 3), round(max(y0, y1), 3), round(max(z0, z1), 3)]})
Scene.col = _col
