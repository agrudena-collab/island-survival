"""Side-by-side sheet: approved reference (middle figure) | first Blender build | corrected build, all scaled to the same figure height.
blender -b --python make_compare_sheet.py -- <ref_crop.png> <first_front.png> <final_front.png> <out.png>"""
import sys

import bpy
import numpy as np

A = sys.argv[sys.argv.index("--") + 1:]
H = 900


def load(p, crop_h=None):
    im = bpy.data.images.load(p)
    w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1][..., :3]
    return a


def resize(a, h):
    w = int(round(a.shape[1] * h / a.shape[0]))
    ys = (np.arange(h) * a.shape[0] / h).astype(int)
    xs = (np.arange(w) * a.shape[1] / w).astype(int)
    return a[ys][:, xs]


def crop_fig(a, pad=40):
    bg = a[:8, :8].reshape(-1, 3).mean(axis=0)
    m = np.abs(a - bg).sum(axis=2) > 0.12
    ys, xs = np.where(m)
    y0, y1, x0, x1 = max(ys.min() - pad, 0), min(ys.max() + pad, a.shape[0]), max(xs.min() - pad, 0), min(xs.max() + pad, a.shape[1])
    return a[y0:y1, x0:x1]


ref = load(A[0])
first = crop_fig(load(A[1]))
final = crop_fig(load(A[2]))
panels = [resize(p, H) for p in (ref, first, final)]
sep = np.ones((H, 12, 3), dtype=np.float32) * 0.2
sheet = np.concatenate([panels[0], sep, panels[1], sep, panels[2]], axis=1)
im = bpy.data.images.new("sheet", sheet.shape[1], sheet.shape[0], alpha=False)
out = np.ones((sheet.shape[0], sheet.shape[1], 4), dtype=np.float32)
out[..., :3] = sheet
im.pixels.foreach_set(out[::-1].reshape(-1))
im.filepath_raw = A[3]
im.file_format = 'PNG'
im.save()
print("SHEET", sheet.shape)
