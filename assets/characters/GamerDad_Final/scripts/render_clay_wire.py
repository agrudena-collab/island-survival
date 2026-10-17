"""Clay and clay+wire renders (Workbench, real geometry of the saved .blend) of the problem zones: elbows, beard, face, grip, shoes.
blender -b <GamerDad_Sweatshirt_Review.blend> --python render_clay_wire.py -- <out_dir>"""
import math
import os
import sys

import bpy
from mathutils import Vector

V = Vector
OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
os.makedirs(OUT, exist_ok=True)
SC = bpy.context.scene
SC.render.engine = 'BLENDER_WORKBENCH'
sh = SC.display.shading
sh.light = 'STUDIO'
sh.color_type = 'OBJECT'
sh.show_cavity = False
sh.show_shadows = False
SC.display.render_aa = '8'
SC.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new("cw")
w.color = (0.93, 0.92, 0.9)
SC.world = w
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in meshes:
    o.color = (0.66, 0.66, 0.68, 1.0)
wires = []
for o in meshes:
    c = o.copy()
    c.data = o.data.copy()
    SC.collection.objects.link(c)
    c.modifiers.clear()
    m = c.modifiers.new("W", 'WIREFRAME')
    m.thickness = 0.012
    m.use_replace = True
    m.use_even_offset = False
    c.color = (0.05, 0.05, 0.08, 1.0)
    c.hide_render = True
    wires.append(c)
cam_d = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cam_d)
SC.collection.objects.link(cam)
SC.camera = cam


def orbit(t, d, az, el):
    a, e = math.radians(az), math.radians(el)
    return V(t) + V((d * math.sin(a) * math.cos(e), -d * math.cos(a) * math.cos(e), d * math.sin(e)))


def shot(name, tgt, az, el, ortho, res=1100, wire=False):
    for o in wires:
        o.hide_render = not wire
    cam.location = orbit(tgt, 20, az, el)
    cam.rotation_euler = (V(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_d.type, cam_d.ortho_scale = 'ORTHO', ortho
    SC.render.resolution_x = SC.render.resolution_y = res
    SC.render.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)


ER, EL = V((-2.02, -0.26, 3.4907)), V((1.84, 0.0, 3.4034))
for tag, wire in (("clay", False), ("clay_wire", True)):
    shot("elbow_R_outer_%s.png" % tag, ER, -90, 6, 2.8, wire=wire)
    shot("elbow_R_top_%s.png" % tag, ER, -30, 72, 2.8, wire=wire)
    shot("elbow_R_back_%s.png" % tag, ER, 180, 8, 2.8, wire=wire)
    shot("elbow_L_outer_%s.png" % tag, EL, 90, 6, 2.8, wire=wire)
    shot("elbow_L_back_%s.png" % tag, EL, 180, 8, 2.8, wire=wire)
    shot("beard_front_%s.png" % tag, V((0, -0.55, 4.8)), 0, 3, 3.0, wire=wire)
    shot("beard_q34_%s.png" % tag, V((0, -0.55, 4.8)), -35, 8, 3.0, wire=wire)
    shot("beard_below_%s.png" % tag, V((0, -0.55, 4.75)), -15, -42, 3.0, wire=wire)
    shot("beard_side_%s.png" % tag, V((0, -0.55, 4.75)), -90, 3, 3.0, wire=wire)
    shot("grip_front_%s.png" % tag, V((-2.05, -1.1, 3.75)), 0, 6, 2.8, wire=wire)
    shot("grip_top_%s.png" % tag, V((-2.05, -1.1, 3.75)), 0, 80, 2.8, wire=wire)
    shot("shoes_%s.png" % tag, V((0, -0.2, 0.7)), 25, 14, 4.2, wire=wire)
    shot("head_hair_%s.png" % tag, V((0, -0.2, 5.5)), -35, 25, 3.2, wire=wire)
