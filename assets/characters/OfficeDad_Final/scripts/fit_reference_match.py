"""Silhouette IoU of the built Office Dad against the reference crop (similarity-aligned by bbox), camera search.
Run: blender -b source/OfficeDad_Redesign.blend --python fit_reference_match.py -- <asset_dir>"""
import bpy, os, sys, json, math
import numpy as np
from mathutils import Vector as V
OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
W, H = 327, 370
arm = bpy.data.objects["OfficeDad_Armature"]; arm.animation_data_create(); arm.animation_data.action = bpy.data.actions["OfficeDad_ReferencePose"]; bpy.context.view_layer.update()
sc = bpy.context.scene; sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'; sc.eevee.taa_render_samples = 4
cam = bpy.data.objects["OD_Cam"]; cd = cam.data
def load(path):
    im = bpy.data.images.load(path); a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4); return a[::-1]
ref = load(os.path.join(OUT, "reference", "OfficeDad_Reference_Crop.png"))[:, :, :3] * 255
border = np.concatenate([ref[:5].reshape(-1, 3), ref[:, :5].reshape(-1, 3), ref[:, -5:].reshape(-1, 3)])
bg = np.median(border, axis=0); rm = np.abs(ref - bg).sum(axis=2) > 45
ys, xs = np.where(rm); rb = (xs.min(), ys.min(), xs.max(), ys.max())
tmp = os.path.join(OUT, "_fit.png")
def mask(loc, lens):
    cam.location = V(loc); cam.rotation_euler = (V((0, -.10, 3.18)) - V(loc)).to_track_quat('-Z', 'Y').to_euler(); cd.type = 'PERSP'; cd.lens = lens; cd.sensor_width = 36
    sc.render.resolution_x, sc.render.resolution_y = W, H; sc.render.filepath = tmp; bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(tmp); a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)[::-1]; bpy.data.images.remove(im); return a[:, :, 3] > .5
def iou(m):
    y_, x_ = np.where(m)
    if len(x_) == 0: return 0, None
    b = (x_.min(), y_.min(), x_.max(), y_.max()); s = (rb[3] - rb[1] + 1) / float(b[3] - b[1] + 1)
    yy, xx = np.mgrid[0:H, 0:W]
    sx = (xx - (rb[0] + rb[2]) / 2) / s + (b[0] + b[2]) / 2; sy = (yy - rb[1]) / s + b[1]
    ix = np.clip(np.round(sx).astype(int), 0, m.shape[1] - 1); iy = np.clip(np.round(sy).astype(int), 0, m.shape[0] - 1)
    w = m[iy, ix]; return (w & rm).sum() / float((w | rm).sum()), w
base = (-7.0, -15.0, 7.0)
i0, _ = iou(mask(base, 70)); print("PRESCRIBED_CAMERA_IOU", round(float(i0), 4))
best = (i0, base, 70)
r = math.hypot(base[0], base[1]); az0 = math.atan2(base[0], -base[1])
for da in (-8, -4, 0, 4, 8):
    for el in (4, 7, 10, 13):
        for lens in (55, 70, 90):
            az = az0 + math.radians(da); d = 18.0 * lens / 70.0
            loc = (d * math.cos(math.radians(el)) * math.sin(az), -d * math.cos(math.radians(el)) * math.cos(az) + 0, 3.18 + d * math.sin(math.radians(el)))
            v, _ = iou(mask(loc, lens))
            if v > best[0]: best = (v, loc, lens)
v, w = iou(mask(best[1], best[2]))
res = {"prescribed_camera": {"loc": base, "lens": 70, "iou": round(float(i0), 4)}, "best_camera": {"loc": [round(c, 3) for c in best[1]], "lens": best[2], "iou": round(float(v), 4)},
       "method": "ref mask = |RGB - median border| > 45; render alpha > .5; similarity alignment on bbox height + centre x", "ref_bbox": [int(c) for c in rb]}
json.dump(res, open(os.path.join(OUT, "data", "reference_fit_result.json"), "w"), indent=1)
ov = np.zeros((H, W, 4), dtype=np.float32); ov[..., 3] = 1; ov[..., 0] = rm; ov[..., 2] = w; ov[..., 1] = rm & w
im = bpy.data.images.new("ov", W, H, alpha=True); im.pixels.foreach_set(ov[::-1].ravel()); im.filepath_raw = os.path.join(OUT, "renders", "18_silhouette_overlay.png"); im.file_format = 'PNG'; im.save()
os.remove(tmp); print("FIT", json.dumps(res))
