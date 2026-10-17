"""Silhouette + landmark comparison of the built model with the approved reference (middle figure = front view), real renders only.
blender -b <build>/source/GamerDad_Sweatshirt_Review.blend --python compare_reference.py -- <reference.png> <out_dir> <tag>
Writes <out_dir>/<tag>_mask_model.png, _mask_ref.png, _overlay.png, _landmarks.png and <tag>_reference_fit.json.
Alignment (stated, not fitted to hide errors): scale = model mask height / reference mask height, the soles' bottom row and the logo X are matched.
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

V = Vector
A = sys.argv[sys.argv.index("--") + 1:]
REF, OUT, TAG = A[0], os.path.abspath(A[1]), A[2]
os.makedirs(OUT, exist_ok=True)
SC = bpy.context.scene
N = 1600
ORTHO = 7.15
TARGET = V((0.0, -0.10, 3.20))
ELEV = 7.0
PXS = N / ORTHO                       # model px per stud


def img_to_np(img):
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    return a[::-1]                    # row 0 = top


def np_to_img(name, arr, path):
    h, w = arr.shape[:2]
    im = bpy.data.images.new(name, w, h, alpha=True)
    out = np.ones((h, w, 4), dtype=np.float32)
    out[..., :arr.shape[2]] = arr
    im.pixels.foreach_set(out[::-1].reshape(-1))
    im.filepath_raw = path
    im.file_format = 'PNG'
    im.save()


# ---- reference mask (middle figure)
ref = bpy.data.images.load(REF)
ra = img_to_np(ref)
H0, W0 = ra.shape[:2]
x0, x1 = 590, 1170
crop = ra[:, x0:x1, :3]
bg = np.median(np.concatenate([crop[:12, :12].reshape(-1, 3), crop[:12, -12:].reshape(-1, 3), crop[-12:, :12].reshape(-1, 3)]), axis=0)
dist = np.sqrt(((crop - bg) ** 2).sum(axis=2))
mask_ref = dist > 0.115
# drop the soft floor shadow: keep pixels whose colour is not a shadow of the background (darker, desaturated and close to bg hue)
lum = crop.mean(axis=2)
sat = crop.max(axis=2) - crop.min(axis=2)
shadow = (dist < 0.30) & (sat < 0.16) & (lum > 0.55)
mask_ref &= ~shadow
# largest connected component + fill holes (simple flood fill on numpy)
from collections import deque


def largest_component(m):
    h, w = m.shape
    lab = np.zeros((h, w), dtype=np.int32)
    best, best_n, cur = 0, 0, 0
    for y in range(h):
        for x in range(w):
            if m[y, x] and lab[y, x] == 0:
                cur += 1
                q = deque([(y, x)])
                lab[y, x] = cur
                n = 0
                while q:
                    cy, cx = q.popleft()
                    n += 1
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and m[ny, nx] and lab[ny, nx] == 0:
                            lab[ny, nx] = cur
                            q.append((ny, nx))
                if n > best_n:
                    best, best_n = cur, n
    return lab == best


def fill_holes(m):
    h, w = m.shape
    outside = np.zeros_like(m)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if not m[y, x]:
                outside[y, x] = True
                q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if not m[y, x] and not outside[y, x]:
                outside[y, x] = True
                q.append((y, x))
    while q:
        cy, cx = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w and not m[ny, nx] and not outside[ny, nx]:
                outside[ny, nx] = True
                q.append((ny, nx))
    return ~outside


mask_ref = fill_holes(largest_component(mask_ref))
ys, xs = np.where(mask_ref)
ref_top, ref_bot = ys.min(), ys.max()
ref_h = ref_bot - ref_top + 1

# ---- model mask: flat white silhouette on black, same camera as the matching render
for ob in bpy.data.objects:
    if ob.type == 'MESH':
        ob.hide_render = False
SC.render.engine = 'BLENDER_WORKBENCH'
SC.display.shading.light = 'FLAT'
SC.display.shading.color_type = 'SINGLE'
SC.display.shading.single_color = (1, 1, 1)
SC.display.render_aa = 'OFF'
SC.view_settings.view_transform = 'Standard'
SC.render.film_transparent = False
w = bpy.data.worlds.new("m")
w.color = (0, 0, 0)
SC.world = w
cam_d = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cam_d)
SC.collection.objects.link(cam)
SC.camera = cam
el = math.radians(ELEV)
cam.location = TARGET + V((0, -30 * math.cos(el), 30 * math.sin(el)))
cam.rotation_euler = (TARGET - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam_d.type, cam_d.ortho_scale = 'ORTHO', ORTHO
SC.render.resolution_x = SC.render.resolution_y = N
p = os.path.join(OUT, TAG + "_mask_model.png")
SC.render.filepath = p
bpy.ops.render.render(write_still=True)
mi = bpy.data.images.load(p)
mm = img_to_np(mi)[..., 0] > 0.5
ys, xs = np.where(mm)
mod_top, mod_bot = ys.min(), ys.max()
mod_h = mod_bot - mod_top + 1
s = mod_h / ref_h


# ---- projection of 3D points to the model render, affine reference -> model
def proj(pt):
    d = V(pt) - TARGET
    right = V((1, 0, 0))
    up = V((0, math.sin(el), math.cos(el)))
    return N / 2 + d.dot(right) * PXS, N / 2 - d.dot(up) * PXS


# reference mask resampled into model pixel space: model_px = ((ref_px - ref_origin) * s) + offset
logo_ref_x = 877 - x0
logo_mod_x, _ = proj((0, -0.9, 3.76))


def ref_to_model(xr, yr):
    """xr in cropped-reference px (x0 removed), yr in image px."""
    return (xr - logo_ref_x) * s + logo_mod_x, (yr - ref_bot) * s + mod_bot


canvas = np.zeros((N, N), dtype=bool)
yy, xx = np.mgrid[0:N, 0:N]
rx = (xx - logo_mod_x) / s + logo_ref_x
ry = (yy - mod_bot) / s + ref_bot
ok = (rx >= 0) & (rx < mask_ref.shape[1] - 1) & (ry >= 0) & (ry < H0 - 1)
canvas[ok] = mask_ref[ry[ok].astype(int), rx[ok].astype(int)]
inter = (canvas & mm).sum()
union = (canvas | mm).sum()
iou = float(inter / union)
ov = np.zeros((N, N, 3), dtype=np.float32)
ov[canvas & mm] = (0.85, 0.85, 0.85)
ov[canvas & ~mm] = (0.9, 0.2, 0.2)       # reference only
ov[~canvas & mm] = (0.2, 0.4, 0.95)      # model only
np_to_img(TAG + "_overlay", ov, os.path.join(OUT, TAG + "_overlay.png"))
np_to_img(TAG + "_maskref", np.stack([canvas] * 3, axis=2).astype(np.float32), os.path.join(OUT, TAG + "_mask_ref.png"))

# ---- landmarks: reference px (full image) vs model 3D points
spec = json.load(open(os.path.join(os.path.dirname(os.path.abspath(REF)), "GamerDad_Sweatshirt_Construction_Spec.json")))
LM3D = {"hair_top": (0, 0.05, 6.35), "headset_left": (-1.30, -0.04, 5.44), "headset_right": (1.30, -0.04, 5.44), "beard_bottom": (0, -1.0, 4.35), "brow_inner_R": (-0.10, -0.755, 5.56),
        "brow_inner_L": (0.10, -0.755, 5.56), "nose_tip": (0, -1.13, 5.13), "sweat_left_hem": (-1.51, -0.1, 2.42), "sweat_right_hem": (1.51, -0.1, 2.42), "logo_center": (0, -0.9, 3.76),
        "shorts_hem_R": (-1.0, -0.58, 1.19), "shorts_hem_L": (1.0, -0.58, 1.19), "shoe_sole_R": (-1.1375, -0.275, 0.0), "shoe_sole_L": (1.1375, -0.275, 0.0),
        "can_top": (-1.62, -1.32, 4.58), "can_bottom": (-1.62, -1.32, 3.14), "free_hand_bottom": (1.98, -0.08, 2.0315)}
rows = []
for name, xr, yr in spec["reference_landmarks"]["front_panel_only"]:
    mx, my = ref_to_model(xr - 590 + 0, yr)
    px, py = proj(LM3D[name])
    err = math.hypot(px - mx, py - my)
    rows.append({"landmark": name, "reference_px": [xr, yr], "reference_in_model_px": [round(mx, 1), round(my, 1)], "model_px": [round(px, 1), round(py, 1)], "error_px": round(err, 1),
                 "error_over_height": round(err / mod_h, 4), "model_point_XDH": LM3D[name]})
errs = [r["error_over_height"] for r in rows]
res = {"tag": TAG, "silhouette_iou": round(iou, 4), "model_mask_height_px": int(mod_h), "reference_mask_height_px": int(ref_h), "scale_ref_to_model": round(s, 4),
       "landmark_median_over_height": round(float(np.median(errs)), 4), "landmark_max_over_height": round(float(np.max(errs)), 4), "landmarks": rows,
       "alignment": "scale = model mask height / reference mask height; soles bottom row and logo X matched; ortho camera yaw 0, elevation 7, target (0,-0.1,3.2), ortho_scale 7.15, 1600x1600",
       "targets": {"iou": 0.90, "landmark_median": 0.008, "landmark_max": 0.02, "note": "targets are assigned, not achieved results"}}
json.dump(res, open(os.path.join(OUT, TAG + "_reference_fit.json"), "w"), indent=1)
print("FIT", json.dumps({k: res[k] for k in ("silhouette_iou", "landmark_median_over_height", "landmark_max_over_height", "scale_ref_to_model")}))
for r in rows:
    print("LM", r["landmark"], r["error_px"], r["error_over_height"])
