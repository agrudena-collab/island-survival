"""Silhouette comparison of the matching-camera render against the unchanged reference crop.
Usage: python compare_reference.py <reference.png> <render.png> <out_dir>
Background = colour of the image corners (threshold on distance); one global similarity align (scale+shift of the bbox, no part stretching).
Auxiliary metric only (IoU target .90 is a project goal, not a pass criterion)."""
import json, os, sys
import numpy as np
import imageio.v2 as iio

ref = iio.imread(sys.argv[1])[:, :, :3].astype(float)
ren = iio.imread(sys.argv[2])[:, :, :3].astype(float)
out = sys.argv[3]
os.makedirs(out, exist_ok=True)


def mask(a, thr=28.0):
    h, w = a.shape[:2]
    bg = np.median(np.concatenate([a[:6, :6].reshape(-1, 3), a[:6, -6:].reshape(-1, 3), a[-6:, :6].reshape(-1, 3), a[-6:, -6:].reshape(-1, 3)]), axis=0)
    return np.linalg.norm(a - bg, axis=2) > thr


def bbox(m):
    ys, xs = np.where(m)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


mr, mn = mask(ref), mask(ren)
# the reference sheet may contain a title strip at the top: ignore rows above the first big gap is NOT done here (crop has none)
br, bn = bbox(mr), bbox(mn)
sx, sy = (br[2] - br[0]) / (bn[2] - bn[0]), (br[3] - br[1]) / (bn[3] - bn[1])
s = (sx + sy) / 2.0   # uniform scale only
H, W = mr.shape
ys, xs = np.mgrid[0:H, 0:W]
cr = ((br[0] + br[2]) / 2, (br[1] + br[3]) / 2)
cn = ((bn[0] + bn[2]) / 2, (bn[1] + bn[3]) / 2)
# map reference pixel -> render pixel
u = ((xs - cr[0]) / s + cn[0]).round().astype(int)
v = ((ys - cr[1]) / s + cn[1]).round().astype(int)
ok = (u >= 0) & (u < mn.shape[1]) & (v >= 0) & (v < mn.shape[0])
mn_al = np.zeros_like(mr)
mn_al[ok] = mn[v[ok], u[ok]]
inter = (mr & mn_al).sum()
union = (mr | mn_al).sum()
res = {"iou_after_global_similarity": round(float(inter / union), 4),
       "scale": round(float(s), 4), "ref_bbox": [int(x) for x in br], "render_bbox": [int(x) for x in bn]}
ov = np.zeros((H, W, 3), np.uint8) + 255
ov[mr & ~mn_al] = (230, 60, 60)      # reference only: red
ov[mn_al & ~mr] = (60, 90, 230)      # render only: blue
ov[mr & mn_al] = (80, 80, 80)
iio.imwrite(os.path.join(out, "silhouette_overlay.png"), ov)
side = np.concatenate([ref.astype(np.uint8), ov, np.clip(np.where(mn_al[..., None], ren[np.clip(v, 0, mn.shape[0] - 1), np.clip(u, 0, mn.shape[1] - 1)], 245), 0, 255).astype(np.uint8)], axis=1)
iio.imwrite(os.path.join(out, "reference_vs_render.png"), side)
json.dump(res, open(os.path.join(out, "reference_fit_result.json"), "w"), indent=1)
print(res)
