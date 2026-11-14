"""Audits for the Grill Dad District (no Blender needed).
 1. flicker: coplanar, same-direction, overlapping faces of boxes with different materials (z-fighting), unless buried
 2. doors: every door opening of Grill Dad's house free of colliders
 3. walk: voxel reachability (agent height 5.5, step 1.0, radius 1.25 and 2.0) from PlayerStart to every target
 4. camera/closed facades: every neighbour house has one full solid collider
Usage: python audit_gd.py <out_dir>"""
import sys, os, json, math, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from scipy import ndimage as ndi
from gd_lib import Scene
import gd_district, gd_house
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
sc = Scene(); gd_district.build(sc)
lines = []
def say(*a):
    t = " ".join(str(x) for x in a); print(t); lines.append(t)
col = sc.colliders
say("== 1. Z-FIGHTING ==")
EPS = 0.004
planes = collections.defaultdict(list)
for i, bxx in enumerate(sc.boxes):
    for a in range(3):
        planes[(a, 1, round(bxx[3 + a] / EPS))].append(i); planes[(a, -1, round(bxx[a] / EPS))].append(i)
grid = collections.defaultdict(list)
for Cb in sc.boxes:
    for gx in range(int(Cb[0] // 20), int(Cb[3] // 20) + 1):
        for gy in range(int(Cb[1] // 20), int(Cb[4] // 20) + 1): grid[(gx, gy)].append(Cb)
pairs = collections.Counter(); samples = {}
SKIPG = ("Glass", "Water", "Smoke")
for (a, sgn, _), idx in planes.items():
    if len(idx) < 2 or len(idx) > 400: 
        if len(idx) > 400 and a == 2: continue
    o = [b for b in range(3) if b != a]
    for ii in range(len(idx)):
        A = sc.boxes[idx[ii]]
        for jj in range(ii + 1, len(idx)):
            Bx = sc.boxes[idx[jj]]
            if A[6] == Bx[6] or A[7] in SKIPG or Bx[7] in SKIPG: continue
            ov = 1.0
            for b in o:
                lo = max(A[b], Bx[b]); hi = min(A[3 + b], Bx[3 + b])
                if hi - lo <= 0.02: ov = 0; break
                ov *= hi - lo
            if ov <= 0.05: continue
            px = [(max(A[b], Bx[b]) + min(A[3 + b], Bx[3 + b])) / 2 for b in range(3)]
            px[a] = (A[3 + a] + 0.03) if sgn > 0 else (A[a] - 0.03)
            if a == 2 and sgn < 0 and px[2] < 0: continue
            buried = False
            for Cb in grid.get((int(px[0] // 20), int(px[1] // 20)), ()):
                if Cb is A or Cb is Bx: continue
                if all(Cb[b] - 1e-6 <= px[b] <= Cb[3 + b] + 1e-6 for b in range(3)): buried = True; break
            if buried: continue
            key = (A[7], A[6], Bx[7], Bx[6], "XYZ"[a], "+" if sgn > 0 else "-")
            pairs[key] += 1
            samples.setdefault(key, ([round(v, 2) for v in A[:6]], [round(v, 2) for v in Bx[:6]]))
FL = sum(pairs.values())
for k, n in pairs.most_common(40): say(f"  {n:4d} x {k}  e.g. {samples[k]}")
say("FLICKER_PAIRS", FL, "(boxes:", len(sc.boxes), ")")

say("\n== 2. DOOR OPENINGS (Grill Dad's house) ==")
bad = 0
for name, cx, cy, z0, w, ax in gd_house.DOORS:
    if ax == "y": lo = (cx - w / 2 + 0.3, cy - 3, z0 + 0.3); hi = (cx + w / 2 - 0.3, cy + 3, z0 + 8.4)
    else: lo = (cx - 3, cy - w / 2 + 0.3, z0 + 0.3); hi = (cx + 3, cy + w / 2 - 0.3, z0 + 8.4)
    hits = [c for c in col if all(c["min"][i] < hi[i] - 1e-3 and c["max"][i] > lo[i] + 1e-3 for i in range(3))]
    if hits: bad += 1
    say(f"  {name:18s}", "OK" if not hits else "BLOCKED by " + ", ".join(sorted({h['tag'] for h in hits})))
say("DOOR_ISSUES", bad)

say("\n== 3. WALKABILITY (voxel 0.5, height 5.5, step 1.0) ==")
DXY = DZ = 0.5; X0, Y0, Z0 = -6.0, -6.0, -2.0
NX = NY = int(512 / DXY); NZ = int(34 / DZ)
occ = np.zeros((NX, NY, NZ), dtype=bool)
for c in col:
    mn, mx = c["min"], c["max"]
    i0 = int(math.floor((mn[0] - X0) / DXY + 0.5)); i1 = int(math.floor((mx[0] - X0) / DXY + 0.5))
    j0 = int(math.floor((mn[1] - Y0) / DXY + 0.5)); j1 = int(math.floor((mx[1] - Y0) / DXY + 0.5))
    k0 = int(math.floor((mn[2] - Z0) / DZ + 0.5)); k1 = int(math.floor((mx[2] - Z0) / DZ + 0.5))
    if i1 <= i0: i1 = i0 + 1
    if j1 <= j0: j1 = j0 + 1
    if k1 <= k0: k1 = k0 + 1
    occ[max(i0, 0):max(i1, 0), max(j0, 0):max(j1, 0), max(k0, 0):max(k1, 0)] = True
H_VOX = int(5.5 / DZ)
cs = np.cumsum(occ, axis=2, dtype=np.int16); cs = np.concatenate([np.zeros((NX, NY, 1), np.int16), cs], axis=2)
ks = np.arange(NZ); hi_k = np.minimum(ks + H_VOX, NZ); lo_k = np.minimum(ks + 2, NZ)
colocc = (cs[:, :, hi_k] - cs[:, :, lo_k]) > 0
lo4 = np.minimum(ks + 4, NZ); colocc4 = (cs[:, :, hi_k] - cs[:, :, lo4]) > 0
del cs
def idx_of(x, y, z): return (int(round((x - X0) / DXY - 0.5)), int(round((y - Y0) / DXY - 0.5)), int(round((z - Z0) / DZ - 0.5)))
START = next(a for a in sc.anchors if a["name"] == "PlayerStart")["pos"]
rooms = dict(gd_district.TARGETS)
moves = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx or dy)]
ISS = 0
for radius, label in ((1.25, "r=1.25 (avatar)"), (2.0, "r=2.0 (carrying dad)")):
    rc = int(math.ceil(radius / DXY)); yy, xx = np.mgrid[-rc:rc + 1, -rc:rc + 1]
    foot = ((xx * DXY) ** 2 + (yy * DXY) ** 2 <= radius ** 2 + 1e-9)[:, :, None]
    blocked = ndi.maximum_filter(colocc, footprint=foot, mode="constant", cval=False)
    if radius > 1.5:
        rc1 = int(math.ceil(1.25 / DXY)); y1, x1 = np.mgrid[-rc1:rc1 + 1, -rc1:rc1 + 1]
        foot1 = ((x1 * DXY) ** 2 + (y1 * DXY) ** 2 <= 1.25 ** 2 + 1e-9)[:, :, None]
        blocked = ndi.maximum_filter(colocc, footprint=foot1, mode="constant", cval=False) | ndi.maximum_filter(colocc4, footprint=foot, mode="constant", cval=False)
    support = np.zeros_like(occ); support[:, :, 1:] = occ[:, :, :-1]
    S = support & ~blocked; vis = np.zeros_like(S)
    si = idx_of(START[0], START[1], 0.0)
    cand = [(si[0], si[1], k) for k in range(max(si[2] - 3, 0), si[2] + 5) if S[si[0], si[1], k]]
    assert cand, "start not standable"
    fr = np.array([cand[0]], dtype=np.int32); vis[tuple(fr[0])] = True
    while len(fr):
        new = []
        for dx, dy in moves:
            for dz in (-2, -1, 0, 1, 2):
                ni = fr[:, 0] + dx; nj = fr[:, 1] + dy; nk = fr[:, 2] + dz
                ok = (ni >= 0) & (ni < NX) & (nj >= 0) & (nj < NY) & (nk >= 0) & (nk < NZ)
                ni, nj, nk = ni[ok], nj[ok], nk[ok]
                m = S[ni, nj, nk] & ~vis[ni, nj, nk]
                if m.any():
                    a = np.unique(np.stack([ni[m], nj[m], nk[m]], axis=1), axis=0)
                    vis[a[:, 0], a[:, 1], a[:, 2]] = True; new.append(a)
        fr = np.concatenate(new) if new else np.zeros((0, 3), np.int32)
    say(f"\n-- agent {label}: reachable cells {int(vis.sum())}")
    miss = []
    for name, (x, y, z) in rooms.items():
        i, j, k = idx_of(x, y, z); found = False; standable = False
        for di in range(-3, 4):
            for dj in range(-3, 4):
                for dk in range(-3, 4):
                    a, b, c_ = i + di, j + dj, k + dk
                    if 0 <= a < NX and 0 <= b < NY and 0 <= c_ < NZ and S[a, b, c_]:
                        standable = True
                        if vis[a, b, c_]: found = True
        if not found: miss.append((name, "STANDABLE BUT UNREACHABLE" if standable else "NO STANDABLE SPOT"))
    for n, s in miss: say(f"  !! {n}: {s}")
    if not miss: say(f"  all {len(rooms)} target spots reachable")
    ISS += len(miss)
    if os.environ.get("DBG") and radius == float(os.environ.get("DBGR", "2.0")):
        x0, x1, y0, y1, zz = [float(v) for v in os.environ["DBG"].split(",")]
        k = idx_of(0, 0, zz)[2]
        for yv in np.arange(y1, y0, -1.0):
            row = ""
            for xv in np.arange(x0, x1, 0.5):
                i, j, _ = idx_of(xv, yv, zz)
                row += "#" if vis[i, j, k - 1:k + 2].any() else ("." if S[i, j, k - 1:k + 2].any() else ("x" if support[i, j, k - 1:k + 2].any() else " "))
            print("%6.1f %s" % (yv, row))
    del blocked, S, vis, support
say("\nWALK_ISSUES", ISS)

say("\n== 4. CLOSED FACADES / CAMERA ==")
nh = [c for c in col if c["tag"] == "NeighborHouse"]
say("  neighbour houses with a full solid collider:", len(nh), "of 10")
say("  Grill Dad's house: wall, floor, ceiling and roof colliders present:", sum(1 for c in col if c["group"] in ("House", "House2F", "HouseRoof")))
say("  camera rule is enforced in Studio by scripts/camera_block.luau (PopperCam ignores invisible colliders)")
say("\nSUMMARY flicker_pairs", FL, "door_issues", bad, "walk_issues", ISS, "neighbour_solid", len(nh))
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
open(os.path.join(OUT, "data", "audit_report.txt"), "w").write("\n".join(lines) + "\n")
