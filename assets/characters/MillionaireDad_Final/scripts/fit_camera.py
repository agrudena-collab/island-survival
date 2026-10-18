"""Fits the source-matched camera (azimuth / elevation / x shift) of the Blender model to the measured 2D landmarks of the package (data in
source/inputs/Measured_2D_Landmarks.json, expressed in the crop frame: crop origin on the sheet = (1110,530)).
Landmarks (crop px): A height 408 (y5..413), B outer shoulder/sleeve span at y=115 (80..385, 305 px), C head/face span at y=90 (170..325, 155 px),
D case visible width at y=293 (23..173, 150 px, no handle), E case visible height at x=178 (y296..401, 105 px, no handle).
The render is orthographic at 63.75 px/stud (the 6.40 convention); for every azimuth/elevation the silhouette is rendered with a transparent film, the
rendered landmark spans are measured on the mask and compared; the case is rendered alone for D and E.
blender -b <package>/source/MillionaireDad_Review.blend --python fit_camera.py -- <package_dir>"""
import bpy, sys, json, math, numpy as np
from mathutils import Vector
PKG = sys.argv[sys.argv.index("--") + 1]
W, H = 422, 425
REF = {"B": 305, "C": 155, "D": 150, "E": 105}
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'FLAT'
sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (1, 1, 1)
sc.render.film_transparent = True
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
sc.view_settings.view_transform = 'Standard'
cd = bpy.data.cameras.new("fit"); cam = bpy.data.objects["fit"] if "fit" in bpy.data.objects else bpy.data.objects.new("fit", cd)
sc.collection.objects.link(cam); sc.camera = cam
cd.type = 'ORTHO'; cd.ortho_scale = 425.0 / 408.0 * 6.40; cd.clip_start, cd.clip_end = 0.1, 200
tgt = Vector((0, 0, 3.15))
case = [o for o in bpy.data.objects if o.name.startswith("Case_Geo")][0]
others = [o for o in bpy.data.objects if o.type == 'MESH' and o is not case]


def render(az, el, case_only=False, path="/tmp/fitm.png"):
    a, e = math.radians(az), math.radians(el)
    cam.location = tgt + Vector((40 * math.sin(a) * math.cos(e), -40 * math.cos(a) * math.cos(e), 40 * math.sin(e)))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    for o in others:
        o.hide_render = case_only
    case.hide_render = False
    sc.render.filepath = "C:/Users/agrud/AppData/Local/Temp/fitm.png"
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load("C:/Users/agrud/AppData/Local/Temp/fitm.png", check_existing=False)
    arr = np.array(im.pixels[:]).reshape(H, W, 4)[::-1]
    bpy.data.images.remove(im)
    return arr[..., 3] > 0.5


def span(mask, row, lo=0, hi=W):
    xs = np.where(mask[row, lo:hi])[0]
    return (int(xs.min()) + lo, int(xs.max()) + lo) if len(xs) else (0, 0)


rows = []
best = None
for az in range(-60, 1, 3):
    for el in (0, 3, 6):
        m = render(az, el)
        c = render(az, el, True)
        ys = np.where(m.any(1))[0]
        b0, b1 = span(m, 115)
        c0, c1 = span(m, 90, 100, 360)
        cx0, cx1 = span(c, 330)             # case body width (rows well below the handle)
        col = np.where(c[:, 178])[0]
        e_h = int(col.max() - col.min()) if len(col) else 0
        # horizontal alignment: the case left edge goes to x=23 (D left endpoint)
        shift = 23 - cx0
        meas = {"B": b1 - b0, "C": c1 - c0, "D": cx1 - cx0, "E": e_h, "A": int(ys.max() - ys.min())}
        err = sum(abs(meas[k] - REF[k]) for k in REF) + abs(meas["A"] - 408)
        rows.append({"az": az, "el": el, "shift_px": shift, "measured": meas, "abs_err_sum": err})
        if best is None or err < best["abs_err_sum"]:
            best = rows[-1]
print("BEST", json.dumps(best))
json.dump({"reference_px": REF, "reference_height_px": 408, "best": best, "table": rows}, open(PKG + "/data/camera_fit.json", "w"), indent=1)
