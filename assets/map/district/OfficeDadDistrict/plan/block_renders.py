"""Stage-1 rough block render of the district massing (boxes only, no detail).
Run: blender -b --factory-startup --python block_renders.py -- <out dir>"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan_data as P

OUT = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
MATS = {}


def mat(hexcol):
    if hexcol in MATS:
        return MATS[hexcol]
    h = hexcol.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lin = lambda c: ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
    m = bpy.data.materials.new('m' + h)
    m.diffuse_color = (lin(r), lin(g), lin(b), 1)
    MATS[hexcol] = m
    return m


def box(x0, x1, y0, y1, z0, z1, col, name='b'):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(mat(col))
    bpy.context.scene.collection.objects.link(ob)
    return ob


def tree(x, y, h=9.0, r=4.5):
    if 52 < x < 150 and 0 < y < 90:          # keep the tower plaza and the tower front free
        return
    box(x - 0.5, x + 0.5, y - 0.5, y + 0.5, 0, h * 0.45, '#7A5232', 'trunk')
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=r, location=(x, y, h * 0.45 + r * 0.75))
    ob = bpy.context.active_object
    ob.data.materials.append(mat('#34B04A'))
    return ob


# ---- ground, streets, areas
box(-P.HALF - 4, P.HALF + 4, -P.HALF - 4, P.HALF + 4, -0.6, 0.0, '#5BC247', 'ground')
for (nm, ax, c, ha, hs, conn) in P.STREETS:
    if ax == 'x':
        box(-P.HALF, P.HALF, c - hs, c + hs, 0, 0.3, '#DAD7CE', 'walk')
    else:
        box(c - hs, c + hs, -P.HALF, P.HALF, 0, 0.3, '#DAD7CE', 'walk')
for (nm, ax, c, ha, hs, conn) in P.STREETS:
    if ax == 'x':
        box(-P.HALF, P.HALF, c - ha, c + ha, 0, 0.35, '#464B58', 'road')
    else:
        box(c - ha, c + ha, -P.HALF, P.HALF, 0, 0.35, '#464B58', 'road')
for (i, x0, x1, y0, y1, lab, col) in P.AREAS:
    box(x0, x1, y0, y1, 0, 0.18 if i.startswith('P') and i != 'PARK' and i != 'PLAZA' else 0.12, col, i)

# ---- buildings
for (i, x0, x1, y0, y1, fl, kind, fac, front) in P.B:
    h = fl * P.FLOOR_H + (2.0 if i == 'TOWER' else 1.2)
    box(x0, x1, y0, y1, 0, h, P.PAL[fac], i)
    box(x0 - 0.6, x1 + 0.6, y0 - 0.6, y1 + 0.6, h, h + 1.0, '#F6F4EC', i + '_cornice')
    box(x0 + 1, x1 - 1, y0 + 1, y1 - 1, h + 1.0, h + 1.4, P.ROOF, i + '_roof')
    # entrance canopy on the front side
    if front == 'W':
        box(x0 - 5, x0, (y0 + y1) / 2 - 6, (y0 + y1) / 2 + 6, 6.5, 7.2, '#2D58B0', i + '_canopy')
    elif front == 'E':
        box(x1, x1 + 5, (y0 + y1) / 2 - 6, (y0 + y1) / 2 + 6, 6.5, 7.2, '#2D58B0', i + '_canopy')
    elif front == 'N':
        box((x0 + x1) / 2 - 6, (x0 + x1) / 2 + 6, y1, y1 + 5, 6.5, 7.2, '#2D58B0', i + '_canopy')
    else:
        box((x0 + x1) / 2 - 6, (x0 + x1) / 2 + 6, y0 - 5, y0, 6.5, 7.2, '#2D58B0', i + '_canopy')
# tower sign band (APARTMENTS) and glass lobby on the west face
t = [b for b in P.B if b[0] == 'TOWER'][0]
box(t[1] - 0.6, t[1] + 0.1, 36, 54, 7.4, 10.4, '#2C4C94', 'tower_sign')
box(t[1] - 0.3, t[1], 38, 52, 0.4, 6.4, '#BFE4F4', 'tower_lobby_glass')

# ---- park, fountain, trees
box(-56, -40, 40, 56, 0, 1.2, '#DCD0BB', 'fountain_base')
box(-50, -46, 46, 50, 1.2, 4.5, '#3A88E4', 'fountain')
for gx in range(-100, 12, 22):
    for gy in range(6, 100, 24):
        if (gx + 48) ** 2 + (gy - 48) ** 2 > 18 ** 2:
            tree(gx, gy)
for (nm, ax, c, ha, hs, conn) in P.STREETS:           # street trees on the sidewalk edge, every ~38 studs, away from crossings
    for k in range(-6, 7):
        p = k * 38 + 19
        if ax == 'x':
            for s in (-1, 1):
                if abs(p - 40) > 30 and abs(p + 130) > 22 and abs(p) < 235:
                    tree(p, c + s * (hs - 1.8), 8, 3.6)
        else:
            for s in (-1, 1):
                if abs(p + 30) > 30 and abs(p - 120) > 22 and abs(p) < 235:
                    tree(c + s * (hs - 1.8), p, 8, 3.6)
# bus stop and kiosk
box(55, 60, 8, 22, 0, 0.4, '#E4E7EB', 'bus_pad')
box(55.5, 59.5, 8, 22, 6.2, 6.8, '#2D58B0', 'bus_roof')
box(-34, -26, -6, 0, 0, 5, '#F4BA3A', 'kiosk')
# parked cars (simple blocks) on the parkings
cols = ['#E43A2E', '#2F63B8', '#FFFFFF', '#F58A2A', '#12AC9C', '#B9BAB6']
n = 0
for (i, x0, x1, y0, y1, lab, col) in P.AREAS:
    if i in ('P1', 'P2', 'P3'):
        for xx in range(int(x0) + 8, int(x1) - 8, 11):
            for yy in (int(y0) + 14, int(y0) + 40, int(y1) - 40, int(y1) - 14):
                n += 1
                if n % 3:
                    box(xx, xx + 4.6, yy, yy + 9.4, 0.2, 3.2, cols[n % len(cols)], 'car')
# fence ring with gaps at the connectors
G = P.GAP
def fence(x0, x1, y0, y1):
    box(x0, x1, y0, y1, 0, 3.2, '#FFFFFF', 'fence')
fence(-P.HALF, -P.HALF + 1, -P.HALF, -30 - G); fence(-P.HALF, -P.HALF + 1, -30 + G, P.HALF)
fence(P.HALF - 1, P.HALF, -P.HALF, -30 - G); fence(P.HALF - 1, P.HALF, -30 + G, P.HALF)
fence(-P.HALF, 40 - G, -P.HALF, -P.HALF + 1); fence(40 + G, P.HALF, -P.HALF, -P.HALF + 1)
fence(-P.HALF, 40 - G, P.HALF - 1, P.HALF); fence(40 + G, P.HALF, P.HALF - 1, P.HALF)

# ---- render setup
sc = bpy.context.scene
for eng in ('BLENDER_WORKBENCH', 'BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        sc.render.engine = eng
        break
    except TypeError:
        continue
try:
    sc.view_settings.view_transform = 'Standard'
except TypeError:
    pass
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.show_shadows = True
sc.display.shading.shadow_intensity = 0.55
sc.display.shading.show_cavity = False
w = bpy.data.worlds.new('w')
w.color = (0.62, 0.80, 0.95)
sc.world = w
sc.render.resolution_x, sc.render.resolution_y = 1400, 880
sc.render.image_settings.file_format = 'PNG'


def shot(name, loc, target, lens=28, ortho=None):
    cam = bpy.data.objects.get('cam') or bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    if cam.name not in sc.collection.objects:
        sc.collection.objects.link(cam)
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    cam.data.clip_end = 3000
    if ortho:
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = ortho
    else:
        cam.data.type = 'PERSP'
    sc.camera = cam
    sc.render.filepath = os.path.join(OUT, name + '.png')
    bpy.ops.render.render(write_still=True)
    print('rendered', name)


shot('block_aerial_sw', (-330, -360, 250), (30, 20, 5), 32)
shot('block_aerial_ne', (350, 360, 250), (-10, 0, 5), 32)
shot('block_plan_top', (0, 0, 800), (0, 0, 0), ortho=560)
shot('block_tower_street', (40, -2, 7), (112, 45, 22), 26)
shot('block_eye_avenue_b', (40, -90, 5.5), (40, 60, 8), 22)
