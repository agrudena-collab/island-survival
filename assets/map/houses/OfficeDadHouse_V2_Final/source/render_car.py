"""OfficeDad car sheet: python -I render_car.py OUTDIR  (3 beauty views + 4 orthographic blueprint views)"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import odh_core as K, odh_scene as S, odh_car as C
import bpy
from mathutils import Vector
out = sys.argv[-1]
os.makedirs(out, exist_ok=True)
import odh_site as ST
K.tf_push(0, 0, 0, 0)
C.dad_car('Site', pass_on_dash=False, sc=ST.CAR_SC)
K.tf_pop()
K.B('Site', 'concrete', -16, 16, -0.3, 0.0, -16, 16, solid=False)
S.clear(); S.materialize()
S.setup_scene(res=(1200, 750), samples=int(os.environ.get('SAMPLES', '32')), sun_energy=3.0)
for name, loc, tgt, lens in (('car_front34', (12, 5.5, 14), (0, 1.8, 0), 34), ('car_rear34', (-12, 5.5, -14), (0, 1.8, 0), 34), ('car_inside', (2.8, 5.6, 8.2), (-0.6, 2.8, 0.4), 30)):
    S.shot(os.path.join(out, name + '.png'), loc, tgt, lens=lens)
# orthographic blueprint views (Workbench, flat)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'FLAT'; sh.color_type = 'MATERIAL'
sc.render.film_transparent = False
sc.world.color = (1, 1, 1)
sc.render.resolution_x, sc.render.resolution_y = 1200, 600
for o in list(bpy.data.objects):
    if o.name.startswith('Site_concrete'):
        o.hide_render = True
cam = bpy.data.cameras.new('o'); cam.type = 'ORTHO'
co = bpy.data.objects.new('o', cam); sc.collection.objects.link(co); sc.camera = co
def ortho(name, loc, scale):
    cam.ortho_scale = scale
    co.location = (loc[0], -loc[2], loc[1])
    d = Vector((0, 0, 1.9)) - co.location
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, name + '.png')
    bpy.ops.render.render(write_still=True)
ortho('bp_side', (60, 1.9, 0), 15.0)
ortho('bp_front', (0, 1.9, 60), 7.5)
ortho('bp_rear', (0, 1.9, -60), 7.5)
sc.render.resolution_x, sc.render.resolution_y = 1200, 900
ortho('bp_top', (0.0, 80, 0.01), 16.0)
print('done')
