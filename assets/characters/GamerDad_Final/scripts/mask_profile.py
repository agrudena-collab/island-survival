"""Row-by-row horizontal spans (studs) of the model mask and the reference mask (same canvas): where do the silhouettes differ?
blender -b --python mask_profile.py -- <dir> <tag>"""
import os, sys
import bpy, numpy as np
A = sys.argv[sys.argv.index("--") + 1:]
D, TAG = A[0], A[1]
N, ORTHO = 1600, 7.15
PXS = N / ORTHO
import math
el = math.radians(7.0)


def load(p):
    im = bpy.data.images.load(p)
    w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]
    return a[..., 0] > 0.5


mm = load(os.path.join(D, TAG + "_mask_model.png"))
mr = load(os.path.join(D, TAG + "_mask_ref.png"))


def spans(row):
    out, start = [], None
    for x in range(len(row)):
        if row[x] and start is None:
            start = x
        if (not row[x]) and start is not None:
            out.append((start, x - 1))
            start = None
    if start is not None:
        out.append((start, len(row) - 1))
    return out


def xs(v):
    return round((v - N / 2) / PXS, 2)


# H of a pixel row (orthographic, elevation 7): H = 3.2 + (N/2 - y)/PXS / cos(el) (points on the central plane)
for H in (6.3, 6.0, 5.6, 5.2, 4.8, 4.5, 4.3, 4.0, 3.6, 3.2, 2.8, 2.5, 2.3, 2.0, 1.7, 1.4, 1.2, 1.0, 0.8, 0.6, 0.4, 0.2):
    y = int(round(N / 2 - (H - 3.2) * math.cos(el) * PXS))
    print("H=%.1f" % H, "MODEL", [(xs(a), xs(b)) for a, b in spans(mm[y])], "REF", [(xs(a), xs(b)) for a, b in spans(mr[y])])
