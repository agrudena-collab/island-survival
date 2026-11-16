"""Audits for MistressFlat4 (no Blender needed): z-fighting, door openings, walkability (r=1.25 and r=2.0 carrying the dad)
from Arrival to every room / both seats, contract anchors, invisible blockers. Usage: python audit_flat.py <out_dir>"""
import sys, os, math, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from scipy import ndimage as ndi
from gd_lib import Scene
import gm_flat
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
sc = Scene(); gm_flat.build(sc)
lines = []
def say(*a):
    t = " ".join(str(x) for x in a); print(t); lines.append(t)
col = sc.colliders
boxes = [b for b in sc.boxes if b[7] != "View"]

say("== 1. Z-FIGHTING (interior, window view excluded) ==")
EPS = 0.004
planes = collections.defaultdict(list)
for i, b in enumerate(boxes):
    for a in range(3):
        planes[(a, 1, round(b[3 + a] / EPS))].append(i); planes[(a, -1, round(b[a] / EPS))].append(i)
grid = collections.defaultdict(list)
for Cb in boxes:
    for gx in range(int(Cb[0] // 10), int(Cb[3] // 10) + 1):
        for gy in range(int(Cb[1] // 10), int(Cb[4] // 10) + 1): grid[(gx, gy)].append(Cb)
pairs = collections.Counter(); samples = {}
for (a, sgn, _), idx in planes.items():
    if len(idx) < 2: continue
    o = [b for b in range(3) if b != a]
    for ii in range(len(idx)):
        A = boxes[idx[ii]]
        for jj in range(ii + 1, len(idx)):
            Bx = boxes[idx[jj]]
            if A[6] == Bx[6] or A[7] in ("Glass", "Water") or Bx[7] in ("Glass", "Water"): continue
            ov = 1.0
            for b in o:
                lo = max(A[b], Bx[b]); hi = min(A[3 + b], Bx[3 + b])
                if hi - lo <= 0.02: ov = 0; break
                ov *= hi - lo
            if ov <= 0.02: continue
            px = [(max(A[b], Bx[b]) + min(A[3 + b], Bx[3 + b])) / 2 for b in range(3)]
            px[a] = (A[3 + a] + 0.03) if sgn > 0 else (A[a] - 0.03)
            buried = False
            for Cb in grid.get((int(px[0] // 10), int(px[1] // 10)), ()):
                if Cb is A or Cb is Bx: continue
                if all(Cb[b] - 1e-6 <= px[b] <= Cb[3 + b] + 1e-6 for b in range(3)): buried = True; break
            if buried: continue
            key = (A[7], A[6], Bx[7], Bx[6], "XYZ"[a], "+" if sgn > 0 else "-")
            pairs[key] += 1; samples.setdefault(key, ([round(v, 2) for v in A[:6]], [round(v, 2) for v in Bx[:6]]))
FL = sum(pairs.values())
for k, n in pairs.most_common(40): say(f"  {n:4d} x {k}  e.g. {samples[k]}")
say("FLICKER_PAIRS", FL, "(boxes:", len(boxes), ")")

say("\n== 2. DOOR OPENINGS ==")
bad = 0
for name, cx, cy, w, ax in gm_flat.DOORS:
    if name == "exit door":
        lo = (cx - w / 2 + 0.3, cy + 0.7, 0.4); hi = (cx + w / 2 - 0.3, cy + 3.0, 8.4)   # the leaf is decor; the space in front must be free
    elif ax == "x": lo = (cx - w / 2 + 0.3, cy - 2.5, 0.4); hi = (cx + w / 2 - 0.3, cy + 2.5, 8.4)
    else: lo = (cx - 2.5, cy - w / 2 + 0.3, 0.4); hi = (cx + 2.5, cy + w / 2 - 0.3, 8.4)
    hits = [c for c in col if all(c["min"][i] < hi[i] - 1e-3 and c["max"][i] > lo[i] + 1e-3 for i in range(3))]
    if hits: bad += 1
    say(f"  {name:16s}", "OK" if not hits else "BLOCKED by " + ", ".join(sorted({h['tag'] for h in hits})))
say("DOOR_ISSUES", bad)

say("\n== 3. WALKABILITY (voxel 0.5, height 5.5, step 1.0) ==")
DXY = DZ = 0.5; X0, Y0, Z0 = -2.0, -2.0, -2.0
NX = int(88 / DXY); NY = int(60 / DXY); NZ = int(17 / DZ)
occ = np.zeros((NX, NY, NZ), dtype=bool)
for c in col:
    mn, mx = c["min"], c["max"]
    i0 = int(math.floor((mn[0] - X0) / DXY + 0.5)); i1 = int(math.floor((mx[0] - X0) / DXY + 0.5))
    j0 = int(math.floor((mn[1] - Y0) / DXY + 0.5)); j1 = int(math.floor((mx[1] - Y0) / DXY + 0.5))
    k0 = int(math.floor((mn[2] - Z0) / DZ + 0.5)); k1 = int(math.floor((mx[2] - Z0) / DZ + 0.5))
    i1 = max(i1, i0 + 1); j1 = max(j1, j0 + 1); k1 = max(k1, k0 + 1)
    occ[max(i0, 0):max(i1, 0), max(j0, 0):max(j1, 0), max(k0, 0):max(k1, 0)] = True
H_VOX = int(5.5 / DZ)
cs = np.cumsum(occ, axis=2, dtype=np.int16); cs = np.concatenate([np.zeros((NX, NY, 1), np.int16), cs], axis=2)
ks = np.arange(NZ); hi_k = np.minimum(ks + H_VOX, NZ); lo_k = np.minimum(ks + 2, NZ)
colocc = (cs[:, :, hi_k] - cs[:, :, lo_k]) > 0
def idx_of(x, y, z): return (int(round((x - X0) / DXY - 0.5)), int(round((y - Y0) / DXY - 0.5)), int(round((z - Z0) / DZ - 0.5)))
ax_, ay_, az_ = gm_flat.ANCH["arrival"]["pos"]
targets = dict(gm_flat.TARGETS)
moves = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx or dy)]
ISS = 0
for radius, label in ((1.25, "r=1.25 (avatar)"), (2.0, "r=2.0 (carrying dad)")):
    rc = int(math.ceil(radius / DXY)); yy, xx = np.mgrid[-rc:rc + 1, -rc:rc + 1]
    foot = ((xx * DXY) ** 2 + (yy * DXY) ** 2 <= radius ** 2 + 1e-9)[:, :, None]
    blocked = ndi.maximum_filter(colocc, footprint=foot, mode="constant", cval=True)
    support = np.zeros_like(occ); support[:, :, 1:] = occ[:, :, :-1]
    Sg = support & ~blocked; vis = np.zeros_like(Sg)
    si = idx_of(ax_, ay_, az_)
    cand = [(si[0], si[1], k) for k in range(max(si[2] - 3, 0), si[2] + 5) if Sg[si[0], si[1], k]]
    assert cand, "arrival not standable"
    fr = np.array([cand[0]], dtype=np.int32); vis[tuple(fr[0])] = True
    while len(fr):
        new = []
        for dx, dy in moves:
            for dz in (-2, -1, 0, 1, 2):
                ni = fr[:, 0] + dx; nj = fr[:, 1] + dy; nk = fr[:, 2] + dz
                ok = (ni >= 0) & (ni < NX) & (nj >= 0) & (nj < NY) & (nk >= 0) & (nk < NZ)
                ni, nj, nk = ni[ok], nj[ok], nk[ok]
                m = Sg[ni, nj, nk] & ~vis[ni, nj, nk]
                if m.any():
                    a = np.unique(np.stack([ni[m], nj[m], nk[m]], axis=1), axis=0)
                    vis[a[:, 0], a[:, 1], a[:, 2]] = True; new.append(a)
        fr = np.concatenate(new) if new else np.zeros((0, 3), np.int32)
    say(f"-- agent {label}: reachable cells {int(vis.sum())}")
    miss = []
    for name, (x, y, z) in targets.items():
        i, j, k = idx_of(x, y, z); found = standable = False
        for di in range(-3, 4):
            for dj in range(-3, 4):
                for dk in range(-3, 4):
                    a, b, c_ = i + di, j + dj, k + dk
                    if 0 <= a < NX and 0 <= b < NY and 0 <= c_ < NZ and Sg[a, b, c_]:
                        standable = True
                        if vis[a, b, c_]: found = True
        if not found: miss.append((name, "STANDABLE BUT UNREACHABLE" if standable else "NO STANDABLE SPOT"))
    for n, s in miss: say(f"  !! {n}: {s}")
    if not miss: say(f"  all {len(targets)} target spots reachable")
    # nothing reachable outside the flat
    out = vis.copy(); i0, j0, _ = idx_of(0.5, 0.5, 0); i1, j1, _ = idx_of(83.5, 55.5, 0)
    out[i0:i1 + 1, j0:j1 + 1, :] = False
    if out.any(): say("  !! reachable cells OUTSIDE the walls:", int(out.sum())); miss.append(("outside", "leak"))
    ISS += len(miss)
say("WALK_ISSUES", ISS)

say("\n== 4. CONTRACT ==")
need = ("arrival", "exit_door", "table_top", "mistress_seat", "guest_seat")
missing = [k for k in need if k not in gm_flat.ANCH]
say("  anchors:", ", ".join(sorted(gm_flat.ANCH)), "| missing:", missing or "none")
tx, ty, tz = gm_flat.ANCH["table_top"]["pos"]
say(f"  table top at ({tx},{ty}) z={tz}; seats {gm_flat.ANCH['mistress_seat']['pos']} / {gm_flat.ANCH['guest_seat']['pos']}")
def touches(c, b):
    return all(min(c["max"][i], b[3 + i]) - max(c["min"][i], b[i]) > 0.01 for i in range(3))
solids = []
for (g, m, _, _), lst in sc.items.items():
    if g == "View": continue
    for verts, _f in lst:
        xs = [v[0] for v in verts]; ys = [v[1] for v in verts]; zs = [v[2] for v in verts]
        solids.append((min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)))
inv = [c for c in col if not any(touches(c, b) for b in solids)]
say("  invisible colliders (no visible geometry inside them):", len(inv), [c["tag"] for c in inv][:10])
say("\nSUMMARY flicker_pairs", FL, "door_issues", bad, "walk_issues", ISS, "contract_missing", len(missing), "invisible", len(inv))
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
open(os.path.join(OUT, "data", "audit_report.txt"), "w").write("\n".join(lines) + "\n")
